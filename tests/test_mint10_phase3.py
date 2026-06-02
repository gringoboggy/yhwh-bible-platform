"""mint-10 Phase 3 — silent-data-loss + clone-correctness regressions.

Two HIGH findings from the round-3 deep audit:

1. ``_iter_note_ref_attribution_years`` skipped every 8-field legacy note
   (the ``len(tup) < 9`` guard), so a positive ``time_filter_ceiling`` never
   disabled them. Undated notes (``year is None``) are *supposed* to be
   disabled by a time ceiling (contemporary content a period reader wouldn't
   have had), so the skip silently let them survive the filter.

2. ``_append_cloned_edition`` omitted the kind-gate fields
   (``enabled_categories`` / ``enabled_kinds`` / ``disabled_kinds`` /
   ``max_phase``), so a cloned edition enabled zero kinds and shipped 0 notes.

Both fixes are additive + byte-stable for the 9 KJV editions (none set a
``time_filter_ceiling``; cloned-edition fields appear only on new clones).
"""

from pathlib import Path


REPO = Path(__file__).resolve().parent.parent


class TestMint10TimeFilterEightField:
    def test_eight_field_note_is_disabled_by_time_ceiling(self, monkeypatch, tmp_path):
        from scripts import build_edition as be
        from scripts.core import config as core_config
        from scripts.core import notes_io, source_dates

        notes_dir = tmp_path / "content" / "notes"
        notes_dir.mkdir(parents=True)
        (notes_dir / "gen.py").write_text("NOTES = []\n", encoding="utf-8")

        eight = (1, 1, "", "anchor", "comm", "Title", "Label", "body")  # 8-field: no attribution
        nine_old = (1, 2, "", "anchor", "comm", "Title", "Label", "body", "Old Source (1850)")

        monkeypatch.setattr(be, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(core_config, "books_by_code", lambda: {"gen": {"id_prefix": "ge"}})
        monkeypatch.setattr(notes_io, "load_notes", lambda _p: [eight, nine_old])
        monkeypatch.setattr(source_dates, "lookup_year", lambda a: 1850 if "1850" in (a or "") else None)

        result = be.compute_time_filtered_html_ref_ids({"time_filter_ceiling": 1900})

        # The 8-field, undated note must now be disabled (year None → disabled).
        # Before the fix the `< 9` guard skipped it entirely and it silently
        # survived the time filter — this assertion would have failed.
        assert "ref-ge0101" in result
        # Control: a dated note older than the ceiling stays enabled.
        assert "ref-ge0102" not in result

    def test_no_ceiling_is_still_a_noop(self, monkeypatch, tmp_path):
        # Byte-stability guarantee: with no ceiling the set is empty regardless
        # of the corpus (the `< 8` change must not perturb the default path).
        from scripts import build_edition as be

        assert be.compute_time_filtered_html_ref_ids({}) == set()
        assert be.compute_time_filtered_html_ref_ids({"time_filter_ceiling": 0}) == set()


class TestMint10CloneKindGate:
    def test_clone_carries_kind_gate_fields(self):
        import yaml

        from scripts.api import editions as ed
        from scripts.core import config

        src_id = "ethiopian-tewahedo"
        src = config.editions_by_id()[src_id]
        text = (REPO / "content" / "editions.yaml").read_text(encoding="utf-8")

        new_text = ed._append_cloned_edition(text, src_id, "mint10-clone-test", "Mint10 Clone Test")
        data = yaml.safe_load(new_text)
        clone = next(e for e in data["editions"] if e["id"] == "mint10-clone-test")

        # The bug: these were omitted, so the clone enabled 0 kinds → 0 notes.
        assert clone.get("enabled_categories"), "clone must carry a non-empty kind gate"
        assert clone.get("enabled_categories") == src.get("enabled_categories")
        if src.get("enabled_kinds"):
            assert clone.get("enabled_kinds") == src.get("enabled_kinds")
        if src.get("disabled_kinds"):
            assert clone.get("disabled_kinds") == src.get("disabled_kinds")
        if src.get("max_phase"):
            assert clone.get("max_phase") == src.get("max_phase")
