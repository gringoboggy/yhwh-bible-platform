# Ge'ez→KJV Partial-Anchoring Cross-Reference Tool — Implementation Plan (Phase B)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax. Read the companion spec `docs/superpowers/specs/2026-05-27-geez-own-versification-design.md` §3.3 FIRST. This is **Phase B** of `docs/superpowers/plans/2026-05-27-geez-own-versification-plan.md` (Phase A — the base-structured collation engine + the 10 `_collation_v2.json` files — is COMPLETE).

**Goal:** Build a deterministic, honesty-tagged tool that maps each Ge'ez base verse in a `_collation_v2.json` to its corresponding KJV verse(s) as a *secondary cross-reference*, and fold that `kjv_xref` into the v2 collations.

**Architecture:** Hard anchors come from two clean, language-bridging signals — (1) **numerals** (parse the Ge'ez numeral → int; parse KJV English number-words → int; match) and (2) **proper nouns** (a curated Ge'ez↔KJV-English name map matched against the KJV verse text). Base verses without a hard anchor are filled by **order-preserving interpolation** between surrounding anchors. Every mapping is tagged `anchored` (a hard token matched) or `interpolated` (positional). KJV is NEVER the structure — `kjv_xref` is an informative sidecar folded into the v2 collation; the immutable witnesses are never touched. Full Ge'ez→English semantic matching (the paid model) stays OUT of scope.

**Tech Stack:** Python 3.14, pytest. New module `scripts/core/geez_kjv_xref.py` (pure functions). Reuses `manuscript_collation.load_kjv_skeleton` (KJV `(ch, verse, text)` rows) and the Phase-A v2 collations. Windows/PowerShell.

**Environment invariants (this box):** python = `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe` (bare `python` is a broken stub); every test run needs `$env:PYTHONUTF8="1"` (PowerShell); `subprocess.run(...)` in tests must pass `stdin=subprocess.DEVNULL`; commit via `./save.ps1 -Message "..."` (PowerShell tool ONLY, never Bash); no git remote (local commits); back up via `git bundle create <E:/F: path> --all`.

---

## Execution discipline (ALL tasks)
- **TDD:** failing test → run-and-confirm-FAIL → minimal implementation → run-and-confirm-PASS → commit. One logical change per commit.
- **Pure functions:** `geez_kjv_xref.py` does NO file I/O (callers pass loaded data). The only I/O is the B5 integration driver.
- **Honesty (cardinal):** interpolation is NEVER presented as certainty — confidence is `anchored` vs `interpolated`. The immutable witnesses (`content/manuscript/**/calibration/*_witness*.json`) and the 4 Samuel calibration goldens are NEVER touched. `kjv_xref` is written ONLY into `content/manuscript/{kings,samuel}/collation/*_collation_v2.json`.
- **Regression after the integration step:** re-run `tests/test_manuscript_collation.py` (45 — engine untouched) + `tests/test_manuscript_collation_basestructured.py` and confirm green.

## Ground-truth anchor data (confirmed from `1ki6_collation_v2.json`)
- v1 (`geez_v` 1) tokens include `፬ ፻ ፹` (= 480) + `ሰሎሞን` (Solomon), `ግብጽ` (Egypt), `እስራኤል` (Israel), `እግዚእብሔር` (the LORD). KJV 1ki6:1 = "…four hundred and eightieth year after the children of **Israel** were come out of …**Egypt**…that **Solomon**…began to build the house of the **LORD**." → v1 anchors to 6:1.
- v2 tokens include `፷`(60) `፳`(20) `፴`(30). KJV 6:2 = "…**threescore** cubits…**twenty**…**thirty**." → v2 anchors to 6:2.
- CAM 1ki6 base = 33 verses; KJV 1ki6 = 38 verses (so some Ge'ez verses span >1 KJV verse — interpolation handles this).

## File structure
- **Create `scripts/core/geez_kjv_xref.py`** — the pure cross-ref engine: Ge'ez-numeral parser, KJV English-number parser, Ge'ez↔KJV proper-noun seed map + matcher, and `build_kjv_xref` (anchor + monotonic interpolate). One module, one responsibility.
- **Create `scripts/apply_kjv_xref.py`** — thin driver: for each of the 10 v2 collations, load it + the KJV chapter rows, call `build_kjv_xref`, fold `kjv_xref` + `metrics["kjv_coverage"]` in, atomic-rewrite. (Mirrors `scripts/recollate_base_structured.py`.)
- **Tests:** `tests/test_geez_kjv_xref.py` (B1–B4 unit) + extend `tests/test_manuscript_collation_basestructured.py` (B5 integration).

---

## Task B1: Ge'ez numeral parser

**Files:** Create `scripts/core/geez_kjv_xref.py`; Test `tests/test_geez_kjv_xref.py`

- [ ] **Step 1 — failing test.**
```python
import importlib
gx = importlib.import_module("scripts.core.geez_kjv_xref")

def test_single_geez_numerals():
    assert gx.numeral_token_value("፬") == 4
    assert gx.numeral_token_value("፲") == 10
    assert gx.numeral_token_value("፳") == 20
    assert gx.numeral_token_value("፴") == 30
    assert gx.numeral_token_value("፷") == 60
    assert gx.numeral_token_value("፻") == 100
    assert gx.numeral_token_value("፬፻") == 400      # digit before 100 multiplies
    assert gx.numeral_token_value("፲፪") == 12        # ten + two
    assert gx.numeral_token_value("ሰሎሞን") is None    # not a numeral

def test_verse_numerals_runs():
    # 1ki6 v1: "...በ፬፻ ፡ ወ፹ ፡ ዓመት..." tokenised ["፬","፻","ወ"?,"፹",...] -> 480
    toks = ["ወእምዝ", "፬", "፻", "ወ", "፹", "ዓመት", "እስራኤል"]
    assert 480 in gx.verse_numerals(toks)
    # 1ki6 v2 temple dimensions -> 60, 20, 30 each present
    toks2 = ["፷", "እመት", "ኑኁ", "ወ", "፳", "ራኅቡ", "ወ", "፴", "እመት"]
    assert {60, 20, 30} <= gx.verse_numerals(toks2)
```
- [ ] **Step 2 — run, confirm FAIL** (`numeral_token_value` undefined). `$env:PYTHONUTF8="1"; & "<python>" -m pytest tests/test_geez_kjv_xref.py -v`
- [ ] **Step 3 — implement.** Define `_GEEZ_NUM = {'፩':1,'፪':2,…,'፱':9,'፲':10,'፳':20,'፴':30,'፵':40,'፶':50,'፷':60,'፸':70,'፹':80,'፺':90,'፻':100,'፼':10000}`.
  - `numeral_token_value(tok)`: if every char ∈ `_GEEZ_NUM`, compose: iterate chars, `total=0, group=0`; for each value `v`: if `v>=100` → `group = (group or 1) * v; total += group; group = 0`; elif `v` is a tens (≥10) or unit → `group += v`; at end `total += group`. Return `total`; else `None`. (`፬፻`→4*100=400; `፲፪`→12.)
  - `verse_numerals(tokens)`: walk tokens; collect maximal runs of numeral tokens, allowing a single connector token `ወ`/`ወ-`prefix between numeral tokens; compose each run via the same hundreds/units logic *across* tokens (so `["፬","፻","ወ","፹"]` → 400 then +80 = 480) AND also add each standalone numeral token's value to the result set. Return the `set[int]` of all values found (both run-composed totals and individual tens/units, so `፷ ፳ ፴` yields {60,20,30}).
- [ ] **Step 4 — run, confirm PASS.**
- [ ] **Step 5 — commit.** `Phase B1: Ge'ez numeral parser (geez_kjv_xref)`

## Task B2: KJV English number-word parser

**Files:** Modify `scripts/core/geez_kjv_xref.py`; Test same.

- [ ] **Step 1 — failing test.**
```python
def test_kjv_number_values():
    assert 480 in gx.kjv_number_values("in the four hundred and eightieth year")
    assert gx.kjv_number_values("threescore cubits was the length") == {60}
    assert gx.kjv_number_values("the breadth thereof twenty cubits") == {20}
    assert gx.kjv_number_values("and the height thereof thirty cubits") == {30}
    assert gx.kjv_number_values("the house of the LORD") == set()
```
- [ ] **Step 2 — run, FAIL.**
- [ ] **Step 3 — implement `kjv_number_values(text) -> set[int]`.** Lowercase + tokenize on non-letters. Maps: `_UNITS` (one…nineteen + ordinals first…nineteenth → 1–19), `_TENS` (twenty…ninety + ordinals twentieth…ninetieth → 20–90), `score`=20, `threescore`=60, `fourscore`=80, `hundred`/`hundredth`=×100, `thousand`=×1000. Parse left→right accumulating standard English number grammar (`current` + `result`; `hundred`/`thousand` multiply `current`), emitting a value at conjunction/segment boundaries; collect every distinct integer found into a set. Handle the ordinal forms (`eightieth`→80) the same as cardinals for matching. ("four hundred and eightieth" → 4*100 then +80 → 480.) Keep it bounded to ≤ thousands (the corpus has no larger numbers).
- [ ] **Step 4 — run, PASS.**
- [ ] **Step 5 — commit.** `Phase B2: KJV English number-word parser`

## Task B3: Ge'ez↔KJV proper-noun seed map + matcher

**Files:** Modify `scripts/core/geez_kjv_xref.py`; Test same.

- [ ] **Step 1 — failing test.**
```python
def test_proper_noun_hits_1ki6_v1():
    geez_tokens = ["ወእምዝ", "ሰሎሞን", "እስራኤል", "ግብጽ", "እግዚእብሔር", "ቤተ"]
    kjv = ("…children of Israel were come out of the land of Egypt … "
           "Solomon … began to build the house of the LORD")
    hits = gx.proper_noun_hits(geez_tokens, kjv)
    assert {"solomon", "israel", "egypt"} <= hits
    # cherub / lebanon appear later in 1ki6
    assert gx.proper_noun_hits(["ኪሩብ"], "the cherubims of olive tree") == {"cherub"}
    assert gx.proper_noun_hits(["ሊባኖስ"], "cedar trees out of Lebanon") == {"lebanon"}

def test_proper_noun_no_false_hit():
    assert gx.proper_noun_hits(["ቤተ", "ወርሐ"], "Solomon built the house") == set()
```
- [ ] **Step 2 — run, FAIL.**
- [ ] **Step 3 — implement.** `_GEEZ_KJV_NAMES` = a curated dict of recurring Kings/Samuel proper nouns mapping the Ge'ez surface form (and obvious orthographic variants) → the lowercase KJV English term, seeded from the spec + 1ki6/Samuel content: `ሰሎሞን→solomon, እስራኤል→israel, ግብጽ→egypt, ሊባኖስ→lebanon, ኪሩብ→cherub, እግዚእብሔር→lord, ዳዊት→david, ኢየሩሳሌም→jerusalem, ሒራም/ኪራም→hiram, ይሁዳ→judah, ሳኦል→saul, ሳሙኤል→samuel`. `proper_noun_hits(geez_tokens, kjv_text)`: lowercase `kjv_text`; for each geez token that is a key (strip a leading prefix conjunction `ወ`/preposition `በ/ለ/እም` if the bare stem is a key), if its English term appears as a word/substring in the lowercased KJV text, add the term. Return the `set[str]` of matched terms. (Curated map, NOT pure transliteration — `ግብጽ` does not transliterate to "egypt".)
- [ ] **Step 4 — run, PASS.**
- [ ] **Step 5 — commit.** `Phase B3: Ge'ez↔KJV proper-noun seed map + matcher`

## Task B4: anchor + order-preserving interpolation (`build_kjv_xref`)

**Files:** Modify `scripts/core/geez_kjv_xref.py`; Test same.

- [ ] **Step 1 — failing test.**
```python
import json
def _load_v2(book, ch):
    tr = "kings" if book in {"1ki","2ki"} else "samuel"
    return json.load(open(f"content/manuscript/{tr}/collation/{book}{ch}_collation_v2.json", encoding="utf-8"))

def test_build_kjv_xref_1ki6_anchors():
    from scripts.core.manuscript_collation import load_kjv_skeleton
    col = _load_v2("1ki", 6)
    kjv_rows = load_kjv_skeleton("1ki", 6)
    xref = gx.build_kjv_xref(col, kjv_rows, "1ki")
    # every base verse gets an entry, tagged honestly
    assert set(xref) == {pv["geez_v"] for pv in col["primary_verses"]}
    for e in xref.values():
        assert e["confidence"] in {"anchored", "interpolated"}
        assert e["kjv"] and all(len(t) == 3 for t in e["kjv"])
    # the two hard anchors
    assert xref[1]["confidence"] == "anchored" and xref[1]["kjv"] == [["1ki", 6, 1]]
    assert xref[2]["confidence"] == "anchored" and [t[2] for t in xref[2]["kjv"]] == [2]
    # monotonic non-decreasing in KJV verse across base order
    seq = [xref[pv["geez_v"]]["kjv"][0][2] for pv in col["primary_verses"]]
    assert seq == sorted(seq)
```
- [ ] **Step 2 — run, FAIL.**
- [ ] **Step 3 — implement `build_kjv_xref(collation, kjv_rows, book) -> dict`.**
  - For each base verse `i`: `nums = verse_numerals(tokens)`, and score each KJV row `(kch,kv,ktext)` by `len(nums & kjv_number_values(ktext)) + len(proper_noun_hits(tokens, ktext))`. The best-scoring KJV verse (score>0, lowest verse on ties) is a candidate hard anchor `cand[i] = kv`.
  - **Monotonic filter:** keep the longest non-decreasing subsequence of `cand` by base order (drop anchors that violate monotonicity — a mis-match can't reorder the spine). The survivors are the confirmed anchors.
  - **Interpolate** the rest: between consecutive anchors `(i→a, j→b)` distribute base verses `i+1..j-1` across KJV verses `a..b` order-preserving (`kv = a + round((k-i)/(j-i) * (b-a))`, clamped non-decreasing); before the first / after the last anchor, extend proportionally over `[1, len(kjv_rows)]`. If NO anchor exists at all, fall back to a straight proportional map base→KJV (all `interpolated`).
  - Output `{geez_v: {"kjv": [[book, chapter, kv]], "confidence": "anchored"|"interpolated"}}`. (A base verse spanning multiple KJV verses MAY list >1 `kv`; for v1 of the plan, one `kv` per base verse is sufficient and the test only requires a non-empty list.)
  - Add `kjv_coverage(xref) -> dict` returning `{"base_verses": N, "anchored": a, "interpolated": N-a, "anchored_pct": round(a/N*100,2)}`.
- [ ] **Step 4 — run, PASS.**
- [ ] **Step 5 — commit.** `Phase B4: build_kjv_xref anchor + monotonic interpolation + coverage`

## Task B5: integrate `kjv_xref` into the v2 collations

**Files:** Create `scripts/apply_kjv_xref.py`; Modify `tests/test_manuscript_collation_basestructured.py`

- [ ] **Step 1 — failing test** (add to `tests/test_manuscript_collation_basestructured.py`):
```python
import pytest
XREF_DONE = [("1ki",1),("1ki",2),("1ki",3),("1ki",4),("1ki",5),("1ki",6),("1sa",1),("1sa",3),("1sa",17),("2sa",11)]

@pytest.mark.parametrize("book,chapter", XREF_DONE)
def test_v2_has_kjv_xref(book, chapter):
    import json
    tr = "kings" if book in {"1ki","2ki"} else "samuel"
    out = json.load(open(f"content/manuscript/{tr}/collation/{book}{chapter}_collation_v2.json", encoding="utf-8"))
    assert "kjv_xref" in out and set(out["kjv_xref"]) == {str(pv["geez_v"]) for pv in out["primary_verses"]}
    assert out["metrics"]["kjv_coverage"] is not None and out["metrics"]["kjv_coverage"]["base_verses"] == len(out["primary_verses"])

def test_1ki6_known_anchors_after_integration():
    import json
    out = json.load(open("content/manuscript/kings/collation/1ki6_collation_v2.json", encoding="utf-8"))
    assert out["kjv_xref"]["1"]["confidence"] == "anchored"
    assert out["kjv_xref"]["1"]["kjv"][0] == ["1ki", 6, 1]
```
(Note: JSON object keys are strings, so `geez_v` keys serialize as `"1"`, `"2"`, … — the integration writes string keys; assert with `str(...)`.)
- [ ] **Step 2 — run, FAIL** (no `kjv_xref` yet).
- [ ] **Step 3 — implement `scripts/apply_kjv_xref.py`.** `DONE_CHAPTERS` = the 10 tuples. For each: load the v2 (`content/manuscript/{track}/collation/{ref}_collation_v2.json`), `kjv_rows = load_kjv_skeleton(book, ch)`, `xref = build_kjv_xref(col, kjv_rows, book)`, set `col["kjv_xref"] = xref` and `col["metrics"]["kjv_coverage"] = geez_kjv_xref.kjv_coverage(xref)`, atomic-rewrite (temp + `os.replace`, deterministic `json.dump(..., ensure_ascii=False, indent=2)`). `run(targets=DONE_CHAPTERS) -> {"written":[...], "failed":[...]}` + a `main()`. (For an Ethiopian-only book with no KJV file, `load_kjv_skeleton` would raise — guard: skip + leave `kjv_xref` absent / `kjv_coverage=None`. The 10 Phase-B chapters are all in KJV.)
- [ ] **Step 4 — run the driver, then run, confirm PASS.** `& "<python>" -m scripts.apply_kjv_xref` → 10 written; then pytest green. `git status` shows ONLY the 10 v2 files + the new script + the test changed; **zero `calibration/` changes**.
- [ ] **Step 5 — regression + commit + backup.** Run `tests/test_manuscript_collation.py -q` (45) + the full base-structured file; `ruff format` the new script + test; `scripts/lint_rules.py` clean (add `apply_kjv_xref.py` / `geez_kjv_xref.py` to `dev/REPO_MAP.md` if flagged). Commit `Phase B5: fold kjv_xref + kjv_coverage into the 10 v2 collations`; then `git bundle --all` to E:/F:.

---

## PHASE B done-criteria
- `geez_kjv_xref.py` pure engine (numeral + English-number + proper-noun + anchor/interpolate), fully unit-tested.
- All 10 v2 collations carry an honest `kjv_xref` (every base verse tagged `anchored`/`interpolated`) + `metrics["kjv_coverage"]`.
- 1ki6 known anchors validated (v1→6:1, v2→6:2). Samuel goldens + witnesses byte-untouched. Engine regression 45/45 green.

## Optional / deferred (NOT core B tasks)
- Reviewer-note KJV references as a third anchor source (spec §3.3 "where present") — low yield, fold in later only if a chapter's notes carry explicit KJV citations.
- A base verse mapping to a *range* of KJV verses (multi-`kv`) — v1 emits one best `kv` per base verse; widen later if Phase C rendering needs explicit ranges.

## Self-review (against spec §3.3)
- **Numerals → int + match:** B1 (Ge'ez) + B2 (KJV English) + B4 scoring. ✓
- **Proper-noun transliteration match:** B3 (curated seed map — corrected from "pure transliteration" since `ግብጽ`≠"egypt"). ✓
- **Order-preserving interpolation between anchors:** B4 monotonic filter + interpolate. ✓
- **Confidence anchored vs interpolated, honest:** B4 output + B5 assertions. ✓
- **Sidecar folded into collation, never the witnesses:** B5 writes only `*_collation_v2.json`; `kjv_xref` is a top-level key + `metrics.kjv_coverage`. ✓
- **Ethiopian-only books → xref absent:** B5 guard. ✓
- **Placeholder scan:** every task has concrete grounded tests (1ki6 data) + a precise algorithm; no TBD/TODO. ✓
- **Name consistency:** `numeral_token_value`, `verse_numerals`, `kjv_number_values`, `proper_noun_hits`, `build_kjv_xref`, `kjv_coverage`, `kjv_xref` used consistently across B1–B5. ✓
