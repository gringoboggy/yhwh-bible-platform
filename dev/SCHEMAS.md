# YAML schemas

> **Phase tags:** ω.19 + ω.19.1 + ω.19.2. Companion to
> `scripts/validate_schemas.py`.

The project's structure-of-truth lives in a handful of YAML files
under `content/`. Hand-edits and tool-driven mutations both pass
through these files; a typo or wrong-type value can silently break
the build pipeline. ω.19's `validate_schemas.py` validates each
file against an explicit per-record schema and exits non-zero on
any violation.

Run::

    python scripts/validate_schemas.py
    python scripts/validate_schemas.py --json
    python scripts/validate_schemas.py --file kinds

The framework lives in `scripts/validate_schemas.py` itself
(`FieldSpec`, `RecordSpec`, `validate_record` — ~50 lines, no
external deps per CLAUDE_PROJECT_RULES §10).

---

## 1. Files validated

| File | Records | Required fields | Notes |
|---|---|---|---|
| `content/editions.yaml` | one per edition (9 today) | `id` | every list field validated as `list[str]`; phase enum on `max_phase` |
| `content/kinds.yaml` | one per kind (66) | `code`, `category` | phase enum: `{mvp, phase2, phase3, phase4, legacy}` |
| `content/categories.yaml` | one per category (15) | `id`, `label` | `sort_order` ≥ 0 |
| `content/books.yaml` | one per book (87) | `code`, `title` | `ch_count` ≥ 0; `files` validated as `list[str]` |
| `content/canons.yaml` | one canon entry per id (5) | `books` | parsed via PyYAML (different shape) |
| `<cross-refs>` (virtual) | one synthetic record per edition + kind | n/a | ω.19.1 — checks references resolve across files; see §4 |

Coverage is intentionally focused on the load-bearing files. Per-
translation `_meta.yaml` files, scenario / reading-plan YAML, and
edition templates are validated by their respective owning code
paths (`config.load_translations`, `api_save_scenario`,
`scripts.core.reading_plans.load_plan`,
`scripts.core.edition_templates`); ω.19 deliberately doesn't
duplicate them.

---

## 2. The framework — three pieces

### `FieldSpec(name, *, required, type, item_type, constraint, constraint_message)`

One field's expectations:

- `name` — field name in the record
- `required` — `True` (default) → missing is an error; `False` →
  absent is OK and `None`-valued is OK too
- `type` — expected type or tuple of types (e.g. `(str, int)`)
- `item_type` — when `type` is `list`, every item must match this
- `constraint` — optional `callable(value) → bool` for custom
  validation (e.g. enum membership, range checks)
- `constraint_message` — human-readable explanation surfaced on
  constraint failure

### `RecordSpec(fields=[...], strict_unknown=False)`

A record is a `dict`; the spec lists every field:

- `fields` — list of `FieldSpec`
- `strict_unknown` — `False` (default) → unknown fields silently
  pass (the project's YAML files often carry transitional keys);
  `True` → unknown fields are errors

### `validate_record(record, spec, *, label)`

Returns a list of error strings (empty = clean). The `label` is
prefixed onto every error so the caller can build "`<file>:<id>:
<error>`" diagnostics without re-threading context.

---

## 3. Adding a new validator

When shipping a new YAML config:

1. Define a `*_SPEC = RecordSpec(fields=[...])` for the file.
2. Add a `validate_<name>() -> dict` function returning
   `{file, status, errors, record_count}`.
3. Register it in `_VALIDATORS = {"<name>": validate_<name>, ...}`.
4. Add tests to `tests/test_scripts.py:TestOmega19SchemaValidator`
   covering happy + at least one unhappy path (missing required
   field; wrong type).
5. Add a row to §1 above.

For files that use the project's custom `_parse_yaml_records`
parser (top-level `<key>: [- record1 - record2 ...]` shape), use
`_records_from_yaml`. For files using standard PyYAML mapping
shape (top-level dict), use `_records_from_pyyaml`.

---

## 4. Cross-file referential integrity (ω.19.1)

`validate_cross_refs()` runs after every per-file validator and
catches the drift class where one file references an id that
doesn't exist in its target file. Coverage:

| Source field | Target file | Notes |
|---|---|---|
| `editions.yaml` `canon` | `canons.yaml` (top-level keys) | one ref per edition |
| `editions.yaml` `enabled_categories[*]` | `categories.yaml` `id` | per-edition list |
| `editions.yaml` `enabled_kinds[*]` | `kinds.yaml` `code` | per-edition list |
| `editions.yaml` `disabled_kinds[*]` | `kinds.yaml` `code` | per-edition list |
| `editions.yaml` `enabled_reading_plans[*]` | `content/reading_plans/<id>.yaml` | filename stem |
| `kinds.yaml` `category` | `categories.yaml` `id` | one ref per kind |

Run via `--file cross-refs`; integrated into the default `run_all`
sweep. Type-mismatch errors (e.g. `enabled_kinds: "abc"` instead of
a list) are NOT re-reported here — the per-file spec owns those.

ω.19.1 also fixed the `_parse_yaml_records` empty-list bug: bare
`field: []` now round-trips as `[]` (was the literal string
`"[]"`). The buggy quoted form `field: "[]"` left over from prior
round-trips is detected by the per-file validator as
"expected list, got str".

## 4.1 Remaining limitations

- **No PyYAML schema validation for canons.yaml.** The validator
  hand-rolls the canons check. If canons.yaml gets a more
  complex shape, lift it to its own `RecordSpec`.

---

## 5. CI integration

`validate_schemas.py` exits non-zero on any violation, so it can
be wired into a pre-commit hook or CI pipeline:

    # .git/hooks/pre-commit
    python scripts/validate_schemas.py || exit 1

The `--strict-unknown` flag (ω.19.2) flips every per-file spec's
`strict_unknown=True` for that run, surfacing transitional /
typo'd fields older code paths still write. Default off — the
project's YAML files routinely carry transitional keys; turn it
on when auditing for orphaned fields.

    python scripts/validate_schemas.py --strict-unknown

## 6. Preflight composition (ω.19.2)

`validate_schemas.run_all()` is composed into the readiness
dashboard's `_compute_preflight_uncached()` as the
`schema_compliance` check, mirroring the `rules_compliance`
shape (Tier-3 structural enforcement per CLAUDE_PROJECT_RULES
§9 — "Add a meta-tool that integrates with the preflight
dashboard"):

- **status: pass** — all per-file checks ok
- **status: fail** — any per-file check fails or errors
- **details** — list of failing files with up to 3 errors each
  so a publisher sees what's wrong without leaving the page
- **jump_to** — `/preflight` (the issue is code/data-level,
  not console-level)
- **try/except wrapper** — a broken validator can't 500 the
  dashboard; degrades to a `warn` with the failure reason

This means schema drift surfaces continuously alongside rules
linting on every preflight read, not just on manual CLI runs.
