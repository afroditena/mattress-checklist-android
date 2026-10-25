(function () {
  'use strict';

  var STORAGE_KEY = 'mattress_inspections_v1';

  // 매트리스 점검 항목 (단일 소스: 여기서만 정의하고 화면/보고서는 이 배열을 참조한다)
  var CHECK_ITEMS = [
    { id: 'surface', label: '매트리스 외관에 오염이나 손상이 없습니까?' },
    { id: 'zipper', label: '커버 봉제 및 지퍼 상태가 양호합니까?' },
    { id: 'spring', label: '스프링/폼 눌림 자국이 없습니까?' },
    { id: 'label', label: '라벨(모델명·사이즈) 부착이 정확합니까?' },
    { id: 'odor', label: '특이한 냄새(이취)가 없습니까?' },
    { id: 'size', label: '사이즈가 주문 규격과 일치합니까?' },
    { id: 'package', label: '포장 상태가 양호합니까?' },
    { id: 'accessory', label: '부속품(다리·설명서 등)이 모두 포함되어 있습니까?' }
  ];

  // ---------- 날짜 유틸 ----------

  function pad(n) {
    return n < 10 ? '0' + n : '' + n;
  }

  function todayStr() {
    var d = new Date();
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  }

  function formatDateTime(d) {
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) +
      ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
  }

  // ---------- 로컬 저장소 (서버 전송 없음, 기기 내부에만 보관) ----------

  function loadInspections() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    } catch (e) {
      return [];
    }
  }

  function saveInspections(list) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  }

  // ---------- 점검 체크리스트 탭 ----------

  function renderChecklistItems() {
    var container = document.getElementById('checklistItems');
    container.innerHTML = '';

    CHECK_ITEMS.forEach(function (item, idx) {
      var row = document.createElement('div');
      row.className = 'check-item';

      var label = document.createElement('span');
      label.className = 'check-label';
      label.textContent = (idx + 1) + '. ' + item.label;

      var radioGroup = document.createElement('div');
      radioGroup.className = 'radio-group';

      ['yes', 'no'].forEach(function (val) {
        var lbl = document.createElement('label');
        var input = document.createElement('input');
        input.type = 'radio';
        input.name = 'chk_' + item.id;
        input.value = val;
        input.addEventListener('change', updateTally);
        lbl.appendChild(input);
        lbl.appendChild(document.createTextNode(val === 'yes' ? ' 예' : ' 아니오'));
        radioGroup.appendChild(lbl);
      });

      row.appendChild(label);
      row.appendChild(radioGroup);
      container.appendChild(row);
    });
  }

  function getFormAnswers() {
    return CHECK_ITEMS.map(function (item) {
      var checked = document.querySelector('input[name="chk_' + item.id + '"]:checked');
      return { id: item.id, label: item.label, value: checked ? checked.value : null };
    });
  }

  function updateTally() {
    var answers = getFormAnswers();
    var yes = answers.filter(function (a) { return a.value === 'yes'; }).length;
    var no = answers.filter(function (a) { return a.value === 'no'; }).length;
    var unanswered = answers.length - yes - no;
    document.getElementById('tally').textContent =
      '예: ' + yes + '건 · 아니오: ' + no + '건 · 미응답: ' + unanswered + '건';
  }

  function resetChecklistForm() {
    document.getElementById('customerName').value = '';
    document.getElementById('inspectorName').value = '';
    document.getElementById('inspectionDate').value = todayStr();
    document.getElementById('notes').value = '';
    var radios = document.querySelectorAll('#checklistItems input[type="radio"]');
    radios.forEach(function (el) { el.checked = false; });
    updateTally();
  }

  function saveInspection() {
    var customerName = document.getElementById('customerName').value.trim();
    var inspectorName = document.getElementById('inspectorName').value.trim();
    var inspectionDate = document.getElementById('inspectionDate').value;
    var notes = document.getElementById('notes').value.trim();
    var answers = getFormAnswers();

    if (!customerName || !inspectorName || !inspectionDate) {
      alert('고객명/현장명, 점검자, 점검일을 모두 입력해주세요.');
      return;
    }
    if (answers.some(function (a) { return a.value === null; })) {
      alert('모든 점검 항목에 예/아니오로 응답해주세요.');
      return;
    }

    var yesCount = answers.filter(function (a) { return a.value === 'yes'; }).length;
    var noCount = answers.filter(function (a) { return a.value === 'no'; }).length;

    var record = {
      id: Date.now(),
      customerName: customerName,
      inspectorName: inspectorName,
      inspectionDate: inspectionDate,
      notes: notes,
      answers: answers,
      yesCount: yesCount,
      noCount: noCount,
      savedAt: new Date().toISOString()
    };

    var list = loadInspections();
    list.push(record);
    saveInspections(list);

    alert('저장되었습니다. "일일 보고" 탭에서 확인할 수 있습니다.');
    resetChecklistForm();

    var reportDateInput = document.getElementById('reportDate');
    if (reportDateInput.value === inspectionDate) {
      renderReport(inspectionDate);
    }
  }

  function buildSingleChecklistText() {
    var customerName = document.getElementById('customerName').value.trim() || '(미입력)';
    var inspectorName = document.getElementById('inspectorName').value.trim() || '(미입력)';
    var inspectionDate = document.getElementById('inspectionDate').value || todayStr();
    var notes = document.getElementById('notes').value.trim();
    var answers = getFormAnswers();
    var yes = answers.filter(function (a) { return a.value === 'yes'; }).length;
    var no = answers.filter(function (a) { return a.value === 'no'; }).length;

    var lines = [];
    lines.push('매트리스 점검 결과');
    lines.push('점검일: ' + inspectionDate);
    lines.push('고객/현장명: ' + customerName);
    lines.push('점검자: ' + inspectorName);
    lines.push('----------------------------------------');
    answers.forEach(function (a, idx) {
      var mark = a.value === 'yes' ? '예' : (a.value === 'no' ? '아니오' : '미응답');
      lines.push((idx + 1) + '. ' + a.label + ' : ' + mark);
    });
    lines.push('----------------------------------------');
    lines.push('예: ' + yes + '건 · 아니오: ' + no + '건');
    if (notes) {
      lines.push('비고: ' + notes);
    }
    return lines.join('\n');
  }

  // ---------- 일일 보고 탭 (본부장 보고용) ----------

  function renderReport(date) {
    var all = loadInspections();
    var list = all
      .filter(function (r) { return r.inspectionDate === date; })
      .sort(function (a, b) { return a.savedAt.localeCompare(b.savedAt); });

    var total = list.length;
    var noIssueCount = list.filter(function (r) { return r.noCount === 0; }).length;
    var issueCount = total - noIssueCount;

    var itemNoCounts = CHECK_ITEMS.map(function (item) {
      return list.filter(function (r) {
        return r.answers.some(function (a) { return a.id === item.id && a.value === 'no'; });
      }).length;
    });

    renderSummaryCards(total, noIssueCount, issueCount);
    renderItemBreakdown(itemNoCounts);
    renderEntries(list);

    document.getElementById('reportText').value =
      buildDailyReportText(date, list, itemNoCounts, noIssueCount);
  }

  function renderSummaryCards(total, noIssueCount, issueCount) {
    var container = document.getElementById('reportSummary');
    container.innerHTML = '';
    var cards = [
      { value: total, label: '총 점검 건수' },
      { value: noIssueCount, label: '이상 없음' },
      { value: issueCount, label: '이상 발견' }
    ];
    cards.forEach(function (c) {
      var card = document.createElement('div');
      card.className = 'summary-card';
      card.innerHTML = '<div class="value">' + c.value + '건</div><div class="label">' + c.label + '</div>';
      container.appendChild(card);
    });
  }

  function renderItemBreakdown(itemNoCounts) {
    var container = document.getElementById('reportItemBreakdown');
    container.innerHTML = '';
    CHECK_ITEMS.forEach(function (item, idx) {
      var count = itemNoCounts[idx];
      var row = document.createElement('div');
      row.className = 'row';
      row.innerHTML =
        '<span>' + item.label + '</span>' +
        '<span class="count' + (count > 0 ? ' has-issue' : '') + '">' + count + '건</span>';
      container.appendChild(row);
    });
  }

  function renderEntries(list) {
    var container = document.getElementById('reportEntries');
    container.innerHTML = '';

    if (list.length === 0) {
      var empty = document.createElement('div');
      empty.className = 'empty-message';
      empty.textContent = '선택한 날짜에 저장된 점검 기록이 없습니다.';
      container.appendChild(empty);
      return;
    }

    list.forEach(function (r, idx) {
      var entry = document.createElement('div');
      entry.className = 'report-entry';

      var title = document.createElement('div');
      title.className = 'entry-title';
      title.textContent = (idx + 1) + '. ' + r.customerName + ' (점검자: ' + r.inspectorName + ')';
      entry.appendChild(title);

      var tally = document.createElement('div');
      tally.textContent = '예 ' + r.yesCount + '건 · 아니오 ' + r.noCount + '건' +
        (r.notes ? ' · 비고: ' + r.notes : '');
      entry.appendChild(tally);

      var noItems = r.answers.filter(function (a) { return a.value === 'no'; }).map(function (a) { return a.label; });
      if (noItems.length) {
        var issue = document.createElement('div');
        issue.className = 'entry-issue';
        issue.textContent = '이상 항목: ' + noItems.join(', ');
        entry.appendChild(issue);
      }

      container.appendChild(entry);
    });
  }

  function buildDailyReportText(date, list, itemNoCounts, noIssueCount) {
    var lines = [];
    lines.push('매트리스 점검 일일 보고');
    lines.push('보고일: ' + date);
    lines.push('작성 시각: ' + formatDateTime(new Date()));
    lines.push('----------------------------------------');
    lines.push('총 점검 건수: ' + list.length + '건');
    lines.push('이상 없음: ' + noIssueCount + '건');
    lines.push('이상 발견: ' + (list.length - noIssueCount) + '건');
    lines.push('');
    lines.push('[항목별 이상 발견 현황]');
    CHECK_ITEMS.forEach(function (item, idx) {
      lines.push('- ' + item.label + ' : ' + itemNoCounts[idx] + '건');
    });
    lines.push('');
    lines.push('[상세 내역]');
    if (list.length === 0) {
      lines.push('저장된 점검 기록이 없습니다.');
    } else {
      list.forEach(function (r, idx) {
        lines.push(
          (idx + 1) + '. 고객/현장명: ' + r.customerName +
          ' | 점검자: ' + r.inspectorName +
          ' | 예 ' + r.yesCount + '건 · 아니오 ' + r.noCount + '건' +
          (r.notes ? ' | 비고: ' + r.notes : '')
        );
        var noItems = r.answers.filter(function (a) { return a.value === 'no'; }).map(function (a) { return a.label; });
        if (noItems.length) {
          lines.push('   └ 이상 항목: ' + noItems.join(', '));
        }
      });
    }
    lines.push('----------------------------------------');
    lines.push('위와 같이 금일 매트리스 점검 결과를 본부장님께 보고드립니다.');
    return lines.join('\n');
  }

  function resetReportForDate(date) {
    if (!date) {
      return;
    }
    var ok = confirm(date + ' 날짜의 점검 기록을 모두 삭제할까요? 이 작업은 되돌릴 수 없습니다.');
    if (!ok) {
      return;
    }
    var all = loadInspections();
    var remaining = all.filter(function (r) { return r.inspectionDate !== date; });
    saveInspections(remaining);
    renderReport(date);
  }

  // ---------- 클립보드 / 인쇄 (AndroidBridge 우선, 없으면 브라우저 API로 대체) ----------

  function copyText(text) {
    if (window.AndroidBridge && typeof window.AndroidBridge.copyText === 'function') {
      window.AndroidBridge.copyText(text);
      return;
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        alert('복사되었습니다.');
      });
      return;
    }
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    try {
      document.execCommand('copy');
      alert('복사되었습니다.');
    } catch (e) {
      alert('복사에 실패했습니다.');
    }
    document.body.removeChild(ta);
  }

  function printCurrent(jobName) {
    if (window.AndroidBridge && typeof window.AndroidBridge.printPage === 'function') {
      window.AndroidBridge.printPage(jobName);
      return;
    }
    window.print();
  }

  // ---------- 탭 전환 ----------

  function switchTab(name) {
    document.querySelectorAll('.tab-btn').forEach(function (btn) {
      btn.classList.toggle('active', btn.getAttribute('data-tab') === name);
    });
    document.querySelectorAll('.tab-panel').forEach(function (panel) {
      panel.classList.toggle('active', panel.id === 'tab-' + name);
    });
    if (name === 'report') {
      var reportDateInput = document.getElementById('reportDate');
      if (!reportDateInput.value) {
        reportDateInput.value = todayStr();
      }
      renderReport(reportDateInput.value);
    }
  }

  // ---------- 초기화 ----------

  document.addEventListener('DOMContentLoaded', function () {
    renderChecklistItems();
    document.getElementById('inspectionDate').value = todayStr();
    updateTally();

    document.getElementById('checklistForm').addEventListener('submit', function (e) {
      e.preventDefault();
    });

    document.querySelectorAll('.tab-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        switchTab(btn.getAttribute('data-tab'));
      });
    });

    document.getElementById('saveBtn').addEventListener('click', saveInspection);
    document.getElementById('copyChecklistBtn').addEventListener('click', function () {
      copyText(buildSingleChecklistText());
    });
    document.getElementById('printChecklistBtn').addEventListener('click', function () {
      printCurrent('매트리스_점검_체크리스트');
    });
    document.getElementById('resetChecklistBtn').addEventListener('click', function () {
      if (confirm('작성 중인 내용을 초기화할까요?')) {
        resetChecklistForm();
      }
    });

    var reportDateInput = document.getElementById('reportDate');
    reportDateInput.addEventListener('change', function () {
      renderReport(reportDateInput.value);
    });

    document.getElementById('copyReportBtn').addEventListener('click', function () {
      copyText(document.getElementById('reportText').value);
    });
    document.getElementById('printReportBtn').addEventListener('click', function () {
      printCurrent('매트리스_점검_일일보고_' + (reportDateInput.value || todayStr()));
    });
    document.getElementById('resetReportBtn').addEventListener('click', function () {
      resetReportForDate(reportDateInput.value);
    });
  });
})();
