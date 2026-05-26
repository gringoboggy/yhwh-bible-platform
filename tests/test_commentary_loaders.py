"""Shared-contract characterization tests for the six verse-keyed
commentary corpora (B1.9 de-dup safety net, 2026-05-26).

The six loaders — Patristic (γ.3), Ethiopian (γ.4), Protestant (χ.2),
Catholic (χ.4), Reformation (χ.3), Rabbinic (χ.5) — were ~540 lines of
near-clone differing only in the JSON path, the "person" field name
(``father`` vs ``commentator``), the SourceMissingError message, and the
``by_father``/``by_commentator`` accessor name (audit B1.9). This file
pins the UNIFORM contract every loader must honour, so the de-dup to a
shared base cannot silently mis-wire any one corpus (wrong path → wrong
data; wrong person field → empty index).

Uses only the public surface (the loader class, its dataclass, the
person-field name, ``PATH``, ``for_verse``, ``by_*``, ``__len__``) plus
the seed JSON on disk — no coupling to the private per-person index —
so the same assertions hold before and after the refactor.

Per-tradition behavioural pins live in the six ``test_*`` topic files;
this file is the cross-cutting infrastructure pin.
"""

from __future__ import annotations

import json

import pytest

from scripts.core import sources as src

# (loader class, its frozen-dataclass entry type, the "person" field name,
#  the by_* accessor name). Every name here is public and exists both
# before and after the B1.9 de-dup.
CORPORA = [
    (src.PatristicCommentaries, src.PatristicCommentary, "father", "by_father"),
    (src.EthiopianCommentaries, src.EthiopianCommentary, "father", "by_father"),
    (src.ProtestantCommentaries, src.ProtestantCommentary, "commentator", "by_commentator"),
    (src.CatholicCommentaries, src.CatholicCommentary, "father", "by_father"),
    (src.ReformationCommentaries, src.ReformationCommentary, "commentator", "by_commentator"),
    (src.RabbinicCommentaries, src.RabbinicCommentary, "commentator", "by_commentator"),
]

_IDS = [loader.__name__ for loader, _dc, _pf, _acc in CORPORA]


def _first_indexed_entry(loader, raw_entries, person_field):
    """Return (raw_dict, dataclass_instance) for the first seed entry the
    loader actually indexed by verse, or (None, None). Robust against a
    malformed leading entry that the loader's defensive parse skips."""
    for raw in raw_entries:
        try:
            book = raw["book"]
            chapter = int(raw["chapter"])
            verse = int(raw["verse"])
            raw[person_field]
        except (KeyError, ValueError, TypeError):
            continue
        hits = loader.for_verse(book, chapter, verse)
        if hits:
            return raw, hits[0]
    return None, None


@pytest.mark.parametrize("loader_cls, dataclass_cls, person_field, accessor", CORPORA, ids=_IDS)
def test_loader_indexes_by_verse_and_person(loader_cls, dataclass_cls, person_field, accessor):
    loader = loader_cls()

    # A non-empty seed indexed by verse.
    assert len(loader) >= 1, f"{loader_cls.__name__} indexed no entries"

    data = json.loads(loader_cls.PATH.read_text(encoding="utf-8"))
    raw, entry = _first_indexed_entry(loader, data.get("entries", []), person_field)
    assert entry is not None, f"{loader_cls.__name__} indexed nothing for_verse from its own seed"

    # for_verse returns instances of the corpus's own frozen dataclass…
    assert isinstance(entry, dataclass_cls)
    # …carrying its distinctive person field, populated.
    person = getattr(entry, person_field)
    assert isinstance(person, str) and person, f"{person_field!r} unset on {loader_cls.__name__} entry"
    assert person == str(raw[person_field])

    # The by-person accessor round-trips that entry back.
    matches = getattr(loader, accessor)(person)
    assert any(e.book == entry.book and e.chapter == entry.chapter and e.verse == entry.verse for e in matches), (
        f"{loader_cls.__name__}.{accessor}({person!r}) did not surface its own entry"
    )

    # for_verse copies out — a fresh list each call, not the live index.
    assert loader.for_verse(entry.book, entry.chapter, entry.verse) is not loader.for_verse(
        entry.book, entry.chapter, entry.verse
    )


@pytest.mark.parametrize("loader_cls, dataclass_cls, person_field, accessor", CORPORA, ids=_IDS)
def test_for_verse_empty_for_uncommented_verse(loader_cls, dataclass_cls, person_field, accessor):
    loader = loader_cls()
    # No real seed reaches chapter 999; the lookup degrades to [].
    assert loader.for_verse("gen", 999, 999) == []
    assert getattr(loader, accessor)("Nobody At All Ever") == []


@pytest.mark.parametrize("loader_cls, dataclass_cls, person_field, accessor", CORPORA, ids=_IDS)
def test_missing_cache_file_raises_source_missing(
    loader_cls, dataclass_cls, person_field, accessor, tmp_path, monkeypatch
):
    # Each loader checks PATH.is_file() at construction and raises
    # SourceMissingError when the JSON cache is absent — the graceful-
    # degrade contract prospect.py relies on. Construct the class
    # directly (not the cached singleton) so no cache_clear dance is
    # needed; monkeypatch restores PATH afterwards.
    monkeypatch.setattr(loader_cls, "PATH", tmp_path / "absent.json")
    with pytest.raises(src.SourceMissingError):
        loader_cls()
