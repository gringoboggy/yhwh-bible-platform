# lane_watch_win.ps1 — Windows-side cross-lane poll (pull + handoff + optional Mac queue).
# STANDING: pair with save-all.ps1 — commit+save often without asking or waiting on input.
#
# --auto-pull is **always** passed. This enforces the STANDING "Auto-pull on BEHIND" rule
# (LANE_HANDOFF) and RULES guard #8: when the branch is behind origin/main + tree is clean,
# the radar must just do `git pull --rebase origin main`. The user never has to say "pull".
# See CLAUDE_PROJECT_RULES.md guard #8 (literal implementation of "always just do the
# logical automation" directives) and the doc-update discipline (update AGENTS/RULES/PLAYBOOK
# etc. proactively after such changes; no confirmation wait when obvious).
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