"""
config.py — load content/books.yaml, content/kinds.yaml, and
content/categories.yaml without introducing a PyYAML dependency.

We use a deliberately tiny parser that handles only the constrained
shape of our YAML files (key: value pairs, hyphenated lists, strings
quoted with double quotes per JSON-style emit). If anyone hand-edits
the YAML in a way that introduces multi-line strings or anchors, this
parser will reject the file with a clear error.

Public API:
  load_books()              -> list[dict]   (one per book)
  load_kinds()              -> list[dict]
  load_categories()         -> list[dict]
  load_editions()           -> list[dict]   (empty if editions.yaml missing)
  books_by_code()           -> dict[str, dict]
  kinds_by_code()           -> dict[str, dict]
  categories_by_id()        -> dict[str, dict]
  editions_by_id()          -> dict[str, dict]
  get_book(code)            -> dict
  get_kind(code)            -> dict
  get_category(id)          -> dict
  kinds_in_category(cat_id) -> list[dict]
  kinds_by_phase(phase)     -> list[dict]
  resolve_symbol(kind_code) -> str          (kind override OR category default)

Note tuple format (introduced v28a-4):
  (chapter, verse, suffix, anchor, kind, title, label, body_html [, attribution])

  The 9th field — `attribution` — is OPTIONAL during the migration phase.
  It identifies the source / provenance of the note (e.g. "User original",
  "Strong's H7779 (PD)", "Paraphrase summarising Westermann, Genesis 1-11
  (1984)"). After the corpus migration completes, validate_taxonomy.py
  will error on missing attribution; until then it warns.

  Use NoteSpec.from_tuple(t) or note_attribution(t) to read attribution
  in a backward-compatible way (returns None if the tuple is the legacy
  8-field form).
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from functools import lru_cache
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CONTENT = _REPO_ROOT / "content"


def _books_yaml_path() -> Path:
    """ω.5 paths-resolver entrypoint for content/books.yaml. Existing
    ``_CONTENT`` constant is preserved for back-compat with sibling
    YAML lookups; new call sites should prefer this function so they
    pick up dev/installed/test-override resolution automatically."""
    from . import paths
    return paths.books_yaml()


# ----------------------------------------------------------------------
# Note tuple schema (v28a-4 onwards: 9-field with optional attribution)
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class NoteSpec:
    """Typed view of a note tuple. The tuple format is the canonical
    on-disk representation (in content/notes/<book>.py). NoteSpec is the
    preferred Python-side handle for new code.

    Backward-compatible: ``from_tuple`` accepts both the legacy 8-field
    form and the 9-field form (with attribution).
    """

    chapter: int
    verse: int
    suffix: str
    anchor: str
    kind: str
    title: str
    label: str
    body_html: str
    attribution: Optional[str] = None  # 9th field, optional during migration

    @classmethod
    def from_tuple(cls, tup: tuple) -> "NoteSpec":
        if not isinstance(tup, tuple) or len(tup) < 8:
            raise ValueError(f"note tuple must have ≥8 fields, got {len(tup)}")
        attribution = tup[8] if len(tup) >= 9 else None
        # Normalise empty-string attribution to None for downstream consistency.
        if isinstance(attribution, str) and not attribution.strip():
            attribution = None
        return cls(
            chapter=tup[0],
            verse=tup[1],
            suffix=tup[2],
            anchor=tup[3],
            kind=tup[4],
            title=tup[5],
            label=tup[6],
            body_html=tup[7],
            attribution=attribution,
        )

    def to_tuple(self) -> tuple:
        """Emit the canonical tuple form. Always 9 fields when attribution is set;
        emits the legacy 8-field form when attribution is None to keep diffs minimal
        for unattributed notes during the migration phase."""
        base = (
            self.chapter,
            self.verse,
            self.suffix,
            self.anchor,
            self.kind,
            self.title,
            self.label,
            self.body_html,
        )
        if self.attribution is None:
            return base
        return base + (self.attribution,)


def note_attribution(tup: tuple) -> Optional[str]:
    """Return the attribution string for a note tuple, or None if absent.
    Convenience wrapper for code that doesn't need the full NoteSpec."""
    if not isinstance(tup, tuple) or len(tup) < 9:
        return None
    a = tup[8]
    if isinstance(a, str) and not a.strip():
        return None
    return a


# ----------------------------------------------------------------------
# Tiny YAML parser — sufficient for our two files.
# ----------------------------------------------------------------------


def _parse_value(s):
    """Parse a scalar YAML value. Strings are JSON-quoted; integers and `null`
    are bare; booleans not used here."""
    s = s.strip()
    # Strip trailing comments: a `#` that is not inside a quoted string.
    # We scan for `#` outside double-quoted regions.
    in_q = False
    cut = None
    for i, ch in enumerate(s):
        if ch == '"' and (i == 0 or s[i - 1] != "\\"):
            in_q = not in_q
        elif ch == "#" and not in_q and (i == 0 or s[i - 1] in " \t"):
            cut = i
            break
    if cut is not None:
        s = s[:cut].rstrip()
    if s == "" or s == "null":
        return None
    if s.startswith('"'):
        return json.loads(s)
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        return s


def _parse_yaml_records(text):
    """Parse our constrained YAML: a top-level key followed by a list of records,
    each starting with `  - field: value` and continuing with `    field: value`,
    with `field:` introducing a sub-list of `      - value` items.

    Returns a list of dicts.
    """
    lines = text.split("\n")
    records = []
    current = None
    list_field = None
    in_list = False

    # Find the top-level list start (e.g. "books:" or "kinds:")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        # Section header: `books:` or `kinds:`
        if re.match(r"^[a-z_]+:\s*$", line):
            i += 1
            break
        i += 1

    # Now parse list items
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # New record marker: `  - code: <value>`
        m = re.match(r"^( {2,})-\s+([a-z_]+):\s*(.*)$", line)
        if m:
            if current is not None:
                records.append(current)
            current = {}
            list_field = None
            in_list = False
            current[m.group(2)] = _parse_value(m.group(3))
            i += 1
            continue

        # Field continuation in current record: `    field: value`
        m = re.match(r"^( {4,})([a-z_]+):\s*(.*)$", line)
        if m:
            field = m.group(2)
            val = m.group(3)
            if val == "":
                # Sub-list start
                list_field = field
                in_list = True
                current[field] = []
            else:
                current[field] = _parse_value(val)
                in_list = False
            i += 1
            continue

        # Sub-list item: `      - value`
        m = re.match(r"^( {6,})-\s+(.*)$", line)
        if m and in_list:
            current[list_field].append(_parse_value(m.group(2)))
            i += 1
            continue

        # Anything else: ignore (top-level comments, blank lines)
        i += 1

    if current is not None:
        records.append(current)
    return records


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


@lru_cache(maxsize=1)
def load_books():
    """Load and cache the 87-book registry from content/books.yaml.

    Returns a list of dicts with keys: code, title, bxx, bp, next_bp,
    ch_count, strategy, id_prefix, files. The result is cached for the
    life of the process — call ``load_books.cache_clear()`` to refresh
    after editing books.yaml.
    """
    return _parse_yaml_records((_CONTENT / "books.yaml").read_text())


@lru_cache(maxsize=1)
def load_kinds():
    """Load and cache the kind registry from content/kinds.yaml.

    Returns a list of dicts with keys: code, category, label, note_class,
    marker_class, optional symbol/budget overrides. Cached for the life
    of the process.
    """
    return _parse_yaml_records((_CONTENT / "kinds.yaml").read_text())


@lru_cache(maxsize=1)
def load_categories():
    """Load content/categories.yaml. Returns [] if the file doesn't exist
    (so older deployments without categories continue working)."""
    p = _CONTENT / "categories.yaml"
    if not p.is_file():
        return []
    return _parse_yaml_records(p.read_text())


@lru_cache(maxsize=1)
def load_editions():
    """Load content/editions.yaml. Returns [] if missing."""
    p = _CONTENT / "editions.yaml"
    if not p.is_file():
        return []
    return _parse_yaml_records(p.read_text())


def books_by_code():
    """Return a dict mapping book code → book dict (e.g. ``{"gen": {...}}``)."""
    return {b["code"]: b for b in load_books()}


def kinds_by_code():
    """Return a dict mapping kind code → kind dict (e.g. ``{"comm-rabbinic": {...}}``)."""
    return {k["code"]: k for k in load_kinds()}


def categories_by_id():
    """Return a dict mapping category id → category dict (e.g. ``{"lang": {...}}``)."""
    return {c["id"]: c for c in load_categories()}


def editions_by_id():
    """Return a dict mapping edition id → edition dict (e.g. ``{"catholic-study": {...}}``)."""
    return {e["id"]: e for e in load_editions()}


def get_book(code):
    """Look up a single book by its code. Raises KeyError with hint if unknown."""
    bb = books_by_code()
    if code not in bb:
        raise KeyError(f"Unknown book code {code!r}. Known: {sorted(bb)[:8]}...")
    return bb[code]


def get_kind(code):
    """Look up a single kind by its code. Raises KeyError with hint if unknown."""
    kk = kinds_by_code()
    if code not in kk:
        raise KeyError(f"Unknown kind code {code!r}. Known: {sorted(kk)[:8]}...")
    return kk[code]


def get_category(cat_id):
    """Look up a single category by its id. Raises KeyError with hint if unknown."""
    cc = categories_by_id()
    if cat_id not in cc:
        raise KeyError(f"Unknown category id {cat_id!r}. Known: {sorted(cc)}")
    return cc[cat_id]


def kinds_in_category(cat_id):
    """Return list of kinds whose `category` field equals cat_id."""
    return [k for k in load_kinds() if k.get("category") == cat_id]


def kinds_by_phase(phase):
    """Return list of kinds whose `phase` field matches.
    phase ∈ {'legacy', 'mvp', 'phase2', 'phase3'}."""
    return [k for k in load_kinds() if k.get("phase") == phase]


def resolve_symbol(kind_code):
    """Return the inline marker symbol for a kind. Falls back to the
    category default if the kind itself doesn't override."""
    k = get_kind(kind_code)
    sym = k.get("symbol")
    if sym:
        return sym
    cat_id = k.get("category")
    if cat_id:
        cat = categories_by_id().get(cat_id)
        if cat and cat.get("symbol"):
            return cat["symbol"]
    return "·"  # last-resort fallback


_PHASE_ORDER = {"legacy": 0, "mvp": 1, "phase2": 2, "phase3": 3}


def _kinds_in_edition(edition_id):
    """Return list of kind dicts visible in a given edition profile.

    Filter logic (matches editions.yaml documentation):
      1. Start from kinds whose `category` is in `enabled_categories`
         (or all kinds if `enabled_categories` is empty/missing).
      2. Add any kinds explicitly listed in `enabled_kinds`.
      3. Remove any kinds explicitly listed in `disabled_kinds`.
      4. Filter out kinds whose `phase` is later than `max_phase`
         (e.g. max_phase='phase2' excludes phase3 kinds).

    Legacy kinds (`word`, `comm`, `source`, `parallel`) are always
    included if their category is enabled — they're the safety net
    for backwards compatibility.

    Returns kind dicts in their kinds.yaml declaration order.
    """
    eds = editions_by_id()
    if edition_id not in eds:
        raise KeyError(f"Unknown edition id {edition_id!r}. Known: {sorted(eds)}")
    ed = eds[edition_id]

    enabled_cats = set(ed.get("enabled_categories") or [])
    explicit_add = set(ed.get("enabled_kinds") or [])
    explicit_remove = set(ed.get("disabled_kinds") or [])
    max_phase = ed.get("max_phase")
    max_phase_n = _PHASE_ORDER.get(max_phase, 99) if max_phase else 99

    out = []
    for k in load_kinds():
        code = k.get("code")
        cat = k.get("category")
        # Step 1 + 2: included if category is enabled OR code is explicitly added
        included = (not enabled_cats) or (cat in enabled_cats) or (code in explicit_add)
        if not included:
            continue
        # Step 3: explicit removal wins
        if code in explicit_remove:
            continue
        # Step 4: phase ceiling
        kp = k.get("phase", "mvp")
        if _PHASE_ORDER.get(kp, 99) > max_phase_n:
            continue
        out.append(k)
    return out


if __name__ == "__main__":
    bb = load_books()
    kk = load_kinds()
    cc = load_categories()
    ee = load_editions()
    print(f"Books:      {len(bb)} loaded")
    for b in bb[:3]:
        print(
            f"  {b['code']:4} {b.get('bxx') or '—':4} "
            f"ch={b['ch_count']:>4}  files={len(b.get('files') or [])}  "
            f"strategy={b['strategy']}  {b['title']}"
        )
    print(f"... {len(bb) - 3} more")
    print(f"\nCategories: {len(cc)} loaded")
    for c in cc:
        n = len(kinds_in_category(c["id"]))
        print(f"  {c['id']:8} {c['symbol']}  {c['label']:24}  ({n} kinds)")
    print(f"\nKinds:      {len(kk)} loaded")
    by_phase = {p: len(kinds_by_phase(p)) for p in ("legacy", "mvp", "phase2", "phase3")}
    print(f"  by phase: {by_phase}")
    print(f"\nEditions:   {len(ee)} loaded")
    for e in ee:
        print(f"  {e.get('id'):20}  {e.get('title','')}")
