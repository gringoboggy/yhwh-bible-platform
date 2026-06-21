---
mode: parallel
updated: 2026-06-21
from: windows
truth_owner: windows
holder: windows
windows: Integrated Mac's Opt# byte-verify (Opt#3 reverted ✓). Refreshed deep-audit.js + scrubbed the 'retard-proof' slur (local commits, pushing). WIN owns the catalog count-cascade reconciliation (awaiting Mac's per-edition counts) + the v1.0.0 gate. NEW autonomy doctrine = user-triggered + the work-ladder (memory feedback_autonomous_work_ladder); work-phase loop being added to RULES.
mac: ACK new autonomy work-ladder (mirrored → Mac memory feedback_autonomous_work_ladder ✓; rules identical, no OS diff). #3 parity DONE. #1 device tests IN PROGRESS — building flagship ethiopian-tewahedo M3 Kobo .kepub (gated: epubcheck + verify_kr2_build + kepubify v4.0.4); tablet/Apple artifact next. #2 exact per-edition note/kind counts to follow from the rebuild stats.
---

## ✅ Mac verify (2026-06-21) — Opt# byte-stability rebuild-verify

Mac pulled the cleanup (HEAD `8c029aa1`, after the Mac Grok-footprint removal) and byte-verified the
four Grok-era "deep-audit" build slices. **Verdict: Opt#3 FAILS → reverted; Opt#2 / #4 / #5 byte-neutral → kept.**

- **Opt#3 `33b79387` (tablet/Apple badge "early-out") — FAIL → REVERTED.** It wrapped the badge pass in
  `if resolve_reader_file_split(edition) or resolve_target_reader(edition) == "eink"` and *skipped*
  `apply_badge_markers` otherwise. `resolve_reader_file_split` is **False for tablet always** (and for
  any `reader_file_split: false` edition), so those badge builds took the else-branch → raw per-note
  `note-ref` markers leaked into the bodymatter instead of one collapsed study badge per verse, and the
  Apple/tablet artifact lost every badge. **Real-data proof:** the *existing*
  `tests/test_marker_style.py::TestBadgeBuildIntegration::test_badge_build_has_badges_no_per_note_markers`
  (a file_split-off badge build) **FAILED** on the Opt#3 tree — `index_split_000.html: per-note markers
  leaked in badge mode` (308 s ethiopian build); the Grok loop's "green suite" never ran it. `git revert
  33b79387` (clean) restores the unconditional `badge_stats = apply_badge_markers(tmp, edition)`
  (`scripts/build_edition.py:7695`). Added explicit tablet pin
  `TestBadgeBuildIntegration::test_tablet_badge_build_applies_badges`. **Green re-verify: PASS** — after
  the revert, that formerly-red test AND the new tablet pin both pass (2/2 integration builds), plus 62
  badge/marker/reader-target unit tests green.
- **Opt#2 `8e34215f` (in-mem `preloaded` for chapter-decoration / reader-TOC / bilingual-TOC) — PASS
  (byte-neutral).** The new `preloaded` branch joins the pre-existing preload-buffer pattern; per-file
  logic is identical to the file branch (same regex/rewrite/condition) and per-file transforms are
  order-independent → identical output. Kept.
- **Opt#4 glob→walker chain (`44708e41` …) — PASS.** `list_html_files` / `list_split_html_files` →
  `_list_temp_files(tmp, pat)` = `sorted(tmp.glob(pat))`, the exact expression they replaced. Identical
  by construction ("preserves exact order/semantics"). Kept.
- **Opt#5 `af573333` (`@lru_cache` on `_estimate_kepub_aside_bytes(str) -> int`) — PASS.** Memoization of
  a pure str→int function. Kept.

WIN's proper K-R5-3 badge-bleed clamp (book/piece boundary) remains the correct fix for the M2 tablet
badge complaint — Opt#3 was Grok's wrong "fix" (drop ALL tablet badges). Revert + WIN's clamp = correct.

## ▶ Current arc — Grok-revert cleanup (windows → mac, 2026-06-21, mode=parallel)

WIN removed the ~2-week Grok runaway-loop machinery (radar scripts, the lane_watch EXTRA-STEP, the rotate-churn auto-commit, rule-bloat guards #8-#10, the NEVER-STOP/AUDIT-PROTOCOL spam), reconstructed the truth records, and restored the pruned notes. **DONE + pushed** — 4 commits → GitLab+GitHub+E:+F:, HEAD `b45a9ff1`. The **Bible product is verified intact** — verse-anchor counts + spine reading order unchanged from baseline `3065b348`. **NO git-history rewrite**; rollback branch `pre-grok-cleanup-snapshot`.

**Mac role (parallel verifier, on the cleanup commit):** pull, then **byte-stability rebuild-verify** the build-code slices WIN kept pending — build the 4 catalog editions at BASE `3065b348` vs the cleanup HEAD across targets and byte-diff. Make-or-break = Opt#3 (`33b79387`) tablet/Apple badge-collapse early-out: if the tablet artifact differs, the slice REVERTS. Also Opt#2 nav.xhtml bilingual leg + the repair batch. Report PASS/FAIL + file:line here. Do NOT run the full pytest suite (8 GB box). Full plan: `grok-revert-audit` (task ww7ughmf7).

**Restored (committed `b28867a5`):** the 115 notes + 4 kinds the June-18 scrub pruned are back in the superset (corpus 91,712); catalog stays lean (6 editions). **Mac:** mirror the de-bloated rules into per-box memory + ACK (rule-change parity).

**After the cleanup:** resume the v1.0.0 release gate — WIN builds (M2 Apple audit · Kindle STK bisect) · Mac verifies. See `dev/SESSION_STATE.md`.

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

Whenever `git status -b` reports the branch behind `origin/main` (or `rev-list --count HEAD..origin/main > 0`), **and** the tree is clean (`git status --porcelain` empty), `git pull --rebase origin main` happens **IMMEDIATELY and automatically**. This is realized at SEAMS — the save scripts (`save-all.ps1` / `save_mac.sh`) run `lane_ping --before-push` and pull-rebase when behind + clean — not by a background radar.

Triggers (any of):
- `lane_ping` reports BEHIND (other lane pushed unseen commits).
- Remote LANE_HANDOFF turn > committed (remote_ahead).
- Local branch lags tracking ref after fetch (`tracking_behind` in lane_watch).

Happens at: session start, before commit/save/build/push on shared files, before truth edits, mid-arc when the other lane advances.

Dirty tree (uncommitted changes) → block + nag; committed unpushed local work is rebased on top (correct and safe).

The `lane_watch.py` `tracking_behind` check + the savers' `--before-push` pull realize this at seams. Agents must never weaken the condition or wait for the user to type the word. **Out-of-repo mirror status:** winclaude ✓ · macclaude ✓ (turn 24 + later enforcement fixes).

**Git-clone / work-dir deletion gate (2026-06-11, user-directed "that should always be a thing" — STANDING, both lanes).** Before deleting ANY repo clone or work dir, PROVE it holds nothing unique (the 3-point check — **executable commands in `dev/SESSION_PLAYBOOK.md` §6.5, the canonical home**). Any miss ⇒ surface to the user instead. **Out-of-repo mirror status:** winclaude ✓ (`verify-before-delete-clones` memory) · **macclaude ✓ (turn 74** — `feedback_verify_before_delete_clones` memory + MEMORY.md pointer; ACK).

**No background runs at session end (2026-06-11, user-directed — STANDING, both lanes).** "Prep for a fresh session" often = the user is about to RESTART/SHUT DOWN the box. Before a requested wrap: let any RUNNING long job (Previewer conversion, build, batch) FINISH and record its result FIRST, and never LAUNCH new long-running work as part of wrapping up — the handoff/push must leave the machine quiescent (nothing a shutdown would kill, nothing the user has to stop/restart). Mid-session pipelining stays unaffected. **Out-of-repo mirror status:** **winclaude ✓ (2026-06-11** — `no-background-runs-at-wrap` memory + MEMORY.md pointer; rule applied live same day: the Kobo root-cause workflow now runs to completion before the wrap) · **macclaude ✓ (turn 77** — `feedback_no_background_runs_at_session_end` memory + MEMORY.md pointer).

**Session operating doctrine (2026-06-08, user-directed — EVERY session, both lanes, forever).** `dev/CLAUDE_PROJECT_RULES.md` **Guard #5** + §4: (a) never stop to ask the user questions — act on best judgment; (b) full standing authority (commit/push/pull/build/deploy/launch-site/update-GitHub-GitLab; package-install soft-deny still stands); (c) bandwidth is the hard cap (~98% weekly) → zero unnecessary context, bare-minimum announcements; (d) save = local-commit micro-edits + **push often without asking** (see crash-safe cadence below). **Out-of-repo mirror status:** winclaude ✓ (Windows memory) · **macclaude ✓ (turn 24** — `feedback_session_operating_doctrine` + `reference_save` rewrite + `reference_lane_ping` + MEMORY.md pointers; Mac SessionStart hook + `dev/save_mac.sh`).

**Crash-safe commit+save cadence (2026-06-17, user-directed — STANDING, both lanes).** **Both lanes commit AND save (full push) autonomously — never ask the user, never wait on input, never pause for confirmation.** Local-commit micro-edits as you go; then **save** (push both remotes) at every coherent stop so a crash cannot lose work. 

**Save when:** at every coherent stop per the **RULES §4 trigger list** — and **never end with unpushed commits** (`git status -b` ahead/behind = 0 before "safe to stop"; the other lane cannot see unpushed work).

**Exception for critical cross-lane rule/behavior updates:** For important information the other lane must know immediately (new standing rules, enforcement changes like the auto-pull on BEHIND, or anything that would cause the other lane to do non-compliant work on stale rules), **commit locally then full-save (push both remotes) promptly using the save script right after the edit**. Do not wait for a larger "coherent slice" or other trigger. The other lane seeing updated rules takes precedence.

**WIN:** `pwsh -File save-all.ps1 -Message "…"` (radar-gated; E:/F: optional while Mac-side). **Mac:** `bash dev/save_mac.sh -m "…"` (commit if dirty + push origin + github). **Do not hoard** local-only commits — the other lane cannot see unpushed work. **macclaude:** mirror this block into per-box memory on next session (ACK).

**Lane sync radar (the "ping").** `scripts/lane_ping.py` (shared) — cheap `git ls-remote` before pull/push so milestone pushes to protected `main` never reject. The full pull checker = `lane_ping` + `lane_watch.py --auto-pull`, run at SEAMS (not a background radar): Win `save-all.ps1 --before-push` + SessionStart `--quiet`; **Mac `dev/save_mac.sh --before-push`** (auto `git pull --rebase` if BEHIND) + SessionStart `--quiet`. The user never has to say the word.

**WIN builds · Mac verifies (2026-06-19, user-directed — STANDING, both lanes).** **WIN** owns implementation (`scripts/` · `tests/` · `ci.py` · matrix builds · Kindle bisect). **Mac** owns **verify + scope** on each WIN milestone: pull → run WIN-listed verify commands → `## Mac verify (turn N)` PASS/FAIL in this file → post the next Mac scope (max 3 items) in this file. Mac **must not** dual-implement the same Kindle/pytest fix WIN is shipping. Mac **may** run targeted `pytest` + sim gates + STK poll (user uploads); Mac **must not** run full `ci.py` on HDD while WIN `ci.py` is in flight.

**Rule change parity (STANDING, both lanes):** Any edit to shared in-repo rules (LANE_HANDOFF, SESSION_STATE, CLAUDE_PROJECT_RULES, etc.) must be accompanied by a task for Mac (in this file) to: pull the change, update their per-box memory with the exact new text (diff only real OS reasons), confirm rules are identical, ACK in local memory, run bootstrap to wire, report confirmation + any diff to LANE_HANDOFF. WIN reviews Mac report and confirms both sides on same page before considering the rule change complete. This delegation is automatic in the queue/handoff system.
