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

## WS1 — first auditor run (flagship eink, 2026-06-24)

`dev/audit_verse_formatting.py` (built TDD, 8/8 unit pins) run on the fresh flagship eink epub:
- **472 mid-verse line breaks** (verse-p paragraphs with no `v-` anchor = a paragraph break that
  landed mid-verse). **18 stray pilcrows ¶** + **109 mixed-translation `[bracket]` verses** —
  across gen/exo/lev/num/mat, so the WEB/KJV mix is WIDESPREAD, not just gen 46/49. **30,104
  badge-trail spans.**
- **Key structural fact (measured):** the doc has **36,329 `v-` verse anchors in only 2,088
  `<p class="verse-p">` paragraphs** → verses flow WITHIN a paragraph (good); a paragraph holds
  many verses. So the mid-verse breaks = the 472 *continuation* paragraphs (a source paragraph
  break that fell inside a verse). The 41,811 ¶ in the whole doc are mostly in the study-note
  backmatter (KJV cross-ref markers); only 18 are in scripture-body verse text.
- **Auditor refinement queued (counts are right; labels need polish):** (a) report "verses
  scanned" as the 36,329 anchors, not the 1,616 anchored paragraphs; (b) attribute ¶/bracket to
  the nearest PRECEDING `v-` anchor within the paragraph (today it attributes to the paragraph's
  first verse, so gen 46:13 reads as gen 46:1); (c) attribute apocrypha continuation paragraphs
  (they showed "unknown" — 1 Clement etc. use a different anchor scheme).
- **Fix approach (WS1 fix phase):** mid-verse breaks → merge each continuation `<p class="verse-p">`
  into its preceding verse paragraph at the emitter/base (so a verse never spans a `<p>` boundary);
  mixed translation → normalize the KJV-text verses to the edition's English base (NO scripture
  guessing — use the real source), stripping ¶ + `[supplied]` markers. Byte-stability: base-HTML
  change → deliberate re-baseline, prove only intended bytes moved.

## Status
- [x] WS1 auditor built (TDD, 8/8) · first run on flagship · root-cause + scope confirmed (472 breaks · 18 ¶ · 109 mixed-translation)
- [ ] WS1 auditor refinement (anchor-accurate attribution + verse count + apocrypha)
- [ ] Discrete: Prayer of Azariah ToC title re-shortened + pinned
- [ ] WS1 fix (multi-`<p>` verses + mixed-translation) + re-baseline + device-verify
- [ ] WS2 note-redundancy audit + cascade rework + device-verify
- [ ] WS3 Kobo popup formatting research + fix + device A/B
- [ ] Final device eyeball clean → program closed
