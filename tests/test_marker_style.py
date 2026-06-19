"""`marker_style` edition field (Wave 3 §4.1) — the note-marker display enum.

Two modes:

  - ``numbers`` (selectable) — the historical per-note superscript number, one
    inline marker per note. Realized BASE-WIDE by the re-bake
    (``resync_marker_glyphs`` numbers the shared base); the build's
    ``renumber_markers`` pass closes the gaps a kind/id filter leaves.
  - ``badge`` (the DEFAULT, Phase 5) — clean scripture with ONE note-count
    badge per verse → tap → that verse's notes as a list, via the native
    EPUB3 popup-footnote contract (``noteref`` → ``footnote``, no JS).
    Realized at BUILD TIME by ``apply_badge_markers`` as a per-edition
    post-pass over the temp HTML (``epub_working/`` stays the canonical
    ``numbers`` form — no base re-bake).

Wired like the other enum settings: const + api_save_edition_meta validation +
api_customize_data default + /customize <select>.
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

BASETEMP = Path(r"C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt")


class TestMarkerStyleConst:
    def test_enum_exposes_numbers(self):
        from scripts.build_edition import MARKER_STYLES

        assert "numbers" in MARKER_STYLES

    def test_badge_is_now_a_valid_value(self):
        from scripts.build_edition import MARKER_STYLES

        assert "badge" in MARKER_STYLES


class TestMarkerStyleValidator:
    def test_accepts_badge(self):
        from scripts.api.editions import api_save_edition_meta

        edyaml = REPO / "content" / "editions.yaml"
        backup = edyaml.read_bytes()
        try:
            res = api_save_edition_meta("catholic-study", {"marker_style": "badge"})
            assert "error" not in res, res
            config.load_editions.cache_clear()
            assert config.editions_by_id()["catholic-study"].get("marker_style") == "badge"
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()

    def test_rejects_unknown_value(self):
        from scripts.api.editions import api_save_edition_meta

        res = api_save_edition_meta("catholic-study", {"marker_style": "bogus"})
        assert "error" in res and "marker_style" in res["error"]

    def test_accepts_and_persists_numbers(self):
        from scripts.api.editions import api_save_edition_meta

        edyaml = REPO / "content" / "editions.yaml"
        backup = edyaml.read_bytes()
        try:
            res = api_save_edition_meta("catholic-study", {"marker_style": "numbers"})
            assert "error" not in res, res
            config.load_editions.cache_clear()
            assert config.editions_by_id()["catholic-study"].get("marker_style") == "numbers"
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()


class TestMarkerStyleLoader:
    def test_api_customize_data_defaults_to_badge(self):
        from scripts.web import api_customize_data

        eds = {e["id"]: e for e in api_customize_data()["editions"]}
        # catholic-study does not pin marker_style → it surfaces the code default.
        assert eds["catholic-study"].get("marker_style") == "badge"


class TestMarkerStyleUI:
    def test_customize_template_has_the_select(self):
        src = (REPO / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")
        assert 'data-field="marker_style"' in src

    def test_customize_template_badge_not_disabled(self):
        src = (REPO / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")
        # The badge <option> must be selectable now (no `disabled`).
        m = re.search(r'<option value="badge"[^>]*>', src)
        assert m, "badge option missing from /customize"
        assert "disabled" not in m.group(0), "badge option still disabled"


# ----------------------------------------------------------------------
# Badge transform — unit tests (fast, no full build)
# ----------------------------------------------------------------------


class TestApplyBadgeMarkersUnit:
    """``apply_badge_markers`` rewrites a filtered temp tree in place: per-verse
    markers → one count badge; per-note asides → one merged verse aside."""

    def _gen1_file(self):
        """Return the real gen ch1 file's text from epub_working (the canonical
        ``numbers`` base) for a focused unit transform."""
        from scripts.core import config as _c

        book = _c.get_book("gen")
        epub = REPO / "epub_working"
        # gen ch1 lives in the first split file that carries v-gen-1-1
        for fname in book["files"]:
            t = (epub / fname).read_text(encoding="utf-8")
            if 'id="v-gen-1-1"' in t:
                return fname, t
        raise AssertionError("gen 1 base file not found")

    def test_badge_replaces_per_note_markers_in_one_verse(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        fname, _ = self._gen1_file()
        # Build a minimal temp tree of just gen's files so the book iterator
        # has its real verse regions to walk.
        from scripts.core import config as _c

        book = _c.get_book("gen")
        epub = REPO / "epub_working"
        tmp = tmp_path / "build"
        tmp.mkdir()
        for f in book["files"]:
            (tmp / f).write_text((epub / f).read_text(encoding="utf-8"), encoding="utf-8")

        stats = apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        assert stats["badges_inserted"] > 0

        text = (tmp / fname).read_text(encoding="utf-8")
        # (a) no per-note inline markers survive in the transformed file
        assert 'class="note-ref' not in text, "per-note markers must be gone in badge mode"
        # (b) exactly one badge per verse-that-has-notes; gen 1 has 31 such verses
        # round-7 -s split: a verse with an oversized popup emits multiple -sN
        # (badge, aside) units, so count DISTINCT verses-with-badges, not raw units.
        v1_verses = set(re.findall(r'id="vbadge-gen-1-(\d+)(?:-s\d+)?"', text))
        assert len(v1_verses) == 31, f"expected 31 gen-1 verses-with-badges, got {len(v1_verses)}"
        # RX-beta2 ①: the badge glyph is the ◈ note-mark + a count (never a bare
        # number that blends with the verse number / the translation marker).
        for sup in re.findall(r'<sup class="marker-badge">([^<]*)</sup>', text):
            assert sup.startswith("◈"), f"badge sup missing the ◈ glyph: {sup!r}"
        # RX-beta2 ②③: each badge's displayed count == the number of de-duped,
        # grouped .vn-item rows in its merged aside, and the chapter total is
        # CONSERVED-OR-LOWER vs the 225 raw base markers (dedup may drop byte-
        # identical repeats — e.g. the gen 1:1 duplicate cross-ref — nothing else).
        total = 0
        for vv in re.findall(r'id="vbadge-gen-1-(\d+)(?:-s\d+)?"', text):
            bm = re.search(rf'id="vbadge-gen-1-{vv}(?:-s\d+)?"[^>]*title="(\d+) notes?[^"]*"', text)
            am = re.search(
                rf'<aside class="verse-notes" id="vnotes-gen-1-{vv}(?:-s\d+)?"[^>]*>(.*?)</aside>',
                text,
                re.DOTALL,
            )
            assert bm and am, f"gen 1:{vv} badge/aside missing"
            cnt = int(bm.group(1))
            rows = am.group(1).count('class="vn-item')
            assert cnt == rows, f"gen 1:{vv} badge count {cnt} != {rows} rows in its aside"
            total += cnt
        assert 0 < total <= 225, f"gen 1 badge counts sum {total} should be in (0, 225]"

    def test_tablet_one_badge_per_verse_gen_1_1(self, tmp_path):
        """Apple M2 — Gen 1:1 carries ONE study badge with the full note count."""
        from scripts.build_edition import apply_badge_markers
        from scripts.core import config as _c

        book = _c.get_book("gen")
        epub = REPO / "epub_working"
        tmp = tmp_path / "build"
        tmp.mkdir()
        for f in book["files"]:
            (tmp / f).write_text((epub / f).read_text(encoding="utf-8"), encoding="utf-8")

        edition = {
            "id": "ethiopian-tewahedo",
            "marker_style": "badge",
            "target_reader": "tablet",
            "note_attribution_dedup": True,
            "note_group_by_category": True,
            "note_topic_dedup": True,
        }
        apply_badge_markers(tmp, edition)
        fname = next(f for f in book["files"] if 'id="v-gen-1-1"' in (tmp / f).read_text(encoding="utf-8"))
        text = (tmp / fname).read_text(encoding="utf-8")

        assert text.count('id="vbadge-gen-1-1-s1"') == 1, "gen 1:1 must have exactly one study badge unit"
        assert 'id="vbadge-gen-1-1-s2"' not in text, "tablet must not emit multi-unit badge splits"
        bm = re.search(r'id="vbadge-gen-1-1-s1"[^>]*title="(\d+) notes?"', text)
        assert bm, "gen 1:1 badge must carry a note count"
        assert "part " not in bm.group(0), "tablet badge must not show continuation parts"
        am = re.search(
            r'<aside class="verse-notes" id="vnotes-gen-1-1-s1"[^>]*>(.*?)</aside>',
            text,
            re.DOTALL,
        )
        assert am, "gen 1:1 must have one merged study aside"
        assert 'id="vnotes-gen-1-1-s2"' not in text, "tablet must not emit multi-unit aside splits"
        rows = am.group(1).count('class="vn-item')
        assert int(bm.group(1)) == rows, f"badge count {bm.group(1)} != {rows} vn-item rows"

    def test_badge_sits_at_verse_end_not_mid_verse(self, tmp_path):
        """device-QA (Kobo, 2026-06-09): the note badge must TRAIL the verse, not sit
        at the last annotated word. A verse whose only note is on an early word would
        otherwise drop the badge right beside the verse-number popup trigger, and the
        Kobo's coarse tap box makes the two easy to mis-hit. The verse number leads the
        verse (start); the badge trails it (end) so the two triggers never cluster.
        Gen 1 is run-in prose (all verses in one <p>), so 'badge at verse end' means
        nothing but the badge sits between a verse's prose and the NEXT verse number."""
        from scripts.build_edition import apply_badge_markers
        from scripts.core import config as _c

        book = _c.get_book("gen")
        epub = REPO / "epub_working"
        tmp = tmp_path / "build"
        tmp.mkdir()
        for f in book["files"]:
            (tmp / f).write_text((epub / f).read_text(encoding="utf-8"), encoding="utf-8")

        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        fname = next(f for f in book["files"] if 'id="v-gen-1-1"' in (tmp / f).read_text(encoding="utf-8"))
        text = (tmp / fname).read_text(encoding="utf-8")

        checked = 0
        for v in range(1, 31):  # gen 1 has 31 verses; v+1 must exist for the check
            bm = re.search(rf'<a class="verse-notes-badge" id="vbadge-gen-1-{v}(?:-s\d+)?" .*?</a>', text, re.DOTALL)
            if not bm:
                continue
            tail = text[bm.end() :].lstrip()
            # K-R4-2: an over-cap verse carries a CLUSTER of sibling badges
            # (vbadge-…-s2, -s3, …) at the same verse-end spot — walk past
            # them; the invariant is the WHOLE cluster trails the verse.
            while tail.startswith(f'<a class="verse-notes-badge" id="vbadge-gen-1-{v}-s'):
                nxt = re.match(r'<a class="verse-notes-badge".*?</a>', tail, re.DOTALL)
                assert nxt is not None
                tail = tail[nxt.end() :].lstrip()
            # K-R15a: badge-trail spacer follows the cluster before the next vn-link.
            if tail.startswith('<span class="badge-trail"'):
                trail = re.match(r'<span class="badge-trail"[^>]*>.*?</span>', tail, re.DOTALL)
                assert trail is not None
                tail = tail[trail.end() :].lstrip()
            assert tail.startswith(f'<a class="vn-link" id="v-gen-1-{v + 1}"'), (
                f"gen 1:{v} badge is not at verse end — verse prose follows it before v{v + 1}"
            )
            checked += 1
        assert checked >= 5, f"expected to verify several gen-1 verses, only checked {checked}"

    def test_one_merged_aside_per_verse_with_notes(self, tmp_path):
        from scripts.build_edition import apply_badge_markers
        from scripts.core import config as _c

        book = _c.get_book("gen")
        epub = REPO / "epub_working"
        tmp = tmp_path / "build"
        tmp.mkdir()
        for f in book["files"]:
            (tmp / f).write_text((epub / f).read_text(encoding="utf-8"), encoding="utf-8")

        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        fname = next(f for f in book["files"] if 'id="v-gen-1-1"' in (tmp / f).read_text(encoding="utf-8"))
        text = (tmp / fname).read_text(encoding="utf-8")
        # (c) one merged aside per verse-with-notes; none of the old per-note asides
        assert 'class="note note-' not in text, "per-note asides must be merged away"
        merged = re.findall(r'<aside class="verse-notes" id="vnotes-gen-1-(\d+)(?:-s\d+)?" epub:type="footnote">', text)
        # round-7 -s split: >=1 -sN aside per verse-with-notes; assert per-verse coverage.
        assert len(set(merged)) == 31, f"expected 31 gen-1 verses-with-asides, got {len(set(merged))}"
        # (d) every badge href resolves to its vnotes aside id
        for vv in re.findall(r'href="#vnotes-gen-1-(\d+)(?:-s\d+)?"', text):
            assert f'id="vnotes-gen-1-{vv}-s1"' in text, f"badge href #vnotes-gen-1-{vv} has no aside"
        # the merged aside for v1 lists one .vn-item per UNIQUE note in that verse's
        # region; the count matches the badge (post-dedup, post-grouping).
        m = re.search(
            r'<aside class="verse-notes" id="vnotes-gen-1-1-s1"[^>]*>(.*?)</aside>',
            text,
            re.DOTALL,
        )
        assert m
        bm = re.search(r'id="vbadge-gen-1-1-s1"[^>]*title="(\d+) notes?[^"]*"', text)
        assert bm
        assert m.group(1).count('class="vn-item') == int(bm.group(1))

    def test_orphan_marker_verse_is_skipped_and_counted(self, tmp_path):
        # round-5 audit Phase 4 (LOW): a verse whose inline marker has no matching
        # aside must be SKIPPED (no badge with a popup short a row) AND counted in
        # ``badges_skipped`` — not silently dropped. Construct the orphan by
        # deleting exactly one of gen 1's asides while leaving its inline marker.
        from scripts.build_edition import apply_badge_markers
        from scripts.core import config as _c

        book = _c.get_book("gen")
        epub = REPO / "epub_working"
        tmp = tmp_path / "build"
        tmp.mkdir()
        target = None
        for f in book["files"]:
            t = (epub / f).read_text(encoding="utf-8")
            (tmp / f).write_text(t, encoding="utf-8")
            if target is None and 'id="v-gen-1-1"' in t:
                target = f
        assert target is not None, "gen 1 base file not found"

        text = (tmp / target).read_text(encoding="utf-8")
        # Drop exactly ONE per-note aside (same file as its marker — inject
        # co-locates them), orphaning that marker.
        new_text, n = re.subn(
            r'<aside class="note note-[a-z][a-z0-9-]*" id="note-[^"]+"[^>]*>.*?</aside>',
            "",
            text,
            count=1,
            flags=re.DOTALL,
        )
        assert n == 1, "fixture: expected to remove exactly one aside"
        (tmp / target).write_text(new_text, encoding="utf-8")

        stats = apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        assert stats["badges_skipped"] >= 1, f"orphaned-marker verse was not counted as skipped: {stats}"
        # Only the orphaned verse bails; the rest of gen 1 still badges normally.
        assert stats["badges_inserted"] >= 1, f"expected the non-orphan verses to still badge: {stats}"

    def test_idempotent_and_no_nested_anchor(self, tmp_path):
        from scripts.build_edition import apply_badge_markers
        from scripts.check_nested_anchors import find_nested_anchors
        from scripts.core import config as _c

        book = _c.get_book("gen")
        epub = REPO / "epub_working"
        tmp = tmp_path / "build"
        tmp.mkdir()
        for f in book["files"]:
            (tmp / f).write_text((epub / f).read_text(encoding="utf-8"), encoding="utf-8")

        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        fname = next(f for f in book["files"] if 'id="vbadge-gen-1-1-s1"' in (tmp / f).read_text(encoding="utf-8"))
        once = (tmp / fname).read_text(encoding="utf-8")
        # no nested <a> introduced by the badge (the badge is itself an <a>)
        assert find_nested_anchors(once) == [], "badge introduced a nested <a> (RSC-005)"
        # second pass is a no-op (idempotent / deterministic)
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        twice = (tmp / fname).read_text(encoding="utf-8")
        assert twice == once, "apply_badge_markers is not idempotent"

    def test_dedup_drops_byte_identical_note(self, tmp_path):
        # RX-beta2 ②: a verse carrying two byte-identical-CONTENT notes (the
        # duplicate-cross-ref class of bug) collapses to ONE row. Construct it by
        # cloning a real note's marker + aside under a fresh id in gen 1.
        from scripts.build_edition import apply_badge_markers
        from scripts.core import config as _c

        book = _c.get_book("gen")
        epub = REPO / "epub_working"
        tmp = tmp_path / "build"
        tmp.mkdir()
        target = None
        for f in book["files"]:
            t = (epub / f).read_text(encoding="utf-8")
            (tmp / f).write_text(t, encoding="utf-8")
            if target is None and 'id="v-gen-1-1"' in t:
                target, ttext = f, t
        assert target is not None
        mk = re.search(r'<a class="note-ref note-([a-z0-9-]+)" id="ref-([^"]+)"[^>]*>.*?</a>', ttext, re.DOTALL)
        assert mk
        kind, fid = mk.group(1), mk.group(2)
        am = re.search(
            r'<aside class="note note-' + re.escape(kind) + r'" id="note-' + re.escape(fid) + r'"[^>]*>.*?</aside>',
            ttext,
            re.DOTALL,
        )
        assert am
        dup_marker = mk.group(0).replace(f'id="ref-{fid}"', f'id="ref-{fid}DUP"')
        dup_aside = am.group(0).replace(f'id="note-{fid}"', f'id="note-{fid}DUP"')
        new = ttext.replace(mk.group(0), mk.group(0) + dup_marker, 1).replace(am.group(0), am.group(0) + dup_aside, 1)
        (tmp / target).write_text(new, encoding="utf-8")
        stats = apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        assert stats["notes_deduped"] >= 1, f"injected duplicate note was not de-duped: {stats}"

    def test_badge_rows_grouped_by_category_order(self, tmp_path):
        # RX-beta2 ③: within each merged aside, rows are ordered by the fixed
        # category rank (most-useful first; the long topical block always last).
        from scripts.build_edition import (
            apply_badge_markers,
            _POPUP_CATEGORY_RANK,
            _POPUP_CATEGORY_FALLBACK_RANK,
        )
        from scripts.inject import category_for
        from scripts.core import config as _c

        book = _c.get_book("gen")
        epub = REPO / "epub_working"
        tmp = tmp_path / "build"
        tmp.mkdir()
        for f in book["files"]:
            (tmp / f).write_text((epub / f).read_text(encoding="utf-8"), encoding="utf-8")
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        checked = 0
        for f in book["files"]:
            text = (tmp / f).read_text(encoding="utf-8")
            for aside in re.findall(r'<aside class="verse-notes"[^>]*>(.*?)</aside>', text, re.DOTALL):
                kinds = re.findall(r'<div class="vn-item note-([a-z0-9-]+)">', aside)
                if len(kinds) < 2:
                    continue
                ranks = [_POPUP_CATEGORY_RANK.get(category_for(k), _POPUP_CATEGORY_FALLBACK_RANK) for k in kinds]
                assert ranks == sorted(ranks), f"badge rows not in category order in {f}: {kinds}"
                if any(category_for(k) == "topic" for k in kinds):
                    assert category_for(kinds[-1]) == "topic", "topical note not grouped last"
                checked += 1
        assert checked > 0, "no multi-note badge asides found to check grouping"

    def test_chapter_last_verse_badge_stays_in_its_chapter(self, tmp_path):
        """K-R3-3/K-R3-4 (Kobo round 3, kobo8): inject's spill resolver bakes some
        of a chapter-last verse's xref/topic markers AFTER the next chapter's
        heading; the badge — placed at the LAST marker — then renders inside the
        WRONG chapter (264 artifact instances; gen 1:31's ◈ badge led Gen 2's
        first paragraph and its tap "teleported to chapter 1"). The badge must
        stay at its verse's own text end; the spilled markers still merge into
        the verse's aside (collection unchanged — placement only)."""
        from scripts.build_edition import apply_badge_markers
        from scripts.core import config as _c

        book = _c.get_book("gen")
        epub = REPO / "epub_working"
        tmp = tmp_path / "build"
        tmp.mkdir()
        for f in book["files"]:
            (tmp / f).write_text((epub / f).read_text(encoding="utf-8"), encoding="utf-8")
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})

        # (a) the canonical instance: gen 1:31's badge sits at the verse end —
        #     BEFORE the ch-2 anchor, immediately preceding its paragraph close.
        fname = next(f for f in book["files"] if 'id="v-gen-1-31"' in (tmp / f).read_text(encoding="utf-8"))
        text = (tmp / fname).read_text(encoding="utf-8")
        bm = re.search(r'<a class="verse-notes-badge" id="vbadge-gen-1-31(?:-s\d+)?.*?</a>', text, re.DOTALL)
        ch2 = re.search(r'<a id="ch-b\d+-c2" class="ch-anchor">', text)
        assert bm and ch2, "gen 1:31 badge / ch-2 anchor missing"
        assert bm.end() <= ch2.start(), "gen 1:31's badge rendered past the chapter-2 heading (K-R3-4)"
        tail = text[bm.end() :].lstrip()
        # K-R15a: badge-trail spacer may follow the badge before </p>.
        if tail.startswith('<span class="badge-trail"'):
            trail = re.match(r'<span class="badge-trail"[^>]*>.*?</span>', tail, re.DOTALL)
            assert trail, "gen 1:31 badge-trail span malformed"
            tail = tail[trail.end() :].lstrip()
        assert tail.startswith("</p>"), (
            "gen 1:31's badge is not at the verse's text end (must directly precede the paragraph close)"
        )

        # (b) conservation: the spilled markers' notes still merge into the aside —
        #     the badge count equals the aside's rows. Current base: 2 inline
        #     (g0131c/d) + 5 spilled (g0131a/b/e/f/g) = 7 pre-dedup; RX-beta2
        #     byte-dedup may collapse near-identical xref rows (→ 5 surviving).
        tb = re.search(r'id="vbadge-gen-1-31(?:-s\d+)?"[^>]*title="(\d+) notes?[^"]*"', text)
        am = re.search(r'<aside class="verse-notes" id="vnotes-gen-1-31(?:-s\d+)?"[^>]*>(.*?)</aside>', text, re.DOTALL)
        assert tb and am
        rows = am.group(1).count('class="vn-item')
        assert int(tb.group(1)) == rows, "badge count != merged-aside rows for gen 1:31"
        assert rows >= 5, f"gen 1:31's spilled notes were dropped from its aside (rows={rows})"

        # (c) the CLASS, whole-book: walking every gen file in document order, no
        #     badge may appear after a chapter anchor numbered past its own chapter —
        #     and no splice corruption: every vbadge id keeps its <a> head (a sheared
        #     badge = the kr3a overlapping-splice bug) and every <aside> stays balanced.
        for f in book["files"]:
            t = (tmp / f).read_text(encoding="utf-8")
            heads = t.count('<a class="verse-notes-badge"')
            vbids = len(re.findall(r'\bid="vbadge-', t))
            assert heads == vbids, f"{f}: {vbids - heads} sheared badge anchor(s) — splice overlap corruption"
            opens = len(re.findall(r"<aside\b", t))
            closes = t.count("</aside>")
            assert opens == closes, f"{f}: unbalanced <aside> ({opens} open / {closes} close)"
            # no badge may sit INSIDE an aside (the silent kr3a variant: 263
            # badges landed inside notes-section asides — well-formed but
            # invisible to the reader).
            walk = sorted(
                [(m.start(), 1) for m in re.finditer(r"<aside\b", t)]
                + [(m.start(), -1) for m in re.finditer(r"</aside>", t)]
                + [(m.start(), 0) for m in re.finditer(r'<a class="verse-notes-badge"', t)]
            )
            depth = 0
            for _pos, d in walk:
                if d == 0:
                    assert depth == 0, f"{f}: a verse-notes badge is nested inside an aside (hidden from the reader)"
                else:
                    depth += d
            events: list[tuple[int, str, int]] = []
            for m in re.finditer(r'id="ch-b\d+-c(\d+)"', t):
                events.append((m.start(), "ch", int(m.group(1))))
            for m in re.finditer(r'id="vbadge-gen-(\d+)-(\d+)(?:-s\d+)?', t):
                events.append((m.start(), "badge", int(m.group(1))))
            cur = None
            for _pos, kind, val in sorted(events):
                if kind == "ch":
                    cur = val
                elif cur is not None:
                    assert val >= cur, f"{f}: a gen {val} badge renders inside chapter {cur} (K-R3-4 class)"


class TestKoboPreviewSeparators:
    """K-R3-2 (Kobo round 3, kobo1/5/6/7): Kobo eInk's Footnote preview is a
    TAG-STRIPPED plain-text extraction (vendor-documented) — every block
    boundary in the merged aside flattens into one run-on line. The fix bakes
    plain-TEXT separators into the markup (`.vn-sep` spans: ¶ before category
    heads, ◦ before source bylines, • before each note row) and hides them
    via CSS wherever CSS applies (the real page; conformant popups like Apple
    Books). The eInk preview ignores CSS, so only there do they show."""

    def test_vn_item_rows_carry_text_separator(self):
        from scripts.build_edition import _badge_aside_inner_to_row

        row = _badge_aside_inner_to_row("<p>body text</p>", "comm")
        assert row.startswith('<div class="vn-item note-comm"><span class="vn-sep">\u2028• </span>'), row
        assert "body text" in row

    def test_cascade_heads_and_bylines_carry_text_separators(self):
        from scripts.build_edition import _emit_cascade_sections

        rows = [
            {
                "cat": "lang",
                "source_key": "strongs",
                "source_display": "Strong's Concordance",
                "suppress_byline": False,
                "row": '<div class="vn-item note-lang-hebrew">L1</div>',
            },
            {
                "cat": "topic",
                "source_key": "nave",
                "source_display": "Nave's Topical Bible",
                "suppress_byline": False,
                "row": '<div class="vn-item note-topic-nave">T1</div>',
            },
        ]
        out = _emit_cascade_sections(rows, {"lang": ("⌘", "Linguistic"), "topic": ("✦", "Topical")})
        # every category head leads with the ¶ separator; every byline with ◦
        assert out.count('<p class="vn-cat-head"><span class="vn-sep">\u2028¶ </span>') == 2, out
        assert out.count('<p class="vn-source-byline"><span class="vn-sep">\u2028◦ </span>') == 2, out

    def test_vn_sep_hidden_by_css_in_both_popup_styles(self):
        from scripts.build_edition import apply_note_popup_style

        for style in ("chip", "pills", "category-color"):
            css = apply_note_popup_style("", style)
            m = re.search(r"\.vn-sep\s*\{[^}]*display:\s*none", css)
            assert m, f"note_popup_style={style} does not hide .vn-sep"

    def test_flat_path_merged_asides_carry_item_separators(self, tmp_path):
        from scripts.build_edition import apply_badge_markers
        from scripts.core import config as _c

        book = _c.get_book("gen")
        epub = REPO / "epub_working"
        tmp = tmp_path / "build"
        tmp.mkdir()
        for f in book["files"]:
            (tmp / f).write_text((epub / f).read_text(encoding="utf-8"), encoding="utf-8")
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        fname = next(f for f in book["files"] if 'id="vnotes-gen-1-1-s1"' in (tmp / f).read_text(encoding="utf-8"))
        text = (tmp / fname).read_text(encoding="utf-8")
        m = re.search(r'<aside class="verse-notes" id="vnotes-gen-1-1-s1"[^>]*>(.*?)</aside>', text, re.DOTALL)
        assert m
        items = m.group(1).count('class="vn-item')
        seps = m.group(1).count('<span class="vn-sep">\u2028• </span>')
        # round-7 -s split: the s1 unit can hold a single item; the invariant is
        # one • separator per item (seps == items), which holds for items >= 1.
        assert items >= 1 and seps == items, f"every flat row needs its • separator ({seps}/{items})"


class TestVnotePreviewSeparators:
    """K-R4-1 (Kobo round 4): the vnote (translation) popup asides had NO
    plain-text separators — K-R3-2 covered only the merged study cascade — so
    the tag-stripped eInk Footnote preview ran header + verse + every
    source-label + translation together as one line. Same mechanism as
    K-R3-2: bake `.vn-sep` spans (¶ before the verse text, ◦ before each
    source label), hidden by CSS everywhere CSS applies."""

    VNOTE = (
        '<aside class="vnote" id="vnote-gen-1-1" epub:type="footnote">'
        "<p><strong>The First Book of Moses, Genesis 1:1.</strong></p>"
        '<p class="vnote-text">In the beginning God created the heaven and the earth.</p>\n'
        '  <p class="vnote-source-label">Hebrew (Masoretic / WLC)</p>\n'
        '  <p class="vnote-hebrew" dir="rtl" lang="he"><em>ב</em></p>\n'
        '  <p class="vnote-source-label">Greek (Septuagint / Swete)</p>\n'
        '  <p class="vnote-greek" lang="grc">ΕΝ</p>\n'
        '<p><a href="#v-gen-1-1" class="vnote-back" title="Back">↩</a></p></aside>'
    )

    def test_source_labels_get_byline_separator(self):
        from scripts.build_edition import add_vnote_preview_separators

        out = add_vnote_preview_separators(self.VNOTE)
        assert out.count('<p class="vnote-source-label"><span class="vn-sep">\u2028◦ </span>') == 2, out

    def test_vnote_text_gets_paragraph_separator(self):
        from scripts.build_edition import add_vnote_preview_separators

        out = add_vnote_preview_separators(self.VNOTE)
        assert '<p class="vnote-text"><span class="vn-sep">\u2028¶ </span>In the beginning' in out

    def test_idempotent(self):
        from scripts.build_edition import add_vnote_preview_separators

        once = add_vnote_preview_separators(self.VNOTE)
        assert add_vnote_preview_separators(once) == once

    def test_non_vnote_markup_untouched(self):
        from scripts.build_edition import add_vnote_preview_separators

        html = '<p class="vnote-text-x">x</p><p class="source-label">y</p>'
        assert add_vnote_preview_separators(html) == html

    def test_vnote_empty_placeholder_gains_separator(self):
        # round-7 5.3(a): the 346 base `vnote-text vnote-empty` placeholders
        # render in the eInk preview like any vnote (their translation rows
        # follow), so the block separator applies to them too — the old
        # exact-class regex skipped every multi-class paragraph.
        from scripts.build_edition import add_vnote_preview_separators

        html = '<p class="vnote-text vnote-empty"><em>[no text in this edition; verse marker only]</em></p>'
        out = add_vnote_preview_separators(html)
        assert '<p class="vnote-text vnote-empty"><span class="vn-sep">\u2028¶ </span><em>' in out
        assert add_vnote_preview_separators(out) == out  # idempotent on the new shape

    def test_leading_pilcrow_text_not_double_marked(self):
        # round-7 5.3(b): 2,970 recovered-base KJV popup verses already start
        # with their own ¶ — inserting the separator would preview as "¶ ¶".
        from scripts.build_edition import add_vnote_preview_separators

        html = '<p class="vnote-text">¶ And God said, Let there be light.</p>'
        assert add_vnote_preview_separators(html) == html

    def test_hide_css_rule_is_class_wide(self):
        # vnote asides are NOT inside .verse-notes — the K-R3-2 rule
        # `.verse-notes .vn-sep` never reached them. The rule must be the bare
        # `.vn-sep` selector (rule start, not descendant-scoped).
        from scripts import build_edition

        assert re.search(r"(?:^|[}\n])\s*\.vn-sep\s*\{[^}]*display:\s*none", build_edition._VN_SEP_HIDE_CSS), (
            build_edition._VN_SEP_HIDE_CSS
        )

    def test_real_base_vnote_aside_gains_separators(self, tmp_path):
        from scripts.build_edition import add_vnote_preview_separators

        src = (REPO / "epub_working" / "index_split_000.html").read_text(encoding="utf-8")
        m = re.search(r'<aside class="vnote" id="vnote-gen-1-1".*?</aside>', src, re.DOTALL)
        assert m, "vnote-gen-1-1 missing from the base fixture"
        out = add_vnote_preview_separators(m.group(0))
        labels = out.count('<p class="vnote-source-label">')
        seps = out.count('<p class="vnote-source-label"><span class="vn-sep">\u2028◦ </span>')
        assert labels > 0 and labels == seps, f"every source label needs its ◦ separator ({seps}/{labels})"


class TestEinkVnotePreviewBreaks:
    """K-R14: Kobo Footnote preview ignores U+2028 in koboSpan-wrapped `.vn-sep`
    spans — eink builds bake ``<br class="kobo-vnote-br" />`` before every
    ``<p class="vnote-…">`` so language blocks break in the tag-stripped dialog."""

    VNOTE = TestVnotePreviewSeparators.VNOTE

    def test_breaks_before_vnote_paragraphs(self):
        from scripts.build_edition import add_eink_vnote_preview_breaks

        out = add_eink_vnote_preview_breaks(self.VNOTE)
        assert out.count('<p class="vnote-kobo-sep">') == 5  # text + 2×(label+content)
        assert '<p class="vnote-kobo-sep">' in out and '<br class="kobo-vnote-br" /><p class="vnote-text">' in out
        assert '<br class="kobo-vnote-br" /><p class="vnote-source-label">' in out
        assert '<br class="kobo-vnote-br" /><p class="vnote-hebrew"' in out
        assert '<br class="kobo-vnote-br" /><p class="vnote-greek"' in out
        assert 'class="vnote-back"' in out
        assert '<br class="kobo-vnote-br" /><p><a href="#v-gen-1-1"' not in out

    def test_idempotent(self):
        from scripts.build_edition import add_eink_vnote_preview_breaks

        once = add_eink_vnote_preview_breaks(self.VNOTE)
        assert add_eink_vnote_preview_breaks(once) == once

    def test_apply_pass_eink_only(self, tmp_path):
        from scripts.build_edition import apply_vnote_preview_separators

        html = (
            "<html><body>"
            '<aside class="vnote" id="vnote-x-1-1">'
            "<p><strong>X 1:1.</strong></p>"
            '<p class="vnote-text">t</p>'
            '<p class="vnote-source-label">L</p>'
            "</aside></body></html>"
        )
        f = tmp_path / "index_split_000.html"
        f.write_text(html, encoding="utf-8")
        apply_vnote_preview_separators(tmp_path, {"target_reader": "eink"})
        eink = f.read_text(encoding="utf-8")
        assert "kobo-vnote-br" in eink

        f.write_text(html, encoding="utf-8")
        apply_vnote_preview_separators(tmp_path, {"target_reader": "kindle"})
        assert "kobo-vnote-br" not in f.read_text(encoding="utf-8")


class TestTabletPopupStripSeparators:
    """Apple M2 — Kobo preview separators must not leak as stray bullets."""

    SAMPLE = (
        '<aside class="vnote" id="vnote-gen-1-1">'
        '<p class="vnote-source-label"><span class="vn-sep">\u2028◦ </span>Hebrew (WLC)</p>'
        "</aside>"
        '<aside class="verse-notes" id="vnotes-gen-1-1-s1">'
        '<section class="vn-group note-cat-hist">'
        '<p class="vn-cat-head"><span class="vn-sep">\u2028¶ </span>Historical</p>'
        '<div class="vn-item note-dict-easton"><span class="vn-sep">\u2028• </span><p>Body</p></div>'
        "</section></aside>"
    )

    def test_tablet_strips_vn_sep_spans(self, tmp_path):
        from scripts.build_edition import apply_tablet_popup_strip_separators

        f = tmp_path / "index_split_000.html"
        f.write_text(self.SAMPLE, encoding="utf-8")
        n = apply_tablet_popup_strip_separators(tmp_path, {"target_reader": "tablet"})
        out = f.read_text(encoding="utf-8")
        assert n == 1
        assert "vn-sep" not in out
        assert "Hebrew (WLC)" in out and "Body" in out

    def test_eink_leaves_vn_sep_spans(self, tmp_path):
        from scripts.build_edition import apply_tablet_popup_strip_separators

        f = tmp_path / "index_split_000.html"
        f.write_text(self.SAMPLE, encoding="utf-8")
        assert apply_tablet_popup_strip_separators(tmp_path, {"target_reader": "eink"}) == 0
        assert "vn-sep" in f.read_text(encoding="utf-8")


class TestEmptyVerseProseRepair:
    """K-R15a: WEB/KJV versification gaps leave marker-only verse anchors."""

    SAMPLE = (
        '<p class="verse-p">dry. <a class="vn-link" id="v-gen-8-15" href="#vnote-gen-8-15" '
        'epub:type="noteref"><span class="vn">15</span></a>'
        '<a class="note-ref note-topic-nave" id="ref-g0815a" href="#note-g0815a" epub:type="noteref">'
        '<sup class="marker-num">1</sup></a> '
        '<a class="vn-link" id="v-gen-8-16" href="#vnote-gen-8-16" epub:type="noteref">'
        '<span class="vn">16</span></a> God spoke to Noah.</p>'
        '<aside class="vnote" id="vnote-gen-8-15" epub:type="footnote">'
        "<p><strong>Genesis 8:15.</strong></p>"
        '<p class="vnote-text">And God spake unto Noah, saying,</p></aside>'
    )

    def test_injects_vnote_text_when_region_empty(self):
        from scripts.build_edition import repair_empty_verse_prose

        out, n = repair_empty_verse_prose(self.SAMPLE)
        assert n == 1
        assert "And God spake unto Noah, saying," in out
        assert out.index("And God spake") < out.index("v-gen-8-16")

    def test_idempotent_when_prose_present(self):
        from scripts.build_edition import repair_empty_verse_prose

        html = (
            '<p class="verse-p"><a class="vn-link" id="v-gen-1-1" href="#vnote-gen-1-1">'
            '<span class="vn">1</span></a> In the beginning.</p>'
        )
        assert repair_empty_verse_prose(html) == (html, 0)

    def test_repair_after_study_badge_and_trail(self):
        from scripts.build_edition import repair_empty_verse_prose

        html = (
            'dry. <a class="vn-link" id="v-gen-8-15" href="#vnote-gen-8-15">'
            '<span class="vn">15</span></a>'
            '<a class="study-glossary-jump badge-cat-topic" href="#">'
            '<span class="marker-badge">*</span></a>'
            '<span class="badge-trail" aria-hidden="true">\xa0\u200b\xa0\u200b\xa0\u200b</span> '
            '<a class="vn-link" id="v-gen-8-16" href="#vnote-gen-8-16">'
            '<span class="vn">16</span></a> God spoke to Noah.</p>'
        )
        out, n = repair_empty_verse_prose(html)
        assert n == 1
        assert "spake unto Noah" in out
        assert out.index("spake unto Noah") < out.index("v-gen-8-16")

    def test_falls_back_to_translation_store(self, monkeypatch):
        from scripts.build_edition import repair_empty_verse_prose

        html = (
            '<p class="verse-p"><a class="vn-link" id="v-gen-8-15" href="#vnote-gen-8-15">'
            '<span class="vn">15</span></a> '
            '<a class="vn-link" id="v-gen-8-16" href="#vnote-gen-8-16">'
            '<span class="vn">16</span></a> Next verse.</p>'
        )

        def fake_get(tid, code, ch, v):
            return "And God spake unto Noah, saying," if (tid, code, ch, v) == ("web", "gen", 8, 15) else None

        monkeypatch.setattr("scripts.core.translations.get_verse", fake_get)
        out, n = repair_empty_verse_prose(html)
        assert n == 1 and "And God spake unto Noah" in out


# ----------------------------------------------------------------------
# Badge build — integration (real build_one, both modes)
# ----------------------------------------------------------------------


class TestBadgeBuildIntegration:
    EDITION = "ethiopian-tewahedo"

    def _build(self, tmp_path, monkeypatch, marker_style):
        import scripts.build_edition as be
        from scripts.core import build_cache

        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)

        eds = dict(config.editions_by_id())
        ed = dict(eds[self.EDITION])
        ed["marker_style"] = marker_style
        ed["reader_file_split"] = False  # keep this badge-focused build fast; splitting is tested in test_file_split
        eds[self.EDITION] = ed
        monkeypatch.setattr(config, "editions_by_id", lambda: eds)

        all_kinds = config.load_kinds()
        stats = be.build_one(self.EDITION, tmp_path, f"badge-test-{marker_style}", all_kinds, force=True)
        return Path(stats["output_path"])

    def _bodymatter_xhtml(self, epub):
        out = []
        with zipfile.ZipFile(epub) as zf:
            for n in zf.namelist():
                if "index_split_" in n and n.endswith(".html"):
                    out.append((n, zf.read(n).decode("utf-8")))
        return out

    def _all_ids_in_epub(self, epub):
        ids: set[str] = set()
        with zipfile.ZipFile(epub) as zf:
            for n in zf.namelist():
                if n.endswith(".html"):
                    ids.update(re.findall(r'\bid="([^"]+)"', zf.read(n).decode("utf-8")))
        return ids

    def test_badge_build_has_badges_no_per_note_markers(self, tmp_path, monkeypatch):
        epub = self._build(tmp_path, monkeypatch, "badge")
        files = self._bodymatter_xhtml(epub)
        all_ids = self._all_ids_in_epub(epub)
        assert files, "no bodymatter in the badge EPUB"
        any_badge = False
        # K-R9 backmatter: study footnotes live in index_split_900*, not prose files.
        prose_files = [(n, t) for n, t in files if "900" not in n]
        for name, text in prose_files:
            # (a) ZERO per-note markers remain in the bodymatter
            assert 'class="note-ref' not in text, f"{name}: per-note markers leaked in badge mode"
            assert 'class="note note-' not in text, f"{name}: per-note asides leaked in badge mode"
            if 'class="verse-notes-badge"' in text or 'class="study-glossary-jump' in text:
                any_badge = True
                # (c) every study badge resolves to a glossary footnote (may be cross-file)
                for vid in re.findall(r'href="#(vnotes-[a-z0-9-]+)"', text):
                    assert vid in all_ids, f"{name}: badge href #{vid} unresolved across EPUB"
        assert any_badge, "badge build produced no study badges at all"

    def test_numbers_build_unchanged_regression(self, tmp_path, monkeypatch):
        epub = self._build(tmp_path, monkeypatch, "numbers")
        files = self._bodymatter_xhtml(epub)
        # numbers mode keeps the historical per-note markers + asides; no badges.
        saw_marker = any('class="note-ref' in t for _, t in files)
        saw_badge = any('class="verse-notes-badge"' in t for _, t in files)
        assert saw_marker, "numbers mode lost its per-note markers"
        assert not saw_badge, "numbers mode must NOT emit verse badges"


class TestKoboTapGapCss:
    """device-QA 2026-06-09 (colour Kobo): at every verse boundary the trailing
    `◈ notes` badge and the NEXT verse's number popup are tap-adjacent, and the
    Kobo hit-box is coarse — mis-taps open the wrong popup. The user decision:
    KEEP both popups (translation = verse start, notes ◈ = verse end) and add a
    clear CSS gap. Base rules get a modest gap (every reader benefits — also
    fixes the number-glued-to-text "²The"); `#book-inner` (the kepubify wrapper
    div, present ONLY in the .kepub.epub) scopes a wider Kobo-only dead zone.
    Inert elsewhere: the plain EPUB has no #book-inner element."""

    def _css(self) -> str:
        return (REPO / "epub_working" / "stylesheet.css").read_text(encoding="utf-8")

    def _rule(self, css: str, selector: str) -> str:
        idx = css.find(selector + " {")
        assert idx != -1, f"stylesheet must have a `{selector}` rule"
        return css[idx : css.find("}", idx)]

    def test_badge_base_margin_separates_both_sides(self):
        rule = self._rule(self._css(), ".verse-notes-badge")
        assert "margin: 0 0.4em 0 0.12em" in rule, (
            f"the badge needs a real gap before the next verse's number (was `margin: 0 1px`); got: {rule}"
        )

    def test_tappable_verse_number_unglued_from_text(self):
        # "²The" — the wrapped verse number needs clear air before the verse text.
        rule = self._rule(self._css(), ".vn-link .vn")
        assert "margin-right: 0.25em" in rule, f"got: {rule}"

    def test_kepub_only_wider_gap(self):
        css = self._css()
        badge = self._rule(css, "#book-inner .verse-notes-badge")
        assert "margin: 0 0.7em 0 0.2em" in badge, f"got: {badge}"
        vn = self._rule(css, "#book-inner .vn-link .vn")
        assert "margin-right: 0.35em" in vn, f"got: {vn}"

    def test_numbers_mode_boundary_gap(self):
        # K① sibling (turn-57/58 review): marker_style=numbers (a live
        # /customize option) ships per-note .note-ref markers, and the verse's
        # LAST marker abuts the NEXT verse's number popup exactly like the
        # badge did. The fix gaps ONLY the marker→next-verse-number boundary
        # via an adjacency rule — a blanket .note-ref right-margin would
        # loosen mid-verse typography where markers sit inside the prose.
        css = self._css()
        base = self._rule(css, ".note-ref + .vn-link")
        assert "margin-left: 0.4em" in base, f"got: {base}"
        kepub = self._rule(css, "#book-inner .note-ref + .vn-link")
        assert "margin-left: 0.7em" in kepub, f"got: {kepub}"


class TestKoboChapterNumeralCss:
    """K-R2-4 (device-QA round 2, kobo7/9/13): chapter numerals rendered
    LEFT-aligned on Kobo although `.ch-heading` centers — Kobo's reader-side
    justification setting stomps <p> text-align with an injected !important
    rule. Centering the INNER `.section-heading` wrapper as a block dodges it:
    the override targets paragraphs, not nested blocks. Inert on conformant
    readers (a centered block inside an already-centered paragraph renders
    identically)."""

    def _css(self) -> str:
        return (REPO / "epub_working" / "stylesheet.css").read_text(encoding="utf-8")

    def test_numeral_centered_on_inner_block(self):
        css = self._css()
        idx = css.find(".ch-heading .section-heading {")
        assert idx != -1, "stylesheet must center the numeral's inner wrapper"
        rule = css[idx : css.find("}", idx)]
        assert "display: block" in rule, f"got: {rule}"
        assert "text-align: center" in rule, f"got: {rule}"


class TestSeparatorNewlines:
    def test_separator_spans_carry_leading_line_separator(self):
        """K-R5-7 (round 5b): the single-char marks (¶ ◦ •) gave the stripped
        eInk preview structure but no LINE BREAKS — bake a leading break char
        into each vn-sep span's text (CSS hides the span everywhere CSS
        applies; a raw-text extractor gains real line starts).
        K-R6-3 (round 6, on-device): the \\n variant COLLAPSED in the Kobo
        Footnote dialog → flipped to the designed fallback, U+2028 LINE
        SEPARATOR (a hard line break to Unicode-aware text extraction that
        HTML whitespace collapsing never eats)."""
        from scripts.build_edition import _VN_SEP_BYLINE, _VN_SEP_CAT, _VN_SEP_ITEM

        for sep in (_VN_SEP_ITEM, _VN_SEP_CAT, _VN_SEP_BYLINE):
            assert sep.startswith('<span class="vn-sep">\u2028'), repr(sep)
