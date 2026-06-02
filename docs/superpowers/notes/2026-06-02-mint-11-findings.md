# mint-11 deep-audit (round 4) — findings record · 2026-06-02

**Run:** `wf_4b250c81-348` / task `w2wxhtf4h` · engine `.claude/workflows/deep-audit.js`
(find → adversarially-verify → synthesize; 15 dims; find+verify pinned **sonnet**,
synth+completeness on inherited Opus). 95 agents · ~4.32M subagent tokens · ~3.9 h.
Round 4 (mint-8 = R1, mint-9 = R2, mint-10 = R3).

**Counts:** 64 deduped → **30 survived / 34 refuted**. By severity: medium 13 · low 14 ·
info 3. **No high/critical survivors** — the expected convergence signal after three prior
fix rounds.

**Artifacts:** raw result `notes/2026-06-02-mint-11-audit-raw.json`; phased fixes plan
`plans/2026-06-02-mint-11-fixes-plan.md` (indexed — the actionable list, with verifier-
corrected fixes).

---

## ⚠ Engine caveat — sonnet StructuredOutput failures (false-negative risk)

**21 of 95 agents completed WITHOUT calling the forced `StructuredOutput` tool** (sonnet
skips the forced-tool call more often than Opus — the cost of the cap=2 speed pinning). A
failed FINDER drops that angle's findings; a failed VERIFY panel leaves `panel.length == 0`
→ the engine's `refuted = panel.length === 0 ? true : …` rule **auto-refutes** it. So this
round's coverage was reduced, and **several findings were "refuted" only because their
verifier crashed, not because they are wrong.** The 30 survivors passed *real* verification
and are trustworthy. The empty-panel auto-refutes were re-triaged BY HAND this session
(below) — the genuine ones are promoted into the fixes plan.

### Empty-panel auto-refutes (panelSize = 0 — NOT genuine refutations; hand-triaged)
| sev | finding | hand-verdict |
|---|---|---|
| HIGH | `_iter_note_ref_traditions` / `_iter_note_ref_attribution_years` drop notes for books with neither `id_prefix` nor `bxx` | **re-verify** (relates to survivor #1) |
| HIGH | `build_cache` per-book cover bytes not in cache key (`cover_image_per_book` vs `book_covers`) | **re-verify** (stale-EPUB on cover change) |
| med | `run_kenyon` (+ the full 8-driver sweep) missing `coord_in_canonical_extent` | **promote** → Phase 3 class-sweep |
| med | `run_kenyon --books` legacy book-code alias silently excludes candidates | re-verify (bookcode cluster) |
| med | `translations.get_chapter()` TypeError on own-vers string verse labels (+ low `api_compare` `max()` mixed int/str) | re-verify (own-vers crash) |
| med | `check_render_coverage_no_regression` guard stale — 4 new stores unprotected | re-verify |
| med | `_canons_index` lru_cache not in audit_caches whitelist → preflight WARN | re-verify (mint-10 P6 added the cache) |
| med | `filter_books_for_canon` bare `write_text` — encoding unspecified on one branch | re-verify (build path) |
| low | `matrix_app.js` two `innerHTML` use unescaped `data.error` | re-verify (XSS site missed by mint-9/10) |
| low | `add_note.py` direct-write path has no verse-extent guard | promote → coord-guard class |
| low | `canonical_verse_counts.py` phantom lint-rule ref `check_canonical_skeleton_coverage` | re-verify (cheap doc fix) |
| info | build pipeline / vision-marathon CONFIRM-OPTIMAL | accept (no action) |

(Duplicates of survivors, already covered: filter_html O(N×N) = #26; render_coverage EN
dirs = #27; `_resolve_popup_languages` per-aside decode = deferred #12.)

### Genuinely refuted (a verifier actually read the code — trusted)
closure-capture in `filter_books_for_canon` (uses `fname` default args — not a bug);
negative `Content-Length` (the `> cap` check already rejects −1); 404 JSON path echo
(local single-user app, not disclosure); `inject.py` local ANSI constants (cosmetic);
`promote_candidate` chapter=0 fallback (chapter 0 not a valid coord); `run_kenyon`
re-index of existing IDs (normal-path safe); `discover_verses` first-gap stop (base HTML
is contiguous); unsorted `tmp.glob` in title-pages / main loop (no cross-file state →
byte-stable). These stay dropped.

---

## Survivors (30) — full detail + fixes in the plan
medium ×13, low ×14, info ×3. Grouped by the plan's phases:
- **Phase 0 (docs):** corpus count 67,715→91,733 (5 sites) · MATRIX_MAP line#s · Torrey 630→628 · REPO_MAP 182→184 tests / 27→28 plans.
- **Phase 1 (stale tests) ✅ DONE:** tau6x2 / tau7xi / tau7xt / tau7xu / render_coverage / test_scripts PublisherConsole — all 6 fixed, 200 green.
- **Phase 2 (test hardening):** test_mint9_phase1 silent-skip · test_inflight no-assert.
- **Phase 3 (additive guards):** run_xref coord guard + commit-time lint class-check · build_cache `+source_dates.py` · is_output_current +5 inputs.
- **Phase 4 (silent-data-loss/atomicity):** standalone_store atomic_write ×3 · promote within-batch dedup · notes_io None-vs-[] (3 targeted) · corpus_index fingerprint race.
- **Phase 5 (byte-stability latents):** topical.xhtml hashseed `sorted()` · build_cache popup-witness resolution (4/5 witnesses hash `<missing>`).
- **Phase 6 (behavior-changing):** annotation count override canon-scoped (catholic-study negative/understated count).
- **dead-code doc:** web_sources `_compute_attribution_audit_uncached` comment.

## Completeness gaps (10) — seed the next round's finder lenses
batch_promote_xrefs partial-batch status-write (silent corruption?) · the 8-driver
coord-guard sweep · config.py YAML parser round-trip fidelity (commas/quotes/`[]`) ·
build_merged_topic_index cross-launch PYTHONHASHSEED test · standalone_store
`lxx_psalms_to_kjv` seam boundaries · corpus_index rebuild() concurrency stress ·
`_patch_yaml_*` malformed/edge YAML · 8-field note count under real time-filter corpus ·
ALL_CHECKS==28 pin currency · `_append_cloned_edition` field completeness vs `_resolve_publishing`.

## Engine lesson for round 5 (deep-audit.js)
The 21/95 StructuredOutput failure rate is too high under sonnet. Options:
1. **Re-run a null verify panel once** before auto-refuting (cheap; biggest win).
2. A finding whose entire panel is null → mark **UNVERIFIED (carry to next round)**, not refuted.
3. Or pin VERIFY to Opus (keep FIND on sonnet) — verify panels are smaller, so the cost is bounded.
Recommend (1)+(2) — preserve the speed of sonnet finders but stop losing real findings to a tool-call miss.
