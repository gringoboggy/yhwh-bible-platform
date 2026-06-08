# Round-6 split deep-audit — plan (2026-06-08)

**Status:** READY. Engine updated + syntax-checked. Runs on the user's go, one fresh
session per box. **FINDINGS-ONLY — stop before fixes** (user marching order
2026-06-08: "neither lane stops until the auditor is complete, BEFORE FIXES").

## Why this round

v0.0.3 shipped (full-notes Ethiopian Bible ~91.5K notes; Win/Linux/macOS desktop
builders; live website). Round 5 (2026-06-05) predates a lot of that surface. Round 6
is the **post-v0.0.3 / v1.0.0-readiness sweep** — make the auditor current, run it
split across both machines to convergence, produce ONE merged findings plan, then
STOP. Fixes are a separate, later go.

## What changed in the engine (already done, committed)

`.claude/workflows/deep-audit.js` + `deep-audit-merge.js`:

1. **`ROUND = 6`, `NOW = '2026-06-08'`.**
2. **Cross-lane parity BAKED IN (fixes the round-5 15×-Mac-failure).** `LANE` is now the
   single in-file knob: flipping it auto-selects the right `REPO` path *and* the right
   sub-agent types for that box. The Mac no longer needs 3 separate local edits.
   - `REPO_BY_LANE`: win = `C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4`,
     mac = `/Volumes/MacHD2/yhwh-bible-platform`.
   - `AGENTS_BY_LANE`: win uses `feature-dev:code-reviewer` / `feature-dev:code-architect`;
     mac maps those to `general-purpose` / `Plan` (the Mac lacks `feature-dev:*`). Guard
     dims use `Explore` on both.
3. **Two NEW dimensions** (no prior dim covered them):
   - `dist-packaging` — the desktop builders + release pipeline (launcher spec, Azure
     signing, dmg notarization, AppImage CI, SHA256SUMS merge): version drift,
     stale-artifact ships ("deploy" = rebuild-then-publish), secret leakage, checksum
     correctness. READ-ONLY (does not run builds).
   - `website-deploy` — `website/**` + `gen_website_progress.py`: the "sources-not-missing"
     display guard, the EN-flag ≥50-rows rule, the 83-book `_SUPERSET_EXCLUDE`, broken
     download links/checksums, the 83-count consistency across page+meta+social-card,
     `build.mjs` injection. READ-ONLY.
4. **`rx-surfaces` extended** to the v0.0.3 post-passes (`apply_superscriptions`,
   `apply_appendix_demotion_and_renumber` 87→83 gapless renumber on canon-filtered
   editions, cross-verse byte-identical dedup, alt-book-name removal) and to the
   lang-greek / topic-torrey / topic-nave re-ingests (not just dict-easton).
5. **New DEFERRED-BY-DESIGN** so they're not re-litigated: 83-vs-87 is intended; ONE
   Bible (standalones are future); the ~205 epubcheck-clean orphan aes asides in 028;
   the title-page misalignment needs render-not-blind-CSS (the CSS is already centered).
6. **Doctrine constraints in the synth:** local-commit-per-fix / full-sync-at-milestone;
   findings-only.

## The split (by RESOURCE, so it truly parallelizes)

The two lanes hit DIFFERENT bottlenecks → real concurrency, not contention.

| Lane | Bottleneck | Dimensions | Notes |
|---|---|---|---|
| 🪟 **win (N95)** | local disk / CPU (pytest + builds) | `tests-run`, `opt-build`, `byte-stability`, `rx-surfaces` | the "takes forever" half — runs the full suite incl. the ~205s byte-stability gate + the slow matrix/filesplit tests, plus eth + catholic-study builds + epubcheck. SSD box. |
| 🖥️ **mac (iMac)** | model calls (read-only review) | `correctness`, `security`, `code-debt`, `tests`, `docs`, `data-validity`, `concurrency-caching`, `cross-module`, `marathon-boundary`, `dist-packaging`, `website-deploy`, `opt-vision`, `opt-ingest`, `opt-render` | 14 disk-light dims; no build/test wait. HDD-bound box is fine here. |

Mac's 14 light dims ≈ Win's 4 heavy dims in wall-clock → **Mac will usually finish
first** → see the **Meantime backlog** below.

## Run protocol (one fresh session per box, on the user's go)

Both boxes:
1. `git pull --rebase origin main` (the lane ping / `save-all` does this; land on the
   committed engine). Confirm the cross-lane parity bake is present (this plan's commit).
2. Edit `.claude/workflows/deep-audit.js` **LOCALLY, do NOT commit** — set `const LANE`:
   **mac →** `const LANE = 'mac'` · **win →** `const LANE = 'win'`. (That ONE line now
   also fixes REPO + agent types — nothing else to edit.)
3. `Workflow({scriptPath: "<repo>/.claude/workflows/deep-audit.js"})`. **Confirm the
   startup-log dim count:** mac → **14**, win → **4**. If it echoes 18, the LANE edit
   didn't take — fix before letting it run.
4. **Cost control (the $80/hr lesson):** finders + verifiers are pinned to **sonnet**
   in-engine; the 4-core N95 cap = 2 concurrent. Do NOT bump to Opus or add finders.
   Keep sleep/hibernate OFF, terminal open (mint-10 died on a manual shutdown).
5. **Output:** `JSON.parse(<result file>).result.survivors`.
   - **mac** writes its survivors to `_audit-split/findings-mac.json`, commits to branch
     `lane-transfer/audit`, pushes. (That push IS mac's audit-completion milestone.)
   - **win** keeps its survivors locally; when BOTH are in hand, win runs the merge.

## Merge (on the N95)

1. Paste `WIN_SURVIVORS` (win's `result.survivors`) and `MAC_SURVIVORS` (pull
   `lane-transfer/audit` → `findings-mac.json` `.survivors`) into
   `.claude/workflows/deep-audit-merge.js`.
2. `Workflow({scriptPath: ".../deep-audit-merge.js"})` → write `result.fixesPlanMarkdown`
   to `docs/superpowers/notes/2026-06-08-round6-split-audit-findings.md`.
3. Delete `lane-transfer/audit`. **STOP — present the findings. Do NOT start fixes.**
4. Milestone save (5-leg) of the findings doc.

## ▶ Mac MEANTIME BACKLOG — what to do when your 14 dims finish and win is still grinding

You will almost certainly finish before the win lane. **Do NOT idle and do NOT start
fixes** (marching order). Work this list top-to-bottom — all **read-only / local-commit
only / file-disjoint from win's build path / cheap** (no new heavy Workflows; prefer
solo-Claude). Push nothing until the merge milestone.

1. **Strengthen your own audit lane first.** Re-verify any **UNVERIFIED** survivors
   (empty-skeptic-panel-after-retry) from your run with a fresh adversarial skeptic —
   these are the round-4 false-negative risk. Confirm or drop each.
2. **Deepen the two brand-new dims** (`dist-packaging`, `website-deploy`) — they're
   new this round so likely under-covered. Re-run just those two with the second
   `angles` perspective / an extra finder, and fold any new survivors into
   `findings-mac.json` before you push it.
3. **Title-page misalignment — the render-then-diagnose pass** (the recurring Kobo/Apple
   item the engine refuses to "blind re-center"). Build is win's job, but you can
   inspect a *already-built* EPUB if one exists, or render the title-page HTML+CSS
   structure (Chrome/Playwright MCP) to PIN the one off element. Write findings to
   `docs/superpowers/notes/2026-06-08-title-page-render-diagnosis.md`. Read-only.
4. **Website launch-readiness (read-only, disjoint repo surface).** Lighthouse / a11y /
   broken-link / OG-meta pass on the live site via Chrome MCP → append to a notes file.
   Does not touch win's `scripts/`/`epub_working/`/`content/`.
5. **Mac-side memory + doc hygiene.** Run `py -3 dev/cc-hooks/memory_hygiene.py audit`
   (cheap, read-only) and note dead links / drift; sanity-check MATRIX_MAP / REPO_MAP
   currency vs the v0.0.3 tree. Local notes only.
6. **Mirror-parity check.** Confirm your Mac out-of-repo halves are done (the
   `session-operating-doctrine` + `reference_save` + `reference_lane_ping` memories; the
   SessionStart-hook ping block; the Mac save-path `--before-push` wiring) and ACK in the
   handoff. (This is from turn 23 — do it first if not already.)

If you exhaust this list and win is *still* running, report "mac lane idle, win heavy
lane still running" in the handoff and wait — do not invent new scope or start fixes.

## Constraints (carried)

Never touch the marathon core (`build_standalone.py`, `core/manuscript_*`, GAPS/, the
patrologia sources); 9 KJV editions byte-stable; additive schema; atomic writes;
single-user local app (no CSRF/rate-limit/hosting findings); 83 books (never 87); ONE
Bible. **Save cadence:** local-commit during the run; full 5-leg sync only at the
audit-completion / merge milestone. **Findings-only — stop before fixes.**
