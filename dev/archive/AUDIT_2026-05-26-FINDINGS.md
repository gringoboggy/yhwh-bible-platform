# Audit findings — 2026-05-26 (light solo-Claude, post-de-dup full-suite sweep)

**Type:** lighter solo-Claude audit (per the audit-cadence rule — not the heavy parallel-subagent sweep). Run after the B1.8/B1.9 de-dup arc closed, as the user-requested "in-depth audit of the whole project / matrix / map / everything" before a pre-TIER-3 `/clear`.
**HEAD at audit:** `c45ca38` (post-de-dup cleanup) + the 10 stale-pin fixes below (uncommitted at audit time; committed this session).

---

## Verdict: ✅ PASS — healthy; no CRITICAL/HIGH open

The first full-suite run since 2026-05-25 surfaced **10 failures, all stale test-pins / uncatalogued data** from the three intervening ships (Torrey, the `web.py` split, Phase E) that were each gated on *targeted* tests rather than the whole suite. **Zero are logic regressions; zero are from the B1.8/B1.9 de-dup** (the de-dup's full surface is among the 7,358 that passed). All 10 are fixed + verified.

## Fresh gates (run from scratch, 2026-05-26)

| Dimension | Result | Tool |
|---|---|---|
| Full test suite | **10 failed / 7,358 passed** → all 10 fixed → **7,368 green** | `pytest tests/` (serial, 29 min) |
| ruff format / lint_rules / mypy / vulture / pip-audit | **CLEAN** (format ✓ · 16/0/0 · no type errors · no dead code · 0 CVEs) | `scripts/ci.py --no-tests` |
| Matrix integrity (trace_matrix) + repo map (trace_repo) | green (via `lint_rules` `plan_coherence` + `repo_map_complete`, 16/0/0) | `lint_rules.py` |
| Attribution coverage | **91,733 / 91,733 (100.0%)** | `validate_taxonomy.py` |
| Note↔marker pairing | **errors=0** · 32,264 / 32,264 paired (88 warn / 615 info = baseline residual) | `ebible verify` |
| Maps prose currency | no stale refs to the removed `.refactor_log.yaml` or the pre-split `sources.py` framing | grep MATRIX_MAP / REPO_MAP |

Corpus grew 67,713 → **91,733** notes since the 2026-05-23 baseline (Torrey +21,762, Phase E Vulgate appendix +1,117, plus earlier reference works); tests 7,064 → 7,368.

## The 10 full-suite failures — diagnosis + fix (all stale-after-ship)

| # | Test(s) | Root cause (which ship) | Fix |
|---|---|---|---|
| 1-3 | `test_matrix_psi35` B2/B3/B4 marker-present | **web.py split `bae92e4`** moved the matrix functions (carrying the ψ.35-B2/B3/B4 inline markers) from `web.py` → `web_matrix.py` | point the 3 tests at `scripts/web_matrix.py` (markers confirmed present there) |
| 4 | `test_web_filesplit::test_api_covers_get_remains_in_web_py` | **web.py split `bae92e4`** relocated `api_covers` → `web_covers.py` (still re-exported via the hub; route table intact) | assert `__module__ == "scripts.web_covers"`; the intent (NOT in `api/covers`) still holds |
| 5 | `test_vulgate_douay_ingest::test_store_has_expected_book_count[vulgate-clementine]` | **Phase E `cc6523fe`** added the Clementine Latin appendix man/1es/2es → vulgate 74→77 (douay stayed 74); the pin was shared | `EXPECTED_BOOK_COUNT` → per-store `{vulgate: 77, douay: 74}` |
| 6-8 | `test_audit_caches` clean-state / main-rc / json (×3) | **Torrey ingest `13462720`** added `torrey_topical()` `@lru_cache` with no clear-path + not whitelisted → `no_clear_path` finding | add `torrey_topical` to `.cache_audit_whitelist.py` (read-once PD singleton like `tsk`/`strongs_*`) |
| 9-10 | `test_time_travel_psi37` coverage-≥95% + ceiling-keeps-pre-2000 (×2) | **Torrey ingest** — 21,762 Torrey notes uncatalogued in `source_dates.yaml` → coverage 97.3%→73.9%; their year=None made the 2000-ceiling drop them as "contemporary" (9,831 > 5,000 cap) | add `prefix: "Torrey's New Topical Textbook"` year 1897 → coverage→97.6%; Torrey notes now pre-2000, drop count back in range |

**Files touched (all test/data/config — no product code, hence the 7,358 are unaffected):** `tests/test_matrix_psi35.py` · `tests/test_web_filesplit.py` · `tests/test_vulgate_douay_ingest.py` · `scripts/.cache_audit_whitelist.py` · `content/source_dates.yaml`. Verified: the 10 node-ids green + the 5 touched files run in full = 331 green.

**Lesson (already a known pattern — TIER-1 fixed "12 stale pins" for the same reason):** corpus-growth + structural-refactor ships need a full-suite run, not just targeted gates, or location/count/coverage pins drift. The intervening ships each ran targeted gates; this sweep caught the residue. Consider a full-suite run as part of any ingest/split arc-close.

## 2026-05-23 deep-audit ledger — reconciled (~95% resolved)

The `dev/AUDIT_2026-05-23-DEEP.md` ledger is now largely historical (a reconciliation header was added to its top). Its Phase 3 applied 17 SAFE-FIXes inline; the headline CRITICAL/HIGH all closed since (★BUGCLUSTER-BOOKCODE, G1/G2 security, CC0 relicense, dead-checks→ci.py, the god-module splits + de-dups). **No CRITICAL/HIGH remains open.**

## Remaining backlog (all low-severity; none blocking TIER-3)

- **Stale docstrings/counts** needing per-item verification: `C3b.docstrings`, `C2.misc`, `C2.stalecounts`, `F2`/`F9` (`_meta` notes + hardcoded counts), `E.version`/`E.schemas`/`E.dangling`/`E.readme`/`E.handoff`.
- **Bigger refactors** (attended-better): `A.N` (unify the 3 API error-envelope shapes), `C3b.atscaledup` (shared `core/at_scale_base`), `D.dup` (test-monolith parametrization).
- **Quarantined-module cleanup:** `B2a.1/2` (license_key), `C3a.release/printcover/splitweb`, `F3` (Brenton LXX stubs).
- **Latent-SEC notes** (unexploited today): `B2a.9/G4` (positional-secret redaction in audit_log), `G5`/`C3b.bannerxss` (STATUS_BANNER raw interpolation), `B2a.13` (installed-mode path math).
- **TIER-3 provenance:** `F5` (geez/amharic-tewahedo-en `_meta.yaml`).
- **Doc archival:** `E.archival` (~50 historical reports clutter `dev/`).
- **User-action:** `G3` — rotate the `.env` Voyage key (treat as exposed; gitignored, not in history).
- **Fabrication-deferred (re-verified this session, correct to keep deferred):** Phase-E appendix chapters 1es 5/8 + 2es 14 (sub-verse / name-list divergence; can't align verse-perfect without fabricating scripture boundaries).

## C2.addkind (one real but low-urgency bug, not fixed this pass)

`scripts/add_kind.py` writes a kind record with **no `category:`** field → the kind fails `validate_taxonomy`. Real bug, but a moderate CLI-interface change (add `--category` + emit the field + update tests) — deferred from this unattended pass as too risky to land right before a `/clear`; flagged for an attended fix. (Low urgency: the 72 kinds are stable; `add_kind` is rarely run.)
