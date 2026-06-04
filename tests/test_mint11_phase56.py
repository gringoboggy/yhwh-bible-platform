"""Mint-11 round-4 fixes — Phase 5 (byte-stability latents) + Phase 6
(annotation-count canon-scope).

Phase 5a — ``matter_pages.build_merged_topic_index`` orders its output
deterministically (sorted keys + a raw-string tiebreaker on casefold-equal
display names) so ``topical.xhtml`` is byte-stable across ``PYTHONHASHSEED``.
NOTE: on the *current* corpus the merge invariant (each group's display
casefolds to its own group key, and distinct groups have distinct keys) already
makes the output deterministic — these tests pin the ordering CONTRACT so a
future change to ``_norm_topic`` / the strip-set / display selection can't
reintroduce a hash-seed-dependent order.

Phase 5b — ``build_cache._referenced_translations`` resolves every default
popup witness to its real ``content/translations/<dir>/`` id (the registry
``translation_id``), not the registry key, so the content-cache key hashes the
data actually read instead of the ``<missing>`` token.

Phase 6 — the printed annotation-count override subtracts only the disabled
notes the matrix total actually counted (in canon AND of an enabled kind); the
old raw ``len(...)`` over-subtracted on both axes and could print a NEGATIVE
count for a tradition/time-filtered edition.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.core import build_cache, config, popup_versions  # noqa: E402
from scripts.matter_pages import build_merged_topic_index  # noqa: E402


# --------------------------------------------------------------------------
# Phase 5a — topical-index ordering contract
# --------------------------------------------------------------------------


class _Hit:
    def __init__(self, book, ch, vs):
        self.target_book = book
        self.target_chapter = ch
        self.target_verse = vs


class _StubSource:
    """Minimal stand-in for sources.NavesTopical / TorreyTopical."""

    def __init__(self, mapping):
        # mapping: {topic_name: [(book, ch, vs), ...]}
        self._m = mapping

    def topics(self):
        return list(self._m.keys())

    def verses_for(self, topic):
        return [_Hit(*r) for r in self._m.get(topic, [])]


_BOOK_ORDER = {"gen": 0, "exo": 1, "lev": 2, "psa": 18}


def test_merged_topic_index_sorted_by_casefold_then_raw():
    """Output is ordered by (display.casefold(), display) — the raw-string
    tiebreaker pins casefold-equal display names to a stable order."""
    nav = _StubSource({"GRACE": [("gen", 1, 1)], "abasement": [("gen", 2, 2)]})
    tor = _StubSource({"Grace": [("exo", 3, 3)], "Zeal": [("psa", 4, 4)]})
    out = build_merged_topic_index(nav, tor, {"gen", "exo", "lev", "psa"}, _BOOK_ORDER)
    displays = [e[0] for e in out]
    expected = sorted(displays, key=lambda d: (d.casefold(), d))
    assert displays == expected, displays
    # Determinism: a second call yields an identical structure.
    out2 = build_merged_topic_index(nav, tor, {"gen", "exo", "lev", "psa"}, _BOOK_ORDER)
    assert out == out2


def test_merged_topic_index_deterministic_across_hash_seeds():
    """Cross-launch determinism: build the merged index over the REAL Nave's +
    Torrey sources in two subprocesses with different PYTHONHASHSEED and assert
    a byte-identical result. The in-process byte-stability gate cannot catch a
    PYTHONHASHSEED dependency (the seed is fixed within one process)."""
    snippet = (
        "import hashlib, sys\n"
        f"sys.path.insert(0, {str(REPO)!r})\n"
        "from scripts.core import sources, config\n"
        "from scripts.matter_pages import build_merged_topic_index\n"
        "nav = sources.naves_topical()\n"
        "tor = sources.torrey_topical()\n"
        "order = {b['code']: i for i, b in enumerate(config.load_books())}\n"
        "out = build_merged_topic_index(nav, tor, None, order)\n"
        "print(hashlib.sha256(repr(out).encode('utf-8')).hexdigest())\n"
    )
    digests = []
    for seed in ("0", "1"):
        env = {**_clean_env(), "PYTHONHASHSEED": seed, "PYTHONUTF8": "1"}
        proc = subprocess.run(
            [sys.executable, "-c", snippet],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            env=env,
            cwd=str(REPO),
        )
        assert proc.returncode == 0, proc.stderr
        digests.append(proc.stdout.strip())
    assert digests[0] == digests[1], f"topical index differs across hash seeds: {digests}"


def _clean_env():
    import os

    return {k: v for k, v in os.environ.items() if k != "PYTHONHASHSEED"}


# --------------------------------------------------------------------------
# Phase 5b — popup-witness cache-key resolution
# --------------------------------------------------------------------------


def test_referenced_translations_resolves_default_witnesses_to_existing_dirs():
    """All five default popup witnesses must resolve to a real
    content/translations/<dir>/ id, not the registry key (which hashes
    '<missing>')."""
    edition = {"popup_languages_default": list(popup_versions.DEFAULT_POPUP_WITNESSES)}
    refs = build_cache._referenced_translations(edition)
    tx_root = REPO / "content" / "translations"
    for tx_id in refs:
        assert (tx_root / tx_id).is_dir(), f"{tx_id} -> missing content/translations/{tx_id}/"
    # The four previously-broken witnesses must now map to their translation_id dirs.
    assert "lxx-swete-greek" in refs
    assert "byzantine-greek" in refs
    assert "vulgate-clementine" in refs
    assert "arabic-vandyke" in refs
    # The registry KEYS must NOT leak through (they have no data dir).
    for key in ("lxx-greek", "greek-nt", "vulgate", "arabic"):
        assert key not in refs, f"raw registry key {key} leaked into referenced translations"


# --------------------------------------------------------------------------
# Phase 6 — annotation-count canon + enabled-kind scope
# --------------------------------------------------------------------------
#
# RETIRED (σ.6.2, 2026-06-04): the printed annotation count no longer uses the
# mint-9 #8 / mint-11 P6 ``annotation_count_override`` (matrix total minus the
# in-scope disabled ref-ids). The copyright page now reads
# ``edition_stats.resolved_note_counts`` directly — which honors the FULL ρ.3
# hierarchy (per-book/chapter/note overrides) AND the base-HTML coverage gate,
# strictly subsuming the old correction. The override param +
# ``build_edition._count_in_scope_disabled_ref_ids`` were deleted, so the three
# Phase-6 tests that pinned them were removed with this change. The build-accurate
# count is now pinned by ``tests/test_edition_stats.py`` (resolved_note_counts +
# the slow built-EPUB cross-check) and ``tests/test_mint9_phase3.py`` (copyright
# count == resolved total == legend category count).


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
