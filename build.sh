#!/usr/bin/env bash
# Reference EPUB build pipeline. Run from inside the working EPUB directory.
# Usage:  cd <working-copy> && ../build.sh OUT.epub
set -e
OUT="${1:-Ethiopian_Bible.epub}"
[ -f mimetype ] || { echo "ERROR: run from inside EPUB working dir (no mimetype found)"; exit 1; }

# CRITICAL: mimetype must be FIRST and uncompressed (store-only)
zip -X0 "../$OUT" mimetype > /dev/null
# Everything else compressed
zip -Xr9 "../$OUT" . -x mimetype > /dev/null

echo "Built: ../$OUT ($(du -h "../$OUT" | cut -f1))"
