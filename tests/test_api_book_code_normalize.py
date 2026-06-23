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


def test_html_ref_id_from_note_id_normalizes_legacy_alias():
    # round-11 gap-1: a user-supplied note_id with an alias book must resolve to
    # the canonical book's ref-id, else the web editor can't navigate to it.
    from scripts.web_helpers import html_ref_id_from_note_id

    assert html_ref_id_from_note_id("joh:1:1:word") == html_ref_id_from_note_id("jhn:1:1:word")
    assert html_ref_id_from_note_id("joh:1:1:word") is not None


def test_validate_keyed_list_field_stores_canonical_book_key():
    # round-11 gap-1: a legacy-alias key ('joh') passes validation but must be
    # PERSISTED under the canonical code ('jhn') — else the override silently
    # vanishes at read time, which looks up 'jhn'.
    from scripts.api.editions import _validate_keyed_list_field
    from scripts.build_edition import encode_per_book_tokens

    encoded, err = _validate_keyed_list_field(
        "note_families_on_per_book",
        {"joh": ["◈"]},
        key_parts=1,
        valid_values={"◈", "★"},
        value_label="symbol token",
        encode_fn=encode_per_book_tokens,
    )
    assert err is None
    assert any(s.startswith("jhn=") for s in encoded)
    assert not any(s.startswith("joh") for s in encoded)


def test_book_index_cache_keyed_on_resolved_path_dedups_alias():
    # round-11 gap-5: _book_index_cached must key on the RESOLVED file path, so
    # the canonical id and its on-disk alias (exo / ex) for the SAME physical
    # file share ONE cache entry instead of two divergent ones.
    import pytest

    from scripts.core import translations as tx

    t = "geez-tewahedo-en"  # uses the 2-letter ex.py stem (the alias fires)
    if not tx.has_book(t, "exo"):
        pytest.skip(f"{t} has no Exodus book")
    tx._book_index_cached.cache_clear()
    idx_canon = tx._book_index(t, "exo")
    idx_alias = tx._book_index(t, "ex")
    assert idx_canon == idx_alias
    assert tx._book_index_cached.cache_info().currsize == 1  # one entry per file
