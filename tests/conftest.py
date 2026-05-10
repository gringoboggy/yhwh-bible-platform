"""Shared pytest fixtures for the E-Bible test suite."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


# Δ.6 — disable the corpus_index fingerprint TTL cache during tests
# by default. Tests routinely mutate the corpus and immediately
# query (e.g. write a notes file then call `rebuild()`); the
# production TTL=1.0s cache would return stale data inside that
# window. The cache is correct-by-construction in production where
# `notes_io.atomic_write` callers can pair with
# `corpus_index.invalidate()` to force freshness, but test helpers
# write notes directly. Setting TTL≤0 makes the cache invisible to
# every test by default. Tests that specifically exercise the
# cache (TestDelta6FingerprintCache) re-set TTL>0 via their own
# monkeypatch and reset module state explicitly — the local
# monkeypatch takes precedence.
@pytest.fixture(autouse=True)
def _disable_corpus_index_fingerprint_cache(monkeypatch):
    import sqlite3

    try:
        from scripts.core import corpus_index
    except ImportError:
        return
    monkeypatch.setattr(corpus_index, "_FINGERPRINT_TTL_SEC", 0.0)
    corpus_index._FINGERPRINT_CACHE = None
    # Δ.4.1 attempt #5 — also close any lingering cached sqlite
    # connection so the next test's invalidate()/rebuild()/replace()
    # cycle doesn't race with a still-held file handle on Windows.
    # Production keeps the connection cached for performance; tests
    # need fresh handles to avoid PermissionError on the cross-test
    # rebuild→replace path.
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
