# Lane-Coordination v2 — Design (2026-06-08)

**Status:** adopted 2026-06-08 (Mac lane, user-directed: "revamp the whole baton system").
**Supersedes** the single-baton work-mutex of `docs/superpowers/specs/2026-06-03-lane-handoff-baton-system-design.md` (kept for history; its file/Python/hook scaffolding is reused — only the *model* changes).

## Why a revamp

The v1 baton modeled coordination as a single exclusive token: "exactly one lane **holds the baton** = the active worker AND the sole pusher AND the truth-record owner." Two things broke that model:

1. **The bandwidth-first cadence (2026-06-08, RULES §4 + `session-operating-doctrine`).** Each lane now commits locally and pushes only at its own milestones, with `scripts/lane_ping.py` keeping the protected-`main` push a clean fast-forward. So "only the holder pushes" is obsolete — **both** lanes push, at different times, coordinated by the radar, not by an exclusive token.
2. **`holder` was overloaded and actively hid work.** It meant "active worker" *and* "sole pusher" *and* "who the SessionStart `incoming` banner fires for." In practice the lanes have run **file-disjoint in parallel** for most of the project (website vs build pipeline; audit dims; research), with the baton pinned to one lane while the other worked "regardless." The concrete failure: turn 23 was a *Mac-directed* handoff (Mac TODOs) written with `holder: windows` (Windows kept push/merge ownership) → `do_incoming` only fired when `holder == lane` → **the handoff never surfaced to Mac**, and `/resume` told Mac to STOP. The system hid Mac's own assignment from Mac.

Two more papercuts: the engine **clobbered** the handoff body on each `handoff` while humans **appended** turn sections (history mismatch); and stale done-TODOs accreted at the top and misled (the v0.0.3 `.dmg` "MAC TODO" was still listed after it had shipped).

## Model: mode + task-board + truth-owner

The board (`dev/LANE_HANDOFF.md`) is a **task assignment + truth-record ownership** record, not a work-mutex. Frontmatter:

```
mode: parallel        # parallel (default) | exclusive
turn: N               # monotonic
from: <lane>          # who wrote this update
updated: <iso>
status: working | handing-off
mac: <one-line task or "idle">       # each lane's current assignment
windows: <one-line task or "idle">
truth_owner: <lane>   # owns SESSION_STATE/IN_FLIGHT/CHANGELOG + any merge-commit this period
holder: <lane>        # back-compat alias of truth_owner (exclusive mode = the sole shared-file worker)
```

- **parallel (the default now):** lanes work **file-disjoint**; each does its own `<lane>:` task; **both commit locally + push at milestones** (radar-gated). `truth_owner` is the only lane that edits the shared truth-records + does merges → no dual-edit conflict. An `idle` lane takes the top backlog item.
- **exclusive:** the old mutex — `holder` is the **sole worker on shared files**; the other lane idles or does disjoint side-work; only the holder mutates the shared files. Use **only** when both lanes would otherwise touch the SAME files (e.g., a content-store re-ingest + bake).

Why this is right: it matches how the lanes actually run (parallel, file-disjoint, both pushing) while preserving an explicit escape hatch (`exclusive`) for the genuinely-shared-file case the v1 mutex was built for. Truth-record ownership still follows one lane → the dual-edit-conflict guarantee survives.

## Engine — `scripts/lane_handoff.py` (pure, tested, cross-platform; no git side effects)

- `status` — prints `mode`, `turn`, both lanes' tasks, `truth_owner`, and a `YOU (<lane>): <task>` line (+ an exclusive-mode wait notice).
- `handoff --to <lane> [--mode m] [--mac t] [--windows t] --done --next [--watch] [--force]` — **transfers** truth-ownership to `<lane>` (sets `truth_owner` + `holder`), sets mode/tasks, bumps `turn`, **preserves history** (prepends a `## ▶ from → to (turn N)` block — no clobber). Refuses if the caller is not the current `truth_owner` (override `--force`).
- `assign [--mode m] [--mac t] [--windows t] [--note ..]` — updates the board **in place** with **no refusal** (either lane may set its own task / the mode for parallel coordination); does not transfer ownership.
- `incoming` (**the fix**) — exit 0 + banner iff `turn > last-seen` **AND** work is addressed to this lane: `<lane>:` is a non-idle task **OR** `truth_owner == lane`. No longer gated on `holder`.
- `mark-seen` — records the seen turn (called by `/resume`).
- `prune [--keep N]` — trims old turn sections to `dev/archive/LANE_HANDOFF_LOG.md`, always keeping the `STANDING` block + the most recent N (caps the live file → less confusion, less context to read).

Back-compat: old-format boards (only `holder/from/turn/updated/status`) parse and behave (`mode`→`parallel`, `truth_owner`→`holder`); the v1 tests pass unchanged.

## Slash commands (`.claude/commands/`)

- **`/handoff <to-mac|to-windows>`** — reconcile truth-records → `handoff --to … --mode … --mac … --windows …` → (optional `prune`) → commit → **radar-gated milestone push** (`lane_ping --before-push` → `git pull --rebase` if BEHIND → push both remotes; Mac may use `dev/save_mac.sh`).
- **`/resume`** — fetch → radar/rebase → read the board → **parallel: pick up YOUR task (do NOT stop when `truth_owner` ≠ self)**; exclusive: if the other lane holds, do disjoint side-work or wait → `mark-seen` → begin.
- **`/sync`** — radar-gated milestone push for **either** lane, no ownership transfer.

## Out-of-repo (per-box, NOT shared — each lane wires its own)

The script + commands + spec travel via git. Each box additionally wires, in its own (gitignored) config: (1) the **SessionStart hook** runs `lane_ping.py --quiet` + `lane_handoff.py incoming`; (2) the **save path** runs `lane_ping.py --before-push` (Windows: `save-all.ps1`; Mac: `dev/save_mac.sh`). Each lane also mirrors the model into its own memory (`reference_lane_coordination`, `reference_lane_ping`). The landing lane passes the mirror instruction to the other via `dev/LANE_HANDOFF.md` (the Guard #4 banner pattern).
