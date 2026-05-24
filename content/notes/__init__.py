"""
Per-book commentary notes. One file per canonical book code.

Convention:
  Every notes module exposes a top-level `NOTES` list and a `NOTES_<CODE>`
  alias for backward compatibility with the legacy injectors.

Programmatic access:
  from content.notes import load_notes
  notes = load_notes('gen')         # list of 8-tuples

  from content.notes import all_codes
  for code in all_codes(): …
"""

from pathlib import Path

_HERE = Path(__file__).parent


def all_codes():
    """Return sorted list of all book codes that have a notes module here."""
    return sorted(p.stem for p in _HERE.glob("*.py") if p.stem != "__init__" and not p.stem.startswith("_"))


def load_notes(code):
    """Return the NOTES list from content/notes/<code>.py.

    The module's data is parsed with ``ast.literal_eval`` (via
    ``scripts.core.notes_io.load_notes``) — the file is NEVER executed,
    so a corrupted or hostile notes module cannot run code (RULES §7.1).
    """
    fname = _HERE / f"{code}.py"
    if not fname.exists():
        raise FileNotFoundError(f"No notes module for code {code!r}")
    # Lazy import mirrors notes_io's own corpus_index import — avoids any
    # startup-order import cycle; cached in sys.modules after first call.
    from scripts.core.notes_io import load_notes as _load_notes_ast

    notes = _load_notes_ast(fname)
    if notes is None:
        raise ValueError(f"Notes module {code!r} could not be parsed as literal data")
    return notes
