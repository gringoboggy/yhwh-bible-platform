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


# ---------------------------------------------------------------------------
# σ.4.4 — vertical-overflow guard: the drawn text block stays inside the
# top/bottom safe band (not just within img.size — Pillow silently clips,
# so img.size alone proves nothing). ``_compose_cover_layout`` returns the
# laid-out blocks so the test can assert their pixel bounds.
# ---------------------------------------------------------------------------


def _measured_block_bounds(draw, lines, font, top_y):
    """Top/bottom y of an actually-drawn block, matching _draw_centered_block's
    line stacking (ascent+descent + TITLE_LINE_SPACING between lines)."""
    from scripts.generate_edition_covers import TITLE_LINE_SPACING

    if not lines:
        return (top_y, top_y)
    ascent, descent = font.getmetrics()
    line_h = ascent + descent
    bottom = top_y + len(lines) * line_h + (len(lines) - 1) * TITLE_LINE_SPACING
    return (top_y, bottom)


def _assert_layout_within_band(layout):
    from scripts.generate_edition_covers import BOTTOM_SAFE_Y, TOP_SAFE_Y

    draw = _draw()
    # Main block.
    mtop, mbot = _measured_block_bounds(draw, layout["main_lines"], layout["main_font"], layout["main_top_y"])
    assert mtop >= TOP_SAFE_Y, f"main block top {mtop} above safe {TOP_SAFE_Y}"
    assert mbot <= BOTTOM_SAFE_Y, f"main block bottom {mbot} below safe {BOTTOM_SAFE_Y}"
    if layout["sub_lines"]:
        stop, sbot = _measured_block_bounds(draw, layout["sub_lines"], layout["sub_font"], layout["sub_top_y"])
        assert stop >= TOP_SAFE_Y, f"subtitle top {stop} above safe {TOP_SAFE_Y}"
        assert sbot <= BOTTOM_SAFE_Y, f"subtitle bottom {sbot} below safe {BOTTOM_SAFE_Y}"


def test_safe_band_constants_bound_the_frame():
    from scripts.generate_edition_covers import BOTTOM_SAFE_Y, FINAL_HEIGHT, TOP_SAFE_Y

    assert 0 < TOP_SAFE_Y < BOTTOM_SAFE_Y < FINAL_HEIGHT


def test_compose_cover_long_subtitle_never_overflows_pixel_bounds():
    # The crux of σ.4.4: a pathological subtitle's DRAWN pixels must stay
    # inside the vertical safe band (Pillow would otherwise silently clip).
    from scripts.generate_edition_covers import _compose_cover_layout

    layout = _compose_cover_layout(
        "HOLY BIBLE",
        "The Extraordinarily Long Ethiopian Tewahedo Commemorative Study Bible Personal Heirloom Edition",
    )
    _assert_layout_within_band(layout)


def test_compose_cover_pathological_main_and_subtitle_within_band():
    # Both a pathological main title AND a pathological subtitle (the worst
    # case the console could ever produce, and worse) must fit the band.
    from scripts.generate_edition_covers import _compose_cover_layout

    main = "THE EXTRAORDINARILY MONUMENTAL COMMEMORATIVE HEIRLOOM PRESENTATION HOLY SCRIPTURE EDITION OF GREAT LENGTH"
    subtitle = (
        "An Equally Preposterous And Unreasonably Verbose Subtitle That Should Never Have Been Typed By Anyone Ever"
    )
    layout = _compose_cover_layout(main, subtitle)
    _assert_layout_within_band(layout)
    # It still rendered both blocks (didn't silently drop them).
    assert layout["main_lines"]
    assert layout["sub_lines"]


def test_compose_cover_clamps_top_for_a_tall_stack():
    # A stack tall enough that its centered top would go above the frame must
    # be clamped down to the top-safe margin (never negative / above-frame).
    from scripts.generate_edition_covers import TOP_SAFE_Y, _compose_cover_layout

    main = "VERY LONG TITLE " * 8  # forces multiple wrapped lines
    layout = _compose_cover_layout(main.strip(), "A Reasonably Sized Subtitle Here")
    assert layout["main_top_y"] >= TOP_SAFE_Y


def test_compose_cover_short_real_cover_is_unchanged_layout():
    # Byte-neutrality guard rail: a short real cover's layout must be the SAME
    # whether or not the clamp exists — i.e. its centered top_y is well below
    # the top-safe margin and the stack fits the band (so the clamp is a no-op).
    from scripts.generate_edition_covers import (
        SUBTITLE_FONT_MAX,
        SUBTITLE_FONT_MIN,
        TITLE_CENTER_Y,
        TITLE_FONT_MAX,
        TITLE_FONT_MIN,
        TITLE_MAX_WIDTH,
        _block_height,
        _compose_cover_layout,
        fit_text_block,
        RULE_GAP,
        RULE_THICKNESS,
        SUBTITLE_GAP,
    )

    draw = _draw()
    main, subtitle = "HOLY BIBLE", "Catholic Study Bible"
    ml, mf = fit_text_block(draw, main, TITLE_MAX_WIDTH, max_pt=TITLE_FONT_MAX, min_pt=TITLE_FONT_MIN)
    sl, sf = fit_text_block(draw, subtitle, TITLE_MAX_WIDTH, max_pt=SUBTITLE_FONT_MAX, min_pt=SUBTITLE_FONT_MIN)
    total = _block_height(mf, len(ml)) + RULE_GAP + RULE_THICKNESS + SUBTITLE_GAP + _block_height(sf, len(sl))
    expected_top = TITLE_CENTER_Y - total // 2

    layout = _compose_cover_layout(main, subtitle)
    # The clamp left the centered top untouched (no-op for the real cover).
    assert layout["main_top_y"] == expected_top
    # And it kept the full-size subtitle font (no re-fit / shrink happened).
    assert layout["sub_font"].size == sf.size
