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

    def test_defaults_preserve_data_and_provenance(self, tmp_path, monkeypatch):
        # Honest contract (AUDIT_2026-05-16-DEEP-5 correction — the
        # earlier "byte-identical" framing was an over-claim): default
        # callers keep the SAME data + provenance — SOURCE_PROVENANCE,
        # the source-yaml ref, and the Tool line all stay
        # parallel-bible-eotc. This is DATA-preservation, NOT byte
        # identity: the generic provenance docstring opening line was
        # intentionally generalized. Existing committed book modules
        # are static and unaffected (write_book_module only runs on
        # (re-)ingest), so no shipped artifact changes.
        import scripts.extract_parallel_pdf as ep

        monkeypatch.setattr(ep, "TRANSLATIONS_DIR", tmp_path)
        out = self._fn()("geez-tewahedo", "zzz", [(1, 1, "ብፁዕ")], "ocr-tier3", "2026-05-16")
        txt = out.read_text(encoding="utf-8")
        # data + provenance preserved for default callers:
        assert "SOURCE_PROVENANCE = 'parallel-bible-eotc'" in txt
        assert "content/translations/sources/parallel-bible-eotc/_source.yaml" in txt
        assert "Tool: scripts/extract_parallel_pdf.py" in txt
        # the ONE intentional generalization (so this is NOT byte-identical):
        assert "Extracted/ingested from source (" in txt
        assert "Extracted from the parallel-Bible EOTC PDF (" not in txt

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

    def test_verse1_structure_and_unicode_decode(self):
        # Pins STRUCTURE + encoding behavior (verse-1 incipit, colon-
        # cola merge, NCR→Unicode-Ge'ez decode, tag-strip), NOT content
        # fidelity — the committed fixture is a tiny hand-trim per
        # spec §8 (renamed at AUDIT_2026-05-16-DEEP-5; the old name
        # over-stated content coverage).
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


class TestFetcherCache:
    def _mod(self):
        import scripts.ingest_hacohen as ih

        return ih

    def test_cache_hit_skips_network(self, tmp_path, monkeypatch):
        ih = self._mod()
        cache = tmp_path / "PsalmNrR 7.html"
        cache.write_text(
            "<p><span style='font-size:70%'>1</span> &#4632; &#4962;</p>",
            encoding="utf-8",
        )

        def _boom(*a, **k):
            raise AssertionError("network must not be called on cache hit")

        monkeypatch.setattr(ih, "_http_get", _boom)
        out = ih.fetch_psalm(7, cache_dir=tmp_path)
        assert out == cache
        assert "&#4632;" in cache.read_text(encoding="utf-8")

    def test_fetch_writes_cache_then_reuses(self, tmp_path, monkeypatch):
        ih = self._mod()
        calls = []

        def _fake_get(url):
            calls.append(url)
            return "<p><span style='font-size:70%'>1</span> &#4632; &#4962;</p>"

        monkeypatch.setattr(ih, "_http_get", _fake_get)
        p1 = ih.fetch_psalm(3, cache_dir=tmp_path)
        p2 = ih.fetch_psalm(3, cache_dir=tmp_path)
        assert p1 == p2 and p1.exists()
        assert len(calls) == 1  # second call served from cache
        assert "PsalmNrR%203.html" in calls[0]

    def test_fetch_error_no_partial_write(self, tmp_path, monkeypatch):
        ih = self._mod()

        def _fail(url):
            raise OSError("HTTP 500")

        monkeypatch.setattr(ih, "_http_get", _fail)
        try:
            ih.fetch_psalm(9, cache_dir=tmp_path)
            raised = False
        except OSError:
            raised = True
        assert raised
        assert not (tmp_path / "PsalmNrR 9.html").exists()


class TestCalibrate:
    def _fn(self):
        from scripts.ingest_hacohen import calibrate

        return calibrate

    def test_go_on_well_formed_sample(self, tmp_path):
        good = (FIX / "psalm1.html").read_text(encoding="utf-8")
        for n in (1, 118, 151):
            (tmp_path / f"PsalmNrR {n}.html").write_text(good, encoding="utf-8")
        result = self._fn()(sample=[1, 118, 151], cache_dir=tmp_path)
        assert result["go"] is True
        # parsed[1] is the list of (psalm, verse, text); [0][:2] = (psalm, verse).
        # (Plan's assertion compared a 3-tuple to (1,1) — corrected in-execution.)
        assert result["parsed"][1][0][:2] == (1, 1)

    def test_nogo_on_malformed(self, tmp_path):
        bad = (FIX / "psalm_malformed.html").read_text(encoding="utf-8")
        for n in (1, 118, 151):
            (tmp_path / f"PsalmNrR {n}.html").write_text(bad, encoding="utf-8")
        result = self._fn()(sample=[1, 118, 151], cache_dir=tmp_path)
        assert result["go"] is False
        assert "no verses parsed" in result["reason"].lower()
