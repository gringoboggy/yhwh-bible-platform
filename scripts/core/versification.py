"""scripts.core.versification — adapters mapping a translation's own verse
numbering onto the project's canonical (KJV/WEB) numbering.

Phase 2 of the fully-customizable-builder roadmap; the seam the registry's
``popup_versions.normalize_coord`` documents. The first adapter loads the
OpenScriptures morphhb ``VerseMap.xml`` — a catalogue of the WLC (Masoretic) ↔
KJV differences (the Genesis 31/32 chapter boundary, Psalm superscriptions
counted as Hebrew verse 1, …). Only the *differences* are listed; every other
verse maps identity, so callers default with ``map.get(coord, coord)``.

Parsing is XML-only (ElementTree) — translation/versification data is never
executed as code (RULES §7.1).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

Coord = tuple[str, int, int]  # (OSIS book name, chapter, verse)


def _local(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def _parse_ref(ref: str | None) -> Coord | None:
    """Parse an OSIS verse ref ``Book.C.V`` → ``(Book, C, V)``.

    Returns ``None`` for sub-verse partial refs (``…!a``) or malformed refs, so
    only clean verse-level entries participate in the coord map.
    """
    if not ref or "!" in ref:
        return None
    parts = ref.split(".")
    if len(parts) != 3:
        return None
    book, ch, vs = parts
    if not (ch.isdigit() and vs.isdigit()):
        return None
    return (book, int(ch), int(vs))


def parse_versemap(path) -> list[tuple[Coord, Coord, str]]:
    """Return ``[(wlc_coord, kjv_coord, type), …]`` for each clean verse-level
    entry in a morphhb ``VerseMap.xml``."""
    root = ET.parse(path).getroot()
    out: list[tuple[Coord, Coord, str]] = []
    for el in root.iter():
        if _local(el.tag) != "verse":
            continue
        wlc = _parse_ref(el.get("wlc"))
        kjv = _parse_ref(el.get("kjv"))
        if wlc is None or kjv is None:
            continue
        out.append((wlc, kjv, el.get("type") or "full"))
    return out


def wlc_to_kjv_map(path) -> dict[Coord, Coord]:
    """WLC (Masoretic) → KJV coord map, from the ``full`` entries only.

    ``partial`` (sub-verse ``!a``/``!b``) entries are excluded — a sub-verse
    split can't be represented at whole-verse granularity, so those verses keep
    identity numbering (a documented Phase-2 limitation). The set of map *values*
    is the set of KJV coords explicitly claimed, which lets an ingester drop a
    WLC superscription verse whose identity coord is already taken.
    """
    return {wlc: kjv for wlc, kjv, typ in parse_versemap(path) if typ == "full"}
