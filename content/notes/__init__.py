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

import importlib
import importlib.util
from pathlib import Path

_HERE = Path(__file__).parent


def all_codes():
    """Return sorted list of all book codes that have a notes module here."""
    return sorted(p.stem for p in _HERE.glob("*.py") if p.stem != "__init__" and not p.stem.startswith("_"))


def load_notes(code):
    """Import content/notes/<code>.py and return its NOTES list."""
    # Module names with a leading digit (e.g. '1en', '2ki') need importlib by path.
    fname = _HERE / f"{code}.py"
    if not fname.exists():
        raise FileNotFoundError(f"No notes module for code {code!r}")
    spec = importlib.util.spec_from_file_location(f"content.notes._{code}", fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.NOTES
