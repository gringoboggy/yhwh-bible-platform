"""mint-8 Finding #4 — write_book attribution-field schema invariant.

Regression coverage for the bug where ``write_book`` serialised an absent
attribution as ``{}``, turning an 8-field NOTES tuple into a schema-violating
9-field tuple whose 9th value was an empty dict (the ``str | None`` contract
expects a real attribution string or no 9th field at all).

Invariants asserted here:
  * an 8-field note (no attribution) round-trips back to an 8-field tuple,
    never gaining a ``{}`` (or ``None``) 9th field;
  * a 9-field note with ``None`` / empty attribution also collapses to 8 fields;
  * a 9-field note with a real, non-empty attribution string survives with
    its 9th field intact;
  * web_helpers serialisation helpers (tuple_to_dict / dict_to_tuple) round-trip
    an unattributed note without inventing an empty-dict 9th field;
  * write_book emits notes in canonical (chapter, verse, suffix) order.

write_book writes to a FIXED path (``NOTES_DIR / <book>.py``), so every test
monkeypatches ``web_helpers.NOTES_DIR`` to a tmp dir and clears the
notes_io load cache, never touching real ``content/notes/``.
"""

import pytest


@pytest.fixture
def wh(monkeypatch, tmp_path):
    """web_helpers with NOTES_DIR redirected to a tmp dir (lazy-imported,
    matching this repo's in-method import convention)."""
    from scripts import web_helpers
    from scripts.core import notes_io

    monkeypatch.setattr(web_helpers, "NOTES_DIR", tmp_path)
    notes_io.clear_load_notes_cache()
    return web_helpers


def _reparse(wh_mod, book_code):
    from scripts.core import notes_io

    text = (wh_mod.NOTES_DIR / f"{book_code}.py").read_text(encoding="utf-8")
    return notes_io.load_notes_from_text(text), text


class TestWriteBookAttributionInvariant:
    def test_eight_field_note_round_trips_to_eight_fields(self, wh):
        """An 8-field note must NOT gain a {} (or any) 9th field on write."""
        note8 = (1, 1, "", "", "word", "T", "L", "<aside>b</aside>")
        wh.write_book("zzz", [note8])

        notes, text = _reparse(wh, "zzz")
        assert len(notes) == 1
        assert len(notes[0]) == 8, f"expected 8-field round-trip, got {notes[0]!r}"
        assert "{}" not in text, "serialised file must not contain an empty-dict 9th field"

    def test_none_attribution_collapses_to_eight_fields(self, wh):
        """A 9-field note whose attribution is None (as produced by
        dict_to_tuple for an absent attribution) drops the 9th field."""
        note_none = (1, 2, "", "", "word", "T", "L", "<aside>x</aside>", None)
        wh.write_book("zzz", [note_none])

        notes, text = _reparse(wh, "zzz")
        assert len(notes[0]) == 8, f"None attribution must collapse to 8 fields, got {notes[0]!r}"
        assert "None" not in text

    def test_empty_string_attribution_collapses_to_eight_fields(self, wh):
        """An empty / whitespace-only attribution string is not a real
        attribution and must not be serialised as a 9th field."""
        note_empty = (1, 3, "", "", "word", "T", "L", "<aside>y</aside>", "   ")
        wh.write_book("zzz", [note_empty])

        notes, _ = _reparse(wh, "zzz")
        assert len(notes[0]) == 8, f"empty attribution must collapse to 8 fields, got {notes[0]!r}"

    def test_real_attribution_string_survives_as_ninth_field(self, wh):
        """A genuine attribution string is preserved as the 9th field."""
        note9 = (2, 3, "a", "", "comm", "T9", "L9", "<aside>b9</aside>", "Henry, PD.")
        wh.write_book("zzz", [note9])

        notes, _ = _reparse(wh, "zzz")
        assert len(notes[0]) == 9, f"real attribution must round-trip as 9 fields, got {notes[0]!r}"
        assert notes[0][8] == "Henry, PD."
        assert not isinstance(notes[0][8], dict)

    def test_mixed_notes_no_empty_dict_anywhere(self, wh):
        """Mixed 8-field / None / real-attribution notes produce no {} field."""
        notes_in = [
            (1, 1, "", "", "word", "T8", "L8", "<aside>b8</aside>"),
            (1, 2, "", "", "word", "T", "L", "<aside>x</aside>", None),
            (2, 3, "a", "", "comm", "T9", "L9", "<aside>b9</aside>", "Henry, PD."),
        ]
        wh.write_book("zzz", notes_in)

        notes, text = _reparse(wh, "zzz")
        assert "{}" not in text
        lengths = sorted(len(t) for t in notes)
        assert lengths == [8, 8, 9]
        assert not any(isinstance(t[-1], dict) for t in notes if len(t) == 9)


class TestWriteBookSortedOrder:
    def test_notes_written_in_canonical_order(self, wh):
        """write_book serialises notes sorted by (chapter, verse, suffix),
        bare-verse before suffixed — regardless of input order."""
        unsorted_in = [
            (2, 3, "a", "", "comm", "T", "L", "<aside>c</aside>"),
            (1, 1, "", "", "word", "T", "L", "<aside>a</aside>"),
            (1, 2, "", "", "word", "T", "L", "<aside>b</aside>"),
            (1, 1, "b", "", "word", "T", "L", "<aside>ab</aside>"),
        ]
        wh.write_book("zzz", unsorted_in)

        notes, _ = _reparse(wh, "zzz")
        keys = [(t[0], t[1], t[2]) for t in notes]
        assert keys == [(1, 1, ""), (1, 1, "b"), (1, 2, ""), (2, 3, "a")], keys


class TestSerialisationHelpersRoundTrip:
    def test_tuple_to_dict_to_tuple_unattributed(self, wh):
        """An 8-field note → dict → tuple carries None (not {}) for the
        absent attribution. dict_to_tuple is positional so the 9th slot is
        present-but-None; the empty-dict ({}) corruption is what the fix
        eliminates, and write_book is what drops the trailing None on disk
        (see TestWriteBookAttributionInvariant.test_none_attribution_*)."""
        note8 = (1, 1, "", "", "word", "T", "L", "<aside>b</aside>")
        d = wh.tuple_to_dict(note8)
        assert d["attribution"] in ("", None)
        assert not isinstance(d["attribution"], dict)
        back = wh.dict_to_tuple(d)
        # The 9th field must be falsy and must NOT be an empty dict.
        assert not back[8], f"absent attribution must be falsy, got {back!r}"
        assert not isinstance(back[8], dict), f"absent attribution must not be {{}}, got {back!r}"

    def test_tuple_to_dict_to_tuple_attributed(self, wh):
        """A 9-field note with a real attribution survives the dict round-trip."""
        note9 = (2, 3, "a", "", "comm", "T9", "L9", "<aside>b9</aside>", "Henry, PD.")
        d = wh.tuple_to_dict(note9)
        assert d["attribution"] == "Henry, PD."
        back = wh.dict_to_tuple(d)
        assert len(back) == 9
        assert back[8] == "Henry, PD."
