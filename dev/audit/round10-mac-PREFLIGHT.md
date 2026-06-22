# Deep-audit round 10 — MAC lane PRE-FLIGHT (prepared 2026-06-22 for a FRESH session)

> **Why a fresh session:** the round-10 MAC lane is a heavy multi-agent **Opus** run (18 dims ×
> find → adversarial-verify → synthesize). The session that prepped this was context-heavy from a
> long day; the user chose to run the audit in a CLEAN session for full context + attention. This
> file is the runbook — a fresh Mac session should bootstrap, read this, and execute. Mac-runnability
> is **already verified** below (REPO, agents, dim count, model), so there's nothing to re-derive.

## 0. Pre-conditions (the bootstrap auto-pull radar handles the pull)
- Be at commit **`3ce5a40c`** (the audit-launch commit) **or later**. `git rev-parse --short HEAD`.
- WIN's full instructions: `dev/LANE_HANDOFF.md` → "▶ Deep-audit round 10 — SPLIT RUN".
- Machine quiescent (no builds/pytest competing). This lane is **read-only / model-call-bound** — it
  does NOT build epubs or run pytest (that's the WIN lane), so no disk/RAM contention on the iMac.

## 1. RUN (the exact command)
```
Workflow({scriptPath:'.claude/workflows/deep-audit.js',
          args:{lane:'mac', round:10, scope:'product', now:'2026-06-22', model:'opus'}})
```

## 2. VERIFY the startup `log` line BEFORE letting it run far (the args-propagation gate)
Expect (engine line 455):
```
deep-audit round 10 | scope=product | depth=deep | 18 dimensions | repo=/Volumes/MacHD2/yhwh-bible-platform | argsRound=10 | deferred=N
```
- **`18 dimensions`** ✓ (the MAC lane at scope=product: 21 lane dims − the 3 sweep dims = 18).
- **`repo=/Volumes/MacHD2/yhwh-bible-platform`** ✓ (auto-picked from `lane='mac'`).
- **`scope=product`**, **`round 10`**, **`argsRound=10`** ✓.

**If the count is NOT 18** (e.g. 24 = lane didn't apply, or 21 = scope=all leaked) → **args didn't
propagate.** Fallback (memory `reference_deep_audit_tool`, never commit the flip):
1. Edit `.claude/workflows/deep-audit.js` **line 20**: `const LANE = args?.lane ?? 'all'` → `const LANE = 'mac'`.
2. (Optional, for the date stamp) **line 38**: `const NOW = args?.now ?? '2026-06-21'` → `'2026-06-22'`.
3. Relaunch the Workflow; confirm `18 dimensions` + the Mac repo path.
4. **`git checkout -- .claude/workflows/deep-audit.js`** after — the committed default stays `'all'`. NEVER commit the flip.

**Mac-runnability — ALREADY VERIFIED (no action needed unless the count check fails):**
- `lane='mac'` → REPO = `/Volumes/MacHD2/yhwh-bible-platform` (line 23) + agents = `general-purpose`/`Plan`/`Explore` (line 30) — all available on this Mac (the feature-dev:* agents the WIN lane uses are NOT required here).
- Model defaults to **Opus** (line 468, 2026-06-22 user directive: audits run on the strongest model) even if `model` arg doesn't propagate.

## 3. WRITE the findings (from the returned result object) — into THIS dir (`dev/audit/`)
- `round10-mac-survivors.json` → `{lane:'mac', round:10, now:'2026-06-22', counts:<result.counts>, survivors:<result.survivors>, completeness:<result.completeness>}`
- `round10-mac-plan.md` → the returned `fixesPlanMarkdown` (append the `completeness` gaps at the end for the next round).

## 4. SAVE + ACK
- `bash dev/save_mac.sh -m "audit(mac): deep-audit round-10 MAC-lane findings → dev/audit/"`
- Append a `### ✅ MAC AUDIT round-10 DONE` block in `dev/LANE_HANDOFF.md` (under the SPLIT-RUN section)
  with: survivor count · severity breakdown · count of any **UNVERIFIED** (empty-panel) survivors flagged
  for manual triage · the top 3 completeness gaps.

## 5. After
Mac is **findings-only** this round — WIN remediates (merges both lanes + the structural pass into
`dev/audit/round10-remediation.md`, TDD + byte-stability + commit-per-fix). Do **not** dual-implement
fixes. After WIN pushes fixes, Mac **verifies** per the standing WIN-builds · Mac-verifies cadence.

— Prep status @ 2026-06-22: dev/audit/ created · machine quiescent · repo clean @ `3ce5a40c` · pushed.
