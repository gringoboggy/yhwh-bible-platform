# Round-8 parallel deep-audit — fresh-session runbook (2026-06-15)

**Status:** READY — engine at `ROUND=8`, `NOW=2026-06-15` in `.claude/workflows/deep-audit.js`.
**Do NOT start fixes** until user approves the merged findings plan.

## Auditor location

| Piece | Path |
|---|---|
| Engine | `.claude/workflows/deep-audit.js` |
| Merge | `.claude/workflows/deep-audit-merge.js` |
| Protocol (split lanes) | `docs/superpowers/plans/2026-06-08-round6-split-audit-plan.md` |
| Program context | `docs/superpowers/plans/2026-06-10-full-project-audit-program.md` |
| Resume command | `.claude/commands/resume.md` |

## Round-8 focus

Post-K-R15 edition-isolation / cross-bleed sweep. `popup-integrity` and `rx-surfaces` hunt
**regressions and bleed across editions**, not re-litigation of K-R13/14/15 fix arcs (see
`DEFERRED_BY_DESIGN` in the engine).

## Parallel session — one fresh Grok/Claude session per box

### Both boxes (start)

1. `git fetch origin && git fetch github`
2. `py -3 scripts/lane_ping.py` — if BEHIND → `git pull --rebase origin main`
3. `py -3 scripts/lane_handoff.py status` + read your section in `dev/LANE_HANDOFF.md`
4. `py -3 scripts/lane_handoff.py mark-seen`

### Local-only LANE flip (never commit)

Edit **one line** in `.claude/workflows/deep-audit.js`:

- **Windows (N95 / Grok):** `const LANE = 'mac' → 'win'`  (use `'win'`)
- **Mac (iMac / Grok):** `const LANE = 'mac'`

This auto-picks `REPO` + sub-agent types (`REPO_BY_LANE`, `AGENTS_BY_LANE`).

### Launch

```
Workflow({ scriptPath: "<repo>/.claude/workflows/deep-audit.js" })
```

**Startup-log tripwire:**

| Lane | Expected dim count | Dimensions |
|---|---|---|
| **win** | **7** | `tests-run`, `opt-build`, `byte-stability`, `rx-surfaces`, `claude-setup`, `popup-integrity`, `github-gitlab` |
| **mac** | **14** | `correctness`, `security`, `code-debt`, `tests`, `docs`, `data-validity`, `concurrency-caching`, `cross-module`, `marathon-boundary`, `dist-packaging`, `website-deploy`, `opt-vision`, `opt-ingest`, `opt-render` |

If the log echoes **18** dims, the LANE edit did not take — fix before running.

### Outputs

- **Mac:** write survivors to `_audit-split/findings-mac.json`, push branch `lane-transfer/audit`
- **Win:** keep survivors locally until Mac branch is in hand

### Merge (Windows, after both complete)

1. Pull `lane-transfer/audit` → read `findings-mac.json` `.survivors`
2. Paste `WIN_SURVIVORS` + `MAC_SURVIVORS` into `.claude/workflows/deep-audit-merge.js`
3. `Workflow({ scriptPath: ".../deep-audit-merge.js" })`
4. Write `result.fixesPlanMarkdown` → `docs/superpowers/notes/2026-06-15-round8-split-audit-findings.md`
5. Delete `lane-transfer/audit` branch. **STOP — present findings only.**

### Mac meantime backlog (if win still grinding)

See `docs/superpowers/plans/2026-06-08-round6-split-audit-plan.md` §Meantime backlog
(render-then-diagnose title pages, website a11y pass, memory hygiene — all read-only).

## Cost / stability

- Finders + verifiers pinned to sonnet in-engine; cap = 2 concurrent on N95
- Sleep/hibernate OFF; keep terminal open
- **FINDINGS-ONLY** — no fix implementation until user approves merged plan

## Deferred (not in this audit run)

- EPUB modest colour: non-native ToC, pills, matter pages (K-R16)
- Per-book title cover art refresh (`content/covers/_book_defaults/` + 21 Ethiopic extras)
- Translation popup letter-spacing polish (Kobo `kobo_img/4.png` baseline)