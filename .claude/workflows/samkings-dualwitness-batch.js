export const meta = {
  name: 'samkings-dualwitness-batch',
  description: "Sam/Kings dual-witness Ge'ez draft-at-scale: 2 blind vision passes per witness, converge, collate, per chapter (agent path, Max subscription)",
  phases: [
    { title: 'Transcribe', detail: '2 blind Opus vision passes per witness (4/chapter)' },
    { title: 'Finalize', detail: 'converge -> assemble -> collate (deterministic CLI)' },
  ],
}

// ── run config ───────────────────────────────────────────────────────────────
// `args` do NOT reliably propagate to a Workflow on this harness (memory
// reference_deep_audit_tool), so the run config is read from a JSON file via a
// bootstrap agent. The controller WRITES this file before launching; edit
// CONFIG_PATH per environment (Windows N95 vs the Linux pod). Config shape:
//   { track, chapters:[{book,chapter,GG:{crops,source_images,folios,topologyPath?},CAM:{...}}],
//     finalize, sequential, outDir, py, repoRoot, maxChapters }
//   finalize:false  -> return the raw 4 passes/chapter (N95 proof; controller finalizes)
//   finalize:true   -> a finalize agent runs manuscript_finalize_chapter.py (pod, python3)
//   sequential:true -> blind passes one-at-a-time (MAX-1 heavy-vision; the 16 GB N95 OOM rule)
// Default = pod path (the controller writes this file before launching). The
// 2026-06-02 N95 1Ki1 proof used 'C:/Users/bogda/AppData/Local/Temp/yhwh-1ki1-proof/input.json'.
const CONFIG_PATH = '/workspace/samkings_batch_input.json'

// ── the transcription protocol (verbatim from run_manuscript_transcribe_at_scale._TRANSCRIBE_PROTOCOL) ──
const PROTOCOL = `You are transcribing an Ethiopic (Ge'ez) biblical manuscript folio. Produce
a faithful first-draft diplomatic transcription of EXACTLY what the
parchment inks — not what a printed Bible says it should say. Transcribe as
written, including scribal variants and apparent errors; flag uncertainty
rather than silently normalising.

Rules:
- Separate words with the black wordspace \` ፡ \` (U+1361, space-padded).
- Preserve the RED body cross \`✣\` (U+2723) as its own glyph in the geez
  where it appears between words — do NOT collapse it to \`፡\` and do NOT
  promote it to a fidel like \`እ\`. Rubric crosses \`❈\` are rubric-only.
- Read column by column, line by line. Note line-break splits: a word
  broken across a line/column boundary is ONE token, not two.
- For each verse give: \`v\` (number), \`column\` (e.g. "f030v-M-L23" =
  folio-column-line), \`line_start\`, the \`geez\` string, and \`uncertain[]\`
  entries (marker ∈ uncertain|damaged|illegible) for anything you cannot
  read confidently. Be honest about resolution limits.
- Do NOT output a \`tokens\` field — it is computed downstream from \`geez\`.
Return ONLY the structured JSON of the required schema.

Honesty contract (load-bearing, travels with every pass):
- (q) If you cannot resolve a glyph, MARK IT uncertain — never recite the
  expected/standard text to fill a gap. A pass that recites instead of reads
  is rejected.
- (u) Verify verse ENDINGS, not just glyphs: do NOT add clauses the parchment
  lacks (no harmonizing toward the MT / a printed Bible).
- (v) Even a glyph you are confident about is transcribed as INKED, not as it
  "should" be — load-bearing glyphs are read off the parchment.`

// ── the output schema (verbatim from TRANSCRIBE_OUTPUT_SCHEMA) ────────────────
const SCHEMA = {
  type: 'object',
  properties: {
    verses: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          v: { type: 'integer' },
          column: { type: 'string' },
          line_start: { type: 'integer' },
          geez: { type: 'string' },
          uncertain: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                token_index: { type: 'integer' },
                marker: { type: 'string', enum: ['uncertain', 'damaged', 'illegible'] },
                note: { type: 'string' },
              },
              required: ['token_index', 'marker', 'note'],
              additionalProperties: false,
            },
          },
        },
        required: ['v', 'column', 'line_start', 'geez', 'uncertain'],
        additionalProperties: false,
      },
    },
    transcription_notes: { type: 'string' },
  },
  required: ['verses', 'transcription_notes'],
  additionalProperties: false,
}

const FINALIZE_SCHEMA = {
  type: 'object',
  properties: {
    needs_qa: { type: 'boolean' },
    gg_convergence_pct: { type: 'number' },
    cam_convergence_pct: { type: 'number' },
    gg_valid: { type: 'boolean' },
    cam_valid: { type: 'boolean' },
    collation_ok: { type: 'boolean' },
    base_witness: { type: 'string' },
    verse_count: { type: 'integer' },
    raw: { type: 'string', description: 'the finalize CLI stdout JSON, verbatim' },
  },
  required: ['needs_qa', 'collation_ok', 'raw'],
  additionalProperties: true,
}

function blindPass(ch, witness, passId) {
  const w = ch[witness]
  const topo = w.topologyPath
    ? `\nBefore transcribing, Read the witness topology at ${w.topologyPath} (known scribal-hand failure classes for ${witness}) and watch for them.`
    : ''
  return agent(
    `${PROTOCOL}${topo}\n\n` +
      `Transcribe ${ch.book} chapter ${ch.chapter}, witness ${witness}. ` +
      `Read these folio crop PNG(s) in order with the Read tool, then output every verse you can read on them:\n` +
      w.crops.map((p) => `- ${p}`).join('\n'),
    { label: `${ch.book}${ch.chapter}:${witness}:${passId}`, phase: 'Transcribe', schema: SCHEMA },
  )
}

// ── bootstrap: read the run config from CONFIG_PATH (args-propagation workaround) ──
const _cfg = await agent(
  `Use the Read tool to read the file at ${CONFIG_PATH}. It is JSON. Return its EXACT raw text contents in the "raw" field — do not summarize, reformat, or wrap it in markdown fences.`,
  { label: 'load-config', phase: 'Transcribe', schema: { type: 'object', properties: { raw: { type: 'string' } }, required: ['raw'], additionalProperties: false } },
)
let _raw = (_cfg.raw || '').trim()
if (_raw.startsWith('```')) _raw = _raw.replace(/^```[a-z]*\n?/i, '').replace(/\n?```$/, '').trim()
const cfg = JSON.parse(_raw)
log(`config loaded: track=${cfg.track} chapters=${(cfg.chapters || []).length} finalize=${cfg.finalize !== false} sequential=${!!cfg.sequential}`)

const PY = cfg.py || 'python3'
const FINALIZE = cfg.finalize !== false
const SEQUENTIAL = !!cfg.sequential
const chapters = (cfg.chapters || []).slice(0, cfg.maxChapters || 999)

const results = await pipeline(
  chapters,
  // Stage 1 — four independent blind passes (2 per witness). parallel() => true
  // independence (pod). sequential => one-at-a-time (MAX-1 heavy-vision N95).
  async (ch) => {
    const tasks = [
      () => blindPass(ch, 'GG', 'A'),
      () => blindPass(ch, 'GG', 'B'),
      () => blindPass(ch, 'CAM', 'A'),
      () => blindPass(ch, 'CAM', 'B'),
    ]
    let ggA, ggB, camA, camB
    if (SEQUENTIAL) {
      ggA = await tasks[0]()
      ggB = await tasks[1]()
      camA = await tasks[2]()
      camB = await tasks[3]()
    } else {
      ;[ggA, ggB, camA, camB] = await parallel(tasks)
    }
    return { ch, passes: { ggA, ggB, camA, camB } }
  },
  // Stage 2 — finalize (deterministic) or hand the raw passes back to the controller.
  async (r) => {
    const { ch, passes } = r
    const { ggA, ggB, camA, camB } = passes
    if (!ggA || !ggB || !camA || !camB) {
      return { ch: { book: ch.book, chapter: ch.chapter }, error: 'a blind pass returned null', passes }
    }
    if (!FINALIZE) {
      return { ch: { book: ch.book, chapter: ch.chapter }, passes }
    }
    const payload = JSON.stringify({
      track: cfg.track,
      book: ch.book,
      chapter: ch.chapter,
      gg: { a: ggA, b: ggB, source_images: ch.GG.source_images, folios: ch.GG.folios },
      cam: { a: camA, b: camB, source_images: ch.CAM.source_images, folios: ch.CAM.folios },
    })
    const outArg = cfg.outDir ? ` --out-dir ${JSON.stringify(cfg.outDir)}` : ''
    const cd = cfg.repoRoot ? `cd ${JSON.stringify(cfg.repoRoot)} && ` : ''
    return agent(
      `Finalize one dual-witness chapter deterministically. Do EXACTLY this with the Bash tool, nothing more:\n` +
        `1. Write this JSON to a temp file /tmp/${ch.book}${ch.chapter}_payload.json (use a heredoc so it is byte-exact):\n` +
        `\`\`\`json\n${payload}\n\`\`\`\n` +
        `2. Run: ${cd}${PY} scripts/manuscript_finalize_chapter.py${outArg} < /tmp/${ch.book}${ch.chapter}_payload.json\n` +
        `3. Return the command's stdout JSON verbatim in the \`raw\` field, and copy needs_qa / *_convergence_pct / *_valid / collation_ok / base_witness / verse_count out of it into the matching fields.`,
      { label: `finalize:${ch.book}${ch.chapter}`, phase: 'Finalize', schema: FINALIZE_SCHEMA },
    )
  },
)

const clean = results.filter(Boolean)
return { chapters: clean, finalize_mode: FINALIZE, config_chapters: chapters.length }
