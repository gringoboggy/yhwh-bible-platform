# Round-16 remediation tracker — Build-Program Bulletproofing

Plan USER-APPROVED in plan mode (2026-06-27). Program: `dev/audit/round-16-build-program-bulletproofing-2026-06-27.md` (READ FIRST).
Process: configure `deep-audit.js ROUND=16` (DONE) → run two-lane (both lanes all 11 dims; WIN harness + Mac cross-OS verify) → adversarially verify → **gather all findings (FINDINGS-ONLY)** → merge → phased fixes plan for user approval. NO fixes this round.
`truth_owner = windows`; file-disjoint parallel. Marathon core OFF-LIMITS. Round-14 build-source dims + round-15 D1–D9 are `DEFERRED_BY_DESIGN` (do NOT re-litigate).

## Status: ▶ WIN LANE — engine COMPLETE + merged (2026-06-27); non-flagship build sweep finishing; flagship-eink + Mac cross-OS + finalize = fresh session.
**Engine done:** 36→26 survivors (3 med, 23 low), 10 refuted — merged below + artifacts in `round16-engine-win-{survivors.json,plan.md,completeness.md}`. **Harness:** everywhere/tablet/kindle/eink-epub all CLEAN; kepub gate-FAILs = harness-applicability (fixed kepub-aware). **Build-free F1/F2 corroborated by the engine.** Phased plan below; **FINDINGS-ONLY — no fixes applied.**

## Findings (filled as the run surfaces them)

| # | dim | sev | source | finding / defect class | file:line or artifact | status |
|---|-----|-----|--------|------------------------|-----------------------|--------|
| F1 | cross-product / options-completeness | high | harness (`audit_cross_product`) | **`computer` ORPHAN reader target** — `/customize` offers 💻 Computer (`customize.py:534`) and `apply_target_override` accepts `computer` (it's in `TARGET_READERS`, `build_edition.py:1977`), but there is **no `FORMAT_MATRIX` row** for it → it builds as a silent alias of `everywhere` with no catalog asset, no colour fan-out, no test. | `build_edition.py:1977` (TARGET_READERS) · `build_edition.py:2034` (FORMAT_MATRIX, 5 rows) · `scripts/templates/customize.py:534` | ✅ CONFIRMED (gate `dev/audit_cross_product.py` FAIL; deterministic, build-free) |
| F2 | options-completeness | low-med | harness (`audit_customize_completeness`) | **`verse_marker_glyph` ORPHAN /customize field** — a text input (`customize.py`, max 4 chars) that is schema'd (`validate_schemas.py:229`), validated (`api/editions.py` EDITABLE_TEXT_FIELDS), and echoed back to the UI (`web_editions.py:419`), but is **READ by nothing on the build/cover path** (build_edition / matter_pages / core / generate_edition_covers all have zero consumers) → the control does nothing. | `scripts/validate_schemas.py:229` · `scripts/web_editions.py:419` · (no consumer) | ✅ CONFIRMED (gate `dev/audit_customize_completeness.py` FAIL; re-verified across whole tree). Fix options: wire it to the verse-marker render, or retire the field. |

**Seed verifications (scoping seeds confirmed NON-defects — the code already handles them; logged so they are not re-raised):**
- Seed #2 *kindle declared≠built* — `FORMAT_MATRIX` kindle row carries `post_process: kindle_safe` and `base_build_target` correctly returns `everywhere`; `audit_cross_product` check 2 PASSES → **not a defect** (the declared/built divergence is explicit + handled).
- Seed #3 *standalone target degeneracy* — `apply_target_override` raises `ValueError` on both standalone editions; they are excluded from `standard_edition_ids()`; `audit_cross_product` check 4 PASSES → **not a defect** (correct by design).
- Grid integrity: 4 catalog editions × 5 format cells × 5 colours = **100** expected catalog assets (+2 standalones = the 102 the scoping pass enumerated); no dup cell ids; no dup asset names.

`source ∈ {engine-win, engine-mac, harness, xos-verify}`. Severity from the calibrated skeptic panel. UNVERIFIED survivors (empty panel after retry) get their own row flagged `⚠ UNVERIFIED — human triage`.

## The 3 pre-found scoping seeds (start the verification here)

1. **`computer` orphan option** — valid `TARGET_READERS` value + `/customize` reader option, NO `FORMAT_MATRIX` row → silent everywhere-alias, no catalog asset, no test. (`cross-product` + `options-completeness`.)
2. **kindle declared ≠ built** — `FORMAT_MATRIX` kindle row declares `target_reader:"kindle"`, ships everywhere base + `kindle_post`. (`cross-product`.)
3. **standalone target degeneracy** — `apply_target_override` raises on a standalone `--target-reader`; geez/amharic = one shape each. (`cross-product`.)
4. **headline NEW gap** — code/template leak + built-artifact HTML well-formedness has NO gate (`[Reviewer:]` lint is commit-time only; G1 nested-anchor is base-only). (`html-integrity` + `audit_output_hygiene.py`.)

## Lane / side-work division (truth_owner = windows)

| Lane | Engine | Side-work |
|------|--------|-----------|
| WIN | all 11 `ROUND16_DIMS` | full-catalog build-inspect harness + `audit_output_hygiene` + existing gates; owns `build_edition.py` |
| MAC | all 11 `ROUND16_DIMS` | cross-OS verify (9 KJV golden → G1 9/9; one catholic-study eink → gates) + build-free gate `_selftest` |

## Gate deliverables (authored during the run; permanent)

- `dev/audit_cross_product.py` (build-free, dim 4 — headline) + `dev/audit_customize_completeness.py` (build-free, dim 9) → `tests/test_round16_source_gates.py`.
- `dev/audit_output_hygiene.py` (merged artifact scanner, dims 5/6/7/8; reuses audit_spine_breaks + audit_badge_conservation[extended] + audit_idmap_frags) → `tests/test_round16_build_gates.py`.
- `lint_rules` checks (dim 3): subprocess `stdin=DEVNULL`; `epub_working/` writes via `notes_io.atomic_write`.

## Log

- **2026-06-27 setup (WIN)** — plan approved; `deep-audit.js` configured (ROUND=16, 8 new dims, ROUND16_DIMS, selector, DEFERRED folded, PRIOR_SURVIVORS updated, stale pointer fixed; node syntax OK; all 11 keys resolve); program doc + this tracker authored; `dev/LANE_HANDOFF.md` Mac block pushed. **Audit NOT started this session** (user directive). Next: the fresh WIN session + the Mac session run their lanes autonomously to completion.
- **2026-06-27 WIN lane RUN (this session)** — bootstrap + env-health (CommitFree ~50 GB, no AppXSvc leak; tree clean; in sync both remotes) + `git pull --rebase` (up to date). Flipped local `LANE='win'` (NOT committed; revert before push). Launched the engine `Workflow` `wf_571060b9-289` (LANE=win, ROUND=16, 11 dims, feature-dev agents; confirmed running with the WIN repo path + DEFERRED fed). **Authored 3 gates (ruff-clean, selftests pass):**
  - `dev/audit_output_hygiene.py` — R16 headline merged artifact scanner (families A html-integrity/code-leak [NEW] · B whitespace/pagebreak [reuses `audit_spine_breaks`] · C display-redundancy · D orphan-aside marker-logic). `--selftest` PASS (9 leak hits on dirty / 0 on clean; nested-`<a>` detected).
  - `dev/audit_cross_product.py` — R16 build-free dim-4 gate → **surfaced F1 (`computer` orphan)**; checks 1/2/4/5 PASS (seeds #2/#3 = non-defects). `--selftest` PASS.
  - `dev/round16_build_inspect.py` — the full-catalog build-inspect harness driver (RAM-safe ladder; flagship eink LAST+SOLO w/ CommitFree pre-flight; incremental JSON; per-asset scan suite). Ruff+parse clean; smoke-test (catholic-study:everywhere) RUNNING.
  - In flight: Explore recon of `/customize` field-wiring (for `audit_customize_completeness.py`, dim 9). **Heavy full-catalog build sweep + final merge staged for a FRESH session** (user-directed RAM seam).
- **2026-06-27 WIN lane — gates committed + sweep launched autonomously (`c01ba2e9`).** Smoke-test (catholic-study everywhere+kindle) VALIDATED the harness end-to-end: zip/epubcheck/idmap/badge PASS; hygiene **content-clean** (leak_hits=0, nested=0, orphan_asides=0, empty-anchors/asides=0). Two tooling refinements applied from the smoke-test: (a) gate subprocesses importing `scripts.*` now get `PYTHONPATH=repo` (audit_canonical_order had errored `ModuleNotFoundError: scripts`); (b) hygiene mid-chapter spine-break severity is now **reader-aware** — FAIL on eink (forces a page break), WARN on reflowable everywhere/tablet (it found psa 119:88→89 + dan 12:21→22 on the everywhere build = reflowable-low-impact, not a defect). **Dim-3 lint deliverable largely PRE-EXISTS**: `lint_rules.py` already enforces "subprocess calls pass explicit stdin=" (W-W1) + "Atomic writes (no raw open('w') outside notes_io)" — both PASS; a new dim-3 lint is unnecessary (note for the merge). Gates committed (6 files, pre-commit incl. mypy green). **Build sweep RUNNING** (`--skip-flagship`, 13 jobs / 20 assets, bg `bsen5mmqv`) concurrently with the engine; **Monitor armed** (`babphifvi`) streaming per-job progress. Flagship-eink (job 12, RAM ceiling) + standalones-if-needed + final merge = the fresh-session handoff.

---

## ▶ CONSOLIDATED MERGE (WIN lane) — engine + harness + build-free gates

**Engine (`wf_571060b9-289`, LANE=win):** deduped 36 → **survived 26** (3 medium · 23 low), refuted 10. Full data: `round16-engine-win-survivors.json` · plan `round16-engine-win-plan.md` · completeness-critic `round16-engine-win-completeness.md`.

> Dedup: engine #12/#16/#20 = build-free **F1** (`computer` orphan); engine #17/#21 = build-free **F2** (`verse_marker_glyph` orphan) — same defects, independently corroborated source+gate.


### Engine survivors — MEDIUM (3)

| # | dim | title | file:line | note |
|---|-----|-------|-----------|------|
| 1 | correctness (was high) | Core config loaders read glyph-bearing YAML with the platform-default encoding (cp1252 crash on Windows) | `scripts/core/config.py:280, 292, 316, 341` | |
| 2 | builder-robustness (was high) | Study-glossary str splitter holds ~3x copies of the body (offset-vs-slice not done); the structure-surprise fallback reintroduces the full-monolith OOM the | `scripts/build_edition.py:5191-5236 (residual); 5386-5393 (fallback amplifier)` | |
| 3 | display-redundancy (was high) | Round-16 display-redundancy gate (family C) is a dead check: scans for a class the build never emits, and omits the body/byline checks its docstring promis | `dev/audit_output_hygiene.py:108, 200-209 (docstring 26-27)` | |

### Engine survivors — LOW (23)

| # | dim | title | file:line | note |
|---|-----|-------|-----------|------|
| 4 | correctness (was medium) | Authoring/dev tools read & write Unicode content without encoding= (same cp1252 hazard; writes can also raise UnicodeEncodeError) | `scripts/add_note.py:add_note.py:149,203; add_kind.py:60,79,85,95; bulk_inject.py` | |
| 5 | correctness | dashboard_stats() runs its second SQL query on a connection that has escaped the _read_cursor() lock (gap-4 use-after-close race) | `scripts/core/corpus_index.py:1487-1514` | |
| 6 | correctness | translations.get_chapter sorts by raw verse value, crashing on 'own'-versification stores that mix int and lettered verse keys | `scripts/core/translations.py:241` | |
| 7 | security | _send_file magic-byte verification is defeated by the extension fallback in _detect_format — non-image bytes with a whitelisted extension are served with a | `scripts/web.py:1345-1355` | |
| 8 | cross-module | run_kenyon_at_scale.py --books filter is not normalized → a legacy alias silently drops that book's candidates | `scripts/run_kenyon_at_scale.py:116-117, 132` | |
| 9 | cross-module | add_note.py routes the notes-file write through the raw --book alias after get_book only normalized validation (crash on legacy alias) | `scripts/add_note.py:301, 322, 346` | |
| 10 | builder-robustness (was medium) | Flagship glossary from-file streamer's structural fallback re-materializes the whole-document str while still holding the 480 MB raw bytes (re-introduces t | `scripts/build_edition.py:5390-5393` | |
| 11 | cross-product | Cross-product gate audit_cross_product.py checks only the /customize reader dropdown, not the wizard target cards — a parallel target_reader entry point th | `dev/audit_cross_product.py:49-74` | |
| 12 ·DUP F1 | cross-product (was medium) | `computer` is an orphan reader target — selectable in /customize + wizard, but has no FORMAT_MATRIX cell, no build behavior, and no catalog asset | `scripts/build_edition.py:1977 (TARGET_READERS); 2034-2086 (FORMAT_MATRIX); 1766-` | |
| 13 | html-integrity (was medium) | Output-hygiene gate misses html.escape'd Python class reprs (<class '...'>) — _unescape only decodes &lt;/&gt;/&amp;, not &#x27; | `dev/audit_output_hygiene.py:115-116, 78, 149-152, 329-357` | |
| 14 | whitespace-pagebreak (was medium) | apply_eink_verse_line_breaks ignores verse-p-flush — leaves an empty paragraph and drops flush styling at every chapter/stanza opener | `scripts/build_edition.py:3965, 3976-3999` | |
| 15 | display-redundancy (was medium) | S2 cascade body-boilerplate de-dup is gated on note_attribution_dedup instead of note_group_by_category — category text prints twice in the {S1-off, S2-on} | `scripts/build_edition.py:4226-4243 (helper 3004-3025)` | |
| 16 ·DUP F1 | options-completeness (was medium) | `computer` target_reader is offered + accepted but has no build branch or FORMAT_MATRIX row — a dead option that silently builds as an `everywhere` alias | `scripts/build_edition.py:1977, 2034-2086` | |
| 17 ·DUP F2 | options-completeness | `verse_marker_glyph` is schema'd + validated + echoed + has a /customize control but is read NOWHERE on the build/cover path (orphan option) | `scripts/api/editions.py:68, 1256-1257` | |
| 18 | options-completeness (was medium) | Change-impact Preview hides + misreports real savable options: `api_preview_edition_changes` keeps a duplicate EDITABLE allow-list that has drifted from th | `scripts/api/editions.py:695-756, 786` | |
| 19 | options-completeness (was medium) | Four /customize options never display their saved value (loader leg missing in api_customize_data) | `scripts/web_editions.py:393-499` | |
| 20 ·DUP F1 | options-completeness (was high) | `computer` target_reader is an offered option that produces output identical to `everywhere` (dead/meaningless choice) | `scripts/build_edition.py:1977` | |
| 21 ·DUP F2 | options-completeness | `verse_marker_glyph` is a savable /customize option with no build consumer (orphan); catholic-study's `¶` is silently ignored | `content/editions.yaml:197` | |
| 22 | options-completeness | Dead eink-unsafe badge guard: `dot` marker_badge_style is not rejected server-side for eink builds | `scripts/build_edition.py:2278` | |
| 23 | os-binary-parity | Linux AppImage ships an unbranded placeholder icon while Win/Mac carry the branded app icon (cross-OS branding divergence) | `dev/build_appimage.sh:80-97` | |
| 24 | os-binary-parity | Windows desktop build installs an UNPINNED PyInstaller, diverging from the CI/Mac pin (could build the shipping .exe on an untested major) | `dev/build_desktop.cmd:19-24` | |
| 25 | os-binary-parity | build_appimage.sh has unreachable code and a contradictory user message after the appimagetool guard | `dev/build_appimage.sh:42-50` | |
| 26 | os-binary-parity | Frozen Windows .exe carries no version resource while the macOS .app embeds CFBundleVersion (file-metadata parity gap) | `dev/launcher.spec:217-237` | |

### ⚠ Findings about the round-16 gates themselves (fix before relying on them)

- **#3** (medium): `audit_output_hygiene.py` family C (display-redundancy) is a **dead check** — scans a class the build never emits + omits the body/byline checks its docstring promises.
- **#11** (low): `audit_cross_product.py` checks only the /customize dropdown, **not the wizard target cards** (a parallel `target_reader` entry point).
- **#13** (low): `audit_output_hygiene.py` `_unescape` misses `&#x27;` → an html.escape'd `<class '…'>` repr leak slips past the leak detector.


### WIN build-inspect harness (built artifacts)

| edition | format | result |
|---------|--------|--------|
| catholic-study | everywhere | clean |
| catholic-study | kindle | clean |
| evangelical-reformed | everywhere | clean |
| evangelical-reformed | kindle | clean |
| eastern-orthodox | everywhere | clean |
| eastern-orthodox | kindle | clean |
| ethiopian-tewahedo | everywhere | clean |
| ethiopian-tewahedo | kindle | clean |
| catholic-study | apple-tablet | clean |
| evangelical-reformed | apple-tablet | clean |
| eastern-orthodox | apple-tablet | clean |
| ethiopian-tewahedo | apple-tablet | clean |
| catholic-study | eink-epub | clean |
| catholic-study | kobo-kepub | FAIL epubcheck,audit_idmap_frags,audit_glossary_contract |

_14 assets scanned so far. eastern-orthodox eink + 2 standalones + the flagship ethiopian-tewahedo eink (RAM ceiling) = fresh-session._

> **Kepub gate-applicability (NOT product defects):** the catholic-study `kobo-kepub` idmap/glossary/epubcheck FAILs are harness-scope — `audit_idmap_frags`+`audit_glossary_contract` are PLAIN-eink-epub gates (kepubify koboSpan inflates the glossary cap [gate WARNs this] + per-document layout ids `book-columns`/`book-inner`, never link targets, read as cross-piece dups), and epubcheck **timed out under engine CPU load** (not an error). The plain `eink-epub` scanned **clean** on all gates, and `verify_kr2_build` (the authoritative Kobo gate) **passed GREEN**. Harness fixed to be kepub-aware (skip idmap/glossary on kepubs; epubcheck best-effort).

### Final WIN sweep state (sweep killed mid-standalone-geez — non-flagship ladder essentially complete)
- **18 assets scanned, all 11 non-standalone jobs done:** 4 everywhere + 4 kindle + 4 tablet + 3 filtered eink-epub = **ALL CLEAN**.
- **All 3 filtered kepubs** (catholic/evangelical/eastern `kobo-kepub`) show the **identical** epubcheck/idmap/glossary pattern → confirms it is **systematic harness-applicability, not a product defect** (idmap/glossary are plain-eink-epub gates; verify_kr2_build green; the plain eink-epub clean on all). Harness now kepub-aware.
- **Remaining (fresh session):** the 2 standalone builds (geez/amharic — FUTURE per DEFERRED, low priority) + the **flagship ethiopian-tewahedo eink** (RAM ceiling). Resume steps in `dev/IN_FLIGHT.md`.

---

## ▶ CROSS-LANE CONSOLIDATION (both lanes complete) — 2026-06-27

Both deep-audit lanes ran to completion + adversarially verified. **Detailed per-lane plans:** WIN `round16-engine-win-plan.md` + completeness `round16-engine-win-completeness.md`; MAC `round16-engine-mac.md` (carries its own Phases 1–7 + optimization-verdicts + constraints).

- **engine-win:** 36→**26** survivors (3 medium, 23 low), 10 refuted.
- **engine-mac:** 32→**20** survivors (2 medium, 18 low), 12 refuted. **9 touch `build_edition.py`/`epub_working/` → WIN-owned fix surface.**
- **WIN build-inspect harness:** 18 artifacts, all everywhere/tablet/kindle/eink-epub **CLEAN**; 3 kepubs = harness-applicability (now kepub-aware).
- **MAC cross-OS verify ✅ (done-def #3):** G1 9/9 byte-identical Win↔Mac · G3/G4/G5/G6 PASS on a fresh macOS catholic-study eink. ☐ `audit_output_hygiene` + the build-free `_selftest`s on macOS = **pending Mac re-pull** (WIN's gates just landed/pushed).

### Dedup map (same defect, both lanes — count once)
- **F2 `verse_marker_glyph` orphan** = engine-win #17/#21 = engine-mac #18.
- **AppImage placeholder icon** = engine-win #23 = engine-mac #20.
- **4 options don't display saved value** = engine-win #19 = engine-mac #19.
- **Glossary ~3×-copy / whole-doc fallback OOM** = engine-win #2/#10 ≈ engine-mac #9/#12 (+ mac #10 enrich_nav OOM, #11 ThreadPool-eink are sibling RAM hazards).
- **F1 `computer` orphan** = engine-win #12/#16/#20 (+ my build-free gate); mac did not re-raise it.

### ★ Priority items (5 mediums across the lanes)
1. **[mac#1, medium, WIN] Kindle DIRECT build path ships the E999-failing variant** — `build_one` never applies `make_kindle_safe`; only the matrix path (`build_format_matrix._apply_kindle_post`) does. **This refines/corrects my seed#2** ("kindle declared==built") — the *matrix* path is correct, but a desktop /customize user who picks 📬 Kindle + rebuilds gets a non-deliverable artifact. (My cross-product gate only checked the FORMAT_MATRIX level → missed the build_one path — a gate-coverage gap to close.)
2. **[mac#2, medium, WIN] eink study-glossary return link teleports to chapter start** for the 13 Strategy-B books that DO carry v-anchors (psa/job/kings/...) — turn-135 regression; gate on actual v-anchor presence, not `strategy=='B'`.
3. **[win#1, medium] `config.py` reads glyph YAML without `encoding="utf-8"`** → cp1252 crash on Windows without PYTHONUTF8 (4 loaders).
4. **[win#2, medium, WIN] glossary str-splitter ~3×-copy + structure-fallback OOM** (≈ mac#9/#12).
5. **[win#3, medium] my own `audit_output_hygiene` family-C is a dead check** — fix before relying on the display-redundancy dim.

### Notable lows (cross-lane, by theme)
- **Code/placeholder leak in shipped output:** mac#16 `TODO_CERTIFIER_NAME` in every edition's OPF (a11y:certifiedBy) — the html-integrity class, but in the .opf (my hygiene scanner only scans html/xhtml → extend to .opf). mac#15 reviewer-scaffold lint screens only the body field.
- **Security boundaries:** mac#5 note-editor READ path innerHTML unsanitized; mac#6 SSRF allowlist bypassed by redirects; win#7 `_send_file` magic-byte defeated by extension fallback; mac#14 `sanitize_html` emits unbalanced/nested-`<a>`.
- **Book-code ★BUGCLUSTER:** win#8/#9 (run_kenyon/add_note alias) + mac#7/#8 (patristic lint omits the 6th store) — prefer the glob-based lint fix.
- **My round-16 gate self-fixes:** win#3 (family-C dead), win#11 (gate misses wizard target cards — Mac corroborates a parallel `target_reader` entry point), win#13 (`_unescape` misses `&#x27;`).
- **OS-binary parity:** win#24 unpinned PyInstaller, win#25 unreachable code, win#26 no Windows version resource (+ the shared AppImage icon).
- **Cross-OS harness bug (mac-observed):** the EXISTING `tests/test_round14_build_gates.py:58` runs gates via subprocess WITHOUT `PYTHONPATH`/`cwd` → `audit_canonical_order` fails on clean macOS — the same fix I applied to the round-16 harness should land in `test_round14_build_gates.py` too.

### Combined next-round seeds (completeness-critics: WIN 7 + MAC 8)
Kepub colour-variant fan-out (only 1 colour scanned) · no build-time enum validation of `editions.yaml` (validate_schemas is type=str only) · the website **release-catalog** as a 3rd offering surface (`gen_release_catalog`) · eink/kepub **cross-OS determinism** (only 9 KJV cells gated; Win/Mac eink xref count already diverges) · per-book/chapter **override→marker** chain · kindle_post output shape · the whole 6-store enumeration class. Full text in the two completeness files.

### ▶ Remaining (fresh session — RAM seam) — then STOP
1. WIN flagship **ethiopian-tewahedo eink** build + the 2 standalones (the kepub-aware harness; CommitFree pre-flight).
2. Mac re-pull → run `audit_output_hygiene` + the build-free `_selftest`s on macOS (done-def #3b/#3c).
3. Produce ONE unified severity-RANKED remediation plan from the two lane plans (safest-first), present for user approval. **FINDINGS-ONLY — no fixes this round.**
