@echo off
REM Phase theta.4 - Windows installer wrapper.
REM
REM Wraps dist\YHWH.exe (produced by dev\build_desktop.cmd ->
REM pyinstaller dev\launcher.spec) into a click-through Setup.exe
REM via Inno Setup. Despite the .cmd filename hint, the actual
REM output is an Inno Setup .exe installer (industry-standard,
REM lighter than MSI, free); the .msi convention name is kept
REM for parity with the spec's DMG/MSI/AppImage trio.
REM
REM Requires Inno Setup 6.x installed:
REM   https://jrsoftware.org/isdl.php
REM
REM Tries common install paths automatically. Override with:
REM   set ISCC=C:\path\to\ISCC.exe
REM
REM Code-signing is opt-in (configure SignTool inside Inno Setup
REM IDE Tools > Configure Sign Tools, then uncomment SignTool=
REM in installer.iss). Unsigned installers work fine for personal
REM / dev use; SmartScreen warns end-users on download until
REM signed with an Authenticode cert.
REM
REM Usage:
REM     dev\build_msi.cmd
REM
REM Output: dist\YHWH-<version>-windows-x64.exe (matches releases.html + gh release)

setlocal
pushd "%~dp0\.."

if not exist "dist\YHWH.exe" (
    echo dist\YHWH.exe not found - running PyInstaller first...
    call dev\build_desktop.cmd
    if errorlevel 1 goto :err
)

REM Locate Inno Setup compiler (ISCC.exe).
if not defined ISCC (
    if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
)
if not defined ISCC (
    if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
)
if not defined ISCC (
    echo ERROR: Inno Setup 6 not found.
    echo        Install from https://jrsoftware.org/isdl.php
    echo        Or set ISCC=C:\path\to\ISCC.exe before running.
    goto :err
)

REM First line of VERSION only (build_dmg.sh parity — full file has prose below).
set "VERSION=dev"
if exist "VERSION" for /f "usebackq delims=" %%V in (`more +0 VERSION`) do set "VERSION=%%V" & goto :ver_done
:ver_done

echo Compiling Inno Setup script with "%ISCC%" (version %VERSION%)...
"%ISCC%" /DMyAppVersion=%VERSION% dev\installer.iss
if errorlevel 1 goto :err

echo.
echo Build complete:
dir /b dist\YHWH-*-windows-x64.exe
echo.
echo Note: Installer is unsigned unless SignTool is configured.
echo       SmartScreen warns end-users on download for unsigned binaries.
popd
endlocal
exit /b 0

:err
echo.
echo BUILD FAILED.
popd
endlocal
exit /b 1
