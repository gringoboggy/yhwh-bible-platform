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
            d = json.load(open(f, encoding="utf-8"))
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
