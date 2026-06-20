# Cross-Lane Rules Parity & Machine Optimization Plan

**Owner:** Both lanes (coordinated via LANE_HANDOFF + MAC_WORK_QUEUE)  
**Goal:** Windows and Mac are "exactly on the same page" for every rule.  
- In-repo (git) rules are identical.  
- Out-of-repo (per-box memory, hooks, local configs) are identical in content except where genuine OS differences require divergence.  
- All divergences are explicitly documented, minimal, and optimized for the specific machine.  
- The system is self-maintaining on future rule changes.

This plan is activated when Mac sends its next batch of updates (via pull / incoming handoff). WIN will receive, audit, harmonize, and send back required Mac-side changes.

## 1. Definitions

- **Repo rules (in-repo):** Everything tracked in git that defines behavior, process, or mental models. Must be 100% identical on both sides (or have OS-variant files that are semantically equivalent).
  - Core: `dev/CLAUDE_PROJECT_RULES.md`, `dev/SESSION_PLAYBOOK.md`, `dev/PLAN_*.md`, `dev/LANE_HANDOFF.md` (task sections may differ), `dev/MAC_WORK_QUEUE.md`, `dev/REPO_MAP.md`, `dev/MATRIX_MAP.md`, checklists, etc.
  - Scripts: `dev/cc-hooks/*` (both .ps1 + .sh), `dev/start_session_radars*`, `dev/save_mac.sh`, `save-all.ps1`, `dev/install_*`, `memory_hygiene.py`, lint scripts, etc.
  - Markers: `dev/.lane`

- **Out-of-repo rules (per-box):** Local to each machine, not in git.
  - Per-box memory (`~/.claude/.../memory/` + project memory files).
  - Hook wiring (`.claude/settings.json` or `settings.local.json` on each machine).
  - Local env (PYTHON paths, UTF8 settings, drive mappings, TMPDIR, conda vs system python, etc.).
  - Machine facts recorded in memory (RAM limits, plugin availability, previous ACKs of rules).

- **Allowed divergences:** Only where OS fundamentally differs (shell, paths, process names, interpreter invocation, build toolchain, low-level env). Never for convenience or "I like it this way."

## 2. Audit Categories (do on receipt of Mac update)

### 2.1 In-Repo Shared Documents
- Compare all non-OS-variant .md files byte-for-byte or via semantic review.
- Ensure any recent changes from either lane have been mirrored.
- Produce unified version if drift exists.

### 2.2 In-Repo OS-Adapter Scripts
- `bootstrap-triad.ps1` vs `bootstrap-triad.sh`
- `start_session_radars.ps1` vs `start_session_radars_mac.sh`
- Save commands (`save-all.ps1` + `save.ps1` vs `save_mac.sh`)
- Installers (`install_cc_hooks.ps1` vs manual Mac wiring)
- Any other dual scripts.

Action: Make structure, comments, and behavior as parallel as possible. Document every OS difference in a "OS Divergences" table (see §5).

### 2.3 Bootstrap, Radars & Session Lifecycle
- Verify both sides:
  - Read the triad first (CLAUDE_PROJECT_RULES → SESSION_STATE → PLAN).
  - Start **both** radars (`lane_watch` + `agent_idle_radar`).
  - Perform RAM hygiene + env health.
  - Enforce lane identity via `dev/.lane`.
- Ensure SessionStart hooks (installed per-box) produce equivalent user-visible behavior.

### 2.4 Out-of-Repo Per-Box Memory
- Each lane exports/summarizes its current memory index (key facts, ACKs of rules, machine env).
- Cross-check against canonical rules.
- Mirror any missing canonical rules + add machine-specific notes (e.g., "Windows 16 GB: heavy trio sequential", "Mac 8 GB: no concurrent browser MCP + VSCode").
- Run `dev/cc-hooks/memory_hygiene.py audit` + `propose-prune` on both sides.
- ACK in local memory: "Rules parity sync <date> — all repo + out-of-repo aligned per CROSS_LANE_RULES_PARITY_PLAN.md"

### 2.5 Environment & Tooling
- Python: Win `py -3` / full 3.14 path vs Mac `.venv/bin/python` (uv).
- UTF8: User env var on Win, export on Mac.
- Save cadence: `save-all.ps1` (with E:/F: bundles) vs `bash dev/save_mac.sh`.
- Bundles: Win mandatory to E:/F:; Mac defers or uses different transport.
- RAM / heavy work: Explicit per-machine budgets and process kill lists.
- Plugins/MCP/agents: Core set identical; note Mac limitations (fewer sub-agents, playwright restrictions due to RAM).
- Git: Same remotes (`origin`=GitLab, `github`), protected main, no force-push.

### 2.6 Machine Optimizations (Documented Only)
Create/maintain a single table of approved differences (see §5). Examples already in PLAYBOOK:
- Windows N95 16 GB full setup.
- Mac 2017 iMac 8 GB (STK user-upload + agent poll only, no heavy concurrent, etc.).

## 3. Execution Steps (when Mac's update arrives)

1. **Receive**  
   - Git pull (hope checker auto-triggers on behind/incoming).  
   - Review new handoff / MAC_WORK_QUEUE content from Mac.  
   - Ask Mac (via next handoff if needed) for: current memory summary, `~/.claude/settings*` excerpts (sanitized), list of locally-mirrored rules.

2. **Audit** (WIN leads this pass)  
   - Run side-by-side on all categories above.  
   - Use `diff`, `git diff`, manual review of critical files.  
   - Flag every divergence.

3. **Harmonize**  
   - For in-repo: edit to identical (or proper OS variants). Commit locally.  
   - For out-of-repo: produce "canonical + machine notes" text for each side.  
   - Update this plan + add "OS Divergences" table to CLAUDE_PROJECT_RULES.md or a new dedicated section.

4. **Send to Mac**  
   - Update LANE_HANDOFF with:
     - Summary of audit findings.
     - Exact files/sections Mac must change on their side.
     - Text to paste into their per-box memory.
   - Use `/handoff` or direct assignment in MAC_WORK_QUEUE if appropriate.
   - WIN applies its side changes in the same turn.

5. **Both sides verify**  
   - Fresh session on each machine runs bootstrap + confirms triad + radars + memory hygiene clean.
   - Run any new "rules parity" light check if added.

6. **Close the loop**  
   - Both lanes ACK in their local memory: "Cross-lane rules parity complete <date>. See dev/CROSS_LANE_RULES_PARITY_PLAN.md".
   - Record in SESSION_STATE / CHANGELOG if this was a notable arc.

## 4. Ongoing Maintenance (after this sync)

- Any edit to a canonical rule file must be pulled by the other lane before the next cross-lane handoff.
- On every handoff or major rule change, the receiving lane runs a quick "parity spot-check" (at minimum: triad files + bootstrap scripts + memory hygiene audit).
- Bootstrap hooks can be enhanced later to warn if local memory is missing a recent rule ACK.
- New machine or fresh account: follow "Fresh-machine setup" in cc-hooks/README + this plan.

## 5. OS Divergences Matrix (living document — keep minimal)

(Will be populated/expanded during the audit. Current known examples from PLAYBOOK and rules:)

| Area                  | Windows (N95)                          | Mac (2017 iMac)                          | Reason / Optimization                  |
|-----------------------|----------------------------------------|------------------------------------------|----------------------------------------|
| Python                | `py -3` or full 3.14 path             | `.venv/bin/python` (uv)                 | uv env on Mac; Store stub on Win      |
| Milestone save        | `pwsh -File save-all.ps1 -Message "..."` | `bash dev/save_mac.sh -m "..."`        | E:/F: bundles only on Win             |
| RAM hygiene           | Detailed Win process kill list (16 GB) | Very strict (8 GB); no browser MCP + VSCode | Hardware difference                   |
| Hook wiring           | `install_cc_hooks.ps1` + repo-parent .claude | Manual in ~/.claude/settings.json      | Claude Code per-OS conventions        |
| lane_watch            | `-AssignMac`                           | plain                                  | WIN assigns Mac queue                 |
| Bundles / backups     | E: + F: required                       | Deferred / different transport          | External drives currently with Mac    |
| ... (add more during audit) | ... | ... | ... |

Only add a row when a real, unavoidable OS difference exists. Every row must have a comment in the corresponding script or doc.

## 6. Deliverables from this sync

- `dev/CROSS_LANE_RULES_PARITY_PLAN.md` (this file) — living.
- Updated `dev/CLAUDE_PROJECT_RULES.md` (if new parity guard or matrix added).
- Synced `dev/cc-hooks/bootstrap-triad.{ps1,sh}` and related scripts.
- Both per-box memories up to date + ACKed.
- Clean LANE_HANDOFF entry closing the parity loop.

## 7. Activation

This plan is live. Mac: when you pull WIN's latest and see this file + handoff note, begin execution on your side (capture your current state, apply changes WIN requests, send your side back). WIN will do the symmetric review on receipt of your bundle.

**Most logical sequence:** receive → audit both sides → harmonize in-repo first → per-box memories → test bootstrap on fresh sessions → document + ACK → close via handoff.

---

*Drafted on Windows (turn ~146 context). To be shared immediately with Mac via next handoff / MAC_WORK_QUEUE update.*