# Post-flight: verify all 20 M3 kepubs exist + epubcheck 0/0/0/0 + K-R2 GREEN.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot/..
$env:PYTHONUTF8 = "1"
$dir = "build/matrix-m3"
$list = Get-Content "dev/M3_Kobo_Assets_v0.1.0.txt" | Where-Object { $_ -match '\.kepub\.epub$' }
$missing = @()
$failEc = 0
$log = "dev/m3_e2e_verify.log"
"[$(Get-Date -Format o)] START e2e verify $($list.Count) assets" | Tee-Object -FilePath $log
foreach ($name in $list) {
    $path = Join-Path $dir $name
    if (-not (Test-Path $path)) {
        $missing += $name
        "[$(Get-Date -Format o)] MISSING $name" | Tee-Object -FilePath $log -Append
        continue
    }
    "[$(Get-Date -Format o)] epubcheck $name" | Tee-Object -FilePath $log -Append
    py -3 scripts/epubcheck.py --require --strict $path 2>&1 | Tee-Object -FilePath $log -Append
    if ($LASTEXITCODE -ne 0) { $failEc++; continue }
    "[$(Get-Date -Format o)] kr2 $name" | Tee-Object -FilePath $log -Append
    py -3 dev/verify_kr2_build.py $path 2>&1 | Tee-Object -FilePath $log -Append
    if ($LASTEXITCODE -ne 0) { $failEc++ }
}
if ($missing.Count) {
    "[$(Get-Date -Format o)] MISSING count=$($missing.Count)" | Tee-Object -FilePath $log -Append
    $missing | ForEach-Object { "[$(Get-Date -Format o)]   $_" | Tee-Object -FilePath $log -Append }
    exit 2
}
"[$(Get-Date -Format o)] DONE gate_fails=$failEc / $($list.Count)" | Tee-Object -FilePath $log -Append
exit $failEc