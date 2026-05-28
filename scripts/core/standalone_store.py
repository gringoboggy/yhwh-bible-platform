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
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{book}.py").write_text(_render_book_module(book, all_verses), encoding="utf-8")
    (out_dir / f"{book}_apparatus.json").write_text(json.dumps(appmap, ensure_ascii=False, indent=2), encoding="utf-8")
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
