"""API/config book-code alias normalization (round-8 Phase 4)."""

from __future__ import annotations

from scripts.core import config


def test_get_book_resolves_legacy_alias():
    assert config.get_book("joh")["code"] == "jhn"
    assert config.get_book("jas")["code"] == "jam"


def test_validate_keyed_list_field_accepts_legacy_book_alias():
    from scripts.api.editions import _validate_keyed_list_field
    from scripts.build_edition import encode_per_book_tokens

    valid_tokens = {"◈", "★"}
    encoded, err = _validate_keyed_list_field(
        "note_families_on_per_book",
        {"joh": ["◈"]},
        key_parts=1,
        valid_values=valid_tokens,
        value_label="symbol token",
        encode_fn=encode_per_book_tokens,
    )
    assert err is None
    assert encoded is not None


def test_resolve_book_code_is_public_api():
    assert config.resolve_book_code("joh") == "jhn"
    assert config.resolve_book_code("php") == "phi"
    assert config.resolve_book_code("gen") == "gen"


def test_api_compare_normalizes_legacy_book_alias():
    # round-10: /api/compare skipped resolve_book_code, so a legacy alias
    # (joh) returned empty verses instead of John. It must now match the
    # canonical code byte-for-byte.
    from scripts.web_content import api_compare

    alias = api_compare("joh", 1, ["kjv"])
    canon = api_compare("jhn", 1, ["kjv"])
    assert alias["book"] == "jhn"
    assert alias["verse_count"] == canon["verse_count"] > 0
    # the alias path actually yields verse text, not a None-filled shell
    assert alias["verses"][0]["by_translation"].get("kjv")
