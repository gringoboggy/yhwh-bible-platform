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

import sys
from pathlib import Path

# SPECPATH is set by PyInstaller to the directory containing this
# spec file. The repo root is one level up.
ROOT = Path(SPECPATH).resolve().parent


# Version string for the .app bundle Info.plist — first non-blank line of
# the repo VERSION file (the same source dev/build_dmg.sh + installer.iss
# consume). Falls back to a sentinel if the file is somehow absent.
def _read_version() -> str:
    vf = ROOT / "VERSION"
    if vf.is_file():
        for _line in vf.read_text(encoding="utf-8").splitlines():
            if _line.strip():
                return _line.strip()
    return "0.0.0"


VERSION = _read_version()

block_cipher = None

# Hidden imports the PyInstaller static analyzer misses. The base set covers the
# dynamically-registered detectors/sources and the first-run migrator. On macOS
# we ALSO name the PyWebView Cocoa backend + its pyobjc framework bridges:
# pywebview importlib-loads ``webview.platforms.cocoa`` at runtime, so PyInstaller
# omits it (and the pyobjc modules) from the frozen .app unless listed here — and
# without them the native window silently falls back to the browser (finding 7;
# pre-flight docs/superpowers/notes/2026-06-08-macos-native-window-preflight.md,
# import-proven on Python 3.14.5). Windows/Linux resolve their backend from the
# top-level "webview" scan, so they need only the base set.
_HIDDENIMPORTS = [
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
    # θ.2: PyWebView for native shell mode. On Windows/Linux the platform backend
    # (WebView2 / WebKitGTK) is picked up by scanning the top-level "webview"
    # package, so listing it is sufficient there.
    "webview",
]
if sys.platform == "darwin":
    # macOS: name the dynamically-imported Cocoa backend + pyobjc bridges so the
    # frozen .app actually opens its native WKWebView window (finding 7).
    _HIDDENIMPORTS += [
        "webview.platforms.cocoa",
        "objc",
        "Foundation",
        "AppKit",
        "WebKit",
        "Quartz",
        "Security",
        "CoreFoundation",
        "UniformTypeIdentifiers",
    ]

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
        # The base HTML the build pipeline injects notes into + filters per
        # edition (build_edition copies epub_working/ → a tmp working dir).
        # MUST be bundled or the frozen build fails with WinError 3. The huge
        # epub_working/.backups/ snapshot subtree (~2.6 GB) is filtered below.
        (str(ROOT / "epub_working"), "epub_working"),
        # Self-hosted UI fonts (SIL OFL 1.1) so the frozen app's manuscript skin
        # renders EB Garamond + Noto Serif Ethiopic exactly like the website instead
        # of 404ing the /fonts/ route + falling back to Georgia. Same files the site
        # ships (website/fonts/), served by scripts/web.py's /fonts/ route. Without
        # this the route works in dev but 404s in the frozen build (the §1.5 bundle-
        # path gotcha). Spec: docs/superpowers/specs/2026-06-09-app-eb-garamond-selfhosting.md §2.
        (str(ROOT / "website" / "fonts"), "website/fonts"),
    ],
    hiddenimports=_HIDDENIMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Wave 4 (W4.1, 2026-05-25) — drop regenerable scratch data from the bundle so the
# desktop binary ships only what the app actually reads at runtime:
#   content/candidates/           — prospect->promote pipeline output (~77 MB, 1646 files)
#   content/translations/sources/ — raw extractor source text/XML (~220 MB, 171 files)
#   epub_working/.backups/        — base-HTML backup snapshots (~2.6 GB!)
# The app uses the PROMOTED notes (content/notes/) + the per-id translation stores
# (content/translations/<id>/) + the epub_working/ base, never the scratch/backup
# subtrees. Filtering a.datas keeps the directory datas entries above simple while
# excluding these large regenerable subtrees.
_DROP_PREFIXES = ("content/candidates", "content/translations/sources", "epub_working/.backups")
a.datas = [
    (dst, src, typ)
    for (dst, src, typ) in a.datas
    if not dst.replace("\\", "/").startswith(_DROP_PREFIXES)
]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Run the bundled interpreter in UTF-8 mode. The codebase reads its UTF-8
# corpus (kinds.yaml symbols, Hebrew/Greek notes, HTML) via read_text()/
# open() WITHOUT an explicit encoding, relying on the dev convention
# PYTHONUTF8=1. A double-clicked binary has no such env, and PyInstaller's
# frozen interpreter ignores the PYTHONUTF8 env var — so without -X utf8
# reads default to cp1252 and fail (charmap decode error).
_EXE_OPTIONS = [("X utf8", None, "OPTION")]

if sys.platform == "darwin":
    # macOS — ONEDIR layout (EXE bootloader → COLLECT tree → BUNDLE .app).
    # A onefile binary inside a .app "clashes with macOS's security"
    # (PyInstaller's own deprecation warning): Gatekeeper can reject or
    # flag the self-extracting single file even after notarization. onedir
    # keeps each dylib individually signable inside the bundle, which is
    # the layout Apple notarization + the hardened runtime expect.
    # Codesigning + entitlements are applied post-build by dev/build_dmg.sh
    # (opt-in via CODESIGN_IDENTITY), not here.
    exe = EXE(
        pyz,
        a.scripts,
        _EXE_OPTIONS,
        exclude_binaries=True,  # onedir: binaries + datas live in COLLECT
        name="YHWH",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="YHWH",
    )
    _ICNS = ROOT / "assets" / "icons" / "YHWH.icns"
    app = BUNDLE(
        coll,
        name="YHWH.app",
        icon=str(_ICNS) if _ICNS.is_file() else None,  # branded .app icon (assets/icons/YHWH.icns)
        bundle_identifier="com.yhwhyaway.yhwh",
        version=VERSION,
        info_plist={
            "CFBundleName": "YHWH",
            "CFBundleDisplayName": "YHWH Ya' Way",
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "10.15.0",
            "NSHumanReadableCopyright": "Source-available; incorporates public-domain texts.",
        },
    )
else:
    # Windows / Linux — ONEFILE (single dist/YHWH.exe or ELF binary), the
    # original θ.1 behavior; unaffected by the macOS .app restructure.
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        _EXE_OPTIONS,
        name="YHWH",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,  # UPX corrupts Mach-O code signatures (breaks notarization)
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
