"""scripts.core — the stable foundation library for the YHWH Ya' Way platform.

Modules in this package are imported by 30+ scripts across the codebase.
Their public APIs are considered stable: breaking changes require a major
version bump and a CHANGELOG entry.

Public modules:

  config          YAML loaders for books / kinds / categories / editions.
                  Use ``load_books()``, ``books_by_code()``, ``get_book(code)``,
                  and the parallel kind/category/edition functions. Results
                  are LRU-cached for the life of the process.

  notes_io        Atomic write + backup helpers (used by every authoring
                  tool). ``atomic_write(path, text)`` writes through a
                  ``.tmp`` sibling so partial writes are impossible.
                  ``ensure_backup(path)`` snapshots a file into ``.backups/``
                  with a timestamped name before mutation.
                  ``load_notes(path)`` is LRU-cached and 42x faster than
                  re-evaluating the .py file each call.

  detectors       Polymorphic note-candidate scanners. Each detector
                  produces a list of ``Candidate`` objects from a verse
                  text. New detectors implement the same ``detect()``
                  signature.

  sources         Lazy loaders for the public-domain reference corpora
                  (Strong's Hebrew, Treasury of Scripture Knowledge).
                  Singletons cached for the process lifetime.

  html_utils      Tiny HTML helpers: ``strip_tags()`` and ``word_count()``.

  ui              Terminal styling constants (GREEN, RED, DIM, BOLD, …)
                  + ``ok()`` / ``warn()`` / ``err()`` / ``info()`` printers.

Stability commitment:

  * Adding new functions, classes, or kwargs is non-breaking.
  * Removing or renaming any public symbol is breaking.
  * Changing the meaning of an existing return value is breaking.
  * Internal helpers (names starting with ``_``) are NOT covered.

If you find yourself needing to break a public API, prefer:

  1. Add a new function with the new behaviour
  2. Mark the old one as deprecated (add a ``DeprecationWarning``)
  3. Schedule removal in the next major version (with a CHANGELOG note)

over silently changing semantics.
"""
