# 자동 블로그 파이프라인 (auto-blog-autopilot)

사람이 매일 손대지 않아도, 정해진 시간에 Claude API가 블로그 글을 자동으로 쓰고
`docs/` (GitHub Pages)에 자동으로 발행하는 파이프라인입니다.

**2026-09-18: 니치를 "AI-Powered Productivity Tools"(영어, 미국 독자 대상)로
완전히 전환했습니다.** 이전 니치(매트리스/건강/재무/정치경제 핫이슈, 전부
한국어)는 폐기됐고, `docs/_posts`의 예전 한국어 글들은 아카이브로 그대로
남아있지만 새 글은 전부 이 새 니치/포맷으로 나갑니다.

## 먼저 알아두실 점 (현실적인 기대치)

- **이건 "5일 안에 300만원"을 만드는 도구가 아닙니다.** 완전 무인 자동화 자체는
  지금 바로 돌아가지만, 실제 광고/제휴 수익이 붙으려면 애드센스 심사, 트래픽,
  검색엔진 노출까지 보통 몇 주~몇 달이 걸립니다.
- 이 저장소는 원래 Android 앱(mattress-checklist-android) 저장소라서, 이 프로젝트는
  `auto-blog-autopilot/`(자동화 코드)와 최상위 `docs/`(GitHub Pages가 요구하는
  경로라 부득이하게 루트에 위치) 두 곳에 나뉘어 있습니다. 나중에 완전히 분리하고
  싶으시면 별도 저장소를 만들어주시면 이 폴더 내용을 그대로 옮겨드릴 수 있습니다.
- **스케줄(cron) 실행은 `main` 브랜치에 병합된 이후에만 자동으로 동작합니다**
  (GitHub 정책). 병합 전에는 Actions 탭에서 수동 실행(`workflow_dispatch`)으로만
  테스트할 수 있습니다.

## 어떻게 동작하나요?

1. GitHub Actions가 하루 4번(KST 오전 7시/9시/낮 12시/오후 5시) 실행되고,
   어느 시간에 켰는지에 따라 한 번에 한 갈래만 돕니다 - "일반 니치"(A/B/C/E,
   new-maind, 오전 7시)와 "AI/테크 논평 전용"(T1/T2, simple-tech-fix, 9시/
   12시/17시 - 하루 3번 발행해달라는 요청으로 이렇게 나눴습니다). 일반
   니치는 화요일/일요일이 `REST_WEEKDAYS`로 지정된 휴무일이라 지정 발행
   (아래 4번)이 없는 한 건너뛰지만(매일 발행 대신 주 5회로 품질에 집중),
   AI/테크 논평 전용 갈래는 휴무일 없이 매번 돕니다. 어느 cron이 실행을
   켰는지로 `RUN_ARMS` 환경변수가 자동으로 정해지고(워크플로 파일 참고),
   두 갈래는 서로 독립적이라 한쪽이 API 오류로 실패해도 다른 쪽에는 영향이
   없습니다 (자세한 내용은 "5-1. 클러스터별로 다른 Blogger 블로그에
   발행하기" 참고).
2. `data/topics.json`에 니치별 키워드 풀이 고정으로 들어있습니다: new-maind용
   A/B/C/E(각 6개, 총 24개) + simple-tech-fix용 T1/T2(2026-09-26부터
   AI/테크 논평 니치, 총 20개). 일반 니치 갈래는 A/B/C/E에서, AI/테크
   논평 전용 갈래는 T1/T2에서만 클러스터 가중치 기반 가중 무작위로 고릅니다:
   - **A. AI Writing & Content Tools** — ChatGPT/Claude 실사용 가이드 (How-to 포맷)
   - **B. AI Productivity & Automation** — 일정관리·자동화 가이드 (How-to 포맷)
   - **C. Free/Budget Software Alternatives** — Canva/Notion/Zoom/Photoshop/
     Grammarly/Slack 무료 대안 (Alternative 포맷)
   - **E. Productivity Software Comparisons** — Notion vs Obsidian 등 정면 비교
     (Comparison 포맷, 광고 친화적이라 우선 발행)
   - **T1. AI Tool Verdicts** — 개별/맞대결 AI 툴에 대한 주관적 평가
     (AI Commentary 포맷, 가중치 3, 발행 비중이 더 큼)
   - **T2. AI & Tech Trend Watch** — AI/테크 업계 트렌드에 대한 논평
     (AI Commentary 포맷, 가중치 2)

   `NICHE_CLUSTER_WEIGHT`는 new-maind 쪽은 단순 How-to(A/B)보다 비교/대안형
   (C/E)을 더 자주 고르도록(Google AI Overviews가 단순 정보성 How-to 검색의
   클릭률을 크게 깎아먹는 반면 비교·대안·구매의도 검색은 상대적으로 안전
   하다는 신호에 따른 전략), simple-tech-fix 쪽은 구매의도·광고 친화도가
   더 높다고 본 개별/맞대결 툴 평가(T1)를 업계 트렌드 논평(T2)보다 더 자주
   고르도록 되어 있습니다. 최근 사용한 주제(`data/used_topic_ids.json`)는
   먼저 제외해서, 풀을 거의 다 돌기 전까지는 같은 주제가 반복되지 않습니다.
3. 포맷마다 프롬프트 구조가 다릅니다 (`NICHE_FORMAT_PROMPT_BUILDERS`의 4개 함수):
   - **How-to**: 직접 답변 → 준비물 → 단계별 설명 → FAQ → 요약
   - **Alternative**: 직접 답변 → 선정 기준 → 목록형 비교 → 표 → FAQ
   - **Comparison**: 직접 답변(결론 요약) → 비교표 → 항목별 분석 → 추천 대상 → FAQ
   - **AI Commentary** (T1/T2 전용): 필자의 결론(퀵 앤서)을 먼저 던지고 →
     "What's Actually Going On"(검증된 사실) → "My Take"(주관적 판단·근거를
     명시적으로 밝히는 섹션) → 반대 논거에 대한 공정한 언급 → "Bottom Line"
     → FAQ 순서로 씁니다. new-maind의 중립적인 How-to/대안/비교 가이드와
     겹치지 않도록 의도적으로 "결론을 분명히 내리는 논평" 포맷으로
     차별화했습니다. 가격·기능·검색 순위 등 사실은 여전히 `web_search`로
     검증하게 하고 지어내지 못하게 하지만, 그 사실을 어떻게 해석하느냐는
     필자(모델) 관점을 분명히 드러내라고 명시적으로 요구합니다.

   전부 Claude의 `web_search` 도구를 켜서 실제 검색 결과(가격 페이지, 공식
   지원문서, 업계 리포트 등)를 근거로 쓰게 하고, 그 출처 URL을
   `SOURCES` 필드로 받습니다 (본문에 인용될 뿐 아니라 아래 4번의 스크린샷
   캡처 대상으로도 쓰입니다). 특정 제품에 실제 제휴 링크를 달아 발행하고
   싶은 날짜가 있으면(현재는 이 니치와 맞는 제품이 없어 쓰이지 않지만 기능은
   남겨뒀습니다), 이 풀을 건드리지 않고 "쿠팡파트너스 지정 발행" 오버라이드로
   날짜·제품·링크를 직접 지정할 수 있습니다.
4. 생성된 글을 `docs/_posts/`에 Jekyll 포스트 파일로 저장합니다. 이미지는
   Unsplash 일반 스톡사진이 아니라, `SOURCES`로 받은 공식 페이지(가격/지원문서
   등, 로그인 불필요)를 Playwright(headless Chromium)로 직접 캡처해서 씁니다
   — "직접 제작/캡처/AI생성/명확한 라이선스만" 원칙상 소프트웨어 화면 캡처
   자리에 무관한 스톡사진을 쓸 수 없어서입니다. 캡처된 화면은
   `docs/assets/img/<글 slug>/`에 저장되고, 로그인이 필요하거나 캡처가
   실패하면 그 자리는 조용히 건너뜁니다. 캡처된 화면이 하나도 없을 때만
   Unsplash 사진 1장을 대표 이미지로 대신 씁니다 (아래 "6. 무료 사진 자동
   삽입" 참고).
5. 자동으로 커밋·푸시하면, GitHub Pages가 자동으로 사이트를 다시 빌드해서
   글이 공개됩니다. 구글 Blogger 인증 정보가 설정돼 있으면 같은 글을
   Blogger에도 동시 발행합니다 — T1/T2(AI/테크 논평) 글은 new-maind가
   아니라 같은 구글 계정 소유의 별도 블로그(simple-tech-fix.blogspot.com)로,
   나머지 클러스터는 new-maind로 갑니다 (아래 "5-1. 클러스터별로 다른
   Blogger 블로그에 발행하기" 참고). GitHub Pages는 이 분기와 무관하게
   항상 전체 클러스터를 보관합니다.
6. 최근 글 제목을 프롬프트에 같이 넘겨서 내용이 겹치지 않게 하고, 이번에
   고른 주제 id를 `data/used_topic_ids.json`에 남겨서 같은 주제가 당분간
   반복되지 않게 합니다.

## 설정 방법 (최초 1회만 사람이 할 일)

### 1. Claude API 키 등록 (필수)

1. https://console.anthropic.com 에서 API 키를 발급받으세요.
2. 이 저장소 GitHub 페이지 → **Settings → Secrets and variables → Actions →
   New repository secret**
3. Name: `ANTHROPIC_API_KEY`, Value: 발급받은 키 → Save

이 키가 없으면 워크플로가 바로 실패하며, GitHub가 실패 이메일을 보내줍니다
(즉, 조용히 멈추지 않고 알림이 옵니다).

### 2. GitHub Pages 활성화 (필수, main 병합 후)

**Settings → Pages**
- Source: `Deploy from a branch`
- Branch: `main` / 폴더: `/docs`
- Save

몇 분 후 `https://afroditena.github.io/mattress-checklist-android/` 에서
사이트를 볼 수 있습니다.

### 3. Google 애드센스

승인에 필요한 사전 준비(개인정보처리방침 `docs/privacy.md`, 소개 페이지
`docs/about.md`, 헤더/푸터 내비게이션)는 이미 만들어져 있습니다. 남은 건
사람이 계정으로 직접 해야 하는 부분뿐입니다.

1. **GitHub Pages와 Blogger 중 어디로 신청할지 고르기**: 이 파이프라인은
   같은 글을 두 곳에 동시 발행합니다(5번 참고). 애드센스는 둘 중 아무
   도메인으로나 신청할 수 있는데,
   - **Blogger(`new-maind.blogspot.com`)**: Blogger 대시보드 →
     **수익 창출(Earnings)** 탭에서 애드센스 계정을 바로 연결·신청할 수
     있습니다. 코드를 만질 필요가 전혀 없고, 승인되면 광고 위치도
     Blogger가 자동으로 잡아줍니다. 실제 독자가 보는 메인 채널이라 우선
     추천합니다.
   - **GitHub Pages(`https://afroditena.github.io/mattress-checklist-android/`)**:
     https://adsense.google.com 에서 이 URL로 별도 신청. 프로젝트 경로형
     URL이라 루트 도메인보다 심사가 조금 더 까다로울 수 있습니다.
   - 둘 다 신청해도 무방합니다(사이트 추가는 계정당 여러 개 가능).
2. **심사 기준**: 콘텐츠 양·트래픽에 정해진 최소치는 없지만, 실질적인
   정보가 담긴 글이 있고, 개인정보처리방침 페이지가 있고, 정책 위반
   콘텐츠(성인물, 저작권 침해 등)가 없어야 승인 확률이 높습니다. "가치가
   별로 없는 콘텐츠" 판정을 받은 적이 있어서, 글자수/깊이를 늘리고 발행
   빈도를 주 5회로 낮추고 운영자 정체성을 명시하는 조치를 이미 반영해뒀습니다
   (`docs/about.md` 참고). 보통 심사에 며칠~몇 주가 걸립니다 — 여기가
   유일하게 "사람이 기다려야 하는" 구간입니다.
3. **승인 후 (GitHub Pages 쪽)**: 발급되는 스크립트 태그를
   `docs/_includes/head-custom.html`에 그대로 붙여넣고, 애드센스가 안내하는
   `ads.txt` 내용(`google.com, pub-XXXXXXXXXXXXXXXX, DIRECT,
   f08c47fec0942fa0` 형식)을 `docs/ads.txt` 파일로 만들어 커밋하세요.
   (Blogger 쪽은 Earnings 탭 안내만 따라가면 이 두 단계가 필요 없습니다.)
4. 그 이후로는 완전 자동 — 새 글이 올라올 때마다 광고도 자동으로 붙습니다.

### 4. 쿠팡파트너스로 제휴 수익 추가 (현재 미사용, 기능만 유지)

새 니치(AI 생산성 툴)에는 쿠팡파트너스로 소개할 만한 실물 제품이 없어서,
이 오버라이드는 현재 쓰이지 않습니다. 다만 나중에 필요해질 수 있어 코드는
그대로 남겨뒀습니다: `manual_topic.json`(1건) 또는
`manual_topic_queue.json`(여러 건을 날짜 순서대로)에 `topic`/`product_name`/
`product_info`와 `affiliate_html`/`disclosure_text`(또는
`affiliate_url`/`affiliate_label`)를 넣어두면, 다음 실행이 이 항목으로만
글을 쓰고 평소 주제 풀은 건드리지 않습니다.

### 5. (선택) 구글 Blogger에도 동시 발행

같은 글을 [Blogger](https://blogger.com)에도 자동으로 함께 올릴 수 있습니다. 공식
Blogger API를 쓰기 때문에 확실하게 자동화되지만, **설정 과정이 앞의 단계들보다
좀 더 복잡합니다** (구글 클라우드 콘솔을 한 번 거쳐야 합니다).

1. **Blogger 블로그 만들기**: https://blogger.com 에서 새 블로그 생성 (없으면).
   블로그 설정(Settings) 페이지 URL에 있는 숫자가 "블로그 ID"입니다 — 메모해두세요.
2. **구글 클라우드 콘솔에서 프로젝트 만들기**: https://console.cloud.google.com
   → 새 프로젝트 생성.
3. **Blogger API 사용 설정**: 왼쪽 메뉴 `API 및 서비스 → 라이브러리` → "Blogger API v3"
   검색 → 사용(Enable).
4. **OAuth 동의 화면 구성**: `API 및 서비스 → OAuth 동의 화면` → User Type: 외부 →
   앱 이름 등 최소 정보만 입력 → 테스트 사용자에 본인 구글 계정 추가.
5. **OAuth 클라이언트 ID 만들기**: `API 및 서비스 → 사용자 인증 정보 → 사용자 인증
   정보 만들기 → OAuth 클라이언트 ID` → 애플리케이션 유형: 웹 애플리케이션 →
   승인된 리디렉션 URI에 `https://developers.google.com/oauthplayground` 추가 →
   생성되는 **클라이언트 ID**와 **클라이언트 보안 비밀**을 저장해두세요.
6. **Refresh Token 발급** (OAuth Playground 이용, 코드 실행 없이 브라우저로만 진행):
   - https://developers.google.com/oauthplayground 접속
   - 오른쪽 위 톱니바퀴 아이콘 → "Use your own OAuth credentials" 체크 →
     방금 만든 클라이언트 ID/보안 비밀 입력
   - 왼쪽 목록에서 "Blogger API v3" 찾아서 `https://www.googleapis.com/auth/blogger`
     스코프 체크 → **Authorize APIs** → 본인 구글 계정으로 로그인/동의
   - **Exchange authorization code for tokens** 클릭 → 나오는 **Refresh token** 복사
7. **GitHub Secrets에 4개 등록** (Settings → Secrets and variables → Actions):
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REFRESH_TOKEN`
   - `BLOGGER_BLOG_ID`

이 4개가 모두 등록되면, 다음 자동 발행부터 같은 글이 Blogger에도 함께 올라갑니다.
하나라도 비어 있으면 스크립트가 자동으로 Blogger 발행만 건너뛰고 GitHub Pages
발행은 평소대로 계속됩니다 (즉, 이 설정을 안 해도 기존 기능은 전혀 영향 없습니다).

#### 5-1. 클러스터별로 다른 Blogger 블로그·다른 빈도로 발행하기 (현재: T1/T2 AI/테크 논평, 하루 3번)

2026-09-20부터, simple-tech-fix로 나가는 두 번째 블로그 갈래는 아예 완전히
별도 갈래로 분리됐습니다. 워크플로의 cron이 4개로 늘었고(`.github/workflows/
auto-blog-daily-post.yml`), 어느 cron이 실행을 켰는지에 따라 `RUN_ARMS`
환경변수("general"/"tech_fix"/빈 문자열=둘 다)가 자동으로 정해져서, `main()`이
그에 맞는 갈래만 돕니다. 이 두 번째 갈래의 니치는 2026-09-22에 "원격근무 툴
트러블슈팅"에서 "미국 개인금융"으로, **2026-09-26부터는 "금융은 빼고 테크/AI로
바꿔달라"는 요청에 따라 "AI/테크 논평(AI Tool Verdicts + AI & Tech Trend
Watch)"으로 다시 전환했습니다** - `RUN_ARMS` 값 이름 자체는 `"tech_fix"`를
그대로 쓰고 있지만(도입 당시 이름을 코드·워크플로 전반에서 바꾸지 않았을
뿐), 실제로 다루는 내용과는 이제 무관합니다:

- **일반 니치 갈래** (`RUN_ARMS=general`, A/B/C/E,
  `select_niche_topic(exclude_clusters=SECOND_BLOG_CLUSTERS)`) — KST 오전
  7시 cron 하나로 돌고, 기존처럼 `BLOGGER_BLOG_ID`(new-maind)로 발행되며
  화/일 휴무일(`REST_WEEKDAYS`)이 그대로 적용됩니다.
- **AI/테크 논평 전용 갈래** (`RUN_ARMS=tech_fix`, T1/T2만,
  `select_niche_topic(include_clusters=SECOND_BLOG_CLUSTERS)`) — KST 오전
  9시/낮 12시/오후 5시, 하루 3개의 별도 cron으로 돌고, 같은 구글 계정
  소유의 다른 블로그(`SECOND_BLOG_URL` 상수, 현재
  `https://simple-tech-fix.blogspot.com/`)로 **휴무일 없이 매번 새 글
  하나씩** 발행됩니다. new-maind(A/B/C/E)가 중립적인 How-to/대안/비교
  가이드 위주인 것과 겹치지 않도록, 이 갈래는 의도적으로 "결론을 분명히
  내리는 주관적 논평" 포맷으로 차별화했습니다. 2개 콘텐츠 시리즈
  (`NICHE_CLUSTER_WEIGHT`의 T1/T2 가중치):
  - **T1. AI Tool Verdicts** (가중치 3, 가장 자주 선택) — 개별/맞대결 AI
    툴에 대한 주관적 평가(무엇이 진짜 돈값을 하고 무엇이 과대평가됐는지)
  - **T2. AI & Tech Trend Watch** (가중치 2) — AI/테크 업계 트렌드에 대한
    논평(마케팅 문구를 걷어낸 실제 상황 진단)

  총 20개 주제(`data/topics.json`의 T1/T2)가 하루 3개씩 나가므로 대략
  일주일이면 한 바퀴 돕니다. 반복 주기를 늘리려면 `topics.json`에 T1/T2
  항목을 더 추가하세요. 글 포맷은 둘 다 `build_ai_commentary_prompt()`
  하나로 통일되어 있습니다: 필자의 결론(퀵 앤서) → "What's Actually Going
  On"(검증된 사실) → "My Take"(주관적 판단을 명시적으로 밝히는 섹션) →
  반대 논거에 대한 공정한 언급 → "Bottom Line" → FAQ. 가격·기능·검색
  순위 등 사실은 여전히 `web_search`로 검증하게 하고 지어내지 못하게 하되,
  그 사실을 어떻게 해석하느냐는 필자 관점을 분명히 드러내라고 프롬프트에서
  명시적으로 요구합니다(`AI_TREND_CONTEXT_BLOCK`으로 2026년 AI/테크
  트렌드에 대한 배경지식도 함께 심어줍니다 - ChatGPT/Gemini/Claude 검색
  순위, AI Overviews가 정보성 검색 CTR을 깎는 현상 등, 실제 리서치로
  확인한 내용).

`workflow_dispatch`로 수동 실행할 때는 `run_arms` 입력으로 갈래를 지정할
수 있습니다(비워두면 기존처럼 둘 다 실행). 두 갈래는 각각 `_run_arm()`으로
감싸여 있어서, 한쪽이 API 오류(레이트리밋 등)로 실패해도 다른 쪽이나 이미
성공한 글의 커밋을 막지 않습니다. 그 실행에서 시도한 갈래가 전부
실패했을 때만 워크플로 자체가 실패로 표시되어(GitHub 실패 이메일) 눈에
띕니다. GitHub Pages(docs/_posts)는 이 분기와 무관하게 항상 모든 갈래의
글을 보관하는 단일 아카이브로 남습니다.

**비용 참고**: 화/일이 아닌 날은 하루에 Claude API 호출이 총 4번(일반
니치 1 + AI/테크 논평 3)까지 나갑니다. 화/일에도 AI/테크 논평 갈래 3번은
그대로 나갑니다.

**별도 GitHub Secrets 등록이 필요 없습니다** — 같은 구글 계정 소유 블로그라면
위 4개 시크릿(특히 `GOOGLE_REFRESH_TOKEN`)이 이미 접근 권한을 갖고 있어서,
`resolve_blog_id_by_url()`이 Blogger API로 URL만 보고 블로그 ID를 매번
자동으로 조회합니다. 이 블로그가 없거나 접근 권한이 없으면(다른 계정 소유
등) 그 회차의 AI/테크 논평 글 자체를 생성하지 않고 건너뜁니다(API 비용
절약 - resolve 실패를 먼저 확인한 뒤에 Claude를 호출하므로), 로그에 이유가
남습니다.

이 블로그에도 new-maind와 똑같이 개인정보처리방침·소개 페이지가 자동으로
동기화됩니다(`sync_second_blogger_static_pages()`) - AI/테크 논평 갈래를
실행하지 않는 회차(예: 오전 7시 일반 니치 슬롯)에도 매번 블로그 ID를
조회해서 페이지 내용을 최신 상태로 맞춥니다. 내용은
`SECOND_BLOG_PRIVACY_PAGE_MD`/`SECOND_BLOG_ABOUT_PAGE_MD_TEMPLATE` 상수에서
이 블로그(2개 콘텐츠 시리즈 소개, 이 블로그는 의견/논평이라는 점)에 맞게
따로 관리합니다.

다른 클러스터도 이런 식으로 별도 블로그·별도 빈도로 분리하고 싶으면,
`generate_post.py`의 `main()`에 있는 두 갈래(일반/AI·테크 논평 전용)
패턴과 워크플로의 cron/`RUN_ARMS` 계산 패턴을 참고해서 갈래를 하나 더
추가하면 됩니다. 다른 구글 계정 소유의 블로그를 추가하려면 그 계정으로
6단계 OAuth 절차를 다시 밟아 별도 시크릿(예: `GOOGLE_REFRESH_TOKEN_2`)으로
등록해야 합니다.

### 6. (선택) 화면 캡처 실패 시 대체용 무료 사진

기본 이미지 소스는 Playwright로 직접 캡처하는 공식 페이지 화면이라 별도
설정이 필요 없습니다 (Chromium은 워크플로가 매번 자동으로 설치합니다).
[Unsplash](https://unsplash.com) 키는 그 캡처가 하나도 성공하지 못했을 때만
쓰이는 대체 수단입니다.

1. https://unsplash.com/developers 접속 → 계정 없으면 가입 → **"Your apps"** →
   **"New Application"** 클릭
2. 약관 체크 후 앱 이름/설명 아무거나 입력 (예: 이름 `auto-blog-autopilot`,
   설명 `personal blog automation`)
3. 만들어진 앱 페이지에서 **"Access Key"** 복사
4. **GitHub Secrets에 등록** (Settings → Secrets and variables → Actions):
   - `UNSPLASH_ACCESS_KEY`

미설정 시에는 캡처가 전부 실패했을 때 이미지 없이 글만 발행되니, 이 설정을
안 해도 기존 기능에 영향 없습니다.

## 커스터마이징

- **주제 추가/수정**: `data/topics.json`에 `{id, cluster, cluster_name,
  keyword, format, content_type}` 형식으로 항목을 추가하면 됩니다. `format`은
  `how_to`/`alternative`/`troubleshoot`/`comparison` 중 하나여야
  `NICHE_FORMAT_PROMPT_BUILDERS`가 알맞은 프롬프트 빌더를 찾을 수 있습니다.
- **클러스터 발행 우선순위 변경**: `scripts/generate_post.py`의
  `NICHE_CLUSTER_WEIGHT` 딕셔너리를 조정하세요.
- **휴무일(발행 빈도) 변경**: 같은 파일의 `REST_WEEKDAYS` 튜플을 조정하세요
  (월요일=0 ... 일요일=6).
- **발행 시간 변경**: `.github/workflows/auto-blog-daily-post.yml`의
  `cron` 값을 수정하세요 (UTC 기준).
- **모델 변경**: 기본값은 `claude-opus-5`입니다. 매일 자동으로 도는 반복 작업이라
  비용을 더 아끼고 싶다면, 워크플로 파일에 `CLAUDE_MODEL` 환경변수를
  `claude-sonnet-5` 또는 `claude-haiku-4-5`로 지정해서 바꿀 수 있습니다.
  (모델 변경은 품질/비용 트레이드오프이니 본인 판단으로 결정하시면 됩니다.)
- **글 톤/분량/구조**: `scripts/generate_post.py`의 `build_how_to_prompt`/
  `build_alternative_prompt`/`build_troubleshoot_prompt`/
  `build_comparison_prompt` 함수에서 조정.

## 비용 감각

Claude Opus 5 기준, 글 1편당 입력+출력 토큰이 대략 수천 토큰 수준이라
주 5회 발행 시 한 달 비용은 대략 몇 달러 수준으로 예상됩니다(실제 사용량에
따라 달라집니다). `claude-sonnet-5`나 `claude-haiku-4-5`로 바꾸면 더 저렴합니다.

## 로컬에서 테스트하기

```bash
cd auto-blog-autopilot
pip install -r requirements.txt
python -m playwright install chromium  # 화면 캡처를 로컬에서도 테스트하려면
export ANTHROPIC_API_KEY=sk-ant-...
python scripts/generate_post.py
```

`docs/_posts/`에 새 글이 생기는지, `docs/assets/img/`에 캡처된 스크린샷이
생기는지 확인하세요.
