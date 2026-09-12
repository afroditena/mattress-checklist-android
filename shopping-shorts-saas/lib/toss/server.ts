const TOSS_API_BASE = 'https://api.tosspayments.com/v1';

function getAuthHeader(): string {
  const secretKey = process.env.TOSS_SECRET_KEY;
  if (!secretKey) {
    throw new Error('TOSS_SECRET_KEY 환경변수가 설정되지 않았습니다.');
  }
  return `Basic ${Buffer.from(`${secretKey}:`).toString('base64')}`;
}

interface IssueBillingKeyParams {
  authKey: string;
  customerKey: string;
}

export interface TossBillingKeyResponse {
  billingKey: string;
  customerKey: string;
  card?: {
    company: string;
    number: string;
  };
  [key: string]: unknown;
}

/**
 * 카드 등록(authKey) → 빌링키 발급.
 * https://docs.tosspayments.com/reference#authkey로-발급
 */
export async function issueBillingKey({
  authKey,
  customerKey,
}: IssueBillingKeyParams): Promise<TossBillingKeyResponse> {
  const res = await fetch(`${TOSS_API_BASE}/billing/authorizations/issue`, {
    method: 'POST',
    headers: {
      Authorization: getAuthHeader(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ authKey, customerKey }),
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(
      `빌링키 발급 실패: ${errorBody.message ?? res.statusText} (${res.status})`
    );
  }

  return res.json();
}

interface ChargeBillingParams {
  billingKey: string;
  customerKey: string;
  amount: number;
  orderId: string;
  orderName: string;
}

/**
 * 빌링키로 정기 결제 승인 요청 (월간 자동 결제).
 * https://docs.tosspayments.com/reference#자동결제-승인
 */
export async function chargeBillingKey({
  billingKey,
  customerKey,
  amount,
  orderId,
  orderName,
}: ChargeBillingParams) {
  const res = await fetch(`${TOSS_API_BASE}/billing/${billingKey}`, {
    method: 'POST',
    headers: {
      Authorization: getAuthHeader(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ customerKey, amount, orderId, orderName }),
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(`정기 결제 승인 실패: ${data.message ?? res.statusText} (${res.status})`);
  }

  return data;
}

/**
 * 토스 웹훅 서명 검증 (Webhook Secret Key 기반).
 * 토스는 헤더 `TossPayments-Webhook-Signature`로 HMAC-SHA256 서명을 전달한다.
 */
export async function verifyTossWebhookSignature(
  rawBody: string,
  signatureHeader: string | null
): Promise<boolean> {
  const secret = process.env.TOSS_WEBHOOK_SECRET;
  if (!secret || !signatureHeader) return false;

  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  const signatureBuffer = await crypto.subtle.sign('HMAC', key, encoder.encode(rawBody));
  const computed = Buffer.from(signatureBuffer).toString('base64');

  return computed === signatureHeader;
}
