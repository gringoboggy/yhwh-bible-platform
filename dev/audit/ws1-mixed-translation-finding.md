# WS1 "mixed-translation" (¶ pilcrows) — corrected root cause: a dropped-verse-boundary defect

> **Mac → WIN, 2026-06-25. A course-correction, not a verse-rewrite spec.** The WS1 program
> (`dev/audit/kobo-deep-audit-program-2026-06-24.md` §WS1; LANE_HANDOFF "the 18 ¶-co-located
> mixed-translation set") assumed the 18 `¶`/`[bracket]` findings are **KJV-text intrusions in the
> WEB scripture body** to be **normalized by rewriting the verses to WEB**. **That premise is wrong
> on every axis.** There is no KJV text in the scripture body, the count is not 18, and the fix is not
> a rewrite. The real defect is a **systematic dropped verse boundary**: **162 verse anchors across
> the canon are EMPTY** because the verse's WEB text was merged into the *following* verse. On the
> eink edition the inlined KJV verse-popup fills the empty slot, surfacing the KJV's own `¶` — which
> is the "weird symbol" the user saw. **Do not rewrite scripture; restore the verse boundaries.**

---

## TL;DR for WIN

1. **Do NOT rewrite/normalize any verse wording.** Scripture bodies are clean WEB; no KJV is in them.
2. The real defect: **162 empty verse anchors** (`<a class="vn-link" id="v-…">` with no body) whose
   WEB text is the **lead clause of the next verse** (base verse N+1 = WEB[N] + WEB[N+1]). All 18
   `¶`-flagged verses are a subset of these 162.
3. **The `¶`/`[brackets]` are KJV verse-POPUP content** (`<p class="vnote-text">`, the KJV English
   beside Hebrew/Greek — `build_edition.py:794-816`). The **eink study layout inlines popups into
   prose** (`eink_inline_in_prose`, `build_edition.py:3988-4368`), so the KJV popup of an *empty*
   verse renders inline — KJV `¶` and all. That is the only reason the 18 are "visible."
4. **Fix (versification-faithful, no wording change):** for each of the 162, split base verse N+1's
   body at the WEB[N] / WEB[N+1] seam, moving WEB[N]'s clause back under the empty v-N anchor. The
   exact per-verse split data is in **`dev/audit/ws1-empty-verse-resplit-data.json`**.
5. The auditor `dev/audit_verse_formatting.py` mislabels this as "stray pilcrow / mixed base
   translation." It should detect **empty verse anchors** directly (§Auditor).
6. This is a **large, versification-sensitive base-HTML change** (162 verses, all editions) → it is a
   **deliberate re-baseline** and a **user decision** (→ `dev/HUMAN_DECISIONS.md`), not a quick patch.

---

## How we got here (honest record)

- **Program premise:** "18 KJV-text verses in a WEB base → rewrite to WEB." 
- **First Mac read:** "bodies are clean WEB → just strip the popup `¶`." *Partly wrong* — it missed
  that the verse bodies are not merely clean, they are **empty**, so stripping the popup `¶` alone
  would leave the verse **blank** on eink.
- **Adversarial refutation (independent agent):** "the verse bodies are **missing**, KJV fills the
  gap → inject WEB." *Partly right* (it found the empty bodies) but the fix it proposed is also
  wrong: the WEB text is **not missing from the file** — it is mis-attached to the next verse;
  injecting from the VPL would **duplicate** it.
- **Ground truth (verified against real bytes, below):** an empty anchor + the verse's WEB text
  absorbed as the lead clause of verse N+1 = a **dropped verse boundary**. Fix = **re-split**, not
  rewrite, not inject, not popup-strip-alone.

---

## Proof (real data, macOS, HEAD `39799498`)

**(1) Zero pilcrows in scripture body; all 2,970 are in the popup apparatus.** Bucketing every base
`<p>` that contains a `¶` by class: `verse-p` (body) **0** · `vnote-text` (KJV popup) **2,970** ·
other **0**. The auditor's body matcher is `verse-p` (`audit_verse_formatting.py:58`).

**(2) The flagged verses are EMPTY anchors; their WEB text sits under the next verse.** From the base
(`epub_working/index_split_001.html`), with note-refs/badges/asides stripped:
```
[v8:14] In the second month … the earth was dry.   [v8:15] (empty)   [v8:16] God spoke to Noah, saying, “Go out of the ship, you, your wife …
```
`v8:15` has no body. `God spoke to Noah, saying,` is **WEB 8:15** — it is the lead clause of base
`v8:16` (`eng-web_vpl.txt`: `GEN 8:15 God spoke to Noah, saying,` · `GEN 8:16 “Go out of the ship…`).

**(3) The pattern is universal across the canon** (psa, mat, pro, job, luk, num, gen, exo, lev, …):
in every case base[N+1] begins with WEB[N], e.g. base `mat 5:5` = WEB 5:4 "Blessed are those who
mourn…" + WEB 5:5 "Blessed are the gentle…"; base `num 3:15` = WEB 3:14 + WEB 3:15.

**(4) Scope (triaged against the in-repo WEB source `content/translations/sources/web/eng-web_vpl.txt`):**
- **205** empty verse anchors in the base.
- **162** confirmed off-by-one dropped-boundary defects (base[N+1] starts with WEB[N]) — **the fix
  set**. All 18 `¶`-flagged verses are here. By book: psa 31 · mat 13 · pro 11 · num 8 · gen 7 ·
  job 7 · luk 6 · act 6 · 1ch 5 · sng 5 · isa 4 · jer 4 · 2es 4 · … (full list in the JSON).
- **34** need individual triage (NOT the mechanical fix): **legitimate WEB omissions**
  (`luk 17:36`, `act 8:37`, `act 15:34`, `act 24:7` — textual-critical omissions; the empty anchor is
  *correct* for WEB) and **deuterocanon versification offsets** (Sirach ×~26, `jos 15:29-30`,
  `neh 10:19-20`, `1th 5:19-20`) where WEB's verse numbering differs from the project's canonical-KJV
  numbering, so a direct match is unreliable.

**(5) Why the eink build surfaces it.** `READER_EINK_STUDY_LAYOUTS = {"backmatter","inline","popup"}`
(`build_edition.py:2291`); for the eink target with an `inline`/`popup` study layout,
`eink_inline_in_prose` keeps/inserts the `<aside class="vnote">` popups **in prose order**
(`build_edition.py:3990, 4331, 4365-4368`). The empty verse has no WEB body, so its inlined KJV popup
is what the reader sees — KJV `¶`/`[brackets]` included. In the **built** eink epub the `gen 8:15`
`verse-p` reads `[15] ¶ And God spake unto Noah, saying,* [16] God spoke to Noah, saying, “Go out of
the ship…` with **no `<aside>`/`vnote-text` wrapper** (already flattened), which is exactly why the
auditor's `verse-p` regex catches the KJV `¶`.

---

## The fix (WIN owns; content/base surface; versification-faithful; NO scripture rewrite)

For each of the **162 confirmed** verses, restore the dropped boundary:

- Base verse N+1 currently contains `WEB[N] + WEB[N+1]` and verse N's anchor is empty.
- **Split at the WEB[N] / WEB[N+1] seam:** move WEB[N]'s clause out of verse N+1 and into the empty
  v-N anchor's body (preserving the existing note-ref markers that already sit on the v-N anchor).
- **No words change** — only which verse marker each clause sits under. The WEB VPL gives the exact,
  deterministic seam. **`dev/audit/ws1-empty-verse-resplit-data.json`** has, per verse:
  `{book, ch, verse, file (index_split_NNN.html), web_N (clause to move), web_N1 (residual), base_next_full}`.
- **The 34 triage cases:** leave the legitimate WEB omissions empty (the KJV popup is the correct
  fallback there — a popup-`¶` cosmetic decision applies, see below); resolve the Sirach/deuterocanon
  numbering offsets against the actual deuterocanon source, **per verse, no guessing**.

**Why not the alternatives:** rewriting the 18 verses to WEB would corrupt clean scripture (and the
body is already WEB); injecting WEB from the VPL would duplicate text that is already present in
verse N+1; stripping the popup `¶` alone would leave the 162 verses **blank** on eink.

**Cosmetic companion (independent of the re-split):** the inlined KJV popups carry the KJV's own `¶`
and `[supplied-word]` brackets. Even after the re-split, consider stripping a leading `^\s*¶\s*` from
the inlined `vnote-text` (eink-gated) so legitimate empty/omitted verses and any still-inlined KJV
popup don't show the bare pilcrow. Brackets are valid KJV supplied-word notation → keep/strip is a
user call. This is the same note/build surface as WS2/WS3, **not** scripture.

## Auditor correction (recommended — `dev/audit_verse_formatting.py` is WIN's WS1 gate)

The "stray pilcrow / mixed base translation" classes are factually wrong (Proof 1-3). Replace with a
direct **empty-verse-anchor** check: flag any `v-<book>-<ch>-<v>` whose body has no prose, then
classify against the WEB source — *dropped boundary* (WEB has the text → ERROR/fix) vs *legitimate
omission* (WEB has none → INFO). Strip `<aside>`/`vnote` content before counting body `¶`/brackets so
the inlined KJV popup never masquerades as a scripture-body defect. Fix the docstring lines 25-30/28-30.

---

## Reproduce
```bash
export PYTHONUTF8=1
# the four numbers (0 body ¶ / 2970 popup ¶ / 205 empty anchors / 162 confirmed):
.venv/bin/python dev/audit_verse_formatting.py build/ws1-verify-eink/Ethiopian_Bible_ethiopian-tewahedo_0.1.0_eink_2026-06-25T044133Z.epub --sample 30
grep -E '^(GEN 8:15|GEN 8:16) ' content/translations/sources/web/eng-web_vpl.txt   # WEB seam
python -c "import json;d=json.load(open('dev/audit/ws1-empty-verse-resplit-data.json'));print(len(d['confirmed_off_by_one']),'confirmed,',len(d['needs_triage']),'triage')"
```

## Gates after WIN's re-split (deliberate re-baseline, all editions)
- `dev/audit_verse_formatting.py <rebuilt eink epub>` → 0 empty-anchor ERRORs in the 162 set; the 34
  triage cases classified correctly.
- **Byte-stability:** this touches the SHARED base `epub_working/` → it re-baselines **all** editions
  including the **9-KJV byte-stable** set. There is no KJV golden gate → manual regen + `git diff`
  across editions to prove **only** the 162 verse boundaries moved (no wording change anywhere).
- `epubcheck` 0/0/0/0 on rebuilt editions; structural auditor PASS; every `#vnote-…`/`#v-…` frag still
  resolves (the v-N anchors gain a body but keep their ids).
- Device A/B (user gate): empty verses now show WEB text (not the KJV `¶`) on the Kobo.

## ⚠ User decision (→ `dev/HUMAN_DECISIONS.md`)
This is a **162-verse, all-edition, versification-sensitive** base change (Boggy's faith-driven scope:
no scripture guessing). Recommend the user ratify the WEB re-split before WIN re-baselines, and eyeball
a sample (gen 8:15, mat 5:4, psa 10:12) of before/after. The cosmetic popup-`¶` strip is a separate,
smaller call.

---

## Adversarial verification record
An independent refutation pass was run against the first Mac read ("clean WEB, strip popup `¶`"). It
**refuted** that read by discovering the verse bodies are **empty**, which was the key to the real
root cause. Its own proposed fix ("inject WEB text") was then disproven by the off-by-one evidence
(the WEB text is present under verse N+1, not missing). The dropped-boundary conclusion survives both:
verified across 162 verses, 6 book types, and the full WEB-source cross-check.
