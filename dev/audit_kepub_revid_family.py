#!/usr/bin/env python3
"""Round-15 D9 — kepub popup-id ``-sN`` rev-id family census (guard #19).

A Kobo ``.kepub`` reaches its INLINE footnote popups via Nickel's slice measurement,
which mis-fires when an inline ``verse-notes`` aside id is a strict PREFIX of a sibling
(the K-R6-2 reason every inline id wears a single-digit ``-s1``..``-s9`` tail). The
BACKMATTER navigate family (``study-glossary-cat`` asides reached by a cross-file
``noteref``) is bare ON PURPOSE — Kobo NAVIGATES to it, no slice measurement. Guard #19
(the "792 bare rev ids" scare) conflates the two; this gate separates them:

  * BUCKET A — inline (``class`` begins ``verse-notes`` / ``vnote``, NOT
    ``study-glossary-cat``): EVERY ``vnotes-*`` aside id MUST carry a ``-s[1-9]`` tail.
    Any bare inline id is a LIVE regression (the footnote navigates away mid-read).
  * BUCKET B — navigate (``study-glossary-cat``): bare is correct; counted, never failed.

Plus a LIVENESS self-check (the program's ``_POPUP_ASIDE_RE`` blindspot): if kepubify
ever reorders attributes so ``class`` is no longer first, the aside regex matches 0 and a
naive gate passes VACUOUSLY. We assert the popup-aside regex matches > 0 on a koboSpan'd
file. Per-book census (isolating ``rev``) so future rounds don't re-derive ad-hoc counts.

Run on a FRESH ``.kepub`` (kepubify v4.0.4) — an aged dist artifact is the trap guard #19
fell into.

Usage:
    py -3 dev/audit_kepub_revid_family.py <kepub> [<kepub> ...] [--json OUT.json] [--census]
Exit 0 = no bare inline id + liveness ok; 1 = any bare inline id (live regression) or a
vacuous-match liveness failure.
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field

# Every <aside> with an id, attribute-order-agnostic (does NOT assume class is first — the
# point of the liveness check is that a class-first regex can go vacuous).
_ASIDE_RE = re.compile(r"<aside\b([^>]*)>")
_ID_RE = re.compile(r'\bid="([^"]+)"')
_CLASS_RE = re.compile(r'\bclass="([^"]*)"')
# The program's class-FIRST popup regex (mirrors dev/verify_kr2_build._POPUP_ASIDE_RE) —
# used ONLY as the liveness probe (matches 0 ⇒ kepubify reordered attrs ⇒ vacuous gate).
_CLASS_FIRST_POPUP_RE = re.compile(r'<aside class="(?:verse-notes|vnote)[^"]*" id="')
_SN_TAIL_RE = re.compile(r"-s[1-9]$")
# vnotes-{code}-{ch}-{v}-…  → pull the book code for the per-book census.
_VNOTES_CODE_RE = re.compile(r"^vnotes?-([a-z0-9]+)-\d")


@dataclass
class RevidResult:
    path: str
    fails: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)
    by_book: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def green(self) -> bool:
        return not self.fails


def _book_of(vid: str) -> str:
    m = _VNOTES_CODE_RE.match(vid)
    return m.group(1) if m else "?"


def _bucket(vid: str, cls: str) -> str | None:
    """The ``vnotes`` aside's family: ``nav`` (navigate — bare by design), ``inline_sn``
    (inline with its required ``-sN`` tail), ``inline_bare`` (inline MISSING ``-sN`` = the
    live guard-#19 regression), or ``None`` (not a popup family)."""
    if "study-glossary-cat" in cls:
        return "nav"
    if "verse-notes" in cls or "vnote" in cls:
        return "inline_sn" if _SN_TAIL_RE.search(vid) else "inline_bare"
    return None


def audit_kepub(path: str, max_show: int = 25) -> RevidResult:
    res = RevidResult(path=path)
    counts = {"inline_sn": 0, "inline_bare": 0, "nav": 0}
    liveness = popup_family = 0
    bare_samples: list[str] = []
    by_book: dict[str, dict[str, int]] = defaultdict(lambda: {"inline_sn": 0, "inline_bare": 0, "nav": 0})
    with zipfile.ZipFile(path) as zf:
        for n in zf.namelist():
            if not n.endswith((".html", ".xhtml")):
                continue
            text = zf.read(n).decode("utf-8", "replace")
            liveness += len(_CLASS_FIRST_POPUP_RE.findall(text))
            for m in _ASIDE_RE.finditer(text):
                attrs = m.group(1)
                clsm = _CLASS_RE.search(attrs)
                cls = clsm.group(1) if clsm else ""
                # Attr-agnostic membership in the _POPUP_ASIDE_RE family (inline verse-notes
                # or a vnote translation popup, NOT the navigate glossary) — the baseline the
                # class-FIRST liveness probe is compared against.
                if ("verse-notes" in cls and "study-glossary-cat" not in cls) or "vnote" in cls:
                    popup_family += 1
                idm = _ID_RE.search(attrs)
                vid = idm.group(1) if idm else ""
                bucket = _bucket(vid, cls) if vid.startswith("vnotes") else None
                if bucket is None:
                    continue
                counts[bucket] += 1
                by_book[_book_of(vid)][bucket] += 1
                if bucket == "inline_bare" and len(bare_samples) < max_show:
                    bare_samples.append(f"{n.rsplit('/', 1)[-1]} :: {vid} (class={cls[:40]!r})")

    inline_bare = counts["inline_bare"]
    # Bucket A bare = the live regression guard #19 actually cares about.
    for s in bare_samples:
        res.fails.append(f"bare INLINE popup id (no -sN → Kobo navigates away mid-read): {s}")
    if inline_bare > len(bare_samples):
        res.fails.append(f"… +{inline_bare - len(bare_samples)} more bare inline id(s)")
    # Liveness: when the kepub DOES contain inline/vnote popup asides (attr-agnostic) but
    # the class-FIRST popup regex matched 0, kepubify reordered the attributes and the
    # verify_kr2_build gate is matching 0 → passing VACUOUSLY. (0 popups → 0 matches is fine.)
    if popup_family > 0 and liveness == 0:
        res.fails.append(
            f"LIVENESS: {popup_family} inline/vnote popup aside(s) present but the class-first "
            "popup regex matched 0 — kepubify reordered attributes; verify_kr2_build would pass VACUOUSLY"
        )
    res.stats = {
        "inline_sN": counts["inline_sn"],
        "inline_bare": counts["inline_bare"],
        "navigate_bare_by_design": counts["nav"],
        "liveness_class_first_matches": liveness,
    }
    res.by_book = {b: v for b, v in sorted(by_book.items()) if v["inline_bare"] or b == "rev"}
    return res


def _print(res: RevidResult, census: bool) -> None:
    name = res.path.replace("\\", "/").rsplit("/", 1)[-1]
    s = res.stats
    status = "PASS" if res.green else "FAIL"
    print(f"\n=== {name} — D9 kepub rev-id family {status} ===")
    if s:
        print(
            f"  inline -sN={s['inline_sN']} | inline BARE={s['inline_bare']} (live-regression) | "
            f"navigate bare (by-design)={s['navigate_bare_by_design']} | "
            f"liveness matches={s['liveness_class_first_matches']}"
        )
    for f in res.fails:
        print("  ✗", f)
    for w in res.warns:
        print("  ⚠", w)
    if census and res.by_book:
        print("  -- per-book (inline_bare>0 or rev) --")
        for b, v in res.by_book.items():
            print(f"     {b}: inline_sN={v['inline_sn']} inline_bare={v['inline_bare']} nav={v['nav']}")


def main(argv: list[str]) -> int:
    _value_flags = ("--json",)
    _skip = {argv.index(f) + 1 for f in _value_flags if f in argv}
    paths = [a for i, a in enumerate(argv) if not a.startswith("--") and i not in _skip]
    json_out = argv[argv.index("--json") + 1] if "--json" in argv else None
    census = "--census" in argv
    if not paths:
        print(__doc__)
        return 2
    results = [audit_kepub(p) for p in paths]
    for r in results:
        _print(r, census)
    if json_out:
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump(
                [
                    {"path": r.path, "green": r.green, "stats": r.stats, "by_book": r.by_book, "fails": r.fails}
                    for r in results
                ],
                fh,
                indent=1,
            )
        print(f"\nwrote {json_out}")
    print(f"\nTOTAL: {sum(r.green for r in results)}/{len(results)} kepub(s) rev-id-clean")
    return 1 if any(not r.green for r in results) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
