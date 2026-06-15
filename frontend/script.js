/* ================================================================
   AI CODE REVIEW TUTOR — Frontend Logic
   ----------------------------------------------------------------
   Fitur:
   - Analisis kode via /api/analyze (rule engine + LLM fallback)
   - Riwayat percakapan/analisis TERSIMPAN di localStorage
     -> bertahan walau browser/komputer dimatikan & dinyalakan lagi
   - Sidebar berfungsi penuh: Analisis baru, Contoh kode, Rules KB,
     daftar Riwayat (buka kembali / hapus)
   - Contoh kode bisa langsung dipakai dari layar manapun
   ================================================================ */

/* ================================================================
   STATE
   ================================================================ */
const LS_SESSIONS = 'crt_sessions_v1';   // daftar sesi analisis
const LS_ACTIVE   = 'crt_active_v1';     // id sesi yang sedang dibuka
const LS_THEME    = 'crt_theme_v1';      // 'light' | 'dark'
const LS_SIDEBAR  = 'crt_sidebar_v1';    // 'open' | 'closed'

let sessions = [];      // [{ id, title, createdAt, updatedAt, rounds:[{code, violations, summary}] }]
let activeId = null;    // id sesi aktif
let analysisRound = 0;  // penghitung bubble di tampilan saat ini
let allViolations = {}; // round -> violations[] (dipakai tombol Salin)

/* ================================================================
   PERSISTENCE (localStorage)
   ================================================================ */
function loadState() {
  try {
    sessions = JSON.parse(localStorage.getItem(LS_SESSIONS)) || [];
  } catch {
    sessions = [];
  }
  if (!Array.isArray(sessions)) sessions = [];
  activeId = localStorage.getItem(LS_ACTIVE) || null;
}

function persist() {
  try {
    localStorage.setItem(LS_SESSIONS, JSON.stringify(sessions));
    if (activeId) localStorage.setItem(LS_ACTIVE, activeId);
    else localStorage.removeItem(LS_ACTIVE);
  } catch (e) {
    console.warn('Gagal menyimpan riwayat ke localStorage:', e);
  }
}

function getActive() {
  return sessions.find(s => s.id === activeId) || null;
}

function uid() {
  return 'c' + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

/* Judul pintar: lewati komentar & baris separator, ambil baris kode bermakna.
   Prioritas: nama fungsi/class -> baris kode pertama -> komentar pertama. */
function titleFromCode(code) {
  const rawLines = code.split('\n').map(l => l.trim());
  const lines = rawLines.filter(Boolean);
  if (!lines.length) return 'Analisis';

  const isSeparator = l => /^[#=\-_*~/]{3,}$/.test(l.replace(/\s/g, ''));
  const isComment   = l => l.startsWith('#');

  // 1) Definisi fungsi/class paling informatif
  const def = lines.find(l => /^(def|class|async\s+def)\s+/.test(l));
  if (def) {
    const m = def.match(/^(?:async\s+def|def|class)\s+([A-Za-z_]\w*)/);
    if (m) return m[1].slice(0, 48);
  }

  // 2) Baris kode pertama yang bukan komentar/separator
  const codeLine = lines.find(l => !isComment(l) && !isSeparator(l));
  if (codeLine) return codeLine.slice(0, 48);

  // 3) Komentar pertama yang bukan sekadar separator
  const comment = lines.find(l => isComment(l) && !isSeparator(l));
  if (comment) return comment.replace(/^#+\s*/, '').trim().slice(0, 48) || 'Analisis';

  return 'Analisis';
}

function createSession(code) {
  const s = {
    id: uid(),
    title: titleFromCode(code),
    titleEdited: false,   // true bila judul diubah manual oleh pengguna
    createdAt: Date.now(),
    updatedAt: Date.now(),
    rounds: [],
  };
  sessions.push(s);
  activeId = s.id;
  persist();
  return s;
}

function saveRound(code, violations, summary, llmUsed) {
  const s = getActive();
  if (!s) return;
  s.rounds.push({
    code,
    violations: violations || [],
    summary: summary || null,
    llmUsed: llmUsed === undefined ? true : llmUsed,
  });
  s.updatedAt = Date.now();
  // Jangan timpa judul yang sudah diedit manual
  if (s.rounds.length === 1 && !s.titleEdited) s.title = titleFromCode(code);
  persist();
  renderHistory();
}

/* ================================================================
   HELPERS
   ================================================================ */
function esc(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function $(id) { return document.getElementById(id); }

/* Input mana yang sedang aktif: editor welcome atau bottom-bar */
function targetInput() {
  const analysis = $('analysisView');
  if (analysis && analysis.classList.contains('show')) return $('miniInput');
  return $('mainEditor');
}

function fillInput(code) {
  const el = targetInput();
  if (!el) return;
  el.value = code;
  el.focus();
  if (el.id === 'miniInput') {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  }
}

/* ================================================================
   VIEW SWITCHING
   ================================================================ */
function showWelcome() {
  $('analysisView').classList.remove('show');
  $('welcomeScreen').style.display = '';   // kembalikan ke flex (dari CSS .welcome)
  $('chatWrap').innerHTML = '';
  $('bottomBar').classList.remove('show');
  analysisRound = 0;
  allViolations = {};
}

function showAnalysisView() {
  $('welcomeScreen').style.display = 'none';
  $('analysisView').classList.add('show');
}

/* ================================================================
   SIDEBAR — Riwayat
   ================================================================ */
function renderHistory() {
  const el = $('histList');
  if (!el) return;

  if (!sessions.length) {
    el.innerHTML = '<div class="hist-empty">Belum ada riwayat analisis.</div>';
    return;
  }

  const sorted = [...sessions].sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));
  el.innerHTML = sorted.map(s => {
    const count = (s.rounds || []).length;
    const active = s.id === activeId ? ' active' : '';
    return `
<div class="hist-row${active}" role="listitem" onclick="openSession('${s.id}')" title="${esc(s.title)}">
  <span class="hist-title">${esc(s.title)}</span>
  ${count ? `<span class="hist-count">${count}</span>` : ''}
  <span class="hist-actions">
    <button type="button" class="hist-btn" title="Ubah nama" aria-label="Ubah nama riwayat"
      onclick="renameSession(event, '${s.id}')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
      </svg>
    </button>
    <button type="button" class="hist-btn hist-del" title="Hapus riwayat" aria-label="Hapus riwayat"
      onclick="deleteSession(event, '${s.id}')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/>
      </svg>
    </button>
  </span>
</div>`;
  }).join('');

  // Tandai "Analisis baru" aktif hanya saat tidak ada sesi terbuka
  const navNew = $('navNew');
  if (navNew) navNew.classList.toggle('active', !activeId);
}

/* Ubah nama riwayat secara inline */
function renameSession(e, id) {
  if (e) e.stopPropagation();
  const s = sessions.find(x => x.id === id);
  if (!s) return;
  const next = window.prompt('Ubah nama riwayat:', s.title);
  if (next === null) return;            // dibatalkan
  const clean = next.trim();
  if (!clean) return;                   // kosong -> abaikan
  s.title = clean.slice(0, 60);
  s.titleEdited = true;
  persist();
  renderHistory();
}

function openSession(id) {
  const s = sessions.find(x => x.id === id);
  if (!s) return;
  activeId = id;
  persist();
  restoreSession(s);
  renderHistory();
}

function deleteSession(e, id) {
  if (e) e.stopPropagation();
  sessions = sessions.filter(s => s.id !== id);
  if (activeId === id) {
    activeId = null;
    showWelcome();
  }
  persist();
  renderHistory();
}

function newAnalysisSession() {
  // Sesi lama sudah tersimpan otomatis — cukup buka layar kosong.
  activeId = null;
  persist();
  showWelcome();
  renderHistory();
  const ed = $('mainEditor');
  if (ed) { ed.value = ''; ed.focus(); }
}

/* Kerangka (skeleton) yang berkedip selagi isi riwayat dirender */
function skeletonHtml(count) {
  const blocks = Array.from({ length: Math.min(count || 1, 3) }).map(() => `
<div class="sk-round">
  <div class="sk-line sk-avatar"></div>
  <div class="sk-code"></div>
  <div class="sk-line sk-w70"></div>
  <div class="sk-line sk-w90"></div>
  <div class="sk-line sk-w50"></div>
</div>`).join('');
  return `<div class="chat-skeleton" aria-label="Memuat riwayat">${blocks}</div>`;
}

/* Bangun ulang seluruh sesi ke tampilan (dipakai saat buka riwayat / setelah restart) */
function restoreSession(s) {
  analysisRound = 0;
  allViolations = {};
  showAnalysisView();
  $('bottomBar').classList.add('show');

  const wrap = $('chatWrap');
  const rounds = s.rounds || [];

  // Tampilkan skeleton dulu supaya layar tidak kosong/putih saat memuat isi besar
  wrap.innerHTML = skeletonHtml(rounds.length);

  // Render isi sesungguhnya pada frame berikutnya (UI sempat menggambar skeleton)
  requestAnimationFrame(() => {
    wrap.innerHTML = '';
    analysisRound = 0;
    rounds.forEach(r => renderRound(r.code, r.violations || [], r.llmUsed));
    const scroll = $('chatScroll');
    if (scroll) scroll.scrollTop = scroll.scrollHeight;
  });
}

/* Render satu round LANGSUNG dari data tersimpan (tanpa fetch) */
function renderRound(code, violations, llmUsed) {
  analysisRound++;
  const round = analysisRound;
  allViolations[round] = violations;

  const wrap = $('chatWrap');
  wrap.insertAdjacentHTML('beforeend',
    buildUserBubble(code, round) + buildThinkingBubble(round));

  const cv = $(`codeViewer-${round}`);
  if (cv) cv.innerHTML = buildCodeLines(code, violations);

  const aiBody = $(`aiBubbleBody-${round}`);
  if (aiBody) aiBody.innerHTML = buildAiResponse(violations, round, llmUsed);
}

/* ================================================================
   CONTOH KODE
   ================================================================ */
async function loadSample(key) {
  try {
    const res = await fetch(`/api/samples/${key}`);
    if (!res.ok) throw new Error('Gagal memuat contoh');
    const data = await res.json();
    useSample(data.code);
  } catch (e) {
    console.error('loadSample error:', e);
  }
}

/* Sample bisa langsung dipakai: isi input + jalankan analisis */
function useSample(code) {
  fillInput(code);
  const analysis = $('analysisView');
  if (analysis && analysis.classList.contains('show')) {
    continueAnalysis();
  } else {
    startAnalysis();
  }
}

/* ================================================================
   MODAL — Pilih file sample
   ================================================================ */
async function openSampleModal() {
  const modal = $('sampleModal');
  const list  = $('sampleFileList');
  modal.classList.add('show');
  list.innerHTML = '<div class="modal-loading">Memuat daftar file...</div>';

  try {
    const res = await fetch('/api/files');
    if (!res.ok) throw new Error('Gagal memuat daftar file');
    const data = await res.json();
    list.innerHTML = data.files.map(f => `
      <button type="button" class="modal-file-row" onclick="loadSampleFile('${f}')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          stroke-linecap="round" stroke-linejoin="round" class="modal-file-icon" aria-hidden="true">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        ${esc(f)}
      </button>`).join('');
  } catch (e) {
    list.innerHTML = `<div class="modal-loading" style="color:var(--red)">Gagal memuat: ${esc(e.message)}</div>`;
  }
}

async function loadSampleFile(filename) {
  $('sampleModal').classList.remove('show');
  try {
    const res = await fetch(`/api/files/${encodeURIComponent(filename)}`);
    if (!res.ok) throw new Error('Gagal memuat file');
    const data = await res.json();
    useSample(data.code);
  } catch (e) {
    console.error('loadSampleFile error:', e);
  }
}

function closeSampleModal(e) {
  if (e.target === $('sampleModal')) $('sampleModal').classList.remove('show');
}

/* ================================================================
   MODAL — Rules KB
   ================================================================ */
async function openRulesModal() {
  const modal = $('rulesModal');
  const list  = $('rulesList');
  modal.classList.add('show');
  list.innerHTML = '<div class="modal-loading">Memuat daftar rules...</div>';

  try {
    const res = await fetch('/api/rules');
    if (!res.ok) throw new Error('Gagal memuat rules');
    const data = await res.json();
    const rules = data.rules || [];
    list.innerHTML = rules.map(r => `
      <div class="rule-row">
        <span class="sev-dot sev-bg-${r.severity}" aria-hidden="true"></span>
        <div class="rule-info">
          <div class="rule-name">${esc(r.rule_name)}</div>
          <div class="rule-id">${esc(r.rule_id)}</div>
        </div>
        <span class="sev-inline sev-${r.severity}">${esc(r.severity)}</span>
      </div>`).join('');
  } catch (e) {
    list.innerHTML = `<div class="modal-loading" style="color:var(--red)">Gagal memuat: ${esc(e.message)}</div>`;
  }
}

function closeRulesModal(e) {
  if (e.target === $('rulesModal')) $('rulesModal').classList.remove('show');
}

function clearEditor() {
  const el = targetInput();
  if (el) {
    el.value = '';
    el.focus();
    if (el.id === 'miniInput') el.style.height = 'auto';
  }
}

/* ================================================================
   ANALYSIS FLOW
   ================================================================ */

// Analisis pertama — dari halaman welcome (membuat sesi baru)
async function startAnalysis() {
  const code = ($('mainEditor')?.value || '').trim();
  if (!code) return;

  createSession(code);

  analysisRound = 0;
  allViolations = {};
  $('chatWrap').innerHTML = '';
  showAnalysisView();
  renderHistory();

  await runAnalysis(code);
}

// Analisis lanjutan — dari bottom bar (append ke sesi yang sama)
async function continueAnalysis() {
  const inp  = $('miniInput');
  const code = (inp?.value || '').trim();
  if (!code) return;
  inp.value = '';
  inp.style.height = 'auto';

  if (!getActive()) createSession(code);   // jaga-jaga bila sesi hilang

  await runAnalysis(code);
}

// Inti analisis — dipakai oleh startAnalysis & continueAnalysis
async function runAnalysis(code) {
  analysisRound++;
  const round = analysisRound;

  $('bottomBar').classList.remove('show');

  const wrap = $('chatWrap');
  wrap.insertAdjacentHTML('beforeend',
    buildUserBubble(code, round) + buildThinkingBubble(round)
  );

  const newBubble = $(`userBubble-${round}`);
  if (newBubble) newBubble.scrollIntoView({ behavior: 'smooth', block: 'start' });

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Server error' }));
      throw new Error(err.detail || 'Gagal menganalisis kode');
    }

    const data = await res.json();
    finishAnalysis(data, round, code);
    saveRound(code, data.violations || [], data.summary || null, data.llm_used);   // <- simpan riwayat
  } catch (e) {
    showAnalysisError(e.message, round);
  }
}

function finishAnalysis(data, round, code) {
  const violations = data.violations || [];
  allViolations[round] = violations;

  const codeViewer = $(`codeViewer-${round}`);
  if (codeViewer) codeViewer.innerHTML = buildCodeLines(code, violations);

  const aiBody = $(`aiBubbleBody-${round}`);
  if (aiBody) aiBody.innerHTML = buildAiResponse(violations, round, data.llm_used);

  $('bottomBar').classList.add('show');
}

function showAnalysisError(message, round) {
  const aiBody = $(`aiBubbleBody-${round}`);
  if (aiBody) {
    aiBody.innerHTML = `<p style="color:var(--red);font-size:14px;">&#9888; ${esc(message)}</p>`;
  }
  $('bottomBar').classList.add('show');
}

/* ================================================================
   USER BUBBLE
   ================================================================ */
function buildUserBubble(code, round) {
  return `
<div class="user-message" id="userBubble-${round}">
  <div class="msg-header">
    <div class="user-avatar" aria-hidden="true">R</div>
    <span class="msg-sender">Kamu</span>
  </div>
  <div class="user-msg-body">
    <div class="code-viewer" id="codeViewer-${round}">
      ${buildCodeLines(code, [])}
    </div>
  </div>
</div>`;
}

/* Render code lines with optional severity strips */
function buildCodeLines(code, violations) {
  const SEV_PRIORITY = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 };

  const lineMap = {};
  violations.forEach(v => {
    const existing = lineMap[v.line_no];
    if (!existing || SEV_PRIORITY[v.severity] > SEV_PRIORITY[existing]) {
      lineMap[v.line_no] = v.severity;
    }
  });

  const lines = code.split('\n');
  if (lines.length && lines[lines.length - 1] === '') lines.pop();

  return lines.map((line, idx) => {
    const lineNo    = idx + 1;
    const sev       = lineMap[lineNo];
    const lineClass = sev ? 'cv-line has-issue' : 'cv-line';
    const stripClass = sev ? `cv-strip-${sev}` : '';
    return `<div class="${lineClass}">
      <span class="cv-ln">${lineNo}</span>
      <span class="cv-strip ${stripClass}"></span>
      <span class="cv-text">${esc(line) || ' '}</span>
    </div>`;
  }).join('');
}

/* ================================================================
   AI THINKING BUBBLE
   ================================================================ */
function buildThinkingBubble(round) {
  return `
<div class="ai-message">
  <div class="msg-header">
    <div class="ai-gem" aria-hidden="true">
      <svg viewBox="0 0 20 20"><polygon points="10,2 18,7 18,13 10,18 2,13 2,7" fill="white"/></svg>
    </div>
    <span class="msg-sender">Code Review Tutor</span>
  </div>
  <div class="ai-msg-body" id="aiBubbleBody-${round}">
    <div class="thinking-dots" aria-label="Sedang menganalisis">
      <div class="td"></div>
      <div class="td"></div>
      <div class="td"></div>
    </div>
  </div>
</div>`;
}

/* ================================================================
   AI RESPONSE CONTENT
   ================================================================ */
function buildAiResponse(violations, round, llmUsed) {
  const total     = violations.length;

  if (total === 0) {
    return `<p class="msg-intro">&#10003; Mantap! Saya tidak menemukan antipattern pada kode ini. Kode kamu sudah cukup rapi.</p>`;
  }

  const critCount = violations.filter(v => v.severity === 'CRITICAL').length;

  let intro = `Saya menemukan <strong>${total} masalah</strong> pada kode kamu`;
  if (critCount > 0) {
    intro += `, termasuk <strong>${critCount} masalah kritis</strong> yang perlu segera diperbaiki`;
  }
  intro += '.';

  // Penanda: tampil hanya bila LLM TIDAK terhubung (jawaban umum & universal)
  const note = (llmUsed === false)
    ? `<div class="offline-note">&#8505; LLM tidak terhubung — berikut penjelasan <strong>umum &amp; universal</strong> untuk setiap masalah beserta contoh perbaikan.</div>`
    : '';

  const filterBar = buildFilterBar(violations, round);
  const items = violations.map((v, i) => violationHtml(v, round, i)).join('');

  return `${note}<p class="msg-intro">${intro}</p>${filterBar}<div class="vi-list" id="viList-${round}">${items}</div>`;
}

/* Bar filter severity per jawaban — agar user bisa fokus (mis. CRITICAL saja)
   tanpa scroll jauh. Chip hanya muncul untuk severity yang memang ada. */
function buildFilterBar(violations, round) {
  const ORDER = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
  const counts = {};
  violations.forEach(v => { counts[v.severity] = (counts[v.severity] || 0) + 1; });

  const total = violations.length;
  if (total <= 1) return '';   // tak perlu filter untuk 1 masalah

  const chips = [`
    <button type="button" class="flt-chip active" data-round="${round}" data-sev="ALL"
      onclick="filterRound(${round}, 'ALL', this)">Semua <span class="flt-num">${total}</span></button>`];

  ORDER.forEach(sev => {
    if (!counts[sev]) return;
    chips.push(`
    <button type="button" class="flt-chip flt-${sev}" data-round="${round}" data-sev="${sev}"
      onclick="filterRound(${round}, '${sev}', this)">${sev} <span class="flt-num">${counts[sev]}</span></button>`);
  });

  return `<div class="flt-bar" id="fltBar-${round}" role="group" aria-label="Filter berdasarkan tingkat keparahan">${chips.join('')}</div>`;
}

/* Terapkan filter: sembunyikan kartu yang tidak cocok via class pada kontainer */
function filterRound(round, sev, btn) {
  const list = $(`viList-${round}`);
  if (!list) return;

  // Bersihkan kelas filter sebelumnya lalu set yang baru
  list.className = 'vi-list' + (sev === 'ALL' ? '' : ` flt-only-${sev}`);

  // Status aktif pada chip
  const bar = $(`fltBar-${round}`);
  if (bar) {
    bar.querySelectorAll('.flt-chip').forEach(c => c.classList.remove('active'));
  }
  if (btn) btn.classList.add('active');
}

function violationHtml(v, round, i) {
  const explainSection = `<p class="vi-explain">${v.explanation}</p>`;

  // Kode bermasalah (snippet asli dari kode user) — tampil langsung di kartu
  // agar tidak perlu scroll ke atas untuk melihat baris yang dimaksud.
  const badSection = v.snippet ? `
  <div class="vi-block vi-block-bad">
    <div class="vi-block-head">
      <span class="vi-block-label"><span class="vi-x">&#10007;</span> Kode kamu — Baris ${v.line_no}</span>
    </div>
    <pre class="vi-pre vi-pre-bad">${esc(v.snippet)}</pre>
  </div>` : '';

  // Perbaikan (bertumpuk di bawah kode bermasalah)
  const fixSection = v.fixed_code ? `
  <div class="vi-block vi-block-fix">
    <div class="vi-block-head">
      <span class="vi-block-label"><span class="vi-check">&#10003;</span> Perbaikan</span>
      <button type="button" class="copy-btn" onclick="copyCode(${round},${i})" aria-label="Salin kode perbaikan"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Salin</button>
    </div>
    <pre class="vi-pre vi-pre-fix">${esc(v.fixed_code)}</pre>
  </div>` : '';

  // Badge sumber penjelasan: dari LLM ("AI") atau jawaban umum ("Umum")
  const badge = v.source === 'ai'
    ? `<span class="src-badge src-ai" title="Penjelasan dari LLM">AI</span>`
    : `<span class="src-badge src-fallback" title="Penjelasan umum (tanpa LLM)">Umum</span>`;

  return `
<div class="vi-item" data-sev="${v.severity}" style="animation-delay:${i * 90}ms">
  <p class="vi-header-line"><span class="sev-inline sev-${v.severity}">[${v.severity}]</span> <strong class="vi-title">${esc(v.rule_name)}</strong> ${badge} <span class="vi-meta">— Baris ${v.line_no} · ${v.rule_id}</span></p>
  ${explainSection}
  ${badSection}
  ${fixSection}
</div>`;
}

/* ================================================================
   COPY
   ================================================================ */
function copyCode(round, i) {
  navigator.clipboard.writeText(allViolations[round]?.[i]?.fixed_code || '').catch(() => {});
}

/* ================================================================
   THEME (gelap / terang) — tersimpan di localStorage
   ================================================================ */
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const btn = $('themeToggle');
  if (btn) btn.title = theme === 'dark' ? 'Mode terang' : 'Mode gelap';
}

function loadTheme() {
  const saved = localStorage.getItem(LS_THEME) || 'light';
  applyTheme(saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  const next = current === 'dark' ? 'light' : 'dark';
  applyTheme(next);
  try { localStorage.setItem(LS_THEME, next); } catch {}
}

/* ================================================================
   SIDEBAR — buka / tutup (tersimpan)
   ================================================================ */
function applySidebar(state) {
  // state: 'open' | 'closed'
  document.body.classList.toggle('sidebar-collapsed', state === 'closed');
}

function loadSidebar() {
  // Di layar sempit default tertutup; selain itu ikuti preferensi tersimpan
  const saved = localStorage.getItem(LS_SIDEBAR);
  if (saved) {
    applySidebar(saved);
  } else {
    applySidebar(window.innerWidth < 880 ? 'closed' : 'open');
  }
}

function toggleSidebar() {
  const collapsed = document.body.classList.contains('sidebar-collapsed');
  const next = collapsed ? 'open' : 'closed';
  applySidebar(next);
  try { localStorage.setItem(LS_SIDEBAR, next); } catch {}
}

function closeSidebar() {
  applySidebar('closed');
  try { localStorage.setItem(LS_SIDEBAR, 'closed'); } catch {}
}

/* ================================================================
   INIT — event listeners & restore state
   ================================================================ */
function initEditorKeys() {
  const mainEditor = $('mainEditor');
  mainEditor?.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      startAnalysis();
    }
    if (e.key === 'Tab') {
      e.preventDefault();
      const el = e.target;
      const s  = el.selectionStart;
      el.value = el.value.substring(0, s) + '    ' + el.value.substring(el.selectionEnd);
      el.selectionStart = el.selectionEnd = s + 4;
    }
  });

  const miniInput = $('miniInput');
  miniInput?.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      continueAnalysis();
    }
  });
  miniInput?.addEventListener('input', () => {
    miniInput.style.height = 'auto';
    miniInput.style.height = Math.min(miniInput.scrollHeight, 200) + 'px';
  });

  // Tutup modal dengan tombol Escape
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      $('sampleModal')?.classList.remove('show');
      $('rulesModal')?.classList.remove('show');
    }
  });
}

function init() {
  loadState();
  loadTheme();
  loadSidebar();
  initEditorKeys();
  renderHistory();

  // Lanjutkan sesi terakhir setelah restart bila ada isinya
  const active = getActive();
  if (active && (active.rounds || []).length) {
    restoreSession(active);
  } else {
    activeId = null;
    persist();
    showWelcome();
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
