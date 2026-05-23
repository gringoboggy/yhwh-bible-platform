# Plan B1 — Popup Multi-Version Model Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Refactor the verse-popup model from fixed `{english, hebrew, greek}` slots to an ordered **list of versions**, driven by one shared **version registry**, so later phases can drop in more PD translations (Douay, JPS, Vulgate, Arabic, Greek-NT…) by data + one registry line — no model change.

**Architecture:** Today the *bake* (`generate_verse_popups.py`) hardcodes three sources and the *strip* (`build_edition.py`) owns a `POPUP_LANGUAGES` map. B1 lifts the registry into `scripts/core/popup_versions.py` (single source of truth), makes `build_vnote_aside` take a version list, generalizes harvesting, and adds an identity **versification seam** (`normalize_coord`) where per-source remaps land in Phases 2–3. The existing class-based stripper needs only the expanded registry. **No new translation data in B1** — with only kjv/wlc/lxx-greek registered, a regen reproduces today's asides byte-for-byte (the safety pin).

**Tech Stack:** Python stdlib + pytest; `scripts.core.translations`, `scripts.core.config`. Windows PowerShell; `$env:PYTHONUTF8="1"`; interpreter `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe`.

**Commit discipline:** `continue` ≠ `save`. Commit via `save.ps1`/`save.cmd` (PowerShell only) on explicit user "save". Each task ends at a committable checkpoint; do NOT auto-commit. The pre-commit hook runs `ruff format --check` + `lint_rules.py` — run `python -m ruff format <files>` before saving.

---

## File Structure

- **Create** `scripts/core/popup_versions.py` — the version registry + legacy aliases + `normalize_coord` seam. One responsibility: "what popup versions exist and how is each rendered/located." Imported by both the bake and the build.
- **Modify** `scripts/generate_verse_popups.py` — `build_vnote_aside` (list-based), `harvest_existing_langs` (all versions), `_wrap_and_build_asides` (source every registered version).
- **Modify** `scripts/build_edition.py` — replace the inline `POPUP_LANGUAGES` dict with a re-export from `popup_versions`; add legacy-alias resolution in `_resolve_popup_languages`.
- **Test** `tests/test_popup_versions.py` (new).

---

### Task 1: The shared version registry (`scripts/core/popup_versions.py`)

**Files:** Create `scripts/core/popup_versions.py`; Test `tests/test_popup_versions.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_popup_versions.py
"""Multi-version popup registry — single source of truth for which translation
versions a verse popup can carry, how each is rendered, and how its coordinate
maps onto the canonical (KJV) verse system. See
docs/superpowers/specs/2026-05-22-themes-and-multitranslation-popups-design.md."""
from __future__ import annotations

from scripts.core import popup_versions as pv


class TestVersionRegistry:
    def test_core_versions_present(self):
        for vid in ("kjv", "wlc", "lxx-greek"):
            assert vid in pv.VERSION_REGISTRY, f"{vid} missing from registry"

    def test_kjv_keeps_legacy_content_class(self):
        # back-compat: KJV English stays in the recovered-base 'vnote-text'
        assert pv.VERSION_REGISTRY["kjv"]["content_class"] == "vnote-text"
        assert pv.VERSION_REGISTRY["wlc"]["content_class"] == "vnote-hebrew"
        assert pv.VERSION_REGISTRY["lxx-greek"]["content_class"] == "vnote-greek"

    def test_each_version_has_required_fields(self):
        for vid, spec in pv.VERSION_REGISTRY.items():
            for key in ("label", "content_class", "lang", "dir", "has_label_para", "translation_id"):
                assert key in spec, f"{vid} registry entry missing {key!r}"
            assert spec["dir"] in ("ltr", "rtl")

    def test_legacy_aliases_resolve(self):
        assert pv.resolve_version_id("english") == "kjv"
        assert pv.resolve_version_id("hebrew") == "wlc"
        assert pv.resolve_version_id("greek") == "lxx-greek"
        assert pv.resolve_version_id("kjv") == "kjv"      # identity for real ids
        assert pv.resolve_version_id("nope") is None       # unknown -> None

    def test_normalize_coord_identity_default(self):
        # B1: no per-source remaps yet — every adapter is identity.
        assert pv.normalize_coord("lxx-greek", "psa", 23, 1) == ("psa", 23, 1)
        assert pv.normalize_coord("kjv", "gen", 1, 1) == ("gen", 1, 1)
```

- [ ] **Step 2: Run — verify FAIL**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest "tests/test_popup_versions.py::TestVersionRegistry" -v
```
Expected: FAIL — `ModuleNotFoundError: scripts.core.popup_versions`.

- [ ] **Step 3: Create `scripts/core/popup_versions.py`**

```python
"""Verse-popup version registry — the single source of truth for which
translation versions a popup can carry, how each renders, and how its
coordinate maps onto the canonical (KJV/WEB) verse numbering.

Both the bake (scripts/generate_verse_popups.py) and the per-edition build
(scripts/build_edition.py) import from here, so adding a version is one entry
plus its ingested data — no model change.

`content_class` is the literal CSS class of the version's content <p>. KJV
keeps the recovered-base 'vnote-text' for byte-compatibility; every other
version gets 'vnote-<id>'. `translation_id` is the id in
scripts.core.translations. `order` sets render order within a popup.
"""
from __future__ import annotations

# id -> spec. `order` ascending = render order (English first, then originals,
# then secondary versions). Versions with no ingested data simply never appear
# (the bake includes a version only when get_verse returns text).
VERSION_REGISTRY: dict[str, dict] = {
    "kjv":        {"label": "King James Version", "content_class": "vnote-text",      "lang": "en",  "dir": "ltr", "has_label_para": False, "translation_id": "kjv",                 "order": 10},
    "wlc":        {"label": "Hebrew (Masoretic / WLC)", "content_class": "vnote-hebrew", "lang": "he", "dir": "rtl", "has_label_para": True,  "translation_id": "wlc",                 "order": 20},
    "lxx-greek":  {"label": "Greek (Septuagint / Brenton)", "content_class": "vnote-greek", "lang": "grc", "dir": "ltr", "has_label_para": True, "translation_id": "lxx-brenton-greek",  "order": 30},
    "greek-nt":   {"label": "Greek (Textus Receptus)", "content_class": "vnote-greek-nt", "lang": "grc", "dir": "ltr", "has_label_para": True, "translation_id": "byzantine-greek",     "order": 35},
    "brenton-en": {"label": "English (Brenton LXX)", "content_class": "vnote-brenton-en", "lang": "en", "dir": "ltr", "has_label_para": True, "translation_id": "lxx-brenton-english", "order": 40},
    "douay":      {"label": "Douay-Rheims", "content_class": "vnote-douay",            "lang": "en",  "dir": "ltr", "has_label_para": True,  "translation_id": "douay-rheims",        "order": 50},
    "jps":        {"label": "JPS (1917)", "content_class": "vnote-jps",                "lang": "en",  "dir": "ltr", "has_label_para": True,  "translation_id": "jps",                 "order": 60},
    "vulgate":    {"label": "Latin (Clementine Vulgate)", "content_class": "vnote-vulgate", "lang": "la", "dir": "ltr", "has_label_para": True, "translation_id": "vulgate-clementine", "order": 70},
    "arabic":     {"label": "Arabic (Van Dyck)", "content_class": "vnote-arabic",      "lang": "ar",  "dir": "rtl", "has_label_para": True,  "translation_id": "arabic-vandyke",      "order": 80},
}

# Legacy popup-language ids (pre-B1 editions / baked asides) -> version id.
_ALIASES = {"english": "kjv", "hebrew": "wlc", "greek": "lxx-greek"}

ALL_VERSION_IDS: tuple[str, ...] = tuple(VERSION_REGISTRY.keys())


def resolve_version_id(token: str) -> str | None:
    """Map a legacy language id or a version id to a registry id, else None."""
    if token in VERSION_REGISTRY:
        return token
    return _ALIASES.get(token)


def normalize_coord(version_id: str, book: str, ch: int, vs: int) -> tuple[str, int, int]:
    """Map a canonical (KJV) coordinate to the version's own coordinate.

    B1: identity for every version (no per-source remaps yet). Phases 2–3 add
    per-source remap tables here for the known Hebrew/LXX/Vulgate divergence
    loci (Psalm titles, Daniel additions, Joel/Malachi splits, …).
    """
    return (book, ch, vs)
```

- [ ] **Step 4: Run — verify PASS**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest "tests/test_popup_versions.py::TestVersionRegistry" -v
```
Expected: PASS (5 tests).

- [ ] **Step 5: Checkpoint** — `git status --short` shows the new module + test; leave for user save.

---

### Task 2: `build_vnote_aside` becomes list-based

**Files:** Modify `scripts/generate_verse_popups.py:21-42` (`build_vnote_aside`); Test `tests/test_popup_versions.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_popup_versions.py
class TestBuildVnoteAsideListBased:
    def _versions(self):
        return [
            {"id": "kjv", "label": "King James Version", "lang": "en", "dir": "ltr", "has_label_para": False, "content_class": "vnote-text", "text": "In the beginning..."},
            {"id": "wlc", "label": "Hebrew (Masoretic / WLC)", "lang": "he", "dir": "rtl", "has_label_para": True, "content_class": "vnote-hebrew", "text": "בְּרֵאשִׁית"},
        ]

    def test_renders_one_paragraph_per_version(self):
        from scripts.generate_verse_popups import build_vnote_aside
        html = build_vnote_aside(code="gen", ch=1, vs=1, title="Genesis", versions=self._versions())
        assert 'id="vnote-gen-1-1"' in html
        assert 'epub:type="footnote"' in html
        assert '<p class="vnote-text">In the beginning...</p>' in html
        assert '<p class="vnote-source-label">Hebrew (Masoretic / WLC)</p>' in html
        assert '<p class="vnote-hebrew" dir="rtl" lang="he">בְּרֵאשִׁית</p>' in html
        # KJV has_label_para False -> no source-label before vnote-text
        assert '<p class="vnote-source-label">King James Version</p>' not in html
        assert 'href="#v-gen-1-1"' in html  # back-link preserved

    def test_empty_versions_yields_placeholder(self):
        from scripts.generate_verse_popups import build_vnote_aside
        html = build_vnote_aside(code="gen", ch=1, vs=1, title="Genesis", versions=[])
        assert "vnote-empty" in html
```

- [ ] **Step 2: Run — verify FAIL**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest "tests/test_popup_versions.py::TestBuildVnoteAsideListBased" -v
```
Expected: FAIL — `build_vnote_aside() got an unexpected keyword argument 'versions'`.

- [ ] **Step 3: Replace `build_vnote_aside` in `scripts/generate_verse_popups.py`**

```python
def build_vnote_aside(*, code: str, ch: int, vs: int, title: str, versions: list[dict]) -> str:
    """Build one ``<aside class="vnote">`` from an ordered list of version
    dicts ``{id, label, lang, dir, has_label_para, content_class, text}``.
    ``text`` is plain (escaped here) for ``lang in (en, la, ar)``; pre-formatted
    HTML fragments for original-language scripts pass through (already escaped
    at ingest)."""
    vid = f"vnote-{code}-{ch}-{vs}"
    parts = [
        f'<aside class="vnote" id="{vid}" epub:type="footnote"><p><strong>{_html.escape(title)} {ch}:{vs}.</strong></p>'
    ]
    rendered = False
    for v in versions:
        text = v.get("text")
        if not text:
            continue
        if v.get("has_label_para"):
            parts.append(f'\n  <p class="vnote-source-label">{_html.escape(v["label"])}</p>')
        dir_attr = f' dir="{v["dir"]}"' if v.get("dir") == "rtl" else ""
        lang_attr = f' lang="{v["lang"]}"' if v.get("lang") else ""
        parts.append(f'\n  <p class="{v["content_class"]}"{dir_attr}{lang_attr}>{_html.escape(text)}</p>')
        rendered = True
    if not rendered:
        parts.append(_EMPTY_TEXT)
    parts.append(f'\n<p><a href="#v-{code}-{ch}-{vs}" class="vnote-back" title="Back">↩</a></p></aside>')
    return "".join(parts)
```

Note: the original escaped `english` but passed `hebrew`/`greek` as trusted pre-formatted HTML. Here all `text` is escaped uniformly. Verify in Task 6 that the regen output stays byte-identical for he/gr; if the ingested originals contain markup that must survive, add a per-version `trusted_html: bool` flag to the registry and skip escaping for those. (KJV/WLC/LXX plain text → escaping is correct.)

- [ ] **Step 4: Run — verify PASS**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest "tests/test_popup_versions.py::TestBuildVnoteAsideListBased" -v
```
Expected: PASS (2 tests).

- [ ] **Step 5: Checkpoint.**

---

### Task 3: Generalize `harvest_existing_langs` to all versions

**Files:** Modify `scripts/generate_verse_popups.py:64-82`; Test `tests/test_popup_versions.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_popup_versions.py
class TestHarvestAllVersions:
    SAMPLE = (
        '<aside class="vnote" id="vnote-gen-1-1" epub:type="footnote">'
        '<p class="vnote-text">In the beginning</p>'
        '<p class="vnote-source-label">Hebrew (Masoretic / WLC)</p>'
        '<p class="vnote-hebrew" dir="rtl" lang="he">בְּרֵאשִׁית</p>'
        '<p class="vnote-source-label">Latin (Clementine Vulgate)</p>'
        '<p class="vnote-vulgate" lang="la">In principio</p>'
        '</aside>'
    )

    def test_harvests_every_registered_version(self):
        from scripts.generate_verse_popups import harvest_existing_langs
        got = harvest_existing_langs(self.SAMPLE)
        entry = got["vnote-gen-1-1"]
        assert entry["wlc"] == "בְּרֵאשִׁית"
        assert entry["vulgate"] == "In principio"
        assert entry["kjv"] == "In the beginning"
```

- [ ] **Step 2: Run — verify FAIL** (`KeyError: 'vulgate'` or `'kjv'` — old harvest only kept hebrew/greek).

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest "tests/test_popup_versions.py::TestHarvestAllVersions" -v
```

- [ ] **Step 3: Replace `harvest_existing_langs` in `scripts/generate_verse_popups.py`**

```python
def harvest_existing_langs(text: str) -> dict[str, dict[str, str | None]]:
    """Parse every existing ``vnote`` aside -> ``{vnote_id: {version_id: text|None}}``
    for every registered version's content class, so a uniform regen never drops
    content the resolver can no longer reproduce (e.g. originals ingested before
    a translation file existed)."""
    from scripts.core import popup_versions as pv

    class_to_id = {spec["content_class"]: vid for vid, spec in pv.VERSION_REGISTRY.items()}
    out: dict[str, dict[str, str | None]] = {}
    for m in _ASIDE_RE.finditer(text):
        block = m.group(0)
        entry: dict[str, str | None] = {}
        for cls, vid in class_to_id.items():
            cm = re.search(rf'<p class="{re.escape(cls)}"[^>]*>(.*?)</p>', block, re.DOTALL)
            entry[vid] = cm.group(1) if cm else None
        out[m.group(1)] = entry
    return out
```

- [ ] **Step 4: Run — verify PASS.**
- [ ] **Step 5: Checkpoint.**

---

### Task 4: Bake sources every registered version (`_wrap_and_build_asides`)

**Files:** Modify `scripts/generate_verse_popups.py:187-195`; Test `tests/test_popup_versions.py`

- [ ] **Step 1: Write the failing test** (unit-test the per-verse version assembly via a small extracted helper)

```python
# append to tests/test_popup_versions.py
class TestAssembleVersionsForVerse:
    def test_includes_only_versions_with_text(self, monkeypatch):
        import scripts.generate_verse_popups as gvp
        from scripts.core import translations as tx

        # kjv + wlc have text for gen 1:1; everything else returns None.
        def fake_get_verse(tid, code, ch, vs):
            return {"kjv": "In the beginning", "wlc": "בְּרֵאשִׁית"}.get(
                {"kjv": "kjv", "wlc": "wlc"}.get(tid, ""), None
            )
        monkeypatch.setattr(tx, "get_verse", fake_get_verse)

        versions = gvp.assemble_versions_for_verse("gen", 1, 1, harvested={})
        ids = [v["id"] for v in versions]
        assert ids == ["kjv", "wlc"]                  # order = registry order, text-only
        assert versions[0]["content_class"] == "vnote-text"
        assert versions[1]["dir"] == "rtl"
```

- [ ] **Step 2: Run — verify FAIL** (`assemble_versions_for_verse` not defined).

- [ ] **Step 3: Add the helper + rewire `_wrap_and_build_asides` in `scripts/generate_verse_popups.py`**

Add the helper (near `build_vnote_aside`):

```python
def assemble_versions_for_verse(code: str, ch: int, vs: int, *, harvested: dict) -> list[dict]:
    """Build the ordered version list for one verse: every registered version
    that has text (live via translations.get_verse at its normalized coord, or
    harvested from the prior aside), in registry order."""
    from scripts.core import popup_versions as pv

    vid = f"vnote-{code}-{ch}-{vs}"
    h = harvested.get(vid, {})
    out: list[dict] = []
    for version_id in sorted(pv.ALL_VERSION_IDS, key=lambda i: pv.VERSION_REGISTRY[i]["order"]):
        spec = pv.VERSION_REGISTRY[version_id]
        nb, nc, nv = pv.normalize_coord(version_id, code, ch, vs)
        text = tx.get_verse(spec["translation_id"], nb, nc, nv) or h.get(version_id)
        if not text:
            continue
        out.append({
            "id": version_id, "label": spec["label"], "lang": spec["lang"],
            "dir": spec["dir"], "has_label_para": spec["has_label_para"],
            "content_class": spec["content_class"], "text": text,
        })
    return out
```

Then replace the aside-building block in `_wrap_and_build_asides` (currently L189-195) with:

```python
    new_asides = []
    for vs in dict.fromkeys(verse_numbers_in_region(region_html)):
        versions = assemble_versions_for_verse(code, ch, vs, harvested=harvested)
        new_asides.append(build_vnote_aside(code=code, ch=ch, vs=vs, title=title, versions=versions))
        stats["asides_built"] += 1
```

(Remove the old `eng = / he = / gr =` lines — `assemble_versions_for_verse` replaces them.)

- [ ] **Step 4: Run — verify PASS** (`tests/test_popup_versions.py::TestAssembleVersionsForVerse`).
- [ ] **Step 5: Checkpoint.**

---

### Task 5: Build side imports the shared registry; stripper + resolve handle version ids

**Files:** Modify `scripts/build_edition.py` (`POPUP_LANGUAGES` → re-export; `_resolve_popup_languages` alias-aware); Test `tests/test_popup_versions.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_popup_versions.py
class TestBuildSideRegistry:
    def test_build_edition_popup_languages_is_the_shared_registry(self):
        import scripts.build_edition as be
        from scripts.core import popup_versions as pv
        for vid in pv.VERSION_REGISTRY:
            assert vid in be.POPUP_LANGUAGES, f"{vid} not exposed in build_edition.POPUP_LANGUAGES"
        assert be.POPUP_LANGUAGES["kjv"]["content_class"] == "vnote-text"

    def test_resolve_popup_languages_accepts_legacy_ids(self):
        import scripts.build_edition as be
        # an edition that still lists legacy ids must resolve to version ids
        ed = {"popup_languages_default": ["english", "hebrew"]}
        got = be._resolve_popup_languages(ed, "gen")
        assert "kjv" in got and "wlc" in got
```

- [ ] **Step 2: Run — verify FAIL** (`kjv` not in `be.POPUP_LANGUAGES`; legacy resolve returns `{"english","hebrew"}`).

- [ ] **Step 3: Edit `scripts/build_edition.py`**

(a) Replace the inline `POPUP_LANGUAGES = {...}` dict (L669-702) with a derivation from the shared registry (keep the module-level name + `ALL_POPUP_LANGUAGES` so the stripper and route code are unchanged):

```python
from scripts.core import popup_versions as _pv

# Version registry is the single source of truth (scripts/core/popup_versions.py).
# Keep the historical name + shape the stripper expects: id -> {label,
# content_class, has_label_para}. Legacy ids (english/hebrew/greek) alias in.
POPUP_LANGUAGES: dict[str, dict] = {
    vid: {"label": s["label"], "content_class": s["content_class"], "has_label_para": s["has_label_para"]}
    for vid, s in _pv.VERSION_REGISTRY.items()
}
ALL_POPUP_LANGUAGES: tuple[str, ...] = tuple(POPUP_LANGUAGES.keys())
```

(b) In `_resolve_popup_languages` (L707-727) map tokens through the registry's alias resolver before the membership filter — replace the final `return {...}` line:

```python
    resolved = {_pv.resolve_version_id(t) for t in (raw or [])}
    return {v for v in resolved if v in POPUP_LANGUAGES}
```

(The `set(ALL_POPUP_LANGUAGES)` default-all branch and the per-book/default precedence are unchanged.)

- [ ] **Step 4: Run — verify PASS**, then run the existing popup-language tests to confirm no regression:

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest "tests/test_popup_versions.py" -v
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest "tests/" -k "popup" -v
```
Expected: all PASS (the class-based stripper already handles the new content classes; existing per-book popup tests still green via the aliases).

- [ ] **Step 5: Checkpoint.**

---

### Task 6: Byte-compatible regen + full verification (the safety pin)

**Files:** none modified — verification. Plus: add `.vnote-*` CSS for the new version classes so future data renders (mirrors `.vnote-hebrew`).

- [ ] **Step 1: Add CSS for the new version classes** in the stylesheet source (`scripts/apply_style.py` where `.vnote-hebrew`/`.vnote-greek` are defined — grep `vnote-hebrew`). Add `.vnote-greek-nt`, `.vnote-brenton-en`, `.vnote-douay`, `.vnote-jps`, `.vnote-vulgate`, `.vnote-arabic` mirroring the existing source-language block (italic/indent; `.vnote-arabic{direction:rtl}`). No-op until data lands, but keeps rendering correct then.

- [ ] **Step 2: Regenerate popups on a sample book and diff against HEAD** — with only kjv/wlc/lxx-greek carrying data, output MUST be unchanged:

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" "scripts\generate_verse_popups.py" --books gen
git diff --stat -- epub_working/
```
Expected: **0 changed lines** in `epub_working/` for `gen` (byte-identical regen — the refactor is behavior-preserving with today's data). If there IS a diff, inspect it: the only legitimate diffs are escaping/ordering changes — reconcile via the `trusted_html` flag note in Task 2 before proceeding.

- [ ] **Step 3: Full regen + build + verify**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" "scripts\generate_verse_popups.py"
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest "tests/test_verse_popups.py" "tests/test_popup_versions.py" "tests/test_build_smoke.py" -v
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" "scripts\lint_rules.py"
```
Expected: regen reports same vn-link/aside counts as the 2026-05-22 baseline (36,556 popups); all tests PASS; `lint_rules` 16/0/0.

- [ ] **Step 4: epubcheck the flagship** (Java 8 + bundled jar — see `dev/CHANGELOG`/memory): build `ethiopian-tewahedo`, run `scripts/epubcheck.py --jar <site-packages/epubcheck/epubcheck.jar>` → **0/0/0/0**.

- [ ] **Step 5: Checkpoint** — update `dev/SESSION_STATE.md` + `dev/CHANGELOG.md` (B1 shipped: model refactor, no behavior change, ready for Phase-2 data); user saves via `save.ps1`.

---

## Self-review notes (author)

- **Spec coverage:** implements spec §4.2 (multi-version model) + §4.3 registry/stripper + the §4.4 `normalize_coord` seam (identity in B1; per-source maps are Phases 2–3). Per-edition `popup_versions` *content* (the tradition mapping) is Phase 4, not B1.
- **No placeholders:** all test + impl code is concrete; exact files/lines named (`generate_verse_popups.py:21-42,64-82,187-195`; `build_edition.py:669-702,707-727`).
- **Type/name consistency:** `pv.VERSION_REGISTRY`, `pv.ALL_VERSION_IDS`, `pv.resolve_version_id`, `pv.normalize_coord`, `build_vnote_aside(..., versions=)`, `assemble_versions_for_verse(code,ch,vs,*,harvested)` used consistently across tasks. `POPUP_LANGUAGES`/`ALL_POPUP_LANGUAGES` names preserved on the build side so the unchanged stripper + routes keep working.
- **Risk pinned:** Task 6 Step 2 is the byte-compat guard — if the list-based rebuild diverges from today's asides on existing data, it's caught on one book before the full regen.
