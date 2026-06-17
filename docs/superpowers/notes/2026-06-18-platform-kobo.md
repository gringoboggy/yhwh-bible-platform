# Platform research — Kobo e-ink (Round 9)

**Status:** FINDINGS — Round 9 WIN lane `platform-kobo` dimension.
**Date:** 2026-06-18 · **Lane:** win · **Dim:** `platform-kobo`

---

## 1. Our target UX (non-negotiables)

From `dev/EREADERS.md` §Kobo, device QA rounds 4–13, and the v1.0.0 plan:

| Surface | Target behavior |
|---|---|
| **Delivery** | `.kepub.epub` sideloaded (kepubify v4.0.4 PINNED — plain `.epub` uses ADE engine, **no popups**) |
| **Translation popups** | `vn-link` at verse start → Footnote-preview dialog; tag-stripped plain text in **reading font**; multi-script via `dc:language` fallbacks + Cardo font-pack |
| **Study notes** | Default **backmatter glossary** (K-R9c/K-R13): per-category coloured badges at verse end → **navigate** to Study Notes section (not preview popup); translation popups unchanged |
| **Popup integrity** | No "teleport to chapter 1" / "nothing happened" from oversized preview targets |
| **ToC** | Flat chapter pills (no `<details>`); native nav book-level + nested Study Notes per-book links |
| **Page breaks** | New spine file only on e-ink — CSS `page-break-*` all **N** per Kobo spec |
| **Fonts** | Embedded fonts in body; preview uses reading font + OPF language chain; Cardo deselect/re-select refresh after sideload |
| **Catalog** | M3 column ships 45× `.kepub.epub`; user round-9 taps gate **live** claim |

**Round-13 device proof (2026-06-15):** Gen 1:1 all six study badges **teleport** to glossary; translation popups still **pop**; Kobo-safe badge glyphs visible (`H`, `◇2`, `†`, `⌘7`, `*`). See `notes/2026-06-15-kobo-round13-device-qa.md`.

---

## 2. Official format support

| Topic | Vendor says | Our build uses |
|---|---|---|
| EPUB version | EPUB 3.3 preferred; 2.0.1–3.3 supported ([Kobo EPUB Guidelines](https://github.com/kobolabs/epub-spec)) | EPUB 3.3; kepubify v4.0.4 post-process |
| Popup footnotes (`noteref`/`aside`) | "Footnotes/Endnotes are fully supported across Kobo platforms" (same spec) — **no documented size cap**; e-ink uses Nickel WebKit when `.kepub.epub` | `epub:type="noteref"` + `epub:type="footnote"` asides; study badges use padded footnote targets (K-R13) to force navigate path |
| Embedded fonts | TTF/OTF/WOFF; user selects Publisher Default / Document Default; FXL locks fonts | OFL pack (`dist/yhwh-kobo-font-pack.zip`) + embedded CSS fonts in book |
| Page-break CSS | **All 12 properties = N on EPD** (e-ink); new HTML file = guaranteed break | `apply_file_split` spine pieces (~405 KB max); no CSS-break reliance on e-ink |
| Collapsible ToC (`<details>`) | Unknown on e-ink WebKit; KOReader (crengine) shows flat | Gated off (`TARGET_CAPS.eink.toc_expandable: false`) |
| RTL / multi-script | RTL supported; languages via OPF + `lang` attrs | Multi-value `dc:language` block (non-kindle) + per-span `lang`; preview strips tags → OPF is the only preview signal |

### Kobo Footnote-preview limits (device-proven, not vendor-documented)

The preview dialog behavior is **heuristic**, measured across rounds 4–6:

| Measure | Proven bracket | Build default | Gate |
|---|---|---|---|
| **Tag-stripped chars** (what preview extracts) | Pops ≤ **4,498** · declines ≥ **5,500** (8/9 taps; gen 35:18 anomaly pending re-tap) | `note_popup_split_cap` = **4,400** (`build_edition.py:3023`) | `verify_kr2_build.py` gate **4g** (`POP_FLOOR = 4_498`) |
| **Serialized kepub bytes** (Nickel forward-scan) | Opens ≤ **8,858 B** · refuses > **9,273 B** (round-6d) | `note_popup_split_byte_cap` = **8,858** (eink only) | gate **4n** (`BYTE_FLOOR = 8_858`, kepub only) |
| **Preview rendering** | Strips **all markup**; collapses `\n`; uses **reading font** + OPF `dc:language` for script fallbacks — **not** embedded per-span fonts | `.vn-sep` U+2028 separators (K-R4-1); `add_eink_vnote_preview_breaks` | K-R4-1 separators in `build_edition.py:2479–2526` |
| **Large-target fallback** | Decline → navigate to **piece top** (hidden aside = file start) | Study notes → backmatter navigate (K-R13 pad ≥ 5,600 stripped) | gate **4g-bis** (`GLOSSARY_DECLINE_HI = 7_748`) |

**Sources (cite URLs):**

- Kobo EPUB spec (page breaks, footnotes, fonts, kepub sideload): https://github.com/kobolabs/epub-spec
- Kobo page-break grid (EPD = N for all): `notes/2026-06-09-kepub-pagebreak-research.md`
- Device brackets: `notes/2026-06-10-kobo-round4-device-qa.md` §K-R4-2 · `notes/2026-06-10-kobo-round5-device-qa.md` §K-R5-2 · `notes/2026-06-11-kobo-round6-device-qa.md` §K-R6-2
- Calibration tool: `dev/kobo_tap_calibration.py`

---

## 3. How others achieved similar goals

| Technique | Who / where | Applies to us? |
|---|---|---|
| **KePub conversion** (`.kepub.epub`) to trigger Nickel popups | Kobo sideload docs; MobileRead kepubify threads | ✅ Required — `build_format_matrix.py:256–262` kepubify post-process |
| **Cap popup payload** below reader heuristic | Nickel/crengine community (~5k chars); our round-5 pin | ✅ Shipped — dual stripped + byte budgets |
| **Split oversized notes** at category / paragraph boundaries | Our round-4 design `(a)+(b)`; Easton `hist` monoliths | ✅ `_split_popup_units` in `apply_badge_markers` |
| **Move study content off preview path** | K-R9 glossary backmatter + K-R13 padded `epub:type="footnote"` targets | ✅ Default `reader_eink_study_layout: backmatter` |
| **OPF multi-language declarations** for script fallbacks | K-R2-5 / K-R5-6 device proof (Arabic popups) | ✅ `patch_opf` kindle-gated single-lang; all else restore 6-value block (`build_edition.py:1719–1755`) |
| **Reading-font + language refresh** after sideload | Round-5 K-R5-1; round-8 K-R8-5 | ✅ Documented mitigations in `EREADERS.md` |
| **Prefix-free aside ids** (`-s1..-s9`) | K-R6-2 Nickel forward-scan forensics | ✅ Always-suffixed units; gate 4m |

---

## 4. Gap vs our pipeline

| Gap | `build_edition` / post-process / `TARGET_CAPS` | Severity |
|---|---|---|
| **gen 35:18 anomaly** — 3,509 stripped declined in round-5; re-tap never recorded | Cap assumes 4,498 floor; vnote translation asides only **WARN** in gate 4g (`verify_kr2_build.py:207–208`) | **MED** — one inversion could widen decline factor |
| **`kobo_tap_calibration.py` stale bracket** — still `3,313 < T ≤ 7,748` (round-4) not round-5 `4,498 / 5,500` | `dev/kobo_tap_calibration.py:28–31` | **LOW** — misleading tap-list for future calibration |
| **`EREADERS.md` drift** — summary still says "M3 catalog **hold**" + "K-R7-4b **pending**" while round-9/13 PASS and catalog M3 `live` | `dev/EREADERS.md:20` vs `website/src/data/catalog.json` kobo column | **MED** — truth-record skew |
| **Glossary piece size** — some pieces ~700 KB (under 73 MB crash, above 400 KB comfort) | `split_study_glossary_document` 8 KB row cap in tests; round-9 notes tune later | **LOW** |
| **Clement / deuterocanon** — verse translator numbers not clickable | Separate inject gap (`notes/2026-06-15-kobo-round9-device-qa.md` P2) | **LOW** — out of K-R4-2 scope |
| **Gate 4n raw UTF-8** vs true post-kepubSpan serialized size | `verify_kr2_build.py:333` uses `len(m.group(0).encode("utf-8"))` not koboSpan-inflated measure | **LOW** — build estimator (85 B/seg) is the real guard |
| **Legacy `popup` study layout** still in wizard/customize | `reader_eink_study_layout: popup` re-enables K-R4-2 split badges | **LOW** — opt-in legacy; default is backmatter |

---

## 5. Options ranked

### Option A (recommended) — **Ship the proven stack; close QA gaps**

- **Change:** Treat K-R4-2 + K-R6-2 + K-R9/K-R13 as **closed in builder**; run round-9 device matrix on latest `ethiopian-tewahedo` kepub; record PASS in `EREADERS.md`; re-tap gen 35:18 once; sync `kobo_tap_calibration.py` bracket to round-5 values.
- **Files:** `dev/EREADERS.md` · `dev/kobo_tap_calibration.py` · `notes/2026-06-15-kobo-round9-device-qa.md` (verdict fill) · optional M3 re-fan if artifact SHA changes
- **Device proof:** Round-13 PASS + round-9 P0 matrix (glossary crash regressions) + gen 35:18 re-tap
- **Risk:** Low — code path is test-pinned (`tests/test_popup_split.py` 52 tests); risk is stale docs/catalog claim ahead of user sign-off

### Option B — **Belt-and-braces for translation `vnote` declines**

- **Change:** If gen 35:18 re-tap reproduces decline under 4,400 cap, add non-hidden navigate anchor adjacent to `vn-link` OR split rare oversized **translation** asides (today only WARN, not FAIL). Do **not** regress study backmatter navigate UX.
- **Files:** `scripts/build_edition.py` (`add_eink_vnote_preview_breaks` / vnote emitters) · `dev/verify_kr2_build.py` (promote vnote WARN → FAIL once probed)
- **Device proof:** `dev/kobo_tap_calibration.py` on post-fix kepub; gen 35:18 + max `vnote-*` stripped distribution
- **Risk:** Medium — anchor research from round-4 option (b) was never device-proven for translation popups

### Option C (decline / defer) — **Revert to legacy popup study mode**

- **Change:** Set `reader_eink_study_layout: popup` catalog-wide — restores K-R4-2 multi-badge `(1/7)` clusters and preview-decline exposure for study notes; abandons K-R9 glossary UX that fixed 73 MB crash.
- **Files:** editions.yaml per-edition flags · `apply_badge_markers` eink_backmatter branch off
- **Device proof:** Would re-open K-R7-2d/2e page-count and round-8 FAIL class
- **Risk:** **High** — explicitly rejected by round-8/9/13 arc; only for emergency rollback

---

## 6. Study glossary backmatter (K-R9 → K-R13)

**Problem:** Merged `verse-notes` popups exceeded preview limits; monolithic `index_split_900.html` (73 MB) crashed Kobo (round-8 FAIL).

**Shipped architecture:**

| Layer | Implementation | File:line |
|---|---|---|
| Layout resolver | Default `backmatter`; legacy `popup` / opt-in `inline` | `build_edition.py:2207–2228` |
| Glossary emit | `inject_eink_study_backmatter` → `index_split_900.html` | `matter_pages.py:1035–1093` · `build_edition.py:7386–7389` |
| Piece split | `split_study_glossary_document` → 107 pieces (max ~720 KB) | `build_edition.py:4836+` · `tests/test_file_split.py:971+` |
| Verse badges | Per-category coloured chips → `epub:type="noteref"` | `build_edition.py:3979–4018` |
| Navigate forcing | Padded `<aside class="study-glossary-cat" epub:type="footnote">` ≥ 5,600 stripped (`.` filler — K-R13c) | `build_edition.py:3066–3076` · `_pad_kobo_study_footnote` |
| Badge glyphs | Kobo-safe substitutes (`hist→H`, `topic→*`, …) | `build_edition.py:3038–3054` · K-R13b |
| Gates | `dev/verify_study_backmatter.py` · `verify_kr2_build` 4g-bis | round-9 forensics PASS |

**User flow:** Tap coloured badge → Study Notes at `#vnotes-{book}-{ch}-{v}-{cat}` → ↩ or verse tag returns to scripture. Translation: tap verse number → preview popup (unchanged).

---

## 7. `dc:language` chain (popup script fallbacks)

**Mechanism (proven round-6, K-R5-6 regression closed):**

1. Kobo Footnote-preview is a **tag-stripping** extractor — `xml:lang` / per-span `lang` never reach it.
2. OPF `<dc:language>` declarations are the **only** script signal for preview fallback fonts.
3. Kindle E999 requires **single** `dc:language` — must stay **target-gated** to kindle only.

**Pipeline:**

```text
patch_opf (build_edition.py:1719–1755)
  ├─ kindle → single en-US (kindle_post reinforces)
  └─ eink/everywhere/tablet/computer → en-US + hbo + grc + arc + gez + ar

User reading font (Cardo from font-pack) + OPF chain → Hebrew/Greek/Arabic/Geʽez in preview
After sideload: deselect/re-select Cardo (K-R8-5) if scripts tofu in preview only
```

**Regression guard:** `tests/test_opf_clean.py` · `tests/test_scripts.py:539–553` — non-kindle must emit 6 languages.

---

## 8. Open questions for device QA

1. **gen 35:18 re-tap** — single round-5 inversion (3,509 stripped → decline). Decides whether vnote translation asides need Option B.
2. **Round-9 checklist completion** — fill verdict table in `notes/2026-06-15-kobo-round9-device-qa.md` (P0 crash items).
3. **M3 catalog live claim** — artifacts attached (turn 107b) but `EREADERS.md` still says hold; user sign-off needed to mark column **proven**.
4. **Glossary 400 KB cap** — tune `split_study_glossary_document` threshold if paging jank appears (round-9 P2).
5. **Legacy popup study layout** — confirm no edition in catalog still sets `reader_eink_study_layout: popup`.

---

## 9. Recommended implementation plan

| Step | Owner | Blocks |
|---|---|---|
| 1. User runs round-9 P0 tap matrix on `build/kobo-marker-ab/…213413Z.kepub.epub` | User + WIN | M3 live claim in `EREADERS.md` |
| 2. Re-tap gen 35:18 `vn-link` / any remaining `vnote-*` near cap | User | Option B decision |
| 3. Sync `kobo_tap_calibration.py` `BRACKET_LO/HI` → 4,498 / 5,500; update `DEFAULT_TARGETS` | WIN | Accurate future calibration |
| 4. Patch `EREADERS.md` summary row (M3 status, K-R7-4b PASS, K-R9/K-R13 default) | WIN | Format-matrix / website truth parity |
| 5. If round-9 PASS → `build_format_matrix --phase M3` re-fan only if builder delta since last attach | WIN | Catalog SHA256 refresh |
| 6. Optional: promote `vnote` gate 4g WARN → FAIL after gen 35:18 resolved | WIN | Translation popup integrity gate |