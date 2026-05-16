# Ge'ez external PD-source ingest — design spec

**Date:** 2026-05-16
**Proposed phase:** `τ.6.x.5` (external PD-source Ge'ez ingest
capability). First consumer: `τ.6.x.2.i` (Ge'ez Psalms), re-scoped
from OCR+merge to external-source ingest.
**Status:** design (brainstorming spec-review loop — revises the
approved direction after the Option-C decision + source validation).
**Supersedes (as primary):** the colometric-merge spec
`2026-05-16-geez-colometric-merge-design.md` is **retained as the
documented FALLBACK** for poetic books with *no* clean external
source; it is no longer the Ge'ez-Psalms path.
**Unaffected:** `τ.6.x.1.E` parser Fixes A/B/C (NT + narrative)
remain valid, implemented, and needed independently.

## 1. Decision & rationale

User selected **Option C**: source every poetic Ge'ez book from
the best available PD external source; use the colometric merge
only where no clean source exists. Rationale: the parallel-PDF
Ge'ez column is OCR-garbled (`τ.6.x.2.i` reproduced 4551 cola vs a
2531 floor; single-line mode 69/2531). A clean digitized critical
edition is dramatically higher fidelity for the flagship's Psalter
(the most liturgically-central book of the Tewahedo Bible) and
matches the project's already-established **per-book best-source**
provenance model (Patrologia PDFs for Chronicles/Ezra-Neh/Esther/
Job; GAPS manuscripts for Samuel/Kings; parallel-PDF elsewhere).
This serves the two-standalone-Bibles north star
(`CLAUDE_PROJECT_RULES` §1) directly.

## 2. Source — validated

**Ran HaCohen's digitized Ethiopic Bible**, Tel Aviv University
(`https://www.tau.ac.il/~hacohen/`). Validated 2026-05-16 by
fetching real pages:

- **Psalms** — ed. Hiob **Ludolf** (*Psalterium Davidis*, 1701;
  PD by age — three centuries old), Septuagint/Ethiopic numbering,
  Psalms 1–151. URL pattern
  `https://www.tau.ac.il/~hacohen/Psalm/PsalmNrR%20<N>.html`,
  N = 1..151.
- Psalm 1:1 verbatim:
  `ብፁዕ ፡ ብእሲ ፡ ዘኢሖረ ፡ በምክረ ፡ ረሲዓን ፤ ወዘኢቆመ ፡ ውስተ ፡ ፍኖተ ፡ ኃጥኣን ፤ ወዘኢነበረ ፡ ውስተ ፡ መንበረ ፡ መስተሳልቃን ።`
  — **clean Unicode Ethiopic** (native ግዕዝ fidäl, NOT a
  custom-font/ASCII transliteration), one correctly-numbered verse,
  intra-verse cola `፤`, verse-end `።`. Contrast the parallel-PDF
  OCR for the same verse (`ህቡዕ ፣ ብእሲ ፡ ዘኢሐሪረ…`, split across
  2–3 `።`-fragments).
- Psalm **151** present at the same URL pattern — the
  Tewahedo/Septuagint-distinctive David-vs-Goliath psalm
  (`መተርኩ ርእሶ` = "I cut off his head"), same clean structure →
  the 151-Psalm numbering matches `PSALMS_VERSE_COUNTS` exactly.
- Site also carries clean Ge'ez for **Sirach** (51 ch),
  **Wisdom of Solomon** (19 ch), **Proverbs** (ed. Pilkington),
  **Job** (ed. Pereira, 42 ch — cross-validates the GAPS
  Patrologia Job), **Song of Songs** (ed. Gleave, 8 ch),
  **Lamentations** (ed. Bachmann, 5 ch). Prayer of Azariah is
  embedded in the Daniel section (not separately addressable).
- No site-wide or per-page restrictive copyright/license/usage
  statement was found. The editions are old scholarly critical
  editions (Ludolf 1701; Pereira/Gleave/Bachmann/Pilkington
  late-19th/early-20th-c.), PD by age. HaCohen's digitization is
  a scholarly transcription of PD sources. User explicitly
  authorized PD use with citation; the project's attribution /
  bibliography / citation-index infrastructure
  (`scripts/attribute.py`, `bibliography.py`, `citation_index.py`)
  records source provenance for every datum.

## 3. Approach & rationale

**Trust-the-source-structure ingest.** Unlike the parallel-PDF
OCR path (distrust structure → `renumber_against_floor`), a clean
correctly-versified critical edition **is** the versification
authority. Therefore:

- Parse the source's own verse structure; **do not** force it
  through `renumber_against_floor` or the colometric merge.
- The canonical floor (`PSALMS_VERSE_COUNTS`, etc.) becomes a
  **validation check** (sanity: per-chapter counts within a small
  tolerance of the source), not a renumber target. Honest
  discrepancy reporting, not silent reshaping.
- Quality tier is a NEW higher tier — `digitized-critical-edition`
  — distinct from `ocr-tier3`. The module docstring + source
  record cite the exact edition (e.g. "Ge'ez Psalter, ed. Hiob
  Ludolf, *Psalterium Davidis* 1701; digitized by Ran HaCohen,
  TAU; PD by age").

Rejected: keep OCR+colometric-merge for Psalms (Option B) —
needlessly ships low fidelity when a clean PD source exists.

## 4. Architecture & components

A new ingest path in the existing tooling (not a parallel
universe). Components, each independently testable:

1. **Fetcher + local cache.** Fetch each source page once into a
   local, uncommitted cache
   (`content/translations/sources/hacohen-geez/<book>/<n>.html`),
   mirroring the parallel-PDF "large source lives locally, not
   committed" pattern. Polite: sequential, a small inter-request
   delay, resumable, skip-if-cached. Re-runs parse from cache
   (deterministic, offline, no re-fetch).
2. **Per-edition HTML parser.** `parse_hacohen_psalter(html) ->
   list[(chapter, verse, text)]`. Pure function over cached HTML.
   Psalms (Ludolf): each page = one Psalm = one canonical chapter;
   split body on the Arabic verse-number markers; capture the
   Ge'ez run per verse; preserve authentic `፡ ፤ ።` punctuation;
   collapse only incidental whitespace. Other books use sibling
   parsers (`parse_hacohen_<book>`) — editions differ
   (Ludolf/Pereira/Gleave/Bachmann/Pilkington), so HTML shape may
   differ per book; each gets its own small parser + calibration.
3. **Module writer.** Reuse the existing translation-module
   writer to emit `content/translations/geez-tewahedo/<book>.py`
   with the standard constants; `SOURCE_QUALITY =
   "digitized-critical-edition"`, `SOURCE_PROVENANCE =
   "hacohen-geez"`, `INGEST_PHASE` set per ship.
4. **Source-provenance record.** New
   `content/translations/sources/hacohen-geez/_source.yaml`:
   site, per-book edition + editor + year + PD basis, URL
   pattern, fetch date, per-ship ingest records — same shape as
   the parallel-PDF `_source.yaml`. Wires into the existing
   citation/bibliography system.

## 5. Calibrate-first gate (project-consistent)

Mirrors the Samuel/Kings calibrate-first discipline + the
`τ.6.x.0b` honesty contract. Before any bulk ingest of a book:

- Fetch a calibration sample (Psalms: Ps 1, Ps 118/119 the
  176-verse acrostic giant, Ps 151 boundary).
- Confirm: URL pattern holds; HTML structure stable; Unicode
  Ethiopic; verse numbering parseable; per-chapter verse counts
  within tolerance of the floor.
- **GO** → bulk-ingest all chapters. **NO-GO** (structure
  inconsistent / not extractable) → stop, report honestly, do
  not fabricate; fall back to the colometric-merge spec for that
  book. No artifacts written on NO-GO.

## 6. Versification reconciliation

Ludolf/HaCohen uses LXX/Ethiopic numbering (151 Psalms) — already
the `PSALMS_VERSE_COUNTS` basis. Per-Psalm verse counts may differ
slightly from our floor (Ludolf's colon/verse division vs the
floor's). Policy: **the source is authoritative**; record the
source's counts; report any per-chapter delta vs floor in the
ingest record for the `τ.6.x.3` audit, but **do not reshape** the
source text to the floor.

Concrete tolerance (default; the plan may tighten after the
calibration sample): a per-chapter delta is *recorded* if it
exceeds 2 verses or 5% of that chapter's floor (whichever is
larger). If more than 20% of chapters mismatch by that bar, the
source structure is not reliably aligned to our numbering → a
calibrate-first **NO-GO** for the book (fall back to the
colometric-merge spec), **never** a silent renumber.

## 7. Error handling & honesty

- Fetch failure / non-200 / unexpected redirect → abort that
  book's ingest with a clear error; never write partial/fabricated
  content.
- Page present but unparseable (structure drift) → calibrate-first
  NO-GO; fall back to colometric-merge spec; nothing written.
- Output is `digitized-critical-edition` quality — high fidelity,
  but the module docstring still states the exact edition,
  digitizer, PD basis, fetch date, and any per-chapter
  floor-delta, so provenance is fully transparent. Not presented
  as anything other than what it is.

## 8. Testing (TDD — characterization first)

- **Parser unit tests** over committed *tiny* fixture HTML
  snippets (1–2 psalms' worth, hand-trimmed from a cached page):
  exact (chapter,verse,text) output; Unicode Ethiopic preserved;
  `፤`/`።` retained; verse numbers stripped from text; whitespace
  normalized; no cross-contamination between verses.
- **Calibration tests:** Ps 1 first verse ==
  `ብፁዕ ፡ ብእሲ ፡ ዘኢሖረ …`; Ps 151 present + David/Goliath marker;
  151 chapters; per-chapter counts within tolerance of
  `PSALMS_VERSE_COUNTS`.
- **Fetcher tests:** cache-hit skips network (offline-deterministic);
  resumable; never partial-writes a module on fetch error.
- **Integration:** full Psalms ingest from cache → 151 chapters,
  Ps 1:1 / Ps 151 content correct, total verses within tolerance
  of the floor, 0 fabricated.
- **Regression:** full suite green; ruff-format clean;
  `PYTHONUTF8=1` on all Windows runs.

## 9. Scope / non-goals (YAGNI)

In scope **now:** the fetch+cache+parse+write pipeline + the
provenance record + the Ludolf-Psalms parser + calibration →
ships `τ.6.x.2.i` Ge'ez Psalms at `digitized-critical-edition`
quality.

Built to extend (sibling per-edition parsers) but **not built
now:** Sirach/Wisdom/Proverbs/Song-of-Songs/Lamentations/Job —
each is a later per-book ship with its own calibrate-first
(their editions differ). No speculative multi-book code.

Non-goals: no scraping beyond the user-authorized HaCohen site;
no change to the parallel-PDF / NT / narrative paths; the
colometric-merge spec is **retained** (fallback for any poetic
book HaCohen lacks, e.g. standalone Prayer of Azariah); no
re-sourcing of already-shipped books.

## 10. Acceptance criteria

1. `hacohen-geez` source-provenance record created; per-book
   edition + PD basis + citation captured; integrates the
   existing attribution/bibliography system.
2. Fetcher caches locally, polite, resumable, offline-replayable;
   no partial/fabricated writes on error.
3. `parse_hacohen_psalter` pure + unit-tested on committed
   fixtures; output exact, Unicode Ge'ez, authentic punctuation.
4. Calibrate-first gate enforced; honest NO-GO path with
   colometric-merge fallback; nothing written on NO-GO.
5. `τ.6.x.2.i` Ge'ez Psalms ships: 151 chapters,
   `SOURCE_QUALITY="digitized-critical-edition"`, Ps 1:1 ==
   `ብፁዕ ፡ ብእሲ ፡ ዘኢሖረ …`, Ps 151 David/Goliath present, totals
   within floor tolerance, per-chapter floor-deltas recorded for
   `τ.6.x.3`.
6. New TDD tests green; ruff-format clean; full regression
   `0 fail`.
7. Colometric-merge spec explicitly noted as retained fallback;
   `τ.6.x.1.E` parser fix unaffected.

## 11. Relationship to the other specs

- `2026-05-16-geez-colometric-merge-design.md` — **retained as
  the fallback** for poetic books with no clean external source;
  no longer the Ge'ez-Psalms path. (A one-line "superseded as
  primary, retained as fallback" pointer to be added to that spec
  in the same revision commit, for coherence.)
- `τ.6.x.1.E` parser pre-pass (Fixes A/B/C) — independent and
  still required for the NT and the OCR'd narrative parallel-PDF
  books; unaffected by this spec.
- The narrative Ge'ez OT catchup (2es, tob, jdt, …) continues on
  the parallel-PDF path; this spec only changes the **poetic**
  books that have a clean external source.
