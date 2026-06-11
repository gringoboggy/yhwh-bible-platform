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

## Round-5b (2026-06-11, user follow-up — Cardo set on-device)

User report after setting the reading font to Cardo on the r5 book:

- **K-R5-1 CONFIRMED on-device** — Greek + Hebrew popups render again with
  Cardo set. The font-reset theory is proven; the "translations broken"
  regression is closed. (◈ badge glyph not yet re-confirmed — still pending.)
- **K-R5-6 (NEW, ★REAL REGRESSION — the user was right) — the round-7 audit's
  unconditional `dc:language` drop broke the Kobo preview's script fallback.**
  The user was POSITIVE all translations (incl. Arabic) had rendered under
  Publisher Default before the deep-audit fixes — and the artifact diff proves
  a real candidate the K-R5 forensics never probed (it compared asides/badges,
  not the OPF): **v0.1.0 declares `en-US + hbo + grc + arc + gez`; r5 declares
  `en-US` only** (measured by execution on both kepubs). Timeline locks it:
  the multi-language block was ADDED 2026-06-09 as the K-R2-5 fix (`63f3cc99`,
  between rounds 2 and 3 — round-2's recorded Publisher-Default tofu was on
  the PRE-declaration artifact), rode rounds 3–4 + v0.1.0, then the turn-67
  Kindle-E999 fix #1 dropped it **unconditionally** (`build_edition.py`
  `patch_opf`, "the in-content language info already rides per-span
  xml:lang"). That justification fails for Kobo: the per-span `lang` tags DO
  exist (r5 spine: `lang="ar"/grc/he/la` ×88/file) but the preview dialog is
  a TAG-STRIPPING extractor — markup-level lang never reaches it; the OPF
  declarations were the only language signal it could key fallback fonts on.
  Mechanism-consistent with every observation: v0.1.0 + Publisher Default =
  fallback fonts engage = everything renders; r5 + Publisher Default = no
  declarations = tofu; Cardo rescues only its own scripts (Greek/Hebrew, no
  Arabic/Ethiopic glyphs). **Fix (Mac — `patch_opf` is this arc's file):
  target-gate the drop** — single `en-US` ONLY when `is_kindle_target`
  (E999 is Amazon's validator, nobody else's); every other target RESTORES
  the multi-value block, **adding `ar`** (truthful: the Van Dyck Arabic popups
  exist per-span ×88/file; the old block oddly lacked it — if v0.1.0's Arabic
  really rendered, Kobo's fallback may engage book-wide once multi-lang is
  declared; declaring `ar` removes the doubt either way). Re-true the bcp47
  single-lang pin to kindle-only; verifier gate 5 (single dc:language) already
  judges kindle artifacts only. **Device gate (round 6): Publisher Default +
  one Hebrew + one Arabic popup on the rebuilt kepub.** Contingency if the
  restore does NOT revive Publisher Default: the merged pan-script reading
  font (Cardo + Noto Naskh + Noto Serif Ethiopic via `fontTools.merge`, fresh
  OFL name; needs a user-OK'd `fonttools` install — guard #1).
- **K-R5-7 (NEW) — run-on popups persist WITH the separators present.**
  Verified in the r5 artifact: `vn-sep` ×900+ per spine file (K-R3-2 + K-R4-1
  both shipped). The single-char marks (¶ ◦ •) give structure but no LINE
  BREAKS — the stripped preview still reads as one wall. **Round-6 experiment
  (Mac — rides the K-R4-2 edit):** bake a literal newline into each vn-sep
  span text (`<span class="vn-sep">\n¶ </span>` etc.). Everywhere CSS applies
  the span is display:none so the change is invisible; if the eInk extractor
  preserves raw text the popup gains real line breaks. If `\n` collapses, the
  fallback variant is U+2028 LINE SEPARATOR. Cheap, idempotent-safe (the
  existing negative lookaheads key on the span opener).
- **gen 1:1 "still doesn't open" = K-R5-2 as expected** — 9,058 stripped is
  over the decline floor; the tap self-lands at its own piece top. Unchanged
  until the K-R4-2 cap fix lands (Mac, round 6).

## Assignments

- **Mac (owns `build_edition.py` + stylesheet this arc):** ★the K-R5-6
  `dc:language` restore (target-gated: single `en-US` kindle-only; all other
  targets get the multi-value block back + `ar`; re-true the bcp47 pin) +
  the K-R4-2 cap fix (a)+(b) at ≤~4,400 stripped (pending the 35:18 re-tap
  verdict) + the K-R5-3 book-boundary clamp fix + gate 4h + **the K-R5-7
  newline-separator experiment** (one-line change to the `_VN_SEP_*`
  constants + `add_vnote_preview_separators`, same files).
- **WIN:** matrix M1 (CI workflow + catalog) per the v1.0.0 assessment —
  now folding in the Mac spec review's 4 blocking classes; EREADERS §Kobo
  updated this commit; the merged pan-script font ONLY as the K-R5-6
  contingency (needs a user-OK'd `fonttools` install).
- **USER:** ✔ Cardo set (round-5b) — still pending: one ◈ badge glyph check
  under Cardo; ONE re-tap of gen 35:18's ◈ badge; round-6 Publisher-Default
  re-check (one Hebrew + one Arabic popup) once the restore ships;
  Send-to-Kindle K-KIN-1..4 (1st try failed after ~1h crunch — retry in
  flight, Mac board turn 71).

## Round-6 build (2026-06-11, Mac turn 71) — the assigned fixes SHIPPED

All four Mac items landed in one slice (TDD; tests named in the commit):

- **K-R4-2 ✅** `apply_badge_markers` now splits any over-cap merged popup
  into units ≤ `note_popup_split_cap` (default **4,400** stripped; 0 = off;
  /customize + API wired) at category boundaries — design (a) — and chunks a
  single over-cap note body at depth-0 sentence boundaries with visible
  ⋯ continuation marks + (i/k) part headers — design (b). One unit = the
  historical byte-identical path. Round-6 kepub: max verse-notes unit
  **4,368** (was 19k+); gate 4g green (one honest warn: vnote-1ki-12-24 at
  6,937 — the un-probed translation-popup class, round-5 taps all popped).
- **K-R5-3 ✅** the badge clamp bounds at `<div class="book-title-page"` —
  artifact: **0** title pieces carry badges (was 38); gate 4h green +
  fires-on-defect proven on synthetic zips both ways.
- **K-R5-6 ✅** `patch_opf` target-gates the dc:language drop: single en-US
  ONLY for kindle; everyone else restores en-US+hbo+grc+arc+gez **+ ar**.
  bcp47 pin re-trued (test_opf_clean).
- **K-R5-7 ✅** every `_VN_SEP_*` span now leads with a literal `\n` (U+2028
  is the fallback if the device collapses it).
- **NEW class caught by the round-6 gates + fixed:** the K-R4-2 byte-shift
  moved a 400KB cut between a spill-duplicate anchor (`v-1en-106-1-x2`) and
  its aside → 1 PROMOTED noteref. `split_html_document` now CLONES the aside
  into the referencing piece under a suffixed id (`--cNN`) + retargets the
  local href. Round-6 rebuilt: **66,694 noterefs all-resolve, 0 promoted,
  0 dup-ids, ALL GATES GREEN on epub AND kepub; epubcheck 0/0/0/0.**
- **Kindle (K-KIN round 2):** 2nd Send-to-Kindle try failed after ~50 min →
  full artifact forensics in `notes/2026-06-11-kindle-stk-failure-forensics.md`
  (ranked causes + one-variable bisect ladder; Kindle Previewer = the local
  oracle, NEEDS USER GO). Belt-and-braces shipped: `apply_kindle_unhide`
  strips `hidden=""` from footnote wrappers on kindle targets (3 odd-template
  `verse-refs-section` pieces had 692k chars of popups under [hidden]); gate
  5 extended to fail any kindle artifact still carrying one.

**Round-6 device tap-list (USER):** Publisher Default + one Hebrew + one
Arabic popup (K-R5-6 verdict) · one ◈ badge glyph under Cardo · gen 35:18
re-tap (K-R5-2 anomaly) · 1sa 16:12 / act 23:6 ◈ badge rows (the split worst
cases) · any book title page (K-R5-3 spot-check).
