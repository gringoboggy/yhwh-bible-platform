# Kobo deep-audit program — scripture formatting · study-note redundancy · popup formatting (2026-06-24)

**User directive (2026-06-24):** after the page-break fix landed on-device, *"plan the audit, run
the audit and its fixing autonomously, with Mac helping every step of the way, and neither of you
stops till the fixing is done."* This is the user-triggered autonomous remediation program — same
shape as the round-10/11 full-audit program: plan → split across both boxes → build deterministic
auditors → run → fix everything → loop until green + device-clean.

## Origin — device-QA of the flagship eink kepub (color Kobo, Cardo reading font), 2026-06-24

The newest flagship `ethiopian-tewahedo` eink kepub (page-break Parts 1+2 + Hebrew font fix) was
built fresh from HEAD, verified, and loaded to the Kobo. The user's eyeball:

- **✅ NO PAGE BREAKS, Genesis → Revelation** — the weeks-long page-break defect is confirmed
  RESOLVED on-device (Parts 1+2+2b). Page-to-page is smooth; a new chapter sometimes takes a few
  seconds to load (acceptable — NOT a defect).

## Findings (verbatim) + root cause (proven against the built epub)

1. **Mid-verse line breaks** — random line breaks mid-verse: `gen 17:23` (after 1st sentence),
   `gen 19:1` (after 2nd sentence), `gen 30:1` (after 1st), `gen 48:1` (after 1st); **continues
   through Exodus** (systemic, not isolated).
   **ROOT CAUSE (proven):** a single verse is split across multiple `<p class="verse-p">` blocks.
   E.g. `gen 19:1`'s "Lot saw them, and rose up to meet them…" is a SECOND `<p>` still tagged
   `vbadge-gen-19-1-comm` (same verse). On Kobo every `<p>` is block-level → a line break appears
   mid-verse. Source = the base scripture HTML (`epub_working/`), which preserves the English
   text's intra-verse paragraphing. **Byte-stability-critical** (shared base → all editions).

2. **"Weird symbol" after a verse marker** = the **pilcrow `¶` (U+00B6)**.
   `gen 46:13`: `…<span class="vn">13</span></a> ¶ And the sons of Issachar…`
   `gen 49:14`: `…<span class="vn">14</span></a> ¶ Issachar [is] a strong ass…`
   **DEEPER (proven):** those verses are **KJV text** (¶ paragraph marks + `[bracketed]` supplied
   words) while the surrounding verses are **WEB/modern** ("When he finished talking with him, God
   went up from Abraham"). → a **mixed / inconsistent base translation** in Genesis. The ¶ +
   brackets are KJV-isms that don't belong if the base is WEB. This is a data-consistency defect,
   not just a glyph; the auditor must find EVERY mixed-translation verse, not only these two.

3. **Empty spaces after most verse badges** (~3 character spaces before the next verse) = the
   `<span class="badge-trail" aria-hidden="true"> ​ ​ </span>` (zero-width U+200B + regular spaces)
   PLUS leading spaces in the verse text after the badge (`</a>    When…`). User: "may just be
   something we are stuck with since we justify the chapter bodies — may be fine." → LOW; quantify
   and decide (keep / tighten), surface to `dev/HUMAN_DECISIONS.md` if it's a presentation choice.

4. **Prayer of Azariah** — the native-reader ToC title reverted to the long form
   ("…and the Song of the Three…"), which is too long → truncates to `[+]` in the Kobo ToC.
   Shorten to **"Prayer of Azariah"** (as it was before). It REVERTED — find why + re-pin so it
   can't revert again. → discrete fix.

5. **Study notes still redundant** — naming conventions / category symbol / cross-references
   repeated; "lots of repetitions." Want a **cascade feel** with no repeated information. → WS2.

6. **Kobo popups are run-on sentences** — long-standing since the first Kobo trial. The popup
   bodies read as one undifferentiated run-on. → WS3.

## Workstreams

### WS1 — Scripture-body formatting auditor + fix  (WIN owns; byte-stability-critical)
- **Auditor `dev/audit_verse_formatting.py`** (mirror the spine-break auditor's rigor — point it at
  any built `.epub`/`.kepub`, reconstruct verse→HTML, classify per book/chapter/verse):
  - **multi-`<p>` verses** — a verse whose text spans >1 `<p class="verse-p">` before the next verse
    anchor → the mid-verse line breaks. (ERROR)
  - **stray `¶` pilcrows** in verse text. (ERROR)
  - **KJV-ism / mixed-translation markers** — `[bracketed]` supplied words and/or `¶` in a verse
    whose neighbors are modern → flags every inconsistent verse. (ERROR)
  - **badge-trail / leading-space** anomalies — quantify (WARN; presentation decision).
  - Edition/canon/platform-agnostic; exit 1 on ERROR. This is the regression gate for the fix.
- **Fix** at the real emitter / base HTML: collapse multi-paragraph verses to one flowing `<p>`,
  normalize the mixed translation (decide the canonical English base, strip stray KJV-isms — NO
  guessing on scripture; use the real source). Re-baseline the goldens deliberately (the base
  change shifts bytes on every edition — prove only the intended change moved).

### WS2 — Study-note redundancy / contradiction / code-break deep audit + cascade rework  (WIN + Mac, Workflow)
- Deep **semantic** audit of note bodies (every kind × category) for: repeated naming/byline/symbol/
  cross-reference, contradictions, broken markup. Build/extend a deterministic finder where possible
  (`dev/audit_note_redundancy.py`) AND a multi-agent semantic pass (adversarially verified).
- Design the **cascade** presentation (one heading per category, no repeated info) → implement at
  the cascade emitter (`_emit_cascade_sections`); folds in device-QA C/F (drop redundant per-note
  `note-sym`; supersedes B-1c). Byte-impact gated to eink where possible.

### WS3 — Kobo popup formatting research + fix  (Mac research, WIN implement, device-verify)
- Deep research (web + code): why Kobo `epub:type="footnote"` popups render as run-on; the
  reliable technique to structure them (block elements vs `<br>`, kepub popup constraints, what
  Kobo's popup renderer honors). Prescription → `dev/audit/kobo-popup-formatting-research.md` →
  implement (eink-gated) → device A/B.

### Discrete — Prayer of Azariah ToC title  (WIN, quick win, do first)
- Re-shorten the nav/NCX title to "Prayer of Azariah"; root-cause the revert; pin it (lint/test).

## Lane split (file-disjoint — parallel mode, truth_owner = windows)
- **WIN:** WS1 (the auditor lives in `dev/` but the FIX is `scripts/build_edition.py` + base
  `epub_working/` + `content/` → WIN), the discrete fixes, all device builds + Kobo loads (the Kobo
  is on the WIN box), WS2 implementation.
- **Mac:** WS3 research (`dev/audit/`), independent WS2 semantic-audit runs + findings
  (`dev/audit/`), cross-OS verify of every WIN fix + new auditor, structural re-confirms.

## Protocol — neither lane stops until fixed
- TDD on every auditor + fix; **byte-stability proof** on any base-HTML/build-path touch (the base
  change is a deliberate re-baseline — prove only the intended bytes moved; there is NO KJV golden
  hash, so manual regen + `git diff` across editions is mandatory).
- Commit-per-fix; push at coherent stops; full `save-all.ps1` at milestones; both lanes sync via
  `dev/LANE_HANDOFF.md` + the lane-ping radar (auto pull --rebase on BEHIND).
- **Loop until:** WS1 auditor green on every edition × platform · WS2 cascade has zero redundancy
  finding · WS3 popups structured + device-verified · discrete fixes pinned · a clean device eyeball.
- User-only calls (e.g. the badge-trail keep/tighten decision, any device A/B) → `dev/HUMAN_DECISIONS.md`.

## WS1 — first auditor run (flagship eink, 2026-06-24) — SUPERSEDED, see re-architecture below

First cut reported **472 breaks / 18 ¶ / 109 brackets** keyed on "verse-p paragraph with no
`v-` anchor". Investigation (2026-06-24, WIN) proved that heuristic measured the **WRONG thing**:
the 472 were 1 Clement strategy-B chapters (plain `<span class="vn">`, no anchor) + psalm
superscriptions + Song speaker rubrics + apocrypha section headings — none of which are mid-verse
breaks — while it **MISSED the real gen/exo narrative breaks** (whose continuation paragraph still
carries the *next* verse's anchor). ¶/bracket were mis-attributed to the paragraph's first verse
(gen 46:13 read as gen 46:1).

## WS1 — auditor RE-ARCHITECTED + true scope (2026-06-24, WIN)

`dev/audit_verse_formatting.py` rewritten (TDD, **14/14 pins**, `tests/test_audit_verse_formatting.py`).
Correct signal: a **mid-verse break = ALPHABETIC PROSE before a paragraph's first verse marker**
(that prose is the previous verse's tail; the `</p><p>` boundary fell inside the verse). Note-marker
digits / single-glyph badges before the marker are NOT prose, so chapter-starts don't false-flag.
¶/bracket attributed to the nearest PRECEDING verse marker. Verified the build PRESERVES paragraph
structure (base gen19 = kepub gen19 = 2 paragraphs), so **the defect lives in — and is fixed at —
the base HTML `epub_working/`**, not the build.

**True scope on the built flagship eink kepub (and base HTML, which agree):**
- **62 regular-canon mid-verse breaks (ERROR)** — the real device defect. By book: psa 13 · gen 4 ·
  job 4 · sng 4 · num 3 · 1ch 3 · pro 3 · isa 3 · jer 3 · mat 2 · jhn 2 · 2ch 2 · + 1 each
  (nah, mrk, act, rom, 1co, 1th, jdg, 2ki, tob, est, ecc, lam, bar, eze, oba) + 1 unknown. The four
  user-reported cases (gen 17:23, 19:1, 30:1, 48:1) are all present. **(psa/sng = poetry — decide in
  the fix phase whether their line-splits are a defect or intentional verse-per-line.)**
- **18 stray pilcrows ¶ (ERROR)** — now correctly located: gen 46:13 + 49:14 (the user's two), plus
  lev 3:12 · exo 28:31/40:28 · num 3:14/19:11 · gen 8:15 · jer ×2 · 2ch · ecc · pro · isa · dan · sng ×3.
- **11 irregular-apocrypha breaks (WARN)** (1en 8 · sir 3) + **37 strategy-B chapter splits (WARN)** =
  known-residual / different-layout, not the regular-canon gate.
- **143 mixed-translation `[bracket]` occurrences (WARN)** — but man (32) + 1en (31) are the **Charles
  translation's legitimate editorial brackets**, NOT KJV-isms. The real KJV-text-in-WEB-base class =
  the brackets co-located with the 18 pilcrows (gen/exo/num/lev/jer/dan/pro/isa/ecc/2ch/mat). That
  co-located ¶+bracket set IS the mixed-translation defect (WS1 task #4).
- **160 superscriptions / rubrics / headings (INFO)** — psalm titles, Song speaker rubrics, section
  headings: correctly NOT counted as breaks. 36,329 deep-linked verses + 3,870 plain-vn.

**Fix approach (WS1 fix phase, base HTML — byte-stability-critical, all editions, deliberate re-baseline):**
mid-verse breaks → move a verse's spilled tail-prose into its own verse paragraph so no verse spans a
`<p>` boundary (preserves between-verse paragraphing); mixed translation → normalize the KJV-text verses
to the WEB base from the real source (NO scripture guessing), stripping ¶ + `[supplied]`. No KJV golden
gate exists → manual regen + `git diff` across editions to prove only intended bytes moved; rebuild
flagship eink + kepubify + epubcheck 0/0/0/0 + auditor green + Kobo device eyeball.

## Status
- [x] WS1 auditor built · first run (472/18/109) — SUPERSEDED (measured the wrong thing)
- [x] **WS1 auditor RE-ARCHITECTED** (correct prose-before-marker detection, accurate attribution,
      irregular/strategy-B/superscription classification; TDD 14/14) · true scope = 62 breaks · 18 ¶ ·
      mixed-translation = the ¶-co-located bracket set · fix target = base HTML
- [x] Discrete: Prayer of Azariah ToC title re-shortened + pinned (`83391827`; verified done + wired)
- [x] **WS1 fix — mid-verse breaks DONE** (`b7721a4f` + auditor owner-None fix). Poetry = user "keep".
      Eink-gated `_merge_mid_verse_breaks` (after the page-break base-file merge); narrative/prose canon only
      (`_MIDVERSE_BREAK_KEEP_BOOKS`). **Built flagship `ethiopian-tewahedo` eink: 62 → 0 narrative breaks**
      (auditor); kepubified → staged `C:\Users\bogda\YHWH-device-staging\YHWH-koboQA.kepub.epub` → **0 breaks
      survive kepubify**. 9-KJV/tablet/default base untouched (eink-gated, no re-baseline). TDD 24 pins +
      file-split 54. **epubcheck 0/0/0/0 ✓ · Mac cross-OS PASS ✓ (`39799498`, incl. byte-stability eink-gate).**
      ⏳ device eyeball (HUMAN_DECISIONS).
- [ ] WS1 "¶" (was "mixed-translation") — **ROOT CAUSE CORRECTED by Mac (`90d48cfb`,
      `dev/audit/ws1-mixed-translation-finding.md`): NOT KJV-in-WEB / NOT a verse rewrite.** It's a
      **dropped verse boundary**: **162 EMPTY verse anchors** whose WEB text was merged into the *next* verse
      (base[N+1] = WEB[N]+WEB[N+1]); on eink the empty verse's inlined KJV popup shows its ¶ = the "weird symbol."
      **Fix = RE-SPLIT** base[N+1] at the WEB[N]/WEB[N+1] seam, moving WEB[N] back under the empty v-N anchor —
      **NO wording change** (data: `dev/audit/ws1-empty-verse-resplit-data.json`). My earlier worklist
      (`ws1-mixed-translation-worklist.md`) used the WRONG (KJV→WEB-rewrite) premise → **SUPERSEDED**, do not action.
      162-verse all-edition versification re-baseline → **USER RATIFICATION queued in `dev/HUMAN_DECISIONS.md`**;
      34 triage cases (legit WEB omissions + Sirach/deuterocanon offsets). **Sub-task: correct the auditor to detect
      EMPTY verse anchors** (the ¶/bracket classes are wrong — Mac proof: 0 body ¶, all 2,970 are KJV popups).
- [x] **WS2 note-cascade de-dup DONE** (`8115876f`). Class 1 — drop leaf `note-sym` in grouped
      `_emit_cascade_sections`; Class 2 — strip `xref-citation`/`text-witness` body lead-ins
      (`_strip_redundant_body_boilerplate`, exact-kind, s1_dedup-gated). 6 TDD pins + 96 cascade green.
      Deliberate grouped re-baseline. ✅ build-verify catholic-study eink: leaf note-sym 0 · xref/text-witness
      lead-ins 0 · 12,994 leaves intact · epubcheck 0/0/0/0. ⏳ Mac cross-OS byte-diff.
- [ ] WS3 Kobo popup run-on fix — **Mac research DONE** (`dev/audit/kobo-popup-formatting-research.md`): the study/
      cascade `verse-notes` popups use hidden U+2028 `.vn-sep` separators that Kobo's native footnote overlay DROPS;
      give them the K-R14 treatment the translation family already has — **visible `·` (U+00B7, the ONLY device-proven
      glyph — NOT `•`, which near-crashed) + `<br class="kobo-vn-br"/>`, eink-gated.** Swap `_VN_SEP_ITEM/CAT/BYLINE`
      → eink variants at `:2825` · `:3877` · `:3889` · `:3595/3597`; add `br.kobo-vn-br{line-height:1.6}` near `:2391`.
      **Load-bearing threading (eink=False default → non-eink byte-identical):** thread `eink` through
      `_emit_cascade_sections` ← (`_unit_inner` 4234 has eink_target; `_study_glossary_category_body` 3729 ← footnote
      builder 3749 ← `_emit_backmatter_glossary_inner` 3759 ← caller 4265 has eink_target) · `_badge_aside_inner_to_row`
      ← 4143 (eink_target) · `_chunk_vn_item_row` ← 3619 (`apply_note_popup_split` chain). Gates: gate-4n byte-floor
      (markers inflate koboSpan bytes) · epubcheck 0/0/0/0 · regen+diff non-eink byte-identical · **device A/B (user gate:
      `·` renders in Cardo + the worst-case unit still POPS not crashes).** Implement fresh (byte-critical refactor).
- [ ] Final device eyeball clean → program closed
