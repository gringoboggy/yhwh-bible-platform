# save-all.ps1 — the FULL save (user-directed 2026-05-31): one command, five legs.
#
#   Leg 1  local commit         (delegates to save.ps1 — 200-file guard, pre-commit hook)
#   Leg 2  git push origin      (GitLab — the code home)
#   Leg 3  git push github      (GitHub mirror)
#   Leg 4  git bundle --all      -> external drive E:
#   Leg 5  copy that bundle      -> external drive F:
#
# "save" = "commit" = "push" = "backup" all mean THIS (CLAUDE_PROJECT_RULES §4).
# Every leg is verified; a failed or unavailable leg is reported and the rest
# still run; the script exits 1 if ANY leg did not land, so an incomplete save is
# never reported as complete. Use -DryRun to preview without changing anything.
#
# Usage:
#   pwsh -File save-all.ps1 -Message "your message"
#   pwsh -File save-all.ps1 -Message "msg" -Label short-label   # bundle label
#   pwsh -File save-all.ps1 -DryRun                              # preview only
#   pwsh -File save-all.ps1 -Message "big sweep" -Yes            # allow >200 files

param(
    [string]$Message,
    [string]$Label,
    [switch]$Yes,
    [switch]$DryRun
)

Set-Location $PSScriptRoot
$env:GIT_TERMINAL_PROMPT = '0'
$env:GCM_INTERACTIVE = 'never'

$failures = @()
function Leg($n, $name) { Write-Host ("`n=== Leg {0}/5 - {1} ===" -f $n, $name) -ForegroundColor Cyan }
function Ok($m) { Write-Host ("  OK: {0}" -f $m) -ForegroundColor Green }
function Bad($m) { Write-Host ("  FAIL: {0}" -f $m) -ForegroundColor Red }
function Skip($m) { Write-Host ("  SKIP: {0}" -f $m) -ForegroundColor Yellow }

if ($DryRun) { Write-Host "DRY RUN - nothing will be committed, pushed, or written." -ForegroundColor Magenta }

# ---------------------------------------------------------------- Leg 1: commit
Leg 1 "local commit (save.ps1)"
if ($DryRun) {
    $pending = git status --porcelain
    $n = (($pending | Where-Object { $_ }) | Measure-Object).Count
    if ($n -gt 0) { Write-Host ("  would commit {0} changed path(s)" -f $n) } else { Write-Host "  working tree clean - would skip commit, still push/bundle" }
}
else {
    # Hashtable splat for the NAMED -Message param (array splat would pass it
    # positionally, so save.ps1 would receive the literal string "-Message").
    # The --yes flag goes positionally into save.ps1's $args.
    $named = @{}
    if ($Message) { $named['Message'] = $Message }
    $extra = @()
    if ($Yes) { $extra += '--yes' }
    & "$PSScriptRoot\save.ps1" @named @extra
    if ($LASTEXITCODE -ne 0) {
        Bad "commit (save.ps1 exit $LASTEXITCODE) - aborting before push/bundle"
        exit 1
    }
    Ok "commit leg done (committed, or nothing to commit)"
}

# Truth-record rotation is now a MANUAL tool only (run `py -3 scripts/rotate_truth_records.py --apply`
# when the truth_record_budget lint actually trips). The old per-save auto-commit was removed
# 2026-06-20 — it produced 66 "chore: rotate truth records" churn commits during the runaway loop.

# Resolve bundle name from the (possibly new) HEAD.
$short = (git rev-parse --short HEAD 2>$null)
if ($short) { $short = $short.Trim() } else { $short = 'unknown' }
$date = Get-Date -Format 'yyyy-MM-dd'
if (-not $Label) {
    if ($Message) {
        $slug = ($Message -replace '[^a-zA-Z0-9]+', '-').Trim('-').ToLower()
        if ($slug.Length -gt 40) { $slug = $slug.Substring(0, 40).Trim('-') }
        $Label = if ($slug) { $slug } else { 'save' }
    }
    else { $Label = 'save' }
}
$bundleName = "YHWH-v2.4-repo-$date-$Label-$short.bundle"

# ----------------------------------------- Pre-push: lane sync radar (the "ping")
# Before pushing a milestone, check whether the OTHER lane (mac<->win) has pushed
# since our last fetch (cheap `git ls-remote`). If so, rebase our unpushed local
# commits onto it FIRST (lanes are file-disjoint -> safe) so the push to the
# protected GitLab main fast-forwards instead of being rejected. See RULES s4.
Write-Host "`n=== Pre-push: lane sync radar (ping) ===" -ForegroundColor Cyan
if ($DryRun) { Write-Host "  would: py -3 scripts/lane_ping.py --before-push  (+ auto git pull --rebase if BEHIND)" }
else {
    & py -3 "$PSScriptRoot\scripts\lane_ping.py" --before-push
    $ping = $LASTEXITCODE
    if ($ping -eq 10) {
        Write-Host "  other lane has pushed -> git pull --rebase origin main" -ForegroundColor Yellow
        git pull --rebase origin main
        if ($LASTEXITCODE -ne 0) {
            git rebase --abort *> $null
            Bad "auto pull --rebase failed (conflict?) - resolve manually, then re-run save-all.ps1; NOT pushing"
            exit 1
        }
        Ok "rebased local commits onto the other lane's pushed main"
    }
    elseif ($ping -eq 2) { Skip "remote unreachable - proceeding (the push leg will fail loudly if truly offline)" }
    else { Ok "in sync with both remotes - clear to push" }
}

# ------------------------------------------------------- Leg 2: push origin (GitLab)
Leg 2 "push origin (GitLab)"
if ($DryRun) { Write-Host "  would: git push origin main" }
else {
    git push origin main
    if ($LASTEXITCODE -eq 0) { Ok "GitLab up to date" } else { Bad "push origin"; $failures += 'push origin (GitLab)' }
}

# ------------------------------------------------------- Leg 3: push github (GitHub)
Leg 3 "push github (GitHub)"
if ($DryRun) { Write-Host "  would: git push github main" }
else {
    git push github main
    if ($LASTEXITCODE -eq 0) { Ok "GitHub up to date" } else { Bad "push github"; $failures += 'push github (GitHub)' }
}

# ------------------------------------------------------------- Leg 4: bundle -> E:
Leg 4 "git bundle --all -> E:"
$ePath = "E:\$bundleName"
if (-not (Test-Path 'E:\')) { Skip "E: not mounted (optional per LANE_HANDOFF STANDING; pushes still count as success)" }
elseif ($DryRun) { Write-Host ("  would: git bundle create {0} --all" -f $ePath) }
else {
    git bundle create "$ePath" --all
    if ($LASTEXITCODE -eq 0 -and (Test-Path $ePath)) {
        git bundle verify "$ePath" *> $null
        if ($LASTEXITCODE -eq 0) { Ok $bundleName } else { Bad "E: bundle verify"; $failures += 'E: bundle verify' }
    }
    else { Bad "E: bundle create"; $failures += 'E: bundle create' }
}

# --------------------------------------------------------------- Leg 5: copy -> F:
Leg 5 "copy bundle -> F:"
$fPath = "F:\$bundleName"
if (-not (Test-Path 'F:\')) { Skip "F: not mounted (optional per LANE_HANDOFF STANDING; pushes still count as success)" }
elseif ($DryRun) { Write-Host ("  would: copy bundle -> {0}" -f $fPath) }
elseif (Test-Path $ePath) {
    Copy-Item -LiteralPath "$ePath" -Destination "$fPath" -Force
    if (Test-Path $fPath) { Ok "F: copy" } else { Bad "F: copy"; $failures += 'F: copy' }
}
else {
    # E: was unavailable - create the bundle directly on F: so a backup still lands.
    git bundle create "$fPath" --all
    if ($LASTEXITCODE -eq 0 -and (Test-Path $fPath)) { Ok "F: bundle (created directly; E: unavailable)" }
    else { Bad "F: bundle"; $failures += 'F: bundle' }
}

# ------------------------------------------------------------------------ Summary
Write-Host "`n=== save-all summary ===" -ForegroundColor Cyan
git status -b --porcelain=v1 | Select-Object -First 1
if ($DryRun) { Write-Host "DRY RUN complete - no changes made." -ForegroundColor Magenta; exit 0 }
if ($failures.Count -eq 0) {
    Write-Host "FULL SAVE COMPLETE - core legs landed (local + GitLab + GitHub; E:/F: bundles optional on WIN per STANDING)." -ForegroundColor Green
    exit 0
}
else {
    Write-Host ("INCOMPLETE SAVE - {0} leg(s) did not land: {1}" -f $failures.Count, ($failures -join '; ')) -ForegroundColor Red
    Write-Host "Fix the cause (mount the drive / restore the connection) and re-run save-all.ps1." -ForegroundColor Yellow
    exit 1
}
