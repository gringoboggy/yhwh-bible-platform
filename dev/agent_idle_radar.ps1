# agent_idle_radar.ps1 — WIN anti-idle companion to lane_watch.
# Surfaces next work when the agent has been quiet too long.
#
# Usage:
#   pwsh -File dev/agent_idle_radar.ps1 -Next
#   pwsh -File dev/agent_idle_radar.ps1 -Ping -Note "pytest slice"
#   pwsh -File dev/agent_idle_radar.ps1 -LoopSec 120 -Background

param(
    [switch]$Next,
    [switch]$Ping,
    [string]$Note = "",
    [int]$LoopSec = 120,
    [switch]$Background
)

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo

$py = "py"
$args = @("-3", "scripts/agent_idle_radar.py")

if ($Ping) {
    if ($Note) { $args += @("--ping", "--note", $Note) }
    else { $args += "--ping" }
} elseif ($Next) {
    $args += "--next"
} elseif ($Background) {
    $log = Join-Path $Repo "dev\.agent_idle_radar.log"
    Start-Process -FilePath $py -ArgumentList (@("-3", "scripts/agent_idle_radar.py", "--loop", "$LoopSec")) `
        -WorkingDirectory $Repo -WindowStyle Hidden
    Write-Host "agent_idle_radar: background loop ${LoopSec}s — log $log"
    exit 0
} else {
    $args += "--next"
}

& $py @args
exit $LASTEXITCODE