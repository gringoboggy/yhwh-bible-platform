# In-flight work — current task tracker

<!-- TRACKER-STATE: idle -->

## Active task

*(none — tracker is idle. ω.14 epubcheck preflight validation gate
shipped 2026-05-08: scripts/core/epubcheck.py wrapper +
_compute_preflight_uncached integration + 18 tests across 2 classes;
667 tests green, 10/10 linter clean. The W3C/IDPF EPUB validator is
now wired into the readiness dashboard. Java is missing on the
user's current machine, so the check degrades gracefully to a warn
with an install hint; once Java is installed (OpenJDK 8+) and a
real EPUB build runs, the check becomes a real shipping gate.

Next ψ-cluster batch is **ψ.8.2-B + ψ.8.3** — popup HTML redesign
(collapsible tradition stack with first-80-char preview) +
customize Traditions card UI (driven by the `traditions` registry
already exposed by api_customize_data). Spec at
dev/SCOPE_2026-05-08-addendum-cross-denom-compare.md.)*
`traditions_default` validator + customize API exposure +
`compute_tradition_disabled_html_ref_ids` build-pipeline filter
+ 16 tests; 649 tests green, 10/10 linter clean. Publishers can
now manually set `traditions_default` in editions.yaml and the
build pipeline silently filters non-matching notes from the EPUB.

Next ψ.8 sub-phase batch is **ψ.8.2-B + ψ.8.3** — popup HTML
redesign (collapsible tradition stack with first-80-char preview
per spec §"Build pipeline change") + customize Traditions card UI
(checkboxes driven by the `traditions` registry already exposed
by api_customize_data, plus the per-book override matrix
mirroring ν.2.7's pattern).

Spec at dev/SCOPE_2026-05-08-addendum-cross-denom-compare.md.)*

## Earlier idle context (kept for §14 audit reference)

ψ.8.0 tradition schema foundation shipped
2026-05-08: scripts/core/traditions.py + content/traditions.yaml +
scripts/backfill_traditions.py + 37 tests across 3 classes; 633 tests
green, 10/10 linter clean. The audit confirms all 15,925 existing
notes resolve to the default `cross` tradition — the `--apply`
rewriter is reserved for ψ.8.0.1 (lands when χ.2-χ.5 ship
tradition-tagged commentary content). Next ψ.8 sub-phase is the
**ψ.8.1 + ψ.8.2 + ψ.8.3 batch**: editions.yaml `traditions_default`
schema field + build-pipeline tradition stack in popup HTML +
customize Traditions card UI. Spec at
dev/SCOPE_2026-05-08-addendum-cross-denom-compare.md.)*
infrastructure shipped 2026-05-08: source loader, detector, at-scale
driver, +19 tests across 4 classes; 596 tests green, 10/10 linter
clean. Source-data fetch + batch promote are user-side, identical to
χ.7's contract — run `python scripts/fetch_sources.py` (or upload
JSON via `/sources`) to populate strongs_greek.json, then
`python scripts/run_greek_at_scale.py`, then
`python scripts/batch_promote_xrefs.py --kind lang-greek` for the
~5-10K corpus delta. Next pre-v1.0 platform phase per PLAN is **ψ.8
cross-denom compare apparatus** — the v1.0 differentiator;
~2-3 sessions; spec at
dev/SCOPE_2026-05-08-addendum-cross-denom-compare.md.)*
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
