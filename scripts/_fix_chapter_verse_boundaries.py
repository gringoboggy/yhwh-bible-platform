"""One-shot: repair the chapter-start verse-boundary bug in the recovered base
(RX-beta2 — see docs/superpowers/notes/2026-06-06-chapter-start-verse-boundary-bug.md).

At many chapter starts the base has an EMPTY verse-1 (number + its fallback notes,
no text) and WEB verse-1 + verse-2 text MERGED under the verse-2 anchor. The text
is all present (recoverable) — only the verse boundary is wrong.

Per affected chapter the region between v1's anchor and v3's anchor is:
    [NOTES1] [V2ANCHOR] [TEXT1 = WEB v1] [TEXT2 = WEB v2]
and we rewrite it CONTENT-PRESERVINGLY (a reorder + one split) to:
    [TEXT1] [NOTES1] [V2ANCHOR] [TEXT2]
so verse 1 = number + WEB-v1 text + its notes, verse 2 = number + WEB-v2 text.

The only inferred value is the TEXT1|TEXT2 split point, found by locating WEB
verse-2's opening words (derived from the on-disk KJV store, corroborated by JPS)
inside the merged text. CONFIDENCE-GATED: split only when the anchor phrase occurs
exactly once; otherwise the chapter is FLAGGED and left untouched (never guess on
scripture). Idempotent. Run --dry-run first.

    py -3 -m scripts._fix_chapter_verse_boundaries --dry-run [--book exo]
    py -3 -m scripts._fix_chapter_verse_boundaries --apply
"""

from __future__ import annotations

import argparse
import importlib
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EPUB = REPO / "epub_working"

NOTE_A = re.compile(r'<a class="note-ref.*?</a>', re.DOTALL)
TAGS = re.compile(r"<[^>]+>")
LEADING = {"and", "now", "but", "so", "then", "for", "also", "yea"}
# KJV→modern word forms so a KJV-derived anchor matches the modern WEB reading text.
_SUBS = {
    "unto": "to",
    "thou": "you",
    "thee": "you",
    "thy": "your",
    "thine": "your",
    "ye": "you",
    "hath": "has",
    "doth": "does",
    "hast": "have",
    "art": "are",
    "wilt": "will",
    "shalt": "shall",
    "dost": "do",
    "saith": "says",
    "spake": "spoke",
    "bare": "bore",
    "brake": "broke",
    "cometh": "comes",
    "goeth": "goes",
}
_V1_RE = re.compile(r'<a class="vn-link" id="v-([a-z0-9]+)-(\d+)-1"[^>]*>\s*<span class="vn">1</span>\s*</a>')


def _kjv(book: str) -> dict:
    for trans in ("kjv", "jps", "douay-rheims"):
        try:
            mod = importlib.import_module(f"content.translations.{trans.replace('-', '_')}.{book}")
            return {(c, v): t for (c, v, t) in mod.VERSES}, trans
        except Exception:
            continue
    return {}, None


def _anchor_words(text: str, n: int = 5) -> list[str]:
    # Keep articles (they mark where verse-2 actually starts, e.g. "The woman…");
    # drop only a leading conjunction (KJV's "And"/"Now" that WEB usually omits)
    # and the bracketed KJV supplied-words so the anchor tracks shared wording.
    t = re.sub(r"\[[^\]]*\]", "", text).replace("¶", "").strip()
    words = re.findall(r"[A-Za-z']+", t)
    if words and words[0].lower() in LEADING:
        words = words[1:]
    return [_SUBS.get(w.lower(), w.lower()) for w in words[:n]]


def _visible_map(html: str):
    """Visible (note/tag-stripped) lowercased chars + each one's html offset."""
    vis: list[str] = []
    offs: list[int] = []
    i, n = 0, len(html)
    while i < n:
        if html[i] == "<":
            m = NOTE_A.match(html, i)
            if m:
                i = m.end()
                continue
            j = html.find(">", i)
            if j < 0:
                break
            i = j + 1
            continue
        vis.append(html[i].lower())
        offs.append(i)
        i += 1
    return "".join(vis), offs


def _find_split(merged: str, words: list[str]) -> int | None:
    if len(words) < 2:
        return None
    vis, offs = _visible_map(merged)
    # Try the verse-2 opening anchor at decreasing length (most precise first);
    # take the FIRST length that occurs EXACTLY ONCE. Each length keeps the
    # uniqueness gate, so a shorter anchor is accepted only when it is itself
    # unambiguous in this chapter's merged text — recall up, no guessing.
    for length in range(min(len(words), 4), 1, -1):
        pat = re.compile(r"\b" + r"\s+".join(re.escape(w) for w in words[:length]) + r"\b")
        hits = list(pat.finditer(vis))
        if len(hits) == 1:
            return offs[hits[0].start()]
    return None  # ambiguous or absent at every length -> do not guess


def process_file(path: Path, dry: bool):
    t = path.read_text(encoding="utf-8")
    out = []  # (book, ch, status, detail)
    edits = []  # (start, end, replacement) on original offsets

    for m in _V1_RE.finditer(t):
        book, ch = m.group(1), m.group(2)
        v1_end = m.end()
        v2 = t.find(f'id="v-{book}-{ch}-2"', v1_end)
        if v2 < 0:
            continue
        v2_open = t.rfind("<a ", 0, v2)
        notes1 = t[v1_end:v2_open]
        # affected == empty verse 1 (only notes/whitespace before v2)
        if TAGS.sub("", NOTE_A.sub("", notes1)).strip():
            continue
        v2_close = t.find("</a>", v2)
        if v2_close < 0:
            continue
        v2_end = v2_close + 4
        v3 = t.find(f'id="v-{book}-{ch}-3"', v2_end)
        if v3 < 0:
            out.append((book, ch, "SKIP", "no v3 anchor (2-verse chapter)"))
            continue
        v3_open = t.rfind("<a ", 0, v3)
        merged = t[v2_end:v3_open]

        verses, _ = _kjv(book)
        kjv_v2 = verses.get((int(ch), 2)) if verses else None
        if not kjv_v2:
            out.append((book, ch, "FLAG", "no KJV v2 to anchor on"))
            continue
        rel = _find_split(merged, _anchor_words(kjv_v2))
        if rel is None:
            out.append((book, ch, "FLAG", f"ambiguous/absent anchor: {_anchor_words(kjv_v2)}"))
            continue
        text1, text2 = merged[:rel], merged[rel:]
        if not TAGS.sub("", NOTE_A.sub("", text1)).strip():
            out.append((book, ch, "FLAG", "split would leave v1 empty"))
            continue
        v2anchor = t[v2_open:v2_end]
        new_region = text1 + notes1 + v2anchor + text2
        edits.append((v1_end, v3_open, new_region))
        snip = " ".join(TAGS.sub(" ", NOTE_A.sub("", text2)).split())[:48]
        out.append((book, ch, "FIX", f"v2 starts: {snip!r}"))

    if not dry and edits:
        for start, end, repl in sorted(edits, key=lambda e: e[0], reverse=True):
            t = t[:start] + repl + t[end:]
        path.write_text(t, encoding="utf-8")
    return out


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--book", default=None, help="limit to one book code (e.g. exo)")
    args = p.parse_args(argv)
    dry = not args.apply

    tally = {"FIX": 0, "FLAG": 0, "SKIP": 0}
    flags = []
    for f in sorted(EPUB.glob("index_split_*.html")):
        for book, ch, status, detail in process_file(f, dry):
            if args.book and book != args.book:
                continue
            tally[status] = tally.get(status, 0) + 1
            if status in ("FIX",) and (args.book or tally["FIX"] <= 12):
                print(f"  FIX  {book} {ch}:1  ({detail})")
            if status == "FLAG":
                flags.append(f"{book} {ch} — {detail}")
    print(f"\n{'DRY-RUN' if dry else 'APPLIED'}: FIX={tally['FIX']} FLAG={tally['FLAG']} SKIP={tally['SKIP']}")
    if flags:
        print("FLAGGED (left untouched — review):")
        for fl in flags[:25]:
            print(f"  - {fl}")
        if len(flags) > 25:
            print(f"  … +{len(flags) - 25} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
