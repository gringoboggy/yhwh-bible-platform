"""Compose per-book title-page cover JPGs from reimagined full-bleed scene art.

Workflow (see content/covers/_book_defaults/COVER_MANIFEST.yaml):
  1. Midjourney refs live in ``_scenes/_midjourney/<code>.jpg`` (inspiration only).
  2. Reimagined Grok scenes land in ``_scenes/<variant>/<code>.jpg``.
  3. ``python scripts/generate_book_title_covers.py regen-queue`` lists regen work.
  4. ``python scripts/generate_book_title_covers.py compose [--variant alt02]``.
  5. Output: ``covers/_book_defaults/<variant>/<code>.jpg`` (1024×1536).

Plates are full background scenes — no leather, no gold border. A/B/C share the
same compose grade and edge fade; variants differ by reimagine composition prompt.

Audit: ``python scripts/generate_book_title_covers.py audit``
Prompts: ``python scripts/generate_book_title_covers.py prompts [--variant alt02]``
Regen:  ``python scripts/generate_book_title_covers.py regen-queue [--variant alt02]``
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
DEFAULTS_DIR = REPO_ROOT / "content" / "covers" / "_book_defaults"
SCENES_ROOT = DEFAULTS_DIR / "_scenes"
MIDJOURNEY_DIR = SCENES_ROOT / "_midjourney"
MANIFEST_PATH = DEFAULTS_DIR / "COVER_MANIFEST.yaml"

WORK_WIDTH = 1792
WORK_HEIGHT = 2688
FINAL_WIDTH = 1024
FINAL_HEIGHT = 1536

# Shared look for default / alt02 / alt03 — only crop centering varies.
_PLATE_COMPOSE = {"sharpen": 1.14, "vignette": 0.12}
_VARIANT_CENTERING: dict[str, tuple[float, float]] = {
    "default": (0.5, 0.5),
    "alt02": (0.5, 0.44),
    "alt03": (0.5, 0.56),
}


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


def _compose_opts(manifest: dict) -> dict:
    style = manifest.get("style") or {}
    compose = style.get("compose") or {}
    sharpen = float(compose.get("sharpen", _PLATE_COMPOSE["sharpen"]))
    vignette = float(compose.get("vignette", _PLATE_COMPOSE["vignette"]))
    style_grade = compose.get("style_grade", True)
    if isinstance(style_grade, str):
        style_grade = style_grade.lower() not in {"false", "0", "no"}
    return {"sharpen": sharpen, "vignette": vignette, "style_grade": bool(style_grade)}


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


def _reference_dir(manifest: dict) -> Path:
    style = manifest.get("style") or {}
    reimagine = style.get("reimagine") or {}
    sub = (reimagine.get("reference_dir") or "_midjourney").strip()
    return SCENES_ROOT / sub


def reference_scene_path(manifest: dict, code: str) -> Path | None:
    """Midjourney reference for reimagine prompts — never used in compose."""
    return _find_scene_file(_reference_dir(manifest), code)


def reimagine_out_path(manifest: dict, variant: str, code: str) -> Path:
    return _scene_dir(manifest, variant) / f"{code}.jpg"


def build_reimagine_prompt(manifest: dict, code: str, rec: dict, variant: str = "default") -> str:
    """Image-edit prompt: redraw from scratch using reference for scenery ideas only."""
    base = build_prompt(manifest, code, rec, variant)
    ref = reference_scene_path(manifest, code)
    if ref is None:
        return base
    return (
        f"{base} The attached reference suggests the book's scenery and symbolic "
        "subject only — do not copy its style, borders, or composition. Redraw as a "
        "new refined plate in the unified family described above."
    )


def _scene_stems_in_dir(scene_dir: Path) -> set[str]:
    if not scene_dir.is_dir():
        return set()
    out: set[str] = set()
    for ext in ("png", "jpg", "jpeg"):
        out |= {p.stem for p in scene_dir.glob(f"*.{ext}")}
    return out


def _find_scene_file(directory: Path, code: str) -> Path | None:
    if not directory.is_dir():
        return None
    for ext in ("jpg", "jpeg", "png"):
        candidate = directory / f"{code}.{ext}"
        if candidate.is_file():
            return candidate
    return None


def _resolve_scene_path(manifest: dict, variant: str, code: str) -> tuple[Path | None, str]:
    """Prefer reimagined Grok scenes; Midjourney refs are never shipped."""
    grok = _find_scene_file(_scene_dir(manifest, variant), code)
    if grok is not None:
        return grok, "reimagined"
    if variant != "default":
        grok = _find_scene_file(_scene_dir(manifest, "default"), code)
        if grok is not None:
            return grok, "reimagined-fallback"
    return None, "missing"


def cmd_audit(args: argparse.Namespace) -> int:
    from scripts.core.matrix import _load_canons

    manifest = _load_manifest()
    books = manifest.get("books") or {}
    eth = _load_canons()["ethiopian"]["books"]
    variant = getattr(args, "variant", None) or "default"

    out_dir = _out_dir(manifest, variant)
    existing = {p.stem for p in out_dir.glob("*.jpg")} if out_dir.is_dir() else set()
    scenes = _scene_stems_in_dir(_scene_dir(manifest, variant))
    mj = _scene_stems_in_dir(MIDJOURNEY_DIR)

    print(f"Variant: {variant}")
    print(f"Manifest books: {len(books)}")
    print(f"Ethiopian canon: {len(eth)}")
    print(f"Midjourney scenes: {len(mj)}")
    print(f"Grok scenes ({variant}): {len(scenes)}")
    print(f"JPGs in {out_dir.relative_to(REPO_ROOT)}: {len(existing)}")
    missing_jpg = [c for c in eth if c not in existing]
    print(f"Canon missing JPG: {len(missing_jpg)}")
    if missing_jpg:
        print("  " + ", ".join(missing_jpg))
    return 0


def cmd_prompts(args: argparse.Namespace) -> int:
    manifest = _load_manifest()
    variant = getattr(args, "variant", None) or "default"
    use_reimagine = getattr(args, "reimagine", False)
    for code, rec in _books_to_process(manifest, args.only, args.status):
        print(f"## {code} ({variant})")
        if use_reimagine:
            print(build_reimagine_prompt(manifest, code, rec, variant))
        else:
            print(build_prompt(manifest, code, rec, variant))
        print()
    return 0


def cmd_regen_queue(args: argparse.Namespace) -> int:
    manifest = _load_manifest()
    variant = getattr(args, "variant", None) or "default"
    pending = 0
    for code, rec in _books_to_process(manifest, args.only, args.status):
        out_path = reimagine_out_path(manifest, variant, code)
        if getattr(args, "skip_existing", False) and out_path.is_file():
            continue
        ref = reference_scene_path(manifest, code)
        pending += 1
        print(f"## {code}\t{variant}")
        print(f"out: {out_path.relative_to(REPO_ROOT)}")
        print(f"ref: {ref.relative_to(REPO_ROOT) if ref else '(none — motif only)'}")
        print(build_reimagine_prompt(manifest, code, rec, variant))
        print()
    print(f"Pending regen ({variant}): {pending}")
    return 0


def _fit_scene(
    scene_path: Path,
    *,
    size: tuple[int, int] = (WORK_WIDTH, WORK_HEIGHT),
    centering: tuple[float, float] = (0.5, 0.5),
) -> Image.Image:
    scene = Image.open(scene_path).convert("RGB")
    return ImageOps.fit(
        scene,
        size,
        method=Image.Resampling.LANCZOS,
        centering=centering,
    )


def _edge_mean_color(img: Image.Image, band: int = 20) -> tuple[int, int, int]:
    w, h = img.size
    pixels: list[tuple[int, int, int]] = []
    step_x = max(1, w // 36)
    step_y = max(1, h // 36)
    for x in range(0, w, step_x):
        for y in range(band):
            pixels.append(img.getpixel((x, y)))
            pixels.append(img.getpixel((x, h - 1 - y)))
    for y in range(0, h, step_y):
        for x in range(band):
            pixels.append(img.getpixel((x, y)))
            pixels.append(img.getpixel((w - 1 - x, y)))
    if not pixels:
        return (48, 16, 22)
    return tuple(sum(channel) // len(pixels) for channel in zip(*pixels, strict=True))


def _apply_grok_style_grade(img: Image.Image) -> Image.Image:
    """Crimson painterly grade — atmosphere only, no leather frame compositing."""
    graded = ImageEnhance.Color(img).enhance(1.12)
    graded = ImageEnhance.Contrast(graded).enhance(1.05)
    tint = Image.new("RGB", img.size, (92, 20, 30))
    warmed = ImageChops.soft_light(graded, tint)
    return Image.blend(graded, warmed, 0.20)


def _apply_scene_fade_vignette(img: Image.Image, strength: float = 0.12) -> Image.Image:
    """Soft edge fade that blends into the scene's own border colors."""
    w, h = img.size
    edge_color = _edge_mean_color(img)
    fade_target = Image.new("RGB", (w, h), edge_color)

    margin_x = int(w * 0.05)
    margin_y = int(h * 0.05)
    mask = Image.new("L", (w, h), 0)
    inner = Image.new("L", (w - 2 * margin_x, h - 2 * margin_y), 255)
    mask.paste(inner, (margin_x, margin_y))
    mask = mask.filter(ImageFilter.GaussianBlur(radius=int(min(w, h) * 0.085)))

    faded = Image.composite(img, fade_target, mask)
    return Image.blend(img, faded, strength)


def compose_scene(
    scene_path: Path,
    out_path: Path,
    *,
    sharpen: float = 1.14,
    centering: tuple[float, float] = (0.5, 0.5),
    vignette: float = 0.12,
    style_grade: bool = True,
) -> None:
    scene = _fit_scene(scene_path, centering=centering)
    if style_grade:
        scene = _apply_grok_style_grade(scene)
    if sharpen != 1.0:
        scene = ImageEnhance.Sharpness(scene).enhance(sharpen)
    scene = _apply_scene_fade_vignette(scene, strength=vignette)

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


def cmd_bootstrap_alts(args: argparse.Namespace) -> int:
    """Compose alt02/alt03 from resolved scene sources (MJ-first)."""
    manifest = _load_manifest()
    opts = _compose_opts(manifest)
    composed = 0
    for variant in ("alt02", "alt03"):
        if args.only_variant and variant != args.only_variant:
            continue
        out_dir = _out_dir(manifest, variant)
        centering = _VARIANT_CENTERING[variant]
        for code, _rec in _books_to_process(manifest, args.only, None):
            scene_path, _src = _resolve_scene_path(manifest, variant, code)
            if scene_path is None:
                continue
            out_path = out_dir / f"{code}.jpg"
            compose_scene(scene_path, out_path, centering=centering, **opts)
            composed += 1
            print(f"bootstrap {variant} {code}")
    print(f"Done: {composed} bootstrap composes")
    return 0 if composed else 1


def cmd_compose(args: argparse.Namespace) -> int:
    manifest = _load_manifest()
    variant = getattr(args, "variant", None) or "default"
    opts = _compose_opts(manifest)
    centering = _VARIANT_CENTERING.get(variant, (0.5, 0.5))

    out_dir = _out_dir(manifest, variant)
    composed = 0
    skipped = 0
    reimagined = 0
    for code, _rec in _books_to_process(manifest, args.only, args.status):
        scene_path, source = _resolve_scene_path(manifest, variant, code)
        out_path = out_dir / f"{code}.jpg"
        if scene_path is None:
            print(f"skip {code}: no reimagined scene — run regen-queue")
            skipped += 1
            continue
        reimagined += 1
        sharpen = args.sharpen if args.sharpen != 1.15 else opts["sharpen"]
        compose_scene(
            scene_path,
            out_path,
            sharpen=sharpen,
            centering=centering,
            vignette=opts["vignette"],
            style_grade=opts["style_grade"],
        )
        print(f"composed {code} ({source}) -> {out_path.relative_to(REPO_ROOT)}")
        composed += 1

    print(f"Done: {composed} composed ({reimagined} reimagined scenes), {skipped} skipped")
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
    p_prompts.add_argument("--reimagine", action="store_true", help="Include reference-redraw instructions")
    add_variant(p_prompts)
    p_prompts.set_defaults(func=cmd_prompts)

    p_regen = sub.add_parser("regen-queue", help="List pending reimagine jobs with prompts")
    p_regen.add_argument("--only", help="Single book code")
    p_regen.add_argument("--status", help="Filter by manifest status")
    p_regen.add_argument(
        "--skip-existing",
        action="store_true",
        help="Omit books that already have a scene file at the out path",
    )
    add_variant(p_regen)
    p_regen.set_defaults(func=cmd_regen_queue)

    p_ingest = sub.add_parser("ingest", help="Copy numbered session JPGs into _scenes/")
    p_ingest.add_argument("--from-dir", required=True, help="Session images directory")
    p_ingest.add_argument("--codes", required=True, help="Comma-separated book codes")
    p_ingest.add_argument("--numbers", required=True, help="Comma-separated source image numbers")
    add_variant(p_ingest)
    p_ingest.set_defaults(func=cmd_ingest)

    p_boot = sub.add_parser("bootstrap-alts", help="Build alt02/alt03 JPGs from scene sources")
    p_boot.add_argument("--only", help="Single book code")
    p_boot.add_argument("--only-variant", choices=("alt02", "alt03"), help="Single alt variant")
    p_boot.set_defaults(func=cmd_bootstrap_alts)

    p_compose = sub.add_parser("compose", help="Composite scene art to final JPGs")
    p_compose.add_argument("--only", help="Single book code")
    p_compose.add_argument("--status", help="Filter by manifest status")
    p_compose.add_argument("--sharpen", type=float, default=1.15, help="Sharpness factor (1.0 = none)")
    add_variant(p_compose)
    p_compose.set_defaults(func=cmd_compose)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
