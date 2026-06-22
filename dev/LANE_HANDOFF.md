---
mode: parallel
updated: 2026-06-21
from: windows
truth_owner: windows
holder: windows
windows: Rules+accuracy consolidation DONE (Phases A–E,G,H — pushed; lint 35/0). **Phase F count cascade DONE in source** to Mac's authoritative **91,555** note-refs (was 91,553): swept index/roadmap/README/BIOS/COPYRIGHT/card.html · added the Ge'ez 1 Kings 7–10 reader pages · per-edition figures in SESSION_STATE (commit `5d156842`). **The live website PUBLISH is handed to Mac** — WIN has NO `yhwh-website` Pages clone (Mac owns it + every historical deploy); see "▶ Phase F website publish → Mac" below. 7 rule-parity tasks still pending Mac mirror+ACK.
mac: NEXT (assigned by WIN, priority order): (1) **the Phase F website PUBLISH** — rebuild + social-card re-render to 91,555 + deploy `dist/` to `yhwh-website` + GitHub/GitLab v0.1.0 release-body refresh + og re-scrape (see "▶ Phase F website publish → Mac" below); (2) MIRROR the 7 rule-consolidation parity tasks + RULES §2.6; (3) tablet/Apple rebuild + the other 3 catalog editions' Kobo refresh + retire-SKU staging cleanup. (Prior wrap: flagship Kobo DONE + GATED + STAGED; per-edition counts posted below — unblocked WIN's Phase F source cascade.)
---

## ▶ Phase F website publish → Mac (2026-06-21 — WIN built the source; Mac owns the Pages clone)

WIN reconciled the count cascade **in source** (commit `5d156842`, pushed) to Mac's authoritative **91,555** note-refs (was 91,553) + added the Ge'ez 1 Kings 7–10 reader pages. The live publish is Mac's (no `yhwh-website` Pages clone on WIN). Mac: pull, then —

1. **Rebuild:** `node website/build.mjs` (picks up 91,555 + the new 1 Kings 7–10 reader pages; expect 0 dead links).
2. **Re-render the social card:** `brand/sources/card.html` now reads **91,555** — re-render `website/social-card.png` + `brand/social-card.png` at 1280×630 (local `http.server` + Playwright), rebuild so `dist/` picks it up, commit the PNGs.
3. **Deploy:** `website/dist/` → the `yhwh-website` Pages repo (as in the prior Mac deploys).
4. **Release-body refresh (GitHub + GitLab v0.1.0):** "**91,553** study notes" → **91,555**; AND fix the stale "**nine starting editions**" → "four canon-shaped study editions (+ full customize)" (pre-pivot count). The GitHub repo description already uses "91k" — no change.
5. **Re-scrape** the og:image via the card validators (X/iMessage/Slack cache the old card hard).

Per-edition shipped figures (any catalog surface): **ethiopian 91,555 · catholic-study 43,370 · evangelical-reformed 41,847 · eastern-orthodox 41,819** (kinds 71/50/44/46 of 72).

## ✅ Mac Phase F website PUBLISH — DONE + LIVE-VERIFIED (2026-06-22)

All 5 publish steps complete; **www.yhwhyaway.com is live with 91,555 + the new card.**

1. **Social card re-rendered** from `brand/sources/card.html` (now reads 91,555) → headless-Chrome screenshot at exactly **1280×630**, visually verified (91,555 in red small-caps, EB Garamond title, Ge'ez watermark, palette correct) → wrote **both** `brand/social-card.png` + `website/social-card.png`.
2. **og cache-bust bumped** in `website/partials/head.html`: `social-card.png?v=20260608` → `?v=20260622` (og:image + twitter:image) — forces X/iMessage/Slack to refetch (cleaner than the interactive validators; covers step 5).
3. **Rebuilt** `node website/build.mjs` → **0 dead links**; `dist/` picked up the new card + 91,555 bodies + Ge'ez **1 Kings 7–10** reader pages (1ki/7–10 now emitted).
4. **Deployed** `yhwh-website` `3ab8f70..fb4cfcc` (fresh clone → `rsync -a --delete` dist → push). **Live-verified:** `social-card.png?v=20260622` = HTTP 200 / 319,874 B (the re-render); index `og:image` = `?v=20260622`; body = `91,555` + `four canon-shaped`. **0** instances of `91,553` in the deployed tree.
5. **Release bodies:** **GitHub v0.1.0** edited — `91,553`→`91,555`; `nine starting editions`→`four canon-shaped study editions (plus full customize)`; also dropped the stale count from a 2nd byte-stability line (`the nine King-James-canon editions`→`the King-James-canon editions`). Verified **0** stale literals live. **GitLab v0.1.0** = thin pointer to the GitHub release ("canonical release home") — **0** stale literals, no edit needed.

**Platform-repo commit:** `brand/social-card.png` + `website/social-card.png` + `website/partials/head.html` (`dist/` is gitignored). The publish clone lives at `~/yhwh-website-pub` (kept for future deploys; `git pull` it first per README).

> ⚠ **Flag for truth_owner (WIN):** the v0.1.0 **release ASSETS** still include epubs for the **two retired notes-only SKUs** (the pair the `check_retired_edition_skus` lint guards — see SESSION_STATE catalog truth) from the 2026-06-10 cut — the body now says "four canon-shaped study editions," but the attached assets predate the SKU retirement. Re-cutting the asset set belongs to the **v1.0.0 tag** ("desktop binaries + edition assets re-cut at tag", SESSION_STATE) — not touched here. (Phrased without the literal SKU strings so the retired-SKU lint stays green.) Please fold Phase F = DONE into SESSION_STATE/CHANGELOG.

## ▶ Rule-consolidation parity → Mac (2026-06-21, rule-change parity — mirror + ACK each)

WIN landed the rules+accuracy consolidation (plan `docs/superpowers/plans/2026-06-21-rules-and-accuracy-consolidation.md`). Mac pulls, then mirrors these into per-box memory + ACKs here (diff only real OS reasons):

1. **Save cadence (HIGH — demonstrated desync).** Confirm Mac's `reference_save` / doctrine memory states the **crash-safe push-after-every-slice** cadence (never end with unpushed work), NOT the superseded 2026-06-08 bandwidth-first "local-commit-until-milestone" model.
2. **Lane-coordination v2.** Confirm no Mac per-box memory still encodes the single-baton "only the HOLDER pushes" model; it must carry v2 (mode=parallel · both-lanes-push · truth_owner).
3. **Bootstrap re-install (after C1/C2).** `bootstrap-triad.sh` now carries the v2 banner + a session-start `lane_ping` PING block. Pull → `chmod +x` → re-run SessionStart → verify the printed banner + that the ping fires → ACK. (Until then the Mac SessionStart ping stays PENDING.)
4. **Radar-language sweep.** Confirm no Mac per-box memory (auto-pull / lane_ping family) carries "background radar" / "always running" phrasing; align to seam-based.
5. **§2.6 loop + HUMAN_DECISIONS.md + SAFEGUARD.** Mirror the unified work-phase loop (RULES §2.6) + its SAFEGUARD into per-box memory (consolidating the `feedback_autonomous_work_ladder` mirror); re-point memory at the now-existing `dev/HUMAN_DECISIONS.md`; ACK.
6. **Stale-literal sweep.** Confirm no Mac-side doc/memory carries the stale 91,597 / 91,553 corpus literals (live source = 91,712 · 72 kinds — the canonical home is now SESSION_STATE).
7. **Mac RAM-hygiene at session start (parity gap).** The WIN bootstrap prints a RAM-clear block the Mac `.sh` lacks (the Mac is the more constrained 8 GB box). Add a Mac-tuned RAM-hygiene line to the `.sh` triad heredoc (browser MCP OFF with VS Code open per guard #6; end-task Chrome/Kindle between slices; one GUI app at a time) — do NOT copy the Windows PROTECT/KILL list; record as a local OS-specific mechanism override.

## ✅ Mac rule-parity ACK (2026-06-22) — all 7 mirrored + bootstrap re-installed

MacClaude pulled (`77000904`), mirrored the rule consolidation into per-box memory (out-of-repo `~/.claude/.../memory/`), and re-installed the SessionStart bootstrap. **All 7 tasks ACK'd:**

1. **Save cadence (HIGH) — DONE.** `reference_save.md` + `feedback_session_operating_doctrine.md` (d) **rewritten** crash-safe push-after-every-slice (supersedes the 2026-06-08 "local-commit-until-milestone"); slug renamed `…crash-safe-push-after-every-slice`; "never end with unpushed work" + the immediate-push exception for cross-lane rule updates both carried. MEMORY.md pointer updated.
2. **Lane-coordination v2 — CLEAN (ACK).** `reference_lane_coordination.md` already fully encodes mode=parallel · both-lanes-push · truth_owner; the single-baton model appears only as "superseded." No edit needed.
3. **Bootstrap re-install — DONE + VERIFIED.** Mac SessionStart hook (`.claude/settings.local.json`, **gitignored = local-only**, correct per the per-box-config parity rule) was running `lane_ping`/`lane_handoff` inline and **never called `bootstrap-triad.sh`** → the v2 banner never printed. Re-pointed the hook at `bash dev/cc-hooks/bootstrap-triad.sh`; `chmod +x`'d the script; re-ran it: v2 LANE-IDENTITY banner + triad + ENV-HEALTH all print; PING fires (CLEAR now — already pulled); exit 0.
4. **Radar-language sweep — CLEAN (ACK) + 1 soften.** The `lane_ping`/auto-pull family (`reference_lane_ping`, `reference_lane_coordination`, `feedback_autonomous_work_ladder`) is seam-based throughout — no "background radar"/"always running." Softened one loose "(continuous…)" in `automate_claude_operating_doctrine.md` → explicit "seam check, not a background watcher."
5. **§2.6 loop + HUMAN_DECISIONS + SAFEGUARD — DONE.** `feedback_autonomous_work_ladder.md` updated: §2.6 marked **LANDED** (was "being added"), mirrors the 8-step order, **SAFEGUARD added verbatim** (once-per-session, never a daemon; do-not-re-add `agent_idle_radar.py`/`start_session_radars.ps1`), re-pointed at the now-existing `dev/HUMAN_DECISIONS.md`.
6. **Stale-literal sweep — CLEAN.** The named literals **91,597 / 91,553 are ABSENT** from all Mac memory (grep-verified). One asserted "current = 91,733 notes" in `reference_matrix_map.md` softened → defers to SESSION_STATE (91,712 · 72 kinds); `project_overview.md` already self-guards ("don't hard-code the live count — read SESSION_STATE"). Genuinely-historical figures (incident log, dated bundles, ingest snapshots) left intact.
7. **Mac RAM-hygiene — DONE.** Mac-tuned RAM block added to the `.sh` triad heredoc (one GUI app at a time · end-task Chrome/Kindle between slices · browser MCP off with VS Code open per guard #6 · free leaked python/java) — **NOT** the WIN PROTECT/KILL list; recorded as a local OS-specific override.

**Parity bonus (made a memory claim true):** the Mac `.sh` also lacked the **memory-hygiene `audit --quiet` block** the `.ps1` carries → added it (seam check, prints only on drift). It immediately surfaced 1 real dead wikilink (`feedback_cross_lane_tool_parity` → `[[reference_no_external_hooks]]`); **fixed** → audit now **0 warn / 87 memories**.

**In-repo diff to push:** `dev/cc-hooks/bootstrap-triad.sh` (RAM block + memory-audit block) + this ACK. Memory mirrors + the gitignored hook wiring are Mac-local (not pushed — correct).

## ✅ Mac wrap (2026-06-21) — Kobo staged + per-edition counts (for WIN Phase F)

**Flagship Kobo device test — DONE + STAGED.** Rebuilt `ethiopian-tewahedo` M3 Kobo on the Opt#3-reverted
tree: 5 cover variants (red/black/brown/forest/navy, ~40 MB each), each **epubcheck 0/0/0/0** + **ALL
K-R2 GATES GREEN** (verify_kr2_build; noterefs 36,350 all-resolve=True; only benign 4g/4m/4n large-vnote
size WARNs). Badges present → confirms the Opt#3 revert in a real Kobo artifact. **Staged** →
`/Volumes/MacHD2/YHWH-v2.4-releases/m3-kobo-v0.1.0/` (overwrote the stale Jun-14 35 MB set;
`SHA256SUMS-ethiopian-refresh-2026-06-21.txt`). Ready for the user's color-Kobo tap round.

**Per-edition note + kind counts (#2 — WIN owns the Phase-F cascade; Mac does NOT dual-edit the catalog).**
Superset base = **91,555 note-refs** (the website "91,553" → new shipped figure **91,555**; cross-check:
ethiopian kepub = 43,017 inline vn-items + ~48,538 backmatter-glossary entries = 91,555). Per-edition
shipped notes = base − dry-run-filtered:

| edition | kinds | shipped notes |
|---|---|---|
| ethiopian-tewahedo | 71/72 | **91,555** (filters 0 — the superset) |
| catholic-study | 50/72 | **43,370** (91,555 − 48,185) |
| evangelical-reformed | 44/72 | **41,847** (91,555 − 49,708) |
| eastern-orthodox | 46/72 | **41,819** (91,555 − 49,736) |
| standalone-geez | 28/72 | scripture edition — no study notes (EN back-translation popups) |
| standalone-amharic | 28/72 | scripture edition — no study notes (EN back-translation popups) |

Counts from `--list` (kinds) + `build_edition.py <ed> --dry-run` (filtered asides) + base note-ref count.
Inline-vs-glossary split is mode-dependent; the headline reconciliation number is **91,555**.

> ⚠ **Phase-E note (found during the count):** `gen_website_progress.py` is NOT read-only — it regenerates
> website artifacts. It surfaced that Ge'ez **1 Kings ch 7–10** reader pages exist in source
> (`content/translations/geez-tewahedo/1ki.py`) but were never generated into `website/src/read/geez/1ki/`
> (only ch 6 present). Reverted here (wrap = no partial uncoordinated website regen); fold into Phase E's
> rebuild + redeploy.

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

**External drives E:/F: now on the Windows box (2026-06-22, user-directed — supersedes the 2026-06-16 "with Mac" note; STANDING, both lanes).** The portable **E:** and **F:** volumes (release bundles, `YHWH-v2.4-releases/`, M3/M4 handoff packs, etc.) are **mounted on Windows** (E: ~750 GB free · F: ~265 GB free). **Windows:** runs the **full 5-leg save** — `save-all.ps1`'s E:/F: `git bundle` legs are **REQUIRED again**, not optional; a missing E:/F: now means a genuinely *partial* save (fix + re-run). **Mac:** `git pull` / push to both remotes is its cross-lane sync (`dev/save_mac.sh` = 3-leg push-only; no local E:/F: bundle leg while the drives are WIN-side).

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

**WIN:** `pwsh -File save-all.ps1 -Message "…"` (seam-gated `lane_ping`; **E:/F: bundle legs REQUIRED — drives are WIN-side as of 2026-06-22**). **Mac:** `bash dev/save_mac.sh -m "…"` (commit if dirty + push origin + github). **Do not hoard** local-only commits — the other lane cannot see unpushed work. **macclaude:** mirror this block into per-box memory on next session (ACK).

**Lane sync ping (seam check).** `scripts/lane_ping.py` (shared) — cheap `git ls-remote` before pull/push so milestone pushes to protected `main` never reject. The full pull checker = `lane_ping` + `lane_watch.py --auto-pull`, run at SEAMS (not a background radar): Win `save-all.ps1 --before-push` + SessionStart `--quiet`; **Mac `dev/save_mac.sh --before-push`** (auto `git pull --rebase` if BEHIND). **Mac SessionStart ping = PENDING** — the `bootstrap-triad.sh` ping block landed in-repo 2026-06-21 but Mac must pull + re-install + ACK before it fires (→ Phase H / the Mac re-install task below); until then Mac auto-pulls only at the `save_mac.sh` seam. The user never has to say the word.

**WIN builds · Mac verifies (2026-06-19, user-directed — STANDING, both lanes).** **WIN** owns implementation (`scripts/` · `tests/` · `ci.py` · matrix builds · Kindle bisect). **Mac** owns **verify + scope** on each WIN milestone: pull → run WIN-listed verify commands → `## Mac verify (turn N)` PASS/FAIL in this file → post the next Mac scope (max 3 items) in this file. Mac **must not** dual-implement the same Kindle/pytest fix WIN is shipping. Mac **may** run targeted `pytest` + sim gates + STK poll (user uploads); Mac **must not** run full `ci.py` on HDD while WIN `ci.py` is in flight.

**Rule change parity (STANDING, both lanes):** Any edit to shared in-repo rules (LANE_HANDOFF, SESSION_STATE, CLAUDE_PROJECT_RULES, etc.) must be accompanied by a task for Mac (in this file) to: pull the change, update their per-box memory with the exact new text (diff only real OS reasons), confirm rules are identical, ACK in local memory, run bootstrap to wire, report confirmation + any diff to LANE_HANDOFF. WIN reviews Mac report and confirms both sides on same page before considering the rule change complete. This delegation is automatic in the queue/handoff system.

> **Older turns archived to `dev/archive/LANE_HANDOFF_LOG.md`** (rotated by `scripts/rotate_truth_records.py`; newest batch first).
