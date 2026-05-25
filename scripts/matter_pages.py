#!/usr/bin/env python3
"""Front/back-matter EPUB pages — the render_*/inject_* family extracted
(verbatim) from build_edition.py. Each inject_* writes one XHTML page into the
per-edition build tempdir; build_edition.build_one calls the six inject_* here.
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
    version: str,
    *,
    annotation_count: int,
    category_count: int,
) -> str:
    """Render the front colophon XHTML. Identity from ``publishing``
    (_resolve_publishing), NOT the dead content/onix.py TODO_ defaults; counts
    are the edition's REAL computed values (scripts.core.matrix). The long
    description lives on the separate 'About this Edition' page; full source
    credits live in the back-matter 'Sources & Acknowledgments' page — keep
    this page compact."""
    pub = publishing.get("publisher_name") or "YHWH Ya' Way Editions"
    holder = (
        publishing.get("copyright_holder") or (publishing.get("contributor") or {}).get("name") or "Bogdan Zorlescu"
    )
    cyear = str(publishing.get("copyright_year") or "2026")
    edition_title = edition.get("title_full", edition.get("title", "Untitled"))
    edition_subtitle = edition.get("title_subtitle", "")
    edition_urn = f"urn:yhwh:edition:{edition['id']}"
    pub_x = html.escape(pub)
    holder_x = html.escape(holder)
    ann = f"{annotation_count:,}"
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>Colophon</title>
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
    <h2 class="copyright-heading">This Edition</h2>
    <p><strong>Edition ID:</strong> {edition_urn}<br/>
       <strong>Publisher:</strong> {pub_x}<br/>
       <strong>Build:</strong> {html.escape(version)}</p>
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


def inject_copyright_page(tmp: Path, edition: dict, version: str) -> None:
    """Write copyright.xhtml, register it in content.opf (manifest + spine after
    titlepage) and nav.xhtml. Identity from _resolve_publishing; counts from
    scripts.core.matrix (real, per-edition)."""
    from scripts.core import matrix as _matrix

    publishing = _resolve_publishing(edition)
    edition_id = edition["id"]
    annotation_count = _matrix.total_for_edition(edition_id)
    category_count = sum(1 for n in _matrix.breakdown_by_category(edition_id).values() if n > 0)

    # 1) Write the page
    html_text = render_copyright_page(
        edition, publishing, version, annotation_count=annotation_count, category_count=category_count
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


def inject_dedication_page(tmp: Path, edition: dict, version: str) -> None:
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
    drops its symbol from the guide."""
    from scripts.core import config, matrix as _matrix

    present = _matrix.breakdown_by_category(edition_id)  # {cat_id: count}
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


def render_symbol_legend_page(edition: dict, categories: list[dict], version: str) -> str:
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


def inject_symbol_legend_page(tmp: Path, edition: dict, version: str) -> None:
    """Write legend.xhtml, register it in the OPF (manifest + spine right after
    copyright) and add a nav.xhtml TOC entry (also renaming the copyright TOC
    label to 'Colophon' to match its page title)."""
    categories = _legend_categories_for_edition(edition["id"])
    html_text = render_symbol_legend_page(edition, categories, version)
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
                '<li><a href="copyright.xhtml">Colophon</a></li>\n'
                '      <li><a href="legend.xhtml">A Guide to the Notes</a></li>',
                1,
            )
            nav_path.write_text(nav, encoding="utf-8")


def _about_specs_for_edition(edition_id: str) -> dict:
    """Compose the data dict for render_about_page from this edition's config.

    Returns::

        {
          "canon_label":        str,           # short canon name, e.g. "Catholic"
          "book_count":         int,           # books in the edition's canon
          "annotation_count":   int,           # total notes (matrix)
          "category_count":     int,           # number of non-zero categories
          "categories":         list[dict],    # [{label, count}, ...] sort_order
          "witness_labels":     list[str],     # popup language human labels
          "theme":              str,
          "description":        str,           # empty string when absent
        }
    """
    from scripts.core import config as _cfg
    from scripts.core import matrix as _matrix
    from scripts.core.popup_versions import VERSION_REGISTRY, resolve_version_id

    edition = _cfg.editions_by_id()[edition_id]

    # Canon name + book count
    canon_id = edition.get("canon") or "protestant"
    all_canons = load_canons()
    canon_info = all_canons.get(canon_id, {})
    # Use full label but strip any parenthetical annotation comment after '('
    raw_label = canon_info.get("label") or canon_id.replace("-", " ").title()
    canon_label = raw_label.split("(")[0].strip().rstrip(",")
    book_count = len(canon_info.get("books") or [])

    # Annotation counts from matrix
    annotation_count = _matrix.total_for_edition(edition_id)
    breakdown = _matrix.breakdown_by_category(edition_id)

    # Categories: sorted by sort_order, count > 0 only
    cats_meta = sorted(_cfg.load_categories(), key=lambda c: c.get("sort_order", 999))
    categories = [
        {"label": c.get("label", c["id"]), "count": breakdown.get(c["id"], 0)}
        for c in cats_meta
        if breakdown.get(c["id"], 0) > 0
    ]
    category_count = len(categories)

    # Popup witness labels: resolve legacy aliases → registry labels
    popup_raw = edition.get("popup_languages_default") or []
    witness_labels: list[str] = []
    seen_vids: set[str] = set()
    for tok in popup_raw:
        vid = resolve_version_id(str(tok))
        if vid and vid not in seen_vids:
            seen_vids.add(vid)
            label = VERSION_REGISTRY.get(vid, {}).get("label") or vid
            witness_labels.append(label)

    return {
        "canon_label": canon_label,
        "book_count": book_count,
        "annotation_count": annotation_count,
        "category_count": category_count,
        "categories": categories,
        "witness_labels": witness_labels,
        "theme": str(edition.get("theme") or ""),
        "description": str(edition.get("description") or ""),
    }


def render_about_page(edition: dict, specs: dict, version: str) -> str:
    """Render the 'About this Edition' XHTML.

    ``specs`` is the dict from ``_about_specs_for_edition`` (or a synthetic
    dict for unit tests). All user-facing text is html.escape'd. The page
    uses a ``<section class="about-page">`` and mirrors the legend-page
    structural style."""
    edition_title = edition.get("title_full", edition.get("title", "Untitled"))

    # Canon line
    canon_line = (
        f'<p class="about-canon">'
        f"<strong>Canon:</strong> {html.escape(specs['canon_label'])}"
        f" — {specs['book_count']:,} books</p>"
    )

    # Annotation summary line
    ann_line = (
        f'<p class="about-annotations">'
        f"<strong>Annotations:</strong> {specs['annotation_count']:,} notes"
        f" across {specs['category_count']} categories</p>"
    )

    # Per-category list
    cat_items = []
    for cat in specs.get("categories") or []:
        cat_items.append(f'<li class="about-cat-item">{html.escape(cat["label"])} — {cat["count"]:,} notes</li>')
    cats_block = (
        ('<ul class="about-cat-list">\n    ' + "\n    ".join(cat_items) + "\n  </ul>")
        if cat_items
        else '<p class="about-cat-empty">No annotations in this edition.</p>'
    )

    # Witnesses line (omit if empty list)
    witnesses = specs.get("witness_labels") or []
    if witnesses:
        witnesses_line = (
            f'<p class="about-witnesses">'
            f"<strong>Verse-popup witnesses:</strong> "
            f"{html.escape(', '.join(witnesses))}</p>"
        )
    else:
        witnesses_line = ""

    # Theme line
    theme_val = specs.get("theme") or ""
    theme_line = f'<p class="about-theme"><strong>Theme:</strong> {html.escape(theme_val)}</p>' if theme_val else ""

    # Optional description paragraph
    desc = specs.get("description") or ""
    desc_para = f'<p class="about-description">{html.escape(desc)}</p>' if desc else ""

    body_parts = [canon_line, ann_line, cats_block]
    if witnesses_line:
        body_parts.append(witnesses_line)
    if theme_line:
        body_parts.append(theme_line)
    if desc_para:
        body_parts.append(desc_para)

    body = "\n  ".join(body_parts)

    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>About this Edition</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="frontmatter">
  <section class="about-page" epub:type="frontmatter">
    <h1 class="about-title">About this Edition</h1>
    <p class="about-edition-name"><em>{html.escape(edition_title)}</em></p>
  {body}
  </section>
</body>
</html>
"""


def inject_about_page(tmp: Path, edition: dict, version: str) -> None:
    """Write about.xhtml and register it in OPF (manifest + spine after legend)
    and nav.xhtml (TOC entry after legend). Guard against double-injection."""
    specs = _about_specs_for_edition(edition["id"])
    html_text = render_about_page(edition, specs, version)
    (tmp / "about.xhtml").write_text(html_text, encoding="utf-8")

    opf_path = tmp / "content.opf"
    if opf_path.is_file():
        opf = opf_path.read_text(encoding="utf-8")
        if "about.xhtml" not in opf:
            _anchor_m = '<item id="legend" href="legend.xhtml" media-type="application/xhtml+xml"/>'
            _new = opf.replace(
                _anchor_m,
                _anchor_m + '\n    <item id="about" href="about.xhtml" media-type="application/xhtml+xml"/>',
            )
            if _new == opf:
                raise RuntimeError(f"OPF manifest anchor not found: {_anchor_m!r}")
            opf = _new
            _spine_anchor = '<itemref idref="legend"/>'
            _new = opf.replace(
                _spine_anchor,
                _spine_anchor + '\n    <itemref idref="about"/>',
            )
            if _new == opf:
                raise RuntimeError(f"OPF spine anchor not found: {_spine_anchor!r}")
            opf = _new
            opf_path.write_text(opf, encoding="utf-8")

    nav_path = tmp / "nav.xhtml"
    if nav_path.is_file():
        nav = nav_path.read_text(encoding="utf-8")
        if 'href="about.xhtml"' not in nav:
            nav = nav.replace(
                '<li><a href="legend.xhtml">A Guide to the Notes</a></li>',
                '<li><a href="legend.xhtml">A Guide to the Notes</a></li>\n'
                '      <li><a href="about.xhtml">About this Edition</a></li>',
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


def render_sources_page(version: str) -> str:
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


def render_reference_tables_page(version: str) -> str:
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


def render_closing_colophon_page(edition: dict, version: str) -> str:
    """Render the Closing Colophon XHTML — the genuinely last page of the EPUB."""
    edition_title = html.escape(edition.get("title_full", edition.get("title", "Untitled")))
    edition_id = html.escape(edition.get("id", "unknown"))
    urn = f"urn:yhwh:edition:{edition_id}"
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
    <p class="colophon-version">Generated {html.escape(version)}</p>
    <p class="colophon-urn"><code>{html.escape(urn)}</code></p>
    <p class="colophon-closing">Prepared for study and devotion. <em>Soli Deo Gloria.</em></p>
  </section>
</body>
</html>
"""


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


def render_topical_index_page(version: str, topic_index, book_abbrev) -> str:
    """Render the Nave's topical-index back-matter XHTML. ``topic_index`` is the
    output of ``build_topic_index``; ``book_abbrev(code) -> str`` formats a book
    code for a verse reference (e.g. ``gen`` → ``Gen``)."""
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
    <p class="topical-intro">A concordance of verses by theme, after Nave&#x2019;s Topical Bible (Orville J. Nave, 1896; public domain). Topics are listed alphabetically; only verses present in this edition are shown.</p>
{body}
  </section>
</body>
</html>
"""


def inject_back_matter(tmp: Path, edition: dict, version: str, canon_books: set[str] | None = None) -> None:
    """Write sources.xhtml, reftables.xhtml, topical.xhtml, colophonend.xhtml and
    register each in content.opf (manifest + spine, appended at END in order) and
    nav.xhtml (TOC entries appended at the END of the main <ol>).

    Spine order guaranteed: backsources → backreftables → backtopical →
    backcolophon. backcolophon is the very last spine item.
    Guards against double-injection via per-file href check."""
    # --- Write the back-matter XHTML files (sources → reftables → topical → colophon) ---
    (tmp / "sources.xhtml").write_text(render_sources_page(version), encoding="utf-8")
    (tmp / "reftables.xhtml").write_text(render_reference_tables_page(version), encoding="utf-8")
    # §5.4 #4 — Nave's topical index, filtered to this edition's canon.
    from scripts.core import config as _config
    from scripts.core import sources as _sources

    topical_ok = False
    try:
        naves = _sources.naves_topical()
        book_order = {b["code"]: i for i, b in enumerate(_config.load_books())}
        topic_index = build_topic_index(naves, canon_books, book_order)
        (tmp / "topical.xhtml").write_text(
            render_topical_index_page(version, topic_index, book_abbrev=str.title), encoding="utf-8"
        )
        topical_ok = True
    except _sources.SourceMissingError:
        topical_ok = False  # Nave's not cached in this env — skip the page entirely
    (tmp / "colophonend.xhtml").write_text(render_closing_colophon_page(edition, version), encoding="utf-8")

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
        if "colophonend.xhtml" not in opf:
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
        if 'idref="backcolophon"' not in opf:
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
        if 'href="colophonend.xhtml"' not in nav:
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
