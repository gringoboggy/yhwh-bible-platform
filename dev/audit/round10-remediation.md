# Round-10 audit — remediation tracker

**Status (2026-06-23 — WIN REMEDIATION COMPLETE):** Both lanes IN + merged. WIN lane = 8 survivors. MAC lane
= 44 survivors (30 mac-dim NET + 14 win-dim corroboration, deduped against WIN's authoritative compute
run). Combined unique set = WIN's 8 (authoritative on the 6 compute dims) + Mac's 30 mac-dim findings.
**Both HIGHs ✅ FIXED:** W1 (cache red-gate) and the frozen-app `content_root()` silent-data-loss
(`paths._content_root_cached()` now carries the `sys.frozen` guard + ~37 content read/write sites routed
through `paths.*` across 20 files; test_core 46 + test_scripts 994 + 4 frozen-sim pins green; no-op in dev).
**ALL 8 round-11 gap classes CLOSED + all byte-stability leftovers** (char-vs-byte deferred → grand audit,
see below). Structural auditor RAN (Mac: 293/294 books green). **WIN side of "remediate everything to green"
(user directive) is DONE;** remaining = the FINAL joint grand audit (char-vs-byte re-cut · Mac's 2 round-12
HIGH zip-writer-reproducibility · the `1en` misordering · `sources_base` lazy-PATH tail) + Mac's cross-OS verify.

### ✅ Done this session (Phase 0 — lint/test hygiene; all byte-neutral, no engine output change)
- **W1 (HIGH, cache red-gate)** — whitelisted `_estimate_kepub_aside_bytes` (pure fn) in
  `scripts/.cache_audit_whitelist.py` (new "Pure-function value caches" section). `audit_caches` ok=True
  (44 caches: 23 clear-path / 21 whitelisted); `test_audit_caches` 17/17. Commit `377a880a`.
- **ruff F402/F841** — `build_edition.py`: loop var `html`→`fpath` (un-shadow the `html` module);
  `enabled, disabled = …`→`_, disabled = …` at both branches. `ruff check` clean; omega4x 15/15.
- **ALL_CHECKS pin 34→37** — `test_lint_rules.py`; verified the 3 net-new via AST diff vs the 34-pin
  commit (`b2789cdd`): `hook_parity`, `no_background_radar`, `retired_edition_skus` (the Mac plan's
  "superpowers_coherence" guess was wrong — it pre-existed). History comment updated.
- **bare `python`→`sys.executable`** — `test_lint_rules.py:1032` (ruff-format subprocess).
- **`test_note_rehaul` stale dedup pins** (W4 + Mac) — rewrote both `…_defaulting_false` tests to
  **derive the expectation from the registry** (`config.load_editions()` + `.get(field, False)`) and
  assert plumbing-as-bool — robust to rollout pin flips, not hard-coded. All 4 study editions now pin all
  3 flags True; the 2 standalone editions aren't in customize-data. 2/2 green.
- **`test_lane_watch` real-git hazard** — `test_auto_pull_skips_dirty_tree` monkeypatched a no-op
  (`_auto_pull` no longer calls `_working_tree_dirty`; dirty-tree handling moved to `check()`, which
  auto-commits-then-pulls) and then **ran live `git fetch`/`rebase`** in-suite. Replaced with two
  deterministic `_git`-stubbed unit tests (fetch+rebase contract; abort-on-failure). 10/10 green, 0.6s.
- Commits `d9ba911f` (build_edition + lint pins + note_rehaul) + this batch (lane_watch).

### ⚖ Phase-0 decisions (re-verified, conservative)
- **tau6x1 Amharic floor — NO CHANGE (re-verified NO-GO).** The Mac flagged `test_amharic_column_…1318`
  as "yields 0 verses (<2)" but it **passes on WIN/CI** (1 passed, 12.7s — live OCR yields ≥2). The
  prescribed `@pytest.mark.done_gate` MISFITS the marker's semantics ("deliberately-RED *future*-milestone
  pin, red-by-design") — this test is green and asserts *current* behavior. Downgrading it over a macOS
  tesseract-noise quirk would lose real coverage + misuse the marker. Classified Mac-environment fragility,
  not a WIN defect. (A deterministic-OCR-fixture refactor is a future option; extractor/PDF are off-limits.)
- **W3 `editions.yaml` `theme:"modern"` — DEFERRED to Phase 3 (byte-stability).** `theme` selects the
  edition CSS (`edition.get("theme","classic")`), so removing the catholic-study pin could change that
  edition's built CSS → needs a regen + `git diff` proof, not a Phase-0 quick edit. Grouped with the
  theme-CSS cache-key fix (same neighborhood).

### ✅ Done this session (Phase 4 — byte-neutral behavior + W2/W5 byte-stability)
- **api_compare book-code** (gap-1 site 1/3) — `web_content.py` now `config.resolve_book_code` (joh→jhn);
  was returning empty verses. Guard in `test_api_book_code_normalize.py`. Commit `2e2d6ede`.
- **`_version_key` SemVer prerelease** — `updates.py`: keyed `(core, pre_marker)` so `1.0.0 > 1.0.0-rc1`,
  `rc1 < rc2`; tightened `test_desktop_theta`. `2e2d6ede`.
- **W2/W5 Kindle byte-stability** — shared `_ocf_rezip` pins 1980 epoch + 0o644 on every member at both
  `make_kindle_safe` + `apply_kindle_m4b`; determinism guard (byte-identical ×2 + epoch). KJV editions
  don't run the Kindle post-process → byte-stable. Commit `07b5208d`.
- **promote.py** `q`-at-`[v]iew` now quits (was silently skip-mutating the queue). `2b4711fd`.
- **navigator has_notes** (`web_editions.py`) gates through `enabled_kind_codes_for` coord resolver
  (matches the symbols cell; closes the count-vs-build divergence class). **Re-verified no-op on current
  data** (no catholic-study Genesis chapter is xref-only) → defensive correctness-of-construction. `2b4711fd`.

## Round-11 (Mac) — 69 enumerated sites of the 8 completeness classes (FOLDED IN; WIN remediates)

Source: `dev/audit/round11-mac-{survivors.json,plan.md}` (`3742c1b9`). 8 single-findings → **69 sites**
(30 high · 24 med · 12 low · 3 info), 0 FP, 17 critic-found. One canonical fix-pattern per class.

| gap | class | sites | top sev | WIN status |
|---|---|---|---|---|
| 1 | web_*.py user book-param not `resolve_book_code`'d | 3 | med | ✅ **DONE (3/3)** — api_compare + `html_ref_id_from_note_id` resolve before lookup + `_validate_keyed_list_field` now STORES the canonical key (was persisting the alias → silent read-time vanish) |
| 2 | own-vers STRING verse labels hit int `max/range/int()` | 4 | **high** | ✅ **DONE (4/4)** — `api_compare` aligns on `sorted(union, key=verse_sort_key)`; `preview` keys `notes_by_verse` on `str(verse)` (matches own-vers labels, byte-identical canonical); `verse_of_day` picker guards the `int()` coercion (skips Addition-labelled notes vs crashing) |
| 3 | unauth public emitters interpolate corpus → HTML/XML | 6 | med | ✅ **DONE** — `_cdata()` chokepoint over the whole RSS `description` (was per-field/ad-hoc `]]>` handling) + XML-parse/round-trip guards. The other 5 sites (`_render_sample_html`, preview) were enumerated-but-already-escaped (no live bug, per Mac analysis) |
| 4 | shared `_CACHED_CONN` read outside `_CONN_LOCK` (race) | **18** | **high** | ✅ **DONE `75e77595`** — all 10 readers (18 execute sites) → `_read_cursor()`; +2 deterministic race guards; 133 corpus tests green |
| 5 | cache key from UNRESOLVED id vs resolved mtime/payload | 1 | med | ✅ **DONE** — `_book_index_cached` re-keyed on the resolved path (dedups exo/ex → 1 entry/file; key matches the mtime'd file) + reuses `_load_book_cached` |
| 6 | user-editable scripture refs → built output, no resolve | 9 | **high** | ✅ **DONE** — chokepoint: `parse_verse_ref` normalizes alias + `validate_plan_refs`/`ref_ships` + render **canon-filters** out-of-canon/unparseable refs (`build_edition:7750` now passes `canon_books`) + `validate_schemas` validates verse refs at save. **Byte-stable: no edition emits the page (`enabled_reading_plans` empty) + current plans (gen/psa) are universal → zero EPUB change** |
| 7 | migration runner `ok:False` handling + per-migration | 13 | **high** | ✅ **DONE** — tri-state `deferred` outcome in `scripts/migrate.py` (`apply_up` returns it un-recorded; `run_up` collects a `deferred` list, never aborts, exit 0; hard failures still abort) + 0002 returns `deferred` on pending rewrites (was the `ok:False` wedge) + **argv crash-fix** (`backfill_traditions.main(argv)`; 0002 calls `main([])` — was re-parsing the runner's argv → SystemExit) + **frozen-safe ledger** (`_default_state_path()` → `paths.content_root()`; +sys.path insert for standalone CLI; `.gitignore`'d) + **`core/migrate.py` atomicity** (DDL+bookkeeping in one explicit BEGIN/COMMIT via `_iter_sql_statements`, no `executescript` ahead-of-ledger window). TDD: 9 new tests + CLI subprocess guard; 57 migrate + 205 dependent green. **Scope calls:** version-aware-copy *blanket-overwrite* = conservative **NO-GO** (it would clobber user-created editions in user-data `content/` — keep `force=False`; shipped content updates land via NEW numbered migrations or a future 3-way-merge spec, not a re-copy); launcher→ledger routing = LOW follow-up (both first-run paths already idempotent via the marker). |
| 8 | paired producer/consumer with hardcoded edition/key-shape | 15 | **high** | ✅ **DONE** — `build_standalone()` reads `edition['base_translation']`/`['popup_translation']` + resolves the apparatus dir from the body store (was hardcoded `geez-tewahedo`/`-en`/`GEEZ_STORE` → rendered Ge'ez into the Amharic edition); `standalone_store` `_render_book_module`/`build_book_store`/`build_psalms_apparatus` take a `translation` arg (default geez → byte-identical); **`geez_kjv_xref.build_kjv_xref` keys by `str(geez_v)`** so the in-memory hand-off to `collation_to_store_entries` (str-keyed) drops no xrefs (was int-keyed, only survived the apply_kjv_xref JSON round-trip). **Byte-PROVEN: standalone-geez bodies SHA-256 `870ad9e5…486aca` identical pre/post** (165 chapters). TDD: 4 new tests (in-memory no-drop guard, amharic-never-reads-geez, store-param stamp + geez default) + migrated test_geez_kjv_xref int→str keys. **Scope call:** `gen_website_progress` amharic-track (211/352) = conservative **DEFER to LANE P** — re-verified with real data: `_bible_progress` marks `stage="ready"` for any `code in standalone` UNCONDITIONALLY, so feeding the geez `_standalone_books()` set to the amharic track would falsely advertise amharic psa "ready" with no buildable amharic EPUB; the reader renderer is geez-templated throughout (`page: geez`). Proper home = the amharic standalone constitution (LANE P), not a misleading tracker now. |

**Remediation order:** gap-4 → gap-2 → gap-1 → gap-3 → gap-5 → gap-6 → **gap-7 ✅** → **gap-8 ✅** →
**byte-stability leftovers ✅** (W3a stray-theme removal · W3b default-theme cache-key hash · W6 tap-calibration sync ·
W7 Kobo byte-WARN · theme_id mirror) → **frozen-app `content_root()` HIGH ✅** (guard + ~37 routed sites, 20 files;
test_core 46 + test_scripts 994 + 4 frozen-sim green; `sources_base` lazy-PATH tail deferred) **— all 2026-06-23.
ALL WIN REMEDIATION COMPLETE.** **Structural auditor + round-12 new-dim audit + Phase-1 docs = delegated to Mac**
(file-disjoint; see `LANE_HANDOFF.md` top block). **All 8 round-11 gap classes CLOSED.**

> **⛔ char-vs-byte file-split measure = conservative DEFER → grand audit (re-verified NO-GO this pass).** REAL DATA:
> catholic-study builds to **297 pieces, ALL 297 non-ASCII, 20.7M non-ASCII bytes** — so switching the packer from
> codepoints to UTF-8 bytes (`build_edition.py` 4728/4796/4799/4971/4990/5016) shifts boundaries on **every** edition,
> **breaking the 9-KJV-byte-stable invariant** + re-cutting the shipped product structure (epubcheck/K-R2/golden
> re-verify across every edition×platform). LOW severity; the **W7 byte-WARN already catches the symptom**. An
> all-edition re-cut + golden re-baseline is a deliberate, user-aware change → take it on in the FINAL grand audit
> (which rebuilds everything), not a buried leftover commit.

Full fix text + evidence: `round10-win-survivors.json` (slim) · `round10-win-result.json` (raw, +logs/panels)
· `round10-win-plan.md` (synthesized phased plan) · Mac's → `round10-mac-*` (pending).

## WIN lane — 8 survivors (1 high · 1 med · 5 low · 1 info)

| # | sev | dim | file:line | one-line | fix posture |
|---|-----|-----|-----------|----------|-------------|
| W1 | **HIGH** | tests-run | `scripts/build_edition.py:3301` (whitelist: `scripts/.cache_audit_whitelist.py`) | Opt#5 `@lru_cache` on `_estimate_kepub_aside_bytes` not whitelisted → 3 `test_audit_caches` fail | **Add one whitelist line** (pure fn; NOT a cache_clear). Verified safe + byte-neutral. Quickest green. |
| W2 | **MED** | byte-stability | `scripts/core/kindle_post.py:195-201, 657-662` | OCF re-zip stamps wall-clock time → Kindle assets not byte-reproducible | Add `_ZIP_EPOCH=(1980,1,1,0,0,0)`; pinned `ZipInfo` (date_time + `external_attr`) at BOTH loops, mirroring `swap_epub_cover`/`build_epub`. **Same fix as W5.** |
| W3 | low | tests-run | `content/editions.yaml:186` | catholic-study pins `theme:"modern"`; `test_themes` asserts no edition declares a theme SKU | Remove the stray `theme:"modern"` line (atomic-write path). |
| W4 | low | tests-run | `tests/test_note_rehaul.py:240-242` | stale test: uses catholic-study to prove `note_attribution_dedup` default False, but that edition now pins it true | Test-only: assert the CODE default via a synthetic edition. Do NOT touch editions.yaml pins. |
| W5 | low | opt-build | `scripts/core/kindle_post.py:195-201, 657-662` | same kindle re-zip non-reproducibility, 2 sibling sites | **= W2** (one fix closes both). |
| W6 | low | platform-kobo | `dev/kobo_tap_calibration.py:6-17,32,79` | stale DEFAULT_TARGETS + docstring contradict the round-5 narrowed bracket | dev-only doc/targets sync (no engine/byte impact). |
| W7 | low | platform-kobo | `dev/verify_kr2_build.py:500-535,722-726` | no max-piece-size gate; round-9 kepub hit 882 KB piece (> 881 KB broken-Kobo-render threshold per EREADERS) | add a **non-failing WARN** by BYTES (not codepoints) for pieces > ~500 KB. |
| W8 | info | opt-build | `scripts/build_edition.py` | build inject→filter→zip = CONFIRM-OPTIMAL | no change. |

**Suggested remediation order (safest/foundational first):** W1 (unblock the gate) → W3, W4 (stale config/test, additive) → W2/W5 (kindle byte-repro — touches build path → byte-stability proof obligation: regen + `git diff` the affected assets) → W6, W7 (dev-tool hygiene) → W8 (none). Commit-per-fix; full save at the milestone.

## Refuted (3) — correctly dropped, but READ ONE

- **[high] K-R4-2 popup size-clamp never extended to the vnote translation class — "the exact surface the user reported."** Refuted **only because it re-raises a known-deferred in-flight item** (DEFERRED_BY_DESIGN list; `_split_popup_units` has one study-path call site). ⚠ **This is the user's REAL Kobo bug** — it is NOT closed; it lives on WIN's existing **M2 / K-R4-2 floor-on-tablet** backlog (`LANE_HANDOFF.md` §user-fail M2 + the "does the 4,498 floor gate the tablet target" question). Remediation of the round-10 set does not subsume it; keep it on the M2 track.
- [low] no `.vn-sep` separator-coverage gate; [medium] gate 4g/4n WARN-only on the device-proven vnote decline class — both refuted; related to the same K-R4-2 vnote surface.

## Structural auditor — AUTHORED, UNRUN (do first next session)

`dev/audit_book_structure.py` (deterministic verse→chapter→book→out-of-book). A round-10 completeness
critic READ it and flagged: **its badge regex matches only ONE of two emitters** → fix the regex, then
RUN it on a real built `catholic-study` epub + kepub and confirm it actually exercises badge/aside paths.
(mypy/ruff/compile clean; never executed against an artifact.)

## MAC lane — DONE + MERGED (44 survivors; ran full 24-dim `all`, args didn't propagate but findings valid)

Full detail: `dev/audit/round10-mac-survivors.json` + `round10-mac-plan.md` (30 KB phased plan + 8
completeness gaps). 64 deduped → 44 survived (1 high · 12 med · 23 low · 8 info), 20 refuted, **0
UNVERIFIED**. **30 mac-dim survivors = the NET deliverable** (1 high · 5 med · 17 low · 7 info); the 14
win-dim survivors corroborate WIN's authoritative 6-dim run (dedup, don't double-fix).

**Mac-lane remediation order** (per `round10-mac-plan.md` phases; WIN executes):
- **Phase 0 — lint/test hygiene** (no engine, no output change): ruff F402/F841 `build_edition.py:7094,7123-7125` · audit_caches whitelist (= W1, ✅ done) · stale `test_note_rehaul` pins (= W4) · registry-size pin `test_lint_rules.py:43` (34→37) · bare-`python` `test_lint_rules.py:1032` · `test_lane_watch.py:107-111` (⚠ leaves `_git` UNMOCKED → real `git fetch` in-suite) · `test_parallel_bible_tau6x1.py:1344` OCR floor.
- **Phase 1 — doc accuracy** (prose only): roadmap.html Geʽez over-claim (Mac owns rebuild+redeploy) · MATRIX_MAP 68→72 + dead pointer · m4b spec banner · platform-play 100 MB ceiling · REPO_MAP counts.
- **Phase 2 — additive guards:** Kobo oversized-piece byte gate (= W7) · whole-corpus `check_notes_extent` lint.
- **Phase 3 — byte-stability** (proof obligation): theme-CSS unhashed cache key · kindle re-zip wall-clock (= W2/W5) · char-vs-byte split measure · `build_epub.should_skip` dotfile exclusion.
- **Phase 4 — behavior** (scoped, byte-neutral): SSRF redirect re-check · version-compare prerelease · `api_compare` book-code normalize · matrix count-grid override gating · `promote.py` `q`-at-view.
- **Phase 5 — the HIGH** (most invasive, last): frozen-app `content_root()` → route content read/write sites through `paths.content_root()` + frozen guard.
- **Phase 6 — code-debt** (optional): comm-* detector base class · dead `_EMPTY_VERSE_REFS_RE`.

> **Mac round-11 (queued, findings-only, parallel):** completeness-gap class sweep on the 8 gaps →
> `round11-mac-*` (so WIN fixes each recurring class completely, not the first site). See `LANE_HANDOFF.md`.

## Completeness gaps (next-round seeds)

1. Run + fix `audit_book_structure.py` (badge regex = 1 of 2 emitters).
2. Byte-reproducibility of EVERY `zipfile.ZipFile(..,"w")` writer in `scripts/` (not just build_epub + kindle_post) — the date_time/external_attr pin is enforced by exactly one determinism test.
3. `audit_caches.py` is blind to `@functools.cache`/`@cache`/`@cached_property` (only matches `@lru_cache`) → extend `_is_lru_cache_decorator`.
4. Platform dim covered Kobo only — Apple (tablet) + Play profiles not exercised.
5. popup-integrity returned 0/3 survivors — may have re-derived de-scoped K-R4/14/15 arcs instead of hunting NEW emitter/hidden-target classes.
