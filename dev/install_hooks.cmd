@echo off
rem Activates the tracked git hooks in .githooks\ for this checkout.
rem Run this once per clone:
rem     .\dev\install_hooks.cmd
rem
rem Sets git's core.hooksPath to the tracked .githooks\ directory, so the
rem canonical pre-commit hook (ruff format --check + scripts\lint_rules.py +
rem mypy via scripts\audit_types.py) runs before each commit. This supersedes
rem the old "copy dev\git-hooks\pre-commit into .git\hooks\" flow: the hook now
rem lives in version control and updates apply to every clone automatically.

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 goto NOT_A_REPO

if not exist ".githooks\pre-commit" goto NO_HOOK

git config core.hooksPath .githooks
if errorlevel 1 goto CONFIG_FAILED

echo Installed: core.hooksPath = .githooks
echo Future commits run .githooks\pre-commit (ruff format --check + lint_rules.py + mypy).
echo Use 'git commit --no-verify' to bypass for a single commit.
exit /b 0

:NOT_A_REPO
echo ERROR: not inside a git work tree. Run from the repo root.
exit /b 1

:NO_HOOK
echo ERROR: .githooks\pre-commit not found. Run from the repo root.
exit /b 1

:CONFIG_FAILED
echo ERROR: 'git config core.hooksPath .githooks' failed.
exit /b 1
