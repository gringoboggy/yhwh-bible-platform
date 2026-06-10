# Round-7 P3 verify-first triage — verdicts (2026-06-10, win)

**Run:** workflow `wf_81c9dea3-f98` (11 read-only clusters, ~863k tok, ~37 min) over the WIN-share survivors of `2026-06-10-round7-findings.md`. **46 items: 28 VALID · 11 VALID_FIX_ADJUST · 2 ALREADY_FIXED · 5 PARTIAL.** Mac Phase-3 items independently re-verified DONE (`73edc815`) and struck. Full evidence: the workflow output (session-local); the load-bearing corrections are inlined below.

## Verdict table (fix-relevant deltas only — VALID items execute as planned)

| Item | Verdict | Load-bearing delta vs the synth plan |
|---|---|---|
| 1.1 lru_cache HIGH | VALID | **DROP the cache from `_kind_default_labels` (bd:2027), do NOT whitelist** — `customize.py:124` invalidates kinds in-process via `load_kinds.cache_clear()`, which never reaches the private cache (stale-label hazard is real; no hot loop — one call per `apply_badge_markers`). Whitelist `_topic_vocab` (bd:2188) only. |
| 1.2 ethiopian extent guard | FIX_ADJUST | Also add the driver to `KJV_COORD_DRIVERS` in `tests/test_mint11_phase3.py:79-84` or the regression test never covers it. |
| 1.3 bookcode JSON lint | VALID | 135 legacy codes live (eth 121 / prot 5 / cath 5 / rab 2 / ref 2). Loader drifted to `scripts/core/sources_commentary.py:302/316` (raw store, key-only normalize). |
| 1.4 MEMORY.md byte budget | VALID | Fits beside `MEMORY_INDEX_LINE_BUDGET` (`memory_hygiene.py:73`); severity `info`. |
| 2.1 frozen content root HIGH | FIX_ADJUST | Guard goes in **`_content_root_cached()`** (after env check), returning **`user_data_root()/"content"`** (NOT bare — the migrator's dst is `/content`; also reconcile the bare fallback at `paths.py:169`). web_helpers gets a `_notes_dir()` shim (translations.py pattern), constant kept as back-compat re-export. |
| 2.2 preview paths | VALID | Add `paths.themes_dir()` helper (class-consistent) + use `paths.notes_dir()`. |
| O3 translations resolver | VALID | 4 edit sites: `:55, :154, :162+165, :214`. Behavior-level pin + `translations.clear_cache()` in teardown. |
| 3.1 gen_checksums HIGH | VALID | Suffix-tuple match ⇒ `.epub` also covers `.kepub.epub` free. Test file exists — extend it. |
| 3.5 save.ps1 | VALID | As planned. |
| 3.x Mac items | ALREADY_FIXED | Verified live (`save_mac.sh:42/58-63`, notary ×3, NOTARIZATION_STATUS v0.1.0). Struck. |
| 4.5 dead workflows | VALID | Also touch the `deep-audit.js:306` comment + memory note. |
| 4.6 runbook banner | VALID | Use the PLAN's banner variant verbatim; runbook also missing from INDEX.md (fold into 8.10 regen). |
| 8.2 stale hook MED | FIX_ADJUST | **TWO-WAY drift:** the installed copy carries a LANE SYNC RADAR block (lane_ping --quiet) never committed to `dev/cc-hooks/`. Backport it FIRST, commit, THEN run `install_cc_hooks.ps1` — a plain reinstall would delete the radar. |
| 8.3 pip wildcard MED | VALID | Delete `settings.local.json:135`; keep the exact-match ruff line 113 + the manifest-scoped line 184. |
| 5.1 topic span cap | VALID | `bd:2213`; eth-only output change (note_topic_dedup only on eth). |
| 5.3 vnote-empty/¶ regex | FIX_ADJUST | vnote-empty SHOULD get the ¶ (346 base instances; renders in the preview like any vnote; the "leave untouched" critic lens had no technical basis). 2,970 `vnote-text">¶` sites currently double-mark. ¶-leading text = recovered-base KJV popup text (not WEB). All-edition output change. |
| 5.4 empty verse-refs husk | VALID | 58 live `<section class="verse-refs-section"` opens; the husk carries ~52 newlines ⇒ regex needs `\s*`. All-edition output change. |
| 5.5 unsorted globs | PARTIAL | **8 unsorted loops, not 2** (4296, 4323, 4332, 4389, 4722, 5018, 5109, 5224); none affect bytes (order-independent passes) — wrap all 8, prove byte-identical. |
| O1 filter_html | PARTIAL | **Latent only** — `disabled_html_ref_ids` is EMPTY for all 11 stock editions (the kind path is already pre-built). Implement as zero-risk hardening with the exact byte-identity semantics recorded in the workflow output (generic capture + set-lookup, preserve ref-→note- replace direction). |
| 5.2 xref teleport MED | PARTIAL | **92 live instances, not 88** — 001=3 (note-comm/note-word!) + 050=2 + 058=40 + 059=47; all resolve in-file (defect = hidden-target teleport only). Retarget detectors `:401/:746` → `#v-…`; add V_HREF_RE pass to fix_xref_targets; repair all 92 in the base; extend verify_kr2 gate 2 to non-noteref `#vnote-` body links. |
| 5.11 Torrey escape | FIX_ADJUST | Live screen name = `_xhtml_bad` (eastons:149). Escape BOTH detectors (`:528` Torrey + `:474` Nave — latent twin). **Lockstep-escape the 104 raw-`&` store bodies** (61 Herbs + 43 others) — base already holds `&amp;`, so store converges to base, zero base change. |
| 5.12 reingest doc | VALID | Header comment only. |
| 5.7 tsk._data | VALID | `_raw` never existed (`sources_lexicon.py:216` = `_data`); singleton-cached. |
| 5.8 extent-ok dedup | FIX_ADJUST | Shared home = **`scripts/core/at_scale_base.py`** (dependency-free LEAF — use a thin wrapper with the lazy import inside the body, not a module-top alias). |
| 5.9 estimate_cost | FIX_ADJUST | The proposed test re-point is a tautology — replace the two test methods with a meaningful constant pin instead. |
| 5.10 error-at-200 | PARTIAL | **6 routes** (4 cited + `/api/export/preview` :1602 + `/api/compare` :1679) **+ 2 envelope bypasses** (`/api/sources/cache` :1515; `/api/apihelp` via the always-200 simple table). Fix the class via `_dispatch_table_result` (mint-6 precedent at web.py:659-662). |
| 6.1 flagship gate | FIX_ADJUST | `_EDITIONS[0]` + fix the trailing comment; keep a catholic-study determinism leg too (canon-filter doctrine). |
| 6.2 / 6.3 | VALID | As planned (n2==1 on second run — verifier confirmed). |
| build-cache guard | GREEN | `TestCacheCoverageGuard` 3 passed; `_PIPELINE_SCRIPTS` complete (core/ui deliberately waived). No defect. |
| 7.1–7.6 copy sweep | VALID | 91,733 at exactly 6 sites; website/src+dist already 91,553-clean. BIOS 87-book ×6. roadmap stage-6 stale. index.html:330 "very soon". README :9/:33. Deploy = manual git to `gringoboggy/yhwh-website` (pull the publish copy first — multi-machine caveat). Bonus: COPYRIGHT.md:22 says "71 kinds" (check vs 72); website/README.md:81 still instructs "v1.0.0-beta.1" publishing. |
| 8.1 PLAYBOOK Java | **PARTIAL — REVERSED** | The prescribed "Temurin 26 / needs Java 11+" replacement is FALSE on the live box: PATH java = **Oracle JRE 1.8.0_491** (java8path shim), no Temurin anywhere on disk (likely removed in the 2026-06-10 env curation), and the 5.1.0 jar RAN clean under Java 8. TOOLCHAIN.md:39 + LANE_HANDOFF:168 + memory `reference_epubcheck` now contradict the box. **Resolution: empirical full-EPUB epubcheck run under the live Java decides the doc wording** (do at the P4 gate); keep always-`--jar` everywhere. |
| 8.4 PLAYBOOK counts | FIX_ADJUST | Gate lines take **91,723** (live `validate_taxonomy` source-corpus count), NOT the public 91,553. |
| 8.5 RULES plugins | ALREADY_FIXED | §0.3 rewritten turn-66/67 (named 15-official list + arithmetic correction). |
| 8.6 console inventory | VALID | 21 consoles (the 19 + HOME_HTML + INDEX_HTML); `/` = HOME, `/notes` = editor. |
| 8.7 _design.py "13" | FIX_ADJUST | Fix the line-2 headline only; lines 4-9/35-40 are dated ψ.13 history — annotate, don't falsify. |
| 8.8 REPO_MAP | VALID | 224 test files; also :19 plans/specs 49/26 → 50/28. Right fix = `py dev/trace_repo.py` regen. |
| 8.9 roadmap rows | VALID | mint-3..6 → done; dead-remote note → restored. |
| 8.10 INDEX.md | VALID | 78/50/28; regenerate via the generator (superpowers_coherence lint verifies). |
| O-doc parallelism note | VALID | No note exists at either site; add at `bd:~5456` + MATRIX_MAP. |
| O2 ebible /tmp | FIX_ADJUST | Add `import tempfile` + module `TMP` constant; 3 code sites + 2 doc strings; severity = wrong-location/portability (C:\tmp exists here), repl-crash only on a fresh box. |

## Execution order (this session)

A (no behavior change): 1.1 · 1.2 · 1.4 · 3.1 · 3.5 · 5.7 · 5.8 · 5.9 · 6.1-6.3 · 8.3 · 8.2 · 4.5 · 4.6 · O2 · 1.3 ‖ agent: 5.10 + 5.11/5.12
B (build path, one regen-proof pass): 5.1 · 5.3 · 5.4 · 5.5 · O1 · 5.2 (base repair + gates) · Kindle fix #1 (dc:language → en-US, `bd:1542`)
C: 117-displacement WEB-fixture sweep (design `2026-06-10-verse-boundary-residual-design.md`)
D: Phase-7 copy sweep + card re-render + site rebuild + deploy + repo descriptions
E: truth records (8.1 empirical · 8.4 · 8.6-8.10 · O-doc)
F: mint 3.1/3.3 rotation (compressed; RULES diet 3.2 deferred post-release)
G: P4 round-5 rebuild + all gates + kepub + calibration tap-list
H: v1.0.0 assessment vs the midnight soft target (user directive 2026-06-10)
