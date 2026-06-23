"""round-11 gap-2 — own-versification STRING verse labels must not crash the
verse-alignment paths that assume dense integer coordinates.

`/api/compare` accepts any id in ``list_translations()``, which includes the
``VERSIFICATION == "own"`` Geʽez stores. Those can emit lettered / Addition
verse labels ("2a", "B1"); the old ``max(keys)`` + ``range(1, max+1)`` raised
``TypeError`` on them. The fix aligns on the sorted union of actual keys via
``translations.verse_sort_key``.
"""

from __future__ import annotations

from scripts.core.translations import verse_sort_key


def test_verse_sort_key_orders_int_and_string_labels():
    assert sorted([3, 1, "2a", 2, 10, "B1"], key=verse_sort_key) == [1, 2, "2a", 3, 10, "B1"]
    # pure-int input is byte-identical to a plain int sort (dense canonical path)
    assert sorted([5, 1, 12, 2], key=verse_sort_key) == [1, 2, 5, 12]


def test_api_compare_handles_own_vers_string_verse_labels(monkeypatch):
    import scripts.core.translations as tx
    from scripts.web_content import api_compare

    monkeypatch.setattr(tx, "list_translations", lambda: ["kjv", "ov"])
    monkeypatch.setattr(tx, "has_book", lambda t, b: t == "ov")
    # an own-vers chapter with a lettered Addition label, returned OUT of order
    monkeypatch.setattr(tx, "get_chapter", lambda t, b, c: [(2, "two"), (1, "one"), ("2a", "extra"), (3, "three")])

    r = api_compare("gen", 1, ["ov"])

    assert "error" not in r
    # versification-aware order (no TypeError from max()/range() on a str key)
    assert [row["verse"] for row in r["verses"]] == [1, 2, "2a", 3]
    assert r["verse_count"] == 4
    assert r["verses"][2]["by_translation"]["ov"] == "extra"
