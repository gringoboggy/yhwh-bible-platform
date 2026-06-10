"""ω.27 follow-on (2026-05-11) — v1.0 polish test classes (ω.34 +
ψ.34 + ω.34.1 + TestFaviconRoute), split out of the monolithic
``tests/test_scripts.py`` into a topic file alongside the other
ω.27 follow-on splits.

Seventh topic extraction. The v1.0 polish push shipped three
phases in quick succession on 2026-05-10/11:

- ω.34   test-gap pass — every edition's enabled-kind set
  pinned + an EPUB end-to-end build test guard
- ψ.34   matrix JS extraction — the inline matrix JS moved
  from `MATRIX_HTML` into `scripts/templates/matrix_app.js`
  served via `/static/matrix.js`
- ω.34.1 test cleanup — per-book corpus floors, Strong's
  Hebrew loader coverage, CrossRefDetector edge cases

The section also bundles TestFaviconRoute (the icon-pack
ingestion + `/favicon.ico` wiring) which has no explicit
phase marker but sat adjacent in the file.

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.
"""

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------- Phase ω.34 : test gap pass --------------------------------


class TestOmega34EditionKindSetPins:
    """ω.34 — pin per-edition kind-set invariants.

    The bug class this catches: a typo in `editions.yaml`
    (`enabled_kinds: [comm-rabbic]` vs `comm-rabbinic`) silently
    drops a kind. The matrix surface uses `_enabled_kinds_for_edition`
    so the typo'd entry just disappears, and only the loose
    1381-note corpus floor (often slack by orders of magnitude) had
    a chance of catching it before this test.

    Two complementary checks:

      1. **Every code in `enabled_kinds` / `disabled_kinds` resolves
         to a real kind in `kinds.yaml`.** Catches typos directly.
      2. **Tradition-defining kinds are present in their primary
         tradition.** A regression that drops `comm-catholic` from
         `catholic-study` would still pass check 1 (the code
         resolves) but break the product. Pin the tradition
         signatures.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import config

        cls.editions = config.editions_by_id()
        cls.all_kinds = config.load_kinds()
        cls.kind_codes = {k["code"] for k in cls.all_kinds}

    def test_every_explicit_kind_resolves_in_kinds_yaml(self):
        from scripts.core import config

        # Re-read in case the test fixture is stale
        editions = config.editions_by_id()
        all_kind_codes = {k["code"] for k in config.load_kinds()}

        unknown = {}
        for ed_id, ed in editions.items():
            mentioned = set(ed.get("enabled_kinds") or []) | set(ed.get("disabled_kinds") or [])
            unknown_for_ed = mentioned - all_kind_codes
            if unknown_for_ed:
                unknown[ed_id] = sorted(unknown_for_ed)
        assert unknown == {}, (
            f"editions.yaml references kind codes not in kinds.yaml: {unknown}. "
            "This is the typo class — fix the typo or add the kind to kinds.yaml."
        )

    def test_every_enabled_category_resolves_in_kinds_yaml(self):
        from scripts.core import config

        editions = config.editions_by_id()
        all_categories = {k.get("category") for k in config.load_kinds()}
        all_categories.discard(None)

        unknown = {}
        for ed_id, ed in editions.items():
            mentioned = set(ed.get("enabled_categories") or [])
            unknown_for_ed = mentioned - all_categories
            if unknown_for_ed:
                unknown[ed_id] = sorted(unknown_for_ed)
        assert unknown == {}, f"editions.yaml has unknown enabled_categories: {unknown}"

    def test_tradition_signature_kinds_present(self):
        # If catholic-study loses comm-catholic, the product is broken
        # in a way that no other test pins. These signature pins lock
        # tradition identity into the test suite.
        from scripts.core.matrix import _enabled_kinds_for_edition

        signatures = {
            "catholic-study": "comm-catholic",
            "jewish-study": "comm-rabbinic",
            "ethiopian-tewahedo": "comm-ethiopian",
            "evangelical-reformed": "comm-reformation",
            "eastern-orthodox": "comm-orthodox",
            "coptic-orthodox": "comm-orthodox",
            "lutheran-confessional": "comm-reformation",
            "anglican-bcp": "comm-catholic",
            "scholarly-academic": "comm-modern-critical",
        }
        missing = []
        for ed_id, must_have in signatures.items():
            if ed_id not in self.editions:
                missing.append(f"{ed_id}: edition itself missing")
                continue
            kinds = _enabled_kinds_for_edition(self.editions[ed_id], self.all_kinds)
            if must_have not in kinds:
                missing.append(f"{ed_id}: {must_have!r} not in enabled set")
        assert missing == [], "Tradition signatures dropped: " + "; ".join(missing)

    def test_each_edition_has_floor_of_kinds(self):
        # Sanity floor — no edition should ship with fewer than 25
        # enabled kinds (every shipping edition is well above this).
        # Catches "edition lost most of its kinds" regressions.
        from scripts.core.matrix import _enabled_kinds_for_edition

        too_thin = []
        for ed_id, ed in self.editions.items():
            kinds = _enabled_kinds_for_edition(ed, self.all_kinds)
            if len(kinds) < 25:
                too_thin.append(f"{ed_id}: only {len(kinds)} kinds")
        assert too_thin == [], "Editions below kind-count floor: " + "; ".join(too_thin)

    def test_ai_drafted_kinds_filtered_out_for_every_edition_by_default(self):
        # Every edition today defaults to enable_ai_notes=False (or
        # unset). The AI_DRAFTED_KINDS gate must apply uniformly. A
        # regression that flipped the gate's polarity would silently
        # ship AI drafts on every edition.
        from scripts.core.matrix import AI_DRAFTED_KINDS, _enabled_kinds_for_edition

        leaks = []
        for ed_id, ed in self.editions.items():
            if ed.get("enable_ai_notes"):
                continue  # opt-in editions are fair to include
            kinds = _enabled_kinds_for_edition(ed, self.all_kinds)
            ai_leaked = AI_DRAFTED_KINDS & kinds
            if ai_leaked:
                leaks.append(f"{ed_id}: leaked {sorted(ai_leaked)}")
        assert leaks == [], "AI-drafted kinds leaked: " + "; ".join(leaks)


class TestOmega34EpubEndToEnd:
    """ω.34 — end-to-end EPUB smoke test.

    Closest pre-ω.34 coverage was `test_build_one_stats_*` with
    `dry_run=True` (never reaches the EPUB writer) and
    `TestApiBuildAll` (mocks `build_one`). A regression in
    `_zip_epub`, theme injection, OPF generation, or NCX/nav
    construction would have shipped silently.

    This test does the minimum to assert the EPUB writer's
    contract: build one edition end-to-end, open the resulting
    .epub as a zipfile, and assert the structural invariants.
    Limited to ONE edition (the smallest, jewish-study) to keep
    test wall-time manageable; full 9-edition coverage is covered
    by `TestApiBuildAll` (mocked) plus this real-build smoke.
    """

    def test_build_one_produces_valid_epub_structure(self, tmp_path):
        import zipfile

        import pytest

        from scripts.build_edition import EPUB_DIR, build_one
        from scripts.core import config

        # Skip if `epub_working/` is absent — the EPUB scaffolding is
        # generated by `scripts/inject.py --all-books` and is part of
        # a dev's standard setup, not the source tree. On a fresh
        # checkout (or after a tree clean), the scaffolding might not
        # exist; in that case we degrade to "skip with clear reason"
        # rather than fail. Any dev who has run inject gets the
        # full e2e signal.
        if not EPUB_DIR.is_dir() or not any(EPUB_DIR.iterdir()):
            pytest.skip(
                f"epub_working scaffold not present at {EPUB_DIR} — "
                "run `python scripts/inject.py --all-books` to enable "
                "this e2e test"
            )

        out_dir = tmp_path / "out"
        out_dir.mkdir()

        # jewish-study is the smallest canon (Tanakh, 39 books) and
        # therefore the fastest real build. We're not asserting
        # speed; we're asserting the writer's contract.
        all_kinds = config.load_kinds()
        result = build_one(
            "jewish-study",
            output_dir=out_dir,
            version="omega34_smoke",
            all_kinds=all_kinds,
            dry_run=False,
        )

        # Build must succeed. build_edition.build_one() returns the stats
        # dict whose `output_path` is the freshly-built (or cache-restored)
        # EPUB; it has no "ok"/"filename" key — that is api_export_build's
        # separate response contract, not this function's. A cache hit /
        # incremental skip is still a successful build with a real artifact
        # at output_path.
        epub_path = result["output_path"]
        assert epub_path.is_file(), f"build_one did not produce an EPUB: {result}"
        assert epub_path.is_file(), f"EPUB not at expected path: {epub_path}"
        assert epub_path.stat().st_size > 0, "EPUB is empty"

        # Structural invariants — open as a zipfile and inspect
        with zipfile.ZipFile(epub_path) as z:
            names = z.namelist()

            # Mandatory EPUB files
            assert "mimetype" in names, "missing mimetype entry"
            mimetype = z.read("mimetype").decode("ascii")
            assert mimetype.strip() == "application/epub+zip", f"wrong mimetype: {mimetype!r}"

            # Container manifest — points to the OPF
            assert "META-INF/container.xml" in names, "missing META-INF/container.xml"
            container = z.read("META-INF/container.xml").decode("utf-8")
            assert "rootfile" in container, "container.xml missing rootfile"

            # OPF (package document) must exist somewhere
            opf_files = [n for n in names if n.endswith(".opf")]
            assert opf_files, f"no .opf in EPUB: {names[:20]}"
            opf = z.read(opf_files[0]).decode("utf-8")
            assert "<package" in opf, "OPF missing <package> root"
            assert "<manifest>" in opf, "OPF missing <manifest>"
            assert "<spine" in opf, "OPF missing <spine>"

            # TOC — either NCX (epub2-style) or nav.xhtml (epub3-style)
            has_ncx = any(n.endswith(".ncx") for n in names)
            has_nav = any("nav" in n.lower() and n.endswith((".xhtml", ".html")) for n in names)
            assert has_ncx or has_nav, f"no TOC (NCX or nav) in EPUB: {names[:20]}"

            # Content — at least one chapter file
            content_files = [n for n in names if n.endswith((".xhtml", ".html")) and "nav" not in n.lower()]
            assert len(content_files) >= 1, f"no chapter content: {content_files}"

            # First content file should have the verse-reading shape
            first_content = z.read(content_files[0]).decode("utf-8")
            assert "<html" in first_content, "first content file is not HTML"
            assert "<body" in first_content, "first content file has no body"


# ---------- Phase ψ.34 : matrix JS extraction --------------------------


class TestPsi34MatrixJsExtraction:
    """ψ.34 — matrix console JS lifted out of the inline `<script>`
    block in `scripts/templates/matrix.py` into a standalone
    `scripts/templates/matrix_app.js`, served by `/static/matrix.js`.

    Pure refactor — no behavior change. The pins below catch
    re-inlining drift and route regressions.
    """

    @classmethod
    def setup_class(cls):
        from pathlib import Path

        cls.REPO = Path(__file__).resolve().parent.parent
        cls.JS_PATH = cls.REPO / "scripts" / "templates" / "matrix_app.js"

    # ---- file presence ----

    def test_matrix_app_js_exists(self):
        assert self.JS_PATH.is_file(), (
            f"matrix_app.js missing at {self.JS_PATH} — ψ.34 invariant: "
            "the standalone JS file must exist and be servable"
        )

    def test_matrix_app_js_has_expected_app_entry_point(self):
        text = self.JS_PATH.read_text(encoding="utf-8")
        assert "loadMatrix" in text, "matrix_app.js missing loadMatrix entrypoint"
        assert "function buildBody" in text, "matrix_app.js missing buildBody"
        assert "let DATA" in text or "var DATA" in text, "matrix_app.js missing DATA state"

    def test_matrix_app_js_size_within_expected_range(self):
        # Floor: 1000 lines. Ceiling: 5000 lines. At time of ψ.34: ~1550 lines.
        text = self.JS_PATH.read_text(encoding="utf-8")
        line_count = text.count("\n") + 1
        assert 1000 < line_count < 5000, f"matrix_app.js line count {line_count} out of expected range"

    # ---- HTML template references the static URL ----

    def test_matrix_html_references_static_script(self):
        from scripts.templates.matrix import MATRIX_HTML

        assert "/static/matrix.js" in MATRIX_HTML, "MATRIX_HTML must reference /static/matrix.js (ψ.34 invariant)"

    def test_matrix_html_no_longer_contains_inline_app_code(self):
        from scripts.templates.matrix import MATRIX_HTML

        assert "async function loadMatrix" not in MATRIX_HTML
        assert "function buildBody" not in MATRIX_HTML
        assert "let DATA = null" not in MATRIX_HTML

    def test_matrix_html_size_shrunk(self):
        # ψ.34 reduced MATRIX_HTML by ~50 KB (the matrix app block).
        # The ω.0.6 UI defense prelude is shared infrastructure
        # (lives inline in all 14 consoles via bulk_inject.py) and
        # legitimately stays inline. Threshold catches the matrix
        # app block coming back — that's the regression class.
        from scripts.templates.matrix import MATRIX_HTML

        assert len(MATRIX_HTML) < 50000, (
            f"MATRIX_HTML size {len(MATRIX_HTML)} suggests the inline "
            "matrix app came back (was ~85K before ψ.34, ~34K after)"
        )

    # ---- /static/matrix.js route ----

    def test_static_matrix_route_registered(self):
        web_py = self.REPO / "scripts" / "web.py"
        text = web_py.read_text(encoding="utf-8")
        assert '"/static/matrix.js"' in text, "web.py missing /static/matrix.js route (ψ.34 invariant)"

    def test_static_matrix_route_serves_js_via_handler(self):
        from io import BytesIO

        from scripts.web import Handler

        class FakeWfile:
            def __init__(self):
                self.buffer = BytesIO()

            def write(self, data):
                self.buffer.write(data)

        class FakeHandler(Handler):
            def __init__(self):
                self.path = "/static/matrix.js"
                self.headers = {"Authorization": ""}
                self.wfile = FakeWfile()
                self._status = None
                self._sent_headers = {}

            def send_response(self, code, message=None):
                self._status = code

            def send_header(self, k, v):
                self._sent_headers[k] = v

            def end_headers(self):
                pass

            def log_message(self, *a, **kw):
                pass

            def _check_admin_auth(self):
                return True

        h = FakeHandler()
        h.do_GET()
        assert h._status == 200, f"expected 200, got {h._status}"
        assert "application/javascript" in h._sent_headers["Content-Type"]
        assert "private" in h._sent_headers["Cache-Control"]
        assert "Content-Security-Policy" in h._sent_headers
        assert h._sent_headers["X-Content-Type-Options"] == "nosniff"
        body = h.wfile.buffer.getvalue().decode("utf-8")
        assert "loadMatrix" in body
        assert len(body) > 1000

    def test_static_matrix_route_404_when_file_missing(self, tmp_path, monkeypatch):
        from io import BytesIO

        from scripts import web
        from scripts.web import Handler

        monkeypatch.setattr(web, "REPO", tmp_path)

        class FakeWfile:
            def __init__(self):
                self.buffer = BytesIO()

            def write(self, data):
                self.buffer.write(data)

        class FakeHandler(Handler):
            def __init__(self):
                self.path = "/static/matrix.js"
                self.headers = {"Authorization": ""}
                self.wfile = FakeWfile()
                self._status = None
                self._sent_headers = {}

            def send_response(self, code, message=None):
                self._status = code

            def send_header(self, k, v):
                self._sent_headers[k] = v

            def end_headers(self):
                pass

            def log_message(self, *a, **kw):
                pass

            def _check_admin_auth(self):
                return True

        h = FakeHandler()
        h.do_GET()
        assert h._status == 404


class TestFaviconRoute:
    """Favicon route — serves assets/icons/program_icon.ico from
    /favicon.ico with image/x-icon content-type + 24h public cache.
    Wired 2026-05-11 alongside the icon pack ingest."""

    def test_favicon_route_serves_ico(self):
        from io import BytesIO

        from scripts.web import Handler

        class FakeWfile:
            def __init__(self):
                self.buffer = BytesIO()

            def write(self, data):
                self.buffer.write(data)

        class FakeHandler(Handler):
            def __init__(self):
                self.path = "/favicon.ico"
                self.headers = {"Authorization": ""}
                self.wfile = FakeWfile()
                self._status = None
                self._sent_headers = {}

            def send_response(self, code, message=None):
                self._status = code

            def send_header(self, k, v):
                self._sent_headers[k] = v

            def end_headers(self):
                pass

            def log_message(self, *a, **kw):
                pass

            def _check_admin_auth(self):
                return True

        h = FakeHandler()
        h.do_GET()
        assert h._status == 200
        assert h._sent_headers["Content-Type"] == "image/x-icon"
        assert "max-age" in h._sent_headers["Cache-Control"]
        # ICO file magic: 00 00 01 00
        body = h.wfile.buffer.getvalue()
        assert body[:4] == bytes([0, 0, 1, 0]), "expected ICO magic bytes"
        assert len(body) > 1000, "favicon suspiciously small"

    def test_favicon_file_exists_on_disk(self):
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent
        ico = repo_root / "assets" / "icons" / "program_icon.ico"
        assert ico.is_file(), f"missing icon master: {ico}"
        # Verify it's a real .ico
        assert ico.read_bytes()[:4] == bytes([0, 0, 1, 0])

    def test_favicon_route_404_when_file_missing(self, tmp_path, monkeypatch):
        from io import BytesIO

        from scripts import web
        from scripts.web import Handler

        monkeypatch.setattr(web, "REPO", tmp_path)

        class FakeWfile:
            def __init__(self):
                self.buffer = BytesIO()

            def write(self, data):
                self.buffer.write(data)

        class FakeHandler(Handler):
            def __init__(self):
                self.path = "/favicon.ico"
                self.headers = {"Authorization": ""}
                self.wfile = FakeWfile()
                self._status = None
                self._sent_headers = {}

            def send_response(self, code, message=None):
                self._status = code

            def send_header(self, k, v):
                self._sent_headers[k] = v

            def end_headers(self):
                pass

            def log_message(self, *a, **kw):
                pass

            def _check_admin_auth(self):
                return True

        h = FakeHandler()
        h.do_GET()
        assert h._status == 404

    def test_all_documented_icon_sizes_exist(self):
        # The README catalogs sizes 16/24/32/48/64/96/128/192/256/384/512/1024
        # plus the 2048 masters. Pin so a future cleanup doesn't
        # accidentally drop one we depend on (PWA / Apple-touch / etc).
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent
        icons_dir = repo_root / "assets" / "icons"
        expected_sizes = (16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 1024)
        for size in expected_sizes:
            f = icons_dir / f"icon_{size}.png"
            assert f.is_file(), f"missing icon size: {f}"
        # PNG magic: 89 50 4E 47
        for size in expected_sizes:
            f = icons_dir / f"icon_{size}.png"
            assert f.read_bytes()[:4] == bytes([0x89, 0x50, 0x4E, 0x47]), f"{f} not a PNG"


# ---------- Phase ω.34.1 : test cleanup -------------------------------


class TestOmega341BookFloors:
    """ω.34.1 — per-book corpus floors.

    Pre-ω.34.1 the only corpus-size pin was a single floor of `>= 1381`
    against the entire 87-book set. A regression that wiped one
    obscure book (e.g. `obd.py`, `phm.py`) would not move the
    aggregate enough to trigger that test. Per-book floors close that
    gap.

    Snapshot lives in `dev/BOOK_FLOORS.json`. Floor regeneration is a
    deliberate operator action via `python scripts/update_book_floors.py`
    — the test cannot lower its own floors, only enforce them.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core.notes_io import load_notes

        cls.load_notes = staticmethod(load_notes)
        cls.NOTES_DIR = REPO_ROOT / "content" / "notes"
        cls.FLOOR_PATH = REPO_ROOT / "dev" / "BOOK_FLOORS.json"

    def test_floor_file_exists_and_parses(self):
        assert self.FLOOR_PATH.is_file(), (
            f"BOOK_FLOORS.json missing at {self.FLOOR_PATH} — regenerate via scripts/update_book_floors.py"
        )
        data = json.loads(self.FLOOR_PATH.read_text(encoding="utf-8"))
        assert "floors" in data
        assert isinstance(data["floors"], dict)
        assert len(data["floors"]) >= 80, (
            f"only {len(data['floors'])} books in floor file; "
            "expected >=80 (87 canonical books minus a handful of placeholders)"
        )

    def test_every_book_meets_floor(self):
        # The core invariant: for every book with a floor, current
        # count >= floor. Aggregates per-book violations into one
        # report so a regression that wipes 5 books shows all 5.
        data = json.loads(self.FLOOR_PATH.read_text(encoding="utf-8"))
        floors = data["floors"]

        violations = []
        for stem, floor in floors.items():
            book_path = self.NOTES_DIR / f"{stem}.py"
            if not book_path.is_file():
                if floor > 0:
                    violations.append(f"{stem}: book file missing (floor={floor})")
                continue
            current = len(self.load_notes(book_path))
            if current < floor:
                violations.append(f"{stem}: current={current} < floor={floor}")
        assert violations == [], (
            "Per-book floor violations:\n  "
            + "\n  ".join(violations)
            + "\n\nIf the reductions are intentional, regenerate floors via "
            "`python scripts/update_book_floors.py`."
        )

    def test_no_book_in_corpus_lacks_floor(self):
        # The other direction — every book that has a notes file
        # should have a floor entry. Catches a new book file landing
        # without a corresponding floor pin.
        data = json.loads(self.FLOOR_PATH.read_text(encoding="utf-8"))
        floors = data["floors"]

        in_floors = set(floors.keys())
        in_corpus = {p.stem for p in self.NOTES_DIR.glob("*.py") if p.stem != "__init__"}
        missing_floor = in_corpus - in_floors
        assert missing_floor == set(), (
            f"books with notes/*.py files but no floor entry: {sorted(missing_floor)}. "
            "Regenerate via `python scripts/update_book_floors.py`."
        )


class TestOmega341StrongsHebrewSourceLoader:
    """ω.34.1 — dedicated tests for ``scripts.core.sources.StrongsHebrew``.

    Mirrors `TestStrongsGreekSourceLoader`. The Hebrew loader was the
    odd one out — every sibling had coverage, this one did not. A
    regression in the Hebrew lexicon's loader would only have been
    caught by integration tests that consume it transitively.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources as src

        cls.src = src

    def test_loader_raises_when_cache_absent(self, tmp_path, monkeypatch):
        nope = tmp_path / "strongs_hebrew.json"
        monkeypatch.setattr(self.src.StrongsHebrew, "PATH", nope)
        try:
            self.src.StrongsHebrew()
        except self.src.SourceMissingError as e:
            assert "fetch_sources.py" in str(e)
            return
        raise AssertionError("expected SourceMissingError")

    def test_loader_reads_synthetic_cache(self, tmp_path, monkeypatch):
        cache = {
            "H1254": {
                "lemma": "בָּרָא",
                "xlit": "bara",
                "pron": "baw-raw'",
                "derivation": "a primitive root",
                "strongs_def": "to create",
                "kjv_def": "Choose, create, dispatch.",
            },
            "H7225": {
                "lemma": "רֵאשִׁית",
                "xlit": "reshith",
                "pron": "ray-sheeth'",
                "derivation": "from H7223",
                "strongs_def": "the first, in place, time, order or rank",
                "kjv_def": "Beginning, chief.",
            },
        }
        cache_path = tmp_path / "strongs_hebrew.json"
        cache_path.write_text(json.dumps(cache), encoding="utf-8")
        monkeypatch.setattr(self.src.StrongsHebrew, "PATH", cache_path)

        h = self.src.StrongsHebrew()
        assert len(h) == 2
        assert "H1254" in h and "H7225" in h
        assert "H99999" not in h

        bara = h.get("H1254")
        assert bara is not None
        assert bara.lemma == "בָּרָא"
        assert bara.xlit == "bara"
        assert "create" in bara.definition.lower()
        assert "Choose" in bara.kjv_def
        assert "Hebrew" in bara.attribution or "Strong" in bara.attribution

    def test_get_returns_none_on_unknown_number(self, tmp_path, monkeypatch):
        cache_path = tmp_path / "strongs_hebrew.json"
        cache_path.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(self.src.StrongsHebrew, "PATH", cache_path)

        h = self.src.StrongsHebrew()
        assert h.get("H9999999") is None

    def test_loader_handles_missing_optional_fields(self, tmp_path, monkeypatch):
        # A real PD dump might be missing some optional fields. The
        # loader must default them to empty strings rather than crash.
        cache = {
            "H1": {
                "lemma": "אָב",
                # no xlit, pron, derivation, kjv_def
            }
        }
        cache_path = tmp_path / "strongs_hebrew.json"
        cache_path.write_text(json.dumps(cache), encoding="utf-8")
        monkeypatch.setattr(self.src.StrongsHebrew, "PATH", cache_path)

        h = self.src.StrongsHebrew()
        entry = h.get("H1")
        assert entry is not None
        assert entry.lemma == "אָב"
        # Missing fields default to empty strings, not None
        assert entry.xlit == ""
        assert entry.pron == ""


class TestOmega341CrossRefDetector:
    """ω.34.1 — dedicated tests for ``scripts.core.detectors.CrossRefDetector``.

    The TSK detector — foundational engine for every χ-cluster
    downstream phase. Pre-ω.34.1 it had no dedicated test class;
    `min_votes=30` and `top_n=3` thresholds were unpinned.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import detectors

        cls.detectors = detectors

    def _make_detector_with_stub_tsk(self, refs_per_verse):
        """Build a CrossRefDetector with a stubbed `tsk()` source."""

        class StubRef:
            def __init__(self, target_book, target_chapter, target_verse, votes, attribution):
                self.target_book = target_book
                self.target_chapter = target_chapter
                self.target_verse = target_verse
                self.votes = votes
                self.attribution = attribution

        class StubTsk:
            def refs_for(self, book, chapter, verse, *, min_votes, top_n):
                key = (book, chapter, verse)
                if key not in refs_per_verse:
                    return []
                refs = [StubRef(*r) for r in refs_per_verse[key] if r[3] >= min_votes]
                return refs[:top_n]

        det = self.detectors.CrossRefDetector.__new__(self.detectors.CrossRefDetector)
        det.tsk = StubTsk()
        det.min_votes = 30
        det.top_n = 3
        det.name = "CrossRefDetector"
        det.kind = "xref-citation"
        return det

    def test_detector_kind_is_xref_citation(self):
        det = self._make_detector_with_stub_tsk({})
        assert det.kind == "xref-citation"
        assert det.name == "CrossRefDetector"

    def test_detector_returns_empty_when_no_refs(self):
        det = self._make_detector_with_stub_tsk({})
        cands = det.detect("gen", 1, 1, "verse text")
        assert cands == []

    def test_detector_emits_one_candidate_per_verse(self):
        # Multiple refs become ONE aggregated candidate (the spec).
        det = self._make_detector_with_stub_tsk(
            {
                ("gen", 1, 1): [
                    ("jhn", 1, 1, 100, "TSK"),
                    ("col", 1, 16, 80, "TSK"),
                    ("heb", 1, 2, 60, "TSK"),
                ]
            }
        )
        cands = det.detect("gen", 1, 1, "")
        assert len(cands) == 1

    def test_detector_filters_below_min_votes(self):
        # Refs below min_votes (30) are dropped by the stub.
        det = self._make_detector_with_stub_tsk(
            {("gen", 1, 1): [("jhn", 1, 1, 10, "TSK")]}  # below 30
        )
        cands = det.detect("gen", 1, 1, "")
        assert cands == []

    def test_detector_caps_at_top_n_3(self):
        # Even with 5 refs above min_votes, only 3 reach the body
        # because top_n=3.
        det = self._make_detector_with_stub_tsk(
            {
                ("gen", 1, 1): [
                    ("a", 1, 1, 50, "TSK"),
                    ("b", 1, 1, 50, "TSK"),
                    ("c", 1, 1, 50, "TSK"),
                    ("d", 1, 1, 50, "TSK"),
                    ("e", 1, 1, 50, "TSK"),
                ]
            }
        )
        cands = det.detect("gen", 1, 1, "")
        assert len(cands) == 1
        body = cands[0].draft_body
        # First 3 books appear; 4th + 5th do not
        assert "A 1:1" in body
        assert "B 1:1" in body
        assert "C 1:1" in body
        assert "D 1:1" not in body
        assert "E 1:1" not in body

    def test_detector_confidence_scales_with_votes(self):
        # confidence = min(0.5 + votes/200, 0.95)
        det_high = self._make_detector_with_stub_tsk({("gen", 1, 1): [("jhn", 1, 1, 200, "TSK")]})
        det_low = self._make_detector_with_stub_tsk({("gen", 1, 1): [("jhn", 1, 1, 30, "TSK")]})
        c_high = det_high.detect("gen", 1, 1, "")[0]
        c_low = det_low.detect("gen", 1, 1, "")[0]
        assert c_high.confidence > c_low.confidence
        assert c_high.confidence <= 0.95  # ceiling

    def test_detector_reviewer_flag_lives_in_reviewer_notes(self):
        # RX Phase 1: the reviewer guidance (rewrite the link list into a
        # thematic note) no longer ships in the reader-facing body; it lives
        # in reviewer_notes=. The body carries only the cross-reference list.
        det = self._make_detector_with_stub_tsk({("gen", 1, 1): [("jhn", 1, 1, 100, "TSK")]})
        c = det.detect("gen", 1, 1, "")[0]
        assert "[Reviewer:" not in c.draft_body
        assert "thematic" in c.reviewer_notes.lower() or "explain" in c.reviewer_notes.lower()

    def test_detector_anchor_links_to_target_verse(self):
        # The body wraps each ref in <a href="#v-<book>-<ch>-<v>"> — the
        # VISIBLE verse anchor (round-7 P3 xref retarget; #vnote- body links
        # are the Kobo teleport class and gate 2b FAILS them in artifacts).
        det = self._make_detector_with_stub_tsk({("gen", 1, 1): [("jhn", 3, 16, 100, "TSK Plus")]})
        c = det.detect("gen", 1, 1, "")[0]
        assert "#v-jhn-3-16" in c.draft_body
        assert "#vnote-jhn-3-16" not in c.draft_body
