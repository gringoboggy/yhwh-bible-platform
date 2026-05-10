"""ω.26 — vulture false-positive whitelist.

Vulture's static analysis can't see two patterns the project relies
on heavily:

  1. **`@functools.lru_cache` key parameters** — cache wrappers
     accept signature args used only by the decorator's hashing
     machinery; the function body legitimately ignores them.
     Pattern: `_cached_X(*sigs) -> _compute_X_uncached()`.

  2. **`HTMLParser` hook overrides** — `handle_decl(self, decl)`,
     `handle_pi(self, data)`, etc. take a parameter required by
     the parent class's API but the override may legitimately
     ignore it (e.g. when stripping the construct entirely).

Vulture treats any name appearing in this file as "used", so listing
the false-positive symbol names here silences them without polluting
the source files themselves with `# noqa: vulture` markers.

Run::

    python -m vulture scripts/ scripts/.vulture_whitelist.py

The whitelist is intentionally narrow -- every entry should have a
documented reason. Adding a new entry here is a deliberate
"this isn't dead, vulture is wrong" decision.
"""

# ---- @lru_cache key parameters (scripts/web.py) ----
# These are used by functools.lru_cache for hashing; the function
# bodies don't reference them by design.
_.notes_sig
_.kinds_sig
_.cats_sig
_.books_sig
_.eds_sig
_.canons_sig

# ---- HTMLParser hook overrides (scripts/core/html_sanitize.py) ----
# Required by html.parser.HTMLParser API; we strip the construct.
_.decl
