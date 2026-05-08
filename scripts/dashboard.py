#!/usr/bin/env python3
"""
dashboard.py — Generate a single-file HTML report on project state.

Walks ``content/notes/<code>.py`` for every book in the canon and produces a
self-contained ``dashboard.html`` (no external CSS/JS/font dependencies)
showing where the project stands at a glance:

  * Top-line counts: total notes, books-with-notes, chapter coverage, %
  * Kind distribution (bar chart, sourced from kinds.yaml)
  * Per-book progress table (notes, %-covered, kind columns)
  * Density heatmap (SVG): book × chapter, hover for per-cell counts
  * Coverage gaps: books with zero notes

Examples:
    python3 scripts/dashboard.py
        # writes ./dashboard.html

    python3 scripts/dashboard.py -o /tmp/state.html
        # custom output path

    python3 scripts/dashboard.py --quiet
        # suppress the "wrote …" log line

Exit codes:
    0  ok
    2  setup error (missing config, parse failure)
"""

import argparse
import html
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402
from scripts.core.notes_io import load_notes

NOTES_DIR = REPO_ROOT / "content" / "notes"
EPUB_DIR = REPO_ROOT / "epub_working"
DEFAULT_OUT = REPO_ROOT / "dashboard.html"
DEFAULT_HEATMAP_OUT = REPO_ROOT / "coverage_heatmap.html"


# ----------------------------------------------------------------------
# Note loading (AST, no exec) — same pattern as note_quality.py
# ----------------------------------------------------------------------



# ----------------------------------------------------------------------
# Stats
# ----------------------------------------------------------------------


def gather_stats(books, kinds):
    per_book = {}
    per_kind: Counter = Counter()
    chapter_density: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))

    total_notes = 0
    parse_failures = []

    for book in books:
        code = book["code"]
        path = NOTES_DIR / f"{code}.py"
        if not path.is_file():
            notes = []
        else:
            notes = load_notes(path)
            if notes is None:
                parse_failures.append(code)
                notes = []

        chapters_touched: set[int] = set()
        kinds_count: Counter = Counter()
        attributed_count = 0
        for tup in notes:
            if not isinstance(tup, tuple) or len(tup) < 5:
                continue
            ch, _v, _suffix, _anchor, kind = tup[:5]
            chapters_touched.add(ch)
            kinds_count[kind] += 1
            per_kind[kind] += 1
            chapter_density[code][ch] += 1
            # Attribution presence (v28a-4 schema): 9th tuple field, non-empty string
            if (
                len(tup) >= 9
                and isinstance(tup[8], str)
                and tup[8].strip()
            ):
                attributed_count += 1

        n = sum(kinds_count.values())
        per_book[code] = {
            "code": code,
            "title": book.get("title", code),
            "ch_count": book.get("ch_count", 0),
            "note_count": n,
            "attributed": attributed_count,
            "kinds": dict(kinds_count),
            "chapters_touched": len(chapters_touched),
            "pct_covered": (len(chapters_touched) / book["ch_count"] * 100) if book.get("ch_count") else 0.0,
        }
        total_notes += n

    return {
        "total_notes": total_notes,
        "per_book": per_book,
        "per_kind": per_kind,
        "chapter_density": chapter_density,
        "books": books,
        "kinds": kinds,
        "parse_failures": parse_failures,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


CH_ID_RE = re.compile(r'id="ch-(b\d+)-c(\d+)"')


def build_chapter_file_index(epub_dir: Path, books) -> dict[tuple[str, int], str]:
    """Map ``(book_code, chapter_num) → filename`` by scanning ``id="ch-bxx-cN"``.

    Used by the heatmap to make cells click-through to the chapter HTML.
    Returns an empty dict if epub_working is unavailable.
    """
    idx: dict[tuple[str, int], str] = {}
    if not epub_dir.is_dir():
        return idx
    bxx_to_code = {b.get("bxx"): b["code"] for b in books if b.get("bxx")}
    for f in sorted(epub_dir.glob("*.html")):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        for m in CH_ID_RE.finditer(text):
            bxx, ch_str = m.group(1), m.group(2)
            code = bxx_to_code.get(bxx)
            if code:
                idx.setdefault((code, int(ch_str)), f.name)
    return idx


# ----------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------

CSS = """
:root {
  --paper: #f5f1e6;
  --paper-2: #ece5d2;
  --rule: #d4c9ad;
  --ink: #2a2520;
  --ink-2: #5d564d;
  --ink-muted: #8a8378;
  --accent: #8b2330;
  --kind-word: #2c4a6e;
  --kind-comm: #3a3a3a;
  --kind-source: #9b7a2b;
  --kind-parallel: #8b2330;
}
* { box-sizing: border-box; }
html { background: var(--paper); }
body {
  margin: 0 auto;
  padding: 3.5rem clamp(1.2rem, 4vw, 4rem) 5rem;
  max-width: 92rem;
  background: var(--paper);
  color: var(--ink);
  font-family: "Iowan Old Style", "Charter", "Palatino Linotype", "Cambria", Georgia, serif;
  font-size: 16px;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}
header.preamble {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 1rem;
  border-bottom: 2px solid var(--ink);
  padding-bottom: 1rem;
  margin-bottom: 2.5rem;
}
header h1 {
  font-size: clamp(1.4rem, 2.4vw, 1.95rem);
  font-weight: 600;
  margin: 0;
  letter-spacing: -0.005em;
}
header .subtitle {
  font-style: italic;
  color: var(--ink-2);
  margin: 0.4rem 0 0;
  font-size: 0.95rem;
}
header .meta {
  font-size: 0.75rem;
  color: var(--ink-muted);
  font-family: "iA Writer Mono", "JetBrains Mono", "SF Mono", ui-monospace, monospace;
  letter-spacing: 0.02em;
}
section { margin: 3rem 0 0; }
section h2 {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--ink-muted);
  margin: 0 0 1.2rem;
  font-weight: 600;
  border-bottom: 1px solid var(--rule);
  padding-bottom: 0.5rem;
}
.summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr));
  gap: 2rem;
}
.stat .num {
  font-size: 2.4rem;
  font-weight: 600;
  color: var(--accent);
  font-variant-numeric: tabular-nums;
  line-height: 1.05;
}
.stat .num .of {
  color: var(--ink-muted);
  font-size: 0.5em;
  font-weight: 500;
}
.stat .lbl {
  font-size: 0.7rem;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-top: 0.4rem;
}
.kind-bars { display: grid; gap: 0.7rem; }
.kind-row {
  display: grid;
  grid-template-columns: 7rem 1fr 6rem;
  align-items: center;
  gap: 1rem;
  font-size: 0.92rem;
}
.kind-row .name { font-weight: 600; }
.kind-row .name .symbol {
  display: inline-block;
  width: 1.4em;
  color: var(--ink-muted);
  text-align: center;
}
.kind-row .bar-track {
  height: 0.65rem;
  background: var(--paper-2);
  border-radius: 1px;
  overflow: hidden;
}
.kind-row .bar { height: 100%; }
.kind-row .pct {
  font-family: "iA Writer Mono", ui-monospace, monospace;
  font-size: 0.78rem;
  color: var(--ink-2);
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.k-word { background: var(--kind-word); }
.k-comm { background: var(--kind-comm); }
.k-source { background: var(--kind-source); }
.k-parallel { background: var(--kind-parallel); }

table.books {
  width: 100%;
  border-collapse: collapse;
  font-family: "iA Writer Mono", "JetBrains Mono", "SF Mono", ui-monospace, monospace;
  font-size: 0.78rem;
  font-variant-numeric: tabular-nums;
}
table.books th {
  text-align: left;
  padding: 0.45rem 0.7rem;
  font-weight: 600;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 0.68rem;
  border-bottom: 1px solid var(--rule);
}
table.books th.num, table.books td.num { text-align: right; }
table.books td {
  padding: 0.4rem 0.7rem;
  border-bottom: 1px solid rgba(212, 201, 173, 0.4);
}
table.books tr:hover td { background: var(--paper-2); }
table.books td.title {
  font-family: "Iowan Old Style", Georgia, serif;
  font-size: 0.88rem;
}
.dim { color: var(--ink-muted); }

.heatmap-wrap {
  overflow-x: auto;
  border: 1px solid var(--rule);
  background: var(--paper);
  padding: 0.8rem;
}
svg.heatmap { display: block; }
.legend {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.74rem;
  font-family: "iA Writer Mono", ui-monospace, monospace;
  color: var(--ink-muted);
  margin: 0.8rem 0 0;
  flex-wrap: wrap;
}
.legend .swatches { display: inline-flex; gap: 1px; }
.legend .swatch { width: 18px; height: 12px; }

ul.gaps {
  padding: 0;
  margin: 0;
  list-style: none;
  columns: 3;
  column-gap: 2rem;
  font-family: "iA Writer Mono", ui-monospace, monospace;
  font-size: 0.8rem;
}
ul.gaps li { padding: 0.2rem 0; break-inside: avoid; }
ul.gaps li .code {
  color: var(--accent);
  font-weight: 600;
  display: inline-block;
  min-width: 3em;
}
ul.gaps li .ch {
  color: var(--ink-muted);
  font-variant-numeric: tabular-nums;
}

footer.colophon {
  margin-top: 4rem;
  padding-top: 1rem;
  border-top: 1px solid var(--rule);
  color: var(--ink-muted);
  font-size: 0.74rem;
  font-family: "iA Writer Mono", ui-monospace, monospace;
}

@media print {
  body { padding: 1.5rem; }
  table.books tr:hover td { background: transparent; }
}
"""


# Sequential warm-paper → oxblood scale, 6 stops.
HEAT_STOPS = ["#ece5d2", "#e8d3b8", "#d39f8e", "#b86a6f", "#9b3e4f", "#8b2330"]


def heat_color(n: int) -> str:
    if n == 0:
        return HEAT_STOPS[0]
    if n == 1:
        return HEAT_STOPS[1]
    if n <= 3:
        return HEAT_STOPS[2]
    if n <= 6:
        return HEAT_STOPS[3]
    if n <= 10:
        return HEAT_STOPS[4]
    return HEAT_STOPS[5]


def render_preamble(stats) -> str:
    return f"""<header class="preamble">
  <div>
    <h1>Ethiopian Bible · Project Dashboard</h1>
    <p class="subtitle">Scholar's Edition · 87-book canon · live state of <code>content/notes/</code></p>
  </div>
  <div class="meta">{html.escape(stats['generated_at'])}</div>
</header>"""


def render_summary(stats) -> str:
    total = stats["total_notes"]
    n_books = len(stats["books"])
    n_books_with = sum(1 for b in stats["per_book"].values() if b["note_count"] > 0)
    total_chs = sum(b.get("ch_count", 0) for b in stats["books"])
    chs_touched = sum(b["chapters_touched"] for b in stats["per_book"].values())
    pct = (chs_touched / total_chs * 100) if total_chs else 0.0
    # Attribution coverage (v28a-4 schema)
    total_attributed = sum(b.get("attributed", 0) for b in stats["per_book"].values())
    attr_pct = (total_attributed / total * 100) if total else 0.0
    return f"""<section>
  <div class="summary">
    <div class="stat"><div class="num">{total:,}</div><div class="lbl">total notes</div></div>
    <div class="stat"><div class="num">{n_books_with}<span class="of">/{n_books}</span></div><div class="lbl">books with notes</div></div>
    <div class="stat"><div class="num">{chs_touched:,}<span class="of">/{total_chs:,}</span></div><div class="lbl">chapters touched</div></div>
    <div class="stat"><div class="num">{pct:.1f}%</div><div class="lbl">canon coverage</div></div>
    <div class="stat"><div class="num">{attr_pct:.1f}%</div><div class="lbl">attribution coverage</div></div>
  </div>
</section>"""


def render_kind_breakdown(stats) -> str:
    per_kind = stats["per_kind"]
    total = sum(per_kind.values())
    if total == 0:
        return ""
    kind_meta = {k["code"]: k for k in stats["kinds"]}
    rows = []
    for kind in sorted(per_kind, key=lambda k: -per_kind[k]):
        n = per_kind[kind]
        pct = n / total * 100
        meta = kind_meta.get(kind, {})
        sym = html.escape(meta.get("symbol", "·"))
        label = html.escape(meta.get("label", kind))
        klass = f"k-{html.escape(kind)}"
        rows.append(
            f'<div class="kind-row">'
            f'<div class="name"><span class="symbol">{sym}</span>'
            f'{html.escape(kind)} <span class="dim">· {label}</span></div>'
            f'<div class="bar-track"><div class="bar {klass}" style="width:{pct:.1f}%"></div></div>'
            f'<div class="pct">{n:,} · {pct:.1f}%</div>'
            f"</div>"
        )
    return (
        '<section><h2>Kind distribution</h2>'
        '<div class="kind-bars">' + "\n".join(rows) + "</div></section>"
    )


def render_book_table(stats) -> str:
    pb = stats["per_book"]
    nonzero = [c for c, b in pb.items() if b["note_count"] > 0]
    nonzero.sort(key=lambda c: -pb[c]["note_count"])
    kind_codes = [k["code"] for k in stats["kinds"]]
    th_kinds = "".join(f'<th class="num">{html.escape(k)}</th>' for k in kind_codes)

    rows = []
    for code in nonzero:
        b = pb[code]
        density = b["note_count"] / b["ch_count"] if b["ch_count"] else 0
        kind_cells = "".join(
            (
                f'<td class="num">{b["kinds"][k]}</td>'
                if b["kinds"].get(k)
                else '<td class="num dim">—</td>'
            )
            for k in kind_codes
        )
        rows.append(
            f"<tr>"
            f'<td>{html.escape(code)}</td>'
            f'<td class="title">{html.escape(b["title"])}</td>'
            f'<td class="num">{b["ch_count"]}</td>'
            f'<td class="num">{b["chapters_touched"]}/{b["ch_count"]} '
            f'<span class="dim">({b["pct_covered"]:.0f}%)</span></td>'
            f'<td class="num">{b["note_count"]}</td>'
            f'<td class="num">{density:.1f}</td>'
            f"{kind_cells}</tr>"
        )

    return (
        '<section>'
        f'<h2>Per-book progress · {len(nonzero)} books with notes</h2>'
        '<table class="books"><thead><tr>'
        '<th>code</th><th>title</th>'
        '<th class="num">chs</th><th class="num">covered</th>'
        '<th class="num">notes</th><th class="num">/ch</th>'
        f"{th_kinds}"
        "</tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table></section>"
    )


def render_heatmap(stats, chapter_files: dict | None = None, link_prefix: str = "") -> str:
    pb = stats["per_book"]
    cd = stats["chapter_density"]
    books_with = [b for b in stats["books"] if pb[b["code"]]["note_count"] > 0]
    if not books_with:
        return ""
    # Canonical order: by `bxx` if present, else by code
    books_with.sort(key=lambda b: (b.get("bxx") or "", b["code"]))

    cell_w, cell_h = 9, 14
    label_w, top_pad, side_pad = 50, 18, 6
    max_ch = max(b.get("ch_count", 0) for b in books_with)

    elems = []
    # Top tick labels every 10 chapters
    for tick in range(10, max_ch + 1, 10):
        x = label_w + (tick - 1) * cell_w + cell_w / 2
        elems.append(
            f'<text x="{x:.1f}" y="{top_pad - 5}" text-anchor="middle" '
            f'font-size="8.5" font-family="ui-monospace, monospace" fill="#8a8378">{tick}</text>'
        )

    for i, book in enumerate(books_with):
        code = book["code"]
        ch_count = book.get("ch_count", 0)
        density = cd[code]
        y = top_pad + i * cell_h
        elems.append(
            f'<text x="{label_w - 6}" y="{y + cell_h - 4}" text-anchor="end" '
            f'font-size="9.5" font-family="ui-monospace, monospace" fill="#5d564d">'
            f"{html.escape(code)}</text>"
        )
        for ch in range(1, ch_count + 1):
            n = density.get(ch, 0)
            x = label_w + (ch - 1) * cell_w
            fill = heat_color(n)
            tooltip = f"{code} {ch}: {n} note{'s' if n != 1 else ''}"
            rect = (
                f'<rect x="{x}" y="{y + 1}" width="{cell_w - 1}" height="{cell_h - 2}" '
                f'fill="{fill}"><title>{html.escape(tooltip)}</title></rect>'
            )
            # If we know which file holds this chapter, wrap in an SVG <a>
            target_file = chapter_files.get((code, ch)) if chapter_files else None
            if target_file:
                href = f"{link_prefix}{target_file}#ch-{book['bxx']}-c{ch}"
                rect = (
                    f'<a href="{html.escape(href)}" target="_blank">{rect}</a>'
                )
            elems.append(rect)

    width = label_w + max_ch * cell_w + side_pad
    height = top_pad + len(books_with) * cell_h + side_pad
    svg = (
        f'<svg class="heatmap" width="{width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
        + "".join(elems)
        + "</svg>"
    )

    swatch_html = "".join(
        f'<span class="swatch" style="background:{c}"></span>' for c in HEAT_STOPS
    )
    hint = "click any cell to jump to the chapter" if chapter_files else "hover any cell for the count"
    legend = (
        '<div class="legend"><span>0 notes</span>'
        f'<span class="swatches">{swatch_html}</span><span>11+</span>'
        f'<span style="margin-left:auto;">{hint}</span></div>'
    )

    return (
        f'<section><h2>Note density · book × chapter</h2>'
        f'<div class="heatmap-wrap">{svg}</div>{legend}</section>'
    )


def render_gaps(stats) -> str:
    pb = stats["per_book"]
    empty = [b for b in stats["books"] if pb[b["code"]]["note_count"] == 0]
    if not empty:
        return ""
    items = "".join(
        f'<li><span class="code">{html.escape(b["code"])}</span> '
        f'<span class="dim">{html.escape(b.get("title", ""))}</span> '
        f'<span class="ch">· {b.get("ch_count", 0)} ch</span></li>'
        for b in empty
    )
    return (
        f"<section>"
        f"<h2>Coverage gaps · {len(empty)} books not yet noted</h2>"
        f'<ul class="gaps">{items}</ul></section>'
    )


def render_footer(stats) -> str:
    parse_warning = ""
    if stats["parse_failures"]:
        codes = ", ".join(stats["parse_failures"])
        parse_warning = (
            '<div style="color:var(--accent);margin-bottom:0.4rem;">'
            f"Warning: failed to parse content/notes/ for: {html.escape(codes)}</div>"
        )
    return (
        '<footer class="colophon">'
        f"{parse_warning}"
        "Generated by <code>scripts/dashboard.py</code> · "
        "Self-contained · No external CSS, JS, or fonts.</footer>"
    )


def render_html(stats, heatmap_only: bool = False, chapter_files=None, link_prefix: str = "") -> str:
    title = (
        "Ethiopian Bible — Coverage Heatmap"
        if heatmap_only
        else "Ethiopian Bible — Project Dashboard"
    )
    parts = [
        '<!DOCTYPE html>',
        '<html lang="en"><head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{title}</title>",
        f"<style>{CSS}</style>",
        "</head><body>",
        render_preamble(stats),
    ]
    if heatmap_only:
        parts.append(render_heatmap(stats, chapter_files=chapter_files, link_prefix=link_prefix))
    else:
        parts.extend([
            render_summary(stats),
            render_kind_breakdown(stats),
            render_book_table(stats),
            render_heatmap(stats, chapter_files=chapter_files, link_prefix=link_prefix),
            render_gaps(stats),
        ])
    parts.append(render_footer(stats))
    parts.append("</body></html>")
    return "\n".join(parts)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Generate a single-file HTML report on project state.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="output path (default: dashboard.html, or coverage_heatmap.html with --heatmap-only)",
    )
    p.add_argument(
        "--heatmap-only",
        action="store_true",
        help="emit only the density heatmap (with click-through links to chapters)",
    )
    p.add_argument(
        "--link-prefix",
        default="epub_working/",
        help="prefix for chapter-cell links (default: 'epub_working/'); set '' if output is "
        "already inside epub_working/",
    )
    p.add_argument("--quiet", action="store_true", help="suppress the 'wrote …' log line")
    args = p.parse_args()

    if args.output is None:
        args.output = DEFAULT_HEATMAP_OUT if args.heatmap_only else DEFAULT_OUT

    books = config.load_books()
    kinds = config.load_kinds()
    stats = gather_stats(books, kinds)
    chapter_files = build_chapter_file_index(EPUB_DIR, books) if args.heatmap_only else None

    if stats["parse_failures"] and not args.quiet:
        for code in stats["parse_failures"]:
            print(
                f"\033[93mWARNING: failed to parse content/notes/{code}.py\033[0m",
                file=sys.stderr,
            )

    html_text = render_html(
        stats,
        heatmap_only=args.heatmap_only,
        chapter_files=chapter_files,
        link_prefix=args.link_prefix,
    )
    args.output.write_text(html_text, encoding="utf-8")
    size_kb = args.output.stat().st_size / 1024

    if not args.quiet:
        mode = "heatmap" if args.heatmap_only else "dashboard"
        n_books = sum(1 for b in stats["per_book"].values() if b["note_count"] > 0)
        print(
            f"\033[92m✓ {mode}:\033[0m wrote {args.output} "
            f"({size_kb:.1f} KB · {stats['total_notes']:,} notes · {n_books} books)"
        )


if __name__ == "__main__":
    main()
