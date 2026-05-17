# tests/test_manuscript_collation.py
import importlib
import json
import glob
import os

mc = importlib.import_module("scripts.core.manuscript_collation")


class TestFoldAndClassify:
    def test_strict_identity_is_agree(self):
        assert mc.classify_pair("ዳዊት", "ዳዊት") == "agree"

    def test_skeleton_fold_diacritic_order(self):
        # same consonantal skeleton, different vowel order → skeleton-equal → agree
        assert mc.fold_skeleton("ሳሙኤል") == mc.fold_skeleton("ሳመኤል")
        assert mc.classify_pair("ሳሙኤል", "ሳመኤል") == "agree"

    def test_clearly_different_is_disagree(self):
        assert mc.classify_pair("ደቂቅ", "ውሉድ") == "disagree"

    def test_one_sided_row_is_disagree(self):
        assert mc.classify_pair("ዳዊት", "") == "disagree"
        assert mc.classify_pair("", "ዳዊት") == "disagree"

    def test_is_strict_identity_helper(self):
        assert mc.is_strict("ዳዊት", "ዳዊት") is True
        assert mc.is_strict("ሳሙኤል", "ሳመኤል") is False
        assert mc.is_strict("ዳዊት", "") is False


class TestMetrics:
    def _toy(self):
        # 1 spine verse: 2 agree, 1 disagree, 1 one-sided disagree
        return [
            {
                "v": 1,
                "gg_tokens": ["ዳዊት", "ሳሙኤል", "ደቂቅ"],
                "cam_tokens": ["ዳዊት", "ሳመኤል", "ውሉድ", "እግዚእ"],
                "alignment": [
                    {"gg": "ዳዊት", "cam": "ዳዊት", "class": "agree"},
                    {"gg": "ሳሙኤል", "cam": "ሳመኤል", "class": "agree"},
                    {"gg": "ደቂቅ", "cam": "ውሉድ", "class": "disagree"},
                    {"gg": "", "cam": "እግዚእ", "class": "disagree"},
                ],
                "semantic_pass": True,
                "semantic_note": "toy",
            }
        ]

    def test_metrics_recompute(self):
        verses = self._toy()
        gg = {"verses": [{"tokens": ["ዳዊት", "ሳሙኤል", "ደቂቅ"], "uncertain": []}]}
        cam = {"verses": [{"tokens": ["ዳዊት", "ሳመኤል", "ውሉድ", "እግዚእ"], "uncertain": []}]}
        m = mc.compute_metrics(verses, gg, cam, base="CAM")
        assert m["ww_agreement_skeleton_basis"] == "2/4"
        assert m["ww_agreement_pct"] == 25.0  # strict: only ዳዊት==ዳዊት literal
        assert m["semantic_pass_basis"] == "1/1"
        assert m["lacuna_counts"] == {"gg": 0, "cam": 0, "both": 0}
        assert m["definitions"] == mc.DEFINITIONS

    def test_token_conservation_gate_raises_on_drift(self):
        verses = self._toy()
        gg = {
            "verses": [
                {
                    "tokens": ["ዳዊት", "ሳሙኤል", "ደቂቅ", "EXTRA"],
                    "uncertain": [],
                }
            ]
        }
        cam = {"verses": [{"tokens": ["ዳዊት", "ሳመኤል", "ውሉድ", "እግዚእ"], "uncertain": []}]}
        import pytest

        with pytest.raises(AssertionError, match="token-conservation"):
            mc.assert_token_conservation(verses, gg, cam)


CAL = "content/manuscript/samuel/calibration"


class TestWitnessRecords:
    def test_all_calibration_witnesses_valid(self):
        rec = importlib.import_module("scripts.core.manuscript_records")
        files = [f for f in glob.glob(os.path.join(CAL, "*_witness*.json"))]
        assert len(files) >= 9
        for f in files:
            with open(f, encoding="utf-8") as fh:
                d = json.load(fh)
            ok, errs = rec.validate_witness(d)
            assert ok, f"{os.path.basename(f)}: {errs}"

    def test_bijection_violation_detected(self):
        rec = importlib.import_module("scripts.core.manuscript_records")
        bad = {
            "witness": "GG",
            "book": "1sa",
            "chapter": 1,
            "source_images": ["x"],
            "folio_sigla": ["f"],
            "transcription_notes": "n",
            "verses": [
                {
                    "v": 1,
                    "column": 1,
                    "line_start": 1,
                    "geez": "⟦illegible⟧",
                    "tokens": ["⟦illegible⟧"],
                    "uncertain": [],
                }
            ],
        }  # token w/o marker
        ok, errs = rec.validate_witness(bad)
        assert not ok and any("bijection" in e for e in errs)


class TestCollate:
    def test_collate_shape_and_conservation(self):
        gg = json.load(open(f"{CAL}/2sa11_witnessGG.json", encoding="utf-8"))
        cam = json.load(open(f"{CAL}/2sa11_witnessCAM_hires.json", encoding="utf-8"))
        kjv = mc.load_kjv_skeleton("2sa", 11)  # (chapter,verse,text) rows for ch 11
        col = mc.collate(gg, cam, kjv, book="2sa", chapter=11)
        assert list(col) == [
            "book",
            "chapter",
            "base_witness_recommended",
            "base_rationale",
            "verses",
            "metrics",
        ]
        mc.assert_token_conservation(col["verses"], gg, cam)  # must not raise
        assert col["metrics"]["definitions"] == mc.DEFINITIONS
        assert any(a.get("gg_flag") in (True, False) for vv in col["verses"] for a in vv["alignment"])


class TestCalibrationInvariants:
    CASES = [
        ("1sa1", "_collation_hires", 1, "1sa"),
        ("1sa3", "_collation", 3, "1sa"),
        ("1sa17", "_collation", 17, "1sa"),
        ("2sa11", "_collation", 11, "2sa"),
    ]

    def _run(self, ref, suf, ch, book):
        with open(f"{CAL}/{ref}_witnessGG.json", encoding="utf-8") as fh:
            gg = json.load(fh)
        with open(f"{CAL}/{ref}_witnessCAM_hires.json", encoding="utf-8") as fh:
            cam = json.load(fh)
        with open(f"{CAL}/{ref}{suf}.json", encoding="utf-8") as fh:
            golden = json.load(fh)
        got = mc.collate(gg, cam, mc.load_kjv_skeleton(book, ch), book=book, chapter=ch)
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
            assert got["metrics"]["semantic_pass_basis"] == golden["metrics"]["semantic_pass_basis"], ref

    def test_R4_lacuna_counts_exact(self):
        for ref, suf, ch, book in self.CASES:
            _, _, golden, got = self._run(ref, suf, ch, book)
            assert got["metrics"]["lacuna_counts"] == golden["metrics"]["lacuna_counts"], ref

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
                        assert a["gg"] == mc.ILLEGIBLE or a["cam"] == mc.ILLEGIBLE, (
                            f"{ref} v{v['v']}: lacuna w/o illegible"
                        )
        # 1sa17 GG-short vs CAM-long: one-sided recensional minus must be
        # disagree+counted, never lacuna (no brittle magnitude floor — a
        # structural assertion that does not depend on stretch() binning).
        _, _, _, s17 = self._run("1sa17", "_collation", 17, "1sa")
        one_sided = [a for v in s17["verses"] for a in v["alignment"] if (a["gg"] == "") ^ (a["cam"] == "")]
        assert one_sided, "1sa17 must have one-sided recensional cells"
        assert all(a["class"] == "disagree" for a in one_sided), "1sa17 one-sided minus must be disagree, never lacuna"

    def test_R8_engine_vs_hand_helper_honest(self):
        # R8 mechanism = a PURE no-I/O helper (no script, no committed md).
        out = mc.engine_vs_hand_report()
        assert set(out["chapters"]) == {"1sa1", "1sa3", "1sa17", "2sa11"}
        for ref, row in out["chapters"].items():
            assert {"engine", "hand"} <= set(row)
            for side in ("engine", "hand"):
                for k in ("strict_basis", "skeleton_basis", "bothconfident_basis"):
                    assert k in row[side], f"{ref}.{side}.{k}"
        s = out["honest_divergence_statement"]
        assert "intentionally differs" in s and "GO" in s
        assert "not a claim of equality" in s.lower() or "never claimed equal" in s.lower()


class TestManifest:
    def test_manifest_seeded_with_calibration_chapters(self):
        mm = importlib.import_module("scripts.core.manuscript_manifest")
        mm.load_manifest.cache_clear()
        man = mm.load_manifest()
        for book, ch, gg_sig in [
            ("1sa", 1, "f003r"),
            ("1sa", 3, "f004r"),
            ("1sa", 17, "f010v"),
            ("2sa", 11, "f021v"),
        ]:
            e = mm.chapter_entry(man, book, ch)
            assert e["GG"]["folios"] and e["CAM"]["folios"]
            assert e["status"] == "calibrated"
            assert gg_sig in e["GG"]["folios"]

    def test_uncovered_chapters_marked_pending(self):
        mm = importlib.import_module("scripts.core.manuscript_manifest")
        mm.load_manifest.cache_clear()
        e = mm.chapter_entry(mm.load_manifest(), "1sa", 2)
        assert e["status"] == "pending"


def _base_tokens(col, verse):
    """The base witness's own token list for a collation verse."""
    return verse["cam_tokens"] if col["base_witness_recommended"] == "CAM" else verse["gg_tokens"]


class TestReconcile:
    def test_diplomatic_parallel_and_R9_honesty_2sa11(self):
        mr = importlib.import_module("scripts.core.manuscript_reconcile")
        with open(f"{CAL}/2sa11_collation.json", encoding="utf-8") as fh:
            col = json.load(fh)
        recon, app = mr.reconcile(col)
        assert col["base_witness_recommended"] == "CAM"
        assert len(recon) == len(col["verses"])
        for v in col["verses"]:
            if any(a["class"] != "agree" for a in v["alignment"]):
                e = [x for x in app if x["v"] == v["v"]]
                assert e and {"v", "base_reading", "variants"} <= set(e[0])
        # R9 lacuna-honesty (design-spec §7) — CORRECT predicate: forbid
        # FABRICATION + other-witness-merge into the running text; the
        # base's own in-place ⟦illegible⟧ is honest (gap=False), NOT a
        # violation. Every reconciled token is ⟦illegible⟧ or a base-own
        # token; a whole-verse base lacuna is marked gap=True.
        ILL = mc.ILLEGIBLE
        for r, v in zip(recon, col["verses"]):
            base_set = set(_base_tokens(col, v))
            assert set(r["geez"]) - {ILL} <= base_set, (v["v"], "fabricated/foreign token in running text")
            legible = [t for t in _base_tokens(col, v) if t not in ("", ILL)]
            if not legible:
                assert r["gap"] is True, (v["v"], "whole-verse lacuna not gap")


class TestReconcileLacunaHonesty:
    """Synthetic collations exercising the §7 honesty-critical paths the
    2sa11-only test cannot reach (2sa11 has 0 lacunae)."""

    def _col(self, base, verses):
        return {
            "book": "1sa",
            "chapter": 1,
            "base_witness_recommended": base,
            "base_rationale": "test",
            "verses": verses,
            "metrics": {},
        }

    def test_both_witness_lacuna_marked_gap_never_fabricated(self):
        mr = importlib.import_module("scripts.core.manuscript_reconcile")
        ILL = mc.ILLEGIBLE
        col = self._col(
            "CAM",
            [
                {
                    "v": 1,
                    "gg_tokens": [ILL],
                    "cam_tokens": [ILL],
                    "alignment": [{"gg": ILL, "cam": ILL, "class": "lacuna-both"}],
                    "semantic_pass": False,
                    "semantic_note": "both illegible",
                }
            ],
        )
        recon, app = mr.reconcile(col)
        assert recon[0]["gap"] is True
        assert all(t == ILL or t == "" for t in recon[0]["geez"])  # no invented word

    def test_base_side_lacuna_other_witness_not_merged_into_text(self):
        mr = importlib.import_module("scripts.core.manuscript_reconcile")
        ILL = mc.ILLEGIBLE
        # base=CAM is fully illegible; GG is sound — GG must NOT enter the
        # running text (D3); it is recorded in the apparatus only.
        col = self._col(
            "CAM",
            [
                {
                    "v": 1,
                    "gg_tokens": ["ንጉሥ", "ዳዊት"],
                    "cam_tokens": [ILL, ILL],
                    "alignment": [
                        {"gg": "ንጉሥ", "cam": ILL, "class": "lacuna-cam"},
                        {"gg": "ዳዊት", "cam": ILL, "class": "lacuna-cam"},
                    ],
                    "semantic_pass": False,
                    "semantic_note": "base illegible",
                }
            ],
        )
        recon, app = mr.reconcile(col)
        assert recon[0]["gap"] is True
        assert "ንጉሥ" not in recon[0]["geez"] and "ዳዊት" not in recon[0]["geez"]
        e = [x for x in app if x["v"] == 1]
        assert e, "base-side lacuna must be recorded in apparatus"

    def test_gg_base_uses_gg_text_cam_is_variant(self):
        mr = importlib.import_module("scripts.core.manuscript_reconcile")
        col = self._col(
            "GG",
            [
                {
                    "v": 1,
                    "gg_tokens": ["ቃለ", "እግዚአብሔር"],
                    "cam_tokens": ["ነገረ", "እግዚአብሔር"],
                    "alignment": [
                        {"gg": "ቃለ", "cam": "ነገረ", "class": "disagree"},
                        {"gg": "እግዚአብሔር", "cam": "እግዚአብሔር", "class": "agree"},
                    ],
                    "semantic_pass": True,
                    "semantic_note": "ok",
                }
            ],
        )
        recon, app = mr.reconcile(col)
        assert recon[0]["geez"] == ["ቃለ", "እግዚአብሔር"]  # GG base verbatim
        assert recon[0]["gap"] is False
        e = [x for x in app if x["v"] == 1][0]
        assert any(var["witness"] == "CAM" and "ነገረ" in var["reading"] for var in e["variants"])

    def test_disagree_base_stands_recorded_in_apparatus(self):
        mr = importlib.import_module("scripts.core.manuscript_reconcile")
        col = self._col(
            "CAM",
            [
                {
                    "v": 1,
                    "gg_tokens": ["ደቂቅ"],
                    "cam_tokens": ["ውሉድ"],
                    "alignment": [{"gg": "ደቂቅ", "cam": "ውሉድ", "class": "disagree"}],
                    "semantic_pass": True,
                    "semantic_note": "ok",
                }
            ],
        )
        recon, app = mr.reconcile(col)
        assert recon[0]["geez"] == ["ውሉድ"] and recon[0]["gap"] is False
        e = [x for x in app if x["v"] == 1][0]
        assert e["resolution"] == "base"
        assert any(var["witness"] == "GG" and "ደቂቅ" in var["reading"] for var in e["variants"])


class TestQAMetaTool:
    def test_run_all_shape(self):
        q = importlib.import_module("scripts.manuscript_qa")
        r = q.run_all()
        assert set(r) == {"checks", "summary"}
        for c in r["checks"]:
            assert set(c) >= {"id", "name", "status", "message", "violations"}
            assert c["status"] in ("pass", "warn", "fail")
        assert set(r["summary"]) >= {"total", "pass", "warn", "fail", "clean"}

    def test_engine_metrics_held_to_bar_and_divergence_reported(self):
        q = importlib.import_module("scripts.manuscript_qa")
        checks = {c["id"]: c for c in q.run_all()["checks"]}
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
