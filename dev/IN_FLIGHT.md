# In-flight work — current task tracker

<!-- TRACKER-STATE: idle -->

## Active task

*(none — tracker is idle. **χ.0 Kenyon textual-criticism ingest**
shipped 2026-05-08: F.G. Kenyon's *Our Bible and the Ancient
Manuscripts* (1895, PD) was OCR'd via the system's `pdftotext`,
staged into `content/sources/kenyon_textcrit.txt` (775 KB / 18,394
lines), and ingested through:
- new `text-witness` kind in `content/kinds.yaml` (category=text)
- `KenyonText` loader + `KenyonReference` dataclass +
  `KENYON_BOOK_NAME_TO_CODE` map in `scripts/core/sources.py`
- `KenyonReferenceDetector` + `_clean_kenyon_context()` in
  `scripts/core/detectors.py`; registered in `ALL_DETECTORS`
- `scripts/run_kenyon_at_scale.py` driver mirroring χ.6/χ.7 with
  merge-not-clobber + chapter-wide ID renumber semantics
- 117 notes promoted via `batch_promote_xrefs.py --kind
  text-witness` across 38 books (heaviest: Mat/Luk 12 each;
  Gen 9; Jhn 8; Psa 6); all tagged `tradition=cross`
- spec at `dev/SCOPE_2026-05-08-addendum-kenyon-textcrit.md`
- +16 tests across `TestKenyonSourceLoader` (6) +
  `TestKenyonReferenceDetector` (7) + `TestRunKenyonAtScaleDriver`
  (3); **716 tests green, 10/10 linter clean, 16,042 notes**.

Next per the most-logical-path: **χ-AI-xrefs** (~$30-80 Anthropic
API per pass; +5-15K thematic/typological/idiomatic links; cost
gate lifted 2026-05-08 per memory `project_ai_xrefs_unfunded.md`).
Mirror the χ-cluster pattern from §9 with an LLM-backed detector.
Then **ω.5 paths refactor → θ.1 launcher → θ.2 native shell** for
the v1.0 candidate. Audio (ρ.1) + prettification (ψ.14, ψ.17)
ship as v1.x polish on a working v1.0 candidate.

Parallel user-side free-roll (independent of my work): run
`python scripts/fetch_sources.py` from any network-enabled shell
to unblock χ.7 (+2-3K Nave's) + χ.1 (+5-10K Strong's Greek). Both
pipelines are already infrastructure-shipped earlier this session.)*

## Earlier idle context (kept for §14 audit reference)

ψ.8.4 per-book tradition overrides shipped 2026-05-08:
`traditions_per_book` schema field (flat-list-of-`"<book>=<t1,t2>"`
strings on disk, dict in API/UI), `decode_per_book_traditions` /
`encode_per_book_traditions` pair with canonical book-order sort on
encode, `_resolve_traditions_for_book` resolver (per-book wins over
default; ∅ means no filter for that book), validator in
`api_save_edition_meta`, decoded emission in `api_customize_data`,
extended Traditions card on /customize with the per-book matrix
shape (default-row + add-book picker + bulk-clear + per-row remove
×), §6.1 lint coverage bumped 2 → 3 encoders. +21 tests; 698 tests
green. ψ.8.2-B + ψ.8.3 popup tradition stack + customize Traditions
card shipped 2026-05-08: build pipeline labels every surviving
editorial-note `<aside>` with `data-tradition="<id>"` + canonical
display label paragraph (`apply_tradition_labels_to_html`), and
/customize hosts the initial Traditions card. +10 tests; 677 tests
green. ψ.8.1 + ψ.8.2-A traditions schema field + build-pipeline
filter shipped 2026-05-08: 16 tests; 649 tests green. ψ.8.0
backfill (scripts/core/traditions.py + content/traditions.yaml +
backfill_traditions.py + 37 tests) audited the corpus and confirmed
all 15,925 notes resolve to the `cross` tradition. The `--apply`
rewriter is reserved for ψ.8.0.1 (lands when χ.2-χ.5 ship tradition-
tagged commentary content). χ.1 Strong's Greek + GreekWordDetector
infrastructure shipped 2026-05-08: source loader, detector, at-scale
driver, +19 tests; source-data fetch + batch promote are user-side
(run scripts/fetch_sources.py from a network env or upload JSON via
/sources, then run_greek_at_scale.py, then batch_promote_xrefs.py
--kind lang-greek for the ~5-10K corpus delta). χ.7 Nave's Topical
infrastructure (NavesTopical loader + NaveTopicalDetector +
run_naves_at_scale.py + fetcher + prospect.py SourceMissingError
resilience + 16 tests) likewise has data fetch + promote pending
on the user-side network step.

## Pending follow-up (parked)

- **cleanup.py expansion** — should prune exports/, epub_working/,
  builds/, AND content/candidates/ (now ~1,355 files growing).
- **scaffolder integration test** — running --apply against a temp
  dir to catch indent-error class bugs.
- **UI defense prelude** in scaffolder — fold in automatically.
- **χ cluster continuation:**
  - χ.7 Nave's Topical (infra DONE; data fetch is user-side)
  - χ.1 Strong's Greek (Greek lexicon + GreekWordDetector + KJV NT reader)
  - χ.2-5 Commentaries (Henry, Calvin, Catena, Rashi)
- **§14 worked twice last session** (web.py split indent bug;
  HebrewWord cut-off). Document as §12 retrospective trigger
  candidate next time the rules doc is touched.
