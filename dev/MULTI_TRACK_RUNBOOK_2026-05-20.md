# Multi-track marathon runbook — 2026-05-20

**Audience.** Any agent (Claude / human) resuming this project. Five
production tracks are scaffolded; each is INDEPENDENT and can run in
parallel with the others. This file is the single-page kickoff guide
for each track.

**Repo structure (after 2026-05-20 audit):** Everything the project
needs lives inside `C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\`.
The previously-external `GAPS/` source-image folder (1 GB of manuscript
+ Patrologia PDFs) was moved INSIDE on 2026-05-20 and gitignored — so
relative paths from the repo root (`GAPS/2_Kings/...`, etc.) resolve
directly. Backup the whole `YHWH v2.4/` directory and you have
everything; the gitignore keeps the binary GAPS images out of git
history while preserving them in the working tree.

**Prerequisites already shipped (do not re-build):**
- ✅ `scripts/core/manuscript_records.write_witness` — canonical writer
- ✅ `scripts/core/manuscript_chapter_class.chapter_profile` — class screens
- ✅ `scripts/core/manuscript_self_check.screen_witness_for_class_failures` — pre-screen helper
- ✅ `scripts/core/manuscript_rounds.escalate_if_unbounded` — round-bound enforcer
- ✅ `scripts/core/manuscript_collation` + `manuscript_reconcile` — engine
- ✅ `scripts/core/canonical_verse_counts.canonical_count` — KJV ceiling per book
- ✅ `scripts/core/provenance_tiers` — 5 registered tiers
- ✅ `scripts/acquire_cudl_master` — CUDL pre-pull tool
- ✅ `scripts/render_coverage` — whole-project inventory
- ✅ `scripts/extract_parallel_pdf` — parallel-PDF EOTC OCR pipeline
- ✅ `scripts/run_manuscript_collation_at_scale` — at-scale driver (`--track samuel|kings`)
- ✅ Lint suite 14·0·0 (incl. `render_coverage`, `provenance_tier`, `manuscript_witnesses`)
- ✅ `content/manuscript/_reviewer_context/{GG,CAM}_topology.md` — append-only scribal references
- ✅ `dev/MARATHON_LEDGER.md` — per-chapter cadence telemetry

**Plan template (apply per chapter, per track that uses it):**
`docs/superpowers/plans/2026-05-17-kings-manuscript-collation.md` — the
authoritative per-chapter C-1…C-9 procedure with METHOD NOTES 1-5.

---

## Track A — Manuscript collation (τ.6.x.4.b/c)

**Status:** 4/47 Kings calibrated + 4/55 Samuel calibrated. Next: **1 Kings 5** (Kings) or **1 Samuel 2** (Samuel).

**Books:** `1sa` (1Sa1, 1Sa3, 1Sa17, 2sa11 already calibrated; 51 pending), `2sa` (same), `1ki` (1Ki1-4 calibrated, 18 pending), `2ki` (25 pending).

**Kickoff (Kings, next chapter):**

```powershell
# From C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4 :
# Per-chapter procedure template per
#   docs/superpowers/plans/2026-05-17-kings-manuscript-collation.md
# Hybrid cadence per METHOD NOTE 5:
#   NARRATIVE chapters run continuously; LIST/REGNAL stop-and-check-in.
# Next chapter: 1ki:5 (NARRATIVE — Solomon's preparations + Hiram).
```

The C-1…C-9 template is invoked via `superpowers:subagent-driven-development`.
Controller assembles per-class prompts using `chapter_profile("1ki", 5)` at C-1.

**Kickoff (Samuel, in parallel with Kings):**

```powershell
# Same template, --track samuel. Next pending = 1sa:2 (NARRATIVE).
# All audit-U-belt upgrades apply identically to Samuel.
& "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" `
  scripts/run_manuscript_collation_at_scale.py --track samuel
# Confirms 51/55 pending; chapter_profile("1sa", 2) → NARRATIVE.
```

**Parallel safety:** Kings + Samuel touch DIFFERENT manifest paths (`content/manuscript/{samuel,kings}/`) and different per-track collation dirs. No shared mutable state. Both subagent flows can run simultaneously without collision.

**Watch for:**
- 1Ki5 should be NARRATIVE per the classifier — if R1 finds >50 defects, surface (mis-classification).
- 1Ki15-16 will hit REGNAL_FRAME → stop-and-check-in.
- Method notes 1-5 govern every chapter; the controller embeds them in C-2/C-5 prompts.

---

## Track B — Patrologia Orientalis ingest (τ.6.x.5, NEW)

**Status:** 4 PDFs on disk (5 books); design spec shipped; pipeline NOT YET BUILT.

**Books:** 1ch + 2ch (PO 23), ezr + neh (PO 13), est (PO 9, optional re-render), job (PO 2 — smallest, recommended smoke).

**Design spec:** `docs/superpowers/specs/2026-05-20-patrologia-ingest-design.md`.

**Kickoff (build pipeline + Job smoke):**

```powershell
# Build scripts/extract_patrologia_pdf.py mirroring extract_parallel_pdf.py:
#  - pymupdf to rasterize the bilingual Ge'ez/French columns
#  - Tesseract --engine tesseract --language ethi (or "fra" for French side)
#  - Verse parsing keyed on Ethiopic verse numerals (already handled in
#    extract_parallel_pdf.normalize_verse_numerals)
#  - Reuse canonical_count("job", ch) as the per-chapter floor
#  - Write to content/translations/geez-tewahedo/job.py via write_book_module
#  - SOURCE_QUALITY = "patrologia-printed-tier1"
# Smoke target: PO 2 fasc 5 Pereira 1907 (39.5 MB, smallest PDF; Job 42 ch / 1070 v).
```

**Parallel safety:** Track B writes to `content/translations/geez-tewahedo/{1ch,2ch,ezr,neh,job}.py` — distinct files from any other track. Can run simultaneously with A/C/D.

**Watch for:**
- `provenance_tier` lint pin checks the SOURCE_QUALITY field — use the registered `patrologia-printed-tier1`.
- Esther overlap with the parallel-PDF `est.py` — per spec D4, **keep both files** (`est.py` + `est_patrologia.py`). DO NOT overwrite `est.py`.
- Render-coverage tool reports Track B as `patrologia_pending` until books land in `geez-tewahedo/`.

---

## Track C — Parallel-PDF Ge'ez catchup (τ.6.x.2.o+ paused)

**Status:** Paused at τ.6.x.2.o Sirach. `extract_parallel_pdf.py` shipped; Sirach floor `SIRACH_VERSE_COUNTS` shipped. Resume = run the existing pipeline.

**Books:** Pending = Sirach, plus any of pro/ecc/sng/isa/jer/etc. that aren't rendered yet. See `scripts/render_coverage.py --pretty` "Other missing" line.

**Kickoff:**

```powershell
# Resume Sirach Ge'ez ingest:
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" `
  scripts/extract_parallel_pdf.py --book sir --target geez `
  --engine tesseract --language ethi
# Output goes to content/translations/geez-tewahedo/sir.py at SOURCE_QUALITY = "ocr-tier3"
```

**Parallel safety:** Track C writes to `content/translations/geez-tewahedo/<book>.py` for books C reaches. As long as it doesn't touch the manuscript-track books (1sa/2sa/1ki/2ki) or the Patrologia-track books (1ch/2ch/ezr/neh/job), no collision with A/B.

**Watch for:**
- `provenance_tier` lint pin — `ocr-tier3` is registered.
- `render_coverage_no_regression` lint pin — adding books is silent; removing is a fail.

---

## Track D — Amharic NT cadence (τ.7.x.w+ paused)

**Status:** Paused. NT 27/27 canonical floors resolve via `canonical_count()`. `extract_parallel_pdf` supports the Amharic side.

**Books:** All 27 NT books (mat, mrk, luk, jhn, act, rom, 1co, 2co, gal, eph, phi, col, 1th, 2th, 1ti, 2ti, tit, phm, heb, jam, 1pe, 2pe, 1jn, 2jn, 3jn, jud, rev). Total 260 chapters / 7957 verses (canonical ceiling).

**Kickoff:**

```powershell
# Resume Amharic NT ingest (start with the smallest: Philemon 1 ch / 25 v):
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" `
  scripts/extract_parallel_pdf.py --book phm --target amharic `
  --engine tesseract --language amh
# Output: content/translations/amharic-tewahedo/phm.py at SOURCE_QUALITY = "ocr-tier3"
```

**Parallel safety:** Track D writes to `content/translations/amharic-tewahedo/<book>.py` — disjoint from A/B/C/E. Can run simultaneously.

**Watch for:**
- Same lint pins as Track C.
- NT chapter classifier: epistles + Acts are mostly NARRATIVE; Revelation 4-22 may benefit from a new APOCALYPSE class (extend `manuscript_chapter_class` if patterns emerge — currently default NARRATIVE).

---

## Track E — NT Ge'ez (source TBD)

**Status:** Not started. Source identification is the blocker. NT canonical floors resolve via `canonical_count()` — same scaffolding as Track D will apply once source is identified.

**Source candidates:**
- The parallel-Bible-EOTC PDF may have a Ge'ez NT section (verify by browsing the PDF table of contents).
- Patrologia Orientalis volumes contain NT books too — but separately licensed; check archive.org.
- Tewahedo NT manuscripts from CUDL or Gunda Gundē — would be manuscript-collation-tier2 (Track-A-like).

**Once source identified:**

```powershell
# If parallel-PDF source: same as Track D but --target geez --language ethi.
# If Patrologia source: build extract_patrologia_pdf.py first (Track B pipeline).
# If manuscript source: extend Track A's per-track manifest pattern.
# In all cases, write_witness / canonical_count / provenance_tiers are ready.
```

---

## Cross-track conventions (apply to ALL tracks)

1. **Local commit only, no push.** GitHub remote DELETED 2026-05-12. `./save.cmd "<msg>"` from PowerShell.
2. **Lint must stay 14·0·0** at every commit. `python -m scripts.lint_rules` before save.cmd.
3. **`provenance_tier` lint pin** requires every rendered book's `SOURCE_QUALITY` to be a registered tier — add new tier to `scripts/core/provenance_tiers.TIERS` BEFORE shipping a book that uses it.
4. **`manuscript_witnesses` lint pin** requires every `_witness*.json` to validate — use `write_witness` (canonical writer), never raw `json.dump`.
5. **`render_coverage` lint pin** is no-regression — books rendered today must stay rendered. Adding books is silent.
6. **Memories enforce environment:** `$env:PYTHONUTF8="1"` always, full python path (`C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe`), `subprocess.run(stdin=subprocess.DEVNULL)` always.

---

## Quick status

```powershell
# Render coverage across all tracks:
& "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts/render_coverage.py --pretty

# Lint:
& "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m scripts.lint_rules

# Manuscript progress:
& "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts/run_manuscript_collation_at_scale.py --track kings
& "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts/run_manuscript_collation_at_scale.py --track samuel

# Marathon ledger:
type dev\MARATHON_LEDGER.md
```

**Baseline 2026-05-20 EOD (after the audit-U-belt + whole-project ships):**
- geez-tewahedo: 16/82 (20%) rendered
- amharic-tewahedo: 24/82 (29%) rendered
- manuscript track: 8 chapters calibrated (4 Kings + 4 Samuel)
- Patrologia track: 4 PDFs ready (5 books)
- Lint: 14·0·0
- Tests this session: +67 new (manuscript regression 546/0; canonical+render 25/25)
