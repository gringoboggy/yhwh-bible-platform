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
