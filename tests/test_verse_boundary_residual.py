"""round-7 P3 — chapter-start verse-boundary regression pin.

The recovered base's WEB ingestion left chapter starts where verse 1 had NO
visible text (its WEB v1+v2 text sat merged under the v2 anchor, so the
printed v2 number labelled v1's words and the v1/v2 popups paired off-by-one
with what the eye reads). The 2026-06-06 pass repaired 161 chapters from a
KJV-derived anchor; the round-7 sweep repaired the 117 residual sites from
WEB ground truth (``content/sources/web_boundary_anchors.json``; design:
``docs/superpowers/notes/2026-06-10-verse-boundary-residual-design.md``),
including the two-step sites (1ch 1, sir 18) and the two-verse psa 117.

This pin encodes the SIGNATURE SCAN as a permanent test so a future base
recovery / re-bake cannot silently reintroduce the class: at every chapter
start carrying both a v1 and a v2 vn-link anchor, the region between them
must contain visible text (verse 1 is never empty). Allowlist below for any
future LEGIT-BRIDGE site (WEB printing one bridged verse) — none exist today.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EPUB = REPO / "epub_working"

NOTE_A = re.compile(r'<a class="note-ref.*?</a>', re.DOTALL)
TAGS = re.compile(r"<[^>]+>")
V1 = re.compile(r'<a class="vn-link" id="v-([a-z0-9]+)-(\d+)-1"[^>]*>\s*<span class="vn">1</span>\s*</a>')

# Sites where WEB itself bridges verse 1-2 (a single printed verse) — an empty
# v1 region is then CORRECT. None exist in the current base; add "book-ch"
# strings here only with fixture evidence (web_boundary_anchors.json "bridge").
LEGIT_BRIDGE_ALLOWLIST: frozenset[str] = frozenset()


class TestChapterStartVerseBoundary:
    def test_no_empty_verse_one_at_any_chapter_start(self):
        offenders: list[str] = []
        checked = 0
        for f in sorted(EPUB.glob("index_split_*.html")):
            t = f.read_text(encoding="utf-8")
            for m in V1.finditer(t):
                book, ch = m.group(1), m.group(2)
                v2 = t.find(f'id="v-{book}-{ch}-2"', m.end())
                if v2 < 0:
                    continue  # single-verse chapter or strategy-B book
                checked += 1
                site = f"{book}-{ch}"
                between = t[m.end() : t.rfind("<a ", 0, v2)]
                if not TAGS.sub("", NOTE_A.sub("", between)).strip() and site not in LEGIT_BRIDGE_ALLOWLIST:
                    offenders.append(f"{f.name}:{site}")
        assert checked > 1300, f"scan degenerated — only {checked} chapter starts seen"
        assert not offenders, (
            f"{len(offenders)} chapter start(s) have an EMPTY verse 1 (v1/v2 popup "
            f"off-by-one class — see the round-7 sweep design): {offenders[:10]}"
        )
