# WS1 re-split — ratification-hardening check (P2)

> **Mac → WIN, 2026-06-25.** Independent, programmatic re-verification of the 162-verse WS1
> empty-verse re-split package (`dev/audit/ws1-empty-verse-resplit-data.json`) against the **real
> base HTML** (`epub_working/`), so the user's ratification in `dev/HUMAN_DECISIONS.md` is a
> 2-minute yes/no and WIN can apply the re-baseline mechanically with **zero scripture-guessing risk**.
>
> Reusable gate: **`dev/audit/ws1_resplit_verify.py`** (ruff-clean, exits non-zero on any flag or
> unclassified empty). Re-run any time: `.venv/bin/python dev/audit/ws1_resplit_verify.py`.

## Verdict

**158 of 158 re-split empties are mechanically SAFE & byte-reversible · 0 flagged.**
**Completeness: 0 unclassified empty anchors** — every empty verse anchor in the base is accounted
for. The re-baseline will move **only the 158 intended boundaries**; no wording changes anywhere.

| check | result |
|---|---|
| resplit groups | **155** (158 empties — 152 single-empty + 3 consecutive 2-/3-way) |
| (a) each empty is a TRULY EMPTY anchor in base | ✅ 158/158 |
| (b) web[empty] is a clean leading prefix of the terminal body (seam unambiguous) | ✅ 158/158 |
| (c) split is byte-reversible (peel→rejoin == base body, no wording change) | ✅ 155/155 groups |
| **flagged (ambiguous seam / not-a-clean-prefix / wording drift)** | **0** |
| completeness: empty-body anchors in base | 200 — **all 200 classified, 0 unclassified** |
| deutero-defer (leave for the deuterocanon source) | 43 |
| legit WEB omission (stay empty) | 4 |

## Method (what each check proves)

For every group `{empties[], terminal, file, web_per_verse}` the verifier parses the base file,
tokenizes scripture by `vn-link` verse anchors, strips apparatus (`note-ref` anchors, `<sup>`
markers, all tags, HTML entities) and chapter headings, then:

- **(a)** confirms each `empties` coord's anchor has **no prose** between it and the next verse
  anchor (truly empty — the visible defect on eink, where the inlined KJV popup fills the gap).
- **(b)** peels each `web[empty]` off the **front** of the terminal verse's full base prose; it must
  be an exact leading prefix (the seam is therefore unambiguous — the WEB per-verse boundary is the
  only place it can split).
- **(c)** after peeling all empties, the residual must equal `web[terminal]` **exactly**, and
  `" ".join(web[empty…] + [web[terminal]])` must reproduce the base terminal body **byte-for-byte**
  (NFC-normalized, whitespace-collapsed). This guarantees the re-split is the exact inverse of the
  merge — it relocates a clause boundary and changes **no wording**.

### Note on 3 initially-flagged cases (resolved — verifier artifacts, not data defects)

The first pass flagged `ecc 6:12`, `sng 2:17`, `act 17:34`. All three are a chapter's **last**
verse; the parser had bled the next chapter's heading number (` 7`, ` 3`, ` 18` from
`<p class="ch-heading"><span class="bold-num">N</span></p>`) into the terminal body. The scripture
text matched `web[terminal]` exactly. Fixed by stopping body capture at the `ch-heading` boundary →
**0 flags**. (The data itself was correct in all three.)

## Before / after — the user's eyeball samples

These are the actual base bodies and the WEB per-verse texts the re-split assigns. **BEFORE** = the
defect (empty anchor; the whole clause currently sits in the next verse). **AFTER** = the WEB-faithful
boundary the re-split restores — same words, just re-parted at the WEB verse seam.

**gen 8:15 → 8:16**
- BEFORE: `v15 = (empty)` · `v16 = "God spoke to Noah, saying, “Go out of the ship, you, your wife, your sons, and your sons’ wives with you."`
- AFTER:  `v15 = "God spoke to Noah, saying,"` · `v16 = "“Go out of the ship, you, your wife, your sons, and your sons’ wives with you."`

**mat 5:4 → 5:5**
- BEFORE: `v4 = (empty)` · `v5 = "Blessed are those who mourn, for they shall be comforted. Blessed are the gentle, for they shall inherit the earth."`
- AFTER:  `v4 = "Blessed are those who mourn, for they shall be comforted."` · `v5 = "Blessed are the gentle, for they shall inherit the earth."`

**psa 10:12 → 10:13**
- BEFORE: `v12 = (empty)` · `v13 = "Arise, Yahweh! God, lift up your hand! Don’t forget the helpless. Why does the wicked person condemn God, and say in his heart, “God won’t call me into account”?"`
- AFTER:  `v12 = "Arise, Yahweh! God, lift up your hand! Don’t forget the helpless."` · `v13 = "Why does the wicked person condemn God, and say in his heart, “God won’t call me into account”?"`

In every safe case the AFTER is a clean re-parting of the SAME words at the WEB verse boundary —
**no word is added, removed, or changed.**

## Triage re-confirmation (no scripture guessing)

- **4 legit WEB omissions — stay empty** (✅ confirmed empty anchors in base; these are the
  well-known WEB / critical-text omissions, KJV popup is the correct fallback):
  `luk 17:36`, `act 8:37`, `act 15:34`, `act 24:7`.
  Cross-check: none of the 158 re-split empties is a WEB-omitted verse — every re-split empty has
  real WEB text (else (b)/(c) would have flagged "no web text"). The omission set is clean of the
  re-split set and vice-versa.
- **43 deutero-defer — NOT auto-resplit** (resolve per-verse against the Greek/deuterocanon source;
  WEB numbering differs — no guessing). Sirach / Letter-of-Jeremiah (`lje`) / Ethiopian Daniel
  additions. **5 of these (`sir 11:15, 16:15, 19:18, 22:9, 26:19`) are not empty but carry a base
  `-` placeholder** — correctly deferred (placeholder, not a dropped boundary). Verdicts per coord
  belong in `dev/audit/ws1-resplit-triage.md` when WIN folds them at ratification.

## What this de-risks

The user's `HUMAN_DECISIONS.md` gate ("no scripture guessing") is satisfied for the 158-verse
re-split: the move is **purely mechanical and byte-reversible**, touches only the 158 intended
boundaries, and changes no wording. The deuterocanon offsets remain a separate, source-gated task
(not part of this ratification). After ratification, the standing P6 cross-OS byte-verify confirms
only those 158 boundaries moved across all editions (incl. the 9-KJV byte-stable set).
