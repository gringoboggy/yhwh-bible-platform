# Project audit — 2026-05-15 LIGHT-6 (solo-Claude, post-τ.7.x.i, post-Geʽez-catchup + skip-the-gap)

**Trigger:** user "audit and save" after the τ.7.x.i ship close-out —
explicit cadence-window close request per `feedback_audit_cadence`.
This is the LARGEST cadence window since the audit cadence was
established: **11 phases** shipped since the LIGHT-5 baseline
(5069 tests, post-τ.7.x.f):

```
τ.7.x.g    Amharic Judges        +60 pins
τ.7.x.h    Amharic Ruth          +60 pins  (+ structural discovery)
τ.6.x.2.a  Geʽez Genesis  ┐
τ.6.x.2.b  Geʽez Exodus   │
τ.6.x.2.c  Geʽez Leviticus│
τ.6.x.2.d  Geʽez Numbers  │ BATCH  +84 pins (test_parallel_bible_
τ.6.x.2.e  Geʽez Deut     │        tau6x2_geez_arc.py) + 16
τ.6.x.2.f  Geʽez Joshua   │        tau7x{a..h}.py Geʽez-pin
τ.6.x.2.g  Geʽez Judges   │        migrations (net 0)
τ.6.x.2.h  Geʽez Ruth     ┘
τ.7.x.i    Amharic Psalms        +65 pins  (+ skip-the-gap + 11
                                  belated seed-pin migrations)
```

**Form:** LIGHT solo-Claude per default. Crosses the ≥150 cumulative-
drift hard-threshold (~+269 net new pins) AND includes THREE
significant structural events: (1) the **τ.7.x.h structural
discovery** that the source PDF alternates between EOTC-parallel and
dzamaragna-only publication formats; (2) the **τ.6.x.2.a-h parallel-
column-catchup arc-close** bringing both columns to parity for the
pages-0-437 scan range; (3) the **τ.7.x.i skip-the-gap ship + Wisdom-
and-Poetry arc-open**.

---

## 0. TL;DR

**Project state at audit-time is CLEAN — but ONLY after the audit
caught and the operator fixed an incomplete migration.** The full-
sweep audit step did exactly what the cadence is designed to do:
surface latent breakage that the per-ship targeted-test runs missed.

### THE finding: τ.6.x.2.a-h batch left 11 seed-pins un-migrated

The τ.6.x.2.a Geʽez Genesis sub-ship upgraded `geez-tewahedo/gen.py`
from the Π.0 3-verse curated seed to a 1022-verse ocr-tier3 ingest,
and the τ.6.x.2.a-h batch added 7 more Geʽez books. At batch-ship
time the operator migrated the **8 tau7x{a..h}.py** Geʽez-preservation
pins (the ones the per-ship targeted tests exercised) but MISSED
**11 other seed-pinned tests** across 8 files that the targeted runs
never touched:

| File | Test | Pin form | Fix |
|---|---|---|---|
| tau6x0.py | test_geez_tewahedo_remains_at_seed_state | `files == ["gen.py"]` | → `"gen.py" in files` |
| tau6x0b.py | test_geez_tewahedo_still_gen_only | `files == ["gen.py"]` | → superset |
| tau6x0c.py | test_geez_tewahedo_still_gen_only | `files == ["gen.py"]` | → superset |
| tau6x1.py | test_geez_tewahedo_still_gen_only | `files == ["gen.py"]` | → superset |
| tau6x2d.py | test_geez_tewahedo_only_seed_gen_py | `py_files == ["gen.py"]` | → superset |
| delta1.py | test_geez_tewahedo_still_gen_only | `files == ["gen.py"]` | → superset |
| phi1.py | test_geez_tewahedo_still_gen_only | `files == ["gen.py"]` | → superset |
| pi0.py | test_geez_tewahedo_seed_still_intact | `len==3 + "ቀዳሚሁ" in v` | → `≥950 + "ዳሚ" in v` |
| translations_tau6.py | TestTau6Seed::test_three_verses | `count == 3` | → `≥950` |
| translations_tau6.py | TestTau6Seed::test_gen_1_1_starts_with_qedami | `"ቀዳሚሁ" in v` | → `"ዳሚ" in v` |
| translations_tau6.py | TestTau6Seed::test_gen_1_1_contains_egziabher | `"እግዚአብሔር" in v` | → `"ግዚአብሔር" in v` |

All 11 migrated using the **same share-pin→milestone-pin pattern**
already applied to the companion `test_amharic_tewahedo_contains_
gen_py` tests at τ.7.x.b ship-time (`feedback_share_pin_pattern`).
The migration is principled, not a test-weakening hack: the τ.6.x.2.a
ocr-tier3 ingest is a *legitimate* state change (the Π.0 seed was
always documented as a placeholder to be upgraded at τ.6.x.2.a under
D4-c); the pins correctly needed to flip from "Geʽez stays at seed"
to "Geʽez is at ocr-tier3 ingest scale + carries the OCR-survivable
content stem". The OCR garbles `ቀዳሚሁ`→`በሩዳሚ` and `እግዚአብሔር`→
`አግዚአብሔር`; migrated pins assert the discriminative sub-stems (`ዳሚ`,
`ግዚአብሔር`) that survive the garble, consistent with the τ.6.x.0b
honesty contract.

### Process finding (flagged, not yet codified)

**F-LIGHT6-1 — batch-ship migration-completeness gap.** When a batch
ship flips a long-standing invariant (here: "Geʽez stays at Π.0
seed"), the per-ship targeted-test selection is structurally
incapable of catching pins in *unrelated* phase-test files that
happen to assert the same invariant as a closed-arc regression
guard. The τ.6.x.2.a-h batch's targeted verification (526 tests
across tau7x*/tau6x2) was green, but 11 pins in tau6x0/0b/0c/1/2d/
delta1/phi1/pi0/translations_tau6 only surfaced under the full
sweep. **Recommendation for τ.6.x.3 or a future hygiene ship:** when
a ship flips a documented invariant, grep the ENTIRE tests/ tree for
the invariant's assertion signature (`files == ["gen.py"]`,
`book_verse_count(... ) == 3`, content-marker pins) BEFORE running
the targeted suite — a pre-flight "invariant-flip blast-radius scan".
This would have caught all 11 at τ.6.x.2.a-h ship-time. Not
codifying as a rule yet (single occurrence); flagging for the
operator to decide whether it rises to a §12-retrospective trigger.

### Foreground (every check passes post-fix)

- ✓ Linter (`scripts/lint_rules.py`): **11/11 pass · 0 warn · 0 fail**.
- ✓ YAML integrity: `_source.yaml` + `amharic-tewahedo/_meta.yaml`
  + `geez-tewahedo/_meta.yaml` all parse; **9 amharic ingest
  records** (gen→psa) + **8 geez ingest records** (gen→rut); stats
  coherent (amharic 9 books / 8242 verses; geez 8 books / 4337
  verses).
- ✓ `structural_map` now has **9 canonical sections** (Pentateuch
  + Joshua + Judges + Ruth + Psalms) + meqabyan + jubilees +
  one_enoch + laodiceans + tewahedo_distinctive_inventory.
- ✓ ruff format: **488 files clean** (auto-fixed at audit:
  extract_parallel_pdf.py + test_omega4x_hygiene.py + the 8
  migrated seed-pin files).
- ✓ IN_FLIGHT: **idle** (`TRACKER-STATE: idle`); prior-task cascade
  τ.7.x.i → τ.6.x.2.a-h → τ.7.x.h → τ.7.x.g → … preserved.
- ✓ State-doc coherence: all 11 shipped phases referenced
  consistently across SESSION_STATE + IN_FLIGHT + CHANGELOG +
  PLAN §6.
- ✓ Closed-arc invariants: **26 named invariants** preserved in
  `tau7xi_ingest.closed_arc_contracts_preserved` (8 prior τ.7.x.*
  + 8 τ.6.x.2.a-h Geʽez + 10 base contracts).
- ✓ Targeted post-fix verification: bg1fhzq1k = **416 passed / 0
  failed** across the 8 migrated seed-pin files; pi0 + test_perf.py
  = **13 passed**.
- ✓ **Definitive post-fix full sweep (bgup89xsd): 5298 passed, 1
  skipped, 0 failed in 735s (12m14s).** All 12 prior failures
  resolved; the perf flake did NOT recur (confirming it was load-
  induced, not a regression). Net cadence drift since LIGHT-5
  (5069): **+229 passing tests** across the 11-phase window.

### Background findings (no follow-up required)

- **Back-link annotation pattern at 13 instances** with a NOVEL
  variant: `tau7xh_ingest.also_reused_at_phase: τ.7.x.i` — the FIRST
  second-key back-link form (τ.7.x.h is reused by BOTH τ.6.x.2.h
  Geʽez catchup AND τ.7.x.i skip-the-gap Psalms; it is now the
  highest-reuse pipeline in the τ.7.x.* family).
- **17-ship zero-parser-API-delta** across both columns (8 Amharic
  τ.7.x.a-h + 8 Geʽez τ.6.x.2.a-h + Amharic τ.7.x.i). The τ.7.x.a
  template is decisively established as a stable per-book scaffold
  that scales from Ruth (4 ch / 85 v / 6 pages) to Psalms (151 ch /
  2531 v / 104 pages).
- **Skip-the-gap pattern established** as a legitimate project move
  with full state-tracking (10 deferred books marked `SKIPPED-via-
  τ.7.x.i` in translation_slot_state; τ.7.x.J-cluster reserved).
- **§8.1 instance count now at 10** (9 prior + τ.6.x.2.e Geʽez
  Pentateuch arc-close).

### NEW residual classes flagged for τ.6.x.3 audit

- **publication_format_shift_residual** (discovered τ.7.x.h):
  the source PDF alternates between EOTC-parallel and dzamaragna.net
  2002 Amharic-only formats. The 438-802 gap (1 Sam→Job, 10 books)
  is dzamaragna-only and DEFERRED to a τ.7.x.J-cluster sub-arc.
  Future ships must anticipate format alternation; boundary
  detection cannot assume contiguity.
- **psalm_151_renumbered_to_ch126** (discovered τ.7.x.i): the
  Tewahedo-distinctive Psalm 151 (David-vs-Goliath) is preserved
  but renumbered into the ch 126 partial slot by the recovery-
  deficit chapter-exhaustion artifact. τ.6.x.3 re-aligns via
  content-signature matching (the Goliath markers are distinctive).
- **carried forward from LIGHT-5:** publisher_bridge_narrative_
  residual + null_formal_title_banner_pattern (the latter now
  CONFIRMED 3× across Joshua + Judges + Ruth — promoted from
  "candidate quirk" to "stable structural property of the EOTC-
  parallel scan").

---

## 1. Test + linter

```
$env:PYTHONUTF8="1"; py -m pytest -q   (full sweep #1, pre-fix)
  → 12 failed, 5288 passed, 1 skipped in 1560s (~26m)
     [11 seed-pin failures from incomplete τ.6.x.2.a-h migration
      + 1 load-induced perf flake]

[fix: 11 seed-pin migrations + ruff-format]

bg1fhzq1k (8 migrated files, post-fix) → 416 passed / 0 failed
pi0 migration + test_perf.py isolated → 13 passed / 0 failed
test_perf.py::test_notes_io_load_notes_under_budget solo → PASS 0.62s
   (confirms the full-sweep perf failure was load-induced flake;
    content/notes/gen.py was never touched by the Geʽez batch)

$env:PYTHONUTF8="1"; py -m pytest -q   (full sweep #2, post-fix)
  → 5298 passed, 1 skipped, 0 failed in 735s (12m14s)
     [all 12 prior failures resolved; perf flake did NOT recur]

$env:PYTHONUTF8="1"; py scripts/lint_rules.py
  → CLEAN: 11 pass · 0 warn · 0 fail

$env:PYTHONUTF8="1"; py -m ruff format --check .
  → 488 files already formatted
```

### Test growth trajectory

```
LIGHT-5    5069 (post-τ.7.x.f, cadence +169)
[τ.7.x.g]  +60  → 5128 (verified mid-session full sweep)
[τ.7.x.h]  +60  → ~5188
[τ.6.x.2.a-h batch] +84 (tau6x2_geez_arc) + 16 tau7x migrations net 0 → ~5272
[τ.7.x.i]  +65  → ~5337
[LIGHT-6 seed-pin migrations] net 0 (11 renames/flips, no count change)
NOW        5298 passed + 1 skipped (cadence +229 net vs LIGHT-5
                       5069; threshold crossing #3)
```

### Coverage histogram (τ.7.x.* Amharic family, 9 ships)

| Ship | Book | Verses / floor | Coverage |
|---|---|---:|---:|
| τ.7.x.c | Leviticus | 802 / 859 | **93.4%** (highest) |
| τ.7.x.i | Psalms | 2243 / 2531 | **88.6%** (2nd; LARGEST ingest) |
| τ.7.x.d | Numbers | 1107 / 1288 | 85.9% |
| τ.7.x.a | Genesis | 1308 / 1534 | 85.3% |
| τ.7.x.g | Judges | 511 / 618 | 82.7% |
| τ.7.x.e | Deuteronomy | 781 / 959 | 81.4% |
| τ.7.x.b | Exodus | 947 / 1213 | 78.1% |
| τ.7.x.f | Joshua | 483 / 658 | 73.4% |
| τ.7.x.h | Ruth | 60 / 85 | **70.6%** (lowest; smallest book) |

**Amharic 9-book combined: 8242 / 9745 = 84.6%** across Pentateuch
+ Joshua + Judges + Ruth + Psalms (excludes the 10 SKIPPED books in
the 438-802 dzamaragna gap).

**Geʽez 8-book combined (τ.6.x.2.a-h): 4337 / 7214 = 60.1%** — Geʽez
recovers ~72% of what Amharic does at the canonical-block level,
consistent with the τ.6.x.0a honesty-contract observation.

---

## 2. Coherence checks

- ✓ Prior-task cascade in IN_FLIGHT.md: τ.7.x.i (current) →
  τ.6.x.2.a-h batch → τ.7.x.h → τ.7.x.g → τ.7.x.f → … intact.
- ✓ SESSION_STATE.md head reflects τ.7.x.i; "Prior session" blocks
  preserve τ.6.x.2.a-h + τ.7.x.h cascade.
- ✓ CHANGELOG.md newest-first ordering preserved; τ.7.x.i + τ.6.x.2.
  a-h + τ.7.x.h + τ.7.x.g entries present.
- ✓ PLAN §6 ledger: τ.7.x.g/h shipped + τ.6.x.2.a-h batch shipped +
  τ.7.x.i shipped; τ.7.x.j NEXT-UP with 3 candidate blocks; τ.7.x.J-
  cluster (1 Sam→Job dzamaragna gap) BLOCKED + documented.
- ✓ test_omega4x_hygiene.py shipped/pending ledger updated through
  τ.7.x.i; assertion-list phase set extended.
- ✓ Both `_meta.yaml` files carry the upgrade provenance (geez
  `upgraded_from: Π.0-seed-3-verses` on τ.6.x.2.a; amharic
  `arc_skip_the_gap` + `arc_open_wisdom_and_poetry` on τ.7.x.i).

---

## 3. Disposition

- **Fix applied this audit:** 11 seed-pin migrations (7 file-listing
  superset-pins + 4 content-stem pins) — all green post-fix.
- **No code regression:** parser unchanged (17-ship zero-API-delta);
  the failures were stale TEST invariants, not behavior breakage.
- **Perf flake:** not a regression; load-induced; documented.
- **F-LIGHT6-1** (batch-ship migration-completeness gap): flagged
  for operator decision on whether it warrants a §12-retrospective
  trigger or a pre-flight invariant-flip blast-radius scan in the
  ship checklist. Single occurrence; not auto-codified.
- **Save:** proceed once bgup89xsd confirms all-pass (modulo the
  documented perf flake). save.cmd commits locally only — GitHub
  remote was deleted 2026-05-12; the push step in save.ps1 is
  commented out.
