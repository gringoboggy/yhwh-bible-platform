# Platform research — Kindle (Round 9)

**Status:** Research complete — M4b fork design input.
**Date:** 2026-06-18 · **Lane:** mac · **Dim:** `platform-kindle`

---

## 1. Our target UX (non-negotiables)

From `dev/EREADERS.md` §Kindle + `docs/superpowers/notes/2026-06-15-kindle-phone-qa-kindle_img.md`:

- **Delivery:** Send-to-Kindle → Amazon KFX conversion (no sideload).
- **Proven recipe:** everywhere build + `kindle_post.make_kindle_safe` (NOT the retired `--target-reader kindle` in-pipeline variant).
- **User goal (M4b):** Kobo-like split — **translation popups in scripture**, **study notes elsewhere** (suppress inline ◈/numbered markers).
- **Kindle has no true popup footnotes** — visible endnotes / navigate-to-anchor is the ceiling.
- **Gate:** `verify_kindle_safe` + epubcheck 0/0/0/0 + **phone STK spot-check** (link targets, not just delivery).

---

## 2. Official format support

| Topic | Vendor says | Our build uses |
|---|---|---|
| EPUB upload | Send-to-Kindle accepts EPUB; converts to KFX internally | `.epub` per FORMAT_MATRIX `kindle` row |
| Popup footnotes | KF8/KFX: footnotes typically endnotes or inline; pop-up model unreliable | Inline `noteref` + `hidden=""` asides — **phone QA FAIL on anchor resolution** |
| Internal `#` anchors | Historical KindleGen issues with anchors across page breaks ([Stack Overflow](https://stackoverflow.com/questions/9186437/problems-with-internal-links-anchors-in-mobi-output-from-kindlegen)) | Chapter `page-break-before` + per-piece `notes-section` at chapter tail → taps collapse to 3:24, 8:10, 11:26… |
| Embedded fonts | KFX re-flows; partial honoring | Full apparatus fonts in source EPUB; stripped to single `dc:language` in kindle_post |
| `display:none` | Amazon ingestion sensitive — E999 on multi-value `dc:language` | **Physically stripped** by kindle_post (proven june10) |
| Collapsible ToC | No `<details>` support | `toc_expandable` gated off in TARGET_CAPS.kindle |

**Sources:**

- [Amazon KDP HTML/CSS guidelines](https://kdp.amazon.com/en_US/help/topic/GH4DRT75GWWAGBTU)
- Internal: `scripts/core/kindle_post.py`, `2026-06-15-kindle-phone-qa-kindle_img.md`, STK 6/6 notes (2026-06-14)

---

## 3. How others achieved similar goals

| Technique | Who / where | Applies to us? |
|---|---|---|
| Visible endnotes / footnote section at chapter end | Standard Kindle study Bibles (NIV Study, ESV Study) | **Yes — M4b direction** |
| Suppress inline note markers; link from verse to end section | Common KFX-safe pattern | **Yes — primary M4b option** |
| Inline superscript markers + popup asides | Our everywhere build | **Fails on phone KFX** (proven) |
| Study glossary backmatter with jump links | Kobo K-R9c | **Adapt for Kindle** — noteref jumps may work within same file |
| Minimal post-process over standard EPUB | Our june10recipe vs FIXED.epub failure | **Shipped** — `kindle_post` productized |

---

## 4. Gap vs our pipeline

| Gap | `build_edition` / `kindle_post` / `TARGET_CAPS` | Severity |
|---|---|---|
| Inline markers still visible in scripture | everywhere build keeps badge markers; kindle_post does not strip them | **high (UX)** — user "too busy" |
| `noteref` targets in `notes-section` after page-break | Chapter-last-verse + `hidden=""` aside block at piece boundary | **high (UX)** — teleport class |
| M4b fork not implemented | No `apply_kindle_m4b_*`; only `make_kindle_safe` + `_flatten_toc_pills` | **high (feature gap)** |
| STK gate did not test link targets | `verify_kindle_safe` checks hides + dc:language only | medium |
| Devotional theme body background | `strip_body_backgrounds` shipped in kindle_post (2026-06-15) | none (fixed) |
| `vn-sep` spans | Kept intentionally — visible language separators in footnote text | none (correct) |

---

## 5. Options ranked

### Option A (recommended) — M4b marker suppress + chapter-tail study block

- **Change:** Extend `kindle_post` (or pre-zip `target_reader=kindle` pass) to: (1) replace inline study badges with plain verse text; (2) move `vnotes-*` asides to end-of-chapter "Study Notes" section with stable same-file anchors; (3) keep `vn-link` translation markers inline with same-file `vnote-*` targets (not batched in chapter-tail `notes-section`).
- **Files:** `scripts/core/kindle_post.py`, possibly `scripts/build_edition.py` (`_disable_vn_links` inverse for study-only), new `tests/test_kindle_m4b.py`.
- **Device proof:** STK phone — Gen 1/3 badge taps, translation taps, no 3:24/8:10 teleport.
- **Risk:** Medium — must not break `verify_kindle_safe` or Send-to-Kindle delivery; byte-stability on 9 KJV editions N/A (kindle is post-process column).

### Option B — Full study glossary backmatter (Kobo K-R9 mirror)

- **Change:** Suppress all inline study markers; inject Kindle-safe study glossary at back; per-category jump links.
- **Files:** Reuse `inject_eink_study_backmatter` logic with kindle-specific CSS (no `display:none` reliance).
- **Device proof:** Phone QA on glossary jumps + ↩ return links.
- **Risk:** Higher — larger structural change; KFX pagination of huge backmatter unknown.

### Option C (decline) — Keep inline markers; hope for KFX fix

- **Decline:** Phone QA disproved; STK delivery pass is insufficient; user explicitly requested endnotes model.

---

## 6. Open questions for device QA

1. Do same-file `vn-link` → `vnote-*` jumps work on phone KFX when aside is NOT in chapter-tail `notes-section`?
2. End-of-chapter study block vs end-of-book glossary — which survives KFX pagination better?
3. Does `_flatten_toc_pills` (shipped) fix cramped chapter-number rows (IMG_0415)?
4. Scholarly vs Ethiopian first-open latency — KFX indexer vs link density (documented, not a build bug).

---

## 7. Recommended implementation plan

| Step | Owner | Blocks |
|---|---|---|
| Design spec: M4b HTML moves (suppress markers, chapter-tail study, keep vn-link) | Mac | This brief |
| Implement in `kindle_post.py` + `verify_kindle_m4b` gate | Mac | Spec |
| Build 6-variant STK matrix + phone QA checklist (Gen 1/3/11) | Mac | Implementation |
| User Send-to-Kindle phone test | User | STK pack |
| Regen 45 catalog kindle cells + SHA256SUMS | WIN | Device PASS |
| Retire pre-`strip_body_backgrounds` catalog artifacts if any remain | WIN | Rebuild |

---

## What STK 6/6 did NOT gate

- `noteref` → intended aside target (vs chapter page-break anchor)
- Translation `vn-link` tap behavior
- Inline marker density / visual clutter
- ToC horizontal chapter-row layout (only `_flatten_toc_pills` added later)
- First-open KFX download/index time
- Location vs page-number user expectation (Kindle uses locations, not EPUB pages)