# Program — Round 14 Deep Audit of the New Build Pipeline + the Resulting EPUBs

> **STATUS: USER-APPROVED 2026-06-26** (planned in plan mode by Mac on the user's directive; charter
> `dev/audit/build-pipeline-deep-audit-charter-2026-06-25.md`). This is the promoted program doc — it
> now runs as the next autonomous two-lane round, parallel mode, file-disjoint, loop-until-green.
> **truth_owner = windows.** Mac = read-only code analysis + structural/product epub audits on macOS
> builds + semantic passes + the NEW deterministic finders' *detection* runs. WIN = all build-path
> fixes + the new-gate code/golden commits + device builds.
>
> **Immediate next actions:**
> - **Mac (now):** Phase 0 product baseline (build C2–C10, run the 5 auditors + epubcheck) ∥ Phase 1
>   `deep-audit.js` semantic fan-out (`LANE=mac ROUND=14 SCOPE=product DEPTH=deep`). C1 flagship-eink
>   attempted isolated/MAX-1; deferred to WIN if the 8 GB box OOMs.
> - **WIN:** (1) land the 1 remaining flagship-eink OOM site (unblocks C1); (2) own the build-path fixes
>   surfaced in Phases 1–2 (TDD + byte-proof each); (3) build + commit the 5 new gates G1–G5 + the
>   `tests/golden/kjv_golden_hashes.json` manifest (G1 is the headline — there is NO golden-hash gate
>   today, confirmed). Mac cross-OS verifies each.

---

## Context

The YHWH build pipeline was substantially re-architected over the last weeks — a new eink page-break
strategy (per-book base-file merge + mid-verse re-join + 8 MB per-book sharding), a streaming
study-glossary split with several OOM frees, a WS2 note-cascade de-duplication, WS3 eink popup
separators, eink font `!important` rules, and a pending 158-verse versification re-split of the shared
base HTML. These changes are eink-gated and the 9-KJV editions are supposed to stay byte-identical —
but **there is no automated KJV golden-hash gate** (confirmed: `tests/test_byte_stability_gate.py` is
determinism-only — it proves rebuild==rebuild, which cannot catch a leak that lands identically in both
rebuilds), several memory frees rest on unproven "nothing reads this after" claims, and the new
machinery carries many order-of-operations and silent-fallback hazards that can emit a
structurally-valid-but-**wrong** epub with no gate firing.

User directive (2026-06-25): *"a very deep audit for the new way the program builds the epubs and the
resulting epubs — for any error, redundancies, contradictions. Everything in the program or the product
it creates."* + Mac-lane extension: **include any logic fault in the program that can silently
propagate into an error in the epubs it builds** — off-by-ones, swallowed exceptions, degrading
fallbacks, eink-gating leaks (the propagation lens).

## Scope: TWO targets × THREE lenses (+ propagation)

- **TARGET A — the PROGRAM:** `scripts/build_edition.py` (+ `build_standalone.py`, `build_epub.py`,
  `build_format_matrix.py`, `core/build_cache.py`).
- **TARGET B — the PRODUCT:** the built epubs — every edition × format × reader-target.
- **Lenses:** ERROR · REDUNDANCY · CONTRADICTION.
- **Propagation lens:** each build-pipeline logic branch → the specific product defect it can silently
  cause (no crash, no gate, wrong artifact).

## Product matrix & the byte-stability invariant

6 editions × 4 reader-targets (`everywhere`/`eink`/`tablet`/`kindle`) × 2 formats (epub, kepub) ≈
**48 cells**. 4 study editions (ethiopian-tewahedo flagship, catholic-study, evangelical-reformed,
eastern-orthodox) + 2 standalone (standalone-geez, standalone-amharic, via `build_standalone.py`/
`pack_book_chapters`).

- **9-KJV byte-stable set** = {catholic-study, evangelical-reformed, eastern-orthodox} × {everywhere,
  tablet, kindle} = **9 cells that MUST ship byte-identical** when no scripture/base change occurs —
  **and, per the 2026-06-26 cross-OS amendment (dimension A15), byte-identical across Windows / Linux /
  macOS too** (CRLF-vs-LF in the zip/text path makes them OS-divergent today; the A1 LF chokepoint
  closes it). eink + standalones are deliberately re-baselineable.
- **No golden-hash gate exists** — byte-stability is proven today only by manual regen + `git diff`.
  Closing this = the round's headline deliverable (gate G1).
- **Integrity invariant:** matrix == build == config through one resolver (`config.enabled_kind_codes`),
  pinned by `tests/test_enabled_kinds_unified.py`. Live figures (pull fresh): 87 books · 1,702 chapters ·
  72 kinds · 15 categories · ~91.7k notes.

## Finder inventory (today)

5 deterministic auditors in `dev/` (built epub/kepub in, exit non-zero on ERROR): `audit_book_
structure.py` · `audit_spine_breaks.py` (mid-chapter=ERROR; `--max-chapter-breaks`) · `audit_verse_
formatting.py` (`--all`) · `audit_popup_formula.py` (`--pin`) · `audit_translation_integrity.py`
(`--selftest`). Plus `.claude/workflows/deep-audit.js` (Opus-pinned find→verify→synthesize),
`ALL_CHECKS`=37 lint rules, the determinism-only byte-stability gate, the nested-anchors base-invariant
gate, epubcheck (`--jar`, Mac Temurin `~/.local/bin/java`). The coverage gaps these miss → the new
gates.

## Audit dimensions

Each tagged **E**rror / **R**edundancy / **C**ontradiction.

### TARGET A — the PROGRAM (`build_edition.py` unless noted)

| id | Lens | Surface | Finder |
|----|------|---------|--------|
| **A1** eink-gating leak | E·C | the ~9 `=="eink"` branches + kw-only `eink=` thread through the cascade chain | **NEW** `audit_eink_gating_leak.py` (static) + proven in B10/G1 |
| **A2** file-split order-of-ops | E | `apply_file_split` (merge→midverse→split→opener-pop→idmap→rewrite→OPF→nav) | deep-audit.js `file-split` + `audit_book_structure` |
| **A3** idmap-incomplete link rewrite | E (prop) | `rewrite_links` bare/full-href fallback on idmap miss | **NEW** `audit_idmap_frags.py` (G3) |
| **A4** merge abort-to-noop + remap | E·C (prop) | `_merge_scripture_base_files` (None→return 0; per-segment `.replace`) | **NEW** `audit_merge_invariants.py` |
| **A5** glossary-split fall-through | E (prop) | `_iter_study_glossary_pieces` 5 unsplit fall-throughs | **NEW** `audit_glossary_contract.py` (G5) |
| **A6** OOM free-after-use | E (prop) | `del pre_badge_texts`/`repair_texts`, `stats.pop(_study_backmatter_entries)`, glossary `del body/inner/text` | **NEW** `audit_free_after_use.py` (static dataflow) + per-branch tests |
| **A7** mid-verse merge heuristic | E | `_merge_mid_verse_breaks` (lead-prose∧marker∧anchor; book-boundary tracking) | `audit_verse_formatting.py` + **NEW** edge-enum tests |
| **A8** keepset↔auditor drift | C | `_MIDVERSE_BREAK_KEEP_BOOKS` vs auditor `POETRY_BOOKS`+`IRREGULAR_BOOKS` | **NEW** `test_midverse_keepset_parity.py` |
| **A9** cache-key input coverage | E·C (prop) | `core/build_cache.py:compute_cache_key` omits `build_epub.py`/`build_standalone.py`/`build_format_matrix.py`/`core/*` resolvers | **NEW** `test_cache_key_inputs.py` + deep-audit.js `concurrency-caching` |
| **A10** swallowed-exception inventory | E·R | sidecar 7322/7342, `cache_key→None` 7775, `cache_store→pass` 8277 | deep-audit.js `correctness` |
| **A11** standalone path divergence | R·C | `pack_book_chapters` hardcodes `geez_{book}` stem for BOTH geez+amharic; duplicates study merge logic | deep-audit.js `cross-module` |
| **A12** redundant disk passes | R | `apply_file_split` re-reads each piece ~5×; two whole-corpus dict loads; superseded `split_study_glossary_document` | deep-audit.js `opt-build` |
| **A13** determinism / ordering / parallel | E (prop) | idmap dict-order, `iterdir` ordering, `ThreadPoolExecutor` shared output_dir | byte-stability gate + deep-audit.js `byte-stability` |
| **A14** docstring↔code contradictions | C | stale "73 MB"/"480 MB" figures, "grep-verified" claims, drifted line refs in deep-audit.js | deep-audit.js `docs` |
| **A15** cross-OS build determinism + feasibility ★2026-06-26 amendment | E·C (prop) | the `write_text`/`read_bytes`+zip path emits **CRLF on Windows, LF on Mac/Linux** → the same byte-stable edition is **NOT byte-identical across OSes** today; build feasibility diverges (`apply_badge_markers:4444` OOMs on 16 GB Windows, completes on 8 GB Mac via compression) | **NEW** A1 LF chokepoint (`zip_repro.ocf_member_bytes`) + G1 cross-OS golden + A4 ubuntu CI; feasibility = C1–C10 must complete on BOTH Win + Mac |

### TARGET B — the PRODUCT (built artifacts)

| id | Lens | Finder |
|----|------|--------|
| **B1** structural completeness (internal) | E | `audit_book_structure.py` |
| **B2** completeness vs EXPECTED canon ★biggest gap | E | **NEW** `audit_canon_completeness.py` — the unimplemented "v2 layer": enumerate the edition's canonical coords from the resolver → assert presence (the only finder that catches a *silently dropped* book/verse) |
| **B3** spine page-breaks | E | `audit_spine_breaks.py --max-chapter-breaks 0` |
| **B4** verse-body formatting | E | `audit_verse_formatting.py --all` |
| **B5** popup/footnote contract | E | `audit_popup_formula.py` + deep-audit.js `popup-separators` |
| **B6** cross-file link / nav resolution | E | **NEW** `audit_idmap_frags.py` (G3) + `audit_book_structure` nav check |
| **B7** note redundancy / contradiction | R·C | `audit_book_structure` + deep-audit.js `cascade-dedup` semantic pass |
| **B8** validity + fonts | E | `epubcheck.py` + `check_nested_anchors.py` |
| **B9** eink font application | E·C | **NEW** `audit_eink_fonts.py` |
| **B10** 9-KJV cross-target byte-equality ★no gate today | C | **NEW** `test_kjv_golden_hash_gate.py` (G1) |
| **B11** data / translation integrity | E | `audit_translation_integrity.py` |
| **B12** kepub conversion fidelity | E | **NEW** `audit_kepub_conversion.py` (pin kepubify v4.0.4 + diff) |
| **B13** artifact inventory (matrix==build) | C | **NEW** `audit_artifact_inventory.py` |

### Propagation lens (program branch → silent product defect, no gate today)

P1 eink mutation leaks to 9-KJV base (A1→G1) · P2 orphan-marker bail drops a note silently
(`badges_skipped++` only → G4) · P3 glossary unsplit busts Kobo cap (A5→G5) · P4 idmap miss →
dead/wrong cross-file link (A3→G3) · P5 merge no-op ships half-merged tree (A4) · P6 stale cache serves
old epub after a real change (A9) · P7 mid-verse mis-detect reorders verse text (A7) · P8 `except…pass`
ships a degraded-but-valid epub (A10) · P9 kepubify drift silently rewrites every kepub (B12). Each row's
closing finder is a NEW gate — the user's "logic fault → epub error" mandate made concrete and gated.

## New gates / finders (the coverage-gap closers) — WIN builds + commits

**Five build-time invariant gates (G1–G5)** are the priority. G3/G4/G5 → `ALL_CHECKS` (cheap per-build);
G1/G2 → `@pytest.mark.slow` (real builds). WIN commits the code + `tests/golden/`; Mac runs them
read-only to surface drift.

1. **G1 — KJV golden-hash gate (`test_kjv_golden_hash_gate.py`) ★headline.** Builds each non-eink
   byte-stable cell, content-digests it (reuse the existing `_content_digest` URN/modified/date/
   rights-year normalizer from `tests/test_byte_stability_gate.py`), asserts `==
   tests/golden/kjv_golden_hashes.json`; `--regen` re-stamps the golden **only** on a deliberate,
   reviewed base re-baseline. Automates "manual regen+diff"; proves/refutes every eink-gating leak (A1).
2. **G2 — eink-gating-leak detector (`audit_eink_gating_leak.py`).** Build one representative non-eink
   cell at `HEAD~1` and `HEAD`, unzip+normalize, `diff -r` must be empty. Folds into G1 in CI.
3. **G3 — idmap/cross-file-link gate (`audit_idmap_frags.py`).** Post-split: every `href`/`#frag`
   resolves to the piece holding the id; every noteref target resolves; ids unique across pieces; no
   orphaned spine piece. (Closes A3/B6/P4 — `audit_popup_formula` only checks same-file hrefs.)
4. **G4 — orphan-marker / badge-conservation gate (`audit_badge_conservation.py`).** `badges_skipped==0`
   **and** badge count == pre-collapse marker count **and** 0 orphan markers. (Closes P2.)
5. **G5 — glossary-format-contract validator (`audit_glossary_contract.py`).** Every glossary piece ≤
   navigate-target cap; no piece packs two book-heads; atom count == badge entries; streaming split ==
   the str-path reference bytes (the catholic 453/453 proof, made standing). (Closes A5/P3.)

**Plus additive finders** (deterministic/static, Mac-owned detection): `audit_canon_completeness.py`
(B2 — highest-value additive) · `audit_merge_invariants.py` (A4) · `audit_free_after_use.py` (A6) ·
`test_cache_key_inputs.py` (A9) · `test_midverse_keepset_parity.py` (A8) · `audit_eink_fonts.py` (B9) ·
`audit_kepub_conversion.py` (B12) · `audit_artifact_inventory.py` (B13). Doctrine: prefer a commit-time
`lint_rules` check over a pytest-only guard for invariants that recur every ingest.

## Approved cross-OS amendment (2026-06-26 — USER-APPROVED, plan mode)

WIN vetted this program in plan mode for Windows/Linux/macOS final-build coverage and the user approved
a cross-OS amendment that folds in here (A5 of the amendment = this section). Gap found: the program
was strong on within-OS correctness but (a) never defined "cross-OS verify", (b) had **no Linux at
all**, and (c) **nothing proved the final EPUBs are byte-identical across OSes**. Two concrete defects:
a **CRLF-vs-LF leak** (the build's `write_text`/`read_bytes` + zip step emit CRLF on Windows, LF on
Mac/Linux → the same "byte-stable" KJV edition is NOT byte-identical across OSes today) and
**build-feasibility divergence** (`apply_badge_markers:4444` MemoryErrors on 16 GB Windows but completes
on the 8 GB Mac via compression, so a Mac-only Phase-0 would miss Windows-only build failures).

- **A1 — LF chokepoint.** `ocf_member_bytes(name, data)` in `scripts/core/zip_repro.py`, wired at
  `build_epub.py:161` + `kindle_post.py:_ocf_rezip:121` (text-extension allowlist
  `.html/.xhtml/.xml/.opf/.ncx/.css/.svg`, `data.replace(b"\r\n", b"\n")` only; binaries/`mimetype`
  untouched) → OS-independent EPUB bytes. A deliberate one-time **Windows** CRLF→LF re-baseline;
  **Mac/Linux bytes do NOT change** (the replace is a POSIX no-op) → no Mac re-baseline. **WIN-owned.**
- **A2 — DONE (`7e9738fa`).** `apply_badge_markers:4444` per-splice rebuild → single-pass
  `_apply_splices` (`"".join`, raises on overlap); fix-the-class +2 in `apply_eink_verse_line_breaks`.
  Byte-identical (guard `test_badge_splice_apply` 12/12 + 251 regression). Removes the Windows-only build
  OOM that blocked C1 feasibility.
- **A3/G1 — cross-OS golden.** `tests/test_kjv_golden_hash_gate.py` + ONE
  `tests/golden/kjv_golden_hashes.json` (reuse the existing `_content_digest`); after A1 the SAME golden
  passes on Windows, macOS AND Linux — that is the cross-OS proof. **WIN builds + commits; Mac verifies.**
- **A4 — ubuntu CI.** A new `kjv-golden.yml` GitHub-Actions-ubuntu workflow builds the 9 byte-stable
  cells on Linux + checks the golden = the automated **Linux-sided** final-build proof (no cloud VM).
  **WIN-owned.**
- **A15 (this program's new dimension).** Cross-OS final-build determinism (9 cells byte-identical
  Win/Linux/Mac via G1) + build feasibility (C1–C10 build to completion on **both** Windows and Mac,
  not Mac-only). Added to the TARGET-A dimension table above.
- **A6 — G2–G5 unchanged** from this program. Sequencing: A2 (done) → A1 → `G1 --regen` on Windows →
  A3/A4.

## Coverage strategy (product builds)

PROGRAM audit runs once, path-complete. PRODUCT target = full-matrix certification (every cell
epubcheck-0/0/0/0 + auditor-green, the 9 byte-stable cells proven by G1), reached via a **path-complete
10-cell sample first, then expand toward all 48** — builds are the cost (MAX-1 on the 8 GB box, spread
across both lanes); the deterministic auditors are cheap and run on every built cell.

**Phase-0 sample (10 cells):**

| Cell | Why | Risk |
|------|-----|------|
| C1 ethiopian-tewahedo · eink · kepub | flagship superset; eink page-break/glossary/separator path; **the open OOM site** | **HIGH (OOM)** — isolated/MAX-1 or via WIN after the OOM fix |
| C2 catholic-study · eink · kepub | canon-splice + KJV popup; builds clean → safe eink representative | low |
| C3 catholic-study · everywhere · epub | non-eink byte-stable base → feeds G1/G2 | low |
| C4 evangelical-reformed · everywhere + eink | smallest canon; byte-stable + eink-merge | low |
| C5 eastern-orthodox · eink · kepub | 4th canon across eink | low |
| C6 catholic-study · kindle · epub | `make_kindle_safe` post-process | low |
| C7 ethiopian-tewahedo · tablet · epub | Apple/tablet popup style; largest non-eink | medium |
| C8 standalone-geez · eink · kepub | `pack_book_chapters`; Geez glyph tofu risk | low |
| C9 standalone-amharic · eink · kepub | standalone Amharic naming + glyph path | low |
| C10 evangelical-reformed · eink · kepub | confirms eink merge on protestant canon | low |

Build cmd: `PYTHONUTF8=1 PYTHONPATH=<repo> .venv/bin/python scripts/build_edition.py <ed>
--target-reader <t> --version 0.1.0 --output-dir <out> --force`; kepubify the eink cells via
`~/.local/bin/kepubify`. **C1's full audit runs against the WIN-built flagship kepub if the Mac box
OOMs** — eink path coverage held by C2/C5/C10 meanwhile.

## Method · adversarial verification · scale

Deterministic where possible (the 5 auditors + epubcheck + the new gates). Multi-agent semantic via
`.claude/workflows/deep-audit.js` (`Workflow({scriptPath})`), configured in-file (args don't propagate —
confirm via the startup-log `argsRound` echo):

- `LANE='mac'`, `ROUND=14`, `NOW='2026-06-25'`, `SCOPE='product'`, `DEPTH='deep'`.
- **Custom `DIMENSIONS`** = perennial product dims (`tests-run` at array head, `correctness`, `security`,
  `byte-stability`, `cross-module`, `data-validity`) **+ new build-pipeline dims** (`pagebreak-rearch`,
  `file-split`, `eink-gating-leak`, `glossary-streaming`, `cascade-dedup`, `popup-separators`,
  `resplit-integrity`), each with 2 perspective-diverse `angles[]`. Drop out-of-scope dims
  (website/dist/platform/lane-system/decommission/stack-review).
- **Scaled skeptic panel:** critical=5 / high=4 / medium=3 / low=2 votes, refute-by-default;
  `unverified` ≠ refuted (carried as a survivor for human triage); per-finding majority
  `corrected_severity`; built-in completeness critic.
- **`DEFERRED_BY_DESIGN`** extended: OOM #1 glossary-streaming DONE (byte-identical); the remaining 1
  flagship-eink OOM site KNOWN-OPEN (WIN owns); the 158-verse re-split USER-GATED; WS1/WS2/WS3 +
  eink-fonts + page-break re-arch SHIPPED (regression/bleed only); vnote-popup U+2028 sibling QUEUED
  (guard #7); 1en 71/90 + 90:13–18 documented; poetry mid-verse = user "keep"; `audit_popup_formula`
  study-glossary-jump false-positive = known recalibration; char-vs-byte kepub packing =
  deliberate-deferred. **Do NOT** defer "no golden hash" — G1 closes it.
- **`PRIOR_SURVIVOR_TITLES`** = round-13 fixes (confirm-not-regress): conftest `_PROTECTED_DIRS`, zip
  `create_system=0`, `inject.escape_attr`, frozen-app `content_root`, orphaned-api-dir removal.

## Lane split (parallel, file-disjoint; `truth_owner = windows`)

| | **Mac lane** | **WIN lane (truth_owner)** |
|---|---|---|
| Code-semantic dims | ALL of the deep-audit.js dims (read-only, `LANE=mac`) | reviews via its own box if it runs its own copy |
| Product builds | C2–C10 on macOS; **C1 isolated/MAX-1 or deferred to WIN post-OOM-fix** | flagship-eink once the OOM fix lands; all device builds |
| Deterministic auditors + new gates | run all 5 + epubcheck + kepubify + **detection** runs of G1–G5 on every Mac-built cell | re-run on WIN-built flagship + device kepub |
| Build-path FIXES | **none** — must not touch `scripts/**` or `epub_working/**` | ALL fixes to `scripts/**`, `epub_working/**`, `content/**` (TDD + byte-proof each) |
| New-gate code + goldens | detection only (read-only) | **build + commit** G1 golden manifest (`tests/golden/`) + wire G3/G4/G5 into `ALL_CHECKS`; owns `tests/**` |
| Byte-stability proof | cross-OS verify each WIN fix; G1/G2 read-only | own the regen+`git diff` re-baseline + commit goldens |
| Device | — | Kobo loads + clean-eyeball gate |
| Writes | `dev/audit/**` only | `scripts/**`, `epub_working/**`, `content/**`, `tests/**` |

Coordination via this `LANE_HANDOFF.md` + the lane-ping radar. File-disjoint → no merge conflict.
User-only calls → `dev/HUMAN_DECISIONS.md`. Pacing (8 GB box): heavy agent (>100k tok) MAX 1; never
pytest beside a build; flagship-eink runs alone.

## Phasing & loop-until-green

- **Phase 0 — product baseline (Mac).** Pull HEAD; build C2–C10; kepubify eink cells; run all 5 auditors
  + epubcheck + G1–G5 detection; `audit_translation_integrity --selftest`. Record
  `dev/audit/round14-structural.md`. Attempt C1 isolated; defer to Phase 3/WIN if it OOMs.
- **Phase 1 — program-code semantic fan-out (Mac).** Configure + run `deep-audit.js` (read-only, TARGET A).
- **Phase 2 — adversarial verify + synthesize (Mac).** Scaled panels + completeness critic; new-gate
  detection feeds in as findings. Emit `round14-mac-survivors.json` + `round14-mac-plan.md`.
- **Phase 3 — remediate loop-until-green (WIN fixes, Mac verifies).** WIN lands the flagship-eink OOM fix
  (unblocks C1) + all build-path fixes (TDD first — a guard that fails pre-fix — then fix, then
  byte-proof; eink-only changes pass G2) + builds/commits the new gates. Mac cross-OS verifies each,
  rebuilds affected cells, re-runs auditors + G1/G2. Expand product coverage toward the full 48. Loop.
- **Phase 4 — byte/device gates + sign-off (both).** G1 green every byte-stable cell; epubcheck 0/0/0/0
  everywhere; suite green incl. slow; clean Kobo eyeball (WIN). Completeness/critic loop until **K=2
  consecutive dry rounds**. Promote to closed.

## Recording & deliverables

`dev/audit/build-pipeline-deep-audit-program-2026-06-25.md` (this doc) · `round14-structural.md`
(Phase-0 baseline) · `round14-mac-survivors.json` (engine output) · `round14-mac-plan.md` (synth fixes) ·
`round14-remediation.md` (WIN-half + merge tracker, same shape as `round13-remediation.md`) ·
`dev/HUMAN_DECISIONS.md` (user-only calls). New gate code + goldens → `dev/` / `tests/` / `tests/golden/`
(WIN-owned).

## Verification (done-definition — ALL must hold)

1. Every deep-audit.js dim **clean** (0 surviving E/R/C; `unverified` survivors triaged). 2.
`audit_book_structure` all-green every built cell. 3. `audit_spine_breaks --max-chapter-breaks 0`
mid-chapter == 0 every eink + standalone cell. 4. `audit_verse_formatting --all` green (protocanon
empty-anchor ≈ 0 post-resplit). 5. `audit_popup_formula` green (post glossary-jump recalibration). 6.
`audit_translation_integrity --selftest` + full scan green. 7. pytest green **incl. `slow`**. 8.
**epubcheck 0/0/0/0 every artifact** across the full matrix. 9. **G1 green every byte-stable cell + G2
green + G3/G4/G5 green.** 10. clean Kobo device eyeball (WIN). 11. completeness critic ≥ K=2 dry rounds.

## Out of scope / already settled (priorSurvivors — don't re-litigate)

WS1 mid-verse merge · the 158-verse re-split (USER-GATED) · WS2 cascade de-dup · WS3 popup separators ·
eink font fix · page-break re-arch (Parts 1/2/2b) · OOM tier-1 + #1 frees. The **1 open flagship-eink
OOM site** is WIN's active fix (this audit verifies, doesn't re-diagnose). The **1en 71/90 + 90:13–18**
content defects and the **char-vs-byte all-edition re-cut** are separately deferred.
