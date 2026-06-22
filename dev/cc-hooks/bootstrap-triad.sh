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

RAM hygiene (Mac, constrained box -- LOCAL OS-specific override, NOT Windows' PROTECT/
KILL list): keep ONE GUI app open at a time; end-task Chrome/Kindle between slices; run
the browser MCP OFF while VS Code is open (guard #6); free any leaked python/java before
heavy builds. See RULES section 0 + memory feedback_session_start_ram.
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

# --- Memory self-maintenance (local, non-fatal): surface memory drift so it gets
# reconciled. Read-only audit; prints ONLY when a real (warn) issue exists. Mirrors the
# .ps1 block + the automate_claude_operating_doctrine self-maintenance layer. Seam check
# (runs once at session start), NOT a background watcher. See dev/cc-hooks/memory_hygiene.py
# + the memory-reconcile workflow. ---
PYM="$REPO/.venv/bin/python"; [ -x "$PYM" ] || PYM="python3"
HYG="$REPO/dev/cc-hooks/memory_hygiene.py"
if [ -f "$HYG" ]; then
    mem_out="$("$PYM" "$HYG" audit --quiet 2>/dev/null)"
    if [ -n "$mem_out" ]; then
        echo ""
        echo "----- MEMORY HYGIENE (drift detected -- reconcile when convenient) -----"
        echo "$mem_out"
        echo "Full report: .venv/bin/python dev/cc-hooks/memory_hygiene.py audit  |  Deep sweep: Workflow memory-reconcile"
    fi
fi

# --- Lane sync RADAR (seam check + AUTO-PULL): ONE poll cycle that (a) detects whether the
# OTHER lane (mac<->win) pushed while we were away or handed us a baton, AND (b) per the STANDING
# "just pull, never ask" directive AUTO-PULLS (--rebase onto origin/main; auto-commits a dirty
# tree FIRST when a pull is needed) so the user never types "pull". Multi-remote-safe (origin +
# github); read-only no-op when CLEAR; non-fatal. This is the session-start SEAM, NOT a persistent
# background watcher (the loop machinery stays removed). Supersedes the old report-only lane_ping
# --quiet block here; lane_watch wraps lane_ping + lane_handoff incoming + the auto-pull.
# See scripts/lane_watch.py (`check(auto_pull=True)`) + RULES s4 (auto-pull-on-BEHIND). ---
PY="$REPO/.venv/bin/python"; [ -x "$PY" ] || PY="python3"
if [ -f "$REPO/scripts/lane_watch.py" ]; then
    echo ""
    echo "----- LANE SYNC RADAR (seam check + auto-pull) -----"
    "$PY" "$REPO/scripts/lane_watch.py" --once --auto-pull 2>/dev/null
fi
