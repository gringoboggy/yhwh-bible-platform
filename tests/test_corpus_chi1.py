"""ω.27 follow-on (2026-05-11) — χ.1 Strong's Greek + Naves Topical
detector test classes, split out of the monolithic
``tests/test_scripts.py`` into a topic file alongside the other
ω.27 follow-on splits.

Sixth topic extraction. The χ.1 arc added the Strong's Greek
lexicon source loader, the GreekWordDetector that promotes
detected Greek tokens into `lang-greek` xref notes, the
fetch-source utilities for the underlying dataset, and the
at-scale driver that runs the detector across the corpus. The
section also bundles TestRunNavesAtScaleDriver — the Naves
Topical driver shares the χ-cluster pattern (detector class +
driver script + batch-promote pipeline; see CLAUDE_PROJECT_RULES
§9 "Add a new corpus-growth phase").

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------- Phase χ.1 : Strong's Greek + GreekWordDetector ----------


class TestStrongsGreekSourceLoader:
    """Loader-level checks for ``scripts.core.sources.StrongsGreek``:
    SourceMissingError shape, in-memory loader against a synthetic JSON
    fixture, tolerance for both ``xlit`` and ``translit`` field names
    (openscriptures' Greek dump uses ``translit`` where Hebrew uses
    ``xlit``)."""

    @classmethod
    def setup_class(cls):
        from scripts.core import sources as src

        cls.src = src

    def test_loader_raises_when_cache_absent(self, tmp_path, monkeypatch):
        nope = tmp_path / "strongs_greek.json"
        monkeypatch.setattr(self.src.StrongsGreek, "PATH", nope)
        try:
            self.src.StrongsGreek()
        except self.src.SourceMissingError as e:
            assert "fetch_sources.py" in str(e)
            return
        raise AssertionError("expected SourceMissingError")

    def test_loader_reads_synthetic_cache(self, tmp_path, monkeypatch):
        cache = {
            "G3056": {
                "lemma": "λόγος",
                "translit": "logos",
                "pron": "log'-os",
                "derivation": "from G3004",
                "strongs_def": "something said (incl. the thought)",
                "kjv_def": "Word, saying.",
            },
            "G26": {
                "lemma": "ἀγάπη",
                "xlit": "agape",  # alt spelling — also accepted
                "pron": "ag-ah'-pay",
                "derivation": "from G25",
                "strongs_def": "love, i.e. affection or benevolence",
                "kjv_def": "(feast of) charity, dear, love.",
            },
        }
        cache_path = tmp_path / "strongs_greek.json"
        cache_path.write_text(json.dumps(cache), encoding="utf-8")
        monkeypatch.setattr(self.src.StrongsGreek, "PATH", cache_path)

        g = self.src.StrongsGreek()
        assert len(g) == 2
        assert "G3056" in g and "G26" in g

        logos = g.get("G3056")
        assert logos.lemma == "λόγος"
        assert logos.xlit == "logos"  # normalised from translit
        assert "Word" in logos.kjv_def
        assert "G3056" in logos.attribution
        assert "Greek" in logos.attribution

        agape = g.get("G26")
        assert agape.xlit == "agape"  # accepted via xlit field too
        assert agape.lemma == "ἀγάπη"

        assert g.get("G99999") is None  # absent number

    def test_singleton_caches(self, tmp_path, monkeypatch):
        cache = {
            "G1": {
                "lemma": "Α",
                "translit": "a",
                "pron": "al'-fah",
                "derivation": "first letter",
                "strongs_def": "Alpha",
                "kjv_def": "Alpha.",
            }
        }
        cache_path = tmp_path / "strongs_greek.json"
        cache_path.write_text(json.dumps(cache), encoding="utf-8")
        monkeypatch.setattr(self.src.StrongsGreek, "PATH", cache_path)
        self.src.strongs_greek.cache_clear()

        g1 = self.src.strongs_greek()
        g2 = self.src.strongs_greek()
        assert g1 is g2  # lru_cache hit


class TestGreekWordDetector:
    """Detector-level checks: candidate shape, kind, attribution,
    OT-skip behaviour, registration in ALL_DETECTORS."""

    @classmethod
    def setup_class(cls):
        from scripts.core import sources as src, detectors as det

        cls.src = src
        cls.det = det

    def _stub_lex(self, monkeypatch, mapping: dict):
        """Wire ``sources.strongs_greek()`` to a stub with a synthetic
        lex. ``mapping`` is a dict of G-number → entry-dict."""

        class StubEntry:
            def __init__(self, num, d):
                self.number = num
                self.lemma = d.get("lemma", "")
                self.xlit = d.get("xlit") or d.get("translit", "")
                self.pron = d.get("pron", "")
                self.derivation = d.get("derivation", "")
                self.definition = d.get("strongs_def", "")
                self.kjv_def = d.get("kjv_def", "")

            @property
            def attribution(self):
                return f"Strong's {self.number}, Greek Testament. PD."

        class StubLex:
            def __init__(self, m):
                self._m = m

            def get(self, num):
                d = self._m.get(num)
                return StubEntry(num, d) if d else None

        # Bypass the lru_cache singleton in the module
        self.src.strongs_greek.cache_clear()
        monkeypatch.setattr(self.src, "strongs_greek", lambda: StubLex(mapping))

    def test_detector_registered_in_all_detectors(self):
        names = [d.__name__ for d in self.det.ALL_DETECTORS]
        assert "GreekWordDetector" in names

    def test_detector_kind_and_label(self):
        assert self.det.GreekWordDetector.kind == "lang-greek"

    def test_skips_ot_books(self, monkeypatch):
        self._stub_lex(
            monkeypatch,
            {
                "G2316": {
                    "lemma": "θεός",
                    "translit": "theos",
                    "pron": "theh'-os",
                    "derivation": "of uncertain affinity",
                    "strongs_def": "a deity, especially the supreme Divinity",
                    "kjv_def": "God, god.",
                },
            },
        )
        d = self.det.GreekWordDetector()
        # OT book — even though "God" appears, no candidate emitted.
        out = d.detect("gen", 1, 1, "In the beginning God created…")
        assert out == []

    def test_emits_candidate_on_keyword_match_in_nt(self, monkeypatch):
        self._stub_lex(
            monkeypatch,
            {
                "G3056": {
                    "lemma": "λόγος",
                    "translit": "logos",
                    "pron": "log'-os",
                    "derivation": "from G3004",
                    "strongs_def": "something said (incl. thought)",
                    "kjv_def": "Word.",
                },
            },
        )
        d = self.det.GreekWordDetector()
        out = d.detect("jhn", 1, 1, "In the beginning was the Word…")
        assert len(out) == 1
        c = out[0]
        assert c.kind == "lang-greek"
        assert c.book == "jhn" and c.chapter == 1 and c.verse == 1
        assert c.source_name == "G3056"
        assert "logos" in c.draft_body.lower() or "λόγος" in c.draft_body
        assert c.draft_title == "Greek"
        assert c.detector == "GreekWordDetector"
        assert "Greek" in c.source_attribution
        assert c.anchor.lower() == "word"  # cased substring from verse

    def test_dedupes_repeated_strongs_within_verse(self, monkeypatch):
        # Map distinct keywords to the SAME strongs number — detector
        # should emit only one candidate per strongs number per verse.
        self._stub_lex(
            monkeypatch,
            {
                "G2962": {
                    "lemma": "κύριος",
                    "translit": "kyrios",
                    "pron": "koo'-ree-os",
                    "derivation": "from kyros (supremacy)",
                    "strongs_def": "supreme in authority, i.e. master",
                    "kjv_def": "God, Lord, master, Sir.",
                },
            },
        )
        d = self.det.GreekWordDetector()
        # Both "lord" and "Lord" map to G2962 in GREEK_KEYWORD_MAP — but
        # the same strongs is also keyed under multiple english words.
        # Pick a verse with multiple synonyms to verify dedupe.
        out = d.detect("rom", 10, 9, "the Lord Jesus is Lord and Lord above")
        assert len(out) == 1
        assert out[0].source_name == "G2962"

    def test_nt_only_filter_excludes_ot(self):
        d_class = self.det.GreekWordDetector
        # Sanity-check the NT_BOOKS set
        assert "jhn" in d_class.NT_BOOKS
        assert "gen" not in d_class.NT_BOOKS
        assert "psa" not in d_class.NT_BOOKS

    def test_high_confidence_in_johannine_or_pauline_core(self, monkeypatch):
        self._stub_lex(
            monkeypatch,
            {
                "G3056": {
                    "lemma": "λόγος",
                    "translit": "logos",
                    "pron": "log'-os",
                    "derivation": "",
                    "strongs_def": "word",
                    "kjv_def": "Word.",
                },
                "G26": {
                    "lemma": "ἀγάπη",
                    "translit": "agape",
                    "pron": "ag-ah'-pay",
                    "derivation": "",
                    "strongs_def": "love",
                    "kjv_def": "love.",
                },
            },
        )
        d = self.det.GreekWordDetector()
        # John 1 ("word") — high confidence
        c_jhn = d.detect("jhn", 1, 1, "In the beginning was the Word")[0]
        assert c_jhn.confidence >= 0.8
        # Regression guard for the php/jas book-code bug: the CANONICAL codes
        # for Philippians/James must be in NT_BOOKS so the Greek detector RUNS
        # (and the Hebrew detector SKIPS) on them. The pre-fix code used the
        # non-canonical php/jas, so real phi/jam were mis-routed — and the old
        # test asserted on "jas" (which IS php/jas-shaped), masking the bug.
        assert {"phi", "jam"} <= self.det.GreekWordDetector.NT_BOOKS
        assert {"phi", "jam"} <= self.det.HebrewWordDetector.NT_BOOKS
        # James 1 (canonical "jam") must receive a Greek candidate, lower
        # confidence than John 1 (not Joh/Rom 1-8).
        jam_cands = d.detect("jam", 1, 1, "the engrafted word, which is able")
        assert jam_cands, "James (jam) is an NT book — must receive Greek candidates"
        assert jam_cands[0].confidence < c_jhn.confidence


class TestNTBookLanguageInvariant:
    """Corpus-data guard for the php/jas book-code bug — the DATA-cleanup
    half (the code-fix half is TestGreekWordDetector's NT_BOOKS asserts).

    The book-code drift (php/jas vs canonical phi/jam) wrongly attached
    Strong's-Hebrew word-studies to the two Greek NT books Philippians
    (phi) + James (jam) — 165 total — and simultaneously withheld Greek
    from them. The Hebrew lexicon does not apply to the Greek NT: the
    detectors enforce this by skipping NT_BOOKS, and the corpus must
    agree. These invariants must hold corpus-wide after the cleanup.
    """

    # The 27-book NT canon (canonical 3-letter codes; see books.yaml).
    NT_BOOKS = (
        "mat",
        "mrk",
        "luk",
        "jhn",
        "act",
        "rom",
        "1co",
        "2co",
        "gal",
        "eph",
        "phi",
        "col",
        "1th",
        "2th",
        "1ti",
        "2ti",
        "tit",
        "phm",
        "heb",
        "jam",
        "1pe",
        "2pe",
        "1jn",
        "2jn",
        "3jn",
        "jud",
        "rev",
    )

    @staticmethod
    def _kind_counts(book: str) -> dict:
        """{kind: count} for a book's NOTES list, read via the project's
        notes loader (literal-only; code in notes modules is never run)."""
        from scripts.core.notes_io import load_notes

        path = REPO_ROOT / "content" / "notes" / f"{book}.py"
        counts: dict = {}
        for tup in load_notes(path) or []:
            if isinstance(tup, tuple) and len(tup) >= 5:
                counts[tup[4]] = counts.get(tup[4], 0) + 1
        return counts

    def test_no_nt_book_carries_lang_hebrew(self):
        offenders = {b: self._kind_counts(b).get("lang-hebrew", 0) for b in self.NT_BOOKS}
        offenders = {b: n for b, n in offenders.items() if n}
        assert not offenders, (
            f"NT (Greek) books must not carry lang-hebrew notes — the php/jas "
            f"book-code drift mis-routed Strong's-Hebrew here; offenders: {offenders}"
        )

    def test_philippians_and_james_carry_lang_greek(self):
        for book in ("phi", "jam"):
            n = self._kind_counts(book).get("lang-greek", 0)
            assert n > 0, (
                f"{book} is a Greek NT book — must carry lang-greek notes; the "
                f"book-code bug withheld Greek from it (got {n})"
            )


class TestStrongsGreekFetchUtilities:
    """Pure-function checks for the χ.1 fetch_sources.py additions:
    parser is registered, parses synthetic JS-wrapped JSON, fetcher
    config knows the source, attribution doc gets the Greek section."""

    @classmethod
    def setup_class(cls):
        from scripts import fetch_sources as fs

        cls.fs = fs

    def test_parser_registered(self):
        from scripts.core.fetcher_config import KNOWN_PARSERS

        assert "strongs-greek-js" in KNOWN_PARSERS
        assert "strongs-greek-js" in self.fs.PARSERS

    def test_parser_extracts_dict_from_js_wrapper(self, monkeypatch):
        synthetic = (
            "var strongsGreekDictionary = "
            '{"G1":{"lemma":"\\u0391","translit":"a",'
            '"pron":"al-fah","derivation":"first letter",'
            '"strongs_def":"Alpha","kjv_def":"Alpha."}};\n'
        )

        def fake_get(url, **_kw):
            return synthetic.encode("utf-8")

        # Patch the http wrapper used inside the parser
        from scripts.core import http as core_http

        monkeypatch.setattr(core_http, "get", fake_get)
        # Also patch the local _http reference inside fetch_sources
        monkeypatch.setattr(self.fs._http, "get", fake_get)

        out = self.fs._parse_strongs_greek_js("https://example/test.js")
        assert isinstance(out, dict)
        assert "G1" in out
        assert out["G1"]["translit"] == "a"

    def test_parser_returns_none_on_unrecognised_payload(self, monkeypatch):
        def fake_get(url, **_kw):
            return b"not the dictionary you were expecting"

        from scripts.core import http as core_http

        monkeypatch.setattr(core_http, "get", fake_get)
        monkeypatch.setattr(self.fs._http, "get", fake_get)

        assert self.fs._parse_strongs_greek_js("https://example/bad") is None

    def test_fetcher_config_includes_strongs_greek(self):
        from scripts.core.fetcher_config import load_fetcher_config

        cfg = load_fetcher_config()
        sg = cfg.find("strongs_greek")
        assert sg is not None
        assert sg.required is True
        assert sg.cache_path == "strongs_greek.json"
        assert any(c.parser == "strongs-greek-js" for c in sg.candidates)

    def test_attribution_doc_includes_strongs_greek(self, tmp_path, monkeypatch):
        """write_attributions composes its body from the loaded config —
        adding the new source to _fetchers.json should automatically
        surface its license in ATTRIBUTIONS.md (no code change required
        in fetch_sources.py per υ.7)."""
        from scripts.core.fetcher_config import load_fetcher_config

        cfg = load_fetcher_config()
        monkeypatch.setattr(self.fs, "SOURCES_DIR", tmp_path)
        self.fs.write_attributions(cfg)
        attrs = (tmp_path / "ATTRIBUTIONS.md").read_text(encoding="utf-8")
        assert "Strong's Greek Dictionary" in attrs


class TestRunGreekAtScaleDriver:
    """End-to-end driver test: a synthetic strongs_greek.json + a real
    run of run_greek_at_scale.run_greek_for_book → verifies candidate
    JSON is emitted in the same shape prospect.py / batch_promote use,
    and that the OT-book skip + append-not-clobber contracts hold."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.driver = importlib.import_module("scripts.run_greek_at_scale")
        from scripts.core import sources as src

        cls.src = src

    def _wire_synthetic_strongs(self, tmp_path, monkeypatch):
        cache = {
            "G3056": {
                "lemma": "λόγος",
                "translit": "logos",
                "pron": "log'-os",
                "derivation": "from G3004",
                "strongs_def": "something said",
                "kjv_def": "Word.",
            },
            "G26": {
                "lemma": "ἀγάπη",
                "translit": "agape",
                "pron": "ag-ah'-pay",
                "derivation": "from G25",
                "strongs_def": "love",
                "kjv_def": "love.",
            },
            "G2316": {
                "lemma": "θεός",
                "translit": "theos",
                "pron": "theh'-os",
                "derivation": "of uncertain",
                "strongs_def": "deity",
                "kjv_def": "God.",
            },
        }
        cache_path = tmp_path / "strongs_greek.json"
        cache_path.write_text(json.dumps(cache), encoding="utf-8")
        monkeypatch.setattr(self.src.StrongsGreek, "PATH", cache_path)
        self.src.strongs_greek.cache_clear()

    def test_driver_skips_ot_books(self, tmp_path, monkeypatch):
        self._wire_synthetic_strongs(tmp_path, monkeypatch)
        cand_dir = tmp_path / "candidates"
        monkeypatch.setattr(self.driver, "CANDIDATES_DIR", cand_dir)

        stats = self.driver.run_greek_for_book("gen")
        assert stats["skipped"] is True
        assert "OT" in stats["reason"]
        assert stats["candidates_written"] == 0

    def test_driver_emits_prospect_format(self, tmp_path, monkeypatch):
        self._wire_synthetic_strongs(tmp_path, monkeypatch)
        cand_dir = tmp_path / "candidates"
        monkeypatch.setattr(self.driver, "CANDIDATES_DIR", cand_dir)

        # John exists in KJV data; pick it for the smoke run.
        stats = self.driver.run_greek_for_book("jhn")
        if stats.get("skipped"):
            pytest.skip(f"jhn KJV data unavailable: {stats.get('reason')}")
        assert stats["chapters_processed"] >= 1
        if stats["candidates_written"] == 0:
            pytest.skip("no Greek keywords matched John KJV — expected when keyword map is sparse")

        # Find any candidate file written for John
        files = sorted(cand_dir.glob("jhn_ch_*.json"))
        assert files, "expected at least one jhn_ch_*.json"
        data = json.loads(files[0].read_text(encoding="utf-8"))
        assert data["book"] == "jhn"
        assert any(c["kind"] == "lang-greek" for c in data["candidates"])
        any_lang_greek = next(c for c in data["candidates"] if c["kind"] == "lang-greek")
        assert any_lang_greek["status"] == "pending"
        assert any_lang_greek["detector"] == "GreekWordDetector"

    def test_driver_appends_to_existing_chapter_file(self, tmp_path, monkeypatch):
        """If a prior at-scale driver (xref / hebrew / naves) already
        wrote candidates for the same chapter, lang-greek must append
        rather than clobber. Mirrors TestRunNavesAtScaleDriver."""
        cand_dir = tmp_path / "candidates"
        cand_dir.mkdir()
        prior = {
            "book": "jhn",
            "chapter": 1,
            "generated_at": "2026-01-01T00:00:00+00:00",
            "n_candidates": 1,
            "candidates": [
                {
                    "id": "jhn-1-1-001",
                    "verse": 1,
                    "kind": "xref-citation",
                    "anchor": "",
                    "confidence": 0.7,
                    "source_name": "TSK",
                    "source_attribution": "TSK PD.",
                    "draft_title": "Cross-ref",
                    "draft_label": "Cite.",
                    "draft_body": "<em>existing</em>",
                    "detector": "CrossRefDetector",
                    "reviewer_notes": "",
                    "status": "pending",
                }
            ],
        }
        out_path = cand_dir / "jhn_ch_001.json"
        out_path.write_text(json.dumps(prior), encoding="utf-8")

        from scripts.core.detectors import Candidate

        new = [
            Candidate(
                book="jhn",
                chapter=1,
                verse=1,
                kind="lang-greek",
                anchor="Word",
                confidence=0.85,
                source_name="G3056",
                source_attribution="Strong's G3056. PD.",
                draft_title="Greek",
                draft_label="Greek.",
                draft_body="<em>logos</em>",
                detector="GreekWordDetector",
                reviewer_notes="",
            )
        ]
        monkeypatch.setattr(self.driver, "CANDIDATES_DIR", cand_dir)
        self.driver.write_queue("jhn", 1, new)

        merged = json.loads(out_path.read_text(encoding="utf-8"))
        assert merged["n_candidates"] == 2
        kinds = [c["kind"] for c in merged["candidates"]]
        assert "xref-citation" in kinds and "lang-greek" in kinds

    def test_driver_replaces_prior_lang_greek_candidates(self, tmp_path, monkeypatch):
        """Re-running the driver against a chapter that already had
        lang-greek candidates should drop the old ones and keep the
        new (idempotent re-run pattern, mirrors run_hebrew_at_scale)."""
        cand_dir = tmp_path / "candidates"
        cand_dir.mkdir()
        prior = {
            "book": "jhn",
            "chapter": 1,
            "generated_at": "2026-01-01T00:00:00+00:00",
            "n_candidates": 2,
            "candidates": [
                {
                    "id": "jhn-1-1-001",
                    "verse": 1,
                    "kind": "xref-citation",
                    "anchor": "",
                    "confidence": 0.7,
                    "source_name": "TSK",
                    "source_attribution": "TSK PD.",
                    "draft_title": "Cross-ref",
                    "draft_label": "Cite.",
                    "draft_body": "<em>existing</em>",
                    "detector": "CrossRefDetector",
                    "reviewer_notes": "",
                    "status": "pending",
                },
                {
                    "id": "jhn-1-1-002",
                    "verse": 1,
                    "kind": "lang-greek",
                    "anchor": "old",
                    "confidence": 0.65,
                    "source_name": "G99",
                    "source_attribution": "Strong's G99. PD.",
                    "draft_title": "Greek",
                    "draft_label": "Greek.",
                    "draft_body": "<em>old</em>",
                    "detector": "GreekWordDetector",
                    "reviewer_notes": "",
                    "status": "pending",
                },
            ],
        }
        out_path = cand_dir / "jhn_ch_001.json"
        out_path.write_text(json.dumps(prior), encoding="utf-8")

        from scripts.core.detectors import Candidate

        new = [
            Candidate(
                book="jhn",
                chapter=1,
                verse=1,
                kind="lang-greek",
                anchor="Word",
                confidence=0.85,
                source_name="G3056",
                source_attribution="Strong's G3056. PD.",
                draft_title="Greek",
                draft_label="Greek.",
                draft_body="<em>logos new</em>",
                detector="GreekWordDetector",
                reviewer_notes="",
            )
        ]
        monkeypatch.setattr(self.driver, "CANDIDATES_DIR", cand_dir)
        self.driver.write_queue("jhn", 1, new)

        merged = json.loads(out_path.read_text(encoding="utf-8"))
        # xref kept; old lang-greek dropped; one new lang-greek
        kinds = [c["kind"] for c in merged["candidates"]]
        assert kinds.count("xref-citation") == 1
        assert kinds.count("lang-greek") == 1
        new_lg = next(c for c in merged["candidates"] if c["kind"] == "lang-greek")
        assert new_lg["source_name"] == "G3056"


class TestRunNavesAtScaleDriver:
    """End-to-end driver test: a synthetic Nave's cache + a real run
    of run_naves_at_scale.run_naves_for_book → verifies candidate JSON
    is emitted in the same shape prospect.py / batch_promote use."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.driver = importlib.import_module("scripts.run_naves_at_scale")
        from scripts.core import sources as src

        cls.src = src

    def test_driver_emits_prospect_format(self, tmp_path, monkeypatch):
        # Build a tiny cache file
        cache = {
            "_meta": {"n_topics": 2, "n_refs": 3, "source": "synthetic"},
            "topics": {
                "Faith": [["heb", 11, 1]],
                "Creation": [["gen", 1, 1], ["heb", 11, 3]],
            },
            "verses": {
                "gen": {"1": {"1": ["Creation"]}},
                "heb": {"11": {"1": ["Faith"], "3": ["Creation"]}},
            },
        }
        cache_path = tmp_path / "naves_topical.json"
        cache_path.write_text(json.dumps(cache), encoding="utf-8")
        monkeypatch.setattr(self.src.NavesTopical, "PATH", cache_path)
        self.src.naves_topical.cache_clear()

        # Redirect candidates output to tmp_path
        cand_dir = tmp_path / "candidates"
        monkeypatch.setattr(self.driver, "CANDIDATES_DIR", cand_dir)

        stats = self.driver.run_naves_for_book("gen")
        assert stats["chapters_processed"] == 1
        assert stats["candidates_written"] == 1

        out_path = cand_dir / "gen_ch_001.json"
        assert out_path.is_file()
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert data["book"] == "gen"
        assert data["chapter"] == 1
        assert data["candidates"][0]["kind"] == "topic-nave"
        assert data["candidates"][0]["status"] == "pending"

    def test_driver_appends_to_existing_chapter_file(self, tmp_path, monkeypatch):
        """If another at-scale driver already wrote candidates for the
        same chapter (e.g. xref), we must append rather than clobber.
        """
        cand_dir = tmp_path / "candidates"
        cand_dir.mkdir()
        prior = {
            "book": "gen",
            "chapter": 1,
            "generated_at": "2026-01-01T00:00:00+00:00",
            "n_candidates": 1,
            "candidates": [
                {
                    "id": "gen-1-1-001",
                    "verse": 1,
                    "kind": "xref-citation",
                    "anchor": "",
                    "confidence": 0.7,
                    "source_name": "TSK",
                    "source_attribution": "TSK PD.",
                    "draft_title": "Cross-ref",
                    "draft_label": "Cite.",
                    "draft_body": "<em>existing</em>",
                    "detector": "CrossRefDetector",
                    "reviewer_notes": "",
                    "status": "pending",
                }
            ],
        }
        out_path = cand_dir / "gen_ch_001.json"
        out_path.write_text(json.dumps(prior), encoding="utf-8")

        # Now write naves candidates against the same chapter
        from scripts.core.detectors import Candidate

        new = [
            Candidate(
                book="gen",
                chapter=1,
                verse=2,
                kind="topic-nave",
                anchor="",
                confidence=0.7,
                source_name="Nave: X",
                source_attribution="Nave's PD.",
                draft_title="Topic",
                draft_label="Topic.",
                draft_body="<em>topic</em>",
                detector="NaveTopicalDetector",
                reviewer_notes="",
            )
        ]
        monkeypatch.setattr(self.driver, "CANDIDATES_DIR", cand_dir)
        self.driver.write_queue("gen", 1, new)

        merged = json.loads(out_path.read_text(encoding="utf-8"))
        assert merged["n_candidates"] == 2
        kinds = [c["kind"] for c in merged["candidates"]]
        assert "xref-citation" in kinds and "topic-nave" in kinds
