# lane_watch_win.ps1 — Windows-side cross-lane poll (pull + handoff + optional Mac queue).
# STANDING: pair with save-all.ps1 — commit+save often without asking or waiting on input.
#
# Usage:
#   pwsh -File dev/lane_watch_win.ps1 -Once
#   pwsh -File dev/lane_watch_win.ps1 -LoopSec 60 -AssignMac
#   pwsh -File dev/lane_watch_win.ps1 -LoopSec 60 -AssignMac -Background
#
param(
    [switch]$Once,
    [int]$LoopSec = 60,
    [switch]$AssignMac,
    [switch]$Background
)

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo

$py = "py"
$args = @("-3", "scripts/lane_watch.py", "--auto-pull")
if ($AssignMac) { $args += "--assign-mac" }
if ($Once) {
    $args += "--once"
} else {
    $args += @("--loop", "$LoopSec")
}

if ($Background) {
    $log = Join-Path $Repo "dev\.lane_watch.log"
    Start-Process -FilePath $py -ArgumentList $args -WorkingDirectory $Repo -WindowStyle Hidden
    Write-Host "lane_watch: background — log $log"
    exit 0
}

& $py @args
exit $LASTEXITCODE