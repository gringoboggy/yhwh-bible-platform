"""ω.35-B.5 — editions cluster API handlers, extracted from scripts/web.py.

Eight audit-logged mutation handlers for the editions/customize
surface, plus two private helpers and one read-only function
(preview). The largest single-slice extraction in the file split.

Handlers (with their route registrations):
- api_save_edition          PUT /api/edition/<id>
- api_save_edition_meta     PUT /api/edition-meta/<id>
- api_save_publisher_meta   PUT /api/publisher/<id>
- api_clone_edition         PUT /api/editions/clone
- api_create_edition_from_template  PUT /api/editions/from-template
- api_save_note_toggle      PUT /api/edition/<id>/note-toggle
- api_apply_kind_to_all_editions  POST /api/matrix/apply-kind-to-all
- api_preview_edition_changes  PUT /api/edition-meta/<id>/preview (bespoke, not in _PUT_ROUTES)

Private helpers moved with this slice (used only by handlers here):
- _patch_edition_kind_lists  (used by api_save_edition)
- _append_cloned_edition     (used by api_clone_edition)

Lazy imports from web.py (helpers + constants shared with handlers
that stay in web.py — like api_publisher_data, api_customize_data):
- _patch_yaml_entry      (also used by api_save_category/api_save_kind in customize.py)
- _patch_yaml_list_field
- _load_themes           (also used by api_customize_data)
- _validate_cover_path
- parse_note_id / html_ref_id_from_note_id
- PUBLISHING_TEXT_LIMITS / PUBLISHING_LIST_FIELDS

The lazy-import-back-to-web pattern (established by B.3a covers
and reinforced by B.3b sources + B.4 customize) avoids the
import cycle: web.py top-imports this module; this module's
function bodies lazy-import the helpers at call time when web.py
is fully loaded.

Cross-module coordination: scripts/api/covers.py was lazy-
importing api_save_edition_meta from scripts.web. As of B.5 it
must lazy-import from scripts.api.editions instead — updated in
the same commit.

scripts/web.py re-imports all 8 handler names so route-table
lambdas and existing tests work unchanged.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.core import audit_log, config, notes_io

REPO = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------
# Private helpers — moved with the handlers because they're used only
# inside this module.
# ---------------------------------------------------------------------


def _patch_edition_kind_lists(text: str, edition_id: str, enabled_kinds: list[str], disabled_kinds: list[str]) -> str:
    """Targeted regex update of one edition's enabled_kinds + disabled_kinds
    blocks in editions.yaml — preserves all comments, ordering, and other
    fields outside those blocks."""
    block_re = re.compile(
        rf"(^  - id: {re.escape(edition_id)}\n)(.*?)(?=^  - id:|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = block_re.search(text)
    if not m:
        raise ValueError(f"edition {edition_id!r} not found in editions.yaml")

    block_start, block_body, block_end = m.start(), m.group(2), m.end()

    def _format_list(name: str, items: list[str]) -> str:
        if not items:
            return f"    {name}: []\n"
        lines = "\n".join(f"      - {x}" for x in items)
        return f"    {name}:\n{lines}\n"

    new_enabled = _format_list("enabled_kinds", enabled_kinds)
    enabled_re = re.compile(
        r"^(    enabled_kinds:.*?\n)((?:      - [^\n]+\n)*)",
        re.MULTILINE,
    )
    if enabled_re.search(block_body):
        new_body = enabled_re.sub(new_enabled, block_body, count=1)
    else:
        cats_re = re.compile(
            r"^(    enabled_categories:.*?\n(?:      - [^\n]+\n)*)",
            re.MULTILINE,
        )
        cm = cats_re.search(block_body)
        if cm:
            new_body = block_body[: cm.end()] + new_enabled + block_body[cm.end() :]
        else:
            new_body = new_enabled + block_body

    new_disabled = _format_list("disabled_kinds", disabled_kinds)
    disabled_re = re.compile(
        r"^(    disabled_kinds:.*?\n)((?:      - [^\n]+\n)*)",
        re.MULTILINE,
    )
    if disabled_re.search(new_body):
        new_body = disabled_re.sub(new_disabled, new_body, count=1)
    else:
        ek_re = re.compile(
            r"^(    enabled_kinds:.*?\n(?:      - [^\n]+\n)*|    enabled_kinds: \[\]\n)",
            re.MULTILINE,
        )
        em = ek_re.search(new_body)
        if em:
            new_body = new_body[: em.end()] + new_disabled + new_body[em.end() :]
        else:
            new_body = new_body + new_disabled

    return text[:block_start] + m.group(1) + new_body + text[block_end:]


def _append_cloned_edition(
    text: str,
    source_id: str,
    new_id: str,
    new_title: str,
    override_cover_image: str = "",
    override_book_covers: list[str] | None = None,
) -> str:
    """Append a deep-copy of one edition record to editions.yaml."""
    src = config.editions_by_id().get(source_id)
    if not src:
        raise ValueError(f"unknown source: {source_id!r}")

    fields_text: list[str] = [f"  - id: {new_id}"]

    scalar_fields = [
        ("title", new_title),
        ("short_title", src.get("short_title", "")),
        # Ω.0 pivot (2026-05-14): isbn field dropped from editions.yaml. term-ref-ok
        ("canon", src.get("canon", "")),
        ("target_audience", src.get("target_audience", "")),
        ("verse_popups", src.get("verse_popups", True)),
        ("verse_marker_glyph", src.get("verse_marker_glyph", "")),
        ("popup_translation", src.get("popup_translation", "")),
        ("theme", src.get("theme", "classic")),
        ("notes", src.get("notes", "")),
        ("description", src.get("description", "")),
        ("dedication", src.get("dedication", "")),
        # σ.4 — edition-identity fields. Use src.get(name) with no default so an
        # absent field stays absent on the clone (None is skipped below),
        # preserving the source's effective default (HOLY BIBLE / title).
        ("display_name", src.get("display_name")),
        ("cover_main_title", src.get("cover_main_title")),
        ("cover_template", src.get("cover_template")),
        ("cover_image", override_cover_image if override_cover_image is not None else src.get("cover_image", "")),
        # mint-10 #high — phase/AI kind-gate scalars. Use src.get(name) with no
        # default so an absent field stays absent on the clone (None is skipped
        # below), preserving the source's effective default exactly.
        ("max_phase", src.get("max_phase")),
        ("enable_ai_notes", src.get("enable_ai_notes")),
    ]
    for fname, fval in scalar_fields:
        if fval is None:
            continue
        if fval is True:
            fields_text.append(f"    {fname}: true")
        elif fval is False:
            fields_text.append(f"    {fname}: false")
        elif isinstance(fval, (int, float)):
            # Emit a numeric scalar as a bare literal. (Bools are handled
            # above via `is True/False`; this catches int/float, incl. 0 —
            # which the old `fval == 0` branch wrongly serialized as "".)
            fields_text.append(f"    {fname}: {fval}")
        elif fval == "":
            fields_text.append(f'    {fname}: ""')
        else:
            sval = str(fval).replace('"', '\\"')
            fields_text.append(f'    {fname}: "{sval}"')

    list_fields: list[tuple[str, list]] = []
    pld = src.get("popup_languages_default")
    if pld:
        list_fields.append(("popup_languages_default", list(pld)))
    plpb = src.get("popup_languages_per_book")
    if plpb:
        list_fields.append(("popup_languages_per_book", list(plpb)))
    td = src.get("traditions_default")
    if td:
        list_fields.append(("traditions_default", list(td)))
    tpb = src.get("traditions_per_book")
    if tpb:
        list_fields.append(("traditions_per_book", list(tpb)))
    # ρ.3 Phase C1 — per-book/chapter/verse hierarchical-customization fields.
    # Mirror the truthy-append pattern; these are list[str] on-disk so they
    # clone correctly when the source edition has them set.
    for _hf in (
        "note_families_on_per_book",
        "note_families_off_per_book",
        "note_families_on_per_chapter",
        "note_families_off_per_chapter",
        "popup_languages_per_chapter",
        "popup_languages_per_verse",
    ):
        _hv = src.get(_hf)
        if _hv:
            list_fields.append((_hf, list(_hv)))
    # mint-10 #high — the kind-gate LIST fields. Omitting these WAS the bug:
    # a clone with no enabled_categories/enabled_kinds enabled ZERO kinds and
    # therefore shipped 0 notes. Mirror the truthy-append pattern above.
    ek = src.get("enabled_kinds")
    if ek:
        list_fields.append(("enabled_kinds", list(ek)))
    ec = src.get("enabled_categories")
    if ec:
        list_fields.append(("enabled_categories", list(ec)))
    dk = src.get("disabled_kinds")
    if dk:
        list_fields.append(("disabled_kinds", list(dk)))

    if override_book_covers is not None:
        if override_book_covers:
            list_fields.append(("book_covers", override_book_covers))
    else:
        bc = src.get("book_covers")
        if bc:
            list_fields.append(("book_covers", list(bc)))

    for fname, items in list_fields:
        fields_text.append(f"    {fname}:")
        for item in items:
            sitem = str(item).replace('"', '\\"')
            fields_text.append(f'      - "{sitem}"')

    new_block = "\n".join(fields_text) + "\n"
    if not text.endswith("\n"):
        text += "\n"
    return text + new_block


# ---------------------------------------------------------------------
# Mutation handlers
# ---------------------------------------------------------------------


def api_create_edition_from_template(
    template_id: str,
    new_id: str,
    new_title: str,
) -> dict:
    """ψ.7-B — Clone a template into editions.yaml as a new edition.

    Returns the §9 standard dict shape:
      {"status": "ok", "edition_id": new_id, "edition": {...}}
      {"status": "error", "code": "...", "http": 4xx, "message": "..."}

    Surfaced at POST /api/editions/from-template with body
    {template_id, new_id, new_title}. Validates template exists,
    new_id format + uniqueness, new_title non-empty.

    Composes scripts.core.edition_templates.create_from_template,
    which handles atomic write + cache invalidation.
    """
    from scripts.core import edition_templates as et

    return et.create_from_template(
        template_id,
        new_id=new_id,
        new_title=new_title,
    )


@audit_log.audit_endpoint(action="save_edition")
def api_save_edition(edition_id: str, payload: dict) -> dict:
    """Persist a new enabled-kind state for one edition (μ.2)."""
    new_enabled_set = set(payload.get("enabled_kinds") or [])
    if not isinstance(new_enabled_set, set) or not all(isinstance(x, str) for x in new_enabled_set):
        return {"error": "enabled_kinds must be a list of strings"}

    editions_path = REPO / "content" / "editions.yaml"
    if not editions_path.is_file():
        return {"error": "editions.yaml missing"}

    editions = config.editions_by_id()
    if edition_id not in editions:
        return {"error": f"unknown edition: {edition_id}"}
    edition = editions[edition_id]

    known_kinds = {k["code"] for k in config.load_kinds()}
    unknown = new_enabled_set - known_kinds
    if unknown:
        return {"error": f"unknown kind(s): {sorted(unknown)}"}

    # The baseline MUST be phase/AI-gated (mint-9 #12): a max_phase-limited or
    # AI-disabled edition never ships the gated-out kinds, so they must not fall
    # into the computed disabled_kinds (which previously happened with a plain
    # category-only baseline, corrupting disabled_kinds for such editions).
    baseline = config.category_baseline_kinds(edition, config.load_kinds())
    new_enabled_kinds = sorted(new_enabled_set - baseline)
    new_disabled_kinds = sorted(baseline - new_enabled_set)

    text = editions_path.read_text(encoding="utf-8")
    try:
        new_text = _patch_edition_kind_lists(text, edition_id, new_enabled_kinds, new_disabled_kinds)
    except ValueError as e:
        return {"error": str(e)}

    notes_io.ensure_backup(editions_path)
    notes_io.atomic_write(editions_path, new_text)

    config.load_editions.cache_clear()
    from scripts.core import matrix as matrix_mod

    matrix_mod.compute_matrix.cache_clear()

    return {
        "ok": True,
        "edition": edition_id,
        "enabled_kinds": new_enabled_kinds,
        "disabled_kinds": new_disabled_kinds,
        "enabled_total": len(new_enabled_set),
    }


@audit_log.audit_endpoint(action="apply_kind_to_all_editions")
def api_apply_kind_to_all_editions(kind_code: str, *, enable: bool) -> dict:
    """Enable or disable `kind_code` in every edition in editions.yaml.

    Composes `api_save_edition` per edition (so each underlying write
    is atomic + backed up + cache-invalidated the same way it would
    be from the per-edition save flow)."""
    if not isinstance(kind_code, str) or not kind_code:
        return {"status": "error", "code": "invalid_input", "http": 400, "message": "kind_code is required"}
    known_kinds = {k["code"] for k in config.load_kinds()}
    if kind_code not in known_kinds:
        return {"status": "error", "code": "unknown_kind", "http": 400, "message": f"unknown kind: {kind_code}"}
    if not isinstance(enable, bool):
        return {"status": "error", "code": "invalid_input", "http": 400, "message": "enable must be a boolean"}

    editions = config.load_editions()
    if not editions:
        return {"status": "error", "code": "no_editions", "http": 503, "message": "no editions in editions.yaml"}

    from scripts.core.matrix import _enabled_kinds_for_edition

    all_kinds = config.load_kinds()

    plan = []
    for ed in editions:
        if not isinstance(ed, dict):
            continue
        ed_id = ed.get("id")
        if not ed_id:
            continue
        current = _enabled_kinds_for_edition(ed, all_kinds)
        was_enabled = kind_code in current
        new_set = (current | {kind_code}) if enable else (current - {kind_code})
        plan.append(
            {
                "edition_id": ed_id,
                "was_enabled": was_enabled,
                "now_enabled": kind_code in new_set,
                "new_set": new_set,
                "noop": was_enabled == (kind_code in new_set),
            }
        )

    results = []
    failures = []
    for p in plan:
        if p["noop"]:
            results.append(
                {
                    "edition_id": p["edition_id"],
                    "ok": True,
                    "noop": True,
                    "was_enabled": p["was_enabled"],
                    "now_enabled": p["now_enabled"],
                }
            )
            continue
        r = api_save_edition(
            p["edition_id"],
            {"enabled_kinds": sorted(p["new_set"])},
        )
        if r.get("ok"):
            results.append(
                {
                    "edition_id": p["edition_id"],
                    "ok": True,
                    "noop": False,
                    "was_enabled": p["was_enabled"],
                    "now_enabled": p["now_enabled"],
                }
            )
        else:
            err = r.get("error") or "unknown error"
            failures.append({"edition_id": p["edition_id"], "error": err})
            results.append(
                {
                    "edition_id": p["edition_id"],
                    "ok": False,
                    "error": err,
                }
            )

    return {
        "status": "ok",
        "kind": kind_code,
        "enable": enable,
        "total": len(plan),
        "changed": sum(1 for r in results if r.get("ok") and not r.get("noop")),
        "noop": sum(1 for r in results if r.get("noop")),
        "results": results,
        "failures": failures,
    }


@audit_log.audit_endpoint(action="clone_edition")
def api_clone_edition(payload: dict) -> dict:
    """Phase ν.4 — clone an existing edition into a new one."""
    if not isinstance(payload, dict):
        return {"error": "payload must be an object"}

    source_id = (payload.get("source_id") or "").strip()
    new_id = (payload.get("new_id") or "").strip()
    new_title = payload.get("new_title")
    clone_files = bool(payload.get("clone_files", False))

    if not source_id:
        return {"error": "source_id is required"}
    if not new_id:
        return {"error": "new_id is required"}
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", new_id):
        return {"error": (f"new_id must be lowercase kebab-case (letters/digits/dashes only): got {new_id!r}")}

    eds = config.editions_by_id()
    if source_id not in eds:
        return {"error": f"unknown source edition: {source_id!r}"}
    if new_id in eds:
        return {"error": f"edition already exists: {new_id!r}"}

    source = eds[source_id]

    from scripts.core import covers as _covers

    copied: list[Path] = []
    new_book_covers_encoded: list[str] | None = None
    new_main_path: str = source.get("cover_image", "")

    if clone_files:
        try:
            src_main = (source.get("cover_image") or "").strip()
            if src_main:
                src_path = REPO / "content" / src_main
                if src_path.is_file():
                    suffix = src_path.suffix.lstrip(".") or "jpg"
                    fmt = {"jpg": "jpeg"}.get(suffix.lower(), suffix.lower())
                    rel_new = _covers.storage_path_for_main(new_id, fmt)
                    abs_new = REPO / "content" / rel_new
                    abs_new.parent.mkdir(parents=True, exist_ok=True)
                    notes_io.atomic_write_bytes(abs_new, src_path.read_bytes())
                    copied.append(abs_new)
                    new_main_path = rel_new
            src_per_book = _covers.decode_book_covers(source.get("book_covers"))
            new_per_book: dict[str, str] = {}
            for code, src_rel in src_per_book.items():
                if not src_rel:
                    new_per_book[code] = ""
                    continue
                src_path = REPO / "content" / src_rel
                if not src_path.is_file():
                    new_per_book[code] = ""
                    continue
                suffix = src_path.suffix.lstrip(".") or "jpg"
                fmt = {"jpg": "jpeg"}.get(suffix.lower(), suffix.lower())
                rel_new = _covers.storage_path_for_book(new_id, code, fmt)
                abs_new = REPO / "content" / rel_new
                abs_new.parent.mkdir(parents=True, exist_ok=True)
                notes_io.atomic_write_bytes(abs_new, src_path.read_bytes())
                copied.append(abs_new)
                new_per_book[code] = rel_new
            new_book_covers_encoded = _covers.encode_book_covers(new_per_book)
        except OSError as e:
            for p in copied:
                try:
                    p.unlink()
                except OSError:
                    pass
            return {"error": f"failed to clone files: {e}"}

    yaml_path = REPO / "content" / "editions.yaml"
    try:
        text = yaml_path.read_text(encoding="utf-8")
        new_text = _append_cloned_edition(
            text,
            source_id,
            new_id,
            new_title or source.get("title", new_id),
            override_cover_image=new_main_path,
            override_book_covers=new_book_covers_encoded,
        )
        notes_io.ensure_backup(yaml_path)
        notes_io.atomic_write(yaml_path, new_text)
    except Exception as e:
        for p in copied:
            try:
                p.unlink()
            except OSError:
                pass
        return {"error": f"failed to write editions.yaml: {e}"}

    config.load_editions.cache_clear()
    from scripts.core import matrix as matrix_mod

    matrix_mod.compute_matrix.cache_clear()

    return {
        "ok": True,
        "source_id": source_id,
        "new_id": new_id,
        "files_cloned": len(copied),
    }


def _validate_keyed_list_field(
    field: str,
    raw,
    *,
    key_parts: int,
    valid_values: set[str],
    value_label: str,
    encode_fn,
) -> "tuple[list[str] | None, str | None]":
    """ρ.3 Phase C1 — DRY validator for the 6 per-book/chapter/verse fields.

    ``key_parts`` is the expected number of colon-separated segments in
    each map key:
      - 1 → book only          (note_families_{on,off}_per_book)
      - 2 → book:chapter       (note_families_{on,off}_per_chapter,
                                 popup_languages_per_chapter)
      - 3 → book:chapter:verse (popup_languages_per_verse)

    Parts 1.. must be positive integers.  Part 0 must be in
    ``config.books_by_code()``.  Values are validated against
    ``valid_values``, deduplicated (preserving order), and passed to
    ``encode_fn`` which returns the on-disk ``list[str]``.

    Returns ``(encoded_list, None)`` on success or ``(None, error_message)``
    on the first validation failure.
    """
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        return (None, f"{field} must be a mapping (dict), not {type(raw).__name__}")
    valid_books = set(config.books_by_code().keys())
    cleaned: dict[str, list[str]] = {}
    for key, values in raw.items():
        if not isinstance(key, str) or not key.strip():
            return (None, f"{field}: keys must be non-empty strings")
        key = key.strip()
        parts = key.split(":")
        if len(parts) != key_parts:
            expected = ":".join(["<book>"] + ["<n>"] * (key_parts - 1))
            return (
                None,
                f"{field}: key {key!r} has {len(parts)} part(s) but expected {key_parts} ({expected})",
            )
        book = parts[0]
        if book not in valid_books:
            return (None, f"{field}: unknown book code {book!r}")
        for idx in range(1, key_parts):
            seg = parts[idx]
            try:
                n = int(seg)
            except (TypeError, ValueError):
                part_name = "chapter" if idx == 1 else "verse"
                return (None, f"{field}: key {key!r} — {part_name} must be a positive integer, got {seg!r}")
            if n < 1:
                part_name = "chapter" if idx == 1 else "verse"
                return (None, f"{field}: key {key!r} — {part_name} must be ≥ 1, got {n}")
        if values is None:
            values = []
        if not isinstance(values, list):
            return (None, f"{field}[{key!r}] must be a list of {value_label}s")
        deduped: list[str] = []
        for v in values:
            if not isinstance(v, str):
                return (None, f"{field}[{key!r}] items must be strings, got {type(v).__name__}")
            s = v.strip()
            if not s:
                continue
            if s not in valid_values:
                return (
                    None,
                    f"{field}[{key!r}]: unknown {value_label} {s!r}; available: {sorted(valid_values)}",
                )
            if s not in deduped:
                deduped.append(s)
        cleaned[key] = deduped
    return (encode_fn(cleaned), None)


def api_preview_edition_changes(edition_id: str, payload: dict) -> dict:
    """Compute the field-by-field diff between the current edition
    record and the proposed payload, without persisting anything."""
    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}
    current = eds[edition_id]

    EDITABLE = {
        "title",
        "short_title",
        "target_audience",
        "notes",
        "verse_marker_glyph",
        "theme",
        "popup_translation",
        "cover_image",
        "verse_popups",
        "note_attribution_dedup",
        "note_group_by_category",
        "note_topic_dedup",
        "popup_languages_default",
        "popup_languages_per_book",
        "traditions_default",
        "traditions_per_book",
        "book_covers",
        "chapter_number_format",
        "chapter_number_decoration",
        "book_toc_ornament",
        "title_page_style",
        "cover_template",
        "verse_popup_style",
        "note_popup_style",
        # K-R6-6 — in-page verse-badge form ("chip" | "glyph+count");
        # absent = target default (chip on eink, glyph+count elsewhere).
        "marker_badge_style",
        "marker_style",
        "topical_index_source",
        "note_popup_split_cap",
        # K-R6-2 — popup-unit byte cap (estimated post-kepubify bytes; 0 =
        # off; unset = the calibrated 8,000 default).
        "note_popup_split_byte_cap",
        "reader_toc_collapsible",
        "reader_toc_default_open",
        # K-R2 — where the builder will read the EPUB ("everywhere" | "eink" |
        # "tablet" | "computer"); set by the wizard's reader-target step, gates
        # which optional features the UIs offer. Absent = everywhere (no-op).
        "target_reader",
        # K-R2-6 — keep/drop the closing colophon page (default keep).
        "closing_colophon",
        "enabled_reading_plans",
        "description",
        "dedication",
        # σ.4 — edition-identity fields (cover subtitle / "Your Edition" name + cover main title)
        "display_name",
        "cover_main_title",
        # ρ.3 Phase C1 — per-book/chapter/verse hierarchical-customization fields
        "note_families_on_per_book",
        "note_families_off_per_book",
        "note_families_on_per_chapter",
        "note_families_off_per_chapter",
        "popup_languages_per_chapter",
        "popup_languages_per_verse",
    }

    changes: list[dict] = []
    unchanged: list[str] = []
    unknown: list[str] = []

    for field, proposed in payload.items():
        if field not in EDITABLE:
            unknown.append(field)
            continue
        before = current.get(field)
        if isinstance(proposed, str) and isinstance(before, str):
            if proposed.strip() == before.strip():
                unchanged.append(field)
                continue
        elif proposed == before:
            unchanged.append(field)
            continue
        changes.append(
            {
                "field": field,
                "before": before,
                "after": proposed,
            }
        )

    result = {
        "edition_id": edition_id,
        "changes": changes,
        "unchanged": unchanged,
        "no_changes": len(changes) == 0,
        "field_count": len(payload),
    }
    if unknown:
        result["unknown_fields"] = unknown
    return result


@audit_log.audit_endpoint(action="save_edition_meta")
def api_save_edition_meta(edition_id: str, payload: dict) -> dict:
    """Update editable metadata for one edition (Phase ν.2)."""
    # Lazy imports of web.py-resident helpers. See module docstring.
    from scripts.web import _load_themes, _patch_yaml_entry, _patch_yaml_list_field, _validate_cover_path

    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}

    EDITABLE_TEXT = {
        "title",
        "short_title",
        "target_audience",
        "notes",
        "verse_marker_glyph",
        "theme",
        "popup_translation",
        "cover_image",
        "chapter_number_format",
        "chapter_number_decoration",
        "book_toc_ornament",
        "title_page_style",
        "cover_template",
        "verse_popup_style",
        "note_popup_style",
        # K-R6-6 — in-page verse-badge form ("chip" | "glyph+count");
        # absent = target default (chip on eink, glyph+count elsewhere).
        "marker_badge_style",
        "marker_style",
        "topical_index_source",
        # ψ.37-C: time_filter_ceiling — stored as text in YAML
        # ("null" or a year like "1900"); the YAML loader parses
        # unquoted digits into ints and "null"/empty into None.
        "time_filter_ceiling",
        # K-R4-2 — popup-unit split cap (stripped chars; 0 = off; unset =
        # the device-calibrated default). Stored as a YAML int like
        # time_filter_ceiling; validated below.
        "note_popup_split_cap",
        # K-R6-2 — popup-unit BYTE cap (estimated post-kepubify serialized
        # bytes; 0 = off; unset = the calibrated 8,000 default). Same storage
        # and validation pattern as note_popup_split_cap.
        "note_popup_split_byte_cap",
        # Free-text front-matter fields (builder-editable via /customize).
        "description",
        "dedication",
        # σ.4 — edition-identity fields surfaced on the /customize name card.
        # display_name = the cover subtitle + Your-Edition heading ("" → cover
        # shows only the main title, no subtitle); cover_main_title = the fixed
        # big cover line (default "HOLY BIBLE" when unset). Both feed the cover
        # compositor, so api_save_edition_meta caps their length below (σ.4.4)
        # to keep a pathological value from overrunning the cover frame.
        "display_name",
        "cover_main_title",
        # K-R2 — the wizard's reader-target pick (validated below).
        "target_reader",
    }
    EDITABLE_BOOL = {
        "verse_popups",
        "note_attribution_dedup",
        "note_group_by_category",
        "note_topic_dedup",
        "reader_toc_collapsible",
        "reader_toc_default_open",
        # K-R2-6 — keep/drop the closing colophon page (default keep).
        "closing_colophon",
        "enable_ai_notes",
    }

    if "theme" in payload:
        valid_theme_ids = {t["id"] for t in _load_themes()}
        if payload["theme"] not in valid_theme_ids:
            return {"error": f"unknown theme: {payload['theme']!r}"}

    if "chapter_number_format" in payload:
        from scripts.build_edition import CHAPTER_NUMBER_FORMATS

        v = (payload["chapter_number_format"] or "").strip()
        if v and v not in CHAPTER_NUMBER_FORMATS:
            return {"error": (f"unknown chapter_number_format: {v!r}; valid: {sorted(CHAPTER_NUMBER_FORMATS)}")}

    if "target_reader" in payload:
        # K-R2 — the wizard's reader-target pick. Empty/absent = everywhere.
        # kindle (turn-69 ①) = the Send-to-Kindle-safe build variant. The valid
        # set is the build's own TARGET_READERS (one-resolver rule — same
        # pattern as CHAPTER_NUMBER_FORMATS above).
        from scripts.build_edition import TARGET_READERS

        v = (payload["target_reader"] or "").strip()
        if v and v not in TARGET_READERS:
            return {"error": f"unknown target_reader: {v!r}; valid: {sorted(TARGET_READERS)}"}
        # round-7 in-passing fix: this line wrote payload["chapter_number_format"]
        # (copy-paste from the block above) — a wizard reader-target save was
        # CLOBBERING the edition's chapter-number format with "eink"/"tablet"/…,
        # sidestepping that field's own validation (it runs earlier).
        payload["target_reader"] = v
    if "chapter_number_decoration" in payload:
        from scripts.build_edition import CHAPTER_NUMBER_DECORATIONS

        v = (payload["chapter_number_decoration"] or "").strip()
        if v and v not in CHAPTER_NUMBER_DECORATIONS:
            return {"error": (f"unknown chapter_number_decoration: {v!r}; valid: {sorted(CHAPTER_NUMBER_DECORATIONS)}")}
        payload["chapter_number_decoration"] = v

    if "book_toc_ornament" in payload:
        from scripts.build_edition import BOOK_TOC_ORNAMENTS

        v = (payload["book_toc_ornament"] or "").strip()
        if v and v not in BOOK_TOC_ORNAMENTS:
            return {"error": (f"unknown book_toc_ornament: {v!r}; valid: {sorted(BOOK_TOC_ORNAMENTS)}")}
        payload["book_toc_ornament"] = v

    if "title_page_style" in payload:
        from scripts.build_edition import TITLE_PAGE_STYLES

        v = (payload["title_page_style"] or "").strip()
        if v and v not in TITLE_PAGE_STYLES:
            return {"error": (f"unknown title_page_style: {v!r}; valid: {sorted(TITLE_PAGE_STYLES)}")}
        payload["title_page_style"] = v

    if "cover_template" in payload:
        from scripts.core.covers import COVER_TEMPLATES

        v = (payload["cover_template"] or "").strip()
        if v and v not in COVER_TEMPLATES:
            return {"error": (f"unknown cover_template: {v!r}; valid: {sorted(COVER_TEMPLATES)}")}
        payload["cover_template"] = v

    if "verse_popup_style" in payload:
        from scripts.build_edition import VERSE_POPUP_STYLES

        v = (payload["verse_popup_style"] or "").strip()
        if v and v not in VERSE_POPUP_STYLES:
            return {"error": (f"unknown verse_popup_style: {v!r}; valid: {sorted(VERSE_POPUP_STYLES)}")}
        payload["verse_popup_style"] = v

    if "note_popup_style" in payload:
        from scripts.build_edition import NOTE_POPUP_STYLES

        v = (payload["note_popup_style"] or "").strip()
        if v and v not in NOTE_POPUP_STYLES:
            return {"error": (f"unknown note_popup_style: {v!r}; valid: {sorted(NOTE_POPUP_STYLES)}")}
        payload["note_popup_style"] = v

    if "marker_style" in payload:
        from scripts.build_edition import MARKER_STYLES

        v = (payload["marker_style"] or "").strip()
        if v and v not in MARKER_STYLES:
            return {"error": (f"unknown marker_style: {v!r}; valid: {sorted(MARKER_STYLES)}")}
        payload["marker_style"] = v

    if "marker_badge_style" in payload:
        from scripts.build_edition import MARKER_BADGE_STYLES

        v = (payload["marker_badge_style"] or "").strip()
        if v and v not in MARKER_BADGE_STYLES:
            return {"error": (f"unknown marker_badge_style: {v!r}; valid: {sorted(MARKER_BADGE_STYLES)}")}
        payload["marker_badge_style"] = v

    if "topical_index_source" in payload:
        from scripts.build_edition import TOPICAL_INDEX_SOURCES

        v = (payload["topical_index_source"] or "").strip()
        if v and v not in TOPICAL_INDEX_SOURCES:
            return {"error": (f"unknown topical_index_source: {v!r}; valid: {sorted(TOPICAL_INDEX_SOURCES)}")}
        payload["topical_index_source"] = v

    if "cover_image" in payload:
        err = _validate_cover_path(payload["cover_image"])
        if err:
            return {"error": err}

    if "popup_translation" in payload:
        v = payload["popup_translation"]
        if v is None:
            v = ""
        if not isinstance(v, str):
            return {"error": "popup_translation must be a string"}
        if v:
            from scripts.core import translations as _tx

            available = set(_tx.list_translations())
            if v not in available:
                return {"error": (f"unknown translation: {v!r}; available: {sorted(available) or 'none'}")}
        payload["popup_translation"] = v

    # ψ.37-C: time_filter_ceiling — None (no filter; default), or
    # int in [1500, 2100]. Year stored as a YAML int (unquoted).
    if "time_filter_ceiling" in payload:
        v = payload["time_filter_ceiling"]
        if v is None or v == "" or v == "null":
            # Clear the filter — patcher writes "null"
            payload["time_filter_ceiling"] = "null"
        else:
            try:
                v_int = int(v)
            except (TypeError, ValueError):
                return {"error": "time_filter_ceiling must be an integer year or null"}
            if v_int < 1500 or v_int > 2100:
                return {"error": (f"time_filter_ceiling out of range: {v_int} (expected 1500-2100)")}
            payload["time_filter_ceiling"] = str(v_int)

    # K-R4-2: note_popup_split_cap — unset/None/"" clears to the build's
    # calibrated default; otherwise an integer >= 0 (0 disables splitting).
    # Mirrors resolve_note_popup_split_cap's contract (the one resolver).
    if "note_popup_split_cap" in payload:
        v = payload["note_popup_split_cap"]
        if v is None or v == "" or v == "null":
            payload["note_popup_split_cap"] = "null"
        else:
            try:
                v_int = int(v)
            except (TypeError, ValueError):
                return {"error": "note_popup_split_cap must be an integer (stripped chars), 0, or null"}
            if v_int < 0:
                return {"error": f"note_popup_split_cap must be >= 0: {v_int}"}
            payload["note_popup_split_cap"] = str(v_int)

    # K-R6-2: note_popup_split_byte_cap — unset/None/"" clears to the build's
    # calibrated default (8,000 estimated post-kepubify bytes); otherwise an
    # integer >= 0 (0 disables the byte driver). Mirrors
    # resolve_note_popup_split_byte_cap's contract (the one resolver).
    if "note_popup_split_byte_cap" in payload:
        v = payload["note_popup_split_byte_cap"]
        if v is None or v == "" or v == "null":
            payload["note_popup_split_byte_cap"] = "null"
        else:
            try:
                v_int = int(v)
            except (TypeError, ValueError):
                return {"error": "note_popup_split_byte_cap must be an integer (kepub bytes), 0, or null"}
            if v_int < 0:
                return {"error": f"note_popup_split_byte_cap must be >= 0: {v_int}"}
            payload["note_popup_split_byte_cap"] = str(v_int)

    list_field_updates: dict[str, list[str]] = {}
    from scripts.build_edition import (
        ALL_POPUP_LANGUAGES,
        encode_per_book_languages,
        encode_per_book_traditions,
    )

    valid_langs = set(ALL_POPUP_LANGUAGES)

    if "popup_languages_default" in payload:
        v = payload["popup_languages_default"]
        if v is None:
            v = []
        if not isinstance(v, list):
            return {"error": "popup_languages_default must be a list of language ids"}
        cleaned: list[str] = []
        for item in v:
            if not isinstance(item, str):
                return {"error": "popup_languages_default items must be strings"}
            s = item.strip()
            if not s:
                continue
            if s not in valid_langs:
                return {"error": (f"unknown popup language: {s!r}; available: {sorted(valid_langs)}")}
            if s not in cleaned:
                cleaned.append(s)
        list_field_updates["popup_languages_default"] = cleaned

    if "traditions_default" in payload:
        from scripts.core.traditions import TRADITION_IDS

        v = payload["traditions_default"]
        if v is None:
            v = []
        if not isinstance(v, list):
            return {"error": "traditions_default must be a list of tradition ids"}
        cleaned = []
        for item in v:
            if not isinstance(item, str):
                return {"error": "traditions_default items must be strings"}
            s = item.strip()
            if not s:
                continue
            if s not in TRADITION_IDS:
                return {"error": (f"unknown tradition: {s!r}; available: {sorted(TRADITION_IDS)}")}
            if s not in cleaned:
                cleaned.append(s)
        list_field_updates["traditions_default"] = cleaned

    if "enabled_reading_plans" in payload:
        from scripts.core.reading_plans import list_plans

        v = payload["enabled_reading_plans"]
        if v is None:
            v = []
        if not isinstance(v, list):
            return {"error": "enabled_reading_plans must be a list of plan ids"}
        valid_plans = {p.id for p in list_plans()}
        cleaned = []
        for item in v:
            if not isinstance(item, str):
                return {"error": "enabled_reading_plans items must be strings"}
            s = item.strip()
            if not s:
                continue
            if s not in valid_plans:
                return {"error": (f"unknown reading plan: {s!r}; available: {sorted(valid_plans)}")}
            if s not in cleaned:
                cleaned.append(s)
        list_field_updates["enabled_reading_plans"] = cleaned

    if "traditions_per_book" in payload:
        from scripts.core.traditions import TRADITION_IDS

        v = payload["traditions_per_book"]
        if v is None:
            v = {}
        if not isinstance(v, dict):
            return {"error": ("traditions_per_book must be a mapping of book_code → list-of-tradition-ids")}
        valid_books = set(config.books_by_code().keys())
        cleaned_dict: dict[str, list[str]] = {}
        for code, traditions in v.items():
            if not isinstance(code, str) or not code.strip():
                return {"error": "traditions_per_book book codes must be non-empty strings"}
            code = code.strip()
            if code not in valid_books:
                return {"error": f"unknown book code: {code!r}"}
            if traditions is None:
                traditions = []
            if not isinstance(traditions, list):
                return {"error": (f"traditions_per_book[{code!r}] must be a list of tradition ids")}
            book_traditions: list[str] = []
            for t in traditions:
                if not isinstance(t, str):
                    return {"error": f"tradition id in {code!r} must be a string"}
                s = t.strip()
                if not s:
                    continue
                if s not in TRADITION_IDS:
                    return {"error": (f"unknown tradition in {code!r}: {s!r}; available: {sorted(TRADITION_IDS)}")}
                if s not in book_traditions:
                    book_traditions.append(s)
            cleaned_dict[code] = book_traditions
        list_field_updates["traditions_per_book"] = encode_per_book_traditions(cleaned_dict)

    if "popup_languages_per_book" in payload:
        v = payload["popup_languages_per_book"]
        if v is None:
            v = {}
        if not isinstance(v, dict):
            return {"error": ("popup_languages_per_book must be a mapping of book_code → list-of-language-ids")}
        valid_books = set(config.books_by_code().keys())
        cleaned_dict = {}
        for code, langs in v.items():
            if not isinstance(code, str) or not code.strip():
                return {"error": "popup_languages_per_book book codes must be non-empty strings"}
            code = code.strip()
            if code not in valid_books:
                return {"error": f"unknown book code: {code!r}"}
            if langs is None:
                langs = []
            if not isinstance(langs, list):
                return {"error": (f"popup_languages_per_book[{code!r}] must be a list of language ids")}
            book_langs: list[str] = []
            for L in langs:
                if not isinstance(L, str):
                    return {"error": f"language id in {code!r} must be a string"}
                s = L.strip()
                if not s:
                    continue
                if s not in valid_langs:
                    return {"error": (f"unknown popup language in {code!r}: {s!r}; available: {sorted(valid_langs)}")}
                if s not in book_langs:
                    book_langs.append(s)
            cleaned_dict[code] = book_langs
        list_field_updates["popup_languages_per_book"] = encode_per_book_languages(cleaned_dict)

    # ρ.3 Phase C1 — per-book/chapter/verse hierarchical fields.
    # All six share the same shape; _validate_keyed_list_field encodes the
    # common validation (key shape + value membership + dedup + encode).
    from scripts.build_edition import (
        _valid_symbol_tokens,
        encode_per_book_tokens,
        encode_per_chapter_tokens,
        encode_per_chapter_languages,
        encode_per_verse_languages,
    )

    valid_tokens = _valid_symbol_tokens()

    _KEYED_LIST_FIELDS: list[tuple[str, int, set, str, object]] = [
        # (field_name, key_parts, valid_values, value_label, encode_fn)
        ("note_families_on_per_book", 1, valid_tokens, "symbol token", encode_per_book_tokens),
        ("note_families_off_per_book", 1, valid_tokens, "symbol token", encode_per_book_tokens),
        ("note_families_on_per_chapter", 2, valid_tokens, "symbol token", encode_per_chapter_tokens),
        ("note_families_off_per_chapter", 2, valid_tokens, "symbol token", encode_per_chapter_tokens),
        ("popup_languages_per_chapter", 2, valid_langs, "popup language", encode_per_chapter_languages),
        ("popup_languages_per_verse", 3, valid_langs, "popup language", encode_per_verse_languages),
    ]
    for _field, _key_parts, _valid_vals, _val_label, _encode_fn in _KEYED_LIST_FIELDS:
        if _field in payload:
            _encoded, _err = _validate_keyed_list_field(
                _field,
                payload[_field],
                key_parts=_key_parts,
                valid_values=_valid_vals,
                value_label=_val_label,
                encode_fn=_encode_fn,
            )
            if _err is not None:
                return {"error": _err}
            list_field_updates[_field] = _encoded

    if "book_covers" in payload:
        from scripts.core.covers import encode_book_covers

        v = payload["book_covers"]
        if v is None:
            v = {}
        if not isinstance(v, dict):
            return {"error": ("book_covers must be a mapping of book_code → cover path string")}
        valid_books = set(config.books_by_code().keys())
        cleaned_covers: dict[str, str] = {}
        for code, path in v.items():
            if not isinstance(code, str) or not code.strip():
                return {"error": "book_covers book codes must be non-empty strings"}
            code = code.strip()
            if code not in valid_books:
                return {"error": f"unknown book code in book_covers: {code!r}"}
            if path is None:
                path = ""
            if not isinstance(path, str):
                return {"error": f"book_covers[{code!r}] must be a string path"}
            err = _validate_cover_path(path)
            if err:
                return {"error": f"book_covers[{code!r}]: {err}"}
            cleaned_covers[code] = path.strip()
        list_field_updates["book_covers"] = encode_book_covers(cleaned_covers)

    updates: dict[str, str] = {}
    for field in EDITABLE_TEXT:
        if field in payload:
            val = payload[field] or ""
            if isinstance(val, str):
                if field == "verse_marker_glyph" and len(val) > 4:
                    return {"error": "verse_marker_glyph max 4 chars"}
                if field in {"title", "short_title"} and len(val) > 200:
                    return {"error": f"{field} too long (max 200)"}
                if field in {"target_audience", "notes"} and len(val) > 500:
                    return {"error": f"{field} too long (max 500)"}
                if field in {"description", "dedication"} and len(val) > 4000:
                    return {"error": f"{field} too long (max 4000)"}
                # σ.4.4 — the two cover-identity fields feed the compositor; cap
                # them server-side (the console maxlength is the first line of
                # defence, this is the can't-be-bypassed second one) so no value
                # can push the cover text past its safe band.
                if field in {"display_name", "cover_main_title"} and len(val) > 80:
                    return {"error": f"{field} too long (max 80)"}
                if field == "popup_translation" and len(val) > 32:
                    return {"error": "popup_translation too long (max 32)"}
                updates[field] = val
            else:
                return {"error": f"{field} must be a string"}
    for field in EDITABLE_BOOL:
        if field in payload:
            v = payload[field]
            if v not in (True, False):
                return {"error": f"{field} must be true or false"}
            updates[field] = "true" if v else "false"
    if not updates and not list_field_updates:
        return {"error": "no updates supplied"}

    path = REPO / "content" / "editions.yaml"
    text = path.read_text(encoding="utf-8")
    try:
        if updates:
            text = _patch_yaml_entry(text, "id", edition_id, updates)
        for lf, items in list_field_updates.items():
            text = _patch_yaml_list_field(text, edition_id, lf, items)
    except ValueError as e:
        return {"error": str(e)}

    notes_io.ensure_backup(path)
    notes_io.atomic_write(path, text)
    config.load_editions.cache_clear()
    from scripts.core import matrix as matrix_mod

    matrix_mod.compute_matrix.cache_clear()
    return {
        "ok": True,
        "id": edition_id,
        "updated": list(updates.keys()) + list(list_field_updates.keys()),
    }


def _set_note_id_in_field(
    edition_id: str,
    nid: str,
    present: bool,
    *,
    field: str,
    anchor_field: str,
) -> dict:
    """ρ.3 — add or remove ``nid`` in one edition's ``field`` YAML list.

    Shared write engine for ``disabled_note_ids`` (force-off) and
    ``enabled_note_ids`` (force-on). ``present`` True ⇒ the id must be in the
    list afterward; False ⇒ it must be absent. The list is kept sorted +
    exceptions-only (rendered ``[]`` when empty) so unrelated editions stay
    byte-stable. On no-op returns ``{"unchanged": True, "count": N}`` WITHOUT
    writing; on a real change writes atomically (with a backup) and clears the
    edition + matrix caches, returning ``{"changed": True, "count": N}``.

    ``anchor_field`` is the sibling field whose line we insert BEFORE when the
    target list does not yet exist in the block (e.g. ``disabled_kinds``), so a
    brand-new list lands in a stable, valid position.

    Field-parameterised so both the legacy note-toggle path and the new unified
    note-override endpoint share one tested implementation (DRY). Validation of
    the edition id + note id is the caller's responsibility (done once).
    """
    eds = config.editions_by_id()
    edition = eds[edition_id]
    current = list(edition.get(field) or [])
    new_set = set(current)
    if present:
        new_set.add(nid)
    else:
        new_set.discard(nid)
    new_list = sorted(new_set)

    if new_list == sorted(current):
        return {"unchanged": True, "count": len(new_list)}

    path = REPO / "content" / "editions.yaml"
    text = path.read_text(encoding="utf-8")

    block_re = re.compile(
        rf"(^  - id: {re.escape(edition_id)}\n)(.*?)(?=^  - id:|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = block_re.search(text)
    if not m:
        return {"error": f"edition {edition_id} not found in YAML"}
    head, body = m.group(1), m.group(2)

    if new_list:
        new_block = f"    {field}:\n" + "\n".join(f'      - "{v}"' for v in new_list) + "\n"
    else:
        new_block = f"    {field}: []\n"

    # Group 1 = the field header line (consumes an inline `: []` too, since
    # `.*?\n` reaches the first newline); group 2 = the bulleted items (zero
    # for the empty form). Together they span the whole existing list block.
    list_re = re.compile(
        rf"^(    {re.escape(field)}:.*?\n)((?:      - [^\n]+\n)*)",
        re.MULTILINE,
    )
    if list_re.search(body):
        new_body = list_re.sub(new_block, body, count=1)
    else:
        # Prefer the sibling note-id field as anchor if it already exists (so
        # the two individual-level lists sit together), else the declared
        # anchor_field, else append to the block end.
        sibling = "enabled_note_ids" if field == "disabled_note_ids" else "disabled_note_ids"
        anchor_re = re.compile(rf"^(    (?:{re.escape(sibling)}|{re.escape(anchor_field)}):)", re.MULTILINE)
        am = anchor_re.search(body)
        new_body = (body[: am.start()] + new_block + body[am.start() :]) if am else (body + new_block)

    new_text = text[: m.start()] + head + new_body + text[m.end() :]
    notes_io.ensure_backup(path)
    notes_io.atomic_write(path, new_text)
    config.load_editions.cache_clear()
    from scripts.core import matrix as matrix_mod

    matrix_mod.compute_matrix.cache_clear()

    return {"changed": True, "count": len(new_list)}


@audit_log.audit_endpoint(action="save_note_toggle")
def api_save_note_toggle(edition_id: str, payload: dict) -> dict:
    """Add or remove a note ID from an edition's disabled_note_ids list (ρ.1)."""
    from scripts.web import html_ref_id_from_note_id, parse_note_id

    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}

    nid = payload.get("note_id", "")
    enabled = payload.get("enabled")
    if enabled not in (True, False):
        return {"error": "enabled must be true or false"}
    parsed = parse_note_id(nid)
    if not parsed:
        return {"error": f"invalid note_id format: {nid!r}"}

    books = config.books_by_code()
    if parsed["book"] not in books:
        return {"error": f"unknown book: {parsed['book']}"}

    html_ref = html_ref_id_from_note_id(nid, books)
    if not html_ref:
        return {"error": f"could not resolve note_id to HTML ref: {nid}"}

    # enabled=True ⇒ note SHIPS ⇒ remove from disabled_note_ids (present=False);
    # enabled=False ⇒ note OFF ⇒ add to disabled_note_ids (present=True).
    res = _set_note_id_in_field(
        edition_id,
        nid,
        present=not enabled,
        field="disabled_note_ids",
        anchor_field="disabled_kinds",
    )
    if "error" in res:
        return res
    if res.get("unchanged"):
        return {"ok": True, "edition": edition_id, "unchanged": True, "disabled_count": res["count"]}

    return {
        "ok": True,
        "edition": edition_id,
        "note_id": nid,
        "now_enabled": enabled,
        "disabled_count": res["count"],
    }


@audit_log.audit_endpoint(action="save_note_override")
def api_save_note_override(edition_id: str, payload: dict) -> dict:
    """ρ.3 Phase C2-5 — atomic three-state per-note override.

    ``payload = {note_id, state}`` with ``state ∈ {"default","on","off"}``:

    - ``"off"``     → add to ``disabled_note_ids``, remove from ``enabled_note_ids``.
    - ``"on"``      → add to ``enabled_note_ids``, remove from ``disabled_note_ids``
                      (force-on; the Phase-A build subtracts ``enabled_note_ids``
                      LAST so it wins over everything — §3.4 level 1).
    - ``"default"`` → remove from BOTH lists (revert to family resolution).

    The two lists stay mutually exclusive (a note is in at most one). Returns
    ``{"ok": True, "edition", "note_id", "state", "disabled_count", "enabled_count"}``
    (plus ``"unchanged": True`` when nothing changed); ``{"error": ...}`` for an
    unknown edition / bad note_id / bad state.
    """
    from scripts.web import html_ref_id_from_note_id, parse_note_id

    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}

    nid = payload.get("note_id", "")
    state = payload.get("state")
    if state not in ("default", "on", "off"):
        return {"error": "state must be one of: default, on, off"}

    parsed = parse_note_id(nid)
    if not parsed:
        return {"error": f"invalid note_id format: {nid!r}"}

    books = config.books_by_code()
    if parsed["book"] not in books:
        return {"error": f"unknown book: {parsed['book']}"}

    html_ref = html_ref_id_from_note_id(nid, books)
    if not html_ref:
        return {"error": f"could not resolve note_id to HTML ref: {nid}"}

    # Desired membership per list (mutually exclusive — at most one True).
    want_disabled = state == "off"
    want_enabled = state == "on"

    # Apply both field-writes (each idempotent; a no-op when already in the
    # target membership state). The order is harmless because each list is
    # independent and resolution subtracts enabled LAST regardless.
    changed = False
    for field, anchor, want in (
        ("disabled_note_ids", "disabled_kinds", want_disabled),
        ("enabled_note_ids", "disabled_kinds", want_enabled),
    ):
        res = _set_note_id_in_field(edition_id, nid, present=want, field=field, anchor_field=anchor)
        if "error" in res:
            return res
        if res.get("changed"):
            changed = True

    # Re-read authoritative counts (cache was cleared by any write above).
    eds = config.editions_by_id()
    edition = eds[edition_id]
    disabled_count = len(edition.get("disabled_note_ids") or [])
    enabled_count = len(edition.get("enabled_note_ids") or [])

    out = {
        "ok": True,
        "edition": edition_id,
        "note_id": nid,
        "state": state,
        "disabled_count": disabled_count,
        "enabled_count": enabled_count,
    }
    if not changed:
        out["unchanged"] = True
    return out


@audit_log.audit_endpoint(action="save_publisher_meta")
def api_save_publisher_meta(edition_id: str, payload: dict) -> dict:
    """Update one edition's publishing metadata (Phase π.1)."""
    from scripts.web import (
        PUBLISHING_LIST_FIELDS,
        PUBLISHING_TEXT_LIMITS,
        _patch_yaml_entry,
        _patch_yaml_list_field,
    )

    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}

    text_updates: dict[str, str] = {}
    list_updates: dict[str, list[str]] = {}

    for field, max_len in PUBLISHING_TEXT_LIMITS.items():
        if field not in payload:
            continue
        v = payload[field]
        if v is None:
            v = ""
        if not isinstance(v, str):
            return {"error": f"{field} must be a string"}
        if len(v) > max_len:
            return {"error": f"{field} too long (max {max_len})"}
        text_updates[field] = v

    for lf in PUBLISHING_LIST_FIELDS:
        if lf not in payload:
            continue
        v = payload[lf]
        if not isinstance(v, list):
            return {"error": f"{lf} must be a list"}
        items: list[str] = []
        for item in v:
            if not isinstance(item, str):
                return {"error": f"{lf} items must be strings"}
            s = item.strip()
            if not s:
                continue
            if len(s) > 300:
                return {"error": f"{lf} item too long (max 300)"}
            items.append(s)
        list_updates[lf] = items

    if not text_updates and not list_updates:
        return {"error": "no updates supplied"}

    path = REPO / "content" / "editions.yaml"
    text = path.read_text(encoding="utf-8")

    if text_updates:
        try:
            text = _patch_yaml_entry(text, "id", edition_id, text_updates)
        except ValueError as e:
            return {"error": str(e)}

    for lf, items in list_updates.items():
        text = _patch_yaml_list_field(text, edition_id, lf, items)

    notes_io.ensure_backup(path)
    notes_io.atomic_write(path, text)
    config.load_editions.cache_clear()
    from scripts.core import matrix as matrix_mod

    matrix_mod.compute_matrix.cache_clear()

    return {
        "ok": True,
        "id": edition_id,
        "updated_text": list(text_updates.keys()),
        "updated_lists": list(list_updates.keys()),
    }
