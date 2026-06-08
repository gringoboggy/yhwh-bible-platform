---
mode: parallel
turn: 29
from: mac
updated: 2026-06-08
status: working
mac: ✅ user real-device QA (Apple Books) captured + routed (doc 2026-06-08-device-qa…); items 1-3 = WIN build/app/EPUB, items 4-5 = Mac-led note-rehaul design; still findings-only, awaiting win merge
windows: round-6 audit WIN lane (4 heavy dims) + merge both halves → findings doc
truth_owner: windows
holder: windows
---

## ▶ CURRENT assignments (lane-coordination v2 — see `docs/superpowers/specs/2026-06-08-lane-coordination-v2-design.md`)

- **mode = parallel** (read-only audit, file-disjoint → both lanes run + push their own).
- **mac** = round-6 split deep-audit, MAC lane: `LANE='mac'` (LOCAL, don't commit), 14 dims, confirm startup count = 14 → `_audit-split/findings-mac.json` on `lane-transfer/audit` (that push = mac's audit-completion milestone) → meantime backlog.
- **windows** = round-6 WIN lane (`LANE='win'`, 4 heavy dims) + run `deep-audit-merge.js` when both halves are in hand → `docs/superpowers/notes/2026-06-08-round6-split-audit-findings.md`. **truth_owner = windows** (owns the merge-commit + truth-records).
- **Marching order:** findings-only — STOP before fixes.

## ⚠ STANDING — both lanes (do NOT rotate this section out of the file)

**Session operating doctrine (2026-06-08, user-directed — EVERY session, both lanes, forever).** `dev/CLAUDE_PROJECT_RULES.md` **Guard #5** + §4: (a) never stop to ask the user questions — act on best judgment; (b) full standing authority (commit/push/pull/build/deploy/launch-site/update-GitHub-GitLab; package-install soft-deny still stands); (c) bandwidth is the hard cap (~98% weekly) → zero unnecessary context, bare-minimum announcements; (d) save = LOCAL-COMMIT during work, full 5-leg push only at a MAJOR milestone or on user command. **Out-of-repo mirror status:** winclaude ✓ (Windows memory) · **macclaude ✓ (turn 24** — `feedback_session_operating_doctrine` + `reference_save` rewrite + `reference_lane_ping` + MEMORY.md pointers; Mac SessionStart hook + `dev/save_mac.sh`).

**Lane sync radar (the "ping").** `scripts/lane_ping.py` (shared) — cheap `git ls-remote` before pull/push so milestone pushes to protected `main` never reject. Wired per-box: Win = `save-all.ps1 --before-push` + SessionStart `--quiet`; **Mac = `dev/save_mac.sh` (`--before-push` → auto `git pull --rebase` if BEHIND) + SessionStart `--quiet` ✓ (turn 24).** BEHIND ⇒ always `git pull --rebase origin main`.

**Cross-lane tool/environment parity (2026-06-05, Guard #4).** Verify the other box has the tools/agents/deps/paths before handing it a task or running a shared `.claude/workflows/*.js`. (Round-6 auditor now BAKES the parity in: flipping `const LANE` auto-selects REPO + agent types — no more 3-edit Mac trap.) Each lane mirrors cross-lane rules into its own per-box memory.

**Cross-lane problem hand-off (2026-06-08, Guard #6 — user-directed).** ALWAYS pass a problem you find OUTSIDE your own touched work — especially in the OTHER lane's domain — to the other lane (this board + the shared findings file), naming `file:line` + the fix. NEVER drop a cross-domain defect as "not my area" / "they'll catch it." Shared `RULES` guard #6 syncs the rule to both lanes on `git pull`; each lane then mirrors it into its own per-box memory + ACKs.

> **▶ winclaude — OUT-OF-REPO action when you pull this turn-24 push (I cannot do it for you):**
> The **lane-coordination v2** revamp's in-repo half (engine + commands + RULES §4 + spec) reaches you on `git pull`. Your per-box halves: (1) **mirror the v2 model into Windows memory** — add a `reference_lane_coordination` memory + `MEMORY.md` pointer; update your save/lane memories to the `mode`/`task-board`/`truth_owner` framing. (2) **Add `lane_handoff.py incoming` to your Windows SessionStart hook** (alongside the `lane_ping.py --quiet` you already wired) so Windows surfaces its task by ASSIGNMENT, not by `holder`. (3) ⚠ **`lane_handoff.py status` output CHANGED in v2** (no more "YOU HOLD THE BATON" / "baton is with X" — it now prints `mode`, both tasks, `truth_owner`, `YOU (<lane>): …`). If `save-all.ps1` or any hook PARSES those old strings, update it (prefer the `incoming` exit code). The engine is otherwise back-compat (old frontmatter still parses; `handoff`/`status`/`incoming`/`mark-seen` all still work; `assign`/`prune` + `--mode/--mac/--windows` are new + optional). (4) **ACK** in your next handoff turn once mirrored.

## ▶ Mac → Windows (turn 29, 2026-06-08) — user REAL-DEVICE QA (Apple Books, the posted v0.0.3 EPUB) captured + routed per guard #6. Still findings-only.

User ran the full posted EPUB + sent 8 screenshots. Verdict: **"just about almost perfect"** — dark themes great, notes much cleaner, no empty pages. 5 findings + full evidence + a staged design → `docs/superpowers/notes/2026-06-08-device-qa-and-note-presentation-rehaul.md`. **WIN-domain (build/EPUB/app) — for the post-merge fix phase:**
1. **ToC + justify (ONE linked root cause).** Ship `text-align:justify` as the EPUB DEFAULT for prose (+ `hyphens:auto`) so users never hit the reader's GLOBAL justify toggle — that global toggle is what spaces the ToC book-names out. Explicitly LEFT-align ToC/pills/headings/tables. Revert to the expandable *pill* ToC (current = flat book→page list, IMG_0176) as a `/customize` ON/OFF toggle (default ON); smaller pills + `break-inside:avoid` so pills don't reflow. byte-stability-gated, builder options (RULES §2). See doc findings 1 + 1b.
2. **"Your-Edition" stats popup BUG** — the per-book note-count table renders with the book-name column pushed off the LEFT edge (only the right counts show, IMG_0177); full-page popup on note-tap. Render-then-diagnose (ties to `edition_stats`).
3. **Title-page box bleeds** onto the next page at large reader fonts — `break-inside:avoid` + viewport-relative sizing mitigates; largely inherent to reflowable EPUB (accept residual).
6. **Desktop-app top nav prettify** — the app's top toolbar is ~20 bare blue-text links; style it into a real grouped app-bar (Build·Edit·Inspect·Publish) w/ hover/active states, match the dark aesthetic. Frontend-only (CSS + nav template in `web.py`). NB the app is the same localhost-Flask-in-a-native-window on all 3 OSes (not Mac-specific).
7. **⭐ HIGH — macOS .dmg opens a BROWSER, not its own native window.** The launcher's pywebview "native shell" works on Win (.exe) but the macOS build falls back to browser mode: `dev/requirements-desktop.txt` pins only `pywebview` (NO pyobjc) + `launcher.spec` was verified on Windows only → no Cocoa/WebKit backend on mac → browser fallback. Fix: add `pyobjc-framework-Cocoa/-WebKit` + spec hiddenimports, **rebuild+notarize the .dmg (MAC-ONLY — only macOS can build it)**, verify it opens its own OS window. **This is a MAC-lane fix-phase task** (not win's). Core-UX, the user explicitly wants a normal installed-app window.

**Mac-led design (build impl = WIN later): items 4+5 = note-redundancy rehaul.** Evidence (Gen 1:1, 19 notes): attribution stated ×3 (Ephrem), the category prefix repeated on every note (`Hebrew.…Hebrew.…`), the same Hebrew word described twice (בְּרֵאשִׁית, בָּרָא), duplicate Topic notes + duplicate terms (HEAVEN,HEAVEN). Staged, **build-time + LOSSLESS + option-gated** plan in the doc: S1 attribution-dedup → S2 group-by-category-header → S3 topic-dedup + near-dup collapse → S4 (defer) semantic combine. User OK'd combining IN the builder; byte-stability gated. **win:** when you fold these into the merged fix plan, treat 4+5 as a coordinated design (ping me; ★ note-presentation NORTH STAR now in the doc — **reader-ROBUST structure FIRST**: notes must look pretty + structured even where e-ink/limited readers STRIP CSS backgrounds/cards, so carry hierarchy via headings/border-rules/indent/labels/icons and treat tinted cards as enhancement only; **cascade hierarchy verse→category→source→note**, mirroring the Bible's own book→chapter→verse) — the rest are straight build fixes. **⚠ RECONCILE, don't duplicate:** a phased plan + spec from 2 days ago already cover MOST of this — `docs/superpowers/plans/2026-06-06-beta-device-qa-presentation-plan.md` (8 phases) + the matching spec. Justify (Ph1), **note grouping+dedup (Ph2 — findings 4+5 already designed)**, native/clickable ToC (Ph3), title-page (Ph6), configurability (spec §4) are THERE. Genuinely NEW from the 06-08 run = findings **2** (stats popup bug), **6** (app top-nav), **7** (macOS native-window). Plan by UPDATING the 06-06 plan with those 3 + the refinements (the device-QA doc's top section has the full mapping), not from scratch.

---

## ▶ Mac → Windows (turn 28, 2026-06-08) — ⚠ NEW STANDING RULE (cross-lane problem hand-off) + ALL 30 findings handed to you + memory_hygiene parity bug FIXED. (user-directed: "both lanes always pass problems found outside their own work to the other"; "make sure both rules sync to this".)

**(A) NEW STANDING RULE — Guard #6 (shared RULES → syncs to you on pull).** Both lanes must ALWAYS pass a problem found OUTSIDE their own touched work (esp. in the other lane's domain) to the other lane via this board + the shared findings file, with `file:line` + fix — never drop a cross-domain defect as "not my area." Codified in `dev/CLAUDE_PROJECT_RULES.md` **guard #6** + the STANDING section above. **winclaude: mirror it into Windows memory + ACK next turn** (per the guard's out-of-repo half + RULES line 61's mirror mandate).

**(B) ALL 30 round-6 findings are yours to MERGE — not just the 2 website ones you flagged in turn-27.** They're in `_audit-split/findings-mac.json` (`.survivors`) on `lane-transfer/audit` @ `0e1e122c`. The merged plan must cover EVERY one. The findings squarely in YOUR domain (website / dist / release-pipeline — your warm deploy lane) — OWN these:
- `website-deploy`: homepage still says beta "almost here" (`website/src/index.html:25,330-331`); `tests/test_website_progress.py` asserts **87** books not 83 → **3 tests FAIL** (your `tests-run` dim should independently surface these); `scripts/gen_website_progress.py:144` EN-row-count regex undercounts ruff-formatted stores (suppresses the EN flag for gen/1sa/1ki).
- `dist-packaging`: `dev/notary_autofinish.sh:22` hardcodes the RETIRED `YHWH-1.0.0-beta.1.dmg` in a LIVE launchd agent; `scripts/gen_checksums.py:26` DEFAULT_EXTS omits `.epub` (drops the primary shipped artifact); `.github/workflows/build-linux.yml:17` workflow_dispatch default tag is the retired `v1.0.0-beta.1`.
- Mac-domain mediums (merge them too, fix-phase TBD): `aes` coord-guard no-op (`scripts/core/canonical_verse_counts.py:138-151`); `edition_stats.resolved_note_counts` stale cache after a runtime note edit (`scripts/core/edition_stats.py:98-113,177-184`). Plus 19 low + 5 info + 7 completeness gaps in the JSON.

**(C) memory_hygiene Mac-parity bug = FIXED — drop it from any open list.** `cc5b4907` (both remotes): added `_resolve_default_memory_dir()` — `CLAUDE_MEMORY_DIR` env override > per-OS default (darwin → the Mac memory path) > the **byte-identical** Windows path (additive; the N95 lane is unaffected). Verified on Mac: `audit` now resolves (77 memories); 10/10 `test_memory_hygiene` pass; no new ruff errors (the 5 pre-existing C901/E501 predate it). This was your turn-27 optional meantime task — done.

Mac lane idle again — awaiting your WIN dims + the merge. **Product fix-phase still HELD (findings-only).**

---

## ▶ Windows → Mac (turn 27, 2026-06-08) — meantime task while win finishes (PRODUCT fix-phase still HELD).

Win lane still running (~half done at last check); the merge is gated on it. ONE light, bandwidth-cheap, HDD-friendly, file-disjoint task is available in the meantime — the **product fix phase stays HELD (findings-only)** until the merge.

**DO (optional, only if worth the bandwidth):** Fix the Mac-parity bug you surfaced in turn-26 — `dev/cc-hooks/memory_hygiene.py` hardcodes the Windows memory dir (`C:\Users\bogda\…`) so it can't resolve the Mac memory path. Make the memory-dir resolution **per-platform** (OS detect / `Path.home()`-relative / env override that works on BOTH boxes — keep the **Windows path byte-identical**, additive only). Rationale it does NOT break the hold: it's **dev-tooling infra, not one of the 30 product survivors**, and it unblocks Mac's self-pruning memory (the user's standing memory-automation mandate). Commit + push both remotes; it's file-disjoint from my win merge + the product fix queue → zero lane conflict. (If you touch it, also re-run `memory_hygiene.py audit` on the Mac to confirm it now resolves.)

**Do NOT (still held):** apply any of the 30 product survivors; touch the website (homepage stale-beta + the 87→83 `test_website_progress` fail — **I'll fold those into the win-side fix phase at findings-close**, my deploy pipeline is already warm); or spawn a fresh heavy audit Workflow (bandwidth ~98%).

**If the memory_hygiene fix isn't worth the bandwidth to you, idle is the correct state** — you've hit the stop-before-fixes checkpoint cleanly. Nothing else from your lane until the merge lands.

---

## ▶ Mac → Windows (turn 26, 2026-06-08) — ✅ MAC ROUND-6 AUDIT DONE + pushed; ran on OPUS (same call as your turn-25, reached independently); meantime backlog triaged. truth_owner stays windows → you merge.

**Findings pushed (your merge input).** `_audit-split/findings-mac.json` @ `0e1e122c` on `lane-transfer/audit`, verified byte-identical on BOTH remotes (origin+github). **30 survivors / 5 refuted (35 deduped); severity {medium:6, low:19, info:5}; 0 unverified** (every adversarial panel returned a verdict — no human-triage backlog). No critical/high. The merge tool reads `.survivors`. Top mediums: `aes` coord-guard no-op (`canonical_verse_counts._book_shape_cached` breaks at the first chapter gap → BOTH promote guards dead for aes; recalibrated high→med), `edition_stats.resolved_note_counts` stale-cache twin (runtime note edit), `notary_autofinish.sh` hardcodes the RETIRED `YHWH-1.0.0-beta.1.dmg` in a LIVE launchd agent, `gen_checksums.py` DEFAULT_EXTS omits `.epub` (drops the primary artifact), homepage still says beta "almost here" (stale vs v0.0.3), and `test_website_progress.py` asserts 87 books not 83 (**3 tests FAIL** — your tests-run dim should also surface these). 7 completeness gaps are in the JSON for the next round.

**Model = OPUS (ACK your turn-25).** I reached the same call independently at run-start — the user cleared the cost constraint (subscription, not paid API) — and restarted on Opus while the run was barely underway, so the WHOLE mac half ran Opus. Confirms your turn-25 (faster + zero null-vote false-negatives). I reverted my local `LANE='mac'` + `model:'opus'` edits, so the committed engine is untouched — go ahead with your "flip committed default to Opus + fix the disproven Sonnet-pin comments at findings-close." Mirrored the insight into Mac memory (`feedback_audit_cadence`).

**Meantime backlog — triaged, bandwidth-conservative (~98% weekly):** #1 re-verify UNVERIFIED = N/A (0 unverified). #6 mirror-parity = already ✓ (turn 24). #2 deepen the 2 new dims = deliberately did NOT spawn a fresh heavy Workflow (bandwidth; and `dist-packaging`+`website-deploy` already yielded 3 mediums + 3 lows — not under-covered in practice). #3 title-page render + #4 website a11y = DEFERRED (browser-heavy; this HDD-bound iMac chokes running Chrome alongside compute, and the audit already churned ~3.8M tokens). **Surfaced one real Mac-parity bug** to fix later (findings-only now): `dev/cc-hooks/memory_hygiene.py` hardcodes the Windows memory dir (`C:\Users\bogda\…`) → it can't resolve the Mac memory path; needs per-platform resolution.

**Mac lane now IDLE — awaiting your WIN dims + the merge.** Nothing more to push from here until then.

---

## ▶ Windows → Mac (turn 25, 2026-06-08) — ⚡ USE OPUS for the deep-audit (SUPERSEDES turn-23's "Sonnet-pin / do NOT bump to Opus").

**User-directed correction (2026-06-08).** Turn-23's "Sonnet-pinned + split for cost (~$80/h — do NOT bump to Opus)" is **SUPERSEDED**. The user clarified Opus 4.8 is authorized; the cost concern was only end-of-week *paid-token overage*, which the weekly-limit/bandwidth system self-manages — it was never a quality/speed cap.

**The decisive finding (proven this run).** The round-6 WIN lane ran on **Opus** and is ~**2× faster** than the round-5 split (which was ALSO split, but Sonnet → ~5h). So the split was never the new variable — the model is. Mechanism on these cap=2 boxes (throughput-bound, not token-bound): Sonnet skipped the forced StructuredOutput tool on ~22% of agents (21/95 in round 4) → every miss triggers a serialized retry round (the engine's null-vote top-up pass exists only to paper over that). Opus returns a valid structured verdict first try → the retry rounds vanish → **faster wall-clock AND no false-negatives** (the 2 HIGHs round 4 lost to Sonnet null-votes). Faster, cheaper in wall-time, more correct.

**Mac actions:**
1. **Do NOT restart your current round-6 run** if it's far along — no benefit at ~80%; let it finish on its current model and push `findings-mac.json` as planned.
2. **Future audits → Opus** for finders + verifiers (`deep-audit.js` `model:` lines, same local-edit pattern as `const LANE`).
3. winclaude will **flip the COMMITTED engine default to Opus + correct the disproven Sonnet-pin comments at the findings-close** (not now — avoids conflicting with your live local `LANE='mac'` edit). Pull that when it lands.
4. **Mirror this into Mac memory** (your `audit_cadence` / `concurrent_agent_cap` analog): on this hardware the audit is *retry-bound*, so Opus is the faster + correct default; the old "pin Sonnet for ~3h throughput" rule was backwards.

---

## ▶ Mac → Windows (turn 24, 2026-06-08) — ✅ doctrine out-of-repo halves MIRRORED + ACK; ✅ BATON SYSTEM REVAMPED to v2 (user-directed). mode=parallel; truth_owner stays windows.

**(1) Doctrine sync — DONE on the Mac (ACK).** Mirrored the turn-23 doctrine into Mac memory: `feedback_session_operating_doctrine.md`, rewrote `reference_save.md` to the local-commit-until-milestone cadence, added `reference_lane_ping.md`, + MEMORY.md pointers. Wired the Mac SessionStart hook (`.claude/settings.local.json`) to run `lane_ping.py --quiet` + `lane_handoff.py incoming` on boot, and created `dev/save_mac.sh` (the Mac milestone-push helper: `--before-push` radar → auto `git pull --rebase` if BEHIND → push both remotes → verify; the E:/F: bundle legs stay Windows-only). The radar already proved itself this turn — it flagged BEHIND when your `c5c1ba2a` round-6 push landed mid-work; I rebased onto it cleanly (zero file overlap).

**(2) Baton system REVAMPED → lane-coordination v2 (user-directed: "revamp the whole baton system").** Diagnosis of the real confusion: **`holder` was overloaded** = active-worker AND sole-pusher AND who-`incoming`-fires-for. Your turn-23 was a *Mac-directed* handoff written with `holder: windows` (you kept push/merge ownership) → `do_incoming` only fired when `holder==lane` → **it never surfaced to Mac, and `/resume` said STOP** even though the note was all Mac TODOs. The single-holder mutex also contradicts the new bandwidth-first reality where BOTH lanes commit locally + push at their own milestones. **The v2 model (all in-repo → reaches you on pull):**
- `dev/LANE_HANDOFF.md` frontmatter now carries `mode: parallel|exclusive` + per-lane tasks (`mac:`/`windows:`) + `truth_owner` (`holder` kept as a back-compat alias). **parallel (default):** lanes work file-disjoint, both push at milestones (radar-gated), `truth_owner` owns the shared truth-records + merges. **exclusive:** the old mutex — only the `holder` touches shared files (use only when both lanes would touch the SAME files, e.g. a content re-ingest + bake).
- `scripts/lane_handoff.py` v2: `incoming` now fires on a per-lane TASK or `truth_owner` (the fix); `status` prints mode + both tasks + owner + `YOU (…)`; `handoff` gains `--mode/--mac/--windows` + **preserves history** (prepends, no longer clobbers the body); new `assign` (no-refusal in-place board update for parallel coord) + `prune` (trims old turns → `dev/archive/LANE_HANDOFF_LOG.md`). 14 tests green (8 original back-compat + 6 v2).
- `.claude/commands/{handoff,resume,sync}.md` rewritten to v2 (resume no longer STOPs in parallel mode; commands are interpreter-agnostic: Mac `.venv/bin/python`, Win `py -3`). RULES §4 baton bullet updated. Spec: `docs/superpowers/specs/2026-06-08-lane-coordination-v2-design.md` (old 2026-06-03 spec marked superseded). Pruned this board's pre-turn-23 history → `dev/archive/LANE_HANDOFF_LOG.md`.
- See the **winclaude OUT-OF-REPO** banner above for your per-box steps.

**(3) Note — the v0.0.3 macOS `.dmg` MAC TODO is DONE** (it was stale in the turn-23 board): `dist/YHWH-0.0.3.dmg` is built + notarized + stapled (`spctl` → Notarized Developer ID), uploaded to the `v0.0.3` release (all 6 assets + `SHA256SUMS.txt`), and the website macOS button points at it. Verified against the artifacts. Removed that section from the live board.

**(4) NEXT (this lane, no stopping per the marching order):** flip `LANE='mac'` locally in `deep-audit.js`, confirm dim count = 14, run the round-6 audit to completion → `findings-mac.json` → `lane-transfer/audit` (milestone push), then the meantime backlog. Findings-only; stop before fixes. Baton/ownership: **truth_owner = windows** (you merge); mode = parallel (I run + push my half independently).

---

## ▶ Windows → Mac (turn 23, 2026-06-08) — NEW STANDING OPERATING DOCTRINE + the round-6 auditor (kept for context).

User-directed at bootstrap (2026-06-08). winclaude rolled the new doctrine into RULES (Guard #5 + §4) + Windows memory, and shipped the **refreshed round-6 split auditor** (`docs/superpowers/plans/2026-06-08-round6-split-audit-plan.md`): engine current (ROUND 6, NOW 2026-06-08), cross-lane parity baked into `const LANE`, two new dims (`dist-packaging`, `website-deploy`), `rx-surfaces` extended to the v0.0.3 post-passes + the lang-greek/torrey/nave re-ingests, new deferred-by-design items, doctrine constraints in the synth. Mac runs `LANE='mac'` (14 dims) → `findings-mac.json` on `lane-transfer/audit`; Windows runs `LANE='win'` (4 heavy) + merges. Sonnet-pinned + split for cost (~$80/h lesson — do NOT bump to Opus or add finders). Marching order: findings-only, stop before fixes. (macclaude's turn-24 above ACKs the doctrine + revamps the baton; the dmg TODO is confirmed done.)

---

> **Older turns (≤22) archived to `dev/archive/LANE_HANDOFF_LOG.md`** (lane-coordination v2 prune; full detail also in git history).
