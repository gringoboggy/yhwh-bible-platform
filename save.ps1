param([string]$Message)

if (-not $Message) {
    $Message = "saved on " + (Get-Date -Format "yyyy-MM-dd HH:mm")
}

# 2026-05-29 mint guard (Task 0.8) — defense-in-depth against a botched commit
# message sweeping stray files via `git add -A` (the spaced-path / arrow-glyph
# hazard). If more than 200 files would stage, list them and require --yes.
$wouldStage = git status --porcelain
$stageCount = (($wouldStage | Where-Object { $_ }) | Measure-Object).Count
if ($stageCount -gt 200 -and $args -notcontains '--yes') {
    Write-Host ("REFUSING: {0} files would stage (> 200). Review the list below; re-run with --yes to proceed." -f $stageCount) -ForegroundColor Red
    $wouldStage | Select-Object -First 50
    if ($stageCount -gt 50) { Write-Host ("... and {0} more" -f ($stageCount - 50)) -ForegroundColor DarkGray }
    exit 1
}

git add -A

$staged = git diff --cached --name-only
if (-not $staged) {
    Write-Host "Nothing changed since the last save." -ForegroundColor Yellow
    exit 0
}

$count = ($staged | Measure-Object).Count
Write-Host ("Saving {0} file(s): {1}" -f $count, $Message) -ForegroundColor Cyan

git commit -m $Message
if ($LASTEXITCODE -ne 0) {
    Write-Host "Commit failed. See message above." -ForegroundColor Red
    exit $LASTEXITCODE
}

# Push step disabled — remote deleted 2026-05-12.
# Re-enable when a new remote is set up.
# git push
# if ($LASTEXITCODE -ne 0) {
#     Write-Host "Push failed. Your work is committed locally; run 'git push' again when the connection is back." -ForegroundColor Red
#     exit $LASTEXITCODE
# }

Write-Host "Saved locally (no remote configured)." -ForegroundColor Green
