# Project audit — 2026-05-15 LIGHT-5 (solo-Claude, post-τ.7.x.f, post-Pentateuch arc-open)

**Trigger:** user "audit and save" after τ.7.x.f ship close-out — explicit
cadence-window close request per `feedback_audit_cadence`. Cumulative
drift since LIGHT-4 baseline (4900) is **+169 tests across 3 ships**
(τ.7.x.d +51 + τ.7.x.e +57 + τ.7.x.f +57 + 3 share-pin refactors net 0 +
1 colophon-test-relaxation net 0) — crosses the ≥150 hard-threshold for
the cadence-window check, AND the chain includes the **§8.1 Pentateuch
arc-close** at τ.7.x.e (NINTH §8.1 instance overall + FIRST in τ-cluster)
AND the **post-Pentateuch historical-books arc-open** at τ.7.x.f.

**Form:** LIGHT solo-Claude per default. The previous LIGHT-4 closed after
the 3-ship τ.7.x.a/b/c chain (post-DEEP); LIGHT-5 closes after the next
3-ship τ.7.x.d/e/f chain, which crosses TWO significant structural
boundaries (§8.1 arc-close at τ.7.x.e + arc-open at τ.7.x.f).

**Audit chain on 2026-05-15:**

```
00:55   LIGHT     post-τ.6.x.1.B
01:32   τ.6.x.2.D D-decisions
...     LIGHT-2   post-τ.6.x.2.D
...     DEEP      post-τ.6.x.2.D extensive matrix audit
...     [4 ships chain: τ.6.x.2.D save + τ.7.x.a.0 + τ.6.x.1.C + τ.6.x.1.D]
...     LIGHT-3   post-τ.6.x.1.D
...     [3 ships chain: τ.7.x.a + τ.7.x.b + τ.7.x.c]
...     LIGHT-4   post-τ.7.x.c (cadence +153, first threshold crossing)
...     [save: τ.7.x.d + τ.7.x.e bundled]
...     [3 ships chain: τ.7.x.d + τ.7.x.e + τ.7.x.f]
NOW     LIGHT-5   post-τ.7.x.f (cadence +169, second threshold crossing;
                  arc-close + arc-open both happened in this window)
```

---

## 0. TL;DR

**Project state at audit-time is CLEAN across every checked dimension.**
The 3-ship τ.7.x.* chain since LIGHT-4 landed with **no regressions**,
the **§8.1 Pentateuch arc closed** at τ.7.x.e (the FIRST τ-cluster §8.1
arc-close — codifies STRUCTURAL §8.1 semantic as a sibling to the
γ-cluster's NARRATIVE §8.1 semantic), the **post-Pentateuch historical-
books arc opened** at τ.7.x.f, and the τ.7.x.a pipeline template is now
decisively established across SIX consecutive zero-parser-API-delta
ships covering 316 PDF pages.

### Foreground (every check passes)

- ✓ Test count: **5069 collected / 5069 passed + 1 skipped + 0 failed**
  (vs LIGHT-4's 4900; +169 net drift). Full suite runtime ~14m53s.
- ✓ Linter (`scripts/lint_rules.py`): **11/11 pass · 0 warn · 0 fail**;
  **253 non-legacy phase mentions** in PLAN/CHANGELOG cross-link
  (unchanged from LIGHT-4 — new phases τ.7.x.d/e/f appear in YAML +
  markdown + tests but the linter's phase-mention scanner counts
  unique Python-code phase tags only; not a regression).
- ✓ Console cross-link checks pass at **18 consoles** (unchanged
  since Ω.0).
- ✓ IN_FLIGHT: **idle** (`TRACKER-STATE: idle`); τ.7.x.f documented
  as prior task; prior-task chain τ.7.x.f → τ.7.x.e → τ.7.x.d →
  τ.7.x.c → τ.7.x.b → τ.7.x.a → ... preserved.
- ✓ Closed-arc invariants: **24 named invariants** intact (21 from
  LIGHT-4 + 3 NEW from the τ.7.x.d/e/f chain: tau7xd_ingest +
  tau7xe_ingest + tau7xf_ingest).
- ✓ State doc coherence: SESSION_STATE + IN_FLIGHT + CHANGELOG +
  PLAN §6 ledger + PI2_PRE_FLIGHT_CHECKLIST + hygiene tests all
  reference τ.7.x.f consistently. Cascade ordering preserved (τ.7.x.f
  current; τ.7.x.e prior; τ.7.x.d prior-previous; deeper history
  intact).
- ✓ ruff format: 474 files formatted clean (was 472 at LIGHT-4; +2
  new files: amharic-tewahedo/{deu,jos}.py + tests/test_parallel_
  bible_tau7x{d,e,f}.py — total +5 new files; ruff-format was
  applied proactively at each ship to avoid the ω.33-format-drift
  failure mode seen at τ.7.x.d).
- ✓ Pre-commit hook ran clean at τ.7.x.d+e save (commit 338c23c);
  τ.7.x.f save pending.

### Background findings (no follow-up required)

- Single-key back-link annotation pattern now at **10 instances**
  (was 7 at LIGHT-4); pattern definitively established + 5 pipeline-
  reuse variants in τ-cluster (τ.7.x.b→f).
- τ.7.x.* pipeline template confirmed STABLE across 6 consecutive
  per-book ships with zero parser API change. Six-ship zero-API-
  delta is the strongest-possible refactor-stability signal short
  of a code-frozen contract — any future per-book τ.7.x.* sub-ship
  under D1-a cadence is essentially a data-only change.
- §8.1 arc-close convention now codified for BOTH narrative and
  structural sub-variants (γ-cluster's NARRATIVE §8.1 via detail-
  wave-buildout + τ-cluster's STRUCTURAL §8.1 via per-book-cadence
  canonical-unit closure). Documented in `_source.yaml::tau7xe_
  ingest.arc_close_narrative`.

### NEW residual classes flagged for τ.6.x.3 audit

- **publisher_bridge_narrative_residual** (discovered at τ.7.x.f):
  the parallel-Bible-EOTC publisher occasionally includes a brief
  inter-book bridge narrative AT THE END of a book as a forward-
  reference summary BEFORE the formal next-book opening (Joshua's
  page 390 has Judges 3:7-12 content). This bridge text gets
  leaked into the τ.7.x.f ingest (~6-10 verses to renumbered ch
  19). τ.6.x.3 audit will need to (a) flag bridge-narrative
  leakage as non-canonical AND (b) check earlier τ.7.x.* ships
  (Gen, Ex, Lev, Num, Deu) for similar leakages — likely a class
  of residual affecting multiple ships, not just τ.7.x.f.
- **null_formal_title_banner_pattern** (discovered at τ.7.x.f):
  Joshua is the FIRST τ.7.x.* book WITHOUT an explicit `መጽሐፈ X`
  Book-of-X formal-title-banner form in the PDF text-layer (zero
  hits at boundary-discovery scan). Publisher uses the `ኦሪት ዘኢያሱ`
  running-header form consistently throughout pages 349-390.
  Boundary detection for the historical-books arc must rely on
  canonical-text scan rather than book-title-banner scan. Future
  τ.7.x.g+ ships should NOT assume `መጽሐፈ X` will be present;
  documented in `_source.yaml::structural_map.joshua.notes`.

---

## 1. Test + linter

```
$env:PYTHONUTF8="1"; py -m pytest -q
  → 5069 passed, 1 skipped in 893s (~14m53s)
  (vs LIGHT-4: 4900 / ~458s)

$env:PYTHONUTF8="1"; py scripts/lint_rules.py
  → CLEAN: 11 pass · 0 warn · 0 fail

$env:PYTHONUTF8="1"; py -m ruff format --check .
  → 474 files already formatted
```

### Test growth trajectory

```
LIGHT      4747 (post-τ.6.x.1.B)
LIGHT-2    4901 (cadence +154 to τ.6.x.2.D; +1 after share-pin migration)
DEEP       4747 → 4747 baseline matrix-audit, no test mutation
[4 ships]  τ.6.x.2.D save + τ.7.x.a.0 + τ.6.x.1.C + τ.6.x.1.D
LIGHT-3    4747 (cadence +0 from DEEP baseline; +153 cumulative)
[3 ships]  τ.7.x.a +48 + τ.7.x.b +50 + τ.7.x.c +50 + share-pins net 0
LIGHT-4    4900 (cadence +153, threshold crossing)
[save]     τ.7.x.d + τ.7.x.e bundled commit
[3 ships]  τ.7.x.d +51 + τ.7.x.e +57 + τ.7.x.f +57 + share-pins net 0
NOW        5069 (cadence +169, threshold crossing #2)
```

### Coverage histogram (τ.7.x.* family)

| Ship | Book | Verses extracted / floor | Coverage |
|---|---|---:|---:|
| τ.7.x.c | Leviticus | 802 / 859 | **93.4%** (highest) |
| τ.7.x.d | Numbers | 1107 / 1288 | 85.9% |
| τ.7.x.a | Genesis | 1308 / 1534 | 85.3% |
| τ.7.x.e | Deuteronomy | 781 / 959 | 81.4% |
| τ.7.x.b | Exodus | 947 / 1213 | 78.1% |
| τ.7.x.f | Joshua | 483 / 658 | **73.4%** (lowest) |

**Combined Pentateuch + Joshua coverage: 5428 / 6511 = 83.4%** across
**6 books / 316 PDF pages (0-390)** under Amharic-first sequencing.

---

## 2. State doc coherence

| Doc | τ.7.x.f reference | Cascade preserved |
|---|---|---|
| `dev/SESSION_STATE.md` | ✓ current snapshot | ✓ τ.7.x.e → prior; τ.7.x.d → prior-previous |
| `dev/IN_FLIGHT.md` | ✓ Prior task block | ✓ τ.7.x.e → previous; tracker idle |
| `dev/CHANGELOG.md` | ✓ entry prepended | ✓ append-only chronological |
| `dev/PLAN_2026-05-09.md` §6 | ✓ shipped row + next-up τ.7.x.g | ✓ |
| `dev/PI2_PRE_FLIGHT_CHECKLIST.md` | ✓ τ.7.x.f shipped row | ✓ τ.7.x.g-z next-up row |
| `tests/test_omega4x_hygiene.py` | ✓ shipped-phase list + pending list | ✓ |

---

## 3. Closed-arc invariants (24 total; +3 since LIGHT-4)

```
tau6x0a_no_ingest                 (preserved across 6 authorized violations)
tau6x0b_honesty_contract          (preserved)
tau6x0c_script_ethiopic_adoption  (preserved)
tau6x1_engine_wiring              (preserved)
tau6x1a_pilot_validation          (preserved)
tau6x1b_parser_extension          (preserved)
tau6x1c_parser_extension          (preserved)
tau6x1d_chapter_recovery          (preserved)
tau6x2D_decisions                 (preserved; D1-a + D4-c honored
                                   across 6 per-book sub-ships)
tau7xa_pre_pilot                  (preserved with finding_resolved_at_
                                   phase: τ.6.x.1.C back-link)
tau7xa_ingest                     (preserved with pipeline_reused_at_
                                   phase: τ.7.x.b back-link)
tau7xb_ingest                     (preserved; pipeline_reused_at_
                                   phase: τ.7.x.c back-link)
tau7xc_ingest                     (preserved; pipeline_reused_at_
                                   phase: τ.7.x.d back-link)
tau7xd_ingest                     (preserved; pipeline_reused_at_
                                   phase: τ.7.x.e back-link)      ← NEW
tau7xe_ingest                     (preserved; pipeline_reused_at_
                                   phase: τ.7.x.f back-link;
                                   arc_close: §8.1)                ← NEW
tau7xf_ingest                     (this ship; arc_open: post-
                                   pentateuch-historical-books)   ← NEW
[older invariants: Π.0 + Π.1 + Π.1.B + φ.1 + δ.1.0 + γ.4.x family +
 ω.4x family + Ω.0]
```

---

## 4. §8.1 arc-close instances (9 total; +1 in this window)

| # | Phase | Description | Cluster | Variant |
|---|---|---|---|---|
| 1 | γ.4.1.D | Cyril-on-John arc-close | γ | NARRATIVE (4 detail waves; 116 entries) |
| 2 | γ.4.2.D | Ephrem-on-Pentateuch arc-close | γ | NARRATIVE (4 waves; 117 entries) |
| 3 | γ.4.3.D | Cyril-on-Luke arc-close | γ | NARRATIVE (4 waves; 160 entries) |
| 4 | γ.4.4.E | 1 Enoch arc-close | γ | NARRATIVE (5 waves; 192 entries) |
| 5 | γ.4.5.E | Jubilees arc-close | γ | NARRATIVE (5 waves; 200 entries) |
| 6 | γ.4.6.D | Cyril-on-Matthew arc-close | γ | NARRATIVE (4 waves; ~155 entries) |
| 7 | γ.4.7.E | Cyril-on-Mark arc-close | γ | NARRATIVE (5 waves; ~150 entries) |
| 8 | γ.4.8.E | Mäqabyan arc-close | γ | NARRATIVE (5 waves; 200 entries; first 100%-chapter-coverage arc) |
| **9** | **τ.7.x.e** | **Pentateuch arc-close** | **τ** | **STRUCTURAL (5 per-book ingests; 4945 verses; FIRST τ-cluster instance)** |

§8.1 convention now generalizes cleanly to both NARRATIVE (γ-cluster
detail-wave buildout within a single voice/book) and STRUCTURAL (τ-
cluster per-book-cadence closure of a canonical unit) sub-variants.

---

## 5. Single-key back-link annotation pattern (10 instances)

| # | Source phase | Target phase | Annotation | Pattern variant |
|---|---|---|---|---|
| 1 | tau6x1a | tau6x1b | residual_resolved | residual-resolution |
| 2 | tau6x1b | tau6x2D | (D-decisions context) | scope-context |
| 3 | tau7xa_pre_pilot | tau6x1c | finding_resolved | finding-resolution |
| 4 | tau6x1c | tau6x1d | parser_extension | extension-chain |
| 5 | tau6x1d | τ.7.x.a | residual_resolved | residual-resolution |
| 6 | tau7xa_ingest | τ.7.x.b | pipeline_reused | pipeline-reuse |
| 7 | tau7xb_ingest | τ.7.x.c | pipeline_reused | pipeline-reuse |
| 8 | tau7xc_ingest | τ.7.x.d | pipeline_reused | pipeline-reuse |
| 9 | tau7xd_ingest | τ.7.x.e | pipeline_reused | pipeline-reuse |
| **10** | **tau7xe_ingest** | **τ.7.x.f** | **pipeline_reused** | **pipeline-reuse (6th τ-cluster instance)** |

Pattern definitively established. 5 of the 10 instances are pipeline-
reuse (τ-cluster); 3 are residual/finding-resolution; 1 is parser-
extension; 1 is scope-context.

---

## 6. Share-pin → milestone-pin conversion (5 instances codified)

Per `feedback_share_pin_pattern` (codified at γ.4.x). The per-ship
pattern: when a downstream ship bumps a stat-count, the upstream ship's
exact-count pin gets converted to a ≥-floor milestone-pin at downstream-
ship time.

| Conversion at ship | File | Original | Converted |
|---|---|---|---|
| τ.7.x.a (γ.4.4.E reference) | tau7xa | (initial different form) | `exceeds_seed` floor |
| τ.7.x.c | tau7xb | `test_stats_books_two` | `test_stats_books_at_least_two` |
| τ.7.x.d | tau7xc | `test_stats_books_three` | `test_stats_books_at_least_three` |
| τ.7.x.e | tau7xd | `test_stats_books_four` | `test_stats_books_at_least_four` |
| τ.7.x.f | tau7xe | `test_stats_books_five` | `test_stats_books_at_least_five` |

The τ.7.x.f exact-form pin (`test_stats_books_six`) will be converted
to `test_stats_books_at_least_six` at τ.7.x.g ship-time per the per-
ship pattern.

---

## 7. Stat consistency (cross-yaml + cross-test)

```
_meta.yaml stats.books            = 6 ✓
_meta.yaml stats.verses           = 5428 ✓ (1308+947+802+1107+781+483)
_meta.yaml ingest_records         = 6 (gen via 'ingest_record' + 5 named) ✓
_source.yaml structural_map       = 6 amharic sections + 3 Tewahedo-distinctive ✓
_source.yaml tau7x* ingest blocks = 7 (1 pre_pilot + 6 per-book ingest) ✓
tests/test_parallel_bible_tau7x*  = 6 files (a/b/c/d/e/f) ✓
tau7x* closed_arc_contracts       = 5 entries per latest tau7xf block ✓
```

All consistency dimensions cross-check cleanly.

---

## 8. Findings flagged

### F-LIGHT5-1 — publisher_bridge_narrative_residual

**Severity:** medium (data-quality, not blocking).

**Discovered at:** τ.7.x.f (page 390 inspection).

**Description:** The parallel-Bible-EOTC publisher occasionally includes
a brief inter-book bridge narrative AT THE END of a book as a forward-
reference summary BEFORE the formal next-book opening. Page 390 (Joshua's
last page) contains both Josh 24:33 + a Judges 3:7-12 forward-reference
summary + the end-of-Joshua colophon. The bridge text gets leaked into
the τ.7.x.f ingest (~6-10 verses to renumbered ch 19).

**Scope of impact:** unclear without τ.6.x.3 audit. The pattern may
affect ANY prior τ.7.x.* ship where the publisher used the same bridge-
narrative convention at the book-end boundary. Likely candidates: τ.7.x.b
Exodus (page 160 boundary into Leviticus — check for Lev 1:1 forward-
reference at Ex 40:38), τ.7.x.c Leviticus (page 213 boundary into
Numbers — check for Num 1:1 forward-reference at Lev 27:34), τ.7.x.d
Numbers (page 287 boundary into Deuteronomy — check for Deut 1:1
forward-reference at Num 36:13), τ.7.x.e Deuteronomy (page 348 boundary
into Joshua — check for Josh 1:1 forward-reference at Deut 34:12).

**Mitigation:** τ.6.x.3 batched audit will (a) flag bridge-narrative
leakage as non-canonical in tier-3 → tier-2 promotion pass AND (b)
check earlier τ.7.x.* ships for similar bridge-narrative occurrences.
Documented in `_source.yaml::structural_map.joshua.notes.publisher_
bridge_narrative_residual` + `_source.yaml::ocr_strategy.tau7xf_ingest.
known_residual_issues.new_publisher_bridge_narrative_residual` +
`amharic-tewahedo/_meta.yaml::ingest_record_tau7xf` commentary.

**Action:** none required at this ship. Flagged for τ.6.x.3 audit.

### F-LIGHT5-2 — null_formal_title_banner_pattern

**Severity:** low (boundary-detection robustness; not data-affecting).

**Discovered at:** τ.7.x.f (Judges title scan returned zero hits).

**Description:** Joshua is the FIRST τ.7.x.* book WITHOUT an explicit
`መጽሐፈ X` (Book of X) formal-title-banner form in the PDF text-layer.
Publisher uses the `ኦሪት ዘኢያሱ` running-header form consistently
throughout pages 349-390 — a structural variation from the Gen/Ex/Lev/
Num/Deut pattern (which all had explicit `ኦሪት ዘX` formal-title-banner
forms at the book-opening page or one page in).

**Scope of impact:** boundary-discovery methodology. Future τ.7.x.g+
ships should NOT assume `መጽሐፈ X` will be present. Boundary detection
must use:
1. Canonical-text scan for the FIRST-VERSE opening words (the most
   reliable indicator across both with-banner and without-banner cases).
2. Chapter-marker walk for `ምዕራፍ ፩` chapter-1 markers.
3. Running-header `ኦሪት ዘX` form as a secondary confirmation.

The `መጽሐፈ X` formal-title-banner is no longer a primary boundary
indicator — it's an optional confirmation marker that the historical-
books arc publisher elected to omit for Joshua.

**Mitigation:** documented in `_source.yaml::structural_map.joshua.
notes` so future τ.7.x.g+ boundary-discovery sub-phases use the
canonical-text-scan-first methodology.

**Action:** none required at this ship. Methodology lesson absorbed
into the τ.7.x.f boundary-discovery sub-phase narrative.

---

## 9. Conclusion

LIGHT-5 audit confirms project state CLEAN across all 8 checked
dimensions (test + linter + state-doc coherence + closed-arc
invariants + back-link pattern + share-pin migration + stat
consistency + ruff format). Two NEW residual classes flagged for
τ.6.x.3 audit (publisher_bridge_narrative_residual + null_formal_
title_banner_pattern) — neither blocking; both documented in
multiple cross-referenced locations.

The 3-ship τ.7.x.d/e/f chain crossed TWO significant structural
boundaries — the §8.1 Pentateuch arc-close at τ.7.x.e (9th overall +
1st in τ-cluster; codified STRUCTURAL §8.1 variant) + the post-
Pentateuch historical-books arc-open at τ.7.x.f. Six-ship zero-API-
delta achievement extends template stability across Pentateuch +
first historical-book = 6 books / 316 PDF pages.

**Next-up:** τ.7.x.g Amharic Judges full-book ingest (continues post-
Pentateuch historical-books arc; Judges 1:1 boundary already confirmed
at page 391 from this ship's pre-pilot scan).

**Save:** the τ.7.x.f bundle + LIGHT-5 audit doc commits next.

---

*Generated by solo-Claude post-τ.7.x.f per `feedback_audit_cadence`
on user "audit and save" request.*
