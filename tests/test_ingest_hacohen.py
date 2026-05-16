"""τ.6.x.5 — HaCohen external Ge'ez source ingest tests."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
HACOHEN = REPO / "content" / "translations" / "sources" / "hacohen-geez"


class TestProvenanceRecord:
    def test_source_yaml_present_and_well_formed(self):
        cfg = yaml.safe_load((HACOHEN / "_source.yaml").read_text(encoding="utf-8"))
        assert cfg["source_id"] == "hacohen-geez"
        assert cfg["site_url"] == "https://www.tau.ac.il/~hacohen/"
        psalms = cfg["books"]["psalms"]
        assert psalms["editor"] == "Hiob Ludolf"
        assert psalms["edition_year"] == 1701
        assert psalms["pd_basis"]
        assert psalms["verse_numbering"] == "Rahlfs-LXX"
        assert psalms["url_pattern"] == "Psalm/PsalmNrR%20{n}.html"
        assert psalms["chapter_range"] == [1, 151]

    def test_cache_dir_gitignored(self):
        gi = (HACOHEN / ".gitignore").read_text(encoding="utf-8")
        assert "cache/" in gi


class TestWriteBookModuleParametrized:
    def _fn(self):
        from scripts.extract_parallel_pdf import write_book_module

        return write_book_module

    def test_defaults_byte_identical(self, tmp_path, monkeypatch):
        # Existing callers pass no provenance kwargs → output must be
        # byte-identical to pre-change (parallel-bible-eotc strings).
        import scripts.extract_parallel_pdf as ep

        monkeypatch.setattr(ep, "TRANSLATIONS_DIR", tmp_path)
        out = self._fn()("geez-tewahedo", "zzz", [(1, 1, "ብፁዕ")], "ocr-tier3", "2026-05-16")
        txt = out.read_text(encoding="utf-8")
        assert "SOURCE_PROVENANCE = 'parallel-bible-eotc'" in txt
        assert "content/translations/sources/parallel-bible-eotc/_source.yaml" in txt
        assert "Tool: scripts/extract_parallel_pdf.py" in txt

    def test_kwargs_override_three_spots(self, tmp_path, monkeypatch):
        import scripts.extract_parallel_pdf as ep

        monkeypatch.setattr(ep, "TRANSLATIONS_DIR", tmp_path)
        out = self._fn()(
            "geez-tewahedo",
            "psa",
            [(1, 1, "ብፁዕ")],
            "digitized-critical-edition",
            "2026-05-16",
            ingest_phase="τ.6.x.2.i",
            source_provenance="hacohen-geez",
            source_yaml_ref="content/translations/sources/hacohen-geez/_source.yaml",
            tool="scripts/ingest_hacohen.py",
        )
        txt = out.read_text(encoding="utf-8")
        assert "SOURCE_PROVENANCE = 'hacohen-geez'" in txt
        assert "content/translations/sources/hacohen-geez/_source.yaml" in txt
        assert "Tool: scripts/ingest_hacohen.py" in txt
        assert "SOURCE_QUALITY = 'digitized-critical-edition'" in txt
        assert "parallel-bible-eotc" not in txt


FIX = REPO / "tests" / "fixtures" / "hacohen"


class TestParseHacohenPsalter:
    def _fn(self):
        from scripts.ingest_hacohen import parse_hacohen_psalter

        return parse_hacohen_psalter

    def test_parses_verses_with_correct_numbering(self):
        html_text = (FIX / "psalm1.html").read_text(encoding="utf-8")
        verses = self._fn()(html_text, 1)
        assert [(c, v) for c, v, _ in verses] == [(1, 1), (1, 2)]

    def test_verse1_is_blessed_is_the_man_unicode_geez(self):
        verses = self._fn()((FIX / "psalm1.html").read_text(encoding="utf-8"), 1)
        ch, v, text = verses[0]
        assert text.startswith("ብፁዕ ፡ ብእሲ"), repr(text[:40])
        assert "መንበረ" in text
        assert "&#" not in text
        assert "<" not in text

    def test_title_and_caption_and_toggle_skipped(self):
        verses = self._fn()((FIX / "psalm1.html").read_text(encoding="utf-8"), 1)
        joined = " ".join(t for _, _, t in verses)
        assert "Nr. Vers" not in joined
        assert "Cap." not in joined
        assert len(verses) == 2
