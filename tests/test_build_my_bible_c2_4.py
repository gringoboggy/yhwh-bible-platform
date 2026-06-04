"""ρ.3 Phase C2-4 — API round-trip tests for the /build-my-bible interactive
symbol tri-state + popup checklist controls.

These exercise the SAME contract the C2-4 UI relies on: the navigator
computes a decoded ``{field: {key: [values]}}`` payload (the full current map
for each touched field — the endpoint is absolute-replace per field), PUTs it
to ``api_save_edition_meta``, then re-reads via ``api_build_my_bible`` and
expects the resolved state to change at the right coordinate and be unchanged
elsewhere. Also covers bulk-clears-finer (a book-level flip drops the chapter
key the UI sends in the same payload) and the C2-4 read-API addition
(``popup_languages_per_book`` now present in ``overrides``).

Isolation: shutil.copy backup + try/finally restore of content/editions.yaml
+ config.load_editions.cache_clear() — the same pattern test_hierarchical_api.py
uses. A real shipping edition (``catholic-study``) is mutated only inside the
guard and always restored.
"""

from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EDITIONS_YAML = REPO_ROOT / "content" / "editions.yaml"
EDITION = "catholic-study"


def _clear_cache():
    from scripts.core import config

    config.load_editions.cache_clear()
    from scripts.core import matrix as matrix_mod

    matrix_mod.compute_matrix.cache_clear()


class _IsolatedEdition:
    """Backup + restore content/editions.yaml around a mutation block."""

    def __init__(self, tmp_path):
        self.backup = tmp_path / "editions.preserve.yaml"

    def __enter__(self):
        shutil.copy(EDITIONS_YAML, self.backup)
        _clear_cache()
        import scripts.web as web

        return web

    def __exit__(self, *exc):
        shutil.copy(self.backup, EDITIONS_YAML)
        _clear_cache()
        return False


def _chapter_symbol(edition, book, ch, token):
    from scripts.web_editions import api_build_my_bible

    r = api_build_my_bible(edition, book=book)
    entry = next(c for c in r["chapters"] if c["num"] == ch)
    return entry["resolved"]["symbols"].get(token)


def _chapter_popups(edition, book, ch):
    from scripts.web_editions import api_build_my_bible

    r = api_build_my_bible(edition, book=book)
    entry = next(c for c in r["chapters"] if c["num"] == ch)
    return set(entry["resolved"]["popups"])


def _verse_popups(edition, book, ch, vs):
    from scripts.web_editions import api_build_my_bible

    r = api_build_my_bible(edition, book=book, chapter=ch)
    entry = next(v for v in r["verses"] if v["vs"] == vs)
    return set(entry["resolved"]["popups"])


# ---------------------------------------------------------------------------
# Read-API addition: popup_languages_per_book in overrides
# ---------------------------------------------------------------------------


class TestOverridesIncludesPerBookPopups:
    def test_overrides_has_popup_languages_per_book(self):
        from scripts.web_editions import api_build_my_bible

        r = api_build_my_bible(EDITION)
        assert "popup_languages_per_book" in r["overrides"]
        assert isinstance(r["overrides"]["popup_languages_per_book"], dict)

    def test_per_book_popups_round_trip_visible_in_overrides(self, tmp_path):
        with _IsolatedEdition(tmp_path) as web:
            from scripts.web_editions import api_build_my_bible

            res = web.api_save_edition_meta(
                EDITION,
                {"popup_languages_per_book": {"gen": ["wlc"]}},
            )
            assert res.get("ok"), res
            _clear_cache()
            ov = api_build_my_bible(EDITION)["overrides"]
            assert ov["popup_languages_per_book"].get("gen") == ["wlc"]


# ---------------------------------------------------------------------------
# Symbol tri-state — book level
# ---------------------------------------------------------------------------


class TestSymbolBookLevel:
    def test_off_per_book_flips_resolved_off_for_that_book_only(self, tmp_path):
        """UI payload: full note_families_off_per_book map with one delta.
        gen resolves OFF for xref; exo (untouched) stays ON."""
        # Baseline: xref ON everywhere for catholic-study.
        assert _chapter_symbol(EDITION, "gen", 1, "xref") == "on"
        assert _chapter_symbol(EDITION, "exo", 1, "xref") == "on"

        with _IsolatedEdition(tmp_path) as web:
            res = web.api_save_edition_meta(
                EDITION,
                {"note_families_off_per_book": {"gen": ["xref"]}},
            )
            assert res.get("ok"), res
            _clear_cache()
            assert _chapter_symbol(EDITION, "gen", 1, "xref") == "off"
            assert _chapter_symbol(EDITION, "exo", 1, "xref") == "on"

    def test_on_per_book_force_on_for_off_category(self, tmp_path):
        """A category OFF at the edition default → ON at one book via the
        on-map. 'dev' is OFF for catholic-study by default."""
        assert _chapter_symbol(EDITION, "gen", 1, "dev") == "off"
        with _IsolatedEdition(tmp_path) as web:
            res = web.api_save_edition_meta(
                EDITION,
                {"note_families_on_per_book": {"gen": ["dev"]}},
            )
            assert res.get("ok"), res
            _clear_cache()
            assert _chapter_symbol(EDITION, "gen", 1, "dev") == "on"
            # untouched book unchanged
            assert _chapter_symbol(EDITION, "exo", 1, "dev") == "off"

    def test_absolute_replace_preserves_other_book_keys(self, tmp_path):
        """Sending the FULL map (gen + exo off) then a second save that drops
        exo from the sent map removes exo's override (absolute-replace)."""
        with _IsolatedEdition(tmp_path) as web:
            r1 = web.api_save_edition_meta(
                EDITION,
                {"note_families_off_per_book": {"gen": ["xref"], "exo": ["xref"]}},
            )
            assert r1.get("ok"), r1
            _clear_cache()
            assert _chapter_symbol(EDITION, "gen", 1, "xref") == "off"
            assert _chapter_symbol(EDITION, "exo", 1, "xref") == "off"

            # The UI now removes exo's override → it sends the full map WITHOUT
            # exo (just gen). Absolute-replace drops exo.
            r2 = web.api_save_edition_meta(
                EDITION,
                {"note_families_off_per_book": {"gen": ["xref"]}},
            )
            assert r2.get("ok"), r2
            _clear_cache()
            assert _chapter_symbol(EDITION, "gen", 1, "xref") == "off"
            assert _chapter_symbol(EDITION, "exo", 1, "xref") == "on"


# ---------------------------------------------------------------------------
# Symbol tri-state — chapter level
# ---------------------------------------------------------------------------


class TestSymbolChapterLevel:
    def test_off_per_chapter_flips_resolved_off_for_that_chapter_only(self, tmp_path):
        assert _chapter_symbol(EDITION, "gen", 1, "xref") == "on"
        assert _chapter_symbol(EDITION, "gen", 2, "xref") == "on"
        with _IsolatedEdition(tmp_path) as web:
            res = web.api_save_edition_meta(
                EDITION,
                {"note_families_off_per_chapter": {"gen:1": ["xref"]}},
            )
            assert res.get("ok"), res
            _clear_cache()
            assert _chapter_symbol(EDITION, "gen", 1, "xref") == "off"
            assert _chapter_symbol(EDITION, "gen", 2, "xref") == "on"

    def test_chapter_kind_token_overrides_one_kind(self, tmp_path):
        """A kind-code token at chapter level (drill-down) is accepted +
        round-trips into the per-chapter map."""
        with _IsolatedEdition(tmp_path) as web:
            res = web.api_save_edition_meta(
                EDITION,
                {"note_families_off_per_chapter": {"gen:1": ["lang-hebrew"]}},
            )
            assert res.get("ok"), res
            _clear_cache()
            from scripts.web_editions import api_build_my_bible

            ov = api_build_my_bible(EDITION)["overrides"]
            assert ov["note_families_off_per_chapter"].get("gen:1") == ["lang-hebrew"]


# ---------------------------------------------------------------------------
# Bulk-clears-finer (§3.2) — the UI strips finer keys before sending
# ---------------------------------------------------------------------------


class TestBulkClearsFiner:
    def test_book_flip_drops_chapter_key_in_same_payload(self, tmp_path):
        """Simulate the UI: a chapter override exists, then the builder flips
        the SAME family at book level. The UI clears the finer chapter key
        and sends BOTH updated maps in one payload. After save, the chapter
        key is gone and the book override resolves."""
        with _IsolatedEdition(tmp_path) as web:
            from scripts.web_editions import api_build_my_bible

            # Pre-existing chapter exception.
            r1 = web.api_save_edition_meta(
                EDITION,
                {"note_families_on_per_chapter": {"gen:1": ["xref"]}},
            )
            assert r1.get("ok"), r1
            _clear_cache()
            ov = api_build_my_bible(EDITION)["overrides"]
            assert ov["note_families_on_per_chapter"].get("gen:1") == ["xref"]

            # Builder flips xref OFF at book level. The UI's bulk-clears-finer
            # removes gen:1 from note_families_on_per_chapter and sends the
            # full (now-empty) per-chapter map alongside the per-book off map.
            r2 = web.api_save_edition_meta(
                EDITION,
                {
                    "note_families_off_per_book": {"gen": ["xref"]},
                    "note_families_on_per_chapter": {},  # cleared finer
                },
            )
            assert r2.get("ok"), r2
            _clear_cache()
            ov2 = api_build_my_bible(EDITION)["overrides"]
            assert "gen:1" not in ov2["note_families_on_per_chapter"]
            assert ov2["note_families_off_per_book"].get("gen") == ["xref"]
            # Resolution: book OFF now wins; gen ch1 is OFF (the stale chapter
            # ON exception is gone).
            assert _chapter_symbol(EDITION, "gen", 1, "xref") == "off"

    def test_book_popup_flip_drops_chapter_and_verse_keys(self, tmp_path):
        """A book-level popup set clears finer popup keys (chapter + verse)
        within that book — the UI sends the cleared maps in the same payload."""
        with _IsolatedEdition(tmp_path) as web:
            from scripts.web_editions import api_build_my_bible

            r1 = web.api_save_edition_meta(
                EDITION,
                {
                    "popup_languages_per_chapter": {"gen:1": ["wlc"]},
                    "popup_languages_per_verse": {"gen:1:1": ["wlc"]},
                },
            )
            assert r1.get("ok"), r1
            _clear_cache()

            # Book-level popup set → UI clears finer maps for gen.
            r2 = web.api_save_edition_meta(
                EDITION,
                {
                    "popup_languages_per_book": {"gen": ["lxx-greek"]},
                    "popup_languages_per_chapter": {},
                    "popup_languages_per_verse": {},
                },
            )
            assert r2.get("ok"), r2
            _clear_cache()
            ov = api_build_my_bible(EDITION)["overrides"]
            assert ov["popup_languages_per_book"].get("gen") == ["lxx-greek"]
            assert "gen:1" not in ov["popup_languages_per_chapter"]
            assert "gen:1:1" not in ov["popup_languages_per_verse"]


# ---------------------------------------------------------------------------
# Popup checklist — chapter + verse levels
# ---------------------------------------------------------------------------


class TestPopupChapterAndVerse:
    def test_chapter_popup_set_wins_for_that_chapter(self, tmp_path):
        with _IsolatedEdition(tmp_path) as web:
            res = web.api_save_edition_meta(
                EDITION,
                {"popup_languages_per_chapter": {"gen:1": ["wlc"]}},
            )
            assert res.get("ok"), res
            _clear_cache()
            assert _chapter_popups(EDITION, "gen", 1) == {"wlc"}

    def test_verse_popup_set_wins_for_that_verse(self, tmp_path):
        with _IsolatedEdition(tmp_path) as web:
            res = web.api_save_edition_meta(
                EDITION,
                {"popup_languages_per_verse": {"gen:1:1": ["wlc", "lxx-greek"]}},
            )
            assert res.get("ok"), res
            _clear_cache()
            assert _verse_popups(EDITION, "gen", 1, 1) == {"wlc", "lxx-greek"}

    def test_verse_revert_to_inherit_removes_key(self, tmp_path):
        """The UI's '↻ inherit' sends the full per-verse map WITHOUT that key
        (absolute-replace) → the key is removed and the verse inherits."""
        with _IsolatedEdition(tmp_path) as web:
            from scripts.web_editions import api_build_my_bible

            r1 = web.api_save_edition_meta(
                EDITION,
                {"popup_languages_per_verse": {"gen:1:1": ["wlc"]}},
            )
            assert r1.get("ok"), r1
            _clear_cache()
            assert "gen:1:1" in api_build_my_bible(EDITION)["overrides"]["popup_languages_per_verse"]

            # Revert: send the map without gen:1:1 (here, empty).
            r2 = web.api_save_edition_meta(
                EDITION,
                {"popup_languages_per_verse": {}},
            )
            assert r2.get("ok"), r2
            _clear_cache()
            assert "gen:1:1" not in api_build_my_bible(EDITION)["overrides"]["popup_languages_per_verse"]
