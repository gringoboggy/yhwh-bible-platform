# Scope addendum — ξ cluster: security hardening

**Added:** 2026-05-08, after Tier A foundations shipped.
**Origin:** user request — *"as unhackable or whatever as it can be."*

The platform binds to localhost by default and is single-user, so
the threat model is narrow. But "narrow" is not "none": a hostile
input file (uploaded JSON, malformed _meta.yaml, crafted note body)
shouldn't be able to escalate beyond reading a file. A misbehaving
mirror serving a fetcher URL shouldn't be able to overwrite arbitrary
disk paths. A Bible verse text rendered into a popup shouldn't be
able to inject JS into the EPUB.

## Threat model (explicit)

In scope (the platform must defend against):
1. **Hostile data files** — a malicious `_meta.yaml`, notes module,
   uploaded JSON, or fetched source file. Must not execute
   arbitrary code; must not escalate disk access beyond
   `content/sources/<id>` for the relevant id.
2. **Path traversal** — a `../` payload in any user-controllable
   filename / book code / source id / cover path.
3. **XSS in EPUB output** — a Bible verse popup containing
   `<script>` (whether deliberately injected or innocently from a
   noisy source) must render as text, not execute.
4. **Resource exhaustion** — an unbounded upload, an unbounded
   pasted URL pointing at a 10 GB file, a recursive YAML reference.

Out of scope (single-user desktop platform):
1. Multi-user authorization (handled by ω.4 if that ever
   reactivates).
2. Network-borne attackers (the server binds 127.0.0.1 by default;
   `--host 0.0.0.0` is conscious opt-in per the existing docs).
3. OS-level privilege escalation (the platform runs as the user;
   not a security boundary the platform owns).

## Sub-phase order

```
ξ.1  Input-validation audit                    ~ 1 session · LOW
     Every API endpoint has a documented input contract; every
     mismatched input returns a 4xx with a clear message instead
     of crashing. The §9 pure-function pattern already does this
     for newer endpoints; ξ.1 sweeps older ones.
     Pre-v1.0: YES.
     Deliverables: per-endpoint input-shape unit tests for every
                   POST/PUT/DELETE; a shared
                   scripts/core/validation.py with primitive
                   validators (book_code, edition_id, kind_id,
                   path_segment); migration of existing ad-hoc
                   checks.

ξ.2  Path-traversal hardening                  ~ ½ session · LOW
     Every endpoint that resolves a user-supplied path against a
     known-safe root (covers, sources cache, future audio):
       - Reject `..`, absolute paths, hidden segments at string
         level BEFORE any resolution.
       - Resolve via Path.resolve() and verify
         relative_to(safe_root) succeeds.
       - Reject symlinks that escape (Windows symlink trickery
         is real).
     The §9 "Add a new static-file route" recipe already specifies
     this; ξ.2 confirms every existing route follows it.
     Pre-v1.0: YES.
     Deliverables: shared scripts/core/safe_path.py; existing
                   route migrations; per-route tests.

ξ.3  Content-Security-Policy headers           ~ ½ session · LOW
     HTML responses get a CSP header restricting:
       - script-src to 'self' + cdn.tailwindcss.com (the only
         current CDN dep) + 'sha256-…' for the inline scripts
         the consoles use (ω.0.6 prelude, init blocks).
       - style-src to 'self' + 'unsafe-inline' (Tailwind requires
         this; documented exception).
       - img-src 'self' data:.
       - connect-src 'self'.
       - frame-ancestors 'none' (no embedding).
     Pre-v1.0: nice-to-have; ships when convenient.
     Deliverables: _send_html method adds CSP header; smoke test
                   verifies no console regresses.

ξ.4  XSS prevention sweep                      ~ 1 session · LOW
     ω.0.7 consolidated the escape helper but didn't audit every
     call site. ξ.4 finishes:
       - Every user-controllable string in rendered HTML uses
         window.ebible.escapeHtml (or template-string equivalent).
       - Every user-controllable string in BUILT EPUB output goes
         through the same sanitization. Specifically: note bodies
         can contain HTML by design (publishers author rich apparatus),
         but the build pipeline must whitelist tags (a → ['href',
         'class'], em / strong / p / span / etc.) and strip
         <script>, <iframe>, on* attributes.
       - A new linter check `check_unescaped_template_strings`
         flags any backtick-template-string in console JS that
         interpolates user data without escapeHtml.
     Pre-v1.0: YES (uploaded JSON / hand-authored notes can carry
               malicious HTML; we must neutralize at the render
               boundary).
     Deliverables: bumped sanitizer; linter check; unit tests
                   covering known XSS payload classes.

ξ.5  Dependency hygiene                        ~ ½ session · LOW
     The platform's runtime deps are stdlib + pyyaml + reportlab
     + (test only) pytest. Add:
       - requirements.txt with explicit versions (so reproducible
         builds become possible later).
       - A note in dev/SECURITY.md about the supply chain (how
         to audit, where to report issues, no automated upgrades).
     Pre-v1.0: nice-to-have.
     Deliverables: requirements.txt; dev/SECURITY.md; preflight
                   check that warns when an installed package
                   version drifts from requirements.txt.

ξ.6  Secrets management                        ~ ½ session · LOW
     Currently no secrets in repo (verified during σ.3). ξ.6 makes
     this durable:
       - .env.example template documenting EBIBLE_ADMIN_TOKEN
         and any future secrets.
       - A pre-commit hook addition that greps staged content for
         AWS-key shapes, GitHub tokens, etc. (gitleaks-style
         patterns; reuses existing pre-commit).
     Pre-v1.0: nice-to-have.
     Deliverables: .env.example; updated pre-commit hook;
                   tests verifying the gitleaks-style patterns
                   match real leaks and don't false-positive on
                   common code.

ξ.7  Auth-gate re-evaluation                   ~ ½ session · LOW
     ω.4 deferred auth gate on mutations; ξ.7 documents the
     decision precisely (single-user desktop = no auth needed)
     and adds a clear opt-in path for any future cloud / shared
     deployment. Specifically:
       - dev/SECURITY.md documents the threat model.
       - The existing EBIBLE_ADMIN_TOKEN code path is verified
         to actually work end-to-end (it shipped but never had
         an integration test that exercises a real Bearer auth
         round trip).
       - Document the Tor / SSH-tunnel pattern for any user who
         needs remote access without exposing the platform.
     Post-v1.0: documentation + verification, no new code.
     Deliverables: dev/SECURITY.md; auth integration test.
```

## v1.0 inclusion

Pre-v1.0:
- **ξ.1** — input validation.
- **ξ.2** — path traversal.
- **ξ.4** — XSS prevention.

Pre-v1.0 if time:
- ξ.3 — CSP headers.
- ξ.5 — dependency hygiene.
- ξ.6 — secrets management.

Post-v1.0:
- ξ.7 — auth-gate re-evaluation.

## Tests / acceptance criteria

- Every endpoint has a "hostile input" unit test (oversized,
  malformed, traversal payload, XSS payload).
- The build pipeline has an XSS smoke test: feed a note body
  containing `<script>alert(1)</script>` and assert the EPUB
  output strips it.
- The linter gains:
  - `check_unsafe_path_resolutions` — every Path() call that
    consumes user data must follow the §9 recipe.
  - `check_unescaped_template_strings` — every backtick-template
    JS string interpolating user data must escape.
  - `check_open_writes` — already proposed under ω.9.

## Tradeoffs

- **Whitelist HTML in note bodies, not strip-everything.** Notes
  legitimately contain rich apparatus (`<em>`, `<a>`, etc.).
  Stripping all HTML breaks the editorial output. Whitelist-based
  sanitization is more work but preserves the product. Use
  Python's html.parser + an allowlist; stdlib only.
- **CSP is an iterative game.** Once added, every UI change that
  introduces new CDN dependencies (none planned) needs a CSP
  update. Documented in dev/SECURITY.md so future changes don't
  silently drop security.
- **No security-without-end-game.** The threat model above is
  explicit; "as secure as possible" is meaningless without a
  named threat. ξ.* phases each defend against named threats from
  the list, not theoretical attackers.
