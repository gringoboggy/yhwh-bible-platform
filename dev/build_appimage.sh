#!/usr/bin/env bash
# Phase θ.4 — Linux AppImage installer wrapper.
#
# Wraps `dist/YHWH` (produced by `dev/build_desktop.sh` →
# `pyinstaller dev/launcher.spec`) into a portable AppImage that
# any modern Linux distribution can run by double-click — no
# package manager, no install. AppImages don't need code-signing.
#
# Required tooling:
#   - appimagetool (from AppImageKit; downloaded to /tmp on first run)
#   - file utilities (already on every distro)
#
# Usage:
#     ./dev/build_appimage.sh
#
# Output: dist/YHWH-<version>-x86_64.AppImage

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "ERROR: build_appimage.sh must run on Linux (uname -s = $(uname -s))." >&2
    echo "       For other platforms see dev/build_dmg.sh / dev/build_msi.cmd." >&2
    exit 1
fi

VERSION="$(cat VERSION 2>/dev/null | head -n1 | tr -d '[:space:]' || echo "dev")"
ARCH="$(uname -m)"
APP_BIN="dist/YHWH"
APPDIR="dist/YHWH.AppDir"
APPIMAGE_OUT="dist/YHWH-${VERSION}-${ARCH}.AppImage"

if [[ ! -f "$APP_BIN" ]]; then
    echo "dist/YHWH not found — running PyInstaller first..."
    ./dev/build_desktop.sh
fi

# Require a pre-installed appimagetool (auto-download removed 2026-05-12).
APPIMAGETOOL="/tmp/appimagetool-${ARCH}.AppImage"
if [[ ! -x "$APPIMAGETOOL" ]]; then
    # R16 Phase I — removed the misleading "Downloading…" echo and the
    # unreachable `chmod` after `exit 1`; this branch only errors + exits.
    echo "ERROR: appimagetool not found at ${APPIMAGETOOL}." >&2
    echo "       Install it manually to that path and re-run." >&2
    exit 1
fi

# Build the AppDir layout.
echo "Building $APPDIR..."
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
cp "$APP_BIN" "$APPDIR/usr/bin/YHWH"

# AppRun (entry point — invoked when the AppImage is launched).
cat > "$APPDIR/AppRun" <<'EOF'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/usr/bin/YHWH" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Desktop entry (shown by AppImage-aware launchers).
cat > "$APPDIR/YHWH.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=YHWH
Comment=Bible publishing platform
Exec=YHWH
Icon=YHWH
Categories=Office;Publishing;
Terminal=false
EOF

# Icon — R16 Phase I: prefer the BRANDED app icon so the Linux AppImage carries
# the same mark as the Win .ico / Mac .icns (they did; the AppImage shipped a
# teal placeholder because content/covers/icon.png does not exist). Fall through
# to the generated placeholder only if no branded PNG is present.
if [[ -f "assets/icons/icon_256.png" ]]; then
    cp "assets/icons/icon_256.png" "$APPDIR/YHWH.png"
elif [[ -f "assets/icons/icon_512.png" ]]; then
    cp "assets/icons/icon_512.png" "$APPDIR/YHWH.png"
elif [[ -f "content/covers/icon.png" ]]; then
    cp "content/covers/icon.png" "$APPDIR/YHWH.png"
else
    # Generate a minimal 256x256 placeholder PNG (8 bytes — solid color).
    # This satisfies appimagetool's icon requirement; real branding
    # should replace it.
    python3 - <<'PY' >"$APPDIR/YHWH.png"
import struct, zlib, sys
w = h = 256
raw = b''.join(b'\x00' + b'\x2c\x4a\x6e' * w for _ in range(h))
def chunk(t, d):
    return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d))
sig = b'\x89PNG\r\n\x1a\n'
ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
idat = zlib.compress(raw)
sys.stdout.buffer.write(sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b''))
PY
fi

# Build the AppImage.
echo "Building $APPIMAGE_OUT..."
rm -f "$APPIMAGE_OUT"
ARCH="$ARCH" "$APPIMAGETOOL" "$APPDIR" "$APPIMAGE_OUT"

echo
echo "Build complete:"
ls -lh "$APPIMAGE_OUT"
echo
echo "AppImages are portable — copy to any modern Linux distro and run."
