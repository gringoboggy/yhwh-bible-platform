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
# Non-fatal throughout — never breaks session start.
set +e

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
==================================================================================
EOF

# repo = two levels up from this script's dir (dev/cc-hooks -> repo)
SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SELF/../.." && pwd)"

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
