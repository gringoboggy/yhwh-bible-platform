# C-8 collation review — 1 Kings 4

*Adversarial review by independent fresh reviewer, 2026-05-20 (tau.6.x.4.c).*

Artifacts audited:
- `content/manuscript/kings/collation/1ki4_collation.json` (5222 lines)
- `content/apparatus/1ki.json` (443 lines, 34 entries)
- `scripts/run_1ki4_collation.py` (284 lines, one-shot driver)
- `content/manuscript/kings/calibration/1ki4_witnessGG.json` (28 v / 486 stored tokens)
- `content/manuscript/kings/calibration/1ki4_witnessCAM_hires.json` (34 v / 425 stored tokens)

Method: re-derived every metric BYTE-IDENTICAL from the engine modules
(`scripts/core/manuscript_collation.py`, `scripts/core/manuscript_records.py`,
`scripts/core/manuscript_reconcile.py`) without invoking the engine — a pure
Python re-derivation from the alignment rows + the witness files. Scratch
script lives outside the repo.

## Independent metric re-computation

| metric              | engine               | mine (independent)  | match |
|---------------------|----------------------|----------------------|-------|
| semantic_pass_pct   | 100.0% (34/34)       | 100.0% (34/34)       | YES   |
| W↔W strict          | 7.39% (42/568)       | 7.39% (42/568)       | YES   |
| W↔W skeleton        | 9.68% (55/568)       | 9.68% (55/568)       | YES   |
| both_confident      | 19.32% (34/176)      | 19.32% (34/176)      | YES   |
| uncertainty         | 32.21% (134/416)     | 32.21% (134/416)     | YES   |
| lacuna {gg,cam,both}| {0, 0, 0}            | {0, 0, 0}            | YES   |
| token-conservation  | 0 fails              | 0 fails              | YES   |

Every metric BYTE-IDENTICAL to the engine. Token conservation: GG 432 tokens
in 323 distinct (witness, geez-derived) == 432 tokens in 323 distinct (alignment,
non-lacuna); CAM 416 / 286 == 416 / 286. No drift in either direction.

## Lacuna honesty
- GG witness ⟦illegible⟧ count: 0 tokens stored, 0 in geez (expected 0)
- CAM witness ⟦illegible⟧ count: 0 tokens stored, 0 in geez (expected 0)
- Engine lacuna {gg:0, cam:0, both:0} matches evidence: **YES**

## Apparatus well-formedness
- 34 entries (one per CAM-spine verse v1..v34 — matches 1ki4 CAM verse count)
- Schema keys per entry: `{base_reading, lacunae, reason, resolution, v, variants}` — exactly the `reconcile()` shape
- All resolution = "base" (34/34): **YES**
- No `from_witness` fields (consistent with all-base resolution): YES
- Every variant has exactly 1 entry, witness=GG: **YES** (since base=CAM, non-base=GG)
- Foreign-token check: every token in `variants[].reading` is a member of the GG geez-derived token pool (323 distinct tokens). **0 fabricated tokens.**
- No `❈` (the unauthorized cross glyph) anywhere in collation or apparatus.
- No `✣` in apparatus base_reading / variants reading (correctly stripped by `_geez_to_tokens`).

Note: `1ki.json` is a NEW file (first commit 2b2a936 today). The prior
1ki1/1ki2/1ki3 collations never persisted an apparatus JSON. So 1ki.json
contains 34 entries = 1ki4 ONLY (NOT a cumulative ledger of 1ki1+2+3+4 — the
parent agent's instructions described a hypothetical pattern that did not in
fact exist in repo). This will be correctly expanded by the at-scale driver
when it runs across all 1ki chapters (the driver flushes one apparatus per
book with all collated chapters merged via `apparatus_by_book[book].extend()`).
For the marathon's current state (only 1ki4 collated under tau.6.x.4.c)
having 1ki4-only in `1ki.json` is the correct partial-write — the at-scale
driver will rebuild it complete later.

## Normalization audit
- Geez strings byte-identical pre/post (git diff against witness files is
  empty; the source files are untouched, normalization is in-memory only): **YES**
- Alignment token validator-clean: every non-empty, non-illegible token in
  the collation alignment cells contains only Ethiopic block (U+1200..U+137F)
  or ✣ (U+2723). **0 dirty cells.** No Latin contamination.

**Content-preservation verdict**: the in-memory rebuild preserves Ge'ez
content faithfully. Token drift (GG 486→432, CAM 425→416) is fully accounted
for by THREE legitimate `_geez_to_tokens` operations:

1. **✣ stripping** (57 in GG, 20 in CAM — total 77 ✣ tokens dropped from
   stored arrays). This is the validator's documented behavior — ✣ is a
   rubric-cross stripped before tokenization.
2. **Numeral atom split**: compound `ወ፪ቱ` → `ወ` + `፪` + `ቱ`, `፩ድ` → `፩` + `ድ`,
   `፬ደ` → `፬` + `ደ`, `፫የ` → `፫` + `የ`, etc. The regex
   `_NUMERAL_RE.sub(r' \1 ', g)` is intentional — numerals are stand-alone
   atoms. This GAINS tokens (e.g. CAM v7 stored 20 → derived 24, v23 14→16,
   v26 11→13, v32 7→8). Net of the ✣ drops, CAM ends at 416.
3. **Ethiopic full-stop ።**: v13 CAM has `ብርት።` → `ብርት` (one ። stripped).
   Same intentional handling as ✡/፣/✣.

**Zero Ge'ez consonant or vowel loss.** Every fidel from the original geez
strings appears in the rebuilt token array, only the delimiters (✣ rubric,
። fullstop, ፣ comma) are stripped (consistent with the validator's bijection
spec) and numerals split into atoms. The geez strings are byte-identical.

## MATCHES criteria check (per bi-directional rule)
- Semantic ≥95% on clean text: **PASS** (1ki4 = 100.0%, well above 95%)
- Both_confident materially <90% on clean folios: **PASS** (1ki4 = 19.32%,
  far below 90% — expected for distinct recensions on a list chapter like
  1Ki4's "officer of Solomon" registry; W↔W strict 7.39% likewise reflects
  this distinct-recension reality)
- Base=CAM ratified: **PASS** (clause-2 path; extents 28 GG / 34 CAM both
  ≥ 0.70 × 34 = 23.8, so material-extent split does NOT trigger; default
  CAM-by-decision-of-record applies)
- No contradiction trigger:
  - No ~unity agreement (W↔W skeleton 9.68% is the OPPOSITE of unity): PASS
  - No base flip to GG (base=CAM): PASS
  - No semantic <95% (semantic = 100.0%): PASS

The distinct-recension sub-bar produces WARNS, not fails, per the
`no-reassert-ratified-bar` memory:
- W↔W <90% strict: 7.39% — **WARN** (expected for distinct recensions; not a
  fail criterion)
- Uncertainty >10%: 32.21% — **WARN** (expected for a name-heavy list
  chapter where CAM's transcribers flagged most name-form / lectio /
  in-body-cross tokens; CAM has 134 uncertain entries across 416 tokens.
  GG-derived uncertainty is irrelevant since base=CAM).

## Driver script assessment

The C-7 driver `scripts/run_1ki4_collation.py` exists because the 1ki4
witness JSONs do not satisfy the validator schema — they alone, of the
four collated Kings chapters, ship in a NON-CANONICAL format:

**Validation results across kings calibration witnesses:**
- 1ki1 GG / CAM: ok=True / ok=True
- 1ki2 GG / CAM: ok=True / ok=True
- 1ki3 GG / CAM: ok=True / ok=True
- **1ki4 GG: AttributeError ("'str' object has no attribute 'get'")** — `uncertain[]` is a list of plain strings, not the canonical `{token_index, marker, note}` dict shape
- **1ki4 CAM: ok=False** — extra top-level keys (`manuscript`, `phase`, `ref`); custom uncertain markers outside the `{uncertain, damaged, illegible}` set (`context`, `name_form`, `lectio`, `lectio_unclear`, `in_body_cross`, `numeral`, `numeral_compound`, `spelling`, `rubric_position`); stored `tokens[]` arrays include `✣` and compound numeral-fidel forms that the validator's `_geez_to_tokens` bijection would reject

The driver does THREE normalizations in-memory: (a) strips extra top-level
keys, (b) rebuilds `tokens[]` from `geez` via `_geez_to_tokens`, (c)
remaps `uncertain[]` markers to one of the validator-allowed values
(`uncertain`/`damaged`/`illegible`) and remaps token_index where the rebuild
changed token positions. The normalization is purely in-memory; the source
files are untouched (verified by `git diff` — zero bytes changed).

**Could the at-scale driver `scripts/run_manuscript_collation_at_scale.py`
have done 1ki4 alone?** **NO** — it calls `validate_witness()` as a HARD
gate (line 191-192) and would have failed with the exact two errors above.
The non-canonical witness schema BLOCKS the at-scale driver. The one-shot
is the workaround.

**Could it have done it if witnesses were re-stored in canonical format?**
**YES** — 1ki1/2/3 work fine with the at-scale driver because their
witnesses ARE in canonical format. The cleanest fix is to migrate the
1ki4 witnesses to canonical format (rewrite each verse's `tokens[]` from
`_geez_to_tokens(geez)`; reshape `uncertain[]` to `{token_index, marker,
note}` dicts with `marker` in the allowed set; strip the extra top-level
keys `manuscript`, `phase`, `ref`). After that, the at-scale driver works
on 1ki4 with zero special-case code.

**Recommendation: NORMALIZE-WITNESSES-INSTEAD** — migrate the 1ki4 witness
files to canonical schema (this is a mechanical transform; no Ge'ez
content changes) and DELETE the one-shot driver. The schema-rot in 1ki4
witnesses is technical debt that will recur on any future chapter
transcribed before the spec was finalized. A clean canonical witness is
both the right long-term state AND makes the marathon at-scale driver
work uniformly.

If the witnesses cannot be normalized in this ship (e.g. the user wants
to defer that work), then **ARCHIVE the driver** to
`dev/archive/ship_scripts/1ki4/run_1ki4_collation.py` as an audit trail
of the one-shot intervention. Do NOT keep it in `scripts/` where the
project's at-scale convention lives — a one-shot in `scripts/` is a
trap for the next implementer who runs `ls scripts/run_*.py` looking
for the at-scale entry point.

## VERDICT

**MATCHES** (proceed to C-9 manifest update + commit) **with one concern**.

- Every engine-emitted metric independently re-derives BYTE-IDENTICAL.
- Lacuna counts honest; apparatus well-formed; no fabrication.
- Geez immutable; alignment validator-clean (no Latin/❈ contamination).
- Base=CAM correctly ratified via the §3.3 clause-2 path.
- MATCHES criteria (semantic ≥95%, both_confident <<90%, base=CAM,
  no unity / no flip / no semantic-fail) all hold.

**Concern (does NOT block C-9):** the 1ki4 witness JSONs are the only
Kings witnesses in non-canonical schema. The one-shot driver hides this
schema-rot rather than fixing it. The right disposition is to either
(a) normalize the witnesses to canonical schema and DELETE the driver
in this same ship, or (b) accept the schema-rot and ARCHIVE the driver
to `dev/archive/ship_scripts/1ki4/`. Keeping `scripts/run_1ki4_collation.py`
permanently in `scripts/` is a trap.

Recommend the implementer surface this choice to the user at C-9 commit
time, so the resolution is on the record (Memory `no-reassert-ratified-bar`
does NOT apply here — this is a one-time schema-debt decision, not a
recurring metric warn).
