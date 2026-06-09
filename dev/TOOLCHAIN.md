# TOOLCHAIN — cross-lane tool parity (Windows ⇄ macOS)

**Purpose.** Both lanes must be able to do *everything that is not physically platform-locked*
on their own machine, so neither lane is ever blocked waiting on the other. This is the canonical
tool inventory + per-OS acquisition + a runnable self-audit. Run **§Verify** on a fresh machine,
after a reinstall, or whenever a lane suspects a gap. Keep it in sync with the `requirements*.txt`
files (those remain the source of truth for pip versions).

Status as of **2026-06-09**: Windows lane = self-sufficient on all cross-platform tools (audited +
kepubify install proven end-to-end). macOS lane should run §Verify and close any gap (kepubify was
the known one — see below).

---

## The platform floor (inherently NOT portable — do not try to make these parity)

| Capability | Only on | Why | Coverage when the owning machine is down |
|---|---|---|---|
| Windows `.exe` installer (PyInstaller `--onefile` + Inno Setup `installer.iss`) + `.ico` | **Windows** | PyInstaller freezes for the host OS only | Wait for the Windows lane / a Windows CI runner |
| macOS `.app` / `.dmg`, `codesign`, `notarytool`, `stapler`, `spctl`, `hdiutil`, `.icns`, pywebview **Cocoa** native window | **macOS** | Apple toolchain + Developer-ID identity (`Bogdan Zorlescu AAHZNDCGFW`) + notary profile `yhwh-notary` live only on the Mac | Wait for the macOS lane |
| Linux `.AppImage` | **CI** (`build-linux.yml`) | built in GitHub Actions, not on either dev box | Re-run the workflow |

**Everything below this line is cross-platform and BOTH machines must have it.**

---

## Cross-platform toolchain (both machines)

| Tool | Purpose | Windows (this box — verified) | macOS acquire | Verify |
|---|---|---|---|---|
| **Python 3** (full interpreter, NOT the Store stub) | everything: build, tests, web app | `pythoncore-3.14` (`py -3` → 3.14.4) | `brew install python@3.x` or python.org | `py -3 --version` / `python3 --version` |
| **pip deps** | build + web + lint + freeze | `pip install -r requirements.txt -r requirements-dev.txt -r dev/requirements-desktop.txt` | same | `py -3 -m pip check` |
| **pytest** (+ `pytest-xdist`) | test suite | 9.0.3 ✓ | via requirements-dev | `py -3 -m pytest --version` |
| **ruff** | format + lint (pre-commit `ruff format --check .` BLOCKS commits) | 0.15.12 ✓ | via requirements-dev | `ruff --version` |
| **mypy** | types (pre-commit `audit_types.py`) | 2.0.0 ✓ | via requirements-dev | `mypy --version` |
| **PyInstaller** | freeze the desktop app (host-OS binary only) | 6.20.0 ✓ | via requirements-desktop | `py -3 -m PyInstaller --version` |
| **pywebview** | desktop native window (Cocoa on mac; falls back to browser elsewhere) | 6.2.1 ✓ | requirements-desktop pulls pyobjc on darwin | `py -3 -c "import webview"` |
| **epubcheck** (pip pkg + bundled jar) | EPUB 3.3 validation | 5.1.0 ✓; jar in site-packages | via requirements-dev | `py -3 -c "import epubcheck,os;print(os.path.dirname(epubcheck.__file__))"` |
| **Java (JRE/JDK)** | runs epubcheck's jar | **Temurin 26** ✓ (epubcheck 5.1.0 needs Java 11+; **the old "Java 8 shim" note is stale**) | `brew install temurin` | `java -version` |
| **Node + npm** | website build (`website/build.mjs`) | node v24.15.0, npm 11.12.1 ✓ | `brew install node` | `node --version && npm --version` |
| **kepubify** (PINNED **v4.0.4**) | EPUB → Kobo `.kepub.epub` (Kobo footnote **popups require the KePub artifact**; a plain `.epub` won't pop on Kobo) | ✅ installed `~/bin/kepubify.exe`, on USER PATH, **conversion proven** (eth 25.85→32.78 MB, 0 errored) | see **§kepubify** below | `kepubify --version` → `kepubify v4.0.4` |
| **git** + **SSH remotes** | the lane sync channel | git 2.54; `origin`=GitLab + `github`=GitHub, both SSH ✓ | system git + the shared ed25519 key | `git remote -v` (expect both) |
| **Chrome / Playwright** (visual QA) | render-verify EPUBs / consoles | via the **Playwright + Chrome-DevTools MCP plugins** (the Python `playwright` pkg is NOT required for this) | same MCP plugins | MCP `browser_navigate` works |

### §kepubify (the parity gap that prompted this doc)

Pinned to **v4.0.4** (the version the macOS lane standardized on). Official source: `github.com/pgaskin/kepubify`.
**Do not commit the binary** — it's external tooling (like epubcheck's jar location), keep it out of the tree.

- **Windows:** `Invoke-WebRequest 'https://github.com/pgaskin/kepubify/releases/download/v4.0.4/kepubify-windows-64bit.exe' -OutFile "$env:USERPROFILE\bin\kepubify.exe"` then add `~/bin` to the USER PATH. (Done on this box.)
- **macOS:** download `kepubify-darwin-arm64` (Apple Silicon) or `kepubify-darwin-64bit` (Intel) from the **v4.0.4** release → `chmod +x` → `xattr -d com.apple.quarantine <file>` → put it on PATH (e.g. `/usr/local/bin/kepubify`). Or `brew install kepubify` if the tap pins v4.0.4.
- **Convert:** `kepubify -o out.kepub.epub in.epub`. Watch the two gotchas: (1) kepubify can turn ordinary cross-reference links into spurious popups — verify real noterefs pop **without over-popping**; (2) confirm note/aside `id`s survive the `koboSpan` transform (the popup target depends on them). See `docs/superpowers/notes/2026-06-05-eink-epub-compat-research.md` refs 41–44.
- **Consequence of parity:** with kepubify on BOTH machines, whichever box has the Kobo plugged in produces the `.kepub.epub` locally — no cross-machine binary shuttle, and the earlier "WIN supplies the kepub" stopgap is moot.

---

## §Verify — runnable self-audit

**Windows (PowerShell):**
```powershell
py -3 --version
py -3 -m pip check
ruff --version; mypy --version
py -3 -c "import webview, epubcheck; print('desktop+epubcheck OK')"
java -version
node --version; npm --version
kepubify --version            # expect: kepubify v4.0.4
git remote -v                 # expect origin=GitLab + github=GitHub
```

**macOS (bash/zsh):**
```bash
python3 --version
python3 -m pip check
ruff --version; mypy --version
python3 -c "import webview, epubcheck; print('desktop+epubcheck OK')"
java -version
node --version; npm --version
kepubify --version            # expect: kepubify v4.0.4 — INSTALL if missing (see §kepubify)
git remote -v
# macOS-only build chain (platform floor): xcrun notarytool --version; codesign -h; hdiutil help >/dev/null && echo hdiutil OK
```

---

## Environment gotchas (carry — both lanes hit these)

- **`$env:PYTHONUTF8="1"`** on Windows test runs or ~72 tests fail with cp1252 errors.
- **`--basetemp`** on every pytest run on Windows (`tmp_path` fails under the harness TEMP): `--basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`.
- **Python path:** bare `python`/`python3` on Windows = broken Store alias; use `py -3` or the pythoncore full path.
- **npm `.npmrc` prefix warning** on Windows (the repo `.npmrc` sets a prefix) — harmless for `node build.mjs`; only global installs complain.
- **epubcheck:** always pass `--jar <bundled jar>` (the PATH `epubcheck.exe` wrapper is unparseable).
- **memory cap (Windows N95, 16 GB soldered):** never run pytest concurrent with a build; heavy tasks MAX-1.
