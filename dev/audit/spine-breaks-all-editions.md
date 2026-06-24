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

## ★★ POST-PART-2 FINAL — full fix verified cross-OS on macOS (2026-06-24)

WIN's **Part-2** (`2c3a7899` — `_merge_scripture_base_files`: concatenate a book's scripture
base files so a book the calibre base split across `index_split` files is contiguous, then shard
at `FILE_SPLIT_CEILING` = 8 MB → **one spine file per book**; EINK target only) is in HEAD. Mac
rebuilt all 6 editions on macOS (`--target-reader eink --force`), re-ran `audit_spine_breaks.py`,
and ran **epubcheck** on each.

| edition (fresh eink build) | mid ERROR | chapter WARN | book OK | pieces | epubcheck F/E/W/I | verdict |
|---|---|---|---|---|---|---|
| **catholic-study** | **0** | **0** | 71 | 72 | **0/0/0/0** | ✅ PASS |
| **evangelical-reformed** | **0** | **0** | 65 | 66 | **0/0/0/0** | ✅ PASS |
| **eastern-orthodox** | **0** | **0** | 74 | 75 | **0/0/0/0** | ✅ PASS |
| **ethiopian-tewahedo** | **0** | **0** | 77 | 77 | **0/0/0/0** | ✅ PASS |
| standalone-geez | 0 | **0** ✅ | 3 | 4 | 0/0/0/0 | ✅ PASS (Part 2b) |
| standalone-amharic | 0 | **0** ✅ | 0 | 1 | 0/0/0/0 | ✅ PASS (Part 2b) |

**✅ THE PAGE-BREAK DEFECT IS RESOLVED ACROSS ALL EDITIONS — CROSS-OS CONFIRMED.** Every study
edition + both standalones now have **ZERO mid-chapter AND ZERO chapter-boundary breaks** — only
the intended book-title breaks (one spine file per book; `pieces == book_breaks [+1 nav]`).
**epubcheck 0/0/0/0 on all six.** `test_file_split.py` **54/54** + `test_build_standalone.py`
**57/57** on macOS. Reproduces WIN's Windows result exactly (study catholic 0+0; standalone-geez
4 pieces 0+0; standalone-amharic 1 piece 0+0). The weeks-long "page breaks throughout the Bibles"
defect is **closed for all 6 editions.**

> **Part 2b update (2026-06-24, `ff7c3544`):** WIN merged the standalone Bibles per-book
> (`pack_book_chapters` in `build_standalone.py` — the standalones use the separate `build_standalone`
> path that Part-2's `apply_file_split` merge never reached). standalone-geez **161 → 0** (4 books →
> 4 spine pieces), standalone-amharic **125 → 0** (psalms → 1 piece); epubcheck 0/0/0/0; per-chapter
> `#ch-{book}-c{ch}` TOC anchors preserved. Cross-OS verified on macOS — the ‡‡‡ residual below is
> CLOSED.

‡‡‡ **STANDALONE RESIDUAL — ✅ CLOSED by Part 2b (`ff7c3544`), 2026-06-24** (history retained below).
~~The two standalone
Bibles still show chapter-per-page breaks (geez 161 / amharic 125, e.g. `1ki 1:52 → 1ki 2:1
(geez_1ki_2.xhtml)`) because **Part-2's merge lives in `apply_file_split` (the study-edition path),
which the standalones do NOT use** — `build_standalone.py` emits one spine file per chapter
(`geez_{book}_{ch}.xhtml`). So Part-2 correctly did not touch them (mid stays 0, epubcheck clean),
but the standalone Ge'ez/Amharic Bibles will still force a page break at **every chapter** on Kobo.
**▶ Part-2b (WIN): apply an equivalent per-book merge to the standalone build path** (collapse the
per-chapter `geez_{book}_{ch}.xhtml` files into per-book spine files ≤ the same `FILE_SPLIT_CEILING`).
Until then the standalones remain at the chapter-per-page extreme of the pre-Part-1 matrix.~~ →
**DONE: WIN shipped this as Part 2b (`pack_book_chapters`); cross-OS verified 0+0 on macOS (above).**

## ★ POST-PART-1 RE-BASELINE — fresh macOS builds, Part-1 applied (2026-06-24) — *intermediate snapshot (Part-1 only); superseded by the POST-PART-2 FINAL above*

WIN's **page-break Part-1** (`39d04301` — dropped the `_VN_LINK_RE` verse-level cut so the
packer never splits between verses) is applied. Mac rebuilt all 6 editions from source on
macOS (`--target-reader eink --force` for the 4 study editions; standalones via their own
path) and re-ran `audit_spine_breaks.py`. **Full per-edition break lists (the Part-2 spec
input) → `dev/audit/spine-breaks-post-part1.json`.**

| edition (fresh eink build) | mid-chapter ERROR | chapter WARN | pieces | build s | Δ mid (pre→post) |
|---|---|---|---|---|---|
| **catholic-study** | **1** ‡‡ | 163 | 238 | 436 | 111 → 1 |
| **evangelical-reformed** | **1** ‡‡ | 159 | 226 | 389 | 109 → 1 |
| **eastern-orthodox** | **1** ‡‡ | 164 | 242 | 392 | 111 → 1 |
| **ethiopian-tewahedo** | **1** ‡‡ | 186 | 266 | 689 | 130 → 1 |
| **standalone-geez** | 0 | 161 | 165 | 10 | 0 → 0 (unchanged) |
| **standalone-amharic** | 0 | 125 | 126 | 2 | 0 → 0 (unchanged) |

‡‡ The lone remaining mid-chapter ERROR is **identical on all 4 study editions**:
`psa 119:88 → psa 119:89  (index_split_035_00.html)` — the documented **BASE calibre-split
artifact** (Psalm 119, the longest chapter, is cut at the source `index_split_035` file
boundary), **not** a packer cut. **Part-2's per-book merge fixes it for free** (merging psa's
base files). So Part-1 drives the *packer* mid-chapter cuts to **ZERO** on every edition. ✅

**✅ Cross-OS CONFIRMED:** Part-1's effect reproduces on macOS exactly as WIN measured on
Windows (catholic-study 111 → 1). `test_file_split.py` **46/46** on macOS.

### The Part-2 target — the remaining ~160 chapter-boundary (WARN) breaks

Part-1 converted the between-verse cuts into **at-chapter-boundary** cuts: an over-cap chapter
now becomes its own piece instead of splitting mid-verse, so the WARN count rose (pre-Part-1
~35–42 → post-Part-1 159–186) while the ERROR count collapsed. **Every remaining break is an
INTRA-book chapter start** (e.g. `gen 3:24 → gen 4:1`, `gen 9:29 → gen 10:1`): a book whose base
`index_split_NNN` file exceeds the cap is cut at its next chapter boundary. These are **exactly
what Part-2 (per-book base-file merge) collapses** — merge a book's base files into one spine
file ≤ the Kobo-safe ceiling and the intra-book chapter breaks vanish, leaving only the intended
book-title breaks (73–79 OK per edition).

Distribution is note-density-driven, concentrated in the large books. **ethiopian-tewahedo
(superset, 186 breaks / 44 books):** psa:14 · gen:11 · exo:9 · eze:9 · jer:9 · num:9 · isa:8 ·
deu:7 · 1ch:6 · 1ki:6 · job:6 · luk:6 · mat:6 · 1sa:5 · 2ch:5 · 2ki:5 · act:5 · lev:5 · pro:5 ·
(…+24 more books at 1–4 each). The study editions are canon-subsets (catholic 163 / evangelical
159 / orthodox 164). **Standalones** are already chapter-per-page (161 / 125) — Part-2's per-book
merge applies to them too (collapse `geez_{book}_{ch}.xhtml` into per-book files ≤ ceiling).

**Part-2 spec for WIN:** collapse every INTRA-book chapter-boundary break above — full exact lists
per edition in `spine-breaks-post-part1.json` (the `chapter` arrays). **Success = mid-chapter == 0**
(incl. psa119, fixed by merging psa's base files) **+ chapter breaks only on books that genuinely
exceed the per-book ceiling.** Mac will cross-OS verify the Part-2 re-cut the same way when it lands.

---

> The matrix below is the **PRE-Part-1 baseline** (it audited the then-live on-disk artifacts).
> Retained for the before/after delta; the **eink numbers are superseded by the re-baseline above.**

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
    — the K-KIN aggregate-doc-count blocker — not for page breaks.)
  - **★ Resolver empirically PROVEN with real data (Mac, 2026-06-24) — not just a code read.**
    `apply_target_override({'id':'probe'}, 'kindle')` → `resolve_file_split_target` returns
    **2_000_000**; eink/default → **400_000**; an explicit `reader_file_split_target` still
    wins (→ 999 in the probe). So the per-target cap selection is confirmed correct at HEAD.
    The **only** step still owed is the **end-to-end full-build re-measure** (build
    `--target-reader kindle` + re-run `audit_spine_breaks.py` → expect scripture pieces ≤2 MB,
    mid-chapter near-zero) — held off to avoid a heavy 91k-noteref build under RAM pressure
    (8 GB box, VS Code open). Re-verify per `feedback_reverify_conservative_nogo`.

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
