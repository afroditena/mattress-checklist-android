export type PlanId = 'starter' | 'pro';

export interface Plan {
  id: PlanId;
  name: string;
  price: number; // KRW
  credits: number;
  description: string;
}

export const PLANS: Record<PlanId, Plan> = {
  starter: {
    id: 'starter',
    name: '스타터',
    price: 29000,
    credits: 100,
    description: '월 100회 쇼츠 대본 생성',
  },
  pro: {
    id: 'pro',
    name: '프로',
    price: 69000,
    credits: 300,
    description: '월 300회 쇼츠 대본 생성',
  },
};

export function getPlan(planId: string): Plan | null {
  return (PLANS as Record<string, Plan>)[planId] ?? null;
}
