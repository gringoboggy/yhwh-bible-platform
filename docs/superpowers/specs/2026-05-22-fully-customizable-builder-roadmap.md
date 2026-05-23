# Master Roadmap — The Fully-Customizable Bible Builder

**Date:** 2026-05-22
**Status:** DRAFT — awaiting user review (then per-phase `writing-plans` → execute)
**Supersedes (for scope):** `docs/superpowers/specs/2026-05-22-themes-and-multitranslation-popups-design.md` (kept for Phase 1–2 detail).
**Origin:** user confirmed the full customization vision + directed "build any tools, check the matrix for upgrades, everything needed; slowest most thought-out plan is fastest; ensure security and professional results."

> Commit discipline: written, not committed — `continue` ≠ `save` (memory `feedback_continue_not_save`). Pacing: single-phase, HITL check-ins (memory `feedback_marathon_pacing`); TDD + verify, no shortcuts (memory `feedback_proper_clean_correct`).

---

## 1. End-state vision

A builder opens `/wizard`, picks a starting edition, and shapes **their** Bible with full control — every choice a *default* they can override (RULES §2: "fully customizable; defaults exist; nothing hard-coded"):

1. **Theme** — pick any house style (or keep the edition default).
2. **Verse popups** — choose which translations appear, **all / none / any mix**, per edition and per book (KJV, Hebrew/WLC, LXX-Greek, Greek-NT, Douay, JPS, Vulgate, Arabic…).
3. **Notes — by type** — toggle each kind/category (symbol) on or off.
4. **Notes — individually** — in a book → chapter → note view that shows **each note's source**, include or exclude **individual** notes for *this* edition, so the builder can (a) check provenance and (b) decide note-by-note.
5. **BUILD** → a themed, validated EPUB containing exactly the chosen notes + popups.

Success = a builder can audit and curate down to the individual note, with sources visible, and trust the output is correct, accessible, and epubcheck-clean.

## 2. Current state (verified this session)

| Capability | State | Evidence |
|---|---|---|
| Theme (default + customizable) | ✅ shipped | Phase 0; `tests/test_themes.py`; 4 distinct stylesheet groups; epubcheck 0/0/0/0 |
| Popup model (3 fixed slots → version registry) | 🔶 in progress | Plan B1 Tasks 1–4 on disk (uncommitted); `scripts/core/popup_versions.py` |
| Popup version select — all/none/mix, per edition + per book | ✅ mechanism / 🔶 enrich | `popup_languages_default` + `_per_book` + `_resolve_popup_languages`; B1 broadens to versions |
| Notes on/off by kind/category/symbol | ✅ shipped | `enabled_categories`/`enabled_kinds`/`disabled_kinds` per edition |
| Per book/chapter review | ✅ shipped | `/build-tracker` (per-book×chapter counts, per-kind, canon coverage) |
| Check a note's source | 🔶 partial | 100% attributed; `/sources` console + attribution audit; **no per-note source line in the book/chapter view yet** |
| **Individual note in/out per edition** | ❌ gap | edition filtering is by **kind** only; no per-edition per-note override |
| Full translation data (he/gr/Greek-NT/Douay/JPS/Vulgate/Arabic) | ❌ gap | only KJV full; others are Genesis-only seeds; no Greek NT |

## 3. Unified architecture

Three cooperating layers, each one responsibility, each independently testable:

- **Version registry** (`scripts/core/popup_versions.py`, B1) — single source of truth: which popup versions exist, how each renders (`content_class`, `lang`, `dir`, `has_label_para`), where its data lives (`translation_id`), whether it is **baked** yet (`bake` flag), and how its coordinate maps onto canonical KJV numbering (`normalize_coord`). Both the bake and the build read it.
- **Note-curation model** (Phase 4) — a per-edition, per-note **override** layer that sits *on top of* kind-level filtering. Stored as a flat, validated edition field (mirrors the `popup_languages_per_book` flat-string pattern so the custom YAML parser handles it). Build-time: after kind-filtering, drop any note whose stable id is in the edition's exclude set (default: empty = no change). Each note already carries provenance; the review UI surfaces it.
- **Review/customize UI** (Phases 3–4) — wizard + `/customize` + `/build-tracker` extensions that expose version selection (per book) and the book→chapter→note source-review-and-toggle, all via the established **pure-function + thin-route-adapter** pattern (RULES §9).

Data flow:
```
PD sources → extract_<id>.py → versification adapter (→ canonical coords) → batch_insert → content/translations/<id>/
generate_verse_popups: per canonical (code,ch,vs): versions = [registry entries with bake=True AND text] → build_vnote_aside → epub_working/
build_edition (per edition): resolve popup-versions (per book) → strip non-selected; resolve note kind-filter THEN per-note exclude set → themed, curated EPUB
```

## 3.5 The non-negotiable safety invariant: matrix == build

`dev/MATRIX_MAP.md` records the project's most expensive past defect (finding #3): "which kinds ship in this edition" was implemented **three times** and drifted, so the matrix UI over-counted vs. the actual EPUB. The fix was ONE canonical resolver (`config.enabled_kind_codes`) that matrix + build + config all delegate to, pinned by `tests/test_enabled_kinds_unified.py`. The matrix (`/build-tracker`, customize counts) and the build (the EPUB) are **two consumers of one config source of truth and must never disagree.**

Therefore every new per-edition control in this roadmap follows the same five-step pattern — this is the "safe way":

1. **One field** on `editions.yaml` (the single source) + a `validate_schemas` entry.
2. **One resolver** both `scripts/core/matrix.py` (counts) and `scripts/build_edition.py` (output) call — never two parallel implementations.
3. **`dev/trace_matrix.py` ref-checks** the field's values (today `popup_languages_*` are `not ref-checked` per the trace table — this roadmap closes that gap for version ids and note ids).
4. **A `matrix == build` invariant test** (extend `test_enabled_kinds_unified.py`).
5. **No-op default** — unset field ⇒ byte-identical build AND unchanged matrix counts.

This is *why* Phase 4 (per-note curation) is sequenced **last**: per-note excludes change the per-chapter **counts** the matrix shows, so it is the most matrix-sensitive change and must extend the unified count/filter resolver (`matrix.compute_matrix` ↔ `build_edition.filter_html`) — not bolt on a second filter the matrix can't see. Doing it last means the version model + UI patterns are settled and the invariant test harness is already in place.

## 4. Phases (re-arranged, value-ordered)

**Phase 0 — Themes.** ✅ DONE.

**Phase 1 — Popup multi-version model (B1).** Plumbing, **zero output change**. Registry + list-based `build_vnote_aside` + generalized harvest + bake assembles registered versions + build-side superset registry + alias-aware resolve. **Two refinements (from execution):**
- `bake: bool` per registry entry — only `kjv`/`wlc`/`lxx-greek` bake now (real coverage already in the base); the seed-only versions stay `bake=False` until Phase 2 lands their *full* data. Keeps Phase 1 byte-identical.
- `POPUP_LANGUAGES` = **superset** (registry versions + preserved legacy slots `latin`/`geez`/`amharic`/`aramaic`/`coptic`/`syriac`); aliases `english→kjv`/`hebrew→wlc`/`greek→lxx-greek`. The bake sources only `bake=True` versions, so `geez`/`amharic` never enter the shared base (preserves the parallel-bible scope, memory `project_parallel_bible_two_standalone_bibles`).

**Phase 2 — Translation acquisition + ingestion.** Per locked PD source (master spec §"Locked PD sources"): `extract_<id>.py` → versification adapter → `batch_insert` to `content/translations/<id>/`, normalized to canonical coords. Flip each version's `bake=True` when full data lands. One sub-phase per source; a blocked source never blocks others. **Highest-value first:** WLC Hebrew → LXX Greek → Greek-NT (the original-language spine), then Douay/JPS/Vulgate/Arabic.

**Phase 3 — Popup-version selection UI.** Surface all/none/any-mix per-book version selection in the wizard "content" card + `/customize`. Mechanism exists (`popup_languages_per_book`); this exposes it with the version registry + per-book matrix in canonical order (RULES §6.1).

**Phase 4 — Note-level curation (closes the gap).** (a) per-edition individual-note exclude set (new validated edition field); (b) build-pipeline pass that drops excluded notes after kind-filtering (default no-op → byte-identical); (c) `/build-tracker` (or a new `/curate`) book→chapter→note view showing each note's **source/attribution**, with include/exclude toggles + a "by symbol/kind" bulk toggle, in canonical order. This is the "check sources + decide note-by-note" capability.

## 5. Tools to build (per the self-upgrading-matrix rule, RULES §1)

- `scripts/core/popup_versions.py` (B1) — version registry + `normalize_coord` seam. ✅ drafted.
- Per-source `scripts/extract_<id>.py` + a shared `scripts/core/versification.py` (per-source remap tables for Psalm titles, Daniel additions, Joel/Malachi splits, 3 John, etc.) — Phase 2.
- `scripts/run_translation_ingest.py` — parse→validate→`batch_insert` driver reused per source (mirrors the Nave's/Easton's pipeline, memory `project_corpus_reference_expansion`).
- A **note stable-id** helper in `scripts/core/` if notes lack a durable per-note id (Phase 4 needs one to reference individual notes across builds) — verify the existing note schema first; only build if missing.
- `/curate` console + its `api_curate_data` / `api_save_note_overrides` (pure-function + thin-adapter) — Phase 4.
- Extend `scripts/build_edition.py`: `_apply_popup_languages_and_translation` (version-aware, B1) + a new `_apply_note_overrides` pass (Phase 4).

## 6. Matrix & validation upgrades ("check the matrix")

- `scripts/validate_schemas.py` — `theme`/`popup_languages_*` already registered ✅; **add** the Phase-4 note-override field (`required=False`, list-of-str). 
- `scripts/trace_matrix.py` — must resolve popup **version ids** (currently language ids) so `trace_matrix` stays "0 unresolved"; add the new translation ids + the note-override references.
- `scripts/render_coverage.py` + `provenance_tiers` — register each new translation track + its PD provenance tier BEFORE shipping it (the lint `provenance_tier_known` fails otherwise).
- `scripts/lint_rules.py` — add pins: (a) every baked version has a registry entry; (b) per-edition popup-version ids resolve; (c) note-override ids reference real notes; (d) `editions×popup-versions` matrix consistency.
- `dev/MATRIX_MAP.md` + `dev/REPO_MAP.md` — document the registry, the note-override layer, the new translation dirs, the `/curate` console (the bootstrap triad is read fresh every session; keep it current).

## 7. Security (professional-grade; RULES §9 patterns)

- **Data files are data, never code:** all translation/note/override loading via `ast.literal_eval` — never `exec` (RULES §7.1). A hostile or corrupt source file must not execute.
- **Ingestion boundary validation:** every external PD source is validated at ingest (coord-in-canonical-extent guard; structural + provenance-tier checks) before `batch_insert`. No unchecked external data reaches the corpus.
- **UI writes (Phase 3–4):** the customize/curate endpoints follow validate-then-write — reject unknown version/note ids, cap payload size, `notes_io.atomic_write` + `ensure_backup`, roll back on failure. Path-bearing fields reuse the `api_save_edition_meta` validator (reject `..`, absolute, hidden, disallowed ext).
- **No injection surface:** note text + sources are escaped at render (the `build_vnote_aside` escaping is a no-op for plain text but blocks any `<`/`&`); the per-book/per-note matrices are server-rendered from validated config, not eval'd.
- **No new external calls** outside `scripts/core/http.py` (lint-enforced). Acquisition uses user-supplied or archive.org PD sources, reviewed before ingest.
- **Determinism + reversibility:** every build pass defaults to a no-op (byte-identical when unset); backups before destructive writes; local-commit-only (no secret/remote exposure).

## 8. Testing strategy

TDD throughout (RULES §8). Per phase: unit (pure functions) + integration (real on-disk build) + the specific guards below.
- **Phase 1:** byte-compat pin (regen with only `bake=True` baked → `git diff epub_working/` == 0); registry/render/harvest/assemble units; build-side back-compat (legacy ids resolve; anglican `latin` preserved).
- **Phase 2:** per-source coverage + sample-verse + **versification-map correctness at named divergence loci** + coord-guard (0 out-of-extent) + an equivalence pin per source.
- **Phase 3:** per-edition resolved version set shows/strips correctly; per-book overrides; standalone bibles unaffected.
- **Phase 4:** override round-trip (save→build→excluded note absent, others present); default no-op = byte-identical; per-note source surfaced; security (reject bad ids, traversal, oversized payload).
- **Always:** epubcheck 0/0/0/0 on the canon-shape reps; `lint_rules` clean; browser spot-check (memory `feedback_visual_qa_self_serviceable`).

## 9. Sequencing, pacing, risk

- **Order:** P0 ✅ → P1 (finish, refined) → P2 (spine: WLC, LXX, Greek-NT) → P3 (version UI) → P2 cont. (Douay/JPS/Vulgate/Arabic) → P4 (note curation). Each phase ships working, tested, committed-on-save software.
- **Pacing:** one phase at a time, HITL check-in at each phase close (memory `feedback_marathon_pacing`); I pause for review/save between phases.
- **Risks:** versification alignment (P2 — the crux; per-source remap + coord guard + graceful omission); EPUB size with many versions (per-edition filtering caps it; monitor); note stable-id durability (P4 — verify/establish before building the override layer); scope is large → the value-ordering means each phase is independently useful even if later ones slip before the deadline.

## 10. Immediate next step

Resume **Phase 1 (B1)** with the two refinements (bake flag + superset `POPUP_LANGUAGES`), finishing Tasks 5–6, then the byte-compat verification. Phase 1 changes nothing the builder sees yet — it is the foundation everything else builds on.
