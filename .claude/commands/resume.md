---
description: Pick up an incoming baton from the other lane (fetch, combine, read the note)
---
You are checking for and picking up a handoff from the other Claude lane.

1. Fetch both remotes: `git fetch origin && git fetch github`.
2. Check the baton: `py -3 scripts/lane_handoff.py status` (on Mac use `python3`).
3. If it prints `baton is with <other>` (NOT this lane): tell the user the baton is still with the other lane and STOP. (Offer that, if they are certain the other lane is idle, you can `--force`-take it — but only on explicit confirmation.)
4. If it prints `YOU HOLD THE BATON`: integrate the incoming work — `git rebase origin/main` (the lanes are file-disjoint + only the holder pushes, so this is a clean fast-forward; resolve any conflict by combining). Then print the `## Done` / `## Next` / `## Watch-outs` sections of `dev/LANE_HANDOFF.md` to the user, and run `py -3 scripts/lane_handoff.py mark-seen` so the session-start banner won't re-fire for this turn.
5. Confirm: "You now hold the baton (turn N). Picking up: <next summary>." Then begin that work.
