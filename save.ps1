param([string]$Message)

if (-not $Message) {
    $Message = "saved on " + (Get-Date -Format "yyyy-MM-dd HH:mm")
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
