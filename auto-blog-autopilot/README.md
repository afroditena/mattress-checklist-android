# 자동 블로그 파이프라인 (auto-blog-autopilot)

사람이 매일 손대지 않아도, 정해진 시간에 Claude API가 블로그 글을 자동으로 쓰고
`docs/` (GitHub Pages)에 자동으로 발행하는 파이프라인입니다.

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

1. 매일 (KST 오전 7시) GitHub Actions가 실행됩니다.
2. `scripts/generate_post.py`가 `data/topics.txt`의 큐 맨 앞 5개 주제 후보를
   놓고 검색량(Google 트렌드·네이버 데이터랩)·자체 유입량/체류시간(GA4)으로 1~5위를 매긴 뒤
   1위 주제로 Claude API를 통해 글을 생성합니다 (설정 안 해도 예전처럼 그냥
   순서대로 FIFO 발행 — 자세한 내용은 "7. 검색량 + 자체 유입량 기반 주제
   순위 매기기" 참고).
3. 생성된 글을 `docs/_posts/`에 Jekyll 포스트 파일로 저장합니다.
4. 자동으로 커밋·푸시하면, GitHub Pages가 자동으로 사이트를 다시 빌드해서
   글이 공개됩니다.
5. 그날 선택된 주제만 큐 맨 뒤로 돌아가고, 나머지 후보는 그대로 앞쪽에 남아
   다음날 다시 후보가 됩니다 (최근 글 제목을 프롬프트에 같이 넘겨서 내용이
   겹치지 않게 합니다).

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

### 3. (나중에, 트래픽이 좀 쌓이면) Google 애드센스

1. https://adsense.google.com 에서 사이트로 가입 신청 (심사에 콘텐츠·트래픽 필요,
   보통 몇 주 소요 — 여기가 유일하게 "사람이 기다려야 하는" 구간입니다).
2. 승인되면 발급되는 스크립트 태그를 `docs/_includes/head-custom.html`에
   그대로 붙여넣기.
3. 그 이후로는 완전 자동 — 새 글이 올라올 때마다 광고도 자동으로 붙습니다.

### 4. (선택) 쿠팡파트너스로 제휴 수익 추가

스크립트는 매 글마다 관련 키워드로 **일반 쿠팡 검색 링크**를 자동으로 넣어줍니다
(이 자체는 수익화되지 않습니다). 실제로 수수료가 붙게 하려면:

1. https://partners.coupang.com 가입.
2. 대시보드의 "딥링크 변환" 기능으로, 글에 들어간 검색 링크를 실제 트래킹
   링크로 바꿔서 교체.

이 부분만큼은 쿠팡파트너스가 계정별 승인·링크 발급 방식이라 완전 자동화가
어렵습니다. 애드센스만으로도 충분히 무인 운영이 가능하니, 쿠팡 연동은
선택사항으로 남겨두었습니다.

### 5. (선택) 구글 Blogger에도 동시 발행

같은 글을 [Blogger](https://blogger.com)에도 자동으로 함께 올릴 수 있습니다. 공식
Blogger API를 쓰기 때문에 확실하게 자동화되지만, **설정 과정이 앞의 단계들보다
좀 더 복잡합니다** (구글 클라우드 콘솔을 한 번 거쳐야 합니다). 참고로 한국
독자 기준으로는 Blogger보다 네이버가 노출이 잘 되는 편이라, 이건 "추가 채널"
정도로 생각하시면 됩니다.

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

### 6. (선택) 글마다 어울리는 무료 사진 자동 삽입

[Unsplash](https://unsplash.com)에서 그날 글 내용에 맞는 무료 스톡 사진을 찾아
본문 맨 위에 자동으로 넣어줍니다 (사진작가·Unsplash 출처 표기 포함). 앞의
Blogger 설정보다 훨씬 간단합니다 — 로그인 인증 절차 없이 키 하나만 발급받으면
끝입니다.

1. https://unsplash.com/developers 접속 → 계정 없으면 가입 → **"Your apps"** →
   **"New Application"** 클릭
2. 약관 체크 후 앱 이름/설명 아무거나 입력 (예: 이름 `auto-blog-autopilot`,
   설명 `personal blog automation`)
3. 만들어진 앱 페이지에서 **"Access Key"** 복사
4. **GitHub Secrets에 등록** (Settings → Secrets and variables → Actions):
   - `UNSPLASH_ACCESS_KEY`

이것만 등록하면 다음 발행부터 사진이 자동으로 붙습니다. 미설정 시에는 사진 없이
글만 발행되니, 역시 이 설정을 안 해도 기존 기능에 영향 없습니다. 무료(Demo) 앱
기준 시간당 50회 요청 한도가 있는데, 하루 1편 발행에는 충분합니다.

### 7. (선택) 검색량 + 자체 유입량 기반 주제 순위 매기기

기존에는 `data/topics.txt`에 있는 주제를 그냥 순서대로(FIFO) 하나씩 꺼내
글을 썼습니다. 이 기능을 켜면, 매일 발행 전에 큐 맨 앞 5개 주제를 놓고

1. **Google 트렌드**로 최근 1개월간 한국에서 검색량이 높은 주제인지,
2. **네이버 데이터랩**(검색어트렌드 공식 API)으로도 최근 검색량이 높은
   주제인지 — 한국 사용자 기준으로는 이게 Google 트렌드보다 더 정확한
   경우가 많아서 같이 참고합니다,
3. **GA4**로 이 블로그에서 실제로 조회수·체류시간이 좋았던 주제와
   비슷한지

를 함께 점수화해서 1~5위를 매기고, **1위 주제로 그날 글을 씁니다.** 밀린
후보들은 큐 맨 앞쪽에 그대로 남아서 다음날 다시 후보가 됩니다.

**세 가지 모두 선택 사항입니다.** 아무것도 설정하지 않으면 예전과 똑같이
큐 순서대로(FIFO) 발행되고, 원인이 무엇이든(트렌드 조회 실패, 네이버/GA4
미설정, 데이터 없음 등) 실패하면 자동으로 조용히 넘어갑니다 — 살아있는
신호만으로 순위를 매기고, 전부 실패하면 FIFO로 돌아갑니다. 즉 이 설정을
하나도 안 해도 기존 기능에는 전혀 영향이 없습니다.

#### 7-1. Google 트렌드 (검색량) — 설정할 것 없음

`pytrends`라는 라이브러리로 Google 트렌드 데이터를 API 키나 로그인 없이
바로 가져옵니다. 그래서 **사람이 따로 설정할 게 없습니다** — 코드가
병합되는 순간부터 자동으로 동작합니다. 다만 이건 구글의 비공식 API라
가끔 레이트리밋에 걸리거나 응답 형식이 바뀔 수 있는데, 그런 경우에도
발행 자체는 실패하지 않고 검색량 점수 없이(또는 완전 FIFO로) 계속됩니다.

#### 7-2. 네이버 데이터랩 (검색량, 로그인 불필요)

**중요**: 네이버 계정 ID/비밀번호를 저장하거나 로그인 세션을 자동으로
연결하는 방식이 아닙니다 (계정 정보 유출 위험, 이용약관 문제, 로그인
화면이 바뀌면 계속 깨지는 문제가 있어서 이렇게 만들지 않았습니다).
대신 네이버가 정식으로 제공하는 **오픈 API**를 씁니다 — Unsplash 키
발급받는 것과 비슷한 난이도로, 개발자센터에서 앱 하나 등록하면 끝입니다.

1. https://developers.naver.com/apps/#/register 접속 → 네이버 계정으로
   로그인 (자동화용 계정이 아니라 본인 계정으로 1회만 로그인해서 앱을
   등록하는 것이며, 이후 자동화는 이 로그인 세션을 쓰지 않습니다).
2. 애플리케이션 이름 아무거나 입력 (예: `auto-blog-autopilot`).
3. 사용 API에서 **"검색"**을 체크 (데이터랩 검색어트렌드가 이 안에
   포함되어 있습니다).
4. 비로그인 오픈 API 서비스 환경에 **"WEB 설정"**을 추가하고, 웹
   서비스 URL에 `https://afroditena.github.io` 입력 → 등록.
5. 등록 완료 화면에서 **Client ID**와 **Client Secret**을 복사.
6. **GitHub Secrets에 2개 등록** (Settings → Secrets and variables →
   Actions):
   - `NAVER_CLIENT_ID`
   - `NAVER_CLIENT_SECRET`

이 2개가 등록되면 다음 발행부터 네이버 검색량이 순위에 반영됩니다.
미설정이면 이 신호 없이(Google 트렌드/GA4만으로, 또는 전부 없으면
FIFO로) 계속 동작합니다.

#### 7-3. GA4 추적 스크립트 심기 (블로그 방문자 데이터 쌓기 시작)

GA4로 "자체 유입량/체류시간"을 알려면, 먼저 이 블로그에 GA4 추적
스크립트가 붙어 있어야 하고, 데이터가 실제로 쌓이는 데 보통 몇 주가
걸립니다 — 그러니 이 단계는 최대한 빨리 해두는 게 좋습니다.

1. https://analytics.google.com 접속 → 계정 없으면 만들기 → **관리(톱니바퀴)
   → 속성 만들기**로 새 GA4 속성 생성 (이름은 아무거나, 예: "생활 정보 블로그").
2. 속성 생성 과정에서 **데이터 스트림 → 웹**을 추가하고, 웹사이트 URL에
   `https://afroditena.github.io/mattress-checklist-android/` 입력.
3. 만들어진 웹 스트림 상세 화면에 나오는 **측정 ID** (`G-`로 시작하는 값)를
   복사.
4. 이 저장소의 `docs/_config.yml` 파일을 열어서
   `google_analytics: ""` 부분을 `google_analytics: "G-XXXXXXXXXX"`
   (복사한 측정 ID)로 바꾸고 커밋. 이 값은 비밀값이 아니라 어차피 모든
   방문자 브라우저에 그대로 노출되는 값이라, GitHub Secrets가 아니라
   이렇게 파일에 직접 적으면 됩니다.
5. (선택) Blogger에도 같이 발행 중이라면, Blogger 관리 화면 →
   **설정 → 애널리틱스 → Google 애널리틱스 속성 ID**에도 같은 측정 ID를
   붙여넣으면 Blogger 쪽 방문자도 같은 GA4 속성에서 볼 수 있습니다.

이렇게 해두면 그 순간부터 방문자 데이터가 GA4에 쌓이기 시작합니다
(과거 데이터는 소급 적용되지 않으니, 실제로 "유입량/체류시간 기반 순위"가
의미 있게 동작하려면 며칠~몇 주 정도 데이터가 쌓여야 합니다. 그 전까지는
자동으로 검색량 순위 또는 FIFO로 동작하니 걱정 안 하셔도 됩니다).

#### 7-4. GA4 데이터를 읽어올 서비스 계정 만들기 (자동화가 읽기 전용으로 조회)

위 7-3은 "쌓기"였고, 이번엔 자동화 스크립트가 그 데이터를 "읽어오기"
위한 인증 정보입니다.

1. https://console.cloud.google.com 접속 (Blogger 설정 때 만든 프로젝트를
   그대로 써도 되고, 새 프로젝트를 만들어도 됩니다).
2. **API 및 서비스 → 라이브러리** → "Google Analytics Data API" 검색 →
   사용(Enable).
3. **API 및 서비스 → 사용자 인증 정보 → 사용자 인증 정보 만들기 →
   서비스 계정** → 이름 아무거나 입력 (예: `ga4-reader`) → 만들기 → 완료
   (역할 부여 단계는 건너뛰어도 됩니다).
4. 만들어진 서비스 계정 목록에서 방금 만든 계정 클릭 → **키(Keys) 탭 →
   키 추가 → 새 키 만들기 → JSON** → 다운로드되는 `.json` 파일을 저장
   (이 파일 안의 `client_email` 값을 다음 단계에서 씁니다).
5. 다시 https://analytics.google.com 으로 가서 **관리 → 속성 액세스 관리
   (Property Access Management)** → 오른쪽 위 **+** → **사용자 추가** →
   방금 다운로드한 JSON 파일 안의 `client_email` 값(예:
   `ga4-reader@프로젝트명.iam.gserviceaccount.com`)을 입력 → 역할은
   **뷰어(Viewer)**로 지정 → 추가.
6. GA4 속성 상세 화면(관리 → 속성 설정)에서 **속성 ID**(숫자만, 예:
   `123456789`)를 확인 — 측정 ID(`G-...`)와는 다른 값이니 헷갈리지 않게
   주의하세요.
7. **GitHub Secrets에 2개 등록** (Settings → Secrets and variables →
   Actions):
   - `GA4_PROPERTY_ID`: 위 6번의 속성 ID (숫자만)
   - `GA4_SERVICE_ACCOUNT_JSON`: 4번에서 다운로드한 JSON 파일의 **전체
     내용을 그대로** 복사해서 붙여넣기 (파일 자체를 저장소에 올리지
     마세요 — 반드시 GitHub Secrets에만 등록)

이 2개가 모두 등록되면, 다음 자동 발행부터 GA4 데이터가 쌓인 만큼
주제 순위에 반영됩니다. 하나라도 비어 있거나 아직 데이터가 없으면
스크립트가 자동으로 검색량 순위만, 또는 완전 FIFO로 건너뜁니다.

## 커스터마이징

- **주제 추가/수정**: `data/topics.txt`에 한 줄씩 추가하면 됩니다.
- **발행 시간 변경**: `.github/workflows/auto-blog-daily-post.yml`의
  `cron` 값을 수정하세요 (UTC 기준).
- **모델 변경**: 기본값은 `claude-opus-5`입니다. 매일 자동으로 도는 반복 작업이라
  비용을 더 아끼고 싶다면, 워크플로 파일에 `CLAUDE_MODEL` 환경변수를
  `claude-sonnet-5` 또는 `claude-haiku-4-5`로 지정해서 바꿀 수 있습니다.
  (모델 변경은 품질/비용 트레이드오프이니 본인 판단으로 결정하시면 됩니다.)
- **글 톤/분량**: `scripts/generate_post.py`의 `build_prompt()` 함수에서 조정.

## 비용 감각

Claude Opus 5 기준, 글 1편당 입력+출력 토큰이 대략 수천 토큰 수준이라
하루 1회 발행 시 한 달 비용은 대략 몇 달러 수준으로 예상됩니다(실제 사용량에
따라 달라집니다). `claude-sonnet-5`나 `claude-haiku-4-5`로 바꾸면 더 저렴합니다.

## 로컬에서 테스트하기

```bash
cd auto-blog-autopilot
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python scripts/generate_post.py
```

`docs/_posts/`에 새 글이 생기는지 확인하세요.
