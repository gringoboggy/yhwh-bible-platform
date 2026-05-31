# Samuel Phase-2 — Dual-Manuscript Collation Tool — Implementation Plan **v2** (rev. 2)
**Status:** superseded — by the 2026-05-27 own-versification re-architecture

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans`, task-by-task. Steps use checkbox (`- [ ]`) syntax.

> **v2 SUPERSEDES** `docs/superpowers/plans/2026-05-17-samuel-phase2-collation-tool.md`. Reason: v1 Task 5 ("engine byte-reproduces the 4 hand calibration collations") was proven mathematically impossible (thrice-verified). Authoritative: `docs/superpowers/specs/2026-05-17-samuel-phase2-collation-spec-revision.md`. **rev. 2** applies two independent adversarial reviews: the base-pick rule is now an honest two-clause + decision-of-record rule (the rev. 1 fitted-threshold fudge is removed), design-spec §8 structural pins are explicitly retained (R9), and R8 is demoted to a pure no-I/O helper + a QA line (no committed artifact, no extra script). **Do NOT auto-execute: the user paused; resume only after they review this v2 + the spec revision.**

**Goal:** Ship the production Samuel dual-witness collation tool — a sound, token-conserving, narrative-anchored engine + manifest + reconciliation/apparatus + QA — proven on the four calibration chapters against the *reproducible* invariants (R1-R9), with honest engine-vs-hand divergence recorded (docstring + QA line, no ceremony).

**Architecture:** Five units (design-spec §5): (A) pure collation engine [SHIPPED], (B) folio manifest, (C) immutable witness-record validator [SHIPPED], (D) reconciliation + apparatus, (E) QA/audit meta-tool wired into preflight. The four immutable Phase-1 calibration JSONs are retained as **human reference** (they produced the GO); the engine is validated against the reproducible contract R1-R9, NOT by regenerating their hand `alignment[]`.

**Tech Stack:** Python 3 (`py -3` on Windows), pytest, PyYAML, the `scripts/core/*` conventions (rules §7), the meta-tool + preflight pattern (rules §9), `lint_rules.py`. No new third-party dependency. No new top-level script beyond the existing plan units.

---

## Orientation (the executing session has zero context)

1. **Bootstrap triad, in order:** `dev/CLAUDE_PROJECT_RULES.md`, `dev/SESSION_STATE.md` (top banner), `dev/PLAN_2026-05-09.md`. Then **this v2 plan** + **`docs/superpowers/specs/2026-05-17-samuel-phase2-collation-spec-revision.md` (authoritative — read fully, esp. §3.2 R1-R9 and §3.3 the base rule)** + the 2026-05-16 design spec §5/§6/§7/§8 + `dev/CALIBRATION_2026-05-16-samuel-widened.md` §2-§4 (the ratified GO + base=CAM decision of record).
2. **Windows realities:** `py -3` (never bare `python`); prefix every test run with `$env:PYTHONUTF8="1"` (PowerShell) / `PYTHONUTF8=1 py -3 …` (Bash) or ~72 cp1252 failures; `subprocess.run` in pytest needs `stdin=subprocess.DEVNULL`; JSON is CRLF — compare by `json.load`-equality never bytes; **local commit only, no push** (remote deleted), **no zip**. Pre-commit `ruff format --check` + `lint_rules.py` hook: if blocked, `py -3 -m ruff format <files>` → re-stage → NEW commit (never `--amend`).
3. **The four calibration files are IMMUTABLE human reference.** `content/manuscript/samuel/calibration/` — for `1sa1`/`1sa3`/`1sa17`/`2sa11`: `*_witnessGG.json`, `*_witnessCAM_hires.json`, `*_collation.json` (the oracle uses `1sa1_collation_hires.json` + `1sa1_witnessCAM_hires.json`). Never edit, never `git add` a change under `content/manuscript/`.

---

## Already SHIPPED — Tasks 1-4 (DONE; do NOT re-implement)

Context only — committed, two-stage-reviewed, green:

- **Task 1** (`2f8872f`) — `scripts/core/manuscript_collation.py`: `DEFINITIONS`, `ILLEGIBLE` (canonical in `manuscript_records`, imported here), `_fold_char`, `fold_skeleton` (diacritic/order + near-homograph `ሀሐጀ`/`ሰሸ`/`ዐአ`), `is_strict`, `classify_pair`. `TestFoldAndClassify` (5).
- **Task 2** (`4f30e33`,`c2e9615`) — `import collections`, `_flag_set`, `assert_token_conservation` (HARD gate), `_pct`, `compute_metrics`. `TestMetrics` (2). both-confident `conf` reads per-row `gg_flag`/`cam_flag` (wired by `collate()`); strong in-code seam comment forbids "fixing" it.
- **Task 3** (`9408ac5`,`15f0e33`) — `scripts/core/manuscript_records.py`: `validate_witness` (schema, geez↔tokens incl. real U+1362 + numeral-spacing regex, bijection, OOB, marker enum, contiguity); `ILLEGIBLE` canonical here, `manuscript_collation` imports it (collation→records, no cycle). `TestWitnessRecords` (2).
- **Task 4** (`97cc1e7`) — `manuscript_collation.py`: `load_kjv_skeleton` (`ast.literal_eval` of `content/translations/kjv/<book>.py` `VERSES`, `@lru_cache`), `align_verse` (global NW over `fold_skeleton` + substitution, never positional), `collate(gg,cam,kjv,*,book,chapter)` (validates both records; **base picked inline at the current `manuscript_collation.py` base-pick block — Task 5 Step 4 replaces exactly that block**; spine = canonical KJV enumeration narrative-sliced; per-cell `gg_flag`/`cam_flag` from `uncertain[]`; `semantic_pass`/`note`; `compute_metrics`; `assert_token_conservation` hard gate; exact top-key order). `TestCollate` (1, shape+conservation).
- **`983cf1c`** — added a "BLOCKED" docstring note; **v2 Task 5 Step 1 rewrites it**.

Current test file has 10 green + the impossible v1 `TestRegressionOracle` (at `tests/test_manuscript_collation.py`, the class named `TestRegressionOracle`) — **v2 Task 5 Step 2 DELETES that class** (verified to exist; removing it loses no other coverage). Engine already satisfies R2/R3/R4/R6 (4/4) and the R7 structural modes.

---

## File Structure

- **Modify** `scripts/core/manuscript_collation.py` — Task 5 (docstring rewrite; `_pick_base` per spec-revision §3.3; a pure no-I/O `engine_vs_hand_report()` helper for R8).
- **Create** `content/manuscript/samuel/manifest.yaml` + `scripts/core/manuscript_manifest.py` — Task 6 (Unit B).
- **Create** `scripts/core/manuscript_reconcile.py` + `content/apparatus/.gitkeep` — Task 7 (Unit D).
- **Create** `scripts/manuscript_qa.py` + **modify** `scripts/web.py` — Task 8 (Unit E + preflight; surfaces R8).
- **Create** `scripts/run_manuscript_collation_at_scale.py` — Task 9 (driver/handoff + R9 ship-gate pins).
- **Modify** `tests/test_manuscript_collation.py` — Tasks 5-9 test classes (delete v1 `TestRegressionOracle`).
- **Modify** `dev/PLAN_2026-05-09.md`, `dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md` — Task 9 ship.

*(No `manuscript_calibration_report.py` and no `dev/CALIBRATION_2026-05-17-engine-vs-hand.md` — R8 is a pure helper + a QA line, per spec-revision §3.2 R8.)*

---

## Task 5: Redefined calibration contract (R1-R9) + honest base-pick + no-ceremony divergence record

**Files:** Modify `scripts/core/manuscript_collation.py`; modify `tests/test_manuscript_collation.py`.

- [ ] **Step 1: Rewrite the module docstring (BLOCKED → factual).** In `scripts/core/manuscript_collation.py`, replace the v1-Task-5 "BLOCKED" diagnosis block in the module docstring with a factual architectural note: the engine is the deterministic forward collator; the four calibration `*_collation.json` are immutable *human philological reference* (their `alignment[]` is per-token human adjudication that produced the 2026-05-17 GO and is intentionally not machine-reproduced); the engine's strict/skeleton/both-confident are its own honest measurement, intentionally distinct from the hand counts, never claimed equal (spec-revision §3). No code/logic change in this step.

- [ ] **Step 2: Failing test — delete v1 oracle, add the invariant contract.** In `tests/test_manuscript_collation.py` DELETE `class TestRegressionOracle` and append:

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
            assert "GO" in got["base_rationale"], f"{ref} rationale must cite GO"

    def test_R6_definitions_byte_stable(self):
        # ENGINE-SIDE ONLY (spec-revision §3.2 R6 / R8): the engine emits
        # ONE byte-stable definitions set every chapter. The immutable hand
        # goldens MAY carry chapter-specific philological annotations the
        # generic engine constant does not (1sa3's golden skeleton does) —
        # that is the R8 "hand reference intentionally differs" thesis, so
        # the goldens are deliberately NOT asserted == DEFINITIONS here.
        for ref, suf, ch, book in self.CASES:
            _, _, _golden, got = self._run(ref, suf, ch, book)
            assert got["metrics"]["definitions"] == mc.DEFINITIONS, ref

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
        # 1sa17 GG-short vs CAM-long: one-sided recensional minus must be
        # disagree+counted, never lacuna (no brittle magnitude floor — a
        # structural assertion that does not depend on stretch() binning).
        _, _, _, s17 = self._run("1sa17", "_collation", 17, "1sa")
        one_sided = [a for v in s17["verses"] for a in v["alignment"]
                     if (a["gg"] == "") ^ (a["cam"] == "")]
        assert one_sided, "1sa17 must have one-sided recensional cells"
        assert all(a["class"] == "disagree" for a in one_sided), \
            "1sa17 one-sided minus must be disagree, never lacuna"

    def test_R8_engine_vs_hand_helper_honest(self):
        # R8 mechanism = a PURE no-I/O helper (no script, no committed md).
        out = mc.engine_vs_hand_report()
        assert set(out["chapters"]) == {"1sa1", "1sa3", "1sa17", "2sa11"}
        for ref, row in out["chapters"].items():
            assert {"engine", "hand"} <= set(row)
            for side in ("engine", "hand"):
                for k in ("strict_basis", "skeleton_basis",
                          "bothconfident_basis"):
                    assert k in row[side], f"{ref}.{side}.{k}"
        s = out["honest_divergence_statement"]
        assert "intentionally differs" in s and "GO" in s
        assert "not a claim of equality" in s.lower() or \
               "never claimed equal" in s.lower()
```

- [ ] **Step 3: Run, verify fail.** `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_manuscript_collation.py::TestCalibrationInvariants -v` → FAIL (R5: base rule yields GG for 2sa11 with the *current shipped* inline base-pick; R8: `engine_vs_hand_report` missing).

- [ ] **Step 4: Replace the inline base-pick with the honest rule** (spec-revision §3.3). In `scripts/core/manuscript_collation.py`, replace the current inline base-selection block in `collate()` with a call to this new helper (insert the helper above `collate()`; the helper is the LITERAL, COMPLETE implementation — there is no "tune to R5", no fitted constant):

```python
def _pick_base(gg_rec, cam_rec):
    """Honest base-pick (spec-revision 2026-05-17 §3.3). Two clauses + a
    decision of record; NO illegible/flagged-ratio derivation, NO fitted
    threshold. base=CAM is the user-ratified project decision
    (dev/CALIBRATION_2026-05-16-samuel-widened.md §4 'Decision (user)',
    2026-05-17 GO). Returns (base, rationale)."""
    gv = len(gg_rec["verses"])
    cv = len(cam_rec["verses"])
    bigger, smaller = max(gv, cv), min(gv, cv)
    # Clause 1: materially-different extent -> the more complete recension.
    if bigger and smaller < 0.70 * bigger:
        base = "GG" if gv > cv else "CAM"
        rationale = (
            f"{base} transmits the more complete recension "
            f"(GG {gv}v vs CAM {cv}v; shorter < 0.70x longer -> material "
            f"extent split, spec-revision 2026-05-17 §3.3 clause 1). "
            f"base=CAM remains the project decision of record "
            f"(2026-05-17 GO)."
        )
        # Clause 3 safeguard: a non-CAM clause-1 pick is surface-to-user.
        if base != "CAM":
            rationale += (
                " SURFACE-TO-USER: clause 1 selected a non-CAM base; flag "
                "for the user, never a silent flip (§3.3 clause 3)."
            )
        return base, rationale
    # Clause 2: otherwise base = CAM, asserted as the decision of record.
    return "CAM", (
        "CAM by the project decision of record "
        "(dev/CALIBRATION_2026-05-16-samuel-widened.md §4 'Decision "
        "(user)'; base=CAM ratified project-wide by the 2026-05-17 GO; "
        "spec-revision 2026-05-17 §3.3 clause 2) - extents not materially "
        f"different (GG {gv}v / CAM {cv}v)."
    )
```

Wire `collate()`: `base, rationale = _pick_base(gg, cam)`; set `base_witness_recommended=base`, `base_rationale=rationale`. **Keep everything else in `collate()` unchanged** (record validation before base-pick, spine, per-cell flags, `compute_metrics`, the `assert_token_conservation` hard gate, exact top-key order). *(Hand-traced against the real witness verse-counts — GG/CAM: 1sa1 28/28 → clause 2 CAM; 1sa3 21/21 → clause 2 CAM; 1sa17 20/58 → clause 1 CAM (more complete); 2sa11 27/26 → clause 2 CAM. **CAM 4/4 with the literal code, no tuning.**)*

- [ ] **Step 5: Implement the R8 pure helper.** Add to `scripts/core/manuscript_collation.py` a pure, no-I/O function `engine_vs_hand_report()` that, for each calibration ref, collates with the engine and reads the immutable hand `*_collation.json` `metrics`, returning:

```python
{"chapters": {ref: {
     "engine": {"strict_basis","skeleton_basis","bothconfident_basis",
                "semantic_pass_basis","lacuna_counts","base"},
     "hand":   {<same keys, read verbatim from the immutable golden>}}
   for ref in ("1sa1","1sa3","1sa17","2sa11")},
 "honest_divergence_statement":
   "The engine's strict/skeleton/both-confident are a reproducible "
   "deterministic measurement that INTENTIONALLY DIFFERS from the "
   "per-token human philological adjudication in the immutable "
   "calibration collations, which already produced the 2026-05-17 GO "
   "(diplomatic-parallel, base=CAM). The engine reproduces semantic-pass, "
   "lacuna-counts and base exactly; agreement % is the engine's own "
   "honest metric, surfaced by the QA tool and read against the design-"
   "spec §4 reference bar - it is NOT a claim of equality with the hand "
   "calibration and is never claimed equal."}
```

It reads the calibration JSONs (allowed: this is the reference-comparison helper, not the pure collation core — keep file reads confined to this one function via `json.load`; no writes anywhere). No script, no committed markdown — Task 8 surfaces this via the QA tool.

- [ ] **Step 6: Run, verify pass.** `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_manuscript_collation.py::TestCalibrationInvariants -v` → 8 passed (R1-R8).

- [ ] **Step 7: Full-file gate.** `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_manuscript_collation.py -v` → all green (TestFoldAndClassify 5 + TestMetrics 2 + TestWitnessRecords 2 + TestCollate 1 + TestCalibrationInvariants 8; v1 TestRegressionOracle deleted). `py -3 scripts/lint_rules.py` → `11·0·0`. `py -3 -m ruff format --check scripts/ tests/` → clean.

- [ ] **Step 8: Commit.**

```bash
git add scripts/core/manuscript_collation.py tests/test_manuscript_collation.py
git commit -m "tau.6.x.4.b: Phase-2 Task 5 REDEFINED per spec-revision 2026-05-17 rev.2 - calibration-invariant contract R1-R9 (semantic/lacuna/base/conservation/definitions/failure-modes exact; agreement is honest engine measurement not hand-reproduction), HONEST two-clause+decision-of-record base-pick (CAM 4/4, no fitted threshold), R8 pure no-I/O engine_vs_hand helper (no artifact ceremony); v1 impossible oracle deleted; local commit only, no push, no zip"
```

---

## Task 6: Folio manifest + cached loader (Unit B) — carried, unchanged

**Files:** Create `content/manuscript/samuel/manifest.yaml`, `scripts/core/manuscript_manifest.py`; test `tests/test_manuscript_collation.py`.

- [ ] **Step 1: Failing test** (append):

```python
class TestManifest:
    def test_manifest_seeded_with_calibration_chapters(self):
        mm = importlib.import_module("scripts.core.manuscript_manifest")
        mm.load_manifest.cache_clear()
        man = mm.load_manifest()
        for book, ch in [("1sa", 1), ("1sa", 3), ("1sa", 17), ("2sa", 11)]:
            e = mm.chapter_entry(man, book, ch)
            assert e["GG"]["folios"] and e["CAM"]["folios"]
            assert e["status"] == "calibrated"
    def test_uncovered_chapters_marked_pending(self):
        mm = importlib.import_module("scripts.core.manuscript_manifest")
        mm.load_manifest.cache_clear()
        e = mm.chapter_entry(mm.load_manifest(), "1sa", 2)
        assert e["status"] == "pending"
```

- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement.** `content/manuscript/samuel/manifest.yaml`: per book → chapter → `{GG:{folios:[...],source_images:[...]}, CAM:{folios:[...],views:[...]}, status:<calibrated|pending>}`. Seed the 4 calibration chapters' folios by reading the `source_images`/`folio_sigla` of the calibration witness JSONs (do not hand-type). Every other 1sa (1-31)/2sa (1-24) chapter `status: pending`, empty folio lists. `scripts/core/manuscript_manifest.py`: `@lru_cache(maxsize=1) load_manifest()` (PyYAML `yaml.safe_load`, rules §7.1) + `chapter_entry(man, book, ch)` returning the entry (or synthesized `{"status":"pending","GG":{"folios":[]},"CAM":{"folios":[]}}`). Tests call `load_manifest.cache_clear()`.
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Commit** — `git add content/manuscript/samuel/manifest.yaml scripts/core/manuscript_manifest.py tests/test_manuscript_collation.py && git commit -m "tau.6.x.4.b: Phase-2 Samuel folio manifest + cached loader (Unit B), seeded w/ 4 calibration chapters; local commit only, no push, no zip"`

---

## Task 7: Reconciliation + apparatus store (Unit D) — carried + R9 pins explicit

**Files:** Create `scripts/core/manuscript_reconcile.py`, `content/apparatus/.gitkeep`; test `tests/test_manuscript_collation.py`.

- [ ] **Step 1: Failing test** (append) — includes the R9 apparatus-well-formedness + lacuna-honesty pins (design-spec §7/§8, named in spec-revision R9):

```python
def _base_tokens(col, verse):
    """The base witness's own token list for a collation verse."""
    return (verse["cam_tokens"]
            if col["base_witness_recommended"] == "CAM"
            else verse["gg_tokens"])


class TestReconcile:
    def test_diplomatic_parallel_and_R9_honesty_2sa11(self):
        mr = importlib.import_module("scripts.core.manuscript_reconcile")
        with open(f"{CAL}/2sa11_collation.json", encoding="utf-8") as fh:
            col = json.load(fh)
        recon, app = mr.reconcile(col)
        assert col["base_witness_recommended"] == "CAM"
        assert len(recon) == len(col["verses"])
        # R9 apparatus well-formedness: every verse with a recorded
        # disagreement/lacuna has a structured apparatus entry.
        for v in col["verses"]:
            if any(a["class"] != "agree" for a in v["alignment"]):
                e = [x for x in app if x["v"] == v["v"]]
                assert e and {"v", "base_reading", "variants"} <= set(e[0])
        # R9 lacuna-honesty (design-spec §7) — CORRECT predicate. The pin
        # forbids FABRICATION and merging the other witness into the
        # running text; it does NOT forbid the base witness's own honest
        # in-place ⟦illegible⟧ marking of a physically-lost word in an
        # otherwise-legible verse (that is honest diplomatic
        # transcription, gap=False — the crude rev.3 predicate
        # false-failed on the real damaged base=GG 1sa1 vv.21-28). So:
        # every reconciled token is ⟦illegible⟧ OR a token the base
        # witness itself wrote for that verse (no invented word, no
        # foreign/other-witness word ever in the running text); AND a
        # whole-verse base lacuna is marked gap=True.
        ILL = mc.ILLEGIBLE
        for r, v in zip(recon, col["verses"]):
            base_set = set(_base_tokens(col, v))
            assert set(r["geez"]) - {ILL} <= base_set, (
                v["v"], "fabricated/foreign token in running text")
            legible = [t for t in _base_tokens(col, v) if t not in ("", ILL)]
            if not legible:
                assert r["gap"] is True, (v["v"], "whole-verse lacuna not gap")
```

- [ ] **Step 1b: Also append `TestReconcileLacunaHonesty`** — the honesty-critical lacuna/eclectic paths are NOT exercised by 2sa11 (0 lacunae); this committed synthetic-fixture regression class closes that gap BEFORE Task 8/9/Phase-3 feed `reconcile` a real damaged chapter:

```python
class TestReconcileLacunaHonesty:
    """Synthetic collations exercising the §7 honesty-critical paths the
    2sa11-only test cannot reach (2sa11 has 0 lacunae)."""

    def _col(self, base, verses):
        return {"book": "1sa", "chapter": 1,
                "base_witness_recommended": base, "base_rationale": "test",
                "verses": verses, "metrics": {}}

    def test_both_witness_lacuna_marked_gap_never_fabricated(self):
        mr = importlib.import_module("scripts.core.manuscript_reconcile")
        ILL = mc.ILLEGIBLE
        col = self._col("CAM", [{"v": 1,
            "gg_tokens": [ILL], "cam_tokens": [ILL],
            "alignment": [{"gg": ILL, "cam": ILL, "class": "lacuna-both"}],
            "semantic_pass": False, "semantic_note": "both illegible"}])
        recon, app = mr.reconcile(col)
        assert recon[0]["gap"] is True
        assert all(t == ILL or t == "" for t in recon[0]["geez"])  # no invented word

    def test_base_side_lacuna_other_witness_not_merged_into_text(self):
        mr = importlib.import_module("scripts.core.manuscript_reconcile")
        ILL = mc.ILLEGIBLE
        # base=CAM is fully illegible; GG is sound — GG must NOT enter the
        # running text (D3); it is recorded in the apparatus only.
        col = self._col("CAM", [{"v": 1,
            "gg_tokens": ["ንጉሥ", "ዳዊት"], "cam_tokens": [ILL, ILL],
            "alignment": [{"gg": "ንጉሥ", "cam": ILL, "class": "lacuna-cam"},
                          {"gg": "ዳዊት", "cam": ILL, "class": "lacuna-cam"}],
            "semantic_pass": False, "semantic_note": "base illegible"}])
        recon, app = mr.reconcile(col)
        assert recon[0]["gap"] is True
        assert "ንጉሥ" not in recon[0]["geez"] and "ዳዊት" not in recon[0]["geez"]
        e = [x for x in app if x["v"] == 1]
        assert e, "base-side lacuna must be recorded in apparatus"

    def test_gg_base_uses_gg_text_cam_is_variant(self):
        mr = importlib.import_module("scripts.core.manuscript_reconcile")
        col = self._col("GG", [{"v": 1,
            "gg_tokens": ["ቃለ", "እግዚአብሔር"], "cam_tokens": ["ነገረ", "እግዚአብሔር"],
            "alignment": [{"gg": "ቃለ", "cam": "ነገረ", "class": "disagree"},
                          {"gg": "እግዚአብሔር", "cam": "እግዚአብሔር", "class": "agree"}],
            "semantic_pass": True, "semantic_note": "ok"}])
        recon, app = mr.reconcile(col)
        assert recon[0]["geez"] == ["ቃለ", "እግዚአብሔር"]  # GG base verbatim
        assert recon[0]["gap"] is False
        e = [x for x in app if x["v"] == 1][0]
        assert any(var["witness"] == "CAM" and "ነገረ" in var["reading"]
                   for var in e["variants"])

    def test_disagree_base_stands_recorded_in_apparatus(self):
        mr = importlib.import_module("scripts.core.manuscript_reconcile")
        col = self._col("CAM", [{"v": 1,
            "gg_tokens": ["ደቂቅ"], "cam_tokens": ["ውሉድ"],
            "alignment": [{"gg": "ደቂቅ", "cam": "ውሉድ", "class": "disagree"}],
            "semantic_pass": True, "semantic_note": "ok"}])
        recon, app = mr.reconcile(col)
        assert recon[0]["geez"] == ["ውሉድ"] and recon[0]["gap"] is False
        e = [x for x in app if x["v"] == 1][0]
        assert e["resolution"] == "base"
        assert any(var["witness"] == "GG" and "ደቂቅ" in var["reading"]
                   for var in e["variants"])
```
(The implementer may adapt the synthetic `alignment`/token shapes minimally if `reconcile`'s real contract needs it — but the four honesty invariants asserted here are fixed: both-witness-lacuna→gap+no-fabrication; base-side-lacuna→other-witness-NOT-in-running-text+apparatus-recorded; GG-base→GG-verbatim+CAM-variant; disagree→base-stands+recorded. These must pass against the AS-SHIPPED `reconcile` with NO change to `manuscript_reconcile.py` — the implementation was already verified honest on these paths; this only adds the committed regression pin. If a fixture needs the engine changed to pass, that is a real bug → report it.)

- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement** `reconcile(collation) -> (reconciled_verses, apparatus)`: reconciled = base-witness running text per spine verse (D3); base scribal slip/lacuna + other witness sound → disciplined eclectic fallback **recorded** in the apparatus (`resolution`,`reason`,`from_witness`); both-witness lacuna → a `gap:true` verse, **never fabricated** (design-spec §7); apparatus entry per verse with a recorded disagreement/lacuna = `{v, base_reading, variants:[{witness,reading}], lacunae, resolution, reason}`. `dump_apparatus(book, app)` writes `content/apparatus/<book>.json` (directory established by `content/apparatus/.gitkeep`; written for real by Phase-3).
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Commit** — `git add scripts/core/manuscript_reconcile.py content/apparatus/.gitkeep tests/test_manuscript_collation.py && git commit -m "tau.6.x.4.b: Phase-2 reconciliation + apparatus store (Unit D, diplomatic-parallel D3) + R9 apparatus-well-formedness & lacuna-honesty pins; local commit only, no push, no zip"`

---

## Task 8: QA/audit meta-tool + preflight (Unit E) — surfaces R8; engine metrics vs §4 bar

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
        assert set(r["summary"]) >= {"total","pass","warn","fail","clean"}
    def test_engine_metrics_held_to_bar_and_divergence_reported(self):
        q = importlib.import_module("scripts.manuscript_qa")
        checks = {c["id"]: c for c in q.run_all()["checks"]}
        # explicit check ids (no invented contract):
        for ref in ("1sa1", "1sa3", "1sa17", "2sa11"):
            assert f"engine_metric_{ref}" in checks
        d = checks.get("engine_vs_hand_divergence")
        assert d is not None and d["status"] == "pass"
        assert "intentionally differs" in d["message"]
    def test_preflight_exposes_manuscript_check(self):
        import importlib as il, scripts.web as web
        il.reload(web)
        pf = web._compute_preflight_uncached()
        ids = [c.get("id") for c in (pf.get("checks") or pf.get("items") or [])]
        assert any("manuscript" in str(i) for i in ids)
```

- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement** `scripts/manuscript_qa.py` (rules §9 `run_all()` shape: `{"checks":[{id,name,status,message,violations}],"summary":{total,pass,warn,fail,clean}}`; `main()` → 0 clean / 1 on any `fail`). Concrete check ids:
  - `witness_valid` — `validate_witness` over every evidence file (fail on invalid).
  - `token_conservation` — `assert_token_conservation` per present collation (fail on raise).
  - `calibration_contract` — R1-R7 over the 4 calibration chapters (fail if any R1-R7 breaks).
  - `coverage` — chapters mapped in BOTH witnesses vs `pending` (informational `pass`/`warn`).
  - `engine_metric_<ref>` for each of `1sa1`/`1sa3`/`1sa17`/`2sa11` — the engine's OWN computed metrics vs the design-spec §4 reference bar. **rev.5 correction (per memory `no-reassert-ratified-bar` — the 4th controller over-assertion caught by review):** design-spec §4's `uncertainty ≤ 10%` and `W↔W ≥ 90%` are components of the **one-time calibration GO bar that already fired GO on 2026-05-17**, NOT per-build production invariants — and the engine's `uncertainty_pct` is **byte-identical to the immutable, GO'd hand goldens** (16.34/10.09/9.62/10.38; 3 of 4 exceed 10%), so a `>10 → fail` would permanently red-flag ratified reference data. Therefore: **`fail` ONLY if `semantic_pass_pct < 95`** (the genuine floor — incoherent/missing narrative; the calibration has 100% semantic on all 4, so a sub-95 here means a real engine regression). **`warn` if `ww_agreement_bothconfident_pct < 90` OR `uncertainty_pct > 10`** — BOTH are expected, GO-ratified, distinct-recension/MS-damage signals (parallel treatment; honesty is enforced by the `⟦illegible⟧↔marker` bijection in `witness_valid`/`calibration_contract`, not a token-ratio ceiling), the message naming each as expected-not-a-failure and citing the 2026-05-17 GO + calibration-finding §4 failure-mode-4. Else `pass`. Message always states semantic / W↔W / uncertainty numbers.
  - `engine_vs_hand_divergence` — status **`pass`**, informational; `message` = `manuscript_collation.engine_vs_hand_report()["honest_divergence_statement"]`; `violations=[]`; the per-chapter engine-vs-hand table goes in the check's `message`/details. It REPORTS the delta; it does NOT assert equality.
  Fold into `_compute_preflight_uncached()` per rules §9 step 3: try/except-guarded (failure → `warn`, never 500), additive, `jump_to:"/preflight"`, id contains `"manuscript"`. (Implementation note: `_compute_preflight_uncached` was extracted to `scripts/api/preflight.py` at ω.35-B.7 and re-exported via `scripts/web.py` — editing `scripts/api/preflight.py` IS the correct way to modify what `scripts.web._compute_preflight_uncached` does; the Task-8 test resolves to the same function object.)
- [ ] **Step 4: Run, verify pass** + smoke `$env:PYTHONUTF8="1"; py -3 scripts/manuscript_qa.py` (exits 0/1 sanely).
- [ ] **Step 5: Commit** — `git add scripts/manuscript_qa.py tests/test_manuscript_collation.py && git add -u scripts/web.py && git commit -m "tau.6.x.4.b: Phase-2 QA meta-tool + preflight (Unit E) - engine's own metrics vs §4 bar (W↔W sub-bar = expected warn, not fail) + engine_vs_hand_divergence informational (R8, NOT hand-equality), per spec-revision 2026-05-17 rev.2; local commit only, no push, no zip"`

---

## Task 9: Book-wide driver/harness + ship — carried; R9 ship-gate pins explicit

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
- [ ] **Step 3: Implement** `run_manuscript_collation_at_scale.py` (mirrors `scripts/run_*_at_scale.py`, rules §9): iterate the manifest; chapters with GG+CAM records → `validate_witness` + `collate()` + `reconcile()` → write `content/manuscript/samuel/collation/<ref>_collation.json` + `content/apparatus/<book>.json`; `pending` chapters → list as needing the blind isolated-subagent vision-transcription (Phase-1 procedure: isolated GG transcriber → adversarial review → CUDL-IIIF CAM hi-res via `cudl-iiif-access` → isolated CAM transcriber → adversarial review). `run(dry=True)` reports only; `run(dry=False)` collates present chapters. The driver does NOT run the vision marathon (downstream effort, manifest-tracked).
- [ ] **Step 4: Full gate + R9 ship pins.** `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_manuscript_collation.py -v` (all green) ; `py -3 scripts/lint_rules.py` (**R9: `11·0·0`**) ; `py -3 -m ruff format --check scripts/ tests/` (clean). **R9 retained design-spec §8 pins to verify here:** the `SAMUEL_VERSE_COUNTS` floor + reconciled-module renumber shape are a Phase-3 deliverable (out of Phase-2 scope, spec §6) — record in the ship note that they are explicitly deferred to Phase-3, NOT silently dropped; the `_meta`/`_source` ingest-record + back-link pins apply when Phase-3 writes the modules. Within Phase-2, R9's enforceable pins are: apparatus well-formedness + lacuna-honesty (Task 7) and lint/format/regression (this step).
- [ ] **Step 5: Ship.** Register **τ.6.x.4.b** in `dev/PLAN_2026-05-09.md`; update `dev/SESSION_STATE.md` headline (Phase-2 tool SHIPPED; engine proven on the R1-R9 reproducible contract; hand calibration retained as immutable reference; honest engine-vs-hand divergence recorded via docstring + QA line; base=CAM 4/4 by decision of record + the one principled extent clause; §8 floor/reconciled-shape explicitly deferred to Phase-3; next = book-wide blind-transcription marathon → Phase-3 render + `manuscript-collation-tier2` + apparatus integration; Kings reuses) and `dev/IN_FLIGHT.md`; then:

```bash
git add scripts/run_manuscript_collation_at_scale.py tests/test_manuscript_collation.py dev/PLAN_2026-05-09.md dev/SESSION_STATE.md dev/IN_FLIGHT.md
git commit -m "tau.6.x.4.b: Phase-2 Samuel dual-manuscript collation TOOL shipped - 5 units proven on the R1-R9 reproducible-invariant contract (spec-revision 2026-05-17 rev.2; semantic/lacuna/base/conservation exact, honest base-pick CAM 4/4, agreement = honest engine metric, §8 pins retained/deferred-not-dropped); next = book-wide blind-transcription marathon then Phase-3; Kings reuses; local commit only, no push, no zip"
```

---

## Self-Review (against the 2026-05-16 design spec + the 2026-05-17 rev.2 revision)

- **Design-spec §5 units:** A (engine) Tasks 1-4 SHIPPED + Task 5 base/helper; B Task 6; C Task 3 SHIPPED; D Task 7; E Task 8. ✔ all five.
- **Design-spec §8:** "Phase-1 *metrics* extended book-wide held to the GO bar" → Task 8 `engine_metric_<ref>` (engine's own metrics vs §4 bar; W↔W sub-bar = expected `warn`, honestly not `fail`) + R3/R4 exact. Structural pins **retained as R9**: apparatus well-formedness + lacuna-honesty (Task 7, tested), lint/format/regression (Task 9 Step 4), and the `SAMUEL_VERSE_COUNTS` floor + reconciled-module shape + `_meta`/`_source` explicitly **deferred to Phase-3 in writing (not dropped)** — design-spec §6 puts module render in Phase-3. ✔ not byte-reproduction of hand `alignment[]` (spec-revision §2-§3).
- **Design-spec §7 honesty:** both-witness lacuna → marked gap never fabricated (Task 7 `test_..._R9_honesty`); immutable evidence + re-derivable (calibration files never edited; R8 helper read-only). ✔
- **Spec-revision R1-R9:** R1 test_R1; R2 test_R2 (+ Task7/8); R3 test_R3; R4 test_R4; R5 test_R5 + Step-4 honest `_pick_base` (hand-traced CAM 4/4, no fitted constant); R6 test_R6; R7 test_R7 (structural, brittle magnitude floor removed); R8 test_R8 + pure `engine_vs_hand_report()` + Task-8 `engine_vs_hand_divergence` (no script/artifact); R9 Task 7 + Task 9 Step 4 pins + explicit Phase-3 deferral. ✔
- **Placeholder scan:** `_pick_base` is the COMPLETE literal implementation — no "tune to R5", no fitted threshold, no "verify empirically" hedge (the rev.1 fudge is removed). Task 8 Step 3 enumerates concrete check ids + the explicit fail/warn boundary. No "TBD/similar to/handle appropriately". The only data-derived value (the `0.70` extent ratio) is the design-finding's own short-vs-long criterion, fixed and justified (1sa17 GG 20 vs CAM 58), not fitted to a target. ✔
- **Type consistency:** `collate(gg,cam,kjv,*,book,chapter)`, `load_kjv_skeleton(book,ch)`, `assert_token_conservation(verses,gg,cam)`, `DEFINITIONS`, `ILLEGIBLE`, `validate_witness`, `_pick_base`, `engine_vs_hand_report`, `load_manifest`/`chapter_entry`, `reconcile`/`dump_apparatus`, `run_all`/`main` — consistent across Tasks 5-9 and with shipped Tasks 1-4. ✔
- **Safe re: shipped Tasks 1-4:** Step 1 (docstring) is comment-only; Step 4 replaces ONLY the inline base-pick block with `_pick_base` (record-validation-before-base, spine, flags, `compute_metrics`, conservation gate, key order untouched); Step 5 adds a new pure function. No silent reopening of Tasks 1-4. ✔
- **Out of scope (unchanged):** Phase-3 render (`geez-tewahedo/1sa.py`/`2sa.py`), `manuscript-collation-tier2`, reader-popup wiring, the book-wide vision marathon, the `SAMUEL_VERSE_COUNTS` floor + reconciled-module shape — all next-gate (design-spec §6). Kings reuses Phase-2/3.

## Execution Handoff

Plan saved to `docs/superpowers/plans/2026-05-17-samuel-phase2-collation-tool-v2.md`; spec revision (rev. 2, post-adversarial-review) at `docs/superpowers/specs/2026-05-17-samuel-phase2-collation-spec-revision.md`. **The user paused execution and chose "revise the spec." Do NOT auto-execute.** Resume only after the user reviews this v2 + the spec revision; then continue with `superpowers:subagent-driven-development` from **Task 5** (Tasks 1-4 shipped), fresh subagent per task + two-stage review, exactly as Tasks 1-4 were executed.
