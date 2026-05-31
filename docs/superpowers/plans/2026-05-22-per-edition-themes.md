# Per-Edition Themes Implementation Plan
**Status:** shipped — per-edition theme CSS

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Assign a distinct visual theme to each of the 11 editions so every built EPUB carries its own house style (the theme machinery already exists; today no edition sets `theme:`, so all fall back to the no-op `classic`).

**Architecture:** Pure config change. Add `theme: <id>` to each edition in `content/editions.yaml`; `scripts/build_edition.py` (~L2782) already appends `content/themes/<theme>.css` to that edition's `stylesheet.css` at build time. A config test pins the mapping; an integration test proves a themed build yields a distinct stylesheet.

**Tech Stack:** Python stdlib + pytest; the project's `scripts.core.config` + `scripts.build_edition`. Windows PowerShell; `$env:PYTHONUTF8="1"` required (memory `feedback_pythonutf8`). Python interpreter: `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe` (bare `python` is a broken Store stub — memory `reference_python_interpreter`).

**Commit discipline:** `continue` ≠ `save`. This project commits via `save.cmd` (PowerShell only — memory `feedback_savecmd_bash_hazard`) on explicit user "save". Each task ends at a committable **checkpoint**; do NOT auto-commit — the user saves at chosen points.

**Theme mapping (locked):**

| theme | editions |
|---|---|
| `classic` | ethiopian-tewahedo, anglican-bcp, standalone-geez, standalone-amharic |
| `scholarly` | scholarly-academic, jewish-study, lutheran-confessional |
| `devotional` | catholic-study, eastern-orthodox, coptic-orthodox |
| `modern` | evangelical-reformed |

(`school.css` stays registered for the wizard picker; no demo edition uses it.)

---

### Task 1: Pin the theme mapping + assign `theme:` to all 11 editions

**Files:**
- Create: `tests/test_themes.py`
- Modify: `content/editions.yaml` (add one `theme:` line per edition, 11 entries)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_themes.py
"""Per-edition theme assignment — every edition declares a theme so its built
EPUB carries a distinct house style (build_edition appends
content/themes/<theme>.css at build time). See
docs/superpowers/specs/2026-05-22-themes-and-multitranslation-popups-design.md."""
from __future__ import annotations

from pathlib import Path

from scripts.core import config

EXPECTED_THEMES = {
    "ethiopian-tewahedo": "classic",
    "anglican-bcp": "classic",
    "standalone-geez": "classic",
    "standalone-amharic": "classic",
    "scholarly-academic": "scholarly",
    "jewish-study": "scholarly",
    "lutheran-confessional": "scholarly",
    "catholic-study": "devotional",
    "eastern-orthodox": "devotional",
    "coptic-orthodox": "devotional",
    "evangelical-reformed": "modern",
}


class TestPerEditionThemes:
    def test_every_edition_declares_expected_theme(self):
        eds = config.editions_by_id()
        for ed_id, theme in EXPECTED_THEMES.items():
            assert ed_id in eds, f"edition {ed_id!r} missing from editions.yaml"
            assert eds[ed_id].get("theme") == theme, (
                f"{ed_id}: expected theme {theme!r}, got {eds[ed_id].get('theme')!r}"
            )

    def test_theme_css_files_exist(self):
        repo = Path(config.__file__).resolve().parents[2]
        for theme in set(EXPECTED_THEMES.values()):
            assert (repo / "content" / "themes" / f"{theme}.css").is_file(), (
                f"content/themes/{theme}.css missing"
            )
```

- [ ] **Step 2: Run the test — verify it FAILS**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest "tests/test_themes.py::TestPerEditionThemes::test_every_edition_declares_expected_theme" -v
```
Expected: FAIL — `expected theme 'classic', got None` (no edition sets `theme:` yet).

- [ ] **Step 3: Add `theme:` to each edition in `content/editions.yaml`**

Make 11 edits. Each edition's `- id:`/`canon:` pair is unique, so use it as the anchor and append a `    theme:` line (4-space indent, matching siblings). Exact edits:

```
  - id: ethiopian-tewahedo
    canon: ethiopian
→   - id: ethiopian-tewahedo
    canon: ethiopian
    theme: classic
```
```
  - id: catholic-study
    canon: catholic
→ + theme: devotional
```
```
  - id: evangelical-reformed
    canon: protestant
→ + theme: modern
```
```
  - id: jewish-study
    canon: tanakh
→ + theme: scholarly
```
```
  - id: scholarly-academic
    canon: ethiopian
→ + theme: scholarly
```
```
  - id: eastern-orthodox
    canon: orthodox
→ + theme: devotional
```
```
  - id: anglican-bcp
    canon: catholic
→ + theme: classic
```
```
  - id: lutheran-confessional
    canon: protestant
→ + theme: scholarly
```
```
  - id: coptic-orthodox
    canon: ethiopian
→ + theme: devotional
```
```
  - id: standalone-geez
    canon: ethiopian
→ + theme: classic
```
```
  - id: standalone-amharic
    canon: ethiopian
→ + theme: classic
```

For each: `old_string` = the two-line `- id:`/`canon:` block; `new_string` = same two lines + `\n    theme: <value>`. (The id makes each block unique; no `replace_all`.)

- [ ] **Step 4: Run the test — verify it PASSES**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest "tests/test_themes.py" -v
```
Expected: PASS (both tests).

- [ ] **Step 5: Checkpoint (do NOT auto-commit)**

```powershell
git diff --stat
```
Expected: `content/editions.yaml` (+11) and `tests/test_themes.py` (new). Leave staged for the user's next `save.cmd`.

---

### Task 2: Integration pin — a themed build appends the theme CSS to the edition stylesheet

**Files:**
- Modify: `tests/test_themes.py` (add the integration class)

- [ ] **Step 1: Write the test** (characterization — proves the config change reaches the EPUB end-to-end via the existing applicator)

```python
# append to tests/test_themes.py
import zipfile


class TestThemeReachesEpub:
    def test_modern_themed_build_appends_modern_css(self, tmp_path, monkeypatch):
        import scripts.build_edition as be
        from scripts.core import build_cache, config

        # Hermetic: bypass the persistent build cache.
        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)

        all_kinds = config.load_kinds()
        stats = be.build_one("evangelical-reformed", tmp_path, "theme-test", all_kinds, force=True)
        epub = Path(stats["output_path"])
        assert epub.is_file()

        with zipfile.ZipFile(epub) as zf:
            css_name = next(n for n in zf.namelist() if n.endswith("stylesheet.css"))
            css = zf.read(css_name).decode("utf-8")

        assert "=== theme: modern ===" in css, "modern theme block not appended to the edition stylesheet"
        assert ("-apple-system" in css) or ("#2563eb" in css), "modern theme CSS rules missing from the stylesheet"
```

- [ ] **Step 2: Run — verify it PASSES** (the applicator already exists; Task 1 supplied the config it needed)

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest "tests/test_themes.py::TestThemeReachesEpub" -v
```
Expected: PASS. If FAIL with "modern theme block not appended", confirm Task 1's `theme: modern` landed on `evangelical-reformed` and that `content/themes/modern.css` exists.

- [ ] **Step 3: Checkpoint** — `git diff --stat` shows the test addition; leave for the user's save.

---

### Task 3: Full-build verification (no new code — the "evidence before done" gate)

**Files:** none modified. Verification only (memory `feedback_proper_clean_correct`).

- [ ] **Step 1: Rebuild all editions from HEAD**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" "scripts\build_edition.py" --all --force --no-parallel --version v28a-themes --output-dir "exports\_themes"
```
Expected: 11 EPUBs in `exports\_themes\` (gitignored). No errors.

- [ ] **Step 2: Confirm themes differ across editions** (hash the in-EPUB stylesheets)

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -c @'
import sys, zipfile, hashlib; sys.path.insert(0, r"C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4")
from pathlib import Path
seen = {}
for ep in sorted(Path(r"C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\exports\_themes").glob("*.epub")):
    with zipfile.ZipFile(ep) as zf:
        css = zf.read(next(n for n in zf.namelist() if n.endswith("stylesheet.css")))
    seen.setdefault(hashlib.sha256(css).hexdigest()[:12], []).append(ep.name.split("_")[2])
for h, names in seen.items(): print(h, names)
'@
```
Expected: **≥4 distinct hashes** (classic / scholarly / devotional / modern groups) — NOT one hash for all (the pre-fix state).

- [ ] **Step 3: epubcheck the 4 theme representatives** (one per theme; Java 8 + bundled jar — memory `reference_epubcheck`)

Run `scripts\epubcheck.py` against `ethiopian-tewahedo` (classic), `scholarly-academic` (scholarly), `catholic-study` (devotional), `evangelical-reformed` (modern). Expected each: **0 fatals / 0 errors / 0 warnings / 0 infos**.

- [ ] **Step 4: Lint + full suite**

```powershell
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" "scripts\lint_rules.py"
$env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest "tests/test_themes.py" "tests/test_build_smoke.py" -v
```
Expected: `lint_rules` 16/0/0; themes + build-smoke tests PASS.

- [ ] **Step 5: Browser spot-check (optional, self-serviceable QA — memory `feedback_visual_qa_self_serviceable`)**

Unzip `evangelical-reformed` (modern) + `ethiopian-tewahedo` (classic) → `python -m http.server` → open an `index_split_*.html` of each in the browser; confirm reformed renders sans-serif/blue-accent vs ethiopian's serif. (Device-only checks stay with the user.)

- [ ] **Step 6: Checkpoint** — repo clean; update `dev/SESSION_STATE.md` + `dev/CHANGELOG.md` (themes shipped) per the continuity protocol; user saves via `save.cmd`.

---

## Self-review notes (author)

- **Spec coverage:** implements §4.1 (themes) of the design spec in full. Popups (§4.2–4.4, Phases 1–4) are a **separate plan** (data-dependent; not in this file).
- **No placeholders:** all test code + edits + commands are concrete.
- **Type/name consistency:** `config.editions_by_id()`, `config.load_kinds()`, `be.build_one(edition_id, out_dir, version, all_kinds, force=...)`, `stats["output_path"]` — match `tests/test_build_smoke.py`.
