# Lane-Handoff Baton System — Design

> **⚠ SUPERSEDED 2026-06-08 by `2026-06-08-lane-coordination-v2-design.md`** — the single
> exclusive-baton model below was replaced by a `mode: parallel|exclusive` + per-lane
> task-board + `truth_owner` model (the file/Python/hook scaffolding here is reused; only
> the *model* changed). Kept for history.

**Status:** design (direction approved 2026-06-03 — baton / turn-based). Supersedes the Windows↔Mac half of the parallel-operation protocol in `plans/2026-06-02-samkings-cloud-agent-workflow-and-run-plan.md` (the pod lane keeps that protocol's single-committer rule; this is the two-workstation lane).

## Problem

Two Claude lanes — **Windows (N95)** and **Mac (2017 iMac)** — share the git remotes (GitLab `origin` + GitHub `github`) and one Max subscription. Coordinating them is currently manual: the user relays "Mac pushed → Windows pull," sequences who pushes, and one lane's commits can strand locally (Windows was pull-only, so its P0 work sat unreachable). 

**Goals (user-chosen 2026-06-03):**
1. **No manual relay** — each lane detects an incoming handoff itself; the user triggers with one word, or it auto-surfaces at session start.
2. **Nothing strands** — both lanes' work reliably reaches the remotes + the other lane.
3. **Shared task board** — a committed note of who's active, what was just finished, and what the other picks up next; either lane can resume the other cleanly.

**Out of scope (deselected):** quota-safety signaling.

## Model: turn-based baton

Exactly one lane **holds the baton** at a time. The holder is the active worker **and** the sole pusher that turn, and **owns the shared truth-records** (SESSION_STATE / IN_FLIGHT / CHANGELOG) that turn. A handoff flips the baton to the other lane and pushes. 

Why this model:
- Only the holder pushes → every push is a clean fast-forward (**zero clobber**), and the holder can push anytime → its work **never strands**.
- Making truth-record ownership follow the baton **eliminates the dual-edit conflict** that the manual flow risks (it only worked last time because Mac happened not to touch them).
- Matches reality: the user drives **one machine at a time**.

## Channel: git only

No external hooks/services (honors memory `feedback_no_external_hooks`; subscription-only). The shared state is a committed file; lanes exchange it by push/pull. Everything below is built from files in the repo (which travel to both machines) plus per-machine hook shims.

## Components

### 1. The baton file — `dev/LANE_HANDOFF.md` (committed)
One file: a machine-parseable YAML header + a human task-board body.
```
---
holder: windows          # windows | mac — active worker + SOLE pusher this turn
from: mac                # who last handed off (init: windows)
turn: 7                  # monotonic handoff counter (ordering / staleness)
updated: 2026-06-03T20:14:00Z
status: working          # working | handing-off
---
## Done (last turn, mac -> windows)
- <what the giver finished>
## Next (this turn, windows picks up)
- <what the receiver should do>
## Watch-outs
- <gotchas, in-flight caveats, files touched>
```
Only the holder writes it → no concurrent writes in the normal flow.

### 2. Deterministic core — `scripts/lane_handoff.py` (pure Python, tested, cross-platform)
The real logic lives here so it is unit-testable and identical on both OSes. Subcommands manipulate + validate the file with **no git side effects**:
- `status` — print holder / turn / from / updated, and whether THIS lane holds the baton.
- `handoff --to <windows|mac> --done <text> --next <text> [--watch <text>]` — assert this lane is the current holder; flip `holder`→target, `from`→me, `turn`++, `updated`=now; rewrite the body. Exit non-zero if this lane isn't the holder (override with `--force`, which logs a warning).
- `incoming` — for the SessionStart hook: exit 0 + print a one-line banner **iff** the baton is addressed to this lane and `turn` > last-seen; else exit 1 (nothing pending). Tracks last-seen in a gitignored `dev/.lane_seen`.

**Lane identity:** a gitignored `dev/.lane` file containing `windows` or `mac`, set once per machine (fallbacks: `$YHWH_LANE`, then a hostname heuristic).

### 3. Slash commands (markdown prompts; travel via git)
Require a `!.claude/commands/` un-ignore in `.gitignore` (today `.claude/*` is ignored with negations only for `settings.json` + `workflows/`). The commands are thin orchestrators that call the Python core + run git:
- **`/handoff <to-mac|to-windows> [note]`** (giving side): (a) reconcile the truth-record for the work done (holder owns it this turn); (b) `lane_handoff.py handoff …`; (c) commit; (d) `git fetch && git rebase origin/main && git push origin main && git push github main`; (e) report "baton → <receiver>."
- **`/resume`** (receiving side): (a) `git fetch` both remotes; (b) `lane_handoff.py status`; (c) if `holder == this-lane` → `git rebase origin/main` (combine) + print the Done/Next/Watch-outs note + "you now hold the baton"; else report "baton still with <holder>" (offer `--force`).
- **`/sync`** (mid-turn, holder only): `git fetch && git rebase origin/main && git push …` **without** flipping the baton — durability without handing off.

### 4. SessionStart auto-check (the "no manual relay" piece) — both machines
Each fresh session: `git fetch` (quiet) → `lane_handoff.py incoming` → if pending, print a banner: `⮕ INCOMING HANDOFF from <from> (turn N) — run /resume to pull+combine: <next-summary>`.
- **Windows:** add the check to `dev/cc-hooks/bootstrap-triad.ps1`.
- **Mac:** new `dev/cc-hooks/bootstrap-triad.sh` + Mac's hook config.
- ⚠ **Shared-settings hazard:** `.claude/settings.json` is committed + shared, so its SessionStart hook command **cannot be a Windows-only `.ps1`**. Resolve by an OS-dispatching hook command (run the `.ps1` on Windows, the `.sh` on Mac) — e.g. a single committed entry that detects the OS, or per-machine local-settings overrides. Pin this in the plan's first task.

## Data flow (one handoff)
Windows holds the baton → works → `/handoff to-mac "done X / next Y"` → writes `LANE_HANDOFF.md` (holder=mac, turn++), commits, pushes both remotes. Later the user opens Mac Claude → SessionStart fetches + sees holder==mac & turn>last-seen → banner "incoming from windows" → `/resume` → Mac rebases/combines, reads Done/Next, now holds the baton. Reverse is symmetric.

## Edge cases
- **Divergent baton** (both think they hold it, e.g. after a `--force`): the `turn` counter + `holder` field arbitrate; higher `turn` wins; `/resume` and `/handoff` check `holder` first.
- **Conflict on `LANE_HANDOFF.md`**: shouldn't occur (only the holder writes); if forced, higher `turn` wins on manual resolve.
- **Truth-record conflicts** (the real pain): eliminated by rule — only the holder edits SESSION_STATE / IN_FLIGHT / CHANGELOG that turn.
- **Mac mid-setup:** initial state `holder: windows` (Windows active); first `/handoff to-mac` when Mac is ready.
- **A lane just stops (forgets `/handoff`):** the other lane's `/resume` sees the baton still with the absent lane → `--force` takes it (logged warning) after the user confirms the absent lane is idle.

## Testing
- `tests/test_lane_handoff.py`: file parses; `handoff` flips holder + bumps turn + refuses a non-holder; `incoming` exit codes + last-seen tracking; a round-trip (windows→mac→windows) preserves invariants; the `--force` path. Pure-Python core → **no git in tests** (run with `--basetemp` per memory `reference_pytest_basetemp`).
- Cross-platform: the core is Python (identical on both); only the per-OS hook shims differ, kept minimal.

## YAGNI / explicitly excluded
- Quota-safety signaling (deselected).
- Real-time mid-session detection of the other lane's push (would need polling; the SessionStart check + `/resume` covers the one-machine-at-a-time reality; a `/loop /resume` is available if ever wanted).
- Auto-merge of overlapping edits (the file-disjoint convention + baton-owns-truth-records rule remove the need).

## Relation to existing protocol
The pod lane (RunPod) keeps the single-committer rule from `plans/2026-06-02-samkings-cloud-agent-workflow-and-run-plan.md` (the pod never pushes). This baton system governs only the two interactive workstations (Windows + Mac), which both push. Memory cross-refs: `reference_mac_dev_env`, `reference_ssh_git_remotes`, `reference_save`, `feedback_no_external_hooks`.
