#!/usr/bin/env bash
# Kindle sim pack — structural gates (verify_kindle_safe + optional m4b). No Previewer.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO"
if [[ -x "$REPO/.venv/bin/python" ]]; then
  PY="$REPO/.venv/bin/python"
elif command -v py >/dev/null 2>&1; then
  PY="py -3"
else
  PY="python3"
fi
ARTIFACT="${1:?usage: gate.sh <path/to.epub>}"
if [[ -n "${M4B:-}" ]]; then
  exec $PY -m scripts.reader_sim --gate kindle --artifact "$ARTIFACT" --m4b
fi
exec $PY -m scripts.reader_sim --gate kindle --artifact "$ARTIFACT"