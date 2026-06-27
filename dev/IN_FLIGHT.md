# In-flight work — current task tracker

<!-- TRACKER-STATE: round-16 FINDINGS-ONLY — BOTH engines done + merged (engine-win 26 + engine-mac 20 survivors; cross-lane consolidation in dev/audit/round16-remediation.md). ✅ MAC LANE COMPLETE (cross-OS 3a G1 9/9 + 3b G3/G4/G5/G6 + audit_output_hygiene + 3c source-gate _selftest, all PASS on macOS). WIN remainder = FRESH SESSION (RAM seam): flagship ethiopian-tewahedo eink + 2 standalone build-inspect scans + the ONE unified severity-ranked remediation plan (truth_owner synth). THEN user approves the fixes (next phase, separate). -->
<!-- task: ROUND-15 ✅ ALL DIMENSIONS COMPLETE (D1–D9 both lanes), 2026-06-27. WIN this session: D5 (flagship glossary byte-streamer proven str==from-file 690/690 + G5 PASS + permanent regression; fixed G5 --reference-split false-FAIL on real builds) + D2 (G3 xref-class breakout + --min-xrefs floor wired into the per-build gate; ethiopian 88541 / catholic 55774 xrefs, 0 dead). Mac cross-OS-verified ALL 9 dims (D3/D5/D8/D9 at 4f69aa05 + D2 at 405eda85). D1 LIVE RE-CUT DONE (WIN, user "do it"): removed the 100 retired-SKU EPUBs + SHA lines from the live GitHub v0.1.0 release, gate PASS (87 assets, 0 retired). ★ ROUND-15 FULLY CLOSED, NO REMAINING FOLLOW-UPS. Next = the separate v1.0.0 release gate / next audit round (need a user trigger). Mac monitor stood down at wrap. Tracker dev/audit/round15-remediation.md. -->

<!-- task: ROUND-16 deep-audit PREPARED + Mac instructions pushed (2026-06-27). Engine deep-audit.js configured (ROUND=16, 8 new dims, ROUND16_DIMS=11, selector branch, round-15 D1–D9 + round-14 build-source dims folded into DEFERRED_BY_DESIGN, round-15 fixes in PRIOR_SURVIVOR_TITLES, stale dist pointer fixed; node syntax OK; all 11 keys resolve). Program dev/audit/round-16-build-program-bulletproofing-2026-06-27.md + tracker dev/audit/round16-remediation.md. NOT STARTED (user directive: set up + push Mac, then a FRESH session runs it). FINDINGS-ONLY two-lane (both lanes all 11 dims; WIN full-catalog build-inspect harness; Mac cross-OS verify). -->

> **▶▶ 2026-06-27 — ROUND-16 WIN LANE IS RUNNING (autonomous; user "bootstrap and continue" + monitor armed).**
> Bootstrap + env-health (CommitFree ~50 GB, no AppXSvc leak; tree clean; in sync) + pull (up to date). Local `LANE='win'`
> flipped (NOT committed — revert before push). **Engine `Workflow` `wf_571060b9-289`** (LANE=win, ROUND=16, 11 dims,
> feature-dev agents) running. **Authored + COMMITTED (`c01ba2e9`, findings-only) 3 gates + the harness + tests** (all
> ruff-clean, synthetic selftests, pre-commit incl. mypy green): `dev/audit_output_hygiene.py` (dims 5/6/7/8, headline
> html-integrity/code-leak) · `dev/audit_cross_product.py` (dim 4 → **F1 `computer` orphan**) · `dev/audit_customize_completeness.py`
> (dim 9 → **F2 `verse_marker_glyph` orphan**) · `dev/round16_build_inspect.py` (full-catalog harness) · `tests/test_round16_source_gates.py`.
> **Build sweep RUNNING** (`bsen5mmqv`, `--skip-flagship`, 13 jobs / 20 assets) concurrently; **Monitor `babphifvi`** streams progress.
> Findings live in `dev/audit/round16-remediation.md`. Smoke-test validated the harness (epubcheck/idmap/badge PASS; hygiene content-clean).
>
> **▶ FRESH-SESSION HANDOFF (the RAM-heavy seam, per user 2026-06-27):** when this session's engine + non-flagship sweep finish
> and their findings are recorded, the NEXT (fresh, clean-RAM) WIN session: (1) bootstrap + confirm `LANE='win'` (re-flip if a
> pull reverted it); (2) run the **flagship ethiopian-tewahedo eink** build solo —
> `py -3 dev/round16_build_inspect.py --only ethiopian-tewahedo:eink --out build/r16` (CommitFree pre-flight guards OOM; reboot
> if AppXSvc leak recurs) + the 2 standalones if not yet scanned; (3) collect the engine survivors (both lanes) + harness gate-FAILs
> + Mac cross-OS deltas → **merge** into `dev/audit/round16-remediation.md` (dedup by `keyOf`, source-tag, severity-calibrate,
> verbatim COUNT_LINE); (4) run the completeness-critic + the 8-asks×11-dims coverage matrix; (5) STOP at the phased fixes plan
> for user approval. `git checkout -- .claude/workflows/deep-audit.js` to drop the local LANE flip before any push.
>
> **★ 2026-06-27 — ROUND-16 READY TO RUN (PREPARED — now RUNNING, see above). ▶▶ NEXT WIN SESSION = run the WIN lane autonomously.**
> Build-Program Bulletproofing — audit the EPUB-builder across the full output cross-product (edition × reader-version
> × OS) + options-completeness + display-redundancy + HTML-integrity + per-reader marker-logic + builder-robustness.
> **Two-lane, FINDINGS-ONLY** (rounds 14/15 pattern). The Mac has its standing autonomous block in `dev/LANE_HANDOFF.md`.
> **WIN run steps:** (1) bootstrap + `git pull --rebase`; (2) flip ONLY the local `LANE` line → `const LANE = 'win'`
> (never commit); confirm the engine startup log shows `ROUND=16`; (3) `Workflow({scriptPath:"C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4/.claude/workflows/deep-audit.js"})`
> — runs all 11 `ROUND16_DIMS`; (4) CONCURRENTLY run the full-catalog build-inspect harness (12 base builds + 4
> kindle-posts + 2 standalones → colour fan-out → scan each asset with epubcheck + check_nested_anchors +
> `dev/audit_output_hygiene.py` + G3/G4(extended)/G5/G6; flagship-eink LAST + SOLO; build→scan→free; never pytest beside a build);
> (5) author the new gates (`audit_cross_product.py`, `audit_customize_completeness.py`, `audit_output_hygiene.py`, the
> lint) as findings warrant; (6) record + merge all findings into `dev/audit/round16-remediation.md` (dedup, provenance-tag,
> verbatim `COUNT_LINE`), run the completeness-critic + the 8-asks×11-dims coverage matrix; (7) STOP — present the phased
> fixes plan for the user to approve (NO fixes this round). Program: `dev/audit/round-16-build-program-bulletproofing-2026-06-27.md`.
> Tool/agent parity (Guard #4) + never-pytest-beside-a-build (cap=2) apply.

> **★ 2026-06-26 — ROUND-15 LAUNCHED + RUNNING (WIN, autonomous — user "continue your work" + Mac monitor armed).**
> Plan USER-APPROVED in plan mode; program `dev/audit/round-15-completeness-audit-program-2026-06-26.md` verified
> still-apt vs current code (D3/D4 confirmed LIVE; D2/D9 blindspots real; round-14 SETTLED items on disk). Two-lane
> file-disjoint (truth_owner=windows): **WIN** = `build_edition.py` + D2/D5/D8/D9 + build-needing gates + `deep-audit.js`
> config; **MAC** = `versification.py` + D3/D1/D6/D7 + build-free gates + cross-OS verify. Tracker
> `dev/audit/round15-remediation.md`.
> - **✅ D4 (HIGH) FIXED + PUSHED (WIN, `2afa6126`)** — `_cascade = s2_group` (`build_edition.py:4228`); gen-1
>   `Dictionary (Easton's)` provenance 0→545; regression RED 0≠545 → GREEN; 78 tests; **G1 golden gate PASSED 9/9**
>   (byte-stable empirically confirmed) + tautology (golden cells non-eink ⇒ identical).
> - **✅ D2 PARTIAL + PUSHED (WIN, `2afa6126`+`65bcfa0a`)** — `check_xrefs.py:52` regex guard (`data-*-id` dormant,
>   zero-diff) + **G3 presence floor** (`--min-links`; guards wholesale xref loss → vacuous-green) wired at 10000 +
>   value-flag arg-parse fix. ☐ remaining: G3 xref breakout on a fresh build.
> - **✅ MAC DONE its 4 dims (pulled):** D3 (`_VULGATE_PSALM_FIXES` `(2,13)→(2,12)`+`(4,10)→(4,8)` + coverage gate) ·
>   D1 (release-asset gate; live v0.1.0 has 100 retired-SKU EPUBs → v1.0.0 tag-time re-cut) · D6 (canon book-count
>   gate + de-vacuumed Δ.4) · D7 (migration 0001 torn-safe + idempotence gate). + cross-OS verify pending.
> - **✅ D3 COMPLETE (WIN re-bake, `dev/audit/round15-d3-baked-popup-finding.md`):** the discovery — vulgate/douay
>   popups are BAKED into `epub_working/` (`_BAKED_NOW`), no edition sets `translation_id`, so Mac's store fix didn't
>   reach the shipped popup. Mac resolved the `]` (it's the Clementine psalm-body delimiter → restoring the tail WITH
>   `]` also repairs a dangling unclosed `[`). **WIN surgical 4-append base edit** (Ps 2:12/4:8 vulgate+douay in
>   `index_split_032.html`; confined 4-line diff; `check_nested_anchors` 0 + `test_nested_anchors` 10/10). Verified the
>   restored Latin tail SHIPS in the built epub (`beati omnes qui confidunt in eo` ×1). **G1 golden RE-STAMPED** (6
>   cells = everywhere+tablet × 3 editions; the 3 kindle cells unchanged — kindle compacts the parallel-Latin popup).
>   Mac to cross-OS verify. ⚠ Separator drift (`generate_verse_popups.py` not idempotent-vs-base) = standalone follow-up.
> - **✅ D8 + D9 DONE (WIN, pushed):** D8 `audit_canonical_order.py` (`e57e6c64`) — reading-flow order gate (no defect;
>   validated 1299 ch / 75 books) · D9 `audit_kepub_revid_family.py` (`93d2fb85`) — guard #19 confirmed by-design (rev
>   606 navigate, 0 inline-bare; liveness non-vacuous). Both wired/tested + per-build (D8).
> - **✅ D5 DONE (WIN, 2026-06-27, `dev/audit/round15-d5-glossary-byteproof.md`):** real **255 MB** flagship
>   `index_split_900` monolith str==from-file **byte-identical (690/690 pieces)** + **G5 PASS** on the fresh flagship eink
>   build (`max_inner_cp 399171 < 400000` cap, 0 over-cap, 30148 atoms == distinct) + permanent real-threshold regression
>   `test_real_threshold_byte_branch_identical_to_str_at_scale` (slow, no monkeypatch). Byte branch confirmed firing
>   (255 MB > 64 MB; doc "~480 MB" was a stale str-side estimate). **Found+fixed:** G5 opt-in `--reference-split`
>   false-FAILed on REAL (post-`rewrite_links`) builds → detect+skip+WARN (`_REWRITTEN_HREF_RE`) + regression test.
> - **✅ D2 DONE (WIN, 2026-06-27):** G3 **xref-class breakout** — scripture `v-`/`ch-` cross-references counted +
>   failure-bucketed separately (`xref_links`/`xref_fails`) from the noteref bulk + a dedicated **`--min-xrefs` floor**
>   (the ~45k noteref bulk keeps `--min-links` satisfied even if every xref were dropped); **wired `--min-xrefs 10000`
>   into the per-build gate** (`test_round14_build_gates.py`). Verified on FRESH builds: ethiopian **88,541** / catholic-study
>   **55,774** xrefs, **0 dead**; all 4 per-build gates (G3/G4/G5/D8) PASS; +2 unit tests.
> - **★★ ROUND-15 ✅ FULLY CLOSED (all 9 dims D1–D9 + cross-OS verified, both lanes).** Mac cross-OS-verified D3/D5/D8/D9
>   (`4f69aa05`) AND D2 (`405eda85`: G3 xref-breakout PASS on the macOS catholic-study build, `xref_fails=0`; per-build gate
>   green). **✅ D1 LIVE RE-CUT DONE (WIN, 2026-06-27, user "do it"):** removed all 100 retired-SKU EPUBs + SHA256SUMS
>   lines from the live GitHub v0.1.0 release → D1 gate PASS (87 assets, 0 retired, bijection clean); website references 0
>   retired assets (no breakage). **★★ ROUND-15 FULLY CLOSED — no remaining follow-ups.** Separate future work (needs a user
>   trigger): the v1.0.0 release gate (M2 Apple / Kindle STK / M3 Kobo device taps) · the next audit round · `deep-audit.js:294`
>   stale pointer. _Low-pri cross-OS observation: catholic-study eink G3 xref count Win 55,774 vs Mac 45,057 (not a byte-stable
>   golden cell; floor robust) — future determinism check._
>
> **★ 2026-06-26 — ROUND-14 ✅ COMPLETE (both lanes) · ROUND-15 was PREPARED, now LAUNCHED (above).**
> **Round-14:** all 8 deep-audit survivors GREEN (WIN #4 S1-attr/#5 G1/#6 (HIGH) est-10:2 · Mac #1/#2/#3) + WIN **G5 over-cap** fixed
> (`_atom_rewrite_headroom`) + **A1 cross-OS LF chokepoint** (Mac-verified 9/9 byte-identical Win↔Mac) + **A4** ubuntu CI + **all 5 gates**
> (G1 golden · A4 · G3 idmap · G4 badge · G5 glossary) committed+pushed, G3/G4/G5 wired into a slow per-build gate
> (`tests/test_round14_build_gates.py`); 9-KJV byte-stable PROVEN (golden re-run 9/9). #6 audit-mirror done (Mac, `db049b75`).
> A1 cache-coverage follow-up (`zip_repro`→`_PIPELINE_SCRIPTS`, `48807147`). HEAD `48807147`; both remotes synced; box quiescent.
> **★ ROUND-15 = `dev/audit/round-15-completeness-audit-program-2026-06-26.md` (READ FIRST).** Planned deep-audit of the **9 completeness-critic
> gaps** round-14 flagged as next-round seeds: D1 dist/release pipeline · D2 xref subsystem · D3 `versification.py` fold-tables · D4 /customize
> flag cross-product · D5 glossary-streaming FLAGSHIP verify · D6 `corpus_index`↔matrix book-count · D7 migration definitions · D8 nav/opf
> canonical order (+1en) · D9 kepub bare `-sN` rev-id (guard #19). **Each was independently re-scoped vs current code (a scoping Workflow);
> any concrete defects it spotted are listed per-dimension in the program doc.** **PROCESS (matches round-14): pull → `EnterPlanMode` → review
> the program → `ExitPlanMode` for USER approval → configure `deep-audit.js` (ROUND=15 + dimensions + round-14 settled→deferred-by-design) →
> execute two-lane (WIN build-path + gates / Mac read-only dims), adversarially verify, loop-until-green. Do NOT begin auditing until approved.**
>

> **▶ 2026-06-26 (Mac, autonomous, PARALLEL — both lanes live) — ROUND-14 REMEDIATION IN PROGRESS.** User: "work
> autonomous until you and windows are fully done." ⚠ CORRECTED: WIN was NOT quiescent — it rebooted (cleared the AppXSvc
> commit-leak) and is LIVE on A1(done)/G1/G2-G5; reverted my premature exclusive/mac → PARALLEL, file-disjoint
> (truth_owner=windows; division in LANE_HANDOFF). **Mac delivered:** A5 fold `fc85512f`; **WS1 byte-proof = PASS**
> `e923dfad`; **Phase-1 deep-audit** (`wf_61e196d1-2f2`) 8 survivors/5 refuted → `round14-mac-survivors.json` +
> `round14-mac-plan.md`. **Survivors (tracker `dev/audit/round14-remediation.md`):** ✅ #1 eink_glyphs cache (Mac) ·
> ✅ #2 prospect None-guard (Mac) · #3 canonical-extent (Mac) · #4 S1 attribution (WIN) · #5 G1 golden (WIN, in progress) ·
> #6 est-10:2 merge corruption (WIN build_edition + Mac audit-mirror). Marathon core off-limits.

> **★ 2026-06-26 (WIN, POST-REBOOT RESUME) — A2 CONFIRMED on the freshly-rebooted box · A1 WIRED + P1 green · post-A1 rebuild RUNNING.**
> Bootstrap+pull+continue. Reboot cleared the AppXSvc leak: **CommitFree restored to ~58 GB of 65** (was ~590 MB). Pulled
> 3 Mac commits (rebased clean): A5 cross-OS amendment folded into the program doc · deep-audit engine configured ROUND=14 ·
> **WS1 158-verse re-split all-edition BUILD byte-proof = PASS** (`round14-ws1-byteproof.md`; 9 KJV cells get a ratified
> NEW baseline → **G1 golden MUST be stamped from POST**). Committed the WIP snapshot (`dc9b676c`→rebased): the INERT
> `zip_repro.ocf_member_bytes` A1 helper + the G1 gate test (skips until golden) + the post-reboot IN_FLIGHT note (A4 CI
> held untracked to land with the golden). **✅ A2 CONFIRMED:** built `catholic-study --target-reader eink` (pre-A1) →
> `✓ 24.04 MB`, **exit 0, no swallowed `✗`/MemoryError at `apply_badge_markers:4444`** — the single-pass `_apply_splices`
> fix + commit headroom resolves the WIN-box build-killer → **C1 build-feasibility unblocked on Windows**. Pre-A1 artifact
> captured (`YHWH-builds\catholic-eink-PRE-A1.epub`, SHA256 `C12EA12D…`). **✅ A1 WIRED** at `build_epub.py:161`
> (`ocf_member_bytes(arcname, …)` + REPO_ROOT-on-path import, dual-context verified: standalone subprocess + package/frozen)
> + `kindle_post.py:121` (`ocf_member_bytes(name, …)`; folded the pre-existing unused-`defaultdict` F401). **✅ P1 green**
> (`TestOcfMemberBytes` 6 pins in `test_zip_repro.py`, 9/9). **P2** verifier ready (`dev/audit/round14_a1_byteproof.py`:
> post == `ocf_member_bytes(name, pre)` member-wise). **✅ A1 PROVEN end-to-end:** post-A1 catholic-eink rebuild = exit 0
> `✓ 24.03 MB` (the subprocess import path works) · **P2 PASS** (453 members: 84 byte-identical binaries + **369 CRLF→LF
> text members** [.html×358/.xhtml×8/.css/.ncx/.opf]; 574,104 `\r` removed; OPF volatiles normalized out → A1 = CRLF→LF
> ONLY) · **epubcheck 0/0/0/0** on the LF-normalized epub. **A1 slice PUSHED `17d39197`** (both remotes). **✅ G1 GOLDEN
> STAMPED** (`tests/golden/kjv_golden_hashes.json`, 9 distinct cells, POST-re-split+POST-A1) + **A4** ubuntu CI + **✅ G3
> idmap-frags gate** (`dev/audit_idmap_frags.py`+test, 7 pins; **PASS on real catholic-study eink** — 366 pieces,
> 57k frag+45k noteref+151 ncx resolve, 100,813 unique ids, 0 dup/orphan/dead). **AUTONOMOUS round-14 REMEDIATION
> (user: monitors on, fix everything, Mac helping) — WIN survivors + the G5-finding ALL FIXED + verified (uncommitted,
> pending byte-proof):** **✅ G5 gate** `dev/audit_glossary_contract.py` committed (`ad0eb405`) → surfaced **27 over-cap
> glossary pieces**; root-caused (post-split `rewrite_links` bare-href inflation, NOT the splitter — str==from-file both
> clean) → **G5-FIX** = per-atom `_atom_rewrite_headroom` reservation in the glossary budgeting (eink-only) → G5 re-run
> on the post-fix build = **0 over-cap** (216 pieces, max 399,149, atoms conserved). **✅ #6 (HIGH) est 10:2** —
> `_merge_mid_verse_breaks` displacement guard (`_mv_displacement_would_corrupt` via the WEB base text: skip merge when
> lead is a PREFIX of the current verse's WEB text & NOT a SUFFIX of the prior's) → built catholic-study eink:
> **est 10:1 ends "…sea." (no "Aren't"), est 10:2 starts "Aren't…"**; `test_mid_verse_merge` 10 + `test_file_split` 58.
> **✅ #4 S1 attribution** — gate the dict-* leaf/body strips on `cascade = s2_group or eink_backmatter` (the exact
> re-surface condition @4039) → 5 TDD pins; dict source survives under S1-on/S2-off. **⏳ G1 golden BYTE-PROOF running**
> (rebuild 9 KJV cells post-fix → confirm == golden; all 3 fixes are eink-gated/dormant so expect PASS). **NEXT:** on
> byte-proof PASS → commit (#6+#4+G5-fix+tests) + push → **G4 badge-conservation** (sidecar instrument + auditor) + wire
> G3/G4/G5 → ALL_CHECKS (G2 eink-leak ≈ subsumed by G1). **▶ Mac:** #3 canonical-extent · cross-OS verify A1+golden ·
> #6 `audit_verse_formatting.py` mirror. ⚠ pre-existing debt: kindle_post UP034@477 + C901@540; 5 old git stashes.
>
> **★ 2026-06-26 (WIN, env root-cause) — THE "FLAGSHIP-EINK OOM SITE" IS LARGELY ENVIRONMENTAL: an AppXSvc COMMIT LEAK.**
> Resuming the WIN pickup, the `catholic-study --target-reader eink` build OOM'd at 402s (swallowed `✗` = empty `{e}` =
> MemoryError, `build_edition.py:8633`). Root cause was NOT a new code site: **`svchost` hosting `AppXSvc` (AppX
> Deployment Service) had leaked ~52.8 GB of COMMIT** (private bytes; WS only 725 MB), leaving **CommitFree ~590 MB of a
> 64 GB limit** while PhysFree was a healthy 6.5 GB. On this box COMMIT (RAM + page file) is the binding constraint, so
> builds MemoryError regardless of free physical RAM — **this is almost certainly the same "OOM @443 MB RSS" the prior
> sessions chased as a code defect.** The leaked host (PID 6408, hosts ONLY AppXSvc) could not be killed from a
> non-elevated OR an elevated PowerShell (`Stop-Process`/`taskkill` → Access denied: SeDebugPrivilege not enabled on a
> SYSTEM-owned protected svchost) → **user rebooting to clear it.** Audit implication: re-confirm A2 + the flagship-eink
> build on a freshly-rebooted box with CommitFree headroom BEFORE attributing any remaining OOM to a code site;
> consider a build-pre-flight commit-headroom check (propagation-lens P-env). **Three WIP items already on disk
> (uncommitted, survive reboot — do NOT recreate):** (1) `scripts/core/zip_repro.py` — the A1 `ocf_member_bytes`
> CRLF→LF helper is ADDED but **INERT/unwired** (nothing calls it yet → byte-safe, no behavior change); (2)
> `tests/test_kjv_golden_hash_gate.py` (G1); (3) `.github/workflows/kjv-golden.yml` (A4). **RESUME after reboot:**
> build catholic-study eink (confirm A2 unblocks 4444 + capture pre-A1 artifact) → wire A1 (`build_epub.py:161` +
> `kindle_post.py:121` through `ocf_member_bytes`) + P1 helper unit test + P2 member-wise before/after → rebuild post-A1
> → `G1 --regen` golden (commit golden + A4 CI together) → A6 G2–G5. NOTE: do the pre-A1 build BEFORE wiring A1.
> Commit the WIP cleanly once commit is freed (the pre-commit mypy timed out under the memory starvation, not a real
> failure). HEAD `788f4b53` synced at this note.
>
> **▶ 2026-06-26 (Windows, autonomous, two-lane) — ROUND-14 BUILD-PIPELINE DEEP-AUDIT, plan USER-APPROVED.**
> Program doc: `dev/audit/build-pipeline-deep-audit-program-2026-06-25.md`.
> **WRAP 2026-06-26 (fresh-session prep):** cross-OS final-build AMENDMENT USER-APPROVED (A1 LF chokepoint
> `zip_repro.ocf_member_bytes` into `build_epub:161` + `kindle_post:121` = OS-independent EPUB bytes · A3/G1 one
> platform-independent KJV golden verified Win+Mac+Linux · A4 ubuntu CI · A5 build-feasibility dim; user: ubuntu-CI
> for Linux + true byte-identity via the newline fix). **A2 DONE.** Sequencing A2(done)->A1->G1 regen->A3/A4.
> **NEXT-SESSION WIN pickup:** build `catholic-study --target-reader eink --force` (confirm A2 unblocks the 4444
> site + capture the pre-A1 artifact) -> A1 + byte-safety P1/P2 -> `G1 --regen` golden -> A4 CI -> A6 G2-G5. **Mac:**
> fold A5 into the program doc + cross-OS verify + the all-edition rebuild byte-proof of the WS1 re-split; continue
> Phase 0 (C2-C10) and Phase 1 `deep-audit.js LANE=mac`. See LANE_HANDOFF (WIN->Mac, this turn).
> Mac running Phase 0 baseline ∥ Phase 1
> `deep-audit.js LANE=mac ROUND=14`; WIN owns the OOM site + 5 gates (G1 KJV golden-hash ★ · G3 idmap-frags ·
> G4 badge-conservation · G5 glossary-contract) + build-path fixes. **This WIN session (3 commits, pushed):**
> (1) **OOM #1 deeper fix COMMITTED `aed89170`** — `_iter_study_glossary_pieces_from_file` + `_stream_glossary_pieces_from_bytes`
> (glossary held ~1× as bytes) + `_group_glossary_atoms` shared + `apply_file_split` streams pieces + `badge_stats.pop`;
> **byte-identical `test_file_split` 58/58** (4 new `TestStreamGlossaryFromFile` pins). (2) **★A2 OOM site FIXED (single-pass _apply_splices, guard 12/12 + 251 regression green, byte-identical) =
> `apply_badge_markers:4444`** (`text=text[:start]+repl+text[end:]` per-splice rebuild; MemoryError @443 MB RSS = Windows
> commit-pressure, BEFORE the glossary split) — the real WIN-box build-killer; fix = single-pass `"".join`; **first round-14
> build-path item; blocks the full flagship-eink build + C1 on Windows.** (3) **WS1 158-verse re-split APPLIED+COMMITTED
> `aacb6dd6`** — 155 groups/38 files, 0 flagged; **38/38 pure-relocation proof vs HEAD** + `check_nested_anchors` 0 +
> `test_nested_anchors` 10/10; Mac to run the all-edition rebuild byte-proof. (4) **Kilo removed `733c55c6`.**
> **NEXT (WIN):** plan-mode review of Mac's audit program (Win/Linux/Mac final-build coverage) + plan the two-lane monitored
> run → fix `apply_badge_markers:4444` → build G1–G5. **★ Older Kobo-deep-audit history (WS1/WS2/WS3, OOM, page-breaks)
> below is DONE/superseded — round-14 verifies, doesn't re-litigate.**
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
