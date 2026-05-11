# PROPOSAL — Feature landscape: from v1.0 to spotless + amazing

> **Status:** planning document.
> **Created:** 2026-05-10.
> **Companion to:** `PLAN_2026-05-09.md` (the active plan ledger),
> `PROPOSAL_AI_ARTWORK.md` (AI cover art / icon roadmap),
> `AUDIT_2026-05-11.md` (engineering health audit).
> **Audience:** publisher (decisions on tracks + budget), engineer
> (this is the blueprint for the next ~6 months of work).

---

## 0. How to use this document

This is a **portfolio plan**, not a sequential plan. The existing
`PLAN_2026-05-09.md` enumerates open phases (ψ.21, χ.2-5, τ.2-12,
etc.) within tracks already known. This document adds **net-new
tracks + phases** identified in the 2026-05-10 brainstorm, with
careful dependency-chaining so every phase enables the next one
either within its track or downstream into other tracks.

Read order:
1. **§1 North star** — what "spotless + amazing" actually means.
2. **§2 Invariants** — what we will NOT break (the rails the
   refactor runs on).
3. **§3 Track summary** — 11 tracks; pick which to greenlight.
4. **§4 Phase ledger** — every new phase with id, depends, effort,
   blast radius, key deliverables.
5. **§5 Dependency graph** — which phases unlock which.
6. **§6 Sequencing** — a recommended 6-month rollout.
7. **§7 Tool catalog** — small tools we need to build along the way.
8. **§8 Risk register** — what could go wrong.
9. **§9 Publisher decisions** — inputs needed from you.
10. **§10 Integration** — how this plays with PLAN_2026-05-09.md.
11. **§11 Acceptance criteria** — what "done" looks like.

Phases use the project's Greek-letter convention. NEW letters
proposed (previously unused per `PLAN_2026-05-09.md` §7):
- **γ** — corpus depth (interlinear, patristic, LXX, Vulgate, ...)
- **δ** — reader experience (memorization, streaks, sync)
- **ε** — executive / business intelligence
- **ζ** — UI modernization (dark mode, typography, command palette)
- **ο** — distribution / marketing channels

Extended existing families:
- **ω.37+** — developer tooling (CI, hooks, dev consoles)
- **ξ.18+** — security hardening
- **ψ.36+** — matrix expansion
- **ν.7+** — publisher workflow polish
- **π.6+** — publishing surface (cover composer, approval, ISBN)
- **Δ.10+** — database evolution (FTS5, WAL, migrations)

---

## 1. North star — "spotless + amazing"

Two complementary goals:

### 1.1 Spotless = no perceived flaws
- Zero crashes on user-facing actions.
- Zero data loss (the B.3b near-miss with `strongs_hebrew.json`
  was caught and patched; the CI guard prevents the next instance).
- Zero security holes a casual scan would flag.
- Zero "this looks dated" reactions on first viewing.
- Predictable performance — no surprise hangs.
- Discoverable features — anything the program does can be found
  in <30s without reading docs.
- Consistent visual language — fonts, colors, spacing, motion.

### 1.2 Amazing = wow moments
- First-run experience that sells the product to its own user.
- Content depth that beats every free Bible app's free tier
  (Hebrew/Greek interlinear, patristic commentary, Targums, DSS
  variants, critical apparatus).
- AI features that feel like magic (verse cards, co-pilot,
  daily devotional curation).
- Reader features that compete with paid apps (memorization
  spaced-repetition, audio-sync, sharable cards).
- Publisher tools that compress days of editorial work into
  minutes (cover composer, marketing copy gen, ISBN registration).
- Executive dashboard that makes the business legible at a glance.

---

## 2. Architectural invariants (the rails)

These are CONSTRAINTS the proposal honors. Breaking any of them
needs an explicit design decision; the proposal does not propose
breaking them.

| # | Invariant | Why |
|---|---|---|
| I.1 | **No build step** — Tailwind via CDN, vanilla JS, no Webpack/Vite | Per `CLAUDE_PROJECT_RULES.md` §6.3. Keeps the dev loop instantaneous. |
| I.2 | **Stdlib HTTP server** — `BaseHTTPRequestHandler`, no Flask | Per project rules. Stability + zero dependency creep. |
| I.3 | **File-based persistence** — YAML + JSON + sqlite for derived index | Predictable, diffable, portable. Sqlite stays a DERIVED layer (you can blow it away). |
| I.4 | **Atomic writes via `notes_io.atomic_write`** | Crash-safety. Every persistence change goes through it. |
| I.5 | **Route-table dispatch** — `_SIMPLE/REGEX_GET/QS_REGEX/PUT/POST/DELETE/MULTIPART_ROUTES` | Established 2026-05-11 (ω.35-A). Every new endpoint adds an entry to a table, not a `def do_X` branch. |
| I.6 | **API + UI separation** — pure-function api_X + thin Handler routing | §9 mental model. Lets us unit-test logic without HTTP. |
| I.7 | **Audit-log every mutation** — `@audit_log.audit_endpoint(action=...)` | ξ.13 invariant. Forensic trail for shipped editions. |
| I.8 | **Tier-3 preflight** — every new check is a meta-tool that integrates with `scripts/lint_rules.py` | §9 invariant. Catches drift early; single pane of glass. |
| I.9 | **Phase = code + tests + CHANGELOG + SESSION_STATE + IN_FLIGHT + audit** | Working agreement; non-negotiable. |
| I.10 | **No backwards-compat shims for unused code** | Per `CLAUDE_PROJECT_RULES`. Delete dead code; trust the refactor. |
| I.11 | **Protected production paths via the CI guard** | New 2026-05-10. `content/sources/` + `content/editions.yaml` snapshot-checked at session teardown. |

If any proposal phase below conflicts with an invariant, the
conflict is called out in that phase's "Notes."

---

## 3. Track structure — at a glance

11 tracks, each with a coherent theme. Pick which to greenlight
in §6 sequencing.

| Track | Theme | Phases | Estimated total effort | First-phase blockers |
|---|---|---|---|---|
| **A** | Finish ω.35-B file split | ω.35-B.4 → B.6 | 3 sessions | None — ready now |
| **B** | Developer experience | ω.37–ω.46 | 6–8 sessions | None |
| **C** | UI modernization (ζ family) | ζ.1–ζ.10 | 6–10 sessions | C.1 first (CSS variables) |
| **D** | Corpus depth (γ family) | γ.1–γ.9 | 12–18 sessions | D.1 (interlinear UI scaffold) |
| **E** | Reader experience (δ family) | δ.1–δ.9 | 6–10 sessions | C track (dark mode for δ.5) |
| **F** | Executive / business (ε family) | ε.1–ε.8 | 6–8 sessions | F.1 (event log) before others |
| **G** | Security hardening (ξ.18+) | ξ.18–ξ.29 | 6–8 sessions | None |
| **H** | Matrix expansion (ψ.36+) | ψ.36–ψ.43 | 6–8 sessions | None |
| **I** | Publisher workflow (ν.7+, π.6+) | ν.7–ν.11, π.6–π.12 | 8–12 sessions | C track (consistent UI) |
| **J** | AI features (B.AI.*) | B.AI.1–B.AI.7 | 8–10 sessions | Publisher provider pick |
| **K** | Distribution / marketing (ο family) | ο.1–ο.7 | 6–8 sessions | F track (analytics first) |
| **L** | Database evolution (Δ.10+) | Δ.10–Δ.16 | 4–6 sessions | L.1 (migrations) first |

**Total scope**: ~80–110 sessions across all tracks. Realistic
~50% subset over 6 months = ~40 sessions. Sequencing in §6.

---

## 4. Phase ledger

Each entry: `phase | title | status | depends | effort | blast | notes`.

Effort scale: sessions of ~2–4 hours each. Blast: **S**mall (one
file), **M**edium (a few files + tests), **L**arge (cross-module).

### Track A — finish ω.35-B file split

| ID | Title | Depends | Effort | Blast | Notes |
|---|---|---|---|---|---|
| ω.35-B.4 | editions/customize extraction | B.3b ✓ | 1 | M | api_save_edition*, api_save_category/kind, api_clone_edition, api_create_edition_from_template. |
| ω.35-B.5 | exports/build extraction | B.4 | 1 | M | api_export_*, api_build_*. Notably the bespoke PUTs that stayed in legacy (build/build-all) can migrate here cleanly with their `_dispatch_table_result` adapters. |
| ω.35-B.6 | preflight/audit/help extraction | B.5 | 1 | M | api_preflight, api_audit_log, api_help_data + multipart helpers (`_extract_boundary`, `_parse_multipart`, `_save_cover_bytes`) → `scripts/api/_multipart.py` shared module. Closes the file-split. |

**Track A outcome**: `scripts/web.py` reduced from ~7,400 lines
to ~2,500 lines (the Handler class + route tables). Per-topic
api modules become independently testable + replaceable.

### Track B — developer experience (ω.37+)

| ID | Title | Depends | Effort | Blast | Notes |
|---|---|---|---|---|---|
| ω.37 | Pre-commit hook framework | none | 0.5 | S | `.githooks/pre-commit` runs `ruff format --check` + `scripts/lint_rules.py`. Prevents the recurring "ruff drift" failure pattern. Activation: `git config core.hooksPath .githooks`. (FIRST SHIPMENT — included in this commit) |
| ω.38 | GitHub Actions CI | ω.37 | 1 | S | `.github/workflows/ci.yml` runs tests + linter on every push. Optional Windows-runner + macOS-runner matrix. SonarCloud integration already done (2026-05-11). |
| ω.39 | Hot-reload for templates | none | 0.5 | S | `watchdog`-based file watcher; SSE-driven browser auto-refresh. Halves the dev-loop time. |
| ω.40 | VS Code workspace config | none | 0.25 | S | `.vscode/settings.json` + recommended extensions list (ruff, Python). |
| ω.41 | Dev container | ω.40 | 1 | S | `.devcontainer/devcontainer.json` for cloud-dev parity. Optional. |
| ω.42 | /dev/components console | ω.35-B.6 | 1 | M | Per-template preview. Browse every template's reusable bits in isolation. Catches CSS regressions. |
| ω.43 | /dev/api console (API playground) | ω.42 | 1 | M | Postman-like UI to hit /api/* routes. Self-served via the route tables — `_SIMPLE_GET_ROUTES` etc. are enumerated and rendered as a form. |
| ω.44 | Performance regression dashboard | F.1 (event log) | 1 | M | Renders `scripts/perf_budgets.py` history as a chart. Per-budget trend over the last 90 days. |
| ω.45 | OpenAPI/Swagger generator | ω.43 | 1 | M | Composes existing `api_help_data` scanner output into a real OpenAPI 3.1 spec; serves it at `/apidocs` with embedded Swagger UI (CDN). |
| ω.46 | ADR generator from CHANGELOG | none | 0.5 | S | Each CHANGELOG entry > 50 lines auto-promotes to `dev/adr/NNNN-<slug>.md`. Makes the existing decision trail formally addressable. |

**Track B outcome**: dev loop tightens by 2-3×; CI prevents the
class of bug (ruff drift, monkeypatch regression) we've seen
repeatedly this session.

### Track C — UI modernization (ζ family)

| ID | Title | Depends | Effort | Blast | Notes |
|---|---|---|---|---|---|
| ζ.1 | CSS variable theming foundation | none | 1 | M | Centralize design tokens (color, spacing, type-scale, motion) into `scripts/templates/_design.py`'s `apply_design_system` helper. Currently scattered across templates. Required prerequisite for everything below. |
| ζ.2 | Dark mode | ζ.1 | 0.5 | S | `[data-theme="dark"]` selector, OS-prefers-color-scheme detection, persisted in localStorage. Header toggle. |
| ζ.3 | Sepia / paper mode (reader) | ζ.2 | 0.5 | S | Same machinery, additional palette. Reader-focused theme. |
| ζ.4 | Typography upgrade | ζ.1 | 0.5 | S | Inter for UI, Crimson Pro for reading body. Loaded from Google Fonts CDN (zero build). |
| ζ.5 | Iconography pass (Lucide / Heroicons) | ζ.1 | 1 | M | Replace ad-hoc Unicode + emoji glyphs with a consistent SVG icon set. Inlined SVG (no extra requests). |
| ζ.6 | Toast notifications | ζ.1 | 0.5 | S | Top-right toast container, success/info/error variants, auto-dismiss. Replaces current inline banners. |
| ζ.7 | Skeleton loaders | ζ.1 | 0.5 | S | Grey placeholder bars in the actual shape of pending content. Subjectively much faster. |
| ζ.8 | Command palette (Cmd+K / Ctrl+K) | ζ.5 | 1 | M | Global keyboard shortcut; type-to-search across actions ("go to genesis", "build edition kjv", "open matrix"). Modern desktop standard. |
| ζ.9 | First-run tour | ζ.5, ζ.6 | 1 | M | 90-second guided tour via Shepherd.js (CDN). Skipable; never auto-reshows. Sells the product to its own user. |
| ζ.10 | Page transitions | ζ.1 | 0.5 | S | View-transition API (Chrome) with CSS fade fallback (Safari/Firefox). Subtle polish. |

**Track C outcome**: program feels indistinguishable from a 2026
SaaS product. Dark mode + iconography pass alone shifts perceived
quality dramatically.

### Track D — corpus depth (γ family) — "the most extensive Bible"

| ID | Title | Depends | Effort | Blast | Notes |
|---|---|---|---|---|---|
| γ.1 | Hebrew interlinear UI | none | 2 | M | Word-by-word OT display with Strong's lemma + morphology codes. Strong's data already in `content/sources/strongs_hebrew.json` (2 MB). New template at `/interlinear/<book>/<chapter>`. |
| γ.2 | Greek interlinear UI | γ.1 | 1 | M | Same machinery, NT data. Strong's Greek (1.2 MB) already cached. |
| γ.3 | Patristic commentary kind (`comm-patristic`) | none | 2 | M | New kind in `content/kinds.yaml` with symbol Ⓟ. First 1K-note dump: Augustine on Genesis, Aquinas on the Gospels, Chrysostom on Pauline epistles. All PD. Detector phase + manual review queue. |
| γ.4 | Ethiopian Orthodox commentary kind | γ.3 | 2 | M | `comm-ethiopian-orthodox` kind. Ephrem the Syrian + Eastern fathers. The flagship payload — the Tewahedo Bible's primary differentiator. |
| γ.5 | LXX integration as τ-translation | none | 1.5 | M | Septuagint Greek OT. Joins the τ-cluster (τ.2 candidate). Used by Tewahedo, Eastern Orthodox, NT writers. PD. |
| γ.6 | Vulgate (Latin) | none | 1.5 | M | PD Latin OT+NT. Catholic + Anglican target audiences. |
| γ.7 | Targums (Aramaic OT paraphrases) | none | 2 | M | PD English translations exist (Etheridge). Niche but signals scholarly seriousness. |
| γ.8 | Dead Sea Scrolls variants | none | 2 | M | Where DSS differs from MT, surface as a `comm-textcrit-dss` sidebar note. ~5K theologically meaningful variants. |
| γ.9 | Critical apparatus (NA28-equivalent) | γ.5 | 2 | M | Variant readings with manuscript evidence. PD-equivalent: Tischendorf, Westcott-Hort apparatus. New `comm-textcrit-nt` kind. |

**Track D outcome**: depth that beats every free Bible app's free
tier. The "most extensive" promise is real and demonstrable.

### Track E — reader experience (δ family)

| ID | Title | Depends | Effort | Blast | Notes |
|---|---|---|---|---|---|
| δ.1 | Reading streaks + log | none | 1 | S | localStorage-only; no backend. Quiet bottom-of-page indicator. |
| δ.2 | Bookmarks / highlights / notes | δ.1 | 1.5 | M | JSON sidecar file the reader controls (export/import). Right-click verse → bookmark; long-press → highlight color picker. |
| δ.3 | Verse memorization tool | δ.2 | 1 | M | SM-2 spaced repetition (~50 lines). Pick verses; daily 5-card review at `/memorize`. |
| δ.4 | Audio-sync (verse-level highlighting) | ρ.1 | 1 | M | When audio plays, current verse highlights. Cross-track dependency on the existing ρ.1 audio infrastructure. |
| δ.5 | Dark mode for reader EPUB output | ζ.2 | 0.5 | S | EPUB readers handle this natively but custom CSS in shipped editions helps. |
| δ.6 | Reading-pace tracker | δ.1 | 0.5 | S | "At your current pace, you'll finish in X days." Encouragement, not gamification. |
| δ.7 | Print stylesheet | ζ.4 | 0.5 | S | `@media print` rules for the published HTML edition. |
| δ.8 | PWA install | ψ.22 | 1 | M | Published HTML edition becomes installable. `manifest.json` + service worker for offline. Distribution lever; no App Store. |
| δ.9 | Email subscription for verse-of-day | none | 1 | M | Pure backend: `/api/subscribe/verse-of-day` accepts email; sends daily via SMTP. Built on existing υ.8 RSS. |

**Track E outcome**: shipped editions compete with paid Bible
apps. Memorization + audio-sync are paid-app exclusives elsewhere.

### Track F — executive / business (ε family)

| ID | Title | Depends | Effort | Blast | Notes |
|---|---|---|---|---|---|
| ε.1 | Event log + metrics collector | Δ.15 | 1.5 | M | Append-only `events.jsonl` for every state-change. Lightweight; ~200KB/month at current usage. Foundation for everything below. |
| ε.2 | /exec dashboard MVP | ε.1 | 2 | M | 5 KPI tiles: editions count, notes corpus, AI spend MTD, perf budget health, error rate. Renders from event log. |
| ε.3 | Sales import (KDP/Apple/Google CSV) | ε.2 | 1.5 | M | CSV upload endpoint; per-edition revenue rollup; visible in /exec. |
| ε.4 | Cost-per-edition rollup | ε.2 | 1 | M | AI generation cost + ISBN cost ($125/each from Bowker) + estimated build hours. ROI per edition. |
| ε.5 | Quarterly auto-report PDF | ε.3, ε.4 | 1.5 | M | Composes existing dashboards into a PDF. Auto-emailed end-of-quarter. |
| ε.6 | Distribution channel checklist | ε.2 | 1 | S | Per-edition: which channels (KDP, Apple, Google, archive.org, your site) has it shipped to. Visible in /exec. |
| ε.7 | Press kit auto-build | ε.6 | 1 | M | Per-edition: zip with cover variants (4 sizes), 150-word blurb, 500-word description, sample chapter PDF. |
| ε.8 | SEO audit for shipped HTML | δ.8 | 1 | S | Structured data (JSON-LD), meta tags, sitemap.xml. Run as a Tier-3 check. |

**Track F outcome**: the business becomes legible at a glance.
Decisions on next edition / channel investment have data behind
them.

### Track G — security hardening (ξ.18+)

| ID | Title | Depends | Effort | Blast | Notes |
|---|---|---|---|---|---|
| ξ.18 | CSP nonces | none | 1 | M | Replace `'unsafe-inline'` with per-request nonces. Significantly hardens XSS. |
| ξ.19 | Subresource Integrity (SRI) on CDN scripts | none | 0.25 | S | `integrity="sha384-..."` on Tailwind + Shepherd + Lucide CDN tags. Browser refuses if CDN compromised. |
| ξ.20 | HTTPS-only local dev | none | 0.5 | S | `mkcert` generates locally-trusted certs; serve over `https://localhost`. Enables SW + PWA. |
| ξ.21 | 2FA for admin auth | none | 1.5 | M | TOTP via `pyotp`. Single-password is current. Big win for ever-hosted future. |
| ξ.22 | Backup rotation policy | none | 0.5 | S | `.backups/` rotation: last 7 daily + last 4 weekly + last 12 monthly. Currently unbounded. |
| ξ.23 | Encrypted backups | ξ.22, Δ.16 | 1 | M | PyNaCl libsodium; user holds the key. For unpublished editions. |
| ξ.24 | `pip-audit` in CI | ω.38 | 0.5 | S | Dependency scanning in cloud CI. Already have ξ.5 local; this is the cloud counterpart. |
| ξ.25 | Secret scanning in pre-commit (`gitleaks`) | ω.37 | 0.25 | S | Already have SonarCloud secrets hooks; reinforce locally. Catches secrets BEFORE commit. |
| ξ.26 | License key validation | none | 1.5 | M | Ed25519-signed license keys for commercial editions. Soft enforcement: degraded UI on fail, not crash. |
| ξ.27 | Health check endpoint (`/health`) | none | 0.25 | S | Returns 200 + JSON status. Used by ops dashboards + future load balancers. |
| ξ.28 | Graceful shutdown handler | none | 0.25 | S | SIGINT handler closes sqlite connections cleanly. ~10 lines. |
| ξ.29 | Self-update mechanism | θ chain | 2 | M | `/api/update/check` polls a release URL; download + verify signature + relaunch. Big trust upgrade for shipped desktop. |

**Track G outcome**: A casual security scan (or a real auditor)
finds nothing flagged.

### Track H — matrix expansion (ψ.36+)

| ID | Title | Depends | Effort | Blast | Notes |
|---|---|---|---|---|---|
| ψ.36 | Heatmap mode | none | 1 | M | Color intensity = note count per cell. Toggle in /matrix header. |
| ψ.37 | Compare-two-editions overlay | ψ.36 | 1.5 | M | Pick two editions; render their matrices in one grid with diff highlighting. |
| ψ.38 | Time-travel mode (snapshot diff) | ω.16 ✓ | 1.5 | M | Render matrix at snapshot vN.4 vs vN.5. Visual diff. Massive "what changed?" value. |
| ψ.39 | Bulk-import scenarios from URL | none | 1 | S | Paste `gist.github.com` link → load scenario. Enables peer sharing. |
| ψ.40 | Export matrix as PNG/SVG/PDF | none | 1 | M | For reports + executive docs. SVG generated server-side via simple `<svg>` string. |
| ψ.41 | Matrix annotations | none | 1 | M | Pin a comment to a cell ("intentionally disabled for ESV target audience"). Persisted in scenario YAML. |
| ψ.42 | Macro mode (record + replay) | ψ.29 ✓ | 1.5 | M | Record sequence of actions; replay on another edition. Power-user feature. |
| ψ.43 | Suggested-toggle inference | none | 1.5 | M | "You enabled comm-archaeology for Genesis; want to enable for all OT books?" Heuristic, optional. |
| ψ.35 | (already in PLAN) matrix data-model collapse | none | 1 | L | Parked in PLAN_2026-05-09.md §7. Pre-requisite for some H-track work; surface now. |

**Track H outcome**: /matrix becomes the killer app for serious
editorial work. Diff-against-snapshot alone is a quarterly review
tool.

### Track I — publisher workflow polish (ν.7+, π.6+)

| ID | Title | Depends | Effort | Blast | Notes |
|---|---|---|---|---|---|
| ν.7 | Inline editing standardization | ζ.6, ζ.7 | 1.5 | M | Click → edit-in-place → blur saves. Already partial; standardize across all 14 consoles. |
| ν.8 | Multi-tab support | none | 1 | M | Work on two editions side-by-side. localStorage per-tab state. |
| ν.9 | Workspace layouts | ν.8 | 1 | S | Save current console arrangement; restore on launch. |
| ν.10 | Recently-used quick access | none | 0.5 | S | Last-5 editions/books/scenarios at top of every console. |
| ν.11 | Optimistic UI updates | ζ.6 | 1 | M | Visual state flips immediately on click; rolls back with toast on API fail. |
| π.6 | Cover composition tool | (PROPOSAL_AI_ARTWORK B.AI.2) | 2 | M | Drag-drop text + AI art composite. Konva.js via CDN. Already in PLAN as π.6; now scoped. |
| π.7 | Diff viewer for editions | ω.16, ψ.38 | 1.5 | M | Pick two snapshots; field-by-field diff with visual highlights. |
| π.8 | Approval workflow | none | 1.5 | M | Optional per-edition gate: proofreader signs off before "ship" button enables. |
| π.9 | ISBN registration assistant (Bowker API) | none | 2 | M | Bowker briefed per memory. Edition gets an ISBN field; "Register" calls Bowker API + stamps edition. |
| π.10 | Auto-proofread (LanguageTool) | none | 1 | M | Grammar check on note bodies. Optional, opt-in per edition. |
| π.11 | Verse-coverage gap detector elevation | none | 0.5 | S | Already partial in `attribution_audit`. Surface in /exec + per-edition view. |
| π.12 | Source-coverage parity check | π.11 | 1 | S | "Edition A uses Rashi for Genesis; Edition B doesn't — intentional?" Diff display. |

**Track I outcome**: publisher workflow is 3-5× faster. The
compress-days-into-minutes promise.

### Track J — AI features (B.AI.* — see PROPOSAL_AI_ARTWORK)

These all live in `PROPOSAL_AI_ARTWORK.md` already. Pinned here
for cross-reference + dependency linkage:

| ID | Title | Depends | Effort | Blast | Notes |
|---|---|---|---|---|---|
| B.AI.1 | Main cover AI generation MVP | publisher decisions | 1.5 | M | OpenAI gpt-image-1 + budget gate + /covers integration. |
| B.AI.2 | Per-book cover AI generation | B.AI.1 | 1.5 | M | + `content/_ai_prompts.yaml` template system. |
| B.AI.3 | Second provider (Stability AI) | B.AI.1 | 1 | M | Provider-agnostic abstraction validation. |
| B.AI.4 | Sharable verse cards | B.AI.1, ζ.4 | 1.5 | M | Long-press verse → "share as 1080×1080 image with AI background + typography." Massive social distribution lever. |
| B.AI.5 | AI co-pilot (Cmd+J anywhere) | ζ.8 | 2 | M | "What does this do?" or "Create a scenario where only rabbinic + patristic kinds are enabled." Uses existing Anthropic key. |
| B.AI.6 | Daily devotional auto-curation | χ.11, δ.9 | 1.5 | M | AI picks today's verse based on liturgical calendar + reader history. Emails it. |
| B.AI.7 | Marketing copy generator | B.AI.5 | 1 | S | Given an edition's metadata, draft Amazon/Apple Books product copy. |

**Track J outcome**: AI integration that feels like magic across
publisher + reader + business surfaces.

### Track K — distribution / marketing (ο family)

| ID | Title | Depends | Effort | Blast | Notes |
|---|---|---|---|---|---|
| ο.1 | KDP submission helper | ε.7 | 1 | M | Validates an edition's EPUB against Amazon KDP's spec; generates the required metadata sheet. |
| ο.2 | Apple Books submission helper | ε.7 | 1 | M | Same shape, Apple's epubcheck-strict validation (epubcheck briefed per memory). |
| ο.3 | Google Play Books submission helper | ε.7 | 1 | M | Same shape; Google's looser validation. |
| ο.4 | Archive.org auto-upload | ε.7 | 1 | M | Per memory, archive.org account is available. Endpoint: drop edition → archive.org API push. Free distribution. |
| ο.5 | Press kit auto-build (consolidates ε.7) | ε.7 | 0 | — | Same deliverable; ε.7 is the canonical. ο.5 is just the marketing-side name. |
| ο.6 | "Built with YHWH" badge in shipped editions | none | 0.5 | S | Small footer linking back to your platform in every shipped Bible. Brand awareness. |
| ο.7 | Affiliate link generator | ε.3 | 1 | M | Per-edition referral codes; track per-reader source. |

**Track K outcome**: shipping an edition to 5 channels takes
minutes, not days. Distribution is no longer the bottleneck.

### Track L — database evolution (Δ.10+)

| ID | Title | Depends | Effort | Blast | Notes |
|---|---|---|---|---|---|
| Δ.10 | Schema migration framework | none | 1 | M | Lightweight 30-line custom migration runner (or `yoyo-migrations`). Tracks `schema_version`; replays migrations. |
| Δ.11 | WAL mode for corpus_index | Δ.10 | 0.5 | S | Enable Write-Ahead Logging. Lets reads happen during rebuild. 10-line change. |
| Δ.12 | FTS5 full-text search | Δ.10 | 1.5 | M | SQLite FTS5 virtual table for note bodies. ~10× faster than LIKE; phrase queries + snippets. `api_search_notes` rewires to FTS5. |
| Δ.13 | sqlite-vec for vector similarity | Δ.10 | 1 | M | Vector ops in SQLite. Plays into χ-AI-xref's planned embedding work. Avoids pulling in Postgres + pgvector. |
| Δ.14 | DuckDB read-replica for analytics | none | 1 | M | Read-only OLAP layer for /exec dashboard. Querying "average notes per kind per edition over time" is slow in plain SQLite; DuckDB is built for this. |
| Δ.15 | Event log (`events.jsonl`) | Δ.10 | 1 | M | Append-only event store for every state-change. Foundation for ε.1+. |
| Δ.16 | Encrypted backups | Δ.10 | 1 | M | PyNaCl libsodium encryption for `.backups/`. User holds the key. Feeds into ξ.23. |

**Track L outcome**: data layer scales to the LXX integration +
embedding workloads without re-architecting. Analytics queries
that currently take seconds drop to milliseconds.

---

## 5. Dependency graph

ASCII rendering of how phases unlock each other. Read top-to-bottom
within each chain; cross-chain arrows are shown explicitly.

```
                         ┌──────────────┐
                         │   ω.35-B.4   │
                         │ ed/customize │
                         └──────┬───────┘
                                ▼
                         ┌──────────────┐
                         │   ω.35-B.5   │
                         │ exports/build│
                         └──────┬───────┘
                                ▼
                         ┌──────────────┐
                         │   ω.35-B.6   │
                         │preflight/help│
                         └──────┬───────┘
                                │ unblocks
                                ▼
              ┌────────────┼─────────────────┐
              ▼            ▼                 ▼
         ω.42 components  ω.43 api playground  ω.45 OpenAPI

  ω.37 pre-commit ──→ ω.38 GH Actions ──→ ξ.24 pip-audit
       │                                       in CI
       └────→ ξ.25 gitleaks

  ζ.1 CSS vars ─┬─→ ζ.2 dark mode ──→ ζ.3 sepia ──→ δ.5 reader dark
                │                          │
                ├─→ ζ.4 typography ──→ ζ.7 skeletons ──→ ζ.10 transitions
                │      │
                │      ▼
                ├─→ ζ.5 iconography ──→ ζ.8 cmd palette ──→ B.AI.5 co-pilot
                │                              │
                ├─→ ζ.6 toasts                 └─→ ν.11 optimistic UI
                │
                └─→ ζ.9 first-run tour
                    (needs ζ.5 + ζ.6)

  γ.1 Hebrew interlinear ─→ γ.2 Greek interlinear (parallel)
       │
       └→ feeds: any future "study Bible" edition

  γ.3 comm-patristic ──→ γ.4 comm-ethiopian-orthodox
       │                       │
       └─ flagship payload     └─→ Tewahedo flagship final
                                   completion

  γ.5 LXX ──┐
  γ.6 Vulgate ──┼──→ γ.9 critical apparatus
  γ.7 Targums ──┘
  γ.8 DSS variants ──→ comm-textcrit-dss kind

  Δ.10 migrations ─┬─→ Δ.11 WAL
                   ├─→ Δ.12 FTS5 ──→ search-everywhere upgrade
                   ├─→ Δ.13 sqlite-vec ──→ χ-AI-xref embeddings
                   ├─→ Δ.15 event log ──→ ε.1 metrics collector
                   │                            │
                   │                            ▼
                   │                       ε.2 /exec dashboard
                   │                            │
                   │                            ├─→ ε.3 sales import
                   │                            ├─→ ε.4 cost rollup
                   │                            ├─→ ε.6 channel checklist
                   │                            └─→ ω.44 perf chart
                   │
                   └─→ Δ.16 encrypted backups ──→ ξ.23 (security)

  ω.16 snapshots ✓ ──→ ψ.38 time-travel ──→ π.7 diff viewer
                            │
                            └─→ release-management workflow

  PROPOSAL_AI_ARTWORK:
    B.AI.1 main cover ──→ B.AI.2 per-book ──→ π.6 cover composer
         │                     │                 │
         │                     └─→ B.AI.4 verse cards
         │                                │
         │                                └─→ social distribution
         │
         └─→ B.AI.3 2nd provider (parallel)

    ζ.8 cmd palette ──→ B.AI.5 co-pilot ──→ B.AI.7 marketing copy

    χ.11 liturgical (planned) ──→ B.AI.6 daily devotional
         │
         └─→ δ.9 verse-of-day email subscription

  Distribution chain:
    ε.7 press kit ─┬─→ ο.1 KDP submit
                   ├─→ ο.2 Apple submit
                   ├─→ ο.3 Google submit
                   └─→ ο.4 archive.org

  Reader chain:
    δ.1 streaks ──→ δ.2 bookmarks ──→ δ.3 memorization
         │                                │
         │                                └─→ SM-2 spaced repetition
         │
         └─→ δ.6 pace tracker

    ψ.22 (planned) PDF/MOBI/HTML ──→ δ.8 PWA ──→ ε.8 SEO audit
                                                       │
                                                       └─→ shipped HTML
                                                           discoverable
```

---

## 6. Recommended 6-month sequence

Each month is ~6–8 sessions. Sequencing prioritizes:
1. Foundations that unlock subsequent tracks
2. Bang-for-buck early wins (visible wins ship publisher confidence)
3. Pacing AI features around publisher decisions (PROPOSAL_AI_ARTWORK §8)

### Month 1 — Foundation (≈ 6 sessions)
1. **ω.35-B.4** editions/customize extraction
2. **ω.35-B.5** exports/build extraction
3. **ω.35-B.6** preflight/audit/help extraction (closes the file split)
4. **ω.37** pre-commit hook ← **shipped in this commit**
5. **ω.38** GitHub Actions CI
6. **Δ.10** schema migration framework

**End-of-month state**: web.py file split done; CI prevents next
ruff-drift / monkeypatch regression; schema migrations enabled.

### Month 2 — Modernization (≈ 7 sessions)
1. **ζ.1** CSS variable theming foundation
2. **ζ.2** dark mode
3. **ζ.4** typography upgrade
4. **ζ.5** iconography pass
5. **ζ.6** toast notifications
6. **ζ.7** skeleton loaders
7. **ζ.8** command palette (Cmd+K)

**End-of-month state**: the program looks like a 2026 product.
Dark mode default optional. Toolbar feels modern.

### Month 3 — Content depth wave 1 (≈ 7 sessions)
1. **γ.1** Hebrew interlinear UI
2. **γ.2** Greek interlinear UI
3. **γ.3** Patristic commentary kind (Augustine on Genesis dump)
4. **γ.5** LXX integration
5. **Δ.12** FTS5 full-text search
6. **δ.1** Reading streaks
7. **δ.2** Bookmarks / highlights

**End-of-month state**: corpus is meaningfully deeper. Search
feels instantaneous. Reader features start landing.

### Month 4 — Publisher polish + AI MVP (≈ 7 sessions)
1. **B.AI.1** Main cover AI generation MVP (publisher decision
   needed by start of month)
2. **B.AI.2** Per-book cover AI generation
3. **ν.7** Inline editing standardization
4. **ν.10** Recently-used quick access
5. **π.9** ISBN registration assistant (Bowker)
6. **ψ.36** Matrix heatmap mode
7. **ω.39** Hot-reload for templates (dev quality of life)

**End-of-month state**: AI cover generation in production for the
publisher. Workflow accelerates measurably.

### Month 5 — Executive + distribution (≈ 7 sessions)
1. **Δ.15** Event log
2. **ε.1** Metrics collector
3. **ε.2** /exec dashboard MVP
4. **ε.3** Sales import (KDP/Apple/Google CSV)
5. **ε.6** Distribution channel checklist
6. **ε.7** Press kit auto-build
7. **ο.4** Archive.org auto-upload

**End-of-month state**: business is legible. Shipping an edition
to 4 channels takes minutes.

### Month 6 — Hardening + the "amazing" tier (≈ 7 sessions)
1. **B.AI.4** Sharable verse cards
2. **B.AI.5** AI co-pilot (Cmd+J)
3. **ζ.9** First-run tour
4. **γ.4** Ethiopian Orthodox commentary kind (flagship payload)
5. **ξ.18** CSP nonces
6. **ξ.21** 2FA for admin auth
7. **ξ.26** License key validation

**End-of-month state**: visible "amazing" features ship. Security
hardened. First commercial release-ready.

---

## 7. Tool catalog — what we build along the way

Each tool below is a small, focused utility that supports the
broader plan. Listed here so they don't get forgotten.

| Tool | Lives at | Track | Status | Purpose |
|---|---|---|---|---|
| Pre-commit hook | `.githooks/pre-commit` | ω.37 | **SHIPPED 2026-05-10** | Runs ruff format --check + lint_rules before commit |
| GitHub Actions workflow | `.github/workflows/ci.yml` | ω.38 | ◯ open | Cloud CI runs full test suite |
| Hot-reload watcher | `scripts/dev/watch_templates.py` | ω.39 | ◯ open | File-watch + SSE auto-refresh |
| Component preview server | `scripts/dev/components_server.py` + `/dev/components` console | ω.42 | ◯ open | Per-template iteration |
| API playground console | `/dev/api` | ω.43 | ◯ open | Postman-like UI; self-served via route tables |
| OpenAPI/Swagger generator | `scripts/dev/gen_openapi.py` + `/apidocs` | ω.45 | ◯ open | Composes api_help_data into OpenAPI 3.1 spec |
| ADR generator | `scripts/dev/promote_adrs.py` | ω.46 | ◯ open | Promotes large CHANGELOG entries to dev/adr/ |
| Schema migration runner | `scripts/core/migrations.py` | Δ.10 | ◯ open | 30-line custom migration runner |
| Event log writer | `scripts/core/event_log.py` | Δ.15 | ◯ open | Append-only `events.jsonl` |
| Metrics collector | `scripts/core/metrics.py` | ε.1 | ◯ open | Composes event log → KPI rollups |
| Press kit builder | `scripts/build_press_kit.py` | ε.7 | ◯ open | Per-edition zip: covers + blurbs + sample chapter |
| KDP/Apple/Google validators | `scripts/dev/check_*_spec.py` | ο.1-3 | ◯ open | Format compliance checks per channel |
| Archive.org uploader | `scripts/dev/upload_archive_org.py` | ο.4 | ◯ open | API push to archive.org |
| Bowker ISBN client | `scripts/core/bowker.py` | π.9 | ◯ open | ISBN registration API client |
| LanguageTool client | `scripts/core/languagetool.py` | π.10 | ◯ open | Grammar check via the LanguageTool HTTP API or local server |
| SM-2 spaced-repetition engine | `scripts/core/sm2.py` | δ.3 | ◯ open | ~50 lines; per-card review intervals |
| AI co-pilot router | `scripts/core/copilot.py` | B.AI.5 | ◯ open | Wraps Anthropic API + intent classification |
| Verse-card renderer | `scripts/core/verse_card.py` | B.AI.4 | ◯ open | Composite AI bg + typography into 1080×1080 PNG |
| Icon pipeline | `scripts/build_icons.py` | PROPOSAL_AI_ARTWORK §6 | ◯ open | .ico + .icns + favicon derivation |
| Build-icons stub | `scripts/build_icons_stub.py` (placeholder) | now | ◯ optional | Empty scaffold; surfaces the gap until the user provides the master PNG |

---

## 8. Risk register

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| Track ambition overruns publisher time | Medium | Medium | Sequence in §6 is one plausible path; cut tracks freely. Foundation tracks (A + L.Δ.10) unblock the most downstream work — finish those first. |
| AI costs exceed budget | Low | Medium | PROPOSAL_AI_ARTWORK §3.5 hard cap; B.AI.5 (co-pilot) also gates per-invocation. |
| Schema migration breaks corpus_index | Low | High | Δ.10 ships with reversible migrations + a SHA256 snapshot of pre-migration sqlite stored in .backups/. |
| Dark mode breaks reader EPUBs | Low | Medium | ζ.2 changes only the publisher UI; δ.5 separately ships dark-mode reader EPUB. Different code paths. |
| Heavy new dependency creep | Medium | Medium | Invariants I.1 + I.2 forbid build steps + frameworks. Every CDN library justified per phase; total CDN size capped at ~500KB. |
| Test suite slowdown from new tracks | Medium | Low | Perf budgets (ω.6) enforce per-test ceilings. ω.44 surfaces regression visually. |
| GitHub Actions CI surfaces flaky tests previously masked | High | Low | Pre-existing flakes (test_compute_key_is_deterministic, test_api_matrix_cold_under_budget) are known shared-corpus-contention; address with serialization in a small ω.x slice. |
| Publisher gets ahead of platform on artwork → mismatched expectations | Medium | Low | Quarterly review: section §9 decisions revisited at month 3 + month 5. |
| Security hardening (ξ.18-29) breaks something on the way | Low | High | Each ξ phase is small, atomic, individually testable. CI guard + protected-paths guard catch data-side regressions; per-phase tests catch behavior regressions. |
| AI-generated content slips through review → reputational risk | Low | High | Pre-acceptance human review (PROPOSAL_AI_ARTWORK §7); audit log captures everything; never auto-ship AI-generated text or imagery. |
| Bowker ISBN integration changes their API | Low | Medium | π.9 abstracts behind `scripts/core/bowker.py` so a rewrite is contained. |

---

## 9. Publisher decisions needed

Before greenlighting tracks, please confirm:

### 9.1 Month-2 modernization scope
- **Dark mode default**: opt-in (toggle in header) OR follow-OS-preference?
  Recommended: follow-OS-preference with header override.
- **Typography**: Inter + Crimson Pro recommended. Approved?
- **Icon set**: Lucide (slimmer) vs Heroicons (more variants).
  Recommended: Lucide.

### 9.2 Month-3 corpus depth scope
- Which γ phases to ship first? Recommended order:
  γ.3 patristic (broadest impact) → γ.4 Ethiopian Orthodox (flagship
  payload) → γ.1 Hebrew interlinear (scholarly depth).
- LXX (γ.5): which English translation alongside? Brenton (PD,
  Victorian English) is the standard; or pair with NETS (modern,
  Creative Commons).

### 9.3 AI feature priority (Month 4-6)
- Confirm B.AI.1-2 from PROPOSAL_AI_ARTWORK first; B.AI.5
  (co-pilot) follows in Month 6.
- B.AI.4 sharable verse cards: Instagram/Twitter aspect ratios
  (1080×1080 + 1080×1920 for Stories)?

### 9.4 Distribution channels (Month 5)
- Which channels to prioritize? Recommended: KDP first (largest
  audience), then Apple Books (clean integration with epubcheck),
  then archive.org (free PD distribution), then Google Play
  Books last.

### 9.5 Security tier
- Soft enforcement (warning banner on license-key fail) or hard
  (refuse to launch)? Recommended: soft for v1; hard for v2 if
  piracy becomes measurable.
- Single password admin auth keeps working through ξ.21 (2FA
  is additive, not replacement).

### 9.6 Tooling philosophy
- Self-hosted (everything in-process) OR optional SaaS hooks
  (e.g., Sentry for crash reports, Plausible for analytics)?
  Recommended: keep everything self-hosted; offer Sentry/Plausible
  as opt-in env-var hooks later.

---

## 10. Integration with PLAN_2026-05-09.md

This proposal does NOT replace `PLAN_2026-05-09.md`. The active
plan continues. This document adds tracks/phases alongside.

Integration rules:
- **The lint rule `plan_singular`** stays satisfied: there's still
  exactly one `dev/PLAN_*.md`. Proposals coexist.
- **New Greek-letter phases (γ, δ, ε, ζ, ο) and family extensions
  (ω.37+, ξ.18+, ψ.36+, ν.7+, π.6+, Δ.10+, B.AI.*)** will be
  back-filled into `PLAN_2026-05-09.md` §7 when each phase ships,
  matching the existing convention.
- **Cluster matrix** (`PLAN_2026-05-09.md` §8) gains:
  - **MODERNIZATION** cluster: ζ.* phases
  - **CORPUS-DEPTH** cluster: γ.* phases
  - **READER** cluster: δ.* phases
  - **EXECUTIVE** cluster: ε.* phases
  - **DISTRIBUTION** cluster: ο.* phases
  - **DATABASE** cluster: Δ.10+ phases
- **Existing planned phases** (ψ.21, ψ.25, χ.2-5, τ.2-12, etc.)
  remain untouched. Their priority is publisher's call; this
  proposal doesn't reorder them but does provide dependency
  context (e.g. χ.10 atlas feeds γ.* per-pericope map view).
- **AUDIT_2026-05-11 §7 sequence** continues:
  ω.35-A complete → ω.35-B.4-6 (Track A) → free path for everything
  else.

When this proposal's first phase ships (ω.37 pre-commit hook,
included in this commit), it triggers an addendum entry in
`PLAN_2026-05-09.md` §7 noting "ω.37 ✓ shipped 2026-05-10" via
the standard CHANGELOG workflow.

---

## 11. Acceptance criteria — what "spotless + amazing" looks like

When the proposal's Month 1-6 rollout is complete, the following
must be observable:

### Spotless
- [ ] Full test suite (2100+) green on 3 consecutive CI runs.
- [ ] No `ruff format --check` failures in the last 30 days
      (pre-commit prevents the class).
- [ ] No protected-paths-guard failures in the last 30 days.
- [ ] No `unsafe-inline` in CSP headers (ξ.18 done).
- [ ] All CDN scripts have `integrity` attributes (ξ.19 done).
- [ ] Backup rotation is bounded; .backups/ size stable.
- [ ] /health endpoint returns 200; `/api/preflight` returns
      `status: ready`.
- [ ] All 14 consoles render in <1s on cold start, <200ms warm.
- [ ] Cross-edition consistency check: every edition has a main
      cover + an attribution audit pass + at least 1 snapshot.

### Amazing
- [ ] First-run tour exists and is < 90 seconds.
- [ ] Dark mode toggle works in <50ms.
- [ ] Cmd+K command palette opens in <100ms with all actions
      indexed.
- [ ] AI cover generation produces 3 acceptable variants in <30s.
- [ ] AI co-pilot (Cmd+J) responds in <5s.
- [ ] Sharable verse cards generate in <8s; output is
      visually distinctive per book.
- [ ] /exec dashboard renders in <2s with the last 90 days of
      KPI history.
- [ ] At least 5 of: Hebrew interlinear, Greek interlinear,
      LXX, Vulgate, Targums, DSS variants, Patristic comm,
      Ethiopian Orthodox comm, critical apparatus — are
      reader-visible.
- [ ] Press kit auto-build produces an Amazon-ready zip in <60s.
- [ ] Shipping a new edition to 4 channels (KDP + Apple +
      Google + archive.org) takes <15 minutes of operator
      attention.

### Documentation
- [ ] Every phase shipped has a CHANGELOG entry, IN_FLIGHT
      update, SESSION_STATE update, and ≥3 pin tests.
- [ ] ADRs auto-promoted for any CHANGELOG entry > 50 lines.
- [ ] OpenAPI spec at `/apidocs` reflects every /api/* route.
- [ ] README has a 60-second pitch + a 5-minute walkthrough.

---

— end of proposal —
