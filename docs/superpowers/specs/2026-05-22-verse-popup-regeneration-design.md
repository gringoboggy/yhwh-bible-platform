# Verse-Popup Regeneration — Design Spec

**Date:** 2026-05-22 · **Status:** approved (design), pending implementation plan
**Toward:** the 2026-06-07 deadline / the builder demo north star (CLAUDE_PROJECT_RULES §1)
**Companion docs:** `dev/MATRIX_MAP.md` (data flow), `dev/CLAUDE_PROJECT_RULES.md` §9 (mental models), `project_epub_qa_followups` memory (the finding).

---

## 1. Problem

EPUB-QA (2026-05-22) found that **verse popups — the clickable verse number that opens a parallel-language `<aside class="vnote">` — exist for only 11 of 87 books = 9,689 / 40,406 verses (24%)**: Genesis → 2 Samuel (the first 10 canonical books, contiguous) + 1 Enoch. Books from 1 Kings onward — the entire NT, most deuterocanon, all Ethiopic-distinctive books — render verse numbers as bare `<span class="vn">` with no popup.

**Root cause:** an unfinished verse-popup-generation pass frozen into the recovered 2026-05-07 (v28a-50) base snapshot. The clean canonical-order stop after 2 Samuel is the fingerprint of an incremental job that didn't finish before the snapshot. It is **not** a build bug (the gap is in `epub_working/` itself; the per-edition build only prunes/styles existing popups) and **not** intentional.

**Two losses, not one:**
1. **The generator** — no script in the 351-commit git history ever emitted the `epub:type="noteref"` verse wrapper or the `vnote` aside. The original generator predates the re-init and was not recovered. A new one must be written.
2. **The parallel-text data** — only Genesis stubs remain for the parallel languages (`content/translations/wlc/gen.py`, `lxx-brenton-greek/gen.py`, etc.); there is **no Greek-NT source at all**. Only `kjv` (English, ~81 books) and the WEB base text (all 87) cover the full Bible.

**Demo impact: HIGH.** The wizard north star promises "verse popups in the configured languages." A builder who picks any NT-, Psalms-, or Prophets-heavy edition currently gets zero verse popups.

---

## 2. Goal

Regenerate verse popups with **one uniform scheme across every book that has parallel-text data** (the ~81 KJV-covered books; the 6 Ethiopic-only books without KJV are deferred — §3), so that every such verse is a clickable popup, closing the demo-critical gap — using the data on hand now, and structured so original-language depth layers in opportunistically later.

- **English (KJV) floor** for every KJV-covered book (~81).
- **Hebrew / Greek where data exists** — from the translations resolver (Genesis today; more as PD sources are supplied) **and preserved from the existing base** (harvest-and-merge, see §6).
- **Uniform** scheme across all 87 books (chosen over additive-only), which also corrects the observed Genesis 1:1/1:2 versification offset.

## 3. Scope

**In scope**
- A new re-runnable generator script (`scripts/generate_verse_popups.py`).
- Uniform regeneration of the `vnote` asides + verse-number wrappers across all 87 books in `epub_working/index_split_*.html`.
- KJV English floor; harvest-and-preserve existing Hebrew/Greek; merge resolver Hebrew/Greek where available.
- Versification alignment (correct the Gen 1:1/1:2 offset; skip — never fabricate — verses a source lacks).
- Idempotency + transactional safety; tests (TDD).

**Out of scope (deferred)**
- Acquiring full PD Hebrew (WLC), Greek-OT (LXX), and Greek-NT datasets — a separate ingestion track (the user-supplied-PD-source pattern, like Nave's/Easton's).
- Ge'ez verse popups for the ~6 Ethiopic-only books with no KJV (Meqabyan I–III, 2 Enoch, Jubilees, 4 Baruch) — belongs to the Ge'ez parallel-Bible track (τ.G).
- CSS / typography changes — `apply_style.py` already styles `.vnote` / `.vnote-hebrew` / `.vnote-greek`.

## 4. Architecture

A **base-preprocessing generator**, not a build-time pass:

- It edits `epub_working/index_split_*.html` **in place** (the recovered base), because that is where popups live and where every per-edition `build_one` reads from. The build's existing `_apply_popup_languages_and_translation` then prunes each edition's popups to its configured `popup_languages_default` — unchanged.
- It is **re-runnable and idempotent** (the `run_*_at_scale.py` driver pattern, CLAUDE_PROJECT_RULES §9 "corpus-growth").
- It **reuses existing infrastructure**: `scripts/inject.py`'s verse-region location logic (to find each verse's book/chapter/verse position in the base HTML) and `scripts.core.translations` (the resolver) for parallel-text lookup. No re-implementation.

Data flow:
```
epub_working/*.html  ──harvest──▶  {verse_id: existing he/gr}      (preserve)
content/translations/{kjv,wlc,lxx-brenton-greek,…}  ──resolver──▶  per-verse text
                              │
                              ▼
        generate_verse_popups.py  (wrap verse number + build/merge aside)
                              │
                              ▼
        epub_working/*.html  (uniformly regenerated; committed)
                              │
                    (unchanged) build_one ──prune to edition langs──▶ EPUB
```

## 5. The markup contract (must match exactly)

Per chapter, a hidden footnotes section holds one aside per verse; the inline verse number links to it.

Inline (in `<p class="verse-p">`):
```html
<a id="v-{bk}-{ch}-{vs}" epub:type="noteref" title="{Book} {ch}:{vs}"
   href="#vnote-{bk}-{ch}-{vs}"><span class="vn">{vs}</span></a>
```
Aside (in `<section class="verse-refs-section" epub:type="footnotes" hidden="">`):
```html
<aside class="vnote" id="vnote-{bk}-{ch}-{vs}" epub:type="footnote">
  <p><strong>{Book} {ch}:{vs}.</strong></p>
  <p class="vnote-text">{KJV verse text}</p>
  <p class="vnote-source-label">Hebrew (Masoretic / WLC)</p>      <!-- if present -->
  <p class="vnote-hebrew" dir="rtl" lang="he">…</p>               <!-- if present -->
  <p class="vnote-source-label">Greek (Septuagint / Brenton)</p>  <!-- if present -->
  <p class="vnote-greek" lang="grc">…</p>                          <!-- if present -->
  <p><a href="#v-{bk}-{ch}-{vs}" class="vnote-back" title="Back">↩</a></p>
</aside>
```
- `{bk}` is the book slug used in IDs (e.g. `gen`); the plan resolves the exact id-slug + the `Book` display title from `config.books_by_code()`.
- Unwrapped books currently have a bare `<span class="vn">{vs}</span>` and **no** `v-…` anchor — the generator adds the anchor, the wrapper, and the aside.
- When `vnote-text` has no source (a versification miss), emit the existing `vnote-empty` placeholder rather than fabricate text.

## 6. Uniform regeneration + preservation (the safety design)

Uniform regen's risk is dropping Hebrew/Greek on the existing 11 books whose original source data is partly lost. Mitigation — **harvest then merge**:

1. **Harvest pass (read-only):** parse every existing `<aside class="vnote">` in the base → build `{vnote-id: (hebrew_html, greek_html)}`.
2. **Regenerate pass:** for every verse in all 87 books, rebuild the wrapper + aside uniformly. For each language paragraph, prefer the **resolver** value; if the resolver has none but the **harvest map** does, re-emit the harvested HTML. Result: no original-language content is ever lost, while structure, KJV `vnote-text`, verse-wrapping of missing books, and versification are all rebuilt uniformly.
3. **Versification:** each aside's `vnote-text` is sourced from the KJV verse whose number matches the aside's verse — correcting the Gen 1:1/1:2 offset. The off-by-one's mechanism is investigated during implementation (likely a verse-indexing bug in the lost generator); TDD pins the corrected alignment.

## 7. Idempotency & transactional safety

- Re-running produces byte-identical output (already-correct asides are rewritten identically; verse-wrapping detects the existing wrapper and is a no-op).
- All writes go through `notes_io.atomic_write` + `notes_io.ensure_backup` (CLAUDE_PROJECT_RULES §7.1).
- `epub_working/` changes are committed (the base is tracked since the 2026-05-21 recovery).

## 8. Build / verify compatibility (must hold)

- The build's `_apply_popup_languages_and_translation` / `_replace_verse_popup_translation` consume the contract in §5 **unchanged**.
- `ebible verify` → **errors=0** (paired refs/targets), `trace_matrix` 0 unresolved, build smoke → valid EPUB, ruff + `lint_rules` clean. These are the regression gates.

## 9. Testing (TDD)

- **Unit:** wrap one bare verse number (idempotent on re-run); build one aside from resolver data; harvest-and-merge preserves he/gr when the resolver is empty; versification-skip emits `vnote-empty` (no fabrication).
- **Integration:** run on one currently-unwrapped book (e.g. `1ki`) → its wrapped-% goes 0 → ~100%; `ebible verify` errors=0; build smoke valid.
- **Regression pins:** the existing 11 books retain their Hebrew/Greek after uniform regen; the Gen 1:1/1:2 text aligns to the correct verse.
- **Coverage pin:** post-generation wrapped-% across KJV-covered books ≥ a stated floor (≈100%).

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Uniform regen drops existing he/gr | Harvest-and-merge (§6); regression pin |
| Re-introducing a versification offset | Source by matching verse number; TDD alignment pin |
| Large, hard-to-review base diff | Per-book runs; the `ebible verify` + build-smoke gates catch structural breakage; review per book |
| `vnote-text` source ambiguity (WEB vs KJV) | KJV is the floor; if a book lacks KJV it is deferred (no popup), not faked |

## 11. Success criteria

- Every KJV-covered book: ~100% of verses are clickable popups (wrapped-% pin).
- Existing 11 books keep their Hebrew/Greek (regression pin).
- `ebible verify` errors=0; build smoke → valid EPUB; ruff + `lint_rules` clean.
- Demo: tap any verse in any KJV-covered book in any edition → a popup in that edition's configured languages.
- The 6 Ethiopic-only books remain without popups (documented, deferred to τ.G).
