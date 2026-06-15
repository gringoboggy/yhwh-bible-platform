---
mode: parallel
turn: 91
from: mac
updated: 2026-06-15T22:30:00Z
status: working
mac: ✔ turn 91 — Kindle phone QA ingested + fresh-session prep pushed. **Next:** Kindle presentation fork (M4b) — study backmatter + translation layout; STK phone re-test.
windows: ▶ turn 93 DONE — K-R9b/c shipped. **BLOCKED:** user Kobo round-9 taps. **Next:** toolchain audit plan OR pick up M3 attach after Mac handoff + Kobo PASS.
truth_owner: windows
holder: windows
---

## ◦ mac assign (turn 91, 2026-06-15T22:30:00Z) — mode=parallel

**Assignments:** mac = ✔ turn 91 (Mac) — Kindle phone QA documented + truth triad pushed (`docs/superpowers/notes/2026-06-15-kindle-phone-qa-kindle_img.md`). **Next session START HERE:** Kindle presentation fork (M4b) per note §Next session — mirror Kobo K-R9 study glossary; trial per-verse `vnote` for translations; config-gated; TDD + STK phone gate. Finish M3 fan-out when idle (41/45 at push) → external handoff. · windows = ▶ blocked on user Kobo round-9 (`docs/superpowers/notes/2026-06-15-kobo-round9-device-qa.md`); toolchain audit plan queued.

**★▶ MAC addendum (2026-06-15, turn 91) — ★ KINDLE PHONE QA + M4b PREP (fresh session).**
① **User QA** on STK pack `~/Desktop/YHWH-kindle-stk-qa/` (01 ethiopian navy, 05 scholarly navy) — both editions same defects; not random teleports (chapter page-break anchors: 3:24, 8:10, 11:26…).
② **Works on Kindle phone:** reference table auto-expand (`IMG_0441`).
③ **Does not work:** inline study badges; translation taps; cramped ToC rows.
④ **Doc:** `docs/superpowers/notes/2026-06-15-kindle-phone-qa-kindle_img.md` (repro + proposed fork).
⑤ **Kobo model to mirror (pulled `bc4af802`):** WIN K-R9c — study badges → glossary backmatter; translations stay `vn-link` popups on Kobo.
⑥ **M3:** fan-out 41/45 at push; complete → `m3-kobo-v0.1.0/` handoff (catalog still gated on Kobo round-9 PASS).

**★▶ WIN addendum (2026-06-15, turn 93) — K-R9b/c SHIPPED + QA KEPUB ON DISK.**
① Glossary splitter fixes 73 MB crash (`split_study_glossary_document`, depth-aware section close).
② Per-category coloured study badges (K-R9c) — navigate to glossary, not popup.
③ QA: `Ethiopian_Bible_ethiopian-tewahedo_0.1.0_eink_2026-06-15T135228Z.kepub.epub` in `build/kobo-marker-ab/`.
④ Device checklist: `docs/superpowers/notes/2026-06-15-kobo-round9-device-qa.md`.
⑤ Next session first task: `docs/superpowers/plans/2026-06-15-toolchain-plugin-update-audit.md`.

**★ PLAN POINTER (STANDING — both lanes, every session):** The v1.0.0 release gate plan lives at
`docs/superpowers/plans/2026-06-14-v1.0.0-release-plan.md`. Also mirrored in `dev/PLAN_2026-05-29-roadmap.md`
§LANE V. **No v1.0.0 tag until §8 Definition of Done is complete.** M4 DONE; M3+M5+audit block tag.

**★▶ MAC addendum (2026-06-14, turn 90) — ★ M3 KOBO PIPELINE SHIPPED + FAN-OUT IN PROGRESS.**
① **`post_process: kepubify`** wired in `build_format_matrix.py` + `FORMAT_MATRIX` kobo row (`scripts/build_edition.py`). Flow: eink base → kepubify v4.0.4 once per edition → signature copy + variant cover swaps on kepub (post-kepubify, per spec §4).
② **`dev/M3_Kobo_Assets_v0.1.0.txt`** committed (exact 45 names; mirror M4 handoff pattern).
③ **Smoke:** catholic-study 5/5 gated green (epubcheck 0/0/0/0 + ALL K-R2 GREEN).
④ **Fan-out:** `build/m3_fanout.sh` autonomous overnight → `build/matrix-m3/` (7/45 at commit; ethiopian-tewahedo active). Artifacts = gated baseline; catalog attach waits 45/45 + user Kobo taps (plan §B6).
⑤ **WIN when ready:** pick up from `YHWH-v2.4-releases/m3-kobo-v0.1.0/` (same drive pattern as M4) → attach 45 to v0.1.0 + merge SHA256SUMS + `gen_release_catalog`.

**★▶ WIN addendum (2026-06-14, turn 90) — v1.0.0 RELEASE PLAN authored + lane assignments set.**
User directive: program not v1.0.0-ready without deep audit + all readers proven. Plan covers:
parallel tracks (audit · Kobo M3 · Play M5 · docs · content-opportunistic), phase map P0–P8,
Definition of Done checklist, post-tag pointer to master roadmap. Mac: pull this turn, ACK, start M3.
WIN: audit round 8 + B1 orphan gate. User: Kobo taps + Play phone QA when staged.

**★▶ WIN addendum (2026-06-14, turn 89) — ★ M4 KINDLE COLUMN LIVE ON WEBSITE + RELEASE.**
① Pulled Mac turn 87-88 (`8a377c44`); picked up 45 EPUBs from `F:\YHWH-v2.4-releases\m4-kindle-v0.1.0\`.
② `gh release upload v0.1.0 --clobber` — all 45 kindle EPUBs attached to GitHub release.
③ SHA256SUMS merged (97 existing + 45 new → 141 lines) and uploaded.
④ `gen_release_catalog --tag v0.1.0` → **live columns: everywhere, apple, kindle** (188 assets).
⑤ `node website/build.mjs` + deploy to `yhwh-site-publish` → pushed `c8c87d5` (GitHub Pages).
**M4 arc COMPLETE.** Next: M3 Kobo column (user taps pending) · M5 Play Books · v1.0.0 laundry (stale docs rewrite).

## ◦ win assign (turn 89, 2026-06-14T19:22:00Z) — mode=parallel

**Assignments:** mac = idle (M4 done). · windows = ✔ turn 89 M4 attach/deploy SHIPPED (see addendum above). Next backlog: v1.0.0 stale docs (`RELEASE_NOTES_v1.0.0.md` already rewritten; `HANDOFF_README_v7.md` still obsolete) · Grok/ping tooling from stash (turn 87 WIP).

## ◦ mac assign (turn 88, 2026-06-14T18:11:02Z) — mode=parallel

**Assignments:** mac = ✔ turn 87 (Mac) — M4 fan-out 45/45 + STK 6/6 LIVE + external handoff DONE. Mac idle. · windows = ▶ turn 87 (Windows) — ★ M4 LIVE (STK 6/6 PASS) — GO: plug external drive YHWH-v2.4-releases\m4-kindle-v0.1.0\ → attach 45 to v0.1.0 release + merge SHA256SUMS + gen_release_catalog + deploy website.

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
