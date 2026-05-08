# Scope addendum — ω cluster: robustness sweep

**Added:** 2026-05-08, after Tier A foundations shipped.
**Origin:** user request — *"unbreakable as much as a program can be."*

The platform is mostly defensive already (atomic writes via
`notes_io.atomic_write`, ensure_backup before destructive writes,
input validation on the cover-upload pipeline, the four-tier
guardrail system per CLAUDE_PROJECT_RULES §15). This cluster
finishes the sweep across surfaces that haven't yet been audited
through that lens.

## Goal

Every error path is handled gracefully (no 500s with stack traces
in the wfile, no UI dead-ends, no half-written state). Every
external dependency (network, filesystem, subprocess) has a
defined timeout and retry policy. Every long operation can be
interrupted and resumed. After any crash, the next launch detects
it and offers recovery.

## Sub-phase order

```
ω.8   Error-boundary audit (API + UI)         ~ 1 session · LOW
      Every API endpoint: catches Exception, returns a structured
      {error, message} JSON with appropriate HTTP code. No raw
      tracebacks reaching the browser. Already-followed §9 pattern;
      ω.8 sweeps the codebase to confirm and patch outliers.
      Every UI fetch(): handles network failure with a clear
      message; no hung "loading…" states. window.ebible.safeFetch
      already wraps this — ω.0.6 frontend-defense work — but not
      every console uses it. ω.8 finishes the migration.
      Pre-v1.0: YES.
      Deliverables: lint check that every fetch() call site uses
                    safeFetch (or has an explicit catch);
                    integration test that triggers a server error
                    on each endpoint and verifies the UI shows a
                    user-friendly message.

ω.9   Atomic-write + ensure_backup audit       ~ ½ session · LOW
      Every destructive disk write must go through atomic_write
      (text) / atomic_write_bytes (binary), preceded by
      ensure_backup for any pre-existing file. The CLAUDE_PROJECT_
      RULES §7.1 says this; ω.9 verifies it across the codebase
      and patches any direct open(...).write(...) escapees.
      Pre-v1.0: YES.
      Deliverables: lint check `check_atomic_writes` —
                    grep for open(..., 'w') / 'wb') outside
                    notes_io.py and assert each is wrapped or
                    explicitly waived (a comment marking it
                    intentional). Test that simulates a crash
                    mid-write and verifies the cache survives.

ω.10  Retry & timeout policy                  ~ 1 session · LOW
      Every external call (urllib in fetch_sources.py, future
      LibriVox in ρ.1, future commentary fetchers in χ.2-5) must
      have a configured timeout AND a documented retry policy.
      Today timeouts are inconsistent (30s in some places, none
      in others) and retries are nonexistent. ω.10 introduces a
      tiny scripts/core/http.py wrapper:
        - get(url, *, timeout=30, retries=2, backoff=1.5) -> bytes
        - get_json(url, ...) -> dict
        - post(...) for any future write APIs
      Existing call sites migrate; subprocess timeouts in
      build_edition.py get the same treatment.
      Pre-v1.0: YES (otherwise a transient network blip during
                a fetch hangs the platform).
      Deliverables: scripts/core/http.py + migration; tests cover
                    timeout, retry-on-503, no-retry-on-404,
                    backoff exponential.

ω.11  Recovery doc + helpers                  ~ ½ session · LOW
      A dev/RECOVERY.md doc that walks the user through common
      failure modes:
        - "I deleted a notes file" → restore from .backups/
        - "A build hung" → kill + clean /tmp/full_*
        - "The repo is in a weird state" → git reset to last
          known good
        - "An EPUB build produced garbage" → check
          attribution-audit + lint_rules first
      Plus a scripts/recover.py helper that automates the
      .backups/ restoration step (lists available snapshots per
      file, restores by index).
      Pre-v1.0: helpful, not strictly required.
      Deliverables: dev/RECOVERY.md; scripts/recover.py; tests.

ω.12  Crash-safe state                        ~ 1 session · MED
      Long operations (build, batch_promote_xrefs, scaffold_console
      with --apply) currently have no crash-safety: if the process
      dies mid-way, the partial state may not be detectable on
      next launch. ω.12 adds:
        - Lock files at /tmp/ebible-<op>.lock with PID + start
          timestamp; cleaned up on graceful exit.
        - Stale-lock detection on startup (lock present but PID
          dead → "previous run crashed; here's what was open").
        - For multi-step operations, a per-operation journal
          (/tmp/ebible-<op>.journal) that records "step N
          complete" so the next launch can resume rather than
          restart.
      Post-v1.0: the failure modes ω.12 addresses are rare in
                 single-user desktop use; v1.0 ships without it.
      Deliverables: scripts/core/locks.py; integration tests
                    simulating crashes.

ω.13  Performance budgets                     ~ ½ session · LOW
      Each route gets an SLO (response time at corpus scale).
      A new lint check / preflight check warns when an endpoint
      exceeds its budget (measured by the existing _files_signature
      machinery's timing, plus a new test fixture that builds at
      35K-corpus scale).
      Post-v1.0: optimization, not correctness; v1.0 ships even
                 if some endpoints are slow.
      Deliverables: scripts/core/perf_budgets.py; budgets defined
                    per route; preflight integration.
```

## v1.0 inclusion

Pre-v1.0:
- **ω.8** — error boundaries.
- **ω.9** — atomic-write audit.
- **ω.10** — retry & timeout policy.
- ω.11 — recovery doc (cheap, ship if time).

Post-v1.0:
- **ω.12** — crash-safe state.
- **ω.13** — performance budgets.

Updated v1.0 terminus (compounding with ψ cluster):
```
v1.0 = θ.2 + χ.1 + ψ.8 + ψ.10/12/13/14/17
       + ω.8/9/10
       + ξ.1/2/4 (security — see security addendum)
       + corpus ≥ 25K notes
```

## Tests / acceptance criteria

- Every API endpoint has an integration test that triggers an
  exception path and asserts the JSON-shaped error response.
- Every UI fetch() has a unit/integration test for the network-
  failure path.
- A new linter check `check_open_writes` greps for non-atomic
  write call sites.
- A new linter check `check_external_http` greps for direct
  urllib.request usage outside `scripts/core/http.py`.

## Tradeoffs

- **Sweep work, not feature work.** Each phase produces little
  visible UI change but raises the floor of what the platform can
  survive. Easy to under-prioritize; the user explicitly asked for
  it, so we ship.
- **The retry policy can mask transient issues** — a flaky source
  that *should* be flagged sometimes gets silently retried into
  apparent success. Mitigated by the retry helper logging every
  retry to the existing operator dashboard (ψ.6 /ops).
