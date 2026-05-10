"""0001 — migrate_to_user_data (ω.22 backfill of ω.5 helper).

Wraps `scripts/migrate_to_user_data.py:main()` so the existing
ad-hoc script can be invoked through the unified migration runner
introduced in ω.22.

The wrapped script is idempotent (a second run reports "already
migrated" and exits 0), so re-applying this migration is safe.

Forward-only: the underlying script copies in-tree ``content/`` to
the user-data location. ``down()`` would have to delete user data,
which is destructive in a way the framework deliberately doesn't
support — implementations that need to "go back" should restore
from a snapshot (``ω.16``) rather than try to undo the copy.
"""

from __future__ import annotations

import sys
from pathlib import Path

ID = "0001"
DESCRIPTION = "ω.5 — copy in-tree content/ into the platform user-data dir (idempotent; safe to re-run)."


def up() -> dict:
    """Invoke ``scripts/migrate_to_user_data.py:main([])`` and
    surface its exit code."""
    repo = Path(__file__).resolve().parent.parent.parent
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from scripts.migrate_to_user_data import main as _main  # noqa: E402

    rc = _main([])
    if rc == 0:
        return {"ok": True, "message": "migrate_to_user_data.main() ok"}
    return {
        "ok": False,
        "message": f"migrate_to_user_data.main() exited rc={rc}",
    }


def down() -> dict:
    """Forward-only — see module docstring."""
    raise NotImplementedError(
        "0001 is forward-only; restore from a ω.16 snapshot if you need to revert the user-data copy"
    )
