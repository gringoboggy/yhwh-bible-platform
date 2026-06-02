"""at_scale_base.py — shared helpers for the at-scale candidate-generation drivers.

Extracted (mint-7 D1) from the 10 ``run_*_at_scale.py`` drivers + ``prospect.py``
(which each defined a byte-identical ``candidate_to_dict``), from ``detectors.py`` /
``run_hebrew_at_scale`` / ``run_greek_at_scale`` (which each defined the same 27-code
``NT_BOOKS`` set), and from the ANSI color constants copy-pasted across all of them.

``append_candidates`` IS here (mint-10): the 4 accumulator drivers (xref / naves /
torrey / ethiopian) held a byte-identical append-with-seen-dedup ``write_queue``, and
the 4 kind-replace drivers (hebrew / greek / ai_xrefs / ai_notes) each PURGED their
own-kind candidates before re-adding them — silently resetting a prior ``promoted``
status back to ``pending``. All 8 now delegate to ``append_candidates`` (status-
preserving dedup on ``(verse, kind, draft_body)``). ``run_kenyon`` keeps its own
full-reindex write. ``iter_target_verses`` / ``resolve_books`` ARE here (mint-8): both
AI drivers held byte-identical copies whose copy-then-diverge history caused the mint-7
B1 ``ch_count`` bug; ``resolve_books`` also normalizes an explicit ``--books`` arg to
canonical book codes (mint-10). This module is a dependency-free leaf: it imports
nothing from ``scripts`` at module top (the shared helpers lazy-import ``translations`` /
``config`` / ``sources`` / ``notes_io`` inside the function body), so every driver +
``detectors.py`` can import it without a circular-import hazard.
"""

from __future__ import annotations

from pathlib import Path

# ANSI color codes for the drivers' progress output.
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

# The 27 canonical New Testament book codes (books.yaml codes). The Hebrew word
# detector skips these (lexicon is OT-only); the Greek detector skips everything
# NOT in this set. Canonical codes throughout (phi/jam, never php/jas).
NT_BOOKS = frozenset(
    {
        "mat",
        "mrk",
        "luk",
        "jhn",
        "act",
        "rom",
        "1co",
        "2co",
        "gal",
        "eph",
        "phi",
        "col",
        "1th",
        "2th",
        "1ti",
        "2ti",
        "tit",
        "phm",
        "heb",
        "jam",
        "1pe",
        "2pe",
        "1jn",
        "2jn",
        "3jn",
        "jud",
        "rev",
    }
)


def iter_target_verses(books: list[str], max_verses: int):
    """Yield ``(book, chapter, verse, verse_text)`` tuples in canonical book
    order, capped at ``max_verses`` total. Skips books that aren't present in
    the KJV translation data.

    Shared by both AI drivers (``run_ai_notes_at_scale`` /
    ``run_ai_xrefs_at_scale``); they were byte-identical copies whose
    copy-then-diverge history produced the mint-7 B1 ``ch_count`` bug, so the
    single implementation lives here now (mint-8). ``translations`` / ``config``
    are imported lazily inside the function to keep this module the dependency-
    free leaf its module docstring promises (no top-level ``scripts`` import →
    no circular-import hazard for ``detectors.py`` et al.)."""
    from scripts.core import config, translations

    yielded = 0
    for book in books:
        if yielded >= max_verses:
            return
        if not translations.has_book("kjv", book):
            continue
        try:
            book_meta = config.get_book(book)
            n_chapters = (
                book_meta.get("ch_count", 50) if book_meta else 50
            )  # mint-7 B1: books.yaml key is ch_count (was "chapters" → always 50)
        except KeyError:
            n_chapters = 50
        for chapter in range(1, n_chapters + 1):
            if yielded >= max_verses:
                return
            verses = translations.get_chapter("kjv", book, chapter)
            if not verses:
                continue
            for verse_num, verse_text in verses:
                if yielded >= max_verses:
                    return
                yield (book, chapter, verse_num, verse_text)
                yielded += 1


def resolve_books(books_arg: str | None) -> list[str]:
    """Resolve the ``--books`` CLI argument to a list of canonical book codes.

    With an explicit arg, splits on commas. Otherwise returns every KJV book
    in canonical order (from ``books.yaml``) that has a translation store on
    disk. Shared by both AI drivers (mint-8 dedup). Lazy ``config`` import keeps
    this module a dependency-free leaf."""
    if books_arg:
        # mint-10: normalize explicit --books tokens to canonical codes (php→phi,
        # jas→jam, …) so a legacy alias on the CLI doesn't write candidates to a
        # non-existent book file. The default branch already returns canonical codes.
        from scripts.core.sources import _normalize_book_code

        return [_normalize_book_code(b.strip()) for b in books_arg.split(",") if b.strip()]
    from scripts.core import config

    # Default: every KJV book in canonical order from books.yaml.
    repo_root = Path(__file__).resolve().parent.parent.parent
    canonical = list(config.books_by_code().keys())
    kjv_dir = repo_root / "content" / "translations" / "kjv"
    available = {p.stem for p in kjv_dir.glob("*.py")}
    return [b for b in canonical if b in available]


def candidate_to_dict(c, idx: int) -> dict:
    """Serialize a detector ``Candidate`` into the ``prospect.py`` JSON shape so
    ``promote.py`` / ``batch_promote_xrefs.py`` consume it unchanged. (mint-7 D1:
    was copy-pasted identically across all 10 at-scale drivers + ``prospect.py``.)"""
    return {
        "id": f"{c.book}-{c.chapter}-{c.verse}-{idx:03d}",
        "verse": c.verse,
        "kind": c.kind,
        "anchor": c.anchor,
        "confidence": round(c.confidence, 3),
        "source_name": c.source_name,
        "source_attribution": c.source_attribution,
        "draft_title": c.draft_title,
        "draft_label": c.draft_label,
        "draft_body": c.draft_body,
        "detector": c.detector,
        "reviewer_notes": c.reviewer_notes,
        "status": "pending",
    }


def append_candidates(out_path: Path, book: str, chapter: int, candidates: list) -> Path | None:
    """Append detector ``candidates`` to a per-chapter candidates JSON,
    preserving every existing entry AND its ``status`` (so a prior
    ``promoted`` is never reset to ``pending``). Dedups on
    ``(verse, kind, draft_body)`` against both the existing file and within
    this run; new entries get fresh ids continuing past the existing tail.
    Returns ``out_path`` on a write, or ``None`` when there is nothing new.

    The single write path for the accumulator drivers (xref / naves / torrey /
    ethiopian) AND the kind-replace drivers (hebrew / greek / ai_xrefs /
    ai_notes), which previously purged their own kind before re-adding it and
    so reset promotion status (mint-10). ``run_kenyon`` keeps its own
    full-reindex write. ``json`` / ``datetime`` are stdlib; ``atomic_write`` is
    lazy-imported to keep this module a dependency-free leaf at import time.
    """
    import json
    from datetime import datetime, timezone

    from scripts.core.notes_io import atomic_write

    if not candidates:
        return None
    out_path.parent.mkdir(parents=True, exist_ok=True)

    existing: list[dict] = []
    if out_path.is_file():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8")).get("candidates", [])
        except (json.JSONDecodeError, OSError):
            existing = []

    # Dedup against existing + within-run on (verse, kind, draft_body); ids
    # continue past the existing tail so the chapter-wide NNN suffix stays unique.
    seen = {(c.get("verse"), c.get("kind"), c.get("draft_body")) for c in existing}
    new_dicts: list[dict] = []
    next_idx = len(existing) + 1
    for c in candidates:
        d = candidate_to_dict(c, next_idx)
        key = (d["verse"], d["kind"], d["draft_body"])
        if key in seen:
            continue
        seen.add(key)
        new_dicts.append(d)
        next_idx += 1
    if not new_dicts:
        return None  # idempotent: nothing new to add
    payload = {
        "book": book,
        "chapter": chapter,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_candidates": len(existing) + len(new_dicts),
        "candidates": existing + new_dicts,
    }
    atomic_write(out_path, json.dumps(payload, indent=2, ensure_ascii=False))
    return out_path
