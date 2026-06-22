# ---------------------------------------------------------------------------
# LANE IDENTITY -- which Claude am I? (Mac vs Windows). Derived, not assumed:
#   dev/.lane = authoritative per-machine marker (gitignored); OS cross-check.
# This file is the WINDOWS bootstrap, so the expected lane is "windows"; warn
# on any mismatch so a misconfigured machine is caught before it pushes/hands
# off. Non-fatal (try/catch). Kept in lane-v2 parity with the Mac bootstrap-triad.sh banner.
# ---------------------------------------------------------------------------
try {
    $scriptLane = 'windows'
    $rr1 = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    $rr2 = Join-Path $rr1 'YHWH v2.4'
    $repoL = if     (Test-Path (Join-Path $rr1 'dev\.lane')) { $rr1 }
             elseif (Test-Path (Join-Path $rr2 'dev\.lane')) { $rr2 }
             elseif (Test-Path (Join-Path $rr1 'dev'))       { $rr1 }
             elseif (Test-Path (Join-Path $rr2 'dev'))       { $rr2 } else { $rr1 }
    $laneFile = Join-Path $repoL 'dev\.lane'
    $lane = if (Test-Path $laneFile) { (Get-Content -Raw $laneFile).Trim() } else { '' }
    $laneEff = if ($lane) { $lane } else { $scriptLane }
    $osName  = if ($env:OS) { $env:OS } else { 'unknown' }
    Write-Output '==================== LANE IDENTITY -- WHO AM I? ===================='
    Write-Output ("  >>> You are {0} CLAUDE  (dev/.lane='{1}', OS={2})" -f $laneEff.ToUpper(), $(if ($lane) { $lane } else { '<missing>' }), $osName)
    if (-not $lane) {
        Write-Output ("  note: dev/.lane missing -> assuming this machine is the {0} lane." -f $scriptLane)
        Write-Output ("        create it once with:  Set-Content -NoNewline dev/.lane '{0}'" -f $scriptLane)
    } elseif ($lane -ne $scriptLane) {
        Write-Output ("  !! MISMATCH: this is the WINDOWS bootstrap but dev/.lane says '{0}'." -f $lane)
        Write-Output '     Confirm which lane you really are BEFORE pushing or handing off.'
    }
    Write-Output '  Lane rule (v2): mode=parallel -> file-disjoint, BOTH lanes push their own milestones;'
    Write-Output '  only the TRUTH_OWNER edits SESSION_STATE/IN_FLIGHT/CHANGELOG (see LANE_HANDOFF frontmatter).'
    Write-Output '==================================================================='
} catch { }

Write-Output @'
================ YHWH PROJECT BOOTSTRAP -- DO THIS FIRST ================
Before any other tool call or response this session, READ THE TRIAD IN ORDER:
  1. YHWH v2.4/dev/CLAUDE_PROJECT_RULES.md       (rules + conventions + mental models)
  2. YHWH v2.4/dev/SESSION_STATE.md              (latest snapshot: shipped / next / test count)
  3. YHWH v2.4/dev/PLAN_2026-05-29-roadmap.md    (master forward sequence)

"continue" / "push" / "go ahead" at the start of a FRESH session MEANS:
"read the triad first, THEN resume the in-flight work." It does NOT mean
skip orientation. A quick git-log or a SESSION_STATE-only peek is NOT a
substitute for the full triad read.

This IS the minimum orientation (the triad is ~700-900 lines, by design).
Terseness / bias-to-action applies to what comes AFTER: do not then read the
whole tree, plans, or runner code "to be safe" -- pull deeper reading lazily,
per step. After the triad, confirm in ONE line (which phase; what is next),
reconcile dev/IN_FLIGHT.md if its TRACKER-STATE is active, then proceed.

After the triad + BEFORE resuming work, also: (a) AGGRESSIVELY free RAM -- end
every process NOT needed for Windows / the internet / Claude / Claude's toolchain.
PROTECT (never kill): claude, the node/MCP processes, the pwsh+powershell+
WindowsTerminal+explorer session tree, MsMpEng/AV, the svchost network stack.
KILL (recoverable bloat): 0-window background browsers, msedgewebview2, iCloud/
OneDrive sync, vendor updaters, M365Copilot/Widgets/AppActions/Cross-Device, the
respawning shell hosts. See RULES section 0 "Session-start RAM clear". Then (b)
the env-health check (Claude Code + plugin updates -- apply only on user OK; MCP
servers connected). Report freed RAM in the one-line confirmation.
========================================================================
'@

# --- Memory self-maintenance (local, non-fatal): surface memory drift so it
# gets reconciled. Read-only audit; prints ONLY when a real (warn) issue exists.
# Never breaks session start (try/catch swallows all errors). See
# dev/cc-hooks/memory_hygiene.py + the memory-reconcile workflow. ---
try {
    $hyg = $null
    $cand1 = Join-Path $PSScriptRoot 'memory_hygiene.py'                                                            # source location
    $cand2 = Join-Path (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) 'YHWH v2.4') 'dev\cc-hooks\memory_hygiene.py'  # installed-copy location
    if (Test-Path $cand1) { $hyg = $cand1 } elseif (Test-Path $cand2) { $hyg = $cand2 }
    if ($hyg) {
        $mem = & py -3 $hyg audit --quiet 2>$null
        if ($mem) {
            Write-Output ''
            Write-Output '----- MEMORY HYGIENE (drift detected -- reconcile when convenient) -----'
            Write-Output $mem
            Write-Output 'Full report: py -3 "dev/cc-hooks/memory_hygiene.py" audit  |  Deep sweep: Workflow memory-reconcile  |  Back up: ...memory_hygiene.py backup'
        }
    }
} catch { }

# --- Env health (read-only, non-fatal): Claude Code version + plugins. Updates
# apply ONLY on user OK (RULES section 0). MCP is NOT auto-listed: `claude mcp
# list` health-checks by LAUNCHING each server -- run it manually to verify.
# `claude --version`/`plugin list` don't start a session, so no hook recursion. ---
try {
    Write-Output ''
    Write-Output '==================== ENV HEALTH ===================='
    Write-Output ("  Claude Code: " + ((claude --version 2>$null) | Select-Object -First 1))
    Write-Output '  Plugins:'
    (claude plugin list 2>$null) | ForEach-Object { Write-Output ("    " + $_) }
    Write-Output '  updates -> apply Claude Code / plugin updates only on user OK'
    Write-Output "  MCP     -> run 'claude mcp list' to verify servers (not auto-run: it launches them)"
    Write-Output '==================================================='
} catch { }

# --- Lane-handoff baton incoming check (local, non-fatal): surface a baton the
# OTHER workstation (Mac) handed to this lane. Read-only fetch + check; prints
# ONLY when an incoming baton is pending. Never breaks session start. See
# scripts/lane_handoff.py + docs/superpowers/specs/2026-06-03-lane-handoff-baton-system-design.md ---
try {
    $r1 = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    $r2 = Join-Path $r1 'YHWH v2.4'
    $repo = if (Test-Path (Join-Path $r1 'scripts\lane_handoff.py')) { $r1 }
            elseif (Test-Path (Join-Path $r2 'scripts\lane_handoff.py')) { $r2 } else { $null }
    if ($repo) {
        git -C "$repo" fetch origin --quiet 2>$null
        $banner = & py -3 (Join-Path $repo 'scripts\lane_handoff.py') incoming 2>$null
        if ($LASTEXITCODE -eq 0 -and $banner) {
            Write-Output ''
            Write-Output $banner
            Write-Output 'Run /resume to pull + combine the incoming work.'
        }
    }
} catch { }

# --- Lane sync RADAR (seam check + AUTO-PULL; local, non-fatal): the STANDING
# "just pull, never ask" directive AUTO-PULLS (--rebase onto origin/main; auto-commits a
# dirty tree FIRST when a pull is needed) so the user never types "pull". Multi-remote-safe
# (origin + github); read-only no-op when CLEAR; non-fatal. Session-start SEAM, NOT a
# persistent background watcher (the loop machinery stays removed). Supersedes the old
# report-only lane_ping --quiet block here; lane_watch wraps lane_ping + lane_handoff
# incoming + the auto-pull. Mirrors bootstrap-triad.sh (Mac parity, 2026-06-22).
# See scripts/lane_watch.py (check(auto_pull=True)) + RULES s4 (auto-pull-on-BEHIND). ---
try {
    $lw = Join-Path (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) 'YHWH v2.4') 'scripts\lane_watch.py'
    if (Test-Path $lw) {
        Write-Output ''
        Write-Output '----- LANE SYNC RADAR (seam check + auto-pull) -----'
        & py -3 $lw --once --auto-pull 2>$null
    }
} catch { }
