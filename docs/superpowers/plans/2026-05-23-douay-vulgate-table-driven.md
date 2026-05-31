# Douay-Rheims + Clementine Vulgate (table-driven) Implementation Plan
**Status:** shipped — Douay-Rheims + Clementine Vulgate ingested

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Douay-Rheims (`douay`) and Clementine Vulgate (`vulgate`) verse popups across the 9 non-geez/amharic editions, with versification derived from the authoritative Copenhagen `vul.json` table instead of hand-aligned word-overlap.

**Architecture:** One shared `versification.vulgate_to_kjv` adapter (both translations share Vulgate numbering) whose `_VULGATE_SEGMENTS` are *generated* from `vul.json` composed to KJV, then verified against the real eBible data and the existing `_vg_verify.py` SHIFTS gate. Two thin drivers reuse the proven `extract_translation.extract(remap=…)` pipeline. Bake by flipping `popup_versions._BAKED_NOW`, regenerating, and proving additive-only via aside-id diff.

**Tech Stack:** Python 3.14, the project's `scripts/` package, pytest. Reference data: Copenhagen Alliance `vul.json`/`eng.json` (CC BY-SA — facts extracted, file NOT vendored).

**Spec:** `docs/superpowers/specs/2026-05-23-douay-vulgate-table-driven-design.md`

---

## Project conventions for the executing agent (READ FIRST — these override the generic skill defaults)

- **Python interpreter (full path — bare `python` is a broken Windows Store stub):**
  `$py = "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe"`
- **Every test/script run needs UTF-8:** `$env:PYTHONUTF8 = "1"` (else ~72 tests fail with cp1252 errors).
- **Run ONE test file at a time.** NEVER run the full `tests/test_scripts.py` (hangs on build/socket smokes — use targeted `-k` or other files). Broad `pytest tests/` sweeps can MemoryError under RAM pressure.
- **NO `git commit` per task.** This repo commits ONLY via `save.cmd`/`save.ps1` when the USER says "save" ("continue" ≠ "save"). Replace every "Commit" step with a **Checkpoint** (verify green, leave staged-on-disk). A single user-initiated `save` lands the whole arc at the end. Never run `save.cmd` via the Bash tool (spaced path + arrow glyphs corrupt it) — PowerShell only, and only on user instruction.
- **Throwaway tooling lives in the repo PARENT** `C:\Users\bogda\Documents\YHWH-v2.4-full\` (outside git): the `_vg_*.py`, `_aside_compare.py`, `_probe_*.py`, and the downloaded `_vrs_vul.json` / `_vrs_eng.json` are already there.
- **Greek/accented text:** verify by Read, not Grep (NFC mismatch). Not central here (Latin/English), but the Daniel cross-book checks touch paz.
- **All shell examples below are PowerShell**, run from the repo root `C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\`.

Definition of the `_Seg` tuple (already in `scripts/core/versification.py`): `(_src_lo, _src_hi, _kjv_ch | None, _kjv_v_lo)`; `_HI = 9999`; a verse `v` in `[lo,hi]` → `(kjv_ch, kjv_v_lo + (v - lo))`; `kjv_ch is None` → omit. `_apply_segments` returns identity for chapters not in the table and `None` for an unmapped verse inside a remapped chapter (never misplace).

---

## File structure

| File | Responsibility | Create/Modify |
|---|---|---|
| `../_vg_gen.py` (repo parent) | Parse `_vrs_vul.json`, compose `vul→org→KJV`, emit candidate `_VULGATE_SEGMENTS` + a discrepancy report. Throwaway. | Create |
| `scripts/core/versification.py` | `vulgate_to_kjv` + `_VULGATE_SEGMENTS`/`_VULGATE_PSALM_FIXES`/`_VULGATE_CROSS` filled; add the cross-book intercept branch. | Modify (`~764-833`) |
| `scripts/extract_vulgate.py` | Thin driver: `extract("vulgate-clementine", remap=vulgate_to_kjv)`. | Create |
| `scripts/extract_douay.py` | Thin driver: `extract("douay-rheims", remap=vulgate_to_kjv)` + the Douay-only per-source verse-split overrides. | Create |
| `scripts/core/popup_versions.py` | Add `douay`,`vulgate` to `_BAKED_NOW`. | Modify (`116`) |
| `content/translations/{vulgate-clementine,douay-rheims}/*.py` | Generated verse stores. | Create (by driver) |
| `epub_working/index_split_*.html` | Baked asides (regenerated). | Modify (by regen) |
| `tests/test_vulgate_douay_ingest.py` | All TDD pins for the adapter + drivers + on-disk stores. | Create |
| `dev/CHANGELOG.md`, `dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md`, `dev/MATRIX_MAP.md` | Ship record + Copenhagen/UBS-SIL credit. | Modify |

---

## Phase A — Generator + discrepancy adjudication (the methodology core)

### Task 1: Write `_vg_gen.py` — compose the table to KJV and emit segments + discrepancy report

**Files:**
- Create: `C:\Users\bogda\Documents\YHWH-v2.4-full\_vg_gen.py`

- [ ] **Step 1: Write the generator.** It must (a) load `_vrs_vul.json` `mappedVerses` (Vulgate→org) and `_vrs_eng.json` `mappedVerses` (eng→org); (b) build per-(book,ch,vs) `vul→org`; (c) convert `org→KJV` for the small known eng/org deltas only (3jn, rev, mal, joe, the Daniel 3/4 boundary) using `eng.json`, else `org≈KJV`; (d) translate eBible/USFM book codes (`DAG`/`DAN`,`S3Y`,`SUS`,`BEL`,`LJE`,…) to project codes; (e) emit a `_VULGATE_SEGMENTS`-shaped dict AND a discrepancy report.

```python
"""THROWAWAY: generate candidate _VULGATE_SEGMENTS from Copenhagen vul.json and
report disagreements vs (a) the already-encoded segments and (b) the real eBible
latVUC/engDRA verse counts. Facts only — vul.json (CC BY-SA) is NOT vendored."""
import json, re, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE / "YHWH v2.4"
sys.path.insert(0, str(REPO))
from scripts.extract_translation import parse_vpl, EBIBLE_VPL_TO_PROJECT, split_baruch_letter_of_jeremiah  # noqa: E402
from scripts.core import canonical_verse_counts as cvc  # noqa: E402

# USFM (Copenhagen) book id -> project code. DAG (expanded Daniel) and DAN both -> dan;
# the additions S3Y/SUS/BEL -> paz/sus/bel (cross-book). LJE handled via BAR ch6 split.
USFM_TO_PROJECT = {
    "GEN":"gen","EXO":"exo","LEV":"lev","NUM":"num","DEU":"deu","JOS":"jos","JDG":"jdg",
    "RUT":"rut","1SA":"1sa","2SA":"2sa","1KI":"1ki","2KI":"2ki","1CH":"1ch","2CH":"2ch",
    "EZR":"ezr","NEH":"neh","EST":"est","JOB":"job","PSA":"psa","PRO":"pro","ECC":"ecc",
    "SNG":"sng","SOL":"sng","ISA":"isa","JER":"jer","LAM":"lam","EZK":"eze","EZE":"eze",
    "DAN":"dan","DAG":"dan","HOS":"hos","JOL":"joe","JOE":"joe","AMO":"amo","OBA":"oba",
    "JON":"jon","MIC":"mic","NAM":"nah","NAH":"nah","HAB":"hab","ZEP":"zep","HAG":"hag",
    "ZEC":"zec","MAL":"mal","MAT":"mat","MRK":"mrk","MAR":"mrk","LUK":"luk","JHN":"jhn",
    "JOH":"jhn","ACT":"act","ROM":"rom","1CO":"1co","2CO":"2co","GAL":"gal","EPH":"eph",
    "PHP":"phi","PHI":"phi","COL":"col","1TH":"1th","2TH":"2th","1TI":"1ti","2TI":"2ti",
    "TIT":"tit","PHM":"phm","HEB":"heb","JAS":"jam","JAM":"jam","1PE":"1pe","2PE":"2pe",
    "1JN":"1jo","1JO":"1jo","2JN":"2jo","2JO":"2jo","3JN":"3jo","3JO":"3jo","JUD":"jud",
    "REV":"rev","WIS":"wis","SIR":"sir","BAR":"bar","LJE":"lje","S3Y":"paz","SUS":"sus",
    "BEL":"bel","1MA":"1ma","2MA":"2ma","TOB":"tob","JDT":"jdt","MAN":"man","1ES":"1es",
}
REF = re.compile(r"^([0-9A-Z]{3}) (\d+):(\d+)$")

def expand(side):
    """'GEN 32:1-32' -> [(GEN,32,1),...]; single -> one tuple. Returns flat list."""
    book, rng = side.split(" ", 1)
    ch, vrange = rng.split(":")
    lo, hi = (vrange.split("-") + [vrange])[:2] if "-" in vrange else (vrange, vrange)
    return [(book, int(ch), v) for v in range(int(lo), int(hi) + 1)]

def load_map(path):
    """{(book,ch,vs): (book,ch,vs)} tradition->org, expanding ranges pairwise."""
    mv = json.loads(Path(path).read_text(encoding="utf-8"))["mappedVerses"]
    out = {}
    for src, dst in mv.items():
        srcs, dsts = expand(src), expand(dst)
        if len(srcs) == len(dsts):
            out.update(zip(srcs, dsts))
        else:  # length mismatch (merge/split) -> flag, map head, report later
            out[srcs[0]] = (dsts[0], "LENMISMATCH", src, dst)
    return out

# (Step 1 continues: compose vul->org->KJV, regroup into project (code,ch)->segments,
#  and diff vs versification._VULGATE_SEGMENTS + the real parse_vpl(latVUC) counts.
#  Print three report sections: TABLE_VS_ENCODED, TABLE_VS_SOURCEDATA, LENMISMATCH.)
```

- [ ] **Step 2: Run it.**

Run (PowerShell):
```powershell
$py = "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$env:PYTHONUTF8 = "1"
& $py "..\_vg_gen.py" > "..\_vg_gen_report.txt" 2>&1; Get-Content "..\_vg_gen_report.txt"
```
Expected: a candidate `_VULGATE_SEGMENTS` block + three report sections. No traceback.

- [ ] **Step 3: Checkpoint.** Eyeball the report exists and parses. (No commit — throwaway tool.)

### Task 2: Adjudicate the discrepancy report against source text

**Files:** none (analysis); produces the verified segment text used in Tasks 4-6.

- [ ] **Step 1: For every `TABLE_VS_ENCODED` disagreement, read the Douay + KJV verses and decide.** Known case: `gen 49` (table: shift at Vulgate v31 → KJV v32; encoded segment starts at v32). Confirm against `engDRA` `GEN 49:30-33` vs KJV. Use `_vg_win.py gen` (repo parent worksheet) to print the aligned columns.

```powershell
& $py "..\_vg_win.py" gen   # worksheet: Douay vs KJV columns around the divergence
```

- [ ] **Step 2: For every `TABLE_VS_SOURCEDATA` row, trust the SOURCE DATA shape, not the table** (the table is generic Vulgate; eBible `latVUC`/`engDRA` is the actual text we ship). Record any book where they differ as a per-source override (Task 9) or a corrected segment.

- [ ] **Step 3: For `LENMISMATCH` rows (merges/splits the range form can't auto-pair), hand-encode the segment** by reading the text. Expected set is small (Psalms verse-0 splits, a few OT).

- [ ] **Step 4: Checkpoint.** Save the adjudicated segment block into a scratch note (`..\_vg_segments_verified.txt`) for pasting into Tasks 4-6.

---

## Phase B — versification adapter (TDD)

### Task 3: Add the `_VULGATE_CROSS` cross-book branch to `vulgate_to_kjv`

**Files:**
- Modify: `scripts/core/versification.py` (`_VULGATE_CROSS` at `811`, `vulgate_to_kjv` at `814`)
- Test: `tests/test_vulgate_douay_ingest.py`

- [ ] **Step 1: Write the failing test.**

```python
# tests/test_vulgate_douay_ingest.py
import pytest

class TestVulgateCrossBook:
    """Vulgate/Douay inline the Daniel additions under DAN; they relocate to
    separate project books. The Vulgate Song-of-Three is a CLEAN offset
    (DAN 3:24-90 -> paz 1:1-67), NOT the LXX Theodotion reorder."""

    def test_prayer_of_azariah_clean_offset(self):
        from scripts.core.versification import vulgate_to_kjv
        assert vulgate_to_kjv("dan", 3, 24) == ("paz", 1, 1)
        assert vulgate_to_kjv("dan", 3, 90) == ("paz", 1, 67)

    def test_susanna_is_daniel_13(self):
        from scripts.core.versification import vulgate_to_kjv
        assert vulgate_to_kjv("dan", 13, 1) == ("sus", 1, 1)

    def test_bel_is_daniel_14(self):
        from scripts.core.versification import vulgate_to_kjv
        assert vulgate_to_kjv("dan", 14, 1) == ("bel", 1, 1)
```

- [ ] **Step 2: Run it, verify it fails.**

```powershell
& $py -m pytest tests/test_vulgate_douay_ingest.py::TestVulgateCrossBook -v
```
Expected: FAIL (e.g. `vulgate_to_kjv("dan",3,24)` currently returns `("dan",3,24)` or `None`, not `("paz",1,1)`).

- [ ] **Step 3: Implement the cross-book branch.** Add `_vulgate_cross` and intercept it at the top of `vulgate_to_kjv` (mirroring `lxx_swete_to_kjv`'s `_cross_book`). The paz offset is the clean `−23` confirmed in `vul.json` (`DAN 3:24-90 → S3Y 1:1-67`).

```python
def _vulgate_cross(code: str, ch: int, vs: int) -> Coord | None:
    """Daniel additions inlined under the Vulgate/Douay 'dan' book relocate to
    separate project books. Verified from vul.json (Vulgate numbering):
      - DAN 3:24-90 -> paz 1:1-67  (Prayer of Azariah / Song of the Three; clean -23)
      - DAN 13      -> sus 1       (Susanna)
      - DAN 14      -> bel 1       (Bel and the Dragon)
    The KJV-canonical Daniel verses (3:1-23, the 3/4 boundary, 4-12) are handled
    by _VULGATE_SEGMENTS['dan'], NOT here."""
    if code != "dan":
        return None
    if ch == 3 and 24 <= vs <= 90:
        return ("paz", 1, vs - 23)
    if ch == 13:
        return ("sus", 1, vs)
    if ch == 14:
        return ("bel", 1, vs)
    return None
```

Then at the top of `vulgate_to_kjv`, before the `_VULGATE_OMIT` check:
```python
    cross = _vulgate_cross(code, ch, vs)
    if cross is not None:
        return cross if coord_in_canonical_extent(*cross) else None
```

- [ ] **Step 4: Run it, verify it passes.**

```powershell
& $py -m pytest tests/test_vulgate_douay_ingest.py::TestVulgateCrossBook -v
```
Expected: PASS (3 tests).

- [ ] **Step 5: Checkpoint** (no commit). Confirm `& $py -m pytest tests/test_lxx_swete_ingest.py -q` still green (the paz/dan LXX path is untouched).

### Task 4: Fill `_VULGATE_SEGMENTS` (protocanon) from the verified generator output

**Files:**
- Modify: `scripts/core/versification.py` (`_VULGATE_SEGMENTS` at `775-803`)
- Test: `tests/test_vulgate_douay_ingest.py`

- [ ] **Step 1: Write failing tests pinning the cross-chapter cases** (the ones the old per-chapter aligner could not see — these are the highest-value correctness checks).

```python
class TestVulgateProtoSegments:
    @pytest.mark.parametrize("code,ch,vs,expected", [
        ("num", 13, 1, ("num", 12, 16)),   # cross-chapter: spies boundary
        ("num", 13, 2, ("num", 13, 1)),
        ("deu", 29, 1, ("deu", 28, 69)),   # cross-chapter
        ("2ch", 2, 1, ("2ch", 1, 18)),     # cross-chapter
        ("1ki", 4, 21, ("1ki", 5, 1)),     # cross-chapter (Solomon's provisions)
        ("1sa", 20, 43, ("1sa", 21, 1)),   # cross-chapter
        ("jos", 21, 37, ("jos", 21, 39)),  # in-chapter offset
        ("gen", 1, 1, ("gen", 1, 1)),      # identity sanity
        ("mat", 17, 15, ("mat", 17, 16)),  # NT (already encoded) still correct
    ])
    def test_segment_maps(self, code, ch, vs, expected):
        from scripts.core.versification import vulgate_to_kjv
        assert vulgate_to_kjv(code, ch, vs) == expected
```

- [ ] **Step 2: Run, verify failure** (most pairs not yet encoded).

```powershell
& $py -m pytest tests/test_vulgate_douay_ingest.py::TestVulgateProtoSegments -v
```
Expected: FAIL for the unencoded cross-chapter pairs.

- [ ] **Step 3: Paste the adjudicated `_VULGATE_SEGMENTS` from Task 2** into `versification.py`, replacing the WIP dict (keep the already-verified NT/prophet/Genesis entries, correcting `gen 49` per Task 2's finding). The entries are the generator's verified output — each line content-aligned, e.g.:

```python
    "num": {
        13: [(1, 1, 12, 16), (2, _HI, 13, 1)],   # Vulgate 13:1 = KJV 12:16 (cross-ch)
        # ...remaining num divergences from the report (16/17 swap, 26 boundary, ...)
    },
    "deu": {29: [(1, 1, 28, 69), (2, _HI, 29, 1)]},
    "2ch": {2: [(1, 1, 1, 18), (2, _HI, 2, 1)]},
    # ...all protocanon books flagged by the generator
```

- [ ] **Step 4: Run, verify pass.**

```powershell
& $py -m pytest tests/test_vulgate_douay_ingest.py::TestVulgateProtoSegments -v
```
Expected: PASS.

- [ ] **Step 5: Checkpoint** (no commit).

### Task 5: Psalms — reuse `_psalm_map`, add `_VULGATE_PSALM_FIXES`, cross-check vs `vul.json`

**Files:**
- Modify: `scripts/core/versification.py` (`_VULGATE_PSALM_FIXES` at `767`)
- Test: `tests/test_vulgate_douay_ingest.py`

- [ ] **Step 1: Write failing tests.**

```python
class TestVulgatePsalms:
    def test_reuses_lxx_psalm_scheme(self):
        from scripts.core.versification import vulgate_to_kjv
        # Vulgate Ps 9 covers KJV 9+10; Ps 113 covers KJV 114+115; etc.
        assert vulgate_to_kjv("psa", 9, 22)[:2] == ("psa", 10)   # Vulgate 9:22 -> KJV 10:x
        assert vulgate_to_kjv("psa", 23, 1) == ("psa", 23, 1)    # identity zone
    def test_per_psalm_fixes_present(self):
        from scripts.core.versification import vulgate_to_kjv
        # psa 20/44/56: Latin verse-split differs; last KJV verse must still map.
        for p in (20, 44, 56):
            last = vulgate_to_kjv("psa", p, 1)
            assert last is not None and last[0] == "psa"
```

- [ ] **Step 2: Run, verify failure** for any psalm the bare `_psalm_map` misses (psa 20/44/56 tail).

```powershell
& $py -m pytest tests/test_vulgate_douay_ingest.py::TestVulgatePsalms -v
```

- [ ] **Step 3: Encode `_VULGATE_PSALM_FIXES`** for psa 20/44/56 from Task 2's report (cross-checked against `vul.json` PSA entries). Example shape:
```python
_VULGATE_PSALM_FIXES: dict[tuple[int, int], tuple[int, int]] = {
    # (vulgate_ch, vulgate_vs): (kjv_ch, kjv_vs) — the few psalms whose Latin
    # split differs from the reused LXX _psalm_map (verified vs vul.json + Douay).
    (20, 14): (20, 13),  # example — replace with the report's verified values
}
```

- [ ] **Step 4: Run, verify pass.** Expected: PASS.

- [ ] **Step 5: Checkpoint** (no commit).

### Task 6: OMIT set + `wis` include + Esther-additions auto-omit

**Files:**
- Modify: `scripts/core/versification.py` (`_VULGATE_OMIT` at `809`)
- Test: `tests/test_vulgate_douay_ingest.py`

- [ ] **Step 1: Write the tests.**

```python
class TestVulgateInclusionPolicy:
    def test_recension_books_omitted(self):
        from scripts.core.versification import vulgate_to_kjv
        for code in ("tob", "jdt", "sir"):
            assert vulgate_to_kjv(code, 1, 1) is None  # different recension -> no popup
    def test_wisdom_included(self):
        from scripts.core.versification import vulgate_to_kjv
        assert vulgate_to_kjv("wis", 1, 1) == ("wis", 1, 1)  # table maps it -> include
    def test_esther_greek_additions_auto_omit(self):
        from scripts.core.versification import vulgate_to_kjv
        # Vulgate Esther additions live at 10:4+ / 11-16 -> outside KJV extent -> None
        assert vulgate_to_kjv("est", 11, 2) is None
        assert vulgate_to_kjv("est", 10, 13) is None
```

- [ ] **Step 2: Run, verify** (`_VULGATE_OMIT` already = `{tob,jdt,sir}`; `wis`/`est` rely on identity + the extent guard). Most should pass already; fix any that don't.

```powershell
& $py -m pytest tests/test_vulgate_douay_ingest.py::TestVulgateInclusionPolicy -v
```

- [ ] **Step 3: Ensure `_VULGATE_OMIT = frozenset({"tob", "jdt", "sir"})`** and that Esther/Wisdom take the identity+guard path (no special-casing needed). Add an inline comment that `wis` is intentionally included (overturning the prior "maybe omit").

- [ ] **Step 4: Run, verify pass.**

- [ ] **Step 5: Checkpoint** (no commit).

### Task 7: SHIFTS=0 gate across all books (`_vg_verify.py`)

**Files:** none (verification gate using the existing repo-parent tool).

- [ ] **Step 1: Run the structural+overlap gate per divergent book.**

```powershell
& $py "..\_vg_verify.py" --all   # applies vulgate_to_kjv to engDRA, checks SHIFTS=0 + overlap
```
Expected: `SHIFTS = 0` for every included book; a low-overlap flag ONLY on a genuinely-different recension (which must already be in `_VULGATE_OMIT`).

- [ ] **Step 2: For any SHIFTS>0 book, return to Task 4/5** and correct that book's segment from the text. Re-run until clean.

- [ ] **Step 3: Checkpoint** (no commit). Record the final per-book SHIFTS=0 result for the CHANGELOG.

---

## Phase C — drivers, bake, validation

### Task 8: Write `extract_vulgate.py` and `extract_douay.py` thin drivers

**Files:**
- Create: `scripts/extract_vulgate.py`, `scripts/extract_douay.py`
- Test: `tests/test_vulgate_douay_ingest.py`

- [ ] **Step 1: Write the drivers** (mirror `extract_arabic_vandyke.py`).

```python
# scripts/extract_vulgate.py
"""Clementine Vulgate (latVUC) ingest — shared Vulgate->KJV adapter.
PD: Clementine Vulgate (1592/1598) is public domain by age."""
from __future__ import annotations
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from scripts.core.versification import vulgate_to_kjv  # noqa: E402
from scripts.extract_translation import extract  # noqa: E402
TRANSLATION_ID = "vulgate-clementine"

def main() -> int:
    stats = extract(TRANSLATION_ID, remap=vulgate_to_kjv, report=True)
    print(f"{TRANSLATION_ID}: {stats['project_books_emitted']} books, {stats['total_verses']:,} verses")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

`scripts/extract_douay.py` is identical except `TRANSLATION_ID = "douay-rheims"`. **Per-source overrides:** if Task 2 found chapters where the *Douay English* verse-split differs from the *Latin Vulgate*, add a `douay_to_kjv` wrapper in `versification.py` that layers those few overrides over `vulgate_to_kjv`, and import it here instead. (Expected ≤14 chapters; if Task 2 found zero real divergences in the eBible data, both drivers use `vulgate_to_kjv` directly.)

- [ ] **Step 2: Write driver tests.**

```python
class TestDrivers:
    def test_remap_none_is_byte_identity(self):
        # sanity: extract with identity remap doesn't reorder/merge a clean book
        from scripts.extract_translation import apply_remap
        data = {"gen": [(1, 1, "a"), (1, 2, "b")]}
        assert apply_remap(data, lambda c, ch, v: (c, ch, v)) == data
```

- [ ] **Step 3: Run, verify pass.**
```powershell
& $py -m pytest tests/test_vulgate_douay_ingest.py::TestDrivers -v
```

- [ ] **Step 4: Run the extractions** (writes the stores).
```powershell
$env:PYTHONUTF8 = "1"
& $py scripts\extract_vulgate.py
& $py scripts\extract_douay.py
```
Expected: ~73 books each (66 proto + wis/bar/lje/sus/bel/paz/1ma/2ma; minus tob/jdt/sir), thousands of verses, no traceback.

> **SCOPE NOTE — the Clementine appendix is NOT in this eBible source.** `man` (Prayer of Manasseh), `1es` (3 Esdras), and `2es` (4 Esdras) are live project books (existing popups: man/1es = KJV+Greek; 2es = KJV+Ge'ez+Amharic) that belong to the Clementine Vulgate's post-NT appendix. The eBible `latVUC`/`engDRA` packages omit the appendix (as does Tweedale's transcription, their likely upstream), so these three get no Latin column from THIS ingest. That is a genuine coverage gap — `2es` especially, since its Greek is lost and the Latin is the primary witness. It is addressed in **Phase E** (separate source), not by guessing here.

- [ ] **Step 5: Checkpoint** (no commit). Add on-disk integration tests mirroring `test_arabic_vandyke_ingest.py` (`test_all_coords_in_canonical_extent`, spot-check `get_verse`, book count, `paz`/`sus`/`bel` populated, `tob`/`jdt`/`sir` absent).

### Task 9: Bake — flip `_BAKED_NOW`, regenerate, prove additive-only

**Files:**
- Modify: `scripts/core/popup_versions.py:116`
- Modify: `epub_working/index_split_*.html` (by regen)

- [ ] **Step 1: Snapshot asides BEFORE** (for the aside-id diff).
```powershell
& $py "..\_aside_compare.py" --snapshot "..\_aside_before.json"
```

- [ ] **Step 2: Flip the bake gate.**
```python
_BAKED_NOW: frozenset[str] = frozenset(
    {"kjv", "wlc", "lxx-greek", "greek-nt", "arabic", "jps", "douay", "vulgate"}
)
```

- [ ] **Step 3: Regenerate popups.**
```powershell
$env:PYTHONUTF8 = "1"
& $py scripts\generate_verse_popups.py
```
Expected: completes; reports added `vnote-douay` + `vnote-vulgate` counts.

- [ ] **Step 4: Prove additive-only by aside-id** (NOT line-diff — shared split files create false line diffs).
```powershell
& $py "..\_aside_compare.py" --snapshot "..\_aside_after.json"
& $py "..\_aside_compare.py" --diff "..\_aside_before.json" "..\_aside_after.json"
```
Expected: only `vnote-douay` and `vnote-vulgate` asides ADDED; **0 changes** to any other version's aside content; 0 removed.

- [ ] **Step 5: Update the popup-version bake pin.**
```powershell
& $py -m pytest tests/test_popup_versions.py -v
```
Expected: update the `_BAKED_NOW` assertion to include douay+vulgate; PASS.

- [ ] **Step 6: Checkpoint** (no commit).

### Task 10: Integrity + epubcheck

**Files:** none (validation).

- [ ] **Step 1: `ebible verify`.**
```powershell
$env:PYTHONUTF8 = "1"
& $py scripts\ebible.py verify
```
Expected: `errors=0`, 24,015 paired (unchanged — popups don't add note-markers).

- [ ] **Step 2: Build the two Latin-surfacing editions and epubcheck them** (Java 8 off-PATH; ONE JVM at a time).
```powershell
$env:Path = "C:\Program Files\Java\jre1.8.0_491\bin;$env:Path"
& $py scripts\build_edition.py catholic-study --force --output-dir "$env:TEMP\dv_cat"
$jar = (Get-ChildItem "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\epubcheck\*.jar" | Select -First 1).FullName
& $py scripts\epubcheck.py --jar $jar "$env:TEMP\dv_cat\catholic-study.epub"
# then, separately (not concurrent):
& $py scripts\build_edition.py anglican-bcp --force --output-dir "$env:TEMP\dv_ang"
& $py scripts\epubcheck.py --jar $jar "$env:TEMP\dv_ang\anglican-bcp.epub"
```
Expected: both **0 fatals / 0 errors / 0 warnings / 0 infos**. Delete any `hs_err_pid*.log`/`replay_pid*.log` before any later `git add`.

- [ ] **Step 3: Lint.**
```powershell
& $py -m ruff format --check scripts\ scripts\core\ tests\ ; & $py scripts\lint_rules.py
```
Expected: format clean; `lint_rules` 16/0/0.

- [ ] **Step 4: Checkpoint** (no commit).

---

## Phase D — documentation & save

### Task 11: Update docs + credit, then hand off for save

**Files:**
- Modify: `dev/CHANGELOG.md`, `dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md`, `dev/MATRIX_MAP.md`
- Modify: `scripts/core/versification.py` (source-credit comment)

- [ ] **Step 1: Add the ship record** to `dev/CHANGELOG.md` (2026-05-23): table-driven D/V, book/verse counts, SHIFTS=0 per book, the `gen49` correction, `wis` included, `tob/jdt/sir` omitted, epubcheck 0/0/0/0 on catholic-study+anglican-bcp, test count.
- [ ] **Step 2: Credit** Copenhagen Alliance + UBS/SIL versification mappings in a comment above `vulgate_to_kjv` and in the CHANGELOG entry (facts used under the uncopyrightable-data rationale; CC BY-SA file not vendored).
- [ ] **Step 3: Update `dev/SESSION_STATE.md` + `dev/IN_FLIGHT.md`** — Phase-2 spine COMPLETE; move the D/V grind banner to "shipped"; note the two logged follow-ups (ethiopian_custom Ge'ez reference; prior-translation re-verify).
- [ ] **Step 4: Update `dev/MATRIX_MAP.md`** popup-version row counts.
- [ ] **Step 5: Delete throwaways** that shouldn't linger: leave `_vg_*.py`/`_vrs_*.json` in the repo PARENT (outside git, reusable for the follow-up audit); confirm none landed inside `YHWH v2.4/`.
- [ ] **Step 6: Hand off for save.** Tell the user the arc is green and ready; they run `save.cmd` (PowerShell) when ready. Do NOT commit autonomously.

---

## Phase E — Clementine appendix Latin for `man` / `1es` / `2es` (FAST-FOLLOW, after the A-D save)

> **Sequencing (decided 2026-05-23):** runs AFTER the Phase A-D save, as the first step of the *shared vision-OCR engine* arc (which also powers the Ge'ez/Amharic bulk-ingest — generalize `scripts/core/manuscript_vision.py` into a printed-PDF `--engine vision`, OOM-safe: standalone script, ≤1568px, one book at a time).
> **CLEAN-DIGITAL-FIRST (decided 2026-05-23, the HaCohen lesson):** before any OCR, search la.wikisource / Bibliotheca Augustana for a clean Clementine *Oratio Manassae* + *Esdrae III/IV* Latin text. If found → Phase E is a simple parse like `ingest_hacohen.py` (no OCR, `digitized-critical-edition` quality). Only if no clean text exists → vision-OCR a PD scan (e.g. Hetzenauer 1914) via the shared engine. `2es` (4 Esdras) is the priority — its Greek is lost, so the Latin is the primary witness.

### Task 12: Acquire + ingest the Clementine appendix (Prayer of Manasseh, 3 Esdras, 4 Esdras)

**Files:**
- Create: `content/translations/sources/vulgate-clementine-appendix/` (PD scan-derived Latin text + provenance)
- Modify: `scripts/extract_vulgate.py` (also read the appendix source), `scripts/core/versification.py` (`vulgate_to_kjv` appendix coords)
- Test: `tests/test_vulgate_douay_ingest.py`

- [ ] **Step 1: Acquire a PD Clementine edition that INCLUDES the appendix.** Candidate: Hetzenauer's *Biblia Sacra Vulgatae Editionis* (1914, archive.org) or another pre-1929 Clementine printing with *Oratio Manassae* + *Esdrae III* + *Esdrae IV*. Record the archive.org id + page range in a provenance file. (The Tweedale/eBible texts do NOT have it — confirmed.)
- [ ] **Step 2: Extract the three books' Latin** (OCR → clean → VPL-shape), verifying verse extents against `canonical_verse_counts` for `man` (1 ch), `1es`, `2es` (note 4 Esdras = the full 16-ch text: 5 Ezra ch1-2 + 4 Ezra ch3-14 + 6 Ezra ch15-16, matching the KJV 2 Esdras the project already stores).
- [ ] **Step 3: Map coords** — `man`/`1es`/`2es` are mostly identity onto the project's existing KJVA-based skeleton; encode any per-book offset in `vulgate_to_kjv` (verified against the project's existing `2es`/`man`/`1es` KJV stores by chapter-count and content spot-check). Add tests pinning `vulgate_to_kjv("2es",1,1)`, `("man",1,1)`, `("1es",1,1)`.
- [ ] **Step 4: Re-bake** (`generate_verse_popups.py`) and re-diff (`_aside_compare.py`) — additive-only, now adding `vnote-vulgate` (and `vnote-douay` if the Douay appendix English is also sourced) to man/1es/2es.
- [ ] **Step 5: Validate** — `ebible verify` errors=0; epubcheck catholic-study (which carries the deuterocanon) 0/0/0/0.
- [ ] **Step 6: Checkpoint** (no commit) + CHANGELOG note. Folds into the same user `save`.

---

## Self-review

- **Phase E coverage:** the man/1es/2es Latin gap is no longer silently omitted — it has an explicit scope note (Task 8) + a sourcing task (Task 12) with a concrete PD source and the 4-Esdras structure documented. Sequencing is a user decision, not a guess.
- **Spec coverage:** generator+report (Task 1-2) ✓; license facts-only (Task 11 credit, no vendor) ✓; `wis` include (Task 6) ✓; `tob/jdt/sir` omit (Task 6) ✓; Daniel cross-book (Task 3) ✓; Psalms reuse+fixes (Task 5) ✓; cross-chapter correctness (Task 4) ✓; drivers+14-overrides (Task 8) ✓; bake additive-only (Task 9) ✓; ebible verify + epubcheck 2 editions (Task 10) ✓; follow-ups logged (Task 11) ✓.
- **Placeholder scan:** the `_VULGATE_SEGMENTS`/`_VULGATE_PSALM_FIXES` bodies are intentionally produced by the generator (Task 1-2) and pasted in Task 4-5 — the plan shows the shape + verified anchor tests rather than inventing ~75 tuples from memory (which would be guessing). The `(20,14):(20,13)` psalm-fix value is marked "replace with the report's verified values." Acceptable: the mechanism is fully specified; the data is generated, not hand-waved.
- **Type consistency:** `vulgate_to_kjv(code,ch,vs) -> Coord|None`, `_vulgate_cross` returns `Coord|None`, `_Seg=(lo,hi,kjv_ch|None,kjv_v_lo)`, `coord_in_canonical_extent(*cross)` — consistent with the existing `lxx_swete_to_kjv`/`_cross_book` shapes read from the source.
- **Save-convention adaptation:** every "Commit" replaced by "Checkpoint"; single user-initiated `save` at the end (project rule overrides the skill's frequent-commit default).
