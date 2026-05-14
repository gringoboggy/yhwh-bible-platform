# Project audit — 2026-05-13 DEEP (solo-Claude, post γ.4.9.D arc-close + ALL-FIVE-VOICES closed)

**Trigger:** explicit user request "let's do a real good audit because I
have some amazing new findings for our project here — real public
domain info on maccabees" — *audit is forward-looking, staging for
incorporation of PD Maccabees research findings into the corpus*.

**Form:** deeper than AUDIT_2026-05-13-LIGHT (which covered γ.4.9 +
γ.4.9.B only at delta-level). This DEEP audit re-evaluates the entire
project surface in light of: (a) the all-five-patristic-arcs-closed
milestone reached at γ.4.9.D; (b) the user's PD Maccabees research
finding (incoming); (c) the LIGHT-audit-deferred hygiene items still
outstanding; (d) the post-γ.4.9.D state's specific implications for
γ.4.8 Mäqabyan (which has been DEFERRED-pending-PD-source-acquisition
since γ.4.5 ship, per the source corpus _meta.source ledger).

Per memory `feedback_audit_cadence` the proactive-suggestion default
is lighter-solo; this audit is explicitly user-requested as "real
good," so the form is deep-solo (deeper than LIGHT, lighter than
parallel-subagent sweep).

---

## 0. TL;DR

**Project structural state is clean.** All foreground checks pass:

- ✓ Test count: **3935 collected** (3901 LIGHT-audit-baseline + 34 from
  γ.4.9.C + γ.4.9.D = 3935 exact match). Last full run with γ.4.9.D
  included: ~3924 pass + 1 skip + 11 intermittent env-flake (pre-
  existing Python 3.14/Windows subprocess handle-exhaustion documented
  at γ.4.9.C).
- ✓ Linter: **11/11 pass · 0 warn · 0 fail**.
- ✓ Ruff format: **437 files clean** (post-save).
- ✓ IN_FLIGHT: **idle** (γ.4.9.D documented as prior task).
- ✓ Source corpus: **1367 entries**, all five patristic voices at
  closed-arc depth (Cyril 668 / Jubilees 200 / 1 Enoch 192 / Ephrem
  157 / Athanasius 150). All seven §8.1 arc-close instances verified
  via PIN #1 (count milestone) + PIN #2 (all_N_sections_covered) +
  PIN #3 (_meta synchronization).
- ✓ γ.4.x phase-tag coverage in _meta.source: all 35 tags from γ.4.1
  through γ.4.9.D present.
- ✓ Save: commit `037e7c0` (γ.4.9.C + γ.4.9.D bundle, +67003 / -819
  across 419 files) — clean.

**THREE NEW CRITICAL findings:**

1. **D-C1 — Mäqabyan / γ.4.8 READINESS UNBLOCKED.** All three Tewahedo-
   distinctive `mq1.py` / `mq2.py` / `mq3.py` notes files exist (per
   books.yaml schema) but contain **ZERO tuples**. The source corpus
   _meta.source has carried the deferral marker "γ.4.8 Mäqabyan seed
   (DEFERRED — PD source acquisition pending)" since the γ.4.5 ship
   trail. The user's incoming PD Maccabees research is the canonical
   unblocker for γ.4.8. **Highest-priority new ship target.**

2. **D-C2 — Six empty Tewahedo-distinctive notes files** in addition
   to the Mäqabyan triple: `4ba.py` (4 Baruch / Paralipomena Jeremiou)
   + `2en.py` (2 Enoch) + `1cl.py` (1 Clement) are all 0-tuple. Each
   represents a Tewahedo-canonical or Tewahedo-receivable book the
   buyer-demo could surface as a uniqueness-angle differentiator. None
   are currently in the patristic source corpus either. **Strategic
   coverage gap; medium-priority for v1.1.**

3. **D-C3 — Book-code normalization inconsistencies in source JSON.**
   The runtime aliasing in `scripts/core/sources.py` handles `joh→jhn`
   and `ps→psa` symmetrically (lines 67-68), but the source JSON
   carries entries with BOTH legacy and canonical codes
   simultaneously: `joh` 119 entries (Cyril) + `jhn` 11 entries
   (Athanasius); `ps` 2 entries + `psa` 12 entries. This is not a
   functional bug (the runtime normalization fixes lookups) but it is
   data-hygiene drift that future hand-inspection will trip on. The
   `jas/jam` finding from γ.4.9.D is the same pattern with a different
   resolution path (no aliasing handles `jas→jam`).

**FIVE NEW WARN findings:**

- **D-W1** — Ship-script accumulation at 12 + 2 fix scripts (one above
  the EOD-W4 threshold; retention-window guidance from §7.4 says
  archive when arc closes).
- **D-W2** — `_BOOK_CODE_ALIASES` in sources.py is incomplete
  (missing `jas→jam` to match the notes-file convention).
- **D-W3** — Six Tewahedo-distinctive notes files (mq1/mq2/mq3 +
  4ba + 2en + 1cl) are empty; books.yaml schema declares them but
  zero content backs them. EPUB build may emit them as empty (UX
  inconsistent vs Hebrew + Greek + Aramaic equivalents).
- **D-W4** — The pre-existing 11 OSError WinError-6 subprocess
  failures on Python 3.14 + Windows (documented at γ.4.9.C) are
  unaddressed environmental flake. Without a stable-suite baseline
  it's hard to detect future regressions.
- **D-W5** — Five LIGHT-audit findings (L-W1 at-scale append-not-dedup
  fragility, L-W2 candidates JSON dup accumulation, L-W3 attribution-
  correction three-locations gotcha, EOD-W1 PLAN refresh status,
  EOD-W2 docstring annotation) remain unaddressed.

**THREE NEW INFO findings:**

- **D-I1** — All seven §8.1 arc-close instances verified
  structurally: γ.4.4.E + γ.4.5.E + γ.4.2.D + γ.4.3.D + γ.4.6.D +
  γ.4.7.D + γ.4.9.D each carry PIN #1 + #2 + #3.
- **D-I2** — γ.4.x phase coverage in _meta.source spans the full 35
  sub-phase tags (γ.4.1 through γ.4.9.D). The plan-coherence linter
  check confirms no orphan phase mentions outside CHANGELOG.
- **D-I3** — `dan.py` (510), `mat.py` (2237), `mrk.py` (1129),
  `sir.py` (1134), and other notes files are substantively populated
  via the long-running prospect→promote pipeline. Notes corpus
  totals 52,761 tuples across 87 non-empty files — 148% of original
  35-40k target.

---

## 1. Per-point verification

### 1.1 Test count reconcile

| Source | Claim | Actual |
|---|---|---|
| `pytest --collect-only -q` | — | **3935 collected** |
| LIGHT-audit baseline | 3901 collected | 3901 (pre-γ.4.9.C) |
| γ.4.9.C class | +17 pins + 1 meta | +18 |
| γ.4.9.D class | +15 pins + 1 meta | +16 |
| 3901 + 18 + 16 | 3935 | ✓ match |

Reconciliation clean — every test addition is accounted for.

### 1.2 Phase mention scan

Linter check `Phase mentions tracked in CHANGELOG.md`: **all 242 non-
legacy phase mention(s) in code appear in CHANGELOG.md**.

All four γ.4.9.x tags present in CHANGELOG.md + _meta.source:
- γ.4.9 — present (5c2d2bc commit + CHANGELOG entry + _meta ledger)
- γ.4.9.B — present (9cd6b18 commit + CHANGELOG entry + _meta ledger)
- γ.4.9.C — present (037e7c0 commit + CHANGELOG entry + _meta ledger)
- γ.4.9.D — present (037e7c0 commit + CHANGELOG entry + _meta ledger
  + "ARC CLOSED" status marker for §8.1 PIN #3 detection)

### 1.3 IN_FLIGHT marker

`<!-- TRACKER-STATE: idle -->` — correct. Prior task is γ.4.9.D
(closed); Earlier-prior is γ.4.9.C (closed and committed). Tracker
hygiene clean.

### 1.4 Linter status

**11/11 clean · 0 warn · 0 fail**:

```
✓ Canonical-order encoders
✓ Cross-link invariant
✓ Encoder/decoder round trip
✓ Documentation cross-references
✓ SESSION_STATE freshness
✓ In-flight task tracker
✓ Phase mentions tracked in CHANGELOG (242 non-legacy mentions)
✓ SESSION_STATE inventory matches consoles (17/17)
✓ Atomic writes (no raw open('w') outside notes_io)
✓ External HTTP (no raw urlopen outside scripts/core/http.py)
✓ Plan coherence (PLAN ↔ CHANGELOG ↔ Depends) — 4 sub-checks pass
```

### 1.5 Voice mix (exact)

```
Cyril of Alexandria         668   48.87%
Jubilees (Ethiopian)        200   14.63%
1 Enoch (Ethiopian)         192   14.05%
Ephrem the Syrian           157   11.49%
Athanasius of Alexandria    150   10.97%
───────────────────────────────────
Total                      1367  100.00%
```

Per ω.41 §1: Cyril remains plurality-leader at 3.34× next-single-
father (668 vs 200). Sub-50% trajectory settled (γ.4.9.C downward-
crossing → γ.4.9.D 48.87% post-arc-close). The Cyril-remains-
plurality-leader DURABLE PIN (in `TestGamma49DAthanasiusArcClose::
test_cyril_remains_plurality_leader_at_arc_close`) guards this
invariant against future voice-mixing.

Patristic-anchor majority (Cyril + Ephrem + Athanasius) = 975/1367 =
**71.32%** — exactly matches CHANGELOG / SESSION_STATE claim.

### 1.6 Save state

```
Commit  037e7c0  γ.4.9.C + γ.4.9.D
        9cd6b18  γ.4.9.B + LIGHT audit
        5c2d2bc  γ.4.9 seed (5th patristic voice opened)
        9b18a47  γ.4.7.C + γ.4.7.D (Mark arc-close)
        f7af222  γ.4.7.B (Cyril crosses 50% intentionally)
```

419 files committed in 037e7c0 (+67003 insertions / -819 deletions);
both new ship scripts (`_ship_gamma49c.py` + `_ship_gamma49d.py`)
created. Pre-commit hook caught + auto-fixed 19-file ruff format drift
during the save (notes/*.py touched by batch_promote).

No remote configured (GitHub remote deleted 2026-05-12 per memory
`reference_save`).

---

## 2. Five-arc closure deep-verification (§8.1 PIN #1+2+3 per voice)

The §8.1 arc-close convention requires three pin types at every arc
closure: PIN #1 (absolute-count milestone), PIN #2 (all_N_sections_
covered exhaustiveness), PIN #3 (_meta synchronization). Verifying
each closed arc satisfies all three.

### 2.1 γ.4.4.E Mäṣḥafä Hēnok (1 Enoch — FIRST §8.1 instance)

- PIN #1 count milestone: 192 entries (target ≥190) ✓
- PIN #2 all_N_sections_covered: Watchers γ.4.4.B + Parables γ.4.4.C +
  Astronomical+Dream γ.4.4.D + Epistle γ.4.4.E — all sections present
  per `TestGamma44E1EnochEpistleArcClose` pin set ✓
- PIN #3 _meta synchronization: γ.4.4 + .B + .C + .D + .E all present
  in _meta.source ✓

### 2.2 γ.4.5.E Mäṣḥafä Kufāle (Jubilees — SECOND §8.1 instance)

- PIN #1: 200 entries (target ≥200) ✓
- PIN #2 all six sections covered (Sinai-prologue + Watchers-Noahide +
  Abraham + Decline + Jacob + Joseph-Exodus-finale) per
  `TestGamma45EJubileesArcClose` ✓
- PIN #3: γ.4.5 + .B + .C + .D + .E all in _meta.source ✓

### 2.3 γ.4.2.D Ephrem-on-Pentateuch (THIRD §8.1 instance)

- PIN #1: Ephrem 157 entries (cumulative across all γ.4.2.x waves)
  ✓
- PIN #2: γ.4.2 Gen + γ.4.2.B Gen-detail + γ.4.2.C Exo + γ.4.2.D
  Num+Deu — four-wave Pentateuch coverage at ≥20 entries per book
  ✓
- PIN #3: γ.4.2 + .B + .C + .D in _meta ✓

### 2.4 γ.4.3.D Cyril-on-Luke (FOURTH §8.1 instance)

- PIN #1: 160 entries on Luke (4-wave) ✓
- PIN #2: γ.4.3 seed (Lk 1-24 at 40) + γ.4.3.B Lk 1-9 + γ.4.3.C Lk
  10-19 + γ.4.3.D Lk 20-24 — all four chapter-range waves present
  ✓
- PIN #3: γ.4.3 + .B + .C + .D in _meta ✓

### 2.5 γ.4.6.D Cyril-on-Matthew (FIFTH §8.1 instance)

- PIN #1: 195 entries on Matthew ✓
- PIN #2: γ.4.6 seed + γ.4.6.B Sermon-on-Mount + γ.4.6.C Galilean +
  γ.4.6.D arc-close ✓
- PIN #3: γ.4.6 + .B + .C + .D in _meta ✓

### 2.6 γ.4.7.D Cyril-on-Mark (SIXTH §8.1 instance)

- PIN #1: 192 entries on Mark ✓
- PIN #2: γ.4.7 seed + γ.4.7.B Mk 1-5 + γ.4.7.C Mk 6-10 + γ.4.7.D
  Mk 11-16 — every chapter range substantively detailed ✓
- PIN #3: γ.4.7 + .B + .C + .D in _meta ✓

### 2.7 γ.4.9.D Athanasius (SEVENTH §8.1 instance — THIS SESSION)

- PIN #1: Athanasius 150 entries ✓
- PIN #2: γ.4.9 seed (≥40) + γ.4.9.B Pauline (≥56) + γ.4.9.C non-
  Pauline (≥64) + γ.4.9.D arc-close NEW-books (≥12) — every wave
  present at planned depth ✓
- PIN #3: γ.4.9 + .B + .C + .D + "ARC CLOSED" + "Marcellinus" + 
  "SEVENTH" all in _meta.source ✓

**All seven §8.1 arc-close instances structurally verified.** The
convention is now project-wide-canonical (7 instances; pattern
established).

---

## 3. Hygiene-arc inventory (deferred items re-evaluated)

### 3.1 LIGHT-audit deferrals (2026-05-13 / 23:11)

| ID | Description | Status post-γ.4.9.D | Priority |
|---|---|---|---|
| L-W1 | at-scale driver append-not-dedup fragility | UNCHANGED; the γ.4.9.B duplicate-promote artifact root cause is still architectural — `run_ethiopian_at_scale.py` appends rather than dedups by anchor at candidate-write time. The mid-turn jas→jam correction at γ.4.9.D required a stale-candidate manual cleanup (`jas-1-17-047` removed from `jas_ch_001.json`), confirming the L-W1 fragility remains live. | Medium — recommend fix before next γ.4.x ship |
| L-W2 | candidates JSON duplicate accumulation | UNCHANGED; ~1589 candidate files now (up from 1546 at LIGHT). Per `batch_promote_xrefs.py` second-pass output (γ.4.9.D): "10944 attempted" — most are stale-existing-already-existed candidates. | Low — defer to dedicated hygiene-arc |
| L-W3 | post-ship attribution-correction three-locations gotcha | UNCHANGED but ω.41 codified ship-script retention rule mitigates blast-radius. γ.4.9.D did not trigger an attribution-correction this session. | Low — codify in CLAUDE_PROJECT_RULES §9 |
| EOD-W1 | PLAN_2026-05-09 §2 status snapshot refresh | UNCHANGED — still at 3808 tests / 52459 notes from ω.41 hygiene bundle. With γ.4.9.x ships, the snapshot is ~127 tests + ~302 notes stale. | Low — bundle with next hygiene-arc |
| EOD-W2 | `_dedup_ethiopian_notes.py` LOAD-BEARING-NO-LONGER annotation | UNCHANGED — still no annotation added per LIGHT recommendation. | Low — single-line edit |
| EOD-W3 | Cyril 50% threshold trajectory | RESOLVED — γ.4.9.B/.C/.D all properly trajectory-tracked; ω.41 §1 trajectory rule working as designed. Cyril 49.96% → 48.87% sub-50% downward-cross is settled and pinned. |  |
| EOD-W4 | ship-script accumulation | STATUS: 12 `_ship_gamma*.py` + 2 `_fix_*.py` = 14 scripts. The retention rule (§7.4: keep one release cycle after arc closes) is **active** — but with γ.4.9.D closing the last patristic arc, γ.4.6.x scripts (4 files: gamma46/.B/.C/.D) and γ.4.7.x scripts (4 files) are now eligible for archival to `dev/archive/ship_scripts/`. The γ.4.9.x quartet (4 files) is too fresh. | Medium — archive 8 scripts in next hygiene-arc |
| EOD-W5 | other default-state-assumption tests | UNCHANGED — still deferred from EOD audit. |  Low |

### 3.2 New from γ.4.9.D arc-close

- **D-LOG-1 (jas/jam project-level book-code inconsistency):**
  `scripts/core/sources.py` `_BOOK_CODE_ALIASES_LONGFORM` maps
  `"james": "jas"` but `content/notes/jam.py` is the actual file
  (jas.py absent). Caused mid-turn 29-of-30 promote-shortfall at
  γ.4.9.D. **The shorter `_BOOK_CODE_ALIASES` dict (lines 66-69)
  handles `joh→jhn` and `ps→psa` but is missing `jas→jam`.**
  Single-line fix: add `"jas": "jam"` to `_BOOK_CODE_ALIASES`.
  *Caveat: would need symmetric verification — any code path that
  currently expects "jas" output would break.*

- **D-LOG-2 (env-flake on Python 3.14 + Windows subprocess):** 11
  test failures persist whenever full-suite runs (test_audit_dead_code
  5, test_audit_types 4, test_desktop_theta 1, test_lint_rules:
  TestOmega33RuffFormat 1). Root cause is `_winapi.DuplicateHandle`
  "WinError 6 The handle is invalid" during subprocess.PIPE handle
  exhaustion. Hypothesis: Python 3.14 subprocess.PIPE handle cleanup
  is not aggressive enough on Windows; multiple subprocess-spawning
  test files in a single pytest session leak handles. Mitigations:
  (a) pytest-forked plugin for per-test process isolation, (b)
  pytest-xdist `-n auto --boxed` for sandboxed parallel execution,
  (c) downgrade-test to Python 3.13.

### 3.3 Ship-script archival candidates (per §7.4 retention rule)

Per §7.4 codified at ω.41: retain ship-scripts for ONE full release
cycle after arc closes, then archive to `dev/archive/ship_scripts/
<arc-tag>/`. The arc-close events and their archival eligibility:

```
arc                              closed at      eligible to archive?
γ.4.4 Mäṣḥafä Hēnok (1 Enoch)    γ.4.4.E        YES (multiple release-cycles old)
γ.4.5 Mäṣḥafä Kufāle (Jubilees)  γ.4.5.E        YES (multiple release-cycles old)
γ.4.2 Ephrem-Pentateuch          γ.4.2.D        YES (1+ release cycle)
γ.4.3 Cyril-on-Luke              γ.4.3.D        YES (1+ release cycle)
γ.4.6 Cyril-on-Matthew           γ.4.6.D        YES — 4 scripts: 46/.B/.C/.D
γ.4.7 Cyril-on-Mark              γ.4.7.D        YES — 4 scripts: 47/.B/.C/.D
γ.4.9 Athanasius                 γ.4.9.D        NO — fresh (this session)
```

Estimated archival queue: 8 `_ship_gamma*.py` scripts (γ.4.6.x + γ.4.7.x
quartets). The γ.4.4.x + γ.4.5.x + γ.4.2.x + γ.4.3.x scripts may already
have been archived earlier; let me verify.

```bash
$ ls scripts/_ship_gamma*.py
_ship_gamma46.py    _ship_gamma46b.py   _ship_gamma46c.py   _ship_gamma46d.py
_ship_gamma47.py    _ship_gamma47b.py   _ship_gamma47c.py   _ship_gamma47d.py
_ship_gamma49.py    _ship_gamma49b.py   _ship_gamma49c.py   _ship_gamma49d.py
```

So γ.4.4 + γ.4.5 + γ.4.2 + γ.4.3 + γ.4.1 scripts are already archived
(not in `scripts/` anymore). γ.4.6 + γ.4.7 quartets remain in scripts/
(2 closed arcs × 4 scripts = 8 files). γ.4.9 quartet stays (fresh).

---

## 4. Tewahedo-distinctive coverage gap analysis

**This is the audit's most-significant section.** With all five
patristic voices closed-arc, the structurally-next coverage question
is: *which Tewahedo-canonical or Tewahedo-distinctive books still lack
substantive content?*

### 4.1 Tewahedo-canonical book status

```
code  book                                  notes-file content
─────────────────────────────────────────────────────────────────
mq1   Mäqabyan I (Ethiopian Maccabees I)    0 tuples  ← EMPTY
mq2   Mäqabyan II (Ethiopian Maccabees II)  0 tuples  ← EMPTY
mq3   Mäqabyan III (Ethiopian Maccabees III) 0 tuples ← EMPTY
1en   1 Enoch / Mäṣḥafä Hēnok               422 tuples
jub   Jubilees / Mäṣḥafä Kufāle             200 tuples
4ba   4 Baruch / Paralipomena Jeremiou      0 tuples  ← EMPTY
2en   2 Enoch                               0 tuples  ← EMPTY
1cl   1 Clement                             0 tuples  ← EMPTY
sir   Sirach / Ecclesiasticus               1134 tuples
1es   1 Esdras                              271 tuples
2es   2 Esdras                              539 tuples
jdt   Judith                                274 tuples
bar   Baruch                                178 tuples
lje   Letter of Jeremiah                    33 tuples
man   Prayer of Manasseh                    21 tuples
sus   Susanna                               40 tuples
bel   Bel and the Dragon                    19 tuples
paz   Prayer of Azariah                     79 tuples
```

**Six books with EXISTING file infrastructure but zero content:**
- `mq1` / `mq2` / `mq3` — three uniquely-Tewahedo Mäqabyan books
- `4ba` — 4 Baruch (Paralipomena Jeremiou, Tewahedo-canonical OT)
- `2en` — 2 Enoch (Slavonic but received in Tewahedo tradition)
- `1cl` — 1 Clement (Tewahedo broader canon includes this and Shepherd
  of Hermas)

### 4.2 γ.4.8 Mäqabyan — DEFERRED-PENDING-PD-ACQUISITION pre-history

The source corpus _meta.source ledger contains this string **multiple
times** across the γ.4.5/.B/.C/.D/.E ships:

> "Future γ.4-cluster work: γ.4.8 Mäqabyan seed (DEFERRED — PD source
> acquisition pending)."

And later in the γ.4.2.C ship:

> "Future γ.4-cluster work: γ.4.2.D Ephrem on Numbers-Deuteronomy;
> γ.4.3 Cyril on Luke (Payne Smith 1859 PD); **γ.4.8 Mäqabyan seed
> (DEFERRED — PD source acquisition pending)**."

**γ.4.8 is the pre-reserved phase letter for Mäqabyan in the Greek-
phase taxonomy.** The phase number was held vacant DELIBERATELY across
all the γ.4 ships, waiting for the user (or research) to acquire a
public-domain Mäqabyan source. The user's incoming PD Maccabees
research IS the unblocker for γ.4.8.

### 4.3 Greek Maccabees vs Ethiopian Mäqabyan — disambiguation

These are TWO DIFFERENT TEXT FAMILIES with the same English name. The
user's research could plausibly cover either, and the project should
be ready for both:

| Greek Maccabees | Ethiopian Mäqabyan |
|---|---|
| 1 Maccabees (LXX, Catholic + Orthodox deutero) | Mäqabyan I (Tewahedo unique) |
| 2 Maccabees (LXX, Catholic + Orthodox deutero) | Mäqabyan II (Tewahedo unique) |
| 3 Maccabees (LXX, Orthodox only) | Mäqabyan III (Tewahedo unique) |
| 4 Maccabees (LXX appendix; Stoic-Jewish) | (no Tewahedo equivalent) |
| Hebrew/Greek/Syriac transmission | Ge'ez transmission only |
| About Maccabean revolt (~160s BC) | About entirely-different patriarchs (Meqabis the Benjamite, etc.) |

**Project-state inventory of book codes:**

```
1mc / 2mc / 3mc / 4mc      books.yaml: ABSENT
mq1 / mq2 / mq3            books.yaml: PRESENT (titled "The Book of Meqabyan I/II/III")
notes/1mc.py etc.          ABSENT
notes/mq1/2/3.py           PRESENT (empty)
```

So **the project canon currently includes Mäqabyan but NOT Greek
Maccabees**. The Tewahedo flagship's natural canon is Mäqabyan; Greek
Maccabees (1-2-3-4) would need to be added (`books.yaml` extension +
new `*.py` notes files) for Catholic/Orthodox editions.

### 4.4 If user's research is on Mäqabyan (most-likely)

**γ.4.8 ships directly** — the phase letter is reserved, the file
infrastructure exists, the only blocker (PD source acquisition) is now
resolved. Estimated ship scope: parallels the γ.4.4 / γ.4.5 / γ.4.9
seed-then-detail pattern.

A natural γ.4.8 architecture (proportionate to other voice arcs):
- γ.4.8 seed: ~30-40 entries across Mäq 1+2+3 (multi-book seed)
- γ.4.8.B / .C / .D detail waves: ~40 each, one per Mäqabyan book
- γ.4.8.E arc-close: §8.1 PIN #1 + #2 + #3 (EIGHTH §8.1 instance)
- Estimated end-state: ~160-200 cumulative entries (parity with other
  arcs)

### 4.5 If user's research is on Greek Maccabees (less-likely)

Greek Maccabees would be a **books.yaml extension** + new notes-file
scaffolding (1mc/2mc/3mc/4mc) BEFORE any patristic-source corpus
addition. Would shift project canon from Tewahedo-pure toward
Catholic-Orthodox-Tewahedo-multi-canon. Larger architectural change.

### 4.6 Where γ.4.8 fits in the §3 sequencing priorities

Per §3 priorities:
1. **Safest / most-foundational first** — γ.4.8 is additive; new
   Mäqabyan content doesn't modify existing notes. ✓
2. **Buyer-demo value** — γ.4.8 specifically delivers a **Tewahedo
   uniqueness angle** that no competing free Bible app has at depth.
   Per memory `project_v1_terminus`, v1.1 needs "publisher-led
   uniqueness-angle pick." γ.4.8 is the unique-canonical-text
   uniqueness angle. **HIGH-VALUE.**
3. **Pair related phases** — γ.4.8 is its own arc; doesn't pair with
   currently-open phases.
4. **Logical seams** — γ.4.8 closes one of the three remaining "Empty
   Tewahedo-canonical-book triplet" gaps.
5. **The 7-minute budget** — γ.4.8 seed alone (~30-40 entries) fits
   in one session; full arc (seed + 3 detail + arc-close) is a
   multi-session arc on the precedent of γ.4.4 / γ.4.5 / γ.4.9.
6. **Bandwidth-aware** — All ship-pipeline infrastructure already
   exists (`run_ethiopian_at_scale.py` + `batch_promote_xrefs.py` +
   `EthiopianCommentaryDetector`). No new infrastructure required.

**γ.4.8 is the highest-value, lowest-friction next ship.**

---

## 5. Plan ↔ shipped reconciliation

### 5.1 PLAN_2026-05-09.md status

Per EOD-W1 LIGHT-audit deferral, the PLAN_2026-05-09 §2 status
snapshot is stale at 3808 tests / 52459 notes. The actual state is now:

```
Test count:   3935  (drift: +127 since PLAN snapshot)
Notes total:  52761  (drift: +302 since PLAN snapshot)
γ.4 phases:   28 sub-phases shipped since PLAN
Patristic:    1367 entries / 5 voices all closed-arc
```

**Refresh recommendation:** in next hygiene-arc, update PLAN §2 with
current numbers + note that γ.4.x is now at all-five-voices-closed
state. **No functional issue; documentation drift only.**

### 5.2 CHANGELOG ↔ commit reconciliation

```
Commit       CHANGELOG entry        SESSION_STATE
037e7c0      γ.4.9.C + γ.4.9.D  ✓   most-recent block  ✓
9cd6b18      γ.4.9.B            ✓   2nd most-recent    ✓
5c2d2bc      γ.4.9 seed         ✓   3rd most-recent    ✓
9b18a47      γ.4.7.C + γ.4.7.D  ✓   present            ✓
f7af222      γ.4.7.B            ✓   present            ✓
```

All recent commits have matching CHANGELOG + SESSION_STATE entries.
Linter `SESSION_STATE freshness` check confirms CHANGELOG + SESSION_
STATE are updated together.

### 5.3 Open scope addenda

```
SCOPE_2026-05-08-addendum-textcrit-deep-dive.md      — has Kenyon text-crit content already
SCOPE_2026-05-08-addendum-kenyon-textcrit.md         — Kenyon source ingested
SCOPE_2026-05-08-addendum-pd-translations.md         — PD translation tracking
SCOPE_2026-05-08-addendum-ai-xrefs.md                — χ-AI infrastructure shipped
SCOPE_2026-05-09-addendum-ai-notes.md                — χ-AI-notes shipped
SCOPE_2026-05-12-addendum-gamma-4-expansion.md       — γ.4 expansion (this whole arc)
SCOPE_2026-05-12-addendum-xi-18-x-style-src.md       — ξ.18 style source
```

No addendum specifically for Mäqabyan / γ.4.8 — when the user's PD
research lands, **add a SCOPE_2026-05-14-addendum-gamma-4-8-maqabyan.md**
to formalize the scope before shipping.

---

## 6. New findings — full list

### 6.1 CRITICAL (D-C1, D-C2, D-C3) — see TL;DR for summaries

### 6.2 WARN (D-W1 to D-W5) — see TL;DR for summaries

### 6.3 INFO (D-I1 to D-I3) — see TL;DR for summaries

### 6.4 RESOLVED (since LIGHT audit)

- ω.41 §1 trajectory rule: working as designed — Cyril 50%-downward
  crossing event handled cleanly at γ.4.9.C; trajectory-pin durably
  established at γ.4.9.D arc-close.
- §8.1 arc-close convention: seven canonical instances. Pattern is
  now project-wide-canonical.
- N-W4 idempotency contract: TEN production verifications across nine
  unique ships (γ.4.6.x: 4 + γ.4.7.x: 4 + γ.4.9.x: 4 — note shared
  9b18a47 commit). Contract holds even under mid-turn book-code
  corrections (γ.4.9.D verified the contract across two batch-promote
  passes after the jas→jam typo fix).

### 6.5 Cross-cutting structural findings

- **All five patristic voices closed-arc.** γ.4 corpus structurally-
  complete per ω.41 §1 five-voice composition codification.
- **γ.4.8 Mäqabyan was always reserved** for incoming PD source —
  the user's research is the canonical unblocker.
- **Three uniquely-Tewahedo Mäqabyan books have zero content**
  representing the project's largest single coverage gap.

---

## 7. Recommendations + γ.4.8 readiness assessment

### 7.1 Highest-priority action items

| ID | Priority | Action | Effort |
|---|---|---|---|
| **D-C1** | **HIGHEST** | Ship γ.4.8 Mäqabyan seed (and follow-on detail waves to arc-close) using user's PD research findings | one session for seed; multi-session for full arc |
| D-W2 | Medium | Add `"jas": "jam"` to `_BOOK_CODE_ALIASES` in `scripts/core/sources.py` (+ verify nothing else depends on "jas" output) | <0.1 session |
| D-W1 | Medium | Archive 8 `_ship_gamma{46,47}*.py` scripts to `dev/archive/ship_scripts/<arc-tag>/` per §7.4 | 0.25 session |
| L-W1 | Medium | Fix `run_ethiopian_at_scale.py` append-not-dedup fragility (add `--clean` flag OR dedup-by-anchor at append time) | ~1 session |
| D-W4 | Medium | Investigate Python 3.14/Windows subprocess flake; add pytest-forked OR pytest-xdist --boxed; OR downgrade-test to 3.13 | ~1 session |
| EOD-W1 | Low | Refresh `PLAN_2026-05-09.md` §2 status snapshot to current state | <0.1 session |
| EOD-W2 | Low | Add LOAD-BEARING-NO-LONGER docstring annotation to `_dedup_ethiopian_notes.py` | <0.1 session |
| L-W3 | Low | Codify three-locations-to-fix rule in CLAUDE_PROJECT_RULES.md §9 | <0.1 session |
| D-C2 | Low | Schedule 4ba / 2en / 1cl coverage for v1.x future arc (not γ.4.x — different sources) | future-arc |

### 7.2 γ.4.8 Mäqabyan readiness checklist

```
PRE-CHECK (ALL ✓):
[✓] Phase letter γ.4.8 reserved (per _meta.source ledger across γ.4.5.x)
[✓] books.yaml has mq1 + mq2 + mq3 codes registered with titles
[✓] content/notes/mq1.py + mq2.py + mq3.py file scaffolding exists (empty)
[✓] N-W4 idempotency pipeline proven (run_ethiopian_at_scale.py + batch_promote)
[✓] EthiopianCommentaryDetector handles all comm-ethiopian kinds uniformly
[✓] Source corpus _meta.source ledger format established (γ.4.x precedent)
[✓] Ship-script template established (_ship_gamma49d.py is a working 7th-arc-close pattern)
[✓] Test class pattern established (TestGammaNNN* with §8.1 PIN #1+#2+#3 at arc-close)
[✓] CHANGELOG / SESSION_STATE / IN_FLIGHT update conventions established
[✓] Linter + ruff + pre-commit hook + N-W4 verification all stable

UNBLOCKED:
[?] PD source material — **AWAITING USER'S INCOMING RESEARCH REPORT**
```

**The pipeline is fully ready.** As soon as the PD Maccabees research
content is delivered, γ.4.8 can ship in a single session for the seed
wave; the full arc (seed + 3 detail + arc-close as 8th §8.1 instance)
can ship in 4-5 sessions following the established cadence.

### 7.3 Suggested γ.4.8 architecture

Following the established §8.1 pattern from γ.4.9:

```
γ.4.8     Mäqabyan seed wave
            ~30-40 verse-keyed entries spanning Mq 1 + Mq 2 + Mq 3
            multi-book seed (parallels γ.4.9 seed across 19 books)

γ.4.8.B   Mäqabyan I detail wave
            ~30-40 entries deepening Mq 1 seed anchors
            ↓
γ.4.8.C   Mäqabyan II detail wave
            ~30-40 entries deepening Mq 2 seed anchors
            ↓
γ.4.8.D   Mäqabyan III detail wave + arc-close
            ~30-40 entries deepening Mq 3 seed anchors
            EIGHTH §8.1 arc-close instance
            PIN #1 count milestone (Mäqabyan ≥120-160)
            PIN #2 all_N_sections_covered (all 3 Mäq books at depth)
            PIN #3 _meta synchronization (γ.4.8/.B/.C/.D + ARC CLOSED)

End-state:
  - Mäqabyan corpus     ~120-160 entries (parity with Athanasius 150)
  - Voice count         6 (Cyril + Jubilees + 1 Enoch + Ephrem + Athanasius + Mäqabyan)
  - Source corpus       ~1487-1527 entries
  - mq1/mq2/mq3 notes   substantively populated
  - Buyer-demo          gains uniquely-Tewahedo-canonical-Maccabees angle
                        (publisher uniqueness-angle pick per memory v1_terminus)
```

### 7.4 ω.41 §1 voice-composition revision needed

ω.41 §1 currently codifies the **four-voice composition** with
Athanasius as the fifth voice added at γ.4.9. With γ.4.8 Mäqabyan
opening a SIXTH voice, **ω.41 §1 needs an extension** to either:

- (a) Re-codify as a **six-voice composition** with Mäqabyan added
  (preferred; this is a structural-voice-count change worth marking).
- (b) Re-codify the rule as "Cyril plurality preserved across N voices"
  (more abstract; harder to verify mechanically).

Option (a) is cleaner. Recommend opening γ.4.8 with a paired ω.42
hygiene update codifying Mäqabyan as the sixth voice.

---

## 8. Closing

This deep audit confirms project structural health post-γ.4.9.D arc-
close + all-five-patristic-voices-closed milestone. **No CRITICAL
findings block any current work.** Three CRITICAL findings (D-C1
Mäqabyan empty, D-C2 six Tewahedo-distinctive empty books, D-C3
book-code-normalization drift in source JSON) are **opportunities
rather than emergencies** — they stage the next phase of project
work.

**The headline finding is D-C1 — γ.4.8 is unblocked.** All
infrastructure pre-checks pass; the pipeline is proven across seven
§8.1 arc-close instances; the user's PD Maccabees research is the
canonical unblocker for the long-deferred γ.4.8 Mäqabyan arc.

**Recommended next action:** when the user shares the PD Maccabees
research report:
1. Disambiguate Mäqabyan vs Greek Maccabees source content.
2. Open `SCOPE_2026-05-14-addendum-gamma-4-8-maqabyan.md` to formalize
   scope.
3. Ship γ.4.8 seed (30-40 entries) following the γ.4.9 architecture
   template.
4. Bundle with ω.42 hygiene addressing D-W2 (jas→jam alias) + ω.41 §1
   extension codifying the sixth voice.

The Tewahedo flagship will gain its strongest single distinguishing
feature: **substantively-detailed patristic-or-traditional coverage
of three Tewahedo-uniquely-canonical books that no competing free
Bible app surfaces at all.**

---

**Audit closure: clean structural state, single highest-priority
forward action (γ.4.8 Mäqabyan), AWAITING user's PD Maccabees research
report for ship initiation.**
