import { redirect } from 'next/navigation';
import Link from 'next/link';
import { createClient } from '@/lib/supabase/server';
import { TierBadge } from '@/components/dashboard/tier-badge';
import { Generator } from '@/components/dashboard/generator';

export default async function DashboardPage() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect('/login');
  }

  const { data: profile } = await supabase
    .from('profiles')
    .select('email, credits, tier')
    .eq('id', user.id)
    .single();

  const credits = profile?.credits ?? 0;
  const tier = profile?.tier ?? 'free';

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <header className="mb-8 flex flex-wrap items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-semibold">{profile?.email ?? user.email}</h1>
            <TierBadge tier={tier} />
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            잔여 크레딧: <span className="font-semibold text-foreground">{credits}회</span>
          </p>
        </div>
        <Link
          href="/pricing"
          className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
        >
          충전 / 구독하기
        </Link>
      </header>

      <Generator initialCredits={credits} />
    </div>
  );
}
