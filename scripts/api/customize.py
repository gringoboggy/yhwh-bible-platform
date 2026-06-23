"""ω.35-B.4 — customize API handlers, extracted from scripts/web.py.

Two audit-logged mutation handlers for the /customize console
(Phase ν.1 — edit symbols/labels/descriptions for categories
and kinds):
- api_save_category (PUT /api/category/<id>)
- api_save_kind     (PUT /api/kind/<code>)

The `_patch_yaml_entry` helper stays in web.py because it's
shared with `api_save_edition_meta` and `api_save_publisher_meta`
(both still in web.py until ω.35-B.5). Lazy-import inside each
handler avoids the cycle (web.py top-imports this module).

Out of scope for B.4 (deferred to B.5 — editions cluster):
- api_save_edition / api_save_edition_meta / api_save_publisher_meta
- api_clone_edition / api_create_edition_from_template
- api_save_note_toggle / api_preview_edition_changes
- api_apply_kind_to_all_editions
- api_customize_data (the GET endpoint that bundles
  cats+kinds+editions+themes; lives near these handlers but is
  read-only and not part of the customize-mutation scope)

Backward compatibility: scripts/web.py re-imports both handler
names so route-table lambdas (`_PUT_ROUTES`) and tests that
reference `scripts.web.api_save_*` continue working unchanged.
Tests that monkeypatch `scripts.web._patch_yaml_entry` need
no changes either — the lazy import resolves to web.py's
binding at call time, so any patch on `scripts.web` flows
through.
"""

from __future__ import annotations

from pathlib import Path

from scripts.core import audit_log, config, notes_io, paths

REPO = Path(__file__).resolve().parent.parent.parent


@audit_log.audit_endpoint(action="save_category")
def api_save_category(cat_id: str, payload: dict) -> dict:
    """Update symbol / label / description for one category."""
    # Lazy import — _patch_yaml_entry stays in web.py (also used
    # by api_save_edition_meta + api_save_publisher_meta which
    # remain there until B.5). At call time web.py is fully
    # loaded so the import resolves cleanly.
    from scripts.web import _patch_yaml_entry

    cats = config.categories_by_id()
    if cat_id not in cats:
        return {"error": f"unknown category: {cat_id}"}

    updates = {}
    if "symbol" in payload:
        s = (payload["symbol"] or "").strip()
        if not s or len(s) > 4:
            return {"error": "symbol must be 1-4 visible chars"}
        updates["symbol"] = s
    if "label" in payload:
        lab = (payload["label"] or "").strip()
        if not lab:
            return {"error": "label cannot be empty"}
        if len(lab) > 60:
            return {"error": "label too long (max 60 chars)"}
        updates["label"] = lab
    if "description" in payload:
        updates["description"] = (payload["description"] or "").strip()
    if not updates:
        return {"error": "no updates supplied"}

    path = paths.categories_yaml()
    text = path.read_text(encoding="utf-8")
    try:
        new_text = _patch_yaml_entry(text, "id", cat_id, updates)
    except ValueError as e:
        return {"error": str(e)}

    notes_io.ensure_backup(path)
    notes_io.atomic_write(path, new_text)
    config.load_categories.cache_clear()
    from scripts.core import matrix as matrix_mod

    matrix_mod.compute_matrix.cache_clear()
    return {"ok": True, "id": cat_id, "updated": list(updates.keys())}


@audit_log.audit_endpoint(action="save_kind")
def api_save_kind(kind_code: str, payload: dict) -> dict:
    """Update symbol / label / description for one kind."""
    from scripts.web import _patch_yaml_entry

    kinds = config.kinds_by_code()
    if kind_code not in kinds:
        return {"error": f"unknown kind: {kind_code}"}

    updates = {}
    if "symbol" in payload:
        s = (payload["symbol"] or "").strip()
        if not s or len(s) > 4:
            return {"error": "symbol must be 1-4 visible chars"}
        updates["symbol"] = s
    if "label" in payload:
        lab = (payload["label"] or "").strip()
        if not lab:
            return {"error": "label cannot be empty"}
        if len(lab) > 60:
            return {"error": "label too long (max 60 chars)"}
        updates["label"] = lab
    if "description" in payload:
        updates["description"] = (payload["description"] or "").strip()
    if not updates:
        return {"error": "no updates supplied"}

    path = paths.kinds_yaml()
    text = path.read_text(encoding="utf-8")
    try:
        new_text = _patch_yaml_entry(text, "code", kind_code, updates)
    except ValueError as e:
        return {"error": str(e)}

    notes_io.ensure_backup(path)
    notes_io.atomic_write(path, new_text)
    config.load_kinds.cache_clear()
    from scripts.core import matrix as matrix_mod

    matrix_mod.compute_matrix.cache_clear()
    return {"ok": True, "code": kind_code, "updated": list(updates.keys())}
