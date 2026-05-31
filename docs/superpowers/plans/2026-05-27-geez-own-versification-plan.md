# Ge'ez Own-Versification Collation & Standalone-Bible — Implementation Plan
**Status:** in progress — Phases A–C shipped; Phase D re-ingest ongoing

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax. Read the companion spec `docs/superpowers/specs/2026-05-27-geez-own-versification-design.md` FIRST, then the bootstrap triad (RULES → SESSION_STATE → the live master roadmap PLAN named in RULES §0). The marathon plan `docs/superpowers/plans/2026-05-17-kings-manuscript-collation.md` (witness transcription/review mechanics) is UNCHANGED — this plan only changes what happens to the witnesses DOWNSTREAM (collation → cross-ref → store → render).

**Goal:** Restructure the Ge'ez manuscript collation so the standalone Ge'ez Bible carries its OWN (Ge'ez/LXX recension) versification, with KJV demoted to a secondary cross-reference, and build the render path that produces a standalone Ge'ez Bible EPUB.

**Architecture:** Base-witness sense-units become the primary verses (apparatus = the other witness via Ge'ez↔Ge'ez alignment); a new partial-anchoring tool maps Ge'ez verses → KJV verse(s) as an informative cross-reference; an own-versification store + a dedicated standalone render path produce the EPUB. The 9 KJV editions stay byte-stable.

**Tech Stack:** Python 3.14, pytest. Reuses `scripts/core/manuscript_collation.py` (engine), `manuscript_records.py` (witness schema + `validate_witness`), `translations.py` (store loader), `build_edition.py`/`build_epub.py` (render infra). Windows/PowerShell.

**Environment invariants (this box):** python = `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe` (bare `python` is a broken stub); always `$env:PYTHONUTF8="1"`; commit via `save.ps1` (PowerShell ONLY); no git remote (local commits); back up via `git bundle create <E:/F: path> --all` (every 3rd commit + each /clear).

---

## Execution discipline (ALL phases)
- **TDD:** failing test → run-and-confirm-FAIL → minimal implementation → run-and-confirm-PASS → commit. One logical change per commit.
- **Regression guard after ANY engine edit:** run the Samuel-golden invariant tests (`manuscript_qa` R-invariants + `TestCalibrationInvariants`) AND the token-conservation gate BEFORE committing. The 4 Samuel `*_collation.json` goldens are IMMUTABLE — never overwrite them.
- **Parallelism (never-single-thread, RULES):** per-chapter re-collation is a pure function → dispatch parallel subagents (respect the concurrency cap: light <30k MAX 4 / medium 30–100k MAX 2 / heavy >100k MAX 1). Keep a background lane (CAM pre-pull / next re-collation) running at all times.
- **Honesty gates (cardinal):** 0 fabrication; lacuna == witness `⟦illegible⟧`; cross-ref confidence tagged `anchored` vs `interpolated`.

## File structure (created / modified across phases)
- Modify `scripts/core/manuscript_collation.py` — add `collate_base_structured()` (base-witness-primary); keep `collate()` + `_map_objects_to_spine()` for back-compat but route the new path around the KJV binning.
- Create `scripts/core/geez_kjv_xref.py` — Ge'ez-numeral parser + proper-noun transliteration matcher + order-preserving interpolation + confidence.
- Modify `scripts/manuscript_qa.py` — Ge'ez-internal gates; make it Kings/Samuel-aware (currently `_CASES` is Samuel-hardwired); retire the KJV `_SEMANTIC_PASS_FLOOR` as a *fail* (demote to informative).
- Modify `scripts/core/translations.py` — add a `versification` attribute (`own` vs default canonical-KJV).
- Create `scripts/build_standalone.py` (or a `standalone: true` branch in `build_edition.build_one`) — the standalone render path.
- Create per-chapter base-structured outputs `content/manuscript/<track>/collation/<ref>_collation_v2.json` (leaves the 4 Samuel goldens byte-stable).
- Tests: `tests/test_manuscript_collation_basestructured.py`, `tests/test_geez_kjv_xref.py`, `tests/test_build_standalone.py`.

---

## PHASE A — collation engine re-architecture + re-collate (NO data risk; the executable-now phase)

### Task A1: `collate_base_structured()` — base witness's sense-units become the primary verses
**Files:** Modify `scripts/core/manuscript_collation.py`; Test `tests/test_manuscript_collation_basestructured.py`

- [ ] **Step 1 — failing test.** Load the 1ki6 witnesses (`content/manuscript/kings/calibration/1ki6_witness{GG,CAM_hires}.json`). Assert `collate_base_structured(gg, cam, book="1ki", chapter=6)` returns a dict whose `primary_verses` has **len == base-witness sense-unit count** (CAM = 33, since `_pick_base` selects CAM), each entry carrying `{geez_v, geez_text, tokens}` straight from the base witness (no KJV spine, no empties).
```python
def test_base_structured_primary_is_base_witness_units():
    gg, cam = _load("1ki", 6)
    out = mc.collate_base_structured(gg, cam, book="1ki", chapter=6)
    assert out["base_witness"] == "CAM"
    assert len(out["primary_verses"]) == 33          # CAM's own units, not 38 KJV
    assert all(v["geez_text"] for v in out["primary_verses"])  # no empty spine rows
```
- [ ] **Step 2 — run, confirm FAIL** (`collate_base_structured` undefined). Run: `…python.exe -m pytest tests/test_manuscript_collation_basestructured.py -v` (with `PYTHONUTF8=1`).
- [ ] **Step 3 — implement minimally.** Add `collate_base_structured(gg, cam, *, book, chapter)`: call `_pick_base(gg, cam)` → base/other; `primary_verses` = the base witness's `verses` (geez/tokens) in order; do NOT call `load_kjv_skeleton` or `_map_objects_to_spine`.
- [ ] **Step 4 — run, confirm PASS.**
- [ ] **Step 5 — commit.** `save.ps1 -Message "Phase A1: base-structured collation primary = base-witness units (1ki6)"`

### Task A2: apparatus from the OTHER witness via Ge'ez↔Ge'ez alignment
**Files:** Modify `scripts/core/manuscript_collation.py`; Test same file.
- [ ] **Step 1 — failing test.** Assert each `primary_verses[i]` has an `apparatus` list aligning the other witness (GG) to that base verse using the existing `align_verse`, with classes in {agree, disagree, lacuna, insertion}; assert **token conservation**: every GG token + every CAM token appears exactly once across the apparatus (reuse the existing token-conservation checker).
```python
def test_token_conservation_base_structured():
    gg, cam = _load("1ki", 6)
    out = mc.collate_base_structured(gg, cam, book="1ki", chapter=6)
    assert mc.tokens_conserved(out, gg, cam)   # GG 433==433, CAM 500==500
```
- [ ] **Step 2 — run, FAIL.**
- [ ] **Step 3 — implement.** For each base verse, align the corresponding other-witness unit(s) via `align_verse`; where the other witness has no parallel unit (recension minus) → a `lacuna`/one-sided row; where it has extra → `insertion`. Map other-witness units to base verses by their own order + the existing alignment (NOT positional KJV binning).
- [ ] **Step 4 — run, PASS** (token conservation holds).
- [ ] **Step 5 — commit.** `Phase A2: other-witness apparatus via Ge'ez alignment + token conservation`

### Task A3: Ge'ez-internal metrics; retire the KJV semantic FLOOR as a fail
**Files:** Modify `scripts/core/manuscript_collation.py` (`compute_metrics`) + `scripts/manuscript_qa.py`; Test same.
- [ ] **Step 1 — failing test.** Assert `out["metrics"]` reports `witness_agreement_pct`, `lacuna_counts`, and an INFORMATIVE `kjv_coverage` (filled in Phase B), and that there is **no pass/fail keyed on KJV slot coverage**. Assert a recension-shorter chapter (1ki6) is NOT marked `fail`.
- [ ] **Step 2 — run, FAIL.**
- [ ] **Step 3 — implement.** Add Ge'ez-internal metrics; in `manuscript_qa.py` replace the `_SEMANTIC_PASS_FLOOR` *fail* with: fail iff (fabrication > 0) OR (a base verse is fully illegible with no honest lacuna marker) OR (token conservation broken). KJV coverage becomes a reported number, not a gate.
- [ ] **Step 4 — run, PASS.**
- [ ] **Step 5 — commit.** `Phase A3: Ge'ez-internal collation metrics; KJV coverage informative, not a gate`

### Task A4: re-collate the 10 done chapters (parallel); keep Samuel goldens byte-stable
**Files:** Create `content/manuscript/{kings,samuel}/collation/<ref>_collation_v2.json`; Test `tests/test_manuscript_collation_basestructured.py`
- [ ] **Step 1 — failing test.** Parametrized over the 10 refs (1ki1–6, 1sa1, 1sa3, 1sa17, 2sa11): assert a `<ref>_collation_v2.json` exists, loads, has base-structured shape, 0 fabrication, honest lacunae. Assert the original 4 Samuel `*_collation.json` goldens are **byte-identical** to git HEAD (immutability).
- [ ] **Step 2 — run, FAIL** (v2 files absent).
- [ ] **Step 3 — implement.** A small driver `collate_base_structured` over each ref's witnesses → write `<ref>_collation_v2.json` (atomic). Dispatch the 10 as parallel subagents (per-chapter pure). Do NOT touch the goldens.
- [ ] **Step 4 — run, PASS** (10 v2 files; goldens unchanged).
- [ ] **Step 5 — commit + E:/F: backup.** `Phase A4: re-collate 10 chapters base-structured (v2); Samuel goldens preserved`

---

## PHASE B — geez→kjv partial-anchoring cross-reference tool
> Expand to its own detailed plan at phase start (`docs/superpowers/plans/<date>-geez-kjv-xref-plan.md`). Task outline:
- **B1** `scripts/core/geez_kjv_xref.py`: Ge'ez-numeral parser (፩–፼ → int; e.g. ፬፻፹ → 480). TDD against 1ki6 v1 (480), the cubit numerals (፷=60, ፳=20, ፴=30).
- **B2** proper-noun transliteration matcher (Ge'ez fidel → Latin → fuzzy-match KJV verse tokens): ሰሎሞን↔Solomon, ግብጽ↔Egypt, ሊባኖስ↔Lebanon, ኪሩብ↔cherub, እስራኤል↔Israel.
- **B3** order-preserving interpolation between hard anchors; `confidence ∈ {anchored, interpolated}` per Ge'ez verse.
- **B4** integrate: write `kjv_xref` into each `<ref>_collation_v2.json`; validate against 1ki6 known anchors (v1=480→KJV 6:1; the vv11–12 cluster; v38 11th-year completion). Parallel per chapter.

## PHASE C — standalone render path + first Ge'ez Bible EPUB
> Own detailed plan at phase start. Task outline:
- **C1** `scripts/core/translations.py`: add a `versification` attribute (`own` vs canonical); loader reads it without breaking the 9 KJV editions.
- **C2** generate an own-versification Ge'ez store for Samuel/Kings FROM the `<ref>_collation_v2.json` (each base verse → `(ch, geez_v, geez_text)` + EN back-translation + kjv_xref).
- **C3** `scripts/build_standalone.py` (or a `standalone: true` branch in `build_one`): render the Ge'ez body from the own-versification store; popups = EN back-translation + KJV cross-ref + apparatus.
- **C4** build the first standalone Ge'ez Bible EPUB (Samuel/Kings + Psalms which already has own-versification); epubcheck 0/0; PROVE the 9 KJV editions are byte-stable.

## PHASE D — own-versification re-ingest of the 15 KJV-renumbered store books (DATA-GATED)
> Own detailed plan; sequenced LAST. Each book gated on a versification-preserving source (GAPS folder + clean PD critical editions per SCOPE §3/§4). Generalize the Psalms `source_authoritative: true` ingest (skip `renumber_against_floor`). Book-by-book, parallel as sources confirm. This is the real risk; isolate it here.

## Cross-cutting — RULES codification (done THIS session, recorded here)
- Top-level **no-shortcuts / completeness-first / can-pause / can-stop-and-redesign** principle.
- **Never-single-thread** rule + the side-task backlog + auto-pick-next.

---

## Self-review (against the spec)
- **Spec coverage:** §3.2 collation → Phase A; §3.3 cross-ref → Phase B; §3.4 store → Phase C (C1–C2); §3.5 render → Phase C (C3–C4); §4 Phase D → Phase D; §8 rules → cross-cutting. All sections mapped. ✓
- **Placeholders:** Phase A is concrete (files, tests, commits). B/C/D are deliberately outlines pending their own plans (per the writing-plans scope-check for multi-subsystem specs) — flagged explicitly, not hidden TODOs. ✓
- **Type/name consistency:** `collate_base_structured`, `primary_verses`, `<ref>_collation_v2.json`, `kjv_xref`, `versification` used consistently across tasks. ✓
- **Immutability:** the 4 Samuel goldens are pinned byte-stable (A4 test) so the engine-vs-hand invariant survives. ✓
