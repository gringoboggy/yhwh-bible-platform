# CLAUDE_PROJECT_RULES — extracted finished-arc history

This file preserves the finished-arc narrative, frozen statistics, per-instance
tallies, and verbose dated history that was slimmed out of
`dev/CLAUDE_PROJECT_RULES.md` (Task 1.3 of the 2026-05-29 mint-cleanup). The
*rules* themselves remain in the live RULES file; what lives here is the
historical detail behind them, preserved verbatim behind a pointer rather than
lost. Each section is headed by the § / topic it came from.

---

## §1 — Patristic-source voice composition (full statistical history)

> **Durable invariant retained in RULES §1:** the corpus is a Cyril-led
> patristic chorus plus the three uniquely-Tewahedo-canonical voices (1 Enoch /
> Jubilees / Meqabyan) and the Syriac + apostolic-bridge supplements; Cyril
> remains plurality-leader, guarded by
> `test_cyril_remains_plurality_leader_at_arc_close` (asserts Cyril > Athanasius
> AND Cyril > Jubilees — sufficient under all plausible future expansion).

### Four-voice composition (codified at ω.41 hygiene bundle, 2026-05-13, per AUDIT_2026-05-13-EOD EOD-W3)

The γ.4 patristic source corpus (`content/sources/ethiopian_commentaries.json`,
then 1,065 entries) is **Cyril-led** by design. The four-voice composition was:

- **Cyril of Alexandria** (48.5%, 516 entries — Alexandrian-Coptic patriarchal
  commentary; the Tewahedo Christological doctrinal centerpiece via the Mark →
  Athanasius → Frumentius apostolic lineage).
- **Jubilees (Ethiopian tradition)** (18.8%, 200 entries — uniquely-Tewahedo-
  canonical OT pseudepigraphical witness).
- **1 Enoch (Ethiopian tradition)** (18.0%, 192 entries — uniquely-Tewahedo-
  canonical OT pseudepigraphical witness).
- **Ephrem the Syrian** (14.7%, 157 entries — Syriac patristic voice; the
  East-Syrian-Alexandrian bridge).

**Cyril's plurality is intentional, not accidental.** Cyril is the 24th Patriarch
of the See of Mark, standing in direct apostolic succession to John Mark (Coptic
founder) and to Athanasius (Tewahedo founder Frumentius's consecrator c. 330).
His commentary on the four canonical Gospels is the doctrinal heart of the
Tewahedo flagship. The corpus is therefore "Cyrillian-led patristic chorus +
three Tewahedo-canonical-OT + one Syriac supplement" rather than an even
four-voice quartet.

**If Cyril's share crosses 50% (single-father-majority threshold)** in future
γ.4.7.x detail-wave expansion, that is acceptable per the rule — but flag it
explicitly in the relevant SESSION_STATE headline so the trajectory is visible.
Balance with Ephrem or pseudepigraphical expansion if a publisher
uniqueness-angle pick (per memory `v1_terminus`) calls for it.

### Five-voice extension (ω.41 §1.B / γ.4.9.D 2026-05-13)

Extended at γ.4.9.D arc-close, 2026-05-13: the corpus opened a FIFTH voice with
γ.4.9 Athanasius of Alexandria (the Tewahedo apostolic-bridge: 20th Patriarch of
the See of Mark + Frumentius's consecrator c. 330 + author of Festal Letter 39
codifying the 27-book NT canon). The five-voice composition was:

- Cyril of Alexandria — 48.86% (668 entries; 4 canonical-Gospel arcs)
- Jubilees (Ethiopian tradition) — 14.63% (200 entries)
- 1 Enoch (Ethiopian tradition) — 14.05% (192 entries)
- Ephrem the Syrian — 11.49% (157 entries)
- Athanasius of Alexandria — 10.97% (150 entries; γ.4.9.x arc closed)

At γ.4.9.C Cyril's share crossed DOWNWARD below 50% (51.5% → 49.96%) as the
natural consequence of two consecutive Athanasius detail-waves. Cyril remained
plurality-leader at 3.34× the next single-father. This threshold-crossing was
flagged in SESSION_STATE per the trajectory rule above. The
Cyril-remains-plurality-leader durable safeguard pin in
`TestGamma49DAthanasiusArcClose::test_cyril_remains_plurality_leader_at_arc_close`
guards this invariant against future voice-mixing.

### Six-voice extension (ω.42 §1.C / γ.4.8 2026-05-14)

Extended at ω.42 hygiene bundle paired with γ.4.8 ship, 2026-05-14: the corpus
opened a SIXTH voice with γ.4.8 Mäṣḥafä Mäqabyan — the THIRD
uniquely-Tewahedo-canonical text alongside Mäṣḥafä Hēnok (1 Enoch) and Mäṣḥafä
Kufāle (Jubilees). γ.4.8 had been DEFERRED across the entire γ.4 corpus history
pending PD source acquisition; the 2026-05-14 user-contributed CC0 1.0 English
translation (archive.org/details/three-books-of-meqabyan-cc0-translation) is the
canonical unblocker.

The six-voice composition was:

- **Cyril of Alexandria** — 47.48% (668 entries) — Alexandrian-Coptic
  patriarchal commentary; the Tewahedo Christological doctrinal centerpiece via
  the Mark → Athanasius → Frumentius apostolic lineage.
- **Jubilees / Mäṣḥafä Kufāle (Ethiopian tradition)** — 14.22% (200 entries) —
  uniquely-Tewahedo-canonical OT pseudepigraphical witness.
- **1 Enoch / Mäṣḥafä Hēnok (Ethiopian tradition)** — 13.65% (192 entries) —
  uniquely-Tewahedo-canonical OT pseudepigraphical witness.
- **Ephrem the Syrian** — 11.16% (157 entries) — Syriac patristic voice; the
  East-Syrian-Alexandrian bridge.
- **Athanasius of Alexandria** — 10.66% (150 entries) — Tewahedo apostolic-
  bridge: 20th Patriarch of See of Mark + Frumentius's consecrator.
- **Mäqabyan / Mäṣḥafä Mäqabyan (Ethiopian tradition)** — 2.84% (40 entries;
  γ.4.8 seed; opens-the-sixth-voice) — uniquely-Tewahedo-canonical broader-canon
  Maccabees-named-but-distinct text (Maqabis-of-Benjamin + Maqabis-of-Moab +
  angelological/resurrection-doctrine cycles).

**Tewahedo-distinctive-canonical block:** the three uniquely-Tewahedo canonical
texts (Mäṣḥafä Hēnok + Mäṣḥafä Kufāle + Mäqabyan) jointly held 432/1407 = 30.71%
of the patristic-and-canonical corpus — the FIRST TIME the three together
constituted a numerically significant block. **Patristic-anchor majority** (Cyril
+ Ephrem + Athanasius) held at 975/1407 = 69.30%. **Cyril plurality** remained
intact at 3.34× next-single-father (668 vs 200), guarded durably by the
`test_cyril_remains_plurality_leader_at_arc_close` pin (which asserts Cyril >
Athanasius AND Cyril > Jubilees — sufficient under all plausible future
expansion).

### Update — ω.43 / γ.4.8.E arc-close 2026-05-14

The γ.4.8 Mäqabyan arc is now CLOSED at the EIGHTH §8.1 instance, with the
five-wave detail-wave family (γ.4.8 seed + γ.4.8.B Mäqabyan-I detail + γ.4.8.C
Mäqabyan-II detail + γ.4.8.D Mäqabyan-III detail + γ.4.8.E arc-close) all
shipped. **Mäqabyan reached 200 entries — PARITY WITH JUBILEES at 200; TIE for
2ND-PLACE in the voice-ranking** (Cyril 668 / Jubilees 200 / Meqabyan 200 / 1
Enoch 192 / Ephrem 157 / Athanasius 150). The estimated end-state of ~120-160
entries was EXCEEDED by ~40-80 entries — the broader scope (per memory
`feedback_extensive_answers`) achieved PARITY rather than mere benchmark-match.
All three Mäqabyan books at 100% chapter coverage: mq1 36/36 + mq2 21/21 + mq3
10/10 = 67/67 chapters. The Mäqabyan trilogy is the FIRST γ.4 arc to achieve 100%
chapter-coverage across its entire scope. **Tewahedo-distinctive-canonical block
(Mäṣḥafä Hēnok + Mäṣḥafä Kufāle + Mäqabyan) at 37.78%** (592/1567) — strongest
position in γ.4 corpus history; directly supports v1.1 publisher-led
uniqueness-angle pick per memory `project_v1_terminus`. Cyril remained
plurality-leader at 42.63% (sub-50% trajectory continues; 3.34×
next-single-father preserved). With γ.4.8.E ALL SIX γ.4 PATRISTIC/CANONICAL
VOICES are at substantively-closed-arc depth.

---

## §8.1 — Arc-close pin convention: existing instances

> **Durable convention retained in RULES §8.1:** at the closing wave of a
> multi-wave content arc, the closing test class adds three pins — a `_meta`
> synchronization pin (regex word-boundary per sub-phase), an absolute-count
> milestone pin (NEVER a share-pin), and an `all_N_sections_covered`
> exhaustiveness pin. Anti-pattern: a share-pin in the arc-close class.

Existing instances (the convention was codified after the third instance of the
pattern shipped — γ.4.4.E Mäṣḥafä Hēnok arc-close + γ.4.5.E Mäṣḥafä Kufāle
arc-close, both 2026-05-12, plus the share-pin → count-milestone repair pattern
in memory `feedback_share_pin_pattern.md`):

- **γ.4.4.E (Mäṣḥafä Hēnok arc)** — `TestGamma44EEpistleOfEnochWave` in
  `tests/test_ethiopian_gamma4.py` at the closing of the six-section 1 Enoch arc;
  arc-close pin `test_all_six_mashafa_henok_sections_covered`.
- **γ.4.5.E (Mäṣḥafä Kufāle arc)** —
  `TestGamma45EJubileesJosephExodusFinaleWave` at the closing of the Jubilees
  four-major-section arc; arc-close pin
  `test_all_six_jubilees_sections_substantively_covered` plus the
  `test_jubilees_milestone_count_at_arc_close` count milestone.
- **ω.37 (W10 closure)** — `TestGamma4MetaPhasesCoverage` extends the `_meta`
  synchronization pin pattern across every previously-shipped sub-phase
  (γ.4.4.B/C/D/E + γ.4.5/B/C/D/E), so future drift gets caught at commit time.

---

## §9 — χ-cluster corpus-growth: existing instances

> **Durable recipe retained in RULES §9** (the "Add a new corpus-growth phase"
> pipeline + the BAKE-AND-PROVE gate + the mandatory nested-`<a>` check).

Existing instances of the χ-cluster pattern:

- χ.6 (CrossRefDetector + run_xref_at_scale.py): +6,127 notes
- χ.6+ HebrewWord (HebrewWordDetector + run_hebrew_at_scale.py): +8,412 notes
- Together: 1,381 → 15,925 in one session via this pattern.
- Torrey's New Topical Textbook (`TorreyTopicalDetector` +
  `run_torrey_at_scale.py`): +~21,800 notes (2026-05-26).

The nested-`<a>` gate was skipped after the Nave's/Easton's/Torrey ingests →
**14,568** nested `<a>` accumulated undetected (found + `--fix`-repaired
2026-05-26). That instance is the origin of the "MANDATORY — epubcheck does NOT
replace it" emphasis retained in the live recipe.

---

## §9 — ω.35-B god-module extraction: existing instances (B.1–B.7)

> **Durable recipe retained in RULES §9** (the "Extract a topic cluster from a
> god-module into scripts/api/<topic>.py" template + its lazy-import pattern +
> the `TestOmega35BN<Topic>Extraction` uniform test shape).

The ω.35-B file-split track shipped eight instances; each slice reduced web.py by
70–1200 lines; cumulative 40.5% reduction (7670 → 4564 lines) with **zero**
behavior change at any HTTP boundary:

- B.1 snapshots
- B.2 scenarios
- B.3a covers-mutations
- B.3b sources-cache
- B.4 customize
- B.5 editions
- B.6 exports/build
- B.7 preflight/audit/help/multipart

After B.7 closed the file split for web.py, the pattern is durable enough to
apply elsewhere (`scripts/build_edition.py`, `scripts/prospect.py`, etc.); future
invocations can label themselves with their own phase letter (the pattern is
generic, not ω-only).

---

## §9 — Δ-family index-backed optimization: full detail (Δ.0–Δ.9)

> **Durable recipe retained in RULES §9** (the "Build an index-backed alternative
> for an expensive file-walk operation (the Δ-family pattern)" template: build
> the equivalent under a new name + a non-negotiable byte-identical equivalence
> test; land all five infra unblockers BEFORE flipping any wire; never delete the
> file-walk reference; no `force=True` in equivalence tests — use `invalidate() +
> rebuild()`; per-worker SQLite storage).

Codified after the ω.34/Δ-family arc shipped Δ.0 through Δ.9 (2026-05-10 →
2026-05-11). The pattern recurred in two distinct operations (`compute_matrix`
via Δ.4 and `dashboard_stats` via Δ.5) and the *infrastructure* slices (Δ.0, Δ.6,
Δ.7, Δ.8, Δ.9) were collectively load-bearing — the wire-flip attempts kept
reverting until all five unblockers were in place.

**The full nine-step shape (recipe form is in the live RULES; this is the
detail):**

1. Build the equivalent function under a new name (`<name>_indexed()` alongside
   `<name>()`), plus an equivalence test pinning byte-identical output.
2. The equivalence test is non-negotiable. Δ.4's test caught the index path
   diverging on disabled-kind filtering, empty-edition handling, and chapter-key
   dtype (int vs str).
3. A rebuild lock under `content/.locks/` — file-based
   (`<feature>_rebuild.lock`) with `_acquire_rebuild_lock(*, timeout: float =
   30.0)`. Pin TimeoutError-on-exceed with a short timeout in tests.
4. TTL fingerprint cache — `_compute_fingerprint()` stats every `notes/*.py` (87
   files); memoize keyed on a monotonic clock with a configurable refresh
   interval (default 1s prod, 0s tests). Without this, every wire-flip attempt
   intermittently fails xdist as workers race to rebuild.
5. `notes_io` invalidation hook — wire a callback in `notes_io.atomic_write` that
   calls the index's `invalidate()`. Without it, edits during a test run produce
   stale index reads and false-failing equivalence assertions.
6. Per-worker index storage — `corpus_index_<worker_id>.sqlite` (worker_id =
   `gw0`, `gw1`, … for xdist; `_serial_` for non-xdist). Prevents the
   cross-worker write race that defeated wire-flip attempts #1-4.
7. Server warmup + session-scoped test fixture — production warms at server boot;
   tests use a session-scoped `corpus_index_warmup` fixture in
   `tests/conftest.py`. Without warmup, cold tests random-fail.
8. Wire-flip in a separate phase — the public function gets a one-line change to
   call the indexed variant; the file-walk implementation stays under its private
   name as the equivalence-test reference. **Do not delete the file-walk path.**
9. Test convention: no `force=True` in equivalence tests — on Windows under
   xdist that races with other workers' cached connections (PermissionError on
   `sqlite` unlink). Use `invalidate() + rebuild()`.

**Why this needs all 5 infrastructure slices** (each unblocker eliminates one
failure mode; skipping any makes the wire-flip flaky):

| Skip                      | Failure mode                            |
|---------------------------|-----------------------------------------|
| (3) rebuild lock          | concurrent writes corrupt the index     |
| (4) TTL fingerprint cache | 87 stat() calls per query → xdist storm |
| (5) notes_io hook         | edits during test → stale index reads   |
| (6) per-worker storage    | cross-worker write race → SQLite lock   |
| (7) warmup fixture        | cold tests hit first-rebuild race       |

A wire-flip attempted before all five land will hit one of these and revert. The
Δ.4.1 wire-flip succeeded on attempt #5 specifically because Δ.6/Δ.7/Δ.8/Δ.9 (the
four infra slices) + the equivalence-test convention (no force=True) all landed
first. Treat new index-backed optimizations the same way: **land every unblocker
before flipping any wire.**

**Existing instances:**

- Δ.4 + Δ.4.1: file-walk `compute_matrix` → SQL-indexed `compute_matrix_indexed`.
  Empirical: file-walk ~3.2s on 51K corpus, indexed ~263ms cold (~12× speedup);
  both sub-millisecond after the parent-level `@lru_cache(maxsize=1)` serves.
- Δ.5 + Δ.5.1: same shape for `dashboard_stats`. TTL=1s caches fingerprints
  between calls; same per-worker SQLite path convention reused.

**Anti-patterns:**

- Wire-flipping before all five infrastructure unblockers exist (you'll revert).
- Deleting the file-walk reference implementation after the wire flip (you lose
  the equivalence-test anchor — needed for any future change to the index
  schema).
- Using `force=True` in equivalence tests (Windows xdist race; use `invalidate()
  + rebuild()` instead).
- Sharing one SQLite path across xdist workers (cross-worker write race; always
  per-worker).

---

## §9 — Four-tier defensive system: existing instances

> **Durable recipe retained in RULES §9** (the four-tier shape: T4 behavioral/
> protocol → T1 per-action audit → T2 state-of-record → T3 continuous automated
> check; the coverage-matrix discipline that forces explicit thinking about gaps;
> the "if no failure mode escapes a single layer, DON'T tier" guard).

Two existing instances (for reference):

- **§15 — Backend drift detection.** Built ω.0.4. Catches the "code shipped but
  not journaled" failure class. Primary tiers: T4 §13/§14 protocols, T1 §12
  footnote audit, T2 IN_FLIGHT.md, T3 lint_rules.py.
- **ω.0.6 — Frontend crash defense.** Built one turn after the meta-pattern
  crystallized. Catches null-pointer / unexpected-exception / API-failure /
  unguarded-DOM-query failure classes. Primary tiers: T4 (graceful degradation
  discipline), T1 (input validation), T2 (safeFetch wrapper), T3 (browser DOM
  helpers + Tier 4 backstop).

A third instance applying this template would confirm it as a durable pattern;
until then it's two examples and a recipe.

---

## §9 — Aggregate-API / feature-endpoint / injectable-callable: existing instances

> **Durable recipes retained in RULES §9** ("compose, don't recompute"; "pure
> function + thin route adapter"; the injectable-callable variant for
> orchestration).

- **Compose-don't-recompute** codified after the second instance (ψ.3 corpus
  progress widget composing `api_attribution_audit`; the first was the preflight
  aggregator composing `run_all` + 7 other sub-checks).
- **Pure-function + thin-route-adapter** codified after the sixth instance (ν.5
  customize preview, ψ.5 sample-chapter export, ω.0.2 console scaffold, ω.1
  backup restore, ψ.6 ops dashboard, ω.2 build-all).
- **Injectable-callable variant** existing instances: `apply_plan(plan,
  target_file=...)` from ω.0.2; `api_build_all_editions(*, build_one)` from ω.2.
  Pattern instances of this exact shape: 2 of 6 (the others use the basic shape
  because their work is light enough that real calls are fine in tests). ω.2's
  orchestration is exercised in 4 tests, none of which run a real subprocess EPUB
  build.

---

## §4 — Checkpoint-save first instances

> **Durable rule retained in RULES §4:** a mid-task checkpoint save is a valid
> pattern; at checkpoint time IN_FLIGHT stays `active` with progress documented,
> SESSION_STATE reflects the save happened during the in-flight task, and the
> linter's `inflight_freshness` showing `active … (fresh)` is correct, not a bug.

First instance: v28a-64-full was issued mid-ψ.3 (corpus widget). Second:
v28a-65-full was issued mid-ν.5 customize wiring. Both captured the partial state
with IN_FLIGHT correctly active. (Build-tag scheme since retired — see RULES §5.)

---

## §10 — Scope-guardrail history (pre-free-public-pivot strike-throughs)

> **Durable stance retained in RULES §10:** re-framed to free-public present
> tense — no retail / sales / ISBN / ONIX / POD / ledger surfaces; multi-format
> export survives only as a FREE download option; "buyer" now means the "builder"
> who makes their own free edition.

The original §10 carried the evolution as strike-throughs, preserved here:

- ~~Not a multi-language UI.~~ Lifted 2026-05-09 (PLAN θ.5). The editorial
  apparatus baseline is English; localized UI shells (Spanish, Portuguese,
  French, German) were brought in scope for the LONG TRACK once a real buyer ask
  materialized. Bible *content* in many languages remains the whole point;
  *interface* in many languages joins it as a long-tail roadmap item.
- ~~Not a print-on-demand pipeline.~~ **Partially lifted 2026-05-12** — focus
  remained digital retail, but ψ.22 (multi-format export: PDF / MOBI / HTML /
  TXT) became an open MEDIUM item in PLAN §7. Print PDF for direct buyer
  consumption (sample chapter PDFs in ε.7 press kits; full-edition PDF in ψ.22)
  was in scope. Full POD (KDP paperback / IngramSpark) stayed deferred — the
  print-cover-customize wiring existed in `content/customization.yaml` but the
  build pipeline integration was beyond v1.x. **(Superseded by the 2026-05-14
  free-public pivot — see RULES §1: no retail / sales / ISBN / POD.)**

---

## §13 / §14 — Original drift-event narratives (real instances)

> **Durable protocols retained in RULES §13 (topic-shift) and §14
> (state-uncertainty / resume-audit).** The originating real instances:

### §13 topic-shift — the 2026-05-07 ν.6 drift event

ν.6 chapter labels shipped fully (code, tests, UI) but never landed in the
addenda; the user caught it manually by auditing test counts ("you claimed 262
tests, actual is 269").

Bad (what happened):
> Me: [shipped ν.6 chapter labels via 7 tests + UI but didn't update CHANGELOG]
> User: "Should the book ToC have a square pill or no pill?"
> Me: "Great question, here's my opinion on pills... [pivots]"
> [ν.6 ships orphaned; user catches it 3 turns later]

Good (what would have prevented it):
> Me: [shipped ν.6 — but before any further response, runs the linter, sees
> CHANGELOG/SESSION_STATE haven't caught up, says:] "Before answering: I just
> shipped ν.6 chapter labels. Let me log that first, then I'll address pills."

### §14 state-uncertainty — the 2026-05-07 ν.5 post-compaction instance

After a context compaction, Claude was about to start ν.5 (change-impact
preview) from scratch. The IN_FLIGHT.md file showed unexpected content not
written that turn — "ν.5 change-impact preview shipped 2026-05-07 in
PUBLISHER_HTML; CUSTOMIZE_HTML wiring is the natural follow-up." Treating this as
a §14 trigger, the audit (`grep -n "ν\.5\|preview_impact" scripts/web.py` showed
extensive existing implementation; tests had 7 new tests in the `# ---------- Phase
ν.5 :` block; CHANGELOG had a full ν.5 entry) found the correct task was the
customize-wiring follow-up, not a from-scratch build. The audit caught it before
any duplicated work.

---

## §15 — Original drift event + the build-out of all four tiers

> **Durable chain-of-command matrix retained in RULES §15.**

The original drift event (early 2026-05-07): ν.6 chapter labels shipped (code,
tests, UI all complete) but CHANGELOG was never updated. The user caught it
manually with a test-count audit ("you claimed 262 tests, actual is 269"). At
that point:

- Tier 4 had failed (didn't audit before pivoting topics)
- Tier 1 didn't exist yet
- Tier 2 didn't exist yet
- Tier 3's `untracked_phases` check didn't exist yet

So the user was the de-facto Tier 5. After the catch, all four tiers were built
in one push (ω.0.4). Now if Tier 4 slips again, Tier 1 would catch the test-count
mismatch before claiming ship; if Tier 1 slips, Tier 2's stale-marker check
surfaces in the next linter run; if Tier 2 slips because the marker was never
flipped, Tier 3's `check_untracked_phases` flags the phase mention without a
CHANGELOG entry.

The git-truth drift class (claimed-saved-but-uncommitted) was added with the §12
5-point audit after the 2026-05-26 Torrey near-miss: the prior session reported
the work "committed and backed up" while HEAD didn't reflect it and no bundle
existed, and all four other pre-summary audit points passed. Tier 1's git-truth
check (pre-summary audit point 5) catches it before the user reads the claim; the
§14 resume audit (Tier 4) is the cross-session backstop.

---

## §12 — Pre-summary audit drift-catch origin

The user caught Claude on audit point (1) — test-count reconcile — once, and that
was enough; the other four pre-summary points are preventive layers. Point (5),
commit/backup truth, was added after the 2026-05-26 Torrey near-miss (21,762
verified notes left uncommitted on disk across a /clear despite a "committed +
backed up" claim — the resume audit's other four steps don't look at git).

---

## SESSION_PLAYBOOK §4 — `tests/test_scripts.py` runnability history (extracted 2026-06-21 rules-consolidation Phase B / B10)

> **Durable line retained in PLAYBOOK §4:** the genuinely-slow lane is real edition builds
> (`test_byte_stability_gate.py`); `test_matrix_psi35.py` + `test_web_filesplit.py` are the
> slowest non-build files, all `slow`-tagged → `pytest -m "not slow"` skips them; run one file
> at a time under RAM pressure. Exact second-counts deliberately NOT pinned — they rot (memory
> `feedback_slow_test_files`: re-measure before quoting).

`tests/test_scripts.py` became runnable again 2026-05-24 (was ~976 tests, ~2.9 min green). Both
blockers fixed: **D.hang** (9 socket tests → `ThreadingHTTPServer` + `test_ops` mocks
`api_preflight`) and **D.slow** (a session-autouse conftest fixture, `_stub_exports_epubcheck`,
stubs the real epubcheck/Java run over the populated `exports/` dir — minutes per call — while
leaving `TestEpubcheckWrapper`'s tmp-dir calls real). The old "NEVER run the full
test_scripts.py" rule was retired then. `test_web_filesplit.py` (~88 tests) and
`test_matrix_psi35.py` (~39) — the same fixture removed the worst cost (the
`api_preflight()`→epubcheck-over-`exports/` path; test_web_filesplit alone made 15 such calls) —
later grew into the 2 slowest non-build files (re-measured 2026-05-31; the earlier "~11 s/~12 s"
and the "23 min" myth were both stale). Both `slow`-tagged (mint-7 E2).

## §0 env-health — plugin-roster "16-official" arithmetic slip (extracted 2026-06-21 Phase B / B11)

The §0 plugin/MCP sanity step once listed "16 official" plugins. That was an arithmetic slip: the
pre-expansion 15 = 14 official + `gitkraken-hooks@gitkraken`; the 2026-06-10 user-approved
expansion brought the live `claude plugin list` to **30** across 3 marketplaces. The live RULES §0
now states the durable invariant ("trust the SessionStart ENV-HEALTH hook's live
`claude plugin list`") rather than a hard-coded 30-name roster.
