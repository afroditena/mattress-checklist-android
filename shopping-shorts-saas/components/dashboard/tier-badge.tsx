import type { Tier } from '@/types/database';

const TIER_STYLES: Record<Tier, string> = {
  free: 'bg-gray-100 text-gray-700',
  starter: 'bg-blue-100 text-blue-700',
  pro: 'bg-violet-100 text-violet-700',
};

const TIER_LABELS: Record<Tier, string> = {
  free: 'FREE',
  starter: 'STARTER',
  pro: 'PRO',
};

export function TierBadge({ tier }: { tier: Tier }) {
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${TIER_STYLES[tier]}`}
    >
      {TIER_LABELS[tier]}
    </span>
  );
}
