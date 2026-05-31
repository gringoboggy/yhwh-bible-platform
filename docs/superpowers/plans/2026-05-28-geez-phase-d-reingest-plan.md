# Ge'ez Phase D — Own-Versification Re-ingest (HaCohen lane + Wisdom proof) Implementation Plan
**Status:** in progress — Phase D own-versification re-ingest lane

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax. Read the companion spec `docs/superpowers/specs/2026-05-27-geez-own-versification-design.md` (esp. **§11 + the §11 Correction**) FIRST, then the bootstrap triad (RULES → SESSION_STATE → the live master roadmap PLAN named in RULES §0).

**Goal:** Re-ingest KJV-renumbered Geʽez books to their OWN versification so they join the standalone Geʽez Bible — proven end-to-end on **Wisdom of Solomon** via the clean HaCohen path, then **Sirach**; the Patrologia vision-transcription lane (D1b) + the distinctive-source acquisition lane (D2) get their own detailed plans at their start.

**Architecture:** One principle — *trust the source's own versification; never `renumber_against_floor`; emit `VERSIFICATION="own"`.* The HaCohen path (`scripts/ingest_hacohen.py`, which already produced Psalms) is generalized from psalms-only to a per-book registry; each new book gets a small per-edition parser + a calibrate-first GO/NO-GO gate, writes `content/translations/geez-tewahedo/<book>.py` at `digitized-critical-edition` quality, gets a Geʽez→KJV xref sidecar via the Phase-B `geez_kjv_xref` tool, and is added to `build_standalone._STANDALONE_BOOKS`. The 9 KJV editions never enter the standalone path → byte-stable.

**Tech Stack:** Python 3.14, pytest, stdlib + the project's `scripts/core/http.py` (retry/timeout/SSRF allowlist). Windows/PowerShell.

**Environment invariants (this box):**
- python = `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe` (bare `python`/`python3` is a broken Win-Store stub).
- Always `$env:PYTHONUTF8="1"` before any test/run (or 72 tests fail with cp1252 errors).
- Commit via `save.ps1` through **PowerShell ONLY** (never the Bash tool). Pre-commit hook runs `ruff format --check .` + `lint_rules.py`; **`python -m ruff format` every generated `content/translations/...` file before saving** or the hook blocks the commit.
- No git remote (local commits only). Back up via `git bundle create <E:/F: path> --all` (every 3rd commit + each `/clear`); E:/F: are external — verify mounted first.
- epubcheck: Java 8 on PATH; ALWAYS pass `--jar <bundled jar>` (memory `reference_epubcheck`).

---

## Execution discipline (ALL tasks)
- **TDD:** failing test → run-and-confirm-FAIL → minimal implementation → run-and-confirm-PASS → commit. One logical change per commit.
- **Calibrate-first (cardinal honesty gate):** before any bulk ingest of a book, fetch a small calibration sample and confirm the URL pattern holds, the HTML is parseable, it's Unicode Ethiopic, and the first verse is numbered 1. **NO-GO → stop, report honestly, write NOTHING** (τ.6.x.0b contract). Never silently renumber or fabricate.
- **Byte-stable invariant (cardinal):** the 9 KJV editions' output must not change. The standalone path (`build_standalone`) is the only consumer of `geez-tewahedo`; the 9 never enter it. Prove it each ship: rebuild a KJV flagship at `epubcheck 0/0/0/0` + `git status` shows `epub_working/` untouched.
- **Never-single-thread (RULES §2.5):** keep a background lane running — e.g. while the Wisdom proof runs, a light lane can pre-fetch the Sirach HaCohen pages or research the D2 (1 Enoch / Jubilees) source quality. Respect the concurrency cap (heavy >100k MAX 1 / medium 30-100k MAX 2 / light <30k MAX 4).
- **Honesty gates:** 0 fabrication; xref confidence tagged `anchored`/`interpolated`; each module records the exact edition, editor, PD basis, fetch date, tier; the witnesses + 4 Samuel goldens are immutable.

## File structure (created / modified)
- **Modify** `scripts/ingest_hacohen.py` — generalize psalms-only → a per-book registry (`_BOOKS`) with URL pattern + parser + chapter range + calibration sample; add `parse_hacohen_wisdom`; generalize `fetch`/`calibrate`/`ingest`/`main`.
- **Modify** `scripts/extract_parallel_pdf.py` (`write_book_module`) — accept an optional `versification="own"` so the emitted module carries `VERSIFICATION = "own"` (Psalms had it hand-added at Phase C1; generalize so HaCohen books emit it directly). Default unset = byte-identical for every existing caller.
- **Create (by running the ingest):** `content/translations/geez-tewahedo/wis.py` (OVERWRITES the current `ocr-tier3` `wis.py` — see Task 6 safety note) + later `sir.py`.
- **Create (by running the xref adapter):** `content/translations/geez-tewahedo/wis_apparatus.json`.
- **Modify** `content/translations/sources/hacohen-geez/_source.yaml` — add the Wisdom (+ Sirach) edition/PD records.
- **Modify** `scripts/build_standalone.py:151` — add `"wis"` (then `"sir"`) to `_STANDALONE_BOOKS`.
- **Modify** `scripts/core/standalone_store.py` — add a small `build_hacohen_xref_sidecar(book, out_dir)` that maps own-vers Geʽez → KJV via `geez_kjv_xref.build_kjv_xref` and writes `<book>_apparatus.json` (the HaCohen analogue of the Psalms `lxx_psalms_to_kjv` sidecar generator already there).
- **Tests:** `tests/test_ingest_hacohen.py` (extend — parser + registry + versification), `tests/test_build_standalone.py` (extend — wis in the standalone book set, apparatus sidecar shape).

---

## TASK 0 — HaCohen Wisdom source recon (calibrate-first; NO artifacts written)

**Goal:** discover the HaCohen Wisdom URL pattern + page markup so the parser (Task 2) is concrete. The Psalms view is `https://www.tau.ac.il/~hacohen/Psalm/PsalmNrR%20{n}.html` with verses marked by a leading `<span style="font-size:70%">N</span>` inside each `<p>` (see `parse_hacohen_psalter`). Wisdom's edition differs, so its URL + verse-number markup must be confirmed.

- [ ] **Step 1 — find the Wisdom URL pattern.** Fetch the HaCohen index once and locate the Wisdom-of-Solomon links:

Run: `$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -c "from scripts.core import http; import re; h=http.get('https://www.tau.ac.il/~hacohen/', allowlist=frozenset({'tau.ac.il'})).decode('utf-8','replace'); print('\n'.join(l for l in re.findall(r'href=\"([^\"]+)\"', h) if any(k in l.lower() for k in ('wisd','sap','solomon','sir','ecclus'))))"`
Expected: a set of relative links revealing the Wisdom (and Sirach) page pattern (e.g. a per-chapter `.html` like the Psalms view). Record the exact pattern.

- [ ] **Step 2 — fetch 2-3 Wisdom calibration pages into the cache.** Wisdom has **19 chapters**. Sample chapters 1, 9 (a long central chapter), and 19 (boundary):

Run a one-off using the project HTTP wrapper, writing to `content/translations/sources/hacohen-geez/cache/` with a `Wisdom <n>.html`-style name (mirror the Psalms cache naming convention you discovered). Use `scripts.core.http.get(url, allowlist=frozenset({"tau.ac.il"}))`; a 1s delay between fetches; never partial-write.

- [ ] **Step 3 — inspect the verse-number markup.** Open one cached Wisdom page and identify: (a) how a new verse begins (the leading verse-number element — is it the same `<span style="font-size:70%">N</span>`, a different span, an `<a>` anchor, or inline numerals?), (b) the chapter-caption element, (c) any "Nr. Vers" toggle / title paragraphs to skip. Record findings into Task 2 below.

- [ ] **Step 4 — GO/NO-GO.** GO if: URL pattern holds, Unicode Ethiopic, verse numbering is parseable, page 1 starts at verse 1. **NO-GO** (structure not extractable) → STOP, report, write nothing; fall back to **Sirach as the proof** (Task 9 first) or escalate to the user. (No `merge_to_floor` fallback here — that produces *canonical* numbering, which defeats own-versification; a HaCohen book that won't parse cleanly is deferred, not floor-merged.)

> No commit in Task 0 (recon only; the cache dir is gitignored per `content/translations/sources/hacohen-geez/.gitignore`).

---

## TASK 1 — generalize `ingest_hacohen.py` to a per-book registry

**Files:** Modify `scripts/ingest_hacohen.py`; Test `tests/test_ingest_hacohen.py`

- [ ] **Step 1 — failing test.** Add to `tests/test_ingest_hacohen.py`:

```python
def test_book_registry_has_wisdom():
    from scripts import ingest_hacohen as ih
    assert "wisdom" in ih._BOOKS
    spec = ih._BOOKS["wisdom"]
    assert spec["book_code"] == "wis"
    assert spec["chapters"] == range(1, 20)        # 19 chapters
    assert callable(spec["parser"])
    assert "{n}" in spec["url"]
```

- [ ] **Step 2 — run, confirm FAIL.**
Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m pytest tests/test_ingest_hacohen.py::test_book_registry_has_wisdom -v`
Expected: FAIL — `AttributeError: module 'scripts.ingest_hacohen' has no attribute '_BOOKS'`.

- [ ] **Step 3 — implement the registry.** In `scripts/ingest_hacohen.py`, replace the psalms-only `_PSALM_URL` constant + the hard-wired `fetch_psalm`/`ingest_psalms` with a registry-driven path. Keep `parse_hacohen_psalter` unchanged (psalms parser). Add:

```python
# Per-book HaCohen ingest registry. Each book's HaCohen edition differs,
# so each gets its own parser + URL pattern + calibration sample.
_BOOKS: dict[str, dict] = {
    "psalms": {
        "book_code": "psa",
        "url": _BASE + "Psalm/PsalmNrR%20{n}.html",
        "cache_name": "PsalmNrR {n}.html",
        "chapters": range(1, 152),
        "calib": [1, 118, 151],
        "parser": parse_hacohen_psalter,
        "quality": "digitized-critical-edition",
        "provenance": "hacohen-geez",
        "docstring_extra": (
            "Ingested from Ran HaCohen's digitized Ge'ez Psalter "
            "(Psalterium Davidis, ed. Hiob Ludolf 1701; Rahlfs/LXX "
            "verse numbering; PD by age). Source numbering is "
            "authoritative — NOT renumbered against the floor."
        ),
    },
    # "wisdom" added in Task 2 step 3 (after the parser exists).
}
```

Generalize the fetch/calibrate/ingest to take a book key (signatures: `fetch_book(book, *, cache_dir=DEFAULT_CACHE, delay=1.0)`, `calibrate(book, *, cache_dir=DEFAULT_CACHE)`, `ingest_book(book, *, cache_dir=DEFAULT_CACHE, phase)`). Each reads `_BOOKS[book]`. Preserve `fetch_psalm`/`calibrate(sample=...)`/`ingest_psalms` as thin back-compat shims that delegate to the generic functions with `"psalms"` (so existing tests/callers keep working — confirm by running the full `tests/test_ingest_hacohen.py`).

- [ ] **Step 4 — run, confirm the registry test + the existing psalms tests PASS.**
Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m pytest tests/test_ingest_hacohen.py -v`
Expected: PASS (registry test + all pre-existing psalms tests green — back-compat shims hold).

- [ ] **Step 5 — commit.** `pwsh -File save.ps1 -Message "Phase D: generalize ingest_hacohen to a per-book registry (psalms back-compat preserved)"`

---

## TASK 2 — `parse_hacohen_wisdom` parser (TDD on a committed fixture)

**Files:** Modify `scripts/ingest_hacohen.py`; add a fixture under `tests/fixtures/hacohen/`; Test `tests/test_ingest_hacohen.py`

- [ ] **Step 1 — capture a tiny fixture.** From a Task-0 cached Wisdom page, hand-trim 1-2 verses' worth of the real HTML into `tests/fixtures/hacohen/wisdom_ch1_sample.html` (small, committed — the deterministic offline parser input, mirroring the spec §8 fixture approach). Include the chapter caption + verse 1 + verse 2 markup exactly as the page has it.

- [ ] **Step 2 — failing test** (fill `EXPECTED` from the fixture's real Geʽez text):

```python
def test_parse_hacohen_wisdom_first_two_verses():
    from pathlib import Path
    from scripts import ingest_hacohen as ih
    html = (Path(__file__).parent / "fixtures" / "hacohen" / "wisdom_ch1_sample.html").read_text(encoding="utf-8")
    verses = ih.parse_hacohen_wisdom(html, 1)
    assert verses[0][0] == 1 and verses[0][1] == 1        # (chapter, verse)
    assert verses[0][2].startswith("አ")                    # real Ge'ez text, no leading number/tags (confirm exact prefix from fixture)
    assert verses[1][1] == 2
    assert "<" not in verses[0][2] and "Nr. Vers" not in verses[0][2]
```

- [ ] **Step 3 — run, confirm FAIL** (`parse_hacohen_wisdom` undefined).

- [ ] **Step 4 — implement `parse_hacohen_wisdom`** in `scripts/ingest_hacohen.py`, modeled on `parse_hacohen_psalter` but using the verse-number + caption markup discovered in Task 0 Step 3. Reuse `_clean_fragment`, `_P_RE`, `_WS_RE`, `_TAG_RE`. If Wisdom uses the SAME `<span style="font-size:70%">N</span>` verse marker as Psalms, `parse_hacohen_wisdom` can delegate to a shared `_parse_numbered_page(page_html, chapter, *, num_re, cap_re)` helper (refactor `parse_hacohen_psalter` to call it too — keep its behavior byte-identical, re-run the psalms tests). If the marker differs, write a Wisdom-specific `_WIS_VERSENUM_RE`.

- [ ] **Step 5 — register Wisdom in `_BOOKS`** (now that the parser exists):

```python
_BOOKS["wisdom"] = {
    "book_code": "wis",
    "url": _BASE + "<WISDOM_URL_PATTERN_FROM_TASK0>/{n}.html",
    "cache_name": "<WISDOM_CACHE_NAME_FROM_TASK0> {n}.html",
    "chapters": range(1, 20),                  # 19 chapters
    "calib": [1, 9, 19],
    "parser": parse_hacohen_wisdom,
    "quality": "digitized-critical-edition",
    "provenance": "hacohen-geez",
    "docstring_extra": (
        "Ingested from Ran HaCohen's digitized Ge'ez Wisdom of Solomon "
        "(ed. <EDITOR_FROM_SOURCE>; LXX/Ethiopic numbering; PD by age). "
        "Source numbering is authoritative — NOT renumbered against the floor."
    ),
}
```

- [ ] **Step 6 — run, confirm PASS** (parser test + registry test + psalms regression all green).

- [ ] **Step 7 — commit.** `pwsh -File save.ps1 -Message "Phase D: parse_hacohen_wisdom + Wisdom registry entry (TDD on committed fixture)"`

---

## TASK 3 — `write_book_module` emits `VERSIFICATION = "own"`

**Files:** Modify `scripts/extract_parallel_pdf.py` (`write_book_module`); Test `tests/test_parser_structure_aware_prepass.py` (or wherever `write_book_module` is tested) + `tests/test_build_standalone.py`

- [ ] **Step 1 — failing test.** Assert the writer can emit the versification attribute:

```python
def test_write_book_module_emits_versification(tmp_path):
    from scripts.extract_parallel_pdf import write_book_module
    out = write_book_module("geez-tewahedo", "zzz", [(1, 1, "ሰላም")],
                            "digitized-critical-edition", "2026-05-28",
                            versification="own", out_dir=tmp_path)
    text = out.read_text(encoding="utf-8")
    assert 'VERSIFICATION = "own"' in text
    from scripts.core import translations as tx
    assert tx._load_book_attr_from_text(text, "VERSIFICATION") == "own"
```

> Confirm `write_book_module`'s real signature first (it currently takes `(translation, book, verses, quality, date, *, ingest_phase, docstring_extra, source_provenance, source_yaml_ref, tool)` per the `ingest_psalms` call site). Add a keyword-only `versification: str | None = None`; `out_dir` may already exist — if not, add it as a test-only override or write to the real store path and assert there.

- [ ] **Step 2 — run, confirm FAIL** (unexpected `versification` kwarg).

- [ ] **Step 3 — implement.** In `write_book_module`, when `versification` is not None, emit a `VERSIFICATION = "<value>"` line in the module header (next to `SOURCE_QUALITY`). Default `None` ⇒ no line ⇒ **byte-identical** output for every existing caller (verify: re-run any existing `write_book_module` test).

- [ ] **Step 4 — run, confirm PASS** (new test + existing writer tests green).

- [ ] **Step 5 — commit.** `pwsh -File save.ps1 -Message "Phase D: write_book_module optional VERSIFICATION attr (default unset = byte-identical)"`

---

## TASK 4 — fetch → calibrate → ingest `geez-tewahedo/wis.py`

**Files:** runs the generalized ingest; writes `content/translations/geez-tewahedo/wis.py` + updates `_source.yaml`

- [ ] **Step 1 — fetch the 19 Wisdom pages** (polite, cached, resumable):
Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m scripts.ingest_hacohen --book wisdom --fetch`
Expected: `cached Wisdom 1 … 19`. (The cache dir is gitignored.)

- [ ] **Step 2 — calibrate (GO/NO-GO gate):**
Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m scripts.ingest_hacohen --book wisdom --calibrate`
Expected: `GO: calibration sample parsed cleanly`. **If NO-GO → STOP** (do not ingest; report; consider Sirach instead).

- [ ] **Step 3 — ingest → write the store module:**
Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m scripts.ingest_hacohen --book wisdom --ingest --phase "D1a"`
Expected: `wrote content/translations/geez-tewahedo/wis.py` with `VERSIFICATION = "own"`, `SOURCE_QUALITY = "digitized-critical-edition"`, `SOURCE_PROVENANCE = "hacohen-geez"`, ~19 chapters.

- [ ] **Step 4 — record provenance.** Add a Wisdom block to `content/translations/sources/hacohen-geez/_source.yaml` (edition, editor, year, PD basis, URL pattern, fetch date, ingest record `D1a`) mirroring the Psalms block.

- [ ] **Step 5 — ruff-format the generated store (REQUIRED before commit):**
Run: `& "...python.exe" -m ruff format content/translations/geez-tewahedo/wis.py`
Then sanity-load: `$env:PYTHONUTF8="1"; & "...python.exe" -c "from scripts.core import translations as t; print(t.versification_of('geez-tewahedo','wis'), len(t.get_chapter('geez-tewahedo','wis',1)))"`
Expected: `own <N>` (N = Wisdom 1's verse count from the source).

- [ ] **Step 6 — sanity test + commit.** Add `tests/test_build_standalone.py::test_wisdom_is_own_versified` asserting `tx.versification_of("geez-tewahedo","wis") == "own"` and a known chapter count (19). Run it green, then:
`pwsh -File save.ps1 -Message "Phase D: ingest Ge'ez Wisdom of Solomon from HaCohen (own-versification, digitized-critical-edition)"`

---

## TASK 5 — Geʽez→KJV xref sidecar `wis_apparatus.json`

**Files:** Modify `scripts/core/standalone_store.py` (add `build_hacohen_xref_sidecar`); writes `content/translations/geez-tewahedo/wis_apparatus.json`; Test `tests/test_build_standalone.py`

- [ ] **Step 1 — failing test.** Append to `tests/test_build_standalone.py`:

```python
def test_wis_apparatus_sidecar_is_xref_only():
    import json
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent / "content" / "translations" / "geez-tewahedo" / "wis_apparatus.json"
    assert p.is_file()
    am = json.loads(p.read_text(encoding="utf-8"))
    any_ch = next(iter(am.values()))
    any_v = next(iter(any_ch.values()))
    assert "kjv" in any_v and any_v.get("apparatus") == []     # HaCohen book → no manuscript apparatus
    assert any_v.get("confidence") in ("anchored", "interpolated")
```

- [ ] **Step 2 — run, confirm FAIL** (sidecar absent).

- [ ] **Step 3 — implement `build_hacohen_xref_sidecar(book, out_dir)`** in `scripts/core/standalone_store.py`, beside the Psalms `lxx_psalms_to_kjv` generator. For each chapter of the own-vers Geʽez book, load the Geʽez verses (`translations.get_chapter("geez-tewahedo", book, ch)`) + the KJV verses (`translations.get_chapter("kjv", book, ch)` — `kjv/wis.py` exists), call `geez_kjv_xref.build_kjv_xref(geez_verses, kjv_verses, book=book, chapter=ch)` (confirm the real signature in `scripts/core/geez_kjv_xref.py`), and emit `{str(ch): {str(geez_v): {"kjv": [[book,ch,v],…], "confidence": "anchored"|"interpolated", "apparatus": []}}}`. Write `out_dir / f"{book}_apparatus.json"` (ensure_ascii=False, indent=2). Honest confidence — `anchored` only where a numeral/proper-noun matched, else `interpolated`; never fabricate.

- [ ] **Step 4 — run the generator:**
Run: `$env:PYTHONUTF8="1"; & "...python.exe" -c "from pathlib import Path; from scripts.core import standalone_store as ss; ss.build_hacohen_xref_sidecar('wis', Path('content/translations/geez-tewahedo')); print('wrote wis_apparatus.json')"`

- [ ] **Step 5 — run the test, confirm PASS.**

- [ ] **Step 6 — commit.** `pwsh -File save.ps1 -Message "Phase D: Ge'ez->KJV xref sidecar for Wisdom (geez_kjv_xref; honest confidence)"`

---

## TASK 6 — wire Wisdom into the standalone + the proof gates

**Files:** Modify `scripts/build_standalone.py:151`; Test `tests/test_build_standalone.py`

> **Safety note (overwrite):** Task 4 overwrote the old `ocr-tier3` `wis.py` (canonical) with the own-vers HaCohen `wis.py`. This is safe: `geez-tewahedo` feeds ONLY the standalone path, `wis` was NOT in `_STANDALONE_BOOKS` (so it rendered nowhere before), and there is no `geez-tewahedo-en/wis.py` keyed to the old coordinates. Confirm with `git status` that ONLY `wis.py` / `wis_apparatus.json` / `_source.yaml` changed under `content/`, and that `epub_working/` is untouched.

- [ ] **Step 1 — failing test.** Append:

```python
def test_wisdom_in_standalone_book_set():
    from scripts import build_standalone as bs
    assert "wis" in bs._STANDALONE_BOOKS
```

- [ ] **Step 2 — run, confirm FAIL.**

- [ ] **Step 3 — add `"wis"`** to `_STANDALONE_BOOKS` in `scripts/build_standalone.py:151`: `_STANDALONE_BOOKS = ["1ki", "1sa", "2sa", "psa", "wis"]`.

- [ ] **Step 4 — run the standalone test suite, confirm PASS.**
Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m pytest tests/test_build_standalone.py -v`

- [ ] **Step 5 — build the real standalone EPUB:**
Run: `$env:PYTHONUTF8="1"; & "...python.exe" -c "from pathlib import Path; from scripts import build_standalone as bs; print(bs.build_standalone('standalone-geez', Path('exports'), 'v28a'))"`
Expected: `status: ok`, `books: 5`, chapters = 161 + 19 = **180**.

- [ ] **Step 6 — epubcheck the proof EPUB at 0/0** (per memory `reference_epubcheck`, always `--jar`):
Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m scripts.run_epubcheck --jar <bundled-jar> "exports\Geez_Standalone_standalone-geez_v28a_….epub"`
Expected: `0 errors / 0 warnings`. If RSC errors appear, fix the generator/sidecar and rebuild.

- [ ] **Step 7 — prove the 9 KJV editions byte-stable.** Build a flagship + epubcheck; confirm `epub_working/` untouched:
Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m scripts.build_edition --edition catholic-study --version v28a` then epubcheck `--jar`; then `git -C "<repo>" status -- epub_working` (expect no changes).
Expected: `epubcheck 0/0/0/0`; `epub_working/` clean.

- [ ] **Step 8 — full proof-suite + lint gate.**
Run: `$env:PYTHONUTF8="1"; & "...python.exe" -m pytest tests/test_build_standalone.py tests/test_ingest_hacohen.py -q` then `& "...python.exe" scripts/lint_rules.py` then `& "...python.exe" -m ruff format --check scripts/ingest_hacohen.py scripts/core/standalone_store.py content/translations/geez-tewahedo/wis.py`
Expected: all green; lint clean (or known-benign warns); ruff clean.

- [ ] **Step 9 — update truth record + commit + back up.** Update `dev/SESSION_STATE.md` (Wisdom own-vers shipped; standalone now 5 books / 180 ch; next = Wisdom EN + Sirach), `dev/IN_FLIGHT.md`, `dev/CHANGELOG.md`.
`pwsh -File save.ps1 -Message "Phase D PROOF: Ge'ez Wisdom own-versification shipped + folded into the standalone (epubcheck 0/0; 9 editions byte-stable; standalone 5 books/180 ch)"`
Then (3rd-commit cadence / checkpoint) back up to E:/F: if mounted: `git -C "<repo>" bundle create "E:\YHWH-v2.4-repo-2026-05-28-phaseD-wisdom-<hash>.bundle" --all` + same to `F:`; `git bundle verify` each.

---

## TASK 7 — Wisdom EN back-translation (following lane)

> Per spec §11.5 + §10, EN follows the own-vers ship. Reuse the Psalms/Kings method: a translator subagent (Opus; faithful to the Geʽez wording NOT KJV/NRSV; "Yahweh"; `[brackets]` for uncertainty) reads `geez-tewahedo/wis.py` in source order → drafts `content/translations/geez-tewahedo-en/wis.py` (`VERSES=[(ch, geez_v, english)]`, same own coords, tier `ai-back-translation-reviewed-tier3`); an INDEPENDENT reviewer subagent checks each verse for faithfulness/drift/KJV-contamination → revise to convergence. Then rebuild the standalone → confirm `vnote-text` English appears in Wisdom popups → `epubcheck 0/0` + 9-editions byte-stable. Commit. (Detailed per the existing `docs/superpowers/plans/2026-05-28-geez-en-backtranslation-plan.md` method; this is its application to `wis`.)

---

## TASK 8 — Sirach (repeat the proven HaCohen lane)

> Repeat Tasks 0-7 with `sir` (Sirach, 51 chapters): recon the HaCohen Sirach URL/markup → `parse_hacohen_sirach` (or reuse the shared `_parse_numbered_page` if the markup matches) → register in `_BOOKS` → fetch/calibrate/ingest `geez-tewahedo/sir.py` (own, digitized-critical-edition) → `sir_apparatus.json` (xref vs `kjv/sir.py`) → add `"sir"` to `_STANDALONE_BOOKS` → standalone 6 books → epubcheck 0/0 + byte-stable → EN lane. This validates the per-book registry generalizes cleanly. Each step mirrors the Wisdom tasks above (no new patterns).

---

## SCALE-OUT — own detailed plans at their start (NOT in this plan's scope)

- **D1b — Patrologia vision-transcription lane (6 books: `1ch`,`2ch`,`ezr`,`neh`,`est_patrologia`,`job`).** Per the spec §11 Correction: the PO PDFs are Tesseract-OCR'd and lose the margin numerals + bleed apparatus, so own-versification needs an **Opus vision agent** reading the PO page images (the GAPS PDFs) to transcribe the Geʽez body + capture the margin Ethiopic verse numerals + EXCLUDE the French apparatus — a lighter cousin of the manuscript marathon (clean print). Output: own-vers `geez-tewahedo/<book>.py` + xref + standalone wiring + EN. Gets its own plan (`docs/superpowers/plans/<date>-geez-patrologia-vision-plan.md`) — page-location, crop discipline (≤1568px, MAX 1 heavy agent), per-chapter blind-transcribe + adversarial-review, calibrate-first per book. `job` first (HaCohen Pereira cross-validates).

- **D2 — distinctive-source acquisition (`1en`,`jub`,`mq1-3`,`4ba`).** Acquire clean PD Geʽez critical editions (1 Enoch — Charles 1906; Jubilees — Charles 1895; Meqabyan + 4 Baruch — research, may NO-GO). Per book: verify PD + clean digital text (archive.org) → calibrate-first GO/NO-GO → per-source parser → own-vers ingest → xref (Ethiopian-only books have no KJV → no xref) → standalone wiring → EN. Gets its own plan; honest deferral on NO-GO (esp. Meqabyan — the γ.4.8 source was an English CC0 translation, not Geʽez).

---

## Self-review (against spec §11 + the §11 Correction)

- **Spec coverage:** §11 D1a (HaCohen sir/wis) → Tasks 0-8 ✓; §11 mechanism (generalize source_authoritative, never renumber, VERSIFICATION="own") → Tasks 1/3/4 ✓; §11 proof = Wisdom end-to-end (parser→store→xref→render→epubcheck→byte-stable) → Tasks 2-6 ✓; §11 EN following lane → Task 7 ✓; §11 D1b Patrologia vision + D2 acquisition → Scale-out outlines (own plans, per the "expand at phase start" pattern) ✓; honesty gates (calibrate-first, 0 fabrication, confidence-tagged, byte-stable, immutable goldens) → Execution discipline + Task 6 ✓.
- **Placeholder scan:** The `<…FROM_TASK0>` tokens in Task 2 Step 5 are explicit recon-output bindings (URL pattern, cache name, editor) — genuinely data-dependent on the live HaCohen page, filled by Task 0, NOT vague TODOs. The Task-2 fixture `EXPECTED` Geʽez text is filled from the committed fixture. No hidden gaps.
- **Type/name consistency:** `_BOOKS`, `fetch_book`/`calibrate(book,…)`/`ingest_book`, `parse_hacohen_wisdom`, `write_book_module(..., versification=)`, `build_hacohen_xref_sidecar(book, out_dir)`, `_STANDALONE_BOOKS`, sidecar shape `{str(ch):{str(v):{kjv,confidence,apparatus}}}` are used consistently across tasks + match the existing code (`parse_hacohen_psalter`, `ingest_psalms`, `lxx_psalms_to_kjv`, `geez_kjv_xref.build_kjv_xref`).
- **Known execution-time confirmations (flagged, not gaps):** the HaCohen Wisdom URL pattern + verse-number markup (Task 0 recon); `write_book_module`'s exact signature + whether it takes `out_dir`; `geez_kjv_xref.build_kjv_xref`'s exact signature. Each has a "confirm the real …" note.
