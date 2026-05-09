# Session state — current snapshot

**Updated:** 2026-05-08, after **ω.5 (foundation)** shipped — the
per-user data location resolver. Built `scripts/core/paths.py`
(repo_root + user_data_root + content_root resolver with in-tree
dev-mode fallback + sub-path helpers + cache invalidation hooks),
migrated the 5 `scripts/core/` consumers (sources, translations,
config, covers, traditions) to expose paths-resolver entrypoints
without removing back-compat constants, and wrote
`scripts/migrate_to_user_data.py` as the one-shot bootstrap helper.
Remaining 41 call-site files (web.py + at-scale drivers + CLI
tools) become rolling sub-phases ω.5.1+ — the in-tree fallback
keeps them working unchanged during the rolling migration.
Session arc so far (continuous-go): scope expansion → ν.2.9+ψ.10
→ ξ.4 → ω.8 → ω.9 → ξ.2 → ω.10 → ξ.1 → ψ.12 → ψ.13 → χ.1 → ψ.8.0
→ ψ.8.1+8.2-A → ω.14 → ψ.8.2-B+ψ.8.3 → ψ.8.4 → ψ.8.5 → χ.0 →
χ-AI-xrefs → τ.1 WEB + χ.0+ scope → **ω.5 foundation**. Twenty
implementation phases this session. ω.5 unblocks the desktop
binary (θ.1/θ.2) — bundled .app/.exe payloads can now find their
user-mutable data in the platform user-data dir while keeping
read-only resources in the bundle. Corpus growth remains the
largest v1.0 gap (16,042 / 25K floor); the unlock paths
(χ-AI-xrefs paid + χ.7/χ.1 free + τ.1 WEB free) are all parked
on user-side runs. Next per the most-logical-path is **θ.1
launcher → θ.2 shell** for the v1.0 candidate; ω.5.1+ rolling
call-site migrations ship in parallel as needed.
**Save tag:** σ.3 → ω.6 → scope add → ω.7 → υ.7 → υ.1 → τ-scope →
3rd-rev scope on `bridge4kaladin-collab/yhwh-bible-platform`,
private. Saves are now git pushes, not zips — see "GIT BACKUP" in
the inventory below and the root-level `save.cmd` / `save.ps1`
helpers. Each commit runs the pre-commit hook
(`scripts/lint_rules.py` 10/10 must pass).

> 📖 **First time reading this?** Then go read
> `dev/CLAUDE_PROJECT_RULES.md` first, then come back here, then
> `dev/PLAN_2026-05-08.md`. Three files = full orientation.
>
> **Also peek** at `dev/IN_FLIGHT.md` — if its
> `<!-- TRACKER-STATE: ... -->` marker is `active`, work is open.

---

## Status snapshot

```
13 consoles · 783 tests · 10/10 linter · 5 editions · 16,042 notes

PLATFORM:    Feature-complete for the buyer demo.
             Tier 1 (debt + refactor) DONE.
             Tier B (v1.0 differentiator) DONE — ψ.8 cluster complete:
               ψ.8.0 schema foundation
               ψ.8.1 + ψ.8.2-A schema field + filter
               ψ.8.2-B + ψ.8.3 popup labels + customize UI
               ψ.8.4 per-book tradition overrides
               ψ.8.5 wizard Traditions step (this turn)
             Tier 2 (corpus growth via χ cluster) UNDERWAY:
               χ.6 done  (xref + hebrew via existing detectors)
               χ.7 INFRA done; data fetch is user-side
               χ.1 INFRA done; data fetch is user-side
             Path to v1.0 candidate (per "most-logical" sequence):
               next: χ.0 Kenyon ingest (free, code-only)
               then: χ-AI-xrefs (cost gate lifted)
               then: ω.5 paths refactor → θ.1 launcher → θ.2 shell
             v1.x polish: ρ.1 audio, ψ.14 buyer-arc, ψ.17 reader-EPUB

CORPUS:      15,925 notes (45.5% of 35K target — unchanged this session;
             AI-augmented xrefs unblocked on user funding 2026-05-08;
             slotted as a v1.x χ-cluster phase post-v1.0).
```

---

## Current phase: ω.5 paths-resolver foundation shipped

Foundation-only ship. The new `scripts/core/paths.py` is the single
source of truth for project paths; the 5 `scripts/core/` modules
that the rest of the project imports now expose paths-resolver
entrypoints. Remaining 41 call-site files migrate as rolling
sub-phases ω.5.1+ — the in-tree fallback in the resolver keeps
un-migrated sites working unchanged during the roll.

```
✓ scripts/core/paths.py                 repo_root() + user_data_root()
                                        (Win/macOS/Linux platform-
                                        aware) + content_root()
                                        resolver: testing override
                                        > YHWH_CONTENT_ROOT env var
                                        > in-tree dev (requires
                                        editions.yaml marker) >
                                        user_data_root() installed.
                                        Sub-path helpers
                                        (notes/candidates/sources/
                                        translations/covers/audio +
                                        7 yaml helpers); build-
                                        output siblings (exports/
                                        epub_working/builds/
                                        backups). lru_cache + reset
                                        + set-for-testing hooks.
✓ scripts/core/{sources,translations,   each grew a paths-resolver
  config,covers,traditions}.py          entrypoint helper function
                                        (_sources_dir, _translations
                                        _dir, _books_yaml_path,
                                        _covers_dir, _traditions_
                                        yaml_path). Existing module
                                        constants preserved verbatim
                                        for back-compat with every
                                        existing PATH-monkeypatch
                                        test.
✓ scripts/migrate_to_user_data.py        one-shot bootstrap copies
                                        in-tree content/ →
                                        user_data_root/content/.
                                        Idempotent (skips existing
                                        unless --force); --dry-run
                                        previews; refuses on missing
                                        source; short-circuits with
                                        "Already migrated" when
                                        destination has the marker.
✓ tests/test_scripts.py                 +32 tests across 5 new
                                        classes:
                                        - TestPathsRepoAndUserData (7)
                                        - TestPathsContentRootResolver (6)
                                        - TestPathsSubPathHelpers (4)
                                        - TestPathsCacheBehavior (2)
                                        - TestCoreModulesUsePathsResolver (5)
                                        - TestMigrateToUserData (8)
~ Corpus delta                          0 — pure infrastructure.
```

Rolling migration parked as **ω.5.1+ sub-phases** (each migrates
one cluster of call sites; in-tree fallback means un-migrated
files continue to work):
```
ω.5.1   at-scale drivers (run_*_at_scale.py)
ω.5.2   scripts/web.py content references (~41 occurrences)
ω.5.3   remaining CLI tools (promote, prospect, attribute, etc.)
```

## Prior phase: τ.1 WEB infrastructure + χ.0+ scope shipped

Two-part ship: τ.1 WEB lays the groundwork for the entire τ cluster
(11 PD-translation extensions parked in Tier D); the χ.0+ scope
addendum stages the next four textual-criticism ingests after χ.0
Kenyon. Both are infrastructure / spec — corpus delta is 0.

```
✓ scripts/extract_translation.py        TRANSLATIONS registry +
                                        meta_for() helper; KJV
                                        moved into the registry
                                        verbatim (back-compat
                                        byte-identical _meta.yaml
                                        modulo regenerated date).
                                        New τ phases now register
                                        an entry; rest of the
                                        pipeline works unchanged.
                                        --list flag dumps the
                                        registered translations
                                        with URLs + fetch packages.
                                        Unregistered ids fall back
                                        to a stub _meta.yaml with
                                        an explicit "promote to
                                        registry before publishing"
                                        notes field.
✓ TRANSLATIONS["web"]                   World English Bible
                                        registered. Source:
                                        https://eBible.org/eng-web/
                                        package eng-web_vpl.zip
                                        (PD; modern English; ρ.1
                                        audio synergy via LibriVox
                                        WEB recordings).
✓ dev/SCOPE_2026-05-08-addendum-       χ.0.1 W&H 1881 + χ.0.2
  textcrit-deep-dive.md                 Burgon 1883 + χ.0.3 Souter
                                        1913 + χ.0.4 Driver 1890
                                        as next textual-criticism
                                        ingests. Each ~1 session,
                                        mirrors χ.0; reuses the
                                        text-witness kind +
                                        KenyonReferenceDetector
                                        pattern. Conservative
                                        cumulative yield ~360-720
                                        promoted notes. Per-source
                                        shipping (omnibus rejected
                                        so reviewer can tune
                                        confidence floors between
                                        sources).
✓ tests/test_scripts.py                 +7 tests in
                                        TestTranslationsRegistry
                                        (kjv registered; web
                                        registered; list_registered
                                        stable; meta_for kjv +
                                        web from registry; meta_for
                                        unregistered → stub;
                                        end-to-end synthetic-VPL
                                        WEB extraction smoke).
~ Corpus delta                          0 (infrastructure-only).
                                        τ.1 user-side completion:
                                        download eng-web_vpl.zip
                                        from eBible, unzip into
                                        content/translations/
                                        sources/web/, run
                                        `python3 scripts/extract_
                                        translation.py web --report`.
                                        χ.0+ data fetch: PDFs
                                        from archive.org per the
                                        addendum's links.
```

## Prior phase: χ-AI-xrefs infrastructure shipped

First χ-cluster phase backed by an API rather than a static cached
source. The infrastructure is feature-complete and tested; the data
fetch is paid + user-side, identical contract to χ.7 / χ.1's
"infrastructure-shipped, fetch-pending" parking pattern but with a
real cost dial.

```
✓ content/kinds.yaml                    new `xref-thematic` kind
                                        under category=xref;
                                        symbol ‖ inherited; phase=mvp.
✓ scripts/core/sources.py               AnthropicXrefClient (lazy +
                                        injectable completion_fn);
                                        SourceMissingError when no
                                        ANTHROPIC_API_KEY + no
                                        injected fn (mirror of
                                        NaveTopical's contract).
                                        Singleton via
                                        anthropic_xref_client().
                                        Default real-SDK call uses
                                        prompt caching on the
                                        system prompt (~10× cost
                                        cut). DEFAULT_AI_XREF_MODEL
                                        = claude-haiku-4-5-20251001.
                                        propose_xrefs() validates
                                        target book against
                                        config.books_by_code(),
                                        clamps confidence to [0,1],
                                        defensively returns [] on
                                        any malformed completion.
✓ scripts/core/detectors.py             AIXrefDetector emits
                                        xref-thematic candidates;
                                        registered in ALL_DETECTORS;
                                        attribution mentions
                                        "Claude AI"; body composes
                                        target-link + reasoning +
                                        explicit [Reviewer:] flag.
✓ scripts/run_ai_xrefs_at_scale.py       new driver mirroring
                                        run_greek_at_scale.py with
                                        cost guards: --dry-run
                                        prints projected cost & exits
                                        without API call;
                                        --max-verses N default 100;
                                        --confirm-cost required
                                        when --max-verses > 200
                                        (CONFIRM_COST_THRESHOLD);
                                        --model passthrough;
                                        merge-not-clobber output.
✓ dev/SCOPE_2026-05-08-addendum-ai-xrefs.md   spec.
✓ tests/test_scripts.py                 +28 tests across 3 new classes
                                        (TestAnthropicXrefClient 8 +
                                        TestAIXrefDetector 9 +
                                        TestRunAIXrefsAtScaleDriver 10
                                        + 1 kind-yaml smoke).
~ Corpus delta                          0 (infrastructure-only;
                                        data fetch is paid + user-
                                        side: ~$0.09/100v; ~$28
                                        full 31K-verse pass).
```

User-side completion (parked, paid):
```
1. export ANTHROPIC_API_KEY=...   (one-time)
   pip install anthropic           (one-time)
2. python3 scripts/run_ai_xrefs_at_scale.py --dry-run
3. python3 scripts/run_ai_xrefs_at_scale.py --books jhn --max-verses 50
4. (when ready) python3 scripts/run_ai_xrefs_at_scale.py \
       --max-verses 31000 --confirm-cost
5. python3 scripts/batch_promote_xrefs.py --kind xref-thematic
```

## Prior phase: χ.0 Kenyon textual-criticism ingest shipped

First χ-cluster phase since χ.1 Strong's Greek; first one fed by
**local public-domain text** rather than a network fetch. F.G.
Kenyon's *Our Bible and the Ancient Manuscripts* (1895, PD) was
OCR'd via the system's `pdftotext`, staged under `content/sources/`,
and ingested through a new detector + driver mirroring the χ.6 / χ.7
pattern. Promoted 117 notes across 38 books, all tagged
`tradition=cross` (manuscript history is denominationally neutral).

```
✓ content/sources/kenyon_textcrit.txt   775 KB OCR text from
                                        oldfindings.pdf (Princeton
                                        Theological Seminary scan).
✓ content/kinds.yaml                    new text-witness kind under
                                        category=text; symbol ✧
                                        inherited; phase=mvp.
✓ scripts/core/sources.py               KENYON_BOOK_NAME_TO_CODE
                                        (66+ entries) + KenyonReference
                                        dataclass + KenyonText loader
                                        with regex-tolerant parser +
                                        kenyon_text() singleton.
✓ scripts/core/detectors.py             KenyonReferenceDetector emits
                                        text-witness candidates;
                                        _clean_kenyon_context() strips
                                        OCR artifacts (carets,
                                        backticks, pipes, backslashes,
                                        repeated punctuation);
                                        registered in ALL_DETECTORS.
✓ scripts/run_kenyon_at_scale.py        new driver mirroring
                                        run_xref_at_scale.py; merge-
                                        not-clobber semantics with
                                        chapter-wide ID renumber on
                                        write; --max-per-verse cap.
✓ dev/SCOPE_2026-05-08-addendum-kenyon-textcrit.md   spec.
✓ tests/test_scripts.py                 +16 tests across 3 new classes
                                        (TestKenyonSourceLoader 6 +
                                        TestKenyonReferenceDetector 7
                                        + TestRunKenyonAtScaleDriver 3).
✓ Corpus delta                          +116 notes (15,925 → 16,042;
                                        45.8% of 35K target). 38 books
                                        (1 bogus index citation
                                        removed pre-save);
                                        heaviest: Mat (12), Luk (12),
                                        Gen (9), Jhn (8), Psa (6).
```

## Prior phase: ψ.8.5 wizard Traditions step shipped — ψ.8 cluster complete

The last ψ.8 sub-phase. The /wizard buyer-demo flow now has a
Traditions step (Step 5 of 7) that pre-selects sensible defaults
from the chosen profile and folds the picks into the build payload.
The cross-denominational compare apparatus — the v1.0 differentiator
— is feature-complete.

```
✓ scripts/templates/wizard.py      step indicator bumped 6 → 7;
                                   new <section id="step-5"> Traditions
                                   pane with card-style picker driven
                                   by DATA.customize.traditions registry.
                                   PROFILE_TO_TRADITIONS map seeds
                                   defaults (catholic-study →
                                   ["catholic","cross"], etc.); pre-
                                   existing edition.traditions_default
                                   wins over the seed for re-runs.
                                   STATE.traditions_initialized flag
                                   preserves user edits across back/
                                   forward navigation. Step 6 (Review)
                                   gains a Traditions pill row;
                                   startBuild folds traditions_default
                                   into the edition-meta save (no new
                                   endpoint — pure composition over
                                   ψ.8.1's validator).
✓ tests/test_scripts.py             +2 tests — test_wizard_has_traditions
                                   _step + test_wizard_step_indicator
                                   _has_seven_dots; updated existing
                                   test_wizard_html_constant_exists
                                   (range bumped 6 → 7).
```

## Prior phase: ψ.8.4 per-book tradition overrides shipped

The fourth ψ.8 sub-phase. Editions can now override the default
tradition filter on a per-book basis — same shape as ν.2.7's
`popup_languages_per_book`. New `traditions_per_book` schema field
(flat list of `"<book>=<t1>,<t2>"` strings on disk, dict in API/UI),
encoder + decoder + canonical-order linter coverage, validator,
per-book resolver in the build pipeline, and an extended Traditions
card on /customize with the same per-book matrix the popup-languages
card already uses. Only **ψ.8.5** wizard-step integration remains.

```
✓ scripts/build_edition.py         decode_per_book_traditions /
                                   encode_per_book_traditions mirror
                                   the ν.2.7 popup-language pair.
                                   _resolve_traditions_for_book(edition,
                                   book) returns the active set per
                                   book (per-book wins over default;
                                   ∅ means "no filter for that book").
                                   compute_tradition_disabled_html_ref
                                   _ids + build_ref_id_to_tradition_map
                                   refactored to use the resolver with
                                   a per-book active-set cache.
                                   _iter_note_ref_traditions now yields
                                   (ref_id, tradition, book_code).
✓ scripts/web.py                   traditions_per_book validator
                                   in api_save_edition_meta (mirror
                                   of popup_languages_per_book);
                                   _decode_traditions_per_book_for_api
                                   surfaces decoded dict in
                                   api_customize_data; preview EDITABLE
                                   set + clone passthrough updated.
✓ scripts/templates/customize.py   Traditions card extended with the
                                   per-book matrix (overrides count,
                                   bulk-clear, add-book picker, remove
                                   per row). wireTraditionsSection
                                   rewritten to manage
                                   {default, perBook, original} state.
                                   buildCustomizePayload emits both
                                   traditions_default + traditions_per
                                   _book on save; post-save baseline
                                   reset clones the dual-shape original.
✓ scripts/lint_rules.py            encode_per_book_traditions added
                                   to check_encoder_canonical_order
                                   and check_encode_decode_round_trip.
                                   Linter now reports "all 3 encoders /
                                   3 encode/decode pairs" cleanly.
✓ tests/test_scripts.py             +21 tests across 3 new classes —
                                   TestTraditionsPerBookEncoderDecoder
                                   (7), TestTraditionsPerBookResolver
                                   (7), TestTraditionsPerBookCustomizeAPI
                                   (6); plus updated traditions-card
                                   HTML smoke (1).
```

## Prior phase: ψ.8.2-B + ψ.8.3 popup tradition stack + customize Traditions card shipped

The second half of the spec's ψ.8.1+8.2+8.3 batch. Build pipeline
labels every surviving editorial-note `<aside>` with its tradition
(data-tradition attr + canonical display label paragraph), and the
/customize console hosts a Traditions card so publishers can pick the
denominational filter in the UI rather than hand-editing
editions.yaml.

```
✓ scripts/build_edition.py         _iter_note_ref_traditions() yields
                                   (ref_id, tradition) for every note;
                                   shared by ψ.8.2-A filter and the
                                   new ψ.8.2-B labeller (compose-don't-
                                   recompute, §9).
                                   build_ref_id_to_tradition_map(edition)
                                   returns {ref_id: tradition} for
                                   surviving notes; empty when
                                   traditions_default unset (§7.2).
                                   apply_tradition_labels_to_html()
                                   adds data-tradition="<id>" to each
                                   surviving aside opening tag and
                                   prepends a <p class="note-tradition-
                                   label">Display Label</p> paragraph.
                                   Idempotent on already-labelled HTML.
                                   build_one() runs the pass after
                                   filter_html + the vnote pass, gated
                                   on a non-empty map; new
                                   tradition_labels_applied stat.
✓ scripts/templates/customize.py   <details class="traditions-section">
                                   card between Reader Experience and
                                   Per-book popup languages. Checkboxes
                                   driven by DATA.traditions registry
                                   (single source of truth from ψ.8.1).
                                   wireTraditionsSection() mirrors
                                   wirePopupLanguageSection's pattern;
                                   box.traditionsState / .dataset.
                                   traditionsDirty fold into the
                                   generic dirty handler + ν.2.9 badge
                                   + buildCustomizePayload + post-save
                                   baseline reset.
✓ tests/test_scripts.py             +10 tests — TestTraditionLabelInjection
                                   (9: empty-map no-op / happy path /
                                   skip-not-in-map / idempotent /
                                   canonical labels for every CANONICAL_
                                   TRADITIONS id / xml-escape /
                                   real-corpus iterator / build_ref_id
                                   _to_tradition_map empty-when-unset /
                                   cross-keeps-corpus) +
                                   test_customize_html_has_traditions
                                   _card (1: HTML smoke).
```

## Prior phase: ω.14 epubcheck preflight validation gate shipped

Wired the W3C/IDPF epubcheck Java tool into the readiness dashboard
as check #9. Real EPUB validation, gracefully degraded when Java is
absent — once OpenJDK 8+ lands on the build machine and a real
build cycle runs, this becomes a hard shipping gate.

```
✓ scripts/core/epubcheck.py        is_available() + run_epubcheck() +
                                   run_epubcheck_on_dir() pure-function
                                   wrapper around the bundled JAR.
✓ scripts/web.py · _compute_       new check id 'epubcheck' surfaces
  preflight_uncached()             the aggregate validator status.
✓ tests/test_scripts.py             +18 tests across 2 classes.
```

## Prior phase: ψ.8.1 + ψ.8.2-A traditions schema field + filter shipped

The first half of the ψ.8.1+8.2+8.3 batch from the spec's sub-phasing.
Splits at a clean seam — the schema/validator/API + a working
build-pipeline filter ship now (publishers can manually edit
editions.yaml and see filtered EPUBs). The popup redesign + UI ship
in the next batch (ψ.8.2-B + ψ.8.3).

```
✓ scripts/web.py · api_save_edition_meta   traditions_default validator
                                            (mirrors popup_languages_default;
                                             list of strings, each in
                                             TRADITION_IDS; dedupe; reject
                                             unknown / non-string).
✓ scripts/web.py · api_customize_data      `traditions_default` exposed per
                                            edition (defensive-filtered);
                                            new top-level `traditions`
                                            registry — [{id, label}, …]
                                            in CANONICAL_TRADITIONS order.
✓ scripts/web.py · _filter_traditions_default
                                            defensive helper for the YAML-
                                            round-trip-junk corner case.
✓ scripts/build_edition.py                  compute_tradition_disabled_html_ref_ids
                                            walks notes, derives tradition,
                                            returns the ref-id set whose
                                            tradition isn't in the edition's
                                            traditions_default. Empty list →
                                            empty set (no-op, §7.2).
                                            build_one unions into existing
                                            disabled_html_ref_ids before
                                            filter_html runs.
✓ tests/test_scripts.py                     +16 tests across 2 classes —
                                            TestTraditionsCustomizeAPI (9),
                                            TestTraditionFilterBuildPipeline (7).
```

## Prior phase: ψ.8.0 tradition schema foundation shipped

The first sub-phase of ψ.8 (the v1.0 differentiator). Establishes the
tradition axis as a typed schema + lookup module + idempotent audit
script, without touching the build pipeline or any UI (those are
ψ.8.1 / ψ.8.2 / ψ.8.3, the next batch).

```
✓ scripts/core/traditions.py        CANONICAL_TRADITIONS (closed
                                    ordered set: catholic, protestant,
                                    orthodox, jewish, tewahedo, cross)
                                    + note_tradition() resolver
                                    + edition_to_tradition() lookup
                                    + with_tradition() stamping helper
                                    + tiny YAML parser
✓ content/traditions.yaml           edition_to_tradition mapping for
                                    the 5 seeded editions (using actual
                                    edition ids — the spec mapping was
                                    aspirational and slightly off).
✓ scripts/backfill_traditions.py    audit + (parked) migration script.
                                    Today: dry-run only, confirms all
                                    15,925 notes resolve to `cross`.
                                    --apply reserved for ψ.8.0.1 (the
                                    AST-aware rewriter, lands when
                                    χ.2-χ.5 ship tradition-tagged
                                    commentary content).
✓ tests/test_scripts.py              +37 tests across 3 classes —
                                    TestTraditionsModule (25),
                                    TestTraditionsYaml (5),
                                    TestBackfillTraditionsScript (7).
```

**Audit result this ship:** all 15,925 notes → `cross` (as expected
— the corpus is exclusively χ-cluster output: TSK / Strong's H /
Strong's G / Nave's, all denominationally neutral).

## Prior phase: χ.1 Strong's Greek + GreekWordDetector shipped

Mirror of HebrewWordDetector for NT verses, applying the §9 χ-cluster
pattern for the third time (after χ.6 hebrew and χ.7 naves). Source
loader + detector class + at-scale driver + tests are in place; the
fetch + batch promote remain user-side, identical to χ.7's contract.

```
✓ content/sources/_fetchers.json   strongs_greek source declared
                                   (required, parser strongs-greek-js,
                                   openscriptures Greek dump).
✓ scripts/core/fetcher_config.py   KNOWN_PARSERS adds strongs-greek-js.
✓ scripts/fetch_sources.py         _parse_strongs_greek_js + PARSERS
                                   entry. Mirror of the Hebrew parser;
                                   different JS variable name.
✓ scripts/core/sources.py          StrongsGreekEntry + StrongsGreek
                                   loader + strongs_greek() singleton.
                                   Tolerates both `xlit` and `translit`
                                   field names — openscriptures' Greek
                                   dump uses translit historically.
✓ scripts/core/detectors.py        GREEK_KEYWORD_MAP (~60 entries) +
                                   GreekWordDetector + ALL_DETECTORS
                                   registration. NT-only filter
                                   (mirror of Hebrew's NT-skip, flipped).
✓ scripts/run_greek_at_scale.py    new driver iterating
                                   content/translations/kjv/<book>.py
                                   for NT books only. Appends to
                                   existing chapter files; idempotent
                                   on re-run.
```

**+19 tests** across four classes (`TestStrongsGreekSourceLoader` 3 ·
`TestGreekWordDetector` 7 · `TestStrongsGreekFetchUtilities` 5 ·
`TestRunGreekAtScaleDriver` 4). All synthetic fixtures — no network.

**User-side completion (parked):** run
`python scripts/fetch_sources.py` from a network-permitted env (or
upload via `/sources`) to populate `strongs_greek.json`, then
`python scripts/run_greek_at_scale.py` to write candidates, then
`python scripts/batch_promote_xrefs.py --kind lang-greek` to promote
(~5-10K notes expected).

## Prior phase: υ.1 /sources console upgrade shipped

The `/sources` console now hosts a Public-domain source cache section
above the existing per-book note-attribution navigator. Reads
`_fetchers.json` via the υ.7 loader; supports per-source Fetch / Force
re-fetch / Upload-pre-built-JSON / Clear, plus a top-level Fetch all /
Force re-fetch all. The χ.7 user-side completion (drop a pre-built
`naves_topical.json`) is now a one-click Upload JSON action in the UI
rather than a CLI dance.

```
✓ /api/sources/cache (GET)        status grid: cached, size_kb,
                                  mtime, candidates per source
✓ /api/sources/cache/<id>/fetch    POST {force, url_override?,
                                  parser_override?} — single source
                                  via injectable fetch_fn (testable)
✓ /api/sources/cache/_all/fetch    POST {force} — iterate every source
✓ /api/sources/cache/<id>/upload   POST multipart — JSON validated
                                  + atomic write + ensure_backup;
                                  disk untouched on validation failure
                                  (§9 binary-asset pattern)
✓ /api/sources/cache/<id>          DELETE — backup + unlink
✓ /sources HTML                    new <details> section above the
                                  per-book navigator; Tailwind only;
                                  no build step; cross-link invariant
                                  unchanged (no new console).
```

**+22 tests:** TestSourcesCacheUI in tests/test_scripts.py covers status
grid (4), fetch dispatch with injectable fetch_fn including url_override
and parser_override paths (5), fetch_all aggregation (2), upload happy
+ 6 rejection paths (multipart parser, JSON validity, dict shape, size
cap, missing file part, unknown source), clear (3), HTML wiring (1).
All synthetic — no network.

**Naming-collision avoided:** the existing `/api/sources/*` endpoints
remain about *note attribution* (per-book / per-note source strings).
The new endpoints live under `/api/sources/cache/*`. The `/sources`
HTML page hosts both as sibling sections under one page, preserving
the §6.2 cross-link invariant (no new console added; no other console's
nav block touched).

**Prior phases this session:**
- υ.7 — Pluggable fetcher config (declarative `_fetchers.json` loaded
  by `scripts/core/fetcher_config.py`).
- ω.7 — Persistent dev ergonomics (PYTHONUTF8=1 + Scripts on PATH +
  pre-commit hook + `.gitattributes`).
- ω.6 — Verified baseline (393/393 tests, 14/14 routes, 8/8 linter).
- σ.3 — GitHub backup workflow.
- Scope expansion — ψ.8 + ρ.1 + ω.6/ω.7 + ψ.10 + ψ.12 + polish trio.
- χ.7 Nave's Topical infrastructure.

**Cumulative this session:**
```
υ.1:         /api/sources/cache/* + /sources page extension; +22 tests.
υ.7:         _fetchers.json + fetcher_config.py + parser registry;
             +19 tests; 1 existing test repaired.
ω.7:         user env + tracked pre-commit hook + .gitattributes.
ω.6:         baseline verification (393/393, 14/14 routes, 8/8 lint).
σ.3:         repo init + private push + save.cmd/.ps1 wrappers.
Scope exp:   ψ.8 + ρ.1 + ω.6 + ω.7 + ψ.10 + ψ.12 + polish trio.
χ.7 infra:   16 new tests, 0 corpus notes.
End state:   434 tests, 8/8 linter, 15,925 notes.
```

## Prior phase: υ.7 pluggable fetcher config shipped

The PD-source list moved from Python constants in
`scripts/fetch_sources.py` to declarative JSON in
`content/sources/_fetchers.json`, loaded and validated by a new
typed module `scripts/core/fetcher_config.py`. Adding a new PD
source is now: (a) write a parser in `scripts/fetch_sources.py`,
(b) register its name in
`fetcher_config.KNOWN_PARSERS` and `fetch_sources.PARSERS`,
(c) add a `sources[]` entry to `_fetchers.json`. No constants need
touching, and the schema validator catches drift between the two.

```
✓ content/sources/_fetchers.json   schema v1; 3 sources declared
                                   (strongs_hebrew, tsk required;
                                    naves_topical optional with 4
                                    candidate URLs).
✓ scripts/core/fetcher_config.py   typed dataclasses (Source,
                                   Candidate, FetcherConfig);
                                   FetcherConfigError on any
                                   validation failure.
✓ scripts/fetch_sources.py          parsers registered in
                                   PARSERS dict; main() iterates
                                   loaded config; write_attributions
                                   now assembles its body from the
                                   config so adding a source auto-
                                   includes its license notice.
```

**+19 tests:** TestFetcherConfig in tests/test_scripts.py covers
the schema validator (default config loads, rejects 7 distinct
malformed shapes including unknown parser / duplicate id / wrong
version / empty candidates / non-bool required / missing license)
and the dispatcher (synthetic-parser stubbed via monkeypatch — no
network — verifying happy path, fall-through-on-failure,
all-candidates-failed, cached-skip, force-rerun).

**One existing test repaired:**
`TestNavesFetchSourceUtilities::test_naves_appears_in_attribution_doc`
called `write_attributions()` with no args; updated to load the
default config and pass it.

**Prior phases this session:**
- ω.7 — Persistent dev ergonomics (PYTHONUTF8=1 + Scripts on PATH +
  pre-commit hook + .gitattributes).
- ω.6 — Verified baseline (393/393 tests, 14/14 routes, 8/8 linter).
- σ.3 — GitHub backup workflow.
- Scope expansion — ψ.8 + ρ.1 + ω.6/ω.7 + ψ.10 + ψ.12 + polish trio.
- χ.7 Nave's Topical infrastructure.

**Cumulative this session:**
```
υ.7:         _fetchers.json + fetcher_config.py + parser registry
             refactor; +19 tests, 1 test repaired.
ω.7:         user env + tracked pre-commit hook + .gitattributes.
ω.6:         baseline verification (393/393, 14/14 routes, 8/8 lint).
σ.3:         repo init + private push + save.cmd/.ps1 wrappers.
Scope exp:   ψ.8 + ρ.1 + ω.6 + ω.7 + ψ.10 + ψ.12 + polish trio.
χ.7 infra:   16 new tests, 0 corpus notes.
End state:   412 tests, 8/8 linter, 15,925 notes.
```

## Prior phase: ω.7 persistent dev ergonomics shipped

Three locked-in ergonomic upgrades. All future sessions on this
machine inherit them automatically; future machines re-do (a) and
(b) once via env-var GUI / one PowerShell line, then run
`./dev/install_hooks.cmd` for (c).

```
✓ PYTHONUTF8=1 set in User registry env
   Future shells inherit it. Files in the project that the runtime
   reads with `open(path)` (no explicit encoding) now work without
   the cp1252 fallback that bit ω.6.

✓ Python Scripts/ dir on User PATH
   C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\Scripts
   `pytest`, `py.test` etc. callable directly in fresh shells.

✓ Pre-commit hook installed
   Tracked template:    dev/git-hooks/pre-commit  (sh script)
   Tracked installer:   dev/install_hooks.cmd     (CRLF, cmd-parser-safe)
   Active copy:         .git/hooks/pre-commit     (per-checkout)
   Behavior: every git commit (and therefore every save.cmd) runs
   `python3 scripts/lint_rules.py` first. Failures abort the commit.
   Bypass with `git commit --no-verify` only when truly needed.
```

**Caveats / known caveats:**
- Currently-running shells (this Claude Code session, any open
  PowerShell windows) won't see the new env vars until restart.
  The registry change took effect; only inherited copies are stale.
- The installer needed CRLF line endings on Windows — cmd's parser
  chokes on parenthesized blocks with bare LF. The tracked file is
  CRLF; if a future machine commits LF it will fail until reformatted.
- The hook's `python3` lookup falls back through `python` → `py -3`
  for portability. On Windows, the Microsoft Store's `python3` stub
  is intentionally ranked below the real install via the user's PATH
  ordering set in ω.7 (b).

**Prior phases this session:**
- ω.6 — Verified baseline (393/393 tests, 14/14 routes, 8/8 linter).
- σ.3 — GitHub backup workflow.
- Scope expansion — ψ.8 + ρ.1 + ω.6/ω.7 + ψ.10 + ψ.12 + polish trio.
- χ.7 Nave's Topical infrastructure.

**Cumulative this session:**
```
ω.7:         user env (PYTHONUTF8 + PATH) + tracked pre-commit hook +
             installer (cmd, CRLF). Two new tracked files.
ω.6:         baseline verification (393/393, 14/14 routes, 8/8 lint).
σ.3:         repo init + private push + save.cmd/.ps1 wrappers.
Scope exp:   ψ.8 + ρ.1 + ω.6 + ω.7 + ψ.10 + ψ.12 + polish trio.
χ.7 infra:   16 new tests, 0 corpus notes (fetch is user-side).
End state:   393 tests, 8/8 linter, 15,925 notes.
```

## Prior phase: ω.6 verified baseline shipped

Local Windows install confirmed clean against the project's claimed
baselines:

```
✓ 393/393 tests pass     (with PYTHONUTF8=1 — see encoding note below)
✓ 14/14 routes return 200 (the 13 consoles + the / editor)
  /, /matrix, /sources, /export, /customize, /audit, /publisher,
  /wizard, /diff, /compare, /covers, /preflight, /apihelp, /ops
✓ 8/8 linter checks pass
~ /api/preflight: 5 pass · 2 warn · 1 fail
  fail = "Main covers per edition" — pre-existing, documented
  warn = "Popup translation per edition", "Kind utilization"
```

**Encoding gotcha caught:** Python's default file-read codec on
Windows is `cp1252`; without `PYTHONUTF8=1`, 72 tests fail with
`UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d`. The
project's source uses `open(path)` without an explicit encoding,
which works on Linux/Mac (UTF-8 default) but breaks on Windows.
Workaround for now: always run pytest with `PYTHONUTF8=1` set.
ω.7 will set this as a user-scope environment variable so it's
permanent. The proper fix (sweep `open()` calls to add
`encoding="utf-8"`) is parked as a low-priority follow-up — the
env-var workaround is fine for single-developer use.

**Dependency installed:** `reportlab` (was missing; print-cover
PDF generation requires it). Installed via pip into the local
Python; not committed since it's environment, not source.

**Prior phases this session:**
- σ.3 — GitHub backup workflow (initial push, save.cmd/.ps1
  wrappers, `.claude/` in `.gitignore`).
- Scope expansion — ψ.8 cross-denom + ρ.1 audio + ω.6/ω.7
  added to PLAN; v1.0 terminus updated to include ψ.8; two
  new SCOPE addenda written.
- χ.7 Nave's Topical infrastructure (16 new tests, 0 corpus
  notes — data fetch + promote remain user-side, blocked on
  network egress to archive.org / openbible.info).

**Cumulative this session:**
```
ω.6:         baseline verification (393/393 tests, 14/14 routes,
             8/8 linter; encoding workaround documented;
             reportlab installed)
σ.3:         repo init + private push + save.cmd/.ps1 wrappers
Scope exp:   ψ.8 + ρ.1 + ω.6 + ω.7 added to PLAN; 2 new addenda
χ.7 infra:   16 new tests, 0 corpus notes (fetch is user-side)
End state:   393 tests, 8/8 linter, 15,925 notes
```

**New / modified scripts:**
- `scripts/core/sources.py` — `NavesTopical` loader + singleton
- `scripts/core/detectors.py` — `NaveTopicalDetector` (in `ALL_DETECTORS`)
- `scripts/prospect.py` — detector instantiation tolerates
  `SourceMissingError` (forward-compatible with χ.1+)
- `scripts/fetch_sources.py` — `fetch_naves_topical()` with
  mirror-list fallback; full English book-name remap
- `scripts/run_naves_at_scale.py` — new driver mirroring
  `run_xref_at_scale.py`; **appends** to existing chapter files
  so xref + hebrew + naves coexist
- `content/categories.yaml` — `topic` category (sort_order 15)
- `content/kinds.yaml` — `topic-nave` kind
- `tests/test_scripts.py` — 16 new tests (4 classes, all
  synthetic-fixture, no network dep)
- `tests/test_scripts.py` — `TestCustomize` count assertions
  migrated from `==` to `>=` floors

---

## What's next per `dev/PLAN_2026-05-08.md` (the new master sequence)

The 05-08 scope refresh re-shaped the sequence around a v1.0
terminus, and the 2026-05-08 *scope expansion* (cross-denom compare
apparatus + audio EPUBs) promoted ψ.8 into the v1.0 definition:

```
v1.0 = θ.2 + χ.1 + ψ.8 + corpus ≥ 25K notes
```

See `dev/SCOPE_2026-05-08.md` for the base refresh,
`dev/SCOPE_2026-05-08-addendum-cross-denom-compare.md` for ψ.8 spec,
and `dev/SCOPE_2026-05-08-addendum-audio-epubs.md` for ρ.1 spec.
`dev/PLAN_2026-05-08.md` carries the full 22-phase order. Top of
queue right now:

```
ω.6  Verified baseline                  ✓ SHIPPED 2026-05-08
ω.7  Persistent dev ergonomics          ✓ SHIPPED 2026-05-08
υ.7  Pluggable fetcher config           ✓ SHIPPED 2026-05-08
υ.1  /sources console upgrade           ✓ SHIPPED 2026-05-08
     (Public-domain source cache section on /sources: status grid,
      Fetch / Force / Upload JSON / Clear per source, plus a top-
      level Fetch all. Wraps υ.7's config; subsumes the parked
      χ.7 user-side completion into a single Upload action.)

— END OF TIER A FOUNDATIONS —

Tier B is next: corpus growth + uniqueness levers (χ.1 Greek,
ψ.10 popup polish, ψ.12 matrix smoothness, ψ.8 cross-denom
compare apparatus, ρ.1 LibriVox audio, ω.5 path refactor).

Post-v1.0 polish includes the τ cluster (PD translation expansion):
τ.1 WEB → τ.2 Douay-Rheims → τ.3 Vulgate → τ.4 Brenton LXX →
τ.5 JPS+WLC → τ.6 Ge'ez Tewahedo → τ.7 Greek NT → τ.8 Geneva →
τ.9 ASV+YLT → τ.10 non-English → τ.11 Reformation partials.
Spec: dev/SCOPE_2026-05-08-addendum-pd-translations.md.

The third-revision (2026-05-08) scope expansion promoted ξ.1/2/4
(security: input validation, path traversal, XSS), ω.8/9/10
(robustness: error boundaries, atomic writes, retry/timeout), and
ψ.13/14/17 (prettification: design system, buyer arc, reader EPUB)
into the v1.0 terminus. Specs:
  dev/SCOPE_2026-05-08-addendum-security.md
  dev/SCOPE_2026-05-08-addendum-robustness.md
  dev/SCOPE_2026-05-08-addendum-prettification.md
Operator-facing polish and other softer items stay v1.1+.

υ.7  Pluggable fetcher config           AFTER ω cluster
     content/sources/_fetchers.json — declarative URL +
     parser-kind list. Lets fetch_sources.py read its source
     list from config rather than Python constants.

υ.1  /sources console upgrade           AFTER υ.7
     Real source-management page: status grid, "Fetch this" /
     "Fetch all" buttons, drag-drop file upload. Permanently
     closes source-fetch friction; subsumes the parked χ.7
     finalization step into a UI button.

χ.7 USER-SIDE COMPLETION (parked):
     User runs fetch_sources.py + run_naves_at_scale.py +
     batch_promote_xrefs.py --kind topic-nave from a network env
     (+2-3K topic-nave notes). Likely subsumed by υ.1.

χ.1  Strong's Greek + GreekWordDetector
     Parallels existing HebrewWordDetector exactly. ~5-10K
     lang-greek notes. Risk: LOW (proven pattern).

ψ.10 Popup typography polish                  PRECURSOR TO ψ.8
     Theme-aware CSS-only pass on the .vnote popup so the
     ψ.8 tradition stack inherits styling instead of being
     designed twice. ~½ session.

ψ.12 Matrix smoothness pass                   PRECURSOR TO ψ.8
     Surfaced by 2026-05-08 audit. Bundle of 7 fixes in
     scripts/templates/matrix.py: incremental DOM patching
     (killer at scale), sticky headers, keyboard nav, scroll
     preservation, dismissable banner, etc. Lands BEFORE ψ.8
     adds the tradition data axis. ~1 session.

ψ.8  Cross-denominational compare apparatus    THE v1.0 DIFFERENTIATOR
     Single popup, side-by-side notes from Catholic /
     Protestant / Orthodox / Jewish / Tewahedo + cross-tradition.
     ~2-3 sessions; schema change. Spec in
     dev/SCOPE_2026-05-08-addendum-cross-denom-compare.md.

ρ.1  Audio-augmented EPUBs (LibriVox)
     EPUB 3 native <audio> embed; PD recordings.
     ~1-2 sessions. Spec in
     dev/SCOPE_2026-05-08-addendum-audio-epubs.md.

ω.5  Per-user data location refactor
     Path resolver into user_data_dir() — must precede θ.
     ~1-2 sessions.

θ.1, θ.2  Desktop binary
     Launcher + native shell. Reaches v1.0 candidate.
```

---

## Pending follow-ups (parked)

- **cleanup.py expansion** — should also prune `exports/`,
  `epub_working/`, `builds/`, AND `content/candidates/`.
- **scaffolder integration test** — running `--apply` against a
  temp dir, to catch indent-error class bugs.
- **UI defense prelude in scaffolder** — fold the bulk_inject
  step in so future scaffolded consoles get the prelude
  automatically.
- **§14 worked twice last session** (web.py split indent bug;
  HebrewWord cut-off). Document this as a §12 retrospective
  trigger candidate next time the rules doc is touched.

---

## Inventory pointers (where things live)

```
GIT BACKUP (σ.3 — shipped 2026-05-08):
  Remote:    https://github.com/bridge4kaladin-collab/yhwh-bible-platform (private)
  Default branch: main
  Save command:  ./save.cmd "<message>"   (preferred Windows wrapper)
                 ./save.ps1 "<message>"   (needs PS execution policy)
                 raw: git add -A; git commit -m "<msg>"; git push
  Pull command:  git pull                 (start of fresh session)
  Excluded:  .claude/ (per-machine), plus everything in .gitignore.
  GitHub CLI lives at: C:\Program Files\GitHub CLI\gh.exe
  gh authed as: bridge4kaladin-collab (HTTPS, keyring-stored token).

LOCAL DEV ENVIRONMENT (ω.6 verified, ω.7 ergonomic — 2026-05-08):
  Python 3.14.4 at C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\
  Scripts dir on User PATH (ω.7): ...\pythoncore-3.14-64\Scripts\
                                  pytest, py.test, normalizer, pyhtmlizer
                                  callable directly in fresh shells.
  pip-installed: pytest, pyyaml, reportlab.
  PYTHONUTF8=1 set in User registry env (ω.7) — fresh shells inherit.
                Required on this install: without it, 72 tests fail
                on `UnicodeDecodeError: 'charmap' codec` at byte 0x9d
                (Python's Windows default is cp1252).
  Test invocation:  pytest                 (in a fresh shell post-ω.7)
                    PYTHONUTF8=1 python3 -m pytest   (current/old shell)
  Web server:       python3 scripts/web.py
                    Default: 127.0.0.1:8765 (the editor at /, plus
                    13 cross-linked consoles)
  Linter:           python3 scripts/lint_rules.py
                    8 checks. Pre-commit hook (ω.7) runs this on every
                    `git commit` automatically; failures abort the commit.
  Pre-commit hook:  Tracked template:  dev/git-hooks/pre-commit
                    Tracked installer: dev/install_hooks.cmd (CRLF)
                    Active copy:       .git/hooks/pre-commit
                    Bypass for one commit: `git commit --no-verify`
  Known pre-existing /api/preflight conditions:
    fail "Main covers per edition"     placeholder paths in seeded
                                        editions.yaml — fix via
                                        /covers upload or /customize blank
    warn "Popup translation per edition"  pre-existing; not blocking
    warn "Kind utilization"             pre-existing; not blocking

INGESTION INFRA — already complete as CLI + UI:
  scripts/fetch_sources.py        (υ.7: declarative; reads _fetchers.json)
  scripts/core/fetcher_config.py  (υ.7: schema + loader + validator)
  content/sources/_fetchers.json  (υ.7: source list, schema v1)
  scripts/core/sources.py         (cache loaders for parsed data)
  scripts/core/detectors.py (HebrewWordDetector, CrossRefDetector,
                              NaveTopicalDetector — χ.7)
  scripts/prospect.py / scripts/promote.py
  scripts/add_note.py / scripts/inject.py
  /sources console PD-cache section (υ.1)  Fetch / Force / Upload
                                           JSON / Clear per source +
                                           top-level Fetch all
  /api/sources/cache (GET) + /api/sources/cache/<id>/* (POST/DELETE)

PD CORPORA cached locally:
  content/sources/strongs_hebrew.json   (populated)
  content/sources/tsk_xrefs.json        (populated)
  content/sources/naves_topical.json    (zero-byte placeholder; χ.7)
  fetch_sources.py populates with network access.

POPUP LANGUAGES (ν.2.7):
  scripts/build_edition.py POPUP_LANGUAGES + resolver
  encode/decode_per_book_languages
  editions.yaml: popup_languages_default + popup_languages_per_book

COVERS (π.4 — full upload pipeline + UI):
  scripts/core/covers.py + scripts/web.py
  Routes: GET /covers, GET /content/covers/<path>, GET /api/covers,
          POST/DELETE /api/covers/<edition>/{main,book/<code>}

PREFLIGHT (ψ.2 + composes lint_rules):
  api_preflight aggregates 8 checks; rules_compliance is the linter
  Routes: GET /preflight, GET /api/preflight

EDITION CLONING (ν.4):
  api_clone_edition + _append_cloned_edition
  Route: POST /api/editions/clone

AUTH GATE (ω.4):
  Handler._check_admin_auth gates POST/PUT/DELETE
  Off by default; set EBIBLE_ADMIN_TOKEN env var to enable

RULES LINTER (ω.0.1 + ω.0.4):
  scripts/lint_rules.py — CLI + run_all() API, 8 checks
    6.1 canonical-order encoders
    6.2 cross-link invariant
    encode_decode round-trip
    docs cross-references
    freshness CHANGELOG vs SESSION_STATE mtime
    inflight (Tier 3 — IN_FLIGHT.md marker)
    untracked_phases (Tier 3 — code phases vs CHANGELOG)
    code_doc_sync (Tier 3 — consoles in inventory)

READER EXPERIENCE (ν.6 + ν.6.1 + ν.6.x — full loop):
  scripts/build_edition.py:
    CHAPTER_NUMBER_FORMATS, CHAPTER_NUMBER_DECORATIONS,
    BOOK_TOC_ORNAMENTS, chapter_number_to_word,
    format_chapter_label, decorate_chapter_label,
    apply_chapter_decoration, apply_reader_toc_transforms
  scripts/web.py: api_save_edition_meta validates 5 new fields
  /customize: "Reader experience" card with all controls

GUARDRAIL SYSTEM (ω.0.4):
  dev/IN_FLIGHT.md   tier-2 task tracker (HTML-comment marker)
  dev/CLAUDE_PROJECT_RULES.md §12 footnote (tier 1) + §13 (tier 4)
  scripts/lint_rules.py — 3 new tier-3 checks

CACHING (φ.1):
  scripts/web.py: _files_signature, _notes_dir_signature,
  _cached_attribution_audit, _cached_edition_diff,
  _cached_publisher_data, _cached_covers, _cached_preflight

ATOMIC WRITES:
  scripts/core/notes_io.py: atomic_write (text), atomic_write_bytes
  (binary), ensure_backup (pre-mutation snapshot)

HOUSEKEEPING:
  scripts/cleanup.py (dry-run by default; prunes __pycache__ +
  *.pyc + .backups/) — TODO: also prune exports/, epub_working/,
  builds/, content/candidates/ (all regenerable)
  scripts/bulk_inject.py (ω.0.7 — bulk-modify *_HTML constants)
  scripts/scaffold_console.py (ω.0.2 — single-command new-console
  bootstrap)
  tests/fixtures.py (ω.0.3 — shared test fixtures)

CORPUS GROWTH PIPELINE (χ cluster — pattern proven repeatable
across 4 detectors now):
  scripts/run_xref_at_scale.py    (χ.6  — TSK xrefs at scale)
  scripts/run_hebrew_at_scale.py  (χ.6+ — HebrewWord at scale; OT only)
  scripts/run_naves_at_scale.py   (χ.7  — Nave's Topical at scale)
  scripts/run_greek_at_scale.py   (χ.1  — GreekWord at scale; NT only)
  scripts/batch_promote_xrefs.py  (χ.6  — generic in-process batch
                                          promoter; --kind filter)

  Pattern for future χ.* phases (χ.2-5 commentaries):
    write detector class → write driver script iterating cached
    source data → run → batch_promote_xrefs.py --kind X.

CONSOLES (web UI) — all 13 cross-linked per Rule §6.2:
  /          note editor (different design, no console nav)
  /matrix    symbol toggle matrix view
  /sources   sources navigator
  /export    buyer-facing build flow
  /customize edition customization (chapter/ToC reader experience)
  /audit     attribution + quality audit
  /publisher publisher console
  /wizard    Bible Builder wizard
  /diff      sales-tool edition diff
  /compare   translation comparison view (ψ.4 — buyer demo)
  /covers    cover upload + per-book grid
  /preflight pre-ship readiness dashboard
  /apihelp   api reference
  /ops       operator dashboard
```

---

## In-flight notes

- **IN_FLIGHT.md is `idle`** at the time of this snapshot —
  χ.0 Kenyon ingest shipped (16 tests, +117 promoted notes,
  new `text-witness` kind). Corpus is now 16,042 / 25K v1.0 floor
  (8,958-note gap remaining). Next per the most-logical-path is
  **χ-AI-xrefs** (~$30-80 Anthropic API per pass; +5-15K thematic
  links; cost gate lifted 2026-05-08; mirrors the χ-cluster pattern
  with an LLM-backed detector). Then **ω.5 paths refactor → θ.1
  launcher → θ.2 native shell** for the v1.0 candidate. Audio
  (ρ.1) + buyer-arc polish (ψ.14) + reader-EPUB polish (ψ.17)
  ship as v1.x polish on a working v1.0 candidate.
  Parallel user-side free-roll (independent of my work): run
  `python scripts/fetch_sources.py` from any network-enabled
  shell to unblock χ.7 (+2-3K Nave's) + χ.1 (+5-10K Strong's
  Greek). Both pipelines already shipped infrastructure-wise.
  ω.14 epubcheck gate still degrading-to-warn until OpenJDK 8+
  is installed on this machine.
- **Preflight FAILs on cover paths** — placeholder paths in
  seeded editions.yaml. Fixable via /covers upload or /customize
  blank.
- **Auth gate is OFF by default.** Set EBIBLE_ADMIN_TOKEN env
  var to require Bearer tokens on POST/PUT/DELETE.
- **`exports/` is empty.** Run `python3 scripts/build_edition.py
  <id>` per edition to populate.
- **PD corpus `naves_topical.json` is missing** awaiting network
  fetch via `scripts/fetch_sources.py` (or manual JSON drop).
  `NaveTopicalDetector` skips gracefully via prospect.py's
  resilient instantiation; existing TSK + Strong's flows
  unaffected.
- **`_files_signature` is intentionally NOT lru_cached** (rebound
  to `_files_signature_impl`). Don't "optimize" by re-adding.
- **Pre-existing nav debt — matrix alias.** Consoles' "matrix"
  nav link points to `/`, not `/matrix`. Linter accepts both.

---

## Memory rules pinned (canonical list)

1. Save = present zip (never just on disk)
2. Pause at 7-min mark
3. When sequencing delegated, pick safest+foundational first
4. "Continue/push" is NOT a save command
5. Read dev/CLAUDE_PROJECT_RULES.md FIRST
6. Read dev/SESSION_STATE.md to get current state
7. On user topic-shift: audit working tree + IN_FLIGHT before
   responding (§13 — pivot is a close-the-loop signal, not an
   abandon signal)
