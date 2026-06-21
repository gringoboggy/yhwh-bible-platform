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
echo "  Lane rule (v2): mode=parallel -> file-disjoint, BOTH lanes push their own milestones;"
echo "  only the TRUTH_OWNER edits SESSION_STATE/IN_FLIGHT/CHANGELOG (see LANE_HANDOFF frontmatter)."
echo "==================================================================="

cat <<'EOF'
================ YHWH PROJECT BOOTSTRAP (mac lane) -- DO THIS FIRST ================
Read the triad in order:
  1. dev/CLAUDE_PROJECT_RULES.md   (rules + conventions + mental models)
  2. dev/SESSION_STATE.md          (latest snapshot: shipped / next / test count)
  3. dev/PLAN_2026-05-29-roadmap.md (master forward sequence)

This is the 2nd lane (Mac). mode=parallel (default): keep files DISJOINT from the
Windows lane's active work; BOTH lanes commit + push their own milestones; only the
TRUTH_OWNER edits SESSION_STATE/IN_FLIGHT/CHANGELOG (see LANE_HANDOFF frontmatter).
Use /resume to pick up THIS lane's task (parallel: do NOT stop when truth_owner !=
self), /handoff to transfer truth-ownership, /sync for a milestone push.
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

# --- Lane sync PING (seam check; local, non-fatal): cheap `git ls-remote` so a fresh
# session learns immediately if the OTHER lane (mac<->win) pushed while it was away.
# Prints ONLY when BEHIND (pull --rebase before starting / any milestone push). Read-only
# + bandwidth-cheap; run at the session-start SEAM, NOT a persistent background radar.
# See scripts/lane_ping.py + RULES s4. ---
PY="$REPO/.venv/bin/python"; [ -x "$PY" ] || PY="python3"
if [ -f "$REPO/scripts/lane_ping.py" ]; then
    ping_out="$("$PY" "$REPO/scripts/lane_ping.py" --quiet 2>/dev/null)"
    if [ -n "$ping_out" ]; then
        echo ""
        echo "----- LANE SYNC PING (seam check) -----"
        echo "$ping_out"
    fi
fi
