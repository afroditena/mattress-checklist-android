import { NextResponse } from 'next/server';
import { z } from 'zod';
import { createClient } from '@/lib/supabase/server';
import { issueBillingKey, chargeBillingKey } from '@/lib/toss/server';
import { getPlan } from '@/lib/toss/plans';

export const runtime = 'nodejs';

const bodySchema = z.object({
  authKey: z.string().min(1),
  planId: z.enum(['starter', 'pro']),
});

export async function POST(req: Request) {
  const supabase = createClient();
  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (authError || !user) {
    return NextResponse.json({ error: '로그인이 필요합니다.' }, { status: 401 });
  }

  const parsed = bodySchema.safeParse(await req.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: '잘못된 요청입니다.' }, { status: 400 });
  }
  const { authKey, planId } = parsed.data;

  const plan = getPlan(planId);
  if (!plan) {
    return NextResponse.json({ error: '존재하지 않는 플랜입니다.' }, { status: 400 });
  }

  const { data: profile, error: profileError } = await supabase
    .from('profiles')
    .select('customer_key')
    .eq('id', user.id)
    .single();

  if (profileError || !profile?.customer_key) {
    return NextResponse.json({ error: '프로필을 찾을 수 없습니다.' }, { status: 404 });
  }

  try {
    // 1. authKey → 빌링키 발급
    const billing = await issueBillingKey({
      authKey,
      customerKey: profile.customer_key,
    });

    // 2. 최초 정기 결제 즉시 승인 (구독 시작)
    const orderId = `sub_${planId}_${user.id}_${Date.now()}`;
    await chargeBillingKey({
      billingKey: billing.billingKey,
      customerKey: profile.customer_key,
      amount: plan.price,
      orderId,
      orderName: `쇼핑 쇼츠 대본 생성 - ${plan.name} 플랜`,
    });

    // 3. 빌링키 저장 + 플랜 크레딧 지급
    await supabase
      .from('profiles')
      .update({ billing_key: billing.billingKey, tier: plan.id })
      .eq('id', user.id);

    const { data: remainingCredits, error: creditError } = await supabase.rpc(
      'add_user_credits',
      { p_user_id: user.id, p_amount: plan.credits, p_tier: plan.id }
    );

    if (creditError) {
      return NextResponse.json(
        { error: '결제는 완료되었지만 크레딧 지급 중 오류가 발생했습니다. 고객센터에 문의해주세요.' },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      tier: plan.id,
      credits: remainingCredits,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : '결제 처리 중 오류가 발생했습니다.';
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
