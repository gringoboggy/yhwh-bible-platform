# M1 — macOS native-window `.dmg` de-risk (finding 7, HIGH) — VERIFICATION RESULT

**Lane:** 🖥️ Mac · **Turn 40 · 2026-06-08** · gated on WIN STAGE E (`23e3c178`, pulled this session).
**Plan:** `docs/superpowers/notes/2026-06-08-mac-lane-v0.1.0-execution-plan.md` (M1).
**Verdict:** ✅ **finding-7 FIXED — the frozen macOS `.app` opens its OWN native Cocoa window, not a browser.** Proven on this iMac (Python 3.14.5). M1 is ~90% done; the only remainder is wrapping a TEST dmg + minor visual confirms (the load-bearing risk — the native window — is settled).

---

## What WIN landed (STAGE E, `23e3c178`) — the fix under test
- `dev/launcher.spec` — macOS-conditional `hiddenimports += ["webview.platforms.cocoa","objc","Foundation","AppKit","WebKit","Quartz","Security","CoreFoundation","UniformTypeIdentifiers"]` (pywebview importlib-loads the cocoa backend → PyInstaller had dropped it from the frozen `.app`). Also sets the `.app` BUNDLE `icon` → `assets/icons/YHWH.icns` (guarded `is_file()`).
- `dev/requirements-desktop.txt` — `pywebview==6.2.1` (NOT `[cocoa]`) + marker-gated `pyobjc-*==12.2 ; sys_platform=="darwin"` pins.
- `scripts/launcher.py:242-243` — explicit native→browser fallback print, fired only when `frozen and not pywebview_available and args.shell != "browser"`.

## Verification steps + evidence (all PASS)

### 1. Dependency resolution on Python 3.14.5 ✅
`.venv/bin/python -m pip install -r dev/requirements-desktop.txt` → all 6 pyobjc 12.2 frameworks (core, Cocoa, Quartz, WebKit, Security, UniformTypeIdentifiers) resolved via **`cp314` `macosx_10_15_universal2` wheels — NO source build**, plus pywebview 6.2.1 (+ bottle, proxy_tools). Import probe clean:
```
import objc, webview, AppKit, WebKit, Foundation, Quartz, Security, UniformTypeIdentifiers
from webview.platforms import cocoa     # → "OK all native imports"
```
(The Mac turn-36 pre-flight prediction — plain `pywebview`, cp314 wheels, no `[cocoa]` extra — is confirmed empirically.)

### 2. Fresh `.app` rebuild bundles the backend ✅
`./dev/build_desktop.sh` (uses `.venv/bin/python` → PyInstaller 6.20.0; exit 0). The stale Jun-7 `dist/YHWH.app` (pre-STAGE-E, no pyobjc) was replaced. Bundle inspection:
- `objc` present in `Contents/Resources/objc` + `Contents/Frameworks/objc`.
- `webview.platforms.cocoa` is in the PYZ (not a loose file — `noarchive=False`); proven importable by the runtime test below (the app would crash at `webview.start()` if it were missing).
- `Contents/Resources/YHWH.icns` (2.0M) present.
- `Info.plist`: `CFBundleIconFile=YHWH.icns`, `CFBundleIdentifier=com.yhwhyaway.yhwh`, `CFBundleShortVersionString=0.0.3`.

### 3. Native Cocoa window — PROVEN ✅ (the load-bearing check)
Launched the frozen app (`open dist/YHWH.app --args --skip-bootstrap --port 0`). On-screen window enumeration via Quartz `CGWindowListCopyWindowInfo` (no Accessibility permission needed):
```
FOUND native window -> owner="YHWH Ya' Way" name='YHWH — Bible publishing platform'
                       bounds={X:320, Y:90, Width:1280, Height:900} layer=0
```
- Owner = **"YHWH Ya' Way"** = the bundle's `CFBundleDisplayName` → running with full app identity.
- Title = `desktop_shell.DEFAULT_TITLE`; size = exactly `window_config()` defaults (1280×900).
- It is a window **owned by the app process itself** — NOT a browser. No browser process owns a localhost window; the app self-listens on `127.0.0.1` (verified via `lsof`).
- Screenshot (`screencapture -l <windowid>`): `docs/superpowers/notes/assets/2026-06-08-M1-native-window.png` — macOS traffic-light buttons + native title bar + the app shell ("YHWH Ya' Way | note editor", filter/editor panes), **zero browser chrome / no address bar**.

> Note: full-screen `screencapture` grabs initially showed only the desktop because the YHWH window wasn't frontmost (System Settings/Code were) and the direct-launch first-run content migration delays the window; the per-window capture by window-id is the clean shot. Use `--skip-bootstrap` to skip the first-run migration when re-verifying quickly.

## M1 REMAINING (resume here — small)
1. **Wrap a TEST dmg.** `dev/build_dmg.sh` derives the name from `VERSION` (0.0.3) and `rm -f`s that path — which would clobber the **notarized + uploaded** `dist/YHWH-0.0.3.dmg`. So wrap to a NON-`0.0.3` name instead, e.g.:
   `hdiutil create -volname "YHWH" -srcfolder dist/YHWH.app -ov -format UDZO dist/YHWH-0.0.3-nativewin-TEST.dmg`
   (unsigned TEST only — do NOT upload; delete after). The real M3 release dmg reuses this verified `.app` recipe.
2. **Visual dock icon + About** — static proof is already solid (icns in Resources + plist `CFBundleIconFile`); a frontmost screenshot of the dock/About is a nice-to-have, not a risk.
3. **Explicit fallback line** (`launcher.py:242-243`) — source-correct but **not testable on the frozen build** (stdout is block-buffered + `console=False`, and the backend can't be removed from a good bundle). The GOOD build correctly does NOT print it (it goes native). → see Guard #6.

## Guard #6 → WIN (shared code, WIN-owned)
The new fallback print `scripts/launcher.py:242-243` ("native window backend unavailable — falling back to the browser") has **no regression test** in `tests/test_desktop_theta.py` (grep: zero hits for the string). Add a `main()` test using the existing injectable collaborators: monkeypatch `sys.frozen=True` + `desktop_shell.is_pywebview_available`→False (cache_clear) + `--port 0` + injected `server_factory`/`serve_fn`, assert capsys contains the message; plus a negative test asserting it is absent when native is selected. (Same class of follow-up as the turn-38 findings-2/3 regression tests.)

## Environment / hygiene
- `dev/requirements-desktop.txt` deps are now installed in `.venv` (gitignored; no repo change).
- The notarized `dist/YHWH-0.0.3.dmg` was moved to `~/` during the `rm -rf dist/` rebuild and **RESTORED** afterward (intact, 309M, original mtime). `dist/` + `build/` are gitignored.
