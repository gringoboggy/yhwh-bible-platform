export const meta = {
  name: 'memory-reconcile',
  description: 'Cross-check every Claude memory file against the live repo + truth records; flag stale/contradicted claims (read-only, proposes fixes)',
  whenToUse: 'On demand when memory may have drifted from reality — after a big arc ships, after several audits, or when the user asks "does my memory still match the project". READ-ONLY: it proposes fixes; you/the user apply them. Pair the cheap deterministic check (dev/cc-hooks/memory_hygiene.py audit) with THIS deep semantic sweep.',
  phases: [
    { title: 'Scout', detail: 'enumerate the memory dir' },
    { title: 'Reconcile', detail: 'each agent checks a batch of memories vs the live repo' },
  ],
}

// --- config (edit in-file; args may not propagate — see [[reference_deep_audit_tool]]) ---
const MEM = 'C:/Users/bogda/.claude/projects/C--Users-bogda-Documents-YHWH-v2-4-full/memory'
const REPO = 'C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4'
const AGENTS = args?.agents ?? 8
const FOCUS = args?.focus ?? 'the latest dev/SESSION_STATE.md + dev/CHANGELOG.md entries, dev/IN_FLIGHT.md, and the recent git log — i.e. whatever shipped most recently'

const FILES_SCHEMA = {
  type: 'object',
  properties: { files: { type: 'array', items: { type: 'string' }, description: 'every *.md basename in the memory dir EXCEPT MEMORY.md and anything starting with _' } },
  required: ['files'],
}

const DRIFT_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      description: 'ONE entry per memory claim that is stale/contradicted OR uncertain. Do NOT list claims that match.',
      items: {
        type: 'object',
        properties: {
          memoryFile: { type: 'string' },
          claimQuoted: { type: 'string', description: 'the exact stale/uncertain sentence or figure' },
          verdict: { type: 'string', enum: ['stale', 'uncertain'] },
          whatChanged: { type: 'string' },
          evidence: { type: 'string', description: 'file:line or grep result proving current reality' },
          suggestedEdit: { type: 'string', description: 'the minimal edit to make the memory match reality' },
        },
        required: ['memoryFile', 'claimQuoted', 'verdict', 'whatChanged', 'evidence', 'suggestedEdit'],
      },
    },
    cleanFiles: { type: 'array', items: { type: 'string' } },
  },
  required: ['findings', 'cleanFiles'],
}

const GROUND = `GROUND TRUTH — check each memory claim against the LIVE repo at ${REPO} (Grep/Read the actual code, configs, and counts) and against ${FOCUS}.
Be CONSERVATIVE: only mark 'stale' when the live repo or a truth-record CLEARLY contradicts the memory; 'uncertain' when you cannot confirm either way. Quote the exact claim. IGNORE behavioral/preference memories (save semantics, terseness, pacing, RAM) UNLESS they contain a concrete factual claim (a count, a path, a function name, a status) that current reality falsifies. Watch especially for: stale counts (notes/tests/checks/dims/dirs), moved files (dev/ -> dev/archive/), renamed/deleted functions or modules, and status lines whose gating condition has since been met.`

phase('Scout')
const list = await agent(
  `List every memory file in ${MEM}. Use Glob on ${MEM}/*.md and return the basenames, EXCLUDING MEMORY.md and any file starting with "_".`,
  { label: 'scout:list-memory', phase: 'Scout', schema: FILES_SCHEMA, agentType: 'Explore' }
)
const files = (list?.files || []).filter((f) => f && f.endsWith('.md') && f !== 'MEMORY.md' && !f.startsWith('_'))
log(`memory-reconcile: ${files.length} memory files to check across ${AGENTS} agents`)
if (!files.length) return { error: 'no memory files found', memoryDir: MEM }

const batches = Array.from({ length: AGENTS }, (_, i) => files.filter((_f, idx) => idx % AGENTS === i)).filter((b) => b.length)

phase('Reconcile')
const results = await parallel(
  batches.map((batch, i) => () =>
    agent(
      `${GROUND}\n\nYour batch of memory files (read EACH fully, in ${MEM}/):\n${batch.map((f) => '- ' + f).join('\n')}\n\nFor each file, check every concrete factual claim against the live repo. Return ONLY drift (stale/uncertain) findings + the list of files whose every checkable claim MATCHES.`,
      { label: `reconcile:batch${i + 1}`, phase: 'Reconcile', schema: DRIFT_SCHEMA, agentType: 'general-purpose' }
    )
  )
)

const ok = results.filter(Boolean)
const findings = ok.flatMap((r) => r.findings || [])
const cleanFiles = ok.flatMap((r) => r.cleanFiles || [])
return {
  memoryDir: MEM,
  filesChecked: files.length,
  cleanCount: cleanFiles.length,
  driftCount: findings.length,
  stale: findings.filter((f) => f.verdict === 'stale').length,
  uncertain: findings.filter((f) => f.verdict === 'uncertain').length,
  findings,
  cleanFiles,
  note: 'READ-ONLY. Apply the suggestedEdits yourself (or have the user confirm deletions). Back up first: dev/cc-hooks/memory_hygiene.py backup.',
}
