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

---

## Findings — 2026-05-22 (browser-level QA pass, Claude)

**Method:** unzipped the committed `exports/_revalidate_v28a68/*.epub`, served the
tree over `python -m http.server` on localhost (the managed browser blocks
`file:`), and drove the rendered XHTML in a real browser (Playwright) + hashed/
diffed the package assets. This covers every markup / render / canon / glyph /
TOC check; only the device-only items (see "Remaining") still need a human.

**PASS — verified by rendering + DOM inspection:**
- **Canon splice correct, all 5 shapes** — ethiopian + scholarly = full 87-book
  Tewahedo (Jubilees / Enoch / 2 Enoch / Meqabyan I–III / 4 Baruch / 1 Clement
  interleaved in canonical slots); catholic = full NT + Catholic deuteros
  (Tobit / Judith / Wisdom / Sirach / Baruch / Greek additions) and **no**
  Ethiopic-only books; reformed = clean 66; jewish = 39 (no NT, no deutero).
  `nav.xhtml` + the in-page ToC are both in canonical reading order.
- **Verse popups work** — `#vnote-<bk>-<c>-<v>` targets resolve with intact
  content. Genesis 1:1 = KJV + Hebrew (`dir=rtl lang=he`) + Greek (`lang=grc`);
  John 3:16 / Psalm 1:1 = KJV floor. ~109 popups/chapter; 1,413 on the Luke→John
  split file.
- **Note glyphs render** (no tofu boxes): ⌘ ‖ ◇ ⌂ ✧ across editions; scholarly
  adds **✦** topical (×80 on Genesis) + ⚖ ⊛, while the flagship has **no ✦**
  (it excludes the `topic` category) — per-edition kind filtering is visibly
  correct.
- **EPUB footnote mechanism correct** — note/verse asides are `display:none`
  (the reader reveals them as tap-popups) with 943 `epub:type` nodes on Genesis.
- **OPF metadata** — `dc:identifier` = `urn:yhwh:edition:<id>` + a uuid, **no
  ISBN** (Ω.0 pivot honored); WCAG-AA a11y block + BCP-47 lang tags present and
  actually used in the popups.
- Sole console error on any page = `favicon.ico` 404 (benign browser auto-request).

**FINDINGS for a TDD fix (next session)** — both are "feature configured but not
applied to the EPUB output." Neither breaks epubcheck/validity, but both blunt
the builder demo's per-edition differentiation (currently editions differ only
in **canon + note density**, not theme or cover):

1. **Per-edition THEME not applied.** `stylesheet.css` is byte-identical (same
   SHA256) across all 5 editions. Root cause: **no** edition sets a `theme:`
   field in `editions.yaml`, so `build_edition.py` (~L2782,
   `edition.get("theme", "classic")`) always lands on the no-op `classic`
   theme. The 4 real themes (`content/themes/{scholarly,devotional,modern,
   school}.css`) ship with the repo but reach **no** edition — notably
   scholarly-academic does not use `scholarly.css`. Fix: assign a `theme:` per
   demo edition (and/or give the themes real overrides) + a test pinning that
   two differently-themed editions produce different stylesheets.
2. **Per-edition COVER not applied.** Built `cover.jpeg` is byte-identical
   (185,316 B) across all editions and equals the master
   `epub_working/cover.jpeg`. Yet 9/11 editions declare distinct curated covers
   (`content/covers/<id>.jpg`, 660–800 KB) that preflight validates and the
   customize UI edits — but `build_edition.py` never reads `cover_image`, so the
   declared cover never reaches the EPUB. (The 2 standalone bibles set
   `cover_image: ""` on purpose.) Fix: wire `cover_image` into `build_one`
   (validate → swap `cover.jpeg` → keep the OPF `cover-image` property) + a test
   that a declared cover changes the output bytes.

**Observations (not bugs):**
- NT + most OT popups are KJV-English-only; Hebrew/Greek appear only in the ~11
  originally-wrapped books (incl. Genesis). Matches the documented he/gr dataset
  deferral.
- The stylesheet's `blockquote` rules ("Psalms, Proverbs") are vestigial —
  poetry renders as `.verse-p` paragraphs; there is no `<blockquote>` in output.

**Remaining — genuinely user/device-only (not self-verifiable):**
- Open a `.epub` on a real reader (Apple Books / Calibre / Thorium / Kindle) and
  confirm the tap-popup **overlay presentation** (not just the linked aside),
  page-turn behavior, e-ink color/justification handling, and the cover on the
  title page as the device renders it.
