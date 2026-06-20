#!/usr/bin/env bash
# save_mac.sh — Mac save helper (lane-coordination v2 / crash-safe cadence 2026-06-17).
#
# STANDING: run autonomously after each coherent slice — no asking, no waiting on user input.
# Mac counterpart to save-all.ps1 (no E:/F: bundle legs). Legs: local commit (if -m) +
# push origin (GitLab) + push github (GitHub), radar-gated. See RULES §4 + lane_ping.py.
#
# Usage:
#   bash dev/save_mac.sh -m "commit message"   # commit tracked changes, then push both remotes
#   bash dev/save_mac.sh                        # no commit — just push existing local commits
#   bash dev/save_mac.sh -n                     # dry-run (radar + plan only; no commit/push)
#
# Run from anywhere; it locates the repo from its own path.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
PY="$REPO/.venv/bin/python"; [ -x "$PY" ] || PY="python3"

MSG=""; DRYRUN=0
while getopts "m:n" opt; do
  case "$opt" in
    m) MSG="$OPTARG" ;;
    n) DRYRUN=1 ;;
    *) echo "usage: save_mac.sh [-m msg] [-n]" >&2; exit 2 ;;
  esac
done

# Leg 1 — stage EVERYTHING (-A: tracked + untracked, mirroring save.ps1) and commit
# if a message was given and the tree is dirty. `git diff`/-am only see tracked files,
# so the old form silently dropped new notes/specs created during the session.
if [ -n "$MSG" ]; then
  if [ "$DRYRUN" = 1 ]; then
    if [ -z "$(git status --porcelain)" ]; then
      echo "save_mac: tree clean — nothing to commit."
    else
      echo "[dry-run] would: git add -A && git commit -m \"$MSG\" — staging:"
      git status --short
    fi
  else
    git add -A
    if git diff --cached --quiet; then
      echo "save_mac: tree clean — nothing to commit."
    else
      git commit -m "$MSG"
    fi
  fi
fi

# Post-commit: truth-record rotation (mirror save-all.ps1 so Mac saves also trim)
# STANDING: the save script is the rotation ACTOR.
echo "=== Post-commit: truth-record rotation ==="
"$PY" scripts/rotate_truth_records.py --apply || echo "  rotator exited non-zero (non-fatal for this leg)"
rotPaths=(dev/SESSION_STATE.md dev/IN_FLIGHT.md dev/LANE_HANDOFF.md dev/archive)
if git status --porcelain -- "${rotPaths[@]}" | grep -q . ; then
  git add -- "${rotPaths[@]}"
  git commit -m "chore: rotate truth records (save_mac auto; keep 2 + standing sections)" || true
else
  echo "  truth records already within entry budget"
fi

# Radar — is the other lane ahead? (exit 10 = BEHIND)
git fetch origin -q || true
set +e; "$PY" scripts/lane_ping.py --before-push; PING=$?; set -e
if [ "$PING" = 10 ]; then
  echo "lane radar: BEHIND — pulling --rebase before push."
  if [ "$DRYRUN" = 1 ]; then
    echo "[dry-run] would: git pull --rebase origin main"
  elif ! git pull --rebase origin main; then
    # Never leave the repo mid-rebase (mirrors save-all.ps1's pull-failure guard).
    git rebase --abort 2>/dev/null || true
    echo "save_mac: pull --rebase FAILED — rebase aborted; resolve by COMBINING (RULES §4), then re-run." >&2
    exit 1
  fi
fi

# Legs 2-3 — push both remotes.
if [ "$DRYRUN" = 1 ]; then
  echo "[dry-run] would: git push origin main && git push github main"
  exit 0
fi
git push origin main
git push github main

# Verify — both remotes in sync.
git fetch origin -q && git fetch github -q
AB="$(git rev-list --left-right --count origin/main...HEAD 2>/dev/null || echo '? ?')"
echo "save_mac: pushed. origin behind/ahead vs HEAD: $AB (want 0\t0). github:"
git rev-list --left-right --count github/main...HEAD 2>/dev/null || true
