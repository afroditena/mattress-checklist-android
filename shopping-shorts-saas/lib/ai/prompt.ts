export type ScriptTone = 'humor' | 'review' | 'urgent-sale';

export const TONE_LABELS: Record<ScriptTone, string> = {
  humor: '유머러스',
  review: '리뷰형(솔직 후기 톤)',
  'urgent-sale': '긴급 세일형(임박 마감 톤)',
};

interface BuildPromptInput {
  productName: string;
  sellingPoints: string;
  tone: ScriptTone;
}

/**
 * 30초 쇼핑 쇼츠 대본 생성용 프롬프트.
 * 후킹(0~3초) - 본문(3~23초) - CTA(23~30초) 구조와 씬별 연출 지문을 강제한다.
 */
export function buildShortsScriptPrompt({
  productName,
  sellingPoints,
  tone,
}: BuildPromptInput): string {
  const toneLabel = TONE_LABELS[tone] ?? tone;

  return `당신은 국내 이커머스(쿠팡 파트너스, 스마트스토어 등) 셀러를 위한
30초 쇼핑 쇼츠(숏폼) 대본 전문 카피라이터입니다.

# 상품 정보
- 상품명: ${productName}
- 핵심 셀링포인트: ${sellingPoints}
- 톤앤매너: ${toneLabel}

# 작성 규칙
1. 전체 분량은 30초 내레이션 기준(약 300~330자 내외의 한국어 대사)으로 작성한다.
2. 아래 3단 구조를 반드시 지키고, 각 구간의 시간(초)을 명시한다.
   - [후킹] 0~3초: 시청자의 스크롤을 멈추게 할 강력한 한 문장 (질문형, 반전, 충격적 사실 등)
   - [본문] 3~23초: 핵심 셀링포인트를 ${toneLabel} 톤으로 설득력 있게 전달. 2~3개의 씬(Scene)으로 나눈다.
   - [CTA] 23~30초: 구매 유도 문구 + 긴급성/혜택 강조 (예: "지금 링크 클릭하고 할인받으세요")
3. 각 씬마다 다음 형식으로 출력한다.
   - "대사": 실제 내레이션/자막 텍스트
   - "연출 지문": 카메라 앵글, 자막 효과, 배경음악(BGM) 분위기, 상품 노출 방식 등 촬영/편집 지시사항
4. 출력은 마크다운 형식으로, 아래 템플릿을 그대로 따른다.

## 쇼츠 대본: ${productName}

### [후킹] 0~3초
- 대사: ...
- 연출 지문: ...

### [본문] 3~23초
**씬 1 (3~10초)**
- 대사: ...
- 연출 지문: ...

**씬 2 (10~17초)**
- 대사: ...
- 연출 지문: ...

**씬 3 (17~23초)**
- 대사: ...
- 연출 지문: ...

### [CTA] 23~30초
- 대사: ...
- 연출 지문: ...

---
지금부터 위 형식에 맞춰 "${productName}" 상품의 쇼츠 대본을 작성하세요.
과장 광고, 허위·과대 표현(예: "100% 완치", "부작용 없음")은 사용하지 마세요.`;
}
