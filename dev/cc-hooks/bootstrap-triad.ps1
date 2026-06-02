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
