# Round-14 remediation tracker (Mac, autonomous — user "fix everything the audit surfaced")

WIN box quiescent → Mac is sole worker (`LANE_HANDOFF` mode=exclusive/holder=mac). Drives ALL 8 deep-audit
survivors to green with TDD + verification. Source: `round14-mac-survivors.json` / `round14-mac-plan.md`
(engine `wf_61e196d1-2f2`). Marathon core stays off-limits.

| # | sev | finding | file | status |
|---|-----|---------|------|--------|
| 1 | MED | `eink_glyphs.py` missing from `_PIPELINE_SCRIPTS` → stale cached eink/kepub EPUB | `core/build_cache.py` | ✅ DONE — added to tuple; `TestCacheCoverageGuard` green (was RED) |
| 2 | LOW | `prospect.main()` None `out_path` → AttributeError crash on all-deduped chapter | `scripts/prospect.py` | ✅ DONE — None-guard + regression test (`test_prospect_write_queue` 3/3) |
| 3 | LOW | canonical-extent guard is a silent no-op for the 8 Tewahedo-distinctive books | `core/canonical_verse_counts.py` | ⏳ TODO — new dep-free leaf + per-chapter ceiling + lint |
| 4 | LOW | S1 note-dedup drops dict source attribution when `note_group_by_category` off | `build_edition.py:4213` | ⏳ TODO |
| 5 | HIGH | no real-build golden gate covers tablet/kindle byte-stable cells (= G1) | `tests/test_kjv_golden_hash_gate.py` (new) | ⏳ TODO — baseline from POST; 9 cells already built in byteproof-out |
| 6 | HIGH | eink mid-verse merge corrupts est 10:2 on the shipped flagship (displacement-blind) | `build_edition.py:5650` + `audit_verse_formatting.py` | ⏳ TODO — WEB-source discriminator + regression + catholic-study eink build verify |

**Refuted (do NOT re-open):** idmap-miss fallback · byte-cap self-gate · popup-separator thread-dependence ·
glossary single-piece divergence · badges_skipped-not-enforced.

**Verification gate (done = all hold):** every fix has a regression test that fails pre-fix; `prospect`/cache
guards green; G1 green on all 9 byte-stable cells (baselined from POST per the WS1 byte-proof); est 10:2 correct
in a built catholic-study eink (no "Aren't" relocation) + the 9-KJV byte-stable set unchanged (byte-proof/determinism);
full `pytest` green incl. slow.

## Log

- **2026-06-26** — kickoff. #1 (cache guard) + #2 (prospect) DONE+verified. Order next: #3, #4 (additive, no build),
  then #5 (G1 golden, reuse byteproof-out builds), then #6 (est 10:2 HIGH, needs eink build verify).
