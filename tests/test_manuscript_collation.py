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


class TestValidatorNonEthiopicScreen:
    """The corrected non-Ethiopic contamination screen
    is folded into validate_witness so every chapter's adversarial review is
    enforced, not run inline by hand. A literal Latin ``f`` (U+0066) once
    slipped into a transcription; ALLOWED = Ethiopic block U+1200–U+137F ∪
    ASCII space ∪ rubric-cross ✣ U+2723, with the whole ⟦illegible⟧ sentinel
    whitelisted. CRITICAL: ✣ is a SANCTIONED divider _geez_to_tokens already
    legitimizes and appears 94× in the immutable Samuel goldens' geez — it
    MUST NOT be flagged."""

    REC = importlib.import_module("scripts.core.manuscript_records")

    def _verse(self, geez, *, v=1):
        # tokens computed via the REAL _geez_to_tokens so the existing
        # geez<->tokens invariant is satisfied — the point is the new
        # screen, not the pre-existing invariant.
        return {
            "v": v,
            "column": 1,
            "line_start": 1,
            "geez": geez,
            "tokens": self.REC._geez_to_tokens(geez),
            "uncertain": [],
        }

    def _wit(self, verses):
        return {
            "witness": "GG",
            "book": "1sa",
            "chapter": 1,
            "source_images": ["x"],
            "folio_sigla": ["f003r"],
            "transcription_notes": "n",
            "verses": verses,
        }

    def test_latin_f_in_geez_is_flagged(self):
        # Latin 'f' U+0066 injected; tokens recomputed so geez<->tokens holds.
        w = self._wit([self._verse("ወሀሎ ብእሲf ዘእምነ")])
        ok, errs = self.REC.validate_witness(w)
        assert not ok
        assert any("non-Ethiopic" in e and ("0x66" in e or "0X66" in e) for e in errs), errs

    def test_mojibake_char_in_geez_is_flagged(self):
        # A classic UTF-8/cp1252 mojibake byte (Â U+00C2) must be caught.
        w = self._wit([self._verse("ወሀሎ Â ብእሲ")])
        ok, errs = self.REC.validate_witness(w)
        assert not ok
        assert any("non-Ethiopic" in e and hex(0xC2) in e for e in errs), errs

    def test_replacement_char_in_geez_is_flagged(self):
        w = self._wit([self._verse("ወሀሎ � ብእሲ")])
        ok, errs = self.REC.validate_witness(w)
        assert not ok
        assert any("non-Ethiopic" in e and hex(0xFFFD) in e for e in errs), errs

    def test_latin_letter_inside_token_is_flagged(self):
        # Latin 's' U+0073 fused into a word (no separator) so _geez_to_tokens
        # carries it INTO a token verbatim — geez<->tokens invariant stays
        # satisfied and the per-token screen must independently flag it.
        w = self._wit([self._verse("ወሀሎ ብእsሲ ዘእምነ")])
        # fixture guard: the contaminated token really did survive tokenising
        assert "ብእsሲ" in w["verses"][0]["tokens"]
        ok, errs = self.REC.validate_witness(w)
        assert not ok
        assert any("non-Ethiopic token" in e and "ብእsሲ" in e for e in errs), errs

    def test_clean_ethiopic_witness_passes(self):
        w = self._wit([self._verse("ወሀሎ ብእሲ ዘእምነ አርማቴም")])
        ok, errs = self.REC.validate_witness(w)
        assert ok, errs

    def test_rubric_cross_U2723_not_flagged(self):
        # ✣ U+2723 is a SANCTIONED inline section divider — _geez_to_tokens
        # strips it (so it is NOT a token) but it stays in geez and MUST be
        # in ALLOWED. This pins the whole correctness point of the task.
        w = self._wit([self._verse("ወሀሎ ብእሲ ዘእምነ ✣")])
        ok, errs = self.REC.validate_witness(w)
        assert ok, errs
        # And the divider is genuinely present in geez (guard the fixture).
        assert "✣" in w["verses"][0]["geez"]
        assert "✣" not in w["verses"][0]["tokens"]

    def test_illegible_sentinel_whitelisted_geez_and_token(self):
        # A legit ⟦illegible⟧ token+geez with the matching uncertain
        # marker:"illegible" → still ok (sentinel whitelisted in BOTH the
        # geez screen and the token screen; bijection satisfied).
        ILL = self.REC.ILLEGIBLE
        w = self._wit(
            [
                {
                    "v": 1,
                    "column": 1,
                    "line_start": 1,
                    "geez": f"ወሀሎ {ILL} ብእሲ",
                    "tokens": ["ወሀሎ", ILL, "ብእሲ"],
                    "uncertain": [{"token_index": 1, "marker": "illegible"}],
                }
            ]
        )
        ok, errs = self.REC.validate_witness(w)
        assert ok, errs

    # ── immutable-golden regression pins ──────────────────────────────────
    SAMUEL_GOLDENS = [
        "1sa1_witnessGG",
        "1sa1_witnessCAM",
        "1sa1_witnessCAM_hires",
        "1sa3_witnessGG",
        "1sa3_witnessCAM_hires",
        "1sa17_witnessGG",
        "1sa17_witnessCAM_hires",
        "2sa11_witnessGG",
        "2sa11_witnessCAM_hires",
    ]
    KINGS_GOLDENS = ["1ki1_witnessGG", "1ki1_witnessCAM_hires"]

    def test_nine_immutable_samuel_goldens_still_valid(self):
        for name in self.SAMUEL_GOLDENS:
            with open(f"{CAL}/{name}.json", encoding="utf-8") as fh:
                d = json.load(fh)
            ok, errs = self.REC.validate_witness(d)
            assert ok, f"{name}: {errs}"

    def test_kings_1ki1_goldens_still_valid(self):
        kcal = "content/manuscript/kings/calibration"
        for name in self.KINGS_GOLDENS:
            with open(f"{kcal}/{name}.json", encoding="utf-8") as fh:
                d = json.load(fh)
            ok, errs = self.REC.validate_witness(d)
            assert ok, f"{name}: {errs}"

    def test_samuel_goldens_actually_exercise_the_cross_allowance(self):
        # Defends the correctness constraint itself: if some refactor ever
        # dropped ✣ from ALLOWED, the goldens would (correctly) fail — so
        # confirm the goldens really do carry ✣ in geez (94 occurrences).
        total = 0
        for name in self.SAMUEL_GOLDENS:
            with open(f"{CAL}/{name}.json", encoding="utf-8") as fh:
                d = json.load(fh)
            total += sum(vv["geez"].count("✣") for vv in d["verses"])
        assert total == 94, total


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
        for r, v in zip(recon, col["verses"], strict=False):
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
        import importlib as il
        import scripts.web as web

        il.reload(web)
        pf = web._compute_preflight_uncached()
        ids = [c.get("id") for c in (pf.get("checks") or pf.get("items") or [])]
        assert any("manuscript" in str(i) for i in ids)


class TestScaleDriver:
    def test_driver_reports_coverage_and_pending(self):
        d = importlib.import_module("scripts.run_manuscript_collation_at_scale")
        rep = d.run(dry=True)
        assert rep["chapters_collated"] >= 4
        assert rep["chapters_pending"] >= 1
        assert "1sa" in rep["by_book"] and "2sa" in rep["by_book"]

    def test_dry_run_always_has_empty_failed_list(self):
        # `failed` is ALWAYS in the report; empty on a dry run (nothing
        # is collated, so nothing can fail).
        d = importlib.import_module("scripts.run_manuscript_collation_at_scale")
        rep = d.run(dry=True)
        assert rep["failed"] == []

    def test_one_bad_chapter_is_isolated_and_batch_continues(self, monkeypatch):
        """Fix-1 fail-soft regression (rules §9 unattended-marathon).

        One calibrated chapter's collate raises; the driver must NOT
        propagate, must record it in ``report["failed"]`` with
        ``book/chapter/ref/error``, must still process the other (good)
        calibrated chapters, and must write NOTHING real — neither the
        immutable ``content/manuscript/samuel/calibration/`` dir nor any
        actual ``content/`` artifact (``_collate_chapter`` /
        ``_write_collation`` / ``dump_apparatus`` are monkeypatched to
        in-memory stand-ins; no filesystem touch, nothing left behind).
        """
        import pathlib

        d = importlib.import_module("scripts.run_manuscript_collation_at_scale")

        BAD = ("1sa", 17)  # one of the four real calibration chapters
        calls = {"collate": [], "write": [], "apparatus": []}

        def fake_collate_chapter(book, ch, ref):
            calls["collate"].append((book, ch, ref))
            if (book, ch) == BAD:
                raise ValueError(f"synthetic corrupt witness for {ref}")
            # Trivial in-memory stand-ins (no real engine / no real
            # data) — the apparatus is a tiny marker list per ref.
            return ({"book": book, "chapter": ch, "ref": ref}, [{"ref": ref}])

        def fake_write_collation(ref, collation):
            calls["write"].append(ref)
            return f"<memory>/{ref}_collation.json"  # never hits disk

        def fake_dump_apparatus(book, app):
            calls["apparatus"].append((book, len(app)))
            return f"<memory>/{book}.json"  # never hits disk

        monkeypatch.setattr(d, "_collate_chapter", fake_collate_chapter)
        monkeypatch.setattr(d, "_write_collation", fake_write_collation)
        monkeypatch.setattr(d.mr, "dump_apparatus", fake_dump_apparatus)

        # Guard: the immutable calibration dir must be untouched. Snapshot
        # its file list before and after; assert byte-for-byte identical.
        cal_dir = pathlib.Path(CAL)
        before = sorted(p.name for p in cal_dir.iterdir())

        rep = d.run(dry=False)  # must NOT raise

        # The bad chapter is isolated into report["failed"] with the
        # required keys; the exception did not propagate.
        assert len(rep["failed"]) == 1
        bad = rep["failed"][0]
        assert (bad["book"], bad["chapter"], bad["ref"]) == ("1sa", 17, "1sa17")
        assert set(bad) == {"book", "chapter", "ref", "error"}
        assert "synthetic corrupt witness" in bad["error"]

        # The other three good calibration chapters were still
        # collated + written (the batch continued past the failure).
        good_refs = {"1sa1", "1sa3", "2sa11"}
        assert set(calls["write"]) == good_refs
        assert "1sa17" not in calls["write"]  # never written (it failed)
        # Per-book apparatus flush still happened for the chapters that
        # DID succeed (succeeded apparatus is preserved, not lost).
        flushed_books = {b for b, _ in calls["apparatus"]}
        assert flushed_books == {"1sa", "2sa"}
        assert rep["apparatus_written"]  # non-empty: flush ran

        # Nothing real was written; the immutable calibration dir is
        # byte-identical (nothing created, nothing left behind).
        after = sorted(p.name for p in cal_dir.iterdir())
        assert after == before


class TestWriteWitness:
    """The canonical witness writer derives tokens from geez via
    _geez_to_tokens, normalizes uncertain[] markers, validates the result
    BEFORE writing, and never leaves a partial file on disk if the record
    fails validation. Direct response to the 1ki4 schema-drift incident:
    transcribers using this writer cannot produce a non-canonical record.
    """

    def test_round_trip_validates_and_derives_tokens(self, tmp_path):
        from scripts.core.manuscript_records import (
            ILLEGIBLE,
            validate_witness,
            write_witness,
        )

        out = tmp_path / "1ki99_witnessGG.json"
        written = write_witness(
            witness="GG",
            book="1ki",
            chapter=99,
            source_images=["test.jpg"],
            folio_sigla=["f999r"],
            verses=[
                {
                    "v": 1,
                    "column": "L",
                    "line_start": 1,
                    "geez": "ወሰሎምን፡ንጉሥ✣",
                    "uncertain": [],
                },
                {
                    "v": 2,
                    "column": "L",
                    "line_start": 3,
                    "geez": f"{ILLEGIBLE}፡ብእሲ",
                    "uncertain": [{"marker": "illegible", "note": "ink damage"}],
                },
            ],
            transcription_notes="test fixture",
            output_path=str(out),
        )

        # tokens auto-derived (✣ stripped; ⟦illegible⟧ preserved as token)
        assert written["verses"][0]["tokens"] == ["ወሰሎምን", "ንጉሥ"]
        assert written["verses"][1]["tokens"] == [ILLEGIBLE, "ብእሲ"]
        # illegible token_index auto-assigned to the ⟦illegible⟧ position
        u = written["verses"][1]["uncertain"][0]
        assert u["marker"] == "illegible"
        assert u["token_index"] == 0
        # disk write validates round-trip
        data = json.loads(out.read_text(encoding="utf-8"))
        ok, errs = validate_witness(data)
        assert ok, errs

    def test_top_level_keys_are_canonical_only(self, tmp_path):
        from scripts.core.manuscript_records import write_witness

        out = tmp_path / "ok.json"
        written = write_witness(
            witness="GG",
            book="1ki",
            chapter=99,
            source_images=["t.jpg"],
            folio_sigla=["f0"],
            verses=[
                {
                    "v": 1,
                    "column": "L",
                    "line_start": 1,
                    "geez": "ወ",
                    "uncertain": [],
                }
            ],
            transcription_notes="",
            output_path=str(out),
        )
        assert set(written) == {
            "witness",
            "book",
            "chapter",
            "source_images",
            "folio_sigla",
            "verses",
            "transcription_notes",
        }

    def test_rejects_invalid_uncertain_marker(self, tmp_path):
        import pytest

        from scripts.core.manuscript_records import write_witness

        out = tmp_path / "bad.json"
        with pytest.raises(ValueError, match="bad marker"):
            write_witness(
                witness="GG",
                book="1ki",
                chapter=99,
                source_images=["t.jpg"],
                folio_sigla=["f0"],
                verses=[
                    {
                        "v": 1,
                        "column": "L",
                        "line_start": 1,
                        "geez": "ወ",
                        "uncertain": [{"marker": "name_form", "note": "x"}],
                    }
                ],
                transcription_notes="",
                output_path=str(out),
            )
        assert not out.exists()

    def test_no_file_on_validation_failure(self, tmp_path):
        """Transactional: bad geez (Latin contamination) raises and writes nothing."""
        import pytest

        from scripts.core.manuscript_records import write_witness

        out = tmp_path / "bad.json"
        with pytest.raises(ValueError):
            write_witness(
                witness="GG",
                book="1ki",
                chapter=99,
                source_images=["t.jpg"],
                folio_sigla=["f0"],
                verses=[
                    {
                        "v": 1,
                        "column": "L",
                        "line_start": 1,
                        "geez": "f",  # Latin f -> non-Ethiopic screen rejects
                        "uncertain": [],
                    }
                ],
                transcription_notes="",
                output_path=str(out),
            )
        assert not out.exists()
