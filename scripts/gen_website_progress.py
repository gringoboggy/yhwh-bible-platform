"""Generate the website's Ge'ez & Amharic progress data + HTML fragment from the
REAL translation store, so the public page can never over-claim. Run before
website/build.mjs (which inlines the fragment). Re-run + commit when transcription
advances."""

from __future__ import annotations

import json
import re
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


def _display_name(title: str, code: str) -> str:
    """A short, public-friendly book name from the formal title."""
    # "The First Book of Moses, Genesis" -> "Genesis"; fall back to the code.
    tail = title.rsplit(",", 1)[-1].strip()
    return tail or code.upper()


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
                "en": code in en,
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
    en = _store_books(repo, "geez-tewahedo-en")
    geez = _bible_progress(repo, books, store="geez-tewahedo", standalone=standalone, en=en)
    amharic = _bible_progress(repo, books, store="amharic-tewahedo", standalone=set(), en=set())
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


def _grid(rows: list[dict]) -> str:
    cells = []
    for r in rows:
        en = ' <span class="pb-en" title="English back-translation available">EN</span>' if r["en"] else ""
        cells.append(
            f'<li class="pb-cell pb-{r["stage"]}" data-stage="{r["stage"]}" '
            f'title="{escape(r["name"])} — {STAGE_LABEL[r["stage"]]}">'
            f'<span class="pb-badge" aria-hidden="true">{STAGE_BADGE[r["stage"]]}</span>'
            f'<span class="pb-name">{_t(r["name"])}</span>{en}</li>'
        )
    return '<ol class="pb-grid">' + "".join(cells) + "</ol>"


def render_fragment(data: dict) -> str:
    g, a = data["geez"], data["amharic"]
    legend = (
        '<p class="pb-legend">'
        + " ".join(f"{STAGE_BADGE[s]} {STAGE_LABEL[s]}" for s in ("source", "transcribed", "ready"))
        + ' · <span class="pb-en">EN</span> English back-translation</p>'
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
        + '<h3 class="pb-h">Ge’ez Bible — book by book</h3>'
        + _grid(g["books"])
        + '<h3 class="pb-h">Amharic Bible — book by book</h3>'
        + _grid(a["books"])
        + "</div>"
    )


def write_outputs(repo_root: str | Path) -> None:
    repo = Path(repo_root)
    data = compute_progress(repo)
    out_dir = repo / "website" / "src" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "progress.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "geez-progress.html").write_text(render_fragment(data), encoding="utf-8")


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    write_outputs(repo)
    print("wrote website/src/data/geez-progress.html + progress.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
