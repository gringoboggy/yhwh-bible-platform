# Fable-5 system mint — design (program step ①, addendum 3)

**Status:** DESIGN 2026-06-10 — written while the round-7 audit runs; implementation lands NEXT session with the audit's claude-setup findings in hand (the audit is evidence for exactly this redesign; implementing first would discard it).

**Goal (user, 2026-06-09):** "max brain power for the least bandwidth" + zero what's-what ambiguity. Token-efficiency as a first-class design goal across RULES / PLAYBOOK / hooks / memory / boards: slim what's re-read every session, deduplicate rule sources, single-home + self-enforce each rule, prefer deterministic hooks over prose Claude must re-read.

## 1. Measured every-session read surface (2026-06-10, tonight)

| Surface | Size | Lines | Read when | Diagnosis |
|---|---|---|---|---|
| `dev/CLAUDE_PROJECT_RULES.md` | **90.0 KB** | 1,298 | every session, full (triad #1) | ~22-25k tokens/session. The single biggest lever. Carries rules + history-flavored exposition + worked examples that belong in archive/topic docs. |
| `dev/SESSION_STATE.md` | **106.4 KB** | 102 | triad #2 (truncates on Read) | 44 entries vs the lint's budget of 2 (`truth_record_budget` warns NOW). Only the top 1-2 entries are live state. |
| `dev/PLAN_2026-05-29-roadmap.md` | 16.7 KB | 179 | triad #3 | Healthy. |
| `dev/IN_FLIGHT.md` | **152.8 KB** | 179 | top-read each session | Same rot class as SESSION_STATE — months of closed entries. |
| `dev/LANE_HANDOFF.md` | **117.6 KB** | 377 | each lane boot | Board archaeology; only the frontmatter + the latest 1-2 turns are live. |
| `dev/SESSION_PLAYBOOK.md` | 16.4 KB | 83 | on demand | Healthy. |
| `MEMORY.md` (index) | 16.8 KB | 81 | every session (auto-loaded) | Trimmed TONIGHT 25.4→16.8 KB (was over the 24.4 KB load cap — entries were absorbing topic-file detail; the cap breach silently truncated recall). |
| memory topic files | 261 KB / 81 files | — | on recall only | Lazy-loaded; size fine. Hygiene rule needed so index lines stay one-line hooks (see §3.4). |
| SessionStart hooks | 3.6 KB script | — | every session | Output is lean; fine. |
| `.remember/remember.md` | 0 KB | — | consumed at boot | Working as designed. |

**Reality check on the bandwidth math:** the triad alone is ~50-55k tokens of every-session input before any work happens (RULES ~23k + SESSION_STATE-as-truncated ~12k + roadmap ~4k + IN_FLIGHT top + boards + hook output + MEMORY.md ~4k). Halving it saves ~25k tokens × every session × both lanes.

## 2. Design principles (the redesign's contract)

1. **Single-home per rule.** Every rule has exactly ONE authoritative home; every other surface may carry at most a one-line pointer. Home assignment: *behavioral doctrine* → RULES; *procedures/checklists* → PLAYBOOK; *per-box environment facts* → that box's memory; *live state* → SESSION_STATE top; *cross-lane assignments* → LANE_HANDOFF frontmatter. (Today the save cadence lives in 4 places — RULES §4 + guard #5 + `reference_save` + `session-operating-doctrine` — every restatement is drift surface; this session read all four.)
2. **Deterministic mechanism over re-read prose.** A rule that a hook/lint can enforce gets the hook/lint, and its prose shrinks to one line + the enforcement pointer. Already-proven pattern: the pre-commit gate, `lint_rules.py` (33 checks), the SessionStart triad hook, `lane_ping --before-push`.
3. **Truth records are FIFO queues, not ledgers.** `scripts/rotate_truth_records.py --apply` already exists and the lint already warns; rotation becomes a STANDING part of milestone saves (or a SessionEnd hook), not a manual rescue. CHANGELOG remains the permanent ledger.
4. **History is archive, not bootstrap.** RULES keeps the rule + the one-line "why"; multi-paragraph case studies move to `dev/archive/RULES_HISTORY.md` (the extraction pattern RULES already started).
5. **Zero what's-what ambiguity.** One table (in RULES §0) names every surface and its single purpose (the §1 table above is the seed).

## 3. Proposed changes (implement NEXT session, audit findings in hand)

**3.1 Rotate the truth records (mechanical, zero-risk, biggest cheap win).** `py -3 scripts/rotate_truth_records.py --apply` → SESSION_STATE 106→~10 KB, IN_FLIGHT 153→~10 KB. Deferred tonight ONLY to keep the audit's read substrate stable mid-run. Then: wire rotation into `save-all.ps1` (post-commit, pre-push) so the budget never breaches again — the lint stays as the tripwire, the save script becomes the actor.

**3.2 RULES diet (90→~45-50 KB target, NO rule deleted).** For each §: keep the rule statement + enforcement pointer + one-line why; move worked examples/history to RULES_HISTORY. Candidates visible without the audit: §9 mental models (~28 KB — keep the recipes but the 4 longest ones carry full code blocks already duplicated in the codebase/specs they cite); the guards' multi-paragraph origin stories; §4's save narrative (duplicates `reference_save` + `save-all.ps1` behavior — the script IS the spec). **GATED on the audit's claude-setup dim:** its duplication/contradiction findings decide the exact cut list (do not pre-empt).
**3.3 LANE_HANDOFF board rotation.** Same FIFO treatment: frontmatter + latest 2 turns live; older turns → `dev/archive/LANE_HANDOFF_HISTORY.md`. Extend `rotate_truth_records.py` (it already knows the entry format family) or a small sibling.
**3.4 Memory hygiene as standing rules (adopted TONIGHT for new writes):** (a) an index line is a ≤200-char hook + pointer — detail lives in the topic file ONLY (tonight's breach: index lines had absorbed updates until the file blew its own load cap); (b) every UPDATE goes into the topic file, never appended to the index line; (c) the reconciliation sweep (automate-claude doctrine) prunes superseded topic files at milestones.
**3.5 Hook candidates (deterministic > prose) — evaluate against audit findings:** (i) rotation-on-save (3.1); (ii) a SessionEnd junk-sweep check (PLAYBOOK §6.5 is prose today); (iii) a pre-push lane-board freshness check; (iv) the RAM-clear step as a script the hook prints the result of, instead of 14 lines of instruction prose re-read every boot.
**3.6 What's-what table** lands at RULES §0 top (the §1 table, minus sizes).

## 4. Explicitly NOT changing

- The triad READ ORDER + the "read it in full" bootstrap contract (the design slims the files, not the discipline).
- The two-layer automation doctrine (memory + hooks) — this design IS that doctrine applied to itself.
- CHANGELOG (the permanent ledger; its 1.1 MB is within its own budget and it is not an every-session read).
- No rule is deleted anywhere — relocation + deduplication only ([[feedback_bring_solutions_dont_remove]] applies to rules too).

## 5. Sequencing

1. Tonight: this design + MEMORY.md trim (DONE) + the round-7 audit gathers the claude-setup evidence.
2. Next session (P3): triage audit findings → execute 3.1 (rotation) first (mechanical), then 3.2/3.3 informed by the duplication/contradiction findings, then 3.5 hooks; each slice = local commit + the lint suite green.
3. The end-game master plan (program ④) inherits the slimmed system as its substrate.
