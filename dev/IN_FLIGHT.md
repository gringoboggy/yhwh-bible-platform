# In-flight work — current task tracker

<!-- TRACKER-STATE: idle -->

## Active task

*(none — tracker is idle. Scope refresh + close-out shipped 2026-05-08:
SCOPE_2026-05-08.md and PLAN_2026-05-08.md are now the active master
docs; SCOPE_2026-05-07.md and PLAN_2026-05-07.md moved to dev/archive/;
CLAUDE_PROJECT_RULES §0 bootstrap protocol updated to point at the new
PLAN; lint_rules.py:check_doc_cross_references hardened to auto-discover
the latest PLAN_*.md (no more hardcoded date-stamped path); CHANGELOG
entry added; SESSION_STATE pointers refreshed. Linter back to 8/8;
393 tests still green. χ.7 Nave's Topical infrastructure shipped earlier
this session: schema (categories.yaml + kinds.yaml), loader
(NavesTopical), detector (NaveTopicalDetector + ALL_DETECTORS), driver
(run_naves_at_scale.py), fetcher (fetch_naves_topical with mirror-list
(NavesTopical), detector (NaveTopicalDetector + ALL_DETECTORS), driver
(run_naves_at_scale.py), fetcher (fetch_naves_topical with mirror-list
fallback), prospect.py resilience to SourceMissingError, and 16 new
tests — all 393 tests green, 8/8 linter clean. Source-data fetch
and promote are user-side: archive.org / openbible.info egress is
blocked from the development sandbox; the user runs fetch_sources.py
from a network env, or drops a pre-built naves_topical.json into
content/sources/. Once the source lands, run_naves_at_scale.py +
batch_promote_xrefs.py --kind topic-nave produce the +2-3K topic-nave
notes expected for χ.7.)*

## Pending follow-up (parked)

- **cleanup.py expansion** — should prune exports/, epub_working/,
  builds/, AND content/candidates/ (now ~1,355 files growing).
- **scaffolder integration test** — running --apply against a temp
  dir to catch indent-error class bugs.
- **UI defense prelude** in scaffolder — fold in automatically.
- **χ cluster continuation:**
  - χ.7 Nave's Topical (infra DONE; data fetch is user-side)
  - χ.1 Strong's Greek (Greek lexicon + GreekWordDetector + KJV NT reader)
  - χ.2-5 Commentaries (Henry, Calvin, Catena, Rashi)
- **§14 worked twice last session** (web.py split indent bug;
  HebrewWord cut-off). Document as §12 retrospective trigger
  candidate next time the rules doc is touched.
