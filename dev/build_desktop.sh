#!/usr/bin/env bash
# Phase θ.1 — POSIX desktop-binary build wrapper.
#
# Wraps `pyinstaller dev/launcher.spec` with sanity checks:
#   1. PyInstaller is installed (install if missing).
#   2. Run from the repo root so SPECPATH resolves correctly.
#   3. Clean prior build artifacts (PyInstaller's cache lives in
#      build/ and dist/ at the working directory).
#
# Usage:
#     ./dev/build_desktop.sh                # production build
#     ./dev/build_desktop.sh --debug        # console=True for stack traces
#
# Output: dist/YHWH (Linux) / dist/YHWH.app (macOS).
#
# Windows users: see dev/build_desktop.cmd for the equivalent.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Resolve the Python that carries the project + build deps. Prefer the
# repo venv — on macOS bare `python3` is the system 3.9, which lacks
# PyInstaller and the app's deps. Override explicitly with PYTHON=… .
PYBIN="${PYTHON:-}"
if [[ -z "$PYBIN" ]]; then
    if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
        PYBIN="$REPO_ROOT/.venv/bin/python"
    else
        PYBIN="python3"
    fi
fi

if ! "$PYBIN" -c "import PyInstaller" >/dev/null 2>&1; then
    echo "ERROR: PyInstaller is not installed in $PYBIN." >&2
    echo "       It is a declared build dependency — install it with:" >&2
    echo "           $PYBIN -m pip install -r requirements-dev.txt" >&2
    exit 1
fi

echo "Cleaning prior build artifacts..."
rm -rf build/ dist/

echo "Building YHWH desktop binary (via $PYBIN)..."
"$PYBIN" -m PyInstaller dev/launcher.spec --noconfirm "$@"

echo
echo "Build complete:"
ls -lh dist/ | tail -n +2
echo
echo "Run: ./dist/YHWH    (or open dist/YHWH.app on macOS)"
