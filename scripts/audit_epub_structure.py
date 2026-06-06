"""Structural-consistency audit for a BUILT EPUB (RX-beta2 ⑪).

Every notes-pill, translation-pill, book, chapter, and verse is generated from
ONE template, so the emitted markup is uniform — any deviation is a bug. This
diagnostic parses a built ``.epub`` and flags the deviations epubcheck does not:

  1. DUP_NOTE_ROWS   — two byte-identical notes inside one verse-notes popup
                       (the duplicate-cross-ref class of bug).
  2. DUP_IDS         — an ``id="…"`` repeated within a single XHTML file
                       (illegal; a broken anchor target).
  3. BROKEN_NOTEREF  — a ``href="#X"`` (noteref / vn-link) whose ``id="X"`` does
                       not exist in the same file (a popup that opens nothing).
  4. UNBALANCED_TAGS — a piece that is not well-formed (missing ``<``/``>`` or an
                       unclosed element) — the broken-markup signature.
  5. NEAR_EMPTY_PAGE — a bodymatter piece with almost no visible text (a
                       blank-page candidate; informational).

Usage:
    py -3 -m scripts.audit_epub_structure <path-to.epub> [--json]

Exit code is non-zero when any CRITICAL finding (1-4) is present, so it can gate
a build. NEAR_EMPTY_PAGE is reported but never fatal.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter
from html.parser import HTMLParser

# Bodymatter pieces only (the cover/nav/opf are not template-uniform).
_BODY_RE = re.compile(r"index_split_[0-9_]+\.html$")
# Only a REAL ``id="…"`` (preceded by whitespace) — never the ``-id="…"`` tail of
# a data-* attribute such as ``data-tradition-id="cross"``.
_ID_RE = re.compile(r'(?<=\s)id="([^"]+)"')
_HREF_HASH_RE = re.compile(r'href="#([^"]+)"')
_VERSE_NOTES_RE = re.compile(r'<aside class="verse-notes"[^>]*>(.*?)</aside>', re.DOTALL)
_VN_KIND_RE = re.compile(r'note-([a-z0-9-]+)"')
_TAG_RE = re.compile(r"<[^>]+>")
_VOID = {"br", "img", "hr", "meta", "link", "input", "source", "col", "area", "base", "wbr"}


class _Balance(HTMLParser):
    """A tolerant well-formedness check: every non-void start tag must close."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in _VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in _VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.errors.append(f"unclosed <{self.stack.pop()}>")
            if self.stack:
                self.stack.pop()
        else:
            self.errors.append(f"stray </{tag}>")


def _text(html: str) -> str:
    return " ".join(_TAG_RE.sub(" ", html).split())


def _check_dup_rows(html: str, short: str, findings: dict) -> None:
    for aside in _VERSE_NOTES_RE.findall(html):
        seen: set[str] = set()
        for chunk in aside.split('<div class="vn-item ')[1:]:
            km = _VN_KIND_RE.match(chunk)
            kind = km.group(1) if km else "?"
            body = _text(chunk).replace("</aside>", "").strip()
            key = f"{kind}|{body}"
            if body and key in seen:
                findings["DUP_NOTE_ROWS"].append({"file": short, "kind": kind, "snippet": body[:70]})
            seen.add(key)


def _check_wellformed(html: str, short: str, findings: dict) -> None:
    b = _Balance()
    try:
        b.feed(html)
        b.close()
    except Exception as e:  # noqa: BLE001 — any parser failure is a finding
        findings["UNBALANCED_TAGS"].append({"file": short, "error": f"parse: {e}"})
    if b.stack:
        findings["UNBALANCED_TAGS"].append({"file": short, "error": f"unclosed: {b.stack[-5:]}"})
    for err in b.errors[:5]:
        findings["UNBALANCED_TAGS"].append({"file": short, "error": err})


def _check_file(html: str, short: str, findings: dict) -> None:
    ids = _ID_RE.findall(html)
    for dup, c in Counter(ids).items():
        if c > 1:
            findings["DUP_IDS"].append({"file": short, "id": dup, "count": c})
    idset = set(ids)
    for tgt in set(_HREF_HASH_RE.findall(html)):
        if tgt not in idset:
            findings["BROKEN_NOTEREF"].append({"file": short, "missing_target": tgt})
    _check_dup_rows(html, short, findings)
    _check_wellformed(html, short, findings)
    body_m = re.search(r"<body[^>]*>(.*)</body>", html, re.DOTALL)
    visible = _text(body_m.group(1)) if body_m else _text(html)
    if len(visible) < 60:
        findings["NEAR_EMPTY_PAGE"].append({"file": short, "chars": len(visible)})


def audit_epub(epub_path: str) -> dict:
    findings: dict[str, list] = {
        "DUP_NOTE_ROWS": [],
        "DUP_IDS": [],
        "BROKEN_NOTEREF": [],
        "UNBALANCED_TAGS": [],
        "NEAR_EMPTY_PAGE": [],
    }
    with zipfile.ZipFile(epub_path) as zf:
        for name in sorted(n for n in zf.namelist() if _BODY_RE.search(n)):
            html = zf.read(name).decode("utf-8", "replace")
            _check_file(html, name.rsplit("/", 1)[-1], findings)
    critical = sum(len(findings[k]) for k in ("DUP_NOTE_ROWS", "DUP_IDS", "BROKEN_NOTEREF", "UNBALANCED_TAGS"))
    return {"epub": epub_path, "critical": critical, "findings": findings}


def _print(report: dict) -> None:
    f = report["findings"]
    print(f"\nStructural audit — {report['epub']}")
    for key in ("DUP_NOTE_ROWS", "DUP_IDS", "BROKEN_NOTEREF", "UNBALANCED_TAGS", "NEAR_EMPTY_PAGE"):
        items = f[key]
        mark = "OK " if not items else ("crit" if key != "NEAR_EMPTY_PAGE" else "info")
        print(f"  [{mark}] {key}: {len(items)}")
        for it in items[:8]:
            print(f"        - {it}")
        if len(items) > 8:
            print(f"        … +{len(items) - 8} more")
    print(f"  => {report['critical']} critical finding(s)\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Structural-consistency audit for a built EPUB.")
    p.add_argument("epub", help="path to the built .epub")
    p.add_argument("--json", action="store_true", help="emit the full report as JSON")
    args = p.parse_args(argv)
    report = audit_epub(args.epub)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print(report)
    return 1 if report["critical"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
