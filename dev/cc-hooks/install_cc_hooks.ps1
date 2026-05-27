[CmdletBinding()]
param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$repoRoot   = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$parentDir  = Split-Path -Parent $repoRoot
$claudeDir  = Join-Path $parentDir '.claude'
$hooksDir   = Join-Path $claudeDir 'hooks'
$settings   = Join-Path $claudeDir 'settings.json'
$srcHook    = Join-Path $PSScriptRoot 'bootstrap-triad.ps1'
$dstHook    = Join-Path $hooksDir 'bootstrap-triad.ps1'

if (-not (Test-Path $srcHook)) { throw "Missing tracked source: $srcHook" }

New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null

if ((Test-Path $dstHook) -and -not $Force) {
    $srcHash = (Get-FileHash $srcHook -Algorithm SHA256).Hash
    $dstHash = (Get-FileHash $dstHook -Algorithm SHA256).Hash
    if ($srcHash -eq $dstHash) {
        Write-Host "Hook already installed and current: $dstHook"
    } else {
        Copy-Item $srcHook -Destination $dstHook -Force
        Write-Host "Hook updated (content drifted): $dstHook"
    }
} else {
    Copy-Item $srcHook -Destination $dstHook -Force
    Write-Host "Hook installed: $dstHook"
}

if (Test-Path $settings) {
    $json = Get-Content $settings -Raw | ConvertFrom-Json
} else {
    $json = [PSCustomObject]@{}
}

if (-not $json.PSObject.Properties['hooks']) {
    $json | Add-Member -NotePropertyName 'hooks' -NotePropertyValue ([PSCustomObject]@{})
}
if (-not $json.hooks.PSObject.Properties['SessionStart']) {
    $json.hooks | Add-Member -NotePropertyName 'SessionStart' -NotePropertyValue @()
}

$cmd = 'powershell -NoProfile -File "' + ($dstHook -replace '\\','/') + '"'
$existing = @($json.hooks.SessionStart) | Where-Object {
    $_.hooks | Where-Object { $_.command -eq $cmd }
}

if ($existing) {
    Write-Host "settings.json: SessionStart entry already registered"
} else {
    $entry = [PSCustomObject]@{
        matcher = '*'
        hooks   = @([PSCustomObject]@{
            type    = 'command'
            command = $cmd
            timeout = 15
        })
    }
    $json.hooks.SessionStart = @(@($json.hooks.SessionStart) + $entry)
    $json | ConvertTo-Json -Depth 20 | Set-Content $settings -Encoding UTF8
    Write-Host "settings.json: SessionStart entry added"
}

Write-Host ""
Write-Host "Done. Open /hooks in Claude Code (or restart) to load the hook."
