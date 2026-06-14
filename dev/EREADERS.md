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
| **Kobo e-ink** | `.kepub.epub` (kepubify v4.0.4) | `eink` | ⚠ pops ONLY in kepub; cap-split units mostly pop (K-R6-2: a non-size factor or tap geometry on 2 of gen 1:1's 3 — taps pending) | ❌ flat (KOReader/crengine by design) | ✅ in book; preview dialog = reading font + **`dc:language`-keyed fallback — PROVEN round-6** (Publisher Default renders Heb/Grc/**Ar**/Geʽez with the OPF block restored; per-span lang never reaches the tag-stripped preview) | ❌ none of the 12 properties on e-ink kepub — new spine file = the only break | Round-6 2026-06-11: ★K-R5-6 restore PROVEN on-device; clamp HOLDS; `\n` seps collapsed → U+2028 (K-R6-3); "BOOKII" eyebrow space quirk (K-R6-4, pre-existing) |
| **Kindle** | `.epub` via Send-to-Kindle | `kindle` | ❌ no popups → visible endnotes (`display:none` stripped) | ❌ (KF8/KFX no support) | partial (KFX re-flows) | partial | Recipe DEVICE-PROVEN via Send-to-Kindle (2026-06-14); productized as `kindle_post` (everywhere build + strip-hidden + single `en-US` + OCF re-zip); catalog artifacts reproduce it, epubcheck 0/0/0/0 |
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
  the READING font — embedded fonts and per-span `lang` tags never reach it (the
  extractor strips all markup). **The OPF `dc:language` declarations govern its
  per-script FALLBACK fonts — PROVEN round-6 (2026-06-11):** with the multi-value
  block restored (`en-US + hbo + grc + arc + gez + ar`, target-gated kindle-only
  drop) every translation script renders under Publisher Default AND any pack
  font — including the first-ever Arabic popups (K-R6-1 screenshots). History:
  the block was the K-R2-5 fix; the turn-67 Kindle-E999 fix dropped it
  unconditionally → the K-R5-6 regression the user caught. The dialog also
  collapses `\n` in text (K-R6-3 — U+2028 is the next separator variant) and
  **DECLINES large notes** — instead of
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
  no direct EPUB sideload on modern Kindles. ⚠ The Mac Kindle app has NO local
  import — it silently MOVES a "sent" file into its container.
- **★ The PROVEN recipe (turn-84, 2026-06-14, USER-CONFIRMED on the REAL
  Send-to-Kindle channel).** A *minimal* post-process over a STANDARD everywhere
  build DELIVERS where the elaborate `--target-reader kindle` variant FAILED:
  physically strip every `display:none`/`visibility:hidden` (CSS + inline), LEAVE
  the Kobo-only `.vn-sep` spans intact (Mac turn-85 correction: with their hide
  rule stripped they ARE the visible language separators in the popups — the
  measured june10recipe.epub KEPT all 132,949; dropping them is FIXED.epub/FAIL
  behavior), collapse `dc:language` → single `en-US`, LEAVE `hidden=""` intact,
  OCF re-zip (mimetype first/stored). ≈25.3 MiB, epubcheck 0/0/0/0.
- **What the variant got WRONG (now dormant, not deleted):** the Kindle-Previewer-
  oracle extras — source-label compaction, a 2-popup language cap, `apply_kindle_
  toc_rows`, `apply_kindle_unhide`, the `_KINDLE_SAFE_CSS` append, the 2 MB split —
  were exactly what BROKE Send-to-Kindle (the `FIXED.epub` failure). The Previewer
  + epubcheck passed them; Amazon's ingestion did not. Minimal beat clever.
- **Productized (WIN turn-85, 2026-06-14):** `scripts/core/kindle_post.py`
  (`make_kindle_safe` + `verify_kindle_safe`) + driver `scripts/build_kindle.py`;
  `build_format_matrix` builds the Kindle column as the everywhere base + this
  post-process (the FORMAT_MATRIX `kindle` row carries `post_process: kindle_safe`;
  `target_reader` stays `kindle` for the catalog label). Windows catalog artifacts
  reproduce the device-proven recipe byte-faithfully (catholic-study: **~25.3 MiB,
  epubcheck 0/0/0/0, `verify_kindle_safe` clean, K-R2 gates green, 132,949 vn-sep
  spans KEPT, 7 CSS hides stripped, 6 `dc:language` → 1**).
- **No popup footnotes** in KF8/KFX → visible endnotes are the correct
  presentation; stripping `display:none` makes the note sections render inline.
- **Gate:** `scripts/core/kindle_post.verify_kindle_safe` (zero raw
  `display:none`/`visibility:hidden`, single `dc:language`, `mimetype` first/stored)
  + epubcheck 0/0/0/0 + `dev/verify_kr2_build.py` (gates 1–4; the artifact is
  unstamped, so the dormant variant's gate-5 correctly skips).
- **Acceptance:** the RECIPE is device-proven (2026-06-14, Mac-built artifact, user
  Send-to-Kindle). The Windows catalog artifacts are byte-faithful reproductions of
  that recipe; ONE Send-to-Kindle re-confirm on a catalog artifact is the remaining
  nicety before the column is declared "live."
- **QA history:** the june10 recipe (test-2) → turn-82 forensics (the Previewer/KP3
  oracle was falsified) → turn-84 STK re-proof → turn-85 productization. The dormant
  variant's plan: `plans/2026-06-10-kindle-safe-variant.md`.

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
