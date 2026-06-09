"""γ.2 — /greek console template (Greek interlinear UI).

Direct mirror of `scripts/templates/hebrew.py`. Diffs:
    - Greek text reads LTR (no `direction: rtl` on the lemma).
    - Greek lexicon doesn't have a pron field — render conditional.
    - URL/endpoint swap: /api/hebrew → /api/greek.

Composes the same ζ foundation as γ.1 (theme tokens + dark mode +
icons + toasts + cmd palette). Pattern's now proven across two
languages; γ.3+ will follow the same shape for further detector
surfaces.
"""

from scripts.templates._design import (  # noqa: E402
    BUYER_ARC_POLISH_CSS,
    HEADER_NAV_LINKS,
    apply_design_system,
)

__all__ = ["GREEK_HTML", "HEADER_NAV_LINKS", "BUYER_ARC_POLISH_CSS"]

GREEK_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>YHWH Ya' Way · Greek Interlinear</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  /* γ.2: Greek polytonic — LTR direction (the default), larger size
     for legibility. No RTL flip vs Hebrew. */
  .greek-lemma {
    font-size: 2.25rem;
    line-height: 1.2;
  }
</style>
<!-- THEME_TOKENS_CSS -->
<!-- DARK_MODE_JS -->
<!-- THEME_ICONS_JS -->
<!-- THEME_TOAST_JS -->
<!-- THEME_CMD_PALETTE_JS -->
<!-- BUYER_ARC_POLISH_CSS -->
</head>
<body class="theme-bg-page theme-text">

<header class="border-b theme-bg-surface theme-border">
  <div class="max-w-5xl mx-auto px-4 py-3 flex items-baseline gap-4 text-sm flex-wrap">
    <strong class="text-base">YHWH Ya' Way</strong>
    <!-- HEADER_NAV_LINKS -->
    <span id="corpus-progress" class="ml-auto text-xs theme-text-muted" title="corpus depth toward the 35,000-note Ethiopian Tewahedo target">·· loading ··</span>
  </div>
</header>

<main class="max-w-3xl mx-auto px-4 py-6">
  <h1 class="theme-text-2xl theme-weight-semibold mb-2">Greek Interlinear</h1>
  <p class="theme-text-sm theme-text-muted mb-6">
    Look up a Strong's Greek number — covers all 5,523 entries.
    Type <code class="theme-font-mono">G3056</code> for
    <span class="theme-font-mono">λόγος</span> ("word", "reason"),
    or <code class="theme-font-mono">G26</code> for
    <span class="theme-font-mono">ἀγάπη</span> ("love").
  </p>

  <form id="lookup-form" class="flex gap-2 mb-6" autocomplete="off">
    <input
      id="num-input"
      type="text"
      inputmode="text"
      placeholder="G1 or 1 or G0001 …"
      class="flex-1 px-3 py-2 rounded theme-bg-surface theme-text theme-border border"
      aria-label="Strong's Greek number">
    <button
      type="submit"
      class="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 theme-weight-medium">Look up</button>
  </form>

  <div id="result" aria-live="polite"></div>

  <p class="theme-text-xs theme-text-muted mt-8">
    Source: Strong's <em>A Concise Dictionary of the Words in the Greek Testament</em>
    (James Strong, 1894). Public domain.
  </p>
</main>

<script>
function renderEntry(data) {
  const root = document.getElementById('result');
  // γ.2 — render via DOM nodes (not innerHTML interpolation) so any
  // exotic-codepoint Greek polytonic content stays XSS-safe by
  // construction.
  root.innerHTML = '';

  const card = document.createElement('section');
  card.className = 'theme-bg-surface theme-border border rounded-lg p-6 space-y-4';

  // Header: number + lemma + transliteration (+ pron if present)
  const head = document.createElement('div');
  head.className = 'flex items-baseline gap-4 flex-wrap';

  const num = document.createElement('span');
  num.className = 'theme-text-sm theme-font-mono theme-text-muted';
  num.textContent = data.number;
  head.appendChild(num);

  const lemma = document.createElement('span');
  lemma.className = 'greek-lemma theme-weight-bold';
  lemma.textContent = data.lemma;
  head.appendChild(lemma);

  const xlit = document.createElement('span');
  xlit.className = 'theme-text-lg theme-font-mono theme-text-muted';
  xlit.textContent = data.xlit;
  head.appendChild(xlit);

  // Greek lexicon entries don't carry a pron field; only render
  // the slot if the data has one (γ.1 always renders; γ.2
  // conditional).
  if (data.pron) {
    const pron = document.createElement('span');
    pron.className = 'theme-text-sm theme-text-muted';
    pron.textContent = '/' + data.pron + '/';
    head.appendChild(pron);
  }

  card.appendChild(head);

  // Sections: derivation, definition, kjv_def
  function addSection(label, value) {
    if (!value) return;
    const wrap = document.createElement('div');
    const lbl = document.createElement('div');
    lbl.className = 'theme-text-xs theme-weight-semibold theme-text-muted mb-1 uppercase tracking-wide';
    lbl.textContent = label;
    wrap.appendChild(lbl);
    const val = document.createElement('div');
    val.className = 'theme-text-base';
    val.textContent = value;
    wrap.appendChild(val);
    card.appendChild(wrap);
  }
  addSection('Derivation', data.derivation);
  addSection('Definition', data.definition);
  addSection('KJV Usage', data.kjv_def);

  // Attribution footer
  const attr = document.createElement('div');
  attr.className = 'theme-text-xs theme-text-muted pt-3 border-t theme-border';
  attr.textContent = data.attribution;
  card.appendChild(attr);

  root.appendChild(card);
}

function renderEmpty(message) {
  const root = document.getElementById('result');
  root.innerHTML = '';
  const empty = document.createElement('div');
  empty.className = 'theme-bg-surface theme-border border rounded-lg p-6 text-center theme-text-muted';
  empty.textContent = message;
  root.appendChild(empty);
}

async function lookup(rawNum) {
  const num = rawNum.trim();
  if (!num) {
    document.getElementById('result').innerHTML = '';
    return;
  }
  try {
    const r = await fetch('/api/greek/' + encodeURIComponent(num));
    const data = await r.json();
    if (data.status === 'ok') {
      renderEntry(data);
    } else {
      renderEmpty(data.message || ('error: ' + (data.code || r.status)));
      if (window.ebibleToast && r.status >= 500) {
        window.ebibleToast(data.message || 'Lookup failed.', 'error');
      }
    }
  } catch (e) {
    renderEmpty('Network error: ' + e.message);
    if (window.ebibleToast) {
      window.ebibleToast('Network error: ' + e.message, 'error');
    }
  }
}

document.getElementById('lookup-form').addEventListener('submit', function (ev) {
  ev.preventDefault();
  lookup(document.getElementById('num-input').value);
});

// Auto-lookup on URL hash (e.g. /greek#G3056) for shareable links.
if (window.location.hash) {
  const num = decodeURIComponent(window.location.hash.slice(1));
  document.getElementById('num-input').value = num;
  lookup(num);
}

// Corpus-progress widget (mirrors the pattern in every other console).
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
</script>

</body>
</html>
"""


# γ.2: design-system substitution (cross-link nav + theme markers).
GREEK_HTML = apply_design_system(GREEK_HTML, "/greek")
