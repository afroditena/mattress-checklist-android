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

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5")
MAX_RECENT_TITLES = 10

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN", "")
BLOGGER_BLOG_ID = os.environ.get("BLOGGER_BLOG_ID", "")

UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")
UNSPLASH_APP_NAME = os.environ.get("UNSPLASH_APP_NAME", "auto-blog-autopilot")


def get_next_topic() -> str:
    if not TOPICS_FILE.exists():
        sys.exit(f"주제 큐 파일이 없습니다: {TOPICS_FILE}")

    lines = [line.strip() for line in TOPICS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        sys.exit(f"주제 큐가 비어 있습니다: {TOPICS_FILE}")

    topic = lines[0]
    rotated = lines[1:] + [topic]
    TOPICS_FILE.write_text("\n".join(rotated) + "\n", encoding="utf-8")
    return topic


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


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY 환경변수가 설정되어 있지 않습니다.")

    topic = get_next_topic()
    recent_titles = get_recent_titles()

    prompt = build_prompt(topic, recent_titles)
    raw_output = call_claude(prompt)
    title, tags, keyword, image_query, body = parse_output(raw_output, fallback_title=topic)

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

    affiliate_block = build_affiliate_block(keyword)
    post_path.write_text(front_matter + "\n" + body + affiliate_block, encoding="utf-8")

    print(f"생성 완료: {post_path.relative_to(PROJECT_DIR.parent)}")

    post_to_blogger(safe_title, body + affiliate_block)


if __name__ == "__main__":
    main()
