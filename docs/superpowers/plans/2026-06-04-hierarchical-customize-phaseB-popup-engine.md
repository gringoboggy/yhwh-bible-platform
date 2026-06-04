# Hierarchical Customization — Phase B: Popup-Language Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend translation-popup language selection to resolve per (book, chapter, verse) — Bible → book → chapter → individual-verse — most-specific-wins, byte-identical when the new fields are unset.

**Architecture:** Two new edition fields (`popup_languages_per_chapter`, `popup_languages_per_verse`, flat `"book:ch=langs"` / `"book:ch:vs=langs"`) + their decode/encode helpers, then a 5-tier extension of the existing `_resolve_popup_languages(edition, book_code)` to `(edition, book_code, chapter=None, verse=None)` (verse ▸ chapter ▸ book ▸ default ▸ DEFAULT_POPUP_WITNESSES). The single call site passes chapter+verse. The per-verse vnote bake already exists; only the `active_langs` *input* becomes verse-aware. `filter_html`-style stripping is unchanged.

**Tech Stack:** Python 3.12 (`py -3`, NOT the Store stub), pytest. No new dependencies.

**Status:** IN PROGRESS 2026-06-04 — ready to execute. Phase B of the hierarchical-customization spec (`docs/superpowers/specs/2026-06-04-hierarchical-edition-customization-design.md`, §6). Byte-stability gate = the ship bar. Phase A (symbols) shipped; Phase C (the `/build-my-bible` navigator) follows.

---

## Pre-flight (read once)

- Spec §3.4-popup (precedence), §4 (popup schema), §6 (build path).
- Pattern sources (read them):
  - `scripts/build_edition.py:1054-1081` — `_resolve_popup_languages(edition, book_code)` (the function to extend; tiers per_book → default → DEFAULT_POPUP_WITNESSES; legacy-id mapping via `_pv.resolve_version_id`; filter to `POPUP_LANGUAGES`).
  - `scripts/build_edition.py:1084-1126` — `decode_per_book_languages` (the decoder to mirror; note the explicit-empty `"book="` → `[]` semantics distinct from absent-key).
  - `scripts/build_edition.py:1129-1157` — `encode_per_book_languages` (encoder to mirror; sorts canonical book order, filters unknowns).
  - `scripts/build_edition.py:1240` — the ONLY call site: `active_langs = _resolve_popup_languages(edition, book)`, inside `_apply_popup_languages_and_translation` (def `:1202`), where `book`/`ch`/`vs` are in scope (ch/vs used at `:1248`). The vnote aside id is `vnote-<book>-<ch>-<vs>` (no suffix — popups are per verse).
  - `tests/test_hierarchical_symbols_build.py` — the slow build-integration harness to reuse for the Phase-B build test.

**Windows env (every test run):** `$env:PYTHONUTF8="1"`; `py -3` (not `python`); `--basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`; run from the repo dir; one file at a time; `ruff format` before each commit; per-task LOCAL commits via `pwsh -File save.ps1`, the full 5-leg `save-all.ps1` only at the last task.

**Field reference (all default-absent ⇒ byte-identical):**
| Field | Level | Disk format | Meaning |
|-------|-------|-------------|---------|
| `popup_languages_default` | Bible | (exists) list of lang ids | edition default |
| `popup_languages_per_book` | book | (exists) `"gen=wlc,lxx-greek"` | per-book absolute set |
| `popup_languages_per_chapter` | chapter | `"gen:1=wlc"` | per-chapter absolute set |
| `popup_languages_per_verse` | verse | `"gen:1:1=wlc,lxx-greek"` | per-verse absolute set |

Precedence (most-specific-wins, ABSOLUTE set per scope): verse ▸ chapter ▸ book ▸ default ▸ `DEFAULT_POPUP_WITNESSES`. An explicit empty (`"gen:1:1="`) is a meaningful override ("no popups on this verse"), distinct from an absent key.

---

## Task B-0: Fold in the Phase-A cosmetic nits

**Files:** Modify `scripts/build_edition.py`; Modify `tests/test_hierarchical_symbols_build.py`.

- [ ] **Step 1: Move `_NOTE_ID_RE` out of the import block.** In `scripts/build_edition.py`, the line `_NOTE_ID_RE = re.compile(r"^([a-z0-9]+):(\d+):(\d+)([a-z]*):([a-z][a-z0-9-]*)$")` currently sits between `import shutil` (≈:45) and `import subprocess` (≈:48). DELETE it from there, and RE-ADD the identical line immediately after the `from scripts.core import config  # noqa: E402` line (≈:58), where module-level constants belong (alongside `REPO_ROOT`).

- [ ] **Step 2: Delete the dead diagnostic block.** In `tests/test_hierarchical_symbols_build.py`, in `test_per_book_off_strips_exo_xref_keeps_gen_xref`, delete the trailing diagnostic block (the lines from `# Broader: no exo xref-citation ref-ids at all` through `_ = exo_xref_survivors  # suppress unused-variable lint` — `exo_xref_ids_in_epub` / `exo_xref_survivors` are computed but never asserted). The function should end after the `assert _EXO_XREF_REF_ID_ABSENT not in ref_ids, (...)` block.

- [ ] **Step 3: Verify nothing broke.**
Run: `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_hierarchical_symbols.py -q --basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"` (expect 21 passed — confirms `_NOTE_ID_RE` still resolves) and `py -3 -m pytest tests/test_hierarchical_symbols_build.py --collect-only -q --basetemp="..."` (expect it collects 2 tests cleanly — confirms the test edit parses; do NOT run the slow build here).
Also `py -3 -c "import scripts.build_edition"` (no import error).

- [ ] **Step 4: Commit (LOCAL only).** `py -3 -m ruff format scripts/build_edition.py tests/test_hierarchical_symbols_build.py`, then `pwsh -File save.ps1 -Message "ρ.3 Phase B-0: fold in Phase-A review nits (_NOTE_ID_RE placement; drop dead test diagnostic)"`.

---

## Task B-1: per-chapter + per-verse popup-language decode/encode

**Files:** Modify `scripts/build_edition.py` (add after `encode_per_book_languages`, ≈:1157). Test: `tests/test_hierarchical_popups.py` (new).

- [ ] **Step 1: Write the failing test** `tests/test_hierarchical_popups.py`:
```python
import importlib
be = importlib.import_module("scripts.build_edition")


class TestPerChapterLangs:
    def test_decode_basic(self):
        assert be.decode_per_chapter_languages(["gen:1=wlc,lxx-greek", "exo:3="]) == {
            "gen:1": ["wlc", "lxx-greek"], "exo:3": []
        }

    def test_decode_none_and_dict(self):
        assert be.decode_per_chapter_languages(None) == {}
        assert be.decode_per_chapter_languages({"gen:1": ["wlc"]}) == {"gen:1": ["wlc"]}

    def test_encode_sorts_canonical_then_numeric_and_filters_unknown(self):
        out = be.encode_per_chapter_languages({"gen:10": ["wlc"], "gen:2": ["wlc"], "exo:1": ["wlc", "not-a-lang"]})
        assert out == ["gen:2=wlc", "gen:10=wlc", "exo:1=wlc"]

    def test_roundtrip(self):
        d = {"gen:1": ["wlc"], "gen:50": ["lxx-greek"]}
        assert be.decode_per_chapter_languages(be.encode_per_chapter_languages(d)) == d


class TestPerVerseLangs:
    def test_decode_basic(self):
        assert be.decode_per_verse_languages(["gen:1:1=wlc,lxx-greek", "gen:1:2="]) == {
            "gen:1:1": ["wlc", "lxx-greek"], "gen:1:2": []
        }

    def test_encode_sorts_canonical_then_numeric(self):
        out = be.encode_per_verse_languages({"gen:1:10": ["wlc"], "gen:1:2": ["wlc"], "gen:2:1": ["wlc"]})
        assert out == ["gen:1:2=wlc", "gen:1:10=wlc", "gen:2:1=wlc"]

    def test_roundtrip(self):
        d = {"gen:1:1": ["wlc", "lxx-greek"], "psa:119:1": ["wlc"]}
        assert be.decode_per_verse_languages(be.encode_per_verse_languages(d)) == d
```

- [ ] **Step 2: Run it, expect FAIL** (`decode_per_chapter_languages` not defined):
`$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_hierarchical_popups.py -v --basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`

- [ ] **Step 3: Implement** in `scripts/build_edition.py` after `encode_per_book_languages` (≈:1157). The decoders mirror `decode_per_book_languages` (parse `"key=csv"` → dict, explicit-empty `"key="` → `[]`); the encoders mirror `encode_per_book_languages` but sort by canonical book then numeric chapter (then verse), and filter unknown ids against `POPUP_LANGUAGES`:
```python
def decode_per_chapter_languages(raw) -> dict[str, list[str]]:
    """Decode ``popup_languages_per_chapter``. Key is ``"<book>:<ch>"``;
    otherwise identical to ``decode_per_book_languages`` (explicit-empty
    ``"gen:1="`` → ``[]`` is a meaningful override)."""
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


def decode_per_verse_languages(raw) -> dict[str, list[str]]:
    """Decode ``popup_languages_per_verse``. Key is ``"<book>:<ch>:<vs>"``;
    same parsing as ``decode_per_chapter_languages``."""
    return decode_per_chapter_languages(raw)


def _encode_keyed_languages(per_key: dict[str, list[str]], key_parts: int) -> list[str]:
    """Shared encoder for the per-chapter (key_parts=2 → book:ch) and per-verse
    (key_parts=3 → book:ch:vs) language maps. Sorts by canonical book order then
    numeric chapter (then numeric verse); filters unknown ids against
    POPUP_LANGUAGES (validate-at-write, like encode_per_book_languages)."""
    if not per_key:
        return []
    from scripts.core import config as _cfg

    book_order = list(_cfg.books_by_code().keys())
    rank = {code: i for i, code in enumerate(book_order)}

    def _sort_key(item):
        parts = item[0].split(":")
        book = parts[0]
        nums = []
        for p in parts[1:key_parts]:
            try:
                nums.append(int(p))
            except ValueError:
                nums.append(1 << 30)
        return (rank.get(book, len(book_order) + 1), book, *nums)

    out: list[str] = []
    for key, langs in sorted(per_key.items(), key=_sort_key):
        clean = [L for L in (langs or []) if L in POPUP_LANGUAGES]
        out.append(f"{key}={','.join(clean)}")
    return out


def encode_per_chapter_languages(per_chapter: dict[str, list[str]]) -> list[str]:
    """Inverse of decode_per_chapter_languages (key ``book:ch``)."""
    return _encode_keyed_languages(per_chapter, key_parts=2)


def encode_per_verse_languages(per_verse: dict[str, list[str]]) -> list[str]:
    """Inverse of decode_per_verse_languages (key ``book:ch:vs``)."""
    return _encode_keyed_languages(per_verse, key_parts=3)
```

- [ ] **Step 4: Run, expect PASS** (7 tests). (`wlc`/`lxx-greek` are real ids in `POPUP_LANGUAGES` via the version registry — if `test_*_filters_unknown` fails, inspect `ALL_POPUP_LANGUAGES` for real ids and adjust the test constants.)

- [ ] **Step 5: Commit (LOCAL).** `py -3 -m ruff format scripts/build_edition.py tests/test_hierarchical_popups.py`, then `pwsh -File save.ps1 -Message "ρ.3 Phase B-1: per-chapter + per-verse popup-language decode/encode (TDD)"`.

---

## Task B-2: extend `_resolve_popup_languages` to (book, chapter, verse)

**Files:** Modify `scripts/build_edition.py:1054-1081`. Test: append to `tests/test_hierarchical_popups.py`.

- [ ] **Step 1: Append the failing tests:**
```python
class TestResolvePopupLangs:
    def _ed(self, **kw):
        base = {"id": "t"}
        base.update(kw)
        return base

    def test_no_override_two_arg_unchanged(self):
        # Back-compat: the old 2-arg call must behave exactly as before.
        ed = self._ed(popup_languages_default=["wlc", "lxx-greek"])
        assert be._resolve_popup_languages(ed, "gen") == {"wlc", "lxx-greek"}

    def test_no_per_scope_with_chapter_verse_equals_book(self):
        ed = self._ed(popup_languages_per_book=["gen=wlc"])
        # passing chapter/verse but no per-chapter/verse fields → same as per-book
        assert be._resolve_popup_languages(ed, "gen", 1, 1) == be._resolve_popup_languages(ed, "gen")

    def test_per_chapter_overrides_book(self):
        ed = self._ed(popup_languages_per_book=["gen=wlc,lxx-greek"],
                      popup_languages_per_chapter=["gen:1=wlc"])
        assert be._resolve_popup_languages(ed, "gen", 1, 5) == {"wlc"}
        assert be._resolve_popup_languages(ed, "gen", 2, 5) == {"wlc", "lxx-greek"}

    def test_per_verse_overrides_chapter(self):
        ed = self._ed(popup_languages_per_chapter=["gen:1=wlc"],
                      popup_languages_per_verse=["gen:1:1=wlc,lxx-greek"])
        assert be._resolve_popup_languages(ed, "gen", 1, 1) == {"wlc", "lxx-greek"}
        assert be._resolve_popup_languages(ed, "gen", 1, 2) == {"wlc"}

    def test_explicit_empty_verse_means_no_popups(self):
        ed = self._ed(popup_languages_per_book=["gen=wlc"],
                      popup_languages_per_verse=["gen:1:1="])
        assert be._resolve_popup_languages(ed, "gen", 1, 1) == set()
        assert be._resolve_popup_languages(ed, "gen", 1, 2) == {"wlc"}
```

- [ ] **Step 2: Run, expect FAIL** (current 2-arg signature can't take chapter/verse).

- [ ] **Step 3: Replace `_resolve_popup_languages`** (≈:1054-1081) with the 5-tier version. Keep the legacy-id mapping + POPUP_LANGUAGES filter at the end IDENTICAL; use `is None` checks so an explicit-empty `[]` override correctly stops the cascade:
```python
def _resolve_popup_languages(edition: dict, book_code: str, chapter=None, verse=None) -> set[str]:
    """Resolve the active popup-language set for one (edition, book[, chapter, verse]).

    Most-specific-wins (Phase ρ.3 / spec §3.4-popup):
      1. popup_languages_per_verse["book:ch:vs"]   if present
      2. popup_languages_per_chapter["book:ch"]    if present
      3. popup_languages_per_book[book]            if present
      4. popup_languages_default                   if present
      5. DEFAULT_POPUP_WITNESSES                    (back-compat default)

    Calling without chapter/verse (the legacy 2-arg form) skips tiers 1-2 and
    behaves exactly as before — the invariant existing callers rely on. An
    explicit empty list at any tier (``"gen:1:1="``) is a meaningful override
    ("no popups on this verse"); ``is None`` checks preserve that vs absence.

    Returns a set of language ids — only ids in POPUP_LANGUAGES are retained;
    legacy ids (english/hebrew/greek) map to version ids via resolve_version_id.
    """
    raw: list[str] | None = None

    if chapter is not None and verse is not None:
        per_verse = decode_per_verse_languages(edition.get("popup_languages_per_verse"))
        vkey = f"{book_code}:{chapter}:{verse}"
        if vkey in per_verse:
            raw = per_verse[vkey]

    if raw is None and chapter is not None:
        per_chapter = decode_per_chapter_languages(edition.get("popup_languages_per_chapter"))
        ckey = f"{book_code}:{chapter}"
        if ckey in per_chapter:
            raw = per_chapter[ckey]

    if raw is None:
        per_book = decode_per_book_languages(edition.get("popup_languages_per_book"))
        if book_code in per_book:
            raw = per_book[book_code]
        elif edition.get("popup_languages_default") is not None:
            raw = edition.get("popup_languages_default")
        else:
            # §4.3 — no default → the default witness set (Hebrew + Greek LXX/NT
            # + Latin + Arabic), NOT every baked version.
            return {m for m in _pv.DEFAULT_POPUP_WITNESSES if m in POPUP_LANGUAGES}

    mapped = ((_pv.resolve_version_id(lang) or lang) for lang in (raw or []))
    return {m for m in mapped if m in POPUP_LANGUAGES}
```

- [ ] **Step 4: Run, expect PASS** (the 6 new resolve tests + the whole file). Then run the full popup file: `py -3 -m pytest tests/test_hierarchical_popups.py -q --basetemp="..."`.

- [ ] **Step 5: Commit (LOCAL).** ruff format, then `pwsh -File save.ps1 -Message "ρ.3 Phase B-2: _resolve_popup_languages 5-tier per-coordinate resolution (TDD)"`.

---

## Task B-3: wire the call site (pass chapter + verse)

**Files:** Modify `scripts/build_edition.py:1240`.

- [ ] **Step 1: Read** `scripts/build_edition.py:1228-1250` and confirm `book`, `ch`, `vs` are in scope at the `active_langs = _resolve_popup_languages(edition, book)` line (≈:1240) — `book` is the aside's book code, `ch`/`vs` are ints (used just below at the `_tx.get_verse(translation_id, book, ch, vs)` call). Confirm this is the ONLY caller (`grep _resolve_popup_languages(` shows just the def + this call).

- [ ] **Step 2: Change** the call (≈:1240) from:
```python
        active_langs = _resolve_popup_languages(edition, book)
```
to:
```python
        active_langs = _resolve_popup_languages(edition, book, chapter=ch, verse=vs)
```

- [ ] **Step 3: Verify no regression + the byte-stability no-op.** Run, one at a time:
- `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_hierarchical_popups.py -q --basetemp="..."` (green)
- `py -3 -m pytest tests/test_build_cache.py -q --basetemp="..."` (green; ~60s)
- `py -3 -c "import scripts.build_edition"` (no import break).
**Byte-stability reasoning to confirm in the code:** with no `popup_languages_per_chapter`/`_per_verse` fields, the resolver's tiers 1-2 find nothing (`vkey`/`ckey` absent) → `raw` stays None → falls to the identical per-book/default tiers → identical language set → identical strip decisions → byte-identical EPUB. The real proof is Task B-5's gate.

- [ ] **Step 4: Commit (LOCAL).** ruff format, then `pwsh -File save.ps1 -Message "ρ.3 Phase B-3: thread chapter+verse into the popup-language resolver call site"`.

---

## Task B-4: build-integration test (per-verse popup override changes the EPUB)

**Files:** Test: `tests/test_hierarchical_popups_build.py` (new, slow-tagged). Reuse the build harness from `tests/test_hierarchical_symbols_build.py` (`_build` with the `monkeypatch.setattr(config, "editions_by_id", ...)` + `force=True` pattern; read inner XHTML via `zipfile`).

- [ ] **Step 1: Write the slow integration test.** Build `jewish-study` (smallest canon; gen/exo/psa present) twice: a baseline and an override. The override sets `popup_languages_per_verse=["<book:ch:vs>=wlc"]` for a real early verse (e.g. `gen:1:1`), forcing ONLY Hebrew (`wlc`/`vnote-hebrew`) on that verse while a sibling verse keeps its full set. The vnote aside is `id="vnote-<book>-<ch>-<vs>"`; its body carries `<p class="vnote-hebrew">`, `<p class="vnote-greek">`, etc. **Before asserting**, confirm via a baseline build (or by inspecting one aside) which classes `gen:1:1` and `gen:1:2` carry by default, then assert: after the override, `gen 1:1`'s aside contains `vnote-hebrew` but NOT `vnote-greek`, while `gen 1:2`'s aside still contains both. Pull the per-verse aside with a regex like `r'id="vnote-g-1-1"(.*?)</aside>'` (DOTALL) and check `'vnote-greek' in that_aside`. Tag `pytestmark = pytest.mark.slow`.
  - If the popup default for `jewish-study` doesn't include Greek on `gen:1:1` (so the override isn't observable), pick a verse/edition where the default set DOES carry ≥2 languages so removing one is visible — or set `popup_languages_default=["wlc","lxx-greek"]` on the patched edition so the baseline is known, then override one verse to `["wlc"]`.

- [ ] **Step 2: Run** (`-m slow`, expect a few minutes for the builds). Iterate until green.

- [ ] **Step 3: Commit (LOCAL).** ruff format, then `pwsh -File save.ps1 -Message "ρ.3 Phase B-4: end-to-end build test — per-verse popup override changes one verse's languages"`.

- [ ] **Escalation:** if the per-verse aside class extraction or the baseline-language determination is unclear, report NEEDS_CONTEXT with what you found (which classes the default carries) rather than a test that doesn't actually assert the behavior — we can fall back to a function-level test of `_resolve_popup_languages` across coordinates (already covered by B-2) plus a lighter build smoke.

---

## Task B-5: byte-stability proof + cache-key check (ship bar)

**Files:** none changed — run gates + one verification.

- [ ] **Step 1: epub_working/ untouched.** `git -C "<repo>" status --porcelain epub_working` → empty.
- [ ] **Step 2: nested-anchors.** `py -3 scripts/check_nested_anchors.py` (clean) + `py -3 -m pytest tests/test_nested_anchors.py -q --basetemp="..."` (pass).
- [ ] **Step 3: ★byte-stability gate (ship bar).** `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_byte_stability_gate.py -v -m slow --basetemp="..."` → 1 passed (note wall time). None of the gate's editions set the new popup fields, so they must build byte-identical.
- [ ] **Step 4: affected suites** (one at a time): `tests/test_hierarchical_popups.py`, `tests/test_build_cache.py`, `tests/test_web_filesplit.py` (if it exercises the vnote pass), `tests/test_scripts.py -k popup` (any popup tests). Expect green.
- [ ] **Step 5: cache-key check.** Verify the content-addressable build cache reflects the new edition fields so a changed per-chapter/per-verse override invalidates the cache. Inspect `scripts/core/build_cache.py` — does the edition portion of the cache key hash the full edition dict (→ new fields auto-included) or an explicit field list? Confirm `popup_languages_per_chapter`/`_per_verse` (and, retroactively, the Phase-A `note_families_*`/`enabled_note_ids` fields) are covered. If the cache hashes an explicit allow-list that omits them, ADD them (a one-line fix) and note it; if it hashes the whole edition dict, note "covered, no change." (This is correctness for real edition edits, not byte-stability.)
- [ ] **Step 6: flagship epubcheck (best-effort).** Build `catholic-study` + epubcheck via the bundled jar (memory `reference_epubcheck`); expect 0/0. Skip-with-note if the tooling won't invoke cleanly.

---

## Task B-6: docs + 5-leg save

- [ ] **Step 1: Lint + types.** `py -3 scripts/lint_rules.py` (clean or only the pre-existing freshness/size warns) + `py -3 -m mypy scripts/build_edition.py`. Fix any new violations.
- [ ] **Step 2: Truth records.** Re-read the top ~6 lines of each (they truncate + the Mac lane may have pushed), then prepend a Phase-B-COMPLETE entry to `dev/SESSION_STATE.md` + `dev/IN_FLIGHT.md` + `dev/CHANGELOG.md` (and register this plan in `docs/superpowers/INDEX.md` if not already). **If the Mac lane has pushed, `git pull --rebase origin main` FIRST** (rebase the Phase-B commits on top), then write the truth records on the latest state.
- [ ] **Step 3: ruff format** `scripts/ tests/`.
- [ ] **Step 4: 5-leg save** (separate message from any file write): `pwsh -File save-all.ps1 -Message "ρ.3 Hierarchical Customization PHASE B COMPLETE (popup engine): per-coordinate popup-language resolution (Bible/book/chapter/verse); byte-stable (gate PASSED, 9 KJV identical)" -Label phaseB-popup-engine`. Verify all 5 legs land.

---

## Self-review notes (executor watch-items)

- **Backward-compat invariant (load-bearing):** the 2-arg `_resolve_popup_languages(edition, book)` and the new 4-arg call with no per-chapter/verse fields BOTH must equal the pre-Phase-B result. B-2's `test_no_override_two_arg_unchanged` + `test_no_per_scope_with_chapter_verse_equals_book` pin this; the byte-stability gate proves it end-to-end.
- **`is None` vs truthiness:** the cascade MUST use `if raw is None` (not `if not raw`) so an explicit-empty override (`"gen:1:1="` → `[]`) correctly stops the cascade and yields no popups. B-2's `test_explicit_empty_verse_means_no_popups` pins it.
- **Legacy-id mapping + POPUP_LANGUAGES filter** must stay identical (the final two lines of the resolver), applied uniformly to whichever tier `raw` came from.
- **Real ids:** `wlc` (Hebrew/WLC) + `lxx-greek` (Greek LXX) are real version ids; confirm against `ALL_POPUP_LANGUAGES` before binding tests.
- **Phase C (the `/build-my-bible` navigator + the API write path for ALL the new fields) is a separate plan** — not in Phase B. The encode_* helpers are write-path scaffolding consumed there.
