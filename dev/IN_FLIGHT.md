# In-flight work — current task tracker

<!-- TRACKER-STATE: idle -->

## Active task

*(none — tracker is idle. **ω.5 paths-resolver foundation**
shipped 2026-05-08. Built `scripts/core/paths.py` as the single
source of truth for project paths:
- `repo_root()` — read-only resource path (parent of scripts/);
  bundled into the desktop binary as a read-only template.
- `content_root()` — resolver with precedence: testing override
  > YHWH_CONTENT_ROOT env var > in-tree `<repo>/content/` IFF
  the editions.yaml marker exists (dev mode) > platform
  `user_data_root()` (installed mode).
- `user_data_root()` — Win `%APPDATA%\YHWH`, macOS
  `~/Library/Application Support/YHWH`, Linux
  `$XDG_DATA_HOME/YHWH` or `~/.local/share/YHWH`.
- Sub-path helpers cascade (notes/candidates/sources/translations/
  covers/audio + 7 yaml helpers); build-output siblings
  (exports/epub_working/builds/backups) cascade from
  `content_root().parent`.
- `lru_cache(maxsize=1)` on resolver; `reset_content_root()` busts
  cache; `set_content_root_for_testing(p)` bypasses cache for
  tests.

Migrated the 5 `scripts/core/` modules (sources, translations,
config, covers, traditions) to expose paths-resolver entrypoint
helpers (`_sources_dir`, `_translations_dir`, `_books_yaml_path`,
`_covers_dir`, `_traditions_yaml_path`) without removing existing
back-compat constants — every existing PATH-monkeypatch test
continues passing.

Wrote `scripts/migrate_to_user_data.py` one-shot bootstrap helper
(idempotent; `--dry-run` previews; `--force` overwrites; refuses
on missing source; short-circuits "Already migrated" when
destination has the editions.yaml marker — safe to call from a
launcher's first-run flow).

+32 tests across 6 new classes (TestPathsRepoAndUserData,
TestPathsContentRootResolver, TestPathsSubPathHelpers,
TestPathsCacheBehavior, TestCoreModulesUsePathsResolver,
TestMigrateToUserData). End state: **783 tests green, 10/10
linter clean, 16,042 notes**.

Remaining 41 call-site files (web.py + at-scale drivers + CLI
tools) get migrated as rolling sub-phases **ω.5.1+** on whatever
cadence makes sense; the in-tree fallback in the resolver keeps
un-migrated sites working unchanged during the roll.

Next per the most-logical-path: **θ.1 launcher → θ.2 native
shell** for the v1.0 candidate. ω.5 unblocks θ — bundled
.app/.exe payloads can now find user-mutable data at
`paths.content_root()` while keeping read-only resources in the
bundle. Apple Developer ID becomes load-bearing at θ.2 (per
memory `feedback_license_flagging.md`); flag again when θ.2 is
the next phase.

Prior ship this session — **τ.1 WEB (infrastructure) + χ.0+
deep-dive scope**. Two-part ship:

τ.1 generalised `scripts/extract_translation.py` behind a
`TRANSLATIONS` registry — KJV folded in verbatim (byte-identical
_meta.yaml modulo regenerated `fetched` date), WEB added as the
first non-KJV entry (`https://eBible.org/eng-web/`,
`eng-web_vpl.zip`). New `meta_for()` helper composes the
_meta.yaml dict from the registry; unregistered ids fall back to
a stub with an explicit "promote to registry before publishing"
notes field. New `--list` CLI flag dumps registered entries.
+7 tests in `TestTranslationsRegistry`. Corpus delta 0 — data
fetch is user-side (download eBible's ZIP → unzip into
`content/translations/sources/web/` → re-run extractor).

χ.0+ scope addendum at `dev/SCOPE_2026-05-08-addendum-textcrit-
deep-dive.md` stages the next four textual-criticism ingests
mirroring χ.0 Kenyon: χ.0.1 W&H 1881 (W&H Vol II Introduction,
~600pp NT prose), χ.0.2 Burgon 1883 (*The Revision Revised*),
χ.0.3 Souter 1913 (*Text and Canon of the NT*), χ.0.4 Driver
1890 (*Notes on the Hebrew Text of Samuel* — fills OT side).
Each ~1 session; reuses `text-witness` kind +
`KenyonReferenceDetector` pattern. Conservative cumulative yield
~360-720 promoted notes after reviewer curation. Per-source
shipping (omnibus rejected). All sources PD, archive.org-accessible
via the user's existing account.

End state: **751 tests green, 10/10 linter clean, 16,042 notes**.

Prior ship this session — **χ-AI-xrefs (infrastructure)** — the
first χ-cluster detector backed by an API rather than a static
cached source. The data fetch is paid + user-side (~$0.09/100v;
~$28 full 31K-verse pass with Haiku 4.5 + prompt caching),
identical contract to χ.7 / χ.1's "infra-shipped, fetch-pending"
parking pattern but with a real cost dial. Built:

- new `xref-thematic` kind in `content/kinds.yaml` (category=xref;
  symbol ‖ inherited; phase=mvp; distinct from xref-citation /
  xref-allusion / xref-inner-biblical — captures AI-proposed
  thematic, typological, and idiomatic links the static χ sources
  miss)
- `AnthropicXrefClient` in `scripts/core/sources.py`: lazy +
  injectable `completion_fn`; `SourceMissingError` when no
  ANTHROPIC_API_KEY + no injected fn (mirror of NaveTopical's
  graceful-degrade contract — `prospect.py`'s resilient
  instantiation handler catches and skips); singleton via
  `anthropic_xref_client()` lru_cache; `propose_xrefs()` validates
  target against `config.books_by_code()`, clamps confidence to
  [0,1], defensively returns `[]` on malformed completion. Default
  real-SDK call uses prompt caching on the system prompt
  (`cache_control: ephemeral`) for ~10× cost reduction across
  per-verse calls. Default model `claude-haiku-4-5-20251001`.
- `AIXrefDetector` in `scripts/core/detectors.py`: emits
  `xref-thematic` candidates; registered in `ALL_DETECTORS`;
  attribution string contains "Claude AI" (provenance invariant);
  body composes target-link + reasoning + explicit
  `[Reviewer: AI-proposed]` flag.
- `scripts/run_ai_xrefs_at_scale.py` driver mirroring
  `run_greek_at_scale.py` with cost guards: `--dry-run` prints
  projected cost & exits without API call; `--max-verses N`
  default 100 (hard cap); `--confirm-cost` required when
  `--max-verses > 200` (`CONFIRM_COST_THRESHOLD`); `--model`
  passthrough; `--top-n` / `--min-confidence` passthrough;
  merge-not-clobber output (preserves prior detector candidates,
  replaces only `kind=xref-thematic` entries on re-run).
- spec at `dev/SCOPE_2026-05-08-addendum-ai-xrefs.md`
- +28 tests across `TestAnthropicXrefClient` (8) +
  `TestAIXrefDetector` (9) + `TestRunAIXrefsAtScaleDriver` (10) +
  one kinds.yaml smoke; **744 tests green, 10/10 linter clean,
  16,042 notes** (corpus delta is 0 until the user runs the paid
  driver — same contract as χ.7 / χ.1).

User-side completion (parked, paid):
1. `export ANTHROPIC_API_KEY=...` and `pip install anthropic`
   (one-time setup for this machine)
2. `python3 scripts/run_ai_xrefs_at_scale.py --dry-run` to see
   projected cost
3. Smoke: `python3 scripts/run_ai_xrefs_at_scale.py --books jhn
   --max-verses 50` (~$0.05)
4. Pauline slice: `python3 scripts/run_ai_xrefs_at_scale.py
   --books rom,gal,eph,php,col,heb --max-verses 1000
   --confirm-cost` (~$0.92)
5. Full pass: `python3 scripts/run_ai_xrefs_at_scale.py
   --max-verses 31000 --confirm-cost` (~$28)
6. `python3 scripts/batch_promote_xrefs.py --kind xref-thematic`
   to promote (reviewer-curated; conservative yield ~5K notes
   alone closes ≈half of the 8,958-note v1.0 corpus floor gap).

Next per the most-logical-path: **ω.5 paths refactor → θ.1
launcher → θ.2 native shell** for the v1.0 candidate. Audio
(ρ.1) + buyer-arc polish (ψ.14) + reader-EPUB polish (ψ.17)
ship as v1.x polish on a working v1.0 candidate.

Parallel user-side free-roll (independent of my work): run
`python scripts/fetch_sources.py` from any network-enabled shell
to unblock χ.7 (+2-3K Nave's) + χ.1 (+5-10K Strong's Greek). Both
pipelines were infrastructure-shipped earlier this session.)*

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
