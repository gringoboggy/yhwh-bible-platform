"""Compose per-book title-page cover JPGs from reimagined full-bleed scene art.

Workflow (see content/covers/_book_defaults/COVER_MANIFEST.yaml):
  1. Midjourney refs live in ``_scenes/_midjourney/<code>.jpg`` (inspiration only).
  2. Reimagined Grok scenes land in ``_scenes/<variant>/<code>.jpg``.
  3. ``python scripts/generate_book_title_covers.py regen-queue`` lists regen work.
  4. ``python scripts/generate_book_title_covers.py compose [--variant alt02]``.
  5. Output: ``covers/_book_defaults/<variant>/<code>.jpg`` (1024×1536).

v5 scene families (alt04/alt05/alt06) use ``v5_scenes.yaml`` for distinct iconic
scenes per book — see ``prompts --variant alt04`` and ``compose --variant alt04``.

Audit: ``python scripts/generate_book_title_covers.py audit``
Optimize: ``python scripts/generate_book_title_covers.py optimize`` (recompress JPGs)
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
from scripts.core.covers import save_book_cover_jpeg  # noqa: E402

DEFAULTS_DIR = REPO_ROOT / "content" / "covers" / "_book_defaults"
SCENES_ROOT = DEFAULTS_DIR / "_scenes"
MIDJOURNEY_DIR = SCENES_ROOT / "_midjourney"
MANIFEST_PATH = DEFAULTS_DIR / "COVER_MANIFEST.yaml"
V5_SCENES_PATH = DEFAULTS_DIR / "v5_scenes.yaml"

WORK_WIDTH = 1792
WORK_HEIGHT = 2688
FINAL_WIDTH = 1024
FINAL_HEIGHT = 1536

V4_SOURCE_VARIANTS = ("default", "alt02", "alt03")
V5_VARIANTS = ("alt04", "alt05", "alt06")
CATALOG_VARIANTS = ("default",) + V5_VARIANTS
ALL_VARIANTS = CATALOG_VARIANTS
SELECTION_PATH = DEFAULTS_DIR / "COVER_VARIANT_SELECTION.yaml"

# Shared look for default / alt02 / alt03 — only crop centering varies.
_PLATE_COMPOSE = {"sharpen": 1.14, "vignette": 0.12}
_VARIANT_CENTERING: dict[str, tuple[float, float]] = {
    "default": (0.5, 0.5),
    "alt02": (0.5, 0.44),
    "alt03": (0.5, 0.56),
    "alt04": (0.5, 0.5),
    "alt05": (0.5, 0.38),
    "alt06": (0.5, 0.5),
}
_V5_COMPOSE: dict[str, dict] = {
    # Same painterly plate treatment as v4 — only the color grade differs.
    "alt04": {"sharpen": 1.14, "vignette": 0.12, "grade": "forest"},
    "alt05": {"sharpen": 1.14, "vignette": 0.12, "grade": "navy"},
    "alt06": {"sharpen": 1.14, "vignette": 0.12, "grade": "amber"},
}


def _load_manifest() -> dict:
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8")) or {}
    return data


def _load_v5_scenes() -> dict:
    if not V5_SCENES_PATH.is_file():
        return {}
    return yaml.safe_load(V5_SCENES_PATH.read_text(encoding="utf-8")) or {}


def is_v5_variant(variant: str) -> bool:
    return variant in V5_VARIANTS


def _variant_spec(manifest: dict, variant: str) -> dict:
    if is_v5_variant(variant):
        v5 = _load_v5_scenes()
        families = v5.get("families") or {}
        if variant not in families:
            raise ValueError(f"unknown v5 variant {variant!r}")
        fam = families[variant]
        return {
            "scene_dir": variant,
            "out_dir": variant,
            "prompt_extra": "",
            "prompt_prefix": fam.get("prompt_prefix", ""),
            "prompt_suffix": fam.get("prompt_suffix", ""),
        }
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


def _compose_opts(manifest: dict, variant: str = "default") -> dict:
    if is_v5_variant(variant):
        row = _V5_COMPOSE[variant]
        return {
            "sharpen": row["sharpen"],
            "vignette": row["vignette"],
            "style_grade": row["grade"],
        }
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


def _v5_books_to_process(v5: dict, only: str | None) -> list[str]:
    books = v5.get("books") or {}
    codes = sorted(books)
    if only:
        return [only] if only in books else []
    return codes


def build_v5_prompt(v5: dict, code: str, variant: str) -> str:
    families = v5.get("families") or {}
    fam = families.get(variant) or {}
    books = v5.get("books") or {}
    scene = (books.get(code) or {}).get(variant) or ""
    prefix = (fam.get("prompt_prefix") or "").strip()
    rules = (v5.get("content_rules") or "").strip()
    suffix = (fam.get("prompt_suffix") or "").strip()
    parts = [prefix, scene + ".", rules, suffix]
    return " ".join(p for p in parts if p)


def build_prompt(manifest: dict, code: str, rec: dict, variant: str = "default") -> str:
    if is_v5_variant(variant):
        return build_v5_prompt(_load_v5_scenes(), code, variant)
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


def _scene_source(manifest: dict) -> str:
    style = manifest.get("style") or {}
    compose = style.get("compose") or {}
    return str(compose.get("scene_source") or "midjourney_first").strip().lower()


def _resolve_scene_path(manifest: dict, variant: str, code: str) -> tuple[Path | None, str]:
    """Resolve compose input: midjourney_first (Windows default) or grok_first (v4 regen)."""
    source_mode = _scene_source(manifest)
    mj = _find_scene_file(MIDJOURNEY_DIR, code)
    grok = _find_scene_file(_scene_dir(manifest, variant), code)
    if variant != "default" and grok is None:
        grok = _find_scene_file(_scene_dir(manifest, "default"), code)
    if source_mode == "grok_first":
        if grok is not None:
            return grok, "reimagined"
        if variant != "default" and mj is not None:
            return mj, "midjourney-fallback"
        return None, "missing"
    if mj is not None:
        return mj, "midjourney"
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
    if is_v5_variant(variant):
        v5 = _load_v5_scenes()
        for code in _v5_books_to_process(v5, args.only):
            print(f"## {code} ({variant})")
            print(build_v5_prompt(v5, code, variant))
            print()
        return 0
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
    if is_v5_variant(variant):
        v5 = _load_v5_scenes()
        for code in _v5_books_to_process(v5, args.only):
            out_path = _scene_dir(manifest, variant) / f"{code}.jpg"
            if getattr(args, "skip_existing", False) and out_path.is_file():
                continue
            pending += 1
            print(f"## {code}\t{variant}")
            print(f"out: {out_path.relative_to(REPO_ROOT)}")
            print(build_v5_prompt(v5, code, variant))
            print()
        print(f"Pending regen ({variant}): {pending}")
        return 0
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


def _apply_forest_grade(img: Image.Image) -> Image.Image:
    """Option B — deep forest-green atmosphere (v4 family, different hue)."""
    graded = ImageEnhance.Color(img).enhance(1.06)
    graded = ImageEnhance.Contrast(graded).enhance(1.05)
    tint = Image.new("RGB", img.size, (32, 58, 42))
    toned = ImageChops.soft_light(graded, tint)
    return Image.blend(graded, toned, 0.22)


def _apply_navy_grade(img: Image.Image) -> Image.Image:
    """Option C — deep navy twilight atmosphere (v4 family, different hue)."""
    graded = ImageEnhance.Color(img).enhance(0.98)
    graded = ImageEnhance.Contrast(graded).enhance(1.06)
    tint = Image.new("RGB", img.size, (22, 38, 72))
    toned = ImageChops.soft_light(graded, tint)
    return Image.blend(graded, toned, 0.22)


def _apply_amber_grade(img: Image.Image) -> Image.Image:
    """Option D — warm amber dusk atmosphere (v4 family, not crimson-A)."""
    graded = ImageEnhance.Color(img).enhance(1.10)
    graded = ImageEnhance.Contrast(graded).enhance(1.05)
    tint = Image.new("RGB", img.size, (88, 52, 28))
    toned = ImageChops.soft_light(graded, tint)
    return Image.blend(graded, toned, 0.20)


def _apply_style_grade(img: Image.Image, mode: bool | str) -> Image.Image:
    if mode is False:
        return img
    if mode == "forest":
        return _apply_forest_grade(img)
    if mode == "navy":
        return _apply_navy_grade(img)
    if mode == "amber":
        return _apply_amber_grade(img)
    return _apply_grok_style_grade(img)


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
    style_grade: bool | str = True,
) -> None:
    scene = _fit_scene(scene_path, centering=centering)
    scene = _apply_style_grade(scene, style_grade)
    if sharpen != 1.0:
        scene = ImageEnhance.Sharpness(scene).enhance(sharpen)
    scene = _apply_scene_fade_vignette(scene, strength=vignette)

    final = scene.resize((FINAL_WIDTH, FINAL_HEIGHT), Image.Resampling.LANCZOS)
    save_book_cover_jpeg(final, out_path)


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
    composed = 0
    for variant in ("alt02", "alt03"):
        if args.only_variant and variant != args.only_variant:
            continue
        opts = _compose_opts(manifest, variant)
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
    opts = _compose_opts(manifest, variant)
    centering = _VARIANT_CENTERING.get(variant, (0.5, 0.5))

    out_dir = _out_dir(manifest, variant)
    composed = 0
    skipped = 0
    reimagined = 0
    if is_v5_variant(variant):
        v5 = _load_v5_scenes()
        codes = _v5_books_to_process(v5, args.only)
    else:
        codes = [c for c, _ in _books_to_process(manifest, args.only, args.status)]
    for code in codes:
        scene_path, source = _resolve_scene_path(manifest, variant, code)
        out_path = out_dir / f"{code}.jpg"
        if scene_path is None:
            print(f"skip {code}: no scene — add _midjourney/{code}.jpg or run regen-queue")
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


def _load_selection() -> dict[str, str]:
    if not SELECTION_PATH.is_file():
        return {}
    data = yaml.safe_load(SELECTION_PATH.read_text(encoding="utf-8")) or {}
    return dict((data.get("books") or {}))


def _v4_source_path(code: str, source: str) -> Path:
    if source == "default":
        return DEFAULTS_DIR / f"{code}.jpg"
    return DEFAULTS_DIR / source / f"{code}.jpg"


def cmd_consolidate(args: argparse.Namespace) -> int:
    """Copy best-of v4 pick into unified option A (default/)."""
    import shutil

    force = bool(getattr(args, "force", False))
    selection = _load_selection()
    if not selection:
        print(f"Missing selection file: {SELECTION_PATH}", file=sys.stderr)
        return 1
    changed = 0
    skipped = 0
    for code, source in sorted(selection.items()):
        if source not in V4_SOURCE_VARIANTS:
            print(f"skip {code}: bad source {source!r}", file=sys.stderr)
            skipped += 1
            continue
        src = _v4_source_path(code, source)
        dst = DEFAULTS_DIR / f"{code}.jpg"
        if not src.is_file():
            print(f"skip {code}: missing {src.relative_to(REPO_ROOT)}", file=sys.stderr)
            skipped += 1
            continue
        if source == "default" and dst.is_file() and not force:
            skipped += 1
            continue
        if src.resolve() == dst.resolve():
            skipped += 1
            continue
        shutil.copy2(src, dst)
        print(f"consolidated {code} <- {source}")
        changed += 1
    print(f"Done: {changed} copied, {skipped} unchanged/missing")
    return 0 if changed or skipped else 1


def cmd_restore_v4_a(args: argparse.Namespace) -> int:
    """Restore option-A JPGs from pre-consolidation v4 default commit."""
    import subprocess

    commit = (getattr(args, "commit", None) or "e4dd1a5").strip()
    rel = "content/covers/_book_defaults"
    manifest = _load_manifest()
    codes = sorted((manifest.get("books") or {}).keys())
    paths = [
        f"{rel}/{code}.jpg" for code in codes if (manifest.get("books") or {}).get(code, {}).get("status") != "skip"
    ]
    proc = subprocess.run(
        ["git", "checkout", commit, "--", *paths],
        cwd=REPO_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout, file=sys.stderr)
        return proc.returncode
    print(f"restored {len(paths)} option-A plates from {commit}")
    return 0


def _iter_cover_jpgs(variant: str | None) -> list[Path]:
    paths: list[Path] = []
    if variant:
        if variant == "default":
            paths.extend(sorted(DEFAULTS_DIR.glob("*.jpg")))
        else:
            out = DEFAULTS_DIR / variant
            paths.extend(sorted(out.glob("*.jpg")))
        return paths
    paths.extend(sorted(DEFAULTS_DIR.glob("*.jpg")))
    for sub in V5_VARIANTS:
        d = DEFAULTS_DIR / sub
        if d.is_dir():
            paths.extend(sorted(d.glob("*.jpg")))
    return paths


def cmd_optimize(args: argparse.Namespace) -> int:
    """Re-save existing title plates at lean EPUB-safe JPEG settings."""
    paths = _iter_cover_jpgs(getattr(args, "variant", None))
    if not paths:
        print("No JPGs found to optimize")
        return 1
    before = 0
    after = 0
    done = 0
    for path in paths:
        before += path.stat().st_size
        with Image.open(path) as img:
            save_book_cover_jpeg(img, path)
        after += path.stat().st_size
        done += 1
        if args.verbose:
            print(f"optimized {path.relative_to(REPO_ROOT)}")
    saved = before - after
    pct = (100.0 * saved / before) if before else 0.0
    print(f"Optimized {done} JPGs: {before // 1024} KB -> {after // 1024} KB (saved {saved // 1024} KB, {pct:.1f}%)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_variant(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--variant",
            default="default",
            choices=ALL_VARIANTS,
            help="Catalog variant (default | alt02..alt06)",
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

    p_opt = sub.add_parser("optimize", help="Recompress title plates to lean JPEG settings")
    p_opt.add_argument("--variant", choices=ALL_VARIANTS, help="Single variant dir only")
    p_opt.add_argument("-v", "--verbose", action="store_true")
    p_opt.set_defaults(func=cmd_optimize)

    p_cons = sub.add_parser("consolidate", help="Apply best-of v4 selection into option A")
    p_cons.add_argument("--force", action="store_true", help="Overwrite even when source is default")
    p_cons.set_defaults(func=cmd_consolidate)

    p_restore = sub.add_parser("restore-v4-a", help="Restore option A from pre-consolidation v4 commit")
    p_restore.add_argument("--commit", default="e4dd1a5", help="Git commit with v4 default plates")
    p_restore.set_defaults(func=cmd_restore_v4_a)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
