const pptxgen = require("pptxgenjs");
const React = require("react");
const RDS = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

const NAVY = "1B2A41", NAVY2 = "24385A", GOLD = "C9A45C", ICE = "EEF2F7", WHITE = "FFFFFF",
  INK = "1F2937", MUTED = "6B7280", LINE = "D6DDE6";
const F = "Malgun Gothic";

async function icon(Comp, color, size = 256) {
  const svg = RDS.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
const shadow = () => ({ type: "outer", color: "000000", opacity: 0.12, blur: 8, offset: 2, angle: 90 });

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
  pres.title = "엘디스리젠트호텔 객실 매트리스 위생 케어 제안서";
  pres.company = "청호나이스 대구홈케어지사";

  const T = (s, text, o) => s.addText(text, Object.assign({ isTextBox: true, fontFace: F, color: INK, margin: 0, valign: "top" }, o));
  const title = (s, kicker, text) => {
    T(s, kicker, { x: 0.6, y: 0.45, w: 12, h: 0.35, fontSize: 13, bold: true, color: GOLD, charSpacing: 2 });
    T(s, text, { x: 0.6, y: 0.82, w: 12.1, h: 0.75, fontSize: 30, bold: true, color: NAVY });
  };
  const footer = (s, n, dark) => T(s, `청호나이스 대구홈케어지사  |  ${n} / 7`, { x: 0.6, y: 7.0, w: 12.1, h: 0.3, fontSize: 10, color: dark ? "9FB0C8" : MUTED, align: "right" });

  // ---------- 1. Cover ----------
  {
    const s = pres.addSlide(); s.background = { color: NAVY };
    s.addShape(pres.shapes.OVAL, { x: 8.4, y: 1.35, w: 4.4, h: 4.4, fill: { color: NAVY2 } });
    s.addImage({ data: await icon(fa.FaBed, GOLD), x: 9.55, y: 2.5, w: 2.1, h: 2.1 });
    T(s, "B2B PROPOSAL  ·  2026.10", { x: 0.8, y: 1.3, w: 7, h: 0.4, fontSize: 14, bold: true, color: GOLD, charSpacing: 3 });
    T(s, "엘디스리젠트호텔\n객실 매트리스 위생·케어 제안", { x: 0.8, y: 1.9, w: 7.8, h: 2.1, fontSize: 38, bold: true, color: WHITE, lineSpacingMultiple: 1.1 });
    T(s, "4성급 호텔의 '청결 평판'을 지키는 법인 전용 매트리스 + 정기 케어 솔루션", { x: 0.8, y: 4.2, w: 7.6, h: 0.8, fontSize: 17, color: "CADCFC" });
    T(s, "제안: 청호나이스 대구홈케어지사 (케어마스터)\n대상: 엘디스리젠트호텔 (대구 중구 동산동 360)", { x: 0.8, y: 5.6, w: 7.6, h: 0.8, fontSize: 13, color: "9FB0C8", lineSpacingMultiple: 1.3 });
    s.addNotes("인사 후 제안 목적 한 줄: 매트리스를 '사는 것'이 아니라 '관리되는 상태로 쓰는 것'을 제안드립니다.");
  }

  // ---------- 2. Hotel situation ----------
  {
    const s = pres.addSlide(); s.background = { color: WHITE };
    title(s, "01  호텔 현황", "숫자로 본 엘디스리젠트호텔");
    const stats = [
      ["4성급", "본관(유럽형 비즈니스)\n+ 신관(메디텔)"],
      ["약 110실", "공개 예약사이트 기준\n(정확한 객실 수는 실사 확인)"],
      ["6,825건", "아고다 이용후기 수\n평점 8.3 / 10"],
      ["4.5 / 5", "야놀자 평점\n(후기 752건)"],
    ];
    stats.forEach(([big, small], i) => {
      const x = 0.6 + i * 3.08;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.9, w: 2.85, h: 2.2, fill: { color: ICE }, rectRadius: 0.12 });
      T(s, big, { x: x + 0.25, y: 2.15, w: 2.4, h: 0.8, fontSize: 32, bold: true, color: NAVY });
      T(s, small, { x: x + 0.25, y: 3.05, w: 2.45, h: 0.9, fontSize: 12.5, color: MUTED, lineSpacingMultiple: 1.2 });
    });
    s.addImage({ data: await icon(fa.FaHospital, GOLD), x: 0.6, y: 4.55, w: 0.55, h: 0.55 });
    T(s, "동산의료원 인접 · 의료관광 메디텔 구조", { x: 1.35, y: 4.52, w: 11, h: 0.4, fontSize: 18, bold: true, color: NAVY });
    T(s, [
      { text: "환자 보호자·장기 투숙 고객 비중이 높은 입지 → 일반 관광호텔보다 침구 위생에 대한 기대치가 높습니다.", options: { bullet: true, breakLine: true } },
      { text: "후기가 많이 쌓이는 호텔인 만큼, '청결·침대' 한 줄 평가를 다음 예약 고객이 그대로 읽게 됩니다.", options: { bullet: true, breakLine: true } },
      { text: "한실(온돌) 스위트는 매트리스 대상에서 제외, 침대 객실 중심으로 검토합니다.", options: { bullet: true } },
    ], { x: 1.35, y: 5.0, w: 11.3, h: 1.6, fontSize: 14.5, paraSpaceAfter: 6 });
    T(s, "출처: 호텔 공식 홈페이지, 아고다·야놀자·구글 호텔 정보(2026.09 조회). 평점·후기 수는 조회 시점에 따라 변동.", { x: 0.6, y: 6.65, w: 9, h: 0.3, fontSize: 9.5, color: MUTED });
    footer(s, 2);
    s.addNotes("객실 수는 사이트마다 110~187실로 다르게 표기됨. 현장 실사 때 반드시 확인할 것.");
  }

  // ---------- 3. Problem ----------
  {
    const s = pres.addSlide(); s.background = { color: WHITE };
    title(s, "02  과제", "매트리스는 '보이지 않는 곳'에서 평판을 깎습니다");
    const items = [
      [fa.FaBug, "위생", "시트·커버는 투숙객마다 바뀌지만, 매트리스 내부의 땀·각질·먼지는 바뀌지 않고 쌓입니다."],
      [fa.FaCompressArrowsAlt, "꺼짐·변형", "다수가 번갈아 쓰는 객실 매트리스는 가장자리부터 꺼져 '침대가 불편하다' 후기로 이어집니다."],
      [fa.FaWonSign, "교체 비용", "전 객실 일괄 교체는 목돈이 들고, 교체 시점을 놓치면 품질 편차가 생깁니다."],
      [fa.FaFireExtinguisher, "안전", "여러 사람이 머무는 숙박시설일수록 침구 소재의 화재 안전성이 중요합니다."],
    ];
    for (let i = 0; i < items.length; i++) {
      const [Ic, h, d] = items[i];
      const col = i % 2, row = Math.floor(i / 2);
      const x = 0.6 + col * 6.15, y = 1.95 + row * 2.35;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 5.9, h: 2.1, fill: { color: WHITE }, line: { color: LINE, width: 1 }, rectRadius: 0.12, shadow: shadow() });
      s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: y + 0.35, w: 0.9, h: 0.9, fill: { color: NAVY } });
      s.addImage({ data: await icon(Ic, GOLD), x: x + 0.52, y: y + 0.57, w: 0.46, h: 0.46 });
      T(s, h, { x: x + 1.45, y: y + 0.32, w: 4.2, h: 0.45, fontSize: 19, bold: true, color: NAVY });
      T(s, d, { x: x + 1.45, y: y + 0.85, w: 4.2, h: 1.1, fontSize: 13.5, color: INK, lineSpacingMultiple: 1.2 });
    }
    footer(s, 3);
    s.addNotes("질문으로 시작: '현재 매트리스 교체 주기와 관리 방법이 어떻게 되시나요?' — 답변을 듣고 해당 카드를 강조.");
  }

  // ---------- 4. Solution ----------
  {
    const s = pres.addSlide(); s.background = { color: ICE };
    title(s, "03  솔루션", "청호나이스 법인 전용 '클린핏(CLEAN FIT)' + 정기 케어");
    // left: product card
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 1.9, w: 6.6, h: 4.75, fill: { color: WHITE }, rectRadius: 0.12, shadow: shadow() });
    T(s, "제품 · 클린핏 매트리스", { x: 0.95, y: 2.15, w: 6, h: 0.45, fontSize: 19, bold: true, color: NAVY });
    const feats = [
      [fa.FaFire, "난연 기능 강화 원단", "화재 위험에 대비한 다중이용시설용 설계"],
      [fa.FaShieldAlt, "항균·소취 스마트셀 소재", "오코텍스 스탠다드 100 인증 소재"],
      [fa.FaLayerGroup, "독립 포켓스프링 + 고탄성 하드폼", "여러 체형의 투숙객을 안정적으로 지지"],
      [fa.FaBorderStyle, "측면 보강 폼케이스", "가장자리 꺼짐을 줄여 모서리 내구성 강화"],
    ];
    for (let i = 0; i < feats.length; i++) {
      const [Ic, h, d] = feats[i]; const y = 2.8 + i * 0.93;
      s.addShape(pres.shapes.OVAL, { x: 0.95, y, w: 0.62, h: 0.62, fill: { color: NAVY } });
      s.addImage({ data: await icon(Ic, GOLD), x: 1.1, y: y + 0.15, w: 0.32, h: 0.32 });
      T(s, h, { x: 1.8, y: y - 0.02, w: 5.2, h: 0.35, fontSize: 15, bold: true, color: INK });
      T(s, d, { x: 1.8, y: y + 0.34, w: 5.2, h: 0.35, fontSize: 12.5, color: MUTED });
    }
    // right: care card
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.5, y: 1.9, w: 5.23, h: 4.75, fill: { color: NAVY }, rectRadius: 0.12, shadow: shadow() });
    s.addImage({ data: await icon(fa.FaUserShield, GOLD), x: 7.85, y: 2.2, w: 0.6, h: 0.6 });
    T(s, "서비스 · 케어마스터 정기 케어", { x: 7.85, y: 2.95, w: 4.7, h: 0.45, fontSize: 19, bold: true, color: WHITE });
    T(s, [
      { text: "교육 이수 케어마스터 직접 방문", options: { bullet: true, breakLine: true } },
      { text: "청호나이스 7단계 위생 케어 적용", options: { bullet: true, breakLine: true } },
      { text: "객실 점검 결과 담당자 공유", options: { bullet: true, breakLine: true } },
      { text: "공실 시간대 위주로 일정 협의", options: { bullet: true } },
    ], { x: 7.85, y: 3.55, w: 4.6, h: 2.3, fontSize: 14, color: "E5ECF6", paraSpaceAfter: 8 });
    T(s, "제품 사양 출처: 청호나이스 클린핏 출시 보도(한국경제·지디넷코리아, 2025.09.30)", { x: 7.85, y: 6.1, w: 4.7, h: 0.4, fontSize: 9.5, color: "9FB0C8" });
    footer(s, 4);
    s.addNotes("케어 주기·정기 보고 양식은 계약 조건에 따라 협의. 현장에서 약속하지 말고 견적서에 명시할 것.");
  }

  // ---------- 5. Options ----------
  {
    const s = pres.addSlide(); s.background = { color: WHITE };
    title(s, "04  도입 방식", "부담 없이 시작하는 3가지 선택지");
    const opts = [
      ["A", "케어 서비스만", "기존 매트리스 유지", ["초기 비용 최소", "현재 매트리스 상태 점검 겸용", "꺼진 매트리스는 해결 불가"], false],
      ["B", "파일럿 도입", "1개 층 또는 약 10실, 3개월", ["실제 투숙객 반응으로 검증", "하우스키핑 의견 수렴", "결과 보고 후 확대 여부 결정"], true],
      ["C", "전 객실 도입", "클린핏 렌탈 + 정기 케어", ["객실 품질 편차 해소", "구매 대신 월 렌탈로 비용 분산", "비수기 순차 교체로 영업 영향 최소"], false],
    ];
    opts.forEach(([tag, h, sub, pts, rec], i) => {
      const x = 0.6 + i * 4.13, w = 3.88;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.95, w, h: 4.1, fill: { color: rec ? NAVY : ICE }, rectRadius: 0.12, shadow: rec ? shadow() : undefined });
      const c1 = rec ? WHITE : NAVY, c2 = rec ? "CADCFC" : MUTED, c3 = rec ? "E5ECF6" : INK;
      s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: 2.25, w: 0.7, h: 0.7, fill: { color: GOLD } });
      T(s, tag, { x: x + 0.3, y: 2.25, w: 0.7, h: 0.7, fontSize: 22, bold: true, color: WHITE, align: "center", valign: "middle" });
      if (rec) {
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + w - 1.35, y: 2.38, w: 1.05, h: 0.42, fill: { color: GOLD }, rectRadius: 0.2 });
        T(s, "추천", { x: x + w - 1.35, y: 2.38, w: 1.05, h: 0.42, fontSize: 13, bold: true, color: WHITE, align: "center", valign: "middle" });
      }
      T(s, h, { x: x + 0.3, y: 3.2, w: w - 0.6, h: 0.5, fontSize: 21, bold: true, color: c1 });
      T(s, sub, { x: x + 0.3, y: 3.72, w: w - 0.6, h: 0.4, fontSize: 13, color: c2 });
      T(s, pts.map((p, j) => ({ text: p, options: { bullet: true, breakLine: j < pts.length - 1 } })),
        { x: x + 0.3, y: 4.35, w: w - 0.5, h: 1.9, fontSize: 14, color: c3, paraSpaceAfter: 8 });
    });
    T(s, "월 렌탈료·케어 주기는 실사 후 객실 수·매트리스 규격 기준으로 정식 견적서에 명시합니다.", { x: 0.6, y: 6.3, w: 11, h: 0.3, fontSize: 10.5, color: MUTED });
    footer(s, 5);
    s.addNotes("B(파일럿)로 문턱을 낮추고, 결과가 좋으면 C로 확대하는 흐름. A는 결정이 어려운 경우의 대안으로만 제시.");
  }

  // ---------- 6. Timeline & effect ----------
  {
    const s = pres.addSlide(); s.background = { color: WHITE };
    title(s, "05  실행 계획", "실사부터 확대 결정까지, 약 4개월");
    const steps = [
      ["1주차", "현장 실사", "객실 수·침대 규격·\n매트리스 상태 확인"],
      ["2주차", "견적·파일럿 계약", "대상 객실과\n케어 주기 확정"],
      ["3주차", "설치·첫 케어", "공실 시간대에\n순차 교체"],
      ["~3개월", "파일럿 운영", "후기·하우스키핑\n의견 기록"],
      ["평가", "결과 보고", "전 객실 확대\n여부 결정"],
    ];
    const y0 = 2.35, gap = 2.47;
    s.addShape(pres.shapes.LINE, { x: 1.2, y: y0 + 0.35, w: gap * 4, h: 0, line: { color: LINE, width: 2 } });
    steps.forEach(([when, h, d], i) => {
      const cx = 1.2 + i * gap;
      s.addShape(pres.shapes.OVAL, { x: cx - 0.35, y: y0, w: 0.7, h: 0.7, fill: { color: i === 4 ? GOLD : NAVY } });
      T(s, String(i + 1), { x: cx - 0.35, y: y0, w: 0.7, h: 0.7, fontSize: 18, bold: true, color: WHITE, align: "center", valign: "middle" });
      T(s, when, { x: cx - 1.1, y: y0 + 0.85, w: 2.2, h: 0.3, fontSize: 12, bold: true, color: GOLD, align: "center" });
      T(s, h, { x: cx - 1.1, y: y0 + 1.15, w: 2.2, h: 0.4, fontSize: 16, bold: true, color: NAVY, align: "center" });
      T(s, d, { x: cx - 1.1, y: y0 + 1.6, w: 2.2, h: 0.75, fontSize: 12.5, color: MUTED, align: "center", lineSpacingMultiple: 1.15 });
    });
    // effect band
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 4.85, w: 12.13, h: 1.75, fill: { color: ICE }, rectRadius: 0.12 });
    T(s, "파일럿에서 함께 확인할 지표", { x: 0.95, y: 5.05, w: 5, h: 0.4, fontSize: 16, bold: true, color: NAVY });
    const kpis = [["후기 키워드", "'청결·침대·잠' 언급 변화"], ["하우스키핑", "객실 정비 시 불편 사항"], ["컴플레인", "침구 관련 민원 건수"]];
    const kIcons = [fa.FaCommentDots, fa.FaBroom, fa.FaExclamationCircle];
    for (let i = 0; i < kpis.length; i++) {
      const [h, d] = kpis[i]; const x = 0.95 + i * 3.95;
      s.addImage({ data: await icon(kIcons[i], NAVY), x, y: 5.65, w: 0.45, h: 0.45 });
      T(s, h, { x: x + 0.65, y: 5.6, w: 3.0, h: 0.35, fontSize: 14.5, bold: true, color: INK });
      T(s, d, { x: x + 0.65, y: 5.98, w: 3.0, h: 0.35, fontSize: 12.5, color: MUTED });
    }
    footer(s, 6);
    s.addNotes("일정은 호텔 비수기·객실 점유율에 맞춰 조정 가능. 효과 수치는 약속하지 않고, 측정 방법만 합의.");
  }

  // ---------- 7. Closing ----------
  {
    const s = pres.addSlide(); s.background = { color: NAVY };
    T(s, "NEXT STEP", { x: 0.8, y: 0.9, w: 6, h: 0.4, fontSize: 14, bold: true, color: GOLD, charSpacing: 3 });
    T(s, "30분 현장 실사로 시작하겠습니다", { x: 0.8, y: 1.4, w: 11.5, h: 0.9, fontSize: 36, bold: true, color: WHITE });
    const asks = [
      [fa.FaCalendarCheck, "실사 일정", "호텔 편하신 날짜·시간\n공실 2~3개 확인"],
      [fa.FaClipboardList, "객실 정보", "객실 타입별 수량과\n침대·매트리스 규격"],
      [fa.FaUserTie, "담당자 지정", "시설/객실 관리 담당\n1분과 소통 창구 일원화"],
    ];
    for (let i = 0; i < asks.length; i++) {
      const [Ic, h, d] = asks[i]; const x = 0.8 + i * 4.0;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.75, w: 3.7, h: 2.5, fill: { color: NAVY2 }, rectRadius: 0.12 });
      s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: 3.05, w: 0.8, h: 0.8, fill: { color: GOLD } });
      s.addImage({ data: await icon(Ic, WHITE), x: x + 0.5, y: 3.25, w: 0.4, h: 0.4 });
      T(s, h, { x: x + 0.3, y: 4.05, w: 3.2, h: 0.4, fontSize: 18, bold: true, color: WHITE });
      T(s, d, { x: x + 0.3, y: 4.5, w: 3.2, h: 0.7, fontSize: 13, color: "CADCFC", lineSpacingMultiple: 1.15 });
    }
    T(s, "실사 후 1주 이내 객실별 정식 견적서와 파일럿 계획서를 전달드립니다.", { x: 0.8, y: 5.6, w: 11.5, h: 0.4, fontSize: 15, color: WHITE });
    T(s, "청호나이스 대구홈케어지사 · 케어마스터", { x: 0.8, y: 6.3, w: 11.5, h: 0.4, fontSize: 13, color: "9FB0C8" });
    footer(s, 7, true);
    s.addNotes("마무리: 실사 날짜를 그 자리에서 잡는 것이 목표. 즉시 결정이 어려우면 소개 가능한 인근 숙박업체 문의로 연결.");
  }

  await pres.writeFile({ fileName: "EldisRegent_Proposal.pptx" });
  console.log("done");
})();
