"""Structural audit of the recovered base HTML: which chapters' verse text
is reachable from their chapter anchor (regular) vs. split across files
(irregular). Read-only; re-runnable detector."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402

EPUB_DIR = REPO_ROOT / "epub_working"
_VN = re.compile(r'<span class="vn">(\d+)</span>')


def _file_texts(book: dict) -> dict[str, str]:
    out = {}
    for fname in book.get("files", []):
        p = EPUB_DIR / fname
        if p.is_file():
            out[fname] = p.read_text(encoding="utf-8")
    return out


def classify_book(code: str) -> dict:
    """For a Strategy-B book, a chapter is 'irregular' when its ch anchor's
    file holds no verse spans between this ch anchor and the next ch anchor,
    yet the book does contain verse spans for that chapter elsewhere."""
    book = config.get_book(code)
    bxx = book.get("bxx")
    strategy = book.get("strategy", "A")
    texts = _file_texts(book)
    irregular: list[int] = []
    if strategy != "B" or not bxx:
        return {"code": code, "strategy": strategy, "irregular_chapters": irregular}
    n = book.get("ch_count", 0)
    for ch in range(1, n + 1):
        anchor = f'id="ch-{bxx}-c{ch}"'
        host = next((t for t in texts.values() if anchor in t), None)
        if host is None:
            continue  # chapter-absent; handled elsewhere
        start = host.find(anchor)
        nxt = host.find(f'id="ch-{bxx}-c{ch + 1}"', start + 1)
        region = host[start:nxt] if nxt != -1 else host[start:]
        if not _VN.search(region):
            irregular.append(ch)
    return {"code": code, "strategy": strategy, "irregular_chapters": irregular}


def run_all() -> dict:
    books, flagged = [], {}
    for b in config.load_books():
        if not (REPO_ROOT / "content" / "notes" / f"{b['code']}.py").is_file():
            continue
        rep = classify_book(b["code"])
        books.append(rep)
        if rep["irregular_chapters"]:
            flagged[rep["code"]] = rep["irregular_chapters"]
    return {"flagged": flagged, "checked": len(books)}


def verse_absent_report() -> list[tuple[str, int, int]]:
    """Strategy-A notes whose verse anchor ``id="v-{code}-{ch}-{v}"`` is absent
    from every one of the book's split files — the verse number does not exist
    in the WEB rendering of that chapter (a versification mismatch between the
    note's source and the base translation). These are NOT addable content.
    Mirrors ``inject.inject_book``'s Strategy-A "(no verse anchor)" branch.
    Returns sorted ``(code, ch, v)`` rows."""
    from scripts.core.notes_io import load_notes

    rows: list[tuple[str, int, int]] = []
    for b in config.load_books():
        code = b["code"]
        if b.get("strategy", "A") != "A":
            continue
        notes_path = REPO_ROOT / "content" / "notes" / f"{code}.py"
        if not notes_path.is_file():
            continue
        texts = _file_texts(b)
        if not texts:
            continue
        for tup in load_notes(notes_path) or []:
            if not isinstance(tup, tuple) or len(tup) < 8:
                continue
            ch, v = tup[0], tup[1]
            if not isinstance(ch, int) or not isinstance(v, int):
                continue
            anchor = f'id="v-{code}-{ch}-{v}"'
            if not any(anchor in t for t in texts.values()):
                rows.append((code, ch, v))
    return sorted(rows)


def coverage_report() -> dict[str, list[int]]:
    """Per book, the chapters (1..ch_count) with NO anchor in the base HTML —
    i.e. genuinely-missing scripture, the class of bug a stale 'truncated at
    chN' note describes. Uses ``config`` ch_count (covers ALL 87 books, incl.
    Tewahedo-distinctives with no KJV skeleton). Strategy-B: chapter anchor
    ``id="ch-{bxx}-c{ch}"`` absent. Strategy-A: no verse anchor
    ``id="v-{code}-{ch}-N"`` for the chapter. A book whose files are entirely
    absent from this base is reported as ``["BOOK-ABSENT", ch_count]`` (e.g.
    standalone editions render from their own HTML, not this base)."""
    gaps: dict[str, list] = {}
    for b in config.load_books():
        code = b["code"]
        n = b.get("ch_count", 0)
        if not n:
            continue
        texts = _file_texts(b)
        if not texts:
            gaps[code] = ["BOOK-ABSENT", n]
            continue
        blob = "\n".join(texts.values())
        strategy = b.get("strategy", "A")
        bxx = b.get("bxx")
        absent = []
        for ch in range(1, n + 1):
            if strategy == "B" and bxx:
                present = f'id="ch-{bxx}-c{ch}"' in blob
            else:
                present = re.search(rf'id="v-{re.escape(code)}-{ch}-\d+"', blob) is not None
            if not present:
                absent.append(ch)
        if absent:
            gaps[code] = absent
    return gaps


def main() -> int:
    if "--coverage" in sys.argv[1:]:
        gaps = coverage_report()
        for code, chs in sorted(gaps.items()):
            print(f"  {code:5} {len(chs) if chs[0] != 'BOOK-ABSENT' else chs[1]:>4} ch absent: {chs}")
        print(f"\nbooks with chapter-coverage gaps = {len(gaps)}")
        return 0
    if "--verse-absent" in sys.argv[1:]:
        rows = verse_absent_report()
        for code, ch, v in rows:
            print(f"  {code:5} {ch}:{v}")
        print(f"\nverse-absent (Strategy-A versification gaps) = {len(rows)}")
        return 0
    result = run_all()
    for code, chs in sorted(result["flagged"].items()):
        print(f"  {code:5} irregular chapters: {chs}")
    print(f"\nchecked={result['checked']} irregular_books={len(result['flagged'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
