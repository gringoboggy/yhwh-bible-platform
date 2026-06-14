# kindle_safe Variant Implementation Plan (board turn-69 item ①)

> **⚠ RETIRED 2026-06-14 (WIN turn 86):** This document describes the `--target-reader kindle` FAIL variant (the `apply_kindle_*` / `_KINDLE_SAFE_CSS` / gate-5 in-pipeline path that produced the artifacts that failed real Send-to-Kindle). It has been **consolidated away** in favor of the single production path: everywhere base + `scripts.core.kindle_post.make_kindle_safe` + `verify_kindle_safe` (wired via `build_format_matrix` `post_process: kindle_safe` and the dedicated `build_kindle` driver). The live code for the variant (the four apply fns + helpers + call sites) was excised from `build_edition.py`; only the general resolver + K-KIN emitter flags remain. This plan file is retained as historical audit trail of the experiments. Current truth: LANE_HANDOFF (turn 86), kindle_post.py, build_format_matrix.py, and the M4 45-artifact column.

**Status:** EXECUTED 2026-06-10 (Mac turn 69) — tasks 1–7 complete: TDD slices shipped + byte-identity proven (before/after SHA equal with the field unset) + the kindle acceptance artifact staged to `~/Desktop` (gates green incl. gate 5). Acceptance = the user's Send-to-Kindle re-verify (K-KIN-1..4). **Later superseded/retired by the minimal post-process recipe proven on the real STK channel (turn 84/85) and the dead-variant cleanup (turn 86).**

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `target_reader: kindle` build variant whose EPUB survives Send-to-Kindle (E999/E3013: ≤10K chars under `display:none`, single `dc:language`) and reads well on Kindle (visible endnotes, plain ToC chapter rows, no book-seam shatter), plus a `kindle_safe` artifact gate — with the 9 KJV editions byte-identical when the field is unset.

**Architecture:** A new 5th `target_reader` value `kindle` flows through ONE resolver in `build_edition.py` (`resolve_target_reader` / `is_kindle_target`) consumed by the API validator, the customize/matrix surface, the wizard, and the build. The build half is CSS-only-plus-one-ToC-markup-pass: a `_KINDLE_SAFE_CSS` append (un-hides notes/verse-refs sections + note labels + `.vn-sep`, fixes the seam page-break CSS) and an `apply_kindle_toc_rows` pass (chapter pills → plain inline anchor rows) gated on the resolver. `patch_opf` stamps the resolved target into the OPF (legacy `<meta name>` form, additive only when the field is set) so the stdlib-only artifact verifier can run kindle checks skew-free. Empirical basis: Kindle test-2 (CSS hides stripped, `hidden=""` attrs left intact) DELIVERED and rendered notes visibly — CSS-only is proven sufficient; markup stays identical across targets.

**Tech Stack:** Python 3 (stdlib + project core), pytest, the existing append-to-stylesheet build mechanism, `dev/verify_kr2_build.py` (stdlib-only zip verifier).

**Evidence inputs:** `docs/superpowers/notes/2026-06-10-kindle-e999-investigation.md` (E999 verdict + K-KIN-1..4), the 6-mapper understand workflow (wf_c6874099-bff, 2026-06-10).

**Key design decisions (locked):**
1. `kindle` = a **5th target value**, NOT an eink alias — eink (Kobo) *requires* hidden asides + `.vn-sep` separators; Kindle requires the opposite. One value cannot serve both.
2. **CSS-only un-hide** (no `hidden=""` attr stripping): author `display:block` overrides the UA hidden rule; proven on-device (test-2 + Kindle round-1 QA). Markup byte-identical across targets except the ToC rows pass.
3. `.vn-sep` becomes **visible** (`display:inline`) on kindle instead of skipping emission — the separator bullets are *useful* in visible endnote flow, and markup parity keeps the test surface small.
4. **Do NOT un-force the title singleton** (pure function, test-pinned, Kobo-critical). The seam fix is CSS: drop `.book-title-page`'s forced breaks (the singleton spine file already breaks), exempt `h1.bookpage-title` from the global `h1 {page-break-before:always}`, cap art height for vh-less KF8.
5. Gate target source = **OPF stamp** `<meta name="yhwh:target-reader" content="…"/>` emitted by patch_opf only when `target_reader` is explicitly set (unset ⇒ no element ⇒ byte-identical) — skew-proof, keeps the verifier stdlib-only.
6. Both kindle checks (display:none volume ≤10K, `dc:language` count==1) live in a kindle-stamp-gated gate 5 (`kindle_safe_checks`) — never asserted on non-kindle artifacts (no-reassert-ratified-bar).

---

### Task 1: The one resolver — `TARGET_READERS` + `resolve_target_reader` + `is_kindle_target`

**Files:**
- Modify: `scripts/build_edition.py` (constants region near `MARKER_STYLES`, ~line 1764)
- Modify: `scripts/api/editions.py:766-776` (import the constant, accept kindle)
- Modify: `scripts/web_editions.py:454` (route through the resolver)
- Test: `tests/test_kindle_safe.py` (new file)

- [ ] **Step 1: Write the failing tests**

```python
"""kindle_safe variant (board turn-69 ①, Kindle E999/E3013 arc).

A `target_reader: kindle` edition builds a Send-to-Kindle-survivable EPUB:
visible endnotes (no >10K chars under display:none — Amazon's documented
hard-fail), plain ToC chapter rows (KFX linearizes the pills), no book-seam
shatter (KFX double-break), single dc:language (WIN's half, already shipped).
Everything is gated on ONE resolver; unset ⇒ byte-identical builds (RULES 7.2).
Evidence: docs/superpowers/notes/2026-06-10-kindle-e999-investigation.md.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class TestTargetReaderResolver:
    """The one resolver both matrix and build call (MATRIX_MAP finding #3)."""

    def test_target_readers_constant_has_five_values(self):
        from scripts.build_edition import TARGET_READERS

        assert TARGET_READERS == ("everywhere", "eink", "tablet", "computer", "kindle")

    def test_resolver_defaults_unset_to_everywhere(self):
        from scripts.build_edition import resolve_target_reader

        assert resolve_target_reader({}) == "everywhere"
        assert resolve_target_reader({"target_reader": ""}) == "everywhere"
        assert resolve_target_reader({"target_reader": "  "}) == "everywhere"

    def test_resolver_passes_valid_values_and_defuses_unknown(self):
        from scripts.build_edition import resolve_target_reader

        assert resolve_target_reader({"target_reader": "kindle"}) == "kindle"
        assert resolve_target_reader({"target_reader": "eink"}) == "eink"
        # an unknown on-disk value must never activate a variant
        assert resolve_target_reader({"target_reader": "smartfridge"}) == "everywhere"

    def test_is_kindle_target(self):
        from scripts.build_edition import is_kindle_target

        assert is_kindle_target({"target_reader": "kindle"}) is True
        assert is_kindle_target({}) is False
        assert is_kindle_target({"target_reader": "eink"}) is False

    def test_api_validator_imports_the_shared_constant(self):
        # one-resolver rule: no inline enum copy in the API layer
        src = (REPO / "scripts" / "api" / "editions.py").read_text(encoding="utf-8")
        assert 'valid_targets = {"everywhere", "eink", "tablet", "computer"}' not in src
        assert "TARGET_READERS" in src

    def test_api_accepts_kindle(self):
        from scripts.api.editions import api_save_edition_meta
        from scripts.core import config

        yaml_path = REPO / "content" / "editions.yaml"
        original = yaml_path.read_bytes()
        try:
            r = api_save_edition_meta("catholic-study", {"target_reader": "kindle"})
            assert "error" not in r, r
            assert 'target_reader: "kindle"' in yaml_path.read_text(encoding="utf-8")
        finally:
            yaml_path.write_bytes(original)
            config.load_editions.cache_clear()

    def test_customize_surface_routes_through_the_resolver(self):
        src = (REPO / "scripts" / "web_editions.py").read_text(encoding="utf-8")
        assert 'e.get("target_reader", "everywhere")' not in src
        assert "resolve_target_reader" in src
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kindle_safe.py -x -q`
Expected: FAIL (ImportError: cannot import name 'TARGET_READERS')

- [ ] **Step 3: Implement the resolver in `scripts/build_edition.py`** — insert directly below the `DEFAULT_MARKER_STYLE = "badge"` block (~line 1769):

```python
# K-R2 + kindle_safe — the reader-target enum and its ONE resolver. Both the
# matrix/UI surfaces (web_editions.api_customize_data) and the build (build_one)
# and the save validator (api_save_edition_meta) resolve through here, so a
# target-gated behavior can never drift between the printed matrix and the
# built EPUB (MATRIX_MAP finding #3). "kindle" (turn-69 ①) tunes the build for
# Send-to-Kindle: visible endnotes (E3013 — Amazon hard-fails >10K chars under
# display:none), plain ToC chapter rows (KFX linearizes the pills), and seam
# page-break CSS (KFX double-break). Unknown/unset values resolve to
# "everywhere" so a stale on-disk value can never activate a variant.
TARGET_READERS = ("everywhere", "eink", "tablet", "computer", "kindle")


def resolve_target_reader(edition: dict) -> str:
    """The edition's reader target — the single resolver for every consumer."""
    v = (edition.get("target_reader") or "").strip()
    return v if v in TARGET_READERS else "everywhere"


def is_kindle_target(edition: dict) -> bool:
    """True when the edition builds for Send-to-Kindle (kindle_safe variant)."""
    return resolve_target_reader(edition) == "kindle"
```

- [ ] **Step 4: Route `scripts/api/editions.py` through the constant** — replace lines 766-776's inline set:

```python
    if "target_reader" in payload:
        # K-R2 — the wizard's reader-target pick. Empty/absent = everywhere.
        # kindle (turn-69 ①) = the Send-to-Kindle-safe build variant. The valid
        # set is the build's own TARGET_READERS (one-resolver rule — same
        # pattern as CHAPTER_NUMBER_FORMATS above).
        from scripts.build_edition import TARGET_READERS

        v = (payload["target_reader"] or "").strip()
        if v and v not in TARGET_READERS:
            return {"error": f"unknown target_reader: {v!r}; valid: {sorted(TARGET_READERS)}"}
        # round-7 in-passing fix: this line wrote payload["chapter_number_format"]
        # (copy-paste from the block above) — a wizard reader-target save was
        # CLOBBERING the edition's chapter-number format with "eink"/"tablet"/…,
        # sidestepping that field's own validation (it runs earlier).
        payload["target_reader"] = v
```

- [ ] **Step 5: Route `scripts/web_editions.py:454` through the resolver** — replace `"target_reader": e.get("target_reader", "everywhere"),` with:

```python
                "target_reader": _resolve_target_reader(e),
```

and add the lazy import at the top of `api_customize_data` (mirror how the function already lazy-imports; if none exists, add at function top):

```python
    from scripts.build_edition import resolve_target_reader as _resolve_target_reader
```

- [ ] **Step 6: Run the new tests + the existing reader-target pins**

Run: `.venv/bin/python -m pytest tests/test_kindle_safe.py tests/test_reader_target.py -q`
Expected: test_kindle_safe PASS; test_reader_target still PASS (its `smartfridge` rejection + clobber pin are unaffected).

- [ ] **Step 7: Commit**

```bash
git add tests/test_kindle_safe.py scripts/build_edition.py scripts/api/editions.py scripts/web_editions.py
git commit -m "kindle_safe ①: TARGET_READERS + resolve_target_reader one-resolver (kindle = 5th target; api + customize surface routed through it)"
```

---

### Task 2: Wizard + customize kindle surfaces

**Files:**
- Modify: `scripts/templates/wizard.py` (target card ~166-169, TARGET_CAPS ~506-531)
- Modify: `scripts/templates/customize.py:503-508`
- Modify: `tests/test_reader_target.py:28-52` (count pins 4→5)
- Test: `tests/test_kindle_safe.py` (extend)

- [ ] **Step 1: Write the failing tests** (append to `tests/test_kindle_safe.py`)

```python
class TestKindleWizardSurfaces:
    """The wizard + customize offer the kindle target with Send-to-Kindle copy."""

    def test_wizard_has_kindle_card_naming_send_to_kindle(self):
        from scripts.templates.wizard import WIZARD_HTML

        assert 'data-target="kindle"' in WIZARD_HTML
        assert "Send to Kindle" in WIZARD_HTML

    def test_target_caps_has_kindle_entry_gated_off_expandable(self):
        from scripts.templates.wizard import WIZARD_HTML

        caps = WIZARD_HTML[WIZARD_HTML.index("const TARGET_CAPS") : WIZARD_HTML.index("function applyTargetGating")]
        assert "kindle:" in caps
        assert caps.count("toc_expandable: false") == 4  # everywhere/eink/computer/kindle
        assert caps.count("toc_expandable: true") == 1  # tablet only, unchanged

    def test_customize_select_offers_kindle(self):
        from scripts.templates.customize import CUSTOMIZE_HTML

        assert "'kindle'" in CUSTOMIZE_HTML and 'value="kindle"' in CUSTOMIZE_HTML
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kindle_safe.py::TestKindleWizardSurfaces -q`
Expected: FAIL (no kindle card)

- [ ] **Step 3: Add the wizard card** after the `computer` card (wizard.py ~169):

```html
          <div class="pick-card target-card" data-target="kindle">
            <div class="font-semibold">📬 Kindle</div>
            <div class="text-xs text-slate-500 mt-1">Built for Send to Kindle — notes read as visible endnotes.</div>
          </div>
```

and change the grid to fit five cards (same line 153): `grid-cols-2 md:grid-cols-4` → `grid-cols-2 md:grid-cols-5`.

- [ ] **Step 4: Add the TARGET_CAPS entry** after `computer: {...},` (~530):

```javascript
  kindle: {
    label: '📬 Kindle',
    toc_expandable: false,
    note: 'Built for Send to Kindle: notes render as visible endnotes (Kindle has no popup footnotes), chapter lists are plain rows, and the metadata passes Amazon’s delivery checks.',
    gate_reason: 'Kindle’s format has no support for collapsible lists — the chapter rows stay always visible instead.',
  },
```

- [ ] **Step 5: Add the customize option** after the `computer` option (customize.py ~507):

```javascript
                <option value="kindle"     ${e.target_reader === 'kindle' ? 'selected' : ''}>📬 Kindle (Send to Kindle — visible endnotes)</option>
```

- [ ] **Step 6: Update the four/three count pins in `tests/test_reader_target.py`:**
  - line 32: `for target in ("everywhere", "eink", "tablet", "computer", "kindle"):`
  - line 52: `assert caps.count("toc_expandable: false") == 4`
  - docstring of `test_wizard_has_target_picker_with_all_four_targets` → rename to `test_wizard_has_target_picker_with_all_five_targets`

- [ ] **Step 7: Run both files**

Run: `.venv/bin/python -m pytest tests/test_kindle_safe.py tests/test_reader_target.py -q`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add scripts/templates/wizard.py scripts/templates/customize.py tests/test_reader_target.py tests/test_kindle_safe.py
git commit -m "kindle_safe ②: wizard 5th target card + TARGET_CAPS kindle entry + customize option (Send-to-Kindle copy per the E999 prescription)"
```

---

### Task 3: `_KINDLE_SAFE_CSS` + `apply_kindle_safe_css` + build_one wiring (visible endnotes + seam CSS — K-KIN-1, K-KIN-3, E3013)

**Files:**
- Modify: `scripts/build_edition.py` (CSS constant + append fn below `apply_note_cascade_css` ~1851; build_one wiring after the cascade block ~5122)
- Test: `tests/test_kindle_safe.py` (extend)

- [ ] **Step 1: Write the failing tests**

```python
class TestKindleSafeCss:
    """E3013 (visible endnotes) + K-KIN-3 (seam) CSS — pure append, kindle-gated."""

    def test_appends_only_the_kindle_block(self):
        from scripts.build_edition import _KINDLE_SAFE_CSS, apply_kindle_safe_css

        base = ".notes-section, .notes-rule { display: none; }\n"
        out = apply_kindle_safe_css(base)
        assert out == base + _KINDLE_SAFE_CSS
        assert out.startswith(base)  # append-only — base rules untouched

    def test_unhides_every_text_bearing_hidden_class(self):
        from scripts.build_edition import _KINDLE_SAFE_CSS as css

        # the E3013 mass (≈486K chars in catholic-study) — both section hides
        assert ".notes-section { display: block;" in css
        assert ".verse-refs-section { display: block;" in css
        # the ~13K note-label hides (base stylesheet.css:227-233) — same selector
        # strings as the base so the artifact gate can pair override with hide
        assert "[class*=\"note-comm-\"] > div > .note-label { display: block; }" in css
        assert ".note-label:where([data-noise])" in css
        # the .vn-sep separators become VISIBLE bullets (useful in endnote flow)
        assert ".vn-sep { display: inline; }" in css

    def test_keeps_the_bottom_notes_heading_hidden(self):
        # inject puts the hr+h3 "Notes" heading at the section BOTTOM (cosmetic
        # inversion in a visible render) — keep it hidden; ~305 chars ≪ 10K
        from scripts.build_edition import _KINDLE_SAFE_CSS as css

        assert ".notes-heading { display: none; }" in css

    def test_seam_fix_rules(self):
        # K-KIN-3: the forced singleton spine file already breaks the page on
        # every renderer — the CSS forced breaks are pure KFX double-break
        # liability; the global h1 break tears the caption band off the title.
        from scripts.build_edition import _KINDLE_SAFE_CSS as css

        assert ".book-title-page { page-break-before: auto;" in css
        assert "h1.bookpage-title { page-break-before: avoid;" in css
        assert ".bookpage-art" in css and "max-height: 12em" in css
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kindle_safe.py::TestKindleSafeCss -q`
Expected: FAIL (ImportError: _KINDLE_SAFE_CSS)

- [ ] **Step 3: Implement** — insert below `apply_note_cascade_css` (~line 1851):

```python
# kindle_safe (turn-69 ①) — the Send-to-Kindle variant CSS, appended LAST so it
# wins every earlier rule. Three jobs:
#   1. E3013/E999 (CONFIRMED): Amazon hard-fails conversion when >10,000 chars
#      hide under display:none (~486K hidden in a default build). Un-hide the
#      notes/verse-refs sections (visible endnote style — Kindle's reader
#      follows the noteref links natively) and the note-label hides. CSS-only:
#      author display:block also overrides the asides' hidden="" UA rule —
#      empirically proven (test-2 delivered + rendered with hidden intact).
#      Selector strings INTENTIONALLY mirror the base hide rules verbatim so
#      the kindle_safe artifact gate can pair each hide with its override.
#   2. .vn-sep separators (a Kobo eInk-preview mechanism) become visible
#      bullets — useful structure in visible endnote flow, and the hidden-char
#      budget stays near zero without diverging the markup per target.
#   3. K-KIN-3 seam shatter: the title singleton spine file already guarantees
#      the page break, so .book-title-page's forced CSS breaks only produce
#      KFX's classic double-break blank page; the global h1 page-break-before
#      tears the caption band ("BOOK II / The Second Book of Moses") off its
#      book name; KF8 drops vh so the art falls back to max-height:20em and
#      claims a page — re-cap lower so caption+title+art share one page.
_KINDLE_SAFE_CSS = """
/* === kindle_safe (target_reader=kindle) — Send-to-Kindle variant === */
/* E3013: visible endnotes — nothing big may hide under display:none */
.notes-section { display: block; margin: 1.2em 0 0.8em; padding-top: 0.5em; border-top: 1px solid rgba(110, 88, 64, 0.4); }
.notes-rule { display: none; }
.notes-heading { display: none; }
.verse-refs-section { display: block; margin: 1.2em 0 0.8em; padding-top: 0.5em; border-top: 1px solid rgba(110, 88, 64, 0.4); }
.note-comm > p > .note-label,
.note-comm > div > .note-label,
[class*="note-comm-"] > p > .note-label,
[class*="note-comm-"] > div > .note-label { display: block; }
.note-label:where([data-noise]), .note p > .note-label:first-child:is(:empty) { display: block; }
.vn-sep { display: inline; }
/* K-KIN-3: no double-break blanks, no caption-band tear, art shares the page */
.book-title-page { page-break-before: auto; break-before: auto; page-break-after: auto; break-after: auto; }
h1.bookpage-title { page-break-before: avoid; break-before: avoid; }
.bookpage-art, .bookpage-art-bleed { max-height: 12em; }
/* K-KIN-2 companion: plain chapter rows (markup pass apply_kindle_toc_rows) */
.toc-chapter-row { text-align: left; line-height: 2; word-spacing: 0.35em; margin: 0.25em 0 0.6em 1.4em; }
.toc-chapter-row a { text-decoration: none; color: #2a1a1a; padding: 0 0.1em; }
"""


def apply_kindle_safe_css(stylesheet_css: str) -> str:
    """Append the kindle_safe variant CSS (visible endnotes + seam fixes).

    Pure CSS against the existing baked classes — no base re-bake, no markup
    change. Mirrors apply_note_cascade_css; the caller gates on
    is_kindle_target, so non-kindle editions append NOTHING (byte-identical,
    RULES 7.2)."""
    return stylesheet_css + _KINDLE_SAFE_CSS
```

- [ ] **Step 4: Wire into build_one** — after the cascade block (ends ~5122), insert:

```python
        # kindle_safe (turn-69 ①) — append the Send-to-Kindle variant CSS
        # (visible endnotes per E3013, K-KIN-3 seam fixes, K-KIN-2 row chrome)
        # when the resolved reader target is kindle. Same append-to-stylesheet
        # mechanism; absent/other targets ⇒ byte-identical (RULES 7.2).
        if css_path.is_file() and is_kindle_target(edition):
            css_path.write_text(
                apply_kindle_safe_css(css_path.read_text(encoding="utf-8")),
                encoding="utf-8",
            )
            stats["kindle_safe_css"] = True
```

- [ ] **Step 5: Run the tests**

Run: `.venv/bin/python -m pytest tests/test_kindle_safe.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/build_edition.py tests/test_kindle_safe.py
git commit -m "kindle_safe ③: _KINDLE_SAFE_CSS + apply_kindle_safe_css — visible endnotes (E3013), seam page-break fixes (K-KIN-3), vn-sep visible; kindle-gated append in build_one"
```

---

### Task 4: `apply_kindle_toc_rows` — chapter pills → plain inline rows (K-KIN-2)

**Files:**
- Modify: `scripts/build_edition.py` (pass beside `apply_reader_toc_transforms`; build_one wiring after `apply_bilingual_toc` ~5304, BEFORE `apply_badge_markers`)
- Test: `tests/test_kindle_safe.py` (extend)

**Why this seam:** `apply_bilingual_toc`'s chapter regex (build_edition.py:3910) requires the `<li><a href…>` pill shape, so the rows pass must run AFTER it (5301) and BEFORE `apply_file_split` (5376) so href remapping covers the rewritten anchors for free. ToC hrefs are MIXED `#page_N` and `#ch-bXX-cN` — the pass matches whole `<ol class="toc-chapters">` blocks, never individual href shapes. nav.xhtml/toc.ncx need no change (Kindle round-1 QA: NCX nav correct).

- [ ] **Step 1: Write the failing tests**

```python
_KINDLE_TOC_PAGE = (
    "<?xml version='1.0' encoding='utf-8'?>\n"
    '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>T</title></head><body>\n'
    '<div class="toc-wrap"><h1 class="toc-title">Contents</h1><ol class="toc-books">\n'
    '<li class="toc-book"><p class="toc-book-label"><a href="index_split_000.html#bp-00">Genesis</a></p>'
    '<ol class="toc-chapters"><li><a href="index_split_000.html#page_4">1</a></li>'
    '<li><a href="index_split_000.html#ch-b00-c18">18</a></li></ol></li>\n'
    "</ol></div>\n</body></html>"
)


class TestKindleTocRows:
    """K-KIN-2: KFX drops the li display → one pill per line. Plain inline
    anchors in a <p> are inline text in every renderer including KFX."""

    def test_rewrites_pill_ols_to_plain_rows(self, tmp_path):
        from scripts.build_edition import apply_kindle_toc_rows

        (tmp_path / "index_split_000.html").write_text(_KINDLE_TOC_PAGE, encoding="utf-8")
        stats = apply_kindle_toc_rows(tmp_path, {"target_reader": "kindle"})
        out = (tmp_path / "index_split_000.html").read_text(encoding="utf-8")
        assert stats["toc_rows_rewritten"] == 1
        assert 'class="toc-chapters"' not in out
        assert '<p class="toc-chapter-row">' in out
        # every anchor survives verbatim (mixed #page_N / #ch-bXX-cN hrefs)
        assert '<a href="index_split_000.html#page_4">1</a>' in out
        assert '<a href="index_split_000.html#ch-b00-c18">18</a>' in out
        # the book label row is untouched
        assert '<p class="toc-book-label">' in out

    def test_noop_for_non_kindle_targets(self, tmp_path):
        from scripts.build_edition import apply_kindle_toc_rows

        (tmp_path / "index_split_000.html").write_text(_KINDLE_TOC_PAGE, encoding="utf-8")
        stats = apply_kindle_toc_rows(tmp_path, {})
        out = (tmp_path / "index_split_000.html").read_text(encoding="utf-8")
        assert stats["toc_rows_rewritten"] == 0
        assert out == _KINDLE_TOC_PAGE  # byte-identical

    def test_idempotent(self, tmp_path):
        from scripts.build_edition import apply_kindle_toc_rows

        (tmp_path / "index_split_000.html").write_text(_KINDLE_TOC_PAGE, encoding="utf-8")
        apply_kindle_toc_rows(tmp_path, {"target_reader": "kindle"})
        first = (tmp_path / "index_split_000.html").read_text(encoding="utf-8")
        apply_kindle_toc_rows(tmp_path, {"target_reader": "kindle"})
        assert (tmp_path / "index_split_000.html").read_text(encoding="utf-8") == first

    def test_collapsible_details_shape_also_rewrites(self, tmp_path):
        # /customize can set collapsible=true + kindle; the ol inside <details>
        # must still become a row (the <details> wrapper itself is harmless —
        # Kindle converts it to a permanently-expanded block, K-KIN-4)
        from scripts.build_edition import apply_kindle_toc_rows

        page = _KINDLE_TOC_PAGE.replace(
            '<p class="toc-book-label"><a href="index_split_000.html#bp-00">Genesis</a></p>',
            '<details><summary><a href="index_split_000.html#bp-00">Genesis</a></summary>',
        ).replace("</ol></li>", "</ol></details></li>")
        (tmp_path / "index_split_000.html").write_text(page, encoding="utf-8")
        stats = apply_kindle_toc_rows(tmp_path, {"target_reader": "kindle"})
        assert stats["toc_rows_rewritten"] == 1
        assert 'class="toc-chapters"' not in (tmp_path / "index_split_000.html").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kindle_safe.py::TestKindleTocRows -q`
Expected: FAIL (ImportError: apply_kindle_toc_rows)

- [ ] **Step 3: Implement** — insert below `apply_reader_toc_transforms` (after its closing line ~3647):

```python
# K-KIN-2 (kindle_safe): the in-content ToC's chapter pills are <li
# display:inline-block> items — KFX drops the list display, so every pill
# renders block-level (one chapter per LINE; Genesis ToC spans pages on
# Kindle). Plain anchors inside a <p> are inline TEXT in every renderer
# including KFX. The pass rewrites each <ol class="toc-chapters"> block to a
# <p class="toc-chapter-row"> of space-joined anchors (hrefs untouched —
# they're MIXED #page_N / #ch-bXX-cN, so we match the ol block, never href
# shapes). Runs AFTER apply_bilingual_toc (its chapter regex needs the pill
# shape) and BEFORE apply_file_split (href remapping then covers the rewritten
# anchors like all content). Styling rides _KINDLE_SAFE_CSS (.toc-chapter-row).
_TOC_CHAPTERS_OL_RE = re.compile(r'<ol class="toc-chapters">(.*?)</ol>', re.DOTALL)
_TOC_CHAPTER_ANCHOR_RE = re.compile(r"<a\b[^>]*>.*?</a>", re.DOTALL)


def _toc_ol_to_row(m: "re.Match[str]") -> str:
    anchors = _TOC_CHAPTER_ANCHOR_RE.findall(m.group(1))
    return '<p class="toc-chapter-row">' + " ".join(anchors) + "</p>"


def apply_kindle_toc_rows(tmp: Path, edition: dict) -> dict:
    """Rewrite ToC chapter-pill <ol>s to plain inline anchor rows (K-KIN-2).

    Kindle-gated through the one resolver; any other target returns without
    touching a byte (RULES 7.2). Mutates only the per-edition temp tree."""
    stats = {"toc_rows_rewritten": 0}
    if not is_kindle_target(edition):
        return stats
    for fpath in sorted(tmp.glob("index_split_*.html")):
        text = fpath.read_text(encoding="utf-8")
        out, n = _TOC_CHAPTERS_OL_RE.subn(_toc_ol_to_row, text)
        if n:
            fpath.write_text(out, encoding="utf-8")
            stats["toc_rows_rewritten"] += n
    return stats
```

- [ ] **Step 4: Wire into build_one** — directly after the bilingual block (ends ~5304):

```python
        # K-KIN-2 (kindle_safe) — chapter pills → plain inline rows. MUST stay
        # after apply_bilingual_toc (its chapter regex needs the pill shape)
        # and before apply_file_split (which remaps the rewritten hrefs).
        # No-op for every non-kindle target (byte-identical).
        toc_rows_stats = apply_kindle_toc_rows(tmp, edition)
        stats["toc_rows_rewritten"] = toc_rows_stats["toc_rows_rewritten"]
```

- [ ] **Step 5: Run the tests + the neighbors that pin the pill modes**

Run: `.venv/bin/python -m pytest tests/test_kindle_safe.py tests/test_reader_target.py tests/test_file_split.py::TestInContentTocModes -q`
Expected: PASS (the existing flat/collapsible pill pins are untouched — kindle is a third mode)

- [ ] **Step 6: Commit**

```bash
git add scripts/build_edition.py tests/test_kindle_safe.py
git commit -m "kindle_safe ④: apply_kindle_toc_rows — ToC chapter pills → plain inline anchor rows for KFX (K-KIN-2); runs post-bilingual pre-split"
```

---

### Task 5: OPF target stamp in `patch_opf`

**Files:**
- Modify: `scripts/build_edition.py` (inside `patch_opf`, beside the dc:language refinement ~1559-1575)
- Test: `tests/test_kindle_safe.py` (extend) + `tests/test_opf_clean.py` (one guard)

- [ ] **Step 1: Write the failing tests**

```python
class TestOpfTargetStamp:
    """patch_opf stamps the resolved target so the stdlib-only artifact
    verifier can run kindle checks skew-free (editions.yaml is mutable
    post-build; the OPF is not). Additive ONLY when target_reader is set —
    unset editions stay byte-identical."""

    _BASE_OPF = (
        "<?xml version='1.0'?>\n"
        '<package version="3.0">\n'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        '<dc:title>X</dc:title><dc:creator id="creator">PD</dc:creator>\n'
        '<meta refines="#creator" property="role" scheme="marc:relators">aut</meta>\n'
        '<meta refines="#creator" property="file-as">PD</meta>\n'
        '<dc:contributor id="contributor">calibre</dc:contributor>\n'
        "<dc:date>2020-01-01</dc:date><dc:language>en</dc:language>\n"
        "</metadata></package>"
    )

    def test_no_stamp_when_target_unset(self):
        from scripts.build_edition import patch_opf

        opf = patch_opf(self._BASE_OPF, {"id": "catholic-study", "title": "X"}, "v1")
        assert "yhwh:target-reader" not in opf

    def test_stamp_present_when_kindle(self):
        from scripts.build_edition import patch_opf

        opf = patch_opf(self._BASE_OPF, {"id": "catholic-study", "title": "X", "target_reader": "kindle"}, "v1")
        assert '<meta name="yhwh:target-reader" content="kindle"/>' in opf

    def test_stamp_uses_the_resolver_not_the_raw_value(self):
        from scripts.build_edition import patch_opf

        # a stale unknown value resolves to everywhere — and everywhere is the
        # default, so an unknown value stamps NOTHING (defused, not propagated)
        opf = patch_opf(self._BASE_OPF, {"id": "catholic-study", "title": "X", "target_reader": "smartfridge"}, "v1")
        assert "yhwh:target-reader" not in opf
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kindle_safe.py::TestOpfTargetStamp -q`
Expected: FAIL (no stamp emitted)

- [ ] **Step 3: Implement in `patch_opf`** — right after the dc:language refinement block (ends ~1575), add:

```python
    # kindle_safe (turn-69 ①): stamp the resolved reader target into the OPF
    # (legacy OPF2 meta form — epubcheck-tolerated, RS-ignored) so the artifact
    # verifier (dev/verify_kr2_build.py, stdlib-only) learns the target from
    # the artifact itself — skew-proof against post-build editions.yaml edits.
    # Additive ONLY when target_reader is explicitly set AND resolves off the
    # default: unset/everywhere editions emit no element (byte-identical,
    # RULES 7.2). Unknown stale values resolve to "everywhere" ⇒ no stamp.
    resolved_target = resolve_target_reader(edition)
    if (edition.get("target_reader") or "").strip() and resolved_target != "everywhere":
        new_text = new_text.replace(
            "</metadata>",
            f'    <meta name="yhwh:target-reader" content="{resolved_target}"/>\n</metadata>',
            1,
        )
```

- [ ] **Step 4: Add the cleanliness guard to `tests/test_opf_clean.py`** (TestOpfClean class — its fixture edition has no target_reader):

```python
    def test_no_target_stamp_on_untargeted_editions(self):
        # kindle_safe: the yhwh:target-reader stamp is additive-only — an
        # edition without target_reader must emit no stamp (byte-identity).
        assert "yhwh:target-reader" not in self.opf
```

- [ ] **Step 5: Run**

Run: `.venv/bin/python -m pytest tests/test_kindle_safe.py tests/test_opf_clean.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/build_edition.py tests/test_kindle_safe.py tests/test_opf_clean.py
git commit -m "kindle_safe ⑤: patch_opf stamps yhwh:target-reader (legacy meta, additive only when set) — skew-proof target source for the artifact gate"
```

---

### Task 6: Gate 5 — `kindle_safe_checks` in `dev/verify_kr2_build.py`

**Files:**
- Modify: `dev/verify_kr2_build.py` (new function + call from `main` after gate 4, ~line 228)
- Test: `tests/test_kindle_safe_gate.py` (new file — synthetic zips, fires-on-defect proven both ways)

**Semantics:** runs ONLY when the OPF carries `yhwh:target-reader` = `kindle` (no-reassert-ratified-bar: non-kindle artifacts are never judged). Checks: (a) effective `display:none` text volume ≤ 10,000 chars — *effective* means last-rule-wins across every `.css` member, pairing each base hide with the kindle override by exact selector string; (b) exactly one `<dc:language>`; (c) the kindle_safe CSS marker is present at all (fail fast with a clear message when the variant CSS never got appended).

- [ ] **Step 1: Write the failing tests**

```python
"""Fires-on-defect proof for the kindle_safe artifact gate (gate 5).

Synthetic minimal zips — the gate function is called directly so the other
gates' artifact requirements (pieces, nav, colophon) don't confound the test.
"""

import importlib.util
import io
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location("verify_kr2_build", REPO / "dev" / "verify_kr2_build.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_KINDLE_OPF = (
    '<package><metadata><dc:language>en-US</dc:language>\n'
    '<meta name="yhwh:target-reader" content="kindle"/>\n'
    "</metadata></package>"
)
_PLAIN_OPF = "<package><metadata><dc:language>en-US</dc:language>\n</metadata></package>"

_HIDE_CSS = ".notes-section, .notes-rule { display: none; }\n.verse-refs-section { display: none; }\n"
_KINDLE_CSS = (
    "/* === kindle_safe (target_reader=kindle) — Send-to-Kindle variant === */\n"
    ".notes-section { display: block; }\n.verse-refs-section { display: block; }\n"
)

_BIG = "x" * 11000
_PIECE_HIDDEN = (
    "<html><body><p>scripture</p>"
    f'<aside class="notes-section" epub:type="footnotes" hidden="">{_BIG}</aside>'
    "</body></html>"
)


def _zip(opf: str, css: str, piece: str) -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("content.opf", opf)
        z.writestr("stylesheet.css", css)
        z.writestr("index_split_000.html", piece)
    return zipfile.ZipFile(io.BytesIO(buf.getvalue()))


class TestKindleSafeGate:
    def test_fires_on_hidden_volume_over_10k(self):
        zf = _zip(_KINDLE_OPF, _HIDE_CSS, _PIECE_HIDDEN)
        fails = _mod.kindle_safe_checks(zf, zf.namelist(), zf.read("content.opf").decode())
        assert any("display:none" in f for f in fails), fails

    def test_green_when_kindle_css_overrides_the_hides(self):
        zf = _zip(_KINDLE_OPF, _HIDE_CSS + _KINDLE_CSS, _PIECE_HIDDEN)
        fails = _mod.kindle_safe_checks(zf, zf.namelist(), zf.read("content.opf").decode())
        assert fails == [], fails

    def test_skips_entirely_without_the_kindle_stamp(self):
        # >10K hidden + no stamp ⇒ not a kindle artifact ⇒ no kindle judgment
        zf = _zip(_PLAIN_OPF, _HIDE_CSS, _PIECE_HIDDEN)
        fails = _mod.kindle_safe_checks(zf, zf.namelist(), zf.read("content.opf").decode())
        assert fails == []

    def test_fires_on_multi_dc_language(self):
        opf = _KINDLE_OPF.replace(
            "<dc:language>en-US</dc:language>",
            "<dc:language>en-US</dc:language><dc:language>gez</dc:language>",
        )
        zf = _zip(opf, _HIDE_CSS + _KINDLE_CSS, _PIECE_HIDDEN)
        fails = _mod.kindle_safe_checks(zf, zf.namelist(), zf.read("content.opf").decode())
        assert any("dc:language" in f for f in fails), fails

    def test_fires_when_kindle_css_marker_absent(self):
        # stamp says kindle but the variant CSS never got appended — fail fast
        # with the clear message even if the volume math were somehow green
        zf = _zip(_KINDLE_OPF, _HIDE_CSS, "<html><body><p>s</p></body></html>")
        fails = _mod.kindle_safe_checks(zf, zf.namelist(), zf.read("content.opf").decode())
        assert any("kindle_safe CSS" in f for f in fails), fails
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kindle_safe_gate.py -q`
Expected: FAIL (AttributeError: kindle_safe_checks)

- [ ] **Step 3: Implement in `dev/verify_kr2_build.py`** — add the function above `main` and the call after gate 4 (before the stats print, ~line 228):

```python
# ── 5. kindle_safe (turn-69 ①) ──────────────────────────────────────────
# Runs ONLY when the build stamped the OPF with target-reader=kindle (the
# stamp is patch_opf's, emitted from the one resolver — skew-proof; non-kindle
# artifacts are never judged against the kindle bar). Checks the CONFIRMED
# E999 trigger pair: (a) ≤10,000 chars of text under EFFECTIVE display:none —
# effective = last-rule-wins per selector string across every .css member, so
# the base hides pair with the kindle overrides; (b) exactly one dc:language.
_CSS_RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")
_CSS_DISPLAY_RE = re.compile(r"display\s*:\s*([a-z-]+)")


def _effective_hidden_selectors(css_texts: list[str]) -> list[str]:
    """Selector strings whose LAST display declaration is none."""
    last: dict[str, str] = {}
    for css in css_texts:
        for m in _CSS_RULE_RE.finditer(css):
            d = _CSS_DISPLAY_RE.search(m.group(2))
            if not d:
                continue
            for sel in m.group(1).split(","):
                sel = " ".join(sel.split())
                if sel:
                    last[sel] = d.group(1)
    return [s for s, v in last.items() if v == "none"]


def _class_token(selector: str) -> str | None:
    """The LAST class token of a selector (conservative element matcher);
    pseudo-element selectors return None (no text content)."""
    if "::" in selector:
        return None
    classes = re.findall(r"\.([A-Za-z0-9_-]+)", selector)
    return classes[-1] if classes else None


def _hidden_text_chars(zf: zipfile.ZipFile, names: list[str], tokens: set[str]) -> int:
    total = 0
    docs = [n for n in names if n.endswith((".html", ".xhtml"))]
    open_re = re.compile(r"<([a-z][a-z0-9]*)\b[^>]*\bclass=\"[^\"]*\b(" + "|".join(sorted(tokens)) + r")\b[^\"]*\"[^>]*>")
    for n in docs:
        t = zf.read(n).decode("utf-8", "replace")
        for m in open_re.finditer(t):
            tag = m.group(1)
            depth, pos = 1, m.end()
            tag_re = re.compile(rf"<{tag}\b[^>]*>|</{tag}>")
            while depth and pos < len(t):
                nm = tag_re.search(t, pos)
                if not nm:
                    break
                depth += 1 if not nm.group(0).startswith("</") else -1
                pos = nm.end()
            inner = t[m.end() : pos]
            total += len(re.sub(r"<[^>]+>", "", inner))
    return total


def kindle_safe_checks(zf: zipfile.ZipFile, names: list[str], opf: str) -> list[str]:
    """Gate 5 — kindle_safe. Empty list = green (or not a kindle artifact)."""
    stamp = re.search(r'<meta name="yhwh:target-reader" content="([^"]+)"', opf)
    if not stamp or stamp.group(1) != "kindle":
        return []
    fails: list[str] = []
    if opf.count("<dc:language>") != 1:
        fails.append(f"kindle: OPF carries {opf.count('<dc:language>')} dc:language values (want exactly 1 — E999)")
    css_names = [n for n in names if n.endswith(".css")]
    css_texts = [zf.read(n).decode("utf-8", "replace") for n in css_names]
    if not any("kindle_safe" in c for c in css_texts):
        fails.append("kindle: target stamped kindle but the kindle_safe CSS was never appended (stale/mismatched build)")
    hidden = _effective_hidden_selectors(css_texts)
    tokens = {tok for tok in (_class_token(s) for s in hidden) if tok}
    chars = _hidden_text_chars(zf, names, tokens) if tokens else 0
    if chars > 10_000:
        fails.append(
            f"kindle: {chars:,} chars under effective display:none (Amazon hard-fails >10,000 — E3013); hidden selectors: {hidden[:8]}"
        )
    return fails
```

and in `main`, after the gate-4 block (after line 227's `fails.extend(...)`):

```python
    kindle_fails = kindle_safe_checks(zf, names, opf)
    fails.extend(kindle_fails)
```

(note: `opf` is already decoded at line 145 — gate 5 reuses it; `zipfile` is already imported.)

- [ ] **Step 4: Run**

Run: `.venv/bin/python -m pytest tests/test_kindle_safe_gate.py -q`
Expected: PASS (all 5, both directions proven)

- [ ] **Step 5: Regression — the verifier still greens a current non-kindle artifact** (any fresh eth/catholic build available locally; if none, defer to Task 7's build):

Run: `.venv/bin/python dev/verify_kr2_build.py <fresh-built.epub>`
Expected: `ALL K-R2 GATES GREEN` (gate 5 skips — no stamp)

- [ ] **Step 6: Commit**

```bash
git add dev/verify_kr2_build.py tests/test_kindle_safe_gate.py
git commit -m "kindle_safe ⑥: gate 5 kindle_safe_checks — effective-display:none volume ≤10K + single dc:language + CSS-marker fail-fast, OPF-stamp-gated; fires-on-defect proven both ways"
```

---

### Task 7: Proof + acceptance artifact + truth records

**Files:**
- Modify: `dev/MATRIX_MAP.md` (resolver + new pass rows), `docs/superpowers/INDEX.md` (this plan), `dev/SESSION_STATE.md` + `dev/IN_FLIGHT.md` + `dev/LANE_HANDOFF.md` (wrap)
- Artifact: `~/Desktop/Ethiopian_Bible_catholic-study_kindle-safe_<UTC>.epub`

- [ ] **Step 1: Byte-identity proof (RULES 7.2 + bytecompat doctrine).** Build catholic-study (NO target set) at the pre-change baseline commit and at HEAD; compare SHA-256:

```bash
git stash list  # ensure clean
git rev-parse HEAD  # note
.venv/bin/python -m scripts.build_edition catholic-study --force
shasum -a 256 build/Ethiopian_Bible_catholic-study*.epub  # after-SHA
git checkout <pre-task-1-commit> -- scripts/ && .venv/bin/python -m scripts.build_edition catholic-study --force && shasum -a 256 build/...  # before-SHA
git checkout HEAD -- scripts/
```

Expected: identical SHAs (the variant is unset everywhere). If the build is cached, `--force` bypasses; build determinism is pinned by test_byte_stability_gate.

- [ ] **Step 2: Full not-slow targeted suite** (the files this arc touched + neighbors):

Run: `.venv/bin/python -m pytest tests/test_kindle_safe.py tests/test_kindle_safe_gate.py tests/test_reader_target.py tests/test_opf_clean.py tests/test_file_split.py tests/test_popup_styles.py tests/test_marker_style.py tests/test_scripts.py -q`
Expected: green (test_scripts is big — run last; under RAM pressure run one file at a time).

- [ ] **Step 3: Pre-commit gates:** `ruff format --check .` clean (format the touched files first), `.venv/bin/python scripts/lint_rules.py` clean, mypy via the pre-commit hook.

- [ ] **Step 4: Build the kindle acceptance artifact.** Set the target via the proven API path, build, gate, restore byte-exactly:

```bash
.venv/bin/python - <<'EOF'
from pathlib import Path
from scripts.api.editions import api_save_edition_meta
from scripts.core import config
p = Path("content/editions.yaml"); orig = p.read_bytes()
Path("/tmp/editions.yaml.orig").write_bytes(orig)
r = api_save_edition_meta("catholic-study", {"target_reader": "kindle"})
assert "error" not in r, r
config.load_editions.cache_clear()
EOF
.venv/bin/python -m scripts.build_edition catholic-study --force
.venv/bin/python dev/verify_kr2_build.py build/<artifact>.epub   # gate 5 ACTIVE (stamp present)
java -jar <epubcheck-jar> build/<artifact>.epub                  # 0 errors / 0 warnings
cp build/<artifact>.epub ~/Desktop/Ethiopian_Bible_catholic-study_kindle-safe_$(date -u +%Y-%m-%dT%H%M%SZ).epub
.venv/bin/python - <<'EOF'
from pathlib import Path
Path("content/editions.yaml").write_bytes(Path("/tmp/editions.yaml.orig").read_bytes())
from scripts.core import config; config.load_editions.cache_clear()
EOF
git diff --stat content/editions.yaml  # MUST be empty
```

Also spot-verify in-zip: stylesheet.css ends with the kindle_safe block; OPF has the stamp + single dc:language; `toc-chapter-row` present, `toc-chapters` absent; notes-sections still in the markup (CSS-only).

- [ ] **Step 5: Truth records + INDEX + MATRIX_MAP.** Add this plan to `docs/superpowers/INDEX.md`; add `resolve_target_reader`/`apply_kindle_safe_css`/`apply_kindle_toc_rows`/the OPF stamp/gate 5 to `dev/MATRIX_MAP.md`'s build-pass table; SESSION_STATE/IN_FLIGHT wrap entries; board update (kindle artifact staged → user's Send-to-Kindle re-verify = the acceptance).

- [ ] **Step 6: Final commit + milestone sync** (arc close = milestone; Mac legs 1-3):

```bash
git add -A && git commit -m "kindle_safe ⑦: byte-proof + kindle acceptance artifact staged + truth records (MATRIX_MAP/INDEX/board)"
# /sync (radar-gated push to origin + github)
```

---

## Self-review checklist

- **Spec coverage:** E3013 visible notes (Task 3) ✓ · dc:language gate half (Task 6; generator half = WIN's, untouched) ✓ · K-KIN-2 rows (Task 4) ✓ · K-KIN-3 seams (Task 3 CSS) ✓ · kindle_safe gate (Task 6) ✓ · TARGET_CAPS/wizard Send-to-Kindle copy (Task 2) ✓ · one-resolver (Task 1) ✓ · 9-KJV byte-identity (Task 7 proof; every gate is additive-when-set) ✓ · acceptance = user Send-to-Kindle re-verify on the staged artifact (Task 7) ✓.
- **K-KIN-4** (`<details>` cosmetics): accepted-as-converts (permanently expanded — conversion-proof per round-1 QA); kindle TARGET_CAPS gates the option off anyway.
- **Known-stale wording:** build_one's comment at ~5376 says file-split is opt-in; it defaults ON (`DEFAULT_READER_FILE_SPLIT=True`) — fix the comment in passing during Task 4's wiring edit.
- **Type consistency:** `resolve_target_reader(edition: dict) -> str`, `is_kindle_target(edition: dict) -> bool`, `apply_kindle_safe_css(stylesheet_css: str) -> str`, `apply_kindle_toc_rows(tmp: Path, edition: dict) -> dict`, `kindle_safe_checks(zf, names, opf) -> list[str]` — used identically across tasks.
