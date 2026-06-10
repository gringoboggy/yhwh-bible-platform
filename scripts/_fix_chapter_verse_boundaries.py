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
verse-2's opening words inside the merged text. CONFIDENCE-GATED: split only when
the anchor phrase occurs exactly once; otherwise the chapter is FLAGGED and left
untouched (never guess on scripture). Idempotent. Run --dry-run first.

round-7 P3 extension (2026-06-10, design: docs/superpowers/notes/
2026-06-10-verse-boundary-residual-design.md): the 2026-06-06 pass fixed 161
chapters but FLAGGED 116 — its anchor came from the on-disk KJV store pushed
through a KJV→modern word map, which diverges from the base's actual WEB text
(archaic phrasing / genealogy spellings / no-KJV apocrypha). The fixer now
anchors on the REAL WEB text first: ``content/sources/web_boundary_anchors.json``
(eng-web v1+v2 for every affected chapter, PD) — a same-translation match, so
``_SUBS``/``LEADING`` are bypassed for fixture anchors. The KJV chain stays as
the fallback for any site outside the fixture. Two more residual-class fixes:
typographic apostrophes normalize to ascii on BOTH sides of the match (1 char →
1 char, offsets preserved), and a chapter with no verse-3 anchor (psa 117, the
two-verse psalm) bounds its merged region at the verse paragraph's ``</p>``
instead of being skipped.

    py -3 -m scripts._fix_chapter_verse_boundaries --dry-run [--book exo]
    py -3 -m scripts._fix_chapter_verse_boundaries --apply
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EPUB = REPO / "epub_working"
FIXTURE = REPO / "content" / "sources" / "web_boundary_anchors.json"

# Typographic → ascii (1 char → 1 char, so _visible_map offsets stay valid).
_TYPO = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})

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


@lru_cache(maxsize=1)
def _web_anchors() -> dict:
    """The round-7 WEB ground-truth fixture: {"<book>-<ch>": {"v1":…, "v2":…}}.
    Empty dict when the fixture file is absent (the KJV chain then applies)."""
    if not FIXTURE.is_file():
        return {}
    return json.loads(FIXTURE.read_text(encoding="utf-8")).get("anchors", {})


def _anchor_words_raw(text: str, n: int = 6) -> list[str]:
    """Fixture-anchor words: SAME-translation match, so no KJV→modern _SUBS and
    no leading-conjunction drop — the WEB fixture text should appear near-
    verbatim in the merged run. Typographic apostrophes normalized to ascii."""
    t = re.sub(r"\[[^\]]*\]", "", text).translate(_TYPO).replace("¶", "").strip()
    return [w.lower() for w in re.findall(r"[A-Za-z']+", t)[:n]]


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
        # round-7: typographic apostrophes/quotes → ascii (1:1) so a fixture
        # anchor like "yahweh's" matches the base's "Yahweh’s"; offsets hold.
        vis.append(html[i].lower().translate(_TYPO))
        offs.append(i)
        i += 1
    return "".join(vis), offs


def _find_split(merged: str, words: list[str], max_len: int = 4) -> int | None:
    if len(words) < 2:
        return None
    vis, offs = _visible_map(merged)
    # Try the verse-2 opening anchor at decreasing length (most precise first);
    # take the FIRST length that occurs EXACTLY ONCE. Each length keeps the
    # uniqueness gate, so a shorter anchor is accepted only when it is itself
    # unambiguous in this chapter's merged text — recall up, no guessing.
    # round-7: words join on \W+ (not \s+) so punctuation inside the opener
    # ("Kenan, Mahalalel, Jared" / "nations! Extol") no longer defeats the
    # match; max_len is a parameter — same-translation fixture anchors are
    # near-verbatim, so a LONGER window only sharpens them (e.g. gen 2's
    # "on the seventh day" repeats; "…god finished" is unique at 6).
    for length in range(min(len(words), max_len), 1, -1):
        pat = re.compile(r"\b" + r"\W+".join(re.escape(w) for w in words[:length]) + r"\b")
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

        # round-7: TWO-STEP displacement (1ch 1, sir 18) — v2's gap is ALSO
        # notes-only and v1+v2(+v3) text sits merged under the v3 anchor.
        # Requires fixture v2 AND v3 ground truth; rebuilt as
        # [T1][N1][V2][T2][N2][V3][T3] (T3 may be legitimately empty — WEB
        # sir 18:3 is a blank verse). Confidence gates as in the single-step.
        fix2 = _web_anchors().get(f"{book}-{ch}")
        v3_probe = t.find(f'id="v-{book}-{ch}-3"', v2_end)
        if v3_probe >= 0 and fix2 and "v3" in fix2:
            v3_open_p = t.rfind("<a ", 0, v3_probe)
            notes2 = t[v2_end:v3_open_p]
            if not TAGS.sub("", NOTE_A.sub("", notes2)).strip():
                v3_close = t.find("</a>", v3_probe)
                v3_end = v3_close + 4
                v4 = t.find(f'id="v-{book}-{ch}-4"', v3_end)
                right = t.rfind("<a ", 0, v4) if v4 >= 0 else t.find("</p>", v3_end)
                if right > v3_end:
                    merged2 = t[v3_end:right]
                    w2 = _anchor_words_raw(fix2["v2"], n=14)
                    s2 = _find_split(merged2, w2, max_len=len(w2))
                    if s2 is None:
                        out.append((book, ch, "FLAG", f"two-step: v2 anchor not unique: {w2}"))
                        continue
                    if fix2["v3"]:
                        w3 = _anchor_words_raw(fix2["v3"], n=14)
                        s3 = _find_split(merged2, w3, max_len=len(w3))
                        if s3 is None or s3 <= s2:
                            out.append((book, ch, "FLAG", f"two-step: v3 anchor not unique/ordered: {w3}"))
                            continue
                    else:
                        s3 = len(merged2)  # WEB v3 is a blank verse — T3 stays empty
                    t1, t2_, t3_ = merged2[:s2], merged2[s2:s3], merged2[s3:]
                    if not TAGS.sub("", NOTE_A.sub("", t1)).strip():
                        out.append((book, ch, "FLAG", "two-step: split would leave v1 empty"))
                        continue
                    v2anchor = t[v2_open:v2_end]
                    v3anchor = t[v3_open_p:v3_end]
                    new_region = t1 + notes1 + v2anchor + t2_ + notes2 + v3anchor + t3_
                    edits.append((v1_end, right, new_region))
                    snip = " ".join(TAGS.sub(" ", NOTE_A.sub("", t2_)).split())[:48]
                    out.append((book, ch, "FIX", f"two-step; v2 starts: {snip!r}"))
                    continue

        v3 = v3_probe
        if v3 < 0:
            # round-7: a TWO-verse chapter (psa 117) has no v3 anchor — bound
            # the merged region at the verse paragraph's close instead.
            p_close = t.find("</p>", v2_end)
            if p_close < 0:
                out.append((book, ch, "SKIP", "no v3 anchor and no </p> bound"))
                continue
            v3_open = p_close
        else:
            v3_open = t.rfind("<a ", 0, v3)
        merged = t[v2_end:v3_open]

        # round-7: the WEB ground-truth fixture is the FIRST anchor source —
        # same-translation text, so no modernization map is needed and the
        # 2026-06-06 failure classes (archaic KJV phrasing / genealogy
        # spellings / no-KJV apocrypha) disappear. KJV chain = fallback.
        fix_rec = _web_anchors().get(f"{book}-{ch}")
        if fix_rec and fix_rec.get("bridge"):
            out.append((book, ch, "LEGIT-BRIDGE", f"WEB bridges vv {fix_rec['bridge']} — leave as-is"))
            continue
        if fix_rec and fix_rec.get("v2"):
            # n=14: psalms whose v2 RESTATES v1's opener (124/129 "let Israel
            # now say" pattern) need the window to reach past the shared text;
            # the uniqueness gate still rejects anything ambiguous.
            words = _anchor_words_raw(fix_rec["v2"], n=14)
            anchor_src = "web-fixture"
            max_len = len(words)  # same-translation: longer window = sharper
        else:
            verses, _ = _kjv(book)
            kjv_v2 = verses.get((int(ch), 2)) if verses else None
            if not kjv_v2:
                out.append((book, ch, "FLAG", "no KJV v2 to anchor on"))
                continue
            words = _anchor_words(kjv_v2)
            anchor_src = "kjv-chain"
            max_len = 4  # modernization noise grows with length (06-06 cap)
        rel = _find_split(merged, words, max_len=max_len)
        if rel is None:
            out.append((book, ch, "FLAG", f"ambiguous/absent anchor ({anchor_src}): {words}"))
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
    extra = "".join(f" {k}={v}" for k, v in sorted(tally.items()) if k not in ("FIX", "FLAG", "SKIP"))
    print(f"\n{'DRY-RUN' if dry else 'APPLIED'}: FIX={tally['FIX']} FLAG={tally['FLAG']} SKIP={tally['SKIP']}{extra}")
    if flags:
        print("FLAGGED (left untouched — review):")
        for fl in flags[:25]:
            print(f"  - {fl}")
        if len(flags) > 25:
            print(f"  … +{len(flags) - 25} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
