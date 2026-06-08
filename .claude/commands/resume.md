---
description: Pick up your assignment from the other lane (fetch, rebase-if-behind, read your section, start)
---
You are picking up work from the lane-coordination board (v2). The board assigns each lane a
task in `parallel` mode (the default — both lanes work file-disjoint and both push at
milestones) or names one `holder` in `exclusive` mode (the old single-worker mutex, used only
when both lanes would touch the SAME files). Spec:
`docs/superpowers/specs/2026-06-08-lane-coordination-v2-design.md`. (Python: Mac =
`.venv/bin/python`, Windows = `py -3`.)

1. Fetch: `git fetch origin && git fetch github`.
2. Sync — run the radar: `<py> scripts/lane_ping.py`. If BEHIND, `git pull --rebase origin main` (replays your unpushed local commits; conflict-free for file-disjoint lanes; resolve any conflict by COMBINING). If already current, `git rebase origin/main` is a no-op.
3. Read the board: `<py> scripts/lane_handoff.py status`. It prints `mode`, both lanes' tasks, the `truth_owner`, and a `YOU (<lane>): <task>` line.
4. Branch on mode:
   - **parallel** (default): pick up YOUR task from the `YOU (...)` line — do NOT stop just because the other lane is `truth_owner`. Read the matching `## ▶ ... → <you>` section of `dev/LANE_HANDOFF.md` for detail. If your task is `idle`, take the top backlog item (roadmap LANE T / SESSION_STATE "Next"). `/sync` before touching anything; if your assignment would touch the same files the other lane is working, coordinate first.
   - **exclusive**: if the other lane is `holder`, you are NOT to touch shared files — do disjoint side-work or wait, and tell the user. Only when YOU are the holder do you work the shared files.
5. `<py> scripts/lane_handoff.py mark-seen` so the SessionStart banner won't re-fire for this turn.
6. Confirm in one line: "Picked up (turn N, mode=<mode>): <your task>." Then begin.
