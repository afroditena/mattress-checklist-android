-- ============================================================================
-- 0001_init.sql
-- 쇼핑 쇼츠 대본 생성 SaaS 초기 스키마
-- ============================================================================

-- 확장 (UUID 생성용)
create extension if not exists "pgcrypto";

-- ----------------------------------------------------------------------------
-- profiles: 사용자 프로필 + 크레딧 + 결제 정보
-- ----------------------------------------------------------------------------
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text,
  credits integer not null default 10,
  tier text not null default 'free' check (tier in ('free', 'starter', 'pro')),
  billing_key text,
  customer_key text unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.profiles is '사용자 프로필, 크레딧, 구독/빌링 정보';

-- updated_at 자동 갱신 트리거
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_profiles_updated_at on public.profiles;
create trigger trg_profiles_updated_at
  before update on public.profiles
  for each row
  execute function public.set_updated_at();

-- 신규 가입 시 profiles 자동 생성 (customer_key는 user id 기반으로 고유 생성)
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email, customer_key)
  values (new.id, new.email, 'cust_' || replace(new.id::text, '-', ''))
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists trg_on_auth_user_created on auth.users;
create trigger trg_on_auth_user_created
  after insert on auth.users
  for each row
  execute function public.handle_new_user();

-- ----------------------------------------------------------------------------
-- generation_logs: 대본 생성 이력
-- ----------------------------------------------------------------------------
create table if not exists public.generation_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  product_name text not null,
  selling_points text,
  tone text not null,
  script_content jsonb,
  created_at timestamptz not null default now()
);

comment on table public.generation_logs is 'AI 쇼츠 대본 생성 이력';

create index if not exists idx_generation_logs_user_id
  on public.generation_logs (user_id, created_at desc);

-- ----------------------------------------------------------------------------
-- deduct_user_credits: 트랜잭션 안전 크레딧 차감 RPC
-- ----------------------------------------------------------------------------
create or replace function public.deduct_user_credits(
  p_user_id uuid,
  p_amount integer default 1
)
returns integer
language plpgsql
security definer set search_path = public
as $$
declare
  v_remaining integer;
begin
  if p_amount <= 0 then
    raise exception 'INVALID_AMOUNT: amount must be positive';
  end if;

  -- 행 잠금(FOR UPDATE)으로 동시 요청 시 원자적 차감 보장
  select credits into v_remaining
  from public.profiles
  where id = p_user_id
  for update;

  if v_remaining is null then
    raise exception 'PROFILE_NOT_FOUND: no profile for user %', p_user_id;
  end if;

  if v_remaining < p_amount then
    raise exception 'INSUFFICIENT_CREDITS: remaining=%, requested=%', v_remaining, p_amount
      using errcode = 'P0001';
  end if;

  update public.profiles
  set credits = credits - p_amount
  where id = p_user_id
  returning credits into v_remaining;

  return v_remaining;
end;
$$;

comment on function public.deduct_user_credits is
  '사용자 크레딧을 원자적으로 차감. 잔여 크레딧 부족 시 예외(INSUFFICIENT_CREDITS) 발생.';

-- ----------------------------------------------------------------------------
-- add_user_credits: 결제/충전 시 크레딧 지급 + 플랜 변경 RPC
-- ----------------------------------------------------------------------------
create or replace function public.add_user_credits(
  p_user_id uuid,
  p_amount integer,
  p_tier text default null
)
returns integer
language plpgsql
security definer set search_path = public
as $$
declare
  v_remaining integer;
begin
  update public.profiles
  set
    credits = credits + p_amount,
    tier = coalesce(p_tier, tier)
  where id = p_user_id
  returning credits into v_remaining;

  if v_remaining is null then
    raise exception 'PROFILE_NOT_FOUND: no profile for user %', p_user_id;
  end if;

  return v_remaining;
end;
$$;

-- ----------------------------------------------------------------------------
-- Row Level Security
-- ----------------------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.generation_logs enable row level security;

drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own"
  on public.profiles for select
  using (auth.uid() = id);

drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own"
  on public.profiles for update
  using (auth.uid() = id)
  with check (auth.uid() = id);

-- insert는 트리거(security definer)로만 수행하므로 클라이언트 insert는 막아둔다.
drop policy if exists "generation_logs_select_own" on public.generation_logs;
create policy "generation_logs_select_own"
  on public.generation_logs for select
  using (auth.uid() = user_id);

drop policy if exists "generation_logs_insert_own" on public.generation_logs;
create policy "generation_logs_insert_own"
  on public.generation_logs for insert
  with check (auth.uid() = user_id);

-- profiles/generation_logs 삭제는 애플리케이션 정책상 허용하지 않음 (정책 미생성 = 기본 거부)
