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
        rf'<aside class="verse-notes" id="(vnotes-{coord}(?:-s\d+)?)" epub:type="footnote">.*?</aside>',
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
        from scripts.build_edition import _stripped_len, apply_badge_markers

        tmp = _book_tree(tmp_path, "gen")
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        fname = next(f for f in config.get_book("gen")["files"] if 'id="v-gen-1-1"' in (tmp / f).read_text("utf-8"))
        text = (tmp / fname).read_text("utf-8")

        units = _aside_map(text, "gen-1-1")
        assert "vnotes-gen-1-1" in units, "unit 1 must keep the unsuffixed id"
        assert len(units) >= 2, "gen 1:1 (~9k stripped) must split"
        # suffixes are sequential from s2
        suffixed = sorted(k for k in units if k != "vnotes-gen-1-1")
        assert suffixed == [f"vnotes-gen-1-1-s{i}" for i in range(2, len(units) + 1)]
        for uid, html_u in units.items():
            assert _stripped_len(html_u) <= 4_400, f"{uid} still over the cap"
            # each unit's back-link points at its OWN badge
            bid = uid.replace("vnotes-", "vbadge-")
            assert f'href="#{bid}"' in html_u
            assert f'id="{bid}"' in text, f"badge {bid} missing"

    def test_badge_cluster_sits_together_at_verse_end(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        tmp = _book_tree(tmp_path, "gen")
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        fname = next(f for f in config.get_book("gen")["files"] if 'id="v-gen-1-1"' in (tmp / f).read_text("utf-8"))
        text = (tmp / fname).read_text("utf-8")
        # the cluster: unsuffixed badge immediately followed (single space) by -s2
        m = re.search(r'<a class="verse-notes-badge" id="vbadge-gen-1-1" .*?</a>', text, re.DOTALL)
        assert m
        tail = text[m.end() :]
        assert tail.startswith(' <a class="verse-notes-badge" id="vbadge-gen-1-1-s2"'), tail[:90]

    def test_under_cap_verse_byte_identical_to_legacy_form(self, tmp_path):
        from scripts.build_edition import _stripped_len, apply_badge_markers

        tmp = _book_tree(tmp_path, "gen")
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        fname = next(f for f in config.get_book("gen")["files"] if 'id="v-gen-1-1"' in (tmp / f).read_text("utf-8"))
        text = (tmp / fname).read_text("utf-8")
        # gen 1:3 is the round-3 control (~3.1k stripped) — must NOT split and
        # must keep the exact historical single-badge shape.
        units = _aside_map(text, "gen-1-3")
        assert list(units) == ["vnotes-gen-1-3"]
        assert _stripped_len(units["vnotes-gen-1-3"]) <= 4_400
        assert 'id="vbadge-gen-1-3-s2"' not in text
        bm = re.search(r'<a class="verse-notes-badge" id="vbadge-gen-1-3" [^>]*>', text)
        assert bm and 'epub:type="noteref"' in bm.group(0)
        assert "part" not in bm.group(0)

    def test_conservation_against_cap_off_run(self, tmp_path):
        """Splitting must conserve EVERY .vn-item row's text (nothing dropped,
        nothing duplicated) — compare against a cap=0 (off) run of the same tree."""
        from scripts.build_edition import apply_badge_markers

        tmp_on = _book_tree(tmp_path / "on", "gen")
        tmp_off = _book_tree(tmp_path / "off", "gen")
        apply_badge_markers(tmp_on, {"id": "x", "marker_style": "badge"})
        apply_badge_markers(tmp_off, {"id": "x", "marker_style": "badge", "note_popup_split_cap": 0})
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
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge", "note_popup_split_cap": 0})
        fname = next(f for f in config.get_book("gen")["files"] if 'id="v-gen-1-1"' in (tmp / f).read_text("utf-8"))
        text = (tmp / fname).read_text("utf-8")
        units = _aside_map(text, "gen-1-1")
        assert list(units) == ["vnotes-gen-1-1"]
        assert _stripped_len(units["vnotes-gen-1-1"]) > 4_400  # the unsplit giant

    def test_s2_cascade_path_splits_with_category_heads(self, tmp_path):
        """The shipped eth profile (S2 cascade on) must split too, each unit a
        well-formed cascade (category heads present; conservation guard quiet)."""
        from scripts.build_edition import _stripped_len, apply_badge_markers

        tmp = _book_tree(tmp_path, "gen")
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge", **_S2_FLAGS})
        fname = next(f for f in config.get_book("gen")["files"] if 'id="v-gen-1-1"' in (tmp / f).read_text("utf-8"))
        text = (tmp / fname).read_text("utf-8")
        units = _aside_map(text, "gen-1-1")
        assert len(units) >= 2
        for uid, html_u in units.items():
            assert _stripped_len(html_u) <= 4_400, uid
            assert 'class="vn-cat-head"' in html_u, f"{uid}: cascade head missing"

    def test_giant_single_note_chunked_within_body(self, tmp_path):
        """1sa 16:12 carries ONE ~19k dict-easton note (Easton's DAVID) — design
        (b): the body chunks across multiple units, visibly marked continued."""
        from scripts.build_edition import _stripped_len, apply_badge_markers

        tmp = _book_tree(tmp_path, "1sa")
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge", **_S2_FLAGS})
        fname = next(f for f in config.get_book("1sa")["files"] if 'id="v-1sa-16-12"' in (tmp / f).read_text("utf-8"))
        text = (tmp / fname).read_text("utf-8")
        units = _aside_map(text, "1sa-16-12")
        assert len(units) >= 4, f"19k body should chunk into >=4 units, got {len(units)}"
        for uid, html_u in units.items():
            assert _stripped_len(html_u) <= 4_400, uid
        assert any("vn-cont" in u for u in units.values()), "no continuation chunk marked vn-cont"
        assert any('class="vn-cont-mark"' in u for u in units.values())


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
        badge_pos = text.find('id="vbadge-rut-4-22"')
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
