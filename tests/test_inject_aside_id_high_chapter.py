"""Regression: aside-id regex must parse chapters >=100 (findings H3/M13/M9).

An aside id is ``note-{prefix}{ch:02d}{v:02d}{suffix}``, so ch=100 renders as
``note-1e10001`` (the chapter digits run to 3+ chars while the verse stays a
fixed 2). The old fixed-width chapter group ``(\\d{2})`` mis-parsed that string
(it read ch=10, v=00), so 1En chapters 100-108 were never matched by
``inject.find_aside_insertion_point`` (mis-ordered asides) nor counted by
``coverage.count_injected``. The fix makes the chapter group ``(\\d+)`` while a
trailing ``(\\d{2})`` keeps the verse exactly 2 digits.

These tests pin the regex contract directly (NO build / inject / coverage run
against epub_working/).
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts import inject  # noqa: E402


def _aside_id(prefix, ch, v, suffix=""):
    """Reproduce the id-format inject/coverage write: {prefix}{ch:02d}{v:02d}{s}."""
    return f"note-{prefix}{ch:02d}{v:02d}{suffix}"


def _aside_open(prefix, ch, v, suffix=""):
    """A full opening tag so inject._aside_existing_re (which requires the
    ``<aside class="note ...">`` prefix) can match."""
    return f'<aside class="note note-comm" id="{_aside_id(prefix, ch, v, suffix)}" epub:type="footnote">'


class TestInjectAsideExistingRe:
    def test_chapter_100_parses(self):
        prefix = "1e"
        tag = _aside_open(prefix, 100, 1)
        assert _aside_id(prefix, 100, 1) == "note-1e10001"
        m = inject._aside_existing_re(prefix).search(tag)
        assert m is not None
        assert m.group(1) == "100"
        assert m.group(2) == "01"
        assert int(m.group(1)) == 100
        assert int(m.group(2)) == 1

    def test_chapter_99_still_parses(self):
        prefix = "1e"
        tag = _aside_open(prefix, 99, 1)
        assert _aside_id(prefix, 99, 1) == "note-1e9901"
        m = inject._aside_existing_re(prefix).search(tag)
        assert m is not None
        assert m.group(1) == "99"
        assert m.group(2) == "01"

    def test_low_chapter_parses(self):
        prefix = "1e"
        tag = _aside_open(prefix, 5, 12)
        m = inject._aside_existing_re(prefix).search(tag)
        assert m is not None
        assert m.group(1) == "05"
        assert m.group(2) == "12"

    def test_chapter_108_with_suffix(self):
        prefix = "1e"
        tag = _aside_open(prefix, 108, 7, "a")
        m = inject._aside_existing_re(prefix).search(tag)
        assert m is not None
        assert m.group(1) == "108"
        assert m.group(2) == "07"
        assert m.group(3) == "a"

    def test_helper_is_cached(self):
        # Same prefix returns the identical compiled object (lru_cache hit).
        assert inject._aside_existing_re("1e") is inject._aside_existing_re("1e")


class TestCoverageCountPattern:
    """coverage.count_injected uses its own (intentionally broader) bare-id
    pattern; pin that it too parses chapters >=100 with the (\\d+)(\\d{2}) split."""

    @staticmethod
    def _coverage_pat(id_prefix):
        return re.compile(rf'id="note-{re.escape(id_prefix)}(\d+)(\d{{2}})([a-z]?)"')

    def test_coverage_pattern_parses_chapter_100(self):
        pat = self._coverage_pat("1e")
        m = pat.search(f'id="{_aside_id("1e", 100, 1)}"')
        assert m is not None
        assert m.group(1) == "100"
        assert m.group(2) == "01"

    def test_coverage_pattern_parses_chapter_99(self):
        pat = self._coverage_pat("1e")
        m = pat.search(f'id="{_aside_id("1e", 99, 1)}"')
        assert m is not None
        assert m.group(1) == "99"
        assert m.group(2) == "01"

    def test_coverage_pattern_parses_low_chapter(self):
        pat = self._coverage_pat("1e")
        m = pat.search(f'id="{_aside_id("1e", 5, 3)}"')
        assert m is not None
        assert m.group(1) == "05"
        assert m.group(2) == "03"
