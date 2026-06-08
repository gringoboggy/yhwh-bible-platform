#!/usr/bin/env python3
"""One-shot re-ingest of the ``topic-torrey`` bodies corrupted by two junk "topics"
the CCEL parser admitted — byte-minimal **lockstep** in the SOURCE store
(``content/notes/*.py``) and the baked BASE (``epub_working/index_split_*.html``),
plus a regenerate of ``content/sources/torrey_topical.json`` so the cache stays
consistent with the fixed extractor.

Defects #3 + #5 of the auto-note re-ingest
(``docs/superpowers/notes/2026-06-06-auto-note-reingest-plan.md`` §3/§5). ★The audit
filed #5 under topic-nave, but the live store shows it is entirely topic-TORREY — all
87 "…for his service against." description bodies and all 596 "appears under: BookName
N:N N:N …" ref-dump bodies are topic-torrey (676 union); topic-nave is clean. So #3
and #5 are ONE defect with ONE root cause.

Root cause + permanent fix
--------------------------
``scripts/extract_torrey_ccel.py::parse_text`` admitted exactly two non-topics as
topic headings (verified: the only Torrey topics ending in ``.`` or containing a
``\\d+:\\d+`` run):
  * ``"The king of Babylon … for his service against."`` — a sentence-case sub-entry
    DESCRIPTION inside the Tyre prophecies block (its ref ``Eze 29:18-20`` is the next
    line); and
  * ``"Zechariah 1:1  1:7 …"`` — a wrapped-citation dump expand_refs can't split.
Each STOLE the ref block that followed it from the real preceding topic. The fix adds
a discriminator that rejects a heading ending in ``.`` or carrying a ``\\d+:\\d+`` run
while KEEPING ``current`` — so those refs flow back to the real topic (Tyre, …). This
preserves n_refs exactly (55,566) and drops only the 2 junk keys (630→628 topics).

Method (recompute, not blind-strip)
-----------------------------------
1. Regenerate ``torrey_topical.json`` via the fixed extractor (``T.build``).
2. Recompute every ``topic-torrey`` body with ``TorreyTopicalDetector`` against the
   new index (the detector reproduces all 21,764 CURRENT bodies from the CURRENT
   index exactly, so the new bodies are the exactly-correct re-ingest).
3. For each changed verse, exact-string-replace its old body → new body in source +
   base (lockstep). 676 bodies change; 0 verses lose all topics (no note dropped); 0
   residual junk. Post-check: every store body == detector(new index).

Usage
-----
    python3 scripts/_reingest_torrey_topics.py            # dry-run (no writes)
    python3 scripts/_reingest_torrey_topics.py --write    # apply
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.extract_torrey_ccel as T  # noqa: E402
from scripts.core.detectors import TorreyTopicalDetector  # noqa: E402
from scripts.core.sources_lexicon import TorreyTopical  # noqa: E402
from scripts.core import notes_io  # noqa: E402  — crash-safe canonical writes

NOTES_DIR = REPO / "content" / "notes"
BASE_DIR = REPO / "epub_working"
TORREY_JSON = REPO / "content" / "sources" / "torrey_topical.json"
_BOOKRUN = re.compile(r"[A-Z][a-z]+ \d+:\d+\s+\d+:\d+")  # a ref-dump signature


def _store_torrey() -> list[tuple[str, int, int, str, str]]:
    """Every topic-torrey note: (book, ch, v, suffix, body)."""
    out: list[tuple[str, int, int, str, str]] = []
    for p in sorted(NOTES_DIR.glob("*.py")):
        if p.name == "__init__.py":
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "NOTES" for t in node.targets):
                for t in ast.literal_eval(node.value):
                    if len(t) >= 8 and t[4] == "topic-torrey":
                        out.append((p.stem, t[0], t[1], t[2], t[7]))
    return out


def _detector_for(index_path: Path) -> TorreyTopicalDetector:
    """A detector whose Torrey index is loaded fresh from ``index_path`` (bypasses the
    module-level cache so we can recompute against the just-regenerated json)."""
    det = TorreyTopicalDetector()
    fresh = TorreyTopical.__new__(TorreyTopical)
    import json

    data = json.loads(index_path.read_text(encoding="utf-8"))
    fresh._data = data
    fresh._topics = data.get("topics", {})
    fresh._verses = data.get("verses", {})
    det.torrey = fresh
    return det


def _recompute(det: TorreyTopicalDetector, book: str, ch: int, v: int) -> str | None:
    cands = det.detect(book, ch, v, "")
    return cands[0].draft_body if cands else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="apply (default: dry-run)")
    args = ap.parse_args(argv)

    store = _store_torrey()
    print(f"store topic-torrey notes: {len(store)}")

    # 1) sanity: the CURRENT index reproduces every CURRENT store body exactly.
    cur_det = _detector_for(TORREY_JSON)
    drift = [(b, c, v) for b, c, v, _s, body in store if _recompute(cur_det, b, c, v) != body]
    if drift:
        print(f"⚠ {len(drift)} store bodies do NOT match the current index (unexpected) — ABORT")
        for b, c, v in drift[:8]:
            print(f"    {b} {c}:{v}")
        return 2
    print("current index reproduces all store bodies ✓")

    # 2) regenerate the index with the fixed extractor (in dry-run, build in memory;
    #    on --write, write the json so the cache stays extractor-consistent).
    text = T.SOURCE_TXT.read_text(encoding="utf-8")
    new_idx = T._build_naves_indices(T.parse_text(text), source=T.TORREY_SOURCE_LABEL)
    old_idx_topics = TorreyTopical().n_topics
    removed = old_idx_topics - len(new_idx["topics"])
    print(f"topics: {old_idx_topics} → {len(new_idx['topics'])} (removed {removed})")

    # build a fresh detector over the NEW in-memory index
    det = TorreyTopicalDetector()
    fresh = TorreyTopical.__new__(TorreyTopical)
    fresh._data = new_idx
    fresh._topics = new_idx["topics"]
    fresh._verses = new_idx["verses"]
    det.torrey = fresh

    # 3) recompute → old→new map (changed only); flag any verse that loses all topics.
    mapping: dict[str, str] = {}
    changed = 0
    emptied: list[tuple[str, int, int, str]] = []
    for b, c, v, suf, old_body in store:
        nb = _recompute(det, b, c, v)
        if nb is None:
            emptied.append((b, c, v, suf))
            continue
        if nb != old_body:
            changed += 1
            mapping[old_body] = nb
    print(f"changed bodies: {changed}  ({len(mapping)} distinct old→new)")
    print(f"verses that would lose ALL topics (note dropped): {len(emptied)}")
    if emptied:
        print("⚠ note-dropping is out of scope for a body-only lockstep — ABORT")
        for b, c, v, suf in emptied[:10]:
            print(f"    {b} {c}:{v}{suf}")
        return 2

    # safety: every NEW body is junk-free and XHTML-trivial (the template adds no
    # metacharacters; topic labels are plain text).
    bad = [nb for nb in mapping.values() if _BOOKRUN.search(nb) or "service against." in nb or '"' in nb]
    if bad:
        print(f"⚠ {len(bad)} new bodies still carry junk / a double-quote — ABORT")
        for nb in bad[:5]:
            print(f"    {nb[:90]!r}")
        return 2

    src_texts = {p: p.read_text(encoding="utf-8") for p in sorted(NOTES_DIR.glob("*.py")) if p.name != "__init__.py"}
    base_texts = {p: p.read_text(encoding="utf-8") for p in sorted(BASE_DIR.glob("index_split_*.html"))}
    src_occ = {ob: sum(t.count(ob) for t in src_texts.values()) for ob in mapping}
    base_occ = {ob: sum(t.count(ob) for t in base_texts.values()) for ob in mapping}
    missing_src = [ob for ob, c in src_occ.items() if c == 0]
    if missing_src:
        print(f"⚠ {len(missing_src)} old bodies not found in source — ABORT")
        return 2
    base_miss = sum(1 for c in base_occ.values() if c == 0)
    print(
        f"source: all {len(mapping)} old bodies found ✓   base: {len(mapping) - base_miss} found / {base_miss} source-only"
    )

    if not args.write:
        print("\nDRY-RUN — no files written. Re-run with --write to apply.")
        return 0

    # write the regenerated index (canonical extractor write path keeps json↔extractor
    # consistent), then lockstep-replace the bodies.
    T.build(dry_run=False)
    bak = TORREY_JSON.with_suffix(TORREY_JSON.suffix + ".bak")
    if bak.exists():
        bak.unlink()

    sw = bw = brepl = 0
    for p, txt in src_texts.items():
        nt = txt
        for ob, nb in mapping.items():
            if ob in nt:
                nt = nt.replace(ob, nb)
        if nt != txt:
            notes_io.ensure_backup(p)
            notes_io.atomic_write(p, nt)
            sw += 1
    for p, txt in base_texts.items():
        nt = txt
        for ob, nb in mapping.items():
            cnt = nt.count(ob)
            if cnt:
                nt = nt.replace(ob, nb)
                brepl += cnt
        if nt != txt:
            notes_io.ensure_backup(p)
            notes_io.atomic_write(p, nt)
            bw += 1
    print(f"\nWROTE: index regenerated; src={sw} base={bw} ({brepl} occ).")

    # 4) post-check: every store body == detector(new index); 0 residual junk.
    post = _store_torrey()
    post_det = _detector_for(TORREY_JSON)
    mism = [(b, c, v) for b, c, v, _s, body in post if _recompute(post_det, b, c, v) != body]
    junk = [(b, c, v) for b, c, v, _s, body in post if _BOOKRUN.search(body) or "service against." in body]
    print(f"post-check: store↔index mismatches={len(mism)}  residual-junk bodies={len(junk)}")
    if mism or junk:
        print("⚠ POST-CHECK FAILED")
        return 2
    print("post-check ✓ store is fully consistent with the regenerated index; 0 junk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
