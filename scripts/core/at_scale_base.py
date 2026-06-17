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


class CandidateQueueCorruptError(RuntimeError):
    """Raised when a candidate JSON queue exists but cannot be parsed."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        super().__init__(f"candidate queue corrupt: {self.path}")


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


def emit_extent_ok(book: str, chapter: int, verse: int) -> bool:
    """A candidate at ``(book, chapter, verse)`` is emitted only when its coord
    is within the book's canonical extent — the ★BUGCLUSTER guard shared by the
    accumulator drivers that iterate an INGESTED corpus's own coordinates
    (xref / naves / torrey / kenyon / ethiopian). Was a byte-identical private
    copy in each driver (round-7 5.8 consolidation); each driver imports it
    ``as _emit_extent_ok`` so the ``mod._emit_extent_ok`` contract that
    ``tests/test_mint11_phase3.py`` exercises is preserved. Lazy import keeps
    this module the dependency-free leaf its docstring promises
    (``canonical_verse_counts`` imports ``manuscript_collation`` at top)."""
    from scripts.core.canonical_verse_counts import coord_in_canonical_extent

    return coord_in_canonical_extent(book, chapter, verse)


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
        except json.JSONDecodeError as exc:
            raise CandidateQueueCorruptError(out_path) from exc
        except OSError:
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


# ---------------------------------------------------------------------------
# Word-detector drivers (Hebrew / Greek) — shared core.
#
# ``run_hebrew_at_scale.py`` and ``run_greek_at_scale.py`` were ~95% clones:
# identical per-book chapter loop + ``main()`` differing only by the detector
# INSTANCE, the in/out-of-scope predicate (OT vs NT), and three label strings.
# Hoisted here (v0.1.0 STAGE A). The detector is passed as an INSTANCE so this
# leaf never imports ``detectors.py`` (preserving the no-circular-import
# contract); the thin CLI files construct the detector + supply the labels.


def run_word_detector_for_book(
    book: str,
    detector,
    *,
    in_scope: bool,
    out_of_scope_reason: str,
    min_confidence: float,
    candidates_dir: Path,
) -> dict:
    """Run a word ``detector`` (INSTANCE) over one KJV book, writing per-chapter
    candidate JSON via ``append_candidates``. Returns the same stats dict the
    Hebrew/Greek drivers returned. ``in_scope`` is whether THIS book is in the
    detector's language scope (Hebrew: OT only; Greek: NT only); out-of-scope or
    no-KJV-data books are reported skipped with the given reason. Lazy ``config``/
    ``translations`` import keeps this module a dependency-free leaf."""
    from scripts.core import config, translations

    if not in_scope:
        return {
            "book": book,
            "skipped": True,
            "reason": out_of_scope_reason,
            "chapters_processed": 0,
            "candidates_written": 0,
            "files_written": 0,
        }
    if not translations.has_book("kjv", book):
        return {
            "book": book,
            "skipped": True,
            "reason": "no KJV data",
            "chapters_processed": 0,
            "candidates_written": 0,
            "files_written": 0,
        }

    try:
        book_meta = config.get_book(book)
        n_chapters = book_meta.get("ch_count", 50) if book_meta else 50
    except KeyError:
        # Deuterocanonical / non-canonical books may exist in KJV data but not in
        # config — assume up to 50 chapters; get_chapter returns empty past the end.
        n_chapters = 50

    chapters_processed = 0
    candidates_written = 0
    files_written = 0
    for chapter in range(1, n_chapters + 1):
        verses = translations.get_chapter("kjv", book, chapter)
        if not verses:
            continue
        chapters_processed += 1
        chapter_candidates = []
        for verse_num, verse_text in verses:
            for c in detector.detect(book, chapter, verse_num, verse_text):
                if c.confidence >= min_confidence:
                    chapter_candidates.append(c)
        if chapter_candidates:
            out = append_candidates(candidates_dir / f"{book}_ch_{chapter:03d}.json", book, chapter, chapter_candidates)
            if out:
                files_written += 1
                candidates_written += len(chapter_candidates)
    return {
        "book": book,
        "skipped": False,
        "chapters_processed": chapters_processed,
        "candidates_written": candidates_written,
        "files_written": files_written,
    }


def run_word_detector_main(
    *,
    detector,
    detector_label: str,
    scope_label: str,
    skipped_scope_label: str,
    in_scope_predicate,
    out_of_scope_reason: str,
    candidates_dir: Path,
    repo_root: Path,
    argv: list[str] | None = None,
) -> int:
    """Parametrized ``main()`` for the Hebrew/Greek at-scale drivers. ``detector``
    is the constructed INSTANCE; ``scope_label`` is the script's own scope
    ("OT"/"NT") and ``skipped_scope_label`` the complement. Output is byte-identical
    to the pre-hoist drivers. ``_normalize_book_code`` is lazy-imported."""
    import argparse

    from scripts.core.sources import _normalize_book_code

    p = argparse.ArgumentParser(
        description=f"Run {detector_label} at scale via direct KJV iteration.",
    )
    p.add_argument("--books", help=f"comma-separated list of {scope_label} books (default: all)")
    p.add_argument("--min-confidence", type=float, default=0.7)
    args = p.parse_args(argv)

    if args.books:
        books = [_normalize_book_code(b.strip()) for b in args.books.split(",") if b.strip()]
    else:
        all_books = [Path(pth).stem for pth in (repo_root / "content/translations/kjv").glob("*.py")]
        books = sorted(b for b in all_books if in_scope_predicate(b))

    print(f"Running {detector_label} across {len(books)} {scope_label} books (min-conf={args.min_confidence})")
    print()

    total_chapters = 0
    total_candidates = 0
    total_files = 0
    skipped_count = 0
    for book in books:
        stats = run_word_detector_for_book(
            book,
            detector,
            in_scope=in_scope_predicate(book),
            out_of_scope_reason=out_of_scope_reason,
            min_confidence=args.min_confidence,
            candidates_dir=candidates_dir,
        )
        if stats.get("skipped"):
            skipped_count += 1
            print(f"  {DIM}-{RESET} {book:5s} skipped ({stats.get('reason', '?')})")
            continue
        if stats["candidates_written"]:
            print(
                f"  {GREEN}✓{RESET} {book:5s} "
                f"{stats['chapters_processed']:3d} chapters "
                f"→ {stats['candidates_written']:5d} candidates "
                f"({stats['files_written']} files)"
            )
        else:
            print(f"  {DIM}-{RESET} {book:5s} {stats['chapters_processed']:3d} chapters → 0 candidates")
        total_chapters += stats["chapters_processed"]
        total_candidates += stats["candidates_written"]
        total_files += stats["files_written"]

    print()
    print(
        f"TOTAL: {len(books) - skipped_count} books processed · "
        f"{total_chapters} chapters · "
        f"{total_candidates} candidates · {total_files} candidate files"
    )
    print(f"({skipped_count} books skipped — {skipped_scope_label} or no KJV data)")
    return 0


# ---------------------------------------------------------------------------
# AI drivers (note / xref) — shared core + CLI scaffolding.
#
# ``run_ai_notes_at_scale.py`` and ``run_ai_xrefs_at_scale.py`` were near-clones:
# an identical parallel-map aggregation core + a near-identical argparse parser +
# a near-identical cost-guarded ``main()``, differing only by the detector/client
# classes, the per-driver extra arg (``--tradition`` / ``--top-n``),
# ``COST_PER_VERSE`` (0.0020 / 0.0023), the ``--min-confidence`` default
# (0.65 / 0.7), and the ``--kind`` promote hint (comm-ai / xref-thematic). Hoisted
# here (v0.1.0 STAGE A). The thin CLIs supply the detector/client classes (so this
# leaf never imports ``detectors.py`` or the Anthropic clients) + the per-driver
# labels/callables.


def run_ai_detector(
    books: list[str],
    *,
    max_verses: int,
    detector_factory,
    candidates_dir: Path,
    workers: int = 1,
) -> dict:
    """Pure-function aggregation core shared by both AI drivers.
    ``detector_factory`` constructs the per-run detector INSTANCE (so this leaf
    never imports the detector/client classes). Gathers target verses up front,
    runs ``detector.detect`` per verse (optionally via ``parallel_map``, which
    preserves INPUT order → byte-identical to the serial path), groups by
    (book, chapter), and writes via the shared ``append_candidates``.

    Returns ``{verses_processed, candidates_written, files_written, per_book}``.
    Lazy ``parallel_map`` import keeps this module a dependency-free leaf."""
    from scripts.core.parallel import parallel_map

    detector = detector_factory()
    targets = list(iter_target_verses(books, max_verses))
    verses_processed = len(targets)

    def _work(t):
        book, chapter, verse_num, verse_text = t
        return (book, chapter, detector.detect(book, chapter, verse_num, verse_text))

    if workers and workers > 1:
        processed = parallel_map(_work, targets, workers=workers)
    else:
        processed = [_work(t) for t in targets]

    by_chapter: dict[tuple[str, int], list] = {}
    per_book: dict[str, dict] = {}
    for book, chapter, cands in processed:
        per_book.setdefault(book, {"verses": 0, "candidates": 0})
        per_book[book]["verses"] += 1
        if cands:
            by_chapter.setdefault((book, chapter), []).extend(cands)
            per_book[book]["candidates"] += len(cands)

    candidates_written = 0
    files_written = 0
    for (book, chapter), cands in sorted(by_chapter.items()):
        out = append_candidates(candidates_dir / f"{book}_ch_{chapter:03d}.json", book, chapter, cands)
        if out:
            files_written += 1
            candidates_written += len(cands)

    return {
        "verses_processed": verses_processed,
        "candidates_written": candidates_written,
        "files_written": files_written,
        "per_book": per_book,
    }


def build_ai_arg_parser(
    *,
    detector_label: str,
    min_confidence_default: float,
    confirm_threshold: int,
    model_default: str,
    extra_args: tuple = (),
):
    """Build the shared argparse parser for an AI driver. ``extra_args`` is a
    tuple of ``(flags_tuple, kwargs_dict)`` for the per-driver arg
    (``--top-n`` / ``--tradition``), inserted between ``--min-confidence`` and
    ``--model``."""
    import argparse

    p = argparse.ArgumentParser(
        description=(f"Run {detector_label} at scale via direct KJV iteration with cost guards."),
    )
    p.add_argument(
        "--books",
        help=("comma-separated list of canonical 3-letter book codes (default: all books with KJV data)"),
    )
    p.add_argument(
        "--max-verses",
        type=int,
        default=100,
        help=(
            f"hard cap on API calls per run (default 100). The driver refuses to "
            f"run more than {confirm_threshold} verses without --confirm-cost."
        ),
    )
    p.add_argument(
        "--min-confidence",
        type=float,
        default=min_confidence_default,
        help=(f"drop AI candidates below this confidence (default {min_confidence_default})"),
    )
    for flags, kwargs in extra_args:
        p.add_argument(*flags, **kwargs)
    p.add_argument(
        "--model",
        default=model_default,
        help=(f"Anthropic model id (default: {model_default})"),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help=("print projected verse count and cost, then exit. No API calls made."),
    )
    p.add_argument(
        "--confirm-cost",
        action="store_true",
        help=(f"explicit acknowledgement of cost; required when --max-verses > {confirm_threshold}."),
    )
    p.add_argument(
        "--workers",
        type=int,
        default=1,
        help=(
            "parallel API workers (default 1 = serial). The calls are I/O-bound; "
            "4-8 gives a large wall-clock speedup. Keep modest to respect rate "
            "limits (the SDK retries 429s)."
        ),
    )
    p.add_argument(
        "--cache",
        default=None,
        help=(
            "path to a SQLite response cache. Re-runs skip verses whose text "
            "(and model/prompt) are unchanged, paying only for what changed."
        ),
    )
    return p


def run_ai_driver_main(
    args,
    *,
    cost_per_verse: float,
    confirm_threshold: int,
    candidates_dir: Path,
    kind_hint: str,
    make_client,
    make_detector_factory,
    format_target_line,
) -> int:
    """Shared cost-guarded ``main()`` body for the AI drivers. ``make_client(model,
    cache)`` constructs the Anthropic client (may raise ``SourceMissingError``);
    ``make_detector_factory(client, args)`` returns a zero-arg detector factory;
    ``format_target_line(args, n_verses, n_books)`` returns the driver-specific
    "Target: …" line. Aggregation is delegated to ``run_ai_detector``. Lazy imports
    keep this module a dependency-free leaf."""
    from scripts.core.sources import SourceMissingError
    from scripts.core.work_cache import WorkCache

    books = resolve_books(args.books)

    # Pre-count target verses so the cost estimate is accurate (and the
    # confirm-cost guard fires before any API call).
    n_verses = sum(1 for _ in iter_target_verses(books, args.max_verses))
    cost_usd = n_verses * cost_per_verse

    print(format_target_line(args, n_verses, len(books)))
    print(f"Projected cost: ~${cost_usd:.2f} USD (@ ${cost_per_verse:.5f}/verse).")
    print()

    if args.dry_run:
        print(f"{DIM}--dry-run: nothing written; no API calls made.{RESET}")
        return 0

    if args.max_verses > confirm_threshold and not args.confirm_cost:
        print(
            f"{RED}REFUSING:{RESET} --max-verses ({args.max_verses}) "
            f"exceeds the {confirm_threshold}-verse confirm-cost threshold."
        )
        print(f"  Re-run with {YELLOW}--confirm-cost{RESET} to proceed, or lower --max-verses.")
        print(f"  Projected spend: ${cost_usd:.2f} USD.")
        return 1

    # Construct the client once (validates the SDK + key); fail cleanly if the
    # source is missing. Opt-in response cache is shared across all workers.
    cache = WorkCache(args.cache) if args.cache else None
    try:
        client = make_client(args.model, cache)
    except SourceMissingError as e:
        print(f"{RED}REFUSING:{RESET} {e}")
        return 1

    detector_factory = make_detector_factory(client, args)
    stats = run_ai_detector(
        books,
        max_verses=args.max_verses,
        detector_factory=detector_factory,
        candidates_dir=candidates_dir,
        workers=args.workers,
    )

    print()
    for book in sorted(stats["per_book"].keys()):
        s = stats["per_book"][book]
        marker = GREEN + "✓" + RESET if s["candidates"] else DIM + "-" + RESET
        print(f"  {marker} {book:5s} {s['verses']:4d} verses → {s['candidates']:3d} candidates")

    print()
    print(
        f"TOTAL: {stats['verses_processed']} verses processed · "
        f"{stats['candidates_written']} candidates · "
        f"{stats['files_written']} candidate files updated"
    )
    print(f"Files written under: {candidates_dir}")
    print()
    print(f"{DIM}Next: python3 scripts/batch_promote_xrefs.py --kind {kind_hint}{RESET}")
    return 0
