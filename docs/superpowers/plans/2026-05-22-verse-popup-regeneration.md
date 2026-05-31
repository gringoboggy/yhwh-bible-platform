# Verse-Popup Regeneration Implementation Plan
**Status:** shipped — verse popups 24%→90.5%

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a re-runnable base-preprocessing generator that uniformly rebuilds the clickable verse-number wrappers + `vnote` popup asides across every KJV-covered book in `epub_working/`, closing the 24%→~100% verse-popup coverage gap.

**Architecture:** A new pure-function-heavy module + a thin CLI driver (`scripts/generate_verse_popups.py`). It edits `epub_working/index_split_*.html` in place. It harvests existing Hebrew/Greek from the current asides first, then for every verse (numbers sourced from KJV via the translations resolver) it wraps the inline `<span class="vn">N</span>` and emits/refreshes a `<aside class="vnote">` in that chapter's `verse-refs-section`, preferring resolver Hebrew/Greek and falling back to harvested content. The per-edition build is unchanged (it still prunes popups to each edition's configured languages).

**Tech Stack:** Python 3.14 (run via `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe` with `$env:PYTHONUTF8="1"`), pytest, ruff. Reuses `scripts.core.translations`, `scripts.core.config`, `scripts.core.notes_io`. Spec: `docs/superpowers/specs/2026-05-22-verse-popup-regeneration-design.md`.

**Conventions (read first):** `dev/CLAUDE_PROJECT_RULES.md` §7 (code), §8 (testing), §9 ("corpus-growth driver" pattern). Tests: full interpreter path + `$env:PYTHONUTF8="1"`, ONE file at a time (memory: local memory pressure). "continue" ≠ "save" — commit only on user "save"; the per-step `git commit` below is the engineer's local checkpoint, run via `save.ps1 -Message "..."` (PowerShell only; ASCII message).

---

## File Structure

- **Create** `scripts/generate_verse_popups.py` — the generator. Pure helpers (`build_vnote_aside`, `wrap_verse_number`, `harvest_existing_langs`, `verse_spans_in_chapter`, `ensure_verse_refs_section`) + a `generate_book(code, *, dry_run)` orchestrator + a `main()` CLI. One responsibility: produce the popup markup in the base HTML.
- **Create** `tests/test_verse_popups.py` — unit tests for the pure helpers + integration test on one book.
- **Modify** `epub_working/index_split_*.html` — the generator's output (data, not code).
- **Reference (no change):** `scripts/inject.py` (verse-region patterns), `scripts/core/translations.py`, `scripts/core/config.py`, `scripts/core/notes_io.py`, `scripts/build_edition.py` (consumes the markup unchanged).

The id contract (from the spec / observed base): verse anchor `id="v-{code}-{ch}-{vs}"`; aside `id="vnote-{code}-{ch}-{vs}"`; wrapper `<a … epub:type="noteref" title="{Title} {ch}:{vs}" href="#vnote-{code}-{ch}-{vs}">`.

---

## Task 1: Aside builder (pure function)

**Files:**
- Create: `scripts/generate_verse_popups.py`
- Test: `tests/test_verse_popups.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_verse_popups.py
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


class TestBuildVnoteAside:
    def test_english_only_floor(self):
        from scripts.generate_verse_popups import build_vnote_aside

        html = build_vnote_aside(
            code="1ki", ch=1, vs=1, title="The First Book of Kings",
            english="And king David was old.", hebrew=None, greek=None,
        )
        assert 'id="vnote-1ki-1-1"' in html
        assert 'class="vnote"' in html
        assert "<strong>The First Book of Kings 1:1.</strong>" in html
        assert '<p class="vnote-text">And king David was old.</p>' in html
        assert "vnote-hebrew" not in html
        assert "vnote-greek" not in html
        assert '<a href="#v-1ki-1-1" class="vnote-back" title="Back">↩</a>' in html

    def test_includes_hebrew_and_greek_when_present(self):
        from scripts.generate_verse_popups import build_vnote_aside

        html = build_vnote_aside(
            code="gen", ch=1, vs=3, title="Genesis",
            english="God said, Let there be light.",
            hebrew='<em>וַיֹּ֥אמֶר</em>', greek="Καὶ εἶπεν ὁ Θεὸς",
        )
        assert '<p class="vnote-source-label">Hebrew (Masoretic / WLC)</p>' in html
        assert '<p class="vnote-hebrew" dir="rtl" lang="he"><em>וַיֹּ֥אמֶר</em></p>' in html
        assert '<p class="vnote-source-label">Greek (Septuagint / Brenton)</p>' in html
        assert '<p class="vnote-greek" lang="grc">Καὶ εἶπεν ὁ Θεὸς</p>' in html

    def test_empty_english_uses_placeholder(self):
        from scripts.generate_verse_popups import build_vnote_aside

        html = build_vnote_aside(code="gen", ch=1, vs=1, title="Genesis",
                                 english=None, hebrew=None, greek=None)
        assert 'class="vnote-text vnote-empty"' in html
        assert "verse marker only" in html

    def test_english_is_html_escaped(self):
        from scripts.generate_verse_popups import build_vnote_aside

        html = build_vnote_aside(code="gen", ch=1, vs=1, title="Genesis",
                                 english='A < B & "q"', hebrew=None, greek=None)
        assert "A &lt; B &amp;" in html
        assert "<p class=\"vnote-text\">A &lt; B" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_verse_popups.py::TestBuildVnoteAside -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.generate_verse_popups'`.

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/generate_verse_popups.py
"""Regenerate verse-popup wrappers + vnote asides in the base HTML
(epub_working/). Base-preprocessing, re-runnable, idempotent. See
docs/superpowers/specs/2026-05-22-verse-popup-regeneration-design.md."""

from __future__ import annotations

import html as _html

_EMPTY_TEXT = '<p class="vnote-text vnote-empty"><em>[no text in this edition; verse marker only]</em></p>'


def build_vnote_aside(*, code: str, ch: int, vs: int, title: str,
                      english: str | None, hebrew: str | None,
                      greek: str | None) -> str:
    """Build one ``<aside class="vnote">`` matching the recovered-base contract.
    ``english`` is plain text (escaped here); ``hebrew``/``greek`` are trusted
    pre-formatted HTML fragments (from the resolver or harvested asides)."""
    vid = f"vnote-{code}-{ch}-{vs}"
    parts = [
        f'<aside class="vnote" id="{vid}" epub:type="footnote">'
        f"<p><strong>{_html.escape(title)} {ch}:{vs}.</strong></p>"
    ]
    if english:
        parts.append(f'<p class="vnote-text">{_html.escape(english)}</p>')
    else:
        parts.append(_EMPTY_TEXT)
    if hebrew:
        parts.append('\n  <p class="vnote-source-label">Hebrew (Masoretic / WLC)</p>')
        parts.append(f'\n  <p class="vnote-hebrew" dir="rtl" lang="he">{hebrew}</p>')
    if greek:
        parts.append('\n  <p class="vnote-source-label">Greek (Septuagint / Brenton)</p>')
        parts.append(f'\n  <p class="vnote-greek" lang="grc">{greek}</p>')
    parts.append(f'\n<p><a href="#v-{code}-{ch}-{vs}" class="vnote-back" title="Back">↩</a></p></aside>')
    return "".join(parts)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_verse_popups.py::TestBuildVnoteAside -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```
& .\save.ps1 -Message "feat.popup-gen: vnote aside builder (pure fn) + tests"
```

---

## Task 2: Verse-number wrapper (pure function, idempotent)

**Files:**
- Modify: `scripts/generate_verse_popups.py`
- Test: `tests/test_verse_popups.py`

- [ ] **Step 1: Write the failing test**

```python
class TestWrapVerseNumber:
    def test_wraps_bare_span(self):
        from scripts.generate_verse_popups import wrap_verse_number

        chunk = '<p class="verse-p"><span class="vn">1</span>And king David was old.'
        out, changed = wrap_verse_number(chunk, code="1ki", ch=1, vs=1,
                                         title="The First Book of Kings")
        assert changed is True
        assert ('<a id="v-1ki-1-1" epub:type="noteref" '
                'title="The First Book of Kings 1:1" href="#vnote-1ki-1-1">'
                '<span class="vn">1</span></a>') in out

    def test_idempotent_when_already_wrapped(self):
        from scripts.generate_verse_popups import wrap_verse_number

        already = ('<a id="v-1ki-1-1" epub:type="noteref" '
                   'title="The First Book of Kings 1:1" href="#vnote-1ki-1-1">'
                   '<span class="vn">1</span></a>And king David was old.')
        out, changed = wrap_verse_number(already, code="1ki", ch=1, vs=1,
                                         title="The First Book of Kings")
        assert changed is False
        assert out == already

    def test_only_first_matching_span_in_chunk(self):
        # The chunk is ONE verse region; the verse number appears once at its head.
        from scripts.generate_verse_popups import wrap_verse_number

        chunk = '<span class="vn">2</span>text with a stray "2" inside.'
        out, changed = wrap_verse_number(chunk, code="1ki", ch=1, vs=2,
                                         title="The First Book of Kings")
        assert out.count('id="v-1ki-1-2"') == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_verse_popups.py::TestWrapVerseNumber -v`
Expected: FAIL — `ImportError: cannot import name 'wrap_verse_number'`.

- [ ] **Step 3: Write minimal implementation**

```python
import re  # add to imports at top of scripts/generate_verse_popups.py


def wrap_verse_number(chunk: str, *, code: str, ch: int, vs: int,
                      title: str) -> tuple[str, bool]:
    """Wrap the first bare ``<span class="vn">{vs}</span>`` in ``chunk`` with the
    verse-popup noteref anchor. Idempotent: if a wrapper for this verse already
    exists, return unchanged. ``chunk`` MUST be scoped to one verse region so the
    head verse-number span is the right one. Returns ``(new_chunk, changed)``."""
    if f'id="v-{code}-{ch}-{vs}"' in chunk:
        return chunk, False
    needle = f'<span class="vn">{vs}</span>'
    idx = chunk.find(needle)
    if idx == -1:
        return chunk, False
    wrapper = (
        f'<a id="v-{code}-{ch}-{vs}" epub:type="noteref" '
        f'title="{_html.escape(title)} {ch}:{vs}" href="#vnote-{code}-{ch}-{vs}">'
        f"{needle}</a>"
    )
    return chunk[:idx] + wrapper + chunk[idx + len(needle):], True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_verse_popups.py::TestWrapVerseNumber -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```
& .\save.ps1 -Message "feat.popup-gen: idempotent verse-number wrapper + tests"
```

---

## Task 3: Harvest existing Hebrew/Greek from the base

**Files:**
- Modify: `scripts/generate_verse_popups.py`
- Test: `tests/test_verse_popups.py`

- [ ] **Step 1: Write the failing test**

```python
class TestHarvestExistingLangs:
    SAMPLE = (
        '<aside class="vnote" id="vnote-gen-1-3" epub:type="footnote">'
        '<p><strong>Genesis 1:3.</strong></p>'
        '<p class="vnote-text">God said...</p>'
        '<p class="vnote-source-label">Hebrew (Masoretic / WLC)</p>'
        '<p class="vnote-hebrew" dir="rtl" lang="he"><em>וַיֹּ֥אמֶר</em></p>'
        '<p class="vnote-source-label">Greek (Septuagint / Brenton)</p>'
        '<p class="vnote-greek" lang="grc">Καὶ εἶπεν</p>'
        '<p><a href="#v-gen-1-3" class="vnote-back" title="Back">↩</a></p></aside>'
    )

    def test_extracts_inner_html_keyed_by_vnote_id(self):
        from scripts.generate_verse_popups import harvest_existing_langs

        got = harvest_existing_langs(self.SAMPLE)
        assert got["vnote-gen-1-3"]["hebrew"] == "<em>וַיֹּ֥אמֶר</em>"
        assert got["vnote-gen-1-3"]["greek"] == "Καὶ εἶπεν"

    def test_absent_languages_are_none(self):
        from scripts.generate_verse_popups import harvest_existing_langs

        text = ('<aside class="vnote" id="vnote-1ki-1-1" epub:type="footnote">'
                '<p class="vnote-text">x</p></aside>')
        got = harvest_existing_langs(text)
        assert got["vnote-1ki-1-1"]["hebrew"] is None
        assert got["vnote-1ki-1-1"]["greek"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_verse_popups.py::TestHarvestExistingLangs -v`
Expected: FAIL — `ImportError: cannot import name 'harvest_existing_langs'`.

- [ ] **Step 3: Write minimal implementation**

```python
_ASIDE_RE = re.compile(r'<aside class="vnote" id="(vnote-[^"]+)".*?</aside>', re.DOTALL)
_HE_RE = re.compile(r'<p class="vnote-hebrew"[^>]*>(.*?)</p>', re.DOTALL)
_GR_RE = re.compile(r'<p class="vnote-greek"[^>]*>(.*?)</p>', re.DOTALL)


def harvest_existing_langs(text: str) -> dict[str, dict[str, str | None]]:
    """Parse every existing ``vnote`` aside in ``text`` → ``{vnote_id:
    {"hebrew": html|None, "greek": html|None}}``. Used so a uniform regen never
    drops original-language content the resolver can no longer reproduce."""
    out: dict[str, dict[str, str | None]] = {}
    for m in _ASIDE_RE.finditer(text):
        block = m.group(0)
        he = _HE_RE.search(block)
        gr = _GR_RE.search(block)
        out[m.group(1)] = {
            "hebrew": he.group(1) if he else None,
            "greek": gr.group(1) if gr else None,
        }
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_verse_popups.py::TestHarvestExistingLangs -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```
& .\save.ps1 -Message "feat.popup-gen: harvest existing he/gr from base asides + tests"
```

---

## Task 4: Locate chapter regions + verse spans in a file

**Context:** Unwrapped books have NO `v-…` anchor (the thing we add), so we cannot reuse `inject.find_verse_region` (Strategy A keys on that anchor). Instead, locate the chapter by its heading anchor `id="ch-{bxx}-c{ch}"` (present in all books per the recovered base), take the slice up to the next `id="ch-{bxx}-c"` or the `verse-refs-section`, and walk `<span class="vn">N</span>` occurrences within it.

**Files:**
- Modify: `scripts/generate_verse_popups.py`
- Test: `tests/test_verse_popups.py`

- [ ] **Step 1: Write the failing test**

```python
class TestVerseSpansInChapter:
    HTML = (
        '<p id="ch-b10-c1" class="ch-heading"><span class="bold-num">1</span></p>'
        '<p class="verse-p"><span class="vn">1</span>First verse.</p>'
        '<p class="verse-p"><span class="vn">2</span>Second verse.</p>'
        '<p id="ch-b10-c2" class="ch-heading"><span class="bold-num">2</span></p>'
        '<p class="verse-p"><span class="vn">1</span>Next chapter v1.</p>'
        '<section class="verse-refs-section" epub:type="footnotes" hidden=""></section>'
    )

    def test_finds_chapter_1_region_bounds(self):
        from scripts.generate_verse_popups import chapter_region

        start, end = chapter_region(self.HTML, bxx="b10", ch=1)
        slice_ = self.HTML[start:end]
        assert "First verse." in slice_ and "Second verse." in slice_
        assert "Next chapter v1." not in slice_

    def test_lists_verse_numbers_in_order(self):
        from scripts.generate_verse_popups import chapter_region, verse_numbers_in_region

        start, end = chapter_region(self.HTML, bxx="b10", ch=1)
        assert verse_numbers_in_region(self.HTML[start:end]) == [1, 2]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_verse_popups.py::TestVerseSpansInChapter -v`
Expected: FAIL — `ImportError: cannot import name 'chapter_region'`.

- [ ] **Step 3: Write minimal implementation**

```python
def chapter_region(text: str, *, bxx: str, ch: int) -> tuple[int, int] | None:
    """Byte range of chapter ``ch`` of book ``bxx`` in ``text`` — from its
    heading anchor to the next chapter heading (any chapter), the verse-refs
    section, or end of text. Returns None if the chapter heading is absent."""
    anchor = f'id="ch-{bxx}-c{ch}"'
    start = text.find(anchor)
    if start == -1:
        return None
    after = start + len(anchor)
    nxt = re.search(rf'id="ch-{re.escape(bxx)}-c\d+"', text[after:])
    sect = text.find('<section class="verse-refs-section"', after)
    end = len(text)
    if nxt:
        end = min(end, after + nxt.start())
    if sect != -1:
        end = min(end, sect)
    return start, end


_VN_RE = re.compile(r'<span class="vn">(\d+)</span>')


def verse_numbers_in_region(region: str) -> list[int]:
    """Verse numbers (in document order) inside one chapter region."""
    return [int(m.group(1)) for m in _VN_RE.finditer(region)]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_verse_popups.py::TestVerseSpansInChapter -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```
& .\save.ps1 -Message "feat.popup-gen: chapter-region + verse-number location (no v-anchor needed) + tests"
```

---

## Task 5: Ensure a verse-refs-section exists per file

**Context:** Wrapped books already have `<section class="verse-refs-section" epub:type="footnotes" hidden="">`; unwrapped books do not. The generator appends asides just before `</body>` if no section exists.

**Files:**
- Modify: `scripts/generate_verse_popups.py`
- Test: `tests/test_verse_popups.py`

- [ ] **Step 1: Write the failing test**

```python
class TestEnsureVerseRefsSection:
    def test_returns_existing_section_span(self):
        from scripts.generate_verse_popups import ensure_verse_refs_section

        text = 'x<section class="verse-refs-section" epub:type="footnotes" hidden=""></section></body>'
        new_text, insert_at = ensure_verse_refs_section(text)
        assert new_text == text  # already present, unchanged
        assert text[insert_at:insert_at + len("</section>")] == "</section>"

    def test_creates_section_before_body_close(self):
        from scripts.generate_verse_popups import ensure_verse_refs_section

        text = "<body><p>scripture</p></body></html>"
        new_text, insert_at = ensure_verse_refs_section(text)
        assert 'class="verse-refs-section"' in new_text
        assert new_text[insert_at:insert_at + len("</section>")] == "</section>"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_verse_popups.py::TestEnsureVerseRefsSection -v`
Expected: FAIL — `ImportError: cannot import name 'ensure_verse_refs_section'`.

- [ ] **Step 3: Write minimal implementation**

```python
_SECTION_OPEN = '<section class="verse-refs-section" epub:type="footnotes" hidden="">'


def ensure_verse_refs_section(text: str) -> tuple[str, int]:
    """Return ``(text, insertion_index)`` where ``insertion_index`` points at the
    section's closing ``</section>`` (asides are inserted just before it). Creates
    an empty section before ``</body>`` if none exists."""
    pos = text.find(_SECTION_OPEN)
    if pos != -1:
        close = text.find("</section>", pos)
        return text, close
    body = text.rfind("</body>")
    if body == -1:
        body = len(text)
    new_text = text[:body] + f"\n{_SECTION_OPEN}</section>\n" + text[body:]
    pos = new_text.find(_SECTION_OPEN)
    return new_text, new_text.find("</section>", pos)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_verse_popups.py::TestEnsureVerseRefsSection -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```
& .\save.ps1 -Message "feat.popup-gen: ensure verse-refs-section (create if absent) + tests"
```

---

## Task 6: Book orchestration — `generate_book`

**Context:** Wire the helpers over one book: read its files, harvest existing he/gr, for each chapter wrap each verse and (re)build its aside, then write changed files. Dry-run returns stats without writing. Hebrew/Greek precedence: resolver (`wlc` / `lxx-brenton-greek`) → harvested → None. English: `kjv` via the resolver. Book metadata from `config.books_by_code()`.

**Files:**
- Modify: `scripts/generate_verse_popups.py`
- Test: `tests/test_verse_popups.py`

- [ ] **Step 1: Write the failing test** (integration on a real, currently-unwrapped book)

```python
class TestGenerateBook:
    def test_1ki_gains_wrappers_and_asides_dry_run(self):
        # 1 Kings is currently 0% wrapped; dry-run should report it would wrap.
        from scripts.generate_verse_popups import generate_book

        stats = generate_book("1ki", dry_run=True)
        assert stats["verses_wrapped"] > 500, stats   # 1Ki has 816 verses
        assert stats["asides_built"] == stats["verses_wrapped"], stats
        assert stats["files_changed"], stats

    def test_genesis_is_idempotent_dry_run(self):
        # Genesis is already fully wrapped; a dry-run wrap pass should be a no-op
        # for the WRAPPER (asides may refresh, but no NEW wraps).
        from scripts.generate_verse_popups import generate_book

        stats = generate_book("gen", dry_run=True)
        assert stats["verses_wrapped"] == 0, stats  # already wrapped
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_verse_popups.py::TestGenerateBook -v`
Expected: FAIL — `ImportError: cannot import name 'generate_book'`.

- [ ] **Step 3: Write minimal implementation**

```python
from pathlib import Path

from scripts.core import config, notes_io
from scripts.core import translations as tx

REPO = Path(__file__).resolve().parents[1]
EPUB_DIR = REPO / "epub_working"


def generate_book(code: str, *, dry_run: bool) -> dict:
    book = config.books_by_code().get(code)
    if book is None:
        return {"error": f"unknown book {code!r}"}
    title = book["title"]
    bxx = book.get("bxx")
    ch_count = int(book.get("ch_count", 0) or 0)
    files = book.get("files", [])
    stats = {"code": code, "verses_wrapped": 0, "asides_built": 0,
             "files_changed": [], "skipped_reason": None}

    if not tx.has_book("kjv", code):
        stats["skipped_reason"] = "no KJV source (Ethiopic-only — deferred)"
        return stats
    if not bxx or not files:
        stats["skipped_reason"] = "missing bxx/files metadata"
        return stats

    for fname in files:
        fpath = EPUB_DIR / fname
        if not fpath.is_file():
            continue
        text = fpath.read_text(encoding="utf-8")
        harvested = harvest_existing_langs(text)
        original = text

        for ch in range(1, ch_count + 1):
            region = chapter_region(text, bxx=bxx, ch=ch)
            if region is None:
                continue
            r_start, r_end = region
            region_html = text[r_start:r_end]
            new_asides = []
            # Wrap verse numbers (right-to-left so earlier offsets stay valid).
            for vs in sorted(verse_numbers_in_region(region_html), reverse=True):
                # Scope to this verse: from its span to the next verse span.
                needle = f'<span class="vn">{vs}</span>'
                vpos = region_html.find(needle)
                if vpos == -1:
                    continue
                nxt = _VN_RE.search(region_html, vpos + len(needle))
                vchunk = region_html[vpos:(nxt.start() if nxt else len(region_html))]
                wrapped, changed = wrap_verse_number(
                    vchunk, code=code, ch=ch, vs=vs, title=title)
                if changed:
                    region_html = region_html[:vpos] + wrapped + region_html[vpos + len(vchunk):]
                    stats["verses_wrapped"] += 1
            text = text[:r_start] + region_html + text[r_end:]

            # Build/refresh asides for every verse the chapter actually has.
            for vs in verse_numbers_in_region(region_html):
                vid = f"vnote-{code}-{ch}-{vs}"
                eng = tx.get_verse("kjv", code, ch, vs)
                he = tx.get_verse("wlc", code, ch, vs) or harvested.get(vid, {}).get("hebrew")
                gr = (tx.get_verse("lxx-brenton-greek", code, ch, vs)
                      or harvested.get(vid, {}).get("greek"))
                new_asides.append(build_vnote_aside(
                    code=code, ch=ch, vs=vs, title=title,
                    english=eng, hebrew=he, greek=gr))
                stats["asides_built"] += 1

            if new_asides:
                # Remove any existing asides for this chapter, then insert fresh.
                text = _strip_chapter_asides(text, code, ch)
                text, insert_at = ensure_verse_refs_section(text)
                text = text[:insert_at] + "\n".join(new_asides) + "\n" + text[insert_at:]

        if text != original:
            stats["files_changed"].append(fname)
            if not dry_run:
                notes_io.ensure_backup(fpath)
                notes_io.atomic_write(fpath, text)
    return stats


def _strip_chapter_asides(text: str, code: str, ch: int) -> str:
    """Remove existing ``vnote`` asides for (code, ch) so a regen replaces rather
    than duplicates them. Idempotency relies on this + deterministic rebuild."""
    pat = re.compile(rf'<aside class="vnote" id="vnote-{re.escape(code)}-{ch}-\d+".*?</aside>\s*', re.DOTALL)
    return pat.sub("", text)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_verse_popups.py::TestGenerateBook -v`
Expected: PASS (2 passed). If `verses_wrapped` for `1ki` is 0, inspect `chapter_region` against the real `epub_working` 1 Kings file (the `ch-b10-c{ch}` anchor format) and adjust before proceeding.

- [ ] **Step 5: Commit**

```
& .\save.ps1 -Message "feat.popup-gen: generate_book orchestration (wrap + harvest-merge asides) + integration test"
```

---

## Task 7: CLI driver + idempotency test

**Files:**
- Modify: `scripts/generate_verse_popups.py`
- Test: `tests/test_verse_popups.py`

- [ ] **Step 1: Write the failing test**

```python
class TestIdempotency:
    def test_second_run_changes_nothing(self, tmp_path, monkeypatch):
        # Run generate_book twice on a temp copy of one book's files; the second
        # run must report no files changed.
        import shutil
        import scripts.generate_verse_popups as g

        work = tmp_path / "epub_working"
        work.mkdir()
        for f in (g.EPUB_DIR.glob("index_split_*.html")):
            shutil.copy(f, work / f.name)
        monkeypatch.setattr(g, "EPUB_DIR", work)

        first = g.generate_book("1ki", dry_run=False)
        assert first["files_changed"], first
        second = g.generate_book("1ki", dry_run=False)
        assert second["files_changed"] == [], second
```

- [ ] **Step 2: Run test to verify it fails (or errors)**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_verse_popups.py::TestIdempotency -v`
Expected: FAIL — second run still reports `files_changed` (the wrap pass or aside rebuild is non-deterministic). Fix `_strip_chapter_asides` + `build_vnote_aside` until the rebuilt bytes equal the prior bytes.

- [ ] **Step 3: Add the CLI `main()`**

```python
import argparse


def main() -> int:
    ap = argparse.ArgumentParser(description="Regenerate verse popups in epub_working/.")
    ap.add_argument("--books", nargs="*", help="book codes; default = all KJV-covered")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    codes = args.books or list(config.books_by_code())
    total_w = total_a = 0
    for code in codes:
        s = generate_book(code, dry_run=args.dry_run)
        if s.get("skipped_reason"):
            print(f"  skip {code}: {s['skipped_reason']}")
            continue
        total_w += s["verses_wrapped"]
        total_a += s["asides_built"]
        print(f"  {code}: wrapped {s['verses_wrapped']}, asides {s['asides_built']}, "
              f"files {len(s['files_changed'])}")
    print(f"TOTAL wrapped {total_w}, asides {total_a}{' (dry-run)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run idempotency test to verify it passes**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_verse_popups.py::TestIdempotency -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```
& .\save.ps1 -Message "feat.popup-gen: CLI driver + idempotency test"
```

---

## Task 8: Run the generator over all books + regression gates

**Files:**
- Modify: `epub_working/index_split_*.html` (generator output)
- Test: existing `tests/test_build_smoke.py`

- [ ] **Step 1: Dry-run all books, eyeball the totals**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts/generate_verse_popups.py --dry-run`
Expected: ~30,000+ verses wrapped across the 76 missing books; the 6 Ethiopic-only books print `skip … no KJV source`.

- [ ] **Step 2: Real run**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts/generate_verse_popups.py`
Expected: files changed across the previously-unwrapped books.

- [ ] **Step 3: Regression gate — verify + build smoke**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_build_smoke.py -v`
Then: `& "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m ebible verify` (or `scripts/ebible.py verify`)
Expected: build smoke 31/31 PASS; `ebible verify` **errors=0**. If verify reports unpaired refs, a wrapper/aside id mismatch exists — diff one chapter and fix the id format.

- [ ] **Step 4: Lint**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m ruff format scripts/generate_verse_popups.py tests/test_verse_popups.py; & "...python.exe" -m ruff check scripts/generate_verse_popups.py tests/test_verse_popups.py; & "...python.exe" scripts/lint_rules.py`
Expected: ruff clean; `lint_rules` 0 fail.

- [ ] **Step 5: Commit** (large data commit — base HTML)

```
& .\save.ps1 -Message "data.popup-gen: regenerate verse popups for all KJV-covered books (epub_working/); verify errors=0, build smoke green"
```

---

## Task 9: Coverage + versification regression pins

**Files:**
- Test: `tests/test_verse_popups.py`

- [ ] **Step 1: Write the coverage + alignment pins**

```python
class TestCoverageAfterGeneration:
    def test_1ki_now_has_popups_in_base(self):
        from scripts.generate_verse_popups import EPUB_DIR
        blob = "".join(p.read_text(encoding="utf-8")
                       for p in EPUB_DIR.glob("index_split_*.html"))
        assert 'href="#vnote-1ki-1-1"' in blob
        assert 'id="vnote-1ki-1-1"' in blob

    def test_genesis_1_1_text_aligned(self):
        # The uniform regen fixes the old Gen 1:1/1:2 offset: 1:1's aside must
        # carry Genesis 1:1's text (KJV), not be empty.
        from scripts.core import translations as tx
        from scripts.generate_verse_popups import EPUB_DIR
        kjv_11 = tx.get_verse("kjv", "gen", 1, 1)
        gen_file = (EPUB_DIR / "index_split_000.html").read_text(encoding="utf-8")
        import re as _re
        m = _re.search(r'<aside class="vnote" id="vnote-gen-1-1".*?</aside>', gen_file, _re.DOTALL)
        assert m and kjv_11 and kjv_11.split()[0] in m.group(0)
```

- [ ] **Step 2: Run to verify** (these run against the generated base from Task 8)

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_verse_popups.py::TestCoverageAfterGeneration -v`
Expected: PASS. If `test_genesis_1_1_text_aligned` fails, the offset wasn't corrected — re-examine how `verse_numbers_in_region` maps to KJV verse numbers for Genesis 1.

- [ ] **Step 3: Full file run** (one file, memory-aware)

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_verse_popups.py -v`
Expected: all PASS.

- [ ] **Step 4: Commit**

```
& .\save.ps1 -Message "test.popup-gen: coverage + versification-alignment regression pins"
```

---

## Self-review notes (for the implementer)

- **Spec coverage:** Task 1 (markup contract), Task 3+6 (harvest-and-merge preservation), Task 4 (no-v-anchor verse location), Task 6 (KJV floor + resolver he/gr), Task 7 (idempotency), Task 8 (build/verify gates), Task 9 (coverage + versification). The 6 Ethiopic-only books are skipped in `generate_book` (Task 6) — matches spec §3.
- **Known risk to watch:** the real `epub_working` chapter-heading format may differ slightly between Strategy-A and Strategy-B books (`id="ch-{bxx}-c{ch}"` vs a `<p class="ch-heading">` variant — see `inject.find_notes_section_for_chapter`). If `chapter_region` returns None for a book in the Task 8 dry-run, generalize its anchor match before the real run.
- **Versification:** the generator maps each `<span class="vn">N</span>` to KJV verse N directly. If a book's base verse numbering diverges from KJV (e.g., Psalms titles, merged verses), `get_verse("kjv", …, N)` may be None → `vnote-empty` placeholder (honest, no fabrication). Note any such book for the deferred original-language pass.
