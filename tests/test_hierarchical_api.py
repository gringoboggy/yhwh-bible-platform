"""ρ.3 Phase C1 — API write+read tests for the 6 per-coordinate
symbol/popup fields added to ``api_save_edition_meta`` +
``api_customize_data``.

Fields covered (all 6):
  note_families_on_per_book    {book: [tok]}        encode_per_book_tokens
  note_families_off_per_book   {book: [tok]}        encode_per_book_tokens
  note_families_on_per_chapter {"book:ch": [tok]}   encode_per_chapter_tokens
  note_families_off_per_chapter {"book:ch": [tok]}  encode_per_chapter_tokens
  popup_languages_per_chapter  {"book:ch": [lang]}  encode_per_chapter_languages
  popup_languages_per_verse    {"book:ch:vs": [lang]} encode_per_verse_languages

Isolation: same shutil.copy + config.load_editions.cache_clear() pattern
used by the existing edition-API tests (test_scripts.py + test_traditions_psi8.py).
Never mutates the real content/editions.yaml outside a try/finally guard.
"""

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestNoteSymbolFieldsPerBook:
    """note_families_on_per_book + note_families_off_per_book."""

    def setup_method(self):
        import scripts.web as web

        self.web = web

    # ------------------------------------------------------------------ accept

    def test_on_per_book_round_trip(self, tmp_path):
        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"note_families_on_per_book": {"gen": ["xref", "comm"]}},
            )
            assert r.get("ok"), r

            data = self.web.api_customize_data()
            cath = next(e for e in data["editions"] if e["id"] == "catholic-study")
            v = cath["note_families_on_per_book"]
            assert isinstance(v, dict)
            assert v.get("gen") == ["xref", "comm"]
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    def test_off_per_book_round_trip(self, tmp_path):
        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"note_families_off_per_book": {"gen": ["xref"]}},
            )
            assert r.get("ok"), r

            data = self.web.api_customize_data()
            cath = next(e for e in data["editions"] if e["id"] == "catholic-study")
            v = cath["note_families_off_per_book"]
            assert isinstance(v, dict)
            assert v.get("gen") == ["xref"]
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    def test_on_per_book_encodes_to_correct_on_disk_format(self, tmp_path):
        """Encoded list on disk must be ['gen=xref'] for {gen: [xref]}."""
        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"note_families_on_per_book": {"gen": ["xref"]}},
            )
            assert r.get("ok"), r

            config.load_editions.cache_clear()
            cath_raw = next(e for e in config.load_editions() if e["id"] == "catholic-study")
            encoded = cath_raw.get("note_families_on_per_book", [])
            assert "gen=xref" in encoded
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    def test_none_treated_as_empty_dict(self, tmp_path):
        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"note_families_on_per_book": None},
            )
            assert r.get("ok"), r
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    # ------------------------------------------------------------------ reject

    def test_rejects_non_dict(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"note_families_on_per_book": ["gen=xref"]},
        )
        assert "error" in r

    def test_rejects_unknown_book(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"note_families_on_per_book": {"NOT_A_BOOK": ["xref"]}},
        )
        assert "error" in r
        assert "NOT_A_BOOK" in r["error"]

    def test_rejects_unknown_token(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"note_families_on_per_book": {"gen": ["totally_fake_token_xyz"]}},
        )
        assert "error" in r
        assert "totally_fake_token_xyz" in r["error"]

    def test_off_per_book_rejects_unknown_token(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"note_families_off_per_book": {"gen": ["totally_fake_token_xyz"]}},
        )
        assert "error" in r

    def test_dedupes_tokens(self, tmp_path):
        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"note_families_on_per_book": {"gen": ["xref", "xref", "comm"]}},
            )
            assert r.get("ok"), r

            data = self.web.api_customize_data()
            cath = next(e for e in data["editions"] if e["id"] == "catholic-study")
            assert cath["note_families_on_per_book"]["gen"].count("xref") == 1
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    # ------------------------------------------------------------------ decode

    def test_customize_data_decodes_note_families_on_per_book_as_dict(self):
        d = self.web.api_customize_data()
        for e in d["editions"]:
            assert "note_families_on_per_book" in e
            v = e["note_families_on_per_book"]
            assert isinstance(v, dict), f"edition {e['id']}: expected dict, got {type(v)}"

    def test_customize_data_decodes_note_families_off_per_book_as_dict(self):
        d = self.web.api_customize_data()
        for e in d["editions"]:
            assert "note_families_off_per_book" in e
            v = e["note_families_off_per_book"]
            assert isinstance(v, dict)


class TestNoteSymbolFieldsPerChapter:
    """note_families_on_per_chapter + note_families_off_per_chapter."""

    def setup_method(self):
        import scripts.web as web

        self.web = web

    # ------------------------------------------------------------------ accept

    def test_on_per_chapter_round_trip(self, tmp_path):
        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"note_families_on_per_chapter": {"gen:1": ["xref-citation"]}},
            )
            assert r.get("ok"), r

            data = self.web.api_customize_data()
            cath = next(e for e in data["editions"] if e["id"] == "catholic-study")
            v = cath["note_families_on_per_chapter"]
            assert isinstance(v, dict)
            assert v.get("gen:1") == ["xref-citation"]
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    def test_off_per_chapter_round_trip(self, tmp_path):
        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"note_families_off_per_chapter": {"gen:1": ["comm"]}},
            )
            assert r.get("ok"), r

            data = self.web.api_customize_data()
            cath = next(e for e in data["editions"] if e["id"] == "catholic-study")
            v = cath["note_families_off_per_chapter"]
            assert isinstance(v, dict)
            assert v.get("gen:1") == ["comm"]
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    def test_on_per_chapter_encodes_to_correct_on_disk_format(self, tmp_path):
        """Encoded list on disk must be ['gen:1=xref-citation'] for {gen:1: [xref-citation]}."""
        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"note_families_on_per_chapter": {"gen:1": ["xref-citation"]}},
            )
            assert r.get("ok"), r

            config.load_editions.cache_clear()
            cath_raw = next(e for e in config.load_editions() if e["id"] == "catholic-study")
            encoded = cath_raw.get("note_families_on_per_chapter", [])
            assert "gen:1=xref-citation" in encoded
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    def test_none_treated_as_empty_dict(self, tmp_path):
        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"note_families_on_per_chapter": None},
            )
            assert r.get("ok"), r
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    # ------------------------------------------------------------------ reject

    def test_rejects_non_dict(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"note_families_on_per_chapter": ["gen:1=xref"]},
        )
        assert "error" in r

    def test_rejects_malformed_key_no_colon(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"note_families_on_per_chapter": {"gen": ["xref"]}},
        )
        assert "error" in r

    def test_rejects_malformed_key_too_many_parts(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"note_families_on_per_chapter": {"gen:1:1": ["xref"]}},
        )
        assert "error" in r

    def test_rejects_non_numeric_chapter(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"note_families_on_per_chapter": {"gen:abc": ["xref"]}},
        )
        assert "error" in r

    def test_rejects_zero_chapter(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"note_families_on_per_chapter": {"gen:0": ["xref"]}},
        )
        assert "error" in r

    def test_rejects_unknown_book(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"note_families_on_per_chapter": {"NOT_A_BOOK:1": ["xref"]}},
        )
        assert "error" in r
        assert "NOT_A_BOOK" in r["error"]

    def test_rejects_unknown_token(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"note_families_on_per_chapter": {"gen:1": ["totally_fake_xyz"]}},
        )
        assert "error" in r
        assert "totally_fake_xyz" in r["error"]

    def test_off_per_chapter_rejects_non_dict(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"note_families_off_per_chapter": "gen:1"},
        )
        assert "error" in r

    # ------------------------------------------------------------------ decode

    def test_customize_data_decodes_note_families_on_per_chapter_as_dict(self):
        d = self.web.api_customize_data()
        for e in d["editions"]:
            assert "note_families_on_per_chapter" in e
            assert isinstance(e["note_families_on_per_chapter"], dict)

    def test_customize_data_decodes_note_families_off_per_chapter_as_dict(self):
        d = self.web.api_customize_data()
        for e in d["editions"]:
            assert "note_families_off_per_chapter" in e
            assert isinstance(e["note_families_off_per_chapter"], dict)


class TestPopupLanguagesPerChapter:
    """popup_languages_per_chapter."""

    def setup_method(self):
        import scripts.web as web

        self.web = web

    # ------------------------------------------------------------------ accept

    def test_per_chapter_round_trip(self, tmp_path):
        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"popup_languages_per_chapter": {"gen:1": ["wlc", "hebrew"]}},
            )
            assert r.get("ok"), r

            data = self.web.api_customize_data()
            cath = next(e for e in data["editions"] if e["id"] == "catholic-study")
            v = cath["popup_languages_per_chapter"]
            assert isinstance(v, dict)
            assert v.get("gen:1") == ["wlc", "hebrew"]
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    def test_per_chapter_encodes_to_correct_on_disk_format(self, tmp_path):
        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"popup_languages_per_chapter": {"gen:1": ["wlc"]}},
            )
            assert r.get("ok"), r

            config.load_editions.cache_clear()
            cath_raw = next(e for e in config.load_editions() if e["id"] == "catholic-study")
            encoded = cath_raw.get("popup_languages_per_chapter", [])
            assert "gen:1=wlc" in encoded
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    def test_none_treated_as_empty_dict(self, tmp_path):
        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"popup_languages_per_chapter": None},
            )
            assert r.get("ok"), r
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    # ------------------------------------------------------------------ reject

    def test_rejects_non_dict(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"popup_languages_per_chapter": ["gen:1=wlc"]},
        )
        assert "error" in r

    def test_rejects_malformed_key_no_colon(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"popup_languages_per_chapter": {"gen": ["wlc"]}},
        )
        assert "error" in r

    def test_rejects_malformed_key_too_many_parts(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"popup_languages_per_chapter": {"gen:1:1": ["wlc"]}},
        )
        assert "error" in r

    def test_rejects_non_numeric_chapter(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"popup_languages_per_chapter": {"gen:abc": ["wlc"]}},
        )
        assert "error" in r

    def test_rejects_zero_chapter(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"popup_languages_per_chapter": {"gen:0": ["wlc"]}},
        )
        assert "error" in r

    def test_rejects_unknown_book(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"popup_languages_per_chapter": {"NOT_A_BOOK:1": ["wlc"]}},
        )
        assert "error" in r
        assert "NOT_A_BOOK" in r["error"]

    def test_rejects_unknown_language(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"popup_languages_per_chapter": {"gen:1": ["klingon"]}},
        )
        assert "error" in r
        assert "klingon" in r["error"]

    # ------------------------------------------------------------------ decode

    def test_customize_data_decodes_popup_languages_per_chapter_as_dict(self):
        d = self.web.api_customize_data()
        for e in d["editions"]:
            assert "popup_languages_per_chapter" in e
            v = e["popup_languages_per_chapter"]
            assert isinstance(v, dict)


class TestPopupLanguagesPerVerse:
    """popup_languages_per_verse."""

    def setup_method(self):
        import scripts.web as web

        self.web = web

    # ------------------------------------------------------------------ accept

    def test_per_verse_round_trip(self, tmp_path):
        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"popup_languages_per_verse": {"gen:1:1": ["wlc"]}},
            )
            assert r.get("ok"), r

            data = self.web.api_customize_data()
            cath = next(e for e in data["editions"] if e["id"] == "catholic-study")
            v = cath["popup_languages_per_verse"]
            assert isinstance(v, dict)
            assert v.get("gen:1:1") == ["wlc"]
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    def test_per_verse_encodes_to_correct_on_disk_format(self, tmp_path):
        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"popup_languages_per_verse": {"gen:1:1": ["wlc"]}},
            )
            assert r.get("ok"), r

            config.load_editions.cache_clear()
            cath_raw = next(e for e in config.load_editions() if e["id"] == "catholic-study")
            encoded = cath_raw.get("popup_languages_per_verse", [])
            assert "gen:1:1=wlc" in encoded
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    def test_none_treated_as_empty_dict(self, tmp_path):
        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"popup_languages_per_verse": None},
            )
            assert r.get("ok"), r
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    def test_dedupes_languages(self, tmp_path):
        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"popup_languages_per_verse": {"gen:1:1": ["wlc", "wlc", "hebrew"]}},
            )
            assert r.get("ok"), r

            data = self.web.api_customize_data()
            cath = next(e for e in data["editions"] if e["id"] == "catholic-study")
            v = cath["popup_languages_per_verse"]
            assert v["gen:1:1"].count("wlc") == 1
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    # ------------------------------------------------------------------ reject

    def test_rejects_non_dict(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"popup_languages_per_verse": ["gen:1:1=wlc"]},
        )
        assert "error" in r

    def test_rejects_malformed_key_only_one_part(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"popup_languages_per_verse": {"gen": ["wlc"]}},
        )
        assert "error" in r

    def test_rejects_malformed_key_only_two_parts(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"popup_languages_per_verse": {"gen:1": ["wlc"]}},
        )
        assert "error" in r

    def test_rejects_malformed_key_four_parts(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"popup_languages_per_verse": {"gen:1:1:extra": ["wlc"]}},
        )
        assert "error" in r

    def test_rejects_non_numeric_chapter(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"popup_languages_per_verse": {"gen:abc:1": ["wlc"]}},
        )
        assert "error" in r

    def test_rejects_non_numeric_verse(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"popup_languages_per_verse": {"gen:1:abc": ["wlc"]}},
        )
        assert "error" in r

    def test_rejects_zero_verse(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"popup_languages_per_verse": {"gen:1:0": ["wlc"]}},
        )
        assert "error" in r

    def test_rejects_unknown_book(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"popup_languages_per_verse": {"NOT_A_BOOK:1:1": ["wlc"]}},
        )
        assert "error" in r
        assert "NOT_A_BOOK" in r["error"]

    def test_rejects_unknown_language(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"popup_languages_per_verse": {"gen:1:1": ["klingon"]}},
        )
        assert "error" in r
        assert "klingon" in r["error"]

    # ------------------------------------------------------------------ decode

    def test_customize_data_decodes_popup_languages_per_verse_as_dict(self):
        d = self.web.api_customize_data()
        for e in d["editions"]:
            assert "popup_languages_per_verse" in e
            v = e["popup_languages_per_verse"]
            assert isinstance(v, dict)


class TestPreviewIncludesNewFields:
    """api_preview_edition_changes must accept the 6 new fields in EDITABLE."""

    def setup_method(self):
        import scripts.web as web

        self.web = web

    def test_preview_accepts_note_families_on_per_book(self):
        r = self.web.api_preview_edition_changes(
            "catholic-study",
            {"note_families_on_per_book": {"gen": ["xref"]}},
        )
        assert "unknown_fields" not in r or "note_families_on_per_book" not in r.get("unknown_fields", [])

    def test_preview_accepts_note_families_off_per_book(self):
        r = self.web.api_preview_edition_changes(
            "catholic-study",
            {"note_families_off_per_book": {"gen": ["xref"]}},
        )
        assert "unknown_fields" not in r or "note_families_off_per_book" not in r.get("unknown_fields", [])

    def test_preview_accepts_note_families_on_per_chapter(self):
        r = self.web.api_preview_edition_changes(
            "catholic-study",
            {"note_families_on_per_chapter": {"gen:1": ["xref"]}},
        )
        assert "unknown_fields" not in r or "note_families_on_per_chapter" not in r.get("unknown_fields", [])

    def test_preview_accepts_note_families_off_per_chapter(self):
        r = self.web.api_preview_edition_changes(
            "catholic-study",
            {"note_families_off_per_chapter": {"gen:1": ["xref"]}},
        )
        assert "unknown_fields" not in r or "note_families_off_per_chapter" not in r.get("unknown_fields", [])

    def test_preview_accepts_popup_languages_per_chapter(self):
        r = self.web.api_preview_edition_changes(
            "catholic-study",
            {"popup_languages_per_chapter": {"gen:1": ["wlc"]}},
        )
        assert "unknown_fields" not in r or "popup_languages_per_chapter" not in r.get("unknown_fields", [])

    def test_preview_accepts_popup_languages_per_verse(self):
        r = self.web.api_preview_edition_changes(
            "catholic-study",
            {"popup_languages_per_verse": {"gen:1:1": ["wlc"]}},
        )
        assert "unknown_fields" not in r or "popup_languages_per_verse" not in r.get("unknown_fields", [])
