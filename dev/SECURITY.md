# Security policy

> **Phase tags:** ξ.5 (this doc) · ξ.3 (CSP headers) · ξ.6 (secrets
> management). See `dev/PLAN_2026-05-09.md` §5.4 for the full
> hardening roadmap (ξ.7-ξ.15 are planned successors).

This document covers the YHWH Bible publishing platform's security
posture: what it protects, what it doesn't, how to report issues,
and which dependencies + env vars are load-bearing.

---

## 1. Threat model

The platform is a **single-user desktop application**. The web UI
binds to localhost:8765 by default (overridable via
`--host`). The threat model is:

- **In scope:** the operator's own browser ↔ the operator's own
  HTTP server. CSRF, clickjacking, XSS in editor consoles, response-
  header tampering by a malicious LAN peer (when the operator
  binds `--host 0.0.0.0`).
- **Out of scope today:** multi-user / multi-tenant access (one
  editor per server); cloud-era attack surface (no cloud deploy
  yet); supply-chain attacks against dependencies (pip-audit
  follow-on in ξ.11).

The `--host 0.0.0.0` flag is the documented escape valve for LAN-
share workflows; setting it shifts the threat model toward
network-peer concerns. The CSP headers (ξ.3) and admin-token gate
(`EBIBLE_ADMIN_TOKEN`) cover the most common LAN exposures.

---

## 2. Reporting a vulnerability

Please report security issues privately:

- Email the maintainer directly. Do **not** post details to
  public issue trackers.

We aim to acknowledge reports within 7 days and ship a fix or
mitigation within 30 days for confirmed issues. Coordinated
disclosure timelines are negotiable for severe issues.

---

## 3. Runtime dependencies

Pinned in `requirements.txt`. Per CLAUDE_PROJECT_RULES §10, the
project intentionally avoids heavy frameworks (Flask / FastAPI /
Django) and uses the Python standard library for the HTTP server.

| Package | Floor | Ceiling | Why |
|---|---|---|---|
| **PyYAML** | 6.0 | <7 | YAML parsing for `editions.yaml`, `kinds.yaml`, `scenarios/*.yaml`, `_meta.yaml`. The only mandatory runtime dep. |

Optional / opt-in (commented in `requirements.txt`):

| Package | Why |
|---|---|
| pywebview | θ.2 native desktop shell. Optional — the launcher's `--shell browser` flow uses the system browser instead. |
| pyinstaller | θ.4 single-file binary builds. Build-time only. |
| anthropic | χ-AI-xrefs / χ-AI-notes paid detectors. Cost-gated; only load if you intend to run a paid pass. |

Tooling shipped this hardening arc:

- **ξ.11 — pip-audit wrapper** (`scripts/audit_deps.py`). Run with
  `python scripts/audit_deps.py` after installing pip-audit
  (`pipx install pip-audit`). Exits non-zero on HIGH+ CVEs by
  default; pass `--severity LOW` or `--strict` to gate on lower
  severities. JSON output via `--json` for CI integration.

Future:

- **ξ.12 — bandit SAST.** Scans `scripts/` and `tests/` for unsafe
  Python patterns.

---

## 4. Environment variables

Documented in `.env.example`. The platform reads only project-
prefixed env vars (`YHWH_*` / `EBIBLE_*`) plus a handful of well-
known third-party ones. Never commit a real `.env` file.

| Variable | Required | Purpose |
|---|---|---|
| `YHWH_CONTENT_ROOT` | no | Override the `content/` root path. Useful for tests + multi-checkout dev. Tests use `paths.set_content_root_for_testing()`. |
| `EBIBLE_ADMIN_TOKEN` | conditional | Required when running with `--auth-token` to gate `/api/*` mutations. Without it, the server runs in single-user-localhost mode (no auth needed). |
| `EPUBCHECK_JAR` | no | Path to the IDPF `epubcheck.jar` for EPUB validation. Defaults to a project-relative path. |
| `ANTHROPIC_API_KEY` | conditional | Required only for χ-AI-xrefs / χ-AI-notes detectors. Read at call time. |
| `CODESIGN_IDENTITY` | no | macOS code-signing identity for θ.4 signed builds. Unsigned builds work without it. |
| `NOTARIZE_KEYCHAIN_PROFILE` | no | macOS notarization profile name. Required only for the `notarytool` step in θ.4. |
| `AC_PROFILE` | no | Apple Connect profile alias used by θ.4 signing scripts. |
| `TEAMID` | no | Apple Developer Team ID for θ.4 macOS signing. |

The `.env.example` file lists every variable with a sample value
where the format isn't obvious. Copy it to `.env` and fill in your
own values; `.gitignore` already excludes `.env` so a copy with
real secrets won't be committed accidentally.

---

## 5. Security response headers (ξ.3)

Every HTML and JSON response from the server includes:

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'
X-Content-Type-Options: nosniff
Referrer-Policy: same-origin
```

The Tailwind CDN is intentionally allow-listed (CLAUDE_PROJECT_RULES
§6.3 — no build step). `frame-ancestors 'none'` blocks clickjacking;
`form-action 'self'` blocks form-tampering attacks; `base-uri
'self'` blocks `<base>` tag injection.

The headers are applied via `Handler._send_security_headers()` which
is called from `_send_html`, `_send_json`, `_send_file`, and every
inline-built download response (RSS feed, scenario YAML export,
EPUB download). Tests in `TestXi3CspHeaders` lock in the contract.

A future `ξ.9` phase will add Subresource Integrity hashes for the
Tailwind CDN script tag so a CDN compromise can't serve malicious
JS undetected.

---

## 6. Secrets management (ξ.6)

- **Never commit `.env`.** The `.gitignore` excludes both `.env`
  (exact match) and `*.env` (suffix glob). Always copy from
  `.env.example` rather than starting from a real env.
- **Never log env-var values.** The project's `log_message` calls
  in `scripts/web.py` deliberately don't include any env var
  payloads.
- **Future ξ.6.1 → ξ.14** — OS keychain integration for
  `ANTHROPIC_API_KEY` so the value lives in macOS Keychain /
  Windows Credential Manager / Linux Secret Service rather than
  the shell environment. Reduces "I accidentally committed my
  .env" risk class.

---

## 6.1 Outbound-egress allowlist (ξ.10)

Every outbound HTTP call now goes through
`scripts.core.http.get(url, allowlist=...)`. Calls supplying an
`allowlist` parameter are validated against it BEFORE any network
I/O — non-matching hosts raise `SSRFBlockedError` and never touch
the wire. Subdomain-aware: `example.com` in the allowlist accepts
`api.example.com`, `data.example.com`, etc. Anti-spoof
guard: `evil-example.com` does NOT match `example.com` (only
suffix-with-leading-dot is accepted).

Three pre-built allow-list groups in
`scripts/core/http.py`:

- `DEFAULT_PD_SOURCES_ALLOWLIST` — public-domain source corpora
  (openscriptures.org, ebible.org, archive.org, openbible.info).
- `DEFAULT_AI_BACKEND_ALLOWLIST` — Anthropic API
  (api.anthropic.com).
- `DEFAULT_DESKTOP_UPDATE_ALLOWLIST` — appcast / release hosting
  (provider-specific, configured by deployment).

Calls without an `allowlist` parameter log a warning and
continue (back-compat). A future ξ.10.x can flip this to
fail-closed once every call site has migrated.

---

## 7. Atomic writes + backup invariants

Every file mutation that the project performs goes through one of
two helpers in `scripts/core/notes_io.py`:

- `atomic_write(path, text)` — writes to a temp file then renames,
  so partial writes are impossible.
- `ensure_backup(path)` — creates a timestamped `.bak` file in
  `.backups/` before any destructive write.

The lint rule `check_atomic_writes` in `scripts/lint_rules.py`
enforces that no other code path uses raw `open(path, 'w')`. This
is part of the "structural invariant" tier (CLAUDE_PROJECT_RULES
§15) — the linter catches drift continuously.

---

## 8. Out-of-scope (today)

- **Multi-user authentication / authorization.** Scope-locked
  per CLAUDE_PROJECT_RULES §10: "Not a real-time collab tool. One
  editor at a time." A future `ξ.7` revisit would re-evaluate
  if/when a cloud-hosted variant ships.
- **Database security.** No database. State is files on disk
  (YAML + Python tuple data + JSON candidates).
- **Network security at scale.** Localhost-only by default. The
  `--host 0.0.0.0` LAN-share path is documented as a deliberate
  opt-in.

---

## 9. Quick checklist for contributors

- [ ] All file writes go through `notes_io.atomic_write` /
      `ensure_backup`. (Linter enforces.)
- [ ] All outbound HTTP goes through `scripts/core/http.get`.
      (Linter enforces.)
- [ ] No new env vars added without updating `.env.example` +
      this doc's §4.
- [ ] No new dependency added without updating
      `requirements.txt` + this doc's §3.
- [ ] No raw inline `<script src="...">` from new CDN domains
      without extending the CSP allowlist in
      `scripts/web.py:Handler._CSP_POLICY`.
