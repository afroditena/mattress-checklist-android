'use client';

import { createClient } from '@/lib/supabase/client';

function KakaoIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M12 3C6.48 3 2 6.48 2 10.78c0 2.73 1.83 5.13 4.6 6.52-.2.73-.72 2.64-.83 3.05-.13.5.18.5.38.36.16-.11 2.5-1.7 3.52-2.4.75.11 1.53.17 2.33.17 5.52 0 10-3.48 10-7.78C22 6.48 17.52 3 12 3z" />
    </svg>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden>
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.07 5.07 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.99.66-2.25 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.85A11 11 0 0 0 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09A6.59 6.59 0 0 1 5.5 12c0-.73.13-1.43.34-2.09V7.06H2.18A11 11 0 0 0 1 12c0 1.77.42 3.45 1.18 4.94l3.66-2.85z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 1.99 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.85C6.71 7.31 9.14 5.38 12 5.38z"
      />
    </svg>
  );
}

export default function LoginPage() {
  const supabase = createClient();

  const signInWith = async (provider: 'kakao' | 'google') => {
    await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted px-4">
      <div className="w-full max-w-sm space-y-6 rounded-lg border border-border bg-card p-8 shadow-sm">
        <div className="text-center">
          <h1 className="text-2xl font-bold">쇼츠 대본 AI</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            상품 정보만 입력하면 30초 쇼핑 쇼츠 대본이 완성돼요
          </p>
        </div>

        <div className="space-y-3">
          <button
            onClick={() => signInWith('kakao')}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-[#FEE500] py-2.5 text-sm font-medium text-black/85 transition hover:brightness-95"
          >
            <KakaoIcon />
            카카오로 시작하기
          </button>
          <button
            onClick={() => signInWith('google')}
            className="flex w-full items-center justify-center gap-2 rounded-md border border-border bg-white py-2.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50"
          >
            <GoogleIcon />
            Google로 시작하기
          </button>
        </div>
      </div>
    </div>
  );
}
