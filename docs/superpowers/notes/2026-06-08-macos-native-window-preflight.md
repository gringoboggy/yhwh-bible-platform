# macOS native-window (finding 7) pre-flight — PROVEN; deps + `launcher.spec` for WIN's Stage E

**Status:** PRE-FLIGHT **PROOF COMPLETE** 2026-06-08 (Mac). A throwaway-venv install + import test ran on this Mac's **Python 3.14.5** (user toggled auto-mode off to authorize the install per Guard #1). Throwaway venv cleaned up after.

## ✅ Proof results (throwaway venv, Python 3.14.5)
- **`pywebview==6.2.1` pulls the pyobjc backend AUTOMATICALLY on macOS** via PEP 508 markers. Its `Requires-Dist` for `sys_platform == "darwin"` are: `pyobjc-core>=9.0`, `pyobjc-framework-Cocoa>=9.0`, `pyobjc-framework-Quartz>=9.0`, `pyobjc-framework-WebKit>=9.0`, `pyobjc-framework-security>=9.0`, `pyobjc-framework-UniformTypeIdentifiers>=9.0`. **⚠ There is NO `[cocoa]` extra** — `pywebview[cocoa]` warns *"does not have an extra named cocoa"* and is ignored. (This corrects the turn-35 board note / my earlier draft.)
- **All resolved to WHEELS — no source build:** `pyobjc-core==12.2` + `pyobjc-framework-{Cocoa,Quartz,WebKit,Security,UniformTypeIdentifiers}==12.2`. pyobjc ships **cp310–cp315 wheels**, so **`cp314` is present** → the Python-3.14 wheel risk I earlier flagged is **RESOLVED**; the `.dmg` build interpreter need NOT be downgraded to 3.12/3.13.
- **Import proof PASSED on Python 3.14.5:** `import webview`, `from webview.platforms import cocoa`, `import objc, Foundation, AppKit, WebKit, Quartz` all succeed.

## Corrected root cause (sharper than the device-QA guess)
finding 7's browser fallback is **NOT** because `requirements-desktop.txt` "forgot pyobjc" — on macOS, installing `pywebview` pulls pyobjc itself. The real cause is **PyInstaller bundling**: pywebview imports its platform backend **dynamically** (`importlib`), so PyInstaller's static analysis misses `webview.platforms.cocoa` + the pyobjc framework modules and omits them from the frozen `.app` → at runtime the cocoa backend import fails inside the app → pywebview falls back to the browser. `dev/launcher.spec` hiddenimports lists only `"webview"` (commented "verified building YHWH.exe" — Windows-only), confirming the gap. **So the fix is primarily the `launcher.spec` hiddenimports.**

## What WIN adds in Stage E
1. **`dev/requirements-desktop.txt`:** KEEP `pywebview==6.2.1` (it pulls the pyobjc frameworks on macOS via markers). Do **NOT** write `pywebview[cocoa]`. *Optional* for build reproducibility — additionally pin the frameworks (all `==12.2`), marker-gated:
   ```
   pyobjc-core==12.2 ; sys_platform == "darwin"
   pyobjc-framework-Cocoa==12.2 ; sys_platform == "darwin"
   pyobjc-framework-Quartz==12.2 ; sys_platform == "darwin"
   pyobjc-framework-WebKit==12.2 ; sys_platform == "darwin"
   pyobjc-framework-Security==12.2 ; sys_platform == "darwin"
   pyobjc-framework-UniformTypeIdentifiers==12.2 ; sys_platform == "darwin"
   ```
2. **`dev/launcher.spec` `hiddenimports` (THE FIX):**
   ```python
   hiddenimports += [
       "webview.platforms.cocoa",   # pywebview importlib-loads this at runtime on macOS
       "objc", "Foundation", "AppKit", "WebKit", "Quartz", "Security",
       "CoreFoundation", "UniformTypeIdentifiers",
   ]
   ```
   Keep platform-conditional (darwin branch), alongside `icon='assets/icons/YHWH.icns'` (already committed). Windows keeps EdgeChromium + `program_icon.ico`; Linux the GTK backend + `icon_512.png`.
3. **Make the native→browser fallback EXPLICIT** in `scripts/launcher.py` / `scripts/desktop_shell.py` (`select_shell_mode`/`_run_native`): log a clear "native backend unavailable — falling back to browser" instead of a silent browser open, so a future packaging regression is visible.

## Verified vs still-to-verify
- **Verified on this Mac:** install resolves to cp314 wheels + the cocoa backend + the pyobjc bridge import on Python 3.14.5 (the exact failure mode behind the browser fallback no longer applies once bundled).
- **Still on-device (Mac release-time, after WIN lands the shared edit):** the rebuilt `.dmg` opens its OWN Cocoa window (dock entry + window + About) with the `.icns` icon — proven end-to-end when I rebuild/notarize/staple the dmg + launch it.

## Hand-off
WIN owns the shared Stage-E edit (requirements + `launcher.spec` hiddenimports + the explicit-fallback message). Mac owns the `.dmg` rebuild/notarize/staple + device-verify after, and references the committed `assets/icons/YHWH.icns`.
