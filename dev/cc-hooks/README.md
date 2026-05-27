# Claude Code hooks for this project

Tracked source-of-truth for the per-project Claude Code hook + installer.
**Required reading for any Claude/machine working on this project.**

## What lives here

| File | Role |
|---|---|
| `bootstrap-triad.ps1` | SessionStart hook — forces every fresh Claude session to read the triad (`dev/CLAUDE_PROJECT_RULES.md`, `dev/SESSION_STATE.md`, `dev/PLAN_*-end-scope.md`) before acting. |
| `install_cc_hooks.ps1` | Idempotent installer — copies the hook into the cwd-parent `.claude/hooks/` and patches `.claude/settings.json` to register it. |
| `README.md` | This file. |

## Why a tracked copy

Claude Code reads hook scripts from `<cwd>/.claude/hooks/` and reads its registration from `<cwd>/.claude/settings.json`. Both `.claude/*` paths are gitignored (see `.gitignore` line 46), so the runtime files do **not** survive:

- a fresh clone of the repo,
- a wipe of `~/.claude/`,
- a new Anthropic account on the same machine,
- a new machine.

The first time the bootstrap hook was shipped, only the docs landed in git — the runtime `.ps1` + `settings.json` entry lived only on the original machine. This directory closes that gap.

## Fresh-machine / fresh-account setup

From a Windows PowerShell prompt **in the parent of this repo** (i.e. cwd =
`...\YHWH-v2.4-full\`, not the `YHWH v2.4\` subdir — Claude Code reads `.claude/`
from cwd):

```powershell
pwsh -NoProfile -File "YHWH v2.4\dev\cc-hooks\install_cc_hooks.ps1"
```

The installer:
1. Creates `<cwd-parent>\.claude\hooks\` if missing.
2. Copies `bootstrap-triad.ps1` from the tracked source.
3. Reads `<cwd-parent>\.claude\settings.json` (creates `{}` if missing).
4. Appends a `SessionStart` hook entry that points at the copied script (skips if already present).

It is idempotent — running it twice reports "already installed and current". To force-overwrite the on-disk copy if the script content drifted, pass `-Force`.

After install: open `/hooks` in Claude Code once or restart the session — the file watcher only re-scans dirs that had a settings file at session start.

## Other portability notes for a new Claude/machine

- **Python interpreter** — many `dev/*.md` runbooks reference
  `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe` because
  Windows Store ships a broken `python.exe` stub on this machine. On a clean
  machine, `py -3` (the Python launcher) usually resolves a working interpreter.
  Substitute accordingly when reading older runbooks.
- **`PYTHONUTF8=1`** — required on Windows or ~72 tests fail with cp1252 errors.
  Persist as a User env var:
  `[Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "User")`.
- **Git pre-commit hook** — install separately:
  `.\dev\install_hooks.cmd` (runs `scripts\lint_rules.py` on every commit).
- **`.env`** — kept gitignored. Variable names + structure live in
  `.env.example`. Real values are never committed.
- **External services** — the project itself has zero required external
  services. AI-assisted ingest (Anthropic, Voyage) and acquisition (CUDL IIIF)
  are optional; absent credentials, those code paths stay inert.

## The triad the hook directs Claude to

The hook output names them by relative path. They live at the repo root
(inside `YHWH v2.4/`), all tracked in git:

- `dev/CLAUDE_PROJECT_RULES.md` — rules, conventions, mental models
- `dev/SESSION_STATE.md` — current snapshot (shipped / next / test count)
- `dev/PLAN_2026-05-24-end-scope.md` — master forward sequence
- `dev/IN_FLIGHT.md` — current task tracker (read after the triad if its
  `TRACKER-STATE` is active)
