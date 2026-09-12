import { NextResponse } from 'next/server';
import { createServiceRoleClient } from '@/lib/supabase/server';
import { verifyTossWebhookSignature } from '@/lib/toss/server';
import { getPlan } from '@/lib/toss/plans';

export const runtime = 'nodejs';

/**
 * 토스페이먼츠 정기결제(빌링) 웹훅 처리.
 * 문서: https://docs.tosspayments.com/guides/webhook
 *
 * 이벤트 예시: PAYMENT_STATUS_CHANGED (status: DONE | CANCELED | FAILED 등)
 * 자체 정기 스케줄러(Cron)가 chargeBillingKey를 매월 호출한 뒤,
 * 토스가 그 결제 건의 최종 상태 변경을 이 웹훅으로 통지한다고 가정한다.
 */
export async function POST(req: Request) {
  const rawBody = await req.text();
  const signature = req.headers.get('TossPayments-Webhook-Signature');

  const isValid = await verifyTossWebhookSignature(rawBody, signature);
  if (!isValid) {
    return NextResponse.json({ error: 'invalid signature' }, { status: 401 });
  }

  const payload = JSON.parse(rawBody);
  const { eventType, data } = payload ?? {};

  if (eventType !== 'PAYMENT_STATUS_CHANGED' || !data) {
    // 처리 대상이 아닌 이벤트는 200으로 응답하여 재전송을 막는다.
    return NextResponse.json({ received: true });
  }

  const supabase = createServiceRoleClient();
  const { status, orderId, totalAmount, customerKey, orderName } = data;

  // orderId 형식: sub_{planId}_{userId}_{timestamp}
  const match = /^sub_(starter|pro)_([0-9a-fA-F-]{36})_/.exec(orderId ?? '');
  const planId = match?.[1];
  const userId = match?.[2];

  await supabase.from('billing_events').insert({
    user_id: userId ?? null,
    order_id: orderId ?? null,
    status,
    amount: totalAmount ?? null,
    raw_payload: payload,
  });

  if (status === 'DONE' && planId && userId) {
    const plan = getPlan(planId);
    if (plan) {
      // 정기 결제 성공 → 크레딧 충전 + 플랜 갱신
      await supabase.rpc('add_user_credits', {
        p_user_id: userId,
        p_amount: plan.credits,
        p_tier: plan.id,
      });
    }
  } else if ((status === 'FAILED' || status === 'CANCELED') && userId) {
    // 정기 결제 실패 → 플랜을 free로 강등 (크레딧은 유지, 신규 지급만 중단)
    await supabase.from('profiles').update({ tier: 'free' }).eq('id', userId);
  }

  void customerKey;
  void orderName;

  return NextResponse.json({ received: true });
}
