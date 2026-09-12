'use client';

import { useState, useRef } from 'react';
import { Copy, Check, Loader2, Sparkles } from 'lucide-react';

type Tone = 'humor' | 'review' | 'urgent-sale';

const TONE_OPTIONS: { value: Tone; label: string }[] = [
  { value: 'humor', label: '유머러스' },
  { value: 'review', label: '리뷰형' },
  { value: 'urgent-sale', label: '긴급 세일형' },
];

interface GeneratorProps {
  initialCredits: number;
}

export function Generator({ initialCredits }: GeneratorProps) {
  const [productName, setProductName] = useState('');
  const [sellingPoints, setSellingPoints] = useState('');
  const [tone, setTone] = useState<Tone>('humor');
  const [script, setScript] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [credits, setCredits] = useState(initialCredits);
  const abortRef = useRef<AbortController | null>(null);

  const canSubmit = productName.trim() && sellingPoints.trim() && !isGenerating;

  const handleGenerate = async () => {
    setError(null);
    setScript('');
    setIsGenerating(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ productName, sellingPoints, tone }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error ?? '대본 생성에 실패했습니다.');
      }

      const remaining = res.headers.get('X-Remaining-Credits');
      if (remaining !== null) setCredits(Number(remaining));

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let acc = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        acc += decoder.decode(value, { stream: true });
        setScript(acc);
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(script);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* 입력 폼 */}
      <div className="space-y-4 rounded-lg border border-border bg-card p-6">
        <div>
          <label className="mb-1.5 block text-sm font-medium">상품명</label>
          <input
            value={productName}
            onChange={(e) => setProductName(e.target.value)}
            placeholder="예: 초극세사 극세모 물걸레 청소포"
            className="w-full rounded-md border border-border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium">핵심 셀링포인트</label>
          <textarea
            value={sellingPoints}
            onChange={(e) => setSellingPoints(e.target.value)}
            placeholder="예: 물기 99% 제거, 세탁기 세탁 가능, 초극세사 원단, 1+1 프로모션"
            rows={5}
            className="w-full resize-none rounded-md border border-border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium">톤앤매너</label>
          <select
            value={tone}
            onChange={(e) => setTone(e.target.value as Tone)}
            className="w-full rounded-md border border-border bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
          >
            {TONE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          onClick={handleGenerate}
          disabled={!canSubmit || credits <= 0}
          className="flex w-full items-center justify-center gap-2 rounded-md bg-primary py-2.5 text-sm font-semibold text-primary-foreground transition disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isGenerating ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
          {credits <= 0 ? '크레딧이 부족합니다' : '쇼츠 대본 생성 (1 크레딧)'}
        </button>
      </div>

      {/* 스트리밍 뷰어 */}
      <div className="relative rounded-lg border border-border bg-card p-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-muted-foreground">생성된 대본</h2>
          {script && (
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 rounded-md border border-border px-2.5 py-1 text-xs font-medium hover:bg-muted"
            >
              {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              {copied ? '복사됨' : '복사'}
            </button>
          )}
        </div>
        <div className="prose prose-sm max-h-[600px] min-h-[300px] max-w-none overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed">
          {script || (
            <p className="text-sm text-muted-foreground">
              상품 정보를 입력하고 생성 버튼을 누르면 여기에 실시간으로 대본이 표시됩니다.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
