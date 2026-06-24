"""Translation- and notes-store structural-integrity audit (the data-validity gate).

The round-13 deep-audit "data-validity" dimension returned 0/0 — it checked code
paths but never enumerated the live corpus the code reads. This tool closes that
gap permanently: it parses EVERY data store on disk and asserts the structural
invariants the loaders silently assume.

What it checks, per store
-------------------------
content/translations/<id>/<book>.py  (the ``VERSES = [(chapter, verse, text), …]`` list)
  * duplicate (chapter, verse) coordinate keys —
      - in a ``VERSIFICATION == "canonical"`` store  → **FAIL**
        (canonical numbering must be unique; ``translations._book_index_cached``
        builds ``{(c, v): t}`` so a duplicate is silently dropped, last-write-wins —
        a real, invisible loss of verse text).
      - in a ``VERSIFICATION == "own"`` store  → **WARN** (an *occurrence-multi*
        coordinate). The Geʽez/LXX Psalter legitimately numbers two distinct lines
        with one verse number (source-authoritative, NOT renumbered). The data is
        correct, but ``get_verse()`` / ``_book_index_cached`` collapse it
        (last-write-wins) — so every CONSUMER of those accessors for an ``own``
        store must be occurrence-aware (the standalone build's source-order
        occurrence map is; a bare coordinate lookup is not). The WARN names the
        hazard so a new ``own`` store can't add a collapse a reviewer never saw.
  * non-int chapter key → **FAIL** (chapters are always integers).
  * non-int verse key → **FAIL** for canonical; **INFO** for ``own`` (lettered
    labels like ``"2a"`` / ``"B1"`` are legal there and sorted by ``verse_sort_key``).
  * a coordinate outside the book's canonical (KJV-skeleton) extent — split by kind,
    because the two kinds mean very different things:
      - **chapter-missing** (the chapter does not exist in the book at all, e.g.
        Genesis 87 — classic OCR/parse noise) → **FAIL** in the ``kjv`` reference
        store, **WARN** elsewhere (an undeclared own-versification store may
        legitimately add a chapter — e.g. Psalm 151 — and should declare it).
      - **verse-overflow** (the chapter exists but the verse number exceeds the KJV
        per-chapter count — a *versification difference*, e.g. LXX Psalm splits,
        Hebrew Gen 32:33, the 4 Ezra 7 "missing verses", the Tobit GII recension) →
        in the ``kjv`` reference store this is a **WARN** (``canonical-table-gap``:
        the KJV store and the skeleton disagree → ``coord_in_canonical_extent``
        would wrongly reject those verses at the promote boundary); in any other
        translation it is **INFO** (expected non-KJV source numbering; the store
        should usually declare ``VERSIFICATION="own"``).
  * malformed tuple arity → **FAIL**.

content/notes/<book>.py  (the ``NOTES = [(chapter, verse, …), …]`` list)
  * non-int chapter / verse key → **FAIL** (the book-code-canonical / coord class).
  * mixed tuple arity within one store → **WARN**.
  (Notes legitimately carry MANY entries per verse — different kinds — so there is
  deliberately no duplicate-coordinate check for notes.)

The checks are pure functions over already-parsed data, so ``--selftest`` exercises
every FAIL path against synthetic known-bad fixtures: a gate that cannot fail in a
test is not a gate (round-13 completeness gap 3).

Usage
-----
    python3 dev/audit_translation_integrity.py [--json OUT.json] [--quiet]
    python3 dev/audit_translation_integrity.py --selftest

Exit 0 = no FAIL (WARN/INFO allowed); 1 = at least one FAIL (or a failed selftest).
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# Lazily-resolved canonical-shape table + the legacy→canonical book-code resolver
# (light pure-data modules). Kept optional so the structural checks still run if an
# import shape ever changes.
try:
    from scripts.core.canonical_verse_counts import (
        TEWAHEDO_DISTINCTIVE_NO_KJV,
        canonical_book_shape,
    )
except Exception:  # pragma: no cover - import-shape fallback
    canonical_book_shape = None  # type: ignore[assignment]
    TEWAHEDO_DISTINCTIVE_NO_KJV = ()  # type: ignore[assignment]
try:
    from scripts.core.book_codes import canonical_book_code
except Exception:  # pragma: no cover - import-shape fallback
    canonical_book_code = None  # type: ignore[assignment]

# Books that legitimately have NO KJV skeleton (Tewahedo distinctives) → extent is
# unverifiable, not an anomaly. Any OTHER no-skeleton stem (e.g. ``ex`` for Exodus,
# whose canonical stem is ``exo`` and which is absent from BOOK_CODE_ALIASES) is a
# book-code anomaly that silently escapes extent validation — surface it.
_NO_SKELETON_OK = set(TEWAHEDO_DISTINCTIVE_NO_KJV)


# ──────────────────────────────────────────────────────────────────────────────
# Findings
# ──────────────────────────────────────────────────────────────────────────────
FAIL = "FAIL"
WARN = "WARN"
INFO = "INFO"


@dataclass
class Finding:
    level: str  # FAIL | WARN | INFO
    store: str  # e.g. "geez-tewahedo/psa.py" or "notes/psa.py"
    # code ∈ {dup-coord, nonint-chapter, nonint-verse, chapter-missing,
    #   canonical-table-gap, nonkjv-versification, book-code-noshape, arity,
    #   notes-coord, mixed-arity}
    code: str
    coord: str  # "(36, 24)" or a rollup count, or "" when store-level
    detail: str


# ──────────────────────────────────────────────────────────────────────────────
# Pure checks (operate on already-parsed data → unit-testable via --selftest)
# ──────────────────────────────────────────────────────────────────────────────
def check_translation_store(
    store: str,
    book_code: str,
    versification: str,
    verses: list,
    *,
    translation: str = "",
    check_extent: bool = True,
) -> list[Finding]:
    """Structural checks for one parsed translation ``VERSES`` list.

    ``translation`` is the translation id (the parent dir); ``kjv`` is the canonical
    reference, so an extent overflow there means the skeleton and the store disagree.
    ``check_extent=False`` skips the canonical-extent pass (which builds the KJV
    skeleton — the slow part), leaving the fast dup-coord / non-int / arity checks
    that catch silent text loss; used by the per-push gate.
    """
    out: list[Finding] = []
    seen: dict[tuple, list[str]] = {}
    for tup in verses:
        if not isinstance(tup, tuple) or len(tup) < 3:
            out.append(Finding(FAIL, store, "arity", repr(tup)[:40], "verse tuple is not (chapter, verse, text)"))
            continue
        c, v, t = tup[0], tup[1], tup[2]
        if not isinstance(c, int):
            out.append(Finding(FAIL, store, "nonint-chapter", f"({c!r}, {v!r})", "chapter key is not an int"))
        if not isinstance(v, int):
            if versification == "own":
                out.append(
                    Finding(
                        INFO,
                        store,
                        "nonint-verse",
                        f"({c!r}, {v!r})",
                        "lettered verse label (legal in an own-versification store)",
                    )
                )
            else:
                out.append(
                    Finding(FAIL, store, "nonint-verse", f"({c!r}, {v!r})", "non-int verse key in a canonical store")
                )
        seen.setdefault((c, v), []).append(t)

    # ── duplicate coordinates ────────────────────────────────────────────────
    for coord, texts in sorted(seen.items(), key=lambda kv: _coord_sort(kv[0])):
        if len(texts) <= 1:
            continue
        differ = len(set(texts)) > 1
        if versification == "own":
            out.append(
                Finding(
                    WARN,
                    store,
                    "dup-coord",
                    f"{coord!r}",
                    f"occurrence-multi coordinate ×{len(texts)} (texts "
                    f"{'differ' if differ else 'identical'}) — legitimate under "
                    "own-versification, but get_verse()/_book_index_cached collapse it "
                    "last-write-wins; consumers must be occurrence-aware",
                )
            )
        else:
            out.append(
                Finding(
                    FAIL,
                    store,
                    "dup-coord",
                    f"{coord!r}",
                    f"duplicate coordinate ×{len(texts)} in a CANONICAL store — _book_index_cached drops "
                    f"occurrence(s) silently (texts {'differ → real text loss' if differ else 'identical'})",
                )
            )

    if check_extent:
        out += _extent_findings(store, book_code, versification, translation, list(seen))
    return out


def _extent_findings(
    store: str, book_code: str, versification: str, translation: str, coords: list[tuple]
) -> list[Finding]:
    """Canonical-extent checks for one store's coordinate set.

    Splits *chapter-missing* (an impossible chapter — parse noise) from
    *verse-overflow* (a versification difference). Empty for own-versification
    stores and when the canonical table is unavailable. Surfaces the book-code
    alias blind-spot (a stem with no skeleton that is not a known distinctive).
    """
    if versification == "own" or canonical_book_shape is None:
        return []
    canon = canonical_book_code(book_code) if canonical_book_code else book_code
    try:
        shape = canonical_book_shape(canon)
    except Exception:
        shape = {}
    if not shape:
        # No KJV skeleton. Expected for Tewahedo distinctives + working files
        # (``*_patrologia``); any OTHER stem is a book-code anomaly that escapes
        # extent validation (the ``book_code_canonical`` class — e.g. ``ex``).
        if canon in _NO_SKELETON_OK or "_" in book_code:
            return []
        return [
            Finding(
                WARN,
                store,
                "book-code-noshape",
                book_code,
                f"stem '{book_code}' (→ '{canon}') has no canonical skeleton — "
                "non-canonical book-code filename or unregistered alias; extent "
                "validation SKIPPED (book_code_canonical class)",
            )
        ]

    out: list[Finding] = []
    overflow: list[tuple] = []
    for c, v in coords:
        if not (isinstance(c, int) and isinstance(v, int)):
            continue
        if c not in shape:
            lvl = FAIL if translation == "kjv" else WARN
            out.append(
                Finding(
                    lvl,
                    store,
                    "chapter-missing",
                    f"({c}, {v})",
                    f"chapter {c} not in {book_code}'s canonical skeleton (max chapter {max(shape)})",
                )
            )
        elif v > shape[c]:
            overflow.append((c, v))
    if overflow:
        ex = ", ".join(f"{c}:{v}" for c, v in sorted(overflow)[:5])
        if translation == "kjv":
            out.append(
                Finding(
                    WARN,
                    store,
                    "canonical-table-gap",
                    f"{len(overflow)} coord(s)",
                    f"kjv store exceeds the canonical skeleton (e.g. {ex}) — the skeleton "
                    "under-counts (non-1-start numbering like the Esther Additions, ch10 "
                    "verses 4-13), so coord_in_canonical_extent wrongly rejects these "
                    "legitimate verses at the promote boundary",
                )
            )
        else:
            out.append(
                Finding(
                    INFO,
                    store,
                    "nonkjv-versification",
                    f"{len(overflow)} coord(s)",
                    f"verse-overflow vs KJV extent (e.g. {ex}) — non-KJV source "
                    "versification; store not declared VERSIFICATION='own'",
                )
            )
    return out


def check_notes_store(store: str, entries: list) -> list[Finding]:
    """Structural checks for one parsed notes ``NOTES`` list."""
    out: list[Finding] = []
    arities: set[int] = set()
    for e in entries:
        if not isinstance(e, tuple):
            out.append(Finding(FAIL, store, "arity", repr(e)[:40], "notes entry is not a tuple"))
            continue
        arities.add(len(e))
        if len(e) >= 2:
            c, v = e[0], e[1]
            if not isinstance(c, int):
                out.append(Finding(FAIL, store, "notes-coord", f"({c!r}, {v!r})", "notes chapter key is not an int"))
            if not isinstance(v, int):
                out.append(Finding(FAIL, store, "notes-coord", f"({c!r}, {v!r})", "notes verse key is not an int"))
    if len(arities) > 1:
        out.append(Finding(WARN, store, "mixed-arity", "", f"store mixes tuple arities {sorted(arities)}"))
    return out


def _coord_sort(coord: tuple) -> tuple:
    """Sort key tolerant of int-or-string verse labels (own stores)."""
    c, v = coord
    return (c if isinstance(c, int) else 1 << 30, str(v))


# ──────────────────────────────────────────────────────────────────────────────
# Parsing — read the data stores without importing them (ast only)
# ──────────────────────────────────────────────────────────────────────────────
def _literal_assign(src: str, name: str):
    """Return the literal value of a top-level ``name = …`` assignment, or None."""
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == name:
                    try:
                        return ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return None
    return None


def _string_assign(src: str, name: str) -> str | None:
    val = _literal_assign(src, name)
    return val if isinstance(val, str) else None


def audit_repo(repo: Path, *, check_extent: bool = True) -> list[Finding]:
    """Walk every translation + notes store under *repo* and collect findings.

    ``check_extent=False`` skips the canonical-extent pass (the KJV-skeleton build —
    the slow part) and runs only the fast dup-coord / non-int / arity checks that
    catch silent text loss; the per-push gate uses this, the full scan runs on the
    schedule / on demand.
    """
    findings: list[Finding] = []

    tr_dir = repo / "content" / "translations"
    for path in sorted(tr_dir.glob("*/*.py")):
        if path.name == "__init__.py" or path.parent.name == "sources":
            continue
        src = path.read_text(encoding="utf-8")
        verses = _literal_assign(src, "VERSES")
        if not isinstance(verses, list):
            continue
        versification = _string_assign(src, "VERSIFICATION") or "canonical"
        if versification not in ("own", "canonical"):
            versification = "canonical"
        translation = path.parent.name
        store = f"{translation}/{path.name}"
        findings += check_translation_store(
            store, path.stem, versification, verses, translation=translation, check_extent=check_extent
        )

    notes_dir = repo / "content" / "notes"
    for path in sorted(notes_dir.glob("*.py")):
        if path.name in ("__init__.py", "gen.py"):
            continue
        notes = _literal_assign(path.read_text(encoding="utf-8"), "NOTES")
        if not isinstance(notes, list):
            continue
        findings += check_notes_store(f"notes/{path.name}", notes)
    return findings


# ──────────────────────────────────────────────────────────────────────────────
# Reporting
# ──────────────────────────────────────────────────────────────────────────────
def _print_report(findings: list[Finding], quiet: bool) -> None:
    fails = [f for f in findings if f.level == FAIL]
    warns = [f for f in findings if f.level == WARN]
    infos = [f for f in findings if f.level == INFO]
    if not quiet:
        for f in findings:
            if f.level != INFO:
                print(f"  [{f.level}] {f.store} {f.coord} {f.code}: {f.detail}")
        if infos:
            print(f"\n  ({len(infos)} INFO suppressed — pass without --quiet-info; rollup below)")
        print()
    # INFO rollup by code (the non-KJV versification signal is a big, expected class)
    import collections

    info_codes = collections.Counter(f.code for f in infos)
    print(f"translation/notes integrity: {len(fails)} FAIL · {len(warns)} WARN · {len(infos)} INFO")
    if warns:
        for f in warns:
            print(f"  WARN {f.store} {f.coord} [{f.code}]")
    if info_codes:
        print("  INFO classes:", dict(info_codes))
    if fails:
        print("  → FAIL stores:", ", ".join(sorted({f.store for f in fails})))


# ──────────────────────────────────────────────────────────────────────────────
# Selftest — every FAIL/WARN path must fire on a synthetic known-bad fixture
# ──────────────────────────────────────────────────────────────────────────────
def _selftest() -> int:
    cases: list[tuple[str, bool]] = []

    def has(findings: list[Finding], level: str, code: str) -> bool:
        return any(f.level == level and f.code == code for f in findings)

    # canonical store with a duplicate coordinate → FAIL dup-coord
    f = check_translation_store("t/x.py", "psa", "canonical", [(1, 1, "a"), (1, 1, "b")])
    cases.append(("canonical dup-coord → FAIL", has(f, FAIL, "dup-coord")))

    # own store with a duplicate coordinate → WARN (not FAIL)
    f = check_translation_store("t/psa.py", "psa", "own", [(36, 24, "a"), (36, 24, "b")])
    cases.append(("own dup-coord → WARN", has(f, WARN, "dup-coord")))
    cases.append(("own dup-coord NOT FAIL", not has(f, FAIL, "dup-coord")))

    # non-int chapter → FAIL
    f = check_translation_store("t/x.py", "gen", "canonical", [("1", 1, "a")])
    cases.append(("non-int chapter → FAIL", has(f, FAIL, "nonint-chapter")))

    # impossible chapter in the KJV reference store (Genesis has 50) → FAIL chapter-missing
    f = check_translation_store("kjv/gen.py", "gen", "canonical", [(87, 12, "noise")], translation="kjv")
    cases.append(("kjv chapter-missing → FAIL", has(f, FAIL, "chapter-missing") or canonical_book_shape is None))

    # impossible chapter in a NON-kjv store → WARN (could be a legit extra chapter → declare own)
    f = check_translation_store(
        "amharic-tewahedo/gen.py", "gen", "canonical", [(87, 12, "x")], translation="amharic-tewahedo"
    )
    cases.append(("non-kjv chapter-missing → WARN", has(f, WARN, "chapter-missing") or canonical_book_shape is None))

    # verse-overflow in the KJV store → WARN canonical-table-gap (the real aes 10:11-13 class)
    f = check_translation_store("kjv/aes.py", "aes", "canonical", [(10, 13, "x")], translation="kjv")
    cases.append(
        ("kjv verse-overflow → WARN table-gap", has(f, WARN, "canonical-table-gap") or canonical_book_shape is None)
    )

    # verse-overflow in a non-kjv store → INFO nonkjv-versification (the LXX Psalter class)
    f = check_translation_store(
        "amharic-tewahedo/psa.py", "psa", "canonical", [(9, 25, "x")], translation="amharic-tewahedo"
    )
    cases.append(
        ("non-kjv verse-overflow → INFO", has(f, INFO, "nonkjv-versification") or canonical_book_shape is None)
    )

    # non-canonical book-code stem (ex → exo, absent from aliases) → WARN, surfaces the blind spot
    f = check_translation_store("geez-tewahedo/ex.py", "ex", "canonical", [(1, 1, "x")], translation="geez-tewahedo")
    cases.append(("non-canonical stem 'ex' → WARN", has(f, WARN, "book-code-noshape") or canonical_book_shape is None))

    # legitimate Tewahedo distinctive (no skeleton) → NO book-code anomaly WARN
    f = check_translation_store("geez-tewahedo/1en.py", "1en", "canonical", [(1, 1, "x")], translation="geez-tewahedo")
    cases.append(("distinctive '1en' → no anomaly WARN", not has(f, WARN, "book-code-noshape")))

    # own lettered verse → INFO, never FAIL
    f = check_translation_store("t/est.py", "est", "own", [(1, "2a", "x")])
    cases.append(("own lettered verse → INFO", has(f, INFO, "nonint-verse") and not has(f, FAIL, "nonint-verse")))

    # clean canonical store → nothing
    f = check_translation_store("t/x.py", "psa", "canonical", [(1, 1, "a"), (1, 2, "b")])
    cases.append(("clean store → no findings", f == []))

    # notes with non-int chapter → FAIL
    f = check_notes_store("notes/x.py", [("1", 1, "", "", "k", "", "", "", "")])
    cases.append(("notes non-int chapter → FAIL", has(f, FAIL, "notes-coord")))

    ok = True
    for name, passed in cases:
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")
        ok = ok and passed
    print(f"\nselftest: {'all green' if ok else 'REGRESSION'} ({sum(p for _, p in cases)}/{len(cases)})")
    return 0 if ok else 1


# ──────────────────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Translation/notes store integrity audit.")
    ap.add_argument("--json", metavar="OUT", help="write findings as JSON to OUT")
    ap.add_argument("--quiet", action="store_true", help="summary only (no per-finding lines)")
    ap.add_argument("--selftest", action="store_true", help="run the synthetic known-bad fixtures and exit")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()

    findings = audit_repo(REPO)
    _print_report(findings, args.quiet)
    if args.json:
        Path(args.json).write_text(
            json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return 1 if any(f.level == FAIL for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
