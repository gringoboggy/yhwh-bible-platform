"""HTML for /wizard console — extracted from scripts/web.py
during the web.py split refactor (2026-05-07).

Re-imported by scripts/web.py for back-compat with existing
`from scripts.web import WIZARD_HTML` callers.

ψ.14 buyer-arc polish (2026-05-08): cross-link nav substituted from
`_design.HEADER_NAV_LINKS("/wizard")` at module load.
"""

from scripts.templates._design import (  # noqa: E402
    BUYER_ARC_POLISH_CSS,
    HEADER_NAV_LINKS,
    apply_design_system,
)

__all__ = ["WIZARD_HTML", "HEADER_NAV_LINKS", "BUYER_ARC_POLISH_CSS"]

WIZARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Bible Builder · YHWH Ya' Way</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
  .step-dot {
    display: inline-flex; align-items: center; justify-content: center;
    width: 2rem; height: 2rem; border-radius: 9999px;
    background: #e2e8f0; color: #64748b; font-weight: 600; font-size: 0.875rem;
    transition: all 0.25s ease;
  }
  .step-dot.active { background: #2563eb; color: white; transform: scale(1.1); }
  .step-dot.done { background: #10b981; color: white; }
  .step-line { flex: 1; height: 2px; background: #e2e8f0; transition: background 0.25s; }
  .step-line.done { background: #10b981; }
  .step-pane { display: none; animation: fade-in 0.3s ease; }
  .step-pane.active { display: block; }
  @keyframes fade-in {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .field-input {
    width: 100%; border: 1px solid #cbd5e1; border-radius: 4px;
    padding: 0.5rem 0.75rem; font-size: 0.95rem;
  }
  .field-input:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px #dbeafe; }
  .label-text { font-size: 0.75rem; font-weight: 600; color: #475569;
                text-transform: uppercase; letter-spacing: 0.03em;
                margin-bottom: 0.25rem; display: block; }
  /* ψ.11 — branding-step fieldset rhythm */
  .psi11-group { border: 1px solid #e2e8f0; border-radius: 0.5rem;
                 padding: 1rem 1.25rem 1.25rem; background: #fafbfc; }
  .psi11-legend { font-size: 0.7rem; font-weight: 700; color: #475569;
                  text-transform: uppercase; letter-spacing: 0.05em;
                  background: white; padding: 0 0.5rem;
                  border: 1px solid #e2e8f0; border-radius: 9999px;
                  display: inline-block; margin-left: -0.25rem;
                  margin-bottom: 0.25rem; }
  .pick-card {
    border: 2px solid #e2e8f0; border-radius: 0.5rem; padding: 1rem;
    cursor: pointer; transition: all 0.2s; background: white;
  }
  .pick-card:hover { border-color: #93c5fd; }
  .pick-card.picked { border-color: #2563eb; background: #eff6ff; }
  .theme-preview {
    border: 1px solid #cbd5e1; border-radius: 0.375rem; padding: 0.6rem;
    font-size: 0.875rem; background: white; min-height: 4em;
  }
  .pill {
    display: inline-flex; align-items: center; gap: 0.4em;
    padding: 0.2em 0.7em; border-radius: 9999px; font-size: 0.8em;
    background: #f1f5f9; border: 1px solid #cbd5e1;
  }
  .pill-x { cursor: pointer; opacity: 0.5; padding-left: 0.3em; }
  .pill-x:hover { opacity: 1; color: #dc2626; }
  .kind-row { padding: 0.5rem 0.75rem; border-radius: 0.375rem;
              transition: background 0.15s; cursor: pointer; user-select: none; }
  .kind-row:hover { background: #f1f5f9; }
  .build-progress {
    background: linear-gradient(90deg, #2563eb 0%, #3b82f6 50%, #2563eb 100%);
    background-size: 200% 100%; animation: shimmer 1.4s ease-in-out infinite;
  }
  @keyframes shimmer {
    0%, 100% { background-position: 200% 0; }
    50%      { background-position: -200% 0; }
  }
</style>
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="bg-slate-50 text-slate-800">

<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold tracking-tight">Bible Builder</h1>
    <p class="text-xs text-slate-500">click a few buttons → walk away with your Bible</p>
  </div>
  <div class="flex items-center gap-4 text-xs flex-wrap">
    <!-- HEADER_NAV_LINKS -->
    <span id="corpus-progress" class="ml-auto text-xs text-slate-500" title="corpus depth toward the 35,000-note Ethiopian Tewahedo target">·· loading ··</span>
  </div>
</header>
<script>
// Phase ψ.3 — corpus progress widget. Cheap fetch + DOM update;
// silently no-ops on failure so a stale browser tab never breaks
// because the API endpoint changed shape.
(function () {
  fetch('/api/corpus-progress').then(function (r) { return r.json(); })
    .then(function (d) {
      var el = document.getElementById('corpus-progress');
      if (!el) return;
      var cur = (d.current || 0).toLocaleString();
      var tgt = (d.target || 0).toLocaleString();
      var pct = (typeof d.percent === 'number') ? d.percent.toFixed(1) : '0.0';
      el.textContent = cur + ' / ' + tgt + ' · ' + pct + '%';
    })
    .catch(function () {});
})();
</script>


<main class="p-6 max-w-4xl mx-auto">

  <!-- Step indicator -->
  <div class="flex items-center mb-8 gap-2">
    <div id="dot-1" class="step-dot active">1</div><div id="line-1" class="step-line"></div>
    <div id="dot-2" class="step-dot">2</div><div id="line-2" class="step-line"></div>
    <div id="dot-3" class="step-dot">3</div><div id="line-3" class="step-line"></div>
    <div id="dot-4" class="step-dot">4</div><div id="line-4" class="step-line"></div>
    <div id="dot-5" class="step-dot">5</div><div id="line-5" class="step-line"></div>
    <div id="dot-6" class="step-dot">6</div><div id="line-6" class="step-line"></div>
    <div id="dot-7" class="step-dot">7</div>
  </div>

  <div id="loading" class="text-center text-slate-400 py-20">loading editions…</div>

  <div id="wizard-content" class="hidden bg-white rounded-lg shadow-sm border border-slate-200 p-6">

    <!-- ───────── Step 1: Start from ───────── -->
    <section id="step-1" class="step-pane active">
      <h2 class="text-2xl font-bold mb-1">1. Start from a profile</h2>
      <p class="text-slate-600 mb-5">Pick a Bible profile to start with. You can change anything in the next steps.</p>

      <!-- ψ.7-B — starter-pack template entry point -->
      <div class="mb-5 flex items-center gap-3 text-sm">
        <button id="from-template-btn" type="button"
                class="px-3 py-2 rounded border border-blue-300 bg-blue-50 text-blue-700 hover:bg-blue-100 font-medium">
          ✨ Start from template…
        </button>
        <span class="text-slate-500">or pick an existing edition profile below.</span>
      </div>

      <div id="start-cards" class="grid grid-cols-1 md:grid-cols-2 gap-3"></div>
      <div class="mt-6 flex justify-end">
        <button id="next-1" class="px-5 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white font-medium opacity-50" disabled>Next →</button>
      </div>
    </section>

    <!-- ψ.7-B — Template picker modal (hidden by default; opened
         by from-template-btn). Lists every edition_template, lets
         the user pick one + supply new_id + new_title, then calls
         POST /api/editions/from-template. -->
    <div id="template-modal" class="hidden fixed inset-0 z-50 bg-black/40 flex items-center justify-center px-4">
      <div class="bg-white rounded-lg shadow-xl border border-slate-200 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div class="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <h3 class="text-lg font-bold">Start from template</h3>
          <button id="template-modal-close" class="text-slate-400 hover:text-slate-700 text-2xl leading-none" aria-label="Close">×</button>
        </div>
        <div class="px-5 py-4">
          <p class="text-sm text-slate-600 mb-4">Templates are partial edition configurations you can clone and tweak. The new edition appears in /customize, /publisher, and /matrix immediately.</p>
          <div id="template-list" class="space-y-2"></div>
          <div id="template-form" class="hidden mt-5 pt-4 border-t border-slate-200">
            <div class="text-xs text-slate-500 mb-2">Cloning from template: <span id="template-form-id" class="font-mono text-slate-700"></span></div>
            <label class="block text-xs font-medium text-slate-600 mb-1">New edition id <span class="text-slate-400">(lowercase, hyphenated — e.g. "my-school-bible")</span></label>
            <input id="template-new-id" type="text" maxlength="60" pattern="[a-z][a-z0-9]*(-[a-z0-9]+)*" placeholder="my-new-edition" class="w-full border border-slate-300 rounded px-2 py-1.5 text-sm mb-3 font-mono">
            <label class="block text-xs font-medium text-slate-600 mb-1">New title <span class="text-slate-400">(shown to readers)</span></label>
            <input id="template-new-title" type="text" maxlength="200" placeholder="My New Study Bible" class="w-full border border-slate-300 rounded px-2 py-1.5 text-sm mb-3">
            <div id="template-error" class="hidden text-sm text-red-700 mb-3"></div>
            <div class="flex justify-end gap-2">
              <button id="template-form-cancel" type="button" class="px-3 py-1.5 rounded border border-slate-300 text-sm hover:bg-slate-50">Cancel</button>
              <button id="template-form-create" type="button" class="px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium">Create edition</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ───────── Step 2: Branding ───────── -->
    <section id="step-2" class="step-pane">
      <h2 class="text-2xl font-bold mb-1">2. Brand your edition</h2>
      <p class="text-slate-600 mb-3">Title, publisher, copyright. These appear on the copyright page of the EPUB you build.</p>

      <!-- ψ.11 — reversibility hint. Going back preserves entries
           in JS state until the user explicitly resets / closes
           the tab. Nothing is persisted to disk until BUILD. -->
      <p class="text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 rounded px-3 py-2 mb-5 flex items-center gap-2">
        <span aria-hidden="true">↶</span>
        <span>You can move between steps freely — entries on this page (and every page) survive navigation. Nothing is saved until you click <strong>BUILD</strong> on the final step.</span>
      </p>

      <!-- ψ.11 — fields grouped into 3 visual blocks: identity,
           publisher, copyright + authors. Each fieldset gets a
           small uppercase label so the rhythm reads like a real
           form rather than a flat field list. Ω.0 pivot dropped
           the former ISBN block. term-ref-ok -->

      <fieldset class="psi11-group mb-4">
        <legend class="psi11-legend">Identity</legend>
        <div class="grid grid-cols-1 gap-4">
          <div>
            <label class="label-text" for="w-title">Title</label>
            <input id="w-title" class="field-input" maxlength="200">
          </div>
        </div>
      </fieldset>

      <fieldset class="psi11-group mb-4">
        <legend class="psi11-legend">Publisher / imprint</legend>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="label-text" for="w-publisher_name">Publisher name</label>
            <input id="w-publisher_name" class="field-input" maxlength="200">
          </div>
          <div>
            <label class="label-text" for="w-publisher_url">Publisher URL</label>
            <input id="w-publisher_url" class="field-input" maxlength="500" placeholder="https://...">
          </div>
        </div>
      </fieldset>

      <fieldset class="psi11-group mb-4">
        <legend class="psi11-legend">Copyright &amp; authors</legend>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="label-text" for="w-copyright_year">Copyright year</label>
            <input id="w-copyright_year" class="field-input" maxlength="10">
          </div>
          <div>
            <label class="label-text" for="w-copyright_holder">Copyright holder</label>
            <input id="w-copyright_holder" class="field-input" maxlength="200">
          </div>
          <div class="md:col-span-2">
            <label class="label-text" for="w-authors">Authors <span class="text-slate-400 normal-case font-normal">(one per line, "Name (role)")</span></label>
            <textarea id="w-authors" rows="3" class="field-input font-mono text-sm" placeholder="Dr. Jane Editor (editor)&#10;Bishop John Smith (foreword)"></textarea>
          </div>
        </div>
      </fieldset>

      <div class="mt-6 flex justify-between">
        <button class="back-btn px-5 py-2 rounded border border-slate-300 hover:bg-slate-50">← Back</button>
        <button class="next-btn px-5 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white font-medium">Next →</button>
      </div>
    </section>

    <!-- ───────── Step 3: Theme ───────── -->
    <section id="step-3" class="step-pane">
      <h2 class="text-2xl font-bold mb-1">3. Pick a visual theme</h2>
      <p class="text-slate-600 mb-5">Each theme is a typography + color treatment. The same notes; different feel.</p>
      <div id="theme-cards" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3"></div>
      <div class="mt-6 flex justify-between">
        <button class="back-btn px-5 py-2 rounded border border-slate-300 hover:bg-slate-50">← Back</button>
        <button class="next-btn px-5 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white font-medium">Next →</button>
      </div>
    </section>

    <!-- ───────── Step 4: Content ───────── -->
    <section id="step-4" class="step-pane">
      <h2 class="text-2xl font-bold mb-1">4. Choose your note categories</h2>
      <p class="text-slate-600 mb-5">Click categories to include or exclude entire families of notes. Per-note tweaks happen in <a href="/sources" class="text-blue-600 underline">Sources</a> later.</p>
      <div id="cat-cards" class="grid grid-cols-1 md:grid-cols-2 gap-2"></div>
      <div class="mt-4 text-sm text-slate-500" id="cat-summary"></div>
      <div class="mt-6 flex justify-between">
        <button class="back-btn px-5 py-2 rounded border border-slate-300 hover:bg-slate-50">← Back</button>
        <button class="next-btn px-5 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white font-medium">Next →</button>
      </div>
    </section>

    <!-- ───────── Step 5: Traditions (Phase ψ.8.5) ───────── -->
    <section id="step-5" class="step-pane">
      <h2 class="text-2xl font-bold mb-1">5. Pick traditions to include</h2>
      <p class="text-slate-600 mb-5">
        Notes are tagged by tradition. Choose which denominational lenses
        appear in this edition's popups; <em>Cross-tradition</em> covers
        linguistic and cross-reference apparatus that's denominationally
        neutral. We've pre-selected a sensible default for the profile
        you started from — change anything.
      </p>
      <div id="tradition-cards" class="grid grid-cols-1 md:grid-cols-2 gap-2"></div>
      <div class="mt-4 text-sm text-slate-500" id="trad-summary"></div>

      <!-- Phase ψ.37-E — year-ceiling control inline with traditions
           (both are note filters; one wizard step covers both). -->
      <div class="mt-6 pt-4 border-t border-slate-200">
        <h3 class="text-lg font-semibold mb-1">Time-traveling commentary <span class="text-slate-400 font-normal text-sm">(optional)</span></h3>
        <p class="text-sm text-slate-600 mb-3">
          Restrict commentary to what a reader in a given year would have
          had. Today's PD corpus is 1834-1903; pre-1700 positions are
          empty until a future commentary expansion lands.
        </p>
        <label class="text-sm flex items-center gap-2">
          <span class="font-medium text-slate-700">Year ceiling:</span>
          <select id="wizard-time-ceiling" class="px-2 py-1 rounded border border-slate-300 text-sm">
            <option value="null">no limit (full corpus)</option>
            <option value="2000">by 2000 — modern PD only</option>
            <option value="1900">by 1900 — drops Kenyon (1903)</option>
            <option value="1895">by 1895 — drops Nave's (1897) too</option>
            <option value="1885">by 1885 — drops Strong's (1890)</option>
            <option value="1850">by 1850 — TSK era only (≈6K notes)</option>
            <option value="1700">by 1700 — empty (pre-TSK)</option>
            <option value="1611">by 1611 — King James era (empty)</option>
          </select>
        </label>
      </div>

      <div class="mt-6 flex justify-between">
        <button class="back-btn px-5 py-2 rounded border border-slate-300 hover:bg-slate-50">← Back</button>
        <button class="next-btn px-5 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white font-medium">Next →</button>
      </div>
    </section>

    <!-- ───────── Step 6: Review ───────── -->
    <section id="step-6" class="step-pane">
      <h2 class="text-2xl font-bold mb-1">6. Review before building</h2>
      <p class="text-slate-600 mb-5">Last chance to go back and tweak.</p>
      <div id="review-pane" class="space-y-4"></div>
      <div class="mt-6 flex justify-between">
        <button class="back-btn px-5 py-2 rounded border border-slate-300 hover:bg-slate-50">← Back</button>
        <button class="next-btn px-5 py-2 rounded bg-emerald-600 hover:bg-emerald-700 text-white font-medium">Build my Bible →</button>
      </div>
    </section>

    <!-- ───────── Step 7: Build & Download ───────── -->
    <section id="step-7" class="step-pane">
      <div id="build-stage" class="text-center py-8">
        <div class="text-5xl mb-4">📖</div>
        <h2 class="text-2xl font-bold mb-2">Building your Bible…</h2>
        <p class="text-slate-600 mb-6" id="build-status">Saving your settings…</p>
        <div class="max-w-md mx-auto h-2 rounded-full overflow-hidden bg-slate-200">
          <div class="h-full build-progress" style="width: 100%;"></div>
        </div>
      </div>
      <div id="done-stage" class="hidden text-center py-8">
        <div class="text-6xl mb-4">✓</div>
        <h2 class="text-2xl font-bold text-emerald-700 mb-2">Your Bible is ready</h2>
        <p class="text-slate-600 mb-2" id="done-summary"></p>
        <p class="text-xs text-slate-400 mb-6" id="done-filename"></p>
        <a id="download-link" class="inline-block px-8 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-lg shadow" download>⬇  Download EPUB</a>
        <div class="mt-8">
          <button id="restart-btn" class="text-sm text-slate-500 hover:text-slate-700 underline">Build another</button>
        </div>
      </div>
      <div id="error-stage" class="hidden text-center py-8">
        <div class="text-5xl mb-4">⚠</div>
        <h2 class="text-2xl font-bold text-red-700 mb-2">Build failed</h2>
        <p class="text-slate-600 mb-4" id="error-message"></p>
        <button class="back-btn px-5 py-2 rounded border border-slate-300 hover:bg-slate-50">← Back</button>
      </div>
    </section>

  </div>
</main>

<script>
const STATE = {
  step: 1,
  edition_id: null,           // chosen starting edition
  // Branding fields (Step 2). Ω.0 pivot: no isbn_epub / isbn_print.
  title: '', publisher_name: '', publisher_url: '',
  copyright_year: String(new Date().getFullYear()),
  copyright_holder: '',
  authors: [],                 // list of "Name (role)"
  // Theme (Step 3)
  theme: 'classic',
  // Disabled categories computed via DATA (Step 4)
  enabled_cats: new Set(),
  // Phase ψ.8.5 — Traditions (Step 5). Empty Set = "no tradition
  // filter" (pre-ψ.8 build behaviour). Pre-populated when entering
  // step 5 from the chosen profile's edition_to_tradition mapping.
  traditions: new Set(),
  traditions_initialized: false,  // flag so back→forward keeps user edits
  // Phase ψ.37-E — year ceiling control (Step 5, inline with traditions).
  // null = no filter (default; full corpus); int (year) = filter notes
  // whose source's circa-year > year. Empty/"null" string from the
  // <select> is normalised to null at submit time.
  time_filter_ceiling: null,
};
let DATA = null;

async function init() {
  const [c, m] = await Promise.all([
    fetch('/api/customize').then(r => r.json()),
    fetch('/api/matrix').then(r => r.json()),
  ]);
  DATA = {customize: c, matrix: m};
  document.getElementById('loading').classList.add('hidden');
  document.getElementById('wizard-content').classList.remove('hidden');
  renderStep1();
  renderStep3();
  renderStep4();
  renderStep5();
  // Wire navigation
  document.getElementById('next-1').addEventListener('click', () => goto(2));
  document.querySelectorAll('.back-btn').forEach(b =>
    b.addEventListener('click', () => goto(STATE.step - 1)));
  document.querySelectorAll('.next-btn').forEach(b =>
    b.addEventListener('click', () => {
      if (STATE.step === 6) {
        startBuild();
      } else {
        goto(STATE.step + 1);
      }
    }));
  document.getElementById('restart-btn').addEventListener('click', () => {
    location.reload();
  });
}

function goto(step) {
  if (step < 1 || step > 7) return;
  if (step === 6) renderReview();
  document.querySelectorAll('.step-pane').forEach(p => p.classList.remove('active'));
  document.getElementById(`step-${step}`).classList.add('active');
  // Step indicators
  for (let i = 1; i <= 7; i++) {
    const dot = document.getElementById(`dot-${i}`);
    const line = document.getElementById(`line-${i}`);
    dot.classList.remove('active', 'done');
    if (i < step) dot.classList.add('done');
    else if (i === step) dot.classList.add('active');
    if (line) {
      line.classList.toggle('done', i < step);
    }
  }
  STATE.step = step;
  // When entering Step 2, populate from chosen edition
  if (step === 2 && STATE.edition_id) populateBranding();
  if (step === 3) refreshThemeSelection();
  if (step === 4) refreshCategorySelection();
  // Phase ψ.8.5 — when first entering Step 5, seed sensible defaults
  // from the profile's tradition; thereafter preserve user edits.
  if (step === 5) {
    if (!STATE.traditions_initialized) {
      seedTraditionDefaultsFromProfile();
      STATE.traditions_initialized = true;
    }
    refreshTraditionSelection();
  }
}

// Phase ψ.8.5 — map from starting profile to a sensible tradition
// default. Mirror of the catholic-study → ["catholic","cross"] etc.
// pattern. Falls back to ["cross"] for unknown editions; the user
// can always override on the step itself.
const PROFILE_TO_TRADITIONS = {
  'catholic-study':       ['catholic', 'cross'],
  'reformed':             ['protestant', 'cross'],
  'reformed-study':       ['protestant', 'cross'],
  'evangelical-reformed': ['protestant', 'cross'],
  'orthodox-study':       ['orthodox', 'cross'],
  'orthodox':             ['orthodox', 'cross'],
  'jewish-study':         ['jewish', 'cross'],
  'jewish':               ['jewish', 'cross'],
  'ethiopian-tewahedo':   ['tewahedo', 'cross'],
  'tewahedo':             ['tewahedo', 'cross'],
};

function seedTraditionDefaultsFromProfile() {
  // 1. If the picked edition already has traditions_default set (e.g.
  //    a user-customized edition the wizard is re-running on), respect it.
  const ed = DATA.customize.editions.find(e => e.id === STATE.edition_id);
  if (ed && Array.isArray(ed.traditions_default) && ed.traditions_default.length) {
    STATE.traditions = new Set(ed.traditions_default);
    return;
  }
  // 2. Otherwise pick from the profile-id map.
  const seed = PROFILE_TO_TRADITIONS[STATE.edition_id] || ['cross'];
  STATE.traditions = new Set(seed);
}

// ───────── Step 1 ─────────
function renderStep1() {
  const wrap = document.getElementById('start-cards');
  wrap.innerHTML = DATA.customize.editions.map(e => `
    <div class="pick-card" data-edition="${e.id}">
      <div class="font-semibold mb-1">${esc(e.title)}</div>
      <div class="text-xs text-slate-500 mb-2 font-mono">${e.id}</div>
      <div class="text-sm text-slate-600">${esc(e.target_audience || 'No audience description.')}</div>
    </div>
  `).join('');
  wrap.querySelectorAll('.pick-card').forEach(c => {
    c.addEventListener('click', () => {
      wrap.querySelectorAll('.pick-card').forEach(o => o.classList.remove('picked'));
      c.classList.add('picked');
      STATE.edition_id = c.dataset.edition;
      const btn = document.getElementById('next-1');
      btn.disabled = false;
      btn.classList.remove('opacity-50');
    });
  });
  // ψ.7-B — wire up "Start from template" button
  const tplBtn = document.getElementById('from-template-btn');
  if (tplBtn && !tplBtn.dataset.bound) {
    tplBtn.dataset.bound = '1';
    tplBtn.addEventListener('click', openTemplatePicker);
  }
}

// ψ.7-B — Template picker modal helpers.
let TEMPLATE_PICK = null;  // currently-picked template id

async function openTemplatePicker() {
  const modal = document.getElementById('template-modal');
  const list  = document.getElementById('template-list');
  const form  = document.getElementById('template-form');
  if (!modal || !list || !form) return;
  list.innerHTML = '<div class="text-sm text-slate-400 italic">loading…</div>';
  form.classList.add('hidden');
  modal.classList.remove('hidden');
  let data;
  try {
    const r = await fetch('/api/edition-templates');
    data = await r.json();
  } catch (_) {
    list.innerHTML = '<div class="text-sm text-red-700">Failed to load templates.</div>';
    return;
  }
  const templates = (data && data.templates) || [];
  if (!templates.length) {
    list.innerHTML = '<div class="text-sm text-slate-400 italic">No templates installed.</div>';
    return;
  }
  list.innerHTML = templates.map(t => `
    <div class="template-row border border-slate-200 rounded p-3 hover:bg-slate-50 cursor-pointer" data-template="${esc(t.template_id)}">
      <div class="flex items-center justify-between mb-1">
        <div class="font-semibold text-slate-700">${esc(t.label)}</div>
        <div class="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-mono">${esc(t.canon)}</div>
      </div>
      <div class="text-xs text-slate-500 mb-1">${esc(t.target_audience || '')}</div>
      <div class="text-sm text-slate-600">${esc(t.description || '')}</div>
    </div>
  `).join('');
  list.querySelectorAll('.template-row').forEach(row => {
    row.addEventListener('click', () => {
      list.querySelectorAll('.template-row').forEach(r =>
        r.classList.remove('ring-2', 'ring-blue-400'));
      row.classList.add('ring-2', 'ring-blue-400');
      TEMPLATE_PICK = row.dataset.template;
      document.getElementById('template-form-id').textContent = TEMPLATE_PICK;
      form.classList.remove('hidden');
      // Suggest a default new_id from the template id + "-mine"
      const idIn = document.getElementById('template-new-id');
      if (!idIn.value) idIn.value = TEMPLATE_PICK + '-mine';
      idIn.focus();
    });
  });
}

function closeTemplatePicker() {
  const modal = document.getElementById('template-modal');
  if (modal) modal.classList.add('hidden');
  TEMPLATE_PICK = null;
  const errEl = document.getElementById('template-error');
  if (errEl) errEl.classList.add('hidden');
}

async function createFromTemplate() {
  const idIn = document.getElementById('template-new-id');
  const titleIn = document.getElementById('template-new-title');
  const errEl = document.getElementById('template-error');
  errEl.classList.add('hidden');
  if (!TEMPLATE_PICK) {
    errEl.textContent = 'Pick a template first.';
    errEl.classList.remove('hidden');
    return;
  }
  const new_id = (idIn.value || '').trim();
  const new_title = (titleIn.value || '').trim();
  if (!new_id || !new_title) {
    errEl.textContent = 'Both new id and new title are required.';
    errEl.classList.remove('hidden');
    return;
  }
  try {
    const r = await fetch('/api/editions/from-template', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        template_id: TEMPLATE_PICK,
        new_id: new_id,
        new_title: new_title,
      }),
    });
    const data = await r.json();
    if (!r.ok || data.error) {
      errEl.textContent = data.message || data.error || 'Failed to create edition.';
      errEl.classList.remove('hidden');
      return;
    }
    closeTemplatePicker();
    // Hard-refresh so the new edition appears in DATA.customize.editions
    window.location.reload();
  } catch (e) {
    errEl.textContent = 'Network error: ' + (e && e.message || e);
    errEl.classList.remove('hidden');
  }
}

// Bind modal close + create handlers once on page load
document.addEventListener('DOMContentLoaded', () => {
  const closeBtn = document.getElementById('template-modal-close');
  if (closeBtn) closeBtn.addEventListener('click', closeTemplatePicker);
  const cancelBtn = document.getElementById('template-form-cancel');
  if (cancelBtn) cancelBtn.addEventListener('click', closeTemplatePicker);
  const createBtn = document.getElementById('template-form-create');
  if (createBtn) createBtn.addEventListener('click', createFromTemplate);
  // ESC closes modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const modal = document.getElementById('template-modal');
      if (modal && !modal.classList.contains('hidden')) closeTemplatePicker();
    }
  });
});

// ───────── Step 2 ─────────
async function populateBranding() {
  // Pull current values from the chosen edition
  const ed = DATA.customize.editions.find(e => e.id === STATE.edition_id);
  const pub = await fetch('/api/publisher').then(r => r.json());
  const pubEd = pub.editions.find(e => e.id === STATE.edition_id);
  // Apply if state empty (don't clobber user edits)
  STATE.title = STATE.title || ed.title || '';
  STATE.theme = STATE.theme === 'classic' ? (ed.theme || 'classic') : STATE.theme;
  for (const f of ['publisher_name','publisher_url',
                    'copyright_year','copyright_holder']) {
    if (!STATE[f]) STATE[f] = pubEd[f] || '';
  }
  if (!STATE.authors.length) STATE.authors = [...(pubEd.authors || [])];
  // Sync to inputs
  document.getElementById('w-title').value = STATE.title;
  for (const f of ['publisher_name','publisher_url',
                    'copyright_year','copyright_holder']) {
    document.getElementById(`w-${f}`).value = STATE[f];
  }
  document.getElementById('w-authors').value = STATE.authors.join('\n');
  // Wire inputs to STATE
  document.getElementById('w-title').oninput = ev => STATE.title = ev.target.value;
  for (const f of ['publisher_name','publisher_url',
                    'copyright_year','copyright_holder']) {
    document.getElementById(`w-${f}`).oninput = ev => STATE[f] = ev.target.value;
  }
  document.getElementById('w-authors').oninput = ev =>
    STATE.authors = ev.target.value.split('\n').map(s => s.trim()).filter(Boolean);
}

// ───────── Step 3 ─────────
function renderStep3() {
  const wrap = document.getElementById('theme-cards');
  wrap.innerHTML = (DATA.customize.themes || []).map(t => `
    <div class="pick-card" data-theme="${t.id}">
      <div class="font-semibold mb-1">${esc(t.name)}</div>
      <div class="text-xs text-slate-500 mb-2">${esc(t.description || '')}</div>
      <div class="theme-preview theme-${t.id}">
        <strong>Genesis 1:1.</strong> In the beginning, God created the heavens and the earth.
      </div>
    </div>
  `).join('');
  // Apply mini theme previews via inline styles
  wrap.querySelectorAll('.theme-classic').forEach(p => p.style.fontFamily = 'Georgia, serif');
  wrap.querySelectorAll('.theme-modern').forEach(p => {
    p.style.fontFamily = 'system-ui, sans-serif'; p.style.color = '#1a202c';
  });
  wrap.querySelectorAll('.theme-scholarly').forEach(p => {
    p.style.fontFamily = 'Charter, Palatino, serif'; p.style.fontSize = '0.82em';
  });
  wrap.querySelectorAll('.theme-devotional').forEach(p => {
    p.style.fontFamily = 'Iowan Old Style, Palatino, serif';
    p.style.background = '#fffbf3'; p.style.color = '#2c1810';
    p.style.fontStyle = 'italic';
  });
  wrap.querySelectorAll('.theme-school').forEach(p => {
    p.style.fontFamily = 'Verdana, sans-serif'; p.style.fontSize = '1.05em';
  });
  wrap.querySelectorAll('.pick-card').forEach(c => {
    c.addEventListener('click', () => {
      wrap.querySelectorAll('.pick-card').forEach(o => o.classList.remove('picked'));
      c.classList.add('picked');
      STATE.theme = c.dataset.theme;
    });
  });
}

function refreshThemeSelection() {
  document.querySelectorAll('#theme-cards .pick-card').forEach(c => {
    c.classList.toggle('picked', c.dataset.theme === STATE.theme);
  });
}

// ───────── Step 4 ─────────
function renderStep4() {
  const wrap = document.getElementById('cat-cards');
  const cats = (DATA.matrix.categories || []).slice().sort((a,b) => a.sort_order - b.sort_order);
  // Pre-populate from chosen edition's enabled categories
  if (STATE.enabled_cats.size === 0 && STATE.edition_id) {
    const ed = DATA.customize.editions.find(e => e.id === STATE.edition_id);
    const enabled = (DATA.matrix.editions || []).find(e => e.id === STATE.edition_id);
    if (enabled) {
      STATE.enabled_cats = new Set(
        cats.filter(c => (enabled.cells[c.id] || {}).any_enabled).map(c => c.id)
      );
    }
  }
  wrap.innerHTML = cats.map(c => {
    const checked = STATE.enabled_cats.has(c.id);
    const kindCount = (DATA.matrix.kinds || []).filter(k => k.category === c.id).length;
    return `
      <div class="kind-row pick-card !p-3" data-cat="${c.id}">
        <div class="flex items-center gap-3">
          <input type="checkbox" ${checked ? 'checked' : ''} class="w-4 h-4 cursor-pointer pointer-events-none">
          <div class="flex-1">
            <div class="font-semibold">${esc(c.symbol)} <span class="ml-1">${esc(c.label)}</span></div>
            <div class="text-xs text-slate-500">${esc(c.description || '')} · ${kindCount} note kind${kindCount === 1 ? '' : 's'}</div>
          </div>
        </div>
      </div>
    `;
  }).join('');
  wrap.querySelectorAll('.kind-row').forEach(row => {
    row.addEventListener('click', () => {
      const id = row.dataset.cat;
      if (STATE.enabled_cats.has(id)) STATE.enabled_cats.delete(id);
      else STATE.enabled_cats.add(id);
      const cb = row.querySelector('input[type="checkbox"]');
      cb.checked = STATE.enabled_cats.has(id);
      row.classList.toggle('picked', STATE.enabled_cats.has(id));
      renderCatSummary();
    });
  });
  refreshCategorySelection();
}

function refreshCategorySelection() {
  document.querySelectorAll('#cat-cards .kind-row').forEach(row => {
    const id = row.dataset.cat;
    const on = STATE.enabled_cats.has(id);
    row.classList.toggle('picked', on);
    const cb = row.querySelector('input[type="checkbox"]');
    if (cb) cb.checked = on;
  });
  renderCatSummary();
}

function renderCatSummary() {
  const n = STATE.enabled_cats.size;
  document.getElementById('cat-summary').textContent =
    `${n} of ${(DATA.matrix.categories || []).length} categories enabled`;
}

// ───────── Step 5: Traditions (Phase ψ.8.5) ─────────
function renderStep5() {
  const wrap = document.getElementById('tradition-cards');
  const traditions = DATA.customize.traditions || [];
  wrap.innerHTML = traditions.map(t => `
    <div class="kind-row pick-card !p-3" data-tradition="${t.id}">
      <div class="flex items-center gap-3">
        <input type="checkbox" class="w-4 h-4 cursor-pointer pointer-events-none">
        <div class="flex-1">
          <div class="font-semibold">${esc(t.label)}</div>
          <div class="text-xs text-slate-500 font-mono">${esc(t.id)}</div>
        </div>
      </div>
    </div>
  `).join('');
  wrap.querySelectorAll('.kind-row').forEach(row => {
    row.addEventListener('click', () => {
      const id = row.dataset.tradition;
      if (STATE.traditions.has(id)) STATE.traditions.delete(id);
      else STATE.traditions.add(id);
      const cb = row.querySelector('input[type="checkbox"]');
      cb.checked = STATE.traditions.has(id);
      row.classList.toggle('picked', STATE.traditions.has(id));
      renderTraditionSummary();
    });
  });
  refreshTraditionSelection();
}

function refreshTraditionSelection() {
  document.querySelectorAll('#tradition-cards .kind-row').forEach(row => {
    const id = row.dataset.tradition;
    const on = STATE.traditions.has(id);
    row.classList.toggle('picked', on);
    const cb = row.querySelector('input[type="checkbox"]');
    if (cb) cb.checked = on;
  });
  renderTraditionSummary();
}

function renderTraditionSummary() {
  const n = STATE.traditions.size;
  const total = (DATA.customize.traditions || []).length;
  const el = document.getElementById('trad-summary');
  if (!el) return;
  if (n === 0) {
    el.textContent =
      `0 of ${total} selected — no tradition filter (every note survives)`;
  } else {
    el.textContent = `${n} of ${total} traditions enabled`;
  }
}

// ───────── Step 6 ─────────
function renderReview() {
  const cats = (DATA.matrix.categories || []).filter(c => STATE.enabled_cats.has(c.id));
  const themeName = (DATA.customize.themes || []).find(t => t.id === STATE.theme)?.name || STATE.theme;
  const ed = DATA.customize.editions.find(e => e.id === STATE.edition_id);
  // Phase ψ.8.5 — tradition labels for the review chip row, in
  // canonical order (the registry is already canonical).
  const tradList = (DATA.customize.traditions || [])
    .filter(t => STATE.traditions.has(t.id));
  const tradHtml = tradList.length
    ? tradList.map(t => `<span class="pill mr-1 mb-1">${esc(t.label)}</span>`).join('')
    : '<span class="text-slate-400 italic text-sm">no tradition filter — every note survives</span>';
  document.getElementById('review-pane').innerHTML = `
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="bg-slate-50 border border-slate-200 rounded p-4">
        <div class="text-xs uppercase tracking-wide text-slate-500 mb-2">Edition</div>
        <div class="font-semibold">${esc(STATE.title || ed.title)}</div>
        <div class="text-xs text-slate-500 font-mono mt-1">based on: ${esc(STATE.edition_id)}</div>
      </div>
      <div class="bg-slate-50 border border-slate-200 rounded p-4">
        <div class="text-xs uppercase tracking-wide text-slate-500 mb-2">Branding</div>
        <div>${esc(STATE.publisher_name || 'Independent')}</div>
        <div class="text-xs text-slate-500">© ${esc(STATE.copyright_year)} ${esc(STATE.copyright_holder || '—')}</div>
      </div>
      <div class="bg-slate-50 border border-slate-200 rounded p-4">
        <div class="text-xs uppercase tracking-wide text-slate-500 mb-2">Theme</div>
        <div class="font-semibold">${esc(themeName)}</div>
      </div>
      <div class="bg-slate-50 border border-slate-200 rounded p-4">
        <div class="text-xs uppercase tracking-wide text-slate-500 mb-2">Categories enabled</div>
        <div class="text-sm">${cats.map(c => `<span class="pill mr-1 mb-1">${esc(c.symbol)} ${esc(c.label)}</span>`).join('')}</div>
      </div>
      <div class="bg-slate-50 border border-slate-200 rounded p-4 md:col-span-2">
        <div class="text-xs uppercase tracking-wide text-slate-500 mb-2">Traditions (popup filter)</div>
        <div class="text-sm">${tradHtml}</div>
      </div>
    </div>
    <div class="bg-amber-50 border border-amber-200 rounded p-3 mt-4 text-sm">
      <strong>Note:</strong> clicking <em>Build my Bible</em> will save these settings to <code class="font-mono">${esc(STATE.edition_id)}</code> and produce a fresh EPUB. The corpus itself is not modified.
    </div>

    <!-- ψ.1.2 — live preview iframe. Reads /api/preview rendering
         the persisted state of STATE.edition_id (the wizard's
         in-progress edits aren't saved until Build, so the preview
         shows the starting-from edition's spec). The status strip
         makes that explicit. -->
    <div class="bg-white border border-slate-200 rounded mt-4">
      <div class="px-4 py-3 border-b border-slate-200 flex items-center gap-3 flex-wrap">
        <h3 class="font-semibold text-slate-700 flex-1">
          👁 Live preview
          <span class="text-xs font-normal text-slate-400 ml-2">— see the chapter rendered</span>
        </h3>
        <label class="text-xs flex items-center gap-1.5">
          <span>book:</span>
          <select id="psi12-preview-book" class="field-input" style="padding:0.25rem 0.5rem; font-size:0.85rem; min-width:9rem;"></select>
        </label>
        <label class="text-xs flex items-center gap-1.5">
          <span>chapter:</span>
          <input id="psi12-preview-chapter" type="number" min="1" value="1" class="field-input" style="padding:0.25rem 0.5rem; font-size:0.85rem; width:4rem;">
        </label>
        <button id="psi12-preview-refresh" type="button" class="px-2 py-1 rounded border border-slate-300 text-xs hover:bg-slate-50">↻ Refresh</button>
      </div>
      <div class="px-4 py-2 text-xs text-slate-500 bg-slate-50 border-b border-slate-200 flex items-center gap-3 flex-wrap">
        <span id="psi12-preview-status">loading…</span>
        <span class="text-slate-400">·</span>
        <span class="italic">Showing the persisted state of <code class="font-mono">${esc(STATE.edition_id)}</code>. Wizard edits apply on Build.</span>
      </div>
      <iframe id="psi12-preview-iframe" sandbox="allow-same-origin" style="border:0; width:100%; min-height:50vh; background:white;"></iframe>
    </div>
  `;
  // ψ.1.2 — wire the preview iframe handlers + initial fetch.
  initPsi12Preview();
}

// ─── ψ.1.2 — wizard preview iframe ────────────────────────────
function initPsi12Preview() {
  const bookSel = document.getElementById('psi12-preview-book');
  const chInp = document.getElementById('psi12-preview-chapter');
  const refreshBtn = document.getElementById('psi12-preview-refresh');
  if (!bookSel || !chInp || !refreshBtn) return;
  // Populate book picker from the edition's canon.
  const canonBooks = (DATA.customize.edition_canon_books || {})[STATE.edition_id] || [];
  const booksByCode = {};
  for (const b of (DATA.customize.books_canonical || [])) booksByCode[b.code] = b;
  bookSel.innerHTML = canonBooks.map(code => {
    const b = booksByCode[code] || {code, title: code};
    return `<option value="${code}">${esc(b.title || code)}</option>`;
  }).join('');
  // Default: last-used per-edition via localStorage, else jhn 1
  // if in canon, else first canon book.
  const lastKey = 'psi12-last-' + STATE.edition_id;
  let lastVal;
  try { lastVal = localStorage.getItem(lastKey); } catch (_) { lastVal = null; }
  if (lastVal) {
    const [bc, ch] = lastVal.split(':');
    if (canonBooks.includes(bc)) {
      bookSel.value = bc;
      if (ch) chInp.value = ch;
    }
  } else {
    if (canonBooks.includes('jhn')) bookSel.value = 'jhn';
    chInp.value = 1;
  }
  // Bind once per renderReview call (cleared on re-render via
  // innerHTML replacement, so no dataset.bound dance needed).
  refreshBtn.addEventListener('click', refreshPsi12Preview);
  bookSel.addEventListener('change', refreshPsi12Preview);
  let timer = null;
  chInp.addEventListener('input', () => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(refreshPsi12Preview, 300);
  });
  // Kick off the initial fetch.
  refreshPsi12Preview();
}

async function refreshPsi12Preview() {
  if (!STATE.edition_id) return;
  const bookSel = document.getElementById('psi12-preview-book');
  const chInp = document.getElementById('psi12-preview-chapter');
  const status = document.getElementById('psi12-preview-status');
  const iframe = document.getElementById('psi12-preview-iframe');
  if (!bookSel || !chInp || !status || !iframe) return;
  const bookCode = bookSel.value;
  const ch = parseInt(chInp.value, 10) || 1;
  if (!bookCode) {
    status.textContent = 'pick a book to preview';
    return;
  }
  try { localStorage.setItem('psi12-last-' + STATE.edition_id, bookCode + ':' + ch); } catch (_) {}
  status.textContent = 'loading ' + bookCode + ' ' + ch + '…';
  try {
    const r = await fetch('/api/preview/' + encodeURIComponent(STATE.edition_id)
                          + '/' + encodeURIComponent(bookCode)
                          + '/' + encodeURIComponent(ch));
    const data = await r.json();
    if (!r.ok || data.status !== 'ok') {
      const msg = (data.message || data.error || 'preview failed');
      status.innerHTML = '<span class="text-red-700">✗ ' + esc(msg) + '</span>';
      return;
    }
    iframe.srcdoc = data.html;
    status.textContent = bookCode + ' ' + ch + ' · '
      + data.verse_count + ' verses · '
      + data.notes_shown + ' notes shown';
  } catch (e) {
    status.innerHTML = '<span class="text-red-700">✗ network error: '
      + esc(String(e && e.message || e)) + '</span>';
  }
}

// ───────── Step 7: Build ─────────
async function startBuild() {
  goto(7);
  document.getElementById('build-stage').classList.remove('hidden');
  document.getElementById('done-stage').classList.add('hidden');
  document.getElementById('error-stage').classList.add('hidden');
  const status = document.getElementById('build-status');

  try {
    // 1. Save edition meta (title, theme, traditions_default)
    status.textContent = 'Saving your branding…';
    // Phase ψ.8.5 — fold the wizard's tradition picks into the same
    // edition-meta save so the build pipeline picks up the filter on
    // the very next /api/export/build call. Empty Set sends an empty
    // list, which the validator translates to "no filter" (§7.2 no-op).
    // Phase ψ.37-E — fold the wizard's year-ceiling pick into the
    // edition-meta save. Read the <select> value at submit time so
    // the JS doesn't need a separate event listener.
    const ceilEl = document.getElementById('wizard-time-ceiling');
    const ceilRaw = ceilEl ? ceilEl.value : 'null';
    const ceilNorm = (ceilRaw === 'null' || ceilRaw === '') ? null : parseInt(ceilRaw, 10);
    STATE.time_filter_ceiling = (Number.isFinite(ceilNorm) ? ceilNorm : null);
    const editionMeta = {
      title: STATE.title,
      theme: STATE.theme,
      traditions_default: [...STATE.traditions],
      time_filter_ceiling: STATE.time_filter_ceiling,
    };
    const r1 = await fetch(`/api/edition-meta/${encodeURIComponent(STATE.edition_id)}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(editionMeta),
    });
    if (!r1.ok) throw new Error('failed to save edition meta');

    // 2. Save publisher fields
    status.textContent = 'Saving publisher info…';
    const pubMeta = {
      publisher_name: STATE.publisher_name,
      publisher_url: STATE.publisher_url,
      copyright_year: STATE.copyright_year,
      copyright_holder: STATE.copyright_holder,
      authors: STATE.authors,
    };
    const r2 = await fetch(`/api/publisher/${encodeURIComponent(STATE.edition_id)}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(pubMeta),
    });
    if (!r2.ok) throw new Error('failed to save publisher info');

    // 3. Build the EPUB
    status.textContent = 'Building EPUB (this can take a minute)…';
    const r3 = await fetch(`/api/export/build/${encodeURIComponent(STATE.edition_id)}`, {
      method: 'PUT',
    });
    const data = await r3.json();
    if (!r3.ok || !data.ok) throw new Error(data.error || 'build failed');

    // Done
    document.getElementById('build-stage').classList.add('hidden');
    document.getElementById('done-stage').classList.remove('hidden');
    document.getElementById('done-summary').textContent =
      `${esc(STATE.title || STATE.edition_id)} — ${data.size_mb} MB`;
    document.getElementById('done-filename').textContent = data.filename;
    document.getElementById('download-link').href = data.download_url;
  } catch (err) {
    document.getElementById('build-stage').classList.add('hidden');
    document.getElementById('error-stage').classList.remove('hidden');
    document.getElementById('error-message').textContent = err.message || String(err);
  }
}

function esc(s) {
  return (s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

init().catch(e => {
  document.getElementById('loading').textContent = 'failed to load: ' + e.message;
});
</script>

<!-- ω.0.6 — UI defense prelude — START -->
<!-- Re-injecting / refreshing this block uses
     scripts/bulk_inject.py replace --open-marker "ω.0.6 — UI defense prelude — START"
     ...                          --close-marker "ω.0.6 — UI defense prelude — END"
     The markers are stable contracts; do not change without a coordinated migration. -->
<script>
(function () {
  'use strict';

  // -------------------------------------------------------------------
  // Tier 4 — Global error backstop. Catches anything that escapes
  // the other tiers (null-pointer accesses, unhandled rejections,
  // syntax errors in inline scripts) and shows a soft red banner
  // instead of leaving the page frozen.
  // -------------------------------------------------------------------

  function ensureErrorBanner() {
    var banner = document.getElementById('ebible-error-banner');
    if (banner) return banner;
    banner = document.createElement('div');
    banner.id = 'ebible-error-banner';
    banner.setAttribute('role', 'alert');
    banner.setAttribute('aria-live', 'polite');
    banner.style.cssText =
      'position:fixed;top:0;left:0;right:0;z-index:9999;' +
      'background:#dc2626;color:#fff;padding:8px 16px;font-size:13px;' +
      'font-family:system-ui,sans-serif;display:none;' +
      'box-shadow:0 2px 4px rgba(0,0,0,0.1)';
    banner.innerHTML =
      '<div style="max-width:72rem;margin:0 auto;display:flex;' +
      'align-items:center;justify-content:space-between;gap:12px">' +
      '<span class="ebible-error-text" style="flex:1;min-width:0;' +
      'overflow:hidden;text-overflow:ellipsis;white-space:nowrap"></span>' +
      '<button type="button" class="ebible-error-dismiss" ' +
      'style="background:none;border:1px solid rgba(255,255,255,0.4);' +
      'color:#fff;padding:2px 10px;border-radius:4px;cursor:pointer;' +
      'font-size:12px">Dismiss</button></div>';
    if (document.body) {
      document.body.appendChild(banner);
    } else {
      document.addEventListener('DOMContentLoaded', function () {
        document.body.appendChild(banner);
      });
    }
    banner.querySelector('.ebible-error-dismiss')
      .addEventListener('click', function () { banner.style.display = 'none'; });
    return banner;
  }

  function showErrorBanner(message) {
    try {
      var banner = ensureErrorBanner();
      var text = banner.querySelector('.ebible-error-text');
      if (text) text.textContent = message;
      banner.style.display = 'block';
    } catch (e) {
      // If even the banner fails, log to console as last resort
      try { console.error('[ebible] error banner failed:', e, message); }
      catch (_) {}
    }
  }

  // Install global error handlers
  window.addEventListener('error', function (ev) {
    var msg = (ev && ev.message) ? ev.message : 'Script error';
    // Filter out "Script error." with no info — usually cross-origin
    // loaded resources, nothing actionable for us
    if (msg === 'Script error.') return;
    showErrorBanner('Something went wrong: ' + msg);
    try { console.error('[ebible global error]', ev.error || msg); }
    catch (_) {}
  });
  window.addEventListener('unhandledrejection', function (ev) {
    var reason = ev && ev.reason;
    var msg = (reason && reason.message) ? reason.message : String(reason);
    showErrorBanner('Background task failed: ' + msg);
    try { console.error('[ebible unhandled rejection]', reason); }
    catch (_) {}
  });

  // -------------------------------------------------------------------
  // Tier 2 — safeFetch wrapper. Standard helper for every API call.
  // Throws on non-OK status, parses JSON safely, surfaces failures
  // via the banner. Re-throws so callers can do feature-specific
  // handling on top.
  // -------------------------------------------------------------------

  async function safeFetch(url, opts) {
    opts = opts || {};
    let response;
    try {
      response = await fetch(url, opts);
    } catch (netErr) {
      // Network drop, DNS fail, fetch aborted, etc.
      const msg = (netErr && netErr.message) ? netErr.message : 'network error';
      showErrorBanner('Network error: ' + msg + ' (' + url + ')');
      throw netErr;
    }
    if (!response.ok) {
      let errMsg = response.status + ' ' + response.statusText;
      try {
        const text = await response.text();
        if (text) {
          try {
            const parsed = JSON.parse(text);
            if (parsed && parsed.error) errMsg = parsed.error;
          } catch (_) {
            // Not JSON; use text snippet
            errMsg = text.slice(0, 200);
          }
        }
      } catch (_) {}
      showErrorBanner('API ' + response.status + ': ' + errMsg);
      const err = new Error(errMsg);
      err.status = response.status;
      throw err;
    }
    // Parse response. If empty body, return null (DELETE often is).
    const text = await response.text();
    if (!text) return null;
    try {
      return JSON.parse(text);
    } catch (parseErr) {
      showErrorBanner('Server returned invalid JSON from ' + url);
      throw parseErr;
    }
  }

  // -------------------------------------------------------------------
  // Tier 3 — DOM null-safe helpers. querySelector / querySelectorAll
  // wrappers that don't throw on missing elements. Opt-in: existing
  // code keeps working; new code can adopt these.
  // -------------------------------------------------------------------

  function safe$(selector, parent) {
    try {
      return (parent || document).querySelector(selector);
    } catch (e) {
      // Invalid selector syntax → log and return null instead of crash
      try { console.warn('[safe$] invalid selector:', selector, e); }
      catch (_) {}
      return null;
    }
  }

  function safe$$(selector, parent) {
    try {
      return Array.from((parent || document).querySelectorAll(selector));
    } catch (e) {
      try { console.warn('[safe$$] invalid selector:', selector, e); }
      catch (_) {}
      return [];
    }
  }

  // -------------------------------------------------------------------
  // ω.0.7 — Shared escape helpers. Eleven separate definitions of
  // essentially the same HTML-escaping logic existed across the
  // consoles before this consolidation. New code should use
  // window.ebible.escapeHtml (or the bare alias). Existing call
  // sites can migrate incrementally.
  // -------------------------------------------------------------------

  var ESCAPE_HTML_MAP = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  };

  function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, function (c) {
      return ESCAPE_HTML_MAP[c] || c;
    });
  }

  // -------------------------------------------------------------------
  // Public surface — attach to window.ebible namespace
  // -------------------------------------------------------------------

  window.ebible = window.ebible || {};
  window.ebible.showErrorBanner = showErrorBanner;
  window.ebible.safeFetch = safeFetch;
  window.ebible.safe$ = safe$;
  window.ebible.safe$$ = safe$$;
  window.ebible.escapeHtml = escapeHtml;
  // Convenience aliases for less typing in inline scripts
  window.safeFetch = safeFetch;
  window.safe$ = safe$;
  window.safe$$ = safe$$;
  window.escapeHtml = escapeHtml;
})();
</script>
<!-- ω.0.6 — UI defense prelude — END -->

</body>
</html>
"""


# ψ.13.5: consolidated design-system substitution.
WIZARD_HTML = apply_design_system(WIZARD_HTML, "/wizard")
