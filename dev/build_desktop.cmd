@echo off
REM Phase theta.1 - Windows desktop-binary build wrapper.
REM
REM Wraps `pyinstaller dev\launcher.spec` with sanity checks:
REM   1. PyInstaller is installed (install if missing).
REM   2. Run from the repo root so SPECPATH resolves correctly.
REM   3. Clean prior build artifacts (build\ and dist\).
REM
REM Usage:
REM     dev\build_desktop.cmd
REM
REM Output: dist\YHWH.exe.
REM
REM Linux/macOS users: see dev\build_desktop.sh for the equivalent.

setlocal
pushd "%~dp0\.."

where pyinstaller >nul 2>&1
if errorlevel 1 (
    REM R16 Phase I — install from the PINNED canonical desktop deps (pyinstaller==
    REM 6.20.0 to match build-linux.yml + pywebview==6.2.1) instead of an unpinned
    REM `pip install pyinstaller`, so all three OSes freeze on one tested toolchain.
    echo PyInstaller not found. Installing pinned desktop deps into the active Python...
    python -m pip install --user -r dev\requirements-desktop.txt
    if errorlevel 1 goto :err
)

echo Cleaning prior build artifacts...
if exist build  rmdir /s /q build
if exist dist   rmdir /s /q dist

echo Building YHWH.exe...
python -m PyInstaller dev\launcher.spec --noconfirm
if errorlevel 1 goto :err

echo.
echo Build complete:
dir /b dist
echo.
echo Run: dist\YHWH.exe (double-click or invoke from terminal)
popd
endlocal
exit /b 0

:err
echo.
echo BUILD FAILED.
popd
endlocal
exit /b 1
