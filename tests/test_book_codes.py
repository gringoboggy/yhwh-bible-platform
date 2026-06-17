"""Unified book-code canonicalization — API/CLI/config resolver."""

from __future__ import annotations

import pytest

from scripts.core.book_codes import BOOK_CODE_ALIASES, canonical_book_code
from scripts.core import config
from scripts import web_notes


@pytest.mark.parametrize(
    "legacy,canon",
    [
        ("joh", "jhn"),
        ("ps", "psa"),
        ("jas", "jam"),
        ("mar", "mrk"),
        ("jol", "joe"),
        ("ezk", "eze"),
        ("nam", "nah"),
        ("php", "phi"),
    ],
)
def test_canonical_book_code_legacy_aliases(legacy: str, canon: str) -> None:
    assert canonical_book_code(legacy) == canon
    assert config.resolve_book_code(legacy) == canon


def test_canonical_book_code_passthrough() -> None:
    assert canonical_book_code("gen") == "gen"
    assert canonical_book_code("1en") == "1en"


def test_get_book_accepts_legacy_alias() -> None:
    book = config.get_book("joh")
    assert book["code"] == "jhn"


def test_sources_normalize_delegates_to_canonical() -> None:
    from scripts.core.sources import _normalize_book_code

    for legacy, canon in BOOK_CODE_ALIASES.items():
        assert _normalize_book_code(legacy) == canon


def test_torrey_legacy_map_is_the_central_alias_table() -> None:
    from scripts.extract_torrey_ccel import _LEGACY_TO_CANON

    assert _LEGACY_TO_CANON is BOOK_CODE_ALIASES


def test_api_notes_legacy_alias_joh() -> None:
    result = web_notes.api_notes("joh")
    assert "error" not in result
    assert result["book"] == "jhn"
    assert result["notes"]


def test_api_preview_legacy_alias_php() -> None:
    result = web_notes.api_preview("ethiopian-tewahedo", "php", 1)
    assert result["status"] == "ok"
    assert "html" in result and result["html"]


def test_build_my_bible_legacy_alias_joh() -> None:
    from scripts.web_editions import api_build_my_bible

    result = api_build_my_bible("catholic-study", book="joh")
    assert "error" not in result
    assert result["book"]["code"] == "jhn"


def test_build_tracker_legacy_alias_joh() -> None:
    from scripts.web_editions import api_build_tracker_book

    result = api_build_tracker_book("catholic-study", "joh")
    assert result.get("http") != 404
    assert "notes" in result


def test_sample_html_legacy_alias_joh() -> None:
    from scripts.web_content import api_sample_html

    result = api_sample_html("catholic-study", "joh", 1, 1)
    assert result["status"] == "ok"
    assert result["book"] == "jhn"
