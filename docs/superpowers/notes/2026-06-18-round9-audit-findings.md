# Round-9 audit — merged findings (2026-06-18)

**Status:** Mac audit COMPLETE + fixes shipped @ turn 119; WIN dims 6/9 complete @ turn 119.
**Gate:** Round-8 remediation **COMPLETE** (0 open HIGH/MEDIUM).
**Platform briefs:** `notes/2026-06-18-platform-{apple,kindle,kobo,play}.md`

## Executive summary

**Mac (22 dims):** 8 survivors (0 critical · 0 high · 2 medium · 3 low · 3 info). All actionable Mac defects **fixed @ turn 119**.

**WIN (9 dims in progress):** Release-hygiene + platform gates. Play Books unverified (M5); Kobo shipped pending user tap round 9.

---

## Mac lane — fixes shipped (turn 119)

- [x] **MEDIUM** Book-code alias gap — `api_build_my_bible`, `api_build_tracker_book`, `api_sample_html` → `config.resolve_book_code` · tests in `test_book_codes.py`
- [x] **MEDIUM** `sources_base` vulture dead-import — `_BOOK_CODE_ALIASES` assignment re-export (lint + vulture green)
- [x] **LOW** `web_sources` index/summary → `load_notes_checked`; summary exposes `parse_errors`
- [x] **LOW** Test gap for build-my-bible / build-tracker legacy aliases
- [ ] **LOW** Archive closed-arc `scripts/_*.py` one-shots — deferred (hygiene)

**INFO:** Apple M2 CONFIRM-OPTIMAL · Kindle M4b design gap documented · build orchestration CONFIRM-OPTIMAL

---

## WIN lane — survivors

### Phase 1 — Release / mirror hygiene

- [ ] **HIGH** `v0.1.0` tag points to different commits on GitLab vs GitHub — origin `6d67adaf` vs github `e7e05276`. **Fix:** retag GitHub `v0.1.0` to GitLab canonical tip.
- [x] **MEDIUM** Stray `SHA256SUMS-merged-overnight.txt` duplicate on v0.1.0 release — **WIN turn 119**

### Phase 2 — Platform gates

- [ ] **HIGH** Play Books — zero device proof; M5 column dark. **Fix:** M5 phone-QA protocol.
- [ ] **MEDIUM** No `play` `target_reader` path — defer until M5 QA (see `platform-play.md`).
- [ ] **MEDIUM** gen 35:18 preview-decline anomaly — user re-tap; see `platform-kobo.md`.

### Phase 3 — Doc / tooling (fixed)

- [x] **MEDIUM** RULES §0 index table stale — **WIN turn 119**
- [x] **MEDIUM** EREADERS.md Kobo summary stale — **WIN turn 119**
- [x] **LOW** `kobo_tap_calibration.py` bracket outdated — **WIN turn 119**

---

## WIN dims status

| Dim | Status |
|---|---|
| github-gitlab | ✅ |
| claude-setup | ✅ |
| byte-stability | ✅ GREEN |
| opt-build | ✅ CONFIRM-OPTIMAL |
| platform-kobo | ✅ brief |
| platform-play | ✅ brief |
| tests-run | ⏳ ci.py |
| rx-surfaces | ⏳ pending |
| popup-integrity | ⏳ pending |

---

## Next

1. WIN: finish ci.py + rx-surfaces + popup-integrity; merge Mac JSON
2. Fix WIN Phase 1 HIGH (v0.1.0 tag skew) + M5 Play QA when ready
3. Website deployed @ `efb7386` (188 assets; kobo live)