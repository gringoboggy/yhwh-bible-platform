#!/usr/bin/env python3
"""Batch-fill Kings manifest folios for P0 tail: 1ki 19–22 + 2ki 1–25.

Mappings from SAMKINGS_FOLIO_ANCHOR_INDEX §17 + MARATHON_LOOKAHEAD GG bands;
CAM folios are boundary-generous sequential estimates (vision-confirmed at
transcription). Status stays ``pending``.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

from scripts.fill_manifest_entry import fill  # noqa: E402

MANIFEST = REPO / "content/manuscript/kings/manifest.yaml"


def _gg(book: str, *folios: str) -> list[str]:
    folder = "1-Kings" if book == "1ki" else "2-Kings"
    prefix = "1-Kings" if book == "1ki" else "2-Kings"
    return [f"GAPS/2_Kings/GG-00106/{folder}/{prefix}_{f}.jpg" for f in folios]


def _cam(book: str, ch: int, *folios: str) -> list[str]:
    return [f"GAPS/2_Kings/Cambridge-Add-1570-hires/MS-ADD-01570_{f}_{book}{ch}_hires.jpg" for f in folios]


# (book, chapter, gg_folios, cam_folios)
_ENTRIES: list[tuple[str, int, list[str], list[str]]] = [
    # 1ki 19–22 — GG on disk f038v–f040v; CAM continues past ch18 (f139v)
    ("1ki", 19, ["f038v", "f039r"], ["f140r", "f140v", "f141r"]),
    ("1ki", 20, ["f039r", "f039v", "f040r"], ["f141v", "f142r", "f142v"]),
    ("1ki", 21, ["f040r", "f040v"], ["f142v", "f143r", "f143v"]),
    ("1ki", 22, ["f040r", "f040v"], ["f143v", "f144r", "f144v", "f145r", "f146v"]),
    # 2ki 1–25 — GG on disk f040v–f053r; CAM from ~f147 (anchor §8)
    ("2ki", 1, ["f040v"], ["f147r", "f147v"]),
    ("2ki", 2, ["f040v", "f041r"], ["f147v", "f148r"]),
    ("2ki", 3, ["f041r"], ["f148r", "f148v"]),
    ("2ki", 4, ["f041v"], ["f148v", "f149r", "f149v"]),
    ("2ki", 5, ["f042v"], ["f149v", "f150r"]),
    ("2ki", 6, ["f043r"], ["f150r", "f150v", "f151r"]),
    ("2ki", 7, ["f043v"], ["f151r", "f151v"]),
    ("2ki", 8, ["f044r"], ["f151v", "f152r", "f152v"]),
    ("2ki", 9, ["f044v"], ["f152v", "f153r"]),
    ("2ki", 10, ["f045r"], ["f153r", "f153v", "f154r"]),
    ("2ki", 11, ["f045v"], ["f154r", "f154v"]),
    ("2ki", 12, ["f046r"], ["f154v", "f155r"]),
    ("2ki", 13, ["f046v"], ["f155r", "f155v", "f156r"]),
    ("2ki", 14, ["f047r", "f047v"], ["f156r", "f156v", "f157r"]),
    ("2ki", 15, ["f047v", "f048v"], ["f157r", "f157v", "f158r", "f158v"]),
    ("2ki", 16, ["f048v", "f049r"], ["f158v", "f159r"]),
    ("2ki", 17, ["f049r", "f050r"], ["f159r", "f159v", "f160r", "f160v", "f161r"]),
    ("2ki", 18, ["f050r", "f050v"], ["f161r", "f161v", "f162r"]),
    ("2ki", 19, ["f050v", "f051r"], ["f162r", "f162v", "f163r"]),
    ("2ki", 20, ["f051r"], ["f163r", "f163v"]),
    ("2ki", 21, ["f051r", "f051v"], ["f163v", "f164r"]),
    ("2ki", 22, ["f051v"], ["f164r", "f164v"]),
    ("2ki", 23, ["f051v", "f052v"], ["f164v", "f165r", "f165v", "f166r"]),
    ("2ki", 24, ["f052v", "f053r"], ["f166r", "f166v", "f167r"]),
    ("2ki", 25, ["f053r"], ["f167r", "f167v", "f168r"]),
]


def main() -> int:
    for book, ch, gg_f, cam_f in _ENTRIES:
        fill(
            MANIFEST,
            book,
            ch,
            gg_f,
            _gg(book, *gg_f),
            cam_f,
            _cam(book, ch, *cam_f),
        )
    print(f"filled {len(_ENTRIES)} chapters in {MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
