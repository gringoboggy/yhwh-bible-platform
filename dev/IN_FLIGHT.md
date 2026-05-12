# In-flight work — current task tracker

<!-- TRACKER-STATE: idle -->

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
