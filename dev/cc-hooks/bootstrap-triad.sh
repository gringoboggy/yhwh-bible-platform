#!/usr/bin/env bash
# Mac-lane SessionStart bootstrap — mirror of bootstrap-triad.ps1.
#
# WIRING (Mac, one-time): the shared .claude/settings.json stays empty {};
# each machine configures its own SessionStart hook in its PER-MACHINE local
# settings. On the Mac, add to ~/.claude/settings.json (or the project
# .claude/settings.local.json, which is gitignored) a SessionStart hook whose
# command runs:  bash "<repo>/dev/cc-hooks/bootstrap-triad.sh"
# Make it executable once:  chmod +x dev/cc-hooks/bootstrap-triad.sh
#
# lane_handoff.py is pure stdlib (no third-party deps) so any python3 works.
# bash 3.2-safe (macOS default) — no bash-4 features. Non-fatal throughout.
set +e

# repo = two levels up from this script's dir (dev/cc-hooks -> repo)
SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SELF/../.." && pwd)"

# ---------------------------------------------------------------------------
# LANE IDENTITY -- which Claude am I? (Mac vs Windows). Derived, not assumed:
#   dev/.lane  = authoritative per-machine marker (gitignored)
#   uname      = OS cross-check
# This file is the MAC bootstrap, so the expected lane is "mac"; warn on any
# mismatch so a misconfigured machine is caught before it pushes/hands off.
# ---------------------------------------------------------------------------
SCRIPT_LANE="mac"
OS="$(uname -s 2>/dev/null)"
LANE=""
[ -f "$REPO/dev/.lane" ] && LANE="$(tr -d '[:space:]' < "$REPO/dev/.lane")"
LANE_EFF="${LANE:-$SCRIPT_LANE}"
LANE_UP="$(printf '%s' "$LANE_EFF" | tr '[:lower:]' '[:upper:]')"

echo "==================== LANE IDENTITY -- WHO AM I? ===================="
echo "  >>> You are ${LANE_UP} CLAUDE  (dev/.lane='${LANE:-<missing>}', uname=${OS:-?})"
if [ -z "$LANE" ]; then
  echo "  note: dev/.lane missing -> assuming this machine is the ${SCRIPT_LANE} lane."
  echo "        create it once with:  printf '%s' '${SCRIPT_LANE}' > dev/.lane"
elif [ "$LANE" != "$SCRIPT_LANE" ]; then
  echo "  !! MISMATCH: this is the MAC bootstrap but dev/.lane says '${LANE}'."
  echo "     Confirm which lane you really are BEFORE pushing or handing off."
fi
[ -n "$OS" ] && [ "$OS" != "Darwin" ] && \
  echo "  !! NOTE: uname='${OS}' (expected 'Darwin' for the Mac lane)."
echo "  Baton rule: only the HOLDER pushes + edits SESSION_STATE/IN_FLIGHT/CHANGELOG."
echo "==================================================================="

cat <<'EOF'
================ YHWH PROJECT BOOTSTRAP (mac lane) -- DO THIS FIRST ================
Read the triad in order:
  1. dev/CLAUDE_PROJECT_RULES.md   (rules + conventions + mental models)
  2. dev/SESSION_STATE.md          (latest snapshot: shipped / next / test count)
  3. dev/PLAN_2026-05-29-roadmap.md (master forward sequence)

This is the 2nd lane (Mac). Keep files DISJOINT from the Windows lane's active
work. Baton rule: only the HOLDER pushes + edits SESSION_STATE/IN_FLIGHT/
CHANGELOG this turn. Use /resume to pick up an incoming baton, /handoff to pass
it, /sync for mid-turn durability.

DUAL RADARS (STANDING -- both ON every session, bootstrap auto-starts them):
  1. lane_watch        -- cross-lane push/handoff (15s — faster for critical cross-lane rule propagation)
  2. agent_idle_radar  -- never wait for user input; surface next work (120s)
  If either is not running: bash dev/start_session_radars_mac.sh
  Backlog: dev/AGENT_WORK_BACKLOG.md · python3 scripts/agent_idle_radar.py --next
  Strategic replan ping: --replan when due. Checklist: dev/STRATEGIC_REPLAN_CHECKLIST.md
==================================================================================
EOF

# --- Env health (read-only): Claude Code version + plugins. Updates apply ONLY
# on user OK (RULES section 0). MCP is NOT auto-listed: `claude mcp list` health-
# checks by LAUNCHING each server (e.g. the Playwright/Chrome MCP) -- run it
# manually to verify. `claude --version`/`plugin list` don't start a session, so
# no hook recursion. ---
echo ""
echo "==================== ENV HEALTH ===================="
echo "  Claude Code: $(claude --version 2>/dev/null | head -1)"
echo "  Plugins:"
claude plugin list 2>/dev/null | sed 's/^/    /' | head -20
echo "  updates -> apply Claude Code / plugin updates only on user OK"
echo "  MCP     -> run 'claude mcp list' to verify servers (not auto-run: it launches them)"
echo "==================================================="

# --- Lane-handoff baton incoming check (read-only fetch + check; prints only
# when an incoming baton is pending) ---
if [ -f "$REPO/scripts/lane_handoff.py" ]; then
    git -C "$REPO" fetch origin --quiet 2>/dev/null
    banner="$(python3 "$REPO/scripts/lane_handoff.py" incoming 2>/dev/null)"
    if [ $? -eq 0 ] && [ -n "$banner" ]; then
        echo ""
        echo "$banner"
        echo "Run /resume to pull + combine the incoming work."
    fi
fi

# --- Dual session radars (STANDING, non-fatal): lane_watch + agent_idle_radar.
# Both MUST run on every session; bootstrap starts them idempotently in background.
# lane_watch is started with --auto-pull to literally enforce the STANDING
# auto-pull rule (user never says "pull" when behind + clean). See guard #8 in RULES.
if [ -f "$REPO/dev/start_session_radars_mac.sh" ]; then
    bash "$REPO/dev/start_session_radars_mac.sh" 2>/dev/null
fi

# --- Self-gov watcher bootstrap for fresh sessions (STANDING, non-fatal):
# Ensures fresh session (Mac or WIN) auto-starts the full self-gov/automation system.
# Radars started above.
echo ""
echo "=== FRESH SESSION SELF-GOV WATCHER BOOTSTRAP (STANDING) ==="
echo "  - Start persistent monitor tool on dev/.agent_idle_radar.log (for visibility of surfaced tasks)."
echo "  - Run initial python3 scripts/agent_idle_radar.py --next (or equiv) to surface top self-gov protocol tasks from watcher (P01 NEVER-STOP: chain --next + bg verif + Mac block; after Mac update continue next logical. P02 CheckInOnMacAgent: append full Mac verify post-sig; update IN_FLIGHT. P02 RelaxedAuditAgent more often: D + kr2 after 5+ commits. Plus rotate, re-cut, etc.)."
echo "  - Follow the surfaced tasks to drive self-gov without idle (NEVER-STOP, Mac check-ins via blocks, relaxed/deep audits, rotate, etc.)."
echo "  - Read LANE_HANDOFF for full current operational rules (STANDING, AUDIT PROTOCOL, watcher with tasks+watchers lists, cross-audit, Mac prep always)."
echo "  - Bootstrap-triad updated to explicitly instruct the above on fresh."
echo "============================================================"
