---
holder: mac
from: windows
turn: 1
updated: 2026-06-03T06:22:47Z
status: working
---

## Done (turn 0 → 1; windows built, mac picks up + combines)
- **Windows:** built the lane-handoff baton system (this) — spec + plan + `scripts/lane_handoff.py` + 8 tests + `/handoff`·`/resume`·`/sync` + SessionStart incoming-check (win+mac). COMPLETE. Also P0 (file-disjoint): backfilled manifest folios from witness JSONs + samuel pilot 1sa 4–6.
- **Mac (findings combined in):** 2nd-lane bring-up COMPLETE — toolchain (uv Py3.14 · claude CLI · VS Code), GAPS + OCR PDFs placed & verified, **Tesseract OCR via conda-forge** (macOS 13 = Homebrew-unsupported; `amh`+`script/Ethiopic` tessdata_best, OCR-proven on the parallel-Bible PDF), **SSH push to GitLab+GitHub wired** (gh/glab side-loaded, host keys pinned, passphrase ed25519 in Keychain), 3 cross-platform test fixes landed (`f75029f2`). **Full suite: 7,385 pass / 12 explained non-regressions, ZERO real** (5 tau6x1 OCR = Claude-Bash sandbox `/tmp` artifact → pass w/ `TMPDIR` on MacHD2; 3 perf = iMac budget delta; 2 samkings = the P0 WIP gate you own; 1 hardening backslash = Windows path semantics; 1 ruff = transient mid-edit, clean now).
- **Mac adopted the baton:** `dev/.lane=mac` set. (The SessionStart auto-banner hook → `bootstrap-triad.sh` is PENDING user approval — auto-mode blocked the local-settings edit; the baton works without it via manual `/resume`.)

## Next (turn 1, mac holds)
- **Plan + build the project WEBSITE** — file-disjoint from Windows' P0 / manuscript work (a `website/` subtree). Landing-page-first free-download portal for the Ethiopian Tewahedo Bible editions on `yhwhyaway.com`; static site → free GitLab/GitHub Pages; reuse the per-edition cover art in `content/covers/`. Starting with a one-page plan + a clickable prototype.

## Watch-outs
- ⚠ Running OCR tests through Claude's Bash needs `export TMPDIR=/Volumes/MacHD2/<dir>` (conda leptonica can't read the sandboxed `/tmp`). NOT an OCR defect — passes in a real terminal.
- **Mac holds the baton this turn** → sole pusher + owns SESSION_STATE / IN_FLIGHT / CHANGELOG. Windows: `/resume` when the user switches back; P0 stays file-disjoint from the website.
- Expected reds remain (not regressions): 3 perf (iMac hardware), 2 samkings (P0 WIP), 1 hardening backslash (Windows-only test).
