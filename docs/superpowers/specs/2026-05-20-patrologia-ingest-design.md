# Patrologia Orientalis ingest — design spec (audit U-belt 2026-05-20)

**Status:** DESIGN — implementation pending. Companion to
`docs/superpowers/specs/2026-05-16-samuel-kings-dual-manuscript-collation-design.md`.

**Goal:** Render `1ch`, `2ch`, `ezr`, `neh`, `job` into
`content/translations/geez-tewahedo/` (and `amharic-tewahedo/` if the
French translations parallel-render cleanly) by OCR'ing the printed
bilingual Patrologia Orientalis critical editions.

## 1. Source inventory (verified on disk 2026-05-20)

| Book(s)      | PDF | PO citation |
|---|---|---|
| 1+2 Chronicles | `GAPS/3_Chronicles/Chronicles__Paralipomenes-I-II__PO-23-fasc-4_Grebaut_1932.pdf` | PO 23 fasc 4, Grébaut 1932 |
| Ezra + Nehemiah | `GAPS/4_Ezra-Nehemiah/Ezra-Nehemiah-canonical__PO-13-fasc-5_Pereira_1919.pdf` | PO 13 fasc 5, Pereira 1919 |
| Esther | `GAPS/5_Esther/Esther__PO-9-fasc-1_Pereira_1913.pdf` | PO 9 fasc 1, Pereira 1913 |
| Job | `GAPS/6_Job/Job__PO-2-fasc-5_Pereira_1907.pdf` | PO 2 fasc 5, Pereira 1907 |

All four are **public domain** (PO is open archive, archive.org links in
`GAPS/SOURCES.md`). Printed bilingual Ge'ez + French critical edition;
the editors have already done the philological work (manuscript
collation + variant apparatus in French).

**Esther overlaps with the parallel-PDF EOTC render** (already shipped
`geez-tewahedo/est.py` at `ocr-tier3`). The Patrologia Esther would be
a **higher-quality re-render** (`patrologia-printed-tier1`) — kept as a
separate `est_patrologia.py`? Or override `est.py`? **Decision point:
see §6.**

## 2. Why Patrologia is EASIER than the parallel-PDF EOTC

| Axis | parallel-PDF EOTC (τ.6.x.2) | Patrologia |
|---|---|---|
| Source | photo-scanned printed Tewahedo edition | printed PD critical edition |
| Layout | 2-column bilingual Ge'ez / Amharic | 2-column bilingual Ge'ez / French |
| OCR target | `script/Ethiopic` (Tesseract Ge'ez) + `amh` | same `script/Ethiopic` + Tesseract French (`fra`) |
| Quality signal | OCR confidence ONLY (no apparatus) | OCR confidence + the editor's printed apparatus footnotes |
| Witness count | 1 (the printed Tewahedo edition; single tradition) | N (collated; printed apparatus records the variants) |
| Provenance tier | `ocr-tier3` | `patrologia-printed-tier1` (HIGHER) |
| Page count | ~1300 pages (whole Bible) | ~50-200 pages per volume × 4 volumes = ~400-800 pages |

The leverage: Patrologia is fewer pages, cleaner print, and the
editor's work is the most-of-the-quality-difference vs the EOTC photo
scan.

## 3. Architecture (reuses Phase-2 from τ.6.x.4.c + τ.6.x.2 infrastructure)

**Three reuses + one new:**

1. **OCR pipeline** — reuse `scripts/extract_parallel_pdf.py`'s
   pymupdf + Tesseract + LIGHT-1 subprocess pattern (memory
   `w_w1_subprocess_devnull`). New language: `--engine tesseract
   --language fra` for the French column (extracted but NOT
   used for render; the French is the editorial apparatus + the
   French side serves as a sanity-anchor for verse alignment).
2. **Render** — reuse `scripts.core.write_book_module` + the τ.7.x
   render conventions. Files: `content/translations/geez-tewahedo/
   {1ch,2ch,ezr,neh,job,est_patrologia}.py`. `SOURCE_QUALITY =
   "patrologia-printed-tier1"`; `SOURCE_PROVENANCE` records the PO
   volume + fascicle + editor (`Grébaut 1932` / `Pereira 1907-1919`).
3. **Verse-count floor** — reuse `scripts.core.canonical_verse_counts.
   canonical_count(book, ch)` — these books have KJV skeletons; the
   floor is `len(load_kjv_skeleton(book, ch))` per chapter. No new
   hand-typed dict needed.
4. **NEW: Patrologia OCR extractor** — `scripts/extract_patrologia_pdf.py`
   handles the PO layout specifically (2-column Ge'ez/French side-by-
   side; French column extracted as gloss; the editor's footnotes
   discarded except for the apparatus markers that survive into
   `_source.yaml` as transcription notes). Tasks 1–4 ship as a single
   `τ.6.x.5.a` arc-kickoff.

## 4. Decisions (lock at spec review)

- **D1 Deliverable scope:** reconstructed Ge'ez text per book + the
  editor's French gloss as a verse-aligned secondary stream in
  `_source.yaml`. (Apparatus from the printed footnotes: out of
  scope for first pass; can be a τ.6.x.5.b detail-wave later.)
- **D2 Accuracy gate:** semantic-skeleton cross-check against the
  KJV skeleton at C-7-equivalent (NOT a full marathon — printed text
  is much more reliable than vision transcription; single-pass OCR
  with audit at verse-count + per-verse semantic-pass on a sample).
- **D3 Witness disagreement:** N/A (single witness — the printed
  PO edition is already collated). The PO editor's variant apparatus
  could be recorded in a future detail-wave but not as base/variant
  in our pipeline.
- **D4 Esther overlap:** generate `est_patrologia.py` SEPARATELY from
  the existing `est.py`; the publisher's edition-config picks one or
  the other via `popup_languages_default` / `popup_translation`
  (memory `feedback_extensive_answers` — broader scope = both
  available, not silently overwriting).

## 5. Phasing

- **τ.6.x.5.a** — `extract_patrologia_pdf.py` + Job ingest (smallest
  volume: PO 2 fasc 5, Pereira 1907; fastest smoke test). Smoke-test
  the pipeline end-to-end before scaling.
- **τ.6.x.5.b** — Esther (PO 9 fasc 1, Pereira 1913) as a 2nd-tier
  re-render of the existing `est.py` (separate file `est_patrologia.py`).
- **τ.6.x.5.c** — Ezra + Nehemiah (PO 13 fasc 5, Pereira 1919); one
  volume contains both books.
- **τ.6.x.5.d** — 1+2 Chronicles (PO 23 fasc 4, Grébaut 1932); one
  volume contains both books. **Heaviest volume** — Grébaut's edition
  is the most extensive; expect the longest OCR pass.
- **τ.6.x.5.e** — arc-close: book-wide QA + Phase-3 render integration
  + `_meta`/`_source` + lint 11·0·0 + tests pin.

## 6. Esther override decision

The existing `geez-tewahedo/est.py` was rendered at `ocr-tier3`
quality from the parallel-PDF EOTC. The Patrologia Esther would be
`patrologia-printed-tier1` (higher). Options:

- **A. Overwrite `est.py`.** Highest text quality wins; loses the
  ocr-tier3 baseline.
- **B. Keep both: `est.py` + `est_patrologia.py`.** Publisher chooses
  per-edition which to ship.
- **C. Make Patrologia the default `est.py`; archive the OCR version
  as `est_ocr.py`.** Same as A but preserves the OCR baseline as a
  fallback.

**Recommendation: B.** Per memory `feedback_extensive_answers`, the
broader scope wins — both versions available, publisher choice.
Phase-3 render produces both files; the customize console exposes a
"prefer Patrologia for Esther" toggle if the user wants it.

## 7. Testing & success criteria

- **Pin tests mirror τ.7.x convention** (book loads, verse-count floor
  matches KJV skeleton, renumber shape, `_meta`/`_source` back-link).
- **Lint check** `manuscript_witnesses_valid` does NOT apply (no
  witnesses; the printed edition is the source). NEW lint:
  `check_render_provenance_tier` (pins every rendered book's
  `SOURCE_QUALITY` is a known tier per
  `scripts.core.provenance_tiers.is_known_tier`).
- **Coverage delta:** geez-tewahedo +5 books (Chronicles ×2, Ezra, Neh,
  Job — minimum) and possibly +1 (Esther re-render). amharic-tewahedo
  does NOT gain books from this track (the French gloss is editorial,
  not Amharic).
- **Phase-3 release gate:** `lint_rules` **12·0·0** (was 12 after the
  audit U-belt; this track adds checks without breaking the
  existing); `ruff format --check` clean; full focused regression
  green; local commit only (no push, no zip; memories
  `reference_save`, `feedback_continue_not_save`).

## 8. Out of scope (deferred to later detail-waves)

- The Patrologia editor's variant apparatus → not recorded in the
  first pass; potential future τ.6.x.5.f wave.
- French-side translation as a published popup language → no, French
  stays editorial-only.
- A "Patrologia-overrides-OCR" project-wide policy → no, per-book.

## 9. Attribution

PO volumes are public domain (pre-1923 publication). The
`SOURCE_PROVENANCE` records the volume, fascicle, editor, year,
archive.org URL. No attribution-required license; the
`_source.yaml` block is for scholarly traceability + the
honesty contract.

## 10. Parallelization notes

This track is **independent of the manuscript marathon** (τ.6.x.4.b/c)
and **independent of the parallel-PDF Ge'ez catchup** (τ.6.x.2).
Same engine reuses apply; no shared mutable state. Can run in parallel
with both AND with the Amharic NT cadence (τ.7.x.w+). The four
volumes can be ingested in any order; the smallest (Job) is the
recommended smoke target.
