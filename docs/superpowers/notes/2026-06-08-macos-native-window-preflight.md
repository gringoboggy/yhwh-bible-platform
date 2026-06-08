# macOS native-window (finding 7) pre-flight — deps + `launcher.spec` for WIN's Stage E

**Status:** PRE-FLIGHT REPORT for WIN (Stage E shared edit). Mac-led. 2026-06-08.
**Goal:** so WIN's `requirements-desktop.txt` + `launcher.spec` edit is correct first-try and the Mac `.dmg` rebuild opens its OWN Cocoa window instead of falling back to a browser.

## Confirmed root cause (matches the device-QA finding-7 diagnosis)
- `dev/requirements-desktop.txt` pins **only** `pywebview==6.2.1` — **no pyobjc**. On macOS, pywebview's Cocoa backend (`webview/platforms/cocoa.py`) imports the Objective-C bridge (`objc`, `Foundation`, `AppKit`, `WebKit`, `Quartz`); with no pyobjc present, backend init fails → pywebview falls back to opening the default browser at localhost (the bug the user saw).
- This Mac's interpreter is **Python 3.14.5** (uv venv); `pywebview`/`pyobjc` are **not installed** here (verified `pip list`). The v0.0.3 `.dmg` shipped without the Cocoa backend bundled, consistent with the fallback.

## What WIN must add (authoritative, from pywebview 6.x's `cocoa` extra + its backend imports)

**1. `dev/requirements-desktop.txt`** — prefer the extra (pywebview itself declares the correct pyobjc set, so we don't hand-drift it):
```
pywebview[cocoa]==6.2.1
```
The `cocoa` extra resolves to: `pyobjc-core`, `pyobjc-framework-Cocoa`, `pyobjc-framework-WebKit`, `pyobjc-framework-Quartz`, `pyobjc-framework-Security`. (If a per-platform requirements split is wanted, gate it `pywebview[cocoa]==6.2.1 ; sys_platform == "darwin"` and keep bare `pywebview==6.2.1` for Win/Linux — Windows uses the EdgeChromium/WinForms backend, Linux the GTK/Qt backend, neither of which wants pyobjc.)

**2. `dev/launcher.spec` `hiddenimports`** — PyInstaller misses pywebview's runtime-chosen backend module + the pyobjc framework modules. Add (alongside the existing `"webview"`):
```python
hiddenimports += [
    "webview.platforms.cocoa",   # the backend pywebview importlib-loads at runtime on macOS
    "objc", "Foundation", "AppKit", "WebKit", "Quartz", "Security", "CoreFoundation",
]
```
Keep the build **platform-conditional** (the spec already needs the icon split per Stage D): the cocoa hiddenimports + `icon='assets/icons/YHWH.icns'` apply on the `sys.platform == 'darwin'` branch only; Windows keeps its EdgeChromium backend + `program_icon.ico`, Linux its AppImage `.png`.

**3. Make the native→browser fallback EXPLICIT** (device-QA finding 7): in the launcher's shell-selection (`scripts/launcher.py` / `scripts/desktop_shell.py`, the `select_shell_mode`/`_run_native` path), when native init is unavailable, log a clear message ("native window backend unavailable — falling back to browser") instead of silently opening the browser, so a future packaging regression is visible.

## ⚠ The one real RISK the empirical proof must settle — Python 3.14 wheels
Python **3.14** is very new. pyobjc ships per-CPython-version wheels; if `cp314` wheels are not yet published, `pip install pywebview[cocoa]` on this Mac would fall back to a **source build** (needs Xcode Command Line Tools + a long compile) or fail outright. WIN's `.dmg` build interpreter must have pyobjc importable, so this matters. **This is exactly what the throwaway proof checks** (does the install resolve to a wheel on this Python, and does a Cocoa window actually open). Mitigation if cp314 wheels are missing: build the `.dmg` with a Python that has pyobjc wheels (3.12/3.13) — PyInstaller bundles its own interpreter, so the dmg's Python need not be the uv 3.14 venv.

## The throwaway proof — GATED on a package install (supply-chain guard #1)
The empirical proof = install `pywebview[cocoa]` into a throwaway venv and run a ~10-line pywebview script that opens a native Cocoa window (`webview.create_window(...); webview.start()`), confirming an OS window (own dock entry + title bar) — NOT a browser. **`pyobjc` is an undeclared dependency, so installing it trips the auto-mode package-install soft-deny (RULES Operational Guard #1).** Per the guard this is flagged for explicit go-ahead (toggle auto OFF / approve), not silently run. Once approved, the proof will report: (a) whether `cp314` wheels resolved or a source build was needed; (b) the exact resolved pyobjc versions to pin; (c) that a real Cocoa window opened. Until then, the deps/hiddenimports above are authoritative from pywebview's own `cocoa` extra and backend source — WIN can wire Stage E from them; the proof only hardens the version pins + the cp314 answer.

## Hand-off
- WIN owns the shared edit (`requirements-desktop.txt` + `launcher.spec` + the explicit-fallback message) in Stage E.
- Mac owns: this pre-flight (done — pending the gated install proof) + the actual `.dmg` rebuild/notarize/staple + device-verify of the native window, after WIN lands the shared edit. The `.icns` it references is already committed (`assets/icons/YHWH.icns`).
