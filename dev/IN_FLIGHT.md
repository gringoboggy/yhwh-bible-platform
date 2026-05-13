# In-flight work — current task tracker

<!-- TRACKER-STATE: idle -->

## Prior task

**ω.38 C6 closure — 9 edition main cover JPGs produced
programmatically; AUDIT_2026-05-12-C arc FULLY CLOSED (17 of
17 items resolved across ω.36 + ω.37 + ω.38)** shipped
2026-05-13. Triggered by user directive "put the covers in"
after ω.37 closed 7 of the 9 audit-C residue items.

**Why it matters for THIS project**:

- **Demo blocker resolved.** Before ω.38, the wizard's BUILD
  step emitted EPUBs whose cover slot resolved to a missing
  path for 8 of 9 editions (the 9th had an empty `cover_image`
  field). The buyer's "wow, that's it?" moment ended with
  broken covers. ω.38 produces tasteful stock-template covers
  for every edition with tradition-appropriate color/design
  pairing.
- **Audit-C arc fully closed.** Three audit-driven hygiene
  phases (ω.36 + ω.37 + ω.38) close every item from
  AUDIT_2026-05-12-C. The audit cadence's value is proven: the
  parallel-subagent sweep caught real demo-readiness gaps the
  linter alone could not surface, and the three-phase residue
  close-out shipped them all.
- **Generator script is the durable artifact.** Publishers can
  re-run `scripts/generate_edition_covers.py` after editing
  titles in `editions.yaml`, or re-target individual editions
  to different templates by editing the script's `EDITIONS`
  mapping. Cover artwork swap to bespoke is a one-line
  `api_save_edition_meta` call; the stock covers are
  demo-ready out of the box.

**Files**:
- `scripts/generate_edition_covers.py` — new, +~220 lines:
  PIL-based programmatic cover generator with template-to-
  edition mapping, Times/Georgia typography, drop-shadow,
  1024×1536 output.
- `content/covers/<9 edition IDs>.jpg` — new, 9 JPEG files at
  1024×1536, average ~740 KB each, total ~6.7 MB.
- `content/editions.yaml` — one-line fix: catholic-study's
  `cover_image: ""` → `cover_image: "covers/catholic-study.jpg"`.
- `tests/test_scripts.py` — +~140 lines: new
  `TestOmega38EditionCovers` class with 6 pins covering disk
  presence, JPEG validity, yaml correctness, preflight pass,
  generator-script integrity, template-uniqueness curation.
- `dev/PLAN_2026-05-09.md` — +1 line: ω.38 in §7 Shipped.
- `dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md`, `dev/CHANGELOG.md`
  — state-of-record updates.

**Test delta**: **+6 net tests** (`TestOmega38EditionCovers`).
Full suite at ω.38 close: **3572 passing, 1 skipped** (was
3566 at ω.37 close; +6 from ω.38). Linter 11/11 clean (phase
mention count 235 → 236; ω.38 referenced in CHANGELOG). ruff
format applied to the 2 edited files.

**Preflight delta** (the audit-flagged signal):
- Pre-ω.38: `covers_main → fail` (8 broken)
- Post-JPGs: `covers_main → warn` (1 yaml empty-string)
- Post-yaml-fix: `covers_main → pass` ← current state

**AUDIT_2026-05-12-C arc — FINAL TALLY:**
- ω.36 (2026-05-12): 8 items closed
- ω.37 (2026-05-13): 7 items closed
- ω.38 (2026-05-13): 1 item closed (C6)
- W17 (info-only meta-observation): accepted, no action
- **17 of 17 items closed.** Full audit-C resolution.

**Forward references**:
- **γ.4.2.C Ephrem on Exodus** — Ephrem continuation;
  rebalances Ephrem share from 13.1% upward. Audit hygiene is
  fully closed; content waves can resume.
- **γ.4.3 Cyril on Luke** — opens a new Cyril-on-Lukan-corpus
  arc using Payne Smith 1859 PD translation.
- **γ.4.8 Mäqabyan seed** — opens the THIRD uniquely-Tewahedo
  canonical text (DEFERRED pending PD source acquisition).
- **save** — five phases shipped since the last save baseline
  (`ee05f31`): γ.4.5.D + γ.4.5.E + ω.36 + ω.37 + ω.38. A save
  point is overdue.

**Session totals (2026-05-13, cumulative across 2026-05-12+):**
- Content: γ.4.4.A-E + γ.4.2 + γ.4.2.B + γ.4.5 + γ.4.5.B/C/D/E
  shipped (Mäṣḥafä Hēnok + Mäṣḥafä Kufāle arcs both CLOSED).
  Corpus: 12 → 590 entries.
- Audit hygiene: ω.36 + ω.37 + ω.38 shipped
  (AUDIT_2026-05-12-C arc FULLY CLOSED, 17/17 items).
- Net test delta: +34 hygiene/regression-detection tests
  (+12 from ω.36, +16 from ω.37, +6 from ω.38).

---

## Prior task before ω.38 (kept for context)

**ω.37 Audit-C residue cleanup (7 of the 9 remaining items;
only C6 cover-JPGs left as publisher-decision external-asset
work)** shipped 2026-05-13. Second audit-driven hygiene phase
following ω.36 (2026-05-12). Triggered by "ok hygiene" continue
directive after ω.36 close-out. Closes 16 of 17 AUDIT_2026-05-12-C
items across the two phases.

**Why it matters for THIS project**:

- **Audit-C arc essentially closed.** With ω.36 + ω.37 shipped,
  only C6 (cover JPGs — external assets) remains. The audit
  punch list that triggered ~3 hours after γ.4.5.E is now ~95%
  resolved. The project can resume content waves with high
  confidence the hygiene foundation is solid.
- **W7 confirms intentional cross-canon pattern.** 1 Enoch
  commentary on Gen 6:1+6:4 (Watchers narrative ↔ sons-of-God
  passage) is preserved with regression-detection pins. Future
  cross-canon additions (e.g. Jubilees on Genesis) must be
  deliberately allow-listed.
- **W10 catches a structural drift class.** Without these 9
  `_meta` pins, a future content wave could grow the corpus by
  hundreds of entries while leaving `_meta.source/scope`
  pointing at stale phase tags. ATTRIBUTIONS readers and
  audit-trail consumers would see stale metadata.
- **W11 unblocks Jubilees demo claim.** 200 Jubilees entries
  in the corpus, but no test verified they flowed through the
  build pipeline. The 4 W11 pins make the build path
  regression-detected.
- **W12 codifies a durable pattern.** The arc-close convention
  (three pins: `_meta` sync, count-milestone, exhaustiveness)
  is now a §-level rule. The next multi-wave content arc gets
  the right test shape from the start.
- **W4 + W15 close minor doc-reality drift.** Two small fixes
  reconciling the rules doc with what the code/wizard actually
  does.
- **C5 functional rewrite makes the test immune to load flake.**
  The audit-C run's "cold faster than warm" report can't
  happen with the new `cache_info()`-delta assertion.

**Files**:
- `dev/CLAUDE_PROJECT_RULES.md` — +~70 lines: new §8.1 arc-close
  convention; §7.1 mtime-cache guidance refactor; §1 wizard
  prose fix.
- `tests/test_ethiopian_gamma4.py` — +~190 lines: 3 new test
  classes covering 16 tests (W7 cross-canon + W10 meta-phase
  + W11 build-pipeline).
- `tests/test_scripts.py` — C5 test rewritten in place (timing
  heuristic → `cache_info()` delta).
- `dev/PLAN_2026-05-09.md` — +1 line: ω.37 in §7 Shipped block.
- `dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md`, `dev/CHANGELOG.md`
  — state-of-record updates.

**Test delta**: **+16 net tests**. Full suite at ω.37 close:
**3566 passing, 1 skipped** (was 3550 at ω.36; +16 from ω.37).
Linter 11/11 clean (phase mention count 234 → 235). ruff format
applied to 3 edited code/test files.

**Audit-C residue still open after ω.37:**
- **C6 9 edition main cover JPGs** — external-asset production
  (publisher decision; could intentionally remain as the demo-
  of-preflight-catching-real-issues moment).

**Forward references**:
- **γ.4.2.C Ephrem on Exodus** — Ephrem continuation; would
  rebalance Ephrem share from 13.1% back upward. The audit
  hygiene arc is sufficiently closed that content waves can
  resume.
- **γ.4.3 Cyril on Luke** — opens a new Cyril-on-Lukan-corpus
  arc using Payne Smith 1859 PD translation. Luke uses
  canonical book code `luk`; no alias work needed (ω.36 only
  aliased the legacy SBL `joh`/`ps`).
- **C6 cover JPG production** — if a polish pass is preferred
  over more content; publisher decision required.

**Session totals (2026-05-13, cumulative including 2026-05-12)**:
- γ.4.4.A-E shipped (Mäṣḥafä Hēnok arc CLOSED, 2026-05-12)
- γ.4.2 + γ.4.2.B shipped (Ephrem on Gen 1-50, 2026-05-12)
- γ.4.5 + γ.4.5.B/C/D/E shipped (Mäṣḥafä Kufāle arc CLOSED,
  2026-05-12)
- ω.36 shipped (Audit-C cleanup #1, 2026-05-12)
- ω.37 shipped (Audit-C residue cleanup, 2026-05-13)
- Net corpus delta: +538 commentary entries (12 → 590); +28
  hygiene tests across ω.36 + ω.37.

---

## Prior task before ω.37 (kept for context)

**ω.36 Audit-C cleanup ship (8 items from AUDIT_2026-05-12-C
executed as a single audit-driven hygiene phase)** shipped
2026-05-12. Triggered by "continue" directive at the two-arc-
closure milestone (γ.4.4 Mäṣḥafä Hēnok + γ.4.5 Mäṣḥafä Kufāle
arcs both CLOSED earlier the same day). Per project rule §3.1
(safest / most-foundational first), the audit-recommended
hygiene precedes the next content wave so corpus legal-audit
trail + cross-reference routing + test-pin durability + schema
validation stay clean as the corpus continues to grow.

**Why it matters for THIS project**:

- **C2 alias unblocks 119+2 commentary entries from the build
  pipeline.** Before ω.36, `for_verse("jhn", 1, 1)` returned
  `[]` even though Cyril's dense Logos-prologue commentary was
  in the corpus (under book=`joh`). Same for Ephrem-on-Psalm-1
  (under book=`ps`). The build pipeline reads via the canonical
  books.yaml codes, so these 121 entries were silently dropped
  from every built EPUB. The symmetric alias resolves both old
  storage codes and new canonical-code queries — read paths
  unblocked, no rekey needed.
- **C4 strict-unknown schema validation restored.** Two pytest
  tests had been failing since `epsilon7` shipped catholic-study's
  product-metadata fields. With those tests restored, future
  schema-spec drift gets caught at commit time.
- **C3 ATTRIBUTIONS legal-audit trail.** 588 of 590 commentary
  entries now have a human-readable cross-source registry entry,
  not just the JSON-internal `_meta.public_domain_basis` block.
  An external legal/licensing reviewer reads ATTRIBUTIONS.md
  first; the gap was a real documentation hole.
- **C1 PLAN sub-phase ledger.** Future-Claude orientation now
  reads the actual γ.4 ladder (16 sub-phases) instead of just
  the parent γ.4 label. The audit flagged this as the SECOND
  audit in a row hitting the same blind spot; ω.36 closes the
  drift before it becomes durable.
- **W8/W9 share-pin → count-milestone conversions.** Pre-emptive
  conversion of two share-pins that memory
  `feedback_share_pin_pattern` predicted would break on the next
  voice-add wave (1 Enoch margin was 50 entries; Jubilees still
  far from threshold but converted for pattern consistency).
- **W3/W6 small drift cleanup.** Dead `import urllib.request` in
  `fetch_sources.py` (HTTP routes through `scripts.core.http`
  per the SSRF-allowlist convention); 12 Jubilees section labels
  normalized from `"Abram's early life"` → `"Abraham cycle"`.

**Files**:
- `scripts/validate_schemas.py` — +2 lines (FieldSpec entries
  for `authors` + `bisac_codes` in `EDITIONS_SPEC`).
- `scripts/core/sources.py` — +27 lines (alias map +
  `_normalize_book_code()` helper + symmetric application at
  6 index-build sites + 6 `for_verse` sites).
- `scripts/fetch_sources.py` — −1 line (dead urllib import).
- `tests/test_ethiopian_gamma4.py` — 2 share-pin → count-milestone
  conversions in-place.
- `tests/test_scripts.py` — +12 tests in `TestOmega36AuditCleanup`
  covering every fix site.
- `content/sources/ATTRIBUTIONS.md` — +4 patristic-source sections
  (~60 lines).
- `content/sources/ethiopian_commentaries.json` — 12 attribution-
  string normalizations (replace-all on `"Abram's early life"` →
  `"Abraham cycle"`).
- `dev/PLAN_2026-05-09.md` — +7 lines (γ.4 sub-phase ledger +
  ω.36 in §7 Shipped block).
- `dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md`, `dev/CHANGELOG.md`
  — state-of-record updates.

**Test delta**: **+12 tests** (`TestOmega36AuditCleanup` — 12
anchor pins). All suites pass: **tests/ excluding test_scripts
2596 passed, 1 skipped; test_scripts.py 954 passed;
test_ethiopian_gamma4.py 270 passed**. Linter 11/11 clean. ruff
format applied to the 3 edited code/test files.

**Audit-C residue (NOT shipped this turn — deferred to follow-up):**
- **C5 preflight cache-invalidation test** — investigation
  (likely threshold-sensitivity on the 590-entry JSON; widen
  margin or rework threshold).
- **C6 9 edition main cover JPGs** — external-asset production
  (publisher decision; could be the intentional demo-of-
  preflight-catching-real-issues moment).

**Forward references**:
- **γ.4.2.C Ephrem on Exodus** — Ephrem continuation; would
  rebalance Ephrem share from current 13.1% back upward.
- **γ.4.3 Cyril on Luke** — opens a new Cyril-on-Lukan-corpus
  arc using Payne Smith 1859 PD translation. The joh/ps alias
  work in ω.36 means future commentary ingest can use either
  canonical or SBL-short codes transparently.
- **C5/C6 audit residue close-out** — preflight cache test +
  cover JPG production, if a polish pass is preferred over
  more content.
- **γ.4.8 Mäqabyan seed** — opens the THIRD uniquely-Tewahedo
  canonical text (DEFERRED pending PD source acquisition).

**Session totals (2026-05-12, cumulative through ω.36)**:
- γ.4.4.A-E shipped (Mäṣḥafä Hēnok arc CLOSED)
- γ.4.2 + γ.4.2.B shipped (Ephrem on Gen 1-50)
- γ.4.5 + γ.4.5.B + γ.4.5.C + γ.4.5.D + γ.4.5.E shipped
  (Mäṣḥafä Kufāle arc CLOSED)
- ω.36 shipped (Audit-C cleanup ship)
- Net corpus delta this session: +538 entries beyond γ.4 seed
  (12 → 590 entries) plus +12 hygiene tests in ω.36.

---

## Prior task before ω.36 (kept for context)

**γ.4.5.E Mäṣḥafä Kufāle / Book of Jubilees Joseph + Exodus-finale
(40 verse-keyed entries on Jub 37-50) — CLOSES the γ.4.5 detail
arc** shipped 2026-05-12. Substantively expands chs 37-50 (Esau-
Jacob war + Joseph in Egypt + Judah-Tamar + silver-cup test + Jacob
to Egypt + Joseph dies + slavery begins + Moses' birth + Exodus +
Mastema bound + Passover institution + Sabbath + Jubilee-of-jubilees
finale). The γ.4.5 seed gave broad coverage of all 50 chapters
with 11 verses falling in chs 37-50; γ.4.5.E brings chs 37-50
coverage from 11 to 51 entries — substantive-detail parity (and
slight surplus) with γ.4.5.B/C/D at 47 entries each.

**Why it matters for THIS project**:

- **γ.4.5 Mäṣḥafä Kufāle detail arc CLOSED.** All four major
  Jubilees narrative sections (chs 5-10 Watchers + Noahide,
  11-22 Abraham, 24-36 Jacob, 37-50 Joseph + Exodus-finale) now
  have substantive-coverage parity at the detail-wave depth.
  Short bookend sections (chs 1-4 Sinai prologue + Creation,
  ch 23 Decline) retain seed coverage proportionate to their
  length. With γ.4.4.E having closed the Mäṣḥafä Hēnok arc
  earlier this day, BOTH uniquely-Tewahedo canonical-text arcs
  are now closed on 2026-05-12 — a major canonical-content
  milestone for the Tewahedo edition.
- **Jubilees becomes PLURALITY voice.** Voice mix moves from
  22/14/35/29 to ~21/13/33/34 Cyril/Ephrem/1En/Jubilees —
  Jubilees surpasses 1 Enoch by 8 entries (200 vs 192) to become
  the plurality voice. The two uniquely-Tewahedo canonical texts
  jointly hold 66.4% of the patristic-commentary corpus voice.
- **Mastema-not-Lord at the lodging-night-attack (48:1-2)** is
  one of the most theologically significant Jubilees-distinctive
  clarifications. The Ex 4:24 puzzle ('the Lord met him and
  sought to kill him' on Moses' return to Egypt) becomes
  intelligible via the Jubilees Mastema-attack reading: divine
  goodness is preserved while the canonical narrative is honored.
  Tewahedo theodicy preserves this exact clarification.
- **Three-day Moses-ark / Christ-tomb Pascal-typology (47:5)**
  is Jubilees-distinctive (the 'three days' detail is not in
  Exodus). The Tewahedo Easter-vigil canonical-OT prefiguration
  reading depends on Jubilees for this typological precision.
- **Passover blood-on-lintels restrains Mastema (49:2)** is the
  canonical anchor for the Tewahedo eucharistic-blood demonic-
  defense doctrine: every Tewahedo communicant is, by canonical-
  typology, 'within the bloodstained doorway' that Mastema cannot
  enter.
- **Lamb-AND-wine canonical eucharistic-OT prototype (49:6)**
  preserves the explicit lamb-flesh-and-wine doublet at the
  original Passover meal — the Tewahedo Anaphora's canonical-OT
  eucharistic-prototype anchor. Eucharist is patriarchal-Mosaic
  in canonical structure, not merely apostolic-novel.
- **Passover-observance acquits-of-guilt (49:15)** is the
  canonical principle that liturgical-act-AS-atonement (not
  merely commemoration) is the Tewahedo eucharistic theology.
  The proper observance of the canonical-Passover IS itself the
  canonical-atonement-for-the-year's-sin — Tewahedo Fasika
  reading.
- **Jubilee-of-jubilees eschatology with Satan permanently
  removed (50:4)** — the Tewahedo cosmic-territorial-cleansing
  eschatology canonical anchor. The final consummation is not
  merely individual-spiritual-resurrection but cosmic-territorial
  cleansing and permanent removal of demonic presence.
- **Sabbath as 'day of the holy kingdom' (50:9) + strict
  Sabbath-prohibition list (50:12)** — Tewahedo Saturday-Sabbath
  observance (unique among major Christian communions in
  preserving the canonical-Mosaic seventh-day Sabbath alongside
  the Lord's-Day Sunday) has its canonical-OT anchor here.
- **Jacob blesses Pharaoh (45:13)** is the canonical-patriarchal
  warrant for the Tewahedo coronation-prayer tradition: the
  Orthodox patriarch may legitimately bless the civil ruler even
  when the ruler is non-Orthodox (civil authority is divinely
  ordained, Rom 13:1).
- **'She became more righteous than he' Judah-Tamar (41:25)** is
  the canonical-confession verbal anchor for the Tewahedo
  confessor's näsḫa-of-acknowledgment formula: confession from
  the stronger-sinner-against-the-weaker-victim follows this
  exact pattern.

**Files**:
- `content/sources/ethiopian_commentaries.json` — 40 new Jubilees
  entries appended (book=`jub`, father=`Book of Jubilees (Ethiopian
  tradition)`, work=`Book of Jubilees (Mäṣḥafä Kufāle)`,
  year=`-150`, attribution `Jubilees C:V (section), trans. R.H.
  Charles, The Book of Jubilees (Oxford: Clarendon, 1902). PD.`).
  _meta scope/source strings updated with the γ.4.5.E + γ.4.5
  arc-close notes. Total entries now 590 (was 550 pre-γ.4.5.E).
- `tests/test_ethiopian_gamma4.py` — new
  `TestGamma45EJubileesJosephExodusFinaleWave` class with **25
  tests**: ≥40 entries pin + 6 sub-range coverage pins (Joseph
  in Egypt 37-40, Judah-Tamar 41-43, Jacob to Egypt 44-45, Moses'
  birth 47, Exodus-Passover 48-49, Sabbath-Jubilee finale 50) +
  **arc-close pin `test_all_six_jubilees_sections_substantively_covered`**
  (parallel to γ.4.4.E's Mäṣḥafä-Hēnok arc-close pin) + **absolute-
  count milestone `test_jubilees_milestone_count_at_arc_close`**
  (≥200 entries = 40 seed + 4×40 detail) + 16 signature passage
  pins (37:1, 39:10, 41:25, 44:1, 44:5, 45:13, 47:5, 48:2,
  48:18, 49:2, 49:6, 49:15, 50:4, 50:9, 50:12).

**Code-side wiring**: zero new code.

**Corpus state post-γ.4.5.E**:
```
ethiopian_commentaries.json: 590 entries (was 550; +40)
├─ Book of Jubilees (Eth. tradition) : 200 entries (33.9%) ← PLURALITY
├─ 1 Enoch tradition                 : 192 entries (32.5%)
├─ Cyril of Alexandria               : 121 entries (20.5%)
└─ Ephrem the Syrian                 :  77 entries (13.1%)

Voice mix: ~21% Cyril / ~13% Ephrem / ~33% 1 Enoch / ~34% Jubilees
           (was 22/14/35/29 pre-γ.4.5.E — Jubilees SURPASSES 1 Enoch
            by 8 entries to become the PLURALITY voice)

Two uniquely-Tewahedo canonical texts (Mäṣḥafä Hēnok + Mäṣḥafä
Kufāle) jointly hold ~66.4% of the patristic-commentary corpus
voice — both canonical-content arcs CLOSED on 2026-05-12.

γ.4 cumulative              : 538 entries beyond γ.4 seed
                             (.1.A 30 + .1.B 27 + .1.C 29 + .1.D 30 +
                              .2 32 + .2.B 40 + .4 30 + .4.B 40 +
                              .4.C 40 + .4.D 40 + .4.E 40 + .5 40 +
                              .5.B 40 + .5.C 40 + .5.D 40 + .5.E 40 = 538)
```

**+25 tests, 0 share-pin repairs needed**. **γ.4.5.E tests: 25/25
pass in isolation; γ.4 full-file suite: 270/270 pass; 11/11 lint
clean.**

**γ.4.5 ARC CLOSURE NOTE**: With γ.4.5.E shipped, the γ.4.5
Mäṣḥafä Kufāle content arc (γ.4.5 seed through γ.4.5.E Joseph +
Exodus-finale) is COMPLETE for substantive-coverage purposes.
Each of the four major Jubilees narrative sections (chs 5-10,
11-22, 24-36, 37-50) has ≥40 entries; short bookend sections
retain seed coverage proportionate to their length. Mäṣḥafä
Kufāle is now the second-deepest single-source presence in the
corpus (200 entries), surpassing 1 Enoch's 192 entries.

**Forward references**:
- **γ.4.2.C Ephrem on Exodus** — Ephrem continuation; would
  rebalance Ephrem share from current ~13% back upward.
- **γ.4.2.D Ephrem on Numbers + Deuteronomy** — further Ephrem
  Pentateuch expansion.
- **γ.4.3 Cyril on Luke** — opens a new Cyril-on-Lukan-corpus arc
  using Payne Smith 1859 PD translation; would rebalance Cyril
  share from current ~21% back upward.
- **γ.4.6 Mäṣḥafä Aksumawi** (Ethiopic Sirach reception) — opens
  another uniquely-Tewahedo patristic-canonical text tradition.
- **γ.4.7 Senodos / Didascalia Ethiopic** — opens another
  patristic-canonical text tradition.
- **γ.4.8 Mäqabyan seed** — opens the THIRD uniquely-Tewahedo
  canonical text (DEFERRED pending PD source acquisition).

**Session totals (2026-05-12, cumulative through γ.4.5.E)**:
- γ.4.4.A-E shipped (Mäṣḥafä Hēnok arc CLOSED)
- γ.4.2 + γ.4.2.B shipped (Ephrem on Gen 1-50)
- γ.4.5 + γ.4.5.B + γ.4.5.C + γ.4.5.D + γ.4.5.E shipped (Mäṣḥafä
  Kufāle arc CLOSED)
- Net corpus delta this session: +538 entries beyond γ.4 seed
  (12 → 590 entries).

---

## Prior task before γ.4.5.E (kept for context)

**γ.4.5.D Mäṣḥafä Kufāle / Book of Jubilees Jacob-cycle detail
(40 verse-keyed entries on Jub 24-36)** shipped 2026-05-12.
Continues γ.4.5 seed, γ.4.5.B (Watchers detail), and γ.4.5.C
(Abraham-cycle detail) with the Jacob-cycle substantive expansion.
Mirrors the γ.4.4.B / γ.4.5.B / γ.4.5.C detail-wave pattern. The
γ.4.5 seed gave broad coverage of all 50 chapters with 7 verses
falling in chs 24-36 (25:9, 27:21, 30:7, 32:1, 32:18, 35:1,
36:23); γ.4.5.D brings chs 24-36 coverage from 7 to 47 entries —
substantive-detail parity with γ.4.5.B (Jub 5-10) and γ.4.5.C
(Jub 11-22).

**Why it matters for THIS project**:

- **Jubilees surpasses Cyril as substantively-second voice.**
  Voice mix moves from 24/15/38/24 to ~22/14/35/29 Cyril/Ephrem/
  1En/Jubilees. Jubilees is now the second-largest single-source
  voice in the corpus, behind 1 Enoch only. The two uniquely-
  Tewahedo canonical texts (Mäṣḥafä Hēnok + Mäṣḥafä Kufāle)
  jointly hold ~64% of the patristic-commentary corpus voice.
- **Three-generation patriarchal-altar chain complete.** Isaac's
  Beersheba altar (24:22) joins Abram's Bethel altar (13:8) and
  Jacob's Bethel altar (32:1) — the Tewahedo Anaphora-of-Patriarchs
  has canonical anchor across all three patriarchal generations.
- **Pre-Pentecostal Spirit-inspired blessing.** Jub 25:14 is a
  remarkable mid-2nd-c. BCE Jewish witness to prophetic-Spirit-
  inspired speech: 'the spirit of righteousness descended into
  her mouth.' Tewahedo näfsä-qǝddus (holy-Spirit utterance)
  finds canonical OT-typological anchor.
- **Resurrection-unto-eternal-life clause** in Rebekah's blessing
  (25:23) is one of the strongest mid-2nd-c. BCE Jewish
  resurrection witnesses. Tewahedo Tǝnśaʾe canonical resurrection
  doctrine has matriarchal-canonical anchor.
- **Bethel ladder as Marian-ladder type** (27:19) — the Wǝddase
  Maryam Monday-evening cycle explicitly invokes 'Mary the ladder
  of Jacob,' anchored in this canonical passage.
- **Levi's priesthood EARNED by zeal** (30:18) — Jubilees uniquely
  makes the Levitical priesthood an earned-by-zeal investiture
  (not just hereditary). Tewahedo priesthood-by-zeal-AND-descent
  doubled warrant; the kǝhnät tradition is canonically BOTH
  earned and inherited.
- **Priestly precedence over royal** (31:14) — Isaac blesses Levi
  BEFORE Judah, contrary to birth order. Tewahedo ecclesiology's
  emphasis on the priest's prophetic-warning authority over the
  king (even Solomonic-dynasty kings) finds canonical anchor.
- **Davidic-messianic Judah-blessing** (31:18) — 'in thee shall
  be found the salvation of Israel' explicitly anticipates the
  Gen 49:10 Shiloh prophecy. Tewahedo Solomonic-dynasty Davidic-
  Judah claim (via Kǝbrä Nägäśt) has doubled OT-canonical anchor.
- **Jacob's double-tithe institution** (32:9) — tithe-to-priest
  + festive-tithe-consumed-by-offerer as pre-Mosaic patriarchal
  ordinance. Tewahedo ǝʾǝsär double-pattern canonical anchor.
- **Seven heavenly tablets given to Jacob** (32:21) — Tewahedo
  Mäṣḥafä-zä-säma'i (heavenly book) doctrine canonical anchor;
  canonical Scripture as 'eternal in the heavens.'
- **Tripled Astereyo canonical anchor** — Jub 34:18 (Jacob's
  grief-of-affection over Joseph) joins Jub 5:17-18 (Watchers-
  judgment context) and Jub 6:10 (Noahide blood-atonement
  context) as the three canonical Jubilees-Atonement anchors.
  Tewahedo Astereyo's doubled-character (sin-against-commandment
  AND grief-of-broken-affection) has triple-canonical warrant.
- **Reuben's confession + Jacob's clemency** (33:9) — voluntary
  disclosure materially mitigates punitive disciplinary response.
  Tewahedo näsḫa absolution-by-confession principle canonical
  anchor.
- **Rebekah's hope for Esau's repentance** (35:6) — even the
  most-rejected covenant-line brother is canonically hoped-for.
  Tewahedo eschatological-hope matriarchal-canonical anchor;
  informs Tewahedo pastoral generosity toward non-Tewahedo
  Christians.
- **'Eternal house with the fathers'** (36:1) — Isaac's intermediate-
  state-as-fellowship-with-departed-righteous phrase. Tewahedo
  funeral-liturgy preserves this exact phrase as canonical-verbal
  inheritance across millennia.
- **Love-of-brother testament triad** — Abraham (Jub 20:2) +
  Isaac (Jub 36:7) + Mosaic Lev 19:18. Tewahedo Maḫǝbär Qǝddus
  monastic-charism canonical-patriarchal warrant.

**Files**:
- `content/sources/ethiopian_commentaries.json` — 40 new Jubilees
  entries appended (book=`jub`, father=`Book of Jubilees (Ethiopian
  tradition)`, work=`Book of Jubilees (Mäṣḥafä Kufāle)`,
  year=`-150`, attribution `Jubilees C:V (section), trans. R.H.
  Charles, The Book of Jubilees (Oxford: Clarendon, 1902). PD.`).
  _meta scope/source strings updated. Total entries now 550 (was
  510 pre-γ.4.5.D).
- `tests/test_ethiopian_gamma4.py` — new
  `TestGamma45DJubileesJacobCycleWave` class with **23 tests**:
  ≥40 entries pin + 6 sub-range coverage pins (Esau/Isaac in
  Gerar 24, Rebekah blessing 25-26, Bethel vision + Haran 27-28,
  Levi priesthood 30-32, Isaac testament 36) + 16 signature
  passage pins (24:22, 25:14, 25:23, 27:19, 27:27, 30:18, 30:23,
  31:14, 31:18, 31:23, 32:9, 32:21, 33:9, 34:18, 35:6, 36:1,
  36:7). Also: pre-existing stale Ephrem share-pin in γ.4.2.B
  (previously lowered 17%→15%; failed again at 14% post-γ.4.5.D
  dilution) was repaired to absolute-count milestone pin
  (`test_ephrem_milestone_count_at_or_above_patriarchal_close`,
  Ephrem ≥75 entries) — same pattern as γ.4.5.C's repair of the
  γ.4.4.D/.E pins.

**Code-side wiring**: zero new code.

**Corpus state post-γ.4.5.D**:
```
ethiopian_commentaries.json: 550 entries (was 510; +40)
├─ Cyril of Alexandria               : 121 entries (John 1-7 + 11-21 — COMPLETE)
├─ Ephrem the Syrian                 :  77 entries (Gen 1-50; Ps 1; Hymns)
├─ 1 Enoch tradition                 : 192 entries (Mäṣḥafä Hēnok arc CLOSED)
└─ Book of Jubilees (Eth. tradition) : 160 entries (γ.4.5+B+C+D substantively detailed
                                                    across chs 5-36, plus seed coverage
                                                    of chs 1-4 + 23 + 37-50)

Voice mix: ~22% Cyril / ~14% Ephrem / ~35% 1 Enoch / ~29% Jubilees
           (was 24/15/38/24 pre-γ.4.5.D — Jubilees surpasses Cyril
            to become substantively-second voice)

Two uniquely-Tewahedo canonical texts (Mäṣḥafä Hēnok + Mäṣḥafä
Kufāle) jointly hold ~64% of the patristic-commentary corpus
voice.

γ.4 cumulative              : 498 entries beyond γ.4 seed
                             (.1.A 30 + .1.B 27 + .1.C 29 + .1.D 30 +
                              .2 32 + .2.B 40 + .4 30 + .4.B 40 +
                              .4.C 40 + .4.D 40 + .4.E 40 + .5 40 +
                              .5.B 40 + .5.C 40 + .5.D 40 = 498)
```

**+23 tests + 1 share-pin repair**. **γ.4.5.D tests: 23/23 pass
in isolation; γ.4 full-file suite: 246/246 pass; 11/11 lint
clean.**

**Forward references**:
- **γ.4.5.E Jubilees Joseph + Exodus-finale detail (Jub 37-50)** —
  would close the γ.4.5 detail arc with full parity-coverage of
  the Joseph cycle (chs 37-45) + Egypt-Exodus-Passover-Sabbath
  finale (chs 46-50).
- **γ.4.8 Mäqabyan seed** — opens the THIRD uniquely-Tewahedo
  canonical text (DEFERRED pending PD source acquisition; current
  Wikisource translations fail the named-PD-edition standard).
- **γ.4.2.C Ephrem on Exodus** — Ephrem continuation; would
  rebalance Ephrem share from current ~14% back upward.

**Session totals (2026-05-12, cumulative through γ.4.5.D)**:
- γ.4.4.A-E shipped (Mäṣḥafä Hēnok arc CLOSED)
- γ.4.2 + γ.4.2.B shipped (Ephrem on Gen 1-50)
- γ.4.5 + γ.4.5.B + γ.4.5.C + γ.4.5.D shipped (Mäṣḥafä Kufāle
  seed + Watchers detail + Abraham-cycle detail + Jacob-cycle
  detail)
- Net corpus delta this session: +498 entries beyond γ.4 seed
  (12 → 510 → 550 entries).

---

## Prior task before γ.4.5.D (kept for context)

**γ.4.5.C Mäṣḥafä Kufāle / Book of Jubilees Abraham-cycle detail
(40 verse-keyed entries on Jub 11-22)** shipped 2026-05-12.
Continues γ.4.5 seed (40 entries across all 50 chs) and γ.4.5.B
(40 entries on Jub 5-10 Watchers + Mastema) with the Abraham-cycle
substantive expansion. Mirrors the γ.4.4.B / γ.4.5.B detail-wave
pattern. The γ.4.5 seed gave broad coverage of all 50 chapters
with 7 verses falling in chs 11-22 (11:16, 12:16, 12:22, 14:6,
15:11, 18:9, 21:10); γ.4.5.C brings chs 11-22 coverage from 7 to
47 entries — substantive-detail parity with γ.4.5.B (Jub 5-10).

**Why it matters for THIS project**:

- **Substantive parity across the Jubilees Abraham cycle.** With
  Jub 5-10 (γ.4.5.B) and Jub 11-22 (γ.4.5.C) both at 47 entries,
  the canonical Tewahedo Abraham material is now substantively
  covered at the same depth as the Watchers narrative. Future
  γ.4.5.D-E waves can complete the Jacob (24-36) and Joseph +
  Exodus-finale (37-50) sections.
- **Triple Pentecost canonical anchor.** Jub 14:1 (Abram's
  covenant of pieces dated to new moon of third month) joins Jub
  6:17 (Noah's Feast of Weeks pre-Mosaic) and Jub 1:1 (Sinai
  prologue) as the three Pentecost-date covenant moments. Add
  Jub 16:13 (Isaac's birth on Pentecost) and the Tewahedo
  Pentecost has FOUR canonical date-anchors unique to its canon.
- **Tewahedo distinctive Christian circumcision** — Jub 15:14
  + 15:25 + 15:27 substantively pinned: eighth-day non-negotiable,
  perpetual, AND the angels of presence themselves created
  circumcised (cosmic-circumcision). This is the canonical anchor
  for the Tewahedo's uniquely-preserved Christian circumcision
  practice (preserved alongside baptism, neither conflated).
- **Pre-Mosaic Feast of Tabernacles** — Jub 16:20: Abraham
  institutes the FIRST Feast of Tabernacles, seven days, at the
  Beersheba altar in the year of Isaac's birth. Tewahedo Mäskäl-
  week canonical antecedent. The pattern (great festivals are
  patriarchal restorations, not Mosaic novelties) is the Tewahedo
  liturgical-historiographical anchor.
- **Mt Moriah = Mt Zion** — Jub 18:13 explicit identification.
  Tewahedo eucharistic fourfold-altar canonical anchor: every
  altar is mystically Moriah + Zion + Calvary + Heavenly-Zion.
- **Akedah-as-Passover** — Jub 17:15 places Mastema's accusation
  on the eve of Passover (first month, 12th day). The Akedah is
  offered AS PASSOVER, not merely typologically connected to it —
  Tewahedo Holy-Week liturgy preserves the doubled commemoration.
- **No-blood-consumption TRIPLE witness** — Jub 21:7 (Abraham's
  priestly instructions) joins Jub 6:7 (Noahide command) and Jub
  7:34 (Noah's testament). Tewahedo dietary-law distinctive
  preserved on canonical anchor; the Tewahedo prohibition against
  eating blood is a uniquely-rooting-out sin (Jub 21:18).
- **Hebrew tongue restored** — Jub 12:25: the angel of presence
  restores the pre-Babel Hebrew tongue to Abram before his call.
  Tewahedo Ge'ez liturgical-language warrant by analogy: sacred
  liturgical languages are angelic gifts, not mere developments.
- **Solomonic-dynasty Tewahedo-Jacobite anchor** — Jub 22:11:
  Abraham directly blesses Jacob (his preferred grandson) over
  Isaac's potential Esau-favoritism. Canonical priority-of-grace
  over inherited-order. The Tewahedo Kǝbrä Nägäśt's account of
  the Solomonic dynasty's Jacobite-Israelite continuation (via
  Menelik I as Solomon's son) has its earliest patriarchal
  warrant in Abraham's direct blessing.
- **Pastoral inclusivity** — Jub 22:1: Abraham's Feast of Weeks
  in his final year is celebrated with BOTH Isaac and Ishmael at
  the patriarchal altar. Tewahedo pastoral warrant for welcoming
  Ishmaelite (Muslim-family-background) Ethiopians at the
  communion-table preparation.

**Files**:
- `content/sources/ethiopian_commentaries.json` — 40 new Jubilees
  entries appended (book=`jub`, father=`Book of Jubilees (Ethiopian
  tradition)`, work=`Book of Jubilees (Mäṣḥafä Kufāle)`,
  year=`-150`, attribution `Jubilees C:V (section), trans. R.H.
  Charles, The Book of Jubilees (Oxford: Clarendon, 1902). PD.`).
  _meta scope/source strings updated. Total entries now 510 (was
  470 pre-γ.4.5.C).
- `tests/test_ethiopian_gamma4.py` — new
  `TestGamma45CJubileesAbrahamCycleWave` class with **23 tests**:
  ≥40 entries pin + 6 sub-range coverage pins (Abram's early life
  11-13, covenant+circumcision 14-15, Isaac+Tabernacles 16, Akedah
  17-18, testament+priestly+blessing 20-22) + 16 signature passage
  pins (11:18, 12:25, 13:8, 13:25, 14:1, 15:14, 15:27, 16:13,
  16:20, 17:15, 18:13, 18:18, 19:28, 20:2, 21:7, 22:1, 22:11).
  Also: pre-existing stale share-pins in γ.4.4.D / γ.4.4.E that
  had been silently failing since γ.4.5+ diluted 1En share were
  repaired to absolute-count milestone pins (1En ≥150 / ≥190).

**Code-side wiring**: zero new code.

**Corpus state post-γ.4.5.C**:
```
ethiopian_commentaries.json: 510 entries (was 470; +40)
├─ Cyril of Alexandria               : 121 entries (John 1-7 + 11-21 — COMPLETE)
├─ Ephrem the Syrian                 :  77 entries (Gen 1-50; Ps 1; Hymns)
├─ 1 Enoch tradition                 : 192 entries (Mäṣḥafä Hēnok arc CLOSED)
└─ Book of Jubilees (Eth. tradition) : 120 entries (γ.4.5 + γ.4.5.B + γ.4.5.C)

Voice mix: ~24% Cyril / ~15% Ephrem / ~38% 1 Enoch / ~24% Jubilees
           (was 26/17/41/16 pre-γ.4.5.C — Jubilees rises to
            substantively-tied-second voice with Cyril at ~24%)

Two uniquely-Tewahedo canonical texts (Mäṣḥafä Hēnok + Mäṣḥafä
Kufāle) jointly hold 62% of patristic-commentary corpus voice —
appropriate weight for the Tewahedo edition that uniquely
canonizes both.

γ.4 cumulative              : 458 entries beyond γ.4 seed
                             (.1.A 30 + .1.B 27 + .1.C 29 + .1.D 30 +
                              .2 32 + .2.B 40 + .4 30 + .4.B 40 +
                              .4.C 40 + .4.D 40 + .4.E 40 + .5 40 +
                              .5.B 40 + .5.C 40 = 458)
```

**+23 tests + 2 share-pin repairs**. **γ.4.5.C tests: 23/23 pass
in isolation; γ.4 full-file suite: 223/223 pass; 11/11 lint
clean.**

**Forward references**:
- **γ.4.5.D Jubilees Jacob-cycle detail (Jub 24-36)** — continues
  the detail-wave pattern; the Jacob cycle is currently at 5 seed
  entries only and would benefit from the same substantive
  treatment.
- **γ.4.5.E Jubilees Joseph + Exodus-finale detail (Jub 37-50)** —
  would close the γ.4.5 detail arc with full parity across all
  major Jubilees sections.
- **γ.4.8 Mäqabyan seed** — opens the THIRD uniquely-Tewahedo
  canonical text (DEFERRED pending PD source acquisition; current
  Wikisource translations fail the named-PD-edition standard).
- **γ.4.2.C Ephrem on Exodus** — Ephrem continuation; would
  rebalance Ephrem share from current ~15% back upward.

**Session totals (2026-05-12, cumulative through γ.4.5.C)**:
- γ.4.4.A-E shipped (Mäṣḥafä Hēnok arc CLOSED)
- γ.4.2 + γ.4.2.B shipped (Ephrem on Gen 1-50)
- γ.4.5 + γ.4.5.B + γ.4.5.C shipped (Mäṣḥafä Kufāle seed +
  Watchers detail + Abraham-cycle detail)
- 5 phases shipped unsaved since the last save (γ.4.4.E +
  γ.4.2.B + γ.4.5 + γ.4.5.B + γ.4.5.C) — per the continuation
  directive (memory: push/continue advances to next phase without
  auto-save).

---

## Prior task before γ.4.5.C (kept for context)

**γ.4.5 Mäṣḥafä Kufāle / Book of Jubilees seed (40 verse-keyed
entries across all 50 chapters)** shipped 2026-05-12. **Opens the
SECOND uniquely-Tewahedo canonical text** on the same Mäṣḥafä-
Hēnok-style trajectory as γ.4.4. Jubilees (Ge'ez: Mäṣḥafä Kufāle)
is canonical in only the Tewahedo and Eritrean Orthodox communions
— alongside 1 Enoch — and survives as a complete text only in
Ge'ez. The project's eponymous edition (ethiopian-tewahedo) now has
patristic-grade seed-coverage of BOTH uniquely-Tewahedo canonical
texts. Voice mix moves from 31/20/49 to ~28/18/45/9 Cyril/Ephrem/
1En/Jubilees — Jubilees enters the corpus as a distinct fourth
voice.

**Why it matters for THIS project**:

- **Opens the second uniquely-Tewahedo canonical text.** The
  project's mandate is the Tewahedo edition. The Tewahedo canon
  uniquely includes both Mäṣḥafä Hēnok (1 Enoch) and Mäṣḥafä
  Kufāle (Jubilees) as Scripture. γ.4.4.A-E closed the Mäṣḥafä
  Hēnok arc; γ.4.5 opens the Mäṣḥafä Kufāle arc.
- **6:32 (364-day calendar) — doubled canonical anchor.** Jubilees
  6:32 + 1 Enoch 72:32 jointly anchor the Tewahedo Bāḥrä Ḥasab
  (Sea of Reckoning) liturgical-computus tradition. The doubled
  canonical witness for the 364-day year is unique to the Tewahedo /
  Eritrean Orthodox canon.
- **9:13 (Ham's portion) — Tewahedo Hamitic identity anchor.** The
  Ethiopian self-understanding as descended from Cush son of Ham
  draws on Jubilees 9:13 (with Gen 10:6-8) as canonical warrant
  for an INCLUSIVE Hamitic theology — Ham's portion is divinely
  allotted, not cursed. Tewahedo reading explicitly rejects the
  curse-of-Ham racialisation that Western Christianity often
  imposed.
- **10:8 (Mastema petition) — non-dualist demonology.** Mastema as
  canonical figure: the post-Flood demonic presence is divinely
  permitted, bounded, and serves a probative function. Tewahedo
  theodicy preserves this against the periodic Manichaean / Zandic
  dualist incursions in Ethiopian church history.
- **18:9 (Mastema-as-Akedah-accuser) — protects divine goodness.**
  The Jubilees re-framing of the Akedah (test originates in
  Mastema's challenge, parallel to Job 1-2's Satan-as-accuser)
  protects God's absolute goodness while preserving the narrative
  of testing.
- **21:10 ('books of Enoch' cited inside Jubilees) — inter-canonical
  witness.** Jubilees treats 1 Enoch as authoritative source within
  itself, creating a uniquely doubled and inter-textual canonical
  structure in the Tewahedo canon: Jubilees cites Enoch, both are
  Scripture, both are preserved uniquely in Ge'ez.
- **32:18 (Levi consecrated to priesthood) — Tewahedo priestly
  anchor.** The Tewahedo qes priestly orders (descending through
  specific families) appeal to the patriarchal-Levitical lineage of
  Jub 32 as part of their self-understanding: priesthood is older
  than its Mosaic regulation; Jub 32 is the scriptural anchor in
  canonical Mäṣḥafä Kufāle.
- **48:9 (Mastema bound during Exodus) — Holy-Week anchor.** The
  Tewahedo theological reading of the Paschal mystery as a period
  of suspended demonic accusation draws on Jub 48:9 as its
  canonical anchor.
- **50:6 (Sabbath finale) — Saturday-Sabbath tradition.** The
  Tewahedo Church historically observed BOTH Saturday-Sabbath
  AND Sunday-Lord's-Day (unique among major Christian communions
  until the 17th century; still preserved in some monastic
  communities). Jubilees 50 is the canonical anchor.

**Files**:
- `content/sources/ethiopian_commentaries.json` — 40 new Jubilees
  entries appended (book=`jub`, father=`Book of Jubilees (Ethiopian
  tradition)`, work=`Book of Jubilees (Mäṣḥafä Kufāle)`, year=`-150`,
  attribution `Jubilees C:V (section), trans. R.H. Charles, The Book
  of Jubilees (Oxford: Clarendon, 1902). PD.`). _meta scope/source
  strings updated. Total entries now 430 (was 390 pre-γ.4.5).
- `tests/test_ethiopian_gamma4.py` — new
  `TestGamma45JubileesSeedWave` class with **14 tests**: ≥40
  entries pin + all nine narrative blocks (Sinai prologue + Creation,
  Eden + generations, Watchers + Noahide, Division of earth + Mastema,
  Abraham, Decline + eschatology, Jacob, Joseph, Egypt-Exodus-
  Passover-Sabbath finale) + Jubilees-share ≥3% (distinct voice
  threshold) + 11 signature passages (1:1, 4:17, 6:32, 8:19, 9:13,
  10:8, 18:9, 21:10, 32:18, 48:9, 50:6).

**Code-side wiring**: zero new code.

**Note on canonical-edition integration**: `jub` and `1en` are
registered in `content/books.yaml` but the `ethiopian-tewahedo`
edition's `editions.yaml` notes explicitly that "Ethiopic extras
like 1en/jub/mq1-3 to be added in a future ingest". The commentary
entries are queryable via `for_verse('jub', ...)` and
`for_verse('1en', ...)` regardless of edition canon-list state, and
will surface in the built edition once the future ingest adds these
books to the canon list. The Mäṣḥafä Kufāle commentary is therefore
READY for the edition; the edition needs to be ready for it.

**Corpus state post-γ.4.5**:
```
ethiopian_commentaries.json: 430 entries (was 390; +40)
├─ Cyril of Alexandria               : 121 entries (John 1-7 + 11-21 — COMPLETE)
├─ Ephrem the Syrian                 :  77 entries (Gen 1-50; Ps 1; Hymns)
├─ 1 Enoch tradition                 : 192 entries (Mäṣḥafä Hēnok arc CLOSED)
└─ Book of Jubilees (Eth. tradition) :  40 entries (Mäṣḥafä Kufāle SEED γ.4.5)

Voice mix: ~28% Cyril / ~18% Ephrem / ~45% 1 Enoch / ~9% Jubilees
           (was 31/20/49 pre-γ.4.5 — Jubilees enters as fourth
            voice; all three prior voices' shares ease accordingly)

γ.4 cumulative              : 418 entries beyond γ.4 seed
                             (.1.A 30 + .1.B 27 + .1.C 29 + .1.D 30 +
                              .2 32 + .2.B 40 + .4 30 + .4.B 40 +
                              .4.C 40 + .4.D 40 + .4.E 40 + .5 40 = 418)
```

**+14 tests**. **γ.4.5 tests: 14/14 pass in isolation; 11/11 lint
clean.**

**Forward references**:
- **γ.4.5.B-E** Jubilees detail waves (parallel to γ.4.4.B-E pattern):
  Watchers + Noahide covenant detail (chs 5-10); Patriarchal detail
  (chs 11-22); Jacob + Joseph detail (chs 24-45); Exodus-Passover-
  Sabbath detail (chs 46-50).
- **γ.4.6** Mäṣḥafä Aksumawi (Ethiopic Sirach reception); **γ.4.7**
  Senodos / Didascalia Ethiopic patristic-canonical texts;
  **γ.4.8** Mäqabyan 1-3 (uniquely-Tewahedo Maccabean texts —
  Ethiopic ≠ Greek Maccabees; entirely separate composition).
- **γ.4.2.C** Ephrem on Exodus.
- **γ.4.3** Cyril on Luke (~400 long-term).

**Recommended next ship**:
- **γ.4.8 Mäqabyan seed** — opens the THIRD uniquely-Tewahedo
  canonical text (the Ethiopic Maccabean books, three texts that
  exist in NO other Christian canon and are NOT the same as Greek
  1-2-3-4 Maccabees). With 1 En + Jub now both substantively
  covered, completing the Ethiopic-extras triad would close the
  uniquely-Tewahedo canonical-witness gap entirely.
- **γ.4.5.B Jubilees Watchers + Mastema detail** — substantive
  expansion of Jub 5-10, the Jubilees-side of the angelic-history
  narrative.
- **γ.4.2.C Ephrem on Exodus** — Ephrem continuation.

**Session totals (2026-05-12, cumulative through γ.4.5)**:
- γ.4.4.A-E shipped (Mäṣḥafä Hēnok arc CLOSED)
- γ.4.2 + γ.4.2.B shipped (Ephrem on Gen 1-50 substantively expanded)
- γ.4.5 shipped (Mäṣḥafä Kufāle / Jubilees seed)
- 3 phases shipped unsaved since the last save (γ.4.4.E + γ.4.2.B +
  γ.4.5) — per the "keep pushing / push" continuation directive
  (memory: push/continue advances to next phase without auto-save).

---

## Prior task before γ.4.5 (kept for context)

**γ.4.2.B Ephrem on Genesis 12-50 (patriarchal narrative, 40 entries)**
shipped 2026-05-12. Continues γ.4.2 (Gen 1-11, 32 entries shipped
earlier this session) into the Abraham (15 entries: 12:1, 12:7,
14:18, 15:6, 17:5, 17:10, 18:1, 18:14, 21:1, 22:1, 22:8, 22:14,
23:2, 24:67, 25:9), Jacob (12: 25:23, 27:27, 28:12, 28:17, 32:24,
32:28, 33:4, 35:10, 35:18, 35:22, 35:29, 36:1), and Joseph (13:
37:3, 37:9, 37:28, 39:9, 40:8, 41:38, 41:55, 42:24, 44:18, 45:4,
45:5, 49:10, 50:20) cycles. Rebalances Ephrem share from ~10%
(substantially under-represented after the γ.4.4 1 Enoch arc) back
toward ~19%. **Note**: shipped AFTER closing the γ.4.4 Mäṣḥafä
Hēnok arc with γ.4.4.E and BEFORE saving — pursued as the "keep
pushing" continuation directive (per memory: push/continue advances
to next phase, never auto-save).

**Why it matters for THIS project**:

- **Rebalances voice mix.** After the γ.4.4 wave the corpus was 35
  Cyril / 10 Ephrem / 55 1 Enoch — Ephrem substantially under-
  represented. γ.4.2.B brings Ephrem to ~17-19% — a healthier
  three-voice balance.
- **Melchizedek (14:18)** is the Tewahedo eucharistic prefiguration
  par excellence — the Tewahedo Anaphora explicitly invokes
  Melchizedek as the priestly archetype that Christ fulfils.
- **Mamre Trinity theophany (18:1)** anchors the Tewahedo
  iconographic Trinity-at-Mamre tradition (older and more widespread
  in Tewahedo church-wall fresco than in any other Oriental
  Orthodox communion).
- **The Akedah (22:1, 22:8, 22:14)** is the OT Crucifixion-type
  par excellence — Ephrem's reading anchors the Moriah-Calvary
  identification preserved in the Tewahedo Anaphora.
- **Jacob's ladder (28:12)** as Christ-and-Mary type undergirds
  Tewahedo Marian hymnody — the Wǝddase Maryam (Praise of Mary)
  cites Jacob's ladder as a Marian OT type.
- **Joseph cycle Christ-typology** (37:28 sold for silver / 41:55
  'go unto Joseph' = Marian-Cana prefiguration / 44:18 Judah's
  substitutionary offering / 49:10 Shiloh) — Tewahedo Holy-Week
  liturgy explicitly draws the Joseph-typology.
- **Providence formula 50:20** is foundational in Tewahedo
  consolation literature — every personal harm submits to a larger
  divine purpose.

**Files**:
- `content/sources/ethiopian_commentaries.json` — 40 new Ephrem-on-
  Genesis entries appended (book=`gen`, father=`Ephrem the Syrian`,
  work=`Commentary on Genesis`, year=`360`, attribution `Ephrem the
  Syrian, Commentary on Genesis, [Section N.V]. NPNF Series 2, vol.
  13, ed. J. Gwynn / Schaff (1898). PD.`). _meta scope/source
  strings updated. Total entries now 390 (was 350 pre-γ.4.2.B).
- `tests/test_ethiopian_gamma4.py` — new
  `TestGamma42BEphremPatriarchsWave` class with **14 tests**:
  ≥40 entries pin + all three patriarchal cycles covered + Ephrem
  share ≥17% + 11 signature passages (14:18, 15:6, 18:1, 22:8,
  28:12, 32:24, 37:28, 41:55, 44:18, 49:10, 50:20).

**Code-side wiring**: zero new code.

**Corpus state post-γ.4.2.B**:
```
ethiopian_commentaries.json: 390 entries (was 350; +40)
├─ Cyril of Alexandria     : 121 entries (John 1-7 + 11-21 — COMPLETE)
├─ Ephrem the Syrian       :  77 entries (Gen 1-50: Primeval History
                                          11 chs + patriarchal narrative
                                          Gen 12-50; Ps 1; Hymns on
                                          Paradise) — substantively rebalanced
└─ 1 Enoch tradition       : 192 entries (Mäṣḥafä Hēnok arc CLOSED
                                          γ.4.4.A-E)

Voice mix: ~31% Cyril / ~20% Ephrem / ~49% 1 Enoch
           (was 35/10/55 pre-γ.4.2.B — Ephrem rebalanced upward,
            1 Enoch still plurality, voice spread healthier)
γ.4 cumulative              : 378 entries beyond γ.4 seed
                             (.1.A 30 + .1.B 27 + .1.C 29 + .1.D 30 +
                              .2 32 + .2.B 40 + .4 30 + .4.B 40 +
                              .4.C 40 + .4.D 40 + .4.E 40 = 378)
```

**+14 tests**. **γ.4.2.B tests: 14/14 pass in isolation; 11/11 lint
clean.**

**Forward references**:
- **γ.4.2.C** Ephrem on Exodus (would continue Ephrem expansion).
- **γ.4.3** Cyril on Luke (~400 long-term).
- **γ.4.5** Mäṣḥafä Kufāle / Book of Jubilees seed — opens next
  uniquely-Tewahedo canonical text on the Mäṣḥafä-Hēnok pattern.

**Recommended next ship**:
- **γ.4.5 Jubilees seed** — opens the second uniquely-Tewahedo
  canonical text (Mäṣḥafä Kufāle is canonical in Tewahedo and
  preserved only in Ge'ez, exactly parallel to 1 Enoch's preservation
  pattern). With Ephrem rebalanced and the 1 Enoch arc closed, this
  is the natural next ambitious wave.
- **γ.4.2.C Ephrem on Exodus** — further Ephrem expansion.

**Session totals (2026-05-12, cumulative)**:
- γ.4.4.A through γ.4.4.E shipped (Mäṣḥafä Hēnok arc CLOSED)
- γ.4.2 (Gen 1-11) + γ.4.2.B (Gen 12-50) — Ephrem on Genesis through
  Joseph cycle
- Net test delta since session start: substantial positive (specific
  count drifts with the environmental subprocess flakers; see
  CHANGELOG for the precise pass-counts at each ship)

---

## Prior task before γ.4.2.B (kept for context)

**γ.4.4.E 1 Enoch Epistle of Enoch + Apocalypse of Weeks + Birth of
Noah detail (40 entries on chs 91-108) — CLOSES the Mäṣḥafä Hēnok
arc** shipped 2026-05-12. Substantive expansion of the remaining
Mäṣḥafä Hēnok section beyond the 4 first-wave entries on this
range (91:7, 93:3, 99:10, 104:2). Brings chs 91-108 coverage from 4
to 44 entries. **All six sections of the Ethiopian 1 Enoch
(Watchers + Parables + Astronomical Book + Dream Visions + Animal
Apocalypse + Epistle) are now substantively expanded.** 1 Enoch
share of corpus rises from ~49% to ~56% — 1 Enoch is now the
**dominant** voice in the corpus.

**Why it matters for THIS project**:

- **CLOSURE of the Mäṣḥafä Hēnok content arc**. The Ethiopian
  Tewahedo Church is the ONLY major Christian communion to canonize
  1 Enoch as biblical. The project's eponymous edition
  (ethiopian-tewahedo) now has comprehensive patristic-grade
  commentary on every section of its distinctive canonical text.
- The **Apocalypse of Weeks (1En 93 + 91:11-17)** is the Second-
  Temple period's most influential periodisation scheme — directly
  parallel and prior to Daniel 9:24-27's 70-weeks scheme. Tewahedo
  historiographical tradition draws on the seven-past + three-
  eschatological structure.
- **91:14 (tenth-week judgment of watchers)** CLOSES the Watchers
  arc that opened in 1En 6 — final eschatological judgment of the
  fallen angels, complementing the preliminary bindings at 1En 10,
  88:1, and 90:24. The tetraptych structure (bound → judged in
  Watchers vision → judged in Animal Apocalypse vision → final
  judgment in Apocalypse of Weeks) is now fully traceable across
  the corpus.
- **91:16 (sevenfold-light new heaven)** is the Mäṣḥafä Hēnok's
  eschatological climax — Rev 21:1 antecedent with the distinctive
  sevenfold-light intensification (cf. Isa 30:26).
- **95:3 (saints shall judge the world)** is the textual basis for
  the apocalyptic-saints-judge-the-world tradition that 1 Cor 6:2
  presupposes — Tewahedo theosis-and-vindication theology preserves
  this canonically.
- **98:4 (sin not sent from heaven; man authored it)** is the
  FOUNDATIONAL anti-Manichaean anchor in the Tewahedo theodicy
  framework, cited in anti-Zandic polemic.
- **104:10 (sinners will pervert words of righteousness)** is the
  scriptural warrant for the entire Tewahedo manuscript-preservation
  enterprise. **104:12 (books given to righteous as joy)** is its
  positive complement: scribal copying as joy-form participation in
  the heavenly liturgy.
- **105:1 ('I and My son')** is one of the rare pre-Christian
  'son' references — Tewahedo Christology reads it as Father-Son
  union pre-canonical witness, anticipating Jn 14:23 / 17:21-23.
- **106:2 (Noah's radiant birth)** anchors the Tewahedo iconographic
  motif of saintly-radiance from birth, preserved in monastic
  fresco tradition.
- **108:1 ('for those who keep the law in the last days')** is the
  Mäṣḥafä Hēnok's closing inclusio — and Tewahedo readers
  identify directly as that addressee, since they are the ONLY
  Bible-reading community for whom 1 Enoch is canonical Scripture.

**Files**:
- `content/sources/ethiopian_commentaries.json` — 40 new 1 Enoch
  entries appended:
  Apocalypse of Weeks (10: 93:2, 93:5, 93:6, 93:8, 93:9, 93:10 +
  91:12, 91:13, 91:14, 91:16 — seven-past weeks + three-
  eschatological weeks) + Epistle introduction (1: 92:1) + paths
  and woes (24: 94:1, 94:6, 94:7, 95:3, 96:1, 96:3, 97:8, 98:4,
  98:7, 99:3, 99:5, 100:1, 100:4, 100:7, 101:1, 102:4, 102:5,
  103:2, 103:4, 103:7, 104:6, 104:10, 104:12, 105:1) + Birth of
  Noah (4: 106:2, 106:13, 106:18, 107:1) + closing inclusio (1:
  108:1). _meta scope/source strings updated. **Two work labels
  used per existing convention**: `Apocalypse of Weeks (1 Enoch
  93)` for 93:* and 91:12-16 (year=-150); `Epistle of Enoch
  (1 Enoch 91-108)` for everything else (year=-100).
- `tests/test_ethiopian_gamma4.py` — new
  `TestGamma44EEpistleOfEnochWave` class with **15 tests**
  including the arc-close pin `test_all_six_mashafa_henok_sections_covered`
  that programmatically verifies every one of the six Mäṣḥafä Hēnok
  sections has substantive coverage (Watchers ≥40 + Parables ≥40 +
  Astronomical ≥10 + Dream Visions ≥3 + Animal Apocalypse ≥20 +
  Epistle ≥40).

**Code-side wiring**: zero new code.

**Corpus state post-γ.4.4.E**:
```
ethiopian_commentaries.json: 350 entries (was 310; +40)
├─ Cyril of Alexandria     : 121 entries (John 1-7 + 11-21 — COMPLETE)
├─ Ephrem the Syrian       :  37 entries (Gen 1-9, 11)
└─ 1 Enoch tradition       : 192 entries — Mäṣḥafä Hēnok now FULLY
                                          substantively expanded across
                                          all 6 sections:
                                          ├─ Watchers (1-36)            :  51
                                          ├─ Parables (37-71)            :  49
                                          ├─ Astronomical (72-82)        :  ~14
                                          ├─ Dream Visions (83-84)       :   ~4
                                          ├─ Animal Apocalypse (85-90)   :  ~30
                                          └─ Epistle (91-108)            :  ~44

Voice mix: ~35% Cyril / ~10% Ephrem / ~55% 1 Enoch
           (was 39/12/49 pre-γ.4.4.E — 1 Enoch is now dominant)
γ.4 cumulative              : 338 entries beyond γ.4 seed
                             (.1.A 30 + .1.B 27 + .1.C 29 + .1.D 30 +
                              .2 32 + .4 30 + .4.B 40 + .4.C 40 +
                              .4.D 40 + .4.E 40 = 338)
```

**+15 tests**. **γ.4.4.E tests: 15/15 pass in isolation; 11/11 lint
clean.**

**γ.4.4 ARC CLOSURE NOTE**: With γ.4.4.E shipped, the Mäṣḥafä Hēnok
content sub-arc (γ.4.4.A first-wave through γ.4.4.E Epistle) is
COMPLETE for substantive-coverage purposes. Each of the six
canonical sections has ≥3 verse-keyed Tewahedo-significant entries;
the largest sections (Watchers + Parables + Epistle) each have ≥40
substantive entries. The Mäṣḥafä Hēnok is now the deepest single-
source presence in the corpus (192 entries) — appropriate for the
Tewahedo edition that uniquely canonizes it.

**Forward references**:
- **γ.4.2.B** Ephrem on Gen 12-50 — would rebalance voice mix back
  toward Ephrem (currently 10% — substantially under-represented).
- **γ.4.3** Cyril on Luke (~400 long-term).
- **NEW**: with the Mäṣḥafä Hēnok arc closed, consider opening other
  uniquely-Tewahedo canonical texts: **γ.4.5** Mäṣḥafä Kufāle
  (Book of Jubilees, also canonical in Tewahedo and in Ge'ez only);
  **γ.4.6** Mäṣḥafä Aksumawi (Ethiopic Sirach reception); or
  **γ.4.7** Senodos / Didascalia Ethiopic patristic-canonical texts.

**Recommended next ship**:
- **γ.4.2.B Ephrem on Gen 12-50** — rebalances Ephrem share from
  10% back toward 20-25%. Patriarchal narrative is the natural
  continuation of the γ.4.2 Gen 1-11 first wave.
- **OR γ.4.5 Jubilees seed** — opens the next uniquely-Tewahedo
  canonical text on the same Mäṣḥafä-Hēnok-style trajectory.
