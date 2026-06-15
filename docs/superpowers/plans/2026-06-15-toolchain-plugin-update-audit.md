# Toolchain + IDE plugin update audit (next fresh session)

**Status:** ACTIVE 2026-06-15 — next fresh-session first task for Grok (Windows lane); run before Kobo round-9 ingest or M3 catalog.

**Owner:** Grok (Windows lane) — run **before** resuming Kobo round-9 device QA ingest or M3 work.  
**Goal:** Confirm every editor, agent harness, plugin, skill, and CLI extension is current; document drift; apply safe updates only.

## Scope

| Area | Paths / sources |
|---|---|
| **Cursor / VS Code** | User settings, extensions list, `.vscode/` if present |
| **Grok CLI** | `~/.grok/skills/`, bundled skills, `grok` version |
| **Claude Code** | `~/.claude/plugins/`, project `.claude/`, `CLAUDE.md`, hooks, MCP |
| **Kilo** | Kilo-specific config if installed (check user profile) |
| **Project harness** | `YHWH v2.4/.githooks`, `dev/TOOLCHAIN.md`, `scripts/lint_rules.py` plugin refs |
| **Python toolchain** | `.venv`, `requirements*.txt`, ruff, epubcheck, kepubify |
| **Node CI** | `.github/workflows/`, `website/package.json` |
| **MCP servers** | `mcps/`, chrome-devtools-mcp, project `.mcp.json` |

## Procedure (ordered)

1. **Inventory** — export current versions (no upgrades yet):
   - `code --list-extensions --show-versions` (or Cursor equivalent)
   - `py -3 --version`; `kepubify --version`; `java -version` (epubcheck)
   - `gh --version`; `git --version`
   - Read `dev/TOOLCHAIN.md` and diff against live `where`/`Get-Command` output
2. **Claude / Grok skills** — list installed marketplace plugins; note versions in frontmatter; flag duplicates (e.g. superpowers vs project-local copies)
3. **Check for updates** — extension marketplace, `pip list --outdated` (venv only), `npm outdated` in website/, GitHub Action runner bumps
4. **Risk classify** — GREEN = patch/doc only; YELLOW = extension minor; RED = major Python/Node/kepubify (needs regression: `pytest tests/test_file_split.py`, one `build_kobo_marker_ab` smoke)
5. **Apply GREEN/YELLOW** — one category per commit; re-run `lint_rules.py` + targeted tests after each
6. **Record** — append results to `dev/TOOLCHAIN.md` + `dev/CHANGELOG.md` bullet; if RED deferred, add to `dev/IN_FLIGHT.md` backlog

## Acceptance

- Written report: what was checked, what updated, what deferred, exact versions after
- No silent skill/plugin drift (stale MCP descriptors, broken hook paths)
- YHWH build gates still green after any applied update

## Non-goals

- Do not change YHWH edition content or Kobo study UX in this pass
- Do not auto-update RED items without user ack