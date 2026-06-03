---
holder: mac
from: windows
turn: 1
updated: 2026-06-03T13:45:21Z
status: working
---

## Done (turn 1, mac lane — this session)
- **Mac 2nd-lane bring-up COMPLETE:** uv Py3.14 + deps · Tesseract OCR via conda-forge (macOS 13 = Homebrew-unsupported; `amh`+`script/Ethiopic`, OCR-proven) · GAPS + OCR PDFs placed & verified · SSH push to GitLab+GitHub wired (Keychain ed25519, gh/glab side-loaded, host keys pinned). 3 cross-platform test fixes landed. **Full suite: 7,385 pass / 12 explained non-regressions, ZERO real.**
- **Adopted the baton** (`dev/.lane=mac`, turn 1). SessionStart auto-hook pending user approval (auto-mode blocked the settings.local.json edit).
- **Website:** 5-agent plan → manuscript-reverent Phase-1 prototype (`website/`) → **★USER RE-SCOPE: the site is the YHWH PROGRAM's (builder's) home page, NOT a Bible-download portal — no EPUBs.** Decisions: showcase + get-the-code · example-editions gallery (no downloads) · keep the look. Prototype content needs rebuild to that framing.
- **Combined Windows' P0** (1sa 7–11 mapping + `fill_manifest_entry.py`) by rebase + **pushed both remotes.**

## Next (turn 1, mac — for the new session)
- **Rebuild `website/index.html` content to the program-homepage framing** per `plans/2026-06-03-website-plan.md` (follow its **⚠ RE-SCOPE block** at the top; ignore the superseded download-portal sections). Keep `style.css`. Then: self-host Noto Ethiopic fonts + generate the 2 missing covers (geez/amharic) + write `scripts/build_site.py` (reads `editions.yaml`) + deploy to GitLab Pages → yhwhyaway.com.
- (Windows lane, file-disjoint:) continue P0 Sam/Kings folio-mapping.

## Watch-outs
- ⚠ Running OCR tests through Claude's Bash needs `export TMPDIR=/Volumes/MacHD2/<dir>` (conda leptonica can't read the sandboxed `/tmp`). Not an OCR defect.
- The website-plan doc's lower sections are the SUPERSEDED download-portal framing — the top **RE-SCOPE block** is the source of truth.
- **Baton held by `mac`.** A new Mac session continues the website (holds the baton). If the new session is Windows and needs to push P0, `/resume --force` (Mac is idle) after confirming. Memory `reference_mac_dev_env` carries the full Mac setup.
