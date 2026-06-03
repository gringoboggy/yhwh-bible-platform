---
description: Mid-turn durability — push the holder's work without handing off the baton
---
You are syncing this lane's work to the remotes WITHOUT handing off (you keep the baton).

1. Confirm you hold the baton: `py -3 scripts/lane_handoff.py status` (on Mac use `python3`). If it prints `baton is with <other>`, STOP — only the holder pushes.
2. Stage + commit any pending work (use a precise message). If the tree is clean, skip.
3. `git fetch origin && git fetch github && git rebase origin/main && git push origin main && git push github main`. Resolve conflicts before pushing.
4. Report what was pushed. The baton stays with this lane.
