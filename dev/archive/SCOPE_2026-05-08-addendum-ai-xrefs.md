# Scope addendum — χ-AI-xrefs (LLM-backed thematic cross-references)

**Added:** 2026-05-08, after χ.0 Kenyon shipped (corpus 16,042 / 25K
v1.0 floor; 8,958-note gap remaining). The user's cost gate on this
phase was lifted on 2026-05-08; per memory `project_ai_xrefs_unfunded.md`
this is the next-most-logical χ phase.

## Origin

The static χ-cluster sources (TSK, Strong's H/G, Nave's, Kenyon)
together cap out at the **explicit-citation** and **single-keyword**
classes of cross-reference. They do not surface:

- **Typological links** (Adam→Christ; Joseph→Christ; the brazen
  serpent → John 3:14 etc.). TSK has *some* of these but only where
  they were considered conventional by 1830s Reformed editors.
- **Thematic resonance** across canon (e.g. "remnant" theology
  through Isaiah → Romans; "wilderness" trope from Exodus → Mark).
- **Idiomatic / phraseological** echoes that no English keyword map
  catches (Hebrew/Greek figures of speech that survive translation).

These are the cross-references a careful pastor or scholar would
notice on a re-read but the static sources lack. An LLM is a good
proposer for them — not a final author, but a generator of draft
candidates that a reviewer trims to the strongest one or two.

## Why this is its own χ-phase

It belongs in the corpus as a new note **kind** (`xref-thematic`
under the existing `xref` category, `‖` symbol). It is
denominationally neutral (`tradition=cross`) — thematic links cross
all five seeded editions.

It does **not** replace TSK or any of the static χ sources. They run
independently; their outputs co-exist in `content/candidates/`. The
batch promoter's `--kind xref-thematic` filter scopes promotion.

## Realistic corpus delta

KJV ships ~31,102 verses across the Reformed-66 canon. At top-N=3
candidates per verse with a confidence floor of 0.7 plus reviewer
filtering at promote time, the realistic promotable yield is
**~5,000–15,000 notes**, scoping toward the lower end on first pass
because reviewers will (correctly) reject many AI-proposed links as
too thin. Re-running with a tightened prompt or a higher confidence
floor is cheap once the infrastructure exists.

## Cost model (the new variable in this phase)

Per-verse cost with `claude-haiku-4-5-20251001`, prompt-cached system
prompt, ~150 input tokens per verse + ~200 output tokens:

```
input  : 150 tok × $0.80 / 1M tokens   = $0.00012
output : 200 tok × $4.00 / 1M tokens   = $0.00080
total  : ~$0.00092 per verse
                     × 31,102 verses   ≈ $28.61   (full pass)
                     × 5,000 verses    ≈ $4.60    (one-book scope)
                     × 100 verses      ≈ $0.09    (smoke run)
```

Sonnet 4.6 would be ~10× more expensive (~$300 full pass). Haiku 4.5
is the right model for the volume; the prompt is tightly templated
and the task (propose 3 thematic xrefs) is well within Haiku's
range. The driver supports a `--model` flag for re-runs at higher
quality if the corpus warrants it.

The driver's `--dry-run` flag prints the projected cost before any
API call and exits. The driver refuses to run more than 200 verses
without an explicit `--confirm-cost` flag.

## Pipeline shape (mirrors the §9 χ-cluster pattern)

```
ANTHROPIC_API_KEY env  →  AnthropicXrefClient            →  AIXrefDetector              →  candidates JSON          →  promoted notes
+ anthropic SDK           (scripts/core/sources.py;          (scripts/core/detectors.py;     (content/candidates/         (content/notes/<book>.py)
                          lazy + injectable                   verse-text-driven; kind          <book>_ch_<NNN>.json,        xref-thematic, tradition=cross
                          completion_fn for tests)            = xref-thematic)                merge-not-clobber)
```

Same shape as every other χ phase. The novelty is the source isn't a
cached JSON file on disk; it's the Anthropic API itself.

## Implementation steps

1. **Register kind** `xref-thematic` in `content/kinds.yaml`:
   - `category: xref`
   - `symbol: ‖` (inherits)
   - `note_class: note-xref-thematic`, `marker_class: marker-xref-thematic`
   - `label: Thematic`
   - `title_attr: AI-proposed thematic / typological cross-reference`
   - `description: LLM-proposed thematic, typological, or idiomatic
     cross-reference. Drafted by Claude AI; trimmed and rewritten by
     a reviewer before promotion.`
   - `phase: mvp`

2. **Source loader.** `AnthropicXrefClient` in `scripts/core/sources.py`:
   - `__init__(*, model="claude-haiku-4-5-20251001", completion_fn=None)`
     where `completion_fn` is the injectable callable that returns a
     parsed list of dicts. Default uses the `anthropic` SDK.
   - Construction raises `SourceMissingError` when `completion_fn` is
     None AND (`ANTHROPIC_API_KEY` env var is absent OR the
     `anthropic` package is not importable). Mirrors NaveTopical's
     graceful-degrade contract — `prospect.py` skips the detector
     silently rather than 500-ing.
   - `propose_xrefs(book, chapter, verse, verse_text, *, top_n=3)`
     returns a list of result dicts with shape `{"target_book",
     "target_chapter", "target_verse", "kind_subclass", "reasoning",
     "confidence"}`. The method validates each result against the
     known canon book codes; unknown codes are dropped silently.
     Malformed JSON from the model returns `[]` (defensive).
   - System prompt is constructed once and passed with
     `cache_control: {"type": "ephemeral"}` so per-verse calls only
     pay for the per-verse user message after the first call.
   - Singleton via `anthropic_xref_client()` lru_cache.

3. **Detector class.** `AIXrefDetector` in `scripts/core/detectors.py`:
   - `name = "AIXrefDetector"`, `kind = "xref-thematic"`.
   - `__init__(*, client=None, top_n=3, min_confidence=0.7)`. When
     `client` is None, lazy-loads `sources.anthropic_xref_client()`.
     SourceMissingError propagates to prospect.py's resilient
     instantiation handler.
   - `detect(book, chapter, verse, verse_text)` calls
     `client.propose_xrefs(...)` and emits one Candidate per result
     above the confidence floor. The Candidate's `draft_body`
     formats the target reference + the model's reasoning + a
     reviewer note explicitly flagging the AI provenance.
   - Source attribution string: `"Claude AI (claude-haiku-4-5,
     2026); reviewer-curated."` — never claims unattributed
     authorship.
   - Registered in `ALL_DETECTORS`.

4. **Driver.** `scripts/run_ai_xrefs_at_scale.py`:
   - Mirror of `run_greek_at_scale.py` (NT-only there → all-66 here)
     with cost guards layered on top.
   - Iterates KJV verses in canonical order, calls the detector per
     verse, writes per-chapter candidate JSON in prospect's exact
     format, merge-not-clobber on existing files.
   - Flags:
     - `--books a,b`: scope to listed canonical book codes
     - `--max-verses N` (default 100): hard cap on API calls
     - `--min-confidence X` (default 0.7): drop weaker candidates
     - `--dry-run`: print projected cost + verse count, exit 0 with
       no API call
     - `--confirm-cost`: required when `--max-verses > 200`
     - `--model M`: model id passthrough (default haiku-4-5)
   - Prints a per-book summary at the end and the next-step hint
     `python3 scripts/batch_promote_xrefs.py --kind xref-thematic`.

5. **Smoke + batch promote.** Run `--books jhn --max-verses 50
   --dry-run` first to confirm the cost is what you expect. Drop
   `--dry-run` for the real call. Inspect a sample candidate JSON,
   then a wider `--books rom,gal,heb --max-verses 500` Pauline
   slice, then promote with the existing batch promoter using
   `--kind xref-thematic`.

6. **Verify.** `pytest` passes; `lint_rules.py` passes; attribution
   audit shows the new AI-attributed notes correctly tagged.

7. **CHANGELOG entry** with cumulative corpus math.

## Tests

Per the §9 χ-cluster pattern. All synthetic — no real API calls.

- **AnthropicXrefClient unit tests:**
  - Missing `ANTHROPIC_API_KEY` AND no injected `completion_fn` →
    `SourceMissingError` on construction.
  - Injected `completion_fn` works without env var.
  - `propose_xrefs` returns parsed list when `completion_fn` returns
    valid JSON dict list.
  - Malformed completion → empty list (defensive).
  - Unknown book codes in completion → silently dropped.
  - Confidence outside [0, 1] → clamped or dropped.

- **AIXrefDetector unit tests:**
  - `SourceMissingError` from `__init__` when no client + no key.
  - Stub client returning N proposals → N Candidates with
    `kind="xref-thematic"`.
  - `min_confidence` floor filters weak proposals.
  - `top_n` cap honored even when client returns more.
  - Source attribution string contains "Claude AI" (provenance
    invariant).
  - Registered in `ALL_DETECTORS`.

- **Driver unit tests** (against synthetic verse fixtures + stub
  client):
  - `--books` filter scopes correctly.
  - `--max-verses` hard cap honored.
  - `--dry-run` writes nothing, prints estimate, exits 0.
  - `--confirm-cost` required for `--max-verses > 200`; absent →
    exit 1 with explanatory message.
  - Idempotent re-run: merge-not-clobber on existing per-chapter
    file (existing non-`xref-thematic` candidates preserved).
  - Per-book stats reported.

- **Kind registration** (one-line smoke):
  - `xref-thematic` is present in `content/kinds.yaml`.

Target: ~18-22 new tests across 3-4 classes.

## Tradeoffs / known limits

- **Reviewer load.** AI proposals need careful curation. The note
  body explicitly flags AI provenance with a `[Reviewer:]` note;
  the conservative confidence floor (0.7) and top-N cap (3) keep
  the noise tractable.
- **No streaming, no batch API for v1.** The 5-15K note delta is
  done in one driver run; using the batch API would halve cost but
  adds complexity that doesn't pay back at this volume. Revisit if
  a re-pass at higher quality is needed.
- **Model lock-in.** `claude-haiku-4-5-20251001` is hard-coded as
  the default; the driver's `--model` flag handles override. Prompt
  caching survives model changes (the system prompt is re-cached
  per model).
- **No internet during tests.** Every test path uses the injected
  `completion_fn`. The real SDK call lives behind a single
  `_default_completion_fn` that the tests never reach.
- **English-only.** Verse text is KJV; the prompt asks for English-
  expressed reasoning. Future τ-cluster translations don't change
  this — the AI still reasons in English about whatever verse text
  is fed in.

## v1.0 inclusion

χ-AI-xrefs is the largest unblocked corpus-growth lever toward the
v1.0 floor (corpus ≥ 25K notes per memory `project_v1_terminus.md`).
Conservative reviewer-promote yield of ~5K notes alone closes about
half of the 8,958-note gap. With the parallel free user-side
unblock of χ.7 Nave's (+2-3K) and χ.1 Strong's Greek (+5-10K), the
v1.0 corpus floor becomes attainable in one or two more sessions.

After χ-AI-xrefs ships, the most-logical-path remaining is **ω.5
paths refactor → θ.1 launcher → θ.2 native shell** for the v1.0
candidate.
