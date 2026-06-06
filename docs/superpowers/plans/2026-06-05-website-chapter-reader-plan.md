# Website Chapter-Reader — Implementation Plan (Phase 1: the Geʽez+English Psalter, honestly)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or superpowers:executing-plans — implement task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Status:** READY 2026-06-05 — Phase 1 of the on-site Geʽez+English chapter reader (spec `specs/2026-06-05-website-chapter-reader-design.md`, approved). 7 TDD tasks: per-chapter coverage → website parallel renderer → reader-page + book-index emission → pill/cell links → `build.mjs` `read/` pass + `{{root}}` token + sitemap + honesty assertion → build/visual-QA → finalize. Builds on the just-shipped progress page; static + dep-free; never over-claims by construction; byte-disjoint from the EPUB pipeline.

**Goal:** Make the Geʽez/Amharic progress pills clickable into a real on-site reader showing the **already-transcribed scripture** — Geʽez + literal English side-by-side where both exist, Geʽez-only / Amharic-only where English isn't done yet — generated statically from the same translation store the EPUBs use, beautifully manuscript-styled and **freely copy-pasteable**. Grows automatically as transcription advances.

**Scope (2026-06-05, user-confirmed — three tiers, ≈903 complete chapter pages):**
- **Gate = the progress map's transcribed signal** (own-versified ◑/● via `_own_versified`/`_standalone` — reuse `gen_website_progress.py`'s existing logic). Raw OCR source (◐) is **never** emitted — that is the whole point of the progress map. Per chapter: **parallel** where an EN back-translation exists (len + verse-seq match), else **single-column** Geʽez (Tier B) / Amharic (Tier C).
- **Currently emitted = 161 parallel chapters** across the 4 transcribed Geʽez books: `psa` 1–151 (2531 v), `1ki` 1–6 (191 v), `1sa` {1,3,17} (107 v), `2sa` {11} (26 v) — all EN-paired. **Tier B (Geʽez-only) and Tier C (Amharic-only) are 0 today** (everything transcribed already has EN; no Amharic is own-versified) but fully supported — they fill in automatically as books reach ◑/●.
- Partial chapters of the marathon books (e.g. 1 Kings 1–6, some short of their full canonical length) show the transcribed verses, exactly EN-paired; the book index marks not-yet-transcribed chapters as non-clickable "to come."
- **Free copy-paste** (real selectable Unicode; verse-gutter `user-select:none`; a per-column "Copy chapter" button — tiny inline vanilla JS, graceful fallback) and **manuscript-authentic styling** (Ethiopic-numeral + rubricated chapter headings & verse numbers, gold ornamented rule, parchment, Noto Serif Ethiopic). Tasks below are written Tier-A-first; Tiers B/C reuse the same renderer single-column.

**Architecture:** Extend the proven two-stage pipeline — a Python pre-step (`scripts/gen_website_progress.py`) computes per-chapter parallel-readiness from the REAL store via `scripts.core.translations` and emits one static reader page per *clickable* chapter + a per-book reader index under `website/src/read/geez/...`; the dep-free `website/build.mjs` recurses `src/`, wraps each through the shared head/foot frame via a depth-correct `{{root}}` asset token, appends the reader URLs to the sitemap, and asserts every reader-link target exists before writing `dist/`. The `geez.html` pills link in only where a reader exists. No server, no JS, no second copy of the text, no touch to `build_edition.py`/`epub_working`.

**Tech stack:** Python 3.14 (`scripts.core.{config,translations}`, `scripts.build_standalone`); plain HTML/CSS; Node-core `build.mjs` (no npm). Tests: pytest.

**Spec:** `docs/superpowers/specs/2026-06-05-website-chapter-reader-design.md`

**Verified ground truth (controller-verified — pin in tests):**
- EN-paired chapters = 168 across the stores, BUT the reader gate is **own-versified (◑/●)**, which excludes the ◐-source `gen`/`ex`/`lev` (OCR drafts that happen to carry a few EN chapters) → **emitted today = 161 parallel chapters** across the 4 transcribed books: `psa` 1–151 (2531 v), `1ki` 1–6 (191 v), `1sa` {1,3,17} (107 v), `2sa` {11} (26 v). Own-versified set verified via `_own_versified` + `_STANDALONE_BOOKS`; amharic-tewahedo own-versified = ∅ today.
- Pairing is **positional / occurrence-index** — duplicate `(ch,verse)` keys exist (Ps 36 = 40 rows / 38 distinct). Use `scripts.build_standalone.chapter_verses_in_source_order(store, book) -> dict[ch, list[(verse,text)]]` (source order, dup-preserving) for BOTH `geez-tewahedo` and `geez-tewahedo-en`.
- A chapter is **parallel-ready** iff both stores have it AND `len(geez[ch]) == len(en[ch])` AND `[v for v,_ in geez[ch]] == [v for v,_ in en[ch]]`.
- `_STANDALONE_BOOKS = ["1ki","1sa","2sa","psa"]`. `geez-tewahedo-en` files = `gen,ex,lev,psa,1sa,2sa,1ki` (7).
- Text is **plain** (0/2531 verses contain HTML); Ethiopic `፡`/`።` are content. Geʽez is **LTR**, `lang="gez"` (Noto Serif Ethiopic wired at `style.css:55`). English divine name renders **"Yahweh"** (already in the `-en` store text).

**⚠ Pitfalls (verified — do NOT repeat):**
- `translations.get_chapter()` returns **`(verse, text)` 2-tuples** sorted by verse, **no dedup** — NOT `(ch,verse,text)`. Use `chapter_verses_in_source_order` (or `_load_book` → 3-tuples) instead.
- The `_en_books` `\s*\(\d` line-regex **under-counts wrapped tuples** (1ki = 21 vs 191 true) — never use it for per-chapter readiness.
- `canonical_book_shape(book)` **raises `FileNotFoundError`** for `1en/jub/4ba/mq1-3` (no KJV skeleton) and 62 Psalms chapters are LXX-short — relevant only to the deferred Gate B (Phase 3); Phase-1 Gate A uses exact key-set match and never touches the KJV table.

**Env (per-lane — cross-lane parity Guard #4):**
- **Mac (this lane):** interpreter `.venv/bin/python` (NOT `python3` = sys 3.9); `export PYTHONPATH=<repo>`; `export TMPDIR=/Volumes/MacHD2/<dir>` for any tmp-using run; pytest `--basetemp="$TMPDIR/yhwh-pytest/bt"`; `node website/build.mjs`.
- **Windows (N95):** interpreter `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe`; `$env:PYTHONUTF8="1"`; `$env:PYTHONPATH=<repo>`; `--basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`.

**File structure:**
- Modify `scripts/gen_website_progress.py` — add per-chapter coverage (`chapter_coverage`), the website parallel renderer (`render_reader_chapter`, `render_book_index`), reader-page emission (`write_reader_pages`), and link-wiring into the pills; `main()`/`write_outputs` calls the new emit.
- Modify `tests/test_website_progress.py` — coverage + renderer + emission + honesty tests.
- Modify `website/build.mjs` — recurse `src/` subdirs, `{{root}}` depth token, append reader URLs to the sitemap, build-time link-target assertion.
- Modify `website/partials/head.html` (+ `foot.html` if it refs assets) — relative asset refs → `{{root}}<asset>`.
- Modify `website/src/geez.html` — (only if the heatbar legend needs a one-line "click a Bible-ready book to read it" note).
- Modify `website/style.css` — additive `.rdr-*` block (parallel rows, mobile collapse, link affordance on ready pills).
- Generated (committed): `website/src/read/geez/<book>/<ch>.html`, `website/src/read/geez/<book>.html` (book index), and the per-chapter data folded into `website/src/data/progress.json`.

---

### Task 1: Per-chapter parallel-coverage computation (the data core)

**Files:** Modify `scripts/gen_website_progress.py`; test `tests/test_website_progress.py`.

- [ ] **Step 1 — failing test.** Add `test_parallel_coverage_truth`: `cov = gp.chapter_coverage(REPO)` returns `{book: {ch: {"geez": int, "en": int|None, "parallel": bool}}}` for the 7 EN books. Assert: total parallel-ready chapters across all books == **168**; sum of parallel verses == **3032**; `cov["psa"]` has 151 parallel chapters and `cov["psa"][36]["geez"] == 40` (duplicate-verse chapter survives); `cov["1ki"]` parallel chapters == {1,2,3,4,5,6}; `cov["1sa"]` == {1,3,17}; a chapter where lengths differ is `parallel: False`.
- [ ] **Step 2 — run, expect fail** (`AttributeError: chapter_coverage`).
- [ ] **Step 3 — implement** `chapter_coverage(repo)`: import `scripts.build_standalone as bs`; for each EN book, `gz = bs.chapter_verses_in_source_order("geez-tewahedo", bk)`, `en = bs.chapter_verses_in_source_order("geez-tewahedo-en", bk)`; per chapter compute `geez_len`, `en_len` (None if absent), `parallel = en is present and geez_len == en_len and [v for v,_ in gz[ch]] == [v for v,_ in en[ch]]`. Return the nested dict. (No `get_chapter`, no `_en_books` regex.)
- [ ] **Step 4 — run, expect pass.**
- [ ] **Step 5 — commit** (local, no push this turn): `feat(website): per-chapter Geʽez↔English parallel-coverage computation`.

### Task 2: The website parallel renderer

**Files:** Modify `scripts/gen_website_progress.py`; test.

- [ ] **Step 1 — failing test.** `test_render_reader_chapter`: `html = gp.render_reader_chapter("psa", 36, geez_rows, en_rows)` (rows from `chapter_verses_in_source_order`). Assert: 40 `.rdr-row` rows (duplicate verse preserved via positional zip); `lang="gez"` on the Geʽez span; text is HTML-escaped (`&`/`<`/`>` safe; no `<script>`); the verse-number gutter shows the source verse number; a single-column variant (`render_reader_chapter("job", 1, geez_rows, None)`) emits Geʽez-only rows + a "back-translation not yet available" note.
- [ ] **Step 2 — run, expect fail.**
- [ ] **Step 3 — implement** `render_reader_chapter(book, ch, geez_rows, en_rows)`: zip positionally; per row emit `<div class="rdr-row"><span class="rdr-vn">{v}</span><p class="rdr-gez" lang="gez">{esc(text)}</p>{<p class="rdr-en">{esc(en)}</p> if en_rows else ""}</div>`. Escape with the existing `escape`/`_t`. Keep Ethiopic punctuation as-is. Single-column when `en_rows is None`.
- [ ] **Step 4 — run, expect pass.**
- [ ] **Step 5 — commit** (local): `feat(website): parallel Geʽez|English chapter renderer (occurrence-index paired)`.

### Task 3: Reader-page + book-index emission

**Files:** Modify `scripts/gen_website_progress.py` (`render_book_index`, `write_reader_pages`, wire into `write_outputs`/`main`); test.

- [ ] **Step 1 — failing test.** `test_write_reader_pages_only_ready`: run `gp.write_reader_pages(tmp_repo)` against a temp `website/src/read/` and assert exactly **168** chapter files + **7** book-index files exist; that `read/geez/psa/1.html` exists but `read/geez/psa/200.html` does NOT; that a non-ready book (e.g. `job`) emits **no** files in Phase 1 (Gate B deferred); each emitted chapter file starts with a `<!--page title:... canonical:... page:read -->` front-matter block; filenames are deterministic (re-run → byte-identical). Book index contains a chapter heatmap (`rdr-cell` per chapter) + an "X of Y chapters readable" bar, linking ready chapters only.
- [ ] **Step 2 — run, expect fail.**
- [ ] **Step 3 — implement:** `write_reader_pages(repo)` loops `chapter_coverage`; for each parallel chapter, pull `gz[ch]`/`en[ch]`, call `render_reader_chapter`, wrap with `<!--page ...-->` front-matter (title e.g. "Psalm 1 — Geʽez & English", canonical `https://www.yhwhyaway.com/read/geez/psa/1.html`, `page: read`) + a provenance/attribution footer line + prev/next (clickable siblings only) + back-links, and write to `website/src/read/geez/<book>/<ch>.html`. `render_book_index(book, cov)` builds `read/geez/<book>.html` (heatmap + bar). Add `chapters` data into `progress.json` rows. Wipe+rewrite `website/src/read/geez/` each run (stale-page hygiene). Call from `write_outputs`/`main` after the existing two writes.
- [ ] **Step 4 — run + generate the real outputs** (`.venv/bin/python scripts/gen_website_progress.py`); spot-check `read/geez/psa/1.html` + `read/geez/psa/36.html`.
- [ ] **Step 5 — commit** (local): `feat(website): emit static reader pages + per-book chapter index (parallel-ready only)`.

### Task 4: Pill/cell links on geez.html

**Files:** Modify `scripts/gen_website_progress.py` (`_grid`); test; small `style.css` link affordance (Task 6).

- [ ] **Step 1 — failing test.** `test_ready_pills_link_to_reader`: in the rendered geez fragment, a book with ≥1 parallel-ready chapter (`psa`) is wrapped in `<a class="pb-link" href="read/geez/psa.html">`; a book with zero ready chapters is NOT a link; the EN chip lights only where ≥1 parallel-ready chapter exists.
- [ ] **Step 2 — run, expect fail.**
- [ ] **Step 3 — implement:** thread the coverage map into `_bible_progress`/`_grid`; when a Geʽez book has ≥1 parallel-ready chapter, wrap the cell content in `<a class="pb-link" href="read/geez/<code>.html">…</a>`; recompute the `en` chip from real parallel coverage (not the old `_en_books` proxy) — keep the ≥50 proxy only as a fallback for the book-level EN badge if needed, but prefer the coverage map. Amharic grid unchanged (no links).
- [ ] **Step 4 — run, expect pass.**
- [ ] **Step 5 — commit** (local): `feat(website): link Bible-ready pills into the chapter reader`.

### Task 5: build.mjs — `read/` subtree, `{{root}}` token, sitemap, honesty assertion

**Files:** Modify `website/build.mjs`, `website/partials/head.html` (+ `foot.html` if needed).

- [ ] **Step 1 — `{{root}}` asset token.** In `head.html` (and `foot.html` if it refs assets), change relative asset refs (`href="style.css"`, font/icon/favicon refs) to `{{root}}style.css` etc. In `build.mjs`, compute `root` per output page = `"../".repeat(depth)` where depth = number of path segments below `dist/` (top-level pages → `""`); `fill(..., 'root', root)`. Top-level page output stays byte-identical (root="").
- [ ] **Step 2 — recurse `src/`.** Replace the top-level `src/*.html` glob with a recursive walk that preserves the subpath (`src/read/geez/psa/1.html` → `dist/read/geez/psa/1.html`), running each through the same head/foot + front-matter + `{{root}}` fill. Keep the existing `{{geez_progress}}` inline.
- [ ] **Step 3 — sitemap.** After the page loop, collect every emitted page's site path and build the `<url>` list programmatically (keep the 5 hand-listed section pages; append the reader URLs) — replaces the hardcoded `PAGES` mapping at `build.mjs:107/114`.
- [ ] **Step 4 — honesty assertion.** Before/after writing `dist/`, scan emitted HTML for `href="read/geez/..."`/`{{root}}read/...` targets and assert each resolves to an emitted `dist/` file; **throw (fail the build)** on any dead reader link. (Reader pages are emitted only for ready chapters, so this can only fail on a generator/build bug — which is exactly what we want caught.)
- [ ] **Step 5 — verify by build** (Task 6); no standalone JS test (zero-dep, no JS test infra) — covered by the build + Playwright pass.
- [ ] **Step 6 — commit** (local): `feat(website): build.mjs reader subtree + {{root}} asset token + sitemap + dead-link guard`.

### Task 6: Styles + build + visual QA

**Files:** Modify `website/style.css`; build + verify.

- [ ] **Step 1 — CSS.** Append a `/* chapter reader */` block (read the top of `style.css` first for the palette custom-props and reuse them): `.rdr-wrap`, `.rdr-row` (CSS grid `[vn] auto [gez] 1fr [en] 1fr`, gap; collapse to one stacked column under ~640px via a media query), `.rdr-vn` (gutter), `.rdr-gez` (`:lang(gez)` already gives the font), `.rdr-en`, prev/next + back-link bar, `.pb-link` hover/focus affordance, and the `rdr-*` heatmap cell classes for the book index. Plain, parchment/gold palette, nothing gaudy.
- [ ] **Step 2 — generate + build:** `.venv/bin/python scripts/gen_website_progress.py` then `node website/build.mjs`. Expect `dist/read/geez/psa/1.html` etc. and `built dist/...` output; the dead-link assertion passes.
- [ ] **Step 3 — token/path checks:** grep `dist/read/geez/psa/1.html` for no literal `{{root}}`/`{{geez_progress}}`, a resolved `../../../../style.css`-style path, `lang="gez"`, and 6 `.rdr-row` (Ps 1). Grep `dist/sitemap.xml` for `/read/geez/psa/1.html`.
- [ ] **Step 4 — visual QA (self-serviceable; memory `feedback_visual_qa_self_serviceable`).** Serve `website/dist` via `python -m http.server`; Playwright-load and screenshot: `geez.html` (a Psalms pill is now a link), `read/geez/psa.html` (chapter heatmap + bar), `read/geez/psa/1.html` (two columns, Geʽez in Noto Serif Ethiopic, EN right, stylesheet loaded), `read/geez/psa/36.html` (duplicate-verse chapter renders all 40 rows aligned), and a mobile viewport (single-column stack). 0 console errors; stylesheet + font actually load (network 200, not 404).
- [ ] **Step 5 — full test file + lint + format:** `pytest tests/test_website_progress.py -v`; `lint_rules.py` (no new fail; if a `superpowers_coherence`/console check trips, fix); `ruff format scripts/gen_website_progress.py tests/test_website_progress.py`.
- [ ] **Step 6 — commit** (local): `feat(website): chapter-reader styles + generated reader pages (Phase 1: 168 parallel chapters)`.

### Task 7: Finalize — INDEX, truth records, deploy decision

- [ ] **Step 1 — INDEX.md:** confirm the spec + this plan are registered (done at planning commit); flip this plan's status to reflect Phase-1 shipped.
- [ ] **Step 2 — truth records:** SESSION_STATE headline + IN_FLIGHT (Phase 1 built; Phases 2–4 queued; pushes held per the user).
- [ ] **Step 3 — deploy:** the site deploy (mirror `website/dist/` → the publish repo → push) is the live-site step — **do only on explicit user GO** (irreversible public change; memory `feedback_install_guard_auto_mode`). Local commits only this turn per the user.
- [ ] **Step 4 — save:** local commits only this turn (user: "commit it but don't push"); run the full 5-leg `save-all.ps1` when the user authorizes the push.

---

## Self-review
- **Spec coverage:** per-chapter coverage ✓ (T1) · parallel two-column renderer ✓ (T2) · static reader pages + book-index heatmap, ready-only ✓ (T3) · pill/cell links ✓ (T4) · build.mjs subtree/`{{root}}`/sitemap/honesty-assertion ✓ (T5) · styles + visual QA ✓ (T6) · single source of truth (build-time read of the EPUB stores) ✓ · Guard #2 structural (no page ⇒ no link) ✓.
- **Pitfalls pinned:** occurrence-index pairing (not `get_chapter`/dict-key); coverage from true rows (not the `_en_books` regex); Gate B's `canonical_book_shape` trap deferred to Phase 3.
- **Type/name consistency:** `chapter_coverage` / `render_reader_chapter` / `render_book_index` / `write_reader_pages` used consistently; cell/row classes (`rdr-row`/`rdr-vn`/`rdr-gez`/`rdr-en`, `pb-link`) consistent across renderer, CSS, and tests.
- **Placeholders:** none — every step has concrete code/commands.

## Constraints carried
Static + dep-free (GitHub Pages); single source of truth (one text origin = the EPUB stores); never over-claim (no page ⇒ no link, by construction + a build-time assertion); plain manuscript-reverent register reusing `style.css`; byte-disjoint from `build_edition.py`/`epub_working`; collision-free with the re-ingest/audit lanes (touches `website/**` + `scripts/gen_website_progress.py` + `tests/test_website_progress.py` only). Deploy is a separate, user-gated step.
