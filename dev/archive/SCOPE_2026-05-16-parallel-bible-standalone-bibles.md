# SCOPE addendum — Parallel-Bible END-STATE: two standalone Bibles

**Date:** 2026-05-16
**Status:** ACTIVE — supersedes the popup-only framing.
**Relationship:** end-state design addendum to the authoritative
`dev/SCOPE_2026-05-14-parallel-bible.md`. Where the two conflict on
*purpose/destination*, this document wins; the 2026-05-14 spec
remains authoritative for the *ingest mechanics* (engines, parser,
structural_map, renumber-against-floor, the τ.6.x/τ.7.x cadence).

---

## 0. Why this addendum exists

The τ.6.x (`content/translations/geez-tewahedo/`) and τ.7.x
(`content/translations/amharic-tewahedo/`) per-book ingests were
written, and the in-repo docs / `_meta.yaml` notes framed, as if
the goal were **verse-popup language slots** (add `geez` /
`amharic` to editions' `popup_languages_default`, or use them as a
`popup_translation` swap). That framing is incomplete and misled a
prior session. The user clarified the actual intent on 2026-05-16.
This addendum is the durable, in-repo record so the misread does
not recur.

The per-book rendering already shipped is **NOT wasted** — it is
the foundation for the end-state below.

---

## 1. End-state (the actual goal)

`geez-tewahedo` and `amharic-tewahedo` become **two new STANDALONE
Bible editions** — a **Ge'ez Bible** and an **Amharic Bible** —
each a full version with its own books and chapters, sitting
alongside the existing 9 canon/notes editions (they are NOT a
10th/11th canon variant; they are full-text scripture editions in
their own right).

Each of the two standalone Bibles carries, in **its own verse
popups**, a **faithful English translation derived from that
Bible's actual Ge'ez / Amharic wording** — a fresh rendering of
what the text actually says, NOT the KJV and NOT the existing
English editorial-apparatus baseline.

---

## 2. Verse-popup policy (decided 2026-05-16)

| Target | Ge'ez / Amharic in verse popups? |
|---|---|
| The other 9 editions (catholic, protestant, tanakh, orthodox, eastern-orthodox, anglican-BCP, lutheran-confessional, coptic-orthodox, **and the existing English `ethiopian-tewahedo`**) | **NO.** Do not wire `geez`/`amharic` into their `popup_languages_default` or `popup_translation`. Drop the "enable once full coverage" plan for them. |
| `ethiopian-tewahedo` (the existing **English** Ethiopian edition) | **MAYBE — conditional only.** Permitted *only if* every verse count matches across **all** books and **all** chapters (full per-verse parity between the apparatus text and the parallel text). If parity is not total, do not add them. This is an option to revisit, not a commitment. |
| The two new **standalone** Bibles (Ge'ez Bible, Amharic Bible) | **YES — this is the point.** Each shows, per verse, a faithful English translation of that Bible's own actual wording. This is the preferred design. |

Rationale: the parallel scripture belongs *as scripture* in its own
editions with an honest English gloss of what it actually says —
not sprinkled into unrelated editions' popups.

---

## 3. Source & citation policy

- **Amharic:** use the text **as written in the parallel-Bible
  EOTC PDF**, cited/referenced to that source accordingly. No
  reconstruction of the Amharic column.
- **Ge'ez:** the parallel-PDF Ge'ez column is ocr-tier3
  (garbled/partial — see `_source.yaml::ocr_caveats`). Its **gaps
  are filled from the `GAPS` folder**
  (`C:\Users\bogda\Documents\YHWH-v2.4-full\GAPS`, outside the
  `YHWH v2.4\` project subdir). GAPS is **DEFERRED — note only**:
  do not open, list, or process it until the user re-engages it
  after rendering completes. (Memory: `gaps-folder`.)
- The faithful English back-translation is produced **from the
  finished Ge'ez / Amharic text** (post-rendering, post-gap-fill),
  not from English sources.

---

## 4. Sequence (do NOT reorder; do NOT pull forward)

1. **Rendering (IN PROGRESS).** Finish all per-book Ge'ez +
   Amharic verse ingests — the current τ.7.x.* (Amharic, 22/87)
   and τ.6.x.2.* (Ge'ez catchup) cadence. This is the only active
   phase. Keep shipping per-book under D1-a + D4-c.
2. **Constitute the two standalone Bible editions** (full books +
   chapters) once rendering is sufficiently complete.
3. **Amharic finalized** as-written-from-PDF with citation;
   **Ge'ez gaps filled** from `GAPS`.
4. **Faithful English back-translation** of each Bible's actual
   Ge'ez / Amharic wording.
5. **Wire that English into the two Bibles' own verse popups.**

Phases 2–5 are post-rendering. Until the user explicitly says
rendering is finished and re-engages, only phase 1 work proceeds —
do **not** start the standalone-edition constitution, the GAPS
gap-fill, or the back-translation.

---

## 5. What does NOT change

- The τ.6.x/τ.7.x ingest mechanics, parser, `structural_map`,
  renumber-against-floor, the per-book test-pin convention, and
  the honesty contract (`τ.6.x.0b`; defer-don't-fabricate, the
  `lje`/`susanna` `present_in_pdf:false` precedent) all stand
  unchanged. `dev/SCOPE_2026-05-14-parallel-bible.md` remains
  authoritative for those.
- The existing 9 editions and the builder demo are unaffected.
- "continue" still advances the per-book rendering cadence.

---

## 6. Cross-references

- Authoritative ingest spec: `dev/SCOPE_2026-05-14-parallel-bible.md`
- North star: `dev/CLAUDE_PROJECT_RULES.md` §1
- Memory: `parallel-bible-two-standalone-bibles`, `gaps-folder`
- Per SCOPE §11 convention, the PLAN carries a one-line
  cross-reference to this addendum; SESSION_STATE references it
  while the arc is active.
