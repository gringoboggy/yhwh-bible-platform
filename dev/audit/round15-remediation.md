# Round-15 remediation tracker — the 9 completeness-critic gaps (two-lane, PARALLEL)

Plan USER-APPROVED in plan mode (2026-06-26). Program: `dev/audit/round-15-completeness-audit-program-2026-06-26.md`.
Process matches round-14: configure `deep-audit.js ROUND=15` → run two-lane → adversarially verify → fix TDD +
byte-stability → loop-until-green. `truth_owner = windows`; file-disjoint (WIN owns `scripts/build_edition.py` +
build-heavy dims; Mac owns `scripts/core/versification.py` + source/build-free dims + cross-OS verify).
Marathon core off-limits. Round-14 SETTLED items are `DEFERRED_BY_DESIGN` (a verifier must refute any finding that
merely re-raises them).

## Dimensions

| Dim | sev | lane | finding / defect class | status |
|-----|-----|------|------------------------|--------|
| **D4** | HIGH | WIN | round-14 #4 `_cascade = s2_group or eink_backmatter` over-strips dict/topic/xref/witness **source provenance** in the `{S1-on, S2-off, eink-backmatter}` /customize combo — the eink-backmatter glossary (`_study_glossary_category_body`, `s2_group=False`) emits BARE rows with no re-surfacing byline | ✅ **FIXED** (WIN) — `build_edition.py:4228` narrowed to `_cascade = s2_group`. Empirically confirmed: gen-1 dict-easton provenance `Dictionary (Easton's)` 545→**0** pre-fix vs **545** post-fix (matches non-eink control). Regression test `test_d4_dict_source_provenance_conserved_on_eink_backmatter_s2off` (RED 0≠545 → GREEN 545==545). `test_note_rehaul` 51 + `test_ws2_cascade_redundancy` 11 (round-14 #4 strip-fn pins intact) + `test_kobo_device_qa` 16 green. **Byte-stable by tautology** (all 9 KJV golden cells non-eink ⇒ `eink_backmatter=False` ⇒ line identical; catholic-study eink has `s2_group=True` ⇒ `_cascade` identical) — G1 golden gate confirming. |
| **D3** | HIGH | MAC | Douay/Clementine-Vulgate **Psalm 2:13 + Psalm 4:10 silently DROPPED** — `vulgate_to_kjv` returns `None`, so real scripture text is missing from the parallel popups | ☐ **CONFIRMED LIVE (WIN verified, Mac to fix).** `vulgate_to_kjv("psa",2,13)→None`, `("psa",4,10)→None`; both verses present in `content/translations/sources/douay-rheims/engDRA_vpl.txt`. Fix = add `_VULGATE_PSALM_FIXES` `(2,13)→(2,12)` + `(4,10)→(4,8)` (trailing concat-fold, same shape as the present `(135,27)→(136,26)` at `versification.py:886`). Build `dev/audit_versification_coverage.py` (source-coverage gate). **Byte note:** changes catholic-study (carries the Douay popup) → reviewed re-baseline via `G1 --regen` on the affected cells; confirm diff confined to Ps 2:12 / 4:8 popups. |
| **D1** | HIGH | MAC | release asset-set integrity (orphan/missing/dup SHA256SUMS, stale hard-coded version, retired-SKU EPUBs) | ☐ TODO (Mac) — `dev/audit_release_assets.py`. Spotted: `gen_release_catalog.py:47-55/61-68` hard-codes `v0.1.0`; `lint_rules.check_retired_edition_skus` scans only the repo tree. |
| **D2** | MED | WIN | rendered xref/noteref anchor whose target id is absent from the reader's spine piece (idmap miss / canon-filter drop); `check_xrefs.py` scans only pre-split superset | ◐ **PARTIAL (WIN).** ✅ `check_xrefs.py:52-53` regex hardened — `\bid=`/`\bhref=` → `(?<![-\w])…` so a future `data-*-id=`/`data-*-href=` value is no longer harvested as a real id/link (dormant today: 0 in base, proven zero-diff; self-checked). ☐ Remaining: extend **G3** `audit_idmap_frags` with an xref breakout on FRESH canon-filtered + superset builds + wire into the per-build gate (needs a build). |
| **D5** | HIGH | WIN | `_stream_glossary_pieces_from_bytes` byte-streamer reached in PROD only by the >64 MB ethiopian flagship glossary, never byte-verified at scale; G5/`_atom_rewrite_headroom` proven only on catholic link density | ☐ TODO (WIN) — CHECK A (real flagship `index_split_900` str==from-file) + CHECK B (G5 on a fresh flagship build). Resolve: is catholic-study's glossary <64 MB (str-delegate)? |
| **D6** | MED | MAC | two independent canon determinations feed one EPUB with no source-anchored cross-check; Delta.4 equivalence pin is vacuous | ☐ TODO (Mac) — `dev/audit_canon_bookcount.py` (4-way source-anchored recount + note recount + printed "It spans N books" == spine count). |
| **D7** | MED | MAC | migration re-run/idempotency: 0001 coarse single-file marker before non-atomic `shutil.copy2`; torn-partial reports "migrated" | ☐ TODO (Mac) — `dev/audit_migration_idempotence.py` (AST write-route + double-apply convergence + ledger-independence + torn-partial probe). |
| **D8** | MED | WIN | emitted nav/opf order never asserted vs config; `enrich_nav_chapters` sorts chapters ascending → a reading-flow swap is invisible to the ToC AND the auditor | ☐ TODO (WIN) — `dev/audit_canonical_order.py` (spine bp == canonical w/ folds/demotions; chapter anchors ascending in DOCUMENT order; encode the nav-83-vs-spine-86 demotion model). No confirmed order defect; latent sort-masking. |
| **D9** | MED | WIN | fresh ethiopian `.kepub` inline `verse-notes` ids missing `-sN` tail (Kobo navigates instead of pops); `verify_kr2_build._POPUP_ASIDE_RE` can pass vacuously if kepubify reorders attrs | ☐ TODO (WIN) — `dev/audit_kepub_revid_family.py` (bucket inline vs navigate ids on a FRESH `.kepub`; assert `_POPUP_ASIDE_RE` matches >0). Fix `deep-audit.js:294` stale `dist/…kepub` pointer. |

## Round-14 SETTLED → DEFERRED_BY_DESIGN (do NOT re-litigate)
A1 LF chokepoint · A2 single-pass `_apply_splices` (the OOM was largely the AppXSvc commit-leak) · G1–G5 + A4 built ·
survivors #1–#6 + the G5 over-cap fix. Earlier-settled (regression/bleed only): WS1 re-split, WS2 cascade, WS3
separators, eink font `!important`, page-break re-arch, poetry mid-verse KEPT.

## Lane division

| owner | dimensions | files |
|-------|-----------|-------|
| **WIN** | D4 ✅ · D2 · D5 · D8 · D9 + `audit_customize_flag_matrix.py` (couples with the D4 fix) | `scripts/build_edition.py` (WIN-exclusive), `scripts/check_xrefs.py`, `dev/audit_canonical_order.py`, `dev/audit_kepub_revid_family.py`, `dev/audit_customize_flag_matrix.py`, `tests/**`, `.claude/workflows/deep-audit.js` |
| **MAC** | D3 · D1 · D6 · D7 + cross-OS verify every WIN build | `scripts/core/versification.py`, `dev/audit_versification_coverage.py`, `dev/audit_release_assets.py`, `dev/audit_canon_bookcount.py`, `dev/audit_migration_idempotence.py` |

## Log
- **2026-06-26 kickoff (WIN)** — plan approved in plan mode; program verified still-apt against current code (D3/D4
  confirmed live; D2/D9 blindspots real; round-14 settled items on disk). Mac monitor armed.
- **2026-06-26 D4 FIXED (WIN)** — `_cascade = s2_group`; RED→GREEN regression + 78 related tests green; byte-stable
  (tautology + G1 gate running). D3/D1/D6/D7 handed to Mac via LANE_HANDOFF.
