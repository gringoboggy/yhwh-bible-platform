import os
from pathlib import Path

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
    assert geez["gen"]["stage"] in ("source", "ready")  # gen has store data
    # there is NO "not started" stage — the whole canon is sourced, so an absent book
    # still has its source in hand (Guard #2 / the progress map's load-bearing rule).
    assert geez["rev"]["stage"] == "source"

    # Amharic: nothing transcribed yet → every one of the 87 canon books is "source"
    assert data["amharic"]["counts"]["ready"] == 0
    assert data["amharic"]["counts"]["transcribed"] == 0
    assert data["amharic"]["counts"]["source"] == 87

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
    # honesty: Ge'ez has ready cells; no script injection in the fragment
    assert 'data-stage="ready"' in frag
    assert "<script" not in frag


# ---- the chapter reader -----------------------------------------------------


def test_ethiopic_numeral():
    assert gp.ethiopic_numeral(1) == "፩"
    assert gp.ethiopic_numeral(7) == "፯"
    assert gp.ethiopic_numeral(10) == "፲"
    assert gp.ethiopic_numeral(11) == "፲፩"
    assert gp.ethiopic_numeral(25) == "፳፭"
    assert gp.ethiopic_numeral(100) == "፻"  # leading 1 dropped before ፻
    assert gp.ethiopic_numeral(119) == "፻፲፱"
    assert gp.ethiopic_numeral(151) == "፻፶፩"


def test_only_transcribed_books_are_clickable():
    # The reader gate is the progress map's OWN transcribed (own-versified) signal —
    # never raw OCR ◐ source. Today: psa/1ki/1sa/2sa in Ge'ez, nothing in Amharic.
    assert sorted(gp._transcribed_store_codes(Path(REPO), "geez-tewahedo")) == ["1ki", "1sa", "2sa", "psa"]
    assert gp._transcribed_store_codes(Path(REPO), "amharic-tewahedo") == []

    data = gp.compute_progress(REPO)
    glinks = data["geez"]["links"]
    assert set(glinks) == {"psa", "1ki", "1sa", "2sa"}
    assert "gen" not in glinks and "rev" not in glinks  # OCR source / absent → no reader link
    assert data["amharic"]["links"] == {}

    # the pill becomes a real link in the fragment, but the cell count is unchanged
    frag = gp.render_fragment(data)
    assert 'class="pb-link"' in frag
    assert 'href="{{root}}read/geez/psa.html"' in frag
    assert frag.count('class="pb-cell') == 87 * 2
    assert 'class="pb-en"' not in frag  # EN moved OFF the book pills (onto chapter cells)


def test_render_reader_chapter_parallel_escapes_and_pairs():
    # duplicate verse numbers must survive (positional pairing, not dict-keying) + escaping
    gz = [(24, "ሀ < ለ"), (24, "ሐ& መ"), (25, "ሠ")]
    en = [(24, "first <"), (24, "second &"), (25, "third")]
    html = gp.render_reader_chapter(
        slug="geez",
        lang="gez",
        norm="psa",
        book_label="Psalms",
        geez_name="መዝሙር",
        ch=36,
        geez_rows=gz,
        en_rows=en,
        ready_chs=[35, 36, 37],
    )
    assert html.count('<li class="rdr-row') == 3  # both duplicate-24 rows kept
    assert 'lang="gez"' in html
    assert "ሀ &lt; ለ" in html and "first &lt;" in html  # text HTML-escaped
    assert "ሐ&amp; መ" in html and "second &amp;" in html
    assert "Copy English" in html and "Copy Geʽez" in html
    assert "reader.js" in html
    assert "፴፮" in html  # Ethiopic chapter numeral 36
    assert 'class="rdr-prev"' in html and 'class="rdr-next"' in html


def test_render_reader_chapter_solo_has_no_english():
    html = gp.render_reader_chapter(
        slug="geez",
        lang="gez",
        norm="job",
        book_label="Job",
        geez_name=None,
        ch=1,
        geez_rows=[(1, "x")],
        en_rows=None,
        ready_chs=[1],
    )
    assert "Copy English" not in html
    assert "rdr-row solo" in html
    assert "after the full release" in html  # honest English-coming note
    assert 'class="rdr-prev"' not in html  # only ready chapter → no prev/next


def test_render_book_index_marks_ready_todo_and_en_per_chapter():
    # all 6 ready chapters carry English -> each chapter cell gets the EN chip
    html = gp.render_book_index(
        slug="geez",
        norm="1ki",
        book_label="1 Kings",
        geez_name=None,
        total_ch=22,
        ready_chs=[1, 2, 3, 4, 5, 6],
        parallel_chs=[1, 2, 3, 4, 5, 6],
    )
    assert html.count("rdx-cell rdx-ready") == 6
    assert html.count('class="rdx-cell rdx-todo"') == 16  # 22 − 6 not yet transcribed
    assert html.count('class="rdx-en"') >= 6  # EN on every parallel chapter (+legend)
    assert "6 of 22 chapters readable" in html

    # a ready chapter WITHOUT English shows no EN chip and is labelled "Geʽez only"
    mixed = gp.render_book_index(
        slug="geez",
        norm="job",
        book_label="Job",
        geez_name=None,
        total_ch=3,
        ready_chs=[1, 2, 3],
        parallel_chs=[1, 2],
    )
    assert mixed.count("rdx-cell rdx-ready rdx-parallel") == 2  # only ch1,2 are parallel
    assert "Geʽez only" in mixed  # ch3 + the legend note
