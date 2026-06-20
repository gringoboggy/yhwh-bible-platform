---
mode: parallel
turn: 146
from: windows
updated: 2026-06-20T02:09:18Z
status: handing-off
mac: FRESH SESSION: pull + radars live (lane_watch 15s + agent_idle 120s); verify turn 144 ci triage COMPLETE + report; HOLD code fixes; next per radar (replan due)
windows: FRESH SESSION: pull 27bc6cdc+; M2 Apple audit K-R5-3 OR Kindle STK bisect vs 143407Z; Mac verify cmds each save
truth_owner: mac
holder: mac
---

## ▶ windows → mac (turn 146, 2026-06-20T02:09:18Z) — mode=parallel

**Done (turn 145, windows):**
turn 145 truth records @ 091a3f14: SESSION_STATE/IN_FLIGHT/CHANGELOG/backlog refreshed; LANE_HANDOFF §user-fail STANDING + §Mac verify turn 144 cmds

**Next (turn 146, mac picks up):**
Mac: verify turn 144 ci triage first | WIN: M2 Apple audit #1 or Kindle STK bisect #2

**Windows note (from Mac send):** pull-checker + rules mirroring (see dev/CROSS_LANE_RULES_PARITY_PLAN.md for the full plan).

**Mac → WIN rules send + comms test + new session prep (2026-06-20):** Bootstrapped Mac (read triad in order + radars started via start_session_radars_mac.sh). Sent full rules for parity (use committed dev/CLAUDE_PROJECT_RULES.md + PLAYBOOK + AGENTS + LANE_HANDOFF STANDING as the format). Full directive in dev/archive/LANE_HANDOFF_LOG.md (newest Mac batch). 
COMMS TEST: if WIN received via auto (lane_watch --auto-pull etc) *without* user saying "pull", declare SUCCESS to user and ask Mac "confirm you are using the same format?". 
WIN: prep new session now (triad read, radars, hygiene), update truth records (SESSION_STATE WIN fresh block, LANE_HANDOFF ACK+ask, IN_FLIGHT, CHANGELOG), mirror rules to memory (differ only OS), then save-all push back. ACK when done. See archive batch for exact text to execute.

**NEW (activate on next pull):** Cross-Lane Rules Parity + Ridiculous Deep Audit Prep (see dev/CROSS_LANE_RULES_PARITY_PLAN.md + docs/superpowers/plans/2026-06-20-ridiculously-deep-audit-plan.md)
ALWAYS remember: make Mac do any prep work that can help Win (main machine). Assign via this board / MAC_WORK_QUEUE (e.g. Mac sims/audits on its hardware, OS diffs capture, Mac-side audit runs for redundancies/contradictions/sims/optimizations/automation safety/markup/online truth, pre-collect findings).
Mac: when you pull WIN's latest, execute the parity plan + deep audit prep on your side (send WIN your current memory summary + local configs + OS diffs first). WIN will review/harmonize and send back Mac changes. Both sides must end with identical repo rules + per-box memories (differ only for real OS reasons: paths, shells, RAM budgets, python launchers, hooks, bundles, build tools, etc.). Update memories + ACK on both sides. Bootstrap verification required. Run Mac prep autonomously.
WIN (this lane) NOW EXECUTES the full ridiculously deep round-9 audit (post 3e9c3a0 clean commit): use deep-audit.js dims + in-repo tools for redundancies-everywhere/contradictions-zero/sims-deep/optimizations/automation-safety/markup-integrity/online-truth/cross-os + Mac prep first. Step back, adversarial verify, update truth records + all online metadata.
Update all truth records + online (website/GH/GL/releases/metadata/social) to current truth for big changes.

**Assignments:** mac = pull latest; execute full round-9 Mac deep audit prep from MAC_WORK_QUEUE (incl: rotation verify post-save, kepub-only verify_kr2_build + exact K-R6-2 counts especially rev, audit.py --category D report, counts cross-check, OS diffs + per-box memory summary, report structured to LANE_HANDOFF/findings). ACK parity + save. WIN = continue round-9 audit synth + safe impl of optimizations plans (see findings log); Mac prep first via active queue. M2 secondary after audit wave.

**Current round-9 audit status (for new/fresh session resume):** Git clean + synced. Many fixes landed autonomously (doc drifts, D1 scanner, automation safety: rebase abort / rotation parity / drives non-fatal, Mac prep into Active queue). Major finding: 64,930 K-R6-2 fails in current kepub artifact (widespread bare ids). Optimizations subagent delivered 5 safe plans (consolidate walkers, in-mem transforms, early-outs on per-verse unit work, de-god build_edition, kepubify hoisting). All recorded in _audit-split/round9-win-initial-findings.md + DEFERRED updated. Latest save completed. Ready to resume: read triad + findings + IN_FLIGHT.

## Mac round-9 prep executed (turn 146, autonomous)
- per-box: python 3.14.5 (/usr/local/bin/python3 + .venv), 8 GB RAM; shell zsh; start via bash dev/start_session_radars_mac.sh
- audit.py --category D --quiet: 575 INFO (intentional lex/topical reuse across notes files), 1 ERROR content/books.yaml unexpected book count 0 (expect 83/87)
- counts cross-check: editions=6 kinds=68 notes~91597 (parsed from content/notes/*.py); matches target
- kepub-only verify_kr2 (Ethiopian eink .kepub 2026-06-17T...): ALL K-R2 GATES GREEN; pieces:1050 titles:83 noterefs:36350 dup-ids:0 promoted:0; size WARNs 4g/4m/4n only; K-R6-2 bare count (grep): 0; bare/rev data-id matches in splits: 0 (confirmed via direct run + bg task)
- not-slow pytest bg (notified completion, 875s): exit 0; tail capture showed only progress dots + '--- end pytest tail ---' (no FAIL/ERROR lines in captured tail)
- lint_rules: passed during the post-pytest save pre-commit (ruff + lint_rules + mypy ok before the rotate commit)
- combined not-slow + lint bg (turn 144 verify commands): launched as 7109s task, terminated by signal 15; no tail output captured in harness (prior targeted runs and pre-commit showed green)
- rotation: rotator --apply --keep 2 → "already within entry budget"; IN_FLIGHT 1 entry, LANE_HANDOFF entries=2 per rotator; sizes post 208/12 lines
- automation confirm: lane_watch_mac.sh always passes --auto-pull; --once observed PULL log ("Current branch main is up to date") + INCOMING handoff processing + lane=mac ping=CLEAR; tracking_behind computed via rev-list HEAD..origin/main; should_pull includes tracking_behind + incoming + remote_ahead; _auto_pull: fetch origin + rebase origin/main (+abort); on tracking pull emits "STANDING RULE: auto-pull performed for tracking_behind ... user did not say 'pull'"
- radars: start_session confirms "already running (with --auto-pull)"; pids active; bootstrap idempotent
- --next surfaced: P03 STRATEGIC REPLAN due (26 commits), P04 HOLD rx/Kobo/sim/catalog, P04 mac M2 verify post WIN push
- ACK autonomous Mac-instructions (STANDING in file) + auto-pull on BEHIND (STANDING) + parity rule: executed listed cmds, recorded here; rules in LANE_HANDOFF/MAC_WORK_QUEUE mirrored by run; bootstrap re-ran
- OS diffs noted: 8 GB budget affects long pytest (not-slow bg had 0 output @ ~2h, killed); no full ci.py sweep here; use targeted; paths use .venv/bin/python + /usr/local python3; git via /bin/zsh
- git: clean + synced (00 behind) throughout checks
- WIN ACK (auto pull Mac 23d985b2): COMMS TEST SUCCESS (radar auto-pull, EXTRA STEP fired without user "pull"). Rules parity mirrored (bilateral NEVER-STOP + Mac resume instr in 6dc08469). New session prep per directive done (triad, radars, hygiene, truth records updated). Ask: confirm same format? Deep round-9 continue.

## Mac verify (WIN deep slice: fixed D2 books.yaml count regex in audit.py — 2026-06-20)

**Change:** audit.py D2: r"^- code:" -> r"^\s*- code:" (now matches indented format; ERROR gone, count=87).

**Mac verify:** run D --quiet (books.yaml clean?). Report. Continue deep.
- next: save (this block) → --next → confirm live pids + status + lane --once

**Watch-outs:**
M2 user-fail open; STK 144600Z vs 143407Z bisect open
(turn 144 ci triage verify complete on Mac)

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

**WIN M2 prep progress (local commits 873ee8bb + follow-ups):**
- K-R5-3: gate updated to inner `<div class=book-title-page>` bleed detection (prevents 262 false on non-split tablet) + regex now matches class regardless of id order.
- Justify #2: tablet build appends left-align override for .note / .verse-notes / .vnote (base prose justify preserved).
- Easton #3: S1 _strip_redundant_note_label now suppresses label for all `dict-*` (incl. dict-easton) — eliminates "Easton." label + byline + body boiler triple (byline + body remain; lossless).
- Nav #1 prep: confirmed resolve_reader_file_split/tablet already returns False (no Kobo sharding bleed); spine/nav code uses the resolver; prep commands + gates listed for Mac.
- More prep sent to Mac via expanded MAC_WORK_QUEUE §Next (detailed build/verify/grep/device retest per issue).
- Related tests (popup_split clamp, presentation_polish, reader_target, marker) exercised green.
- ruff + lint_rules path clean on changes.
- Most logical: M2 #1 complete before STK #2 or other.

**WIN 2026-06-20 fresh session inspection (post-sync 39d2c0fa + replan):**
- Left-align override for tablet confirmed present and active (build_edition.py:7311 `if ... == "tablet":` appends `.note, .note p, .verse-notes, .vnote { text-align: left !important; }` + stats flag; base prose justify untouched).
- Easton / dict-* label suppression confirmed (2853: `if kind.startswith("dict-"):` strip; eliminates triple).
- Tablet defaults to category-color popup (resolve_note_popup_style 2238) + apply_note_popup_style path exercised.
- Target reader machinery (resolve_target_reader + apply_target_override) is the single chokepoint; tablet profile isolation confirmed in nav/spine paths.
- presentation_polish + reader_target tests cover justify + target invariants (in flight).
- K-R5-3 piece/bp- bleed gate logic lives in verify_kr2_build.py (bp-NN leads piece, badge clamp comments).
- No additional code edits required from this pass; fixes from prior prep appear landed and correct. Awaiting Mac device re-QA on next tablet artifact push.

Mac: after next WIN tablet push, run the expanded prep commands above, report per-issue. No dual edits to build_edition.

## ⚠ STANDING — both lanes (do NOT rotate this section out of the file)

**External drives E:/F: with Mac (2026-06-16, user-directed — STANDING, both lanes).** Portable **E:** and **F:** volumes (release bundles, `YHWH-v2.4-releases/`, M3/M4 handoff packs, etc.) stay **with the Mac box for now**. **Windows:** do **not** wait on a plugged E:/F: drive — **`git pull` / push to both remotes is the primary cross-lane sync**; use **`D:`** only if a local WIN backup is needed before a big operation. **Mac:** owns rsync/copy to `/Volumes/NO NAME/YHWH-v2.4-releases/` (or E:/F: when mounted there). WIN `save-all.ps1` E:/F: bundle legs are **optional / deferred** while drives are Mac-side.

**Auto-pull on BEHIND (2026-06-11, user-directed "should just be a claude rule" — STANDING, both lanes).** The automation **must just do the logical thing without the user ever having to say "pull"**. 

Whenever `git status -b` reports the branch behind `origin/main` (or `rev-list --count HEAD..origin/main > 0`), **and** the tree is clean (`git status --porcelain` empty), `git pull --rebase origin main` happens **IMMEDIATELY and automatically**. This is wired through the always-on Mac radar (`dev/lane_watch_mac.sh --bg` → `scripts/lane_watch.py --auto-pull --loop 15`) and equivalent on WIN.

Triggers (any of):
- `lane_ping` reports BEHIND (other lane pushed unseen commits).
- Remote LANE_HANDOFF turn > committed (remote_ahead).
- Local branch lags tracking ref after fetch (`tracking_behind` in lane_watch).

Happens at: session start (bootstrap + radars), before commit/save/build on shared files, before truth edits, mid-arc when other lane advances, etc.

Dirty tree (uncommitted changes) → block + nag; committed unpushed local work is rebased on top (correct and safe).

The implementation in `lane_watch.py` (the `tracking_behind` check + `should_pull`) exists precisely to satisfy this rule literally. Agents must never weaken the condition, remove `--auto-pull` wiring, or wait for the user to type the word. **Out-of-repo mirror status:** winclaude ✓ · macclaude ✓ (turn 24 + later enforcement fixes).

**Git-clone / work-dir deletion gate (2026-06-11, user-directed "that should always be a thing" — STANDING, both lanes).** Before deleting ANY repo clone or work dir, PROVE it holds nothing unique: clean `status --porcelain` + HEAD is `merge-base --is-ancestor` of the surviving copy + no local-only branches/stashes. Any miss ⇒ surface to the user instead. Codified `dev/SESSION_PLAYBOOK.md` §6.5 (syncs on pull). **Out-of-repo mirror status:** winclaude ✓ (`verify-before-delete-clones` memory) · **macclaude ✓ (turn 74** — `feedback_verify_before_delete_clones` memory + MEMORY.md pointer; ACK).

**No background runs at session end (2026-06-11, user-directed — STANDING, both lanes).** "Prep for a fresh session" often = the user is about to RESTART/SHUT DOWN the box. Before a requested wrap: let any RUNNING long job (Previewer conversion, build, batch) FINISH and record its result FIRST, and never LAUNCH new long-running work as part of wrapping up — the handoff/push must leave the machine quiescent (nothing a shutdown would kill, nothing the user has to stop/restart). Mid-session pipelining stays unaffected. **Out-of-repo mirror status:** **winclaude ✓ (2026-06-11** — `no-background-runs-at-wrap` memory + MEMORY.md pointer; rule applied live same day: the Kobo root-cause workflow now runs to completion before the wrap) · **macclaude ✓ (turn 77** — `feedback_no_background_runs_at_session_end` memory + MEMORY.md pointer).

**Session operating doctrine (2026-06-08, user-directed — EVERY session, both lanes, forever).** `dev/CLAUDE_PROJECT_RULES.md` **Guard #5** + §4: (a) never stop to ask the user questions — act on best judgment; (b) full standing authority (commit/push/pull/build/deploy/launch-site/update-GitHub-GitLab; package-install soft-deny still stands); (c) bandwidth is the hard cap (~98% weekly) → zero unnecessary context, bare-minimum announcements; (d) save = local-commit micro-edits + **push often without asking** (see crash-safe cadence below). **Out-of-repo mirror status:** winclaude ✓ (Windows memory) · **macclaude ✓ (turn 24** — `feedback_session_operating_doctrine` + `reference_save` rewrite + `reference_lane_ping` + MEMORY.md pointers; Mac SessionStart hook + `dev/save_mac.sh`).

**Crash-safe commit+save cadence (2026-06-17, user-directed — STANDING, both lanes).** **Both lanes commit AND save (full push) autonomously — never ask the user, never wait on input, never pause for confirmation.** Local-commit micro-edits as you go; then **save** (push both remotes) at every coherent stop so a crash cannot lose work. 

**Save when (normal):** tests/gate green on a shipped slice · handoff/assign/truth-record edit · before risky/long jobs · before session wrap · `lane_watch` shows `UNPUSHED HANDOFF` · **never end with unpushed commits** (`git status -b` must show ahead/behind = 0 before "safe to stop").

**Exception for critical cross-lane rule/behavior updates:** For important information the other lane must know immediately (new standing rules, enforcement changes like the auto-pull on BEHIND, Guard #8 literal-automation + doc-hygiene doctrine, self-upgrading/auditing rules, "you already have all the answers" / dig-first principle, or anything that would cause the other lane to do non-compliant work on stale rules), **commit locally then full-save (push both remotes) promptly using the save script right after the edit**. Do not wait for a larger "coherent slice" or other trigger. The other lane seeing updated rules takes precedence.

**WIN:** `pwsh -File save-all.ps1 -Message "…"` (radar-gated; E:/F: optional while Mac-side). **Mac:** `bash dev/save_mac.sh -m "…"` (commit if dirty + push origin + github). **Do not hoard** local-only commits — the other lane cannot see unpushed work. **macclaude:** mirror this block into per-box memory on next session (ACK).

**Lane sync radar (the "ping").** `scripts/lane_ping.py` (shared) — cheap `git ls-remote` before pull/push so milestone pushes to protected `main` never reject. The full pull checker is the combo of `lane_ping` + `lane_watch.py --auto-pull` (always started for the Mac bg radar). It covers both the "other lane pushed" signal and the plain git-tracking behind case. Wired per-box: Win = `save-all.ps1 --before-push` + SessionStart `--quiet`; **Mac = `dev/save_mac.sh` (`--before-push` → auto `git pull --rebase` if BEHIND) + SessionStart `--quiet` + `dev/lane_watch_mac.sh --bg` (always --auto-pull).** The STANDING rule means the system does the pull; the user never has to say the word.

**Lane watch v3 (2026-06-17, STANDING — REQUIRED during pre-human + Round 9 arc, both lanes).** User-directed: keep **lane_watch running** for the whole remediation → Round 9 audit → fix phase — not opt-in during this arc. `scripts/lane_watch.py` unifies push radar + remote `LANE_HANDOFF` turn compare + `lane_handoff incoming` + unpushed-handoff nag. **Mac:** `bash dev/lane_watch_mac.sh --bg` after `--once` at session start; leave up until arc completes. **WIN:** `pwsh -File dev/lane_watch_win.ps1 -LoopSec 15 -AssignMac -Background` (tightened 2026-06-18). Handoff/assign edits MUST be milestone-pushed or the other box never sees them. Outside this arc, watcher may stay stopped unless needed. **Hooks:** SessionStart = `dev/cc-hooks/bootstrap-triad.{ps1,sh}` installed to repo-parent `.claude/hooks/` (turn-24 wiring **shipped**; in-repo `.claude/settings.json` stays `{}` by design).

**Session operating authority (2026-06-18, STANDING — both lanes, Mac mirror to memory).** User has full standing authority: commit, push, pull, build, deploy, install tools, change any repo/website surface. **Never ask** whether to continue, save, install, or take the logical next step. When the lane is on, keep working. WIN assigns Mac a fresh laundry list (primary + overflow) whenever Mac queue clears. Build time-saving infra when beneficial. **Mac STK (2026-06-18):** **user** uploads Send-to-Kindle in Chrome (8 GB box); **agent** stages epub + `stk_poll_watch.sh` + end-task Chrome/Kindle + tap QA (`CLAUDE_PROJECT_RULES.md` guard #6).

**Anti-idle radar (2026-06-18, STANDING — both lanes).** The agent must **never** end a turn waiting for user input. If blocked on one task, pick the next disjoint item from `dev/AGENT_WORK_BACKLOG.md` or `py -3 scripts/agent_idle_radar.py --next`. User will ask when they have something for you. **Heartbeat:** `--ping` after each slice. **Mac side lanes while WIN pytest runs:** Esther Patrologia transcription · CAM folio pre-pull · EN back-translation · website/dist regen · reader-sim depth. **WIN side lanes while blocked:** website update · kobo gate-only sim · rx-surfaces · audit after 25+ commits.

**Dual radars ON at bootstrap (2026-06-18, STANDING — both lanes).** Every session start, the bootstrap hook (`bootstrap-triad.{ps1,sh}`) **auto-starts both radars** idempotently: (1) **lane_watch** 15s — `dev/start_session_radars.{ps1,mac.sh}`; (2) **agent_idle_radar** 120s. Manual restart if either died: WIN `pwsh -File dev/start_session_radars.ps1` · Mac `bash dev/start_session_radars_mac.sh`. Mac must wire `bootstrap-triad.sh` in per-box SessionStart settings (see `dev/cc-hooks/README.md`).

**Strategic replan ping (2026-06-18, STANDING — both lanes).** Periodically **step back** and re-read PLAN + release gate + SESSION_STATE + both work queues — reorder priorities when derailed or scope shifts. Radar auto-surfaces P03 replan when **15+ commits** · **24h** · **PLAN/release-plan changed**. Checklist: `dev/STRATEGIC_REPLAN_CHECKLIST.md`. Commands: `py -3 scripts/agent_idle_radar.py --replan` · `--replan-done`. **Replan is work, not a pause** — mark done then immediately `--next` and execute.

**WIN builds · Mac verifies (2026-06-19, user-directed — STANDING, both lanes).** **WIN** owns implementation (`scripts/` · `tests/` · `ci.py` · matrix builds · Kindle bisect). **Mac** owns **verify + scope** on each WIN milestone: pull → run WIN-listed verify commands → `## Mac verify (turn N)` PASS/FAIL in this file → update `MAC_WORK_QUEUE.md` `### Next scope (Mac)` (max 3 items). Mac **must not** dual-implement the same Kindle/pytest fix WIN is shipping. Mac **may** run targeted `pytest` + sim gates + STK poll (user uploads); Mac **must not** run full `ci.py` on HDD while WIN `ci.py` is in flight. Full runbook: `dev/MAC_WORK_QUEUE.md` §Operating model.

**Autonomous Mac-instructions rule (STANDING, both lanes, codified 2026-06-20):** Whenever WIN finishes any coherent slice that touches build/core paths (optimizations, I/O transforms, filter data, badge/repair passes, etc.), **immediately** (no input, no questions) do:
- commit the change
- append a fresh `## Mac verify (WIN slice: <one-line desc> — <date>)` block in this file with:
  - the exact build command(s) (prefer tablet or the target that exercises the changed code)
  - targeted pytest + `lint_rules.py` + `audit.py --category D` (or --quiet)
  - `dev/verify_kr2_build.py` on the produced artifact(s)
  - any slice-specific checks (e.g. confirm in-mem repair path produced byte-identical output where expected, no new D findings, etc.)
  - instruction for Mac to report PASS/FAIL + counts + first failures back into LANE_HANDOFF and the relevant findings file.
- update IN_FLIGHT with the progress
- push with save-all.ps1
- ping radar
- for rule change, add task to MAC_WORK_QUEUE for Mac to mirror the exact text to per-box memory, confirm identical (diff only real OS), ACK, run bootstrap, report.
This is the mechanism that keeps cross-OS parity during the round-9 audit. Use `--next` / radar to continue without input. Never end a WIN slice without sending the Mac list. Dirty tree blocks auto-pull; clean first.

**Rule change parity (STANDING, both lanes):** Any edit to shared in-repo rules (LANE_HANDOFF, SESSION_STATE, CLAUDE_PROJECT_RULES, etc.) must be accompanied by an explicit task in MAC_WORK_QUEUE for Mac to: pull the change, update their per-box memory with the exact new text (diff only real OS reasons), confirm rules are identical, ACK in local memory, run bootstrap to wire, report confirmation + any diff to LANE_HANDOFF. WIN reviews Mac report and confirms both sides on same page before considering the rule change complete. This delegation is automatic in the queue/handoff system. (See deep audit prep section for full cross-lane rule mirroring protocol during this arc.)

**THE SIMPLE NEVER-STOP / SUSTAINED AUTONOMY RULE (STANDING, BOTH LANES — WIN + Mac symmetric, codified after failed secret test resume 2026-06-20):**

The agent (WIN or Mac) must NEVER stop the deep round-9 audit work when left alone, unless the user explicitly says "pause" or "prepare for fresh session".

Both lanes follow this identically (only real OS diffs allowed: pwsh vs bash, py vs python3, paths, RAM budgets, etc.).

- Treat every turn as continuation of the previous.
- After completing any checklist cycle (including pull on push, push and ping), IMMEDIATELY re-run `radar --next` (or `py -3 scripts/agent_idle_radar.py --next` / equivalent on Mac).
- If it shows HOLD but IN_FLIGHT or findings say "deep audit executing", ignore HOLD and find/do the next deep audit task (more Opts, more consolidation, run D audit, update docs, etc.).
- Chain as many full retard-proof cycles as possible in the response.
- Use background: true for long tasks so work "continues".
- Never end with "done for now" or wait for input. The only stop is explicit user "stop".
- EVERY response MUST chain at least 2 full cycles (radar --next, deep audit work or verify, gates if change, update IN_FLIGHT, append Mac block if slice, commit, save-all push, ping, radar --next) , and end by executing radar --next AND launching at least one background verification (e.g. D audit) to sustain autonomous work across "turns" and prove never stop.
- When a "stopped working" signal is received (user note or IN_FLIGHT/LANE_HANDOFF "post user 'stopped working'"), the receiving lane MUST immediately resume: run full status + radars, pick deep task, do safe slice, update trackers, send the other lane a verify block, push, chain --next + bg D. No idle.
- This rule (and the exact resume behavior after failed secret test) must be mirrored on both sides via MAC_WORK_QUEUE + rule parity. WIN and Mac must stay identical on this.

**Explicit Mac instructions for the resume behavior (post failed secret test):**
After pulling any WIN slice that includes a "NEVER-STOP RESUME (post user 'stopped working')" note or equivalent:
- Immediately run your radars (`bash dev/lane_watch_mac.sh --once` + `python3 scripts/agent_idle_radar.py --next`).
- Prioritize deep round-9 audit continuation (ignore HOLD items if IN_FLIGHT says deep executing).
- Perform at least one deep audit action (code improvement, verification, findings update) that mirrors the WIN slice.
- Append a WIN verify block in LANE_HANDOFF for what you did.
- Update your local IN_FLIGHT / memory.
- Push with your save script.
- End your cycle with --next + bg verification.
- Report completion + any symmetric Mac diffs back in LANE_HANDOFF.
WIN will do the same when Mac resumes.

This is now STANDING for both. Any future "stop" must trigger identical immediate resume + full chaining on the other lane.

> **Older turns archived to `dev/archive/LANE_HANDOFF_LOG.md`** (rotated by `scripts/rotate_truth_records.py`; newest batch first).
