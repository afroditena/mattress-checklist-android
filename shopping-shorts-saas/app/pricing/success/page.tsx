'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2 } from 'lucide-react';

function BillingSuccessContent() {
  const router = useRouter();
  const params = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const authKey = params.get('authKey');
    const planId = params.get('planId');

    if (!authKey || !planId) {
      setError('잘못된 접근입니다.');
      return;
    }

    (async () => {
      const res = await fetch('/api/payments/issue-billing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ authKey, planId }),
      });
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        setError(data.error ?? '결제 처리 중 오류가 발생했습니다.');
        return;
      }

      router.replace('/dashboard');
    })();
  }, [params, router]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center">
      {error ? (
        <>
          <p className="text-sm font-medium text-red-600">{error}</p>
          <a href="/pricing" className="text-sm text-primary underline">
            요금제로 돌아가기
          </a>
        </>
      ) : (
        <>
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">구독을 처리하고 있습니다...</p>
        </>
      )}
    </div>
  );
}

export default function BillingSuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      }
    >
      <BillingSuccessContent />
    </Suspense>
  );
}
