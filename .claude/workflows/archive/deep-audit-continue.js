export const meta = {
  name: 'deep-audit-continue',
  description: 'Continue the killed mint-10 deep-audit (run wf_ba367edc-a4a): verify the 46 recovered candidate findings, run the 4 finders that never completed, then synthesize. Verify-first so slow finders cannot starve verification the way they did last night.',
  phases: [
    { title: 'VerifyRecovered', detail: 'Adversarially verify (default-refuted) the 46 recovered candidate findings from the 15 completed finder agents' },
    { title: 'FindMissing', detail: 'Run the finders that never completed: cross-module#1 (book-code angle) + opt-build + opt-ingest + opt-render' },
    { title: 'VerifyMissing', detail: 'Adversarially verify the newly-found candidates' },
    { title: 'Synthesize', detail: 'Dedup, severity-calibrate, phased fixes plan (authoritative counts) + completeness critic' },
  ],
}

// ============================================================================
// Recovery context — this is a CONTINUATION of mint-10 round 3.
// The original run (wf_ba367edc-a4a) completed the FIND phase for 11 of 15
// dimensions (46 candidate findings, recovered from the agent transcripts) but
// was killed before ANY verify or synth ran. We inject the recovered candidates
// and only run what is missing.
// ============================================================================
const REPO = 'C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4'
const DEPTH = 'deep'
const ROUND = 3
const NOW = '2026-06-01'

const rank = { critical: 4, high: 3, medium: 2, low: 1, info: 0, none: -1 }

const DEFERRED_BY_DESIGN = [
  'ex.py -> exo.py rename for the 4 Tewahedo translation stores (geez/amharic + -en): DEFERRED to the tau.G standalone-build wiring. The data is latent (no live consumer until the standalone editions are wired). Do NOT propose the rename now; an additive _book_path alias is the only acceptable early action, and even that is optional. Re-flagging the rename as a NEW finding is wrong.',
  'aes (Esther-Greek-additions) notes at KJV chapters 11-16 are uninjectable because the base HTML only renders chapters 1-10: this is a PARKED known-residual (roadmap "Parked / known-residual"), editorial not mechanical, guarded by html_chapter_count at the promote boundary. Re-flagging it as a NEW bug is wrong.',
  'zip compresslevel 9->6: DECLINED on the merits (enlarges every EPUB 1-3% to save ~30s/build; quality output > build speed). Do NOT re-propose it.',
  'Splitting scripts/web.py or scripts/build_edition.py for size alone: DECLINED (large files of small cohesive functions). CSRF / rate-limiting / public-server hardening: OUT OF SCOPE (single-user local app).',
]

// ----------------------------------------------------------------------------
// Schemas (identical to deep-audit.js)
// ----------------------------------------------------------------------------
const FINDINGS_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
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
  type: 'object', additionalProperties: false,
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
  type: 'object', additionalProperties: false,
  properties: {
    gaps: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
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
// Shared orientation preamble (identical to deep-audit.js)
// ----------------------------------------------------------------------------
const PREAMBLE = `You are auditing the YHWH v2.4 Bible-publishing platform. The repo root is "${REPO}/" relative to your working directory; ALL file paths you cite must be under it (e.g. ${REPO}/scripts/web.py). Read files yourself; do not guess.

Fast orientation (read what you need):
- ${REPO}/dev/MATRIX_MAP.md   = data-flow map (config -> loaders -> matrix/build/inject -> consumers) + the base-HTML structure. Use this to find where things live; never grep blind.
- ${REPO}/dev/REPO_MAP.md     = file/folder index.
- ${REPO}/dev/CLAUDE_PROJECT_RULES.md = conventions (S7 code: lru_cache discipline, ast.literal_eval-not-exec, atomic writes; S6 UI: canonical book/chapter order; S8 tests; S9 mental models).
- ${REPO}/dev/SESSION_STATE.md = current snapshot (read it for what just shipped; this is deep-audit round ${ROUND}).

ALREADY-SETTLED / DEFERRED-BY-DESIGN (round ${ROUND} runs AFTER prior rounds' fixes — do NOT re-report these as new findings; a verifier MUST refute a finding that merely re-raises one of them):
${DEFERRED_BY_DESIGN.map((d, i) => `  ${i + 1}. ${d}`).join('\n')}
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
// RECOVERED candidate findings (46) from the killed run's 15 completed finders.
// Injected as a raw JSON literal; `kind` is derived from `dimension` below.
// ----------------------------------------------------------------------------
const RECOVERED_RAW = [
  {
    "dimension": "correctness",
    "severity": "high",
    "title": "`_iter_note_ref_attribution_years` skips all 8-field (legacy) notes — `time_filter_ceiling` silently defeated for bulk corpus",
    "file": "scripts/build_edition.py",
    "line": "341",
    "evidence": "```python\nfor tup in notes:\n    if not isinstance(tup, tuple) or len(tup) < 9:\n        continue\n    ...attribution = tup[8] or \"\"\n```\nThe minimum valid note tuple is 8 fields (the legacy form, used by the majority of the 67,715-note corpus during the migration phase). The guard `len(tup) < 9` silently skips every 8-field note, so `_iter_note_ref_attribution_years` yields nothing for them. `compute_time_filtered_html_ref_ids` therefore never adds those notes to the disabled-ref-id set, regardless of the edition's `time_filter_ceiling`. The intended behaviour — treat notes with no attribution as 'year=None → contemporary → filter out under any ceiling' — is documented in the function's own docstring but never executes for legacy notes. The sibling function `_iter_note_ref_traditions` (line 144 of the same file) correctly uses `len(tup) < 8` and handles the optional 9th field explicitly. Checked both iterator helpers in this file; this is the only one with the wrong guard.",
    "fix": "Change line 341 from `if not isinstance(tup, tuple) or len(tup) < 9:` to `if not isinstance(tup, tuple) or len(tup) < 8:`. Then change the attribution read on line 346 from `attribution = tup[8] or \"\"` to `attribution = (tup[8] if len(tup) > 8 else \"\") or \"\"`. This mirrors the 8-vs-9 pattern used everywhere else in the codebase and in `_iter_note_ref_traditions`."
  },
  {
    "dimension": "correctness",
    "severity": "high",
    "title": "`_append_cloned_edition` omits `enabled_categories`, `enabled_kinds`, `disabled_kinds`, and `max_phase` — cloned edition ships 0 notes",
    "file": "scripts/api/editions.py",
    "line": "120-194",
    "evidence": "`_append_cloned_edition` copies only scalar and popup/tradition list fields (lines 135–189). It never copies `enabled_categories`, `enabled_kinds`, `disabled_kinds`, or `max_phase` from the source edition. `enabled_kind_codes` (the canonical resolver for both the matrix and the EPUB build) returns an empty set when both `enabled_categories` and `enabled_kinds` are empty (gate 4: `if code in explicit_enabled or k.get('category') in enabled_cats:` — both empty → nothing passes). A cloned edition therefore immediately produces 0 notes in the build and the matrix UI. Verified against `content/editions.yaml`: every edition relies on `enabled_categories` as its primary gate; without it, `compute_enabled_kinds` returns `(set(), all_codes)` — all kinds disabled. No post-clone `api_save_edition` call compensates for the omission. No tests exist for this code path.",
    "fix": "Add the four missing fields to `_append_cloned_edition`. `enabled_categories`, `enabled_kinds`, and `disabled_kinds` are list fields; `max_phase` and `enable_ai_notes` are scalars. In the scalar_fields list (around line 135), append `(\"max_phase\", src.get(\"max_phase\", \"\"))` and `(\"enable_ai_notes\", src.get(\"enable_ai_notes\", False))`. In the list_fields block (around line 163), append three entries: `if src.get(\"enabled_categories\"): list_fields.append((\"enabled_categories\", list(src[\"enabled_categories\"])))` and similarly for `enabled_kinds` and `disabled_kinds`. This preserves the source edition's full kind-filter state in the clone."
  },
  {
    "dimension": "correctness",
    "severity": "high",
    "title": "time_filter_ceiling silently ignores all legacy 8-field notes (they always survive any temporal filter)",
    "file": "scripts/build_edition.py",
    "line": "341",
    "evidence": "In `_iter_note_ref_attribution_years`, line 341: `if not isinstance(tup, tuple) or len(tup) < 9: continue`. Any 8-field legacy note tuple (which has no attribution field) is silently skipped — it is never yielded, so it is never added to the `disabled_html_ref_ids` set inside `compute_time_filtered_html_ref_ids`. The docstring for that function explicitly states: 'adds the ref-id to the output set if EITHER: the year is None (contemporary content like \"User original\" — a 1900 reader wouldn't have had it), OR the year is strictly greater than the ceiling.' The 8-field notes have no attribution, so `lookup_year(\"\")` returns `None`, which satisfies the year-is-None condition — they should be excluded. Instead they are invisible to the filter and always survive. This contradicts the filter's own contract. Today `time_filter_ceiling` is `null` for all editions so the defect is latent; once any edition sets a positive integer ceiling, a large fraction of the corpus (however many notes lack a 9th field) will silently slip through.",
    "fix": "Change the guard to include 8-field tuples in the iteration. Replace:\n  `if not isinstance(tup, tuple) or len(tup) < 9: continue`\nwith:\n  `if not isinstance(tup, tuple) or len(tup) < 5: continue`\nThen derive attribution as:\n  `attribution = (tup[8] if len(tup) >= 9 else None) or \"\"`\nThis mirrors `_iter_note_ref_traditions` which already uses `len(tup) < 8` as its guard and processes all valid note shapes."
  },
  {
    "dimension": "correctness",
    "severity": "medium",
    "title": "batch_insert_notes silently drops notes that fail coord_in_canonical_extent with no log or count",
    "file": "scripts/promote.py",
    "line": "354-358",
    "evidence": "In `batch_insert_notes`, lines 354-358:\n  `if not coord_in_canonical_extent(book_path.stem, ch, v):\n      continue  # boundary guard: drop impossible coordinates`\n  `_html_chs = html_chapter_count(book_path.stem)`\n  `if _html_chs and ch > _html_chs:\n      continue  # base-HTML extent guard`\nBoth guards silently `continue` with no warning, no counter increment, and no return to the caller. The caller (`batch_insert_notes`) returns the count of inserted notes but has no way to communicate how many were dropped by these guards. By contrast, the missing-chapter/verse guard a few lines earlier (lines 346-350) emits `warnings.warn(...)` so the drop is visible. For the at-scale ingest pipelines that call `batch_insert_notes` in bulk (e.g. Nave's, Torrey, xref), a systematic off-by-one in the coordinate guard would drop thousands of notes invisibly — the operator sees a lower-than-expected inserted count with no diagnostic.",
    "fix": "Add a `dropped` counter and emit a `warnings.warn` (or `logging.warning`) at function exit when any notes were dropped by either guard. For example, increment a `dropped` counter at each `continue` and at the end of the loop:\n  `if dropped:\n      warnings.warn(f'batch_insert_notes: dropped {dropped} note(s) for {book_path.stem!r} due to out-of-extent coordinates', stacklevel=2)`\nThis matches the existing pattern for the missing-chapter/verse case and keeps the silence deliberate rather than accidental."
  },
  {
    "dimension": "correctness",
    "severity": "medium",
    "title": "_chapter_from_id parses IDs using parts[-3] which is wrong for multi-part book codes containing hyphens",
    "file": "scripts/promote.py",
    "line": "494-497",
    "evidence": "The ID format emitted by `candidate_to_dict` is `f\"{c.book}-{c.chapter}-{c.verse}-{idx:03d}\"` (at_scale_base.py:130). `_chapter_from_id` at promote.py:496 splits on `-` and takes `parts[-3]`. For a book code like `lxx-brenton-english` (a translation ID — not currently a candidate source book, but book codes like `1en`, `4ba` etc. don't have hyphens), or hypothetically `bar` (fine), the split is correct. However, the id for a book like `1co` chapter 13 verse 1 would be `1co-13-1-001` → parts `['1co', '13', '1', '001']` → parts[-3] = `'13'`. That is correct. But if any at-scale driver ever passes a composite id whose book segment contains a hyphen, the parse silently picks the wrong component. The real risk is the fallback path: `promote_candidate` at line 435 calls `c.get(\"chapter\") or _chapter_from_id(c[\"id\"])`. If `c[\"chapter\"]` is explicitly 0 (falsy but valid — impossible since chapters start at 1, but defensively) or if \"chapter\" is missing from a malformed queue entry, it falls to `_chapter_from_id` which would then crash with an `IndexError` or return a wrong chapter if the id has extra hyphens. The `or` operator treats 0 as falsy, and `c.get(\"chapter\")` returns 0 only if explicitly set to 0, which should not happen but is not guarded.",
    "fix": "Make `_chapter_from_id` more robust by parsing right-to-left with a fixed split count: `_, ch_str, v_str, idx_str = cid.rsplit('-', 3)` — this tolerates any number of hyphens in the book segment. Also replace `c.get(\"chapter\") or _chapter_from_id(c[\"id\"])` with `c.get(\"chapter\") if c.get(\"chapter\") is not None else _chapter_from_id(c[\"id\"])` to avoid the falsy-zero footgun."
  },
  {
    "dimension": "correctness",
    "severity": "medium",
    "title": "apply_chapter_decoration and apply_bilingual_toc write to temp-dir files without atomic_write, risking corrupt EPUB on build interruption",
    "file": "scripts/build_edition.py",
    "line": "1588, 1733, 1906",
    "evidence": "Three separate passes over the temp-dir HTML files use `fpath.write_text(new_text, encoding=\"utf-8\")` and `f.write_text(new_text, encoding=\"utf-8\")` directly (lines 1588, 1733, 1906). These are in the temp build dir (not the corpus), so there is no corpus integrity risk. However, the `build_one` function has no crash-recovery mechanism: if the process is interrupted between a successful `shutil.copytree` and the final `build_epub.package_epub(...)`, the next build call re-copies the tree from `EPUB_DIR` (clean) — so the interrupted temp dir is abandoned and the defect is practically benign. No finding warranting immediate action beyond the documentation inconsistency (other writes in the same pipeline use `atomic_write`).",
    "fix": "No immediate action required; these writes are in an ephemeral `tempfile.TemporaryDirectory()` block (line 2813) so abandonment on crash is safe. If the build-pipeline is later refactored to use a persistent staging dir, switch these to `atomic_write`."
  },
  {
    "dimension": "correctness",
    "severity": "low",
    "title": "run_naves_at_scale and run_xref_at_scale write candidate counts as candidates_written += len(chapter_candidates) but that counts pre-dedup candidates, not the number actually appended",
    "file": "scripts/run_naves_at_scale.py",
    "line": "117-121",
    "evidence": "In `run_naves_for_book`, lines 117-121:\n  `out = write_queue(book, chapter, chapter_candidates)\n  if out:\n      files_written += 1\n      candidates_written += len(chapter_candidates)`\n`write_queue` returns `None` when all candidates deduplicate against the existing queue (\"nothing new to add\"). In that case `if out:` is False and `candidates_written` is not incremented — that part is correct. But when `out` is non-None, `candidates_written` is incremented by `len(chapter_candidates)` (the INPUT list) rather than `len(new_dicts)` (the actually-written list after deduplication inside `write_queue`). So the reported count is inflated whenever re-running with existing candidates in the queue. The same pattern exists in `run_xref_at_scale.py` at line 120-121. This is a cosmetic display issue (the stat is only printed, never consumed as logic), but it can mislead operators about how many new candidates were generated.",
    "fix": "Have `write_queue` return the count of newly appended candidates (len(new_dicts)) instead of the path, or return a `(path_or_none, n_appended)` tuple so the caller can use the accurate count. Alternatively, change the stats line to `candidates_written += len(chapter_candidates)` only when the queue was brand-new (no existing), and 0 otherwise — but returning the count from `write_queue` is cleaner. The same fix applies to `run_xref_at_scale.py`."
  },
  {
    "dimension": "security",
    "severity": "medium",
    "title": "WLC trusted-HTML ingest missing the <>&-character guard present on sibling sources",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/scripts/extract_wlc_morphhb.py",
    "line": "216-235",
    "evidence": "The `write_book_module` function writes WLC verses that are passed raw (unescaped) into the EPUB because `popup_versions._TRUSTED_HTML` contains `\"wlc\"`. Both sibling extractors that also live in `_TRUSTED_HTML` enforce an ingest-time guard: `extract_lxx_swete.py` lines 164-170 and `extract_byzantine_nt.py` lines 87-93 both iterate over every verse and `raise ValueError` if any verse text contains `<`, `>`, or `&`. The WLC extractor has no equivalent check. Its `verse_to_em_html` structurally can only emit `<em>text</em>` from OSIS `<w>` elements, so the current corpus is safe — but a source-level corruption or future OSIS variant that slips an unexpected character through `_word_text` would write unescaped HTML into a trusted-html store, and at render time `generate_verse_popups.py:43` (`body = text if v.get('trusted_html') else _html.escape(text)`) would pass it raw into the EPUB without sanitization. All 3 sites in `_TRUSTED_HTML` were checked; only WLC lacks the guard.",
    "fix": "Add the same `<>&` precondition check to `write_book_module` in `extract_wlc_morphhb.py` immediately before the file-write loop, mirroring the pattern already in both sibling extractors:\n```python\nfor c, v, t in sorted(verses, key=lambda r: (r[0], r[1])):\n    if any(ch in t for ch in \"<>&\"):\n        raise ValueError(\n            f\"wlc {book_code} {c}:{v}: trusted-html verse contains HTML-special \"\n            f\"character (<>&) but is rendered raw; refusing to write. Text: {t[:80]!r}\"\n        )\n```\nPlace this loop before the `lines` list build so disk is never mutated on a violation."
  },
  {
    "dimension": "security",
    "severity": "low",
    "title": "audit_log._summarize_args redacts sensitive kwargs by name but leaves positional args unredacted",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/scripts/core/audit_log.py",
    "line": "284-294",
    "evidence": "The `_summarize_args` function at lines 288-294 iterates `kwargs.items()` and applies the `_REDACT_KEYS` case-insensitive check — but the positional-args branch at lines 285-287 calls `_short_repr(a)` on each arg without any key-based redaction: `summary['args'] = [_short_repr(a) for a in args]`. Any future `@audit_endpoint`-decorated function that receives a secret (token, api_key, password) as a positional argument would log it. Currently all 15 decorated functions are safe because string positional args are edition_ids / kind_codes / source_ids (non-sensitive), and dict positional args (TOTP payload in `api_auth_totp_confirm`) are summarized as `{\"<dict>\": \"N keys\"}` by `_short_repr`. The gap is latent: a contributor adding e.g. `@audit_endpoint\\ndef api_rotate_token(new_token: str)` would silently log the token value up to 200 chars. All 15 files containing `@audit_log.audit_endpoint` were checked.",
    "fix": "Apply the same redaction logic to positional args: inspect each positional arg value against _REDACT_KEYS using its parameter name if available (from `fn.__code__.co_varnames`), or at minimum replace any `str` arg that looks like a secret (matches REDACT pattern in its repr) with `\"[REDACTED]\"`.\n\nMinimally safe fix — in `_summarize_args`, after building the positional reprs, check if any of the wrapped function's parameter names at those positions are in `_REDACT_KEYS`:\n```python\n# In audit_endpoint's _wrapper, pass fn.co_varnames to _summarize_args\ndef _summarize_args(args, kwargs, param_names=()):\n    summary = {}\n    for i, a in enumerate(args):\n        pname = param_names[i] if i < len(param_names) else str(i)\n        if pname.lower() in _REDACT_KEYS:\n            summary[pname] = \"[REDACTED]\"\n        else:\n            summary[pname] = _short_repr(a)\n    ...\n```\nThen call as `_summarize_args(args, kwargs, fn.__code__.co_varnames)` in the wrapper."
  },
  {
    "dimension": "security",
    "severity": "medium",
    "title": "Server error messages containing user-supplied field values reflected into innerHTML without escaping",
    "file": "scripts/templates/customize.py",
    "line": "1364, 1441, 1791",
    "evidence": "Line 1364: `status.innerHTML = \\`<span class=\"text-red-600\">✗ ${result.error}</span>\\`` and line 1441: `status.innerHTML = \\`<span class=\"text-red-600\">✗ ${msg}</span>\\`` where `msg = data.error`. Server-side handlers in `scripts/api/editions.py` generate error strings that embed user-supplied values via Python repr, e.g. line 633: `return {\"error\": (f\"unknown title_page_style: {v!r}; valid: {sorted(TITLE_PAGE_STYLES)}\")}` where `v = payload[\"title_page_style\"]`. A value like `'><img src=x onerror=fetch(\"http://evil\")>` would reach the innerHTML interpolation. The strict CSP script-src nonce blocks dynamically injected <script> tags but inline event handlers on injected elements (onerror, onclick etc.) are also restricted by the same nonce-based script-src policy in Chromium/Firefox. Pattern recurs at export.py line 502: `status.innerHTML = \\`<div ...>✗ ${data.error || 'build failed'}</div>\\``.",
    "fix": "Apply escapeHTML (already defined and available via window.escapeHTML in every console via the UI defense prelude) to all server-sent error strings before innerHTML interpolation. Replace `${result.error}` with `${escapeHTML(result.error || '')}` at all three sites in customize.py and at export.py line 502. Same fix at sources.py line 485 (`${data.error}` → `${escapeHTML(data.error || '')}`)."
  },
  {
    "dimension": "security",
    "severity": "medium",
    "title": "Corpus-sourced note fields (suffix, anchor) interpolated into innerHTML without HTML-escaping in audit and sources consoles",
    "file": "scripts/templates/audit.py",
    "line": "234",
    "evidence": "Line 234 in renderIssues(): `<span class=\"verse-anchor text-xs text-slate-500\">${n.book} ${n.chapter}:${n.verse}${n.suffix || ''}</span>` — `n.suffix` comes from corpus notes tuple field[2] via `api_attribution_audit` → `_compute_attribution_audit_uncached`. The `escapeHTML` function is defined in this same file (line 247) and used on line 240 for `n.body_preview`, but NOT applied to `n.suffix`. Likewise, in `scripts/templates/sources.py` line 553: `${n.chapter}:${n.verse}${n.suffix || ''}${n.anchor ? ` ${n.anchor}` : ''}` — both `n.suffix` and `n.anchor` are unescaped. In practice suffix values are short alphanumeric discriminators (\"a\", \"b\", \"intro\") and anchor values are programmatic identifiers (\"ge1-1\"), but they are corpus data, not config, and a corrupted or adversarially-crafted notes file could inject HTML. The CSP nonce mitigates script execution.",
    "fix": "Apply escapeHTML to all corpus-sourced fields before innerHTML interpolation. In audit.py line 234: `${n.suffix ? escapeHTML(n.suffix) : ''}`. In sources.py line 553: `${n.suffix ? escapeHTML(n.suffix) : ''}${n.anchor ? ` ${escapeHTML(n.anchor)}` : ''}`. Also apply escapeHTML to `n.kind` (line 555 in sources.py uses it unescaped: `<span ...>${n.kind}</span>`), `n.category_symbol` (line 554), and `n.category_label` (used as a title attribute)."
  },
  {
    "dimension": "security",
    "severity": "low",
    "title": "Content-Disposition filename in export download route sets unescaped URL-captured filename in attachment header",
    "file": "scripts/web.py",
    "line": "1580-1583",
    "evidence": "Route at line 1570: `m = re.match(r\"^/api/export/download/([\\w.-]+)$\", path)` then at line 1580: `self.send_header(\"Content-Disposition\", f'attachment; filename=\"{m.group(1)}\"')`. The route-level regex `[\\w.-]+` allows only word chars, dots, and hyphens — no `\"` or `;`. The subsequent `api_download_export` function applies a strict allowlist pattern so only valid EPUB/ZIP names survive. However, the route regex `[\\w.-]+` does allow adjacent dots (`..`) which makes the route-level validation weaker than the handler-level validation. The two-layer validation is correct but the gap between the permissive route regex and the strict handler-level pattern creates structural inconsistency: if the handler-level check is ever relaxed, the route level provides no backstop. Additionally, `\\w` in Python regex matches Unicode word characters (`\\w` with default flags includes non-ASCII), so non-ASCII filenames matching `[\\w.-]+` would pass the route check but fail the handler's `[a-z0-9]` pattern — this produces a correct 400 but obscures the intent.",
    "fix": "Tighten the route-level regex to match the handler's intended patterns: use `r\"^/api/export/download/([A-Za-z0-9_.:-]+)$\"` to restrict to ASCII alphanumeric + safe filename chars only, removing the Unicode `\\w` ambiguity. This makes the route a pre-filter that matches the same character class the handler's allowlist accepts, eliminating the gap."
  },
  {
    "dimension": "security",
    "severity": "low",
    "title": "version parameter in api_export_build is unvalidated before being passed to subprocess and embedded in glob pattern",
    "file": "scripts/api/exports.py",
    "line": "120-165",
    "evidence": "`api_export_build(edition_id, version)` at line 120 accepts `version` from `payload.get('version', 'v28a')` with no validation. Line 165: `'--version', version` passes it as a CLI argument (list form — no shell injection). Line 225: `pattern = f\"Ethiopian_Bible_{edition_id}_{version}_*.epub\"` — a `version` containing glob metacharacters (`*`, `?`, `[`) would alter the glob pattern used to find the output file. For example `version=\"v28a_*\"` would create pattern `Ethiopian_Bible_<id>_v28a_*_*.epub` which could match unintended files in EXPORTS_DIR. While confined to the exports directory and only affecting file discovery (not reading outside it), it could return wrong EPUB files.",
    "fix": "Add a version validation guard before the subprocess call: `if not re.match(r'^[a-z0-9._-]{1,32}$', version or ''): return {'error': 'invalid version format'}`. The same pattern is already used in `scripts/core/snapshots.py:_validate_version`. Alternatively, import and reuse `_validate_version` from that module."
  },
  {
    "dimension": "code-debt",
    "severity": "medium",
    "title": "write_queue copy-pasted verbatim across 4 at-scale drivers — mint-9 fix applied to 4 of 8 sites, stale at_scale_base docstring",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/scripts/run_xref_at_scale.py",
    "line": "40-83",
    "evidence": "After mint-9 #9 added the triple-key dedup `seen = {(c.get(\"verse\"), c.get(\"kind\"), c.get(\"draft_body\")) for c in existing}` guard, the `write_queue` bodies in run_xref_at_scale.py (lines 40–83), run_naves_at_scale.py (lines 41–86), run_torrey_at_scale.py (lines 41–82), and run_ethiopian_at_scale.py (lines 49–96) became near-identical — same dedup logic, same payload shape, differing only in the `except` clause breadth (`except Exception` vs `except (json.JSONDecodeError, OSError)`). The at_scale_base.py docstring at line 8 still says '``write_queue`` is deliberately NOT here — each driver has its own append / dedup / overwrite semantics', which was true at mint-7 but is now stale. Project memory explicitly records that an incomplete 1-of-2 fix to these driver bodies caused two mint-9 re-surfacings. All 4 sites checked: confirmed identical in functional logic.",
    "fix": "Extract the shared dedup-append logic into `at_scale_base.append_candidates(out_path, candidates, *, except_broad=False) -> Path | None` that encapsulates the read-existing / triple-key-dedup / sequential-id / atomic-write steps. Each of the 4 drivers becomes a 2-line call. Update the at_scale_base docstring to reflect that `write_queue` IS now extractable for the accumulator-style drivers (xref/naves/torrey/ethiopian) while Hebrew, Greek, AI-notes, AI-xrefs keep their kind-replace write_queue locally (genuinely different semantics). kenyon keeps its own because of the extra full-re-index step. This closes the 4-site duplication without touching the drivers whose semantics genuinely differ."
  },
  {
    "dimension": "code-debt",
    "severity": "medium",
    "title": "_normalize_book_code missing from --books CLI path in 4 of 8 at-scale drivers (★BUGCLUSTER incomplete fix)",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/scripts/run_ai_xrefs_at_scale.py",
    "line": "269",
    "evidence": "mint-7 added `books = [sources._normalize_book_code(b) for b in books]` in the `main()` of run_xref_at_scale.py (line 149), run_naves_at_scale.py (line 154), run_torrey_at_scale.py (line 190), and run_ethiopian_at_scale.py (line 159) — each with the comment 'Defense-in-depth: canonicalize legacy codes (mint-7 ★BUGCLUSTER)'. The same normalization call is absent from run_ai_xrefs_at_scale.py (`books = resolve_books(args.books)`, line 269), run_ai_notes_at_scale.py (analogous `resolve_books` call), run_hebrew_at_scale.py (line 139: `books = args.books.split(\",\")`), and run_greek_at_scale.py (line 136: `books = args.books.split(\",\")`). All 4 missing sites confirmed by grep. Effect: passing a legacy code such as `--books joh` to the AI drivers causes `iter_target_verses` to silently skip John (`translations.has_book(\"kjv\", \"joh\")` → False); passing `--books jol` to the Hebrew driver similarly yields zero output for Joel. The resulting `write_queue` call is either never reached or produces a file named `joh_ch_001.json` which `promote.py` cannot resolve. The `resolve_books()` function in at_scale_base.py itself does not normalize explicit args (line 113–114).",
    "fix": "Two-site fix: (1) In `resolve_books()` in `at_scale_base.py` (lines 113–114), normalize explicit args: `return [sources._normalize_book_code(b.strip()) for b in books_arg.split(\",\") if b.strip()]` — but this introduces a `scripts` import into at_scale_base which the docstring forbids (circular-import hazard for detectors.py). Therefore keep the normalization in each driver. (2) Add the normalization call in the 4 drivers' main() functions immediately after the book list is resolved, mirroring the 4 already-fixed drivers: in run_hebrew and run_greek after `books = args.books.split(\",\")`, and in run_ai_xrefs and run_ai_notes after `books = resolve_books(args.books)`, add `from scripts.core import sources; books = [sources._normalize_book_code(b) for b in books]`. Add a comment 'Defense-in-depth: canonicalize legacy codes (★BUGCLUSTER)' to match the existing 4 sites."
  },
  {
    "dimension": "tests",
    "severity": "high",
    "title": "Cyril absolute-count ceiling (≤700) leaves only 32 entries headroom — future authorized Cyril expansion will cause spurious test failures",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/tests/test_ethiopian_gamma4.py",
    "line": "1171-1183",
    "evidence": "```python\nassert len(cyril) <= 700, f\"γ.4.2 wave-1 Cyril ceiling: expected ≤700 Cyril entries; found {len(cyril)}\"\n```\nThe comment on line 1180 states 'Live count at pin-time (2026-05-31) = 668', leaving only 32 entries before the ceiling trips. RULES §1 explicitly authorizes future Cyril expansion ('If Cyril's share crosses 50% in future detail-wave expansion, that is acceptable'). The γ.4.9.D voice-mix table at line 7101 confirms the current Cyril count is 668. The authoritative plurality-leader guard (test_cyril_remains_plurality_leader_at_arc_close in TestGamma49DAthanasianArcClose, line 7014) already guards the real invariant — that Cyril > every other challenger — making this ceiling a redundant but brittle constraint. The specific mutation that breaks under the existing ceiling but should not fail: any future Cyril expansion wave adding ≥33 entries (e.g. a γ.4.1.E or a new patristic commentary seed wave, all authorized by §1). The test would block the ship even though the corpus is well-balanced and plurality is preserved.",
    "fix": "In TestGamma42EphremWave.test_voice_rebalance_achieved (line 1183), raise the ceiling to a value that gives meaningful headroom without blocking legitimate ingest — e.g. 1000 — or remove the ceiling entirely and rely solely on the durable plurality-leader tests that already guard the real invariant. If a ceiling is retained, update the comment to document the new headroom calculation. The §8.1-compliant floor test (test_ephrem_now_substantively_present, ≥30 Ephrem entries) already guards the rebalance from the Ephrem side; a Cyril ceiling that conflicts with §1's authorized expansion is the wrong instrument."
  },
  {
    "dimension": "tests",
    "severity": "medium",
    "title": "TestStrayArtifacts.test_flags_junk is not state-aware: accepts 'warn' even though _ENFORCE_STRAY_ARTIFACTS is True",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/tests/test_lint_guardrails.py",
    "line": "231-239",
    "evidence": "```python\ndef test_flags_junk(self, monkeypatch):\n    monkeypatch.setattr(\n        lint_rules, \"_git_candidate_files\", lambda: [\"scripts/x.py\", \"scratch.tmp\", \"dev/notes.bak\"]\n    )\n    r = lint_rules.check_no_stray_artifacts()\n    # FAIL-tier once the tree is verified clean (_ENFORCE_STRAY_ARTIFACTS);\n    # WARN beforehand. Tier-robust: a breach is at least surfaced.\n    assert r[\"status\"] in {\"warn\", \"fail\"}\n```\nlint_rules.py lines 1707-1709 confirm `_ENFORCE_STRAY_ARTIFACTS = (True # tree verified clean 2026-05-29)`. Every sibling guard in the same file uses the state-aware pattern: `assert r[\"status\"] == (\"fail\" if lint_rules._ENFORCE_COMMERCIAL else \"warn\")` (line 148) and similar for RETIRED_TERMS (line 178) and TRIAD_PLAN (line 216). The specific mutation this test misses: if check_no_stray_artifacts() returns 'warn' when _ENFORCE_STRAY_ARTIFACTS is True (e.g. the flag is accidentally ignored in the status-selection branch at lint_rules.py line 1952), this test still passes while the other sibling tests would correctly fail.",
    "fix": "Replace `assert r[\"status\"] in {\"warn\", \"fail\"}` with the state-aware pattern consistent with the sibling tests:\n```python\nassert r[\"status\"] == (\"fail\" if lint_rules._ENFORCE_STRAY_ARTIFACTS else \"warn\")\n```\nThis matches the exact pattern at lines 148, 178, 216 of the same file and would correctly catch a regression where the enforce flag is True but the function returns 'warn'."
  },
  {
    "dimension": "tests",
    "severity": "low",
    "title": "test_audit_clean_state_on_real_tree carries a stale hardcoded count comment ('23 cached functions') — the actual decorator count is now ~37",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/tests/test_audit_caches.py",
    "line": "181-199",
    "evidence": "```python\n# Pin: scripts/ has 23 cached functions (15 with clear paths\n# + 8 whitelisted) and zero \"no_clear_path\" findings.\n```\nA grep for `^@lru_cache|^@functools.lru_cache` across scripts/ returns 37 hits across 17 files (scripts/core/sources_lexicon.py:6, scripts/core/sources_commentary.py:6, etc.). The actual assertions only check `result[\"ok\"] is True` and `result[\"summary\"][\"no_clear_path\"] == 0`, which are still correct. However, the comment misleads maintainers into thinking the count is pinned at 23 and is stable — in reality it has grown 60% without notice. There is no assertion that would fail if the count drifted further, and the existing spot-checks (_cached_attribution_audit, strongs_hebrew) only verify 2 specific entries.",
    "fix": "Update the comment to reflect the current count (run `scripts/audit_caches.py --json` to get the exact breakdown) and add a floor assertion: `assert result[\"summary\"][\"total\"] >= N` where N is the current count minus a small buffer. This converts the stale comment into a live guard — if someone accidentally removes a cache decorator (deletes a function without removing its whitelist entry), the test would catch it. Separately, consider adding one or two additional spot-check assertions for newly-added caches that now lack their own spot-checks (e.g. a translation.py or notes_io.py cache)."
  },
  {
    "dimension": "docs",
    "severity": "medium",
    "title": "REPO_MAP scripts/core/ count is 65, actual is 66 (manuscript_records.py unaccounted)",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/dev/REPO_MAP.md",
    "line": "41",
    "evidence": "Line 41 reads: `- **`scripts/core/`** (65) — the engine: ...`. A direct glob of `scripts/core/*.py` returns 66 files: the 65 previously counted plus `scripts/core/manuscript_records.py` (docstring: 'Witness-record schema + honesty-contract validator (Phase-2 Unit C)'). The Phase 6 doc-truth pass corrected test-file, plan, and notes/ counts but did not update this one. The `check_repo_map_complete` lint explicitly skips prose-count validation, so this does not self-heal.",
    "fix": "Change `(65)` to `(66)` on REPO_MAP.md line 41, and optionally append `manuscript_records.py` to the `etc.` list if a new landmark module deserves mention."
  },
  {
    "dimension": "docs",
    "severity": "medium",
    "title": "MATRIX_MAP variable-trace table claims popup_translation is 'OK' but _replace_verse_popup_translation is explicitly NOT YET WIRED INTO THE BUILD",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/dev/MATRIX_MAP.md",
    "line": "107",
    "evidence": "MATRIX_MAP line 107: `| popup_translation | translations/<id>/ | build _replace_verse_popup_translation | OK (kjv, *-en, \"\") |`. The code at `scripts/build_edition.py:618` reads: `⚠ NOT YET WIRED INTO THE BUILD (flagged mint-7 D3, 2026-05-31): a complete, tested feature (5 tests in test_scripts.py) with no production caller yet.` The MATRIX_MAP 'OK' status actively misleads a future Claude session into thinking popup_translation is a live build variable, when no edition's popup_translation field currently has any effect at build time. This is mint-9 finding #16 confirmed still unresolved.",
    "fix": "Replace the trace status cell on MATRIX_MAP.md line 107 with: `DEFERRED — function exists + tested but has no production caller; wiring is a τ.G standalone-bible phase (RULES §9 'Add a new edition feature')`."
  },
  {
    "dimension": "docs",
    "severity": "low",
    "title": "docs/superpowers/INDEX.md and mint-9-fixes-plan.md Status both stale: claim 'Phases 3–6 in progress' when all 6 are complete",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/docs/superpowers/INDEX.md",
    "line": "13",
    "evidence": "INDEX.md line 13 (In progress table): `EXECUTING 2026-05-31 — round-2 re-audit found 45 survivors; Phases 1–2 shipped, 3–6 in progress; then re-audit (round 3) to convergence`. The corresponding plan file `plans/2026-05-31-mint-9-fixes-plan.md` line 3 reads: `EXECUTING 2026-05-31 — Phase 1 (data-loss/filter HIGH) + Phase 2 (stale-cache/guards) shipped; Phases 3–6 in progress.` CHANGELOG 2026-06-01 line 9 and SESSION_STATE confirm: 'ALL 6 FIX PHASES SHIPPED'. The `check_superpowers_coherence` lint validates only that a `**Status:**` header exists and the file is indexed — it does not validate semantic currency of the status text, so this drift is invisible to the linter. Both files must be updated together to keep them in sync (the lint also checks that INDEX mirrors the file's status).",
    "fix": "In `docs/superpowers/plans/2026-05-31-mint-9-fixes-plan.md` line 3, replace the Status value with: `COMPLETE — all Phases 1–6 shipped 2026-06-01 (b1a39485 + HEAD); byte-stability gate PASSED; lint 27✓/1warn/0fail. H4/H5 ex.py→exo + aes ch11–16 + M8 compresslevel deferred-by-design. NEXT = round-3 re-audit.` Then regenerate or hand-update INDEX.md line 13 to match (move the row from the 'In progress' table to the 'Shipped' table)."
  },
  {
    "dimension": "byte-stability",
    "severity": "high",
    "title": "Build cache: scripts/core/popup_versions.py missing from _PIPELINE_SCRIPTS — stale EPUB served after version-registry edit",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/scripts/core/build_cache.py",
    "line": "62-70",
    "evidence": "`_PIPELINE_SCRIPTS` lists 7 scripts under `scripts/` but omits `scripts/core/popup_versions.py`, which is imported at module-level in `build_edition.py` (line 749: `from scripts.core import popup_versions as _pv`) and whose `VERSION_REGISTRY` dict is merged into `POPUP_LANGUAGES` at lines 751-760. This table drives `_strip_language_paragraph` for every vnote aside across all 9 KJV editions (all of which declare `popup_languages_default`). If `popup_versions.py` changes — e.g., a `content_class` is renamed, `DEFAULT_POPUP_WITNESSES` is updated, or a new version is added — the SHA-256 cache key is unchanged and the cache serves the pre-edit EPUB. Checked: `popup_versions` appears nowhere in `build_cache.py`.",
    "fix": "Add `\"core/popup_versions.py\"` to `_PIPELINE_SCRIPTS`:\n```python\n_PIPELINE_SCRIPTS = (\n    \"build_edition.py\",\n    \"matter_pages.py\",\n    \"epub_utils.py\",\n    \"resync_marker_glyphs.py\",\n    \"build_epub.py\",\n    \"style_config.py\",\n    \"inject.py\",\n    \"core/popup_versions.py\",   # drives POPUP_LANGUAGES / language-stripping\n)\n```\nThen update the corresponding `_hash_file` call path — the existing loop at lines 266-271 uses `_REPO / \"scripts\" / script_name`, so `\"core/popup_versions.py\"` resolves correctly to `scripts/core/popup_versions.py`."
  },
  {
    "dimension": "byte-stability",
    "severity": "medium",
    "title": "Build cache: scripts/core/traditions.py missing from _PIPELINE_SCRIPTS — stale EPUB served for tradition-filtered editions after label/ID change",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/scripts/core/build_cache.py",
    "line": "62-70",
    "evidence": "`scripts/core/traditions.py` is imported at build time in three places in `build_edition.py` (lines 126, 227, 459) and its `CANONICAL_TRADITIONS` tuple provides the display labels injected by `apply_tradition_labels_to_html` into editions that declare `traditions_default`. `catholic-study` has `traditions_default: [catholic, cross]` in `editions.yaml`, so this path is actively exercised. Editing a label in `CANONICAL_TRADITIONS` (e.g., correcting a capitalisation) would change the HTML bytes of the built EPUB without invalidating the cache key. `traditions` appears nowhere in `build_cache.py`. The same `scripts/` prefix in `_PIPELINE_SCRIPTS` covers `core/` sub-paths (verified: the hash loop at line 266 does `_REPO / 'scripts' / script_name`).",
    "fix": "Add `\"core/traditions.py\"` to `_PIPELINE_SCRIPTS` alongside the `popup_versions.py` addition above:\n```python\n    \"core/traditions.py\",   # CANONICAL_TRADITIONS labels injected for tradition-filtered editions\n```"
  },
  {
    "dimension": "byte-stability",
    "severity": "medium",
    "title": "build_cache._referenced_translations resolves legacy popup-language aliases to non-existent directories — stale cache for any edition using 'english'/'hebrew'/'greek' aliases",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/scripts/core/build_cache.py",
    "line": "111-136",
    "evidence": "`_referenced_translations` collects raw language IDs from `popup_languages_default` and `popup_languages_per_book` and hashes `translations/<id>/_meta.yaml` + per-book files. But `build_edition._resolve_popup_languages` maps legacy aliases through `_pv.resolve_version_id` at runtime (line 795): `'english' → 'kjv'`, `'hebrew' → 'wlc'`, `'greek' → 'lxx-greek'`. If an edition declares `popup_languages_default: [english]`, the cache key hashes `translations/english/_meta.yaml` (returns `\"<missing>\"`) while the build actually reads `translations/kjv/*.py`. Editing any `kjv/<book>.py` verse will not bust the cache for that edition. All 9 current KJV editions use the registry IDs directly (`wlc`, `lxx-greek`, etc.), so this is not currently triggered — but is a latent correctness trap for any future edition using the legacy aliases, which `_resolve_popup_languages` explicitly continues to support.",
    "fix": "In `_referenced_translations`, apply the same alias-resolution the build does before adding to `refs`:\n```python\nfrom scripts.core import popup_versions as _pv\n\n# inside the loop over langs:\nmapped_id = _pv.resolve_version_id(lang) or lang\nrefs.add(mapped_id.strip())\n```\nApply the same normalization for entries parsed from `popup_languages_per_book`. This ensures the hashed translation paths match what `_apply_popup_languages_and_translation` actually reads."
  },
  {
    "dimension": "byte-stability",
    "severity": "high",
    "title": "Build cache key omits topical-index source data files; stale EPUB served after naves/torrey JSON rebuild",
    "file": "scripts/core/build_cache.py",
    "line": "62-70, 277",
    "evidence": "The `compute_cache_key` function explicitly hashes `source_dates.yaml` at line 277 with the rationale 'not under epub_working/, so hash it directly or a … edit serves a stale … EPUB' (comment lines 274-276). The same class of input is missed for the two topical-index data files. Every EPUB build calls `inject_back_matter` (build_edition.py:3040) → `_write_topical_page` (matter_pages.py:983) → `_sources.naves_topical()` / `_sources.torrey_topical()` (matter_pages.py:1020-1021), which load `content/sources/naves_topical.json` and `content/sources/torrey_topical.json` respectively. Neither path appears anywhere in `_PIPELINE_SCRIPTS` (line 62) nor in any other `parts.append(...)` call in `compute_cache_key`. Consequence: after a user runs `extract_naves_ccel.py` or `extract_torrey_ccel.py` to fix an OCR error in the topical data, the cache key is byte-identical to the pre-fix key; `cache_lookup` at build_edition.py:2775 returns the old EPUB and the fix is silently not applied. Verified by tracing all 15 `parts.append` call sites in the function.",
    "fix": "Add two entries immediately after the `source_dates.yaml` line (277) in `compute_cache_key`, using the identical pattern established there:\n\n```python\n# Topical-index source data consumed by inject_back_matter -> build_merged_topic_index.\n# Re-running extract_naves_ccel.py or extract_torrey_ccel.py must bust the cache.\nparts.append((\"naves_topical.json\",  _hash_file(_CONTENT / \"sources\" / \"naves_topical.json\")))\nparts.append((\"torrey_topical.json\", _hash_file(_CONTENT / \"sources\" / \"torrey_topical.json\")))\n```\n\nBecause `parts.sort()` at line 305 canonicalises label order before hashing, insertion position is irrelevant. `_hash_file` returns `'<missing>'` if a file is absent, so editions that have never run the extractor still get a valid (distinct) key. The fix is additive and does not invalidate any currently-correct cache entry."
  },
  {
    "dimension": "data-validity",
    "severity": "medium",
    "title": "run_naves_at_scale.py and run_torrey_at_scale.py lack coord_in_canonical_extent guard — defense-in-depth gap lets impossible-chapter candidates be written",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/scripts/run_naves_at_scale.py",
    "line": "101-121",
    "evidence": "In run_naves_at_scale.py lines 101-121 (and the byte-identical loop in run_torrey_at_scale.py lines 120-141), the driver iterates `book_data.items()` — the `_verses` reverse index from the cached JSON — and calls `detector.detect(book, chapter, verse, ...)` with no `coord_in_canonical_extent` check:\n\n```python\nfor chapter_str, verses in book_data.items():\n    chapter = int(chapter_str)\n    for verse_str in verses:\n        verse = int(verse_str)\n        cands = detector.detect(book, chapter, verse, _verse_text=\"\")\n```\n\nThe design assumption is that `_build_naves_indices` already filtered bad coords at JSON-build time. That assumption proved false for a prior run: five candidate files today carry impossible coordinates from a pre-guard Nave's source run — `1ch_ch_038.json` (1 Chr has 29 chapters; candidate has chapter=38, verse=11), `1co_ch_035.json` (1 Cor has 16 chapters; candidate has chapter=35, verse=51), `1jn_ch_006.json` (1 Jn has 5 chapters; candidate has chapter=6, verse=45), `1sa_ch_034.json` (1 Sam has 31 chapters; candidate has chapter=34, verse=50), `1ti_ch_008.json` (1 Tim has 6 chapters; candidate has chapter=8, verse=9). All are status=pending and kind=topic-nave. The `promote_candidate` boundary guard (promote.py line 441) prevents promotion, so no bad notes reach content/notes/. But if run_naves_at_scale.py or run_torrey_at_scale.py is re-run with a JSON source that has any leakage, the same stale-candidate pattern silently recurs. Both drivers were checked — both share the same missing line.",
    "fix": "Add a `coord_in_canonical_extent` call in both drivers' inner loops before `detector.detect`, mirroring the pattern already in `batch_insert_notes` (promote.py line 354):\n\n```python\n# run_naves_at_scale.py, inside the inner verse loop\nfrom scripts.core.canonical_verse_counts import coord_in_canonical_extent  # top of file\n\nfor verse_str in verses:\n    try:\n        verse = int(verse_str)\n    except ValueError:\n        continue\n    if not coord_in_canonical_extent(book, chapter, verse):  # ADD THIS\n        continue\n    cands = detector.detect(book, chapter, verse, _verse_text=\"\")\n```\n\nApply identically to run_torrey_at_scale.py (same location, lines 127-138). Both drivers were checked — apply to both. This is the \"fix the whole class\" fix (2 sites)."
  },
  {
    "dimension": "data-validity",
    "severity": "low",
    "title": "Stale impossible-chapter candidate files in content/candidates/ from pre-guard Nave's run (5 confirmed)",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/content/candidates/1ch_ch_038.json",
    "line": "",
    "evidence": "Five candidate JSON files have chapter numbers that exceed their book's canonical chapter count: `1ch_ch_038.json` (chapter=38, 1 Chr has 29), `1co_ch_035.json` (chapter=35, 1 Cor has 16), `1jn_ch_006.json` (chapter=6, 1 Jn has 5), `1sa_ch_034.json` (chapter=34, 1 Sam has 31), `1ti_ch_008.json` (chapter=8, 1 Tim has 6). All contain `\"status\": \"pending\"` and `\"detector\": \"NaveTopicalDetector\"`. Confirmed that the current `naves_topical.json` source does NOT contain these coordinates (NEPHTOAH maps to jos, not 1sa 34; verified by searching the topics index). These are artifacts from a pre-guard source run that predates the `_naves_coord_in_extent` guard in `_build_naves_indices`. The promote_candidate guard (promote.py line 441) blocks their promotion — they cannot reach content/notes/. Impact is clutter in the review queue and potential reviewer confusion. Checked all 5 files individually.",
    "fix": "Delete or mark-rejected the five stale files: `1ch_ch_038.json`, `1co_ch_035.json`, `1jn_ch_006.json`, `1sa_ch_034.json`, `1ti_ch_008.json`. The fix to run_naves_at_scale.py above prevents regeneration. Optionally add a lint rule in `lint_rules.py` that rejects any candidate file whose chapter exceeds `canonical_chapters(book)` (using `coord_in_canonical_extent` already imported elsewhere)."
  },
  {
    "dimension": "concurrency-caching",
    "severity": "medium",
    "title": "corpus_index.connection(): unprotected check-then-set race leaks a sqlite3.Connection on ThreadingHTTPServer",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/scripts/core/corpus_index.py",
    "line": "669-679",
    "evidence": "```python\n    if _CACHED_CONN is None:\n        _CACHED_CONN = sqlite3.connect(current_path, check_same_thread=False)\n        _CACHED_CONN.row_factory = sqlite3.Row\n        _CACHED_CONN_PATH = current_path\n```\nThe `if _CACHED_CONN is None:` check and the subsequent `_CACHED_CONN = sqlite3.connect(...)` assignment are NOT protected by any lock. Under `ThreadingHTTPServer`, two concurrent request threads can both observe `_CACHED_CONN is None` (after a rebuild has reset it or on first startup) and both call `sqlite3.connect()`. Thread B's assignment overwrites Thread A's connection, leaking it. Python's GIL does not prevent this: `sqlite3.connect()` can release the GIL during I/O, so the scheduler can switch between the `is None` check and the assignment. The comment at line 603–608 correctly notes the rebuild lock serialises the reset inside `rebuild()`, but that lock is released before `connection()` does its own open. Result: one leaked `sqlite3.Connection` per race occurrence; the GC finaliser will eventually close it, but on a server with rapid corpus-rebuild cycles or many concurrent first-calls it compounds.",
    "fix": "Protect the open with the existing `_acquire_rebuild_lock` (already imported and used in `rebuild()`), OR add a dedicated threading.Lock around the `_CACHED_CONN is None` check-and-set block. Minimal change:\n```python\n_CONN_LOCK = threading.Lock()\n\ndef connection() -> sqlite3.Connection:\n    global _CACHED_CONN, _CACHED_CONN_PATH\n    rebuild()\n    current_path = str(_index_path())\n    with _CONN_LOCK:\n        if _CACHED_CONN is not None and current_path != _CACHED_CONN_PATH:\n            try:\n                _CACHED_CONN.close()\n            except sqlite3.Error:\n                pass\n            _CACHED_CONN = None\n            _CACHED_CONN_PATH = None\n        if _CACHED_CONN is None:\n            _CACHED_CONN = sqlite3.connect(current_path, check_same_thread=False)\n            _CACHED_CONN.row_factory = sqlite3.Row\n            _CACHED_CONN_PATH = current_path\n        return _CACHED_CONN\n```\nAlso fix the misleading comment at lines 670–672: `_warm_corpus_index()` only calls `rebuild()`, it does NOT call `connection()` and does not open `_CACHED_CONN` in the main thread."
  },
  {
    "dimension": "concurrency-caching",
    "severity": "low",
    "title": "conftest.py: _disable_corpus_index_fingerprint_cache fixture requests `monkeypatch` but never uses it — dead parameter wastes fixture overhead per test",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/tests/conftest.py",
    "line": "237",
    "evidence": "```python\n@pytest.fixture(autouse=True)\ndef _disable_corpus_index_fingerprint_cache(monkeypatch):\n    import sqlite3\n    try:\n        from scripts.core import corpus_index\n    except ImportError:\n        return\n    if corpus_index._CACHED_CONN is not None:\n        ...\n        corpus_index._CACHED_CONN = None\n        corpus_index._CACHED_CONN_PATH = None\n```\nThe `monkeypatch` fixture is declared as a parameter but never referenced in the function body. This is a leftover from the refactor that removed the `_FINGERPRINT_TTL_SEC = 0` override (see comment 'No more TTL=0 override'). Because `monkeypatch` is function-scoped, requesting it forces pytest to spin up the full monkeypatch machinery for every one of the ~200+ test functions this autouse fixture applies to. Checked the full conftest.py — the parameter is not used on any code path including the `ImportError` branch.",
    "fix": "Remove the unused `monkeypatch` parameter:\n```python\n@pytest.fixture(autouse=True)\ndef _disable_corpus_index_fingerprint_cache():\n    import sqlite3\n    try:\n        from scripts.core import corpus_index\n    except ImportError:\n        return\n    if corpus_index._CACHED_CONN is not None:\n        try:\n            corpus_index._CACHED_CONN.close()\n        except sqlite3.Error:\n            pass\n        corpus_index._CACHED_CONN = None\n        corpus_index._CACHED_CONN_PATH = None\n```"
  },
  {
    "dimension": "concurrency-caching",
    "severity": "low",
    "title": "_canons_index() docstring claims 'Cached load' but function has no cache and re-reads canons.yaml on every call",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/scripts/web_helpers.py",
    "line": "371-379",
    "evidence": "```python\ndef _canons_index() -> dict:\n    \"\"\"Cached load of canons.yaml — returns {canon_id: {label, description, books}}.\"\"\"\n    canons_path = REPO / \"content\" / \"canons.yaml\"\n    if not canons_path.is_file():\n        return {}\n    import yaml\n    data = yaml.safe_load(canons_path.read_text(encoding=\"utf-8\")) or {}\n    return data.get(\"canons\", {}) or {}\n```\nThe docstring says 'Cached load' but there is no `@lru_cache` decorator or any other caching mechanism. The function re-reads and re-parses canons.yaml from disk on every invocation. The caching happens at the outer `_cached_edition_diff` (mtime-keyed lru_cache in web_matrix.py line 25), so correctness is unaffected. But the misleading docstring violates the S7.1 caching-tier vocabulary (RULES §7.1 uses 'cache' to specifically mean the `lru_cache`-keyed pattern), and a developer could rely on it when auditing performance. Checked both callers: `_compute_edition_diff_uncached` in web_matrix.py line 422 (only called on a mtime-keyed cache miss) and no other call sites in scripts/.",
    "fix": "Correct the docstring to remove the false 'Cached' claim:\n```python\ndef _canons_index() -> dict:\n    \"\"\"Load canons.yaml and return {canon_id: {label, description, books}}.\n    Not cached directly — caller (_compute_edition_diff_uncached) is wrapped\n    by the mtime-keyed _cached_edition_diff, so disk reads only happen on\n    a cache miss.\n    \"\"\"\n```\nAlternatively, add `@functools.lru_cache(maxsize=1)` if the file is considered project-internal published data (canons.yaml is not user-editable at runtime via any API endpoint), which would match the S7.1 singleton tier and make the docstring accurate."
  },
  {
    "dimension": "cross-module",
    "severity": "medium",
    "title": "Cyril plurality test at γ.4.8.E arc-close only checks 2 of 5 rival voices — incomplete-fix pattern missed in mint-9",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/tests/test_ethiopian_gamma4.py",
    "line": "8174-8197",
    "evidence": "```python\n# test_cyril_remains_plurality_leader_at_meqabyan_arc_close (line 8174):\ncyril_count = 0\njubilees_count = 0\nfor verse_entries in self.ec._by_verse.values():\n    for e in verse_entries:\n        if e.father == \"Cyril of Alexandria\":\n            cyril_count += 1\n        elif e.father.startswith(\"Jubilees\"):\n            jubilees_count += 1\nmeq_count = len(self._all_meq())\nassert cyril_count > meq_count, ...\nassert cyril_count > jubilees_count, ...\n```\nThis checks only Meqabyan and Jubilees. It does NOT check Athanasius (~150 entries), Ephrem (~165 entries), or 1 Enoch (~200 entries). The γ.4.9.D test (`test_cyril_remains_plurality_leader_at_arc_close`, line 7014) was upgraded in mint-9 fix P5 specifically because 'A future Ephrem / 1-Enoch expansion wave could overtake Cyril while this test, checking only two rivals, stayed green.' The SAME two-rival weakness exists in the γ.4.8.E sibling at line 8174, which was not upgraded in the same change. The γ.4.8.F class (line 8515) does check all 5 voices, but the γ.4.8.E test class is stale. The 'fix the class, not the instance' doctrine (project memory + SESSION_STATE) explicitly requires all sites of a pattern defect to be fixed together — the γ.4.8.E test is the missed site.",
    "fix": "Replace the two-rival check in `test_cyril_remains_plurality_leader_at_meqabyan_arc_close` with the same all-challengers pattern used in `test_cyril_remains_plurality_leader_at_arc_close` (γ.4.9.D): use `collections.Counter` over all `_by_verse` entries, collapse tradition suffixes with `_voice()`, then assert `cyril_count > max(challengers.values())`. This mirrors the γ.4.9.D upgrade exactly. Optionally add the `≥2× next-single-father` ratio guard that γ.4.8.F introduced. Both are read-only test changes; no corpus data is affected."
  },
  {
    "dimension": "tests-run",
    "severity": "medium",
    "title": "Unwhitelisted lru_cache in inject.py without clear path",
    "file": "scripts/inject.py",
    "line": "610",
    "evidence": "@functools.lru_cache(maxsize=256)\ndef _aside_existing_re(prefix: str) -> re.Pattern: ... — No cache_clear() site found in codebase, and not in whitelist.",
    "fix": "Add to scripts/.cache_audit_whitelist.py: `_._aside_existing_re` (documented as a read-once compiled regex per prefix with no input dependencies requiring invalidation)."
  },
  {
    "dimension": "tests-run",
    "severity": "medium",
    "title": "Stale test: test_delete_table_has_eight_entries_now expects future routes",
    "file": "tests/test_web_routetable.py",
    "line": "1068",
    "evidence": "assert len(web._DELETE_ROUTES) == 8 but actual count is 6. Test comment references ε.6 (distribution/<edition>/<channel>) and ξ.26 (license/<edition>) routes that don't exist. These are future phases not yet implemented.",
    "fix": "Update test assertion from 8 to 6, OR if those routes are meant to exist, implement them in scripts/web.py. Recommend reviewing the roadmap to determine if ε/ξ phases are in-scope."
  },
  {
    "dimension": "tests-run",
    "severity": "medium",
    "title": "Stale test: test_multipart_table_has_four_entries expects future routes",
    "file": "tests/test_web_routetable.py",
    "line": "1195",
    "evidence": "assert len(web._MULTIPART_ROUTES) == 4 but actual count is 3. Test comment references ε.3 (sales/import/<channel>) route not yet implemented.",
    "fix": "Update test assertion from 4 to 3, OR if that route is meant to exist, implement it. Check roadmap for ε.3 scope."
  },
  {
    "dimension": "tests-run",
    "severity": "medium",
    "title": "Stale test: test_put_table_has_twelve_entries expects future routes",
    "file": "tests/test_web_routetable.py",
    "line": "1410",
    "evidence": "assert len(web._PUT_ROUTES) == 12 but actual count is 10. Test comment references ε.6 (distribution mark), ε.7 (press-kit save), and ξ.26 (license set) routes not yet implemented.",
    "fix": "Update test assertion from 12 to 10, OR implement missing routes. Check roadmap for phase status."
  },
  {
    "dimension": "tests-run",
    "severity": "medium",
    "title": "Multiple stale scope document tests fail with missing files",
    "file": "tests/test_parallel_bible_tau6x0b.py",
    "line": "1",
    "evidence": "8 test failures in TestTau6x0bScopeDecisionBlock checking for scope doc sections that don't exist: test_scope_doc_exists, test_decision_block_present, test_option_d_authorized, test_authorized_date_recorded, test_tesseract_engine_choice_recorded, test_tesseract_not_installed_verification_recorded, test_geez_tessdata_uncertainty_documented. Similar pattern in tau6x0, tau6x0c, tau6x1, tau6x2 tests.",
    "fix": "Review the scope documents in dev/ to determine if tau6x phases are still in-scope. Either remove the tests or implement the required scope sections in dev/SCOPE_*.md or dev/PLAN_*.md files."
  },
  {
    "dimension": "tests-run",
    "severity": "medium",
    "title": "Test checking for deleted commercial module still fails",
    "file": "tests/test_omega0_free_public_pivot.py",
    "line": "1",
    "evidence": "FAILED test_deleted_modules_gone[scripts/api/distribution.py] — Test expects scripts/api/distribution.py to be deleted, but file exists or test is checking wrong location.",
    "fix": "Verify if distribution.py should actually exist or be deleted. Check SESSION_STATE and CHANGELOG for context on the free-public-pivot phase."
  },
  {
    "dimension": "tests-run",
    "severity": "medium",
    "title": "Test for url_override not working in sources cache fetch",
    "file": "tests/test_scripts.py",
    "line": "8066",
    "evidence": "assert seen_urls == [\"https://my-mirror/example.json\"] but got []. The url_override parameter is not being passed through to the stub_fetch function, suggesting the implementation doesn't handle the override.",
    "fix": "Check api_sources_cache_fetch implementation in scripts/api/sources.py or scripts/web_sources.py to ensure url_override parameter is properly destructured and passed to the fetch_fn callback."
  },
  {
    "dimension": "tests-run",
    "severity": "medium",
    "title": "Audit log chain verification fails on pre-ξ.17 records",
    "file": "tests/test_security_xi_late.py",
    "line": "1176",
    "evidence": "assert result[\"status\"] == \"ok\" but got \"broken\". Test creates a pre-ξ.17 ndjson line (without prev_hash) then appends a new line. The verify_chain function reports broken instead of ok.",
    "fix": "Review scripts/core/audit_log.py verify_chain() to ensure it properly handles legacy pre-ξ.17 lines without prev_hash. The chain should seed from the old line's hash, not treat it as a break."
  },
  {
    "dimension": "tests-run",
    "severity": "high",
    "title": "Lint rules tests fail: ALL_CHECKS count mismatch",
    "file": "tests/test_lint_rules.py",
    "line": "1",
    "evidence": "Multiple test failures in TestAllChecksMetaContract and TestOmega23LintProfile: test_every_check_runs_returns_valid_shape_and_does_not_fail, test_main_profile_prints_per_check_timing, test_main_default_mode_unchanged, test_main_json_includes_duration_ms, test_profile_and_json_compose. These suggest the ALL_CHECKS registry count has changed or checks have been added/removed without updating the pin.",
    "fix": "Run `python scripts/lint_rules.py` to see the current check list and count. Update tests/test_lint_rules.py with the correct expected count and verify all checks pass individually."
  },
  {
    "dimension": "tests-run",
    "severity": "medium",
    "title": "Test for defaults_used_when_unset fails in publisher console",
    "file": "tests/test_scripts.py",
    "line": "1",
    "evidence": "FAILED TestPublisherConsole::test_defaults_used_when_unset — Likely stale assertion on default values or missing mock setup.",
    "fix": "Review the test_defaults_used_when_unset test and the api_publisher implementation to identify which default is not being applied correctly."
  },
  {
    "dimension": "tests-run",
    "severity": "low",
    "title": "Test error in test_work_cache.py::test_persists_to_disk",
    "file": "tests/test_work_cache.py",
    "line": "1",
    "evidence": "ERROR (not FAILED) with AssertionError. An error state suggests an unhandled exception during test setup or execution.",
    "fix": "Run the test individually with pytest -vv to see the full traceback: `pytest tests/test_work_cache.py::test_persists_to_disk -vv` to identify the root cause."
  },
  {
    "dimension": "opt-vision",
    "severity": "medium",
    "title": "corpus_index.connection() has an unguarded TOCTOU that leaks a SQLite connection per concurrent request pair",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/scripts/core/corpus_index.py",
    "line": "659-680",
    "evidence": "Lines 669-679: `if _CACHED_CONN is None: _CACHED_CONN = sqlite3.connect(current_path, check_same_thread=False)`. Under ThreadingHTTPServer two worker threads can both pass the `_CACHED_CONN is None` check simultaneously, both call `sqlite3.connect()`, and one connection is stored in `_CACHED_CONN` while the other is leaked (unreachable, not closed). The mint-9 #20 fix (putting the _CACHED_CONN reset inside `_acquire_rebuild_lock` in `rebuild()`) addresses the reset-while-held race but NOT this double-open race in `connection()` itself. Each leaked connection holds an OS file descriptor on the SQLite file. In CPython the GC collects it when the reference drops, but under rapid concurrent /matrix + /customize requests a short burst produces multiple leaked fds. Checked: no `threading.Lock` exists around this check-and-set anywhere in corpus_index.py.",
    "fix": "Add a module-level `_CONN_LOCK = threading.Lock()` and wrap the None-check-and-create block in `connection()` with it: `with _CONN_LOCK: if _CACHED_CONN is None: _CACHED_CONN = sqlite3.connect(...); _CACHED_CONN_PATH = current_path`. The path-mismatch close block (lines 662-668) should also be inside the same lock for the same reason. `_acquire_rebuild_lock` already serializes rebuild() calls; this lock only serialises the connection object's creation/replacement, so there is no deadlock risk."
  },
  {
    "dimension": "opt-vision",
    "severity": "low",
    "title": "check_render_coverage_no_regression in lint_rules.py checks raw .stem values but the expected sets still contain the legacy code \"ex\" — will silently break when ex.py is renamed to exo.py without a paired expected-set update",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/scripts/lint_rules.py",
    "line": "977, 1042",
    "evidence": "Line 1042: `actual = {p.stem for p in ed_dir.glob('*.py') if not p.stem.startswith('_')}` — uses raw file stems. Lines 977 (geez expected) and matching amharic set: `\"ex\"` listed. `render_coverage.py:54` defines `_BOOK_ALIASES = {\"ex\": \"exo\", ...}` and uses it in `_list_rendered()`, but lint_rules.py's check uses its OWN scan (line 1042) that does NOT apply the alias. Today `ex.py` exists so `\"ex\" in actual` is True. When the deferred `ex.py`→`exo.py` rename ships (MEMORY `reference_deep_audit_tool` deferred τ.G), the expected set still has `\"ex\"`, actual will have `\"exo\"`, and `missing = expected - actual` will report `{\"ex\"}` as a false regression, immediately blocking every commit. Checked both expected sets (lines 960-1025): `\"ex\"` appears in both; no conditional or alias logic present.",
    "fix": "In both `expected_geez` and `expected_amharic` sets in `check_render_coverage_no_regression`: replace `\"ex\"` with `\"exo\"` (the canonical code). Do this as part of the τ.G rename commit — the change is a one-liner in lint_rules.py and must be atomic with the rename. Add a comment `# was ex.py (legacy 2-letter); renamed to exo.py at τ.G` to explain the history. Since the rename is deferred, no code change is needed now, but the τ.G ship checklist must include this lint_rules.py update."
  },
  {
    "dimension": "opt-vision",
    "severity": "low",
    "title": "web_helpers.html_ref_id_from_note_id silently returns None for Strategy-B books (missing bxx fallback), while every other ref-id builder applies the bxx fallback",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/scripts/web_helpers.py",
    "line": "262-265",
    "evidence": "Lines 262-265: `prefix = book.get('id_prefix'); if not prefix: return None`. All other ref-id builders in the codebase apply the Strategy-B bxx fallback: `build_edition.py:139` `prefix = book.get('id_prefix') or book.get('bxx')`, `build_edition.py:336` same, `build_edition.py:2666` same, `inject.py:691` same. The web_helpers variant is used by `note_id_from_tuple` / `html_ref_id_from_note_id` in the web editor path (add_note, delete, jump-to-ref UI). A Strategy-B book (e.g. 2ch, ezr, neh — books without id_prefix but with bxx) would return `None` here, making the editor unable to navigate to the HTML ref-id for any note in those books. Grep confirmed 4 sites use the bxx fallback; only web_helpers.py:262 omits it.",
    "fix": "At line 262 change `prefix = book.get('id_prefix')` to `prefix = book.get('id_prefix') or book.get('bxx')`. This is the identical pattern used at build_edition.py:139, 336, 2666 and inject.py:691 — sweeping ALL sites of this pattern."
  },
  {
    "dimension": "opt-vision",
    "severity": "info",
    "title": "CONFIRM-OPTIMAL: Vision-transcription marathon method (Patrologia Esther + Kings/Samuel) is still optimal under today's constraints",
    "file": "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/content/translations/sources/patrologia/_vision_notes.md",
    "line": "",
    "evidence": "The OOM crashes (documented in _vision_notes.md (n), plan 2026-05-17-kings-manuscript-collation.md crash-fix section) were caused by stacked heavy agents with whole-folio upscale buffering ~400k parent tokens — not context window limits. Today's 1M-context models (Sonnet 4.6/Opus 4) do NOT change the RAM constraint: the 16 GB box is the ceiling, and the parent-buffered output from concurrent heavy agents is the load-bearing variable, not context window depth. Larger context per agent would make the OOM WORSE (more output buffered), not better. Ultracode/Workflow orchestration runs under the same subscription (no paid API); it can manage dispatch coordination but cannot reduce per-agent RAM. The current method — MAX-1 heavy vision agent, tight ≤1568px region crops, per-step commits, OOM-recovery from StructuredOutput jsonl (note (n)/(o)) — correctly eliminates the root cause. The 3-pass convergence (2 blind + adjudicator) is producing clean results at p24-p27 with only 3 uncertain flags each. One additive improvement is available: codifying note (n)'s transcript-recovery procedure into a small recovery helper script (e.g. scripts/recover_vision_transcript.py) that auto-walks subagent jsonl and extracts completed StructuredOutputs — reducing recovery cost from manual PowerShell to one command. This is an enhancement, not a method change.",
    "fix": "Confirmed optimal: maintain MAX-1 heavy vision agent, tight ≤1568px crops, per-step commits, 3-pass convergence. Optional additive: create scripts/recover_vision_transcript.py that implements the note-(n) recovery procedure (walk .claude/projects/.../subagents/*.jsonl, find tool_use with name==StructuredOutput, extract .input) as a standalone command, reducing OOM recovery time. No RAM/cost risk — the script only reads existing jsonl files, no new agent dispatches."
  }
]

function kindOf(dim) {
  if (dim === 'opt-vision' || dim.startsWith('opt-')) return 'optimization'
  if (dim === 'tests-run' || dim === 'marathon-boundary') return 'guard'
  return 'find'
}
const RECOVERED = RECOVERED_RAW.map((f) => ({ ...f, kind: kindOf(f.dimension) }))

// ----------------------------------------------------------------------------
// The finders that NEVER completed (cross-module#1 book-code angle + 3 opt dims).
// ----------------------------------------------------------------------------
const CROSS_MODULE_PROMPT = `DIMENSION: CROSS-MODULE INVARIANTS. Find violations of project-wide invariants: (a) BOOK-CODE canonicalization — re-verify the mint-7 bookcode_canonical lint holds across ANY map; hunt for a NEW or missed legacy alias (php/jas/jol/ezk/nam/joh/mar/ps) in any detector, loader, renderer, or xref map that would route to a non-existent notes file or drop notes; (b) the enabled-kinds 3-way divergence (MATRIX_MAP debt #1 — is it still diverging across the three enablement surfaces?); (c) the patristic-voice composition invariant (Cyril remains plurality-leader; guarded by test_cyril_remains_plurality_leader); (d) canonical book/chapter order everywhere (RULES S6.1) — any UI/encoder sorting books alphabetically/by-count instead of content/books.yaml order.`
const CROSS_MODULE_ANGLE0 = 'Emphasize book-code canonicalization (any missed legacy-alias map) and canonical book/chapter ordering.'

const MISSING_DIMS = [
  {
    key: 'cross-module', kind: 'find', agentType: 'feature-dev:code-reviewer',
    prompt: `${CROSS_MODULE_PROMPT}\n\nINDEPENDENT ANGLE [1/2]: ${CROSS_MODULE_ANGLE0} Bring a fresh perspective; do not assume another finder will catch the obvious — report it yourself.`,
    label: 'find:cross-module#1',
  },
  {
    key: 'opt-build', kind: 'optimization', agentType: 'feature-dev:code-architect',
    prompt: `OPTIMIZATION RE-EVALUATION. A single-edition build is ~133 s (re-zips a ~23 MB epub_working/ tree per edition; measured mint-7 E3) — the all-9 loop is slow. Read scripts/build_edition.py + the build pipeline in MATRIX_MAP. Is the inject -> filter -> zip path optimizable: incremental builds, a shared pre-filtered base, parallel edition builds, cheaper/streamed zip, caching the unchanged base across editions? Produce CONFIRM-OPTIMAL or a concrete BETTER PLAN with the expected speedup AND the byte-stability proof obligation (the 9 KJV editions MUST stay byte-identical — any optimization must demonstrate byte-identical output, RULES byte-compat invariant).`,
    label: 'find:opt-build',
  },
  {
    key: 'opt-ingest', kind: 'optimization', agentType: 'feature-dev:code-architect',
    prompt: `OPTIMIZATION RE-EVALUATION. Re-evaluate the INGEST pipeline (detector -> candidate -> promote; the chi-cluster pattern RULES S9; the at-scale drivers scripts/run_*_at_scale.py; post core/at_scale_base.py dedup). Given Workflow/parallel-agents, is this still the best orchestration, or is there a better shape (parallel detector runs over books, batched/streamed promote, a single unified driver replacing the ~10 clones)? CONFIRM-OPTIMAL or concrete BETTER PLAN; must stay idempotent and keep the canonical-coordinate guard at the promote boundary.`,
    label: 'find:opt-ingest',
  },
  {
    key: 'opt-render', kind: 'optimization', agentType: 'feature-dev:code-architect',
    prompt: `OPTIMIZATION RE-EVALUATION. Re-evaluate the RENDER-COVERAGE (scripts/render_coverage.py) + STANDALONE-BUILD (scripts/build_standalone.py — READ-ONLY, off-limits to edit) lanes plus the standalone EN back-translation lane. Are they optimal given current capabilities? CONFIRM-OPTIMAL or a concrete BETTER PLAN (you may RECOMMEND, never edit the standalone core).`,
    label: 'find:opt-render',
  },
]

// ----------------------------------------------------------------------------
// Helpers (identical semantics to deep-audit.js)
// ----------------------------------------------------------------------------
function panelSize(sev, kind) {
  if (DEPTH !== 'deep') return 1
  if (kind === 'optimization') return 1
  if (sev === 'critical') return 3
  if (sev === 'high') return 2
  return 1
}
function agentTypeForVerify(kind) {
  if (kind === 'optimization') return 'feature-dev:code-architect'
  if (kind === 'guard') return 'Explore'
  return 'feature-dev:code-reviewer'
}
function keyOf(f) {
  return ((f.file || '').toLowerCase().trim()) + '::' + ((f.title || '').toLowerCase().trim().slice(0, 90))
}
function dedupe(findings) {
  const seen = new Set(); const out = []
  for (const f of findings) {
    if (!f || !f.title) continue
    const k = keyOf(f)
    if (seen.has(k)) continue
    seen.add(k); out.push(f)
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
function verifyPrompt(f) {
  const common = `${PREAMBLE}

You are an ADVERSARIAL VERIFIER. Default to refuted=TRUE. Only set refuted=false if you INDEPENDENTLY confirm, by reading the cited code yourself, that the finding is real and material.

FINDING (dimension: ${f.dimension}, finder severity: ${f.severity}):
- title: ${f.title}
- file: ${f.file}   line: ${f.line}
- evidence: ${f.evidence}
- proposed fix: ${f.fix}
`
  if (f.kind === 'optimization') {
    return common + `
This is an OPTIMIZATION recommendation, not a bug. The finding claims the current project method is sub-optimal and proposes a better approach (or confirms it optimal). REFUTE unless the proposed approach is concretely, demonstrably better (faster / cheaper / higher-fidelity) AND feasible WITHOUT a paid API, WITHOUT touching the marathon core, and WITHOUT breaking the 9-edition byte-stability. If the finder said "confirmed optimal", set refuted=false only if you agree the current method is genuinely the best available today (else refute and explain the better path in reasoning). Set corrected_severity (info for a confirmed-optimal, low/medium for a worthwhile change, none if you refute the claim entirely).`
  }
  return common + `
Read the cited file/region. Check: (a) does the code actually do what the evidence claims? (b) is it a genuine defect, not intended behavior / already-guarded / dead-unreachable / a de-scoped item? (c) is the severity right (recalibrate down if the blast radius is bounded — e.g. no shipped-output corruption and the 9 KJV editions stay byte-stable)? (d) is the proposed fix correct AND safe (must not touch the marathon core; must keep the 9 KJV editions byte-stable; additive schema only)? Provide corrected_severity ('none' if refuted) and a corrected_fix if the finder's fix is wrong or unsafe.`
}

// verify ONE finding with a severity/kind-scaled adversarial panel -> verdict
function verifyOne(f, phaseTitle) {
  const size = panelSize(f.severity, f.kind)
  const atype = agentTypeForVerify(f.kind)
  return parallel(
    Array.from({ length: size }, (_, i) => () =>
      agent(verifyPrompt(f) + (size > 1 ? `\n\n[Skeptic ${i + 1}/${size} — verify independently.]` : ''), {
        label: `verify:${f.dimension}`,
        phase: phaseTitle,
        schema: VERDICT_SCHEMA,
        agentType: atype,
        model: 'sonnet',  // N95 cap=2; Sonnet ~2-3x faster latency + matches rounds 1-2 verify methodology
      })
    )
  ).then((votes) => {
    const panel = votes.filter(Boolean)
    const refutes = panel.filter((v) => v.refuted).length
    const refuted = panel.length === 0 ? true : refutes > Math.floor(panel.length / 2)
    return { ...f, panel, verdict: { refuted, refutes, panelSize: panel.length } }
  })
}

// ============================================================================
// PHASE 1 — verify the recovered candidates (barrier; fast; no slow finders competing)
// ============================================================================
log(`deep-audit-continue round ${ROUND} | recovered=${RECOVERED.length} candidates | missingFinders=${MISSING_DIMS.length} | repo=${REPO}`)
phase('VerifyRecovered')
const recoveredVerified = await parallel(RECOVERED.map((f) => () => verifyOne(f, 'VerifyRecovered')))
log(`  verified ${recoveredVerified.filter(Boolean).length}/${RECOVERED.length} recovered candidates`)

// ============================================================================
// PHASE 2 — run the finders that never completed (isolated; cannot starve verifies)
// ============================================================================
phase('FindMissing')
const missingFound = (await parallel(
  MISSING_DIMS.map((dim) => () =>
    agent(`${PREAMBLE}\n\n${dim.prompt}\n\nReturn findings via the structured output (empty array if nothing material).`, {
      label: dim.label,
      phase: 'FindMissing',
      schema: FINDINGS_SCHEMA,
      agentType: dim.agentType,
      model: 'sonnet',  // finder latency on N95 cap=2; matches original mint-10 finder model (sonnet-4-6)
    }).then((r) => {
      const arr = (r && Array.isArray(r.findings)) ? r.findings : []
      log(`  ${dim.label} -> ${arr.length} candidate finding(s)`)
      return arr.map((f) => ({ ...f, dimension: dim.key, kind: dim.kind }))
    })
  )
)).filter(Boolean).flat()
const missingDeduped = dedupe(missingFound)

// ============================================================================
// PHASE 3 — verify the newly-found candidates
// ============================================================================
phase('VerifyMissing')
const missingVerified = await parallel(missingDeduped.map((f) => () => verifyOne(f, 'VerifyMissing')))

// ============================================================================
// PHASE 4 — synthesize (same as deep-audit.js)
// ============================================================================
phase('Synthesize')
const verified = dedupe([...recoveredVerified, ...missingVerified].filter(Boolean))
const survivors = verified
  .filter((f) => f && !f.verdict.refuted)
  .map((f) => ({ ...f, finalSeverity: calibrateSeverity(f) }))
  .sort((a, b) => (rank[b.finalSeverity] ?? 0) - (rank[a.finalSeverity] ?? 0))
const dropped = verified.filter((f) => f && f.verdict.refuted)

log(`verified: ${survivors.length} survived, ${dropped.length} refuted (of ${verified.length} deduped)`)

const survForPlan = survivors.map((f) => ({
  dimension: f.dimension, kind: f.kind, severity: f.finalSeverity,
  title: f.title, file: f.file, line: f.line, evidence: f.evidence,
  fix: (f.panel || []).map((v) => v && v.corrected_fix).filter(Boolean)[0] || f.fix,
}))
const bugSurv = survForPlan.filter((f) => f.kind !== 'optimization')
const optSurv = survForPlan.filter((f) => f.kind === 'optimization')

let fixesPlanMarkdown = 'No surviving findings — nothing to plan.'
if (survForPlan.length) {
  const sevTally = survivors.reduce((a, f) => { a[f.finalSeverity] = (a[f.finalSeverity] || 0) + 1; return a }, {})
  const COUNT_LINE = `ROUND ${ROUND}: ${verified.length} deduped findings -> ${survivors.length} verified survivors / ${dropped.length} refuted. By severity: ${JSON.stringify(sevTally)}. Bug/correctness/etc = ${bugSurv.length}; optimization = ${optSurv.length}.`
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

const dims = ['correctness', 'security', 'code-debt', 'tests', 'docs', 'byte-stability', 'data-validity', 'concurrency-caching', 'cross-module', 'marathon-boundary', 'tests-run', 'opt-vision', 'opt-build', 'opt-ingest', 'opt-render']
const completeness = await agent(
  `${PREAMBLE}

This deep-audit round covered these dimensions: ${dims.join(', ')}.
Findings per dimension (survived / total verified):
${dims.map((k) => { const v = verified.filter((f) => f.dimension === k); const s = v.filter((f) => !f.verdict.refuted); return `  ${k}: ${s.length}/${v.length}`; }).join('\n')}
Surviving finding titles: ${survivors.map((f) => f.title).join(' | ') || '(none)'}

As a COMPLETENESS CRITIC, identify what this round likely MISSED — a subtree/module/data-set not searched, an invariant not checked, a failure mode a single-pass finder would skip, or a dimension that returned suspiciously little. Return concrete gaps + a finder lens for each (these seed the next convergence round). Be specific to THIS codebase, not generic.`,
  { label: 'synth:completeness-critic', phase: 'Synthesize', schema: COMPLETENESS_SCHEMA, agentType: 'feature-dev:code-reviewer' }
)

return {
  tool: 'deep-audit-continue',
  round: ROUND,
  now: NOW,
  depth: DEPTH,
  note: 'Continuation of killed run wf_ba367edc-a4a; 46 candidates recovered from completed finders + 4 missing finders re-run.',
  counts: {
    deduped: verified.length,
    survived: survivors.length,
    refuted: dropped.length,
    bySeverity: survivors.reduce((a, f) => { a[f.finalSeverity] = (a[f.finalSeverity] || 0) + 1; return a }, {}),
  },
  survivors: survivors.map((f) => ({
    dimension: f.dimension, kind: f.kind, severity: f.finalSeverity, originalSeverity: f.severity,
    title: f.title, file: f.file, line: f.line, evidence: f.evidence, fix: f.fix,
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

