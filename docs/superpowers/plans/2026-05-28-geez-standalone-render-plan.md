# Ge'ez Standalone-Bible Render Path (Phase C) — Implementation Plan
**Status:** shipped — standalone render path (Phase C); 4-book proof EPUB

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Read the companion spec `docs/superpowers/specs/2026-05-27-geez-own-versification-design.md` (esp. §3.4–§3.5 + §9 "Phase C — resolved decisions") FIRST, then the bootstrap triad (RULES → SESSION_STATE → the live master roadmap PLAN named in RULES §0).

**Goal:** Build a dedicated standalone-Bible render path that turns the own-versification Ge'ez data (the 10 base-structured Kings/Samuel collations + own-versified Psalms) into a valid standalone Ge'ez Bible EPUB whose verse popups carry the KJV cross-reference + the manuscript apparatus — while the 9 KJV editions stay byte-stable.

**Architecture:** A per-book `VERSIFICATION` store attribute (`own`/`canonical`) is read by `translations.py`. A pure store-builder converts each `<ref>_collation_v2.json` into a `geez-tewahedo/{book}.py` (Ge'ez verses at their OWN numbering) + a `{book}_apparatus.json` sidecar (xref + variants). A NEW `scripts/build_standalone.py` GENERATES the Ge'ez body XHTML from that store (there is no verse→HTML renderer today — fully greenfield), assembles a fresh OPF manifest+spine over a copied `epub_working/` skeleton, reuses the shared `build_epub.build`/`patch_opf`/`matter_pages` machinery, and `build_one` gains a 3-line guard that delegates `standalone: true` editions to it (a no-op for the 9 KJV editions, so their output is provably unchanged).

**Tech Stack:** Python 3.14, pytest, stdlib only (no Flask/lxml — OPF is patched by regex, mirroring the existing `patch_opf`). Reuses `scripts/build_epub.py` (`build`), `scripts/build_edition.py` (`patch_opf`, `apply_edition_cover`), `scripts/matter_pages.py`, `scripts/core/translations.py`. Windows/PowerShell.

**Environment invariants (this box):**
- python = `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe` (bare `python`/`python3` is a broken Win-Store stub).
- Always set `$env:PYTHONUTF8="1"` before any test/run (or 72 tests fail with cp1252 errors).
- Commit via `save.ps1` through **PowerShell ONLY** (never the Bash tool). The pre-commit hook runs `ruff format --check .` + `lint_rules.py`; **`python -m ruff format` every generated `content/translations/...` file before saving** or the hook blocks the commit.
- No git remote (local commits only). Back up via `git bundle create <E:/F: path> --all` (every 3rd commit + each `/clear`).
- epubcheck: Java 8 is on PATH; ALWAYS pass `--jar <bundled jar>` (auto-discovery resolves a broken wrapper). See memory `reference_epubcheck`.

---

## Execution discipline (ALL tasks)
- **TDD:** failing test → run-and-confirm-FAIL → minimal implementation → run-and-confirm-PASS → commit. One logical change per commit.
- **Byte-stable invariant (cardinal):** the 9 KJV editions' output must not change. The dispatch guard (Task C3d) fires ONLY for `edition.get("standalone")`, so the 9 never enter new code. Prove it: the C3d spy test + a real `catholic-study` build (C4) at `epubcheck 0/0`.
- **Never-single-thread (RULES §2.5):** keep a background lane running during execution — the next CAM hi-res pre-pull (`scripts/acquire_cudl_master.py`, disk-only, RAM-gated) or a Phase-D source check. Don't idle a single lane. Respect the concurrency cap (heavy >100k MAX 1 / medium 30–100k MAX 2 / light <30k MAX 4).
- **Honesty gates:** xref confidence (`anchored`/`interpolated`) is shown verbatim; the apparatus shows the reviewed variants; **English is explicitly ABSENT** in this phase and **never faked from KJV** (the EN back-translation is the next lane). No fabrication.
- **Immutability:** never touch the witness JSONs or the 4 Samuel `*_collation.json` goldens. Task C2 reads only the `*_collation_v2.json` files.

## File structure (created / modified)
- **Modify** `scripts/core/translations.py` — add `_load_book_attr_from_text()` + `versification_of()` (C1).
- **Modify** `content/translations/geez-tewahedo/psa.py` — add `VERSIFICATION = "own"` (C1; formalizes the docstring that already states it).
- **Create** `scripts/core/standalone_store.py` — pure store-generation from collations + a `main()` driver (C2).
- **Create** `content/translations/geez-tewahedo/{1ki,1sa,2sa}.py` + `{1ki,1sa,2sa,psa}_apparatus.json` — generated own-vers store + sidecars (C2 + C4 Psalms xref).
- **Create** `scripts/build_standalone.py` — body XHTML generator + OPF/nav assembly + `build_standalone()` orchestrator (C3a–C3c).
- **Modify** `scripts/build_edition.py` — 3-line `standalone` guard at the top of `build_one` (C3d).
- **Create** `tests/test_build_standalone.py` — all Phase-C tests (C1–C4).

---

## TASK C1 — per-book `versification` attribute in the translation store

**Files:**
- Modify: `scripts/core/translations.py` (add after `load_book_verses_from_text`, ~line 76, and a public fn after `translation_meta`, ~line 188)
- Modify: `content/translations/geez-tewahedo/psa.py` (add module attribute)
- Test: `tests/test_build_standalone.py`

- [ ] **Step 1 — write the failing test.** Create `tests/test_build_standalone.py`:

```python
import json
from pathlib import Path

import pytest

from scripts.core import translations as tx

REPO = Path(__file__).resolve().parent.parent
COLL = REPO / "content" / "manuscript" / "kings" / "collation"


class TestVersificationAttr:
    def test_parser_reads_own(self):
        assert tx._load_book_attr_from_text('VERSIFICATION = "own"\nVERSES = []', "VERSIFICATION") == "own"

    def test_parser_none_when_absent(self):
        assert tx._load_book_attr_from_text("VERSES = []", "VERSIFICATION") is None

    def test_parser_ignores_non_string(self):
        assert tx._load_book_attr_from_text("VERSIFICATION = 3\nVERSES = []", "VERSIFICATION") is None

    def test_versification_of_defaults_canonical(self):
        # kjv/gen has no VERSIFICATION attr → canonical (back-compat for all 9 editions)
        assert tx.versification_of("kjv", "gen") == "canonical"

    def test_versification_of_missing_book_is_canonical(self):
        assert tx.versification_of("kjv", "zzz") == "canonical"

    def test_psalms_is_own_versified(self):
        # set by C1 step 5 (psa.py already documents own/Rahlfs numbering)
        assert tx.versification_of("geez-tewahedo", "psa") == "own"
```

- [ ] **Step 2 — run, confirm FAIL.**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_build_standalone.py::TestVersificationAttr -v`
Expected: FAIL — `AttributeError: module 'scripts.core.translations' has no attribute '_load_book_attr_from_text'`.

- [ ] **Step 3 — implement in `scripts/core/translations.py`.** Add after `load_book_verses_from_text` (the function ends ~line 76):

```python
def _load_book_attr_from_text(text: str, attr: str) -> str | None:
    """Parse a module-level string assignment (e.g. ``VERSIFICATION = "own"``)
    and return its value. ``None`` if absent, on syntax error, or if the value
    is not a string. Uses ``ast.literal_eval`` — never executes module code.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == attr:
                    try:
                        val = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return None
                    return val if isinstance(val, str) else None
    return None
```

Add after `translation_meta` (~line 188):

```python
def versification_of(translation: str, book_code: str) -> str:
    """Return the book's versification scheme: ``"own"`` or ``"canonical"``.

    Defaults to ``"canonical"`` when the per-book ``VERSIFICATION`` attribute
    is absent, so every existing translation/book (and the 9 KJV editions)
    is unchanged. ``"own"`` marks a store whose ``(chapter, verse)`` keys are
    the source's own numbering (e.g. the Ge'ez/LXX recension), NOT KJV-renumbered.
    """
    path = _book_path(translation, book_code)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return "canonical"
    val = _load_book_attr_from_text(text, "VERSIFICATION")
    return val if val in ("own", "canonical") else "canonical"
```

- [ ] **Step 4 — formalize Psalms.** In `content/translations/geez-tewahedo/psa.py`, add `VERSIFICATION = "own"` immediately after the `INGEST_PHASE = "τ.6.x.2.i"` line (before `VERSES = [`). (Its docstring already states "Source numbering is authoritative — NOT renumbered against the floor.")

- [ ] **Step 5 — run, confirm PASS.**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_build_standalone.py::TestVersificationAttr -v`
Expected: PASS (6 tests).

- [ ] **Step 6 — commit.** `pwsh -File save.ps1 -Message "Phase C1: per-book VERSIFICATION attr (own/canonical) + psa formalized own"`

---

## TASK C2 — generate the own-versification Kings/Samuel store from the v2 collations

**Files:**
- Create: `scripts/core/standalone_store.py`
- Create (by running the driver): `content/translations/geez-tewahedo/{1ki,1sa,2sa}.py` + `{1ki,1sa,2sa}_apparatus.json`
- Test: `tests/test_build_standalone.py`

- [ ] **Step 1 — write the failing test.** Append to `tests/test_build_standalone.py`:

```python
from scripts.core import standalone_store as ss


class TestStandaloneStore:
    def test_collation_to_entries_uses_own_numbering(self):
        coll = json.loads((COLL / "1ki6_collation_v2.json").read_text(encoding="utf-8"))
        verses, appmap = ss.collation_to_store_entries(coll)
        assert len(verses) == 33                         # CAM's own sense-units, NOT 38 KJV
        assert verses[0] == (6, 1, coll["primary_verses"][0]["geez_text"])
        assert appmap["1"]["kjv"] == [["1ki", 6, 1]]     # v1 anchored to KJV 6:1
        assert appmap["1"]["confidence"] == "anchored"
        assert appmap["1"]["apparatus"]                   # the GG-vs-CAM variant rows

    def test_build_book_store_writes_module_and_sidecar(self, tmp_path):
        paths = [COLL / f"1ki{n}_collation_v2.json" for n in range(1, 7)]
        res = ss.build_book_store("1ki", paths, tmp_path)
        assert res["book"] == "1ki" and res["chapters"] == 6 and res["verses"] > 0
        # module round-trips through the real translation loader
        text = (tmp_path / "1ki.py").read_text(encoding="utf-8")
        verses = tx.load_book_verses_from_text(text)
        assert verses and all(len(t) == 3 for t in verses)
        assert tx._load_book_attr_from_text(text, "VERSIFICATION") == "own"
        # sidecar keyed by chapter then geez_v
        am = json.loads((tmp_path / "1ki_apparatus.json").read_text(encoding="utf-8"))
        assert "6" in am and "1" in am["6"] and am["6"]["1"]["kjv"] == [["1ki", 6, 1]]
```

- [ ] **Step 2 — run, confirm FAIL.**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_build_standalone.py::TestStandaloneStore -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.core.standalone_store'`.

- [ ] **Step 3 — implement `scripts/core/standalone_store.py`.**

```python
"""scripts.core.standalone_store — Phase C2.

Generate an OWN-versification translation store from the base-structured
manuscript collations (``content/manuscript/<track>/collation/<ref>_collation_v2.json``).
Each base witness sense-unit becomes a store verse at its OWN ``(chapter, geez_v)``
coordinate (NOT KJV-renumbered); the KJV cross-reference + the manuscript apparatus
go to a ``<book>_apparatus.json`` sidecar for the standalone render path.

Pure data transform — reads collations only; never touches the witnesses or the
4 Samuel ``*_collation.json`` goldens.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
GEEZ_STORE = REPO / "content" / "translations" / "geez-tewahedo"


def collation_to_store_entries(
    collation: dict,
) -> tuple[list[tuple[int, int, str]], dict]:
    """Return ``(verses, apparatus_map)`` for one base-structured collation.

    - ``verses``: ``[(chapter, geez_v, geez_text), …]`` at the base witness's
      own numbering.
    - ``apparatus_map``: ``{str(geez_v): {"kjv": [[bk,ch,v],…], "confidence": str|None,
      "apparatus": [{base, other, class}, …]}}``.
    """
    ch = collation["chapter"]
    xref = collation.get("kjv_xref", {})
    verses: list[tuple[int, int, str]] = []
    appmap: dict[str, dict] = {}
    for pv in collation["primary_verses"]:
        gv = pv["geez_v"]
        verses.append((ch, gv, pv["geez_text"]))
        x = xref.get(str(gv), {})
        appmap[str(gv)] = {
            "kjv": x.get("kjv", []),
            "confidence": x.get("confidence"),
            "apparatus": pv.get("apparatus", []),
        }
    return verses, appmap


def _render_book_module(book: str, verses: list[tuple[int, int, str]]) -> str:
    out = [
        f'"""Translation: geez-tewahedo · Book: {book}',
        "",
        "Own-versification store generated from the base-structured manuscript",
        "collations (Phase C2). Verse coordinates are the base witness's OWN",
        "sense-unit numbering (NOT KJV-renumbered). KJV cross-refs + the",
        f"manuscript apparatus live in {book}_apparatus.json.",
        '"""',
        "",
        'TRANSLATION = "geez-tewahedo"',
        f'BOOK = "{book}"',
        'VERSIFICATION = "own"',
        "VERSES = [",
    ]
    for c, v, t in verses:
        esc = t.replace("\\", "\\\\").replace('"', '\\"')
        out.append(f'    ({c}, {v}, "{esc}"),')
    out.append("]")
    return "\n".join(out) + "\n"


def build_book_store(book: str, collation_paths: list[Path], out_dir: Path) -> dict:
    """Aggregate a book's chapter collations → ``<book>.py`` + ``<book>_apparatus.json``
    in ``out_dir``. Returns a stats dict."""
    all_verses: list[tuple[int, int, str]] = []
    appmap: dict[str, dict] = {}  # {str(chapter): {str(geez_v): {...}}}
    for p in collation_paths:
        coll = json.loads(p.read_text(encoding="utf-8"))
        verses, am = collation_to_store_entries(coll)
        all_verses.extend(verses)
        appmap[str(coll["chapter"])] = am
    all_verses.sort(key=lambda t: (t[0], t[1]))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{book}.py").write_text(_render_book_module(book, all_verses), encoding="utf-8")
    (out_dir / f"{book}_apparatus.json").write_text(
        json.dumps(appmap, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"book": book, "verses": len(all_verses), "chapters": len(appmap)}


# Maps the 10 done chapters to their books. Kings collations live under
# content/manuscript/kings/collation; Samuel under .../samuel/collation.
_BOOK_CHAPTERS = {
    "1ki": ("kings", [1, 2, 3, 4, 5, 6]),
    "1sa": ("samuel", [1, 3, 17]),
    "2sa": ("samuel", [11]),
}


def main() -> int:
    man = REPO / "content" / "manuscript"
    for book, (track, chapters) in _BOOK_CHAPTERS.items():
        paths = [man / track / "collation" / f"{book}{c}_collation_v2.json" for c in chapters]
        missing = [p for p in paths if not p.is_file()]
        if missing:
            print(f"SKIP {book}: missing {[p.name for p in missing]}")
            continue
        res = build_book_store(book, paths, GEEZ_STORE)
        print(f"WROTE {book}: {res['verses']} verses / {res['chapters']} chapters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4 — run, confirm PASS.**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_build_standalone.py::TestStandaloneStore -v`
Expected: PASS (2 tests).

- [ ] **Step 5 — run the driver to generate the real store files.**

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m scripts.core.standalone_store`
Expected: `WROTE 1ki: … / 6 chapters`, `WROTE 1sa: … / 3 chapters`, `WROTE 2sa: … / 1 chapters`.

- [ ] **Step 6 — ruff-format the generated stores (REQUIRED before commit).**

Run: `& "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m ruff format content/translations/geez-tewahedo/1ki.py content/translations/geez-tewahedo/1sa.py content/translations/geez-tewahedo/2sa.py`
Then sanity-load: `& "...python.exe" -c "from scripts.core import translations as t; print(t.versification_of('geez-tewahedo','1ki'), len(t.get_chapter('geez-tewahedo','1ki',6)))"`
Expected: `own 33`.

- [ ] **Step 7 — commit.** `pwsh -File save.ps1 -Message "Phase C2: generate own-vers Kings/Samuel store + apparatus sidecars from v2 collations"`

---

## TASK C3a — body XHTML generator (greenfield; no verse→HTML renderer exists)

**Files:**
- Create: `scripts/build_standalone.py`
- Test: `tests/test_build_standalone.py`

The target element shape (confirmed from `epub_working/index_split_001.html`): a chapter is `<a id="ch-…" class="ch-anchor">` + `<p class="ch-heading">…</p>` then `<p class="verse-p"><a class="vn-link" id="v-{bk}-{ch}-{vs}" href="#vnote-{bk}-{ch}-{vs}" epub:type="noteref" title="…"><span class="vn">{n}</span></a> TEXT</p>`, and popups in `<section class="verse-refs-section" epub:type="footnotes" hidden=""><aside class="vnote" id="vnote-…" epub:type="footnote">…</aside></section>`.

- [ ] **Step 1 — write the failing test.** Append:

```python
from scripts import build_standalone as bs


class TestBodyRender:
    def _sample(self):
        verses = [(1, "ወእምዝ ፡ በ፬፻ ፡ ወ፹ ፡ ዓመት"), (2, "ወቤት ፡ ዘሐነፀ ፡ ሰሎሞን")]
        appmap = {
            "1": {"kjv": [["1ki", 6, 1]], "confidence": "anchored",
                  "apparatus": [{"base": "ወእምዝ", "other": "ወውእቱ", "class": "disagree"}]},
            "2": {"kjv": [["1ki", 6, 2]], "confidence": "interpolated", "apparatus": []},
        }
        return bs.render_chapter_body("1ki", 6, verses, appmap)

    def test_verse_uses_own_number_and_vnlink(self):
        html = self._sample()
        assert '<a class="vn-link" id="v-1ki-6-1" href="#vnote-1ki-6-1"' in html
        assert '<span class="vn">1</span>' in html
        assert "ወእምዝ ፡ በ፬፻ ፡ ወ፹ ፡ ዓመት" in html

    def test_popup_carries_kjv_xref_with_confidence(self):
        html = self._sample()
        assert '<aside class="vnote" id="vnote-1ki-6-1"' in html
        assert "1 Kings 6:1" in html
        assert "anchored" in html
        assert "interpolated" in html  # v2

    def test_popup_carries_apparatus_variants(self):
        html = self._sample()
        assert "ወውእቱ" in html              # the GG variant for v1
        assert "vnote-text" not in html     # NO English faked in this phase
```

- [ ] **Step 2 — run, confirm FAIL.**

Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m pytest tests/test_build_standalone.py::TestBodyRender -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.build_standalone'`.

- [ ] **Step 3 — implement the renderers in `scripts/build_standalone.py`.**

```python
"""scripts.build_standalone — Phase C3.

The standalone-Bible render path. Generates the Ge'ez body XHTML from the
own-versification store (there is no verse→HTML renderer in the rest of the
project — the 9 KJV editions inject into the pre-baked epub_working/ tree),
assembles a fresh OPF over a copied epub_working/ skeleton, and reuses the
shared build_epub.build / patch_opf / matter_pages machinery.

Popups carry the KJV cross-reference + the manuscript apparatus. English
back-translation is the NEXT lane and is intentionally absent here (never
faked from KJV).
"""

from __future__ import annotations

import html as _html
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GEEZ_STORE = REPO / "content" / "translations" / "geez-tewahedo"

# Display titles for popup headers. Extend as the standalone book set grows.
_BOOK_TITLES = {
    "1ki": "1 Kings", "2ki": "2 Kings", "1sa": "1 Samuel", "2sa": "2 Samuel",
    "psa": "Psalms",
}


def _esc(s: str) -> str:
    return _html.escape(s, quote=True)


def _fmt_kjv_ref(ref: list) -> str:
    bk, ch, vs = ref
    return f"{_BOOK_TITLES.get(bk, bk)} {ch}:{vs}"


def _render_vnote(book: str, chapter: int, gv: int, app: dict) -> str:
    nid = f"vnote-{book}-{chapter}-{gv}"
    title = f"{_BOOK_TITLES.get(book, book)} {chapter}:{gv}"
    parts = [
        f'<aside class="vnote" id="{nid}" epub:type="footnote">',
        f"<p><strong>{_esc(title)}</strong></p>",
    ]
    kjv = app.get("kjv") or []
    if kjv:
        refs = "; ".join(_fmt_kjv_ref(r) for r in kjv)
        conf = app.get("confidence") or ""
        conf_html = f' <span class="xref-confidence">({_esc(conf)})</span>' if conf else ""
        parts.append(f'<p class="vnote-xref">KJV cross-reference: {_esc(refs)}{conf_html}</p>')
    variants = [a for a in (app.get("apparatus") or []) if a.get("class") in ("disagree", "insertion", "lacuna")]
    if variants:
        items = []
        for a in variants:
            base = _esc(a.get("base") or "—")
            other = _esc(a.get("other") or "—")
            cls = _esc(a.get("class") or "")
            items.append(f'<li><span class="app-base">{base}</span> / '
                         f'<span class="app-other">{other}</span> '
                         f'<span class="app-class">[{cls}]</span></li>')
        parts.append('<p class="vnote-apparatus">Manuscript variants (base / other witness):</p>')
        parts.append('<ul class="apparatus-list">' + "".join(items) + "</ul>")
    parts.append("</aside>")
    return "\n".join(parts)


def render_chapter_body(book: str, chapter: int, verses: list[tuple[int, str]], appmap: dict) -> str:
    """``verses``: ``[(geez_v, geez_text), …]``; ``appmap``: ``{str(geez_v): {...}}``.
    Returns the chapter body fragment (verse-p paragraphs + the hidden footnotes section)."""
    body = [
        f'<a id="ch-{book}-c{chapter}" class="ch-anchor"></a>',
        f'<p class="ch-heading"><span class="section-heading"><span class="bold-num">{chapter}</span></span></p>',
    ]
    asides = []
    for gv, text in verses:
        vid = f"v-{book}-{chapter}-{gv}"
        nid = f"vnote-{book}-{chapter}-{gv}"
        title = f"{_BOOK_TITLES.get(book, book)} {chapter}:{gv}"
        body.append(
            f'<p class="verse-p"><a class="vn-link" id="{vid}" href="#{nid}" '
            f'epub:type="noteref" title="{_esc(title)}"><span class="vn">{gv}</span></a> '
            f"{_esc(text)}</p>"
        )
        asides.append(_render_vnote(book, chapter, gv, appmap.get(str(gv), {})))
    body.append('<section class="verse-refs-section" epub:type="footnotes" hidden="">')
    body.extend(asides)
    body.append("</section>")
    return "\n".join(body)
```

- [ ] **Step 4 — run, confirm PASS.**

Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m pytest tests/test_build_standalone.py::TestBodyRender -v`
Expected: PASS (3 tests).

- [ ] **Step 5 — commit.** `pwsh -File save.ps1 -Message "Phase C3a: standalone Ge'ez body XHTML generator (verse-p + vnote xref/apparatus)"`

---

## TASK C3b — XHTML document wrapper + OPF/nav assembly (recon-first)

**Files:**
- Modify: `scripts/build_standalone.py`
- Test: `tests/test_build_standalone.py`

> **Recon step (do this FIRST — the exact skeleton resource names are needed for correct code):** read these real files and record their structure into this task before implementing:
> - `epub_working/META-INF/container.xml` → the OPF path (the `full-path` attribute).
> - that OPF (e.g. `epub_working/OEBPS/content.opf`) → the `<manifest>` item ids/hrefs for the **CSS**, **nav** (`properties="nav"`), **cover-image**, and **fonts**; and the `<spine>` shape. These non-body resources are RETAINED; the body `index_split_*.html` items are REPLACED.
> - the `<head>` of one body file (`epub_working/index_split_001.html`) → the exact XHTML doctype, `<html>` namespaces (`xmlns`, `xmlns:epub`), and the `<link rel="stylesheet" href="…">` — copy this verbatim into `_XHTML_HEAD` below.

- [ ] **Step 1 — write the failing test.** Append:

```python
class TestXhtmlDocAndOpf:
    def test_wrap_xhtml_doc_is_wellformed(self):
        import xml.dom.minidom as md
        frag = bs.render_chapter_body("1ki", 6, [(1, "ወእምዝ")], {"1": {"kjv": [], "apparatus": []}})
        doc = bs.wrap_xhtml_doc("1 Kings 6", frag)
        md.parseString(doc.encode("utf-8"))  # raises if not well-formed XML
        assert "xmlns:epub" in doc and "verse-p" in doc

    def test_build_spine_manifest_lists_generated_files(self):
        items = [("geez_1ki_6", "geez_1ki_6.xhtml")]
        manifest, spine = bs.build_manifest_and_spine(items)
        assert 'id="geez_1ki_6"' in manifest and 'href="geez_1ki_6.xhtml"' in manifest
        assert 'media-type="application/xhtml+xml"' in manifest
        assert 'idref="geez_1ki_6"' in spine
```

- [ ] **Step 2 — run, confirm FAIL.**

Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m pytest tests/test_build_standalone.py::TestXhtmlDocAndOpf -v`
Expected: FAIL — `AttributeError: ... has no attribute 'wrap_xhtml_doc'`.

- [ ] **Step 3 — implement in `scripts/build_standalone.py`.** Paste the real doctype/namespaces/CSS link captured in the recon step into `_XHTML_HEAD` (the values below match the observed `epub_working` format; CONFIRM the CSS href against the recon).

```python
# Captured from epub_working/index_split_001.html <head> in the C3b recon.
# CONFIRM the stylesheet href matches the skeleton OPF manifest.
_XHTML_HEAD = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<!DOCTYPE html>\n'
    '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" '
    'lang="gez" xml:lang="gez">\n'
    "<head>\n"
    '<meta charset="utf-8"/>\n'
    "<title>{title}</title>\n"
    '<link rel="stylesheet" type="text/css" href="stylesheet.css"/>\n'
    "</head>\n"
    "<body>\n"
)
_XHTML_TAIL = "\n</body>\n</html>\n"


def wrap_xhtml_doc(title: str, body_fragment: str) -> str:
    """Wrap a chapter body fragment into a complete, well-formed XHTML document."""
    return _XHTML_HEAD.format(title=_esc(title)) + body_fragment + _XHTML_TAIL


def build_manifest_and_spine(items: list[tuple[str, str]]) -> tuple[str, str]:
    """``items``: ``[(item_id, href), …]`` for the generated chapter files (spine order).
    Returns ``(manifest_items_xml, spine_itemrefs_xml)`` to splice into the skeleton OPF."""
    manifest = "\n".join(
        f'<item id="{i}" href="{h}" media-type="application/xhtml+xml"/>' for i, h in items
    )
    spine = "\n".join(f'<itemref idref="{i}"/>' for i, _ in items)
    return manifest, spine


def patch_standalone_opf(opf_text: str, chapter_items: list[tuple[str, str]]) -> str:
    """Replace the body portion of the skeleton manifest+spine with the generated
    chapter files, RETAINING non-body resources (css/nav/cover/fonts). Strategy:
    drop every existing ``index_split_*`` manifest item + its spine itemref, then
    inject the generated items. Mirrors the regex approach of build_edition.patch_opf
    (stdlib only — no lxml)."""
    import re

    # 1. drop existing body items (manifest) + their spine itemrefs
    opf_text = re.sub(r'\s*<item\b[^>]*href="[^"]*index_split_[^"]*"[^>]*/>', "", opf_text)
    opf_text = re.sub(r'\s*<itemref\b[^>]*idref="[^"]*split[^"]*"[^>]*/>', "", opf_text)

    manifest_items, spine_items = build_manifest_and_spine(chapter_items)
    # 2. inject generated manifest items just before </manifest>
    opf_text = opf_text.replace("</manifest>", manifest_items + "\n</manifest>", 1)
    # 3. inject generated spine itemrefs just before </spine>
    opf_text = opf_text.replace("</spine>", spine_items + "\n</spine>", 1)
    return opf_text
```

> Note for the implementer: the `index_split` / `split` regexes assume the skeleton's body manifest ids/hrefs contain `index_split`. Verify against the recon'd OPF; if the ids differ, adjust the two `re.sub` patterns to match the real body-item naming. The non-body items (css/nav/cover/fonts) must NOT match these patterns — confirm by diffing the manifest before/after on a copied skeleton.

- [ ] **Step 4 — run, confirm PASS.**

Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m pytest tests/test_build_standalone.py::TestXhtmlDocAndOpf -v`
Expected: PASS (2 tests).

- [ ] **Step 5 — commit.** `pwsh -File save.ps1 -Message "Phase C3b: standalone XHTML doc wrapper + OPF manifest/spine assembly"`

---

## TASK C3c — `build_standalone()` orchestrator

**Files:**
- Modify: `scripts/build_standalone.py`
- Test: `tests/test_build_standalone.py`

- [ ] **Step 1 — write the failing test.** Append (uses the real store from C2; writes to tmp):

```python
class TestBuildStandalone:
    def test_build_standalone_produces_epub(self, tmp_path):
        out = bs.build_standalone("standalone-geez", tmp_path, "v28a")
        assert out["status"] == "ok"
        epub = Path(out["output_path"])
        assert epub.is_file() and epub.suffix == ".epub" and epub.stat().st_size > 10_000
        # the EPUB is a zip whose first entry is an uncompressed mimetype
        import zipfile
        with zipfile.ZipFile(epub) as z:
            names = z.namelist()
            assert names[0] == "mimetype"
            assert any("geez_1ki_6" in n for n in names)  # a generated body file is packaged
```

- [ ] **Step 2 — run, confirm FAIL.**

Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m pytest tests/test_build_standalone.py::TestBuildStandalone -v`
Expected: FAIL — `AttributeError: ... has no attribute 'build_standalone'`.

- [ ] **Step 3 — implement the orchestrator in `scripts/build_standalone.py`.** (Reuses `build_epub.build`, `build_edition.patch_opf`, `matter_pages`; reads the real skeleton paths confirmed in C3b recon. The book set is the own-vers proof scope.)

```python
import shutil
import tempfile
import time

EPUB_DIR = REPO / "epub_working"

# Proof-EPUB book set: own-versification content only (Phase C scope).
# Psalms is added by C4 (after its xref sidecar exists).
_STANDALONE_BOOKS = ["1ki", "1sa", "2sa"]


def _chapters_for(book: str) -> list[int]:
    """All chapters present in the own-vers store for one book, ascending."""
    from scripts.core import translations as tx

    verses = tx._load_book(book="", translation="geez-tewahedo") if False else None  # see below
    chs = sorted({c for (c, _v, _t) in (tx._load_book("geez-tewahedo", book) or [])})
    return chs


def build_standalone(edition_id: str, output_dir: Path, version: str) -> dict:
    """Render a standalone Ge'ez Bible EPUB from the own-versification store.
    Returns ``{"status": "ok", "output_path": str, "books": int, "chapters": int}``
    or ``{"status": "error", "message": str}``."""
    from scripts import build_edition as be
    from scripts import build_epub
    from scripts.core import config, translations as tx

    eds = config.editions_by_id()
    edition = eds.get(edition_id)
    if edition is None or not edition.get("standalone"):
        return {"status": "error", "message": f"not a standalone edition: {edition_id}"}

    books = [b for b in _STANDALONE_BOOKS if tx.has_book("geez-tewahedo", b)]
    if not books:
        return {"status": "error", "message": "no own-versification books found in geez-tewahedo"}

    tmp = Path(tempfile.mkdtemp(prefix="standalone_"))
    try:
        # 1. copy the epub_working skeleton (CSS/fonts/nav/cover/OPF/container)
        shutil.copytree(EPUB_DIR, tmp, dirs_exist_ok=True)
        oebps = tmp  # epub_working files live at the root of the working tree

        # 2. remove the KJV body split files (the standalone supplies its own body)
        for f in oebps.glob("index_split_*.html"):
            f.unlink()

        # 3. generate the Ge'ez body files
        chapter_items: list[tuple[int, int, str, str]] = []  # (book_idx, ch, item_id, href)
        for bi, book in enumerate(books):
            chs = sorted({c for (c, _v, _t) in (tx._load_book("geez-tewahedo", book) or [])})
            appmap_path = GEEZ_STORE / f"{book}_apparatus.json"
            appmap_all = json.loads(appmap_path.read_text(encoding="utf-8")) if appmap_path.is_file() else {}
            for ch in chs:
                verses = tx.get_chapter("geez-tewahedo", book, ch)  # [(v, text)]
                frag = render_chapter_body(book, ch, verses, appmap_all.get(str(ch), {}))
                title = f"{_BOOK_TITLES.get(book, book)} {ch}"
                href = f"geez_{book}_{ch}.xhtml"
                (oebps / href).write_text(wrap_xhtml_doc(title, frag), encoding="utf-8")
                chapter_items.append((bi, ch, f"geez_{book}_{ch}", href))

        spine_items = [(item_id, href) for (_bi, _ch, item_id, href) in chapter_items]

        # 4. patch the OPF: metadata (reuse build_edition.patch_opf) + body manifest/spine
        opf_rel = _find_opf(tmp)
        opf_path = tmp / opf_rel
        opf_text = opf_path.read_text(encoding="utf-8")
        opf_text = be.patch_opf(opf_text, edition, version)
        opf_text = patch_standalone_opf(opf_text, spine_items)
        opf_path.write_text(opf_text, encoding="utf-8")

        # 5. rewrite the nav/toc to the standalone book set
        _rewrite_nav(tmp, books, chapter_items)

        # 6. cover: standalone-geez sets cover_image="" → keep the master (back-compat)
        be.apply_edition_cover(edition, tmp)

        # 7. package
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_path = output_dir / f"Geez_Standalone_{edition_id}_{version}_{ts}.epub"
        output_dir.mkdir(parents=True, exist_ok=True)
        build_epub.build(tmp, out_path, bump=True)
        return {
            "status": "ok",
            "output_path": str(out_path),
            "books": len(books),
            "chapters": len(chapter_items),
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _find_opf(root: Path) -> str:
    """Read META-INF/container.xml → the OPF's full-path (relative to root)."""
    import re

    container = (root / "META-INF" / "container.xml").read_text(encoding="utf-8")
    m = re.search(r'full-path="([^"]+)"', container)
    if not m:
        raise ValueError("no rootfile full-path in container.xml")
    return m.group(1)


def _rewrite_nav(root: Path, books: list[str], chapter_items: list[tuple[int, int, str, str]]) -> None:
    """Replace the nav/toc ordered list with the standalone book→chapter links.
    Reuses the skeleton nav doc; rewrites only the <ol> under epub:type='toc'."""
    import re

    nav_rel = _find_nav(root)
    nav_path = root / nav_rel
    nav_text = nav_path.read_text(encoding="utf-8")
    lis = []
    for _bi, ch, item_id, href in chapter_items:
        book = item_id.split("_")[1]
        lis.append(f'<li><a href="{href}">{_BOOK_TITLES.get(book, book)} {ch}</a></li>')
    new_ol = '<ol>\n' + "\n".join(lis) + "\n</ol>"
    nav_text = re.sub(r"<ol>.*?</ol>", new_ol, nav_text, count=1, flags=re.DOTALL)
    nav_path.write_text(nav_text, encoding="utf-8")


def _find_nav(root: Path) -> str:
    """Locate the nav document via the OPF manifest properties='nav' item."""
    import re

    opf_rel = _find_opf(root)
    opf_dir = (root / opf_rel).parent
    opf_text = (root / opf_rel).read_text(encoding="utf-8")
    m = re.search(r'<item\b[^>]*properties="[^"]*\bnav\b[^"]*"[^>]*href="([^"]+)"', opf_text)
    if not m:
        m = re.search(r'<item\b[^>]*href="([^"]+)"[^>]*properties="[^"]*\bnav\b[^"]*"', opf_text)
    if not m:
        raise ValueError("no nav item in OPF manifest")
    return str((opf_dir / m.group(1)).relative_to(root))
```

> Implementer notes (grounded in the C3b recon + the Explore findings):
> - `epub_working` files live at the **tree root** (the body files are `index_split_*.html` at the top level, per the Explore report's path `epub_working/index_split_001.html`). If the recon shows an `OEBPS/` subdir instead, set `oebps = tmp / "OEBPS"` and adjust the OPF/href relativity accordingly.
> - `config.editions_by_id()`, `build_edition.patch_opf`, `build_edition.apply_edition_cover`, and `build_epub.build(epub_dir, out_path, *, bump)` are the real signatures (confirmed). If `apply_edition_cover` has a different name in the recon, use the cover-swap function called at `build_edition.py:2828`.
> - Delete the dead `_chapters_for` stub above (it was a scratch helper); the inline `sorted({...})` is the real path.

- [ ] **Step 4 — run, confirm PASS.**

Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m pytest tests/test_build_standalone.py::TestBuildStandalone -v`
Expected: PASS. If the OPF/nav regex misses a real resource, fix the pattern (per the C3b note) and re-run.

- [ ] **Step 5 — commit.** `pwsh -File save.ps1 -Message "Phase C3c: build_standalone() orchestrator (skeleton copy + body gen + OPF/nav + package)"`

---

## TASK C3d — dispatch guard in `build_one` (byte-stable for the 9 KJV editions)

**Files:**
- Modify: `scripts/build_edition.py` (top of `build_one`, after the edition is loaded ~line 2609)
- Test: `tests/test_build_standalone.py`

- [ ] **Step 1 — write the failing test.** Append:

```python
class TestDispatchGuard:
    def test_build_one_routes_standalone(self, tmp_path, monkeypatch):
        from scripts import build_edition as be
        called = {}

        def fake_standalone(edition_id, output_dir, version):
            called["id"] = edition_id
            return {"status": "ok", "output_path": str(tmp_path / "x.epub")}

        monkeypatch.setattr("scripts.build_standalone.build_standalone", fake_standalone)
        be.build_one("standalone-geez", tmp_path, "v28a", [], False, False)
        assert called.get("id") == "standalone-geez"

    def test_build_one_does_not_route_kjv_edition(self, tmp_path, monkeypatch):
        # a non-standalone edition must NOT enter build_standalone (byte-stable guard)
        from scripts import build_edition as be
        tripped = {"v": False}

        def fake_standalone(*a, **k):
            tripped["v"] = True
            return {}

        monkeypatch.setattr("scripts.build_standalone.build_standalone", fake_standalone)
        # dry_run avoids a full real build; the guard is checked before any heavy work
        be.build_one("catholic-study", tmp_path, "v28a", [], True, False)
        assert tripped["v"] is False
```

- [ ] **Step 2 — run, confirm FAIL.**

Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m pytest tests/test_build_standalone.py::TestDispatchGuard -v`
Expected: FAIL — `test_build_one_routes_standalone` fails (standalone not routed; `build_one` tries the normal path and `called` stays empty).

- [ ] **Step 3 — add the guard in `scripts/build_edition.py`.** Immediately after the block that loads `edition = eds[edition_id]` near the top of `build_one` (the Explore report places this ~line 2609), insert:

```python
    # Phase C3d: standalone Bibles render from the own-versification store via a
    # dedicated path; the 9 KJV editions never enter this branch, so their output
    # is byte-identical to before. (Single chokepoint: every build_one caller —
    # api_export_build, build-all, matrix — is routed here.)
    if edition.get("standalone"):
        from scripts import build_standalone

        return build_standalone.build_standalone(edition_id, output_dir, version)
```

> Confirm the local variable names at the insertion site: `edition_id`, `output_dir`, `version` are `build_one`'s params (per the confirmed signature `build_one(edition_id, output_dir, version, all_kinds, dry_run=False, force=False)`), and `edition` is the loaded dict. Adjust if the recon shows different local names.

- [ ] **Step 4 — run, confirm PASS.**

Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m pytest tests/test_build_standalone.py::TestDispatchGuard -v`
Expected: PASS (2 tests).

- [ ] **Step 5 — commit.** `pwsh -File save.ps1 -Message "Phase C3d: build_one standalone dispatch guard (no-op for the 9 KJV editions)"`

---

## TASK C4 — first proof EPUB + invariants (Psalms xref, epubcheck, byte-stable proof)

**Files:**
- Create (by running the xref tool): `content/translations/geez-tewahedo/psa_apparatus.json`
- Modify: `scripts/build_standalone.py` (`_STANDALONE_BOOKS` += `"psa"`)
- Test: `tests/test_build_standalone.py`

- [ ] **Step 1 — generate the Psalms KJV cross-ref sidecar.** Reuse the Phase-B tool (`scripts/core/geez_kjv_xref.py` / `scripts/apply_kjv_xref.py`) to map own-vers Ge'ez Psalms → KJV Psalms (LXX vs KJV numbering genuinely diverges). Write a small adapter step that, for each Psalm chapter, builds `{str(ch): {str(v): {"kjv": [["psa", ch, v]], "confidence": "...", "apparatus": []}}}` and writes `content/translations/geez-tewahedo/psa_apparatus.json`. (Psalms has no manuscript apparatus → empty `apparatus` lists; popups carry the xref only.)

> If a direct numbering map is cleaner than the anchoring tool for Psalms, a per-chapter identity-or-offset map is acceptable — but the confidence MUST stay honest (`anchored` only where a real token/number matched; otherwise `interpolated`). Do NOT fabricate.

- [ ] **Step 2 — write the failing test.** Append:

```python
class TestProofEpub:
    def test_psalms_in_standalone_book_set(self):
        assert "psa" in bs._STANDALONE_BOOKS

    def test_psalms_apparatus_sidecar_exists_and_is_xref_only(self):
        p = REPO / "content" / "translations" / "geez-tewahedo" / "psa_apparatus.json"
        assert p.is_file()
        am = json.loads(p.read_text(encoding="utf-8"))
        # spot-check: a chapter exists, entries carry kjv + empty apparatus
        any_ch = next(iter(am.values()))
        any_v = next(iter(any_ch.values()))
        assert "kjv" in any_v and any_v.get("apparatus") == []
```

- [ ] **Step 3 — add Psalms to the proof set.** In `scripts/build_standalone.py`, change `_STANDALONE_BOOKS = ["1ki", "1sa", "2sa"]` to `["1ki", "1sa", "2sa", "psa"]`.

- [ ] **Step 4 — run the Phase-C tests + confirm PASS.**

Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m pytest tests/test_build_standalone.py -v`
Expected: PASS (all classes).

- [ ] **Step 5 — build the real proof EPUB.**

Run: `$env:PYTHONUTF8="1"; & "...python.exe" -c "from pathlib import Path; from scripts import build_standalone as bs; print(bs.build_standalone('standalone-geez', Path('exports'), 'v28a'))"`
Expected: `{'status': 'ok', 'output_path': 'exports\\Geez_Standalone_standalone-geez_v28a_….epub', 'books': 4, 'chapters': 160}` (6 Kings + 3 + 1 Samuel + 150 Psalms = 160).

- [ ] **Step 6 — epubcheck the proof EPUB at 0/0.**

Run (per memory `reference_epubcheck`, always `--jar`): `$env:PYTHONUTF8="1"; & "...python.exe" -m scripts.run_epubcheck --jar <bundled-jar> "exports\Geez_Standalone_standalone-geez_v28a_….epub"`
Expected: `0 errors / 0 warnings`. If RSC-005/nested-anchor or spine errors appear, fix the generator/OPF and rebuild (the body generator emits no nested `<a>`; the `vn-link` is the only verse anchor, and `note-ref` markers are absent in this phase).

- [ ] **Step 7 — prove the 9 KJV editions are byte-stable.** Build a KJV flagship and epubcheck it; the dispatch guard (C3d test) already proves non-standalone editions never enter the new path.

Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m scripts.build_edition --edition catholic-study --version v28a` then epubcheck the output `--jar`.
Expected: `epubcheck 0/0/0/0`; the build succeeds unchanged. Also confirm `git status` shows NO modification to `epub_working/` (the standalone path copies it read-only into a tempdir; it must never mutate the master tree).

- [ ] **Step 8 — full Phase-C suite + lint gate.**

Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m pytest tests/test_build_standalone.py -q` then `& "...python.exe" scripts/lint_rules.py` then `& "...python.exe" -m ruff format --check scripts/build_standalone.py scripts/core/standalone_store.py content/translations/geez-tewahedo/`
Expected: all green; `lint_rules` clean (or known-benign warns only); ruff format clean (run `ruff format` on any file it flags).

- [ ] **Step 9 — update the truth record + commit + back up.** Update `dev/SESSION_STATE.md` (Phase C complete; next = EN back-translation lane), `dev/IN_FLIGHT.md` (idle), `dev/CHANGELOG.md` (Phase C entry).

Run: `pwsh -File save.ps1 -Message "Phase C complete: standalone Ge'ez render path + first proof EPUB (Kings/Samuel + Psalms; epubcheck 0/0; 9 editions byte-stable)"`
Then back up (3rd-commit cadence / checkpoint): `git -C "<repo>" bundle create "E:\YHWH-v2.4-repo-2026-05-28-phaseC-complete-<hash>.bundle" --all` and the same to `F:`; `git bundle verify` each.

---

## Self-review (against the spec)

**1. Spec coverage:**
- §3.4 own-vers store + per-book `versification` → **C1** (`versification_of`) + **C2** (store generation). ✓
- §3.5 render path (generate body from store; popups = xref + apparatus; reuse EPUB infra; 9 editions untouched) → **C3a** (body), **C3b** (XHTML/OPF), **C3c** (orchestrator reusing `build_epub`/`patch_opf`/`matter`/cover), **C3d** (guard). ✓
- §9.1 EN pipeline-first / absent-not-faked → enforced in C3a (`vnote-text` absent; test asserts it). ✓
- §9.2 per-book versification → C1. ✓  §9.3 dedicated `build_standalone.py` → C3. ✓  §9.4 C2 store output shape → C2. ✓  §9.5 proof EPUB = Kings/Samuel + Psalms, epubcheck 0/0 + byte-stable → C4. ✓
- §6 testing (versification loader; store-gen; body render; epubcheck smoke; 9-editions-byte-stable) → covered across C1–C4. ✓

**2. Placeholder scan:** No "TBD/handle edge cases/similar to". The C3b recon + the two implementer-note blocks are explicit "confirm the real resource names" instructions with concrete fallback code, not vague placeholders — the skeleton resource names are genuinely data-dependent and must be read at execution. The `_chapters_for` stub is explicitly flagged for deletion.

**3. Type/name consistency:** `versification_of(translation, book_code)`, `collation_to_store_entries`, `build_book_store`, `render_chapter_body(book, chapter, verses, appmap)`, `wrap_xhtml_doc`, `build_manifest_and_spine`, `patch_standalone_opf`, `build_standalone(edition_id, output_dir, version)` are used consistently across tasks and tests. The apparatus sidecar is `{str(ch): {str(geez_v): {kjv, confidence, apparatus}}}` everywhere. `build_epub.build(epub_dir, out_path, *, bump)` matches the confirmed signature.

**Known execution-time confirmations (not gaps, but flagged):** the exact `epub_working` body-file location (root vs `OEBPS/`), the stylesheet href, the nav item, and the body manifest-id naming (`index_split`) are read in the C3b recon and used by C3b/C3c — each has a concrete default + a "confirm/adjust" note.
