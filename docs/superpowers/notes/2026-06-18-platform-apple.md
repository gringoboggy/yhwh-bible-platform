# Platform research — Apple Books (Round 9)

**Status:** Research complete — M2 prep input.
**Date:** 2026-06-18 · **Lane:** mac · **Dim:** `platform-apple`

---

## 1. Our target UX (non-negotiables)

From `dev/EREADERS.md` §Apple + `docs/superpowers/notes/2026-06-15-apple-m2-layout-directive.md`:

- **Artifact:** plain `.epub` (no kepubify, no `kindle_post`).
- **`target_reader`:** `tablet` (FORMAT_MATRIX `apple` row).
- **Per verse, two tap targets only:**
  - Verse **start:** `vn-link` → translation popup (`vnote-{code}-{ch}-{v}`).
  - Verse **end:** **one** study badge with count → merged `verse-notes` popup (`vnotes-*-s1`).
- **Polish inside Apple's native footnote sheet only** — typography, RTL, cascade cards.
- **Do NOT port:** Kobo K-R9 study glossary backmatter, per-category eink badges, Kindle M4b marker suppress.
- **Gate:** user Apple device re-test; epubcheck 0/0/0/0; M2 backgrounds-off structure pass stays green.

---

## 2. Official format support

| Topic | Vendor says | Our build uses |
|---|---|---|
| EPUB version | EPUB 3.3 supported; backwards compatible with EPUB 3 ([Apple Books Asset Guide 5.3.1](https://help.apple.com/itc/booksassetguide/en.lproj/static.html)) | EPUB 3; epubcheck 0/0/0/0 on shipped v0.1.0 |
| Popup footnotes (`noteref`/`aside`) | `epub:type="noteref"` anchor + `epub:type="footnote"` aside; aside text hidden in body, shown in popup ([Asset Guide §Pop-up Footnotes](https://help.apple.com/itc/booksassetguide/en.lproj/static.html)) | `vn-link` noteref + `aside.verse-notes` / `vnote-*` — **device-proven M2-1 PASS** |
| Embedded fonts | Supported; embed when system fonts insufficient ([Asset Guide §Embedding Fonts](https://help.apple.com/itc/booksassetguide/en.lproj/static.html)) | `style_config.EMBED_FONT_PATHS` + `patch_opf_fonts` — Cardo, Noto Ethiopic, etc. |
| Page-break CSS | Flowing books reflow; spine order drives pagination | `apply_file_split` title-page singleton pieces (works on all targets; beneficial on Apple) |
| Collapsible ToC (`<details>`) | `nav epub:type="toc"` required; nested `<ol>` supported | `reader_toc_expandable` opt-in via wizard `TARGET_CAPS.tablet.toc_expandable=true` — **live-verified round-6** |
| RTL / multi-script | `dir` on package; `writing-mode` on body/html; footnote RTL via wrapped `<p style="direction:rtl">` | Popup `lang` spans + embedded fonts; no tablet-specific fork |

**Sources (cite URLs):**

- [Apple Books Asset Guide 5.3.1](https://help.apple.com/itc/booksassetguide/en.lproj/static.html) — pop-up footnotes, fonts, navigation, EPUB 3.3
- [W3C EPUB 3.3](https://www.w3.org/TR/epub-33/) — structural semantics
- Internal: `docs/superpowers/notes/2026-06-10-target-caps-research.md`, `2026-06-09-M2-device-qa-results.md`

---

## 3. How others achieved similar goals

| Technique | Who / where | Applies to us? |
|---|---|---|
| Verse-end single badge + count → one merged study popup | Our M2 device QA (◈18 Gen 1:1) — pre-Kobo fork design | **Yes — keep as north star** |
| `noteref` + hidden `aside` footnote pattern | Apple Asset Guide canonical example | **Yes — already our emitter** |
| Per-category inline markers | Many print study Bibles | **No on Apple** — Kobo-only compromise |
| Study notes in backmatter glossary | Kobo K-R9c model | **No on Apple** — breaks M2 inline-badge UX |

---

## 4. Gap vs our pipeline

| Gap | `build_edition` / post-process / `TARGET_CAPS` | Severity |
|---|---|---|
| Popup typography polish (cascade legibility inside sheet) | `apply_badge_markers` + popup HTML generators — no tablet-specific CSS pass yet | low (device QA cosmetic) |
| Title-page centering residual | Known open Kobo/Apple device-QA item; CSS already `text-align:center` — needs render-then-diagnose | low (deferred) |
| Kobo `.vn-sep` spans in translation popups | Emitted on all targets; harmless on Apple (hidden in aside until popup) | none |
| eink study backmatter / per-category badges | Correctly gated off when `target_reader != eink` (`resolve_reader_eink_study_layout` L2216) | none — **no bleed** |
| `TARGET_CAPS.tablet.max_popup_languages` | `null` (no cap) — Apple honors full apparatus | none |

---

## 5. Options ranked

### Option A (recommended)

- **Change:** Ship M2 column as **status quo** `target_reader=tablet` everywhere build + optional FORMAT_MATRIX `apple` row; polish popup CSS only (cascade spines, RTL `lang` spans, font sizes inside `aside`).
- **Files:** `scripts/build_edition.py` (badge emitters only if markup tweak needed), `epub_working/stylesheet.css` §4.1, `scripts/templates/wizard.py` TARGET_CAPS (already correct).
- **Device proof:** User Apple re-test on ethiopian-tewahedo navy `.epub`; Gen 1:1 badge tap + translation tap; backgrounds-off pass.
- **Risk:** Low — additive CSS only; 9 KJV byte-stable editions unaffected (tablet is separate matrix column).

### Option B

- **Change:** Add `reader_tablet_popup_compact` flag to trim cascade HTML density inside popups (shorter bylines) without changing marker geometry.
- **Files:** `scripts/build_edition.py` popup merge path, `scripts/core/popup_versions.py`.
- **Device proof:** A/B screenshot on iPhone Apple Books.
- **Risk:** Medium — could drop visible attribution if over-trimmed.

### Option C (decline / defer)

- **Change:** Port Kobo per-category badges or study glossary backmatter to tablet.
- **Decline:** Violates M2 layout directive; Apple popups work with inline badges; Kobo compromises are engine-specific.

---

## 6. Open questions for device QA

1. After v0.1.0 popup cascade ship — do long `verse-notes` popups scroll smoothly on iPhone vs iPad (sheet height)?
2. Geʽez/Arabic inside translation popups — does Apple honor embedded Noto vs system fallback without font-pack sideload?
3. Collapsible ToC on 83-book edition — any scroll performance regression on phone?
4. Title-page book name alignment — which element is off-center (needs screenshot pinpoint, not blind CSS)?

---

## 7. Recommended implementation plan

| Step | Owner | Blocks |
|---|---|---|
| Build ethiopian-tewahedo `--target-reader tablet` from FORMAT_MATRIX | Mac | None |
| epubcheck 0/0/0/0 + verify_kr2 gates on tablet artifact | Mac | Build |
| Optional: tablet-only popup CSS pass (typography) | Mac | User GO on screenshots |
| User Apple device QA (M2 checklist) | User | Artifact on Desktop |
| Attach to v0.1.x release / website apple column if distinct from everywhere | WIN | Device PASS |