"""mint-11 round-4 fixes — Phase 3 (additive cache-key / invalidation guards).

Covers:
- HIGH #B: build_cache read the NONEXISTENT field ``cover_image_per_book`` instead
  of the real ``book_covers`` → per-book cover changes never busted the cache key
  (a stale EPUB shipped on a cover change). Behavioral test below.
- #22: ``core/source_dates.py`` (the lookup_year CODE) belongs in ``_PIPELINE_SCRIPTS``.
- #25: ``is_output_current`` must watch the full ``_PIPELINE_SCRIPTS`` set + the
  topical / source-date data the build reads (was drifting from build_cache).
- #23 + class-sweep: every KJV-coordinate at-scale driver (xref/naves/torrey/kenyon)
  must apply ``coord_in_canonical_extent`` before emitting candidates.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class TestMint11BuildCacheCoverKey:
    def test_book_covers_field_invalidates_key(self, monkeypatch):
        """The cache key MUST change when an edition's per-book ``book_covers``
        changes. Under the pre-fix code (which read the nonexistent
        ``cover_image_per_book``) the field was ignored and these two keys were
        identical — a stale-EPUB-on-cover-change bug."""
        from scripts.core import build_cache as bc
        from scripts.core import config as _config

        baseline = _config.editions_by_id()
        target = "catholic-study"
        original = dict(baseline[target])

        with_cover = {**original, "book_covers": ["gen=covers/__mint11_probe__.png"]}
        without_cover = {**original, "book_covers": []}

        monkeypatch.setattr(_config, "editions_by_id", lambda: {**baseline, target: with_cover})
        key_with = bc.compute_cache_key(target)
        monkeypatch.setattr(_config, "editions_by_id", lambda: {**baseline, target: without_cover})
        key_without = bc.compute_cache_key(target)

        assert key_with != key_without, "book_covers must contribute to the cache key (mint-11 HIGH #B)"

    def test_build_cache_does_not_reference_phantom_field(self):
        """Regression guard: the nonexistent ``cover_image_per_book`` field must
        never reappear in build_cache (the actual field is ``book_covers``)."""
        src = (REPO / "scripts" / "core" / "build_cache.py").read_text(encoding="utf-8")
        assert "cover_image_per_book" not in src, "build_cache must read 'book_covers', not the phantom field"
        assert 'edition.get("book_covers")' in src


class TestMint11PipelineScripts:
    def test_source_dates_py_tracked(self):
        from scripts.core.build_cache import _PIPELINE_SCRIPTS

        assert "core/source_dates.py" in _PIPELINE_SCRIPTS

    def test_is_output_current_watches_pipeline_and_data(self):
        """is_output_current must compose _PIPELINE_SCRIPTS (no drift) + the
        topical / source-date data files (mint-11 #25)."""
        src = (REPO / "scripts" / "build_edition.py").read_text(encoding="utf-8")
        # locate the function body
        start = src.index("def is_output_current(")
        end = src.index("\ndef ", start + 1)
        body = src[start:end]
        assert "_PIPELINE_SCRIPTS" in body, "is_output_current must compose build_cache._PIPELINE_SCRIPTS"
        assert "source_dates.yaml" in body
        assert "naves_topical.json" in body
        assert "torrey_topical.json" in body


class TestMint11CoordGuardClassSweep:
    """The ★BUGCLUSTER class: every at-scale driver that emits candidates from a
    KJV-coordinate source must drop out-of-extent coords before emitting. mint-10
    fixed naves/torrey; mint-11 completes the class with xref + kenyon. (Own-
    versification manuscript drivers and AI/Hebrew/Greek drivers that read
    canonical coords by construction are intentionally NOT in this set.)"""

    KJV_COORD_DRIVERS = (
        "run_xref_at_scale.py",
        "run_naves_at_scale.py",
        "run_torrey_at_scale.py",
        "run_kenyon_at_scale.py",
    )

    def test_kjv_coord_drivers_apply_extent_guard(self):
        missing = []
        for name in self.KJV_COORD_DRIVERS:
            src = (REPO / "scripts" / name).read_text(encoding="utf-8")
            if "coord_in_canonical_extent" not in src:
                missing.append(name)
        assert not missing, f"KJV-coordinate driver(s) missing coord_in_canonical_extent guard: {missing}"
