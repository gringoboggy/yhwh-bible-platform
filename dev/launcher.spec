# -*- mode: python ; coding: utf-8 -*-
# Phase θ.1 — PyInstaller spec for the YHWH desktop launcher.
#
# Produces a single-file binary that bundles:
#   * scripts/launcher.py as the entry
#   * the rest of scripts/ as importable code
#   * content/ as a read-only template (the launcher copies it
#     to user_data_root on first run via ω.5's migrator)
#
# Build (from repo root):
#
#     pyinstaller dev/launcher.spec        # produces dist/YHWH(.exe)
#
# Cross-platform: PyInstaller chooses the right output type based on
# the host (.exe on Windows, .app on macOS, ELF binary on Linux).
# ``console=False`` means no terminal window in GUI shells; on Linux
# you'll still see stdout if you launch from a terminal.
#
# θ.2 will replace this single-file spec with a proper bundled .app
# / .msi via PyWebView; θ.4 will sign + notarize.

from pathlib import Path

# SPECPATH is set by PyInstaller to the directory containing this
# spec file. The repo root is one level up.
ROOT = Path(SPECPATH).resolve().parent

block_cipher = None

a = Analysis(
    [str(ROOT / "scripts" / "launcher.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Bundled read-only template; copied to user_data_root on
        # first run by scripts.migrate_to_user_data.
        (str(ROOT / "content"), "content"),
        # Web template HTML constants live alongside scripts.web —
        # PyInstaller follows imports, but the templates dir has
        # both .py modules and (potentially) sibling assets, so
        # bundle the whole directory.
        (str(ROOT / "scripts" / "templates"), "scripts/templates"),
    ],
    hiddenimports=[
        # ALL_DETECTORS dynamically registers detector classes;
        # PyInstaller's static analyzer doesn't always pick them up.
        "scripts.core.detectors",
        "scripts.core.sources",
        "scripts.core.traditions",
        "scripts.core.covers",
        "scripts.core.config",
        "scripts.core.translations",
        "scripts.core.notes_io",
        "scripts.core.html_utils",
        "scripts.core.epubcheck",
        "scripts.core.fetcher_config",
        "scripts.migrate_to_user_data",
        # θ.2: PyWebView for native shell mode. Platform-specific
        # backends (CEF / Edge / Cocoa / GTK) are conditionally
        # imported by the webview package itself; PyInstaller picks
        # them up when scanning the package, so listing the top-
        # level "webview" is sufficient on all platforms.
        "webview",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="YHWH",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
