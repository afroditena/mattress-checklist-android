import { createServerClient } from '@supabase/ssr';
import { createClient as createSupabaseClient } from '@supabase/supabase-js';
import { cookies } from 'next/headers';
import type { Database } from '@/types/database';

/**
 * Server Component / Route Handler / Server Action 에서 사용하는 Supabase 클라이언트.
 * 세션 쿠키를 읽고 쓸 수 있도록 Next.js `cookies()`와 연결한다.
 */
export function createClient() {
  const cookieStore = cookies();

  return createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) => {
              cookieStore.set(name, value, options);
            });
          } catch {
            // Server Component에서 호출된 경우 무시 (미들웨어가 세션을 갱신함)
          }
        },
      },
    }
  );
}

/**
 * 서버 전용 서비스 롤 클라이언트. RLS를 우회해야 하는 웹훅/관리 작업에서만 사용.
 * 절대 클라이언트 번들에 포함되지 않도록 route handler 내부에서만 import 할 것.
 */
export function createServiceRoleClient() {
  return createSupabaseClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { persistSession: false } }
  );
}
