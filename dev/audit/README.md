# `dev/audit/` — audit findings + remediation tracking

Durable, shareable output of the cross-lane audit program (so both boxes consume the same
findings). Distinct from the truth records: this holds **audit artifacts**, not live state.

## Round 10 (2026-06-22) — full-audit split run

The first clean product audit after the 2026-06-21 Grok-revert cleanup. Two complementary audits,
split across both machines, then remediate everything surfaced.

| File | Producer | Contents |
|---|---|---|
| `round10-win-survivors.json` | WIN (`deep-audit.js` LANE=win) | survivors + counts + completeness for the 6 compute-heavy dims |
| `round10-win-plan.md` | WIN | the WIN-lane `fixesPlanMarkdown` |
| `round10-mac-survivors.json` | Mac (`deep-audit.js` LANE=mac) | survivors + counts + completeness for the 18 read-only dims |
| `round10-mac-plan.md` | Mac | the MAC-lane `fixesPlanMarkdown` |
| `round10-structural-*.json` | WIN (`dev/audit_book_structure.py`) | per (edition × format × book) verse→chapter→book→out-of-book PASS/FAIL |
| `round10-remediation.md` | WIN | merged tracker: every finding → fix → verify → commit |

**Lane split** (`LANE_DIMS` in `deep-audit.js`, scope=product): WIN = tests-run, opt-build,
byte-stability, rx-surfaces, popup-integrity, platform-kobo. MAC = correctness, security,
code-debt, tests, docs, data-validity, concurrency-caching, cross-module, marathon-boundary,
dist-packaging, website-deploy, future-work, opt-vision, opt-ingest, opt-render, platform-apple,
platform-kindle, platform-play. Disjoint; together = all 24 product dims.
