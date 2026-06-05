# Ge'ez & Amharic progress page — design (2026-06-05)

**Status:** APPROVED (design) 2026-06-05 — its own website page tracking the Ge'ez/Amharic transcription with an honest **per-book staged grid** + manuscript-source links + a free-will-offering tie-in; **data-driven** from the real store so it can never over-claim. Next: writing-plans.

## Purpose
Give the project's most distinctive work — the **Ge'ez & Amharic Bibles, transcribed from the manuscripts** — its own home on the website: an honest, always-accurate view of exactly where each Bible stands, the manuscripts behind it, and how support accelerates the *free* work. Reinforces the launch message ("9 English editions now; Ge'ez + Amharic coming") with radical transparency, and gives the faith community a place to follow the work.

## The real state — the source of truth (the page MUST NOT over-claim)
- **Ge'ez:** **4 books Bible-ready** — `1ki, 1sa, 2sa, psa` (exactly the standalone build's `_STANDALONE_BOOKS`), own-versified; **English back-translation on 7** (`1ki,1sa,2sa,ex,gen,lev,psa`); the manuscript marathon (1 & 2 Samuel done, Kings underway) feeds more.
- **Amharic:** **source text gathered for 28 books** (as-written from the PD parallel Bible), but **not yet own-versified / assembled** into a standalone Bible (that stage is still ahead).
- The two Bibles are at **genuinely different stages** → a single flat "% complete" would mislead (Amharic would read ~0% despite 28 books of real work) → use a **per-book staged view**.

## The page
A new page `website/src/geez.html` + a nav item **"Ge'ez & Amharic"** in `partials/head.html`. Plain HTML/CSS, matching the existing site (no framework). Sections:
1. **Hero / narrative** — the manuscript work, witness by witness; why it is slow and sacred; honest, warm framing.
2. **Per-Bible summary** — a short headline + small summary bar per Bible (Ge'ez: "4 books Bible-ready"; Amharic: "28 books of source text gathered — assembly ahead").
3. **Per-book status grid** — THE honest core, one grid per Bible in canonical order; each book carries a **stage badge**:
   - ◻ **not started** · ◐ **source gathered** · ◑ **transcribed** (own-versified) · ● **Bible-ready** (own-versified + in the standalone build), with an **EN** mark where English back-translation exists.
   - This is what keeps it honest AND shows the Amharic work (28 books at ◐) instead of a demoralizing 0%.
4. **The sources** — linked manuscripts/archives: Cambridge **CUDL MS Add. 1570** (IIIF), **Patrologia Orientalis**, the **HaCohen** apocrypha — so people can see the real folios behind the work.
5. **"What further support makes possible"** — the free-will-offering tie-in (Ko-fi/PayPal links already live). **★INVIOLABLE:** the Word / digital output ALWAYS stays free; a gift *accelerates* the work (more witnesses collated, more books transcribed, the **Amharic** begun), it never *unlocks* anything.

## Data pipeline (never drifts from reality)
- A build-time generator (`scripts/gen_website_progress.py`, run before `website/build.mjs`) computes **`website/src/data/progress.json`** from the REAL store. Per canonical book, its stage is COMPUTED (never hand-set):
  - **source gathered (◐):** the book exists in `content/translations/{geez,amharic}-tewahedo/<book>.py`.
  - **transcribed / own-versified (◑):** that book file has a `VERSIFICATION =` block.
  - **Bible-ready (●):** the book is in `build_standalone._STANDALONE_BOOKS` for that Bible.
  - **EN mark:** the book exists in `content/translations/geez-tewahedo-en/<book>.py`.
  - Canon order + the full book list from `content/books.yaml` (the Ethiopian Tewahedo canon as the denominator).
- `website/build.mjs` reads `progress.json` and renders the bars + grid at **build time** (server-side stitch — no client fetch; the data is known at build). Mirrors how the site already stitches content.
- Re-running the generator after any transcription progress refreshes the page automatically — the numbers can never lie.

## Honesty constraints
- A book is never shown further along than the store proves; stages are computed from disk, not authored.
- Amharic is shown at its true stage (source-gathered), never inflated to look "done."
- The support ask never implies paying to unlock Scripture.

## Testing / verification
- **Unit:** the generator's stage computation (a book in `_STANDALONE_BOOKS` → ●; with `VERSIFICATION` → ◑; in the store only → ◐; absent → ◻; EN-present → EN mark). Pin the current truth (Ge'ez 4 ●, Amharic 28 ◐, 0 ●).
- **Render/visual:** the project's self-serviceable loop — `node website/build.mjs` → `http.server` → Playwright screenshot of `geez.html`; confirm bars + grid + source links render + the nav item appears.
- **Coherence:** `progress.json` totals cross-checked against the real store counts.

## Scope (YAGNI)
**v1** = the page + per-Bible summary bars + the per-book grid + source links + the support tie-in, all generated from the store. **NOT v1:** animations, historical-progress charts, per-verse granularity, a public API. Presentation refinements are configurable later if wanted.

## Constraints carried
Plain HTML/CSS (no framework — matches the site); honest + warm public copy; the generator is a small pure function (testable); **collision-free with the re-ingest** (website + a `scripts/` generator are file-disjoint from `content/notes/**` + `epub_working/**`).
