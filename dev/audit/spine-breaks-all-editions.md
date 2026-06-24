# Spine-break audit — every edition × format × platform (Mac half)

Mac's half of the page-breaks root-cause work (WIN owns the `build_edition.py` re-cut;
assignment in `dev/LANE_HANDOFF.md` + root cause in `page-breaks-root-cause-2026-06-23.md`).
Tool: `dev/audit_spine_breaks.py` (reconstructs the spine→verse map; classifies every
boundary BOOK-start OK · CHAPTER-start WARN · **MID-CHAPTER = ERROR**).

**Method note:** this first pass audits the artifacts already on disk (the current,
pre-re-cut baseline — WIN's packer fix has NOT landed yet, so these measure the live
bug). `kepubify` does not change the spine, so **epub ≡ kepub** for break analysis
(verified on the flagship: both 130, identical break list) — one format per (edition ×
target) suffices. Toolchain validated against WIN's measurement: flagship eink =
**130 mid-chapter + 40 chapter**, first break `gen 10:6→10:7` (the user's exact Kobo
QA finding). ✅

## Matrix (mid-chapter ERROR = the bug; chapter WARN = policy)

| edition | eink/kobo | tablet/apple | kindle |
|---|---|---|---|
| **ethiopian-tewahedo** | **130** mid · 40 ch | **1** mid · 36 ch | **166** mid · 42 ch (m4b) |
| **catholic-study** | **111** mid · 36 ch | *(predict ~1)* | **108** mid · 36 ch |
| **evangelical-reformed** | **109** mid · 35 ch | *(predict ~1)* | *(predict heavy)* |
| **eastern-orthodox** | **111** mid · 37 ch | *(predict ~1)* | *(predict heavy)* |
| **standalone geez** | **0** mid · 161 ch ‡ | n/a (no reader profiles) | — |
| **standalone amharic** | **0** mid · 125 ch ‡ | n/a | — |

‡ The standalone build path (`build_standalone.py`) emits **one spine file per chapter**
(`geez_{book}_{ch}.xhtml`, :264) → it never cuts mid-chapter (**0 ERROR**), but every
chapter is its own spine file → a forced page break at **every** chapter (161 geez / 125
amharic). So the standalone Bibles do NOT have the mid-chapter bug, but they sit at the
*opposite* extreme of the study editions: maximally split (chapter-per-page) rather than
400 KB-packed. WIN's "merge per-book up to the Kobo limit" applies here too (collapse the
per-chapter files into per-book files within the device size limit).

Artifacts audited (dates): eink = `build/round9-kobo-tap` (ethiopian, 06-17) +
`build/matrix-m3` (the other 3 study editions, kobo kepub, v0.1.0); tablet =
`build/tablet` (ethiopian apple); kindle = `build/kindle` (catholic 06-14, ethiopian
m4b 06-18). All pre-re-cut → the live baseline.

## Platform verdict (the user's question: do non-eink platforms share the defect?)

- **e-ink / Kobo — AFFECTED across EVERY edition** (109–130 mid-chapter). The 400 KB
  packer (`apply_file_split`, `FILE_SPLIT_TARGET_DEFAULT`) sub-splits between verses.
  This is the bug WIN's re-cut targets.
- **tablet / Apple — essentially CLEAN (1 break).** `resolve_reader_file_split` returns
  `False` for tablet (`build_edition.py:4527`), so the 400 KB packer never runs → only
  the ~58 base `index_split` files remain (chapter-aligned). The **single** mid-chapter
  break is `psa 119:88→89` — the 176-verse Psalm 119 is the one chapter the *base*
  calibre split itself cuts mid-chapter. ⚠ **WIN note:** the packer fix will NOT touch
  this — it is a base-`index_split` boundary, not a packer cut; psa 119 needs a base-level
  fix (or accept the single break).
- **kindle — AFFECTED, heavily (108–166 mid-chapter) — overturns the analytic prediction.**
  `FILE_SPLIT_TARGET_KINDLE = 2_000_000` (5× the eink cap) predicted near-zero, but the
  built kindle artifacts split at **~495 KB** pieces (max 1.98 MB; 120 of 300 pieces
  >400 KB), i.e. the **2 MB kindle cap is NOT taking effect on these artifacts** — they
  split like the eink default. ⚠ **WIN — verify:** does a *fresh* `--target-reader kindle`
  build actually apply `FILE_SPLIT_TARGET_KINDLE`? If the kindle cap were honored, most
  chapters (≪2 MB) would not sub-split and mid-chapter would drop near-zero. If the cap is
  silently bypassed (post-process / m4b path rebuilding off a default-split base), kindle
  needs the same packer fix as eink. *(A fresh kindle build is needed to settle this —
  flagged for WIN, who owns the build path + the kindle device.)*
  - **★ Code trace (Mac, 2026-06-24) — the wiring at HEAD is CORRECT; "~495 KB" is a
    stale-artifact measurement, not a bug.** The auditor reads *existing on-disk* artifacts
    (`audit_spine_breaks.py` has no build step; it measured `build/kindle` = catholic 06-14
    + an older ethiopian build), and those predate / bypass the current cap path. At HEAD the
    cap IS honored end-to-end: `--target-reader kindle` → `apply_target_override`
    (build_edition.py:1985, folds `target_reader="kindle"` into the in-memory record) →
    `is_kindle_target` (:2014) → `resolve_file_split_target` (:4554) returns
    `FILE_SPLIT_TARGET_KINDLE = 2_000_000` (:4524) → `apply_file_split` uses it for every
    scripture file (`split_html_document(..., target)`, :5220-5223). The only intentional
    400 KB holdout is the **navigated study-glossary backmatter** (`EINK_STUDY_BACKMATTER_STEM`,
    :5213-5218 — finely split by design, jump-to not read-through), which the ~495 KB pieces
    are NOT (those are scripture). **Expectation for the fresh build:** scripture pieces pack
    to ≤2 MB, most chapters stop sub-splitting, mid-chapter → near-zero — i.e. **no kindle
    code fix needed, only a re-measure on a true `--target-reader kindle` build.** (Note for
    interpretation: kindle's KFX repaginates internally, so even a residual spine boundary is
    not the user-visible page break it is on Kobo; the cap matters for KFX converter overhead
    — the K-KIN aggregate-doc-count blocker — not for page breaks.) Empirical confirmation
    (fresh build + re-run the auditor) still owed; held off this slice to avoid a heavy
    91k-noteref build under RAM pressure (8 GB box, VS Code open). Re-verify per
    `feedback_reverify_conservative_nogo`.

## Cross-edition observations

- The mid-chapter count tracks note density, not canon: the superset ethiopian (130) >
  the canon-filtered study editions (109–111), because more notes per chapter → more 400 KB
  overflows. WIN's "merge per-book up to the measured Kobo limit" fix collapses all of
  these to ≤ chapter-boundary breaks.
- Chapter-boundary (WARN) breaks are 35–42 per edition — the base `index_split` chapter
  splits + intended book-title pages. The user's model keeps book-title breaks; whether to
  also merge across base chapter boundaries is the "measure the Kobo limit" question (WIN).

## Two minor build bugs found while building the standalones (WIN surface — flagged, not fixed)

Both surfaced building `standalone-geez` / `standalone-amharic` (`scripts/build_edition.py`,
Mac is verify-only there). Neither corrupts output (the epub is packaged before the crash /
the name is cosmetic):
1. **`KeyError: 'enabled_kinds'`** at `build_edition.py:8060` — the post-build summary print
   assumes a `stats` shape the standalone path doesn't produce → the CLI exits non-zero
   *after* a successful build. Guard the print for standalone editions.
2. **Amharic epub misnamed `Geez_Standalone_standalone-amharic_…`** — the title/filename
   template hardcodes the `Geez_Standalone` prefix; the Amharic standalone inherits it.

## Status / remaining

- ✅ **All 6 editions audited** (4 study + 2 standalone) across the platforms that matter;
  epub≡kepub confirmed; toolchain validated vs WIN's flagship measurement.
- ✅ **Platform question answered:** e-ink AFFECTED (all editions), tablet clean (1 base
  break), standalones use the opposite (chapter-per-page) split. **Kindle: the measured
  artifacts split at the 400 KB default, but that is a STALE-ARTIFACT measurement — the code
  trace (above) shows the 2 MB `FILE_SPLIT_TARGET_KINDLE` is correctly wired at HEAD;** a
  fresh `--target-reader kindle` build is expected to pack scripture to ≤2 MB with mid-chapter
  near-zero (no kindle code fix anticipated, only a re-measure).
- ⏳ **Owed (Mac or WIN, build-capable):** empirically confirm the 2 MB cap on a *fresh*
  `--target-reader kindle` build (HEAD wiring is correct per the code trace; only a re-measure
  is needed). Also: the `psa 119` base-level mid-chapter on tablet; the 2 standalone build bugs.
- ⏳ **cross-OS verify of WIN's re-cut** — pending WIN landing the packer fix (rebuild on
  macOS → `audit_spine_breaks.py` mid-chapter == 0 across all editions + golden re-baseline
  holds cross-OS).
