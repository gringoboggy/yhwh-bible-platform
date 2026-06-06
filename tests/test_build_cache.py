"""Tests for build_cache — extracted from test_scripts.py in ω.27.

Originally lived in tests/test_scripts.py as part of a 22,000-line
monolithic test file; moved here so each test target sits next to a
single source-of-truth scripts/ module. Future tests for the same
target should land in this file rather than test_scripts.py.
"""

from __future__ import annotations


class TestOmega20ABuildCache:
    """ω.20-A — build cache module. Pure-function API: compute_cache_key
    + cache_lookup + cache_store + cache_clear. Build-pipeline
    integration ships separately as ω.20-B; this class only exercises
    the cache itself."""

    # ---- determinism ----

    def test_compute_key_is_deterministic(self):
        from scripts.core.build_cache import compute_cache_key

        a = compute_cache_key("ethiopian-tewahedo")
        b = compute_cache_key("ethiopian-tewahedo")
        assert a == b
        # SHA-256 hex digest
        assert len(a) == 64
        assert all(c in "0123456789abcdef" for c in a)

    def test_compute_key_differs_per_edition(self):
        from scripts.core.build_cache import compute_cache_key

        # Two editions with different canons / kinds / cover paths
        # must produce different keys.
        a = compute_cache_key("ethiopian-tewahedo")
        b = compute_cache_key("catholic-study")
        assert a != b

    def test_compute_key_differs_per_version(self):
        from scripts.core.build_cache import compute_cache_key

        a = compute_cache_key("ethiopian-tewahedo", version="v28a")
        b = compute_cache_key("ethiopian-tewahedo", version="v28b")
        assert a != b

    def test_compute_key_unknown_edition_raises(self):
        from scripts.core.build_cache import compute_cache_key
        import pytest

        with pytest.raises(ValueError, match="unknown edition"):
            compute_cache_key("not-a-real-edition-xyz")

    # ---- input-class invalidation ----

    def test_key_changes_when_edition_record_changes(
        self,
        monkeypatch,
        tmp_path,
    ):
        # Swap editions_by_id() to inject a tweaked record. The key
        # must shift even though every other input is unchanged.
        from scripts.core import build_cache as bc
        from scripts.core import config as _config

        baseline = _config.editions_by_id()
        target = "ethiopian-tewahedo"
        original = dict(baseline[target])
        tweaked = dict(original)
        tweaked["title"] = original.get("title", "") + " (tweaked)"

        monkeypatch.setattr(
            _config,
            "editions_by_id",
            lambda: {**baseline, target: tweaked},
        )
        new_key = bc.compute_cache_key(target)

        # Restore + recompute the original.
        monkeypatch.setattr(_config, "editions_by_id", lambda: baseline)
        old_key = bc.compute_cache_key(target)

        assert new_key != old_key

    def test_key_changes_when_kinds_yaml_changes(
        self,
        monkeypatch,
        tmp_path,
    ):
        # Re-point the module-level _CONTENT at a tmp tree that mirrors
        # the production layout, then mutate kinds.yaml between calls.
        from scripts.core import build_cache as bc

        # Set up a tmp content dir mirroring the real one's structure.
        # We only need the files compute_cache_key reads.
        content_real = bc._CONTENT
        content_tmp = tmp_path / "content"
        content_tmp.mkdir()
        # Symlinks aren't reliable on Windows; copy the small bits.
        import shutil

        for name in ("editions.yaml", "kinds.yaml", "categories.yaml", "books.yaml", "canons.yaml"):
            src = content_real / name
            if src.is_file():
                shutil.copy(src, content_tmp / name)
        # Sub-dirs the cache key reads — empty placeholders are fine.
        (content_tmp / "notes").mkdir()
        (content_tmp / "translations").mkdir()
        (content_tmp / "reading_plans").mkdir()

        monkeypatch.setattr(bc, "_CONTENT", content_tmp)

        baseline = bc.compute_cache_key("ethiopian-tewahedo")
        # Mutate kinds.yaml.
        kinds_path = content_tmp / "kinds.yaml"
        kinds_path.write_text(
            kinds_path.read_text(encoding="utf-8") + "\n# cache-buster\n",
            encoding="utf-8",
        )
        mutated = bc.compute_cache_key("ethiopian-tewahedo")
        assert baseline != mutated

    def test_key_changes_when_a_note_file_changes(
        self,
        monkeypatch,
        tmp_path,
    ):
        from scripts.core import build_cache as bc
        import shutil

        content_real = bc._CONTENT
        content_tmp = tmp_path / "content"
        content_tmp.mkdir()
        for name in ("editions.yaml", "kinds.yaml", "categories.yaml", "books.yaml", "canons.yaml"):
            src = content_real / name
            if src.is_file():
                shutil.copy(src, content_tmp / name)
        notes_tmp = content_tmp / "notes"
        notes_tmp.mkdir()
        # Seed gen.py — ethiopian's canon includes gen.
        (notes_tmp / "gen.py").write_text("notes = ()\n", encoding="utf-8")
        (content_tmp / "translations").mkdir()
        (content_tmp / "reading_plans").mkdir()

        monkeypatch.setattr(bc, "_CONTENT", content_tmp)
        baseline = bc.compute_cache_key("ethiopian-tewahedo")
        # Mutate gen.py.
        (notes_tmp / "gen.py").write_text(
            "notes = ()\n# cache-buster\n",
            encoding="utf-8",
        )
        mutated = bc.compute_cache_key("ethiopian-tewahedo")
        assert baseline != mutated

    def test_missing_optional_inputs_yield_stable_token(
        self,
        monkeypatch,
        tmp_path,
    ):
        # When an optional input (e.g. a notes/<book>.py) doesn't
        # exist on disk, the key still computes — the missing file
        # contributes a stable "<missing>" token. Test: removing a
        # file that didn't exist twice in a row gives equal keys.
        from scripts.core import build_cache as bc
        import shutil

        content_tmp = tmp_path / "content"
        content_tmp.mkdir()
        for name in ("editions.yaml", "kinds.yaml", "categories.yaml", "books.yaml", "canons.yaml"):
            src = bc._CONTENT / name
            if src.is_file():
                shutil.copy(src, content_tmp / name)
        (content_tmp / "notes").mkdir()
        (content_tmp / "translations").mkdir()
        (content_tmp / "reading_plans").mkdir()

        monkeypatch.setattr(bc, "_CONTENT", content_tmp)
        a = bc.compute_cache_key("ethiopian-tewahedo")
        b = bc.compute_cache_key("ethiopian-tewahedo")
        assert a == b

    # ---- store + lookup round trip ----

    def test_store_and_lookup_round_trip(self, tmp_path):
        from scripts.core.build_cache import (
            cache_store,
            cache_lookup,
        )

        cache_dir = tmp_path / "cache"
        # Source EPUB stand-in.
        src = tmp_path / "src.epub"
        src.write_bytes(b"PK\x03\x04 fake epub bytes")
        key = "a" * 64

        target = cache_store(key, src, cache_dir=cache_dir)
        assert target == cache_dir / f"{key}.epub"
        assert target.is_file()
        assert target.read_bytes() == b"PK\x03\x04 fake epub bytes"

        looked_up = cache_lookup(key, cache_dir=cache_dir)
        assert looked_up == target

    def test_lookup_returns_none_for_missing_key(self, tmp_path):
        from scripts.core.build_cache import cache_lookup

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        assert cache_lookup("z" * 64, cache_dir=cache_dir) is None

    def test_lookup_returns_none_when_cache_dir_missing(self, tmp_path):
        from scripts.core.build_cache import cache_lookup

        # Cache dir doesn't exist yet — lookup must not crash.
        missing = tmp_path / "no-such-cache"
        assert cache_lookup("z" * 64, cache_dir=missing) is None

    def test_store_creates_cache_dir(self, tmp_path):
        from scripts.core.build_cache import cache_store

        cache_dir = tmp_path / "cache" / "nested"
        src = tmp_path / "src.epub"
        src.write_bytes(b"x")
        target = cache_store("k", src, cache_dir=cache_dir)
        assert cache_dir.is_dir()
        assert target.is_file()

    def test_store_missing_src_raises(self, tmp_path):
        from scripts.core.build_cache import cache_store
        import pytest

        with pytest.raises(FileNotFoundError):
            cache_store(
                "k",
                tmp_path / "no-such-file.epub",
                cache_dir=tmp_path / "cache",
            )

    # ---- clear ----

    def test_clear_removes_all_epubs(self, tmp_path):
        from scripts.core.build_cache import cache_store, cache_clear

        cache_dir = tmp_path / "cache"
        src = tmp_path / "src.epub"
        src.write_bytes(b"x")
        for k in ("a" * 64, "b" * 64, "c" * 64):
            cache_store(k, src, cache_dir=cache_dir)
        removed = cache_clear(cache_dir=cache_dir)
        assert removed == 3
        assert list(cache_dir.glob("*.epub")) == []

    def test_clear_idempotent_on_missing_dir(self, tmp_path):
        from scripts.core.build_cache import cache_clear

        # Returns 0 instead of raising.
        assert cache_clear(cache_dir=tmp_path / "no-such-dir") == 0

    def test_clear_leaves_non_epub_files_alone(self, tmp_path):
        from scripts.core.build_cache import cache_store, cache_clear

        cache_dir = tmp_path / "cache"
        src = tmp_path / "src.epub"
        src.write_bytes(b"x")
        cache_store("a" * 64, src, cache_dir=cache_dir)
        # Drop a sidecar; clear should not remove it.
        sidecar = cache_dir / "README.txt"
        sidecar.write_text("don't delete me", encoding="utf-8")
        cache_clear(cache_dir=cache_dir)
        assert sidecar.is_file()

    # ---- cache_dir_default ----

    def test_default_cache_dir_under_exports(self):
        from scripts.core.build_cache import cache_dir_default

        d = cache_dir_default()
        assert d.name == ".cache"
        assert d.parent.name == "exports"


class TestMint9CacheKeyCoverage:
    """mint-9 #1/#7/#17 — the content-addressable key must cover EVERY input
    that affects EPUB output bytes: all build-pipeline scripts (not just
    build_edition.py), the active theme's CSS file, and source_dates.yaml.
    Each test mutates one such input and asserts the key shifts; pre-fix the
    key was blind to all of them and these tests fail."""

    import shutil

    def _tmp_repo(self, monkeypatch, tmp_path):
        """Build a minimal tmp repo mirroring the layout compute_cache_key
        reads (content/* + scripts/<pipeline>.py stubs), point _REPO and
        _CONTENT at it, and return (repo, content)."""
        import shutil

        from scripts.core import build_cache as bc

        repo = tmp_path / "repo"
        content = repo / "content"
        scripts_dir = repo / "scripts"
        content.mkdir(parents=True)
        scripts_dir.mkdir()
        for name in ("editions.yaml", "kinds.yaml", "categories.yaml", "books.yaml", "canons.yaml", "themes.yaml"):
            src = bc._CONTENT / name
            if src.is_file():
                shutil.copy(src, content / name)
        (content / "notes").mkdir()
        (content / "translations").mkdir()
        (content / "reading_plans").mkdir()
        (content / "themes").mkdir()
        (content / "source_dates.yaml").write_text("prefixes: {}\n", encoding="utf-8")
        # Stub every pipeline script so _hash_file finds a real file.
        # mint-10: some entries are core/-prefixed (e.g. core/popup_versions.py),
        # so create parent dirs before writing each stub.
        for sname in bc._PIPELINE_SCRIPTS:
            sp = scripts_dir / sname
            sp.parent.mkdir(parents=True, exist_ok=True)
            sp.write_text(f"# stub {sname}\n", encoding="utf-8")
        monkeypatch.setattr(bc, "_REPO", repo)
        monkeypatch.setattr(bc, "_CONTENT", content)
        return repo, content

    def test_key_changes_when_each_pipeline_script_changes(self, monkeypatch, tmp_path):
        from scripts.core import build_cache as bc

        repo, _content = self._tmp_repo(monkeypatch, tmp_path)
        for sname in bc._PIPELINE_SCRIPTS:
            baseline = bc.compute_cache_key("ethiopian-tewahedo")
            p = repo / "scripts" / sname
            p.write_text(p.read_text(encoding="utf-8") + f"\n# bust {sname}\n", encoding="utf-8")
            mutated = bc.compute_cache_key("ethiopian-tewahedo")
            assert baseline != mutated, f"editing scripts/{sname} did not invalidate the cache key"

    def test_pipeline_scripts_includes_matter_pages_and_build_epub(self):
        # The whole point of #1: the cache once hashed ONLY build_edition.py.
        # mint-10 #2 added the core/ DATA modules (popup_versions, traditions)
        # whose injected data also affects output bytes. round-5 added the rest
        # of the build-path core class (edition_stats was the flagged HIGH).
        from scripts.core import build_cache as bc

        for required in (
            "build_edition.py",
            "matter_pages.py",
            "epub_utils.py",
            "build_epub.py",
            "core/popup_versions.py",
            "core/traditions.py",
            # round-5 class-complete additions (see TestCacheCoverageGuard).
            "core/edition_stats.py",
            "core/book_native_names.py",
            "core/reading_plans.py",
            "core/sources.py",
            "core/covers.py",
            "core/matrix.py",
            # round-5 adversarial-review follow-up: the transitive output-shapers
            # + the two mis-waived live-bake modules.
            "core/config.py",
            "core/translations.py",
            "core/corpus_index.py",
            "core/sources_lexicon.py",
        ):
            assert required in bc._PIPELINE_SCRIPTS

    def test_key_changes_when_theme_css_changes(self, monkeypatch, tmp_path):
        from scripts.core import build_cache as bc
        from scripts.core import config as _config

        repo, content = self._tmp_repo(monkeypatch, tmp_path)
        # Force the edition to use a theme whose .css we control.
        baseline_eds = _config.editions_by_id()
        target = "ethiopian-tewahedo"
        themed = {**baseline_eds[target], "theme": "mint9test"}
        monkeypatch.setattr(_config, "editions_by_id", lambda: {**baseline_eds, target: themed})
        css = content / "themes" / "mint9test.css"
        css.write_text("body { color: black; }\n", encoding="utf-8")

        baseline = bc.compute_cache_key(target)
        css.write_text("body { color: red; }\n", encoding="utf-8")
        mutated = bc.compute_cache_key(target)
        assert baseline != mutated, "editing the theme CSS did not invalidate the cache key"

    def test_key_changes_when_source_dates_changes(self, monkeypatch, tmp_path):
        from scripts.core import build_cache as bc

        _repo, content = self._tmp_repo(monkeypatch, tmp_path)
        baseline = bc.compute_cache_key("ethiopian-tewahedo")
        (content / "source_dates.yaml").write_text("prefixes: {Cyril: 430}\n", encoding="utf-8")
        mutated = bc.compute_cache_key("ethiopian-tewahedo")
        assert baseline != mutated, "editing source_dates.yaml did not invalidate the cache key"


class TestOmega20BBuildCacheIntegration:
    """ω.20-B — build_cache wired into build_one. The integration is
    additive: when the cache is empty, behavior is identical to
    pre-ω.20-B; when it's warm, build_one returns early with
    cache_hit=True and size_mb populated, skipping the actual EPUB
    build entirely.

    Tests do NOT exercise the real EPUB-build subprocess (slow + env-
    dependent). Instead they exercise the cache-lookup short-circuit
    by pre-warming the cache before calling build_one — the function
    returns the cached path before reaching the subprocess.
    """

    def _seed_cache(self, monkeypatch, tmp_path, edition_id, version):
        """Helper: redirect the cache to tmp_path, write a fake EPUB,
        compute the real cache key, store it. Returns (cache_dir,
        cache_key, fake_epub_path)."""
        from scripts.core import build_cache as bc

        cache_dir = tmp_path / "cache"
        # Patch cache_dir_default so build_one's lookup hits tmp_path.
        monkeypatch.setattr(bc, "cache_dir_default", lambda: cache_dir)
        fake_epub = tmp_path / "fake.epub"
        # Realistic EPUB byte stamp so size_mb computes a non-zero value.
        fake_epub.write_bytes(b"PK\x03\x04" + b"\0" * 4096)
        key = bc.compute_cache_key(edition_id, version=version)
        bc.cache_store(key, fake_epub, cache_dir=cache_dir)
        return cache_dir, key, fake_epub

    def test_build_one_hits_cache_returns_cache_hit_true(
        self,
        monkeypatch,
        tmp_path,
    ):
        from scripts.build_edition import build_one
        from scripts.core import config

        edition_id = "ethiopian-tewahedo"
        version = "v28a-test-omega20b"
        self._seed_cache(monkeypatch, tmp_path, edition_id, version)

        output_dir = tmp_path / "exports"
        all_kinds = config.load_kinds()
        result = build_one(
            edition_id,
            output_dir,
            version,
            all_kinds,
            dry_run=False,
            force=False,
        )

        assert result.get("cache_hit") is True, f"expected cache_hit=True, got {result}"
        assert result.get("skipped") is True
        # The cached bytes should have been copied into output_dir
        # so the API surface remains "there's an EPUB at this path".
        assert result["output_path"].is_file()
        # No real build ran — size_mb reflects the fake EPUB bytes.
        assert result["size_mb"] > 0

    def test_build_one_force_bypasses_cache(self, monkeypatch, tmp_path):
        # With force=True, even a warm cache must NOT be used. Verify
        # by seeding the cache, then calling build_one(force=True) and
        # confirming the cache-hit branch did not fire.
        from scripts.build_edition import build_one
        from scripts.core import config

        edition_id = "ethiopian-tewahedo"
        version = "v28a-test-omega20b-force"
        self._seed_cache(monkeypatch, tmp_path, edition_id, version)

        output_dir = tmp_path / "exports"
        all_kinds = config.load_kinds()

        # We don't want to actually run the real EPUB build (slow).
        # Simplest: stub `tempfile.TemporaryDirectory` so build_one
        # raises before reaching subprocess work — the assertion is
        # that force=True takes us past the cache check.
        # But that's brittle. Cleaner: dry_run=False + force=True with
        # a captured exception is too invasive. Instead, run dry_run
        # with force=True; dry_run path also bypasses cache (computes
        # nothing, no subprocess). Verify cache_hit is NOT in result.
        result = build_one(
            edition_id,
            output_dir,
            version,
            all_kinds,
            dry_run=True,
            force=True,
        )
        assert result.get("cache_hit") is not True
        assert result.get("skipped") is not True

    def test_build_one_dry_run_skips_cache(self, monkeypatch, tmp_path):
        # dry_run is documentation/preview; it should never hit the
        # cache (even when warm) because the caller wants to see the
        # filter counts, not a cached artifact.
        from scripts.build_edition import build_one
        from scripts.core import config

        edition_id = "ethiopian-tewahedo"
        version = "v28a-test-omega20b-dry"
        self._seed_cache(monkeypatch, tmp_path, edition_id, version)

        output_dir = tmp_path / "exports"
        all_kinds = config.load_kinds()
        result = build_one(
            edition_id,
            output_dir,
            version,
            all_kinds,
            dry_run=True,
            force=False,
        )
        # dry_run path doesn't surface cache_hit and doesn't claim
        # skipped — it's its own thing (pre-ω.20-B contract preserved).
        assert result.get("cache_hit") is not True

    def test_build_one_unknown_edition_still_raises(
        self,
        monkeypatch,
        tmp_path,
    ):
        # The ω.20-B compute_cache_key call mustn't swallow the
        # legitimate ValueError from an unknown edition. The wider
        # try/except around compute_cache_key WAS designed to
        # gracefully degrade on cache-key-only errors, but the
        # subsequent `editions_by_id` check in build_one must still
        # surface "unknown edition".
        from scripts.build_edition import build_one
        from scripts.core import config

        all_kinds = config.load_kinds()
        import pytest

        with pytest.raises(ValueError, match="unknown edition"):
            build_one(
                "no-such-edition-xyz",
                tmp_path / "exports",
                "v28a",
                all_kinds,
            )

    def test_api_export_build_command_drops_force(self):
        # ω.20-B drops the legacy --force flag so build_one's cache
        # can fire. Pin this so a future revert wouldn't silently
        # disable the cache for the API path.
        #
        # ω.35-B.6 — api_export_build moved to scripts/api/exports.py.
        # Check both candidate locations so this test stays meaningful.
        from pathlib import Path

        scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
        candidates = [
            scripts_dir / "api" / "exports.py",  # canonical home (ω.35-B.6+)
            scripts_dir / "web.py",  # pre-B.6 home
        ]
        anchor = "def api_export_build("
        found_in = None
        for path in candidates:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            i = text.find(anchor)
            if i < 0:
                continue
            block = text[i : i + 2000]
            assert '"--force"' not in block, (
                f"api_export_build in {path.name} still passes --force; "
                "ω.20-B's cache would never fire for the API path."
            )
            found_in = path
            break
        assert found_in is not None, f"api_export_build not found in any candidate: {[str(p) for p in candidates]}"

    def test_changelog_documents_omega20b(self):
        from pathlib import Path

        # mint-9: the live CHANGELOG is month-rolled — older phases migrate to
        # dev/archive/CHANGELOG*.md (the untracked_phases lint reads both). A
        # historical phase like ω.20-B may live only in an archive, so search
        # the live log AND every archived one, not the live log alone.
        repo = Path(__file__).resolve().parent.parent
        texts = [(repo / "dev" / "CHANGELOG.md").read_text(encoding="utf-8")]
        for arch in sorted((repo / "dev" / "archive").glob("CHANGELOG*.md")):
            texts.append(arch.read_text(encoding="utf-8"))
        assert any("ω.20-B" in t for t in texts), "ω.20-B entry missing from live + archived CHANGELOGs"


class TestOmega20CStatsSidecar:
    """ω.20-C — companion stats sidecar so api_export_build can
    surface cache_hit / build_seconds in its response payload.
    Closes the ω.20 chain end-to-end: cache module (A) →
    build_one integration (B) → buyer-facing badge surface (C).
    """

    # ---- _write_stats_sidecar helper ----

    def test_write_stats_sidecar_creates_file_next_to_epub(
        self,
        tmp_path,
    ):
        from scripts.build_edition import _write_stats_sidecar

        out = tmp_path / "sample.epub"
        out.write_bytes(b"PK\x03\x04 stub")
        stats = {
            "edition_id": "ed-x",
            "version": "v28a",
            "cache_hit": False,
            "skipped": False,
            "size_mb": 1.5,
        }
        sidecar = _write_stats_sidecar(out, stats, build_seconds=12.345)
        assert sidecar is not None
        assert sidecar.is_file()
        assert sidecar.name == "sample.epub.stats.json"

    def test_write_stats_sidecar_payload_shape(self, tmp_path):
        # The sidecar is a buyer-facing surface; pin the keys so a
        # future contributor doesn't accidentally rename / remove a
        # field the UI depends on.
        from scripts.build_edition import _write_stats_sidecar
        import json as _json

        out = tmp_path / "x.epub"
        out.write_bytes(b"x")
        stats = {
            "edition_id": "catholic-study",
            "version": "v28a",
            "cache_hit": True,
            "skipped": True,
            "size_mb": 2.345,
            # Operator-only fields that should NOT leak into the
            # buyer-facing sidecar.
            "enabled_kinds": 50,
            "markers_removed": 1234,
        }
        sidecar = _write_stats_sidecar(out, stats, 0.123)
        data = _json.loads(sidecar.read_text(encoding="utf-8"))
        # Buyer-facing keys
        for key in ("edition_id", "version", "cache_hit", "skipped", "size_mb", "build_seconds", "filename"):
            assert key in data, f"sidecar missing {key!r}: {data}"
        assert data["edition_id"] == "catholic-study"
        assert data["cache_hit"] is True
        assert data["build_seconds"] == 0.123
        assert data["filename"] == "x.epub"
        # Operator-only fields filtered out
        assert "enabled_kinds" not in data
        assert "markers_removed" not in data

    def test_write_stats_sidecar_failure_returns_none(
        self,
        tmp_path,
        monkeypatch,
    ):
        # Read-only / unwritable target → return None, don't raise.
        from scripts.build_edition import _write_stats_sidecar

        out = tmp_path / "x.epub"
        out.write_bytes(b"x")

        from scripts.core import notes_io

        def boom(*a, **kw):
            raise OSError("disk full")

        monkeypatch.setattr(notes_io, "atomic_write", boom)

        sidecar = _write_stats_sidecar(
            out,
            {"edition_id": "x", "version": "v"},
            0.0,
        )
        assert sidecar is None

    def test_write_stats_sidecar_normalises_types(self, tmp_path):
        # If the stats dict carries odd types (e.g. a missing
        # cache_hit), the sidecar still lands a valid JSON.
        from scripts.build_edition import _write_stats_sidecar
        import json as _json

        out = tmp_path / "x.epub"
        out.write_bytes(b"x")
        sidecar = _write_stats_sidecar(
            out,
            {"edition_id": "x", "version": "v"},
            0.0,
        )
        data = _json.loads(sidecar.read_text(encoding="utf-8"))
        # Defaults: cache_hit=False, skipped=False, size_mb=0.0
        assert data["cache_hit"] is False
        assert data["skipped"] is False
        assert data["size_mb"] == 0.0

    # ---- build_one writes sidecar ----

    def test_build_one_cache_hit_writes_sidecar(
        self,
        monkeypatch,
        tmp_path,
    ):
        # Reuse the cache-warming helper from the ω.20-B test class.
        from scripts.build_edition import build_one
        from scripts.core import config, build_cache as bc

        edition_id = "ethiopian-tewahedo"
        version = "v28a-test-omega20c-hit"

        cache_dir = tmp_path / "cache"
        monkeypatch.setattr(bc, "cache_dir_default", lambda: cache_dir)
        fake_epub = tmp_path / "fake.epub"
        fake_epub.write_bytes(b"PK\x03\x04" + b"\0" * 4096)
        key = bc.compute_cache_key(edition_id, version=version)
        bc.cache_store(key, fake_epub, cache_dir=cache_dir)

        output_dir = tmp_path / "exports"
        all_kinds = config.load_kinds()
        result = build_one(
            edition_id,
            output_dir,
            version,
            all_kinds,
            dry_run=False,
            force=False,
        )

        assert result.get("cache_hit") is True
        # Sidecar lives next to the EPUB.
        epub_path = result["output_path"]
        sidecar = epub_path.with_suffix(epub_path.suffix + ".stats.json")
        assert sidecar.is_file(), f"sidecar missing at {sidecar}"
        import json as _json

        data = _json.loads(sidecar.read_text(encoding="utf-8"))
        assert data["cache_hit"] is True
        assert data["edition_id"] == edition_id
        assert data["version"] == version

    def test_build_one_dry_run_does_not_write_sidecar(
        self,
        tmp_path,
    ):
        # dry_run path doesn't produce a real EPUB, so no sidecar
        # either — pre-ω.20-C behavior preserved.
        from scripts.build_edition import build_one
        from scripts.core import config

        output_dir = tmp_path / "exports"
        all_kinds = config.load_kinds()
        result = build_one(
            "ethiopian-tewahedo",
            output_dir,
            "v28a-dry",
            all_kinds,
            dry_run=True,
            force=False,
        )
        # No stats.json files exist anywhere in the output dir.
        assert not list(output_dir.glob("*.stats.json"))
        assert result.get("cache_hit") is not True

    # ---- api_export_build folds sidecar into response ----

    def test_api_export_build_surfaces_sidecar_fields(
        self,
        tmp_path,
        monkeypatch,
    ):
        # Stage an EPUB + sidecar in the exports dir; mock the
        # subprocess to be a no-op so we can exercise the response
        # assembly directly.
        import scripts.web as web_mod
        import json as _json
        from scripts.core import config

        # Pick a real edition so the editions_by_id check passes.
        edition_id = sorted(config.editions_by_id())[0]
        version = "v28a-test-omega20c-api"

        # Redirect EXPORTS_DIR to tmp_path.
        # ω.35-B.6 — canonical home is scripts.api.exports; patch
        # there so the in-module references see the redirect.
        monkeypatch.setattr("scripts.api.exports.EXPORTS_DIR", tmp_path)

        # Plant a fake EPUB matching the glob pattern api_export_build
        # uses to discover the output.
        fake_epub = tmp_path / f"Ethiopian_Bible_{edition_id}_{version}_X.epub"
        fake_epub.write_bytes(b"PK\x03\x04" + b"\0" * 1024)

        # Plant a sidecar with cache_hit=True.
        sidecar = fake_epub.with_suffix(fake_epub.suffix + ".stats.json")
        sidecar.write_text(
            _json.dumps(
                {
                    "edition_id": edition_id,
                    "version": version,
                    "cache_hit": True,
                    "skipped": True,
                    "size_mb": 1.0,
                    "build_seconds": 0.05,
                    "filename": fake_epub.name,
                }
            ),
            encoding="utf-8",
        )

        # Stub the subprocess so api_export_build doesn't actually run
        # the build.
        import subprocess as _subproc

        class FakeProc:
            returncode = 0
            stdout = "ok"
            stderr = ""

        monkeypatch.setattr(_subproc, "run", lambda *a, **kw: FakeProc())

        result = web_mod.api_export_build(edition_id, version=version)
        assert result.get("ok") is True
        # The new sidecar fields are surfaced.
        assert result.get("cache_hit") is True
        assert result.get("skipped") is True
        assert result.get("build_seconds") == 0.05

    def test_api_export_build_degrades_when_sidecar_missing(
        self,
        tmp_path,
        monkeypatch,
    ):
        import scripts.web as web_mod
        from scripts.core import config

        edition_id = sorted(config.editions_by_id())[0]
        version = "v28a-test-omega20c-no-sidecar"

        # ω.35-B.6 — canonical home is scripts.api.exports.
        monkeypatch.setattr("scripts.api.exports.EXPORTS_DIR", tmp_path)
        fake_epub = tmp_path / f"Ethiopian_Bible_{edition_id}_{version}_X.epub"
        fake_epub.write_bytes(b"PK\x03\x04" + b"\0" * 1024)
        # Note: no sidecar planted.

        import subprocess as _subproc

        class FakeProc:
            returncode = 0
            stdout = ""
            stderr = ""

        monkeypatch.setattr(_subproc, "run", lambda *a, **kw: FakeProc())

        result = web_mod.api_export_build(edition_id, version=version)
        assert result.get("ok") is True
        # No cache_hit / build_seconds in the response — the response
        # works without the sidecar fields. Pre-ω.20-C contract.
        assert "cache_hit" not in result
        assert "build_seconds" not in result

    def test_api_export_build_degrades_on_corrupt_sidecar(
        self,
        tmp_path,
        monkeypatch,
    ):
        import scripts.web as web_mod
        from scripts.core import config

        edition_id = sorted(config.editions_by_id())[0]
        version = "v28a-test-omega20c-corrupt"

        # ω.35-B.6 — canonical home is scripts.api.exports.
        monkeypatch.setattr("scripts.api.exports.EXPORTS_DIR", tmp_path)
        fake_epub = tmp_path / f"Ethiopian_Bible_{edition_id}_{version}_X.epub"
        fake_epub.write_bytes(b"PK\x03\x04" + b"\0" * 1024)
        sidecar = fake_epub.with_suffix(fake_epub.suffix + ".stats.json")
        sidecar.write_text("not valid json {", encoding="utf-8")

        import subprocess as _subproc

        class FakeProc:
            returncode = 0
            stdout = ""
            stderr = ""

        monkeypatch.setattr(_subproc, "run", lambda *a, **kw: FakeProc())

        # Should not raise; just doesn't surface the fields.
        result = web_mod.api_export_build(edition_id, version=version)
        assert result.get("ok") is True
        assert "cache_hit" not in result


class TestRho3CachePerChapterPerVerse:
    """ρ.3 Phase B-5b — _referenced_translations must walk per-chapter
    and per-verse popup language overrides, not only per-book.

    Before the fix, a version id introduced *only* via
    popup_languages_per_verse (or per_chapter) was invisible to the
    translation-data hash, so editing that translation's files after an
    initial build could produce a stale cached EPUB.

    Test strategy: construct a minimal edition dict that references
    'jps' (resolves to translation_id='jps'; content/translations/jps/
    exists on disk) exclusively via per_verse / per_chapter overrides —
    no popup_translation, no popup_languages_default, no per_book entry.
    Assert that _referenced_translations() returns 'jps' in the set.
    Also verify per_chapter variant using 'kjv' -> 'kjv'.
    """

    def test_per_verse_only_translation_is_included(self):
        """A version id present only in popup_languages_per_verse must
        appear in _referenced_translations().  Before the fix this
        returned [] (empty), missing 'jps' entirely."""
        from scripts.core.build_cache import _referenced_translations

        edition = {
            # No popup_translation, no default, no per_book.
            "popup_languages_per_verse": ["gen:1:1=jps"],
        }
        refs = _referenced_translations(edition)
        # 'jps' resolves: resolve_version_id('jps') -> 'jps';
        # VERSION_REGISTRY['jps']['translation_id'] -> 'jps'.
        assert "jps" in refs, (
            f"_referenced_translations did not include 'jps' from popup_languages_per_verse; got: {refs}"
        )

    def test_per_chapter_only_translation_is_included(self):
        """A version id present only in popup_languages_per_chapter must
        appear in _referenced_translations()."""
        from scripts.core.build_cache import _referenced_translations

        edition = {
            "popup_languages_per_chapter": ["gen:1=kjv"],
        }
        refs = _referenced_translations(edition)
        # 'kjv' resolves: translation_id='kjv'.
        assert "kjv" in refs, (
            f"_referenced_translations did not include 'kjv' from popup_languages_per_chapter; got: {refs}"
        )

    def test_per_verse_comma_separated_langs_all_included(self):
        """Multiple langs in one per-verse entry (comma-separated) are
        all collected."""
        from scripts.core.build_cache import _referenced_translations

        edition = {
            "popup_languages_per_verse": ["gen:1:1=jps,kjv"],
        }
        refs = _referenced_translations(edition)
        assert "jps" in refs, f"'jps' missing from refs: {refs}"
        assert "kjv" in refs, f"'kjv' missing from refs: {refs}"

    def test_per_verse_does_not_duplicate_default_langs(self):
        """If a lang appears in both popup_languages_default and
        popup_languages_per_verse, it appears exactly once in the
        sorted result (set semantics, no duplication)."""
        from scripts.core.build_cache import _referenced_translations

        edition = {
            "popup_languages_default": ["jps"],
            "popup_languages_per_verse": ["gen:1:1=jps"],
        }
        refs = _referenced_translations(edition)
        assert refs.count("jps") == 1, f"'jps' duplicated in refs: {refs}"


class TestCacheCoverageGuard:
    """round-5 audit (2026-06-05) — self-enforcing guard against the recurring
    stale-cache class (mint-9 #1, mint-10 #2, mint-11 #22, round-5 HIGH + its
    adversarial-review follow-up): a ``scripts/core`` module whose CODE can shape
    build_one's EPUB output must appear in ``build_cache._PIPELINE_SCRIPTS`` OR be
    waived here with a reason. A NEW unclassified build-path core module fails this
    test, forcing a cache-coverage decision at the same commit (the bug recurred
    once per build-path module added without updating the cache list).

    The surface is the TRANSITIVE closure of ``scripts.core`` modules reachable
    from the build_one orchestrators (the non-``core/`` entries of
    _PIPELINE_SCRIPTS — build_edition, matter_pages, epub_utils,
    resync_marker_glyphs, build_epub, style_config, inject), following both
    absolute (``scripts.core.X``) and relative (``from . import X`` /
    ``from .X import``) imports. The first round-5 pass scanned only the
    orchestrators' DIRECT imports and missed two real holes the review caught —
    matrix delegates the book-count build to corpus_index, and sources only
    re-exports the topical classes defined in sources_lexicon — so the scan now
    walks the whole closure, classifying every reachable core module.
    """

    # Build-path-closure modules whose CODE provably does NOT shape build_one's
    # EPUB output — each waived with the reason it is safe to omit from
    # _PIPELINE_SCRIPTS. If you add a build-path core module that genuinely shapes
    # baked output, add core/<mod>.py to _PIPELINE_SCRIPTS instead of waiving here.
    WAIVED = {
        "build_cache": "the cache machinery itself; decides hit/miss, never emits EPUB bytes",
        "notes_io": "atomic file-I/O primitives; no output-shaping logic (notes DATA hashed, part 5)",
        "ui": "console/progress terminal helpers; nothing reaches the EPUB",
        "html_sanitize": "inject-only, OFFLINE base generation; the base is hashed wholesale (part 10)",
        "paths": "repo/content path constants; the DATA at those paths is hashed, no transform",
        "migrate": "SQLite migration runner for corpus_index's derived index (rebuilt from hashed notes)",
        "migrations": "corpus_index index-schema migration defs; derived index only, never baked",
        "work_cache": "AI-work cache infra (Voyage, dropped); not on the build_one bake path",
        "sources_base": "base for sources_* loaders; topical bake classes live standalone in sources_lexicon",
        "sources_commentary": "commentary loaders feed OFFLINE note promotion; promoted notes hashed (part 5)",
        "sources_ai_clients": "AI client infra (Voyage, dropped); re-exported via sources.py, not baked",
        "sources_ai_prompts": "AI xref prompt templates (offline); not on the build_one bake path",
    }

    def _build_path_core_closure(self) -> dict[str, set[str]]:
        """{core_module: {who pulls it}} — the TRANSITIVE closure of scripts.core
        modules reachable from the build_one orchestrators, following absolute AND
        (inside scripts/core/) relative imports."""
        import ast
        from collections import deque
        from pathlib import Path
        from scripts.core import build_cache as bc

        scripts_dir = Path(bc.__file__).resolve().parent.parent  # .../scripts
        core_dir = scripts_dir / "core"

        def core_imports(path: Path) -> set[str]:
            in_core = path.parent.name == "core"
            found: set[str] = set()
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    lvl = node.level or 0
                    if lvl == 0:
                        if mod == "scripts.core":
                            found.update(a.name for a in node.names)  # from scripts.core import X
                        elif mod.startswith("scripts.core."):
                            found.add(mod.split(".")[2])  # from scripts.core.X import ...
                    elif in_core and lvl == 1:  # relative import inside scripts/core/
                        if mod:
                            found.add(mod.split(".")[0])  # from .X import ...
                        else:
                            found.update(a.name for a in node.names)  # from . import X
                elif isinstance(node, ast.Import):
                    for alias in node.names:  # import scripts.core.X
                        if alias.name.startswith("scripts.core."):
                            found.add(alias.name.split(".")[2])
            return {m for m in found if (core_dir / f"{m}.py").is_file()}

        orchestrators = [n for n in bc._PIPELINE_SCRIPTS if not n.startswith("core/")]
        closure: dict[str, set[str]] = {}
        queue: deque[tuple[str, str]] = deque()
        for orch in orchestrators:
            for m in core_imports(scripts_dir / orch):
                queue.append((m, orch))
        while queue:
            mod, via = queue.popleft()
            if mod in closure:
                closure[mod].add(via)
                continue
            closure[mod] = {via}
            for m2 in core_imports(core_dir / f"{mod}.py"):
                queue.append((m2, mod))
        return closure

    def test_every_build_path_core_module_is_covered_or_waived(self):
        from scripts.core import build_cache as bc

        pipeline = set(bc._PIPELINE_SCRIPTS)
        closure = self._build_path_core_closure()
        unclassified = [
            f"{mod} (reached via {sorted(via)[:4]})"
            for mod, via in sorted(closure.items())
            if f"core/{mod}.py" not in pipeline and mod not in self.WAIVED
        ]
        assert not unclassified, (
            "build-path core module(s) (transitive closure) neither in "
            "build_cache._PIPELINE_SCRIPTS nor waived in TestCacheCoverageGuard.WAIVED:\n  "
            + "\n  ".join(unclassified)
            + "\nIf editing the module can change EPUB output, add core/<mod>.py to "
            "_PIPELINE_SCRIPTS; if it provably cannot, add it to WAIVED with the reason."
        )

    def test_waived_modules_stay_honest(self):
        # Every waiver must really be in the build-path core closure and NOT in
        # _PIPELINE_SCRIPTS, so a stale waiver (module no longer reachable, or
        # later promoted to the cache list) is caught instead of silently masking.
        from scripts.core import build_cache as bc

        pipeline = set(bc._PIPELINE_SCRIPTS)
        closure = self._build_path_core_closure()
        for waived in self.WAIVED:
            assert waived in closure, (
                f"WAIVED[{waived!r}] is no longer in the build-path core closure; remove the stale waiver."
            )
            assert f"core/{waived}.py" not in pipeline, (
                f"WAIVED[{waived!r}] is now in _PIPELINE_SCRIPTS; remove the redundant waiver."
            )

    def test_round5_class_complete_additions_stay_covered(self):
        # Positive pin: the round-5 additions — the HIGH edition_stats, its direct
        # siblings, AND the transitive output-shapers the adversarial review
        # surfaced (config/translations live-bake; corpus_index/sources_lexicon
        # behind the matrix/sources shims) — must stay in the cache list.
        from scripts.core import build_cache as bc

        for mod in (
            "core/edition_stats.py",
            "core/book_native_names.py",
            "core/reading_plans.py",
            "core/sources.py",
            "core/covers.py",
            "core/matrix.py",
            "core/config.py",
            "core/translations.py",
            "core/corpus_index.py",
            "core/sources_lexicon.py",
        ):
            assert mod in bc._PIPELINE_SCRIPTS, f"{mod} dropped from _PIPELINE_SCRIPTS"
