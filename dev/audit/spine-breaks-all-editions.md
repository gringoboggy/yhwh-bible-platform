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
| **standalone geez** | *(building)* | *(building)* | — |
| **standalone amharic** | *(building)* | *(building)* | — |

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

## Cross-edition observations

- The mid-chapter count tracks note density, not canon: the superset ethiopian (130) >
  the canon-filtered study editions (109–111), because more notes per chapter → more 400 KB
  overflows. WIN's "merge per-book up to the measured Kobo limit" fix collapses all of
  these to ≤ chapter-boundary breaks.
- Chapter-boundary (WARN) breaks are 35–42 per edition — the base `index_split` chapter
  splits + intended book-title pages. The user's model keeps book-title breaks; whether to
  also merge across base chapter boundaries is the "measure the Kobo limit" question (WIN).

## Status / remaining

- ✅ 4 study editions × {eink, tablet*, kindle*} from existing artifacts (*partial per the
  matrix). epub≡kepub confirmed.
- ⏳ **standalone geez + amharic** — no built artifacts on disk → building eink (the affected
  platform) to complete the edition coverage; results appended below.
- ⏳ **cross-OS verify of WIN's re-cut** — pending WIN landing the packer fix (rebuild on
  macOS → `audit_spine_breaks.py` mid-chapter == 0 + golden re-baseline holds).
