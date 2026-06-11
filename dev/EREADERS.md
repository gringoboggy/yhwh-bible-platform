# EREADERS.md — the e-reader compatibility tracker

> **The always-there knowledge home for every reader we ship EPUBs to** (user-directed
> 2026-06-10, turn 69): per-reader capabilities, quirks, format requirements, QA
> status, and open questions — so "what does reader X do with feature Y" is one
> lookup, never a re-research. Companion surfaces that MUST agree with this file:
> `TARGET_CAPS` in `scripts/templates/wizard.py` (the machine-enforced capability
> map the wizard gates on) and the format-matrix spec
> (`docs/superpowers/specs/2026-06-10-website-format-matrix-design.md` §2).
> **Maintenance protocol:** every device-QA round, vendor-doc research pass, or
> format-profile change updates this file in the same commit, date-stamped. A claim
> here carries its evidence (QA round / vendor doc / by-execution proof) — no
> folklore.

## Summary table

| Reader | We ship | `target_reader` | Popup footnotes | Collapsible ToC (`<details>`) | Embedded fonts | Page-break CSS | Status (date) |
|---|---|---|---|---|---|---|---|
| **Apple Books** | `.epub` | `tablet` | ✅ pops in place | ✅ (live-verified) | ✅ honored | ✅ honored | Proven — user rounds + Mac live test (2026-06-10) |
| **Kobo e-ink** | `.kepub.epub` (kepubify v4.0.4) | `eink` | ⚠ pops ONLY in kepub; preview declines notes ≥5,500 stripped (pops ≤4,498; fix = cap ~4,400) | ❌ flat (KOReader/crengine by design) | ✅ in book; ❌ in the footnote-preview dialog (follows the READING font — set Cardo) | ❌ none of the 12 properties on e-ink kepub — new spine file = the only break | Round-5 calibration DONE 2026-06-11 (1 anomaly re-tap pending); K-R4-2 cap fix + K-R5-3 clamp fix = Mac |
| **Kindle** | `.epub` via Send-to-Kindle | `kindle` | ❌ no popups → visible endnotes (kindle_safe) | ❌ (KF8/KFX no support) | partial (KFX re-flows) | partial | Variant SHIPPED + epubcheck 0/0/0/0 by execution; user K-KIN-1..4 acceptance PENDING (2026-06-10) |
| **Google Play Books** | `.epub` (library upload) | `everywhere` (provisional) | ❓ unverified — user phone-QA = the gate | ❌ closed-and-stuck (cannot expand) | ❓ | ❓ | UNTESTED — matrix M5 gate (2026-06-10) |
| **Computer & everywhere else** (Calibre, Thorium, ADE, Nook) | `.epub` | `everywhere` / `computer` | ✅ Thorium/Calibre; ⚠ ADE limited | ❌ ADE documents unsupported → gated off | ✅ generally | ✅ generally | The shipped v0.1.0 artifact IS this profile; epubcheck 0/0/0/0 |

## Apple Books (`tablet`)

- **Delivery:** open the `.epub` on iPhone/iPad/Mac — no conversion.
- **Works:** EPUB3 popup footnotes (`epub:type="noteref"`/`aside`); `<details>`
  collapsible ToC (full click round-trip live-verified on the Mac, 2026-06-10
  target-caps research); embedded fonts; page-break CSS; the title-box/edition-page
  layout after the 2026-06-10 fixes.
- **Quirks:** larger default font than Kobo (per-device font sizing shipped in the
  beta device-QA arc); very long `<details>` lists may need scrolling view.
- **QA history:** user Apple Books rounds (2026-06-08..10) + Mac live tests;
  `notes/2026-06-10-target-caps-research.md`.

## Kobo e-ink (`eink` → `.kepub.epub`)

- **Delivery:** the `.kepub.epub` copied to the device (popups REQUIRE the KePub
  artifact — a plain `.epub` won't pop on Kobo). kepubify v4.0.4 PINNED
  (`dev/TOOLCHAIN.md` §kepubify; watch its two gotchas: spurious popups from
  ordinary cross-ref links; aside `id`s must survive the koboSpan transform).
- **The footnote-preview dialog** (the popup): renders TAG-STRIPPED plain text in
  the READING font (NOT the embedded fonts → Hebrew/Arabic/Geʽez/◈ tofu unless the
  user sets a font-pack font like Cardo), and **DECLINES large notes** — instead of
  popping it NAVIGATES to **the containing piece's TOP** (confirmed round 5: all
  five jumps landed exactly at piece tops; a target near its own piece top looks
  like "nothing happened" — Gen 1:1 across 4 artifacts). Threshold NARROWED round-5
  (2026-06-11): **pops ≤ 4,498 · declines ≥ 5,500 stripped chars** — 8/9 tap points
  consistent; the one inversion (gen 35:18, 3,509 → declined) is anomalous on every
  measured axis and awaits ONE re-tap. K-R4-2 fix: cap units **≤ ~4,400 stripped**
  via (a) split-by-category + (b) split WITHIN a note body (`hist` ≈19K = ONE
  Easton note in both worst verses — Mac, 2026-06-10). Calibration tool:
  `dev/kobo_tap_calibration.py`.
- **⚠ Per-book settings reset on NEW files:** a swapped QA artifact with a new
  filename = a new book → the reading-font choice resets to default → tofu
  "regression" that isn't one (round-5 lesson, `notes/2026-06-10-kobo-round5-device-qa.md`
  K-R5-1). **QA swaps now REUSE the on-device filename.**
- **Mitigation for popup fonts:** the **font-pack add-on** (`dist/yhwh-kobo-font-pack.zip`,
  OFL ttf ×5 → device `fonts/` folder; user selects e.g. Cardo as reading font).
- **Page breaks:** Kobo's own epub spec lists **N for all 12 page-break properties
  on e-ink kepub** (decade-persistent; `notes/2026-06-09-kepub-pagebreak-research.md`).
  A NEW SPINE FILE is the only guaranteed break → `apply_file_split` forces
  book-title singleton pieces; piece sizes matter (round-2: 881 KB pieces broke
  rendering; now max ~405 KB / mean ~233 KB).
- **Other quirks:** justification stomps `<p>` text-align (numerals center via an
  inner block); chapter-last badges must clamp before the next heading (the
  round-3 "teleport cluster"); plain-text separators (¶ ◦ •) needed inside merged
  popups because the preview strips all markup.
- **QA history:** device rounds 1–4 (`notes/2026-06-0{9,10}-kobo-round*-device-qa.md`);
  the color Kobo = the real-device eyeball (memory `kobo_color_ereader_end_stage_qa`).

## Kindle (`kindle`, Send-to-Kindle)

- **Delivery:** Send-to-Kindle (email/app/web) — Amazon CONVERTS the EPUB (KFX);
  there is no direct sideload of EPUB on modern Kindles. ⚠ The Mac Kindle app has
  NO local import — it silently MOVES a "sent" file into its container.
- **Delivery checks (hard failures fixed 2026-06-10):** **E999** = multiple
  `<dc:language>` elements → single `en-US` (patch_opf); **E3013** = large
  `display:none` volume → the kindle_safe variant renders notes as VISIBLE
  ENDNOTES (artifact hidden text 486,188 → 955 chars).
- **No popup footnotes** in KF8/KFX → endnotes are the correct presentation;
  `.vn-sep` separators visible.
- **ToC:** chapter pills → plain inline rows (`apply_kindle_toc_rows`); no
  collapsible lists.
- **Seams:** book-boundary "shatter" (K-KIN-3) → seam CSS (forced-break drop +
  title exemption + art re-cap).
- **Gate:** verifier **gate 5 `kindle_safe_checks`** (≤10K effective display:none +
  single dc:language), OPF-stamped via `yhwh:target-reader`; epubcheck 0/0/0/0
  proven by execution on the staged artifact (Mac, Temurin 21).
- **Acceptance PENDING:** the user's Send-to-Kindle re-verify (K-KIN-1..4) on
  `Ethiopian_Bible_catholic-study_kindle-safe_2026-06-10T224859Z.epub`.
- **QA history:** Kindle round-1 (K-KIN-1..4, Mac 2026-06-10) + the E999
  investigation; plan `plans/2026-06-10-kindle-safe-variant.md`.

## Google Play Books (`everywhere`, provisional)

- **Delivery:** upload to the user's Play Books library (web/Android/iOS); accepts
  EPUB 2/3 (3.3 preferred); readable on any signed-in device. EPUB3 feature
  support varies per platform (Google's own caveat).
- **Known:** collapsible `<details>` lists render CLOSED AND STUCK (the one reader
  that locks them; why `toc_expandable` is tablet-only).
- **Unverified:** popup-footnote behavior, embedded-font honoring, page-break
  handling — **the user's offered phone-QA is the acceptance gate** (matrix M5).
- **Profile question (open):** does Play need its own `target_reader` value, or
  does the `everywhere` build hold? Decide from phone-QA round 1.

## Computer & everywhere else (`everywhere` / `computer`)

- **Covers:** Calibre, Thorium, Adobe Digital Editions, Nook, and any standard
  EPUB3 reader. This is the vanilla artifact — the shipped v0.1.0 EPUB.
- **Known:** ADE documents collapsible lists as unsupported (vendor release
  notes); Thorium/Calibre render popups + fonts well; epubcheck 0/0/0/0 under
  EPUB 3.3 is the floor gate for everything we ship.

## Cross-reader invariants

- **One resolver:** every per-reader behavior flows through `target_reader`
  (`scripts/core/…resolve_target_reader`, kindle = 5th value) → `TARGET_CAPS` →
  `build_edition` passes. No second control path.
- **Popups everywhere = `epub:type="footnote"` asides**; what differs is each
  reader's RENDERING of them (pop / preview-strip / endnote) — tracked above.
- **epubcheck 0/0/0/0** on every shipped artifact (WIN: PATH Oracle JRE 1.8 +
  the PyPI jar with `--jar`; Mac: Temurin 21 since 2026-06-10).
- **Format-matrix mapping** (the 5 catalog formats ↔ these readers):
  `docs/superpowers/specs/2026-06-10-website-format-matrix-design.md` §2.

## Open questions (next QA rounds answer these)

1. Kobo preview-decline threshold T — round-5 tap calibration (this session).
2. Play Books round-1: popups / fonts / breaks on the user's phone (M5 gate).
3. Kindle K-KIN-1..4 acceptance on the kindle_safe artifact (user, pending).
4. Whether Play Books needs its own `target_reader` profile (after #2).
