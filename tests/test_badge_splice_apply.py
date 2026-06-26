"""Byte-identity guard for apply_badge_markers' splice-apply (A2, round-14).

The production ``_apply_splices`` replaces the old O(n·k) per-splice rebuild
(``text = text[:start] + repl + text[end:]`` looped reverse-descending) which
re-allocated ~|text| every iteration and MemoryError'd on the flagship glossary
at the Windows commit limit (``build_edition.py:4444``, ~443 MB RSS). The new
form is a single-pass ascending assembly + one ``"".join``.

For DISJOINT spans the two are provably equal (both replace each ``[start,end)``
with ``repl`` and preserve every gap). This guard pins that equality — real-shape
edge cases + a randomized property test — so the swap is proven byte-neutral, and
the disjointness invariant (no overlapping splices, which markers/asides honor)
fails LOUDLY on any future regression instead of silently corrupting output.
"""

import random

import pytest

import scripts.build_edition as be


def _old_apply(text: str, splices: list[tuple[int, int, str]]) -> str:
    """The original reverse-descending rebuild — the reference oracle."""
    for start, end, repl in sorted(splices, key=lambda s: (s[0], s[1]), reverse=True):
        text = text[:start] + repl + text[end:]
    return text


def _disjoint(splices: list[tuple[int, int, str]]) -> bool:
    spans = sorted((s[0], s[1]) for s in splices)
    return all(spans[i][1] <= spans[i + 1][0] for i in range(len(spans) - 1))


class TestApplySplicesEquivalence:
    """``_apply_splices`` must equal the old reverse-descending rebuild for every
    disjoint input — byte-for-byte."""

    def test_empty(self):
        assert be._apply_splices("hello", []) == "hello"

    def test_single(self):
        s = [(0, 1, "H")]
        assert be._apply_splices("hello", s) == _old_apply("hello", s) == "Hello"

    def test_deletion_empty_repl(self):
        s = [(1, 3, "")]
        assert be._apply_splices("abcde", s) == _old_apply("abcde", s) == "ade"

    def test_repl_longer_and_shorter(self):
        s = [(1, 2, "XXX"), (3, 4, "")]
        assert be._apply_splices("abcde", s) == _old_apply("abcde", s)

    def test_adjacent_spans(self):
        s = [(0, 2, "X"), (2, 4, "Y")]  # end == next start -> allowed (not an overlap)
        assert be._apply_splices("abcd", s) == _old_apply("abcd", s) == "XY"

    def test_span_at_start_and_end(self):
        s = [(0, 1, "A"), (4, 5, "E")]
        assert be._apply_splices("abcde", s) == _old_apply("abcde", s)

    def test_full_replacement(self):
        s = [(0, 5, "XYZ")]
        assert be._apply_splices("abcde", s) == _old_apply("abcde", s) == "XYZ"

    def test_unsorted_input(self):
        s = [(3, 4, "D"), (0, 1, "A"), (1, 2, "B")]
        assert be._apply_splices("abcde", s) == _old_apply("abcde", s)

    def test_nonascii(self):
        t = "אבגΑβγአለመ note ¶"
        s = [(0, 3, "X"), (3, 6, "Y")]
        assert be._apply_splices(t, s) == _old_apply(t, s)

    def test_insert_and_span_share_start(self):
        # Production CAN place a zero-width insert at the same offset a span starts (e.g. a
        # prose-insert at a marker boundary) — a same-START but disjoint case. NEW must still
        # equal OLD here. (What production NEVER does — and what is the sole NEW≠OLD case — is
        # two IDENTICAL (start,end) zero-width inserts at one offset; distinct finditer / per-verse
        # positions preclude it.)
        t = "abcdefghijk"
        for s in ([(5, 5, "I"), (5, 9, "S")], [(5, 9, "S"), (5, 5, "I")], [(3, 5, "A"), (5, 5, "I")]):
            assert be._apply_splices(t, s) == _old_apply(t, s), s

    def test_property_random_disjoint(self):
        rnd = random.Random(20260626)
        for _ in range(500):
            n = rnd.randint(0, 40)
            text = "".join(rnd.choice("abcde \n<>אΑ¶") for _ in range(n))
            splices: list[tuple[int, int, str]] = []
            cur = rnd.randint(0, 3)  # first start
            while cur < len(text):
                end = min(cur + rnd.randint(0, 3), len(text))  # span (end==start = pure insert)
                repl = "".join(rnd.choice("XYZ") for _ in range(rnd.randint(0, 4)))
                splices.append((cur, end, repl))
                cur = end + rnd.randint(1, 4)  # advance >=1 from end -> strictly increasing
                # distinct starts: the production model (finditer / per-verse offsets never collide).
            rnd.shuffle(splices)
            assert _disjoint(splices)
            assert be._apply_splices(text, splices) == _old_apply(text, splices)

    def test_overlap_raises(self):
        # Overlapping spans must fail loudly (disjointness invariant) — never silent corruption.
        with pytest.raises(AssertionError):
            be._apply_splices("abcde", [(0, 3, "X"), (2, 4, "Y")])
