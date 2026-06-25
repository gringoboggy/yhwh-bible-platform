# In-flight work — current task tracker

<!-- TRACKER-STATE: active -->
<!-- task: Kobo deep-audit program — scripture line-breaks + study-note redundancy + popup formatting (2026-06-24, autonomous, Mac-assisted) -->

> **▶ 2026-06-24 (Windows, autonomous Mac-helping session) — IN PROGRESS.**
> **★ NEW PROGRAM (2026-06-24, user-triggered autonomous) — Kobo deep-audit: `dev/audit/kobo-deep-audit-program-2026-06-24.md` (READ FIRST).**
> Device eyeball of the newest flagship eink kepub (built fresh from HEAD, loaded to G:): **✅ NO PAGE BREAKS Genesis→Revelation**
> — the page-break defect is RESOLVED on-device. New findings → 3 workstreams + discrete fixes, planned + run + fixed
> autonomously with Mac, neither lane stops till done. **WS1** scripture-body formatting — ROOT-CAUSED: mid-verse line breaks =
> a verse split across multiple `<p class="verse-p">` blocks (gen 19:1 etc.); "weird symbol" = the pilcrow `¶` on KJV-text verses
> (gen 46:13, 49:14) MIXED into WEB/modern text → a mixed-translation defect; badge-trail spaces → `dev/audit_verse_formatting.py`
> + fix + deliberate re-baseline. **WS2** study-note redundancy/contradiction → cascade rework. **WS3** Kobo run-on popup
> formatting research (Mac) → fix. **Discrete:** Prayer of Azariah ToC title reverted to the long form (→ `[+]` truncation) —
> re-shorten + pin. Lane split + loop-until-done protocol in the program doc; Mac's slice in `LANE_HANDOFF.md`. **Earlier today:**
> **✅ Slice 1 DONE (committed):** the 2 WIN-surface standalone build-bugs Mac flagged in
> `dev/audit/spine-breaks-all-editions.md` — (1) `build_one` summary-print `KeyError:'enabled_kinds'`
> that crashed the CLI *after* a successful standalone build (new `_print_edition_build_summary` +
> `build_one` raises on standalone error for contract parity); (2) Amharic standalone misnamed
> `Geez_Standalone_*` (new `_output_filename` derives the script label; Ge'ez filename byte-stable).
> +9 TDD pins; `test_build_standalone` 52/52. No EPUB-byte change. CHANGELOG 2026-06-24.
> **✅ Page-break Part 1 DONE (drop `_VN_LINK_RE`):** the packer now cuts ONLY at book/chapter
> boundaries (removed the verse-level cut candidate + the obsolete K-R15b re-merge + the dead regex).
> **Verified on real data: catholic-study eink 111 mid-chapter → 1** (`audit_spine_breaks.py`); the lone
> `psa 119:88→89` is the documented BASE calibre-split artifact (`index_split_035`), not a packer cut →
> Part 2 fixes it for free. +2 TDD pins (`TestNoMidChapterSplit`); `test_file_split` 46/46. Companion: fixed
> a pre-existing glossary-test breakage from the wrap's backmatter WIP (`min(target, default)`; byte-safe).
> **✅ Page-break Part 2 DONE (per-book base-file merge):** new `_merge_scripture_base_files` concatenates the
> scripture base files (EINK target only) so a book the calibre base split across files is contiguous; then shards
> at `FILE_SPLIT_CEILING` (8 MB, device-validated) → one spine file per book (over-ceiling books chapter-split, never
> mid-chapter). **Verified end-to-end: catholic-study eink 111 mid + 163 chapter → 0 + 0** (only 71 intended
> book-title breaks; 238→72 pieces); `audit_spine_breaks.py` PASS; **epubcheck 0/0/0/0**; +5 TDD pins incl. eink-merge
> determinism (the byte-stability guard); `test_file_split` 54/54. The cross-file opener pop is skipped post-merge.
> **★ The weeks-long page-break defect is RESOLVED on eink (Parts 1+2).** eink-only → tablet/default/KJV untouched.
> **✅ FLAGSHIP VERIFIED (the user's exact 130-break case):** `ethiopian-tewahedo --target-reader eink` rebuilt →
> **130 mid + 40 chapter breaks → 0 + 0** (77 intended book-title breaks; scripture pieces → 77; 29.69 MB);
> `audit_spine_breaks.py` PASS; **epubcheck 0/0/0/0**; kepubified → `YHWH-koboQA.kepub.epub` (39.1 MB).
> **⏳ STAGED for the user's device eyeball at `C:\Users\bogda\YHWH-device-staging\YHWH-koboQA.kepub.epub`** (the Kobo
> `G:` is NOT mounted — when the user connects it, DELETE the old `G:\YHWH-koboQA.kepub.epub` then copy this one).
> **✅ Page-break Part 2b DONE (standalone per-book merge — completes the defect across ALL editions):** the standalones
> (`standalone-geez`/`standalone-amharic`) use a SEPARATE path (`build_standalone`) that emitted one spine file PER
> CHAPTER → chapter-per-page on Kobo (Mac's audit: geez 161 / amharic 125). New pure `pack_book_chapters(book, chapters,
> ceiling)` merges each book's chapter fragments into one spine file (shards at `be.FILE_SPLIT_CEILING`=8 MB, chapter
> boundaries only, never mid-chapter); per-chapter `#ch-{book}-c{ch}` anchors keep TOC nav; noterefs stay same-file.
> **Verified on real builds: standalone-geez 4 books/165 ch → 4 spine pieces 0 mid + 0 chapter (was 161); standalone-amharic
> psa/126 ch → 1 piece 0+0 (was 125)**; `audit_spine_breaks.py` PASS + **epubcheck 0/0/0/0** on both; +5 TDD pins
> (`TestPerBookMerge` + `TestStandaloneSpineMerge`); `test_build_standalone` 57/57. UX-only (standalones are not
> byte-stable-pinned). ⏳ Mac cross-OS verify queued in `LANE_HANDOFF.md`.
> **▶ NEXT (WIN, in priority order):**
> 1. **[USER] device eyeball** of the staged flagship kepub on the color Kobo (confirms the page-break fix on-device);
>    **Mac cross-OS verify Parts 1+2+2b + re-baseline `dev/audit/spine-breaks-all-editions.md`** across all editions incl.
>    the standalones (instructed in `LANE_HANDOFF.md`; Mac already pushed `spine-breaks-post-part1.json`).
> 2. **✅ Hebrew/Greek/Ge'ez popup-font fix DONE (eink CSS, byte-safe):** added `!important` `font-family` rules for
>    `.vnote-hebrew/greek/greek-nt/geez/amharic` to the eink-only `_EINK_READER_CSS` (Hebrew/Greek = embedded Cardo;
>    Ge'ez/Amharic = embedded `"Noto Serif Ethiopic"`, not the stale wrong `"Noto Sans Ethiopic"`). **Verified on a real
>    eink build:** all 3 rules ship in the built `stylesheet.css`, **epubcheck 0/0/0/0**; `test_kobo_device_qa` 16/16
>    (+2 pins). eink-only → 9-KJV untouched. **⏳ DEVICE GATE (`dev/HUMAN_DECISIONS.md`):** does the author `!important`
>    beat Kobo's firmware override? — the user's "Cardo" vs "Publisher Default" A/B decides (the staged kepub carries it).
>    **DEFERRED follow-ups:** (a) embed **Noto Naskh Arabic** for `.vnote-arabic` (a global `EMBED_FONT_PATHS` add changes
>    KJV bytes → needs an eink-only embed path; Arabic is tofu today); (b) the eink "Publisher Default" front-matter page
>    (Kobo's only guaranteed lever + the only fix for the native footnote-PREVIEW overlay). Plan: `kobo-font-override-research.md`.
> 3. Device-QA **E** (study-note back-link navigate, `_study_verse_return_link` → cross-file noteref) + **F** (drop redundant
>    per-note `note-sym` in `_emit_cascade_sections`; supersedes B-1c). round-13 merge remainder (char-vs-byte · 1en 71/90
>    — Mac fetched the PD Charles source `dev/audit/1en-charles-source-71-90.md` · 5 Mac mediums I remediate / Mac verifies).
> Plan: `dev/audit/page-breaks-root-cause-2026-06-23.md`. **⏳ Mac cross-OS verifies the re-cut when Part 2 lands.**
>

## ▶ Full-audit program — WIN audit DONE · Mac running · REMEDIATION NEXT (2026-06-22, autonomous)

> **Goal (user):** "run autonomously with Mac helping until the full audit is in and everything it surfaces is fixed." Two complementary audits, split across both boxes, then remediate everything:
>
> 1. **Code/product deep-audit round 10** (`.claude/workflows/deep-audit.js`, scope=product, Opus) — SPLIT: **WIN lane** (6 compute dims: tests-run · opt-build · byte-stability · rx-surfaces · popup-integrity · platform-kobo) runs locally; **MAC lane** (18 read-only dims) runs on the iMac (handoff in `dev/LANE_HANDOFF.md` "Deep-audit round 10 — SPLIT RUN"). Disjoint → together = all 24 product dims.
> 2. **EPUB structural+content audit** (`dev/audit_book_structure.py`, spec `docs/superpowers/specs/2026-06-22-epub-structural-content-audit.md`) — deterministic per (edition × format × book) verse→chapter→book→out-of-book pass. Authored while #1 runs; run on built epubs after.
>
> **Findings land in `dev/audit/`** (`round10-win/mac-survivors.json` + `-plan.md`); WIN merges → `round10-remediation.md` → fixes everything (TDD, byte-stability proof on any build-path touch, commit-per-fix, push at coherent stops). **This run OVERRIDES the engine's "findings-only" marching order** — the user wants remediation through to green. Loop until: all survivors fixed + structural audit all-green + suite green.
>
> **WRAP STATE (2026-06-23 — REMEDIATION WELL UNDERWAY; wrapped for a fresh session).** Both audit lanes
> are IN + merged (`round10-win-*` + `round10-mac-*`), and the Mac's **round-11 completeness-gap sweep**
> turned the 8 single-findings into **69 enumerated sites** (`round11-mac-{survivors,plan}.md`). The master
> tracker with the live per-class status is **`dev/audit/round10-remediation.md`** — read it FIRST.
>
> **✅ DONE this session (16 WIN commits, all green+pushed, Mac-verified cross-OS = 118 tests PASS):**
> Phase-0 hygiene (W1 HIGH cache red-gate · ruff F402/F841 · ALL_CHECKS 34→37 · bare-python · note_rehaul
> ×2 · `test_lane_watch` live-git hazard) · Phase-4 byte-neutral (book-code · SemVer prerelease · promote
> q-quit · navigator coord-resolver) · **W2/W5 Kindle byte-stability** (OCF re-zip reproducible) · **6 of 8
> round-11 classes**: gap-1 (3 sites) · gap-2 (4, own-vers `verse_sort_key`) · gap-3 (CDATA `_cdata`
> chokepoint) · **gap-4 (18-site SQLite use-after-close race → `_read_cursor()`)** · gap-5 (cache-key) ·
> gap-6 (reading-plan refs chokepoint).
>
> **▶ 2026-06-23 session — IN PROGRESS (autonomous; Mac running a BIG 6-workstream parallel batch — `LANE_HANDOFF.md` top):**
> - **✅ gap-7 DONE** (migration runner, 13 sites) — tri-state `deferred` outcome (`apply_up`/`run_up` non-fatal skip, exit 0; hard failures still abort) + 0002 deferred-on-pending (was the `ok:False` wedge) + argv crash-fix (`backfill_traditions.main(argv)`; 0002→`main([])`) + frozen-safe ledger (`_default_state_path()`→`content_root()`, gitignored, +sys.path) + `core/migrate.py` atomic DDL+ledger (`_iter_sql_statements`, no `executescript`). 9 new tests + CLI subprocess guard; 57 migrate + 205 dependent green. Scope: version-aware-copy blanket-overwrite = conservative NO-GO (would clobber user editions); launcher→ledger routing = LOW follow-up. Detail in `round10-remediation.md` gap-7 row.
> - **✅ gap-8 DONE** (producer/consumer, 15 sites) — `build_standalone` reads `edition['base_translation']`/`['popup_translation']` + resolves apparatus dir from the body store (was hardcoded geez → rendered Ge'ez into the Amharic edition); `standalone_store` `_render_book_module`/`build_book_store`/`build_psalms_apparatus` take a `translation` arg (default geez); `geez_kjv_xref.build_kjv_xref` keys by `str(geez_v)` (in-memory hand-off drops no xrefs). **Byte-PROVEN: standalone-geez bodies SHA-256 `870ad9e5…486aca` identical pre/post (165 ch); 71 build-suite tests green (17.7 min).** Scope: `gen_website_progress` amharic-track = conservative DEFER to LANE P (false-"ready" risk; reader is geez-templated). **★ ALL 8 round-11 gap classes CLOSED.**
>
> - **✅ Round-10 byte-stability leftovers — W3 + W6 + W7 + theme_id DONE** (3 commits): W3a removed the stray `theme:"modern"` (added 2026-06-22 `dd7bb53f`, wedged in a comment; the only `theme:` decl) → restores intended default `classic` + fixes `test_editions_do_not_pin_theme_skus`; W3b `build_cache` hashes the ACTIVE theme CSS unconditionally (default classic included) + theme_id mirrors `build_edition` exactly; W6 `kobo_tap_calibration` targets/docstring → round-5 bracket; W7 `verify_kr2_build` non-failing byte-size WARN (>500KB, true bytes). 44 cache + 8 theme tests green.
>   - **⛔ char-vs-byte split-measure = conservative DEFER (re-verified NO-GO this pass).** REAL DATA: catholic-study = **297 pieces, ALL non-ASCII, 20.7M non-ASCII bytes** → switching the file-split packing from codepoints to UTF-8 bytes would shift boundaries on **every** edition, **breaking the sacred 9-KJV-byte-stable invariant** + re-cutting the shipped product structure. It's LOW severity, the **W7 byte-WARN already catches the symptom** (oversized pieces), and an all-edition re-cut + golden re-baseline is a deliberate, user-aware change → folded into the **FINAL grand audit** (rebuilds everything anyway), not a buried leftover commit. Sites for when it's taken on: `build_edition.py` 4728/4796/4799/4971/4990/5016.
>
> - **✅ frozen-app `content_root()` HIGH DONE** — added the `sys.frozen` guard to `paths._content_root_cached()` (mirrors `_build_output_root`; placed after the `YHWH_CONTENT_ROOT` override, before in-tree detection) + **routed ~37 read/write sites through `paths.*` across 20 files** (config.py loaders+mtimes, web_helpers `write_book`/`_canons_index`, web_notes/sources/matrix/covers/content/editions, api/editions/covers/sources/customize/scenarios/preflight, core/translations/covers/preview/traditions/press_kit) + deleted the dead `web.py:65 SCENARIOS_DIR`. **No-op in dev** (content_root()==repo/content) — proven: **test_core 46 + test_scripts 994 green** + 4 new frozen-sim pins (`tests/test_frozen_app_paths.py`). Also fixed 2 fallout: config caching tests re-homed to `set_content_root_for_testing` (loaders are now content-root-aware) + a **pre-existing malformed IN_FLIGHT marker** (`active — extra text`, present since session start; broke `flip_inflight`+lint+3 pytest tests) → strict `<!-- TRACKER-STATE: active -->`. **Deferred (sources_base lazy-PATH):** `sources_lexicon`/`sources_commentary` `PATH` class-attrs freeze at import; routing them needs a lazy-PATH refactor that changes the test-monkeypatched `loader_cls.PATH` shape → grand-audit follow-up (read-only published data, bundle-read is correct meanwhile). **★ ALL WIN round-10/11 remediation COMPLETE.**
>
> **▶ REMAINING:**
> 0. **✅ WIN OPEN round-13 items DONE (2026-06-23, this session — `04340574` #9 · `c85a772b` #5 · `243efb7` #6; all green + epubcheck 0/0/0/0):** #9 inject `escape_attr` (escapes `& < > "`, preserves `'` — "Nave's …" is a real title; 4 title-attr sites) · #5 dropped 3 dead `REPO` (re-verify caught 2 spec false-positives — `api/exports`+`api/preflight` `REPO` are LIVE dev-server paths, kept) · #6 `ZipInfo.create_system=0` in all EPUB writers (catholic-study built → all 383 entries `create_system=0`). **`sources_base` lazy-PATH = conservative DEFER** (read-only published data → in-bundle read is correct for a frozen app; not a bug). **Remaining round-13 = the joint merge w/ Mac's half: char-vs-byte #2 · #7 `audit_popup_formula` · the `1en` 71/90 base-content fix (WIN root-caused Mac's structural FAIL: a split editorial bracket — Charles's "xlvi. 3" cross-ref mis-read as a verse 46, NOT a re-order; needs the PD Charles source) · device-QA.** Mac's structural pass + cross-OS verify (`b20ff74e`/`161f37e8`: WIN's tree ALL GREEN on macOS) are IN; **Mac's `deep-audit` `LANE=mac` survivors DONE + pushed** (`333e7366`: 33 survivors / 12 refuted) + **#7 `audit_popup_formula` fixed** (`00b2de3d`).
> 1. **🔬 FINAL joint grand audit — LAUNCHED (2026-06-23)** (user: full auditor top-to-bottom, verse + word, no time limit). **WIN half RUNNING:** `deep-audit` round-13 `LANE=win` (6 compute dims) → `wf_64ba6cb1-f47` (background; findings → `dev/audit/round13-win-*`). **Mac half + the verse/word structural pass** = handed off (`LANE_HANDOFF.md` top). On completion both lanes merge → `round13-remediation.md` → remediate to green. **Grand-audit agenda:** (a) the deferred **char-vs-byte** all-edition re-cut + golden re-baseline; (b) ~~Mac's 2 round-12 HIGH zip writers~~ **✅ DONE 2026-06-23** (shared `scripts/core/zip_repro.py` helper → press_kit `build_zip` + exports All-Editions bundle now pin `date_time`; 3 zip-repro + 33 press_kit + 5 exports tests green); (c) Mac's **`1en` misordering** in ethiopian-tewahedo (structural auditor's 1 real FAIL — likely the known 1En 37–108 residual, WIN to confirm); (d) the `sources_base` lazy-PATH frozen-app tail.
> 2. **▶ Mac: cross-OS verify** gap-7 + frozen-app + W3 (Mac already ✅'d gap-6 + gap-8). See `LANE_HANDOFF.md`.
> 3. gap-2 LOW (verse_of_day/preview) = ✅ already done.
>
> ⚠ The user's **K-R4-2 vnote Kobo bug** stays on the **M2 / K-R4-2** backlog (surfaced + refuted-as-known-
> deferred), NOT closed. Device-QA gates live in `dev/HUMAN_DECISIONS.md`.

## ▶ Rules + accuracy consolidation — EXECUTED (2026-06-21)

> **The consolidation plan `docs/superpowers/plans/2026-06-21-rules-and-accuracy-consolidation.md` is DONE** — Phases **A–E, G, H** (9 local commits on `main`). Radar/contradiction seed fixed (§4 auto-pull merged; no "background radar") · save-cadence + E:/F: contradictions resolved · rotted counts (91,597→**91,712** · 68→**72 kinds**, verified live) consolidated to `dev/SESSION_STATE.md` as the ONE live-figures home · bloat → RULES_HISTORY/invariants · Mac hook baton→lane-v2 + session-start PING + a `hook_parity` lint · radar echoes → seam wording · **RULES §2.6 work-phase loop + `dev/HUMAN_DECISIONS.md`** + a `no_background_radar` regression lint (the residual confirm — INCLUDED) · 8 website offer-accuracy fixes (built, 0 dead links) · the 7 Mac rule-change-parity tasks filed in `dev/LANE_HANDOFF.md`. **Adversarial 4-dim review:** completeness clean; 2 valid coherence fixes applied; the "83→87" flag rejected (83 = the public superset). **Gates green:** lint 35 pass/0 fail · trace_matrix 0 · trace_repo complete · ebible verify errors=0 (all paired) · website 0 dead links.

### Remaining (priority order)

1. **Phase F — count cascade DONE in source; the live website PUBLISH → Mac.** Mac's rebuild gave the
   authoritative shipped figure **91,555** note-refs (was 91,553; per-edition: ethiopian 91,555 ·
   catholic-study 43,370 · evangelical-reformed 41,847 · eastern-orthodox 41,819). WIN swept the source
   cascade (index/roadmap/README/BIOS/COPYRIGHT/`card.html` · SESSION_STATE) + the README Anglican/Lutheran
   fix + added the Ge'ez 1 Kings 7–10 reader pages (commit `5d156842`, pushed). EPUB metadata needs no edit
   (matter pages compute counts live); the GitHub repo description uses "91k" (no change). **The live
   publish is Mac's** (WIN has no `yhwh-website` Pages clone) — rebuild `dist/` + re-render the social-card
   PNG to 91,555 + deploy to `yhwh-website` + refresh the GitHub/GitLab v0.1.0 release body (91,555 + fix
   the stale "nine starting editions" → 4 canon SKUs) + re-scrape the og card. Checklist:
   `dev/LANE_HANDOFF.md` "▶ Phase F website publish → Mac".
2. **Resume the v1.0.0 release gate** (`docs/superpowers/plans/2026-06-14-v1.0.0-release-plan.md`). The
   human-gated device QA is now queued in **`dev/HUMAN_DECISIONS.md`** (Kobo taps · Apple device re-QA ·
   Kindle STK device check · Play Books phone QA · the `v1.0.0` tag command). WIN = M2 Apple audit
   (K-R5-3) · Kindle STK device bisect; Mac verifies.

## Standalone status (unchanged)

> Phases A-C shipped (`build_standalone.py`, 4 books, epubcheck 0/0/0/0); EN back-translation done
> for collated Kings/Samuel + all 151 Psalms; Phase D (own-vers re-ingest) via the Esther vision lane.
