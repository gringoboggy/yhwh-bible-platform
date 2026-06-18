"""Matrix M1 blocker #1 — the build-time ``--target-reader`` override.

The format-matrix spec (docs/superpowers/specs/2026-06-10-website-format-
matrix-design.md §2) forbids mutating editions.yaml, so non-default reader
targets need a build-time override: a ``--target-reader`` CLI flag feeding
the ONE resolver (``resolve_target_reader``), plumbed through ``build_one``.
The Mac spec review (docs/superpowers/notes/2026-06-10-matrix-spec-review.md
blocker #1 + corollary) requires the RESOLVED target folded into
``compute_cache_key`` — otherwise an override build is invisible to the
content cache and a wrong-format artifact gets served. The same class bug
exists in the legacy mtime shortcut (``is_output_current``), fixed here by
target-aware artifact naming + candidate filtering.
"""

from __future__ import annotations

import json
from pathlib import Path


class TestApplyTargetOverride:
    """The pure fold helper — one chokepoint build_one uses so every
    downstream consumer (resolve_target_reader / is_kindle_target /
    patch_opf stamp / kindle passes) sees the override."""

    def test_none_override_returns_record_unchanged(self):
        from scripts.build_edition import apply_target_override

        edition = {"id": "x", "target_reader": "eink"}
        out = apply_target_override(edition, None)
        assert out == edition

    def test_valid_override_folds_into_copy_without_mutating_original(self):
        from scripts.build_edition import apply_target_override

        edition = {"id": "x"}
        out = apply_target_override(edition, "kindle")
        assert out["target_reader"] == "kindle"
        assert "target_reader" not in edition  # original untouched

    def test_invalid_override_raises_value_error(self):
        import pytest

        from scripts.build_edition import apply_target_override

        with pytest.raises(ValueError, match="target_reader"):
            apply_target_override({"id": "x"}, "papyrus")

    def test_standalone_edition_rejects_override(self):
        # The standalone build path (build_standalone) does not consume
        # target_reader; silently ignoring an explicit override would be a
        # silent failure, so it must raise instead.
        import pytest

        from scripts.build_edition import apply_target_override

        with pytest.raises(ValueError, match="standalone"):
            apply_target_override({"id": "x", "standalone": True}, "eink")


class TestCacheKeyTargetFold:
    """Review blocker #1 corollary: compute_cache_key must fold the
    RESOLVED reader target so override builds key correctly."""

    def test_override_changes_key_off_the_stored_default(self):
        from scripts.core.build_cache import compute_cache_key

        base = compute_cache_key("catholic-study")
        eink = compute_cache_key("catholic-study", target_reader="eink")
        assert base != eink

    def test_override_matching_resolution_yields_identical_key(self):
        # catholic-study stores no target_reader => resolves "everywhere".
        # An explicit "everywhere" override produces byte-identical output,
        # so it MUST hit the same cache entry (resolved-fold semantics —
        # the key hashes the resolved target, not the raw override).
        from scripts.core.build_cache import compute_cache_key

        base = compute_cache_key("catholic-study")
        explicit = compute_cache_key("catholic-study", target_reader="everywhere")
        assert base == explicit

    def test_distinct_targets_yield_pairwise_distinct_keys(self):
        from scripts.core.build_cache import compute_cache_key

        keys = [compute_cache_key("catholic-study", target_reader=t) for t in ("eink", "kindle", "tablet")]
        assert len(set(keys)) == 3

    def test_invalid_target_raises_value_error(self):
        import pytest

        from scripts.core.build_cache import compute_cache_key

        with pytest.raises(ValueError, match="target_reader"):
            compute_cache_key("catholic-study", target_reader="papyrus")


class TestBuildOneTargetOverridePlumbing:
    """build_one must (a) pass the override to compute_cache_key, (b) name
    the artifact with the target token so the mtime shortcut can tell
    formats apart, (c) surface the resolved target in stats. Exercised via
    a stubbed cache hit so no real build runs."""

    def _run_cached_build(self, tmp_path, monkeypatch, *, target_reader):
        from scripts import build_edition as be
        from scripts.core import build_cache as bc
        from scripts.core import config

        captured: dict = {}

        def fake_compute(edition_id, *, version="v28a", target_reader=None):
            captured["edition_id"] = edition_id
            captured["version"] = version
            captured["target_reader"] = target_reader
            return "f" * 64

        fake_epub = tmp_path / "cached.epub"
        fake_epub.write_bytes(b"fake-epub-bytes")
        monkeypatch.setattr(bc, "compute_cache_key", fake_compute)
        monkeypatch.setattr(bc, "cache_lookup", lambda key, **kw: fake_epub)

        out_dir = tmp_path / "out"
        stats = be.build_one(
            "catholic-study",
            out_dir,
            "vTEST",
            config.load_kinds(),
            False,
            False,
            target_reader=target_reader,
        )
        return stats, captured

    def test_override_reaches_cache_key_and_artifact_name(self, tmp_path, monkeypatch):
        stats, captured = self._run_cached_build(tmp_path, monkeypatch, target_reader="eink")
        assert captured["target_reader"] == "eink"
        assert stats["target_reader"] == "eink"
        name = Path(stats["output_path"]).name
        assert name.startswith("Ethiopian_Bible_catholic-study_vTEST_eink_")
        # round-trip: the artifact build_one just wrote must be found by the
        # mtime shortcut under the SAME target — and never by a plain lookup
        # (keeps the two naming sites coupled).
        from scripts.build_edition import is_output_current

        out_dir = Path(stats["output_path"]).parent
        assert is_output_current(out_dir, "catholic-study", "vTEST", target_reader="eink") == Path(stats["output_path"])
        assert is_output_current(out_dir, "catholic-study", "vTEST") is None

    def test_no_override_keeps_legacy_name_and_passes_none(self, tmp_path, monkeypatch):
        stats, captured = self._run_cached_build(tmp_path, monkeypatch, target_reader=None)
        assert captured["target_reader"] is None
        assert stats["target_reader"] == "everywhere"
        name = Path(stats["output_path"]).name
        assert name.startswith("Ethiopian_Bible_catholic-study_vTEST_")
        # the segment after the version must be the timestamp, not a target token
        rest = name[len("Ethiopian_Bible_catholic-study_vTEST_") :]
        from scripts.build_edition import TARGET_READERS

        assert rest.split("_", 1)[0] not in TARGET_READERS

    def test_standalone_edition_with_override_raises(self, tmp_path):
        import pytest

        from scripts import build_edition as be
        from scripts.core import config

        eds = config.editions_by_id()
        standalone_ids = [eid for eid, e in eds.items() if e.get("standalone")]
        assert standalone_ids, "expected at least one standalone edition"
        with pytest.raises(ValueError, match="standalone"):
            be.build_one(
                standalone_ids[0],
                tmp_path,
                "vTEST",
                config.load_kinds(),
                True,
                False,
                target_reader="eink",
            )


class TestIsOutputCurrentTargetAware:
    """The legacy mtime shortcut must never serve a wrong-format artifact:
    plain lookups skip target-named files; target lookups match only their
    own token."""

    def _touch(self, directory: Path, name: str) -> Path:
        p = directory / name
        p.write_bytes(b"x")
        return p

    def test_plain_lookup_ignores_override_named_artifacts(self, tmp_path):
        from scripts.build_edition import is_output_current

        self._touch(tmp_path, "Ethiopian_Bible_catholic-study_vT_eink_2099-01-01T000000Z.epub")
        assert is_output_current(tmp_path, "catholic-study", "vT") is None

    def test_target_lookup_matches_only_its_own_token(self, tmp_path):
        from scripts.build_edition import is_output_current

        eink = self._touch(tmp_path, "Ethiopian_Bible_catholic-study_vT_eink_2099-01-01T000000Z.epub")
        self._touch(tmp_path, "Ethiopian_Bible_catholic-study_vT_kindle_2099-01-01T000000Z.epub")
        self._touch(tmp_path, "Ethiopian_Bible_catholic-study_vT_2099-01-01T000000Z.epub")
        found = is_output_current(tmp_path, "catholic-study", "vT", target_reader="eink")
        # may be None if repo sources are newer than the just-written file is
        # not possible here — the file was written now, sources are older.
        assert found == eink

    def test_target_lookup_returns_none_when_only_plain_exists(self, tmp_path):
        from scripts.build_edition import is_output_current

        self._touch(tmp_path, "Ethiopian_Bible_catholic-study_vT_2099-01-01T000000Z.epub")
        assert is_output_current(tmp_path, "catholic-study", "vT", target_reader="eink") is None


class TestCliTargetReaderFlag:
    """--target-reader must exist, validate against TARGET_READERS, and
    plumb to build_one."""

    def _stub_stats(self, out_dir: Path) -> dict:
        p = out_dir / "Ethiopian_Bible_x_v_2099.epub"
        return {
            "enabled_kinds": 0,
            "disabled_kinds": 0,
            "markers_removed": 0,
            "asides_removed": 0,
            "output_path": p,
            "size_mb": 0.0,
            "skipped": False,
        }

    def test_flag_plumbs_to_build_one(self, tmp_path, monkeypatch):
        import pytest

        from scripts import build_edition as be

        captured: dict = {}

        def fake_build_one(
            edition_id, output_dir, version, all_kinds, dry_run=False, force=False, *, target_reader=None
        ):
            captured["edition_id"] = edition_id
            captured["target_reader"] = target_reader
            return self._stub_stats(tmp_path)

        monkeypatch.setattr(be, "build_one", fake_build_one)
        monkeypatch.setattr(
            "sys.argv",
            [
                "build_edition.py",
                "catholic-study",
                "--target-reader",
                "eink",
                "--output-dir",
                str(tmp_path),
                "--version",
                "vTEST",
            ],
        )
        with pytest.raises(SystemExit) as exc:
            be.main()
        assert exc.value.code == 0
        assert captured == {"edition_id": "catholic-study", "target_reader": "eink"}

    def test_invalid_flag_value_rejected_by_argparse(self, tmp_path, monkeypatch):
        import pytest

        from scripts import build_edition as be

        monkeypatch.setattr(
            "sys.argv",
            ["build_edition.py", "catholic-study", "--target-reader", "papyrus"],
        )
        with pytest.raises(SystemExit) as exc:
            be.main()
        assert exc.value.code == 2

    def test_all_with_override_skips_standalone_editions(self, tmp_path, monkeypatch):
        # The format matrix covers the 8 canon editions (spec §7: the
        # standalone Ge'ez/Amharic stay in LANE P) — `--all --target-reader X`
        # must skip standalones with a note rather than fail per edition.
        import pytest

        from scripts import build_edition as be
        from scripts.core import config

        built: list[str] = []

        def fake_build_one(
            edition_id, output_dir, version, all_kinds, dry_run=False, force=False, *, target_reader=None
        ):
            built.append(edition_id)
            return self._stub_stats(tmp_path)

        monkeypatch.setattr(be, "build_one", fake_build_one)
        monkeypatch.setattr(
            "sys.argv",
            [
                "build_edition.py",
                "--all",
                "--no-parallel",
                "--target-reader",
                "eink",
                "--output-dir",
                str(tmp_path),
                "--version",
                "vTEST",
            ],
        )
        with pytest.raises(SystemExit) as exc:
            be.main()
        assert exc.value.code == 0
        standalone_ids = {e["id"] for e in config.load_editions() if e.get("standalone")}
        assert standalone_ids, "expected standalone editions to exist"
        assert not (set(built) & standalone_ids)
        assert built, "expected the non-standalone editions to build"


class TestCacheKeySidecarHonesty:
    """The stats sidecar written on a cache hit must carry the resolved
    target so artifact-level tooling (gates, CI manifests) can read the
    format from the sidecar without re-deriving it."""

    def test_cache_hit_sidecar_records_target(self, tmp_path, monkeypatch):
        from scripts import build_edition as be
        from scripts.core import build_cache as bc
        from scripts.core import config

        fake_epub = tmp_path / "cached.epub"
        fake_epub.write_bytes(b"fake")
        monkeypatch.setattr(bc, "compute_cache_key", lambda *a, **kw: "f" * 64)
        monkeypatch.setattr(bc, "cache_lookup", lambda key, **kw: fake_epub)

        out_dir = tmp_path / "out"
        stats = be.build_one(
            "catholic-study", out_dir, "vTEST", config.load_kinds(), False, False, target_reader="kindle"
        )
        sidecars = list(out_dir.glob("*.stats.json"))
        assert sidecars, "expected a stats sidecar next to the artifact"
        data = json.loads(sidecars[0].read_text(encoding="utf-8"))
        assert data.get("target_reader") == "kindle"
        assert stats["target_reader"] == "kindle"
