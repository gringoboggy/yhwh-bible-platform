# Master roadmap — the forward sequence

> The single live master plan (the third leg of the bootstrap triad). One live
> `dev/PLAN_*.md` at a time is a hard lint invariant (`plan_singular`); prior plans
> live in `dev/archive/` for history. Created 2026-05-30 (mint Phase 2), replacing
> `PLAN_2026-05-24-end-scope.md` (archived) — same forward content, **deadline-free**.
>
> **Guiding principle: quality / completeness over speed.** No time-gating, no
> calendar pressure. Always pick the most complete + correct path; pause to do it
> right. The bar is "mint, professional, solo-maintainable," not "shipped by date X."
> (RULES §2; memory `project_deadline`.)
>
> **Never single-thread (RULES §2.5):** keep ≥2 lanes moving — a foreground lane plus
> a background side-task; when a lane frees, auto-pick the next from the backlog.

---

## The dependency model (own-versification design §4 — load-bearing)

The standalone Ge'ez Bible **render pipeline already exists and is not gated on
finishing the manuscript marathon.** Two independent data-supply lanes both feed the
same own-versification store; neither blocks the render, which ships a complete,
correct Bible for whatever books currently have own-vers data:

```
   LANE M  Kings/Samuel manuscript marathon ┐
   (witness transcription + collation)      ├─► own-vers store ─► build_standalone.py ─► standalone EPUB
   LANE D  Phase-D own-vers re-ingest        ┘                     (LANE A/B/C, shipped)
   (Patrologia vision + HaCohen + distinctive)
```

Per book the order is **pipeline-first / EN-next**: the own-vers text ships first
(popups = KJV cross-ref + variant apparatus), then a faithful English back-translation
trails as its own reviewed lane. The 9 KJV editions never enter `build_standalone`, so
their **byte-stable invariant is structurally independent** of all Ge'ez/Amharic work.

---

## Where things stand (status snapshot — live counts in SESSION_STATE)

**Shipped:**
- ✅ **Standalone Ge'ez Bible, Phases A–C** — collation engine re-architected
  base-witness-primary (drops KJV-spine binning), Ge'ez→KJV cross-ref tool,
  own-vers store model (per-book `VERSIFICATION`), and `scripts/build_standalone.py`.
  Proof EPUB = 4 books / 161 chapters (1ki, 1sa, 2sa, psa), epubcheck 0/0/0/0.
- ✅ **9 KJV editions byte-stable** — `epub_working/` untouched; `build_standalone`
  is a separate path; flagship `catholic-study` epubcheck 0/0/0/0.
- ✅ **EN back-translation core** — Kings/Samuel (324 v) + all 151 Psalms collated in
  `content/translations/geez-tewahedo-en/` (faithful to the Ge'ez wording, never KJV,
  labelled a reading-aid; absent — never faked — where not yet produced).
- ✅ **Corpus depth target comfortably met** — the Ethiopian superset is the deepest
  free Bible apparatus; continued growth is opportunistic, not blocking.
- ✅ **Mint cleanup Phases 0–1** — 11 anti-bloat lint guards + bootstrap slim
  (SESSION_STATE / IN_FLIGHT / RULES); no production code path touched.

**In progress (critical path):**
- ▶ **Mint cleanup Phases 3–6** (this lane) — the near-term sequence (Phase 2 = this roadmap, ✅ done).
- ▶ **Phase D1b — Patrologia own-versification vision lane**, proving the printed-PDF
  vision-transcription path on one book (PO Esther). **Paused at p28** during the mint
  cleanup; resumes after Phase 2. (Marathon-core files are untouched by the cleanup.)

---

## LANE 0 — Mint cleanup (near-term, sequential)

Plan: `docs/superpowers/plans/2026-05-29-mint-cleanup-and-guardrails.md`. Guards ship
RED and force the work; each cleanup phase flips its `_ENFORCE_*` flag to FAIL.

| Phase | What | Status | Depends |
|---|---|---|---|
| mint-0 | 11 anti-bloat lint guards ship RED | ✅ done | — |
| mint-1 | Bootstrap slim (SESSION_STATE / IN_FLIGHT / RULES) → `truth_record_budget` + `frozen_stats` GREEN | ✅ done | mint-0 |
| mint-2 | **Roadmap refresh** (this doc; archive old plan + `SCOPE_2026-05-14`; sync triad plan-name; clear retired-term refs) → `triad_plan_consistency` + `retired_terms` GREEN | ✅ done | mint-0, mint-1 |
| mint-3 | Archive sweep (~75 dated finished docs → `dev/archive/`) → `dev_doc_sprawl` GREEN | ◻ todo | mint-2 |
| mint-4 | Decommercialize (~5,300 LOC dead commercial-era code removed; trim press_kit/distribution to free-only; relocate `resolve_cover_path`; flip banner-pin test first; prove zero EPUB-output change) → `commercial_*` GREEN | ◻ todo · **CHECKPOINT first** | mint-3 |
| mint-5 | Enforce gates (regen REPO_MAP / MATRIX_MAP; wire mypy into pre-commit; restore a remote + CI) → `repo_map_complete` FAIL-enforced | ◻ todo | mint-4 |
| mint-6 | Polish (SessionEnd hygiene hook; sweep stale scanner-cache dirs + root `*.log`; superpowers INDEX + Status headers; optional web.py route-table refactor) | ◻ todo | mint-5 |

Protect the build in every phase: byte-compat invariant (regen + empty `git diff
epub_working/`), flagship epubcheck 0/0/0/0, 9 editions byte-stable. **Never touch the
Ge'ez marathon core.** The remote + CI restore (mint-5) is the single biggest pro-bar
gap — `git push` has failed since the remote was deleted 2026-05-12. (mint-5's remote restore re-opens the closed Git-LFS decision — if the repo nears the host's media cap, reconsider LFS for the cover templates and move backups off `git bundle`.)

---

## LANE A — Standalone Ge'ez Bible pipeline (shipped)

| Phase | What | Status | Depends |
|---|---|---|---|
| A | Collation engine re-architecture (base-witness-primary) + re-collate | ✅ done | — |
| B | Ge'ez→KJV cross-ref tool | ✅ done | A |
| C | Standalone render path + proof EPUB (4 books, epubcheck 0/0/0/0) | ✅ done | A, B |
| EN-core | EN back-translation of Kings/Samuel (324 v) + all 151 Psalms | ✅ done | C |

Spec: `docs/superpowers/specs/2026-05-27-geez-own-versification-design.md`.

---

## LANE D — Phase-D own-versification re-ingest (data-supply; parallel to LANE M)

The geez-tewahedo store is 36 books: 4 own-versified (psa, 1ki, 1sa, 2sa) + 32
KJV-renumbered awaiting Phase-D re-ingest. Each book: vision/parse → own-vers store →
xref sidecar → add to `_STANDALONE_BOOKS` → rebuild → (later) EN back-translation.
**Calibrate-first GO/NO-GO per book.**

| Phase | What | Status | Depends |
|---|---|---|---|
| D1b | Resume PO Esther vision marathon at **p28** → finish Esther → ingest `est_patrologia` → Ge'ez→KJV xref → add to standalone → epubcheck 0/0 + 9 editions byte-stable | ▶ paused p28 | mint-2 |
| D1b-batch | Other 5 Patrologia books (1ch, 2ch, ezr, neh, job — job early since HaCohen cross-validates) + D1a HaCohen sir/wis | ◻ todo | D1b |
| D2 | Distinctive PD acquisition (background lane): 1 Enoch (Charles 1906) + Jubilees (Charles 1895) first; then Meqabyan I–III + 4 Baruch pending a clean-PD-Ge'ez check (re-verify the Meqabyan NO-GO per book) | ◻ todo | C · parallel to D1b/M (background lane, NOT gated on D1b) |
| D-EN | EN back-translation trailing each newly own-versified Phase-D book (translator + independent reviewer) | ◻ todo | D1b-batch |

Method (RATIFIED): the **AGENT** vision path (paid script-API is out of scope — no
budget); MAX 1 heavy agent; tight ≤1568px region crops; controller renders / subagents
Read; per-unit commits; convergence + adversarial review; print-vs-source divergence
**flagged, not harmonized** (read-the-print). Plan
`docs/superpowers/plans/2026-05-28-geez-patrologia-vision-plan.md`; decisions
`content/translations/sources/patrologia/_vision_notes.md`.

---

## LANE M — Kings/Samuel manuscript marathon (parallel data lane; user-paced)

| Phase | What | Status | Depends |
|---|---|---|---|
| M | Remaining Kings/Samuel Ge'ez dual-witness transcription + collation, **run slowly with check-ins** | 🔄 ongoing | A |

The render is NOT gated on this (own-vers §4). Every chapter shipped is a permanent
gain. AGENT path, MAX 1 heavy agent, ≤1568px crops, auto-commit per agent-step (the
unit = one agent-step, not a chapter). Locate folios by vision, not arithmetic. Plan
`docs/superpowers/plans/2026-05-17-kings-manuscript-collation.md`.

---

## LANE P — Parallel-Bible two-standalone end-state (TIER-3, last)

End-state (`dev/archive/SCOPE_2026-05-16-parallel-bible-standalone-bibles.md`,
supersedes the popup-only framing of the archived `SCOPE_2026-05-14`): geez-tewahedo
and amharic-tewahedo become **two full standalone Bible editions** alongside the 9
canon/notes editions, each carrying — in **its own** verse popups — a faithful English
back-translation of **that Bible's actual wording** (never KJV, never the English
apparatus baseline). The other 9 editions get **no** Ge'ez/Amharic popups; the existing
English ethiopian-tewahedo edition may get them **only** under full per-verse parity (a
revisitable option, not a commitment).

| Phase | What | Status | Depends |
|---|---|---|---|
| P2 | Constitute the two standalone editions | ◻ todo | D1b-batch, D2 |
| P3 | Amharic finalized as-written-from-PDF (cited) + Ge'ez gaps filled from the `GAPS/` folder (**DEFERRED, note-only** until the user re-engages) | ◻ todo | P2 |
| P4 | EN back-translation of each Bible's own wording | ◻ todo | P3 |
| P5 | Wire that EN into each Bible's own popups | ◻ todo | P4 |

Do **not** reorder or pull these forward. The Amharic Bible's full ingest is sequenced
**after** the Ge'ez breadth proof (own-vers spec §7). The Ge'ez side is already partway
through this end-state (the standalone EPUB exists with 4 books + EN on
Kings/Samuel/Psalms).

---

## LANE T — Opportunistic depth + correctness backlog (post-decommercialize)

Bounded, mostly not demo-blocking. Verify current state before re-scoping each (several
may have been partly addressed since the old plan). High-priority **corpus-correctness**
items first.

| Item | What | Priority | Status |
|---|---|---|---|
| bookcode | ★BUGCLUSTER — canonicalize legacy book codes (php→phi, jas→jam, jol/ezk/nam/joh) across detectors / `run_*_at_scale` / xrefs / Kenyon map; complete the central `_normalize_book_code`; regen phi/jam corpus; fix the masking test | **P0** corpus-correctness | ◻ open (partly fixed) |
| chap-backfill | Re-run hebrew/greek at-scale for >50-chapter books (Psalms 51–150, Isaiah, Jeremiah); the runner key defaulted to 50, now code-fixed (verify whether already executed) | P0 | ◻ open · pairs with bookcode |
| security | SSRF `{http,https}` scheme allowlist in `core/http.py` (close `file://` LFI) + preview-XSS through `sanitize_html` + rotate the gitignored Voyage key + redact positional secret args in audit_log (verify current state — single-user local app reframes CSRF/rate-limit out of scope, but content-integrity XSS stays) | P1 | ◻ open |
| coverage-floor | Activate the W4.5 coverage floor (install `requirements-dev`, set `--fail-under` from first real measurement); wire `vulture` + `pip-audit` (currently graceful-skipped) — reconcile with mint-5 | P1 | ◻ open |
| smoke-cleanup | `smoke_desktop.py` self-cleanup of the orphaned `_MEI*` PyInstaller extraction dirs left after its `taskkill /F` (TIER-1 hygiene loose-end) | P1 | ◻ open |
| no-kjv-popups | Verse popups for the 7 no-KJV books (Meqabyan I–III, 2 Enoch, Jubilees, 4 Baruch, 1 Clement) — needs PD/Ge'ez source data (overlaps LANE D / GAPS) | P2 | ◻ open |
| phase-E | Clementine Latin appendix (man / 1es / 2es) — clean-digital-first from la.wikisource / Bibliotheca Augustana; 2es Greek is lost so Latin is its primary witness; reuse `vulgate_to_kjv` | P2 | ◻ open |
| track-C | Topical corpus: Torrey shipped **full**; the remaining bounded set (Matthew Henry, JFB, Barnes, Vincent — PD on CCEL) is opportunistic depth, not demo-blocking (Voyage embeddings integration **dropped**) | P2 | ◻ open |
| dead-checks | Wire the built-but-uninvoked audit checks (`audit_dead_code/caches/deps/types` + coverage/taxonomy/a11y) into preflight | P2 | ◻ open · overlaps mint-5/6 |
| code-debt | Reviewed per-category ruff backlog pass (E501/UP045/F401 — **not** wholesale `--fix`; F401 re-export-hub hazard); web.py cluster cleanup (dead code, unified API error envelope, optional god-module extraction, byte-compat-proof); shared `core/at_scale_base` + sources.py split + collapse the 6 commentary clones | P2–P3 | ◻ open · reconcile with mint-4/5/6 |
| data-hygiene | Retire Brenton stubs; recompute geez `_meta`; add geez/amharic-en `_meta`; refresh seed `_meta` notes (couples to LANE P) | P3 | ◻ open |
| identity-docs | Rewrite LICENSE + COPYRIGHT for CC0 (needs the user's copyright-holder name — the one early user ask) + de-commercialize the identity docs (VERSION/README/RELEASE_NOTES/HANDOFF) — **bundles with mint-4** | P3 | ◻ open · needs user input |
| asset-licensing | Asset-licensing/attribution docs for the 25 Midjourney cover templates + book art + fonts, extending `content/sources/ATTRIBUTIONS.md` (text sources already documented) | P3 | ◻ open |
| reverify | Generalize the Douay/Vulgate SHIFTS=0 versification check to the earlier-ingested translations (WLC/LXX/Arabic/JPS) — verification hardening | P3 | ◻ open |
| vision-ocr | Generalize `manuscript_vision.py` into a shared printed-PDF vision-OCR engine (powers phase-E + bulk Ge'ez/Amharic ingest; OOM caps) | P3 enabler | ◻ open |
| builder-UI | Phase 3 (per-book version-selection UI) + Phase 4 (per-note curation / source review) — the last builder-roadmap UI phases, as configurable builder options | P4 | ◻ open |
| **[USER]** eyeball | Real-reader presentation eyeball — final visual QA on real hardware (e-ink Kobo color + tablet/phone reader apps); the one item Claude can't self-verify; **batched at project END** with final tests/touch-ups, NOT pulled forward (much visual QA is self-serviceable via unzip→`http.server`→Playwright; only true device behaviours need the user) | end-stage | ◻ open |

---

## Parked / known-residual (not active tasks)

- **Irregular-layout inject residual (~156–161 notes).** All 87 books / 1,702 chapters
  ARE complete; the residual is note sources numbering a verse the base chapter lacks
  (aes, 1en, mq1–3, sir, jub). Editorial — NOT addable by guessing; needs a per-book
  multi-file verse index or a base re-render. Carry as a known residual, not a task.

---

## Explicitly NOT doing (de-scoped, on the merits — not schedule)

- **No deadline / no time-gating.** Quality over speed; recommend the right fix even if
  big or invasive.
- **No commercial surfaces** — the free-public pivot (2026-05-14) dropped all retail
  metadata and sales/distribution surfaces; multi-format export survives only as a free
  download. <!-- term-ref-ok -->
- **No language rewrite** — KEEP PYTHON (strongest ecosystem fit; rewrite = pure
  regression risk for zero functional gain).
- **No DB / no replacing the data-as-tuples store** — deliberate, git-diffable,
  dependency-free.
- **No splitting web.py / build_edition.py for size** — large files of small cohesive
  functions, not god-modules.
- **Voyage embeddings INTEGRATION dropped** — only the key-rotation security item
  survives. "More AI" = content runs, not infra builds.
- **No public-server hardening** — Wave 4 chose a single-user **local** desktop app, so
  CSRF / rate-limiting / hosting are out of scope.

---

## Sequencing (RULES §3)

TIER ordering from the post-Wave-4 backlog: **TIER-1 loose ends → TIER-2 depth →
TIER-3 parallel-Bibles arc LAST.** Within that: safest/most-foundational first
(mint cleanup is foundational doc/guard work); builder-demo value next; pair related
phases; stop at clean seams; inventory before building. The near-term spine is
mint-2 → mint-3 → mint-4 (CHECKPOINT) → mint-5/6, with LANE D (Phase-D Esther) resuming
in parallel after mint-2 and LANE M proceeding at the user's pace throughout.
