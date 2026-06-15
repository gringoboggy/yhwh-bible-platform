#!/usr/bin/env python3
"""Front/back-matter EPUB pages — the render_*/inject_* family extracted
(verbatim) from build_edition.py. Each inject_* writes one XHTML page into the
per-edition build tempdir; build_edition.build_one calls the inject_* here.
"""

import html
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.epub_utils import (  # noqa: E402
    _resolve_publishing,
    _xml_escape_text,
    load_canons,
)


def render_copyright_page(
    edition: dict,
    publishing: dict,
    *,
    annotation_count: int,
    category_count: int,
) -> str:
    """Render the front colophon XHTML. Identity from ``publishing``
    (_resolve_publishing), NOT the dead content/onix.py TODO_ defaults; counts term-ref-ok
    are the edition's REAL computed values (scripts.core.matrix). The builder's
    own description + the per-edition summary live on the separate 'Your Edition'
    page (the first page after the cover); full source credits live in the
    back-matter 'Sources & Acknowledgments' page — keep this page compact."""
    pub = publishing.get("publisher_name") or "YHWH Ya' Way Editions"
    holder = (
        publishing.get("copyright_holder") or (publishing.get("contributor") or {}).get("name") or "Bogdan Zorlescu"
    )
    cyear = str(publishing.get("copyright_year") or "2026")
    edition_title = edition.get("title_full", edition.get("title", "Untitled"))
    edition_subtitle = edition.get("title_subtitle", "")
    pub_x = html.escape(pub)
    holder_x = html.escape(holder)
    ann = f"{annotation_count:,}"
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>Copyright</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="copyright-page">
  <section class="copyright-page" epub:type="copyright-page">
    <h1 class="copyright-title">{html.escape(edition_title)}</h1>
    {f'<p class="copyright-subtitle">{html.escape(edition_subtitle)}</p>' if edition_subtitle else ""}
    <hr class="copyright-rule"/>
    <p class="copyright-compiler"><strong>YHWH Ya&#8217; Way</strong> — published by <strong>{pub_x}</strong>, {cyear}.</p>
    <p>&#169; {cyear} {holder_x}. All rights reserved. Editorial notes, selection, arrangement, and presentation are original editorial work; the underlying biblical texts and cited public-domain reference works retain their own public-domain status.</p>
    <p>This edition carries <strong>{ann}</strong> annotations across <strong>{category_count} categories</strong> — a key to the symbols follows on the next page; full source credits are at the back.</p>
  </section>
</body>
</html>
"""


def _drop_placeholder_introduction(tmp: Path) -> None:
    """Remove the placeholder introduction.xhtml from OPF manifest, spine, and
    nav.xhtml in the per-build temp directory.

    The base epub_working/introduction.xhtml contains only placeholder text
    ("About this edition — placeholder text. The full introduction will be
    added later") and should never ship in a built EPUB. The file is left in
    epub_working/ as a design anchor but is stripped from every built edition
    here so it is not included in any EPUB output.

    Called at the end of inject_copyright_page so it runs every build.
    """
    opf_path = tmp / "content.opf"
    if opf_path.is_file():
        opf = opf_path.read_text(encoding="utf-8")
        # Remove manifest item (matches any media-type variant). NB: use
        # [^>]* not [^/]* — the media-type "application/xhtml+xml" contains a
        # '/', so [^/]* stops at it and leaves the item behind (→ a dangling
        # reference to the deleted file = epubcheck RSC-001).
        opf = re.sub(
            r'\n?\s*<item id="introduction" href="introduction\.xhtml"[^>]*/>\n?',
            "\n",
            opf,
        )
        # Remove spine itemref
        opf = re.sub(
            r'\n?\s*<itemref idref="introduction"/>\n?',
            "\n",
            opf,
        )
        opf_path.write_text(opf, encoding="utf-8")

    nav_path = tmp / "nav.xhtml"
    if nav_path.is_file():
        nav = nav_path.read_text(encoding="utf-8")
        # Remove any <li> linking to introduction.xhtml
        nav = re.sub(
            r'\n?\s*<li><a href="introduction\.xhtml">[^<]*</a></li>\n?',
            "\n",
            nav,
        )
        nav_path.write_text(nav, encoding="utf-8")

    # Also remove the physical file from the build temp directory so
    # build_epub.collect_files cannot pick it up as a zip member.
    intro_file = tmp / "introduction.xhtml"
    if intro_file.is_file():
        intro_file.unlink()


def inject_copyright_page(tmp: Path, edition: dict) -> None:
    """Write copyright.xhtml, register it in content.opf (manifest + spine after
    titlepage) and nav.xhtml. Identity from _resolve_publishing.

    σ.6.2 — the printed "N annotations across M categories" comes from
    ``edition_stats.resolved_note_counts`` (the build-accurate counter), so the
    copyright page == the symbol legend == the "Your Edition" page == the real
    EPUB. This subsumes the retired mint-9 #8 ``annotation_count_override``
    (which only corrected the tradition/time ref-id filters) AND adds the rest of
    the ρ.3 hierarchy (per-book/chapter/note overrides) + the base-HTML coverage
    gate — strictly more accurate. ``category_count`` counts the categories that
    actually ship at least one note, matching ``_legend_categories_for_edition``
    exactly.
    """
    from scripts.core import edition_stats

    publishing = _resolve_publishing(edition)
    stats = edition_stats.resolved_note_counts(edition)
    annotation_count = stats["total"]
    category_count = len([n for n in stats["per_category"].values() if n > 0])

    # 1) Write the page
    html_text = render_copyright_page(
        edition, publishing, annotation_count=annotation_count, category_count=category_count
    )
    (tmp / "copyright.xhtml").write_text(html_text, encoding="utf-8")

    # 2) Patch OPF — add manifest item + insert into spine after titlepage
    opf_path = tmp / "content.opf"
    if opf_path.is_file():
        opf = opf_path.read_text(encoding="utf-8")
        if "copyright.xhtml" not in opf:
            opf = opf.replace(
                '<item id="titlepage" href="titlepage.xhtml"',
                '<item id="copyright" href="copyright.xhtml" media-type="application/xhtml+xml"/>\n    '
                '<item id="titlepage" href="titlepage.xhtml"',
            )
            # Spine: after titlepage
            opf = opf.replace(
                '<itemref idref="titlepage"/>', '<itemref idref="titlepage"/>\n    <itemref idref="copyright"/>'
            )
            opf_path.write_text(opf, encoding="utf-8")

    # 3) Patch nav.xhtml TOC
    nav_path = tmp / "nav.xhtml"
    if nav_path.is_file():
        nav = nav_path.read_text(encoding="utf-8")
        if 'href="copyright.xhtml"' not in nav:
            nav = nav.replace(
                "<ol>\n      <li>",
                '<ol>\n      <li><a href="copyright.xhtml">Copyright &amp; Credits</a></li>\n      <li>',
                1,
            )
            nav_path.write_text(nav, encoding="utf-8")

    # 4) Drop the placeholder introduction page (never ships in a built EPUB)
    _drop_placeholder_introduction(tmp)


def render_dedication_page(edition: dict) -> str:
    """Render the optional Dedication page. Only injected when the edition has a
    non-empty `dedication` (see inject_dedication_page)."""
    ded = (edition.get("dedication") or "").strip()
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>Dedication</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="frontmatter">
  <section class="dedication-page" epub:type="dedication">
    <p class="dedication-text">{html.escape(ded)}</p>
  </section>
</body>
</html>
"""


def inject_dedication_page(tmp: Path, edition: dict) -> None:
    """If the edition has a non-empty `dedication`, write dedication.xhtml and
    place it in the front matter RIGHT AFTER the title page (before the colophon).
    No-op when there's no dedication (back-compat: most editions have none)."""
    if not (edition.get("dedication") or "").strip():
        return
    (tmp / "dedication.xhtml").write_text(render_dedication_page(edition), encoding="utf-8")
    opf_path = tmp / "content.opf"
    if opf_path.is_file():
        opf = opf_path.read_text(encoding="utf-8")
        if "dedication.xhtml" not in opf:
            _anchor_m = '<item id="titlepage" href="titlepage.xhtml"'
            _new = opf.replace(
                _anchor_m,
                '<item id="dedication" href="dedication.xhtml" media-type="application/xhtml+xml"/>\n    ' + _anchor_m,
            )
            if _new == opf:
                raise RuntimeError(f"OPF manifest anchor not found: {_anchor_m!r}")
            opf = _new
            _spine_anchor = '<itemref idref="titlepage"/>'
            _new = opf.replace(
                _spine_anchor,
                _spine_anchor + '\n    <itemref idref="dedication"/>',
            )
            if _new == opf:
                raise RuntimeError(f"OPF spine anchor not found: {_spine_anchor!r}")
            opf = _new
            opf_path.write_text(opf, encoding="utf-8")
    nav_path = tmp / "nav.xhtml"
    if nav_path.is_file():
        nav = nav_path.read_text(encoding="utf-8")
        if 'href="dedication.xhtml"' not in nav:
            nav = nav.replace(
                '<li><a href="copyright.xhtml">Copyright &amp; Credits</a></li>',
                '<li><a href="dedication.xhtml">Dedication</a></li>\n      <li><a href="copyright.xhtml">Copyright &amp; Credits</a></li>',
                1,
            )
            nav_path.write_text(nav, encoding="utf-8")


def _legend_categories_for_edition(edition_id: str) -> list[dict]:
    """Ordered list of {id, symbol, label, description, count} for the categories
    that actually appear in this edition (count > 0), in categories.yaml
    sort_order. Edition-aware: disabling a category (or a canon that excludes it)
    drops its symbol from the guide.

    σ.3.1 — driven by ``edition_stats.resolved_note_counts`` (the build-accurate
    counter that honors the ρ.3 per-book/chapter/note hierarchy), NOT the
    edition-wide ``matrix.breakdown_by_category`` it used before. So a family
    turned off across the canon drops its symbol, while a single force-on note
    of an otherwise-off family resurfaces it — exactly the symbols that ship."""
    from scripts.core import config, edition_stats

    edition = config.editions_by_id()[edition_id]
    present = edition_stats.resolved_note_counts(edition)["per_category"]  # {cat_id: count}
    cats = sorted(config.load_categories(), key=lambda c: c.get("sort_order", 999))
    return [
        {
            "id": c["id"],
            "symbol": c.get("symbol", "•"),
            "label": c.get("label", c["id"]),
            "description": c.get("description", ""),
            "count": present.get(c["id"], 0),
        }
        for c in cats
        if present.get(c["id"], 0) > 0
    ]


def render_symbol_legend_page(edition: dict, categories: list[dict]) -> str:
    """Render the 'A Guide to the Notes' XHTML. `categories` is the ordered,
    already-filtered list from _legend_categories_for_edition. Each row gets a
    stable anchor id='legend-<category-id>' so in-note symbols (Phase 2) can link
    to it. Spec 2026-05-24 §5.3."""
    rows = []
    for c in categories:
        rows.append(
            f'    <p class="legend-row" id="legend-{html.escape(c["id"])}">'
            f'<span class="legend-sym">{html.escape(c["symbol"])}</span> '
            f'<span class="legend-label">{html.escape(c["label"])}</span> '
            f'<span class="legend-count">({c["count"]:,} notes)</span><br/>'
            f'<span class="legend-desc">{html.escape(c["description"])}</span></p>'
        )
    body = "\n".join(rows) if rows else '    <p class="legend-row">This edition carries no annotations.</p>'
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>A Guide to the Notes</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="frontmatter">
  <section class="legend-page" epub:type="frontmatter">
    <h1 class="legend-title">A Guide to the Notes</h1>
    <p class="legend-intro">Each annotation in this edition opens with a symbol marking the kind of note. The symbols used in this edition are:</p>
{body}
  </section>
</body>
</html>
"""


def inject_symbol_legend_page(tmp: Path, edition: dict) -> None:
    """Write legend.xhtml, register it in the OPF (manifest + spine right after
    copyright) and add a nav.xhtml TOC entry (also renaming the copyright TOC
    label to 'Copyright' to match its page title — K-R2-6: the reader's ToC
    used to list TWO pages named 'Colophon', front and back)."""
    categories = _legend_categories_for_edition(edition["id"])
    html_text = render_symbol_legend_page(edition, categories)
    (tmp / "legend.xhtml").write_text(html_text, encoding="utf-8")

    opf_path = tmp / "content.opf"
    if opf_path.is_file():
        opf = opf_path.read_text(encoding="utf-8")
        if "legend.xhtml" not in opf:
            _anchor_m = '<item id="copyright" href="copyright.xhtml" media-type="application/xhtml+xml"/>'
            _new = opf.replace(
                _anchor_m,
                _anchor_m + '\n    <item id="legend" href="legend.xhtml" media-type="application/xhtml+xml"/>',
            )
            if _new == opf:
                raise RuntimeError(f"OPF manifest anchor not found: {_anchor_m!r}")
            opf = _new
            _spine_anchor = '<itemref idref="copyright"/>'
            _new = opf.replace(
                _spine_anchor,
                _spine_anchor + '\n    <itemref idref="legend"/>',
            )
            if _new == opf:
                raise RuntimeError(f"OPF spine anchor not found: {_spine_anchor!r}")
            opf = _new
            opf_path.write_text(opf, encoding="utf-8")

    nav_path = tmp / "nav.xhtml"
    if nav_path.is_file():
        nav = nav_path.read_text(encoding="utf-8")
        if 'href="legend.xhtml"' not in nav:
            nav = nav.replace(
                '<li><a href="copyright.xhtml">Copyright &amp; Credits</a></li>',
                '<li><a href="copyright.xhtml">Copyright</a></li>\n'
                '      <li><a href="legend.xhtml">A Guide to the Notes</a></li>',
                1,
            )
            nav_path.write_text(nav, encoding="utf-8")


def _edition_canon_book_count(edition_id: str) -> int:
    """Number of books actually in this edition's canon (the build canon, from
    ``matrix.compute_matrix().edition_canon_books``). Truthful to what ships —
    the books the build emits, not the canon-yaml standard count."""
    from scripts.build_edition import APPENDIX_BOOKS
    from scripts.core import matrix as _matrix

    # beta-3 (f): appendix books (the Daniel additions) ship as appendices, not
    # standalone numbered books, so they don't count toward "spans N books".
    appendix = set(APPENDIX_BOOKS)
    canon = _matrix.compute_matrix().edition_canon_books.get(edition_id) or set()
    return len([b for b in canon if b not in appendix])


def _canon_label(edition: dict) -> str:
    """Short canon name for the 'What's inside' line — the canons.yaml label with
    any parenthetical annotation stripped (e.g. 'Catholic Bible (73 books…)' →
    'Catholic Bible')."""
    canon_id = edition.get("canon") or "protestant"
    canon_info = load_canons().get(canon_id, {})
    raw_label = canon_info.get("label") or canon_id.replace("-", " ").title()
    return raw_label.split("(")[0].strip().rstrip(",")


def _category_labels_for_stats(stats: dict) -> list[str]:
    """Human labels of the note families that actually ship (``stats['per_category']``
    keys with count>0), in categories.yaml sort_order. Skips the empty bucket
    ('' = notes whose kind lacks a registered category) so the summary reads
    cleanly."""
    from scripts.core import config as _cfg

    present = {cat for cat, n in (stats.get("per_category") or {}).items() if n > 0 and cat}
    cats_meta = sorted(_cfg.load_categories(), key=lambda c: c.get("sort_order", 999))
    return [c.get("label", c["id"]) for c in cats_meta if c["id"] in present]


def _popup_language_labels(stats: dict) -> list[str]:
    """Human labels of the popup languages that ship (``stats['popup_languages']``),
    via build_edition.POPUP_LANGUAGES; unknown tokens fall back to the raw id."""
    from scripts.build_edition import POPUP_LANGUAGES

    out: list[str] = []
    for tok in stats.get("popup_languages") or []:
        out.append(POPUP_LANGUAGES.get(tok, {}).get("label") or tok)
    return out


def _oxford_join(items: list[str]) -> str:
    """Join a label list as a readable Oxford-comma series ('A', 'A and B',
    'A, B, and C')."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + ", and " + items[-1]


def _whats_inside_sentence(edition: dict, stats: dict) -> str:
    """A truthful description of the edition: canon + note families + popup
    languages, as two clean sentences. Gracefully degrades when there are no
    notes / no popups. Returns an html.escape'd fragment (callers embed it
    directly)."""
    canon = _canon_label(edition)
    families = _category_labels_for_stats(stats)
    languages = _popup_language_labels(stats)

    if families:
        first = f"This edition follows the {html.escape(canon)} canon and includes {html.escape(_oxford_join(families))} notes."
    else:
        first = f"This edition follows the {html.escape(canon)} canon and carries no annotation notes."

    if languages:
        second = f" Verses open in {html.escape(_oxford_join(languages))} popups."
    else:
        second = " It has no verse popups."

    return first + second


def render_your_edition_page(edition: dict, stats: dict, version: str) -> str:
    """Render the 'Your Edition' XHTML — the FIRST content page after the cover.

    It tells the builder exactly what they built:

      * heading      = the builder's ``display_name`` (falls back to ``title``);
      * notes        = the builder's ``description``, an italic blockquote IF set;
      * what's inside = canon + book count + note families present + popup
                        languages + theme (a truthful sentence, graceful when
                        there are no notes / no popups);
      * total        = ``stats['total']`` notes;
      * per-book table = ``stats['per_book']`` in canonical book order, books
                        with count>0 only.

    ``stats`` is the build-accurate ``edition_stats.resolved_note_counts`` dict —
    the same source the glossary uses — so every printed number equals the real
    EPUB. All user-facing text is html.escape'd."""
    from scripts.core import config as _cfg

    heading = edition.get("display_name") or edition.get("title", "Untitled")

    # Notes blockquote — only when the builder set a description.
    desc = (edition.get("description") or "").strip()
    notes_block = (
        f'    <blockquote class="your-edition-notes"><em>{html.escape(desc)}</em></blockquote>\n' if desc else ""
    )

    # What's inside.
    book_count = _edition_canon_book_count(edition["id"])
    whats_inside = _whats_inside_sentence(edition, stats)
    theme = str(edition.get("theme") or "").strip()
    theme_clause = f" The presentation theme is <em>{html.escape(theme)}</em>." if theme else ""
    inside_line = (
        f'    <p class="your-edition-inside">{whats_inside}'
        f" It spans <strong>{book_count:,}</strong> books.{theme_clause}</p>"
    )

    # Total notes.
    total = int(stats.get("total") or 0)
    total_line = (
        f'    <p class="your-edition-total"><strong>{total:,}</strong> {"note" if total == 1 else "notes"} in all.</p>'
    )

    # Per-book counts — canonical book order (RULES §6.1), count>0 only.
    # finding 2: a <table table-layout:fixed> clipped the book-name column off the
    # left in Apple-Books (no first-row/<colgroup> widths → intrinsic overflow); a
    # float-based 2-column block has no table-layout dependency + is e-ink-safe.
    # Count emitted FIRST in source so float:right clears correctly.
    per_book = stats.get("per_book") or {}
    book_order = [b["code"] for b in _cfg.load_books()]
    book_titles = _cfg.books_by_code()
    rows: list[str] = []
    for code in book_order:
        n = per_book.get(code, 0)
        if n <= 0:
            continue
        title = book_titles.get(code, {}).get("title", code)
        rows.append(
            f'      <p class="ye-row"><span class="ye-count">{n:,}</span>'
            f'<span class="ye-book">{html.escape(title)}</span></p>'
        )
    if rows:
        perbook_block = (
            '    <div class="ye-rows">\n'
            '      <p class="ye-rows-head"><span class="ye-count">Notes</span>'
            '<span class="ye-book">Book</span></p>\n' + "\n".join(rows) + "\n    </div>"
        )
    else:
        perbook_block = '    <p class="your-edition-perbook-empty">This edition carries no annotations.</p>'

    # Edition identity (Edition ID + Build) — relocated here from the front colophon
    # (device-QA 2026-06-09) so it sits beside the composition + per-book note details,
    # which the user found more logical than splitting it onto the colophon.
    edition_urn = f"urn:yhwh:edition:{edition['id']}"
    meta_line = (
        f'    <p class="your-edition-meta"><strong>Edition ID:</strong> {edition_urn}'
        f" &#183; <strong>Build:</strong> {html.escape(version)}</p>"
    )

    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>Your Edition</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="frontmatter">
  <section class="your-edition-page" epub:type="frontmatter">
    <h1 class="your-edition-title">{html.escape(heading)}</h1>
{notes_block}{inside_line}
{total_line}
{perbook_block}
{meta_line}
  </section>
</body>
</html>
"""


def inject_your_edition_page(tmp: Path, edition: dict, version: str) -> None:
    """Write your-edition.xhtml and register it in OPF (manifest + spine RIGHT
    AFTER titlepage, before copyright) and nav.xhtml (first TOC entry). Guards
    against double-injection.

    Counts come from ``edition_stats.resolved_note_counts`` (computed once here)
    so the page is build-accurate and honors the ρ.3 hierarchy — the same source
    the glossary uses."""
    from scripts.core import edition_stats

    stats = edition_stats.resolved_note_counts(edition)
    html_text = render_your_edition_page(edition, stats, version)
    (tmp / "your-edition.xhtml").write_text(html_text, encoding="utf-8")

    opf_path = tmp / "content.opf"
    if opf_path.is_file():
        opf = opf_path.read_text(encoding="utf-8")
        if "your-edition.xhtml" not in opf:
            _anchor_m = '<item id="titlepage" href="titlepage.xhtml"'
            _new = opf.replace(
                _anchor_m,
                '<item id="youredition" href="your-edition.xhtml" media-type="application/xhtml+xml"/>\n    '
                + _anchor_m,
            )
            if _new == opf:
                raise RuntimeError(f"OPF manifest anchor not found: {_anchor_m!r}")
            opf = _new
            _spine_anchor = '<itemref idref="titlepage"/>'
            _new = opf.replace(
                _spine_anchor,
                _spine_anchor + '\n    <itemref idref="youredition"/>',
            )
            if _new == opf:
                raise RuntimeError(f"OPF spine anchor not found: {_spine_anchor!r}")
            opf = _new
            opf_path.write_text(opf, encoding="utf-8")

    nav_path = tmp / "nav.xhtml"
    if nav_path.is_file():
        nav = nav_path.read_text(encoding="utf-8")
        if 'href="your-edition.xhtml"' not in nav:
            nav = nav.replace(
                "<ol>\n      <li>",
                '<ol>\n      <li><a href="your-edition.xhtml">Your Edition</a></li>\n      <li>',
                1,
            )
            nav_path.write_text(nav, encoding="utf-8")


def _sources_sections() -> list[tuple[str, str]]:
    """Return list of (heading, body_html) pairs for Sources & Acknowledgments.

    Composed from ATTRIBUTIONS.md + popup_versions.py VERSION_REGISTRY.
    All text is static (not per-edition). Returns pre-escaped HTML fragments
    suitable for embedding in the XHTML body."""
    from scripts.core.popup_versions import VERSION_REGISTRY

    # Translation witnesses: list human labels of all registry versions
    # (order by 'order' key ascending).
    witnesses = sorted(VERSION_REGISTRY.values(), key=lambda v: v["order"])
    witness_items = "".join(
        f'\n        <li class="sources-item">{html.escape(w["label"])} — Public Domain</li>' for w in witnesses
    )

    sections: list[tuple[str, str]] = [
        (
            "Biblical Text",
            "<p>World English Bible (WEB). Public Domain. "
            "The WEB is a revision of the American Standard Version (1901) "
            "placed in the public domain by Rainbow Missions, Inc.</p>",
        ),
        (
            "Lexicons &amp; Reference Works",
            "<p>The following public-domain reference works were used to compile annotations:</p>"
            '<ul class="sources-list">'
            '\n        <li class="sources-item">Strong&#x2019;s Exhaustive Concordance'
            " (Hebrew &amp; Greek Dictionaries), James Strong, 1894. Public Domain."
            " Digital edition: Open Scriptures, CC-BY-SA.</li>"
            '\n        <li class="sources-item">Treasury of Scripture Knowledge (TSK),'
            " Canne, Browne, Blayney, Scott et al., 1830s. Public Domain."
            " Digital edition: OpenBible.info, CC-BY 4.0.</li>"
            '\n        <li class="sources-item">Nave&#x2019;s Topical Bible,'
            " Orville J. Nave, 1896. Public Domain.</li>"
            '\n        <li class="sources-item">Torrey&#x2019;s New Topical Textbook,'
            " R.A. Torrey, 1897. Public Domain.</li>"
            '\n        <li class="sources-item">Easton&#x2019;s Bible Dictionary,'
            " Matthew George Easton, 1897. Public Domain.</li>"
            "\n      </ul>",
        ),
        (
            "Commentary &amp; Canonical Voices",
            "<p>Patristic and Ethiopian canonical commentary drawn from public-domain sources:</p>"
            '<ul class="sources-list">'
            '\n        <li class="sources-item">Cyril of Alexandria,'
            " <em>Commentary on the Gospel of St. John</em>,"
            " trans. Pusey &amp; Randell (1874&#x2013;1885). Public Domain.</li>"
            '\n        <li class="sources-item">Ephrem the Syrian,'
            " <em>Commentary on Genesis</em> and <em>Hymns on Paradise</em>,"
            " Nicene and Post-Nicene Fathers Series II, vol. XIII (1898). Public Domain.</li>"
            '\n        <li class="sources-item">Athanasius of Alexandria'
            " &#x2014; selected writings from Nicene and Post-Nicene Fathers. Public Domain.</li>"
            '\n        <li class="sources-item">1 Enoch (M&#xe4;&#x1e63;&#x1e25;afä H&#x113;nok),'
            " trans. R. H. Charles (Oxford: Clarendon Press, 1912). Public Domain.</li>"
            '\n        <li class="sources-item">Book of Jubilees (M&#xe4;&#x1e63;&#x1e25;afä Kuf&#x101;le),'
            " trans. R. H. Charles (Adam and Charles Black, 1902). Public Domain.</li>"
            '\n        <li class="sources-item">Mäqabyan (1&#x2013;3) &#x2014;'
            " Ethiopian canonical texts, public-domain English translations.</li>"
            "\n      </ul>",
        ),
        (
            "Translation Witnesses",
            "<p>Verse-popup witnesses baked into this volume"
            " (all public domain):</p>"
            f'<ul class="sources-list">{witness_items}\n      </ul>',
        ),
        (
            "Attribution Statement",
            "<p>Per-note attribution is preserved in the apparatus."
            " All sources incorporated in this volume are in the public domain.</p>",
        ),
    ]
    return sections


def render_sources_page() -> str:
    """Render Sources &amp; Acknowledgments XHTML (static; not per-edition)."""
    sections_html_parts: list[str] = []
    for heading, body_html in _sources_sections():
        sections_html_parts.append(
            f'  <section class="sources-section">\n'
            f'    <h2 class="sources-heading">{heading}</h2>\n'
            f"    {body_html}\n"
            f"  </section>"
        )
    body = "\n\n".join(sections_html_parts)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>Sources &amp; Acknowledgments</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="backmatter">
  <section class="backmatter-page" epub:type="backmatter">
    <h1 class="backmatter-title">Sources &amp; Acknowledgments</h1>

{body}
  </section>
</body>
</html>
"""


def render_reference_tables_page() -> str:
    """Render Reference Tables XHTML (static study-Bible reference data)."""

    def _table(caption: str, headers: list[str], rows: list[list[str]]) -> str:
        th_cells = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
        tr_rows = "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in row) + "</tr>" for row in rows)
        return (
            f'<table class="reftable">'
            f'<caption class="reftable-caption">{html.escape(caption)}</caption>'
            f"<thead><tr>{th_cells}</tr></thead>"
            f"<tbody>{tr_rows}</tbody>"
            f"</table>"
        )

    length_table = _table(
        "Length",
        ["Unit", "Approx. (imperial)", "Approx. (metric)"],
        [
            ["Handbreadth", "3 in", "7.6 cm"],
            ["Span", "9 in", "23 cm"],
            ["Cubit", "18 in", "45 cm"],
            ["Long cubit", "21 in", "53 cm"],
            ["Reed (6 cubits)", "9 ft", "2.7 m"],
        ],
    )
    weight_table = _table(
        "Weight",
        ["Unit", "Approx."],
        [
            ["Gerah", "0.6 g"],
            ["Beka (10 gerahs)", "6 g"],
            ["Shekel (20 gerahs)", "11.4 g"],
            ["Mina (50 shekels)", "0.6 kg"],
            ["Talent (3,000 shekels)", "34 kg"],
        ],
    )
    dry_table = _table(
        "Dry Capacity",
        ["Unit", "Approx."],
        [
            ["Omer", "2 L"],
            ["Seah (3.3 omers)", "7.3 L"],
            ["Ephah (10 omers)", "22 L"],
            ["Homer / Cor (10 ephahs)", "220 L"],
        ],
    )
    liquid_table = _table(
        "Liquid Capacity",
        ["Unit", "Approx."],
        [
            ["Log", "0.3 L"],
            ["Hin (12 logs)", "3.7 L"],
            ["Bath", "22 L"],
        ],
    )
    money_table = _table(
        "Money",
        ["Unit", "Notes"],
        [
            ["Shekel", "Standard weight-based currency"],
            ["Mina (50 shekels)", ""],
            ["Talent (3,000 shekels)", ""],
            ["Denarius", "Approx. one day's wage (NT)"],
            ["Drachma", "Greek silver coin, similar to denarius"],
            ["Mite / Lepton", "Smallest coin in NT usage"],
        ],
    )

    calendar_rows = [
        ["Nisan / Abib", "Mar–Apr", "Passover, Unleavened Bread"],
        ["Iyar", "Apr–May", ""],
        ["Sivan", "May–Jun", "Weeks / Pentecost"],
        ["Tammuz", "Jun–Jul", ""],
        ["Av", "Jul–Aug", ""],
        ["Elul", "Aug–Sep", ""],
        ["Tishri", "Sep–Oct", "Trumpets, Day of Atonement, Tabernacles"],
        ["Cheshvan", "Oct–Nov", ""],
        ["Kislev", "Nov–Dec", ""],
        ["Tevet", "Dec–Jan", ""],
        ["Shevat", "Jan–Feb", ""],
        ["Adar", "Feb–Mar", ""],
    ]
    calendar_table = _table(
        "Hebrew Calendar",
        ["Month", "Approx. Gregorian", "Major Feasts"],
        calendar_rows,
    )

    disclaimer = (
        '<p class="reftable-note"><em>All values are approximate; measures varied by period and region.</em></p>'
    )

    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>Reference Tables</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="backmatter">
  <section class="backmatter-page" epub:type="backmatter">
    <h1 class="backmatter-title">Reference Tables</h1>
    {disclaimer}

    {length_table}

    {weight_table}

    {dry_table}

    {liquid_table}

    {money_table}

    {calendar_table}
  </section>
</body>
</html>
"""


def render_closing_colophon_page(edition: dict) -> str:
    """Render the Closing Colophon XHTML — the genuinely last page of the EPUB.

    K-R2-6 (device-QA 2026-06-09): the internal build string ("Generated vX")
    and the edition URN are GONE from this reader-visible page — edition
    identity lives on the Your-Edition page. What remains is the minimal
    traditional closing colophon."""
    edition_title = html.escape(edition.get("title_full", edition.get("title", "Untitled")))
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>Colophon</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="backmatter">
  <section class="backmatter-page colophon-end" epub:type="backmatter">
    <h1 class="backmatter-title">{edition_title}</h1>
    <p class="colophon-publisher">Published by YHWH Ya&#x2019; Way Editions</p>
    <p class="colophon-closing">Prepared for study and devotion. <em>Soli Deo Gloria.</em></p>
  </section>
</body>
</html>
"""


TOPICAL_INDEX_SOURCES = ("both", "naves", "torrey")


def _norm_topic(t: str) -> str:
    """Casefold + collapse whitespace + strip edge punctuation. No comma split
    (Torrey's subtopics like 'Affliction, Consolation Under' must stay distinct)."""
    t = " ".join(t.casefold().split())
    return t.strip(" .;:-’'\"")


def _title_topic(name: str) -> str:
    """Title-case an ALL-CAPS / mixed Nave's topic for display: capitalize the
    first letter of each space- and hyphen-delimited segment, lowercase the rest
    (so 'ABED-NEGO' -> 'Abed-Nego', "GOD'S WILL" -> "God's Will")."""

    def cap(seg: str) -> str:
        return seg[:1].upper() + seg[1:].lower() if seg else seg

    words = ["-".join(cap(s) for s in word.split("-")) for word in name.split(" ")]
    return " ".join(words)


def build_topic_index(naves, canon_books, book_order: dict[str, int]) -> list[tuple[str, list[tuple[str, int, int]]]]:
    """Invert Nave's into a back-of-book topical index.

    Returns ``[(topic, [(book, ch, vs), …]), …]`` — topics alphabetical, each
    topic's refs deduped and in canonical order. ``canon_books`` (a set, or None
    for "all books") filters refs to the edition's canon; a topic with no
    in-canon ref is omitted. ``book_order`` maps a book code to its canonical
    index (from ``config.load_books()``). ``naves`` is a ``sources.NavesTopical``
    (injected for testing)."""
    index: list[tuple[str, list[tuple[str, int, int]]]] = []
    for topic in naves.topics():
        seen: set[tuple[str, int, int]] = set()
        refs: list[tuple[str, int, int]] = []
        for hit in naves.verses_for(topic):
            key = (hit.target_book, hit.target_chapter, hit.target_verse)
            if canon_books is not None and key[0] not in canon_books:
                continue
            if key in seen:
                continue
            seen.add(key)
            refs.append(key)
        if refs:
            refs.sort(key=lambda r: (book_order.get(r[0], 9999), r[1], r[2]))
            index.append((topic, refs))
    return index


def build_merged_topic_index(naves, torrey, canon_books, book_order: dict[str, int]):
    """Merge two topical sources into a tagged back-of-book index.

    Returns ``[(display, tag, [(book, ch, vs), …]), …]`` — sorted alphabetically
    by ``display`` (casefold). ``tag`` is ``"N·T"`` (both works), ``"N"``
    (Nave's only), or ``"T"`` (Torrey only), decided by which side has in-canon
    verses. Topic names are matched by ``_norm_topic`` (casefold); a topic with no
    in-canon ref is omitted. ``naves`` / ``torrey`` are ``sources.NavesTopical`` /
    ``TorreyTopical`` (or None if a source is unavailable)."""

    def collect(src):
        groups: dict[str, dict] = {}
        if src is None:
            return groups
        for topic in src.topics():
            key = _norm_topic(topic)
            g = groups.setdefault(key, {"names": [], "refs": set()})
            g["names"].append(topic)
            for hit in src.verses_for(topic):
                ref = (hit.target_book, hit.target_chapter, hit.target_verse)
                if canon_books is not None and ref[0] not in canon_books:
                    continue
                g["refs"].add(ref)
        return groups

    nav_g, tor_g = collect(naves), collect(torrey)
    out: list[tuple[str, str, list[tuple[str, int, int]]]] = []
    # mint-11 P5: iterate keys in sorted order so two distinct topic keys that
    # render to the same display string append in a stable order — without this
    # the set-iteration order is PYTHONHASHSEED-dependent and topical.xhtml is
    # not byte-stable across process launches.
    for key in sorted(set(nav_g) | set(tor_g)):
        nav_refs = nav_g.get(key, {}).get("refs", set())
        tor_refs = tor_g.get(key, {}).get("refs", set())
        all_refs = sorted(nav_refs | tor_refs, key=lambda r: (book_order.get(r[0], 9999), r[1], r[2]))
        if not all_refs:
            continue
        tag = "N·T" if (nav_refs and tor_refs) else "N" if nav_refs else "T"
        if key in tor_g:
            display = sorted(tor_g[key]["names"])[0]  # Torrey is already Title Case
        else:
            display = _title_topic(sorted(nav_g[key]["names"])[0])
        out.append((display, tag, all_refs))
    # mint-11 P5: tiebreak casefold-equal display names by the raw display string
    # so the final order is fully deterministic (Python's sort is stable, so two
    # entries with an equal casefold key would otherwise keep their append order,
    # which the sorted() loop above now also pins).
    out.sort(key=lambda e: (e[0].casefold(), e[0]))
    return out


_NAVES_TOPICAL_INTRO = (
    "A concordance of verses by theme, after Nave&#x2019;s Topical Bible "
    "(Orville J. Nave, 1896; public domain). Topics are listed alphabetically; "
    "only verses present in this edition are shown."
)
_TORREY_TOPICAL_INTRO = (
    "A concordance of verses by theme, after Torrey&#x2019;s New Topical Textbook "
    "(R.A. Torrey, 1897; public domain). Topics are listed alphabetically; "
    "only verses present in this edition are shown."
)
_MERGED_TOPICAL_INTRO = (
    "A concordance of verses by theme, drawn from Nave&#x2019;s Topical Bible "
    "(Orville J. Nave, 1896) and Torrey&#x2019;s New Topical Textbook "
    "(R.A. Torrey, 1897), both public domain. Topics marked (N·T) are "
    "treated by both works; (N) Nave&#x2019;s only; (T) Torrey only. Only verses "
    "present in this edition are shown."
)


def render_topical_index_page(topic_index, book_abbrev, *, intro: str = _NAVES_TOPICAL_INTRO) -> str:
    """Render a single-source topical-index back-matter XHTML. ``topic_index`` is
    the output of ``build_topic_index``; ``book_abbrev(code) -> str`` formats a book
    code for a verse reference (e.g. ``gen`` → ``Gen``). ``intro`` is the source
    attribution sentence (defaults to Nave's — byte-stable for existing builds)."""
    rows: list[str] = []
    for topic, refs in topic_index:
        ref_str = "; ".join(f"{book_abbrev(b)} {c}:{v}" for b, c, v in refs)
        rows.append(f'    <p class="topic-entry"><span class="topic-name">{html.escape(topic)}</span> {ref_str}</p>')
    body = "\n".join(rows) if rows else '    <p class="topic-entry">This edition carries no topical index.</p>'
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>Topical Index</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="backmatter">
  <section class="backmatter-page topical-index" epub:type="backmatter">
    <h1 class="backmatter-title">Topical Index</h1>
    <p class="topical-intro">{intro}</p>
{body}
  </section>
</body>
</html>
"""


def render_merged_topical_index_page(merged_index, book_abbrev) -> str:
    """Render the merged Nave's + Torrey topical index. ``merged_index`` is the
    output of ``build_merged_topic_index`` — ``[(display, tag, refs), …]``."""
    rows: list[str] = []
    for topic, tag, refs in merged_index:
        ref_str = "; ".join(f"{book_abbrev(b)} {c}:{v}" for b, c, v in refs)
        rows.append(
            f'    <p class="topic-entry"><span class="topic-name">{html.escape(topic)}</span>'
            f' <span class="topic-src">({html.escape(tag)})</span> {ref_str}</p>'
        )
    body = "\n".join(rows) if rows else '    <p class="topic-entry">This edition carries no topical index.</p>'
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>Topical Index</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="backmatter">
  <section class="backmatter-page topical-index" epub:type="backmatter">
    <h1 class="backmatter-title">Topical Index</h1>
    <p class="topical-intro">{_MERGED_TOPICAL_INTRO}</p>
{body}
  </section>
</body>
</html>
"""


def _write_topical_page(tmp, mode, canon_books, book_order, *, naves, torrey) -> bool:
    """Write ``topical.xhtml`` per ``mode`` (naves | torrey | both; default both).
    Returns True if a page was written. Degrades gracefully when a source is
    unavailable: 'both' falls back to whichever single source is present; if
    neither is present, nothing is written and False is returned."""
    mode = (mode or "both").strip().lower()
    out = tmp / "topical.xhtml"

    def write_single(src, intro):
        idx = build_topic_index(src, canon_books, book_order)
        out.write_text(render_topical_index_page(idx, book_abbrev=str.title, intro=intro), encoding="utf-8")
        return True

    if mode == "naves":
        return write_single(naves, _NAVES_TOPICAL_INTRO) if naves is not None else False
    if mode == "torrey":
        return write_single(torrey, _TORREY_TOPICAL_INTRO) if torrey is not None else False
    # both (default)
    if naves is not None and torrey is not None:
        merged = build_merged_topic_index(naves, torrey, canon_books, book_order)
        out.write_text(render_merged_topical_index_page(merged, book_abbrev=str.title), encoding="utf-8")
        return True
    if naves is not None:
        return write_single(naves, _NAVES_TOPICAL_INTRO)
    if torrey is not None:
        return write_single(torrey, _TORREY_TOPICAL_INTRO)
    return False


EINK_STUDY_BACKMATTER_FILE = "index_split_900.html"


def render_eink_study_backmatter_page(edition: dict, entries: list[tuple]) -> str:
    """Render the Kobo Study Notes glossary (K-R9).

    ``entries`` is ``[(sort_key, book_code, aside_html), …]`` already sorted.
    Grouped by book with an ``h2`` per canon book that has notes in this edition."""
    from scripts.core import config as _config

    books_by_code = _config.books_by_code()
    edition_title = html.escape(edition.get("title_full", edition.get("title", "Study Bible")))
    body_parts = [
        '<section class="study-notes-index" epub:type="backmatter">',
        "<h1>Study Notes</h1>",
        '<p class="study-notes-lead">Tap a study badge († or ◇) in the text to jump here. '
        "Each entry ends with a ↩ link back to the verse you were reading. "
        "Translation links still open as quick popups.</p>",
    ]
    current_code: str | None = None
    for _sort_key, code, aside_html in entries:
        if code != current_code:
            current_code = code
            book_title = html.escape((books_by_code.get(code) or {}).get("title") or code.upper())
            body_parts.append(f'<h2 class="study-book-head">{book_title}</h2>')
        body_parts.append(aside_html)
    body_parts.append("</section>")
    body = "\n".join(body_parts)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>Study Notes</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="backmatter">
{body}
</body>
</html>
"""


def inject_eink_study_backmatter(tmp: Path, edition: dict, entries: list[tuple[tuple, str, str]]) -> dict:
    """Write the Study Notes glossary and register it in OPF + nav (K-R9).

    Runs after body transforms, immediately before ``inject_back_matter`` so
    spine order is: scripture → study notes → sources → … → colophon.
    ``apply_file_split`` may fan ``index_split_900.html`` into smaller pieces."""
    if not entries:
        return {"entries_written": 0, "skipped_reason": "no study entries"}
    ordered = sorted(entries, key=lambda row: row[0])
    out_name = EINK_STUDY_BACKMATTER_FILE
    out_path = tmp / out_name
    out_path.write_text(render_eink_study_backmatter_page(edition, ordered), encoding="utf-8")

    opf_path = tmp / "content.opf"
    if opf_path.is_file():
        opf = opf_path.read_text(encoding="utf-8")
        if out_name not in opf:
            opf = opf.replace(
                "</manifest>",
                f'\n    <item id="studynotes" href="{out_name}" media-type="application/xhtml+xml"/>\n  </manifest>',
            )
            opf = opf.replace("</spine>", '\n    <itemref idref="studynotes"/>\n  </spine>')
            opf_path.write_text(opf, encoding="utf-8")

    nav_path = tmp / "nav.xhtml"
    if nav_path.is_file():
        nav = nav_path.read_text(encoding="utf-8")
        if f'href="{out_name}"' not in nav:
            study_li = f'\n      <li><a href="{out_name}">Study Notes</a></li>'
            nav = nav.replace("</ol>", study_li + "\n    </ol>", 1)
            nav_path.write_text(nav, encoding="utf-8")

    return {"entries_written": len(ordered), "output_file": out_name, "skipped_reason": None}


def inject_back_matter(tmp: Path, edition: dict, canon_books: set[str] | None = None) -> None:
    """Write sources.xhtml, reftables.xhtml, topical.xhtml, colophonend.xhtml and
    register each in content.opf (manifest + spine, appended at END in order) and
    nav.xhtml (TOC entries appended at the END of the main <ol>).

    Spine order guaranteed: backsources → backreftables → backtopical →
    backcolophon. backcolophon is the very last spine item.
    Guards against double-injection via per-file href check.

    K-R2-6: the closing colophon is option-gated — ``closing_colophon: false``
    drops the page entirely (no file, no manifest/spine/nav entries); the
    default keeps the minimal traditional closing page."""
    closing_colophon = edition.get("closing_colophon", True) is not False
    # --- Write the back-matter XHTML files (sources → reftables → topical → colophon) ---
    (tmp / "sources.xhtml").write_text(render_sources_page(), encoding="utf-8")
    (tmp / "reftables.xhtml").write_text(render_reference_tables_page(), encoding="utf-8")
    # §5.4 #4 — topical index (Nave's + Torrey), filtered to this edition's canon.
    from scripts.core import config as _config
    from scripts.core import sources as _sources

    def _load(loader):
        try:
            return loader()
        except _sources.SourceMissingError:
            return None

    book_order = {b["code"]: i for i, b in enumerate(_config.load_books())}
    topical_ok = _write_topical_page(
        tmp,
        edition.get("topical_index_source"),
        canon_books,
        book_order,
        naves=_load(_sources.naves_topical),
        torrey=_load(_sources.torrey_topical),
    )
    if closing_colophon:
        (tmp / "colophonend.xhtml").write_text(render_closing_colophon_page(edition), encoding="utf-8")

    # --- Patch content.opf ---
    opf_path = tmp / "content.opf"
    if opf_path.is_file():
        opf = opf_path.read_text(encoding="utf-8")

        # Manifest: append all three items before </manifest>
        new_manifest_items = ""
        if "sources.xhtml" not in opf:
            new_manifest_items += (
                '\n    <item id="backsources" href="sources.xhtml" media-type="application/xhtml+xml"/>'
            )
        if "reftables.xhtml" not in opf:
            new_manifest_items += (
                '\n    <item id="backreftables" href="reftables.xhtml" media-type="application/xhtml+xml"/>'
            )
        if topical_ok and "topical.xhtml" not in opf:
            new_manifest_items += (
                '\n    <item id="backtopical" href="topical.xhtml" media-type="application/xhtml+xml"/>'
            )
        if closing_colophon and "colophonend.xhtml" not in opf:
            new_manifest_items += (
                '\n    <item id="backcolophon" href="colophonend.xhtml" media-type="application/xhtml+xml"/>'
            )
        if new_manifest_items:
            opf = opf.replace("</manifest>", new_manifest_items + "\n  </manifest>")

        # Spine: append itemrefs before </spine> (sources → reftables → topical → colophon)
        new_spine_items = ""
        if 'idref="backsources"' not in opf:
            new_spine_items += '\n    <itemref idref="backsources"/>'
        if 'idref="backreftables"' not in opf:
            new_spine_items += '\n    <itemref idref="backreftables"/>'
        if topical_ok and 'idref="backtopical"' not in opf:
            new_spine_items += '\n    <itemref idref="backtopical"/>'
        if closing_colophon and 'idref="backcolophon"' not in opf:
            new_spine_items += '\n    <itemref idref="backcolophon"/>'
        if new_spine_items:
            opf = opf.replace("</spine>", new_spine_items + "\n  </spine>")

        opf_path.write_text(opf, encoding="utf-8")

    # --- Patch nav.xhtml ---
    nav_path = tmp / "nav.xhtml"
    if nav_path.is_file():
        nav = nav_path.read_text(encoding="utf-8")
        new_nav_items = ""
        if 'href="sources.xhtml"' not in nav:
            new_nav_items += '\n      <li><a href="sources.xhtml">Sources &amp; Acknowledgments</a></li>'
        if 'href="reftables.xhtml"' not in nav:
            new_nav_items += '\n      <li><a href="reftables.xhtml">Reference Tables</a></li>'
        if topical_ok and 'href="topical.xhtml"' not in nav:
            new_nav_items += '\n      <li><a href="topical.xhtml">Topical Index</a></li>'
        if closing_colophon and 'href="colophonend.xhtml"' not in nav:
            new_nav_items += '\n      <li><a href="colophonend.xhtml">Colophon</a></li>'
        if new_nav_items:
            nav = nav.replace("</ol>", new_nav_items + "\n    </ol>", 1)
            nav_path.write_text(nav, encoding="utf-8")


def render_reading_plans_page(edition: dict, plans: list) -> str:
    """Render the XHTML page bundling every enabled plan's day-by-day
    schedule.

    `plans` is a list of `ReadingPlan` records (from
    scripts.core.reading_plans.load_plan); the caller is responsible
    for filtering to the edition's `enabled_reading_plans` list. The
    output is the full XHTML document including doctype + head, ready
    to write to ``tmp/reading_plans.xhtml``.

    Verse refs render as plain text (no in-EPUB deep links for v1);
    a future ψ.19.2 could resolve refs to chapter HTML anchors.
    """
    edition_title = edition.get("title", "Untitled")
    sections = []
    for plan in plans:
        entry_lines = []
        for entry in plan.entries:
            verses_text = " · ".join(_xml_escape_text(v) for v in entry.verses)
            entry_lines.append(
                f'      <li class="reading-plan-day">'
                f'<span class="reading-plan-day-number">Day {entry.day}</span>'
                f' — <span class="reading-plan-refs">{verses_text}</span>'
                f"</li>"
            )
        entries_html = "\n".join(entry_lines)
        description_html = ""
        if plan.description:
            # Trim to first paragraph for the section header; full
            # description may be long-form Markdown-style.
            first_para = plan.description.strip().split("\n\n")[0]
            description_html = f'<p class="reading-plan-description">{_xml_escape_text(first_para)}</p>'
        sections.append(
            f'<section class="reading-plan" id="reading-plan-{_xml_escape_text(plan.id)}">\n'
            f'  <h2 class="reading-plan-title">{_xml_escape_text(plan.label)}</h2>\n'
            f"  {description_html}\n"
            f'  <ol class="reading-plan-days">\n'
            f"{entries_html}\n"
            f"  </ol>\n"
            f"</section>"
        )
    body_sections = (
        "\n\n".join(sections)
        if sections
        else ('<p class="reading-plans-empty">No reading plans enabled for this edition.</p>')
    )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>Reading Plans</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="frontmatter">
  <section class="reading-plans-page" epub:type="frontmatter">
    <h1 class="reading-plans-page-title">Reading Plans</h1>
    <p class="reading-plans-page-intro">Daily reading schedules for <em>{_xml_escape_text(edition_title)}</em>. Verse references follow the canonical book / chapter / verse format used throughout the apparatus.</p>
    <hr class="reading-plans-rule"/>
{body_sections}
  </section>
</body>
</html>
"""


def inject_reading_plans_page(tmp: Path, edition: dict) -> dict:
    """Render + write the reading-plans page; patch OPF + nav.xhtml.

    Returns ``{"plans_written": int, "skipped_reason": str | None}``
    so the build_one stats accumulator can record what happened.
    No-op when:
      - the edition's `enabled_reading_plans` is empty / absent
      - none of the listed plan ids resolve to a real file (the
        validator usually catches this on save, but the build is
        defensive)
    """
    enabled_ids = list(edition.get("enabled_reading_plans") or [])
    if not enabled_ids:
        return {"plans_written": 0, "skipped_reason": "no plans enabled"}

    # Lazy import — keeps the module's import surface clean for
    # consumers that don't trigger the build pipeline.
    from scripts.core.reading_plans import load_plan

    plans = []
    for pid in enabled_ids:
        try:
            plan = load_plan(pid)
        except ValueError:
            continue
        if plan is None:
            continue
        plans.append(plan)
    if not plans:
        return {"plans_written": 0, "skipped_reason": "no plans loaded"}

    html = render_reading_plans_page(edition, plans)
    out_path = tmp / "reading_plans.xhtml"
    out_path.write_text(html, encoding="utf-8")

    # Patch OPF — add manifest item + insert into spine after the
    # copyright page (so the order is title → copyright → reading
    # plans → main matter).
    opf_path = tmp / "content.opf"
    if opf_path.is_file():
        opf = opf_path.read_text(encoding="utf-8")
        if "reading_plans.xhtml" not in opf:
            opf = opf.replace(
                '<item id="copyright" href="copyright.xhtml"',
                '<item id="readingplans" href="reading_plans.xhtml" media-type="application/xhtml+xml"/>\n    '
                '<item id="copyright" href="copyright.xhtml"',
            )
            opf = opf.replace(
                '<itemref idref="copyright"/>',
                '<itemref idref="copyright"/>\n    <itemref idref="readingplans"/>',
            )
            opf_path.write_text(opf, encoding="utf-8")

    # Patch nav.xhtml — append a ToC entry after the Copyright link.
    nav_path = tmp / "nav.xhtml"
    if nav_path.is_file():
        nav = nav_path.read_text(encoding="utf-8")
        if 'href="reading_plans.xhtml"' not in nav:
            anchor = '<li><a href="copyright.xhtml">Copyright &amp; Credits</a></li>'
            if anchor in nav:
                nav = nav.replace(
                    anchor,
                    anchor + '\n      <li><a href="reading_plans.xhtml">Reading Plans</a></li>',
                    1,
                )
                nav_path.write_text(nav, encoding="utf-8")

    return {
        "plans_written": len(plans),
        "skipped_reason": None,
        "plan_ids": [p.id for p in plans],
        "total_days": sum(len(p.entries) for p in plans),
    }
