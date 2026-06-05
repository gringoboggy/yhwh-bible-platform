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
        v1_badges = re.findall(r'id="vbadge-gen-1-\d+"', text)
        assert len(v1_badges) == 31, f"expected 31 gen-1 verse badges, got {len(v1_badges)}"
        # The badge count is BY POSITION (the task's rule): a verse-end-fallback
        # marker counts for the verse it physically renders in, not the verse its
        # id encodes. Gen 1:1's region holds 15 markers (2 Hebrew word-notes whose
        # KJV-anchor word isn't in the WEB text fell back into 1:2's region).
        m = re.search(r'<a class="verse-notes-badge" id="vbadge-gen-1-1"[^>]*title="(\d+) notes?"', text)
        assert m and m.group(1) == "15", f"gen 1:1 badge count wrong: {m.group(1) if m else None}"
        # The total notes collapsed across the chapter is conserved (= the base's
        # per-note marker count for gen 1): nothing is dropped, only regrouped.
        total = sum(int(x) for x in re.findall(r'id="vbadge-gen-1-\d+"[^>]*title="(\d+) notes?"', text))
        assert total == 225, f"gen 1 badge counts must sum to the 225 base markers, got {total}"

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
        merged = re.findall(r'<aside class="verse-notes" id="vnotes-gen-1-(\d+)" epub:type="footnote">', text)
        assert len(merged) == 31, f"expected 31 merged gen-1 asides, got {len(merged)}"
        # (d) every badge href resolves to its vnotes aside id
        for vv in re.findall(r'href="#vnotes-gen-1-(\d+)"', text):
            assert f'id="vnotes-gen-1-{vv}"' in text, f"badge href #vnotes-gen-1-{vv} has no aside"
        # the merged aside for v1 lists one .vn-item per note IN that verse's
        # region (15, matching the badge count — see the position-grouping note).
        m = re.search(
            r'<aside class="verse-notes" id="vnotes-gen-1-1"[^>]*>(.*?)</aside>',
            text,
            re.DOTALL,
        )
        assert m
        assert m.group(1).count('class="vn-item') == 15

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
        fname = next(f for f in book["files"] if 'id="vbadge-gen-1-1"' in (tmp / f).read_text(encoding="utf-8"))
        once = (tmp / fname).read_text(encoding="utf-8")
        # no nested <a> introduced by the badge (the badge is itself an <a>)
        assert find_nested_anchors(once) == [], "badge introduced a nested <a> (RSC-005)"
        # second pass is a no-op (idempotent / deterministic)
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        twice = (tmp / fname).read_text(encoding="utf-8")
        assert twice == once, "apply_badge_markers is not idempotent"


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

    def test_badge_build_has_badges_no_per_note_markers(self, tmp_path, monkeypatch):
        epub = self._build(tmp_path, monkeypatch, "badge")
        files = self._bodymatter_xhtml(epub)
        assert files, "no bodymatter in the badge EPUB"
        any_badge = False
        for name, text in files:
            # (a) ZERO per-note markers remain in the bodymatter
            assert 'class="note-ref' not in text, f"{name}: per-note markers leaked in badge mode"
            assert 'class="note note-' not in text, f"{name}: per-note asides leaked in badge mode"
            if 'class="verse-notes-badge"' in text:
                any_badge = True
                # (c) every badge resolves to its merged aside
                for vid in re.findall(r'href="#(vnotes-[a-z0-9-]+)"', text):
                    assert f'id="{vid}"' in text, f"{name}: badge href #{vid} unresolved"
        assert any_badge, "badge build produced no verse-notes badges at all"

    def test_numbers_build_unchanged_regression(self, tmp_path, monkeypatch):
        epub = self._build(tmp_path, monkeypatch, "numbers")
        files = self._bodymatter_xhtml(epub)
        # numbers mode keeps the historical per-note markers + asides; no badges.
        saw_marker = any('class="note-ref' in t for _, t in files)
        saw_badge = any('class="verse-notes-badge"' in t for _, t in files)
        assert saw_marker, "numbers mode lost its per-note markers"
        assert not saw_badge, "numbers mode must NOT emit verse badges"
