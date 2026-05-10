#!/usr/bin/env python3
"""
fix_vnote_xrefs.py — Repair broken cross-file ``#vnote-`` references.

The EPUB uses ``id="vnote-CODE-CH-V"`` for verse popover footnotes (rich
asides containing the verse text + Hebrew/Greek originals + variants).
A typical ref is ``href="#vnote-gen-1-1"``, a same-file link to that
verse's popover.

Hand-typed cross-canon references in commentary notes (e.g. a Genesis
note linking to ``Deuteronomy 32:11``) used the same same-file form
``href="#vnote-deu-32-11"`` — but the popover for Deut 32:11 lives in
the Deuteronomy chapter file, not the Genesis file. Result: the link is
broken (no such id in the current file).

This script repairs those broken cross-file refs by adding the proper
file prefix:

    Source file F has ``href="#vnote-X"``
    └─ if ``vnote-X`` exists in F        → leave alone (already valid)
    └─ if ``vnote-X`` exists in file G   → rewrite to ``href="G#vnote-X"``
    └─ if ``vnote-X`` exists nowhere     → report, leave alone

It updates BOTH:

  * ``content/notes/*.py``    — source of truth, so re-injection produces
                                correct hrefs going forward.
  * ``epub_working/*.html``   — current rendered EPUB.

For source notes, since the eventual aside placement isn't known at write
time, every match that resolves anywhere is rewritten with an explicit
file prefix (defensive: works regardless of destination).

Examples:
    python3 scripts/fix_vnote_xrefs.py
        # dry-run; show what would change

    python3 scripts/fix_vnote_xrefs.py --apply
        # write changes to both source and rendered

    python3 scripts/fix_vnote_xrefs.py --apply --rendered-only
    python3 scripts/fix_vnote_xrefs.py --apply --source-only

Exit codes:
    0  no unresolved refs (or no work needed)
    1  some refs unresolved (target popover doesn't exist anywhere)
    2  setup error
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EPUB_DIR = REPO_ROOT / "epub_working"
NOTES_DIR = REPO_ROOT / "content" / "notes"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

VNOTE_HREF_RE = re.compile(r'href="#vnote-([a-z0-9]+-\d+-\d+[a-z]?)"')
VNOTE_ID_RE = re.compile(r'id="(vnote-[a-z0-9]+-\d+-\d+[a-z]?)"')


def build_vnote_index(epub_dir: Path) -> tuple[dict[str, str], dict[str, set[str]]]:
    """Returns (vnote_index, file_ids).
    vnote_index: {vnote-CODE-CH-V: first filename containing that id}
    file_ids:    {filename: set of vnote ids in that file}
    """
    vnote_index: dict[str, str] = {}
    file_ids: dict[str, set[str]] = {}
    for f in sorted(epub_dir.glob("*.html")):
        text = f.read_text(encoding="utf-8")
        ids = {m.group(1) for m in VNOTE_ID_RE.finditer(text)}
        file_ids[f.name] = ids
        for vid in ids:
            vnote_index.setdefault(vid, f.name)
    return vnote_index, file_ids


def build_chapter_index(epub_dir: Path, books_meta) -> dict[str, str]:
    """Build a `vnote-CODE-CH-V` → `file.html#ch-bxx-cCH` fallback map for
    Strategy-B books. When a vnote target doesn't exist (because the book
    uses Strategy-B chapter-scoped anchors instead of per-verse), this
    map provides the closest navigable target — the chapter heading.
    """
    fallback: dict[str, str] = {}
    for book in books_meta:
        if book.get("strategy") != "B":
            continue
        bxx = book.get("bxx")
        code = book.get("code")
        files = book.get("files", [])
        ch_count = book.get("ch_count", 0)
        if not (bxx and code and files):
            continue
        # Find which file contains each chapter
        for fname in files:
            fpath = epub_dir / fname
            if not fpath.is_file():
                continue
            ftext = fpath.read_text(encoding="utf-8")
            for ch in range(1, ch_count + 1):
                ch_id = f"ch-{bxx}-c{ch}"
                if f'id="{ch_id}"' in ftext:
                    # Map every potential vnote-CODE-CH-V (any V) to this chapter anchor
                    # We don't know the verse count cheaply; just remember chapter target.
                    # A cheap upper bound on V: 200 (no chapter has more verses).
                    for v in range(1, 200):
                        fallback[f"vnote-{code}-{ch}-{v}"] = f"{fname}#{ch_id}"
    return fallback


def rewrite_rendered(
    text: str, this_file_ids: set[str], vnote_index: dict[str, str], chapter_fallback: dict[str, str] | None = None
):
    """Surgical: only rewrite refs whose target id is NOT in the current file.
    For Strategy-B targets that lack per-verse vnote anchors, fall back to
    the chapter heading anchor."""
    n_resolved = 0
    n_already_ok = 0
    n_fallback = 0
    unresolved: list[str] = []

    def repl(m: re.Match) -> str:
        nonlocal n_resolved, n_already_ok, n_fallback
        target = m.group(1)
        vid = f"vnote-{target}"
        if vid in this_file_ids:
            n_already_ok += 1
            return m.group(0)
        if vid in vnote_index:
            n_resolved += 1
            return f'href="{vnote_index[vid]}#{vid}"'
        # Fallback: Strategy-B chapter anchor
        if chapter_fallback and vid in chapter_fallback:
            n_fallback += 1
            return f'href="{chapter_fallback[vid]}"'
        unresolved.append(target)
        return m.group(0)

    new_text = VNOTE_HREF_RE.sub(repl, text)
    return new_text, n_resolved, n_already_ok, unresolved, n_fallback


def rewrite_source(text: str, vnote_index: dict[str, str], chapter_fallback: dict[str, str] | None = None):
    """For source notes: always rewrite resolvable refs to cross-file form,
    with Strategy-B chapter fallback for late-canon targets."""
    n_resolved = 0
    n_fallback = 0
    unresolved: list[str] = []

    def repl(m: re.Match) -> str:
        nonlocal n_resolved, n_fallback
        target = m.group(1)
        vid = f"vnote-{target}"
        if vid in vnote_index:
            n_resolved += 1
            return f'href="{vnote_index[vid]}#{vid}"'
        if chapter_fallback and vid in chapter_fallback:
            n_fallback += 1
            return f'href="{chapter_fallback[vid]}"'
        unresolved.append(target)
        return m.group(0)

    new_text = VNOTE_HREF_RE.sub(repl, text)
    return new_text, n_resolved, unresolved, n_fallback


def main() -> None:
    p = argparse.ArgumentParser(
        description="Repair broken cross-file #vnote- references.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--apply", action="store_true", help="write changes (default is dry-run)")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--source-only", action="store_true", help="only fix content/notes/*.py")
    g.add_argument("--rendered-only", action="store_true", help="only fix epub_working/*.html")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    if not EPUB_DIR.is_dir():
        print(f"{RED}ERROR: not a directory: {EPUB_DIR}{RESET}", file=sys.stderr)
        sys.exit(2)

    if not args.quiet:
        print("indexing vnote ids in epub_working/ …")
    vnote_index, file_ids = build_vnote_index(EPUB_DIR)
    if not args.quiet:
        print(f"  {len(vnote_index):,} unique vnote ids across {len(file_ids)} files")

    # Build Strategy-B chapter-fallback index
    if not args.quiet:
        print("indexing Strategy-B chapter anchors as fallback targets …")
    sys.path.insert(0, str(EPUB_DIR.parent))
    from scripts.core import config as _config

    chapter_fallback = build_chapter_index(EPUB_DIR, _config.load_books())
    if not args.quiet:
        print(f"  {len(chapter_fallback):,} potential Strategy-B chapter targets")

    total_resolved = 0
    total_already_ok = 0
    total_fallback = 0
    files_changed = 0
    all_unresolved: set[str] = set()

    # --- Rendered HTML: surgical
    if not args.source_only:
        for f in sorted(EPUB_DIR.glob("*.html")):
            text = f.read_text(encoding="utf-8")
            if "#vnote-" not in text:
                continue
            new_text, n_res, n_ok, un, n_fb = rewrite_rendered(
                text, file_ids.get(f.name, set()), vnote_index, chapter_fallback
            )
            all_unresolved.update(un)
            total_resolved += n_res
            total_already_ok += n_ok
            total_fallback += n_fb
            if new_text != text:
                files_changed += 1
                verb = "rewrote" if args.apply else "would rewrite"
                if not args.quiet:
                    un_note = f" · {len(un)} unresolved" if un else ""
                    fb_note = f" · {n_fb} chapter-fallback" if n_fb else ""
                    ok_note = f" · {n_ok} already-ok same-file"
                    print(f"  rendered {f.name}: {verb} {n_res} ref(s){ok_note}{fb_note}{un_note}")
                if args.apply:
                    f.write_text(new_text, encoding="utf-8")

    # --- Source notes: always rewrite resolvable
    if not args.rendered_only:
        for f in sorted(NOTES_DIR.glob("*.py")):
            if f.name == "__init__.py":
                continue
            text = f.read_text(encoding="utf-8")
            if "#vnote-" not in text:
                continue
            new_text, n_res, un, n_fb = rewrite_source(text, vnote_index, chapter_fallback)
            all_unresolved.update(un)
            total_resolved += n_res
            total_fallback += n_fb
            if new_text != text:
                files_changed += 1
                verb = "rewrote" if args.apply else "would rewrite"
                if not args.quiet:
                    un_note = f" · {len(un)} unresolved" if un else ""
                    print(f"  source   {f.name}: {verb} {n_res} ref(s){un_note}")
                if args.apply:
                    f.write_text(new_text, encoding="utf-8")

    # Summary
    n_unresolved = len(all_unresolved)
    if n_unresolved == 0:
        color, sym = GREEN, "✓"
    else:
        color, sym = YELLOW, "⚠"

    action = "applied" if args.apply else "dry-run"
    print(
        f"\n{color}{sym} fix_vnote_xrefs ({action}): "
        f"resolved={total_resolved}  already-ok={total_already_ok}  "
        f"unresolved={n_unresolved}  files-changed={files_changed}{RESET}"
    )

    if all_unresolved:
        sample = sorted(all_unresolved)[:10]
        more = "" if len(all_unresolved) <= 10 else f" … (+{len(all_unresolved) - 10} more)"
        print(f"  unresolved (target popover absent): {', '.join(sample)}{more}")

    if not args.apply and files_changed > 0:
        print("\n  re-run with --apply to write changes")

    sys.exit(1 if n_unresolved else 0)


if __name__ == "__main__":
    main()
