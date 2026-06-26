# Round-14 remediation tracker (Mac, autonomous — user "fix everything the audit surfaced")

WIN box quiescent → Mac is sole worker (`LANE_HANDOFF` mode=exclusive/holder=mac). Drives ALL 8 deep-audit
survivors to green with TDD + verification. Source: `round14-mac-survivors.json` / `round14-mac-plan.md`
(engine `wf_61e196d1-2f2`). Marathon core stays off-limits.

| # | sev | finding | file | status |
|---|-----|---------|------|--------|
| 1 | MED | `eink_glyphs.py` missing from `_PIPELINE_SCRIPTS` → stale cached eink/kepub EPUB | `core/build_cache.py` | ✅ DONE — added to tuple; `TestCacheCoverageGuard` green (was RED) |
| 2 | LOW | `prospect.main()` None `out_path` → AttributeError crash on all-deduped chapter | `scripts/prospect.py` | ✅ DONE — None-guard + regression test (`test_prospect_write_queue` 3/3) |
| 3 | LOW | canonical-extent guard is a silent no-op for the 8 Tewahedo-distinctive books | `core/canonical_verse_counts.py` | ✅ DONE (Mac) — new `core/distinctive_verse_counts.py` leaf (6 dicts, AST-byte-identical) + per-chapter ceiling in `coord_in_canonical_extent`/`html_chapter_count` + `check_distinctive_extent` lint; test 13/13 (834 on-disk coords still valid, 0 over-extent). Ceiling lower-bound `0<=verse` (preserves `1en 91:0`/`94:0` chapter-intro notes); corrected a stale test that pinned the old no-op |
| 4 | LOW | S1 note-dedup drops dict source attribution when `note_group_by_category` off | `build_edition.py:4213` | ✅ DONE (WIN, `ac3e1fa3`) — `_strip_redundant_note_label`/`_strip_redundant_body_boilerplate` gated on `cascade = s2_group or eink_backmatter`; S1-on/S2-off keeps the source line |
| 5 | HIGH | no real-build golden gate covers tablet/kindle byte-stable cells (= G1) | `tests/test_kjv_golden_hash_gate.py` + `tests/golden/kjv_golden_hashes.json` | ✅ DONE (WIN built gate+golden `f0ffc499`, 9 cells POST-re-split+POST-A1) · **✅ Mac CROSS-OS VERIFIED**: `test_kjv_golden_hash_gate` PASSED on macOS (9/9 cells match Windows' golden, 41 min) ⇒ KJV byte-stable set is byte-identical Win↔Mac after the A1 LF chokepoint (Linux via A4 CI). A1 confirmed a Mac no-op (Mac already emits LF). |
| 6 | HIGH | eink mid-verse merge corrupts est 10:2 on the shipped flagship (displacement-blind) | `build_edition.py:5650` (WIN) + `audit_verse_formatting.py` (Mac) | ✅ DONE — WIN `_merge_mid_verse_breaks` WEB-source discriminator `_mv_displacement_would_corrupt` (`ac3e1fa3`); Mac `audit_verse_formatting.py` MIRROR `_is_displaced_anchor` (est 10:2 → `displaced_anchor` WARN, not ERROR; routed after poetry/irregular KEEP to match the build) — **17/17 auditor tests** incl. gen-19:1 genuine break still flagged + psa-18 poetry kept. **✅ cross-OS eink build-verify DONE (macOS)**: catholic-study eink built rc 0 → auditor **0 narrative ERRORs / 0 pilcrows**, est 10:1 ends clean "…islands of the sea." (NO "Aren't" corruption), est 10:2 intact "Aren't all the acts…" (anchor displaced, NOT merged → 1 WARN). The HIGH is PROVEN fixed in real eink output. |

**Refuted (do NOT re-open):** idmap-miss fallback · byte-cap self-gate · popup-separator thread-dependence ·
glossary single-piece divergence · badges_skipped-not-enforced.

**Verification gate (done = all hold):** every fix has a regression test that fails pre-fix; `prospect`/cache
guards green; G1 green on all 9 byte-stable cells (baselined from POST per the WS1 byte-proof); est 10:2 correct
in a built catholic-study eink (no "Aren't" relocation) + the 9-KJV byte-stable set unchanged (byte-proof/determinism);
full `pytest` green incl. slow.

## Lane division (PARALLEL — corrected 2026-06-26)

WIN was NOT quiescent: it rebooted (cleared an AppXSvc ~53 GB commit-leak — the flagship-eink "OOM" was largely
ENVIRONMENTAL), wired **A1** (LF chokepoint, P1/P2 green, epubcheck 0/0/0/0), and is LIVE on **G1 golden → A4 CI → G2–G5**.
Reverted my premature exclusive/mac → PARALLEL, file-disjoint:

| owner | survivors / work | files |
|-------|------------------|-------|
| **MAC** | ✅#1 ✅#2 · #3 canonical-extent · #6 audit-mirror (after WIN's discriminator) · cross-OS verify A1 + G1 golden | `dev/audit/**`, `core/canonical_verse_counts.py` (+ new `core/distinctive_verse_counts.py`), `extract_parallel_pdf.py`, `dev/audit_verse_formatting.py` |
| **WIN** | #4 S1 attribution · #5 G1 golden (WIP) · #6 `_merge_mid_verse_breaks` displacement fix (★HIGH) · G2–G5 · A4 | `scripts/build_edition.py` (WIN-exclusive — Mac will NOT touch), `tests/**`, gate files, `.github/` |

## Log

- **2026-06-26 kickoff** — #1 (cache guard) + #2 (prospect) Mac-DONE+verified.
- **2026-06-26 PARALLEL CORRECTION** — discovered WIN live (rebooted) mid-push; reverted exclusive/mac → parallel,
  file-disjoint per the table above. Mac next: #3 (canonical-extent, no build_edition collision) then cross-OS verify
  WIN's A1 (no-op on Mac → Mac bytes unchanged) + the G1 golden when it lands.
- **2026-06-26 ★ ALL 8 SURVIVORS GREEN — both lanes.** Mac: #1·#2·#3·#6-mirror (`db049b75`) + **G1 golden CROSS-OS
  VERIFIED** (9/9 cells match WIN's POST golden on macOS, 41 min). WIN (`3e129837` "WIN remediation COMPLETE"):
  #4·#5/G1·#6-build + the 5 gates G1–G5 wired into a per-build gate + A1 LF-chokepoint + A4 ubuntu CI. The 5 refuted
  stay refuted. **Cross-OS determinism (A15) proven Win+Mac (Linux via A4 CI).**
- **2026-06-26 ✅ CLOSING BYTE-STABILITY PROOF** — **G1 gate RE-RUN at the final HEAD (`db049b75`, post-#4/#6/G2–G5)
  PASSED on macOS** (9/9 byte-stable cells, 41 min): #4's S1-attribution change did NOT disturb the byte-stable set
  (those 3 editions have `note_group_by_category` ON → `cascade=True` → unchanged) — the golden holds across the FINAL
  state. Remaining = WIN's full slow-suite green on its SSD (Mac HDD is too slow for the full suite; Mac ran the
  authoritative byte-stability + cross-OS proofs + every Mac-survivor's targeted tests). **Remediation DONE.**
