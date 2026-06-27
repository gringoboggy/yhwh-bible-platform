#!/usr/bin/env python3
"""Round-15 gate D6 — canon book-set + note-count cross-check (build-free, no rebuild).

TWO independent canon determinations feed one EPUB and the front-matter "It spans N books"
claim, through mirror loaders with NO source-anchored cross-check:
  - ``scripts.epub_utils.load_canons``  (the BUILD path — which books physically ship)
  - ``scripts.core.matrix._load_canons`` (the matrix/UI path — the printed count + note totals)
  - ``compute_matrix().edition_canon_books`` (cached/indexed) + ``_compute_matrix_via_file_walk``
    (the Δ.4 reference) — BOTH compute the per-edition book set via the SHARED
    ``_canon_books_for_edition``, so the existing Δ.4 equivalence pin is VACUOUS for the book set.

This gate adds the missing source anchor: it recomputes each edition's canon book set DIRECTLY
from a fresh ``yaml.safe_load`` of ``content/canons.yaml`` (inline — NOT via the shared helper)
and asserts every loader + both matrix paths agree with it. A divergence means one canon
determination disagrees with the source → a reader gets a different book set than the front-matter
/ ToC claims.

Checks (all build-free):
  1. CANON AGREEMENT — for every edition, the source-anchored book set (fresh yaml) ==
     ``compute_matrix`` == ``_compute_matrix_via_file_walk`` == ``epub_utils.load_canons`` ==
     ``matrix._load_canons``. Any pairwise divergence FAILs (de-vacuums Δ.4).
  2. BOOK RESOLVABILITY — every book in an edition's canon is a known book code
     (``config.load_books``). A canon listing a typo'd / non-existent book FAILs.
  3. NOTE-COUNT CONSISTENCY — for every edition, ``resolved_note_counts`` is internally
     consistent (total == Σ per_book == Σ per_category == Σ per_kind) and every per_book book is
     inside the edition canon. A double-count / miss / out-of-canon leak FAILs.

``--selftest`` proves the comparison logic is non-tautological. Exit 0 = clean; 1 = FAIL; 2 = usage.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


@dataclass
class CanonResult:
    fails: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    @property
    def green(self) -> bool:
        return not self.fails


def _canon_books_inline(canons: dict, edition: dict) -> set[str]:
    """Source-anchored book set for an edition — the SAME contract as
    ``matrix._canon_books_for_edition`` but recomputed INLINE so the gate is an independent
    witness (a regression in the shared helper cannot hide here)."""
    canon_id = edition.get("canon")
    if not canon_id:
        return set()
    return set((canons.get(canon_id) or {}).get("books") or [])


def compare_canon_sources(sources: dict[str, dict[str, set[str]]]) -> list[str]:
    """Pure detector (selftested). ``sources`` = {source_name: {edition_id: book_set}}.
    FAIL on any edition where two sources disagree, naming the sources + the symmetric diff."""
    fails: list[str] = []
    all_eds = sorted({ed for m in sources.values() for ed in m})
    names = sorted(sources)
    ref_name = names[0]
    for ed in all_eds:
        ref = sources[ref_name].get(ed, set())
        for other in names[1:]:
            cur = sources[other].get(ed, set())
            if cur != ref:
                missing = sorted(ref - cur)
                extra = sorted(cur - ref)
                fails.append(
                    f"{ed}: canon book set diverges {ref_name} vs {other} "
                    f"(only-in-{ref_name}={missing[:6]} only-in-{other}={extra[:6]})"
                )
    return fails


def _check_note_counts(editions: dict) -> tuple[list[str], int]:
    from scripts.core import matrix as matrix_mod
    from scripts.core.edition_stats import resolved_note_counts

    fails: list[str] = []
    grand = 0
    canon = matrix_mod.compute_matrix().edition_canon_books
    for eid, ed in editions.items():
        rc = resolved_note_counts(ed)
        total = rc["total"]
        grand += total
        for label, sub in (
            ("per_book", rc["per_book"]),
            ("per_category", rc["per_category"]),
            ("per_kind", rc["per_kind"]),
        ):
            s = sum(sub.values())
            if s != total:
                fails.append(f"{eid}: resolved_note_counts total {total} != Σ {label} {s}")
        out_of_canon = sorted(set(rc["per_book"]) - (canon.get(eid) or set()))
        if out_of_canon:
            fails.append(
                f"{eid}: per_book has {len(out_of_canon)} book(s) outside the edition canon: {out_of_canon[:6]}"
            )
    return fails, grand


def audit() -> CanonResult:
    res = CanonResult()
    from scripts.core import config
    from scripts.core import matrix as matrix_mod
    from scripts.epub_utils import load_canons as epub_load_canons

    editions = config.editions_by_id()
    known_books = {b["code"] if isinstance(b, dict) else b for b in config.load_books()}

    # Fresh, independent source read (bypasses every cached loader + the shared helper).
    import yaml

    raw = yaml.safe_load((REPO / "content" / "canons.yaml").read_text(encoding="utf-8")) or {}
    canons_src = raw.get("canons", {}) or {}

    matrix_mod.compute_matrix.cache_clear()
    m_indexed = matrix_mod.compute_matrix()
    m_walk = matrix_mod._compute_matrix_via_file_walk()
    canons_matrix = matrix_mod._load_canons()
    canons_epub = epub_load_canons()

    sources = {
        "source_yaml": {eid: _canon_books_inline(canons_src, ed) for eid, ed in editions.items()},
        "compute_matrix": dict(m_indexed.edition_canon_books),
        "file_walk": dict(m_walk.edition_canon_books),
        "epub_utils": {eid: _canon_books_inline(canons_epub, ed) for eid, ed in editions.items()},
        "matrix_loader": {eid: _canon_books_inline(canons_matrix, ed) for eid, ed in editions.items()},
    }
    res.fails.extend(compare_canon_sources(sources))

    # Check 2 — every canon book is a known book code.
    for eid, books in sources["source_yaml"].items():
        unknown = sorted(books - known_books)
        if unknown:
            res.fails.append(f"{eid}: canon lists {len(unknown)} unknown book code(s): {unknown[:6]}")

    # Check 3 — note-count internal consistency + in-canon.
    note_fails, grand = _check_note_counts(editions)
    res.fails.extend(note_fails)

    res.stats = {
        "editions": len(editions),
        "canon_sources_compared": len(sources),
        "known_books": len(known_books),
        "total_notes_all_editions": grand,
    }
    return res


def _selftest() -> int:
    ok = True
    agree = {
        "a": {"ethiopian": {"gen", "exo"}, "catholic": {"gen"}},
        "b": {"ethiopian": {"gen", "exo"}, "catholic": {"gen"}},
        "c": {"ethiopian": {"gen", "exo"}, "catholic": {"gen"}},
    }
    if compare_canon_sources(agree):
        print("  ✗ selftest: agreeing sources produced divergence FAILs")
        ok = False
    diverge = {
        "a": {"ethiopian": {"gen", "exo"}},
        "b": {"ethiopian": {"gen"}},  # missing exo
    }
    f = compare_canon_sources(diverge)
    if not any("diverges" in m and "exo" in m for m in f):
        print("  ✗ selftest: a canon book-set divergence was NOT flagged (tautological gate!)")
        ok = False
    print("  ✓ D6 canon-bookcount-gate selftest passed" if ok else "  selftest FAILED")
    return 0 if ok else 1


def _print(res: CanonResult, max_show: int) -> None:
    s = res.stats
    status = "PASS" if res.green else "FAIL"
    print(f"\n=== D6 canon book-set + note-count cross-check {status} ===")
    if s:
        print(
            f"  editions={s['editions']} canon_sources={s['canon_sources_compared']} "
            f"known_books={s['known_books']} total_notes={s['total_notes_all_editions']}"
        )
    for f in res.fails[:max_show]:
        print("  ✗", f)
    if len(res.fails) > max_show:
        print(f"  ✗ … +{len(res.fails) - max_show} more FAIL(s)")


def _arg(argv: list[str], flag: str, default: str | None = None) -> str | None:
    return argv[argv.index(flag) + 1] if flag in argv else default


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    max_show = int(_arg(argv, "--max-show", "50"))
    json_out = _arg(argv, "--json")
    res = audit()
    _print(res, max_show)
    if json_out:
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump({"green": res.green, "stats": res.stats, "fails": res.fails, "warns": res.warns}, fh, indent=1)
        print(f"\nwrote {json_out}")
    verdict = "cross-check-clean" if res.green else "DIVERGE"
    print(f"\n{'PASS' if res.green else 'FAIL'}: canon book-set + note counts {verdict}")
    return 1 if not res.green else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
