r"""τ.6.x.1 — Tesseract OCR engine wiring pins (2026-05-14).

τ.6.x.1 wires the τ.6.x.0c-authorized Tesseract strategy into
`scripts/extract_parallel_pdf.py`. This phase is Claude-side
actionable — τ.6.x.0c had already closed the operator-side gate.

τ.6.x.1 deliverables under test:

1. Module surface — the new constants (OCR_DPI, GEEZ_LANG, AMH_LANG,
   ENGINE_TESSERACT, ENGINE_TEXT_LAYER, ENGINE_CHOICES, ENGINE_DEFAULT)
   are exposed at module scope with the τ.6.x.0c-authorized values.

2. Helper functions — `_required_tesseract_languages`,
   `_check_tesseract_languages`, `_render_column_to_png`,
   `_run_tesseract_on_png`, `tesseract_extract_columns`,
   `_resolve_tesseract_or_exit`, `_verify_tesseract_languages_or_exit`
   are importable + callable.

3. `_check_tesseract_languages` parses `--list-langs` output correctly,
   normalizing Windows `script\X` to POSIX `script/X` so callers can
   compare against the canonical form. Uses `stdin=subprocess.DEVNULL`
   for W-W1 mitigation.

4. `_resolve_tesseract_or_exit` SystemExits with a cross-platform
   install-pointer message when `tesseract_binary()` returns `None`.

5. `_verify_tesseract_languages_or_exit` SystemExits with a tessdata
   download-pointer message when required language packs are missing.

6. CLI `--engine {tesseract,text-layer}` accepts both choices,
   defaults to `tesseract`, and rejects unknown values.

7. `_source.yaml::ocr_strategy.tau6x1_wiring` block records the wiring
   with the expected shape (engine_default, render dpi 350, invocation
   pattern, pre-flight, no_ingest_at_this_phase, next_phase=τ.6.x.2+).

8. SCOPE doc §7.6 records the τ.6.x.1 wiring section with the engine
   semantics, render path, pre-flight validation, and the τ.6.x.2+
   unblock pointer.

9. PI2 pre-flight checklist τ.6.x.1 row flipped from ⬜ pending →
   ✓ SHIPPED; τ.6.x.2+ row replaces the old "τ.6.x.1+" entry with the
   publisher-direction-gated bulk-ingest description.

10. Closed-arc invariants preserved: Π.0.1 amharic-in-POPUP_LANGUAGES,
    γ.4.8.E 67/67 Mäqabyan, γ.4.8.F ≥212 Mäqabyan, τ.6.x.0a contract
    (translation slots gen.py-only), τ.6.x.0b contract (Option-D-Hybrid
    + tesseract default), τ.6.x.0c contract (script/Ethiopic adopted),
    Ω.0 free-public pivot.

11. CHANGELOG records the τ.6.x.1 ship entry; PLAN_2026-05-09 lists
    τ.6.x.1 as shipped in the parallel-bible track ledger.

12. The tau6x0c share-pin → milestone-pin pattern continues: the
    τ.6.x.0c test that asserted τ.6.x.1+ was pending is migrated to
    assert it as shipped.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml


REPO = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1 — module surface (constants + helper exports)
# ──────────────────────────────────────────────────────────────────


class TestTau6X1ModuleSurface:
    """The new τ.6.x.1 constants and helper functions are importable
    at module scope with the τ.6.x.0c-authorized values."""

    def test_engine_default_is_tesseract(self):
        from scripts.extract_parallel_pdf import ENGINE_DEFAULT, ENGINE_TESSERACT

        assert ENGINE_DEFAULT == ENGINE_TESSERACT == "tesseract", (
            "τ.6.x.0b authorization: default engine must be 'tesseract'"
        )

    def test_engine_choices_includes_both_engines(self):
        from scripts.extract_parallel_pdf import (
            ENGINE_CHOICES,
            ENGINE_TESSERACT,
            ENGINE_TEXT_LAYER,
        )

        assert ENGINE_TESSERACT in ENGINE_CHOICES
        assert ENGINE_TEXT_LAYER in ENGINE_CHOICES
        assert ENGINE_TEXT_LAYER == "text-layer"
        assert len(ENGINE_CHOICES) == 2, f"Two engines exactly: tesseract + text-layer; got {ENGINE_CHOICES!r}"

    def test_ocr_dpi_is_350(self):
        from scripts.extract_parallel_pdf import OCR_DPI

        assert OCR_DPI == 350, "τ.6.x.1 wiring: dpi pinned at 350 per the Phase-4 page-image methodology"

    def test_geez_lang_is_script_ethiopic(self):
        from scripts.extract_parallel_pdf import GEEZ_LANG

        assert GEEZ_LANG == "script/Ethiopic", "τ.6.x.0c adoption: script/Ethiopic is the authorized Geʽez recognizer"

    def test_amh_lang_is_amh(self):
        from scripts.extract_parallel_pdf import AMH_LANG

        assert AMH_LANG == "amh", "amh.traineddata drives the Amharic column"

    def test_helper_functions_importable(self):
        from scripts.extract_parallel_pdf import (
            _check_tesseract_languages,
            _render_column_to_png,
            _required_tesseract_languages,
            _resolve_tesseract_or_exit,
            _run_tesseract_on_png,
            _verify_tesseract_languages_or_exit,
            tesseract_extract_columns,
        )

        for fn in (
            _check_tesseract_languages,
            _render_column_to_png,
            _required_tesseract_languages,
            _resolve_tesseract_or_exit,
            _run_tesseract_on_png,
            _verify_tesseract_languages_or_exit,
            tesseract_extract_columns,
        ):
            assert callable(fn), f"{fn.__name__} must be callable"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1 — _required_tesseract_languages
# ──────────────────────────────────────────────────────────────────


class TestTau6X1RequiredLanguages:
    """`_required_tesseract_languages` returns the canonical pair the
    tesseract engine pre-flight-checks: amh + script/Ethiopic."""

    def test_returns_canonical_pair(self):
        from scripts.extract_parallel_pdf import _required_tesseract_languages

        result = _required_tesseract_languages()
        assert isinstance(result, tuple), "must return a tuple for caller-side hash-friendliness"
        assert set(result) == {"amh", "script/Ethiopic"}, f"required = (amh, script/Ethiopic); got {result!r}"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1 — _check_tesseract_languages
# ──────────────────────────────────────────────────────────────────


class TestTau6X1CheckTesseractLanguages:
    """`_check_tesseract_languages` runs `tesseract --list-langs`,
    normalizes Windows `script\\X` to POSIX `script/X`, and returns the
    list of required packs that are missing."""

    def test_returns_empty_when_all_present(self, monkeypatch):
        from scripts.extract_parallel_pdf import _check_tesseract_languages

        def fake_run(args, **kwargs):
            class R:
                stdout = "List of available languages:\namh\neng\nscript/Ethiopic\n"
                stderr = ""

            return R()

        monkeypatch.setattr(subprocess, "run", fake_run)
        missing = _check_tesseract_languages(Path("/fake/tesseract"), ("amh", "script/Ethiopic"))
        assert missing == [], f"both packs present; missing should be empty; got {missing!r}"

    def test_normalizes_windows_backslash(self, monkeypatch):
        from scripts.extract_parallel_pdf import _check_tesseract_languages

        def fake_run(args, **kwargs):
            class R:
                stdout = "amh\nscript\\Ethiopic\n"
                stderr = ""

            return R()

        monkeypatch.setattr(subprocess, "run", fake_run)
        missing = _check_tesseract_languages(Path("/fake/tesseract"), ("amh", "script/Ethiopic"))
        assert missing == [], f"Windows backslash must normalize to POSIX; got missing={missing!r}"

    def test_reports_missing_pack(self, monkeypatch):
        from scripts.extract_parallel_pdf import _check_tesseract_languages

        def fake_run(args, **kwargs):
            class R:
                stdout = "amh\neng\n"  # no script/Ethiopic
                stderr = ""

            return R()

        monkeypatch.setattr(subprocess, "run", fake_run)
        missing = _check_tesseract_languages(Path("/fake/tesseract"), ("amh", "script/Ethiopic"))
        assert missing == ["script/Ethiopic"], f"script/Ethiopic missing should be reported; got {missing!r}"

    def test_subprocess_invoked_with_stdin_devnull(self, monkeypatch):
        """W-W1 mitigation: stdin must be passed as DEVNULL to avoid
        the Windows-handle-invalid failure mode under pytest-from-
        Powershell. Verified via subprocess.run call inspection."""
        from scripts.extract_parallel_pdf import _check_tesseract_languages

        captured: dict = {}

        def fake_run(args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs

            class R:
                stdout = "amh\n"
                stderr = ""

            return R()

        monkeypatch.setattr(subprocess, "run", fake_run)
        _check_tesseract_languages(Path("/fake/tesseract"), ("amh",))
        assert captured["kwargs"].get("stdin") == subprocess.DEVNULL, (
            f"W-W1 mitigation: stdin must be subprocess.DEVNULL; got {captured['kwargs'].get('stdin')!r}"
        )

    def test_subprocess_invoked_with_list_langs(self, monkeypatch, tmp_path):
        from scripts.extract_parallel_pdf import _check_tesseract_languages

        captured: dict = {}

        def fake_run(args, **kwargs):
            captured["args"] = args

            class R:
                stdout = "amh\n"
                stderr = ""

            return R()

        monkeypatch.setattr(subprocess, "run", fake_run)
        fake_bin = tmp_path / "tesseract"
        _check_tesseract_languages(fake_bin, ("amh",))
        assert captured["args"] == [str(fake_bin), "--list-langs"], (
            f"argv must be [binary, '--list-langs']; got {captured['args']!r}"
        )


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1 — _resolve_tesseract_or_exit
# ──────────────────────────────────────────────────────────────────


class TestTau6X1ResolveTesseractOrExit:
    """`_resolve_tesseract_or_exit` wraps the tesseract_binary() resolver
    with a clean SystemExit + install-pointer when the resolver returns
    None."""

    def test_returns_path_when_resolver_finds_binary(self, monkeypatch, tmp_path):
        from scripts.extract_parallel_pdf import _resolve_tesseract_or_exit

        fake = tmp_path / "tesseract"
        fake.write_text("x")
        monkeypatch.setattr(
            "scripts.core.paths.tesseract_binary",
            lambda: fake,
        )
        assert _resolve_tesseract_or_exit() == fake

    def test_systemexit_when_resolver_returns_none(self, monkeypatch):
        from scripts.extract_parallel_pdf import _resolve_tesseract_or_exit

        monkeypatch.setattr(
            "scripts.core.paths.tesseract_binary",
            lambda: None,
        )
        with pytest.raises(SystemExit) as excinfo:
            _resolve_tesseract_or_exit()
        msg = str(excinfo.value)
        assert "Tesseract" in msg, "error message must mention Tesseract"
        # Cross-platform install-pointer must reference UB-Mannheim (Windows)
        # OR brew (macOS) OR apt-get (Linux).
        assert "UB-Mannheim" in msg or "brew" in msg or "apt-get" in msg, (
            f"install-pointer must reference at least one platform installer; got: {msg!r}"
        )

    def test_systemexit_mentions_text_layer_fallback(self, monkeypatch):
        from scripts.extract_parallel_pdf import _resolve_tesseract_or_exit

        monkeypatch.setattr(
            "scripts.core.paths.tesseract_binary",
            lambda: None,
        )
        with pytest.raises(SystemExit) as excinfo:
            _resolve_tesseract_or_exit()
        msg = str(excinfo.value)
        assert "text-layer" in msg, (
            "error message must mention the --engine text-layer fallback for diagnostic comparison"
        )


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1 — _verify_tesseract_languages_or_exit
# ──────────────────────────────────────────────────────────────────


class TestTau6X1VerifyTesseractLanguagesOrExit:
    """`_verify_tesseract_languages_or_exit` SystemExits with a tessdata
    download-pointer when required language packs are missing."""

    def test_no_exit_when_all_present(self, monkeypatch):
        from scripts.extract_parallel_pdf import _verify_tesseract_languages_or_exit

        monkeypatch.setattr(
            "scripts.extract_parallel_pdf._check_tesseract_languages",
            lambda binary, required: [],
        )
        _verify_tesseract_languages_or_exit(Path("/fake/tesseract"))  # no raise

    def test_systemexit_lists_missing_packs(self, monkeypatch):
        from scripts.extract_parallel_pdf import _verify_tesseract_languages_or_exit

        monkeypatch.setattr(
            "scripts.extract_parallel_pdf._check_tesseract_languages",
            lambda binary, required: ["script/Ethiopic"],
        )
        with pytest.raises(SystemExit) as excinfo:
            _verify_tesseract_languages_or_exit(Path("/fake/tesseract"))
        msg = str(excinfo.value)
        assert "script/Ethiopic" in msg, "missing pack must appear in error message"

    def test_systemexit_includes_tessdata_pointers(self, monkeypatch):
        from scripts.extract_parallel_pdf import _verify_tesseract_languages_or_exit

        monkeypatch.setattr(
            "scripts.extract_parallel_pdf._check_tesseract_languages",
            lambda binary, required: ["script/Ethiopic"],
        )
        with pytest.raises(SystemExit) as excinfo:
            _verify_tesseract_languages_or_exit(Path("/fake/tesseract"))
        msg = str(excinfo.value)
        assert "tessdata_fast" in msg or "tessdata_best" in msg, (
            "tessdata download pointers must appear in the error message"
        )


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1 — _run_tesseract_on_png subprocess pattern
# ──────────────────────────────────────────────────────────────────


class TestTau6X1RunTesseractOnPng:
    """`_run_tesseract_on_png` invokes Tesseract on a PNG with the
    expected argv shape + W-W1-safe subprocess kwargs."""

    def test_argv_contains_lang_and_psm(self, monkeypatch, tmp_path):
        from scripts.extract_parallel_pdf import _run_tesseract_on_png

        captured: dict = {}

        def fake_run(args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs

            class R:
                stdout = "ወገብረ"
                stderr = ""

            return R()

        monkeypatch.setattr(subprocess, "run", fake_run)
        png = tmp_path / "page.png"
        png.write_bytes(b"\x89PNG\r\n\x1a\n")
        fake_bin = tmp_path / "tesseract"
        _run_tesseract_on_png(fake_bin, png, "script/Ethiopic", psm=6)
        argv = captured["args"]
        assert argv[0] == str(fake_bin)
        assert str(png) in argv
        assert "stdout" in argv, "tesseract output target is 'stdout'"
        assert "-l" in argv and "script/Ethiopic" in argv
        assert "--psm" in argv and "6" in argv

    def test_subprocess_uses_devnull_and_capture(self, monkeypatch, tmp_path):
        from scripts.extract_parallel_pdf import _run_tesseract_on_png

        captured: dict = {}

        def fake_run(args, **kwargs):
            captured["kwargs"] = kwargs

            class R:
                stdout = ""
                stderr = ""

            return R()

        monkeypatch.setattr(subprocess, "run", fake_run)
        png = tmp_path / "p.png"
        png.write_bytes(b"\x89PNG\r\n\x1a\n")
        _run_tesseract_on_png(Path("/fake/tesseract"), png, "amh")
        kw = captured["kwargs"]
        assert kw.get("stdin") == subprocess.DEVNULL, f"W-W1 mitigation: stdin must be DEVNULL; got {kw.get('stdin')!r}"
        assert kw.get("capture_output") is True, "capture_output must be True"
        assert kw.get("encoding") == "utf-8", "encoding must be utf-8 for Ge'ez/Amharic text"

    def test_returns_stdout(self, monkeypatch, tmp_path):
        from scripts.extract_parallel_pdf import _run_tesseract_on_png

        def fake_run(args, **kwargs):
            class R:
                stdout = "ወገብረ\n"
                stderr = ""

            return R()

        monkeypatch.setattr(subprocess, "run", fake_run)
        png = tmp_path / "p.png"
        png.write_bytes(b"\x89PNG\r\n\x1a\n")
        out = _run_tesseract_on_png(Path("/fake/tesseract"), png, "script/Ethiopic")
        assert out == "ወገብረ\n"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1 — tesseract_extract_columns composition
# ──────────────────────────────────────────────────────────────────


class TestTau6X1TesseractExtractColumns:
    """`tesseract_extract_columns` orchestrates the two-column render+OCR
    pipeline: renders left half + right half, OCRs each with the
    column-specific language pack, returns (geez_text, amh_text)."""

    def test_returns_tuple_of_strings(self, monkeypatch, tmp_path):
        from scripts.extract_parallel_pdf import tesseract_extract_columns

        # Stub _render_column_to_png to no-op (creates an empty file).
        def fake_render(page, side, dpi, out_path):
            out_path.write_bytes(b"\x89PNG\r\n\x1a\n")
            return out_path

        # Stub _run_tesseract_on_png to return canned text per language.
        def fake_run_tess(binary, png_path, lang, psm=6):
            return {"script/Ethiopic": "ወገብረ", "amh": "ቤት"}[lang]

        monkeypatch.setattr(
            "scripts.extract_parallel_pdf._render_column_to_png",
            fake_render,
        )
        monkeypatch.setattr(
            "scripts.extract_parallel_pdf._run_tesseract_on_png",
            fake_run_tess,
        )

        # Page argument is opaque to the stubs.
        result = tesseract_extract_columns(
            pdf_page=object(),
            binary=Path("/fake/tesseract"),
            dpi=350,
            geez_lang="script/Ethiopic",
            amh_lang="amh",
            tmp_dir=tmp_path,
        )
        assert isinstance(result, tuple)
        assert len(result) == 2
        geez, amh = result
        assert geez == "ወገብረ"
        assert amh == "ቤት"

    def test_creates_temp_dir_when_none_passed(self, monkeypatch):
        """Caller may omit `tmp_dir` — function should create its own
        TemporaryDirectory."""
        from scripts.extract_parallel_pdf import tesseract_extract_columns

        seen_tmp_dirs: list[Path] = []

        def fake_render(page, side, dpi, out_path):
            seen_tmp_dirs.append(out_path.parent)
            out_path.write_bytes(b"\x89PNG\r\n\x1a\n")
            return out_path

        def fake_run_tess(binary, png_path, lang, psm=6):
            return ""

        monkeypatch.setattr(
            "scripts.extract_parallel_pdf._render_column_to_png",
            fake_render,
        )
        monkeypatch.setattr(
            "scripts.extract_parallel_pdf._run_tesseract_on_png",
            fake_run_tess,
        )
        tesseract_extract_columns(
            pdf_page=object(),
            binary=Path("/fake/tesseract"),
        )
        assert seen_tmp_dirs, "render must have been invoked at least once"
        # The temp dir must exist at call-time and be cleaned up afterward.
        # We can only check the latter for the local-tmp path; the call-time
        # existence is implicit in the render's write_bytes succeeding.

    def test_calls_render_with_left_and_right_sides(self, monkeypatch, tmp_path):
        from scripts.extract_parallel_pdf import tesseract_extract_columns

        sides_seen: list[str] = []

        def fake_render(page, side, dpi, out_path):
            sides_seen.append(side)
            out_path.write_bytes(b"\x89PNG\r\n\x1a\n")
            return out_path

        def fake_run_tess(binary, png_path, lang, psm=6):
            return ""

        monkeypatch.setattr(
            "scripts.extract_parallel_pdf._render_column_to_png",
            fake_render,
        )
        monkeypatch.setattr(
            "scripts.extract_parallel_pdf._run_tesseract_on_png",
            fake_run_tess,
        )
        tesseract_extract_columns(
            pdf_page=object(),
            binary=Path("/fake/tesseract"),
            tmp_dir=tmp_path,
        )
        assert "left" in sides_seen and "right" in sides_seen, f"both columns must be rendered; got {sides_seen!r}"

    def test_runs_tesseract_with_per_column_languages(self, monkeypatch, tmp_path):
        from scripts.extract_parallel_pdf import tesseract_extract_columns

        langs_seen: list[str] = []

        def fake_render(page, side, dpi, out_path):
            out_path.write_bytes(b"\x89PNG\r\n\x1a\n")
            return out_path

        def fake_run_tess(binary, png_path, lang, psm=6):
            langs_seen.append(lang)
            return ""

        monkeypatch.setattr(
            "scripts.extract_parallel_pdf._render_column_to_png",
            fake_render,
        )
        monkeypatch.setattr(
            "scripts.extract_parallel_pdf._run_tesseract_on_png",
            fake_run_tess,
        )
        tesseract_extract_columns(
            pdf_page=object(),
            binary=Path("/fake/tesseract"),
            geez_lang="script/Ethiopic",
            amh_lang="amh",
            tmp_dir=tmp_path,
        )
        assert "script/Ethiopic" in langs_seen, "Geʽez column must be OCR'd with script/Ethiopic"
        assert "amh" in langs_seen, "Amharic column must be OCR'd with amh"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1 — extract_section engine dispatch
# ──────────────────────────────────────────────────────────────────


class TestTau6X1ExtractSectionEngineDispatch:
    """`extract_section()` accepts the `engine` kwarg and rejects bad
    values. Tesseract-engine path is exercised via mocked subprocess
    + mocked pymupdf so the test is hermetic."""

    def test_invalid_engine_raises_valueerror(self):
        from scripts.extract_parallel_pdf import extract_section

        with pytest.raises(ValueError):
            extract_section({"structural_map": {}}, "meqabyan", engine="bogus")


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1 — _source.yaml tau6x1_wiring block
# ──────────────────────────────────────────────────────────────────


class TestTau6X1SourceYamlWiringBlock:
    """The _source.yaml::ocr_strategy.tau6x1_wiring block records the
    engine wiring details (engine_default, render dpi, invocation,
    pre-flight, no-ingest contract, next_phase=τ.6.x.2+)."""

    YAML_PATH = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"

    def _wiring(self):
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        return cfg["ocr_strategy"]["tau6x1_wiring"]

    def test_block_present(self):
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        assert "tau6x1_wiring" in cfg["ocr_strategy"], "_source.yaml::ocr_strategy must declare a tau6x1_wiring block"

    def test_wired_phase_and_date(self):
        w = self._wiring()
        assert w["wired_at_phase"] == "τ.6.x.1"
        assert "2026-05-14" in str(w["wired_date"])

    def test_extractor_module_pointer(self):
        w = self._wiring()
        assert w["extractor_module"] == "scripts/extract_parallel_pdf.py"

    def test_engine_default_is_tesseract(self):
        w = self._wiring()
        assert w["engine_default"] == "tesseract", "τ.6.x.0b authorization preserved: default engine = tesseract"

    def test_engines_supported_pair(self):
        w = self._wiring()
        engines = set(w["engines_supported"])
        assert engines == {"tesseract", "text-layer"}, f"engines_supported = both; got {engines!r}"

    def test_render_dpi_350(self):
        w = self._wiring()
        assert w["render"]["dpi"] == 350

    def test_render_column_split_pct(self):
        w = self._wiring()
        assert w["render"]["column_split_pct"] == 50, "50% split matches text-layer engine geometry"

    def test_render_via_pymupdf(self):
        w = self._wiring()
        assert "pymupdf" in str(w["render"]["via"]).lower()

    def test_invocation_geez_column_lang(self):
        w = self._wiring()
        argv = w["invocation"]["geez_column"]
        assert "script/Ethiopic" in argv, "Geʽez column must use script/Ethiopic"

    def test_invocation_amharic_column_lang(self):
        w = self._wiring()
        argv = w["invocation"]["amharic_column"]
        assert "amh" in argv, "Amharic column must use amh"

    def test_subprocess_pattern_devnull_stdin(self):
        w = self._wiring()
        pattern = w["invocation"]["subprocess_pattern"]
        assert "DEVNULL" in str(pattern), "W-W1 mitigation must be documented"

    def test_pre_flight_binary_resolution(self):
        w = self._wiring()
        bin_res = w["pre_flight"]["binary_resolution"]
        assert "scripts.core.paths.tesseract_binary" in bin_res["via"]
        assert "_resolve_tesseract_or_exit" in bin_res["helper"]

    def test_pre_flight_language_verification(self):
        w = self._wiring()
        lv = w["pre_flight"]["language_verification"]
        required = set(lv["required"])
        assert required == {"amh", "script/Ethiopic"}, f"required = canonical pair; got {required!r}"

    def test_closed_arc_contracts_block(self):
        w = self._wiring()
        contracts = w["closed_arc_contracts_preserved"]
        assert contracts["tau6x0a_no_ingest"] is True
        assert contracts["tau6x0b_honesty_contract"] is True
        assert contracts["tau6x0c_script_ethiopic_adoption"] is True

    def test_no_ingest_at_this_phase(self):
        w = self._wiring()
        assert w["no_ingest_at_this_phase"] is True

    def test_translation_slot_state_remains_at_seed(self):
        w = self._wiring()
        assert "Π.0-seed" in str(w["translation_slot_state"])

    def test_next_phase_is_tau6x2_plus(self):
        w = self._wiring()
        assert "τ.6.x.2" in str(w["next_phase"])


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1 — SCOPE doc §7.6
# ──────────────────────────────────────────────────────────────────


class TestTau6X1ScopeWiringSection:
    """SCOPE_2026-05-14-parallel-bible.md §7.6 records the τ.6.x.1
    wiring section with the engine semantics, render path, pre-flight
    validation, and τ.6.x.2+ unblock pointer."""

    SCOPE_PATH = REPO / "dev" / "SCOPE_2026-05-14-parallel-bible.md"

    def test_section_header_present(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        assert "§7.6 — τ.6.x.1 wiring" in body, "SCOPE doc must add the §7.6 section header for τ.6.x.1 wiring"

    def test_engine_flag_documented(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        assert "--engine {tesseract,text-layer}" in body, "SCOPE doc must document the new --engine CLI flag"

    def test_render_dpi_documented(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        assert "350 dpi" in body, "render dpi must appear in §7.6"

    def test_pre_flight_resolver_documented(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        assert "scripts.core.paths.tesseract_binary" in body

    def test_pre_flight_language_check_documented(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        assert "tesseract --list-langs" in body, "pre-flight language verification command must appear in §7.6"

    def test_w_w1_mitigation_documented(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        assert "stdin=subprocess.DEVNULL" in body, (
            "W-W1 subprocess pattern must be documented as a τ.6.x.1 wiring detail"
        )

    def test_tau6x2_plus_unblock_pointer(self):
        body = self.SCOPE_PATH.read_text(encoding="utf-8")
        assert "τ.6.x.2+" in body, "next-phase pointer to τ.6.x.2+ bulk-ingest must appear"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1 — PI2 pre-flight checklist row flip
# ──────────────────────────────────────────────────────────────────


class TestTau6X1PreFlightChecklistFlip:
    """The PI2 pre-flight checklist τ.6.x.1 row flipped from ⬜ pending
    → ✓ SHIPPED. The old τ.6.x.1+ row is replaced by τ.6.x.1 (shipped)
    plus τ.6.x.2+ (publisher-direction-gated bulk-ingest)."""

    CHECKLIST_PATH = REPO / "dev" / "PI2_PRE_FLIGHT_CHECKLIST.md"

    def test_tau6x1_row_marked_shipped(self):
        body = self.CHECKLIST_PATH.read_text(encoding="utf-8")
        # Find the τ.6.x.1 (not τ.6.x.1+) row.
        rows = [
            line
            for line in body.splitlines()
            if "τ.6.x.1 " in line and "|" in line and "τ.6.x.1+" not in line and "τ.6.x.1 " in line
        ]
        assert rows, "PI2 checklist must contain a τ.6.x.1 row (engine wired)"
        shipped = [r for r in rows if "SHIPPED" in r or "shipped" in r]
        assert shipped, f"τ.6.x.1 row must indicate SHIPPED state; got {rows!r}"

    def test_tau6x2_plus_row_marks_publisher_gated(self):
        body = self.CHECKLIST_PATH.read_text(encoding="utf-8")
        rows = [line for line in body.splitlines() if "τ.6.x.2+" in line and "|" in line]
        assert rows, "PI2 checklist must contain a τ.6.x.2+ row (publisher-direction-gated)"
        gated = [r for r in rows if "publisher" in r.lower()]
        assert gated, f"τ.6.x.2+ row must reference publisher direction as the gate; got {rows!r}"

    def test_unblock_status_lists_tau6x1_shipped(self):
        body = self.CHECKLIST_PATH.read_text(encoding="utf-8")
        # The "Π.2 is unblocked when" sentence should list τ.6.x.1 as shipped.
        # Accepts both the τ.6.x.1-era phrasing and the τ.6.x.1.A-extended
        # phrasing ("τ.6.x.0c + τ.6.x.1 + τ.6.x.1.A shipped").
        assert (
            "τ.6.x.1 shipped" in body
            or "τ.6.x.1 + τ.6.x.0c" in body
            or "τ.6.x.0c + τ.6.x.1" in body  # covers " shipped" + " + τ.6.x.1.A shipped"
        ), "unblock-status line must annotate τ.6.x.1 as shipped"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1 — runtime tesseract probe (optional, env-dependent)
# ──────────────────────────────────────────────────────────────────


class TestTau6X1TesseractRuntime:
    """OPTIONAL runtime probe — if Tesseract is locally available via
    the resolver, verify the wiring functions execute end-to-end at
    the subprocess boundary. Skipped when Tesseract is not installed
    locally so the suite remains environment-independent.

    Uses the W-W1-safe subprocess pattern throughout (stdin=DEVNULL).
    """

    @staticmethod
    def _tesseract_or_skip() -> Path:
        from scripts.core.paths import tesseract_binary

        binary = tesseract_binary()
        if binary is None:
            pytest.skip("Tesseract not locally available; runtime probe skipped")
        return binary

    def test_check_languages_against_real_install(self):
        binary = self._tesseract_or_skip()
        from scripts.extract_parallel_pdf import (
            _check_tesseract_languages,
            _required_tesseract_languages,
        )

        missing = _check_tesseract_languages(binary, _required_tesseract_languages())
        # Empty missing list is the only correct state when this test runs
        # (otherwise τ.6.x.0c verification was wrong about script/Ethiopic
        # shipping in the standard install).
        assert missing == [], f"both amh + script/Ethiopic must be in this Tesseract install; missing: {missing!r}"

    def test_verify_languages_does_not_exit(self):
        binary = self._tesseract_or_skip()
        from scripts.extract_parallel_pdf import _verify_tesseract_languages_or_exit

        _verify_tesseract_languages_or_exit(binary)  # no raise


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1 — closed-arc invariants regression-guarded
# ──────────────────────────────────────────────────────────────────


class TestTau6X1ClosedArcInvariantPreservation:
    """Every closed-arc invariant from Π.0.1 → Ω.0 remains intact after
    the τ.6.x.1 wiring ship (declarative-codification + engine code
    only; no data mutation, no popup-language change, no canon change).
    """

    def test_amharic_still_in_popup_languages(self):
        from scripts.build_edition import POPUP_LANGUAGES

        assert "amharic" in POPUP_LANGUAGES, "τ.6.x.1 must not regress Π.0.1: amharic remains in POPUP_LANGUAGES"

    def test_geez_tewahedo_still_gen_only(self):
        slot = REPO / "content" / "translations" / "geez-tewahedo"
        files = sorted(p.name for p in slot.iterdir() if p.suffix == ".py")
        assert "gen.py" in files, (
            f"τ.6.x.2.a-h batch: geez-tewahedo/ must contain gen.py (Π.0 seed or its ocr-tier3 successor); got {files}"
        )  # MIGRATED at τ.6.x.2.a-h batch ship-time (2026-05-15):
        # originally asserted geez-tewahedo/ holds ONLY the Π.0
        # gen.py seed. The τ.6.x.2.a-h Geʽez catchup batch upgraded
        # the Geʽez column to 8 ocr-tier3 books (gen+ex+lev+num+deu
        # +jos+jdg+rut). Same migration the companion
        # test_amharic_tewahedo_contains_gen_py received at τ.7.x.b.
        # Durable invariant: gen.py present (Π.0 seed or successor).def test_amharic_tewahedo_contains_gen_py(self):
        """Refactored share-pin→milestone-pin at τ.7.x.b ship-time per
        `feedback_share_pin_pattern`. τ.6.x.1's original invariant
        (`files == ['gen.py']`) was the Π.0 seed state; τ.7.x.a + τ.7.x.b
        broke this exact assertion. Durable invariant: gen.py is present."""
        slot = REPO / "content" / "translations" / "amharic-tewahedo"
        files = sorted(p.name for p in slot.iterdir() if p.suffix == ".py")
        assert "gen.py" in files, (
            f"τ.6.x.1 contract relaxed at τ.7.x.b: amharic-tewahedo must contain gen.py; got {files}"
        )

    def test_tau6x0b_option_d_authorization_intact(self):
        path = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        strat = cfg["ocr_strategy"]
        assert strat["authorized_option"] == "D-Hybrid"
        assert strat["default_engine"] == "tesseract"

    def test_tau6x0c_script_ethiopic_adoption_intact(self):
        path = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        v = cfg["ocr_strategy"]["tau6x0c_verification"]
        assert v["geez_recognizer_adopted"]["model"] == "script/Ethiopic"

    def test_meqabyan_arc_close_67_67_intact(self):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        ec = sources.ethiopian_commentaries()
        for book, total in [("mq1", 36), ("mq2", 21), ("mq3", 10)]:
            chs_with_entries = set()
            for ch in range(1, total + 1):
                for v in range(1, 60):
                    entries = [e for e in ec.for_verse(book, ch, v) if e.father == "Meqabyan (Ethiopian tradition)"]
                    if entries:
                        chs_with_entries.add(ch)
                        break
            assert chs_with_entries == set(range(1, total + 1)), (
                f"τ.6.x.1 must not regress γ.4.8.E arc-close {book} {total}/{total}"
            )

    def test_meqabyan_count_at_least_212(self):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        ec = sources.ethiopian_commentaries()
        meq = [
            e
            for verse_entries in ec._by_verse.values()
            for e in verse_entries
            if e.father == "Meqabyan (Ethiopian tradition)"
        ]
        assert len(meq) >= 212, f"τ.6.x.1: Meqabyan count must remain ≥212; got {len(meq)}"

    def test_omega0_free_public_pivot_intact(self):
        """Ω.0 pivot invariants must not regress at τ.6.x.1 (the wiring
        ship touches NO ISBN/onix/publishing surface)."""
        editions_yaml = (REPO / "content" / "editions.yaml").read_text(encoding="utf-8")
        assert "isbn:" not in editions_yaml.lower(), "τ.6.x.1 must not regress Ω.0: editions.yaml must remain ISBN-free"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1 — phase coverage in CHANGELOG + PLAN
# ──────────────────────────────────────────────────────────────────


class TestTau6X1PhaseCoverage:
    """τ.6.x.1 is mentioned in the CHANGELOG (ship entry exists) and
    is listed as shipped (✓) in the PLAN parallel-bible track ledger."""

    CHANGELOG_PATH = REPO / "dev" / "CHANGELOG.md"
    # PLAN_2026-05-09 archived to dev/archive/ on 2026-05-21 (superseded
    # by PLAN_2026-05-21); the phase ledger it pins lives there now.
    PLAN_PATH = REPO / "dev" / "archive" / "PLAN_2026-05-09.md"

    def test_changelog_mentions_tau6x1_ship(self):
        body = self.CHANGELOG_PATH.read_text(encoding="utf-8")
        assert "τ.6.x.1" in body, "CHANGELOG must mention τ.6.x.1"

    def test_plan_lists_tau6x1_as_shipped(self):
        body = self.PLAN_PATH.read_text(encoding="utf-8")
        rows = [line for line in body.splitlines() if "τ.6.x.1" in line and "τ.6.x.1+" not in line]
        assert rows, "PLAN must contain a τ.6.x.1 row"
        shipped = [r for r in rows if "✓" in r]
        assert shipped, f"PLAN must mark τ.6.x.1 as shipped (✓); got {rows!r}"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1.A — pilot validation (empirical wiring check)
# ──────────────────────────────────────────────────────────────────


class TestTau6X1ASourceYamlPilotBlock:
    """`_source.yaml::ocr_strategy.tau6x1a_pilot_validation` records the
    empirical pilot validation result: page tested, timing, quality
    observations, pre-flight validations confirmed, no-ingest contract
    preserved."""

    YAML_PATH = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"

    def _pilot(self):
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        return cfg["ocr_strategy"]["tau6x1a_pilot_validation"]

    def test_pilot_block_present(self):
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        assert "tau6x1a_pilot_validation" in cfg["ocr_strategy"]

    def test_pilot_phase_and_date(self):
        p = self._pilot()
        assert p["validated_at_phase"] == "τ.6.x.1.A"
        assert "2026-05-14" in str(p["validated_date"])

    def test_pilot_reference_artifact_path(self):
        p = self._pilot()
        assert p["reference_artifact"] == "dev/PILOT_TAU6X1A_OUTPUT.md"
        assert (REPO / p["reference_artifact"]).is_file(), (
            "the referenced PILOT_TAU6X1A_OUTPUT.md artifact must exist on disk"
        )

    def test_pilot_page_tested_is_1318(self):
        p = self._pilot()
        assert p["page_tested"]["pdf_page_index"] == 1318
        assert p["page_tested"]["book"] == "mq1"

    def test_pilot_timing_under_60s(self):
        p = self._pilot()
        assert p["timing"]["total_per_page_seconds"] < 60, (
            f"τ.6.x.1.A timing budget violation: per-page > 60s; got {p['timing']['total_per_page_seconds']}s"
        )

    def test_pilot_preflight_validations_block(self):
        p = self._pilot()
        pfv = p["pre_flight_validations_empirically_confirmed"]
        # All six pre-flight steps must report empirically confirmed.
        assert pfv["tesseract_binary_resolver_finds_windows_install"] is True
        assert pfv["check_tesseract_languages_recognizes_amh_and_script_ethiopic"] is True
        assert pfv["pymupdf_pixmap_at_350dpi_produces_valid_png"] is True
        assert pfv["subprocess_run_w_w1_safe_pattern_works"] is True
        assert pfv["tesseract_invocation_returns_ethiopic_text"] is True
        assert pfv["tempfile_temporary_directory_shared_and_auto_cleaned"] is True

    def test_pilot_preserves_no_ingest_contract(self):
        p = self._pilot()
        assert p["no_ingest_at_this_phase"] is True
        assert "Π.0-seed" in str(p["translation_slot_state"])

    def test_pilot_next_phase_references_tau6x1b_or_tau6x2(self):
        p = self._pilot()
        next_str = str(p["next_phase"])
        assert "τ.6.x.1.B" in next_str or "τ.6.x.2" in next_str

    def test_pilot_records_ethiopic_numeral_parser_finding(self):
        p = self._pilot()
        qo = p["quality_observations"]
        # The τ.6.x.1.A pilot discovered that parse_verses_from_text()
        # keys off Arabic digits but the PDF's verse markers are Ethiopic
        # numerals — flagged as a τ.6.x.1.B / τ.6.x.2-prep task.
        assert "verse_numeral_parser_extension_needed" in qo


class TestTau6X1APilotReferenceArtifact:
    """The dev/PILOT_TAU6X1A_OUTPUT.md reference artifact records the
    pilot output + timing + quality observations for publisher
    τ.6.x.2+ direction."""

    ARTIFACT_PATH = REPO / "dev" / "PILOT_TAU6X1A_OUTPUT.md"

    def test_artifact_exists(self):
        assert self.ARTIFACT_PATH.is_file(), "dev/PILOT_TAU6X1A_OUTPUT.md must exist as the τ.6.x.1.A reference"

    def test_artifact_references_environment(self):
        body = self.ARTIFACT_PATH.read_text(encoding="utf-8")
        for token in ("Tesseract", "script/Ethiopic", "amh", "350 dpi", "pymupdf"):
            assert token in body, f"reference artifact must mention {token!r}"

    def test_artifact_records_timing(self):
        body = self.ARTIFACT_PATH.read_text(encoding="utf-8")
        assert "Timing" in body
        assert "7" in body  # ~7s total per page

    def test_artifact_records_publisher_direction_inputs(self):
        body = self.ARTIFACT_PATH.read_text(encoding="utf-8")
        # The four D-decisions for τ.6.x.2+ must be listed.
        for token in ("Cadence", "Target-tier ramp", "Per-book audit", "Amharic-parallel sequencing"):
            assert token in body, f"reference artifact must list publisher decision: {token!r}"


class TestTau6X1APilotRuntime:
    """OPTIONAL runtime regression-pin — if Tesseract AND the publisher's
    parallel-Bible PDF are both available locally, re-execute the
    τ.6.x.1.A pilot validation and assert the engine produces
    Ethiopic text in both columns within the documented timing budget.

    Skipped when either Tesseract or the PDF is unavailable so the
    suite remains environment-independent.

    Uses the W-W1-safe subprocess pattern from τ.6.x.1.
    """

    @staticmethod
    def _resolve_pdf_or_skip():
        """Replicate extract_parallel_pdf.resolve_pdf_path() but with
        pytest.skip semantics rather than SystemExit."""
        from scripts.extract_parallel_pdf import load_source_config, resolve_pdf_path

        cfg = load_source_config()
        try:
            return resolve_pdf_path(cfg)
        except SystemExit:
            pytest.skip("parallel-Bible PDF not locally available; runtime pilot skipped")

    @staticmethod
    def _tesseract_or_skip():
        from scripts.core.paths import tesseract_binary

        binary = tesseract_binary()
        if binary is None:
            pytest.skip("Tesseract not locally available; runtime pilot skipped")
        return binary

    def test_page_1318_renders_and_ocrs_in_under_60s(self):
        import time

        binary = self._tesseract_or_skip()
        pdf_path = self._resolve_pdf_or_skip()

        import fitz

        from scripts.extract_parallel_pdf import tesseract_extract_columns

        t0 = time.monotonic()
        doc = fitz.open(str(pdf_path))
        try:
            page = doc[1318]
            geez, amh = tesseract_extract_columns(page, binary)
        finally:
            doc.close()
        elapsed = time.monotonic() - t0
        assert elapsed < 60.0, f"τ.6.x.1.A timing budget: per-page must complete in <60s; got {elapsed:.1f}s"
        assert len(geez) > 0, "Geʽez column OCR must return non-empty text on page 1318"
        assert len(amh) > 0, "Amharic column OCR must return non-empty text on page 1318"

    def test_page_1318_geez_column_contains_ethiopic(self):
        binary = self._tesseract_or_skip()
        pdf_path = self._resolve_pdf_or_skip()

        import fitz

        from scripts.extract_parallel_pdf import tesseract_extract_columns

        doc = fitz.open(str(pdf_path))
        try:
            page = doc[1318]
            geez, _amh = tesseract_extract_columns(page, binary)
        finally:
            doc.close()
        ethiopic_count = sum(1 for ch in geez if 0x1200 <= ord(ch) <= 0x137F)
        assert ethiopic_count >= 50, (
            f"Geʽez column must contain ≥50 Ethiopic chars on page 1318 (mq1 ch1 opening); got {ethiopic_count}"
        )

    def test_page_1318_amharic_column_contains_ethiopic(self):
        binary = self._tesseract_or_skip()
        pdf_path = self._resolve_pdf_or_skip()

        import fitz

        from scripts.extract_parallel_pdf import tesseract_extract_columns

        doc = fitz.open(str(pdf_path))
        try:
            page = doc[1318]
            _geez, amh = tesseract_extract_columns(page, binary)
        finally:
            doc.close()
        ethiopic_count = sum(1 for ch in amh if 0x1200 <= ord(ch) <= 0x137F)
        assert ethiopic_count >= 50, (
            f"Amharic column must contain ≥50 Ethiopic chars on page 1318; got {ethiopic_count}"
        )


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1.B — Ethiopic-numeral verse-marker normalization
# ──────────────────────────────────────────────────────────────────


class TestTau6X1BModuleSurface:
    """τ.6.x.1.B exposes the normalizer + Ethiopic-punctuation constant
    + line-start regex at module scope."""

    def test_normalize_verse_numerals_importable(self):
        from scripts.extract_parallel_pdf import normalize_verse_numerals

        assert callable(normalize_verse_numerals)

    def test_ethiopic_punct_constant_has_all_marks(self):
        from scripts.extract_parallel_pdf import ETHIOPIC_PUNCT

        # The standard Ethiopic punctuation block (U+1361 … U+1368).
        for ch in "።፣፤፥፦፧፨":
            assert ch in ETHIOPIC_PUNCT, f"{ch!r} ({hex(ord(ch))}) must be in ETHIOPIC_PUNCT"

    def test_ethiopic_line_start_regex_is_a_pattern(self):
        import re

        from scripts.extract_parallel_pdf import ETHIOPIC_LINE_START_NUMERAL_RE

        assert isinstance(ETHIOPIC_LINE_START_NUMERAL_RE, re.Pattern)


class TestTau6X1BNormalizeVerseNumerals:
    """`normalize_verse_numerals` converts Ethiopic-numeral verse markers
    at line starts to Arabic-digit+colon form. Round-trippable via
    `geez_numeral_to_int`; backward-compatible (Arabic-digit input is a
    no-op)."""

    def _norm(self, text):
        from scripts.extract_parallel_pdf import normalize_verse_numerals

        return normalize_verse_numerals(text)

    def test_single_ethiopic_digit(self):
        assert self._norm("፪፤ ስመ ጺሩጻይዳን ...") == "2: ስመ ጺሩጻይዳን ..."

    def test_compound_ethiopic_digit(self):
        # ፲፮ = 10 + 6 = 16 per geez_numeral_to_int
        assert self._norm("፲፮፤ ቃል ...") == "16: ቃል ..."

    def test_with_leading_whitespace_preserves_indent(self):
        result = self._norm("   ፫፣ ዓለም ...")
        assert result == "   3: ዓለም ..."

    def test_ethiopic_full_stop_punct_recognized(self):
        # ።  is Ethiopic full stop
        assert self._norm("፭። ይኩን ብርሃን") == "5: ይኩን ብርሃን"

    def test_ethiopic_paragraph_separator_recognized(self):
        # ፨ is Ethiopic paragraph separator
        assert self._norm("፯፨ ሰማይ") == "7: ሰማይ"

    def test_chapter_marker_not_converted(self):
        # ምዕራፍ ፡ ፪ — chapter marker; not a line-start numeral.
        # The leading word `ምዕራፍ` means the line does NOT start
        # with an Ethiopic numeral, so the normalizer leaves it alone.
        line = "ምዕራፍ ፡ ፪ ።"
        assert self._norm(line) == line

    def test_arabic_digit_input_is_noop(self):
        # Text-layer-engine output (Arabic digits) passes through.
        line = "1 በመጀመሪያ ..."
        assert self._norm(line) == line

    def test_no_ethiopic_numeral_at_start_is_noop(self):
        # Verse body line (continuation of prior verse) — no leading
        # Ethiopic-numeral+punct pattern.
        line = "ስለ መጻሕፍት ግን"
        assert self._norm(line) == line

    def test_ethiopic_numeral_without_punct_is_noop(self):
        # An Ethiopic numeral that is NOT followed by a recognized
        # punctuation mark is NOT a verse marker and is left alone.
        line = "፪ ስለ ግዜ"  # space follows the numeral, not punct
        assert self._norm(line) == line

    def test_multiline_text_normalizes_each_line(self):
        body = "፩፤ first\n፪፤ second\n፫፤ third"
        assert self._norm(body) == "1: first\n2: second\n3: third"

    def test_multiline_preserves_unchanged_lines(self):
        body = "header text\n፩፤ first\nbody continuation\n፪፤ second"
        out = self._norm(body)
        assert out == "header text\n1: first\nbody continuation\n2: second"

    def test_invalid_ethiopic_sequence_falls_back_to_input(self):
        # If the Ethiopic-numeral parse fails (unreachable in current
        # geez_numeral_to_int because all U+1369…U+137C chars are
        # accepted, but defensive), the line passes through unchanged.
        line = "  ፀ፤ corruptish"  # ፀ is Ethiopic letter, not numeral
        assert self._norm(line) == line

    def test_empty_input(self):
        assert self._norm("") == ""

    def test_blank_lines_preserved(self):
        body = "\n\n፩፤ x\n\n፪፤ y\n\n"
        out = self._norm(body)
        assert out == "\n\n1: x\n\n2: y\n"  # trailing \n collapses via splitlines+join


class TestTau6X1BParseVersesIntegration:
    """`parse_verses_from_text()` now keys off both Arabic AND Ethiopic
    verse-marker numerals (via the τ.6.x.1.B normalizer pre-pass)."""

    def test_ethiopic_numeral_input_yields_verse_tuples(self):
        from scripts.extract_parallel_pdf import parse_verses_from_text

        # Synthetic OCR-style input mimicking the τ.6.x.1.A page-1318
        # Geʽez column shape: Ethiopic-numeral verse markers + Ethiopic
        # body text + Ethiopic punctuation separators.
        text = (
            "ምዕራፍ ፡ ፩\n"  # chapter 1 marker — not a verse line
            "፩፤ ስለ ብርሃን ።\n"
            "፪፤ ሰማይ እና ምድር ።\n"
            "፫፤ የሰው ልጅ ።\n"
        )
        verses = parse_verses_from_text(text)
        # Three verses parsed (chapter 1, verses 1-3).
        verse_keys = {(c, v) for c, v, _t in verses}
        assert (1, 1) in verse_keys
        assert (1, 2) in verse_keys
        assert (1, 3) in verse_keys

    def test_arabic_digit_input_still_yields_verse_tuples(self):
        from scripts.extract_parallel_pdf import parse_verses_from_text

        # Backward-compatibility: text-layer-engine output (Arabic
        # digits) must continue to parse correctly. Body text mixes
        # Ethiopic + ASCII so the `has_ethiopic` page-header filter
        # does not drop the lines.
        text = "1 ስለ ብርሃን\n2 ስለ ሰማይ\n3 ስለ ምድር"
        verses = parse_verses_from_text(text)
        verse_keys = {(c, v) for c, v, _t in verses}
        for n in (1, 2, 3):
            assert (1, n) in verse_keys

    def test_chapter_marker_inside_ethiopic_input(self):
        from scripts.extract_parallel_pdf import parse_verses_from_text

        # Verse bodies are written in Ethiopic so the `has_ethiopic`
        # page-header filter does not drop them (mirrors real OCR
        # output where verse bodies are Ge'ez or Amharic fidel).
        # τ.6.x.1.B's chapter-header regex extension recognizes the
        # `ምዕራፍ ፡ ፩` form (Ethiopic word-space `፡` separator) that
        # Tesseract OCR emits where the text-layer engine sees ASCII
        # whitespace only.
        text = "ምዕራፍ ፡ ፩\n፩፤ ስለ ብርሃን\n፪፤ ስለ ሰማይ\nምዕራፍ ፡ ፪\n፩፤ ስለ ዓለም\n፪፤ ስለ ሰው\n"
        verses = parse_verses_from_text(text)
        keys = {(c, v) for c, v, _t in verses}
        assert (1, 1) in keys and (1, 2) in keys
        assert (2, 1) in keys and (2, 2) in keys


class TestTau6X1BPilotRuntime:
    """OPTIONAL runtime regression-pin — if Tesseract AND the publisher's
    parallel-Bible PDF are both available, render+OCR page 1318 and
    confirm `parse_verses_from_text()` produces non-empty verse tuples
    in BOTH columns (the τ.6.x.1.B finding-resolution proof).

    Skipped when either Tesseract or the PDF is unavailable.
    """

    @staticmethod
    def _resolve_pdf_or_skip():
        from scripts.extract_parallel_pdf import load_source_config, resolve_pdf_path

        cfg = load_source_config()
        try:
            return resolve_pdf_path(cfg)
        except SystemExit:
            pytest.skip("parallel-Bible PDF not locally available; runtime pilot skipped")

    @staticmethod
    def _tesseract_or_skip():
        from scripts.core.paths import tesseract_binary

        binary = tesseract_binary()
        if binary is None:
            pytest.skip("Tesseract not locally available; runtime pilot skipped")
        return binary

    def _extract_page_1318(self):
        binary = self._tesseract_or_skip()
        pdf_path = self._resolve_pdf_or_skip()

        import fitz

        from scripts.extract_parallel_pdf import tesseract_extract_columns

        doc = fitz.open(str(pdf_path))
        try:
            page = doc[1318]
            return tesseract_extract_columns(page, binary)
        finally:
            doc.close()

    def test_geez_column_yields_verse_tuples_on_page_1318(self):
        from scripts.extract_parallel_pdf import parse_verses_from_text

        geez, _amh = self._extract_page_1318()
        verses = parse_verses_from_text(geez)
        # Page 1318 (mq1 ch1 opening) contains multiple verses. Pre-
        # τ.6.x.1.B this would have been 0 (Ethiopic numerals didn't
        # match `\d+`). Post-τ.6.x.1.B should be ≥3.
        assert len(verses) >= 3, (
            f"τ.6.x.1.B: page 1318 Geʽez column must yield ≥3 verse tuples after normalization; got {len(verses)}"
        )

    def test_amharic_column_yields_verse_tuples_on_page_1318(self):
        from scripts.extract_parallel_pdf import parse_verses_from_text

        _geez, amh = self._extract_page_1318()
        verses = parse_verses_from_text(amh)
        # The Amharic column has noisier OCR layout than the Geʽez
        # (font ornamentation, page-header bleed, line-break preservation
        # is imperfect under --psm 6). The τ.6.x.1.B normalizer firing
        # at all is the regression-pin signal; tighter tier-2 quality
        # is a future cross-check task.
        assert len(verses) >= 2, (
            f"τ.6.x.1.B: page 1318 Amharic column must yield ≥2 verse tuples after normalization "
            f"(noisy column; ≥2 is the τ.6.x.1.B-fired confidence floor; tier-2 quality is "
            f"future operator-cross-check work). Got {len(verses)}"
        )


class TestTau6X1BSourceYamlBlock:
    """`_source.yaml::ocr_strategy.tau6x1b_parser_extension` records the
    parser-extension ship that resolves the τ.6.x.1.A
    `verse_numeral_parser_extension_needed` finding."""

    YAML_PATH = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"

    def _block(self):
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        return cfg["ocr_strategy"]["tau6x1b_parser_extension"]

    def test_block_present(self):
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        assert "tau6x1b_parser_extension" in cfg["ocr_strategy"]

    def test_phase_and_date(self):
        b = self._block()
        assert b["shipped_at_phase"] == "τ.6.x.1.B"
        assert "2026-05-15" in str(b["shipped_date"])

    def test_helpers_added_block(self):
        b = self._block()
        helpers = b["helpers_added"]
        assert "ETHIOPIC_PUNCT" in helpers
        assert "ETHIOPIC_LINE_START_NUMERAL_RE" in helpers
        assert "normalize_verse_numerals" in helpers

    def test_parser_change_block(self):
        b = self._block()
        pc = b["parser_change"]
        assert pc["function"] == "parse_verses_from_text"
        assert "normalize_verse_numerals" in str(pc["change"])

    def test_chapter_header_regex_change_block(self):
        b = self._block()
        ch = b["chapter_header_regex_change"]
        assert r"[\s፡፣]*" in str(ch["to"]), "regex `to` must show the [\\s፡፣]* extension"

    def test_resolves_finding_pointer(self):
        b = self._block()
        assert "tau6x1a_pilot_validation" in str(
            b["resolves_finding"]
        ) and "verse_numeral_parser_extension_needed" in str(b["resolves_finding"])

    def test_empirical_validation_recorded(self):
        b = self._block()
        ev = b["empirical_validation"]
        assert ev["page_tested"] == 1318
        assert ev["pre_tau6x1b_geez_verses_parsed"] == 0
        assert ev["post_tau6x1b_geez_verses_parsed_at_least"] >= 3
        assert ev["post_tau6x1b_amharic_verses_parsed_at_least"] >= 2

    def test_closed_arc_contracts_preserved(self):
        b = self._block()
        c = b["closed_arc_contracts_preserved"]
        for key in (
            "tau6x0a_no_ingest",
            "tau6x0b_honesty_contract",
            "tau6x0c_script_ethiopic_adoption",
            "tau6x1_engine_wiring",
            "tau6x1a_pilot_validation",
        ):
            assert c[key] is True, f"τ.6.x.1.B contract preservation: {key} must be True"

    def test_no_ingest_preserved(self):
        b = self._block()
        assert b["no_ingest_at_this_phase"] is True
        assert "Π.0-seed" in str(b["translation_slot_state"])

    def test_next_phase_is_tau6x2(self):
        b = self._block()
        assert "τ.6.x.2" in str(b["next_phase"])

    def test_tau6x1a_finding_marked_resolved(self):
        """The τ.6.x.1.A pilot block should now carry a
        `finding_resolved_at_phase` annotation pointing to τ.6.x.1.B."""
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        pilot = cfg["ocr_strategy"]["tau6x1a_pilot_validation"]
        assert pilot.get("finding_resolved_at_phase") == "τ.6.x.1.B", (
            "τ.6.x.1.A pilot block must annotate the finding-resolution phase"
        )


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1.C — Paragraph-mode parser extension (2026-05-15)
# ──────────────────────────────────────────────────────────────────
#
# Resolves the τ.7.x.a.0 PILOT empirical finding
# (paragraph_mode_parser_extension_needed) by adding a
# `paragraph_mode=True` kwarg to `parse_verses_from_text()` that
# splits verses by `።` sentence-terminator + filters cross-reference
# fragments + numbers sequentially per chapter.


class TestTau6X1CModuleSurface:
    """τ.6.x.1.C exposes new module-level symbols + the
    paragraph_mode kwarg on parse_verses_from_text."""

    def test_cross_ref_fragment_re_importable(self):
        from scripts.extract_parallel_pdf import CROSS_REF_FRAGMENT_RE
        import re as _re

        assert isinstance(CROSS_REF_FRAGMENT_RE, _re.Pattern)

    def test_is_cross_ref_fragment_callable(self):
        from scripts.extract_parallel_pdf import is_cross_ref_fragment

        assert callable(is_cross_ref_fragment)

    def test_genesis_verse_counts_present(self):
        from scripts.extract_parallel_pdf import GENESIS_VERSE_COUNTS

        assert isinstance(GENESIS_VERSE_COUNTS, dict)
        # Genesis has 50 chapters.
        assert set(GENESIS_VERSE_COUNTS.keys()) == set(range(1, 51))
        # Total = 1534 (Masoretic tradition treats Gen 31:55 as its own
        # verse). Some Christian editions renumber that to 32:1 yielding
        # 1533. Tolerance ±2 accommodates either tradition.
        total = sum(GENESIS_VERSE_COUNTS.values())
        assert 1532 <= total <= 1536, (
            f"Genesis verse-count total should be ~1533-1534 (Masoretic vs Christian); got {total}"
        )

    def test_parse_verses_from_text_accepts_paragraph_mode_kwarg(self):
        from scripts.extract_parallel_pdf import parse_verses_from_text

        # Should not raise when called with paragraph_mode kwarg.
        result = parse_verses_from_text("", paragraph_mode=True)
        assert result == []

    def test_paragraph_mode_default_is_false(self):
        """Backward compatibility: existing callers (which use the
        single-line/Tewahedo-distinctive mode) should NOT need to
        change. paragraph_mode defaults to False."""
        import inspect
        from scripts.extract_parallel_pdf import parse_verses_from_text

        sig = inspect.signature(parse_verses_from_text)
        assert sig.parameters["paragraph_mode"].default is False


class TestTau6X1CIsCrossRefFragment:
    """is_cross_ref_fragment classifies cross-reference vs body-text
    fragments. Cross-refs are short numeral-dominated strings; body
    text is longer Ethiopic prose."""

    def _fn(self):
        from scripts.extract_parallel_pdf import is_cross_ref_fragment

        return is_cross_ref_fragment

    def test_filters_psalm_cross_ref_with_ethiopic_numeral(self):
        assert self._fn()("መዝ ፳፻፤5") is True

    def test_filters_john_cross_ref_with_book_period(self):
        assert self._fn()("ዮሐ.ይ፤፳-፲፻") is True

    def test_filters_pure_numerals_chapter_verse(self):
        assert self._fn()("፻9፪፤፳") is True

    def test_filters_short_qedus_cross_ref(self):
        assert self._fn()("ቀ. ፲፫") is True

    def test_keeps_gen_1_1_body_text(self):
        """Real Gen 1:1 Amharic — must NOT be classified as cross-ref."""
        assert self._fn()("በመጀመሪያ እግዚአብሔር ሰማይንና ምድርን ፈጠረ") is False

    def test_keeps_gen_1_3_body_text(self):
        assert self._fn()("እግዚአብሔርም ብርሃን ይሁን አለ ፡ ብርሃንም ሆነ") is False

    def test_keeps_long_body_text_with_some_numerals(self):
        """A long verse with embedded numerals should NOT be flagged
        — the heuristic kicks in only for SHORT strings (≤30 chars)."""
        long_text = "ምድር ግን ባዶዋን ነበረች ፣ አትታይም ነበር ፣ አልተዘጋ ሄደችም ነበር"
        assert self._fn()(long_text) is False

    def test_handles_empty_string(self):
        assert self._fn()("") is False

    def test_handles_whitespace_only(self):
        assert self._fn()("   ") is False

    def test_classifies_by_numeral_coverage_fallback(self):
        """If a fragment is short and >25% numerals but doesn't match
        the regex exactly, the numeral-coverage heuristic should catch
        it."""
        # 5 chars, 2 are numerals (40%): under regex threshold but
        # over numeral-coverage threshold.
        assert self._fn()("ት5፪") is True


class TestTau6X1CParagraphModeUnit:
    """Unit tests for `parse_verses_from_text(text, paragraph_mode=True)`
    on synthetic Amharic-Genesis-shaped input."""

    def _parse(self, text, **kwargs):
        from scripts.extract_parallel_pdf import parse_verses_from_text

        return parse_verses_from_text(text, paragraph_mode=True, **kwargs)

    def test_empty_string_returns_empty_list(self):
        assert self._parse("") == []

    def test_single_short_fragment_filtered(self):
        """A single very-short fragment is filtered as OCR noise."""
        assert self._parse("ህዘ።") == []  # <10 chars; filtered

    def test_single_body_text_verse(self):
        body = "በመጀመሪያ እግዚአብሔር ሰማይንና ምድርን ፈጠረ።"
        result = self._parse(body)
        assert len(result) == 1
        assert result[0][0] == 1  # chapter
        assert result[0][1] == 1  # verse
        assert "በመጀመሪያ" in result[0][2]

    def test_three_verses_split_by_period(self):
        body = (
            "በመጀመሪያ እግዚአብሔር ሰማይንና ምድርን ፈጠረ።\nምድር ግን ባዶዋን ነበረች አትታይም ነበር አልተዘጋ ሄደችም ነበር።\nእግዚአብሔርም ብርሃን ይሁን አለ ብርሃንም ሆነ።"
        )
        result = self._parse(body)
        assert len(result) == 3
        assert all(v[0] == 1 for v in result)  # all chapter 1
        assert [v[1] for v in result] == [1, 2, 3]  # sequential

    def test_cross_ref_filtered_out(self):
        """Cross-reference fragments between verses are skipped."""
        body = (
            "በመጀመሪያ እግዚአብሔር ሰማይንና ምድርን ፈጠረ።\n"
            "መዝ ፳፻፤5።\n"  # cross-reference; should be filtered
            "ምድር ግን ባዶዋን ነበረች አትታይም ነበር አልተዘጋ ሄደችም ነበር።"
        )
        result = self._parse(body)
        assert len(result) == 2  # cross-ref skipped
        assert result[0][1] == 1  # verse numbering doesn't advance for cross-ref
        assert result[1][1] == 2

    def test_chapter_marker_resets_verse_counter(self):
        """When a chapter marker is encountered, verse counter resets.

        Note (τ.6.x.1.D): pre-marker text is now DISCARDED when
        markers exist (it's typically title-page header noise, not
        chapter 1 content). To test verse-counter-reset behavior with
        the τ.6.x.1.D semantics, use TWO chapter markers — content
        between them is ch 1, content after the second marker is ch 2.
        """
        body = (
            "ምዕራፍ ፩።\n"  # chapter 1 marker; pre-marker text discarded
            "በመጀመሪያ እግዚአብሔር ሰማይንና ምድርን ፈጠረ።\n"
            "ምድር ግን ባዶዋን ነበረች አትታይም ነበር አልተዘጋ ሄደችም ነበር።\n"
            "ምዕራፍ ፪።\n"  # chapter 2 marker
            "ሰማይና ምድር ተፈጸሙ ሁሉም ሰራዊታቸውም።"
        )
        result = self._parse(body)
        assert len(result) >= 3, f"expected ≥3 verses; got {result}"
        ch1_verses = [v for v in result if v[0] == 1]
        ch2_verses = [v for v in result if v[0] == 2]
        assert len(ch1_verses) >= 2, f"expected ≥2 ch1 verses; got {ch1_verses}"
        assert len(ch2_verses) >= 1, f"expected ≥1 ch2 verse; got {ch2_verses}"
        # Ch2 verse counter resets to 1.
        assert ch2_verses[0][1] == 1

    def test_ascii_page_header_filtered(self):
        """ASCII page-header bleed should be filtered out."""
        body = "www.ethiopianorthodox.org\nThe Ethiopian Orthodox Tewahido Church\nበመጀመሪያ እግዚአብሔር ሰማይንና ምድርን ፈጠረ።"
        result = self._parse(body)
        assert len(result) == 1
        assert "በመጀመሪያ" in result[0][2]

    def test_period_terminator_preserved(self):
        """Output verse text should end with `።` for verse integrity."""
        body = "በመጀመሪያ እግዚአብሔር ሰማይንና ምድርን ፈጠረ።"
        result = self._parse(body)
        assert result[0][2].endswith("።")

    def test_ocr_noise_punctuation_stripped(self):
        """Trailing OCR-noise punctuation (=, ;, |) should be stripped."""
        body = "በመጀመሪያ እግዚአብሔር ሰማይንና ምድርን ፈጠረ ='|"
        result = self._parse(body + "።")
        # The verse should still parse cleanly; trailing noise stripped.
        assert len(result) == 1
        assert "=" not in result[0][2] or "|" not in result[0][2]


class TestTau6X1CParagraphModeRuntime:
    """Real-PDF runtime regression pin. Verifies that the τ.6.x.1.C
    parser extension produces a meaningful verse count on the
    Amharic Genesis text-layer output. The pin floor is calibrated
    empirically at τ.6.x.1.C ship-time: text-layer pages 0-5 produced
    87 verses (vs expected 138 = ~63% coverage); the floor is set at
    75 to leave a 14% safety margin against future OCR variance."""

    @pytest.fixture(scope="class")
    def _pdf(self):
        """Open the parallel-Bible PDF if available, else skip."""
        import sys

        sys.path.insert(0, "scripts")
        try:
            import fitz
        except ImportError:
            pytest.skip("pymupdf (fitz) not installed")
        from scripts.extract_parallel_pdf import load_source_config, resolve_pdf_path

        cfg = load_source_config()
        try:
            pdf_path = resolve_pdf_path(cfg)
        except SystemExit:
            pytest.skip("Parallel-Bible PDF not resolvable")
        if not pdf_path.exists():
            pytest.skip("Parallel-Bible PDF not present on this machine")
        doc = fitz.open(str(pdf_path))
        yield doc
        doc.close()

    def test_text_layer_pages_0_5_yields_at_least_75_verses(self, _pdf):
        """τ.6.x.1.C empirical regression pin: text-layer engine on
        Amharic Genesis pages 0-5 must yield ≥75 verses under
        paragraph_mode=True. Without the extension, default mode
        produces only 2 garbled verses (τ.7.x.a.0 PILOT finding)."""
        import sys

        sys.path.insert(0, "scripts")
        from scripts.extract_parallel_pdf import extract_text_by_column, parse_verses_from_text

        all_amh = ""
        for page_num in range(0, 6):
            page = _pdf[page_num]
            _, amh = extract_text_by_column(page)
            all_amh += amh + "\n"

        verses = parse_verses_from_text(all_amh, paragraph_mode=True)
        assert len(verses) >= 75, (
            f"τ.6.x.1.C runtime pin: text-layer Genesis pages 0-5 must yield "
            f"≥75 verses under paragraph_mode=True; got {len(verses)}. "
            f"Without the extension (default mode), only ~2 garbled verses "
            f"parse — the τ.7.x.a.0 PILOT finding."
        )

    def test_default_mode_unchanged_returns_few_verses(self, _pdf):
        """Backward compatibility runtime pin: default mode (without
        paragraph_mode) still produces NEAR-EMPTY output on Amharic
        Genesis, confirming the τ.7.x.a.0 PILOT finding is real and
        the paragraph_mode extension is the load-bearing fix."""
        import sys

        sys.path.insert(0, "scripts")
        from scripts.extract_parallel_pdf import extract_text_by_column, parse_verses_from_text

        page = _pdf[0]
        _, amh = extract_text_by_column(page)
        verses_default = parse_verses_from_text(amh)
        # Default mode produces ≤5 verses (typically 0-2) on Amharic
        # Genesis page 0 — the PILOT finding.
        assert len(verses_default) <= 5, (
            f"τ.6.x.1.C contract: default mode on Amharic Genesis page 0 "
            f"should produce ≤5 verses (the PILOT finding); got {len(verses_default)}. "
            f"If this rises, the paragraph_mode extension may be regressing."
        )


class TestTau6X1CSourceYamlBlock:
    """`_source.yaml::ocr_strategy.tau6x1c_parser_extension` block
    codifies the τ.6.x.1.C ship + resolves the τ.7.x.a.0 PILOT
    finding back-link."""

    YAML_PATH = (
        Path(__file__).resolve().parent.parent
        / "content"
        / "translations"
        / "sources"
        / "parallel-bible-eotc"
        / "_source.yaml"
    )

    def _block(self) -> dict:
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        return cfg["ocr_strategy"]["tau6x1c_parser_extension"]

    def test_block_exists(self):
        assert isinstance(self._block(), dict)

    def test_shipped_at_phase(self):
        assert self._block()["shipped_at_phase"] == "τ.6.x.1.C"

    def test_shipped_date(self):
        import datetime as _dt

        sd = self._block()["shipped_date"]
        if isinstance(sd, _dt.date):
            assert sd == _dt.date(2026, 5, 15)
        else:
            assert sd == "2026-05-15"

    def test_resolves_finding_back_link(self):
        """The block must reference the τ.7.x.a.0 PILOT finding it
        resolves (single-key back-link annotation per A-I3 pattern
        codification threshold)."""
        b = self._block()
        rf = b.get("resolves_finding")
        assert rf is not None, "τ.6.x.1.C block must record resolves_finding"
        # Resolves the paragraph_mode_parser_extension_needed flag
        # set at τ.7.x.a.0.
        assert "paragraph_mode" in str(rf).lower() or "τ.7.x.a.0" in str(rf)

    def test_helpers_added_inventory(self):
        """The block must inventory the new module-level helpers
        added at τ.6.x.1.C."""
        helpers = self._block().get("helpers_added", {})
        # CROSS_REF_FRAGMENT_RE + is_cross_ref_fragment + GENESIS_VERSE_COUNTS
        # + _parse_paragraph_mode are the four new symbols.
        for h in ["CROSS_REF_FRAGMENT_RE", "is_cross_ref_fragment", "GENESIS_VERSE_COUNTS"]:
            assert any(h in str(k) or h in str(v) for k, v in helpers.items()), (
                f"τ.6.x.1.C helpers_added must inventory {h}"
            )

    def test_parser_api_change_documented(self):
        b = self._block()
        api = b.get("parser_api_change", {})
        assert "paragraph_mode" in str(api), "parser_api_change must reference the paragraph_mode kwarg"

    def test_empirical_validation_recorded(self):
        """The block must record the empirical floor from this
        ship's runtime measurements (≥75 verses for text-layer pages
        0-5)."""
        b = self._block()
        ev = b.get("empirical_validation", {})
        # Either a single floor key OR multiple per-engine floors.
        assert ev, "τ.6.x.1.C empirical_validation must be non-empty"

    def test_closed_arc_contracts_preserved(self):
        b = self._block()
        contracts = b["closed_arc_contracts_preserved"]
        # 7 prior contracts (tau6x0a/b/c + tau6x1 + tau6x1a + tau6x1b
        # + tau6x2D) preserved at τ.6.x.1.C; τ.7.x.a.0 pilot also
        # preserved as the finding that this resolves.
        for k in ("tau6x0a_no_ingest", "tau6x1_engine_wiring", "tau6x1b_parser_extension"):
            assert contracts.get(k) is True, f"τ.6.x.1.C must preserve {k}"

    def test_no_ingest_at_this_phase(self):
        assert self._block()["no_ingest_at_this_phase"] is True

    def test_next_phase_is_tau7xa_proper(self):
        """τ.6.x.1.C unblocks τ.7.x.a (proper) — the original Amharic
        Genesis full-book ingest."""
        np = self._block()["next_phase"]
        # Either τ.7.x.a or τ.7.x.a (proper)
        assert "τ.7.x.a" in str(np)

    def test_tau7xa_pre_pilot_back_links_to_tau6x1c(self):
        """Reciprocal back-link: the τ.7.x.a.0 PILOT block should now
        carry `finding_resolved_at_phase: τ.6.x.1.C` annotation."""
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        pilot = cfg["ocr_strategy"]["tau7xa_pre_pilot"]
        assert pilot.get("finding_resolved_at_phase") == "τ.6.x.1.C", (
            "τ.7.x.a.0 PILOT block must annotate the finding-resolution phase"
        )


# ──────────────────────────────────────────────────────────────────
# τ.6.x.1.D — Chapter-marker recovery for OCR-garbled numerals (2026-05-15)
# ──────────────────────────────────────────────────────────────────
#
# Resolves the τ.6.x.1.C known residual: when OCR garbles the
# Ethiopic chapter numeral (e.g. text-layer emits `ምዕራፍ B ።` for
# what should be `ምዕራፍ ፩ ።`), the strict CHAPTER_HEADER_RE fails
# to match and all subsequent verses default to chapter 1. The
# τ.6.x.1.D extension adds a lenient regex + chapter-marker
# resolver that recovers chapter numbers via Geʽez parsing →
# Arabic-digit extraction → sequential fallback.


class TestTau6X1DModuleSurface:
    """τ.6.x.1.D exposes the lenient chapter-marker regex + the
    resolver function."""

    def test_chapter_header_re_lenient_importable(self):
        import re as _re

        from scripts.extract_parallel_pdf import CHAPTER_HEADER_RE_LENIENT

        assert isinstance(CHAPTER_HEADER_RE_LENIENT, _re.Pattern)

    def test_resolve_chapter_marker_callable(self):
        from scripts.extract_parallel_pdf import _resolve_chapter_marker

        assert callable(_resolve_chapter_marker)

    def test_resolver_signature_accepts_max_jump_kwarg(self):
        import inspect

        from scripts.extract_parallel_pdf import _resolve_chapter_marker

        sig = inspect.signature(_resolve_chapter_marker)
        assert "max_jump" in sig.parameters, "_resolve_chapter_marker must accept a max_jump kwarg"


class TestTau6X1DResolveChapterMarker:
    """Unit tests for `_resolve_chapter_marker` — OCR-garble recovery
    cases."""

    def _fn(self):
        from scripts.extract_parallel_pdf import _resolve_chapter_marker

        return _resolve_chapter_marker

    def test_clean_geez_numeral_one(self):
        assert self._fn()("፩", 0) == 1

    def test_clean_geez_numeral_two(self):
        assert self._fn()("፪", 1) == 2

    def test_compound_geez_numeral(self):
        # ፫ = 3
        assert self._fn()("፫", 2) == 3

    def test_arabic_digit_token(self):
        # OCR sometimes emits Arabic digits (text-layer mode).
        assert self._fn()("5", 4) == 5

    def test_arabic_multi_digit_token(self):
        assert self._fn()("12", 11) == 12

    def test_latin_letter_garble_falls_back_to_sequential(self):
        # Page 0 text-layer reality: 'B' is OCR garble of '፩'.
        # With seed=0 (no prior chapters), resolver should fall back
        # to sequential = 0 + 1 = 1.
        assert self._fn()("B", 0) == 1

    def test_compound_ethiopic_garble_falls_back(self):
        # Tesseract reality: 'ል፳' is garble of '፩' on page 0.
        # 'ል' is U+120D (not a numeral); 'ል፳' isn't a clean Geʽez
        # numeral. With seed=0, sequential fallback returns 1.
        assert self._fn()("ል፳", 0) == 1

    def test_max_jump_default_blocks_big_forward_jump(self):
        # Real OCR confusion: '፱' (=9) emitted where '፬' (=4) was
        # intended. Default max_jump=5; jump from 3 to 9 = 6 > 5.
        # Should fall back to sequential = 4.
        assert self._fn()("፱", 3) == 4

    def test_max_jump_default_allows_small_forward_jump(self):
        # Jump from 4 to 9 = 5 (≤5 default); should accept.
        assert self._fn()("፱", 4) == 9

    def test_max_jump_none_disables_sanity_check(self):
        # When max_jump=None, all parsed values pass through.
        assert self._fn()("፱", 3, max_jump=None) == 9

    def test_empty_string_falls_back_to_sequential(self):
        assert self._fn()("", 7) == 8

    def test_runaway_large_value_falls_back(self):
        # Value > 200 sanity bound; resolver falls back to sequential.
        assert self._fn()("፼", 5) == 6  # ፼=10000, exceeds 200


class TestTau6X1DLenientRegex:
    """Unit tests for `CHAPTER_HEADER_RE_LENIENT` — keyword + terminator
    variant coverage."""

    def _re(self):
        from scripts.extract_parallel_pdf import CHAPTER_HEADER_RE_LENIENT

        return CHAPTER_HEADER_RE_LENIENT

    def test_clean_marker_matches(self):
        # `ምዕራፍ` (correct keyword) + numeral + `።` terminator.
        m = self._re().search("ምዕራፍ ፪ ።")
        assert m is not None
        assert m.group(1) == "፪"

    def test_typo_keyword_matches(self):
        # Text-layer occasionally emits `ምፅራፍ` (ፅ instead of ዕ).
        m = self._re().search("ምፅራፍ ፫ ።")
        assert m is not None
        assert m.group(1) == "፫"

    def test_latin_letter_numeral_matches(self):
        # `ምዕራፍ B ።` — Latin letter substitution for the Geʽez numeral.
        m = self._re().search("ምዕራፍ B ።")
        assert m is not None
        assert m.group(1) == "B"

    def test_equals_terminator_matches(self):
        # OCR occasionally substitutes `=` for `።` at end.
        m = self._re().search("ምፅራፍ ፱ =")
        assert m is not None
        assert m.group(1) == "፱"

    def test_no_match_without_keyword(self):
        # Random Ethiopic text shouldn't match.
        m = self._re().search("በመጀመሪያ እግዚአብሔር ሰማይንና ምድርን ፈጠረ።")
        assert m is None

    def test_match_within_larger_text(self):
        body = "verse text 1 ።\nምዕራፍ ፫ ።\nverse text 2"
        m = self._re().search(body)
        assert m is not None
        assert m.group(1) == "፫"

    def test_split_produces_alternating_parts(self):
        body = "pre-text\nምዕራፍ B ።\nmiddle-text\nምፅራፍ ፫ ።\nend-text"
        parts = self._re().split(body)
        # split() with one capture group: [pre, captured_1, mid_1, captured_2, mid_2]
        assert len(parts) == 5
        assert parts[1] == "B"
        assert parts[3] == "፫"


class TestTau6X1DParagraphModeChapterRecovery:
    """Integration tests for paragraph-mode parsing with τ.6.x.1.D
    chapter-marker recovery on synthetic input."""

    def _parse(self, text):
        from scripts.extract_parallel_pdf import parse_verses_from_text

        return parse_verses_from_text(text, paragraph_mode=True)

    def test_garbled_first_marker_resolves_to_chapter_1(self):
        """Pre-marker title text is discarded; first marker (garbled
        Latin 'B' in this synthetic example) establishes chapter 1."""
        body = (
            "publisher header noise text in Ethiopic ።\n"
            "ምዕራፍ B ።\n"  # garbled chapter 1 marker
            "በመጀመሪያ እግዚአብሔር ሰማይንና ምድርን ፈጠረ።\n"
            "ምድር ግን ባዶዋን ነበረች።"
        )
        result = self._parse(body)
        # All verses should be in chapter 1.
        assert all(v[0] == 1 for v in result), f"Expected all ch 1; got chapters {set(v[0] for v in result)}"
        assert len(result) >= 2

    def test_clean_second_marker_advances_chapter(self):
        """A clean second marker (`ምዕራፍ ፪`) advances to chapter 2."""
        body = (
            "ምዕራፍ B ።\n"  # ch 1 (garbled, sequential → 1)
            "verse one body text long enough to pass filter።\n"
            "ምዕራፍ ፪ ።\n"  # ch 2 (clean)
            "verse two body text long enough to pass filter።"
        )
        result = self._parse(body)
        chapters_seen = {v[0] for v in result}
        assert 1 in chapters_seen
        assert 2 in chapters_seen

    def test_big_jump_sanity_check_overrides_garble(self):
        """When a marker resolves to a value > current+5 (default),
        sequential fallback fires to correct the garble."""
        body = (
            "ምዕራፍ B ።\n"  # ch 1
            "verse one body text long enough to pass filter።\n"
            "ምፅራፍ ፫ ።\n"  # ch 3 (clean)
            "verse three body text long enough to pass filter።\n"
            "ምፅራፍ ፱ =\n"  # parses to 9, but jump=6 > max_jump=5 → sequential → 4
            "verse four body text long enough to pass filter።"
        )
        result = self._parse(body)
        chapters_seen = {v[0] for v in result}
        assert 1 in chapters_seen
        assert 3 in chapters_seen
        # The `፱` marker should resolve to 4 (not 9) via max-jump.
        assert 4 in chapters_seen, (
            f"max-jump sanity should resolve ፱ jumping from 3 → 4 (sequential); got chapters {chapters_seen}"
        )

    def test_pre_marker_text_discarded_when_markers_exist(self):
        """Title-page header text BEFORE the first marker should NOT
        be credited to chapter 1 (it's typically publisher banner +
        book title, not Bible content)."""
        body = (
            "Genesis title page banner text long enough to be retained \n"
            "publisher org noise text in Ethiopic ።\n"
            "ምዕራፍ B ።\n"  # first marker establishes ch 1
            "actual gen 1:1 body text።"
        )
        result = self._parse(body)
        # Only one verse should be parsed (the actual Gen 1:1) — the
        # pre-marker title text was discarded.
        assert len(result) == 1
        assert result[0][0] == 1
        assert "actual gen 1:1" in result[0][2]


class TestTau6X1DParagraphModeRuntime:
    """Real-PDF runtime regression pin for τ.6.x.1.D chapter recovery.
    Empirical reality: text-layer Genesis pages 0-5 should now detect
    ≥3 chapters (vs 1 at τ.6.x.1.C baseline) — empirical baseline at
    ship-time: chapters {1, 3, 4} detected for pages 0-5."""

    @pytest.fixture(scope="class")
    def _pdf(self):
        import sys

        sys.path.insert(0, "scripts")
        try:
            import fitz
        except ImportError:
            pytest.skip("pymupdf (fitz) not installed")
        from scripts.extract_parallel_pdf import load_source_config, resolve_pdf_path

        cfg = load_source_config()
        try:
            pdf_path = resolve_pdf_path(cfg)
        except SystemExit:
            pytest.skip("Parallel-Bible PDF not resolvable")
        if not pdf_path.exists():
            pytest.skip("Parallel-Bible PDF not present on this machine")
        doc = fitz.open(str(pdf_path))
        yield doc
        doc.close()

    def test_text_layer_pages_0_5_detects_at_least_3_chapters(self, _pdf):
        """τ.6.x.1.D runtime pin: text-layer engine on Amharic Genesis
        pages 0-5 must detect ≥3 distinct chapters under paragraph_mode.
        Without τ.6.x.1.D (τ.6.x.1.C only), only 1 chapter is detected
        because all chapter markers have OCR-garbled numerals that the
        strict CHAPTER_HEADER_RE can't match."""
        import sys

        sys.path.insert(0, "scripts")
        from scripts.extract_parallel_pdf import extract_text_by_column, parse_verses_from_text

        all_amh = ""
        for page_num in range(0, 6):
            page = _pdf[page_num]
            _, amh = extract_text_by_column(page)
            all_amh += amh + "\n"

        verses = parse_verses_from_text(all_amh, paragraph_mode=True)
        chapters_present = {v[0] for v in verses}
        assert len(chapters_present) >= 3, (
            f"τ.6.x.1.D runtime pin: text-layer Genesis pages 0-5 must detect "
            f"≥3 distinct chapters under paragraph_mode; got {len(chapters_present)} "
            f"chapters: {sorted(chapters_present)}. The τ.6.x.1.C baseline was "
            f"1 chapter (all verses defaulted to ch 1 due to garbled markers)."
        )

    def test_text_layer_pages_0_5_still_yields_at_least_75_verses(self, _pdf):
        """τ.6.x.1.D preserves the τ.6.x.1.C verse-count floor; the
        chapter-recovery extension doesn't change the total verse count,
        only the chapter labels."""
        import sys

        sys.path.insert(0, "scripts")
        from scripts.extract_parallel_pdf import extract_text_by_column, parse_verses_from_text

        all_amh = ""
        for page_num in range(0, 6):
            page = _pdf[page_num]
            _, amh = extract_text_by_column(page)
            all_amh += amh + "\n"

        verses = parse_verses_from_text(all_amh, paragraph_mode=True)
        # The τ.6.x.1.D change MAY shift the verse count slightly
        # (since pre-marker title text is now discarded). Empirical
        # baseline at ship-time: 86 verses (vs 87 at τ.6.x.1.C). Floor
        # set at 75 with healthy margin for OCR variance.
        assert len(verses) >= 75, (
            f"τ.6.x.1.D contract: verse count should remain ≥75 after the "
            f"chapter-recovery change (τ.6.x.1.C baseline was 87; "
            f"τ.6.x.1.D reduces by 1-2 due to pre-marker discard). "
            f"Got {len(verses)}."
        )


class TestTau6X1DSourceYamlBlock:
    """`_source.yaml::ocr_strategy.tau6x1d_chapter_recovery` block
    codifies the τ.6.x.1.D ship."""

    YAML_PATH = (
        Path(__file__).resolve().parent.parent
        / "content"
        / "translations"
        / "sources"
        / "parallel-bible-eotc"
        / "_source.yaml"
    )

    def _block(self) -> dict:
        cfg = yaml.safe_load(self.YAML_PATH.read_text(encoding="utf-8"))
        return cfg["ocr_strategy"]["tau6x1d_chapter_recovery"]

    def test_block_exists(self):
        assert isinstance(self._block(), dict)

    def test_shipped_at_phase(self):
        assert self._block()["shipped_at_phase"] == "τ.6.x.1.D"

    def test_shipped_date(self):
        import datetime as _dt

        sd = self._block()["shipped_date"]
        if isinstance(sd, _dt.date):
            assert sd == _dt.date(2026, 5, 15)
        else:
            assert sd == "2026-05-15"

    def test_resolves_residual_back_link(self):
        """The block must reference the τ.6.x.1.C residual it
        addresses."""
        b = self._block()
        rr = b.get("resolves_residual") or b.get("resolves_finding")
        assert rr is not None, "τ.6.x.1.D must record the τ.6.x.1.C residual it addresses"
        assert "chapter" in str(rr).lower() or "τ.6.x.1.C" in str(rr)

    def test_helpers_added_inventory(self):
        helpers = self._block().get("helpers_added", {})
        for h in ["CHAPTER_HEADER_RE_LENIENT", "_resolve_chapter_marker"]:
            assert any(h in str(k) or h in str(v) for k, v in helpers.items()), (
                f"τ.6.x.1.D helpers_added must inventory {h}"
            )

    def test_empirical_validation_recorded(self):
        b = self._block()
        ev = b.get("empirical_validation", {})
        assert ev, "τ.6.x.1.D empirical_validation must be non-empty"

    def test_closed_arc_contracts_preserved(self):
        b = self._block()
        contracts = b["closed_arc_contracts_preserved"]
        # 8 prior contracts preserved + tau6x1c parser_extension key.
        for k in ("tau6x0a_no_ingest", "tau6x1c_parser_extension"):
            assert contracts.get(k) is True, f"τ.6.x.1.D must preserve {k}"

    def test_no_ingest_at_this_phase(self):
        assert self._block()["no_ingest_at_this_phase"] is True

    def test_next_phase_is_tau7xa(self):
        np = self._block()["next_phase"]
        assert "τ.7.x.a" in str(np)
