# Beta Device-QA — Reader Presentation & Distribution Polish — Implementation Plan

> **▶ UPDATED 2026-06-08 — sequenced by the v0.1.0 master plan** (`docs/superpowers/plans/2026-06-08-v0.1.0-master-plan.md`).
> This 8-phase plan remains the presentation-implementation detail; the master plan orders it with the
> round-6 audit + app icons + outward-facing surfaces. **Changes from the 06-08 device run:**
> (a) **release retarget — Phase 8 `v1.0.0-beta.2` → `v0.1.0` (STILL A BETA);** v1.0.0 deferred further.
> (b) **ADD finding 2** — "Your-Edition" stats popup renders full-page with the book-name column off-screen
> (render-then-diagnose the modal + table CSS; relates to `edition_stats`).
> (c) **ADD finding 6** — desktop-app top-nav prettify (`scripts/web.py` nav template + app CSS → a real
> app-bar, routes grouped Build·Edit·Inspect·Publish, hover/active; behavior unchanged).
> (d) **ADD finding 7 ⭐HIGH** — macOS `.dmg` opens a browser, not a native window (pyobjc/Cocoa not bundled;
> MAC dmg rebuild + native-window verify — distinct from Phase 8 notarization) **+ app icons**
> (`launcher.spec icon=None`; Win `program_icon.ico` / Linux `icon_512.png` / macOS `.icns` via `iconutil`).
> (e) **Refinements:** Ph1 justify must be **prose-WHITELIST-scoped + a build guard** (never headings/ToC/
> tables); Ph2 grouping carries the **reader-robust-structure-FIRST north star** (cascade
> verse→category→source→note in primitives that survive any reader; tinted cards = enhancement only) and
> folds the staged **S1–S4** (S4 deferred); Ph3 the expandable in-EPUB pill ToC is a **`/customize` ON/OFF
> toggle (default ON)** + native per-chapter toggle **with reader-dependent instructions** + **incipit
> chapter labels**. Evidence + design detail:
> `docs/superpowers/notes/2026-06-08-device-qa-and-note-presentation-rehaul.md`.

**Status:** READY 2026-06-06 — 8-phase plan from the `v1.0.0-beta.1` device-QA design spec (`specs/2026-06-06-beta-device-qa-presentation-design.md`); ready to execute. macOS notarization for the final beta.2 release is Mac-gated.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the `v1.0.0-beta.1` device-QA polish — readable/justified typography, distinct note vs translation markers, colour-coded de-duplicated note popups, Kobo-friendly ToC + kepub popups, clickable in-content ToC, fixed book title pages, an OCR de-hyphenation + structural audit, and a cleaner website download + update-log — then cut `v1.0.0-beta.2`.

**Architecture:** All EPUB changes flow through the established base-HTML + build-pipeline pattern: hand-authored base `epub_working/` (HTML + `stylesheet.css`), mutated per-edition by passes in `scripts/build_edition.py::build_one`, validated by epubcheck + `ebible verify` + lint guards. Presentation choices are per-edition `editions.yaml` settings with sensible defaults (RULES §2). Corpus cleanups edit `content/notes/*.py` lockstep with the re-baked base. The website is the static `website/` tree.

**Tech Stack:** Python 3 (full interpreter path; `$env:PYTHONUTF8="1"`), pytest (`--basetemp` per memory), epubcheck (`--jar`), kepubify (new dep for the Kobo target), Node (`website/build.mjs`), ruff/mypy/lint_rules.

**Conventions (per project memory):** run one test file at a time; `ruff format` generated stores before save; after any `epub_working` mutation run `check_nested_anchors`; gate build-pipeline/HTML changes on a canon-filtered edition (catholic-study) **and** the superset (ethiopian-tewahedo); 5-leg save (local + GitLab + GitHub + E: bundle + F: copy). This **intentionally** changes output — pin new output, prove non-targeted parts unchanged via categorize-diff, do **not** assert byte-stability for touched surfaces.

---

## Phase 0: Branch + baseline

- [ ] **Step 1: Confirm clean tree + capture a baseline build for before/after compare**

Run:
```
cd "C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4"
git status -sb
git rev-parse HEAD
```
Expected: clean, on `main`. Record HEAD as the pre-change ref.

- [ ] **Step 2: Build the flagship + a canon-filtered edition as the visual baseline** (so each phase can re-render the same pages).

Run (full interpreter path, `PYTHONUTF8=1`):
```
$env:PYTHONUTF8="1"; <py> -m scripts.build_edition ethiopian-tewahedo
<py> -m scripts.build_edition catholic-study
```
Expected: both build; note output EPUB paths. Keep for diffing.

---

## Phase 1: CSS quick wins — justify, ToC link affordance, body size, Kobo-native font

**Files:**
- Modify: `epub_working/stylesheet.css` (lines per recon: 54, 114, 244-246, 352-354, 355, 357, 358, 437-446, 597-600)

> CSS is verified by build + epubcheck + render, not pytest. Each task = edit → rebuild → epubcheck → Playwright/localhost render compare.

- [ ] **Step 1: Justify verse paragraphs only.** In `epub_working/stylesheet.css`:
  - `.verse-p,.verse-p-flush` (line ~114): `text-align:left !important` → `text-align:justify`
  - `p.verse-p` (line ~358): `text-align:left` → `text-align:justify`
  - Force-left block (lines ~243-249): change `body p { text-align:left }` → `body p { text-align:left }` **kept** but ADD `body p.verse-p, body p.verse-p-flush { text-align:justify }` so front-matter labels (`.intro-*`, `.your-edition-*`, `.bookpage-*`, `.legend-*`) stay left and never re-stretch.
  - Add to the verse selectors: `hyphens:auto; -webkit-hyphens:auto; overflow-wrap:break-word;` (avoid justify rivers).

- [ ] **Step 2: Body size (Apple-tuned) + leading, reader-overridable.** Line ~357 `font-size:0.95em` → `font-size:1.05em` (Apple Books reads the plain `.epub`; the **Kobo-tuned smaller** size lands on the `.kepub.epub` in Phase 3). Promote the value to a `style_config.py` `BODY_FONT_SIZE` knob (default `1.05em`) so Phase 3 can override it for Kobo. Line ~355 `line-height:1.32 !important` → `line-height:1.45` (DROP `!important`). Everything stays relative/overridable.

- [ ] **Step 2b: Empty pages between chapters (⑫) — diagnose + fix.** Render a multi-chapter span (Genesis→Exodus) at localhost/Apple Books; locate the blanks. Check (a) stacked/redundant `page-break-*:always` on `.book-title-page`/`.ch-heading`/chapter wrappers in `stylesheet.css` (collapse to ONE break per chapter); (b) empty/near-empty `index_split_*` pieces from `apply_file_split` (`scripts/build_edition.py`) — if that's the cause, have the splitter drop/merge whitespace-only pieces (defer the splitter fix here if it's purely CSS). Apply the real fix; re-render to confirm no stray blanks. (The Phase-4 audit also detects empty pieces.)

- [ ] **Step 3: Let the reader-native serif win on Kobo body text.** Reconcile BOTH body font stacks (fix-the-class): amplification stack (lines ~352-354) and managed-region stack (lines ~597-600). Remove `Cardo` and the dead `IM Fell English`/`Goudy Bookletter 1911`/`Sorts Mill Goudy` names from the **body/`p`/`.verse-p`** font-family lists (or drop the `!important` so the reader serif wins). **KEEP** `Cardo` on `.vnote-hebrew`/`.vnote-greek` (lines ~311-333) and Noto Serif Ethiopic (unicode-range scoped). Reconcile to a single canonical body stack to kill the silent-shadow hazard.

- [ ] **Step 4: In-content ToC label link affordance.** Extend the ToC-link rule (lines ~437-446) selector list to also match `.toc-wrap li.toc-book > p.toc-book-label > a` with `color:#7B0E0E; font-weight:600; text-decoration:underline;` and give `.toc-book-label` block padding (`padding:0.25em 0`) for a large tap target.

- [ ] **Step 5: Rebuild + gate.**

Run:
```
$env:PYTHONUTF8="1"; <py> -m scripts.build_edition ethiopian-tewahedo
<py> -m scripts.build_edition catholic-study
<py> scripts/check_nested_anchors.py
# epubcheck both (per memory: pass --jar)
```
Expected: epubcheck 0/0/0/0 both editions; nested-anchors 0.

- [ ] **Step 6: Visual verify** (unzip → `http.server` → Playwright; per `feedback_visual_qa_self_serviceable`): a verse page is justified; front-matter labels still left-aligned (not stretched); in-content ToC book names render maroon/underlined/clearly tappable; body slightly larger.

- [ ] **Step 7: Commit.** `git add epub_working/stylesheet.css && git commit -m "fix(epub): justify verse text, larger reader-overridable body, native Kobo serif, clickable in-content ToC"`

---

## Phase 2: Note popup — ◈ marker, tinted cards, data-driven colours, grouping, dedup

**Files:**
- Modify: `content/categories.yaml` (add `color`/`background` per record, lines 13-103)
- Modify: `scripts/build_edition.py` (`apply_badge_markers` badge glyph 1959-1963; row assembly + dedup + grouping 1810-1955; CSS append for note_popup_style 1743-1773)
- Modify: `scripts/resync_marker_glyphs.py` (numbers-mode parity, line ~155)
- Modify: `epub_working/stylesheet.css` (category background fills, extend 640-679; vn-item card styling)
- Test: `tests/test_badge_markers.py` (or the existing badge test file), `tests/test_categories.py`

- [ ] **Step 1: Failing test — dedup.** Add `test_badge_popup_dedups_identical_notes`: build a verse region with two byte-identical `(kind, body)` note asides; assert the merged `verse-notes` aside contains the block exactly once.

- [ ] **Step 2: Run → fail.** `<py> -m pytest tests/test_badge_markers.py::test_badge_popup_dedups_identical_notes -v --basetemp=...` Expected: FAIL (block appears twice).

- [ ] **Step 3: Implement render-time dedup.** In `apply_badge_markers` row assembly (`build_edition.py:1922-1948`): maintain `seen=set()`; normalize each row to `(kind, normalized_body)` (strip whitespace); skip a marker/aside whose normalized content already appeared for that verse.

- [ ] **Step 4: Run → pass.**

- [ ] **Step 5: Failing test — grouping/sort.** Add `test_badge_popup_groups_by_category_order`: a verse with notes of kinds {topical, hist, comm, xref} → assert the emitted rows are ordered Note(hist) → Commentary(comm) → Cross-refs(xref) → Topical(topic) with a category wrapper/divider per group, topical last.

- [ ] **Step 6: Run → fail.**

- [ ] **Step 7: Implement grouping.** In row assembly: bucket rows by `category_for(kind)` (reuse `inject.category_for`), order buckets by a curated `_POPUP_CATEGORY_ORDER = [hist, comm, xref, text, lang, ... , topic]` (topical last; rare cats by the same priority), emit a `<div class="vn-group vn-group-{cat}">` with an optional header per group.

- [ ] **Step 8: Run → pass.**

- [ ] **Step 9: ◈ note marker.** Change `build_edition.py:1959-1963` badge `<sup class="marker-badge">{n}</sup>` → `<sup class="marker-badge">◈{n}</sup>` (config glyph `note_marker_glyph`, default `◈`). Mirror in `resync_marker_glyphs.py:155` numbers-mode (`◈` prefix or per-category glyph). Add `test_badge_marker_uses_glyph` asserting `◈` present, bare-number absent.

- [ ] **Step 10: Data-driven category colours.** Add `color` + `background` to each `content/categories.yaml` record (the deconflicted palette from spec §3.2). Add `test_categories_have_colors` (every category has a valid hex `color` + `background`; no duplicate `color` among the high-volume categories). Have the build emit per-category CSS from `categories.yaml` (replace the hard-coded `stylesheet.css:640-679` block with build-generated rules, or generate an appended sheet) — both a `border-left` accent and a soft `background` fill on `.vn-item.note-{cat}` / `.vn-group-{cat}`.

- [ ] **Step 11: Tinted-card CSS.** Style `.vn-item` as a card (padding, radius, the category background fill + accent border, margin between cards) and `.vn-group` separation. Wire as the default `note_popup_style` (cards) in the build CSS append (`build_edition.py:1743-1773`).

- [ ] **Step 12: Rebuild + gate + visual verify.** epubcheck 0/0/0/0 (eth + catholic-study); nested-anchors 0; render Gen 1:1 popup → exactly one cross-ref block, categories grouped + colour-tinted, topical last, ◈ marker inline.

- [ ] **Step 13: Commit.** `feat(epub): colour-coded tinted note cards, category grouping + ordering, popup dedup, ◈ note marker`

---

## Phase 3: Native ToC book-level + kepub Kobo output

**Files:**
- Modify: `content/editions.yaml` (new field), `scripts/build_edition.py:4298-4299` (gate `enrich_nav_chapters`)
- Create: `scripts/build_kepub.py` (kepubify wrapper) + wire an optional output target in `build_one`
- Test: `tests/test_native_toc_books_only.py`, `tests/test_kepub_output.py`

- [ ] **Step 1: Failing test — native ToC book-level by default.** `test_native_toc_is_book_level_without_flag`: build nav.xhtml/toc.ncx for an edition WITHOUT `reader_native_toc_chapters` → assert NO `toc-nav-chapters` / per-chapter navPoints.

- [ ] **Step 2: Run → fail** (currently enriched whenever `reader_toc_books_only`).

- [ ] **Step 3: Implement.** `build_edition.py:4298-4299`: gate `enrich_nav_chapters(tmp)` on `edition.get('reader_native_toc_chapters')` (new field, default false) instead of `reader_toc_books_only`. Add the field to `editions.yaml` schema + `/customize` (RULES §6.5); omit it for ethiopian-tewahedo (→ book-level). Keep the function for opt-in editions.

- [ ] **Step 4: Run → pass.**

- [ ] **Step 5: Kepub wrapper.** Install kepubify (document the binary path; no pip). `scripts/build_kepub.py`: given a built `.epub`, produce `<name>.kepub.epub` via kepubify; enforce ASCII-letter-initial ids (already true); pass kepubify flags to **suppress auto-popping every internal cross-reference** (`--no-...` per kepubify docs) while keeping footnote popups. Add `kepub_output` edition flag (default on for the additional target). **Apply the Kobo-tuned smaller body font** to the kepub variant: build the kepub from an EPUB whose `style_config.BODY_FONT_SIZE` is set to the smaller Kobo value (~`0.92em`), or inject a Kobo CSS size override before kepubify — so Apple keeps the larger plain-EPUB size and Kobo gets the smaller one (the per-device differentiation).

- [ ] **Step 6: Test kepub.** `test_kepub_output_is_valid`: run the wrapper on a tiny built EPUB; assert a `.kepub.epub` is produced, is a valid zip, contains `koboSpan` markup, and the note/aside ids are intact. (If kepubify unavailable in CI, mark `slow`/skip-if-missing.)

- [ ] **Step 7: Wire into build_one** as an extra output (NOT a transform of the canonical EPUB) behind `kepub_output`.

- [ ] **Step 8: Gate + commit.** epubcheck the plain EPUB (kepub is intentionally non-epubcheck-standard); `feat(epub): book-level native ToC default (opt-in chapters) + .kepub.epub Kobo target for popups`

---

## Phase 4: Structural formatting audit (diagnostic + lint guard)

**Files:**
- Create: `scripts/audit_epub_structure.py` (diagnostic), a lint rule in the existing lint harness
- Test: `tests/test_epub_structure_audit.py`

- [ ] **Step 1: Failing test.** `test_audit_flags_duplicate_note_block`: feed a built-EPUB fragment with a duplicated `vn-item` block → assert the audit reports it; a clean fragment → zero criticals.

- [ ] **Step 2: Run → fail.**

- [ ] **Step 3: Implement the diagnostic.** Parse built XHTML; assert the canonical uniform shape and flag deviations: duplicate `(kind, body)` note blocks per verse; duplicate ids; broken/missing `href` targets; unbalanced/missing `<`/`>` (well-formedness per piece); witness-identical adjacent translation popups; pills off the canonical shape; OCR word-break residue (`\w+- \w+` in note bodies). Output a triaged report (path → finding → count). Run over the built eth + catholic-study.

- [ ] **Step 4: Run → pass; then RUN IT for real** to size Phase 5: count `(book,ch,v,kind,body)` duplicate-tuple collisions corpus-wide and OCR word-break occurrences. Save the report to `docs/superpowers/notes/2026-06-06-structure-audit.md`.

- [ ] **Step 5: Permanent lint guard.** Add a check in the lint-rules harness enforcing the canonical-shape invariants (no dup blocks, balanced tags, resolvable hrefs) so it can't regress; seed-test it fails on a planted violation.

- [ ] **Step 6: Commit.** `feat(audit): EPUB structural-consistency diagnostic + lint guard`

---

## Phase 5: Corpus cleanups — duplicate-tuple prune + OCR de-hyphenation (gated on Phase 4 report)

**Files:**
- Create: `scripts/_prune_duplicate_notes.py`, `scripts/_dehyphenate_notes.py` (frozen one-shots, per the re-ingest pattern)
- Modify: `content/notes/*.py` + `epub_working/index_split_*.html` (lockstep)
- Test: `tests/test_note_dedup_cleanup.py`, `tests/test_dehyphenation.py`

- [ ] **Step 1: Duplicate-tuple prune.** One-shot pruning on-disk duplicate note tuples colliding on `(book,ch,v,kind,body,attribution)` across suffixes (the `promote.py:88-144` key, suffix-independent). Pair each removal to exact old-body equality; remove from source `content/notes/*.py` AND the baked base lockstep. Verify byte-exact base reconstruction.

- [ ] **Step 2: De-hyphenation.** One-shot rejoining source-OCR line-break splits `"word- word" → "wordword"` ONLY where the join forms a dictionary/affix-valid word; **never** touch legitimate hyphens (maintain an allowlist: `cross-references`, `image-of-God`, etc.). Scope first to known OCR sources (`dict-easton`, manuscript-witness). Obvious unambiguous errors (`^n ` → `In `) only where safe; log ambiguous ones (`Eome`→`Rome`) for [USER] review, do NOT blind-replace.

- [ ] **Step 3: Tests.** Sample assertions: `"con- tains"→"contains"`; `"cross-references"` untouched; byte-exact reconstruction (`apply_map(HEAD)==working`); categorize-diff proves only targeted bodies changed (marker/aside id+kind invariant).

- [ ] **Step 4: Lint guards** — `no_ocr_word_breaks` (count → 0 over cleaned sources), extend the dedup guard.

- [ ] **Step 5: `ruff format` the regenerated stores** (per memory — else pre-commit blocks).

- [ ] **Step 6: Gate.** epubcheck 0/0/0/0 (eth + catholic-study); `ebible verify` errors=0; nested-anchors 0; re-run the Phase-4 audit → dup + word-break counts now 0.

- [ ] **Step 7: Commit.** `fix(corpus): prune duplicate note tuples + de-hyphenate OCR word-breaks (Easton/MS)`

---

## Phase 6: Book title-page alignment (render-first)

**Files:**
- Modify: `epub_working/stylesheet.css` (`.book-title-page`/`.book-title-frame` ~503-507) — **only after the render pins the element**

- [ ] **Step 1: RENDER FIRST (non-negotiable).** Unzip the current ethiopian-tewahedo build; `http.server`; Playwright-render a book title page (Genesis); screenshot. Pin the exact off-element (hypothesis: `.book-title-frame` is a left-anchored `inline-block` → short eyebrow/subtitle hug left, big title extends right).

- [ ] **Step 2: Fix the pinned element.** Most likely: ensure `.book-title-frame`'s parent `.book-title-page` is `text-align:center` AND the frame is block-centered (`margin:0 auto` with a real width, or make the frame not shrink-wrap), so all lines share one centred axis. Do NOT just re-assert `text-align:center` on already-centered children.

- [ ] **Step 3: Re-render + verify** eyebrow/subtitle/title on one centred axis across 2-3 books (Genesis + a short-titled + a long-titled book). epubcheck 0/0/0/0.

- [ ] **Step 4: Commit.** `fix(epub): centre book title-page frame (eyebrow/subtitle/title share one axis)`

---

## Phase 7: Website downloads + update log

**Files:**
- Modify: `website/src/releases.html`, `website/src/releases.js` (+ CSS), `website/build.mjs` if needed
- Create: an update-log data source (e.g. `website/src/data/changelog.json` or inline) capped at 3 entries

- [ ] **Step 1: Single download block.** One clean Download section: 3 platform buttons (Windows app / Mac app / Linux app) — human-friendly labels; raw filename + checksum behind a "details" disclosure. Exactly one current beta (no multiple downloadable betas).

- [ ] **Step 2: Update log.** A separate "What's changed" section, capped at **3 entries (1 present + 2 past)**, oldest drops off. Seed with the `beta.2 → beta.1` entry once Phase 8 lands. Visually separated from the download CTAs.

- [ ] **Step 3: Mobile layout.** Responsive: buttons stack cleanly on small screens; the cramped/weird mobile look fixed (test at ~375px).

- [ ] **Step 4: Build + verify.** `node website/build.mjs`; check 0 dead links (the build's guard); render desktop + 375px mobile via Playwright.

- [ ] **Step 5: Commit** (source only; deploy is the Pages step, on the user's go / when Mac is up). `feat(site): single current-beta download + capped update log + mobile fix`

---

## Phase 8: Release v1.0.0-beta.2 (Mac-gated for notarization)

**Files:** `VERSION`, `dev/CHANGELOG.md`, release artifacts

- [ ] **Step 1: Bump `VERSION` → `1.0.0-beta.2`** (must differ from beta.1).
- [ ] **Step 2: Rebuild artifacts** — the Ethiopian Bible EPUB (with all the above), the Windows `YHWH.exe` (Azure-sign via `dev/sign_windows.ps1`), the Linux AppImage (CI). **macOS `.dmg` notarization requires the Mac lane** → stage; join when Mac is back.
- [ ] **Step 3: Checksums** — regenerate merged `SHA256SUMS.txt` (all assets).
- [ ] **Step 4: GitHub release** — new tag `v1.0.0-beta.2`, upload signed assets, mark prerelease; supersede/retire `beta.1`. `releases.js` auto-surfaces it.
- [ ] **Step 5: Update log** — write the `beta.2 → beta.1` "what's changed" entry (Phase 7) + `dev/CHANGELOG.md`.
- [ ] **Step 6: Verify live** — download URLs HTTP 200 at the right byte sizes; site shows the single current beta.

> **Mac-gated note:** Windows + Linux + EPUB can be built/signed here; macOS notarization waits for the Mac. Either ship beta.2 with Win+Linux+EPUB and add the notarized dmg when Mac returns (`--clobber` onto the same tag, per the beta.1 pattern), or hold the tag until Mac is up — user's call at release time.

---

## Self-review (spec coverage)

- ① markers → Phase 2 (◈ marker) + spec §3.1 translation-marker decision (kept verse number; no code beyond ensuring the popup header is prominent — already emitted at `generate_verse_popups.py:34`).
- ② dedup → Phase 2 (render-time) + Phase 5 (corpus prune).
- ③ grouping/order → Phase 2.
- ④ colour-coded tinted cards → Phase 2.
- ⑤ typography (justify/size/font) → Phase 1.
- ⑥ OCR de-hyphenation → Phase 5.
- ⑦ Kobo popups (kepub) → Phase 3.
- ⑧ native ToC book-level → Phase 3.
- ⑨ in-content ToC clickable → Phase 1.
- ⑩ title page → Phase 6.
- ⑪ formatting audit → Phase 4.
- website + versioning + release → Phases 7–8.

All spec sections map to a phase. Each phase is independently committable and epubcheck-clean.
