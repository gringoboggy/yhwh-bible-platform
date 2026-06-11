# Kobo round-5 device QA — findings + forensics (K-R5)

**Status:** INGESTED 2026-06-11 — user round-5 report (10 screenshots,
`kobo_img/1..10.png`) + same-night artifact forensics (r5 kepub vs the archived
v0.1.0 kepub, `E:\kobo-archive`). HEADLINE: **no build regression** — every
probed aside/badge/title-piece is byte-identical across the two artifacts; the
"went back in time" symptoms decompose into one device-setting reset + two
pre-existing (newly inventoried) classes + a genuinely narrowed popup-decline
bracket. Fix assignments at the bottom.

## K-R5-1 — "translations don't work" + missing ◈/category glyphs = the READING-FONT RESET (not a bug)

Every translation popup opened but showed box-runs for Hebrew/Greek/Geʽez
(img 5) and boxes before "Topical" etc. (img 9/10); in-page badges showed the
count without ◈. Forensics: the aside content, language lines, and the literal
`◈N` badge text are all present and byte-identical to v0.1.0 — and English
renders fine. Root cause: **the r5 kepub is a NEW book to Kobo, so the
per-book reading font reset to the default**, which lacks ◈ + the original
scripts; the Footnote-preview dialog follows the reading font (K-R2-3, proven
in rounds 3–4 with Cardo set). **User action: set the reading font to Cardo
on the new book** (the font pack is still on the device). **Process fix
(adopted): QA swaps REUSE the on-device filename** so per-book settings
persist across rounds — verify next swap.

## K-R5-2 — the ◈-badge popup decline: bracket NARROWED to 4,498 < T ≤ 5,500 (one anomaly)

The round-5 taps (translation popups all popped; ◈ note popups split):

| verse | stripped | raw html | koboSpans | result |
|---|---|---|---|---|
| 1ch 24:10 | 3,300 | 7,149 | 58 | **P** |
| gen 1:3 (r4) | 3,067¹ | 11,191 | 104 | **P** |
| jos 11:1 | 4,498 | 11,245 | 100 | **P** |
| gen 35:18 | 3,509 | 9,226 | 82 | **J → piece top (ch34)** ← the anomaly |
| gen 2:18 | 5,500 | 16,235 | 148 | J → piece top (ch1) |
| gen 41:51 | 6,442 | 12,695 | 99 | J → piece top (41:36 region) |
| gen 1:26 | 7,417 | 21,522 | 195 | J → piece top (ch1) |
| 1sa 1:20 | 8,074 | 13,375 | 89 | J → piece top (1sa ch1) |
| gen 1:1 | 9,058 | 25,276 | 234 | N = J → its own piece top (self) |

¹ gen 1:3 re-measured on r5 (round-4's 3,313 was the old artifact's unit).

- **Every J landed exactly at its piece's top** — the failed-pop fallback
  (confirms the K-R3-4 mechanism; gen 1:1's "nothing" = navigating to its own
  piece start; **3rd–4th artifact in a row**, user-noted — same class, not new).
- **Size separates 8 of 9 points**: pops ≤ 4,498; declines ≥ 5,500.
  **gen 35:18 (3,509) is the single inversion** and stays inverted on raw
  bytes, koboSpan count, p-count, link locality, badge markup, badge→aside
  distance, and piece locality — every measurable axis matches the popping
  asides. → **ONE user re-tap of gen 35:18's ◈4 badge** decides: mis-tap
  (size theory clean, set the cap from T≈4.5–5.5k) vs reproducible (a second
  decline factor exists; its content becomes the key specimen).
- Refuted this night by measurement: pure badge→aside distance (P at 212k
  delta vs J at 88k), in-aside link resolvability (0 unresolved everywhere),
  missing `epub:type="noteref"` (present everywhere, markup identical).
- **K-R4-2 fix parameter:** cap each popup unit at **≤ ~4,400 stripped chars**
  (just under the proven-pop 4,498) pending the 35:18 re-tap; design =
  (a) split-by-category + (b) split WITHIN a note body (Mac's prep: `hist`
  ≈19K = ONE Easton note in both worst verses). 195/66,683 asides over 3,313;
  re-run `dev/kobo_tap_calibration.py` post-fix as the gate-4g calibration.

## K-R5-3 — book-boundary badge spill ×38 (PRE-EXISTING, now inventoried)

Every book's title page carries the PREVIOUS book's last-verse ◈ badge
(Samuel title ← `vnotes-rut-4-22`; 1 Chronicles ← `vnotes-2ki-25-30`; 38
sites total, identical in v0.1.0 — img 8). The K-R3 chapter-clamp bounds a
chapter-last badge "before the next heading", but for a BOOK-last verse the
next heading sits in the NEXT book's title singleton piece. (r5 actually
IMPROVED the class: v0.1.0's Ruth/Zephaniah/Mark titles carried extra stray
`vnote-*` cross-refs the xref retarget removed.) **Fix:** clamp must bound at
the book/piece boundary; add the title-piece-carries-no-badges check to
`dev/verify_kr2_build.py` (gate 4h, fires-on-defect proven on r5).

## K-R5-4 — mid-chapter page breaks = file-split piece boundaries (180 sites; options for Boggy)

180 of 393 r5 pieces start mid-content (170/381 in v0.1.0 — the class is the
K-R2 file-split necessity: a new spine file is Kobo's ONLY honored break, and
pieces cap at ~400 KB for renderer stability). Presentation OPTIONS (builder
options per the presentation-doctrine, user picks the default):
(a) prefer verse-boundary cut points (no mid-verse/mid-paragraph cuts) —
cheap, removes the "weirdly aligned" landings; (b) accept chapter-misaligned
breaks as-is (paper Bibles break mid-chapter too); (c) larger piece caps on
non-eink targets (the matrix's per-format builds make this natural).

## K-R5-5 — regression sweep CLEARED

r5 vs v0.1.0: all probed asides byte-identical (size/structure/badges/links);
piece counts 393 vs 381 (the deliberate base mutations); title-spill set
identical-or-improved. The round-7 audit + fix pass introduced NO device
regressions on any probed surface (audits ran Opus/Fable per the standing
model rule).

## Assignments

- **Mac (owns `build_edition.py` + stylesheet this arc):** the K-R4-2 cap fix
  (a)+(b) at ≤~4,400 stripped (pending the 35:18 re-tap verdict) + the
  K-R5-3 book-boundary clamp fix + gate 4h.
- **WIN:** matrix M1 (CI workflow + catalog) per the v1.0.0 assessment;
  EREADERS §Kobo updated this commit.
- **USER:** set Cardo on the new book → re-check one translation popup +
  one ◈ badge glyph; ONE re-tap of gen 35:18's ◈ badge; (whenever)
  Send-to-Kindle K-KIN-1..4.
