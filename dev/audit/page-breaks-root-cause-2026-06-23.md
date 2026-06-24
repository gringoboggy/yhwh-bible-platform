# Spurious page breaks — ROOT-CAUSED + fix plan (2026-06-23)

The weeks-long "page breaks throughout the Bibles" defect is **root-caused with proof**, a
deterministic finder is built, and the user chose the fix direction. This is the reference for
the multi-session re-cut (WIN + Mac, byte-stability-critical → golden re-baseline required).

## The finding (proven, not guessed)

On a Kobo e-ink kepub **every spine file starts on a new page** — CSS `page-break-*` is ignored
at the depth kepubify nests content (build_edition.py:4596–4600), so a **spine-file boundary is
the only thing that forces a page break**. The build's file-split packer (`apply_file_split`)
targets **400 KB per spine file** (`FILE_SPLIT_TARGET_DEFAULT`, build_edition.py:4510) and, when a
heavily-noted chapter exceeds that, **cuts between verses** — the `_VN_LINK_RE` cut candidate
(build_edition.py:4621, comment: "so a heavily-noted chapter can split between verses"). This
flatly contradicts the packer's own "we never split mid-chapter" comment (:4511). The cut lands
wherever 400 KB falls → the breaks look random because **the byte cap, not the structure, picks
the cut**.

**Scope (flagship `ethiopian-tewahedo` eink, measured by the new auditor):**
- 79 BOOK-title breaks — intended ✓
- **40 CHAPTER-boundary breaks** (mid-book; base `index_split_NNN` boundaries, chapter-aligned) — undesired
- **130 MID-CHAPTER breaks** (half-empty page BETWEEN two verses of one chapter) — the bug, Genesis→Revelation

**Two split layers** (both produce mid-book spine boundaries):
1. **Base** `index_split_NNN.html` (calibre-produced, ~61 files) — split at CHAPTER boundaries, NOT
   per book (Genesis spans index_split_000/001/002…). These are the ~chapter-aligned breaks.
2. **Per-edition packer** `apply_file_split` — sub-splits each base file into `_MM` pieces at the
   400 KB cap, using verse-level cut candidates → **the 130 mid-chapter breaks** (e.g. base file
   `index_split_001` = gen 4–26 → `_00` 4:1–10:6 | `_01` 10:7–17:3 | … each `_MM` cut is mid-chapter).

**Why every prior audit missed it for weeks:** they inspected *file contents*. No single file is
malformed — the defect is in *where one file ends and the next begins*. You only see it by
reconstructing the spine→verse map.

## The finder (built 2026-06-23) — `dev/audit_spine_breaks.py`

Edition/canon/platform-agnostic. Point it at any built `.epub`/`.kepub.epub`; it parses the OPF
spine, maps each spine file → (book, chapter, verse) range, and classifies every boundary:
BOOK-start (OK) · CHAPTER-start (WARN, mid-book) · MID-CHAPTER (ERROR). Exit 1 on any ERROR;
`--max-chapter-breaks N` also fails excess WARNs. **This is the regression gate for the fix.**

```
py -3 dev/audit_spine_breaks.py <built.epub | built.kepub.epub> [...]
```

## The constraint (why the split exists — the fix is a real tradeoff)

The split is NOT gratuitous: (a) Kobo ignores CSS breaks, so a spine boundary is the ONLY way to
force the book-title-page break; (b) pieces of **700–880 KB caused on-device trouble** (build_edition.py:4617
— hence the conservative 400 KB target; memory: "Kobo break ~881 KB"). So we **cannot** blindly
merge every book into one multi-MB file — a giant Genesis might choke Kobo. **The one unknown that
gates the fix: Kobo's real max spine-file size.** It needs ONE device measurement.

## The plan — "MEASURE, then merge per-book" (user-chosen 2026-06-23)

1. **Kill mid-chapter unconditionally** (WIN, `scripts/build_edition.py`): make the packer cut ONLY
   at chapter/book boundaries — drop the `_VN_LINK_RE` verse-level candidate; an over-cap chapter
   becomes its own piece. Converts all 130 mid-chapter → (at worst) chapter breaks. TDD; gate with
   `audit_spine_breaks.py` (mid-chapter == 0).
2. **Measure Kobo's file-size limit** (WIN — the Kobo is on the WIN box at `G:`): build a test
   artifact with books merged toward one-file-each (prototype merge, or a raised cap), load it, the
   user reports the largest single-file book Kobo renders + page-flips cleanly.
3. **Merge per-book up to the measured limit** (WIN): each book → one spine file when it fits; the
   few that exceed Kobo's limit split ONLY at chapter boundaries (never mid-chapter). Most books →
   ZERO breaks.
4. **Byte-stability:** re-cutting file boundaries shifts pieces on EVERY edition → **breaks the
   9-KJV byte-stable golden hashes by design** → a deliberate **golden re-baseline** is part of this
   work (the long-deferred char-vs-byte re-cut; the user has now authorized it). Prove "only the
   intended boundary changes" + re-baseline + run the determinism gate.

## ✅ MEASUREMENT DONE (2026-06-24) — the gating unknown is answered; merge is GO

Step 2 (measure Kobo's limit) is complete. Method: temporarily set `reader_file_split_target: 20000000`
on ethiopian-tewahedo (huge cap → packer never sub-splits a base file) + made the backmatter glossary use
`FILE_SPLIT_TARGET_DEFAULT` regardless (build_edition.py:~5213 — so the navigated glossary stays finely
split; **byte-safe no-op for every current edition**, KEEP this WIP). Built + kepubified + loaded.

- **129 of 130 mid-chapter breaks VANISHED** just by not sub-splitting (`audit_spine_breaks.py`). The lone
  holdout `psa 119:88→89` is a **base**-split artifact (calibre cut `index_split_035` mid-Psalm-119) — the
  per-book merge (which merges base files) fixes it for free. → CONFIRMS the packer's verse-level
  sub-splitting is the sole mid-chapter cause.
- **Kobo renders the big merged files without lag** — the user read the merged build (scripture pieces up
  to **~6.2 MB post-kepubify**, vs the old ~880 KB) and reported NO lag. → **one-file-per-book merge is
  VIABLE**; pick a safe ceiling (~8–10 MB) and only chapter-split books that exceed it (never mid-chapter).
- Remaining in that measurement build: the ~36/40 **chapter-boundary** breaks (the base split, layer 2 —
  e.g. gen 3→4, which the user flagged) + the 1 psa119 residual. Layer-2 = the per-book base-file MERGE
  (step 3), which `apply_file_split` does NOT yet do (it sub-splits base files but never merges across them;
  a book spans several base files — Genesis = `index_split_000/001/002`).

**So step 3 (the implementation) is now unblocked:** (a) drop `_VN_LINK_RE`; (b) MERGE each book's base
files into one spine file ≤ ceiling (concatenate bodies, regen spine+manifest, rewrite cross-file hrefs —
the existing href-rewrite pass is the model); (c) golden re-baseline. Gate: `audit_spine_breaks.py`
mid-chapter == 0 AND chapter-breaks only on books that genuinely exceed the ceiling.

## Lane split (WIN + Mac — file-disjoint, no rebase collision)

- **WIN owns** `scripts/build_edition.py` (the packer re-cut), the golden re-baseline, and the Kobo
  device measurement (device is on the WIN box).
- **Mac owns** (after its current round-13 tasks): RUN `dev/audit_spine_breaks.py` across **every
  edition × format** (4 study editions + standalones, epub + kepub) → `dev/audit/spine-breaks-all-editions.md`
  (the full cross-Bible/cross-platform scope the user wants); investigate whether tablet/kindle/apple
  artifacts have the same break class; then cross-OS verify WIN's re-cut. Mac does NOT edit
  `scripts/build_edition.py` (WIN's heavy surface).
