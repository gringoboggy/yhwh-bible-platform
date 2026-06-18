"""ρ.3 Phase B-4 — end-to-end build-integration test for per-verse popup
language override.

Proves that ``popup_languages_per_verse`` propagates all the way through
a real EPUB build, changing exactly the targeted verse's popup aside while
leaving sibling verses intact.

Scenario (single build):
  evangelical-reformed + ``popup_languages_default=["wlc","lxx-greek"]``
                + ``popup_languages_per_verse=["gen:1:1=wlc"]``

  Gen 1:1 aside  → contains vnote-hebrew, NOT vnote-greek   (per-verse override)
  Gen 1:2 aside  → contains BOTH vnote-hebrew AND vnote-greek (default)

Confirmed content classes (scripts/build_edition.py POPUP_LANGUAGES):
  wlc       → content_class "vnote-hebrew"
  lxx-greek → content_class "vnote-greek"

Vnote aside ids use the BOOK CODE (not id_prefix): ``vnote-gen-1-1`` and
``vnote-gen-1-2`` (confirmed by inspecting a real built EPUB; the id_prefix
"g" is for ref-ids such as "ref-g0101", not for vnote asides).

This test is tagged ``slow`` (real EPUB build, ~1.5-2 min on the N95 box).
"""

from __future__ import annotations

import copy
import re
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

# ---------------------------------------------------------------------------
# Build helper — reuses the exact same pattern as test_hierarchical_symbols_build
# ---------------------------------------------------------------------------

_ED_ID = "evangelical-reformed"


def _build(ed_id: str, out_dir: Path, *, monkeypatch, extra_fields: dict | None = None) -> Path:
    """Build one edition into *out_dir*, optionally patching edition fields.

    Mirrors the harness in ``tests/test_hierarchical_symbols_build.py``:
    monkeypatches ``config.editions_by_id`` to inject extra fields without
    touching editions.yaml; builds with ``force=True`` to bypass the cache.
    """
    from scripts import build_edition as be
    from scripts.core import config

    out_dir.mkdir(parents=True, exist_ok=True)

    if extra_fields is not None:
        real_eds = config.editions_by_id()
        patched_ed = copy.deepcopy(real_eds[ed_id])
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


def _extract_aside(content: str, aside_id: str) -> str:
    """Extract the body of the vnote aside with the given id attribute value.

    Returns the matched text (including the closing ``</aside>``), or an
    empty string if the aside is not found.
    """
    pat = re.compile(
        rf'id="{re.escape(aside_id)}"(.*?)</aside>',
        re.DOTALL,
    )
    m = pat.search(content)
    return m.group(0) if m else ""


# ---------------------------------------------------------------------------
# Content-class constants (confirmed against POPUP_LANGUAGES, 2026-06-04)
# ---------------------------------------------------------------------------

_CLASS_HEBREW = "vnote-hebrew"  # wlc
_CLASS_GREEK = "vnote-greek"  # lxx-greek

# vnote aside ids for gen ch 1 vs 1 and gen ch 1 vs 2.
# The aside id uses the BOOK CODE (not id_prefix): "vnote-gen-1-1"
# (confirmed by inspecting a real built EPUB — the id_prefix "g" is for
# cross-reference ref-ids such as "ref-g0101", not for vnote asides).
_ASIDE_GEN_1_1 = "vnote-gen-1-1"
_ASIDE_GEN_1_2 = "vnote-gen-1-2"


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------


def test_per_verse_popup_override_changes_one_verse(tmp_path, monkeypatch):
    """popup_languages_per_verse["gen:1:1=wlc"] removes Greek from gen 1:1 only.

    Setup:
      - popup_languages_default = ["wlc", "lxx-greek"]   → every verse gets Hebrew+Greek
      - popup_languages_per_verse = ["gen:1:1=wlc"]       → gen 1:1 gets Hebrew only

    Assertions:
      gen 1:1 aside: contains "vnote-hebrew", does NOT contain "vnote-greek"
      gen 1:2 aside: contains BOTH "vnote-hebrew" AND "vnote-greek"
    """
    epub = _build(
        _ED_ID,
        tmp_path / "popup_override",
        monkeypatch=monkeypatch,
        extra_fields={
            "popup_languages_default": ["wlc", "lxx-greek"],
            "popup_languages_per_verse": ["gen:1:1=wlc"],
        },
    )
    content = _epub_xhtml_text(epub)

    aside_1_1 = _extract_aside(content, _ASIDE_GEN_1_1)
    aside_1_2 = _extract_aside(content, _ASIDE_GEN_1_2)

    assert aside_1_1, (
        f"Expected to find vnote aside id={_ASIDE_GEN_1_1!r} in the EPUB — "
        f"check that gen 1:1 is present in evangelical-reformed and that the aside id "
        f"format is correct (book code 'gen' → vnote-gen-1-1)"
    )
    assert aside_1_2, (
        f"Expected to find vnote aside id={_ASIDE_GEN_1_2!r} in the EPUB — "
        f"check that gen 1:2 is present in evangelical-reformed"
    )

    # gen 1:1 — per-verse override → Hebrew only, Greek stripped
    assert _CLASS_HEBREW in aside_1_1, (
        f"gen 1:1 aside should contain {_CLASS_HEBREW!r} "
        f"(wlc is in the per-verse override 'gen:1:1=wlc')\n"
        f"Aside text: {aside_1_1[:500]!r}"
    )
    assert _CLASS_GREEK not in aside_1_1, (
        f"gen 1:1 aside should NOT contain {_CLASS_GREEK!r} "
        f"(lxx-greek was removed by per-verse override 'gen:1:1=wlc')\n"
        f"Aside text: {aside_1_1[:500]!r}"
    )

    # gen 1:2 — falls through to default → both Hebrew and Greek present
    assert _CLASS_HEBREW in aside_1_2, (
        f"gen 1:2 aside should contain {_CLASS_HEBREW!r} "
        f"(wlc is in popup_languages_default)\n"
        f"Aside text: {aside_1_2[:500]!r}"
    )
    assert _CLASS_GREEK in aside_1_2, (
        f"gen 1:2 aside should contain {_CLASS_GREEK!r} "
        f"(lxx-greek is in popup_languages_default, no per-verse override for gen 1:2)\n"
        f"Aside text: {aside_1_2[:500]!r}"
    )


def test_per_verse_override_alone_runs_the_vnote_pass(tmp_path, monkeypatch):
    """Round-5 audit Phase-0 regression lock for ``needs_vnote_pass``.

    Bug (now fixed, build_edition.py ~3917): the gate that decides whether the
    popup-language pass runs checked only ``popup_languages_default`` /
    ``_per_book``. An edition whose ONLY popup config was ``_per_chapter`` or
    ``_per_verse`` was silently SKIPPED → the per-verse override never applied.

    This locks the fix: with the default cleared to ``None``, the ONLY thing
    that can trigger the pass is the per-verse override. If the gate regressed,
    no vnote asides are emitted and the first assertion fails.

    Setup:
      - popup_languages_default = None        (so default/per-book can't trigger it)
      - popup_languages_per_verse = ["gen:1:1=wlc"]
    Expect:
      gen 1:1 → wlc only (Hebrew; override applied ⇒ the pass ran)
      gen 1:2 → DEFAULT_POPUP_WITNESSES = wlc+lxx-greek+… ⇒ Hebrew AND Greek
    """
    epub = _build(
        _ED_ID,
        tmp_path / "per_verse_only",
        monkeypatch=monkeypatch,
        extra_fields={
            "popup_languages_default": None,
            "popup_languages_per_verse": ["gen:1:1=wlc"],
        },
    )
    content = _epub_xhtml_text(epub)
    aside_1_1 = _extract_aside(content, _ASIDE_GEN_1_1)
    aside_1_2 = _extract_aside(content, _ASIDE_GEN_1_2)

    assert aside_1_1, (
        f"No vnote aside id={_ASIDE_GEN_1_1!r} — with the default cleared, the per-verse "
        f"override is the ONLY trigger; a missing aside means the needs_vnote_pass gate "
        f"skipped this per-verse-only edition (the regressed bug)."
    )
    assert aside_1_2, f"Expected vnote aside id={_ASIDE_GEN_1_2!r}"

    # gen 1:1 — per-verse override → Hebrew only (proves the pass ran + pruned)
    assert _CLASS_HEBREW in aside_1_1, f"gen 1:1 should contain {_CLASS_HEBREW!r}\n{aside_1_1[:400]!r}"
    assert _CLASS_GREEK not in aside_1_1, (
        f"gen 1:1 should be wlc-only; Greek present ⇒ the per-verse override didn't apply\n{aside_1_1[:400]!r}"
    )
    # gen 1:2 — no override, default cleared → DEFAULT_POPUP_WITNESSES (Hebrew + Greek)
    assert _CLASS_HEBREW in aside_1_2, f"gen 1:2 should contain {_CLASS_HEBREW!r}\n{aside_1_2[:400]!r}"
    assert _CLASS_GREEK in aside_1_2, f"gen 1:2 should contain {_CLASS_GREEK!r}\n{aside_1_2[:400]!r}"
