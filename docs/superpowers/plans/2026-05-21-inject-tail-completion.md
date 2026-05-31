# Inject-Tail Completion (base-HTML irregular-layout robustness) Implementation Plan
**Status:** shipped — inject coverage ~99.76% via the boundary-aware spill resolver

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take EPUB note placement from the current **52,553 / 52,973 (99.21%)** to ~100% by making the note injector robust to the recovered base HTML's irregular split-file layout, then rendering the genuinely-absent chapters and documenting the true versification gaps — without rewriting the base HTML that 80+ working books depend on.

**Architecture:** The base scripture HTML (`epub_working/index_split_*.html`) is a *recovered artifact* — there is **no in-repo WEB source and no renderer** (`scripts/build_epub.py` only zips the existing files). For most books each chapter is regular: a chapter anchor `id="ch-{bxx}-c{ch}"` sits in the scripture region immediately before that chapter's verses, with a per-chapter notes-section nearby. For ~12 irregular books (jer, isa, 1ch, psa, Mäqabyan, jub, sir, rom…) the layout is split: the chapter's verse text (correctly `<span class="vn">N</span>`-marked) lives in one split file while the only `id="ch-{bxx}-c{ch}"` anchor lives in a *notes* region of a different file. `inject.find_chapter_region_b` therefore selects the anchor's file and lands a verse-less region → the verse can't be located → the note is dropped ("verse region not parseable", 241 notes). The fix resolves each Strategy-B chapter's verse region from **where the verses physically are** (walking `<span class="vn">` spans in document order across the book's files, assigning chapters with the canonical verse-count map as the authority), and places the aside in the verse's file via the already-shipped `ensure_notes_section_a`. This is contained to `scripts/inject.py` + tests; the base HTML is untouched. Two smaller follow-ons render the absent deuterocanon chapters (aes, 110) and audit the remaining versification mismatches (69).

**Tech Stack:** Python 3.14 (run via `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe` with `$env:PYTHONUTF8="1"`), pytest, ruff (config in `pyproject.toml`: select E/W/F/B/UP/SIM/N/C90, line-length 120). No new dependencies. Existing modules: `scripts/inject.py`, `scripts/core/canonical_verse_counts.py` (`canonical_book_shape(book) -> {chapter: verse_count}`, `canonical_count`, `canonical_chapters`), `scripts/core/config.py` (`get_book`, `load_books`).

**Baseline state (verified 2026-05-21, HEAD after this session's commit):**
- `inject --all-books` → `52553 injected/already · 7804 verse-end fallback · 420 anchor-not-found · 0 no-notes-section`.
- `ebible verify` → `errors=0 / 15766 paired`; `pytest tests/test_build_smoke.py` → 16 passed; `ruff check scripts/inject.py` → clean.
- The 420 residual breaks down: **241 verse-unparseable (Strategy B)** + **110 chapter-absent-B** (aes 73 + small pro/isa/1jn/rev) + **69 verse-absent (Strategy A)** versification.

**Hard rules for the executor (from the project + this session's scars):**
- TDD: failing test first, watch it fail, minimal impl, watch it pass, commit. One behavior per test.
- Run tests ONE FILE AT A TIME with the full interpreter path + `PYTHONUTF8=1` (memory: `local_test_memory_pressure`, `python-interpreter-path`, `feedback_pythonutf8`).
- **Cross-file duplicate ids fail `ebible verify`.** Never insert an `id="ch-{bxx}-c{ch}"` that already exists in another split file (this session's gen-27 scar). Synthesized sections use `id="notes-{bxx}-c{ch}"`.
- After every inject change: re-run `inject --all-books`, then `ebible verify` (errors MUST stay 0, paired N/N), then `pytest tests/test_build_smoke.py` (valid EPUB). A drop in placement vs. the baseline is a regression — stop and fix.
- `epub_working/` is a regenerable inject target: to get a clean deterministic run, `git checkout -- epub_working/` then re-inject (scoped to epub_working only; never touch code with it).
- Commit locally only (`save.cmd`/`save.ps1` via the **PowerShell** tool, never Bash — memory `feedback_savecmd_bash_hazard`); no remote, no zip.

---

## File Structure

- `scripts/inject.py` (MODIFY) — add the Strategy-B verse-index resolver + a `--report` mode; wire the resolver into `inject_book`. Already complex (C901 ignored per `pyproject.toml`); keep helpers small and pure.
- `scripts/audit_base_html.py` (CREATE) — standalone structural-audit/report tool: per book, classify regular vs irregular layout and list which chapters' verses are unreachable. Re-runnable detector (stays in `scripts/`, mirrors `run_*_at_scale.py` retention).
- `tests/test_build_smoke.py` (MODIFY) — extend with `TestVerseIndexB` (resolver) + `TestInjectIrregularLayout` (integration on a real irregular book) classes. This file is the established inject/build test home.
- `content/translations/kjv/aes.py` (READ only) — source for the absent Additions-to-Esther chapters in Phase 4.
- `dev/IN_FLIGHT.md`, `dev/SESSION_STATE.md` (MODIFY at phase close) — state-of-record.

---

## Phase 1 — Structural audit tool (know the exact scope before fixing)

### Task 1: Standalone base-HTML structural audit

**Files:**
- Create: `scripts/audit_base_html.py`
- Test: `tests/test_build_smoke.py` (class `TestAuditBaseHtml`)

- [ ] **Step 1: Write the failing test**

```python
class TestAuditBaseHtml:
    """audit_base_html.classify_book reports, per book, whether every
    chapter's verse text is reachable from its chapter anchor (regular) or
    whether scripture and the chapter anchor are split across files
    (irregular). It must flag 1ch as irregular and gen as regular."""

    def test_gen_is_regular(self):
        from scripts.audit_base_html import classify_book
        report = classify_book("gen")
        assert report["irregular_chapters"] == [], report

    def test_1ch_flags_chapter_3_irregular(self):
        from scripts.audit_base_html import classify_book
        report = classify_book("1ch")
        # ch3's verse text is in a different split file than its ch anchor
        assert 3 in report["irregular_chapters"], report
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& $py -m pytest tests/test_build_smoke.py::TestAuditBaseHtml -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.audit_base_html'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/audit_base_html.py
"""Structural audit of the recovered base HTML: which chapters' verse text
is reachable from their chapter anchor (regular) vs. split across files
(irregular). Read-only; re-runnable detector."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402

EPUB_DIR = REPO_ROOT / "epub_working"
_VN = re.compile(r'<span class="vn">(\d+)</span>')


def _file_texts(book: dict) -> dict[str, str]:
    out = {}
    for fname in book.get("files", []):
        p = EPUB_DIR / fname
        if p.is_file():
            out[fname] = p.read_text(encoding="utf-8")
    return out


def classify_book(code: str) -> dict:
    """For a Strategy-B book, a chapter is 'irregular' when its ch anchor's
    file holds no verse spans between this ch anchor and the next ch anchor,
    yet the book does contain verse spans for that chapter elsewhere."""
    book = config.get_book(code)
    bxx = book.get("bxx")
    strategy = book.get("strategy", "A")
    texts = _file_texts(book)
    irregular: list[int] = []
    if strategy != "B" or not bxx:
        return {"code": code, "strategy": strategy, "irregular_chapters": irregular}
    n = book.get("ch_count", 0)
    for ch in range(1, n + 1):
        anchor = f'id="ch-{bxx}-c{ch}"'
        host = next((t for t in texts.values() if anchor in t), None)
        if host is None:
            continue  # chapter-absent; handled elsewhere
        start = host.find(anchor)
        nxt = host.find(f'id="ch-{bxx}-c{ch + 1}"', start + 1)
        region = host[start:nxt] if nxt != -1 else host[start:]
        if not _VN.search(region):
            irregular.append(ch)
    return {"code": code, "strategy": strategy, "irregular_chapters": irregular}


def run_all() -> dict:
    books, flagged = [], {}
    for b in config.load_books():
        if not (REPO_ROOT / "content" / "notes" / f"{b['code']}.py").is_file():
            continue
        rep = classify_book(b["code"])
        books.append(rep)
        if rep["irregular_chapters"]:
            flagged[rep["code"]] = rep["irregular_chapters"]
    return {"flagged": flagged, "checked": len(books)}


def main() -> int:
    result = run_all()
    for code, chs in sorted(result["flagged"].items()):
        print(f"  {code:5} irregular chapters: {chs}")
    print(f"\nchecked={result['checked']} irregular_books={len(result['flagged'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `& $py -m pytest tests/test_build_smoke.py::TestAuditBaseHtml -q`
Expected: PASS (2 passed)

- [ ] **Step 5: Run the audit over the whole corpus and capture the catalog**

Run: `& $py scripts/audit_base_html.py`
Expected: a printed list of irregular books+chapters. **Record the full output in `dev/IN_FLIGHT.md`** — this catalog is the authoritative scope for Phase 2/3. Confirm the irregular set matches the unparseable books (jer/isa/1ch/psa/mq1-3/jub/sir/rom…). **Decision gate:** if any irregular chapter is NOT of the "verses-in-another-file, spans present" class (e.g. verses genuinely lack `<span class="vn">`), note it — those need a different remedy (Phase 5), not the Phase-2 resolver.

- [ ] **Step 6: Commit**

```
save.cmd "audit.base-html-layout: classify regular vs split-file irregular chapters (scopes the 241-note inject tail)"
```

---

## Phase 2 — Strategy-B verse-index resolver

The resolver builds, for one book, an index mapping `(chapter, verse) -> (fname, span_start)` by walking `<span class="vn">N</span>` spans across the book's files **in document order** (book-metadata file order), starting a new chapter each time the verse number resets to 1, and validating the chapter count against `canonical_chapters(code)`. This locates verses regardless of where the chapter anchor sits.

### Task 2: `build_verse_index_b` walks spans across files

**Files:**
- Modify: `scripts/inject.py` (add `build_verse_index_b` after `find_verse_region_b`)
- Test: `tests/test_build_smoke.py` (class `TestVerseIndexB`)

- [ ] **Step 1: Write the failing test** (real 1ch-3 fixture; verses in a "second" file with no ch3 anchor)

```python
class TestVerseIndexB:
    """build_verse_index_b maps (chapter, verse) -> (fname, offset) by
    walking vn-spans across files in order, resetting chapter on v1.
    The 1ch-3 case: ch1 ends in file A, ch3's verses open file B with NO
    ch3 anchor — the index must still place them under chapter 3."""

    FILE_A = (
        '<a id="ch-b12-c1" class="ch-anchor"></a><p class="verse-p">'
        '<span class="vn">1</span> Adam <span class="vn">2</span> Seth</p>'
        '<a id="ch-b12-c2" class="ch-anchor"></a><p class="verse-p">'
        '<span class="vn">1</span> Sons of Israel</p>'
    )
    # file B opens with ch3's verses, no ch3 anchor; ch4 anchor follows
    FILE_B = (
        '<body class="bible-body">\n<p class="verse-p">'
        '<span class="vn">1</span> sons of David <span class="vn">2</span> Absalom</p>'
        '<a id="ch-b12-c4" class="ch-anchor"></a><p class="verse-p">'
        '<span class="vn">1</span> Solomon</p></body>'
    )

    def test_index_assigns_orphan_verses_to_chapter_3(self, monkeypatch):
        from scripts import inject
        file_texts = {"a.html": self.FILE_A, "b.html": self.FILE_B}
        # canonical shape: ch1=2v, ch2=1v, ch3=2v, ch4=1v
        monkeypatch.setattr(inject, "canonical_book_shape_for", lambda code: {1: 2, 2: 1, 3: 2, 4: 1})
        idx = inject.build_verse_index_b("1ch", "b12", ["a.html", "b.html"], file_texts)
        assert (3, 1) in idx and idx[(3, 1)][0] == "b.html"
        assert (3, 2) in idx and idx[(3, 2)][0] == "b.html"
        assert (4, 1) in idx and idx[(4, 1)][0] == "b.html"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& $py -m pytest tests/test_build_smoke.py::TestVerseIndexB -q`
Expected: FAIL — `AttributeError: module 'scripts.inject' has no attribute 'build_verse_index_b'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/inject.py — near the top, alongside the other core imports:
from scripts.core.canonical_verse_counts import canonical_book_shape  # noqa: E402


def canonical_book_shape_for(code: str) -> dict[int, int]:
    """Indirection seam so tests can inject a tiny shape. Returns
    {chapter: verse_count} for the book, or {} if not canonically known."""
    try:
        return canonical_book_shape(code)
    except Exception:
        return {}


_VN_SPAN = re.compile(r'<span class="vn">(\d+)</span>')


def build_verse_index_b(code: str, bxx: str, files: list[str], file_texts: dict[str, str]) -> dict:
    """Map (chapter, verse) -> (fname, span_start_offset) by walking vn-spans
    across the book's files in document order. A new chapter starts whenever
    the verse number resets to 1 after a higher number (or on the very first
    span). The canonical shape, when known, caps run-on so a missing v1
    (verse-absent) doesn't shift every later chapter."""
    shape = canonical_book_shape_for(code)
    index: dict[tuple[int, int], tuple[str, int]] = {}
    chapter = 0
    prev_v = None
    for fname in files:
        text = file_texts.get(fname)
        if not text:
            continue
        for m in _VN_SPAN.finditer(text):
            v = int(m.group(1))
            if prev_v is None or v == 1 or v <= prev_v:
                chapter += 1
            elif shape and chapter in shape and prev_v is not None and prev_v >= shape[chapter] and v > prev_v:
                # current chapter already complete per canonical shape and the
                # number kept climbing without a reset -> next chapter started
                # with a non-1 first verse (rare); advance.
                chapter += 1
            index[(chapter, v)] = (fname, m.start())
            prev_v = v
    return index
```

- [ ] **Step 4: Run test to verify it passes**

Run: `& $py -m pytest tests/test_build_smoke.py::TestVerseIndexB -q`
Expected: PASS

- [ ] **Step 5: Add a guard test for verse-1-only chapters and commit**

```python
    def test_single_file_regular_book_indexes_all(self, monkeypatch):
        from scripts import inject
        text = ('<a id="ch-b12-c1" class="ch-anchor"></a><p class="verse-p">'
                '<span class="vn">1</span> a <span class="vn">2</span> b</p>'
                '<a id="ch-b12-c2" class="ch-anchor"></a><p class="verse-p">'
                '<span class="vn">1</span> c</p>')
        monkeypatch.setattr(inject, "canonical_book_shape_for", lambda code: {1: 2, 2: 1})
        idx = inject.build_verse_index_b("x", "b12", ["only.html"], {"only.html": text})
        assert idx[(1, 1)][1] < idx[(1, 2)][1] < idx[(2, 1)][1]
```

Run: `& $py -m pytest tests/test_build_smoke.py::TestVerseIndexB -q` → PASS, then
```
save.cmd "inject.verse-index-b: locate Strategy-B verses across split files by walking vn-spans + canonical shape"
```

### Task 3: `find_verse_region_b_indexed` returns the verse's region from the index

**Files:**
- Modify: `scripts/inject.py`
- Test: `tests/test_build_smoke.py` (class `TestVerseIndexB`)

- [ ] **Step 1: Write the failing test**

```python
    def test_region_spans_from_this_vn_to_next(self, monkeypatch):
        from scripts import inject
        text = ('<p class="verse-p"><span class="vn">1</span> sons of David '
                '<span class="vn">2</span> Absalom</p>')
        idx = {(3, 1): ("b.html", text.find('<span class="vn">1</span>')),
               (3, 2): ("b.html", text.find('<span class="vn">2</span>'))}
        region = inject.find_verse_region_b_indexed(text, idx, 3, 1)
        assert region is not None
        s, e = region
        assert "sons of David" in text[s:e]
        assert "Absalom" not in text[s:e]
```

- [ ] **Step 2: Run to verify fail**

Run: `& $py -m pytest tests/test_build_smoke.py::TestVerseIndexB::test_region_spans_from_this_vn_to_next -q`
Expected: FAIL — no attribute `find_verse_region_b_indexed`

- [ ] **Step 3: Implement**

```python
# scripts/inject.py
def find_verse_region_b_indexed(text: str, index: dict, ch: int, v: int) -> tuple[int, int] | None:
    """Region for (ch, v) using a prebuilt verse index: from just after this
    verse's vn-span to the start of the next indexed span in the same file,
    or end of that file's text."""
    here = index.get((ch, v))
    if here is None:
        return None
    fname, start = here
    m = _VN_SPAN.match(text, start)
    content_start = m.end() if m else start
    nxts = [off for (c, vv), (fn, off) in index.items() if fn == fname and off > start]
    end = min(nxts) if nxts else len(text)
    return (content_start, end)
```

- [ ] **Step 4: Run to verify pass**

Run: `& $py -m pytest tests/test_build_smoke.py::TestVerseIndexB::test_region_spans_from_this_vn_to_next -q`
Expected: PASS

- [ ] **Step 5: Commit**

```
save.cmd "inject.verse-region-indexed: derive a Strategy-B verse region from the cross-file verse index"
```

---

## Phase 3 — Wire the resolver into inject and re-inject

### Task 4: `inject_book` uses the index for Strategy-B when the anchor-region has no verses

**Files:**
- Modify: `scripts/inject.py` (`inject_book`, the Strategy-B branch around the chapter-region/verse-region lookup)
- Test: `tests/test_build_smoke.py` (class `TestInjectIrregularLayout`)

- [ ] **Step 1: Write the failing integration test** (build a tiny 2-file book on disk, note in the orphaned chapter, assert it injects)

```python
class TestInjectIrregularLayout:
    """End-to-end: a Strategy-B book whose ch2 verses open a second split
    file with no ch2 anchor must still inject ch2's note (marker into the
    verse's file, aside into a section created there)."""

    def test_orphan_chapter_note_injects(self, tmp_path, monkeypatch):
        from scripts import inject
        a = ('<html><body><a id="ch-b99-c1" class="ch-anchor"></a>'
             '<p class="verse-p"><span class="vn">1</span> alpha</p></body></html>')
        b = ('<html><body class="bible-body"><p class="verse-p">'
             '<span class="vn">1</span> the deep word here</p>'
             '<a id="ch-b99-c2" class="ch-anchor"></a>'  # this is really ch3's anchor in the wild; kept simple
             '</body></html>')
        epub = tmp_path / "epub_working"; epub.mkdir()
        (epub / "a.html").write_text(a, encoding="utf-8")
        (epub / "b.html").write_text(b, encoding="utf-8")
        monkeypatch.setattr(inject, "EPUB_DIR", epub)
        monkeypatch.setattr(inject, "canonical_book_shape_for", lambda code: {1: 1, 2: 1})
        book = {"code": "zz", "bxx": "b99", "strategy": "B", "ch_count": 2,
                "files": ["a.html", "b.html"], "id_prefix": "b99"}
        # one note on ch2 v1 anchored to a word that IS in the verse
        monkeypatch.setattr(inject, "load_notes",
                            lambda p: [(2, 1, "", "word", "lang-hebrew", "T", "L", "B")])
        stats = inject.inject_book(book, dry_run=True)
        assert stats["injected"] == 1, stats
        assert len(stats["missing_anchor"]) == 0, stats
```

- [ ] **Step 2: Run to verify fail**

Run: `& $py -m pytest tests/test_build_smoke.py::TestInjectIrregularLayout -q`
Expected: FAIL — the note lands in `missing_anchor` ("chapter heading not in any file" or "verse region not parseable") because ch2's verses are in `b.html` with no usable ch2 region.

- [ ] **Step 3: Implement — fall back to the index in the Strategy-B branch**

In `inject_book`, build the index once per book (before the note loop):
```python
    verse_index_b = build_verse_index_b(code, bxx, files, file_texts) if strategy == "B" else {}
```
Then in the Strategy-B verse-location block, after the existing chapter-region attempt, when `target_text`/`verse_region` resolution fails, consult the index:
```python
        else:  # strategy == "B"
            # 1) try the conventional anchor-region path (regular books)
            region = None
            for fname, text in file_texts.items():
                if f'id="ch-{bxx}-c{ch}"' in text:
                    ch_region = find_chapter_region_b(text, bxx, ch, ch_count)
                    if ch_region:
                        region = find_verse_region_b(text, ch_region[0], ch_region[1], v)
                        if region:
                            target_fname, target_text, verse_region = fname, text, region
                            break
            # 2) irregular split-file layout: locate via the verse index
            if region is None:
                hit = verse_index_b.get((ch, v))
                if hit is None:
                    stats["missing_anchor"].append(f"{ch}:{v}{suffix} (verse not in index)")
                    continue
                target_fname = hit[0]
                target_text = file_texts[target_fname]
                verse_region = find_verse_region_b_indexed(target_text, verse_index_b, ch, v)
            if verse_region is None:
                stats["missing_anchor"].append(f"{ch}:{v}{suffix} (verse region not parseable)")
                continue
```
> NOTE: this REPLACES the current Strategy-B block (which assumed one file holds both anchor and verses). Preserve the existing Strategy-A branch untouched. The aside still flows through `ensure_notes_section_a(target_text, ch, bxx, v_start)` (already shipped), which creates an `id="notes-{bxx}-c{ch}"` section in the verse's file when none exists — so marker and aside stay in the same file (reader-safe footnotes, no cross-file hrefs, no duplicate chapter anchors).

- [ ] **Step 4: Run to verify pass**

Run: `& $py -m pytest tests/test_build_smoke.py::TestInjectIrregularLayout -q`
Expected: PASS (1 passed)

- [ ] **Step 5: Run the full smoke file + ruff**

Run: `& $py -m pytest tests/test_build_smoke.py -q` → all pass
Run: `& $py -m ruff check scripts/inject.py scripts/audit_base_html.py tests/test_build_smoke.py` → `All checks passed!`

- [ ] **Step 6: Clean re-inject + verify the tail collapsed + no regression**

```powershell
git checkout -- epub_working/
& $py scripts\inject.py --all-books | Select-Object -Last 6
& $py scripts\ebible.py verify | Select-Object -Last 2
& $py -m pytest tests\test_build_smoke.py -q | Select-Object -Last 3
```
Expected: `injected/already` ≈ 52,794 (52,553 + ~241); `verse region not parseable` near 0; `ebible verify` **errors=0**, paired N/N (HIGHER than 15766); build smoke valid EPUB. **Regression gate:** placement MUST be ≥ 52,553 and verify errors MUST be 0. If a book's index miscounts chapters (canonical shape vs. WEB versification), it will show as new `(verse not in index)` misses — inspect with `& $py scripts\audit_base_html.py` and the Task-1 catalog; fix the shape-cap logic in `build_verse_index_b`, do NOT loosen the verify gate.

- [ ] **Step 7: Commit**

```
save.cmd "inject.irregular-layout: resolve Strategy-B verses via cross-file index when scripture/notes are split (lands the ~241 unparseable tail)"
```

---

## Phase 4 — Render the genuinely-absent deuterocanon chapters (aes, 110)

> **⛔ PREMISE REFUTED 2026-05-21 — DO NOT EXECUTE AS WRITTEN.** The base did NOT
> "simply never render aes's chapters." It renders aes (`b25`, `index_split_028.html`)
> as **chapters 1–10** in the World English Bible narrative ordering of the Greek
> Additions (`b25 c1` = Dream of Mordecai; `b25 c10` = canonical Esther 10's "the king
> levied a tax"). The 82 aes **notes** are keyed to the **KJV/Vulgate appendix scheme**
> (chapters 10, 11, 13, 14, 15, 16). So the 73 "chapter heading not in any file" misses
> are notes on ch11–16, which the base renders under DIFFERENT numbers (1–10). Rendering
> KJV ch11–16 into the base would graft a duplicate copy of the Additions. The correct
> fix is an **editorial WEB↔KJV verse concordance** that re-keys the notes 10–16 → 1–10
> (do NOT guess) — deferred to editorial review. See
> `dev/AUDIT_2026-05-21-inject-tail-residual.md` §A. Phase 3's boundary-aware spill
> resolver already captured the mechanically-placeable tail (+143 → 99.48%).

The 110 chapter-absent-B is dominated by **aes = Additions to Esther (73)**; the rest are small (pro/isa/1jn/rev) and are versification artifacts handled in Phase 5. aes's English text exists at `content/translations/kjv/aes.py`; the base HTML simply never rendered those chapters.

### Task 5: Confirm aes is renderable, then render its chapters into the base HTML

**Files:**
- Read: `content/translations/kjv/aes.py`, an existing regular Strategy-B book's HTML (e.g. the file holding `tob`/`jdt`) as the structural template
- Modify: the `epub_working/index_split_*.html` file in aes's canonical position (per `content/books.yaml` order); `content/books.yaml`/`editions.yaml` only if aes's file/anchor metadata is missing
- Test: `tests/test_build_smoke.py` (class `TestAesRendered`)

- [ ] **Step 1: Investigate (read-only) and write the failing test**

First read `content/translations/kjv/aes.py` to confirm chapter/verse structure, and `config.get_book("aes")` for `bxx`/`files`/`ch_count`. Then:
```python
class TestAesRendered:
    def test_aes_chapters_present_and_injectable(self):
        from scripts import inject
        from scripts.core import config
        stats = inject.inject_book(config.get_book("aes"), dry_run=True)
        # after rendering, no aes note should be 'chapter heading not in any file'
        absent = [m for m in stats.get("missing_anchor", []) if "chapter heading not in any file" in m]
        assert absent == [], absent
```

- [ ] **Step 2: Run to verify fail**

Run: `& $py -m pytest tests/test_build_smoke.py::TestAesRendered -q`
Expected: FAIL — aes chapters missing → `chapter heading not in any file`.

- [ ] **Step 3: Render aes chapters into the base HTML**

Write a one-shot `scripts/_render_aes.py` (retain per §7.4 ship-script policy, then archive) that emits, for each aes chapter, the **regular** structure copied from a known-good Strategy-B book: `<a id="ch-{bxx}-c{ch}" class="ch-anchor"></a><p ... ch-heading>{ch}</p>` then a `<p class="verse-p">` with one `<span class="vn">{v}</span> {verse_text}` per verse from `kjv/aes.py`, then a per-chapter `<aside class="notes-section" epub:type="footnotes" hidden=""><hr class="notes-rule"/><h3 class="notes-heading">Notes</h3></aside>`. Insert at aes's canonical position in the correct split file (between the preceding and following book per `books.yaml`). Use `notes_io.atomic_write` + `ensure_backup`.

- [ ] **Step 4: Run to verify pass + verify integrity**

Run: `& $py -m pytest tests/test_build_smoke.py::TestAesRendered -q` → PASS
Run: `& $py scripts\inject.py --all-books | Select-Object -Last 6` → aes notes now inject
Run: `& $py scripts\ebible.py verify | Select-Object -Last 2` → errors=0, paired up by ~73

- [ ] **Step 5: Commit**

```
save.cmd "render.aes: add Additions-to-Esther chapters to the base HTML (regular layout) so its 73 notes inject"
```

---

## Phase 5 — Audit + document the true versification tail (69 + residue)

The 69 verse-absent (Strategy A) plus any small residue are notes whose verse number does not exist in the WEB rendering of that chapter (translation versification differs from the note's source). These are NOT addable content.

### Task 6: Versification audit report + documented decision

**Files:**
- Create: `scripts/audit_base_html.py` — add a `verse_absent_report()` function (reuse the module)
- Test: `tests/test_build_smoke.py` (class `TestAuditBaseHtml`)
- Modify: `dev/IN_FLIGHT.md` (record the final residual + the decision)

- [ ] **Step 1: Write the failing test**

```python
    def test_verse_absent_report_lists_book_chapter_verse(self):
        from scripts.audit_base_html import verse_absent_report
        rows = verse_absent_report()
        # every row is a concrete (book, ch, v) the WEB base does not contain
        assert all(len(r) == 3 for r in rows)
```

- [ ] **Step 2: Run to verify fail** → `AttributeError: verse_absent_report`

- [ ] **Step 3: Implement** — iterate notes per Strategy-A book, collect `(code, ch, v)` where `id="v-{code}-{ch}-{v}"` is absent from every file (mirror `inject_book`'s `missing_anchor` "(no verse anchor)" branch).

- [ ] **Step 4: Run to verify pass**, then run `& $py scripts/audit_base_html.py --verse-absent` and **paste the full list into `dev/IN_FLIGHT.md`** with the decision: for each, either (a) the note's verse maps cleanly to an existing WEB verse → fix the note's `(ch, v)` in `content/notes/{code}.py` (only with a clear 1:1 mapping; this is editorial, do NOT guess), or (b) genuine WEB-versification gap → leave unplaceable and DOCUMENT. Record final placement %.

- [ ] **Step 5: Commit**

```
save.cmd "audit.verse-absent: enumerate + adjudicate the residual versification mismatches; document final inject placement"
```

---

## Self-Review

**Spec coverage:**
- 241 verse-unparseable (Strategy B split layout) → Phases 1–3 (audit → verse index → wired into inject). ✅
- 110 chapter-absent-B (aes 73 dominant) → Phase 4 renders aes; small pro/isa/1jn/rev fall to Phase 5 as versification. ✅
- 69 verse-absent (Strategy A versification) → Phase 5 audit + documented decision. ✅
- "No base-HTML rewrite of working books" constraint → Phases 1–3 touch only `scripts/inject.py`; only Phase 4 adds new (absent) chapters, never edits existing book HTML. ✅
- Verified-state protection → every phase ends with `ebible verify` errors=0 + build smoke + a placement-regression gate. ✅

**Placeholder scan:** No "TBD"/"handle edge cases"/"similar to" — each task has concrete code, real fixtures, exact commands, expected output. The only deliberate investigate-then-implement step is Phase 4 Step 1 (read `kjv/aes.py` to template the render) and Phase 1 Step 5's decision gate (the audit's catalog drives whether Phase 2 needs extra classes); both are explicit, with the structural template specified.

**Type consistency:** `build_verse_index_b(code, bxx, files, file_texts) -> dict[(ch,v)->(fname,offset)]` is produced in Task 2 and consumed identically in Task 3 (`find_verse_region_b_indexed(text, index, ch, v)`) and Task 4 (`verse_index_b.get((ch, v))`). `canonical_book_shape_for(code)` is the single monkeypatch seam used by every Task-2/3 test. `ensure_notes_section_a(text, ch, bxx, after_pos)` is the already-shipped signature reused unchanged in Task 4's wiring.

**Risk notes for the executor:** the one genuinely tricky algorithm is chapter assignment in `build_verse_index_b` when WEB versification disagrees with the canonical shape (a missing v1, or a chapter with a non-1 first verse). The shape-cap branch handles the common case; if Phase 3 Step 6 surfaces new `(verse not in index)` misses, that is the place to refine — never relax the `ebible verify` gate to make a miss disappear.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-21-inject-tail-completion.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration. (Heavy-agent cap applies — memory `feedback_concurrent_agent_cap`: these are light/medium text tasks, so up to the medium cap; drain before re-dispatch.)

**2. Inline Execution** — execute tasks in this/next session via executing-plans, batch with checkpoints.

**Which approach?**
