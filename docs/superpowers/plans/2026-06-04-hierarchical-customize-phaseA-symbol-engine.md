# Hierarchical Customization — Phase A: Symbol Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-coordinate note-symbol resolution across four levels (Bible → book → chapter → individual note), resolving to the build's existing ref-id disable set, byte-identical when nothing is overridden.

**Architecture:** Two new signed-token per-scope fields each at book and chapter level + a new `enabled_note_ids` force-on list, resolved by one new pure function `config.enabled_kind_codes_for(edition, all_kinds, book, chapter)` layered on the existing `enabled_kind_codes`. At build time a new corpus walk (`compute_symbol_disabled_html_ref_ids`, short-circuiting to empty when nothing is overridden) turns "this family is off at this coordinate" into concrete HTML ref-ids, unioned into the `disabled_html_ref_ids` the build already strips; force-on ref-ids are subtracted last. `filter_html` is **not** modified.

**Tech Stack:** Python 3.12 (full interpreter path, NOT the Windows Store stub), pytest, the project's `scripts/core/config.py` + `scripts/build_edition.py`. No new dependencies.

**Status:** IN PROGRESS 2026-06-04 — ready to execute. Phase A of the hierarchical-customization spec (`docs/superpowers/specs/2026-06-04-hierarchical-edition-customization-design.md`); 8 TDD tasks; byte-stability gate (9 KJV editions identical) = the ship bar. Phase B (popup hierarchy) + Phase C (`/build-my-bible` navigator) follow in their own plans.

---

## Pre-flight (read once before starting)

- Spec: `docs/superpowers/specs/2026-06-04-hierarchical-edition-customization-design.md` (§3–§5, §9, §11).
- Pattern sources to mirror (read them):
  - `scripts/build_edition.py:178-241` — `decode_per_book_traditions` / `encode_per_book_traditions` (the encode/decode template).
  - `scripts/build_edition.py:110-155` — `_iter_note_ref_traditions` (the corpus-walk template; note tuple = `(ch, vs, suffix, anchor, kind, …)`, i.e. `tup[0]=ch, tup[1]=vs, tup[2]=suffix, tup[4]=kind`; ref-id = `f"ref-{prefix}{ch:02d}{vs:02d}{suffix}"`; `prefix = book["id_prefix"] or book["bxx"]`).
  - `scripts/build_edition.py:264-296` — `compute_tradition_disabled_html_ref_ids` (the compute template; short-circuits empty).
  - `scripts/core/config.py:393-438` — `enabled_kind_codes` (the resolver to extend; 4 gates).
  - `scripts/core/config.py:441-476` — `category_baseline_kinds` (gates 2+3 only; template for the phase/AI helper).
  - `scripts/build_edition.py:2740-2776` — `build_one`'s disable-set assembly (the integration point).
  - `scripts/build_edition.py:2967-2974` — the per-file `filter_html(text, disabled, disabled_html_ref_ids, …)` call (change `disabled` → `disabled_kinds_for_filter` here).
  - `scripts/build_edition.py:1081-1132` — `filter_html` (READ ONLY; do not modify).

**Windows env (every test run):** `$env:PYTHONUTF8="1"`; use the full python path (not `python`/`python3` Store stub — `py -3` or the pythoncore path); add `--basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"` to every pytest run; `$env:PYTHONPATH="C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4"` when running from outside the repo dir. Run **one test file at a time** under RAM pressure.

**Field reference (all default absent ⇒ byte-identical):**
| Field | Level | Disk format | Meaning |
|-------|-------|-------------|---------|
| `note_families_on_per_book` | book | `"gen=xref,comm-patristic"` | force these families/kinds ON for the book |
| `note_families_off_per_book` | book | `"exo=xref"` | force OFF for the book |
| `note_families_on_per_chapter` | chapter | `"gen:1=xref"` | force ON for book:chapter |
| `note_families_off_per_chapter` | chapter | `"exo:3=comm"` | force OFF for book:chapter |
| `enabled_note_ids` | note | `"exo:3:2:comm-patristic"` | force ONE note ON (absolute finest) |
| `disabled_note_ids` | note | `"gen:1:1a:xref"` | force ONE note OFF (**already exists**) |

A token is a **category id** (e.g. `xref`, `comm`) OR a **kind code** (e.g. `comm-patristic`). Precedence (most-specific-wins): chapter-kind ▸ chapter-category ▸ book-kind ▸ book-category ▸ edition default; OFF beats ON at equal specificity; phase/AI gates bound the family levels; `enabled_note_ids` (note force-on) overrides everything.

---

## Task 1: Encode/decode for per-book + per-chapter symbol tokens

**Files:**
- Modify: `scripts/build_edition.py` (add four functions after `encode_per_book_traditions`, near line 241)
- Test: `tests/test_hierarchical_symbols.py` (new)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_hierarchical_symbols.py
import importlib
be = importlib.import_module("scripts.build_edition")


class TestPerBookTokens:
    def test_decode_book_tokens_basic(self):
        raw = ["gen=xref,comm-patristic", "exo="]
        assert be.decode_per_book_tokens(raw) == {"gen": ["xref", "comm-patristic"], "exo": []}

    def test_decode_book_tokens_none_and_dict(self):
        assert be.decode_per_book_tokens(None) == {}
        assert be.decode_per_book_tokens({"gen": ["xref"]}) == {"gen": ["xref"]}

    def test_encode_book_tokens_sorts_canonical_and_filters_unknown(self):
        # exo precedes gen alphabetically but FOLLOWS it canonically; unknown token dropped
        out = be.encode_per_book_tokens({"exo": ["xref"], "gen": ["xref", "not-a-real-token"]})
        assert out == ["gen=xref", "exo=xref"]

    def test_book_tokens_roundtrip(self):
        d = {"gen": ["xref"], "psa": ["comm-patristic"]}
        assert be.decode_per_book_tokens(be.encode_per_book_tokens(d)) == d


class TestPerChapterTokens:
    def test_decode_chapter_tokens_basic(self):
        raw = ["gen:1=xref", "exo:3=comm"]
        assert be.decode_per_chapter_tokens(raw) == {"gen:1": ["xref"], "exo:3": ["comm"]}

    def test_encode_chapter_tokens_sorts_canonical_then_numeric(self):
        out = be.encode_per_chapter_tokens({"gen:10": ["xref"], "gen:2": ["xref"], "exo:1": ["xref"]})
        # gen before exo (canonical book order); within gen, chapter 2 before 10 (numeric, not lexical)
        assert out == ["gen:2=xref", "gen:10=xref", "exo:1=xref"]

    def test_chapter_tokens_roundtrip(self):
        d = {"gen:1": ["xref"], "gen:50": ["comm-patristic"]}
        assert be.decode_per_chapter_tokens(be.encode_per_chapter_tokens(d)) == d
```

- [ ] **Step 2: Run it to verify it fails**

Run: `$env:PYTHONUTF8="1"; <python> -m pytest tests/test_hierarchical_symbols.py -v --basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`
Expected: FAIL — `AttributeError: module 'scripts.build_edition' has no attribute 'decode_per_book_tokens'`.

- [ ] **Step 3: Implement the four functions**

Insert into `scripts/build_edition.py` after `encode_per_book_traditions` (after line 241). The token validity set is `category ids ∪ kind codes`.

```python
def _valid_symbol_tokens() -> set[str]:
    """The set of legal per-scope symbol tokens: category ids ∪ kind codes."""
    from scripts.core import config as _cfg

    cats = {c.get("id") for c in _cfg.load_categories()}
    kinds = {k.get("code") for k in _cfg.load_kinds()}
    return {t for t in (cats | kinds) if t}


def decode_per_book_tokens(raw) -> dict[str, list[str]]:
    """Decode ``note_families_{on,off}_per_book`` on-disk format.

    Flat list of ``"<book>=<tok1>,<tok2>"`` strings (tokens are a category
    id or a kind code). Empty value (``"gen="``) is meaningful: an explicit
    empty override. Accepts None / [] / {} / list[str] / dict. Mirrors
    ``decode_per_book_traditions``.
    """
    if raw is None or raw == [] or raw == {}:
        return {}
    if isinstance(raw, dict):
        return {str(k): list(v or []) for k, v in raw.items()}
    out: dict[str, list[str]] = {}
    for entry in raw:
        if not isinstance(entry, str) or "=" not in entry:
            continue
        code, blob = entry.split("=", 1)
        code = code.strip()
        if not code:
            continue
        out[code] = [s.strip() for s in blob.split(",") if s.strip()] if blob.strip() else []
    return out


def encode_per_book_tokens(per_book: dict[str, list[str]]) -> list[str]:
    """Inverse of decode_per_book_tokens. Sorts by canonical book order
    (§6.1); drops unknown tokens (validate-at-write, like traditions)."""
    if not per_book:
        return []
    from scripts.core import config as _cfg

    valid = _valid_symbol_tokens()
    book_order = list(_cfg.books_by_code().keys())
    rank = {code: i for i, code in enumerate(book_order)}
    out: list[str] = []
    for code, toks in sorted(per_book.items(), key=lambda it: (rank.get(it[0], len(book_order) + 1), it[0])):
        clean = [t for t in (toks or []) if t in valid]
        out.append(f"{code}={','.join(clean)}")
    return out


def decode_per_chapter_tokens(raw) -> dict[str, list[str]]:
    """Decode ``note_families_{on,off}_per_chapter``. Key is ``"<book>:<ch>"``;
    otherwise identical to decode_per_book_tokens."""
    if raw is None or raw == [] or raw == {}:
        return {}
    if isinstance(raw, dict):
        return {str(k): list(v or []) for k, v in raw.items()}
    out: dict[str, list[str]] = {}
    for entry in raw:
        if not isinstance(entry, str) or "=" not in entry:
            continue
        key, blob = entry.split("=", 1)
        key = key.strip()
        if not key:
            continue
        out[key] = [s.strip() for s in blob.split(",") if s.strip()] if blob.strip() else []
    return out


def encode_per_chapter_tokens(per_chapter: dict[str, list[str]]) -> list[str]:
    """Inverse of decode_per_chapter_tokens. Sorts by canonical book order
    then NUMERIC chapter (so gen:2 precedes gen:10); drops unknown tokens."""
    if not per_chapter:
        return []
    from scripts.core import config as _cfg

    valid = _valid_symbol_tokens()
    book_order = list(_cfg.books_by_code().keys())
    rank = {code: i for i, code in enumerate(book_order)}

    def _sort_key(item):
        key = item[0]
        book, _, ch = key.partition(":")
        try:
            ch_n = int(ch)
        except ValueError:
            ch_n = 1 << 30
        return (rank.get(book, len(book_order) + 1), book, ch_n)

    out: list[str] = []
    for key, toks in sorted(per_chapter.items(), key=_sort_key):
        clean = [t for t in (toks or []) if t in valid]
        out.append(f"{key}={','.join(clean)}")
    return out
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `$env:PYTHONUTF8="1"; <python> -m pytest tests/test_hierarchical_symbols.py -v --basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`
Expected: PASS (10 tests). Note: `test_encode_*_filters_unknown` relies on `xref`/`comm` being real category ids and `comm-patristic` a real kind — they are (15 categories / 72 kinds).

- [ ] **Step 5: Commit**

```
pwsh -File save.ps1 -Message "ρ.3 Phase A-1: per-book + per-chapter symbol-token encode/decode (TDD)"
```
(Local commit only here; the full 5-leg save is Task 8. `save.ps1` runs the pre-commit hook — `ruff format --check` + lint + mypy. Run `<python> -m ruff format scripts/build_edition.py tests/test_hierarchical_symbols.py` first.)

---

## Task 2: The per-coordinate resolver `enabled_kind_codes_for`

**Files:**
- Modify: `scripts/core/config.py` (add after `category_baseline_kinds`, near line 476)
- Test: `tests/test_hierarchical_symbols.py` (append)

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_hierarchical_symbols.py
import scripts.core.config as config

KINDS = [
    {"code": "xref-citation", "category": "xref", "phase": "legacy"},
    {"code": "comm-patristic", "category": "comm", "phase": "legacy"},
    {"code": "comm-rabbinic", "category": "comm", "phase": "legacy"},
    {"code": "future-kind", "category": "comm", "phase": "phase3"},
    {"code": "comm-ai", "category": "comm", "phase": "legacy"},
]


def _ed(**kw):
    base = {"id": "t", "enabled_categories": [], "enabled_kinds": [], "disabled_kinds": []}
    base.update(kw)
    return base


class TestResolverPrecedence:
    def test_no_override_equals_base(self):
        ed = _ed(enabled_categories=["xref"])
        assert config.enabled_kind_codes_for(ed, KINDS, "gen", 1) == config.enabled_kind_codes(ed, KINDS)

    def test_book_off_removes_family(self):
        ed = _ed(enabled_categories=["xref"], note_families_off_per_book=["exo=xref"])
        assert "xref-citation" in config.enabled_kind_codes_for(ed, KINDS, "gen", 1)
        assert "xref-citation" not in config.enabled_kind_codes_for(ed, KINDS, "exo", 3)

    def test_book_on_reenables_edition_disabled_family(self):
        ed = _ed(enabled_categories=[], note_families_on_per_book=["gen=xref"])  # xref OFF edition-wide
        assert "xref-citation" not in config.enabled_kind_codes_for(ed, KINDS, "exo", 1)
        assert "xref-citation" in config.enabled_kind_codes_for(ed, KINDS, "gen", 1)

    def test_chapter_beats_book(self):
        ed = _ed(enabled_categories=["comm"], note_families_off_per_book=["psa=comm"],
                 note_families_on_per_chapter=["psa:23=comm"])
        assert "comm-patristic" not in config.enabled_kind_codes_for(ed, KINDS, "psa", 1)
        assert "comm-patristic" in config.enabled_kind_codes_for(ed, KINDS, "psa", 23)

    def test_kind_token_beats_category_token(self):
        ed = _ed(enabled_categories=["comm"], note_families_off_per_book=["psa=comm"],
                 note_families_on_per_book=["psa=comm-patristic"])
        got = config.enabled_kind_codes_for(ed, KINDS, "psa", 1)
        assert "comm-patristic" in got       # kind ON wins over category OFF
        assert "comm-rabbinic" not in got    # category OFF still applies to the rest

    def test_off_beats_on_at_equal_specificity(self):
        ed = _ed(enabled_categories=[], note_families_on_per_book=["gen=comm-patristic"],
                 note_families_off_per_book=["gen=comm-patristic"])
        assert "comm-patristic" not in config.enabled_kind_codes_for(ed, KINDS, "gen", 1)

    def test_phase_gate_not_bypassed_by_family_on(self):
        ed = _ed(max_phase="mvp", note_families_on_per_book=["gen=comm"])  # future-kind is phase3
        assert "future-kind" not in config.enabled_kind_codes_for(ed, KINDS, "gen", 1)
        assert "comm-patristic" in config.enabled_kind_codes_for(ed, KINDS, "gen", 1)

    def test_ai_gate_not_bypassed_by_family_on(self):
        ed = _ed(enable_ai_notes=False, note_families_on_per_book=["gen=comm-ai"])
        assert "comm-ai" not in config.enabled_kind_codes_for(ed, KINDS, "gen", 1)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `$env:PYTHONUTF8="1"; <python> -m pytest tests/test_hierarchical_symbols.py::TestResolverPrecedence -v --basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`
Expected: FAIL — `AttributeError: module 'scripts.core.config' has no attribute 'enabled_kind_codes_for'`.

- [ ] **Step 3: Implement the resolver**

Insert into `scripts/core/config.py` after `category_baseline_kinds` (after line 476):

```python
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
            (on_ch, off_ch, code), (on_ch, off_ch, cat),
            (on_book, off_book, code), (on_book, off_book, cat),
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `$env:PYTHONUTF8="1"; <python> -m pytest tests/test_hierarchical_symbols.py::TestResolverPrecedence -v --basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`
Expected: PASS (8 tests).

- [ ] **Step 5: Guard the tri-path invariant against real editions**

```python
# append to tests/test_hierarchical_symbols.py
class TestResolverInvariant:
    def test_real_editions_unchanged_with_no_override(self):
        all_kinds = config.load_kinds()
        for ed in config.load_editions():
            base = config.enabled_kind_codes(ed, all_kinds)
            assert config.enabled_kind_codes_for(ed, all_kinds, "gen", 1) == base
            assert config.enabled_kind_codes_for(ed, all_kinds, "rev") == base
```

Run: same file, `::TestResolverInvariant`. Expected: PASS (no committed edition has per-book/chapter symbol tokens yet, so every coordinate equals the base).

- [ ] **Step 6: Commit**

```
<python> -m ruff format scripts/core/config.py tests/test_hierarchical_symbols.py
pwsh -File save.ps1 -Message "ρ.3 Phase A-2: enabled_kind_codes_for per-coordinate resolver + invariant (TDD)"
```

---

## Task 3: Richer corpus iterator `_iter_note_ref_symbols`

**Files:**
- Modify: `scripts/build_edition.py` (add after `_iter_note_ref_traditions`, near line 156)
- Test: `tests/test_hierarchical_symbols.py` (append)

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_hierarchical_symbols.py
class TestCorpusIterator:
    def test_yields_8_tuple_with_chapter_kind_category(self):
        rows = list(be._iter_note_ref_symbols())
        assert rows, "expected the on-disk corpus to yield notes"
        ref_id, note_id, book, chapter, verse, suffix, kind, category = rows[0]
        assert ref_id.startswith("ref-")
        assert note_id.count(":") == 3            # book:ch:vs[suffix]:kind
        assert isinstance(chapter, int) and isinstance(verse, int)
        assert note_id == f"{book}:{chapter}:{verse}{suffix}:{kind}"

    def test_note_id_reparses_to_same_ref_id(self):
        from scripts.web_helpers import html_ref_id_from_note_id
        for ref_id, note_id, *_ in list(be._iter_note_ref_symbols())[:200]:
            assert html_ref_id_from_note_id(note_id) == ref_id
```

- [ ] **Step 2: Run it to verify it fails**

Run: `::TestCorpusIterator`. Expected: FAIL — `module 'scripts.build_edition' has no attribute '_iter_note_ref_symbols'`.

- [ ] **Step 3: Implement the iterator** (mirror `_iter_note_ref_traditions` at :110-155)

Insert after `_iter_note_ref_traditions` (after line 155):

```python
def _iter_note_ref_symbols():
    """Walk every note tuple on disk and yield
    ``(ref_id, note_id, book_code, chapter, verse, suffix, kind, category)``.

    Sibling of ``_iter_note_ref_traditions`` that surfaces the chapter/verse/
    kind/category baked into each note, for the Phase-ρ.3 per-coordinate symbol
    resolver. ``note_id`` is the canonical ``book:ch:vs[suffix]:kind`` form;
    ``ref_id`` is the compact HTML id ``ref-<prefix><cc><vv><suffix>`` (same
    Strategy-B ``id_prefix``→``bxx`` fallback as the tradition walk).
    """
    from scripts.core.notes_io import load_notes

    books_idx = config.books_by_code()
    cat_by_kind = {k.get("code"): k.get("category") for k in config.load_kinds()}
    notes_dir = REPO_ROOT / "content" / "notes"
    for book_path in sorted(notes_dir.glob("*.py")):
        if book_path.stem == "__init__" or book_path.stem.startswith("_"):
            continue
        book_code = book_path.stem
        book = books_idx.get(book_code) or {}
        prefix = book.get("id_prefix") or book.get("bxx")
        if not prefix:
            continue
        for tup in load_notes(book_path) or []:
            if not isinstance(tup, tuple) or len(tup) < 8:
                continue
            try:
                ch_i = int(tup[0])
                vs_i = int(tup[1])
            except (TypeError, ValueError):
                continue
            suffix = tup[2] or ""
            kind = tup[4]
            ref_id = f"ref-{prefix}{ch_i:02d}{vs_i:02d}{suffix}"
            note_id = f"{book_code}:{ch_i}:{vs_i}{suffix}:{kind}"
            yield ref_id, note_id, book_code, ch_i, vs_i, suffix, kind, cat_by_kind.get(kind)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `::TestCorpusIterator`. Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```
<python> -m ruff format scripts/build_edition.py tests/test_hierarchical_symbols.py
pwsh -File save.ps1 -Message "ρ.3 Phase A-3: _iter_note_ref_symbols corpus iterator (TDD)"
```

---

## Task 4: `_symbol_overridden_kinds` + `compute_symbol_disabled_html_ref_ids`

**Files:**
- Modify: `scripts/build_edition.py` (add after `compute_tradition_disabled_html_ref_ids`, near line 296; add a module-level `_NOTE_ID_RE` near the top imports)
- Test: `tests/test_hierarchical_symbols.py` (append)

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_hierarchical_symbols.py
ALL_KINDS = None  # set in tests via config.load_kinds()


class TestSymbolCompute:
    def test_overridden_kinds_from_tokens_and_force_on(self):
        ed = _ed(note_families_off_per_book=["psa=comm"],            # category → all comm kinds
                 note_families_on_per_chapter=["gen:1=xref-citation"],  # one kind
                 enabled_note_ids=["exo:3:2:comm-rabbinic"])           # one kind
        ak = config.load_kinds()
        ov = be._symbol_overridden_kinds(ed, ak)
        comm_kinds = {k["code"] for k in ak if k.get("category") == "comm"}
        assert comm_kinds <= ov                 # category token expanded
        assert "xref-citation" in ov            # kind token
        assert "comm-rabbinic" in ov            # force-on kind

    def test_compute_short_circuits_empty(self):
        ed = _ed(enabled_categories=["xref"])   # no per-book/chapter token, no enabled_note_ids
        assert be.compute_symbol_disabled_html_ref_ids(ed, config.load_kinds(), set()) == set()

    def test_compute_disables_off_coordinate_only(self):
        # xref ON edition-wide, OFF in exo only → exo xref ref-ids disabled, gen xref ref-ids not
        ed = _ed(enabled_categories=["xref"], note_families_off_per_book=["exo=xref"])
        ak = config.load_kinds()
        ov = be._symbol_overridden_kinds(ed, ak)
        disabled = be.compute_symbol_disabled_html_ref_ids(ed, ak, ov)
        exo_prefix = config.books_by_code()["exo"].get("id_prefix") or config.books_by_code()["exo"].get("bxx")
        gen_prefix = config.books_by_code()["gen"].get("id_prefix") or config.books_by_code()["gen"].get("bxx")
        # at least one exo ref-id disabled; no gen ref-id disabled (xref still ON in gen)
        assert any(r.startswith(f"ref-{exo_prefix}") for r in disabled)
        assert not any(r.startswith(f"ref-{gen_prefix}") for r in disabled)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `::TestSymbolCompute`. Expected: FAIL — `_symbol_overridden_kinds` / `compute_symbol_disabled_html_ref_ids` not defined.

- [ ] **Step 3: Implement** — add `_NOTE_ID_RE` near the top of `scripts/build_edition.py` (after the `import re`), then the two functions after `compute_tradition_disabled_html_ref_ids` (after line 296):

```python
# near the top-of-file constants:
_NOTE_ID_RE = re.compile(r"^([a-z0-9]+):(\d+):(\d+)([a-z]*):([a-z][a-z0-9-]*)$")
```

```python
def _symbol_overridden_kinds(edition: dict, all_kinds) -> set[str]:
    """Kind codes touched by ANY per-book/per-chapter symbol token (category
    tokens expanded to their kinds) ∪ kinds named by ``enabled_note_ids``.
    These are resolved at ref-id granularity (so a per-coordinate ON can
    re-include them); all OTHER edition-disabled kinds keep the efficient
    whole-kind strip. Cheap — no corpus walk."""
    cat_to_kinds: dict[str, set[str]] = {}
    valid_kinds: set[str] = set()
    for k in all_kinds:
        code = k.get("code")
        valid_kinds.add(code)
        cat_to_kinds.setdefault(k.get("category"), set()).add(code)

    out: set[str] = set()

    def _absorb(tokens):
        for t in tokens:
            if t in valid_kinds:
                out.add(t)
            elif t in cat_to_kinds:
                out.update(cat_to_kinds[t])

    for field in ("note_families_on_per_book", "note_families_off_per_book"):
        for toks in decode_per_book_tokens(edition.get(field)).values():
            _absorb(toks)
    for field in ("note_families_on_per_chapter", "note_families_off_per_chapter"):
        for toks in decode_per_chapter_tokens(edition.get(field)).values():
            _absorb(toks)
    for nid in edition.get("enabled_note_ids") or []:
        m = _NOTE_ID_RE.match(nid)
        if m:
            out.add(m.group(5))
    return out


def compute_symbol_disabled_html_ref_ids(edition: dict, all_kinds, overridden_kinds: set[str]) -> set[str]:
    """Phase ρ.3 — ref-ids of notes whose kind resolves OFF at their coordinate
    under the per-book/per-chapter symbol overrides. Mirrors
    ``compute_tradition_disabled_html_ref_ids``. Only processes notes whose kind
    is in ``overridden_kinds`` (non-overridden kinds are handled by the edition-
    wide whole-kind strip). SHORT-CIRCUITS to an empty set when nothing is
    overridden, so standard builds never walk the corpus.

    Individual ``disabled_note_ids`` / ``enabled_note_ids`` are applied in
    ``build_one`` (force-on is subtracted from the final set), not here.
    """
    if not overridden_kinds:
        return set()
    from scripts.core.config import enabled_kind_codes_for

    out: set[str] = set()
    cache: dict[tuple, set[str]] = {}
    for ref_id, _note_id, book, chapter, _verse, _suffix, kind, _cat in _iter_note_ref_symbols():
        if kind not in overridden_kinds:
            continue
        key = (book, chapter)
        enabled = cache.get(key)
        if enabled is None:
            enabled = enabled_kind_codes_for(edition, all_kinds, book, chapter)
            cache[key] = enabled
        if kind not in enabled:
            out.add(ref_id)
    return out
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `::TestSymbolCompute`. Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```
<python> -m ruff format scripts/build_edition.py tests/test_hierarchical_symbols.py
pwsh -File save.ps1 -Message "ρ.3 Phase A-4: overridden-kinds + compute_symbol_disabled_html_ref_ids (TDD)"
```

---

## Task 5: Wire into `build_one` (force-on, union, whole-kind narrowing)

**Files:**
- Modify: `scripts/build_edition.py` — `build_one` disable-set block (~:2740-2776) and the per-file `filter_html` call (~:2969-2974)

- [ ] **Step 1: Write the failing integration test** (uses the real flagship build path with an injected edition)

```python
# append to tests/test_hierarchical_symbols.py
import re as _re


def _ref_ids_in(html: str) -> set[str]:
    return set(_re.findall(r'id="(ref-[a-z0-9]+)"', html))
```

This test is exercised through Task 6's `build_one` harness; Step 1 here is the **code-reading checkpoint**: open `scripts/build_edition.py:2740-2776` and confirm the current shape:
```python
disabled_note_ids = list(edition.get("disabled_note_ids") or [])
disabled_html_ref_ids: set[str] = set()
if disabled_note_ids: ...        # :2745-2763  builds ref-ids from note-ids
disabled_html_ref_ids |= compute_tradition_disabled_html_ref_ids(edition)   # :2768
disabled_html_ref_ids |= compute_time_filtered_html_ref_ids(edition)        # :2776
```
and the per-file call at :2969-2974 passes `disabled` (from `enabled, disabled = compute_enabled_kinds(...)` at :2738).

- [ ] **Step 2: Edit the disable-set block.** Replace the existing note-id translation loop body to reuse `_NOTE_ID_RE`, then append the Phase-ρ.3 wiring. After the existing `disabled_html_ref_ids |= compute_time_filtered_html_ref_ids(edition)` line (:2776), insert:

```python
    # Phase ρ.3: per-book / per-chapter symbol overrides → ref-ids, and the
    # enabled_note_ids force-on (absolute finest — subtracted last).
    overridden_kinds = _symbol_overridden_kinds(edition, all_kinds)
    disabled_html_ref_ids |= compute_symbol_disabled_html_ref_ids(edition, all_kinds, overridden_kinds)

    force_on_ref_ids: set[str] = set()
    for nid in edition.get("enabled_note_ids") or []:
        m = _NOTE_ID_RE.match(nid)
        if not m:
            continue
        book = books_idx.get(m.group(1)) or {}
        prefix = book.get("id_prefix") or book.get("bxx")
        if not prefix:
            continue
        force_on_ref_ids.add(f"ref-{prefix}{int(m.group(2)):02d}{int(m.group(3)):02d}{m.group(4)}")
    disabled_html_ref_ids -= force_on_ref_ids

    # Whole-kind strip must NOT remove a kind that has a per-coordinate override
    # (else a per-book/chapter ON could never re-include it). Overridden kinds
    # are handled at ref-id granularity above.
    disabled_kinds_for_filter = disabled - overridden_kinds
```
(`books_idx` is already in scope from the existing block at :2746; if the linter flags it out of scope, add `books_idx = config.books_by_code()` at the top of the new block.)

- [ ] **Step 3: Point `filter_html` at the narrowed set.** At :2969-2974 change the second arg from `disabled` to `disabled_kinds_for_filter`:

```python
            new_text, counts = filter_html(
                text,
                disabled_kinds_for_filter,
                disabled_html_ref_ids,
                verse_popups_enabled=verse_popups_enabled,
            )
```

- [ ] **Step 4: DRY the existing note-id loop (optional, same commit).** The existing inline regex at the old :2747 (`re.compile(r"^([a-z0-9]+):...")`) is now duplicated by the module-level `_NOTE_ID_RE`. Replace the inline `note_id_re = re.compile(...)` with `note_id_re = _NOTE_ID_RE` so there is one source of truth.

- [ ] **Step 5: Run the existing build + symbol suites to confirm nothing regressed**

Run: `$env:PYTHONUTF8="1"; <python> -m pytest tests/test_hierarchical_symbols.py tests/test_build_cache.py -v --basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`
Expected: PASS (the symbol suite + the build-cache suite; no behavioural change yet since no committed edition sets the new fields).

- [ ] **Step 6: Commit**

```
<python> -m ruff format scripts/build_edition.py
pwsh -File save.ps1 -Message "ρ.3 Phase A-5: wire per-coordinate symbol overrides + force-on into build_one"
```

---

## Task 6: Build-integration tests (spec §9 examples)

**Files:**
- Test: `tests/test_hierarchical_symbols.py` (append) — drive `build_one` on a temp edition and assert which ref-ids survive in the built HTML.

- [ ] **Step 1: Write the failing tests.** Build a minimal edition that includes the `xref`/`comm` categories, inject the per-coordinate fields, run `build_one`, unzip the EPUB, and check surviving `ref-` ids per book/chapter. (Reuse the existing build-test harness — model on `tests/test_byte_stability_gate.py`'s build helper; it already knows how to invoke `build_one` into a temp dir and read entries.)

```python
class TestBuildIntegration:
    def test_example1_xref_off_global_on_in_gen1(self, tmp_path):
        # spec §9 #1 — xref OFF edition-wide, ON only in gen:1
        from tests._build_helpers import build_edition_html  # see Step 3
        html = build_edition_html(
            enabled_categories=["comm"],                 # xref NOT enabled
            note_families_on_per_chapter=["gen:1=xref"],
        )
        gen = config.books_by_code()["gen"]
        gp = gen.get("id_prefix") or gen.get("bxx")
        survivors = _ref_ids_in(html["gen"])
        # a gen:1 xref ref-id survives; a gen:2 xref ref-id does not
        assert any(r.startswith(f"ref-{gp}01") for r in survivors)

    def test_example2_commentary_book_on_chapter_off_one_forced_on(self, tmp_path):
        from tests._build_helpers import build_edition_html
        html = build_edition_html(
            enabled_categories=["comm"],
            note_families_off_per_chapter=["psa:23=comm"],
            enabled_note_ids=["psa:23:1:comm-patristic"],   # NOTE: use a real psa 23:1 comm note id
        )
        psa = config.books_by_code()["psa"]
        pp = psa.get("id_prefix") or psa.get("bxx")
        survivors = _ref_ids_in(html["psa"])
        assert f"ref-{pp}2301" in survivors        # the forced-on note survives
```

- [ ] **Step 2: Run it to verify it fails**

Run: `::TestBuildIntegration`. Expected: FAIL — `tests._build_helpers` missing.

- [ ] **Step 3: Add the build helper** `tests/_build_helpers.py` — a thin wrapper that writes a temp edition dict, runs `build_one` into a `tmp_path`, unzips, and returns `{book_code: html_text}` for the books with notes. Model it on the build invocation in `tests/test_byte_stability_gate.py` (reuse its EPUB-read code; do not duplicate the zip logic — import its helper if one exists). Verify the chosen example note-ids exist first by grepping `_iter_note_ref_symbols()` output for a real `psa:23:1:comm-*` and a `gen:1:*:xref-*`; if the exact ids differ, adjust the test constants to real ones (the test must assert against notes that actually exist on disk).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `::TestBuildIntegration`. Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```
<python> -m ruff format tests/test_hierarchical_symbols.py tests/_build_helpers.py
pwsh -File save.ps1 -Message "ρ.3 Phase A-6: build-integration tests for the §9 worked examples"
```

---

## Task 7: Byte-stability proof (the ship bar)

**Files:** none changed — this task PROVES the 9 KJV editions are byte-identical.

- [ ] **Step 1: Regenerate + diff `epub_working/`.** The symbol engine does not touch `epub_working/`, but confirm:

Run: `$env:PYTHONUTF8="1"; git -C "C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4" status --porcelain epub_working`
Expected: **empty** (no `epub_working/` changes).

- [ ] **Step 2: Nested-anchor base invariant**

Run: `<python> scripts/check_nested_anchors.py` then `$env:PYTHONUTF8="1"; <python> -m pytest tests/test_nested_anchors.py --basetemp="...\bt"`
Expected: 0 nested anchors; PASS.

- [ ] **Step 3: Byte-stability gate** (the determinism + multi-edition validity gate)

Run: `$env:PYTHONUTF8="1"; <python> -m pytest tests/test_byte_stability_gate.py -v -m slow --basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`
Expected: PASS (~205s — builds multi-canon editions valid+distinct + flagship rebuild byte-deterministic). **This is the Phase-A ship gate.**

- [ ] **Step 4: Flagship epubcheck**

Run: build `catholic-study` and run epubcheck per `dev/SESSION_PLAYBOOK.md` (`--jar <bundled jar>`).
Expected: `0/0/0/0`.

- [ ] **Step 5: Targeted full-suite sanity** (the affected modules)

Run, one file at a time: `tests/test_hierarchical_symbols.py`, `tests/test_enabled_kinds_unified.py`, `tests/test_build_cache.py`, `tests/test_web_sample_kindfilter_parity.py`, `tests/test_mint11_phase56.py`.
Expected: all PASS — confirms the resolver invariant didn't disturb the tri-path agreement or preview/build parity.

- [ ] **Step 6: Record the proof** in the commit message of Task 8 (gate timing + epubcheck result + "epub_working/ untouched").

---

## Task 8: Lint, docs, and the 5-leg save

**Files:**
- Modify: `dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md`, `dev/CHANGELOG.md`, `dev/REPO_MAP.md` (if test-file count tracked), `docs/superpowers/INDEX.md`

- [ ] **Step 1: Lint + types**

Run: `$env:PYTHONUTF8="1"; <python> scripts/lint_rules.py` and `<python> -m mypy scripts/build_edition.py scripts/core/config.py`
Expected: lint clean (or only the pre-existing SESSION_STATE-freshness/size warns); mypy clean. Fix any new violations.

- [ ] **Step 2: Update the truth records.** Re-read the top 6 lines of each big MD first (they truncate), then prepend a concise entry: SESSION_STATE headline (Phase A symbol engine shipped, byte-stable, what's next = Phase B), IN_FLIGHT active block, CHANGELOG entry with the byte-stability proof. Register both 2026-06-04 specs + this plan in `docs/superpowers/INDEX.md`.

- [ ] **Step 3: ruff-format everything generated**

Run: `<python> -m ruff format scripts/ tests/`

- [ ] **Step 4: The full 5-leg save** (separate message from any file write — never race `git add -A`)

Run: `pwsh -File save-all.ps1 -Message "ρ.3 Phase A COMPLETE: per-coordinate note-symbol engine (Bible/book/chapter/individual) — byte-stable, 9 KJV identical; gate PASSED <Ns>, flagship epubcheck 0/0; force-on + per-chapter/per-book signed tokens" -Label phaseA-symbol-engine`
Expected: all 5 legs land (local commit + GitLab + GitHub + E: + F:); `git status -b` ahead/behind 0; `git bundle verify` ok. If a drive is unmounted, report the partial save and re-run when fixed.

- [ ] **Step 5: Verify the save** (`git log --oneline -1`, `git status -b`) and report the proof line.

---

## Self-review notes (gaps the executor should watch)

- **Real note-ids:** Tasks 4/6 assume specific example notes exist (`gen:1` xref, `psa:23:1` comm). Before asserting, the executor MUST confirm real ids via `_iter_note_ref_symbols()` and adjust constants — the tests must bind to notes that exist on disk.
- **`all_kinds` in `build_one`:** confirm the local variable name at :2738 (`enabled, disabled = compute_enabled_kinds(edition, all_kinds)`) — `all_kinds` is already in scope; reuse it for `_symbol_overridden_kinds` / `compute_symbol_disabled_html_ref_ids`.
- **`config.load_categories()`:** verify the loader name (the map cites `content/categories.yaml`, 15 categories). If it is `load_categories`/`categories()` confirm and use the real name in `_valid_symbol_tokens`.
- **Phase B & C are separate plans** — popups (`_resolve_popup_languages` per-chapter/verse) and the `/build-my-bible` navigator console are NOT in this plan.
```
