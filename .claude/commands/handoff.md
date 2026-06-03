---
description: Hand the baton to the other lane (write the handoff note, commit, push both remotes)
argument-hint: <to-mac|to-windows> [free-text note]
---
You are handing off the work baton to the other Claude lane. Arguments: `$ARGUMENTS`
(first token = `to-mac` or `to-windows`; the rest = an optional free-text note).

Do these steps in order, stopping if any fails:

1. Reconcile the truth-record for what THIS turn accomplished: update `dev/SESSION_STATE.md` + `dev/IN_FLIGHT.md` (and `dev/CHANGELOG.md` if a coherent unit shipped) to observed reality. You own these files this turn (baton rule).
2. Decide the target lane from the first argument (`to-mac` -> `mac`, `to-windows` -> `windows`). Summarize what you finished (`--done`), what the receiver should pick up (`--next`), and any `--watch` gotchas, drawing on the note and the session.
3. Run: `py -3 scripts/lane_handoff.py handoff --to <target> --done "<done bullets>" --next "<next bullets>" --watch "<watch>"` (on Mac use `python3`). If it prints `REFUSED`, STOP and tell the user this lane does not hold the baton (do not `--force` without explicit user say-so).
4. Stage + commit: `git add dev/LANE_HANDOFF.md dev/SESSION_STATE.md dev/IN_FLIGHT.md dev/CHANGELOG.md` (+ any work files), commit with a message `lane-handoff: <lane> -> <target> (turn N) — <one-line>`.
5. Sync + push BOTH remotes: `git fetch origin && git fetch github && git rebase origin/main && git push origin main && git push github main`. Resolve any rebase conflict before pushing.
6. Report: "Baton handed to <target> (turn N). They'll see it at their next session start or on `/resume`." Do NOT keep working on baton-owned files after this — the other lane is now the holder.
