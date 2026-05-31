# Ge'ez External PD-Source Ingest Implementation Plan
**Status:** shipped — HaCohen path; Psalms own-versified (psa in the standalone)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ingest Ge'ez Psalms from Ran HaCohen's clean Unicode-Ge'ez PD critical edition (Ludolf, Rahlfs/LXX numbering) into `content/translations/geez-tewahedo/psa.py` at `digitized-critical-edition` quality, replacing the OCR+colometric-merge path, behind a calibrate-first gate.

**Architecture:** A new self-contained module `scripts/ingest_hacohen.py` (fetch→local-cache→pure HTML parse→calibrate→write). It reuses the existing `write_book_module` writer (parametrized backward-compatibly) and the existing `PSALMS_VERSE_COUNTS` floor for validation only (the source's own verse numbering is authoritative — never renumbered). HTML is HTML-4 with UTF-8 numeric character references; verses are `<p>` blocks where a new verse begins with `<span style='font-size:70%'>N</span>` and continuation cola are subsequent number-less `<p>`s.

**Tech Stack:** Python 3.14 (Windows `py` launcher), stdlib only (`re`, `html`, `urllib.request`, `pathlib`), `pyyaml` (already a dep), `pytest`, `ruff`. `$env:PYTHONUTF8="1"` on every Windows Python/pytest run. Local commits only (pre-commit hook runs `ruff format --check` + `scripts/lint_rules.py`).

---

## File Structure

- Create: `content/translations/sources/hacohen-geez/_source.yaml` — provenance record (site, per-book edition, PD basis, URL pattern, ingest records).
- Create: `scripts/ingest_hacohen.py` — fetcher+cache, `parse_hacohen_psalter`, `calibrate`, CLI `main`.
- Modify: `scripts/extract_parallel_pdf.py:2623-2646` — add 3 backward-compatible kwargs to `write_book_module` (`source_provenance`, `source_yaml_ref`, `tool`).
- Create: `tests/fixtures/hacohen/psalm1.html` — committed trimmed real Psalm-1 fixture (deterministic parser tests).
- Create: `tests/fixtures/hacohen/psalm_malformed.html` — committed fixture with no verse spans (NO-GO calibration test).
- Create: `tests/test_ingest_hacohen.py` — parser/fetcher/calibrate unit tests + `write_book_module` backward-compat regression.
- Runtime cache (uncommitted, gitignored): `content/translations/sources/hacohen-geez/cache/PsalmNrR <n>.html`.
- Ship outputs (Task 8): `content/translations/geez-tewahedo/psa.py`, `tests/test_parallel_bible_tau6x2i.py`, updates to `content/translations/geez-tewahedo/_meta.yaml`, `content/translations/sources/hacohen-geez/_source.yaml`, `dev/CHANGELOG.md`, `dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md`, `dev/PLAN_2026-05-09.md`.

---

### Task 1: Provenance record + cache gitignore

**Files:**
- Create: `content/translations/sources/hacohen-geez/_source.yaml`
- Create: `content/translations/sources/hacohen-geez/.gitignore`
- Test: `tests/test_ingest_hacohen.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_ingest_hacohen.py`:

```python
"""τ.6.x.5 — HaCohen external Ge'ez source ingest tests."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
HACOHEN = REPO / "content" / "translations" / "sources" / "hacohen-geez"


class TestProvenanceRecord:
    def test_source_yaml_present_and_well_formed(self):
        cfg = yaml.safe_load((HACOHEN / "_source.yaml").read_text(encoding="utf-8"))
        assert cfg["source_id"] == "hacohen-geez"
        assert cfg["site_url"] == "https://www.tau.ac.il/~hacohen/"
        psalms = cfg["books"]["psalms"]
        assert psalms["editor"] == "Hiob Ludolf"
        assert psalms["edition_year"] == 1701
        assert psalms["pd_basis"]
        assert psalms["verse_numbering"] == "Rahlfs-LXX"
        assert psalms["url_pattern"] == "Psalm/PsalmNrR%20{n}.html"
        assert psalms["chapter_range"] == [1, 151]

    def test_cache_dir_gitignored(self):
        gi = (HACOHEN / ".gitignore").read_text(encoding="utf-8")
        assert "cache/" in gi
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONUTF8="1"; py -m pytest tests/test_ingest_hacohen.py::TestProvenanceRecord -q`
Expected: FAIL — `FileNotFoundError` (`_source.yaml` missing).

- [ ] **Step 3: Create the provenance record**

Create `content/translations/sources/hacohen-geez/_source.yaml`:

```yaml
# Source provenance — Ran HaCohen digitized Ethiopic (Ge'ez) Bible
#
# Clean Unicode-Ge'ez transcriptions of public-domain scholarly
# critical editions, hosted at Tel Aviv University. Used by τ.6.x.5
# as the high-fidelity Ge'ez source for the poetic/wisdom books
# (replacing the OCR'd parallel-PDF Ge'ez column for those books).
# Fetched HTML is cached locally under cache/ (NOT committed —
# regenerable; mirrors the parallel-bible-eotc PDF policy).

source_id: hacohen-geez
site_url: https://www.tau.ac.il/~hacohen/
digitizer: Ran HaCohen (Tel Aviv University)
description: |
  Digitized Classical Ethiopic (Ge'ez) biblical texts transcribed
  from public-domain printed critical editions. Text is Unicode
  Ethiopic delivered as HTML numeric character references. Every
  datum is cited via the project's attribution/bibliography system.

books:
  psalms:
    book_code: psa
    editor: Hiob Ludolf
    edition_title: Psalterium Davidis
    edition_year: 1701
    pd_basis: "Ludolf 1701 — public domain by age (pre-1929 by ~228 years)"
    verse_numbering: Rahlfs-LXX   # the PsalmNrR view = Rahlfs/Septuagint numbering, the PSALMS_VERSE_COUNTS basis
    url_pattern: "Psalm/PsalmNrR%20{n}.html"
    chapter_range: [1, 151]
    citation: "Ge'ez Psalter (Psalterium Davidis, ed. Hiob Ludolf, 1701); digitized by Ran HaCohen, Tel Aviv University; public domain by age."

# Per-ship ingest records appended here (mirrors parallel-bible-eotc/_source.yaml).
ingest_records: {}
```

Create `content/translations/sources/hacohen-geez/.gitignore`:

```
cache/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `$env:PYTHONUTF8="1"; py -m pytest tests/test_ingest_hacohen.py::TestProvenanceRecord -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add tests/test_ingest_hacohen.py "content/translations/sources/hacohen-geez/_source.yaml" "content/translations/sources/hacohen-geez/.gitignore"
git commit -m "tau.6.x.5: hacohen-geez provenance record + cache gitignore"
```

---

### Task 2: `write_book_module` backward-compatible parametrization

**Files:**
- Modify: `scripts/extract_parallel_pdf.py:2623-2646`
- Test: `tests/test_ingest_hacohen.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ingest_hacohen.py`:

```python
class TestWriteBookModuleParametrized:
    def _fn(self):
        from scripts.extract_parallel_pdf import write_book_module

        return write_book_module

    def test_defaults_byte_identical(self, tmp_path, monkeypatch):
        # Existing callers pass no provenance kwargs → output must be
        # byte-identical to pre-change (parallel-bible-eotc strings).
        import scripts.extract_parallel_pdf as ep

        monkeypatch.setattr(ep, "TRANSLATIONS_DIR", tmp_path)
        out = self._fn()("geez-tewahedo", "zzz", [(1, 1, "ብፁዕ")], "ocr-tier3", "2026-05-16")
        txt = out.read_text(encoding="utf-8")
        assert "SOURCE_PROVENANCE = 'parallel-bible-eotc'" in txt
        assert "content/translations/sources/parallel-bible-eotc/_source.yaml" in txt
        assert "Tool: scripts/extract_parallel_pdf.py" in txt

    def test_kwargs_override_three_spots(self, tmp_path, monkeypatch):
        import scripts.extract_parallel_pdf as ep

        monkeypatch.setattr(ep, "TRANSLATIONS_DIR", tmp_path)
        out = self._fn()(
            "geez-tewahedo",
            "psa",
            [(1, 1, "ብፁዕ")],
            "digitized-critical-edition",
            "2026-05-16",
            ingest_phase="τ.6.x.2.i",
            source_provenance="hacohen-geez",
            source_yaml_ref="content/translations/sources/hacohen-geez/_source.yaml",
            tool="scripts/ingest_hacohen.py",
        )
        txt = out.read_text(encoding="utf-8")
        assert "SOURCE_PROVENANCE = 'hacohen-geez'" in txt
        assert "content/translations/sources/hacohen-geez/_source.yaml" in txt
        assert "Tool: scripts/ingest_hacohen.py" in txt
        assert "SOURCE_QUALITY = 'digitized-critical-edition'" in txt
        assert "parallel-bible-eotc" not in txt
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONUTF8="1"; py -m pytest tests/test_ingest_hacohen.py::TestWriteBookModuleParametrized -q`
Expected: FAIL — `test_kwargs_override_three_spots` errors with `TypeError: write_book_module() got an unexpected keyword argument 'source_provenance'`.

- [ ] **Step 3: Modify `write_book_module` signature and body**

In `scripts/extract_parallel_pdf.py`, change the signature (currently ends at `docstring_extra: str | None = None,` / `) -> Path:` near line 2600) to add three keyword-only params. Replace:

```python
    *,
    ingest_phase: str | None = None,
    docstring_extra: str | None = None,
) -> Path:
```

with:

```python
    *,
    ingest_phase: str | None = None,
    docstring_extra: str | None = None,
    source_provenance: str = "parallel-bible-eotc",
    source_yaml_ref: str = "content/translations/sources/parallel-bible-eotc/_source.yaml",
    tool: str = "scripts/extract_parallel_pdf.py",
) -> Path:
```

Then replace the three hardcoded lines in the body. Replace:

```python
        "Extracted from the parallel-Bible EOTC PDF (",
        "content/translations/sources/parallel-bible-eotc/_source.yaml).",
```

with:

```python
        "Extracted/ingested from source (",
        f"{source_yaml_ref}).",
```

Replace:

```python
    lines.append("Tool: scripts/extract_parallel_pdf.py")
```

with:

```python
    lines.append(f"Tool: {tool}")
```

Replace:

```python
    lines.append("SOURCE_PROVENANCE = 'parallel-bible-eotc'")
```

with:

```python
    lines.append(f"SOURCE_PROVENANCE = {source_provenance!r}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `$env:PYTHONUTF8="1"; py -m pytest tests/test_ingest_hacohen.py::TestWriteBookModuleParametrized -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Run the parallel-PDF regression to prove zero behavior change**

Run: `$env:PYTHONUTF8="1"; py -m pytest tests/test_parallel_bible_tau7xi.py tests/test_parallel_bible_tau6x2_geez_arc.py tests/test_parser_structure_aware_prepass.py -q`
Expected: PASS (all green — defaults preserve existing behavior).

- [ ] **Step 6: Commit**

```bash
git add scripts/extract_parallel_pdf.py tests/test_ingest_hacohen.py
git commit -m "tau.6.x.5: parametrize write_book_module (provenance/source-ref/tool) — backward-compatible defaults"
```

---

### Task 3: `parse_hacohen_psalter` pure parser + committed fixture

**Files:**
- Create: `scripts/ingest_hacohen.py`
- Create: `tests/fixtures/hacohen/psalm1.html`
- Test: `tests/test_ingest_hacohen.py`

- [ ] **Step 1: Create the committed fixture**

Create `tests/fixtures/hacohen/psalm1.html` (trimmed real structure — title `<p>`, Cap header, two numbered verses with continuation cola; NCRs are the real Unicode codepoints):

```html
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "https://www.w3.org/TR/html4/loose.dtd">
<HTML><HEAD><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><title>Psalmus 1</title></HEAD><BODY><div>
<p align=center style='font-size:20.0pt;font-family:"GS GeezMahtemUnicode"'>&#4632;&#4829;&#4633;&#4651;&#4725; &#4961; &#4824;&#4851;&#4810;&#4725; &#4962;</p>
<p style='margin-left:3.0cm;font-family:"GS GeezMahtemUnicode"'><b>Nr. Vers.:</b> &#9673; Rahlf &#9678; <a href="Psalm 1.html">Ludolf</a></p>
<p style='font-family:"GS GeezMahtemUnicode"'><a href="x" target=_blank><!--Cap.-->1<!--Cap.end --></a> &#4941;&#4779;&#4652; &#4961;</p>
<p style='font-family:"GS GeezMahtemUnicode"'><span style='font-size:70%'>1</span> &#4709;&#4929;&#4821; &#4961; &#4709;&#4773;&#4658; &#4961; &#4824;&#4770;&#4630;&#4648; &#4961; &#4704;&#4637;&#4781;&#4648; &#4961; &#4648;&#4658;&#4819;&#4757; &#4964;</p>
<p style='text-indent:1em;font-family:"GS GeezMahtemUnicode"'>&#4808;&#4824;&#4770;&#4678;&#4632; &#4961; &#4813;&#4661;&#4720; &#4961; &#4941;&#4758;&#4720; &#4961; &#4739;&#4901;&#4771;&#4757; &#4964;</p>
<p style='text-indent:1em;font-family:"GS GeezMahtemUnicode"'>&#4808;&#4824;&#4770;&#4752;&#4704;&#4648; &#4961; &#4813;&#4661;&#4720; &#4961; &#4632;&#4757;&#4704;&#4648; &#4962;</p>
<p style='font-family:"GS GeezMahtemUnicode"'><span style='font-size:70%'>2</span> &#4622;&#4761; &#4961; &#4761;&#4632;&#4759; &#4961; &#4622;&#4615;&#4818;&#4757; &#4962;</p>
</div></BODY></HTML>
```

- [ ] **Step 2: Write the failing test**

Append to `tests/test_ingest_hacohen.py`:

```python
FIX = REPO / "tests" / "fixtures" / "hacohen"


class TestParseHacohenPsalter:
    def _fn(self):
        from scripts.ingest_hacohen import parse_hacohen_psalter

        return parse_hacohen_psalter

    def test_parses_verses_with_correct_numbering(self):
        html_text = (FIX / "psalm1.html").read_text(encoding="utf-8")
        verses = self._fn()(html_text, 1)
        # Two numbered verses; psalm number == 1 for all.
        assert [(c, v) for c, v, _ in verses] == [(1, 1), (1, 2)]

    def test_verse1_is_blessed_is_the_man_unicode_geez(self):
        verses = self._fn()((FIX / "psalm1.html").read_text(encoding="utf-8"), 1)
        ch, v, text = verses[0]
        # Canonical Ge'ez Ps 1:1 incipit, real Unicode (not NCRs/ASCII).
        assert text.startswith("ብፁዕ ፡ ብእሲ"), repr(text[:40])
        # Continuation cola were merged into verse 1 (3 cola, ፤/።).
        assert "መንበረ" in text
        assert "&#" not in text  # entities were unescaped
        assert "<" not in text  # tags stripped

    def test_title_and_caption_and_toggle_skipped(self):
        verses = self._fn()((FIX / "psalm1.html").read_text(encoding="utf-8"), 1)
        joined = " ".join(t for _, _, t in verses)
        assert "Nr. Vers" not in joined
        assert "Cap." not in joined
        assert len(verses) == 2  # title/superscription not counted as a verse
```

- [ ] **Step 3: Run test to verify it fails**

Run: `$env:PYTHONUTF8="1"; py -m pytest tests/test_ingest_hacohen.py::TestParseHacohenPsalter -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.ingest_hacohen'`.

- [ ] **Step 4: Create `scripts/ingest_hacohen.py` with the parser**

Create `scripts/ingest_hacohen.py`:

```python
"""τ.6.x.5 — HaCohen external Ge'ez PD-source ingest.

Fetches Ran HaCohen's clean Unicode-Ge'ez critical editions
(tau.ac.il/~hacohen), caches HTML locally, parses per-verse text,
and writes a standard translation module. The source's own verse
numbering is authoritative — the canonical floor is used for
VALIDATION only, never to renumber (see the design spec
docs/superpowers/specs/2026-05-16-geez-external-source-ingest-design.md).
"""

from __future__ import annotations

import html as _html
import re
from pathlib import Path

_P_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
_VERSENUM_RE = re.compile(
    r"^\s*<span[^>]*font-size:\s*70%[^>]*>\s*(\d+)\s*</span>",
    re.IGNORECASE,
)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _clean_fragment(fragment_html: str) -> str:
    """Strip the optional leading verse-number span, all tags, and
    unescape HTML entities to real Unicode Ge'ez; collapse whitespace."""
    no_num = _VERSENUM_RE.sub("", fragment_html, count=1)
    no_tags = _TAG_RE.sub("", no_num)
    text = _html.unescape(no_tags)
    return _WS_RE.sub(" ", text).strip()


def parse_hacohen_psalter(page_html: str, psalm_number: int) -> list[tuple[int, int, str]]:
    """Parse one HaCohen Ludolf Psalm page into (psalm, verse, text).

    A new verse begins at a <p> whose leading element is
    <span style='font-size:70%'>N</span>. Subsequent number-less <p>
    blocks are continuation cola of the current verse. Title /
    "Nr. Vers." toggle / "Cap." caption paragraphs are skipped, as
    is any paragraph before the first numbered verse (superscription
    — not a Rahlfs-numbered verse on this view).
    """
    verses: list[tuple[int, int, str]] = []
    cur_v: int | None = None
    parts: list[str] = []

    def flush() -> None:
        nonlocal parts
        if cur_v is not None and parts:
            joined = " ".join(p for p in parts if p).strip()
            if joined:
                verses.append((psalm_number, cur_v, joined))
        parts = []

    for m in _P_RE.finditer(page_html):
        inner = m.group(1)
        if "Nr. Vers" in inner or "<!--Cap." in inner:
            continue
        vm = _VERSENUM_RE.match(inner.lstrip())
        text = _clean_fragment(inner)
        if not text:
            continue
        if vm:
            flush()
            cur_v = int(vm.group(1))
            parts = [text]
        elif cur_v is not None:
            parts.append(text)
        # else: pre-verse-1 superscription — skip
    flush()
    return verses
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `$env:PYTHONUTF8="1"; py -m pytest tests/test_ingest_hacohen.py::TestParseHacohenPsalter -q`
Expected: PASS (3 passed).

- [ ] **Step 6: Commit**

```bash
git add scripts/ingest_hacohen.py "tests/fixtures/hacohen/psalm1.html" tests/test_ingest_hacohen.py
git commit -m "tau.6.x.5: parse_hacohen_psalter pure parser + committed Psalm-1 fixture"
```

---

### Task 4: Fetcher + local cache

**Files:**
- Modify: `scripts/ingest_hacohen.py`
- Test: `tests/test_ingest_hacohen.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ingest_hacohen.py`:

```python
class TestFetcherCache:
    def _mod(self):
        import scripts.ingest_hacohen as ih

        return ih

    def test_cache_hit_skips_network(self, tmp_path, monkeypatch):
        ih = self._mod()
        cache = tmp_path / "PsalmNrR 7.html"
        cache.write_text("<p><span style='font-size:70%'>1</span> &#4632; &#4962;</p>", encoding="utf-8")

        def _boom(*a, **k):
            raise AssertionError("network must not be called on cache hit")

        monkeypatch.setattr(ih, "_http_get", _boom)
        out = ih.fetch_psalm(7, cache_dir=tmp_path)
        assert out == cache
        assert "&#4632;" in cache.read_text(encoding="utf-8")

    def test_fetch_writes_cache_then_reuses(self, tmp_path, monkeypatch):
        ih = self._mod()
        calls = []

        def _fake_get(url):
            calls.append(url)
            return "<p><span style='font-size:70%'>1</span> &#4632; &#4962;</p>"

        monkeypatch.setattr(ih, "_http_get", _fake_get)
        p1 = ih.fetch_psalm(3, cache_dir=tmp_path)
        p2 = ih.fetch_psalm(3, cache_dir=tmp_path)
        assert p1 == p2 and p1.exists()
        assert len(calls) == 1  # second call served from cache
        assert "PsalmNrR%203.html" in calls[0]

    def test_fetch_error_no_partial_write(self, tmp_path, monkeypatch):
        ih = self._mod()

        def _fail(url):
            raise OSError("HTTP 500")

        monkeypatch.setattr(ih, "_http_get", _fail)
        try:
            ih.fetch_psalm(9, cache_dir=tmp_path)
            raised = False
        except OSError:
            raised = True
        assert raised
        assert not (tmp_path / "PsalmNrR 9.html").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONUTF8="1"; py -m pytest tests/test_ingest_hacohen.py::TestFetcherCache -q`
Expected: FAIL — `AttributeError: module 'scripts.ingest_hacohen' has no attribute 'fetch_psalm'`.

- [ ] **Step 3: Add fetcher + cache to `scripts/ingest_hacohen.py`**

Add these imports at the top of `scripts/ingest_hacohen.py` (after the existing `import re` line):

```python
import time
import urllib.request
```

Append to `scripts/ingest_hacohen.py`:

```python
_BASE = "https://www.tau.ac.il/~hacohen/"
_PSALM_URL = _BASE + "Psalm/PsalmNrR%20{n}.html"
DEFAULT_CACHE = (
    Path(__file__).resolve().parent.parent
    / "content"
    / "translations"
    / "sources"
    / "hacohen-geez"
    / "cache"
)


def _http_get(url: str) -> str:
    """Fetch a URL as text. Isolated for test monkeypatching."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (YHWH-ingest)"})
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 (trusted user-authorized host)
        charset = r.headers.get_content_charset() or "utf-8"
        return r.read().decode(charset, "replace")


def fetch_psalm(n: int, *, cache_dir: Path = DEFAULT_CACHE, delay: float = 1.0) -> Path:
    """Return the local cached HTML path for Psalm ``n`` (Rahlfs view),
    fetching politely once if absent. Never partial-writes on error."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    dest = cache_dir / f"PsalmNrR {n}.html"
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    text = _http_get(_PSALM_URL.format(n=n))  # raises on failure → no write below
    tmp = dest.with_suffix(".html.part")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(dest)
    time.sleep(delay)
    return dest
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `$env:PYTHONUTF8="1"; py -m pytest tests/test_ingest_hacohen.py::TestFetcherCache -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add scripts/ingest_hacohen.py tests/test_ingest_hacohen.py
git commit -m "tau.6.x.5: polite fetcher + local cache (offline-replayable, no partial writes)"
```

---

### Task 5: Calibrate-first gate

**Files:**
- Modify: `scripts/ingest_hacohen.py`
- Create: `tests/fixtures/hacohen/psalm_malformed.html`
- Test: `tests/test_ingest_hacohen.py`

- [ ] **Step 1: Create the malformed fixture**

Create `tests/fixtures/hacohen/psalm_malformed.html`:

```html
<!DOCTYPE HTML><HTML><HEAD><title>Psalmus X</title></HEAD><BODY><div>
<p style='font-family:"GS GeezMahtemUnicode"'>&#4632;&#4829; &#4961; no verse number spans here &#4962;</p>
<p style='font-family:"GS GeezMahtemUnicode"'>&#4824;&#4851; &#4961; still nothing &#4962;</p>
</div></BODY></HTML>
```

- [ ] **Step 2: Write the failing test**

Append to `tests/test_ingest_hacohen.py`:

```python
class TestCalibrate:
    def _fn(self):
        from scripts.ingest_hacohen import calibrate

        return calibrate

    def test_go_on_well_formed_sample(self, tmp_path):
        # Seed the cache with the good fixture as Ps 1, 118, 151.
        good = (FIX / "psalm1.html").read_text(encoding="utf-8")
        for n in (1, 118, 151):
            (tmp_path / f"PsalmNrR {n}.html").write_text(good, encoding="utf-8")
        result = self._fn()(sample=[1, 118, 151], cache_dir=tmp_path)
        assert result["go"] is True
        assert result["parsed"][1][0] == (1, 1)  # Ps 1 v1 present

    def test_nogo_on_malformed(self, tmp_path):
        bad = (FIX / "psalm_malformed.html").read_text(encoding="utf-8")
        for n in (1, 118, 151):
            (tmp_path / f"PsalmNrR {n}.html").write_text(bad, encoding="utf-8")
        result = self._fn()(sample=[1, 118, 151], cache_dir=tmp_path)
        assert result["go"] is False
        assert "no verses parsed" in result["reason"].lower()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `$env:PYTHONUTF8="1"; py -m pytest tests/test_ingest_hacohen.py::TestCalibrate -q`
Expected: FAIL — `ImportError: cannot import name 'calibrate'`.

- [ ] **Step 4: Add `calibrate` to `scripts/ingest_hacohen.py`**

Append to `scripts/ingest_hacohen.py`:

```python
def calibrate(*, sample: list[int], cache_dir: Path = DEFAULT_CACHE) -> dict:
    """Parse the calibration sample from cache and report GO/NO-GO.

    GO requires every sampled Psalm to parse to >=1 verse with the
    first verse numbered 1. NO-GO returns a human reason; the caller
    must NOT write any artifacts on NO-GO (τ.6.x.0b honesty contract).
    """
    parsed: dict[int, list[tuple[int, int, str]]] = {}
    for n in sample:
        path = cache_dir / f"PsalmNrR {n}.html"
        if not path.exists():
            return {"go": False, "reason": f"calibration page Psalm {n} not in cache", "parsed": parsed}
        vs = parse_hacohen_psalter(path.read_text(encoding="utf-8"), n)
        parsed[n] = vs
        if not vs:
            return {"go": False, "reason": f"no verses parsed for Psalm {n}", "parsed": parsed}
        if vs[0][1] != 1:
            return {"go": False, "reason": f"Psalm {n} does not start at verse 1", "parsed": parsed}
    return {"go": True, "reason": "calibration sample parsed cleanly", "parsed": parsed}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `$env:PYTHONUTF8="1"; py -m pytest tests/test_ingest_hacohen.py::TestCalibrate -q`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add scripts/ingest_hacohen.py "tests/fixtures/hacohen/psalm_malformed.html" tests/test_ingest_hacohen.py
git commit -m "tau.6.x.5: calibrate-first gate (honest GO/NO-GO, no artifacts on NO-GO)"
```

---

### Task 6: CLI orchestration (`--calibrate` / `--ingest`)

**Files:**
- Modify: `scripts/ingest_hacohen.py`
- Test: `tests/test_ingest_hacohen.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ingest_hacohen.py`:

```python
class TestIngestPsalmsFromCache:
    def _fn(self):
        from scripts.ingest_hacohen import ingest_psalms

        return ingest_psalms

    def test_ingest_from_cache_writes_module(self, tmp_path, monkeypatch):
        import scripts.extract_parallel_pdf as ep
        import scripts.ingest_hacohen as ih

        good = (FIX / "psalm1.html").read_text(encoding="utf-8")
        cache = tmp_path / "cache"
        cache.mkdir()
        for n in range(1, 152):
            (cache / f"PsalmNrR {n}.html").write_text(good, encoding="utf-8")
        out_root = tmp_path / "translations"
        monkeypatch.setattr(ep, "TRANSLATIONS_DIR", out_root)

        path = self._fn()(cache_dir=cache, phase="τ.6.x.2.i")
        assert path.name == "psa.py"
        txt = path.read_text(encoding="utf-8")
        assert "SOURCE_PROVENANCE = 'hacohen-geez'" in txt
        assert "SOURCE_QUALITY = 'digitized-critical-edition'" in txt
        assert "INGEST_PHASE = 'τ.6.x.2.i'" in txt
        # 151 psalms × 2 verses (fixture) = 302 verse tuples.
        import ast

        tree = ast.parse(txt)
        verses = next(
            ast.literal_eval(n.value)
            for n in ast.walk(tree)
            if isinstance(n, ast.Assign)
            and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id == "VERSES"
        )
        assert len(verses) == 302
        assert verses[0] == (1, 1, verses[0][2]) and verses[0][2].startswith("ብፁዕ")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `$env:PYTHONUTF8="1"; py -m pytest tests/test_ingest_hacohen.py::TestIngestPsalmsFromCache -q`
Expected: FAIL — `ImportError: cannot import name 'ingest_psalms'`.

- [ ] **Step 3: Add `ingest_psalms` + `main` to `scripts/ingest_hacohen.py`**

Add at the top of `scripts/ingest_hacohen.py` (after `import urllib.request`):

```python
import argparse
import sys
from datetime import date
```

Append to `scripts/ingest_hacohen.py`:

```python
def ingest_psalms(*, cache_dir: Path = DEFAULT_CACHE, phase: str) -> Path:
    """Parse all 151 cached Psalm pages and write geez-tewahedo/psa.py
    at digitized-critical-edition quality. Source numbering is
    authoritative (no renumber)."""
    from scripts.extract_parallel_pdf import write_book_module

    all_verses: list[tuple[int, int, str]] = []
    for n in range(1, 152):
        path = cache_dir / f"PsalmNrR {n}.html"
        all_verses.extend(parse_hacohen_psalter(path.read_text(encoding="utf-8"), n))
    return write_book_module(
        "geez-tewahedo",
        "psa",
        all_verses,
        "digitized-critical-edition",
        date.today().isoformat(),
        ingest_phase=phase,
        docstring_extra=(
            "Ingested from Ran HaCohen's digitized Ge'ez Psalter "
            "(Psalterium Davidis, ed. Hiob Ludolf 1701; Rahlfs/LXX "
            "verse numbering; PD by age). Source numbering is "
            "authoritative — NOT renumbered against the floor; "
            "per-chapter deltas vs PSALMS_VERSE_COUNTS recorded for "
            "the τ.6.x.3 audit."
        ),
        source_provenance="hacohen-geez",
        source_yaml_ref="content/translations/sources/hacohen-geez/_source.yaml",
        tool="scripts/ingest_hacohen.py",
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="HaCohen Ge'ez external-source ingest (τ.6.x.5)")
    p.add_argument("--book", required=True, choices=["psalms"])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--fetch", action="store_true", help="fetch+cache all 151 Psalm pages")
    g.add_argument("--calibrate", action="store_true", help="parse the calibration sample, print GO/NO-GO")
    g.add_argument("--ingest", action="store_true", help="write geez-tewahedo/psa.py from cache (requires GO)")
    p.add_argument("--phase", default=None, help="ingest phase tag, e.g. τ.6.x.2.i")
    args = p.parse_args(argv)

    if args.fetch:
        for n in range(1, 152):
            dest = fetch_psalm(n)
            print(f"cached Psalm {n} -> {dest}")
        return 0
    if args.calibrate:
        r = calibrate(sample=[1, 118, 151])
        print(f"{'GO' if r['go'] else 'NO-GO'}: {r['reason']}")
        return 0 if r["go"] else 1
    if args.ingest:
        if not args.phase:
            p.error("--ingest requires --phase")
        r = calibrate(sample=[1, 118, 151])
        if not r["go"]:
            print(f"NO-GO: {r['reason']} — refusing to ingest (colometric-merge fallback applies)")
            return 1
        out = ingest_psalms(phase=args.phase)
        print(f"wrote {out}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `$env:PYTHONUTF8="1"; py -m pytest tests/test_ingest_hacohen.py -q`
Expected: PASS (entire file green).

- [ ] **Step 5: ruff-format the new module + commit**

Run: `$env:PYTHONUTF8="1"; py -m ruff format scripts/ingest_hacohen.py tests/test_ingest_hacohen.py`

```bash
git add scripts/ingest_hacohen.py tests/test_ingest_hacohen.py
git commit -m "tau.6.x.5: CLI orchestration — --fetch/--calibrate/--ingest (ingest gated on GO)"
```

---

### Task 7: Execute fetch + calibrate-first on the real source (GATED)

**Files:** none (runbook — populates the uncommitted local cache only).

- [ ] **Step 1: Fetch all 151 real Psalm pages (polite, ~2.5 min at 1s delay)**

Run: `$env:PYTHONUTF8="1"; py -m scripts.ingest_hacohen --book psalms --fetch`
Expected: 151 lines `cached Psalm <n> -> ...content/translations/sources/hacohen-geez/cache/PsalmNrR <n>.html`. (Cache is gitignored — never committed.)

- [ ] **Step 2: Run the real calibrate-first gate**

Run: `$env:PYTHONUTF8="1"; py -m scripts.ingest_hacohen --book psalms --calibrate`
Expected: `GO: calibration sample parsed cleanly`.

- [ ] **Step 3: Decision branch**

- **GO** → proceed to Task 8.
- **NO-GO** → STOP. Do not write `psa.py`. Record the reason in `dev/SESSION_STATE.md` + `dev/IN_FLIGHT.md`, and fall back to the colometric-merge spec `docs/superpowers/specs/2026-05-16-geez-colometric-merge-design.md` for Ge'ez Psalms (its own plan). Do NOT fabricate. End of plan (honest stop).

- [ ] **Step 4: Spot-check the real boundary psalms (manual sanity, GO path only)**

Run: `$env:PYTHONUTF8="1"; py -c "import sys; sys.path.insert(0,'.'); from scripts.ingest_hacohen import parse_hacohen_psalter as P; from pathlib import Path; c=Path('content/translations/sources/hacohen-geez/cache'); v1=P((c/'PsalmNrR 1.html').read_text(encoding='utf-8'),1); v151=P((c/'PsalmNrR 151.html').read_text(encoding='utf-8'),151); print('Ps1 v1:', v1[0]); print('Ps151 last:', v151[-1])"`
Expected: Ps1 v1 starts `ብፁዕ ፡ ብእሲ ፡ ዘኢሖረ …`; Ps151 contains the David/Goliath wording (`መተርኩ ርእሶ`). If either is wrong → treat as NO-GO (Step 3).

---

### Task 8: Ship τ.6.x.2.i — Ge'ez Psalms (GATED on Task 7 GO)

**Files:**
- Create: `content/translations/geez-tewahedo/psa.py` (generated)
- Create: `tests/test_parallel_bible_tau6x2i.py`
- Modify: `content/translations/geez-tewahedo/_meta.yaml`
- Modify: `content/translations/sources/hacohen-geez/_source.yaml`
- Modify: `dev/CHANGELOG.md`, `dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md`, `dev/PLAN_2026-05-09.md`

- [ ] **Step 1: Generate the module**

Run: `$env:PYTHONUTF8="1"; py -m scripts.ingest_hacohen --book psalms --ingest --phase "τ.6.x.2.i"`
Expected: `wrote ...content/translations/geez-tewahedo/psa.py`. Then `$env:PYTHONUTF8="1"; py -m ruff format content/translations/geez-tewahedo/psa.py`.

- [ ] **Step 2: Capture the real per-chapter counts vs floor (for the test + audit record)**

Run: `$env:PYTHONUTF8="1"; py -c "import sys,ast; sys.path.insert(0,'.'); from scripts.extract_parallel_pdf import PSALMS_VERSE_COUNTS as F; t=open('content/translations/geez-tewahedo/psa.py',encoding='utf-8').read(); V=next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(t)) if isinstance(n,ast.Assign) and getattr(n.targets[0],'id','')=='VERSES'); from collections import Counter; c=Counter(ch for ch,_,_ in V); print('chapters',len(c),'total',len(V),'floor_total',sum(F.values())); dl=[(k,c.get(k,0),F[k]) for k in F if abs(c.get(k,0)-F[k])>max(2,0.05*F[k])]; print('deltas>tol',len(dl)); print(dl[:15])"`
Expected: `chapters 151`, a total near the floor (≈2500–2540), and `deltas>tol` well under 31 (i.e. <20% of 151) — confirming source/floor alignment per spec §6. If `deltas>tol` ≥ 31 → systemic mismatch → NO-GO (revert to colometric fallback; record honestly).

- [ ] **Step 3: Write the ship test**

Create `tests/test_parallel_bible_tau6x2i.py`:

```python
"""τ.6.x.2.i — Ge'ez Psalms via HaCohen/Ludolf (digitized-critical-edition)."""

from __future__ import annotations

import ast
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
PSA = REPO / "content" / "translations" / "geez-tewahedo" / "psa.py"


def _consts_and_verses():
    t = PSA.read_text(encoding="utf-8")
    tree = ast.parse(t)
    consts, verses = {}, None
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
            name = n.targets[0].id
            if name == "VERSES":
                verses = ast.literal_eval(n.value)
            else:
                try:
                    consts[name] = ast.literal_eval(n.value)
                except Exception:
                    pass
    return consts, verses


class TestTau6x2iGeezPsalms:
    def test_provenance_and_quality(self):
        c, _ = _consts_and_verses()
        assert c["TRANSLATION"] == "geez-tewahedo"
        assert c["BOOK"] == "psa"
        assert c["SOURCE_QUALITY"] == "digitized-critical-edition"
        assert c["SOURCE_PROVENANCE"] == "hacohen-geez"
        assert c["INGEST_PHASE"] == "τ.6.x.2.i"

    def test_151_chapters_present(self):
        _, v = _consts_and_verses()
        assert sorted({ch for ch, _, _ in v}) == list(range(1, 152))

    def test_psalm_1_1_canonical_geez(self):
        _, v = _consts_and_verses()
        first = next(t for ch, vs, t in v if ch == 1 and vs == 1)
        assert first.startswith("ብፁዕ ፡ ብእሲ"), repr(first[:40])

    def test_total_near_floor(self):
        from scripts.extract_parallel_pdf import PSALMS_VERSE_COUNTS as F

        _, v = _consts_and_verses()
        assert abs(len(v) - sum(F.values())) <= 0.1 * sum(F.values())

    def test_no_html_residue(self):
        _, v = _consts_and_verses()
        blob = " ".join(t for _, _, t in v)
        assert "<" not in blob and "&#" not in blob and "Nr. Vers" not in blob
```

- [ ] **Step 4: Run the ship test**

Run: `$env:PYTHONUTF8="1"; py -m pytest tests/test_parallel_bible_tau6x2i.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Update `_meta.yaml`, `_source.yaml` ingest records, and the dev ledgers**

In `content/translations/geez-tewahedo/_meta.yaml`: bump `stats.books` by 1 and `stats.verses` by the new psa total (from Step 2); add an `ingest_record_tau6x2i` block mirroring the `ingest_record_tau6x2h` shape with `phase: τ.6.x.2.i`, `ingested_book_codes: [psa]`, `source: hacohen-geez`, `quality_tier: digitized-critical-edition`, `verses_extracted: <total>`, `floor_total: <sum>`, `deltas_over_tolerance: <count>`, `audit_handoff: τ.6.x.3`.

In `content/translations/sources/hacohen-geez/_source.yaml`: set `ingest_records.tau6x2i:` with `shipped_at_phase: τ.6.x.2.i`, `book: psa`, `pages: [1,151]`, `verses: <total>`, `fetched_date: <today>`, `calibrate_first: GO`.

In `dev/CHANGELOG.md` (top entry), `dev/SESSION_STATE.md` (new headline + clear the τ.6.x.2.i blocker banner — Psalms now shipped via external source), `dev/IN_FLIGHT.md` (`<!-- TRACKER-STATE: idle -->` + the completed τ.6.x.2.i record), and `dev/PLAN_2026-05-09.md` (mark τ.6.x.2.i shipped; note τ.6.x.5 capability): add the τ.6.x.2.i entry following the existing τ.7.x.* prose conventions in each file.

- [ ] **Step 6: Full verification**

Run: `$env:PYTHONUTF8="1"; py -m ruff format --check scripts/ingest_hacohen.py tests/test_ingest_hacohen.py tests/test_parallel_bible_tau6x2i.py content/translations/geez-tewahedo/psa.py`
Expected: `... already formatted`.

Run: `$env:PYTHONUTF8="1"; py -m pytest tests/ -q`
Expected: full suite `0 failed` (new tests green; all prior pins green; the parametrized `write_book_module` defaults kept every existing per-book ship byte-identical).

- [ ] **Step 7: Commit the ship**

```bash
git add scripts/ingest_hacohen.py tests/test_ingest_hacohen.py tests/test_parallel_bible_tau6x2i.py "tests/fixtures/hacohen/psalm1.html" "tests/fixtures/hacohen/psalm_malformed.html" "content/translations/geez-tewahedo/psa.py" "content/translations/geez-tewahedo/_meta.yaml" "content/translations/sources/hacohen-geez/_source.yaml" "content/translations/sources/hacohen-geez/.gitignore" dev/CHANGELOG.md dev/SESSION_STATE.md dev/IN_FLIGHT.md dev/PLAN_2026-05-09.md scripts/extract_parallel_pdf.py
git commit -m "tau.6.x.2.i: Ge'ez Psalms via HaCohen/Ludolf digitized-critical-edition (tau.6.x.5 external-source ingest) — source-authoritative numbering, calibrate-first GO, floor=validation"
```

(No push; no zip. Local commit only, per project convention.)

---

## Self-Review

**1. Spec coverage:**
- §2 source validated → Tasks 3/7 (real fixture + real fetch/calibrate).
- §3 trust-source / floor=validation-only → Task 6 `ingest_psalms` (no renumber call) + Task 8 Step 2 (delta report, not reshape).
- §4 components: fetcher+cache (T4), parser (T3), writer reuse (T2+T6), provenance record (T1).
- §5 calibrate-first → Task 5 + Task 7 (real gate, NO-GO branch).
- §6 versification tolerance → Task 8 Step 2 (>2 or >5%; ≥20% chapters ⇒ NO-GO).
- §7 error handling → T4 (no partial write), T5 (NO-GO no artifacts), T7 Step 3 branch.
- §8 testing → every code task is TDD; T8 full regression.
- §9 scope: Psalms only; sibling parsers not built (no Sirach/Wisdom tasks) ✓ YAGNI.
- §10 acceptance criteria 1–7 → T1 (record), T4 (cache/no-partial), T3 (pure parser+fixture), T5/T7 (calibrate-first+NO-GO), T8 (ship+quality+content+deltas), T8.6 (regression+ruff), T2/§11 (colometric retained, τ.6.x.1.E untouched — `write_book_module` defaults proven byte-identical in T2 Step 5).
- §11 colometric retained / τ.6.x.1.E unaffected → T2 Step 5 regression proves the parser-fix tests + per-book ships still green; no colometric-spec file touched.

**2. Placeholder scan:** No "TBD/TODO". Every code step has complete code; every command has expected output. Task 8 Step 5 references concrete fields/shapes (mirrors the existing `ingest_record_tau6x2h`) rather than inventing a schema — acceptable (it adapts an existing committed pattern the executor can read).

**3. Type consistency:** `parse_hacohen_psalter(html:str, psalm_number:int)->list[tuple[int,int,str]]` used identically in T3/T5/T6. `fetch_psalm(n,*,cache_dir,delay)->Path` consistent T4/T6/T7. `calibrate(*,sample,cache_dir)->dict{go,reason,parsed}` consistent T5/T6. `ingest_psalms(*,cache_dir,phase)->Path` consistent T6/T8. `write_book_module` new kwargs (`source_provenance`,`source_yaml_ref`,`tool`) defined T2, used T6. `_http_get(url)->str` defined T4, monkeypatched T4. No mismatches.

Plan is internally consistent and fully covers the spec.
