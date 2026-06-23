# Round-10 audit — remediation tracker

**Status (2026-06-22 wrap):** WIN lane DONE (8 survivors). MAC lane STILL RUNNING (~45/96 find · 12/62
verify at wrap). Structural auditor AUTHORED but UNRUN. **Next session: run structural auditor → merge
Mac's findings → remediate everything to green** (user directive: "until the full audit is in and
everything it surfaces is fixed" — this overrides the engine's findings-only default).

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

## MAC lane — PENDING (still running at wrap)

18 read-only dims, Opus, on the iMac. At wrap: ~45/96 find · 12/62 verify. Will write
`dev/audit/round10-mac-survivors.json` + `-plan.md` and post `✅ MAC AUDIT round-10 DONE` in
`LANE_HANDOFF.md`. **Next session: `git fetch`, merge Mac's survivors into this tracker, remediate.**

## Completeness gaps (next-round seeds)

1. Run + fix `audit_book_structure.py` (badge regex = 1 of 2 emitters).
2. Byte-reproducibility of EVERY `zipfile.ZipFile(..,"w")` writer in `scripts/` (not just build_epub + kindle_post) — the date_time/external_attr pin is enforced by exactly one determinism test.
3. `audit_caches.py` is blind to `@functools.cache`/`@cache`/`@cached_property` (only matches `@lru_cache`) → extend `_is_lru_cache_decorator`.
4. Platform dim covered Kobo only — Apple (tablet) + Play profiles not exercised.
5. popup-integrity returned 0/3 survivors — may have re-derived de-scoped K-R4/14/15 arcs instead of hunting NEW emitter/hidden-target classes.
