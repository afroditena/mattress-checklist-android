# 쇼핑 쇼츠 대본 자동 생성 AI SaaS

국내 이커머스 셀러(쿠팡 파트너스, 스마트스토어 등)를 위한 30초 쇼핑 쇼츠 대본 자동 생성 SaaS.

## 기술 스택
- **프레임워크**: Next.js 14 (App Router) + TypeScript + Tailwind CSS
- **백엔드/DB**: Supabase (Auth, PostgreSQL, RLS, RPC)
- **AI**: Vercel AI SDK (`ai`, `@ai-sdk/openai`) 스트리밍(SSE)
- **결제**: 토스페이먼츠 정기결제(빌링키)
- **배포**: Vercel

## 현재 구현 범위 (1단계)
- [x] 프로젝트 스캐폴드 (Next.js / Tailwind / TS 설정)
- [x] DB 마이그레이션: `profiles`, `generation_logs`, `billing_events`
- [x] 크레딧 원자적 차감 RPC: `deduct_user_credits`, 충전용 `add_user_credits`
- [x] RLS 정책 (본인 데이터만 조회/수정)
- [x] Supabase Auth (카카오/구글 OAuth) + `/auth/callback`
- [x] `/api/generate` 스트리밍 대본 생성 라우트
- [x] `/api/payments/issue-billing`, `/api/payments/webhook`
- [x] `/dashboard`, `/pricing` 기본 UI

## 로컬 개발 시작하기

```bash
cd shopping-shorts-saas
npm install
cp .env.example .env.local   # 값 채우기
npm run dev
```

## Supabase 마이그레이션 적용

```bash
supabase link --project-ref <project-ref>
supabase db push
```

또는 Supabase 대시보드 SQL Editor에서 `supabase/migrations/*.sql` 파일을 순서대로 실행합니다.

## 환경변수

`.env.example` 참고. 필수 항목:

| 변수 | 설명 |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase 프로젝트 접속 정보 |
| `SUPABASE_SERVICE_ROLE_KEY` | 웹훅 등 서버 전용 작업용 (절대 클라이언트 노출 금지) |
| `OPENAI_API_KEY` | Vercel AI SDK가 사용할 모델 API 키 |
| `TOSS_SECRET_KEY` / `NEXT_PUBLIC_TOSS_CLIENT_KEY` | 토스페이먼츠 키 |
| `TOSS_WEBHOOK_SECRET` | 웹훅 서명 검증용 시크릿 |

## Supabase Auth OAuth 설정
Supabase 대시보드 → Authentication → Providers 에서 Kakao, Google Provider를 활성화하고
Redirect URL을 `<사이트 URL>/auth/callback`으로 등록하세요.

## 다음 단계 (제안)
- 토스페이먼츠 매월 자동 청구를 위한 Cron(Edge Function/Scheduled Function) 구성
- 생성 이력(`generation_logs`) 목록/재사용 UI
- 크레딧 소진 임박 알림, 관리자 대시보드
