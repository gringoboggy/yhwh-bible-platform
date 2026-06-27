# Round-15 remediation tracker — the 9 completeness-critic gaps (two-lane, PARALLEL)

Plan USER-APPROVED in plan mode (2026-06-26). Program: `dev/audit/round-15-completeness-audit-program-2026-06-26.md`.
Process matches round-14: configure `deep-audit.js ROUND=15` → run two-lane → adversarially verify → fix TDD +
byte-stability → loop-until-green. `truth_owner = windows`; file-disjoint (WIN owns `scripts/build_edition.py` +
build-heavy dims; Mac owns `scripts/core/versification.py` + source/build-free dims + cross-OS verify).
Marathon core off-limits. Round-14 SETTLED items are `DEFERRED_BY_DESIGN` (a verifier must refute any finding that
merely re-raises them). Mac plan: `~/.claude/plans/tranquil-sleeping-lemur.md`.

## Dimensions

| Dim | sev | lane | finding / defect class | status |
|-----|-----|------|------------------------|--------|
| **D4** | HIGH | WIN | round-14 #4 `_cascade = s2_group or eink_backmatter` over-strips dict/topic/xref/witness **source provenance** in the `{S1-on, S2-off, eink-backmatter}` /customize combo — the eink-backmatter glossary (`_study_glossary_category_body`, `s2_group=False`) emits BARE rows with no re-surfacing byline | ✅ **FIXED** (WIN, `2afa6126`) — `build_edition.py:4228` narrowed to `_cascade = s2_group`. Empirically confirmed: gen-1 dict-easton provenance 545→**0** pre-fix vs **545** post-fix. Regression `test_d4_dict_source_provenance_conserved_on_eink_backmatter_s2off` (RED→GREEN). **Byte-stable by tautology** (9 KJV golden cells non-eink ⇒ `eink_backmatter=False`; catholic-study eink has `s2_group=True`). Gate `audit_customize_flag_matrix.py` = WIN (couples with the fix). Mac diagnosis (3-agent) concurred. |
| **D3** | HIGH | MAC | Douay/Clementine-Vulgate **Ps 2:13 + Ps 4:10 silently DROPPED** — `vulgate_to_kjv`→`None`, real scripture missing from the `vulgate` parallel popup | ✅ **FIXED** (Mac, `29321fad`) — `_VULGATE_PSALM_FIXES` `(2,13)→(2,12)` + `(4,10)→(4,8)` (same trailing-fold shape as `(135,27)→(136,26)`); regen CONFINED to douay/vulgate `psa.py` (2:12/4:8 gain their tails; appendix + `_meta` preserved). `dev/audit_versification_coverage.py` exhaustive gate GREEN (selftest non-taut; breadth pass found 0 more drops). Pinned: `test_psalm_fix_maps[(2,13)/(4,10)]` + `test_round15_source_gates`. ⚠ **G1 golden RE-STAMP PENDING (WIN)** — `vulgate` popup (all 4 study editions) gains the Ps 2:12/4:8 clause; built delta confined to those 2 verses; `douay` store latent. |
| **D1** | HIGH | MAC | release asset-set integrity (orphan/missing/dup SHA256SUMS, retired-SKU EPUBs) | ✅ **GATE DONE** (Mac, `29321fad`) `dev/audit_release_assets.py` (selftest + live). **Live v0.1.0 has 100 retired-SKU EPUBs attached** (all 5 retired editions × 20 cells — not "2"); bijection clean (0 orphan/missing). The `gen_release_catalog` v0.1.0 strings are INTENTIONAL legacy cells (sub-check dropped, per plan). **FIX = v1.0.0 tag-time re-cut** (outward-facing → flagged, NOT autonomous). `check_retired_edition_skus` excludes the gate+tracker (they name SKUs to detect them). |
| **D2** | MED | WIN | rendered xref/noteref anchor whose target id is absent from the reader's spine piece; `check_xrefs.py` scans only pre-split superset | ◐ **PARTIAL (WIN, `2afa6126`).** ✅ `check_xrefs.py:52-53` regex hardened (`\bid=`/`\bhref=` → `(?<![-\w])…`; dormant today, zero-diff). ☐ Remaining: extend **G3** `audit_idmap_frags` xref breakout on FRESH builds + wire into the per-build gate. |
| **D5** | HIGH | WIN | `_stream_glossary_pieces_from_bytes` byte-streamer reached in PROD only by the >64 MB ethiopian flagship glossary, never byte-verified at scale | ☐ TODO (WIN) — CHECK A (real flagship `index_split_900` str==from-file) + CHECK B (G5 on a fresh flagship build). |
| **D6** | MED | MAC | two independent canon determinations feed one EPUB with no source-anchored cross-check; Delta.4 equivalence pin is vacuous (both paths share `_canon_books_for_edition`) | ☐ **IN PROGRESS (Mac)** — `dev/audit_canon_bookcount.py` (source-anchored 4-way recount: fresh `yaml.safe_load(canons.yaml)` == `compute_matrix` == file-walk == `epub_utils.load_canons`; note recount == `resolved_note_counts['total']`) + de-vacuum the Δ.4 test. |
| **D7** | MED | MAC | migration re-run/idempotency: 0001 coarse single-file marker before non-atomic UNSORTED `shutil.copy2`; torn-partial reports "migrated" | ☐ **IN PROGRESS (Mac)** — `dev/audit_migration_idempotence.py` (sandbox via `YHWH_DATA_DIR`: double-apply convergence + ledger-independence + torn-partial probe) + 0001 torn-safe fix (sorted copy + marker written LAST, atomically). |
| **D8** | MED | WIN | emitted nav/opf order never asserted vs config; `enrich_nav_chapters` sorts chapters ascending → a swap is invisible to ToC + auditor | ☐ TODO (WIN) — `dev/audit_canonical_order.py` (encode the nav-83-vs-spine-86 demotion model). |
| **D9** | MED | WIN | fresh ethiopian `.kepub` inline `verse-notes` ids missing `-sN` tail; `_POPUP_ASIDE_RE` can pass vacuously if kepubify reorders attrs | ☐ TODO (WIN) — `dev/audit_kepub_revid_family.py` (bucket inline vs navigate ids on a FRESH `.kepub`). |

## Round-14 SETTLED → DEFERRED_BY_DESIGN (do NOT re-litigate)
A1 LF chokepoint · A2 single-pass `_apply_splices` (the OOM was largely the AppXSvc commit-leak) · G1–G5 + A4 built ·
survivors #1–#6 + the G5 over-cap fix. Earlier-settled (regression/bleed only): WS1 re-split, WS2 cascade, WS3
separators, eink font `!important`, page-break re-arch, poetry mid-verse KEPT.

## Lane division

| owner | dimensions | files |
|-------|-----------|-------|
| **WIN** | D4 ✅ · D2 ◐ · D5 · D8 · D9 + `audit_customize_flag_matrix.py` (D4 gate) + the G1 golden re-stamp for D3 | `scripts/build_edition.py` (WIN-exclusive), `scripts/check_xrefs.py`, `tests/golden/kjv_golden_hashes.json`, `dev/audit_canonical_order.py`, `dev/audit_kepub_revid_family.py`, `dev/audit_customize_flag_matrix.py`, `.claude/workflows/deep-audit.js` |
| **MAC** | D3 ✅ · D1 ✅(gate) · D6 · D7 + cross-OS verify every WIN build | `scripts/core/versification.py`, `content/translations/{douay-rheims,vulgate-clementine}/psa.py`, `dev/audit_versification_coverage.py`, `dev/audit_release_assets.py`, `dev/audit_canon_bookcount.py`, `dev/audit_migration_idempotence.py` |

## D3 detail — versification coverage (HIGH, build-free)

The exhaustive gate walks **every** source vpl coordinate (Douay `engDRA_vpl.txt` 35,811 v + Vulgate
`latVUC_vpl.txt` 35,809 v) through the real `vulgate_to_kjv` and flags any non-allowlisted `None`/out-of-extent.

- **Real defects (FIXED): exactly Ps 2:13 + Ps 4:10** — trailing folds of the closing clause of KJV Ps 2:12 / 4:8
  (`_LXX_PSALM_COUNTS[2]=12`/`[4]=9`, were absent from `_VULGATE_PSALM_FIXES`). The breadth find pass found 0 more.
- **By-design omits (allowlisted, documented in the gate):** 66 psalm superscriptions (62 v1 + 4 two-line v1+v2 for
  Ps 50/51/53/59 — verified psa 50:3 "Miserere mei, Deus" → KJV 51:1); Greek Additions to Esther (est 10:4–16:24,
  no `aes` parallel store, matches the LXX `_EST_OMIT`); **dan 14:42** (Vulgate-only closing decree — documented at
  `versification.py` `_vulgate_cross` ~L1445; **a naive fix would have corrupted bel 42 — caught by reading the code**);
  tob/jdt/sir (`_VULGATE_OMIT`).
- Post-fix gate exits 0 both translations (mapped_ok +2 each; `psa.py` diff confined). Removed 3 stale untracked douay
  `tob/jdt/sir` leftovers (identity coords from an old non-remap extraction; current remap omits them).

**⚠ CROSS-LANE — G1 golden re-stamp (WIN):** the `vulgate` popup → `vulgate-clementine` store, which **all 4 study
editions carry** (`popup_languages_default`), so D3 changes the built EPUB at Ps 2:12/4:8 for catholic-study /
evangelical-reformed / eastern-orthodox (the 3 G1 golden editions) + ethiopian. RATIFIED content restoration (plan-
approved) → re-stamp `tests/golden/kjv_golden_hashes.json` (same as the WS1 re-split). Expected built delta = ONLY the
Ps 2:12/4:8 `vulgate` popup. The `douay` store change is latent (no edition uses the `douay` popup). WIN: rebuild the
9 cells, confirm the confined delta, `G1 --regen`.

## D1 detail — release-asset integrity (HIGH, offline gate)

Gate run against LIVE v0.1.0: **187 attached = 180 grammar + 2 legacy + 4 platform (exe/AppImage/dmg/font-pack) + 1
meta**, bijection clean, **but 100 retired-SKU EPUBs attached** (anglican-bcp, coptic-orthodox, jewish-study,
lutheran-confessional, scholarly-academic × 4 fmt × 5 colour). `check_retired_edition_skus` is blind (repo-tree only).
**FIX = the v1.0.0 tag-time asset re-cut** (delete the 100 + their sums lines) — outward-facing, flagged for the user.

## Invariants
- 9-KJV byte-stable: the KJV scripture BODIES are untouched by every Mac dim. **D3 changes the `vulgate` popup at Ps
  2:12/4:8** in the study editions (the 3 G1 golden editions) — a RATIFIED restoration → G1 re-stamp (WIN). D4 (WIN) is
  unshipped-combo-only. No build-path import added by the Mac gates.
- Gates are standalone `dev/audit_*.py` with `--selftest` (non-tautological), mirroring G3/G4/G5; build-free ones wired
  into `tests/test_round15_source_gates.py` (per-push), exhaustive scans `slow`-marked.
- deep-audit/breadth engine edits stay LOCAL (the Mac breadth pass was a fresh inline Workflow, not a committed-engine
  edit → no commit hazard).

## Log
- **2026-06-26 kickoff (WIN)** — plan approved; program verified still-apt; D3/D4 confirmed live; round-14 settled on disk.
- **2026-06-26 D4 FIXED (WIN, `2afa6126`)** — `_cascade = s2_group`; RED→GREEN + 78 tests; byte-stable. D2 xref regex hardened.
- **2026-06-26 Mac breadth find pass** — fresh inline Workflow, 5 Mac dims, find→adversarially-verify: **0 new survivors**
  (every candidate refuted; confirms the pre-found defects + exhaustive gates are complete).
- **2026-06-26 D3 FIXED + D1 GATE (Mac, `29321fad`)** — Ps 2:13/4:10 fold; D3 + D1 gates built + selftested + wired;
  D1 live-confirmed 100 retired assets; 3 stale douay leftovers removed; `check_retired_edition_skus` exclusion. **WIN: re-stamp G1 golden for D3.**
- **2026-06-26 Mac D6/D7 IN PROGRESS** — building the canon-bookcount + migration-idempotence gates (+ 0001 torn-safe fix).
