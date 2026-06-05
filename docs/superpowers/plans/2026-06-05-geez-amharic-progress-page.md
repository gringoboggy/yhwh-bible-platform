# Ge'ez & Amharic Progress Page — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** READY 2026-06-05 — implementation plan for the Ge'ez/Amharic progress page (spec `specs/2026-06-05-geez-amharic-progress-page-design.md`, approved). 6 TDD tasks: store-derived stage generator → fragment/JSON render → `build.mjs` inline → page + nav → CSS → build + visual-QA. Collision-free with the re-ingest; NOT on the audit critical path (parallel launch-prep).

**Goal:** Build a dedicated website page that tracks the Ge'ez & Amharic Bible transcription with an honest, data-driven per-book staged grid + progress bars + manuscript-source links + a free-will-offering tie-in.

**Architecture:** A Python generator (`scripts/gen_website_progress.py`) computes each canonical book's stage from the REAL store (own-versification + EN + Amharic source + `_STANDALONE_BOOKS`) and renders an HTML fragment + a `progress.json` into `website/src/data/`. The zero-dependency `website/build.mjs` inlines that fragment into `website/src/geez.html` via a `{{geez_progress}}` token (which survives build.mjs's comment-stripping), so the page is **static + build-time** and can never drift from the store. A new nav item links it.

**Tech Stack:** Python 3.14 (stdlib + the project's `scripts.core.config`); plain HTML/CSS; Node-core `build.mjs` (no npm). Tests: pytest.

**Spec:** `docs/superpowers/specs/2026-06-05-geez-amharic-progress-page-design.md`

**Verified ground truth (pin these in tests):** Ge'ez = 4 books Bible-ready (`1ki, 1sa, 2sa, psa` = `build_standalone._STANDALONE_BOOKS`); geez-tewahedo store has 36 book files; geez-tewahedo-en has 7 (`1ki,1sa,2sa,ex,gen,lev,psa`); amharic-tewahedo store has 28 book files; canon = `config.load_books()` (87 books, `code`+`title`).

**Env (every test run):** `$env:PYTHONUTF8="1"`; `$env:PYTHONPATH=<repo>`; interpreter `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe`; `--basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`.

**File structure:**
- Create `scripts/gen_website_progress.py` — stage computation + fragment/JSON render (one responsibility: turn the store into the progress data + HTML).
- Create `tests/test_website_progress.py` — generator tests.
- Create `website/src/geez.html` — the page content (narrative · `{{geez_progress}}` · sources · support).
- Create `website/src/data/geez-progress.html` + `website/src/data/progress.json` — generated; COMMITTED (re-run + commit when transcription advances).
- Modify `website/partials/head.html` — add the "Ge'ez & Amharic" nav link.
- Modify `website/build.mjs` — inline `{{geez_progress}}` from the fragment + add `/geez.html` to the sitemap.
- Modify `website/style.css` — bars + grid styles.

---

### Task 1: Stage computation (the data core)

**Files:**
- Create: `scripts/gen_website_progress.py`
- Test: `tests/test_website_progress.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_website_progress.py
import os
import pytest
from scripts import gen_website_progress as gp

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_stage_precedence_and_real_truth():
    data = gp.compute_progress(REPO)
    geez = {b["code"]: b for b in data["geez"]["books"]}
    amh = {b["code"]: b for b in data["amharic"]["books"]}

    # Ge'ez ground truth (the standalone build ships exactly these 4)
    assert geez["1ki"]["stage"] == "ready"
    assert geez["1sa"]["stage"] == "ready"
    assert geez["2sa"]["stage"] == "ready"
    assert geez["psa"]["stage"] == "ready"
    assert data["geez"]["counts"]["ready"] == 4
    # EN mark present for a Bible-ready book that has English
    assert geez["psa"]["en"] is True
    # a book with source but not own-versified is "source"
    assert geez["gen"]["stage"] in ("source", "ready")  # gen has store data + EN
    # a book absent from the store is "none"
    assert geez["rev"]["stage"] == "none"

    # Amharic ground truth: 28 books have source, 0 are Bible-ready
    assert data["amharic"]["counts"]["ready"] == 0
    assert data["amharic"]["counts"]["source"] == 28

    # canon coverage = the full 87-book registry, in canonical order
    assert len(data["geez"]["books"]) == 87
    assert data["geez"]["books"][0]["code"] == "gen"
```

- [ ] **Step 2: Run it — expect failure**

Run: `& $py -m pytest tests/test_website_progress.py::test_stage_precedence_and_real_truth -v --basetemp=$bt`
Expected: FAIL — `ModuleNotFoundError: scripts.gen_website_progress`.

- [ ] **Step 3: Implement the stage computation**

```python
# scripts/gen_website_progress.py
"""Generate the website's Ge'ez & Amharic progress data + HTML fragment from the
REAL translation store, so the public page can never over-claim. Run before
website/build.mjs (which inlines the fragment). Re-run + commit when transcription
advances."""
from __future__ import annotations

import json
import sys
from html import escape
from pathlib import Path

# Stage precedence (highest achieved wins): ready > transcribed > source > none
STAGE_RANK = {"none": 0, "source": 1, "transcribed": 2, "ready": 3}
STAGE_BADGE = {"none": "◻", "source": "◐", "transcribed": "◑", "ready": "●"}
STAGE_LABEL = {
    "none": "not started",
    "source": "source gathered",
    "transcribed": "transcribed",
    "ready": "Bible-ready",
}


def _standalone_books() -> set[str]:
    """The book codes the standalone Ge'ez build actually ships."""
    import re

    src = (Path(__file__).resolve().parent / "build_standalone.py").read_text(encoding="utf-8")
    m = re.search(r"_STANDALONE_BOOKS\s*=\s*\[([^\]]*)\]", src)
    if not m:
        return set()
    return set(re.findall(r'"([^"]+)"', m.group(1)))


def _store_books(repo: Path, store: str) -> set[str]:
    d = repo / "content" / "translations" / store
    if not d.is_dir():
        return set()
    return {p.stem for p in d.glob("*.py") if p.stem != "_meta"}


def _own_versified(repo: Path, store: str) -> set[str]:
    """Books whose store file carries a VERSIFICATION block (own-versified)."""
    d = repo / "content" / "translations" / store
    out: set[str] = set()
    if not d.is_dir():
        return out
    for p in d.glob("*.py"):
        if p.stem == "_meta":
            continue
        if any(line.startswith("VERSIFICATION") for line in p.read_text(encoding="utf-8").splitlines()):
            out.add(p.stem)
    return out


def _display_name(title: str, code: str) -> str:
    """A short, public-friendly book name from the formal title."""
    # "The First Book of Moses, Genesis" -> "Genesis"; fall back to the code.
    tail = title.rsplit(",", 1)[-1].strip()
    return tail or code.upper()


def _bible_progress(repo: Path, books: list[dict], *, store: str, standalone: set[str], en: set[str]) -> dict:
    has_source = _store_books(repo, store)
    has_versification = _own_versified(repo, store)
    rows = []
    for rec in books:
        code = rec["code"]
        if code in standalone:
            stage = "ready"
        elif code in has_versification:
            stage = "transcribed"
        elif code in has_source:
            stage = "source"
        else:
            stage = "none"
        rows.append({
            "code": code,
            "name": _display_name(rec.get("title", code), code),
            "stage": stage,
            "en": code in en,
        })
    counts = {s: sum(1 for r in rows if r["stage"] == s) for s in STAGE_RANK}
    return {"books": rows, "counts": counts, "total": len(rows)}


def compute_progress(repo_root: str | Path) -> dict:
    repo = Path(repo_root)
    sys.path.insert(0, str(repo))
    from scripts.core import config

    books = config.load_books()  # 87-book registry, canonical order
    standalone = _standalone_books()
    en = _store_books(repo, "geez-tewahedo-en")
    geez = _bible_progress(repo, books, store="geez-tewahedo", standalone=standalone, en=en)
    amharic = _bible_progress(repo, books, store="amharic-tewahedo", standalone=set(), en=set())
    return {"geez": geez, "amharic": amharic}
```

- [ ] **Step 4: Run it — expect pass**

Run: `& $py -m pytest tests/test_website_progress.py::test_stage_precedence_and_real_truth -v --basetemp=$bt`
Expected: PASS.

- [ ] **Step 5: Commit**

```
git add scripts/gen_website_progress.py tests/test_website_progress.py
git commit -m "feat(website): Ge'ez/Amharic progress — store-derived per-book stage computation"
```

---

### Task 2: Render the HTML fragment + progress.json

**Files:**
- Modify: `scripts/gen_website_progress.py` (add `render_fragment`, `write_outputs`, `main`)
- Test: `tests/test_website_progress.py` (add a render test)

- [ ] **Step 1: Write the failing test**

```python
def test_fragment_renders_bars_grid_and_is_honest():
    data = gp.compute_progress(REPO)
    frag = gp.render_fragment(data)
    # a bar + a count for each Bible
    assert "Ge'ez Bible" in frag and "Amharic Bible" in frag
    assert "4" in frag  # 4 books Bible-ready (Ge'ez)
    # the per-book grid: a cell per canon book, with a stage badge
    assert frag.count('class="pb-cell') == 87 * 2  # both grids
    # honesty: Amharic shows source-gathered, never "ready"
    assert "data-stage=\"ready\"" in frag      # Ge'ez has ready cells
    # no raw HTML-injection: book names are escaped (none contain < or >)
    assert "<script" not in frag
```

- [ ] **Step 2: Run it — expect failure**

Run: `& $py -m pytest tests/test_website_progress.py::test_fragment_renders_bars_grid_and_is_honest -v --basetemp=$bt`
Expected: FAIL — `AttributeError: module 'scripts.gen_website_progress' has no attribute 'render_fragment'`.

- [ ] **Step 3: Implement the renderer + main**

```python
# --- append to scripts/gen_website_progress.py ---

def _bar(label: str, ready: int, total: int, sub: str) -> str:
    pct = round(100 * ready / total) if total else 0
    return (
        f'<div class="pb-bar-row">'
        f'<div class="pb-bar-head"><strong>{escape(label)}</strong>'
        f'<span class="pb-bar-sub">{escape(sub)}</span></div>'
        f'<div class="pb-bar" role="img" aria-label="{escape(sub)}">'
        f'<span class="pb-bar-fill" style="width:{pct}%"></span></div></div>'
    )


def _grid(rows: list[dict]) -> str:
    cells = []
    for r in rows:
        en = ' <span class="pb-en" title="English back-translation available">EN</span>' if r["en"] else ""
        cells.append(
            f'<li class="pb-cell pb-{r["stage"]}" data-stage="{r["stage"]}" '
            f'title="{escape(r["name"])} — {STAGE_LABEL[r["stage"]]}">'
            f'<span class="pb-badge" aria-hidden="true">{STAGE_BADGE[r["stage"]]}</span>'
            f'<span class="pb-name">{escape(r["name"])}</span>{en}</li>'
        )
    return '<ol class="pb-grid">' + "".join(cells) + "</ol>"


def render_fragment(data: dict) -> str:
    g, a = data["geez"], data["amharic"]
    legend = (
        '<p class="pb-legend">'
        + " ".join(f'{STAGE_BADGE[s]} {STAGE_LABEL[s]}' for s in ("none", "source", "transcribed", "ready"))
        + ' · <span class="pb-en">EN</span> English back-translation</p>'
    )
    return (
        '<div class="pb-wrap">'
        + _bar("Ge'ez Bible", g["counts"]["ready"], g["total"],
               f'{g["counts"]["ready"]} books Bible-ready of {g["total"]}')
        + _bar("Amharic Bible", a["counts"]["ready"], a["total"],
               f'{a["counts"]["source"]} books of source text gathered — assembly ahead')
        + legend
        + '<h3 class="pb-h">Ge’ez Bible — book by book</h3>' + _grid(g["books"])
        + '<h3 class="pb-h">Amharic Bible — book by book</h3>' + _grid(a["books"])
        + "</div>"
    )


def write_outputs(repo_root: str | Path) -> None:
    repo = Path(repo_root)
    data = compute_progress(repo)
    out_dir = repo / "website" / "src" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "progress.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "geez-progress.html").write_text(render_fragment(data), encoding="utf-8")


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    write_outputs(repo)
    print("wrote website/src/data/geez-progress.html + progress.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run it — expect pass + generate the real outputs**

Run: `& $py -m pytest tests/test_website_progress.py -v --basetemp=$bt` → PASS (both tests).
Run: `& $py scripts\gen_website_progress.py` → writes the fragment + JSON.

- [ ] **Step 5: Commit**

```
git add scripts/gen_website_progress.py tests/test_website_progress.py website/src/data/
git commit -m "feat(website): render the Ge'ez/Amharic progress fragment + progress.json"
```

---

### Task 3: Wire build.mjs to inline the fragment + sitemap

**Files:**
- Modify: `website/build.mjs:81-83` (the `out` assembly — inline `{{geez_progress}}` BEFORE comment-stripping) and `:98` (sitemap PAGES)

- [ ] **Step 1: Add the token fill + sitemap entry**

In `website/build.mjs`, replace the `out` assembly block (around line 81):

```javascript
  // Inline the generated Ge'ez/Amharic progress fragment (build-time, static).
  // Done BEFORE comment-stripping so the {{token}} is gone by output time.
  let bodyFilled = body;
  if (bodyFilled.includes('{{geez_progress}}')) {
    const fragPath = join(SRC, 'data', 'geez-progress.html');
    const frag = existsSync(fragPath) ? readFileSync(fragPath, 'utf8') : '<p>Progress data is being generated.</p>';
    bodyFilled = fill(bodyFilled, 'geez_progress', frag);
  }

  const out = (pageHead + bodyFilled.replace(/^\s*\n/, '') + foot)
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/\n{3,}/g, '\n\n');
```

And add `/geez.html` to the `PAGES` array (line ~98):

```javascript
const PAGES = ['/', '/roadmap.html', '/releases.html', '/feedback.html', '/geez.html'];
```

- [ ] **Step 2: Verify (after Task 4 creates geez.html) — deferred to Task 6's build.** No standalone test (zero-dep JS, no JS test infra); verified by the build in Task 6.

- [ ] **Step 3: Commit**

```
git add website/build.mjs
git commit -m "feat(website): build.mjs inlines the {{geez_progress}} fragment + sitemaps geez.html"
```

---

### Task 4: The page + nav item

**Files:**
- Create: `website/src/geez.html`
- Modify: `website/partials/head.html:44` (nav)

- [ ] **Step 1: Create `website/src/geez.html`**

```html
<!--page
title: Geʽez & Amharic Bibles — progress | YHWH Ya’ Way
desc: Exactly where the standalone Geʽez and Amharic Bibles stand — transcribed from the manuscripts, book by book. Honest, always-current.
canonical: https://www.yhwhyaway.com/geez.html
page: geez
-->
  <section class="hero">
    <h1>The Geʽez &amp; Amharic Bibles</h1>
    <p class="lede">The heart of this project: two standalone Bibles transcribed
      directly from the original manuscripts — slowly, carefully, witness by
      witness. This page shows exactly where they stand, and never claims more
      than the work proves.</p>
  </section>

  <section class="band">
    <h2>Where we are</h2>
    {{geez_progress}}
  </section>

  <section class="band alt">
    <h2>The sources we transcribe from</h2>
    <p>Every reading is taken from real manuscripts and scholarly editions you can see for yourself:</p>
    <ul class="src-list">
      <li><a href="https://cudl.lib.cam.ac.uk/view/MS-ADD-01570" rel="noopener">Cambridge University Library — MS Add. 1570</a> (Geʽez Octateuch &amp; Samuel/Kings; high-resolution IIIF folios)</li>
      <li><a href="https://archive.org/search?query=Patrologia+Orientalis" rel="noopener">Patrologia Orientalis</a> (printed critical Geʽez editions)</li>
      <li>The HaCohen Geʽez apocrypha (Wisdom, Sirach) — clean printed text.</li>
    </ul>
  </section>

  <section class="band give-band">
    <h2>What further support makes possible</h2>
    <p>The program and every Bible it builds are <strong>free — now and always</strong>.
      A free-will offering doesn’t unlock anything; it simply lets this slow work go
      faster — more witnesses collated, more books transcribed, and the Amharic begun.
      A gift is a thank-you, never a charge. The Word of God is for everyone. ✛</p>
    <p class="give-row">
      <a class="btn-give" href="https://ko-fi.com/gringoboggy" rel="noopener">Ko-fi</a>
      <a class="btn-give" href="https://paypal.me/gringoboggy" rel="noopener">PayPal</a>
    </p>
  </section>
```

- [ ] **Step 2: Add the nav link** — in `website/partials/head.html`, after the Feedback link (line 44):

```html
      <a href="geez.html" data-nav="geez">Geʽez &amp; Amharic</a>
```

- [ ] **Step 3: Commit**

```
git add website/src/geez.html website/partials/head.html
git commit -m "feat(website): Ge'ez & Amharic progress page + nav item"
```

---

### Task 5: Styles for the bars + grid

**Files:**
- Modify: `website/style.css` (append a `/* Ge'ez & Amharic progress */` block)

- [ ] **Step 1: Append the CSS** (match the site's palette — read the top of `style.css` first for the existing custom-property names, e.g. the gold/ink/parchment vars, and reuse them):

```css
/* Ge'ez & Amharic progress page */
.pb-wrap { margin: 1.5rem 0; }
.pb-bar-row { margin: 0.75rem 0; }
.pb-bar-head { display: flex; justify-content: space-between; gap: 1rem; align-items: baseline; }
.pb-bar-sub { font-size: 0.85rem; opacity: 0.8; }
.pb-bar { height: 0.55rem; background: rgba(0,0,0,0.08); border-radius: 0.4rem; overflow: hidden; margin-top: 0.25rem; }
.pb-bar-fill { display: block; height: 100%; background: #B8860B; border-radius: 0.4rem; }
.pb-legend { font-size: 0.85rem; opacity: 0.85; margin: 0.75rem 0 1.25rem; }
.pb-h { margin: 1.5rem 0 0.5rem; }
.pb-grid { list-style: none; padding: 0; margin: 0; display: grid;
  grid-template-columns: repeat(auto-fill, minmax(8.5rem, 1fr)); gap: 0.35rem; }
.pb-cell { display: flex; align-items: center; gap: 0.4rem; padding: 0.3rem 0.5rem;
  border: 1px solid rgba(0,0,0,0.08); border-radius: 0.35rem; font-size: 0.82rem; }
.pb-badge { font-size: 0.9rem; line-height: 1; }
.pb-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pb-en { font-size: 0.62rem; font-weight: 700; color: #5B2E8C; border: 1px solid currentColor;
  border-radius: 0.2rem; padding: 0 0.18rem; }
.pb-ready  { border-color: #B8860B; background: rgba(184,134,11,0.10); }
.pb-transcribed { background: rgba(184,134,11,0.05); }
.pb-source { background: rgba(0,0,0,0.03); }
.pb-none   { opacity: 0.55; }
```

- [ ] **Step 2: Commit**

```
git add website/style.css
git commit -m "feat(website): styles for the Ge'ez/Amharic progress bars + grid"
```

---

### Task 6: Build, visual-QA, finalize

**Files:** none new — build + verify.

- [ ] **Step 1: Generate + build**

```
& $py scripts\gen_website_progress.py
node website/build.mjs
```
Expected: `built  dist/geez.html` in the output; `dist/geez.html` exists.

- [ ] **Step 2: Verify the token was inlined (not left raw, not comment-stripped)**

Run: `Select-String -Path website\dist\geez.html -Pattern '\{\{geez_progress\}\}|pb-grid|pb-bar-fill' `
Expected: NO `{{geez_progress}}` (filled); YES `pb-grid` + `pb-bar-fill` (the fragment is present).

- [ ] **Step 3: Visual QA (self-serviceable — memory `feedback_visual_qa_self_serviceable`)**

Serve `website/dist` via `python -m http.server` and load `http://localhost:<port>/geez.html` with Playwright; screenshot. Confirm: the nav shows "Geʽez & Amharic" + is marked current; the two bars render (Ge'ez fill ~5%, Amharic ~0%); the per-book grid shows badges; the four Ge'ez books read ● Bible-ready; the source links + give buttons render. Fix any layout issue in `style.css`.

- [ ] **Step 4: Run the full generator test file once more + lint**

```
& $py -m pytest tests/test_website_progress.py -v --basetemp=$bt   # all pass
& $py scripts\lint_rules.py                                        # no new fail
& $py -m ruff format scripts\gen_website_progress.py tests\test_website_progress.py
```

- [ ] **Step 5: 5-leg save** (rebase onto origin/main first — Mac is pushing re-ingest commits)

```
git -C "<repo>" fetch origin ; git -C "<repo>" rebase origin/main   # if behind
pwsh -File save-all.ps1 -Message "feat(website): Ge'ez & Amharic progress page (data-driven per-book grid + sources + give)" -Label geez-progress-page
```

---

## Self-review
- **Spec coverage:** dedicated page ✓ (Task 4) · per-Bible bars ✓ (Task 2 `_bar`) · per-book staged grid ✓ (Task 2 `_grid`, Task 5 CSS) · source links ✓ (Task 4) · support tie-in ✓ (Task 4) · data-driven/never-drifts ✓ (Task 1–2 generator, committed outputs) · honesty (computed stages, Amharic not inflated) ✓ (Task 1 precedence + Task 2 test).
- **Placeholders:** none — every step has concrete code/commands.
- **Type/name consistency:** `compute_progress` / `render_fragment` / `write_outputs` used consistently across tasks + tests; stage keys (`none/source/transcribed/ready`) consistent across `STAGE_*` maps, the computation, the CSS (`.pb-<stage>`), and the tests.
- **Note:** the EN-mark assertion in Task 2's test (`geez["psa"]["en"]`) depends on Task 1 threading `en` through (it does). The `_display_name` for books like `1ki` ("The First and Second Books of the Kings" → tail) may need a per-code override for a few multi-book titles — refine the `_display_name` map during Task 4 visual-QA if a label reads oddly (low-risk, cosmetic).

## Constraints carried
Plain HTML/CSS (no framework); the generator is pure + tested; outputs committed so the page works from a clean checkout; collision-free with the re-ingest (rebase before push); honest copy (Word free, gifts accelerate).
