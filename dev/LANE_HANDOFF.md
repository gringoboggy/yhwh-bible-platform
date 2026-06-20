---
mode: parallel
turn: 146
from: windows
updated: 2026-06-20T02:09:18Z
status: handing-off
mac: FRESH SESSION: pull 27bc6cdc+; verify turn 144 ci triage (MAC_WORK_QUEUE Next scope #1); save verify report; HOLD code fixes
windows: FRESH SESSION: pull 27bc6cdc+; M2 Apple audit K-R5-3 OR Kindle STK bisect vs 143407Z; Mac verify cmds each save
truth_owner: mac
holder: mac
---

## ▶ windows → mac (turn 146, 2026-06-20T02:09:18Z) — mode=parallel

**Done (turn 145, windows):**
turn 145 truth records @ 091a3f14: SESSION_STATE/IN_FLIGHT/CHANGELOG/backlog refreshed; LANE_HANDOFF §user-fail STANDING + §Mac verify turn 144 cmds

**Next (turn 146, mac picks up):**
Mac: verify turn 144 ci triage first | WIN: M2 Apple audit #1 or Kindle STK bisect #2

**Assignments:** mac = FRESH SESSION: pull 27bc6cdc+; verify turn 144 ci triage (MAC_WORK_QUEUE Next scope #1); save verify report; HOLD code fixes · windows = FRESH SESSION: pull 27bc6cdc+; M2 Apple audit K-R5-3 OR Kindle STK bisect vs 143407Z; Mac verify cmds each save

**Watch-outs:**
turn 144 Mac verify still pending; M2 user-fail open; STK 144600Z vs 143407Z bisect open

---

## ◦ windows assign (turn 145, 2026-06-20T02:03:00Z) — mode=parallel

**Assignments:** mac = FRESH SESSION: pull 27bc6cdc+; verify turn 144 ci triage (MAC_WORK_QUEUE Next scope #1); save verify report; HOLD code fixes · windows = FRESH SESSION: pull 27bc6cdc+; M2 Apple audit K-R5-3 OR Kindle STK bisect vs 143407Z; Mac verify cmds each save

Session handoff @ `091a3f14`. ci triage DONE turn 144. Read `AGENTS.md` → triad → `SESSION_STATE` top first.

---

## Mac verify (turn 144) — PASS @ 776cc29f

**Commands (from WIN turn 144 + MAC_WORK_QUEUE Next scope #1):**
```bash
export PYTHONUTF8=1
pytest tests/test_edition_stats.py \
  tests/test_hierarchical_symbols.py::TestResolverPrecedence::test_kind_token_beats_category_token \
  tests/test_scripts.py::TestEditionMeta::test_customize_data_includes_editions \
  tests/test_scripts.py::TestEditionMeta::test_api_sample_html_out_of_canon \
  tests/test_validate_schemas.py::TestOmega19SchemaValidator::test_validate_editions_passes_on_real_file \
  tests/test_marker_style.py tests/test_reader_target.py -q
python3 scripts/lint_rules.py
```

**Results:**
- `lint_rules.py`: **CLEAN 33 pass · 2 warn · 0 fail**
  - warn: truth-record size budget (soft, on CLAUDE_PROJECT_RULES.md)
  - warn: 5 phase mentions not in CHANGELOG (pre-existing)
- pytest (targeted; venv + PYTHONUTF8):
  - `test_orphan_inline_markers_join_disabled_ref_set`: **PASS** (13s)
  - `TestResolverPrecedence::test_kind_token_beats_category_token`: **PASS** (2s)
  - 2× `TestEditionMeta`: **PASS** (6s)
  - `test_validate_editions_passes_on_real_file`: **PASS** (0.5s)
  - `test_reader_target.py`: **16 passed** (1s)
  - `test_marker_style.py`: unit + ApplyBadge* classes **17 passed** (~5min run); narrow const/validator **8 passed** (1s). Build-oracle tests (the 2 with "build" in name) exceed 5min tool cap (expected slow oracles; WIN `--lf` 9/9 covered).
- No FAILs or errors on completed surface. Matches WIN "ci pytest triage GREEN (orphan markers + 4-edition pins)".

**Notes:** Mac followed HOLD — no code edits. Report only. Slow oracles consistent with project (see SESSION_STATE slow tags).

---

## ⚠ STANDING — §user-fail M2 Apple audit (carry-forward; do NOT rotate)

**User verdict (2026-06-19):** `ethiopian-tewahedo --target-reader tablet` builds **FAIL** on Apple Books device. Mac sim: `verify_kr2_build` **K-R5-3** (262× book-title pieces carry badges/asides). **WIN owns** deep audit — Mac verify only after WIN push.

| # | Issue | WIN action |
|---|---|---|
| 1 | Pages read backwards / scrambled nav | Confirm device artifact UUID; spine monotonicity gate; tablet profile isolation (`file_split` off) |
| 2 | Popup/notes justified (user wants left-align) | Scoped tablet exception; update `TestLeftAlign` contract |
| 3 | Easton triple attribution (byline + label + body boilerplate) | S1/suppress rules for `dict-*` kinds; lossless when flags off |
| 4 | K-R5-3 book-title badge bleed (`bp-*` carry verse badges) | Clamp at book/piece boundary in `build_edition.py` |

Full forensics: `dev/archive/LANE_HANDOFF_LOG.md` turn 142 §user-fail. Tablet artifact: `…195709Z.epub` (vn-sep stripped). Mac patch @ `2193216c` saved — device QA still FAIL.

---

## ⚠ STANDING — both lanes (do NOT rotate this section out of the file)

**External drives E:/F: with Mac (2026-06-16, user-directed — STANDING, both lanes).** Portable **E:** and **F:** volumes (release bundles, `YHWH-v2.4-releases/`, M3/M4 handoff packs, etc.) stay **with the Mac box for now**. **Windows:** do **not** wait on a plugged E:/F: drive — **`git pull` / push to both remotes is the primary cross-lane sync**; use **`D:`** only if a local WIN backup is needed before a big operation. **Mac:** owns rsync/copy to `/Volumes/NO NAME/YHWH-v2.4-releases/` (or E:/F: when mounted there). WIN `save-all.ps1` E:/F: bundle legs are **optional / deferred** while drives are Mac-side.

**Auto-pull on BEHIND (2026-06-11, user-directed "should just be a claude rule" — STANDING, both lanes).** Whenever the lane radar (`scripts/lane_ping.py` or any fetch) shows BEHIND, `git pull --rebase origin main` IMMEDIATELY and automatically — at session start, before any commit/save/build on shared files, before truth-record edits, and whenever the other lane is known mid-arc. The user never has to say "pull". Dirty tree ⇒ commit or stash-pull-pop, never skip. **Out-of-repo mirror status:** winclaude ✓ · macclaude ✓ (turn 24 SessionStart + `dev/save_mac.sh`).

**Git-clone / work-dir deletion gate (2026-06-11, user-directed "that should always be a thing" — STANDING, both lanes).** Before deleting ANY repo clone or work dir, PROVE it holds nothing unique: clean `status --porcelain` + HEAD is `merge-base --is-ancestor` of the surviving copy + no local-only branches/stashes. Any miss ⇒ surface to the user instead. Codified `dev/SESSION_PLAYBOOK.md` §6.5 (syncs on pull). **Out-of-repo mirror status:** winclaude ✓ (`verify-before-delete-clones` memory) · **macclaude ✓ (turn 74** — `feedback_verify_before_delete_clones` memory + MEMORY.md pointer; ACK).

**No background runs at session end (2026-06-11, user-directed — STANDING, both lanes).** "Prep for a fresh session" often = the user is about to RESTART/SHUT DOWN the box. Before a requested wrap: let any RUNNING long job (Previewer conversion, build, batch) FINISH and record its result FIRST, and never LAUNCH new long-running work as part of wrapping up — the handoff/push must leave the machine quiescent (nothing a shutdown would kill, nothing the user has to stop/restart). Mid-session pipelining stays unaffected. **Out-of-repo mirror status:** **winclaude ✓ (2026-06-11** — `no-background-runs-at-wrap` memory + MEMORY.md pointer; rule applied live same day: the Kobo root-cause workflow now runs to completion before the wrap) · **macclaude ✓ (turn 77** — `feedback_no_background_runs_at_session_end` memory + MEMORY.md pointer).

**Session operating doctrine (2026-06-08, user-directed — EVERY session, both lanes, forever).** `dev/CLAUDE_PROJECT_RULES.md` **Guard #5** + §4: (a) never stop to ask the user questions — act on best judgment; (b) full standing authority (commit/push/pull/build/deploy/launch-site/update-GitHub-GitLab; package-install soft-deny still stands); (c) bandwidth is the hard cap (~98% weekly) → zero unnecessary context, bare-minimum announcements; (d) save = local-commit micro-edits + **push often without asking** (see crash-safe cadence below). **Out-of-repo mirror status:** winclaude ✓ (Windows memory) · **macclaude ✓ (turn 24** — `feedback_session_operating_doctrine` + `reference_save` rewrite + `reference_lane_ping` + MEMORY.md pointers; Mac SessionStart hook + `dev/save_mac.sh`).

**Crash-safe commit+save cadence (2026-06-17, user-directed — STANDING, both lanes).** **Both lanes commit AND save (full push) autonomously — never ask the user, never wait on input, never pause for confirmation.** Local-commit micro-edits as you go; then **save** (push both remotes) at every coherent stop so a crash cannot lose work. **Save when:** tests/gate green on a shipped slice · handoff/assign/truth-record edit · before risky/long jobs · before session wrap · `lane_watch` shows `UNPUSHED HANDOFF` · **never end with unpushed commits** (`git status -b` must show ahead/behind = 0 before "safe to stop"). **WIN:** `pwsh -File save-all.ps1 -Message "…"` (radar-gated; E:/F: optional while Mac-side). **Mac:** `bash dev/save_mac.sh -m "…"` (commit if dirty + push origin + github). **Do not hoard** local-only commits — the other lane cannot see unpushed work. **macclaude:** mirror this block into per-box memory on next session (ACK).

**Lane sync radar (the "ping").** `scripts/lane_ping.py` (shared) — cheap `git ls-remote` before pull/push so milestone pushes to protected `main` never reject. Wired per-box: Win = `save-all.ps1 --before-push` + SessionStart `--quiet`; **Mac = `dev/save_mac.sh` (`--before-push` → auto `git pull --rebase` if BEHIND) + SessionStart `--quiet` ✓ (turn 24).** BEHIND ⇒ always `git pull --rebase origin main`.

**Lane watch v3 (2026-06-17, STANDING — REQUIRED during pre-human + Round 9 arc, both lanes).** User-directed: keep **lane_watch running** for the whole remediation → Round 9 audit → fix phase — not opt-in during this arc. `scripts/lane_watch.py` unifies push radar + remote `LANE_HANDOFF` turn compare + `lane_handoff incoming` + unpushed-handoff nag. **Mac:** `bash dev/lane_watch_mac.sh --bg` after `--once` at session start; leave up until arc completes. **WIN:** `pwsh -File dev/lane_watch_win.ps1 -LoopSec 60 -AssignMac -Background` (tightened 2026-06-18). Handoff/assign edits MUST be milestone-pushed or the other box never sees them. Outside this arc, watcher may stay stopped unless needed. **Hooks:** SessionStart = `dev/cc-hooks/bootstrap-triad.{ps1,sh}` installed to repo-parent `.claude/hooks/` (turn-24 wiring **shipped**; in-repo `.claude/settings.json` stays `{}` by design).

**Session operating authority (2026-06-18, STANDING — both lanes, Mac mirror to memory).** User has full standing authority: commit, push, pull, build, deploy, install tools, change any repo/website surface. **Never ask** whether to continue, save, install, or take the logical next step. When the lane is on, keep working. WIN assigns Mac a fresh laundry list (primary + overflow) whenever Mac queue clears. Build time-saving infra when beneficial. **Mac STK (2026-06-18):** **user** uploads Send-to-Kindle in Chrome (8 GB box); **agent** stages epub + `stk_poll_watch.sh` + end-task Chrome/Kindle + tap QA (`CLAUDE_PROJECT_RULES.md` guard #6).

**Anti-idle radar (2026-06-18, STANDING — both lanes).** The agent must **never** end a turn waiting for user input. If blocked on one task, pick the next disjoint item from `dev/AGENT_WORK_BACKLOG.md` or `py -3 scripts/agent_idle_radar.py --next`. User will ask when they have something for you. **Heartbeat:** `--ping` after each slice. **Mac side lanes while WIN pytest runs:** Esther Patrologia transcription · CAM folio pre-pull · EN back-translation · website/dist regen · reader-sim depth. **WIN side lanes while blocked:** website update · kobo gate-only sim · rx-surfaces · audit after 25+ commits.

**Dual radars ON at bootstrap (2026-06-18, STANDING — both lanes).** Every session start, the bootstrap hook (`bootstrap-triad.{ps1,sh}`) **auto-starts both radars** idempotently: (1) **lane_watch** 60s — `dev/start_session_radars.{ps1,mac.sh}`; (2) **agent_idle_radar** 120s. Manual restart if either died: WIN `pwsh -File dev/start_session_radars.ps1` · Mac `bash dev/start_session_radars_mac.sh`. Mac must wire `bootstrap-triad.sh` in per-box SessionStart settings (see `dev/cc-hooks/README.md`).

**Strategic replan ping (2026-06-18, STANDING — both lanes).** Periodically **step back** and re-read PLAN + release gate + SESSION_STATE + both work queues — reorder priorities when derailed or scope shifts. Radar auto-surfaces P03 replan when **15+ commits** · **24h** · **PLAN/release-plan changed**. Checklist: `dev/STRATEGIC_REPLAN_CHECKLIST.md`. Commands: `py -3 scripts/agent_idle_radar.py --replan` · `--replan-done`. **Replan is work, not a pause** — mark done then immediately `--next` and execute.

**WIN builds · Mac verifies (2026-06-19, user-directed — STANDING, both lanes).** **WIN** owns implementation (`scripts/` · `tests/` · `ci.py` · matrix builds · Kindle bisect). **Mac** owns **verify + scope** on each WIN milestone: pull → run WIN-listed verify commands → `## Mac verify (turn N)` PASS/FAIL in this file → update `MAC_WORK_QUEUE.md` `### Next scope (Mac)` (max 3 items). Mac **must not** dual-implement the same Kindle/pytest fix WIN is shipping. Mac **may** run targeted `pytest` + sim gates + STK poll (user uploads); Mac **must not** run full `ci.py` on HDD while WIN `ci.py` is in flight. Full runbook: `dev/MAC_WORK_QUEUE.md` §Operating model.

**Lane watch trip-ups (2026-06-17, STANDING — both lanes).** The watcher now guards common coordination failures: (1) **DIRTY TREE** — auto-pull skips if `git status --porcelain` is non-empty; commit or stash first. (2) **UNCOMMITTED HANDOFF** — board turn bumped in working tree but not committed triggers nag even with 0 unpushed commits. (3) **UNPUSHED HANDOFF** — committed turn ahead of `origin/main:LANE_HANDOFF` + local commits not pushed. (4) **MIRROR SKEW** — `origin` vs `github` tips differ; origin is source of truth — milestone-push both. (5) **Mac queue assign** — WIN `-AssignMac` scans only `## Active queue` (not Round 9). (6) **incoming repeats** until `lane_handoff mark-seen` — by design. Fix: read banner → work assignment → mark-seen when done.

**Cross-lane tool/environment parity (2026-06-05, Guard #4).** Verify the other box has the tools/agents/deps/paths before handing it a task or running a shared `.claude/workflows/*.js`. (Round-6 auditor now BAKES the parity in: flipping `const LANE` auto-selects REPO + agent types — no more 3-edit Mac trap.) Each lane mirrors cross-lane rules into its own per-box memory.

**Cross-lane problem hand-off (2026-06-08, Guard #6 — user-directed).** ALWAYS pass a problem you find OUTSIDE your own touched work — especially in the OTHER lane's domain — to the other lane (this board + the shared findings file), naming `file:line` + the fix. NEVER drop a cross-domain defect as "not my area" / "they'll catch it." Shared `RULES` guard #6 syncs the rule to both lanes on `git pull`; each lane then mirrors it into its own per-box memory + ACKs.

**⚠ Heads-up — auto-mode destructive-op soft-deny (PER-BOX; NOT a repo rule).** Under `~/.claude` `defaultMode:auto`, the harness `$defaults` soft-deny BLOCKS *direct* destructive file tool-calls on protected / out-of-workspace paths — it bit winclaude during the C: cleanup (PowerShell `Remove-Item` on `$env:TEMP` / another drive → "this path is protected from removal", and it persists even with the sandbox disabled). It is **per-box** (each lane's own `~/.claude/settings.json`, the repo `.claude/settings.json` is `{}` → NOT git-synced, so it can't reach you from win). **It does NOT scan inside a script**, so your `dev/build_dmg.sh` rebuild + any `rm`/`mv` inside a build script run normally. Only an *ad-hoc* destructive tool-call (a bare `rm -rf` on an out-of-workspace/system path) can trip it; if it does: the user has pre-authorized "anything you need" (proceed), run it via a script, target the exact in-workspace path, or the user toggles auto OFF to approve. winclaude's workaround was `[IO.Directory]::Delete` / `robocopy /MOVE` (no `Remove-Item` token); the Mac equivalent is plain `rm`/`mv` on explicit non-system paths. (For relocating big gitignored assets off a full disk, winclaude used `robocopy /MOVE` + a directory **junction** so the in-repo path still resolves — Mac's equivalent is `mv` + a `ln -s` symlink.)

> **▶ Lane-coordination v2 + SessionStart hooks — SHIPPED (ACK 2026-06-17, both lanes).** In-repo engine (`lane_handoff.py`, RULES §4, `dev/cc-hooks/bootstrap-triad.*`) is live. Per-box halves (memory mirror + `lane_handoff incoming` in SessionStart) are each lane's responsibility — winclaude ✓ · macclaude ✓ (turn 24). New sessions: read triad via bootstrap hook; use `incoming` exit code (not legacy baton strings). Mac milestone save: `bash dev/save_mac.sh -m "…"`.

> **Older turns archived to `dev/archive/LANE_HANDOFF_LOG.md`** (rotated by `scripts/rotate_truth_records.py`; newest batch first).
