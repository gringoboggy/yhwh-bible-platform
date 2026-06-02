"""scripts.core.standalone_store — Phase C2.

Generate an OWN-versification translation store from the base-structured
manuscript collations (``content/manuscript/<track>/collation/<ref>_collation_v2.json``).
Each base witness sense-unit becomes a store verse at its OWN ``(chapter, geez_v)``
coordinate (NOT KJV-renumbered); the KJV cross-reference + the manuscript apparatus
go to a ``<book>_apparatus.json`` sidecar for the standalone render path.

Pure data transform — reads collations only; never touches the witnesses or the
4 Samuel ``*_collation.json`` goldens.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
GEEZ_STORE = REPO / "content" / "translations" / "geez-tewahedo"


def collation_to_store_entries(
    collation: dict,
) -> tuple[list[tuple[int, int, str]], dict]:
    """Return ``(verses, apparatus_map)`` for one base-structured collation.

    - ``verses``: ``[(chapter, geez_v, geez_text), …]`` at the base witness's
      own numbering.
    - ``apparatus_map``: ``{str(geez_v): {"kjv": [[bk,ch,v],…], "confidence": str|None,
      "apparatus": [{base, other, class}, …]}}``.
    """
    ch = collation["chapter"]
    xref = collation.get("kjv_xref", {})
    verses: list[tuple[int, int, str]] = []
    appmap: dict[str, dict] = {}
    for pv in collation["primary_verses"]:
        gv = pv["geez_v"]
        verses.append((ch, gv, pv["geez_text"]))
        x = xref.get(str(gv), {})
        appmap[str(gv)] = {
            "kjv": x.get("kjv", []),
            "confidence": x.get("confidence"),
            "apparatus": pv.get("apparatus", []),
        }
    return verses, appmap


def _render_book_module(book: str, verses: list[tuple[int, int, str]]) -> str:
    out = [
        f'"""Translation: geez-tewahedo · Book: {book}',
        "",
        "Own-versification store generated from the base-structured manuscript",
        "collations (Phase C2). Verse coordinates are the base witness's OWN",
        "sense-unit numbering (NOT KJV-renumbered). KJV cross-refs + the",
        f"manuscript apparatus live in {book}_apparatus.json.",
        '"""',
        "",
        'TRANSLATION = "geez-tewahedo"',
        f'BOOK = "{book}"',
        'VERSIFICATION = "own"',
        'SOURCE_QUALITY = "manuscript-collation-tier2"',
        'INGEST_PHASE = "C2"',
        "VERSES = [",
    ]
    for c, v, t in verses:
        esc = t.replace("\\", "\\\\").replace('"', '\\"')
        out.append(f'    ({c}, {v}, "{esc}"),')
    out.append("]")
    return "\n".join(out) + "\n"


def build_book_store(book: str, collation_paths: list[Path], out_dir: Path) -> dict:
    """Aggregate a book's chapter collations → ``<book>.py`` + ``<book>_apparatus.json``
    in ``out_dir``. Returns a stats dict."""
    all_verses: list[tuple[int, int, str]] = []
    appmap: dict[str, dict] = {}  # {str(chapter): {str(geez_v): {...}}}
    for p in collation_paths:
        coll = json.loads(p.read_text(encoding="utf-8"))
        verses, am = collation_to_store_entries(coll)
        all_verses.extend(verses)
        appmap[str(coll["chapter"])] = am
    all_verses.sort(key=lambda t: (t[0], t[1]))
    from scripts.core.notes_io import atomic_write  # mint-11 #4: atomic corpus writes

    out_dir.mkdir(parents=True, exist_ok=True)
    atomic_write(out_dir / f"{book}.py", _render_book_module(book, all_verses))
    atomic_write(out_dir / f"{book}_apparatus.json", json.dumps(appmap, ensure_ascii=False, indent=2))
    return {"book": book, "verses": len(all_verses), "chapters": len(appmap)}


# Maps the 10 done chapters to their books. Kings collations live under
# content/manuscript/kings/collation; Samuel under .../samuel/collation.
_BOOK_CHAPTERS = {
    "1ki": ("kings", [1, 2, 3, 4, 5, 6]),
    "1sa": ("samuel", [1, 3, 17]),
    "2sa": ("samuel", [11]),
}


def main() -> int:
    man = REPO / "content" / "manuscript"
    for book, (track, chapters) in _BOOK_CHAPTERS.items():
        paths = [man / track / "collation" / f"{book}{c}_collation_v2.json" for c in chapters]
        missing = [p for p in paths if not p.is_file()]
        if missing:
            print(f"SKIP {book}: missing {[p.name for p in missing]}")
            continue
        res = build_book_store(book, paths, GEEZ_STORE)
        print(f"WROTE {book}: {res['verses']} verses / {res['chapters']} chapters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def lxx_psalms_to_kjv(lxx_ch: int) -> list[int]:
    """Map a Septuagint/Ge'ez Psalm chapter to its KJV (Hebrew) chapter number(s).

    The Ge'ez Psalter follows the LXX numbering, which diverges from KJV/Hebrew at
    four well-known seams: LXX 9 = KJV 9+10; LXX 10-112 = KJV 11-113 (one behind);
    LXX 113 = KJV 114+115; LXX 114+115 = KJV 116; LXX 116-145 = KJV 117-146; LXX
    146+147 = KJV 147; the rest (1-8, 148-150) are identical. Returns the KJV
    chapter(s) a given LXX chapter maps onto; empty for LXX 151 (the LXX-only Psalm,
    absent from the KJV)."""
    if 1 <= lxx_ch <= 8:
        return [lxx_ch]
    if lxx_ch == 9:
        return [9, 10]
    if 10 <= lxx_ch <= 112:
        return [lxx_ch + 1]
    if lxx_ch == 113:
        return [114, 115]
    if lxx_ch in (114, 115):
        return [116]
    if 116 <= lxx_ch <= 145:
        return [lxx_ch + 1]
    if lxx_ch in (146, 147):
        return [147]
    if 148 <= lxx_ch <= 150:
        return [lxx_ch]
    return []


def build_psalms_apparatus(out_dir: Path = GEEZ_STORE) -> dict:
    """Generate geez-tewahedo/psa_apparatus.json for the standalone render path.

    Psalms is single-source (no manuscript apparatus); each own-vers (LXX) verse
    gets a KJV cross-reference via lxx_psalms_to_kjv with confidence 'interpolated'
    (chapter-anchored, verse-approximate — the LXX/KJV verse offset within a chapter
    is not resolved here, so we never claim verse-exact precision). Returns a stats dict."""
    from scripts.core import translations as tx

    verses = tx._load_book("geez-tewahedo", "psa") or []
    appmap: dict[str, dict] = {}
    for ch, v, _t in verses:
        kjv_chs = lxx_psalms_to_kjv(ch)
        appmap.setdefault(str(ch), {})[str(v)] = {
            "kjv": [["psa", kc, v] for kc in kjv_chs],
            "confidence": "interpolated" if kjv_chs else None,
            "apparatus": [],
        }
    from scripts.core.notes_io import atomic_write  # mint-11 #4: atomic corpus write

    out_dir.mkdir(parents=True, exist_ok=True)
    atomic_write(out_dir / "psa_apparatus.json", json.dumps(appmap, ensure_ascii=False, indent=2))
    return {"chapters": len(appmap), "verses": sum(len(c) for c in appmap.values())}
