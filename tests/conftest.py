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
    try:
        from scripts.core import corpus_index
    except ImportError:
        return
    monkeypatch.setattr(corpus_index, "_FINGERPRINT_TTL_SEC", 0.0)
    corpus_index._FINGERPRINT_CACHE = None


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
