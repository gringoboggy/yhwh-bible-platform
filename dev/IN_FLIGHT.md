# In-flight work — current task tracker

<!-- TRACKER-STATE: idle -->

## Prior task

**SESSION_END_2026-05-12** shipped — professional handoff
closer for the longest single-conversation arc in the
project's history. Doc-only; no test delta; 11/11 lint clean.

`dev/SESSION_END_2026-05-12.md` (~250 lines) captures:

1. **38+ ships chronologically** (commits 3d19ef4 → 60d9e57)
   across Month 5 (closed) + Month 6 non-money queue (closed)
   + 5 doc-only removals + audit + PLAN-REFRESH-2.

2. **Code-residue audit for the 5 removed features**
   (B.AI.4/5/6/7 + δ.9) per publisher request to verify the
   removals cleaned up anything in the code. **Result: zero
   residue.**
   - scripts/core/copilot.py + scripts/core/verse_card.py:
     never existed (proposal-only entries).
   - No `import smtplib` / SMTP usage anywhere in scripts/.
   - All textual matches are strikethrough removal markers in
     dev/ docs or append-only historical CHANGELOG entries.
   - One near-match: verse_of_day matches in scripts/web.py +
     scripts/core/verse_of_day.py + test_scripts.py are υ.8
     (existing PD RSS feed, read-only daily verse rotation);
     NOT the removed δ.9 email subscription. Names overlap;
     scope doesn't. υ.8 stays.

3. **Translation status reality check** per publisher request
   ("I want to make sure there are more than just greek and
   hebrew translations available for the verses. latin and
   all that is still in there right?"). Honest answer
   surfaced: **the project ships exactly ONE full
   verse-by-verse translation today — KJV English.** The
   lxx-brenton-greek translation is a 3-verse seed (Genesis
   1:1-3 only, from γ.5). Editions DECLARE hebrew/greek/
   latin/arabic in popup_languages_default but the underlying
   translation data isn't on disk. Hebrew = γ.1 Strong's
   word-lookup only (lemma + morphology, not full text).
   Greek = γ.2 Strong's word-lookup + 3-verse LXX seed.
   Latin = not shipped at all. Arabic = not shipped at all.
   The τ-cluster (τ.2-τ.12) covers all of these in PLAN §7
   but none have shipped yet.

4. **Recommended next-session ordering**:
   - N+1: **τ.5-A JPS + WLC Hebrew ingest** (highest leverage
     — closes the Hebrew column for 6 of 9 editions; PD
     source; mirrors the τ.1 KJV pattern; ~1.5-2 sessions).
   - N+2: τ.4 Brenton LXX English (full ingest from the
     3-verse seed; ~1 session).
   - N+3: τ.3 Vulgate Latin (closes the Latin column for
     anglican-bcp; ~1.5 sessions).
   - N+4: τ.2 Douay-Rheims (Catholic English; ~1 session).
   - N+5+: per publisher direction (more τ, money
     authorization for B.AI.1+B.AI.2, γ.4.1 corpus expansion,
     ψ.30 matrix a11y, or uniqueness angles B/D/E from
     AUDIT_2026-05-10 §5).

The translation work jumped to top priority because closing
the gap improves every edition (9 of 9 declare languages they
don't fully serve) and is fully autonomous (no money
authorization needed for PD source ingest).

**3134/3135 tests pass serially (1 skipped); 11/11 lint
clean.** Doc-only ship.

## Prior task

**EPUB-scope reckoning: B.AI.5 + B.AI.6 + B.AI.7 + δ.9
REMOVED** shipped 2026-05-12. Doc-only per publisher direction
("can B.AI.5 actually be implemented in an EPUB and work on
EPUB readers? i feel like it's way out of scope" → confirmed
unimplementable; same root cause then audited for similar
items). No phase number; no test delta; 11/11 lint clean.

**Root cause**: EPUB readers sandbox JavaScript severely —
Apple Books/iBooks blocks XHR/fetch to external domains,
Kindle KFX strips most JS, Google Play Books blocks
cross-origin network, Calibre/ADE inconsistent. Any feature
requiring runtime network calls from the EPUB is
unimplementable in the actual shipped product.

**Four features failed the EPUB-scope test**:
- **B.AI.5** AI co-pilot (Cmd+J) — Anthropic API calls from
  EPUB JS blocked. Use cases were 100% publisher-console
  operations (scenario synthesis, blurb drafting).
- **B.AI.6** Daily devotional auto-curation — needs LLM call
  + SMTP. Neither callable from EPUB. Pure publisher-side.
- **B.AI.7** Marketing copy generator — depended on B.AI.5
  (orphaned by its removal). Also: "Amazon/Apple Books
  product copy" doesn't ship in the EPUB.
- **δ.9** Email subscription for verse-of-day — verbatim from
  proposal "pure backend; SMTP". Publisher web-server
  endpoint; no way for EPUB JS to subscribe.

**Items considered but kept** (per "everything else is
good"): ε.4 + ε.5 (publisher analytics — they're business-ops
tools you run alongside the platform); ξ/ω/ζ clusters
(publisher console UX); ο.6 "Built with YHWH" badge (DOES
ship in EPUB footer); B.AI.1+B.AI.2 cover gen (output ships
in EPUB); π.9 Bowker ISBN (appears on EPUB).

**12 strike-edits** in `dev/PROPOSAL_FEATURE_LANDSCAPE.md`:
§1.2 amazing-features rewrite, §3 Track summary recount, §5
Track E + Track J tables with vacant slots, §5 dependency-
graph art, §6 Month 6 recount 7→5 sessions, §7 tool catalog
removes scripts/core/copilot.py entry, §8 risk register, §9.3
publisher decisions, §11 acceptance criteria.

**Slot vacancy policy**: ALL five removed slots (B.AI.4 +
B.AI.5 + B.AI.6 + B.AI.7 + δ.9) intentionally LEFT VACANT in
numbering. Historical chronological docs (CHANGELOG, prior
IN_FLIGHT prior-task blocks, prior SESSION_STATE snapshot
blocks, AUDIT_2026-05-12) preserved unchanged — those are
append-only point-in-time records. Do NOT re-use these slot
numbers; assign fresh numbers if similar features are
genuinely needed in the future.

**Track J (AI features) post-reckoning**: narrowly scoped to
cover-generation artifacts that ship in the EPUB (B.AI.1 +
B.AI.2 + B.AI.3, all money-gated on publisher provider pick).

**Track E (reader experience) post-reckoning**: δ.1-δ.8 only.
Every retained item genuinely ships inside the EPUB
(localStorage state, EPUB-side CSS/JS, manifest.json for the
PWA published HTML edition).

**3134/3135 tests pass serially (1 skipped); 11/11 lint
clean.** No code changes; no test changes.

## Prior task

**π-book-covers ingest + B.AI.4 removal** shipped 2026-05-12.
Content + doc-only; no phase number assigned (extends existing
π.4 cover system; no code surface added). No test delta.
11/11 lint clean.

Two parts:

1. **Book covers ingest**: copied the publisher's 66-cover
   curated set from
   `C:\Users\bogda\Documents\book_covers\by_book\<NN_BookName>\primary.jpg`
   into `content/covers/_book_defaults/<book_code>.jpg`
   (Protestant 66-book canon, all books). Wired the Ethiopian
   Tewahedo edition's `book_covers:` YAML block in
   content/editions.yaml to reference all 66 shared paths.
   Added `content/covers/_book_defaults/README.md`
   documenting the inventory + opt-in pattern for other
   editions. Exercises the "paths can point anywhere under
   content/" door that `scripts/core/covers.py` explicitly
   documented as the shared-covers-across-editions pattern.
   Ethiopic-canon extras (1en, jub, mq1-3, 4ba, paz, sus,
   bel, man, 1es, 2es, tob, jdt, wis, bar, lje, sir, aes,
   etc. — 21 books) not covered by this ingest; future
   ingest opportunity.

2. **B.AI.4 sharable verse cards removed**: per publisher
   direction, the social-distribution lever is out of scope.
   7 strike-edits across `dev/PROPOSAL_FEATURE_LANDSCAPE.md`
   (§1.2 amazing-features bullet, §5 Track B table row + the
   dependency-graph art, §6 Month 6 sequence with recount
   from 7 to 6 sessions, §7 tool catalog, §9.3 publisher
   decisions, §11 acceptance criteria). Slot B.AI.4
   intentionally left VACANT in numbering to preserve
   historical references; do not re-use. Historical mentions
   in CHANGELOG / prior IN_FLIGHT prior-task blocks / prior
   SESSION_STATE snapshot blocks / AUDIT_2026-05-12 audit
   corpus snapshot left as-is — those are append-only
   point-in-time records.

**Month 6 status post-removal**: 5 of 6 shipped (γ.4 + ζ.9
+ ξ.18 + ξ.21 + ξ.26). Only B.AI.5 AI co-pilot (Cmd+J)
remains, gated on publisher authorization for Anthropic API
runtime budget.

**3134 / 3135 tests pass serially (1 skipped); 11/11 lint
clean.** No code changes; no test changes.

Per-publisher "finish autonomous" direction: continuing to
the next autonomous item after this ship.

## Prior task

**ξ.26 license-key validation** shipped 2026-05-12. Month 6
#5 — CLOSES the autonomous non-money queue. HMAC-SHA256
substituted for PROPOSAL-spec'd Ed25519 (stdlib-first
invariant § 6.3 forbids the `cryptography` library; soft
enforcement per § 9.5 doesn't justify asymmetric crypto; LK2
format prefix reserved for ξ.26.x Ed25519 upgrade if hard
enforcement ever required).

Three pieces:
- `scripts/core/license_key.py` — `LICENSE_PREFIX = "LK1"`;
  `ENV_SIGNING_KEY = "EBIBLE_LICENSE_SIGNING_KEY"`;
  `is_enforced()` reads the env var (fail-open when unset for
  dev / first-run convenience); `mint(edition_id, *,
  expires_iso, secret=None, issued_at_iso=None)` builds the
  LK1 string + HMAC-SHA256 signature; `verify(license_str, *,
  secret=None, now=None)` returns an envelope with reason ∈
  {ok, no_enforcement, missing, wrong_format,
  unsupported_version, bad_signature, expired}. Constant-time
  signature compare via hmac.compare_digest. Format prefix
  reserved for LK2 (Ed25519) future upgrade.
- `scripts/core/license_state.py` — sparse JSON state at
  content/licenses.json mirroring auth.py / distribution.py /
  press_kit.py persistence discipline (atomic write +
  ensure_backup + whitelist-on-save + empty-state default).
  set_license / remove_license / get_license / load /
  save helpers.
- `scripts/api/license.py` — 3 endpoints: GET
  /api/license/status returns per-edition rollup with
  has_key + valid + reason; PUT /api/license/<edition>
  verifies BEFORE persisting (refuses bad signature / expired
  / edition mismatch so bad keys don't get stuck in state);
  DELETE /api/license/<edition> idempotent. Audit-logged.
  Status endpoint NEVER reveals the stored key string.

Soft-enforcement contract pinned: API never refuses a request
based on license state; status endpoint surfaces validity so
future UI can render warning banner; build/preview/publish
paths must not crash on missing or invalid keys.

Routes registered: GET /api/license/status →
_SIMPLE_GET_ROUTES (20→21); PUT /api/license/<edition> →
_PUT_ROUTES (11→12); DELETE /api/license/<edition> →
_DELETE_ROUTES (7→8). Count tests bumped on both PUT + DELETE.

**+43 tests** in tests/test_license_xi26.py (44 cases in file; 1 deselected at collection):
TestXi26Constants × 2, EnforcementToggle × 3, Mint × 7,
Verify × 9 (round-trip, bad sig, expired, wrong secret,
unsupported version, malformed, missing, fail-open, now
injection), LicenseStateLoadSave × 5, SetRemove × 4,
ApiStatus × 4 (incl never-reveals-stored-key pin),
ApiSet × 5, ApiRemove × 2, RouteRegistration × 3.

**3134 / 3135 tests pass serially (1 skipped); 11/11 lint
clean.**

Forward reference: ξ.26.x Ed25519 upgrade for hard
enforcement (LK2 format prefix; verify() dispatches on
prefix for side-by-side migration). Logged in CHANGELOG so
linter phase-mentions check stays clean.

**Month 6 status: autonomous non-money queue CLOSED.**
Remaining work blocked on publisher decision: B.AI.4 +
B.AI.5 money items, or new direction (γ.4.x / ψ.30 / χ.2-5 /
uniqueness angles B/D/E).

## Prior task

**ξ.21 TOTP-based 2FA for admin auth** shipped 2026-05-12.
Month 6 #4 — stdlib-only RFC 6238 implementation (no pyotp
dep) + persisted enrollment + admin-auth gate extension.

Four pieces:
- `scripts/core/totp.py` — pure-stdlib TOTP: generate_secret
  (160-bit base32 via secrets.token_bytes), current_code (RFC
  6238 HMAC-SHA1, 30s step, 6 digits), verify_code (±1-step
  default drift, constant-time compare via
  hmac.compare_digest, malformed rejection without raising),
  provisioning_uri (otpauth://totp/Issuer:Label?secret=...&
  algorithm=SHA1&digits=6&period=30; URL-encodes label +
  issuer). Verified against all 6 RFC 6238 Appendix B test
  vectors (parametrized).
- `scripts/core/auth.py` — sparse JSON state at
  content/auth.json mirroring distribution.py persistence
  (atomic write + ensure_backup + whitelist-on-save).
  load_auth / save_auth / enroll_totp / disable_totp /
  is_totp_enabled / get_totp_secret.
- `scripts/api/auth.py` — 4 endpoints: GET /status surfaces
  flags + enrollment metadata but never the secret; POST
  /begin generates pending secret + URI WITHOUT persisting;
  POST /confirm verifies code then persists (two-step
  pattern prevents lockout from a never-proved enrollment);
  POST /disable requires a valid current code (refuses
  without proof so an attacker who bypassed the gate can't
  also nuke 2FA).
- `scripts.web.Handler._check_admin_auth` doubled in size to
  handle the factor matrix: Bearer token:code parsed via
  str.partition(':') so tokens containing colons round-trip
  correctly; back-compat preserved when neither factor is
  configured (ω.4 default-open behavior unchanged).

Routes registered: GET /api/auth/status →
_SIMPLE_GET_ROUTES (19→20); 3 POST /api/auth/totp/{begin,
confirm,disable} → _POST_ROUTES (9→12; count test bumped).

Deliberate scope choices: QR-code rendering DEFERRED to
ξ.21.x (publisher pastes otpauth URL into authenticator app;
QR rendering needs ~300 lines hand-rolled Reed-Solomon or a
CDN dep conflicting with §6.3); single-use recovery codes
also DEFERRED to ξ.21.x (acceptable for solo-admin: edit
content/auth.json directly to disable if locked out).

**+54 tests** in tests/test_totp_xi21.py: Rfc6238Vectors × 6
parametrized, SecretGeneration × 5, ProvisioningUri × 4,
VerifyCode × 7, AuthStateLoadSave × 4, EnrollDisable × 6,
ApiBegin × 2, ApiConfirm × 4, ApiDisable × 4, ApiStatus × 3,
AdminAuthGate × 5 (neither/token-only/totp-only/both factor
combinations), RouteRegistration × 3.

**3091 / 3092 tests pass serially (1 skipped); 11/11 lint
clean.**

Forward references: ξ.21.x (QR-code SVG rendering + single-
use recovery codes) logged in CHANGELOG for linter phase-
mentions check.

## Prior task

**PLAN-REFRESH-2** shipped 2026-05-12. Doc-only refresh per
AUDIT_2026-05-12 §5 N+1 ("highest-leverage single action; closes
5 of 7 named drift items in one pass" — actually closed 6 of 7).
No phase shipped, no test delta, no code change; 11/11 lint
clean.

Seven distinct doc changes in one ship:

1. **`dev/PLAN_2026-05-09.md` §7 ledger** — Month 5+6 ships
   added to ✓ list (ε.1-ε.3 + ε.6-ε.7 + ο.4 + γ.4 + ζ.9 +
   ξ.18 + ν.7 + ν.10 + ψ.35 + ψ.36-A + ψ.37 + ψ.38 +
   ω.35-A.1-A.11 + ω.35-B.1-B.7 + ω.37/38/39/47 + Δ.6/7/10/12/15
   + ζ.1-9 + γ.1-5 + δ.1-2).

2. **`dev/PLAN_2026-05-09.md` §10.1 operating model** — new
   section cross-referencing `PROPOSAL_FEATURE_LANDSCAPE.md` §6
   as the canonical post-v1.0 sequence doc. Documents Month
   1-6 status + AUDIT §5 next-N table.

3. **`dev/PLAN_2026-05-09.md` §11 addenda index** — two new
   stubs:
   - `dev/SCOPE_2026-05-12-addendum-xi-18-x-style-src.md`
     (style-src tightening trade-off: option A Tailwind-build
     / B hash-CSP / C accept current surface).
   - `dev/SCOPE_2026-05-12-addendum-gamma-4-expansion.md`
     (γ.4.x corpus expansion roadmap — 6 PD-source ETL
     sub-phases targeting ~1.5K-1.8K entries total).

4. **`dev/CLAUDE_PROJECT_RULES.md` §1 corpus target** —
   updated to reflect actual 51,394 notes (147% of original
   upper bound; floor met; growth opportunistic).

5. **`dev/CLAUDE_PROJECT_RULES.md` §10 NOT-list** — POD line
   partially lifted (PDF in scope via ε.7 + ψ.22; KDP/IngramSpark
   still deferred).

6. **`dev/ROADMAP_FUTURE.md`** — three "definitely NOT
   planned" items reconciled: Audio Bible (lifted; ρ-cluster
   scheduled), POD (partial), Multi-language UI (lifted
   2026-05-09).

7. **`dev/IN_FLIGHT.md` prune** — chain truncated from ~30+
   "Prior task" entries (~8,643 lines) to last 5 (this entry +
   AUDIT + ξ.18 + ζ.9 + γ.4 + ο.4 = 275 lines, -97%). CHANGELOG
   carries the authoritative chronological record.

**Drift items addressed: 6 of 7** (POD/i18n line in §10 was
partial — LMS / native-apps / Flask lines unchanged because
they remain accurate). 18 scope addenda now indexed in PLAN §11
(was 16).

**3037 / 3038 tests pass serially (1 skipped); 11/11 lint
clean.** No code changes.

## Prior task

**AUDIT_2026-05-12** shipped 2026-05-12. Doc-only solo-Claude
audit triggered by `feedback_audit_cadence.md` after Month 5
closure + ≥150 test-count drift both tripped. No phase shipped;
no test delta; lint 11/11 clean.

Single output: `dev/AUDIT_2026-05-12.md` (~250 lines). Sections:

- TL;DR — 2026-05-11 audit's 12 named items mostly shipped (11 of
  12); audit-cadence rule is working.
- Arc statistics — Month 5 + Month 6 opening: 32 ships, +784
  tests; web.py 4,564 → 4,921 (no god-module regression).
- Status table for AUDIT_2026-05-11 recommendations.
- 5 new drift findings: money-gate dominance, ξ.18.x style-src
  trade-off unspeced, PROPOSAL operating model not in PLAN,
  IN_FLIGHT prior-task chain bloat, test-suite balance.
- Route/console/module inventory: 60 table-routed endpoints,
  17 consoles unchanged, 5 new core + 4 new api modules, 5
  new content/ JSON state files.
- Recommended next-N-session ordering: N+1 PLAN-REFRESH-2 → N+2
  ξ.21 2FA → N+3 ξ.26 license-key → N+4 publisher decision.
- Closing: highest-leverage single action is PLAN-REFRESH-2
  (doc-only, ~1 hour, closes 5 of 7 named drift items).

Method: mechanical inventory pass (route table counts via Python
introspection, file sizes via `wc -l`, console count via CONSOLES
tuple length) + recommendation drafting + carry-over flagging.

**3037 / 3038 tests pass serially (1 skipped); 11/11 lint clean.**
No code changes.

## Prior task

**ξ.18 CSP nonces** shipped 2026-05-12. Month 6 #3 — per-
request nonce on script-src; HTML responses get the strict
policy + every &lt;script&gt; gets nonce="X"; JSON/file/zip
responses keep the legacy _CSP_POLICY as defense-in-depth.

Three pieces in scripts/web.py::Handler:
- `_generate_nonce()` staticmethod — secrets.token_urlsafe(16)
  → 22-char base64-urlsafe string; 128 bits of entropy per
  RFC 8941 recommendation.
- `_csp_with_nonce(nonce)` classmethod — builds the strict CSP:
  script-src 'self' 'nonce-<value>' https://cdn.tailwindcss.com.
  style-src deliberately keeps 'unsafe-inline' (Tailwind Play
  CDN compat; tightening needs a build step that §6.3 forbids).
- `_SCRIPT_TAG_RE` class regex + `_inject_script_nonces(html,
  nonce)` classmethod — adds nonce="X" to every &lt;script tag
  variant (no-attr, src=, async, multi-line); regex boundary
  prevents false matches on &lt;scripts&gt;/&lt;scripting&gt;;
  idempotent on already-noncified HTML; preserves internal
  whitespace.

Plumbing:
- `_send_security_headers(*, nonce=None)` kwarg added: when None
  emits the legacy `_CSP_POLICY` (defense in depth for
  JSON/file/zip), when string emits `_csp_with_nonce(nonce)`.
- `_send_html(html)` generates a fresh nonce per call → runs
  injector → sends strict CSP with matching nonce. Nonce
  rebuilds on every render so a cached prior response can't
  replay-attack the current one.

**+26 tests** in `tests/test_csp_nonce_xi18.py`:
NonceGeneration × 3, CspWithNonce × 5 (drops 'unsafe-inline'
from script-src, includes nonce, keeps style-src
'unsafe-inline', other directives preserved, Tailwind CDN
allowed), ScriptInjection × 9 (every &lt;script tag variant +
boundary check vs &lt;scripts&gt;/&lt;scripting&gt; +
idempotence + real EXEC_HTML), SendHtmlContract × 4 with
fake-handler smoke tests, LegacyPolicyPreserved × 2 (ξ.3
contract stays green), JsonResponsesUseLegacyCsp × 3.

**3037 / 3038 tests pass serially (1 skipped); 11/11 lint clean.**

Forward reference: ξ.18.x style-src nonce tightening (needs a
Tailwind-build migration; conflicts with §6.3 "no build step"
today). Logged in CHANGELOG so the linter's "phase mentioned
in code" check stays clean.

## Prior task

**ζ.9 first-run tour** shipped 2026-05-12. Month 6 #2 —
in-house tour overlay engine (no Shepherd.js / CDN
dependency per invariant I.1 "no heavy framework creep");
mirrors Shepherd/Driver/Intro public API shape so future
migration is cheap. + 6-step /exec first-run walk-through.

Three pieces:
- `scripts/templates/_design.py::THEME_TOUR_JS` — new ~330-
  line script constant exposing `window.ebibleTour.{start,
  skip, next, back, startIfFirstRun, reset}`. UX contract:
  dim backdrop + halo on the target (box-shadow provides the
  per-step dim), positioned tooltip with viewport clamping
  via top/bottom/left/right `position` field (default
  `bottom`), centred-modal mode for null-selector steps,
  ARIA `role=dialog` + `aria-modal=true` + `aria-labelledby`
  referencing the title's id, keyboard nav (ESC=skip,
  ←/→=back/next), focus moves to Next button on each step
  with prior focus restored on close, click-outside does NOT
  dismiss (avoid accidental skip), reduced-motion friendly.
  All caller-supplied strings (title, body) inserted via
  textContent. localStorage gate (default key
  `ebible_tour_seen_v1`); `startIfFirstRun(storageKey,
  steps, opts)` short-circuits when the flag is set;
  `reset(storageKey)` clears it for future /apihelp
  restart-link wiring. Each step has a counter
  ("Step N of M") + Back disabled on step 0 + Next reads
  "Done" on the last step.
- `scripts/templates/_design.py::apply_design_system` —
  `<!-- THEME_TOUR_JS -->` marker substitution registered
  + the docstring marker catalog updated to list ζ.9.
- `scripts/templates/exec.py` — `<!-- THEME_TOUR_JS -->`
  marker inserted in the head + 6-step tour declared in an
  IIFE at the bottom of the dashboard script, gated on
  `window.ebibleTour` presence. Steps: welcome modal → KPI
  tiles (`#kpi-grid`) → sales import (`#sales-import-section`)
  → distribution checklist (`#distribution-section`) → press
  kit + archive.org (`#press-kit-section`) → closing modal
  with Cmd+K pointer + /apihelp-restart hint. Storage key
  `ebible_tour_exec_v1` (per-console namespacing so future
  /matrix or /publisher tours can be tracked independently).

**+21 tests** in `tests/test_tour_zeta9.py`:
TestZeta9JsConstantShape × 2, MarkerSubstituted × 2,
MarkerDocumented × 1, XssGuards × 4 (pin textContent over
innerHTML for every caller-controlled string), StorageKey
× 2, Accessibility × 4 (ARIA + ESC handler), ExecWiring × 6
(step count + selectors + modal-bookend pattern + first-run
guard).

**3011 / 3012 tests pass serially (1 skipped); 11/11 lint clean.**

## Prior task

**γ.4 Ethiopian Tewahedo commentary** shipped 2026-05-12.
Month 6 — the flagship payload per PROPOSAL ("the Tewahedo
Bible's primary differentiator"). Opens Month 6 by taking the
v1.x uniqueness angle first.

Three pieces:
- `content/sources/ethiopian_commentaries.json` — new 12-entry
  seed JSON. _meta block documents PD basis (Ephrem the Syrian
  via NPNF Series 2 vol 13 ed. Schaff 1898 + Cyril of
  Alexandria via NPNF vols 7+14 + R.H. Charles, The Book of
  Enoch, Oxford 1912 — all firmly out of copyright). Entries
  cover Gen 1:1/1:3/1:26/2:7/3:1/6:1/6:4 + Ps 1:1+23:1 + John
  1:1/1:14/19:34. Three traditions represented: Ephrem (Syriac
  patristic — Tewahedo theological influence), Cyril
  (non-Chalcedonian Alexandrian — Miaphysite Christology
  foundational to the Oriental Orthodox communion of which
  Tewahedo is one of five canonical jurisdictions), and 1 Enoch
  (Tewahedo-canonical Watchers tradition; the only major
  Christian communion to canonize 1 Enoch).
- `scripts/core/sources.py` — `EthiopianCommentary` frozen
  dataclass mirroring `PatristicCommentary` exactly +
  `EthiopianCommentaries` lazy loader (indexes by_verse +
  by_father, raises SourceMissingError on absent JSON) +
  `ethiopian_commentaries()` `@lru_cache(maxsize=1)` singleton.
- `scripts/core/detectors.py` — `EthiopianCommentaryDetector`
  class (kind="comm-ethiopian", confidence 0.95, direct-lookup
  by (book, chapter, verse), HTML-escaped body via
  `_format_body()` with **BC/AD-aware year renderer** so 1
  Enoch's c. 200 BC dating renders as "200 BC" not "-200 AD",
  `note-comm-ethiopian` CSS class for theme styling, reviewer
  notes reference the Andəmta tradition cross-check). Appended
  to `ALL_DETECTORS` after `PatristicCommentaryDetector` (γ.3)
  so candidate ordering is Father-canonical first,
  Tewahedo-distinctive second.

**Kind reuse**: `comm-ethiopian` already existed in
content/kinds.yaml ("Ethiopian Tewahedo tradition — Andəmta
commentary, Synaxarium, Fetha Nagast"). γ.4 is the first phase
to populate it. No kinds.yaml edit needed.

**Tradition wiring**: pre-existing. content/traditions.yaml
already maps ethiopian-tewahedo→tewahedo, so ψ.8 picks up
comm-ethiopian notes for the ethiopian-tewahedo edition
automatically.

**+30 tests** in `tests/test_ethiopian_gamma4.py`:
TestGamma4DataFile × 7, EthiopianCommentariesLoader × 8,
DetectorContract × 9, KindIsRegistered × 2, Coverage × 4.

**2990 / 2991 tests pass serially (1 skipped); 11/11 lint clean.**

Forward reference: γ.4.x is the natural follow-on — NPNF +
Charles ETL into the 1K-note corpus the PROPOSAL §6 names as
the eventual target. Logged in CHANGELOG so the linter's
"phase mentioned in code" check stays clean.

## Prior task

**ο.4 archive.org auto-upload** shipped 2026-05-11. Month 5 #7
— CLOSES Month 5. Drop-to-archive.org button on /exec; composes
ε.7 press-kit ZIP + S3-style PUT + ε.6 distribution auto-mark.

Three pieces:
- `scripts/core/archive_org.py` — `ENV_ACCESS_KEY` /
  `ENV_SECRET_KEY` / `ENV_CREATOR` env-var name constants;
  `DISTRIBUTION_CHANNEL = "archive_org"` matches
  distribution.DISTRIBUTION_CHANNELS; `IDENTIFIER_PREFIX_DEFAULT
  = "yhwh-bible-"`; `ARCHIVE_S3_BASE = "https://s3.us.archive.org"`;
  `is_configured()` True iff both env vars set + non-whitespace;
  `sanitize_identifier(edition_id, *, prefix)` collapses invalid
  chars → dash, strips leading dots/dashes, ≥5-char + ≤100-char
  guards, empty input → "yhwh-bible-untitled" fallback;
  `build_metadata_headers(edition, blurbs)` emits the full
  x-archive-meta-* header set (title / description / mediatype=
  texts / collection=opensource / language=eng / creator /
  licenseurl=CC0) with CR/LF stripping (defense against HTTP
  response splitting); `upload_press_kit(edition, blurbs,
  zip_bytes, *, filename, http_fn=None)` PUTs via injectable
  http_fn (defaults to scripts.core.http.put with the archive-
  org upload allowlist); exceptions from http_fn become
  ok:False envelope rather than re-raise; identifier still
  computed on network failure so audit trail can correlate.
- `scripts/core/http.py` extended — new `put(url, body, *,
  headers, timeout, retries, backoff, retry_on_status,
  allowlist, sleep_fn, urlopen)` returning (status_code,
  response_bytes); mirrors get()'s retry / timeout / SSRF
  discipline (fails closed on missing allowlist). New
  `DEFAULT_ARCHIVE_ORG_UPLOAD_ALLOWLIST = {"s3.us.archive.org",
  "archive.org"}` frozenset kept separate from PD-sources
  allowlist since uploads are privileged write traffic.
- `scripts/api/archive_org.py` — `api_archive_org_status()` GET
  returns `{configured, message, identifier_prefix,
  env_var_access, env_var_secret}` (env var *names* surfaced so
  UI can tell publisher exactly what to set);
  `api_archive_org_upload(edition_id, payload, *, http_fn=None)`
  POST composes press_kit.build_zip + archive_org.upload_press_kit
  + distribution.mark_shipped(edition_id, "archive_org",
  url=...) — returns one envelope describing all three side-
  effects with distribution_marked + distribution_error fields;
  503 when creds missing; 404 on unknown edition; upload
  failure → ok:False with distribution NOT marked; distribution
  side-effect failure → upload reported ok:True but
  distribution_marked=False with the exception in
  distribution_error. Audit-logged.

/exec extended with archive-org section co-located with press-
kit (the upload composes press-kit ZIP): status banner loaded
from /api/archive-org/status names the exact env vars to set;
Upload button disabled by default until status confirms
configured=true, POSTs to /api/archive-org/upload/<edition>
with ζ.6 toast on result, refreshes distribution checklist via
loadDistribution() so the auto-marked archive_org cell flips
in the UI.

Routes registered: GET `/api/archive-org/status` →
`_SIMPLE_GET_ROUTES`; POST `/api/archive-org/upload/<edition>`
→ `_POST_ROUTES` (count test 8→9).

**+38 tests** in `tests/test_archive_org_omicron4.py`:
TestOmicron4Constants × 4, IsConfigured × 3, SanitizeIdentifier
× 5, MetadataHeaders × 4, UploadPressKit × 5, ApiStatus × 2,
ApiUpload × 5, ExecTemplate × 4, RouteRegistration × 2,
HttpPutHelper × 3, Integration × 1.

**2960 / 2961 tests pass serially (1 skipped); 11/11 lint clean.**

**MONTH 5 CLOSED** — all 7 non-money items shipped (Δ.15 /
ε.1 / ε.2 / ε.3 / ε.6 / ε.7 / ο.4).


---

*Prior-task entries from before ο.4 (Month 5 #7) pruned 2026-05-12
per AUDIT_2026-05-12 §4d (IN_FLIGHT chain bloat). The authoritative
chronological record lives in `dev/CHANGELOG.md`. Each prior task
above also has its own CHANGELOG entry with full detail.*
