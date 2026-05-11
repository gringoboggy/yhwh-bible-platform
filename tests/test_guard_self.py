"""Unit tests for the protected-paths guard in tests/conftest.py.

The guard's purpose: catch tests that inadvertently mutate
production files under content/sources/ or content/editions.yaml.
History: in ω.35-B.3b a monkeypatch regression caused tests to
write/delete to the real content/sources/ directory instead of
tmp_path, and `git add -A` swept the deletion of
strongs_hebrew.json into a commit.

These tests exercise the guard's snapshot/diff machinery
WITHOUT touching real protected paths — they call the snapshot
helper directly against tmp_path overrides, so the tests
themselves are guard-safe.
"""

from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

import pytest


@pytest.fixture
def reload_conftest():
    """Re-import conftest's snapshot helper for direct testing.
    The fixture itself is session-scoped autouse so we can't
    easily re-enter it; instead we call the underlying helper.
    """
    # The conftest module is loaded at pytest collection time;
    # tests can import its exported names directly.
    import sys

    tests_dir = Path(__file__).resolve().parent
    if str(tests_dir) not in sys.path:
        sys.path.insert(0, str(tests_dir))
    import conftest

    importlib.reload(conftest)
    return conftest


class TestProtectedPathsGuardSnapshot:
    """The snapshot helper computes SHA256 over a fixed set of
    files. Verify its inputs and outputs without touching real
    protected paths."""

    def test_snapshot_helper_returns_dict_of_hashes(self, reload_conftest):
        snap = reload_conftest._snapshot_protected_paths()
        # Returns a dict keyed by relative paths
        assert isinstance(snap, dict)
        # Values are 64-char hex strings (SHA256) or sentinels
        for v in snap.values():
            assert isinstance(v, str)
            # Either a SHA256 hex digest, "MISSING", or "DIR"
            assert v in ("MISSING", "DIR") or (len(v) == 64 and all(c in "0123456789abcdef" for c in v))

    def test_snapshot_includes_known_protected_files(self, reload_conftest):
        snap = reload_conftest._snapshot_protected_paths()
        # The list of expected files is content-dependent, but
        # at least one of these must be present in a healthy
        # checkout (Strong's lexicons + the fetcher config).
        present = set(snap.keys())
        # Normalize path separators for cross-OS comparison
        normalized = {p.replace("\\", "/") for p in present}
        # _fetchers.json is the smallest reliably-present file
        assert any("_fetchers.json" in p for p in normalized), (
            f"snapshot missing _fetchers.json; got: {sorted(normalized)[:10]}..."
        )

    def test_snapshot_is_idempotent(self, reload_conftest):
        # Two consecutive snapshots taken with no intervening
        # changes must be identical. Catches non-determinism
        # in the snapshot algorithm.
        snap1 = reload_conftest._snapshot_protected_paths()
        snap2 = reload_conftest._snapshot_protected_paths()
        assert snap1 == snap2

    def test_snapshot_skips_backups_subdir(self, reload_conftest):
        # The .backups/ subdir is a LEGITIMATE write target
        # (notes_io.atomic_write uses it for ensure_backup).
        # The snapshot must skip it so legitimate writes don't
        # poison the guard.
        snap = reload_conftest._snapshot_protected_paths()
        for path in snap:
            normalized = path.replace("\\", "/")
            assert "/.backups/" not in normalized, f"snapshot incorrectly included .backups/: {path}"

    def test_protected_dirs_list_is_non_empty(self, reload_conftest):
        # If the protected paths list is accidentally emptied,
        # the guard becomes a no-op without warning. Pin that
        # at least one path is registered.
        assert len(reload_conftest._PROTECTED_DIRS) >= 1
        assert all(isinstance(p, Path) for p in reload_conftest._PROTECTED_DIRS)


class TestProtectedPathsGuardDetectsChanges:
    """End-to-end-ish: invoke the snapshot before and after a
    simulated mutation in a tmp dir that's been temporarily
    added to the protected list, and verify the diff machinery
    flags the change correctly."""

    def test_snapshot_detects_added_file(self, reload_conftest, tmp_path, monkeypatch):
        # Redirect the protected dirs to tmp_path so the test
        # itself doesn't touch real protected paths.
        monkeypatch.setattr(reload_conftest, "_PROTECTED_DIRS", [tmp_path])
        monkeypatch.setattr(reload_conftest, "_PROTECTED_FILES", [])

        before = reload_conftest._snapshot_protected_paths()
        # Add a new file → should show up as "ADDED" in the diff
        (tmp_path / "new_file.json").write_text('{"key": "value"}')
        after = reload_conftest._snapshot_protected_paths()

        assert before != after
        added = sorted(k for k in after if k not in before)
        assert len(added) == 1
        assert "new_file.json" in added[0]

    def test_snapshot_detects_deleted_file(self, reload_conftest, tmp_path, monkeypatch):
        monkeypatch.setattr(reload_conftest, "_PROTECTED_DIRS", [tmp_path])
        monkeypatch.setattr(reload_conftest, "_PROTECTED_FILES", [])

        target = tmp_path / "soon_to_be_deleted.json"
        target.write_text("{}")
        before = reload_conftest._snapshot_protected_paths()
        target.unlink()
        after = reload_conftest._snapshot_protected_paths()

        assert before != after
        deleted = sorted(k for k in before if k not in after)
        assert len(deleted) == 1
        assert "soon_to_be_deleted.json" in deleted[0]

    def test_snapshot_detects_content_modification(self, reload_conftest, tmp_path, monkeypatch):
        monkeypatch.setattr(reload_conftest, "_PROTECTED_DIRS", [tmp_path])
        monkeypatch.setattr(reload_conftest, "_PROTECTED_FILES", [])

        target = tmp_path / "will_be_modified.json"
        target.write_text("{}")
        before = reload_conftest._snapshot_protected_paths()
        target.write_text('{"changed": true}')
        after = reload_conftest._snapshot_protected_paths()

        assert before != after
        modified = sorted(k for k in before if k in after and before[k] != after[k])
        assert len(modified) == 1
        assert "will_be_modified.json" in modified[0]

    def test_snapshot_passes_for_unchanged_content(self, reload_conftest, tmp_path, monkeypatch):
        # Re-writing the SAME content (same bytes) must NOT
        # be flagged. SHA256 is content-based; mtime alone
        # doesn't trigger the diff.
        monkeypatch.setattr(reload_conftest, "_PROTECTED_DIRS", [tmp_path])
        monkeypatch.setattr(reload_conftest, "_PROTECTED_FILES", [])

        target = tmp_path / "rewritten.json"
        target.write_text('{"same": true}')
        before = reload_conftest._snapshot_protected_paths()
        target.write_text('{"same": true}')  # same bytes
        after = reload_conftest._snapshot_protected_paths()

        assert before == after

    def test_protected_file_snapshot_works(self, reload_conftest, tmp_path, monkeypatch):
        # Test the _PROTECTED_FILES list (individual files,
        # not dirs) is also handled correctly.
        target = tmp_path / "single_protected.yaml"
        target.write_text("foo: bar")
        monkeypatch.setattr(reload_conftest, "_PROTECTED_DIRS", [])
        monkeypatch.setattr(reload_conftest, "_PROTECTED_FILES", [target])

        snap = reload_conftest._snapshot_protected_paths()
        # The target file should be in the snapshot
        keys = list(snap.keys())
        assert len(keys) == 1
        assert "single_protected.yaml" in keys[0]
        # And its hash matches the expected SHA256
        expected = hashlib.sha256(b"foo: bar").hexdigest()
        assert snap[keys[0]] == expected


class TestProtectedPathsGuardContract:
    """Pin the public-ish contract: which paths are protected,
    and what the documented behavior is. Catches accidental
    removal of a protected path from the list."""

    def test_content_sources_is_protected(self, reload_conftest):
        protected_str = [str(p) for p in reload_conftest._PROTECTED_DIRS]
        assert any("content" in p and "sources" in p for p in protected_str), (
            "content/sources/ must be in _PROTECTED_DIRS — that's the directory "
            "whose deletion triggered the original B.3b-fallout incident"
        )

    def test_editions_yaml_is_protected(self, reload_conftest):
        protected_str = [str(p) for p in reload_conftest._PROTECTED_FILES]
        assert any("editions.yaml" in p for p in protected_str), (
            "content/editions.yaml must be in _PROTECTED_FILES — the edition "
            "manifest is load-bearing for the entire build pipeline"
        )

    def test_backups_subdir_is_in_skip_list(self, reload_conftest):
        # The atomic_write mechanism writes legitimate backups
        # to .backups/. Pin that the guard skips this subdir
        # so legitimate writes don't poison the snapshot.
        assert ".backups" in reload_conftest._PROTECTED_DIR_SKIP_SUBDIRS


class TestProtectedPathsGuardCrlfNormalization:
    """ω.35-B.5-fallout — the guard now normalizes CRLF→LF before
    hashing. Reason: on Windows working trees, git checks out
    files with CRLF; Python writes LF (notes_io.atomic_write
    etc.). A legitimate test that writes via atomic_write then
    restores via shutil.copy can produce a file whose BYTES
    differ from the original (LF vs CRLF) but whose CONTENT is
    identical. Without normalization, the guard fires on this
    pure-line-ending churn — a false positive.

    Binary files (detected by null-byte in first 4KB) are NOT
    normalized — they're hashed as-is.
    """

    def test_crlf_vs_lf_text_hashes_match(self, reload_conftest):
        lf_bytes = b"line one\nline two\nline three\n"
        crlf_bytes = b"line one\r\nline two\r\nline three\r\n"
        h_lf = reload_conftest._normalize_for_hash(lf_bytes)
        h_crlf = reload_conftest._normalize_for_hash(crlf_bytes)
        assert h_lf == h_crlf, "CRLF + LF normalize to the same hash"

    def test_actual_content_diff_still_flagged(self, reload_conftest):
        original = b"line one\nline two\n"
        mutated = b"line one\nline THREE\n"
        h_orig = reload_conftest._normalize_for_hash(original)
        h_mut = reload_conftest._normalize_for_hash(mutated)
        assert h_orig != h_mut, "actual content drift is still caught"

    def test_binary_files_not_normalized(self, reload_conftest):
        # Binary files (with null bytes) MUST be hashed as-is.
        # CRLF-normalization would corrupt them (e.g. PNG / JPEG
        # uncommonly contain 0x0d 0x0a sequences that mean
        # something to the codec).
        binary = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100 + b"\r\nrest"
        out = reload_conftest._normalize_for_hash(binary)
        assert out == binary, "binary content must be unchanged"

    def test_snapshot_uses_normalized_hash(self, reload_conftest, tmp_path, monkeypatch):
        # End-to-end smoke: write the same content with LF and
        # then with CRLF; snapshots must be equal.
        monkeypatch.setattr(reload_conftest, "_PROTECTED_DIRS", [tmp_path])
        monkeypatch.setattr(reload_conftest, "_PROTECTED_FILES", [])

        target = tmp_path / "text_file.txt"

        target.write_bytes(b"hello\nworld\n")
        snap_lf = reload_conftest._snapshot_protected_paths()

        target.write_bytes(b"hello\r\nworld\r\n")
        snap_crlf = reload_conftest._snapshot_protected_paths()

        assert snap_lf == snap_crlf, "CRLF/LF differences must not register as drift"
