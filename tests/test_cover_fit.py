"""σ.2 — cover text + overflow-proof fitter tests.

The reported bug: long edition titles overran the gold border because the old
``_fit_title_font`` shrank 72→28pt then returned 28pt *without re-checking fit*.
σ.2 replaces the single full-title composite with a fixed main title
("HOLY BIBLE") + a small builder-chosen subtitle, drawn through a
wrap-then-shrink fitter that GUARANTEES every line fits the safe width.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# σ.2.1 — cover_text_for_edition(edition_id) -> (main_title, subtitle)
# ---------------------------------------------------------------------------


def test_cover_text_for_edition_reads_fields():
    from scripts.generate_edition_covers import cover_text_for_edition

    main, subtitle = cover_text_for_edition("catholic-study")
    assert main == "HOLY BIBLE"  # default main title
    assert isinstance(subtitle, str)  # display_name (falls back to title)
    assert subtitle  # catholic-study has a title/display_name → non-empty


def test_cover_text_unknown_edition_defaults():
    from scripts.generate_edition_covers import cover_text_for_edition

    main, subtitle = cover_text_for_edition("no-such-edition")
    assert main == "HOLY BIBLE"
    assert subtitle == ""  # no edition → no title → empty subtitle (no subtitle drawn)


# ---------------------------------------------------------------------------
# σ.2.2 — fit_text_block: wrap-then-shrink, guaranteed fit
# ---------------------------------------------------------------------------


def _draw():
    from PIL import Image, ImageDraw

    return ImageDraw.Draw(Image.new("RGB", (1024, 1536)))


def test_long_title_never_overflows():
    from PIL import Image, ImageDraw

    from scripts.generate_edition_covers import TITLE_MAX_WIDTH, fit_text_block

    img = Image.new("RGB", (1024, 1536))
    draw = ImageDraw.Draw(img)
    long = "The Extraordinarily Long Ethiopian Tewahedo Commemorative Study Bible Personal Heirloom Edition"
    lines, font = fit_text_block(draw, long, TITLE_MAX_WIDTH, max_pt=72, min_pt=20)
    for line in lines:
        w = draw.textbbox((0, 0), line, font=font)[2]
        assert w <= TITLE_MAX_WIDTH, f"line overflows: {line!r} ({w}px > {TITLE_MAX_WIDTH})"
    assert len(lines) >= 1


def test_pathological_unbreakable_word_is_hard_broken():
    # A single "word" longer than max_width at min_pt must still be hard-broken
    # so every returned line fits — the absolute guarantee.
    from scripts.generate_edition_covers import TITLE_MAX_WIDTH, fit_text_block

    draw = _draw()
    long = "Supercalifragilisticexpialidocious" * 6  # one ~204-char token
    lines, font = fit_text_block(draw, long, TITLE_MAX_WIDTH, max_pt=72, min_pt=20)
    assert len(lines) >= 1
    for line in lines:
        w = draw.textbbox((0, 0), line, font=font)[2]
        assert w <= TITLE_MAX_WIDTH, f"hard-break failed: {line!r} ({w}px > {TITLE_MAX_WIDTH})"


def test_short_main_title_stays_one_line():
    from scripts.generate_edition_covers import TITLE_FONT_MAX, TITLE_MAX_WIDTH, fit_text_block

    draw = _draw()
    lines, font = fit_text_block(draw, "HOLY BIBLE", TITLE_MAX_WIDTH, max_pt=TITLE_FONT_MAX, min_pt=28)
    assert lines == ["HOLY BIBLE"]  # short enough to stay one line
    assert font.size == TITLE_FONT_MAX  # and at full size


def test_empty_text_returns_no_lines():
    from scripts.generate_edition_covers import TITLE_MAX_WIDTH, fit_text_block

    draw = _draw()
    lines, _font = fit_text_block(draw, "", TITLE_MAX_WIDTH, max_pt=40, min_pt=22)
    assert lines == []


# ---------------------------------------------------------------------------
# _compose_cover(main_title, subtitle) — composition + empty-subtitle case
# ---------------------------------------------------------------------------


def test_compose_cover_with_subtitle_produces_full_size_cover():
    from scripts.generate_edition_covers import FINAL_HEIGHT, FINAL_WIDTH, _compose_cover

    img = _compose_cover("03_beadline_navy", "HOLY BIBLE", "The Catholic Study Bible — Ethiopian Edition")
    assert img.size == (FINAL_WIDTH, FINAL_HEIGHT)


def test_compose_cover_empty_subtitle_draws_only_main():
    # Empty subtitle → no subtitle region drawn; main-only cover composites
    # without error at full size.
    from scripts.generate_edition_covers import FINAL_HEIGHT, FINAL_WIDTH, _compose_cover

    main_only = _compose_cover("03_beadline_navy", "HOLY BIBLE", "")
    assert main_only.size == (FINAL_WIDTH, FINAL_HEIGHT)
    # A cover WITH a subtitle differs from the main-only cover (proof the
    # subtitle branch actually drew pixels).
    with_sub = _compose_cover("03_beadline_navy", "HOLY BIBLE", "An Example Subtitle Line")
    assert main_only.tobytes() != with_sub.tobytes()


def test_compose_cover_long_subtitle_never_overflows():
    # End-to-end: a very long subtitle must not raise and must produce a
    # full-size cover (the fitter wraps/shrinks it inside the safe band).
    from scripts.generate_edition_covers import FINAL_HEIGHT, FINAL_WIDTH, _compose_cover

    img = _compose_cover(
        "03_beadline_navy",
        "HOLY BIBLE",
        "The Extraordinarily Long Ethiopian Tewahedo Commemorative Study Bible Personal Heirloom Edition",
    )
    assert img.size == (FINAL_WIDTH, FINAL_HEIGHT)
