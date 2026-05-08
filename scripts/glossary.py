#!/usr/bin/env python3
"""
glossary.py — Build a Hebrew/Greek glossary from ``word``-kind notes.

Walks every ``word``-kind tuple in ``content/notes/*.py``, extracts the
opener of the form ``<strong>TRANSLIT (<em>ORIGINAL</em>) — 'gloss'.</strong>``,
and groups by language (Hebrew / Greek / Other). Each entry records the
verse(s) where the word-note appears.

Examples:
    python3 scripts/glossary.py
        # terminal summary

    python3 scripts/glossary.py --html glossary.html
        # write a self-contained HTML page

    python3 scripts/glossary.py --book gen
        # only consider word-notes in one book

    python3 scripts/glossary.py --lang Hebrew
        # one language only

    python3 scripts/glossary.py --search "tselem"
        # find a transliteration substring across the corpus

Exit codes:
    0  ok
    2  setup error
"""

import argparse
import html
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402
from scripts.core.notes_io import load_notes_from_text

NOTES_DIR = REPO_ROOT / "content" / "notes"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ----------------------------------------------------------------------
# Note loading + extraction
# ----------------------------------------------------------------------



# Match the standard word-kind opener:
#   <strong>TRANSLIT (<em>ORIGINAL</em>)? — 'gloss' . </strong>
# The <em>ORIGINAL</em> portion is optional in some notes (e.g. opener using
# only the transliterated form), so we try both shapes.
OPENER_WITH_ORIG = re.compile(
    r"<strong>([^<()]+?)\s*\(<em>([^<]+)</em>\)\s*(.*?)</strong>",
    re.DOTALL,
)
OPENER_NO_ORIG = re.compile(
    r"<strong>([^<()]+?)</strong>",
    re.DOTALL,
)
GLOSS_RE = re.compile(r"[—–-]\s*['\u2018\u2019]?([^.'\u2018\u2019]+)['\u2018\u2019]?\.?")


HEB_RANGE = re.compile(r"[\u0590-\u05FF]")
GRK_RANGE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")


def detect_lang(text: str) -> str:
    if HEB_RANGE.search(text):
        return "Hebrew"
    if GRK_RANGE.search(text):
        return "Greek"
    return "Other"


def parse_opener(body: str) -> dict | None:
    """Return {'translit', 'original', 'gloss', 'lang'} or None if not parseable."""
    m = OPENER_WITH_ORIG.match(body.lstrip())
    if m:
        translit = m.group(1).strip()
        original = m.group(2).strip()
        rest = m.group(3).strip()
        gloss_m = GLOSS_RE.search(rest)
        gloss = gloss_m.group(1).strip() if gloss_m else ""
        return {
            "translit": translit,
            "original": original,
            "gloss": gloss,
            "lang": detect_lang(original),
        }
    m = OPENER_NO_ORIG.match(body.lstrip())
    if m:
        # Header without an <em> original — still useful as a transliteration entry.
        translit = m.group(1).strip()
        return {
            "translit": translit,
            "original": "",
            "gloss": "",
            "lang": "Other",
        }
    return None


def gather(book_filter: str | None = None) -> dict:
    """Return {(lang, translit_lower): {translit, original, gloss, lang, refs:[…]}}."""
    entries: dict = defaultdict(
        lambda: {"translit": "", "original": "", "gloss": "", "lang": "", "refs": []}
    )

    for f in sorted(NOTES_DIR.glob("*.py")):
        if f.name == "__init__.py":
            continue
        code = f.stem
        if book_filter and code != book_filter:
            continue
        notes = load_notes_from_text(f.read_text(encoding="utf-8"))
        if not notes:
            continue
        for tup in notes:
            if not isinstance(tup, tuple) or len(tup) < 8:
                continue
            ch, v, suffix, _anchor, kind, _title, _label, body = tup[:8]
            if kind != "word" or not isinstance(body, str):
                continue
            parsed = parse_opener(body)
            if not parsed:
                continue
            key = (parsed["lang"], parsed["translit"].lower())
            ent = entries[key]
            # First definition wins; later refs accumulate.
            if not ent["translit"]:
                ent.update(parsed)
            ent["refs"].append((code, ch, v, suffix))
    return entries


# ----------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------


LANG_ORDER = ["Hebrew", "Greek", "Other"]


def cmd_terminal(entries: dict, lang_filter: str | None) -> None:
    by_lang: dict = defaultdict(list)
    for (_lang, _key), ent in entries.items():
        by_lang[ent["lang"]].append(ent)

    total = sum(len(v) for v in by_lang.values())
    if total == 0:
        print(f"  {DIM}no word-notes found in scope{RESET}")
        return

    for lang in LANG_ORDER:
        if lang_filter and lang != lang_filter:
            continue
        items = sorted(by_lang.get(lang, []), key=lambda e: e["translit"].lower())
        if not items:
            continue
        print(f"\n  {BOLD}{lang} ({len(items)} entries){RESET}\n")
        for ent in items:
            translit = ent["translit"]
            orig = ent["original"]
            gloss = ent["gloss"]
            n_refs = len(ent["refs"])
            sample = ", ".join(f"{b} {c}:{v}{s or ''}" for b, c, v, s in ent["refs"][:3])
            more = "" if n_refs <= 3 else f" +{n_refs - 3}"
            head = f"{BOLD}{translit}{RESET}"
            if orig:
                head += f"  {orig}"
            if gloss:
                head += f"  {DIM}— '{gloss}'{RESET}"
            print(f"    {head}")
            print(f"      {DIM}{sample}{more}{RESET}")
    print(f"\n  {DIM}{total} distinct word entries.{RESET}")


def cmd_search(entries: dict, query: str) -> None:
    q = query.lower()
    hits = []
    for ent in entries.values():
        if (
            q in ent["translit"].lower()
            or q in ent["gloss"].lower()
            or q in ent["original"]
        ):
            hits.append(ent)
    if not hits:
        print(f"  {DIM}no matches for {query!r}{RESET}")
        return
    print(f"\n  {len(hits)} match{'es' if len(hits) != 1 else ''} for {query!r}:\n")
    for ent in sorted(hits, key=lambda e: e["translit"].lower()):
        head = f"{BOLD}{ent['translit']}{RESET}"
        if ent["original"]:
            head += f"  {ent['original']}"
        if ent["gloss"]:
            head += f"  — '{ent['gloss']}'"
        print(f"    [{ent['lang']}] {head}")
        for b, c, v, s in ent["refs"]:
            print(f"      {b} {c}:{v}{s or ''}")


def cmd_html(entries: dict, out_path: Path) -> None:
    by_lang: dict = defaultdict(list)
    for ent in entries.values():
        by_lang[ent["lang"]].append(ent)

    sections = []
    for lang in LANG_ORDER:
        items = sorted(by_lang.get(lang, []), key=lambda e: e["translit"].lower())
        if not items:
            continue
        rows = []
        for ent in items:
            refs_html = ", ".join(
                f"{html.escape(b)} {c}:{v}{html.escape(s or '')}"
                for b, c, v, s in ent["refs"]
            )
            translit_html = html.escape(ent["translit"])
            orig_html = html.escape(ent["original"])
            gloss_html = html.escape(ent["gloss"])
            rows.append(
                f'<tr><td class="translit">{translit_html}</td>'
                f'<td class="orig" lang="{"he" if lang == "Hebrew" else ("el" if lang == "Greek" else "und")}"'
                f' dir="{"rtl" if lang == "Hebrew" else "ltr"}">{orig_html}</td>'
                f"<td class=\"gloss\">{gloss_html}</td>"
                f'<td class="refs">{refs_html}</td></tr>'
            )
        sections.append(
            f"<h2>{html.escape(lang)} <span class='count'>· {len(items)}</span></h2>"
            "<table><thead><tr>"
            "<th>transliteration</th><th>original</th><th>gloss</th><th>verses</th>"
            "</tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
        )

    css = """
    :root { --paper:#f5f1e6; --ink:#2a2520; --muted:#8a8378; --rule:#d4c9ad;
            --accent:#8b2330; --hebrew:#2c4a6e; --greek:#9b7a2b; }
    body { margin: 0 auto; max-width: 76rem; padding: 3rem clamp(1rem,4vw,4rem) 5rem;
           background: var(--paper); color: var(--ink);
           font-family: "Iowan Old Style", "Charter", "Cambria", Georgia, serif;
           line-height: 1.55; }
    h1 { margin-top: 0; font-weight: 600; letter-spacing: -0.005em;
         border-bottom: 2px solid var(--ink); padding-bottom: 0.5rem; }
    h2 { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.12em;
         color: var(--muted); margin: 2.5rem 0 0.8rem;
         border-bottom: 1px solid var(--rule); padding-bottom: 0.4rem; font-weight: 600; }
    h2 .count { color: var(--accent); font-size: 0.9em; }
    table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
    th { text-align: left; padding: 0.4rem 0.7rem; color: var(--muted);
         text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em;
         border-bottom: 1px solid var(--rule); font-weight: 600; }
    td { padding: 0.45rem 0.7rem; border-bottom: 1px solid rgba(212,201,173,0.5);
         vertical-align: top; }
    td.translit { font-weight: 600; min-width: 9rem; }
    td.orig { font-size: 1.15em; color: var(--accent); min-width: 7rem;
              font-family: "SBL Hebrew","Ezra SIL","Cardo","Times New Roman", serif; }
    td.gloss { color: var(--ink); font-style: italic; min-width: 12rem; }
    td.refs { color: var(--muted); font-family: "iA Writer Mono", ui-monospace, monospace;
              font-size: 0.78rem; }
    """
    body = (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Ethiopian Bible — Glossary</title>"
        f"<style>{css}</style></head><body>"
        "<h1>Ethiopian Bible · Glossary</h1>"
        "<p style='color:var(--muted);font-style:italic;'>"
        "Hebrew, Greek, and other terms appearing in word-kind apparatus notes."
        "</p>" + "".join(sections) + "</body></html>"
    )
    out_path.write_text(body, encoding="utf-8")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Build a glossary from word-kind notes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--book", help="restrict scan to one book code")
    p.add_argument("--lang", choices=LANG_ORDER, help="show one language only")
    p.add_argument("--search", help="search transliteration / gloss / original (substring)")
    p.add_argument("--html", type=Path, help="write a self-contained HTML page")
    args = p.parse_args()

    if args.book and args.book not in config.books_by_code():
        print(f"{RED}ERROR: unknown book code {args.book!r}{RESET}", file=sys.stderr)
        sys.exit(2)

    entries = gather(args.book)

    if args.html:
        cmd_html(entries, args.html)
        size_kb = args.html.stat().st_size / 1024
        n = len(entries)
        print(
            f"\033[92m✓ glossary:\033[0m wrote {args.html} "
            f"({size_kb:.1f} KB · {n} entries)"
        )
        sys.exit(0)

    if args.search:
        cmd_search(entries, args.search)
        sys.exit(0)

    cmd_terminal(entries, args.lang)
    sys.exit(0)


if __name__ == "__main__":
    main()
