# Round-15 deep-audit program — the 9 completeness-critic gaps

> **STATUS: PREPARED for a fresh session — NOT YET APPROVED, NOT YET RUNNING.**
> Drafted 2026-06-26 at the close of round-14 (which finished green on both lanes). The round-14
> completeness-critic flagged **nine areas the round-14 audit did NOT cover** as explicit
> "seeds for the next round" (see `dev/audit/round14-mac-plan.md` → "Completeness-critic gaps").
> Round-15 turns those nine seeds into a planned, scoped, two-lane deep-audit.

## How the fresh session runs this (matches the round-14 process)

1. **Bootstrap + pull** the triad (RULES → SESSION_STATE → roadmap) + `dev/IN_FLIGHT.md` + this doc.
2. **`EnterPlanMode`** and review this program against current code (the dimensions below were
   scoped at draft time by an independent per-gap scoping pass — verify they are still apt).
3. **`ExitPlanMode` for USER approval.** Do NOT begin auditing until the user approves (the user
   wants to see + approve the plan first, exactly as with round-14).
4. **Configure the engine** (`.claude/workflows/deep-audit.js`, edited in-file per the
   args-don't-propagate convention): bump `ROUND = 15`; replace the build-pipeline dimensions
   with the round-15 dimensions below (or add them); fold the **round-14 SETTLED** list into
   `DEFERRED_BY_DESIGN`; add the round-14 fix titles to `PRIOR_SURVIVOR_TITLES` (confirm-not-regress).
   Set `LANE` per machine (`win` / `mac`), in-file, NOT committed.
5. **Execute two-lane** — WIN = build-heavy dimensions + any new gate code + build-path fixes;
   Mac = read-only/source dimensions + cross-OS verify. Adversarially verify every finding
   (the engine already refutes each finding before it counts). **Loop until green:** all
   survivors fixed (TDD + byte-stability proof on any build-path touch) + the new gates pass +
   `pytest` green.
6. **Save cadence** (RULES §4): local-commit per fix, push both remotes at each coherent slice;
   truth-record every fix in `dev/audit/round15-remediation.md` (create it like
   `round14-remediation.md`).

## Round-14 SETTLED — deferred-by-design for round-15 (do NOT re-litigate; a verifier MUST refute a finding that merely re-raises one of these)

- **A1 LF chokepoint** (`scripts/core/zip_repro.ocf_member_bytes` wired at `build_epub.py:161` +
  `kindle_post.py:121`) — SHIPPED + Mac cross-OS VERIFIED (9/9 KJV cells byte-identical Win↔Mac).
  Do NOT re-flag CRLF-vs-LF / cross-OS byte-identity; `core/zip_repro.py` is in `_PIPELINE_SCRIPTS`.
- **A2** single-pass `_apply_splices` (the `apply_badge_markers:4444` Windows-commit OOM) — SHIPPED.
  The flagship-eink "OOM" was largely an **environmental AppXSvc commit-leak** (reboot clears it);
  do NOT re-diagnose it as a code defect — check `CommitFree` first (memory `reference-hardware-box-and-mac`).
- **The 5 round-14 gates are BUILT** — do NOT re-flag "no KJV golden gate" (G1) / "no idmap gate"
  (G3) / "badges_skipped not enforced" (G4) / "no glossary-cap gate" (G5): G1 `tests/test_kjv_golden_hash_gate.py`
  + `tests/golden/kjv_golden_hashes.json`, A4 `.github/workflows/kjv-golden.yml`, G3 `dev/audit_idmap_frags.py`,
  G4 `dev/audit_badge_conservation.py`, G5 `dev/audit_glossary_contract.py`, wired via `tests/test_round14_build_gates.py`.
- **Survivors fixed:** #1 eink_glyphs cache-coverage · #2 prospect None-guard · #3 canonical-extent
  (`core/distinctive_verse_counts.py`) · #4 S1 attribution (cascade-gate `s2_group or eink_backmatter`) ·
  #5 G1 · #6 est 10:2 (`_mv_displacement_would_corrupt`; Mac mirror in `audit_verse_formatting.py`) ·
  the **G5 over-cap** finding (`_atom_rewrite_headroom`). Do NOT re-raise est 10:2, the glossary over-cap
  on catholic-study, or the S1/S2 attribution combo.
- **Earlier-session settled** (audit for regression/bleed ONLY): the WS1 mid-verse merge + the 158-verse
  re-split (USER-RATIFIED) · WS2 cascade de-dup · WS3 popup separators · the eink font `!important` fix ·
  the page-break re-arch (Parts 1/2/2b) · the poetry/wisdom mid-verse breaks KEPT by user decision.
- **Marathon core is OFF-LIMITS** (read-only): `scripts/build_standalone.py`, `scripts/core/manuscript_*.py`,
  `scripts/core/po_vision_store.py`, `content/manuscript/**`, `content/translations/sources/patrologia/**`,
  `GAPS/`. No edits absent an outright crash.

## Invariants every round-15 fix carries

- **9-KJV byte-stable** — every build-path fix is additive / eink- or customize-gated and carries a
  byte-identity proof (regen the 9 cells + `git diff`, or re-run the **G1 golden gate**) before commit.
  If a new import lands in the EPUB build path, add the module to `_PIPELINE_SCRIPTS` (the
  `TestCacheCoverageGuard` AST guard enforces this — it caught `zip_repro` in round-14).
- **Additive schema only** · writes through `notes_io.atomic_write` / `ensure_backup` · **no paid API**.
- **A real defect spotted while scoping is in-scope to fix** (don't self-narrow); a build-side fix to a
  data/versification corruption class must mirror its detector (like #6 → `audit_verse_formatting.py`).

## The 9 dimensions (D1–D9)

> Scoped by an independent per-gap pass at draft time (one agent per gap, verifying files vs current
> code + sharpening the check/propagation/lane). Each dimension below carries: the defect class to hunt,
> the deterministic check/gate to build, the propagation path, the lane, and any concrete defect already
> spotted while scoping. **(Populated below from the scoping pass.)**

### D1 — Release asset-set integrity · lane: either · no build · **HIGH**
**Defect class:** the public GitHub release carries assets source no longer sanctions (retired-SKU / stale-version EPUBs), and `SHA256SUMS.txt` + the website catalog tolerate them silently — orphan sum lines, missing sum lines, duplicate/conflicting hashes, stale hard-coded version.
**Gate to build:** NEW `dev/audit_release_assets.py` (offline `--assets-file`/`--sums-file`): (1) bijection `attached-assets == SHA256SUMS lines` (orphan + missing + duplicate); (2) every attached `YHWH-<id>-v<ver>-<fmt>-<colour>` asset's `<id>` is an active edition and `<ver>==tag`, + substring-scan vs `lint_rules._RETIRED_EDITION_SKUS`; (3) no hard-coded stale version in `gen_release_catalog`.
**Already spotted:** `gen_release_catalog.py:47-55/61-68` hard-codes `v0.1.0` filenames + URLs (not `--tag`); `lint_rules.check_retired_edition_skus:2038` scans only the repo tree → blind to the 2 retired notes-only SKU EPUBs SESSION_STATE says are live on v0.1.0; `format-matrix.yml:144-153` only appends sums (orphans accumulate); `release.py` is the legacy save-stamper, NOT the real deploy path (that's `format-matrix.yml` + `gen_release_catalog.py`).
**Propagation:** a reader follows a still-live download link / SHA256SUMS and gets the wrong/withdrawn Bible on-device.

### D2 — Xref link resolution in the built+split per-edition EPUB · lane: win · needs build · MEDIUM
**Defect class:** a rendered xref/noteref anchor (`#v-`/`#vnote-`/`#ch-` or `file#frag` post-split) whose target id is absent from the spine piece the reader is in — idmap miss (`_bare` silently leaves it bare) or canon-filter dropped the target. The named `check_xrefs.py` is blind: it scans only `epub_working/` (pre-split, unfiltered SUPERSET).
**Gate:** use **G3** (`audit_idmap_frags`) on FRESH builds of eink catholic-study (canon-filtered+split) + eink ethiopian (superset+split) + a tablet control; add an xref-class breakout + a presence floor; **WIRE G3 into the per-build gate** (the round-14 `test_round14_build_gates.py` already builds catholic-study eink → extend). Fix `check_xrefs.py:52` regex `\bid=` → `(?<=\s)id=` (matches inside `data-*-id=`) or retire it in favor of G3.
**Already spotted:** `build_edition.py:5932-5938 _bare` silent-leaves on idmap miss + last-write-wins on dup ids; `check_xrefs.py:52` regex bug (dormant today, 0 `data-*-id` in base); G3's only real-data test is `slow` + skips unless a catholic eink epub is already on disk.
**Propagation:** a dead/wrong cross-reference ships in the flagship eink/Kobo edition → dead tap on-device.

### D3 — Versification fold/merge segment tiling (Douay + Clementine-Vulgate) · lane: mac · no build · **HIGH** ★LIVE DEFECTS
**Defect class:** silent verse DROP (adapter returns None → `extract_translation.apply_remap:521` drops it) or RE-SLOT (off-by-one → wrong KJV neighbor, the est 10:2 class) from incomplete/incorrect segment maps; existing tests are OUTPUT-driven (blind to dropped inputs) + hand-enumerated.
**★ Already FOUND (fix in round-15):** **Douay/Vulgate Psalm 2:13 is silently DROPPED** — KJV Ps 2:12 is missing its closing clause "When his wrath shall be kindled… blessed are all they that trust in him" (D/V split KJV 2:12 into 2:12+2:13; 2:13→None). **Psalm 4:10 likewise DROPPED** — KJV Ps 4:8 missing "For thou, O Lord, singularly hast settled me in hope." Fix = add `_VULGATE_PSALM_FIXES` entries `(2,13)→(2,12)` + `(4,10)→(4,8)` (trailing concat-fold, like the existing `(135,27)→(136,26)`).
**Gate to build:** NEW `dev/audit_versification_coverage.py`: parse each SOURCE vpl (`content/translations/sources/{douay-rheims,vulgate-clementine}/*_vpl.txt` — NOTE the prompt's `douay/`+`vulgate/` paths were wrong; the stores are post-remap), assert every source `(code,ch,vs)` maps non-None + in-extent UNLESS on a documented-omit allowlist; + structural tiling `[1,last_verse]` per segment chapter. Latin ≠ Douay counts → run BOTH independently. (Ps 2/4 route through `_VULGATE_PSALM_FIXES`, not `_VULGATE_SEGMENTS` — a tiling-only check would miss them; the source-coverage check catches them.)
**Propagation:** the Douay/Clementine parallel popup for that KJV verse ships missing/wrong scripture text on every device.

### D4 — /customize note-flag cross-product · lane: either · no build · **HIGH** ★CONCRETE round-14 RESIDUE
**Defect class:** silent attribution/category/distinct-point LOSS at untested combinations of the note-presentation flags; the S1 strip is gated on a `cascade` predicate that ASSUMES a downstream re-surfacer that isn't always active.
**★ Already FOUND (re-examine the round-14 #4 fix):** my round-14 #4 `_cascade = s2_group or eink_backmatter` (`build_edition.py:4228`) is **over-permissive** — in `{note_attribution_dedup=on, note_group_by_category=off, target_reader=eink, layout=backmatter}` (eink default), `eink_backmatter=True` runs the dict-*/topic-* source strip, but the backmatter glossary `_study_glossary_category_body` (s2_group=False branch) does NOT re-emit the source → provenance lost. The Mac's literal `_cascade = s2_group` was more correct. Recommended fix (verify with the D4 gate first): `_cascade = s2_group` for the source-bearing strips, OR make `_study_glossary_category_body` emit the source head when `s2_group=False`. **(Byte-safe for the 9-KJV + shipped editions — they all have `s2_group` on; only the unshipped S2-off eink combo changes.)**
**Gate to build:** NEW `dev/audit_customize_flag_matrix.py` (reuse `test_note_rehaul.py`'s gen-1 temp-tree fixture, build-free): for each combo of S1×S2×S3a×eink-layout×time_filter×popup_translation, build one fixture carrying every source family, assert (1) `_body_fingerprint` multiset conserved vs all-off baseline; (2) each note's source token still appears somewhere in the rendered HTML.
**Propagation:** the shipped Kobo study-Bible renders dict/topical notes with provenance silently missing.

### D5 — Glossary-streaming FLAGSHIP byte-verify + G5 at flagship density · lane: win · needs build · **HIGH**
**Defect class:** `_stream_glossary_pieces_from_bytes` (the per-book byte streamer) is reached in PRODUCTION only by a >64 MB glossary = the ethiopian flagship ALONE, and was **never byte-verified at scale**; str==from-file is pinned only on a 6-book synthetic with the threshold monkeypatched. A byte-scan miss → wrong pieces (straddle/drop/dup) OR a silent fall-through to the whole-decode str path = the ~1.4 GB OOM the refactor removed. The round-14 G5 over-cap fix + `_atom_rewrite_headroom` were verified only on catholic-study link density.
**DOC CONFLICT to resolve:** is catholic-study's glossary <64 MB? If so the round-14 453/453 proof took the str-delegate branch → the byte streamer has ZERO real-edition coverage.
**Gate:** CHECK A — feed the real flagship `index_split_900.html` into both `split_study_glossary_document` and `_iter_study_glossary_pieces_from_file` (>64 MB forces the byte branch for the first time on real content) → assert identical piece names + bytes (high-RAM lane). CHECK B — run **G5** (`audit_glossary_contract`) on a FRESH flagship eink build → exit 0. Fold B into `test_round14_build_gates.py` (add a flagship artifact); fold A into `test_file_split.py::TestStreamGlossaryFromFile` (a real-size byte-branch case).
**Propagation:** a flagship glossary piece straddles two books / busts the 400 k navigate cap / OOM-crashes the build — on the primary published edition.

### D6 — corpus_index ↔ matrix book/note count vs what ships · lane: either · no build · MEDIUM
**Defect class:** TWO independent canon determinations feed one EPUB — Path A (`build_edition.py:8292 epub_utils.load_canons` → which books physically ship) vs Path B (`matrix._load_canons` → the printed "It spans N books" + the note total) — through mirror loaders with NO source-anchored cross-check; the Delta.4 equivalence pin is VACUOUS (both compute_matrix paths share `_canon_books_for_edition`).
**Gate to build:** NEW `dev/audit_canon_bookcount.py`: (1) source-anchored 4-way canon recount (fresh `yaml.safe_load` of `canons.yaml` == compute_matrix == file-walk == `epub_utils.load_canons`); (2) note recount from source tuples == `edition_stats.resolved_note_counts(ed)['total']`, re-asserted after `corpus_index.rebuild()`; (3) (build) printed "It spans N books" == numbered-book spine count. De-vacuum `TestDelta4` with assertion (1).
**Already spotted:** `matter_pages.py:359` APPENDIX_BOOKS subtraction never checked vs the demoted spine; `compute_matrix` `lru_cache` not invalidated on a `canons.yaml` mtime change.
**Propagation:** the Your-Edition front-matter claims a book/note count that disagrees with the device ToC — a self-contradicting product.

### D7 — Migration DEFINITIONS re-run / idempotency safety · lane: either · no build · MEDIUM
**Defect class:** a migration whose re-run doesn't restore correct on-disk state of `content/notes/**` or `content/translations/**`. 0001's idempotency is a coarse single-file marker (`editions.yaml` present → "Already migrated") evaluated BEFORE a non-atomic `shutil.copy2` over UNSORTED files — an interrupted first run that copied `editions.yaml` but left a torn `notes/<book>.py` is reported migrated on re-run and never repaired (ledger asserts a success the disk lacks). 0002's `--apply` is a dead stub (a future AST rewriter with no pinned idempotency contract).
**Gate to build:** NEW `dev/audit_migration_idempotence.py` (auto-covers 0003+): (A) AST static write-route — any write under content must route through `notes_io.atomic_write` (flags `migrate_to_user_data.py:105 shutil.copy2`); (B) double-apply byte-convergence (run `run_up` twice → every content file SHA identical); (C) ledger-independence (delete `.migration_state.yaml`, re-run, bytes unchanged); (D) torn-partial recovery probe (expected to FAIL today).
**Propagation:** a torn `notes/<book>.py` in the user's content root → that book's notes/popups vanish from the app + any EPUB built off it, while the ledger reports success.

### D8 — Canonical book/chapter ORDER in the emitted nav.xhtml + opf spine · lane: win · needs build · MEDIUM
**Defect class:** emitted order is never asserted against config (only the web-UI `books.yaml` payload is). `enrich_nav_chapters` (`build_edition.py:6646-6647 chs.sort()`) makes nav/ncx chapter entries always ascending-by-number regardless of actual spine document order → a reading-flow chapter swap is invisible in the native ToC AND to the existing auditor (which also sorts before checking).
**Gate to build:** NEW canon-aware `dev/audit_canonical_order.py` (imports `config.load_books`+`load_canons`): assert spine bp sequence == expected canonical (folds/demotions applied); per-book chapter anchors strictly ascending in DOCUMENT order (not sorted-then-checked); nav book/chapter order == spine document order (equality — defeats the sort-masking); ncx playOrder gapless. **Must encode the demotion/fold model** (nav 83 vs spine 86 bp = the demoted appendix paz/sus/bel — a naive nav==spine false-positives).
**Already spotted:** NO confirmed order defect (probed r8 builds: spine monotonic, 1en's 108 chapters ascending — SESSION_STATE's "1en misordering" is the verse-level column-zipper content defect, NOT order); but the sort-masking is a real latent risk.
**Propagation:** a rewrite pass reorders books/chapters; the device reading flow / ToC shows them out of canonical sequence while the ToC reads 1,2,3.

### D9 — Kepub bare `-sN` rev-id family (guard #19): settle artifact-age vs live · lane: win · needs build · MEDIUM
**Defect class:** whether a FRESH ethiopian `.kepub` has any INLINE popup `verse-notes` id missing its `-s[1-9]` tail (→ Kobo mis-measures the slice and NAVIGATES instead of popping) — cleanly separated from the BY-DESIGN bare per-category NAVIGATE ids (backmatter layout, bare on purpose). Plus a **gate blindspot:** `verify_kr2_build._POPUP_ASIDE_RE:179-182` requires `class` first on `<aside`; if kepubify v4.0.4 reorders attributes the regex matches 0 asides → the gate passes VACUOUSLY.
**Gate:** build a FRESH `.kepub` (`reader_sim.py --gate kobo` → kepubify v4.0.4 → `verify_kr2_build`); bucket every `vnotes-*`/`vbadge-*` id by its bearing element's class — bucket A inline (`verse-notes` w/o `study-glossary-cat`) MUST be `-sN`; bucket B navigate (`study-glossary-cat`) bare is OK; per-book census (isolate `rev`). Bare only in B → artifact-age (close guard #19); any bare in A → LIVE regression. Assert `_POPUP_ASIDE_RE` matches >0 asides on the koboSpan'd file (liveness self-check). Add a non-failing `dev/audit_kepub_revid_family.py` census so future rounds don't re-derive ad-hoc counts.
**Already spotted:** `deep-audit.js:294` points finders at the now-GONE `dist/…v0.1.0.kepub.epub` (the aged-asset trap → MUST build fresh; fix the pointer); `kindle_post.py` is a mis-pointer (the real kepub path is `build_format_matrix.py:198` + `build_edition.py:4319/4375` + `verify_kr2_build.py:255-340`). The 792/36k figure is almost certainly the by-design backmatter navigate family (~2 ids/verse × Rev's 404 verses) — PROVE on a fresh artifact, don't re-derive.
**Propagation:** a Revelation inline popup ships without its `-sN` tail → every affected footnote NAVIGATES away mid-reading on the user's color Kobo (and a kepubify-blinded gate would pass green while it ships).

## ★ Concrete defects the scoping pass ALREADY found (start the round-15 remediation here)

These were surfaced read-only while scoping (NOT fixed — left for the approved round-15 run, each with a regression test + byte/coverage proof):
1. **D3 — Douay/Clementine-Vulgate Psalm 2:13 + Psalm 4:10 silently DROPPED** (real missing scripture text in the parallel popups). Fix = `_VULGATE_PSALM_FIXES` `(2,13)→(2,12)` + `(4,10)→(4,8)`. **HIGH, the verse-corruption class round-14 #6 was.**
2. **D4 — the round-14 #4 fix is incomplete:** `_cascade = s2_group or eink_backmatter` (`build_edition.py:4228`) over-strips dict/topic source attribution in `{S1-on, S2-off, eink-backmatter}` because the backmatter glossary doesn't re-surface the source. The Mac's literal `_cascade = s2_group` is correct. Byte-safe for shipped editions. **Re-examine + fix with the D4 conservation gate.**
3. **D2/D5/D8/D9 gate blindspots** (latent, prove on a fresh build): `check_xrefs.py:52` regex matches `data-*-id=`; the byte glossary streamer has ~zero real-edition coverage (D5); `enrich_nav_chapters` sort-masks a chapter swap (D8); `_POPUP_ASIDE_RE` can pass vacuously if kepubify reorders attributes (D9). Plus stale pointers: `deep-audit.js:294` → a `dist/…kepub` that no longer exists; `release.py` ≠ the real deploy path.

## Lane division (derived from the per-dimension lanes; round-14 convention: `build_edition.py` = WIN-exclusive, `dev/audit/**` + macOS builds = Mac)

| Lane | Dimensions | Why |
|------|-----------|-----|
| **WIN** (build-heavy + build-path fixes + gates needing a build) | **D2** xref · **D5** glossary flagship · **D8** nav/opf order · **D9** kepub rev-id; **+** all `build_edition.py` fixes (D4 `_cascade`, any build-path fix); wire G3 (D2) + the new build-needing gates into `test_round14_build_gates.py` | needs local EPUB / .kepub builds; owns `build_edition.py` |
| **MAC** (read-only / source + build-free gates + cross-OS verify) | **D3** versification gate + the Ps 2:13/4:10 store fixes · **D1** release-asset gate · **D6** book-count gate · **D7** migration-idempotence gate · **D4** flag-matrix gate (build-free); cross-OS verify every WIN build | source/static analysis, no build; `dev/audit/**` |

The two lanes work file-disjoint in PARALLEL (truth_owner = windows); each pushes its own milestones. Re-confirm tool/agent parity (guard #4) before either lane runs a shared workflow.

## Deliverables

- A `dev/audit/round15-remediation.md` tracker (per-survivor status, like round-14's).
- New reusable gate scripts where a dimension warrants one (named `dev/audit_<x>.py`, mirroring the
  G3/G4/G5 conventions; wired into `tests/test_round14_build_gates.py` or a sibling per-build test).
- Every surfaced finding fixed (TDD + byte-stability proof) to green, adversarially verified, cross-OS.
