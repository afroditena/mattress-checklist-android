-- ============================================================================
-- 0002_payments.sql
-- 토스페이먼츠 정기결제 웹훅 처리를 위한 결제 이력 테이블
-- ============================================================================

create table if not exists public.billing_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles (id) on delete set null,
  order_id text,
  status text not null, -- 'DONE' | 'FAILED' | 'CANCELED' 등 토스 상태값
  amount integer,
  raw_payload jsonb,
  created_at timestamptz not null default now()
);

comment on table public.billing_events is '토스페이먼츠 정기결제 웹훅 원본 로그';

create index if not exists idx_billing_events_user_id
  on public.billing_events (user_id, created_at desc);

alter table public.billing_events enable row level security;

drop policy if exists "billing_events_select_own" on public.billing_events;
create policy "billing_events_select_own"
  on public.billing_events for select
  using (auth.uid() = user_id);

-- 웹훅은 서버(service role)에서만 기록하므로 클라이언트 insert 정책은 생성하지 않음.
