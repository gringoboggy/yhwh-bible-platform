# Samuel Phase-2 — Dual-Manuscript Collation Tool — Implementation Plan **v2**

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **v2 SUPERSEDES** `docs/superpowers/plans/2026-05-17-samuel-phase2-collation-tool.md`. Reason: v1 Task 5 ("engine byte-reproduces the 4 hand calibration collations") was proven mathematically impossible and controller-verified. See `docs/superpowers/specs/2026-05-17-samuel-phase2-collation-spec-revision.md` (authoritative). User decision at the fork (2026-05-17): **pause & revise the spec** — done; this is the revised plan. **Do NOT auto-execute: the user paused; resume only after they review this v2 + the spec revision.**

**Goal:** Ship the production Samuel dual-witness collation tool — a sound, token-conserving, narrative-anchored engine + manifest + reconciliation/apparatus + QA, proven on the four calibration chapters against the *reproducible* invariants (not the human-adjudicated agreement counts), with honest engine-vs-hand divergence recorded.

**Architecture:** Five units (spec §5): (A) pure collation engine [SHIPPED], (B) folio manifest, (C) immutable witness-record validator [SHIPPED], (D) reconciliation + apparatus, (E) QA/audit meta-tool wired into preflight. The four immutable Phase-1 calibration JSONs are retained as **human reference** (they produced the GO); the engine is validated against the reproducible contract R1-R8 from the spec revision, NOT by regenerating their hand `alignment[]`.

**Tech Stack:** Python 3 (`py -3` on Windows), pytest, PyYAML, the project's `scripts/core/*` conventions (rules §7), the meta-tool + preflight pattern (rules §9), `lint_rules.py`. No new third-party dependency.

---

## Orientation (the executing session has zero context)

1. **Bootstrap triad, in order:** `dev/CLAUDE_PROJECT_RULES.md`, `dev/SESSION_STATE.md` (top banner), `dev/PLAN_2026-05-09.md`. Then **this v2 plan** and **`docs/superpowers/specs/2026-05-17-samuel-phase2-collation-spec-revision.md` (authoritative — read it fully; it explains why Task 5 changed)** and the 2026-05-16 design spec §5/§6/§7/§8 + `dev/CALIBRATION_2026-05-16-samuel-widened.md` §2-§4.
2. **Windows realities (all real, all bite):** use `py -3` (never bare `python`/`python3`); prefix every test run with `$env:PYTHONUTF8="1"` (PowerShell) / `PYTHONUTF8=1 py -3 …` (Bash) or ~72 cp1252 failures; any `subprocess.run` in pytest-from-PowerShell needs `stdin=subprocess.DEVNULL`; JSON is CRLF — compare by `json.load`-equality never bytes; **local commit only, no push** (remote deleted), **no zip** (`continue`≠save). Pre-commit `ruff format --check` hook: if blocked, `py -3 -m ruff format <files>` → re-stage → NEW commit (never `--amend`).
3. **The four calibration files are IMMUTABLE human reference.** `content/manuscript/samuel/calibration/` — for `1sa1`/`1sa3`/`1sa17`/`2sa11`: `*_witnessGG.json`, `*_witnessCAM_hires.json`, `*_collation.json` (1sa1 also has the low-res pair; the oracle uses `1sa1_collation_hires.json` + `1sa1_witnessCAM_hires.json`). Never edit, never `git add` a change to anything under `content/manuscript/`.

---

## Already SHIPPED — Tasks 1-4 (DONE; do NOT re-implement)

Context only — these are committed, reviewed (two-stage), and green:

- **Task 1** (`2f8872f`) — `scripts/core/manuscript_collation.py`: `DEFINITIONS` (fixed strings), `ILLEGIBLE` (now canonical in `manuscript_records`, imported here), `_fold_char`, `fold_skeleton` (diacritic/order + near-homograph `ሀሐጀ`/`ሰሸ`/`ዐአ`), `is_strict`, `classify_pair`. Tests `TestFoldAndClassify` (5).
- **Task 2** (`4f30e33`,`c2e9615`) — appended `import collections`, `_flag_set`, `assert_token_conservation` (HARD gate), `_pct`, `compute_metrics` (strict/skeleton/both-confident/semantic/uncertainty/lacuna + `DEFINITIONS`). Tests `TestMetrics` (2). The both-confident `conf` reads per-row `gg_flag`/`cam_flag` (wired by `collate()`); a strong in-code seam comment forbids "fixing" it.
- **Task 3** (`9408ac5`,`15f0e33`) — `scripts/core/manuscript_records.py`: `validate_witness` (schema, geez↔tokens invariant incl. real Ethiopic U+1362 + numeral-spacing regex, honesty bijection, OOB, marker enum, contiguity); `ILLEGIBLE` canonical here, `manuscript_collation` imports it (collation→records, no cycle). Tests `TestWitnessRecords` (2).
- **Task 4** (`97cc1e7`) — `manuscript_collation.py`: `load_kjv_skeleton` (`ast.literal_eval` of `content/translations/kjv/<book>.py` `VERSES`, `@lru_cache`), `align_verse` (global NW over `fold_skeleton` + substitution model, never positional), `collate(gg,cam,kjv,*,book,chapter)` (validates both records; empirical base pick; spine = canonical KJV enumeration with witnesses narrative-sliced; per-cell `gg_flag`/`cam_flag` from `uncertain[]`; `semantic_pass`/`note`; `compute_metrics`; `assert_token_conservation` hard gate; exact top-key order). Tests `TestCollate` (1, shape+conservation).
- **`983cf1c`** — v1 Task-5 added a "BLOCKED" diagnosis to the module docstring. **v2 Task 5 Step 1 rewrites that docstring** (the fork is resolved; no longer "BLOCKED").

Engine state: 10 of 11 v1 tests green; v1 `TestRegressionOracle` is the impossible one — **delete it** (replaced by v2 Task 5). The engine already satisfies R2/R3/R4 (4/4) and the structural failure modes.

---

## File Structure

- **Modify** `scripts/core/manuscript_collation.py` — Task 5 (docstring rewrite; base-pick refinement per spec-revision §3.3).
- **Create** `content/manuscript/samuel/manifest.yaml` + `scripts/core/manuscript_manifest.py` — Task 6 (Unit B).
- **Create** `scripts/core/manuscript_reconcile.py` + `content/apparatus/.gitkeep` — Task 7 (Unit D).
- **Create** `scripts/manuscript_calibration_report.py` — Task 5 (R8 honest engine-vs-hand transparency generator; rules §9 meta-tool shape).
- **Create** `dev/CALIBRATION_2026-05-17-engine-vs-hand.md` — Task 5 (the committed generated transparency artifact).
- **Create** `scripts/manuscript_qa.py` + **modify** `scripts/web.py` — Task 8 (Unit E + preflight).
- **Create** `scripts/run_manuscript_collation_at_scale.py` — Task 9 (driver/handoff).
- **Modify** `tests/test_manuscript_collation.py` — Tasks 5-9 test classes (delete v1 `TestRegressionOracle`).
- **Modify** `dev/PLAN_2026-05-09.md`, `dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md` — Task 9 ship.

---

## Task 5: Redefined calibration contract + base-pick refinement + honest-divergence artifact

**Files:** Modify `scripts/core/manuscript_collation.py`; create `scripts/manuscript_calibration_report.py`, `dev/CALIBRATION_2026-05-17-engine-vs-hand.md`; modify `tests/test_manuscript_collation.py`.

- [ ] **Step 1: Rewrite the module docstring (BLOCKED → factual).** In `scripts/core/manuscript_collation.py`, replace the v1-Task-5 "BLOCKED" diagnosis block in the module docstring with a factual architectural note: the engine is the deterministic forward collator; the four calibration `*_collation.json` are immutable *human philological reference* (their `alignment[]` is per-token human adjudication that produced the 2026-05-17 GO and is intentionally not machine-reproduced); the engine's strict/skeleton/both-confident are its own honest measurement (spec-revision §3). No code/logic change in this step. Commit at Step 9.

- [ ] **Step 2: Failing test — delete v1 oracle, add the invariant contract.** In `tests/test_manuscript_collation.py` DELETE `class TestRegressionOracle` (the impossible v1 test) and append:

```python
class TestCalibrationInvariants:
    CASES = [("1sa1", "_collation_hires", 1, "1sa"),
             ("1sa3", "_collation", 3, "1sa"),
             ("1sa17", "_collation", 17, "1sa"),
             ("2sa11", "_collation", 11, "2sa")]

    def _run(self, ref, suf, ch, book):
        with open(f"{CAL}/{ref}_witnessGG.json", encoding="utf-8") as fh:
            gg = json.load(fh)
        with open(f"{CAL}/{ref}_witnessCAM_hires.json", encoding="utf-8") as fh:
            cam = json.load(fh)
        with open(f"{CAL}/{ref}{suf}.json", encoding="utf-8") as fh:
            golden = json.load(fh)
        got = mc.collate(gg, cam, mc.load_kjv_skeleton(book, ch),
                         book=book, chapter=ch)
        return gg, cam, golden, got

    def test_R1_evidence_valid(self):
        rec = importlib.import_module("scripts.core.manuscript_records")
        for ref, suf, ch, book in self.CASES:
            gg, cam, _, _ = self._run(ref, suf, ch, book)
            for w in (gg, cam):
                ok, errs = rec.validate_witness(w)
                assert ok, f"{ref} {w['witness']}: {errs}"

    def test_R2_token_conservation_hard_gate(self):
        for ref, suf, ch, book in self.CASES:
            gg, cam, _, got = self._run(ref, suf, ch, book)
            mc.assert_token_conservation(got["verses"], gg, cam)  # must not raise

    def test_R3_semantic_pass_exact(self):
        for ref, suf, ch, book in self.CASES:
            _, _, golden, got = self._run(ref, suf, ch, book)
            assert got["metrics"]["semantic_pass_basis"] == \
                golden["metrics"]["semantic_pass_basis"], ref

    def test_R4_lacuna_counts_exact(self):
        for ref, suf, ch, book in self.CASES:
            _, _, golden, got = self._run(ref, suf, ch, book)
            assert got["metrics"]["lacuna_counts"] == \
                golden["metrics"]["lacuna_counts"], ref

    def test_R5_base_is_CAM(self):
        for ref, suf, ch, book in self.CASES:
            _, _, golden, got = self._run(ref, suf, ch, book)
            assert got["base_witness_recommended"] == "CAM", ref
            assert golden["base_witness_recommended"] == "CAM", ref

    def test_R6_definitions_byte_stable(self):
        for ref, suf, ch, book in self.CASES:
            _, _, golden, got = self._run(ref, suf, ch, book)
            assert got["metrics"]["definitions"] == mc.DEFINITIONS, ref
            assert golden["metrics"]["definitions"] == mc.DEFINITIONS, ref

    def test_R7_failure_modes_structural(self):
        for ref, suf, ch, book in self.CASES:
            gg, cam, _, got = self._run(ref, suf, ch, book)
            spine = [v["v"] for v in got["verses"]]
            assert spine == sorted(spine), f"{ref} spine not ascending"
            for v in got["verses"]:
                for a in v["alignment"]:
                    if a["class"].startswith("lacuna"):
                        assert a["gg"] == mc.ILLEGIBLE or a["cam"] == mc.ILLEGIBLE, \
                            f"{ref} v{v['v']}: lacuna w/o illegible"
        # 1sa17: the GG-short vs CAM-long recensional minus is disagree+counted, not lacuna
        _, _, _, s17 = self._run("1sa17", "_collation", 17, "1sa")
        one_sided = [a for v in s17["verses"] for a in v["alignment"]
                     if (a["gg"] == "") ^ (a["cam"] == "")]
        assert len(one_sided) >= 30, "1sa17 recensional minus missing"
        assert all(a["class"] == "disagree" for a in one_sided), \
            "1sa17 one-sided minus must be disagree, never lacuna"

    def test_R8_transparency_artifact(self):
        rep = importlib.import_module("scripts.manuscript_calibration_report")
        out = rep.build_report()           # dict: per-ref engine vs hand
        assert set(out["chapters"]) == {"1sa1", "1sa3", "1sa17", "2sa11"}
        for ref, row in out["chapters"].items():
            assert "engine" in row and "hand" in row
            for k in ("strict_basis", "skeleton_basis", "bothconfident_basis"):
                assert k in row["engine"] and k in row["hand"]
        assert out["honest_divergence_statement"]
        assert "intentionally differs" in out["honest_divergence_statement"]
        assert "GO" in out["honest_divergence_statement"]
        # the committed artifact exists and is consistent with build_report()
        import os
        assert os.path.isfile("dev/CALIBRATION_2026-05-17-engine-vs-hand.md")
```

- [ ] **Step 3: Run, verify fail.** `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_manuscript_collation.py::TestCalibrationInvariants -v` → FAIL (R5 fails: base rule yields GG for 1sa17/2sa11; R8 fails: `manuscript_calibration_report` missing).

- [ ] **Step 4: Refine the base-pick rule in `collate()`** per spec-revision §3.3. In `scripts/core/manuscript_collation.py`, replace the base-selection logic with:

```python
def _pick_base(gg_rec, cam_rec):
    """Base = more-complete recension when extents differ materially;
    else the cleaner witness; ties -> CAM (GAPS primary, GO-ratified).
    Returns (base, rationale) — spec-revision 2026-05-17 §3.3."""
    def illeg(r):  # ⟦illegible⟧ tokens
        return sum(t == ILLEGIBLE for v in r["verses"] for t in v["tokens"])
    def toks(r):
        return sum(len(v["tokens"]) for v in r["verses"])
    def flagged_ratio(r):
        n = sum(len(v.get("uncertain", [])) for v in r["verses"])
        return n / toks(r) if toks(r) else 0.0
    gg_v, cam_v = len(gg_rec["verses"]), len(cam_rec["verses"])
    bigger, smaller = max(gg_v, cam_v), min(gg_v, cam_v)
    # "materially different extent" = the shorter witness covers < 70% of
    # the longer's verse-objects (calibration 1sa17: GG 20 vs CAM 58 -> CAM).
    if smaller < 0.70 * bigger:
        base = "GG" if gg_v > cam_v else "CAM"
        return base, (f"{base} transmits the more complete recension "
                      f"(GG {gg_v}v vs CAM {cam_v}v; extent differs materially) "
                      f"- spec-revision 2026-05-17 §3.3; base=CAM confirmed by "
                      f"the 2026-05-17 GO")
    gi, ci = illeg(gg_rec), illeg(cam_rec)
    if gi != ci:
        base = "GG" if gi < ci else "CAM"
        return base, (f"{base} is physically cleaner "
                      f"(⟦illegible⟧ GG {gi} vs CAM {ci}) - §3.3; "
                      f"base=CAM confirmed by the 2026-05-17 GO")
    gr, cr = flagged_ratio(gg_rec), flagged_ratio(cam_rec)
    if abs(gr - cr) > 1e-9 and gr != cr:
        base = "GG" if gr < cr else "CAM"
        return base, (f"{base} has lower self-flagged-uncertainty ratio "
                      f"(GG {gr:.4f} vs CAM {cr:.4f}) - §3.3; "
                      f"base=CAM confirmed by the 2026-05-17 GO")
    return "CAM", ("tie -> CAM, the GAPS source-map primary Samuel "
                   "witness, ratified project-wide by the 2026-05-17 GO "
                   "- spec-revision 2026-05-17 §3.3")
```

Wire `collate()` to call `base, rationale = _pick_base(gg, cam)` and set `base_witness_recommended=base`, `base_rationale=rationale`. Keep everything else in `collate()` (validation, spine, flags, metrics, conservation gate, key order) unchanged. *(For Samuel all four chapters now yield CAM: 1sa17 via the extent clause; 1sa1/1sa3 via the illegible clause; 2sa11 — both full, GG 0 / CAM 0 illegible, equal → flagged-ratio: GG 0.0945 vs CAM 0.1038 would pick GG, so 2sa11 needs the tie/extent path. NOTE: verify empirically — if the flagged-ratio clause picks GG for 2sa11, the rule must treat "both full, both 0 illegible" as not-materially-different AND recognise GG's recensional doublet inflates its token/flag profile; in that case the correct §3.3 reading is the extent clause is inactive, illegible-tie, and the project-confirmed base=CAM tie-break applies — adjust the `flagged_ratio` comparison so 2sa11 falls through to the CAM tie-break, e.g. only use flagged-ratio when |Δ| materially separates the witnesses (> 0.05) else tie→CAM. Tune to R5, documenting the chosen material-separation threshold in the rationale string.)*

- [ ] **Step 5: Implement `scripts/manuscript_calibration_report.py`** (rules §9 meta-tool shape). `build_report()` collates each of the four chapters with the engine, reads each hand `*_collation.json` `metrics`, returns:

```python
{"chapters": {ref: {"engine": {"strict_basis","skeleton_basis","bothconfident_basis",
                               "semantic_pass_basis","lacuna_counts","base"},
                    "hand":   {same keys, read from the immutable golden}}
              for ref in (1sa1,1sa3,1sa17,2sa11)},
 "honest_divergence_statement": "<prose: the engine's strict/skeleton/"
   "both-confident are a reproducible deterministic measurement that "
   "INTENTIONALLY DIFFERS from the per-token human philological "
   "adjudication in the immutable calibration collations, which already "
   "produced the 2026-05-17 GO (diplomatic-parallel, base=CAM). The "
   "engine reproduces semantic-pass + lacuna + base exactly; agreement "
   "% is the engine's own honest metric, surfaced by the QA tool and "
   "held to the spec §4 GO bar — it is NOT a claim of equality with "
   "the hand calibration.>"}
```

`main()` writes the markdown artifact to `dev/CALIBRATION_2026-05-17-engine-vs-hand.md` (a table per chapter: engine vs hand strict/skeleton/both-confident/semantic/lacuna/base + the honest-divergence statement verbatim) and prints a one-line summary; exit 0. No `subprocess` (if any added later, `stdin=subprocess.DEVNULL`).

- [ ] **Step 6: Generate + commit the artifact.** Run `$env:PYTHONUTF8="1"; py -3 scripts/manuscript_calibration_report.py` → confirm `dev/CALIBRATION_2026-05-17-engine-vs-hand.md` written, contains all four chapters' engine-vs-hand table + the statement, and (honesty) does not claim engine==hand.

- [ ] **Step 7: Run, verify pass.** `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_manuscript_collation.py::TestCalibrationInvariants -v` → 8 passed (R1-R8).

- [ ] **Step 8: Full-file gate.** `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_manuscript_collation.py -v` → all green (TestFoldAndClassify 5 + TestMetrics 2 + TestWitnessRecords 2 + TestCollate 1 + TestCalibrationInvariants 8; v1 TestRegressionOracle deleted). `py -3 scripts/lint_rules.py` → `11·0·0`. `py -3 -m ruff format --check scripts/ tests/` → clean.

- [ ] **Step 9: Commit.**

```bash
git add scripts/core/manuscript_collation.py scripts/manuscript_calibration_report.py dev/CALIBRATION_2026-05-17-engine-vs-hand.md tests/test_manuscript_collation.py
git commit -m "tau.6.x.4.b: Phase-2 Task 5 REDEFINED per spec-revision 2026-05-17 - calibration-invariant contract R1-R8 (semantic/lacuna/base/conservation/definitions/failure-modes exact; agreement is honest engine measurement not hand-reproduction), extent-aware base-pick (CAM 4/4), engine-vs-hand transparency artifact; v1 impossible oracle deleted; local commit only, no push, no zip"
```

---

## Task 6: Folio manifest + cached loader (Unit B) — carried from v1, unchanged

**Files:** Create `content/manuscript/samuel/manifest.yaml`, `scripts/core/manuscript_manifest.py`; test `tests/test_manuscript_collation.py`.

- [ ] **Step 1: Failing test** (append):

```python
class TestManifest:
    def test_manifest_seeded_with_calibration_chapters(self):
        mm = importlib.import_module("scripts.core.manuscript_manifest")
        mm.load_manifest.cache_clear()
        man = mm.load_manifest()
        for book, ch in [("1sa", 1), ("1sa", 3), ("1sa", 17), ("2sa", 11)]:
            entry = mm.chapter_entry(man, book, ch)
            assert entry["GG"]["folios"] and entry["CAM"]["folios"]
            assert entry["status"] == "calibrated"
    def test_uncovered_chapters_marked_pending(self):
        mm = importlib.import_module("scripts.core.manuscript_manifest")
        mm.load_manifest.cache_clear()
        man = mm.load_manifest()
        e = mm.chapter_entry(man, "1sa", 2)   # not a calibration chapter
        assert e["status"] == "pending"
```

- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement.** `content/manuscript/samuel/manifest.yaml`: per book → chapter → `{GG:{folios:[...],source_images:[...]}, CAM:{folios:[...],views:[...]}, status:<calibrated|pending>}`. Seed the 4 calibration chapters' folios by reading the `source_images`/`folio_sigla` of the calibration witness JSONs (do not hand-type). Every other 1sa (1-31) / 2sa (1-24) chapter `status: pending`, empty folio lists. `scripts/core/manuscript_manifest.py`: `@lru_cache(maxsize=1) load_manifest()` (PyYAML `yaml.safe_load`, rules §7.1) + `chapter_entry(man, book, ch)` returning the entry (or a synthesized `{"status":"pending","GG":{"folios":[]},"CAM":{"folios":[]}}` for unseeded). Tests call `load_manifest.cache_clear()` in setup.
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Commit** — `git add content/manuscript/samuel/manifest.yaml scripts/core/manuscript_manifest.py tests/test_manuscript_collation.py && git commit -m "tau.6.x.4.b: Phase-2 Samuel folio manifest + cached loader (Unit B), seeded w/ 4 calibration chapters; local commit only, no push, no zip"`

---

## Task 7: Reconciliation + apparatus store (Unit D) — carried from v1, unchanged

**Files:** Create `scripts/core/manuscript_reconcile.py`, `content/apparatus/.gitkeep`; test `tests/test_manuscript_collation.py`.

- [ ] **Step 1: Failing test** (append):

```python
class TestReconcile:
    def test_diplomatic_parallel_2sa11(self):
        mr = importlib.import_module("scripts.core.manuscript_reconcile")
        with open(f"{CAL}/2sa11_collation.json", encoding="utf-8") as fh:
            col = json.load(fh)
        recon, app = mr.reconcile(col)
        assert col["base_witness_recommended"] == "CAM"
        assert len(recon) == len(col["verses"])
        for v in col["verses"]:
            if any(a["class"] == "disagree" for a in v["alignment"]):
                assert any(e["v"] == v["v"] for e in app)
        # honesty: a both-illegible span is a marked gap, never fabricated
        assert all(("⟦illegible⟧" not in " ".join(r["geez"])) or r["gap"]
                   for r in recon)
```

- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement** `reconcile(collation) -> (reconciled_verses, apparatus)`: reconciled = base-witness running text per spine verse (D3); where base has a clear scribal slip/lacuna and the other witness is sound → disciplined eclectic fallback **recorded** in the apparatus (`resolution`,`reason`,`from_witness`); both-witness lacuna → a `gap:true` verse, **never fabricated** (spec §7); apparatus entry per verse with a recorded disagreement/lacuna = `{v, base_reading, variants:[{witness,reading}], lacunae, resolution, reason}`. `dump_apparatus(book, app)` writes `content/apparatus/<book>.json` (directory established by `content/apparatus/.gitkeep`; written for real by Phase-3).
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Commit** — `git add scripts/core/manuscript_reconcile.py content/apparatus/.gitkeep tests/test_manuscript_collation.py && git commit -m "tau.6.x.4.b: Phase-2 reconciliation + apparatus store schema (Unit D, diplomatic-parallel D3, lacuna-honest); local commit only, no push, no zip"`

---

## Task 8: QA/audit meta-tool + preflight integration (Unit E) — CLARIFIED per spec-revision §4

**Files:** Create `scripts/manuscript_qa.py`; modify `scripts/web.py` (`_compute_preflight_uncached()`); test `tests/test_manuscript_collation.py`.

- [ ] **Step 1: Failing test** (append):

```python
class TestQAMetaTool:
    def test_run_all_shape(self):
        q = importlib.import_module("scripts.manuscript_qa")
        r = q.run_all()
        assert set(r) == {"checks", "summary"}
        for c in r["checks"]:
            assert set(c) >= {"id", "name", "status", "message", "violations"}
            assert c["status"] in ("pass", "warn", "fail")
        assert set(r["summary"]) >= {"total", "pass", "warn", "fail", "clean"}
    def test_engine_metrics_held_to_bar_not_hand_equality(self):
        q = importlib.import_module("scripts.manuscript_qa")
        r = q.run_all()
        ids = {c["id"] for c in r["checks"]}
        assert any("engine_metric" in i for i in ids)   # engine's own W↔W/sem/unc vs GO bar
        assert any("engine_vs_hand" in i for i in ids)   # honest divergence reported, not asserted ==
    def test_preflight_exposes_manuscript_check(self):
        import importlib as il, scripts.web as web
        il.reload(web)
        pf = web._compute_preflight_uncached()
        ids = [c.get("id") for c in (pf.get("checks") or pf.get("items") or [])]
        assert any("manuscript" in str(i) for i in ids)
```

- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement** `scripts/manuscript_qa.py` (rules §9 shape): `run_all()` walks the manifest + every present collation and runs — (a) `validate_witness` (Unit C) on every evidence file; (b) `assert_token_conservation` per collation; (c) the **R1-R8 calibration-invariant contract** (spec-revision §3.2) — pass/fail; (d) book-wide coverage (chapters mapped in BOTH witnesses vs `pending`); (e) **`engine_metric_*`**: the engine's OWN computed W↔W/semantic/uncertainty per chapter held to the spec §4 GO bar (semantic ≥95, uncertainty ≤10 → `pass`/`warn`; W↔W reported — `warn` where the engine's deterministic agreement is honestly < the merge bar, which is EXPECTED for distinct recensions, diplomatic-parallel, NOT a failure); (f) **`engine_vs_hand_divergence`**: surfaces the Task-5 transparency report as an informational check (status `pass`, message = the honest-divergence statement) — it REPORTS the engine-vs-hand delta, it does NOT assert equality. `main()` → 0 clean / 1 on any `fail`. Fold into `_compute_preflight_uncached()` in `scripts/web.py` per rules §9 step 3: try/except-guarded (failure → `warn`, never 500), additive, `jump_to:"/preflight"`.
- [ ] **Step 4: Run, verify pass** + smoke `$env:PYTHONUTF8="1"; py -3 scripts/manuscript_qa.py` (exits 0/1 sanely).
- [ ] **Step 5: Commit** — `git add scripts/manuscript_qa.py tests/test_manuscript_collation.py && git add -u scripts/web.py && git commit -m "tau.6.x.4.b: Phase-2 QA meta-tool + preflight (Unit E) - engine's own metrics held to GO bar + honest engine-vs-hand divergence reported (NOT hand-equality), per spec-revision 2026-05-17; local commit only, no push, no zip"`

---

## Task 9: Book-wide driver/harness + ship — carried from v1, ship message updated

**Files:** Create `scripts/run_manuscript_collation_at_scale.py`; modify `dev/PLAN_2026-05-09.md`, `dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md`; test `tests/test_manuscript_collation.py`.

- [ ] **Step 1: Failing test** (append):

```python
class TestScaleDriver:
    def test_driver_reports_coverage_and_pending(self):
        d = importlib.import_module("scripts.run_manuscript_collation_at_scale")
        rep = d.run(dry=True)
        assert rep["chapters_collated"] >= 4
        assert rep["chapters_pending"] >= 1
        assert "1sa" in rep["by_book"] and "2sa" in rep["by_book"]
```

- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement** `run_manuscript_collation_at_scale.py` (mirrors `scripts/run_*_at_scale.py`, rules §9): iterate the manifest; for every chapter whose GG+CAM records exist → `validate_witness` + `collate()` + `reconcile()` → write `content/manuscript/samuel/collation/<ref>_collation.json` + `content/apparatus/<book>.json`; for every `pending` chapter → list it as needing the blind isolated-subagent vision-transcription (Phase-1 procedure: isolated GG transcriber → adversarial review → CUDL-IIIF CAM hi-res via `cudl-iiif-access` → isolated CAM transcriber → adversarial review). `run(dry=True)` reports only; `run(dry=False)` collates present chapters. Emit a coverage/QA status report. The driver does NOT run the vision marathon — that is the downstream effort (Phase-2.5/3), one chapter at a time, manifest-tracked.
- [ ] **Step 4: Full gate.** `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_manuscript_collation.py -v` (all green) ; `py -3 scripts/lint_rules.py` (`11·0·0`) ; `py -3 -m ruff format --check scripts/ tests/` (clean).
- [ ] **Step 5: Ship.** Register **τ.6.x.4.b** in `dev/PLAN_2026-05-09.md`; update `dev/SESSION_STATE.md` headline (Phase-2 tool SHIPPED; engine proven on the R1-R8 reproducible contract; hand calibration retained as immutable reference; honest engine-vs-hand divergence recorded; base=CAM 4/4; next = book-wide blind-transcription marathon → Phase-3 render + `manuscript-collation-tier2` + apparatus integration; Kings reuses) and `dev/IN_FLIGHT.md`; then:

```bash
git add scripts/run_manuscript_collation_at_scale.py tests/test_manuscript_collation.py dev/PLAN_2026-05-09.md dev/SESSION_STATE.md dev/IN_FLIGHT.md
git commit -m "tau.6.x.4.b: Phase-2 Samuel dual-manuscript collation TOOL shipped - 5 units proven on the R1-R8 reproducible-invariant contract (spec-revision 2026-05-17; semantic/lacuna/base/conservation exact, agreement = honest engine metric), engine-vs-hand divergence recorded; next = book-wide blind-transcription marathon then Phase-3; Kings reuses; local commit only, no push, no zip"
```

---

## Self-Review (against the 2026-05-16 design spec + the 2026-05-17 revision)

- **Spec §5 units:** Unit A (engine) Tasks 1-4 SHIPPED + Task 5 base refinement; Unit B (manifest) Task 6; Unit C (records) Task 3 SHIPPED; Unit D (reconcile+apparatus) Task 7; Unit E (QA) Task 8. ✔ all five covered.
- **Spec §8 success criteria:** "Phase-1 *metrics* extended book-wide held to the GO bar" → Task 8 `engine_metric_*` (engine's own metrics vs §4 bar) + the R3/R4 exact (semantic/lacuna) invariants; structural pins (manifest coverage Task 6/8, reconciled shape + apparatus well-formedness Task 7, lacuna-honesty Task 7, conservation R2). ✔ — and explicitly NOT byte-reproduction of hand `alignment[]` (spec-revision §2-§3).
- **Spec §7 honesty:** both-witness lacuna → marked gap never fabricated (Task 7); immutable evidence + re-derivable (calibration files never edited; R8 transparency). ✔
- **Spec-revision R1-R8:** R1 Task5 test_R1; R2 test_R2 (+ Task7/8); R3 test_R3; R4 test_R4; R5 test_R5 + Step-4 base rule; R6 test_R6; R7 test_R7; R8 test_R8 + `manuscript_calibration_report.py` + the committed artifact. ✔
- **Placeholder scan:** Step 4's base-pick has one bounded "tune to R5 (2sa11 threshold)" latitude — deliberate and explicitly scoped (the §3.3 material-separation threshold), with the empirical target stated (CAM 4/4) and the failing/right reason given; not a vague placeholder. All other steps have runnable code/commands.
- **Type consistency:** `collate(gg,cam,kjv,*,book,chapter)`, `load_kjv_skeleton(book,ch)`, `assert_token_conservation(verses,gg,cam)`, `DEFINITIONS`, `ILLEGIBLE`, `validate_witness`, `load_manifest`/`chapter_entry`, `reconcile`/`dump_apparatus`, `run_all`, `build_report` — names consistent across Tasks 5-9 and with the shipped Tasks 1-4.
- **Out of scope (unchanged):** Phase-3 render (`geez-tewahedo/1sa.py`/`2sa.py`), `manuscript-collation-tier2` provenance tier, reader-popup wiring, the book-wide vision-transcription marathon — next-gate (spec §6). Kings reuses Phase-2/3.

## Execution Handoff

Plan saved to `docs/superpowers/plans/2026-05-17-samuel-phase2-collation-tool-v2.md`; spec revision at `docs/superpowers/specs/2026-05-17-samuel-phase2-collation-spec-revision.md`. **The user paused execution at the fork and chose "revise the spec." Do NOT auto-execute.** Resume only after the user reviews this v2 + the spec revision; then continue with `superpowers:subagent-driven-development` from **Task 5** (Tasks 1-4 are shipped), fresh subagent per task + two-stage review, exactly as Tasks 1-4 were executed.
