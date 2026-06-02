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
const REPO = args?.repo ?? 'C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4'  // repo root (ABSOLUTE — cwd-independent; round-3 hardening after a cwd-ambiguity risk surfaced)
const DEPTH = args?.depth ?? 'deep'               // 'deep' = multi-finder + scaled skeptic panels
const ROUND = args?.round ?? 4              // mint-11 = round 4 (mint-9=2, mint-10=3); bump in-file, args don't reliably propagate
const NOW = args?.now ?? '2026-06-02'             // Date.now() is unavailable in scripts; stamp via args

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
]
const PRIOR_SURVIVOR_TITLES = args?.priorSurvivors ?? []  // optional: titles already fixed in a prior round, to avoid re-reporting verbatim

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
    prompt: `DIMENSION: DOCS / DATA-HYGIENE DRIFT. Find stale refs / dead pointers and doc-vs-code drift the linter cannot catch semantically: dev/*.md + docs/superpowers/** + module docstrings referencing removed modules, renamed files, or wrong counts (console inventory = 18; kinds/editions counts; the 26-check lint registry); archived-file pointers that 404; MATRIX_MAP / REPO_MAP semantic currency vs the actual tree. Cite the stale line and the correct value.`,
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
    // mint-9 engine upgrade: ACTUALLY RUN THE TESTS. Rounds 1-2 each shipped a
    // STALE test that a single pytest run would have caught (a guard scanning a
    // file for a literal that had moved; a test reading the live CHANGELOG after
    // a month-roll). Source-reading finders can't see a red test — execute them.
    key: 'tests-run', kind: 'guard', finders: 1,
    prompt: `EXECUTE THE TEST SUITE (not a source read — actually run pytest) and report every FAILURE or ERROR as a finding. This catches stale/broken tests that source-scanning misses (e.g. a guard that scans a file for a literal that moved during a refactor; a test asserting on a doc that was month-rolled).

Run from the repo with the project's interpreter + env. Use Bash, one shard at a time to stay under memory limits (RULES: PYTHONUTF8=1, full pythoncore path, --basetemp under %LOCALAPPDATA%). Suggested fast pass (deselect the slow build tests):
  cd "${REPO}"; set PYTHONUTF8=1; set PYTHONPATH=<repo abs path>
  <pythoncore>/python.exe -m pytest tests/ -q -p no:cacheprovider -m "not slow" -x --basetemp="C:/Users/bogda/AppData/Local/Temp/yhwh-pytest/audit" 2>&1 | tail -40
If a single -x run trips early, note the failure, then continue the rest with --deselect or by running the remaining files so you surface ALL failures, not just the first. (If the environment cannot run pytest at all, say so in ONE finding and stop — do not fabricate pass/fail.)

For EACH failing/erroring test produce a finding: severity = high if it indicates a real code regression, medium if it is a STALE test (assertion drifted from reality — the code is right, the test is wrong), low for a flaky/env issue; file = the test file:line; evidence = the assertion + the actual vs expected; fix = correct the code OR update the stale test (say which). If the whole suite passes, return an EMPTY findings list (that is the success signal for this dimension).`,
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
]

const DIMENSIONS = args?.dimensions ?? DEFAULT_DIMENSIONS

// ----------------------------------------------------------------------------
// Helpers
// ----------------------------------------------------------------------------
function agentTypeForFind(dim) {
  if (dim.kind === 'optimization') return 'feature-dev:code-architect'
  if (dim.kind === 'guard') return 'Explore'
  return 'feature-dev:code-reviewer'
}
function agentTypeForVerify(dim) {
  if (dim.kind === 'optimization') return 'feature-dev:code-architect'
  if (dim.kind === 'guard') return 'Explore'
  return 'feature-dev:code-reviewer'
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
log(`deep-audit round ${ROUND} | depth=${DEPTH} | ${DIMENSIONS.length} dimensions | repo=${REPO} | argsRound=${args?.round ?? '(default)'} | deferred=${DEFERRED_BY_DESIGN.length}`)

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
        model: 'sonnet',  // mint-11: pin finders to sonnet (4-core cap=2 -> ~3h not ~8h; audit_cadence memory)
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
      model: 'sonnet',  // pin verifiers to sonnet (cap=2 throughput; post-barrier synth stays on inherited Opus)
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
4. "## Constraints carried" — never touch the marathon core; 9 KJV editions byte-stable; additive schema; atomic writes; 5-leg save per phase.
Return ONLY the Markdown.`,
    { label: 'synth:fixes-plan', phase: 'Synthesize' }
  )
}

const completeness = await agent(
  `${PREAMBLE}

This deep-audit round covered these dimensions: ${DIMENSIONS.map((d) => d.key).join(', ')}.
Findings per dimension (survived / total verified):
${DIMENSIONS.map((d) => { const v = verified.filter((f) => f.dimension === d.key); const s = v.filter((f) => !f.verdict.refuted); return `  ${d.key}: ${s.length}/${v.length}`; }).join('\n')}
Surviving finding titles: ${survivors.map((f) => f.title).join(' | ') || '(none)'}

As a COMPLETENESS CRITIC, identify what this round likely MISSED — a subtree/module/data-set not searched, an invariant not checked, a failure mode a single-pass finder would skip, or a dimension that returned suspiciously little. Return concrete gaps + a finder lens for each (these seed the next convergence round). Be specific to THIS codebase, not generic.`,
  { label: 'synth:completeness-critic', phase: 'Synthesize', schema: COMPLETENESS_SCHEMA, agentType: 'feature-dev:code-reviewer' }
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
