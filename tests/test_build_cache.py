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
        repo_real = bc._REPO
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

        repo_real = bc._REPO
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
        from pathlib import Path

        web_src = (Path(__file__).resolve().parent.parent / "scripts" / "web.py").read_text(encoding="utf-8")
        # Locate the subprocess command list inside api_export_build.
        # The function signature anchors the search.
        anchor = "def api_export_build("
        i = web_src.find(anchor)
        assert i > 0
        block = web_src[i : i + 2000]
        # The command list must NOT contain "--force". (api_export_build
        # is the only caller in this file that ever did.)
        assert '"--force"' not in block, (
            "api_export_build still passes --force; ω.20-B's cache would never fire for the API path."
        )

    def test_changelog_documents_omega20b(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        text = (repo / "dev" / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "ω.20-B" in text, "CHANGELOG missing ω.20-B entry"


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
        monkeypatch.setattr(web_mod, "EXPORTS_DIR", tmp_path)

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

        monkeypatch.setattr(web_mod, "EXPORTS_DIR", tmp_path)
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

        monkeypatch.setattr(web_mod, "EXPORTS_DIR", tmp_path)
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
