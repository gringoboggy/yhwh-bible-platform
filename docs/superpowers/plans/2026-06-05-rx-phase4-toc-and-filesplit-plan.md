# RX Phase 4 — Kobo structural: compact TOC + build-time file-splitter

**Status:** IN PROGRESS 2026-06-05 — Phase 4b (build-time file-splitter `apply_file_split`) SHIPPED + epubcheck 0/0/0/0 (ethiopian-tewahedo split into 227 pieces, max 472 KB from 5 MB; 0 broken links; default ON). Phase 4a (Kobo-safe in-content TOC: unwrap `<details>` + drop `.toc-chapters` flexbox) + the program-end gate (all editions/standalones epubcheck + byte-stability) remain.
**Date:** 2026-06-05 · **Arc:** EPUB Reading-Experience Overhaul (the last RX phase before the [USER] device test).
**Companion:** `plans/2026-06-05-epub-reading-experience-overhaul.md` (Phase 4) · `notes/2026-06-05-rx-discovery-findings.md` (D3/D4).
**Grounded against:** the live `epub_working/` tree + `scripts/build_edition.py` (HEAD `bb489a93`).

> Fixes device-QA issues #3 (Kobo "horrendously slow / crashes"), #4 ("nothing pops up"
> — size-driven), #11 (TOC "messed up"). Build-time only — `epub_working/` stays the
> canonical 61-file base (like the badge post-pass). Every note/feature stays ON.

---

## 0. Verified facts (the design rests on these)

**Pipeline (`build_one`, build_edition.py:3395):** `shutil.copytree(EPUB_DIR → tmp)` then, in order, CSS appends → cover → per-file `filter_html`/`renumber_markers`/vnote/tradition/retitle → canon filter → title-page art → **OPF/nav/ncx canon patch** (3708–3740) → chapter decoration → **`apply_reader_toc_transforms`** (3752) → bilingual TOC → **`apply_badge_markers`** (3778) → matter-page injection (copyright/dedication/your-edition/legend/back-matter/reading-plans, each adds its own manifest+spine+nav entries) → `build_epub` zip (3816). The splitter hooks **last, immediately before zip**, after every content + matter mutation.

**Split-file structure (`index_split_NNN.html`):** standalone XHTML — `<html><head><title>…</title><link css></head><body class="bible-body"> … </body></html>`. Body = a flat sequence of top-level sibling units:
- book start: `<div class="book-title-page" id="bp-NN" data-book-idx="N" epub:type="bodymatter">…</div>` (self-contained title page),
- chapter: `<a id="ch-bNN-cMM" class="ch-anchor">` followed by that chapter's verse content **and its own** `<aside class="notes-section">` (markers + asides co-located).
Chapters are flat siblings (div tags balance 34/34 in file 001; first `<div>` only after the early chapter anchors). **Cutting the body at unit boundaries is well-formed** — no spanning wrapper.

**ID scheme (all globally unique):** `bp-NN` (book), `ch-bNN-cMM` (chapter), `v-{code}-{ch}-{v}` (verse), `note-{id}` / `ref-{id}` (numbers footnotes), `vnotes-…` / `vbadge-…` (badge footnotes), `page_1` (TOC).

**Link inventory (`epub_working`):**
- **8,137** cross-file `href="index_split_NNN.html#id"` (+ nav.xhtml 88, + toc.ncx `src=`) — all navigation (book/chapter/verse anchors + the TOC page's 1,864).
- **bare `#id`** footnote contract (file 001: 2,293 `#note/ref/vnotes/vbadge-`) — **zero cross-file note links**; marker↔aside are same-chapter ⇒ same-piece (we never split mid-chapter), so they stay valid untouched.
- **36,535** bare `#(v|ch|bp)-` content links — same-file today, but can span chapters; after a split the target may land in another piece ⇒ **must be resolved via the id→piece map** (rewrite to `piece#id` only when it crosses a piece).

**Gates / invariants:**
- `check_nested_anchors.py` globs `epub_working/*.html` → base unaffected (splitter touches only `tmp`). Built pieces stay nested-anchor-clean (cutting preserves nesting).
- `build_cache.compute_cache_key` hashes the edition record + **`scripts/build_edition.py` source** ⇒ implementing the splitter *in* build_edition.py + adding a `reader_file_split` edition field re-keys the cache automatically.
- `test_byte_stability_gate.py` = determinism (build flagship twice → identical) + editions distinct → a **deterministic** splitter keeps it green. This RX arc intentionally changes presentation: pin NEW output, categorize-diff the rest.
- `build_standalone.py` also copytrees `epub_working` + globs `index_split_*.html` (fresh-OPF path). Smaller (4 books); splitter extends there as a near-no-op.
- Safety net: **epubcheck** RSC-005 (well-formed) / RSC-007 (missing file) / RSC-012 (missing fragment) validates every piece + every internal href.

---

## 1. Phase 4b — `apply_file_split(tmp, edition) → dict` (build_edition.py)

Gated on `edition.get("reader_file_split")` (new field; default **on** for the standard editions, like badge). `TARGET = 400_000` bytes. **Never splits a chapter** (atomicity preserves the same-file footnote contract).

**Algorithm (deterministic — sorted iteration, stable naming):**
1. **Plan** — for each `sorted(tmp.glob("index_split_*.html"))`:
   - Split text into `head` (through the `<body…>` open tag), `body`, `tail` (`</body>…`).
   - Find unit-boundary offsets in `body`: `re.finditer(r'<div class="book-title-page" id="bp-\d+"|<a id="ch-b\d+-c\d+" class="ch-anchor")`. `body[:first]` (preamble — e.g. file 000's TOC block) joins unit 0.
   - If `len(text) ≤ TARGET`: one piece, **keep original name** (zero churn; inbound hrefs need no rewrite). Else: greedily pack whole units into pieces `≤ TARGET` (a lone oversized unit = its own piece). Piece name = `index_split_{NNN}_{KK:02d}.html`; each piece = `head + units + tail`.
2. **Global maps** (across all files): `idmap[id] → final filename` (scan each piece's `id="…"`), `filemap[index_split_NNN.html] → first piece`.
3. **Rewrite links** in every `*.html`/`*.xhtml` + nav.xhtml + toc.ncx + content.opf, per file knowing its own final name:
   - full `(href|src)="index_split_NNN.html(#frag)?"` → `idmap[frag]` (or `filemap[file]` when no fragment).
   - bare `href="#frag"` → leave if `idmap[frag] == this piece`, else `idmap[frag]#frag` (auto-keeps footnote bare links bare).
4. **Write** — delete split originals, write pieces, keep unchanged files.
5. **OPF** — replace each split file's `<item …href="index_split_NNN.html"…/>` with its N piece items (new unique ids `…_KK`) and its `<itemref idref/>` with N piece itemrefs **in order**; preserve all other (matter/nav/font/css/cover) entries + their positions. Mirror `patch_opf_canon`'s id-extraction.
6. **nav.xhtml / toc.ncx** — book `bp-NN` links already remapped by step 3. (Chapter enrichment: optional add of a nested `<ol>`/navPoints of chapters per book so the reader's native TOC carries chapter nav once the in-content TOC goes compact — do it iff it stays epubcheck-clean.)

**Returns** `{files_split, pieces_created, hrefs_rewritten, largest_piece_kb}`.

**TDD:** unit tests on synthetic two-chapter HTML (head/body/tail split; unit boundaries; piece packing; idmap; bare-link cross-piece rewrite; full-link remap; OPF manifest+spine expansion; determinism = split twice → identical). Integration: build flagship → epubcheck 0/0/0/0, nested-anchors 0, `ebible verify` errors=0, every `index_split_*` ≤ ~0.5 MB, largest piece reported.

## 2. Phase 4a — compact, Kobo-safe in-content TOC

`reader_toc_compact` (new bool, default **on**): strip each `<li class="toc-book">`'s `<ol class="toc-chapters">…</ol>` + unwrap `<details>` → a clean **book-list** (`<p class="toc-book-label"><a href=…#bp-NN>Book</a></p>`). No `<details>`, no flexbox → Kobo-safe; also shrinks file 000 (1,864 links → 88), easing the splitter. Chapter-level nav lives in the reader's **native** nav.xhtml/toc.ncx (enriched in 4b). `reader_toc_compact=false` keeps today's accordion (`reader_toc_collapsible`/`_default_open`). CSS: drop `display:flex;flex-wrap:wrap` from `.toc-wrap ol.toc-chapters` (children already `inline-block`) so the non-compact form is Kobo-safe too. Surface in `/customize` (RULES §6.5 — configurable; safe form is the default for this arc).

## 3. Gate (program end) + handoff
All 11 editions + 2 standalones: epubcheck 0/0/0/0, `ebible verify` errors=0, nested-anchors 0, lint/mypy/ruff clean, determinism green, non-targeted KJV parts categorize-diff to presentation-only. Update SESSION_STATE/IN_FLIGHT/CHANGELOG; 5-leg save; signal Mac "build ready" (LANE_HANDOFF) for the GATED cross-reader validation. The [USER] does the device test (batched at the end).
