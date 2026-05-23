# Visual QA checklist — builder-demo EPUBs

**Status: the LAST demo-readiness item (Track A `[USER]`).** Everything
mechanically verifiable is done — all **11 editions build + validate
epubcheck-clean (0 fatals / 0 errors / 0 warnings / 0 infos)** as of
2026-05-22 (`dev/CHANGELOG.md`). This pass is the human spot-check that the
EPUBs *look right* in a real reader — the one thing Claude can't self-verify.

---

## 0. Get fresh EPUBs

The committed state builds clean. Produce a fresh set from HEAD (PowerShell):

```powershell
$env:PYTHONUTF8="1"
$py = "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe"
& $py "scripts\build_edition.py" --all --force --no-parallel --version v28a-qa --output-dir "exports\_qa"
```

(Or reuse the existing `exports\_revalidate_v28a68\*.epub` — same committed
build logic, already epubcheck-clean.) `exports/` is gitignored, so neither
affects the tree. Open a `.epub` in an e-reader (Apple Books / Calibre /
Thorium), or unzip it and open an `index_split_*.html` in a browser.

---

## 1. Representative editions (open these 5 — they cover all 5 canon shapes + the extremes)

| Edition | Why this one |
|---|---|
| `ethiopian-tewahedo` | flagship — 87-book canon, all kinds |
| `scholarly-academic` | broadest — every kind incl. 26k+ topical notes, all 15 glyphs |
| `jewish-study` | most aggressive canon splice — 39 Tanakh books, **no NT** |
| `catholic-study` | deuterocanon + the BISAC OPF metadata that was repaired |
| `evangelical-reformed` | 66-book Protestant splice |

---

## 2. Per-edition checks

For each edition above, confirm:

- [ ] **Verse popups** — tap/click a verse number; a popup shows the KJV
  English text (+ Hebrew/Greek where the book has it). This is the demo
  headline (≈90.5% verse coverage). Spot-check a few books, incl. a Psalm and
  a Gospel chapter.
- [ ] **Note markers + glyphs** — inline markers render the correct symbol per
  kind (✦ topical, ⌂ Easton's dictionary, ◇ commentary, … — 15 families);
  hover/tap shows the right tooltip (the kind's title).
- [ ] **Note asides** — tapping a marker opens its note; text intact (no split
  tags, no orphaned markers pointing nowhere).
- [ ] **Theme** — the edition's theme/colors render; the cover image shows on
  the title page.
- [ ] **TOC / navigation** — the table of contents lists books in **canonical
  reading order** (Genesis → … → Revelation, then deuteros), chapters
  ascending; tapping a TOC entry jumps correctly.
- [ ] **Canon correctness** — the right books are present: jewish-study = 39
  (no NT), evangelical-reformed = 66, catholic = +deuteros, ethiopian /
  scholarly = 87.

---

## 3. Cross-edition sanity

- [ ] The 5 editions visibly DIFFER (note density, books, themes) — confirms
  the per-canon filter is doing its job.

---

## 4. If you find an issue

Note the **edition + book + chapter + what looked wrong** and hand it to the
next session — it becomes a TDD fix (reproduce → failing test → fix → rebuild
→ re-confirm epubcheck 0/0/0/0).

---

## Reference

- Build pipeline + editions×kinds matrix: `dev/MATRIX_MAP.md`.
- All-11-editions epubcheck validation + the lint cleanup: `dev/CHANGELOG.md`
  2026-05-22.
- epubcheck how-to (Java 8 + the PyPI-bundled jar): `scripts/epubcheck.py`
  (run via `--jar` + `java` on PATH).
