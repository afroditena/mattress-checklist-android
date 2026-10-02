#!/usr/bin/env python3
"""
매일 GitHub Actions에서 실행되어 블로그 글 1편을 자동 생성하는 스크립트.

2026-09-18: 니치를 "AI-Powered Productivity Tools"(영어, 미국 독자 대상)로
완전히 전환했다. 이전 니치(매트리스/건강/재무/정치경제 핫이슈, 전부 한국어)는
폐기했고 관련 코드(select_topic의 Naver/GA4/pytrends 점수화, 핫이슈 프롬프트,
건강/금융 출처 블록 등)는 삭제했다 - 예전 발행글(docs/_posts의 한국어 글들)은
그대로 남아있지만 새 글은 전부 이 새 니치/포맷으로 나간다.

- data/topics.json 에 니치별 키워드 풀이 고정으로 들어있다: new-maind용
  A/B/C/E(각 6개, 총 24개) + simple-tech-fix용 T1/T2(2026-09-26부터 AI/테크
  논평, 총 20개 - SECOND_BLOG_CLUSTERS 참고). 매 실행마다 이 중 하나를
  클러스터 가중치 기반 가중 무작위로 고른다 - new-maind 쪽은 단순
  How-to(클러스터 A/B)보다 비교/대안형(C/E, 광고 친화적이고 AI Overview에
  덜 깎이는 검색 유형)을, simple-tech-fix 쪽은 AI Tool Verdicts(T1, 가중치
  3) > AI & Tech Trend Watch(T2, 가중치 2) 순으로 더 자주 고르도록
  클러스터별 가중치를 둔다(NICHE_CLUSTER_WEIGHT, select_niche_topic() 참고).
  최근 사용한 주제 id는 갈래별로 별도 파일(new-maind는
  data/used_topic_ids.json, simple-tech-fix는
  data/used_topic_ids_second_blog.json)에 남겨서, 각 풀을 거의 다 돌기
  전까지는 같은 주제가 다시 나오지 않게 한다 - 2026-09-30 이전엔 파일을
  공유해서, 발행 빈도가 3배 높은 simple-tech-fix가 20칸짜리 "최근 사용"
  기록을 빨리 채워버리는 바람에 new-maind가 8일 만에 같은 주제(Best Free
  Canva Alternatives)를 다시 뽑아 사실상 중복 글을 발행한 적이 있어
  분리했다.
- 최근에 쓴 글 제목들을 함께 넘겨서 내용이 겹치지 않게 한다.
- 포맷은 클러스터마다 다르게 정해져 있다: How-to(A/B), Alternative(C),
  Comparison(E), AI Commentary(T1/T2) - 각각 구조가 다른 프롬프트
  빌더로 글을 쓴다(build_how_to_prompt 등, NICHE_FORMAT_PROMPT_BUILDERS
  참고). 전부 Claude의 web_search 도구를 켜서, 실제 검색 결과(가격 페이지,
  공식 지원문서, 업계 리포트 등)를 근거로 쓰고 그 출처 URL도 SOURCES
  필드로 받는다 - 모델의 사전 지식만으로 지어내지 않도록.
- Claude API로 본문(영어)을 생성하고, docs/_posts/ 에 Jekyll 포스트
  파일로 저장한다.
- 구글 Blogger API 인증 정보(GOOGLE_CLIENT_ID 등)가 설정되어 있으면,
  같은 글을 Blogger에도 동시에 자동 발행한다 (설정 안 돼 있으면 조용히 건너뜀).
  2026-09-20부터: 클러스터 D(당시엔 트러블슈팅)는 아예 별도 갈래로
  분리됐다 - new-maind(BLOGGER_BLOG_ID)로 나가는 "일반 니치" 갈래는
  A/B/C/E만 후보로 삼고(화/일 휴무일 적용), 같은 구글 계정 소유의 별도
  블로그(SECOND_BLOG_URL, simple-tech-fix.blogspot.com)로 나가는 두 번째
  갈래가 그 나머지 클러스터만 후보로 삼는다. 2026-09-21부터: 이 두 번째
  갈래는 "하루 3번(09/12/17시 KST) 발행해달라"는 요청에 따라 워크플로의
  cron이 4개로 늘었다(07시=new-maind 전용, 09/12/17시=simple-tech-fix
  전용) - 어느 cron이 이번 실행을 켰는지에 따라 RUN_ARMS 환경변수
  ("general"/"tech_fix"/빈 문자열=둘 다)가 정해지고, main()이 그에 맞는
  갈래만 돈다(RUN_ARMS 값 이름 "tech_fix"는 최초 도입 당시의 이름을 그대로
  코드/워크플로 전반에 유지한 것뿐이고, 현재 이 갈래가 실제로 다루는 니치와는
  무관하다 - 2026-09-22 피벗 참고). 두 갈래는 각각 _run_arm()으로 감싸여
  있어서, 한쪽이 API 오류로 실패해도(call_claude()의 sys.exit 포함) 다른
  쪽이나 이미 성공한 파일의 커밋을 막지 않는다. GitHub Pages(docs/_posts)는
  이 분기와 무관하게 항상 두 갈래 전체를 보관하는 단일 아카이브로 남는다
  (resolve_blog_id_by_url(), select_niche_topic()의
  include_clusters/exclude_clusters 참고).
- 2026-09-22: simple-tech-fix로 나가는 두 번째 갈래의 니치를 "원격근무 툴
  트러블슈팅"에서 "미국 개인금융(Personal Finance)" 가이드로 전환했었다.
- 2026-09-26: "금융은 빼고 테크/AI로 바꿔달라"는 요청에 따라, 개인금융
  클러스터(F1/F2/F3)를 다시 폐기하고 새 클러스터 T1(AI Tool Verdicts,
  개별/맞대결 AI 툴에 대한 주관적 평가, 가중치 3)·T2(AI & Tech Trend
  Watch, AI/테크 업계 트렌드에 대한 논평, 가중치 2) 총 20개로 교체했다
  (SECOND_BLOG_CLUSTERS 참고). new-maind(A/B/C/E)가 중립적인 How-to/
  대안/비교 가이드 위주인 것과 겹치지 않도록, 이 갈래는 의도적으로
  "주관적 판단이 들어간 논평/평가" 포맷(build_ai_commentary_prompt(),
  포맷명 "ai_commentary")으로 차별화했다 - 결론을 먼저 명확히 던지고,
  실제 검색 트렌드·가격·기능 등 사실은 여전히 web_search로 검증하되,
  "내 판단(My Take)" 섹션에서 필자 관점의 평가·전망을 분명히 쓰게 한다.
  개인금융 전용이었던 FINANCE_TRUST_BLOCK(YMYL 면책 문구)은 이 니치엔
  해당하지 않아 제거했다.
- 2026-09-30: "new-maind는 영어 대신 한글로, 한국에 맞게 검색·작성해달라"는
  요청에 따라 new-maind(A/B/C/E)의 언어와 리서치 관점을 한국어/한국
  독자로 전환했다 - 클러스터 구성과 topics.json의 주제 풀 자체(영어
  키워드로 된 "컨셉 시드")는 그대로 두고, build_how_to_prompt()/
  build_alternative_prompt()/build_comparison_prompt() 세 개만 한국어
  출력 + 한국 시장 리서치(원화 가격, 한국어 지원 여부, 관련 있으면 국내
  대안 서비스도 언급)를 요구하도록 다시 썼다. OUTPUT_FORMAT_BLOCK_KO을
  새로 만들어 썼는데, 라벨(TITLE:/TAGS:/...) 자체는 parse_niche_output()이
  정규식으로 찾는 파싱 앵커라 영어 그대로 두고 그 값(제목·태그·본문)만
  한국어로 쓰게 했다. simple-tech-fix(T1/T2, AI/테크 논평)는 이번 전환과
  무관하게 계속 영어/미국 독자 대상으로 남는다 - call_claude()의 시스템
  프롬프트가 이제 두 블로그의 언어가 다르다는 것을 명시한다.
- 2026-10-01: 사용자가 Simple Tech Fix 전용 "글쓰기 지침" 문서(구조·문체·
  정직성 규칙, 금지 표현 목록, 의견 주입 방법, 좋은/나쁜 예시, 발행 전
  체크리스트 포함)를 제공하며 그대로 반영해달라고 요청했다.
  build_ai_commentary_prompt()를 이 문서 기준으로 전면 재작성했다 -
  자세한 내용은 그 함수 바로 위 주석 참고(문서의 6단계 워크플로를 API
  호출 1번 안에서의 "초안 -> 자체 검토 -> 최종본만 출력" 지시로 녹여내
  비용을 늘리지 않았다는 점이 핵심). max_tokens(enable_web_search=True
  경로)를 6000 -> 7000으로 올려서 검색 + 자체 검토를 한 응답 안에서
  하기에 더 여유를 뒀다.
- 이미지는 Unsplash 일반 스톡사진 대신, Claude가 SOURCES로 알려준 공식
  페이지(가격/지원문서 등, 로그인 불필요)를 Playwright로 직접 캡처해서
  쓴다 - "직접 제작/캡처/AI생성/명확한 라이선스만" 원칙상 소프트웨어
  화면 캡처 자리에 무관한 스톡사진을 쓸 수 없어서다. 로그인이 필요하거나
  캡처가 실패하면 그 자리는 조용히 건너뛰고, 캡처된 화면이 하나도 없을
  때만 Unsplash 사진 1장을 대표 이미지로 대신 쓴다 (build_screenshot_photos
  참고). 제품 지정 발행(manual, 현재는 쓰이지 않지만 기능은 남겨둠) 글은
  기존처럼 Unsplash나 실제 제품 이미지를 그대로 쓴다.
- 애드센스 "가치가 별로 없는 콘텐츠" 판정 이후 new-maind는 매일 발행 대신
  화/일을 휴무일로 두고 주 5회만 발행한다 (REST_WEEKDAYS) - simple-tech-fix
  전용 갈래(SECOND_BLOG_CLUSTERS)는 이 휴무일 적용 대상이 아니다(하루 3번
  발행 요청).
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
# 참고 - 풀을 거의 다 돌기 전까지 같은 주제가 다시 나오지 않게 한다.
#
# new-maind(일반 니치)와 simple-tech-fix(두 번째 블로그) 갈래가 서로 별도
# 파일을 쓴다 - 2026-09-30에 하나로 공유하던 걸 분리했다. 원래 하나의 파일을
# 공유했을 때, simple-tech-fix가 하루 3번(new-maind는 하루 1번)이라 20칸짜리
# "최근 사용" 기록을 3배 빠르게 채워서 new-maind 자신의 최근 사용 이력이
# 실제 발행 빈도에 비해 너무 빨리 밀려났다 - 그 결과 new-maind의 24개짜리
# 좁은 풀(A/B/C/E)에서 같은 주제(Best Free Canva Alternatives)가 8일 만에
# 다시 뽑혀 사실상 중복 글이 발행됐고(애드센스 "가치가 별로 없는 콘텐츠"
# 재판정의 실제 원인), 이걸 발견하고 분리했다.
USED_TOPIC_IDS_FILE = PROJECT_DIR / "data" / "used_topic_ids.json"
# simple-tech-fix(두 번째 블로그) 전용 사용 기록. 니치가 바뀌어도(트러블슈팅
# -> 개인금융 -> AI/테크 논평) 파일 이름 자체는 특정 니치 이름을 붙이지 않고
# 범용으로 둔다.
SECOND_BLOG_USED_TOPIC_IDS_FILE = PROJECT_DIR / "data" / "used_topic_ids_second_blog.json"
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

# 클러스터별 발행 우선순위 가중치. new-maind(A/B/C/E) 쪽은 "단순 How-to보다
# 비교/대안형 콘텐츠를 우선한다"는 전략에 따라: C/E(비교·대안, 광고
# 친화적이고 AI Overview 노출이 적은 구매의도 검색) > B(생산성/자동화, 트렌드
# 일부 포함) > A(순수 실사용 가이드, AI Overview에 CTR이 가장 많이 깎이는
# 단순 정보성 How-to라 가장 낮은 가중치). simple-tech-fix 쪽(T1/T2,
# 2026-09-26 AI/테크 논평 피벗)은 개별/맞대결 툴 평가(T1)가 업계 트렌드
# 논평(T2)보다 구매의도·광고 친화도가 높다고 보고 T1 > T2로 가중치를 뒀다.
NICHE_CLUSTER_WEIGHT = {"A": 1, "B": 2, "C": 4, "E": 4, "T1": 3, "T2": 2}

# simple-tech-fix로 나가는 두 번째 갈래가 후보로 삼는 클러스터. main()의
# select_niche_topic() 호출(일반 니치는 이걸 exclude, 두 번째 갈래는 이걸
# include)에 쓴다 - 새 허브를 추가/제거할 때 이 한 곳만 고치면 된다.
SECOND_BLOG_CLUSTERS = ("T1", "T2")


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


def load_used_topic_ids(path: Path | None = None) -> list[str]:
    # 기본값을 인자 목록에서 바로 "path: Path = USED_TOPIC_IDS_FILE"로 두면
    # 함수 정의 시점의 값이 그대로 굳어버려서, 테스트가 gp.USED_TOPIC_IDS_FILE을
    # 다른 경로로 바꿔치기해도 이 함수는 계속 원래 경로를 쓰는 버그가 생긴다
    # (이 프로젝트의 다른 모든 경로 상수는 함수 몸통에서 전역을 그대로
    # 참조해서 이 문제가 없다 - 여기도 None 기본값 + 몸통에서 읽기로 맞춘다).
    path = path or USED_TOPIC_IDS_FILE
    if not path.exists():
        return []
    try:
        ids = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return ids if isinstance(ids, list) else []


def save_used_topic_id(topic_id: str, path: Path | None = None) -> None:
    """이번에 고른 주제 id를 사용 기록에 남긴다. USED_TOPIC_IDS_KEEP개를
    넘으면 오래된 것부터 잘라내서, 풀을 거의 다 돌면 다시 등장할 수 있게
    한다 (영구히 다시 안 나오게 막지 않는다 - 결국 콘텐츠는 새로고침이
    필요해질 수 있어서). path를 지정하면 그 갈래 전용 파일에 남긴다
    (SECOND_BLOG_USED_TOPIC_IDS_FILE 참고 - new-maind/simple-tech-fix가
    파일을 공유하면 발행 빈도가 다른 두 갈래의 "최근 사용" 보호 기간이
    서로를 침범한다)."""
    path = path or USED_TOPIC_IDS_FILE
    used = load_used_topic_ids(path)
    used = [i for i in used if i != topic_id] + [topic_id]
    used = used[-USED_TOPIC_IDS_KEEP:]
    path.write_text(json.dumps(used, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def select_niche_topic(
    include_clusters: tuple[str, ...] | None = None,
    exclude_clusters: tuple[str, ...] | None = None,
    used_ids_file: Path | None = None,
) -> dict:
    """topics.json 중 하나를 클러스터 가중치(NICHE_CLUSTER_WEIGHT) 기반
    가중 무작위로 고른다. include_clusters/exclude_clusters로 후보 풀을
    특정 클러스터로 좁히거나(예: SECOND_BLOG_CLUSTERS 전용 발행) 뺄 수 있다
    (예: 일반 니치 발행에서는 SECOND_BLOG_CLUSTERS를 뺀다 - 그쪽은 main()이
    별도로 처리하므로).
    최근에 쓴 주제(used_ids_file, 기본은 new-maind 전용
    USED_TOPIC_IDS_FILE - simple-tech-fix 호출은 main()이
    SECOND_BLOG_USED_TOPIC_IDS_FILE을 넘긴다)는 먼저 제외하고 고르되,
    이번 후보 풀이 거의 다 써서 하나도 안 남으면 그 풀에서 다시 고른다
    (콘텐츠는 결국 새로고침할 수 있으니 영구 배제는 아니다). 선택한 주제의
    id는 main()이 발행에 성공한 뒤에 save_used_topic_id()로 기록한다
    (여기서는 기록하지 않는다 - 실패한 회차까지 "사용됨"으로 남으면
    안 되므로).

    FORCE_NICHE_CLUSTER 환경변수(A/B/C/E/T1/T2)가 설정돼 있고 그
    클러스터가 이번 호출의 후보 풀(include/exclude 적용 후) 안에 있으면 그
    클러스터로만 후보를 더 좁힌다 - workflow_dispatch 수동 검증용. 풀에
    없으면(예: 일반 니치 호출에서 T1을 강제 지정) 무시하고 넘어간다. 평소
    스케줄 실행에는 영향 없다."""
    topics = load_niche_topics()
    used_ids = set(load_used_topic_ids(used_ids_file))

    pool = topics
    if include_clusters:
        pool = [t for t in pool if t["cluster"] in include_clusters]
    if exclude_clusters:
        pool = [t for t in pool if t["cluster"] not in exclude_clusters]
    if not pool:
        pool = topics  # include/exclude 조합이 잘못돼 풀이 비면 안전하게 전체로

    forced_cluster = os.environ.get("FORCE_NICHE_CLUSTER", "").strip().upper()
    if forced_cluster:
        forced_pool = [t for t in pool if t["cluster"] == forced_cluster]
        if forced_pool:
            print(f"FORCE_NICHE_CLUSTER로 강제 지정됨: {forced_cluster}")
            pool = forced_pool
        else:
            print(f"FORCE_NICHE_CLUSTER='{forced_cluster}'가 이번 후보 풀에 없어 무시합니다.")

    candidates = [t for t in pool if t["id"] not in used_ids] or pool
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
    첫 블록만 쓰지 않고 전부 이어붙인다. max_tokens=7000(기존 6000에서
    상향, 2026-10-01): build_ai_commentary_prompt()가 이제 "초안을 쓰고
    스스로 체크리스트에 맞춰 검토·수정한 뒤 최종본만 출력하라"는 자체 검토
    단계를 한 응답 안에서 요구하는데, 검색 여러 번 + 자체 검토까지 하기엔
    기존 6000 토큰이 빠듯할 수 있어 여유를 뒀다."""
    client = anthropic.Anthropic()

    kwargs = dict(
        model=MODEL,
        max_tokens=7000 if enable_web_search else 4096,
        output_config={"effort": "medium"},
        system=(
            "You write for two automated blogs aimed at two different "
            "audiences. The first (new-maind) is a Korean-language blog for "
            "Korean readers, publishing neutral, structured guides (how-to, "
            "free-alternative roundups, head-to-head comparisons) about "
            "AI-powered productivity tools and software - write these in "
            "natural, native-sounding Korean blog prose (자연스러운 구어체), "
            "never a stiff or translated tone, and research Korean-market "
            "specifics (KRW pricing, Korean-language support, Korean "
            "competitor services) wherever the prompt asks for them. The "
            "second (simple-tech-fix) is an English-language blog for a US "
            "audience, publishing opinionated AI/tech commentary - clear, "
            "specific takes on AI tools and industry trends, not "
            "hedge-everything reporting; write this one in natural American "
            "English. For both blogs: base every factual claim on verified "
            "facts (use web search for anything time-sensitive like pricing, "
            "plans, feature availability, or market/search-trend data); "
            "never invent numbers, features, pricing, or rankings. On the "
            "commentary blog specifically: the facts must be verified, but "
            "the judgment and point of view are yours to state clearly and "
            "specifically - don't retreat into vague balance once you've "
            "made a claim. Never copy or closely paraphrase another blog, "
            "article, or review site - synthesize your own original "
            "explanation from what you find. Do not pad the post with "
            "filler just to hit a word count; be concise and useful."
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

# new-maind(A/B/C/E)용 한국어 버전. 라벨(TITLE:/TAGS:/...)은 parse_niche_output()이
# 정규식으로 그대로 찾는 파싱 앵커라 영어 그대로 두고, 라벨이 담는 값(제목·
# 태그·본문)만 한국어로 쓰게 한다.
OUTPUT_FORMAT_BLOCK_KO = """출력 형식(그대로 따를 것 - 라벨은 아래 영어 그대로 쓰고, 내용만 한국어로):
TITLE: (한국 독자에게 자연스러운 SEO 제목, 60자 이내, 낚시성 문구 금지)
TAGS: (쉼표로 구분한 태그 3~5개, 한국어)
KEYWORD: (이 글의 핵심 타겟 키워드/문구, 한국어)
SOURCES: (실제로 참고하고 인용한 공식 URL 2~4개, " | "로 구분 - 각각 그 도구/서비스 \
자체의 공식 도메인이어야 하며(가격 페이지·지원 문서 등), 제3자 리뷰나 \
"모음" 사이트는 안 됨)
---
(위 구조를 따르는 마크다운 본문 - 한국어)"""


def _niche_avoid_block(recent_titles: list[str]) -> str:
    if not recent_titles:
        return ""
    recent_list = "\n".join(f"- {t}" for t in recent_titles)
    return f"\nDo not repeat these already-published titles/topics:\n{recent_list}\n"


def build_how_to_prompt(topic: dict, recent_titles: list[str]) -> str:
    """How-to 포맷(클러스터 A/B): AI 도구 실사용 가이드 / 생산성·자동화 가이드.
    2026-09-30부터: "영어 대신 한글로, 한국에 맞게 검색·작성해달라"는 요청에
    따라 new-maind는 이 포맷부터 한국 독자 대상 한국어로 작성한다(클러스터
    구성·주제 풀은 그대로 유지, 언어와 리서치 관점만 전환). AI Overview가
    단순 정보성 How-to 검색의 CTR을 크게 깎아먹는다는 신호는 원래 미국
    구글 검색 기준이라 한국(네이버 비중이 큰) 검색 환경에 그대로 들어맞는지는
    불확실하지만, 클러스터 가중치 자체를 바꿔달라는 요청은 없어서
    NICHE_CLUSTER_WEIGHT는 그대로 둔다."""
    return f"""당신은 한국 독자를 대상으로 하는 AI 생산성 도구 블로그에 실릴 사용법(하우투) 글을 씁니다.

타겟 키워드/주제: "{topic['keyword']}"
{_niche_avoid_block(recent_titles)}
이 글은 한국어로, 한국 독자 관점에서 씁니다. 웹 검색으로 현재 단계·UI
메뉴 이름·기능 제공 여부를 확인하세요 - 도구가 한국어 인터페이스를
제공한다면 그 한국어 메뉴 명칭 기준으로 설명하고, 한국에서 이용 가능한지
(가입 제한, 결제 수단 등)도 확인하세요. 도구는 UI를 자주 바꾸므로,
확인되지 않은 단계·버튼 이름·메뉴 라벨은 절대 지어내지 마세요.

구성(이 순서대로):
1. 독자의 질문에 대한 직접적인 답을 첫 2~3문장에 - 서론으로 시간 끌지 않기.
2. "준비물" - 정말 필요한 경우에만, 계정·요금제·브라우저 등을 짧게.
3. 번호를 매긴 단계 또는 소제목(##)으로 나눈 단계별 설명.
4. 짧은 FAQ(2~4개) - 자주 나올 후속 질문.
5. 짧은 마무리(2~3문장).

분량: 1500~2200자 내외(한글 기준). 단계 수를 늘리려고 불필요한 내용을
채우지 마세요.

톤: 자연스러운 한국어 블로그 구어체 - 번역투 금지, 친한 지인이 알려주는
느낌으로. 과장이나 근거 없는 효과·수익 약속 금지.

{OUTPUT_FORMAT_BLOCK_KO}
"""


def build_alternative_prompt(topic: dict, recent_titles: list[str]) -> str:
    """Alternative 포맷(클러스터 C): 유료 툴의 무료/저가 대안 목록형 글.
    2026-09-30부터 한국 독자 대상 한국어로 작성 - 글로벌 도구뿐 아니라
    한국에서 실제로 쓰이는 국내 대안도 있으면 함께 다루도록 명시적으로
    요구한다(예: 캔바 -> 미리캔버스)."""
    return f"""당신은 한국 독자를 대상으로 하는 AI/생산성 소프트웨어 블로그에 실릴 "무료 대안 추천" 글을 씁니다.

타겟 키워드/주제: "{topic['keyword']}"
{_niche_avoid_block(recent_titles)}
웹 검색으로 각 도구의 현재 요금제·무료 티어 한도·핵심 기능을 확인하세요
(가격은 자주 바뀌므로, 오래된 정보를 쓰느니 확인된 것만 쓰세요). 이
주제와 관련해 한국에서 실제로 많이 쓰이는 국내 서비스가 있다면(예: 캔바
관련 주제라면 미리캔버스 등 - 실제로 관련 있는 경우에만, 억지로 끼워
넣지 마세요) 최소 1개는 후보에 포함하고, 가격은 원화 기준(또는 달러와
원화 환산 병기)으로 표기하세요.

구성(이 순서대로):
1. 첫 2~3문장에 결론부터: 가장 추천하는 1개와 차선책 1~2개를 바로 제시.
2. "선정 기준" - 가격·기능·사용 편의성 등 선정 기준을 3~5개 불릿으로.
3. 각 대안(3~5개) 소개 - 도구마다 소제목(##) 하나씩, 무엇에 좋은지와
   무료 티어 한도가 실제로 어디까지인지.
4. 가격·핵심 한계·추천 대상을 정리한 마크다운 비교표.
5. 짧은 FAQ(2~4개).

SOURCES에는 반드시 각 도구의 공식 요금제 페이지를 인용하세요 - 리뷰
사이트나 "모음" 글이 아니라 그 서비스 자체의 공식 도메인이어야 합니다.

분량: 1800~2500자 내외(한글 기준).

톤: 자연스러운 한국어 블로그 구어체 - 번역투 금지. 과장·근거 없는 주장
금지.

{OUTPUT_FORMAT_BLOCK_KO}
"""


# build_ai_commentary_prompt()가 배경 지식으로 심어주는 2026년 AI/테크
# 트렌드 요약. 실제로 리서치(WebSearch)해서 확인한 내용이다 - ChatGPT/
# Gemini/Claude 검색 순위, AI Overviews가 정보성 검색 CTR을 깎는 현상 등.
# 모델이 매번 이 사실들을 처음부터 다시 찾는 대신 출발점으로 쓰게 하고,
# 그래도 시점에 따라 바뀌는 숫자(순위, 가격, 점유율 등)는 web_search로
# 다시 확인하게 한다.
AI_TREND_CONTEXT_BLOCK = """Background context (verified via research, current as of late 2026 - treat these as a starting point, and use web search to confirm or update anything that may have shifted):
- ChatGPT and Gemini both rank in the top 20 most-searched terms on Google; Claude also appears in the top 50 - all three are mainstream household names now, not just early-adopter tools.
- Google's AI Overviews are measurably cutting click-through rates on plain informational ("how-to") searches, while comparison/alternative/buying-intent searches are comparatively unaffected - this is reshaping what kind of content still gets clicked.
- AI coding assistants, AI meeting/note-taking tools, and AI writing tools have gone from novelty to default expectation in many workplaces during 2026.
- Digital banking, fintech, and AI-adjacent productivity SaaS remain some of the most heavily searched commercial categories alongside AI tools themselves."""


# 2026-10-01: 사용자가 Simple Tech Fix 전용 "글쓰기 지침" 문서(한국어로 관리,
# 본문은 영어)를 통째로 제공하며 이걸 지침으로 삼아달라고 요청했다. 문서는
# 구조·문체·정직성 규칙과, "리서치 -> 초안 -> 편집 -> 재작성 -> 팩트체크 ->
# 점수 확인" 6단계 워크플로를 명시했는데, 6단계를 전부 별도 API 호출로
# 구현하면 이 갈래의 Claude 호출 비용이 그대로 몇 배로 뛴다(이 갈래는 이미
# 하루 3번 돈다). 그래서 "체크리스트를 통과 못 하면 3~4단계를 반복한다"는
# 조건부 재작성 의도를, 한 번의 호출 안에서 "초안을 쓴 뒤 스스로 아래
# 체크리스트에 맞춰 검토하고 고쳐서 최종본만 낸다"는 자체 검토 지시로
# 녹여냈다 - 비용을 늘리지 않으면서 문서의 모든 실질적 규칙(구조, 금지
# 표현, 의견 주입 방법, 정직성 규칙, 좋은/나쁜 예시, 체크리스트)은 빠짐없이
# 반영했다. 정직성 규칙(직접 써보지 않은 경험을 지어내지 않는다) 중
# "사람이 직접 넣는 부분이 비면 정직하게 '문서를 읽고 쓴 분석'으로 쓴다"는
# 조항 덕분에, 사람 개입 없이 완전 자동으로 돌아가는 이 파이프라인 특성과
# 지침이 이미 맞아떨어진다 - 별도 수정 없이 그대로 쓸 수 있었다.
def build_ai_commentary_prompt(topic: dict, recent_titles: list[str]) -> str:
    """AI Commentary 포맷(클러스터 T1/T2, simple-tech-fix 전용). 2026-10-01
    부터 사용자가 제공한 "Simple Tech Fix 블로그 글쓰기 지침" 문서를 그대로
    반영한다(위 모듈 주석 참고) - 결론 먼저, 출처 기반 근거, 불편한 사실도
    포함, 의견은 의견이라고 표시, 직접 경험을 지어내지 않는다는 원칙이
    핵심이다."""
    return f"""You are writing for Simple Tech Fix, an English-language blog that solves everyday problems people run into with work tools (Slack, Google Meet, Calendly, Google Workspace, etc.) and AI tools, in plain English, step by step. Readers are ordinary people who use these tools for work and don't need to be fluent in tech jargon to follow along.

Content hub for this post: {topic['cluster_name']}
Target keyword/topic: "{topic['keyword']}"
{_niche_avoid_block(recent_titles)}
{AI_TREND_CONTEXT_BLOCK}

## Research and sourcing

Use web search and prefer primary sources: the vendor's own official blog/help docs/changelog, not third-party summaries. Never invent a price, feature, limit, date, or statistic - if you can't confirm something, say so in the piece rather than guessing (see Honesty rules below). Don't quote long passages from a source; paraphrase in your own words, and if you do quote directly, keep it short and use at most one direct quote per source. Don't mirror the structure of any single source article. List every source you actually used as a link at the end (see SOURCES in the output format).

## Structure

Vary the number of subheadings and paragraph lengths from post to post - repeating the exact same skeleton every time reads as AI-generated. Use this as a flexible template, not a rigid fill-in-the-blanks form:

1. **Title** that telegraphs a verdict (e.g. "Turn It On, but Ask the Room First" - not a generic "X: A Complete Guide").
2. **My verdict:** one paragraph, right after the title. State who this is good for and who it isn't, and briefly say why you're leading with the verdict instead of easing into it.
3. **## What's Actually Going On** - what it is / how it works (numbered steps if that helps), who can actually use it, when it rolled out. Source-backed, not opinion yet.
4. **## Where It Breaks** - limitations, failure conditions, common misunderstandings, as a short list.
5. **## Fix It: Check These in Order** - *only if this post is genuinely about troubleshooting a specific problem*: most likely cause first, then less common ones. Skip this section entirely for a pure tool-verdict or trend piece where there's nothing to "fix."
6. **A risk/caution section** - *only if genuinely relevant* (legal, security, privacy implications).
7. **## What I Learned While Writing This (and What I Think)** - 2-3 things that surprised you while researching this, your own opinion clearly marked as opinion, and an honest note on this piece's limits (did you actually use this yourself, or just read the docs - see Honesty rules).
8. **Sources:** link list.

## Readability

Paragraphs: 1-4 sentences. Numbered lists for steps. Tables for comparisons. Bullets for lists - but don't let the whole piece turn into bullet points.

Length: roughly 800-1200 words.

## Writing like a human, not an AI

- Order within a point: verdict, then reason, then exception.
- Vary sentence length on purpose - a short sentence after a long one. An occasional one-sentence paragraph is fine.
- Be concrete: not "a variety of features" but "summaries, action items, and the full transcript."
- Never hide an uncomfortable fact: every post needs at least one real limitation, pricing catch, or thing the tool can't do.
- Explain things through a situation the reader will actually hit ("If the button isn't showing up, check these in order").
- Mark opinions as opinions: "I think", "My take", "In my view" - don't blend opinion into stated fact.

## Do not do this (instant AI-writing tells)

- Clichés: "In today's fast-paced world", "In conclusion", "It's important to note", "Let's dive in", "game-changer", "unlock the power of", "seamlessly", "revolutionary".
- A tidy summary-plus-pep-talk ending ("So go ahead and try it today!").
- Every subheading the same length, following the identical pattern.
- Consecutive sentences starting with the same word.
- Baseless praise or ad-copy tone.
- The reflexive habit of grouping everything into sets of exactly three (three benefits, three tips, three takeaways, repeated throughout).

## How to actually inject a point of view

1. Keep fact and opinion visibly separate: facts carry a source; opinions carry "I think".
2. Give every opinion a reason: "I think this matters because...".
3. Concede at least one line to the other side ("Some teams will love this, but...").
4. Make opinions concrete judgments, not hedges: "Use it for planned team meetings; skip it for feedback conversations" - not "it has pros and cons."
5. Never land on vague neutrality ("there are pros and cons") as your ending.

## Honesty rules (the most important section)

- Never fake hands-on testing you didn't do. Forbidden unless genuinely true: "I tested this for two weeks...", "In my experience...". Fine to say instead: "I read the documentation but didn't run it in a real meeting."
- If you couldn't confirm something, say exactly that: "I couldn't find an answer to that."
- Never state a number, price, or date that your sources don't actually support.
- For legal, medical, or financial angles, disclose the limit plainly ("I'm not a lawyer") and don't make definitive claims.

## Before you finalize

Silently review your own draft against this checklist and fix anything that fails, then output only the corrected final version (don't show your draft or the review itself):
- Structure: verdict in the first paragraph; who it's for and who it isn't; at least one real limitation or failure condition; a closing "what I learned / my take / this piece's limits" section; sources listed.
- Style: zero banned clichés; sentence lengths actually vary; no run of consecutive sentences starting with the same word; every opinion carries "I think" (or equivalent) plus a reason; no tidy summary-and-CTA ending.
- Honesty: no invented hands-on experience; zero unsourced numbers; anything unconfirmed is labeled as such; a legal/medical/financial angle (if present) carries an explicit limits disclaimer.

## Example: the difference a verdict makes

Bad opening (don't write like this): "In today's fast-paced digital world, meetings are more important than ever. Google Meet has introduced an exciting new feature that could revolutionize how you take notes!"

Good opening (write like this): "**My verdict:** Meet's new in-person 'Take notes' button is worth using for planned, single-language meetings that run at least 15 minutes, as long as you're on an eligible plan and everyone in the room knows it's on. It's a bad idea as a quiet background recorder." - this one has a judgment, a condition, and who it's wrong for.

{OUTPUT_FORMAT_BLOCK}
"""


def build_comparison_prompt(topic: dict, recent_titles: list[str]) -> str:
    """Comparison 포맷(클러스터 E): 생산성 소프트웨어 정면 비교.
    2026-09-30부터 한국 독자 대상 한국어로 작성한다."""
    return f"""당신은 한국 독자를 대상으로 하는 생산성 소프트웨어 블로그에 실릴 정면 비교 글을 씁니다.

타겟 키워드/주제: "{topic['keyword']}"
{_niche_avoid_block(recent_titles)}
웹 검색으로 두 도구의 현재 요금제·플랜·핵심 기능을 각 공식 페이지에서
확인하세요. 한국에서의 이용 가능 여부, 한국어 지원 수준, 원화 환산
가격도 함께 확인해서 언급하세요.

구성(이 순서대로):
1. 첫 2~3문장에 결론 요약: 어떤 도구가 누구에게 더 나은지 바로 제시.
2. 가격·핵심 기능·타겟 사용자를 정리한 마크다운 비교표.
3. 항목별 분석 - 가격, 사용 편의성, 핵심 기능 차이, 협업/연동 등 3~4개
   소제목(##)으로 두 도구를 직접 비교.
4. "이런 사람에게 추천" - 사용자 유형별 추천 매칭.
5. 짧은 FAQ(2~4개).

SOURCES에는 두 회사 각각의 공식 요금제/스펙 페이지를 인용하세요(제3자
비교 사이트 금지).

분량: 2000~2600자 내외(한글 기준).

톤: 자연스러운 한국어 블로그 구어체, 양쪽에 공정하되 결론은 분명하게.
과장 금지.

{OUTPUT_FORMAT_BLOCK_KO}
"""


NICHE_FORMAT_PROMPT_BUILDERS = {
    "how_to": build_how_to_prompt,
    "alternative": build_alternative_prompt,
    "comparison": build_comparison_prompt,
    "ai_commentary": build_ai_commentary_prompt,
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
    기본 블로그(BLOGGER_BLOG_ID, new-maind)에 발행한다 - SECOND_BLOG_CLUSTERS
    글을 두 번째 블로그(SECOND_BLOG_URL)에 발행할 때는
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


# SECOND_BLOG_CLUSTERS(T1/T2) 글은 new-maind가 아니라 같은 구글 계정 소유의
# 별도 블로그로 보낸다 - 같은 글을 두 블로그에 중복 발행하면 애드센스가
# "중복 콘텐츠"로 볼 위험도 피할 수 있다. 2026-09-20 도입 당시엔 클러스터
# D(Remote-Work Tool Troubleshooting)가, 2026-09-22부터는 미국 개인금융이
# 이 자리였고, 2026-09-26부터는 AI/테크 논평(AI Tool Verdicts/AI & Tech
# Trend Watch) 니치로 바뀌었다 - 블로그 URL/도메인 이름("simple-tech-fix")
# 은 최초 취지를 그대로 남겨둔 것뿐이라 지금 다루는 내용과는 무관하다.
# GitHub Pages(docs/_posts)는 이 분기와 무관하게 항상 전체 클러스터를
# 그대로 보관하는 단일 아카이브로 남는다.
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


# 2026-09-30부터 new-maind가 한국어로 전환되면서 이 두 페이지도 한국어로
# 다시 썼다. 기존 영어 버전은 "Zoom/Meet/Drive 등 원격근무 툴 문제 해결"을
# 다룬다고 적혀 있었는데, 그건 클러스터 D가 이 블로그에 있었을 때(이미
# 오래전에 두 번째 블로그로 완전히 옮겨감) 얘기라 사실과 달랐다 - 이번에
# 다시 쓰면서 실제로 다루는 범위(A/B/C/E)에 맞게 바로잡았다.
BLOGGER_PRIVACY_PAGE_TITLE = "개인정보처리방침"
BLOGGER_ABOUT_PAGE_TITLE = "소개"

BLOGGER_PRIVACY_PAGE_MD = """\
이 페이지는 이 블로그를 방문하시는 분들의 어떤 정보가 수집되고 어떻게 쓰이는지 설명합니다.

## 1. 쿠키와 방문 기록

이 블로그는 방문 통계 분석을 위해 구글 애널리틱스를 사용할 수 있습니다. 구글 애널리틱스는 방문 페이지, 체류 시간, 기기 종류 등 개인을 특정할 수 없는 통계 정보를 쿠키로 수집합니다. 이름·연락처 등 개인을 식별할 수 있는 정보는 수집하지 않습니다.

## 2. 광고

이 블로그는 구글 애드센스를 포함한 제3자 광고를 게재할 수 있습니다. 구글 및 광고 제공업체는 이전 방문 이력을 바탕으로 맞춤 광고를 보여주기 위해 쿠키를 사용할 수 있습니다.

- 구글이 광고에 쿠키를 어떻게 사용하는지는 [Google 광고 정책](https://policies.google.com/technologies/ads) 페이지에서 확인할 수 있습니다.
- 맞춤 광고를 원치 않으시면 [Google 광고 설정](https://adssettings.google.com)에서 해제할 수 있습니다.

## 3. 콘텐츠와 제작 방식

이 블로그는 한 명의 개인 운영자가 운영하며, 글 작성 과정에 AI 자동화 도구의 도움을 받습니다. 다만 어떤 주제를 다룰지 결정하고 발행된 내용에 대한 최종 책임은 운영자에게 있습니다. 시간이 지나면 바뀔 수 있는 내용(소프트웨어 요금제, 플랜, 기능 제공 여부 등)은 발행 전에 웹 검색으로 최신 사실을 확인하고, 제3자 요약이 아니라 해당 서비스의 공식 페이지를 출처로 인용합니다.

## 4. 제휴 링크 고지

이 블로그는 현재 제휴/추천 링크를 사용하지 않습니다. 추후 변경될 경우, 해당 글에 직접 고지하고 이 페이지에도 반영하겠습니다.

## 5. 문의

이 개인정보처리방침이나 블로그 운영 방식에 대해 궁금한 점이 있으시면 아무 글에나 댓글로 남겨주세요.

## 6. 변경 사항

서비스나 관련 법령이 바뀌면 이 방침도 바뀔 수 있으며, 변경 사항은 이 페이지에 반영됩니다.
"""

BLOGGER_ABOUT_PAGE_MD_TEMPLATE = """\
## 이 블로그는 무엇을 다루나요

이 블로그는 AI 생산성 도구를 다룹니다: ChatGPT·Claude 같은 도구의 실사용 가이드, 인기 소프트웨어의 무료/저가 대안 추천, 생산성 소프트웨어끼리의 정면 비교를 한국 독자 관점에서 씁니다.

## 운영자 소개

이 블로그는 한 명의 개인 운영자가 운영합니다. 어떤 주제를 언제 다룰지는 운영자가 정하고, 글 작성 과정에 AI 자동화 도구를 활용합니다. 다만 발행된 내용의 정확성을 포함한 최종 책임은 AI가 아니라 운영자에게 있습니다. 분량보다 완성도에 집중하기 위해 매일이 아니라 주 5회 발행합니다.

## 콘텐츠 제작 방식

- 소프트웨어 요금제·플랜·기능 제공 여부처럼 시점에 따라 바뀔 수 있는 내용은 발행 전에 웹 검색으로 사실을 확인합니다.
- 제3자 리뷰를 요약하는 대신, 해당 서비스의 공식 페이지(요금제 페이지, 지원 문서 등)를 직접 출처로 인용합니다.
- 글에 쓰이는 스크린샷은 실제로 다루는 공식 공개 페이지를 직접 캡처한 것이며, 다른 사이트나 블로그의 이미지를 그대로 가져다 쓰지 않습니다.
- 분량을 채우기보다 실제로 도움이 되고 구체적인 내용을 목표로 합니다.

이 블로그는 현재 제휴/추천 링크를 사용하지 않습니다. 자세한 내용은 [개인정보처리방침]({privacy_url}) 페이지를 참고해주세요.

## 문의

블로그에 대한 문의나 의견은 아무 글에나 댓글로 남겨주세요.
"""


SECOND_BLOG_PRIVACY_PAGE_TITLE = "Privacy Policy"
SECOND_BLOG_ABOUT_PAGE_TITLE = "About"

SECOND_BLOG_PRIVACY_PAGE_MD = """\
This page explains what information is collected from visitors to this blog and how it's used.

## 1. Cookies and Visit Data

This blog may use Google Analytics to analyze visit statistics. Google Analytics uses cookies to collect non-identifying statistics such as pages visited, time on page, and device type. It does not collect personally identifying information (name, contact details, etc.).

## 2. Advertising

This blog may display third-party ads, including Google AdSense. Google and other ad providers may use cookies to show personalized ads based on your prior visits.

- You can learn how Google uses cookies for advertising at the [Google Ads Policy](https://policies.google.com/technologies/ads) page.
- You can opt out of personalized ads at [Google Ads Settings](https://adssettings.google.com).

## 3. Affiliate Disclosure

This blog currently carries no affiliate or referral links. If that changes in the future, any affiliate relationship will be disclosed directly in the relevant post and reflected here.

## 4. Content and How It's Made

This blog is run by a single independent operator, and posts are written with the help of AI automation tools, but the operator decides what topics to cover and takes final responsibility for what's published. Every fact cited (pricing, features, rankings, trend data) is checked against an official vendor page or a credible primary source before publishing, rather than an unverified blog post. The opinions and judgments expressed in posts are the blog's own point of view, not neutral reporting.

## 5. Contact

If you have questions about this privacy policy or how this blog is run, please leave a comment on any post.

## 6. Changes

This policy may change as the service or applicable law changes; updates will be reflected on this page.
"""

SECOND_BLOG_ABOUT_PAGE_MD_TEMPLATE = """\
## What This Blog Covers

Simple Tech Fix solves everyday problems people run into with work tools (Slack, Google Meet, Calendly, Google Workspace, and the like) and AI tools, in plain English, step by step - plus clear, opinionated verdicts on individual AI tools and where the AI/tech industry is actually heading, cutting past the marketing language.

Each post opens with a verdict - who it's for and who it isn't - lays out the verified facts behind it, and is honest about what the writing process could and couldn't confirm firsthand, before landing on a concrete bottom line.

## About the Operator

This blog is run by a single independent operator, as a focused companion to a broader blog about AI-powered productivity tools - that other blog sticks to neutral, structured how-to and comparison guides, while this one is where the opinions live. The operator decides what topics to cover, and posts are written with the help of AI automation tools, but final responsibility for what's published - and whether it's accurate - rests with the operator, not the AI.

## How Content Is Made

- Every fact cited (pricing, features, plan limits, search/market trend data) is checked against an official vendor page or a credible primary source (an official company blog, an analyst report, reputable tech reporting) before publishing - never an unverified blog post or a content-mill roundup.
- The facts are verified, but the judgment is the blog's own - posts take a real position instead of hedging into "it depends."
- Posts never claim hands-on testing that didn't happen; when a post is based on reading the documentation rather than real first-hand use, it says so plainly.
- Posts aim to be specific and opinionated rather than padded out to hit a word count.

This blog currently carries no affiliate or referral links. See the [Privacy Policy]({privacy_url}) page for more detail.

## Contact

Questions or feedback about this blog can be left as a comment on any post.
"""


def _sync_static_pages_for_blog(
    blog_id: str, privacy_title: str, privacy_md: str, about_title: str, about_md_template: str
) -> None:
    """주어진 blog_id의 블로그에 개인정보처리방침·소개 페이지를 만들어 두고,
    이미 있으면 최신 내용으로 갱신한다(제목 기준으로 찾아 PATCH) - 그래서 이
    콘텐츠를 바꿀 때마다 다음 발행 때 Blogger 쪽도 자동으로 맞춰진다. 실패해도
    본 발행 흐름을 막지 않는다. sync_blogger_static_pages()/
    sync_second_blogger_static_pages()가 각자의 블로그 id와 페이지 내용으로
    이 함수를 호출한다."""
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
    pages_url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/pages/"

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

    privacy_url = _upsert_page(privacy_title, privacy_md)
    about_md = about_md_template.format(privacy_url=privacy_url or "https://www.blogger.com")
    _upsert_page(about_title, about_md)


def sync_blogger_static_pages() -> None:
    """new-maind 블로그(BLOGGER_BLOG_ID)의 개인정보처리방침·소개 페이지를
    동기화한다. 애드센스는 실제로 신청하는 도메인(Blogger)에 이 페이지들이
    있어야 심사가 되므로, GitHub Pages(docs/privacy.md, docs/about.md)와
    같은 내용을 유지한다."""
    _sync_static_pages_for_blog(
        BLOGGER_BLOG_ID,
        BLOGGER_PRIVACY_PAGE_TITLE,
        BLOGGER_PRIVACY_PAGE_MD,
        BLOGGER_ABOUT_PAGE_TITLE,
        BLOGGER_ABOUT_PAGE_MD_TEMPLATE,
    )


def sync_second_blogger_static_pages() -> None:
    """simple-tech-fix 블로그의 개인정보처리방침·소개 페이지를 동기화한다.
    블로그 ID는 저장해두지 않고 매번 URL로 새로 조회한다(같은 구글 계정
    소유라 별도 시크릿이 필요 없다 - resolve_blog_id_by_url 참고). 조회
    실패(권한 없음/블로그 없음 등)해도 본 발행 흐름을 막지 않는다."""
    second_blog_id = resolve_blog_id_by_url(SECOND_BLOG_URL)
    if not second_blog_id:
        print(f"{SECOND_BLOG_URL} 블로그 ID를 찾지 못해 정적 페이지 동기화를 건너뜁니다.")
        return
    _sync_static_pages_for_blog(
        second_blog_id,
        SECOND_BLOG_PRIVACY_PAGE_TITLE,
        SECOND_BLOG_PRIVACY_PAGE_MD,
        SECOND_BLOG_ABOUT_PAGE_TITLE,
        SECOND_BLOG_ABOUT_PAGE_MD_TEMPLATE,
    )


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


def _blogger_get(url: str, access_token: str) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def audit_blog_posts() -> None:
    """읽기 전용 점검(RUN_BLOG_AUDIT=true): new-maind(BLOGGER_BLOG_ID)에 실제로
    올라가 있는 글/페이지를 전부 읽어서 언어·길이·발행일·제목 중복·외부링크
    수를 로그로 찍는다. 아무것도 수정/삭제하지 않는다. 2026-10-02, 애드센스
    "가치가 별로 없는 콘텐츠" 사유가 계속되는데 docs/_posts는 두 블로그
    글이 섞인 미러라 new-maind에 실제로 뭐가 있는지 알 수가 없어서 만들었다."""
    import difflib
    import html as html_lib

    if not blogger_configured():
        print("Blogger 인증 정보가 없어 점검을 건너뜁니다.")
        return
    access_token = get_google_access_token()
    base = f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}"

    info = _blogger_get(base, access_token)
    print(f"블로그: {info.get('name')} ({info.get('url')})")
    print(f"  글 {info.get('posts', {}).get('totalItems')}개 / 페이지 {info.get('pages', {}).get('totalItems')}개")

    posts, page_token = [], ""
    while True:
        qs = "fetchBodies=true&maxResults=50&orderBy=published&status=live&status=draft&status=scheduled"
        if page_token:
            qs += f"&pageToken={urllib.parse.quote(page_token)}"
        data = _blogger_get(f"{base}/posts?{qs}", access_token)
        posts.extend(data.get("items", []) or [])
        page_token = data.get("nextPageToken", "")
        if not page_token:
            break

    print(f"\n=== 글 {len(posts)}개 (발행일 오름차순) ===")
    rows = []
    for p in posts:
        body = p.get("content", "") or ""
        text = html_lib.unescape(re.sub(r"<[^>]+>", " ", body))
        hangul = len(re.findall(r"[가-힣]", text))
        latin = len(re.findall(r"[A-Za-z]", text))
        lang = "KO" if hangul > latin else "EN"
        chars = len(re.sub(r"\s+", "", text))
        ext_links = len(re.findall(r'href=["\']https?://(?!(?:[\w.-]*blogspot\.com|[\w.-]*github\.io))', body))
        imgs = len(re.findall(r"<img\b", body))
        coupang = "Y" if ("coupang" in body.lower() or "쿠팡" in body) else "-"
        rows.append((p.get("published", ""), p.get("status", ""), lang, chars, imgs, ext_links, coupang, p.get("title", ""), p.get("url", ""), p.get("id", "")))
    rows.sort()
    for pub, status, lang, chars, imgs, ext, cp, title, url, pid in rows:
        print(f"{pub[:16]} | {status:5} | {lang} | {chars:5}자 | img={imgs} | ext={ext} | cp={cp} | id={pid} | {title} | {url}")

    print("\n=== 요약 ===")
    by_lang = {}
    for r in rows:
        by_lang[r[2]] = by_lang.get(r[2], 0) + 1
    print(f"언어별: {by_lang}")
    by_day = {}
    for r in rows:
        by_day[r[0][:10]] = by_day.get(r[0][:10], 0) + 1
    print(f"하루 3개 이상 발행한 날: { {d: n for d, n in sorted(by_day.items()) if n >= 3} }")
    short = [(r[7], r[3]) for r in rows if r[3] < 2500]
    print(f"본문 2500자 미만 글 {len(short)}개: {short}")
    titles = [(r[7], r[9]) for r in rows]
    dup_pairs = []
    for i in range(len(titles)):
        for j in range(i + 1, len(titles)):
            if difflib.SequenceMatcher(None, titles[i][0].lower(), titles[j][0].lower()).ratio() >= 0.75:
                dup_pairs.append((titles[i][0], titles[j][0]))
    print(f"제목이 75% 이상 비슷한 쌍 {len(dup_pairs)}개: {dup_pairs}")

    pages = _blogger_get(f"{base}/pages?fetchBodies=false", access_token).get("items", []) or []
    print(f"\n=== 정적 페이지 {len(pages)}개 ===")
    for pg in pages:
        print(f"{pg.get('status')} | {pg.get('title')} | {pg.get('url')}")


def _run_generation(
    prompt: str,
    fallback_title: str,
    *,
    manual: dict | None = None,
    niche_topic: dict | None = None,
    blog_id: str | None = None,
    used_ids_file: Path | None = None,
) -> None:
    """프롬프트 하나로 글 하나를 생성해서 GitHub Pages(docs/_posts, 항상
    전체 클러스터를 보관하는 단일 아카이브)에 저장하고 Blogger에도 발행한다.
    manual/niche_topic 중 정확히 하나만 넘긴다(어느 쪽인지에 따라 이미지
    처리·후처리 방식이 다르다 - 제품 지정 발행은 실제 상품 이미지/Unsplash
    단일 사진, 새 니치는 SOURCES 화면 캡처 여러 장). blog_id를 지정하면
    그 블로그로, 안 주면 기본 블로그(BLOGGER_BLOG_ID, new-maind)로 발행한다.
    used_ids_file은 niche_topic 발행 성공 후 save_used_topic_id()가 기록할
    파일이다 - select_niche_topic() 호출 때 쓴 것과 같은 파일을 넘겨야
    한다(호출부가 책임진다).

    main()이 이 함수를 최대 두 번 부른다 - "일반 니치"(A/B/C/E, 클러스터
    가중치 기반, new-maind, 화/일 휴무)와 "AI/테크 논평 전용"
    (SECOND_BLOG_CLUSTERS, simple-tech-fix, 하루 3번, 휴무 없음). 한쪽이
    call_claude() 등에서
    실패(SystemExit 포함)해도 다른 쪽이나 이미 만들어진 파일의 커밋을
    막으면 안 되므로, 이 함수 자체는 예외를 삼키지 않고 그대로 올려보내고
    (그래야 실패 원인이 로그에 그대로 남는다) 호출부(main())가 _run_arm()으로
    감싸서 격리한다."""
    raw_output = call_claude(prompt, enable_web_search=not manual)

    if manual:
        title, tags, keyword, image_query, body = parse_output(raw_output, fallback_title=fallback_title)
        sources = []
    else:
        title, tags, keyword, sources, body = parse_niche_output(raw_output, fallback_title=fallback_title)

    today = datetime.date.today()
    slug = slugify(title)

    if manual and manual.get("affiliate_html"):
        # 제품 지정 발행: 무관한 Unsplash 스톡사진 대신, 이미 갖고 있는
        # 실제 상품 이미지(쿠팡 배너)를 대표 이미지로 쓴다.
        product_photo = extract_product_image(manual["affiliate_html"])
        image_block = build_product_image_block(product_photo)
        body = image_block + body
    elif manual:
        photo = find_stock_photo(image_query or keyword or fallback_title)
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
            stock_query = f"{niche_topic['cluster_name']} software" if niche_topic else (keyword or fallback_title)
            stock = find_stock_photo(stock_query)
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

    post_to_blogger(safe_title, full_body, blog_id=blog_id)

    if manual:
        consume_manual_topic(manual)
    else:
        save_used_topic_id(niche_topic["id"], used_ids_file)


def _run_arm(label: str, fn) -> bool:
    """한 갈래(지정 발행/일반 니치/개인금융 전용) 실행을 감싸서, 이
    안에서 나는 어떤 오류(call_claude()의 sys.exit 포함)도 다른 갈래의
    실행이나 이미 성공적으로 만들어진 파일의 커밋을 막지 않게 한다 -
    main()이 이제 한 번 실행에 최대 두 번 글을 생성하므로, 한쪽이 API
    레이트리밋 등으로 실패해도 이미 성공한 다른 쪽까지 통째로 날아가면
    안 된다. 성공하면 True를 돌려준다."""
    try:
        fn()
        return True
    except SystemExit as e:
        print(f"[{label}] 오류로 이번 갈래는 건너뜁니다: {e}")
        return False
    except Exception as e:
        print(f"[{label}] 예상치 못한 오류로 이번 갈래는 건너뜁니다: {e}")
        return False


def main() -> None:
    if os.environ.get("RUN_BLOG_AUDIT") == "true":
        # 읽기 전용 점검 모드: Claude API를 쓰지 않으므로 키 검사보다 먼저 처리한다.
        audit_blog_posts()
        return

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY 환경변수가 설정되어 있지 않습니다.")

    if os.environ.get("RUN_FIX_KNOWN_POST_TITLE") == "true":
        # 일회성 유지보수 모드: 정상 발행 흐름을 타지 않고 이 작업만 하고 끝낸다
        # (workflow_dispatch로만 켜지며, 매일 스케줄 실행에는 영향 없음).
        fix_known_post_title()
        return

    manual = load_manual_topic()

    # 요일 판정은 실행 시각(UTC)이 아니라 실제 발행되는 KST 기준이어야 한다 -
    # 이 워크플로는 22:00 UTC(=07:00 KST 다음날)에 돌기 때문에, UTC 그대로
    # 쓰면 요일이 하루 밀린다.
    kst_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    forced_cluster = os.environ.get("FORCE_NICHE_CLUSTER", "").strip()

    # RUN_ARMS: 스케줄(cron)이 4개로 늘어서(07/09/12/17시 KST) 이번 실행이
    # 어느 갈래를 돌려야 하는지 구분해야 한다 - 워크플로가 어느 cron이
    # 켰는지로 자동 계산해서 넣어준다("0 22 * * *"=general, 나머지
    # 3개=tech_fix). 비어있으면(workflow_dispatch 기본값, 로컬 테스트 등)
    # 둘 다 실행한다(기존 동작과 동일).
    run_arms = os.environ.get("RUN_ARMS", "").strip().lower()
    run_general = run_arms in ("", "general")
    run_tech_fix = run_arms in ("", "tech_fix")

    results: list[tuple[str, bool]] = []

    if manual and run_general:
        # 제품 지정 발행(manual)은 일반 니치 갈래의 대체재라서, 두 번째 블로그
        # 전용(simple-tech-fix) cron 슬롯(09/12/17시)에서는 아예 다루지
        # 않는다 - 안 그러면 같은 제품 글이 하루 세 번 나가버린다.
        def _run_manual():
            recent_titles = get_recent_titles()
            prompt = build_product_prompt(manual, recent_titles)
            _run_generation(prompt, manual["topic"], manual=manual)

        results.append(("manual", _run_arm("manual", _run_manual)))
    elif run_general:
        # 일반 니치(A/B/C/E) - 애드센스 "가치가 별로 없는 콘텐츠" 판정 이후
        # 매일 발행 대신 화/일을 휴무일로 두고 주 5회만 발행한다
        # (REST_WEEKDAYS). SECOND_BLOG_CLUSTERS(T1/T2)는 simple-tech-fix에
        # 따로 발행하므로(아래) 이 후보 풀에서는 제외한다.
        if forced_cluster or kst_now.weekday() not in REST_WEEKDAYS:
            def _run_general():
                recent_titles = get_recent_titles()
                general_topic = select_niche_topic(exclude_clusters=SECOND_BLOG_CLUSTERS)
                prompt_builder = NICHE_FORMAT_PROMPT_BUILDERS[general_topic["format"]]
                prompt = prompt_builder(general_topic, recent_titles)
                _run_generation(prompt, general_topic["keyword"], niche_topic=general_topic)

            results.append(("general(new-maind)", _run_arm("general(new-maind)", _run_general)))
        else:
            weekday_kr = "월화수목금토일"[kst_now.weekday()]
            print(
                f"오늘은 휴무일입니다 (KST {kst_now.date().isoformat()} {weekday_kr}요일) - "
                "발행 빈도를 줄이고 품질에 집중하기 위해 new-maind(A/B/C/E) 발행은 건너뜁니다."
            )

    if run_tech_fix:
        # SECOND_BLOG_CLUSTERS(T1/T2, AI/테크 논평) -> simple-tech-fix는
        # 하루 3번(09/12/17시 KST) 발행해달라는 요청에 따라 휴무일 없이
        # 그때마다 새 글 하나씩 낸다("tech_fix"라는 갈래 이름 자체는 이
        # 슬롯을 처음 도입했을 때(당시엔 트러블슈팅)의 이름을 그대로 쓰는
        # 것뿐이다 - RUN_ARMS 값이라 워크플로 cron 분기와 맞물려 있어서
        # 이름만 따로 바꾸지 않았다). 블로그 ID를 먼저 조회해서, 실패하면
        # (권한 없음 등) Claude 호출 자체를 하지 않고 건너뛴다 - 어차피
        # 발행 못 할 글에 API 비용을 쓸 필요가 없다.
        def _run_daily_tech_fix():
            second_blog_id = resolve_blog_id_by_url(SECOND_BLOG_URL)
            if not second_blog_id:
                sys.exit(f"{SECOND_BLOG_URL} 블로그 ID를 찾지 못해 이번 글 발행을 건너뜁니다.")
            recent_titles = get_recent_titles()
            ai_topic = select_niche_topic(
                include_clusters=SECOND_BLOG_CLUSTERS, used_ids_file=SECOND_BLOG_USED_TOPIC_IDS_FILE
            )
            prompt_builder = NICHE_FORMAT_PROMPT_BUILDERS[ai_topic["format"]]
            prompt = prompt_builder(ai_topic, recent_titles)
            _run_generation(
                prompt,
                ai_topic["keyword"],
                niche_topic=ai_topic,
                blog_id=second_blog_id,
                used_ids_file=SECOND_BLOG_USED_TOPIC_IDS_FILE,
            )

        results.append(("daily(simple-tech-fix)", _run_arm("daily(simple-tech-fix)", _run_daily_tech_fix)))

    sync_blogger_static_pages()
    sync_second_blogger_static_pages()

    if results and not any(ok for _, ok in results):
        sys.exit(f"이번 실행의 모든 발행 갈래가 실패했습니다: {[label for label, _ in results]}")


if __name__ == "__main__":
    main()
