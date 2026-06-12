# Kobo round-6 device QA — findings (K-R6)

**Status:** INGESTED 2026-06-11 (WIN) — user round-6 report + 10 screenshots
(`kobo_img/1..10.png`; 11.heic unread) on the r6 kepub (device swap under the
persistent filename; Cardo persisted, user also tested Publisher Default).
Artifact forensics same-session. HEADLINE: **K-R5-6 PROVEN ON-DEVICE — the
dc:language restore brought every translation script back under Publisher
Default** (the user's regression call was right end-to-end). Split popups
partially work; two new presentation classes inventoried.

## K-R6-1 ✅ CLOSED — K-R5-6 verdict: dc:language IS the Kobo preview's fallback key

User: "translations are back up. works with publisher default for font and
the 3 selected font packs … checked a lot of them out in random spots and
they all work." Screenshots corroborate: Hebrew popup (img 4), **Arabic popup
(img 8/9 — first Arabic EVER confirmed in the preview)**, Publisher Default
selected in the Aa sheet (img 10). Mechanism now settled by execution +
device: the Footnote-preview dialog picks per-script fallback fonts from the
**OPF `dc:language` declarations** (per-span `lang` never survives the
tag-strip). The unconditional drop was the regression; the target-gated
restore (+`ar`) is the durable fix. EREADERS updated to PROVEN.

## K-R6-2 — split-unit popups: 1 of gen 1:1's 3 units opens; SIZE THEORY DEAD as sole factor

Gen 1:1 now renders ◈2 ◈5 ◈8 (split landed, badges + titles correct in
artifact). User: only ◈5 (part 2) opens. Forensics (same file
`index_split_000_02.html`, adjacent badges, markup shape identical):

| badge | aside id | stripped | raw | koboSpans | links | device |
|---|---|---|---|---|---|---|
| ◈2 | `vnotes-gen-1-1` | 4,349 | 8,086 | 64 | 3 | ✗ no open |
| ◈5 | `vnotes-gen-1-1-s2` | 2,626 | 8,747 | 84 | 12 | ✓ pops |
| ◈8 | `vnotes-gen-1-1-s3` | 2,537 | 9,266 | 98 | 9 | ✗ no open |

- **No measurable axis separates them**: the failing ◈8 is SMALLER than the
  popping ◈5; the popping unit has the MOST internal links; koboSpan counts
  non-monotonic. (Echoes the gen 35:18 anomaly — still awaiting its re-tap.)
- **⚠ gen 1:1 cannot distinguish "decline" from "missed tap"** — it sits at
  its own piece top, so the decline-fallback (navigate to piece top) is a
  visual no-op there. "No teleportation anywhere" (user) is consistent with
  the cap working broadly.
- **Tap-geometry hypothesis now live**: three adjacent ~glyph-width
  superscript noterefs separated by single spaces; e-ink tap resolution may
  simply miss the outer badges.
- **Decisive next taps (USER, both cheap):**
  1. Bump the reading font size UP a few steps (bigger badge hit-targets),
     re-tap ◈2 and ◈8 at gen 1:1. Open now = tap geometry; still dead =
     a real second decline factor (its content becomes the specimen).
  2. Tap split badges at a MID-PIECE verse — 1sa 16:12 or act 23:6 (tap-list
     carryover) — where a decline TELEPORTS visibly vs a dead tap does
     nothing.

## K-R6-3 — `\n` separators COLLAPSED by the dialog → flip to U+2028

The 953 `\n`-leading vn-sep spans are in the artifact (verified r6 staging),
but popups still read run-on ("no formatting to look nice still"). The
extractor collapses `\n` like HTML whitespace. **Fix (Mac, coded as the
planned fallback): switch `_VN_SEP_*` to U+2028 LINE SEPARATOR** (keep the
visible ¶ ◦ • marks — if U+2028 also collapses they remain the only
structure).

## K-R6-4 — "BOOKII": the eyebrow CSS eats the word space (PRE-EXISTING, every title page)

User: no space between BOOK and the roman numeral on every title page
(img 7: "BOOKLXIV" on Hebrews). Forensics: the markup is CORRECT — one text
node `BOOK LXIV` inside a single koboSpan; CSS `.bookpage-eyebrow
{ font-variant: small-caps; letter-spacing: 0.22em; font-style: italic }` is
byte-identical in v0.1.0 / r5 / r6 → pre-existing render quirk of Kobo's
kepub engine under that combo (newly inventoried, not a regression). **Fix
(Mac, stylesheet arc), belt-and-braces:** replace the eyebrow's word space
with `&#160;` (nbsp) at the base's 87 `bookpage-eyebrow` sites (engine-proof)
and/or add `word-spacing: 0.35em` to the eyebrow rule; A/B next device round.
Check Apple Books renders unchanged (it currently honors the space).

## Round-6b (user follow-up, same r6 artifact) — K-R6-2 geometry REFUTED + K-R6-6 NEW

- **K-R6-2 tap-geometry hypothesis REFUTED**: font-size-up does NOT make
  gen 1:1's ◈2/◈8 open — "they get clicked but nothing happens" (taps
  register, no popup). A real per-unit decline factor exists; gen 1:1 still
  masks decline-vs-dead (self-landing). **THE decisive datum is now the
  mid-piece tap**: act 23:6 (badge at 7% of a 645KB piece — a decline jumps
  visibly back; best) or 1sa 16:12 (3% of 151KB) — each renders SIX badges
  (◈1 ◈1 ◈1 ◈1 ◈2 ◈1, design-b body chunks). Record per badge: pops / jumps
  back / nothing. gen 1:2 (◈12+◈1) + gen 1:26 (◈1/◈7/◈5) add cheap
  position-pattern data (gen 1:1's middle-pops shape).
- **K-R6-6 (NEW) — the ◈ glyph has NEVER rendered on Kobo** (user,
  definitive: "badge has always not shown up on kobo" — any font, incl.
  Cardo; in-page badges display as bare superscript numbers). The font-pack
  note's "covered by Kobo's own UI fonts" claim was wrong. **USER PREFERENCE
  captured: "whatever is most logical but if we have so many pop ups maybe
  badges only instead of numbers."** Design (Mac, stylesheet/build arc; the
  presentation-configurable doctrine): **CSS-chip badge** — style the in-page
  `.marker-badge` as a small bordered chip (border+radius+padding; CSS
  applies in the book view everywhere incl. Kobo) with the count inside, and
  DROP the ◈ character from the badge text on eink (no glyph dependency =
  the K-R2-3 "configurable badge glyph" follow-up solved without a glyph).
  Option-gated (`marker_badge_style: chip | glyph+count`), default chip on
  eink via TARGET_CAPS, others keep ◈+count (Apple renders ◈ fine). Chips
  also visually separate badges from verse numbers — the user's clutter
  point.

## K-R6-5 — mid-chapter page breaks persist = the K-R5-4 class (unchanged)

Still the file-split necessity (new spine file = Kobo's only honored break).
The presentation OPTIONS remain with Boggy (K-R5-4: (a) verse-boundary cut
points · (b) accept as-is · (c) larger pieces on non-eink targets).

## Round-6 holds (no-news-is-good-news)

- K-R5-3 title-badge clamp HOLDS (no stray badges reported on title pages).
- No teleports observed anywhere (cap + clamp working broadly).
- K-R5-1 font-reset process fix HOLDS (filename reuse preserved Cardo).

## Round-6c (USER, 2026-06-11 evening — build identity + re-taps)

- **r6 on-device CONFIRMED by behaviour:** translations/popups work (the
  Arabic/lang-declarations restore is r6's signature — r5's were broken).
  The library entry showed no "unread" reset, as expected: the load reused
  the device filename, which preserves Kobo's read state (worth noting in
  every future load: same-name swap = no unread badge; rename = new entry).
- **gen 1:1 ◈2/◈8 (units 1/3 + 3/3): STILL DEAD on re-tap** — counts visible
  as bare numbers, taps do nothing, ◈5 (2/3) opens. Third independent
  confirmation; gen 1:1 remains non-diagnostic (self-landing) — the
  mid-piece taps below stay the decisive datum.
- **K-R6-6 reconfirmed: NO ◈ glyphs anywhere** (bare superscript counts
  only) — the Mac's chip-badge fix (`marker_badge_style: chip` on eink,
  shipped post-r6) is the cure; ships in round-7.
- **K-R6-4 reconfirmed on-device: "BOOK<numeral>" runs together on EVERY
  title page (all numerals, not one book)** — expected on r6 (the bug is
  the kepub engine eating the space under the small-caps styling; the
  emitter-level nbsp fix shipped post-r6, pinned in
  tests/test_eyebrow_renumber.py for the general pattern). Cure: round-7.

## Assignments

- **Mac (build_edition.py + stylesheet arc):** K-R6-3 U+2028 flip · K-R6-4
  eyebrow fix (nbsp ± word-spacing) · + the queued orphan-vnotes drop
  (gate 4j) and K-KIN bisect. (All landed post-r6 — bundle into round-7.)
- **WIN:** matrix M1 implementation (per the v1.0.0 assessment + spec-review
  blockers); next Kobo rebuild+swap when Mac's slice lands. (M1+M2 SHIPPED
  2026-06-11; round-7 build once the cap verdict lands.)
- **USER (remaining decisive set):** split badges at **1sa 16:12 / act 23:6**
  (mid-piece — a refused popup TELEPORTS visibly; a dead tap doesn't) ·
  **gen 35:18 ◈4** re-tap (still pending) · K-R5-4 presentation pick
  whenever · STK retry verdict. (gen 1:1 re-tap: DONE round-6c, still dead.)
