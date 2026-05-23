"""Arabic Van Dyck (``arabic-vandyke``) ingest — Phase 2 translation spine.

Van Dyck uses KJV/English versification throughout: a full per-chapter probe of
all 66 Protestant books / 1189 chapters against the canonical KJV skeleton found
agreement EVERYWHERE except two tail-splits where Van Dyck carries one extra
trailing verse that the KJV folds into the preceding verse (content-aligned vs
the real text):

  - 1 Timothy 6: AVD 6:21 ("...erred concerning the faith.") + 6:22 ("Grace be
    with thee. Amen.") = KJV 6:21
  - 3 John 1:    AVD 1:14 ("...face to face.") + 1:15 ("Peace be to thee... Greet
    the friends by name.") = KJV 1:14

So ``arabic_to_kjv`` is identity except those two same-book merges, and the
extractor concatenates the merged source verses in source order so the popup
shows the WHOLE verse (the established extract_lxx_swete.build_verses behavior).
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
ARABIC_DIR = REPO / "content" / "translations" / "arabic-vandyke"
VPL = REPO / "content" / "translations" / "sources" / "arabic-vandyke" / "arb-vd_vpl.txt"


class TestArabicToKjv:
    """The versification adapter: identity except the two tail-merges."""

    @pytest.mark.parametrize(
        "book,ch,vs,expected",
        [
            ("gen", 1, 1, ("gen", 1, 1)),
            ("psa", 9, 20, ("psa", 9, 20)),  # KJV-style Ps 9/10 split (not Vulgate-merged)
            ("psa", 10, 1, ("psa", 10, 1)),
            ("psa", 3, 1, ("psa", 3, 1)),  # title psalms numbered KJV-style
            ("joe", 3, 1, ("joe", 3, 1)),  # Joel 3 chapters (not the 4-ch Hebrew split)
            ("mal", 4, 6, ("mal", 4, 6)),  # Malachi 4 ch (not merged into 3)
            ("act", 19, 41, ("act", 19, 41)),  # KJV-style Acts 19:41
            ("rev", 22, 21, ("rev", 22, 21)),
        ],
    )
    def test_identity_normal_verses(self, book, ch, vs, expected):
        from scripts.core.versification import arabic_to_kjv

        assert arabic_to_kjv(book, ch, vs) == expected

    def test_1timothy_tail_merge(self):
        from scripts.core.versification import arabic_to_kjv

        assert arabic_to_kjv("1ti", 6, 21) == ("1ti", 6, 21)  # identity
        assert arabic_to_kjv("1ti", 6, 22) == ("1ti", 6, 21)  # tail folds onto v21

    def test_3john_tail_merge(self):
        from scripts.core.versification import arabic_to_kjv

        assert arabic_to_kjv("3jn", 1, 14) == ("3jn", 1, 14)  # identity
        assert arabic_to_kjv("3jn", 1, 15) == ("3jn", 1, 14)  # tail folds onto v14


class TestApplyRemap:
    """The generic extract-time remap+concat mechanism (Arabic is its first user;
    JPS/Douay/Vulgate reuse it)."""

    def test_identity_remap_unchanged(self):
        from scripts.extract_translation import apply_remap

        data = {"gen": [(1, 1, "a"), (1, 2, "b")]}
        out = apply_remap(data, lambda code, c, v: (code, c, v))
        assert out == {"gen": [(1, 1, "a"), (1, 2, "b")]}

    def test_merge_concatenates_in_source_order(self):
        from scripts.extract_translation import apply_remap

        # deliberately scrambled input order — concat must follow source coord order
        data = {"1ti": [(6, 22, "second"), (6, 20, "x"), (6, 21, "first")]}

        def remap(code, c, v):
            if (code, c, v) == ("1ti", 6, 22):
                return ("1ti", 6, 21)
            return (code, c, v)

        out = apply_remap(data, remap)
        assert out["1ti"] == [(6, 20, "x"), (6, 21, "first second")]

    def test_drop_when_remap_returns_none(self):
        from scripts.extract_translation import apply_remap

        data = {"est": [(1, 1, "keep"), (1, 2, "drop")]}
        out = apply_remap(data, lambda code, c, v: None if v == 2 else (code, c, v))
        assert out["est"] == [(1, 1, "keep")]

    def test_cross_book_move_and_empty_book_omitted(self):
        from scripts.extract_translation import apply_remap

        data = {"dan": [(3, 24, "azariah")]}
        out = apply_remap(data, lambda code, c, v: ("paz", 1, 1) if (code, c, v) == ("dan", 3, 24) else (code, c, v))
        assert out.get("paz") == [(1, 1, "azariah")]
        assert "dan" not in out  # emptied book is not emitted


def _load_arabic_book(code):
    from scripts.core import translations as tx

    p = ARABIC_DIR / f"{code}.py"
    if not p.is_file():
        return None
    return tx.load_book_verses_from_text(p.read_text(encoding="utf-8"))


class TestArabicVandykeIngest:
    """Integration: the committed on-disk arabic-vandyke store."""

    def test_66_books_emitted(self):
        books = sorted(p.stem for p in ARABIC_DIR.glob("*.py"))
        assert len(books) == 66, f"expected 66 Protestant books, got {len(books)}: {books}"

    def test_1timothy_6_21_is_concatenation_of_source_21_and_22(self):
        from scripts.core import translations as tx
        from scripts.extract_translation import parse_vpl

        src = {(c, v): t for (c, v, t) in parse_vpl(VPL).get("1TI", [])}
        expected = (src[(6, 21)] + " " + src[(6, 22)]).strip()
        assert tx.get_verse("arabic-vandyke", "1ti", 6, 21) == expected
        assert tx.get_verse("arabic-vandyke", "1ti", 6, 22) is None  # no orphan tail verse

    def test_3john_1_14_is_concatenation_of_source_14_and_15(self):
        from scripts.core import translations as tx
        from scripts.extract_translation import parse_vpl

        src = {(c, v): t for (c, v, t) in parse_vpl(VPL).get("3JO", [])}
        expected = (src[(1, 14)] + " " + src[(1, 15)]).strip()
        assert tx.get_verse("arabic-vandyke", "3jn", 1, 14) == expected
        assert tx.get_verse("arabic-vandyke", "3jn", 1, 15) is None

    def test_identity_spot_checks_present(self):
        from scripts.core import translations as tx

        assert tx.get_verse("arabic-vandyke", "gen", 1, 1)  # non-empty
        assert tx.get_verse("arabic-vandyke", "psa", 9, 20)
        assert tx.get_verse("arabic-vandyke", "psa", 10, 1)
        assert tx.get_verse("arabic-vandyke", "act", 19, 41)

    def test_all_coords_in_canonical_extent(self):
        from scripts.core.canonical_verse_counts import coord_in_canonical_extent

        bad = []
        for p in ARABIC_DIR.glob("*.py"):
            code = p.stem
            for ch, vs, _t in _load_arabic_book(code) or []:
                if not coord_in_canonical_extent(code, ch, vs):
                    bad.append((code, ch, vs))
        assert bad == [], f"out-of-extent coords after remap: {bad[:20]}"

    def test_total_verses_is_source_minus_two_merges(self):
        from scripts.extract_translation import parse_vpl

        src_total = sum(len(v) for v in parse_vpl(VPL).values())
        on_disk = sum(len(_load_arabic_book(p.stem) or []) for p in ARABIC_DIR.glob("*.py"))
        assert on_disk == src_total - 2, f"source {src_total}, on-disk {on_disk} (expected -2 from the 2 tail-merges)"
