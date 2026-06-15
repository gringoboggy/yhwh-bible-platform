#!/usr/bin/env python3
"""ω.19 — schema validator CLI.

Single-pass validation for every project YAML against an explicit
schema. Catches the "hand-edit broke the build" class of drift
continuously — typo'd field names, wrong-type values, missing
required fields, malformed sub-lists.

Usage::

    python scripts/validate_schemas.py
    python scripts/validate_schemas.py --json
    python scripts/validate_schemas.py --file editions

Per CLAUDE_PROJECT_RULES §10 "Standard library only on the
backend": no Pydantic. The tiny in-house framework
(`FieldSpec`, `RecordSpec`, `validate_record`) is ~50 lines and
covers what we need without introducing a runtime dep.

Exit codes:
  0 — every checked file passes
  1 — at least one file has a violation
  2 — internal error (file unreadable, parser unavailable)

Composes with `scripts/recover.py:verify_yaml` (which checks the
project's custom `_parse_yaml_records` parser); this one validates
SEMANTICS (field types, required fields, enum membership) on top
of structure.
"""

from __future__ import annotations

import argparse
import builtins
import dataclasses
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from collections.abc import Callable


_REPO = Path(__file__).resolve().parent.parent
_CONTENT = _REPO / "content"

# Ensure `scripts.core.config` is importable when this script runs as
# a CLI (e.g. `python scripts/validate_schemas.py`). Without this,
# Python's auto-prepend of the script's parent (`scripts/`) shadows
# the `scripts` package import we need.
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.core import config  # noqa: E402


# ----------------------------------------------------------------------
# Tiny in-house schema framework
# ----------------------------------------------------------------------


@dataclass
class FieldSpec:
    """Spec for one field in a record.

    Attributes:
        name: field name in the YAML record
        required: True = missing → error; False = absent is OK
        type: expected type or tuple of types
        item_type: when ``type`` includes ``list``, every item must
            also match this type
        constraint: optional callable(value) → bool; failing returns
            an error with ``constraint_message``
        constraint_message: human-readable explanation of the
            constraint (e.g. "must be a non-empty string",
            "must be one of: a, b, c")
    """

    name: str
    required: bool = True
    # NB: the field is named `type`, which shadows the builtin within the class
    # body — annotate via `builtins.type` so the annotations on this and the next
    # line resolve to the builtin, not to this field (round-5 audit: cleared 2
    # mypy `valid-type`/`attr-defined` errors that were invisible to the gate).
    type: builtins.type | tuple[builtins.type, ...] = str
    item_type: builtins.type | None = None
    constraint: Callable[[Any], bool] | None = None
    constraint_message: str = ""


@dataclass
class RecordSpec:
    """Spec for a record (dict). Lists every expected field.

    Unknown fields are NOT errors by default — the project's YAML
    files often carry transitional / experimental keys that older
    code paths still write. Pass ``strict_unknown=True`` for the
    rare callers that DO want unknown-field rejection.
    """

    fields: list[FieldSpec] = field(default_factory=list)
    strict_unknown: bool = False


def validate_record(
    record: dict,
    spec: RecordSpec,
    *,
    label: str = "",
) -> list[str]:
    """Validate one record against `spec`. Returns a list of error
    strings; empty list means clean.

    Each error includes the record's ``label`` (e.g. its ``id`` or
    ``code``) so the caller can build "<file>:<id>: missing field"
    diagnostics without re-threading context.
    """
    errors: list[str] = []
    if not isinstance(record, dict):
        errors.append(f"{label}: record must be a dict, got {type(record).__name__}")
        return errors

    seen_fields: set[str] = set()
    for fs in spec.fields:
        seen_fields.add(fs.name)
        if fs.name not in record:
            if fs.required:
                errors.append(f"{label}: missing required field {fs.name!r}")
            continue
        v = record[fs.name]
        # Type check. Allow None for non-required fields whose value
        # is explicitly null in the YAML.
        if v is None and not fs.required:
            continue
        expected_types = fs.type if isinstance(fs.type, tuple) else (fs.type,)
        if not isinstance(v, expected_types):
            type_names = ", ".join(t.__name__ for t in expected_types)
            errors.append(f"{label}: field {fs.name!r} expected {type_names}, got {type(v).__name__}")
            continue
        # Item-type check for lists.
        if fs.item_type and isinstance(v, list):
            for i, item in enumerate(v):
                if not isinstance(item, fs.item_type):
                    errors.append(
                        f"{label}: field {fs.name!r}[{i}] expected {fs.item_type.__name__}, got {type(item).__name__}"
                    )
        # Custom constraint.
        if fs.constraint and not fs.constraint(v):
            msg = fs.constraint_message or "constraint failed"
            errors.append(f"{label}: field {fs.name!r}: {msg}")

    if spec.strict_unknown:
        unknown = set(record.keys()) - seen_fields
        if unknown:
            errors.append(f"{label}: unknown fields not in spec: {sorted(unknown)}")
    return errors


# ----------------------------------------------------------------------
# Per-file specs
# ----------------------------------------------------------------------


def _is_nonempty_string(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


_PHASE_VALUES = config.VALID_PHASES  # C2.phase4: single source of truth (see config.py)

EDITIONS_SPEC = RecordSpec(
    fields=[
        FieldSpec("id", type=str, constraint=_is_nonempty_string, constraint_message="must be a non-empty string"),
        FieldSpec("canon", type=str, required=False),
        FieldSpec("title", type=str, required=False),
        FieldSpec("short_title", type=str, required=False),
        # σ.2 (2026-06-04) — cover identity. ``display_name`` is the builder's
        # short edition name, used as the cover subtitle beneath "HOLY BIBLE"
        # (and the Your-Edition page heading in σ.3); ``cover_main_title``
        # overrides the default "HOLY BIBLE" main line. Both optional / back-compat.
        FieldSpec("display_name", type=str, required=False),
        FieldSpec("cover_main_title", type=str, required=False),
        # The factory cover-template stem chosen for this edition (§4.6 picker),
        # persisted by api_apply_cover_template / api_save_edition_meta.
        FieldSpec("cover_template", type=str, required=False),
        FieldSpec("target_audience", type=str, required=False),
        FieldSpec("notes", type=str, required=False),
        # K-R2-8 (2026-06-10): per-edition e-reader LIBRARY-CARD synopsis —
        # patch_opf writes it into the OPF <dc:description> (eth declares one).
        FieldSpec("description", type=str, required=False),
        FieldSpec(
            "max_phase",
            type=str,
            required=False,
            constraint=lambda v: v in _PHASE_VALUES,
            constraint_message=f"must be one of: {sorted(_PHASE_VALUES)}",
        ),
        FieldSpec("enabled_categories", required=False, type=list, item_type=str),
        FieldSpec("enabled_kinds", required=False, type=list, item_type=str),
        FieldSpec("disabled_kinds", required=False, type=list, item_type=str),
        FieldSpec("enabled_reading_plans", required=False, type=list, item_type=str),
        FieldSpec("popup_languages_default", required=False, type=list, item_type=str),
        FieldSpec("popup_languages_per_book", required=False, type=list, item_type=str),
        FieldSpec("traditions_default", required=False, type=list, item_type=str),
        FieldSpec("traditions_per_book", required=False, type=list, item_type=str),
        FieldSpec("book_covers", required=False, type=list, item_type=str),
        FieldSpec("cover_image", type=str, required=False),
        FieldSpec("cover_credit", type=str, required=False),
        FieldSpec("source_text_credit", type=str, required=False),
        FieldSpec("publisher_name", type=str, required=False),
        FieldSpec("publisher_url", type=str, required=False),
        FieldSpec("authors", required=False, type=list, item_type=str),
        FieldSpec("bisac_codes", required=False, type=list, item_type=str),
        FieldSpec("language_code", type=str, required=False),
        FieldSpec("theme", type=str, required=False),
        FieldSpec("popup_translation", type=str, required=False),
        FieldSpec("time_filter_ceiling", type=int, required=False),
        FieldSpec("verse_popups", type=bool, required=False),
        FieldSpec("verse_marker_glyph", type=str, required=False),
        FieldSpec("chapter_number_format", type=str, required=False),
        FieldSpec("chapter_number_decoration", type=str, required=False),
        FieldSpec("book_toc_ornament", type=str, required=False),
        FieldSpec("reader_toc_collapsible", type=bool, required=False),
        FieldSpec("reader_toc_default_open", type=bool, required=False),
        FieldSpec("reader_toc_books_only", type=bool, required=False),
        # K-R2 (2026-06-09) — the wizard's reader-target pick ("everywhere" |
        # "eink" | "tablet" | "computer"); gates which optional features the
        # UIs offer. Absent = everywhere.
        FieldSpec("target_reader", type=str, required=False),
        # K-R2-6 — option-gated closing colophon (absent/true = keep the minimal
        # traditional last page; false = drop it entirely).
        FieldSpec("closing_colophon", type=bool, required=False),
        # τ.G.constitution.a (2026-05-20) — standalone-Bible fields.
        # Per CLAUDE_PROJECT_RULES §1 "Parallel-Bible end-state — two
        # standalone Bibles", standalone-geez + standalone-amharic
        # carry full scripture text in their base_translation slot
        # (instead of using the English editorial baseline). The
        # standalone:true flag lets the build pipeline branch on the
        # standalone flow vs. the multi-tradition notes-filter flow.
        FieldSpec("standalone", type=bool, required=False),
        FieldSpec("base_translation", type=str, required=False),
        # note-rehaul S1/S2/S3a flags (2026-06-09, flipped True on eth at the
        # STAGE-C re-baseline) — were wired through web_editions/api/customize
        # but never given FieldSpecs, so strict_unknown flagged them.
        FieldSpec("note_attribution_dedup", type=bool, required=False),
        FieldSpec("note_group_by_category", type=bool, required=False),
        FieldSpec("note_topic_dedup", type=bool, required=False),
        # K-R7-3 — eink/Kobo verse layout: one verse per line vs flowing prose.
        FieldSpec("reader_eink_verse_lines", type=bool, required=False),
        FieldSpec("reader_eink_study_inline", type=bool, required=False),
        FieldSpec("reader_eink_study_layout", type=str, required=False),
        # K-R6-6 / K-R7-8 — in-page study-badge glyph (chip, dagger+count, …).
        FieldSpec("marker_badge_style", type=str, required=False),
    ]
)

KINDS_SPEC = RecordSpec(
    fields=[
        FieldSpec("code", type=str, constraint=_is_nonempty_string, constraint_message="must be a non-empty string"),
        FieldSpec("category", type=str),
        FieldSpec("label", type=str, required=False),
        FieldSpec("symbol", type=str, required=False),
        FieldSpec("description", type=str, required=False),
        FieldSpec(
            "phase",
            type=str,
            required=False,
            constraint=lambda v: v in _PHASE_VALUES,
            constraint_message=f"must be one of: {sorted(_PHASE_VALUES)}",
        ),
        FieldSpec("marker_class", type=str, required=False),
        FieldSpec("note_class", type=str, required=False),
        FieldSpec("title_attr", type=str, required=False),
    ]
)

CATEGORIES_SPEC = RecordSpec(
    fields=[
        FieldSpec("id", type=str, constraint=_is_nonempty_string, constraint_message="must be a non-empty string"),
        FieldSpec("label", type=str),
        FieldSpec("symbol", type=str, required=False),
        FieldSpec(
            "sort_order",
            type=int,
            required=False,
            constraint=lambda v: v >= 0,
            constraint_message="must be a non-negative integer",
        ),
        FieldSpec("description", type=str, required=False),
    ]
)

BOOKS_SPEC = RecordSpec(
    fields=[
        FieldSpec("code", type=str, constraint=_is_nonempty_string, constraint_message="must be a non-empty string"),
        FieldSpec("title", type=str),
        FieldSpec(
            "ch_count",
            type=int,
            required=False,
            constraint=lambda v: v >= 0,
            constraint_message="must be a non-negative integer",
        ),
        FieldSpec("section", type=str, required=False),
        FieldSpec("abbrev", type=str, required=False),
        FieldSpec("bp", type=str, required=False),
        FieldSpec("bxx", type=str, required=False),
        FieldSpec("id_prefix", type=str, required=False),
        FieldSpec("next_bp", type=str, required=False),
        FieldSpec("strategy", type=str, required=False),
        FieldSpec("files", type=list, required=False, item_type=str),
    ]
)


# ----------------------------------------------------------------------
# Per-file validation orchestrators
# ----------------------------------------------------------------------


def _records_from_yaml(path: Path) -> tuple[list[dict], str | None]:
    """Parse a project YAML via the custom `_parse_yaml_records` and
    return ``(records, error_or_none)``. Returns ``([], <msg>)`` on
    parse failure so the caller can roll up the error into the
    aggregate report."""
    if not path.is_file():
        return [], f"file not found: {path}"
    try:
        from scripts.core import config

        records = config._parse_yaml_records(path.read_text(encoding="utf-8"))
    except Exception as e:
        return [], f"parse failed: {type(e).__name__}: {e}"
    if not isinstance(records, list):
        return [], "parser did not return a list of records"
    return records, None


def _records_from_pyyaml(path: Path) -> tuple[Any, str | None]:
    """Parse a YAML file via PyYAML (for files like canons.yaml that
    use a different shape than _parse_yaml_records expects)."""
    if not path.is_file():
        return None, f"file not found: {path}"
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:
        return None, f"parse failed: {type(e).__name__}: {e}"
    return data, None


def _validate_record_list(
    records: list[dict],
    spec: RecordSpec,
    *,
    file_label: str,
    label_field: str = "id",
    strict_unknown: bool = False,
) -> list[str]:
    if strict_unknown and not spec.strict_unknown:
        spec = dataclasses.replace(spec, strict_unknown=True)
    errors: list[str] = []
    for i, rec in enumerate(records):
        record_label = (rec.get(label_field) if isinstance(rec, dict) else None) or f"#{i}"
        rec_label = f"{file_label}[{record_label}]"
        errors.extend(validate_record(rec, spec, label=rec_label))
    return errors


def validate_editions(*, strict_unknown: bool = False) -> dict:
    records, err = _records_from_yaml(_CONTENT / "editions.yaml")
    if err:
        return {"file": "editions.yaml", "status": "error", "errors": [err], "record_count": 0}
    errors = _validate_record_list(
        records,
        EDITIONS_SPEC,
        file_label="editions.yaml",
        strict_unknown=strict_unknown,
    )
    return {
        "file": "editions.yaml",
        "status": "ok" if not errors else "fail",
        "errors": errors,
        "record_count": len(records),
    }


def validate_kinds(*, strict_unknown: bool = False) -> dict:
    records, err = _records_from_yaml(_CONTENT / "kinds.yaml")
    if err:
        return {"file": "kinds.yaml", "status": "error", "errors": [err], "record_count": 0}
    errors = _validate_record_list(
        records,
        KINDS_SPEC,
        file_label="kinds.yaml",
        label_field="code",
        strict_unknown=strict_unknown,
    )
    return {
        "file": "kinds.yaml",
        "status": "ok" if not errors else "fail",
        "errors": errors,
        "record_count": len(records),
    }


def validate_categories(*, strict_unknown: bool = False) -> dict:
    records, err = _records_from_yaml(_CONTENT / "categories.yaml")
    if err:
        return {"file": "categories.yaml", "status": "error", "errors": [err], "record_count": 0}
    errors = _validate_record_list(
        records,
        CATEGORIES_SPEC,
        file_label="categories.yaml",
        strict_unknown=strict_unknown,
    )
    return {
        "file": "categories.yaml",
        "status": "ok" if not errors else "fail",
        "errors": errors,
        "record_count": len(records),
    }


def validate_books(*, strict_unknown: bool = False) -> dict:
    records, err = _records_from_yaml(_CONTENT / "books.yaml")
    if err:
        return {"file": "books.yaml", "status": "error", "errors": [err], "record_count": 0}
    errors = _validate_record_list(
        records,
        BOOKS_SPEC,
        file_label="books.yaml",
        label_field="code",
        strict_unknown=strict_unknown,
    )
    return {
        "file": "books.yaml",
        "status": "ok" if not errors else "fail",
        "errors": errors,
        "record_count": len(records),
    }


def validate_cross_refs(*, strict_unknown: bool = False) -> dict:
    """ω.19.1 — cross-file referential integrity.

    The ``strict_unknown`` kwarg is accepted for signature uniformity
    with the per-file validators (run_all dispatches identically) but
    is unused here — cross-refs has no per-record spec to flip.

    Catches the drift class where a field references an id that
    doesn't exist in its target file. Each in-scope file is
    validated in isolation by the per-file specs above; this
    runs AFTER and only inspects ids.

    Coverage:
    - editions.yaml `canon` → must exist in canons.yaml
    - editions.yaml `enabled_categories[*]` → must exist in
      categories.yaml
    - editions.yaml `enabled_kinds[*]` / `disabled_kinds[*]` →
      must exist in kinds.yaml
    - kinds.yaml `category` → must exist in categories.yaml
    - editions.yaml `enabled_reading_plans[*]` → must exist in
      content/reading_plans/<id>.yaml
    """
    from scripts.core import config

    errors: list[str] = []

    # Build the set of valid ids per target file.
    try:
        editions = config.load_editions() or []
        kinds = config.load_kinds() or []
        cats = config.load_categories() or []
    except Exception as e:
        return {"file": "<cross-refs>", "status": "error", "errors": [f"failed to load config: {e}"], "record_count": 0}

    canons_data, canons_err = _records_from_pyyaml(_CONTENT / "canons.yaml")
    if canons_err:
        return {"file": "<cross-refs>", "status": "error", "errors": [f"canons.yaml: {canons_err}"], "record_count": 0}
    canon_ids: set = set()
    if isinstance(canons_data, dict):
        canon_ids = set((canons_data.get("canons") or {}).keys())

    category_ids = {c["id"] for c in cats if isinstance(c, dict) and "id" in c}
    kind_codes = {k["code"] for k in kinds if isinstance(k, dict) and "code" in k}

    # Reading-plan ids — read directly from disk so we don't pull
    # in scripts.core.reading_plans as a hard dep here.
    plan_ids: set = set()
    plans_dir = _CONTENT / "reading_plans"
    if plans_dir.is_dir():
        plan_ids = {p.stem for p in plans_dir.glob("*.yaml")}

    # ----- editions.yaml refs -----
    for ed in editions:
        if not isinstance(ed, dict):
            continue
        ed_id = ed.get("id") or "<no-id>"
        label = f"editions.yaml[{ed_id}]"
        canon = ed.get("canon")
        if isinstance(canon, str) and canon and canon not in canon_ids:
            errors.append(f"{label}: canon {canon!r} not found in canons.yaml (known: {sorted(canon_ids)})")
        for f, target_set, target_label in (
            ("enabled_categories", category_ids, "categories.yaml"),
            ("enabled_kinds", kind_codes, "kinds.yaml"),
            ("disabled_kinds", kind_codes, "kinds.yaml"),
            ("enabled_reading_plans", plan_ids, "content/reading_plans/"),
        ):
            v = ed.get(f) or []
            if not isinstance(v, list):
                # Per-file spec catches the type mismatch; skip
                # silently here so we don't double-report.
                continue
            for item in v:
                if isinstance(item, str) and item not in target_set:
                    errors.append(f"{label}: {f}[{item!r}] not found in {target_label}")

    # ----- kinds.yaml `category` ref -----
    for k in kinds:
        if not isinstance(k, dict):
            continue
        code = k.get("code") or "<no-code>"
        cat = k.get("category")
        if isinstance(cat, str) and cat and cat not in category_ids:
            errors.append(f"kinds.yaml[{code}]: category {cat!r} not found in categories.yaml")

    return {
        "file": "<cross-refs>",
        "status": "ok" if not errors else "fail",
        "errors": errors,
        "record_count": len(editions) + len(kinds),
    }


def validate_canons(*, strict_unknown: bool = False) -> dict:
    """canons.yaml uses standard YAML-mapping shape (top-level
    ``canons:`` dict whose keys are canon ids), so it parses via
    PyYAML rather than `_parse_yaml_records`. Each canon record
    must have a ``books`` list of strings.

    The ``strict_unknown`` kwarg is accepted for signature uniformity
    with the per-file validators (run_all dispatches identically) but
    is unused here — canons.yaml is hand-rolled rather than spec'd."""
    data, err = _records_from_pyyaml(_CONTENT / "canons.yaml")
    if err:
        return {"file": "canons.yaml", "status": "error", "errors": [err], "record_count": 0}
    if not isinstance(data, dict):
        return {"file": "canons.yaml", "status": "fail", "errors": ["top level must be a mapping"], "record_count": 0}
    canons = data.get("canons") or {}
    if not isinstance(canons, dict):
        return {
            "file": "canons.yaml",
            "status": "fail",
            "errors": ["`canons:` key must be a mapping of canon-id → record"],
            "record_count": 0,
        }
    errors: list[str] = []
    for canon_id, rec in canons.items():
        if not isinstance(rec, dict):
            errors.append(f"canons.yaml[{canon_id}]: record must be a mapping")
            continue
        books = rec.get("books")
        if not isinstance(books, list):
            errors.append(f"canons.yaml[{canon_id}]: missing required `books:` list")
            continue
        for i, b in enumerate(books):
            if not isinstance(b, str):
                errors.append(f"canons.yaml[{canon_id}].books[{i}]: expected str, got {type(b).__name__}")
    return {
        "file": "canons.yaml",
        "status": "ok" if not errors else "fail",
        "errors": errors,
        "record_count": len(canons),
    }


# ----------------------------------------------------------------------
# Aggregate runner
# ----------------------------------------------------------------------


_VALIDATORS = {
    "editions": validate_editions,
    "kinds": validate_kinds,
    "categories": validate_categories,
    "books": validate_books,
    "canons": validate_canons,
    "cross-refs": validate_cross_refs,
}


def run_all(
    *,
    only: str | None = None,
    strict_unknown: bool = False,
) -> dict:
    """Run every validator (or just the named one). Returns a dict
    with per-file results + an aggregate summary.

    ``strict_unknown=True`` flips every per-file spec's
    ``strict_unknown`` to True for this run, surfacing unknown-field
    drift as a violation. Default off — the project's YAML files
    routinely carry transitional keys older code paths still write.
    """
    if only is not None and only not in _VALIDATORS:
        return {
            "status": "error",
            "code": "unknown_file",
            "message": (f"unknown file id {only!r}; valid: {sorted(_VALIDATORS.keys())}"),
            "files": [],
            "summary": {"total": 0, "ok": 0, "fail": 0, "error": 0},
        }
    files: list[dict] = []
    for name, fn in _VALIDATORS.items():
        if only and name != only:
            continue
        files.append(fn(strict_unknown=strict_unknown))
    summary = {
        "total": len(files),
        "ok": sum(1 for f in files if f.get("status") == "ok"),
        "fail": sum(1 for f in files if f.get("status") == "fail"),
        "error": sum(1 for f in files if f.get("status") == "error"),
    }
    summary["clean"] = summary["fail"] == 0 and summary["error"] == 0
    return {
        "status": "ok",
        "files": files,
        "summary": summary,
    }


# ----------------------------------------------------------------------
# CLI entrypoint
# ----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate_schemas",
        description="ω.19 — validate every project YAML against an explicit schema.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
    )
    parser.add_argument(
        "--file",
        default=None,
        choices=sorted(_VALIDATORS.keys()),
        help="validate a single file id only",
    )
    parser.add_argument(
        "--strict-unknown",
        action="store_true",
        help=("flip every per-file spec's strict_unknown to True; unknown / transitional fields become violations"),
    )
    args = parser.parse_args(argv)

    result = run_all(only=args.file, strict_unknown=args.strict_unknown)
    if result.get("status") == "error":
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"validate_schemas: {result.get('message')}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["files"]:
            mark = {"ok": "✓", "fail": "✗", "error": "!"}.get(f["status"], "?")
            print(f"  {mark} {f['file']:<22}  {f['record_count']:4} records   {len(f['errors']):3} error(s)")
            if f["errors"]:
                for e in f["errors"][:10]:
                    print(f"      {e}")
                if len(f["errors"]) > 10:
                    print(f"      … {len(f['errors']) - 10} more (use --json for the full list)")
        s = result["summary"]
        print(f"\n  total {s['total']}  ok {s['ok']}  fail {s['fail']}  error {s['error']}")
        if s["clean"]:
            print("  CLEAN")
        else:
            print("  VIOLATIONS")
    return 0 if result["summary"]["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
