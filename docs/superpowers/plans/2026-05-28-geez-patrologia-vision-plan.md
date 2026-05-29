# Ge'ez Phase D1b — Patrologia Vision-Transcription Lane (Esther proof) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax. Read FIRST: the companion spec `docs/superpowers/specs/2026-05-27-geez-own-versification-design.md` (§11 + the §11 Correction), the Patrologia ingest design `docs/superpowers/specs/2026-05-20-patrologia-ingest-design.md`, then the bootstrap triad (RULES → SESSION_STATE → end-scope PLAN).

**Goal:** Transcribe the printed Patrologia Orientalis Ge'ez **Esther** (PO 9 fasc 1, Pereira 1913) to its OWN versification *via an Opus vision agent reading the page images* — recovering the source margin verse-numerals + the LXX Additions A–F that the earlier Tesseract OCR lost — and fold it into the standalone Ge'ez Bible. This **proves the D1b vision lane** end-to-end (vision → own-vers store → KJV xref → standalone render → epubcheck 0/0 → 9 editions byte-stable) before scaling to the other 5 PO books.

**Architecture:** One principle — *trust the source's own versification; never `renumber_against_floor`; emit `VERSIFICATION="own"`.* The earlier OCR path (`extract_patrologia_pdf.extract_patrologia` → `parse_patrologia_pages` → `renumber_against_canonical_with_merge`) is **bypassed** for this lane: it `።`-split the body, swept the Ge'ez-script apparatus band into the verse text, lost the margin numerals, and proportionally re-binned 779 raw fragments into the KJV 167-verse skeleton (see the current garbage `est_patrologia.py` vv1:4–1:6). Instead: the controller renders each chapter's **Ge'ez body strip** (banner + body, apparatus + French excluded) to a PNG via the *existing* `extract_patrologia_pdf._render_strip_to_png`; a **single heavy Opus vision agent** transcribes the body faithfully, capturing the margin/inline verse-numbers + the Addition letters; an **independent reviewer agent** adversarially re-checks the same image; the controller validates + writes an own-versified `est_patrologia.py` (`VERSIFICATION="own"`), generates a Ge'ez→KJV xref sidecar via the Phase-B `geez_kjv_xref` tool, and adds `est_patrologia` to `build_standalone._STANDALONE_BOOKS`. A lighter cousin of the manuscript marathon: clean *printed* critical text (single, already-collated witness) → no dual-witness collation, no multi-round R1/R2/R3 unless a chapter needs it.

**Tech Stack:** Python 3.14, pytest, `pymupdf`(`fitz`, installed — verified 1.27.2), Tesseract NOT used here (vision replaces OCR), the project's `scripts/core/*`. Opus vision subagents (the Claude-Max AGENT path; the paid script-path `manuscript_vision.py` stays OUT OF SCOPE — no API budget). Windows/PowerShell.

**Environment invariants (this box):**
- python = `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe` (bare `python`/`python3` is a broken Win-Store stub).
- Always `$env:PYTHONUTF8="1"` before any test/run (or 72 tests fail with cp1252 errors).
- Commit via `save.ps1` through **PowerShell ONLY** (never the Bash tool — spaced path + arrow glyphs break cmd + sweep stray files). Pre-commit hook runs `ruff format --check .` + `lint_rules.py`; **`python -m ruff format` every generated `content/translations/...` file before saving** or the hook blocks the commit.
- No git remote (local commits only). Back up via `git bundle create <E:/F: path> --all` (every 3rd commit + each `/clear`); **E:/F: are external & currently UNMOUNTED — the user mounts them at a ship point; verify mounted before bundling, otherwise defer the backup with a note.**
- epubcheck: Java 8 on PATH; ALWAYS pass `--jar <bundled jar>` (memory `reference_epubcheck`).
- Source PDF: `GAPS/5_Esther/Esther__PO-9-fasc-1_Pereira_1913.pdf` (gitignored tree — reach by absolute path; Glob/Grep can't see it). 694-page PDF; **Esther body = PDF pages 24–65** (0-indexed; `PO_SOURCES["est"].default_page_range`).

---

## Calibration already done (controller, 2026-05-28 — informs this plan)

Rendered PO Esther pages 24/32/48/60 (full) + body strips of 24/32 at 230 DPI (1518×1093, under the 1568 vision cap) and read them. Findings (the GO basis):
- **Layout per page (consistent):** French banner `LE LIVRE D'ESTHER, <Roman ch>, <verse-range>` (top) → **Ge'ez body** (larger type, top ~6–42%) with **verse-numerals in the right margin + small inline superscripts** → **apparatus band** (smaller dense Ge'ez, keyed to verse + sigla M/N/O/P) → **French translation** (bottom ~40%).
- **Legible:** body glyphs + margin numerals clearly readable at 230 DPI / ≤1568px — vision-tractable.
- **Additions:** Pereira marks the LXX Additions with **margin LETTERS** (p24 opens with margin `A` = Addition A / Mordecai's dream, the LXX incipit before canonical 1:1). The exact per-verse addition numbering is resolved in Task 0.
- **GO** for the vision lane. The apparatus band is visually separable (smaller type, below the body) so a vision agent can exclude it where strip-OCR could not.

---

## Execution discipline (ALL tasks)
- **TDD** for all *code* (the render helper, the writer kwarg, the xref sidecar, the standalone wiring): failing test → confirm-FAIL → minimal impl → confirm-PASS → commit. One logical change per commit. (The *content* transcription, Task 4, is agent-driven + adversarially reviewed, not unit-TDD — but every chapter passes the controller validators below.)
- **Calibrate-first (cardinal honesty gate):** Task 0 vision-transcribes a sample chapter + an addition-boundary page and locks the additions-encoding + book-code decisions BEFORE any bulk transcription. **NO-GO → stop, report, write nothing** (the τ.6.x.0b contract). If Esther's additions need pipeline surgery beyond the proof's scope, fall back to **Job** (PO 2 fasc 5; clean linear ch 1–42, no additions) as the proof book and defer Esther's additions to a dedicated follow-up.
- **Byte-stable invariant (cardinal):** the 9 KJV editions' output must not change. `build_standalone` is the ONLY consumer of `geez-tewahedo`; the 9 never enter it. Prove each ship: rebuild a KJV flagship at `epubcheck 0/0/0/0` + `git status` shows `epub_working/` untouched. **`est.py` (the EOTC ocr-tier3 Esther) is NOT touched** — only `est_patrologia.py` (the separate PO slot, spec §6 decision B) is overwritten.
- **No fabrication (cardinal):** the vision agent transcribes ONLY what is on the page; genuine illegibility → `⟦illegible⟧`; genuine uncertainty → flagged, never silently smoothed to the printed Bible. The apparatus (variant readings) is editorial, NOT scripture — excluded. xref confidence honestly tagged `anchored`/`interpolated`.
- **Never-single-thread (RULES §2.5):** keep the **background lane** below running alongside the foreground heavy vision agent. Respect the concurrency cap (heavy >100k tokens MAX 1 · medium 30–100k MAX 2 · light <30k MAX 4). Image bytes stay OUT of the controller context — the controller renders strips to disk + passes PATHS; the transcriber/reviewer subagents `Read` the PNG in their OWN context (marathon RAM discipline).
- **Self-upgrading-matrix (RULES §1):** if a recurring vision failure-class appears (e.g. apparatus-bleed at a column foot, a margin-numeral misread), append it to a `content/translations/sources/patrologia/_vision_notes.md` so the next chapter inherits the lesson.

## Background lane (start at Task 4, runs through the heavy transcription)
A **light, text-only** D2-source-readiness agent (the NEXT lane): verify the clean-PD-Ge'ez availability + quality of **1 Enoch** (pseudepigrapha.org chs 1–71 Unicode; Charles 1906 archive.org) and **Jubilees** (Charles 1895), recording URL patterns + a GO/NO-GO-leaning note to `docs/superpowers/notes/2026-05-28-d2-source-readiness.md`. Independent of the Esther proof; advances D2's own future plan. (Do NOT pre-render all 42 Esther pages as the background lane — rendering is controller-cheap and on-demand per chapter in Task 4.)

## File structure (created / modified)
- **Modify** `scripts/extract_patrologia_pdf.py` — add `render_body_for_vision(pdf_path, pdf_page, out_path, *, dpi=230, geez_top_fraction=0.45)` (a thin public wrapper over the existing `_render_strip_to_png` "geez" path, but clipped to banner-through-body and EXCLUDING the apparatus band — top `geez_top_fraction` of the page; default 0.45 covers banner+body+margin numerals while excluding the apparatus, per calibration). Pure render-to-PNG; no OCR.
- **Modify** `scripts/extract_parallel_pdf.py` (`write_book_module`) — add keyword-only `versification: str | None = None`; emit a `VERSIFICATION = "<value>"` header line when set. Default `None` ⇒ no line ⇒ **byte-identical** for every existing caller.
- **Create** `scripts/core/po_vision_store.py` — `write_po_vision_module(book, verses, *, additions=None, ...)`: writes `content/translations/geez-tewahedo/<slot>.py` from vision-transcribed `(ch, v, text)` tuples WITHOUT renumbering (`VERSIFICATION="own"`, `SOURCE_QUALITY="patrologia-printed-tier1"`, provenance recording the PO volume + vision method + page range). Mirrors `extract_patrologia_pdf.write_book_module_patrologia` minus the renumber/merge.
- **Overwrite (by the Task-4 run)** `content/translations/geez-tewahedo/est_patrologia.py` — the own-vers vision transcription (replaces the KJV-renumbered OCR garbage; `BOOK="est"`, the `est_patrologia` slot).
- **Create (by the Task-5 run)** `content/translations/geez-tewahedo/est_patrologia_apparatus.json` — the Ge'ez→KJV xref sidecar.
- **Modify** `scripts/core/standalone_store.py` — add `build_patrologia_xref_sidecar(slot, canonical_book, out_dir)` (mirrors the Psalms `lxx_psalms_to_kjv` generator; uses `geez_kjv_xref.build_kjv_xref` vs `kjv/est.py`).
- **Modify** `scripts/build_standalone.py` — add `"est_patrologia"` to `_STANDALONE_BOOKS`; add a `_canonical_book(slot)` resolver that strips the `_patrologia` suffix → `"est"` for KJV-xref + canonical book-ordering; handle the Additions in the chapter iteration (per the Task-0 encoding decision).
- **Modify** `content/translations/sources/patrologia/_source.yaml` (create the dir/file if absent) — the Esther PO edition/PD/vision-method/fetch-date record.
- **Create** `content/translations/sources/patrologia/_vision_notes.md` — the per-chapter vision findings + recurring failure-classes (self-upgrading-matrix).
- **Tests:** `tests/test_po_vision.py` (NEW — render helper produces a valid PNG of expected dims; `write_po_vision_module` emits `VERSIFICATION="own"` + no renumber; store round-trips through `translations`), extend `tests/test_build_standalone.py` (est_patrologia in the standalone set; apparatus sidecar shape; own-versified; standalone book count/chapters), extend `tests/test_extract_patrologia_pdf.py` if the render helper belongs there instead.

---

## TASK 0 — Calibrate-first: vision-transcribe a sample + lock the Additions + book-code decisions (GO/NO-GO; NO store written)

**Goal:** prove a vision agent can transcribe a PO Esther page (body + margin numerals, apparatus excluded), determine Pereira's exact Addition numbering, and lock (a) the Additions store-encoding + (b) the `est_patrologia`→standalone book-code resolution. Resolve the three execution-time unknowns flagged in the Self-review.

- [ ] **Step 1 — render the calibration pages** (controller, `fitz`; write to OS temp, gitignored-safe). Render full pages + body strips for: **p24** (Addition A + canonical 1:1 incipit), the **Addition-boundary pages** (the banners the old `est_patrologia.py` docstring recorded: `III,9 — B,1`, `IV,17 — C,7`, `C,29 — D,6` ⇒ roughly PDF p33–40 by the ~4-pages-per-chapter density; render p34, p36, p38 and adjust by reading the banners), and **p65** (the tail / Addition F). Body strips at 230 DPI, top 0.45 clip (banner+body, apparatus excluded).

Run (adjust page numbers after reading the banners):
```
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -c "import fitz,tempfile,os; d=fitz.open(r'C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\GAPS\5_Esther\Esther__PO-9-fasc-1_Pereira_1913.pdf'); out=tempfile.gettempdir();
for p in (24,34,36,38,40,65):
    pg=d[p]; r=pg.rect; clip=fitz.Rect(r.x0,r.y0,r.x1,r.y0+r.height*0.45); pix=pg.get_pixmap(matrix=fitz.Matrix(230/72.0,230/72.0),clip=clip); fp=os.path.join(out,f'est_calib_p{p}.png'); pix.save(fp); print(fp,pix.width,pix.height)
d.close()"
```

- [ ] **Step 2 — controller reads the rendered pages** and records, per page: the banner (chapter + verse range + any Addition letter), and HOW the Addition verses are numbered in the margin (continuous within the canonical chapter? a separate letter+number like `B 1`? Roman+Arabic?). This is the data that locks Step 4's decision. Append findings to `content/translations/sources/patrologia/_vision_notes.md`.

- [ ] **Step 3 — dispatch ONE Opus vision transcriber subagent on canonical chapter 1's body strip(s)** (the heavy-agent shape Task 4 will reuse). The subagent is given the PNG path(s) + these instructions: *Read the image. Transcribe ONLY the large Ge'ez BODY text (top), NOT the smaller dense apparatus band below it and NOT the French. Output JSON `{"verses":[{"ch":N,"v":N,"label":"<margin label e.g. 1 or A1>","text":"<Ge'ez, terminators preserved>"}],"illegible":[...],"uncertain":[...],"notes":"..."}`. Verse boundaries come from the right-margin numerals + inline superscripts, NOT from `።` counts. Divine name in its 1st-order form as printed. Mark genuine illegibility `⟦illegible⟧`; never harmonize to a printed Bible.* The subagent `Read`s the PNG itself (controller never holds the bytes).

- [ ] **Step 4 — GO/NO-GO + lock decisions.** GO if: the body transcribed cleanly, the margin verse-numbers were recovered, the apparatus was excluded, and the Additions numbering is representable. Then **lock**:
  - **(a) Additions encoding** — default proposal, finalize from Step 2 data: keep canonical chapters as ints `1..10`; represent each Addition as its own chapter keyed by a documented scheme. Preferred = **string chapter labels** (`"A".."F"`) IF `translations.get_chapter` + `build_standalone` tolerate non-int chapter keys (confirm by a 1-line probe: load a tiny temp store with a string chapter + call `translations.chapter_verses_in_source_order`); ELSE fall back to **int offsets** `A=101..F=106` + an ORDER list giving the LXX reading order (A,1,2,3a,B,3b..4,C,D,5..8,E,8b..10,F) + a display-name map (`101→"Addition A"`). Record the exact chosen scheme in `_vision_notes.md` and reference it as "the Task-0 Additions scheme" in Tasks 3/4/6.
  - **(b) book-code resolution** — confirm how `build_standalone` maps a `_STANDALONE_BOOKS` entry to (i) the KJV skeleton for xref and (ii) the canonical book name/order. Confirm `translations` loads `est_patrologia.py` as a slot distinct from `est.py` (both have `BOOK="est"` — verify the loader keys by file stem, not the `BOOK` attr; this determines whether `est_patrologia` is addressable). Lock the `_canonical_book("est_patrologia")=="est"` resolver design for Task 6.
  - **NO-GO** (body unreadable / apparatus inseparable / additions need pipeline surgery beyond proof scope) → STOP; write nothing; switch the proof to **Job** (re-run Tasks 0–6 with `book="job"`, `slot="job"`, page range 584–697, linear int chapters — no additions, no book-code suffix) and report.

> No commit in Task 0 (recon only; temp PNGs are outside the repo). The `_vision_notes.md` decision record is committed at the end of Task 1 (first code commit).

---

## TASK 1 — `render_body_for_vision` helper (TDD)

**Files:** Modify `scripts/extract_patrologia_pdf.py`; Test `tests/test_po_vision.py` (new)

- [ ] **Step 1 — failing test.** Create `tests/test_po_vision.py`:
```python
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EST_PDF = REPO / "GAPS" / "5_Esther" / "Esther__PO-9-fasc-1_Pereira_1913.pdf"

def test_render_body_for_vision_writes_png(tmp_path):
    import pytest
    if not EST_PDF.is_file():
        pytest.skip("Esther PO PDF not on disk")
    import fitz
    from scripts.extract_patrologia_pdf import render_body_for_vision
    doc = fitz.open(str(EST_PDF))
    try:
        out = render_body_for_vision(doc[24], tmp_path / "p24.png", dpi=230, geez_top_fraction=0.45)
    finally:
        doc.close()
    assert out.is_file()
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"   # PNG magic
    import fitz as f2
    pix = f2.Pixmap(str(out))
    assert pix.width <= 1568 and pix.height <= 1568          # under the vision downsample cap
    assert pix.width > 800                                   # full page width preserved
```

- [ ] **Step 2 — run, confirm FAIL.** Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m pytest tests/test_po_vision.py::test_render_body_for_vision_writes_png -v` → FAIL (`render_body_for_vision` undefined).

- [ ] **Step 3 — implement.** In `scripts/extract_patrologia_pdf.py`, add:
```python
def render_body_for_vision(
    pdf_page,
    out_path: Path,
    *,
    dpi: int = 230,
    geez_top_fraction: float = 0.45,
    banner_top_fraction: float = 0.0,
) -> Path:
    """Render the banner+Ge'ez-body region of a PO page to a PNG for an
    Opus vision agent — EXCLUDING the apparatus band + French translation
    (the bottom of the page). Unlike ``_render_strip_to_png(strip='geez')``
    this keeps the top banner (for the chapter/verse cross-check) and the
    right margin (verse numerals), and clips at ``geez_top_fraction`` of
    the page height (default 0.45 — banner+body+margin, apparatus excluded;
    calibrated on PO 9 Esther 2026-05-28). DPI defaults to 230 so a full-
    width strip lands ~1518px (under the 1568 vision downsample cap)."""
    import fitz
    rect = pdf_page.rect
    clip = fitz.Rect(rect.x0, rect.y0 + rect.height * banner_top_fraction,
                     rect.x1, rect.y0 + rect.height * geez_top_fraction)
    zoom = dpi / 72.0
    pix = pdf_page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip)
    pix.save(str(out_path))
    return out_path
```

- [ ] **Step 4 — run, confirm PASS.** Run the test → PASS. Also run the existing `tests/test_extract_patrologia_pdf.py` to confirm no regression.

- [ ] **Step 5 — commit** (includes the Task-0 `_vision_notes.md` decision record). `pwsh -File save.ps1 -Message "Phase D1b: render_body_for_vision helper + Patrologia vision calibration notes (Esther GO; Additions/book-code decisions locked)"`

---

## TASK 2 — `write_book_module` emits `VERSIFICATION = "own"` (TDD)

**Files:** Modify `scripts/extract_parallel_pdf.py` (`write_book_module`); Test `tests/test_po_vision.py`

- [ ] **Step 1 — confirm the real signature** of `write_book_module` (the Task call-site shows `translation=, book=, verses=, source_quality=, extraction_date=, *, ingest_phase=, docstring_extra=, source_provenance=, source_yaml_ref=, tool=`). Add a keyword-only `versification: str | None = None`.

- [ ] **Step 2 — failing test** (append to `tests/test_po_vision.py`):
```python
def test_write_book_module_emits_versification(tmp_path, monkeypatch):
    import scripts.extract_parallel_pdf as ep
    # write into a temp translations dir so we don't touch the real store
    monkeypatch.setattr(ep, "TRANSLATIONS_DIR", tmp_path, raising=False)
    out = ep.write_book_module(
        translation="geez-tewahedo", book="zzz", verses=[(1, 1, "ሰላም።")],
        source_quality="patrologia-printed-tier1", extraction_date="2026-05-28",
        ingest_phase="D1b", docstring_extra="x", source_provenance="p",
        source_yaml_ref="u", tool="t", versification="own",
    )
    text = out.read_text(encoding="utf-8")
    assert 'VERSIFICATION = "own"' in text
```
> Confirm `write_book_module` writes under a module-level `TRANSLATIONS_DIR` (or similar). If it computes the path differently, adapt the monkeypatch to whatever it actually uses; the assertion (emits `VERSIFICATION = "own"`) is the invariant.

- [ ] **Step 3 — run, confirm FAIL** (unexpected `versification` kwarg).

- [ ] **Step 4 — implement.** In `write_book_module`, when `versification is not None`, emit `VERSIFICATION = "<value>"` in the module header next to `SOURCE_QUALITY`. Default `None` ⇒ no line ⇒ byte-identical for every existing caller.

- [ ] **Step 5 — run, confirm PASS** + run any existing `write_book_module`/`extract_parallel_pdf` tests to confirm byte-identical default.

- [ ] **Step 6 — commit.** `pwsh -File save.ps1 -Message "Phase D1b: write_book_module optional VERSIFICATION attr (default unset = byte-identical)"`

---

## TASK 3 — `write_po_vision_module` own-vers store writer (TDD)

**Files:** Create `scripts/core/po_vision_store.py`; Test `tests/test_po_vision.py`

- [ ] **Step 1 — failing test** (append):
```python
def test_write_po_vision_module_is_own_no_renumber(tmp_path, monkeypatch):
    import scripts.extract_parallel_pdf as ep
    monkeypatch.setattr(ep, "TRANSLATIONS_DIR", tmp_path, raising=False)
    from scripts.core import po_vision_store as pv
    # 3 verses whose numbering is NON-canonical (source-authoritative) — must survive verbatim
    verses = [(1, 1, "አንድ።"), (1, 2, "ሁለት።"), (1, 3, "ሦስት።")]
    out = pv.write_po_vision_module(
        slot="zzz_patrologia", book="zzz", verses=verses,
        po_book="est", page_range=(24, 65), phase="D1b",
        translations_module=ep,
    )
    text = out.read_text(encoding="utf-8")
    assert 'VERSIFICATION = "own"' in text
    assert 'SOURCE_QUALITY = "patrologia-printed-tier1"' in text
    assert 'vision' in text.lower()                 # provenance records the vision method
    # round-trips through the loader at the SOURCE numbering (no KJV renumber)
    import ast
    ns = {}
    exec(compile(text, str(out), "exec"), ns)        # test-only; loader uses literal_eval
    assert ns["VERSES"] == verses
```

- [ ] **Step 2 — run, confirm FAIL** (`po_vision_store` undefined).

- [ ] **Step 3 — implement** `scripts/core/po_vision_store.py`:
```python
"""Own-versification store writer for the Patrologia vision lane (D1b).

Unlike ``extract_patrologia_pdf.write_book_module_patrologia`` (which OCR-
extracted then ``renumber_against_canonical``'d into the KJV skeleton), this
writes the vision-transcribed verses VERBATIM at their source margin
numbering (``VERSIFICATION="own"``). No renumber, no merge."""
from __future__ import annotations
from datetime import date
from pathlib import Path

def write_po_vision_module(*, slot, book, verses, po_book, page_range,
                           phase="D1b", extraction_date=None,
                           translations_module=None):
    from scripts.extract_patrologia_pdf import PO_SOURCES
    if translations_module is None:
        import scripts.extract_parallel_pdf as translations_module
    src = PO_SOURCES[po_book]
    ext_date = extraction_date or date.today().isoformat()
    doc_extra = "\n".join([
        f"Source: {src.citation}", f"Archive: {src.archive_url}",
        f"Editor: {src.editor} ({src.year}); public-domain bilingual critical edition.",
        "",
        "Transcription method: OWN-VERSIFICATION via Opus VISION agent reading "
        "the PO page images (D1b vision lane) — captures the source margin "
        "verse-numerals + LXX Additions that the earlier Tesseract OCR lost, "
        "and EXCLUDES the editor's apparatus band. Source numbering is "
        "authoritative — NOT renumbered against the KJV floor.",
        f"PDF pages: {page_range[0]}-{page_range[1]}.",
        f"Verse count: {len(verses)}.",
    ])
    return translations_module.write_book_module(
        translation="geez-tewahedo", book=book, verses=verses,
        source_quality="patrologia-printed-tier1", extraction_date=ext_date,
        ingest_phase=phase, docstring_extra=doc_extra,
        source_provenance=src.provenance, source_yaml_ref=src.archive_url,
        tool="scripts/core/po_vision_store.py (Opus vision)",
        versification="own",
    )
```
> The writer keys the output FILE by `slot` (e.g. `est_patrologia`) not `book`. Confirm `write_book_module`'s filename derivation; if it uses `book` for the filename, add a `filename`/`slot` param to `write_book_module` (keyword-only, default = `book`) at this task and keep it byte-identical when unset.

- [ ] **Step 4 — run, confirm PASS.**

- [ ] **Step 5 — commit.** `pwsh -File save.ps1 -Message "Phase D1b: po_vision_store.write_po_vision_module (own-vers, no renumber, vision provenance)"`

---

## TASK 4 — Vision-transcribe Esther → `est_patrologia.py` (own-vers; the heavy lane)

**Files:** Overwrites `content/translations/geez-tewahedo/est_patrologia.py`; writes `content/translations/sources/patrologia/_source.yaml` + `_vision_notes.md`. Per-chapter; **MAX 1 heavy agent**; **start the background lane now** (see top).

**Per-chapter procedure (repeat for the Esther reading-order units — canonical 1–10 interleaved with Additions A–F per the Task-0 scheme):**

- [ ] **C-a — locate + render.** Controller: identify the PDF page(s) for the unit by reading the banners (Task-0 spread + `parse_banner_chapter`); render each page's body strip via `render_body_for_vision` to OS temp. Tight ≤1568px; apparatus excluded. (Controller does NOT read the bytes.)
- [ ] **C-b — blind transcribe (1 heavy Opus vision agent).** Dispatch the Task-0 transcriber prompt on the unit's strip path(s). Output the `{verses:[{ch,v,label,text}],illegible,uncertain,notes}` JSON. Faithful to the LXX/Ethiopic print (NOT KJV); divine name as printed; Additions labeled per the Task-0 scheme; apparatus excluded.
- [ ] **C-c — adversarial review (1 heavy Opus agent, AFTER C-b drains).** Independent agent re-reads the SAME strip image: verifies every verse-number against the margin, hunts apparatus-bleed (any siglum-keyed variant text that slipped in), boundary correctness (banner range match), 0 fabrication, illegible genuineness. Fixes in place; reports a verdict.
- [ ] **C-d — controller validate + accumulate.** Validate: verse count vs banner range; Ethiopic-only (no Latin sigla); terminators present; numbering monotonic within the Task-0 scheme. Append the unit's verses to the running list + a per-unit note to `_vision_notes.md`. Free system RAM. **Commit per unit (or per 2–3 short units)** so a crash loses ≤1 unit (auto-commit-each-step marathon discipline). The USER runs `/clear` at their discretion between heavy units.
- [ ] **Calibrate gate:** do canonical **chapter 1 (+ Addition A)** first; controller spot-checks the transcript against the page; only then continue. (This is the live re-confirmation of the Task-0 GO on real per-chapter output.)

- [ ] **Final step — write the store.** When all units are transcribed + reviewed-clean, write `est_patrologia.py` via `po_vision_store.write_po_vision_module(slot="est_patrologia", book="est", verses=<all>, po_book="est", page_range=(24,65))`; ruff-format it; add the Esther block to `content/translations/sources/patrologia/_source.yaml`; sanity-load:
`$env:PYTHONUTF8="1"; & "...python.exe" -c "from scripts.core import translations as t; print(t.versification_of('geez-tewahedo','est_patrologia'), len(t.get_chapter('geez-tewahedo','est_patrologia',1)))"` → `own <N>`.
Commit: `pwsh -File save.ps1 -Message "Phase D1b: Esther own-versification via Opus vision transcription (PO 9 Pereira 1913; Additions A-F recovered; apparatus excluded)"`.

> **Safety (overwrite):** Task 4 overwrites the KJV-renumbered `est_patrologia.py` with the own-vers vision version. Safe: `geez-tewahedo` feeds ONLY the standalone path; `est_patrologia` is NOT yet in `_STANDALONE_BOOKS` (rendered nowhere before); `est.py` (EOTC ocr) is untouched; no `geez-tewahedo-en/est_patrologia.py` is keyed to the old coords yet. Confirm with `git status` that only `est_patrologia.py` + `_source.yaml` + `_vision_notes.md` changed under `content/` and `epub_working/` is untouched.

---

## TASK 5 — Ge'ez→KJV xref sidecar `est_patrologia_apparatus.json` (TDD)

**Files:** Modify `scripts/core/standalone_store.py`; writes `content/translations/geez-tewahedo/est_patrologia_apparatus.json`; Test `tests/test_build_standalone.py`

- [ ] **Step 1 — confirm** `geez_kjv_xref.build_kjv_xref`'s real signature (the Phase-B tool; the HaCohen plan recorded `build_kjv_xref(geez_verses, kjv_verses, book=, chapter=)`) and the Psalms `lxx_psalms_to_kjv` sidecar generator shape in `standalone_store.py`.

- [ ] **Step 2 — failing test** (append to `tests/test_build_standalone.py`):
```python
def test_est_patrologia_apparatus_sidecar_xref_only():
    import json
    from pathlib import Path
    p = (Path(__file__).resolve().parent.parent / "content" / "translations"
         / "geez-tewahedo" / "est_patrologia_apparatus.json")
    assert p.is_file()
    am = json.loads(p.read_text(encoding="utf-8"))
    any_ch = next(iter(am.values())); any_v = next(iter(any_ch.values()))
    assert any_v.get("apparatus") == []                       # printed book → no manuscript apparatus
    assert any_v.get("confidence") in ("anchored", "interpolated", "none")
```

- [ ] **Step 3 — run, confirm FAIL** (sidecar absent).

- [ ] **Step 4 — implement `build_patrologia_xref_sidecar(slot, canonical_book, out_dir)`** in `scripts/core/standalone_store.py`, beside `lxx_psalms_to_kjv`. For each canonical chapter of the own-vers slot: load Ge'ez verses (`translations.get_chapter("geez-tewahedo", slot, ch)`) + KJV verses (`translations.get_chapter("kjv", canonical_book, ch)`); call `geez_kjv_xref.build_kjv_xref(...)`; emit `{str(ch):{str(v):{"kjv":[[bk,ch,v],...],"confidence":...,"apparatus":[]}}}`. **Addition chapters (no KJV equivalent) → `{"kjv":[],"confidence":"none","apparatus":[]}`** (honest — KJV Esther has no Additions; never fabricate a mapping). Write `out_dir / f"{slot}_apparatus.json"` (`ensure_ascii=False, indent=2`).

- [ ] **Step 5 — run the generator** then the test → PASS:
`$env:PYTHONUTF8="1"; & "...python.exe" -c "from pathlib import Path; from scripts.core import standalone_store as ss; ss.build_patrologia_xref_sidecar('est_patrologia','est',Path('content/translations/geez-tewahedo')); print('wrote est_patrologia_apparatus.json')"`

- [ ] **Step 6 — commit.** `pwsh -File save.ps1 -Message "Phase D1b: Ge'ez->KJV xref sidecar for Esther (geez_kjv_xref; Additions honestly unmapped)"`

---

## TASK 6 — Wire Esther into the standalone + proof gates (TDD + build)

**Files:** Modify `scripts/build_standalone.py`; Test `tests/test_build_standalone.py`

- [ ] **Step 1 — failing tests** (append):
```python
def test_est_patrologia_in_standalone_set():
    from scripts import build_standalone as bs
    assert "est_patrologia" in bs._STANDALONE_BOOKS

def test_canonical_book_strips_patrologia_suffix():
    from scripts import build_standalone as bs
    assert bs._canonical_book("est_patrologia") == "est"
    assert bs._canonical_book("1ki") == "1ki"
```

- [ ] **Step 2 — run, confirm FAIL.**

- [ ] **Step 3 — implement.** Add `_canonical_book(slot)` (`return slot.split("_patrologia")[0] if slot.endswith("_patrologia") else slot`) and route the standalone's KJV-xref lookup + canonical book-name/order through it; add `"est_patrologia"` to `_STANDALONE_BOOKS`; render Addition chapters per the Task-0 scheme (string labels → display "Addition X"; int-offset → map 101→"Addition A" in the chapter heading). Keep the 9 KJV editions' path untouched (the dispatch fires only for `edition.get("standalone")`).

- [ ] **Step 4 — run the standalone suite** → PASS: `$env:PYTHONUTF8="1"; & "...python.exe" -m pytest tests/test_build_standalone.py -v`

- [ ] **Step 5 — build the standalone EPUB:**
`$env:PYTHONUTF8="1"; & "...python.exe" -c "from pathlib import Path; from scripts import build_standalone as bs; print(bs.build_standalone('standalone-geez', Path('exports'), 'v28a'))"`
Expected: `status: ok`; books 4→**5** (1ki,1sa,2sa,psa,est_patrologia); chapters 161 + Esther's own-vers count.

- [ ] **Step 6 — epubcheck the proof EPUB at 0/0** (`--jar`, per `reference_epubcheck`): if RSC errors, fix the generator + rebuild.

- [ ] **Step 7 — prove the 9 KJV editions byte-stable:** build `catholic-study` + epubcheck 0/0/0/0; `git status -- epub_working` shows no change.

- [ ] **Step 8 — full proof-suite + lint + ruff:** `pytest tests/test_build_standalone.py tests/test_po_vision.py -q`; `lint_rules.py`; `ruff format --check` the touched files.

- [ ] **Step 9 — truth record + commit + (deferred) backup.** Update `dev/SESSION_STATE.md` + `dev/IN_FLIGHT.md` + `dev/CHANGELOG.md` (Esther own-vers via vision shipped; standalone 5 books; D1b lane PROVEN; next = Esther EN + scale-out Job). `pwsh -File save.ps1 -Message "Phase D1b PROOF: Esther own-versification folded into the standalone Ge'ez Bible (vision lane proven; epubcheck 0/0; 9 editions byte-stable; standalone 5 books)"`. **Back up to E:/F: ONLY if the user has mounted them** (`git bundle create "E:\YHWH-...-phaseD1b-esther-<hash>.bundle" --all` + F: + `git bundle verify`); otherwise note "backup deferred — E:/F: unmounted" in the truth record + flag at the next checkpoint.

---

## TASK 7 — Esther EN back-translation (following lane)

> Per spec §11.5 / §10, EN follows the own-vers ship. Reuse the Psalms/Kings method: a translator subagent (Opus; faithful to the **Ge'ez** wording NOT KJV/NRSV; "Yahweh"; `[brackets]` for genuine uncertainty; the Additions translated from their Ge'ez) reads `est_patrologia.py` in source order → drafts `content/translations/geez-tewahedo-en/est_patrologia.py` (`VERSES=[(ch, v, english)]` at the SAME own coords, tier `ai-back-translation-reviewed-tier3`); an INDEPENDENT reviewer subagent checks each verse for faithfulness/drift/KJV-contamination → revise to convergence. Confirm `build_standalone`'s EN lookup keys by `_canonical_book`/slot correctly for `est_patrologia`. Rebuild → `vnote-text` English appears in Esther popups → epubcheck 0/0 + 9 editions byte-stable. Commit. (Method: `docs/superpowers/plans/2026-05-28-geez-en-backtranslation-plan.md` applied to `est_patrologia`.)

---

## SCALE-OUT — the other 5 PO books (own follow-up after the proof validates the lane)

Repeat Tasks 4–7 per book using the now-proven helpers (`render_body_for_vision`, `write_po_vision_module`, `build_patrologia_xref_sidecar`, the `_canonical_book` resolver). Recommended order:
- **Job** (`job`, PO 2 fasc 5, pages 584–697, 42 ch) — **next after Esther**: clean linear int chapters (no additions) — validates the helpers generalize beyond the additions-special-case; longest volume but simplest versification.
- **Ezra** (`ezr`, PO 13, pages 13–47) + **Nehemiah** (`neh`, PO 13, pages 48–97) — one volume, two books (banner ~0.10).
- **1 Chronicles** (`1ch`, PO 23, pages 542–647) + **2 Chronicles** (`2ch`, PO 23, pages 648–776) — Grébaut, French-ordinal banners, heaviest.
Each: own-vers store overwriting the KJV-renumbered version, xref sidecar, `_STANDALONE_BOOKS` add, build/epubcheck/byte-stable, EN lane. `est.py` (EOTC ocr) stays untouched throughout. After all 6: standalone Ge'ez Bible = the Kings/Samuel marathon chapters + Psalms + 6 PO books.

---

## Self-Review (against spec §11 + the §11 Correction + the Patrologia design spec)

- **Spec coverage:** §11 Correction "PO PDFs are OCR-garbled → need a vision agent reading the page images, capture margin numerals, exclude the French/apparatus, own plan" → Tasks 0–6 ✓; §11 mechanism (trust source numbering, never renumber, `VERSIFICATION="own"`) → Tasks 2/3/4 ✓; proof end-to-end (vision→store→xref→render→epubcheck→byte-stable) → Tasks 4–6 ✓; EN following lane → Task 7 ✓; D1b "gets its own plan, job-then-rest scale-out" → this plan + Scale-out ✓; honesty gates (calibrate-first, 0 fabrication, apparatus excluded, confidence-tagged, byte-stable, est.py untouched) → Execution discipline + Tasks 4/5/6 ✓. The patrologia design spec §6 decision B (keep est.py + est_patrologia.py) is honored (only the PO slot changes).
- **Placeholder scan:** the "Task-0 Additions scheme" + "Task-0 book-code resolution" references in Tasks 3/4/6 are explicit calibration-output bindings (genuinely data-dependent on Pereira's printed numbering + the loader's behavior, resolved by Task 0's GO/NO-GO), NOT vague TODOs — same accepted pattern as the HaCohen plan's `<…FROM_TASK0>` bindings. The Job fallback is fully specified. No hidden gaps.
- **Type/name consistency:** `render_body_for_vision(pdf_page, out_path, *, dpi, geez_top_fraction)`, `write_book_module(..., versification=)`, `write_po_vision_module(slot, book, verses, po_book, page_range, ...)`, `build_patrologia_xref_sidecar(slot, canonical_book, out_dir)`, `_canonical_book(slot)`, `_STANDALONE_BOOKS`, sidecar shape `{str(ch):{str(v):{kjv,confidence,apparatus}}}` are used consistently across tasks + align with the existing `PO_SOURCES`, `_render_strip_to_png`, `lxx_psalms_to_kjv`, `geez_kjv_xref.build_kjv_xref`, `translations.versification_of/get_chapter`.
- **Known execution-time confirmations (flagged, not gaps):** `write_book_module`'s filename derivation + whether it needs a `slot`/`filename` param (Task 3 Step 3 note); `geez_kjv_xref.build_kjv_xref`'s exact signature (Task 5 Step 1); whether `translations` loads `est_patrologia.py` as a slot distinct from `est.py` + whether the pipeline tolerates string chapter keys (Task 0 Step 4b probe). Each has an explicit "confirm the real …" instruction.
