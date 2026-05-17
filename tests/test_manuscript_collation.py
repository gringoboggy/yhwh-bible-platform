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
        for book, ch in [("1sa", 1), ("1sa", 3), ("1sa", 17), ("2sa", 11)]:
            e = mm.chapter_entry(man, book, ch)
            assert e["GG"]["folios"] and e["CAM"]["folios"]
            assert e["status"] == "calibrated"

    def test_uncovered_chapters_marked_pending(self):
        mm = importlib.import_module("scripts.core.manuscript_manifest")
        mm.load_manifest.cache_clear()
        e = mm.chapter_entry(mm.load_manifest(), "1sa", 2)
        assert e["status"] == "pending"
