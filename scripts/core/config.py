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
from dataclasses import dataclass
from pathlib import Path
from functools import lru_cache
from typing import Protocol, cast

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
    attribution: str | None = None  # 9th field, optional during migration

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


def note_attribution(tup: tuple) -> str | None:
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
    """Parse a scalar YAML value. Strings are JSON-quoted; integers,
    `null`, and bare `true`/`false` booleans are bare."""
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
    if s == "true":
        return True
    if s == "false":
        return False
    # ω.19.1 — recognise the inline empty-list literal so
    # `field: []` round-trips as an empty list rather than the
    # literal string "[]". `_patch_yaml_list_field` writes this
    # form when a list field becomes empty; without this branch
    # the string survives back into editions.yaml and
    # downstream consumers see a broken value.
    if s == "[]":
        return []
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


class _CachedLoader(Protocol):
    def __call__(self) -> list[dict]: ...
    def cache_clear(self) -> None: ...


@lru_cache(maxsize=4)
def _load_editions_cached(mtime_ns: int) -> list[dict]:
    """Cached parse of editions.yaml. The cache key includes mtime_ns, so
    runtime API edits invalidate automatically without an explicit clear."""
    p = _CONTENT / "editions.yaml"
    if not p.is_file():
        return []
    return _parse_yaml_records(p.read_text())


def _load_editions_uncached() -> list[dict]:
    p = _CONTENT / "editions.yaml"
    mtime_ns = p.stat().st_mtime_ns if p.is_file() else 0
    return _load_editions_cached(mtime_ns)


def clear_editions_cache() -> None:
    """Invalidate ``load_editions()`` — after in-process editions.yaml writes."""
    _load_editions_cached.cache_clear()


_load_editions_uncached.cache_clear = clear_editions_cache  # type: ignore[attr-defined]
load_editions: _CachedLoader = cast(_CachedLoader, _load_editions_uncached)


# Edition → factory cover-template stem (``<NN>_<design>_<colour>``). The
# ONE home (moved from generate_edition_covers so cover-free consumers —
# build_edition's catalog signature, the release-catalog generator — never
# import Pillow): batch regen, the /customize "reset to factory template"
# path, and the Downloads-catalog signature all read THIS map when
# editions.yaml hasn't recorded a ``cover_template``. The colour-to-tradition
# rationale lives in scripts/generate_edition_covers.py's module docstring.
EDITION_COVER_TEMPLATES = {
    "ethiopian-tewahedo": "05_missal_central_red",
    "catholic-study": "02_classical_corner_navy",
    "evangelical-reformed": "03_beadline_black",
    "jewish-study": "02_classical_corner_brown",
    "scholarly-academic": "03_beadline_forest",
    "eastern-orthodox": "01_ornate_leafy_red",
    "anglican-bcp": "03_beadline_navy",
    "lutheran-confessional": "02_classical_corner_black",
    "coptic-orthodox": "01_ornate_leafy_brown",
}
DEFAULT_COVER_TEMPLATE = "03_beadline_navy"


def edition_cover_template(edition_id):
    """The cover template stem for ``edition_id`` — the edition's recorded
    ``cover_template`` from editions.yaml when set, else its factory default
    from ``EDITION_COVER_TEMPLATES``, else the project-wide default."""
    ed = editions_by_id().get(edition_id, {})
    stem = str(ed.get("cover_template") or "").strip()
    if stem:
        return stem
    return EDITION_COVER_TEMPLATES.get(edition_id, DEFAULT_COVER_TEMPLATE)


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

# Single source of truth for valid kind/edition phase values, shared by
# validate_taxonomy + validate_schemas (C2.phase4 — they previously diverged:
# validate_schemas accepted a "phase4" that _PHASE_ORDER rejects at runtime).
# Derived from _PHASE_ORDER so the validators can never drift from what
# edition max_phase resolution actually accepts.
VALID_PHASES: frozenset[str] = frozenset(_PHASE_ORDER)

# Kinds whose content is LLM-drafted and shipped only after human review.
# Excluded by `enabled_kind_codes` unless the edition opts in with
# `enable_ai_notes: true` — a deliberate double opt-in (listing the kind in
# `enabled_kinds` is necessary but not sufficient). Single-element today; a
# frozenset so future AI-drafted kinds gate through one place.
AI_DRAFTED_KINDS: frozenset[str] = frozenset({"comm-ai"})


def enabled_kind_codes(edition: dict, all_kinds) -> set[str]:
    """Canonical resolver: the set of kind codes that ship in `edition`.

    THE single source of truth for "which kinds ship in this edition",
    delegated to by the matrix count grid
    (`matrix._enabled_kinds_for_edition`), the EPUB build
    (`build_edition.compute_enabled_kinds`), and `_kinds_in_edition` below.
    Before this existed those three drifted apart — the matrix lacked the
    phase gate and so over-counted vs. the actual build.

    A kind ships iff it survives every gate, in order:
      1. explicit `disabled_kinds` — always wins.
      2. phase gate — drop kinds whose `phase` is later than the edition's
         `max_phase` (default kind phase ``legacy`` always passes; an
         explicitly-enabled kind is STILL phase-gated, matching the build).
      3. AI double opt-in — drop `AI_DRAFTED_KINDS` unless `enable_ai_notes`
         is true (even if the kind is explicitly enabled).
      4. include if in explicit `enabled_kinds` OR its `category` is in
         `enabled_categories`.

    `all_kinds` is the kind list (dicts with `code`/`category`/`phase`),
    passed in for testability. Raises ValueError on an unknown `max_phase`.
    """
    enabled_cats = set(edition.get("enabled_categories") or [])
    explicit_enabled = set(edition.get("enabled_kinds") or [])
    explicit_disabled = set(edition.get("disabled_kinds") or [])
    allow_ai = bool(edition.get("enable_ai_notes"))

    max_phase = edition.get("max_phase")
    if max_phase and max_phase not in _PHASE_ORDER:
        raise ValueError(f"edition {edition.get('id')!r}: unknown max_phase {max_phase!r}")
    max_idx = _PHASE_ORDER[max_phase] if max_phase else max(_PHASE_ORDER.values())

    out: set[str] = set()
    for k in all_kinds:
        code = k.get("code")
        if code in explicit_disabled:
            continue
        phase = k.get("phase", "legacy")
        if phase != "legacy" and _PHASE_ORDER.get(phase, 99) > max_idx:
            continue
        if code in AI_DRAFTED_KINDS and not allow_ai:
            continue
        if code in explicit_enabled or k.get("category") in enabled_cats:
            out.add(code)
    return out


def category_baseline_kinds(edition: dict, all_kinds) -> set[str]:
    """The set of kinds a save-edition operation should treat as the BASELINE:
    every kind whose `category` is enabled AND which survives the phase + AI
    gates — but WITHOUT the explicit `enabled_kinds`/`disabled_kinds` layer
    (that layer is exactly what the save operation is recomputing).

    `api_save_edition` diffs the user's toggled set against this baseline to
    derive the explicit enable/disable lists. The baseline MUST be phase- and
    AI-gated (mint-9 #12): a `max_phase: phase2` edition never ships — nor shows
    in the UI — a phase3 kind, so such a kind must not fall into the computed
    `disabled_kinds`. Mirrors gates 2+3 of `enabled_kind_codes`, omitting gates
    1 and the explicit-enable half of gate 4.

    Raises ValueError on an unknown `max_phase` (same contract as
    `enabled_kind_codes`).
    """
    enabled_cats = set(edition.get("enabled_categories") or [])
    allow_ai = bool(edition.get("enable_ai_notes"))

    max_phase = edition.get("max_phase")
    if max_phase and max_phase not in _PHASE_ORDER:
        raise ValueError(f"edition {edition.get('id')!r}: unknown max_phase {max_phase!r}")
    max_idx = _PHASE_ORDER[max_phase] if max_phase else max(_PHASE_ORDER.values())

    out: set[str] = set()
    for k in all_kinds:
        code = k.get("code")
        if k.get("category") not in enabled_cats:
            continue
        phase = k.get("phase", "legacy")
        if phase != "legacy" and _PHASE_ORDER.get(phase, 99) > max_idx:
            continue
        if code in AI_DRAFTED_KINDS and not allow_ai:
            continue
        out.add(code)
    return out


def _phase_ai_ok_kinds(edition: dict, all_kinds) -> set[str]:
    """Kinds that pass the HARD gates (phase + AI), ignoring category/enable/
    disable. A family-level per-book/chapter ON may only enable a kind in this
    set — it can never bulk-enable a phase-gated or AI kind the edition forbids.
    """
    allow_ai = bool(edition.get("enable_ai_notes"))
    max_phase = edition.get("max_phase")
    if max_phase and max_phase not in _PHASE_ORDER:
        raise ValueError(f"edition {edition.get('id')!r}: unknown max_phase {max_phase!r}")
    max_idx = _PHASE_ORDER[max_phase] if max_phase else max(_PHASE_ORDER.values())
    out: set[str] = set()
    for k in all_kinds:
        phase = k.get("phase", "legacy")
        if phase != "legacy" and _PHASE_ORDER.get(phase, 99) > max_idx:
            continue
        if k.get("code") in AI_DRAFTED_KINDS and not allow_ai:
            continue
        out.add(k.get("code"))
    return out


def enabled_kind_codes_for(edition: dict, all_kinds, book: str, chapter=None) -> set[str]:
    """Per-coordinate symbol resolution (Phase ρ.3).

    Returns the set of kind codes enabled for ``(book, chapter)``, layering the
    book- and chapter-level signed tokens over the edition default
    (``enabled_kind_codes``). Most-specific-wins:
        chapter-kind ▸ chapter-category ▸ book-kind ▸ book-category ▸ edition default
    OFF beats ON at equal specificity. Phase/AI gates bound the family levels.

    With NO book/chapter token for this coordinate, returns
    ``enabled_kind_codes(edition, all_kinds)`` UNCHANGED (the invariant every
    existing caller relies on).
    """
    from scripts.build_edition import decode_per_book_tokens, decode_per_chapter_tokens

    base = enabled_kind_codes(edition, all_kinds)

    on_book = set(decode_per_book_tokens(edition.get("note_families_on_per_book")).get(book, []))
    off_book = set(decode_per_book_tokens(edition.get("note_families_off_per_book")).get(book, []))
    ch_key = f"{book}:{chapter}" if chapter is not None else None
    per_ch_on = decode_per_chapter_tokens(edition.get("note_families_on_per_chapter"))
    per_ch_off = decode_per_chapter_tokens(edition.get("note_families_off_per_chapter"))
    on_ch = set(per_ch_on.get(ch_key, [])) if ch_key else set()
    off_ch = set(per_ch_off.get(ch_key, [])) if ch_key else set()

    if not (on_book or off_book or on_ch or off_ch):
        return base  # fast path — invariant: identical to the edition-wide resolver

    gate_ok = _phase_ai_ok_kinds(edition, all_kinds)
    out: set[str] = set()
    for k in all_kinds:
        code = k.get("code")
        cat = k.get("category")
        # most-specific-wins; OFF checked before ON at each step
        decision = None  # True=ON, False=OFF, None=inherit
        for on_set, off_set, key in (
            (on_ch, off_ch, code),
            (on_ch, off_ch, cat),
            (on_book, off_book, code),
            (on_book, off_book, cat),
        ):
            if key in off_set:
                decision = False
                break
            if key in on_set:
                decision = True
                break
        if decision is False:
            continue
        if decision is True:
            if code in gate_ok:
                out.add(code)
        else:  # inherit
            if code in base:
                out.add(code)
    return out


def _kinds_in_edition(edition_id):
    """Return list of kind dicts visible in a given edition profile.

    Thin wrapper over `enabled_kind_codes` (the canonical resolver) that
    resolves the edition by id and preserves kinds.yaml declaration order.
    """
    eds = editions_by_id()
    if edition_id not in eds:
        raise KeyError(f"Unknown edition id {edition_id!r}. Known: {sorted(eds)}")
    ed = eds[edition_id]
    all_kinds = load_kinds()
    enabled = enabled_kind_codes(ed, all_kinds)
    return [k for k in all_kinds if k.get("code") in enabled]


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
        print(f"  {e.get('id'):20}  {e.get('title', '')}")
