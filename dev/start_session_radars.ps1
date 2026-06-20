# start_session_radars.ps1 — idempotent dual-radar boot (WIN lane).
# Called by bootstrap-triad.ps1 SessionStart hook every session.
#
# Radars (both REQUIRED, both stay on until session ends):
#   1. lane_watch  — cross-lane push/handoff poll (60s)
#   2. agent_idle_radar — anti-idle work surfacing (120s)
#
# Usage:
#   pwsh -File dev/start_session_radars.ps1
#   pwsh -File dev/start_session_radars.ps1 -Quiet

param([switch]$Quiet)

$ErrorActionPreference = "SilentlyContinue"
$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo

function Write-Radar([string]$Msg) {
    if (-not $Quiet) { Write-Host $Msg }
}

function Test-RadarProcess([string]$Needle) {
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine -like "*$Needle*" } |
        Select-Object -First 1
}

Write-Radar "----- SESSION RADARS (bootstrap) -----"

# lane_watch is always started with -Background + the --auto-pull flag (wired inside
# lane_watch_win.ps1) to enforce the STANDING auto-pull-on-BEHIND rule. User never
# says "pull". New guard #8 + doc hygiene rule also apply: after changes like this,
# update AGENTS.md / RULES / bootstrap files proactively.
$lw = Test-RadarProcess "lane_watch.py"
if ($lw) {
    Write-Radar "  lane_watch: already running (pid $($lw.ProcessId))"
} else {
    & "$Repo\dev\lane_watch_win.ps1" -LoopSec 60 -AssignMac -Background
    Write-Radar "  lane_watch: started (60s loop, -AssignMac, --auto-pull)"
}

$idle = Test-RadarProcess "agent_idle_radar.py"
if ($idle) {
    Write-Radar "  agent_idle_radar: already running (pid $($idle.ProcessId))"
} else {
    & "$Repo\dev\agent_idle_radar.ps1" -LoopSec 120 -Background
    Write-Radar "  agent_idle_radar: started (120s loop)"
}

Write-Radar "  STANDING: never wait for user input — run --next when blocked."
Write-Radar "--------------------------------------"