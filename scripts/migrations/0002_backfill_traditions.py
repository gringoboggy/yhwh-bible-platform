"""0002 — backfill_traditions (ω.22 backfill of ψ.8 helper).

Wraps `scripts/backfill_traditions.py:main()` so the existing
ad-hoc audit can be invoked through the unified migration runner
introduced in ω.22.

The wrapped script's default mode is audit-only: it walks every
note in ``content/notes/`` and reports which (if any) need a
non-default ``tradition`` field stamped. The audit returns exit
0 when nothing needs rewriting (the current state of the corpus,
which is sourced entirely from PD references that resolve to the
default ``cross`` tradition).

When future χ.2-χ.5 commentary phases ship tradition-tagged notes
(Henry → protestant, Catena Aurea → orthodox, etc.) this migration's
behaviour shifts from "no-op audit" to "rewrite pending"; that
change is tracked under ψ.8.0.1 (AST-aware rewriter) and is
deliberately out of scope for ω.22.

Forward-only: an automatic ``down()`` would re-clear the explicit
field, which is itself a kind of rewrite. Restore from a ω.16
snapshot if needed.
"""

from __future__ import annotations

import sys
from pathlib import Path

ID = "0002"
DESCRIPTION = (
    "ψ.8 — audit + (eventually) backfill the tradition field on "
    "non-default notes. Today: no-op audit; future: rewrite when "
    "tradition-tagged content lands."
)


def up() -> dict:
    """Invoke ``scripts/backfill_traditions.py:main()``.

    The wrapped script returns 0 when the audit is clean (nothing
    to rewrite) and 1 when notes WOULD be rewritten without
    ``--apply``. Today's corpus produces 0; we treat that as the
    success case for the migration.
    """
    repo = Path(__file__).resolve().parent.parent.parent
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    # The wrapped script's main() doesn't accept argv; call directly.
    from scripts.backfill_traditions import main as _main  # noqa: E402

    rc = _main()
    if rc == 0:
        return {
            "ok": True,
            "message": ("backfill_traditions.main() audit clean (no rewrites needed)"),
        }
    # rc=1 means "would rewrite but --apply wasn't given." For the
    # framework's purposes, that's a soft failure — the migration
    # is real, but actually applying it requires the AST-aware
    # rewriter (ψ.8.0.1) that hasn't shipped yet.
    return {
        "ok": False,
        "message": (f"backfill_traditions audit found pending rewrites (rc={rc}); see ψ.8.0.1 for the apply path"),
    }


def down() -> dict:
    """Forward-only — see module docstring."""
    raise NotImplementedError(
        "0002 is forward-only; restore from a ω.16 snapshot if you need to revert tradition stamps"
    )
