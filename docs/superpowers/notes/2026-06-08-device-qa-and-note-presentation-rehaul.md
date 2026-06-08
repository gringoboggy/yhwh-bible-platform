# Device-QA (Apple Books, the v0.0.3 posted EPUB) + note-presentation rehaul — design

**Source:** the user's own real-device run of the full posted EPUB, 2026-06-08, with **8
screenshots** (Desktop `IMG_0167–0172, 0176, 0177`).
**Status:** FINDINGS-ONLY. These FEED the post-merge fix phase (the round-6 hold is still
in force) — nothing applied yet. Build/app items routed to the WIN lane (build/EPUB/app
domain) per RULES guard #6; the note-presentation rehaul (4+5) is a Mac-led design,
build-time + completeness-preserving + configurable.

## The wins (user)
"Very close to the vision." Dark themes look great (IMG_0167). Notes cleaned up a lot.
**No more random empty pages.** "Very very very decent." "Just about almost perfect."
The reading view + inline note-count badges (◆N = N notes on that verse; Gen 1:1 = ◆19)
render cleanly.

## Findings (with screenshot evidence)

### 1. In-EPUB expandable ToC — a USER ON/OFF TOGGLE; expandable as default; smaller pills; tune books-per-section. [WIN · build]
- **IMG_0176:** the current ToC is a FLAT `book → page-number` list ("The Ethiopian
  Tewahedo Study Bible", Corinthians 789, Galatians 532, …). User wants the *expandable*
  pill ToC back; on expand, chapter pills currently reflow onto the next page.
- **User-directed (RULES §2):** the expandable in-EPUB ToC is itself a builder / `/customize`
  **ON/OFF toggle** — readers pick expandable-pills vs the plain list; **default = expandable
  ON.** Pill size + books-per-section also builder options.
- **Assessment:** reflowable EPUB → the reader owns pagination, so "N books per page"
  can't be pinned exactly. Mitigate: (a) smaller pills (less padding/line-height); (b)
  `break-inside: avoid` on each book block so a book + its expanded pills don't split a
  page; (c) optional soft section breaks.
- **Effort:** moderate (CSS + ToC generator in `build_edition.py`). Verify canon-filtered
  + real device.

### 1b. ⭐ ROOT CAUSE of the ToC spacing — justified text should be the EPUB DEFAULT, and justification must be SCOPED OFF the ToC. [WIN · CSS — high impact, low risk]
- **Observed (user):** the justified body text that makes IMG_0167 look great is NOT the
  EPUB default — the user enables "justified" in the READER app. But the reader's justify
  toggle is GLOBAL → it also justifies the ToC, spacing the book-name lines out horribly
  (huge inter-word gaps). So #1's ToC problem and "I have to toggle justify" are ONE issue.
- **Fix (solves both):** ship `text-align: justify` as the EPUB's OWN default for prose
  (verse + note bodies) so the user never needs the reader toggle; AND explicitly
  `text-align: left/start` the ToC, chapter pills, headings, tables, and the stats view so
  they never justify. With publisher-justified body, the reader stays on "default"
  alignment → it no longer force-justifies the ToC → book names stay tight. Pair body
  justify with `hyphens: auto` (+ `-webkit-hyphens`) so justification doesn't open rivers.
- **Byte-stability:** CSS change → a builder option (`text_align`), default justify+hyphenate
  for the Ethiopian (shipped) edition; the 9 KJV byte-stable editions keep left unless
  flipped (or re-baseline intentionally). ToC/pills/headings are ALWAYS left, not subject
  to the option.
- **Effort:** small CSS, big perceived-quality payoff. Verify the reader-override
  interaction on a real device.

### 2. "Your-Edition" stats popup renders broken (full-page, misaligned table). [WIN/shared · app/EPUB — real bug]
- **IMG_0177:** the "Your-Edition" view shows a per-book NOTE-COUNT table (Genesis 4,903 /
  Exodus 3,642 / Leviticus 2,578 / …). The **book-name column is pushed off the left edge**
  — only the right-aligned counts are visible for most rows (first ~5 names show, rest are
  blank + a floating number column). User: touching the notes on the My-Edition page brings
  up this whole-page "spreadsheet" popup.
- **Assessment:** a layout/overflow bug in the stats table (the label column collapses /
  scrolls off; the modal takes the full page). Relates to `edition_stats` (round-6 also
  flagged its stale cache). Needs render-then-diagnose: reproduce the tap, capture the
  popup, find the handler + the CSS table rule. Likely a contained fix once located.
- **Effort:** small–medium once reproduced.

### 3. Book title-page box bleeds onto the next page when reader font is increased. [WIN · CSS — partly inherent]
- **Observed:** the box around a book's title/picture bleeds onto the next page at larger
  reader fonts. User: "still looks decently clean," maybe unfixable.
- **Assessment:** largely inherent to reflowable EPUB + user font scaling. Mitigate (not
  eliminate) with `break-inside: avoid` on the title box + viewport-relative sizing. Known
  title-page item (deferred-by-design: render-then-diagnose; CSS already centered — do NOT
  blind re-center). Expect reduction, not zero at extreme fonts.
- **Effort:** small CSS attempt + render check; accept residual.

### 4 + 5. NOTE REDUNDANCY → a note-presentation rehaul (build-time, lossless, staged). [Mac-led design · build impl = WIN]
**Concrete redundancies seen (Gen 1:1, ◆19 notes):**
- **Attribution stated up to 3× (IMG_0168):** `◇ Ephrem the Syrian (360).` → bold
  **`Ephrem the Syrian` Commentary on Genesis (c. 360 AD)** → body `"Ephrem reads…"`.
  Easton ×2 (IMG_0169): `⌂ Easton. Dictionary (Easton's).`.
- **Category prefix repeated on every note (IMG_0170/0171):** `Hebrew. … Hebrew. …
  Hebrew. …` — the user's exact "make a title/category, put everything under it."
- **Same word described twice (IMG_0170 vs 0171):** בְּרֵאשִׁית as `B'reshit` AND
  `Bereshit — 'In the beginning'`; בָּרָא as `Bara' and the LXX choice` AND `Bârâ'`. Two
  near-identical linguistic notes per word, from different sources/passes.
- **Topic notes duplicated, internally + across sources (IMG_0172):** `Topics: CREATION,
  EARTH, GOD, HEAVEN, HEAVEN` (HEAVEN ×2) AND a 2nd Topic note `Creation, Creation,
  Denunciations against, Heaven` (Creation ×2) — Nave's + Torrey both firing on the verse.

**Design principle (non-negotiable):** north star = the FULLEST Bible. Group + dedup must
PRESERVE all distinct scholarship — collapse only TRUE redundancy (repeated attribution /
category prefixes; identical or near-identical bodies; duplicate topic terms). Never drop a
distinct point.

**Staged plan (cheapest/safest first; each a builder option, default-on for the Ethiopian
Bible, gated so the 9 KJV editions stay byte-identical when unset). User has OK'd doing the
combining in the builder.**
- **S1 — Attribution de-dup (build-time, ZERO info loss, HIGH impact).** In the per-verse
  aside-merge (`apply_badge_markers`): render each source/author ONCE as a byline; drop the
  redundant "(360)" / "a note by X" wrappers. Ephrem ×3 → ×1. Lowest risk — do first.
- **S2 — Group a verse's notes by CATEGORY → SOURCE (build-time, ZERO info loss).** One
  header per category (Word study / Commentary / Cross-reference / Topic / Dictionary /
  Harmonization), entries beneath WITHOUT repeating the prefix. Directly answers the user's
  "title + everything under it." The notes already carry category icons/labels (◇ ⌂ ⌘ ▌ ⚖ ○
  ✦) — group on those.
- **S3a — Topic-note dedup (build-time, easy, safe).** Within a Topic note dedup the term
  list (HEAVEN,HEAVEN → HEAVEN); merge the two topic-index notes (Nave's + Torrey) into ONE
  "Topics: …" union. Cheap, obviously correct — good early win alongside S1.
- **S3b — Collapse NEAR-identical linguistic/commentary bodies within a verse (careful).**
  Detect near-dup bodies (the בְּרֵאשִׁית/בָּרָא twins) via a similarity heuristic; keep the
  fullest, optionally footnote the alternate source. High threshold; guard hard against
  dropping distinct notes. This is the "some work" part.
- **S4 — Semantic combine across sources (the genuine rehaul; defer, opt-in).** Cluster /
  synthesize when many sources comment on a verse. Risky for completeness + heavy (LLM build
  pass). Only after S1–S3b prove out.

**Why build-time, not re-ingest:** S1–S3 act on rendered notes at build → no re-writing the
91,733 stored notes; additive; reversible; option-gated so byte-stability holds. Verify each
stage byte-stable on KJV + visually on eth + a real device.

## Routing (RULES guard #6)
- Items 1–3 (ToC / stats-popup / title-page) → **WIN lane** (build + EPUB + app; needs SSD
  builds + epubcheck + device verify) for the post-merge fix phase.
- Items 4–5 → **Mac-led design** (this doc → a follow-on spec); build impl on WIN. Both lanes
  aware via the board.
- All gated behind the round-6 findings-only hold → fold into the ONE post-merge fix phase.
