"""scripts.core.edition_templates — partial-edition starter packs.

Phase ψ.7-B (2026-05-09). Companion to ψ.7-A's built-in editions.

The 9 built-in editions in `content/editions.yaml` ship as fully-
configured edition records. Templates are partial editions that
buyers clone-and-tweak via the wizard's "Start from template…"
button on step 1.

Each template lives in `content/edition_templates/<template_id>.yaml`
with the same field shape as an editions.yaml entry plus three
template-specific fields:

    template_id:           unique slug
    template_label:        wizard-picker display name
    template_description:  multi-line explanation
    canon, title, short_title, isbn, target_audience,
    enabled_categories, enabled_kinds, disabled_kinds,
    max_phase, cover_image, notes, popup_languages_default,
    popup_translation

Public API:
    load_templates() -> list[dict]
        Returns every template, sorted by template_id.
    get_template(template_id) -> dict | None
        Returns one template by id.
    create_from_template(template_id, *, new_id, new_title,
                          editions_path=None) -> dict
        Pure function: validates inputs, clones template into
        editions.yaml, returns {"status": "ok"|"error", ...}
        per the §9 mental model.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml

from scripts.core import config, notes_io


REPO = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = REPO / "content" / "edition_templates"
EDITIONS_PATH = REPO / "content" / "editions.yaml"

# Required template fields (separate from editions.yaml fields)
TEMPLATE_REQUIRED = {"template_id", "template_label", "template_description"}

# Required editions.yaml-equivalent fields for a clone to validate
EDITION_REQUIRED = {
    "canon",
    "title",
    "short_title",
    "target_audience",
    "enabled_categories",
    "max_phase",
    "popup_languages_default",
}

# id format: lowercase, hyphenated, alphanumeric. Same shape as
# the existing 9 built-in editions.
import re

ID_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


@dataclass(frozen=True)
class TemplateLoadError(Exception):
    """Raised when a template file is malformed or missing fields."""

    template_id: str
    detail: str


@lru_cache(maxsize=1)
def load_templates() -> list[dict]:
    """Read every YAML in content/edition_templates/ and return a
    sorted list of template dicts.

    Sorted by template_id alphabetically. Cached for the life of
    the process; call `load_templates.cache_clear()` after editing
    templates on disk to refresh.

    Templates with malformed YAML or missing required fields are
    skipped with a logged warning rather than aborting the load —
    a single bad template doesn't break the wizard for the others.
    """
    if not TEMPLATES_DIR.is_dir():
        return []

    templates: list[dict] = []
    for path in sorted(TEMPLATES_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        # Skip if missing template-specific fields
        if not TEMPLATE_REQUIRED.issubset(data.keys()):
            continue
        # Skip if missing edition-equivalent required fields
        if not EDITION_REQUIRED.issubset(data.keys()):
            continue
        templates.append(data)
    return sorted(templates, key=lambda t: t["template_id"])


def get_template(template_id: str) -> Optional[dict]:
    """Return one template by id, or None if not found."""
    for t in load_templates():
        if t.get("template_id") == template_id:
            return t
    return None


def _existing_edition_ids() -> set[str]:
    """Return the set of edition ids currently in editions.yaml.
    Used to reject duplicate new_ids."""
    eds = config.load_editions()
    return {e["id"] for e in eds}


def _strip_template_fields(template: dict) -> dict:
    """Return a dict of editions.yaml-shape fields, dropping the
    template_* fields. The result is suitable for appending as a
    new entry under `editions:` in editions.yaml."""
    out = {}
    for k, v in template.items():
        if k.startswith("template_"):
            continue
        out[k] = v
    return out


def _format_yaml_block(edition: dict) -> str:
    """Render an edition dict as YAML in the same style as
    editions.yaml entries (2-space indent, list items dashed,
    block strings unquoted unless ambiguous).

    Mirrors yaml.safe_dump's default but with explicit indent +
    sort_keys=False so field order matches the input dict.
    """
    text = yaml.safe_dump(
        [edition],
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        indent=2,
    )
    # safe_dump emits "- id: ..." at the top of each list item. The
    # editions.yaml style uses "  - id:" (2-space indent before
    # the dash). Re-indent to match.
    lines = []
    for line in text.splitlines():
        if line.startswith("- "):
            lines.append("  " + line)
        elif line.startswith("  "):
            # nested fields under the item — bump indent by 2
            lines.append("  " + line)
        else:
            lines.append(line)
    return "\n".join(lines)


def create_from_template(
    template_id: str,
    *,
    new_id: str,
    new_title: str,
    editions_path: Optional[Path] = None,
) -> dict:
    """Clone a template into editions.yaml as a new edition.

    Returns the §9 standard dict shape:
      {"status": "ok", "edition_id": new_id, "edition": {...}}
      {"status": "error", "code": "...", "http": 4xx, "message": "..."}

    Validates:
      - template_id exists in content/edition_templates/
      - new_id matches ID_RE (lowercase, hyphenated)
      - new_id is not already in editions.yaml
      - new_title is non-empty and stripped

    On success, atomically appends the cloned edition to
    editions.yaml + clears config.load_editions cache so the new
    edition appears immediately in /customize, /publisher, /matrix.

    `editions_path` override is for testing; production uses the
    module-level EDITIONS_PATH.
    """
    template = get_template(template_id)
    if template is None:
        return {
            "status": "error",
            "code": "unknown_template",
            "http": 404,
            "message": f"template {template_id!r} not found",
        }

    new_id_clean = (new_id or "").strip()
    if not new_id_clean:
        return {
            "status": "error",
            "code": "missing_new_id",
            "http": 400,
            "message": "new_id is required",
        }
    if not ID_RE.match(new_id_clean):
        return {
            "status": "error",
            "code": "invalid_new_id",
            "http": 400,
            "message": ("new_id must be lowercase, alphanumeric, and hyphenated (e.g. 'my-new-edition')"),
        }

    new_title_clean = (new_title or "").strip()
    if not new_title_clean:
        return {
            "status": "error",
            "code": "missing_new_title",
            "http": 400,
            "message": "new_title is required",
        }

    # Refresh the cache so we see any concurrent additions
    if hasattr(config.load_editions, "cache_clear"):
        config.load_editions.cache_clear()
    if new_id_clean in _existing_edition_ids():
        return {
            "status": "error",
            "code": "duplicate_id",
            "http": 409,
            "message": (f"edition id {new_id_clean!r} already exists in editions.yaml"),
        }

    # Build the new edition dict — id/title overrides come first
    # so they appear at the top of the YAML block, then the rest
    # of the template's fields.
    cloned = _strip_template_fields(template)
    new_edition = {"id": new_id_clean, "title": new_title_clean}
    for k, v in cloned.items():
        if k in ("title",):
            continue  # overridden above
        new_edition[k] = v

    target = editions_path or EDITIONS_PATH

    # Read existing editions.yaml, append the new block, write back
    # atomically. Preserves the existing file's comments + ordering.
    existing = target.read_text(encoding="utf-8")
    block = _format_yaml_block(new_edition)
    # Ensure there's a separating blank line between the last
    # existing entry and the new one
    if not existing.endswith("\n"):
        existing = existing + "\n"
    if not existing.endswith("\n\n"):
        existing = existing + "\n"
    new_text = existing + block + ("\n" if not block.endswith("\n") else "")

    # ensure_backup before atomic_write — both standard project
    # mutation safety per CLAUDE_PROJECT_RULES §7.1
    notes_io.ensure_backup(target)
    notes_io.atomic_write(target, new_text)

    # Cache invalidation so the new edition appears immediately
    if hasattr(config.load_editions, "cache_clear"):
        config.load_editions.cache_clear()
    # matrix cache too — its compute_matrix() reads editions
    try:
        from scripts.core import matrix as _matrix_mod

        _matrix_mod.compute_matrix.cache_clear()
    except Exception:
        pass

    return {
        "status": "ok",
        "edition_id": new_id_clean,
        "edition": new_edition,
    }
