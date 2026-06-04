from __future__ import annotations


def test_filter_sets_helper_exists_and_shapes():
    from scripts.build_edition import compute_edition_filter_sets
    from scripts.core import config

    ed = config.editions_by_id()["catholic-study"]
    disabled_kinds, disabled_ref_ids = compute_edition_filter_sets(ed)
    assert isinstance(disabled_kinds, set)
    assert isinstance(disabled_ref_ids, set)
