# Ge'ez colometric-merge — design spec

**Date:** 2026-05-16
**Phase:** `τ.6.x.1.E` Fix D (the final part of the unifying
structure-aware parser pre-pass). Consumed first by `τ.6.x.2.i`
(Ge'ez Psalms ingest).
**Status:** design approved (brainstorming), pre-implementation.
**Related:** `dev/CLAUDE_PROJECT_RULES.md` §1 (two-standalone-Bibles
north star), the `τ.6.x.0b` honesty contract, the τ.7.x.v
NT-renumber-overflow blocker.

## 1. Background — the unifying bug class

`τ.7.x.v` paused the Amharic cadence on an "NT-renumber-overflow"
blocker. Investigation (2026-05-16) found the OT-narrative-tuned
`_parse_paragraph_mode` (split on `።`) + `renumber_against_floor`
pipeline breaks on **any** structurally-different scripture:

- **NT** — `!`-terminated chapter markers were dropped (Mt 1-2
  lost) and `ክፍል N፡` pericope headers parsed as verses.
- **Ge'ez poetry (Psalms)** — the Ge'ez Psalter is colometrically
  pointed (`።` after every poetic colon, not just verse-end), so
  paragraph-mode yields ~1.8× the canonical verse count.

`τ.6.x.1.E` Fixes A/B/C are **implemented and verified**
(2026-05-16): (A) `!`/`|` added to `CHAPTER_HEADER_RE_LENIENT`'s
terminator class; (B) `is_pericope_header()` / `PERICOPE_HEADER_RE`
filtering `ክፍል N፡` headers; (C) `renumber_against_floor` hard-fails
gross over-segmentation instead of silently shipping distorted
scripture. ruff-clean; 9/9 characterization + 1291/0 focused
regression. This spec covers **Fix D**, the remaining part: making
the colometrically-over-segmented Ge'ez poetic column shippable.

## 2. Problem (settled by real data)

Empirical, Ge'ez Psalms, `--engine text-layer`:

| Mode | Ge'ez verses | vs 2531 floor |
|---|---:|---|
| paragraph-mode (split `።`) | 4551 | ~1.8× — colometric over-seg |
| single-line / explicit-numeral (`τ.6.x.1.B`) | 69 | 2.7% — numerals too OCR-garbled (`Fየ`,`ጀZ`,`፪$`,`፻፲`) |

Amharic Psalms paragraph-mode = 2243 (== shipped τ.7.x.i), so the
engine and page range `[803,906]` are correct; only the **Ge'ez
column** over-segments. Single-line mode was tested and **rejected**
— the Ge'ez Psalter's explicit verse numerals exist but are
OCR-garbled past `ETHIOPIC_LINE_START_NUMERAL_RE` recovery. The
4551 paragraph-mode cola **do contain the genuine Psalm text**;
they are merely over-segmented. The task: regroup those cola into
the canonical per-chapter verse structure at honest ocr-tier3
fidelity.

## 3. Approach & rationale

**Floor-guided colometric merge.** Extend the project's already-
proven `renumber_against_floor` philosophy — *"the chapter+verse
INDEX is canonical; verse-boundary content may misalign 1-3 verses
per chapter; the τ.6.x.3 audit reconciles against an independent
reference"* — from *one fragment → one slot* (which overflows for
poetry) to *merge ~N/V cola → one verse*. The canonical floor
(`PSALMS_VERSE_COUNTS`, etc.) is the structural ground truth;
no dependence on the unrecoverable OCR numerals, no external
anchor, fully deterministic.

Rejected alternatives: single-line/numeral mode (refuted by data,
§2); hybrid (degenerates to merge since single-line yields 69);
punctuation-aware split (no mark reliably distinguishes verse-end
from colon-end — both use `።`).

## 4. Component — `merge_to_floor`

A pure function in `scripts/extract_parallel_pdf.py`, beside
`renumber_against_floor`:

```
merge_to_floor(verses: list[(int,int,str)],
               verse_counts: dict[int,int]) -> list[(int,int,str)]
```

`verses` = parsed cola in **source order** (labels untrusted, as
`renumber_against_floor` already treats them). `verse_counts` =
canonical chapter → verse-count floor.

Algorithm:

- `N = len(verses)`; `chapters = sorted(verse_counts)`;
  `V = sum(verse_counts.values())`.
- `N == 0` → return `[]`.
- `N < V` (under-recovery) → **fall back** to
  `renumber_against_floor(verses, verse_counts)` (existing
  ocr-tier3 sequential under-fill; merge is neither needed nor
  possible).
- `N >= V` — walk `chapters` in order, maintaining `idx` (cola
  consumed), `rem_cola = N - idx`, `rem_floor` (sum of not-yet-
  allocated chapters' floors). For chapter `ch` with `c =
  verse_counts[ch]`:
  - **Last chapter:** `share = N - idx` (absorbs the remainder so
    the stream is consumed exactly — no rounding leak).
  - **Otherwise:** `share = round(c / rem_floor * rem_cola)`, then
    clamp into `[c, rem_cola - (rem_floor - c)]`. The invariant
    `rem_cola >= rem_floor` holds at every step (it holds initially
    since `N >= V`, and the clamp preserves it), so the clamp range
    is always non-empty and `share >= c`.
  - Split `share` cola into exactly `c` verses by even grouping:
    `base = share // c`, `extra = share % c`; the first `extra`
    verses take `base + 1` cola, the rest take `base` (every verse
    gets `>= base >= 1` cola since `share >= c`).
  - For each of the `c` verses: slice its cola group from `idx`,
    join their text parts with a single space, collapse internal
    whitespace, emit `(ch, verse_ordinal_1_based, joined)`; advance
    `idx`.
  - Recompute `rem_cola = N - idx`; `rem_floor -= c`.
- Return the list: **exactly `V` entries, canonical `(ch, v)`
  order, every chapter present at exactly its floor count, all
  source colon-text preserved by concatenation**.

The function is independent, deterministic, and unit-testable in
isolation: input cola + floor → canonical-structured verses.

## 5. Wiring

- New CLI flag `--colometric-merge` (`action="store_true"`,
  default `False`). It **requires** `--renumber` (the floor); if
  absent, `p.error(...)`.
- `extract_section(...)` gains a `colometric_merge: bool = False`
  parameter. When `True` **and** a `renumber_floor` is set, each
  book's parsed verse list is passed to `merge_to_floor` **instead
  of** `renumber_against_floor` (merge already emits canonical
  `(ch,v)`; renumber is not additionally applied).
- `main()` passes `args.colometric_merge` through (mirroring how
  `paragraph_mode` / `renumber_floor` are already threaded).
- `τ.6.x.2.i` invocation:
  `--section psalms --lang geez --engine text-layer
  --paragraph-mode --renumber psalms --colometric-merge`.
- **Default off ⇒ byte-identical behavior for every existing
  narrative ship** (τ.6.x.2.a-h, all τ.7.x.*). This flag is the
  only behavioral delta, opt-in per ship — consistent with
  `--paragraph-mode` being explicit.

## 6. Error handling & honesty backstop

- `--colometric-merge` without `--renumber` → hard CLI error.
- `N < V` → graceful fallback to `renumber_against_floor` (no
  raise; the existing acceptable ocr-tier3 under-fill).
- The Fix C gross-overflow gate in `renumber_against_floor` is
  unchanged and remains the honesty backstop for the **non-merge**
  paths (narrative books, NT). `merge_to_floor` itself emits
  exactly `V` verses, so it structurally cannot produce an
  overflow. There is no silent-distortion path.

## 7. Testing (TDD — characterization first)

Extend `tests/test_parser_structure_aware_prepass.py` with a
`TestColometricMerge` class. Failing tests written and confirmed
RED before implementation:

- **Exact floor structure:** floor `{1:2, 2:3}` (V=5), a 9-colon
  stream → output is exactly
  `[(1,1),(1,2),(2,1),(2,2),(2,3)]`; len == 5; every chapter at
  its floor count.
- **Source text preserved:** the ordered concatenation of output
  texts contains every input colon's text, in order (round-trip).
- **Stream consumed exactly / last-chapter remainder:** a stream
  whose proportional rounding would leak a colon → the last
  chapter absorbs it; total == V; no colon dropped or duplicated.
- **Under-fill fallback:** `N < V` → identical to
  `renumber_against_floor` (sequential under-fill; no raise; no
  synthetic overflow chapter).
- **Determinism:** same input → identical output across runs.
- **Integration (dry-run, heavier):** real Ge'ez Psalms
  `--colometric-merge` dry-run → exactly 2531 verses; Psalm 1
  content (`ህቡዕ`/`ብእሲ`) present in chapter 1; 0 overflow.
- **Regression:** full suite green; with the flag **off**, a
  narrative book's output is byte-identical to pre-change.

ruff-format clean; full regression `0 fail`; PYTHONUTF8=1 on all
Windows runs.

## 8. Honesty contract

Output is explicitly **ocr-tier3**: verse-boundary placement is
*approximate* (even colon grouping, not semantic), the
chapter+verse **index is canonical**, and the book is flagged for
`τ.6.x.3` audit reconciliation against an independent reference —
the **same contract as the τ.6.x.2.a-h narrative books**. The
generated module docstring and the `_source.yaml` ingest record
must state the colometric-merge method and its tier-3 boundary
caveat plainly. It is **not** presented as verbatim-accurate verse
boundaries.

## 9. Scope / non-goals (YAGNI)

In scope: the one general `merge_to_floor` function + the opt-in
flag + wiring + tests; enabling `τ.6.x.2.i` Ge'ez Psalms.

Explicit non-goals:
- Not fixing OCR garble or residual title-page contamination
  (ocr-tier3 noise; `τ.6.x.3` audit / GAPS-manuscript track).
- Not semantic / reference-aligned verse-boundary detection.
- Not auto-detecting when to merge (explicit opt-in, like
  `--paragraph-mode`).
- Nothing Psalms-specific: the function is floor-driven and
  book-agnostic, so Sirach / Wisdom / Prayer-of-Azariah reuse it
  when their Ge'ez ships come — but no speculative code is built
  for them now.
- No change to the narrative / NT paths.

## 10. Acceptance criteria

1. `merge_to_floor` added: pure, deterministic; output total ==
   `sum(verse_counts)`; every chapter present at exactly its floor
   count; all source text preserved; `N < V` → fallback;
   `N == 0` → `[]`.
2. `--colometric-merge` flag added; requires `--renumber`;
   **off ⇒ byte-identical narrative/NT behavior** (regression
   proves it).
3. Ge'ez Psalms dry-run with the flag → exactly 2531 verses,
   Psalm 1 content in ch1, 0 overflow.
4. New TDD tests green; ruff-format clean; full regression
   `0 fail`.
5. Ge'ez Psalms output is documented ocr-tier3 / index-canonical /
   `τ.6.x.3`-audit-flagged in the module docstring and the
   `_source.yaml` ingest record.
6. This unblocks `τ.6.x.2.i` (Ge'ez Psalms) and, by reuse, the
   later poetic-book Ge'ez ships.
