# Note-Cascade Redundancy — Deep-Audit Findings (WS2)

**Date:** 2026-06-24
**Scope:** the verse→category→source→note cascade emitted by `_emit_cascade_sections`
(`scripts/build_edition.py:3831`). Findings only — no `scripts/` or `content/` edits.
**Audience:** the WIN (implementation) lane.
**Goal (user's words):** *"cascade feel without repetitions."* One heading per category,
one source byline per source group, one symbol per category, cross-references
de-duplicated.

**Verification basis.** Every code site below was read in the live tree; every corpus
count was re-measured against the **build-consumed** source only (top-level
`content/notes/*.py`, the files `notes_dir.glob('*.py')` loads — `build_edition.py:136`).
The recon's "source-file" magnitude figures were inflated by recursive `grep` descending
into `content/notes/.backups/*.py.bak` (excluded by the build, `build_standalone.py:156`);
the corrected live figures are used throughout and are flagged where they differ.

---

## 1. Current cascade shape (as built today)

`_emit_cascade_sections(rows, cat_meta)` (`build_edition.py:3831-3872`) re-groups the
already category-rank-ordered leaf rows into a 3-level tree per verse:

```
<section class="vn-group note-cat-{cat}">                      ← CATEGORY level (once/category)
  <p class="vn-cat-head">¶ <span class="vn-cat-sym" aria-hidden="true">{glyph}</span> {label}</p>
  <div class="vn-source">                                     ← SOURCE level (once/source bucket)
    <p class="vn-source-byline">◦ {source_display}</p>        ← byline (suppressible)
    <div class="vn-item note-{kind}">• {leaf row body…}</div>  ← NOTE leaf (once/note, repeats ×N)
    …
  </div>
  …
</section>
```

Grouping: `cats[cat][source_key] → [rows]` (`build_edition.py:3841-3844`). Categories in
first-appearance order (rows pre-sorted by `_POPUP_CATEGORY_RANK`); sources in
first-appearance order; notes in document order. The header glyph comes from `cat_meta`
(`build_edition.py:3848`), built at `build_edition.py:3966-3973` with the Cardo-safe eink
substitution applied for eink targets. The header span is `aria-hidden="true"` and is
**not** a hyperlink (`build_edition.py:3854`).

Each leaf `rr['row']` is produced by `_badge_aside_inner_to_row`
(`build_edition.py:2812-2825`), which drops only the per-note back-link `↩` (via
`_NOTE_BACK_RE`, count=1) and **keeps everything else** — including the baked per-note
`<a class="note-sym">` glyph-link and the baked `<span class="note-label">` (docstring,
`build_edition.py:2815-2816`). The leaf body is emitted verbatim at
`build_edition.py:3868-3869`.

Two layouts share this emitter:

- **Popup (inline footnote):** `_unit_inner` → `_emit_cascade_sections`
  (`build_edition.py:4208`), wrapped in `<aside epub:type="footnote">` by
  `_study_glossary_footnote` (`build_edition.py:3734-3739`).
- **Backmatter glossary:** `_emit_backmatter_glossary_inner`
  (`build_edition.py:3743-3821`) → `_study_glossary_category_body`
  (`build_edition.py:3711-3718`) → `_emit_cascade_sections` when `s2_group`.

The whole cascade is **gated** behind `note_group_by_category` / `s2_group`
(`_study_glossary_category_body:3712-3713`). The flat / non-grouped path
(`build_edition.py:3714-3718`) does NOT call `_emit_cascade_sections` — important for the
fix sites below.

**Pre-cascade row pipeline (S1, badge mode only — `apply_badge_markers`, gate
`marker_style=='badge'` at `build_edition.py:7863`):**
- `_strip_redundant_note_label` (`build_edition.py:2930-2955`, called `4141`) — drops the
  leaf `note-label` span when it equals the kind default / body self-attributes / kind is
  `dict-*`.
- `_strip_redundant_body_boilerplate` (`build_edition.py:2967-2975`, called `4144`, gated
  by `note_attribution_dedup`/`s1_dedup`) — strips the leading `<strong>…</strong>` body
  lead-in, but **only** for `kind.startswith("dict-")` and `kind.startswith("topic-")`.
- `_eink_safe_note_sym` (`build_edition.py:2836-2841`, called `4119`) — Cardo-substitutes
  the per-note `note-sym` glyph **in place** (does not remove it).
- `seen_rows` whitespace-normalized dedup (`build_edition.py:4120-4123`) — drops
  byte-identical duplicate rendered rows in badge mode only.

CSS: `_NOTE_CASCADE_CSS` (`build_edition.py:2482-2497`), appended by
`apply_note_cascade_css` (`build_edition.py:2500-2506`) only when grouping is on. Per-hue
rules at `build_edition.py:2201-2205` color the **leaf** `.vn-item .note-sym` with the
**same** per-category hue + `font-weight:700` as the header sym — so a repeated leaf glyph
is user-visible, not hidden.

---

## 2. Confirmed redundancy classes

Three confirmed classes. The adversarial pass returned **4 partial-with-corrections, 0
refuted**; two of those claims (repeated-xref, restated-heading) describe the **same**
body-lead-in surface from different angles and are consolidated into Class 2 here. The
"same xref target-set across different verses" candidate was **refuted as a defect**
(intentional, `_XVERSE_DEDUP_EXCLUDE`) and is excluded from the fix; it is recorded under
Class 2 as out-of-scope.

### Class 1 — Repeated category SYMBOL (per-note `note-sym` vs header `vn-cat-sym`)

**Verdict:** REAL (partial → confirmed with one a11y qualification). **Severity: HIGH.**

The category glyph renders **header(1) + leaf(N)** times within one verse-category. The
header emits it once at `vn-cat-sym` (`build_edition.py:3854`); each leaf row carries a
baked `<a class="note-sym" href="legend.xhtml#legend-{cat}" title="…">{glyph}</a>` that
survives into the cascade. Both surfaces render in the **identical per-category hue**
(`build_edition.py:2201-2205`), so the repeat is user-visible.

| Site | Evidence | Severity |
|---|---|---|
| `scripts/inject.py:252` | Bakes the per-note glyph: `f' <a class="note-sym" href="legend.xhtml#legend-{cat}" title="{safe_cat_label}">{glyph}</a>'` — once for EVERY note. Source of the repeat. | high |
| `scripts/resync_marker_glyphs.py:188` | Byte-identical re-bake: `+ f' <a class="note-sym" href="legend.xhtml#legend-{cat}" title="{label}">{glyph}</a>'`. Lockstep sibling of inject.py:252 — any *baked-corpus* fix must reconcile both; a *downstream* (cascade) fix leaves both untouched. | high |
| `scripts/build_edition.py:3868-3869` | Leaf emit `for rr in src_rows: out.append(f"      {rr['row']}\n")` writes `rr['row']` verbatim, still carrying the baked `note-sym`. **This is where N redundant leaf syms enter the cascade — the fix site.** | high |
| `scripts/build_edition.py:2204-2205` | CSS gives the leaf `.note-sym` the same `color:{hue}` + `font-weight:700` as the header sym → repeat is visible. | medium |
| `scripts/build_edition.py:3854` | Header `vn-cat-sym`, once per category group — the **canonical single source** after the fix. | low |
| `scripts/build_edition.py:2836-2841` (called `4119`) | `_eink_safe_note_sym` — current mitigation only rewrites the glyph **in place**; does not remove the repeat. QA cluster F supersedes it with a DROP. | medium |

**Corpus (live, verified):** 91,555 baked `note-sym` links across `epub_working/`. By
legend target in the flat HTML: topic 48,097, lang 30,709, xref 6,160, hist 3,779, comm
2,682, text 128. Single-file proof: `epub_working/index_split_003.html` carries 683
`legend-lang` (⌘) + 1,256 `legend-topic` (✦) leaf repeats of a glyph the header shows
once. One downstream strip collapses **all** of these — no per-kind work.

**Fix-the-class emitter location:** `_emit_cascade_sections`, leaf emit at
`build_edition.py:3868-3869` (grouped path only).

**Adversarial corrections folded in:**
1. The header `vn-cat-sym` is `<span aria-hidden="true">` with **no `href`** — it is NOT
   a hyperlink and is screen-reader-hidden. Dropping the leaf `note-sym` therefore drops
   the only legend hyperlink + `title` tooltip + a11y-readable category glyph in the
   cascade. **Category identity is still conveyed by the header's adjacent TEXT `label`**
   (`build_edition.py:3855`), so the drop is acceptable, but it is a small information
   loss, **not strictly lossless** — state it honestly. (Mitigating context: the cascade
   renders inside a Kobo footnote popup, where QA cluster E documents that bare `<a>` does
   not navigate — the leaf legend link is largely non-functional on-device already.)
2. **Do the strip in `_emit_cascade_sections` (3868-3869), NOT in
   `_badge_aside_inner_to_row` (2824).** The latter is shared with the FLAT/non-grouped
   path, where the leaf sym is the **only** symbol; stripping there would leave the flat
   layout with no symbol at all. The grouped emitter is the only safe site.
3. eink-safe call is at `build_edition.py:4119` (not just 4119-only ambiguity; single
   call).
4. After the fix, `_eink_safe_note_sym` becomes a **no-op for the grouped path** (no
   `note-sym` left to rewrite) and can be retired there; keep it for any non-grouped path
   that still bakes a leaf sym.

### Class 2 — Repeated source/heading BYLINE in the leaf body lead-in

**Verdict:** REAL (partial → confirmed; magnitude corrected). Consolidates the
adversarial "repeated-byline", "repeated-xref", and "restated-heading" claims, which all
describe the **same** baked `<strong>…</strong>` body lead-in. **Severity: HIGH (xref) /
MEDIUM (text-witness).**

The cascade already states each identity once structurally: category label once at
`vn-cat-head` (`build_edition.py:3853-3856`), source attribution once at
`vn-source-byline` (`build_edition.py:3864-3867`, suppressed when every row in the bucket
self-attributes, `build_edition.py:3863`). The redundancy is the **second surface**: every
note body OPENS with a baked `<strong>…</strong>` lead-in that **restates** that same
identity on every leaf row.

- `dict-*` and `topic-*` lead-ins are **already stripped** by
  `_strip_redundant_body_boilerplate` (`build_edition.py:2967-2975`, regexes 2963-2964) —
  the fix-the-class precedent.
- `xref-citation` (`<strong>Cross-references.</strong>`) and `text-witness`
  (`<strong>Manuscript witness.</strong>`) lead-ins are **NOT stripped** — the function has
  no branch for them (`grep` confirms no `_XREF_BODY_BOILER_RE`; the only "Cross-references"
  in the script is the comment at `build_edition.py:2845`).

The xref case is the highest-severity site because the lead-in
`<strong>Cross-references.</strong>` is **verbatim identical** to the xref category label
`"Cross-references"` (`content/categories.yaml:27`) that `vn-cat-head` already renders. On
the 778 verses carrying ≥2 distinct xref notes the category word prints 3× (header + 2
bodies). text-witness is lower (it restates the kind within the "Textual/Critical"
category, not an exact category-head match).

| Site | Evidence | Severity |
|---|---|---|
| `scripts/build_edition.py:2967-2975` | `_strip_redundant_body_boilerplate` matches only `kind.startswith("dict-")` / `("topic-")`. No xref/text-witness branch. **The mitigation gap — fix site.** | high |
| `content/notes/gen.py` (xref-citation body) | `body = '<strong>Cross-references.</strong> <a …>Jhn 1:1</a> · <a …>Heb 11:3</a> · …'`, attribution `'Treasury of Scripture Knowledge (1830s)…'`. Lead-in == category head; NOT stripped. **Live count: 6,132** xref-citation lead-ins (all kind `xref-citation`; 0 `parallel` carry it). | high |
| `content/notes/gen.py` (text-witness body) | `body = '<strong>Manuscript witness.</strong> …'`, attribution `'Frederic G. Kenyon, *Our Bible and the Ancient Manuscripts*…'`. NOT stripped. **Live count: 114.** | medium |
| `content/notes/zec.py`, `gen.py` (dict-easton) | `'<strong>Dictionary (Easton's).</strong> <strong>BARACHIAS</strong>…'`. ALREADY stripped via `_DICT_BODY_BOILER_RE`. **Live count: 3,778.** Listed as fix-the-class precedent. NB: dict-easton's category is `hist` (`kinds.yaml`), so this lead-in restates the **source byline** (Easton's…), not the category head. | low |
| `content/notes/mat.py`, `gen.py` (topic-nave/topic-torrey) | `'<strong>Topics.</strong> This verse appears under: …'`. ALREADY stripped via `_TOPIC_BODY_BOILER_RE`. **Live count: 48,099.** Precedent. | low |
| `scripts/inject.py:248-256` (`build_aside`) | Bakes `body_html` verbatim into the leaf row, carrying the lead-in. The emitter of the baked surface. | high |
| `scripts/build_edition.py:3864-3867` | `vn-source-byline`, once per source bucket — the **canonical** byline; correct, NOT the redundancy. Its existence is what makes the in-body lead-in duplicative. | low |
| `scripts/build_edition.py:4184` + `2895-2902` (comm-ethiopian) | Self-attributing `<strong>Father</strong> <em>Work</em> <small>(date)</small>` triad sets `suppress_byline=True` → byline correctly suppressed for that bucket. **Not a defect** — third byline surface, correctly handled. | low |

**Out-of-scope (refuted as a defect):** the SAME xref target-set across DIFFERENT verses
(e.g. `ch-b60-c6` recurs across ~19 verses) is intentional —
`_XVERSE_DEDUP_EXCLUDE = {"xref","topic"}` (`build_edition.py:2848`); cross-references are
per-verse by design. Do NOT touch.

**Adjacent (partly mitigated, in-scope only as authoring cleanup):** byte-identical
**same-verse** duplicate xref tuples — e.g. `content/notes/gen.py:16-26` (suffix "") and
`gen.py:49-59` (suffix "c") are two xref-citation tuples at (1,1) with identical
`body_html`/`label`. Live: 1,037 extra copies across 53 importable files; 778 verses carry
≥2 distinct xref notes. These ARE collapsed by `seen_rows`
(`build_edition.py:4120-4123`) in **badge** mode, but the "numbers" marker style leaves
them per-note ("byte-identical to the historical build", `build_edition.py:7859-7860`), so
they double-render there. To clean the corpus itself (and fix numbers mode), de-duplicate
the authored tuples in the **top-level** `content/notes/*.py` (not `.backups`). This is an
authoring fix, separate from the cascade strip.

**Fix-the-class emitter location:** `_strip_redundant_body_boilerplate`
(`build_edition.py:2967-2975`), extended with an xref + text-witness branch.

**Adversarial corrections folded in:**
1. **Counts corrected** (recon used recursive grep into `.backups`):
   `<strong>Cross-references.</strong>` = **6,132** (not 7,435);
   `<strong>Manuscript witness.</strong>` = **114** (not 185);
   `<strong>Topics.</strong>` = **48,099** (not 81,529, already handled);
   `<strong>Dictionary (Easton's).</strong>` = **3,778** (not 8,222, already handled).
   Re-run as `grep -h … content/notes/*.py` (top-level only).
2. **Tighten the xref guard to `kind == "xref-citation"`**, not `startswith("xref-")` /
   `"parallel"`. In the live corpus only `xref-citation` carries the lead-in (0 `parallel`,
   0 other `xref-*`). A broad `startswith` is harmless (anchored count=1 no-ops when absent)
   but would silently strip a future hand-authored `parallel` note that legitimately opens
   with that phrase. dict-/topic- use `startswith` only because those families share the
   boiler; xref does not.

### Class 3 — Residual restated naming LABEL (leaf `note-label`) — already mitigated

**Verdict:** REAL but largely RESOLVED. **Severity: LOW.** Included for completeness so the
WIN lane does not re-fix it.

`inject.py:253` bakes `<span class="note-label">{safe_label}</span>` per note (e.g.
`"Cite."`, `"Hebrew."`, `"Topic."`), restating the kind's default label.
`_strip_redundant_note_label` (`build_edition.py:2930-2955`, called `4141`) already drops it
when it equals the kind default (`_normalize_label_text`, 2885-2892, strips trailing dot +
casefolds, so `"Cite."` == `"Cite"` from `kinds.yaml`), or the body self-attributes, or
kind is `dict-*`. QA reports 85,936/91,733 labels suppressible. **No new fix needed** — the
xref `"Cite."` leaf label is already suppressed; the only residual is labels that genuinely
differ from the kind default, which legitimately add information.

---

## 3. The CANONICAL cascade design — "cascade feel without repetitions"

**One rule per level, each datum stated exactly once:**

| Level | Statement | Site (single canonical source) |
|---|---|---|
| CATEGORY | category **symbol** once + category **label** once | `vn-cat-head` → `vn-cat-sym` + `{label}` (`build_edition.py:3854-3855`) |
| SOURCE | source **byline / attribution** once per source group | `vn-source-byline` (`build_edition.py:3866`) |
| NOTE leaf | ONLY the note's **distinguishing payload** (headword / term list / xref links / MS prose) — no symbol, no category word, no source restatement | `.vn-item` body (`build_edition.py:3869`) |
| Cross-refs | each verse's target links once; same-verse byte-identical xref tuples collapsed | leaf body; `seen_rows` (`build_edition.py:4120-4123`) + authoring de-dup |

### Before / after markup

**A) xref note — BEFORE (today):**

```html
<section class="vn-group note-cat-xref">
  <p class="vn-cat-head">¶ <span class="vn-cat-sym" aria-hidden="true">‖</span> Cross-references</p>
  <div class="vn-source">
    <p class="vn-source-byline">◦ Treasury of Scripture Knowledge (1830s).</p>
    <div class="vn-item note-xref-citation">• <a class="note-sym" href="legend.xhtml#legend-xref" title="Cross-references">‖</a>
        <strong>Cross-references.</strong> <a href="…">Jhn 1:1</a> · <a href="…">Heb 11:3</a> · <a href="…">Isa 45:18</a>.</div>
    <div class="vn-item note-xref-citation">• <a class="note-sym" href="legend.xhtml#legend-xref" title="Cross-references">‖</a>
        <strong>Cross-references.</strong> <a href="…">Psa 33:6</a> · <a href="…">Col 1:16</a>.</div>
  </div>
</section>
```

The category symbol `‖` appears 3× (header + 2 leaves); the word "Cross-references" appears
3× (header + 2 leaf lead-ins).

**A) xref note — AFTER (canonical):**

```html
<section class="vn-group note-cat-xref">
  <p class="vn-cat-head">¶ <span class="vn-cat-sym" aria-hidden="true">‖</span> Cross-references</p>
  <div class="vn-source">
    <p class="vn-source-byline">◦ Treasury of Scripture Knowledge (1830s).</p>
    <div class="vn-item note-xref-citation">• <a href="…">Jhn 1:1</a> · <a href="…">Heb 11:3</a> · <a href="…">Isa 45:18</a>.</div>
    <div class="vn-item note-xref-citation">• <a href="…">Psa 33:6</a> · <a href="…">Col 1:16</a>.</div>
  </div>
</section>
```

Symbol once (header), category word once (header), byline once, each leaf is bare target
links. (Class 1 dropped the leaf `note-sym`; Class 2 dropped the leaf
`<strong>Cross-references.</strong>`; Class 3 already dropped the `"Cite."` label.)

**B) dict / lang note (mixed sources in one category) — AFTER (canonical):**

```html
<section class="vn-group note-cat-hist">
  <p class="vn-cat-head">¶ <span class="vn-cat-sym" aria-hidden="true">H</span> Historical / Cultural</p>
  <div class="vn-source">
    <p class="vn-source-byline">◦ Easton's Illustrated Bible Dictionary, M. G. Easton (1897).</p>
    <div class="vn-item note-dict-easton">• <strong>CREATION</strong> — the act of God in bringing the universe into being…</div>
    <div class="vn-item note-dict-easton">• <strong>BARACHIAS</strong> — the father of Zacharias…</div>
  </div>
</section>
```

Symbol `H` once; category label once; Easton's byline once for the whole bucket; each leaf
keeps only its real headword + definition. (eink glyph `H` shown — see §5.)

---

## 4. Explicit fold-in of device-QA clusters C / F

**Cluster F (`dev/audit/kobo-device-qa-2026-06-23.md:173-175`) — verbatim:**
> *"F — category symbol still redundant. The grouped S2 cascade shows the category symbol
> in the HEADER (`vn-cat-head`→`vn-cat-sym`) AND on every note row (`note-sym`). DROP the
> per-note `note-sym` in `_emit_cascade_sections` (header conveys it). ⚠ SUPERSEDES this
> session's B-1c note-sym substitution."*

This is **Class 1**. The directive is a **DROP**, not a substitution. It **supersedes**
the B-1c mitigation `_eink_safe_note_sym` (`build_edition.py:2836-2841`, called `4119`):
that helper Cardo-substitutes the leaf glyph in place but leaves the repeat. After the
DROP in `_emit_cascade_sections` (`build_edition.py:3868-3869`), there is no leaf
`note-sym` in the grouped cascade, so `_eink_safe_note_sym` is a no-op there and can be
retired for the grouped path. The path is `dev/audit/…` (the recon's
`docs/superpowers/…` citation was wrong; filename + lines are correct).

**Cluster C** — the device-QA Cardo-substitution / eink-glyph cluster (the glyph layer the
B-1c work and `_eink_safe_note_sym` belong to): once Class 1 drops the leaf `note-sym`,
the only category glyph left in the cascade is the **header** `vn-cat-sym`, which is
already routed through the Cardo-safe substitution via `cat_meta`
(`build_edition.py:3966-3973`, `_eink_category_badge_glyph` when `eink_target`). So the
eink-safe glyph concern (C) collapses to the single header surface — no per-leaf glyph
substitution to maintain in the grouped path. The two clusters fold together: **F removes
the redundant surface; C's substitution then applies to the one surviving header glyph
only.**

**Net:** B-1c's per-note substitution is superseded; the header (Cardo-safe via `cat_meta`)
becomes the sole, already-eink-safe glyph surface.

---

## 5. Byte-stability note

- **Class 2 (body-lead-in strip)** runs inside `apply_badge_markers`
  (`marker_style=='badge'`, `build_edition.py:7863`) and the new branch is gated by the
  same `note_attribution_dedup` / `s1_dedup` flag as the existing dict-/topic- strip
  (`build_edition.py:4144`). **Flag OFF → byte-identical to baseline** (no new bytes;
  gate this to the eink build the same way dict-/topic- already are). Anchored count=1
  regex (`<strong>Cross-references\.</strong>\s*`, `<strong>Manuscript witness\.</strong>\s*`)
  — lossless: the xref `<a>` target links and the MS prose that follow survive, exactly as
  the dict headword / topic term-list survive today.

- **Class 1 (leaf `note-sym` drop)** is a **deliberate re-baseline**, not a byte-stable
  change. It alters the rendered grouped-cascade bytes for every verse-category by design
  (that IS the fix). Do it **downstream in `_emit_cascade_sections`** so the baked corpus
  and both bake paths (`inject.py:252`, `resync_marker_glyphs.py:188`) stay byte-identical
  — the golden corpus is undisturbed; only the cascade render changes. Gate under
  `note_group_by_category` / `s2_group` so the **flat / non-grouped** path (where the leaf
  sym is the only sym) is byte-unchanged. This is the same re-baseline discipline QA cluster
  F assumes ("golden re-baseline" language elsewhere in the doc, e.g. line 167). Update the
  golden fixtures for the grouped path in the same commit.

- **A11y honesty:** the Class 1 drop removes the leaf legend hyperlink + `title` + the only
  a11y-visible category glyph (header is `aria-hidden`); category identity persists via the
  header text label. Acceptable for the Kobo-popup target (bare `<a>` non-navigating, QA
  cluster E), but record it as a small, intentional information drop — not "lossless."

---

## Summary for WIN lane

- **3 confirmed redundancy classes:** (1) repeated category **symbol** — HIGH, drop leaf
  `note-sym` in `_emit_cascade_sections:3868-3869`; (2) repeated source/heading **byline**
  lead-in — HIGH(xref)/MEDIUM(text-witness), extend `_strip_redundant_body_boilerplate:2967`
  with `kind == "xref-citation"` and `text-witness` branches; (3) restated leaf **label** —
  already resolved, no action.
- **Live magnitudes (build-consumed):** 6,132 xref + 114 text-witness lead-ins to strip;
  3,778 dict / 48,099 topic already handled; 91,555 baked leaf `note-sym` collapsed by one
  downstream strip.
- **Do NOT touch:** cross-verse xref recurrence (`_XVERSE_DEDUP_EXCLUDE`, by design); the
  flat/non-grouped path; the comm-ethiopian self-attribution byline (correctly suppressed).
- Fold in QA clusters F + C: DROP supersedes B-1c `_eink_safe_note_sym`; the surviving
  header glyph is already Cardo-safe via `cat_meta`.
