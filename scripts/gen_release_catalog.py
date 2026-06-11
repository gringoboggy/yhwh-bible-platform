"""Generate the website Downloads-catalog manifest — matrix M1 (spec §5).

Reads the release's ACTUAL asset list + SHA256SUMS (never expectations) and
writes ``website/src/data/catalog.json`` for ``website/build.mjs`` to inline
at site build — static site, no client fetch, no build step added. The
format table comes from ``FORMAT_MATRIX`` (build_edition.py) and the edition
rows from editions.yaml: the one-homes, never re-typed here (review MED).

Never-over-claim is structural:
  • FULL-COUNT COLUMN GATING — a colour swatch shows only when EVERY
    edition has that colour's asset in the release; a format column goes
    live only when at least one colour is complete. Partial uploads
    under-show, never 404.
  • the GitHub asset listing is read PAGINATED (``gh api --paginate``) — a
    ~232-asset release truncates a naive GET at 100 and columns would
    silently vanish or over-claim (review MED).
  • never-remove-live — until the M3 Kobo column ships, the kobo format
    carries the v0.1.0 flagship kepub the site already serves as a LEGACY
    cell; shipping the catalog must not remove a live offering.

Usage:
    py -3 scripts/gen_release_catalog.py --tag v0.1.0            # live (gh)
    py -3 scripts/gen_release_catalog.py --tag v0.1.0 \
        --assets-file assets.json --sums-file SHA256SUMS.txt     # offline
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))  # CLI runs put scripts/ on sys.path, not the repo root

DEFAULT_OUT = REPO_ROOT / "website" / "src" / "data" / "catalog.json"
DEFAULT_REPO = "gringoboggy/yhwh-bible-platform"

# Never-remove-live (review MED): the Kobo cell the site serves TODAY. Stays
# the kobo column's offering until M3 lights the real column, then retires
# automatically (it is attached only while the column is not live).
LEGACY_KOBO_CELL = {
    "name": "YHWH-Ethiopian-Bible-v0.1.0.kepub.epub",
    "url": (
        "https://github.com/gringoboggy/yhwh-bible-platform"
        "/releases/download/v0.1.0/YHWH-Ethiopian-Bible-v0.1.0.kepub.epub"
    ),
    "edition": "ethiopian-tewahedo",
    "note": "v0.1.0 flagship kepub — the live Kobo offering until the M3 column ships",
}

_SUM_LINE_RE = re.compile(r"^([0-9a-fA-F]{64})\s+\*?(.+)$")


def parse_sums(text: str) -> dict[str, str]:
    """``sha256sum``-format lines → {asset name: hex digest}; anything that
    isn't a sum line is skipped (the release file may carry no/odd lines)."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        m = _SUM_LINE_RE.match(line.strip())
        if m:
            out[m.group(2).strip()] = m.group(1).lower()
    return out


def compute_catalog(
    asset_names: list[str],
    sums: dict[str, str],
    *,
    tag: str,
    edition_ids: list[str],
    repo: str = DEFAULT_REPO,
) -> dict:
    """The pure manifest computation: which columns/swatches are live and
    each live cell's name/url/sha256, from the REAL asset list."""
    from scripts.build_edition import COVER_COLOURS, FORMAT_MATRIX, catalog_asset_name

    version = tag.removeprefix("v")
    present = set(asset_names)
    base_url = f"https://github.com/{repo}/releases/download/{tag}"

    formats: list[dict] = []
    for fmt in FORMAT_MATRIX:
        # A colour is complete iff EVERY edition's asset for it is present.
        complete_colours = [
            c
            for c in COVER_COLOURS
            if all(catalog_asset_name(e, version, fmt["id"], c) in present for e in edition_ids)
        ]
        cells: dict[str, dict] = {}
        for e in edition_ids:
            row: dict[str, dict] = {}
            for c in complete_colours:
                name = catalog_asset_name(e, version, fmt["id"], c)
                row[c] = {"name": name, "url": f"{base_url}/{name}", "sha256": sums.get(name, "")}
            if row:
                cells[e] = row
        entry: dict = {
            "id": fmt["id"],
            "label": fmt["label"],
            "packaging": fmt["packaging"],
            "phase": fmt["phase"],
            "live": bool(complete_colours),
            "colours": complete_colours,
            "cells": cells,
        }
        if fmt["id"] == "kobo" and not entry["live"]:
            entry["legacy_cell"] = dict(LEGACY_KOBO_CELL)
        formats.append(entry)

    return {
        "tag": tag,
        "version": version,
        "editions": [{"id": e} for e in edition_ids],
        "formats": formats,
    }


def render_catalog_fragment(catalog: dict) -> str:
    """The no-JS-first HTML fragment ``build.mjs`` inlines at
    ``{{release_catalog}}`` (the geez-progress pattern): one ``<details>``
    per LIVE format, every edition's download link inside, plus the legacy
    Kobo offering while that column is dark. Fully usable without
    JavaScript; copy stays count-free (the 83-corollary lives on the page,
    not here)."""
    from html import escape

    titles = {e["id"]: e.get("title") or e["id"] for e in catalog["editions"]}
    live = [f for f in catalog["formats"] if f["live"]]
    parts: list[str] = []

    if not live:
        parts.append(
            "<p class='prose'>The per-device edition catalog is being prepared — "
            "the Ethiopian Bible downloads above are live today, and the other "
            "editions join them here as their builds are published.</p>"
        )
    for i, fmt in enumerate(live):
        rows: list[str] = []
        for e in catalog["editions"]:
            cells = fmt["cells"].get(e["id"], {})
            links = " · ".join(
                f"<a href='{escape(cell['url'])}' download>{escape(colour)}</a>"
                for colour, cell in sorted(cells.items())
            )
            if links:
                rows.append(f"<li><strong>{escape(titles[e['id']])}</strong> — {links}</li>")
        parts.append(
            f"<details class='catalog-format'{' open' if i == 0 else ''}>"
            f"<summary>{escape(fmt['label'])} <span class='meta'>(.{escape(fmt['packaging'])})</span></summary>"
            f"<ul class='catalog-list'>{''.join(rows)}</ul>"
            "</details>"
        )

    kobo = next((f for f in catalog["formats"] if f["id"] == "kobo"), None)
    if kobo is not None and not kobo["live"] and kobo.get("legacy_cell"):
        legacy = kobo["legacy_cell"]
        parts.append(
            "<p class='prose'>On a <strong>Kobo</strong>, the Ethiopian Tewahedo kepub is the "
            f"current offering: <a href='{escape(legacy['url'])}' download>{escape(legacy['name'])}</a> "
            "— per-edition Kobo builds join the catalog once calibrated.</p>"
        )
    if live:
        parts.append(
            "<p class='platform-note'>Verify any download against the release's "
            "<code>SHA256SUMS.txt</code> (linked above).</p>"
        )
    return "\n".join(parts)


def _gh(args: list[str]) -> str:
    res = subprocess.run(
        ["gh", *args], check=True, capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL
    )
    return res.stdout


def fetch_release_asset_names(tag: str, repo: str) -> list[str]:
    """Every asset name on the release, PAGINATED — the assets endpoint caps
    a page at 100 and the matrix release carries far more."""
    release = json.loads(_gh(["api", f"repos/{repo}/releases/tags/{tag}"]))
    out = _gh(["api", "--paginate", f"repos/{repo}/releases/{release['id']}/assets?per_page=100", "--jq", ".[].name"])
    return [line.strip() for line in out.splitlines() if line.strip()]


def fetch_release_sums(tag: str, repo: str) -> dict[str, str]:
    """The release's SHA256SUMS.txt (empty dict when it has none yet)."""
    with tempfile.TemporaryDirectory() as td:
        try:
            _gh(["release", "download", tag, "-p", "SHA256SUMS.txt", "-D", td, "--repo", repo])
        except subprocess.CalledProcessError:
            return {}
        p = Path(td) / "SHA256SUMS.txt"
        return parse_sums(p.read_text(encoding="utf-8")) if p.is_file() else {}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate website/src/data/catalog.json from a release's real assets.")
    p.add_argument("--tag", required=True, help="release tag (e.g. v0.1.0)")
    p.add_argument("--repo", default=DEFAULT_REPO)
    p.add_argument("--assets-file", type=Path, help="JSON list of asset names (offline/test; skips gh)")
    p.add_argument("--sums-file", type=Path, help="SHA256SUMS.txt path (offline/test; skips gh)")
    p.add_argument("-o", "--output", type=Path, default=DEFAULT_OUT)
    args = p.parse_args(argv)

    from scripts.core import config

    editions = [e for e in config.load_editions() if not e.get("standalone")]
    edition_ids = [e["id"] for e in editions]
    titles = {e["id"]: (e.get("display_name") or e.get("title") or e["id"]) for e in editions}

    if args.assets_file:
        asset_names = json.loads(args.assets_file.read_text(encoding="utf-8"))
    else:
        asset_names = fetch_release_asset_names(args.tag, args.repo)
    if args.sums_file:
        sums = parse_sums(args.sums_file.read_text(encoding="utf-8"))
    else:
        sums = fetch_release_sums(args.tag, args.repo)

    catalog = compute_catalog(asset_names, sums, tag=args.tag, edition_ids=edition_ids, repo=args.repo)
    for entry in catalog["editions"]:
        entry["title"] = titles[entry["id"]]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    fragment_path = args.output.with_name("catalog.html")
    fragment_path.write_text(render_catalog_fragment(catalog) + "\n", encoding="utf-8")
    live = [f["id"] for f in catalog["formats"] if f["live"]]
    # NOT relative_to(REPO_ROOT): -o may point anywhere (probe/sim runs).
    print(f"wrote {args.output} + {fragment_path.name} — {len(asset_names)} assets; live columns: {live or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
