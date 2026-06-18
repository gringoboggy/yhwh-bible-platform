"""ρ.3 Phase A-6 — end-to-end build-integration tests for per-coordinate
symbol overrides.

Proves that the machinery wired in Tasks 1-5 propagates all the way through
a real EPUB build:

  Scenario 1 (per-book OFF):
    evangelical-reformed + ``note_families_off_per_book=["exo=xref"]``
    → gen xref notes PRESENT, exo xref notes ABSENT in the built EPUB.

  Scenario 2 (force-on override):
    Same edition + ``enabled_note_ids=["exo:1:12:xref-citation"]``
    → The single pinned exo note (ref-e0112) SURVIVES even though xref is
    off for all of exo (force-on subtracted last in build_one).

Both scenarios do a REAL build so the test is tagged ``slow`` and excluded
by ``-m "not slow"``.  A single build of evangelical-reformed (66-book
Protestant canon) takes ~2 minutes on the N95 dev box.

Corpus binding (confirmed against live corpus 2026-06-04):
  gen xref-citation notes: ref-g0101 … (164 total)
  exo xref-citation notes: ref-e0112 … (111 total)
  Force-on target: exo:1:12:xref-citation → ref-e0112
"""

from __future__ import annotations

import copy
import re
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

# ---------------------------------------------------------------------------
# Build helper (mirrors tests/test_byte_stability_gate.py)
# ---------------------------------------------------------------------------

_ED_ID = "evangelical-reformed"

# These ref-ids are bound to real corpus entries (verified 2026-06-04).
# gen ch 1 v 1: at least one xref-citation note survives in gen when xref is
# NOT disabled for gen.
# Popup/badge editions may omit inline ref- markers; aside ids are the ship oracle.
_GEN_XREF_NOTE_ID = "note-g0101"
# exo ch 1 v 12: first xref-citation note in exo — the force-on target.
_EXO_XREF_NOTE_ID_FORCE = "note-e0112"
# A second exo xref note we also assert is absent under the family-off rule.
_EXO_XREF_NOTE_ID_ABSENT = "note-e0117"

# Pattern that matches any ref-id for an exo xref-citation note.
# ref-e<cc><vv>[suffix] — id_prefix for exo is "e" (confirmed).
_EXO_XREF_ID_PAT = re.compile(r'id="(ref-e\d{4}[a-z]?)"')


def _build(ed_id: str, out_dir: Path, *, monkeypatch, extra_fields: dict | None = None) -> Path:
    """Build one edition into *out_dir*.

    When *extra_fields* is given the edition dict for *ed_id* is deep-copied
    and updated with those fields before building — this is how we inject
    per-coordinate overrides without touching editions.yaml.

    The monkeypatch replaces ``scripts.core.config.editions_by_id`` so
    ``build_one``'s very first line (``eds = config.editions_by_id()``) sees
    the patched dict.  ``load_editions`` is lru_cache-backed and is NOT
    patched — only the thin wrapper that converts the list to a dict is
    replaced, which is sufficient and avoids cache-clear side effects.

    ``force=True`` bypasses both the content-addressable cache lookup and the
    mtime incremental check so we always get a fresh build from the patched
    edition dict.
    """
    from scripts import build_edition as be
    from scripts.core import config

    out_dir.mkdir(parents=True, exist_ok=True)

    real_eds = config.editions_by_id()
    patched_ed = copy.deepcopy(real_eds[ed_id])
    # Default builds use marker_style=badge, which collapses per-note asides and
    # drops id="note-…" oracles. Force numbers so ρ.3 family-off assertions
    # can see individual xref asides in the built EPUB.
    patched_ed.setdefault("marker_style", "numbers")
    if extra_fields is not None:
        patched_ed.update(extra_fields)
    patched_eds = {**real_eds, ed_id: patched_ed}
    monkeypatch.setattr(config, "editions_by_id", lambda: patched_eds)

    be.build_one(ed_id, out_dir, "v28a-t", config.load_kinds(), dry_run=False, force=True)

    epubs = list(out_dir.glob("*.epub"))
    assert len(epubs) == 1, f"{ed_id}: expected exactly 1 EPUB, got {len(epubs)}"
    return epubs[0]


def _epub_xhtml_text(epub: Path) -> str:
    """Concatenate all XHTML/HTML content from the EPUB into one string."""
    parts: list[str] = []
    with zipfile.ZipFile(epub) as z:
        for name in sorted(z.namelist()):
            if name.endswith((".xhtml", ".html")):
                parts.append(z.read(name).decode("utf-8", errors="replace"))
    return "\n".join(parts)


def _note_ids_in(text: str) -> set[str]:
    """Extract shipped note aside ids (``id="note-…"``) from HTML text."""
    return set(re.findall(r'id="(note-[^"]+)"', text))


# ---------------------------------------------------------------------------
# Scenario 1: per-book xref OFF for exo
# ---------------------------------------------------------------------------


def test_per_book_off_strips_exo_xref_keeps_gen_xref(tmp_path, monkeypatch):
    """note_families_off_per_book=["exo=xref"] removes exo xref notes only.

    Assertions:
    - At least one gen xref aside (note-g0101) is present in the EPUB.
    - The two specific exo xref ref-ids (ref-e0112, ref-e0117) are ABSENT.
    - No exo xref-citation ref-id at all survives (xref category disabled
      for all of exo).
    """
    epub = _build(
        _ED_ID,
        tmp_path / "off",
        monkeypatch=monkeypatch,
        extra_fields={"note_families_off_per_book": ["exo=xref"]},
    )
    content = _epub_xhtml_text(epub)
    note_ids = _note_ids_in(content)

    # gen xref notes should still be present
    assert _GEN_XREF_NOTE_ID in note_ids, (
        f"Expected gen xref note {_GEN_XREF_NOTE_ID!r} to be present (xref is only disabled for exo, not gen)"
    )

    # The two named exo xref notes should be absent
    assert _EXO_XREF_NOTE_ID_FORCE not in note_ids, (
        f"Expected exo xref note {_EXO_XREF_NOTE_ID_FORCE!r} to be stripped "
        f"(xref disabled for exo via note_families_off_per_book)"
    )
    assert _EXO_XREF_NOTE_ID_ABSENT not in note_ids, (
        f"Expected exo xref note {_EXO_XREF_NOTE_ID_ABSENT!r} to be stripped "
        f"(xref disabled for exo via note_families_off_per_book)"
    )


# ---------------------------------------------------------------------------
# Scenario 2: per-book OFF + force-on for one pinned note
# ---------------------------------------------------------------------------


def test_force_on_note_id_survives_family_off(tmp_path, monkeypatch):
    """enabled_note_ids re-enables a single note despite its family being off.

    Same xref-off-for-exo setup as Scenario 1, but we also pin
    ``enabled_note_ids=["exo:1:12:xref-citation"]`` (→ ref-e0112).
    That note must SURVIVE even though xref is disabled for all of exo.
    The second exo xref note (ref-e0117) must still be ABSENT (not in
    enabled_note_ids).
    """
    epub = _build(
        _ED_ID,
        tmp_path / "force_on",
        monkeypatch=monkeypatch,
        extra_fields={
            "note_families_off_per_book": ["exo=xref"],
            "enabled_note_ids": ["exo:1:12:xref-citation"],
        },
    )
    content = _epub_xhtml_text(epub)
    note_ids = _note_ids_in(content)

    # gen xref still present (not affected by exo override)
    assert _GEN_XREF_NOTE_ID in note_ids, f"Expected gen xref note {_GEN_XREF_NOTE_ID!r} to be present"

    # The force-on note must survive despite xref being off for exo
    assert _EXO_XREF_NOTE_ID_FORCE in note_ids, (
        f"Expected force-on note {_EXO_XREF_NOTE_ID_FORCE!r} to be present "
        f"(pinned via enabled_note_ids despite xref disabled for exo)"
    )

    # The non-pinned exo xref note must still be absent
    assert _EXO_XREF_NOTE_ID_ABSENT not in note_ids, (
        f"Expected non-pinned exo xref note {_EXO_XREF_NOTE_ID_ABSENT!r} to be absent "
        f"(only the pinned note survives the force-on)"
    )
