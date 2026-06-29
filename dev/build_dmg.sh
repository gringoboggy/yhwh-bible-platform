#!/usr/bin/env bash
# Phase θ.4 — macOS DMG installer wrapper.
#
# Wraps `dist/YHWH.app` (produced by `dev/build_desktop.sh` →
# `pyinstaller dev/launcher.spec`) into a drag-to-Applications DMG
# using macOS's built-in `hdiutil` — no third-party dependency.
#
# Signing is opt-in via env vars; unsigned DMGs build fine for
# personal / testing use, but Gatekeeper will warn end-users on
# first launch unless the .app is signed AND notarized.
#
# Required tools (all macOS-native):
#   - hdiutil (creates DMG)
#   - codesign (only when CODESIGN_IDENTITY is set)
#   - xcrun notarytool (only when NOTARIZE_KEYCHAIN_PROFILE is set)
#
# Usage (unsigned):
#     ./dev/build_dmg.sh
#
# Usage (signed + notarized — needs Apple Developer ID):
#     export CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"
#     export NOTARIZE_KEYCHAIN_PROFILE="AC_PROFILE"   # see `xcrun notarytool store-credentials`
#     ./dev/build_dmg.sh
#
# Output: dist/YHWH-<version>.dmg

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "ERROR: build_dmg.sh must run on macOS (uname -s = $(uname -s))." >&2
    echo "       For other platforms see dev/build_msi.cmd / dev/build_appimage.sh." >&2
    exit 1
fi

VERSION="$(cat VERSION 2>/dev/null | head -n1 | tr -d '[:space:]' || echo "dev")"
APP_PATH="dist/YHWH.app"
DMG_PATH="dist/YHWH-${VERSION}.dmg"
ENTITLEMENTS="${ENTITLEMENTS:-$REPO_ROOT/dev/YHWH.entitlements}"

if [[ ! -d "$APP_PATH" ]]; then
    echo "dist/YHWH.app not found — running PyInstaller first..."
    ./dev/build_desktop.sh
fi

# Optional code-sign the .app bundle.
if [[ -n "${CODESIGN_IDENTITY:-}" ]]; then
    echo "Code-signing $APP_PATH with \"$CODESIGN_IDENTITY\"..."
    # Hardened runtime (--options=runtime) is required for notarization; the
    # entitlements let the frozen-Python app load its bundled unsigned dylibs
    # and map executable memory under that runtime (see dev/YHWH.entitlements).
    if [[ -f "$ENTITLEMENTS" ]]; then
        echo "  entitlements: $ENTITLEMENTS"
        codesign --deep --force --options=runtime \
            --sign "$CODESIGN_IDENTITY" \
            --entitlements "$ENTITLEMENTS" \
            --timestamp \
            "$APP_PATH"
    else
        echo "  (no entitlements file at $ENTITLEMENTS — signing without)"
        codesign --deep --force --options=runtime \
            --sign "$CODESIGN_IDENTITY" \
            --timestamp \
            "$APP_PATH"
    fi
    codesign --verify --deep --strict --verbose=2 "$APP_PATH"
fi

# Build the DMG.
echo "Building $DMG_PATH..."
rm -f "$DMG_PATH"
hdiutil create \
    -volname "YHWH" \
    -srcfolder "$APP_PATH" \
    -ov -format UDZO \
    "$DMG_PATH"

# Code-sign the DMG container itself (Apple's recommended flow signs the disk
# image BEFORE notarizing). Without this, the .app inside is notarized/stapled
# but `spctl -a -t open` on the .dmg reports "no usable signature" because the
# container carries no Developer ID signature. Signing it makes the distributable
# assess clean ("accepted, source=Notarized Developer ID") and offline-robust.
if [[ -n "${CODESIGN_IDENTITY:-}" ]]; then
    echo "Code-signing the DMG with \"$CODESIGN_IDENTITY\"..."
    codesign --force --sign "$CODESIGN_IDENTITY" --timestamp "$DMG_PATH"
    codesign --verify --verbose=2 "$DMG_PATH"
fi

# Optional notarization (requires CODESIGN_IDENTITY + NOTARIZE_KEYCHAIN_PROFILE).
if [[ -n "${CODESIGN_IDENTITY:-}" && -n "${NOTARIZE_KEYCHAIN_PROFILE:-}" ]]; then
    echo "Submitting $DMG_PATH for notarization..."
    xcrun notarytool submit "$DMG_PATH" \
        --keychain-profile "$NOTARIZE_KEYCHAIN_PROFILE" \
        --wait
    xcrun stapler staple "$DMG_PATH"
fi

echo
echo "Build complete:"
ls -lh "$DMG_PATH"
echo
if [[ -z "${CODESIGN_IDENTITY:-}" ]]; then
    echo "Note: DMG is unsigned. Gatekeeper will warn on first launch."
    echo "      Set CODESIGN_IDENTITY (and NOTARIZE_KEYCHAIN_PROFILE) for distribution."
fi
