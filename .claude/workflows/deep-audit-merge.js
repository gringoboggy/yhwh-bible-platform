export const meta = {
  name: 'deep-audit-merge',
  description: 'Merge the two SPLIT-lane deep-audit results (win + mac) into ONE synthesized phased fixes plan (round 6). Paste each lane\'s survivors into the in-file constants below, then run on the N95.',
  phases: [{ title: 'Synthesize', detail: 'dedup the union of both lanes\' survivors -> one phased fixes plan + completeness critic' }],
}

// Runs on the N95 AFTER both lanes finish their split deep-audit (see
// docs/superpowers/plans/2026-06-08-round6-split-audit-plan.md). Workflow scripts have no
// filesystem access, so — like deep-audit-continue.js — each lane's survivors are
// pasted as in-file literals. Procedure:
//   1. win lane: JSON.parse(<win output>).result.survivors  -> paste into WIN_SURVIVORS
//   2. mac lane: pull branch lane-transfer/audit -> findings-mac.json .survivors -> MAC_SURVIVORS
//   3. run Workflow({scriptPath: '.../deep-audit-merge.js'}); write result.fixesPlanMarkdown to
//      docs/superpowers/notes/2026-06-08-round6-split-audit-findings.md
const REPO = 'C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4'
const ROUND = 6
const NOW = '2026-06-08'

// ============================================================================
// PASTE EACH LANE'S survivors[] HERE before running:
const WIN_SURVIVORS = [] // <- win lane: tests-run · opt-build · byte-stability · rx-surfaces
const MAC_SURVIVORS = [] // <- mac lane: the 12 read-only code-review dims
// ============================================================================

const rank = { critical: 4, high: 3, medium: 2, low: 1, info: 0, none: -1 }
const keyOf = (f) => ((f.file || '').toLowerCase().trim()) + '::' + ((f.title || '').toLowerCase().trim().slice(0, 90))
function dedupe(findings) {
  const seen = new Set(); const out = []
  for (const f of findings) { if (!f || !f.title) continue; const k = keyOf(f); if (seen.has(k)) continue; seen.add(k); out.push(f) }
  return out
}

const PREAMBLE = `You are finalizing the YHWH v2.4 deep-audit (round ${ROUND}, ${NOW}) — a SPLIT run merged on the N95: the win lane ran tests-run/opt-build/byte-stability/rx-surfaces (pytest + builds), the mac lane ran the 14 read-only code-review dims (incl. the round-6 dist-packaging + website-deploy). Repo root "${REPO}/". CONSTRAINTS: single-user LOCAL app (do NOT raise CSRF/rate-limit/hosting); KEEP PYTHON / no DB; the 9 KJV editions MUST build byte-stable (additive schema; writes via notes_io.atomic_write); never touch the off-limits marathon core (build_standalone.py, core/manuscript_*, GAPS/). Book count is 83 (the superset; never 87). ONE Bible ships; the Geez/Amharic standalones are a FUTURE update — out of scope. This is FINDINGS-ONLY: produce the merged plan, do NOT apply fixes.`

const all = dedupe([...WIN_SURVIVORS, ...MAC_SURVIVORS])
  .map((f) => ({ ...f, finalSeverity: f.severity || 'medium' }))
  .sort((a, b) => (rank[b.finalSeverity] ?? 0) - (rank[a.finalSeverity] ?? 0))
const bugSurv = all.filter((f) => f.kind !== 'optimization')
const optSurv = all.filter((f) => f.kind === 'optimization')

phase('Synthesize')
log(`merge: ${WIN_SURVIVORS.length} win + ${MAC_SURVIVORS.length} mac -> ${all.length} unique survivors`)

if (!all.length) {
  return { tool: 'deep-audit-merge', round: ROUND, now: NOW, survivors: [], fixesPlanMarkdown: 'No surviving findings across either lane — the 9-edition program audits clean.', completeness: [] }
}

const sevTally = all.reduce((a, f) => { a[f.finalSeverity] = (a[f.finalSeverity] || 0) + 1; return a }, {})
const COUNT_LINE = `ROUND ${ROUND} (SPLIT win+mac, merged): ${all.length} unique surviving findings. By severity: ${JSON.stringify(sevTally)}. Bug/correctness/etc = ${bugSurv.length}; optimization = ${optSurv.length}.`

const fixesPlanMarkdown = await agent(
  `${PREAMBLE}

You are SYNTHESIZING a phased fixes plan from the MERGED verified survivors of BOTH audit lanes (each already survived adversarial refutation in its own lane). Concise, actionable Markdown — no fluff.

AUTHORITATIVE COUNTS (use verbatim in the summary; do NOT recompute):
${COUNT_LINE}

VERIFIED BUG / CORRECTNESS / SECURITY / DEBT / TEST / DOC / RX FINDINGS (JSON):
${JSON.stringify(bugSurv, null, 1)}

VERIFIED OPTIMIZATION RECOMMENDATIONS (JSON):
${JSON.stringify(optSurv, null, 1)}

Sections:
1. "## Executive summary" — 3-5 sentences using the authoritative counts verbatim: how many, the most serious, and a direct verdict on whether the 9-edition program is MINT (works as intended) or what stands between it and mint.
2. "## Phased fixes" — group the bug findings into phases ordered SAFEST/MOST-FOUNDATIONAL FIRST (additive + guard-adding before behavior-changing; security + silent-data-loss highest priority). Per finding: a checkbox line with severity, title, file:line, the (corrected) fix, the test/guard to add, and whether it touches the build path (=> byte-stability proof obligation). Prefer a commit-time lint_rules check for invariants that recur.
3. "## Optimization decisions" — a table: Area | Verdict (confirmed-optimal / change) | Recommendation. Marathon-core off-limits; no-paid-API; byte-stability explicit.
4. "## Constraints carried" — never touch the marathon core; 9 KJV byte-stable; additive schema; atomic writes; 5-leg save per phase; Geez/Amharic standalone = future update.
Return ONLY the Markdown.`,
  { label: 'merge:fixes-plan', phase: 'Synthesize' }
)

const completeness = await agent(
  `${PREAMBLE}

The SPLIT audit merged ${all.length} survivors across the win lane (tests-run/opt-build/byte-stability/rx-surfaces) + the mac lane (the 12 code-review dims). Surviving titles: ${all.map((f) => f.title).join(' | ') || '(none)'}.
As a COMPLETENESS CRITIC, identify what the split likely MISSED — a subtree/module/invariant covered by neither lane, or a SEAM between the lanes (a build-path defect only the win lane could see crossed with a code concern only the mac lane could see), or a dimension that returned suspiciously little. Return concrete gaps + a finder lens for each. Specific to THIS codebase, not generic.`,
  { label: 'merge:completeness-critic', phase: 'Synthesize', schema: { type: 'object', additionalProperties: false, properties: { gaps: { type: 'array', items: { type: 'object', additionalProperties: false, properties: { area: { type: 'string' }, why: { type: 'string' }, suggested_lens: { type: 'string' } }, required: ['area', 'why', 'suggested_lens'] } } }, required: ['gaps'] } }
)

return {
  tool: 'deep-audit-merge', round: ROUND, now: NOW,
  counts: { survived: all.length, bySeverity: sevTally, bug: bugSurv.length, opt: optSurv.length },
  survivors: all,
  fixesPlanMarkdown,
  completeness: completeness && completeness.gaps ? completeness.gaps : [],
}
