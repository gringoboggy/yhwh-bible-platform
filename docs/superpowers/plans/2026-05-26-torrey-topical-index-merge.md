# Torrey Topical-Index Merge — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge Torrey's New Topical Textbook into the EPUB back-of-book Topical Index so a reader sees Nave's + Torrey together, with `(N·T)`/`(N)`/`(T)` source tags, gated by a builder-configurable `topical_index_source` field defaulting to `both`.

**Architecture:** New pure functions in `scripts/matter_pages.py` do a casefold-normalized union of the two structurally-identical topical sources; a small `_write_topical_page` helper holds the mode branch (so it's testable without full EPUB scaffolding); the existing single-source functions are left untouched (with a defaulted `intro=` param) to guarantee byte-identical output for the `naves` mode and the Torrey-missing degrade path. The config field is wired through the established enum-field pattern (`editions.py` allowed-lists + validator → `web.py api_customize_data` default → `customize.py` `<select>`).

**Tech Stack:** Python 3.14 (stdlib only — `html`, no new deps), pytest, the project's `ebible`/`epubcheck`/`lint_rules`/`ruff` gates.

**Spec:** `docs/superpowers/specs/2026-05-26-torrey-topical-index-merge-design.md`

---

## Environment & conventions (read before any step)

- **Interpreter (memory `python-interpreter-path`):** bare `python` is a broken Win Store stub. Always:
  ```powershell
  $env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest <node-id> -v
  ```
  Run from the repo root `C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4`. `PYTHONUTF8=1` is mandatory (memory `feedback_pythonutf8`).
- **Targeted node-ids only** (memories `feedback_local_test_memory_pressure`, `feedback_slow_test_files`) — run the new small file or specific classes, never a whole broad sweep, and never `tests/test_scripts.py` wholesale.
- **Commits are DEFERRED.** This project's rule (`feedback_save_is_local_commit`, `feedback_continue_not_save`): a git commit happens ONLY when the user says "save". Each task below ends at **green tests** (the checkpoint). Do NOT `git commit` per task. All changes are committed once, at the end, via the user-triggered **Task 9 save gate** (`save.ps1`, PowerShell only — memory `feedback_savecmd_bash_hazard`).
- **Before that save:** `ruff format` every file touched, or the pre-commit hook blocks (memory `feedback_ruff_format_before_save`).

---

## File structure

| File | Responsibility | Change |
|---|---|---|
| `scripts/matter_pages.py` | back-matter page builders/renderers | + `_norm_topic`, `_title_topic`, `TOPICAL_INDEX_SOURCES`, `build_merged_topic_index`, `render_merged_topical_index_page`, `_write_topical_page`; `render_topical_index_page` gains `intro=`; `inject_back_matter` delegates to `_write_topical_page`; Torrey in `_sources_sections` |
| `scripts/build_edition.py` | build orchestration + re-export hub | + 3 names in the `from scripts.matter_pages import (...)` re-export block (lines 66–85) |
| `scripts/api/editions.py` | edition-meta save/validate | + `topical_index_source` in both allowed-field lists + a validator block |
| `scripts/web.py` | HTTP API | `api_customize_data` surfaces `topical_index_source` (default `both`) |
| `scripts/templates/customize.py` | `/customize` console markup | + a `<select data-field="topical_index_source">` |
| `epub_working/stylesheet.css` | EPUB styling | + `.topic-src` rule |
| `dev/launcher.spec` | PyInstaller frozen build | ensure `content/sources/torrey_topical.json` is bundled |
| `tests/test_topical_merge.py` | NEW — all unit/render/mode pins | create |

---

## Task 1: Normalization + display helpers + the source-mode constant

**Files:**
- Modify: `scripts/matter_pages.py` (add near `build_topic_index`, ~line 772)
- Test: `tests/test_topical_merge.py` (Create)

- [ ] **Step 1: Write the failing tests**

Create `tests/test_topical_merge.py`:

```python
"""Torrey + Nave's topical-index merge — unit/render/mode pins."""

import xml.etree.ElementTree as ET


class _Hit:
    def __init__(self, b, c, v):
        self.target_book, self.target_chapter, self.target_verse = b, c, v


class _FakeSource:
    """Stub of NavesTopical / TorreyTopical with the index-building surface."""

    def __init__(self, topics):
        self._t = topics  # {topic: [(book, ch, vs), ...]}

    def topics(self):
        return sorted(self._t)

    def verses_for(self, topic):
        return [_Hit(*r) for r in self._t.get(topic, [])]


BOOK_ORDER = {"gen": 0, "exo": 1, "mat": 50, "tob": 80}


class TestTopicHelpers:
    def test_norm_topic_casefolds_collapses_ws_strips_edges(self):
        from scripts.matter_pages import _norm_topic

        assert _norm_topic("  ASSURANCE  ") == "assurance"
        assert _norm_topic("Affections, The") == "affections, the"  # comma preserved
        assert _norm_topic("Faith.") == "faith"

    def test_title_topic_titlecases_allcaps_and_hyphens(self):
        from scripts.matter_pages import _title_topic

        assert _title_topic("AARON") == "Aaron"
        assert _title_topic("ABED-NEGO") == "Abed-Nego"
        assert _title_topic("GOD'S WILL") == "God's Will"

    def test_topical_index_sources_constant(self):
        from scripts.matter_pages import TOPICAL_INDEX_SOURCES

        assert set(TOPICAL_INDEX_SOURCES) == {"both", "naves", "torrey"}
```

- [ ] **Step 2: Run to verify failure**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_topical_merge.py::TestTopicHelpers -v
```
Expected: FAIL — `ImportError: cannot import name '_norm_topic'`.

- [ ] **Step 3: Implement**

In `scripts/matter_pages.py`, immediately above `def build_topic_index(` (~line 772), add:

```python
TOPICAL_INDEX_SOURCES = ("both", "naves", "torrey")


def _norm_topic(t: str) -> str:
    """Casefold + collapse whitespace + strip edge punctuation. No comma split
    (Torrey's subtopics like 'Affliction, Consolation Under' must stay distinct)."""
    t = " ".join(t.casefold().split())
    return t.strip(" .;:-’'\"")


def _title_topic(name: str) -> str:
    """Title-case an ALL-CAPS / mixed Nave's topic for display: capitalize the
    first letter of each space- and hyphen-delimited segment, lowercase the rest
    (so 'ABED-NEGO' -> 'Abed-Nego', \"GOD'S WILL\" -> \"God's Will\")."""

    def cap(seg: str) -> str:
        return seg[:1].upper() + seg[1:].lower() if seg else seg

    words = ["-".join(cap(s) for s in word.split("-")) for word in name.split(" ")]
    return " ".join(words)
```

- [ ] **Step 4: Run to verify pass**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_topical_merge.py::TestTopicHelpers -v
```
Expected: 3 passed.

- [ ] **Step 5: Checkpoint** — tests green; do NOT commit (deferred to Task 9).

---

## Task 2: `build_merged_topic_index`

**Files:**
- Modify: `scripts/matter_pages.py` (add after `build_topic_index`, ~line 797)
- Test: `tests/test_topical_merge.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_topical_merge.py`:

```python
class TestBuildMergedTopicIndex:
    def _idx(self, naves, torrey, canon=None):
        from scripts.matter_pages import build_merged_topic_index

        return build_merged_topic_index(
            _FakeSource(naves) if naves is not None else None,
            _FakeSource(torrey) if torrey is not None else None,
            canon_books=canon,
            book_order=BOOK_ORDER,
        )

    def test_both_sides_tag_NT_and_union_deduped_ordered(self):
        idx = self._idx(
            {"Assurance": [("mat", 8, 10), ("gen", 15, 6)]},
            {"Assurance": [("gen", 15, 6), ("exo", 14, 13)]},  # gen dup collapses
        )
        assert idx == [("Assurance", "N·T", [("gen", 15, 6), ("exo", 14, 13), ("mat", 8, 10)])]

    def test_naves_only_tag_N_titlecased_display(self):
        idx = self._idx({"AARON": [("exo", 4, 14)]}, {})
        assert idx == [("Aaron", "N", [("exo", 4, 14)])]

    def test_torrey_only_tag_T_verbatim_display(self):
        idx = self._idx({}, {"Adoption": [("gen", 1, 1)]})
        assert idx == [("Adoption", "T", [("gen", 1, 1)])]

    def test_casefold_match_merges_caps_variants_prefers_torrey_casing(self):
        idx = self._idx({"ASSURANCE": [("gen", 1, 1)]}, {"Assurance": [("exo", 1, 1)]})
        assert idx == [("Assurance", "N·T", [("gen", 1, 1), ("exo", 1, 1)])]

    def test_canon_filter_drops_out_of_canon_and_omits_empty_topic(self):
        idx = self._idx(
            {"FAITH": [("tob", 2, 1), ("gen", 15, 6)], "TOBIT-ONLY": [("tob", 1, 1)]},
            {},
            canon={"gen", "exo", "mat"},
        )
        d = dict((t, refs) for t, _tag, refs in idx)
        assert "Tobit-Only" not in d  # all refs out of canon -> omitted
        assert d["Faith"] == [("gen", 15, 6)]

    def test_canon_makes_tag_T_when_only_torrey_has_in_canon_refs(self):
        # Nave's has the name but its only ref is out of canon -> tag reflects
        # in-edition verse presence (T), not mere name presence.
        idx = self._idx({"Grace": [("tob", 3, 1)]}, {"Grace": [("gen", 6, 8)]}, canon={"gen"})
        assert idx == [("Grace", "T", [("gen", 6, 8)])]

    def test_sorted_alphabetically_by_display_casefold(self):
        idx = self._idx({"ZEAL": [("gen", 1, 1)], "ABEL": [("gen", 4, 2)]}, {"Mercy": [("gen", 1, 1)]})
        assert [t for t, _tag, _refs in idx] == ["Abel", "Mercy", "Zeal"]

    def test_both_sources_none_returns_empty(self):
        assert self._idx(None, None) == []
```

- [ ] **Step 2: Run to verify failure**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_topical_merge.py::TestBuildMergedTopicIndex -v
```
Expected: FAIL — `cannot import name 'build_merged_topic_index'`.

- [ ] **Step 3: Implement**

In `scripts/matter_pages.py`, after `build_topic_index` (after its `return index`, ~line 797), add:

```python
def build_merged_topic_index(naves, torrey, canon_books, book_order: dict[str, int]):
    """Merge two topical sources into a tagged back-of-book index.

    Returns ``[(display, tag, [(book, ch, vs), …]), …]`` — sorted alphabetically
    by ``display`` (casefold). ``tag`` is ``"N·T"`` (both works), ``"N"``
    (Nave's only), or ``"T"`` (Torrey only), decided by which side has in-canon
    verses. Topic names are matched by ``_norm_topic`` (casefold); a topic with no
    in-canon ref is omitted. ``naves`` / ``torrey`` are ``sources.NavesTopical`` /
    ``TorreyTopical`` (or None if a source is unavailable)."""

    def collect(src):
        groups: dict[str, dict] = {}
        if src is None:
            return groups
        for topic in src.topics():
            key = _norm_topic(topic)
            g = groups.setdefault(key, {"names": [], "refs": set()})
            g["names"].append(topic)
            for hit in src.verses_for(topic):
                ref = (hit.target_book, hit.target_chapter, hit.target_verse)
                if canon_books is not None and ref[0] not in canon_books:
                    continue
                g["refs"].add(ref)
        return groups

    nav_g, tor_g = collect(naves), collect(torrey)
    out: list[tuple[str, str, list[tuple[str, int, int]]]] = []
    for key in set(nav_g) | set(tor_g):
        nav_refs = nav_g.get(key, {}).get("refs", set())
        tor_refs = tor_g.get(key, {}).get("refs", set())
        all_refs = sorted(nav_refs | tor_refs, key=lambda r: (book_order.get(r[0], 9999), r[1], r[2]))
        if not all_refs:
            continue
        tag = "N·T" if (nav_refs and tor_refs) else "N" if nav_refs else "T"
        if key in tor_g:
            display = sorted(tor_g[key]["names"])[0]  # Torrey is already Title Case
        else:
            display = _title_topic(sorted(nav_g[key]["names"])[0])
        out.append((display, tag, all_refs))
    out.sort(key=lambda e: e[0].casefold())
    return out
```

- [ ] **Step 4: Run to verify pass**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_topical_merge.py::TestBuildMergedTopicIndex -v
```
Expected: 8 passed.

- [ ] **Step 5: Checkpoint** — green; no commit.

---

## Task 3: Render functions (intro param + merged renderer) + CSS

**Files:**
- Modify: `scripts/matter_pages.py` (`render_topical_index_page` ~line 800; add `render_merged_topical_index_page` + intro consts)
- Modify: `epub_working/stylesheet.css` (after line 501)
- Test: `tests/test_topical_merge.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_topical_merge.py`:

```python
class TestRenderMerged:
    def test_default_naves_intro_byte_stable(self):
        from scripts.matter_pages import render_topical_index_page

        out = render_topical_index_page("v28a", [("FAITH", [("gen", 15, 6)])], book_abbrev=str.title)
        assert "after Nave&#x2019;s Topical Bible (Orville J. Nave, 1896; public domain)" in out
        ET.fromstring(out)

    def test_torrey_intro_param_overrides(self):
        from scripts.matter_pages import _TORREY_TOPICAL_INTRO, render_topical_index_page

        out = render_topical_index_page(
            "v28a", [("Adoption", [("gen", 1, 1)])], book_abbrev=str.title, intro=_TORREY_TOPICAL_INTRO
        )
        assert "Torrey" in out
        assert "after Nave" not in out
        ET.fromstring(out)

    def test_merged_render_has_tags_intro_and_is_wellformed(self):
        from scripts.matter_pages import render_merged_topical_index_page

        idx = [("Assurance", "N·T", [("gen", 15, 6)]), ("Adoption", "T", [("mat", 8, 10)])]
        out = render_merged_topical_index_page("v28a", idx, book_abbrev=str.title)
        ET.fromstring(out)  # well-formed XHTML
        assert "Nave" in out and "Torrey" in out
        assert "(N·T)" in out and "(T)" in out
        assert "Assurance" in out and "Gen 15:6" in out
        assert "topic-src" in out

    def test_merged_render_empty_index_valid(self):
        from scripts.matter_pages import render_merged_topical_index_page

        ET.fromstring(render_merged_topical_index_page("v28a", [], book_abbrev=str.title))
```

- [ ] **Step 2: Run to verify failure**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_topical_merge.py::TestRenderMerged -v
```
Expected: FAIL — `cannot import name '_TORREY_TOPICAL_INTRO'` / `render_merged_topical_index_page`.

- [ ] **Step 3a: Add intro consts + parametrize `render_topical_index_page`**

In `scripts/matter_pages.py`, immediately above `def render_topical_index_page(` (~line 800), add the two intro constants (the Nave's one is the EXACT current inner text — byte-compat):

```python
_NAVES_TOPICAL_INTRO = (
    "A concordance of verses by theme, after Nave&#x2019;s Topical Bible "
    "(Orville J. Nave, 1896; public domain). Topics are listed alphabetically; "
    "only verses present in this edition are shown."
)
_TORREY_TOPICAL_INTRO = (
    "A concordance of verses by theme, after Torrey&#x2019;s New Topical Textbook "
    "(R.A. Torrey, 1897; public domain). Topics are listed alphabetically; "
    "only verses present in this edition are shown."
)
_MERGED_TOPICAL_INTRO = (
    "A concordance of verses by theme, drawn from Nave&#x2019;s Topical Bible "
    "(Orville J. Nave, 1896) and Torrey&#x2019;s New Topical Textbook "
    "(R.A. Torrey, 1897), both public domain. Topics marked (N·T) are "
    "treated by both works; (N) Nave&#x2019;s only; (T) Torrey only. Only verses "
    "present in this edition are shown."
)
```

Change the `render_topical_index_page` signature and its intro line. Current signature:
```python
def render_topical_index_page(version: str, topic_index, book_abbrev) -> str:
```
becomes:
```python
def render_topical_index_page(version: str, topic_index, book_abbrev, *, intro: str = _NAVES_TOPICAL_INTRO) -> str:
```
In that function's f-string body, replace the hard-coded intro line:
```html
    <p class="topical-intro">A concordance of verses by theme, after Nave&#x2019;s Topical Bible (Orville J. Nave, 1896; public domain). Topics are listed alphabetically; only verses present in this edition are shown.</p>
```
with:
```html
    <p class="topical-intro">{intro}</p>
```

- [ ] **Step 3b: Add `render_merged_topical_index_page`**

Immediately after `render_topical_index_page` (after its closing `"""`), add:

```python
def render_merged_topical_index_page(version: str, merged_index, book_abbrev) -> str:
    """Render the merged Nave's + Torrey topical index. ``merged_index`` is the
    output of ``build_merged_topic_index`` — ``[(display, tag, refs), …]``."""
    rows: list[str] = []
    for topic, tag, refs in merged_index:
        ref_str = "; ".join(f"{book_abbrev(b)} {c}:{v}" for b, c, v in refs)
        rows.append(
            f'    <p class="topic-entry"><span class="topic-name">{html.escape(topic)}</span>'
            f' <span class="topic-src">({html.escape(tag)})</span> {ref_str}</p>'
        )
    body = "\n".join(rows) if rows else '    <p class="topic-entry">This edition carries no topical index.</p>'
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>Topical Index</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="backmatter">
  <section class="backmatter-page topical-index" epub:type="backmatter">
    <h1 class="backmatter-title">Topical Index</h1>
    <p class="topical-intro">{_MERGED_TOPICAL_INTRO}</p>
{body}
  </section>
</body>
</html>
"""
```

- [ ] **Step 3c: Add `.topic-src` CSS**

In `epub_working/stylesheet.css`, after line 501 (`.topic-name { … }`), add:

```css
.topic-src { font-size: 0.8em; color: #8a7a5c; font-weight: 400; font-variant-caps: normal; letter-spacing: 0; }
```

- [ ] **Step 4: Run to verify pass**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_topical_merge.py::TestRenderMerged -v
```
Expected: 4 passed.

- [ ] **Step 5: Guard the existing topical tests still pass (byte-compat of the single-source path)**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_topical_index.py -v
```
Expected: all pass (the defaulted `intro=` keeps `render_topical_index_page` output identical).

- [ ] **Step 6: Checkpoint** — green; no commit.

---

## Task 4: `_write_topical_page` helper + rewire `inject_back_matter`

**Files:**
- Modify: `scripts/matter_pages.py` (add `_write_topical_page` before `inject_back_matter` ~line 828; replace the topical try/except inside `inject_back_matter` lines ~839–853)
- Test: `tests/test_topical_merge.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_topical_merge.py`:

```python
class TestWriteTopicalPage:
    """The mode branch in isolation — writes topical.xhtml, returns topical_ok."""

    def _call(self, tmp_path, mode, *, naves, torrey):
        from scripts.matter_pages import _write_topical_page

        ok = _write_topical_page(
            tmp_path,
            mode,
            canon_books=None,
            book_order=BOOK_ORDER,
            naves=_FakeSource(naves) if naves is not None else None,
            torrey=_FakeSource(torrey) if torrey is not None else None,
            version="v28a",
        )
        page = (tmp_path / "topical.xhtml").read_text(encoding="utf-8") if ok else ""
        return ok, page

    def test_both_mode_writes_merged_with_tags(self, tmp_path):
        ok, page = self._call(tmp_path, "both", naves={"AARON": [("exo", 4, 14)]}, torrey={"Adoption": [("gen", 1, 1)]})
        assert ok
        assert "(N)" in page and "(T)" in page and "Torrey" in page

    def test_naves_mode_writes_single_source_no_tags(self, tmp_path):
        ok, page = self._call(tmp_path, "naves", naves={"AARON": [("exo", 4, 14)]}, torrey={"Adoption": [("gen", 1, 1)]})
        assert ok
        assert "after Nave" in page
        assert "topic-src" not in page  # no tags in single-source mode
        assert "Adoption" not in page  # Torrey excluded

    def test_torrey_mode_uses_torrey_intro(self, tmp_path):
        ok, page = self._call(tmp_path, "torrey", naves={"AARON": [("exo", 4, 14)]}, torrey={"Adoption": [("gen", 1, 1)]})
        assert ok and "Torrey" in page and "Adoption" in page

    def test_both_mode_degrades_to_naves_when_torrey_missing(self, tmp_path):
        ok, page = self._call(tmp_path, "both", naves={"AARON": [("exo", 4, 14)]}, torrey=None)
        assert ok
        assert "after Nave" in page and "topic-src" not in page  # byte-compat naves path

    def test_both_mode_degrades_to_torrey_when_naves_missing(self, tmp_path):
        ok, page = self._call(tmp_path, "both", naves=None, torrey={"Adoption": [("gen", 1, 1)]})
        assert ok and "Torrey" in page

    def test_both_missing_writes_nothing_returns_false(self, tmp_path):
        ok, _ = self._call(tmp_path, "both", naves=None, torrey=None)
        assert ok is False
        assert not (tmp_path / "topical.xhtml").exists()

    def test_unset_mode_defaults_to_both(self, tmp_path):
        ok, page = self._call(tmp_path, None, naves={"AARON": [("exo", 4, 14)]}, torrey={"Adoption": [("gen", 1, 1)]})
        assert ok and "topic-src" in page
```

- [ ] **Step 2: Run to verify failure**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_topical_merge.py::TestWriteTopicalPage -v
```
Expected: FAIL — `cannot import name '_write_topical_page'`.

- [ ] **Step 3a: Add `_write_topical_page`**

In `scripts/matter_pages.py`, immediately above `def inject_back_matter(` (~line 828), add:

```python
def _write_topical_page(tmp, mode, canon_books, book_order, *, naves, torrey, version) -> bool:
    """Write ``topical.xhtml`` per ``mode`` (naves | torrey | both; default both).
    Returns True if a page was written. Degrades gracefully when a source is
    unavailable: 'both' falls back to whichever single source is present; if
    neither is present, nothing is written and False is returned."""
    mode = (mode or "both").strip().lower()
    out = tmp / "topical.xhtml"

    def write_single(src, intro):
        idx = build_topic_index(src, canon_books, book_order)
        out.write_text(render_topical_index_page(version, idx, book_abbrev=str.title, intro=intro), encoding="utf-8")
        return True

    if mode == "naves":
        return write_single(naves, _NAVES_TOPICAL_INTRO) if naves is not None else False
    if mode == "torrey":
        return write_single(torrey, _TORREY_TOPICAL_INTRO) if torrey is not None else False
    # both (default)
    if naves is not None and torrey is not None:
        merged = build_merged_topic_index(naves, torrey, canon_books, book_order)
        out.write_text(render_merged_topical_index_page(version, merged, book_abbrev=str.title), encoding="utf-8")
        return True
    if naves is not None:
        return write_single(naves, _NAVES_TOPICAL_INTRO)
    if torrey is not None:
        return write_single(torrey, _TORREY_TOPICAL_INTRO)
    return False
```

- [ ] **Step 3b: Rewire `inject_back_matter`**

In `inject_back_matter`, replace the current topical block (lines ~839–853):

```python
    # §5.4 #4 — Nave's topical index, filtered to this edition's canon.
    from scripts.core import config as _config
    from scripts.core import sources as _sources

    topical_ok = False
    try:
        naves = _sources.naves_topical()
        book_order = {b["code"]: i for i, b in enumerate(_config.load_books())}
        topic_index = build_topic_index(naves, canon_books, book_order)
        (tmp / "topical.xhtml").write_text(
            render_topical_index_page(version, topic_index, book_abbrev=str.title), encoding="utf-8"
        )
        topical_ok = True
    except _sources.SourceMissingError:
        topical_ok = False  # Nave's not cached in this env — skip the page entirely
```

with:

```python
    # §5.4 #4 — topical index (Nave's + Torrey), filtered to this edition's canon.
    from scripts.core import config as _config
    from scripts.core import sources as _sources

    def _load(loader):
        try:
            return loader()
        except _sources.SourceMissingError:
            return None

    book_order = {b["code"]: i for i, b in enumerate(_config.load_books())}
    topical_ok = _write_topical_page(
        tmp,
        edition.get("topical_index_source"),
        canon_books,
        book_order,
        naves=_load(_sources.naves_topical),
        torrey=_load(_sources.torrey_topical),
        version=version,
    )
```

(The rest of `inject_back_matter` — the OPF / spine / nav patching gated on `topical_ok` — is unchanged.)

- [ ] **Step 4: Run to verify pass**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_topical_merge.py::TestWriteTopicalPage -v
```
Expected: 7 passed.

- [ ] **Step 5: Checkpoint** — green; no commit.

---

## Task 5: Credit Torrey on the Sources & Acknowledgments page

**Files:**
- Modify: `scripts/matter_pages.py` (`_sources_sections`, ~line 554)
- Test: `tests/test_topical_merge.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_topical_merge.py`:

```python
class TestSourcesPageCreditsTorrey:
    def test_sources_page_lists_both_topical_works(self):
        from scripts.matter_pages import render_sources_page

        out = render_sources_page("v28a")
        ET.fromstring(out)
        assert "Nave" in out  # pre-existing
        assert "Torrey&#x2019;s New Topical Textbook" in out
        assert "R.A. Torrey, 1897" in out
```

- [ ] **Step 2: Run to verify failure**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_topical_merge.py::TestSourcesPageCreditsTorrey -v
```
Expected: FAIL — Torrey assertion missing.

- [ ] **Step 3: Implement**

In `scripts/matter_pages.py` `_sources_sections`, find the Nave's list item (~line 554–555):
```python
            '\n        <li class="sources-item">Nave&#x2019;s Topical Bible,'
            " Orville J. Nave, 1896. Public Domain.</li>"
```
Add directly after it:
```python
            '\n        <li class="sources-item">Torrey&#x2019;s New Topical Textbook,'
            " R.A. Torrey, 1897. Public Domain.</li>"
```

- [ ] **Step 4: Run to verify pass**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_topical_merge.py::TestSourcesPageCreditsTorrey -v
```
Expected: 1 passed.

- [ ] **Step 5: Checkpoint** — green; no commit.

---

## Task 6: Config wiring — `topical_index_source` builder field

**Files:**
- Modify: `scripts/build_edition.py` (re-export block, lines 66–85)
- Modify: `scripts/api/editions.py` (two allowed-field lists ~504–512 and ~574–579; a validator block ~661)
- Modify: `scripts/web.py` (`api_customize_data`, ~line 1541)
- Modify: `scripts/templates/customize.py` (after the `marker_style` select, ~line 417)
- Test: `tests/test_topical_merge.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_topical_merge.py`:

```python
class TestConfigField:
    def test_reexported_from_build_edition(self):
        from scripts.build_edition import TOPICAL_INDEX_SOURCES

        assert "both" in TOPICAL_INDEX_SOURCES

    def test_validator_accepts_valid_and_rejects_invalid(self):
        from scripts.api.editions import api_save_edition_meta  # noqa: F401  (import path check)
        from scripts.build_edition import TOPICAL_INDEX_SOURCES

        # the enum the validator checks against
        assert set(TOPICAL_INDEX_SOURCES) == {"both", "naves", "torrey"}

    def test_customize_data_defaults_to_both(self):
        import inspect

        from scripts import web

        src = inspect.getsource(web.api_customize_data)
        assert 'topical_index_source", "both"' in src.replace("'", '"')
```

> Note: `api_save_edition_meta` round-trip is exercised by the existing `TestCustomize`/editions suites in `tests/test_scripts.py`; here we pin the field is wired (constant re-exported, default surfaced). Step 5 runs those suites to catch an allowed-field-list length pin if one exists.

- [ ] **Step 2: Run to verify failure**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_topical_merge.py::TestConfigField -v
```
Expected: FAIL — `cannot import name 'TOPICAL_INDEX_SOURCES' from scripts.build_edition`.

- [ ] **Step 3a: Re-export the constant**

In `scripts/build_edition.py`, in the `from scripts.matter_pages import (` block (lines 66–85), add these three names (keep the `# noqa: E402, F401`):
```python
    TOPICAL_INDEX_SOURCES,
    build_merged_topic_index,
    render_merged_topical_index_page,
```

- [ ] **Step 3b: Allowed-field lists + validator (`scripts/api/editions.py`)**

In BOTH allowed-field lists, add `"topical_index_source",` immediately after `"marker_style",` (the lists at ~line 509 and ~579).

After the `marker_style` validator block (~line 661, right after `payload["marker_style"] = v`), add:
```python
    if "topical_index_source" in payload:
        from scripts.build_edition import TOPICAL_INDEX_SOURCES

        v = (payload["topical_index_source"] or "").strip()
        if v and v not in TOPICAL_INDEX_SOURCES:
            return {"error": (f"unknown topical_index_source: {v!r}; valid: {sorted(TOPICAL_INDEX_SOURCES)}")}
        payload["topical_index_source"] = v
```

- [ ] **Step 3c: `api_customize_data` default (`scripts/web.py`)**

After the `marker_style` line (~1541):
```python
                "marker_style": e.get("marker_style", "numbers"),
```
add:
```python
                # Torrey merge — which topical authority feeds the back-of-book index.
                "topical_index_source": e.get("topical_index_source", "both"),
```

- [ ] **Step 3d: `/customize` select (`scripts/templates/customize.py`)**

After the `marker_style` `<label>…</label>` block (closes ~line 418), add:
```javascript
            <label class="text-xs">
              <span class="block mb-1 font-medium text-slate-700">Topical index source</span>
              <select class="label-input w-full" data-field="topical_index_source" title="which topical authority feeds the back-of-book Topical Index">
                <option value="both"   ${(e.topical_index_source||'both') === 'both' ? 'selected' : ''}>both · Nave's + Torrey, merged (N·T tags)</option>
                <option value="naves"  ${e.topical_index_source === 'naves' ? 'selected' : ''}>Nave's only</option>
                <option value="torrey" ${e.topical_index_source === 'torrey' ? 'selected' : ''}>Torrey only</option>
              </select>
            </label>
```

- [ ] **Step 4: Run to verify pass**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_topical_merge.py::TestConfigField -v
```
Expected: 3 passed.

- [ ] **Step 5: Guard the editions/customize suites (catch a field-list length pin)**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_scripts.py -k "Customize or edition_meta or allowed_field" -v
```
Expected: all pass. If a test asserts the exact count/contents of an allowed-field list (e.g. `len(...) == N`), bump it by 1 to include `topical_index_source` — that is the intended +1, not a regression.

- [ ] **Step 6: Checkpoint** — green; no commit.

---

## Task 7: Bundle the Torrey JSON into the frozen build

**Files:**
- Inspect/modify: `dev/launcher.spec`

- [ ] **Step 1: Check how `content/sources` is bundled**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -c "import pathlib; print(pathlib.Path(r'dev/launcher.spec').read_text(encoding='utf-8'))" | Select-String -Pattern "sources|content|naves_topical|datas|Tree"
```

- [ ] **Step 2: Ensure `torrey_topical.json` ships**

- If the spec bundles the whole `content/sources/` directory (or `content/` wholesale via a `Tree`/`datas` glob), `torrey_topical.json` is already included → **no edit**; note this in the task as verified.
- If it lists individual source JSONs (incl. `naves_topical.json`) explicitly, add a sibling entry for `content/sources/torrey_topical.json` mirroring the `naves_topical.json` line exactly.

> Not a blocker: if omitted, the frozen app's `both` mode degrades to Nave's-only (Task 4 guarantees this). This task makes the frozen app feature-complete.

- [ ] **Step 3: Checkpoint** — note whether an edit was needed; no commit.

---

## Task 8: Bake-and-prove integration gate (RULES §9) + docs

**Files:**
- Modify: `dev/SESSION_STATE.md`, `dev/MATRIX_MAP.md`, `dev/CHANGELOG.md` (record the merge + the new presentation data-flow)

- [ ] **Step 1: Run the full new-file suite once**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_topical_merge.py tests/test_topical_index.py tests/test_presentation_polish.py -v
```
Expected: all pass.

- [ ] **Step 2: Rebuild a flagship edition and prove the EPUB**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" ebible build ethiopian-tewahedo
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" ebible verify
```
Then run epubcheck against the built EPUB with the bundled jar (memory `reference_epubcheck` — always pass `--jar`):
```powershell
& "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m epubcheck --jar "<site-packages>\epubcheck\epubcheck.jar" "<built ethiopian-tewahedo .epub>"
```
Expected: `ebible verify` errors=0; epubcheck **0 fatals / 0 errors / 0 warnings / 0 infos**. Open `topical.xhtml` in the built EPUB and confirm `(N·T)`/`(N)`/`(T)` tags render and the intro credits both works.

- [ ] **Step 3: Run the project gates**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts/lint_rules.py
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m ruff format --check scripts/matter_pages.py scripts/api/editions.py scripts/web.py scripts/build_edition.py tests/test_topical_merge.py
```
Expected: `lint_rules` 16/0/0; ruff format clean (if not, run `ruff format` on the listed files — memory `feedback_ruff_format_before_save`).

- [ ] **Step 4: Update the docs** — add a 2026-05-26 SESSION_STATE banner (Torrey now surfaced in the topical index; default `both`; byte-compat naves path), a MATRIX_MAP entry for the `topical_index_source` field + the merged-page data-flow, and a CHANGELOG entry.

- [ ] **Step 5: Checkpoint** — all gates green; no commit.

---

## Task 9: Save gate (user-triggered)

**This is the ONLY commit point.** Per project rules a commit happens only on the user's "save".

- [ ] **Step 1:** Confirm `git status` shows only intended changes (no stray temp files — memory `feedback_session_start_ram`).
- [ ] **Step 2:** Present the work and ask the user to **save**. On their go, run `save.ps1` via **PowerShell** (never Bash — memory `feedback_savecmd_bash_hazard`); the pre-commit hook runs `ruff format --check` + `lint_rules`.
- [ ] **Step 3:** After the commit, verify with `git log`/`git status` before claiming saved (memory `feedback_verify_commit_backup_truth`), then offer the E:/F: `git bundle --all` backup (memory `reference_backup_drives`).

---

## Self-Review

**1. Spec coverage:**
- Unified merged index → Task 2 (`build_merged_topic_index`). ✓
- `(N·T)`/`(N)`/`(T)` tags → Task 2 (tag logic) + Task 3 (render). ✓
- Casefold matching, no comma-split → Task 1 (`_norm_topic`) + Task 2 tests. ✓
- Title Case display → Task 1 (`_title_topic`) + Task 2 test. ✓
- Honest both-works intro → Task 3 (`_MERGED_TOPICAL_INTRO`). ✓
- Modes + graceful degradation + default both → Task 4 (`_write_topical_page`). ✓
- Byte-identical `naves` path → Task 3 (defaulted `intro=`) + Task 4 degrade tests + Task 3 Step 5 guard. ✓
- Configurable field (editions/web/customize) → Task 6. ✓
- Sources page credits Torrey → Task 5. ✓
- Frozen-build bundling → Task 7. ✓
- Bake-and-prove gate → Task 8. ✓

**2. Placeholder scan:** No TBD/TODO; every code step shows the code; the one conditional (Task 6 Step 5 / Task 7) gives the exact decision rule + the +1 it implies. ✓

**3. Type consistency:** `build_merged_topic_index` returns `(display, tag, refs)` 3-tuples; `render_merged_topical_index_page` and `_write_topical_page` consume exactly that. `render_topical_index_page` keeps its 2-tuple `(topic, refs)` contract (single-source). `_write_topical_page` signature matches its call site in `inject_back_matter`. `TOPICAL_INDEX_SOURCES` defined in `matter_pages.py`, re-exported via `build_edition.py`, imported by the validator from `build_edition`. ✓
