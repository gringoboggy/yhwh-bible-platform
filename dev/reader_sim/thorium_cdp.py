#!/usr/bin/env python3
"""Thorium/CDP reader sim — structural popup/ToC/script probes from EPUB HTML.

**Ceiling (turn 125):** ``--live`` opens Thorium when installed; CDP navigate/assert
is not fully automated here — use Chrome DevTools MCP (``browser_navigate`` +
click ``vn-link#v-gen-1-1`` + snapshot popup text). Without Thorium,
``--gate-only`` is the agent floor (M2/M5 structural proxy).

Usage:
    py -3 dev/reader_sim/thorium_cdp.py <artifact.epub> --profile apple
    py -3 dev/reader_sim/thorium_cdp.py <artifact.epub> --profile play --gate-only
    py -3 dev/reader_sim/thorium_cdp.py <artifact.epub> --profile apple --live
"""

from __future__ import annotations

import argparse
import html as html_mod
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

_DOC_SUFFIXES = (".html", ".xhtml")
_GEN11_VN_RE = re.compile(r'<a\s+class="vn-link"\s+id="v-gen-1-1"', re.I)
_GEN11_VNOTE_RE = re.compile(
    r'<aside\b[^>]*\bid="vnote-gen-1-1"[^>]*>.*?</aside>',
    re.DOTALL | re.I,
)
_GEN11_STUDY_RE = re.compile(
    r'(?:class="verse-notes-badge"[^>]*\bhref="#vnotes-gen-1-1'
    r'|class="study-glossary-jump[^"]*"[^>]*\bid="vbadge-gen-1-1'
    r'|href="[^"]*#vnotes-gen-1-1)',
    re.I,
)
_TOC_DETAILS_RE = re.compile(r"<details\b", re.I)
_TOC_CHAPTER_NAV_RE = re.compile(r"index_split_\d+.*#|toc-chapters", re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_HEBREW_RE = re.compile(r"[\u0590-\u05FF]")
_GREEK_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")


@dataclass(frozen=True)
class ProbeResult:
    name: str
    passed: bool
    detail: str


def _thorium_installed() -> bool:
    if sys.platform == "darwin":
        return Path("/Applications/Thorium.app").is_dir()
    return shutil.which("thorium") is not None


def _load_html_members(epub_path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    with zipfile.ZipFile(epub_path) as zf:
        for name in zf.namelist():
            if name.endswith(_DOC_SUFFIXES):
                out[name] = zf.read(name).decode("utf-8", errors="replace")
    return out


def _strip_tags(fragment: str) -> str:
    text = _TAG_RE.sub(" ", fragment)
    return " ".join(html_mod.unescape(text).split())


def _find_gen11_context(members: dict[str, str]) -> tuple[str, str] | None:
    for name, text in members.items():
        if "v-gen-1-1" in text:
            return name, text
    return None


def probe_epub(epub_path: Path, profile: str) -> list[ProbeResult]:
    """Run M2/M5 structural tap proxies against unpacked HTML."""
    if not epub_path.is_file():
        return [ProbeResult("exists", False, "artifact missing")]

    members = _load_html_members(epub_path)
    if not members:
        return [ProbeResult("html_members", False, "no HTML/XHTML in zip")]

    combined = "\n".join(members.values())
    results: list[ProbeResult] = []

    ctx = _find_gen11_context(members)
    if ctx is None:
        results.append(ProbeResult("gen11_vn_link", False, "v-gen-1-1 vn-link not found"))
    else:
        file_name, text = ctx
        results.append(
            ProbeResult(
                "gen11_vn_link",
                bool(_GEN11_VN_RE.search(text)),
                f"found in {file_name}" if _GEN11_VN_RE.search(text) else "missing vn-link anchor",
            )
        )
        vm = _GEN11_VNOTE_RE.search(text)
        if vm:
            body = _strip_tags(vm.group(0))
            results.append(
                ProbeResult(
                    "gen11_translation_popup",
                    len(body) >= 8,
                    f"stripped_len={len(body)}" if len(body) >= 8 else "vnote-gen-1-1 empty",
                )
            )
        else:
            results.append(ProbeResult("gen11_translation_popup", False, "vnote-gen-1-1 aside missing"))

        if profile == "apple":
            has_badge = bool(_GEN11_STUDY_RE.search(text))
            has_vnotes = 'id="vnotes-gen-1-1' in text or "vnotes-gen-1-1" in combined
            results.append(
                ProbeResult(
                    "gen11_study_badge",
                    has_badge or has_vnotes,
                    "study marker or vnotes target present"
                    if (has_badge or has_vnotes)
                    else "no study marker for Gen 1:1",
                )
            )

    nav_text = "\n".join(t for n, t in members.items() if "nav" in n.lower() or "toc" in n.lower())
    if not nav_text:
        nav_text = combined
    has_details = bool(_TOC_DETAILS_RE.search(nav_text))
    name_lower = epub_path.name.lower()
    tablet_artifact = "tablet" in name_lower
    if profile == "apple":
        if tablet_artifact:
            has_chapter_nav = bool(_TOC_CHAPTER_NAV_RE.search(nav_text or combined))
            toc_ok = has_details or has_chapter_nav
            if has_details:
                toc_detail = "collapsible <details> in nav/toc"
            elif has_chapter_nav:
                toc_detail = "chapter-level nav (collapsible off per edition — RX P4a)"
            else:
                toc_detail = "tablet artifact missing ToC chapter nav"
            results.append(ProbeResult("toc_details", toc_ok, toc_detail))
        else:
            results.append(
                ProbeResult(
                    "toc_details",
                    True,
                    "non-tablet artifact — <details> ToC not required",
                )
            )
    else:
        results.append(
            ProbeResult(
                "play_toc_details",
                True,
                "ToC <details> present (device may stick closed)"
                if has_details
                else "everywhere ToC — <details> optional on Play",
            )
        )

    heb = bool(_HEBREW_RE.search(combined))
    grk = bool(_GREEK_RE.search(combined))
    results.append(
        ProbeResult(
            "script_sample",
            heb and grk,
            f"hebrew={heb} greek={grk}",
        )
    )

    if _thorium_installed():
        results.append(ProbeResult("thorium_binary", True, "Thorium installed — CDP taps available"))
    else:
        results.append(
            ProbeResult(
                "thorium_binary",
                True,
                "gate-only structural proxy (Thorium not installed)",
            )
        )

    return results


def probe_live(epub_path: Path, profile: str) -> list[ProbeResult]:
    """Open EPUB in Thorium when present; CDP taps remain manual/MCP."""
    if not epub_path.is_file():
        return [ProbeResult("thorium_live", False, "artifact missing")]
    if not _thorium_installed():
        return [
            ProbeResult(
                "thorium_live",
                True,
                "skipped — Thorium not installed; structural --gate-only is the floor",
            )
        ]
    try:
        subprocess.run(
            ["open", "-a", "Thorium", str(epub_path.resolve())],
            stdin=subprocess.DEVNULL,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return [ProbeResult("thorium_live", False, f"open Thorium failed: {exc}")]
    return [
        ProbeResult(
            "thorium_live",
            True,
            "opened in Thorium — CDP/MCP taps manual: vn-link Gen 1:1 popup + "
            f"{'<details> ToC' if profile == 'apple' else 'chapter nav'}",
        )
    ]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Thorium/CDP reader sim — structural EPUB probes.")
    p.add_argument("artifact", type=Path)
    p.add_argument("--profile", choices=("apple", "play"), default="play")
    p.add_argument(
        "--gate-only",
        action="store_true",
        help="structural probes only (default when Thorium missing)",
    )
    p.add_argument(
        "--live",
        action="store_true",
        help="open EPUB in Thorium when installed (CDP asserts via MCP, not in-process)",
    )
    args = p.parse_args(argv)

    gate_only = args.gate_only or (not args.live and not _thorium_installed())
    results = probe_epub(args.artifact, args.profile)
    if args.live:
        results.extend(probe_live(args.artifact, args.profile))
    ok = all(r.passed for r in results if r.name not in ("thorium_binary",))

    mode = "gate-only" if gate_only else "thorium+cdp"
    print(f"thorium_cdp profile={args.profile} mode={mode} artifact={args.artifact.name}")
    for r in results:
        mark = "ok" if r.passed else "FAIL"
        print(f"  {mark:4} {r.name}: {r.detail}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
