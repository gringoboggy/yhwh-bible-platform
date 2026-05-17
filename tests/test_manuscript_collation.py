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


class TestRegressionOracle:
    CASES = [
        ("1sa1", "_collation_hires", 1),
        ("1sa3", "_collation", 3),
        ("1sa17", "_collation", 17),
        ("2sa11", "_collation", 11),
    ]

    def test_engine_reproduces_calibration(self):
        for ref, suf, ch in self.CASES:
            book = "1sa" if ref.startswith("1sa") else "2sa"
            gg = json.load(open(f"{CAL}/{ref}_witnessGG.json", encoding="utf-8"))
            camf = f"{CAL}/{ref}_witnessCAM_hires.json"
            cam = json.load(open(camf, encoding="utf-8"))
            kjv = mc.load_kjv_skeleton(book, ch)
            golden = json.load(open(f"{CAL}/{ref}{suf}.json", encoding="utf-8"))
            got = mc.collate(gg, cam, kjv, book=book, chapter=ch)
            assert got["metrics"]["ww_agreement_skeleton_basis"] == golden["metrics"]["ww_agreement_skeleton_basis"], (
                ref
            )
            assert got["metrics"]["ww_agreement_pct"] == golden["metrics"]["ww_agreement_pct"], ref
            assert (
                got["metrics"]["ww_agreement_bothconfident_basis"]
                == golden["metrics"]["ww_agreement_bothconfident_basis"]
            ), ref
            assert got["metrics"]["semantic_pass_basis"] == golden["metrics"]["semantic_pass_basis"], ref
            assert got["base_witness_recommended"] == golden["base_witness_recommended"], ref
            assert got["metrics"]["lacuna_counts"] == golden["metrics"]["lacuna_counts"], ref
