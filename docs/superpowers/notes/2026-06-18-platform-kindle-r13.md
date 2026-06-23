# Platform research — Kindle (Round 13, independent re-audit)

**Status:** Research re-pass complete. Independent angle [1/2] — KFX anchor/page-break
failure mode + phone-QA forensics. No new SHIPPING defect; one new latent/test-integrity
finding (M4b glossary content-dir assumption).
**Date:** 2026-06-18 (round-13 pass) · **Lane:** mac · **Dim:** `platform-kindle`
**Authoritative inputs re-read:** `notes/2026-06-15-kindle-phone-qa-kindle_img.md`,
`notes/2026-06-18-kindle-stk-m4b-device-qa.md`, `notes/2026-06-18-m4b-kindle-fork-design.md`,
`notes/2026-06-18-platform-kindle.md`, `dev/EREADERS.md §Kindle`, `scripts/core/kindle_post.py`,
`scripts/build_kindle.py`, `scripts/build_format_matrix.py`, `tests/test_kindle_m4b.py`.

---

## 1. KFX `#` anchor failure across page-breaks — re-confirmed, root cause stands

Phone QA (2026-06-15) and Kindle-for-Mac QA (2026-06-18) agree: inline `noteref` taps
collapse to the **first aside anchor at the next forced chapter page-break**
(Gen 3:24 → 8:10 → 11:26 teleport class). Amazon's KFX converter mis-resolves intra-document
`#` fragment links when the target sits in a per-piece hidden `notes-section` /
`verse-refs-section` tail that is separated from the marker by a `page-break-before: always`
chapter boundary (often a *next spine file*). This is the historical KindleGen anchor bug
(SO #9186437) surviving in modern KFX.

**Two same-file `noteref` classes exist in scripture after the everywhere build:**
- `verse-notes-badge` (consolidated study badge) → `vnotes-*` aside in the `notes-section` tail.
  M4b Option B **relocates** these to a `kindle_study_glossary_NN.html` backmatter spine and
  retargets the badge `href` cross-file → removes the study half of the teleport.
- `vn-link` (translation) → `vnote-*` aside in the `verse-refs-section` tail.
  M4b **keeps** these in the hidden tail (the proven STK-deliverable shape; any unhide/relocate
  broke STK *load* — see 165347Z / 221232Z FAILs). So the translation `vn-link` tap **still
  teleports** on the M4b artifact. This is the open, documented translation-teleport arc.

**Class sweep:** the raw inline `note-ref note-*` markers (91,555 in the pre-build base) are
fully consolidated into `verse-notes-badge` by the build (0 survive in the built artifact;
verified on a built catalog EPUB). So M4b's badge relocation covers the entire study-marker
class — no missed study emitter.

**Residual KFX risk (open bisect, not new):** M4b trades a same-file teleport for a *cross-file*
badge→glossary `#` jump (~156 glossary pieces on ethiopian). KFX cross-file fragment resolution
is the same suspect mechanism; only device STK re-test settles it. SESSION_STATE row 2 + EREADERS
already gate this ("Kindle STK device bisect" blocks v1.0.0).

## 2. Why minimal `kindle_post` beat the elaborate `--target-reader kindle` variant

Documented and correct: the Previewer-oracle extras (`apply_kindle_toc_rows`,
`apply_kindle_unhide`, 2-popup language cap, `_KINDLE_SAFE_CSS`, source-label compaction,
2 MB split, **dropping `vn-sep`**) were exactly what broke Send-to-Kindle (`FIXED.epub` FAIL).
The proven recipe is purely subtractive over a standard everywhere build: physically strip
`display:none`/`visibility:hidden` (CSS + inline), collapse `<dc:language>` to one `en-US`
(Amazon E999 trigger on multi-value), KEEP `vn-sep` spans (visible language separators) and
`hidden=""` attrs, OCF re-zip mimetype-first/stored. `strip_body_backgrounds` added 2026-06-15
(devotional theme tint painted as a KFX content panel).

## 3. Commercial study-Bible endnote patterns

NIV/ESV Study Bible KFX builds suppress inline note markers and use visible end-of-section
endnotes with navigate-to-anchor (no true popup overlay — KFX has none). M4b Option B mirrors
this (Kobo K-R9 model): scripture shows badges, badges navigate to a backmatter Study Notes
glossary with `↩` back-links.

## 4. M4b fork design → concrete HTML moves (as shipped, Option B)

`apply_kindle_m4b` in `scripts/core/kindle_post.py`:
- Extract `aside.verse-notes#vnotes-*` study asides out of every `index_split_*` scripture file.
- Emit a `study-notes-index` backmatter doc (reusing the Kobo splitter
  `split_study_glossary_document`), one piece per book, split at `target` bytes; insert spine
  itemrefs before `backsources`.
- Retarget each `a.verse-notes-badge href="#vnotes-…"` → `kindle_study_glossary_NN.html#vnotes-…`.
- Per-entry `↩` back-link to the verse's `v-…` scripture anchor (cross-file href via the
  harvested `v_anchor_files` map); same-doc `#v-…` xrefs inside relocated asides retargeted to
  their scripture file.
- Translation `vnote-*` left in the hidden tail (unchanged). Title-page + ToC-row pagination CSS
  appended (`apply_kindle_m4b_css`). NAV + NCX `Study Notes` entry added, playOrder renumbered.
- Gates: `verify_kindle_m4b` (m4b-1..6) + `verify_kindle_safe` + epubcheck; `tests/test_kindle_m4b.py` 13/13 green.

**Mirror-Kobo?** Yes — Option B is the Kobo K-R9 backmatter model. Difference: Kobo keeps a
device-honored popup for translation; Kindle cannot (KFX no overlay), so translation degrades
to a (still-teleporting) hidden-tail jump.

## 5. What STK 6/6 (2026-06-14) did NOT gate

`noteref`→intended-aside link target (vs page-break anchor); `vn-link` tap behavior; inline
marker visual density; ToC horizontal chapter-row layout; first-open KFX download/index latency;
location-vs-page user expectation. STK 6/6 gated **delivery + epubcheck shape only**, never
on-device link UX. (All documented; re-confirmed.)

## 6. Catalog vs M4b — shipping reality

`build_format_matrix._apply_kindle_post` runs `make_kindle_safe` **only** (NOT `make_kindle_m4b`);
M4b is reachable only via `build_kindle.py --m4b` (manual staging). So the **shipped/catalog**
Kindle column is the proven `kindle_safe` shape with inline badges + the documented teleport;
M4b is staged-only pending device re-pass. Consistent with the v1.0.0 bisect block.

## 7. NEW finding — M4b glossary content-dir assumption + blind test (latent/robustness)

`_apply_kindle_m4b_members` inserts the glossary file under a **bare** name
(`kindle_study_glossary_NN.html`) and writes **bare** hrefs into the OPF manifest, scripture
badges, nav, and ncx — implicitly assuming all content lives at the **zip root**. The real
catalog editions DO use a flat zip-root layout (verified: `content.opf` + `index_split_*` at
root), so this works today. But `tests/test_kindle_m4b.py` builds its fixture under `OEBPS/`
(`z.writestr("OEBPS/content.opf", …)` etc.). On that fixture the glossary lands at zip-root
while the OPF/badges resolve hrefs relative to `OEBPS/`, so the manifest item + every retargeted
badge point to a non-existent path — yet the test still **passes** because every assertion is a
substring check (`'href="kindle_study_glossary' in chap`), never verifying the glossary's actual
zip path matches where its hrefs resolve. The test therefore gives false confidence and would not
catch a real cross-directory breakage; and if the EPUB layout ever moves to `OEBPS/`, every M4b
badge + the glossary manifest entry silently become dead links / epubcheck RSC-001. Fix: derive
the OPF/container content prefix and prefix the glossary names + back/badge hrefs with it
(`Path(opf_name).parent`), and add a fixture/test that asserts the glossary zip path equals the
prefix the hrefs resolve to.
