"""Shared pytest fixtures for the E-Bible test suite."""

import hashlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ============================================================
# ω.35-B.3b-fallout guard — protect production data paths from
# accidental test mutation. See dev/CHANGELOG.md for the
# incident: a monkeypatch regression in B.3b caused tests to
# write/delete to the real content/sources/ directory instead
# of tmp_path, and `git add -A` swept the deletion of
# strongs_hebrew.json (1.9 MB Strong's Hebrew PD-source cache)
# into a commit. Restored from initial commit; this guard
# catches the next instance of that class of bug early.
# ============================================================

# Paths whose contents MUST NOT change during a test session.
# Listed explicitly rather than glob so additions are also
# caught (a stray file appearing under content/sources/ during
# a test is just as suspicious as a deletion).
_PROTECTED_DIRS = [
    REPO_ROOT / "content" / "sources",
]
_PROTECTED_FILES = [
    REPO_ROOT / "content" / "editions.yaml",
]

# Subdirectory names under protected dirs that are LEGITIMATE
# write targets (the backup mechanism atomic_write uses
# .backups/ — tests that exercise the backup path correctly
# create files there).
_PROTECTED_DIR_SKIP_SUBDIRS = {".backups"}


def _rel_key(p: Path) -> str:
    """Stable key for the snapshot dict. Prefers REPO_ROOT-
    relative for production paths; falls back to absolute for
    tmp paths (used by the guard's self-tests)."""
    try:
        return str(p.relative_to(REPO_ROOT))
    except ValueError:
        return str(p)


def _normalize_for_hash(data: bytes) -> bytes:
    """Normalize file content for content-equivalence hashing.

    The guard distinguishes CONTENT mutation from line-ending
    churn. On Windows working trees, Git checks out files with
    CRLF; Python writes LF (notes_io.atomic_write etc.). A
    legitimate write-then-restore sequence may produce a file
    whose BYTES differ from the original (LF vs CRLF) but whose
    CONTENT is identical. We normalize CRLF→LF before hashing
    so the guard doesn't fire on line-ending churn alone."""
    # Binary files (like images) should be hashed as-is. Detect
    # by null-byte presence in the first 4KB.
    if b"\x00" in data[:4096]:
        return data
    return data.replace(b"\r\n", b"\n")


def _snapshot_protected_paths() -> dict[str, str]:
    """Return {key: sha256_hex_or_sentinel} for every file
    under the protected dirs + every protected file.

    Uses SHA256 over file content (CRLF-normalized) so we catch
    content drift but not line-ending churn. Sentinel "MISSING"
    handles races where a file disappears mid-scan."""
    out: dict[str, str] = {}
    for d in _PROTECTED_DIRS:
        if not d.is_dir():
            continue
        for entry in d.iterdir():
            if entry.is_dir():
                if entry.name in _PROTECTED_DIR_SKIP_SUBDIRS:
                    continue
                # An unexpected subdirectory IS itself a change
                # worth surfacing — record it by name.
                out[_rel_key(entry) + "/"] = "DIR"
                continue
            try:
                out[_rel_key(entry)] = hashlib.sha256(_normalize_for_hash(entry.read_bytes())).hexdigest()
            except OSError:
                out[_rel_key(entry)] = "MISSING"
    for f in _PROTECTED_FILES:
        if not f.is_file():
            continue
        try:
            out[_rel_key(f)] = hashlib.sha256(_normalize_for_hash(f.read_bytes())).hexdigest()
        except OSError:
            out[_rel_key(f)] = "MISSING"
    return out


@pytest.fixture(scope="session", autouse=True)
def _protected_paths_guard():
    """Fail the pytest session if any test mutates a file
    under content/sources/ or other listed production paths.

    This is a session-scoped fixture: the snapshot fires at
    session start and the diff check fires at session
    teardown. Per-worker under xdist (each worker has its
    own session); failures still surface in the per-worker
    report so the regression is visible.

    The check uses SHA256 of file bytes — both content drift
    and accidental empty-writes are caught. False positives
    require an actual content change AND test code touching
    these paths, which is a real bug in the test.

    If you need to legitimately modify content under a
    protected path (e.g. a /save flow that legitimately
    updates editions.yaml at runtime), the production code
    path is fine — this fixture only fires during pytest
    sessions. Production runs are unaffected.
    """
    before = _snapshot_protected_paths()
    yield
    after = _snapshot_protected_paths()

    if before == after:
        return

    deleted = sorted(k for k in before if k not in after)
    added = sorted(k for k in after if k not in before)
    modified = sorted(k for k in before if k in after and before[k] != after[k])

    if not (deleted or added or modified):
        return  # changes cancelled out; nothing to report

    lines = [
        "",
        "=" * 72,
        "PROTECTED PATHS GUARD — TESTS MUTATED PRODUCTION DATA",
        "=" * 72,
        "",
        "Tests modified file(s) under protected production paths.",
        "This is the ω.35-B.3b-class regression that previously deleted",
        "content/sources/strongs_hebrew.json. Restore the file(s) from git",
        "and fix the test (most likely a monkeypatch missing the canonical",
        "module path — see dev/CHANGELOG.md B.3b for the pattern).",
        "",
    ]
    if deleted:
        lines.append(f"DELETED ({len(deleted)}):")
        lines.extend(f"    {p}" for p in deleted)
    if added:
        lines.append(f"ADDED ({len(added)}):")
        lines.extend(f"    {p}" for p in added)
    if modified:
        lines.append(f"MODIFIED ({len(modified)}):")
        lines.extend(f"    {p}" for p in modified)
    lines.append("")
    lines.append("=" * 72)

    raise AssertionError("\n".join(lines))


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
