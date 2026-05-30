# Scope addendum — χ-AI-notes (build-time AI-augmented note generation)

**Date:** 2026-05-09. Companion to `dev/PLAN_2026-05-09.md` §5.3
LONG TRACK. Stub spec; full implementation details elaborate when
the phase ships.

**Sibling spec:** `dev/SCOPE_2026-05-08-addendum-ai-xrefs.md` —
χ-AI-notes mirrors that phase's architecture; this addendum
documents what's *different*.

---

## 1. Why this is distinct from χ-AI-xrefs

| Axis | χ-AI-xrefs | χ-AI-notes |
|---|---|---|
| **What it produces** | Cross-reference proposals (verse → verse links) | New note text for sparse verses |
| **When it runs** | Corpus-time (one-shot enrichment of the master corpus) | Build-time per edition (publisher's editorial choice) |
| **Output kind** | `xref-thematic` | `comm-ai` (new kind, defaults disabled) |
| **Reviewer flag** | `[Reviewer: AI-proposed]` | `[Reviewer: AI-generated, requires human approval]` |
| **Cost gate** | Whole-corpus run ~$72 (one-time) | Per-edition opt-in; per-verse confirm-cost ~$0.002/verse |
| **Default state** | Off; user opts in via `--confirm-cost` | Off; per-edition opt-in via `enable_ai_notes: true` field |

The xref version proposes *links between existing content*. The
notes version proposes *new content* for verses where corpus is
sparse. Different prompts, different output schemas, different
reviewer workflows.

---

## 2. Architecture (mirrors χ-AI-xrefs where possible)

### 2.1 Reuse from χ-AI-xrefs (already shipped infrastructure)

  - `scripts/core/sources.py:_anthropic_client()` — cached SDK
    instance (lru_cache), ANTHROPIC_API_KEY env-var sourcing,
    SourceMissingError on unconfigured environments
  - `scripts/core/sources.py:AI_XREF_CACHE_TTL = "1h"` — same
    1-hour ephemeral cache TTL pattern
  - `scripts/run_ai_xrefs_at_scale.py` driver pattern — `--dry-run`,
    `--max-verses N`, `--confirm-cost`, `--model`, merge-not-clobber
  - Project's existing `scripts/core/http.py` retry/timeout policy
    via ω.10
  - Anthropic SDK's prompt-caching surface (system prompt ≥ 4096
    tokens for Haiku 4.5 minimum cacheable prefix)

### 2.2 New for χ-AI-notes

  - **`AnthropicNoteClient`** in `scripts/core/sources.py` —
    sibling of `AnthropicXrefClient`; same lazy + injectable
    `completion_fn` pattern; different system prompt + output
    schema + telemetry
  - **`AI_NOTE_SYSTEM_PROMPT`** — ~5K-token padded system prompt
    with worked examples of: explanatory notes (1-2 sentences,
    historical/literary/contextual), study notes (verse-anchored
    devotional + bridge), translation notes (idiom +
    cultural-context unpacking). Anti-patterns: don't speculate,
    don't theologically advocate, don't fabricate citations.
  - **`AI_NOTE_OUTPUT_SCHEMA`** — JSON-schema constraint for
    `output_config.format`. Output: `{verse_anchor, note_label,
    note_body, confidence, sources_consulted, reviewer_flags}`.
  - **`AINoteDetector`** in `scripts/core/detectors.py` — emits
    `comm-ai` candidates; attribution string contains
    "Claude AI build-time"; body composes verse-anchor + note-text
    + `[Reviewer: AI-generated, requires human approval]` flag
  - **`scripts/run_ai_notes_at_scale.py`** — driver mirroring
    `run_ai_xrefs_at_scale.py`. Cost guards identical:
    `--max-verses N` default 100, `--confirm-cost` required when
    `--max-verses > 200`, projected-cost dry-run.
  - **New kind in `content/kinds.yaml`** — `comm-ai`, category=comm,
    symbol=Ⓐ (or other distinct glyph), default-disabled in every
    existing edition; per-edition opt-in.
  - **`enable_ai_notes`** boolean field on edition records — when
    true, the build pipeline includes `comm-ai` notes in that
    edition's filter; defaults to false (no behavioral change for
    existing 5+4 editions).

### 2.3 Cost projection

  - Haiku 4.5 with cached system prompt: input $0.80/M tokens
    (cached) → ~5000 cached system + 200 per-verse user → ~$0.001
    cache + $0.0002/verse query + $0.0008/verse output ≈
    **$0.002/verse**
  - 31K-verse corpus full pass: ~$62 (vs χ-AI-xrefs ~$72; lighter
    output schema)
  - Targeted "sparse verses only" pass (5K verses): ~$10

### 2.4 Reviewer workflow

  1. Publisher selects an edition with sparse coverage
  2. /customize → AI Notes panel → "Generate first-draft notes
     for verses with < 2 existing notes" (filter is
     publisher-configurable)
  3. Cost preview shown: "$X for ~N verses"
  4. Publisher confirms; driver runs
  5. Generated candidates land in `content/candidates/<book>_ai_<chapter>.json`
     with explicit `comm-ai` kind tag
  6. Publisher reviews each candidate in /sources or a new
     /ai-review console; approves or rejects
  7. On approve, candidate promoted to `content/notes/<book>.py`
     via existing `batch_promote_xrefs.py --kind comm-ai`
  8. Edition rebuilds with the now-included AI notes (filtered by
     the existing canon ∩ kinds machinery)

---

## 3. Tests

  - **AnthropicNoteClient** — same shape as `TestAnthropicXrefClient`:
    SourceMissingError on no API key, lazy completion_fn, prompt
    cache ≥ 4096 tokens, last_usage telemetry, output schema
    validation, defensive degradation on malformed completions.
  - **AINoteDetector** — emits comm-ai candidates with proper
    attribution; degrades gracefully when AnthropicNoteClient
    raises; respects reviewer-flag invariant.
  - **run_ai_notes_at_scale.py** — `--dry-run` exits 0 without
    API call; `--max-verses` default 100; `--confirm-cost` gates
    >200; merge-not-clobber preserves prior detector candidates.
  - **edition.yaml schema** — `enable_ai_notes` defaults false;
    setting true exposes comm-ai kind in the build filter; round-
    trip via api_save_edition_meta.

---

## 4. Open questions (to resolve when phase ships)

  - **Symbol for `comm-ai` kind** — Ⓐ, ✨, 🤖, AI, ◇? Default
    proposal: Ⓐ as a discreet circled-A.
  - **Should χ-AI-notes write to `content/candidates/` only, or
    direct to `content/notes/`?** Proposal: candidates only.
    Promotion is a deliberate human step (matches χ.6 / χ.7 /
    χ.1 / χ-AI-xrefs convention).
  - **Per-verse confidence score** — should publisher see / sort by
    it? Proposal: yes, surfaced in /ai-review console; threshold
    filter at a configurable default (0.65 mirroring detector
    convention).
  - **Multi-tradition awareness** — when an edition has tradition
    filter (post ψ.8), should AI notes be tradition-tagged?
    Proposal: yes, system prompt includes the edition's
    tradition list; output schema has `tradition` field.

These resolve at ship time when implementation is concrete.
