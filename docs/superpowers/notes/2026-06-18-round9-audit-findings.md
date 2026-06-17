# Round-9 audit — WIN lane findings (2026-06-18)

**Status:** IN PROGRESS — WIN dims 6/9 complete; Mac dims pending parallel lane.
**Gate:** Round-8 remediation **COMPLETE** (0 open HIGH/MEDIUM @ turn 119).
**Platform briefs:** `notes/2026-06-18-platform-{kobo,play}.md` (WIN); apple/kindle (Mac).

## Executive summary

WIN replay sweep confirms Round-8 fixes held on byte-stability and opt-build. New material issues are **release-hygiene** (v0.1.0 tag skew on GitHub mirror, duplicate SHA256 manifest) and **doc drift** (RULES §0 index table, EREADERS Kobo summary — both fixed this turn). Play Books remains **unverified** (M5 gate); Kobo path is **shipped** pending user tap round 9.

---

## Survivors (WIN lane)

### Phase 1 — Release / mirror hygiene

- [ ] **HIGH** `v0.1.0` tag points to different commits on GitLab vs GitHub — origin `6d67adaf` ("v0.1.0 RELEASE milestone") vs github `e7e05276` ("turn-63 Mac M3"). `main` tips match (`afb83f8f`). **Fix:** retag GitHub `v0.1.0` to GitLab canonical tip; verify release assets built from GitLab tag.
- [x] **MEDIUM** Stray `SHA256SUMS-merged-overnight.txt` duplicate on v0.1.0 release — **WIN turn 119** (`gh release delete-asset`)

### Phase 2 — Platform gates (research → fix after user phone QA)

- [ ] **HIGH** Play Books — zero device proof; M5 column dark (`catalog.json` `play.live=false`). **Fix:** M5 phone-QA protocol on `everywhere` navy EPUB; date-stamp EREADERS.md; fan M5 only after rounds 1–3 pass.
- [ ] **MEDIUM** No `play` `target_reader` or post-process path — intentional until M5 QA. **Fix:** defer; add sixth profile only if QA demands (see `platform-play.md` Option B).
- [ ] **MEDIUM** gen 35:18 preview-decline anomaly — vnotes-gen-35-18 at 3,509 stripped declined while floor is 4,498; gate 4g WARN only. **Fix:** user re-tap; if reproducible implement vnote split (Option B in `platform-kobo.md`).

### Phase 3 — Doc / tooling sync (fixed this turn)

- [x] **MEDIUM** RULES §0 index table stale on save cadence — **WIN turn 119** (rules-map §4 row aligned to §4 body crash-safe cadence).
- [x] **MEDIUM** EREADERS.md Kobo summary stale (M3 hold, K-R7-4b pending) — **WIN turn 119** (M3 LIVE, K-R9/K-R13 default, tap round 9 pending).
- [x] **LOW** `kobo_tap_calibration.py` bracket outdated (3313/7748) — **WIN turn 119** (4498/5500 per round-5 calibration).

---

## Refuted / held (no action)

| Area | Verdict |
|---|---|
| SHA256SUMS coverage | 186/186 downloadable assets covered |
| main mirror divergence | origin == github @ `afb83f8f` |
| bootstrap-triad hook drift | installed == source (SHA256 match) |
| matrix vs build resolver | intentional scope split (matrix.py:38–44) |
| edition_stats cache keys | fixed (enable_ai_notes + max_phase) |
| opt-build path | CONFIRM-OPTIMAL (ω.20 cache + byte-stability pins) |

---

## WIN dims status

| Dim | Status |
|---|---|
| github-gitlab | ✅ 2 survivors |
| claude-setup | ✅ 1 survivor (fixed) |
| byte-stability | ✅ GREEN (regressions refuted) |
| opt-build | ✅ CONFIRM-OPTIMAL |
| platform-kobo | ✅ brief written |
| platform-play | ✅ brief written |
| tests-run | ⏳ ci.py running |
| rx-surfaces | ⏳ pending |
| popup-integrity | ⏳ pending |

---

## Next

1. WIN: finish `ci.py` + rx-surfaces + popup-integrity dims
2. Mac: 18 replay dims + apple/kindle briefs → push `lane-transfer/audit`
3. WIN: merge Mac JSON → update this doc → fix Phase 1 HIGH/MEDIUM
4. Deploy website when catalog delta lands (188 assets live columns confirmed @ turn 119)