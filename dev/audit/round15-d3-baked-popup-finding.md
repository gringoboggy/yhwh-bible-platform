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

---

## ✅ Mac resolution of the two store questions (2026-06-27) — WIN cleared to do the surgical base edit

**Q1 (stray `]`) → KEEP it.** Not a stray artifact — it is the Clementine **psalm-body delimiter**. The source
brackets every psalm body: `[` opens the FIRST body verse, `]` closes the LAST (217 bracketed verses in the
vulgate store; e.g. `(1,1)="[Beatus vir…"`, `(1,6)="…peribit.]"`, `(2,1)="[Quare fremuerunt…"`). **The baked
product KEEPS these brackets** — verified in `epub_working/index_split_032.html`: Ps 2:1 ships
`<p class="vnote-vulgate" lang="la">[Quare fremuerunt…`, Ps 1:6 ships `…peribit.]</p>` (69 bracket chars in the
vulgate popups of that one file). Because the dropped Ps 2:13 / 4:10 each carried the body-CLOSING `]`, the
current baked Ps 2 / Ps 4 are left with a **dangling, unclosed `[`** (baked Ps 2:12 = `…de via justa.` — no
`]`). So restoring the tail WITH its `]` is both consistent with the convention AND repairs the broken bracket
balance. A global bracket-strip would be a separate cosmetic decision, entangled with the unsafe full re-bake
(Q2) — OUT of D3 scope.

**Exact surgical tails** (append to the EXISTING Ps 2:12 / 4:8 popup `<p>` text, one leading space, matching
`apply_remap`'s single-space concat — the store already reads exactly this):
- `vnote-vulgate` Ps 2:12 → append: ` Cum exarserit in brevi ira ejus, beati omnes qui confidunt in eo.]`
- `vnote-vulgate` Ps 4:8  → append: ` quoniam tu, Domine, singulariter in spe constituisti me.]`
- `vnote-douay`   Ps 2:12 → append: ` When his wrath shall be kindled in a short time, blessed are all they that trust in him.` (no bracket — Douay has none; latent: no edition uses the `douay` popup, but include for store↔base parity)
- `vnote-douay`   Ps 4:8  → append: ` For thou, O Lord, singularly hast settled me in hope.`

**Q2 (separator drift) → confirmed OUT of D3 scope.** A real base↔bake divergence (the base lacks the bake's
`vn-sep` preview separators); the surgical 2-verse edit sidesteps it. Logged as a standalone follow-up (the
`generate_verse_popups.py` not-idempotent-vs-base issue) — do NOT gate D3 on it.

**Golden:** Mac confirms WIN's call — the store edit does NOT feed the baked popup, so it does NOT change the
byte-stable cells → **no re-stamp from the store edit** (my premature "G1 re-stamp pending" note is corrected in
the tracker). The golden changes only AFTER WIN's surgical base edit (base → golden, a confined reviewed
re-baseline of Ps 2:12 / 4:8). Mac will then cross-OS-verify the re-stamp (the round-14 G1 pattern).

**WIN is cleared to proceed:** surgical `epub_working/` base edit (the 4 appends above) → `check_nested_anchors
--fix` + `test_nested_anchors` → rebuild catholic-study → grep the epub for `confidunt in eo` → `G1 --regen` →
commit `epub_working/` + golden together. Mac cross-OS-verifies.

### Exact find→replace for WIN (all 4 `<p>` are in `epub_working/index_split_032.html`; post-text == the corrected store verse, verified)

1. **Vulgate Ps 2:12** —
   FROM `<p class="vnote-vulgate" lang="la">Apprehendite disciplinam, nequando irascatur Dominus, et pereatis de via justa.</p>`
   TO   `<p class="vnote-vulgate" lang="la">Apprehendite disciplinam, nequando irascatur Dominus, et pereatis de via justa. Cum exarserit in brevi ira ejus, beati omnes qui confidunt in eo.]</p>`
2. **Vulgate Ps 4:8** —
   FROM `<p class="vnote-vulgate" lang="la">In pace in idipsum dormiam, et requiescam;</p>`
   TO   `<p class="vnote-vulgate" lang="la">In pace in idipsum dormiam, et requiescam; quoniam tu, Domine, singulariter in spe constituisti me.]</p>`
3. **Douay Ps 2:12** (latent — no edition uses the `douay` popup; do it for store↔base parity) —
   FROM `<p class="vnote-douay" lang="en">Embrace discipline, lest at any time the Lord be angry, and you perish from the just way.</p>`
   TO   `<p class="vnote-douay" lang="en">Embrace discipline, lest at any time the Lord be angry, and you perish from the just way. When his wrath shall be kindled in a short time, blessed are all they that trust in him.</p>`
4. **Douay Ps 4:8** —
   FROM `<p class="vnote-douay" lang="en">In peace in the selfsame I will sleep, and I will rest:</p>`
   TO   `<p class="vnote-douay" lang="en">In peace in the selfsame I will sleep, and I will rest: For thou, O Lord, singularly hast settled me in hope.</p>`

Each `FROM` is unique in the file (verified). The `TO` text is byte-identical to the corrected store verse
(`content/translations/{vulgate-clementine,douay-rheims}/psa.py` (2,12)/(4,8)), so the base will match a future
clean re-bake of just these verses.
