export const meta = {
  name: 'deep-audit',
  description: 'Deep multi-agent audit: find -> adversarially verify -> synthesize (reusable, parameterized; carries prior-round memory + runs the test suite)',
  whenToUse: 'Run a deep, broad codebase audit to convergence. Args: {dimensions?, scope?, depth?:normal|deep, round?, repo?, now?, deferred?:string[], priorSurvivors?:string[]}. Each finding is independently refuted before it counts; settled/deferred-by-design items are fed in so they are not re-litigated; one dimension actually RUNS pytest. Used by the mint-N convergence loop. NOTE: if invoked by name and args do not propagate, the in-file ROUND/NOW/DEFERRED defaults are what run — bump them in-file (the startup log echoes argsRound to confirm).',
  phases: [
    { title: 'Find', detail: 'Per dimension (incl. a tests-run dimension that executes pytest), fan out read-only finder agents -> structured findings' },
    { title: 'Verify', detail: 'Per finding, adversarial skeptics prompted to REFUTE (default-refuted); a finding that re-raises a deferred-by-design item is refuted' },
    { title: 'Synthesize', detail: 'Dedup, severity-calibrate, phased fixes plan (with authoritative counts) + completeness critic' },
  ],
}

// ----------------------------------------------------------------------------
// Parameters (all overridable via args; defaults tuned for the mint-8 first run)
// ----------------------------------------------------------------------------
// ----- LANE (set THIS ONE line in-file per machine; args don't reliably propagate) -----
// CROSS-LANE PARITY IS BAKED IN (round 6): flipping LANE also auto-picks the right
// REPO path AND the right sub-agent types for that box — so each machine edits ONLY
// this line. (Round 5 needed 3 separate local edits — REPO + 2 agent types — which
// caused the split deep-audit to fail 15× on the Mac. Fixed: one knob.)
const LANE = args?.lane ?? 'all'  // 'win' | 'mac' | 'all'  ('all' = full set on the N95)
const REPO_BY_LANE = {
  win: 'C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4',
  mac: '/Volumes/MacHD2/yhwh-bible-platform',
}
// The Mac does NOT have the feature-dev:* sub-agents (only: claude, claude-code-guide,
// Explore, general-purpose, Plan, statusline-setup). Map review->general-purpose,
// architect->Plan there. 'all'/'win' use feature-dev:* on the N95.
const AGENTS_BY_LANE = {
  win: { review: 'feature-dev:code-reviewer', architect: 'feature-dev:code-architect', guard: 'Explore' },
  mac: { review: 'general-purpose', architect: 'Plan', guard: 'Explore' },
}
const _AG = AGENTS_BY_LANE[LANE === 'mac' ? 'mac' : 'win']
const REPO = args?.repo ?? (REPO_BY_LANE[LANE] ?? REPO_BY_LANE.win)  // ABSOLUTE — cwd-independent
const DEPTH = args?.depth ?? 'deep'               // 'deep' = multi-finder + scaled skeptic panels
// round 14 = the build-pipeline deep audit (the new eink page-break / glossary-streaming / WS1-3 /
// font re-arch + the resulting epubs; user directive 2026-06-25; program
// dev/audit/build-pipeline-deep-audit-program-2026-06-25.md). TARGET A (machinery) + propagation lens.
const ROUND = args?.round ?? 14            // args don't reliably propagate — bump in-file (round-14 build-pipeline audit)
const NOW = args?.now ?? '2026-06-25'             // Date.now() is unavailable in scripts; stamp via args
// SCOPE (user directive 2026-06-10, memory reference_deep_audit_tool): 'product' (default) = project
// code/product dims only; 'all' = the round-7 one-time everything-sweep (also runs claude-setup /
// lane-system / github-gitlab / stack-review / decommission). args don't reliably propagate — set in-file.
const SCOPE = args?.scope ?? 'product'

const rank = { critical: 4, high: 3, medium: 2, low: 1, info: 0, none: -1 }

// ----------------------------------------------------------------------------
// PRIOR-ROUND MEMORY (mint-9 engine upgrade — convergence loops must not
// re-litigate settled decisions). Two failure modes the first two rounds hit:
//   (1) deferred-BY-DESIGN items kept re-surfacing as "new" findings every round
//       (ex.py->exo, the aes ch11-16 residual, the declined compresslevel), and
//   (2) an incomplete fix re-surfaced because round-1 patched 1 of 2 sibling
//       sites and the finder only ever reported the single instance, not the class.
// Feed both as explicit context so verifiers down-rank settled items and finders
// sweep ALL sites of a pattern. Override via args.deferred / args.priorSurvivors.
// ----------------------------------------------------------------------------
const DEFERRED_BY_DESIGN = args?.deferred ?? [
  'ex.py -> exo.py rename for the 4 Tewahedo translation stores (geez/amharic + -en): DEFERRED to the tau.G standalone-build wiring. The data is latent (no live consumer until the standalone editions are wired). Do NOT propose the rename now; an additive _book_path alias is the only acceptable early action, and even that is optional. Re-flagging the rename as a NEW finding is wrong.',
  'aes (Esther-Greek-additions) notes at KJV chapters 11-16 are uninjectable because the base HTML only renders chapters 1-10: this is a PARKED known-residual (roadmap "Parked / known-residual"), editorial not mechanical, guarded by html_chapter_count at the promote boundary. Re-flagging it as a NEW bug is wrong.',
  'zip compresslevel 9->6: DECLINED on the merits (enlarges every EPUB 1-3% to save ~30s/build; quality output > build speed). Do NOT re-propose it.',
  'Splitting scripts/web.py or scripts/build_edition.py for size alone: DECLINED (large files of small cohesive functions). CSRF / rate-limiting / public-server hardening: OUT OF SCOPE (single-user local app).',
  'Book count is 83 (the shipped superset), NOT 87: the raw registry is 87 but 4 additions fold into Daniel/Esther (empty "Additions to Esther" dropped; paz/sus/bel demoted to inline appendix headings; per-edition eyebrow renumber). The 87->83 fold is a FEATURE (v0.0.3), not a defect — do NOT flag an "87 vs 83 mismatch".',
  'ONE Bible ships — the Ethiopian superset (user-directed, supersedes the old "2 EPUBs / catholic-study-as-2nd-Bible" idea). The Geez/Amharic STANDALONE Bibles are a FUTURE update, out of scope for this round. Do NOT flag a "missing 2nd Bible".',
  'The ~205 hidden orphan aes vnote-asides in index_split_028 are a KNOWN epubcheck-clean residual: the canon-splice leaves trailing shared-file asides that are invisible to readers. Do NOT re-flag as a new bug.',
  'The recurring book TITLE-PAGE misalignment (Kobo/Apple device-QA) is a KNOWN open item, but the CSS is ALREADY text-align:center everywhere — so do NOT propose a blind CSS re-centering (that "fix" has failed many times). It needs a RENDER-then-diagnose pass (screenshot the actual title page, find the one off element). Flag the offending element only if you can cite it from a render; otherwise leave it.',
  'The 117-chapter-start v1/v2 verse-anchor displacement in the base (psa 31, job 14, gen 2/11/32/37/43, …) is KNOWN and DESIGNED-FOR (docs/superpowers/notes/2026-06-10-verse-boundary-residual-design.md — WEB-fixture anchor source, v0.1.1, WIN executes). Do NOT re-flag it as a new finding.',
  'K-R4-1 (vnote/translation popup asides lack plain-text preview separators) and K-R4-2 (Kobo eInk preview declines asides over a stripped-text threshold, bracketed 3,313 < T <= 7,748 chars, navigate-fallback lands at file start) are KNOWN with a fix arc IN FLIGHT (docs/superpowers/notes/2026-06-10-kobo-round4-device-qa.md). The popup-integrity dimension must EXTEND beyond them (other aside kinds, other emitters, other hidden-target classes), never re-derive them as new findings.',
  'K-R13 (study-badge footnote targets + eink glyph substitutes + NAV+ pad) is SHIPPED and round-13 device-PASS (2026-06-15). K-R14 (vnote-kobo-sep preview gaps) and K-R15 (verse-line breaks / spine page-break coalesce / empty-verse prose repair) shipped 2026-06-15 — popup-integrity and rx-surfaces must hunt CROSS-EDITION BLEED and regressions, not re-litigate the fix arcs unless a NEW failure mode is evidenced.',
  'theta.4 (the launcher update-prompt feature) is DEFERRED to v0.1.1 by decision, not missing. The X/social posts are POSTED-BY-USER (drafts exist; not a gap). kepub cross-piece duplicate ids generated by kobtoSpan wrappers are excluded by design in the verifier.',
  // round-8 remediation survivors (CONFIRMED-KNOWN — round 9 must not re-open without NEW evidence):
  'S2 popup size census (eth 218 / catholic 184 asides >3,300 stripped chars under 7,748 ceiling): CONFIRMED-KNOWN @ round-8 — not a new emitter class.',
  'vnote-1ki-12-24 @ 6,937 stripped chars (K-R4-2): fix arc in flight — defer unless device QA proves new failure.',
  'Adjacent vnote prefix pair vnote-1en-100-1 < vnote-1en-100-11 on eth: corpus-wide translation-surface WARN, not FAIL.',
  'PLAYBOOK/RULES save doctrine + save-all.ps1 path: FIXED @ WIN turn 115 — re-flag only if drift returns.',
  'Book-code web/API normalization via config.resolve_book_code: SHIPPED @ WIN turn 115.',
  // Post-cleanup product residuals (the Grok-era "round 9" everything-sweep was discarded with the
  // 2026-06-21 cleanup; the meta/automation "deferrals" it added are gone — but these GENUINE PRODUCT
  // items it surfaced must not be re-litigated):
  'Catalog/doc count drift: the per-edition shipped numbers in REPO_MAP/MATRIX_MAP/SESSION_PLAYBOOK/build_edition comments lag the +72 restored comm/word notes (corpus now 91,712 in the superset). RECONCILIATION IS IN FLIGHT after the Mac rebuild (dev/IN_FLIGHT.md task 2 — the full count cascade: page/meta/og/social-card/repo-descriptions/EPUB-metadata/trackers). Fix is dev/ prose + metadata only (no engine change); do NOT re-flag as a new finding.',
  'K-R6-2 (rev-split id family): bare -sN ids + prefix swallows in rev sections were observed on the v0.1.0 epub AND kepub (792 bare rev ids + 36k+ prefixes on the .kepub) — rev sections not emitting proper -sN family ids post all transforms. A real defect class; triage artifact-age vs gate vs real regression before re-flagging, and do not re-derive the counts.',
  // ---- ROUND-14 settled / deferred-by-design (program dev/audit/build-pipeline-deep-audit-program-2026-06-25.md) ----
  'ROUND-14: WS1 mid-verse merge, the 158-verse re-split (USER-RATIFIED, commit 6b690361), WS2 cascade de-dup, WS3 popup separators, the eink font !important fix, and the page-break re-arch (Parts 1/2/2b) are SHIPPED + settled — audit for regression/bleed ONLY, never re-litigate the design or re-derive the original findings.',
  'ROUND-14: the remaining flagship-eink build OOM is WIN\'s ACTIVE fix (A2 single-pass _apply_splices already landed for apply_badge_markers:4444; the glossary byte-streaming deeper fix landed). This audit VERIFIES build feasibility + frees, it does NOT re-diagnose the OOM site.',
  'ROUND-14: the vnote translation-popup U+2028 separator sibling (~119k asides, guard #7) is a QUEUED follow-up, not a new finding — confirm in/out of scope, do not re-derive it.',
  'ROUND-14: the 1en 71/90 + 90:13-18 content defects and the char-vs-byte all-edition kepub re-cut are separately deferred (documented in dev/audit/).',
  'ROUND-14: poetry/wisdom mid-verse breaks are KEPT by user decision (_MIDVERSE_BREAK_KEEP_BOOKS / auditor POETRY_BOOKS WARN); flagging a kept poetry break as a bug is wrong.',
  'ROUND-14: do NOT defer "there is no KJV golden-hash gate" — gate G1 (test_kjv_golden_hash_gate.py + tests/golden/kjv_golden_hashes.json) is the round\'s HEADLINE deliverable that CLOSES it; surface any byte-stability/eink-gating leak it would catch as a real finding.',
]
const PRIOR_SURVIVOR_TITLES = args?.priorSurvivors ?? [  // round-13 fixes — confirm-not-regress (program priorSurvivors)
  'conftest _PROTECTED_DIRS guard',
  'zip ZipInfo.create_system=0 in all EPUB writers',
  'inject.escape_attr on the 4 title-attr sites',
  'frozen-app content_root() sys.frozen guard',
  'orphaned api/exports + api/preflight dir removal',
]

// ----------------------------------------------------------------------------
// Schemas (validated at the tool layer; the agent retries on mismatch)
// ----------------------------------------------------------------------------
const FINDINGS_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          severity: { type: 'string', enum: ['critical', 'high', 'medium', 'low', 'info'] },
          title: { type: 'string', description: 'One-line, specific.' },
          file: { type: 'string', description: 'Path under the repo root (e.g. scripts/web.py).' },
          line: { type: 'string', description: 'Line number or range, or "" if N/A.' },
          evidence: { type: 'string', description: 'A short quoted code snippet + why it is a defect. No hand-waving.' },
          fix: { type: 'string', description: 'A concrete, safe fix.' },
        },
        required: ['severity', 'title', 'file', 'line', 'evidence', 'fix'],
      },
    },
  },
  required: ['findings'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    refuted: { type: 'boolean', description: 'true = the finding is wrong/immaterial/already-handled/unconfirmable.' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    reasoning: { type: 'string', description: 'What you checked in the actual code, and the verdict basis.' },
    corrected_severity: { type: 'string', enum: ['critical', 'high', 'medium', 'low', 'info', 'none'] },
    corrected_fix: { type: 'string', description: 'A corrected fix if the finder fix is wrong/unsafe; else "".' },
  },
  required: ['refuted', 'confidence', 'reasoning', 'corrected_severity'],
}

const COMPLETENESS_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    gaps: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          area: { type: 'string', description: 'A subtree / module / invariant likely under-covered this round.' },
          why: { type: 'string' },
          suggested_lens: { type: 'string', description: 'A concrete finder lens for the next round.' },
        },
        required: ['area', 'why', 'suggested_lens'],
      },
    },
  },
  required: ['gaps'],
}

// ----------------------------------------------------------------------------
// Shared orientation preamble (every agent gets this)
// ----------------------------------------------------------------------------
const PREAMBLE = `You are auditing the YHWH v2.4 Bible-publishing platform. The repo root is "${REPO}/" relative to your working directory; ALL file paths you cite must be under it (e.g. ${REPO}/scripts/web.py). Read files yourself; do not guess.

Fast orientation (read what you need):
- ${REPO}/dev/MATRIX_MAP.md   = data-flow map (config -> loaders -> matrix/build/inject -> consumers) + the base-HTML structure. Use this to find where things live; never grep blind.
- ${REPO}/dev/REPO_MAP.md     = file/folder index.
- ${REPO}/dev/CLAUDE_PROJECT_RULES.md = conventions (S7 code: lru_cache discipline, ast.literal_eval-not-exec, atomic writes; S6 UI: canonical book/chapter order; S8 tests; S9 mental models).
- ${REPO}/dev/SESSION_STATE.md = current snapshot (read it for what just shipped; this is deep-audit round ${ROUND}).

ALREADY-SETTLED / DEFERRED-BY-DESIGN (round ${ROUND} runs AFTER prior rounds' fixes — do NOT re-report these as new findings; a verifier MUST refute a finding that merely re-raises one of them):
${DEFERRED_BY_DESIGN.map((d, i) => `  ${i + 1}. ${d}`).join('\n')}
${PRIOR_SURVIVOR_TITLES.length ? `Prior-round findings already FIXED (confirm the fix held; only report a REGRESSION, not the original):\n${PRIOR_SURVIVOR_TITLES.map((t) => `  - ${t}`).join('\n')}\n` : ''}
PROJECT FACTS (so you do not mis-flag intended design):
- Single-user LOCAL desktop app. OUT OF SCOPE (do NOT flag): CSRF, rate-limiting, public-server / hosting hardening, multi-tenant auth.
- KEEP PYTHON; NO database (data-as-Python-tuples is deliberate); do NOT propose splitting scripts/web.py or scripts/build_edition.py for size alone (large files of small cohesive functions).
- Voyage-embeddings INTEGRATION is dropped (only key-rotation security survives). Commercial surfaces were already removed.
- The 9 KJV editions MUST build byte-stable; schema changes must be additive (byte-identical when unset); writes go through notes_io.atomic_write / ensure_backup.
- SHIPPED STATE (v0.1.0, 2026-06-10, github.com/gringoboggy/yhwh-bible-platform/releases/tag/v0.1.0 published+latest): the full-notes Ethiopian Bible (91,553 notes — the shipped post-consolidation count; use THIS number, not 91,733) as EPUB + kepub, Win exe (Azure-signed) + macOS dmg (notarized) + Linux AppImage + the Kobo font pack + SHA256SUMS, and the website DEPLOYED (counts streamlined to 91,553). Book count is 83 (the superset; raw registry 87, 4 fold into Daniel/Esther — never flag 83-vs-87). ONE Bible ships (Ethiopian superset); the Geez/Amharic standalones are a FUTURE update (out of scope). "deploy" = REBUILD from source THEN publish (a stale-artifact ship is a real defect — see the dist-packaging dim).
- SAVE CADENCE (RULES s4, 2026-06-08): fixes land as LOCAL COMMITS; the full 5-leg push happens only at a milestone. This audit is FINDINGS-ONLY — produce the plan, do NOT apply fixes.

OFF-LIMITS MARATHON CORE (read-only context — never propose edits that touch these; flagging them as a *defect* is itself out of scope unless it is an outright crash):
  scripts/build_standalone.py, scripts/core/manuscript_*.py, scripts/core/po_vision_store.py,
  content/manuscript/**, content/translations/sources/patrologia/**, GAPS/.

SWEEP THE WHOLE CLASS, NOT ONE SITE (load-bearing — a prior round shipped an incomplete fix because a finder reported ONE of two identical sites): when you find a defect that follows a PATTERN (a missing guard, a wrong key, a missing kwarg, a bad regex, an un-escaped interpolation), grep the repo for EVERY other occurrence of that same pattern and either fold them into ONE finding listing all sites, or file one finding per site. Never report just the first instance and stop. State in the evidence how many sites you checked and which.

OUTPUT DISCIPLINE: report only MATERIAL findings; do not pad with style nits or restate the de-scoped / already-settled items above. Every finding needs file + line + a quoted snippet as evidence and a concrete fix. Prefer fewer, real, high-confidence findings over a long shallow list.`

// ----------------------------------------------------------------------------
// Dimensions (the default mint-8 set; override via args.dimensions)
// kind: 'find' (bug hunt) | 'optimization' (approach re-evaluation) | 'guard' (boundary check)
// ----------------------------------------------------------------------------
const DEFAULT_DIMENSIONS = [
  {
    // mint-9 engine upgrade: ACTUALLY RUN THE TESTS. Rounds 1-2 each shipped a
    // STALE test that a single pytest run would have caught (a guard scanning a
    // file for a literal that had moved; a test reading the live CHANGELOG after
    // a month-roll). Source-reading finders can't see a red test — execute them.
    // round-7: moved to the ARRAY HEAD so pytest (here) and the build-heavy
    // rx-surfaces dim (late in the array) never overlap at cap=2 (the
    // never-pytest-beside-a-build rule).
    key: 'tests-run', kind: 'guard', finders: 1,
    prompt: `EXECUTE THE TEST SUITE (not a source read — actually run pytest) and report every FAILURE or ERROR as a finding. This catches stale/broken tests that source-scanning misses (e.g. a guard that scans a file for a literal that moved during a refactor; a test asserting on a doc that was month-rolled).

Run from the repo with the project's interpreter + env. Use Bash, one shard at a time to stay under memory limits (RULES: PYTHONUTF8=1, full pythoncore path, --basetemp under %LOCALAPPDATA%). Suggested fast pass (deselect the slow build tests):
  cd "${REPO}"; set PYTHONUTF8=1; set PYTHONPATH=<repo abs path>
  <pythoncore>/python.exe -m pytest tests/ -q -p no:cacheprovider -m "not slow" -x --basetemp="C:/Users/bogda/AppData/Local/Temp/yhwh-pytest/audit" 2>&1 | tail -40
If a single -x run trips early, note the failure, then continue the rest with --deselect or by running the remaining files so you surface ALL failures, not just the first. (If the environment cannot run pytest at all, say so in ONE finding and stop — do not fabricate pass/fail.)

For EACH failing/erroring test produce a finding: severity = high if it indicates a real code regression, medium if it is a STALE test (assertion drifted from reality — the code is right, the test is wrong), low for a flaky/env issue; file = the test file:line; evidence = the assertion + the actual vs expected; fix = correct the code OR update the stale test (say which). If the whole suite passes, return an EMPTY findings list (that is the success signal for this dimension).`,
  },
  {
    key: 'correctness', kind: 'find', finders: 2,
    prompt: `DIMENSION: CORRECTNESS. Hunt for logic defects in the Python under ${REPO}/scripts/ (excluding the off-limits core). Focus: silent-drop / data-loss paths (data dropped without error — e.g. book-code normalization dropping notes, candidate coords silently skipped), swallowed exceptions (except: pass / bare except), off-by-one + boundary conditions, wrong default values that change behavior, incorrect error handling, mutation of shared/cached state, dict/order assumptions. Start from MATRIX_MAP, then the high-traffic modules: scripts/web.py, scripts/build_edition.py, scripts/inject.py, scripts/core/*.py, scripts/run_*_at_scale.py, scripts/promote.py, scripts/prospect.py. Trace a few real end-to-end paths.`,
    angles: ['Emphasize off-by-one, boundary conditions, and wrong-default behavior changes.', 'Emphasize silent-drop / swallowed-exception / data-loss paths and shared-state mutation.'],
  },
  {
    key: 'security', kind: 'find', finders: 2,
    prompt: `DIMENSION: SECURITY (single-user LOCAL app). Focus: (a) stored-XSS / HTML injection — any path interpolating note/verse/user text into rendered HTML without sanitize_html or escaping; scrutinize the is_trusted_html boundary in scripts/core/popup_versions.py and the sample/preview renderers; (b) ast.literal_eval-not-exec discipline for all data-file loading; (c) path-traversal on file-serving + upload routes (_send_file, /content/covers, build downloads, the distribution console); (d) secret handling — auth.json, the Voyage key (committed? logged? in audit_log positional args?); (e) the download MIME allowlist + Content-Length caps; (f) SSRF in scripts/core/http.py (scheme allowlist, file:// LFI). Re-verify the mint-7 fixes still hold. Do NOT flag CSRF/rate-limit/hosting.`,
    angles: ['Emphasize stored-XSS / HTML-injection / template-escaping and the is_trusted_html boundary.', 'Emphasize secrets, path-traversal, upload validation, SSRF, and the download allowlist.'],
  },
  {
    key: 'code-debt', kind: 'find', finders: 1,
    prompt: `DIMENSION: CODE-DEBT / DEAD CODE. Find genuine duplication not yet deduped (post core/at_scale_base.py), orphaned/dead helpers, dead branches, copy-paste clones across the at-scale drivers and commentary loaders, inconsistent API error envelopes (handlers bypassing _send_json), and not-yet-wired functions. Check scripts/web.py, scripts/build_edition.py, scripts/core/sources.py, scripts/run_*_at_scale.py. Do NOT flag large-but-cohesive file size (web.py/build_edition.py are intentionally large).`,
  },
  {
    key: 'tests', kind: 'find', finders: 1,
    prompt: `DIMENSION: TESTS. Find: (a) guard tests that would NOT actually fail on the pre-fix/broken state (tautological guards) — verify each load-bearing guard truly catches its target; (b) coverage gaps on load-bearing paths (inject, build resolver, promote canonical-coord guard, sanitize_html); (c) tests that assume a default world-state instead of parsing it (RULES S8 state-aware rule); (d) share-based pins that should be absolute-count milestones (RULES S8.1); (e) missing meta-tests. Check ${REPO}/tests/. For each, state the specific mutation that should make the guard fail but might not.`,
  },
  {
    key: 'docs', kind: 'find', finders: 1,
    prompt: `DIMENSION: DOCS / DATA-HYGIENE DRIFT. Find stale refs / dead pointers and doc-vs-code drift the linter cannot catch semantically: dev/*.md + docs/superpowers/** + module docstrings referencing removed modules, renamed files, or wrong counts (console inventory — verify against CONSOLES in scripts/web.py; kinds/editions counts; the lint registry — verify count via ALL_CHECKS in scripts/lint_rules.py; note count = 91,553 shipped); archived-file pointers that 404; MATRIX_MAP / REPO_MAP semantic currency vs the actual tree. Cite the stale line and the correct value.`,
  },
  {
    key: 'byte-stability', kind: 'find', finders: 2,
    prompt: `DIMENSION: BYTE-STABILITY / BUILD-EPUB INTEGRITY. The 9 KJV editions MUST build byte-stable + reproducible. Find: (a) matrix==build resolver DIVERGENCE — any per-edition control (enabled kinds, popup langs, theme, canon filter) whose value is computed differently in the matrix view vs the build path instead of flowing through ONE shared resolver (see MATRIX_MAP); (b) build NON-DETERMINISM — unsorted dict/set iteration, hash-seed dependence, embedded timestamps, filesystem-order globbing, or any ordering that could make two builds of the same edition differ byte-wise; (c) base-invariant gaps — places that mutate epub_working/ without the nested-anchor guard (test_nested_anchors / check_nested_anchors). Read scripts/build_edition.py + scripts/core/matrix.py + the resolver MATRIX_MAP names.`,
    angles: ['Emphasize matrix-vs-build resolver divergence (per-edition controls computed in two places).', 'Emphasize build nondeterminism: set/dict ordering, hash seeding, timestamps, glob order.'],
  },
  {
    key: 'data-validity', kind: 'find', finders: 1,
    prompt: `DIMENSION: DATA-COORDINATE VALIDITY. Find: (a) out-of-extent coordinate artifacts — impossible chapter/verse numbers in content/candidates/** or content/notes/** (the *_ch_08x / >max-chapter class mint-7 A4 only swept for ezk/jol/nam — sweep ALL books using scripts/core/canonical_verse_counts.py); (b) any promote/ingest boundary that does NOT call coord_in_canonical_extent (find the boundary, prove the guard is present or missing); (c) non-canonical book codes in any notes/candidate filename or payload; (d) verse-count parity issues for the standalone Ge'ez Bible. Report the specific bad coordinate(s) found.`,
  },
  {
    key: 'concurrency-caching', kind: 'find', finders: 1,
    prompt: `DIMENSION: CONCURRENCY / CACHING CONTRACTS. Verify RULES S7.1: user-editable runtime data (notes, translations) must use the mtime-keyed lru_cache pattern (auto-invalidate on disk edit); project-internal published data uses @lru_cache(maxsize=1) singletons. Find any loader on the WRONG side (a maxsize=1 cache over a file edited at runtime; or an unbounded/keyless cache that should be mtime-keyed). Also: the Delta-family index correctness (rebuild lock / TTL fingerprint / per-worker storage / notes_io invalidation hook); pytest fixtures that mutate singleton caches without cache_clear(); every subprocess.run missing stdin=subprocess.DEVNULL (Windows WinError 6); xdist --dist=loadfile race safety.`,
  },
  {
    key: 'cross-module', kind: 'find', finders: 2,
    prompt: `DIMENSION: CROSS-MODULE INVARIANTS. Find violations of project-wide invariants: (a) BOOK-CODE canonicalization — re-verify the mint-7 bookcode_canonical lint holds across ANY map; hunt for a NEW or missed legacy alias (php/jas/jol/ezk/nam/joh/mar/ps) in any detector, loader, renderer, or xref map that would route to a non-existent notes file or drop notes; (b) the enabled-kinds 3-way divergence (MATRIX_MAP debt #1 — is it still diverging across the three enablement surfaces?); (c) the patristic-voice composition invariant (Cyril remains plurality-leader; guarded by test_cyril_remains_plurality_leader); (d) canonical book/chapter order everywhere (RULES S6.1) — any UI/encoder sorting books alphabetically/by-count instead of content/books.yaml order.`,
    angles: ['Emphasize book-code canonicalization (any missed legacy-alias map) and canonical book/chapter ordering.', 'Emphasize the enabled-kinds 3-way divergence, the patristic-voice invariant, and the single per-edition resolver.'],
  },
  {
    key: 'marathon-boundary', kind: 'guard', finders: 1,
    prompt: `GUARD CHECK (not a bug hunt). Verify the off-limits Ge'ez marathon core was NOT altered by the recent mint cleanup/audit commits. Off-limits: scripts/build_standalone.py, scripts/core/manuscript_*.py, scripts/core/po_vision_store.py, content/manuscript/**, content/translations/sources/patrologia/**, GAPS/. Use Bash: run "git -C '${REPO}' log --oneline -25 -- <each path>" and "git -C '${REPO}' status". Report a finding ONLY if a recent mint/audit commit touched the core unexpectedly OR the core has an outright internal inconsistency (e.g. a crash). Otherwise return an EMPTY findings list.`,
  },
  {
    // round 5 (2026-06-05): the code shipped AFTER mint-11 — the dims above predate it and only UNDER-cover it.
    key: 'rx-surfaces', kind: 'find', finders: 2,
    prompt: `DIMENSION: RX / RE-INGEST SURFACES (code shipped AFTER mint-11; the other dims predate it). Audit the build-time post-passes + the auto-note re-ingest for silent data-loss / corruption / injection. In ${REPO}/scripts/build_edition.py read: apply_file_split (~2277 — splits index_split_*.html into ~0.4 MB pieces, rewrites ~39.5 K cross-piece hrefs, regenerates OPF manifest+spine + nav.xhtml + toc.ncx) — CHECK every cross-piece href + badge->footnote target still resolves (a wrong-offset/dropped href = a dead link only seen on a real e-reader), every cut is well-formed (the stack-aware reopen/close), and no piece is orphaned from the spine; apply_badge_markers (~1797 — collapses a verse's note-ref markers into ONE verse-notes-badge + MERGES that verse's asides into one <aside class=verse-notes>) — CHECK badge count == pre-collapse marker count (no note dropped/reordered) and the merged aside markup is built WITHOUT unescaped note-text interpolation (stored-XSS); enrich_nav_chapters (~2730 — nests chapter <ol> in nav.xhtml + child navPoints in toc.ncx) — CHECK it runs LAST among the nav passes (a NAV-011 out-of-spine-order bug was already caught here) + gapless playOrder; apply_reader_toc_transforms (~2610). Font embed (style_config.EMBED_FONT_PATHS + patch_opf_fonts in BOTH build_edition.py and build_standalone.py) — CHECK every @font-face url() is OPF-declared (else epubcheck undeclared-resource) and the src is not an injection vector. Scaffold-strip (the <em>[Reviewer:]</em> removal + the check_no_reviewer_scaffolding lint) — CHECK the strip regex is not over-greedy (could eat real body). The dict-easton re-ingest (scripts/_reingest_eastons.py + scripts/extract_eastons_ccel.py + the new check_no_truncated_easton guard + tests/test_easton_reingest.py) — CHECK the full-article bodies are XHTML-escaped (a literal < or > already broke epubcheck in 2 entries), the exact-old-body pairing rewrote the RIGHT note, and the truncation guard actually fails on a truncated body. EXTEND the re-ingest checks beyond dict-easton to the lang-greek (Theós/Phōs head-drop + paren-imbalance) + topic-torrey (ref-dump leak) + topic-nave re-ingests, and confirm each lint guard (greek_gloss_quality, no_torrey_topic_leak, check_no_truncated_easton) actually FAILS on its defect (not tautological). ALSO audit the v0.0.3 post-passes shipped AFTER round 5 (search build_edition.py by function name — line numbers have drifted): apply_superscriptions (Psalm/incipit superscription wrapping — CHECK no verse text dropped or duplicated); apply_appendix_demotion_and_renumber (drops empty "Additions to Esther" from every canon, demotes Daniel additions paz/sus/bel to inline appendix headings, per-edition "BOOK <roman>" eyebrow renumber to 83 books — CHECK the renumber is GAPLESS on a CANON-FILTERED edition and no book is lost/duplicated); the cross-verse DEDUP of byte-identical note bodies per book (CHECK it removes only TRUE byte-identical duplicates, never a distinct note); the alt-book-name (", or …") removal in books.yaml + base HTML (CHECK no anchor/id/href broke). These passes act on the BUILT EPUB — prefer BUILDING eth + catholic-study (canon-filtered, per the gate-caught canon bug) and inspecting (epubcheck + a cross-piece link scan), not just source-reading. NOTE: this dimension is LOCAL-BUILD-heavy -> it runs on the N95 (SSD) lane.`,
    angles: ['Emphasize the file-splitter: cross-piece href integrity + well-formed cuts + spine completeness (silent dead-link data-loss).', 'Emphasize badge-merge note-conservation + unescaped-interpolation XSS, font @font-face OPF-declaration, and the dict-easton re-ingest XHTML-escape + body pairing.'],
  },
  {
    // round 6 (2026-06-08): the desktop builders + release pipeline shipped for v0.0.x — no prior dim covers them. READ-ONLY review (do NOT run builds); mac lane.
    key: 'dist-packaging', kind: 'find', finders: 1,
    prompt: `DIMENSION: DISTRIBUTION / PACKAGING (the desktop builders + release pipeline; shipped for v0.0.x — the other dims predate it). READ-ONLY review — do NOT run a build. Hunt for: (a) VERSION DRIFT + STALE-ARTIFACT ships — the user's rule is "deploy" = REBUILD from source THEN publish; a builder that bundles a stale \`editions.yaml\`/\`VERSION\` ships the wrong Bibles. CHECK \`VERSION\` (currently 0.1.0) is read consistently by every builder and the bundled \`content/editions.yaml\` is the FULL-notes one; no hard-coded stale version string. v0.1.0 shipped SIX asset families (epub, kepub, Win exe, dmg, AppImage via build-linux.yml, font pack) + SHA256SUMS — check the checksum merge covers ALL of them. (b) SECRET LEAKAGE in build scripts — \`dev/sign_windows.ps1\` (Azure Trusted Signing: the data-plane role + \`-ObjectId\` usage; no signing secret / token committed or echoed), \`dev/build_dmg.sh\` (notarization creds via keychain/env, never inline; staple step present), the macOS identity. (c) CHECKSUM / RELEASE-MERGE correctness — the \`SHA256SUMS.txt\` merge step (\`gen_checksums\`) lists EVERY shipped asset and is re-uploaded \`--clobber\`; the launcher's pywebview/\`webview\` import stays \`try/except\` so a headless CI build still works (\`.github/workflows/build-linux.yml\` AppImage). Read \`dev/launcher.spec\`, the launcher entry, \`dev/sign_windows.ps1\`, \`dev/build_dmg.sh\`, \`.github/workflows/build-linux.yml\`. Report drift / stale-ship / secret findings with file:line.`,
  },
  {
    // round 6 (2026-06-08): the public website + progress generator shipped for launch — READ-ONLY review; mac lane.
    key: 'website-deploy', kind: 'find', finders: 1,
    prompt: `DIMENSION: WEBSITE / PUBLIC SURFACE (\`website/**\` + the progress generator; shipped for the public launch). READ-ONLY review. Hunt for: (a) the "sources are NOT missing" DISPLAY guard (RULES guard #2) — \`scripts/gen_website_progress.py\` must NEVER show a book as "not started" / un-sourced (the floor is "source in hand"); the EN-flag must require >=50 real verse rows + a transcribed/ready stage (a stub back-translation must NOT light up EN); the 83-book superset must exclude the 4 folded books via \`_SUPERSET_EXCLUDE\` (NEVER surface 87). (b) STALE / BROKEN download links + checksums in \`website/src/releases.html\` + \`releases.js\` (every asset link resolves; \`SHA256SUMS.txt\` referenced; no \`is-pending\` placeholder left live; no "Windows follows shortly"/"coming soon"/stale-version copy now that all 3 platforms ship). (c) the 83-book count is consistent across the page body + \`<meta>\`/\`og:\`/\`twitter:\` description tags + the social card (\`brand/sources/card.html\` -> \`social-card.png\`) per the RULES "a claim/count lives in MORE than the page HTML" corollary. (d) \`website/build.mjs\` partial-injection correctness (no unescaped interpolation; every page built). Report with file:line; cite the stale value + the correct one.`,
  },
  // ---- ROUND-7 PROGRAM DIMENSIONS (the post-v0.1.0 everything-audit: Claude setup,
  //      lane system, GitHub/GitLab, popup integrity, decommission; user directive
  //      memory project_full_final_audit_program) ----
  {
    key: 'claude-setup', kind: 'find', finders: 2,
    prompt: `DIMENSION: CLAUDE OPERATING SETUP (out-of-repo + in-repo — the autonomous-system audit; feeds the Fable-5 system-mint redesign). Audit these surfaces (absolute paths; Read them yourself):
- C:/Users/bogda/.claude/settings.json (+ settings.local.json if present), C:/Users/bogda/.claude/keybindings.json, the hooks it wires;
- the project memory: C:/Users/bogda/.claude/projects/C--Users-bogda-Documents-YHWH-v2-4-full/memory/MEMORY.md + the topic files in that folder;
- the repo's .claude/: settings.json, hooks/ (bootstrap-triad.ps1 etc.), workflows/ (this engine + any others);
- the every-session reads: ${REPO}/dev/CLAUDE_PROJECT_RULES.md, ${REPO}/dev/SESSION_PLAYBOOK.md, ${REPO}/dev/SESSION_STATE.md (top), ${REPO}/dev/IN_FLIGHT.md (top), the .remember/ handoff system at C:/Users/bogda/Documents/YHWH-v2.4-full/.remember/.
Hunt for: (a) RULE DUPLICATION — the same rule stated in 2+ homes (RULES vs PLAYBOOK vs memory topic files vs LANE_HANDOFF boards) where the copies have DRIFTED or could drift (cite both homes + the divergence); (b) CONTRADICTIONS — two rules/doctrines that conflict (cite both); (c) TOKEN BLOAT in every-session reads — sections of the triad/hooks output that are history rather than live instruction and should move to dev/archive/ (the triad is ~700-900 lines BY DESIGN, so flag only genuinely dead/duplicated weight, with byte estimates); (d) HOOK CORRECTNESS — stale file names, broken paths, hooks that no-op silently, SessionStart output that misstates the live state; (e) SETUP SECURITY — secrets or tokens in settings/hooks/memory files (report PRESENCE + LOCATION ONLY — never quote a secret value into a finding), overly broad permission allowlists, hooks executing untrusted input. Do NOT flag the existence of the memory/hook system itself (it is deliberate); flag defects IN it.`,
    angles: ['Emphasize duplication + contradiction across RULES/PLAYBOOK/memory/boards, with the exact divergent passages cited.', 'Emphasize hook correctness, every-session token weight (with byte estimates), and setup security (presence-only secret reporting).'],
  },
  {
    key: 'lane-system', kind: 'find', finders: 1,
    prompt: `DIMENSION: TWO-LANE SYSTEM MECHANICS (the win+mac parallel-lane machinery). Read: ${REPO}/dev/LANE_HANDOFF.md (frontmatter contract: mode/holder/truth_owner + per-lane tasks), ${REPO}/scripts/lane_handoff.py, ${REPO}/scripts/lane_ping.py, ${REPO}/save-all.ps1 + ${REPO}/save.ps1 (the 5-leg save), docs/superpowers/specs/2026-06-08-lane-coordination-v2-design.md. Hunt for: (a) FAILURE MODES the mechanics don't handle — e.g. both lanes pushing between ping and push (TOCTOU), a truth_owner editing while the other lane holds unpushed truth-record edits, a stale board entry steering a fresh session wrong, save-all leg failures that report success; (b) spec-vs-implementation drift (the design doc says X, the script does Y — cite both); (c) redundancy/contradiction between the board protocol and RULES section 4; (d) the per-box memory mirroring discipline — is there a mechanism ensuring a cross-lane rule actually lands in BOTH boxes' memories, or is it best-effort prose? (e) bundle-leg hygiene (E:/F: naming, verify step, unmounted-drive behavior). Findings need file:line + the concrete failure scenario.`,
  },
  {
    key: 'github-gitlab', kind: 'find', finders: 1,
    prompt: `DIMENSION: GITHUB/GITLAB REPO POSTURE (read-only; findings-only — do NOT change any setting). Use Bash with the gh CLI (authed) + git: \`git -C "${REPO}" remote -v\`, \`git -C "${REPO}" ls-remote origin\` vs \`ls-remote github\` (mirror divergence), \`gh repo view gringoboggy/yhwh-bible-platform --json description,homepageUrl,hasIssuesEnabled,defaultBranchRef,licenseInfo\`, \`gh release view v0.1.0 --json assets,body\`, \`gh api repos/gringoboggy/yhwh-bible-platform/contents\` (top-level visible files), \`gh run list --workflow=build-linux.yml --limit 3\`. Hunt for: (a) release-asset gaps — every asset the release body/website names must exist on the release, SHA256SUMS must cover all of them (cross-check names + the AppImage self-merge landed); (b) description/count drift (91,553 notes / 83 books / no stale version) on BOTH hosts (GitLab checks limited to what git remote allows — flag anything API-gated as a finding routed to the Chrome-MCP account-settings task, memory project_github_gitlab_account_settings); (c) repo-visible files: README/CHANGELOG/LICENSE present + current at the repo root as seen by a visitor; (d) CI hygiene in .github/workflows/* (pinned actions, no secrets echoed, failure visibility); (e) mirror tip divergence origin vs github. Cite the exact command output that evidences each finding.`,
  },
  {
    key: 'popup-integrity', kind: 'find', finders: 2,
    prompt: `DIMENSION: POPUP / ASIDE INTEGRITY — the K-R4 "nowhere else" class sweeps (prior art: ${REPO}/docs/superpowers/notes/2026-06-10-kobo-round4-device-qa.md — READ IT FIRST; do NOT re-derive K-R4-1/K-R4-2 themselves, EXTEND beyond them). The shipped artifacts to inspect: ${REPO}/dist/YHWH-Ethiopian-Bible-v0.1.0.epub and .kepub.epub. You may run Python zip-scans via Bash (interpreter: py -3 with $env:PYTHONUTF8="1").
Sweep THREE classes across EVERY aside/popup kind (study merged asides, vnote translation popups, the category-legend popup, topical.xhtml popups, reference tables, any other epub:type="footnote" emitter you find in ${REPO}/scripts/build_edition.py + the popup generators):
(S1) SEPARATOR coverage — which emitters bake plain-text .vn-sep separators and which do not (the Kobo eInk preview is tag-stripped plain text; any emitter without text-level separators renders run-on there). The study cascade has them (K-R3-2); vnote does not (K-R4-1, fix in flight) — find any OTHERS.
(S2) STRIPPED-SIZE distribution — per aside kind, count asides whose tag-stripped text exceeds 3,300 chars (the conservative pop floor; the decline threshold is bracketed 3,313 < T <= 7,748). List the worst offenders per kind with ids + sizes (the known 67 merged >= 5k are prior art — extend per-kind, per-edition-relevant).
(S3) HIDDEN-TARGET navigate fallback — any epub:type="noteref" whose href target sits inside a hidden=""/display:none ancestor has NO rendered position; on decline Kobo lands at FILE START (the teleport class). Enumerate ALL noteref->target pairs by container type and report any class beyond the known notes-section one.
Also check the build code for emitters added later that would silently miss the separator/clamp/size policies (the fix-the-class rule). Findings need the emitter file:line or the artifact ids + counts.`,
    angles: ['Emphasize S1+S3: enumerate every footnote-aside emitter + every noteref target-container class in code AND artifact.', 'Emphasize S2: the per-kind stripped-size census on both shipped artifacts, with exact ids/sizes/counts.'],
  },
  {
    key: 'decommission', kind: 'find', finders: 1,
    prompt: `DIMENSION: DECOMMISSION CANDIDATES (program step-3 input — find what is no longer needed; findings-only, remove NOTHING). Hunt for: (a) one-shot scripts/_ship_*.py or scripts/_*.py whose arc CLOSED but which were never archived to dev/archive/ship_scripts/ (RULES section 7.4); (b) dead workflows under .claude/workflows/ (superseded engines, continuation scripts for finished runs); (c) stale dist/ artifacts + staging dirs (kr2/kr3 build series now superseded by v0.1.0 — list them with sizes; recommendation must be archive-to-E: or delete, never silent); (d) dead branches on the remotes (e.g. lane-transfer/* whose content merged); (e) requirements/deps no longer imported anywhere (prove with a grep, not a guess); (f) docs/notes that are pure duplicates of CHANGELOG content (NOT the truth records themselves); (g) tools in .tools/ or dev/ no longer referenced. HARD LIMITS: never propose touching the marathon core, GAPS/, content/**, or epub_working/**; archive-first bias; each finding = path + why-dead (with the evidence) + the safe disposal step.`,
  },
  {
    key: 'stack-review', kind: 'optimization', finders: 1,
    prompt: `OPTIMIZATION RE-EVALUATION: THE STACK ITSELF (user mandate: challenge current language/tooling choices incl. the mint-cleanup "KEEP PYTHON" call — re-justify or change). Survey the actual stack: Python 3.14 (stdlib-only web server, data-as-tuples, pytest, ruff, mypy), Node only for website/build.mjs, PowerShell + bash build scripts, PyInstaller desktop builders, the static website. Against the REMAINING program (Phase-D vision transcription, re-verification/re-ingest, parallel-Bible standalone builds, v0.1.x maintenance), evaluate: (a) is KEEP PYTHON still right? (b) within Python: are there upgrade-worthy moves (newer stdlib features, typing coverage, packaging, faster zip, tool consolidation) with real benefit? (c) CONDENSATION: which clone families could collapse into shared cores WITHOUT a rewrite-for-rewrite's-sake (the at_scale_base hoist is the precedent — name the next 2-3 with LOC estimates)? (d) any tool we use that a better free tool replaces (epubcheck/kepubify/PyInstaller alternatives)? Produce ONE finding per recommendation: CONFIRM-OPTIMAL (severity=info) or a concrete BETTER PLAN (severity=low/medium) with migration cost + regression risk explicit. HARD CONSTRAINTS: no DB, no web-framework adoption for the local app, no paid services, 9-KJV byte-stability, the rewrite bar is HIGH (pure regression risk for zero functional gain was the standing verdict — overturn it only with concrete evidence).`,
  },
  {
    key: 'future-work', kind: 'optimization', finders: 1,
    prompt: `OPTIMIZATION RE-EVALUATION: FUTURE-WORK SYSTEMS (user mandate: are the planned systems for the YET-UNDONE work fully optimized BEFORE we run them?). Read the ACTIVE plans/specs for remaining work: docs/superpowers/plans/2026-05-28-geez-patrologia-vision-plan.md (Phase-D vision transcription, paused p28), docs/superpowers/plans/2026-05-17-kings-manuscript-collation.md (LANE M marathon), the re-verification/re-ingest program spec (search docs/superpowers/specs/ for the 2026-06-02 reverification spec), dev/archive/SCOPE_2026-05-16-parallel-bible-standalone-bibles.md + the roadmap LANE P, docs/superpowers/notes/2026-06-10-verse-boundary-residual-design.md (the 117-fix), docs/superpowers/notes/2026-06-10-native-toc-chapters-evaluation.md. For EACH: is the planned method still optimal under TODAY's capabilities (Fable 5 session model, 1M-context Opus subagents, Workflow orchestration, the two-machine split, the shipped tooling)? Produce one finding per plan: CONFIRM-OPTIMAL (severity=info, with why) or a concrete UPGRADE (severity=low/medium, the better method + trade-offs + RAM/OOM realism for the N95 + what stays user-paced). HARD CONSTRAINTS: no paid script-API; the marathon-core data is untouchable; calibrate-first GO/NO-GO per book stays; read-the-print (flag, never harmonize) stays.`,
  },
  // ---- OPTIMIZATION dimension (approach re-evaluation; targets the PROJECT'S WORK, not meta-tooling/env) ----
  {
    key: 'opt-vision', kind: 'optimization', finders: 1,
    prompt: `OPTIMIZATION RE-EVALUATION (not bug-finding). Re-evaluate the VISION-TRANSCRIPTION MARATHON method (Patrologia Esther: docs/superpowers/plans/2026-05-28-geez-patrologia-vision-plan.md; Kings/Samuel: docs/superpowers/plans/2026-05-17-kings-manuscript-collation.md; decisions in content/translations/sources/patrologia/_vision_notes.md). The current method was designed under OOM-era constraints + pre-1M-context models: AGENT path, MAX-1-heavy-agent, tight <=1568px region crops, per-step commits, controller-renders / subagents-Read. Given TODAY (Opus 4.8 1M-context, ultracode, Workflow orchestration, parallel multi-agent): is it still optimal? Produce a finding PER concrete recommendation: either CONFIRM-OPTIMAL (severity=info, fix="confirmed optimal: <why>") OR a concrete BETTER PLAN (severity=low/medium, fix=<the better method + trade-offs + any RAM/cost risk>). HARD CONSTRAINTS: no paid script-path API (out of scope, no budget); recommend method changes only — never propose editing the marathon core's data; the OOM history is real (3 crashes) so any higher-parallelism proposal must address RAM.`,
  },
  {
    key: 'opt-build', kind: 'optimization', finders: 1,
    prompt: `OPTIMIZATION RE-EVALUATION. A single-edition build is ~133 s (re-zips a ~23 MB epub_working/ tree per edition; measured mint-7 E3) — the all-9 loop is slow. Read scripts/build_edition.py + the build pipeline in MATRIX_MAP. Is the inject -> filter -> zip path optimizable: incremental builds, a shared pre-filtered base, parallel edition builds, cheaper/streamed zip, caching the unchanged base across editions? Produce CONFIRM-OPTIMAL or a concrete BETTER PLAN with the expected speedup AND the byte-stability proof obligation (the 9 KJV editions MUST stay byte-identical — any optimization must demonstrate byte-identical output, RULES byte-compat invariant).`,
  },
  {
    key: 'opt-ingest', kind: 'optimization', finders: 1,
    prompt: `OPTIMIZATION RE-EVALUATION. Re-evaluate the INGEST pipeline (detector -> candidate -> promote; the chi-cluster pattern RULES S9; the at-scale drivers scripts/run_*_at_scale.py; post core/at_scale_base.py dedup). Given Workflow/parallel-agents, is this still the best orchestration, or is there a better shape (parallel detector runs over books, batched/streamed promote, a single unified driver replacing the ~10 clones)? CONFIRM-OPTIMAL or concrete BETTER PLAN; must stay idempotent and keep the canonical-coordinate guard at the promote boundary.`,
  },
  {
    key: 'opt-render', kind: 'optimization', finders: 1,
    prompt: `OPTIMIZATION RE-EVALUATION. Re-evaluate the RENDER-COVERAGE (scripts/render_coverage.py) + STANDALONE-BUILD (scripts/build_standalone.py — READ-ONLY, off-limits to edit) lanes plus the standalone EN back-translation lane. Are they optimal given current capabilities? CONFIRM-OPTIMAL or a concrete BETTER PLAN (you may RECOMMEND, never edit the standalone core).`,
  },
  // ---- ROUND-9 PLATFORM RESEARCH (post round-8 remediation — findings-only research dims) ----
  {
    key: 'platform-apple', kind: 'find', finders: 2,
    prompt: `DIMENSION: PLATFORM RESEARCH — Apple Books (M2 / target_reader=tablet). READ-ONLY research + repo cross-check (no code changes). Authoritative UX: ${REPO}/docs/superpowers/notes/2026-06-15-apple-m2-layout-directive.md + ${REPO}/dev/EREADERS.md §Apple. Tasks: (1) Official Apple/iBooks EPUB3 support for popup footnotes, embedded fonts, page-break CSS, details/summary ToC. (2) Community/publisher precedents for verse-end badge + vn-link-at-start study-Bible layout. (3) Gap analysis vs our tablet build path in scripts/build_edition.py + TARGET_CAPS. (4) Rank options A/B/C for M2 polish (typography inside native popup sheet only — NO Kobo/Kindle fork bleed). Output ONE finding per material gap or CONFIRM-OPTIMAL (info) per area; cite vendor doc URLs + repo file:line. Write brief to ${REPO}/docs/superpowers/notes/2026-06-18-platform-apple.md using the template at notes/2026-06-17-platform-research-template.md.`,
    angles: ['Emphasize official EPUB feature matrix vs our tablet profile.', 'Emphasize study-Bible layout precedents + M2 layout directive compliance.'],
  },
  {
    key: 'platform-kobo', kind: 'find', finders: 2,
    prompt: `DIMENSION: PLATFORM RESEARCH — Kobo e-ink (M3 / target_reader=eink / .kepub.epub). READ-ONLY research + optional ONE local kepub build for measurement. Authoritative: ${REPO}/dev/EREADERS.md §Kobo + kobo round-4..8 device QA notes + dev/kobo_tap_calibration.py. Tasks: (1) KePub/kepubify transform rules (koboSpan, aside id survival). (2) Footnote preview stripped-text limits (community + our 4,498/5,500 calibration). (3) Study→glossary backmatter (K-R9c) precedents in other study Bibles. (4) dc:language multi-value for popup script fallbacks. (5) Gap vs eink path: inject_eink_study_backmatter, apply_file_split, byte-cap gate. Rank options for K-R4-2 + tap round 9. Output findings + brief notes/2026-06-18-platform-kobo.md.`,
    angles: ['Emphasize kepub preview dialog limits + K-R9 backmatter model.', 'Emphasize file-split/piece-size + dc:language popup font chain.'],
  },
  {
    key: 'platform-kindle', kind: 'find', finders: 2,
    prompt: `DIMENSION: PLATFORM RESEARCH — Kindle (M4/M4b / kindle_post minimal recipe). READ-ONLY research + repo forensics. Authoritative: ${REPO}/docs/superpowers/notes/2026-06-15-kindle-phone-qa-kindle_img.md + ${REPO}/dev/EREADERS.md §Kindle + scripts/core/kindle_post.py. Tasks: (1) Send-to-Kindle KFX: internal # anchor failure across page-breaks (phone QA theory). (2) Why minimal kindle_post (strip display:none, keep vn-sep, single dc:language) beat elaborate variant. (3) Commercial study-Bible endnote patterns. (4) M4b fork design: suppress inline markers + chapter-tail notes — map to concrete HTML moves (mirror Kobo backmatter?). (5) What STK 6/6 did NOT gate. Output findings + brief notes/2026-06-18-platform-kindle.md.`,
    angles: ['Emphasize KFX anchor/page-break failure mode + phone QA evidence.', 'Emphasize M4b fork options + kindle_post recipe validation.'],
  },
  {
    key: 'platform-play', kind: 'find', finders: 2,
    prompt: `DIMENSION: PLATFORM RESEARCH — Google Play Books (M5 / provisional everywhere). READ-ONLY research. Authoritative: ${REPO}/dev/EREADERS.md §Play + staged artifact YHWH-ethiopian-tewahedo-v0.1.0-everywhere-navy.epub on v0.1.0 release. Tasks: (1) Play Books personal-upload EPUB requirements (version, size, encryption). (2) Popup footnote behavior Android vs iOS Play app. (3) Font embedding + RTL scripts. (4) Stuck details ToC — accept or flat-ToC fork? (5) Does everywhere suffice or need target_reader: play? Output findings + brief notes/2026-06-18-platform-play.md + device QA checklist refinements.`,
    angles: ['Emphasize official Play upload constraints + popup/font support reports.', 'Emphasize everywhere vs play profile decision tree.'],
  },
  // ---- ROUND-14 BUILD-PIPELINE DIMS (2026-06-26; program dev/audit/build-pipeline-deep-audit-program-2026-06-25.md).
  //      TARGET A (the build machinery) + the propagation lens (program logic fault -> silent epub defect).
  //      All read-only source analysis (model-bound -> Mac lane; truly parallelize with the local byte-proof builds). ----
  {
    key: 'pagebreak-rearch', kind: 'find', finders: 2,
    prompt: `DIMENSION (round-14 build-pipeline, program A4/A7/B3): the EINK PAGE-BREAK RE-ARCHITECTURE. Read ${REPO}/scripts/build_edition.py: _merge_scripture_base_files (per-book base-file merge; None->return 0 abort; per-segment .replace remap), _merge_mid_verse_breaks (lead-prose AND marker AND anchor heuristic; book-boundary tracking; _MIDVERSE_BREAK_KEEP_BOOKS), and the 8 MB per-book sharding in apply_file_split. Hunt: (a) a merge that aborts-to-noop and SILENTLY ships a half-merged spine (program A4/P5); (b) a mid-verse merge mis-detecting a real verse boundary -> reordered/duplicated verse text (A7/P7); (c) a per-segment .replace that rewrites the WRONG occurrence; (d) any eink-only gating that LEAKS into the 9-KJV byte-stable base (prove the call sites are strictly inside the =="eink" branch). Cite file:line + the exact failing input class. Settled: do NOT re-litigate the page-break design (shipped) — hunt regressions/leaks only.`,
    angles: ['Emphasize the merge abort-to-noop + wrong-occurrence .replace remap (silent half-merge).', 'Emphasize the mid-verse heuristic mis-detect (verse text reorder/dup) + an eink-gating leak into the KJV base.'],
  },
  {
    key: 'file-split', kind: 'find', finders: 2,
    prompt: `DIMENSION (round-14, program A2/A3/A12/B6): apply_file_split ORDER-OF-OPERATIONS + cross-file link integrity. Trace the full sequence (merge -> midverse -> split -> opener-pop -> idmap -> rewrite_links -> OPF -> nav) in ${REPO}/scripts/build_edition.py. Hunt: (a) rewrite_links bare/full-href FALLBACK on an idmap MISS -> a dead/wrong cross-file link only visible on a real e-reader (A3/P4); (b) a cut that is not well-formed (stack-aware reopen/close) or a piece orphaned from the spine; (c) re-reads of each piece ~5x (redundant disk passes, A12) -> confirm they read CONSISTENT bytes, not divergent reads; (d) every badge->footnote target + noteref still resolves to the piece holding the id; ids unique across pieces. Cite file:line + the miss class.`,
    angles: ['Emphasize the idmap-miss href fallback -> dead/wrong link (silent, e-reader-only).', 'Emphasize cut well-formedness, spine completeness, and cross-piece id uniqueness.'],
  },
  {
    key: 'eink-gating-leak', kind: 'find', finders: 2,
    prompt: `DIMENSION (round-14, program A1/B10/P1 — the HEADLINE byte-stability risk): EINK-GATING LEAKS into the 9-KJV byte-stable set ({catholic-study, evangelical-reformed, eastern-orthodox} x {everywhere, tablet, kindle}). The eink page-break merge, mid-verse merge, WS3 popup separators (kobo-vn-br / visible middot), and the eink font !important rules are ALL supposed to be strictly eink-gated. In ${REPO}/scripts/build_edition.py enumerate EVERY \`== "eink"\` / eink-target branch + every kw-only \`eink=\` threaded through the cascade/badge/chunk/budget-pack/backmatter chains; for EACH, prove the non-eink path is untouched (no shared-mutable, no default flip, no fall-through that runs the eink mutation when eink=False). A single leak silently re-baselines the KJV editions with NO automated gate today (G1 closes it) -> any UNPROVABLE isolation is itself a finding. Cite the branch file:line + whether it is provably isolated.`,
    angles: ['Emphasize default-value / shared-mutable / fall-through leaks where an eink mutation runs at eink=False.', 'Emphasize kw-only eink= thread COMPLETENESS across the full cascade/backmatter chain (one un-threaded call site = a leak).'],
  },
  {
    key: 'glossary-streaming', kind: 'find', finders: 2,
    prompt: `DIMENSION (round-14, program A5/A6/A12/P3): the STREAMING STUDY-GLOSSARY SPLIT + the OOM frees. Read ${REPO}/scripts/build_edition.py: _iter_study_glossary_pieces_from_file / _stream_glossary_pieces_from_bytes / _group_glossary_atoms / split_study_glossary_document, apply_file_split's glossary handling, and the frees (del pre_badge_texts / del repair_texts / badge_stats.pop("study_backmatter_entries") + glossary del body/inner/text). Hunt: (a) any of the ~5 UNSPLIT fall-through paths that ship a glossary piece OVER the Kobo navigate cap or packing two book-heads (A5/P3); (b) a free-after-use where something IS read after the del/pop (prove the byte vs str split paths cut at IDENTICAL points; prove .pop frees the ONLY ref — the .get-vs-.pop bug that left 489 MB resident is the precedent); (c) the from-file byte path vs the str reference producing DIFFERENT bytes (the catholic 453/453 proof must hold). Cite file:line + the divergent/leak case.`,
    angles: ['Emphasize the unsplit fall-throughs (an over-cap or two-book-head glossary piece).', 'Emphasize free-after-use correctness + byte-path == str-path identical cut points.'],
  },
  {
    key: 'cascade-dedup', kind: 'find', finders: 1,
    prompt: `DIMENSION (round-14, program B7/A10/P2): the WS2 NOTE-CASCADE DE-DUPLICATION + badge merge. Read ${REPO}/scripts/build_edition.py: _emit_cascade_sections, _strip_redundant_body_boilerplate, apply_badge_markers (badge collapse + aside merge), and the kobo-study-nav-pad recompute. Hunt: (a) a de-dup that removes a DISTINCT note (not a true byte-identical duplicate) -> data loss; (b) badge count != pre-collapse marker count, or a reordered/dropped note (P2 — badges_skipped must be 0); (c) the body-boilerplate strip regex over-greedy (eats real body); (d) any unescaped note-text interpolation in the merged aside (stored-XSS). Cite file:line + the lost/dropped/over-stripped note class.`,
  },
  {
    key: 'popup-separators', kind: 'find', finders: 1,
    prompt: `DIMENSION (round-14, program B5/A1): the WS3 EINK POPUP SEPARATORS contract. Read ${REPO}/scripts/build_edition.py: the eink _VN_SEP_{ITEM,CAT,BYLINE}_EINK constants + the br.kobo-vn-br rule + the eink= thread through _emit_cascade_sections / _badge_aside_inner_to_row / _chunk_vn_item_row / the budget-pack + backmatter-glossary chains. Hunt: (a) an emitter that bakes hidden-only U+2028 .vn-sep separators (run-on in Kobo's tag-stripped footnote overlay) that the eink swap MISSED — fix-the-class: the known sibling is the vnote translation-popup family carrying ~119k U+2028 (confirm in/out of scope, do NOT re-derive it); (b) the eink separators LEAKING into non-eink output (must be 0). Cite the emitter file:line.`,
  },
  {
    key: 'resplit-integrity', kind: 'find', finders: 1,
    prompt: `DIMENSION (round-14, program A7/B2/B4): the 158-verse VERSIFICATION RE-SPLIT (USER-RATIFIED, applied to epub_working/ at commit 6b690361). SETTLED — do NOT re-litigate the decision; audit only for INTEGRITY + REGRESSION at the SOURCE level. Read ${REPO}/dev/audit/ws1_resplit_apply.py + the resplit data json + a sample of the 38 touched ${REPO}/epub_working/index_split_*.html files. Verify: (a) each re-split moved ONLY a verse boundary (char-multiset invariant per file; prose==web post-check) with NO wording change; (b) no nested <a>, no broken #frag, no duplicate id introduced; (c) the empty-anchor count actually dropped and no NEW empty anchor appeared. Report any file where the relocation added/removed/altered a character or broke an anchor. (The all-edition BUILD byte-proof is a separate Mac deterministic task; this dim is the source-level integrity check.)`,
  },
]

// SPLIT-RUN across the two machines (2026-06-05 — see docs/superpowers/plans/2026-06-05-split-audit-plan.md).
// Set LANE in-file per machine (args don't reliably propagate). 'win' = the SSD / LOCAL-COMPUTE-heavy dims
// (they run pytest + builds — keep them on the N95's fast disk); 'mac' = the read-only code-review dims
// (model-call-bound, disk-light — the Mac is HDD-bound). The two lanes use DIFFERENT resources (local disk
// vs model calls) so they truly parallelize. 'all' (default) = the full made-current set on one machine.
// Findings from each lane merge in ONE final synthesize on the N95 (archive/deep-audit-continue.js is the
// inject-findings precedent; the consumed one-shots live in .claude/workflows/archive/ since round-7 P3).
// Leave LANE='all' committed; each lane flips its OWN local copy, never commits it.
// ★ SCOPE (user, 2026-06-10): round 8+ audits = PROJECT CODE / PRODUCT ONLY (+ occasionally one
// Claude-optimization dim). Drop claude-setup / lane-system / github-gitlab / stack-review /
// decommission from the default set when re-running — round 7 was the one-time everything-sweep.
// LANE is defined at the top of the file (parity bake). win = the LOCAL-COMPUTE-heavy
// dims (pytest + builds → the N95's fast SSD); mac = the read-only, model-call-bound
// code-review dims (disk-light → fine on the HDD-bound iMac). Different bottlenecks ⇒
// they truly parallelize. round 6 adds dist-packaging + website-deploy to the mac set.
// round-7 lane placement for the NEW program dims (used only when LANE != 'all'):
// claude-setup + popup-integrity + github-gitlab are WIN-bound (the C:/Users/bogda
// paths, the dist/ artifacts, and the authed gh CLI live on the N95; a Mac
// claude-setup run would need ITS OWN box's paths — re-prompt locally, never commit).
// The round-7 one-time everything-sweep meta dims: DEFINED above but excluded from the default
// (SCOPE='product'); they run only on explicit SCOPE='all' (memory reference_deep_audit_tool).
const EVERYTHING_SWEEP_DIMS = new Set(['claude-setup', 'lane-system', 'github-gitlab', 'stack-review', 'decommission'])
const LANE_DIMS = {
  // win = LOCAL-COMPUTE-heavy (runs pytest + local builds on the N95's SSD) + the WIN-only surfaces
  //       (C:/Users/bogda paths, dist/ artifacts, the authed gh CLI). The sweep dims here run only at SCOPE='all'.
  win: ['tests-run', 'opt-build', 'byte-stability', 'rx-surfaces', 'popup-integrity', 'platform-kobo',
        'claude-setup', 'github-gitlab'],
  // mac = read-only, model-call-bound code review (disk-light -> fine on the HDD-bound iMac).
  mac: ['correctness', 'security', 'code-debt', 'tests', 'docs', 'data-validity',
        'concurrency-caching', 'cross-module', 'marathon-boundary', 'dist-packaging',
        'website-deploy', 'future-work', 'opt-vision', 'opt-ingest', 'opt-render',
        'platform-apple', 'platform-kindle', 'platform-play',
        'lane-system', 'decommission', 'stack-review'],
}
// SCOPE filter (product default) -> optional LANE filter -> args.dimensions overrides everything.
const _scoped = SCOPE === 'all' ? DEFAULT_DIMENSIONS : DEFAULT_DIMENSIONS.filter((d) => !EVERYTHING_SWEEP_DIMS.has(d.key))
// ROUND-14 build-pipeline audit (2026-06-26): a FOCUSED set — the perennial product/code dims + the
// new build-machinery dims; drops the website/dist/platform/lane/meta dims (program doc "Drop
// out-of-scope dims"). ROUND-gated so the perennial LANE_DIMS stay intact for other rounds; both lanes
// run the same set this round (Mac = semantic fan-out, WIN = fixes). LANE still selects REPO + agent
// types (so the Mac box must run LANE='mac'). NOTE: 'tests-run' is deliberately OMITTED — it is the one
// LOCAL-pytest dim, and round-14 runs the engine CONCURRENTLY with the local byte-proof builds (Mac
// box); pytest is run separately/after the builds (never-pytest-beside-a-build). All round-14 dims here
// are read-only source analysis = model-bound, so they truly parallelize with the local builds.
const ROUND14_DIMS = new Set(['correctness', 'security', 'byte-stability', 'cross-module',
  'data-validity', 'pagebreak-rearch', 'file-split', 'eink-gating-leak', 'glossary-streaming',
  'cascade-dedup', 'popup-separators', 'resplit-integrity'])
const _laneSet = LANE === 'all' ? null : new Set(LANE_DIMS[LANE] || [])
const DIMENSIONS = args?.dimensions ?? (ROUND === 14 ? _scoped.filter((d) => ROUND14_DIMS.has(d.key)) : (_laneSet ? _scoped.filter((d) => _laneSet.has(d.key)) : _scoped))

// ----------------------------------------------------------------------------
// Helpers
// ----------------------------------------------------------------------------
function agentTypeForFind(dim) {
  if (dim.kind === 'optimization') return _AG.architect
  if (dim.kind === 'guard') return _AG.guard
  return _AG.review
}
function agentTypeForVerify(dim) {
  if (dim.kind === 'optimization') return _AG.architect
  if (dim.kind === 'guard') return _AG.guard
  return _AG.review
}
function finderCount(dim) {
  return DEPTH === 'deep' ? (dim.finders ?? 1) : 1
}
function panelSize(sev, dim) {
  if (DEPTH !== 'deep') return 1
  if (dim.kind === 'optimization') return 1
  if (sev === 'critical') return 3
  if (sev === 'high') return 2
  return 1
}
function keyOf(f) {
  return ((f.file || '').toLowerCase().trim()) + '::' + ((f.title || '').toLowerCase().trim().slice(0, 90))
}
function dedupe(findings) {
  const seen = new Set()
  const out = []
  for (const f of findings) {
    if (!f || !f.title) continue
    const k = keyOf(f)
    if (seen.has(k)) continue
    seen.add(k)
    out.push(f)
  }
  return out
}
function calibrateSeverity(f) {
  const votes = (f.panel || []).map((v) => v && v.corrected_severity).filter((s) => s && s !== 'none')
  if (!votes.length) return f.severity
  const tally = {}
  for (const s of votes) tally[s] = (tally[s] || 0) + 1
  let best = null
  for (const s of Object.keys(tally)) {
    if (best === null || tally[s] > tally[best] || (tally[s] === tally[best] && rank[s] > rank[best])) best = s
  }
  return best || f.severity
}

function verifyPrompt(f, dim) {
  const common = `${PREAMBLE}

You are an ADVERSARIAL VERIFIER. Default to refuted=TRUE. Only set refuted=false if you INDEPENDENTLY confirm, by reading the cited code yourself, that the finding is real and material.

FINDING (dimension: ${dim.key}, finder severity: ${f.severity}):
- title: ${f.title}
- file: ${f.file}   line: ${f.line}
- evidence: ${f.evidence}
- proposed fix: ${f.fix}
`
  if (dim.kind === 'optimization') {
    return common + `
This is an OPTIMIZATION recommendation, not a bug. The finding claims the current project method is sub-optimal and proposes a better approach (or confirms it optimal). REFUTE unless the proposed approach is concretely, demonstrably better (faster / cheaper / higher-fidelity) AND feasible WITHOUT a paid API, WITHOUT touching the marathon core, and WITHOUT breaking the 9-edition byte-stability. If the finder said "confirmed optimal", set refuted=false only if you agree the current method is genuinely the best available today (else refute and explain the better path in reasoning). Set corrected_severity (info for a confirmed-optimal, low/medium for a worthwhile change, none if you refute the claim entirely).`
  }
  return common + `
Read the cited file/region. Check: (a) does the code actually do what the evidence claims? (b) is it a genuine defect, not intended behavior / already-guarded / dead-unreachable / a de-scoped item? (c) is the severity right (recalibrate down if the blast radius is bounded — e.g. no shipped-output corruption and the 9 KJV editions stay byte-stable)? (d) is the proposed fix correct AND safe (must not touch the marathon core; must keep the 9 KJV editions byte-stable; additive schema only)? Provide corrected_severity ('none' if refuted) and a corrected_fix if the finder's fix is wrong or unsafe.`
}

// ----------------------------------------------------------------------------
// FIND + VERIFY pipeline (pipeline = each dimension verifies as soon as it is found;
// no barrier between Find and Verify across dimensions)
// ----------------------------------------------------------------------------
// Startup param echo — makes it visible whether args propagated (the known
// papercut: a named Workflow({name}) invocation may not pass args, so the
// in-file defaults are what actually run; check this line to confirm).
log(`deep-audit round ${ROUND} | scope=${SCOPE} | depth=${DEPTH} | ${DIMENSIONS.length} dimensions | repo=${REPO} | argsRound=${args?.round ?? '(default)'} | deferred=${DEFERRED_BY_DESIGN.length}`)

async function findDim(dim) {
  const n = finderCount(dim)
  const atype = agentTypeForFind(dim)
  const runs = await parallel(
    Array.from({ length: n }, (_, i) => () => {
      const angle = (dim.angles && dim.angles[i]) ? `\n\nINDEPENDENT ANGLE [${i + 1}/${n}]: ${dim.angles[i]} Bring a fresh perspective; do not assume another finder will catch the obvious — report it yourself.` : (n > 1 ? `\n\n[Finder ${i + 1}/${n}] Bring an independent perspective.` : '')
      return agent(`${PREAMBLE}\n\n${dim.prompt}${angle}\n\nReturn findings via the structured output (empty array if nothing material).`, {
        label: `find:${dim.key}${n > 1 ? '#' + (i + 1) : ''}`,
        phase: 'Find',
        schema: FINDINGS_SCHEMA,
        agentType: atype,
        // 2026-06-22 (user): default to OPUS — audits MUST run on the strongest model, never
        // Sonnet. The feature-dev:code-reviewer agentType forces Sonnet (defeating the old
        // "inherit session model" intent) and Sonnet skips the forced StructuredOutput → false
        // negatives. Thoroughness over runtime ("I don't care how long it takes"). args.model overrides.
        model: args?.model ?? 'opus',
      })
    })
  )
  const all = runs.filter(Boolean).flatMap((r) => (r && Array.isArray(r.findings)) ? r.findings : [])
  const deduped = dedupe(all).map((f) => ({ ...f, dimension: dim.key, kind: dim.kind }))
  log(`  find:${dim.key} -> ${deduped.length} candidate finding(s)`)
  return deduped
}

// Run `size` adversarial skeptics for one finding, then TOP UP any null votes
// ONCE. ROUND-5 FIX (mint-11, 2026-06-02): a null vote means the sonnet verifier
// skipped the forced StructuredOutput tool (~22% of agents — 21/95 — in round 4),
// NOT that the finding is refuted; re-running only the missing skeptics recovers
// the transient miss without pinning the whole verify stage to Opus (which would
// reintroduce the ~8h runtime the 4-core cap=2 box can't afford). See
// docs/superpowers/notes/2026-06-02-mint-11-findings.md "Engine lesson".
async function runSkepticPanel(f, dim, size, atype) {
  const spawn = (i, suffix) =>
    agent(verifyPrompt(f, dim) + (size > 1 ? `\n\n[Skeptic ${i + 1}/${size} — verify independently.]` : '') + suffix, {
      label: `verify:${dim.key}`,
      phase: 'Verify',
      schema: VERDICT_SCHEMA,
      agentType: atype,
      // 2026-06-22 (user): default to OPUS (see find-stage note). args.model overrides.
      // The StructuredOutput-skip top-up retry below stays as the safety net.
      model: args?.model ?? 'opus',
    })
  let panel = (await parallel(Array.from({ length: size }, (_, i) => () => spawn(i, '')))).filter(Boolean)
  if (panel.length < size) {
    const more = (await parallel(
      Array.from({ length: size - panel.length }, (_, i) => () => spawn(i, '\n\n[Retry — the prior skeptic returned no structured verdict; reply ONLY via the structured-output tool.]'))
    )).filter(Boolean)
    panel = panel.concat(more)
  }
  return panel
}

async function verifyDim(findings, dim) {
  if (!findings || !findings.length) return []
  const atype = agentTypeForVerify(dim)
  return parallel(
    findings.map((f) => () => {
      const size = panelSize(f.severity, dim)
      return runSkepticPanel(f, dim, size, atype).then((panel) => {
        const refutes = panel.filter((v) => v.refuted).length
        // ROUND-5 FIX (mint-11): an empty panel even AFTER the top-up retry is NOT
        // a refutation (the skeptics never reported). Carry the finding as
        // UNVERIFIED — a survivor flagged for human triage — instead of silently
        // auto-refuting it (the round-4 false-negative that lost 2 HIGHs). Only a
        // real skeptic MAJORITY refutes.
        const unverified = panel.length === 0
        const refuted = unverified ? false : refutes > Math.floor(panel.length / 2)
        return { ...f, panel, verdict: { refuted, unverified, refutes, panelSize: panel.length } }
      })
    })
  )
}

const perDim = await pipeline(
  DIMENSIONS,
  (dim) => findDim(dim),
  (findings, dim) => verifyDim(findings, dim)
)

// ----------------------------------------------------------------------------
// SYNTHESIZE (barrier: needs all verified findings)
// ----------------------------------------------------------------------------
phase('Synthesize')
const verified = dedupe(perDim.flat().filter(Boolean))
const survivors = verified
  .filter((f) => f && !f.verdict.refuted)
  .map((f) => ({ ...f, finalSeverity: calibrateSeverity(f) }))
  .sort((a, b) => (rank[b.finalSeverity] ?? 0) - (rank[a.finalSeverity] ?? 0))
const dropped = verified.filter((f) => f && f.verdict.refuted)
const unverifiedSurv = survivors.filter((f) => f && f.verdict.unverified)

log(`verified: ${survivors.length} survived (${unverifiedSurv.length} UNVERIFIED — empty skeptic panel after retry, needs manual triage), ${dropped.length} refuted (of ${verified.length} deduped)`)

const survForPlan = survivors.map((f) => ({
  dimension: f.dimension, kind: f.kind, severity: f.finalSeverity,
  title: f.title, file: f.file, line: f.line, evidence: f.evidence,
  unverified: !!f.verdict.unverified,
  fix: (f.panel || []).map((v) => v && v.corrected_fix).filter(Boolean)[0] || f.fix,
}))

const bugSurv = survForPlan.filter((f) => f.kind !== 'optimization')
const optSurv = survForPlan.filter((f) => f.kind === 'optimization')

let fixesPlanMarkdown = 'No surviving findings — nothing to plan.'
if (survForPlan.length) {
  const sevTally = survivors.reduce((a, f) => { a[f.finalSeverity] = (a[f.finalSeverity] || 0) + 1; return a }, {})
  const COUNT_LINE = `ROUND ${ROUND}: ${verified.length} deduped findings -> ${survivors.length} verified survivors / ${dropped.length} refuted (of the survivors, ${unverifiedSurv.length} are UNVERIFIED — their skeptic panel was empty even after a retry, so they need manual triage, not auto-confirmation). By severity: ${JSON.stringify(sevTally)}. Bug/correctness/etc = ${bugSurv.length}; optimization = ${optSurv.length}.`
  fixesPlanMarkdown = await agent(
    `${PREAMBLE}

You are SYNTHESIZING a phased fixes plan from the VERIFIED audit findings below (each already survived adversarial refutation). Write a concise, actionable Markdown plan — no preamble fluff.

AUTHORITATIVE COUNTS (use these EXACT numbers in the executive summary — do NOT recompute or estimate your own totals; a prior synth hallucinated "36 findings" for a 57-survivor set):
${COUNT_LINE}

VERIFIED BUG/CORRECTNESS/SECURITY/DEBT/TEST/DOC FINDINGS (JSON):
${JSON.stringify(bugSurv, null, 1)}

VERIFIED OPTIMIZATION RECOMMENDATIONS (JSON):
${JSON.stringify(optSurv, null, 1)}

Produce Markdown with these sections:
1. "## Executive summary" — 3-5 sentences using the AUTHORITATIVE COUNTS verbatim: how many findings, the most serious, overall codebase health.
2. "## Phased fixes" — group the bug findings into phases ordered SAFEST/MOST-FOUNDATIONAL FIRST (additive + guard-adding before behavior-changing; security + silent-data-loss high priority). For each finding: a checkbox line with severity, title, file:line, the (corrected) fix, the test/guard to add, and whether it touches the build path (=> byte-stability proof obligation). Prefer a commit-time lint_rules check over a pytest-only guard for invariants that recur every ingest.
3. "## Optimization decisions" — a table: Area | Verdict (confirmed-optimal / change) | Recommendation. Keep the marathon-core off-limits and the no-paid-API + byte-stability constraints explicit.
4. "## Constraints carried" — never touch the marathon core; 9 KJV editions byte-stable; additive schema; atomic writes; **bandwidth-first save cadence (RULES §4): LOCAL-COMMIT per fix, full 5-leg sync only at a milestone**; and this audit is FINDINGS-ONLY — produce the plan, STOP before applying any fix (user marching order 2026-06-08).
Return ONLY the Markdown.`,
    { label: 'synth:fixes-plan', phase: 'Synthesize', model: args?.model ?? 'opus' }
  )
}

const completeness = await agent(
  `${PREAMBLE}

This deep-audit round covered these dimensions: ${DIMENSIONS.map((d) => d.key).join(', ')}.
Findings per dimension (survived / total verified):
${DIMENSIONS.map((d) => { const v = verified.filter((f) => f.dimension === d.key); const s = v.filter((f) => !f.verdict.refuted); return `  ${d.key}: ${s.length}/${v.length}`; }).join('\n')}
Surviving finding titles: ${survivors.map((f) => f.title).join(' | ') || '(none)'}

As a COMPLETENESS CRITIC, identify what this round likely MISSED — a subtree/module/data-set not searched, an invariant not checked, a failure mode a single-pass finder would skip, or a dimension that returned suspiciously little. Return concrete gaps + a finder lens for each (these seed the next convergence round). Be specific to THIS codebase, not generic.`,
  { label: 'synth:completeness-critic', phase: 'Synthesize', schema: COMPLETENESS_SCHEMA, agentType: _AG.review, model: args?.model ?? 'opus' }
)

return {
  tool: 'deep-audit',
  round: ROUND,
  now: NOW,
  depth: DEPTH,
  dimensions: DIMENSIONS.map((d) => ({ key: d.key, kind: d.kind, finders: finderCount(d) })),
  counts: {
    deduped: verified.length,
    survived: survivors.length,
    refuted: dropped.length,
    bySeverity: survivors.reduce((a, f) => { a[f.finalSeverity] = (a[f.finalSeverity] || 0) + 1; return a }, {}),
  },
  survivors: survivors.map((f) => ({
    dimension: f.dimension, kind: f.kind, severity: f.finalSeverity, originalSeverity: f.severity,
    title: f.title, file: f.file, line: f.line, evidence: f.evidence, fix: f.fix,
    unverified: !!f.verdict.unverified,  // round-5: empty skeptic panel after retry → human triage, not auto-confirmed
    verifierFix: (f.panel || []).map((v) => v && v.corrected_fix).filter(Boolean)[0] || '',
    panel: (f.panel || []).map((v) => ({ refuted: v.refuted, confidence: v.confidence, reasoning: v.reasoning })),
  })),
  dropped: dropped.map((f) => ({
    dimension: f.dimension, severity: f.severity, title: f.title, file: f.file,
    refutes: f.verdict.refutes, panelSize: f.verdict.panelSize,
    reason: (f.panel || []).map((v) => v && v.reasoning).filter(Boolean)[0] || '',
  })),
  fixesPlanMarkdown,
  completeness: completeness && completeness.gaps ? completeness.gaps : [],
}
