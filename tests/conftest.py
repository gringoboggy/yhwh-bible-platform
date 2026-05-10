"""Shared pytest fixtures for the E-Bible test suite."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ω.36 (2026-05-11) — production TTL=1.0 in tests too, now that
# Δ.6's fingerprint cache is path-tagged. The previous "TTL=0 +
# clear cache per test" pattern was correct but expensive: every
# test that touched corpus_index forced a fresh 87-file
# `os.stat` walk, and 8 xdist workers contending on the same
# notes/ dir's OS file cache produced 6-8s spikes on
# `api_matrix.cold` (the Δ-family wire flips multiplied the
# number of tests touching the index by ~10×). The path-tag fix
# in `_compute_fingerprint_cached` lets a real-corpus cache
# survive across tests within a worker (since they all resolve
# the same notes_dir) AND auto-invalidate when a test
# monkeypatches `paths.notes_dir` to a tmp_path (different path
# tag → recompute). Tests that mutate-then-query within a
# single test still need explicit `corpus_index.invalidate()`
# between mutations — same contract as production code that
# writes outside `notes_io.atomic_write`.
#
# We still close the per-process cached sqlite connection per
# test (Δ.4.1 attempt #5 fix): closes lingering Windows file
# handles so the next test's invalidate()/rebuild()/replace()
# cycle doesn't race.
@pytest.fixture(autouse=True)
def _disable_corpus_index_fingerprint_cache(monkeypatch):
    import sqlite3

    try:
        from scripts.core import corpus_index
    except ImportError:
        return
    # No more TTL=0 override — production default (1.0s) is now
    # safe in tests because the cache is path-tagged.
    if corpus_index._CACHED_CONN is not None:
        try:
            corpus_index._CACHED_CONN.close()
        except sqlite3.Error:
            pass
        corpus_index._CACHED_CONN = None
        corpus_index._CACHED_CONN_PATH = None


# Δ.4.1 attempt #5 (companion to Δ.9 production warm-up) — pre-build
# the corpus_index ONCE per pytest-xdist worker so the first test
# that touches it via the wire-flipped `compute_matrix()` doesn't
# pay the ~5s rebuild cost (which broke 3 perf budgets in attempt
# #4). With Δ.8 per-worker storage in place, each worker has its
# own `corpus.<worker>.sqlite`; this fixture builds it once at
# session start. Subsequent tests hit the warm sqlite + lru_cache
# path. Best-effort: any failure is swallowed and tests fall back
# to the file-walk paths.
@pytest.fixture(scope="session", autouse=True)
def _prebuilt_corpus_index_per_worker():
    try:
        from scripts.core import corpus_index

        corpus_index.rebuild()
    except Exception:  # noqa: BLE001 — best-effort warm-up; never poison test session
        pass
    yield


@pytest.fixture
def repo_root() -> Path:
    """Path to the project root."""
    return REPO_ROOT


@pytest.fixture
def sample_note_tuple():
    """A representative NOTES tuple for testing parsers / quality checks."""
    return (
        3,
        15,
        "",
        "bruise",
        "comm-rabbinic",
        "Curse on the serpent",
        "Note.",
        "<strong>Curse on the serpent.</strong> The serpent receives the only "
        "direct curse in the Eden narrative — neither the woman nor Adam is "
        "cursed; only the ground and the serpent.",
        {
            "sources": [{"author": "Rashi", "title": "Commentary on the Torah", "year": 1090, "license": "PD"}],
            "voice": "rabbinic",
        },
    )


@pytest.fixture
def sample_notes_module(tmp_path):
    """Write a minimal-but-valid notes module to a temp file and return its path."""
    text = '''"""Sample notes module for testing."""

NOTES = [
    (
        1, 1, '',
        'beginning',
        'comm',
        'In the beginning',
        'Note.',
        '<strong>In the beginning.</strong> The narrator opens with cosmogony.',
        {'voice': 'editorial'},
    ),
    (
        1, 2, '',
        '',
        'lang-hebrew',
        'Tohu wa-bohu',
        'Hebrew.',
        '<strong>Tohu wa-bohu.</strong> Formless and void.',
        {'sources': [{'author': 'Strong', 'year': 1890}], 'license': 'PD'},
    ),
]
'''
    p = tmp_path / "test_book.py"
    p.write_text(text, encoding="utf-8")
    return p


@pytest.fixture
def sample_html_with_marker():
    """Sample HTML containing a vnote marker + aside (used by filter tests).

    NB: filter_html's regex requires `class="..."` to be the FIRST attribute
    of the <a> and <aside>, mirroring the production HTML layout.
    """
    return """<html><body>
<p>Verse 1 text <a class="note-ref note-comm" id="ref-c001a" href="#note-c001a">◇</a></p>
<aside class="note note-comm" id="note-c001a" epub:type="footnote">
<p><a href="#ref-c001a" class="note-back">◇</a> <strong>A note.</strong> Body text here.</p>
</aside>
</body></html>"""
