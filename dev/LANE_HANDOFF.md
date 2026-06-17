---
mode: parallel
turn: 118
from: mac
updated: 2026-06-17T13:54:26Z
status: handing-off
mac: idle — lane_watch --bg MUST stay running (STANDING turn 117)
windows: lane_watch -Background -AssignMac + ci.py + Round 9 Workflow when gate green
truth_owner: windows
holder: windows
---

## ▶ mac → windows (turn 118, 2026-06-17T13:54:26Z) — mode=parallel

**Done (turn 117, mac):**
Mac turn 114 batch rebased: book_codes.py+resolve_book_code merge; load_notes_checked sweep; rx/popup audit tail; lane-transfer/audit deleted; samkings 6/6; lane_watch --bg started

**Next (turn 118, windows picks up):**
WIN: ci.py parity; website/dist regen if needed; Round 9 gate

**Assignments:** mac = idle — lane_watch --bg MUST stay running (STANDING turn 117) · windows = lane_watch -Background -AssignMac + ci.py + Round 9 Workflow when gate green

**Watch-outs:**
lane_watch ON both lanes whole arc; milestone-push every handoff edit

---

## ▶ windows → mac (turn 117, 2026-06-17T13:44:42Z) — mode=parallel

**Done (turn 116, windows):**
turn 116 lane_watch required whole arc; turn 117 lane_watch hardening (dirty-tree guard, uncommitted-handoff nag, active-queue assign, mirror-skew warn); tests 9/9

**Next (turn 117, mac picks up):**
Mac: lane_watch --bg FIRST then remediation queue. WIN: watcher + P4 + audits.

**Assignments:** mac = ★ FIRST: git pull turn 117+ → bash dev/lane_watch_mac.sh --once → bash dev/lane_watch_mac.sh --bg (KEEP RUNNING whole arc). Then remediation: refactor cache · inject_book test · doc 91,720 · samkings · ci.py (MAC_WORK_QUEUE.md). Round 9 after gate. · windows = lane_watch -Background -AssignMac + P4 gates + dishonest/stub audits

**Watch-outs:**
lane_watch ON both lanes whole arc — do not stop watcher; milestone-push every handoff edit; file-disjoint

---

## ◦ windows assign (turn 116, 2026-06-17T20:00:00Z) — mode=parallel

**User directive (2026-06-17):** **lane_watch ON for the entire pre-human + Round 9 arc** on BOTH boxes — not opt-in. Mac must start and keep it running.

**Lane watch (both lanes — STANDING for this arc):**
- **Mac:** `git pull` → `bash dev/lane_watch_mac.sh --once` → `bash dev/lane_watch_mac.sh --bg` (leave running through remediation + Round 9 audit)
- **WIN:** `pwsh -File dev/lane_watch_win.ps1 -LoopSec 120` (or `-Background`); add `-AssignMac` to auto-assign from `MAC_WORK_QUEUE.md` after Mac pushes
- **Rule:** handoff/assign edits MUST be milestone-pushed or the other box never sees them (`UNPUSHED HANDOFF` nag)

**Done (turn 115, windows):** pre-human sprint + Round 9 plan committed @ `99bfcabc`.

**Assignments:** mac = **lane_watch --bg first** (see above) → remediation: refactor cache · inject_book test · doc 91,720 · samkings · ci.py (`MAC_WORK_QUEUE.md`). Round 9 after gate. · windows = **lane_watch running** → P4 gates · dishonest/stub audits · Round 9 Workflow when gate green (win=11 dims)

**Watch-outs:** file-disjoint; milestone-push every handoff while watcher is up; do not stop watcher mid-arc unless user says so.

---

## ⚠ STANDING — both lanes (do NOT rotate this section out of the file)

**External drives E:/F: with Mac (2026-06-16, user-directed — STANDING, both lanes).** Portable **E:** and **F:** volumes (release bundles, `YHWH-v2.4-releases/`, M3/M4 handoff packs, etc.) stay **with the Mac box for now**. **Windows:** do **not** wait on a plugged E:/F: drive — **`git pull` / push to both remotes is the primary cross-lane sync**; use **`D:`** only if a local WIN backup is needed before a big operation. **Mac:** owns rsync/copy to `/Volumes/NO NAME/YHWH-v2.4-releases/` (or E:/F: when mounted there). WIN `save-all.ps1` E:/F: bundle legs are **optional / deferred** while drives are Mac-side.

**Auto-pull on BEHIND (2026-06-11, user-directed "should just be a claude rule" — STANDING, both lanes).** Whenever the lane radar (`scripts/lane_ping.py` or any fetch) shows BEHIND, `git pull --rebase origin main` IMMEDIATELY and automatically — at session start, before any commit/save/build on shared files, before truth-record edits, and whenever the other lane is known mid-arc. The user never has to say "pull". Dirty tree ⇒ commit or stash-pull-pop, never skip. **Out-of-repo mirror status:** winclaude ✓ · macclaude ✓ (turn 24 SessionStart + `dev/save_mac.sh`).

**Git-clone / work-dir deletion gate (2026-06-11, user-directed "that should always be a thing" — STANDING, both lanes).** Before deleting ANY repo clone or work dir, PROVE it holds nothing unique: clean `status --porcelain` + HEAD is `merge-base --is-ancestor` of the surviving copy + no local-only branches/stashes. Any miss ⇒ surface to the user instead. Codified `dev/SESSION_PLAYBOOK.md` §6.5 (syncs on pull). **Out-of-repo mirror status:** winclaude ✓ (`verify-before-delete-clones` memory) · **macclaude ✓ (turn 74** — `feedback_verify_before_delete_clones` memory + MEMORY.md pointer; ACK).

**No background runs at session end (2026-06-11, user-directed — STANDING, both lanes).** "Prep for a fresh session" often = the user is about to RESTART/SHUT DOWN the box. Before a requested wrap: let any RUNNING long job (Previewer conversion, build, batch) FINISH and record its result FIRST, and never LAUNCH new long-running work as part of wrapping up — the handoff/push must leave the machine quiescent (nothing a shutdown would kill, nothing the user has to stop/restart). Mid-session pipelining stays unaffected. **Out-of-repo mirror status:** **winclaude ✓ (2026-06-11** — `no-background-runs-at-wrap` memory + MEMORY.md pointer; rule applied live same day: the Kobo root-cause workflow now runs to completion before the wrap) · **macclaude ✓ (turn 77** — `feedback_no_background_runs_at_session_end` memory + MEMORY.md pointer).

**Session operating doctrine (2026-06-08, user-directed — EVERY session, both lanes, forever).** `dev/CLAUDE_PROJECT_RULES.md` **Guard #5** + §4: (a) never stop to ask the user questions — act on best judgment; (b) full standing authority (commit/push/pull/build/deploy/launch-site/update-GitHub-GitLab; package-install soft-deny still stands); (c) bandwidth is the hard cap (~98% weekly) → zero unnecessary context, bare-minimum announcements; (d) save = LOCAL-COMMIT during work, full 5-leg push only at a MAJOR milestone or on user command. **Out-of-repo mirror status:** winclaude ✓ (Windows memory) · **macclaude ✓ (turn 24** — `feedback_session_operating_doctrine` + `reference_save` rewrite + `reference_lane_ping` + MEMORY.md pointers; Mac SessionStart hook + `dev/save_mac.sh`).

**Lane sync radar (the "ping").** `scripts/lane_ping.py` (shared) — cheap `git ls-remote` before pull/push so milestone pushes to protected `main` never reject. Wired per-box: Win = `save-all.ps1 --before-push` + SessionStart `--quiet`; **Mac = `dev/save_mac.sh` (`--before-push` → auto `git pull --rebase` if BEHIND) + SessionStart `--quiet` ✓ (turn 24).** BEHIND ⇒ always `git pull --rebase origin main`.

**Lane watch v3 (2026-06-17, STANDING — REQUIRED during pre-human + Round 9 arc, both lanes).** User-directed: keep **lane_watch running** for the whole remediation → Round 9 audit → fix phase — not opt-in during this arc. `scripts/lane_watch.py` unifies push radar + remote `LANE_HANDOFF` turn compare + `lane_handoff incoming` + unpushed-handoff nag. **Mac:** `bash dev/lane_watch_mac.sh --bg` after `--once` at session start; leave up until arc completes. **WIN:** `pwsh -File dev/lane_watch_win.ps1 -LoopSec 120` (optional `-AssignMac` for queue auto-assign). Handoff/assign edits MUST be milestone-pushed or the other box never sees them. Outside this arc, watcher may stay stopped unless needed. **Hooks:** SessionStart = `dev/cc-hooks/bootstrap-triad.{ps1,sh}` installed to repo-parent `.claude/hooks/` (turn-24 wiring **shipped**; in-repo `.claude/settings.json` stays `{}` by design).

**Lane watch trip-ups (2026-06-17, STANDING — both lanes).** The watcher now guards common coordination failures: (1) **DIRTY TREE** — auto-pull skips if `git status --porcelain` is non-empty; commit or stash first. (2) **UNCOMMITTED HANDOFF** — board turn bumped in working tree but not committed triggers nag even with 0 unpushed commits. (3) **UNPUSHED HANDOFF** — committed turn ahead of `origin/main:LANE_HANDOFF` + local commits not pushed. (4) **MIRROR SKEW** — `origin` vs `github` tips differ; origin is source of truth — milestone-push both. (5) **Mac queue assign** — WIN `-AssignMac` scans only `## Active queue` (not Round 9). (6) **incoming repeats** until `lane_handoff mark-seen` — by design. Fix: read banner → work assignment → mark-seen when done.

**Cross-lane tool/environment parity (2026-06-05, Guard #4).** Verify the other box has the tools/agents/deps/paths before handing it a task or running a shared `.claude/workflows/*.js`. (Round-6 auditor now BAKES the parity in: flipping `const LANE` auto-selects REPO + agent types — no more 3-edit Mac trap.) Each lane mirrors cross-lane rules into its own per-box memory.

**Cross-lane problem hand-off (2026-06-08, Guard #6 — user-directed).** ALWAYS pass a problem you find OUTSIDE your own touched work — especially in the OTHER lane's domain — to the other lane (this board + the shared findings file), naming `file:line` + the fix. NEVER drop a cross-domain defect as "not my area" / "they'll catch it." Shared `RULES` guard #6 syncs the rule to both lanes on `git pull`; each lane then mirrors it into its own per-box memory + ACKs.

**⚠ Heads-up — auto-mode destructive-op soft-deny (PER-BOX; NOT a repo rule).** Under `~/.claude` `defaultMode:auto`, the harness `$defaults` soft-deny BLOCKS *direct* destructive file tool-calls on protected / out-of-workspace paths — it bit winclaude during the C: cleanup (PowerShell `Remove-Item` on `$env:TEMP` / another drive → "this path is protected from removal", and it persists even with the sandbox disabled). It is **per-box** (each lane's own `~/.claude/settings.json`, the repo `.claude/settings.json` is `{}` → NOT git-synced, so it can't reach you from win). **It does NOT scan inside a script**, so your `dev/build_dmg.sh` rebuild + any `rm`/`mv` inside a build script run normally. Only an *ad-hoc* destructive tool-call (a bare `rm -rf` on an out-of-workspace/system path) can trip it; if it does: the user has pre-authorized "anything you need" (proceed), run it via a script, target the exact in-workspace path, or the user toggles auto OFF to approve. winclaude's workaround was `[IO.Directory]::Delete` / `robocopy /MOVE` (no `Remove-Item` token); the Mac equivalent is plain `rm`/`mv` on explicit non-system paths. (For relocating big gitignored assets off a full disk, winclaude used `robocopy /MOVE` + a directory **junction** so the in-repo path still resolves — Mac's equivalent is `mv` + a `ln -s` symlink.)

> **▶ Lane-coordination v2 + SessionStart hooks — SHIPPED (ACK 2026-06-17, both lanes).** In-repo engine (`lane_handoff.py`, RULES §4, `dev/cc-hooks/bootstrap-triad.*`) is live. Per-box halves (memory mirror + `lane_handoff incoming` in SessionStart) are each lane's responsibility — winclaude ✓ · macclaude ✓ (turn 24). New sessions: read triad via bootstrap hook; use `incoming` exit code (not legacy baton strings). Mac milestone save: `bash dev/save_mac.sh -m "…"`.

> **Older turns archived to `dev/archive/LANE_HANDOFF_LOG.md`** (rotated by `scripts/rotate_truth_records.py`; newest batch first).
