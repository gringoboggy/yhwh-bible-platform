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

if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "PyInstaller not found. Installing into the active Python..."
    python3 -m pip install --user pyinstaller
fi

echo "Cleaning prior build artifacts..."
rm -rf build/ dist/

echo "Building YHWH desktop binary..."
python3 -m PyInstaller dev/launcher.spec --noconfirm "$@"

echo
echo "Build complete:"
ls -lh dist/ | tail -n +2
echo
echo "Run: ./dist/YHWH    (or open dist/YHWH.app on macOS)"
