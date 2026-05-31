# EPUB Presentation Polish Implementation Plan
**Status:** shipped — CSS + front-matter polish + configurable reader settings

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the built EPUBs read well in real readers (Apple Books) — clean 2-page front matter with real computed counts, a reader-facing **"Guide to the Notes"** symbol legend, left-aligned body text, an in-frame cover — then (Phase 2) add the four configurable presentation settings.

**Architecture:** Phase 1 is **build-time + base-CSS only** (no base-HTML structural regen): edit the shared `epub_working/stylesheet.css`, rewrite the build-time copyright page, add a build-time symbol-legend page, and drop the placeholder introduction page. Phase 2 adds the four `editions.yaml` enum settings (`marker_style`, `verse_popup_style`, `note_popup_style`, `title_page_style`) wired through the established `editions.yaml → /customize → build` pattern, and re-bakes the base HTML for the marker/note changes.

**Tech Stack:** Python 3.14 (stdlib `http.server` web layer, no framework), custom comment-preserving YAML, pytest, EPUB3 (calibre-base HTML + a packaging zip step), epubcheck (Java 8).

**Source spec:** `docs/superpowers/specs/2026-05-24-epub-presentation-polish-design.md` (read §5, §5.3, §12 first).

---

## Project-specific execution rules (READ BEFORE STARTING)

- **Interpreter:** use the full path `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe` (bare `python`/`python3` may hit a broken Windows Store alias). Below this is written as `PY`.
- **Every test run:** `$env:PYTHONUTF8="1"` first, or ~72 tests fail with cp1252 errors.
- **Do NOT auto-commit.** This project has NO git remote (deleted 2026-05-12); commits are local-only via `save.ps1` and happen **only when the user says "save."** "continue" ≠ "save." So every task below ends by running `ruff format` on changed Python files + the task's tests; the actual commit is batched when the user asks to save. (This overrides the writing-plans skill's per-task `git commit` step — user/project rules outrank the skill.)
- **Before any save:** `PY -m ruff format <changed .py files>` or the pre-commit hook `ruff format --check .` blocks the commit. CSS/XHTML are not ruff-formatted.
- **Protected paths:** `content/editions.yaml` is SHA-guarded by `tests/conftest.py`; any test mutating it MUST back it up (`shutil.copy`) and restore in `finally`, and call `config.load_editions.cache_clear()` after. (Phase 1 does not mutate `editions.yaml`; Phase 2 does.)
- **Build cache:** build tests MUST `monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)` + `cache_store` likewise, or they read a stale cached EPUB.
- **Do NOT run `scripts/apply_style.py`** during this work — its managed-CSS region is stale vs its generator (agent recon), and a stray run would expand the managed block. All Phase-1 CSS edits are OUTSIDE that managed region (`/* === BEGIN apply_style.py managed region */` at ~line 445), so they survive untouched.
- **Slow files — never run whole:** `tests/test_web_filesplit.py`, `tests/test_matrix_psi35.py` (~23 min each). Use targeted node-ids.
- **Byte-compat posture (different from this project's norm):** Phase 1 **intentionally changes** output (CSS, copyright page, +legend page, −intro page). Do NOT assert byte-identity. Instead pin the NEW expected output and prove the *non-targeted* parts unchanged (verse text, note bodies, `<aside>` counts) via categorize-diff in the final verification task.

---

## File Structure (Phase 1)

| File | Responsibility | Action |
|---|---|---|
| `epub_working/stylesheet.css` | Shared base stylesheet copied into every build; themes append after it | Modify (left-align, cover-fit, legend CSS) |
| `scripts/build_edition.py` | Per-edition build pipeline; `render_copyright_page`, `inject_copyright_page`, `build_one` | Modify (copyright rewrite, new legend functions, drop intro) |
| `scripts/core/matrix.py` | `total_for_edition`, `breakdown_by_category` (per-edition counts) | Read-only (compose) |
| `scripts/core/config.py` | `load_categories()`, `categories_by_id()` | Read-only (compose) |
| `content/categories.yaml` | 15 categories: `id`/`label`/`symbol`/`description`/`sort_order` | Read-only (legend data source) |
| `tests/test_presentation_polish.py` | All Phase-1 tests | Create |

---

## TASK 1 — Left-align body text (kill justified stretching)

**Files:**
- Modify: `epub_working/stylesheet.css` (justify sites at lines ~9, ~71, ~189-195, ~291, ~419-420)
- Test: `tests/test_presentation_polish.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_presentation_polish.py`:

```python
"""EPUB presentation polish (2026-05-24) — front matter, reader guide, CSS fixes.
Spec: docs/superpowers/specs/2026-05-24-epub-presentation-polish-design.md.
NOTE: this work INTENTIONALLY changes built output — pin the NEW output, do not
assume byte-identity."""

from __future__ import annotations

import zipfile
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
BASE_CSS = REPO / "epub_working" / "stylesheet.css"


class TestLeftAlign:
    def test_base_stylesheet_has_no_justified_body_text(self):
        css = BASE_CSS.read_text(encoding="utf-8")
        # Every body-text justify rule is converted to left; centering/right
        # rules use the keywords center/right and are untouched.
        assert "text-align: justify" not in css, (
            "justified body text still present — stretches short lines in Apple Books"
        )

    def test_base_stylesheet_drops_hyphenation_with_justify(self):
        css = BASE_CSS.read_text(encoding="utf-8")
        # Hyphenation only existed to support justification; with left-align it
        # should be gone from the body/verse/intro rules.
        assert "hyphens: auto" not in css
        assert "-webkit-hyphens: auto" not in css
```

- [ ] **Step 2: Run test to verify it fails**

```
$env:PYTHONUTF8="1"; PY -m pytest tests/test_presentation_polish.py::TestLeftAlign -v
```
Expected: FAIL — `text-align: justify` is present (~6 sites).

- [ ] **Step 3: Make the edit**

`Read` `epub_working/stylesheet.css`, then at EACH of these rules replace `text-align: justify` → `text-align: left` and delete any `hyphens: auto;` / `-webkit-hyphens: auto;` declaration in the same rule. Do NOT touch `text-align: center` or `text-align: right` rules. Sites (verify by reading — line numbers approximate):
- `body { … }` (~line 9): `justify`→`left`; drop `hyphens: auto; -webkit-hyphens: auto;`
- `.verse-p, .verse-p-flush, … { … }` (~line 71): `justify !important`→`left !important`; drop `hyphens: auto;`
- the "FORCE JUSTIFY" block `body p { text-align: justify; }` (~lines 189-195): `justify`→`left` (leave the adjacent `body p.right-p { text-align: right; }` alone)
- `p.verse-p { … }` (~line 291): `justify`→`left`; drop `hyphens: auto;`
- `.intro-lede { … }` / `.intro-body-p { … }` (~lines 419-420): `justify`→`left`; drop `hyphens: auto;`

Also rename the "FORCE JUSTIFY" comment to "FORCE LEFT-ALIGN" so the comment doesn't lie.

- [ ] **Step 4: Run test to verify it passes**

```
$env:PYTHONUTF8="1"; PY -m pytest tests/test_presentation_polish.py::TestLeftAlign -v
```
Expected: PASS.

- [ ] **Step 5: Checkpoint (no commit)** — no `.py` changed; nothing to ruff-format. Leave staged for the next user "save."

---

## TASK 2 — Cover fits the reader frame (`object-fit: contain`)

**Files:**
- Modify: `epub_working/stylesheet.css` (`.cover-wrap .cover-img`, ~line 406)
- Test: `tests/test_presentation_polish.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_presentation_polish.py`:

```python
class TestCoverFit:
    def test_cover_img_fits_frame(self):
        css = BASE_CSS.read_text(encoding="utf-8")
        # The cover image must scale to fit the reader frame, not overflow it.
        assert "object-fit: contain" in css, "cover image missing object-fit: contain"
        assert "max-height: 100%" in css, "cover image missing a height cap"
```

- [ ] **Step 2: Run test to verify it fails**

```
$env:PYTHONUTF8="1"; PY -m pytest tests/test_presentation_polish.py::TestCoverFit -v
```
Expected: FAIL — no `object-fit` anywhere in the codebase.

- [ ] **Step 3: Make the edit**

In `epub_working/stylesheet.css`, change the `.cover-wrap .cover-img` rule (~line 406) from:
```css
.cover-wrap .cover-img { display: block; width: 100%; max-width: 100%; height: auto; margin: 0 auto; }
```
to:
```css
.cover-wrap .cover-img { display: block; width: auto; max-width: 100%; max-height: 100%; height: auto; object-fit: contain; margin: 0 auto; }
```
(`width: auto` + `max-height: 100%` + `object-fit: contain` lets the cover scale down to fit the frame without forced full-width stretching.)

- [ ] **Step 4: Run test to verify it passes**

```
$env:PYTHONUTF8="1"; PY -m pytest tests/test_presentation_polish.py::TestCoverFit -v
```
Expected: PASS.

- [ ] **Step 5: Checkpoint (no commit).**

---

## TASK 3 — Copyright page: real counts + real publisher (kill "1,371/14" + `TODO_`) + collapse sections

**Files:**
- Modify: `scripts/build_edition.py` — `render_copyright_page` (~1301-1362), `inject_copyright_page` (~1880-1934)
- Read: `scripts/core/matrix.py:420` (`total_for_edition`), `:425` (`breakdown_by_category`); `build_edition.py:1025` (`_resolve_publishing`)
- Test: `tests/test_presentation_polish.py`

- [ ] **Step 1: Confirm the publisher-data source**

`Read` `build_edition.py:1025-1049` (`_resolve_publishing`) and grep `PUBLISHING_DEFAULTS` in `scripts/web.py` to confirm the key names it returns (e.g. `publisher_name`, `copyright_year`, possibly `copyright_holder`/`contributor`). The render function below uses defensive `.get(...) or "<canonical default>"` so it is correct even if a key is absent — but confirm so the happy path reads from the real source.

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_presentation_polish.py`:

```python
class TestCopyrightPage:
    def _publishing(self):
        return {
            "publisher_name": "YHWH Ya' Way Editions",
            "copyright_year": "2026",
            "copyright_holder": "Bogdan Zorlescu",
        }

    def test_no_todo_placeholders(self):
        from scripts.build_edition import render_copyright_page

        ed = {"id": "catholic-study", "title": "The Catholic Study Bible — Ethiopian Edition"}
        html = render_copyright_page(
            ed, self._publishing(), "test-v", annotation_count=12345, category_count=9
        )
        assert "TODO_" not in html, "copyright page still leaks TODO_ placeholders"

    def test_no_stale_hardcoded_count(self):
        from scripts.build_edition import render_copyright_page

        ed = {"id": "catholic-study", "title": "T"}
        html = render_copyright_page(ed, self._publishing(), "v", annotation_count=12345, category_count=9)
        assert "1,371" not in html, "stale hardcoded annotation count still present"
        assert "14 categories" not in html

    def test_real_counts_rendered(self):
        from scripts.build_edition import render_copyright_page

        ed = {"id": "catholic-study", "title": "T"}
        html = render_copyright_page(ed, self._publishing(), "v", annotation_count=12345, category_count=9)
        assert "12,345" in html, "computed annotation count not rendered (expected thousands-separated)"
        assert "9 categories" in html

    def test_canonical_identity(self):
        from scripts.build_edition import render_copyright_page

        ed = {"id": "catholic-study", "title": "T"}
        html = render_copyright_page(ed, self._publishing(), "v", annotation_count=10, category_count=1)
        assert "YHWH Ya&#8217; Way Editions" in html or "YHWH Ya' Way Editions" in html
        assert "Bogdan Zorlescu" in html
        assert "2026" in html
        assert "urn:yhwh:edition:catholic-study" in html
```

- [ ] **Step 3: Run tests to verify they fail**

```
$env:PYTHONUTF8="1"; PY -m pytest tests/test_presentation_polish.py::TestCopyrightPage -v
```
Expected: FAIL — `render_copyright_page` signature lacks `annotation_count`/`category_count`; current output has `TODO_`, "1,371", no computed counts.

- [ ] **Step 4: Rewrite `render_copyright_page`**

Replace the function at `build_edition.py:1301-1362` with a version that (a) takes `publishing` + keyword counts instead of the onix `defaults`, (b) uses canonical defaults, (c) interpolates the computed counts, (d) collapses to two compact sections:

```python
def render_copyright_page(
    edition: dict,
    publishing: dict,
    version: str,
    *,
    annotation_count: int,
    category_count: int,
) -> str:
    """Render the colophon/copyright XHTML for one edition.

    Identity (publisher / holder / year) comes from ``publishing``
    (scripts.build_edition._resolve_publishing — the post-Ω.0 source of
    truth), NOT the dead content/onix.py TODO_ defaults. Annotation/category
    counts are the edition's REAL computed counts (scripts.core.matrix), not a
    hardcoded literal. Consolidated to a compact 1-page colophon (spec
    2026-05-24 §5.1)."""
    pub = publishing.get("publisher_name") or "YHWH Ya' Way Editions"
    holder = (
        publishing.get("copyright_holder")
        or (publishing.get("contributor") or {}).get("name")
        or "Bogdan Zorlescu"
    )
    cyear = str(publishing.get("copyright_year") or "2026")
    edition_title = edition.get("title_full", edition.get("title", "Untitled"))
    edition_subtitle = edition.get("title_subtitle", "")
    edition_urn = f"urn:yhwh:edition:{edition['id']}"
    description = (edition.get("description", "") or "").strip()
    pub_x = html.escape(pub)
    holder_x = html.escape(holder)
    ann = f"{annotation_count:,}"
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>Colophon</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="copyright-page">
  <section class="copyright-page" epub:type="copyright-page">
    <h1 class="copyright-title">{html.escape(edition_title)}</h1>
    {f'<p class="copyright-subtitle">{html.escape(edition_subtitle)}</p>' if edition_subtitle else ""}

    <hr class="copyright-rule"/>

    <p class="copyright-compiler"><strong>YHWH Ya&#8217; Way</strong> — published by <strong>{pub_x}</strong>, {cyear}.</p>
    <p>&#169; {cyear} {holder_x}. All rights reserved. Editorial notes, selection, arrangement, and presentation are original editorial work; the underlying biblical texts and cited public-domain reference works retain their own public-domain status.</p>
    <p>This edition carries <strong>{ann}</strong> annotations across <strong>{category_count} categories</strong> — a key to the symbols follows on the next page.</p>

    <h2 class="copyright-heading">Sources</h2>
    <p>Biblical text: <strong>World English Bible</strong> (Public Domain). Original-language witnesses, lexica, cross-references, and patristic/rabbinic/reformation commentary are drawn from public-domain sources; per-note attribution is preserved in the apparatus.</p>

    <h2 class="copyright-heading">This Edition</h2>
    <p><strong>Edition ID:</strong> {edition_urn}<br/>
       <strong>Publisher:</strong> {pub_x}<br/>
       <strong>Build:</strong> {html.escape(version)}</p>
    {f'<p class="copyright-about">{html.escape(description)}</p>' if description else ""}
  </section>
</body>
</html>
"""
```

- [ ] **Step 5: Update `inject_copyright_page` to compute + pass the new args**

In `inject_copyright_page` (~1880-1934): remove the onix.py `DEFAULTS` load and the `EDITIONS` merge; instead compute `publishing` and counts. Replace the body up to the `# 1) Write the page` comment with:

```python
def inject_copyright_page(tmp: Path, edition: dict, version: str) -> None:
    """Write copyright.xhtml into tmp, register it in content.opf (manifest +
    spine after titlepage), add a nav.xhtml TOC entry. Identity from
    _resolve_publishing; counts from scripts.core.matrix (real, per-edition)."""
    from scripts.core import matrix as _matrix

    publishing = _resolve_publishing(edition)
    edition_id = edition["id"]
    annotation_count = _matrix.total_for_edition(edition_id)
    category_count = sum(1 for n in _matrix.breakdown_by_category(edition_id).values() if n > 0)

    # 1) Write the page
    html_text = render_copyright_page(
        edition, publishing, version, annotation_count=annotation_count, category_count=category_count
    )
    (tmp / "copyright.xhtml").write_text(html_text, encoding="utf-8")
    # 2) + 3) OPF + nav patches: UNCHANGED from the current implementation.
```
Keep the existing OPF manifest/spine patch and nav patch (steps 2 & 3) exactly as they are. (If `render_copyright_page` is referenced elsewhere — next step — those callers update too.)

- [ ] **Step 6: Find + fix any other caller / pinned test**

```
$env:PYTHONUTF8="1"; PY -m pytest --collect-only -q 2>$null  # sanity
```
Then `Grep` the repo for `render_copyright_page`, `"1,371"`, and `TODO_PUBLISHER` in `tests/` and `scripts/`. Update any test that pins the OLD signature or the OLD strings — in particular inspect `tests/test_omega0_free_public_pivot.py` (it may assert the TODO_/onix behavior). Re-point such assertions to the new behavior (no `TODO_`, real counts). Show the diff for each changed test.

- [ ] **Step 7: Run tests to verify they pass**

```
$env:PYTHONUTF8="1"; PY -m pytest tests/test_presentation_polish.py::TestCopyrightPage -v
$env:PYTHONUTF8="1"; PY -m pytest tests/test_omega0_free_public_pivot.py -v
```
Expected: PASS.

- [ ] **Step 8: ruff-format the changed module (no commit)**

```
PY -m ruff format scripts/build_edition.py tests/test_presentation_polish.py
```

---

## TASK 4 — "A Guide to the Notes" symbol legend page (the reader-facing glossary)

**Files:**
- Modify: `scripts/build_edition.py` — add `render_symbol_legend_page` + `inject_symbol_legend_page`; call the latter in `build_one` (~after line 2992, right after `inject_copyright_page`)
- Modify: `epub_working/stylesheet.css` — legend CSS (static region)
- Read: `content/categories.yaml`, `scripts/core/config.py:288` (`load_categories`), `scripts/core/matrix.py:425` (`breakdown_by_category`)
- Test: `tests/test_presentation_polish.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_presentation_polish.py`:

```python
class TestSymbolLegendPure:
    def _cats(self):
        return [
            {"symbol": "◇", "label": "Commentary / Tradition", "description": "Interpretive readings", "count": 100},
            {"symbol": "✦", "label": "Topical", "description": "Topical groupings", "count": 50},
        ]

    def test_renders_each_symbol_label_description_count(self):
        from scripts.build_edition import render_symbol_legend_page

        html = render_symbol_legend_page({"id": "x", "title": "T"}, self._cats(), "v")
        assert "A Guide to the Notes" in html
        for c in self._cats():
            assert c["symbol"] in html
            assert c["label"] in html
            assert c["description"] in html
        assert "100 notes" in html and "50 notes" in html

    def test_well_formed_xml(self):
        import xml.dom.minidom as _md
        from scripts.build_edition import render_symbol_legend_page

        html = render_symbol_legend_page({"id": "x", "title": "T"}, self._cats(), "v")
        _md.parseString(html)  # raises on malformed XML


class TestSymbolLegendEditionAware:
    def test_only_present_categories_listed(self, tmp_path, monkeypatch):
        import scripts.build_edition as be
        from scripts.core import build_cache, config

        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)
        all_kinds = config.load_kinds()
        # jewish-study uses the Tanakh canon + a scholarly profile; it should
        # NOT carry the edition-distinctive Mariological category symbol (❖).
        stats = be.build_one("jewish-study", tmp_path, "legend-test", all_kinds, force=True)
        import zipfile

        with zipfile.ZipFile(stats["output_path"]) as zf:
            name = next(n for n in zf.namelist() if n.endswith("legend.xhtml"))
            legend = zf.read(name).decode("utf-8")
        assert "A Guide to the Notes" in legend
        # at least one symbol present (the edition has notes)
        assert any(sym in legend for sym in ("⌘", "◇", "✦", "‖", "⌂"))

    def test_legend_in_nav_toc(self, tmp_path, monkeypatch):
        import zipfile

        import scripts.build_edition as be
        from scripts.core import build_cache, config

        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)
        all_kinds = config.load_kinds()
        stats = be.build_one("catholic-study", tmp_path, "legend-test", all_kinds, force=True)
        with zipfile.ZipFile(stats["output_path"]) as zf:
            nav = zf.read(next(n for n in zf.namelist() if n.endswith("nav.xhtml"))).decode("utf-8")
        assert 'href="legend.xhtml"' in nav
```

- [ ] **Step 2: Run tests to verify they fail**

```
$env:PYTHONUTF8="1"; PY -m pytest tests/test_presentation_polish.py::TestSymbolLegendPure -v
```
Expected: FAIL — `render_symbol_legend_page` not defined.

- [ ] **Step 3: Implement the pure renderer**

Add to `scripts/build_edition.py` (near `render_copyright_page`):

```python
def render_symbol_legend_page(edition: dict, categories: list[dict], version: str) -> str:
    """Render the 'A Guide to the Notes' XHTML page.

    ``categories`` is an ORDERED list of dicts {symbol, label, description,
    count} — only the categories that actually appear in this edition (the
    caller filters + sorts). Spec 2026-05-24 §5.3: the necessary companion to
    moving category symbols out of the running text and into the notes."""
    rows = []
    for c in categories:
        rows.append(
            '    <p class="legend-row">'
            f'<span class="legend-sym">{html.escape(c["symbol"])}</span> '
            f'<span class="legend-label">{html.escape(c["label"])}</span> '
            f'<span class="legend-count">({c["count"]:,} notes)</span><br/>'
            f'<span class="legend-desc">{html.escape(c["description"])}</span></p>'
        )
    body = "\n".join(rows) if rows else '    <p class="legend-row">This edition carries no annotations.</p>'
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>A Guide to the Notes</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="frontmatter">
  <section class="legend-page" epub:type="frontmatter">
    <h1 class="legend-title">A Guide to the Notes</h1>
    <p class="legend-intro">Each annotation in this edition opens with a symbol marking the kind of note. The symbols used in this edition are:</p>
{body}
  </section>
</body>
</html>
"""
```

- [ ] **Step 4: Implement the injector + wire into `build_one`**

Add to `scripts/build_edition.py`:

```python
def inject_symbol_legend_page(tmp: Path, edition: dict, version: str) -> None:
    """Build the edition-aware 'A Guide to the Notes' page, write legend.xhtml,
    register it in the OPF (manifest + spine after copyright) and nav.xhtml TOC.
    Edition-aware: only categories with >0 notes in this edition, in
    categories.yaml sort_order."""
    from scripts.core import config, matrix as _matrix

    edition_id = edition["id"]
    present = _matrix.breakdown_by_category(edition_id)  # {cat_id: count}
    cats = sorted(config.load_categories(), key=lambda c: c.get("sort_order", 999))
    ordered = [
        {
            "symbol": c.get("symbol", "•"),
            "label": c.get("label", c["id"]),
            "description": c.get("description", ""),
            "count": present.get(c["id"], 0),
        }
        for c in cats
        if present.get(c["id"], 0) > 0
    ]

    html_text = render_symbol_legend_page(edition, ordered, version)
    (tmp / "legend.xhtml").write_text(html_text, encoding="utf-8")

    opf_path = tmp / "content.opf"
    if opf_path.is_file():
        opf = opf_path.read_text(encoding="utf-8")
        if "legend.xhtml" not in opf:
            opf = opf.replace(
                '<item id="copyright" href="copyright.xhtml" media-type="application/xhtml+xml"/>',
                '<item id="copyright" href="copyright.xhtml" media-type="application/xhtml+xml"/>\n    '
                '<item id="legend" href="legend.xhtml" media-type="application/xhtml+xml"/>',
            )
            opf = opf.replace(
                '<itemref idref="copyright"/>', '<itemref idref="copyright"/>\n    <itemref idref="legend"/>'
            )
            opf_path.write_text(opf, encoding="utf-8")

    nav_path = tmp / "nav.xhtml"
    if nav_path.is_file():
        nav = nav_path.read_text(encoding="utf-8")
        if 'href="legend.xhtml"' not in nav:
            nav = nav.replace(
                '<li><a href="copyright.xhtml">Copyright &amp; Credits</a></li>',
                '<li><a href="copyright.xhtml">Colophon</a></li>\n'
                '      <li><a href="legend.xhtml">A Guide to the Notes</a></li>',
                1,
            )
            nav_path.write_text(nav, encoding="utf-8")
```
NOTE: `inject_copyright_page` inserts the copyright manifest item BEFORE `titlepage` and the spine itemref AFTER `titlepage`; the legend replacements above anchor on the copyright item/itemref, so legend lands right after copyright in both manifest and spine. The nav `.replace` also renames the copyright TOC label to "Colophon" to match the new page title — verify the exact current nav string for copyright first and match it.

Then in `build_one`, immediately after the `inject_copyright_page(tmp, edition, version)` call (~line 2992), add:
```python
        inject_symbol_legend_page(tmp, edition, version)
```

- [ ] **Step 5: Add legend CSS**

In `epub_working/stylesheet.css`, in the static front-matter region (near `.book-title-page`, ~line 403, OUTSIDE the apply_style managed region), add:
```css
/* === A Guide to the Notes (symbol legend) === */
.legend-page { padding: 1.2em 0.8em; text-align: left; }
.legend-title { font-size: 1.5em; text-align: center; margin: 0 0 0.4em; }
.legend-intro { margin: 0 0 1em; }
.legend-row { margin: 0 0 0.7em; line-height: 1.45; }
.legend-sym { font-size: 1.15em; font-weight: 700; margin-right: 0.4em; }
.legend-label { font-variant-caps: small-caps; letter-spacing: 0.04em; font-weight: 700; }
.legend-count { color: #6E5840; font-size: 0.85em; }
.legend-desc { color: #333; }
```

- [ ] **Step 6: Run tests to verify they pass**

```
$env:PYTHONUTF8="1"; PY -m pytest tests/test_presentation_polish.py::TestSymbolLegendPure tests/test_presentation_polish.py::TestSymbolLegendEditionAware -v
```
Expected: PASS. (The two build tests each run one `build_one` — allow ~1 min.)

- [ ] **Step 7: ruff-format (no commit)**

```
PY -m ruff format scripts/build_edition.py tests/test_presentation_polish.py
```

---

## TASK 5 — "About this Edition" auto-generated spec page (repurpose the intro page)

> **SCOPE UPDATED 2026-05-24 (user):** this task no longer merely *drops* the placeholder `introduction.xhtml` — it **repurposes** it into an **auto-generated "About this Edition" specification page**: canon + book count · the verse-popup languages/witnesses selected · the note categories included + counts · theme · total annotations — all **composed** from the edition's resolved config (reuse the `/build-tracker` summary logic + `matrix`/`config`/`popup_versions`), PLUS an optional builder-typed `description` (make `description` editable in `/customize`: add to `EDITABLE_TEXT` + a `<textarea data-field="description">`). Generated at build time so it always matches what the builder picked. See spec §5.1 / §5.3. Full TDD steps to be finalized when the front-matter design locks; the old "drop the placeholder intro content" requirement still holds (no `TODO_`/placeholder copy survives), it's just replaced by real generated content.

**Files (provisional — finalize at execution):**
- Modify: `scripts/build_edition.py` — `inject_copyright_page` (or a sibling helper called in the same place) to remove `introduction.xhtml` from the per-build manifest + spine + nav
- Test: `tests/test_presentation_polish.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_presentation_polish.py`:

```python
class TestFrontMatterConsolidation:
    def test_placeholder_introduction_dropped(self, tmp_path, monkeypatch):
        import zipfile

        import scripts.build_edition as be
        from scripts.core import build_cache, config

        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)
        all_kinds = config.load_kinds()
        stats = be.build_one("catholic-study", tmp_path, "fm-test", all_kinds, force=True)
        with zipfile.ZipFile(stats["output_path"]) as zf:
            opf = zf.read(next(n for n in zf.namelist() if n.endswith("content.opf"))).decode("utf-8")
        # The placeholder introduction page is removed from the reading order.
        assert '<itemref idref="introduction"/>' not in opf, "placeholder introduction still in spine"

    def test_front_matter_order_is_title_colophon_legend(self, tmp_path, monkeypatch):
        import re
        import zipfile

        import scripts.build_edition as be
        from scripts.core import build_cache, config

        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)
        all_kinds = config.load_kinds()
        stats = be.build_one("catholic-study", tmp_path, "fm-test", all_kinds, force=True)
        with zipfile.ZipFile(stats["output_path"]) as zf:
            opf = zf.read(next(n for n in zf.namelist() if n.endswith("content.opf"))).decode("utf-8")
        order = re.findall(r'<itemref idref="(\w+)"/>', opf)
        # titlepage → copyright → legend come first, in that order.
        assert order[:3] == ["titlepage", "copyright", "legend"], order[:3]
```

- [ ] **Step 2: Run test to verify it fails**

```
$env:PYTHONUTF8="1"; PY -m pytest tests/test_presentation_polish.py::TestFrontMatterConsolidation -v
```
Expected: FAIL — `introduction` still in spine; order has `introduction` interleaved.

- [ ] **Step 3: Implement the drop**

Add a helper to `scripts/build_edition.py` and call it from `inject_copyright_page` (after the nav patch) — or inline at the end of `inject_copyright_page`:

```python
def _drop_placeholder_introduction(tmp: Path) -> None:
    """Remove the placeholder introduction.xhtml from the per-build manifest,
    spine, and nav TOC (spec 2026-05-24 §5.1: consolidate front matter; the base
    introduction page carries only 'placeholder text … added later')."""
    opf_path = tmp / "content.opf"
    if opf_path.is_file():
        opf = opf_path.read_text(encoding="utf-8")
        opf = re.sub(r'\s*<item id="introduction" href="introduction\.xhtml"[^>]*/>', "", opf)
        opf = re.sub(r'\s*<itemref idref="introduction"/>', "", opf)
        opf_path.write_text(opf, encoding="utf-8")
    nav_path = tmp / "nav.xhtml"
    if nav_path.is_file():
        nav = nav_path.read_text(encoding="utf-8")
        nav = re.sub(r'\s*<li><a href="introduction\.xhtml">[^<]*</a></li>', "", nav)
        nav_path.write_text(nav, encoding="utf-8")
    intro = tmp / "introduction.xhtml"
    if intro.is_file():
        intro.unlink()
```
Call it at the end of `inject_copyright_page` (so the front-matter consolidation is one coherent step): `_drop_placeholder_introduction(tmp)`. Confirm the exact manifest item string for introduction first (`Read` `epub_working/content.opf` ~line 25) and match the regex.

- [ ] **Step 4: Run test to verify it passes**

```
$env:PYTHONUTF8="1"; PY -m pytest tests/test_presentation_polish.py::TestFrontMatterConsolidation -v
```
Expected: PASS.

- [ ] **Step 5: ruff-format (no commit)**

```
PY -m ruff format scripts/build_edition.py
```

---

## TASK 6 — Phase 1 verification gate (prove the change is clean)

**Files:** none (verification only)

- [ ] **Step 1: Full Phase-1 test file**

```
$env:PYTHONUTF8="1"; PY -m pytest tests/test_presentation_polish.py -v
```
Expected: ALL PASS.

- [ ] **Step 2: Build a canon-shape representative set + epubcheck**

Build at least catholic-study (deutero), jewish-study (Tanakh), evangelical-reformed (66), ethiopian-tewahedo (flagship). For each, confirm the EPUB validates. epubcheck needs Java 8 (`C:\Program Files\Java\jre1.8.0_491\bin`, not on PATH) + the bundled jar in the PyPI `epubcheck` site-package (`--jar`). Expected: **0 fatals / 0 errors** on each (the new legend page + rewritten colophon must be well-formed XHTML — `TestSymbolLegendPure::test_well_formed_xml` pre-checks the legend).

- [ ] **Step 3: Integrity + categorize-diff (non-targeted parts unchanged)**

```
$env:PYTHONUTF8="1"; PY -m scripts.audit ...   # or: ./ebible verify
```
Expected: `ebible verify` **errors=0 / 24,015 paired** (verse text + note bodies + aside pairing UNCHANGED — Phase 1 touched only CSS + front-matter pages, never the scripture/notes body). Confirm `<aside>` counts and note-marker counts are unchanged vs HEAD (the change is additive front matter + CSS, not corpus).

- [ ] **Step 4: Lint + format**

```
$env:PYTHONUTF8="1"; PY scripts/lint_rules.py
PY -m ruff format --check scripts/build_edition.py tests/test_presentation_polish.py
```
Expected: `lint_rules` 16/0/0; ruff-format clean.

- [ ] **Step 5: Report Phase 1 complete.** Front matter is now title → colophon (real counts, no `TODO_`, no "1,371") → **A Guide to the Notes** (edition-aware symbol legend); body text left-aligned; cover fits the frame. Await user "save" to commit (do not auto-commit).

---

# PHASE 2 — Configurable presentation settings (ROADMAP — expand into its own full TDD plan before executing)

Phase 2 is the four `editions.yaml` enum settings + the base-HTML re-bake. It is scoped here with resolved architecture (per spec §12) but should be expanded into a full task-by-task plan (`docs/superpowers/plans/2026-05-24-epub-presentation-polish-phase2.md`) before execution, because it changes the shared base HTML and warrants its own verification gate. The wiring pattern for ALL four fields is the established **"add an edition feature"** 6-step (clone the per-edition `theme` field + the `chapter_number_format` enum validator):

1. **Schema** — add the field to each edition in `content/editions.yaml` (default = unset, back-compat). Add the valid-value frozenset to `scripts/build_edition.py` (model: `CHAPTER_NUMBER_FORMATS`).
2. **Loader** — `scripts/web.py::api_customize_data` (~line 1526): `"<field>": e.get("<field>", "<default>")` next to `"theme"`.
3. **Validator** — `scripts/api/editions.py::api_save_edition_meta`: add to `EDITABLE_TEXT` (~560), the `EDITABLE` preview set (~491), and `_append_cloned_edition` scalar_fields (~144); add an enum-check block mirroring `chapter_number_format` (~583).
4. **UI** — `scripts/templates/customize.py`: a `<select data-field="<field>">` (model: the `chapter_number_format` inline-option select, ~384). Generic dirty-check/save needs no JS change.
5. **Build read** — per field (below).
6. **Tests** — clone `tests/test_traditions_psi8.py::TestTraditionsCustomizeAPI` (round-trip / invalid-input reject / UI-present) + `tests/test_themes.py::TestThemeReachesEpub` (reaches-EPUB). Pin NEW output, not byte-identity.

### 2A — `verse_popup_style` = cards (default) / stack  +  widen witnesses + drop KJV
- **Witness change (data, not bake):** edit each edition's `popup_languages_default` in `editions.yaml` (legacy ids at lines 123,158,205,242,271,310,350,394,436; two empty at 501,542) to the new default set → `wlc` + `lxx-greek` + `greek-nt` + `vulgate` + `arabic`; and change the unset-default fallback in `build_edition.py::_resolve_popup_languages` (~749) so `kjv` is pruned everywhere. `jps`/`douay`/`brenton-en` remain selectable, off by default. The bake (`generate_verse_popups.py`) is UNCHANGED — pruning happens at build time.
- **Layout:** add a container modifier class on `<aside class="vnote">` (`cards`/`stack`) — a build-time class-swap (default `cards`), since `build_vnote_aside` bakes base-wide. CSS for cards/stack + spine colors for the newer witnesses (`vnote-greek-nt`/`vnote-vulgate`/`vnote-arabic`/`vnote-douay`/`vnote-jps`) goes in `scripts/apply_style.py::render_managed_css` — BUT note the managed-region-staleness caveat; coordinate the regen.

### 2B — `note_popup_style` = chip (default) / pills  +  symbols-into-notes  +  `‖` fix (BASE REGEN)
- Edit `scripts/inject.py::build_aside` (~170): back-link char → fixed `↩` (stop reusing the category glyph — that is the `‖` bug); add a deliberate in-note category-symbol element (`<span class="note-sym">{glyph}</span>`). Mind the `.note-comm > p > .note-label { display:none }` rule (`stylesheet.css:163`) — ~95% of notes are `comm`; the chip must not rely on the hidden `.note-label`.
- chip/pills = build-time container class + CSS (managed region).
- **Re-bake the base** via `inject` for all books, then `generate_verse_popups` + `resync_marker_glyphs` (per SESSION_PLAYBOOK §7 — but note that playbook's bare-base regen is LOSSY for harvested popups; use the surgical method). Re-verify `ebible verify` + epubcheck.

### 2C — `marker_style` = numbers (default)  (BASE REGEN)
- Edit `scripts/inject.py::build_marker` (~150): `<sup>` carries a computed superscript **number** (numbering must be computed — pick the reset boundary, e.g. per chapter) with a neutral `marker-num` class (drop the per-kind tinted-pill class so no tofu/color). No inline category symbol (it now lives in the note, 2B).
- This is base-wide (inject runs into the shared base). The `editions.yaml` `marker_style` field defaults to `numbers`; true per-edition switching waits for the deferred `badge` mode.
- Re-bake + re-verify with 2B (same regen).

### 2D — `title_page_style` = full-bleed (default) / framed  +  per-book art (NEW BUILD PLUMBING)
- The 66 `content/covers/_book_defaults/<book>.jpg` do NOT enter the EPUB today. Build a new `apply_title_pages(tmp, edition)` in `build_edition.py` (called in `build_one` alongside `apply_chapter_decoration`, ~2967) that: copies the books' art into `tmp/images/<code>.jpg`, transforms each `book-title-frame` div to full-bleed/framed, and (via a new `patch_opf_book_images` modeled on `patch_opf_fonts`, ~2407) registers each image `<item>` in the manifest. Compute the image set AFTER canon filtering so dropped books don't leave orphaned manifest items. The 21 art-less Ethiopic books fall back to the current text-only title page. Do NOT route through `customize.py` (its `.html.frag` staging is orphaned).
- **Builder-uploadable art (spec §4.5, user request 2026-05-24):** `apply_title_pages` resolves each book's image via `scripts/core/covers.py::cover_record_for_edition` → **uploaded override → `_book_defaults/<book>.jpg` → text-only** — so the title TEXT stays constant while the picture is the builder's. The per-book upload reuses the existing `book_covers` + π.4-B validated-binary-upload + RULES §9 "uploadable binary asset" pipeline; ensure a per-book drag-drop affordance exists in the `/covers` (or title-page) console.

### 2E — Main cover-design + colour picker + universal cover-title placement (CONFIRMED 2026-05-24; spec §4.6)
The 25-template library (`content/covers/templates/`, 5 designs × 5 colours) is intact but generator-only. To make it a builder choice per RULES §2:
- **Clickable picker:** surface the 25 options (design family × colour) as a `/customize` (and/or `/wizard`) picker that writes the chosen template's composited output to the edition's `cover_image`, OR accepts an uploaded bespoke cover (reuse §4.5 upload). Likely touches `scripts/generate_edition_covers.py` (parameterize edition→template so the UI can drive it), `scripts/templates/customize.py` + `scripts/api/editions.py` (picker + save), `scripts/templates/covers.py`.
- **Universal cover-title placement (fix, re `apple_books_screenshots/cover.png`):** `_draw_centered_text` centers via `x = center_x - line_w//2` (ignores glyph side-bearing) and `title_y` is hardcoded to 460. With all 5 designs selectable, the title must sit in ONE band clear of every design's ornament (esp. central ornaments in `04_minimal_lines`/`05_missal_central`). Fix = render all 5 designs, pick a safe title band, re-center with PIL `draw.text(..., anchor="ma")`/`"mm"`, keep title TEXT unchanged; add a visual check across all 5 designs. This is the demo-visible cover bug the user flagged.

### Phase 2 verification
After 2A-2D: rebuild all 11 editions, epubcheck 0/0 each, `ebible verify` errors=0, categorize-diff confirms only the targeted asides/markers/CSS/title-pages changed, `lint_rules` 16/0/0, ruff-format clean. Phase 3 (`marker_style=badge`) stays deferred (needs the per-verse note-container injection point, spec §10).

---

## Self-review (Phase 1, against spec §5 + §5.3 + §12)

- §5.1 front matter → 2 pages: TASK 3 (collapse copyright) + TASK 5 (drop intro) → title + colophon (+ legend). ✓
- §5.1 kill `TODO_`: TASK 3 (switch off onix `DEFAULTS` → `_resolve_publishing`). ✓
- §5.1 kill stale "1,371/14": TASK 3 (`build_edition.py:1344` literal → computed counts). ✓
- §5.1 colophon identity (YHWH Ya' Way Editions / 2026 / © Bogdan Zorlescu): TASK 3 `test_canonical_identity`. ✓
- §5.2 left-align: TASK 1. ✓  §5.2 cover fit: TASK 2. ✓
- §5.3 edition-aware symbol legend + nav entry: TASK 4. ✓
- §12.1/.2 corrections (literal location, front-matter reality): reflected in TASK 3/5. ✓
- Byte-compat posture (pin NEW, categorize-diff non-targeted): TASK 6 step 3. ✓
- Glyph reliability (§10): TASK 4 `test_well_formed_xml` + TASK 6 epubcheck; font-subset embedding deferred to Phase 2 (the in-note symbols) since Phase 1 only shows symbols on the legend page where any missing glyph is immediately visible in the epubcheck/visual pass.
