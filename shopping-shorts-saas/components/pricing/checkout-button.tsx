'use client';

import { useState } from 'react';
import { loadTossPayments } from '@tosspayments/payment-sdk';
import { createClient } from '@/lib/supabase/client';
import type { PlanId } from '@/lib/toss/plans';

const TOSS_CLIENT_KEY = process.env.NEXT_PUBLIC_TOSS_CLIENT_KEY!;

export function CheckoutButton({ planId, label }: { planId: PlanId; label: string }) {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (!user) {
        window.location.href = '/login';
        return;
      }

      const { data: profile } = await supabase
        .from('profiles')
        .select('customer_key, email')
        .eq('id', user.id)
        .single();

      const customerKey = profile?.customer_key ?? user.id;

      const toss = await loadTossPayments(TOSS_CLIENT_KEY);
      // 빌링키 발급창 호출 → 성공 시 successUrl로 authKey와 함께 리다이렉트됨
      await toss.requestBillingAuth('카드', {
        customerKey,
        customerEmail: profile?.email ?? user.email ?? undefined,
        successUrl: `${window.location.origin}/pricing/success?planId=${planId}`,
        failUrl: `${window.location.origin}/pricing?error=billing_auth_failed`,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className="w-full rounded-md bg-primary py-2.5 text-sm font-semibold text-primary-foreground disabled:opacity-50"
    >
      {loading ? '이동 중...' : label}
    </button>
  );
}
