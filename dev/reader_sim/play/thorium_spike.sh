#!/usr/bin/env bash
# Play/Apple Thorium render spike — Mac or WIN with Thorium + Chrome DevTools MCP.
#
# Agent steps (document pass/fail in sim layer):
#   1. Open artifact in Thorium (file:// or drag-drop)
#   2. Navigate Gen 1:1 — tap vn-link — assert popup text non-empty
#   3. Sample Hebrew/Greek verse — assert no tofu in rendered text
#   4. Play only: note <details> ToC stuck closed (expected fail)
#
# Usage: bash dev/reader_sim/play/thorium_spike.sh <path/to.epub> [apple|play]
set -euo pipefail
ARTIFACT="${1:?usage: thorium_spike.sh <epub> [apple|play]}"
PROFILE="${2:-play}"
echo "Thorium spike (STUB) profile=$PROFILE artifact=$ARTIFACT"
echo "Wire Chrome DevTools MCP navigate + snapshot assertions here."
exit 2