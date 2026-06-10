#!/usr/bin/env python3
"""kobo_tap_calibration.py — emit the K-R4-2 calibration tap-list from a built artifact.

The Kobo e-ink Footnote-preview heuristic DECLINES large popups and navigates
instead (the round-4 "teleport"/"nothing" class). Round-4 bracketed the
threshold at 3,313 < T <= 7,748 *tag-stripped* characters (what the preview
heuristic sees — kepub spans add no text, so EPUB and kepub measure alike).

This tool scans a built EPUB/kepub, measures every popup aside's stripped
size, and picks REAL badges nearest the probe targets (~3.5k/4.5k/5.5k/6.5k/
7.5k) inside the bracket, plus the two known controls (the largest aside at or
under the proven-POP floor and the round-4 proven-decline point). One device
tap-pass over the list pins T so the K-R4-2 cap is data-set, not guessed
(QA note: docs/superpowers/notes/2026-06-10-kobo-round4-device-qa.md).

    py -3 dev/kobo_tap_calibration.py build/round5/<artifact>.kepub.epub
    py -3 dev/kobo_tap_calibration.py <artifact> --targets 3500,4500,5500,6500,7500
"""

from __future__ import annotations

import argparse
import html as html_mod
import re
import zipfile
from pathlib import Path

# Round-4 bracket (stripped chars): gen-1-3 (3,313) POPS; gen-1-26 (7,748) declines.
BRACKET_LO = 3_313  # largest size PROVEN to pop (inclusive control)
BRACKET_HI = 7_748  # smallest size PROVEN to decline (inclusive control)
DEFAULT_TARGETS = (3_500, 4_500, 5_500, 6_500, 7_500)

_ASIDE_RE = re.compile(
    r'<aside\b[^>]*\bepub:type="footnote"[^>]*>.*?</aside>',
    re.DOTALL | re.IGNORECASE,
)
_ID_RE = re.compile(r'\bid="([^"]+)"')
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
# vnotes-gen-1-3 / vnote-gen-1-3 / vnote-gen-1-3-2 → (gen, 1, 3)
_COORD_RE = re.compile(r"^v?notes?-([a-z0-9]{2,3})-(\d+)-(\d+)")


def stripped_len(aside_html: str) -> int:
    """Tag-stripped, entity-decoded, whitespace-collapsed character count —
    the round-4 measurement the bracket numbers were taken in."""
    text = _TAG_RE.sub("", aside_html)
    text = html_mod.unescape(text)
    return len(_WS_RE.sub(" ", text).strip())


def scan_artifact(path: Path) -> list[dict]:
    """Every popup aside in the zip: [{id, file, stripped, coord}]."""
    out: list[dict] = []
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not name.endswith((".html", ".xhtml")):
                continue
            text = zf.read(name).decode("utf-8", errors="replace")
            for m in _ASIDE_RE.finditer(text):
                block = m.group(0)
                mid = _ID_RE.search(block[:300])
                aid = mid.group(1) if mid else "?"
                cm = _COORD_RE.match(aid)
                coord = f"{cm.group(1)} {cm.group(2)}:{cm.group(3)}" if cm else "?"
                out.append({"id": aid, "file": name, "stripped": stripped_len(block), "coord": coord})
    return out


def _book_order_key(item: dict) -> tuple:
    # Prefer early-Bible probes (easy to navigate to on the device); gen first.
    code = item["coord"].split(" ")[0] if item["coord"] != "?" else "zzz"
    return (0 if code == "gen" else 1, item["file"], item["id"])


def pick_probes(asides: list[dict], targets: tuple[int, ...]) -> list[dict]:
    """Nearest distinct real aside per probe target, inside the open bracket."""
    pool = [a for a in asides if BRACKET_LO < a["stripped"] < BRACKET_HI and a["coord"] != "?"]
    picks: list[dict] = []
    used: set[str] = set()
    for t in targets:
        ranked = sorted(
            (a for a in pool if a["id"] not in used), key=lambda a: (abs(a["stripped"] - t), _book_order_key(a))
        )
        if ranked:
            probe = dict(ranked[0])
            probe["target"] = t
            picks.append(probe)
            used.add(probe["id"])
    return picks


def controls(asides: list[dict]) -> tuple[dict | None, dict | None]:
    """(largest aside <= proven-POP floor, smallest aside >= proven-decline point)."""
    lo_pool = [a for a in asides if a["stripped"] <= BRACKET_LO and a["coord"] != "?"]
    hi_pool = [a for a in asides if a["stripped"] >= BRACKET_HI and a["coord"] != "?"]
    lo = max(lo_pool, key=lambda a: a["stripped"], default=None)
    hi = min(hi_pool, key=lambda a: a["stripped"], default=None)
    return lo, hi


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("artifact", type=Path, help="built .epub / .kepub.epub")
    p.add_argument(
        "--targets",
        default=",".join(str(t) for t in DEFAULT_TARGETS),
        help="comma-separated stripped-size probe targets",
    )
    args = p.parse_args(argv)
    targets = tuple(int(x) for x in args.targets.split(","))

    asides = scan_artifact(args.artifact)
    if not asides:
        print("no popup asides found — wrong artifact?")
        return 1
    probes = pick_probes(asides, targets)
    lo, hi = controls(asides)

    print(f"# K-R4-2 calibration tap-list — {args.artifact.name}")
    print(f"# {len(asides)} popup asides scanned; bracket {BRACKET_LO:,} < T <= {BRACKET_HI:,} stripped chars")
    print("#")
    print("# Device protocol (same conditions as round 4): open the verse, tap the")
    print("# badge ONCE, record P = pops in place / J = jumps elsewhere / N = nothing.")
    print("# T lands between the largest P and the smallest J/N.")
    print()
    rows: list[tuple[str, dict]] = []
    if lo:
        rows.append(("control (expect P)", lo))
    for pr in probes:
        rows.append((f"probe ~{pr['target']:,}", pr))
    if hi:
        rows.append(("control (expect J/N)", hi))
    print(f"{'role':22} {'verse':12} {'stripped':>9}  aside id (file)")
    for role, a in rows:
        print(f"{role:22} {a['coord']:12} {a['stripped']:>9,}  {a['id']}  ({a['file']})")
    print()
    dist = sorted(a["stripped"] for a in asides)
    n = len(dist)
    print(f"# distribution: min {dist[0]:,} · p50 {dist[n // 2]:,} · p90 {dist[int(n * 0.9)]:,} · max {dist[-1]:,}")
    over = sum(1 for s in dist if s > BRACKET_LO)
    print(f"# asides over the proven-POP floor ({BRACKET_LO:,}): {over} of {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
