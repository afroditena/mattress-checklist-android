#!/usr/bin/env python3
"""
매일 GitHub Actions에서 실행되어 블로그 글 1편을 자동 생성하는 스크립트.

2026-09-18: 니치를 "AI-Powered Productivity Tools"(영어, 미국 독자 대상)로
완전히 전환했다. 이전 니치(매트리스/건강/재무/정치경제 핫이슈, 전부 한국어)는
폐기했고 관련 코드(select_topic의 Naver/GA4/pytrends 점수화, 핫이슈 프롬프트,
건강/금융 출처 블록 등)는 삭제했다 - 예전 발행글(docs/_posts의 한국어 글들)은
그대로 남아있지만 새 글은 전부 이 새 니치/포맷으로 나간다.

- data/topics.json 에 5개 클러스터(A~E) x 6개, 총 30개 키워드가 고정 풀로
  들어있다. 매 실행마다 이 중 하나를 클러스터 가중치 기반 가중 무작위로
  고른다 - 단순 How-to(클러스터 A/B)보다 트러블슈팅(D, 경쟁도 낮아 우선)과
  비교/대안형(C/E, 광고 친화적이고 AI Overview에 덜 깎이는 검색 유형)을
  더 자주 고르도록 클러스터별 가중치를 둔다 (select_niche_topic() 참고).
  최근 사용한 주제 id는 data/used_topic_ids.json에 남겨서, 풀을 거의 다
  돌기 전까지는 같은 주제가 다시 나오지 않게 한다.
- 최근에 쓴 글 제목들을 함께 넘겨서 내용이 겹치지 않게 한다.
- 포맷은 클러스터마다 다르게 정해져 있다: How-to(A/B), Alternative(C),
  Troubleshoot(D), Comparison(E) - 각각 구조가 다른 프롬프트 빌더로 글을
  쓴다 (build_how_to_prompt 등). 전부 Claude의 web_search 도구를 켜서,
  실제 검색 결과(가격 페이지, 공식 지원문서 등)를 근거로 쓰고 그 출처
  URL도 SOURCES 필드로 받는다 - 모델의 사전 지식만으로 지어내지 않도록.
- Claude API로 본문(영어)을 생성하고, docs/_posts/ 에 Jekyll 포스트
  파일로 저장한다.
- 구글 Blogger API 인증 정보(GOOGLE_CLIENT_ID 등)가 설정되어 있으면,
  같은 글을 Blogger에도 동시에 자동 발행한다 (설정 안 돼 있으면 조용히 건너뜀).
  2026-09-20부터: 클러스터 D(트러블슈팅) 글만 new-maind가 아니라 같은
  구글 계정 소유의 별도 블로그(SECOND_BLOG_URL,
  simple-tech-fix.blogspot.com)로 보낸다 - 블로그 이름/니치가 잘 맞고
  같은 글이 두 블로그에 중복 발행되는 걸 피하기 위해서다. GitHub
  Pages(docs/_posts)는 이 분기와 무관하게 항상 전체 클러스터를 보관하는
  단일 아카이브로 남는다 (resolve_blog_id_by_url() 참고).
- 이미지는 Unsplash 일반 스톡사진 대신, Claude가 SOURCES로 알려준 공식
  페이지(가격/지원문서 등, 로그인 불필요)를 Playwright로 직접 캡처해서
  쓴다 - "직접 제작/캡처/AI생성/명확한 라이선스만" 원칙상 소프트웨어
  화면 캡처 자리에 무관한 스톡사진을 쓸 수 없어서다. 로그인이 필요하거나
  캡처가 실패하면 그 자리는 조용히 건너뛰고, 캡처된 화면이 하나도 없을
  때만 Unsplash 사진 1장을 대표 이미지로 대신 쓴다 (build_screenshot_photos
  참고). 제품 지정 발행(manual, 현재는 쓰이지 않지만 기능은 남겨둠) 글은
  기존처럼 Unsplash나 실제 제품 이미지를 그대로 쓴다.
- 애드센스 "가치가 별로 없는 콘텐츠" 판정 이후 매일 발행 대신 화/일을
  휴무일로 두고 주 5회만 발행한다 (REST_WEEKDAYS).
"""

import datetime
import json
import os
import random
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

TOPICS_FILE = PROJECT_DIR / "data" / "topics.json"
# 최근에 어떤 topics.json 항목(id)을 썼는지 남겨두는 상태 파일. select_niche_topic()
# 참고 - 풀(30개)을 거의 다 돌기 전까지 같은 주제가 다시 나오지 않게 한다.
USED_TOPIC_IDS_FILE = PROJECT_DIR / "data" / "used_topic_ids.json"
USED_TOPIC_IDS_KEEP = 20
POSTS_DIR = DOCS_DIR / "_posts"

# 특정 제품(예: 쿠팡파트너스 딥링크가 있는 제품)에 대해 한 번만 글을 쓰고
# 싶을 때 쓰는 수동 오버라이드 파일 (현재는 새 니치와 맞는 제품이 없어 쓰이지
# 않지만, 나중에 필요해질 수 있어 기능은 남겨둔다). 있으면 이번 실행은 평소
# 큐(topics.json)를 건드리지 않고 이 파일 내용으로만 글을 쓴 뒤, 다 쓰고 나면
# 파일을 지워서 다음 실행부터는 다시 평소 큐로 돌아간다. 필수 키:
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

# 클러스터별 발행 우선순위 가중치. "단순 How-to보다 비교/대안형 콘텐츠를
# 우선한다"는 전략에 따라: D(트러블슈팅, 경쟁도 낮아 최우선) > C/E(비교·대안,
# 광고 친화적이고 AI Overview 노출이 적은 구매의도 검색) > B(생산성/자동화,
# 트렌드 일부 포함) > A(순수 실사용 가이드, AI Overview에 CTR이 가장 많이
# 깎이는 단순 정보성 How-to라 가장 낮은 가중치).
NICHE_CLUSTER_WEIGHT = {"A": 1, "B": 2, "C": 4, "D": 5, "E": 4}


def load_niche_topics() -> list[dict]:
    """data/topics.json의 고정 30개 키워드 풀을 읽어온다. 각 항목은
    id/cluster/cluster_name/keyword/format/content_type을 갖는다."""
    if not TOPICS_FILE.exists():
        sys.exit(f"주제 풀 파일이 없습니다: {TOPICS_FILE}")
    try:
        topics = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"주제 풀 파일이 올바른 JSON이 아닙니다: {TOPICS_FILE}: {e}")
    if not isinstance(topics, list) or not topics:
        sys.exit(f"주제 풀이 비어 있습니다: {TOPICS_FILE}")
    return topics


def load_used_topic_ids() -> list[str]:
    if not USED_TOPIC_IDS_FILE.exists():
        return []
    try:
        ids = json.loads(USED_TOPIC_IDS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return ids if isinstance(ids, list) else []


def save_used_topic_id(topic_id: str) -> None:
    """이번에 고른 주제 id를 사용 기록에 남긴다. USED_TOPIC_IDS_KEEP개를
    넘으면 오래된 것부터 잘라내서, 풀(30개)을 거의 다 돌면 다시 등장할
    수 있게 한다 (영구히 다시 안 나오게 막지 않는다 - 결국 콘텐츠는
    새로고침이 필요해질 수 있어서)."""
    used = load_used_topic_ids()
    used = [i for i in used if i != topic_id] + [topic_id]
    used = used[-USED_TOPIC_IDS_KEEP:]
    USED_TOPIC_IDS_FILE.write_text(json.dumps(used, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def select_niche_topic() -> dict:
    """topics.json 30개 중 하나를 클러스터 가중치(NICHE_CLUSTER_WEIGHT) 기반
    가중 무작위로 고른다. 최근에 쓴 주제(used_topic_ids.json)는 먼저
    제외하고 고르되, 풀을 거의 다 써서 후보가 하나도 안 남으면 전체
    풀에서 다시 고른다(콘텐츠는 결국 새로고침할 수 있으니 영구 배제는
    아니다). 선택한 주제의 id는 main()이 발행에 성공한 뒤에
    save_used_topic_id()로 기록한다(여기서는 기록하지 않는다 - 실패한
    회차까지 "사용됨"으로 남으면 안 되므로)."""
    topics = load_niche_topics()
    used_ids = set(load_used_topic_ids())

    candidates = [t for t in topics if t["id"] not in used_ids] or topics
    weights = [NICHE_CLUSTER_WEIGHT.get(t["cluster"], 1) for t in candidates]
    chosen = random.choices(candidates, weights=weights, k=1)[0]
    print(
        f"오늘의 주제 선택: [{chosen['cluster']}] {chosen['cluster_name']} / "
        f"{chosen['keyword']} (포맷: {chosen['format']})"
    )
    return chosen


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
    select_niche_topic() 풀을 그대로 쓴다). 실제 삭제/재기록은 main()에서
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


# 애드센스 "가치가 별로 없는 콘텐츠" 판정 이후, 매일 발행 대신 발행 빈도를
# 줄이고 글 하나의 완성도를 높이기로 했다. 화요일/일요일은 발행을 건너뛴다
# (주 5회 발행). 요일 고정이라 별도 상태 파일 없이 재실행해도 같은
# 결과가 나온다.
REST_WEEKDAYS = (1, 6)  # 화요일=1, 일요일=6


def build_product_prompt(manual: dict, recent_titles: list[str]) -> str:
    """load_manual_topic()으로 받은 특정 제품 정보를 바탕으로 글을 쓰게 하는
    프롬프트 (현재는 새 니치와 맞는 제품이 없어 쓰이지 않지만 기능은
    남겨둔다). TITLE/TAGS/IMAGE_QUERY/본문 형식이며, KEYWORD 대신 이미
    정해진 제휴 링크를 쓰므로 KEYWORD는 요구하지 않고, 실제 제품 사실
    (product_info)만 근거로 쓰고 그 외 숫자는 지어내지 말라고 명시한다."""
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
(본문 마크다운. 1800~2200자 분량. 소제목(##) 3~4개.
먼저 이 주제를 고를 때 일반적으로 확인해야 할 기준을 체크리스트 형태로 자세히
설명하고, 자연스러운 흐름 속에서 위 제품 정보를 근거로 위 제품을 구체적으로
소개/추천해줘. 위에 안 나온 가격·리뷰수·사양 등 숫자는 절대 새로 지어내지 말고,
주어진 제품 정보 항목만 사실로 써 - 분량은 지어낸 숫자가 아니라 선택 기준
설명과 활용법을 더 자세히 풀어서 채워. 과장된 효능이나 확정적인 수익 약속은
절대 쓰지 마. 말투는 자연스러운 존댓말 블로그 톤으로.)
"""


def call_claude(prompt: str, enable_web_search: bool = False) -> str:
    """enable_web_search=True면 Claude의 서버 실행형 web_search 도구를 켜서,
    실제 검색 결과를 근거로 본문을 쓰게 한다 (건강/생활정보처럼 사실관계가
    중요한 정보성 글에서, 모델의 사전 지식만으로 지어내지 않도록 하기 위함).
    검색 도구가 쓰이면 응답 content에 텍스트 블록이 여러 개로 나뉠 수 있어서,
    첫 블록만 쓰지 않고 전부 이어붙인다."""
    client = anthropic.Anthropic()

    kwargs = dict(
        model=MODEL,
        max_tokens=6000 if enable_web_search else 4096,
        output_config={"effort": "medium"},
        system=(
            "You are the writer for an automated English-language blog about "
            "AI-powered productivity tools, software alternatives/comparisons, "
            "and remote-work tool troubleshooting, aimed at a US audience. "
            "Write in natural, native-sounding American English - never a stiff "
            "or translated tone. Base every claim on verified facts (use web "
            "search for anything time-sensitive like pricing, plans, or feature "
            "availability); never invent numbers, features, or pricing. Never "
            "copy or closely paraphrase another blog, article, or review site - "
            "synthesize your own original explanation from what you find. Do "
            "not pad the post with filler just to hit a word count; be concise "
            "and useful."
        ),
        messages=[{"role": "user", "content": prompt}],
    )
    if enable_web_search:
        kwargs["tools"] = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}]

    try:
        response = client.messages.create(**kwargs)
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

    text_parts = [block.text for block in response.content if block.type == "text"]
    if not text_parts:
        sys.exit("응답에 텍스트 콘텐츠가 없습니다.")
    return "\n".join(text_parts)


def _find_field_match(text: str, label: str) -> re.Match | None:
    pattern = rf"^\s*[*_]{{0,2}}{re.escape(label)}[*_]{{0,2}}\s*[:：]\s*(.+?)\s*$"
    return re.search(pattern, text, re.MULTILINE | re.IGNORECASE)


def _find_field(text: str, label: str) -> str:
    """text에서 "LABEL: 값" 형태의 줄을 찾아 값만 돌려준다.

    AI가 형식을 완전히 똑같이 지키지 않는 경우(라벨을 **굵게** 쓰거나,
    콜론 앞에 공백을 넣거나, 전각 콜론 "："을 쓰는 등)에도 인식하도록
    관대하게 매칭한다. 못 찾으면 빈 문자열을 돌려준다.
    """
    match = _find_field_match(text, label)
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

    # 웹 검색 도구를 켜고 부른 경우, 실제 형식(TITLE/TAGS/...) 앞에 검색
    # 과정에 대한 설명이 붙는 경우가 있다. 그냥 텍스트에서 처음 나오는
    # "---"로 자르면, 그 설명 안에 우연히 "---"가 있을 때 본문이 엉뚱한
    # 위치에서 잘릴 수 있다. 그래서 마지막으로 인식된 필드 줄 "이후"에서만
    # 구분선을 찾는다.
    anchor = 0
    for label in ("IMAGE_QUERY", "KEYWORD", "TAGS", "TITLE"):
        match = _find_field_match(text, label)
        if match:
            anchor = match.end()
            break

    separator = re.search(r"^[ \t]*-{3,}[ \t]*$", text[anchor:], re.MULTILINE)
    if separator:
        body = text[anchor + separator.end():].strip()
    else:
        body = text[anchor:].strip() if anchor else text.strip()

    return title, tags, keyword, image_query, body


def parse_niche_output(text: str, fallback_title: str = "") -> tuple[str, str, str, list[str], str]:
    """새 니치(AI Productivity Tools) 포맷 프롬프트(build_how_to_prompt 등)의
    출력을 파싱한다. parse_output()과 같은 관대한 필드 매칭을 쓰되, KEYWORD
    대신 SOURCES(파이프로 구분된 공식 출처 URL 목록)를 추가로 받는다 - 이
    URL들은 본문 인용 출처이자 스크린샷 캡처 대상으로 같이 쓰인다
    (build_screenshot_photos 참고)."""
    title = _find_field(text, "TITLE") or fallback_title or "Untitled Post"
    tags = _find_field(text, "TAGS")
    keyword = _find_field(text, "KEYWORD")
    sources_raw = _find_field(text, "SOURCES")
    sources = [s.strip() for s in re.split(r"[|,]", sources_raw) if s.strip().lower().startswith("http")]

    anchor = 0
    for label in ("SOURCES", "KEYWORD", "TAGS", "TITLE"):
        match = _find_field_match(text, label)
        if match:
            anchor = match.end()
            break

    separator = re.search(r"^[ \t]*-{3,}[ \t]*$", text[anchor:], re.MULTILINE)
    if separator:
        body = text[anchor + separator.end():].strip()
    else:
        body = text[anchor:].strip() if anchor else text.strip()

    return title, tags, keyword, sources, body


# 4개 포맷 프롬프트 빌더가 공통으로 요구하는 출력 필드 형식. TITLE/TAGS/
# KEYWORD는 예전 포맷과 같은 자리에, SOURCES(파이프로 구분된 실제 인용
# URL 2~4개)가 새로 추가됐다 - 이 URL은 본문에서 공식 출처로 인용될 뿐
# 아니라, 로그인 없이 볼 수 있는 공개 페이지라면 그대로 Playwright
# 스크린샷 캡처 대상으로도 쓰인다(build_screenshot_photos 참고).
OUTPUT_FORMAT_BLOCK = """Output format (follow exactly):
TITLE: (a specific, SEO-friendly English title, under 60 characters, no clickbait)
TAGS: (3-5 comma-separated tags)
KEYWORD: (the single primary target keyword/phrase for this post)
SOURCES: (2-4 official URLs you actually used and are citing, separated by " | " - \
each must be the vendor's own official domain, e.g. a pricing or support page, \
never a third-party review/roundup site)
---
(the post body in Markdown, following the structure above)"""


def _niche_avoid_block(recent_titles: list[str]) -> str:
    if not recent_titles:
        return ""
    recent_list = "\n".join(f"- {t}" for t in recent_titles)
    return f"\nDo not repeat these already-published titles/topics:\n{recent_list}\n"


def build_how_to_prompt(topic: dict, recent_titles: list[str]) -> str:
    """How-to 포맷(클러스터 A/B): AI 도구 실사용 가이드 / 생산성·자동화 가이드.
    AI Overview가 단순 정보성 How-to 검색의 CTR을 크게 깎아먹는다는 신호가
    있어서 다른 포맷보다 발행 우선순위(NICHE_CLUSTER_WEIGHT)는 낮지만, 니치
    구성상 필요한 축이라 계속 발행한다."""
    return f"""You are writing a how-to guide for an English-language blog about AI-powered productivity tools, for a US audience.

Target keyword/topic: "{topic['keyword']}"
{_niche_avoid_block(recent_titles)}
Use web search to confirm current steps, UI labels, and feature availability before writing - tools change their interface often, and a stale step-by-step guide is worse than none. Never invent a step, button name, or menu label you haven't verified.

Structure (in this order):
1. A direct answer to the reader's question in the first 2-3 sentences - no throat-clearing intro.
2. "What You'll Need" - a short list of prerequisites (account, plan tier, browser, etc.), only if genuinely needed.
3. Step-by-step instructions, with clear numbered steps or ## subheadings per step.
4. A short FAQ (2-4 questions) addressing likely follow-up questions.
5. A brief wrap-up (2-3 sentences).

Length: about 900-1300 words. Be concise - don't pad steps with filler just to hit a word count.

Tone: natural, native American English, plain and helpful - like a knowledgeable friend, not a stiff translated manual. No hype, no unverified claims about results or savings.

{OUTPUT_FORMAT_BLOCK}
"""


def build_alternative_prompt(topic: dict, recent_titles: list[str]) -> str:
    """Alternative 포맷(클러스터 C): 유료 툴의 무료/저가 대안 목록형 글."""
    return f"""You are writing a "best free alternatives" guide for an English-language blog about AI-powered productivity tools, for a US audience.

Target keyword/topic: "{topic['keyword']}"
{_niche_avoid_block(recent_titles)}
Use web search to confirm each tool's CURRENT pricing, free-tier limits, and core features - these change often and a stale price is worse than none.

Structure (in this order):
1. A direct answer up front: name the single best pick and 1-2 runners-up in the first 2-3 sentences.
2. "How We Picked" - the selection criteria used (price, features, ease of use, etc.), as 3-5 short bullet points.
3. A rundown of each alternative (3-5 tools), one ## subheading per tool, covering what it's good for and its real free-tier limits.
4. A Markdown comparison table summarizing price, key limitation, and best-for across all tools listed.
5. A short FAQ (2-4 questions).

You must cite each tool's OFFICIAL pricing page in SOURCES - not a review site or a "best of" roundup article. These must be links to each vendor's own domain (e.g. canva.com/pricing, notion.so/pricing).

Length: about 1000-1400 words.

Tone: natural, native American English, plain and helpful. No hype, no unverified claims.

{OUTPUT_FORMAT_BLOCK}
"""


def build_troubleshoot_prompt(topic: dict, recent_titles: list[str]) -> str:
    """Troubleshoot 포맷(클러스터 D): 원격근무 툴 오류 해결. 경쟁도가 낮아
    NICHE_CLUSTER_WEIGHT에서 가장 우선순위를 높게 둔 축이다."""
    return f"""You are writing a troubleshooting guide for an English-language blog about remote-work software problems, for a US audience.

Target keyword/topic: "{topic['keyword']}"
{_niche_avoid_block(recent_titles)}
Use web search to confirm the CURRENT fix against the tool's own official support/help-center pages - UI labels and settings menus change often, and a stale fix is worse than none.

Structure (in this order):
1. A direct answer: the single most common fix, in the first 1-2 sentences. People searching an error want the fix fast.
2. "Why This Happens" - the likely causes, briefly.
3. Step-by-step fixes, ordered from the quickest/most common fix to less common ones.
4. "How to Prevent It Next Time" - a short prevention section.

You must cite the tool's own OFFICIAL support/help-center page in SOURCES (e.g. support.zoom.us, support.google.com) - not a random forum or third-party tech blog.

Length: about 700-1000 words. Troubleshooting readers want the fix fast - don't pad this out.

Tone: natural, native American English, plain and direct.

{OUTPUT_FORMAT_BLOCK}
"""


def build_comparison_prompt(topic: dict, recent_titles: list[str]) -> str:
    """Comparison 포맷(클러스터 E): 생산성 소프트웨어 정면 비교. 광고
    친화적이고 AI Overview 노출이 적은 구매의도 검색이라 우선순위가 높다."""
    return f"""You are writing a head-to-head software comparison for an English-language blog about productivity tools, for a US audience.

Target keyword/topic: "{topic['keyword']}"
{_niche_avoid_block(recent_titles)}
Use web search to confirm both tools' CURRENT pricing, plans, and key features directly from their own official pages.

Structure (in this order):
1. A direct answer: a 2-3 sentence verdict summary right away - which tool wins and for whom.
2. A Markdown comparison table across price, core features, and target user.
3. Item-by-item analysis: ## subheadings for 3-4 key dimensions (e.g. pricing, ease of use, a key feature difference, collaboration/integrations), comparing both tools directly in each.
4. "Who Should Use Which" - map user type to recommendation.
5. A short FAQ (2-4 questions).

You must cite each company's own OFFICIAL pricing/spec page in SOURCES (both companies, not a third-party comparison site).

Length: about 1100-1500 words.

Tone: natural, native American English, confident but fair to both sides - no hype, no unverified claims.

{OUTPUT_FORMAT_BLOCK}
"""


NICHE_FORMAT_PROMPT_BUILDERS = {
    "how_to": build_how_to_prompt,
    "alternative": build_alternative_prompt,
    "troubleshoot": build_troubleshoot_prompt,
    "comparison": build_comparison_prompt,
}


def build_manual_affiliate_block(manual: dict) -> str:
    """load_manual_topic()으로 받은, 이미 정해진 실제 쿠팡파트너스 링크(또는 배너
    HTML)를 그대로 쓴다 (현재는 새 니치와 맞는 제품이 없어 쓰이지 않지만
    기능은 남겨둔다).

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


def _search_unsplash_photos(query: str, count: int) -> list[dict]:
    """Unsplash에서 query에 맞는 무료 사진을 최대 count장 찾아 정보를 돌려준다.
    설정이 없거나 실패하면 빈 리스트를 돌려주고, 절대 sys.exit 하지 않는다
    (이미지는 있으면 좋은 부가 기능이지, 없다고 글 발행 자체를 막으면 안 된다)."""
    if not UNSPLASH_ACCESS_KEY or not query:
        return []

    params = urllib.parse.urlencode({"query": query, "per_page": count, "orientation": "landscape"})
    req = urllib.request.Request(
        f"https://api.unsplash.com/search/photos?{params}",
        headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read())
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
        print(f"Unsplash 사진 검색 실패, 이미지 없이 계속합니다: {e}")
        return []

    results = (payload.get("results") or [])[:count]
    if not results:
        print(f"Unsplash에서 '{query}'에 맞는 사진을 못 찾았습니다, 이미지 없이 계속합니다.")
        return []

    photos = []
    for photo in results:
        # Unsplash API 가이드라인상, 실제로 사진을 쓸 때는 download_location을
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

        photos.append(
            {
                "url": (photo.get("urls") or {}).get("regular", ""),
                "alt": photo.get("alt_description") or query,
                "photographer_name": (photo.get("user") or {}).get("name", "Unsplash"),
                "photographer_url": (photo.get("user") or {}).get("links", {}).get("html", "https://unsplash.com"),
            }
        )
    return [p for p in photos if p["url"]]


def find_stock_photo(query: str) -> dict | None:
    photos = _search_unsplash_photos(query, 1)
    return photos[0] if photos else None


def find_stock_photos(query: str, count: int = 5) -> list[dict]:
    """정보성 글에 여러 장(기본 최대 5장)을 배치하기 위한 버전."""
    return _search_unsplash_photos(query, count)


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


def distribute_images_into_body(
    body: str, photos: list[dict], block_builder=build_image_block
) -> str:
    """본문에 사진 여러 장을 흩어 배치한다: 첫 장은 글 맨 위, 나머지는 각
    소제목(##) 바로 아래에 하나씩. 소제목보다 사진이 많으면 남는 사진은
    버리고, 사진이 없으면 원래 본문을 그대로 돌려준다. block_builder로
    사진 한 장을 마크다운 블록으로 렌더링하는 함수를 바꿔 끼울 수 있다
    (기본은 Unsplash용 build_image_block, 새 니치는 build_niche_image_block
    을 넘긴다 - 스크린샷/Unsplash를 섞어서 렌더링해야 해서)."""
    if not photos:
        return body

    photo_iter = iter(photos)
    top_photo = next(photo_iter, None)

    lines = body.split("\n")
    out = []
    for line in lines:
        out.append(line)
        if line.startswith("## "):
            next_photo = next(photo_iter, None)
            if next_photo:
                out.append("")
                out.append(block_builder(next_photo).rstrip("\n"))

    result = "\n".join(out)
    return (block_builder(top_photo) if top_photo else "") + result


# 새 니치는 소프트웨어 화면 캡처가 필요한데, "직접 제작/캡처/AI생성/명확한
# 라이선스만" 원칙상 Unsplash 일반 스톡사진을 화면 캡처 자리에 쓸 수 없다.
# 그래서 Claude가 SOURCES로 알려준 공식 페이지(가격/지원문서 등, 로그인
# 불필요)를 Playwright로 우리가 직접 캡처해서 쓴다. 로그인이 필요한 실제
# 사용 화면(예: 채팅 내용)은 계정 자동화 없이는 캡처할 수 없어서 시도하지
# 않고, 캡처가 실패하거나 하나도 없을 때만 Unsplash로 대체한다.
SCREENSHOTS_ASSET_DIR = DOCS_DIR / "assets" / "img"
# GitHub Pages 배포 URL (auto-blog-autopilot/README.md 참고) - Jekyll
# markdown과 Blogger HTML 양쪽에서 그대로 쓸 수 있는 절대 URL이 필요해서
# site.baseurl 같은 상대 경로 태그 대신 이 값을 직접 붙인다.
SITE_BASE_URL = "https://afroditena.github.io/mattress-checklist-android"
# 기본은 비워둔다 - Playwright가 자기가 설치한 브라우저를 스스로 찾게 둔다
# (워크플로가 매번 `playwright install chromium`으로 설치하므로 GitHub
# Actions에서는 이게 정답이다). 특수한 환경(예: 브라우저가 표준 캐시 경로가
# 아닌 곳에 미리 설치돼 있고 pip playwright 버전과 리비전이 안 맞는 경우)
# 에서만 PLAYWRIGHT_CHROMIUM_PATH 환경변수로 실행 파일 경로를 직접 지정해서
# 오버라이드한다.
PLAYWRIGHT_CHROMIUM_PATH = os.environ.get("PLAYWRIGHT_CHROMIUM_PATH", "")


def capture_page_screenshot(url: str, out_path: Path) -> bool:
    """로그인 없이 볼 수 있는 공개 페이지 하나를 Playwright(headless Chromium)로
    그대로 캡처해서 out_path에 PNG로 저장한다. playwright 미설치, 접속 실패,
    타임아웃 등 어떤 이유로든 실패하면 조용히 False를 돌려준다 - 캡처
    실패가 발행 자체를 막으면 안 되고, 호출부가 Unsplash 등으로 대체한다."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright가 설치돼 있지 않아 화면 캡처를 건너뜁니다.")
        return False

    try:
        with sync_playwright() as p:
            launch_kwargs = {"headless": True}
            if PLAYWRIGHT_CHROMIUM_PATH:
                launch_kwargs["executable_path"] = PLAYWRIGHT_CHROMIUM_PATH
            browser = p.chromium.launch(**launch_kwargs)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 800})
                page.goto(url, timeout=20000, wait_until="load")
                page.wait_for_timeout(1500)  # 지연 로딩되는 요소 대기
                out_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(out_path))
            finally:
                browser.close()
        return out_path.exists() and out_path.stat().st_size > 0
    except Exception as e:
        print(f"화면 캡처 실패({url}): {e}")
        return False


def build_screenshot_photos(sources: list[str], slug: str) -> list[dict]:
    """SOURCES로 받은 공식 페이지 URL들을 직접 캡처해서, docs/assets/img/<slug>/
    에 저장하고 절대 URL과 함께 사진 dict 목록으로 돌려준다(로그인이 필요하거나
    캡처가 실패한 URL은 조용히 건너뜀). 이 파일들은 main()이 성공적으로 글을
    쓴 뒤 GitHub Actions 워크플로가 docs/assets와 함께 커밋해야 실제로
    남는다(워크플로 git add 단계 참고) - 커밋 안 되면 캡처만 되고 다음 실행
    때 사라진다."""
    photos = []
    for i, url in enumerate(sources[:5], start=1):
        out_path = SCREENSHOTS_ASSET_DIR / slug / f"{i}.png"
        if not capture_page_screenshot(url, out_path):
            continue
        domain = urllib.parse.urlparse(url).netloc.replace("www.", "")
        rel = out_path.relative_to(DOCS_DIR).as_posix()
        photos.append(
            {
                "kind": "screenshot",
                "url": f"{SITE_BASE_URL}/{rel}",
                "alt": f"{domain} official page screenshot",
                "source_name": domain,
                "source_url": url,
            }
        )
    return photos


def build_niche_image_block(photo: dict | None) -> str:
    """새 니치용 이미지 블록 렌더러. photo["kind"]가 "screenshot"이면
    build_screenshot_photos()가 만든 실제 화면 캡처를 캡션과 함께 넣고,
    그 외(Unsplash 대체 사진)에는 build_image_block()과 같은 출처 표기를
    쓴다. distribute_images_into_body()에 block_builder로 넘겨서 스크린샷과
    Unsplash 대체 사진이 섞여 있어도 한 함수로 렌더링할 수 있게 한다."""
    if not photo or not photo.get("url"):
        return ""

    if photo.get("kind") == "screenshot":
        alt = photo.get("alt", "screenshot")
        source_name = photo.get("source_name", "the official site")
        source_url = photo.get("source_url", "")
        caption = f"*Screenshot of {source_name}" + (f" ([source]({source_url}))" if source_url else "") + "*"
        return f"![{alt}]({photo['url']})\n{caption}\n\n"

    return build_image_block(photo)


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


def post_to_blogger(title: str, body_markdown: str, blog_id: str | None = None) -> None:
    """설정돼 있으면 같은 글을 구글 Blogger에도 발행한다. blog_id를 안 주면
    기본 블로그(BLOGGER_BLOG_ID, new-maind)에 발행한다 - 클러스터 D
    (트러블슈팅) 글을 두 번째 블로그(SECOND_BLOG_URL)에 발행할 때는
    resolve_blog_id_by_url()로 알아낸 id를 넘긴다 (main() 참고). 실패해도
    GitHub Pages 발행 자체를 막지 않도록, 여기서 나는 오류는 절대 sys.exit
    하지 않고 그냥 건너뛴다."""
    if not blogger_configured():
        print("Blogger 인증 정보가 없어 Blogger 발행은 건너뜁니다.")
        return

    target_blog_id = blog_id or BLOGGER_BLOG_ID

    try:
        access_token = get_google_access_token()
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, ValueError) as e:
        print(f"Blogger 액세스 토큰 갱신 실패, 이번 회차는 건너뜁니다: {e}")
        return

    payload = json.dumps({"title": title, "content": markdown_to_html(body_markdown)}).encode("utf-8")
    url = f"https://www.googleapis.com/blogger/v3/blogs/{target_blog_id}/posts/"
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


# 클러스터 D(Remote-Work Tool Troubleshooting) 글은 new-maind가 아니라 같은
# 구글 계정 소유의 별도 블로그로 보낸다 - 블로그 이름·니치가 잘 맞고, 같은
# 글을 두 블로그에 중복 발행하면 애드센스가 "중복 콘텐츠"로 볼 위험도 피할
# 수 있다. GitHub Pages(docs/_posts)는 이 분기와 무관하게 항상 전체
# 클러스터를 그대로 보관하는 단일 아카이브로 남는다.
SECOND_BLOG_URL = "https://simple-tech-fix.blogspot.com/"


def resolve_blog_id_by_url(blog_url: str) -> str | None:
    """블로그 URL로 Blogger 블로그 ID를 조회한다. 같은 구글 계정(그래서
    GOOGLE_REFRESH_TOKEN이 이미 접근 권한을 가짐) 소유 블로그라면 별도
    시크릿 설정 없이 기존 Blogger 인증 정보로 조회할 수 있다. 실패(권한
    없음/네트워크 오류/미설정 등)하면 None을 돌려주고, 호출부가 해당
    발행만 조용히 건너뛴다."""
    if not blogger_configured():
        return None

    try:
        access_token = get_google_access_token()
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, ValueError) as e:
        print(f"{blog_url} 블로그 ID 조회를 위한 토큰 갱신 실패: {e}")
        return None

    url = f"https://www.googleapis.com/blogger/v3/blogs/byurl?url={urllib.parse.quote(blog_url, safe='')}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read())
        blog_id = payload.get("id")
        if not blog_id:
            print(f"{blog_url}의 블로그 ID를 응답에서 찾지 못했습니다: {payload}")
        return blog_id
    except urllib.error.HTTPError as e:
        print(f"{blog_url} 블로그 ID 조회 실패: {e.code} {e.reason}: {e.read().decode('utf-8', 'replace')}")
        return None
    except urllib.error.URLError as e:
        print(f"{blog_url} 블로그 ID 조회 실패: {e}")
        return None


BLOGGER_PRIVACY_PAGE_TITLE = "Privacy Policy"
BLOGGER_ABOUT_PAGE_TITLE = "About"

BLOGGER_PRIVACY_PAGE_MD = """\
This page explains what information is collected from visitors to this blog and how it's used.

## 1. Cookies and Visit Data

This blog may use Google Analytics to analyze visit statistics. Google Analytics uses cookies to collect non-identifying statistics such as pages visited, time on page, and device type. It does not collect personally identifying information (name, contact details, etc.).

## 2. Advertising

This blog may display third-party ads, including Google AdSense. Google and other ad providers may use cookies to show personalized ads based on your prior visits.

- You can learn how Google uses cookies for advertising at the [Google Ads Policy](https://policies.google.com/technologies/ads) page.
- You can opt out of personalized ads at [Google Ads Settings](https://adssettings.google.com).

## 3. Content and How It's Made

This blog is run by a single independent operator, and posts are written with the help of AI automation tools. The operator decides what topics to cover and takes final responsibility for what gets published. For claims that can change over time - software pricing, plans, and feature availability - the writing process confirms current facts with web search before publishing, and cites the vendor's own official page as a source rather than a third-party summary.

## 4. Affiliate Disclosure

This blog currently carries no affiliate or referral links. If that changes in the future, any affiliate relationship will be disclosed directly in the relevant post and reflected here.

## 5. Contact

If you have questions about this privacy policy or how this blog is run, please leave a comment on any post.

## 6. Changes

This policy may change as the service or applicable law changes; updates will be reflected on this page.
"""

BLOGGER_ABOUT_PAGE_MD_TEMPLATE = """\
## What This Blog Covers

This blog covers AI-powered productivity tools: practical guides for tools like ChatGPT and Claude, free/budget alternatives to popular software, fixes for common remote-work tool problems (Zoom, Google Meet, Google Drive, Slack, Notion, Google Docs), and head-to-head comparisons of productivity software.

## About the Operator

This blog is run by a single independent operator. The operator decides what topics to cover and when to publish, and the writing process uses AI automation tools. Final responsibility for what's published - and whether it's accurate - rests with the operator, not the AI. Posts are published a few days a week rather than daily, to keep the focus on quality over volume.

## How Content Is Made

- Every post is fact-checked with web search before publishing, especially for anything that changes over time, like software pricing, plans, or feature availability.
- Official vendor pages (pricing pages, support/help-center pages) are cited directly as sources rather than summarizing third-party reviews.
- Screenshots used in posts are captured directly from the official public pages being discussed; posts don't reuse other sites' or blogs' images.
- Posts aim to be useful and specific rather than padded out to hit a word count.

This blog currently carries no affiliate or referral links. See the [Privacy Policy]({privacy_url}) page for more detail.

## Contact

Questions or feedback about this blog can be left as a comment on any post.
"""


def sync_blogger_static_pages() -> None:
    """개인정보처리방침·소개 페이지를 Blogger에도 만들어 두고, 이미 있으면
    최신 내용으로 갱신한다(제목 기준으로 찾아 PATCH) - 그래서 이 콘텐츠를
    바꿀 때마다 다음 발행 때 Blogger 쪽도 자동으로 맞춰진다. 애드센스는
    실제로 신청하는 도메인(Blogger)에 이 페이지들이 있어야 심사가 되므로,
    GitHub Pages(docs/privacy.md, docs/about.md)와 같은 내용을 유지한다.
    실패해도 본 발행 흐름을 막지 않는다."""
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

    def _upsert_page(title: str, body_markdown: str) -> str | None:
        content = markdown_to_html(body_markdown)
        existing_page = existing_by_title.get(title)
        if existing_page:
            page_id = existing_page["id"]
            url = f"{pages_url}{page_id}"
            method, verb = "PATCH", "갱신"
        else:
            url = pages_url
            method, verb = "POST", "생성"
        payload = json.dumps({"title": title, "content": content}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
            page_url = result.get("url") or (existing_page or {}).get("url")
            print(f"Blogger {title} 페이지 {verb} 완료: {page_url}")
            return page_url
        except urllib.error.HTTPError as e:
            print(f"Blogger {title} 페이지 {verb} 실패: {e.code} {e.reason}: {e.read().decode('utf-8', 'replace')}")
        except urllib.error.URLError as e:
            print(f"Blogger {title} 페이지 {verb} 실패: {e}")
        return (existing_page or {}).get("url")

    privacy_url = _upsert_page(BLOGGER_PRIVACY_PAGE_TITLE, BLOGGER_PRIVACY_PAGE_MD)

    about_md = BLOGGER_ABOUT_PAGE_MD_TEMPLATE.format(privacy_url=privacy_url or "https://www.blogger.com")
    _upsert_page(BLOGGER_ABOUT_PAGE_TITLE, about_md)


def fix_known_post_title() -> None:
    """일회성 유지보수: 2026-08-21 발행 글이 AI 응답 파싱 실패로 폴백 제목
    ("자동 생성 포스트")을 그대로 달고 나간 버그를 GitHub Pages 파일과
    Blogger 글 양쪽에서 바로잡는다. 내용 자체는 정상(여름철 반려동물
    시간대별 관리 팁)이라 제목만 고치면 된다.

    이미 고쳐져 있으면(해당 파일이 없으면) 조용히 넘어가므로 여러 번
    실행해도 안전하다. RUN_FIX_KNOWN_POST_TITLE=true 환경변수로만
    실행되는 일회성 경로라, 평소 매일 발행 흐름에는 전혀 영향이 없다."""
    OLD_TITLE = "자동 생성 포스트"
    NEW_TITLE = "여름철 반려동물 관리, 아침·낮·저녁 시간대별로 나눠서 확인하기"
    OLD_SLUG_PREFIX = "2026-08-21"

    old_path = None
    for candidate in POSTS_DIR.glob(f"{OLD_SLUG_PREFIX}-*.md"):
        if f'title: "{OLD_TITLE}"' in candidate.read_text(encoding="utf-8"):
            old_path = candidate
            break

    if old_path is None:
        print(f"'{OLD_TITLE}' 제목의 글을 찾지 못했습니다 (이미 고쳐졌거나 파일이 없음) - 건너뜁니다.")
    else:
        text = old_path.read_text(encoding="utf-8")
        fixed = text.replace(f'title: "{OLD_TITLE}"', f'title: "{NEW_TITLE}"', 1)
        new_path = POSTS_DIR / f"{OLD_SLUG_PREFIX}-{slugify(NEW_TITLE)}.md"
        new_path.write_text(fixed, encoding="utf-8")
        if new_path != old_path:
            old_path.unlink()
        print(f"GitHub Pages 파일 수정 완료: {old_path.name} -> {new_path.name}")

    if not blogger_configured():
        print("Blogger 인증 정보가 없어 Blogger 쪽 제목 수정은 건너뜁니다.")
        return

    try:
        access_token = get_google_access_token()
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, ValueError) as e:
        print(f"Blogger 액세스 토큰 갱신 실패, Blogger 쪽 제목 수정을 건너뜁니다: {e}")
        return

    headers = {"Authorization": f"Bearer {access_token}"}
    # posts.search는 한글 제목을 토큰화해서 매칭하는 방식이라 정확한 문구를
    # 못 찾는 경우가 있었다(실제로 이 글을 못 찾는 게 확인됨). 발행일을
    # 정확히 알고 있으니, search 대신 그날 하루치 글 목록을 날짜로 걸러서
    # 제목을 직접 비교하는 방식이 훨씬 안정적이다.
    list_url = (
        f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}/posts/"
        f"?startDate={urllib.parse.quote(f'{OLD_SLUG_PREFIX}T00:00:00+09:00')}"
        f"&endDate={urllib.parse.quote(f'{OLD_SLUG_PREFIX}T23:59:59+09:00')}"
        f"&fetchBodies=false&status=live"
    )
    try:
        req = urllib.request.Request(list_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            found = json.loads(resp.read()).get("items", []) or []
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"Blogger 글 목록 조회 실패, Blogger 쪽 제목 수정을 건너뜁니다: {e}")
        return

    matches = [p for p in found if p.get("title") == OLD_TITLE]
    if not matches:
        titles_that_day = [p.get("title") for p in found]
        print(
            f"Blogger에서 '{OLD_TITLE}' 제목의 글을 찾지 못했습니다 - 건너뜁니다. "
            f"({OLD_SLUG_PREFIX} 발행 글 목록: {titles_that_day})"
        )
        return

    for post in matches:
        post_id = post["id"]
        patch_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}/posts/{post_id}"
        payload = json.dumps({"title": NEW_TITLE}).encode("utf-8")
        req = urllib.request.Request(
            patch_url,
            data=payload,
            method="PATCH",
            headers={**headers, "Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
            print(f"Blogger 글 제목 수정 완료: {result.get('url', post_id)}")
        except urllib.error.HTTPError as e:
            print(f"Blogger 글 제목 수정 실패: {e.code} {e.reason}: {e.read().decode('utf-8', 'replace')}")
        except urllib.error.URLError as e:
            print(f"Blogger 글 제목 수정 실패: {e}")


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY 환경변수가 설정되어 있지 않습니다.")

    if os.environ.get("RUN_FIX_KNOWN_POST_TITLE") == "true":
        # 일회성 유지보수 모드: 정상 발행 흐름을 타지 않고 이 작업만 하고 끝낸다
        # (workflow_dispatch로만 켜지며, 매일 스케줄 실행에는 영향 없음).
        fix_known_post_title()
        return

    manual = load_manual_topic()
    recent_titles = get_recent_titles()

    # 요일 판정은 실행 시각(UTC)이 아니라 실제 발행되는 KST 기준이어야 한다 -
    # 이 워크플로는 22:00 UTC(=07:00 KST 다음날)에 돌기 때문에, UTC 그대로
    # 쓰면 요일이 하루 밀린다.
    kst_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

    if not manual and kst_now.weekday() in REST_WEEKDAYS:
        # 애드센스 "가치가 별로 없는 콘텐츠" 판정 이후 매일 발행 대신 발행
        # 빈도를 줄이기로 했다. 지정 발행(manual)은 예외로 그대로 진행하고,
        # 그 외 니치 글만 화/일에 건너뛴다. Claude API 호출 전에 바로
        # return해서 비용도 함께 아낀다.
        weekday_kr = "월화수목금토일"[kst_now.weekday()]
        print(f"오늘은 휴무일입니다 (KST {kst_now.date().isoformat()} {weekday_kr}요일) - 발행 빈도를 줄이고 품질에 집중하기 위해 이번 발행은 건너뜁니다.")
        return

    niche_topic = None
    if manual:
        topic = manual["topic"]
        prompt = build_product_prompt(manual, recent_titles)
    else:
        niche_topic = select_niche_topic()
        topic = niche_topic["keyword"]
        prompt_builder = NICHE_FORMAT_PROMPT_BUILDERS[niche_topic["format"]]
        prompt = prompt_builder(niche_topic, recent_titles)

    # manual(제품 지정 발행)만 web_search를 끈다 - 이미 실제로 주어진
    # product_info만 근거로 쓰게 돼 있어서 검색이 필요 없다. 새 니치 포맷은
    # 전부 가격/기능/오류 해결법 등 시점에 따라 바뀌는 사실을 다뤄서 검색이
    # 필수다.
    raw_output = call_claude(prompt, enable_web_search=not manual)

    if manual:
        title, tags, keyword, image_query, body = parse_output(raw_output, fallback_title=topic)
        sources = []
    else:
        title, tags, keyword, sources, body = parse_niche_output(raw_output, fallback_title=topic)

    today = datetime.date.today()
    slug = slugify(title)

    if manual and manual.get("affiliate_html"):
        # 제품 지정 발행: 무관한 Unsplash 스톡사진 대신, 이미 갖고 있는
        # 실제 상품 이미지(쿠팡 배너)를 대표 이미지로 쓴다.
        product_photo = extract_product_image(manual["affiliate_html"])
        image_block = build_product_image_block(product_photo)
        body = image_block + body
    elif manual:
        photo = find_stock_photo(image_query or keyword or topic)
        body = build_image_block(photo) + body
    else:
        # 새 니치: SOURCES로 받은 공식 페이지들을 직접 캡처해서 실제 화면
        # 스크린샷으로 쓴다("직접 제작/캡처/AI생성/명확한 라이선스만" 원칙 -
        # 소프트웨어 화면 자리에 무관한 Unsplash 스톡사진을 쓸 수 없어서다).
        # 로그인 필요/타임아웃 등으로 캡처가 하나도 성공하지 못했을 때만
        # Unsplash 사진 1장을 대표 이미지로 대신 쓴다.
        photos = build_screenshot_photos(sources, slug)
        if not photos:
            print("공식 페이지 캡처가 하나도 성공하지 못해 Unsplash 대표 이미지로 대신합니다.")
            stock = find_stock_photo(f"{niche_topic['cluster_name']} software" if niche_topic else keyword or topic)
            if stock:
                stock = dict(stock, kind="unsplash")
                photos = [stock]
        body = distribute_images_into_body(body, photos, block_builder=build_niche_image_block)

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
        # 특정 제품(쿠팡파트너스 링크) 지정 발행: 사용자가 날짜·제품·링크를
        # 직접 지정한 경우에만 실제 링크(또는 배너 HTML)를 그대로 쓴다.
        affiliate_block = build_manual_affiliate_block(manual)
    else:
        # 새 니치 글에는 현재 제휴/수익화 링크를 붙이지 않는다.
        affiliate_block = ""
    full_body = body + affiliate_block
    post_path.write_text(front_matter + "\n" + full_body, encoding="utf-8")

    print(f"생성 완료: {post_path.relative_to(PROJECT_DIR.parent)}")

    if not manual and niche_topic and niche_topic["cluster"] == "D":
        # 트러블슈팅 글은 new-maind가 아니라 두 번째 블로그로 보낸다
        # (SECOND_BLOG_URL 위 주석 참고).
        second_blog_id = resolve_blog_id_by_url(SECOND_BLOG_URL)
        if second_blog_id:
            post_to_blogger(safe_title, full_body, blog_id=second_blog_id)
        else:
            print(
                f"{SECOND_BLOG_URL} 블로그 ID를 찾지 못해 이번 트러블슈팅 글은 "
                "Blogger에 발행하지 못했습니다 (GitHub Pages에는 정상 발행됨)."
            )
    else:
        post_to_blogger(safe_title, full_body)
    sync_blogger_static_pages()

    if manual:
        consume_manual_topic(manual)
    else:
        save_used_topic_id(niche_topic["id"])


if __name__ == "__main__":
    main()
