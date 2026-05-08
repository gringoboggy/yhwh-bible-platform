@echo off
rem Installs tracked git hooks from dev\git-hooks\ into .git\hooks\.
rem Run this once per checkout:
rem     .\dev\install_hooks.cmd
rem
rem Hooks installed:
rem   pre-commit  - runs scripts\lint_rules.py before each commit;
rem                 aborts the commit if the linter reports failures.

if not exist ".git\hooks" goto NO_GIT_HOOKS
if not exist "dev\git-hooks\pre-commit" goto NO_TEMPLATE

copy /Y "dev\git-hooks\pre-commit" ".git\hooks\pre-commit" > nul
if errorlevel 1 goto COPY_FAILED

echo Installed: .git\hooks\pre-commit
echo Future commits run scripts\lint_rules.py before completing.
echo Use 'git commit --no-verify' to bypass for a single commit.
exit /b 0

:NO_GIT_HOOKS
echo ERROR: .git\hooks not found. Run from the repo root.
exit /b 1

:NO_TEMPLATE
echo ERROR: dev\git-hooks\pre-commit not found.
exit /b 1

:COPY_FAILED
echo ERROR: failed to copy pre-commit hook.
exit /b 1
