# Round-16 — UNIFIED Remediation Plan (both lanes synthesized)

> **Status: FINDINGS-ONLY. This is the plan, not the work.** No code is modified by this synthesis.
> Synthesizes `round16-engine-win-plan.md` (26 survivors) + `round16-engine-mac.md` (20 survivors) +
> the build-free gates (F1/F2) + the WIN full-catalog build-inspect harness, after cross-lane `keyOf` dedup.
> Safest/most-foundational first; every build-path item carries an explicit byte-stability obligation
> (KJV golden G1 stays 9/9; glossary parity G5). `truth_owner = windows`. Marathon core OFF-LIMITS.
> Round-14 build-source dims + round-15 D1–D9 = `DEFERRED_BY_DESIGN` (do not re-litigate).
> Companion ledger: `dev/audit/round16-remediation.md`. Program: `dev/audit/round-16-build-program-bulletproofing-2026-06-27.md`.
>
> **★ USER APPROVED REMEDIATION (2026-06-28).** Execute safest-first Phase A→I, TDD, byte-proof. **Two design decisions made:**
> **F1 `computer`** → make it an **explicit alias of `everywhere`** (keep the UI card; no orphan asset; byte-neutral).
> **F2 `verse_marker_glyph`** → **RETIRE** the control + all legs + the catholic-study `¶` value (byte-safe since unread).

## Provenance & method

- **engine-win:** 36 deduped → **26 survivors** (3 medium · 23 low), 10 refuted. 0 UNVERIFIED.
- **engine-mac:** 32 deduped → **20 survivors** (2 medium · 18 low), 12 refuted. 0 UNVERIFIED. 9 touch WIN-owned `build_edition.py`/`epub_working/`.
- **build-free gates (WIN, deterministic):** F1 `computer` orphan target (gate FAIL); F2 `verse_marker_glyph` orphan field (gate FAIL).
- **WIN build-inspect harness — ✅ COMPLETE: all 22 catalog assets built + gate-scanned CLEAN** (4 editions × {everywhere, kindle, apple-tablet, eink-epub, kobo-kepub} + 2 standalones). Flagship ethiopian-tewahedo eink built **exit 0, no OOM** (~26 min) — epubcheck 0/0/0/0, G3 idmap (88,541 xrefs, 0 dead), G4 badge, D8 order, **G5 glossary PASS at scale** (max_inner_cp 399,171 < 400,000), verify_kr2 GREEN; 22 orphan-aside WARN corroborates mac#17. Standalones epubcheck 0/0/0/0. Kepubs verify_kr2 GREEN (idmap/glossary N/A — kepub-aware; epubcheck timeout = soft). **No product defect surfaced by the harness; every round-16 finding is source-level.** This closes completeness-seed #1 (the marker-logic 0/2 + html-integrity 1/4 artifact dims now have their built-artifact detector).
- **MAC cross-OS verify ✅:** G1 9/9 byte-identical Win↔Mac · G3/G4/G5/G6 + `audit_output_hygiene` PASS on macOS catholic-study eink · `test_round16_source_gates` 5/5.

**Cross-lane dedup (count once):**
| unified | win | mac | note |
|---|---|---|---|
| `verse_marker_glyph` orphan (F2) | #17, #21 | #18 | fully-wired option, no build read |
| `computer` orphan target (F1) | #12, #16, #20 + gate | (refuted by mac panel as benign-alias) | WIN gate is deterministic → keep as **low**, alias fix |
| AppImage placeholder icon | #23 | #20 | branded PNG exists in `assets/icons/` |
| 4 /customize fields don't display saved value | #19 | #19 | `api_customize_data` loader gap |
| glossary str-splitter ~3× + whole-doc fallback OOM | #2, #10 | #9, #12 | one work item; mac#10/#11 are sibling RAM hazards (kept separate) |
| patristic lint omission | — | #7, #8 | mac-internal dup → one item |

**Unified survivor count after dedup ≈ 38** distinct work items (5 medium + ~33 low). **0 high/critical, 0 optimization.** Codebase health: **good** — no live data-loss or shipped-output defect; 9 KJV byte-stable; the 22-asset built catalog is clean. Most survivors are latent-until-future-data, audit-script gaps, orphan UI options, RAM-ceiling hazards on the 16 GB box, or OS-packaging nits.

---

## ★ The 5 priority items (all MEDIUM)

| # | item | owner | dim | byte-path |
|---|------|-------|-----|-----------|
| P1 | **Kindle desktop /customize build ships the retired E999-failing variant** — `build_one` never applies `make_kindle_safe` (only `build_format_matrix._apply_kindle_post` does). A /customize user who picks 📬 Kindle + rebuilds gets a non-deliverable artifact (display:none >10K → Amazon E999/E3013). **Refines WIN seed#2** (matrix path is correct; the direct `build_one` path is not). | WIN | cross-product | gated on `is_kindle_target` ⇒ 9 KJV + everywhere byte-identical (prove G1) |
| P2 | **eink study-glossary return link teleports to chapter start** for the 13 Strategy-B books that DO carry v-anchors (psa/job/1ki/2ki/1ch/2ch/neh/ezr/jdt/tob/est/man/1es). Gate on actual per-chapter v-anchor presence, not `strategy=='B'`. turn-135 regression; only `jub` (anchor-less) was tested. | WIN | marker-logic-xreader | eink-only; 9 KJV non-eink ⇒ byte-identical (prove G1) + fresh ethiopian eink RSC-012/orphan gate |
| P3 | **config.py reads glyph YAML with platform-default encoding** → cp1252 `UnicodeDecodeError` on Windows w/o `PYTHONUTF8` (real trigger: `❑`/`❖` U+2751/2756 in `categories.yaml:88,94`). 4 loaders (`config.py:280,292,316,341`). | — | correctness | decode-identical to PYTHONUTF8 path ⇒ KJV bytes unchanged |
| P4 | **glossary str-splitter holds ~3× the ~480 MB body + the byte-streamer's whole-document fallback re-opens the flagship-eink OOM** (`build_edition.py:5191-5236`, fallback `:5393`). win#2/#10 ≈ mac#9/#12. _(Latent: the live flagship path is the proven byte-streamer — this round's fresh flagship build proved exit-0/G5-PASS; the fallback is production-dead today.)_ | WIN | builder-robustness | additive on a production-dead fallback ⇒ byte-identical (prove G5 + a fresh catholic eink build) |
| P5 | **the round-16 `audit_output_hygiene` family-C (display-redundancy) gate is a dead check** — scans `note-category` (never emitted; build writes `vn-cat-head`) + omits the body/byline checks its docstring promises. Fix the gate before relying on the dim. | WIN | display-redundancy (gate self-fix) | audit-script only, no byte impact |

---

## Phased plan (safest-first)

### Phase A — Encoding hardening + commit-time lint completeness (foundational, byte-neutral)
- **[P3, medium] config.py 4 loaders** → add `encoding="utf-8"` (`config.py:280,292,316,341`). Keep the existing `-X utf8`/CI `PYTHONUTF8=1` scaffolding. Back the whole class with a **commit-time `lint_rules` check** (flag `read_text(`/`write_text(`/`open(` over `content/**`, `*.yaml`, notes stores lacking `encoding=`) — the defect recurs every new tool/ingest. **Guard:** pytest loading each loader under forced cp1252.
- **[low] dev/authoring tools encoding=** — `add_note.py:149,203`; `add_kind.py:60,79,85,95`; `bulk_inject.py:99,136,181,215,280,298`; `scaffold_console.py:280,344,368,377,384,389`; `+ coverage.py:162`. Add `encoding="utf-8"` + `newline=""` on LF writes; route `add_kind.py` kinds.yaml/stylesheet.css writes through `notes_io.atomic_write` + `ensure_backup`.
- **[low] bookcode_canonical lint omits the 6th store** (patristic_commentaries.json) — `lint_rules.py:2276-2282` (folds mac#7≡#8). Replace the hardcoded `json_specs` with a **glob** (`(REPO/"content/sources").glob("*_commentaries.json")`) so future stores auto-screen; fix stale "5 stores" wording at `lint_rules.py:2269` + `sources_commentary.py:305`. ★BUGCLUSTER.
- **[low] no_reviewer_scaffolding screens body only** — `lint_rules.py:2586`. Also screen label (`elts[6]`) + attribution (`elts[8]`); NOT title (`elts[5]`, never rendered).

### Phase B — Security boundaries (additive, no build path, byte-stable)
- **[low] note-editor render boundary** loads stored bodies via `innerHTML` unsanitized (only SAVE is gated) — `templates/index.py:315` (+ excerpt `:210/:218`); read at `web_notes.py:83`. Sanitize on the API read path OR run `normalizeBody()` before assigning; replace regex tag-strip with `textContent`. Bulk-ingest bodies (Nave's/Easton's/Torrey/commentary) bypass the save gate.
- **[low] SSRF allowlist bypassed by redirects** — `core/http.py:167-172` (get) + `:232-240` (put). Per-call `_AllowlistRedirectHandler` re-running `_check_allowlist(newurl)`; `urlopen=None` → `_validating_opener(allowlist)`. Do NOT default to no-follow (archive.org/ebible.org legitimately 30x).
- **[low] `_send_file` magic-byte defeated by extension fallback** — `web.py:1345-1355`. Pass empty fallback `_detect_format(data[:32], "")`; keep the 415 cross-checks. Local defense-in-depth.
- **[low, optional D-i-D] sanitize_html/sandbox_ai_html emit unbalanced/nested-`<a>`** — `html_sanitize.py:350-413` + `html_sandbox.py:155-183`. Open-tag stack (refuse 2nd `<a>`, close-only-if-open, close-at-EOF). Byte-identical on the current corpus (0/91,712 bodies change); base gates already block shipping ⇒ hardening, not a live fix. **⏸ DEFERRED (2026-06-28):** the one explicitly-OPTIONAL item — not a live defect (corpus clean + `test_all_master_html_is_wellformed_xml`/`check_nested_anchors`/epubcheck already block any malformed/nested-`<a>` body from shipping), and the new api_notes read-sanitize's security property [stripping active content] does not depend on it. Revisit if a future corpus carries raw `<` in note bodies.

### Phase C — Silent-correctness / stat / cache / concurrency (additive, byte-stable)
- **[low] dashboard_stats use-after-close race** — `corpus_index.py:1487-1514`. Hold `_read_cursor()` across both queries (1 of 11 sites escapes).
- **[low] translations.get_chapter sorts raw verse** → TypeError on `own` stores mixing int + lettered keys — `translations.py:241`. `key=verse_sort_key`. Closes the round-11 gap-2 "fix the class" miss. Latent until lettered Patrologia/Psalter data.
- **[low] at-scale stat over-counts written candidates** (ignores `append_candidates` dedup) — WHOLE class, 7 sites (`at_scale_base.py:307-311,452-458` + xref/naves/torrey/ethiopian/kenyon). `append_candidates → int`; special-case `prospect.py:161-163` to keep `Path|None`. **⏸ DEFERRED (2026-06-28, verifier-sanctioned "acceptable lighter alternative"):** the over-count is a progress-LOG inaccuracy on idempotent re-runs in OFFLINE-only ingest tooling — no build/byte/user-facing impact. Fixing it flips `append_candidates`' `Path|None→int` contract across ~11 wrappers (each annotated `-> Path|None`) + their consumers + the `prospect.py` Path dependency (`.relative_to`) + 2 contract tests (`test_mint10_phase4.py:96/111`) — a disproportionate regression surface for a cosmetic stat. **Recipe preserved (do as a focused unit):** `append_candidates` returns `len(new_dicts)` on write / `0` on the two empty branches; write-consumers → `n = append_candidates(...); if n: files_written += 1; candidates_written += n` (KEEP dry-run `len(...)` branches); `prospect.write_queue` reconstructs the path locally to keep `Path|None`; flip the 6 wrapper annotations to `-> int`.
- **[low] edition_stats cache key omits 3 popup-cap fields** → stale popup-language set baked into the About page after a runtime cap edit — `edition_stats.py:50-79`. Add `target_reader`/`max_popup_languages`/`popup_languages_capped` to `_edition_signature`; D-i-D `edition_stats.cache_clear()` in edition-edit paths. KJV cap fields unset ⇒ clean build byte-identical (confirm).

### Phase D — Book-code canonical normalization (★BUGCLUSTER, additive)
- **[low] run_kenyon_at_scale `--books` not normalized** — `:116-117,132`. `_normalize_book_code` the filter set (lone un-normalized at-scale driver).
- **[low] add_note routes the notes-file write through the raw `--book` alias** — `:301,322,346`. `args.book = book["code"]` after validation; sibling fix in `new_note.py`.

### Phase E — Audit/gate self-corrections (audit-script only, no byte impact)
- **[P5, medium] audit_output_hygiene family-C dead check** — `:108,200-209` (docstring 26-27). Retarget regex to `vn-cat-head` (strip inner `vn-cat-sym`); implement the duplicate-`vn-source-byline` + duplicated-`vn-item` body checks (depth-aware); keep WARN-grade; add a family-C `_selftest` case.
- **[low] audit_output_hygiene `_unescape` misses `&#x27;`** — `:115-116,78,329-357`. Use `html.unescape`; add an `html.escape("<class 'dict'>")` selftest case.
- **[low] audit_cross_product checks only /customize, not the wizard cards** — `:49-74`. Add `_wizard_reader_options()`; FAIL-assert the two surfaces' target sets are identical (Mac corroborates a parallel `target_reader` entry point).
- **[harness, low — cross-OS] `test_round14_build_gates.py:58` runs gates via subprocess w/o `PYTHONPATH`/`cwd`** → `audit_canonical_order` `ModuleNotFoundError('scripts')` on clean macOS. Pass `env`/`cwd` (same fix already in the round-16 harness); `test_round16_build_gates.py` should adopt it.

### Phase F — Builder-robustness / OOM hardening (build path, byte-identical for in-spec inputs)
- **[P4, medium] glossary str-splitter ~3× + whole-doc fallback OOM** — `:5191-5236`, fallback `:5393` (folds win#2/#10 ≈ mac#9/#12). **Do NOT** offset-rewrite the D5 reference impl (would force re-proving str==from-file 690/690 + catholic eink byte-stability). Instead: in `_iter_study_glossary_pieces_from_file`, route `≤64 MB` to the str path and on `_GlossaryStructureError` for a `>64 MB` file **raise** a clear RuntimeError pointing at the byte-twin patterns (`:5259-5262`) instead of decoding ~480 MB. Belt-and-suspenders (byte-neutral): rebind `parts=None`/`sec_parts=None` after `:5213`/`:5218` so the existing `del body`/`del inner` actually free. **G5 + a fresh catholic eink build.**
- **[low] enrich_nav_chapters reads the ~480 MB monolith whole** (no stem skip) → OOM when `reader_native_toc_chapters` on eink flagship — `:6646-6647`. `if p.stem == EINK_STUDY_BACKMATTER_STEM: continue` (mirrors the 2 sibling passes). Byte-identical; latent (option default-off).
- **[low] --all ThreadPool worker count target-blind (fixed 5)** → concurrent in-process eink builds co-reside the monolith → OOM — `:8716`. `workers = 1 if args.target_reader=="eink" else min(len(targets),5)`. Drop psutil (undeclared dep). Update the stale round-7 "CONFIRMED-OPTIMAL" comment.

### Phase G — Options surfacing & wiring (loader/preview legs; mostly byte-neutral)
- **[low] Change-impact Preview duplicate EDITABLE allow-list drifted** (missing time_filter_ceiling, reader_eink_verse_lines, …) → savable edits mislabeled "silently ignored" — `api/editions.py:695-756,786`. Derive `EDITABLE` from the save registry.
- **[low] 4 /customize fields never display saved value** (win#19 = mac#19) — `web_editions.py:393-499`. Add `chapter_number_format`/`chapter_number_decoration`/`note_popup_split_cap`/`note_popup_split_byte_cap` to `api_customize_data`; surface the 2 caps **RAW** (`e.get` — preserve None=unset vs int=pinned).
- **[low] dead eink-unsafe badge guard** — `dot` `marker_badge_style` not rejected for eink — `:2278`. Single-resolver: coerce eink-unsafe → `"chip"` in `resolve_marker_badge_style` when target resolves eink. Byte-neutral (no edition stores `dot`).

### Phase H — Behavior-changing build path (byte-stability obligations)
- **[P1, medium] Kindle desktop build = E999 variant** — `build_one` tail (frozen in-process + dev subprocess branches), gated on `is_kindle_target`: run `make_kindle_safe` + `verify_kindle_safe` (mirror `build_format_matrix._apply_kindle_post`); `raise` on failures. Do NOT delete the UI option (bring-solutions). **Guard:** tiny `target_reader=kindle` build through build_one asserts `verify_kindle_safe == []`. Gated ⇒ 9 KJV + everywhere byte-identical (prove G1).
- **[P2, medium] eink return-link teleport** — `_study_verse_return_link:3749` add `verse_anchored: bool|None=None` (legacy strategy inference default), thread from `_emit_backmatter_glossary_inner:3799` (line 3808) + the call site 4336 using the per-chapter `f'id="v-{code}-{ch}-' in text` signal at 4153. Do NOT hardcode an anchor-less list (aes/2es carry anchors). **Guard:** keep jub/gen; add psa-119-160 verse + a `verse_anchored=False` ch-anchor case. eink-only ⇒ 9 KJV byte-identical (prove) + fresh ethiopian eink RSC-012.
- **[low] numbers+eink note-sym tofu** — eink glyph subst runs only in the badge path — `:4204-4205` (gated by marker_style at 8429). Eink-gated repair pass over `class="note-sym"`, GATED `eink and marker_style != "badge"` (every shipped edition is badge ⇒ no-op). Prove golden.
- **[low] eink backmatter glossary repeats header/byline/return across split-group footnotes (no part indicator)** — `:3857-3877`. _(The 22 orphan-aside WARN in this round's flagship-eink scan is exactly this — the `vnotes-*-c2` continuations whose badge points only at `-c1`.)_ Implement ONLY the `(c_idx/n_groups)` `vn-part` span (mirror popup-unit at 4394); do NOT blanket-suppress byline (cN may lead a different source) or the per-aside back-link (each `<aside>` is its own target). Single-group byte-identical. Flagship eink only.
- **[low] apply_eink_verse_line_breaks ignores verse-p-flush** — leaves an empty `<p>` + drops flush at every chapter/stanza opener (re-triggers K-R15 stray-break when the opt-in flag is on) — `:3965,3976-3999`. Broaden the start-of-para test to match `verse-p-flush`. Byte-identical for 9 KJV + shipped Ethiopian (flag off).
- **[low] S2 cascade body-boilerplate de-dup gated on the wrong flag** — `note_attribution_dedup` instead of `note_group_by_category` → category text prints twice in `{S1-off,S2-on}` — `:4226-4243`. Hoist out of `if s1_dedup:`; gate on `s2_group`. Byte-identical for all 4 shipped (S1-on) + S2-off (helper no-ops).
- **[low] `TODO_CERTIFIER_NAME` placeholder shipped in every edition's OPF (a11y:certifiedBy)** — `:1833`. Drop the optional meta (dcterms:conformsTo alone is valid) or set a fixed project name. Extend the hygiene scanner to `*.opf` metadata. **REAL byte obligation:** changes OPF bytes for all 9 KJV cells (certifiedBy not normalized out of `_content_digest`) → **golden re-baseline** (`test_kjv_golden_hash_gate.py --regen` + byte-stability gate), same re-bake+re-stamp as D3 Vulgate.
- **[low] verse_marker_glyph orphan (F2)** — fully-wired option, no build read; catholic-study ships `¶` with zero effect. **Boggy decision:** (a) WIRE it into the verse-marker emitter, gated so empty/unset reproduces today's bytes (note: catholic-study IS in G1 + is the only edition setting `¶` → wiring changes catholic-study bytes → deliberate re-stamp of its 3 golden hashes); or (b) RETIRE the control + all legs (byte-safe since unread).
- **[low] computer orphan (F1)** — valid `TARGET_READERS` + 2 UI surfaces, no FORMAT_MATRIX row → silent everywhere-alias (differs only by OPF stamp). **Boggy decision:** make `computer` an explicit alias of `everywhere` (`TARGET_READER_ALIASES`, folded into `resolve_target_reader` + `apply_target_override` + asset-name token) so a `--target-reader computer` build is named/located as everywhere; only build a distinct row if Boggy wants desktop tuning. Byte-neutral for the 9 KJV (none uses `computer`).

### Phase I — OS-binary parity (packaging scripts only; zero KJV byte impact)
- **[low] AppImage unbranded placeholder icon** (win#23 = mac#20) — `build_appimage.sh:78-97`. Point at `assets/icons/icon_256.png` (fall through to placeholder only if absent).
- **[low] Windows desktop build installs UNPINNED PyInstaller** — `build_desktop.cmd:19-24`. `-r dev\requirements-desktop.txt` (pins `pyinstaller==6.20.0` + restores `pywebview==6.2.1`).
- **[low] build_appimage.sh unreachable code + contradictory message** — `:42-50`. Remove the unreachable `chmod` + the misleading "Downloading…" echo.
- **[low] frozen Windows .exe carries no version resource** (macOS `.app` embeds CFBundleVersion) — `launcher.spec:217-237`. Build a `VSVersionInfo`, parse VERSION → 4-int tuple, guard on win32.

---

## Constraints carried (both lanes agree)
- **Marathon core OFF-LIMITS:** `build_standalone.py`, `core/manuscript_*.py`, `po_vision_store.py`, `content/manuscript/**`, `content/translations/sources/patrologia/**`, `GAPS/`. No item above touches these.
- **9 KJV byte-stable:** every build-path fix is gated/additive ⇒ byte-identical when the new behavior is unset — EXCEPT `TODO_CERTIFIER_NAME` (Phase H), the one **deliberate** byte change (golden re-stamp), and the `verse_marker_glyph` WIRE option for catholic-study (also a deliberate re-stamp).
- **Additive schema only;** no field removals except the explicit `verse_marker_glyph` retire path (byte-safe, unread).
- **Atomic writes** via `notes_io.atomic_write`/`ensure_backup`.
- **No paid API;** drop psutil + Voyage alternatives; keep lint import-light (glob, not corpus-class imports).
- **Prefer commit-time lint** for ingest-recurring invariants (Phase A patristic + reviewer-scaffold).
- **Bandwidth-first save cadence (RULES §4):** each fix = LOCAL COMMIT; full 5-leg sync only at a milestone; `ruff format` generated files before commit.
- **0 optimization recommendations survived** (both lanes). zip level 9, web.py/build_edition.py size, Python-tuple data model, marathon core = all confirmed-optimal / off-limits.

## Coverage matrix — 8 user-asks × 11 dims (round-16 done-definition)
"Every way we offer the same Bibles, audited end-to-end." Asks: (1) full output cross-product · (2) options-completeness · (3) display-redundancy · (4) HTML-integrity · (5) per-reader marker-logic · (6) builder-robustness · (7) OS-binary parity · (8) cross-OS determinism.
- **(1) cross-product** — F1 computer orphan + P1 kindle build_one; the 22-asset harness covers the built cross-product. ✅ (gap: kepub colour fan-out — seed.)
- **(2) options-completeness** — 5-leg wiring audited; F2 + 4-fields-loader + dead-badge-guard + Preview-drift found. ✅ (gap: build-time enum validation — seed.)
- **(3) display-redundancy** — S2 cascade gating + eink split-group repetition (corroborated by the 22 orphan-asides) + the P5 dead gate. ✅
- **(4) HTML-integrity** — sanitizer balancing + reviewer-scaffold field gap + TODO_CERTIFIER OPF leak; harness output-hygiene clean on all 22. ✅
- **(5) marker-logic-xreader** — P2 return-link teleport + numbers+eink tofu; harness idmap/badge clean (0 orphan markers across the catalog). ✅ (closes engine 0/2 source-only.)
- **(6) builder-robustness** — P4 glossary + enrich_nav + ThreadPool; **flagship-eink OOM proven resolved this round.** ✅
- **(7) os-binary-parity** — AppImage icon + unpinned PyInstaller + version resource + unreachable code (static; binaries not built). ✅ (gap: cover-gen font determinism — seed.)
- **(8) cross-OS determinism** — G1 9/9 byte-identical Win↔Mac; eink only gate-verified, not byte-verified. ⚠ partial (the known catholic-study eink Win 55,774 vs Mac 45,057 xref divergence — seed).

## Completeness-critic — next-round seeds (WIN 7 + MAC 8; NOT this round)
Kepub colour-variant fan-out (only 1 colour scanned) · no build-time enum validation of `editions.yaml` · the website **release-catalog** (`gen_release_catalog`) as a 3rd offering surface · eink/kepub **cross-OS determinism** (only 9 KJV cells byte-gated; Win/Mac eink xref count already diverges) · per-book/chapter **override→marker** chain · kindle_post output shape (post-strip inline-aside redundancy) · the whole **6-store enumeration class** (mac: `detectors.ALL_DETECTORS` drops RabbinicCommentaryDetector → rabbinic corpus never auto-detected) · client-side innerHTML across the 27 templates · matter_pages `render_*` interpolation + cross-edition topic-ref validity · cover-gen cross-OS font determinism (`C:\Windows\Fonts` hardcodes) · editions API validator enum completeness · whitespace-pagebreak re-lens onto matter_pages empty-page emission · per-edition verse-COUNT / anchor-existence invariant (vs reading-plan/topical refs).

## STOP
**FINDINGS-ONLY. This is the plan; no fix applied this round.** On approval, execute safest-first (Phase A→I), TDD, byte-proof every build-path touch (G1 9/9 + G5), commit-per-fix, push at coherent milestones. The two Boggy decisions (F1 `computer` alias-vs-row; F2 `verse_marker_glyph` wire-vs-retire) are flagged for an explicit call before their Phase-H items land.
