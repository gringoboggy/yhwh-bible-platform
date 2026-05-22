#!/usr/bin/env python3
"""ω.22 — Migration scripts framework.

Versioned, idempotent, append-only migration runner. Each migration
is a Python module under ``scripts/migrations/`` named
``<NNNN>_<name>.py`` exposing four module-level attributes:

    ID:           str   — zero-padded 4-digit identifier (matches filename)
    DESCRIPTION:  str   — one-line summary for `migrate.py list/status`
    up():         func  — apply the migration (idempotent)
    down():       func  — reverse the migration (may raise
                          NotImplementedError for forward-only ones)

Both ``up()`` and ``down()`` return a dict ``{ok: bool, message: str,
...}``. An ``up()`` that has nothing to do (already applied) returns
``ok=True`` with an "already applied" message — the runner treats
that as success without recording a duplicate ledger entry.

State of record lives at ``content/.migration_state.yaml`` (the
"ledger"). Each entry: ``{id, name, applied_at}``. ``applied_at`` is
ISO-8601 UTC. The file is created on first apply; never deleted.

Usage::

    python scripts/migrate.py list                  # discover all known
    python scripts/migrate.py status                # applied vs pending
    python scripts/migrate.py up                    # apply all pending
    python scripts/migrate.py up --to 0002          # apply through 0002
    python scripts/migrate.py down --to 0000        # roll back through 0001
    python scripts/migrate.py status --json         # CI-friendly

Per CLAUDE_PROJECT_RULES §10 (standard library only on the
backend): no Alembic, no Yoyo, no SQLAlchemy migrations. PyYAML is
already a project dep and handles the ledger; everything else is
stdlib.

Per §9 "pure function + thin route adapter": discovery + state
parsing + decision logic live as pure functions; the CLI is a thin
shell that translates dicts to console output and exit codes.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


_REPO = Path(__file__).resolve().parent.parent
_MIGRATIONS_DIR = _REPO / "scripts" / "migrations"
_DEFAULT_STATE_PATH = _REPO / "content" / ".migration_state.yaml"


# ----------------------------------------------------------------------
# Pure helpers — discovery + state parsing
# ----------------------------------------------------------------------


def discover_migrations(
    migrations_dir: Path | None = None,
) -> list[dict]:
    """Return every migration module under ``migrations_dir`` as a
    list of dicts ``[{id, name, path, module}]`` sorted by id.

    A migration file is any ``<NNNN>_<name>.py`` where ``NNNN`` is
    a 4-digit identifier. The leading 4 digits set the order; the
    rest of the filename (after the underscore) is the
    human-readable name. Missing ``__init__.py`` markers are OK —
    we load each module by file path so namespace-package gymnastics
    aren't required.
    """
    base = migrations_dir or _MIGRATIONS_DIR
    if not base.is_dir():
        return []
    found: list[dict] = []
    for py in sorted(base.glob("[0-9][0-9][0-9][0-9]_*.py")):
        stem = py.stem  # e.g. "0001_migrate_to_user_data"
        ident, _, name = stem.partition("_")
        if not (ident.isdigit() and len(ident) == 4 and name):
            continue
        module = _load_migration_module(py)
        found.append(
            {
                "id": ident,
                "name": name,
                "path": py,
                "module": module,
                "description": getattr(module, "DESCRIPTION", "").strip(),
            }
        )
    return found


def _load_migration_module(path: Path) -> Any:
    """Import a migration module from its file path."""
    mod_name = f"_yhwh_migration_{path.stem}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load migration {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_state(
    state_path: Path | None = None,
) -> dict:
    """Read the migration ledger. Missing file → empty
    ``{applied: []}``."""
    path = state_path or _DEFAULT_STATE_PATH
    if not path.is_file():
        return {"applied": []}
    try:
        import yaml
    except ImportError:
        # PyYAML is a project dep per requirements.txt; this branch
        # only fires in a degraded environment. Treat it as empty
        # rather than failing — the migrations themselves still run.
        return {"applied": []}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict) or "applied" not in raw:
        return {"applied": []}
    return raw


def save_state(
    state: dict,
    state_path: Path | None = None,
) -> Path:
    """Write the migration ledger atomically. Backs up the prior
    contents via ``notes_io.ensure_backup`` first so a recoverable
    history of state changes accumulates."""
    from scripts.core import notes_io

    path = state_path or _DEFAULT_STATE_PATH
    if path.is_file():
        notes_io.ensure_backup(path)
    import yaml

    text = yaml.safe_dump(state, sort_keys=False, allow_unicode=True)
    notes_io.atomic_write(path, text)
    return path


def applied_ids(state: dict) -> list[str]:
    """Sorted list of already-applied migration ids."""
    return sorted(e["id"] for e in (state.get("applied") or []) if isinstance(e, dict) and "id" in e)


def pending_migrations(
    state: dict,
    migrations: list[dict],
) -> list[dict]:
    """Migrations whose id is NOT yet in the ledger, in id order."""
    done = set(applied_ids(state))
    return [m for m in migrations if m["id"] not in done]


def applied_migrations(
    state: dict,
    migrations: list[dict],
) -> list[dict]:
    """Discovered migrations that ARE in the ledger, in id order."""
    done = set(applied_ids(state))
    return [m for m in migrations if m["id"] in done]


# ----------------------------------------------------------------------
# Action runners
# ----------------------------------------------------------------------


def apply_up(
    migration: dict,
    state: dict,
    *,
    state_path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    """Apply one migration's ``up()``. Updates the ledger on success.

    Idempotency: if ``migration["id"]`` is already in the ledger,
    returns ``{ok: True, message: "already applied", skipped: True}``
    without invoking ``up()``. The migration's own ``up()`` SHOULD
    also be idempotent as a defence in depth, but the framework
    saves a hot subprocess by checking the ledger first.
    """
    if migration["id"] in applied_ids(state):
        return {
            "ok": True,
            "skipped": True,
            "message": f"{migration['id']}: already applied",
        }
    up_fn: Callable[[], dict] = getattr(migration["module"], "up", None)
    if up_fn is None:
        return {
            "ok": False,
            "message": (f"{migration['id']}: module has no up() function"),
        }
    try:
        result = up_fn() or {}
    except Exception as e:
        return {
            "ok": False,
            "message": f"{migration['id']}: up() raised: {e}",
        }
    if not result.get("ok", True):
        return {
            "ok": False,
            "message": (f"{migration['id']}: up() returned not-ok: {result.get('message', '')}"),
        }
    # Success: append to ledger.
    timestamp = (now or datetime.now(timezone.utc)).strftime(
        "%Y-%m-%dT%H:%M:%SZ",
    )
    state.setdefault("applied", []).append(
        {
            "id": migration["id"],
            "name": migration["name"],
            "applied_at": timestamp,
        }
    )
    save_state(state, state_path)
    return {
        "ok": True,
        "skipped": False,
        "message": (f"{migration['id']} ({migration['name']}): {result.get('message', 'up() ok')}"),
    }


def apply_down(
    migration: dict,
    state: dict,
    *,
    state_path: Path | None = None,
) -> dict:
    """Reverse one migration's ``up()`` via its ``down()`` function.
    On success, removes the migration's ledger entry.

    Forward-only migrations raise ``NotImplementedError`` from
    ``down()``; the runner surfaces that as ``{ok: False,
    forward_only: True, ...}`` so callers can render a clear
    message rather than a raw traceback.
    """
    if migration["id"] not in applied_ids(state):
        return {
            "ok": True,
            "skipped": True,
            "message": f"{migration['id']}: not applied; nothing to roll back",
        }
    down_fn: Callable[[], dict] = getattr(migration["module"], "down", None)
    if down_fn is None:
        return {
            "ok": False,
            "message": (f"{migration['id']}: module has no down() function"),
        }
    try:
        result = down_fn() or {}
    except NotImplementedError as e:
        return {
            "ok": False,
            "forward_only": True,
            "message": (f"{migration['id']}: forward-only migration ({e or 'no down() implementation'})"),
        }
    except Exception as e:
        return {
            "ok": False,
            "message": f"{migration['id']}: down() raised: {e}",
        }
    if not result.get("ok", True):
        return {
            "ok": False,
            "message": (f"{migration['id']}: down() returned not-ok: {result.get('message', '')}"),
        }
    state["applied"] = [e for e in state.get("applied", []) if e.get("id") != migration["id"]]
    save_state(state, state_path)
    return {
        "ok": True,
        "skipped": False,
        "message": (f"{migration['id']} ({migration['name']}): {result.get('message', 'down() ok')}"),
    }


# ----------------------------------------------------------------------
# Aggregate runners
# ----------------------------------------------------------------------


def run_up(
    *,
    to: str | None = None,
    migrations_dir: Path | None = None,
    state_path: Path | None = None,
) -> dict:
    """Apply every pending migration in id order, optionally stopping
    after id ``to``. Returns ``{ok, applied: [...], skipped: [...],
    summary: {...}}`` so CI can branch on a single value."""
    migrations = discover_migrations(migrations_dir)
    state = load_state(state_path)
    pending = pending_migrations(state, migrations)
    applied: list[dict] = []
    skipped: list[dict] = []
    failed: dict | None = None
    for m in pending:
        if to is not None and m["id"] > to:
            break
        result = apply_up(m, state, state_path=state_path)
        if not result.get("ok"):
            failed = result
            break
        if result.get("skipped"):
            skipped.append(result)
        else:
            applied.append(result)
    return {
        "ok": failed is None,
        "applied": applied,
        "skipped": skipped,
        "failed": failed,
        "summary": {
            "applied_count": len(applied),
            "skipped_count": len(skipped),
            "stopped_at": to,
        },
    }


def run_down(
    *,
    to: str | None = None,
    migrations_dir: Path | None = None,
    state_path: Path | None = None,
) -> dict:
    """Roll back applied migrations in reverse id order, stopping
    when the next migration's id would be ≤ ``to`` (i.e. ``to`` is
    the lowest id we leave applied; ``to=None`` rolls everything
    back)."""
    migrations = discover_migrations(migrations_dir)
    state = load_state(state_path)
    applied = applied_migrations(state, migrations)
    rolled: list[dict] = []
    skipped: list[dict] = []
    failed: dict | None = None
    for m in reversed(applied):
        if to is not None and m["id"] <= to:
            break
        result = apply_down(m, state, state_path=state_path)
        if not result.get("ok"):
            failed = result
            break
        if result.get("skipped"):
            skipped.append(result)
        else:
            rolled.append(result)
    return {
        "ok": failed is None,
        "rolled_back": rolled,
        "skipped": skipped,
        "failed": failed,
        "summary": {
            "rolled_back_count": len(rolled),
            "skipped_count": len(skipped),
            "stopped_after_id": to,
        },
    }


def status(
    *,
    migrations_dir: Path | None = None,
    state_path: Path | None = None,
) -> dict:
    """Snapshot of the migration world. Pure read; no writes."""
    migrations = discover_migrations(migrations_dir)
    state = load_state(state_path)
    return {
        "applied": [
            {"id": m["id"], "name": m["name"], "description": m["description"]}
            for m in applied_migrations(state, migrations)
        ],
        "pending": [
            {"id": m["id"], "name": m["name"], "description": m["description"]}
            for m in pending_migrations(state, migrations)
        ],
        "ledger_entries": state.get("applied") or [],
        "total": len(migrations),
    }


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="migrate",
        description=("ω.22 — versioned, idempotent migration runner for the project's content/ schema."),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="discover all known migrations")
    p_status = sub.add_parser("status", help="applied vs pending")
    p_status.add_argument("--json", action="store_true", help="machine-readable JSON output")
    p_up = sub.add_parser("up", help="apply pending migrations")
    p_up.add_argument("--to", help="apply up through this id (inclusive)")
    p_up.add_argument("--json", action="store_true")
    p_down = sub.add_parser("down", help="roll back migrations")
    p_down.add_argument(
        "--to",
        required=True,
        help=(
            "lowest id that will REMAIN applied. e.g. --to 0000 rolls "
            "back everything; --to 0001 leaves 0001 applied and rolls "
            "back 0002+."
        ),
    )
    p_down.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    if args.cmd == "list":
        migrations = discover_migrations()
        if not migrations:
            print("(no migrations registered)")
            return 0
        for m in migrations:
            print(f"  {m['id']}  {m['name']:35s}  {m['description']}")
        return 0

    if args.cmd == "status":
        snap = status()
        if args.json:
            print(json.dumps(snap, indent=2, default=str))
            return 0
        print(f"applied: {len(snap['applied'])}; pending: {len(snap['pending'])} (total: {snap['total']})\n")
        if snap["applied"]:
            print("applied:")
            for m in snap["applied"]:
                print(f"  ✓ {m['id']}  {m['name']}")
        if snap["pending"]:
            print("\npending:")
            for m in snap["pending"]:
                print(f"  ○ {m['id']}  {m['name']}  {m['description']}")
        return 0

    if args.cmd == "up":
        result = run_up(to=args.to)
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            for r in result["applied"]:
                print(f"  ✓ {r['message']}")
            for r in result["skipped"]:
                print(f"  · {r['message']}")
            if result["failed"]:
                print(f"  ✗ {result['failed']['message']}", file=sys.stderr)
        return 0 if result["ok"] else 1

    if args.cmd == "down":
        result = run_down(to=args.to)
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            for r in result["rolled_back"]:
                print(f"  ↩ {r['message']}")
            for r in result["skipped"]:
                print(f"  · {r['message']}")
            if result["failed"]:
                print(f"  ✗ {result['failed']['message']}", file=sys.stderr)
        return 0 if result["ok"] else 1

    return 2


if __name__ == "__main__":
    sys.exit(main())
