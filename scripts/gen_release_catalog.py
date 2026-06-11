"""Generate the website Downloads-catalog manifest — matrix M1 (spec §5).

Reads the release's ACTUAL asset list + SHA256SUMS (never expectations) and
writes ``website/src/data/catalog.json`` for ``website/build.mjs`` to inline
at site build — static site, no client fetch, no build step added. The
format table comes from ``FORMAT_MATRIX`` (build_edition.py) and the edition
rows from editions.yaml: the one-homes, never re-typed here (review MED).

Never-over-claim is structural:
  • FULL-COUNT COLUMN GATING — a format column goes live only when EVERY
    edition's SIGNATURE-colour asset (its own cover's colour — spec
    addendum 2026-06-11) is in the release; M2 variant colours light per
    cell, only where that edition's asset exists. Partial uploads
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

# Same never-remove-live rule for the flagship EPUB the site serves today:
# while the 'everywhere' column is dark (signature assets not yet all
# published), the Ethiopian card keeps offering the live v0.1.0 flagship.
# Retires automatically once the column lights.
LEGACY_FLAGSHIP_CELL = {
    "name": "YHWH-Ethiopian-Bible-v0.1.0.epub",
    "url": (
        "https://github.com/gringoboggy/yhwh-bible-platform/releases/download/v0.1.0/YHWH-Ethiopian-Bible-v0.1.0.epub"
    ),
    "edition": "ethiopian-tewahedo",
    "note": "v0.1.0 flagship EPUB — the live offering until the everywhere column ships",
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
    signatures: dict[str, tuple[str, str]],
    repo: str = DEFAULT_REPO,
) -> dict:
    """The pure manifest computation: which format columns are live and each
    live cell's name/url/sha256, from the REAL asset list.

    ``signatures`` maps edition id → its ``(design, colour)`` cover identity
    (``edition_cover_signature``; injected so this stays a pure function).
    Spec addendum 2026-06-11: every edition's catalog asset wears its OWN
    cover, so full-count gating keys on each edition's SIGNATURE-colour
    asset — a format column goes live only when every edition's signature
    asset is published. Extra colours (M2 variants) light per cell, only
    where that edition's variant asset really exists."""
    from scripts.build_edition import COVER_COLOURS, FORMAT_MATRIX, catalog_asset_name

    version = tag.removeprefix("v")
    present = set(asset_names)
    base_url = f"https://github.com/{repo}/releases/download/{tag}"
    missing = [e for e in edition_ids if e not in signatures]
    if missing:
        raise ValueError(f"no cover signature for edition(s): {missing}")

    formats: list[dict] = []
    for fmt in FORMAT_MATRIX:
        # The column is live iff EVERY edition's signature-colour asset exists.
        live = all(catalog_asset_name(e, version, fmt["id"], signatures[e][1]) in present for e in edition_ids)
        cells: dict[str, dict] = {}
        if live:
            for e in edition_ids:
                sig_colour = signatures[e][1]
                row: dict[str, dict] = {}
                # Signature colour first (the card's download), then any M2
                # variant colours that REALLY exist for this edition.
                for c in [sig_colour] + [c for c in COVER_COLOURS if c != sig_colour]:
                    name = catalog_asset_name(e, version, fmt["id"], c)
                    if name in present:
                        row[c] = {"name": name, "url": f"{base_url}/{name}", "sha256": sums.get(name, "")}
                cells[e] = row
        entry: dict = {
            "id": fmt["id"],
            "label": fmt["label"],
            "packaging": fmt["packaging"],
            "phase": fmt["phase"],
            "live": live,
            "cells": cells,
        }
        if fmt["id"] == "kobo" and not live:
            entry["legacy_cell"] = dict(LEGACY_KOBO_CELL)
        if fmt["id"] == "everywhere" and not live:
            entry["legacy_cell"] = dict(LEGACY_FLAGSHIP_CELL)
        formats.append(entry)

    return {
        "tag": tag,
        "version": version,
        "base_url": base_url,
        "editions": [
            {
                "id": e,
                "signature_design": signatures[e][0],
                "signature_colour": signatures[e][1],
                "cover": f"covers/{e}.jpg",
            }
            for e in edition_ids
        ],
        "formats": formats,
    }


_DESIGN_LABELS = {
    "01_ornate_leafy": "ornate leafy",
    "02_classical_corner": "classical corner",
    "03_beadline": "beadline",
    "04_minimal_lines": "minimal lines",
    "05_missal_central": "missal central",
}


def _design_label(design: str) -> str:
    """Human label for a template design stem ("02_classical_corner" →
    "classical corner"); unknown stems degrade to de-underscored text."""
    return _DESIGN_LABELS.get(design, design.split("_", 1)[-1].replace("_", " "))


def render_catalog_fragment(catalog: dict) -> str:
    """The no-JS-first HTML fragment ``build.mjs`` inlines at
    ``{{release_catalog}}``: one cover CARD per edition — the edition's own
    cover art (its signature design + colour, the same cover inside the
    file) with a download link per LIVE format. While columns are dark the
    cards still showcase the covers, download-free except the never-remove-
    live legacy offerings (the flagship EPUB + kepub on the Ethiopian card).
    Fully usable without JavaScript; copy stays count-free (the 83-corollary
    lives on the page, not here)."""
    from html import escape

    live = [f for f in catalog["formats"] if f["live"]]
    by_id = {f["id"]: f for f in catalog["formats"]}
    parts: list[str] = []

    if live:
        # The imperative lives HERE, not in the static page prose, so the
        # page never instructs a pick the dark state can't honour.
        parts.append("<p class='prose'>Pick your edition, then the device you read on.</p>")
    else:
        parts.append(
            "<p class='prose'>The per-device downloads for these editions are being "
            "prepared — the Ethiopian Bible files below are live today, and every "
            "edition joins it as its builds are published.</p>"
        )

    cards: list[str] = []
    for e in catalog["editions"]:
        eid = e["id"]
        title = e.get("title") or eid
        alt = f"{title} cover — {_design_label(e.get('signature_design', ''))} in {e.get('signature_colour', '')}"
        buttons: list[str] = []
        for fmt in live:
            cell = fmt["cells"].get(eid) or {}
            sig = cell.get(e.get("signature_colour", ""))
            if sig:
                buttons.append(f"<a href='{escape(sig['url'])}' download>{escape(fmt['label'])}</a>")
        # Never-remove-live: the flagship files the site serves today stay
        # offered on the Ethiopian card while their columns are dark.
        for fmt_id, label in (("everywhere", "Computer & everywhere else"), ("kobo", "Kobo (.kepub)")):
            fmt = by_id.get(fmt_id)
            legacy = (fmt or {}).get("legacy_cell")
            if fmt is not None and not fmt["live"] and legacy and legacy["edition"] == eid:
                buttons.append(f"<a href='{escape(legacy['url'])}' download>{escape(label)}</a>")
        body = f"<h3>{escape(title)}</h3>"
        if buttons:
            body += f"<p class='dl-row'>{''.join(buttons)}</p>"
        cards.append(
            "<article class='card card-static'>"
            f"<img class='cover' src='{{{{root}}}}{escape(e.get('cover', ''))}' alt='{escape(alt)}' "
            "width='800' height='1200' loading='lazy'>"
            f"<div class='card-body'>{body}</div>"
            "</article>"
        )
    parts.append(f"<div class='grid gallery catalog-cards'>{''.join(cards)}</div>")

    kobo = by_id.get("kobo")
    if kobo is not None and (kobo["live"] or kobo.get("legacy_cell")):
        parts.append(
            "<p class='platform-note'>On a <strong>Kobo</strong>, sideload the "
            "<code>.kepub.epub</code> — it turns on the tap-to-read footnote popups. "
            "On Apple Books and most other readers, use the plain <code>.epub</code>.</p>"  # term-ref-ok: free-catalog platform label, not store distribution
        )
    base_url = catalog.get("base_url") or f"https://github.com/{DEFAULT_REPO}/releases/download/{catalog['tag']}"
    parts.append(
        "<p class='platform-note'>Verify any download against the release's "
        f"<a href='{escape(base_url)}/SHA256SUMS.txt'>SHA256SUMS.txt</a>.</p>"
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


def check_no_withdrawal(previous: dict, new: dict) -> list[str]:
    """Never-remove-live, made structural (review 2026-06-11 finding #1): the
    format columns the committed catalog already offers must not silently go
    dark — a regen against a release that hasn't published the new asset
    complement yet would withdraw live download links from the site on the
    next deploy. Returns the ids of previously-live formats the new manifest
    darkens (empty = safe)."""
    prev_live = {f["id"] for f in previous.get("formats", []) if f.get("live")}
    new_live = {f["id"] for f in new.get("formats", []) if f.get("live")}
    return sorted(prev_live - new_live)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate website/src/data/catalog.json from a release's real assets.")
    p.add_argument("--tag", required=True, help="release tag (e.g. v0.1.0)")
    p.add_argument("--repo", default=DEFAULT_REPO)
    p.add_argument("--assets-file", type=Path, help="JSON list of asset names (offline/test; skips gh)")
    p.add_argument("--sums-file", type=Path, help="SHA256SUMS.txt path (offline/test; skips gh)")
    p.add_argument("-o", "--output", type=Path, default=DEFAULT_OUT)
    p.add_argument(
        "--allow-withdraw",
        action="store_true",
        help="permit a previously-live format column to go dark (deliberate withdrawals only)",
    )
    args = p.parse_args(argv)

    from scripts.build_edition import edition_cover_signature
    from scripts.core import config

    editions = [e for e in config.load_editions() if not e.get("standalone")]
    edition_ids = [e["id"] for e in editions]
    titles = {e["id"]: (e.get("display_name") or e.get("title") or e["id"]) for e in editions}
    signatures = {e: edition_cover_signature(e) for e in edition_ids}
    for e in edition_ids:
        # The card displays website/covers/<id>.jpg — a missing file would
        # ship a broken-image card, so fail loudly here, not on the live site.
        cover = REPO_ROOT / "website" / "covers" / f"{e}.jpg"
        if not cover.is_file():
            raise FileNotFoundError(f"website cover missing for catalog card: {cover}")

    if args.assets_file:
        asset_names = json.loads(args.assets_file.read_text(encoding="utf-8"))
    else:
        asset_names = fetch_release_asset_names(args.tag, args.repo)
    if args.sums_file:
        sums = parse_sums(args.sums_file.read_text(encoding="utf-8"))
    else:
        sums = fetch_release_sums(args.tag, args.repo)

    catalog = compute_catalog(
        asset_names, sums, tag=args.tag, edition_ids=edition_ids, signatures=signatures, repo=args.repo
    )
    for entry in catalog["editions"]:
        entry["title"] = titles[entry["id"]]

    if args.output.is_file() and not args.allow_withdraw:
        previous = json.loads(args.output.read_text(encoding="utf-8"))
        withdrawn = check_no_withdrawal(previous, catalog)
        if withdrawn:
            print(
                f"REFUSING to write {args.output}: previously-live format column(s) {withdrawn} would go "
                "dark — the next site deploy would withdraw live download links (never-remove-live). "
                "Publish the release's full asset complement first, or pass --allow-withdraw for a "
                "deliberate withdrawal.",
                file=sys.stderr,
            )
            return 1

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
