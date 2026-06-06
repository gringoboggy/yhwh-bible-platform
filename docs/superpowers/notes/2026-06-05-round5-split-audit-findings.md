# Round-5 split deep-audit — MERGED findings + collaborative fix plan (2026-06-05)

**Both lanes complete.** This is the single source of truth for the end-of-project /
pre-beta audit. The `v1.0.0-beta.1` release is **gated on working through this** (user:
"no release until after the full audit runs and we fix what we find"), then the public
flip + release ship together.

## Lane results at a glance

| Lane | Dims | Result | Status |
|---|---|---|---|
| **Mac** (code-review, 12 dims) | correctness · security · code-debt · tests · docs · data-validity · concurrency-caching · cross-module · marathon-boundary · opt-vision/ingest/render | **33 survivors** (2 HIGH · 3 MED · ~15 LOW/INFO · rest) | **✅ FIXED** by Mac (`444fe8cc` 2 HIGH + 3 MED · `9e81ee9e`/`93003e05` LOW/INFO; 8 by-design/store-touching SKIPPED). Raw: `findings-mac.json` on branch `lane-transfer/audit`. |
| **Win** (build/test, 4 dims) | byte-stability · tests-run · rx-surfaces · opt-build | **15 survivors** (1 HIGH · 9 MED · 5 LOW; 2 refuted) | **▶ TO FIX** (this plan). Raw: `_audit-split/findings-win.json`. |

**Net remaining work = the win lane's 15** (Mac's are already fixed). The win HIGH is the
only material correctness risk: a stale-EPUB cache-invalidation miss. One of the 9 MED
(`needs_vnote_pass`) is **already fixed in current source** → Phase 0, verify-only.

## ★ The collaborative fix split (both lanes work in parallel, file-disjoint)

Mirrors the audit split + the machines' strengths (N95 = build/byte-stability heavy on
the SSD; Mac = code-review / lint / test on the HDD-bound box). **No file overlap → both
can run + push concurrently (pull before push).**

| Slice | Owner | Phases / files | Why |
|---|---|---|---|
| **Build-path** | 🪟 **Windows (N95)** | Phase 1 (HIGH `build_cache.py` cache fix) · Phase 4 build items (`apply_badge_markers` + `filter_html` opt, both `build_edition.py`) | Each carries a **byte-stability proof obligation** (regen 9 KJV + `git diff` + `test_byte_stability_gate.py`) — needs the fast SSD. Touches `build_cache.py` + `build_edition.py`. |
| **Test / lint / migration / doc** | 🖥️ **Mac** | Phase 2 (atomic-write: `_reingest_eastons.py`, `_strip_reviewer_scaffold.py`, `lint_rules.py` blind-spot) · Phase 3 (test fixes: `validate_schemas.py`, `test_lint_rules.py` ×2, `test_batch_promote_xrefs.py`) · Phase 4 `corpus_index.py` comment + the `needs_vnote_pass` regression test | No heavy builds; code-review/lint/test work. Touches `lint_rules.py` + test files + the `_reingest_*`/`_strip_*` scripts + `validate_schemas.py` + `corpus_index.py`. Mac authored `test_batch_promote_xrefs.py` (#6 is its own file). |

**Disjoint check:** Windows = `build_cache.py` + `build_edition.py`; Mac = `lint_rules.py` +
`validate_schemas.py` + `corpus_index.py` + the test files + `_reingest_eastons.py` +
`_strip_reviewer_scaffold.py`. Zero overlap. ✅

**Coordination:** each lane fixes its slice, runs its gates, 5-leg saves its commits;
`git pull --ff-only` before every push. When both slices are green → the release gate is
clear → public flip + `v1.0.0-beta.1`.

> **✅ Mac slice DONE (2026-06-06):** Phase 2 atomic-write migrations (`_reingest_eastons.py`
> ×2 + `_strip_reviewer_scaffold.py` → `notes_io.ensure_backup`+`atomic_write`); Phase 3 test
> fixes (`validate_schemas` `reader_toc_books_only` FieldSpec → **test_validate_schemas 49
> passed**; `TestOmega18LintFix` freshness anchored to `_ss−7h` ×6 + `two_back_to_back` strips
> `inflight_freshness` message/violations → **test_lint_rules 12 passed**; `test_batch_promote_xrefs`
> `'''`→`"""` already done); Phase 4 `corpus_index` comment correction + the `needs_vnote_pass`
> regression test (written, `slow`-tagged — verify on the SSD). `lint_rules.py` CLEAN, `ruff
> format` clean, mypy no-new-errors. **⏸ DEFERRED — the `check_atomic_writes` lint EXTENSION**
> (catch `.write_text`/`.write_bytes`): its ~80-site sweep spans `build_edition.py` (win's file) +
> `build_standalone.py`/`core/manuscript_*` (marathon core, off-limits) → NOT cleanly disjoint;
> do it AFTER the win build-path lands, to avoid `build_edition.py` merge conflicts. The two
> genuine canonical writers it would have caught are already migrated above.

---

## Win-lane fix plan (the phased queue — synthesizer output, verified against live source)

> The HIGH touches the build path; everything else is test-fixture fragility +
> atomic-write hardening on one-shot migration scripts (off the build path). No
> marathon-core defects, no crashes, no in-scope security issues.

### Phase 0 — Already landed (verify-only)

- [x] **(MED) `needs_vnote_pass` skipped popup-language pass for per-chapter/per-verse-only editions** — `scripts/build_edition.py:3917-3923`. **VERIFIED FIXED in current source** (guard already carries `or bool(edition.get("popup_languages_per_chapter"))` + `_per_verse` with a mint-11 comment). The JSON findings #2/#10 used a pre-fix snapshot. **Action: none** beyond adding the missing branch test (Phase 4).

### Phase 1 — 🪟 Windows · HIGH: silent stale-cache data-loss (build path)

- [x] **(HIGH) `core/edition_stats.py` absent from `_PIPELINE_SCRIPTS`** — ✅ **DONE (Win slice; byte-identical to HEAD proven).** Fix EXPANDED beyond the 2 named modules: a *fix-the-class* audit of the build-path `scripts.core` **transitive closure (25 modules)** added **10** covered (edition_stats + book_native_names/reading_plans/sources/covers/matrix, **+ config/translations live-bake + corpus_index/sources_lexicon behind the matrix/sources shims** — the last 4 caught by a 7-agent adversarial review), waived 12, and the cache-coverage guard ships as a **transitive-closure self-enforcing test** (`tests/test_build_cache.py::TestCacheCoverageGuard`, NOT `lint_rules.py` — kept off Mac's file for lane-disjointness). `scripts/core/build_cache.py:62-81`. `matter_pages.py` embeds `resolved_note_counts()` output into `copyright.xhtml`/`symbollegend.xhtml`/`your-edition.xhtml` (packed into the EPUB), but editing `edition_stats.py` logic doesn't bust the cache → a **stale EPUB** is served. **Fix:** add `"core/edition_stats.py",` after line 80 (documented comment; same pattern as popup_versions/traditions mint-10, source_dates mint-11 #22). Also add `"core/book_native_names.py",` (dormant, free now). **Then evict:** `build_cache.cache_clear()` / delete `exports/.cache/`. **Byte-stability obligation:** regen 9 KJV + `git diff` (expect zero) + `test_byte_stability_gate.py`. **Guard to add:** a `lint_rules.py` commit-time check that every `scripts/core/*.py` imported by build-path modules appears in `_PIPELINE_SCRIPTS` (or is allow-listed) — cache-coverage drift recurs every new build-path module.

### Phase 2 — 🖥️ Mac · atomic-write hardening (one class, ONE commit; off build path)

- [ ] **(MED) `_reingest_eastons.py` non-atomic canonical rewrites** — `:206, 216`. `from scripts.core import notes_io` → `notes_io.ensure_backup(p); notes_io.atomic_write(p, new_text)`. (Findings #7+#9 = same two sites.)
- [ ] **(LOW) `_strip_reviewer_scaffold.py` non-atomic rewrite** — `:64`. Same fix.
- [ ] **(MED) `check_atomic_writes` lint blind spot — screens only `open(...,'w')`, not `Path.write_text()/write_bytes()`** — `scripts/lint_rules.py:725-751`. **Two-step, same commit:** (1) extend the AST finder to match `.write_text`/`.write_bytes`; (2) sweep all existing sites, annotate legit temp/regenerable writers `# atomic-waived: build-pipeline temp` (~60+ in build_edition/matter_pages/build_standalone/gen_website_progress), migrate the genuine canonical writers in the same commit. **This IS the self-enforcing guard.** ⚠ **Marathon core off-limits** — *waive* `build_standalone.py`/`core/manuscript_*` sites via comment, do NOT edit their logic.

### Phase 3 — 🖥️ Mac · test-fixture fragility (test-only; restore green suite)

- [ ] **(MED) `validate_schemas.py` missing `reader_toc_books_only` FieldSpec → 11 strict errors** — `:214-225`. Insert `FieldSpec("reader_toc_books_only", type=bool, required=False),` after line 215. Additive.
- [ ] **(MED) `TestOmega18LintFix` freshness tests stale (CHANGELOG-relative +8h < 6h threshold)** — `tests/test_lint_rules.py:617-743` (5 tests). Replace `cl_mtime = self._cl.stat().st_mtime + 8*3600` with SESSION_STATE-relative `cl_mtime = self._ss.stat().st_mtime - 7*3600` in each body. Test-only.
- [ ] **(MED) `test_two_back_to_back_runs_equivalent` flaky** — `tests/test_lint_rules.py:504-522`. Extend `strip()` to drop `message` + `violations` for `inflight_freshness` rows (the `age_hours` float varies). Test-only.
- [ ] **(MED) `test_batch_promote_xrefs.py` single-quoted triple string → ruff-format drift** — `:23, 36`. Change both `'''` → `"""`, then `ruff format`. Test-only. (Mac's own file.)

### Phase 4 — diagnostics & doc-accuracy (LOW)

- [x] 🪟 **(LOW) `apply_badge_markers` silent orphan-marker bail** — ✅ **DONE.** `"badges_skipped": 0` init + increment at the orphan bail + `badge_verses_skipped` propagation; kept stats-only (NO `logger.warning` — the module carries no logger). Byte-stable (confirmed by the before/after digest, stats never reach the EPUB); guard = a fast orphan-fixture unit test in `test_marker_style.py`. `build_edition.py:1818, 1904-1912, 4207-4210`.
- [ ] 🖥️ **(LOW) `corpus_index.py` misleading `os.replace` comment** — `:508-516`. Comment-only: the swap is NOT self-healing; `MoveFileEx` fails WinError 5 on any open dest handle; the `_CACHED_CONN.close()` guards are what prevent it. No code change.
- [ ] 🖥️ **(test) `needs_vnote_pass` Phase-0 regression test** — `tests/test_hierarchical_popups_build.py`. Set ONLY `popup_languages_per_verse=["gen:1:1=wlc"]`; assert gen 1:1 pruned to Hebrew, gen 1:2 keeps `DEFAULT_POPUP_WITNESSES`. Locks the already-landed fix.

### Optimization decisions

- ✅ 🪟 **`filter_html` per-kind regex loop** (`build_edition.py:1332-1346`) — **DONE (CHANGE, LOW).** `_build_disabled_kind_res` builds ONE marker alternation + ONE aside alternation over `sorted(disabled_kinds)`, pre-built once per edition in `build_one` and threaded to both call sites as keyword-only kwargs (in-function fallback for other callers). ~2N→2 scans/file. **Proven byte-identical** by the before/after full-build digest (catholic/jewish/ethiopian unchanged) AND a direct per-kind-reference equivalence test over the real corpus (`tests/test_filter_html_consolidation.py`, incl. prefix-collision + empty-set + kwargs-path). The `disabled_html_ref_ids` loop was left untouched.
- **Cold-build I/O** (copytree + compresslevel=9 + parallel `--all`) — **CONFIRMED-OPTIMAL.** `compresslevel 9→6` DECLINED (enlarges EPUBs 1-3%; quality > speed). Deterministic `writestr`+pinned `ZipInfo` is correct. Only the `filter_html` change is worth doing.
- **web.py / build_edition.py size split · paid-API build accel** — out of scope (declined / no budget).

### Constraints carried (every fix)

- **Marathon core OFF-LIMITS** — never edit `build_standalone.py`, `core/manuscript_*`, `core/po_vision_store.py`, `content/manuscript/**`, `content/translations/sources/patrologia/**`, `GAPS/`. Phase-2 sweep *waives* their write sites, never rewrites them.
- **9 KJV byte-stable** — every build-path change (Phase 1, the badge stat, `filter_html`) → regen 9 KJV + `git diff` zero + `test_byte_stability_gate.py` before merge.
- **Additive schema** (`required=False`), **atomic writes** (`notes_io.atomic_write` / `ensure_backup`), **5-leg save per phase**, `PYTHONUTF8=1` + `--basetemp=...yhwh-pytest\bt` on pytest.

---

## Completeness gaps (the win critic flagged — for a future round, NOT this pass)

1. `toc_bilingual` dead-control: `apply_bilingual_toc` wired into `build_one` but no API endpoint / EDITABLE / FieldSpec / tests.
2. `EDITIONS_SPEC` systematic under-coverage: ~15 edition fields written by `api_save_edition_meta` absent from `validate_schemas.EDITIONS_SPEC`.
3. `_reingest_greek_glosses.py` + `_reingest_torrey_topics.py` use raw `Path.write_text()` — same class as Phase 2, not yet swept.
4. `edition_stats._edition_signature` omits `enable_ai_notes` — cache stale if the AI flag is toggled via API.
5. `book_native_names.NATIVE_NAMES` completeness: no guard that all 87 books have a record.
6. Ingest pipeline (`extract_*.py`, `promote.py`, `prospect.py`, `batch_promote_xrefs.py`) not covered by any dimension.
7. Web API surface (`scripts/api/*.py` beyond `editions.py`) — XSS / validation / error-path coverage not audited.
8. **mypy gate is narrow** — `[tool.mypy] files` covered only `scripts/core` + `build_edition.py`; round-5 (Mac) added `scripts/validate_schemas.py` after fixing 2 invisible `type`-shadow errors there, but most of `scripts/*.py` is still type-unchecked. Expand outward as call sites annotate (ω.31.x). (Separately: `ruff check` — SIM/C901 etc. — is intentionally NOT a gate; only `ruff format --check` is. Those are non-enforced style/complexity debt under LANE T code-debt, not bugs.)

## Raw data
- Win: the 15 survivors + the full phased fix plan are **embedded above** (the raw JSON was a transient artifact — re-derive from audit run `wf_eeaa8368-6da` if the per-finding verifier panels are ever needed).
- Mac: `findings-mac.json` on branch `lane-transfer/audit` (delete after both lanes consume it).
