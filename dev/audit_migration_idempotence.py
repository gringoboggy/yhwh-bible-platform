#!/usr/bin/env python3
"""Round-15 gate D7 — migration re-run / idempotency safety (build-free, sandboxed).

Migration 0001 (`scripts/migrate_to_user_data.py`, wrapped by `scripts/migrations/0001_*.py`)
bootstraps the bundled `content/` into the user-data dir. Its idempotency rests on a single
`editions.yaml` marker (`_is_already_migrated`) — so the marker MUST be the last thing written
and must appear whole-or-not-at-all, or a torn/interrupted first run can leave the marker
present with content missing and report "Already migrated" forever (the notes of a torn book
vanish from the app + any EPUB built off it, while the ledger claims success).

This gate runs the REAL migration functions against SYNTHETIC temp directories (no real content
copied, no env mutation) and asserts the torn-safety contract holds. The checks are
parametrized on the migration functions so `--selftest` can run a deliberately-BROKEN
(marker-FIRST) variant and prove each check actually fires (non-tautological).

Checks:
  1. MARKER-LAST — `migration_copy_order(src)` ends with `editions.yaml` (its presence is then a
     reliable completion signal).
  2. DOUBLE-APPLY IDEMPOTENT — `perform_migration` twice reproduces src byte-for-byte and the
     second pass copies 0 files (skip-if-exists).
  3. TORN-RECOVERY — after a simulated crash that copied only the FIRST ordered file, the dst
     must NOT report "migrated" while incomplete, and a re-run must restore the full content.
  4. RUNNER CONTRACT — every `scripts/migrations/0*.py` defines `up()`.

Exit 0 = torn-safe + idempotent; 1 = FAIL; 2 = usage.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.migrate_to_user_data import (  # noqa: E402
    MARKER_NAME,
    _is_already_migrated,
    migration_copy_order,
    perform_migration,
)


def _make_src(root: Path) -> Path:
    """A small synthetic migration source: the marker + a few nested content files."""
    src = root / "content"
    (src / "notes").mkdir(parents=True, exist_ok=True)
    (src / "translations" / "kjv").mkdir(parents=True, exist_ok=True)
    (src / MARKER_NAME).write_text("editions:\n  - id: demo\n", encoding="utf-8")
    (src / "notes" / "gen.py").write_text("VERSES = [(1, 1, 'a')]\n", encoding="utf-8")
    (src / "notes" / "exo.py").write_text("VERSES = [(1, 1, 'b')]\n", encoding="utf-8")
    (src / "translations" / "kjv" / "gen.py").write_text("T = 'kjv'\n", encoding="utf-8")
    return src


def _snapshot(d: Path) -> dict[str, bytes]:
    """{relpath: bytes} for every real file under ``d`` (ignores leftover .tmp)."""
    out: dict[str, bytes] = {}
    for p in sorted(d.rglob("*")):
        if p.is_file() and p.suffix != ".tmp":
            out[str(p.relative_to(d)).replace("\\", "/")] = p.read_bytes()
    return out


def _check_marker_last(order_fn, src: Path) -> list[str]:
    order = order_fn(src)
    if not order or order[-1].name != MARKER_NAME:
        return [f"copy order does not end with the {MARKER_NAME} marker (order tail: {[p.name for p in order[-3:]]})"]
    if sum(1 for p in order if p.name == MARKER_NAME) != 1:
        return [f"{MARKER_NAME} appears more than once in the copy order"]
    return []


def _check_double_apply(perform_fn, src: Path, dst: Path) -> list[str]:
    fails: list[str] = []
    r1 = perform_fn(src, dst)
    if r1["errors"]:
        fails.append(f"first apply errors: {r1['errors']}")
    if _snapshot(dst) != _snapshot(src):
        fails.append("first apply did not reproduce src byte-for-byte")
    r2 = perform_fn(src, dst)
    if r2["copied"] != 0:
        fails.append(f"second apply re-copied {r2['copied']} file(s) — not idempotent (skip-if-exists broken)")
    if _snapshot(dst) != _snapshot(src):
        fails.append("second apply mutated dst — not idempotent")
    return fails


def _check_torn_recovery(order_fn, perform_fn, is_migrated_fn, src: Path, dst: Path) -> list[str]:
    fails: list[str] = []
    order = order_fn(src)
    # Simulate a crash right after the FIRST ordered file is copied.
    first = order[0]
    rel = first.relative_to(src)
    (dst / rel).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(first, dst / rel)
    # Torn-safety invariant: an incomplete dst must NOT report "migrated".
    if is_migrated_fn(dst) and _snapshot(dst) != _snapshot(src):
        fails.append(
            "a torn run (only the first file copied) reports ALREADY-MIGRATED while incomplete "
            "— the marker was not written last/atomically, so the partial copy is never repaired"
        )
    # A re-run must repair to the full content.
    perform_fn(src, dst)
    if _snapshot(dst) != _snapshot(src):
        fails.append("re-run after a torn first run did not restore the full content")
    if not is_migrated_fn(dst):
        fails.append("dst is complete but is_migrated() is False (marker missing after a full run)")
    return fails


def _run_behavioral(order_fn, perform_fn, is_migrated_fn) -> list[str]:
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        src = _make_src(root)
        fails += _check_marker_last(order_fn, src)
        fails += _check_double_apply(perform_fn, src, root / "dst1")
        fails += _check_torn_recovery(order_fn, perform_fn, is_migrated_fn, src, root / "dst2")
    return fails


def _check_runner_contract() -> list[str]:
    fails: list[str] = []
    mig = REPO / "scripts" / "migrations"
    defs = sorted(mig.glob("0*.py")) if mig.is_dir() else []
    if not defs:
        return ["no scripts/migrations/0*.py migration definitions found"]
    for f in defs:
        if "def up(" not in f.read_text(encoding="utf-8"):
            fails.append(f"{f.name}: no up() — violates the migrate.py runner contract")
    return fails


def audit() -> tuple[list[str], dict]:
    fails = _run_behavioral(migration_copy_order, perform_migration, _is_already_migrated)
    fails += _check_runner_contract()
    n_defs = len(list((REPO / "scripts" / "migrations").glob("0*.py")))
    return fails, {"migration_defs": n_defs, "checks": 4}


def _selftest() -> int:
    """Prove the behavioral checks fire on a BROKEN (marker-FIRST, non-atomic) migration."""

    def broken_order(src: Path) -> list[Path]:
        # marker FIRST — the bug: a torn run leaves the marker present with content missing.
        files = sorted(p for p in src.rglob("*") if p.is_file())
        marker = src / MARKER_NAME
        return ([marker] if marker.is_file() else []) + [f for f in files if f != marker]

    def broken_perform(src: Path, dst: Path, *, force: bool = False) -> dict:
        dst.mkdir(parents=True, exist_ok=True)
        copied = skipped = 0
        for sf in broken_order(src):
            df = dst / sf.relative_to(src)
            if df.exists() and not force:
                skipped += 1
                continue
            df.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sf, df)
            copied += 1
        return {"copied": copied, "skipped": skipped, "errors": []}

    ok = True
    # The REAL (fixed) functions must pass cleanly.
    if _run_behavioral(migration_copy_order, perform_migration, _is_already_migrated):
        print("  ✗ selftest: the REAL migration failed its own torn-safety checks")
        ok = False
    # The BROKEN variant must be CAUGHT (marker-last + torn-recovery both fire).
    broken_fails = _run_behavioral(broken_order, broken_perform, _is_already_migrated)
    if not any("does not end with" in m for m in broken_fails):
        print("  ✗ selftest: marker-last check did NOT flag a marker-first order (tautological)")
        ok = False
    if not any("torn run" in m for m in broken_fails):
        print("  ✗ selftest: torn-recovery check did NOT flag the marker-first migration (tautological)")
        ok = False
    print("  ✓ D7 migration-idempotence-gate selftest passed" if ok else "  selftest FAILED")
    return 0 if ok else 1


def _arg(argv: list[str], flag: str, default: str | None = None) -> str | None:
    return argv[argv.index(flag) + 1] if flag in argv else default


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    max_show = int(_arg(argv, "--max-show", "50"))
    json_out = _arg(argv, "--json")
    fails, stats = audit()
    status = "PASS" if not fails else "FAIL"
    print(f"\n=== D7 migration re-run / idempotency {status} ===")
    print(f"  migration_defs={stats['migration_defs']} checks={stats['checks']}")
    for f in fails[:max_show]:
        print("  ✗", f)
    if len(fails) > max_show:
        print(f"  ✗ … +{len(fails) - max_show} more FAIL(s)")
    if json_out:
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump({"green": not fails, "stats": stats, "fails": fails}, fh, indent=1)
        print(f"\nwrote {json_out}")
    verdict = "torn-safe + idempotent" if not fails else "has idempotency FAILs"
    print(f"\n{'PASS' if not fails else 'FAIL'}: migration {verdict}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
