---
description: Milestone push — push THIS lane's work to both remotes (radar-gated), without handing off
---
You are pushing this lane's committed work to the remotes at a milestone, WITHOUT transferring
ownership (lane-coordination v2). Under the bandwidth-first cadence (RULES §4) you commit
locally during work and run this at a major milestone of your half — or whenever the user says
save/commit/push/sync. Either lane may push its own file-disjoint work; the radar keeps the
protected-`main` push a clean fast-forward. (Python: Mac = `.venv/bin/python`, Windows = `py -3`.)

1. Stage + commit any pending work with a precise message (`ruff format` generated stores first so the pre-commit hook passes). If the tree is clean, skip.
2. Run the radar: `<py> scripts/lane_ping.py --before-push`. If it says BEHIND, `git pull --rebase origin main` first (the other lane pushed; rebase replays your local commits, conflict-free for file-disjoint lanes — resolve any conflict by combining).
3. Push both remotes: `git push origin main && git push github main`. (Windows: `save-all.ps1` does steps 1–3 + the E:/F: bundle legs. Mac: `bash dev/save_mac.sh -m "<msg>"` does steps 1–3 + verify.)
4. Verify: `git status -b` shows ahead/behind 0 on both. Report what was pushed. Ownership/assignments are unchanged — use `/handoff` to transfer them, or `<py> scripts/lane_handoff.py assign ...` to update the board in place.
