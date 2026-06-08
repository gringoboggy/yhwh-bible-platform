---
description: Hand off to the other lane (transfer truth-record ownership + set assignments; commit + milestone-push)
argument-hint: <to-mac|to-windows> [free-text note]
---
You are handing off to the other Claude lane (lane-coordination v2). Arguments: `$ARGUMENTS`
(first token = `to-mac` or `to-windows`; the rest = an optional free-text note). A handoff
**transfers truth-record ownership** (who edits SESSION_STATE/IN_FLIGHT/CHANGELOG + does
merges) and sets each lane's task. It does NOT mean "stop all work" — in `parallel` mode both
lanes keep working their file-disjoint assignments. A cross-machine handoff IS a milestone ⇒ push.
Spec: `docs/superpowers/specs/2026-06-08-lane-coordination-v2-design.md`. (Python: Mac =
`.venv/bin/python`, Windows = `py -3`.)

Do these in order, stopping if any fails:

1. Reconcile the truth-record for what this turn accomplished — update `dev/SESSION_STATE.md` (+ `dev/IN_FLIGHT.md`, and `dev/CHANGELOG.md` if a coherent unit shipped) to observed reality. You own these if you are the current `truth_owner`.
2. Decide the target (`to-mac`→`mac`, `to-windows`→`windows`) and each lane's next assignment + the mode (`parallel` default; `exclusive` only if both lanes would touch the SAME files).
3. Run: `<py> scripts/lane_handoff.py handoff --to <target> --mode <parallel|exclusive> --mac "<mac task or idle>" --windows "<windows task or idle>" --done "<done bullets>" --next "<next bullets>" --watch "<watch>"`. If it prints `REFUSED`, you are not the current `truth_owner` — STOP and tell the user (do not `--force` without explicit say-so). It preserves the existing board history (prepends a turn block).
4. (Optional hygiene) if `dev/LANE_HANDOFF.md` has grown long, `<py> scripts/lane_handoff.py prune --keep 5` (archives old turns to `dev/archive/LANE_HANDOFF_LOG.md`; the STANDING block is always kept).
5. Stage + commit: `git add dev/LANE_HANDOFF.md dev/SESSION_STATE.md dev/IN_FLIGHT.md dev/CHANGELOG.md` (+ work files), message `lane-handoff: <lane> -> <target> (turn N) — <one-line>`.
6. Milestone-push BOTH remotes with the radar gating the push: `<py> scripts/lane_ping.py --before-push` → if it says BEHIND, `git pull --rebase origin main` first (the other lane pushed; rebase is conflict-free for file-disjoint lanes). Then `git push origin main && git push github main`. (Mac may instead run `bash dev/save_mac.sh -m "<msg>"`, which does the ping/rebase/commit/push/verify.)
7. Report: "Handed to <target> (turn N, mode=<mode>). mac=<task> · windows=<task>. They'll see it at session start or `/resume`." In `exclusive` mode, do NOT keep editing the shared files the other lane now owns; in `parallel` mode, continue your own assignment.
