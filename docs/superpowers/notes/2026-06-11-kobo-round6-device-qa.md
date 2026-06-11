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

## K-R6-5 — mid-chapter page breaks persist = the K-R5-4 class (unchanged)

Still the file-split necessity (new spine file = Kobo's only honored break).
The presentation OPTIONS remain with Boggy (K-R5-4: (a) verse-boundary cut
points · (b) accept as-is · (c) larger pieces on non-eink targets).

## Round-6 holds (no-news-is-good-news)

- K-R5-3 title-badge clamp HOLDS (no stray badges reported on title pages).
- No teleports observed anywhere (cap + clamp working broadly).
- K-R5-1 font-reset process fix HOLDS (filename reuse preserved Cardo).

## Assignments

- **Mac (build_edition.py + stylesheet arc):** K-R6-3 U+2028 flip · K-R6-4
  eyebrow fix (nbsp ± word-spacing) · + the queued orphan-vnotes drop
  (gate 4j) and K-KIN bisect.
- **WIN:** matrix M1 implementation (per the v1.0.0 assessment + spec-review
  blockers); next Kobo rebuild+swap when Mac's slice lands.
- **USER:** the two K-R6-2 decisive taps (font-size-up re-tap of gen 1:1's
  ◈2/◈8 · split badges at 1sa 16:12 / act 23:6) · gen 35:18 ◈4 re-tap (still
  pending) · K-R5-4 presentation pick whenever · STK retry verdict.
