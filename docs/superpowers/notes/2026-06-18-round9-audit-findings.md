# Round-9 audit — merged findings (2026-06-18)

**Status:** Mac audit COMPLETE + fixes shipped @ turn 119; WIN dims 8/9 complete @ turn 119.
**Gate:** Round-8 remediation **COMPLETE** (0 open HIGH/MEDIUM).
**Platform briefs:** `notes/2026-06-18-platform-{apple,kindle,kobo,play}.md`
**Implementation matrix:** `notes/2026-06-18-platform-implementation-matrix.md` (filled @ WIN turn 122)

## Executive summary

**Mac (22 dims):** 8 survivors (0 critical · 0 high · 2 medium · 3 low · 3 info). All actionable Mac defects **fixed @ turn 119**.

**WIN (9 dims):** Release-hygiene + popup integrity + platform gates. Play Books unverified (M5); Kobo shipped pending user tap round 9.

---

## Mac lane — fixes shipped (turn 119)

- [x] **MEDIUM** Book-code alias gap — `api_build_my_bible`, `api_build_tracker_book`, `api_sample_html` → `config.resolve_book_code` · tests in `test_book_codes.py`
- [x] **MEDIUM** `sources_base` vulture dead-import — `_BOOK_CODE_ALIASES` assignment re-export (lint + vulture green)
- [x] **LOW** `web_sources` index/summary → `load_notes_checked`; summary exposes `parse_errors`
- [x] **LOW** Test gap for build-my-bible / build-tracker legacy aliases
- [x] **LOW** Archive closed-arc `scripts/_*.py` one-shots — **Mac turn 121** → `dev/archive/`

**INFO:** Apple M2 CONFIRM-OPTIMAL · Kindle M4b design gap documented · build orchestration CONFIRM-OPTIMAL

---

## WIN lane — survivors

### Phase 1 — Release / mirror hygiene

- [x] **HIGH** `v0.1.0` tag skew GitLab vs GitHub — **WIN turn 119c** (`git push github 6d67adaf:refs/tags/v0.1.0 --force`; both remotes now `6d67adaf`)
- [x] **MEDIUM** Stray `SHA256SUMS-merged-overnight.txt` duplicate on v0.1.0 release — **WIN turn 119**

### Phase 2 — Popup integrity (code-only sweep @ turn 119)

- [x] **MEDIUM** Standalone build bypasses K-R4-1 vnote separator pass — **WIN turn 119** (`add_vnote_preview_separators` on `geez_*.xhtml` + `test_standalone_vnotes_carry_kr4_separators`)
- [ ] **MEDIUM** gen 35:18 vnote preview-decline inversion — 3,509 stripped declined vs 4,498 floor; gate 4g WARN-only. **Fix:** user re-tap on latest kepub.
- [ ] **LOW** `generate_verse_popups.py` emits vnotes without `.vn-sep` at source — policy only in `build_edition` post-pass.
- [ ] **LOW** `vnote-1ki-12-24` at 7,747 stripped chars (bracket edge) — device probe pending.

### Phase 3 — Platform gates (research → fix after user phone QA)

- [ ] **HIGH** Play Books — zero device proof; M5 column dark. **Fix:** M5 phone-QA protocol.
- [ ] **MEDIUM** No `play` `target_reader` path — defer until M5 QA (see `platform-play.md`).
- [ ] **MEDIUM** gen 35:18 preview-decline anomaly — user re-tap; see `platform-kobo.md`.

### Phase 4 — Doc / tooling (fixed)

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
| platform-kobo | ✅ brief written |
| platform-play | ✅ brief written |
| popup-integrity | ✅ code-only sweep (1 medium fixed, 1 medium + 2 low open) |
| tests-run | ⏳ `ci.py` in flight (~6h; coverage pytest pass) |
| rx-surfaces | ⏳ deferred until `ci.py` finishes (RAM on 16GB N95) |

---

## Next

1. WIN: finish ci.py + rx-surfaces; push rebased standalone fix
2. Fix WIN Phase 1 HIGH (v0.1.0 tag skew) + M5 Play QA when ready
3. Website deployed @ `efb7386` (188 assets; kobo live)