# Website chapter-reader — "the Bible on the website" — design (2026-06-05)

**Status:** APPROVED (design) 2026-06-05 — turn the Geʽez/Amharic progress-page pills into a real **on-site Geʽez + literal-English chapter reader**, generated statically from the same translation store the EPUBs use, clickable **only where real parallel text exists** (Guard #2 by construction). Phase 1 = the transcribed content (Psalms-led — gated on the progress map's own-versified signal, never OCR drafts). Next: the implementation plan (`plans/2026-06-05-website-chapter-reader-plan.md`).

> Recon + a 3-lens design panel + an adversarial judge produced this; every load-bearing fact below was verified against the live repo (workflow `wf_fc86a45e-066`, then re-verified by the controller — including two agent errors corrected, see §9).

## Scope update (2026-06-05, user-confirmed — supersedes the "parallel-only Phase 1" framing below)
The user directed **building** the reader now to surface **all already-transcribed scripture as it progresses**, in **three reader tiers**, with **free copy-paste** and a **manuscript-authentic** presentation. (Sources are settled — the whole canon is sourced; this is not re-investigated, per Guard #2.)
- **The gate is the progress map's own transcribed signal** — a book is readable iff it is **own-versified (◑ transcribed / ● Bible-ready)**, the exact signal `gen_website_progress.py` already computes (`_own_versified` / `_standalone_books`). Raw OCR source (◐ "source in hand") is **never** shown — that is the whole point of the progress map; OCR drafts stay ◐ until they're actually transcribed.
- **Per chapter:** **Geʽez+English parallel** (two columns) where an English back-translation exists; **single-column Geʽez (Tier B) / Amharic (Tier C)** where the text is transcribed but English isn't done yet (English trails **after the full release**, then lights those rows automatically).
- **Currently transcribed = `psa` / `1ki` / `1sa` / `2sa` = 161 chapters, all EN-paired → all parallel** (Psalms 151 + 1 Kings 1–6 + 1 Samuel 1/3/17 + 2 Samuel 11). **No Amharic is own-versified yet → no Amharic reader yet.** Tewahedo-distinctives and every ◐-source book are excluded by the gate. The machine emits Geʽez-only/Amharic-only single-column the moment such content exists, and **auto-grows as `_own_versified`/`_standalone` expands** — "as we progress."
- **Free copy-paste** — real selectable Unicode (no anti-copy tricks, unlike other free Bible sites); the verse-number gutter is `user-select:none` so a selection yields **clean scripture**; a "Copy chapter" button per script column (tiny inline vanilla JS, graceful no-JS fallback = manual selection still works).
- **Manuscript-authentic styling** — chapter headings carry the book name in Geʽez + the chapter number in **Ethiopic numerals** (`፩ ፪ … ፻፶፩`) under a gold/rubric-red ornamented rule; verse numbers are small **rubricated (red) Ethiopic numerals** in the gutter (Arabic in `title`/`aria-label` for accessibility); parchment ground; the Geʽez/Amharic column set in Noto Serif Ethiopic. Reverent, not gaudy.
Everything below still holds: Tier A is the clean parallel subset (its honesty-by-construction model, layout, and verified pitfalls apply verbatim); Tiers B/C **reuse the same machinery** single-column with an honest "English translation planned (after full release)" line. The Amharic reader sets `lang="am"` (same Ethiopic font block). URL scheme: `read/geez/<book>/<ch>.html` and `read/amharic/<book>/<ch>.html`.

## Purpose
The most distinctive work of this project is the **Geʽez & Amharic Bibles transcribed from the manuscripts**. Today the site shows them as an honest per-book *progress grid* (`website/src/geez.html`, the just-shipped progress page). This spec advances that surface from "see how far along it is" to **"read it"**: each Bible-ready pill (and, one level down, each ready *chapter*) becomes clickable and opens that chapter **on the website**, showing **Geʽez and a literal English back-translation side by side** — a free, no-download, in-browser way to read the scripture we have transcribed. As transcription advances, re-running one generator adds the new chapters automatically: *"we'll basically be building the Bible on the website too."*

This is the **content-milestone surface** of the versioning model (decided 2026-06-05): app semver (`v1.0.0-beta.1` → 1.0) tracks the *software*; the reader is what makes the **content milestones** (Geʽez OT → Geʽez NT → Amharic OT → Amharic NT) visible and navigable.

## The real state — the source of truth (the reader MUST NOT over-claim)
Controller-verified from the live stores (`content/translations/**`, via `scripts.core.translations`):

- **The Geʽez↔English parallel corpus = 168 chapters / 3,032 verses across 7 books**, every chapter an exact 1:1 verse pairing (no orphan chapters either direction):
  - **Psalms — the standout and the only complete parallel Bible: all 151 chapters, 2,531 verses each side (83% of the paired corpus).** Ludolf-1701 / LXX numbering (151 chapters, incl. Ps 151; 62 chapters are LXX-short of the KJV count yet complete as Geʽez units — a numbering difference, NOT a gap).
  - **Genesis 1–5** (138 v) — the only other contiguous run.
  - **1 Kings 1–6** (191 v), **1 Samuel 1 / 3 / 17** (107 v), **2 Samuel 11** (26 v), **Exodus 1** (22 v), **Leviticus 1** (17 v) — the marathon-calibration slices.
- **Geʽez-only books** (readable Geʽez, no English yet — Phase 3): complete books incl. Job (1070 v), 1 Chronicles (942 v), 2 Chronicles (822 v), Nehemiah (406 v), Ezra (280 v), Esther via `est_patrologia` (167 v), plus large partials (Genesis through ch 34, Numbers 1–22, Deuteronomy 1–17, Joshua 14/14, Matthew 1–25, Sirach 1–23) and the Tewahedo-distinctives (1 Enoch, Jubilees, 4 Baruch, Meqabyan I–III).
- **Amharic has no parallel-English reader** — `amharic-tewahedo-en` covers only Genesis 1–5 + Exodus 1 + Leviticus 1 (177 v). Amharic stays **book-level progress only** on `geez.html`, exactly as today. (Its broad Geʽez/Amharic-script coverage — Genesis 1–42, Psalms 126 ch, etc. — is real but has no English column to pair with.)

**Bottom line for day one:** the finished, parallel, readable product is the **Psalter (all 151 chapters)** plus the six small Geʽez+English slices above — 168 chapters total. Everything else is Geʽez-only (Phase 3) or Amharic-only (no reader).

## Architecture — extend the proven progress pipeline, add no subsystem
The site is a **zero-dependency, two-stage static pipeline** (verified live): a Python pre-step writes artifacts into `website/src/data/`, then the dep-free Node `website/build.mjs` stitches `partials/head.html` + a `src/` body + `partials/foot.html` into `dist/`. The progress page already rides this exact chain (`gen_website_progress.py` → `website/src/data/geez-progress.html` → `build.mjs:84` `{{geez_progress}}` inline → `dist/geez.html`).

The reader **extends that same chain** — no server, no JS framework, no client-side fetch, no second copy of the text, and **no touch to `build_edition.py` / `epub_working/`** (constraint #4). Three additions:

1. **Per-chapter coverage + reader-page emission** in `scripts/gen_website_progress.py` (or a sibling `scripts/gen_website_reader.py` it calls): in the same pass that computes book stages, compute per-chapter parallel-readiness and **emit one static reader page per *clickable* chapter** plus a per-book reader index, into `website/src/read/geez/<book>/<ch>.html` and `website/src/read/geez/<book>.html`.
2. **`build.mjs` learns the `read/` subtree** — recurse `src/` so nested pages build through the *same* head/foot frame (one page-frame source of truth), and **append the emitted reader URLs to the sitemap programmatically** (today's `PAGES` array is hand-kept — reader pages would otherwise be invisible to crawlers).
3. **The `geez.html` pills link in** — a pill becomes a link **only** where its book has ≥1 parallel-ready chapter; a chapter cell on the book index links **only** when that chapter is parallel-ready. Non-ready cells stay plain/dimmed with no link **and no page emitted**.

### Single source of truth (constraint #5)
Reader text is produced **at build time** by reading the identical stores the EPUBs read, via `scripts.core.translations` — there is **no JSON/HTML text dump committed as a divergent copy**. The grouping helper `scripts.build_standalone.chapter_verses_in_source_order(store, book)` returns `dict[chapter → list[(verse, text)]]` in faithful source order with duplicates preserved; the reader consumes that for both `geez-tewahedo` and `geez-tewahedo-en`. If the store changes, re-running the generator changes the pages; they cannot drift because there is one text origin.

## The honesty model — Guard #2 enforced structurally (constraint #1, the heart)
Honesty is a **structural invariant, not a runtime check**: a reader page is emitted **only** for a chapter that passes the parallel-ready gate, so a stub/empty chapter physically has **no page to land on**, and a pill/cell can only link to a page that exists. This is the same discipline that limited the EN badge to real coverage — promoted to "no coverage ⇒ no artifact."

Per-chapter readiness is computed from **true `(verse, text)` rows**, never from a line-count heuristic:

- **Gate A — parallel-ready (the ONLY Phase-1 clickable tier).** A chapter is clickable iff **both** stores contain it **AND** the ordered Geʽez occurrence-list equals the English occurrence-list — same length and same verse-number sequence, paired **by occurrence index** (not by `(ch,verse)` key, because duplicate verse numbers exist — e.g. Ps 36 has 40 rows / 38 distinct numbers). A per-chapter `len(geez) == len(en)` + sequence-equality self-check is the cheap guard; a chapter that fails **drops out** of the tier rather than render a misaligned page. → renders the two-column parallel reader.
- **Gate B — geez-ready (DEFERRED to Phase 3).** Real Geʽez, internally complete. → single-column Geʽez reader. **Not emitted in Phase 1.** ⚠ Must NOT use `canonical_book_shape(book)` naively: it **raises `FileNotFoundError`** for Tewahedo-distinctives (`1en/jub/4ba/mq1-3` have no KJV skeleton) and 62 Psalms chapters are LXX-short of the KJV count — completeness must be judged by the **store's own internal extent**, not the KJV table (see §9).
- **Everything else — non-clickable, no page emitted:** `partial` (present but below its own complete extent) and `source` (nothing transcribed) render as the plain/dimmed cells they are today, with a tooltip and **no link**.

A **build-time assertion** backstops it: before writing `dist/`, every reader-link target file must exist (a dead/empty link **fails the build**), and link-emission and page-emission must read from **one** coverage source so they can never disagree.

## The reader page (layout)
- **Parallel two-column, per-verse rows.** Geʽez **left** (`lang="gez"`, **LTR** — Ethiopic is left-to-right, *not* RTL; Noto Serif Ethiopic, already wired at `style.css:55`), literal English **right** (EB Garamond body default). One shared verse number per row in a narrow gutter (verse keys are identical both sides — verified). Because Geʽez rows render taller (1.12em / 1.7 line-height), use **per-verse paired rows**, never fixed-height side-by-side columns, so alignment holds.
- **NOT interlinear** — we have verse-level, not word-level, alignment; interlinear would over-claim. **NOT a toggle** — it adds JS and a second render path, breaking dep-free/static purity for zero Phase-1 value.
- **Mobile:** pure-CSS grid `1fr 1fr` collapsing to a single stacked column under ~640px (Geʽez verse, then its English directly beneath). No JS.
- **Plain, reverent (constraint #3):** one additive `.rdr-*` block in `style.css` reusing the existing parchment/gold/ink palette and double-rule headers. No new visual vocabulary, nothing gaudy.
- **Geʽez-only chapters (Phase 3)** reuse the same template, single-column.
- **Per-page provenance:** each reader page carries the same honest source/attribution line the EPUBs and the progress page do (manuscript + edition), and labels the English a *literal back-translation reading-aid*, never a substitute scripture. The English divine name renders **"Yahweh"** for `እግዚአብሔር`, per the `-en` store convention.

## Navigation & progress UI — two levels
- **`pill (geez.html) → book index (read/geez/<book>.html) → chapter reader (read/geez/<book>/<ch>.html)`.**
- **`geez.html` stays the BOOK-level overview, unchanged in structure** — pills gain a link only where a reader exists; the per-chapter detail does **not** clutter it (a 151-cell Psalms wall belongs one level down).
- **The per-book chapter heatmap lives on the book index** (`read/geez/<book>.html`), reusing the existing `pb-grid` / `pb-cell` / `_bar` / legend builders with reader-specific cell classes (`rdr-parallel` / `rdr-geez` / `rdr-partial` / `rdr-source`) + an "*X of Y chapters readable*" bar. A drill-down belongs where the reader has committed to a book.
- **Chapter reader** has prev/next limited to **clickable siblings only** + back-links to the book index and `geez.html`.
- **URL/file scheme:** `read/geez/<book>/<ch>.html` (chapter) and `read/geez/<book>.html` (book index) — names the language track so a future Amharic reader is `read/amharic/...` with zero collision. Deterministic, stable filenames so per-regen git diffs stay minimal (one added verse must not reshuffle a file). Phase-1 page count ≈ **168 chapter pages + 7 book indexes**.

## Data-format facts the renderer must honor
- Verses are 3-arity tuples `(chapter:int, verse:int, text:str)`; **text is plain** (0 of 2531 verses carry any HTML) — the renderer escapes it and wraps the Geʽez run in `lang="gez"`. Ethiopic word-divider `፡` (U+1361) and full-stop `።` (U+1369) are **content**, kept as-is.
- `VERSIFICATION = "own"` in both stores; pairing is by **exact key in exact source order**, with **intentional duplicate `(ch,verse)` keys and preserved gaps** → pair **positionally**, never by dict-key.
- Sam/Kings books carry a `*_apparatus.json` own→KJV crosswalk (anchored/interpolated) — **not needed** for the basic Geʽez|English reader; it is the bridge if a future feature wants a KJV-numbered English column.

## Testing / verification
- **Unit (pytest):** per-chapter coverage computation pins the verified truth — **168 parallel-ready chapters / 3,032 verses**, Psalms = 151/2531, the six small slices, duplicate-verse survival (Ps 36 = 40 rows), and the gate rejecting any length/sequence mismatch. The renderer escapes text, sets `lang="gez"`, and degrades to single-column when English is absent.
- **Structural honesty test:** a non-ready chapter emits no page; every emitted pill/cell link has an existing target (the build-time assertion, also covered as a unit on the coverage map).
- **Render/visual (self-serviceable loop):** `node website/build.mjs` → `python -m http.server` → Playwright screenshot of `geez.html`, a book index, and a chapter (Psalm 1, and a duplicate-verse Psalm like 36) — confirm the two columns render, Geʽez uses Noto Serif Ethiopic, the stylesheet loads from the nested `read/` path, pills link only where ready, and mobile stacks. (file-exists is NOT enough for the asset-path check — verify on localhost.)
- **Coherence:** Phase-1 emitted page set == the parallel-ready coverage map; sitemap contains every reader URL.

## Scope (YAGNI)
**Phase 1 (v1):** the parallel Geʽez|English reader for the 168 paired chapters (Psalms-led) + per-book chapter heatmap + pill/cell wiring + the `build.mjs` `read/` pass, `{{root}}` asset-path token, programmatic sitemap, and the build-time honesty assertion + tests + visual QA + deploy. **Phase 2:** a11y/mobile real-device pass (long-chapter scroll e.g. Ps 119, reading-position anchors, screen-reader verse-number semantics) + the regeneration-on-advance release step. **Phase 3:** the Geʽez-only reader (Gate B) for complete Geʽez books, single-column, with the distinctive-book completeness guard. **Phase 4 (future):** an Amharic parallel reader once `amharic-tewahedo-en` is substantial; the don't-commit-`dist/reader/` escape hatch if the committed-dist diff ever becomes the deploy bottleneck. **NOT planned:** interlinear, a render toggle, word-level alignment, animations, a public API, pre-generating the un-transcribed canon. The machine scales by **data**, not by code.

## Open risks (carried into the plan)
1. **Full-canon scale** — a complete reader is eventually thousands of tiny HTML files in both the website repo and `dist/`; stable filenames/byte-ordering keep per-batch diffs small, but the don't-commit-`dist/` escape hatch (Phase 4) may become mandatory at scale.
2. **The wrong counter** — the `_en_books >=50` line-regex **under-counts wrapped tuples** (verified: 1 Kings EN = 21 by regex vs 191 true). Per-chapter readiness must use `chapter_verses_in_source_order` / `_load_book`; document this at the call site and guard it with a test.
3. **`get_chapter` is the wrong grouper** — it returns `(verse, text)` 2-tuples sorted by verse and does **not** dedup, while `_book_index` dedups. Use `chapter_verses_in_source_order` (source-order, duplicate-preserving) and pair by occurrence index with the len self-check.
4. **Gate B distinctive-book trap (Phase 3)** — `canonical_book_shape` raises `FileNotFoundError` for `1en/jub/4ba/mq1-3` and 62 Psalms chapters are LXX-short; judge completeness by the store's own extent.
5. **Subdir asset path** — nested `read/` pages need the stylesheet/fonts via a depth-correct path; a `{{root}}` token (depth-computed in `build.mjs`) preserves both localhost and `file://` preview. Verify on a real localhost/Playwright pass, not file-exists.
6. **Regeneration cadence** — the reader is only as honest as its last regen; re-running + committing the generator after transcription advances must be a **documented release step** (under-claiming is safe; a stale-but-present page after a store *shrinks* is the only unsafe case, partly caught by the build-time equality assertion).

## Constraints carried
Static + dep-free (no server, no PHP, no framework — GitHub Pages); single source of truth (one text origin = the EPUB stores); never over-claim (no page ⇒ no link, by construction); plain manuscript-reverent register reusing `style.css`; byte-disjoint from `build_edition.py` / `epub_working`; collision-free with the re-ingest and audit lanes (touches `website/**` + `scripts/gen_website_*` only). Cross-lane: the generator is portable Python; either lane can build/deploy (pull the publish working copy first).
