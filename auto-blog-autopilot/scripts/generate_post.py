#!/usr/bin/env python3
"""
매일 GitHub Actions에서 실행되어 블로그 글 1편을 자동 생성하는 스크립트.

- data/topics.txt 에서 주제를 하나 꺼내 쓰고, 큐 맨 뒤로 돌려보낸다 (무한 로테이션).
- 최근에 쓴 글 제목들을 함께 넘겨서 내용이 겹치지 않게 한다.
- Claude API로 본문을 생성하고, docs/_posts/ 에 Jekyll 포스트 파일로 저장한다.
- 쿠팡파트너스 관련 문구는 "검색 링크 + 고지문"까지만 자동 생성한다.
  실제 수익화(트래킹되는 딥링크)로 바꾸려면 쿠팡파트너스 대시보드에서
  해당 키워드로 딥링크를 만들어 주기적으로 교체해야 한다 (README 참고).
- 구글 Blogger API 인증 정보(GOOGLE_CLIENT_ID 등)가 설정되어 있으면,
  같은 글을 Blogger에도 동시에 자동 발행한다 (설정 안 돼 있으면 조용히 건너뜀).
- UNSPLASH_ACCESS_KEY가 설정되어 있으면, 글 내용에 맞는 무료 스톡 사진을
  Unsplash에서 찾아 본문 맨 위에 넣는다 (출처 표기 포함, 설정 안 돼 있으면
  조용히 건너뜀).
- 주제를 고를 때 단순 순환(FIFO)만 하지 않고, 큐 맨 앞의 5개 후보를 놓고
  (1) Google 트렌드, (2) 네이버 데이터랩(검색어트렌드 공식 API)으로 최근
  검색량이 높은지, (3) GA4에 이 블로그의 과거 인기글과 겹치는 주제인지
  (조회수+체류시간 기준)를 함께 점수화해서 1~5위를 매긴 뒤 1위 주제로
  글을 쓴다. 세 신호 모두 선택 사항이며, 설정/조회가 안 되면
  (NAVER_CLIENT_ID/SECRET, GA4_PROPERTY_ID/GA4_SERVICE_ACCOUNT_JSON
  미설정, pytrends 조회 실패 등) 조용히 살아있는 신호만으로, 전부
  실패하면 기존 큐 순서(FIFO) 그대로 동작한다 — 즉 이 기능이 없어도
  전혀 문제 없이 발행된다.
"""

import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import anthropic

try:
    import markdown as _markdown
except ImportError:
    _markdown = None

# auto-blog-autopilot/scripts/generate_post.py -> auto-blog-autopilot/
PROJECT_DIR = Path(__file__).resolve().parent.parent
# auto-blog-autopilot/ 의 형제 폴더인 docs/ (GitHub Pages 소스)
DOCS_DIR = PROJECT_DIR.parent / "docs"

TOPICS_FILE = PROJECT_DIR / "data" / "topics.txt"
POSTS_DIR = DOCS_DIR / "_posts"

# 특정 제품(예: 쿠팡파트너스 딥링크가 있는 제품)에 대해 한 번만 글을 쓰고
# 싶을 때 쓰는 수동 오버라이드 파일. 있으면 이번 실행은 평소 큐(topics.txt)를
# 건드리지 않고 이 파일 내용으로만 글을 쓴 뒤, 다 쓰고 나면 파일을 지워서
# 다음 실행부터는 다시 평소 큐로 돌아간다. 필수 키:
#   topic, product_name, product_info
# 그리고 아래 둘 중 하나:
#   - affiliate_url, affiliate_label (마크다운 링크로 삽입)
#   - affiliate_html, disclosure_text (주어진 배너 HTML과 고지문을 그대로 삽입)
MANUAL_TOPIC_FILE = PROJECT_DIR / "data" / "manual_topic.json"

# 여러 제품을 하루에 하나씩(매일 자동 실행되는 스케줄에 맞춰) 순서대로 발행하고
# 싶을 때 쓰는 큐 파일. 위와 같은 키를 갖는 항목들의 JSON 배열이며, 실행할
# 때마다 맨 앞의 항목 하나만 꺼내 쓰고 나머지는 그대로 남겨둔다(다 쓰면 파일을
# 지운다). MANUAL_TOPIC_FILE(단건)보다 우선한다.
MANUAL_TOPIC_QUEUE_FILE = PROJECT_DIR / "data" / "manual_topic_queue.json"

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5")
MAX_RECENT_TITLES = 10

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN", "")
BLOGGER_BLOG_ID = os.environ.get("BLOGGER_BLOG_ID", "")

UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")
UNSPLASH_APP_NAME = os.environ.get("UNSPLASH_APP_NAME", "auto-blog-autopilot")

GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID", "")
GA4_SERVICE_ACCOUNT_JSON = os.environ.get("GA4_SERVICE_ACCOUNT_JSON", "")

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")

CANDIDATE_POOL_SIZE = 5


def get_next_topic() -> str:
    """예전 방식(단순 FIFO 순환)의 주제 선택. 지금은 select_topic()이 대신
    쓰이지만, 트렌드/GA4 조회가 전부 실패했을 때의 동작과 동일하므로 참고용으로
    남겨둔다."""
    if not TOPICS_FILE.exists():
        sys.exit(f"주제 큐 파일이 없습니다: {TOPICS_FILE}")

    lines = [line.strip() for line in TOPICS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        sys.exit(f"주제 큐가 비어 있습니다: {TOPICS_FILE}")

    topic = lines[0]
    rotated = lines[1:] + [topic]
    TOPICS_FILE.write_text("\n".join(rotated) + "\n", encoding="utf-8")
    return topic


def score_candidates_by_trends(candidates: list[str]) -> dict[str, float]:
    """Google 트렌드(pytrends, 비공식/무료)로 최근 1개월 한국 검색 관심도를
    후보별로 점수화한다. pytrends는 로그인/키 없이 쓸 수 있지만 비공식 API라
    레이트리밋이나 스키마 변경에 취약하다 — 실패하면 빈 dict를 돌려주고
    절대 예외를 전파하지 않는다 (검색량 순위 없이 계속 진행)."""
    if not candidates:
        return {}

    try:
        from pytrends.request import TrendReq
    except ImportError as e:
        print(f"pytrends가 설치되어 있지 않아 검색량 기반 순위는 건너뜁니다: {e}")
        return {}

    kw_list = candidates[:5]  # pytrends는 한 번에 최대 5개 키워드까지만 비교 가능
    try:
        trends = TrendReq(hl="ko", tz=540)
        trends.build_payload(kw_list, timeframe="today 1-m", geo="KR")
        df = trends.interest_over_time()
    except Exception as e:  # pytrends는 다양한 예외(HTTP, 파싱 등)를 던질 수 있음
        print(f"Google 트렌드 조회 실패, 검색량 기반 순위 없이 계속합니다: {e}")
        return {}

    if df is None or df.empty:
        return {}

    scores = {}
    for kw in kw_list:
        if kw in df.columns:
            scores[kw] = float(df[kw].mean())
    return scores


def naver_configured() -> bool:
    return bool(NAVER_CLIENT_ID and NAVER_CLIENT_SECRET)


def score_candidates_by_naver_datalab(candidates: list[str]) -> dict[str, float]:
    """네이버 데이터랩 "검색어트렌드" 공식 오픈 API로 최근 1개월간 한국 검색
    관심도를 후보별로 점수화한다. 개인 계정 로그인 세션이 아니라, 네이버
    개발자센터(developers.naver.com)에서 앱 하나 등록하면 받는 Client ID/
    Secret만 쓰는 공식 REST API다 (Unsplash 키 발급과 비슷한 난이도).
    한국 사용자 기준으로는 Google 트렌드보다 이 신호가 더 정확한 편이라
    같이 참고한다. 미설정이거나 조회가 실패하면 빈 dict를 돌려주고
    절대 예외를 전파하지 않는다 (이 신호 없이 계속 진행)."""
    if not naver_configured() or not candidates:
        return {}

    try:
        import requests
    except ImportError as e:
        print(f"requests가 설치되어 있지 않아 네이버 데이터랩 조회를 건너뜁니다: {e}")
        return {}

    kw_list = candidates[:5]  # 데이터랩 검색어트렌드는 그룹 최대 5개까지 비교 가능
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=30)
    body = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "timeUnit": "date",
        "keywordGroups": [{"groupName": kw, "keywords": [kw]} for kw in kw_list],
    }
    try:
        resp = requests.post(
            "https://openapi.naver.com/v1/datalab/search",
            headers={
                "X-Naver-Client-Id": NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
                "Content-Type": "application/json",
            },
            data=json.dumps(body),
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        print(f"네이버 데이터랩 조회 실패, 이 신호 없이 계속합니다: {e}")
        return {}

    scores = {}
    for result in payload.get("results", []):
        group_name = result.get("title", "")
        data_points = result.get("data") or []
        if data_points:
            avg_ratio = sum(p.get("ratio", 0) for p in data_points) / len(data_points)
            scores[group_name] = avg_ratio
    return scores


def ga4_configured() -> bool:
    return bool(GA4_PROPERTY_ID and GA4_SERVICE_ACCOUNT_JSON)


def fetch_ga4_top_pages(days: int = 28) -> list[dict]:
    """최근 N일간 이 블로그(GitHub Pages)의 GA4 데이터에서 조회수 상위 글들을
    (조회수, 평균 체류시간)과 함께 가져온다. 서비스 계정 인증에 필요한
    google-auth만 쓰고, 무거운 공식 google-analytics-data 클라이언트(grpc/
    protobuf 포함)는 쓰지 않는다 — REST API를 직접 호출한다.
    설정이 없거나 인증/조회가 실패하면 빈 리스트를 돌려주고 절대 예외를
    전파하지 않는다 (GA4 데이터 없이 트렌드만으로, 또는 기존 순환으로 계속
    진행). 데이터가 아직 쌓이지 않은 초기 몇 주간은 항상 빈 리스트가 정상이다."""
    if not ga4_configured():
        return []

    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        import requests
    except BaseException as e:
        # 일부 환경에서는 google-auth가 의존하는 cryptography 패키지가
        # 시스템에 이미 깔린(apt 등) 다른 버전과 충돌해 ImportError가 아니라
        # PyO3 쪽 PanicException(BaseException 계열, 일반 Exception으로도 못 잡힘)을
        # 던지는 경우가 있다. GA4는 어디까지나 선택 기능이라 이런 경우에도
        # 전체 발행이 죽으면 안 되므로 BaseException까지 넓게 잡아 건너뛴다.
        print(f"GA4 연동에 필요한 패키지를 불러오지 못해 건너뜁니다: {e}")
        return []

    try:
        info = json.loads(GA4_SERVICE_ACCOUNT_JSON)
        credentials = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/analytics.readonly"]
        )
        credentials.refresh(Request())
    except Exception as e:
        print(f"GA4 인증 실패, GA4 데이터 없이 계속합니다: {e}")
        return []

    property_id = GA4_PROPERTY_ID if GA4_PROPERTY_ID.isdigit() else GA4_PROPERTY_ID.replace("properties/", "")
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
    body = {
        "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "today"}],
        "dimensions": [{"name": "pageTitle"}],
        "metrics": [{"name": "screenPageViews"}, {"name": "userEngagementDuration"}],
        "orderBys": [{"metric": {"metricName": "screenPageViews"}, "desc": True}],
        "limit": 20,
    }
    try:
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json",
            },
            data=json.dumps(body),
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        print(f"GA4 리포트 조회 실패, GA4 데이터 없이 계속합니다: {e}")
        return []

    rows = payload.get("rows") or []
    results = []
    for row in rows:
        try:
            title = row["dimensionValues"][0]["value"]
            pageviews = float(row["metricValues"][0]["value"])
            engagement = float(row["metricValues"][1]["value"])
            results.append({"title": title, "pageviews": pageviews, "engagement_seconds": engagement})
        except (KeyError, IndexError, ValueError):
            continue
    return results


def score_candidates_by_ga4(candidates: list[str], ga4_pages: list[dict]) -> dict[str, float]:
    """GA4 인기글 제목과 후보 주제 문자열 사이의 단어 겹침으로, 각 후보가
    "과거에 실제로 조회수+체류시간이 좋았던 주제"와 얼마나 비슷한지 점수화한다.
    (GA4 페이지 제목은 Jekyll의 `{{ page.title }} · {{ site.title }}` 형식이라
    완전 일치는 기대하지 않고, 어디까지나 근사치 힌트로만 쓴다.)"""
    if not ga4_pages:
        return {}

    max_pv = max((p["pageviews"] for p in ga4_pages), default=0) or 1
    max_eng = max((p["engagement_seconds"] for p in ga4_pages), default=0) or 1

    scores = {c: 0.0 for c in candidates}
    for page in ga4_pages:
        title_tokens = set(re.findall(r"[가-힣A-Za-z0-9]+", page["title"]))
        pv_norm = page["pageviews"] / max_pv
        eng_norm = page["engagement_seconds"] / max_eng
        page_score = pv_norm * 0.5 + eng_norm * 0.5  # 조회수와 체류시간을 절반씩 반영
        for candidate in candidates:
            cand_tokens = set(re.findall(r"[가-힣A-Za-z0-9]+", candidate))
            overlap = len(title_tokens & cand_tokens)
            if overlap:
                scores[candidate] += overlap * page_score
    return scores


def select_topic() -> str:
    """큐 맨 앞 CANDIDATE_POOL_SIZE개 후보를 놓고 검색량(Google 트렌드,
    네이버 데이터랩)과 자체 유입량/체류시간(GA4)을 함께 점수화해서 1~5위를
    매긴 뒤, 1위 주제로 글을 쓴다. 선택된 주제만 큐 맨 뒤로 돌리고 나머지
    후보는 그대로 앞쪽에 남겨서, 이번에 밀린 후보들이 다음날 다시 후보
    풀에 들어가게 한다. 세 신호가 전부 실패/미설정이면 기존 FIFO와
    동일하게 동작하고, 일부만 살아있으면 살아있는 신호만 동일 가중치로
    평균 낸다 (신호가 적다고 순위가 왜곡되지 않도록)."""
    if not TOPICS_FILE.exists():
        sys.exit(f"주제 큐 파일이 없습니다: {TOPICS_FILE}")

    lines = [line.strip() for line in TOPICS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        sys.exit(f"주제 큐가 비어 있습니다: {TOPICS_FILE}")

    pool_size = min(CANDIDATE_POOL_SIZE, len(lines))
    candidates = lines[:pool_size]

    trend_scores = score_candidates_by_trends(candidates)
    naver_scores = score_candidates_by_naver_datalab(candidates)
    ga4_pages = fetch_ga4_top_pages()
    ga4_scores = score_candidates_by_ga4(candidates, ga4_pages)

    def normalize(d: dict[str, float]) -> dict[str, float]:
        if not d:
            return {}
        max_v = max(d.values()) or 1
        return {k: v / max_v for k, v in d.items()}

    available_signals = [
        normalize(s) for s in (trend_scores, naver_scores, ga4_scores) if s
    ]

    if available_signals:
        combined = {
            c: sum(sig.get(c, 0.0) for sig in available_signals) / len(available_signals)
            for c in candidates
        }
        ranked = sorted(candidates, key=lambda c: combined[c], reverse=True)
    else:
        ranked = list(candidates)  # 신호가 전부 실패하면 기존 큐 순서(FIFO) 그대로

    print(f"오늘의 주제 후보 순위 (1~{len(ranked)}위):")
    for i, c in enumerate(ranked, start=1):
        print(
            f"  {i}위: {c}  "
            f"(구글트렌드={trend_scores.get(c, 0.0):.1f}, "
            f"네이버데이터랩={naver_scores.get(c, 0.0):.1f}, "
            f"GA4={ga4_scores.get(c, 0.0):.2f})"
        )

    topic = ranked[0]

    remaining = [line for line in lines if line != topic]
    rotated = remaining + [topic]
    TOPICS_FILE.write_text("\n".join(rotated) + "\n", encoding="utf-8")

    return topic


def _validate_manual_item(data: dict) -> bool:
    base_required = ("topic", "product_name", "product_info")
    if not all(data.get(k) for k in base_required):
        print(f"수동 주제 항목에 필수 항목({', '.join(base_required)})이 빠져 있어 건너뜁니다.")
        return False

    has_markdown_link = data.get("affiliate_url") and data.get("affiliate_label")
    has_raw_html = data.get("affiliate_html") and data.get("disclosure_text")
    if not (has_markdown_link or has_raw_html):
        print(
            "수동 주제 항목에 제휴 정보가 없어 건너뜁니다 "
            "(affiliate_url+affiliate_label 또는 affiliate_html+disclosure_text 필요)."
        )
        return False

    return True


def load_manual_topic() -> dict | None:
    """다음 순서로 이번 실행에 쓸 "수동 지정" 제품 정보를 찾아 돌려준다:

    1. MANUAL_TOPIC_QUEUE_FILE (여러 제품을 하루에 하나씩 순서대로 발행하는 큐) —
       맨 앞 항목 하나를 꺼내 쓰고, 나머지는 그대로 파일에 남겨둔다(다 쓰면 파일 삭제).
    2. MANUAL_TOPIC_FILE (단건 오버라이드) — 이번 실행에 한 번만 쓰고 파일을 지운다.

    둘 다 없거나 형식이 잘못됐으면 None을 돌려준다 (이 경우 평소처럼
    select_topic() 큐를 그대로 쓴다). 실제 삭제/재기록은 main()에서
    발행이 끝난 뒤에 한다(consume_manual_topic 참고) — 여기서는 읽기만 한다.
    """
    if MANUAL_TOPIC_QUEUE_FILE.exists():
        try:
            items = json.loads(MANUAL_TOPIC_QUEUE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"수동 주제 큐 파일을 읽지 못해 건너뜁니다: {e}")
            items = None

        if isinstance(items, list):
            while items:
                candidate = items[0]
                if isinstance(candidate, dict) and _validate_manual_item(candidate):
                    candidate = dict(candidate)
                    candidate["_source"] = "queue"
                    return candidate
                print("수동 주제 큐의 맨 앞 항목이 잘못돼 건너뛰고 다음 항목을 시도합니다.")
                items = items[1:]
            # 큐가 비어 있거나(원래부터, 혹은 잘못된 항목을 다 걸러내서) 남은 게 없음
        elif items is not None:
            print("수동 주제 큐 파일이 배열(JSON list) 형식이 아니어서 건너뜁니다.")

    if MANUAL_TOPIC_FILE.exists():
        try:
            data = json.loads(MANUAL_TOPIC_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"수동 주제 파일을 읽지 못해 건너뜁니다: {e}")
            return None

        if isinstance(data, dict) and _validate_manual_item(data):
            data = dict(data)
            data["_source"] = "single"
            return data

    return None


def consume_manual_topic(manual: dict) -> None:
    """load_manual_topic()이 돌려준 항목을 다 쓰고 난 뒤 호출한다. 큐에서
    온 항목이면 맨 앞 하나만 제거하고 나머지(있다면)를 다시 저장하고,
    단건 파일에서 온 항목이면 그 파일을 지운다."""
    if manual.get("_source") == "queue":
        try:
            items = json.loads(MANUAL_TOPIC_QUEUE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            items = []
        remaining = items[1:] if isinstance(items, list) and items else []
        if remaining:
            MANUAL_TOPIC_QUEUE_FILE.write_text(
                json.dumps(remaining, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            print(f"수동 주제 큐에서 1건 사용, {len(remaining)}건 남음.")
        else:
            MANUAL_TOPIC_QUEUE_FILE.unlink(missing_ok=True)
            print("수동 주제 큐를 모두 사용하여 삭제했습니다 (다음 실행부터는 평소 큐로 돌아갑니다).")
    else:
        MANUAL_TOPIC_FILE.unlink(missing_ok=True)
        print("수동 주제 파일을 사용 완료하여 삭제했습니다 (다음 실행부터는 평소 큐로 돌아갑니다).")


def get_recent_titles(limit: int = MAX_RECENT_TITLES) -> list[str]:
    if not POSTS_DIR.exists():
        return []

    files = sorted(POSTS_DIR.glob("*.md"))[-limit:]
    titles = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        match = re.search(r'^title:\s*"(.+)"\s*$', text, re.MULTILINE)
        if match:
            titles.append(match.group(1))
    return titles


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:60] or "post"


def build_prompt(topic: str, recent_titles: list[str]) -> str:
    avoid_block = ""
    if recent_titles:
        recent_list = "\n".join(f"- {t}" for t in recent_titles)
        avoid_block = f"\n최근에 이미 다룬 제목들이니 내용/각도가 겹치지 않게 새로운 관점으로 써줘:\n{recent_list}\n"

    return f"""오늘의 주제: {topic}
{avoid_block}
아래 형식을 정확히 지켜서 한국어 블로그 글을 작성해줘.

TITLE: (SEO에 좋은 구체적인 제목, 30자 내외, 과장/낚시성 문구 금지)
TAGS: (쉼표로 구분된 태그 3~5개)
KEYWORD: (이 글과 자연스럽게 어울리는 쇼핑 검색 키워드 1개, 예: "캠핑 의자")
IMAGE_QUERY: (이 글에 어울리는 사진을 찾기 위한 영어 검색어 2~4단어,
  구체적인 장면 위주로. 예: "cozy home office desk", "camping tent morning")
---
(본문 마크다운. 1200~1800자 분량. 소제목(##) 2~4개.
실용적인 정보 위주로 쓰고, 확인되지 않은 사실이나 과장된 효능/수익 약속은 절대 쓰지 마.
말투는 자연스러운 존댓말 블로그 톤으로.)
"""


def build_product_prompt(manual: dict, recent_titles: list[str]) -> str:
    """load_manual_topic()으로 받은 특정 제품 정보를 바탕으로 글을 쓰게 하는
    프롬프트. build_prompt()와 형식(TITLE/TAGS/IMAGE_QUERY/본문)은 같지만,
    KEYWORD 대신 이미 정해진 제휴 링크를 쓰므로 KEYWORD는 요구하지 않고,
    실제 제품 사실(product_info)만 근거로 쓰고 그 외 숫자는 지어내지
    말라고 명시한다."""
    avoid_block = ""
    if recent_titles:
        recent_list = "\n".join(f"- {t}" for t in recent_titles)
        avoid_block = f"\n최근에 이미 다룬 제목들이니 내용/각도가 겹치지 않게 새로운 관점으로 써줘:\n{recent_list}\n"

    return f"""오늘의 주제: {manual['topic']}
{avoid_block}
이 글에서는 아래 실제 제품을 자연스럽게 소개하거나 추천해야 해:

제품명: {manual['product_name']}
제품 정보(사실 그대로, 지어내지 말 것): {manual['product_info']}

아래 형식을 정확히 지켜서 한국어 블로그 글을 작성해줘.

TITLE: (SEO에 좋은 구체적인 제목, 30자 내외, 과장/낚시성 문구 금지)
TAGS: (쉼표로 구분된 태그 3~5개)
IMAGE_QUERY: (이 글에 어울리는 사진을 찾기 위한 영어 검색어 2~4단어,
  구체적인 장면 위주로. 예: "puppy training pad", "dog owner home")
---
(본문 마크다운. 1200~1800자 분량. 소제목(##) 2~4개.
먼저 이 주제를 고를 때 일반적으로 확인해야 할 기준을 실용적으로 설명하고,
자연스러운 흐름 속에서 위 제품 정보를 근거로 위 제품을 구체적으로 소개/추천해줘.
위에 안 나온 가격·리뷰수·사양 등 숫자는 절대 새로 지어내지 말고, 주어진
제품 정보 항목만 사실로 써. 과장된 효능이나 확정적인 수익 약속은 절대 쓰지 마.
말투는 자연스러운 존댓말 블로그 톤으로.)
"""


def call_claude(prompt: str) -> str:
    client = anthropic.Anthropic()

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            output_config={"effort": "medium"},
            system=(
                "너는 한국어 생활정보 블로그의 자동 발행 시스템에서 콘텐츠를 작성하는 담당자다. "
                "사실에 기반해서 쓰고, 과장 광고나 확정적인 효과·수익 약속은 절대 하지 않으며, "
                "자연스러운 문체로 작성한다."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.AuthenticationError:
        sys.exit("ANTHROPIC_API_KEY가 잘못되었거나 설정되지 않았습니다.")
    except anthropic.PermissionDeniedError:
        sys.exit("API 키에 이 요청을 수행할 권한이 없습니다.")
    except anthropic.NotFoundError:
        sys.exit(f"모델을 찾을 수 없습니다: {MODEL}")
    except anthropic.RateLimitError as e:
        retry_after = e.response.headers.get("retry-after", "알 수 없음") if e.response else "알 수 없음"
        sys.exit(f"레이트 리밋에 걸렸습니다. retry-after={retry_after}")
    except anthropic.APIStatusError as e:
        sys.exit(f"API 오류 (status={e.status_code}): {e.message}")
    except anthropic.APIConnectionError:
        sys.exit("네트워크 오류로 API에 연결하지 못했습니다.")

    if response.stop_reason == "refusal":
        sys.exit("Claude가 이 요청을 거절했습니다 (stop_reason=refusal). 주제를 확인해 주세요.")

    for block in response.content:
        if block.type == "text":
            return block.text

    sys.exit("응답에 텍스트 콘텐츠가 없습니다.")


def _find_field(text: str, label: str) -> str:
    """text에서 "LABEL: 값" 형태의 줄을 찾아 값만 돌려준다.

    AI가 형식을 완전히 똑같이 지키지 않는 경우(라벨을 **굵게** 쓰거나,
    콜론 앞에 공백을 넣거나, 전각 콜론 "："을 쓰는 등)에도 인식하도록
    관대하게 매칭한다. 못 찾으면 빈 문자열을 돌려준다.
    """
    pattern = rf"^\s*[*_]{{0,2}}{re.escape(label)}[*_]{{0,2}}\s*[:：]\s*(.+?)\s*$"
    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    value = match.group(1).strip()
    # 값 앞뒤에 남아있는 마크다운 강조나 따옴표도 정리
    return re.sub(r'^[*_"\']+|[*_"\']+$', "", value).strip()


def parse_output(text: str, fallback_title: str = "") -> tuple[str, str, str, str, str]:
    title = _find_field(text, "TITLE") or fallback_title or "제목 미확인 포스트"
    tags = _find_field(text, "TAGS")
    keyword = _find_field(text, "KEYWORD")
    image_query = _find_field(text, "IMAGE_QUERY")

    body = text.split("---", 1)[-1].strip() if "---" in text else text.strip()
    return title, tags, keyword, image_query, body


def build_affiliate_block(keyword: str) -> str:
    if not keyword:
        return ""

    query = keyword.replace(" ", "+")
    # NOTE: 아래는 단순 검색 링크입니다 (수익화 안 됨).
    # 실제로 수익이 붙게 하려면 쿠팡파트너스 대시보드에서
    # 이 키워드로 "딥링크"를 생성해서 이 URL을 주기적으로 교체해야 합니다.
    return (
        "\n\n---\n\n"
        f'🔗 관련 상품 보러가기: [쿠팡에서 "{keyword}" 검색하기]'
        f"(https://www.coupang.com/np/search?q={query})\n\n"
        "*(쿠팡파트너스 활동의 일환으로, 위 링크를 통해 상품을 구매하실 경우 "
        "일정액의 수수료를 제공받을 수 있습니다.)*\n"
    )


def build_manual_affiliate_block(manual: dict) -> str:
    """load_manual_topic()으로 받은, 이미 정해진 실제 쿠팡파트너스 링크(또는 배너
    HTML)를 그대로 쓴다 (build_affiliate_block()과 달리 검색 링크로 대체하지 않음).

    manual에 affiliate_html/disclosure_text가 있으면 그 원문 그대로(HTML 배너 +
    지정된 고지문)를 쓰고, 없으면 affiliate_url/affiliate_label로 마크다운 링크
    형태를 만든다."""
    if manual.get("affiliate_html") and manual.get("disclosure_text"):
        return f"\n\n---\n\n{manual['affiliate_html']}\n\n{manual['disclosure_text']}\n"

    return (
        "\n\n---\n\n"
        f"🔗 관련 상품 보러가기: [{manual['affiliate_label']}]({manual['affiliate_url']})\n\n"
        "*(쿠팡파트너스 활동의 일환으로, 위 링크를 통해 상품을 구매하실 경우 "
        "일정액의 수수료를 제공받을 수 있습니다.)*\n"
    )


def find_stock_photo(query: str) -> dict | None:
    """Unsplash에서 query에 맞는 무료 사진 1장을 찾아 정보를 돌려준다.
    설정이 없거나 실패하면 None을 돌려주고, 절대 sys.exit 하지 않는다
    (이미지는 있으면 좋은 부가 기능이지, 없다고 글 발행 자체를 막으면 안 된다)."""
    if not UNSPLASH_ACCESS_KEY or not query:
        return None

    params = urllib.parse.urlencode({"query": query, "per_page": 1, "orientation": "landscape"})
    req = urllib.request.Request(
        f"https://api.unsplash.com/search/photos?{params}",
        headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read())
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
        print(f"Unsplash 사진 검색 실패, 이미지 없이 계속합니다: {e}")
        return None

    results = payload.get("results") or []
    if not results:
        print(f"Unsplash에서 '{query}'에 맞는 사진을 못 찾았습니다, 이미지 없이 계속합니다.")
        return None

    photo = results[0]

    # Unsplash API 가이드라인상, 실제로 사진을 사용할 때는 download_location을
    # 한 번 호출해줘야 한다 (사진작가 통계에 반영됨). 실패해도 무시한다.
    download_location = (photo.get("links") or {}).get("download_location")
    if download_location:
        try:
            ping = urllib.request.Request(
                download_location, headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
            )
            urllib.request.urlopen(ping, timeout=10).close()
        except (urllib.error.URLError, urllib.error.HTTPError):
            pass

    return {
        "url": (photo.get("urls") or {}).get("regular", ""),
        "alt": photo.get("alt_description") or query,
        "photographer_name": (photo.get("user") or {}).get("name", "Unsplash"),
        "photographer_url": (photo.get("user") or {}).get("links", {}).get("html", "https://unsplash.com"),
    }


def build_image_block(photo: dict | None) -> str:
    if not photo or not photo.get("url"):
        return ""

    utm = f"utm_source={UNSPLASH_APP_NAME}&utm_medium=referral"
    photographer_link = f"{photo['photographer_url']}?{utm}"
    unsplash_link = f"https://unsplash.com/?{utm}"

    return (
        f"![{photo['alt']}]({photo['url']})\n"
        f"*Photo by [{photo['photographer_name']}]({photographer_link}) on "
        f"[Unsplash]({unsplash_link})*\n\n"
    )


def extract_product_image(affiliate_html: str) -> dict | None:
    """제품 지정 발행(manual)의 affiliate_html(쿠팡 배너 <img> 태그)에서 실제
    상품 이미지 URL과 alt 텍스트를 뽑아낸다. 상관없는 Unsplash 스톡사진 대신
    이 이미지를 글 대표 이미지로 쓰기 위함 — 실제 그 상품 사진이라 훨씬
    정확하다. 배너에 img 태그가 없거나 파싱에 실패하면 None을 돌려주고,
    호출부는 이 경우 이미지 없이 계속 진행한다(예외를 일으키지 않음)."""
    if not affiliate_html:
        return None

    src_match = re.search(r'<img[^>]*\bsrc="([^"]+)"', affiliate_html)
    if not src_match:
        return None

    alt_match = re.search(r'<img[^>]*\balt="([^"]*)"', affiliate_html)
    return {"url": src_match.group(1), "alt": alt_match.group(1) if alt_match else ""}


def build_product_image_block(photo: dict | None) -> str:
    """extract_product_image()로 뽑은 실제 상품 이미지를 글 맨 위에 넣는다.
    Unsplash 사진작가 출처 표기 대신, 이미지 출처가 쿠팡임을 짧게 밝힌다."""
    if not photo or not photo.get("url"):
        return ""

    alt = photo["alt"] or "제품 이미지"
    return f"![{alt}]({photo['url']})\n*제품 이미지 출처: 쿠팡*\n\n"


def blogger_configured() -> bool:
    return all([GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN, BLOGGER_BLOG_ID])


def get_google_access_token() -> str:
    data = urllib.parse.urlencode(
        {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": GOOGLE_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        # 구글이 왜 거절했는지 본문에 이유가 담겨 있어서(예: invalid_grant),
        # 그냥 "401 Unauthorized"만 찍으면 원인을 알 수 없다. 그대로 노출해서 로그에 남긴다.
        raise urllib.error.HTTPError(e.url, e.code, f"{e.reason}: {e.read().decode('utf-8', 'replace')}", e.headers, None)
    return payload["access_token"]


def markdown_to_html(text: str) -> str:
    if _markdown is not None:
        return _markdown.markdown(text)

    # markdown 패키지가 없을 때를 위한 아주 단순한 대체 변환 (## 소제목, 문단만 처리)
    html_lines = []
    for line in text.split("\n"):
        if line.startswith("## "):
            html_lines.append(f"<h3>{line[3:]}</h3>")
        elif line.strip():
            html_lines.append(f"<p>{line}</p>")
    return "\n".join(html_lines)


def post_to_blogger(title: str, body_markdown: str) -> None:
    """설정돼 있으면 같은 글을 구글 Blogger에도 발행한다. 실패해도 GitHub Pages
    발행 자체를 막지 않도록, 여기서 나는 오류는 절대 sys.exit 하지 않고 그냥 건너뛴다."""
    if not blogger_configured():
        print("Blogger 인증 정보가 없어 Blogger 발행은 건너뜁니다.")
        return

    try:
        access_token = get_google_access_token()
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, ValueError) as e:
        print(f"Blogger 액세스 토큰 갱신 실패, 이번 회차는 건너뜁니다: {e}")
        return

    payload = json.dumps({"title": title, "content": markdown_to_html(body_markdown)}).encode("utf-8")
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}/posts/"
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
        print(f"Blogger 발행 완료: {result.get('url', '(URL 확인 불가)')}")
    except urllib.error.HTTPError as e:
        print(f"Blogger 발행 실패, 이번 회차는 건너뜁니다: {e.code} {e.reason}: {e.read().decode('utf-8', 'replace')}")
    except urllib.error.URLError as e:
        print(f"Blogger 발행 실패, 이번 회차는 건너뜁니다: {e}")


BLOGGER_PRIVACY_PAGE_TITLE = "개인정보처리방침"
BLOGGER_ABOUT_PAGE_TITLE = "소개"

BLOGGER_PRIVACY_PAGE_MD = """\
이 페이지는 이 블로그를 방문하시는 분들에게 어떤 정보가 수집되고 어떻게 쓰이는지 설명합니다.

## 1. 쿠키 및 방문 기록

이 블로그는 방문 통계 분석을 위해 Google Analytics를 사용할 수 있습니다. Google Analytics는 쿠키를 이용해 방문 페이지, 체류 시간, 접속 기기 등 비식별 통계 정보를 수집합니다. 개인을 특정할 수 있는 정보(이름, 연락처 등)는 수집하지 않습니다.

## 2. 광고 게재

이 블로그에는 Google AdSense를 비롯한 제3자 광고가 게재될 수 있습니다. Google 등 광고 게재업체는 이용자의 이전 방문 기록을 바탕으로 맞춤 광고를 보여주기 위해 쿠키를 사용할 수 있습니다.

- Google이 광고에 쿠키를 사용하는 방식은 [Google 광고 정책](https://policies.google.com/technologies/ads)에서 확인하실 수 있습니다.
- 맞춤 광고를 원치 않으시면 [Google 광고 설정](https://adssettings.google.com)에서 개인 맞춤 광고를 비활성화할 수 있습니다.

## 3. 제휴 마케팅(어필리에이트) 고지

이 블로그의 일부 게시글에는 쿠팡 파트너스 활동을 통한 제휴 링크가 포함되어 있으며, 이런 링크를 통해 상품을 구매하시면 이 블로그 운영자가 일정액의 수수료를 제공받을 수 있습니다. 해당 사실은 관련 게시글 본문에도 별도로 고지하고 있습니다.

## 4. 콘텐츠 제작 방식

이 블로그의 글은 자동화된 콘텐츠 파이프라인을 통해 작성·발행됩니다. 주제 선정과 제품 정보는 운영자가 관리하며, 정보의 정확성을 위해 지속적으로 점검하고 있습니다.

## 5. 문의

이 개인정보처리방침이나 블로그 운영과 관련해 문의하실 내용이 있으면 게시글 댓글을 통해 남겨 주세요.

## 6. 개정

이 방침은 서비스 내용 변경이나 관련 법령 개정에 따라 변경될 수 있으며, 변경 시 이 페이지에 반영합니다.
"""

BLOGGER_ABOUT_PAGE_MD_TEMPLATE = """\
## 이 블로그는

1인 가구와 반려동물을 키우는 분들이 반복해서 사야 하는 생활 소모품 — 생수, 화장지, 사료, 모래, 간편식 같은 것들 — 을 어떻게 고르고 어떤 주기로 구매하면 좋은지 정리합니다. 재구매 주기, 보관 방법, 성분표 읽는 법처럼 실제로 사고 쓰면서 부딪히는 질문들을 다룹니다.

## 운영 방식

이 블로그는 콘텐츠 자동화 파이프라인을 통해 매일 새 글을 발행합니다. 다룰 주제와 소개하는 제품 정보는 운영자가 선정·확인하며, 게시글 내용은 이 과정을 거쳐 작성됩니다.

일부 게시글에는 쿠팡 파트너스 제휴 링크가 포함되어 있고, 이를 통한 구매가 이루어지면 운영자가 일정액의 수수료를 받을 수 있습니다. 해당 사실은 관련 게시글마다 명시하고 있습니다. 자세한 내용은 [개인정보처리방침]({privacy_url}) 페이지를 참고해 주세요.

## 연락

블로그 내용에 대한 의견이나 문의는 게시글 댓글로 남겨 주시면 확인합니다.
"""


def sync_blogger_static_pages() -> None:
    """개인정보처리방침·소개 페이지가 Blogger에 아직 없으면 만들어 둔다.
    제목 기준으로 이미 있으면 아무것도 하지 않으므로, 매일 실행돼도 안전하다
    (idempotent). 애드센스는 실제로 신청하는 도메인(Blogger)에 이 페이지들이
    있어야 심사가 되므로, GitHub Pages(docs/privacy.md, docs/about.md)와
    같은 내용을 Blogger 쪽에도 맞춰 둔다. 실패해도 본 발행 흐름을 막지 않는다."""
    if not blogger_configured():
        return

    try:
        access_token = get_google_access_token()
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, ValueError) as e:
        print(f"Blogger 정적 페이지 동기화 건너뜀 (토큰 갱신 실패): {e}")
        return

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    pages_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}/pages/"

    try:
        req = urllib.request.Request(pages_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            existing = json.loads(resp.read()).get("items", []) or []
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"Blogger 페이지 목록 조회 실패, 정적 페이지 동기화 건너뜀: {e}")
        return

    existing_by_title = {p.get("title", ""): p for p in existing}

    def _create_page(title: str, body_markdown: str) -> str | None:
        payload = json.dumps({"title": title, "content": markdown_to_html(body_markdown)}).encode("utf-8")
        req = urllib.request.Request(pages_url, data=payload, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
            url = result.get("url")
            print(f"Blogger {title} 페이지 생성 완료: {url}")
            return url
        except urllib.error.HTTPError as e:
            print(f"Blogger {title} 페이지 생성 실패: {e.code} {e.reason}: {e.read().decode('utf-8', 'replace')}")
        except urllib.error.URLError as e:
            print(f"Blogger {title} 페이지 생성 실패: {e}")
        return None

    privacy_url = existing_by_title.get(BLOGGER_PRIVACY_PAGE_TITLE, {}).get("url")
    if BLOGGER_PRIVACY_PAGE_TITLE not in existing_by_title:
        privacy_url = _create_page(BLOGGER_PRIVACY_PAGE_TITLE, BLOGGER_PRIVACY_PAGE_MD)

    if BLOGGER_ABOUT_PAGE_TITLE not in existing_by_title:
        about_md = BLOGGER_ABOUT_PAGE_MD_TEMPLATE.format(
            privacy_url=privacy_url or "https://www.blogger.com"
        )
        _create_page(BLOGGER_ABOUT_PAGE_TITLE, about_md)


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY 환경변수가 설정되어 있지 않습니다.")

    manual = load_manual_topic()
    recent_titles = get_recent_titles()

    if manual:
        topic = manual["topic"]
        prompt = build_product_prompt(manual, recent_titles)
    else:
        topic = select_topic()
        prompt = build_prompt(topic, recent_titles)

    raw_output = call_claude(prompt)
    title, tags, keyword, image_query, body = parse_output(raw_output, fallback_title=topic)

    if manual and manual.get("affiliate_html"):
        # 제품 지정 발행: 무관한 Unsplash 스톡사진 대신, 이미 갖고 있는
        # 실제 상품 이미지(쿠팡 배너)를 대표 이미지로 쓴다.
        product_photo = extract_product_image(manual["affiliate_html"])
        image_block = build_product_image_block(product_photo)
    else:
        photo = find_stock_photo(image_query or keyword or topic)
        image_block = build_image_block(photo)
    body = image_block + body

    today = datetime.date.today()
    slug = slugify(title)
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    post_path = POSTS_DIR / f"{today.isoformat()}-{slug}.md"

    tag_items = [t.strip() for t in tags.split(",") if t.strip()]
    tag_list = ", ".join(f'"{t}"' for t in tag_items)
    safe_title = title.replace('"', "'")

    front_matter = (
        "---\n"
        "layout: post\n"
        f'title: "{safe_title}"\n'
        f"date: {today.isoformat()} 09:00:00 +0900\n"
        f"tags: [{tag_list}]\n"
        "---\n"
    )

    if manual:
        affiliate_block = build_manual_affiliate_block(manual)
    else:
        affiliate_block = build_affiliate_block(keyword)
    post_path.write_text(front_matter + "\n" + body + affiliate_block, encoding="utf-8")

    print(f"생성 완료: {post_path.relative_to(PROJECT_DIR.parent)}")

    post_to_blogger(safe_title, body + affiliate_block)
    sync_blogger_static_pages()

    if manual:
        consume_manual_topic(manual)


if __name__ == "__main__":
    main()
