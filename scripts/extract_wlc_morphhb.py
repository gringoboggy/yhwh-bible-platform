"""scripts/extract_wlc_morphhb.py — ingest the Westminster Leningrad Codex
(Hebrew) from the OpenScriptures *morphhb* OSIS source into the project's
translation store (Phase 2 of the fully-customizable-builder roadmap).

``scripts/extract_translation.py`` only parses eBible "verse per line" text;
the WLC ships as morphology-rich OSIS XML, so it gets a dedicated extractor
(roadmap §5: "Per-source ``scripts/extract_<id>.py``").

Pipeline (roadmap §3 data flow):

    _acquire/morphhb/wlc/<Book>.xml   OSIS, Masoretic versification, <w>+<seg>
        → verse_to_em_html            <em>-per-word HTML (house format)
        → versification remap         WLC (Masoretic) coords → canonical KJV
        → content/translations/wlc/<code>.py   VERSES = [(ch, vs, html), ...]

The emitted HTML matches the recovered base's existing ``vnote-hebrew`` markup
(each word in ``<em>``, ``/`` morpheme separators stripped, maqaf-joined words
kept in one ``<em>``, sof-pasuq glued to the last word, paseq standalone). It is
trusted pre-formatted HTML — ``popup_versions.is_trusted_html("wlc")`` passes it
to the aside renderer raw.

Standalone one-shot like ``extract_naves_ccel.py``: reads a gitignored source
tree under ``_acquire/`` and writes regenerable per-book modules. Not imported by
runtime code.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

OSIS_NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))  # allow `python scripts/extract_wlc_morphhb.py`
TRANSLATIONS_DIR = REPO / "content" / "translations"
# morphhb is cloned into a gitignored staging dir at the workspace root (one
# level above the repo); re-fetchable from github.com/openscriptures/morphhb.
DEFAULT_SOURCE = REPO.parent / "_acquire" / "morphhb" / "wlc"

# OSIS book name (= morphhb XML filename stem) → project 3-letter book code.
# The 39-book Hebrew (Masoretic) canon; values must exist in books.yaml.
OSIS_BOOK_TO_CODE: dict[str, str] = {
    "Gen": "gen",
    "Exod": "exo",
    "Lev": "lev",
    "Num": "num",
    "Deut": "deu",
    "Josh": "jos",
    "Judg": "jdg",
    "Ruth": "rut",
    "1Sam": "1sa",
    "2Sam": "2sa",
    "1Kgs": "1ki",
    "2Kgs": "2ki",
    "1Chr": "1ch",
    "2Chr": "2ch",
    "Ezra": "ezr",
    "Neh": "neh",
    "Esth": "est",
    "Job": "job",
    "Ps": "psa",
    "Prov": "pro",
    "Eccl": "ecc",
    "Song": "sng",
    "Isa": "isa",
    "Jer": "jer",
    "Lam": "lam",
    "Ezek": "eze",
    "Dan": "dan",
    "Hos": "hos",
    "Joel": "joe",
    "Amos": "amo",
    "Obad": "oba",
    "Jonah": "jon",
    "Mic": "mic",
    "Nah": "nah",
    "Hab": "hab",
    "Zeph": "zep",
    "Hag": "hag",
    "Zech": "zec",
    "Mal": "mal",
}


def _local(tag: str) -> str:
    """Strip an ElementTree ``{namespace}local`` tag down to ``local``."""
    return tag.split("}", 1)[1] if "}" in tag else tag


def _word_text(el: ET.Element) -> str:
    """Full text of a ``<w>`` element, including scribal special letters that
    morphhb nests *inside* the word — the large letters of Deut 6:4 / Lev 11:42,
    the suspended nun of Judg 18:30, etc. (``<seg type="x-large">ע</seg>``). A
    naive ``el.text`` would truncate the word at the first nested element and
    silently drop those letters. Any nested ``<note>`` (the editorial
    large-letter explanation) is excluded; its tail text is kept."""
    parts = [el.text or ""]
    for sub in el:
        if _local(sub.tag) != "note":
            parts.append(_word_text(sub))
        parts.append(sub.tail or "")
    return "".join(parts)


def _assert_no_raw_markup(text: str) -> None:
    """WLC is in ``popup_versions._TRUSTED_HTML`` — its verse HTML is rendered
    RAW (not escaped). That trust is only valid because every RAW token is plain
    Hebrew plus the house ``<em>``/maqaf/paseq markup added here. If a source
    ``<w>``/``<seg>`` ever carried a literal ``<``, ``>``, or ``&`` it would break
    the EPUB XHTML (RSC-005) when emitted raw — so fail CLOSED at ingest rather
    than ship a broken popup (mint-10; mirrors extract_lxx_swete /
    extract_byzantine_nt). The assembled ``<em>…</em>`` string is NOT guarded —
    it legitimately contains ``<``/``>``."""
    if any(ch in text for ch in "<>&"):
        raise ValueError(
            f"WLC ingest: a raw OSIS token contains an HTML-special character (<>&) but the "
            f"verse is rendered as trusted HTML; refusing to emit. Token: {text[:80]!r}"
        )


def verse_to_em_html(verse_el: ET.Element) -> str:
    """Render one OSIS ``<verse>`` element as the project's em-per-word Hebrew.

    Walks the verse's child elements in document order, building word tokens:

    - ``<w>``  → word text with ``/`` morpheme separators removed.
    - ``x-maqqef`` (־) → glue: appends the maqaf and merges the *next* word into
      the same token (so ``אֶת־הָאוֹר`` is one ``<em>``); chains naturally.
    - ``x-sof-pasuq`` (׃) → appends to the current (final) word.
    - ``x-paseq`` (׀) → flushes and becomes its own standalone token.
    - ``x-pe`` / ``x-samekh`` / other segs → dropped (paragraph / editorial
      markers carry no verse text).

    Each token is wrapped in ``<em>…</em>`` and joined with single spaces. The
    output is byte-identical to the recovered base for verses already present
    there (pinned in ``tests/test_wlc_ingest.py``).
    """
    tokens: list[str] = []
    cur = ""
    pending_join = False  # the previous element was a maqaf → next <w> continues cur

    for child in verse_el:
        tag = _local(child.tag)
        if tag == "w":
            word = _word_text(child).replace("/", "")
            _assert_no_raw_markup(word)
            if pending_join:
                cur += word
                pending_join = False
            else:
                if cur:
                    tokens.append(cur)
                cur = word
        elif tag == "seg":
            stype = child.get("type")
            seg_text = child.text or ""
            _assert_no_raw_markup(seg_text)
            if stype == "x-maqqef":
                cur += seg_text
                pending_join = True
            elif stype == "x-sof-pasuq":
                cur += seg_text
            elif stype == "x-paseq":
                if cur:
                    tokens.append(cur)
                    cur = ""
                tokens.append(seg_text)
                pending_join = False
            # x-pe, x-samekh, and any other seg type: dropped (no verse text).

    if cur:
        tokens.append(cur)
    return " ".join(f"<em>{t}</em>" for t in tokens)


def _parse_osis_id(osis_id: str | None) -> tuple[str, int, int] | None:
    """``Gen.1.4`` → ``("Gen", 1, 4)``; ``None`` for malformed/sub-verse ids."""
    if not osis_id:
        return None
    parts = osis_id.split(".")
    if len(parts) != 3:
        return None
    book, ch, vs = parts
    if not (ch.isdigit() and vs.isdigit()):
        return None
    return (book, int(ch), int(vs))


def extract_book(osis_path, kjv_map: dict) -> list[tuple[int, int, str]]:
    """Parse one OSIS book file → a sorted ``[(chapter, verse, em_html), …]``
    list keyed by **canonical (KJV)** coordinates.

    Each verse is rendered by :func:`verse_to_em_html`, then remapped from its
    WLC (Masoretic) coordinate via ``kjv_map`` (from
    :func:`scripts.core.versification.wlc_to_kjv_map`). Verses absent from the
    map keep identity numbering — except a verse whose identity coordinate is
    already *claimed* by an explicit map entry, which is a WLC superscription /
    pre-verse with no KJV slot and is dropped (e.g. the Hebrew title at WLC
    Ps 3:1 when WLC 3:2 → KJV 3:1).
    """
    root = ET.parse(osis_path).getroot()
    claimed = set(kjv_map.values())
    by_kjv: dict[tuple[int, int], str] = {}
    for verse_el in root.iter(OSIS_NS + "verse"):
        coord = _parse_osis_id(verse_el.get("osisID"))
        if coord is None:
            continue
        target = kjv_map.get(coord)
        if target is None:
            if coord in claimed:
                continue  # WLC superscription / pre-verse — no canonical slot
            target = coord
        _book, ch, vs = target
        by_kjv[(ch, vs)] = verse_to_em_html(verse_el)
    return [(ch, vs, by_kjv[(ch, vs)]) for (ch, vs) in sorted(by_kjv)]


# ----------------------------------------------------------------------
# Per-book module emission (mirrors scripts/extract_translation.py's format)
# ----------------------------------------------------------------------


def _py_repr_text(s: str) -> str:
    """Verse text as a Python literal — double-quoted when safe, else repr()."""
    if "\\" not in s and '"' not in s:
        return f'"{s}"'
    return repr(s)


def write_book_module(out_path, translation: str, book_code: str, verses: list[tuple[int, int, str]]) -> None:
    """Emit one ``content/translations/<id>/<book>.py`` — a flat VERSES list,
    one verse per line, loaded at runtime via ``ast.literal_eval`` (never run)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f'"""Translation: {translation} · Book: {book_code}',
        "",
        "AUTO-GENERATED by scripts/extract_wlc_morphhb.py.",
        "Do not edit by hand — re-run extraction to regenerate.",
        '"""',
        f'TRANSLATION = "{translation}"',
        f'BOOK = "{book_code}"',
        "VERSES = [",
    ]
    for c, v, t in sorted(verses, key=lambda r: (r[0], r[1])):
        lines.append(f"    ({c}, {v}, {_py_repr_text(t)}),")
    lines.append("]")
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_meta(out_dir, stats: dict) -> None:
    """Write ``_meta.yaml`` describing the full morphhb ingest + provenance."""
    today = _dt.date.today().isoformat()
    lines = [
        "# Translation metadata — generated by scripts/extract_wlc_morphhb.py",
        "# Full WLC Hebrew ingest from the OpenScriptures morphhb OSIS source.",
        "",
        "id: wlc",
        'title: "Westminster Leningrad Codex (Hebrew)"',
        'short_title: "WLC"',
        'license: "Public Domain"',
        "source:",
        '  publisher: "OpenScriptures morphhb (OSHB); WLC = Leningrad Codex B19A, Kimball transcription"',
        '  url: "https://github.com/openscriptures/morphhb"',
        '  package: "morphhb OSIS wlc/*.xml + VerseMap.xml"',
        f"  fetched: {today}",
        "  source_date: 1008",
        "stats:",
        f"  books: {stats['books']}",
        f"  verses: {stats['verses']}",
        "  books_outside_kjv: 0",
        "notes: |",
        "  Full 39-book Hebrew (Masoretic) ingest of the Westminster Leningrad",
        "  Codex from the OpenScriptures morphhb OSIS source. Each verse renders",
        "  as <em>-per-word HTML (morpheme '/' separators stripped; maqaf-joined",
        "  words kept in one <em>; sof-pasuq glued to the last word; paseq",
        "  standalone). Coordinates are remapped from Masoretic to canonical KJV",
        "  numbering via morphhb's VerseMap.xml (Genesis 31/32 boundary; Psalm",
        "  superscriptions counted as Hebrew verse 1; etc.). Trusted",
        "  pre-formatted HTML — popup_versions.is_trusted_html('wlc') passes it",
        "  to the aside renderer raw. Regenerable: re-run the extractor.",
        "  License: the WLC pointed text is Public Domain; only that text is",
        "  redistributed (OSHB morphology/lemma data, CC-BY-4.0, is not used).",
        '  Hebrew renders right-to-left (RTL) via dir="rtl" in the popup pipeline.',
    ]
    Path(out_dir).joinpath("_meta.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------


def extract_all(source_dir, out_dir, *, dry_run: bool = False) -> dict:
    """Ingest every OSIS book present under ``source_dir`` into ``out_dir``.

    Loads the WLC→KJV map once from ``source_dir/VerseMap.xml`` (passed whole to
    each book — coordinates carry their book name, so cross-book lookups can't
    collide). A missing book file is skipped, never an error. Returns stats.
    """
    from scripts.core import versification as vsf

    source_dir = Path(source_dir)
    out_dir = Path(out_dir)
    vm = source_dir / "VerseMap.xml"
    kjv_map = vsf.wlc_to_kjv_map(vm) if vm.is_file() else {}

    stats: dict = {"books": 0, "verses": 0, "by_book": {}}
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
    for osis_book, code in OSIS_BOOK_TO_CODE.items():
        src = source_dir / f"{osis_book}.xml"
        if not src.is_file():
            continue
        verses = extract_book(src, kjv_map)
        stats["by_book"][code] = len(verses)
        stats["books"] += 1
        stats["verses"] += len(verses)
        if not dry_run:
            write_book_module(out_dir / f"{code}.py", "wlc", code, verses)
    if not dry_run:
        write_meta(out_dir, stats)
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest WLC Hebrew from morphhb OSIS into the translation store.")
    ap.add_argument("--source", default=str(DEFAULT_SOURCE), help="morphhb wlc/ dir (OSIS books + VerseMap.xml)")
    ap.add_argument("--out", default=str(TRANSLATIONS_DIR / "wlc"), help="output translation dir")
    ap.add_argument("--dry-run", action="store_true", help="parse + report without writing")
    args = ap.parse_args()
    src = Path(args.source)
    if not src.is_dir():
        raise SystemExit(f"missing source dir: {src}")
    stats = extract_all(src, Path(args.out), dry_run=args.dry_run)
    print(f"WLC: {stats['books']} books, {stats['verses']:,} verses{' (dry-run)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
