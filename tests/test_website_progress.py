import os

from scripts import gen_website_progress as gp

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_stage_precedence_and_real_truth():
    data = gp.compute_progress(REPO)
    geez = {b["code"]: b for b in data["geez"]["books"]}

    # Ge'ez ground truth (the standalone build ships exactly these 4)
    assert geez["1ki"]["stage"] == "ready"
    assert geez["1sa"]["stage"] == "ready"
    assert geez["2sa"]["stage"] == "ready"
    assert geez["psa"]["stage"] == "ready"
    assert data["geez"]["counts"]["ready"] == 4
    # EN mark present for a Bible-ready book that has English
    assert geez["psa"]["en"] is True
    # a book with source but not own-versified is "source"
    assert geez["gen"]["stage"] in ("source", "ready")  # gen has store data + EN
    # a book absent from the store is "none"
    assert geez["rev"]["stage"] == "none"

    # Amharic ground truth: 28 books have source, 0 are Bible-ready
    assert data["amharic"]["counts"]["ready"] == 0
    assert data["amharic"]["counts"]["source"] == 28

    # canon coverage = the full 87-book registry, in canonical order
    assert len(data["geez"]["books"]) == 87
    assert data["geez"]["books"][0]["code"] == "gen"


def test_fragment_renders_bars_grid_and_is_honest():
    data = gp.compute_progress(REPO)
    frag = gp.render_fragment(data)
    # a bar + a count for each Bible
    assert "Ge'ez Bible" in frag and "Amharic Bible" in frag
    assert "4" in frag  # 4 books Bible-ready (Ge'ez)
    # the per-book grid: a cell per canon book, across both grids
    assert frag.count('class="pb-cell') == 87 * 2
    # honesty: Ge'ez has ready cells; no script injection
    assert 'data-stage="ready"' in frag
    assert "<script" not in frag
