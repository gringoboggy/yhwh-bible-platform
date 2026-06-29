"""K-R4-2 popup-unit split + K-R5-3 book-boundary badge clamp (Kobo round 5).

Device facts the fix is built on (notes/2026-06-10-kobo-round5-device-qa.md):
the Kobo eInk Footnote preview DECLINES a popup whose tag-stripped size is too
big and navigates to the piece top instead. Round-5 taps narrowed the decline
bracket to pops <= 4,498 / declines >= 5,500 stripped chars, so the build caps
every merged verse-notes popup unit at <= ~4,400 (DEFAULT_NOTE_POPUP_SPLIT_CAP,
just under the proven-pop floor; configurable per edition via
``note_popup_split_cap``; 0 = off).

Design (a)+(b) per the round-4 QA note:
  (a) an over-cap merged aside splits into MULTIPLE units at category
      boundaries — each unit gets its own badge + its own aside;
  (b) a single note body that alone exceeds the cap (the ~19k Easton entries)
      is CHUNKED within the body at safe depth-0 text boundaries, each chunk
      its own unit, with visible continuation marks.

K-R5-3: a BOOK-last verse's badge clamp must bound at the next book's
title-page div, not sail past it into the title block (x38 title pages carried
the previous book's badge in v0.1.0).

Round 7 — K-R6-2 root cause (notes/2026-06-11-kobo-round6-device-qa.md):
Nickel measures a tapped popup from its target anchor FORWARD to the next
anchor whose id does NOT string-extend the tapped id, and refuses (navigates)
above ~8,858 serialized kepub bytes. Two build defects fed it:
  (1) PREFIX-NESTED FAMILY IDS — the split head kept the bare
      ``vnotes-<bk>-<c>-<v>`` id, a strict prefix of every ``-sN`` sibling, so
      the head's measured slice swallowed the whole family (98/98 heads over
      cap; family tails failed the same prefix-group bookkeeping; plus 20
      accidental adjacent cross-verse digit-extension pairs like
      jub-7-1 < jub-7-13).
  (2) NO PER-UNIT BYTE BUDGET — the splitter packed by stripped chars only;
      koboSpan inflation (round-6 corpus: +43..81 B per text segment) pushed
      201 units over the 8,000 B split target (97 oversized singles);
      the fix re-anchors default at the 8,858 floor (shell sized to wrapper delta).
Fix contract pinned here:
  * EVERY unit id carries ``-s<N>`` (singles = ``-s1``) and families cap at 9
    units, so no vnotes/vbadge id is EVER a strict prefix of another — the
    whole namespace is structurally prefix-free.
  * a second per-unit budget, ``note_popup_split_byte_cap`` (default 8,858
    estimated post-kepubify bytes, anchored at the proven-open floor; 0 = off),
    splits any unit the char cap missed; ``_estimate_kepub_aside_bytes`` must
    DOMINATE the real measured round-6 inflation (max +81.3 B/segment) and the
    shell allowance is sized so the full emitted <aside> estimates <= cap
    (gate 4n can never trip on a unit the splitter passed).
"""

from __future__ import annotations

import importlib.util
import io
import re
import sys
import zipfile
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _load_dev_module(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "dev" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _book_tree(tmp_path: Path, *codes: str) -> Path:
    """Copy the named books' base files into a temp build tree."""
    epub = REPO / "epub_working"
    tmp = tmp_path / "build"
    tmp.mkdir(parents=True, exist_ok=True)
    for code in codes:
        for f in config.get_book(code)["files"]:
            if not (tmp / f).exists():
                (tmp / f).write_text((epub / f).read_text(encoding="utf-8"), encoding="utf-8")
    return tmp


def _aside_map(text: str, coord: str) -> dict[str, str]:
    """{aside_id: aside_html} for every verse-notes unit of one verse coord
    (the unsuffixed id + any -sN split siblings)."""
    out: dict[str, str] = {}
    for m in re.finditer(
        # ``verse-notes[^"]*`` so this matches the non-eink ``class="verse-notes"`` AND
        # the eink ``class="verse-notes verse-notes--eink-anchor"`` modifier (the split
        # path is eink-only since the device-QA 2026-06-28 single-badge decision).
        rf'<aside class="verse-notes[^"]*" id="(vnotes-{coord}(?:-s\d+)?)" epub:type="footnote">.*?</aside>',
        text,
        re.DOTALL,
    ):
        out[m.group(1)] = m.group(0)
    return out


def _vn_item_texts(html: str) -> list[str]:
    """Stripped text of each .vn-item row, in document order (continuation
    furniture removed so conservation can compare across split settings)."""
    from scripts.build_edition import _stripped_len  # noqa: F401  (import check)

    items = re.findall(r'<div class="vn-item[^"]*">(.*?)</div>', html, re.DOTALL)
    out = []
    for it in items:
        t = re.sub(r'<span class="vn-cont-mark">[^<]*</span>', "", it)
        t = re.sub(r"<[^>]+>", "", t)
        import html as _h

        t = _h.unescape(t)
        out.append(re.sub(r"\s+", " ", t).strip().strip("• ").strip())
    return out


# ----------------------------------------------------------------------
# Resolver + measure
# ----------------------------------------------------------------------


class TestSplitCapResolver:
    def test_unset_defaults_to_4400(self):
        from scripts.build_edition import DEFAULT_NOTE_POPUP_SPLIT_CAP, resolve_note_popup_split_cap

        assert DEFAULT_NOTE_POPUP_SPLIT_CAP == 4_400
        assert resolve_note_popup_split_cap({"id": "x"}) == 4_400
        assert resolve_note_popup_split_cap({"id": "x", "note_popup_split_cap": None}) == 4_400
        assert resolve_note_popup_split_cap({"id": "x", "note_popup_split_cap": ""}) == 4_400

    def test_unset_tablet_defaults_to_zero(self):
        """Apple M2 — one merged study badge per verse; no -s1/-s2/-s3 cascade."""
        from scripts.build_edition import resolve_note_popup_split_cap

        tablet = {"id": "x", "target_reader": "tablet"}
        assert resolve_note_popup_split_cap(tablet) == 0
        assert resolve_note_popup_split_cap({**tablet, "note_popup_split_cap": None}) == 0
        assert resolve_note_popup_split_cap({**tablet, "note_popup_split_cap": ""}) == 0

    def test_zero_disables(self):
        from scripts.build_edition import resolve_note_popup_split_cap

        assert resolve_note_popup_split_cap({"id": "x", "note_popup_split_cap": 0}) == 0

    def test_custom_cap_honored(self):
        from scripts.build_edition import resolve_note_popup_split_cap

        assert resolve_note_popup_split_cap({"id": "x", "note_popup_split_cap": 3000}) == 3000
        assert resolve_note_popup_split_cap({"id": "x", "note_popup_split_cap": "5200"}) == 5200

    def test_invalid_raises(self):
        import pytest

        from scripts.build_edition import resolve_note_popup_split_cap

        with pytest.raises(ValueError):
            resolve_note_popup_split_cap({"id": "x", "note_popup_split_cap": "huge"})
        with pytest.raises(ValueError):
            resolve_note_popup_split_cap({"id": "x", "note_popup_split_cap": -5})


class TestStrippedLenParity:
    def test_matches_calibration_tool(self):
        """The build's measure must be THE round-5 measure (the bracket numbers
        were taken with dev/kobo_tap_calibration.stripped_len)."""
        from scripts.build_edition import _stripped_len

        cal = _load_dev_module("kobo_tap_calibration")
        samples = [
            '<aside><p class="x">Hello &amp; <i>world</i></p>\n  <p>second&nbsp;row</p></aside>',
            "<p>plain   text\twith\nwhitespace</p>",
            '<div class="vn-item"><span class="vn-sep">• </span>note body</div>',
            "",
        ]
        for s in samples:
            assert _stripped_len(s) == cal.stripped_len(s), s


# ----------------------------------------------------------------------
# (b) within-body chunking — pure function
# ----------------------------------------------------------------------


class TestChunkRow:
    ROW_FMT = '<div class="vn-item note-dict-easton"><span class="vn-sep">• </span><p>{}</p></div>'

    def test_under_target_returned_whole(self):
        from scripts.build_edition import _chunk_vn_item_row

        row = self.ROW_FMT.format("short body. " * 5)
        assert _chunk_vn_item_row(row, 4_000) == [row]

    def test_chunks_each_under_target_and_conserved(self):
        from scripts.build_edition import _chunk_vn_item_row, _stripped_len

        body = " ".join(f"Sentence number {i} about David the king of Israel." for i in range(400))
        row = self.ROW_FMT.format(body)
        parts = _chunk_vn_item_row(row, 3_800)
        assert len(parts) >= 4
        for p in parts:
            assert _stripped_len(p) <= 3_800 + 64, f"part over target: {_stripped_len(p)}"
        # conservation: the concatenated stripped text (continuation marks
        # removed) equals the original row's stripped text
        joined = " ".join(_vn_item_texts(p)[0] for p in parts)
        original = _vn_item_texts(row)[0]
        assert re.sub(r"\s+", " ", joined) == re.sub(r"\s+", " ", original)

    def test_never_cuts_inside_an_inline_tag(self):
        from scripts.build_edition import _chunk_vn_item_row

        body = " ".join(f"Word <i>italic{i} run kept together</i> tail." for i in range(300))
        parts = _chunk_vn_item_row(self.ROW_FMT.format(body), 2_000)
        assert len(parts) >= 2
        for p in parts:
            assert p.count("<i>") == p.count("</i>"), "inline tag cut across a chunk boundary"
            assert p.count("<p") == p.count("</p>")

    def test_continuation_furniture(self):
        from scripts.build_edition import _chunk_vn_item_row

        body = "A plain sentence here. " * 400
        parts = _chunk_vn_item_row(self.ROW_FMT.format(body), 3_000)
        assert len(parts) >= 2
        # part 1: original classes, no vn-cont, trailing continuation mark
        assert "vn-cont" not in parts[0].split(">", 1)[0]
        assert 'class="vn-cont-mark"' in parts[0]
        # parts 2+: vn-cont wrapper class + leading continuation mark
        for p in parts[1:]:
            assert "vn-cont" in p.split(">", 1)[0]
            assert 'class="vn-cont-mark"' in p
        # last part has no TRAILING mark after its text (only the lead one)
        assert parts[-1].split('class="vn-cont-mark"')[1:], "lead mark expected"


# ----------------------------------------------------------------------
# (a)+(b) integrated — real gen / 1sa trees
# ----------------------------------------------------------------------

_S2_FLAGS = {
    "note_attribution_dedup": True,
    "note_group_by_category": True,
    "note_topic_dedup": True,
}


class TestApplyBadgeSplit:
    def test_over_cap_verse_splits_flat_path(self, tmp_path):
        # device-QA 2026-06-28: the per-verse popup SPLIT is now EINK-ONLY (single
        # merged badge off-Kobo), so the split path is exercised under target_reader=eink.
        from scripts.build_edition import _stripped_len, apply_badge_markers

        tmp = _book_tree(tmp_path, "gen")
        apply_badge_markers(
            tmp, {"id": "x", "marker_style": "badge", "target_reader": "eink", "reader_eink_study_layout": "popup"}
        )
        fname = next(f for f in config.get_book("gen")["files"] if 'id="v-gen-1-1"' in (tmp / f).read_text("utf-8"))
        text = (tmp / fname).read_text("utf-8")

        units = _aside_map(text, "gen-1-1")
        assert "vnotes-gen-1-1-s1" in units, "head unit must carry -s1 (K-R6-2 prefix-free namespace)"
        assert "vnotes-gen-1-1" not in units, "bare head id = the K-R6-2 family-swallow defect"
        assert len(units) >= 2, "gen 1:1 (~9k stripped) must split"
        # suffixes are sequential from s1
        assert sorted(units) == [f"vnotes-gen-1-1-s{i}" for i in range(1, len(units) + 1)]
        for uid, html_u in units.items():
            assert _stripped_len(html_u) <= 4_400, f"{uid} still over the cap"
            # each unit's back-link points at its OWN badge
            bid = uid.replace("vnotes-", "vbadge-")
            assert f'href="#{bid}"' in html_u
            assert f'id="{bid}"' in text, f"badge {bid} missing"

    def test_non_eink_packs_over_cap_verse_into_single_merged_badge(self, tmp_path):
        """Device-QA 2026-06-28 contract: on a NON-eink target the per-verse split is
        OFF, so even gen 1:1 (~9k stripped, over the eink cap) ships as ONE merged
        badge / unit — no -s2. The split stays eink-only (Kobo's footnote buffer);
        this pins the fix for the 'two badges per verse' leak on Apple/Play/Kindle."""
        from scripts.build_edition import apply_badge_markers

        tmp = _book_tree(tmp_path, "gen")
        # no target_reader == the everywhere (non-eink) default
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        fname = next(f for f in config.get_book("gen")["files"] if 'id="v-gen-1-1"' in (tmp / f).read_text("utf-8"))
        text = (tmp / fname).read_text("utf-8")
        units = _aside_map(text, "gen-1-1")
        assert list(units) == ["vnotes-gen-1-1-s1"], f"non-eink must not split; got {list(units)}"
        assert 'id="vbadge-gen-1-1-s2"' not in text, "non-eink leaked a second badge (the 'two badges' bug)"

    def test_badge_cluster_sits_together_at_verse_end(self, tmp_path):
        # EINK-only split path (device-QA 2026-06-28): the -s1/-s2 badge cluster only
        # exists on eink; non-eink packs the verse into a single merged badge.
        from scripts.build_edition import apply_badge_markers

        tmp = _book_tree(tmp_path, "gen")
        apply_badge_markers(
            tmp, {"id": "x", "marker_style": "badge", "target_reader": "eink", "reader_eink_study_layout": "popup"}
        )
        fname = next(f for f in config.get_book("gen")["files"] if 'id="v-gen-1-1"' in (tmp / f).read_text("utf-8"))
        text = (tmp / fname).read_text("utf-8")
        # the cluster: the -s1 head badge immediately followed (single space) by -s2
        m = re.search(r'<a class="verse-notes-badge" id="vbadge-gen-1-1-s1" .*?</a>', text, re.DOTALL)
        assert m
        tail = text[m.end() :]
        assert tail.startswith(' <a class="verse-notes-badge" id="vbadge-gen-1-1-s2"'), tail[:90]
        # the bare (un-suffixed) badge id must be gone entirely
        assert 'id="vbadge-gen-1-1"' not in text

    def test_under_cap_verse_single_unit_carries_s1(self, tmp_path):
        from scripts.build_edition import _stripped_len, apply_badge_markers

        tmp = _book_tree(tmp_path, "gen")
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        fname = next(f for f in config.get_book("gen")["files"] if 'id="v-gen-1-1"' in (tmp / f).read_text("utf-8"))
        text = (tmp / fname).read_text("utf-8")
        # gen 1:8 carries a genuinely tiny note (markup-light, est ~1.7 kB).
        # Under the K-R6-2 byte model (default now anchored at the 8,858 proven
        # floor) a verse like the markup-dense gen 1:3 legitimately exceeds and
        # splits; gen 1:8 is the single-unit "-s1" control. The K-R6-2
        # prefix-free rule still requires the -s1 suffix even for unsplit units.
        units = _aside_map(text, "gen-1-8")
        assert list(units) == ["vnotes-gen-1-8-s1"]
        assert _stripped_len(units["vnotes-gen-1-8-s1"]) <= 4_400
        assert 'id="vbadge-gen-1-8-s2"' not in text
        bm = re.search(r'<a class="verse-notes-badge" id="vbadge-gen-1-8-s1" [^>]*>', text)
        assert bm and 'epub:type="noteref"' in bm.group(0)
        assert "part" not in bm.group(0)
        # an unsplit unit shows NO (1/1) part furniture
        assert "vn-part" not in units["vnotes-gen-1-8-s1"]

    def test_conservation_against_cap_off_run(self, tmp_path):
        """Splitting must conserve EVERY .vn-item row's text (nothing dropped,
        nothing duplicated) — compare against a cap=0 (off) run of the same tree."""
        from scripts.build_edition import apply_badge_markers

        tmp_on = _book_tree(tmp_path / "on", "gen")
        tmp_off = _book_tree(tmp_path / "off", "gen")
        apply_badge_markers(tmp_on, {"id": "x", "marker_style": "badge"})
        apply_badge_markers(
            tmp_off,
            {"id": "x", "marker_style": "badge", "note_popup_split_cap": 0, "note_popup_split_byte_cap": 0},
        )
        fname = next(f for f in config.get_book("gen")["files"] if 'id="v-gen-1-1"' in (tmp_on / f).read_text("utf-8"))
        t_on = (tmp_on / fname).read_text("utf-8")
        t_off = (tmp_off / fname).read_text("utf-8")
        for coord in ("gen-1-1", "gen-1-26"):
            on_rows = []
            for html_u in _aside_map(t_on, coord).values():
                on_rows.extend(_vn_item_texts(html_u))
            off_rows = _vn_item_texts(next(iter(_aside_map(t_off, coord).values())))
            assert " ".join(" ".join(on_rows).split()) == " ".join(" ".join(off_rows).split()), (
                f"{coord}: split run lost or duplicated note text"
            )

    def test_cap_zero_disables_split(self, tmp_path):
        from scripts.build_edition import _stripped_len, apply_badge_markers

        tmp = _book_tree(tmp_path, "gen")
        apply_badge_markers(
            tmp,
            {"id": "x", "marker_style": "badge", "note_popup_split_cap": 0, "note_popup_split_byte_cap": 0},
        )
        fname = next(f for f in config.get_book("gen")["files"] if 'id="v-gen-1-1"' in (tmp / f).read_text("utf-8"))
        text = (tmp / fname).read_text("utf-8")
        units = _aside_map(text, "gen-1-1")
        # split off, but the single unit STILL wears the prefix-free -s1 id
        assert list(units) == ["vnotes-gen-1-1-s1"]
        assert _stripped_len(units["vnotes-gen-1-1-s1"]) > 4_400  # the unsplit giant

    def test_s2_cascade_path_splits_with_category_heads(self, tmp_path):
        """The shipped eth EINK profile (S2 cascade on) must split too, each unit a
        well-formed cascade (category heads present; conservation guard quiet).
        Split is EINK-only since the device-QA 2026-06-28 single-badge decision."""
        from scripts.build_edition import _stripped_len, apply_badge_markers

        tmp = _book_tree(tmp_path, "gen")
        apply_badge_markers(
            tmp,
            {
                "id": "x",
                "marker_style": "badge",
                "target_reader": "eink",
                "reader_eink_study_layout": "popup",
                **_S2_FLAGS,
            },
        )
        fname = next(f for f in config.get_book("gen")["files"] if 'id="v-gen-1-1"' in (tmp / f).read_text("utf-8"))
        text = (tmp / fname).read_text("utf-8")
        units = _aside_map(text, "gen-1-1")
        assert len(units) >= 2
        for uid, html_u in units.items():
            assert _stripped_len(html_u) <= 4_400, uid
            assert 'class="vn-cat-head"' in html_u, f"{uid}: cascade head missing"

    def test_giant_single_note_chunked_within_body(self, tmp_path):
        """1sa 16:12 carries ONE ~19k dict-easton note (Easton's DAVID) — design
        (b): the body chunks across multiple units, visibly marked continued.
        Chunking is part of the EINK-only split path (device-QA 2026-06-28)."""
        from scripts.build_edition import _stripped_len, apply_badge_markers

        tmp = _book_tree(tmp_path, "1sa")
        apply_badge_markers(
            tmp,
            {
                "id": "x",
                "marker_style": "badge",
                "target_reader": "eink",
                "reader_eink_study_layout": "popup",
                **_S2_FLAGS,
            },
        )
        fname = next(f for f in config.get_book("1sa")["files"] if 'id="v-1sa-16-12"' in (tmp / f).read_text("utf-8"))
        text = (tmp / fname).read_text("utf-8")
        units = _aside_map(text, "1sa-16-12")
        assert len(units) >= 4, f"19k body should chunk into >=4 units, got {len(units)}"
        for uid, html_u in units.items():
            assert _stripped_len(html_u) <= 4_400, uid
        assert any("vn-cont" in u for u in units.values()), "no continuation chunk marked vn-cont"
        assert any('class="vn-cont-mark"' in u for u in units.values())


# ----------------------------------------------------------------------
# Round 7 — K-R6-2 leg 1: prefix-free anchor namespace
# ----------------------------------------------------------------------


class TestPrefixFreeIds:
    def test_no_popup_anchor_id_is_a_strict_prefix_of_another(self, tmp_path):
        """The whole vnotes/vbadge namespace must be prefix-free per file —
        Nickel measures a popup forward to the next NON-prefix-extending
        anchor, so any prefix pair (family head, or cross-verse digit
        extension like gen-1-1 < gen-1-10) inflates the measured slice."""
        from scripts.build_edition import apply_badge_markers

        tmp = _book_tree(tmp_path, "gen")
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge", **_S2_FLAGS})
        for f in config.get_book("gen")["files"]:
            text = (tmp / f).read_text("utf-8")
            ids = sorted(set(re.findall(r'\bid="((?:vnotes|vbadge)-[^"]+)"', text)))
            for a, b in zip(ids, ids[1:], strict=False):
                assert not b.startswith(a), f"{f}: anchor id {a!r} is a strict prefix of {b!r}"

    def test_every_unit_id_ends_with_single_digit_s_suffix(self, tmp_path):
        """-s1..-s9 on EVERY unit (singles included): the single-digit tail is
        what makes digit-extension prefixes structurally impossible."""
        from scripts.build_edition import apply_badge_markers

        tmp = _book_tree(tmp_path, "gen")
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        seen = 0
        for f in config.get_book("gen")["files"]:
            text = (tmp / f).read_text("utf-8")
            for vid in re.findall(r'\bid="((?:vnotes|vbadge)-[^"]+)"', text):
                seen += 1
                assert re.search(r"-s[1-9]$", vid), f"{f}: {vid!r} lacks the -s<1..9> tail"
        assert seen > 100, "precondition: gen carries hundreds of popup anchors"

    def test_family_over_nine_units_raises(self):
        """-s10 would re-introduce a strict prefix (-s1 < -s10), so a family
        that cannot pack into 9 units must fail the build loudly."""
        import pytest

        from scripts.build_edition import _split_popup_units

        # each row ~150 stripped chars: fits a 220-cap unit alone, two don't
        # pack together -> 30 units, far over the 9-unit family ceiling
        rows = [{"cat": "comm", "row": f'<div class="vn-item"><p>{"word " * 30}{i}</p></div>'} for i in range(30)]

        def emit(rs):
            return "".join(r["row"] for r in rs)

        with pytest.raises(ValueError, match="9"):
            _split_popup_units(rows, 220, emit)


# ----------------------------------------------------------------------
# Round 7 — K-R6-2 leg 2: serialized-byte split driver
# ----------------------------------------------------------------------


class TestByteCapResolver:
    def test_unset_defaults_to_8858(self):
        from scripts.build_edition import (
            DEFAULT_NOTE_POPUP_SPLIT_BYTE_CAP,
            resolve_note_popup_split_byte_cap,
        )

        assert DEFAULT_NOTE_POPUP_SPLIT_BYTE_CAP == 8_858
        assert resolve_note_popup_split_byte_cap({"id": "x"}) == 8_858
        assert resolve_note_popup_split_byte_cap({"id": "x", "note_popup_split_byte_cap": None}) == 8_858
        assert resolve_note_popup_split_byte_cap({"id": "x", "note_popup_split_byte_cap": ""}) == 8_858

    def test_zero_disables(self):
        from scripts.build_edition import resolve_note_popup_split_byte_cap

        assert resolve_note_popup_split_byte_cap({"id": "x", "note_popup_split_byte_cap": 0}) == 0

    def test_custom_cap_honored(self):
        from scripts.build_edition import resolve_note_popup_split_byte_cap

        assert resolve_note_popup_split_byte_cap({"id": "x", "note_popup_split_byte_cap": 6000}) == 6000
        assert resolve_note_popup_split_byte_cap({"id": "x", "note_popup_split_byte_cap": "9000"}) == 9000

    def test_invalid_raises(self):
        import pytest

        from scripts.build_edition import resolve_note_popup_split_byte_cap

        with pytest.raises(ValueError):
            resolve_note_popup_split_byte_cap({"id": "x", "note_popup_split_byte_cap": "huge"})
        with pytest.raises(ValueError):
            resolve_note_popup_split_byte_cap({"id": "x", "note_popup_split_byte_cap": -1})


class TestKepubByteEstimator:
    def test_span_overhead_dominates_round6_measured_max(self):
        """Calibrated 2026-06-12 against the round-6 epub↔kepub pair (66,880
        asides matched): per-text-segment koboSpan delta ranged 43.1–81.3 B
        with THIS segmentation rule. The constant must stay >= the measured
        max or the estimator stops dominating the real artifact and gate 4n
        starts failing builds the splitter passed."""
        from scripts.build_edition import _KEPUB_SPAN_OVERHEAD

        assert _KEPUB_SPAN_OVERHEAD >= 82

    def test_estimate_at_least_raw_bytes(self):
        from scripts.build_edition import _estimate_kepub_aside_bytes

        html_s = '<aside id="vnotes-x-1-1-s1"><p>One sentence here.</p></aside>'
        assert _estimate_kepub_aside_bytes(html_s) > len(html_s.encode("utf-8"))

    def test_estimate_grows_per_sentence(self):
        from scripts.build_edition import _KEPUB_SPAN_OVERHEAD, _estimate_kepub_aside_bytes

        one = "<p>" + "Alpha beta gamma delta. " * 1 + "</p>"
        ten = "<p>" + "Alpha beta gamma delta. " * 10 + "</p>"
        d = _estimate_kepub_aside_bytes(ten) - _estimate_kepub_aside_bytes(one)
        raw_d = len(ten.encode("utf-8")) - len(one.encode("utf-8"))
        assert d >= raw_d + 9 * _KEPUB_SPAN_OVERHEAD - 1, "each extra sentence must add a span's overhead"

    def test_markup_dense_runs_each_count(self):
        """em-per-word original-language markup: every inter-tag text run is
        (at least) one koboSpan."""
        from scripts.build_edition import _KEPUB_SPAN_OVERHEAD, _estimate_kepub_aside_bytes

        words = "".join(f"<em>w{i}</em> " for i in range(50))
        est = _estimate_kepub_aside_bytes(f"<p>{words}</p>")
        assert est >= len(f"<p>{words}</p>".encode()) + 50 * _KEPUB_SPAN_OVERHEAD


class TestByteBudgetSplit:
    def test_every_emitted_unit_fits_the_byte_budget(self, tmp_path):
        """Round-6 reality: gen 1:2's char-cap-passing unit serialized to
        15,963 kepub bytes and REFUSED on device. Every emitted verse-notes
        aside must now estimate <= the byte budget. DEFAULT is anchored at
        the 8,858 proven-open floor (estimator dominance over real kepub
        bytes supplies the safety margin; sized shell ensures full <aside>
        est <= cap for any unit the splitter emits). The byte driver is
        eink-only (round-8 Phase 3)."""
        from scripts.build_edition import _estimate_kepub_aside_bytes, apply_badge_markers

        tmp = _book_tree(tmp_path, "gen")
        apply_badge_markers(
            tmp,
            {
                "id": "x",
                "marker_style": "badge",
                "target_reader": "eink",
                "reader_eink_study_layout": "popup",
                **_S2_FLAGS,
            },
        )
        measured = 0
        _VERSE_NOTES_ASIDE_RE = re.compile(
            r'<aside class="verse-notes[^"]*" id="([^"]+)" epub:type="footnote">.*?</aside>',
            re.DOTALL,
        )
        for f in config.get_book("gen")["files"]:
            text = (tmp / f).read_text("utf-8")
            for m in _VERSE_NOTES_ASIDE_RE.finditer(text):
                measured += 1
                est = _estimate_kepub_aside_bytes(m.group(0))
                assert est <= 8_858, f"{m.group(1)} estimates {est:,} kepub bytes (> 8,858 budget)"
        assert measured > 500, "precondition: gen emits many verse-notes units"

    def test_byte_cap_runs_only_on_eink_target(self, tmp_path):
        """The byte driver is a Nickel measure — non-eink editions must not
        byte-split even when the cap is unset (round-8 Phase 3)."""
        from scripts.build_edition import _estimate_kepub_aside_bytes, apply_badge_markers

        tmp = _book_tree(tmp_path, "gen")
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge", **_S2_FLAGS})
        over = 0
        for f in config.get_book("gen")["files"]:
            text = (tmp / f).read_text("utf-8")
            for m in re.finditer(
                r'<aside class="verse-notes" id="[^"]+" epub:type="footnote">.*?</aside>', text, re.DOTALL
            ):
                if _estimate_kepub_aside_bytes(m.group(0)) > 8_858:
                    over += 1
        assert over >= 1, "precondition: gen has byte-over-budget units without the eink driver"

        tmp_eink = _book_tree(tmp_path / "eink", "gen")
        apply_badge_markers(
            tmp_eink,
            {
                "id": "x",
                "marker_style": "badge",
                "target_reader": "eink",
                "reader_eink_study_layout": "popup",
                **_S2_FLAGS,
            },
        )
        for f in config.get_book("gen")["files"]:
            text = (tmp_eink / f).read_text("utf-8")
            for m in re.finditer(
                r'<aside class="verse-notes" id="([^"]+)" epub:type="footnote">.*?</aside>',
                text,
                re.DOTALL,
            ):
                est = _estimate_kepub_aside_bytes(m.group(0))
                assert est <= 8_858, f"{m.group(1)} estimates {est:,} kepub bytes on eink (> 8,858)"

    def test_byte_cap_zero_disables_byte_splitting(self, tmp_path):
        """The knob must gate the behavior: with the byte driver off (char cap
        still default), at least one unit estimates over the 8,858 target —
        the very class the driver exists to kill."""
        from scripts.build_edition import _estimate_kepub_aside_bytes, apply_badge_markers

        tmp = _book_tree(tmp_path, "gen")
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge", "note_popup_split_byte_cap": 0, **_S2_FLAGS})
        over = 0
        for f in config.get_book("gen")["files"]:
            text = (tmp / f).read_text("utf-8")
            for m in re.finditer(
                r'<aside class="verse-notes" id="[^"]+" epub:type="footnote">.*?</aside>', text, re.DOTALL
            ):
                if _estimate_kepub_aside_bytes(m.group(0)) > 8_858:
                    over += 1
        assert over >= 1, "expected over-budget units with the byte driver off (gen 1:2 class)"

    def test_byte_split_conserves_note_text(self, tmp_path):
        """The byte driver must not lose or duplicate text vs a both-caps-off
        run (same conservation contract as the char split)."""
        from scripts.build_edition import apply_badge_markers

        tmp_on = _book_tree(tmp_path / "on", "gen")
        tmp_off = _book_tree(tmp_path / "off", "gen")
        apply_badge_markers(tmp_on, {"id": "x", "marker_style": "badge"})
        apply_badge_markers(
            tmp_off,
            {"id": "x", "marker_style": "badge", "note_popup_split_cap": 0, "note_popup_split_byte_cap": 0},
        )
        fname = next(f for f in config.get_book("gen")["files"] if 'id="v-gen-1-1"' in (tmp_on / f).read_text("utf-8"))
        t_on = (tmp_on / fname).read_text("utf-8")
        t_off = (tmp_off / fname).read_text("utf-8")
        # gen 1:2 = the byte-driver specimen (round-6: 15,963 B unit)
        for coord in ("gen-1-2", "gen-2-7"):
            on_rows = []
            for html_u in _aside_map(t_on, coord).values():
                on_rows.extend(_vn_item_texts(html_u))
            off_units = _aside_map(t_off, coord)
            if not off_units:
                continue  # verse not in this file
            off_rows = _vn_item_texts(next(iter(off_units.values())))
            assert " ".join(" ".join(on_rows).split()) == " ".join(" ".join(off_rows).split()), (
                f"{coord}: byte split lost or duplicated note text"
            )


# ----------------------------------------------------------------------
# K-R5-3 — book-boundary badge clamp
# ----------------------------------------------------------------------


class TestBookBoundaryClamp:
    def test_book_last_verse_badge_stays_before_next_book_title(self, tmp_path):
        """rut 4:22's badge must render BEFORE Samuel's book-title-page div —
        in v0.1.0 all 38 book-last badges spilled into the next book's title
        block (K-R5-3)."""
        from scripts.build_edition import apply_badge_markers

        tmp = _book_tree(tmp_path, "rut")
        fname = next(f for f in config.get_book("rut")["files"] if 'id="v-rut-4-22"' in (tmp / f).read_text("utf-8"))
        base = (tmp / fname).read_text("utf-8")
        v_pos = base.find('id="v-rut-4-22"')
        bp_pos = base.find('<div class="book-title-page"', v_pos)
        assert v_pos != -1 and bp_pos != -1, "precondition: rut end + next title share the file"

        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        text = (tmp / fname).read_text("utf-8")
        badge_pos = text.find('id="vbadge-rut-4-22-s1"')
        title_pos = text.find('<div class="book-title-page"', text.find('id="v-rut-4-22"'))
        assert badge_pos != -1, "rut 4:22 badge missing"
        assert badge_pos < title_pos, "K-R5-3: book-last badge spilled into the next book's title block"


# ----------------------------------------------------------------------
# Artifact gates 4g + 4h (dev/verify_kr2_build.py) — fires-on-defect proofs
# ----------------------------------------------------------------------


def _mini_zip(pieces: dict[str, str]) -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, content in pieces.items():
            z.writestr(name, content)
    return zipfile.ZipFile(io.BytesIO(buf.getvalue()))


class TestGate4gPopupSize:
    def test_fires_on_overcap_verse_notes_aside(self):
        ver = _load_dev_module("verify_kr2_build")
        big = "word " * 1_200  # 6,000 stripped
        zf = _mini_zip(
            {
                "index_split_000.html": (
                    "<html><body><p>s</p>"
                    f'<aside class="verse-notes" id="vnotes-gen-1-1" epub:type="footnote">{big}</aside>'
                    "</body></html>"
                )
            }
        )
        fails, _warns = ver.popup_size_checks(zf, zf.namelist())
        assert any("vnotes-gen-1-1" in f for f in fails), fails

    def test_green_under_floor_and_warns_on_vnote(self):
        ver = _load_dev_module("verify_kr2_build")
        big = "word " * 1_200
        small = "word " * 100
        zf = _mini_zip(
            {
                "index_split_000.html": (
                    "<html><body><p>s</p>"
                    f'<aside class="verse-notes" id="vnotes-gen-1-2" epub:type="footnote">{small}</aside>'
                    f'<aside class="vnote" id="vnote-gen-1-1" epub:type="footnote">{big}</aside>'
                    "</body></html>"
                )
            }
        )
        fails, warns = ver.popup_size_checks(zf, zf.namelist())
        assert fails == [], fails
        assert any("vnote-gen-1-1" in w for w in warns), warns


class TestGate4gBisGlossaryCat:
    def test_fires_on_oversize_study_glossary_cat(self):
        ver = _load_dev_module("verify_kr2_build")
        big = "word " * 2_000  # ~10k stripped
        zf = _mini_zip(
            {
                "index_split_099.html": (
                    "<html><body>"
                    f'<aside epub:type="footnote" class="study-glossary-cat verse-notes" '
                    f'id="vnotes-gen-1-1-hist">{big}</aside>'
                    "</body></html>"
                )
            }
        )
        fails = ver.glossary_cat_checks(zf, zf.namelist())
        assert any("vnotes-gen-1-1-hist" in f for f in fails), fails

    def test_green_under_decline_ceiling(self):
        ver = _load_dev_module("verify_kr2_build")
        ok = "word " * 500
        zf = _mini_zip(
            {
                "index_split_099.html": (
                    "<html><body>"
                    f'<aside epub:type="footnote" class="study-glossary-cat verse-notes" '
                    f'id="vnotes-gen-1-1-hist">{ok}</aside>'
                    "</body></html>"
                )
            }
        )
        assert ver.glossary_cat_checks(zf, zf.namelist()) == []


class TestGate4gTerEmptyVerseRefs:
    def test_fires_on_empty_verse_refs_shell(self):
        ver = _load_dev_module("verify_kr2_build")
        zf = _mini_zip(
            {
                "index_split_001.html": (
                    "<html><body><p>s</p>"
                    '<section class="verse-refs-section" epub:type="footnotes" hidden=""></section>'
                    "</body></html>"
                )
            }
        )
        fails = ver.empty_verse_refs_checks(zf, zf.namelist())
        assert any("empty verse-refs-section" in f for f in fails), fails

    def test_green_when_shell_harvested(self):
        ver = _load_dev_module("verify_kr2_build")
        zf = _mini_zip({"index_split_001.html": "<html><body><p>s</p></body></html>"})
        assert ver.empty_verse_refs_checks(zf, zf.namelist()) == []


class TestGate4hTitlePieceBadges:
    def test_fires_on_badge_in_title_piece(self):
        ver = _load_dev_module("verify_kr2_build")
        zf = _mini_zip(
            {
                "index_split_007.html": (
                    "<html><body>"
                    '<a class="verse-notes-badge" id="vbadge-rut-4-22" href="#vnotes-rut-4-22" '
                    'epub:type="noteref"><sup class="marker-badge">◈4</sup></a>'
                    '<div class="book-title-page" id="bp-9"><p>SAMUEL</p></div>'
                    "</body></html>"
                )
            }
        )
        fails = ver.title_piece_badge_checks(zf, zf.namelist())
        assert any("bp-9" in f or "index_split_007" in f for f in fails), fails

    def test_green_on_clean_title_piece(self):
        ver = _load_dev_module("verify_kr2_build")
        zf = _mini_zip(
            {
                "index_split_007.html": (
                    '<html><body><div class="book-title-page" id="bp-9"><p>SAMUEL</p></div></body></html>'
                ),
                "index_split_008.html": (
                    "<html><body><p>scripture"
                    '<a class="verse-notes-badge" id="vbadge-1sa-1-1" href="#vnotes-1sa-1-1" '
                    'epub:type="noteref"><sup class="marker-badge">◈2</sup></a></p>'
                    '<aside class="verse-notes" id="vnotes-1sa-1-1" epub:type="footnote">ok</aside>'
                    "</body></html>"
                ),
            }
        )
        assert ver.title_piece_badge_checks(zf, zf.namelist()) == []


# ----------------------------------------------------------------------
# Schema / API / UI wiring
# ----------------------------------------------------------------------


class TestGate4mAnchorPrefix:
    def test_fires_on_prefix_nested_family_head(self):
        ver = _load_dev_module("verify_kr2_build")
        zf = _mini_zip(
            {
                "index_split_000.html": (
                    "<html><body>"
                    '<aside class="verse-notes" id="vnotes-gen-1-1" epub:type="footnote">a</aside>'
                    '<aside class="verse-notes" id="vnotes-gen-1-1-s2" epub:type="footnote">b</aside>'
                    "</body></html>"
                )
            }
        )
        fails, _warns = ver.anchor_prefix_checks(zf, zf.namelist())
        assert any("vnotes-gen-1-1" in f for f in fails), fails

    def test_fires_on_cross_verse_digit_extension(self):
        ver = _load_dev_module("verify_kr2_build")
        zf = _mini_zip(
            {
                "index_split_000.html": (
                    "<html><body>"
                    '<aside class="verse-notes" id="vnotes-jub-7-1-s1" epub:type="footnote">a</aside>'
                    '<aside class="verse-notes" id="vnotes-jub-7-1-s12" epub:type="footnote">b</aside>'
                    "</body></html>"
                )
            }
        )
        fails, _warns = ver.anchor_prefix_checks(zf, zf.namelist())
        assert fails, "an -s12 sibling re-creates the strict-prefix defect (-s1 < -s12)"

    def test_fires_on_bare_unsuffixed_id(self):
        # shape check: every vnotes/vbadge id must end -s<1..9> — a bare id is
        # a stale or mixed artifact even when no sibling collides yet
        ver = _load_dev_module("verify_kr2_build")
        zf = _mini_zip(
            {
                "index_split_000.html": (
                    "<html><body>"
                    '<aside class="verse-notes" id="vnotes-gen-9-9" epub:type="footnote">a</aside>'
                    "</body></html>"
                )
            }
        )
        fails, _warns = ver.anchor_prefix_checks(zf, zf.namelist())
        assert any("vnotes-gen-9-9" in f for f in fails), fails

    def test_green_on_study_glossary_cat_navigate_ids_without_s_suffix(self):
        ver = _load_dev_module("verify_kr2_build")
        zf = _mini_zip(
            {
                "index_split_900_00.html": (
                    "<html><body>"
                    '<div class="study-glossary-entry" id="study-entry-isa-40-5">'
                    '<aside epub:type="footnote" class="study-glossary-cat verse-notes" '
                    'id="vnotes-isa-40-5-xref"><p>note</p></aside></div>'
                    "</body></html>"
                )
            }
        )
        fails, _warns = ver.anchor_prefix_checks(zf, zf.namelist())
        assert fails == [], fails

    def test_green_on_prefix_free_namespace_and_warns_on_adjacent_vnote_pair(self):
        ver = _load_dev_module("verify_kr2_build")
        zf = _mini_zip(
            {
                "index_split_000.html": (
                    "<html><body>"
                    '<aside class="verse-notes" id="vnotes-gen-1-1-s1" epub:type="footnote">a</aside>'
                    '<aside class="verse-notes" id="vnotes-gen-1-1-s2" epub:type="footnote">b</aside>'
                    '<aside class="verse-notes" id="vnotes-gen-1-10-s1" epub:type="footnote">c</aside>'
                    '<aside class="vnote" id="vnote-1en-100-1" epub:type="footnote">d</aside>'
                    '<aside class="vnote" id="vnote-1en-100-11" epub:type="footnote">e</aside>'
                    "</body></html>"
                )
            }
        )
        fails, warns = ver.anchor_prefix_checks(zf, zf.namelist())
        assert fails == [], fails
        # the translation (vnote-) namespace is base-baked and un-renamed: an
        # ADJACENT prefix pair there is the device-harmful configuration —
        # surfaced as an honest WARN (1 known corpus-wide: 1en 100:1 < 100:11)
        assert any("vnote-1en-100-1" in w for w in warns), warns


class TestGate4nPopupByteBudget:
    KOBO = '<span class="koboSpan" id="kobo.1.1">x</span>'

    def test_fires_on_oversized_verse_notes_aside_in_kepub(self):
        ver = _load_dev_module("verify_kr2_build")
        big = ('<span class="koboSpan" id="kobo.1.1">' + "word " * 500 + "</span>") * 4  # ~10KB+
        zf = _mini_zip(
            {
                "index_split_000.html": (
                    f"<html><body><p>{self.KOBO}</p>"
                    f'<aside class="verse-notes" id="vnotes-gen-1-1-s1" epub:type="footnote">{big}</aside>'
                    "</body></html>"
                )
            }
        )
        fails, _warns = ver.popup_byte_checks(zf, zf.namelist())
        assert any("vnotes-gen-1-1-s1" in f for f in fails), fails

    def test_warns_on_oversized_vnote_and_green_under_floor(self):
        ver = _load_dev_module("verify_kr2_build")
        big = ('<span class="koboSpan" id="kobo.1.1">' + "word " * 500 + "</span>") * 4
        small = "word " * 50
        zf = _mini_zip(
            {
                "index_split_000.html": (
                    f"<html><body><p>{self.KOBO}</p>"
                    f'<aside class="verse-notes" id="vnotes-gen-1-2-s1" epub:type="footnote">{small}</aside>'
                    f'<aside class="vnote" id="vnote-gen-1-1" epub:type="footnote">{big}</aside>'
                    "</body></html>"
                )
            }
        )
        fails, warns = ver.popup_byte_checks(zf, zf.namelist())
        assert fails == [], fails
        assert any("vnote-gen-1-1" in w for w in warns), warns

    def test_skips_plain_epub(self):
        # pre-kepubify bytes are not the device measure — the gate only judges
        # artifacts that carry koboSpans
        ver = _load_dev_module("verify_kr2_build")
        big = "word " * 3000
        zf = _mini_zip(
            {
                "index_split_000.html": (
                    "<html><body>"
                    f'<aside class="verse-notes" id="vnotes-gen-1-1-s1" epub:type="footnote">{big}</aside>'
                    "</body></html>"
                )
            }
        )
        fails, warns = ver.popup_byte_checks(zf, zf.namelist())
        assert fails == [] and warns == []


class TestSplitCapWiring:
    def test_api_validates_and_persists_note_popup_split_cap(self):
        from scripts.api.editions import api_save_edition_meta

        path = REPO / "content" / "editions.yaml"
        before = path.read_bytes()
        try:
            r = api_save_edition_meta("catholic-study", {"note_popup_split_cap": 5200})
            assert "error" not in r, r
            text = path.read_text(encoding="utf-8")
            assert "note_popup_split_cap: 5200" in text
        finally:
            path.write_bytes(before)
            config.load_editions.cache_clear()

    def test_api_rejects_bad_cap(self):
        from scripts.api.editions import api_save_edition_meta

        path = REPO / "content" / "editions.yaml"
        before = path.read_bytes()
        try:
            assert "error" in api_save_edition_meta("catholic-study", {"note_popup_split_cap": "huge"})
            assert "error" in api_save_edition_meta("catholic-study", {"note_popup_split_cap": -3})
            assert path.read_bytes() == before, "a rejected save must not write"
        finally:
            path.write_bytes(before)
            config.load_editions.cache_clear()

    def test_preview_knows_the_field(self):
        from scripts.api.editions import api_preview_edition_changes

        r = api_preview_edition_changes("catholic-study", {"note_popup_split_cap": 1234})
        assert "unknown_fields" not in r, r
        assert any(c["field"] == "note_popup_split_cap" for c in r["changes"])

    def test_customize_console_exposes_the_field(self):
        import scripts.templates.customize as cz

        assert 'data-field="note_popup_split_cap"' in cz.CUSTOMIZE_HTML

    def test_api_validates_and_persists_byte_cap(self):
        from scripts.api.editions import api_save_edition_meta

        path = REPO / "content" / "editions.yaml"
        before = path.read_bytes()
        try:
            r = api_save_edition_meta("catholic-study", {"note_popup_split_byte_cap": 9000})
            assert "error" not in r, r
            text = path.read_text(encoding="utf-8")
            assert "note_popup_split_byte_cap: 9000" in text
        finally:
            path.write_bytes(before)
            config.load_editions.cache_clear()

    def test_api_rejects_bad_byte_cap(self):
        from scripts.api.editions import api_save_edition_meta

        path = REPO / "content" / "editions.yaml"
        before = path.read_bytes()
        try:
            assert "error" in api_save_edition_meta("catholic-study", {"note_popup_split_byte_cap": "huge"})
            assert "error" in api_save_edition_meta("catholic-study", {"note_popup_split_byte_cap": -3})
            assert path.read_bytes() == before, "a rejected save must not write"
        finally:
            path.write_bytes(before)
            config.load_editions.cache_clear()

    def test_preview_knows_the_byte_cap(self):
        from scripts.api.editions import api_preview_edition_changes

        r = api_preview_edition_changes("catholic-study", {"note_popup_split_byte_cap": 7777})
        assert "unknown_fields" not in r, r
        assert any(c["field"] == "note_popup_split_byte_cap" for c in r["changes"])

    def test_customize_console_exposes_the_byte_cap(self):
        import scripts.templates.customize as cz

        assert 'data-field="note_popup_split_byte_cap"' in cz.CUSTOMIZE_HTML


class TestGate4iBadgeModeMarkerLeak:
    def test_fires_on_leftover_note_ref_in_badge_artifact(self):
        ver = _load_dev_module("verify_kr2_build")
        zf = _mini_zip(
            {
                "index_split_060.html": (
                    "<html><body><p>text"
                    '<a class="verse-notes-badge" id="vbadge-rev-22-21" href="#vnotes-rev-22-21" '
                    'epub:type="noteref"><sup class="marker-badge">◈3</sup></a>'
                    '<a class="note-ref note-topic-nave" id="ref-b862221c" href="#note-b862221c" '
                    'epub:type="noteref"><sup class="marker-num">4</sup></a></p>'
                    '<aside class="verse-notes" id="vnotes-rev-22-21" epub:type="footnote">x</aside>'
                    '<aside class="note note-topic-nave" id="note-b862221c" epub:type="footnote">y</aside>'
                    "</body></html>"
                )
            }
        )
        fails = ver.badge_mode_leak_checks(zf, zf.namelist())
        assert any("note-ref" in f for f in fails), fails

    def test_quiet_in_numbers_mode_artifact(self):
        # no verse-notes badge anywhere => numbers mode => note-ref markers are
        # the contract, not a leak
        ver = _load_dev_module("verify_kr2_build")
        zf = _mini_zip(
            {
                "index_split_000.html": (
                    '<html><body><p>text<a class="note-ref note-x" id="ref-1" href="#note-1" '
                    'epub:type="noteref"><sup class="marker-num">1</sup></a></p>'
                    '<aside class="note note-x" id="note-1" epub:type="footnote">y</aside>'
                    "</body></html>"
                )
            }
        )
        assert ver.badge_mode_leak_checks(zf, zf.namelist()) == []
