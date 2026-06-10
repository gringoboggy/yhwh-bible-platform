# Round-7 audit findings — 2026-06-10 (the program everything-audit, win-solo overnight)

**Status:** FINDINGS CAPTURED 2026-06-10 — triage is verify-first (re-check every survivor vs live code before fixing; prior rounds: ~40% already-fixed/misdescribed; an adversarially-verified plan can still be wrong — mint-11 P6).

Run `wf_1468532d-6f8` · engine round 7 (25 dims, incl. the 7 new program dims) · 158 agents · ~8.8M subagent tokens · ~7.1h · **107 deduped -> 75 survivors / 32 refuted · 0 UNVERIFIED** · severity: 5 high / 16 medium / 46 low / 8 info.
Raw result (full evidence + verifier reasoning + refuted list): `2026-06-10-round7-audit-raw.json`. Synth fixes-plan embedded below.

## Survivors by dimension

| Dimension | n | | Dimension | n |
|---|---|---|---|---|
| claude-setup | 11 | | website-deploy | 3 |
| github-gitlab | 6 | | concurrency-caching | 2 |
| future-work | 6 | | correctness | 2 |
| docs | 6 | | data-validity | 2 |
| decommission | 5 | | opt-build | 2 |
| lane-system | 4 | | rx-surfaces | 2 |
| popup-integrity | 4 | | opt-ingest | 2 |
| code-debt | 4 | | tests-run | 1 |
| opt-render | 4 | | opt-vision | 1 |
| dist-packaging | 3 | | byte-stability | 1 |
| tests | 3 | | stack-review | 1 |

## The 5 HIGHs (full evidence in the raw JSON)

### [tests-run] Two @lru_cache decorated functions lack clear paths and are not whitelisted
`scripts/.cache_audit_whitelist.py`

Test `test_audit_clean_state_on_real_tree` (tests/test_audit_caches.py:189) reports:
  - scripts/build_edition.py:1994  _kind_default_labels
  - scripts/build_edition.py:2155  _topic_vocab
Both functions are decorated with `@lru_cache(maxsize=1)` but have no `.cache_clear()` call sites in the codebase (audit_caches.py confirms via regex scan of scripts/ and tests/).

**Fix:** Add the following two entries to scripts/.cache_audit_whitelist.py, either in the existing "Read-once singletons over immutable manuscript / canonical data" section (lines 49-58) or in a new section after line 72 (after the compiled-regex section). The finder's proposed text is correct:\n\n```\n# ---- Read-once singletons over immutable config/source data ----\n# §7.1 \"project-internal published data\" tier: kinds.yaml and Nave's/Torrey\n# topic JSON files are immutable within a process (updates via git commit +\n# restart). The cache IS the value — clearing would only force identical re-reads.\n_._kind_default_labels  # scripts/build_edition.py:2028 — normalized kind labels from kinds.yaml\n_._topic_vocab         # scripts/build_edition.py:2189 — Nave's + Torrey topic names from JSON files\n```\n\nAlternatively, if preferring to extend the existing §7.1 block (lines 49-58), append afte …[raw JSON]

### [concurrency-caching] web_helpers.py: write_book() and _notes_dir_signature() use NOTES_DIR constant — writes crash in frozen binary; mtime signature reads wrong directory
`scripts/web_helpers.py:29, 64, 67, 159`

Line 29: `NOTES_DIR = REPO / "content" / "notes"`. Line 159 in `write_book()`: `path = NOTES_DIR / f"{book_code}.py"` followed by `notes_io.ensure_backup(path)` and `notes_io.atomic_write(path, ...)`. Line 64+67 in `_notes_dir_signature()`: `if not NOTES_DIR.is_dir(): return ()` / `for f in NOTES_DIR.iterdir()`. In the frozen binary after ω.5 migration, notes live in `user_data_root/content/notes/`. `write_book()` attempts to write into `sys._MEIPASS/content/notes/` (the read-only PyInstaller bundle), which raises PermissionError on Windows — the editor save path is completely broken in the desktop app. `_notes_dir_signature()` reads mtimes from the bundle copy rather than the user-data copy, so the signature never changes after user edits, and every mtime-keyed endpoint cache derived from it (`@lru_cache` callers passing the signature) never invalidates. No `paths.notes_dir()` delegation exists in this module and it has no coverage in `test_paths_omega5.py`.

**Fix:** Two-part fix (both required; part 1 is the root cause, part 2 applies after part 1):

**Part 1 — `scripts/core/paths.py`, `_detect_in_tree_content()` (the root cause):**

Add a `sys.frozen` guard identical to the one already in `_build_output_root()`:

```python
def _detect_in_tree_content() -> Path | None:
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller binary: repo_root() points at the
        # read-only _MEIPASS bundle, which also contains a bundled
        # content/ template.  Returning it here would make content_root()
        # resolve to the read-only bundle instead of user_data_root().
        # Skip in-tree detection entirely when frozen so the resolver
        # always falls through to user_data_root() — same logic as
        # _build_output_root() line 269.
        return None
    candidate = repo_root() / "content"
    if (candidate / "editions.yaml …[raw JSON]

### [dist-packaging] gen_checksums.py DEFAULT_EXTS omits .epub — EPUB and kepub assets silently excluded from SHA256SUMS
`scripts/gen_checksums.py:26`

`DEFAULT_EXTS: tuple[str, ...] = (".exe", ".dmg", ".AppImage", ".msi", ".zip", ".tar.gz")` — `.epub` is absent. The six v0.1.0 asset families include the EPUB (`Ethiopian_Bible_ethiopian-tewahedo_…_.epub`) and kepub (`…_.kepub.epub`), both ending in `.epub`. When `notary_autofinish.sh` calls `gen_checksums.py dist --out dist/SHA256SUMS.txt` with no `--ext` override (line 67 of that script), or when the tool is run bare, EPUB/kepub assets are silently skipped. The project's own release master plan (`dev/docs/superpowers/plans/2026-06-08-v0.1.0-master-plan.md:125`) lists this as a planned but not-yet-applied fix: `gen_checksums.py .epub fix`. Every future release run without the explicit override produces a SHA256SUMS that is incomplete by two of the six shipped asset families.

**Fix:** Add `.epub` to DEFAULT_EXTS at scripts/gen_checksums.py line 26:

`DEFAULT_EXTS: tuple[str, ...] = (".exe", ".dmg", ".AppImage", ".msi", ".zip", ".tar.gz", ".epub")`

No other changes needed. The notary_autofinish.sh invocation on line 67 will then automatically include EPUB/kepub assets without any script edit. Callers that already pass `--ext` explicitly are unaffected.

### [dist-packaging] notary_autofinish.sh hardcodes stale artifact name (YHWH-1.0.0-beta.1.dmg) and stale Mac repo path — will staple the wrong file on next use
`dev/notary_autofinish.sh:21-22`

`REPO="/Volumes/MacHD2/yhwh-bible-platform"` and `DMG="$REPO/dist/YHWH-1.0.0-beta.1.dmg"`. The `beta.N` versioning scheme was retired at v0.0.3 (VERSION file + CHANGELOG confirm this). The current release is v0.1.0, whose DMG is `YHWH-0.1.0.dmg`. The old Mac path `/Volumes/MacHD2/yhwh-bible-platform` refers to the iMac's spinning-disk volume that was fully wiped on 2026-06-02 (memory `reference_hardware_box_and_mac`). `NOTARIZATION_STATUS.md` confirms the script was last used for `YHWH-1.0.0-beta.1.dmg` (v0.0.3); v0.1.0 was notarized manually. If run for v0.1.1+, the script will call `xcrun stapler staple` and `gen_checksums.py` against a nonexistent file, silently succeeding the `STATE: DONE` idempotence guard from v0.0.3 (line 45: `if grep -q "STATE: DONE" "$STATUS"`). The master plan (`docs/superpowers/plans/2026-06-08-v0.1.0-master-plan.md:125`) lists the fix as deferred.

**Fix:** The finder's fix is correct. Apply it exactly as proposed:

1. Replace line 21-22 with:
   REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.."; pwd)"
   VERSION="$(head -n1 "$REPO/VERSION" | tr -d '[:space:]')"
   DMG="$REPO/dist/YHWH-${VERSION}.dmg"

2. Scope the idempotence guard at line 45 to the current DMG's basename so a new-version run is not skipped because a prior version left STATE: DONE:
   if grep -q "STATE: DONE" "$STATUS" 2>/dev/null && grep -q "$(basename "$DMG")" "$STATUS" 2>/dev/null; then exit 0; fi

Severity is medium (not high): the blast radius is a silent no-op on the mac lane, not shipped-artifact corruption. The 9 KJV editions are unaffected; this is a mac-only build-helper script.

### [lane-system] save_mac.sh uses `git commit -am` which silently omits new untracked files
`dev/save_mac.sh:32-37`

Lines 32-37: `if git diff --quiet && git diff --cached --quiet; then echo 'tree clean'; … git commit -am "$MSG"`. Both the clean-check (`git diff`) and the commit (`-am`) only see TRACKED files. A Mac session that creates any new file (e.g., `docs/superpowers/notes/2026-06-10-*.md`, new store, new spec) will see the dirty check pass as 'clean' and skip the commit, OR reach `git commit -am` which stages only tracked-file modifications — leaving the new files out. The Windows equivalent (`save.ps1:19`) uses `git add -A`, which stages everything. The Mac lane regularly creates new notes/spec files each session per the LANE_HANDOFF.md history.

**Fix:** Replace lines 31-39 of dev/save_mac.sh with:

```bash
# Leg 1 — commit all changes (tracked + untracked) if a message was given.
if [ -n "$MSG" ]; then
  git add -A
  if git diff --cached --quiet; then
    echo "save_mac: tree clean — nothing to commit."
  elif [ "$DRYRUN" = 1 ]; then
    echo "[dry-run] would: git commit -m \"$MSG\""
  else
    git commit -m "$MSG"
  fi
fi
```

The key changes: (1) `git add -A` before the dirty check so untracked files are staged; (2) dirty check becomes `git diff --cached --quiet` (checks the index, which now includes untracked files that were just added); (3) `git commit -m` instead of `git commit -am` (the `-a` flag is redundant and misleading after an explicit `git add -A`). This mirrors save.ps1's approach exactly.

## Completeness-critic gaps (round-8 lenses)

- **add_vnote_preview_separators (K-R4-1 fix) — zero test coverage** — The round found K-R4-1 (the vnote separator insert) and the vnote-empty placeholder skip (346 paragraphs with class 'vnote-text vnote-empty' that _VNOTE_SEP_TEXT_RE does not match). No test file exercises add_vnote_preview_separators or apply_vnote_preview_separators at all — Grep of tests/ for those names returns only test_marker_style.py (which calls apply_badge_markers, not the vnote pass). The double-¶ finding (S1: 2,970 base asides already start with ¶) and the vnote-empty skip are both in the survivor list but are not tested. The entire K-R4-1 code surface (build_edition.py:1922–1947) has no dedicated test class pinning idempotency, empty-placeholder handling, or double-¶ avoidance. Lens: Grep tests/ for 'add_vnote_preview_separators' and 'apply_vnote_preview_separators'; expect 0 hits. Write a synthetic unit test class in tests/test_kobo_vnote_separators.py that (a) asserts a plain vnote-text paragraph gets exactly one ¶ prefix, (b) asserts vnote-empty paragraphs are left untouched (the separator MUST NOT be inserted before them), (c) asserts the pass is idempotent (re-running does not double-insert), and (d) asserts vnote-source-label paragraphs get the ◦ prefix.
- **scripts/core/preview.py — REPO-relative NOTES_DIR and THEMES_DIR constants used by _load_book_notes() and _read_theme_css()** — The round found the frozen-binary bug (finding: 'preview.py: _load_book_notes() and _read_theme_css() use REPO-relative NOTES_DIR/THEMES_DIR constants — reads stale bundle data in frozen binary') but did NOT check whether the paths.py resolver is actually wired anywhere in preview.py. Reading preview.py:50-70 confirms REPO and THEMES_DIR are module-level constants derived from __file__, not from paths.notes_dir() / paths.themes_yaml(). The test coverage gap is: no test exercises render_chapter_preview with a set_content_root_for_testing() override to confirm the resolver is invoked; because preview.py does NOT call paths.*_dir() at all, such a test would catch the regression. The finding title says the bug exists — the gap is there is zero test pinning the fix target, so a partial fix (e.g. migrating only translations but not NOTES_DIR) would pass CI silently. Lens: In tests/test_preview_paths.py, use set_content_root_for_testing(tmp_path) to point at a synthetic content root containing a minimal gen.py notes file and a themes/light.css, then call render_chapter_preview('ethiopian-tewahedo', 'gen', 1). Assert it returns status='ok' and that the notes from tmp_path appear (not from the repo-root notes dir). This pins that NOTES_DIR and THEMES_DIR in preview.py resolve through the paths.* API.
- **scripts/core/translations.py — _book_path() uses module-level TRANSLATIONS_DIR constant, not paths.translations_dir()** — The round found 'translations.py: four public functions use hardcoded TRANSLATIONS_DIR, bypassing the paths.translations_dir() resolver.' The _book_path() helper at line 54-55 constructs the per-book path using TRANSLATIONS_DIR (the module-level constant) not paths.translations_dir(). The _translations_dir() ω.5 shim exists at line 39-46 but is never called by _book_path(). There is no test in test_translations_tau*.py that invokes get_verse with a set_content_root_for_testing() override; all tests use the real corpus. This means a frozen-binary test for the translations path resolver is absent. The bug exists in production and is untested. Lens: In tests/test_translations_tau6.py (or a new test_translations_paths.py), add a class TestTranslationsPathsResolver that calls set_content_root_for_testing(tmp_path), writes a synthetic geez-tewahedo/gen.py with VERSES=[(1,1,'test')], calls translations.get_verse('geez-tewahedo','gen',1,1), and asserts it returns 'test'. This will FAIL until _book_path() is migrated to call _translations_dir() / translation / f'{book_code}.py'. Run alongside test_paths_omega5.py.
- **bookcode_canonical lint — commentary JSON files contain legacy book codes ('joh','mar','ps') that are screened by data-normalisation at load time but still stored in dataclass .book fields** — The round found 'bookcode_canonical lint rule has coverage gap: all 5 commentary JSON data files contain legacy book codes ("joh", "ps") that are unscreened.' Confirmed by Grep: protestant_commentaries.json, reformation_commentaries.json, rabbinic_commentaries.json, catholic_commentaries.json and ethiopian_commentaries.json all contain '"book": "ps"', '"book": "joh"', '"book": "mar"'. While _CommentaryCorpus._load() normalizes the INDEX KEY (line 316: key = (_normalize_book_code(obj.book), ...)), it stores the raw legacy string in obj.book. The bookcode_canonical lint does NOT screen these 6 JSON files — only Python dicts (MAP_SPECS / LIST_SPECS). A round-8 lens should check whether obj.book legacy values leak into promoted note attributions or debug logs, and add the 6 JSON paths to the lint's screened set. Lens: Extend check_book_codes_canonical in scripts/lint_rules.py to scan the 'book' field values in all 6 *_commentaries.json files under content/sources/ and fail if any value is in the _BOOK_CODE_ALIASES key set. Separately, verify that _CommentaryCorpus stores _normalize_book_code(obj.book) in obj.book at construction time (not just in the index key) to eliminate the stale-field risk. Run Grep for '"book": "(joh|jol|php|jas|nam|ezk|mar|ps)"' across all content/sources/ to confirm the full class count.
- **scripts/build_edition.py _strip_notes_sections — empty <section class='verse-refs-section'> wrapper left behind after vnote harvesting** — The surviving finding 'S1: _strip_notes_sections leaves an empty <section class="verse-refs-section"> wrapper after vnote harvesting' is in the round-7 list. _EMPTY_NOTES_SECTION_RE at line 2860 matches only '<aside class="notes-section"…', not the '<section class="verse-refs-section"…' containers. After _strip_notes_sections runs, any file whose vnotes lived entirely inside a verse-refs-section rather than a notes-section leaves an empty <section> element. There is no test in test_file_split.py or tests/ that places a verse-refs-section in the synthetic HTML and asserts it is cleaned up. The SYNTH fixture in test_file_split.py only uses notes-section. Lens: Add a variant of SYNTH in tests/test_file_split.py (or a new tests/test_strip_notes_sections.py) that uses '<section class="verse-refs-section"…' as the container. Call _strip_notes_sections() directly and assert the empty wrapper is removed. Also add a complementary _EMPTY_VERSE_REFS_SECTION_RE alongside _EMPTY_NOTES_SECTION_RE in build_edition.py and apply it in _strip_notes_sections() to close the gap. Confirm no empty-section residuals survive with an epub_working-wide scan: Grep epub_working for '<section class="verse-refs-section"[^>]*>\s*</section>'.
- **K-R4-2 (Kobo popup-decline class) — no test coverage for the threshold mechanism or the 'large aside' code path** — K-R4-2 (preview-decline threshold 3,313 < T <= 7,748 stripped chars causes Kobo to navigate to file start instead of showing popup) is in the deferred-by-design list (#10) BUT 'the popup-integrity dimension must EXTEND beyond them' is the explicit instruction. Round 7 found 30,148 merged + 36,535 vnote asides exceed the threshold in v0.1.0. No test currently measures the stripped-char length of any built aside or asserts a maximum; there is no automated regression guard to detect if a new note kind or a data change pushes more asides over the threshold. The entire 'aside stripped-text length' dimension was found via device-QA, not automated testing. Lens: Add a test class TestKoboAsideStrippedLength in tests/ that (a) loads the base epub_working/index_split_001.html (Genesis, dense with notes), (b) for each <aside class='vnote'> strips all tags and counts characters, and (c) asserts the count <= 7748 (the confirmed decline threshold). This converts the device-QA finding into an automated regression gate. The test will initially fail for gen 1:1 (9,434 stripped) and gen 1:26 (7,748 stripped), proving the class size and targeting which asides need truncation or the navigate-fix arc.
- **Versification remap correctness — normalize_coord() is identity for all versions; the LXX/Vulgate/WLC coord divergences are NOT tested in any translation ingest test** — scripts/core/popup_versions.py normalize_coord() at line 153-160 returns identity (book, ch, vs) for every version including wlc/lxx-greek/vulgate — the comment says 'B1: identity for every version. Phases 2-3 add per-source remap tables here.' There is no test file named test_versification*.py at all (Glob returns no results). The versification.py module contains parse_versemap + wlc_to_kjv_map logic but the only consumer that calls normalize_coord is generate_verse_popups.assemble_versions_for_verse, and there is no test that exercises a non-identity remap coordinate (e.g. Psalm superscriptions at WLC Ps.3.1 vs KJV Ps.3 title). If a future remap table is added to normalize_coord, there is zero regression coverage to catch off-by-one errors. Lens: Create tests/test_versification.py with: (a) a test that parse_versemap(VERSE_MAP_XML_PATH) returns at least one (wlc_coord, kjv_coord) pair for a known Psalm superscription entry (Ps.3.0 → Ps.3.1 or similar); (b) a test that the round-trip wlc_to_kjv_map contains Gen.31/32 boundary entries; (c) a test that lxx_swete_to_kjv_map contains the Jeremiah OAN reorder entry. These are the three 'verified manually against KJV' remap claims in MATRIX_MAP.md that currently have no machine-verifiable pin.
- **scripts/core/build_cache.py _PIPELINE_SCRIPTS list — completeness not guarded against new core module additions** — The build cache lists _PIPELINE_SCRIPTS by name and must be updated whenever a new module is added to the build-path core. TestCacheCoverageGuard in tests/test_build_cache.py is supposed to catch this, but there is no evidence in the round-7 findings that the guard was actually run and passed. The round's 'byte-stability: 1/3' result suggests only 1 of 3 byte-stability dimensions was verified. If a new module is imported by build_one but not in _PIPELINE_SCRIPTS, the content-addressable cache serves stale EPUBs silently. The build cache finding 'test_byte_stability_gate uses wrong edition for byte-stability check — actual flagship never tested' (flagship=_EDITIONS[1]=catholic-study) means the real flagship (ethiopian-tewahedo) has never had its byte-stability asserted by the slow gate. Lens: Run tests/test_build_cache.py::TestCacheCoverageGuard specifically and report its output. Also inspect the test at line 92 of test_byte_stability_gate.py: 'flagship = _EDITIONS[1]  # catholic-study' — change to 'flagship = _EDITIONS[0]  # ethiopian-tewahedo' to pin the correct flagship. Separately, do a transitive import trace of build_one's imports (scripts/build_edition.py → matter_pages.py → epub_utils.py → resync_marker_glyphs.py → build_epub.py → style_config.py → inject.py + all core/ imports) and cross-reference with _PIPELINE_SCRIPTS to confirm no module was added since the last coverage audit.
- **ω.5 paths.py migration — 25+ scripts still use REPO_ROOT / 'content' / 'notes' hardcoded paths, not paths.notes_dir()** — The round captured the frozen-binary crash for web_helpers.py and preview.py specifically, but the Grep of NOTES_DIR = REPO_ROOT / 'content' / 'notes' shows 25 files still use this pattern (inject.py, promote.py, build_edition.py:3 sites, dashboard.py, bibliography.py, etc.). The ω.5 migration is documented as 'rolling' but no test enforces the complete migration for a specific class of production scripts. TestCoreModulesUsePathsResolver in test_paths_omega5.py is supposed to pin core/ modules, but the 25 non-core scripts/ files are not in scope. In a frozen binary, every one of those 25 hardcoded REPO_ROOT / 'content' / 'notes' paths resolves correctly in dev but wrong in the installed binary's user-data dir. The build_edition.py sites (lines 132, 175, 545, 2162, 4077) are especially critical because they run during every EPUB build. Lens: Grep scripts/ for 'REPO_ROOT / .content. / .notes' and 'REPO / .content. / .notes' (excluding test fixtures and one-shot scripts). For each hit in a production code path (build_edition.py, inject.py, promote.py, web_editions.py, web_content.py, dashboard.py), verify whether it is in the ω.5 migration backlog and add a lint_rules check 'no_hardcoded_content_notes_path' that fails if any new site is added. The TestCoreModulesUsePathsResolver class in test_paths_omega5.py should be extended to cover the build pipeline scripts, not just core/.

## Synthesized fixes plan (verbatim from the run; VERIFY-FIRST before executing)

## Deep-Audit Round 7 — Phased Fixes Plan (v0.1.0 → v0.1.1 window)

## Executive summary

Round 7 deduplicated to **107 findings**, of which **75 verified survivors / 32 refuted** (0 UNVERIFIED — every survivor passed an adversarial skeptic panel). By severity: **5 high, 16 medium, 46 low, 8 info**; by kind, **59 bug/correctness/security/debt/test/doc findings and 16 optimization recommendations**. The most serious cluster is frozen-binary path resolution (`web_helpers.py` writes into the read-only PyInstaller bundle — the desktop app's editor save path is broken, and the mtime cache signature never invalidates) plus release-tooling staleness (`gen_checksums.py` silently omits `.epub` assets from SHA256SUMS; `save_mac.sh` silently drops untracked files; `notary_autofinish.sh` targets a retired beta.1 artifact). Overall health is strong: zero critical findings, the shipped v0.1.0 artifacts are unaffected, the build pipeline's parallelism/caching audit returned confirm-optimal, and the bulk of the volume is doc/copy drift left behind by the v0.1.0 release sweep.

## Phased fixes

Ordering: additive guards first → frozen-binary data-loss class → release/lane tooling → CI/repo hygiene → build-path correctness (byte-stability proofs) → tests → public-copy sweep (one deploy) → truth-record/Claude-setup hygiene. Duplicate findings merged where noted (Java-8 ×2, build-linux tag ×2, deep-audit-continue ×2, empty verse-refs-section ×2, README version/count ×2, count-sweep ×5).

### Phase 1 — Additive guards & lints (zero behavior change)

- [ ] **HIGH** — Whitelist the two clear-path-less `@lru_cache` functions — `scripts/.cache_audit_whitelist.py` — add `_._kind_default_labels` (build_edition.py:2028) + `_._topic_vocab` (build_edition.py:2189) under the read-once-singleton §7.1 tier with the rationale comments as drafted. Guard: existing `tests/test_audit_caches.py::test_audit_clean_state_on_real_tree` goes green. Build path: **no**. (Note: if Phase 5 item "drop `_kind_default_labels` lru_cache" is chosen instead, omit that whitelist line.)
- [ ] **MEDIUM** — Add `_emit_extent_ok` guard to the one driver missing it — `scripts/run_ethiopian_at_scale.py:54-97` — import `coord_in_canonical_extent`, define `_emit_extent_ok`, filter `cands` before `chapter_candidates.extend()` (exactly as the 4 sibling drivers; Tewahedo-distinctive books pass via the no-shape path). Guard: extend `tests/test_mint11_phase3.py` to assert `mod._emit_extent_ok` exists for the ethiopian driver too. Build path: **no** (staging only). *Class swept: 5 of 5 at-scale accumulator drivers now guarded.*
- [ ] **LOW** — Close the `bookcode_canonical` lint coverage gap — `scripts/lint_rules.py:2157-2187` — add the JSON-scanning tier over the 5 `content/sources/*_commentaries.json` files (imports inside the function body, consistent with line 2139); accompany with an in-place normalization of the legacy codes (`"joh"→"jhn"`, `"ps"→"psa"`) in the 5 JSONs as cleanup. Guard: the lint itself (commit-time, preferred over pytest-only — this invariant recurs every ingest, ★BUGCLUSTER). Build path: **no** (runtime already normalizes; built bytes unchanged — confirm with a spot regen if the JSONs are edited).
- [ ] **LOW** — Add MEMORY.md index byte-budget check — `dev/cc-hooks/memory_hygiene.py` — `MEMORY_INDEX_BYTES_BUDGET = 24_000` constant + the `index_bytes_budget` issue in `audit()` (the acute overrun is already trimmed; this prevents silent platform truncation recurring). Guard: the check is the guard. Build path: **no**.

### Phase 2 — Frozen-binary path resolution (silent-data-loss class — sweep all sites)

- [ ] **HIGH** — Frozen binary writes/reads wrong content root — root cause `scripts/core/paths.py::_detect_in_tree_content` + secondary `scripts/web_helpers.py:29,64,67,159` — Part 1: add the `sys.frozen` early-return guard to `_detect_in_tree_content()` (mirrors `_build_output_root()` line 269) so `content_root()` → `user_data_root()` when frozen. Part 2: `write_book()` and `_notes_dir_signature()` switch to call-time `paths.notes_dir()`; keep module-level `NOTES_DIR` as a legacy re-export only (never in a write or mtime path). Guard: add frozen-mode tests to `tests/test_paths_omega5.py` covering `content_root()` under a fake `sys.frozen`, plus coverage for `write_book`/`_notes_dir_signature` under `set_content_root_for_testing`. Build path: **no** (desktop-app runtime; 9 KJV editions byte-stable, no schema change).
- [ ] **LOW** — Same class, preview module — `scripts/core/preview.py:51-52,70,78` — remove `THEMES_DIR`/`NOTES_DIR` constants; `_read_theme_css()` → `paths.content_root() / "themes" / …` (no `paths.themes_dir()` exists), `_load_book_notes()` → `paths.notes_dir() / …` (lazy imports, matching the module's deferred-import style). Guard: fold into the same test_paths_omega5 additions. Build path: **no**. *Class swept: web_helpers + preview are the remaining frozen-hostile constant users; `translations.py` (same class, filed as optimization) is scheduled in the table below — do them in one pass.*

### Phase 3 — Release & lane tooling (stale-artifact / dropped-work prevention)

- [ ] **HIGH** — SHA256SUMS silently omits EPUB/kepub — `scripts/gen_checksums.py:26` — add `".epub"` to `DEFAULT_EXTS`. Guard: a small unit test asserting `.epub`/`.kepub.epub` files in a tmp dist dir appear in the output. Build path: **no** (release tooling).
- [ ] **HIGH** *(verifier-effective medium)* — notary script targets retired beta.1 DMG + wiped Mac path — `dev/notary_autofinish.sh:21-22,45` — derive `REPO` from `BASH_SOURCE`, read `VERSION` file, `DMG="$REPO/dist/YHWH-${VERSION}.dmg"`; scope the `STATE: DONE` idempotence guard to the current DMG basename. Guard: none feasible on Windows; verify on the Mac lane before the next notarization. Build path: **no** (mac-only helper).
- [ ] **HIGH** — `save_mac.sh` drops untracked files — `dev/save_mac.sh:32-37` — `git add -A` before the dirty check; check `git diff --cached --quiet`; commit with `-m` (drop `-a`), mirroring `save.ps1`. Guard: dry-run mode exercise on the Mac lane. Build path: **no**.
- [ ] **MEDIUM** — `save_mac.sh` mid-rebase abandonment — `dev/save_mac.sh:43-47` — explicit conditional with `git rebase --abort` + exit 1 on pull failure (the explicit-conditional form, not `trap ERR`), mirroring `save-all.ps1:89-91`. Guard: same dry-run exercise. Build path: **no**.
- [ ] **LOW** — `save.ps1` false "no remote configured" message + dead push block — `save.ps1:36-44` — replace with the truthful "leg-1 only; push is save-all.ps1" comment + message; delete the commented-out `git push`. Build path: **no**.
- [ ] **LOW** — `dev/NOTARIZATION_STATUS.md` records beta.1, not v0.1.0 — update to record submission `27aedc8a` (accepted) and `YHWH-0.1.0.dmg`; add Mac-only header comments to the three `notary_*.sh` scripts (or move to `dev/mac-only/`). Build path: **no**.

### Phase 4 — CI / repo hygiene

- [ ] **MEDIUM** *(merged ×2)* — `build-linux.yml` dispatch default targets nonexistent release — `.github/workflows/build-linux.yml:17` — `default: "v0.1.0"` + inline "update when cutting a release" comment; add the pre-upload `gh release view "$TAG" || exit 1` validation step (converts silent partial failure into loud abort); refresh the stale scaffold header comment. Build path: **no**.
- [ ] **LOW** — appimagetool fetched from rolling `continuous` tag — `.github/workflows/build-linux.yml:51` — pin a versioned tag if upstream publishes one; otherwise add the post-curl `sha256sum --check` assertion. Build path: **no**.
- [ ] **LOW** — GitLab CI `allow_failure: true` never flipped — `.gitlab-ci.yml:47` — after confirming one full green `tests` run on the shared runner, flip to `false`; if epubcheck/JRE or build smokes can't run there, split them into a separate allow-failure job and make core pytest blocking. Build path: **no**.
- [ ] **LOW** — Dead `lane-transfer/audit` + `lane-transfer/rules` branches — `git push origin --delete` both, `git fetch origin --prune`, plus delete local `lane-transfer/rules` (`git branch --merged main` first; `-D` if unmerged). Build path: **no**.
- [ ] **LOW** *(merged ×2)* — Archive dead one-shot workflows — `.claude/workflows/deep-audit-continue.js` (round-3 recovery) + `.claude/workflows/deep-audit-merge.js` (round-6 merge, consumed, blank-array state) — `git mv` both to `dev/archive/` (or `.claude/workflows/archive/`); note the archival in `reference_deep_audit_tool.md`. Build path: **no**.
- [ ] **LOW** — DROPPED banner missing on cloud-run runbook — `docs/superpowers/notes/2026-06-02-runpod-bootstrap-runbook.md:1-5` — insert the ⛔ DROPPED 2026-06-04 block after the H1, matching the companion plan/spec wording. Build path: **no**.

### Phase 5 — Build-pipeline correctness (⚠ every item here touches the build path → byte-stability proof obligation: regen all 9 KJV editions + `git diff` / digest compare; where output changes by design, reset the baseline deliberately and run epubcheck + `test_nested_anchors` + `check_nested_anchors --fix` after any `epub_working` mutation)

- [ ] **MEDIUM** — 3-token span cap fragments 5-token Nave's compound topics — `scripts/build_edition.py:2211` — change `min(3, len(tokens) - i)` to `len(tokens) - i` (uncapped). Guard: unit test feeding "MANASSEH, NAPHTALI, REUBEN, SIMEON, ZEBULUN" and asserting single-topic collapse. Build path: **yes** — only `ethiopian-tewahedo` (`note_topic_dedup: true`) changes; **prove the 9 KJV editions byte-identical** via regen+diff.
- [ ] **MEDIUM** — Xref note-body links target hidden `#vnote-*` containers (Kobo teleport-to-file-start) — `scripts/core/detectors.py:401,746` — retarget both emitters to the visible `#v-{b}-{c}-{v}` anchors; extend `scripts/fix_xref_targets.py` with the `V_HREF_RE` pass + `id="v-…"` indexing for cross-file cases; repair the 88 already-rendered instances in `epub_working` (index_split_050/058/059, inside `note-xref-citation` asides only). Guard: new `dev/verify_kr2_build.py` gate — zero plain `<a href="#vnote-">` (non-noteref) inside note-body asides. Build path: **yes** — intentional output change; baseline reset + epubcheck + nested-anchor gates + Kobo round-5 spot-check. *Class swept: 2 of 2 emitter sites in detectors.py; verify_kr2 currently gates only noteref hrefs — the new gate closes the class.*
- [ ] **LOW** *(two findings, one regex edit)* — K-R4-1 separator regex misses `vnote-empty` AND double-marks WEB pilcrow verses — `scripts/build_edition.py:1922` — combined pattern: `re.compile(r'(<p class="vnote-text(?:\s[^"]*)?">)(?!<span class="vn-sep">)(?!¶)')` (multi-class match + skip-when-already-¶ lookahead). Guard: unit tests for both shapes (`vnote-empty` placeholder gets a separator; `¶ And God said` does not get a second mark). Build path: **yes** — lands with the in-flight K-R4-1 rebuild; KJV byte-stability unaffected but prove it.
- [ ] **LOW** *(merged ×2)* — Splitter leaves empty `<section class="verse-refs-section">` shells — `scripts/build_edition.py:2860,2910-2911` — add companion `_EMPTY_VERSE_REFS_SECTION_RE` constant + `.sub("", content)` after the existing notes-section cleanup. Guard: `tests/test_file_split.py` case using the REAL epub_working structure (`<section class="verse-refs-section">` wrapping `<aside class="vnote">`) + a `verify_kr2_build.py` gate asserting no empty shell in any piece. Build path: **yes** — output change (dead markup removed); baseline reset + epubcheck.
- [ ] **LOW** — Unsorted `*.html` glob loops (latent non-determinism) — `scripts/build_edition.py:5109` **and** `:4722` — wrap BOTH in `sorted()` (the finder's single-site fix is incomplete; these are the only 2 unsorted of 14 such loops — class swept). Guard: the existing byte-stability gate (after Phase 6's flagship fix) covers it. Build path: **yes** — must be byte-identical; prove via regen+diff.
- [ ] **LOW** — `_kind_default_labels` cache never invalidated on UI kind-label save — `scripts/api/customize.py:124` — prefer the simpler correct option: **remove** `@lru_cache(maxsize=1)` from `_kind_default_labels` (build_edition.py:2027) since `kinds_by_code()` is uncached and always fresh; otherwise add the guarded `cache_clear()` call. Guard: test that a kind-label save changes the next `_kind_default_labels()` result. Build path: **no byte change** (KJV editions short-circuit at `s1_dedup=False`), but it edits build_edition.py → include in the same regen+diff proof. *Coordinate with the Phase 1 whitelist entry: removal makes that line unnecessary.*
- [ ] **LOW** — `tsk._raw` dead branch re-parses TSK JSON per book — `scripts/run_xref_at_scale.py:61-65` — replace the 5 lines with `raw = tsk._data`; leave the `main()` enumeration load alone. Guard: existing xref driver tests. Build path: **no** (ingest tooling).
- [ ] **LOW** — 4 byte-identical `_emit_extent_ok` copies — `scripts/run_naves_at_scale.py:34-38` + torrey/xref/kenyon siblings — add `emit_extent_ok = coord_in_canonical_extent` export to `at_scale_base.py`; each driver imports `as _emit_extent_ok` (preserves the `mod._emit_extent_ok` name `test_mint11_phase3.py:104` requires). Include the new ethiopian guard (Phase 1) in the same consolidation. Build path: **no**.
- [ ] **LOW** — Dead `estimate_cost()` duplicated in 2 AI drivers — `scripts/run_ai_notes_at_scale.py:106-107` + `run_ai_xrefs_at_scale.py:105` — remove both; update the two test call-sites (`test_scripts.py:14384-14388`, `test_corpus_chi_ai_xrefs.py:964-968`) to assert via `mod.COST_PER_VERSE_USD * n`. Build path: **no**.
- [ ] **LOW** — 4 GET routes return `{"error":…}` at HTTP 200 — `scripts/web.py:1507,1546,1640,1931` — apply the identical `status=404 if result.get("error") else 200` pattern at all 4 sites (class swept: these are the only routes bypassing `_dispatch_table_result`). Guard: route tests asserting 404 on the not-found paths so `safeFetch`'s `!response.ok` branch fires. Build path: **no** (UI runtime).
- [ ] **LOW** — Torrey reingest lacks XHTML-safety screen — `scripts/_reingest_torrey_topics.py:157-163` — add the `_body_xhtml_bad()` guard mirroring the Easton screen; **root fix**: `html.escape()` each topic label when building `topics_str` in `TorreyTopicalDetector.detect()` (detectors.py:528) so the 61 `"Herbs, & C"` bodies stop being store-malformed at source. Guard: the reingest guard itself + a lint/unit check that detector output is entity-safe. Build path: detector change is **yes** on any future reinject — gate with regen+diff when it lands.
- [ ] **LOW** — Torrey reingest base-search misses HTML-escaped old bodies — `scripts/_reingest_torrey_topics.py:167-168` — frozen one-shot script, already executed correctly; if ever reused, apply the `&`→`&amp;` escaped `base_mapping` for base writes + extended post-check. **Document-only now** (header comment noting the limitation). Build path: **no**.

### Phase 6 — Test fixes

- [ ] **MEDIUM** — Byte-stability gate re-checks the wrong "flagship" — `tests/test_byte_stability_gate.py:92` — `flagship = _EDITIONS[0]  # ethiopian-tewahedo — the actual project flagship`. Guard: it IS the guard; one full slow-gate run to confirm green. Build path: **no** (test-only).
- [ ] **LOW** — Dead `str.replace()` result discarded in cache-invalidation test — `tests/test_core.py:73` — delete line 73; fix the line-71 comment ("write a single-note version to force an mtime change"). Build path: **no**.
- [ ] **LOW** — Unused `n2` binding implies unchecked idempotency — `tests/test_resync_markers.py:141-146` — **Option A** (verifier-corrected: `assert n2 == 0` would fail as the regex re-matches `marker-num`): bind to `_` and comment the test's actual coverage (output-stability only). Build path: **no**.

### Phase 7 — Public-surface copy sweep (ONE pass, ONE site rebuild + redeploy — "deploy" = rebuild from source THEN publish; count-change sweeps page+meta+social-card+repo-descriptions per standing rule)

- [ ] **MEDIUM** *(merged ×5 count findings)* — Stale note count 91,733 → shipped **91,553** at every public surface: `README.md:21`, `COPYRIGHT.md:22`, `brand/BIOS.md:33,50,88`, `brand/sources/card.html:38`. Then re-render the 1280×630 social card (local `http.server` + Playwright screenshot) → `website/social-card.png` + `brand/social-card.png`. Gate: `grep -r '91,733'` over public surfaces = zero hits (do NOT touch CHANGELOG/SESSION_STATE/MATRIX_MAP/archive — historical records).
- [ ] **MEDIUM** — BIOS.md says "87-book" ×6 (RULES §5 violation in paste-ready public copy) — `brand/BIOS.md:24,27,33,50,88,95` — all six → "83-book". Gate: `grep '87-book'` over brand/ + website/ = zero. Manually re-paste the corrected BIOS into the GitLab/GitHub profile surfaces where deployed.
- [ ] **MEDIUM** — Roadmap stage still "Opening soon"/is-active post-ship — `website/src/roadmap.html:55-60` — `is-shipped` class, "Shipped" badge, past-tense body; keep the existing releases.html link (no duplicate).
- [ ] **LOW** — Homepage "posted for download very soon" — `website/src/index.html:331` — replace with "available now for Windows, macOS, and Linux…".
- [ ] **MEDIUM + LOW** *(merged)* — README stale release framing — `README.md:33` ("once the first public beta is posted" → present-tense link to releases/latest) and `README.md:9` (`v1.x` → `v0.1.0`).
- [ ] Close the phase with: rebuild `website/dist/` from src, redeploy, and update GitHub/GitLab repo descriptions if they still carry old counts.

### Phase 8 — Truth records & Claude-setup hygiene

- [ ] **MEDIUM** *(merged ×2)* — PLAYBOOK prescribes dead Java 8 for epubcheck — `dev/SESSION_PLAYBOOK.md:34,86,90` + `dev/VISUAL_QA_CHECKLIST.md:84` — all four sites → Temurin 26 on PATH, no prepend, epubcheck 5.1.0 needs Java 11+, **always `--jar <jar>`** (bundled PyPI jar path). Class swept: TOOLCHAIN.md + memory already correct.
- [ ] **MEDIUM** — Installed SessionStart hook is a stale copy (missing lane-identity, env-health, baton-incoming blocks) — `C:/Users/bogda/Documents/YHWH-v2.4-full/.claude/hooks/bootstrap-triad.ps1` vs `dev/cc-hooks/bootstrap-triad.ps1` — run `dev/cc-hooks/install_cc_hooks.ps1`; verify SHA256 equality after.
- [ ] **MEDIUM** — Wildcard `PowerShell(pip install *)` allow-rule bypasses the global undeclared-install soft-deny — `C:/Users/bogda/Documents/YHWH-v2.4-full/.claude/settings.local.json:135` — remove the entry (the exact-match ruff allow at line 113 stays).
- [ ] **LOW** — PLAYBOOK §5 taxonomy target 91,733 → 91,553 — `dev/SESSION_PLAYBOOK.md:11,52,81` only (no bulk-replace in historical records).
- [ ] **LOW** — RULES §0 "~16 plugins" → "15 plugins (14 @claude-plugins-official + gitkraken-hooks@gitkraken)" — `dev/CLAUDE_PROJECT_RULES.md:200`.
- [ ] **LOW** — SESSION_STATE console inventory 19 → 21 (+ HOME_HTML/INDEX_HTML roles corrected) — `dev/SESSION_STATE.md:111-113`.
- [ ] **LOW** — `_design.py` docstring "13 consoles" ×3 → 21 — `scripts/templates/_design.py:2,5,37` (comment-only).
- [ ] **LOW** — REPO_MAP test count 219 → 224 (regen via `py dev/trace_repo.py`) + add `LANE_HANDOFF.md` to the Bootstrap bullet — `dev/REPO_MAP.md:17,51`.
- [ ] **LOW** — Roadmap plan: mint-3..6 rows → ✅ done; stale "git push has failed" note → remote-restored note — `dev/PLAN_2026-05-29-roadmap.md:74-77,82`.
- [ ] **INFO** — INDEX.md header "77 documents — 50 plans · 27 specs" → "78 documents — 50 plans · 28 specs" — `docs/superpowers/INDEX.md:7`.
- [ ] **LOW** — Memory: `reference_save.md:28` baton-holder paragraph contradicts RULES §4 — replace with the 2026-06-08 parallel/exclusive + truth_owner wording as drafted.
- [ ] **LOW** — Memory: `reference_external_tools.md` claims a stored Voyage key (the `.env` is empty) — fix description front-matter + body; treat the chat-pasted key as unused/revoked.
- [ ] **LOW** — Memory: create `reference_lane_coordination.md` on this box (spec line 55 requires it in both lanes) — concise mode/truth_owner//handoff//resume//sync summary pointing at the spec + RULES §4.
- [ ] **INFO** — Memory: Azure GUIDs in `reference_windows_signing_azure.md:19-22` → replace with portal-lookup instructions (optional hygiene; non-credential identifiers, negligible risk).

## Optimization decisions

| Area | Verdict | Recommendation |
|---|---|---|
| Build parallelism (ThreadPoolExecutor=5), content-addressable cache, mtime incremental check | **confirmed-optimal** | No change. Document the confirm-optimal status near build_edition.py:5464 and in MATRIX_MAP.md so future audits don't re-derive it. More workers would OOM the 16 GB box. |
| zip `compresslevel` 9→6 | **confirmed-optimal (DECLINED)** | Stands declined on the merits — quality output > build speed. |
| `filter_html` per-id regex (O(N_ids×N_files) compiles, ~3.66M/build for catholic-study) | **change** | Pre-compile two generic id-scan regexes per edition in `build_one`; set-lookup callables in `filter_html` with the legacy loop as fallback (build_edition.py:1381-1397). **Byte-identical output is the acceptance gate** — regen all 9 + diff. Est. 15–50 s saved per tradition-filtered edition. |
| `ebible.py` hardcoded `/tmp/` paths (lines 69, 239, 414) | **change** | `tempfile.gettempdir()` at all three sites (class swept: only sites in the file). POSIX behavior byte-identical; fixes `ebible status/build/repl` on the primary Windows box. |
| `translations.py` hardcoded `TRANSLATIONS_DIR` in 4 public functions (54-55, 151-157, 160-168, 214) | **change** | Route `_book_path`/`has_translation`/`list_translations`/`translation_meta` through the existing `_translations_dir()` resolver; keep the constant as a back-compat export; add the `set_content_root_for_testing` test to test_paths_omega5.py. Do alongside Phase 2 (same frozen-path class). |
| BIOS.md "87-book" ×6 + counts | **change** | Folded into Phase 7 (RULES §5: never say 87 publicly). |
| README/brand 91,733 + v1.x staleness | **change** | Folded into Phase 7 single-deploy sweep. |
| Empty `verse-refs-section` splitter cleanup | **change** | Folded into Phase 5 (merged with the popup-integrity duplicate). |
| Kings/Samuel manuscript marathon (LANE M) | **confirmed-optimal** | No change — tight-crop ≤1568 px, MAX-1-heavy, per-step commits stand. CAM IIIF tile-stitch stays the Mac's pre-pull task. **Marathon core remains off-limits.** |
| 117-chapter verse-boundary residual (WEB-fixture anchor design) | **confirmed-optimal** | Execute as designed in the v0.1.1 window after round-4 device QA (deferred-by-design item 9 — not a round-7 fix). |
| Native ToC chapters (`enrich_nav_chapters`, default OFF) | **confirmed-optimal** | No code change; the one open item is the 30-second round-5 device eyeball already on the backlog. |
| Standalone Ge'ez/Amharic Bibles (LANE P) | **confirmed-optimal** | Correctly deferred until the D + M render phases deliver. Out of scope this round (settled item 6). |
| Ingest orchestration (12 drivers + at_scale_base) | **confirmed-optimal** | No restructuring; a unified driver would degrade isolation and add RAM pressure. Phase 5's `_emit_extent_ok` consolidation is the only touch. |
| No paid API / no cloud VM | **constraint, not a lever** | Voyage integration stays dropped; cloud-VM permanently off — no optimization may reintroduce either. |

## Constraints carried

- **Marathon core is off-limits** — never edit `scripts/build_standalone.py`, `scripts/core/manuscript_*.py`, `scripts/core/po_vision_store.py`, `content/manuscript/**`, `content/translations/sources/patrologia/**`, `GAPS/`. No finding above touches them.
- **9 KJV editions build byte-stable** — every Phase 5 change (and the filter_html optimization) carries a regen + `git diff`/digest proof obligation; where output changes by design (xref retarget, separator regex, empty-section cleanup), reset the baseline deliberately, run epubcheck (Temurin 26, `--jar`), and run `test_nested_anchors` + `check_nested_anchors --fix` after any `epub_working` mutation; verify on a canon-filtered edition (catholic-study), not just the superset.
- **Schema changes additive only** (byte-identical when unset); **all writes via `notes_io.atomic_write` / `ensure_backup`**.
- **Save cadence (RULES §4, 2026-06-08, bandwidth-first):** each fix lands as a LOCAL COMMIT; the full 5-leg push/deploy (`save-all.ps1`) only at a milestone of this lane's half or on a direct user save/push command; `ruff format` generated files before every save; lane-ping radar before any push.
- **This audit is FINDINGS-ONLY** — this plan is the deliverable; STOP before applying any fix (user marching order 2026-06-08). Phase execution begins only on explicit go-ahead.