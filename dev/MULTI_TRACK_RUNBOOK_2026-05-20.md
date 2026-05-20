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

## Track B — Patrologia Orientalis ingest (τ.6.x.5.a SHIPPED; .b+ active)

**Status:** ACTIVE. τ.6.x.5.a shipped 2026-05-20 — `scripts/extract_patrologia_pdf.py` (900+ lines, 65 tests) + Job at **patrologia-printed-tier1** with **exact 1070/1070 canonical KJV match across all 42 chapters**. Pipeline operational. Esther (τ.6.x.5.b) dispatched 2026-05-20 in this session.

**Design spec:** `docs/superpowers/specs/2026-05-20-patrologia-ingest-design.md`.

**Books shipped:** job (τ.6.x.5.a). In flight: est_patrologia (τ.6.x.5.b, separate file per spec D4 — DO NOT overwrite the existing `est.py` ocr-tier3 ship).

**Books pending:** ezr + neh (τ.6.x.5.c, PO 13 fasc 5 Pereira 1919), 1ch + 2ch (τ.6.x.5.d, PO 23 fasc 4 Grébaut 1932 — heaviest volume).

**Notable pipeline findings codified at τ.6.x.5.a:**
- **Layout is TOP/BOTTOM, not LEFT/RIGHT** as the design spec assumed — verified empirically. Ge'ez body occupies the top ~60% (with a French banner strip at top ~6%); French translation + apparatus is the bottom ~40%. `_render_strip_to_png(strip='geez'|'fra'|'banner')` handles this.
- **French banner-anchored chapter detection** — PO Ge'ez body has NO `ምዕራፍ` banners; only Ethiopic-numeral verse markers in the margin (which Tesseract drops). The script extracts the French banner `LE LIVRE DE <BOOK>, <ROMAN>, <range>` from a thin top-strip and parses the Roman numeral as the chapter number. Pages without a recognizable banner inherit the previous chapter.
- **`renumber_against_canonical_with_merge` variant** — Pereira's print uses `።` for mid-verse colometric pauses (2.5× over-segmentation vs canonical), so the OT-narrative `renumber_against_floor` from `extract_parallel_pdf.py` hard-fails. The new `_with_merge` variant proportionally distributes fragments across canonical chapters and concatenates adjacent fragments to fit each chapter's canonical verse count. τ.6.x.3 batched audit can refine the merge boundaries using the French translation as a guide.
- **`text-layer` engine errors cleanly** — PO PDFs have no embedded text layer; CLI accepts `--engine text-layer` for spec parity but raises a directing-error.

**REAL kickoff CLI (per the operational τ.6.x.5.a Job ship):**

```powershell
# τ.6.x.5.b Esther Patrologia (in flight):
$env:PYTHONUTF8="1"
& "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m scripts.extract_patrologia_pdf `
  --book est --output content/translations/geez-tewahedo/est_patrologia.py `
  --pdf GAPS/5_Esther/Esther__PO-9-fasc-1_Pereira_1913.pdf `
  --target geez --engine tesseract --language ethi `
  --page-start <NN> --page-end <NN> `
  --source-tag patrologia-orientalis-vol9-fasc1-pereira-1913 `
  --ingest-phase "τ.6.x.5.b"
# OCR-probe the PDF first to find the empirical page range (Track B used this
# technique for Job=584-697; documented in extract_patrologia_pdf.py).
```

**Parallel safety:** Track B writes to `content/translations/geez-tewahedo/{1ch,2ch,ezr,neh,job,est_patrologia}.py` — distinct files from any other track. Can run simultaneously with A/C/D.

**Watch for:**
- `provenance_tier` lint pin checks the SOURCE_QUALITY field — use the registered `patrologia-printed-tier1` (already in `scripts/core/provenance_tiers.TIERS`).
- Esther overlap with the parallel-PDF `est.py` — per spec D4 + user confirmation, **keep both files** (`est.py` + `est_patrologia.py`). DO NOT overwrite `est.py`.
- PO_SOURCES registry in `extract_patrologia_pdf.py` carries placeholder `(0,0)` page ranges for est/ezr-neh/chronicles — operator passes `--page-start`/`--page-end` per ingest, or a later phase calibrates them by OCR-probe.

---

## Track C — Parallel-PDF Ge'ez catchup (τ.6.x.2.o-s, ACTIVE)

**Status:** ACTIVE. Sirach (τ.6.x.2.o) + 4ba (τ.6.x.2.p) + bar (τ.6.x.2.q) + wis (τ.6.x.2.r) + paz/bel (τ.6.x.2.s daniel-additions drain) all shipped 2026-05-20. Next pending = `jubilees` (τ.6.x.2.t — large book; manifest-mapped at [1454,1514]), then `one_enoch`.

**Books:** Catchup queue order = sir → 4ba → bar → wis → daniel-additions (paz+bel; sus deferred `present_in_pdf:false`) → jubilees → one_enoch → other missing (pro/ecc/sng/isa/jer/lam/eze/dan + the Twelve + Lamentations). See `scripts/render_coverage.py --pretty` "Other missing" line for the full residual.

**REAL kickoff CLI (verified against `scripts/extract_parallel_pdf.py` argparse):**

```powershell
# Resume Ge'ez catchup — example: any pending book in the queue.
# CRITICAL: the script's CLI does NOT accept --book/--target/--language.
# Use --section/--lang/--renumber (the actual argparse choices).
# Must invoke as module (`-m scripts.extract_parallel_pdf`); direct path errors
# because scripts.core.paths needs Python's module-search machinery.
$env:PYTHONUTF8="1"
& "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m scripts.extract_parallel_pdf `
  --section <section_name> --lang geez --paragraph-mode `
  --renumber <renumber_name> --engine tesseract `
  --ingest-phase "τ.6.x.2.<letter>"
# Section + renumber names come from _source.yaml structural_map +
# extract_parallel_pdf.py argparse `--section`/`--renumber` choices.
# Output lands at content/translations/geez-tewahedo/<book>.py at SOURCE_QUALITY = "ocr-tier3".
```

**Concrete recent invocations** (for reference):
- `--section sirach --lang geez --paragraph-mode --renumber sirach --engine tesseract --ingest-phase "τ.6.x.2.o"`
- `--section paralipomena_jeremiah --lang geez --paragraph-mode --renumber four_baruch --engine tesseract --ingest-phase "τ.6.x.2.p"`
- `--section baruch --lang geez --paragraph-mode --renumber baruch --engine tesseract --ingest-phase "τ.6.x.2.q"`
- `--section wisdom_of_solomon --lang geez --paragraph-mode --renumber wisdom_of_solomon --engine tesseract --ingest-phase "τ.6.x.2.r"`
- `--section prayer_of_azariah --lang geez --paragraph-mode --renumber <…> --engine tesseract --ingest-phase "τ.6.x.2.s"` (paz)
- `--section bel_and_the_dragon --lang geez --paragraph-mode --renumber <…> --engine tesseract --ingest-phase "τ.6.x.2.s"` (bel)

**Share-pin cascade discipline.** Each τ.6.x.2.* ship flips one or more `test_geez_*_still_deferred` pins from negative to durable-positive form, and renames the test class so the NEXT deferred book is the visible queue head. Grep `tests/test_parallel_bible_*.py` for `*_still_deferred` to find the active cascade. Per memory `feedback_share_pin_pattern`, a cascade often spans 2+ test files — search broadly.

**Parallel safety:** Track C writes to `content/translations/geez-tewahedo/<book>.py` for books C reaches. As long as it doesn't touch the manuscript-track books (1sa/2sa/1ki/2ki) or the Patrologia-track books (1ch/2ch/ezr/neh/job), no collision with A/B.

**Watch for:**
- `provenance_tier` lint pin — `ocr-tier3` is registered.
- `render_coverage_no_regression` lint pin — adding books is silent; removing is a fail.

---

## Track D — NT cadence (τ.6.x.NT.a SHIPPED 2026-05-20; .b+ unblocked)

**Status:** UNBLOCKED. τ.6.x.NT.a shipped 2026-05-20 — NT pre-pass (`_nt_prepass` in `scripts/extract_parallel_pdf.py`) filters pericope headers (`ክፍል N፡ <title>`), strips inline chapter markers + cross-reference apparatus, merges colometric continuations. The previous τ.7.x.v "GROSS over-segmentation" honest-fail on NT books is resolved by this pre-pass. Philemon (phm) + Jude (jud) shipped on BOTH Amharic + Ge'ez sides as smoke validation.

**Books shipped:** phm + jud on both sides at τ.6.x.NT.a. Next priority = τ.6.x.NT.b Matthew re-attempt (original overflow case; floor + structural_map already wired at τ.7.x.v).

**Books pending:** All other 25 NT books (mat, mrk, luk, jhn, act, rom, 1co, 2co, gal, eph, phi, col deferred-present_in_pdf:false, 1th, 2th, 1ti, 2ti, tit, heb, jam, 1pe, 2pe, 1jn, 2jn, 3jn, rev). Total 260 chapters / 7957 verses (canonical ceiling). col is the one PDF gap per Track E scope spec; the rest are sourceable from the same parallel-bible-eotc PDF (NT block pp1567-2106).

**REAL kickoff CLI:**

```powershell
# τ.6.x.NT.b Matthew re-attempt — should now pass the pre-pass:
$env:PYTHONUTF8="1"
& "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m scripts.extract_parallel_pdf `
  --section matthew --lang amharic --paragraph-mode `
  --renumber matthew --engine tesseract `
  --ingest-phase "τ.6.x.NT.b"
# Repeat with --lang geez for the Ge'ez side.
# Output: content/translations/{amharic,geez}-tewahedo/mat.py at SOURCE_QUALITY = "ocr-tier3".
```

**For singleton NT books NOT yet structurally mapped** (mrk, luk, jhn, act, rom, gal, eph, phi, tit, heb, jam, rev): extend `_source.yaml.structural_map` with a new section (mirror the τ.6.x.NT.a `philemon`+`jude` blocks); add a `<book>_VERSE_COUNTS` dict + `--renumber` argparse choice + `--section` argparse choice in `scripts/extract_parallel_pdf.py`. The per-book pages are documented in `docs/superpowers/specs/2026-05-20-nt-geez-source-scope.md` §2 table.

**For combined-block NT books** (1-2 Cor pp1915-1961, 1-2 Thes pp1995-2005, 1-2 Tim pp2006-2018, 1-2 Pet pp2045-2057, 1-3 Jn pp2058-2065): build a within-section splitter mirroring the meqabyan-trilogy `subsections` pattern in `_source.yaml`. Track D explicitly deferred this for the smoke phase; it's the τ.6.x.NT.c-equivalent work.

**Parallel safety:** Track D writes to `content/translations/{amharic,geez}-tewahedo/<nt_book>.py` + amends `scripts/extract_parallel_pdf.py` + `_source.yaml` + `scripts/lint_rules.py` expected-books. The pre-pass is additive guarded by `is_nt_book(section_name)` — OT path bytewise identical.

**Watch for:**
- New NT chapter complexity classes: epistles + Acts are mostly NARRATIVE; Revelation 4-22 may benefit from a new APOCALYPSE class in `manuscript_chapter_class` if patterns emerge (currently default NARRATIVE).
- Pre-pass tolerance — phm Amharic shipped 30v vs 25 floor (5 colophon-residue overflow into synthetic ch 2), within the ±10v renumber tolerance. Similar pattern expected on other NT books. τ.6.x.3 batched audit will reconcile.

---

## Track E — NT Ge'ez source scope (✅ SHIPPED 2026-05-20)

**Status:** ✅ SHIPPED. `docs/superpowers/specs/2026-05-20-nt-geez-source-scope.md` is the authoritative source-class identification spec.

**Verdict:** NT Ge'ez source = the SAME parallel-bible-eotc PDF the OT side ships from. NT block at pp1567-2106 (540 pages). **26 of 27 NT books reachable** (Colossians is the one gap — `present_in_pdf:false` per the `laodiceans`/`susanna` precedent; deferred to a future external-source ship).

**Phase tag mapping:** Track E → Track D's τ.6.x.NT.a-g sub-phases. Track E's spec is the roadmap; Track D's pre-pass is the execution.

**Recommended starting book per spec §2:** Philemon (pp2023-2024, 2 PDF pages, 1 ch / 25 v, single-block) — already shipped at τ.6.x.NT.a.

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
