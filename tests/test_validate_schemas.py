"""Tests for validate_schemas — extracted from test_scripts.py in ω.27.

Originally lived in tests/test_scripts.py as part of a 22,000-line
monolithic test file; moved here so each test target sits next to a
single source-of-truth scripts/ module. Future tests for the same
target should land in this file rather than test_scripts.py.
"""

from __future__ import annotations


class TestOmega19SchemaValidator:
    """ω.19 — schema validator CLI. Tests the in-house framework
    + per-file specs + aggregate runner."""

    # ---- framework ----

    def test_field_spec_dataclass_shape(self):
        from scripts.validate_schemas import FieldSpec

        f = FieldSpec(name="x", type=str, required=False)
        assert f.name == "x"
        assert f.required is False
        assert f.type is str
        assert f.constraint is None

    def test_validate_record_clean(self):
        from scripts.validate_schemas import (
            FieldSpec,
            RecordSpec,
            validate_record,
        )

        spec = RecordSpec(
            fields=[
                FieldSpec("id", type=str),
                FieldSpec("count", type=int, required=False),
            ]
        )
        errors = validate_record(
            {"id": "foo", "count": 3},
            spec,
            label="rec",
        )
        assert errors == []

    def test_validate_record_missing_required(self):
        from scripts.validate_schemas import (
            FieldSpec,
            RecordSpec,
            validate_record,
        )

        spec = RecordSpec(fields=[FieldSpec("id", type=str)])
        errors = validate_record({}, spec, label="rec")
        assert len(errors) == 1
        assert "missing required field" in errors[0]
        assert "'id'" in errors[0]

    def test_validate_record_wrong_type(self):
        from scripts.validate_schemas import (
            FieldSpec,
            RecordSpec,
            validate_record,
        )

        spec = RecordSpec(fields=[FieldSpec("count", type=int)])
        errors = validate_record({"count": "three"}, spec, label="rec")
        assert len(errors) == 1
        assert "expected int" in errors[0]
        assert "got str" in errors[0]

    def test_validate_record_optional_none_passes(self):
        # Required-False fields with None values pass (the YAML
        # explicitly null'd them).
        from scripts.validate_schemas import (
            FieldSpec,
            RecordSpec,
            validate_record,
        )

        spec = RecordSpec(fields=[FieldSpec("note", type=str, required=False)])
        errors = validate_record({"note": None}, spec, label="rec")
        assert errors == []

    def test_validate_record_list_item_type(self):
        from scripts.validate_schemas import (
            FieldSpec,
            RecordSpec,
            validate_record,
        )

        spec = RecordSpec(
            fields=[
                FieldSpec("tags", type=list, item_type=str),
            ]
        )
        errors = validate_record(
            {"tags": ["a", 5, "b"]},
            spec,
            label="rec",
        )
        assert any("tags'[1]" in e for e in errors)
        assert any("expected str" in e for e in errors)

    def test_validate_record_constraint(self):
        from scripts.validate_schemas import (
            FieldSpec,
            RecordSpec,
            validate_record,
        )

        spec = RecordSpec(
            fields=[
                FieldSpec(
                    "n",
                    type=int,
                    constraint=lambda v: v > 0,
                    constraint_message="must be positive",
                ),
            ]
        )
        errors = validate_record({"n": -3}, spec, label="rec")
        assert len(errors) == 1
        assert "must be positive" in errors[0]

    def test_validate_record_strict_unknown(self):
        # Default: unknown fields pass silently. strict_unknown=True
        # flips to error.
        from scripts.validate_schemas import (
            FieldSpec,
            RecordSpec,
            validate_record,
        )

        permissive = RecordSpec(fields=[FieldSpec("id", type=str)])
        assert (
            validate_record(
                {"id": "x", "extra": 1},
                permissive,
                label="rec",
            )
            == []
        )
        strict = RecordSpec(
            fields=[FieldSpec("id", type=str)],
            strict_unknown=True,
        )
        errors = validate_record(
            {"id": "x", "extra": 1},
            strict,
            label="rec",
        )
        assert any("unknown fields" in e for e in errors)

    def test_validate_record_label_prefixes_errors(self):
        # Every error string is prefixed with the label so callers
        # can build "<file>:<id>: <error>" diagnostics.
        from scripts.validate_schemas import (
            FieldSpec,
            RecordSpec,
            validate_record,
        )

        spec = RecordSpec(fields=[FieldSpec("id", type=str)])
        errors = validate_record({}, spec, label="MY_LABEL")
        assert errors[0].startswith("MY_LABEL: ")

    def test_validate_non_dict_record_returns_error(self):
        from scripts.validate_schemas import (
            FieldSpec,
            RecordSpec,
            validate_record,
        )

        spec = RecordSpec(fields=[FieldSpec("id", type=str)])
        errors = validate_record("not a dict", spec, label="rec")
        assert len(errors) == 1
        assert "must be a dict" in errors[0]

    # ---- per-file specs ----

    def test_validate_editions_passes_on_real_file(self):
        from scripts.validate_schemas import validate_editions

        result = validate_editions()
        assert result["status"] == "ok", f"editions.yaml unexpected violations: {result['errors']}"
        # 7 tradition wizard SKUs + 2 standalone Bibles (hidden from wizard).
        assert result["record_count"] == 9

    def test_validate_kinds_passes_on_real_file(self):
        from scripts.validate_schemas import validate_kinds

        result = validate_kinds()
        assert result["status"] == "ok", f"kinds.yaml unexpected violations: {result['errors']}"
        # 66 → 67 with χ-AI-notes (2026-05-10): added `comm-ai` kind.
        # 67 → 68 with χ.2 SEED (2026-05-12): added `comm-protestant` kind
        # (sibling of comm-reformation; post-Reformation English
        # Nonconformist / Puritan / Evangelical, e.g. Matthew Henry).
        # 68 → 70 with δ.1.0 (2026-05-14): added `text-geez-revision`
        # ([GZ] label, Phase-4 page-image-tier1 fresh English rendering)
        # + `compare-divergence-geez` (Geʽez divergence apparatus
        # inline-popup content-class commentary). The Π.1 audit caught
        # this floor was not bumped at δ.1.0 ship and corrected it here.
        # 70 → 71 with the Easton's Bible Dictionary ingest (2026-05-21):
        # added `dict-easton` (category `hist`, ⌂ glyph).
        # 71 → 72 with Track C Torrey (2026-05-25): added `topic-torrey`
        # (category `topic`, ✦ glyph — Torrey's New Topical Textbook, net-new
        # vs Nave's).
        assert result["record_count"] == 68

    def test_validate_categories_passes(self):
        from scripts.validate_schemas import validate_categories

        result = validate_categories()
        assert result["status"] == "ok"
        assert result["record_count"] == 15

    def test_validate_books_passes(self):
        from scripts.validate_schemas import validate_books

        result = validate_books()
        assert result["status"] == "ok"
        assert result["record_count"] == 87

    def test_validate_canons_passes(self):
        from scripts.validate_schemas import validate_canons

        result = validate_canons()
        assert result["status"] == "ok"
        assert result["record_count"] >= 4

    # ---- aggregate runner ----

    def test_run_all_clean(self):
        from scripts.validate_schemas import run_all

        result = run_all()
        assert result["status"] == "ok"
        # 5 per-file validators + cross-refs added in ω.19.1.
        assert result["summary"]["total"] == 6
        assert result["summary"]["clean"] is True
        assert result["summary"]["fail"] == 0
        assert result["summary"]["error"] == 0

    def test_run_all_filtered(self):
        from scripts.validate_schemas import run_all

        result = run_all(only="kinds")
        assert result["status"] == "ok"
        assert result["summary"]["total"] == 1
        assert result["files"][0]["file"] == "kinds.yaml"

    def test_run_all_unknown_filter(self):
        from scripts.validate_schemas import run_all

        result = run_all(only="not-a-real-file")
        assert result["status"] == "error"
        assert result["code"] == "unknown_file"

    # ---- CLI ----

    def test_main_clean_returns_0(self, capsys):
        from scripts.validate_schemas import main

        rc = main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "CLEAN" in out

    def test_main_json_output(self, capsys):
        from scripts.validate_schemas import main

        rc = main(["--json"])
        assert rc == 0
        out = capsys.readouterr().out
        import json as _json

        data = _json.loads(out)
        assert data["status"] == "ok"
        assert "summary" in data

    def test_main_filtered_to_one_file(self, capsys):
        from scripts.validate_schemas import main

        rc = main(["--file", "books"])
        assert rc == 0

    # ---- doc presence ----

    def test_schemas_md_present(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        assert (repo / "dev" / "SCHEMAS.md").is_file()

    def test_schemas_md_documents_every_validator(self):
        from pathlib import Path
        from scripts.validate_schemas import _VALIDATORS

        repo = Path(__file__).resolve().parent.parent
        text = (repo / "dev" / "SCHEMAS.md").read_text(encoding="utf-8")
        # Per-file validators are referenced as `<name>.yaml`;
        # virtual validators (no on-disk file, e.g. cross-refs)
        # are referenced by their key.
        virtual = {"cross-refs"}
        for name in _VALIDATORS:
            needle = name if name in virtual else f"{name}.yaml"
            assert needle in text, f"SCHEMAS.md missing entry for {needle}"


class TestOmega191SchemaFollowOn:
    """ω.19.1 — schema validator follow-on. Two pieces:
    (1) `_parse_value` recognises bare ``[]`` as an empty list so
        round-tripped editions.yaml doesn't carry the literal
        string ``"[]"`` forward;
    (2) ``validate_cross_refs()`` walks editions / kinds / canons /
        categories / reading_plans and surfaces dangling references.
    """

    # ---- (1) parse_value empty-list fix ----

    def test_parse_value_bare_empty_list(self):
        from scripts.core.config import _parse_value

        result = _parse_value("[]")
        assert result == []
        assert isinstance(result, list)

    def test_parse_value_bare_empty_list_with_whitespace(self):
        from scripts.core.config import _parse_value

        assert _parse_value("  []  ") == []

    def test_parse_yaml_records_empty_list_round_trip(self):
        # The on-disk editions.yaml uses bare `[]` for an opted-out
        # reading-plans field; the parser must hand back an empty
        # list (not the literal string "[]") so downstream consumers
        # don't blow up on `for x in "[]"`.
        from scripts.core.config import _parse_yaml_records

        text = 'editions:\n  - id: x\n    title: "X"\n    enabled_reading_plans: []\n'
        records = _parse_yaml_records(text)
        assert len(records) == 1
        assert records[0]["enabled_reading_plans"] == []
        assert isinstance(records[0]["enabled_reading_plans"], list)

    # ---- (2) cross-refs validator ----

    def test_validate_cross_refs_passes_on_real_data(self):
        # Production data must round-trip clean — editions.yaml's
        # canons / categories / kinds / reading-plan ids all resolve
        # in their target files. If this fails, the project's data
        # has drifted; a real fix lives in the data, not the test.
        from scripts.validate_schemas import validate_cross_refs

        result = validate_cross_refs()
        assert result["status"] == "ok", f"unexpected cross-ref violations: {result['errors']}"

    def test_cross_refs_registered_in_validators(self):
        from scripts.validate_schemas import _VALIDATORS, validate_cross_refs

        assert "cross-refs" in _VALIDATORS
        assert _VALIDATORS["cross-refs"] is validate_cross_refs

    def test_cross_refs_runs_via_run_all(self):
        from scripts.validate_schemas import run_all

        result = run_all(only="cross-refs")
        assert result["status"] == "ok"
        assert result["summary"]["total"] == 1
        assert result["files"][0]["file"] == "<cross-refs>"

    def test_cross_refs_detects_bogus_canon(self, monkeypatch):
        from scripts.validate_schemas import validate_cross_refs
        from scripts.core import config as _config

        def fake_editions():
            return [
                {"id": "fake-ed", "title": "X", "canon": "no-such-canon"},
            ]

        monkeypatch.setattr(_config, "load_editions", fake_editions)
        result = validate_cross_refs()
        assert result["status"] == "fail"
        assert any("no-such-canon" in e and "canons.yaml" in e for e in result["errors"]), result["errors"]

    def test_cross_refs_detects_bogus_enabled_categories(self, monkeypatch):
        from scripts.validate_schemas import validate_cross_refs
        from scripts.core import config as _config

        def fake_editions():
            return [
                {"id": "fake-ed", "title": "X", "canon": "ethiopian", "enabled_categories": ["real-but-fake-cat"]},
            ]

        monkeypatch.setattr(_config, "load_editions", fake_editions)
        result = validate_cross_refs()
        assert result["status"] == "fail"
        assert any("real-but-fake-cat" in e and "categories.yaml" in e for e in result["errors"]), result["errors"]

    def test_cross_refs_detects_bogus_enabled_kinds(self, monkeypatch):
        from scripts.validate_schemas import validate_cross_refs
        from scripts.core import config as _config

        def fake_editions():
            return [
                {"id": "fake-ed", "title": "X", "canon": "ethiopian", "enabled_kinds": ["zzz-not-a-real-kind"]},
            ]

        monkeypatch.setattr(_config, "load_editions", fake_editions)
        result = validate_cross_refs()
        assert result["status"] == "fail"
        assert any("zzz-not-a-real-kind" in e and "kinds.yaml" in e for e in result["errors"]), result["errors"]

    def test_cross_refs_detects_bogus_disabled_kinds(self, monkeypatch):
        from scripts.validate_schemas import validate_cross_refs
        from scripts.core import config as _config

        def fake_editions():
            return [
                {"id": "fake-ed", "title": "X", "canon": "ethiopian", "disabled_kinds": ["zzz-bogus-disabled"]},
            ]

        monkeypatch.setattr(_config, "load_editions", fake_editions)
        result = validate_cross_refs()
        assert result["status"] == "fail"
        assert any("zzz-bogus-disabled" in e and "kinds.yaml" in e for e in result["errors"]), result["errors"]

    def test_cross_refs_detects_bogus_reading_plan(self, monkeypatch):
        from scripts.validate_schemas import validate_cross_refs
        from scripts.core import config as _config

        def fake_editions():
            return [
                {"id": "fake-ed", "title": "X", "canon": "ethiopian", "enabled_reading_plans": ["no-such-plan-1234"]},
            ]

        monkeypatch.setattr(_config, "load_editions", fake_editions)
        result = validate_cross_refs()
        assert result["status"] == "fail"
        assert any("no-such-plan-1234" in e and "reading_plans" in e for e in result["errors"]), result["errors"]

    def test_cross_refs_detects_bogus_kind_category(self, monkeypatch):
        from scripts.validate_schemas import validate_cross_refs
        from scripts.core import config as _config

        def fake_kinds():
            return [
                {"code": "fake-kind", "category": "no-such-category", "label": "X", "symbol": "?"},
            ]

        monkeypatch.setattr(_config, "load_kinds", fake_kinds)
        result = validate_cross_refs()
        assert result["status"] == "fail"
        assert any("no-such-category" in e and "fake-kind" in e for e in result["errors"]), result["errors"]

    def test_cross_refs_skips_non_string_field_values(self, monkeypatch):
        # If a field is the wrong shape (e.g. dict where list is
        # expected), the per-file validator catches it. cross-refs
        # must not double-report or crash.
        from scripts.validate_schemas import validate_cross_refs
        from scripts.core import config as _config

        def fake_editions():
            return [
                {"id": "fake-ed", "title": "X", "canon": "ethiopian", "enabled_kinds": "not-a-list"},
            ]

        monkeypatch.setattr(_config, "load_editions", fake_editions)
        result = validate_cross_refs()
        # No cross-ref violation surfaced (per-file spec owns this).
        assert all("enabled_kinds" not in e for e in result["errors"])

    # ---- doc presence ----

    def test_schemas_md_documents_cross_refs(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        text = (repo / "dev" / "SCHEMAS.md").read_text(encoding="utf-8")
        assert "cross-refs" in text
        assert "validate_cross_refs" in text


class TestOmega192SchemaPreflight:
    """ω.19.2 — schema validator preflight composition + strict-
    unknown CLI flag. Closes the third ω.19 follow-on item. The
    goal is Tier-3 surface parity with the rules linter: schema
    drift surfaces in the readiness dashboard the moment it
    appears, not at the next manual run.
    """

    # ---- preflight composition ----

    def test_preflight_includes_schema_compliance(self):
        from scripts.web import _compute_preflight_uncached

        result = _compute_preflight_uncached()
        ids = [c["id"] for c in result["checks"]]
        assert "schema_compliance" in ids

    def test_schema_compliance_pass_on_clean_state(self):
        from scripts.web import _compute_preflight_uncached

        result = _compute_preflight_uncached()
        sc = next(c for c in result["checks"] if c["id"] == "schema_compliance")
        assert sc["status"] == "pass", f"unexpected schema_compliance status: {sc}"
        assert "validated YAML" in sc["message"]
        # On clean state, no failing-file details are surfaced.
        assert sc["details"] == []

    def test_schema_compliance_jump_to_preflight(self):
        # The check is code-level; jump_to should be /preflight,
        # consistent with rules_compliance.
        from scripts.web import _compute_preflight_uncached

        result = _compute_preflight_uncached()
        sc = next(c for c in result["checks"] if c["id"] == "schema_compliance")
        assert sc["jump_to"] == "/preflight"

    def test_schema_compliance_degrades_to_warn_on_validator_blow_up(
        self,
        monkeypatch,
    ):
        # If validate_schemas explodes, the dashboard must still
        # render — degrade to 'warn' with the reason in the message.
        # Mirrors the rules_compliance try/except shape.
        import scripts.validate_schemas as vs
        from scripts.web import _compute_preflight_uncached

        def boom(**kw):
            raise RuntimeError("synthetic explosion")

        monkeypatch.setattr(vs, "run_all", boom)
        result = _compute_preflight_uncached()
        sc = next(c for c in result["checks"] if c["id"] == "schema_compliance")
        assert sc["status"] == "warn"
        assert "synthetic explosion" in sc["message"]

    def test_schema_compliance_surfaces_failures(self, monkeypatch):
        # When the validator reports a failure, preflight should
        # surface it as 'fail' with the failing files in details.
        import scripts.validate_schemas as vs
        from scripts.web import _compute_preflight_uncached

        def fake_run_all(**kw):
            return {
                "status": "ok",
                "files": [
                    {
                        "file": "editions.yaml",
                        "status": "fail",
                        "errors": ["editions.yaml[fake-ed]: missing 'id'"],
                        "record_count": 9,
                    },
                    {"file": "kinds.yaml", "status": "ok", "errors": [], "record_count": 66},
                ],
                "summary": {"total": 2, "ok": 1, "fail": 1, "error": 0, "clean": False},
            }

        monkeypatch.setattr(vs, "run_all", fake_run_all)
        result = _compute_preflight_uncached()
        sc = next(c for c in result["checks"] if c["id"] == "schema_compliance")
        assert sc["status"] == "fail"
        # Failing file appears in details; passing file does not.
        files_in_details = {d["file"] for d in sc["details"]}
        assert "editions.yaml" in files_in_details
        assert "kinds.yaml" not in files_in_details

    # ---- --strict-unknown flag ----

    def test_run_all_accepts_strict_unknown_kwarg(self):
        from scripts.validate_schemas import run_all

        # Default off: production data is clean.
        result = run_all(strict_unknown=False)
        assert result["status"] == "ok"
        assert result["summary"]["clean"] is True

    def test_strict_unknown_flips_spec(self, monkeypatch):
        # Inject a record with an unknown field; with strict off,
        # it passes; with strict on, it fails.
        from scripts.validate_schemas import (
            FieldSpec,
            RecordSpec,
            _validate_record_list,
        )

        spec = RecordSpec(fields=[FieldSpec("id", type=str)])
        records = [{"id": "x", "transitional_field": 1}]

        permissive = _validate_record_list(
            records,
            spec,
            file_label="probe.yaml",
            strict_unknown=False,
        )
        assert permissive == []

        strict = _validate_record_list(
            records,
            spec,
            file_label="probe.yaml",
            strict_unknown=True,
        )
        assert any("transitional_field" in e for e in strict)

    def test_validate_editions_strict_unknown_kwarg(self):
        # The per-file validator passes the flag through. Real
        # production data still passes today (no unknown fields).
        from scripts.validate_schemas import validate_editions

        assert validate_editions(strict_unknown=True)["status"] == "ok"

    def test_run_all_threads_strict_unknown_to_validators(
        self,
        monkeypatch,
    ):
        # Capture the kwargs each validator is called with.
        seen: dict[str, bool] = {}
        from scripts import validate_schemas as vs

        def make_probe(name):
            def probe(**kw):
                seen[name] = kw.get("strict_unknown", False)
                return {"file": f"{name}.yaml", "status": "ok", "errors": [], "record_count": 0}

            return probe

        monkeypatch.setattr(
            vs,
            "_VALIDATORS",
            {"foo": make_probe("foo"), "bar": make_probe("bar")},
        )
        vs.run_all(strict_unknown=True)
        assert seen == {"foo": True, "bar": True}

    def test_main_strict_unknown_flag(self, capsys):
        from scripts.validate_schemas import main

        rc = main(["--strict-unknown"])
        assert rc == 0
        # Production data has no unknown fields, so a strict-unknown
        # run still exits clean today. The flag's plumbing is the
        # contract; the runtime verdict can shift later.
        out = capsys.readouterr().out
        assert "CLEAN" in out

    def test_validate_canons_accepts_strict_unknown_kwarg(self):
        # canons + cross-refs accept the kwarg for signature
        # uniformity even though they don't use it.
        from scripts.validate_schemas import (
            validate_canons,
            validate_cross_refs,
        )

        assert validate_canons(strict_unknown=True)["status"] == "ok"
        assert validate_cross_refs(strict_unknown=True)["status"] == "ok"

    # ---- doc presence ----

    def test_schemas_md_documents_preflight_composition(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        text = (repo / "dev" / "SCHEMAS.md").read_text(encoding="utf-8")
        assert "preflight" in text.lower()
        assert "strict-unknown" in text or "strict_unknown" in text
