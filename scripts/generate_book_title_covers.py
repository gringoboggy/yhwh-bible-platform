"""Compose per-book title-page cover JPGs from scene PNGs + border overlay.

Workflow (see content/covers/_book_defaults/COVER_MANIFEST.yaml):
  1. Place raw scene art in ``_scenes/<variant>/<code>.jpg`` (variant dirs:
     ``""`` = default, ``alt02``, ``alt03``).
  2. Run ``python scripts/generate_book_title_covers.py compose [--variant alt02]``.
  3. Output: ``covers/_book_defaults/<variant>/<code>.jpg`` (1024×1536).

Audit: ``python scripts/generate_book_title_covers.py audit``
Prompts: ``python scripts/generate_book_title_covers.py prompts [--variant alt02]``
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
DEFAULTS_DIR = REPO_ROOT / "content" / "covers" / "_book_defaults"
SCENES_ROOT = DEFAULTS_DIR / "_scenes"
MANIFEST_PATH = DEFAULTS_DIR / "COVER_MANIFEST.yaml"
BORDERS_DIR = REPO_ROOT / "content" / "assets" / "borders"

WORK_WIDTH = 1792
WORK_HEIGHT = 2688
FINAL_WIDTH = 1024
FINAL_HEIGHT = 1536


def _load_manifest() -> dict:
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8")) or {}
    return data


def _variant_spec(manifest: dict, variant: str) -> dict:
    style = manifest.get("style") or {}
    variants = style.get("variants") or {}
    if variant not in variants:
        raise ValueError(f"unknown variant {variant!r}; valid: {sorted(variants)}")
    return variants[variant]


def _scene_dir(manifest: dict, variant: str) -> Path:
    spec = _variant_spec(manifest, variant)
    sub = (spec.get("scene_dir") or "").strip()
    return SCENES_ROOT / sub if sub else SCENES_ROOT


def _out_dir(manifest: dict, variant: str) -> Path:
    spec = _variant_spec(manifest, variant)
    sub = (spec.get("out_dir") or "").strip()
    return DEFAULTS_DIR / sub if sub else DEFAULTS_DIR


def _books_to_process(manifest: dict, only: str | None, status: str | None) -> list[tuple[str, dict]]:
    books = manifest.get("books") or {}
    rows: list[tuple[str, dict]] = []
    for code in sorted(books):
        if only and code != only:
            continue
        rec = books[code]
        if status and rec.get("status") != status:
            continue
        if rec.get("status") == "skip":
            continue
        rows.append((code, rec))
    return rows


def build_prompt(manifest: dict, code: str, rec: dict, variant: str = "default") -> str:
    style = manifest.get("style") or {}
    prefix = (style.get("prompt_prefix") or "").strip()
    suffix = (style.get("prompt_suffix") or "").strip()
    motif = (rec.get("motif") or "").strip()
    extra = (_variant_spec(manifest, variant).get("prompt_extra") or "").strip()
    parts = [prefix, motif + ".", extra, suffix]
    return " ".join(p for p in parts if p)


def _scene_stems_in_dir(scene_dir: Path) -> set[str]:
    if not scene_dir.is_dir():
        return set()
    out: set[str] = set()
    for ext in ("png", "jpg", "jpeg"):
        out |= {p.stem for p in scene_dir.glob(f"*.{ext}")}
    return out


def cmd_audit(args: argparse.Namespace) -> int:
    from scripts.core.matrix import _load_canons

    manifest = _load_manifest()
    books = manifest.get("books") or {}
    eth = _load_canons()["ethiopian"]["books"]
    variant = getattr(args, "variant", None) or "default"

    out_dir = _out_dir(manifest, variant)
    existing = {p.stem for p in out_dir.glob("*.jpg")} if out_dir.is_dir() else set()
    scenes = _scene_stems_in_dir(_scene_dir(manifest, variant))

    print(f"Variant: {variant}")
    print(f"Manifest books: {len(books)}")
    print(f"Ethiopian canon: {len(eth)}")
    print(f"JPGs in {out_dir.relative_to(REPO_ROOT)}: {len(existing)}")
    print(f"Scenes: {len(scenes)}")
    missing_jpg = [c for c in eth if c not in existing]
    print(f"Canon missing JPG: {len(missing_jpg)}")
    if missing_jpg:
        print("  " + ", ".join(missing_jpg))
    return 0


def cmd_prompts(args: argparse.Namespace) -> int:
    manifest = _load_manifest()
    variant = getattr(args, "variant", None) or "default"
    for code, rec in _books_to_process(manifest, args.only, args.status):
        print(f"## {code} ({variant})")
        print(build_prompt(manifest, code, rec, variant))
        print()
    return 0


def _apply_vignette(img: Image.Image, strength: float = 0.35) -> Image.Image:
    w, h = img.size
    inner = Image.new("L", (w, h), 255)
    border = int(min(w, h) * 0.08)
    fade = Image.new("L", (w - 2 * border, h - 2 * border), 0)
    inner.paste(fade, (border, border))
    mask = ImageOps.fit(inner, (w, h), centering=(0.5, 0.5))
    mask = mask.filter(ImageFilter.GaussianBlur(radius=int(min(w, h) * 0.06)))
    dark = Image.new("RGB", (w, h), (20, 4, 8))
    return Image.composite(img, dark, mask.point(lambda p: int(255 - (255 - p) * strength)))


def compose_scene(
    scene_path: Path,
    border_path: Path,
    out_path: Path,
    *,
    sharpen: float = 1.15,
    centering: tuple[float, float] = (0.5, 0.5),
    vignette: float = 0.35,
) -> None:
    scene = Image.open(scene_path).convert("RGB")
    scene = ImageOps.fit(
        scene,
        (WORK_WIDTH, WORK_HEIGHT),
        method=Image.Resampling.LANCZOS,
        centering=centering,
    )

    if sharpen != 1.0:
        scene = ImageEnhance.Sharpness(scene).enhance(sharpen)
    scene = _apply_vignette(scene, strength=vignette)

    if border_path.is_file():
        border = Image.open(border_path).convert("RGBA")
        border = ImageOps.fit(border, (WORK_WIDTH, WORK_HEIGHT), method=Image.Resampling.LANCZOS)
        scene_rgba = scene.convert("RGBA")
        scene_rgba.alpha_composite(border)
        scene = scene_rgba.convert("RGB")

    final = scene.resize((FINAL_WIDTH, FINAL_HEIGHT), Image.Resampling.LANCZOS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    final.save(out_path, format="JPEG", quality=92, optimize=True)


def cmd_ingest(args: argparse.Namespace) -> int:
    codes = [c.strip() for c in args.codes.split(",") if c.strip()]
    src_dir = Path(args.from_dir)
    if not src_dir.is_dir():
        print(f"Source dir missing: {src_dir}", file=sys.stderr)
        return 1
    nums = [int(x) for x in args.numbers.split(",")]
    if len(nums) != len(codes):
        print("codes and numbers must be same length", file=sys.stderr)
        return 1
    manifest = _load_manifest()
    variant = getattr(args, "variant", None) or "default"
    scene_dir = _scene_dir(manifest, variant)
    scene_dir.mkdir(parents=True, exist_ok=True)
    for code, num in zip(codes, nums, strict=True):
        src = src_dir / f"{num}.jpg"
        dst = scene_dir / f"{code}.jpg"
        if not src.is_file():
            print(f"missing {src}", file=sys.stderr)
            return 1
        dst.write_bytes(src.read_bytes())
        print(f"ingested {code} <- {src.name} -> {dst.relative_to(REPO_ROOT)}")
    return 0


_VARIANT_COMPOSE: dict[str, dict] = {
    "default": {"sharpen": 1.15, "centering": (0.5, 0.5), "vignette": 0.35},
    "alt02": {"sharpen": 1.28, "centering": (0.5, 0.38), "vignette": 0.30},
    "alt03": {"sharpen": 1.05, "centering": (0.5, 0.62), "vignette": 0.42},
}


def cmd_bootstrap_alts(args: argparse.Namespace) -> int:
    """Compose alt02/alt03 from default scenes (bootstrap until unique art lands)."""
    manifest = _load_manifest()
    style = manifest.get("style") or {}
    border_path = BORDERS_DIR / f"{style.get('border') or 'border_05_corner_accent'}.png"
    scene_dir = _scene_dir(manifest, "default")
    composed = 0
    for variant in ("alt02", "alt03"):
        if args.only_variant and variant != args.only_variant:
            continue
        out_dir = _out_dir(manifest, variant)
        opts = _VARIANT_COMPOSE[variant]
        for code, _rec in _books_to_process(manifest, args.only, None):
            scene_path = next(
                (
                    scene_dir / f"{code}.{ext}"
                    for ext in ("png", "jpg", "jpeg")
                    if (scene_dir / f"{code}.{ext}").is_file()
                ),
                None,
            )
            if scene_path is None:
                continue
            out_path = out_dir / f"{code}.jpg"
            compose_scene(scene_path, border_path, out_path, **opts)
            composed += 1
            print(f"bootstrap {variant} {code}")
    print(f"Done: {composed} bootstrap composes")
    return 0 if composed else 1


def cmd_compose(args: argparse.Namespace) -> int:
    manifest = _load_manifest()
    variant = getattr(args, "variant", None) or "default"
    style = manifest.get("style") or {}
    border_name = style.get("border") or "border_05_corner_accent"
    border_path = BORDERS_DIR / f"{border_name}.png"
    if not border_path.is_file():
        print(f"Border not found: {border_path}", file=sys.stderr)
        return 1

    scene_dir = _scene_dir(manifest, variant)
    out_dir = _out_dir(manifest, variant)
    scene_dir.mkdir(parents=True, exist_ok=True)
    composed = 0
    skipped = 0
    for code, _rec in _books_to_process(manifest, args.only, args.status):
        scene_path = next(
            (scene_dir / f"{code}.{ext}" for ext in ("png", "jpg", "jpeg") if (scene_dir / f"{code}.{ext}").is_file()),
            None,
        )
        out_path = out_dir / f"{code}.jpg"
        if scene_path is None:
            print(f"skip {code}: no scene in {scene_dir.name or 'root'}")
            skipped += 1
            continue
        opts = _VARIANT_COMPOSE.get(variant, {})
        compose_scene(
            scene_path,
            border_path,
            out_path,
            sharpen=args.sharpen if args.sharpen != 1.15 else opts.get("sharpen", args.sharpen),
            centering=opts.get("centering", (0.5, 0.5)),
            vignette=opts.get("vignette", 0.35),
        )
        print(f"composed {code} -> {out_path.relative_to(REPO_ROOT)}")
        composed += 1

    print(f"Done: {composed} composed, {skipped} skipped")
    return 0 if composed or skipped else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_variant(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--variant",
            default="default",
            choices=("default", "alt02", "alt03"),
            help="Catalog variant (default | alt02 | alt03)",
        )

    p_audit = sub.add_parser("audit", help="List canon vs JPG vs scene coverage")
    add_variant(p_audit)
    p_audit.set_defaults(func=cmd_audit)

    p_prompts = sub.add_parser("prompts", help="Print image-generation prompts from manifest")
    p_prompts.add_argument("--only", help="Single book code")
    p_prompts.add_argument("--status", help="Filter by manifest status")
    add_variant(p_prompts)
    p_prompts.set_defaults(func=cmd_prompts)

    p_ingest = sub.add_parser("ingest", help="Copy numbered session JPGs into _scenes/")
    p_ingest.add_argument("--from-dir", required=True, help="Session images directory")
    p_ingest.add_argument("--codes", required=True, help="Comma-separated book codes")
    p_ingest.add_argument("--numbers", required=True, help="Comma-separated source image numbers")
    add_variant(p_ingest)
    p_ingest.set_defaults(func=cmd_ingest)

    p_boot = sub.add_parser("bootstrap-alts", help="Build alt02/alt03 JPGs from default scenes")
    p_boot.add_argument("--only", help="Single book code")
    p_boot.add_argument("--only-variant", choices=("alt02", "alt03"), help="Single alt variant")
    p_boot.set_defaults(func=cmd_bootstrap_alts)

    p_compose = sub.add_parser("compose", help="Composite scene PNGs to final JPGs")
    p_compose.add_argument("--only", help="Single book code")
    p_compose.add_argument("--status", help="Filter by manifest status")
    p_compose.add_argument("--sharpen", type=float, default=1.15, help="Sharpness factor (1.0 = none)")
    add_variant(p_compose)
    p_compose.set_defaults(func=cmd_compose)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
