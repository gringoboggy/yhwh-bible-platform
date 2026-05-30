# SCOPE addendum — ξ.18.x style-src tightening (trade-off captured)

**Date:** 2026-05-12
**Parent phase:** ξ.18 (CSP nonces on script-src — shipped 2026-05-12)
**Status:** stub. Trade-off documented; choice deferred to publisher
direction.

---

## Context

ξ.18 shipped per-request nonces on `script-src`, dropping
`'unsafe-inline'` from the script CSP directive. Every inline
`<script>` block in an HTML response now carries a
`nonce="<value>"` attribute matching the per-request CSP nonce, and
an attacker injecting a `<script>` block must ALSO know the
current request's random nonce — which is generated fresh per
response and never written to a discoverable location.

`style-src` was intentionally left at `'unsafe-inline'`. This
addendum captures the trade-off so a future decision is informed
rather than reactive.

---

## Why style-src is harder than script-src

Three structural reasons:

1. **Tailwind Play CDN** injects `<style>` tags at runtime as
   the class-scanner observes element classes. The browser
   evaluates those inline styles outside the request lifecycle
   that generates our nonce, so the runtime-injected `<style>`
   blocks would fail a strict nonce check.

2. **Theme tokens + ad-hoc inline styles**. The codebase has
   ~30+ inline `style="..."` attributes (per-component layout
   hints, theme-color binding for the ζ.1 dark-mode flicker
   prevention, etc.). Inline `style="..."` attributes aren't
   covered by nonces — they need a separate
   `style-src-attr 'unsafe-hashes'` directive, which is
   browser-coverage-spotty.

3. **`<aside class="note-comm-...">` etc.** The reader-EPUB
   note rendering relies on inline styles for theme adaptation.
   Tightening would surface as visible-only-in-strict-CSP-mode
   bugs.

---

## Options

### Option A — Move off Tailwind Play CDN; bundle Tailwind

- **Pros:** complete control over inline styles; nonce + hash
  protection across the entire CSS surface.
- **Cons:** introduces a build step. CLAUDE_PROJECT_RULES.md §6.3
  explicitly forbids build steps for the editor stack. Would
  require either:
  - Migrating the CSP-tightening goal under a different invariant
    (revisit §6.3), OR
  - Switching to runtime-class-list extraction with server-side
    style generation (more complexity than worth the win).
- **Cost:** 1-2 sessions; touches every console template + adds
  CI build step + adds a Node toolchain dependency.

### Option B — Hash-based CSP for style-src

- **Pros:** no build step required; current invariants preserved.
- **Cons:** every inline `<style>` block's content gets a
  sha-256 hash listed in the CSP. Tailwind's runtime-injected
  styles aren't reachable at server-side render time, so this
  option works only for static template `<style>` blocks +
  doesn't cover the Tailwind dynamic styles. Browser CSS-parsing
  whitespace normalization can make hash matching fragile.
- **Cost:** 1 session for the static-template hashes; doesn't
  close the Tailwind surface.

### Option C — Accept style-src `'unsafe-inline'`; document the threat model

- **Pros:** zero implementation cost; current ξ.18 protection
  is already substantial.
- **Cons:** an attacker who can inject `<style>` content (NOT
  `<script>` — that's already blocked) gets a vector for:
  - **Style-based UI redress** (overlay a hidden button on the
    Save button location; aka click-jacking variant). Note
    `frame-ancestors 'none'` already blocks iframe-based
    click-jacking; this would have to be in-document via a
    successful XSS that style-only delivers.
  - **CSS exfiltration** of structural information (e.g.
    `:has()` selectors + background-image URLs to a remote
    server). Modern browsers tightened this in 2023+; severity
    is bounded.

---

## Recommendation

**Default to Option C** until either (a) the project moves off
Tailwind Play CDN for unrelated reasons (POD pipeline / θ.5 i18n
might force a build step independently), or (b) a specific
style-based vulnerability is reported.

Document the threat model in a `SECURITY.md` block so the
defense-in-depth posture is explicit. The script-src tightening
in ξ.18 closed the high-severity vector; style-src tightening is
medium-low severity at best.

---

## Activation criteria

ξ.18.x becomes "do this now" if any of:

- The project moves off Tailwind Play CDN for any reason.
- A style-based XSS is reported.
- A buyer requires strict CSP compliance (e.g. financial-sector
  customer with auditing requirements).

Until then, this addendum is a "no-op pin" — the trade-off is
captured so a future contributor knows the decision was deliberate.

---

## Tests

When ξ.18.x ships, the existing
`test_csp_nonce_xi18.py::TestXi18CspWithNonce::test_style_src_keeps_unsafe_inline`
pin will need updating. That pin currently locks
`'unsafe-inline'` in style-src as a feature; ξ.18.x flips it to a
regression check (asserting style-src is also nonce-restricted).
