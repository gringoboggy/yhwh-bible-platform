# WIN M3 fan-out: 4 canon-differentiated tradition editions × M3 phase (20 kepub assets).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot/..
$env:PYTHONUTF8 = "1"
$out = "build/matrix-m3"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$eds = py -3 scripts/build_format_matrix.py --list-editions | ConvertFrom-Json
$log = "dev/m3_fanout_win.log"
"[$(Get-Date -Format o)] START M3 fan-out $($eds.Count) editions -> $out" | Tee-Object -FilePath $log
$fail = 0
foreach ($ed in $eds) {
    "[$(Get-Date -Format o)] START $ed" | Tee-Object -FilePath $log -Append
    py -3 scripts/build_format_matrix.py --edition $ed --version 0.1.0 --phase M3 --output-dir $out 2>&1 |
        Tee-Object -FilePath $log -Append
    if ($LASTEXITCODE -ne 0) {
        "[$(Get-Date -Format o)] FAIL $ed exit=$LASTEXITCODE" | Tee-Object -FilePath $log -Append
        $fail++
    } else {
        "[$(Get-Date -Format o)] PASS $ed" | Tee-Object -FilePath $log -Append
    }
}
"[$(Get-Date -Format o)] DONE fails=$fail" | Tee-Object -FilePath $log -Append
exit $fail