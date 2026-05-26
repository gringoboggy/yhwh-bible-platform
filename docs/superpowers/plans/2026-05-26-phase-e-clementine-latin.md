# Phase E — Clementine Latin Appendix (`man`/`1es`/`2es`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add the Clementine Vulgate (Latin) witness to the three deuterocanonical appendix books — Prayer of Manasseh (`man`), 1 Esdras (`1es`), 2 Esdras (`2es`) — completing the Vulgate popup spine (74 → 77 books). Purely additive.

**Architecture:** Fetch the public-domain Clementine wikitext from la.wikisource (the eBible source omits this appendix), commit it as a reproducible source, parse it with a new focused extractor, remap to canonical KJV coords via the **existing** `vulgate_to_kjv` (no versification change needed — verified), write the per-book stores, bake the asides for only these 3 books, and prove additivity + validity with the proven 05-23 categorize-diff + epubcheck gate.

**Tech Stack:** Python 3.14 (stdlib `re` only — no new deps), pytest, the project's `ebible`/`epubcheck`/`lint_rules`/`ruff` gates.

**Spec:** `docs/superpowers/specs/2026-05-26-phase-e-clementine-latin-design.md`

---

## Environment & conventions (read before any step)

- **Interpreter** (memory `python-interpreter-path`): always
  ```powershell
  $env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest <node-id> -v
  ```
  from repo root `C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4`. `PYTHONUTF8=1` mandatory.
- **Targeted node-ids only**; never the whole `test_scripts.py`.
- **Commits DEFERRED to the user's `save`** (memories `feedback_save_is_local_commit`, `feedback_continue_not_save`). Each task ends at green tests; do NOT commit. One commit at the end via `save.ps1` (PowerShell only) — Task 9.
- **Before save:** `ruff format` the new `.py` files incl. the store files (memory `feedback_ruff_format_before_save`).
- **Data files are parsed as literals only, never run as code** (RULES §7.1 — use the project's translation loader / `ast` literal parsing).
- **Sources are web-fetched per the plan** (`PLAN_2026-05-21.md:210`) — do NOT ask the user for them (memory `sources-already-in-place`).

---

## Key grounded facts (verified 2026-05-26)

- **Source pages** (la.wikisource, raw wikitext via `?action=raw`):
  | code | page | book |
  |---|---|---|
  | `man` | `Vulgata_Clementina/Oratio_Manasse` | Oratio Manassae (1 ch) |
  | `1es` | `Vulgata_Clementina/Liber_Tertius_Esdrae` | 3 Esdras |
  | `2es` | `Vulgata_Clementina/Liber_Quartus_Esdrae` | 4 Esdras |
- **Wikitext shape:** leading `{{titulus2 …}}` + `{{Liber …}}` templates; chapters as `==Caput N==`; verses as `<sup>N</sup> Latin text…` running to the next `<sup>` or chapter end.
- **Versification (no edit):** `vulgate_to_kjv("man",…)` = identity; `"1es"` ∈ `_VULGATE_SEGMENTS` (handled); `"2es"` = identity. All in `CANONICAL_BOOKS` → extent guard passes.
- **Canonical skeletons:** `man` 1 ch/15 v · `1es` 9 ch/448 v · `2es` 16 ch/874 v (from `canonical_book_shape(code)`).
- **Store format:** `content/translations/vulgate-clementine/<code>.py` exposing `TRANSLATION="vulgate-clementine"`, `BOOK="<code>"`, `VERSES=[(ch,vs,text),…]` in **canonical KJV coords**; loaded the same safe way as every other store.

---

## File structure

| File | Responsibility |
|---|---|
| `content/translations/sources/vulgate-appendix/{oratio_manasse,esdras_iii,esdras_iv}.wiki` (NEW) | committed raw wikitext (reproducible source) |
| `scripts/extract_vulgate_appendix.py` (NEW) | parse wikitext → remap via `vulgate_to_kjv` → write stores |
| `content/translations/vulgate-clementine/{man,1es,2es}.py` (NEW) | per-book stores (canonical coords) |
| `content/translations/vulgate-clementine/_meta.yaml` | 74→77 books, refreshed counts, appendix provenance |
| `tests/test_phase_e_vulgate_appendix.py` (NEW) | parser · remap-drop · pipeline floor |
| `epub_working/index_split_*.html` | regenerated asides for the 3 books only |
| `dev/CHANGELOG.md`, `dev/MATRIX_MAP.md`, `dev/SESSION_STATE.md` | record the ship |

---

## Task 1: Acquire — fetch + commit the raw wikitext

**Files:** Create `content/translations/sources/vulgate-appendix/{oratio_manasse,esdras_iii,esdras_iv}.wiki`

- [ ] **Step 1: Fetch the three raw wikitext pages.** Use WebFetch on each `…?action=raw` URL (returns plain wikitext), or `curl`/the MediaWiki API if WebFetch mangles it:
  - `https://la.wikisource.org/wiki/Vulgata_Clementina/Oratio_Manasse?action=raw`
  - `https://la.wikisource.org/wiki/Vulgata_Clementina/Liber_Tertius_Esdrae?action=raw`
  - `https://la.wikisource.org/wiki/Vulgata_Clementina/Liber_Quartus_Esdrae?action=raw`
  Save each verbatim with the Write tool to the matching `.wiki` path.
- [ ] **Step 2: Sanity-check** each file contains `==Caput 1==` and `<sup>1</sup>` and is non-trivial in size (`man` smallest). If a fetch returns HTML instead of wikitext, switch to the MediaWiki API: `…/w/api.php?action=query&prop=revisions&rvslots=main&rvprop=content&format=json&titles=Vulgata Clementina/Oratio Manasse`.
- [ ] **Step 3: Checkpoint** — three `.wiki` files on disk (not git). No commit.

---

## Task 2: Parser — `parse_clementine_wikitext`

**Files:** Create `scripts/extract_vulgate_appendix.py`; Create `tests/test_phase_e_vulgate_appendix.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_phase_e_vulgate_appendix.py
from scripts.extract_vulgate_appendix import parse_clementine_wikitext

_SAMPLE = """{{titulus2|OperaeTitulus=Vulgata Clementina|SubTitulus=Oratio}}
{{Liber|Ante=X|Post=Y}}

==Caput 1==
<sup>1</sup> Domine omnipotens, Deus patrum nostrorum, [[Abraham]], et Isaac.
<sup>2</sup> Qui fecisti '''caelum''' et terram.

==Caput 2==
<sup>1</sup> Peccavi Domine, peccavi.
"""


def test_parses_chapters_verses_and_strips_markup():
    out = parse_clementine_wikitext(_SAMPLE)
    assert out == [
        (1, 1, "Domine omnipotens, Deus patrum nostrorum, Abraham, et Isaac."),
        (1, 2, "Qui fecisti caelum et terram."),
        (2, 1, "Peccavi Domine, peccavi."),
    ]


def test_drops_templates_and_collapses_whitespace():
    out = parse_clementine_wikitext("==Caput 1==\n<sup>1</sup>  A  {{ref|x}} B \n")
    assert out == [(1, 1, "A B")]
```

- [ ] **Step 2: Run → fail** (`ImportError`):
```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_phase_e_vulgate_appendix.py::test_parses_chapters_verses_and_strips_markup -v
```

- [ ] **Step 3: Implement** `scripts/extract_vulgate_appendix.py`:

```python
"""Phase E — extract the Clementine Vulgate appendix (man/1es/2es) from
la.wikisource raw wikitext into the vulgate-clementine store. The eBible Vulgate
source omits this post-NT appendix; PLAN_2026-05-21.md:210."""

from __future__ import annotations

import re

_TEMPLATE = re.compile(r"\{\{[^{}]*\}\}")
_CHAPTER = re.compile(r"==\s*Caput\s+(\d+)\s*==")
_VERSE = re.compile(r"<sup>\s*(\d+)\s*</sup>")


def _strip(s: str) -> str:
    prev = None
    while prev != s:  # collapse {{templates}} until stable (handles one-level nesting)
        prev = s
        s = _TEMPLATE.sub("", s)
    s = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", s)  # [[t|disp]] -> disp
    s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)            # [[t]] -> t
    s = s.replace("'''", "").replace("''", "")           # bold/italic
    s = re.sub(r"<[^>]+>", "", s)                          # stray tags
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_clementine_wikitext(text: str) -> list[tuple[int, int, str]]:
    """Return [(chapter, verse, latin_text), …] from Clementine wikitext."""
    out: list[tuple[int, int, str]] = []
    parts = _CHAPTER.split(text)  # [pre, ch1, body1, ch2, body2, …]
    for i in range(1, len(parts), 2):
        ch = int(parts[i])
        vparts = _VERSE.split(parts[i + 1])  # [pre, n1, t1, n2, t2, …]
        for j in range(1, len(vparts), 2):
            vtext = _strip(vparts[j + 1])
            if vtext:
                out.append((ch, int(vparts[j]), vtext))
    return out
```

- [ ] **Step 4: Run → pass** (both tests).
- [ ] **Step 5: Checkpoint** — green; no commit.

---

## Task 3: Remap + write stores — `build_verses` / `write_store`

**Files:** Modify `scripts/extract_vulgate_appendix.py`; Modify `tests/test_phase_e_vulgate_appendix.py`

- [ ] **Step 1: Write the failing test** (append):

```python
def test_remap_drops_unmapped_and_keeps_canonical():
    from scripts.extract_vulgate_appendix import build_verses

    # man is identity + in-extent (1 ch / 15 v); verse 99 is out-of-extent -> dropped
    parsed = [(1, 1, "Domine"), (1, 99, "out of extent")]
    assert build_verses("man", parsed) == [(1, 1, "Domine")]
```

- [ ] **Step 2: Run → fail** (`cannot import name 'build_verses'`).

- [ ] **Step 3: Implement** (append to `extract_vulgate_appendix.py`):

```python
from pathlib import Path

from scripts.core import config
from scripts.core.versification import vulgate_to_kjv

REPO = Path(config.__file__).resolve().parents[2]
_SRC = REPO / "content" / "translations" / "sources" / "vulgate-appendix"
_STORE = REPO / "content" / "translations" / "vulgate-clementine"
_PAGES = {"man": "oratio_manasse", "1es": "esdras_iii", "2es": "esdras_iv"}


def build_verses(code: str, parsed: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    """Remap parsed (vulgate ch,vs,text) to canonical KJV coords; drop unmapped
    (None) coords — never fabricate."""
    out: list[tuple[int, int, str]] = []
    for ch, vs, text in parsed:
        coord = vulgate_to_kjv(code, ch, vs)
        if coord is None:
            continue
        _, kch, kvs = coord
        out.append((kch, kvs, text))
    out.sort(key=lambda r: (r[0], r[1]))
    return out


def write_store(code: str, verses: list[tuple[int, int, str]]) -> Path:
    lines = ['TRANSLATION = "vulgate-clementine"', f'BOOK = "{code}"', "VERSES = ["]
    lines += [f"    ({ch}, {vs}, {text!r})," for ch, vs, text in verses]
    lines.append("]")
    path = _STORE / f"{code}.py"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def extract(code: str) -> list[tuple[int, int, str]]:
    raw = (_SRC / f"{_PAGES[code]}.wiki").read_text(encoding="utf-8")
    return build_verses(code, parse_clementine_wikitext(raw))
```

- [ ] **Step 4: Run → pass.**
- [ ] **Step 5: Checkpoint** — green; no commit.

---

## Task 4: Run extraction + verify `2es` alignment (ship/defer decision)

**Files:** runs the extractor; writes the 3 store files

- [ ] **Step 1:** Add a `main()` to `extract_vulgate_appendix.py` that, for each of `man`/`1es`/`2es`, prints per-chapter extracted verse counts vs `canonical_book_shape(code)` and writes the store via `write_store`.
- [ ] **Step 2: Run it** and inspect the alignment report:
```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m scripts.extract_vulgate_appendix
```
- [ ] **Step 3: Decision (no guessing):**
  - `man` (15 v) + `1es` (9 ch) — if extracted counts ≈ canonical, accept.
  - **`2es`:** if extracted per-chapter counts match the 16-ch/874-v skeleton → accept. **If they diverge materially → DEFER `2es`** (delete its store file, ship `man`+`1es` only, document in CHANGELOG). The extent guard drops out-of-skeleton coords, so divergence shows as a count gap here — this is the gate, not a guess.
- [ ] **Step 4: Pin the pipeline floor** in `tests/test_phase_e_vulgate_appendix.py` — assert on the `extract(code)` output count directly (no data-file re-read, no code-running of the store):

```python
def test_extraction_meets_floor():
    from scripts.extract_vulgate_appendix import extract

    assert len(extract("man")) >= 15
    assert len(extract("1es")) >= 400
    # add: assert len(extract("2es")) >= 800  — only if 2es accepted in Step 3
```

- [ ] **Step 5: Checkpoint** — stores written for accepted books; green; no commit.

---

## Task 5: Update `_meta.yaml` + attributions

**Files:** Modify `content/translations/vulgate-clementine/_meta.yaml`; `content/sources/ATTRIBUTIONS.md`

- [ ] **Step 1:** Bump `stats.books` 74 → 76 or 77 (per ship/defer), `stats.verses` += accepted appendix verses, and add an appendix-provenance note: the appendix books (`man`/`1es`[/`2es`]) come from la.wikisource `Vulgata Clementina` (PD), distinct from the eBible body source. Hand-edit the few lines (preserve comments).
- [ ] **Step 2:** Credit la.wikisource for the appendix in `content/sources/ATTRIBUTIONS.md`.
- [ ] **Step 3: Checkpoint** — no commit.

---

## Task 6: Bake the asides + prove additive-only

**Files:** Modify `epub_working/index_split_*.html` (the 3 books' files only)

- [ ] **Step 1:** Inspect `generate_verse_popups.py` argparse for a per-book flag; confirm `vulgate` is in the baked witness set; regenerate asides for the 3 books (per-book if supported, else full regen):
```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m scripts.generate_verse_popups --books man 1es 2es
```
- [ ] **Step 2: Prove additive-only (categorize-diff).** Mirror the 05-23 `_aside_compare` approach: confirm `vnote-vulgate` asides now exist on `man`/`1es`[/`2es`] and that **every other version on every other book is byte-identical** — `git diff --stat epub_working/` should show only the 3 books' split files changed.
- [ ] **Step 3: Checkpoint** — no commit.

---

## Task 7: Bake-and-prove gate (RULES §9)

- [ ] **Step 1:** Marker↔aside pairing — `ebible verify` (or the verify path inside `build`):
```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts/ebible.py verify
```
- [ ] **Step 2:** Build catholic-study + epubcheck (memory `reference_epubcheck` — pass `--jar`):
```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts/build_edition.py catholic-study --version v28a-dev --output-dir "C:/Users/bogda/AppData/Local/Temp/yhwh_phase_e" --force
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts/epubcheck.py --jar "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\epubcheck\epubcheck.jar" --editions-dir "C:/Users/bogda/AppData/Local/Temp/yhwh_phase_e"
```
Expected: **errors=0 / warnings=0**. Pull `man`/`1es`/`2es` from the built EPUB → confirm the Latin (`vnote-vulgate`) column shows.
- [ ] **Step 3:** Project gates:
```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m ruff format content/translations/vulgate-clementine/man.py content/translations/vulgate-clementine/1es.py scripts/extract_vulgate_appendix.py tests/test_phase_e_vulgate_appendix.py
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m ruff format --check .
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts/lint_rules.py
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_phase_e_vulgate_appendix.py -v
```
Expected: ruff clean · `lint_rules` 16/0/0 · tests green.
- [ ] **Step 4: Checkpoint** — all gates green; clean the `Temp/yhwh_phase_e` dir; no commit.

---

## Task 8: Docs

**Files:** `dev/CHANGELOG.md`, `dev/MATRIX_MAP.md`, `dev/SESSION_STATE.md`

- [ ] **Step 1:** CHANGELOG entry (newest at top) — Phase E shipped: +`man`/`1es`[/`2es`] Latin, Vulgate spine 74→76/77, source la.wikisource, additive-diff clean, epubcheck catholic-study 0/0; note the `2es` ship-or-defer outcome + reason.
- [ ] **Step 2:** MATRIX_MAP — Vulgate spine now includes the appendix; the new extractor + la.wikisource source.
- [ ] **Step 3:** SESSION_STATE — new LATEST banner (Phase E shipped, uncommitted, awaiting save) + demote prior.
- [ ] **Step 4: Checkpoint** — no commit.

---

## Task 9: Save gate (user-triggered) — the ONLY commit point

- [ ] **Step 1:** `git status` shows only intended files (no stray temp; the build dir is outside the repo).
- [ ] **Step 2:** Present for the user's **save**; on their go run `save.ps1` via PowerShell (pre-commit hook = ruff + lint_rules).
- [ ] **Step 3:** Verify `git log`/`git status` (memory `feedback_verify_commit_backup_truth`); offer the E:/F: `git bundle create … --all` backup (memory `reference_backup_drives`).

---

## Self-Review

**1. Spec coverage:** acquire (T1) · extractor (T2) · remap+store (T3) · 2es alignment ship/defer (T4) · _meta + attributions (T5) · bake additive (T6) · epubcheck gate (T7) · docs (T8) · save (T9). All spec sections covered. ✓
**2. Placeholder scan:** parser + remap + store code is complete; the bake/verify CLIs note "inspect actual flag" where the exact arg wasn't pre-confirmed (honest fallback), not a vague placeholder. Data files are parsed as literals, never run as code (RULES §7.1). ✓
**3. Type consistency:** `parse_clementine_wikitext → list[(int,int,str)]` feeds `build_verses(code, parsed) → list[(int,int,str)]` feeds `write_store(code, verses)`; `extract(code)` composes them; `_PAGES` keys = the 3 codes. ✓
**4. Ambiguity:** the `2es` ship/defer is decided by the count-compare in T4 Step 3, not guessed. ✓
