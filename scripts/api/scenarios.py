"""ω.35-B.2 — scenarios API handlers, extracted from scripts/web.py.

Named hypothetical edition profiles (Phase μ.2½). Five handlers
plus two helpers and one regex constant:

- _SCENARIO_NAME_RE / _scenario_path / _resolve_scenario_recipe
  (internal helpers — used by the handlers)
- api_list_scenarios / api_get_scenario (read-only)
- api_save_scenario / api_import_scenario_yaml / api_delete_scenario
  (mutations; audit-logged)
- api_export_scenario_yaml (read-only)

Backward compatibility: scripts/web.py re-imports the 5 api_X names
so the existing flat namespace stays the same. Route-table lambdas
and tests that reference `scripts.web.api_*` continue working.

ψ.27 recipe form: built-in scenarios store
`recipe: {enabled_categories, enabled_kinds, disabled_kinds}`
instead of an explicit `enabled_kinds` list. The resolver
materializes recipes against the current kinds.yaml at read time,
so new kinds in the enabled categories are picked up automatically.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.core import audit_log, config, notes_io, paths

REPO = Path(__file__).resolve().parent.parent.parent
SCENARIOS_DIR = REPO / "content" / "scenarios"

_SCENARIO_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,40}$")


def _scenarios_dir() -> Path:
    """Resolve the scenarios/ directory through the ω.5 paths resolver,
    at CALL time, so a frozen desktop build reads/writes scenarios in the
    writable user-data content root (not the read-only bundle) and the
    test content-root override is honored. The module-level
    ``SCENARIOS_DIR`` constant is retained for back-compat importers."""
    return paths.content_root() / "scenarios"


def _scenario_path(name: str) -> Path:
    """Resolve a scenario name to its file path, validating safety."""
    if not _SCENARIO_NAME_RE.match(name):
        raise ValueError(f"invalid scenario name {name!r} — use lowercase a-z, 0-9, -, _ (max 41 chars)")
    return _scenarios_dir() / f"{name}.yaml"


# ψ.27 — recipe resolver. Built-in scenarios store
# `recipe: {enabled_categories, enabled_kinds, disabled_kinds}` instead
# of an explicit `enabled_kinds` list, so they pick up future kinds in
# their categories automatically. The resolver materializes the recipe
# to a flat list at read time using the same precedence the build
# pipeline applies to editions (via core/matrix._enabled_kinds_for_edition).
def _resolve_scenario_recipe(data: dict) -> list[str]:
    """If the scenario has a `recipe` field, resolve it to a flat
    enabled_kinds list against the current kinds.yaml. Otherwise
    return the explicit `enabled_kinds` field unchanged. Empty list
    if neither is set."""
    recipe = data.get("recipe")
    if isinstance(recipe, dict):
        from scripts.core.matrix import _enabled_kinds_for_edition

        all_kinds = config.load_kinds()
        # `enabled_kinds: ALL` shorthand → every kind in the registry.
        explicit = recipe.get("enabled_kinds")
        if isinstance(explicit, str) and explicit.upper() == "ALL":
            explicit = [k["code"] for k in all_kinds]
        # Build a synthetic edition-shape dict for the resolver. The
        # `enable_ai_notes` flag is passed through so scenarios can
        # express the χ-AI-notes opt-in the same way editions do —
        # "Full Corpus (every kind)" should literally mean every
        # kind, including AI-drafted ones, when the recipe says so.
        synth = {
            "enabled_categories": recipe.get("enabled_categories") or [],
            "enabled_kinds": explicit or [],
            "disabled_kinds": recipe.get("disabled_kinds") or [],
            "enable_ai_notes": bool(recipe.get("enable_ai_notes", False)),
        }
        return sorted(_enabled_kinds_for_edition(synth, all_kinds))
    explicit = data.get("enabled_kinds") or []
    return sorted(set(explicit))


def api_list_scenarios() -> dict:
    """List saved scenarios with their metadata.

    ψ.27 — surfaces the `builtin` flag so the UI can group built-in
    presets separately from user-saved scenarios. Each scenario's
    `enabled_kinds` is materialized through the recipe resolver so
    consumers see the same flat shape regardless of storage format.
    """
    scenarios_dir = _scenarios_dir()
    if not scenarios_dir.is_dir():
        return {"scenarios": []}
    import yaml

    out = []
    for f in sorted(scenarios_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        resolved_kinds = _resolve_scenario_recipe(data)
        out.append(
            {
                "name": f.stem,
                "based_on": data.get("based_on"),
                "label": data.get("label", f.stem),
                "notes": data.get("notes", ""),
                "enabled_kinds": resolved_kinds,
                "created": data.get("created"),
                "builtin": bool(data.get("builtin")),
                "has_recipe": isinstance(data.get("recipe"), dict),
            }
        )
    # Built-ins first, then user-saved alphabetically (current
    # secondary sort comes from the glob — file system order; we
    # apply a stable explicit sort for clarity).
    out.sort(key=lambda s: (0 if s["builtin"] else 1, s["name"]))
    return {"scenarios": out}


def api_get_scenario(name: str) -> dict:
    """Return one scenario's full record.

    ψ.27 — also returns `enabled_kinds_resolved` (recipe materialized
    to flat list) so the /matrix Load button can apply the scenario
    without re-resolving on the client.
    """
    try:
        path = _scenario_path(name)
    except ValueError as e:
        return {"error": str(e)}
    if not path.is_file():
        return {"error": f"scenario {name!r} not found"}
    import yaml

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        return {"error": f"corrupt scenario file: {e}"}
    resolved = _resolve_scenario_recipe(data)
    return {
        "ok": True,
        "scenario": {
            "name": name,
            **data,
            "enabled_kinds_resolved": resolved,
        },
    }


@audit_log.audit_endpoint(action="save_scenario")
def api_save_scenario(name: str, payload: dict) -> dict:
    """Create or overwrite a named scenario from the current toggle state.

    Scenarios live in content/scenarios/<name>.yaml — separate from
    editions.yaml. They store:
      - based_on: the edition id this scenario was forked from
      - label: human-readable name
      - notes: optional description
      - enabled_kinds: the explicit final set of enabled kind codes
      - created: ISO 8601 timestamp

    Saving DOES NOT modify editions.yaml or affect the build pipeline.
    Scenarios are exploration-only until promoted (future μ.2½ task).
    """
    try:
        path = _scenario_path(name)
    except ValueError as e:
        return {"error": str(e)}

    enabled_kinds = payload.get("enabled_kinds") or []
    if not isinstance(enabled_kinds, list) or not all(isinstance(x, str) for x in enabled_kinds):
        return {"error": "enabled_kinds must be a list of strings"}

    based_on = payload.get("based_on")
    if based_on is not None and based_on not in config.editions_by_id():
        return {"error": f"unknown based_on edition: {based_on}"}

    known_kinds = {k["code"] for k in config.load_kinds()}
    unknown = set(enabled_kinds) - known_kinds
    if unknown:
        return {"error": f"unknown kind(s): {sorted(unknown)}"}

    from datetime import datetime, timezone

    record = {
        "based_on": based_on,
        "label": payload.get("label") or name,
        "notes": payload.get("notes", ""),
        "enabled_kinds": sorted(set(enabled_kinds)),
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    _scenarios_dir().mkdir(parents=True, exist_ok=True)

    # Use plain text rendering so we don't need ruamel; PyYAML's default
    # output is fine for these simple records (no comments to preserve).
    import yaml

    text = yaml.safe_dump(record, sort_keys=False, allow_unicode=True, default_flow_style=False)
    if path.is_file():
        notes_io.ensure_backup(path)
    notes_io.atomic_write(path, text)

    return {"ok": True, "name": name, "path": str(path.relative_to(REPO))}


# ψ.27 — YAML export + import. Lets a user copy a scenario between
# machines / publishers / dev <-> prod by paste-and-load.
def api_export_scenario_yaml(name: str) -> dict:
    """Return the raw YAML text of a scenario for download / clipboard.

    Returns ``{"status": "ok", "yaml": str, "name": str}`` on success.
    Built-in scenarios export their recipe form; user-saved export
    their stored explicit `enabled_kinds`.
    """
    try:
        path = _scenario_path(name)
    except ValueError as e:
        return {"status": "error", "code": "invalid_name", "http": 400, "message": str(e)}
    if not path.is_file():
        return {"status": "error", "code": "not_found", "http": 404, "message": f"scenario {name!r} not found"}
    return {
        "status": "ok",
        "name": name,
        "yaml": path.read_text(encoding="utf-8"),
    }


@audit_log.audit_endpoint(action="import_scenario_yaml")
def api_import_scenario_yaml(yaml_text: str, *, name: str | None = None, overwrite: bool = False) -> dict:
    """Parse YAML text and persist as a scenario file.

    `name` may be supplied explicitly; otherwise we try to derive it
    from a top-level `name:` field in the YAML (fallback: error). If
    the resulting file already exists and `overwrite` is False, returns
    a ``conflict`` error so the UI can prompt for a rename.

    The imported record may use either the explicit
    `enabled_kinds` form or the recipe form. Either way we validate
    against the kinds registry before writing — unknown kind codes
    or unknown category ids are rejected with a clear message.
    """
    if not isinstance(yaml_text, str) or not yaml_text.strip():
        return {"status": "error", "code": "empty_input", "http": 400, "message": "yaml text is required"}
    if len(yaml_text) > 64_000:
        return {"status": "error", "code": "too_large", "http": 413, "message": "yaml text must be ≤ 64KB"}
    # ξ.17 SEC-011 — guard against the YAML billion-laughs class:
    # PyYAML's `safe_load` is safe vs arbitrary code execution but
    # NOT vs anchor-aliased blowup. 64 KB of nested aliases can
    # consume seconds of CPU and many GB of RAM. Pre-scan for
    # unusual `&`/`*` anchor density; reject anything beyond a
    # reasonable threshold. Legitimate scenario YAML has at most a
    # handful of anchors (often zero).
    anchor_count = yaml_text.count("&")
    alias_count = yaml_text.count("*")
    if anchor_count > 50 or alias_count > 50:
        return {
            "status": "error",
            "code": "yaml_anchor_density",
            "http": 400,
            "message": (
                f"YAML rejected: {anchor_count} anchors / {alias_count} aliases "
                "exceeds the safety threshold (50 each). Anchor expansion can "
                "consume unbounded resources; legitimate scenario YAML uses "
                "few or no anchors."
            ),
        }
    import yaml

    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        return {"status": "error", "code": "parse_error", "http": 400, "message": f"invalid YAML: {e}"}
    if not isinstance(data, dict):
        return {
            "status": "error",
            "code": "shape_error",
            "http": 400,
            "message": "YAML must be a mapping (key: value pairs)",
        }

    # Derive the scenario name.
    candidate_name = name or data.get("name") or data.get("id")
    if not candidate_name or not isinstance(candidate_name, str):
        return {
            "status": "error",
            "code": "missing_name",
            "http": 400,
            "message": "scenario name required (pass name= or include `name:` in YAML)",
        }
    try:
        path = _scenario_path(candidate_name)
    except ValueError as e:
        return {"status": "error", "code": "invalid_name", "http": 400, "message": str(e)}

    if path.is_file() and not overwrite:
        return {
            "status": "error",
            "code": "conflict",
            "http": 409,
            "message": f"scenario {candidate_name!r} already exists; pass overwrite=true to replace",
        }

    # Validate the resolved kind set + based_on (if set).
    based_on = data.get("based_on")
    if based_on is not None and based_on not in config.editions_by_id():
        return {
            "status": "error",
            "code": "unknown_based_on",
            "http": 400,
            "message": f"unknown based_on edition: {based_on}",
        }

    known_kinds = {k["code"] for k in config.load_kinds()}
    known_cats = {c["id"] for c in config.load_categories()}

    recipe = data.get("recipe")
    if isinstance(recipe, dict):
        cats = recipe.get("enabled_categories") or []
        ek = recipe.get("enabled_kinds")
        dk = recipe.get("disabled_kinds") or []
        if not isinstance(cats, list) or not all(isinstance(x, str) for x in cats):
            return {
                "status": "error",
                "code": "shape_error",
                "http": 400,
                "message": "recipe.enabled_categories must be a list of strings",
            }
        bad_cats = set(cats) - known_cats
        if bad_cats:
            return {
                "status": "error",
                "code": "unknown_category",
                "http": 400,
                "message": f"unknown category id(s): {sorted(bad_cats)}",
            }
        if isinstance(ek, str) and ek.upper() == "ALL":
            pass  # sentinel; resolves to all kinds at read time
        elif ek is None or (isinstance(ek, list) and all(isinstance(x, str) for x in ek)):
            bad_k = set(ek or []) - known_kinds
            if bad_k:
                return {
                    "status": "error",
                    "code": "unknown_kind",
                    "http": 400,
                    "message": f"unknown kind code(s): {sorted(bad_k)}",
                }
        else:
            return {
                "status": "error",
                "code": "shape_error",
                "http": 400,
                "message": "recipe.enabled_kinds must be a list of strings or the literal 'ALL'",
            }
        if not isinstance(dk, list) or not all(isinstance(x, str) for x in dk):
            return {
                "status": "error",
                "code": "shape_error",
                "http": 400,
                "message": "recipe.disabled_kinds must be a list of strings",
            }
    else:
        ek_flat = data.get("enabled_kinds") or []
        if not isinstance(ek_flat, list) or not all(isinstance(x, str) for x in ek_flat):
            return {
                "status": "error",
                "code": "shape_error",
                "http": 400,
                "message": "enabled_kinds must be a list of strings",
            }
        bad = set(ek_flat) - known_kinds
        if bad:
            return {
                "status": "error",
                "code": "unknown_kind",
                "http": 400,
                "message": f"unknown kind code(s): {sorted(bad)}",
            }

    _scenarios_dir().mkdir(parents=True, exist_ok=True)
    existed = path.is_file()
    if existed:
        notes_io.ensure_backup(path)
    notes_io.atomic_write(path, yaml_text if yaml_text.endswith("\n") else yaml_text + "\n")
    return {
        "status": "ok",
        "name": candidate_name,
        "path": str(path.relative_to(REPO)),
        "overwritten": overwrite and existed,
    }


@audit_log.audit_endpoint(action="delete_scenario")
def api_delete_scenario(name: str) -> dict:
    """Remove a saved scenario file.

    ψ.27 — built-in scenarios are protected from deletion so the
    preset library stays intact across checkouts. The user can
    delete user-saved scenarios as before.
    """
    try:
        path = _scenario_path(name)
    except ValueError as e:
        return {"error": str(e)}
    if not path.is_file():
        return {"error": f"scenario {name!r} not found"}
    import yaml

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        data = {}
    if data.get("builtin"):
        return {
            "error": f"scenario {name!r} is a built-in preset and cannot be deleted",
        }
    notes_io.ensure_backup(path)
    path.unlink()
    return {"ok": True, "removed": name}
