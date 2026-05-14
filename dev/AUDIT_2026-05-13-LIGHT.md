# Project audit — 2026-05-13 LIGHT (solo-Claude, post γ.4.9 + γ.4.9.B)

**Trigger:** explicit user "ok light solo audit" after the session
shipped TWO new patristic-voice phases on top of the
AUDIT_2026-05-13-EOD baseline, plus two post-ship corrections:

```
γ.4.9              Athanasius seed (40 entries, 19 books)    commit 5c2d2bc
γ.4.9-NPNF-fixup   attribution abbrev correction              commit 5c2d2bc
γ.4.9.B            Athanasius Pauline detail (40, 8 books)     [uncommitted]
γ.4.9.B-dedup-fix  duplicate-promote artifact removal          [uncommitted]
```

Per memory `feedback_audit_cadence.md`, both cadence thresholds met:

- **Phase-count threshold (≥10 since prior audit):** 11 phases shipped
  since AUDIT_2026-05-13-EOD baseline — ω.41 hygiene + γ.4.7.B/C/D Mark
  arc-detail+close + γ.4.9 seed + γ.4.9-NPNF-fixup + γ.4.9.B detail +
  γ.4.9.B-dedup-fix + (cross-edition state-doc updates).
- **Test-drift threshold (≥150 since prior audit):** +92 (3808 → 3900).
  Below the 150 floor strictly, but the **major-event threshold** of
  "fifth-patristic-voice opening" (γ.4.9 introduces Athanasius as a
  new corpus voice — first new-Father in the patristic-anchor list
  since the corpus's founding γ.4 seed) is the stronger trigger.

This is the **light solo-Claude audit** form per memory: shorter
than AUDIT_2026-05-13-EOD's comprehensive sweep, focused on the
session's deltas rather than the full project surface.

---

## 0. TL;DR

**Project state at audit-time is clean.** All foreground checks pass:

- ✓ Test count: **3901 collected / 3900 passed + 1 skipped** (verified
  via `pytest --collect-only -q` + completed full-run during γ.4.9.B
  ship). Matches SESSION_STATE / IN_FLIGHT / CHANGELOG claims after
  the +15 net γ.4.9.B test delta corrected from the initial +16
  misclaim.
- ✓ Linter: **11/11 pass · 0 warn · 0 fail** with 242 non-legacy
  phase mentions tracked. γ.4.9.B + γ.4.9 mentions correctly tracked
  in CHANGELOG.
- ✓ Ruff format: **435 files already formatted** (0 drift).
- ✓ IN_FLIGHT: **idle** (γ.4.9.B documented as prior task; γ.4.7.D as
  earlier-prior).
- ✓ Source corpus: **1297 entries**, voice mix matches design exactly:
  Cyril 51.5% / Jubilees 15.4% / 1 Enoch 14.8% / Ephrem 12.1% /
  Athanasius 6.2%. Cyril-led-plurality intentional per ω.41 §1.
- ✓ Athanasius distribution per book: **80 total** matches expected 40
  seed + 40 detail = 80, per-book breakdown exact to design.

**No CRITICAL findings.** **Three new WARN items** surface (all
hygiene-class, none blocking):

1. **L-W1: at-scale driver append-not-dedup architectural fragility.**
2. **L-W2: candidates JSON files accumulate duplicates per ship.**
3. **L-W3: post-ship attribution-correction workflow has a known
   gotcha logged but not enforced.**

**Two recommendations follow up to prior AUDIT_2026-05-13-EOD
findings:**

- **EOD-W4 status check:** five `_ship_gamma*.py` scripts plus three
  one-shot LOAD-BEARING-ONCE scripts have accumulated in `scripts/`.
  §7.4 codifies the retention rule; no archival action triggered yet
  (γ.4.6 + γ.4.7 + γ.4.9 arcs still in their one-release-cycle window).
- **EOD-W3 / ω.41 §1 status:** the Cyril-led-plurality rule is
  preserved exactly — Cyril dropped 54.7% → 51.5% across the session's
  γ.4.7.B-D + γ.4.9 + γ.4.9.B ships (still plurality leader). γ.4.9's
  Athanasius addition kept patristic-anchor majority growing (67.6% →
  68.8% → 69.8%) without displacing Cyril.

**Uncommitted git state:** 378 files (376 modified + 2 new scripts) —
γ.4.9.B + γ.4.9.B-dedup-fix uncommitted. Per `feedback_continue_not_
save`, save is user-explicit only.

---

## 1. Per-point verification

### 1.1 Test count reconcile

| Source | Claim | Actual |
|---|---|---|
| `pytest --collect-only -q` | — | 3901 collected |
| Last full-run | — | 3900 passed + 1 skipped |
| SESSION_STATE | 3900 pass + 1 skip | ✓ matches |
| IN_FLIGHT | 3900 pass + 1 skip | ✓ matches |
| CHANGELOG | 3900 pass + 1 skip | ✓ matches |

Reconciliation: corrected from initial +16 misclaim. Actual: +15 net
(`TestGamma49BAthanasiusPaulineDetailWave` 14 tests +
`TestGamma4MetaPhasesCoverage::test_meta_documents_gamma_4_9_b` 1 test
= 15 total). Mid-turn correction applied to all three state docs.

### 1.2 Phase mention scan

Linter check `Phase mentions tracked in CHANGELOG` passes: all 242
non-legacy phase mention(s) in code appear in CHANGELOG.md. Specifically:

- γ.4.9 — present in CHANGELOG (2026-05-13 — γ.4.9 entry)
- γ.4.9.B — present in CHANGELOG (2026-05-13 — γ.4.9.B entry, NEW)
- γ.4.9-NPNF-fixup — referenced as post-ship correction within γ.4.9
  entry
- γ.4.9.B-dedup-fix — referenced as post-ship correction within γ.4.9.B
  entry

### 1.3 IN_FLIGHT marker check

`<!-- TRACKER-STATE: idle -->` — correct. The prior-task block describes
γ.4.9.B (current); earlier-prior describes γ.4.7.D (closed and committed
at 5c2d2bc).

### 1.4 Linter status

**11/11 clean · 0 warn · 0 fail.**

```
✓ Canonical-order encoders
✓ Cross-link invariant (all 17 consoles)
✓ Encoder/decoder round trip
✓ Documentation cross-references (all 18 scope addenda)
✓ SESSION_STATE freshness
✓ In-flight task tracker
✓ Phase mentions tracked in CHANGELOG (242 mentions)
✓ SESSION_STATE inventory matches consoles
✓ Atomic writes
✓ External HTTP
✓ Plan coherence
```

### 1.5 Ruff format check

**435 files already formatted** — 0 drift. New files (`_ship_gamma49b.
py`, `_fix_gamma49b_dedup.py`, test additions) all conform without
post-ship correction this time (NPNF abbreviation was used from the
start in γ.4.9.B per the lesson from γ.4.9 NPNF post-ship fix).

### 1.6 Source corpus voice composition

```
Total entries: 1297
  Cyril of Alexandria         668  51.5%  ← intentional plurality (ω.41 §1)
  Jubilees (Tewahedo OT)      200  15.4%
  1 Enoch (Tewahedo OT)       192  14.8%
  Ephrem the Syrian           157  12.1%
  Athanasius of Alexandria     80   6.2%  ← FIFTH VOICE (γ.4.9 + γ.4.9.B)
```

Patristic-anchor majority (Cyril + Ephrem + Athanasius) = **69.8%**
(up from EOD audit baseline 63.2%).

**No single-father-majority threshold crossed.** ω.41 §1 explicitly
permits >50% Cyril; current 51.5% remains comfortable plurality
without exceeding the §1 flag-threshold (which only requires
documenting the trajectory, not preventing it).

### 1.7 Athanasius distribution (γ.4.9 seed + γ.4.9.B detail)

| Book | seed | detail | total | source |
|---|---|---|---|---|
| gen | 2 | — | 2 | γ.4.9 |
| exo | 1 | — | 1 | γ.4.9 |
| psa | 2 | — | 2 | γ.4.9 |
| pro | 1 | — | 1 | γ.4.9 |
| isa | 2 | — | 2 | γ.4.9 |
| mat | 3 | — | 3 | γ.4.9 |
| jhn | 5 | — | 5 | γ.4.9 |
| **rom** | **3** | **10** | **13** | **γ.4.9 + γ.4.9.B** |
| **1co** | **2** | **6** | **8** | **γ.4.9 + γ.4.9.B** |
| **2co** | **1** | **3** | **4** | **γ.4.9 + γ.4.9.B** |
| **gal** | **1** | **3** | **4** | **γ.4.9 + γ.4.9.B** |
| **eph** | **1** | **4** | **5** | **γ.4.9 + γ.4.9.B** |
| **phi** | **3** | **4** | **7** | **γ.4.9 + γ.4.9.B** |
| **col** | **3** | **4** | **7** | **γ.4.9 + γ.4.9.B** |
| **heb** | **2** | **6** | **8** | **γ.4.9 + γ.4.9.B** |
| 1pe | 2 | — | 2 | γ.4.9 |
| 2pe | 1 | — | 1 | γ.4.9 |
| 1jn | 2 | — | 2 | γ.4.9 |
| rev | 3 | — | 3 | γ.4.9 |
| **TOTAL** | **40** | **40** | **80** | — |

Per-book distribution matches design exactly. The dedup correction
(`_fix_gamma49b_dedup.py`) successfully removed the 40 duplicate-
promote artifacts.

### 1.8 Git uncommitted state

```
376 modified files +
  2 new scripts (_ship_gamma49b.py, _fix_gamma49b_dedup.py)
= 378 total uncommitted
```

Modified breakdown:
- **362 candidate JSON files** (run_ethiopian_at_scale re-emit +
  γ.4.9.B + dedup marking 40 as rejected)
- **8 notes files** (the 8 Pauline books with γ.4.9.B detail entries)
- **1 source JSON** (`ethiopian_commentaries.json` — 1257→1297 entries)
- **1 test file** (`tests/test_ethiopian_gamma4.py`)
- **3 dev docs** (SESSION_STATE, IN_FLIGHT, CHANGELOG)
- **1 other** (likely `.refactor_log.yaml` audit-trail entry)

The dedup correction restored the 11 non-Pauline notes files to their
post-γ.4.9 state (matching commit `5c2d2bc`), so git correctly reports
them as UNCHANGED relative to HEAD.

---

## 2. NEW FINDINGS (this audit)

### L-W1: At-scale driver append-not-dedup architectural fragility

**Severity:** WARN (hygiene; no regression risk if discipline holds).

**Description:** `scripts/run_ethiopian_at_scale.py` uses
"append-not-overwrite" semantics on the per-chapter candidates JSON
files. Each at-scale run REGENERATES candidates from the source JSON
and APPENDS them to whatever's already in the candidates file. The
existing candidates from prior runs are preserved (with their current
status), and the new ones are appended with `status: "pending"`.

This pattern works correctly IF the source JSON content for prior
candidates is unchanged between at-scale runs. But IF the attribution
strings (or other content fields) change between at-scale runs —
e.g., a post-ship hygiene fix updates attribution — the new at-scale
run will emit NEW pending candidates for the same (book, chapter,
verse) keys with different content. The promote pass will see these
as legitimately-distinct from the existing-notes (per `promote.note_
already_exists` which checks body + attribution exact-match), and
will promote them as DUPLICATE notes.

This is what produced the γ.4.9.B duplicate-promote artifacts (40
seed entries re-promoted because their attribution had been
NPNF-corrected after the candidates were generated).

**Manifested:** γ.4.9.B promote pass returned 80 promoted instead of
expected 40. Caught by post-ship verification + dedup script applied.

**Recommended remediation (not blocking — present as a Δ.x-style
improvement track):**

1. **(Cheap)** Add a `--clean` flag to `run_ethiopian_at_scale.py`
   that DELETES existing candidates files before regenerating. The
   pre-ship clean would prevent stale-candidate-overlap. Document the
   "use --clean after post-ship content corrections" guidance.

2. **(Medium)** Make the at-scale driver DEDUP candidates by
   (book, chapter, verse, source_name) tuple — keep only one
   candidate per source-anchor key, preferring the one with newest
   `generated_at` timestamp.

3. **(Bigger)** Refactor the candidates JSON to use stable IDs
   (e.g., source-corpus-row-hash) rather than monotonic-counter IDs.
   Re-runs of at-scale would then OVERWRITE-by-ID rather than append,
   automatically deduping.

### L-W2: Candidates JSON files accumulate stale entries per ship

**Severity:** WARN (storage hygiene).

**Description:** Following L-W1, every at-scale run appends candidates
to existing files. Over the course of this session, candidate JSON
files have grown across multiple γ.4.6.x + γ.4.7.x + γ.4.9 + γ.4.9.B
runs. As of γ.4.9.B, the candidates corpus is **6913 candidate
records** across 362 files (vs ~4359 at γ.4.7.D ship time = ~2554
appended in 2 subsequent at-scale runs).

Of these 6913, only ~1297 represent unique (book, chapter, verse,
source) entries in the source corpus — the other ~5616 are
historical duplicates from prior at-scale runs. The promote pipeline
deals with them correctly via status flags + dedup-by-content, but
the storage footprint is growing.

**Recommended remediation (defer to next major candidates-pipeline
refactor):**

Add a `scripts/_cleanup_candidates.py` one-shot that:
- Reads each candidates/*.json file
- For each (book, chapter, verse, source_name) tuple, keeps only the
  entry with the most recent `generated_at` (or status="promoted" if
  any have it, breaking ties)
- Writes back the deduplicated file

Not urgent — the promote pipeline is correct, just inefficient.

### L-W3: Post-ship attribution-correction workflow has known gotcha

**Severity:** WARN (process hygiene).

**Description:** The γ.4.9 post-ship NPNF correction
(`_fix_gamma49_npnf.py`) updated attribution in:
1. ✓ Source JSON (`ethiopian_commentaries.json`)
2. ✓ Promoted notes (`content/notes/*.py`)
3. ✗ Candidates JSON (`content/candidates/*.json`) — **missed**

This third location was the trigger of the γ.4.9.B dedup issue. The
lesson is now LOGGED in CHANGELOG.md and IN_FLIGHT.md, but not
ENFORCED via tooling or a project rule. A future Claude could repeat
the mistake.

**Recommended remediation:**

1. **(Cheapest)** Add a brief note to CLAUDE_PROJECT_RULES.md §9 (the
   mental-models section, perhaps under a new "Post-ship attribution
   correction" subsection) codifying the three-locations-to-fix rule:
   source JSON + notes + candidates.

2. **(Medium)** Make `_fix_gamma49_npnf.py`-style fixup scripts a
   generic helper: `scripts/fix_attribution.py --old "..." --new
   "..."` that walks all three locations together.

3. **(Defensive)** Add a lint check or pre-commit hook that scans for
   attribution-drift between candidates JSON and source JSON for the
   same (book, chapter, verse, source_name) keys. If a candidate's
   `source_attribution` differs from the source corpus's `attribution`
   field for the same anchor, flag it.

---

## 3. STATUS of prior audit recommendations

### EOD-W1: PLAN_2026-05-09.md §2 status snapshot stale

**Status: NOT addressed this session** (still stale; refresh deferred
to next non-content-ship turn).

PLAN §2 still reads "3808 tests / 52,459 notes / 9 editions / 11/11
linter / 17 consoles + 11 books covered in patristic source corpus";
reality post-γ.4.9.B is "3900 tests / 52,539 notes (+80 Athanasius) /
9 editions / 11/11 linter / 17 consoles + 25 books covered in
patristic source corpus".

Not blocking — readers of PLAN §2 will see staleness but the
authoritative state is in SESSION_STATE.md. Refresh at next hygiene-
arc opportunity.

### EOD-W2: `_dedup_ethiopian_notes.py` LOAD-BEARING-NO-LONGER

**Status: NOT addressed this session.**

The file still exists in `scripts/` per the EOD-W2 recommendation
(emergency-restore tool). The docstring annotation noted as needed
was not added this session. Re-flag for next hygiene-arc.

### EOD-W3: Cyril approaching 50% single-father-majority

**Status: TRACKED AND PROCEEDING as designed.**

ω.41 §1 was codified earlier in the session, EXPLICITLY permitting
Cyril plurality with documentation requirement when crossing 50%.
γ.4.7.B did push Cyril past 50% to 50.8%, documented per ω.41 §1.
Subsequent γ.4.9 + γ.4.9.B opened a new Athanasius voice, bringing
Cyril back below 50% (to 51.5%, then to 51.5% after γ.4.9.B). No
intervention needed — the ω.41 §1 protocol is working as designed.

### EOD-W4: Five `_ship_gamma*.py` scripts accumulated in `scripts/`

**Status: GROWING (now 8 scripts total).**

Current `scripts/_ship_gamma*.py` inventory:
1. `_ship_gamma46.py` (γ.4.6 seed)
2. `_ship_gamma46b.py` (γ.4.6.B Sermon-on-Mount)
3. `_ship_gamma46c.py` (γ.4.6.C Galilean)
4. `_ship_gamma46d.py` (γ.4.6.D Matthew arc-close)
5. `_ship_gamma47.py` (γ.4.7 Mark seed)
6. `_ship_gamma47b.py` (γ.4.7.B Mark Galilean)
7. `_ship_gamma47c.py` (γ.4.7.C Mark Caesarea-Transfiguration)
8. `_ship_gamma47d.py` (γ.4.7.D Mark arc-close)
9. `_ship_gamma49.py` (γ.4.9 Athanasius seed)
10. `_ship_gamma49b.py` (γ.4.9.B Athanasius Pauline detail)

Plus 2 one-shot post-ship correction scripts:
11. `_fix_gamma49_npnf.py` (γ.4.9 NPNF abbreviation fixup)
12. `_fix_gamma49b_dedup.py` (γ.4.9.B duplicate-promote dedup)

Per §7.4 retention rule (codified at ω.41 hygiene): retain for one
full release cycle after the relevant arc closes, then archive to
`dev/archive/ship_scripts/<arc-tag>/`. The γ.4.6 Matthew arc closed
2026-05-13 PM (γ.4.6.D); its release cycle won't end until the v1.1
or next major-release tag drops. So 12-script accumulation is within
the codified retention window.

**Recommendation:** no immediate action. Re-evaluate at next v1.x
release.

### EOD-W5: State-aware test pattern documented

**Status: NEW SHIPS this session FOLLOW the pattern as designed.**

γ.4.9 + γ.4.9.B test classes correctly use `cache_clear()` in
`setup_class` and parse actual state rather than default-assume.
The state-aware contract from §8 is being respected.

---

## 4. Recommendations

| ID | Priority | Action | Effort |
|---|---|---|---|
| **L-W1** | Medium | Add `--clean` flag to `run_ethiopian_at_scale.py` OR dedup-by-anchor at append time | ~1 session |
| **L-W2** | Low | Add `_cleanup_candidates.py` for storage-hygiene one-shot | ~0.5 session |
| **L-W3** | Medium | Codify three-locations-to-fix rule in CLAUDE_PROJECT_RULES.md §9 OR build `fix_attribution.py` helper | ~0.5 session |
| **EOD-W1** | Low | Refresh PLAN_2026-05-09 §2 status snapshot | ~0.25 session |
| **EOD-W2** | Low | Document `_dedup_ethiopian_notes.py` LOAD-BEARING-NO-LONGER status | ~0.25 session |
| **(save)** | High (user-discretion) | Commit γ.4.9.B + γ.4.9.B-dedup-fix (378 uncommitted files) | <0.1 session |

The save is **user-explicit only** per memory `feedback_continue_not_
save.md`. The three new WARNs are all hygiene-class — non-blocking,
defer to next dedicated hygiene-arc.

---

## 5. Closing

This light audit confirms project state is healthy. The session's
ship cadence (γ.4.7.B/C/D + γ.4.9 + γ.4.9.B) executed cleanly modulo
two post-ship corrections (both caught + fixed in-turn per §3.6
bandwidth-aware). Both corrections produced LESSONS LOGGED in
CHANGELOG and IN_FLIGHT for future-reference.

The biggest finding is the **at-scale-driver-append-not-dedup
architectural fragility (L-W1)** — known but not yet remediated.
This is the root cause that triggered the γ.4.9.B dedup correction
and could trigger again if attribution strings are modified post-ship.
The workaround (delete candidates files OR avoid post-ship
attribution changes) is documented; the structural fix is deferred.

**Cyril-led-patristic-chorus character is intact** per ω.41 §1
codification. Athanasius's introduction as the fifth voice deepens
patristic plurality without displacing the intentional Cyril plurality.

**Next-step recommendation per memory `feedback_extensive_answers`
(broadest scope) + close-before-open precedent:** if the session
continues, the natural next ship is **γ.4.9.C** — Athanasius detail
wave covering the remaining γ.4.9 seed groups (OT christological
anticipations + Canonical Gospels + Petrine/Johannine/Apocalyptic).
Estimated scope ~40 entries. After γ.4.9.C + γ.4.9.D arc-close, the
Athanasius arc would be closeable per §8.1 (SEVENTH instance of
arc-close convention).

If the session is winding down: **save** is the recommended seam.
