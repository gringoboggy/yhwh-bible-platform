# Design — Per-edition themes + tradition-aware multi-translation verse popups

**Date:** 2026-05-22
**Status:** DRAFT — awaiting user review (then → writing-plans)
**Origin:** 2026-05-22 visual-QA browser pass found (a) all editions ship the
no-op `classic` theme (no edition sets `theme:`), and (b) verse popups are
KJV-English-only for most books. User direction: "per edition [themes]" + "all
pop ups should have several translations except for the amharic/ge'ez."
**Decisions locked (brainstorm):** theme mapping as proposed; popup scope =
**full multi-version palette** (tradition-aware per edition).

> NOTE: this doc is written, not committed — "continue" ≠ "save" (memory
> `feedback_continue_not_save`). It commits on the user's next explicit save.

---

## 1. Goal

1. **Themes per edition.** Every edition declares a `theme:` so its built EPUB
   carries a visually distinct house style (the 4 real themes already exist).
2. **Multi-translation verse popups.** Every verse popup in the 9 "regular"
   editions shows *several* translations, chosen **per edition by tradition**
   (the existing per-edition popup-language system). The 2 **standalone
   Ge'ez/Amharic** bibles are the explicit **exception** — they keep their own
   English back-translation popups (memory
   `project_parallel_bible_two_standalone_bibles`; `SCOPE_2026-05-16`).

Success: an edition's EPUB looks themed; tapping a verse number shows that
edition's tradition-appropriate set of translations (e.g. Catholic → KJV +
Douay-Rheims + Vulgate + LXX-Greek + Hebrew + Greek-NT). All editions stay
epubcheck-clean (0/0/0/0).

## 2. Current state (verified 2026-05-22)

- **Themes:** `build_edition.py` (~L2782) does `edition.get("theme","classic")`
  and appends `content/themes/{theme}.css`. **No** edition sets `theme:`, so all
  get the no-op `classic`. Real themes on disk: `scholarly` (dense Charter
  serif), `devotional` (warm Iowan italic, cream bg), `modern` (blue sans),
  `school` (large Verdana). `classic` = intentional no-op.
- **Popup model:** `scripts/generate_verse_popups.py::build_vnote_aside` bakes
  `<aside class="vnote">` into the base HTML (`epub_working/`) with **fixed**
  slots `{english, hebrew, greek}` (CSS `.vnote-text/.vnote-hebrew/.vnote-greek`,
  `lang`/`dir` set). `harvest_existing_langs` preserves any he/gr already wrapped.
- **Per-edition popup languages:** `build_edition.py::POPUP_LANGUAGES` registry +
  `_resolve_popup_languages` + `_apply_popup_languages_and_translation` strip
  per-language at build time. Registry already declares `english/hebrew/greek`
  (with data) and dataless `aramaic/geez/latin/coptic/syriac/amharic`.
- **Translation data (the constraint):** `content/translations/` —
  **kjv = full** (81 books); **geez-tewahedo / amharic-tewahedo = full**
  (standalone ingests). **wlc, lxx-brenton-greek, lxx-brenton-english,
  douay-rheims, jps, vulgate-clementine, arabic-vandyke = Genesis-only seed
  samples (~1 KB each).** The ~11 books that currently show he/gr in popups got
  it from a one-time *harvest*, not these files. **No Greek NT exists at all.**
- **Coordinate spine:** popups are keyed to the canonical (WEB/KJV) coordinate
  `(code, ch, vs)`. `scripts/core/canonical_verse_counts.py` defines canonical
  extents + a promote-boundary coord guard.

## 3. The two hard problems

1. **Acquisition.** "Several translations everywhere" requires full-Bible PD
   source for each version, then ingestion across all books. Only KJV is full
   today. This is a content project, not a wiring task.
2. **Versification alignment (the crux).** Hebrew (WLC), LXX, Vulgate, and KJV
   number verses differently (Psalm superscriptions, Psalm splits, Daniel
   additions, Joel/Malachi chapter breaks, 3 John, etc.). Each source's text
   must map onto the canonical `(code, ch, vs)` the popup is keyed to.

## 4. Architecture

### 4.1 Themes (Phase 0 — small)

Add `theme:` to each edition in `content/editions.yaml`. No code change — the
existing applicator handles it. Mapping (locked):

| theme | editions |
|---|---|
| `classic` | ethiopian-tewahedo, anglican-bcp, standalone-geez, standalone-amharic |
| `scholarly` | scholarly-academic, jewish-study, lutheran-confessional |
| `devotional` | catholic-study, eastern-orthodox, coptic-orthodox |
| `modern` | evangelical-reformed |

(`school` stays registered for the wizard picker; no demo edition uses it.)

### 4.2 Multi-version popup model (replaces fixed en/he/gr)

`build_vnote_aside` takes an **ordered list** of version entries instead of
fixed kwargs:

```
version = {id, label, lang, dir, text}      # e.g. {"id":"douay","label":"Douay-Rheims (Challoner)","lang":"en","dir":"ltr","text":...}
build_vnote_aside(*, code, ch, vs, title, versions: list[version]) -> str
```

Each renders as `<p class="vnote-source-label">{label}</p>` +
`<p class="vnote-{id}" lang="{lang}" dir="{dir}">{escaped text}</p>`. KJV leads
(its label may stay implicit for back-compat with the recovered-base contract).
`harvest_existing_langs` generalizes to harvest **all** `vnote-*` version paras,
not just he/gr, so a regen never drops content the resolver can't reproduce.

**Why per-version CSS class (not per-language):** several versions share
`lang="en"` (KJV, Douay, JPS, Brenton-EN). The per-edition stripper must filter
each *version* independently, so the class key is the version id, not the
language.

### 4.3 Version registry + per-edition stripping

`POPUP_LANGUAGES` becomes a **version registry** keyed by a short **version id**:
`{id: {label, content_class: f"vnote-{id}", lang, dir, has_label_para}}`. Version
ids map to translation-module ids: `kjv`→kjv, `wlc`→wlc, `lxx-greek`→
lxx-brenton-greek, `brenton-en`→lxx-brenton-english, `douay`→douay-rheims,
`jps`→jps, `vulgate`→vulgate-clementine, `arabic`→arabic-vandyke, `greek-nt`→
(new PD Greek-NT id chosen at acquisition, e.g. `byzantine-greek`). Legacy
language ids alias for back-compat (`english`→kjv, `hebrew`→wlc,
`greek`→lxx-greek) so existing configs don't break. Per-edition selection
**reuses the existing** `popup_languages_default` / `popup_languages_per_book`
fields — now populated with version ids (no new schema field) — and
`_apply_popup_languages_and_translation` filters by version id. Tradition mapping:

| edition | popup_versions |
|---|---|
| ethiopian-tewahedo | kjv, wlc, lxx-greek, greek-nt |
| scholarly-academic | ALL (kjv, douay, jps, brenton-en, wlc, lxx-greek, greek-nt, vulgate, arabic) |
| jewish-study | jps, wlc, kjv |
| evangelical-reformed | kjv, wlc, lxx-greek, greek-nt |
| catholic-study | kjv, douay, vulgate, lxx-greek, wlc, greek-nt |
| eastern-orthodox | kjv, lxx-greek, brenton-en, greek-nt |
| coptic-orthodox | kjv, lxx-greek, greek-nt, vulgate, arabic |
| anglican-bcp | kjv, wlc, lxx-greek, greek-nt |
| lutheran-confessional | kjv, wlc, greek-nt, vulgate |
| **standalone-geez** | **EXCEPTION** — own Ge'ez text + `geez-tewahedo-en` back-translation popup only |
| **standalone-amharic** | **EXCEPTION** — own Amharic text + `amharic-tewahedo-en` back-translation popup only |

Per-verse availability is graceful: a version is included only if it returns
text for that canonical coord (NT versions absent on OT verses, JPS/WLC absent
on NT, etc.).

### 4.4 Acquisition + versification adapter (per source)

Each translation follows the existing reference-corpus pipeline (memory
`project_corpus_reference_expansion`): clean PD source → `extract_<id>.py` →
validated index → `batch_insert` to `content/translations/<id>/`, **normalized
to canonical `(code, ch, vs)`** via a per-source versification adapter. The
adapter is identity for KJV-aligned sources and a small remap table at known
divergence loci for WLC/LXX/Vulgate. Reuse `canonical_verse_counts` coord guard
so no out-of-extent verse lands. Update `content/translations/ATTRIBUTIONS.md`.

**Locked PD sources (most-accepted per type; web-verified 2026-05-22).** Use the
text portions — public domain even where a host repo adds CC-BY morphology tagging:

| version id | source (PD) | machine-readable access |
|---|---|---|
| `wlc` | Westminster Leningrad Codex | `openscriptures/morphhb` (OSIS XML) |
| `lxx-greek` | Brenton LXX Greek, 1851 (Vaticanus-based) | CCEL `bible/brenton` / archive.org |
| `brenton-en` | Brenton English LXX, 1851 | eBible `eng-Brenton` (USFM) |
| `greek-nt` | Scrivener's Textus Receptus, 1894 (KJV-aligned) | `byztxt/greektext-scrivener` (GitHub) |
| `douay` | Douay-Rheims, Challoner rev. | `seven1m/open-bibles` / drbo.org |
| `jps` | JPS 1917 Tanakh | `seven1m/open-bibles` / sacred-texts |
| `vulgate` | Clementine Vulgate | `seven1m/open-bibles` (Clementine) |
| `arabic` | Smith–Van Dyck, 1865 | eBible (Arabic Van Dyck, USFM) |

**Deliberately NOT used:** Rahlfs LXX and Nestle-Aland/UBS NT — both under active
copyright (Deutsche Bibelgesellschaft). Swete is the PD critical-LXX fallback if a
more critical Greek OT is later wanted; Robinson-Pierpont Byzantine (PD) is an
optional second Greek-NT for the Orthodox editions. Acquisition per source is one
plan sub-phase; a blocked source does not block the others.

## 5. Data flow

```
PD source → extract_<id>.py → versification adapter (→ canonical coords)
          → batch_insert → content/translations/<id>/<book>.py
generate_verse_popups.py: for each canonical (code,ch,vs):
   versions = [translations.get_verse(id, code,ch,vs) for id in REGISTERED if present]
   → build_vnote_aside(versions=...) baked into epub_working/
build_edition.py (per edition): _resolve popup_versions → strip non-selected
   version <p>s from each aside → themed, filtered EPUB
```

## 6. Testing strategy (TDD throughout — memory `feedback_proper_clean_correct`)

- **Themes:** each edition's resolved theme matches the map; two
  differently-themed editions produce **different** `stylesheet.css` (hash);
  each built stylesheet contains its `=== theme: <id> ===` marker. Rebuild +
  epubcheck 0/0/0/0.
- **Popup model:** `build_vnote_aside` with N versions renders N labeled
  per-version paras with correct `lang`/`dir`/class; idempotent regen; harvest
  preserves all versions.
- **Per-source ingest:** coverage assertions (e.g. wlc covers all OT books),
  sample-verse correctness, versification-map correctness at named divergence
  loci, coord-guard (0 out-of-extent).
- **Per-edition stripping:** each edition's resolved `popup_versions` shows
  exactly its set + strips the rest; standalone editions keep their own popups.
- **Integration:** regenerate popups → build all editions → epubcheck 0/0/0/0 →
  browser-render spot check (self-serviceable QA, memory
  `feedback_visual_qa_self_serviceable`); EPUB size monitored (many versions ×
  ~36k verses can bloat — per-edition filtering keeps each reasonable).

## 7. Phasing (value-ordered — partial completion still ships value)

- **Phase 0 — Themes.** Assign `theme:` ×11 + tests + rebuild/verify. *Quick win.*
- **Phase 1 — Multi-version model refactor.** `build_vnote_aside` list-based +
  version registry + stripper by version id + versification-adapter framework.
  No new data yet (tests against KJV + harvested he/gr). Byte-compatible regen.
- **Phase 2 — Original-language spine.** Acquire/ingest full WLC Hebrew (OT) +
  LXX Greek (OT) + Greek NT. Regenerate. Now every verse has English + its
  original language(s). **This is the headline deliverable.**
- **Phase 3 — Secondary versions.** Brenton-EN, Douay, JPS, Vulgate, Arabic —
  one acquire+ingest+align sub-phase each.
- **Phase 4 — Tradition-aware config + finalize.** Per-edition `popup_versions`
  + standalone exception + full regeneration + epubcheck + browser QA.

## 8. Risks

- **Versification alignment** — the crux; mitigated by per-source remap tables +
  coord guard + graceful per-verse omission. Budget real time here.
- **Acquisition dependency** — gated on clean PD sources (user-supplied or
  archive.org). Each source is one sub-phase; blocked sources don't block others.
- **Deadline (2026-06-07)** — value-ordered phasing means Phases 0–2 deliver the
  themed-EPUB + originals headline even if 3–4 slip.
- **EPUB bloat** — per-edition version filtering caps per-edition size; monitor.

## 9. Out of scope

- Ge'ez/Amharic popups in the 9 regular editions (the standalone bibles own
  those; `project_parallel_bible_two_standalone_bibles`).
- The unrelated cover-not-applied finding (separate `build_one` fix; tracked in
  `dev/VISUAL_QA_CHECKLIST.md` Findings).
- New UI in the wizard/customize consoles (the version registry surfaces
  automatically; console wiring is a later, optional follow-up).
