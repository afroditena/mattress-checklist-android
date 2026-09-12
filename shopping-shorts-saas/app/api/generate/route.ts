import { NextResponse } from 'next/server';
import { streamText } from 'ai';
import { createOpenAI } from '@ai-sdk/openai';
import { z } from 'zod';
import { createClient } from '@/lib/supabase/server';
import { buildShortsScriptPrompt, type ScriptTone } from '@/lib/ai/prompt';

// Edge 런타임: 서버리스 콜드스타트/타임아웃을 피하고 SSE 스트리밍에 적합.
export const runtime = 'edge';

const CREDITS_PER_GENERATION = 1;

const requestSchema = z.object({
  productName: z.string().trim().min(1, '상품명을 입력해주세요.').max(200),
  sellingPoints: z.string().trim().min(1, '핵심 셀링포인트를 입력해주세요.').max(2000),
  tone: z.enum(['humor', 'review', 'urgent-sale']),
});

const openai = createOpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(req: Request) {
  // 1. 세션 검증
  const supabase = createClient();
  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (authError || !user) {
    return NextResponse.json({ error: '로그인이 필요합니다.' }, { status: 401 });
  }

  // 입력 검증
  const body = await req.json().catch(() => null);
  const parsed = requestSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.issues[0]?.message ?? '잘못된 요청입니다.' },
      { status: 400 }
    );
  }
  const { productName, sellingPoints, tone } = parsed.data;

  // 2. 크레딧 원자적 차감 (RPC)
  const { data: remainingCredits, error: rpcError } = await supabase.rpc(
    'deduct_user_credits',
    { p_user_id: user.id, p_amount: CREDITS_PER_GENERATION }
  );

  if (rpcError) {
    const insufficientCredits = rpcError.message?.includes('INSUFFICIENT_CREDITS');
    return NextResponse.json(
      {
        error: insufficientCredits
          ? '크레딧이 부족합니다. 플랜을 업그레이드해주세요.'
          : '크레딧 차감 중 오류가 발생했습니다.',
      },
      { status: insufficientCredits ? 402 : 500 }
    );
  }

  // 3. 프롬프트 구성
  const prompt = buildShortsScriptPrompt({
    productName,
    sellingPoints,
    tone: tone as ScriptTone,
  });

  // 4. 스트리밍 응답 (실패 시 생성 로그는 남기지 않고, 완료 시점에 기록)
  let fullText = '';

  const result = await streamText({
    model: openai('gpt-4o-mini'),
    system:
      '당신은 국내 이커머스 쇼핑 쇼츠 대본을 작성하는 전문 카피라이터입니다. 항상 한국어로 답합니다.',
    prompt,
    temperature: 0.8,
    onChunk({ chunk }) {
      if (chunk.type === 'text-delta') {
        fullText += chunk.textDelta;
      }
    },
    onFinish: async ({ text }) => {
      // 생성 이력 저장 (RLS: auth.uid() = user_id 이므로 본인 세션 컨텍스트로 insert)
      await supabase.from('generation_logs').insert({
        user_id: user.id,
        product_name: productName,
        selling_points: sellingPoints,
        tone,
        script_content: text ?? fullText,
      });
    },
  });

  const response = result.toTextStreamResponse();
  response.headers.set('X-Remaining-Credits', String(remainingCredits ?? 0));
  return response;
}
