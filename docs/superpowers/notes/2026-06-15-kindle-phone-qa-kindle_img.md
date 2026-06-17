# Kindle phone QA — `~/Desktop/kindle_img/` (2026-06-15)

**Status:** documented only; no code/build work (M3 Kobo fan-out in progress on Mac).

**Source:** 12 iPhone screenshots (`IMG_0415`, `IMG_0431`–`IMG_0441`) from Send-to-Kindle
reading on the phone Kindle app.

**Artifacts loaded (confirmed):** Mac M4 STK spot-check pack on Desktop —
`~/Desktop/YHWH-kindle-stk-qa/` (see `README.txt`, 2026-06-14).

| # | File | Edition |
|---|------|---------|
| 01 | `01-ethiopian-tewahedo-superset-navy.epub` | **Screenshots in `kindle_img/`** |
| 05 | `05-scholarly-academic-navy.epub` | Same badge/teleport issues as 01 |
| 06 | `06-eastern-orthodox-forest.epub` | Same issues **+ tinted background panel** (0444/0445) |

SHA256 (match `build/matrix/` catalog artifacts):  
`01` = `b86a0867…` · `05` = `c3674fed…`  
Superset-scale in reader: **772,444 locations** total (IMG_0415 et al.).

## User-reported issues (confirmed in images)

### 1. Popups broken / “teleport” on tap — **NOT random; page-break aligned**

- **Editions:** confirmed on **#01 ethiopian navy** and **#05 scholarly navy** (same behavior).
- User pattern (2026-06-15, scholarly opened): badge taps do **not** open popups. They jump to
  the **last verse before the next chapter page-break**, where the chapter’s `notes-section`
  begins and the screen shows a **broken partial page** (e.g. Gen 3 ends ~¼ down; ch 4 on next
  page). Landings observed:
  - Genesis badges → **Gen 3:24** (end ch 3)
  - After ch 4 page-break, all badges in region → **Gen 8:10** (end ch 8 / before ch 9)
  - After ch 9 → **Gen 11:26** (end ch 11; 11:27 continues next page)
- **Translation markers:** two badges before a verse → **no action**. Other taps skip the
  translation (`vnote-*` Hebrew/Greek popup) and land on **verse-end study notes** (`vnotes-*`).
- **EPUB forensics (scholarly STK file):** each landing verse is the **chapter-last verse** in
  its split piece, immediately followed by `<aside class="notes-section" hidden="">` holding
  `vnote-*` (translation) + `vnotes-*` (collapsed badges) asides; next chapter is
  `<p class="ch-heading">` with `page-break-before: always` (often **next spine file**).
  Example: `v-gen-3-24` + notes-section at tail of `index_split_000_02.html`; `ch-b00-c4` opens
  `index_split_001_00.html`.
- **Working theory:** Kindle KFX **mis-resolves internal `#` anchors** across forced chapter
  page-breaks + per-piece `notes-section` blocks — all `noteref` taps in a paginated “screen”
  collapse to the **first aside anchor at that break** (3:24, 8:10, 11:26…), not the intended
  target. Matches codebase intent that markers+asides must stay same-file for popups (Kobo);
  Kindle ignores that contract.
- **Images:** Genesis 3 (`IMG_0438`–`IMG_0440`) — dense inline badges; no popup UI.
- **Fix direction (deferred):** Kindle presentation fork — suppress inline markers; move study
  + translation content to **end-of-chapter/book notes** (M3 Kobo model). Turn-87 STK 6/6 PASS
  did not gate link-target correctness on phone.

### 2. Eastern Orthodox forest — background panel under text (edition-specific)

- **Images:** `IMG_0444` (Gen 1 scripture), `IMG_0445` (in-content ToC).
- **User:** same badge/teleport issues as superset; **additionally** a warm beige/tan
  **rectangle behind all text** (scripture + ToC), with a visible edge/border on ToC.
- **Artifact:** `06-eastern-orthodox-forest.epub` (STK pack #06).
- **Root cause (EPUB forensics):** edition `theme: devotional` → merged
  `content/themes/devotional.css` sets `body { background: #fffbf3; }`. Ethiopian navy
  (`theme: classic`) has **no** body background — no panel. Scholarly navy (`theme:
  scholarly`) also has no body background. Kindle KFX paints the `body` fill as a
  content-area panel against the reader’s native page colour.
- **Fix (shipped in `kindle_post`, 2026-06-15):** `strip_body_backgrounds()` removes
  `background` / `background-color` from all `body` CSS rules during `make_kindle_safe`.
  Rebuild + re-STK to pick up (catalog artifacts pre-fix still carry `#fffbf3`).

### 3. Too busy — inline badges / “Kobo-like”

- User: hoped Kindle would not look like Kobo chip density; open to **end-of-book study
  notes** model (same direction as current M3 Kobo Bibles) if inline cannot work.
- **Images:** `IMG_0438` (Gen 1:1–10) — purple numbered ovals after nearly every clause;
  `IMG_0439`/`IMG_0440` (Gen 3) — circled superscripts in tight clusters (②③ … ⑯).
- **Note:** Busy appearance is **markers visible in scripture**, not ToC chapter grids alone.

### 4. Table of contents — cramped numbers, uneven pages

- **Images:** `IMG_0415` (Pentateuch), `IMG_0431`–`IMG_0435` (prophets → Revelation),
  `IMG_0436` (Clement 1–65 grid).
- Pattern: book title (brown, underlined) + **single-space** blue chapter number rows;
  long books wrap to 2+ lines; short books leave large empty bands → uneven vertical rhythm.
- Clement gets a **standalone 4-row grid** (65 links) — extreme case of density.

### 5. Bottom-left “page” numbering strange

- **Images:** consistent Kindle **Location N of 772444** + **1%** (not EPUB page-list
  1, 2, 3…). Examples: Location 101 (`0415`), 718 (`0432`), 1141 (`0439`), 1166 (`0440`).
- `IMG_0441` (Reference Tables): **“1 minute left in chapter”** + 79% — Kindle time/progress
  mode, not a build bug.
- User expectation mismatch: may need copy/UX note that Kindle never shows sequential pages
  for this delivery path unless we add a `page-list` (KFX may still ignore).

### 6. Reference tables — Kindle auto-expand (works)

- **Image:** `IMG_0441` — small brown square with white arrows under LENGTH and WEIGHT
  tables. **Not a bug:** Kindle phone app adds this automatically for HTML `<table>`
  content. Tap expands the table full-screen (“expand graphs”). Our back-matter is plain
  `reftables.xhtml` (`class="reftable"` in `scripts/matter_pages.py`) — no Kindle-specific
  markup required.

## Screenshot index

| File | Content |
|------|---------|
| IMG_0415 | ToC — Genesis–Deuteronomy |
| IMG_0431 | ToC — Amos–Haggai |
| IMG_0432 | ToC — Zechariah–Acts |
| IMG_0433 | ToC — Romans–1 Thess |
| IMG_0434 | ToC — 2 Thess–1 Peter |
| IMG_0435 | ToC — 2 Peter–Revelation |
| IMG_0436 | ToC — 1 Clement (1–65 grid) |
| IMG_0437 | Section opener — BOOK I / First Book of Moses (cover art) |
| IMG_0438 | Scripture — Genesis 1 (dense purple oval markers) |
| IMG_0439 | Scripture — Genesis 3:8–14 (circled markers) |
| IMG_0440 | Scripture — Genesis 3:15–22 (mixed marker styles) |
| IMG_0441 | Back matter — Reference Tables + arrow icons |
| IMG_0444 | Eastern Orthodox forest — Gen 1 + **body background panel** |
| IMG_0445 | Eastern Orthodox forest — ToC in **bordered beige box** |

## Next session — Kindle presentation fork (M4b prep)

**User goal:** Kobo-like split — **translation popups in scripture**, **study notes elsewhere**.
Kobo reference (WIN turn 93, shipped): `vn-link` → translation popup; per-category study
badges → **Study Notes glossary** backmatter (`K-R9b/c`), not inline footnote popups.

**Kindle reality:** KFX has no true popup footnotes (`dev/EREADERS.md`, wizard `TARGET_CAPS`).
Phone QA proves inline `noteref` taps **collapse to chapter page-break anchors** (3:24 → 8:10
→ 11:26…), not intended targets. STK 6/6 PASS gated delivery only, not link UX.

**Proposed fork (config-gated `target_reader` / `kindle_post` extension — design first):**

1. **Study notes:** suppress ◈/numbered inline markers; move to end-of-chapter or
   end-of-book glossary (mirror K-R9c navigation model where STK-safe).
2. **Translations:** keep verse-number `vn-link` only; try per-verse inline `vnote-*`
   placement (not chapter-tail `notes-section` batching) → STK phone test for reliable
   jump-to-translation (not overlay popup). Fallback: end-of-chapter “Translations” block.
3. **ToC:** revisit cramped chapter-number rows (separate from marker fork).
4. **Gate:** extend Kindle device QA — Gen 1/3 badge taps, translation badges, page-break
   landings; keep `verify_kindle_safe` + epubcheck 0/0/0/0.

**Artifacts for repro:** `~/Desktop/YHWH-kindle-stk-qa/` (01 navy + 05 scholarly; SHA256 =
`build/matrix/`). Screenshots: `~/Desktop/kindle_img/`.

**After M4b STK green (user device-QA queue):** Mac → **M2 Apple** (build/QA prep per
`docs/superpowers/notes/2026-06-15-apple-m2-layout-directive.md` — keep original inline
badge model; polish popups only; user tests Apple) · WIN → **M5 Play Books** (build/QA prep;
user tests Play Books on phone).

## Deferred triage (completed / folded above)

- Edition confirmed: #01 ethiopian navy (`b86a0867…`); scholarly #05 same issues.
- Reference tables: Kindle auto-expand on `<table>` — works (`IMG_0441`).

## Scholarly (#05) slow first-open vs Ethiopian (#01)

User reports `05-scholarly-academic-navy.epub` takes **much longer** to load/open the first
time than `01-ethiopian-tewahedo-superset-navy.epub`.

**On-disk STK pack** (`~/Desktop/YHWH-kindle-stk-qa/`, SHA256 = `build/matrix/`):

| Metric | 01 Ethiopian navy | 05 Scholarly navy |
|--------|-------------------|-------------------|
| File size | 26 MiB | 26 MiB |
| Uncompressed zip | ~120 MiB | ~111 MiB |
| Spine `itemref` | **403** | 378 |
| HTML parts | 404 | 379 |
| `vn-sep` spans (all html) | **245,732** | 184,603 |
| `noteref` (all html) | 67,126 | 66,875 |
| Genesis split bytes | 400,938 | 400,229 |

Ethiopian is the **heavier** artifact by every build metric — so slow scholarly first-open
is unlikely a “bigger EPUB” problem.

**User timing (2026-06-15, corrected):** both files were **already sent** and appear in the
Kindle phone library. This is **first open inside the app** (not the STK upload step).
Navy superset (#01) ≈ **10 s** to readable; scholarly (#05) **≥2 min** at ~**40%** on the
in-app progress bar (still in flight).

**What the in-app % bar usually means on phone:** even after STK, the title is often
**cloud-only** until first tap — the app then **downloads the KFX to local storage** and
builds its index. That combined step is what shows the progress bar.

EPUB-side compare (source before/after Amazon KFX — we cannot see KFX on disk):

| Metric | #01 Ethiopian | #05 Scholarly |
|--------|---------------|---------------|
| Spine items | 403 | 378 |
| Total `<a>` links in HTML | 191,495 | **210,116** (+10%) |
| S2 note-cascade CSS | yes | no |
| `vn-sep` spans | 245,732 | 184,603 |

Scholarly is a **smaller** EPUB but a **denser link graph** — plausible that Amazon’s KFX +
the app’s first-open indexer work harder even though upload MiB matches.

Other factors: CDN variance, phone busy/thermal, #01 already local after first open so
#02 feels slower by comparison.

**If stuck:** let bar reach 100%; if frozen >15 min, delete local copy (keep in cloud) and
re-open to re-download. After both are local, second open should be instant.

**README mismatch:** pack `README.txt` asks to “tap a verse footnote popup” and “ToC pills
expand horizontally” — phone QA shows neither works; popups teleport, ToC is flat chapter rows.

## K-R9c parity sketch (Mac turn 108 — findings-only, no code)

**Kobo shipped model (K-R9b/c):** scripture keeps `vn-link` translation popups; study
categories collapse to end-of-chapter **Study Notes** glossary navigation — not inline
`noteref` popups on every badge.

**Kindle gap:** KFX has no true footnote overlay (`dev/EREADERS.md`). Phone QA shows inline
`noteref` taps **teleport to chapter page-break anchors** (Gen 3:24 → 8:10 → 11:26) because
Kindle mis-resolves `#vnote-*` / `#vnotes-*` across `notes-section` blocks + forced
`page-break-before` splits. STK 6/6 gated delivery only.

**M4b fork proposal (mirror K-R9c where STK-safe):**

| Surface | Kobo (K-R9c) | Kindle M4b target |
|---------|--------------|-------------------|
| Translation | `vn-link` popup at verse start | Keep `vn-link`; try per-verse inline `vnote-*` (not chapter-tail batch) — phone STK gate |
| Study notes | Glossary backmatter; badges navigate | Suppress inline ◈/numbered markers; end-of-chapter or end-of-book study block (no `noteref` in scripture) |
| Presentation | `kindle_post` N/A | Extend `make_kindle_safe` branch: `reader_kindle_study_inline` off (default) |
| QA gate | Kobo tap round | Gen 1/3 badge taps + translation badges + page-break landings; `verify_kindle_safe` + epubcheck |

**Config hook (design):** `target_reader: kindle` + edition flag
`reader_kindle_study_backmatter: true` (default off for byte-stability) → `kindle_post`
suppresses inline study markers and emits STK-safe backmatter links. **HOLD implementation**
until WIN Phase 3 + merged audit plan approved.

## Lane note

Mac M3 fan-out **41/45** at time of capture (`coptic-orthodox` in epubcheck). Do not stack
Kindle rebuilds or full pytest until fan-out completes.