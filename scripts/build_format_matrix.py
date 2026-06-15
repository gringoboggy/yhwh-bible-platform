"""Per-edition format-matrix driver — matrix M1 (format-matrix spec §4.3).

The CI workflow (.github/workflows/format-matrix.yml) runs ONE job per
edition with formats SERIAL inside it (review blocker #4: a single job
blows the 6-hour cap; 9+ jobs self-merging SHA256SUMS is a lost-update).
This driver is the job's payload, computed from the one-home tables —
FORMAT_MATRIX (build_edition.py) + editions.yaml — so the workflow YAML
never re-types the format table or the edition list (review MED).

Per phase-eligible format cell it:
  1. builds the base ONCE per distinct ``target_reader`` via the canonical
     CLI (``build_edition.py <id> --target-reader <t> --version <v>``);
  2. emits every colour of each cell (``cell_asset_names``): the SIGNATURE
     asset is the base copied under the signature colour's name (the
     edition's OWN cover is already embedded — spec addendum 2026-06-11),
     and each M2 variant colour is the base with the edition's own-design
     committed composite (content/covers/catalog/) swapped in
     deterministically via scripts/swap_epub_cover.py;
  3. gates the final asset: zip integrity + epubcheck 0/0/0/0 (and the
     dev/verify_kr2_build.py artifact gates) — skippable for local probes;
  4. writes a sha256sum-compatible ``sums-<edition>.txt`` the fan-in
     SHA256SUMS job merges (matrix jobs never touch the release's
     SHA256SUMS.txt themselves).

Usage:
    py -3 scripts/build_format_matrix.py --edition catholic-study \
        --version 0.1.0 --output-dir build/matrix [--phase M1] [--no-gates]
    py -3 scripts/build_format_matrix.py --list-editions
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))  # CLI runs put scripts/ on sys.path, not the repo root

CATALOG_COVERS_DIR = REPO_ROOT / "content" / "covers" / "catalog"


def matrix_cells(phase: str = "M1", formats: list[str] | None = None) -> list[dict]:
    """The FORMAT_MATRIX rows this run ships: every row whose gating phase is
    ``phase`` (or the explicit ``formats`` id list), in matrix order."""
    from scripts.build_edition import FORMAT_MATRIX

    if formats is not None:
        return [f for f in FORMAT_MATRIX if f["id"] in set(formats)]
    return [f for f in FORMAT_MATRIX if f["phase"] == phase]


def distinct_targets(cells: list[dict]) -> list[str]:
    """The distinct ``target_reader`` profiles among ``cells``, first-seen
    order — each is ONE base build (two formats sharing a profile share the
    base; their assets differ by cover)."""
    seen: list[str] = []
    for c in cells:
        if c["target_reader"] not in seen:
            seen.append(c["target_reader"])
    return seen


def base_build_target(cell: dict) -> str:
    """The ``--target-reader`` profile the cell's BASE build uses — equal to the
    cell's ``target_reader`` except for a ``post_process: kindle_safe`` cell
    (Kindle, K-KIN turn-84): the PROVEN Send-to-Kindle recipe builds the STANDARD
    everywhere base and applies ``scripts.core.kindle_post`` afterward, so its
    base build is ``everywhere`` — never the dormant, Previewer-oracle-tuned
    ``--target-reader kindle`` variant (that artifact FAILED Send-to-Kindle)."""
    return "everywhere" if cell.get("post_process") == "kindle_safe" else cell["target_reader"]


def distinct_base_targets(cells: list[dict]) -> list[str]:
    """The distinct BASE build profiles among ``cells`` (``base_build_target``),
    first-seen order — what the bases dict is keyed on (a kindle cell shares the
    everywhere base instead of triggering a second build)."""
    seen: list[str] = []
    for c in cells:
        bt = base_build_target(c)
        if bt not in seen:
            seen.append(bt)
    return seen


def cell_asset_name(edition_id: str, version: str, cell: dict) -> str:
    """The cell's release-asset name: ``catalog_asset_name`` with the
    EDITION's signature colour (its own cover's colour — the one identity
    the card displays and the file carries)."""
    from scripts.build_edition import catalog_asset_name, edition_cover_signature

    _design, colour = edition_cover_signature(edition_id)
    return catalog_asset_name(edition_id, version, cell["id"], colour)


def cell_asset_names(edition_id: str, version: str, cell: dict) -> list[tuple[str, str]]:
    """Every colour's ``(colour, asset name)`` for one cell — the signature
    colour FIRST (the card's default download), then the M2 variant colours
    in COVER_COLOURS order (spec Addendum A: variants are the edition's OWN
    design re-coloured, offered as per-cell picks)."""
    from scripts.build_edition import COVER_COLOURS, catalog_asset_name, edition_cover_signature

    _design, sig = edition_cover_signature(edition_id)
    colours = [sig] + [c for c in COVER_COLOURS if c != sig]
    return [(c, catalog_asset_name(edition_id, version, cell["id"], c)) for c in colours]


def variant_composite_path(edition_id: str, colour: str) -> Path:
    """The committed M2 composite for (edition × its OWN design × colour).
    Raises when missing: variants are GATED on the committed composites —
    a missing one must fail the job, never ship a wrong cover."""
    from scripts.build_edition import edition_cover_signature

    design, _sig = edition_cover_signature(edition_id)
    p = CATALOG_COVERS_DIR / f"{edition_id}_{design}_{colour}.jpg"
    if not p.is_file():
        raise FileNotFoundError(f"missing variant composite: {p} (generate_catalog_colour_variants + commit it)")
    return p


def standard_edition_ids() -> list[str]:
    """The catalog's edition rows: every non-standalone edition, in
    editions.yaml declaration order (the 9 canon/notes editions; the two
    standalone Bibles stay in LANE P until P2 constitutes them)."""
    from scripts.core import config

    return [e["id"] for e in config.load_editions() if not e.get("standalone")]


def write_sums(paths: list[Path], sums_path: Path) -> Path:
    """A sha256sum-compatible sums file (``<hex>  <basename>``), sorted by
    name so the fan-in merge is deterministic."""
    lines = sorted(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}" for p in paths)
    sums_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sums_path


def _run(cmd: list[str], **kwargs) -> None:
    """Run a child tool loudly; any failure kills the job (CI must never
    upload a half-gated asset)."""
    print(f"  $ {' '.join(str(c) for c in cmd)}", flush=True)
    subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL, **kwargs)


def _build_base(edition_id: str, version: str, target: str, build_dir: Path) -> Path:
    """One base build via the canonical CLI; returns the produced .epub."""
    build_dir.mkdir(parents=True, exist_ok=True)
    _run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_edition.py"),
            edition_id,
            "--target-reader",
            target,
            "--version",
            version,
            "--output-dir",
            str(build_dir),
            "--force",
        ],
        cwd=str(REPO_ROOT),
    )
    candidates = sorted(build_dir.glob("*.epub"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"build produced no .epub in {build_dir}")
    return candidates[0]


def _gate_asset(asset: Path) -> None:
    """The per-asset acceptance gates: zip integrity, epubcheck 0/0/0/0
    (via the project wrapper scripts/epubcheck.py — compose, don't
    recompute; --require hard-fails when the tool is missing, --strict
    fails on warnings too), and the K-R2/K-R3 artifact gates."""
    with zipfile.ZipFile(asset) as z:
        bad = z.testzip()
        if bad is not None:
            raise ValueError(f"zip integrity failure in {asset.name}: {bad}")
    _run(
        [sys.executable, str(REPO_ROOT / "scripts" / "epubcheck.py"), "--require", "--strict", str(asset)],
        cwd=str(REPO_ROOT),
    )
    _run([sys.executable, str(REPO_ROOT / "dev" / "verify_kr2_build.py"), str(asset)], cwd=str(REPO_ROOT))


def _kepubify_exe() -> str:
    """Pinned kepubify v4.0.4 on PATH (dev/TOOLCHAIN.md §kepubify)."""
    exe = shutil.which("kepubify")
    if not exe:
        raise FileNotFoundError("kepubify not on PATH — install pinned v4.0.4 (dev/TOOLCHAIN.md §kepubify)")
    return exe


def _apply_kepubify(source_epub: Path, dest_kepub: Path) -> None:
    """Plain EPUB → Kobo ``.kepub.epub`` via kepubify (footnote popups require it)."""
    if dest_kepub.exists():
        dest_kepub.unlink()
    _run([_kepubify_exe(), "-o", str(dest_kepub), str(source_epub)])


def _apply_kindle_post(edition_id: str, cell: dict, asset: Path) -> None:
    """Apply the proven Send-to-Kindle recipe (``scripts.core.kindle_post``) in
    place over a freshly built / cover-swapped EPUB, then assert conformance.
    Runs LAST (after the cover swap) so the hidden-content strip + the OCF
    mimetype-first/stored re-zip are the final word on the artifact bytes —
    byte-faithful to the artifact the user confirmed delivers via Send-to-Kindle."""
    from scripts.core.kindle_post import make_kindle_safe, verify_kindle_safe

    pre = asset.with_name(asset.stem + "._pre_kindle.epub")
    asset.replace(pre)
    stats = make_kindle_safe(pre, asset)
    pre.unlink()
    print(f"[{edition_id}] cell {cell['id']}: kindle-safe post-process {stats}", flush=True)
    fails = verify_kindle_safe(asset)
    if fails:
        raise ValueError(f"{asset.name}: kindle-safe recipe not satisfied: {fails}")


def build_edition_assets(
    edition_id: str,
    version: str,
    out_dir: Path,
    *,
    phase: str = "M1",
    gates: bool = True,
) -> list[Path]:
    """Build every phase-eligible catalog asset for one edition; returns the
    final asset paths. Per cell: the SIGNATURE asset is the base build copied
    under the signature colour's name (the edition's own cover is already
    embedded), and each M2 variant colour is the same base with the edition's
    own-design composite in that colour swapped in (spec Addendum A)."""
    from scripts.build_edition import edition_cover_signature
    from scripts.swap_epub_cover import swap_cover

    cells = matrix_cells(phase=phase)
    if not cells:
        raise ValueError(f"no formats gate at phase {phase!r}")
    out_dir.mkdir(parents=True, exist_ok=True)

    bases: dict[str, Path] = {}
    for target in distinct_base_targets(cells):
        print(f"[{edition_id}] base build: target={target}", flush=True)
        bases[target] = _build_base(edition_id, version, target, out_dir / f"_base_{target}")

    _design, sig_colour = edition_cover_signature(edition_id)
    assets: list[Path] = []
    for cell in cells:
        base = bases[base_build_target(cell)]
        kepub_base: Path | None = None
        for colour, name in cell_asset_names(edition_id, version, cell):
            asset = out_dir / name
            if cell.get("post_process") == "kepubify":
                # Spec §4: kepubify the eink base once; variant colours re-swap
                # the committed composite onto the kepub (not the plain EPUB).
                if kepub_base is None:
                    kepub_base = out_dir / f"._kepub_base_{edition_id}_{cell['id']}.kepub.epub"
                    print(f"[{edition_id}] cell {cell['id']}: kepubify {base.name}", flush=True)
                    _apply_kepubify(base, kepub_base)
                if colour == sig_colour:
                    print(
                        f"[{edition_id}] cell {cell['id']}: {kepub_base.name} -> {asset.name} (signature)", flush=True
                    )
                    shutil.copyfile(kepub_base, asset)
                else:
                    composite = variant_composite_path(edition_id, colour)
                    print(
                        f"[{edition_id}] cell {cell['id']}: swap {composite.name} -> {asset.name} (kepub)", flush=True
                    )
                    swap_cover(kepub_base, composite, asset)
            elif colour == sig_colour:
                print(f"[{edition_id}] cell {cell['id']}: {base.name} -> {asset.name} (signature)", flush=True)
                shutil.copyfile(base, asset)
            else:
                composite = variant_composite_path(edition_id, colour)
                print(f"[{edition_id}] cell {cell['id']}: swap {composite.name} -> {asset.name}", flush=True)
                swap_cover(base, composite, asset)
            # Kindle (K-KIN turn-84): apply the proven Send-to-Kindle recipe LAST
            # — after the cover swap — so the strip + OCF re-zip are the final
            # word on the bytes. No-op for every other cell.
            if cell.get("post_process") == "kindle_safe":
                _apply_kindle_post(edition_id, cell, asset)
            if gates:
                _gate_asset(asset)
            assets.append(asset)
        if kepub_base is not None and kepub_base.is_file():
            kepub_base.unlink()

    # The base trees are working artifacts, not uploads — drop them so the
    # job's upload glob can never sweep a non-catalog name.
    for target in bases:
        shutil.rmtree(out_dir / f"_base_{target}", ignore_errors=True)
    return assets


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build one edition's format-matrix catalog assets.")
    p.add_argument("--edition", help="edition id (one job per edition)")
    p.add_argument("--version", help="release version (bare or v-prefixed)")
    p.add_argument("--output-dir", type=Path, default=REPO_ROOT / "build" / "matrix")
    p.add_argument("--phase", default="M1", help="ship formats gated at this phase (default M1)")
    p.add_argument("--no-gates", action="store_true", help="skip epubcheck/verify gates (local probes only)")
    p.add_argument("--list-editions", action="store_true", help="print the catalog edition ids as JSON and exit")
    args = p.parse_args(argv)

    if args.list_editions:
        print(json.dumps(standard_edition_ids()))
        return 0
    if not args.edition or not args.version:
        p.error("--edition and --version are required (or use --list-editions)")

    version = args.version.removeprefix("v")
    assets = build_edition_assets(args.edition, version, args.output_dir, phase=args.phase, gates=not args.no_gates)
    sums = write_sums(assets, args.output_dir / f"sums-{args.edition}.txt")
    print(f"[{args.edition}] {len(assets)} asset(s) + {sums.name}:")
    for a in assets:
        print(f"  {a.name}  ({a.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
