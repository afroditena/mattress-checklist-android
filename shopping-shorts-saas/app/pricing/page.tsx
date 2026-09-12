import { CheckoutButton } from '@/components/pricing/checkout-button';
import { PLANS } from '@/lib/toss/plans';
import { Check } from 'lucide-react';

const FREE_FEATURES = ['가입 시 크레딧 10회 무료 제공', '기본 톤 3종 지원'];
const STARTER_FEATURES = ['월 100회 쇼츠 대본 생성', '유머/리뷰/긴급세일 톤 지원', '이메일 지원'];
const PRO_FEATURES = ['월 300회 쇼츠 대본 생성', '전체 톤 + 우선 지원', '생성 이력 무제한 보관'];

function PlanCard({
  name,
  price,
  priceLabel,
  features,
  cta,
}: {
  name: string;
  price: string;
  priceLabel: string;
  features: string[];
  cta: React.ReactNode;
}) {
  return (
    <div className="flex flex-col rounded-xl border border-border bg-card p-6 shadow-sm">
      <h3 className="text-lg font-semibold">{name}</h3>
      <p className="mt-2 text-3xl font-bold">
        {price}
        <span className="text-base font-medium text-muted-foreground"> {priceLabel}</span>
      </p>
      <ul className="mt-6 flex-1 space-y-2.5">
        {features.map((f) => (
          <li key={f} className="flex items-start gap-2 text-sm">
            <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
            {f}
          </li>
        ))}
      </ul>
      <div className="mt-6">{cta}</div>
    </div>
  );
}

export default function PricingPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-16">
      <div className="mb-10 text-center">
        <h1 className="text-3xl font-bold">요금제</h1>
        <p className="mt-2 text-muted-foreground">
          쿠팡 파트너스, 스마트스토어 셀러를 위한 쇼핑 쇼츠 대본 생성 플랜
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <PlanCard
          name="무료 체험"
          price="0원"
          priceLabel="/ 월"
          features={FREE_FEATURES}
          cta={
            <a
              href="/dashboard"
              className="block w-full rounded-md border border-border py-2.5 text-center text-sm font-semibold"
            >
              무료로 시작하기
            </a>
          }
        />
        <PlanCard
          name={PLANS.starter.name}
          price={`${PLANS.starter.price.toLocaleString()}원`}
          priceLabel="/ 월"
          features={STARTER_FEATURES}
          cta={<CheckoutButton planId="starter" label="스타터 구독하기" />}
        />
        <PlanCard
          name={PLANS.pro.name}
          price={`${PLANS.pro.price.toLocaleString()}원`}
          priceLabel="/ 월"
          features={PRO_FEATURES}
          cta={<CheckoutButton planId="pro" label="프로 구독하기" />}
        />
      </div>
    </div>
  );
}
