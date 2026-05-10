#!/usr/bin/env python3
"""
customize.py — Apply visual customization (covers + book title pages).

Reads ``content/customization.yaml`` and applies cover + per-book
title-page overrides to ``epub_working/`` so subsequent edition builds
pick them up. Per-edition overrides are NOT written to the master HTML;
they're staged as variants that ``build_edition.py`` swaps in during
the per-edition build.

Architecture:
  - Master cover    : `epub_working/cover.jpeg`
                      `epub_working/titlepage.xhtml`
  - Edition covers  : `epub_working/cover-{edition}.jpeg`
                      (build_edition.py picks these up)
  - Book title pages: replaced inline inside index_split_NNN.html
                      <div class="book-title-page" id="bp-XX"> wrapper
  - Per-edition title pages: kept as side-files in
                      `epub_working/title_pages/{book}--{edition}.html.frag`
                      and swapped in during edition build

Per Rule S6 (dry-run by default), Rule P6 (consult existing tools first):
  - This tool complements `build_edition.py` — it does NOT duplicate it.
  - All mutations go through `atomic_write` + `ensure_backup`.
  - Defaults to dry-run; `--apply` writes.
  - `--revert` restores from `.backups/`.

Usage:
    python3 scripts/customize.py                      # status
    python3 scripts/customize.py --validate           # check refs
    python3 scripts/customize.py --apply              # write changes
    python3 scripts/customize.py --book gen --image FILE
    python3 scripts/customize.py --book gen --html FILE
    python3 scripts/customize.py --edition jewish-study --cover FILE
    python3 scripts/customize.py --revert
    python3 scripts/customize.py --measure            # count pages for spine calc
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402
from scripts.core.notes_io import atomic_write, ensure_backup  # noqa: E402
from scripts.core.ui import GREEN, RED, YELLOW, DIM, BOLD, RESET  # noqa: E402

CONTENT_DIR = REPO_ROOT / "content"
EPUB_DIR = REPO_ROOT / "epub_working"
CUSTOM_YAML = CONTENT_DIR / "customization.yaml"

# epub_working/title_pages/ stages per-edition fragments that build_edition.py
# picks up at edition-build time.
TITLE_PAGES_STAGE = EPUB_DIR / "title_pages"


# ----------------------------------------------------------------------
# Config loading + validation
# ----------------------------------------------------------------------


def load_customization() -> dict:
    if not CUSTOM_YAML.is_file():
        return {}
    with CUSTOM_YAML.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def validate_assets(cfg: dict) -> list[str]:
    """Return a list of error messages. Empty list = valid."""
    errors: list[str] = []
    eds = {e["id"] for e in config.load_editions()}
    book_codes = {b["code"] for b in config.load_books()}

    # cover
    cover = cfg.get("cover") or {}
    for label, entry in [
        ("global_default", cover.get("global_default") or {}),
        *[(f"edition_overrides[{k}]", v) for k, v in (cover.get("edition_overrides") or {}).items()],
    ]:
        if entry is None:
            continue
        for key in ("image", "html_file"):
            ref = entry.get(key)
            if ref:
                p = CONTENT_DIR / ref
                if not p.is_file():
                    errors.append(f"cover.{label}.{key} → file not found: {ref}")
        if label.startswith("edition_overrides"):
            ed_id = label.split("[", 1)[1].rstrip("]")
            if ed_id not in eds:
                errors.append(f"cover.edition_overrides[{ed_id}] → unknown edition id")

    # book title pages
    btp = cfg.get("book_title_pages", {}) or {}
    for code, spec in (btp.get("book_defaults") or {}).items():
        if code not in book_codes:
            errors.append(f"book_title_pages.book_defaults[{code}] → unknown book code")
        if spec and spec.get("html_file"):
            p = CONTENT_DIR / spec["html_file"]
            if not p.is_file():
                errors.append(f"book_title_pages.book_defaults[{code}].html_file → not found: {spec['html_file']}")
    for ed_id, books in (btp.get("edition_overrides") or {}).items():
        if ed_id not in eds:
            errors.append(f"book_title_pages.edition_overrides[{ed_id}] → unknown edition id")
        for code, spec in (books or {}).items():
            if code not in book_codes:
                errors.append(f"book_title_pages.edition_overrides[{ed_id}][{code}] → unknown book code")
            if spec and spec.get("html_file"):
                p = CONTENT_DIR / spec["html_file"]
                if not p.is_file():
                    errors.append(
                        f"book_title_pages.edition_overrides[{ed_id}][{code}].html_file → not found: {spec['html_file']}"
                    )

    return errors


# ----------------------------------------------------------------------
# Cover application
# ----------------------------------------------------------------------


def apply_master_cover(spec: dict, dry_run: bool) -> str:
    """Apply the global-default cover spec to epub_working/cover.jpeg
    and titlepage.xhtml. Returns a one-line status string."""
    img_ref = spec.get("image")
    html_ref = spec.get("html_file")
    alt = spec.get("alt", "Cover")

    actions: list[str] = []

    if html_ref:
        # Full HTML override: replace titlepage.xhtml entirely
        src = CONTENT_DIR / html_ref
        dst = EPUB_DIR / "titlepage.xhtml"
        if not dry_run:
            ensure_backup(dst)
            shutil.copyfile(src, dst)
        actions.append(f"titlepage.xhtml ← {html_ref}")
    elif img_ref:
        src = CONTENT_DIR / img_ref
        dst_img = EPUB_DIR / "cover.jpeg"
        if not dry_run:
            ensure_backup(dst_img)
            shutil.copyfile(src, dst_img)
        actions.append(f"cover.jpeg ← {img_ref}")
        # Update alt text in titlepage.xhtml
        tp = EPUB_DIR / "titlepage.xhtml"
        if tp.is_file():
            text = tp.read_text(encoding="utf-8")
            new = re.sub(r'alt="[^"]*"', f'alt="{alt}"', text, count=1)
            if new != text and not dry_run:
                ensure_backup(tp)
                atomic_write(tp, new)
            if new != text:
                actions.append("titlepage.xhtml alt= updated")

    return " · ".join(actions) if actions else "(no master cover spec)"


def apply_edition_cover(edition_id: str, spec: dict, dry_run: bool) -> str:
    """Stage a per-edition cover variant in epub_working/. build_edition.py
    swaps cover-{edition}.jpeg in for cover.jpeg during the per-edition build."""
    img_ref = spec.get("image")
    html_ref = spec.get("html_file")
    alt = spec.get("alt", "Cover")

    actions: list[str] = []

    if img_ref:
        src = CONTENT_DIR / img_ref
        dst = EPUB_DIR / f"cover-{edition_id}.jpeg"
        if not dry_run:
            shutil.copyfile(src, dst)
        actions.append(f"cover-{edition_id}.jpeg ← {img_ref}")

    if html_ref:
        src = CONTENT_DIR / html_ref
        dst = EPUB_DIR / f"titlepage-{edition_id}.xhtml"
        if not dry_run:
            shutil.copyfile(src, dst)
        actions.append(f"titlepage-{edition_id}.xhtml ← {html_ref}")

    # Stage the alt text in a sidecar file so build_edition.py can read it
    if alt and (img_ref or html_ref):
        meta = EPUB_DIR / f"cover-{edition_id}.alt.txt"
        if not dry_run:
            atomic_write(meta, alt)
        actions.append(f"alt= staged")

    return " · ".join(actions)


# ----------------------------------------------------------------------
# Per-book title page application
# ----------------------------------------------------------------------


# Each book has a <div class="book-title-page" id="bp-NN" data-book-idx="N" epub:type="bodymatter">
# block at the start of its first index_split file. We replace the *inner*
# content while preserving the wrapper.

BOOK_DIV_RE = re.compile(
    r'(<div class="book-title-page"[^>]*id="bp-(\d+)"[^>]*>)(.*?)(</div>\s*(?=<|\Z))',
    re.DOTALL,
)


def find_book_div_target(book_code: str) -> tuple[Path, int] | None:
    """Locate which index_split_NNN.html file contains the book-title-page
    div for ``book_code``, plus its bp-N index. Returns (path, bp_idx) or None."""
    try:
        book = config.get_book(book_code)
    except (KeyError, Exception):
        return None
    files = book.get("files", [])
    if not files:
        return None
    # Use the first file (where the title-page lives)
    first_file = EPUB_DIR / files[0]
    if not first_file.is_file():
        return None
    text = first_file.read_text(encoding="utf-8")
    # Books are bp-00, bp-01, ... in canonical order. Match by data-book-idx.
    bxx = book.get("bxx", "")
    # bxx is e.g. b00, b01... but bp-N uses N starting at 00 sequentially.
    # Search for the div whose data-book-idx matches the book's index.
    # Simpler: take the first <div class="book-title-page"> that appears
    # in this file IF this is the book's primary file.
    m = BOOK_DIV_RE.search(text)
    if m:
        return (first_file, int(m.group(2)))
    return None


def apply_master_book_title(book_code: str, spec: dict, dry_run: bool) -> str:
    """Replace the inner content of the book-title-page div in master HTML."""
    if not spec or spec.get("layout") is None and not spec.get("html_file"):
        return ""
    target = find_book_div_target(book_code)
    if target is None:
        return f"{RED}✗ {book_code}: no title-page div found{RESET}"
    fpath, bp_idx = target

    html_ref = spec.get("html_file")
    if not html_ref:
        return ""
    src = CONTENT_DIR / html_ref
    if not src.is_file():
        return f"{RED}✗ {book_code}: html_file not found: {html_ref}{RESET}"

    new_inner = src.read_text(encoding="utf-8").strip()
    text = fpath.read_text(encoding="utf-8")

    def repl(m: re.Match) -> str:
        if int(m.group(2)) != bp_idx:
            return m.group(0)  # not this book's div
        return f"{m.group(1)}\n  {new_inner}\n{m.group(4)}"

    new_text = BOOK_DIV_RE.sub(repl, text, count=1)
    if new_text == text:
        return f"{YELLOW}⚠ {book_code}: no change{RESET}"
    if not dry_run:
        ensure_backup(fpath)
        atomic_write(fpath, new_text)
    return f"{book_code}: title-page ← {html_ref}"


def apply_edition_book_title(edition_id: str, book_code: str, spec: dict, dry_run: bool) -> str:
    """Stage a per-edition book-title-page fragment. build_edition.py picks
    these up from epub_working/title_pages/ during edition build."""
    html_ref = spec.get("html_file")
    if not html_ref:
        return ""
    src = CONTENT_DIR / html_ref
    if not src.is_file():
        return f"{RED}✗ {edition_id}/{book_code}: html_file not found: {html_ref}{RESET}"

    if not dry_run:
        TITLE_PAGES_STAGE.mkdir(exist_ok=True)
    dst = TITLE_PAGES_STAGE / f"{book_code}--{edition_id}.html.frag"
    if not dry_run:
        atomic_write(dst, src.read_text(encoding="utf-8").strip())
    return f"{edition_id}/{book_code}: staged ← {html_ref}"


# ----------------------------------------------------------------------
# CLI helpers
# ----------------------------------------------------------------------


def cmd_status(cfg: dict) -> None:
    print(f"\n{BOLD}customize{RESET}  {DIM}status{RESET}\n")

    cover = cfg.get("cover", {}) or {}
    print(f"  {BOLD}Cover{RESET}")
    gd = cover.get("global_default") or {}
    if gd.get("image") or gd.get("html_file"):
        print(f"    global_default: {gd.get('html_file') or gd.get('image')}")
    else:
        print(f"    global_default: {DIM}(unset — using packaged cover.jpeg){RESET}")
    eo = cover.get("edition_overrides") or {}
    if eo:
        for ed_id, spec in eo.items():
            ref = (spec or {}).get("html_file") or (spec or {}).get("image") or "(empty)"
            print(f"    {ed_id}: {ref}")
    else:
        print(f"    edition_overrides: {DIM}(none){RESET}")
    print()

    btp = cfg.get("book_title_pages", {}) or {}
    print(f"  {BOLD}Book title pages{RESET}")
    bd = btp.get("book_defaults") or {}
    if bd:
        for code, spec in bd.items():
            ref = (spec or {}).get("html_file") or "(empty)"
            print(f"    {code}: {ref}")
    else:
        print(f"    book_defaults: {DIM}(none — keeping current rendering){RESET}")
    eov = btp.get("edition_overrides") or {}
    if eov:
        for ed_id, books in eov.items():
            for code, spec in (books or {}).items():
                ref = (spec or {}).get("html_file") or "(empty)"
                print(f"    {ed_id}/{code}: {ref}")
    else:
        print(f"    edition_overrides: {DIM}(none){RESET}")
    print()

    pc = cfg.get("print_covers", {}) or {}
    variants = pc.get("variants") or []
    enabled = [v for v in variants if v.get("enabled")]
    print(f"  {BOLD}Print covers (POD){RESET}")
    if enabled:
        for v in enabled:
            print(f'    {v["profile"]}: {v["trim_width_in"]}"×{v["trim_height_in"]}" bleed={v["bleed_in"]}"')
    else:
        print(f"    {DIM}(none enabled — flip enabled: true in customization.yaml to opt in){RESET}")
    print()


def cmd_validate(cfg: dict) -> int:
    errors = validate_assets(cfg)
    if not errors:
        print(f"{GREEN}✓ customization.yaml valid (all referenced files exist){RESET}")
        return 0
    print(f"{RED}✗ {len(errors)} validation error(s):{RESET}")
    for e in errors:
        print(f"  {RED}✗{RESET} {e}")
    return 1


def cmd_apply(cfg: dict, dry_run: bool) -> int:
    errors = validate_assets(cfg)
    if errors:
        print(f"{RED}✗ refusing to apply — fix validation errors first:{RESET}")
        for e in errors:
            print(f"  {RED}✗{RESET} {e}")
        return 1

    label = "would apply" if dry_run else "applied"
    print(f"\n{BOLD}customize{RESET}  {DIM}{label}{RESET}\n")

    cover = cfg.get("cover", {}) or {}
    gd = cover.get("global_default") or {}
    if gd.get("image") or gd.get("html_file"):
        msg = apply_master_cover(gd, dry_run)
        print(f"  cover (master): {msg}")

    for ed_id, spec in (cover.get("edition_overrides") or {}).items():
        if not spec:
            continue
        msg = apply_edition_cover(ed_id, spec, dry_run)
        print(f"  cover ({ed_id}): {msg}")

    btp = cfg.get("book_title_pages", {}) or {}
    for code, spec in (btp.get("book_defaults") or {}).items():
        msg = apply_master_book_title(code, spec, dry_run)
        if msg:
            print(f"  title page: {msg}")
    for ed_id, books in (btp.get("edition_overrides") or {}).items():
        for code, spec in (books or {}).items():
            msg = apply_edition_book_title(ed_id, code, spec, dry_run)
            if msg:
                print(f"  title page: {msg}")

    if dry_run:
        print(f"\n  {DIM}re-run with --apply to write changes{RESET}\n")
    else:
        print(f"\n  {GREEN}✓ customization applied to epub_working/{RESET}")
        print(f"  {DIM}rebuild editions: ./ebible build{RESET}\n")
    return 0


def cmd_revert() -> int:
    """Restore epub_working/cover.jpeg + titlepage.xhtml from latest .backups/."""
    backup_dir = EPUB_DIR / ".backups"
    if not backup_dir.is_dir():
        print(f"{YELLOW}⚠ no backups found in {backup_dir}{RESET}")
        return 1
    targets = ["cover.jpeg", "titlepage.xhtml"]
    restored = 0
    for name in targets:
        candidates = sorted(backup_dir.glob(f"{name}.*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            shutil.copyfile(candidates[0], EPUB_DIR / name)
            print(f"  {GREEN}✓{RESET} {name} ← {candidates[0].name}")
            restored += 1
    print()
    print(
        f"  {GREEN}✓ {restored} file(s) restored{RESET}"
        if restored
        else f"  {YELLOW}⚠ no matching backups found{RESET}"
    )
    return 0


def cmd_measure() -> int:
    """Count rendered pages per edition for print-cover spine calculation.
    HTML doesn't have hard page breaks; we estimate via word count."""
    WORDS_PER_PAGE = 350  # paperback typical for 6×9 trim
    total_words = 0
    for f in sorted(EPUB_DIR.glob("index_split_*.html")):
        text = f.read_text(encoding="utf-8")
        # Strip tags
        from scripts.core.html_utils import strip_tags

        total_words += len(strip_tags(text).split())
    pages = total_words // WORDS_PER_PAGE
    # Round up to even (printers want even page counts)
    if pages % 2:
        pages += 1
    print(f"\n  {BOLD}page-count estimate{RESET}")
    print(f"    total words : {total_words:,}")
    print(f"    @ {WORDS_PER_PAGE} wpp : {pages:,} pages (rounded to even)")
    print(f"\n  {DIM}Update customization.yaml print_covers[N].page_count: {pages}{RESET}")
    print(f"  {DIM}Then: ./ebible print [profile]{RESET}\n")
    return 0


def cmd_quick_set(args, cfg: dict) -> int:
    """One-line CLI updates without editing YAML by hand."""
    # Defensive normalisation: if a top-level key exists in YAML with no
    # body, yaml.safe_load returns None. Convert any such None values to
    # empty dicts before mutating.
    cover = cfg.get("cover") or {}
    cover_eo = cover.get("edition_overrides") or {}
    btp = cfg.get("book_title_pages") or {}
    btp_defaults = btp.get("book_defaults") or {}
    btp_overrides = btp.get("edition_overrides") or {}

    if args.book and args.image:
        # No direct image slot for book title pages — encourage HTML
        print(f"{YELLOW}⚠ for book title pages, use --html (full HTML control).")
        print(f"  Build a small HTML file referencing the image, then point --html at it.{RESET}")
        return 1

    if args.book and args.html:
        if args.edition:
            ed_block = btp_overrides.get(args.edition) or {}
            ed_block[args.book] = {"html_file": args.html}
            btp_overrides[args.edition] = ed_block
        else:
            btp_defaults[args.book] = {"html_file": args.html}
        btp["book_defaults"] = btp_defaults
        btp["edition_overrides"] = btp_overrides
        cfg["book_title_pages"] = btp
        _write_yaml(cfg)
        location = f"{args.edition}/{args.book}" if args.edition else args.book
        print(f"{GREEN}✓ updated customization.yaml ({location} → {args.html}){RESET}")
        return 0

    if args.edition and args.cover:
        cover_eo[args.edition] = {"image": args.cover, "alt": f"{args.edition} cover"}
        cover["edition_overrides"] = cover_eo
        cfg["cover"] = cover
        _write_yaml(cfg)
        print(f"{GREEN}✓ updated customization.yaml (cover for {args.edition} → {args.cover}){RESET}")
        return 0

    return 0


def _write_yaml(cfg: dict) -> None:
    out = yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True, default_flow_style=False)
    ensure_backup(CUSTOM_YAML)
    atomic_write(CUSTOM_YAML, out)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Apply visual customization (covers + book title pages).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--validate", action="store_true", help="check all referenced files exist")
    p.add_argument("--apply", action="store_true", help="write changes (default is dry-run)")
    p.add_argument("--revert", action="store_true", help="restore cover.jpeg + titlepage.xhtml from backups")
    p.add_argument("--measure", action="store_true", help="estimate page count for print-cover spine calc")
    p.add_argument("--book", help="quick-set: book code (use with --html)")
    p.add_argument("--edition", help="quick-set: edition id (use with --cover or --html)")
    p.add_argument("--image", help="quick-set: image path")
    p.add_argument("--html", help="quick-set: HTML file path")
    p.add_argument("--cover", help="quick-set: cover image path (with --edition)")
    p.add_argument("--dry-run", action="store_true", help="show what would happen but don't write (alias for default)")
    args = p.parse_args()

    cfg = load_customization()

    if args.revert:
        sys.exit(cmd_revert())

    if args.measure:
        sys.exit(cmd_measure())

    # Quick-set short-circuit
    if (args.book and args.html) or (args.edition and args.cover) or (args.book and args.image):
        sys.exit(cmd_quick_set(args, cfg))

    if args.validate:
        sys.exit(cmd_validate(cfg))

    if args.apply:
        sys.exit(cmd_apply(cfg, dry_run=False))

    # Default behaviour: status + dry-run preview
    cmd_status(cfg)
    if (
        cfg.get("cover", {}).get("global_default")
        or cfg.get("cover", {}).get("edition_overrides")
        or (cfg.get("book_title_pages", {}) or {}).get("book_defaults")
        or (cfg.get("book_title_pages", {}) or {}).get("edition_overrides")
    ):
        cmd_apply(cfg, dry_run=True)


if __name__ == "__main__":
    main()
