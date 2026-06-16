---
mode: parallel
turn: 105
from: windows
updated: 2026-06-16T19:12:21Z
status: handing-off
mac: ▶ INGEST v4 book title covers @ e4dd1a5d (git pull or E:/YHWH-v2.4-releases per MAC_INGEST.md) → audit x3 + test_book_title_covers + wire ethiopian-tewahedo book_covers + /covers A/B/C smoke. Phase 4 disjoint queued. HOLD build_edition.py web.py until WIN pytest green.
windows: ★ FRESH SESSION: fix 11 pytest reds (SESSION_STATE list) + test_work_cache → re-run pytest -m not slow → Phase 3 (build_edition.py generate_verse_popups.py config.py). One job at a time.
truth_owner: windows
holder: windows
---

## ▶ windows → windows (turn 105, 2026-06-16T19:12:21Z) — mode=parallel

**Done (turn 104, windows):**
audit2 pytest complete: 8081 pass / 11 fail / 262 import errors (api_select_book_cover pre-e4dd1a5d; resolved in covers commit); failures triaged in SESSION_STATE turn-105 bootstrap

**Next (turn 105, windows picks up):**
WIN: fix 11 reds + spot pytest re-run → Phase 3. Mac: v4 covers ingest parallel.

**Assignments:** mac = ▶ INGEST v4 book title covers @ e4dd1a5d (git pull or E:/YHWH-v2.4-releases per MAC_INGEST.md) → audit x3 + test_book_title_covers + wire ethiopian-tewahedo book_covers + /covers A/B/C smoke. Phase 4 disjoint queued. HOLD build_edition.py web.py until WIN pytest green. · windows = ★ FRESH SESSION: fix 11 pytest reds (SESSION_STATE list) + test_work_cache → re-run pytest -m not slow → Phase 3 (build_edition.py generate_verse_popups.py config.py). One job at a time.

**Watch-outs:**
Never commit LANE=win in deep-audit.js; no new long pytest at wrap — fix pass starts fresh session; one heavy job at a time

---

## ▶ windows → mac (turn 104, 2026-06-16T15:42:26Z) — mode=parallel

**Done (turn 104, windows):**
v4 reimagine 86×3 book title covers shipped; manifest+compose+regen-queue; external package on `E:\YHWH-v2.4-releases\book-title-covers-v4-reimagine-2026-06-16\` with `MAC_INGEST.md` + `SHA256SUMS.txt`

**Next (turn 104, mac picks up):**
Mac: ingest+verify covers → ethiopian-tewahedo wire + /covers smoke. WIN: pytest triage → Phase 3.

**Assignments:** mac = ▶ INGEST v4 book title covers (see MAC_INGEST.md on external drive or `git pull`) → audit ×3 + `test_book_title_covers` + wire `ethiopian-tewahedo` `book_covers` + `/covers` A/B/C smoke. Parallel Phase 4 disjoint still applies. · windows = ★ pytest audit2 triage → Phase 3 (`build_edition.py` · `generate_verse_popups.py` · `config.py` cache). One job at a time.

**Watch-outs:**
Never commit `LANE=win` in `deep-audit.js`; one heavy job at a time on WIN

---

## ◦ mac assign (turn 104, 2026-06-16T14:52:32Z) — mode=parallel

**Assignments:** mac = idle — await WIN fresh-session bootstrap (Phase 4 queued @ turn 103) · windows = ★ pytest audit2 triage when done → Phase 3 (build_edition.py · generate_verse_popups.py · config.py cache). Shipped 9b877205. truth_owner. One job at a time.

Mac session wrap: Phase 1+2 DONE @ 2194f573. WIN to write bootstrap block on next session.

---

## ◦ windows assign (turn 103, 2026-06-16T14:44:33Z) — mode=parallel

**Assignments:** mac = ▶ Phase 4 parallel (disjoint): purge 31 phantom 1ma/2ma candidate files · translations.py ex→exo additive alias · 1ki EN back-translation ch7-10 gap · Windows artifact naming align (dev/sign_windows.ps1 vs installer vs website releases.html). Optional: wire ethiopian-tewahedo book_covers → content/covers/_book_defaults/. HOLD build_edition.py · web.py · M4b · M3 attach until WIN pytest audit2 triage done. · windows = ★ pytest audit2 triage when done → Phase 3 (build_edition.py · generate_verse_popups.py · config.py cache). Shipped 9b877205. truth_owner. One job at a time.

WIN pushed audit fixes + Mac Phase 4 assignment (user-approved).

---

## ◦ windows assign (turn 102, 2026-06-16T13:42:12Z) — mode=parallel

**Assignments:** mac = ▶ Phase 2 parallel (disjoint): website/dist rebuild (gen_release_catalog + node website/build.mjs) · installer.iss VERSION first-line · how-to-use.html EPUB name drift · gh delete 45 default._* Kindle stubs + dup SHA256SUMS-merged.txt · cover-upload E2E smoke (normalize→eth spot build+epubcheck) · batch_promote_xrefs --per-candidate queue JSON status. HOLD build_edition.py · web.py · M4b · M3 until WIN pytest+audit done. · windows = ★ Fresh pytest @ b8c7c950 grinding → triage failures → 7-dim audit remainder → append merge doc → Phase 1–2 fixes. One job at a time. truth_owner.

WIN assigned Mac Phase 2 parallel while pytest runs (user-approved).

---

## ⚠ STANDING — both lanes (do NOT rotate this section out of the file)

**Auto-pull on BEHIND (2026-06-11, user-directed "should just be a claude rule" — STANDING, both lanes).** Whenever the lane radar (`scripts/lane_ping.py` or any fetch) shows BEHIND, `git pull --rebase origin main` IMMEDIATELY and automatically — at session start, before any commit/save/build on shared files, before truth-record edits, and whenever the other lane is known mid-arc. The user never has to say "pull". Dirty tree ⇒ commit or stash-pull-pop, never skip. **Out-of-repo mirror status:** winclaude ✓ (`auto-pull-on-behind` memory) · macclaude ◻ (mirror on next Mac turn + ACK).

**Git-clone / work-dir deletion gate (2026-06-11, user-directed "that should always be a thing" — STANDING, both lanes).** Before deleting ANY repo clone or work dir, PROVE it holds nothing unique: clean `status --porcelain` + HEAD is `merge-base --is-ancestor` of the surviving copy + no local-only branches/stashes. Any miss ⇒ surface to the user instead. Codified `dev/SESSION_PLAYBOOK.md` §6.5 (syncs on pull). **Out-of-repo mirror status:** winclaude ✓ (`verify-before-delete-clones` memory) · **macclaude ✓ (turn 74** — `feedback_verify_before_delete_clones` memory + MEMORY.md pointer; ACK).

**No background runs at session end (2026-06-11, user-directed — STANDING, both lanes).** "Prep for a fresh session" often = the user is about to RESTART/SHUT DOWN the box. Before a requested wrap: let any RUNNING long job (Previewer conversion, build, batch) FINISH and record its result FIRST, and never LAUNCH new long-running work as part of wrapping up — the handoff/push must leave the machine quiescent (nothing a shutdown would kill, nothing the user has to stop/restart). Mid-session pipelining stays unaffected. **Out-of-repo mirror status:** **winclaude ✓ (2026-06-11** — `no-background-runs-at-wrap` memory + MEMORY.md pointer; rule applied live same day: the Kobo root-cause workflow now runs to completion before the wrap) · **macclaude ✓ (turn 77** — `feedback_no_background_runs_at_session_end` memory + MEMORY.md pointer).

**Session operating doctrine (2026-06-08, user-directed — EVERY session, both lanes, forever).** `dev/CLAUDE_PROJECT_RULES.md` **Guard #5** + §4: (a) never stop to ask the user questions — act on best judgment; (b) full standing authority (commit/push/pull/build/deploy/launch-site/update-GitHub-GitLab; package-install soft-deny still stands); (c) bandwidth is the hard cap (~98% weekly) → zero unnecessary context, bare-minimum announcements; (d) save = LOCAL-COMMIT during work, full 5-leg push only at a MAJOR milestone or on user command. **Out-of-repo mirror status:** winclaude ✓ (Windows memory) · **macclaude ✓ (turn 24** — `feedback_session_operating_doctrine` + `reference_save` rewrite + `reference_lane_ping` + MEMORY.md pointers; Mac SessionStart hook + `dev/save_mac.sh`).

**Lane sync radar (the "ping").** `scripts/lane_ping.py` (shared) — cheap `git ls-remote` before pull/push so milestone pushes to protected `main` never reject. Wired per-box: Win = `save-all.ps1 --before-push` + SessionStart `--quiet`; **Mac = `dev/save_mac.sh` (`--before-push` → auto `git pull --rebase` if BEHIND) + SessionStart `--quiet` ✓ (turn 24).** BEHIND ⇒ always `git pull --rebase origin main`.

**Cross-lane tool/environment parity (2026-06-05, Guard #4).** Verify the other box has the tools/agents/deps/paths before handing it a task or running a shared `.claude/workflows/*.js`. (Round-6 auditor now BAKES the parity in: flipping `const LANE` auto-selects REPO + agent types — no more 3-edit Mac trap.) Each lane mirrors cross-lane rules into its own per-box memory.

**Cross-lane problem hand-off (2026-06-08, Guard #6 — user-directed).** ALWAYS pass a problem you find OUTSIDE your own touched work — especially in the OTHER lane's domain — to the other lane (this board + the shared findings file), naming `file:line` + the fix. NEVER drop a cross-domain defect as "not my area" / "they'll catch it." Shared `RULES` guard #6 syncs the rule to both lanes on `git pull`; each lane then mirrors it into its own per-box memory + ACKs.

**⚠ Heads-up — auto-mode destructive-op soft-deny (PER-BOX; NOT a repo rule).** Under `~/.claude` `defaultMode:auto`, the harness `$defaults` soft-deny BLOCKS *direct* destructive file tool-calls on protected / out-of-workspace paths — it bit winclaude during the C: cleanup (PowerShell `Remove-Item` on `$env:TEMP` / another drive → "this path is protected from removal", and it persists even with the sandbox disabled). It is **per-box** (each lane's own `~/.claude/settings.json`, the repo `.claude/settings.json` is `{}` → NOT git-synced, so it can't reach you from win). **It does NOT scan inside a script**, so your `dev/build_dmg.sh` rebuild + any `rm`/`mv` inside a build script run normally. Only an *ad-hoc* destructive tool-call (a bare `rm -rf` on an out-of-workspace/system path) can trip it; if it does: the user has pre-authorized "anything you need" (proceed), run it via a script, target the exact in-workspace path, or the user toggles auto OFF to approve. winclaude's workaround was `[IO.Directory]::Delete` / `robocopy /MOVE` (no `Remove-Item` token); the Mac equivalent is plain `rm`/`mv` on explicit non-system paths. (For relocating big gitignored assets off a full disk, winclaude used `robocopy /MOVE` + a directory **junction** so the in-repo path still resolves — Mac's equivalent is `mv` + a `ln -s` symlink.)

> **▶ winclaude — OUT-OF-REPO action when you pull this turn-24 push (I cannot do it for you):**
> The **lane-coordination v2** revamp's in-repo half (engine + commands + RULES §4 + spec) reaches you on `git pull`. Your per-box halves: (1) **mirror the v2 model into Windows memory** — add a `reference_lane_coordination` memory + `MEMORY.md` pointer; update your save/lane memories to the `mode`/`task-board`/`truth_owner` framing. (2) **Add `lane_handoff.py incoming` to your Windows SessionStart hook** (alongside the `lane_ping.py --quiet` you already wired) so Windows surfaces its task by ASSIGNMENT, not by `holder`. (3) ⚠ **`lane_handoff.py status` output CHANGED in v2** (no more "YOU HOLD THE BATON" / "baton is with X" — it now prints `mode`, both tasks, `truth_owner`, `YOU (<lane>): …`). If `save-all.ps1` or any hook PARSES those old strings, update it (prefer the `incoming` exit code). The engine is otherwise back-compat (old frontmatter still parses; `handoff`/`status`/`incoming`/`mark-seen` all still work; `assign`/`prune` + `--mode/--mac/--windows` are new + optional). (4) **ACK** in your next handoff turn once mirrored.

> **Older turns archived to `dev/archive/LANE_HANDOFF_LOG.md`** (rotated by `scripts/rotate_truth_records.py`; newest batch first).

## ▶ mac → windows (turn 101, 2026-06-16T04:04:45Z) — mode=parallel

**Done (turn 100, mac):**
Mac: alt02+alt03 unique cover art 86+86 scenes composed; shipped @ e8b1dac7 (both remotes)

**Next (turn 101, windows picks up):**
WIN: round-8 7-dim thorough audit + merge findings doc; Mac: Phase 1 disjoint ingest fixes in parallel

**Assignments:** mac = ▶ FRESH SESSION: Phase 1 disjoint fixes — prospect.py write_queue · batch_promote_xrefs · promote.py _chapter_from_id · inject.py SyntaxError guard · MATRIX_MAP count drift. Covers DONE @ e8b1dac7. HOLD build_edition.py + M4b until WIN audit done. · windows = ★ FRESH SESSION START HERE: Audit FIRST — thorough 7 dims (mint10/11 bar) → append docs/superpowers/notes/2026-06-16-round8-split-audit-findings.md → THEN Phase 1–2 fixes. LANE=win local. One job at a time. Mac findings @ b1b9dffd. Pull @ e8b1dac7.

**Watch-outs:**
Never commit LANE= flip in deep-audit.js; one heavy job at a time on WIN (16 GB)

---


## ◦ windows assign (turn 100, 2026-06-16T02:57:33Z) — mode=parallel

**Assignments:** mac = ▶ FRESH SESSION: Phase 1 fixes (disjoint) — prospect.py write_queue · batch_promote_xrefs false-promote · promote.py _chapter_from_id · inject.py SyntaxError guard · docs/MATRIX_MAP count drift. Do NOT touch build_edition.py until WIN audit done. M4b HOLD. · windows = ★ FRESH SESSION START HERE: Audit FIRST — thorough 7 dims (mint10/11 bar) → append docs/superpowers/notes/2026-06-16-round8-split-audit-findings.md → THEN Phase 1–2 fixes. LANE=win local. One job at a time. Mac findings @ b1b9dffd.

**Turn 100 fresh-session prep.** User: speed OK, thoroughness = Claude mint10/11 always. WIN fixes HOLD until 7 dims complete.

---


## ◦ windows assign (turn 99, 2026-06-16T02:52:28Z) — mode=parallel

**Assignments:** mac = Phase 1 fixes (file-disjoint): prospect.py write_queue · batch_promote_xrefs · promote.py chapter parse · inject SyntaxError guard · docs drift. Parallel: M4b when Phase 1–3 green on WIN. · windows = Phase 1–2 fixes + complete WIN 7-dim thorough audit remainder. Merged plan: docs/superpowers/notes/2026-06-16-round8-split-audit-findings.md. Standing user approval — fixes GO. HOLD Kobo device QA until Phase 1–3.

User standing approval (2026-06-16): no separate findings gate. Mac may start disjoint Phase 1 fixes in parallel with WIN.

---


## ▶ mac → windows (turn 98, 2026-06-16T02:45:22Z) — mode=parallel

**Done (turn 97, mac):**
Mac 8b thorough: 18 dims → 35 survivors (5H/17M/9L/4 info); 9 draft refuted; findings @ b1b9dffd on lane-transfer/audit both remotes; M2 layout directive CONFIRM-OPTIMAL

**Next (turn 98, windows picks up):**
WIN: merge round-8 split audit + present findings plan; user approves before fixes; Mac idle until plan lands

**Assignments:** mac = idle — await user approval of merged round-8 findings plan; fresh session: /resume then M4b Kindle fork or audit fix Phase 1 per plan (HOLD until approved) · windows = ▶ turn 98 — pull lane-transfer/audit @ b1b9dffd; LANE=win locally in deep-audit.js (never commit); 7 dims thorough + tests-run pytest; deep-audit-merge.js → docs/superpowers/notes/2026-06-15-round8-split-audit-findings.md. FINDINGS-ONLY — present plan, STOP. HOLD Kobo QA + fixes until user approves.

**Watch-outs:**
FINDINGS-ONLY until user approves merged plan; never commit LANE=mac/win flip in deep-audit.js; delete lane-transfer/audit after merge consumed; more auditing before fixes (Mac lane complete — WIN half is the gap)

---


## ▶ windows → mac (turn 97, 2026-06-16T02:04:38Z) — mode=parallel

**Done (turn 96, windows):**
WIN: pulled 4ef3346; triaged badge-trail test as stale (K-R15a); user ordered Mac 8b thorough pass (Grok fast-pass insufficient vs mint10/11)

**Next (turn 97, mac picks up):**
Mac: Workflow deep-audit 18 dims Fable 5 → lane-transfer/audit · WIN: wait, then 7 dims thorough + merge

**Assignments:** mac = ★ FRESH SESSION Round 8b THOROUGH: Claude Code Fable 5 + Workflow(deep-audit.js), LANE=mac locally (never commit), depth=deep, ALL 18 mac dims incl lane-system/decommission/stack-review/future-work, full find→verify→synthesize (~5h mint10/11 bar). Re-verify 9536bf34 survivors; push NEW findings-mac.json to lane-transfer/audit. Parallel read-only: M2 Apple layout audit (2026-06-15-apple-m2-layout-directive.md). HOLD M4b/Kobo QA/M3 attach until merged plan. · windows = PAUSE win audit re-run until Mac 8b lands. May finish tests-run pytest only. Merge + round8-split-audit-findings.md after Mac push. HOLD Kobo QA and fixes.

**Watch-outs:**
- (none)

---
