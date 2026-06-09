# Kobo device-QA round 2 — 2026-06-09 (user, 26 screenshots) — FINDINGS

Artifact tested: `YHWH-Ethiopian-Bible-koboQA.kepub.epub` (32.9 MB — the turn-57
rebuild WITH K①–K③, confirmed via kobo24 Details). Source images:
`C:\Users\bogda\OneDrive\Desktop\kobo_img\kobo1–26.jpg` (1–8 new angle-shots,
9–26 broader sweep). Catalog = K-R2-#; fixes are NEXT-SESSION work.

## K-R2-1 (HIGH) — title-page bleed ROOT CAUSE REVISED: kepub ignores our page-breaks at the boundary
kobo22 is decisive: ONE Kobo page shows (top→bottom) the in-content ToC's
book-pill rows (pills 56–65) → the framed Genesis title (art + BOOK I + title,
all *contained and centered* — the K③ art em-caps DID work) → chapter "1" →
Gen 1:1 text. `.book-title-page` carries `page-break-before/after: always` +
`break-before/after: page`, so **Kobo's kepub renderer is not honoring those
breaks at this position** (known kepub flakiness for breaks on nested elements
inside the `#book-inner` wrapper). The art-height theory is CLOSED; the break
behavior is the bug.
**Candidate fixes (investigate in order):** (a) make `apply_file_split` cut AT
book boundaries so every book-title starts a fresh spine file (a new file is a
guaranteed fresh page on every renderer — the only bulletproof form); (b)
research kepub-specific break handling (does Kobo only honor breaks on direct
children of `#book-inner`? kepubify diverts?); (c) Mac research item.

## K-R2-2 (HIGH) — badge tap sometimes lands at "start of ToC" instead of popup (Gen 1:1 ◈15 + many others)
User: tapping the note badge often navigates back to the ToC start rather than
opening the Footnote preview. Other badges DO pop (kobo2/5/6/8/12 all fire).
**Hypotheses to repro against the kepub next session:** (i) Kobo falls back to
NAVIGATE when it dislikes the aside (size? position?) — and the merged asides
for early Genesis sit in the same split piece as the front-matter/ToC tail, so
the jump LOOKS like "start of ToC" (consistent with kobo22's pills sharing the
piece); (ii) coarse-tap collision with something whose href targets the ToC;
(iii) piece-relative anchor handling. We have the kepub — inspect where
`vnotes-gen-1-1` physically sits in its piece + what the piece starts with.
NOTE: every noteref href resolves in-file (verified at build) — this is a
renderer-behavior bug, not a broken link.

## K-R2-3 (MED) — Footnote-preview dialog renders with KOBO'S SYSTEM FONT → original-language tofu is NOT an embed problem
kobo1/4/10/11: in the preview dialog, Hebrew = tofu boxes, polytonic Greek =
half-missing diacritic forms, Arabic (Van Dyck) = full tofu; Latin fine.
kobo2/5/6/8/12: English study notes render perfectly. The dialog is a Kobo
SYSTEM overlay — it does NOT use the book's embedded fonts (those style body
text only, and only under "Publisher default" font). So the K② ttf swap cannot
fix the *preview*; same root for the ◈ badge glyph showing as a box in BODY
text when a user-selected reading font lacks U+25C8 (kobo1/7/21/22).
**Mitigations:**
1. **Kobo font-pack add-on (user-approved direction)** — the Kobo exposes a
   root `fonts/` folder for sideloaded ttf/otf. Ship a release artifact
   "kobo-font-pack" (all OFL, already licensed in-repo: Cardo ×3 [Hebrew+Greek],
   Noto Serif Ethiopic; ADD Noto Naskh Arabic — needs LICENSES entry) + a Guide
   step. **Staged on the device this session for the next eyeball** (G:\fonts\
   — user selects e.g. Cardo as reading font; TEST whether the preview dialog
   follows the reading font).
2. Verify "See more" renders the aside in-book WITH embedded fonts (likely yes
   — then the preview is a degraded-but-documented path).
3. Consider a more universally-covered badge glyph (configurable per
   presentation doctrine) if the font pack doesn't carry U+25C8 everywhere.

## K-R2-4 (MED) — chapter numerals: not centered + orphaned at page bottom
kobo7/9/13: the bare chapter numeral renders LEFT-aligned mid-flow and can land
orphaned at the very bottom of a page (the user's "weird formatting gaps like
chapter 3" — kobo9/13/21 show "3" + its stray chapter-badge alone at page end).
Check `.ch-heading` effective text-align on Kobo (the `body p {text-align:left}`
Apple-compat rule may win where the heading lacks an explicit center at class
specificity) + add keep-with-next/break-inside handling so a numeral never
strands. Also note the stray chapter-level ◈ badge renders as a lone box under
the numeral (ties into K-R2-3 glyph coverage).

## K-R2-5 (MED) — Kobo prompts to add ~4 extra language INPUTS (mentions Arabic)
The reader detects the embedded multi-script content (Hebrew/Greek/Arabic/Ge'ez
in the translation popups) and offers language-pack/keyboard downloads. Likely
benign, but audit our `xml:lang`/`dc:language` markup next session — proper
per-span lang tags may stop the mis-detection (it currently names Arabic, which
suggests it's reading content, not metadata).

## K-R2-6 (LOW) — TWO Colophons (front + closing) + the closing one leaks internals
kobo14/20: native ToC lists "Colophon" near the start AND at the end. kobo26:
the CLOSING colophon still shows `Generated v28a-t` + the URN — the 2030e7e0
identity sweep cleaned the FRONT colophon only; internal build strings are
reader-visible at the back. User question: do we need both? **Recommendation
(configurable, per presentation doctrine):** ONE colophon. Either rename the
front page "Copyright" and keep a minimal traditional closing colophon, or fold
the closing page away entirely; strip `Generated vXX`/URN from every reader
surface either way (identity lives on Your Edition).

## K-R2-7 (LOW) — alternate ", or …" book names survive in the NATIVE ToC
kobo15/16/17: "Ecclesiastes or, The Preacher", "The Song of Songs, or Song of
Solomon", "…Sirach, or Ecclesiasticus", "4 Baruch, or Paralipomena of Jeremiah"
still appear in nav.xhtml/toc.ncx — the v0.0.3 (e) alt-name sweep covered
body/base HTML but not the nav-title source. Sweep that source.

## K-R2-8 (MED) — stale "88 scriptures" in the EPUB's own metadata
kobo23: the library Synopsis (OPF `dc:description`) reads "88 scriptures…".
The 83-count rule swept site/meta/social/repo but NOT the EPUB metadata
description. Fix the description source + add it to the count-sweep checklist
(`feedback_deploy_means_build_and_deploy`).

## K-R2-9 — what's GOOD (keep)
Reference Tables render beautifully (kobo25 — user praise). Study-note popups
fire reliably with the full cascade content reading well (kobo2/5/6/8/12/13).
Native ToC is clean book-level (kobo14–20). Load is smooth; the K③ art caps
contained the framed title art; cover + library card look right (kobo23/24).

## Device staging done this session
`G:\fonts\` ← Cardo-Regular/Italic/Bold.ttf + NotoSerifEthiopic-Regular.ttf
(the in-repo OFL binaries) for the K-R2-3 experiment: user picks "Cardo" (or
"Noto Serif Ethiopic") in the reader's font menu, re-opens a translation popup,
and reports whether the preview dialog follows the reading font.

## Next-session WIN sequence (proposed)
1. K-R2-2 repro (kepub inspection: aside positions, piece starts) → fix.
2. K-R2-1 splitter-at-book-boundaries investigation (the bulletproof break).
3. K-R2-4 chapter-numeral centering + keep-with-next.
4. K-R2-8 description + K-R2-7 nav alt-names + K-R2-6 single-colophon
   (option-gated) — one metadata/front-back-matter sweep.
5. Rebuild + kepub + reload G:\ → user round 3.
Mac (parallel): K-R2-1 kepub break-behavior research · K-R2-3 font-pack
licensing prep (Noto Naskh Arabic LICENSES/ATTRIBUTIONS) + release-artifact
shape · review this catalog adversarially.
