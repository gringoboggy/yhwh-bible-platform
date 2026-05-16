"""τ.6.x.5 — HaCohen external Ge'ez PD-source ingest.

Fetches Ran HaCohen's clean Unicode-Ge'ez critical editions
(tau.ac.il/~hacohen), caches HTML locally, parses per-verse text,
and writes a standard translation module. The source's own verse
numbering is authoritative — the canonical floor is used for
VALIDATION only, never to renumber (see the design spec
docs/superpowers/specs/2026-05-16-geez-external-source-ingest-design.md).
"""

from __future__ import annotations

import argparse
import html as _html
import re
import sys
import time
from datetime import date
from pathlib import Path

from scripts.core import http

# Path: re-added at τ.6.x.5 Task 4 (genuinely used by DEFAULT_CACHE;
# AUDIT-DEEP-5 F-DEEP5-8 had removed it as prematurely-dead at Task 3).
# urllib.request dropped — the external-HTTP lint rule requires all
# outbound HTTP go through scripts/core/http.py (retry+timeout+SSRF).

_P_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
_VERSENUM_RE = re.compile(
    r"^\s*<span[^>]*font-size:\s*70%[^>]*>\s*(\d+)\s*</span>",
    re.IGNORECASE,
)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
# The chapter-caption anchor <a ...><!--Cap.-->N<!--Cap.end --></a>.
# Ps 118/151 et al. put it INLINE in the same <p> as verse 1's
# number span (Ps 1 has it standalone) — it must be stripped, not
# cause the <p> to be skipped (that dropped verse 1: the τ.7.x
# calibrate off-by-one, 175/176 with first verse = 2).
_CAP_RE = re.compile(
    r"<a\b[^>]*>\s*<!--Cap\.-->.*?<!--Cap\.end\s*-->\s*</a>",
    re.IGNORECASE | re.DOTALL,
)


def _clean_fragment(fragment_html: str) -> str:
    """Strip the optional leading verse-number span, all tags, and
    unescape HTML entities to real Unicode Ge'ez; collapse whitespace."""
    no_num = _VERSENUM_RE.sub("", fragment_html, count=1)
    no_tags = _TAG_RE.sub("", no_num)
    text = _html.unescape(no_tags)
    return _WS_RE.sub(" ", text).strip()


def parse_hacohen_psalter(page_html: str, psalm_number: int) -> list[tuple[int, int, str]]:
    """Parse one HaCohen Ludolf Psalm page into (psalm, verse, text).

    A new verse begins at a <p> whose leading element is
    <span style='font-size:70%'>N</span>. Subsequent number-less <p>
    blocks are continuation cola of the current verse. Title /
    "Nr. Vers." toggle / "Cap." caption paragraphs are skipped, as
    is any paragraph before the first numbered verse (superscription
    — not a Rahlfs-numbered verse on this view).
    """
    verses: list[tuple[int, int, str]] = []
    cur_v: int | None = None
    parts: list[str] = []

    def flush() -> None:
        nonlocal parts
        if cur_v is not None and parts:
            joined = " ".join(p for p in parts if p).strip()
            if joined:
                verses.append((psalm_number, cur_v, joined))
        parts = []

    for m in _P_RE.finditer(page_html):
        inner = m.group(1)
        if "Nr. Vers" in inner:
            continue
        # Strip the inline chapter-caption anchor BEFORE detecting the
        # verse-number span. Skipping the whole <p> on "<!--Cap."
        # dropped verse 1 for the psalms that inline the caption with
        # verse 1 (Ps 118/151 …). After stripping, verse 1's <span>
        # is leading again; a caption-only <p> cleans to empty and is
        # dropped by the existing not-text guard.
        inner = _CAP_RE.sub("", inner)
        vm = _VERSENUM_RE.match(inner.lstrip())
        text = _clean_fragment(inner)
        if not text:
            continue
        if vm:
            flush()
            cur_v = int(vm.group(1))
            parts = [text]
        elif cur_v is not None:
            parts.append(text)
        # else: pre-verse-1 superscription — skip
    flush()
    return verses


_BASE = "https://www.tau.ac.il/~hacohen/"
_PSALM_URL = _BASE + "Psalm/PsalmNrR%20{n}.html"
DEFAULT_CACHE = (
    Path(__file__).resolve().parent.parent / "content" / "translations" / "sources" / "hacohen-geez" / "cache"
)


_HACOHEN_ALLOWLIST = frozenset({"tau.ac.il"})  # www.tau.ac.il (subdomain-aware) — the user-authorized PD source


def _http_get(url: str) -> str:
    """Fetch a URL as text via the project's retry+timeout HTTP
    wrapper (``scripts/core/http.py`` — required by the external-HTTP
    lint rule; provides retry/backoff + the SSRF allowlist). HaCohen
    pages are UTF-8 (ASCII NCR entities). Isolated for test
    monkeypatching (callers/tests patch this function, not http.get)."""
    return http.get(url, allowlist=_HACOHEN_ALLOWLIST).decode("utf-8", "replace")


def fetch_psalm(n: int, *, cache_dir: Path = DEFAULT_CACHE, delay: float = 1.0) -> Path:
    """Return the local cached HTML path for Psalm ``n`` (Rahlfs view),
    fetching politely once if absent. Never partial-writes on error."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    dest = cache_dir / f"PsalmNrR {n}.html"
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    text = _http_get(_PSALM_URL.format(n=n))  # raises on failure → no write below
    tmp = dest.with_suffix(".html.part")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(dest)
    time.sleep(delay)
    return dest


def calibrate(*, sample: list[int], cache_dir: Path = DEFAULT_CACHE) -> dict:
    """Parse the calibration sample from cache and report GO/NO-GO.

    GO requires every sampled Psalm to parse to >=1 verse with the
    first verse numbered 1. NO-GO returns a human reason; the caller
    must NOT write any artifacts on NO-GO (τ.6.x.0b honesty contract).
    """
    parsed: dict[int, list[tuple[int, int, str]]] = {}
    for n in sample:
        path = cache_dir / f"PsalmNrR {n}.html"
        if not path.exists():
            return {"go": False, "reason": f"calibration page Psalm {n} not in cache", "parsed": parsed}
        vs = parse_hacohen_psalter(path.read_text(encoding="utf-8"), n)
        parsed[n] = vs
        if not vs:
            return {"go": False, "reason": f"no verses parsed for Psalm {n}", "parsed": parsed}
        if vs[0][1] != 1:
            return {"go": False, "reason": f"Psalm {n} does not start at verse 1", "parsed": parsed}
    return {"go": True, "reason": "calibration sample parsed cleanly", "parsed": parsed}


def ingest_psalms(*, cache_dir: Path = DEFAULT_CACHE, phase: str) -> Path:
    """Parse all 151 cached Psalm pages and write geez-tewahedo/psa.py
    at digitized-critical-edition quality. Source numbering is
    authoritative (NOT renumbered against the floor)."""
    from scripts.extract_parallel_pdf import write_book_module

    all_verses: list[tuple[int, int, str]] = []
    for n in range(1, 152):
        path = cache_dir / f"PsalmNrR {n}.html"
        all_verses.extend(parse_hacohen_psalter(path.read_text(encoding="utf-8"), n))
    return write_book_module(
        "geez-tewahedo",
        "psa",
        all_verses,
        "digitized-critical-edition",
        date.today().isoformat(),
        ingest_phase=phase,
        docstring_extra=(
            "Ingested from Ran HaCohen's digitized Ge'ez Psalter "
            "(Psalterium Davidis, ed. Hiob Ludolf 1701; Rahlfs/LXX "
            "verse numbering; PD by age). Source numbering is "
            "authoritative — NOT renumbered against the floor; "
            "per-chapter deltas vs PSALMS_VERSE_COUNTS are recorded "
            "for the τ.6.x.3 audit."
        ),
        source_provenance="hacohen-geez",
        source_yaml_ref="content/translations/sources/hacohen-geez/_source.yaml",
        tool="scripts/ingest_hacohen.py",
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="HaCohen Ge'ez external-source ingest (τ.6.x.5)")
    p.add_argument("--book", required=True, choices=["psalms"])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--fetch", action="store_true", help="fetch+cache all 151 Psalm pages")
    g.add_argument("--calibrate", action="store_true", help="parse the calibration sample, print GO/NO-GO")
    g.add_argument("--ingest", action="store_true", help="write geez-tewahedo/psa.py from cache (requires GO)")
    p.add_argument("--phase", default=None, help="ingest phase tag, e.g. τ.6.x.2.i")
    args = p.parse_args(argv)

    if args.fetch:
        for n in range(1, 152):
            dest = fetch_psalm(n)
            print(f"cached Psalm {n} -> {dest}")
        return 0
    if args.calibrate:
        r = calibrate(sample=[1, 118, 151])
        print(f"{'GO' if r['go'] else 'NO-GO'}: {r['reason']}")
        return 0 if r["go"] else 1
    if args.ingest:
        if not args.phase:
            p.error("--ingest requires --phase")
        r = calibrate(sample=[1, 118, 151])
        if not r["go"]:
            print(f"NO-GO: {r['reason']} — refusing to ingest (colometric-merge fallback applies)")
            return 1
        out = ingest_psalms(phase=args.phase)
        print(f"wrote {out}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
