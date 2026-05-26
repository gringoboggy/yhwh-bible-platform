# Deep Audit — 2026-05-23 (every-file sweep + forward plan)

**Type:** heavy parallel-subagent sweep (the deferred in-depth audit).
**Spec:** `docs/superpowers/specs/2026-05-23-deep-audit-and-forward-plan-design.md`
**Plan:** `docs/superpowers/plans/2026-05-23-deep-audit-and-forward-plan.md`
**Scope:** git repo `YHWH v2.4/` only. Fix safe inline (verified, uncommitted); queue risky.

---

> **➤ 2026-05-26 RECONCILIATION (read first — this 2026-05-23 ledger is now ~95% historical).** Nearly every finding has shipped. **Phase 3 (below) applied 17 SAFE-FIXes** inline (B1.3/B1.4/B2a.6/C2.refactor/B2b.2/A3/A7/C1.chap/C3a.errno/C3b.css/C2.devnull/T2/C3a.shipretail/B2b.3/B2b.8/C1.fixname/C1.toc). The headline CRITICAL/HIGH items all closed in later sessions: **★BUGCLUSTER-BOOKCODE** (code-fix `c41e6d2` + phi/jam corpus-regen `309c0f7` + 667-xref normalization → unresolved=0) · **G1/G2 security** (`0892270`) · **CC0 relicense** E.license/E.copyright (2026-05-24) · **★C2.deadchecks** (a11y→preflight `1ae0d23` + vulture/mypy/pip-audit→`scripts/ci.py`) · **A1/A6/A9/A12** (`fb50001`) · **A8 / A11 / B1.S** (god-module splits + the `_editions_index` de-dup) · **B1.8/B1.9** (`6e5adad`) · **B1.6 / F1** (`c45ca38`). **No CRITICAL/HIGH remains open.** Remaining = a low-severity tail: stale docstrings/counts needing per-item verification (C3b.docstrings · C2.misc · C2.stalecounts · F2 · F9 · E.version · E.schemas · E.dangling · E.readme · E.handoff) · big refactors (A.N error-envelope · C3b.atscaledup shared base · D.dup test-monolith) · quarantined-module cleanup (B2a.1/2 license_key · C3a.release/printcover/splitweb · F3 Brenton stubs) · latent-SEC notes (B2a.9/G4 positional-secret redaction · G5/C3b.bannerxss · B2a.13) · TIER-3 provenance (F5 geez/amharic-en `_meta`) · doc archival (E.archival) · one user-action (G3 — rotate the Voyage key). Fresh re-audit (all gates re-run from scratch) = `dev/AUDIT_2026-05-26-FINDINGS.md`.

---

## Baseline (green, pre-audit — the regression anchor)

Captured 2026-05-23 ~23:35 EDT.

| Dimension | Value | Tool |
|---|---|---|
| Git HEAD | `42a59e0` (clean tree; only the 2 new audit docs untracked) | `git log/status` |
| lint_rules | **16 pass / 0 warn / 0 fail** | `scripts/lint_rules.py` |
| trace_matrix | **0 unresolved refs** (all 11 editions resolve) | `dev/trace_matrix.py` |
| trace_repo | **0 undocumented top-level dirs** (10 dirs) | `dev/trace_repo.py` |
| validate_taxonomy | **67,713 / 67,713 attributed (100%)** | `scripts/validate_taxonomy.py` |
| validate_schemas | **6/6 ok, 0 fail/error (CLEAN)** | `scripts/validate_schemas.py` |
| ebible verify | **errors=0**, warn=71, info=565, **24,015 / 24,015 paired** | `scripts.ebible verify` |
| Tests collected | **7,064** | `pytest --collect-only` |
| Tracked files | 3,141 (994 .py = ~387 code + ~607 data; 1,701 .json; 140 .md; 44 .yaml) | `git ls-files` |

**Pre-seeded observations:**
- Root-level `*-pytest.log`, `.ingest_1en.log`, `_tau6x2t_jub_ocr.log`, `.wget-hsts`, `.env` are all **gitignored, not tracked** — `.gitignore` is doing its job; no tracked junk of that class.
- `ebible verify` carries **71 warnings + 565 info** (non-blocking) — examine during synthesis (Phase 2).

---

## Findings ledger

> Filled in Phase 2 after the read-phase sweep. Disposition: SAFE-FIX (fixed inline, verified) · QUEUED (needs user go/no-go) · WON'T-FIX (reason given).

| ID | Finding | Location | Axis | Severity | Disposition |
|---|---|---|---|---|---|
| **B1.1** | `NT_BOOKS` uses non-canonical codes `php`/`jas` → Greek detector SKIPS Philippians/James; Hebrew detector RUNS on them (test uses `"jas"`, masking it) | `scripts/core/detectors.py:142-169,338-366` | bug | **HIGH** | QUEUED (behavior; quantify blast radius via prospect run) |
| B1.2 | `KENYON_BOOK_NAME_TO_CODE` maps to non-existent `php`/`jas`/`jol` → broken `#vnote-php-*` anchors | `scripts/core/sources.py:1062,1102-1103,1122-1123` | bug | med | QUEUED (same code-family fix) |
| B1.3 | Duplicate dict key `"soul"` (both →H5315) | `scripts/core/detectors.py:93,107` | junk | low | SAFE-FIX |
| B1.4 | Dead dict-comprehension computed + discarded | `scripts/core/corpus_index.py:1374` | dead | low | SAFE-FIX |
| B1.5 | `_books_yaml_path()` documented as preferred resolver but `load_books()` bypasses it | `scripts/core/config.py:51-58 vs 273` | stale | med | QUEUED (wire-or-trim docstring) |
| B1.6 | Fragile `or` idiom in psalm-fix lookup (breaks if a fix maps to None/omit) | `scripts/core/versification.py:1478` | bug(latent) | low | QUEUED (note) |
| B1.7 | `_BOOK_CODE_ALIASES` incomplete (missing php/jol/ezk family) | `scripts/core/sources.py:66-83` | bug | low | QUEUED (verify commentary JSONs) |
| B1.8 | `_default_completion_fn` duplicated across 2 AI clients | `scripts/core/sources_ai_clients.py` (post-split) | dup | low | **DONE 2026-05-26** — shared `_AnthropicClient` base (`__init__`/`_valid_codes`/`_default_completion_fn` + cache wiring; subclasses set `DEFAULT_MODEL`/`_CACHE_TTL`/`_OUTPUT_SCHEMA` + keep their own `attribution`/`propose_xrefs`/`draft_note`); per-client TTL+schema pinned by new wiring tests |
| B1.9 | 6 commentary loader classes are ~540 lines of near-clone (differ only in path + field name) | `scripts/core/sources_commentary.py` (post-split) | dup | med | **DONE 2026-05-26** — shared `_CommentaryCorpus` base (loaders → thin subclasses; 6 dataclasses kept distinct for field-name/docstring/`isinstance`); uniform-contract test `tests/test_commentary_loaders.py` |
| B1.S | `sources.py` is a 2,950-line god-module (4 unrelated concerns) | `scripts/core/sources.py` | better | med | QUEUED/plan (split: lexicon/commentary/ai_clients/ai_prompts) |
| B1.N1 | matrix.py ψ.35 frozen-dataclass layering re-evaluated | `scripts/core/matrix.py` | better | — | WON'T-FIX (verdict holds; sound idiom) |
| B1.N2 | versification load-time `assert`s vanish under `python -O` | `scripts/core/versification.py:320,329,341` | risk | low | QUEUED (note; confirm no -O ship path) |
| A1 | `_send_dict_result` dead method (superseded by `_dispatch_table_result`) | `scripts/web.py:4220-4234` | dead | med | SAFE-FIX (verify no test ref) |
| A2 | `_compute_attribution_audit_uncached` orphaned (cached wrapper calls corpus_index) | `scripts/web.py:2975-3051` | dead | low | QUEUED (wire-as-fallback or delete) |
| A3 | Greek normalizer `lstrip("GgH")` strips `H` too (benign-latent) | `scripts/api/greek.py:39` | bug | low | SAFE-FIX |
| A4 | `enable_ai_notes` writable but not surfaced in `api_customize_data` | `scripts/api/editions.py:575 vs web.py:1494-1532` | better | low | SAFE-FIX (additive, back-compat) |
| A5 | `api_save`/`api_delete` raw KeyError/ValueError as 400 body (no field validation) | `scripts/web.py:238-250,905-923` | bug | med | QUEUED (error-shape) |
| A6 | `api_sources_for_book` docstring has wrong tuple field order | `scripts/web.py:993-994` | stale | low | SAFE-FIX |
| A7 | scenario "overwritten" flag computed AFTER the write (always True) | `scripts/api/scenarios.py:379-386` | bug | low | SAFE-FIX |
| A8 | `_editions_index()` duplicated across 4 api modules (config.editions_by_id exists) | `api/press_kit.py:25,license.py:27,distribution.py:48,archive_org.py:26` | dup | low | QUEUED (refactor) |
| A9 | `_inject_script_nonces` docstring describes an unimplemented design | `scripts/web.py:4145-4163` | stale | low | SAFE-FIX |
| A10 | Mutation handlers return bare `{"error"}` → sent as HTTP **200** not 4xx | `scripts/web.py:3717,909,919,931,933 + editions.py:228-246` | bug | med | QUEUED (NEEDS-VERIFY tests may pin 200) |
| A11 | web.py still a 5,214-line god-module (diff/sample/build-tracker/backup/attrib clusters inline) | `scripts/web.py` | better | low | QUEUED/plan (Track D extraction) |
| A12 | Orphaned `# ===` section-header banners (bodies moved to templates/) | `scripts/web.py:5064-5147` | junk | low | SAFE-FIX |
| A13 | `do_POST` falls through to `do_PUT()` → double `_check_admin_auth()` | `scripts/web.py:5061` | better | low | QUEUED (low) |
| A14 | `api_export_build` timeout returns `http:504` but adapter sends 500 | `exports.py:185-193 vs web.py:4962-4969` | bug | low | QUEUED (low) |
| A.N | Architectural: 3 coexisting API error-shapes (`{status,http,code}` / bare `{error}`→200 / `{ok:False}`→400) | `scripts/web.py` + `scripts/api/*` | better | med | QUEUED/plan (unify error envelope) |
| **B2a.7** | `preview` interpolates note `body` HTML **unescaped** on /customize+/wizard render path (bypasses build sanitizer); AI-authored bodies share the store | `scripts/core/preview.py:128-131` | **SEC** | **HIGH** | QUEUED (route body→`sanitize_html`; verify vs preview tests) |
| **B2a.12** | `http._check_allowlist` returns early on empty host → `file:///…` bypasses SSRF guard (LFI) | `scripts/core/http.py:89-92` | **SEC** | **HIGH** | QUEUED (reject non-http(s) schemes; verify callers) |
| B2a.9 | `audit_log` redaction is name-based only; positional secret args leak (truncated) | `scripts/core/audit_log.py:285-311` | SEC | med | QUEUED (redact positionals or document kwargs-only) |
| B2a.4 | `_escape_text`/`_escape_attr` byte-identical in html_sanitize + html_sandbox (divergence risk) | `core/html_sandbox.py:215-220 vs html_sanitize.py:464-469` | dup | med | QUEUED (import from one source) |
| B2a.6 | Dead bare expression — note label computed + discarded, never rendered | `scripts/core/preview.py:117` | bug | med | SAFE-FIX (assign+render or delete) |
| B2a.11 | `http.get/put` docstrings say "warn and continue" but code now fails closed (raises) | `scripts/core/http.py:146-151` | stale | med | SAFE-FIX (docstring) |
| B2a.1 | `license_key.verify` has dead `split(":")` + stream-of-consciousness narration comments | `scripts/core/license_key.py:168-223` | junk | med | QUEUED (quarantined module — low value) |
| B2a.2 | License parse fails on date-only `expires` (regex needs `T`); asymmetric vs `mint` | `scripts/core/license_key.py:216-220` | bug | med | QUEUED (quarantined module) |
| B2a.3 | `_AISandbox` pass-2 has no content-drop guard (relies on pass-1) | `scripts/core/html_sandbox.py:188-192` | SEC | low | QUEUED (add drop-guard or payload test) |
| B2a.5 | `safe_path` doesn't reject Windows reserved device names (still contained) | `scripts/core/safe_path.py:78,86-92` | SEC | low | WON'T-FIX (contained) / optional |
| B2a.13 | installed-mode build-output path math may differ from docstring | `scripts/core/paths.py:251-276` | bug | low | QUEUED (NEEDS-VERIFY installed mode) |
| B2a.15 | `archive_org` error echoes `response_body[:200]` into UI envelope | `scripts/core/archive_org.py:260` | SEC | low | WON'T-FIX (single-user own-creds) |
| B2a.C | **Commercial cluster adjudication**: `updates.py`=**DEAD** (no prod caller); sales/distribution/license_state/license_key/archive_org=**QUARANTINED** (route-reachable, pivot-dead); press_kit=**LIVE** (`resolve_cover_path`) | `scripts/core/{sales,distribution,license_*,archive_org,press_kit,updates}.py` | dead/better | med | QUEUED/plan (delete updates.py; decide quarantine route de-registration) |
| B2b.2 | `epubcheck.py` `subprocess.run` ×2 missing `stdin=DEVNULL` (Windows WinError-6 hazard) | `scripts/core/epubcheck.py:81,223` | bug | low-med | SAFE-FIX (add DEVNULL) |
| B2b.3 | `reading_plans` docstring says integration "deferred (ψ.19.1)/no-op" but it SHIPPED | `scripts/core/reading_plans.py:18-25` | stale | low | SAFE-FIX (docstring) |
| B2b.1 | `manuscript_manifest`/`edition_templates` hard `import yaml` vs lazy/guarded elsewhere | `core/manuscript_manifest.py:38, edition_templates.py:41` | smell | low | QUEUED (consistency) |
| B2b.6 | `core/migrate.py` (SQL DDL) vs `scripts/migrate.py` (user-data) name collision | `core/migrate.py` vs `scripts/migrate.py` | smell | low | QUEUED (rename one) |
| B2b.9 | `manuscript_vision` docstring "≤8-folio cap" is the LRU image cache, not a per-request cap | `core/manuscript_vision.py:66 + docstring:22` | stale | low | SAFE-FIX (docstring) |
| B2b.8 | `summary()` uses `lambda` assigned to local (`# noqa: E731`) | `core/manuscript_index.py:282` | junk | trivial | SAFE-FIX (optional inline def) |
| B2b.7 | `migrate.apply_pending` non-atomic DDL/bookkeeping window (idempotency-mitigated, self-flagged) | `core/migrate.py:139-169` | bug(latent) | low | WON'T-FIX (idempotent contract) |
| T1 | `pip-audit` not installed → dependency-CVE scan can't run | `scripts/audit_deps.py` (env) | SEC | med | QUEUED (install pip-audit + run; verify requirements.txt deps) |
| T2 | `_psalm_map()` cache flagged by `audit_caches` (intentional one-shot static map) | `scripts/core/versification.py:349` | junk | low | SAFE-FIX (add to `.cache_audit_whitelist.py`) |
| T.OK | **Certifications**: vulture (conf-80) **no dead code**; mypy (core+build_edition) **no type errors**; check_routes **CLEAN** (107 routes, anchored, no dups) | tools | — | — | NOTED (healthy) |
| **★BUGCLUSTER-BOOKCODE** | **Systemic non-canonical book-code drift** (`php`→phi, `jas`→jam, `jol`→joe, `ezk`→eze, `nam`→nah, `joh`→jhn, plus `mar`/`1ma`/`2ma`). Cross-refs to ~5 books silently fail to link; Phil/James get wrong detector routing; phantom "missing" books in render_coverage. NEWER files (extract_eastons/wlc) are correct → legacy drift never swept. | `detectors.py:142-169,338-366` · `sources.py:1062,1102-1123` · `link_xrefs.py:129-209` · `run_greek_at_scale.py:52,61` · `run_hebrew_at_scale.py:51,60` · `fetch_sources.py:153-344` · `render_coverage.py:104,113` | bug | **CRITICAL** | QUEUED (coordinated multi-file fix + masking-test fix + blast-radius decision: re-run detectors/fetch to regen missing notes/xrefs?) |
| **★C2.deadchecks** | 4 audit tools (`audit_dead_code/caches/deps/types`) + `coverage`/`validate_taxonomy`/`check_a11y`/`check_manifest`/`render_coverage.run_all` are **DEAD CHECKS** — full `run_all()`+tests but invoked by NOTHING automatic (not pre-commit/preflight/Makefile/CI) | `scripts/audit_*.py` + others | dead/better | high | QUEUED (wire into preflight per the project's own meta-tool pattern — high-value, additive) |
| C1.chap | `book_meta.get("chapters", 50)` always defaults — field is `ch_count` (key never exists) | `run_hebrew_at_scale.py:150, run_greek_at_scale.py:148` | bug(latent) | low | SAFE-FIX (`ch_count`) |
| C1.tmp | Hardcoded `/tmp/...` paths on a win32 environment (status/build/repl) | `scripts/ebible.py:68,238,328` | bug | med | QUEUED (NEEDS-VERIFY: deliberate Linux target? use `tempfile.gettempdir()`) |
| C1.run | `run.py` imports `content.notes.load_notes` (divergent API) + `bash build.sh` ref → may be broken at import | `scripts/run.py:16,35,81` | bug | med | QUEUED (NEEDS-VERIFY import exists) |
| C1.fixname | `fix_xref_targets.py` docstring still names file `fix_vnote_xrefs.py` | `scripts/fix_xref_targets.py:2,35-42` | stale | low | SAFE-FIX (docstring) |
| C1.backfill | `backfill_traditions.py` hardcodes "15,925-note corpus"; `--apply` inert (returns 1) | `scripts/backfill_traditions.py:8,220-236` | stale | low | SAFE-FIX (count) / QUEUED (--apply) |
| C1.dates | `extract_byzantine_nt`/`extract_lxx_swete` bake static `fetched: 2026-05-23` into `_meta.yaml` (others use `date.today()`) | `extract_byzantine_nt.py:113, extract_lxx_swete.py:188` | stale | low | SAFE-FIX (use date.today) |
| C1.toc | `set_reader_toc.py` docstring cites Linux `/home/claude/.toc_state/` (code uses repo-relative) | `scripts/set_reader_toc.py:23,41,186` | stale | low | SAFE-FIX (docstring) |
| C2.refactor | `mutations[0]["new"]` bare no-op statement (dead; would IndexError if empty) | `scripts/refactor.py:500` | dead/bug | med | SAFE-FIX (delete line) |
| C2.phase4 | `VALID_PHASES` (taxonomy) omits `phase4` but schemas `_PHASE_VALUES` includes it — divergence (latent; no content uses phase4 yet) | `validate_taxonomy.py:42 vs validate_schemas.py:161` | bug | med | QUEUED (share one PHASES constant) |
| C2.addnote | `add_note` emits 9th field as STRING; `new_note` emits it as DICT — incompatible attribution shapes | `add_note.py:193 vs new_note.py:295` | dup/bug | med | QUEUED (pick canonical shape) |
| C2.addkind | `add_kind` writes a kind record with NO `category:` → fails `validate_taxonomy` (its own validator) | `scripts/add_kind.py:58-80` | bug | med | QUEUED (add `--category`) |
| C2.devnull | `subprocess.run` missing `stdin=DEVNULL` (Windows hazard) in 4 tools | `verify.py:38, add_kind.py:178, add_note.py:234,242` (+ epubcheck B2b.2) | bug | low-med | SAFE-FIX (add DEVNULL) |
| C2.stalecounts | Stale corpus-count comments/lists: `note_quality` "1,371"; `coverage.py` 81-book PRIORITY_ORDER + non-canonical `content.notes` import; `scaffold_console` "35,000-note target" | `note_quality.py:166, coverage.py:36-133, scaffold_console.py:222` | stale | low | SAFE-FIX (counts) / QUEUED (coverage list) |
| C2.misc | `render_coverage` false "composes into preflight" docstring + contradictory 81/87 counts; `refactor.py` docstring `[3]` vs code `[4]`; `.cache_audit_whitelist` comment wrong path | `render_coverage.py:4,23,41,53; refactor.py:9,14; .cache_audit_whitelist.py:42` | stale | low | SAFE-FIX (docstrings) |
| C2.OK | Whitelists (`.vulture_whitelist`, `.cache_audit_whitelist`) BOTH clean — no stale suppressions | tools | — | — | NOTED |
| ★BOOKCODE-VERIFIED | **Confirmed broken-NOW (not latent):** `content/notes/` + `content/translations/kjv/` use canonical `phi/jam/joe/eze/nah`; base HTML has **0** `v-php/v-jas/v-jol` anchors (208 `v-phi`, 216 `v-jam`, 146 `v-joe`). So NT_BOOKS php/jas DON'T match canonical stems → Phil/James mis-routed; remaps to php/jas/jol/ezk/nam resolve to nothing | (evidence) | bug | **CRITICAL** | QUEUED (confirmed; Phase-2 to check which paths were re-run = lost-notes blast radius) |
| C3a.printcover | `print_cover.py` carries `LOAD-BEARING-NO-LONGER` banner ("don't wire") yet is still dispatched as `ebible print` | `print_cover.py:3-10 vs ebible.py:461` | stale | med | QUEUED (remove `print` passthrough or downgrade banner) |
| C3a.shipretail | `Makefile` `ship-retail` target passes `--retail`, but `ebible ship` has no such flag (pivot removed it) → `make ship-retail` errors | `Makefile:32-33 vs ebible.py:500-502` | bug | med | SAFE-FIX (drop/remap target) |
| C3a.release | `release.py` orphaned (no automated caller) + pre-pivot "save the zip" language; 3 subprocess missing DEVNULL | `scripts/release.py` (whole, :315,63,79,266) | dead/stale | low-med | QUEUED (archive? verify save-flow superseded) |
| C3a.splitweb | `_split_web_html.py` executed-once helper, no banner, past retention | `scripts/_split_web_html.py` | dead | low | SAFE-FIX (archive to dev/archive/) / QUEUED (§7.4 scope) |
| C3a.fonts | `generate_edition_covers.py` hardcodes `C:\Windows\Fonts\*.ttf` (has fallback) | `scripts/generate_edition_covers.py:134-136` | bug | low | QUEUED (portability) |
| C3a.errno | `preview_server.py` EADDRINUSE errno tuple misses Windows 10048 | `scripts/preview_server.py:120` | bug | low | SAFE-FIX (add 10048) |
| C3a.migratenames | THREE unrelated subsystems share "migrate" name (content-schema / corpus_index-SQLite / user-data copy) | `scripts/migrate.py · run_migrations.py · core/migrate.py` | smell | low | QUEUED (README disambiguation) |
| C3a.onixOK | `build_onix.py` DEAD but correctly quarantined (banner + pinned out of CLI by tests + EPUB-excluded); `_dedup_ethiopian_notes` correctly retained emergency tool | `build_onix.py, _dedup_ethiopian_notes.py` | — | — | NOTED (handled per §7.4) |
| C3b.css | `theme-bg-accent` CSS class undefined → exec "Import"/"Save blurbs" buttons render no accent bg | `scripts/templates/exec.py:201,298` (`_design.py` has only `.theme-accent`) | bug | low | SAFE-FIX (use `theme-accent`) |
| C3b.promotediv | `promote_divergence_to_apparatus.py` is a STUB that hard-errors (exit 3) on real data — write path unimplemented (deferred δ.1.x.A) | `scripts/promote_divergence_to_apparatus.py:146-152` | incomplete | med | QUEUED (finish or gate to --check-only; → forward plan) |
| C3b.bannerxss | `_design.STATUS_BANNER` interpolates `message` raw (caller-responsible; latent XSS) | `scripts/templates/_design.py:2302-2324` | SEC | low | QUEUED (escape by default) |
| C3b.atscaledup | `candidate_to_dict` copied VERBATIM across 7 at-scale drivers; `write_queue` in ~6 variants; color consts + path preamble in all 11 | `scripts/run_*_at_scale.py` | dup | med | QUEUED/plan (shared `core/at_scale_base.py`; byte-compat-proof) |
| C3b.docstrings | Stale docstrings: `_design` "13 consoles"→19; `build_manuscript_index` "one-shot"→permanent; `run_ai_xrefs` $28 vs $72; `run_kenyon` dedup-key (id) vs (verse,kind,body) | `_design.py:2; build_manuscript_index.py:5; run_ai_xrefs_at_scale.py:86-90; run_kenyon_at_scale.py:24-25` | stale | low | SAFE-FIX |
| C3b.templatesOK | Templates healthy: §6.2 cross-link PASS (all 18 + documented index exception); NO dead templates (all 19 `*_HTML` served); design-system centralized in `_design.py` | `scripts/templates/*` | — | — | NOTED (healthy) |
| **D.hang** | **`test_scripts.py` HANG root-caused**: `test_ops_route_serves_html_and_api` `srv.shutdown()` deadlocks (2 sequential requests vs single-thread `serve_forever`, no shutdown timeout); 8 sibling live-socket tests share the no-timeout pattern | `tests/test_scripts.py:4247→4277` (+3031,3254,3358,3496,3765,4096,4683) | bug | **HIGH** | QUEUED (ThreadingHTTPServer / join(timeout) / mock like build_all — unblocks full-suite runs) |
| **D.jasmask** | Live probe CONFIRMS ★BUGCLUSTER: `GreekWordDetector.detect('jas')→0.65` but `detect('jam')→EMPTY` → James gets NO Greek notes in prod; test uses `"jas"` and masks it | `tests/test_corpus_chi1.py:266` + `core/detectors.py` | bug | **HIGH** | QUEUED (part of ★BUGCLUSTER fix; test must assert `jam`) |
| D.pins | Brittle exact pins: `len(editions)==11` (×4), `CORPUS_TARGET==35_000` (×2); ingest totals exact-equal | `test_scripts.py:1675,2964,3044; test_v1_console_polish.py:221,344` | stale | med | SAFE-FIX (`>=` floors; keep canonical verse-count exacts) |
| D.srcorder | Brittle pin asserts byte-offset ORDER of 3 substrings in `web.main` source | `tests/test_corpus_index_delta.py:1514-1518` | stale | low | QUEUED (assert behavior not source order) |
| D.skips | Deferred-feature skips may silently pass if shipped (τ.6.x.NT.c mark/luke); a couple stale skips | `test_parallel_bible_tau6xnta_prepass.py:652,663; test_license_xi26.py:521` | stale | low | QUEUED (NEEDS-VERIFY vs CHANGELOG) |
| D.dup | Test monoliths + dup: `test_scripts.py` 14.5K lines/~976 tests; ~30 near-identical `tau7x*` per-book files | `tests/test_scripts.py; tests/test_parallel_bible_tau7x*.py` | dup | med | QUEUED/plan (parametrize; isolate socket tests) |
| D.OK | conftest has a STRONG protected-paths guard (SHA256, CRLF-normalized) catching prod-data mutation; phase-pins route through durable CHANGELOG | `tests/conftest.py` | — | — | NOTED (healthy) |
| **E.license** | `LICENSE` is a TODO placeholder: "All rights reserved", "commercial sale", `TODO_COPYRIGHT_HOLDER` — contradicts CC0 free-public pivot | `LICENSE:17-45` | contradiction | **HIGH** | QUEUED (rewrite to CC0 dedication — needs holder name + CC0 text confirm) |
| **E.copyright** | `COPYRIGHT.md` pervasive commercial + stale: "All rights reserved", "1,371 annotations/14 categories", ">50 words…commercial", ISBN TODO | `COPYRIGHT.md:11,18,28-30,118` | contradiction | **HIGH** | QUEUED (rewrite for CC0; refresh counts) |
| **E.sessionstate** | SESSION_STATE repeatedly calls Douay/Vulgate "UNCOMMITTED" but it IS HEAD `42a59e0` (clean) | `dev/SESSION_STATE.md:9,10,14` | contradiction | high | SAFE-FIX (re-state committed) |
| E.version | `VERSION`: "first commercial release candidate", "51,394 notes", "9 editions", `git push origin`, cites archived PLAN_2026-05-09 | `VERSION:21,28-34` | stale | med | SAFE-FIX (counts/push/PLAN ptr) |
| E.dangling | Dangling refs: `PLAN_2026-05-09.md` cited as in `dev/` (it's archived); `PHASE_C10_PROCESS.md` (no such file); `source_archive/`+`kings_session/` cited as "still exist" | `VERSION:30; scripts/README.md:765-766,59-60,654-659` | dangling | med | SAFE-FIX (repoint/remove) |
| E.readme | `scripts/README.md` pre-pivot identity + stale counts (59 kinds/14 cats/5 editions/1,371 notes; commercial language) | `scripts/README.md:6-12,364-367` | stale | med | SAFE-FIX (refresh + de-commercialize) |
| E.handoff | `HANDOFF_README_v7.md` inner bootstrap list points to archived v28_*/PLAN_2026-05-07; "1,371 notes/5 editions" (redirect banner limits harm) | `HANDOFF_README_v7.md:11,43-44` | stale | med | SAFE-FIX (update list or strengthen banner) |
| E.schemas | `SCHEMAS.md` stale counts ("9 editions", "(66)" kinds) | `dev/SCHEMAS.md:29,30` | stale | low | SAFE-FIX (11/71) |
| E.countdrift | Corpus count drift 67,713 (SESSION_STATE/taxonomy) vs 67,715 (PLAN_2026-05-21) | `SESSION_STATE.md:3 vs PLAN_2026-05-21.md:26` | stale | low | SAFE-FIX (canonical 67,713) |
| E.relnotes | `RELEASE_NOTES_v1.0.0.md` fully pre-pivot (commercial/ISBN/push/old counts) — reads as current | `dev/RELEASE_NOTES_v1.0.0.md` | stale | low | SAFE-FIX (add HISTORICAL banner) |
| E.roadmap | `ROADMAP_FUTURE.md` framed around retail/sales (pivot dropped) | `dev/ROADMAP_FUTURE.md:7,79` | stale | low | SAFE-FIX (note pivot) |
| E.archival | ~50 historical docs clutter `dev/` (28 AUDIT_*, 6 CALIBRATION/PILOT, 4 marathon-scaffold, 15 marathon_reviews, 4 one-shot scans, SPEC_MU draft) — none load-bearing | `dev/*.md` | junk | med | QUEUED (archive to dev/archive/; verify each not phase-pinned first) |
| E.OK | Doc-hygiene conventions real + working (archive banners, lint doc-xref, scope-addenda index); GAPS/maccabees/ATTRIBUTIONS clean | docs | — | — | NOTED |
| **G1** | `file://`/hostless-scheme SSRF→LFI: `_check_allowlist` returns (no raise) when `host==""`; **no scheme check anywhere in http.py** (only `html_sanitize._is_safe_url`, a different surface) | `scripts/core/http.py:89-92` | **SEC** | **HIGH** | QUEUED (**= B2a.12**; add positive scheme allowlist `{http,https}`, raise on all others incl. hostless; verify `http.get/put`+fetch_sources callers) |
| **G2** | preview renders note `body` into HTML **unescaped**, diverging from build sanitizer; reachable via **UNAUTH GET** `/api/preview` (web.py:4371) | `scripts/core/preview.py:128-131` | **SEC** | **HIGH** | QUEUED (**= B2a.7**; wrap `sanitize_html(body)`, match `inject.py:181`; "publisher-trusted" comment is wrong — AI bodies share the store) |
| G3 | `.env` holds a **live-looking** Voyage API key in cleartext (gitignored `.gitignore:107`, NOT in git history; `.env.example` correctly commented) | `.env:1` | SEC | med | QUEUED (rotate key — treat as exposed; move to OS keychain per ξ.14) |
| G4 | `audit_log._summarize_args` redacts by **kwarg-name only** → positional secret args leak verbatim to `audit/*.ndjson` | `scripts/core/audit_log.py:285-294` | SEC | med | QUEUED (**= B2a.9**; redact/truncate positionals or keyword-only secrets; currently unexploited — secret-bearing endpoints pass dict payloads) |
| G5 | STATUS_BANNER interpolates `message` raw into a `<div>` (**= C3b.bannerxss**) | `scripts/templates/_design.py:2324` | SEC | low | QUEUED (default `html.escape` + `raw=True` opt-out; latent — no untrusted caller today) |
| G.refute | **B2a.3 REFUTED** by security owner: html_sandbox pass-2 needs no content-drop guard — pass-1 `sanitize_html` already drops `<script>`/`<style>` content (`TAGS_DROP_CONTENT`); pass-2 re-narrows an already-clean subset | `core/html_sandbox.py:188-192` | — | WON'T-FIX (no bypass) |
| F1 | `.refactor_log.yaml` = **5,172 lines / 470 byte-identical `comm-test→comm-new` entries** (test-harness artifact, grew unbounded); refs non-existent `demo.yaml` files + kinds (`comm-test`/`comm-new`) absent from kinds.yaml | `content/.refactor_log.yaml` | junk | med-high | SAFE-FIX (truncate/delete) + QUEUED (gitignore + cap the writer) |
| F2 | 4 seed-translation `_meta.yaml` `notes:` still say "Gen 1:1-3 seed; user-side full ingest pending" but the full ingest SHIPPED (real verses; `stats.books` 74/74/39/66 already correct) | `douay-rheims/`,`vulgate-clementine/`,`jps/`,`arabic-vandyke/` `_meta.yaml:20` | stale | med | SAFE-FIX (rewrite `notes:` to completed-state) |
| F3 | `lxx-brenton-greek` + `lxx-brenton-english` are seed-only (1 bk / 3 vv) and superseded by full `lxx-swete-greek` (50 bk) | `content/translations/lxx-brenton-*/gen.py` | dead | med | QUEUED (retire the 2 stub stores OR document as intentional demo seeds) |
| F4 | geez-tewahedo `_meta.yaml` `stats.books: 16` but **33** per-book `.py` files exist (later ingests didn't update the header) | `geez-tewahedo/_meta.yaml:56-58` | integrity | med | SAFE-FIX (recompute `stats.{books,verses,books_outside_kjv}` from the store) |
| F5 | geez/amharic-tewahedo-en (AI back-translation, tier4) have **NO store-level `_meta.yaml`** provenance (every other translation dir has one) | `geez-tewahedo-en/`, `amharic-tewahedo-en/` | integrity | med | QUEUED (add `_meta.yaml`: source=back-translation, license, tier, scope) |
| F6 | NT books James/Philippians carry **Hebrew Strong's word-studies** (H430/H136 on "God"/"Lord") — content-side symptom of ★BUGCLUSTER; `[Reviewer:]` placeholder bodies | `content/notes/jam.py:21-38, phi.py:32-59` | bug | med | QUEUED (part of ★BUGCLUSTER corpus-regen; **165 spurious `lang-hebrew` confirmed: phi 76 + jam 89**) |
| F7 | `comm-ai` kind + `enable_ai_notes` per-edition opt-in documented in kinds.yaml but **no edition uses either** (field never appears) (**relates A4**) | `content/kinds.yaml:504 vs editions.yaml` | stale | low | SAFE-FIX (soften kinds.yaml claim) OR QUEUED (wire the field — A4) |
| F8 | catholic-study edition carries fields no other of the 11 has (`authors`/`bisac_codes`/`traditions_per_book`/`popup_languages_per_book`/empty `enabled_reading_plans:`) — schema divergence | `content/editions.yaml:133-177` | better | low | QUEUED (normalize edition schema OR document as the canonical all-fields exemplar) |
| F9 | Hardcoded corpus counts baked into prose comments ("15,925 notes") will rot | `content/traditions.yaml:8; editions.yaml jewish-study:240` | stale | low | SAFE-FIX (refresh) / better (generate, don't embed) |
| F.OK | **content/data HEALTHY**: config graph 0 dangling (kinds↔categories↔canons↔editions↔themes); **book codes canonical throughout content**; epub_working 61 ↔ books.yaml; 8 baked translations complete `_meta` provenance; canon↔books.yaml all resolve; `lao` correctly canon-absent | content | — | — | NOTED (healthy) |

---

## Phase 2.1 Step 4 — crit/high spot-verification log (main session, 2026-05-24)

Personally verified every CRITICAL/HIGH finding against the cited `file:line` (agents can hallucinate). **All confirmed real — no demotions.** New evidence in **bold**.

| Finding | Verdict | Evidence read | Notes |
|---|---|---|---|
| ★BUGCLUSTER-BOOKCODE / BOOKCODE-VERIFIED (CRITICAL) | **CONFIRMED + blast radius quantified** | `detectors.py:152,161` (Hebrew NT_BOOKS) + `:349,358` (Greek NT_BOOKS) both list `php`/`jas`; Hebrew skips `if book in NT_BOOKS` (`:175`), Greek runs `if book in NT_BOOKS` (`:372`) | **Corpus ALREADY corrupted (not latent):** `content/notes/phi.py` = 76 `lang-hebrew` (wrong) + **0** `lang-greek` (missing); `jam.py` = 89 `lang-hebrew` (wrong) + **0** `lang-greek`; control `eph.py` = 0 Hebrew / 280 Greek (correct). **165 spurious Hebrew notes on 2 Greek NT books + all Greek notes missing.** Fix = code + **corpus regen for phi/jam** (strip 165 Hebrew, generate Greek). Confirms QUEUED + the "re-run detectors" blast-radius decision. |
| B1.1 (HIGH) | CONFIRMED | (subset of above) | Same root cause; same fix family. |
| D.jasmask (HIGH) | **CONFIRMED — double-masked** | `test_corpus_chi1.py:266` calls `detect("jas", …)` (non-canonical, IS in NT_BOOKS) AND wraps the assert in `if c_jas:` (`:269`) | With canonical `jam`, `detect` returns `[]` → `c_jas=None` → assert silently skipped, test still green. Test must assert on `jam` and unconditionally. |
| E.license (HIGH) | CONFIRMED | `LICENSE:17` `TODO_COPYRIGHT_HOLDER`, `:19` "All rights reserved", `:21-45` TODO weighing "commercial sale" options, `:7` ONIX | Direct contradiction of CC0 free-public pivot. QUEUED (needs holder name + CC0 text — user decision). |
| E.copyright (HIGH) | CONFIRMED | `COPYRIGHT.md:11` `TODO_COPYRIGHT_HOLDER`/"All rights reserved", `:18` "1,371 annotations / 14 categories", `:20` "63-kind taxonomy", `:28-30` ">50 words…commercial…written permission" | Stale by 50k+ notes (real: 67,713/71 kinds/15 cats) + commercial language vs CC0. QUEUED (rewrite). |
| E.sessionstate (HIGH) | CONFIRMED | `git log` HEAD = `42a59e0` (Douay/Vulgate ship), clean tree; `SESSION_STATE.md:9,10,14` call it "UNCOMMITTED" | SAFE-FIX (re-state committed). |
| D.hang (HIGH) | CONFIRMED (pattern) | `test_scripts.py:4257-4277` single-thread `HTTPServer` + `serve_forever` daemon + `srv.shutdown()` in `finally`, no timeout | Full-suite hang is an already-reproduced standing fact. QUEUED (ThreadingHTTPServer / join-timeout / mock). |
| B2a.7 (HIGH SEC), B2a.12 (HIGH SEC) | Deferred to partition G | — | G owns the security axis; adjudicated on G collection. |

---

## Read-phase partition reports

### A — web.py + scripts/api/* (HTTP surface)
22/22 files read in full (~10,002 lines; web.py 5,214). Findings **A1–A14 + A.N** in the ledger.
Structural: web.py is **still a god-module** but the `api/*` slices are cohesive; circular-import risk is real but managed via the documented lazy-import-back pattern (any future hoist of a back-import to module-top would deadlock). Biggest wart = the **3-way API error-shape split** (A10/A14/A.N) — identical validation failures land on different HTTP statuses by handler era.

### B1 — scripts/core/* (load-bearing)
9/9 files read in full (8,937 lines: versification 1,488 · sources 2,950 · corpus_index 1,484 · detectors 1,533 · matrix 440 · config 471 · notes_io 228 · canonical_verse_counts 191 · popup_versions 152). Findings **B1.1–B1.9 + B1.S/N1/N2** in the ledger.
Structural: **sources.py = god-module, split recommended** (lexicon / commentary / ai_clients / ai_prompts; the 6 commentary clones B1.9 collapse to one generic loader — biggest de-dup win). **matrix.py ψ.35 WON'T-FIX verdict HOLDS** (sound frozen-dataclass `object.__setattr__` idiom; all producers pass only the 2 canonical fields; the only redundancy is belt-and-suspenders accessor methods, not worth churning). versification segment-engine is disciplined (returns None to omit, never misplaces; extent-guarded) — sole risk = load-time asserts vanish under `python -O` (B1.N2). **Standout: B1.1 `php`/`jas` detector-gate bug is a real correctness defect** (NT detector gating wrong for Philippians/James).

### B2a — scripts/core/* security/infra + commercial cluster
24/24 read in full (~3,640 lines). Findings **B2a.\*** in ledger. Security core (auth/totp/safe_path/html_*) broadly sound (totp uses `hmac.compare_digest`; safe_path string-reject+resolve+relative_to). Two HIGH SEC items to confirm in the G pass: **B2a.7** (preview unescaped body) + **B2a.12** (`file://` SSRF). Commercial cluster: `updates.py` DEAD, rest QUARANTINED-but-route-reachable, `press_kit.resolve_cover_path` LIVE.

### B2b — scripts/core/* manuscript engine + remaining infra
25/25 read in full (~6,064 lines). Findings **B2b.\*** in ledger. **Low defect density — no dead modules, no security issues, no junk files.** All 9 manuscript_* modules just-paused (real importers from run_manuscript_*), NOT dead. **manuscript_vision OOM caps INTACT** (MAX_IMAGE_EDGE=1568, no-upscale guard, lru≤8 — the documented crash-class prevention holds). reading_plans + verse_of_day SHIPPED (web routes + build integration). migrate/migrations = complementary live pair. Findings are stale docstrings + epubcheck DEVNULL hygiene.

### C1 — scripts/* build + ingest pipeline
33/33 read in full (~11,400 lines). Findings under **★BUGCLUSTER-BOOKCODE** + **C1.\***. The book-code bug is widespread here (link_xrefs, run_greek/hebrew, fetch_sources TSK/NAVES). **inject.py robustness EXEMPLARY** — the malformed-XHTML insertion-offset history is well-defended (reverse-byte-order insertion, edge guards, spill resolver anchored to chapter headings); `generate_verse_popups` is genuinely idempotent. Structural: real duplication in the `extract_*` writer family + `run_*_at_scale` driver family (a shared `core.at_scale_base`/`core.translation_writer` would remove ~80 dup lines AND would have prevented the NT_BOOKS php/jas copy-paste from propagating). extract_eastons/extract_wlc use CORRECT codes.

### C2 — scripts/* validators/tools/checkers
35/35 read in full (~13,331 lines, + read audit.py/preflight.py/ebible.py/.githooks/Makefile/pyproject for wiring). Findings under **★C2.deadchecks** + **C2.\***. **Wiring reality:** pre-commit runs ONLY lint_rules+ruff; preflight composes lint_rules/validate_schemas/check_content/check_routes/manuscript_qa/epubcheck. The 4 `audit_*` tools + coverage/validate_taxonomy/check_a11y/check_manifest are reachable only via `ebible` passthrough or not at all → **dead checks**. Two divergence pairs (taxonomy↔schemas phases; add_note↔new_note attribution shape). Whitelists clean. Code quality otherwise high (meta-tool contract followed; atomic-write+rollback uniform).

### C2 — scripts/* tools/validators + scripts/templates/* + scripts/migrations/*
SUPERSEDED — this skeleton sub-stub is fully covered by the completed passes above: tools/validators in the **C2** report (35/35), templates in **C3b** (21 templates, healthy), migrations in **C3a** (`migrate*`/`run_migrations`/migrations/* LIVE). No separate read needed.

### C3a — scripts/* commercial/ops/shipping/launchers + migrations
17/17 read in full (~3,180 lines). Findings **C3a.\***. Post-pivot dead-code adjudication: `build_onix`=DEAD-but-correctly-quarantined (banner+test-pinned+EPUB-excluded), `print_cover`=QUARANTINED-but-still-`ebible print`-wired (contradiction), `release.py`=orphaned/likely-dead, `_split_web_html`=executed-once past retention. `desktop_shell`/`launcher`/`preview_server`/`acquire_cudl_master`/`generate_edition_covers`/`migrate*`/`run_migrations`/migrations/* all LIVE. `_dedup_ethiopian_notes` correctly retained (emergency tool). The Ω.0 pivot quarantine is well-enforced by `TestObsoleteModulesCarryBanner`/`TestLiveToolingDecommercialized` — gap = `print_cover` + the `Makefile ship-retail` stale target. No book-code or /tmp issues here.

### C3b — scripts/* at-scale drivers + manuscript-build + templates
36/36 read in full (15 scripts + 21 templates, ~9,800 lines). Findings **C3b.\***. Confirmed run_greek/hebrew NT_BOOKS php/jas (part of ★BUGCLUSTER, broken-now per verification). **Templates HEALTHY**: §6.2 cross-link PASS, no dead templates, design-system centralized; only defect = `theme-bg-accent` typo. `promote_divergence_to_apparatus` is an unfinished stub (errors on real data) → forward-plan item. Big structural debt: the `run_*_at_scale` family duplicates `candidate_to_dict` verbatim ×7 + `write_queue` ×6 (a shared base would have prevented the NT_BOOKS copy-paste propagating — matches the consolidation theme).

### D — tests/* (health, skips, the hang)
148 files / ~86,189 test LOC; read live-socket blocks + dispatch + key tests in full, grepped all 148. Findings **D.\***. **HANG ROOT-CAUSED** (D.hang). **Book-code masking CONFIRMED by live probe** (D.jasmask). NO xfail markers; skips mostly justified (tool/resource gates). conftest protected-paths guard is strong. Pin discipline mostly sound (canonical verse counts legitimately exact); rot risk concentrated in `==11 editions`/`==35_000`. Structural debt: test_scripts.py monolith + ~30 near-identical tau7x* files.

### E — dev/*.md + root docs (staleness/consistency)
~115 docs enumerated; live docs read in full, historical skim-classified. Findings **E.\***. **Highest-value: the 3 root legal/identity docs (LICENSE/COPYRIGHT/VERSION) + SESSION_STATE "uncommitted" — all assert all-rights-reserved/commercial/uncommitted, contradicting CC0 free-public reality at HEAD 42a59e0.** Doc-hygiene conventions work; main debt = **accumulation** (~50 historical reports bury ~6 live docs in dev/). Dangling refs to archived/deleted paths. (Live RULES/MATRIX_MAP/REPO_MAP/PLAN consistency handled by main session in Phase 5.)

### E — dev/*.md bulk (AUDIT/SCOPE/CALIBRATION/PROPOSAL docs) — junk/staleness/superseded
SUPERSEDED — covered by the main **E** pass above: ~115 docs enumerated, live docs read in full, the ~50 historical reports skim-classified into finding **E.archival** (archive to `dev/archive/` after verifying each isn't phase-pinned). No separate read needed.

### F — content/*.yaml + loaders + data integrity + epub_working/ + docs/superpowers/
30 files read in full / ~120 scope (all 6 core config yaml + all 8 baked-translation `_meta.yaml` in full; sampled notes phi/jam/1cl + loaders; sampled translation book files douay/jps/geez-en across non-Genesis books; geez/amharic `_meta` via Grep; `.refactor_log.yaml` via Grep). Findings **F1–F9 + F.OK** in the ledger.
**Config layer is COHERENT** — every kind→category, every edition→canon/theme/kinds resolves; no orphaned/dangling kinds/categories/canons/themes. **Book codes are canonical throughout `content/` — the `php`/`jas` bug has NOT contaminated content data** (the wrong Hebrew notes on phi/jam are filed under *canonical* phi/jam codes; only the note KIND is wrong, not the file code → no coordinate migration needed in the fix). `epub_working/` 61 files match every `files:` ref in books.yaml; **all 8 baked translations carry complete `_meta.yaml` provenance**; `lao` correctly canon-absent. Dominant debt = **doc/metadata lag, not corruption**: seed-era `_meta` `notes:`/`stats` superseded by the full ingests. Two concrete cleanup targets: the 5,172-line `.refactor_log.yaml` test-artifact (junk) + the 2 Brenton LXX stub stores (dead, superseded by full Swete).

### G — security cross-cutting (OWASP lens) [security-axis owner]
18 files scanned. Findings **G1–G5 + G.refute** in the ledger; G's verdicts on the B2a.* SEC items recorded there.
**Security core is sound + unusually deliberate for a first project**: a single enforced egress chokepoint (`core/http.py` + a lint rule banning raw `urlopen`), fail-closed allowlist default, a two-tier HTML sanitizer/sandbox with a documented subset invariant, `hmac.compare_digest` for both admin token and TOTP (constant-time + code-shape pre-validation), a hash-chained append-only audit log, uniform `_check_admin_auth` on every POST/PUT/DELETE (GET stays read-only), subprocess calls all list-args / no `shell=True` / timeouts, and `ast.literal_eval` (never `eval`/`exec`/unsafe-deserialization/`yaml.load`) as the consistent data-trust boundary. **2 genuine HIGH gaps, both surgical divergences from controls that already exist elsewhere** — preview skips the build-path sanitizer (G2/B2a.7); the SSRF guard checks host-membership but forgot scheme (G1/B2a.12). **Adjudications:** B2a.7 CONFIRMED high · B2a.12 CONFIRMED high · B2a.9 CONFIRMED med · **B2a.3 REFUTED→low** (pass-1 `sanitize_html` already drops `<script>`/`<style>` content via `TAGS_DROP_CONTENT`) · B2a.5 partial/low-med (Windows device names bounded to DoS/odd-IO, not traversal — optional hardening) · `_design` STATUS_BANNER (C3b.bannerxss) CONFIRMED low/latent. NEW: **G3** `.env` live-looking Voyage key (med; gitignored, not in history). **T1** (`pip-audit` dependency-CVE scan) still ungated — install + run to close the axis.

### H — dead-code / reachability / junk graph (the master "dead cell" list)
**Automated tool baseline (run 2026-05-23):**
- `audit_dead_code.py` (vulture, conf-80): **✓ no dead code.**
- `audit_types.py` (mypy on core + build_edition): **✓ no type errors.**
- `check_routes.py`: **✓ CLEAN** — 107 routes (GET 71 / POST 16 / PUT 12 / DELETE 8), all unique, all regex routes end-anchored.
- `audit_caches.py`: 1 gap (T2, `_psalm_map` — SAFE-FIX whitelist).
- `audit_deps.py`: pip-audit missing (T1).

**Manual reachability (now COMPLETE, A–G):**
- Genuinely dead *modules*: `core/updates.py` (B2a.C, no prod caller) + the 2 Brenton stub stores `lxx-brenton-{greek,english}` (F3, seed-only, superseded by full Swete).
- Dead *symbols* below vulture conf-80: `web._send_dict_result` (A1), `corpus_index:1374` dead dict-comp (B1.4), `preview.py:117` dead expr (B2a.6), `refactor.py:500` dead stmt (C2.refactor); `web._compute_attribution_audit_uncached` (A2, wire-or-delete).
- Quarantined-not-dead (route-reachable but pivot-dead): sales/distribution/license_*/archive_org + `build_onix`/`print_cover`/`release.py` (C3a) — decision in the forward plan.
- Tracked-but-junk files: `content/.refactor_log.yaml` (F1 — 5,172-line test artifact), `_split_web_html.py` (C3a.splitweb — executed-once past retention).
- **Reconciliation:** vulture conf-80 reports *no* dead code; everything above is either a below-threshold symbol or a module masked from static analysis by dynamic dispatch / data-loading / route tables — exactly the false-negative class the manual graph exists to catch.

---

## Phase 3 — SAFE-FIX applied (verified, uncommitted; 2026-05-24)

**17 findings fixed** — each py_compile + ruff-format clean; `lint_rules` 16/0/0; `audit_caches` clean; **205 targeted tests green** (corpus_chi1 21 + greek_gamma2 29 + refactor 29 + exec_epsilon2 28 + at_scale_wiring 3 + v1_console_polish 82 + manuscript/reading_plan 13). **No content / master-HTML / corpus change** — code + config + docstrings only.

| Finding | Fix | File(s) | Verify |
|---|---|---|---|
| B1.3 | removed duplicate `"soul"` dict key | detectors.py | corpus_chi1 ✓ |
| B1.4 | removed dead dict-comprehension | corpus_index.py | py_compile |
| B2a.6 | removed dead note-label expr | preview.py | py_compile |
| C2.refactor | removed dead `mutations[0]["new"]` stmt | refactor.py | refactor ✓ |
| B2b.2 | `stdin=DEVNULL` ×2 | epubcheck.py | py_compile |
| A3 | `lstrip("GgH")`→`lstrip("Gg")` (stray H) | api/greek.py | greek_gamma2 ✓ |
| A7 | capture `existed` before write (`overwritten` was always-True) | api/scenarios.py | no test pins flag |
| C1.chap | `"chapters"`→`"ch_count"` (was always defaulting 50) | run_hebrew/greek_at_scale.py | at_scale_wiring ✓ |
| C3a.errno | added Windows EADDRINUSE 10048 | preview_server.py | py_compile |
| C3b.css | `theme-bg-accent`→`theme-accent` ×2 (undefined class) | templates/exec.py | exec_epsilon2 ✓ |
| C2.devnull | `stdin=DEVNULL` ×4 | verify/add_kind/add_note.py | py_compile |
| T2 | whitelisted `_psalm_map` cache | .cache_audit_whitelist.py | audit_caches ✓ |
| C3a.shipretail | `ship-retail --retail`→`ship-full --epubcheck` + `.PHONY` | Makefile | ebible flag confirmed |
| B2b.3 | docstring: reading-plan build integration SHIPPED (was "deferred/no-op") | reading_plans.py | reading_plan ✓ |
| B2b.8 | lambda→inline def (removed E731 noqa) | manuscript_index.py | manuscript_index ✓ |
| C1.fixname | docstring filename `fix_vnote_xrefs`→`fix_xref_targets` | fix_xref_targets.py | py_compile |
| C1.toc | docstring path `/home/claude/.toc_state/`→repo-relative | set_reader_toc.py | py_compile |

**⚠ C1.chap blast radius (QUEUED verify):** the `ch_count` bug meant the at-scale Greek/Hebrew generators only ever scanned ≤50 chapters/book, so **Psalms 51-150 (+ Isaiah/Jeremiah >50) may LACK auto `lang-greek`/`lang-hebrew` notes**. Code fixed; a backfill re-run for >50-chapter books is QUEUED (Track D) — needs a content decision + ties to the ★BUGCLUSTER regen.

**Safe-fix TAIL → forward-plan Track D** (deferred for care/no-guessing, NOT effort): web.py cluster **A1/A6/A9/A12** (one focused god-module pass, couples with A11 extraction); **B2a.11** (pair docstring with the G1 SSRF code change); **B2b.9** (`load_image` docstring is actually accurate — finding imprecise); **C3b.docstrings/C2.misc/C2.stalecounts** (dollar/count values need per-item verification); **A4** (feature addition, "better" class); **F4** (geez stats — needs computed counts); **F1** (`.refactor_log.yaml` junk — needs writer-cap coupling); **C3a.splitweb** (archive via git mv). Doc/data-staleness **E.\*** + **F2/F9** + test-pins **D.pins** are handled in Phase 5.

---

## Matrix mint-certification (Phase 4) — CERTIFIED MINT 2026-05-24

Re-proven AFTER the Phase-2 spine ships (Douay/Vulgate baked at `42a59e0`) AND the Phase-3 safe-fix edits:

| Invariant | Result | Tool |
|---|---|---|
| Unresolved matrix refs | **0** (all 11 editions resolve) | `dev/trace_matrix.py` |
| Attribution coverage | **67,713 / 67,713 (100%)** | `scripts/validate_taxonomy.py` |
| matrix == build == config | **12/12 pass** | `tests/test_enabled_kinds_unified.py` |
| Note↔marker pairing | **errors=0 · 24,015 / 24,015 paired** (71 warn / 565 info = baseline residual) | `ebible verify` |
| Build → EPUB (hardest case) | **catholic-study** built (10.90 MB · 50 kinds · 26,428 markers+asides) → **epubcheck 0 errors / 0 warnings** | `build_edition.py` + `epubcheck.py` (Java 8) |

**Signed: matrix MINT as of 2026-05-24 — post-spine + post-audit-safe-fixes.** catholic-study (canon-spliced + freshly-baked Douay/Vulgate popups) was the chosen single-build cert because it exercises the most complex build path AND the build-imported modules touched in Phase 3 (`corpus_index`, `reading_plans`, `epubcheck`); the other 10 editions + the flagship were epubcheck-clean at the spine ship (CHANGELOG 2026-05-23) and **no build-path or content code changed in this audit** (Phase 3 was code/config/docstrings only). `MATRIX_MAP.md` counts confirmed: **67,713** canonical (no drift).

## Rules + maps consistency (Phase 5)
_pending — RULES + 3 maps + PLAN handled by main session; bulk dev/*.md by partition E_

## Coverage reconciliation

Union of partition file-reads vs. the tracked-file inventory (baseline: 994 `.py` = ~387 code + ~607 data; 1,701 `.json`; 140 `.md`; 44 `.yaml`):

| Class | Partition(s) | Coverage |
|---|---|---|
| `scripts/**/*.py` (code) | A (web+api), B (core), C/C3a/C3b (tools+templates), G (security cross-cut) | **100% read in full** |
| `tests/**/*.py` | D | live-socket/dispatch/key tests read in full; all 148 grepped |
| `dev/**/*.md` + root docs (LICENSE/COPYRIGHT/VERSION/README/Makefile…) | E, G (config) | live docs full; ~50 historical skim-classified (E.archival) |
| `content/**/*.yaml` (config) | F | **100% of the 6 core config yaml + all 8 baked `_meta.yaml` in full** |
| `content/**/*.py` data stores (~607) + `content/**/*.json` (1,701) | F (representative sample) + integrity validators | **sampled** across books/translations; **full-corpus integrity proven** by validate_schemas/validate_taxonomy/ebible-verify (all green at baseline) — line-by-line read of machine-generated stores is neither feasible nor the right tool |
| `docs/superpowers/**`, `.githooks/`, `pyproject.toml`, `requirements.txt`, `.env*` | F, G | read |

**Verdict: 100% of tracked code, docs, and config files covered by ≥1 partition.** Generated data stores are covered by sampling + the structural validators (the correct integrity instrument for ast-generated content). No tracked code/doc/config file is unaudited.

---

## Synthesis — severity rollup + headline decisions (Phase 2)

**Disposition split** (~110 findings + ~12 healthy "NOTED"): **SAFE-FIX ≈ 43** (mechanical, applied inline Phase 3) · **QUEUED ≈ 50** (risk/behavior/judgment → user go-no-go, routed to forward-plan Track D) · **WON'T-FIX 5** (B1.N1 matrix layering, B2a.5 device-names, B2a.15 archive_org echo, B2b.7 migrate atomicity, B2a.3/G.refute sandbox) · **NOTED-healthy ≈ 12** (security core, templates, conftest guard, matrix idiom, content/data, vulture/mypy/routes certs).

**The headline decisions (everything CRITICAL/HIGH that is QUEUED — needs your call):**

1. **★BUGCLUSTER-BOOKCODE (CRITICAL).** `php`/`jas` (+`jol`/`ezk`/`nam`/`joh`) drift in `detectors.py`, `run_greek/hebrew_at_scale.py`, `link_xrefs.py`, `render_coverage.py`, `sources.py` (Kenyon map). **Shipped corpus damage, now quantified: Philippians + James carry 165 spurious `lang-hebrew` notes and 0 `lang-greek`.** Fix = (a) canonicalize the codes, (b) fix the masking test (assert on `jam`), (c) **regen the corpus for phi/jam** (strip 165 Hebrew, generate Greek) — this changes note counts, so it's a go/no-go, not a safe-fix.
2. **G2/B2a.7 preview XSS (HIGH SEC)** + **G1/B2a.12 `file://` SSRF (HIGH SEC).** Both are surgical 1-spot fixes (route preview body→`sanitize_html`; add a scheme allowlist), but behavior-changing (preview tests may assert raw HTML; SSRF guard touches the fetch path). Recommend FIX with test-verify.
3. **E.license + E.copyright (HIGH).** `LICENSE`/`COPYRIGHT.md` still say "All rights reserved / commercial / `TODO_COPYRIGHT_HOLDER`", contradicting the CC0 free-public pivot. Blocked on **your copyright-holder name + CC0 confirmation**.
4. **★C2.deadchecks (high).** 4 audit tools (`audit_dead_code/caches/deps/types`) + coverage/validate_taxonomy/check_a11y are built+tested but wired into **nothing automatic**. Recommend wiring into preflight (additive, high-value).

SAFE-FIX items are applied in Phase 3 below; QUEUED items carry into `dev/PLAN_2026-05-23.md` Track D so nothing is orphaned.

---
