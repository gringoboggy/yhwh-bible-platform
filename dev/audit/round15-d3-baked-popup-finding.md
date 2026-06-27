# Round-15 D3 — the store fix does NOT reach the shipped product (popups are BAKED)

**WIN discovery, 2026-06-27, verified against the BUILT catholic-study epub.** Severity: **HIGH** (dropped
scripture would ship unfixed). Cross-lane (Guard #6): Mac's D3 store fix is correct + necessary but
incomplete; completing it is a WIN `epub_working/` + golden task, gated on two questions below.

## What's true

- Mac's D3 fix (`eedc10b8`) added `_VULGATE_PSALM_FIXES` `(2,13)→(2,12)` + `(4,10)→(4,8)` and regenerated
  `content/translations/{vulgate-clementine,douay-rheims}/psa.py` so KJV Ps 2:12 / 4:8 now carry the folded
  Ps 2:13 / 4:10 tail. The `audit_versification_coverage.py` gate is green. **All correct.**
- BUT the **verse-popup text is BAKED into the base HTML** (`epub_working/`), not read from the store at
  build time. `popup_versions._BAKED_NOW` = `{kjv, wlc, lxx-greek, greek-nt, arabic, jps, douay, vulgate}`
  ("versions whose FULL data is ingested AND baked into the shared base"). The build
  (`_apply_popup_languages_and_translation`) only **keeps/strips** the already-baked vulgate paragraph by
  `active_langs` and swaps the **English** slot **iff** an edition sets `translation_id` — and **no edition
  sets `translation_id`** (`grep translation_id content/editions.yaml` = none). So the build NEVER re-reads
  the vulgate/douay store.
- **Proof (built catholic-study everywhere, at HEAD with D3):** the Latin Ps 2:12 popup is present
  (`Apprehendite disciplinam` ×1) but **without the restored tail** (`beati omnes qui confidunt in eo` ×0);
  the tail is NOT in `epub_working/index_split_032.html` either (Mac's commit re-baked nothing).

## Two consequences

1. **The G1 golden is UNCHANGED → no re-stamp from Mac's store edit.** Mac's "G1 re-stamp pending" flag was
   premature: the store doesn't feed the build, so the byte-stable cells are byte-identical (the digest
   mismatch I first saw was the `--version` string confound — `dcterms:isVersionOf` + the `your-edition.xhtml`
   "Build:" line aren't normalized by `_content_digest`). G1 was already verified 9/9 at `2afa6126`
   (post-D4); no build-path change since affects the byte-stable cells. **Re-stamp avoided (saved a 42-min
   regen).**
2. **D3 is INCOMPLETE — the shipped Bible still drops Ps 2:13 / 4:10 from the Latin popup.** To restore it to
   the product, `epub_working/` must be re-baked with the corrected vulgate (+ douay) text for Ps 2:12 / 4:8.
   Then the base changes → the golden legitimately changes → re-stamp then.

## Why the full re-bake is UNSAFE (the blocker)

`scripts/generate_verse_popups.py --books psa` (the designed, "idempotent" re-bake tool) changes **22,168
lines across 4 files** — it is NOT idempotent against the current base. The drift = the bake now injects
**`<span class="vn-sep"> ¶ </span>` / ` ◦ ` preview separators** into every vnote-text + source-label
paragraph, which the current base lacks (the base predates that separator behavior / had them stripped).
Running it would impose that global separator change, corrupting the byte-stable cells. **Reverted.**

## The safe path (surgical), gated on two store questions

- **SURGICAL base edit** of ONLY the Ps 2:12 + 4:8 Latin-vulgate (and baked-douay) `<p>` paragraphs in
  `epub_working/index_split_032.html` (Ps 2) + the Ps 4 split file — append the folded tail, leave every
  other paragraph (and the absent separators) untouched → the base delta is confined to those 2 verses →
  the golden delta is confined → re-stamp is a clean reviewed re-baseline (the round-15 D3 byte note).
- **Then:** base-invariant gates (`check_nested_anchors --fix` + `test_nested_anchors`) → rebuild
  catholic-study → grep the built epub for the restored tail → `G1 --regen` (9 cells) → commit
  `epub_working/` + golden together.

### ⚠ Store questions to resolve FIRST (Mac lane — `content/translations/`)

1. **Stray `]` artifact.** `latVUC_vpl.txt` itself ends Ps 2:13 / 4:10 with a trailing `]`
   (`…beati omnes qui confidunt in eo.]` / `…constituisti me.]`); the English Douay has none. The bake would
   show a stray `]` in the Latin popup. Decide: strip the `]` at the store/ingest (likely correct — it's a
   source formatting artifact, not Latin text), or keep it. WIN bakes whatever the store settles on.
2. **Separator drift (broader).** The base lacking the bake's `vn-sep` preview separators is a real
   base↔bake divergence (own follow-up): is the base correct (separators added only at build/eink) or is
   the bake script ahead of the base? `generate_verse_popups.py` is currently NOT a safe whole-base re-bake
   tool. Out of D3 scope, but it blocks the "just re-run the bake" shortcut.

## Lesson
Every D3-class "fix a translation/versification store" change MUST be verified against the BUILT product
(grep the epub), because the popup for any `_BAKED_NOW` version lives in `epub_working/`, not the store
(memory `feedback_verify_device_fix_against_build`). A store-only fix is a half-fix for baked versions.
