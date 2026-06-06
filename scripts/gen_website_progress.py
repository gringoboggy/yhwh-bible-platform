"""Generate the website's Ge'ez & Amharic progress data + HTML fragment AND the
on-site chapter reader, from the REAL translation store, so the public site can never
over-claim. Run before website/build.mjs (which inlines the progress fragment and
wraps the reader pages in the shared frame). Re-run + commit when transcription
advances — the reader grows automatically.

The reader surfaces ONLY transcribed scripture: a book gets a clickable reader iff it
is own-versified (◑ transcribed / ● Bible-ready) — the exact signal the progress map
uses. Raw OCR source (◐ "source in hand") is never emitted. Per chapter the reader is
Geʽez+English parallel where an English back-translation exists, else single-column
Geʽez/Amharic (English trails after the full release). All text is plainly selectable
and free to copy."""

from __future__ import annotations

import json
import re
import shutil
import sys
from html import escape
from pathlib import Path

# Stage precedence (highest achieved wins): ready > transcribed > source.
# There is NO "not started" stage: the complete EOTC parallel Geʽez–Amharic Bible
# (content/translations/sources/parallel-bible-eotc/Bible_Amharic_and_Geez.pdf) plus the
# GAPS manuscript sources cover the whole canon, so every book has its source in hand.
STAGE_RANK = {"source": 0, "transcribed": 1, "ready": 2}
STAGE_BADGE = {"source": "◐", "transcribed": "◑", "ready": "●"}
STAGE_LABEL = {
    "source": "source in hand",
    "transcribed": "transcribed",
    "ready": "Bible-ready",
}

# Translation-store legacy codes -> canonical books.yaml codes. Mirrors
# scripts/render_coverage.py _BOOK_ALIASES (the Ge'ez/Amharic stores use "ex" for
# Exodus etc.); the central scripts.core.sources_base normalizer covers a DIFFERENT
# set (notes/detector codes like php/jas), not these store codes.
_STORE_ALIASES = {"ex": "exo", "1k": "1ki", "2k": "2ki"}

# The reader tracks: store -> (url/dir slug, BCP-47 lang for the script column,
# the English back-translation store). Geʽez is LTR (Ethiopic script), no dir="rtl".
_READER_TRACKS = {
    "geez-tewahedo": ("geez", "gez", "geez-tewahedo-en"),
    "amharic-tewahedo": ("amharic", "am", "amharic-tewahedo-en"),
}

# Geʽez book names for chapter headings, only where confidently known; otherwise the
# reader falls back to the English display name (no guessing on a faith site).
_GEEZ_BOOK_NAME = {"psa": "መዝሙር"}  # Psalms

# Ethiopic (Geʽez) numerals — for manuscript-authentic chapter & verse numbers.
_ETH_ONES = "፩፪፫፬፭፮፯፰፱"  # 1–9   (U+1369–U+1371)
_ETH_TENS = "፲፳፴፵፶፷፸፹፺"  # 10–90 (U+1372–U+137A)


def ethiopic_numeral(n: int) -> str:
    """Render a positive integer in Geʽez numerals. Covers our range (chapters ≤ 151,
    verses < 100; hundreds handled up to 999). Modern usage drops the leading 1 before
    ፻ (100 = ፻, not ፩፻)."""
    if n <= 0:
        return str(n)
    out = ""
    hundreds, rem = divmod(n, 100)
    if hundreds:
        if hundreds > 1:
            out += _ETH_ONES[hundreds - 1]
        out += "፻"
    tens, ones = divmod(rem, 10)
    if tens:
        out += _ETH_TENS[tens - 1]
    if ones:
        out += _ETH_ONES[ones - 1]
    return out


def _norm(code: str) -> str:
    return _STORE_ALIASES.get(code, code)


def _t(s: str) -> str:
    """Escape for HTML TEXT content (only <, >, & — apostrophes/quotes are fine)."""
    return escape(s, quote=False)


def _standalone_books() -> set[str]:
    """The (normalized) book codes the standalone Ge'ez build actually ships."""
    src = (Path(__file__).resolve().parent / "build_standalone.py").read_text(encoding="utf-8")
    m = re.search(r"_STANDALONE_BOOKS\s*=\s*\[([^\]]*)\]", src)
    if not m:
        return set()
    return {_norm(c) for c in re.findall(r'"([^"]+)"', m.group(1))}


def _store_books(repo: Path, store: str) -> set[str]:
    d = repo / "content" / "translations" / store
    if not d.is_dir():
        return set()
    return {_norm(p.stem) for p in d.glob("*.py") if p.stem != "_meta"}


def _own_versified(repo: Path, store: str) -> set[str]:
    """Books whose store file carries a VERSIFICATION block (own-versified)."""
    d = repo / "content" / "translations" / store
    out: set[str] = set()
    if not d.is_dir():
        return out
    for p in d.glob("*.py"):
        if p.stem == "_meta":
            continue
        if any(line.startswith("VERSIFICATION") for line in p.read_text(encoding="utf-8").splitlines()):
            out.add(_norm(p.stem))
    return out


def _transcribed_store_codes(repo: Path, store: str) -> list[str]:
    """The ACTUAL store stems (not normalized) that are own-versified (◑/●) — the
    transcribed set the reader is allowed to surface. Same signal the progress map uses
    (_own_versified); kept as raw stems because the translations API keys on them."""
    d = repo / "content" / "translations" / store
    if not d.is_dir():
        return []
    out = []
    for p in sorted(d.glob("*.py")):
        if p.stem == "_meta":
            continue
        if any(line.startswith("VERSIFICATION") for line in p.read_text(encoding="utf-8").splitlines()):
            out.append(p.stem)
    return out


def _en_books(repo: Path, store: str, *, min_rows: int = 50) -> set[str]:
    """Books whose English back-translation has REAL coverage (not a stub file).
    A bare/near-empty file in the store must NOT light the 'EN' badge — the badge has to
    mean a usable back-translation exists, and a back-translation can only exist once the
    Geʽez itself is transcribed (so the stage gate in _bible_progress also applies)."""
    d = repo / "content" / "translations" / store
    out: set[str] = set()
    if not d.is_dir():
        return out
    for p in d.glob("*.py"):
        if p.stem == "_meta":
            continue
        rows = sum(1 for line in p.read_text(encoding="utf-8").splitlines() if re.match(r"\s*\(\d", line))
        if rows >= min_rows:
            out.add(_norm(p.stem))
    return out


def _display_name(title: str, code: str) -> str:
    """A short, public-friendly book name from the formal title."""
    # "The First Book of Moses, Genesis" -> "Genesis"; fall back to the code.
    tail = title.rsplit(",", 1)[-1].strip()
    return tail or code.upper()


def _reader_link_map(repo: Path, store: str, slug: str) -> dict[str, str]:
    """{normalized_book_code: href} for every transcribed (own-versified) book in the
    track — the books whose progress pill becomes a clickable reader. The {{root}} token
    is resolved per-page by build.mjs (so it works from any directory depth)."""
    return {_norm(c): f"{{{{root}}}}read/{slug}/{_norm(c)}.html" for c in _transcribed_store_codes(repo, store)}


def _bible_progress(repo: Path, books: list[dict], *, store: str, standalone: set[str], en: set[str]) -> dict:
    has_source = _store_books(repo, store)
    has_versification = _own_versified(repo, store)
    rows = []
    for rec in books:
        code = rec["code"]
        if code in standalone:
            stage = "ready"
        elif code in has_versification:
            stage = "transcribed"
        elif code in has_source:
            stage = "source"
        else:
            # Whole canon is sourced (complete EOTC parallel Bible PDF + GAPS manuscripts);
            # a book not yet in the store still has its source in hand. No "not started" state.
            stage = "source"
        rows.append(
            {
                "code": code,
                "name": _display_name(rec.get("title", code), code),
                "stage": stage,
                "en": code in en and stage in ("transcribed", "ready"),
            }
        )
    counts = {s: sum(1 for r in rows if r["stage"] == s) for s in STAGE_RANK}
    return {"books": rows, "counts": counts, "total": len(rows)}


def compute_progress(repo_root: str | Path) -> dict:
    repo = Path(repo_root)
    sys.path.insert(0, str(repo))
    from scripts.core import config

    books = config.load_books()  # 87-book registry, canonical order
    standalone = _standalone_books()
    en = _en_books(repo, "geez-tewahedo-en")
    geez = _bible_progress(repo, books, store="geez-tewahedo", standalone=standalone, en=en)
    geez["links"] = _reader_link_map(repo, "geez-tewahedo", "geez")
    amharic = _bible_progress(repo, books, store="amharic-tewahedo", standalone=set(), en=set())
    amharic["links"] = _reader_link_map(repo, "amharic-tewahedo", "amharic")
    return {"geez": geez, "amharic": amharic}


def _bar(label: str, ready: int, total: int, sub: str) -> str:
    pct = round(100 * ready / total) if total else 0
    return (
        '<div class="pb-bar-row">'
        f'<div class="pb-bar-head"><strong>{_t(label)}</strong>'
        f'<span class="pb-bar-sub">{_t(sub)}</span></div>'
        f'<div class="pb-bar" role="img" aria-label="{escape(sub)}">'
        f'<span class="pb-bar-fill" style="width:{pct}%"></span></div></div>'
    )


def _grid(rows: list[dict], links: dict[str, str] | None = None) -> str:
    links = links or {}
    cells = []
    for r in rows:
        en = ' <span class="pb-en" title="English back-translation available">EN</span>' if r["en"] else ""
        inner = (
            f'<span class="pb-badge" aria-hidden="true">{STAGE_BADGE[r["stage"]]}</span>'
            f'<span class="pb-name">{_t(r["name"])}</span>{en}'
        )
        href = links.get(r["code"])
        extra = ""
        if href:
            # Only transcribed (◑/●) books get a clickable reader — never OCR ◐ source.
            inner = f'<a class="pb-link" href="{href}">{inner}</a>'
            extra = " has-reader"
        cells.append(
            f'<li class="pb-cell pb-{r["stage"]}{extra}" data-stage="{r["stage"]}" '
            f'title="{escape(r["name"])} — {STAGE_LABEL[r["stage"]]}">{inner}</li>'
        )
    return '<ol class="pb-grid">' + "".join(cells) + "</ol>"


def render_fragment(data: dict) -> str:
    g, a = data["geez"], data["amharic"]
    legend = (
        '<p class="pb-legend">'
        + " ".join(f"{STAGE_BADGE[s]} {STAGE_LABEL[s]}" for s in ("source", "transcribed", "ready"))
        + ' · <span class="pb-en">EN</span> English back-translation</p>'
    )
    hint = (
        '<p class="pb-hint">A <strong>● Bible-ready</strong> book is a link — open it to read the '
        "scripture on the website, Geʽez beside a literal English. The text is free to read, copy, and share.</p>"
    )
    return (
        '<div class="pb-wrap">'
        + _bar(
            "Ge'ez Bible",
            g["counts"]["ready"],
            g["total"],
            f"{g['counts']['ready']} books Bible-ready of {g['total']}",
        )
        + _bar(
            "Amharic Bible",
            a["counts"]["ready"],
            a["total"],
            f"{a['counts']['source']} books of source text gathered — assembly ahead",
        )
        + legend
        + hint
        + '<h3 class="pb-h">Ge’ez Bible — book by book</h3>'
        + _grid(g["books"], g.get("links"))
        + '<h3 class="pb-h">Amharic Bible — book by book</h3>'
        + _grid(a["books"], a.get("links"))
        + "</div>"
    )


# --------------------------------------------------------------------------- #
# The on-site chapter reader (read/<lang>/<book>/<ch>.html + read/<lang>/<book>.html)
# --------------------------------------------------------------------------- #


def _script_label(slug: str) -> str:
    return "Amharic" if slug == "amharic" else "Geʽez"


def _safe_chapter_rows(repo: Path, store: str, book: str) -> dict[int, list[tuple[int, str]]]:
    """{chapter: [(verse, text), ...]} in faithful SOURCE order (duplicates preserved),
    or {} if the store has no file for the book. Reuses the EPUB's own grouper so the
    reader text has a single origin (never a divergent copy)."""
    if not (repo / "content" / "translations" / store / f"{book}.py").exists():
        return {}
    from scripts import build_standalone as bs

    return bs.chapter_verses_in_source_order(store, book)


def _is_parallel(geez_rows: list[tuple[int, str]], en_rows: list[tuple[int, str]] | None) -> bool:
    """A chapter is parallel-ready iff the English exists AND pairs 1:1 by occurrence
    index — same length and same verse-number sequence (duplicate verse numbers, e.g.
    Ps 36, must line up positionally, never by dict key)."""
    return bool(en_rows) and len(en_rows) == len(geez_rows) and [v for v, _ in geez_rows] == [v for v, _ in en_rows]


def _reader_bar(done: int, total: int, sub: str) -> str:
    pct = round(100 * done / total) if total else 0
    return (
        '<div class="pb-bar-row"><div class="pb-bar-head">'
        f'<span class="pb-bar-sub">{_t(sub)}</span></div>'
        f'<div class="pb-bar" role="img" aria-label="{escape(sub)}">'
        f'<span class="pb-bar-fill" style="width:{pct}%"></span></div></div>'
    )


def render_reader_chapter(
    *,
    slug: str,
    lang: str,
    norm: str,
    book_label: str,
    geez_name: str | None,
    ch: int,
    geez_rows: list[tuple[int, str]],
    en_rows: list[tuple[int, str]] | None,
    ready_chs: list[int],
) -> str:
    """A full reader src-page (front-matter + body). build.mjs wraps it in the shared
    head/foot and resolves {{root}}. Parallel two-column when EN pairs 1:1, else
    single-column with an honest 'English planned' note."""
    parallel = _is_parallel(geez_rows, en_rows)
    script_word = _script_label(slug)

    prevs = [c for c in ready_chs if c < ch]
    nexts = [c for c in ready_chs if c > ch]
    nav_bits = []
    if prevs:
        nav_bits.append(f'<a class="rdr-prev" href="{{{{root}}}}read/{slug}/{norm}/{max(prevs)}.html">‹ previous</a>')
    nav_bits.append(f'<a href="{{{{root}}}}read/{slug}/{norm}.html">all chapters</a>')
    if nexts:
        nav_bits.append(f'<a class="rdr-next" href="{{{{root}}}}read/{slug}/{norm}/{min(nexts)}.html">next ›</a>')
    nav = '<div class="rdr-nav">' + " ".join(nav_bits) + "</div>"

    bk_geez = f'<span class="rdr-bk" lang="gez">{_t(geez_name)}</span> ' if geez_name else ""
    sub = f"{_t(book_label)} {ch}" + (" · Geʽez &amp; English" if parallel else f" · {script_word} only")
    head = (
        '<header class="rdr-head">'
        '<div class="rdr-orn" aria-hidden="true">✛</div>'
        f'<h1 class="rdr-title">{bk_geez}'
        f'<span class="rdr-num" lang="gez" title="{ch}">{ethiopic_numeral(ch)}</span></h1>'
        f'<p class="rdr-sub">{sub}</p></header>'
    )

    copy_en = '<button type="button" class="rdr-copy" data-col="en">Copy English</button>' if parallel else ""
    tools = (
        '<div class="rdr-tools">'
        f'<button type="button" class="rdr-copy" data-col="gez">Copy {script_word}</button>{copy_en}</div>'
    )

    items = []
    for i, (gv, gtext) in enumerate(geez_rows):
        solo = ""
        en_cell = ""
        if parallel:
            en_cell = f'<p class="rdr-en">{_t(en_rows[i][1])}</p>'
        else:
            solo = " solo"
        items.append(
            f'<li class="rdr-row{solo}">'
            f'<span class="sr-only">Verse {gv}.</span>'
            f'<span class="rdr-vn" lang="gez" title="verse {gv}" aria-hidden="true">{ethiopic_numeral(gv)}</span>'
            f'<p class="rdr-gez" lang="{lang}">{_t(gtext)}</p>{en_cell}</li>'
        )
    rows_html = '<ol class="rdr-rows">' + "".join(items) + "</ol>"

    if parallel:
        note = (
            "Geʽez transcribed from the manuscripts; the English is a literal back-translation — a reading aid, "
            "not a replacement for the Geʽez. Free to read, copy, and share."
        )
    else:
        note = (
            f"{script_word} transcribed from the manuscripts. A literal English translation of this chapter is "
            "planned (after the full release). Free to read, copy, and share."
        )

    body = (
        f'<section class="band rdr" aria-label="{_t(book_label)} {ch}">'
        f'<div class="rdr-top">{nav}'
        f'<a href="{{{{root}}}}geez.html">↩ Geʽez &amp; Amharic progress</a></div>'
        + head
        + tools
        + rows_html
        + f'<p class="rdr-foot">{note}</p>'
        + "</section>"
        + '<script src="{{root}}reader.js" defer></script>'
    )

    desc = (
        f"{book_label} {ch} in Geʽez"
        + (" with a literal English back-translation" if parallel else "")
        + " — free to read and copy."
    )
    fm = (
        "<!--page\n"
        f"title: {book_label} {ch} — Geʽez Bible | YHWH Ya’ Way\n"
        f"desc: {desc}\n"
        f"canonical: https://www.yhwhyaway.com/read/{slug}/{norm}/{ch}.html\n"
        "page: geez\n"
        "-->\n"
    )
    return fm + body


def render_book_index(
    *,
    slug: str,
    norm: str,
    book_label: str,
    geez_name: str | None,
    total_ch: int,
    ready_chs: list[int],
    n_parallel: int,
) -> str:
    ready = set(ready_chs)
    cells = []
    for c in range(1, total_ch + 1):
        eth = f'<span class="eth" lang="gez" aria-hidden="true">{ethiopic_numeral(c)}</span>'
        if c in ready:
            cells.append(
                f'<li class="rdx-cell rdx-ready"><a href="{{{{root}}}}read/{slug}/{norm}/{c}.html" '
                f'title="{_t(book_label)} {c}">{eth}{c}</a></li>'
            )
        else:
            cells.append(
                f'<li class="rdx-cell rdx-todo" aria-disabled="true" '
                f'title="{_t(book_label)} {c} — not yet transcribed">{eth}{c}</li>'
            )
    grid = '<ol class="rdx-grid">' + "".join(cells) + "</ol>"
    bk_geez = f'<span lang="gez">{_t(geez_name)}</span> · ' if geez_name else ""
    done = len(ready_chs)
    parallel_line = " with a literal English translation" if n_parallel else ""
    body = (
        '<section class="band rdr">'
        '<div class="rdr-top"><a href="{{root}}geez.html">↩ Geʽez &amp; Amharic progress</a></div>'
        f'<h1 class="rule">{bk_geez}{_t(book_label)}</h1>'
        f'<p class="prose">Open any chapter to read it in Geʽez{parallel_line}. '
        "Faint chapters are not yet transcribed — they fill in as the work proceeds.</p>"
        + _reader_bar(done, total_ch, f"{done} of {total_ch} chapters readable")
        + grid
        + "</section>"
    )
    fm = (
        "<!--page\n"
        f"title: {book_label} — Geʽez Bible | YHWH Ya’ Way\n"
        f"desc: Read {book_label} in Geʽez on the website — {done} of {total_ch} chapters transcribed so far.\n"
        f"canonical: https://www.yhwhyaway.com/read/{slug}/{norm}.html\n"
        "page: geez\n"
        "-->\n"
    )
    return fm + body


def write_reader_pages(repo_root: str | Path) -> int:
    """Emit the static reader src-pages for every transcribed book. Returns the page
    count. Wipes website/src/read/ first so a removed/renumbered chapter can't linger."""
    repo = Path(repo_root)
    sys.path.insert(0, str(repo))
    from scripts.core import config

    by_norm = {rec["code"]: rec for rec in config.load_books()}
    read_root = repo / "website" / "src" / "read"
    if read_root.exists():
        shutil.rmtree(read_root)

    n_pages = 0
    for store, (slug, lang, en_store) in _READER_TRACKS.items():
        for store_code in _transcribed_store_codes(repo, store):
            norm = _norm(store_code)
            rec = by_norm.get(norm, {})
            book_label = _display_name(rec.get("title", norm), norm)
            geez_name = _GEEZ_BOOK_NAME.get(norm)
            geez_by_ch = _safe_chapter_rows(repo, store, store_code)
            en_by_ch = _safe_chapter_rows(repo, en_store, store_code)
            present = sorted(geez_by_ch)
            if not present:
                continue
            n_parallel = sum(1 for c in present if _is_parallel(geez_by_ch[c], en_by_ch.get(c)))
            ch_count = rec.get("ch_count") or max(present)
            total_ch = max(ch_count, max(present))

            book_dir = read_root / slug / norm
            book_dir.mkdir(parents=True, exist_ok=True)
            for ch in present:
                page = render_reader_chapter(
                    slug=slug,
                    lang=lang,
                    norm=norm,
                    book_label=book_label,
                    geez_name=geez_name,
                    ch=ch,
                    geez_rows=geez_by_ch[ch],
                    en_rows=en_by_ch.get(ch),
                    ready_chs=present,
                )
                (book_dir / f"{ch}.html").write_text(page, encoding="utf-8")
                n_pages += 1
            (read_root / slug / f"{norm}.html").write_text(
                render_book_index(
                    slug=slug,
                    norm=norm,
                    book_label=book_label,
                    geez_name=geez_name,
                    total_ch=total_ch,
                    ready_chs=present,
                    n_parallel=n_parallel,
                ),
                encoding="utf-8",
            )
            n_pages += 1
    return n_pages


def write_outputs(repo_root: str | Path) -> None:
    repo = Path(repo_root)
    data = compute_progress(repo)
    out_dir = repo / "website" / "src" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "progress.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "geez-progress.html").write_text(render_fragment(data), encoding="utf-8")
    n = write_reader_pages(repo)
    print(f"wrote website/src/data/geez-progress.html + progress.json + {n} reader pages")


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    write_outputs(repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
