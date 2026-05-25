"""HTML for /index console — extracted from scripts/web.py
during the web.py split refactor (2026-05-07).

Re-imported by scripts/web.py for back-compat with existing
`from scripts.web import INDEX_HTML` callers.

ψ.16 status-dashboard polish (2026-05-10): `BUYER_ARC_POLISH_CSS`
inlined from `_design`. The editor's distinctive heavy nav stays
(it has its own Bible-app brand chrome — `bg-slate-900` header,
3-pane editor layout — that the lighter dashboard polish would
clash with). HEADER_NAV_LINKS is intentionally NOT added here
because the cross-link linter (§6.2) exempts INDEX_HTML for
exactly this reason ("different layout"). The polish CSS itself
brings the same focus rings, transition curves, and tactile
button feedback the dashboard consoles got — universal UX wins
that don't impose a layout.
"""

from scripts.templates._design import BUYER_ARC_POLISH_CSS, WELCOME_OVERLAY_JS  # noqa: E402

INDEX_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>YHWH Ya' Way · note editor</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: ui-sans-serif, system-ui, -apple-system, sans-serif; }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
  .preview strong { font-weight: 600; }
  .preview em { font-style: italic; }
  .preview a { color: #2563eb; text-decoration: underline; }
  .scroll-thin::-webkit-scrollbar { width: 6px; }
  .scroll-thin::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
</style>
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="bg-slate-50 text-slate-900 h-screen flex flex-col">

<header class="bg-slate-900 text-white px-4 py-2 flex items-center gap-4 shadow">
  <h1 class="font-bold text-lg">YHWH Ya' Way</h1>
  <span class="text-slate-400 text-sm">note editor</span>
  <span id="hdr-stats" class="text-slate-400 text-sm ml-auto"></span>
</header>

<main class="flex-1 flex overflow-hidden">

  <!-- Books column -->
  <aside class="w-64 border-r bg-white flex flex-col">
    <div class="p-3 border-b">
      <input id="book-search" placeholder="filter books…"
        class="w-full text-sm border rounded px-2 py-1"/>
    </div>
    <div id="book-list" class="flex-1 overflow-y-auto scroll-thin p-2 space-y-0.5">
      <div class="text-slate-400 text-sm p-2">loading…</div>
    </div>
  </aside>

  <!-- Notes column -->
  <section class="flex-1 flex flex-col overflow-hidden bg-slate-50">
    <div class="px-4 py-2 border-b bg-white flex items-center gap-3">
      <h2 id="notes-title" class="font-semibold">select a book</h2>
      <span id="notes-count" class="text-sm text-slate-500"></span>
      <button id="add-btn" class="ml-auto bg-emerald-600 hover:bg-emerald-700
        text-white text-sm px-3 py-1 rounded" disabled>+ add note</button>
    </div>
    <div class="px-4 py-2 border-b bg-white flex items-center gap-2 flex-wrap">
      <input id="kind-filter" placeholder="filter kind…"
        class="text-sm border rounded px-2 py-1 w-40"/>
      <input id="text-filter" placeholder="filter text…"
        class="text-sm border rounded px-2 py-1 w-40"/>
      <label class="text-sm flex items-center gap-1">
        <input type="checkbox" id="quality-only"/> only quality flags
      </label>
    </div>
    <div id="notes-list" class="flex-1 overflow-y-auto scroll-thin p-2 space-y-1">
      <div class="text-slate-400 text-sm p-4">pick a book on the left</div>
    </div>
  </section>

  <!-- Editor column -->
  <aside class="w-[28rem] border-l bg-white flex flex-col overflow-hidden">
    <div class="px-4 py-2 border-b bg-slate-100">
      <h2 class="font-semibold">editor</h2>
    </div>
    <div id="editor" class="flex-1 overflow-y-auto scroll-thin p-4 space-y-3">
      <div class="text-slate-400 text-sm">select a note to edit, or click + to add</div>
    </div>
  </aside>

</main>

<div id="toast" class="hidden fixed bottom-4 right-4 bg-slate-900 text-white px-4 py-2 rounded shadow-lg"></div>

<script>
const $ = sel => document.querySelector(sel);
const $$ = sel => Array.from(document.querySelectorAll(sel));

const state = {
  books: [],
  kinds: [],
  currentBook: null,
  notes: [],
  editingIndex: null,   // null means a brand-new note
  editingDraft: null,
};

function toast(msg, isError) {
  const t = $('#toast');
  t.textContent = msg;
  t.className = 'fixed bottom-4 right-4 px-4 py-2 rounded shadow-lg ' +
    (isError ? 'bg-rose-700 text-white' : 'bg-slate-900 text-white');
  t.classList.remove('hidden');
  setTimeout(() => t.classList.add('hidden'), 2200);
}

async function api(path, opts) {
  const r = await fetch(path, opts);
  const data = await r.json();
  if (data.error) throw new Error(data.error);
  return data;
}

async function init() {
  try {
    const [b, k] = await Promise.all([
      api('/api/books'), api('/api/kinds')
    ]);
    state.books = b.books;
    state.kinds = k.kinds;
    renderBooks();
    const total = state.books.reduce((s, x) => s + x.note_count, 0);
    $('#hdr-stats').textContent =
      `${state.books.length} books · ${total.toLocaleString()} notes · ${state.kinds.length} kinds`;
  } catch (e) {
    toast('failed to load: ' + e.message, true);
  }
}

function renderBooks() {
  const filter = ($('#book-search').value || '').toLowerCase();
  const list = $('#book-list');
  list.innerHTML = '';
  const filtered = state.books.filter(b =>
    !filter || b.code.includes(filter) || b.name.toLowerCase().includes(filter)
  );
  for (const b of filtered) {
    const div = document.createElement('div');
    div.className = 'cursor-pointer px-2 py-1 rounded hover:bg-slate-100 text-sm flex items-center';
    if (state.currentBook === b.code) div.classList.add('bg-blue-50', 'font-semibold');
    div.innerHTML = `<span class="mono text-xs text-slate-500 w-12">${b.code}</span>
      <span class="flex-1 truncate">${b.name}</span>
      <span class="text-xs text-slate-400 ml-1">${b.note_count}</span>`;
    div.onclick = () => loadBook(b.code);
    list.appendChild(div);
  }
}

async function loadBook(code) {
  state.currentBook = code;
  state.editingIndex = null;
  state.editingDraft = null;
  renderBooks();
  $('#notes-title').textContent = code;
  $('#notes-count').textContent = '';
  $('#notes-list').innerHTML = '<div class="text-slate-400 text-sm p-4">loading…</div>';
  $('#add-btn').disabled = false;
  $('#editor').innerHTML = '<div class="text-slate-400 text-sm">select a note to edit, or click + to add</div>';
  try {
    const data = await api('/api/notes/' + code);
    state.notes = data.notes;
    renderNotes();
  } catch (e) {
    toast('load failed: ' + e.message, true);
  }
}

function renderNotes() {
  const list = $('#notes-list');
  const kindFilter = ($('#kind-filter').value || '').toLowerCase();
  const textFilter = ($('#text-filter').value || '').toLowerCase();
  const qualityOnly = $('#quality-only').checked;
  const filtered = state.notes.filter(n => {
    if (kindFilter && !n.kind.includes(kindFilter)) return false;
    if (textFilter) {
      const hay = (n.body + ' ' + n.title + ' ' + n.label + ' ' + n.anchor).toLowerCase();
      if (!hay.includes(textFilter)) return false;
    }
    if (qualityOnly && (!n.quality || (n.quality.findings.length === 0 && n.quality.in_budget))) {
      return false;
    }
    return true;
  });
  $('#notes-count').textContent = `${filtered.length} of ${state.notes.length}`;
  list.innerHTML = '';
  for (const n of filtered) {
    const div = document.createElement('div');
    div.className = 'cursor-pointer bg-white border rounded p-2 hover:bg-slate-100 text-sm';
    if (state.editingIndex === n.index) div.classList.add('ring-2', 'ring-blue-400');
    const flag = n.quality.findings.length > 0 || !n.quality.in_budget;
    const flagBadge = flag ?
      `<span class="inline-block bg-amber-200 text-amber-900 text-xs px-1 rounded ml-1">⚠</span>` : '';
    const excerpt = (n.body || '').replace(/<[^>]+>/g, '').slice(0, 100);
    div.innerHTML = `
      <div class="flex items-center gap-2 mb-1">
        <span class="mono text-xs text-slate-600">${n.ch}:${n.v}${n.suffix}</span>
        <span class="text-xs bg-slate-200 text-slate-700 px-1.5 rounded">${n.kind}</span>
        ${flagBadge}
        <span class="ml-auto text-xs text-slate-400">${n.quality.word_count}w</span>
      </div>
      <div class="text-slate-700 line-clamp-2">${excerpt}</div>
    `;
    div.onclick = () => editNote(n.index);
    list.appendChild(div);
  }
}

function editNote(index) {
  const n = state.notes.find(x => x.index === index);
  if (!n) return;
  state.editingIndex = index;
  state.editingDraft = JSON.parse(JSON.stringify(n));
  renderNotes();
  renderEditor();
}

async function newNote() {
  const ch = parseInt(prompt('Chapter:', '1') || '1');
  const v = parseInt(prompt('Verse:', '1') || '1');
  const kind = prompt('Kind (e.g. comm-rabbinic, lang-hebrew):', 'comm') || 'comm';
  let template = {label: 'Note.', body: '', attribution: {}};
  try {
    template = await api('/api/template/' + encodeURIComponent(kind));
  } catch (e) { /* fallback ok */ }
  state.editingIndex = null;
  state.editingDraft = {
    ch, v, suffix: '', anchor: '',
    kind, title: template.label.replace(/\.$/, ''),
    label: template.label, body: template.body,
    attribution: template.attribution,
    quality: {word_count: 0, budget: [0, 0], in_budget: true, findings: []},
  };
  renderEditor();
}

function renderEditor() {
  const d = state.editingDraft;
  if (!d) {
    $('#editor').innerHTML = '<div class="text-slate-400 text-sm">select a note to edit</div>';
    return;
  }
  const isNew = state.editingIndex === null;
  const kindOptions = state.kinds.map(k =>
    `<option value="${k.code}" ${k.code === d.kind ? 'selected' : ''}>${k.code}</option>`
  ).join('');
  const findingsHtml = (d.quality.findings || []).map(f =>
    `<li class="text-amber-700 text-xs">⚠ <span class="mono">${f.check}</span>: ${f.detail}</li>`
  ).join('');
  const inBudgetCol = d.quality.in_budget ? 'text-emerald-700' : 'text-amber-700';
  $('#editor').innerHTML = `
    <div class="text-xs text-slate-500">${isNew ? 'NEW NOTE' : 'index ' + state.editingIndex} · book ${state.currentBook}</div>
    <div class="grid grid-cols-3 gap-2">
      <label class="text-xs">ch <input type="number" id="f-ch" value="${d.ch}" class="w-full border rounded px-2 py-1 text-sm"/></label>
      <label class="text-xs">v <input type="number" id="f-v" value="${d.v}" class="w-full border rounded px-2 py-1 text-sm"/></label>
      <label class="text-xs">suffix <input id="f-suffix" value="${d.suffix||''}" class="w-full border rounded px-2 py-1 text-sm"/></label>
    </div>
    <label class="text-xs block">kind
      <select id="f-kind" class="w-full border rounded px-2 py-1 text-sm">${kindOptions}</select>
    </label>
    <label class="text-xs block">anchor
      <input id="f-anchor" value="${escapeAttr(d.anchor||'')}" class="w-full border rounded px-2 py-1 text-sm"/>
    </label>
    <label class="text-xs block">title
      <input id="f-title" value="${escapeAttr(d.title||'')}" class="w-full border rounded px-2 py-1 text-sm"/>
    </label>
    <label class="text-xs block">label
      <input id="f-label" value="${escapeAttr(d.label||'')}" class="w-full border rounded px-2 py-1 text-sm"/>
    </label>
    <label class="text-xs block">body (HTML)
      <textarea id="f-body" rows="8" class="w-full border rounded px-2 py-1 text-sm mono">${escapeText(d.body||'')}</textarea>
    </label>
    <div class="text-xs ${inBudgetCol}">words: ${d.quality.word_count} · kind budget: ${d.quality.budget[0]}–${d.quality.budget[1]}</div>
    <ul class="space-y-0.5">${findingsHtml}</ul>
    <details class="text-xs">
      <summary class="cursor-pointer">attribution (JSON)</summary>
      <textarea id="f-attribution" rows="6" class="w-full border rounded px-2 py-1 text-xs mono mt-1">${escapeText(JSON.stringify(d.attribution || {}, null, 2))}</textarea>
    </details>
    <div class="text-xs"><strong>preview:</strong></div>
    <div id="preview" class="preview text-sm bg-slate-50 border rounded p-2"></div>
    <div class="flex gap-2 pt-2 border-t">
      <button id="save-btn" class="bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-1 rounded">save</button>
      <button id="cancel-btn" class="bg-slate-200 hover:bg-slate-300 text-sm px-3 py-1 rounded">cancel</button>
      ${isNew ? '' : '<button id="delete-btn" class="ml-auto bg-rose-600 hover:bg-rose-700 text-white text-sm px-3 py-1 rounded">delete</button>'}
    </div>
  `;
  // Live preview
  const renderPreview = () => {
    $('#preview').innerHTML = $('#f-body').value;
  };
  $('#f-body').oninput = renderPreview;
  renderPreview();
  $('#save-btn').onclick = saveNote;
  $('#cancel-btn').onclick = () => { state.editingDraft = null; state.editingIndex = null; renderNotes(); renderEditor(); };
  if (!isNew) $('#delete-btn').onclick = deleteNote;
}

function escapeAttr(s) { return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;'); }
function escapeText(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;'); }

async function saveNote() {
  let attribution = {};
  try {
    attribution = JSON.parse($('#f-attribution').value || '{}');
  } catch (e) {
    return toast('attribution is invalid JSON: ' + e.message, true);
  }
  const payload = {
    index: state.editingIndex,
    ch: parseInt($('#f-ch').value),
    v: parseInt($('#f-v').value),
    suffix: $('#f-suffix').value,
    anchor: $('#f-anchor').value,
    kind: $('#f-kind').value,
    title: $('#f-title').value,
    label: $('#f-label').value,
    body: $('#f-body').value,
    attribution,
  };
  try {
    const r = await api('/api/notes/' + state.currentBook,
      { method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload) });
    toast('saved');
    await loadBook(state.currentBook);
    editNote(r.index);
  } catch (e) {
    toast('save failed: ' + e.message, true);
  }
}

async function deleteNote() {
  if (!confirm('Delete this note? A backup will be kept.')) return;
  try {
    await api('/api/notes/' + state.currentBook + '/' + state.editingIndex,
      { method: 'DELETE' });
    toast('deleted');
    state.editingDraft = null;
    state.editingIndex = null;
    await loadBook(state.currentBook);
  } catch (e) {
    toast('delete failed: ' + e.message, true);
  }
}

$('#book-search').oninput = renderBooks;
$('#kind-filter').oninput = renderNotes;
$('#text-filter').oninput = renderNotes;
$('#quality-only').onchange = renderNotes;
$('#add-btn').onclick = newNote;

init();
</script>
<!-- WELCOME_OVERLAY_JS -->
</body>
</html>
"""

# ψ.16 — substitute the polish-CSS marker at module load. We don't
# call `apply_design_system` because INDEX_HTML deliberately omits
# the HEADER_NAV_LINKS marker (linter exempts INDEX); a targeted
# replace is more honest about which substitution is happening.
INDEX_HTML = INDEX_HTML.replace(
    "<!-- BUYER_ARC_POLISH_CSS -->",
    BUYER_ARC_POLISH_CSS,
)
# W4.3 — inject the first-run welcome overlay. INDEX bypasses
# apply_design_system, so substitute the marker directly here.
INDEX_HTML = INDEX_HTML.replace(
    "<!-- WELCOME_OVERLAY_JS -->",
    WELCOME_OVERLAY_JS,
)
