# Performance budgets

> **Phase tag:** ω.13. Companion to `scripts/perf_budgets.py` and
> `tests/test_perf.py`.

This document explains the per-route / per-helper timing budgets
the project enforces in CI. Each budget is a hard pass/fail gate
in the test suite — exceed it and the relevant test fails. Treat
violations as bugs (not "needs more headroom") until you've
ruled out cache invalidation, file-signature drift, and missed
mtime hits.

---

## 1. Why budgets

The project has two perceivable latency surfaces:

1. **Operator-facing API endpoints** (`api_matrix`,
   `api_customize_data`, `api_search_notes`). The editor
   types, clicks, expects a response. Subjective threshold for
   "feels instant" is ~200 ms; for "feels broken" is ~3 s.
2. **Build-pipeline hot paths** (`load_notes`, `_parse_yaml_records`,
   `inject_reading_plans_page`). Each one runs many times per
   build; small regressions multiply.

The budgets here are calibrated against measured baselines on a
developer machine (2026-05-09) plus a multiplier of 1.2-2× for
slower CI machines + future corpus growth headroom.

---

## 2. Current budgets

| Hot path | Budget | Rationale |
|---|---:|---|
| `notes_io.load_notes(book)` | 250 ms | Measured ~115 ms on Genesis (largest book); 2× headroom. |
| `config._parse_yaml_records(editions)` | 50 ms | Measured ~6 ms; ~8× headroom. |
| `config.load_editions` | 50 ms | LRU-cached; rare cold misses. |
| `config.load_kinds` | 50 ms | LRU-cached; rare cold misses. |
| `api_matrix.cold` | 3 s | Full 51K-note × 9-edition × 60-kind walk; capped headroom. |
| `api_matrix.cached` | 50 ms | LRU cache hit; should be near-instant. |
| `api_customize_data` | 500 ms | Composes config loaders + traditions + popup languages. |
| `api_search_notes` | 3 s | Full-corpus walk per query. Same shape as api_matrix.cold. |
| `verse_of_day` | 200 ms | Deterministic walk; SHA-1 hash + per-book filter. |
| `inject_reading_plans_page` | 100 ms | No-op when `enabled_reading_plans` is empty (the common case). |
| `recover.list_backups` | 50 ms | Glob a single directory; caps at 50 entries via `notes_io.ensure_backup`'s `max_keep`. |
| `recover.verify_yaml` | 100 ms | Reads + parses one YAML via `_parse_yaml_records`. |

Every entry above ships an automated test in `tests/test_perf.py`.

---

## 3. Cold vs cached

For paths backed by an `lru_cache` (`api_matrix`, `load_editions`,
`load_kinds`, `load_notes`), the test pair runs:

1. **Cold** — `cache_clear()` first, then measure. Validates that
   the underlying work hasn't slowed down.
2. **Warm** — measure immediately again. Validates that the cache
   is actually hit (a cache invalidation bug would manifest as a
   warm-path budget violation).

The warm-path budget is typically `0.5×` of cold (or specified
explicitly via `BUDGETS[name + '.cached']`).

### 3.1 Test multipliers vs operational budgets (ω.20-A calibration)

The `BUDGETS` table reflects **operational cost** — what a real
caller sees from real code paths. The test invocation can pass a
`multiplier=` to `assert_under_budget` to carry **measurement-
environment tolerance** that doesn't belong in the budget itself.
Two common cases:

- **Warm tests** pass `multiplier=0.5` — budget is the cold cost;
  a warm hit must be ≥ 2× faster. This is the existing convention.
- **Cold corpus-walk tests** pass `multiplier=1.4` (the
  `_PYTEST_HARNESS_MULTIPLIER` constant in `tests/test_perf.py`) —
  pytest collection + per-test setup adds ~0.5-1s of overhead on
  full-corpus walks, pushing the 3s budget over on slower runs
  even though the underlying work is unchanged. Surgical: keeps
  the budget reflecting true work; absorbs harness variance.

Diagnosed 2026-05-09: standalone `compute_matrix.cache_clear() +
compute_matrix()` measured 2.89s (under budget); same call inside
pytest measured 3.4-3.8s (over budget); profile under warm OS
cache showed only 311ms of actual work — the bulk of "cold" cost
is OS-level file I/O on 87 note files. cProfile snapshot showed
`_count_kinds_in_book × 87 = 154ms` and `yaml.safe_load(canons.yaml)
= 102ms` as the dominant non-I/O costs. Conclusion: no regression;
the budget is correct; pytest harness needs an explicit multiplier.

---

## 4. Updating a budget

Bumping a budget is OK when:

- Corpus growth (more notes, more books) legitimately increases
  the work (e.g. doubling the corpus could push `api_matrix.cold`
  past 3 s — budget moves to 5 s).
- A new feature legitimately requires more work (e.g. adding a
  per-edition theme transform inside `api_matrix` adds time).

Bumping a budget is NOT OK when:

- Tests started failing locally — first check `git log -- ...`
  for the culprit commit.
- The cache is silently broken — verify the LRU is being hit by
  measuring back-to-back calls.
- The mtime fingerprint stopped invalidating — touch the file,
  re-run, confirm the cache misses.

When you bump a budget, leave a `# bumped <date>: <reason>`
comment next to the entry in `BUDGETS`. The git blame trail then
serves as a perf-regression log.

---

## 5. CI integration

`tests/test_perf.py` is part of the standard pytest suite — no
separate runner needed. Pass `-k perf` to run just these tests
locally:

    pytest tests/test_perf.py -v

A future ω.13.1 could:

- Add a per-budget `--profile` mode to lint_rules.py (overlaps
  with ω.23).
- Wire perf-budget violations into a Slack / discord webhook
  on CI.

Out of scope for v1: continuous perf graphs over time; today's
contract is "pass / fail on each commit."

---

## 6. Adding a new budget

When you ship a new endpoint or hot path that the user can
perceive:

1. Run `python -c "from scripts.perf_budgets import measure;
   from <module> import <fn>; print(measure(<fn>))"` to baseline.
2. Set the budget at ~2× measured + a round number.
3. Add the entry to `BUDGETS` in `scripts/perf_budgets.py`.
4. Add a test to `tests/test_perf.py` exercising the path with
   `assert_under_budget(name, elapsed)`.
5. Document the entry in §2 above with the rationale.

If the budget needs cold/warm pairs, name them with
`.cold` / `.cached` suffixes (matching the existing
`api_matrix.cold` / `api_matrix.cached` pair).
