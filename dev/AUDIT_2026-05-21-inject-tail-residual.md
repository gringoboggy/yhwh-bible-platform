# Inject-tail residual audit (2026-05-21, after boundary-aware spill resolver)

> **SUPERSEDED SNAPSHOT (pre-rebuild) — read this first.** This documents the **277**-note
> residual at the 52,973-note corpus, BEFORE the 2026-05-21 reference-corpus rebuild.
> **Current state (corpus 67,715, verified via `audit_base_html.py --coverage`): 0
> chapter-coverage gaps** — all **87 books / 1,702 chapters** are present in the base HTML;
> the residual is **~156-161 notes that are purely verse-level versification** (the note's
> *source* numbers a verse the base chapter lacks): `aes` 73 · `1en` 31 · `mq1-3` 33 · `sir`
> 10 · `jub` 9 (by kind `lang-hebrew` 83 / `comm-ethiopian` 70). The "class A — chapter-absent"
> heading below was a **mis-label** (the aes note already corrected it to versification); no
> book is truncated. Authoritative current map: `dev/MATRIX_MAP.md` → "Base-HTML structure &
> coverage". The per-class adjudication below remains a useful reference.

**Context:** `docs/superpowers/plans/2026-05-21-inject-tail-completion.md` Phases 1–3
took EPUB note placement from **52,553 → 52,696 / 52,973 = 99.48%** (+143) via the
boundary-aware Strategy-B spill resolver (`inject.find_verse_region_b_spill`). This
doc enumerates and adjudicates the **277 still-unplaced notes** so the residual is a
documented decision, not an unknown. Tooling: `scripts/audit_base_html.py`
(`classify_book`, `verse_absent_report`, `--verse-absent`).

Placement is **not** expected to reach 100% by mechanical injection — the residual is
dominated by base-HTML coverage gaps and source-data key errors that require editorial
judgement (and must NOT be guessed near the deadline).

---

## The 277 residual, by class

### A. chapter-absent — 110 notes (the chapter has no anchor in the base HTML)

| book | notes | nature | disposition |
|------|------:|--------|-------------|
| aes  | 73 | **versification-scheme mismatch, NOT absence** (see below) — the base ALREADY renders aes | editorial verse-concordance; do NOT render (would duplicate) |
| pro isa 1jn rev 2ch neh jer 2pe job lam jon | 37 | 1–5 each; the chapter exists in the book but its `ch-{bxx}-c{ch}` anchor variant isn't found, or the chapter is genuinely absent | versification/coverage; document, do not hack |

**aes finding (Phase 4 premise REFUTED — verified 2026-05-21):** the plan assumed the base
"never rendered aes's chapters." It did. aes = `b25`, single file `index_split_028.html`, and
the base renders it as **chapters 1–10** (the World English Bible narrative ordering of the
Greek Additions: `b25 c1` = the Dream of Mordecai = KJV's 11:2; `b25 c10` = "the king levied a
tax" = canonical Esther 10). The 82 aes **notes**, however, are keyed to the **KJV/Vulgate
appendix scheme** (chapters 10, 11, 13, 14, 15, 16) — so notes on ch11–16 hit "chapter heading
not in any file" (73 of them) and the ch10 notes (on v4–13) don't match base c10 (v1–2). This
is the same text under two different chapter/verse arrangements. Rendering KJV ch11–16 into the
base would graft a SECOND, duplicate copy of the Additions onto a book that already contains
them. **Correct fix = re-map the 82 aes notes from the KJV appendix scheme to the base's WEB
narrative scheme** (a known but non-trivial Esther-Additions concordance) — an editorial
decision, NOT a guess and NOT a render. Deferred to editorial review with the verse-absent set.

### B. verse-region-not-parseable (Strategy B) that are NOT clean single-file spills — 98 notes

The boundary-aware spill resolver fixed every chapter whose anchor ends file N and whose
verses open file N+1 (jer 57→0, psa 24→0, isa 43→4, 1ch 29→5). The residual 98 are a
DIFFERENT shape and the spill guard correctly **declined** them (placing would have been a
mis-placement):

| books | notes | likely cause |
|-------|------:|--------------|
| mq1 21 · mq3 7 · mq2 5 | 33 | Mäqabyan (Tewahedo-distinctive) — sparse/odd layout: anchors clustered with empty regions; verses not in a single next-file head |
| sir 10 · jub 9 | 19 | deuterocanon — likely multi-file spill or internal structure |
| rom 9 · mat 6 · act 4 · jhn 3 | 22 | NT — investigate per-book |
| 1ch 5 · isa 4 · others | ~24 | residual after the clean spills (e.g. a second internal split, or verse out of the spilled head's range) |

**Disposition (VERIFIED 2026-05-21 via per-note diagnostic — none are recoverable spills,
`spill_resolves=False` for all 98):** two confirmed sub-classes, neither mechanically
addable —
- **Out-of-range verse keys** (`mat 6:83` / `20:39–75`, `act 9:80` / `17:81`, `jhn 16:80`,
  `mrk 3:81` / `10:115`, `gal 3:39`): the verse number exceeds the chapter's real length; the
  `<span class="vn">` doesn't exist in the base at all → source-data key errors (same class as
  the Strategy-A topic-nave defect in §C).
- **Versification mismatches** (`rom 16:26–27` doxology; `sir 26:21–26` Sirach numbering;
  `jub` Jubilees numbering): the note's chapter/verse scheme differs from the WEB base's →
  editorial concordance, do not guess. Defer.

### C. verse-absent (Strategy A) — 72 notes (`verse_absent_report()`; inject runtime "(no verse anchor)" = 69)

The exact verse anchor `id="v-{code}-{ch}-{v}"` is absent from every one of the book's split
files. Two sub-classes:

1. **1 Enoch chapters ≥ 37 — ~25 notes** (39:6, 46:3, 89:59, 90:*, 91:*, 94:0, 96:3, 97:8,
   98:*, 99:*, 100:*, 102:*, 103:*). These are the known **1 Enoch 37-108 base-render gap** —
   1en's later chapters were never rendered into the base HTML (same class as aes, but a much
   larger render). Addable only by rendering 1 Enoch 37-108 (a separate, large effort).
2. **Out-of-range / mis-keyed note coordinates — the rest** (e.g. `deu 81/82/97`, `gen
   85/87/88/89`, `num 81/82/84`, `1sa 34:50`, `jdg 30:16`, plus invalid verses like `gen
   20:20`, `jos 13:81`, `2sa 8:23`, `2sa 19:85`, `1en 91:0`/`94:0` (verse 0)). The chapter or
   verse exceeds the book's real extent (Genesis has 50 chapters, Deuteronomy 34, Numbers 36,
   1 Samuel 31) — these are **source-data key errors in `content/notes/*.py`**, not
   versification subtleties. **ROOT CAUSE VERIFIED 2026-05-21:** every out-of-range gen/deu/num
   case read is `kind=topic-nave` (Nave's Topical Bible, χ.7) with an empty anchor and an
   OCR-garbled topic name (`TO SFECIAJ`, `UXCHARITABLENESS`, `WARNINGS AOAINST`, `AMMIHUD,
   SHEMUEL`). So the **Nave's topical extractor mis-parsed reference coordinates into
   non-existent (book, ch, v) tuples** — a corpus-quality defect in the Nave's pipeline, not a
   placement problem. **FIXED 2026-05-21** (see "Nave's data-bug fix" below): the full
   corpus-wide scope was **114 invalid `topic-nave` notes** across 37 books (not ~40–50); all
   pruned, root cause closed, index cleaned. `1en` ≥37 remains a SEPARATE class (base-render
   gap, §C.1); the 2 invalid `text-witness` notes (gen + jos) are a different kind/provenance,
   flagged but not addressed here.

## Nave's data-bug fix (2026-05-21)

**Root cause:** `fetch_sources._build_naves_indices` accepted pre-parsed `[book, ch, verse]`
triples from the OCR-noisy upstream Nave's source **without canonical-range validation**, so
impossible coordinates (Genesis 87, Deut 81, Matthew 6:83 …) propagated into
`content/sources/naves_topical.json` → `NaveTopicalDetector` candidates → 114 promoted notes
that can never inject. Confirmed: the 114 invalid notes mapped 1:1 to 114 invalid refs in the
index.

**Fix (root cause + cleanup):**
1. `_build_naves_indices` now rejects out-of-range coordinates via a new `_naves_coord_in_extent`
   (validates against `canonical_book_shape`; keeps unknown-extent Tewahedo books). TDD:
   `TestNavesFetchSourceUtilities::test_build_indices_drops_out_of_range_coords` +
   `…keeps_when_extent_unknown`.
2. Rebuilt `naves_topical.json` from its own forward `topics` index via the now-validating
   builder: n_refs 40444 → 40326 (−118), n_topics 3973 → 3967 (−6 all-garbage topics), 0
   out-of-range refs remain.
3. Pruned the 114 invalid `topic-nave` notes from 37 `content/notes/*.py` files via ast-span
   removal (every other byte preserved; each file re-parsed + `load_notes` delta-checked).

**Result:** corpus 52,973 → 52,859 (−114 dead notes); inject placement **99.48% → 99.69%**
(52,696 / 52,859); residual misses 277 → 163. Verified: 7 builder tests + 21 χ.1 + 24 build-smoke
green; ruff-format clean; `lint_rules` clean. **Recurrence prevented** — any future Nave's
re-fetch/re-promote drops impossible coordinates at the builder boundary.

**Disposition:** document; **do NOT auto-fix**. Per the plan's hard rule, a note's (ch, v)
is corrected only with a clear 1:1 mapping to an existing WEB verse — the out-of-range keys
have no unambiguous target, so fixing them is an editorial decision for the maintainer, not a
guess. Recommend a follow-up editorial pass over the flagged coordinates (run
`python scripts/audit_base_html.py --verse-absent` for the live list).

---

## Final placement decision

- **Mechanically addable, DONE:** the 143 split-layout notes (Phase 3). Verified `ebible
  verify` errors=0 / 15790 paired, valid EPUB. Placement **99.48%**.
- **NOT mechanically addable — editorial (do not guess):**
  - aes 73 — WEB↔KJV Esther-Additions versification concordance (re-key notes 10–16 → 1–10).
  - verse-absent out-of-range keys ~44 — source-data (ch, v) corrections in `content/notes/*.py`.
- **NOT mechanically addable — larger render efforts:**
  - 1 Enoch 37-108 render gap (~25 verse-absent notes) — render the absent chapters into base.
  - Strategy-B non-spill irregular layouts (98: mq1/2/3, sir, jub, rom, mat, act, jhn) — per-book
    multi-file spill index or base re-render.

**Both remaining substantive tasks beyond Phase 3 (the planned aes "render", and the
verse-absent "fixes") turned out to be editorial/versification decisions, NOT mechanical inject
fixes** — confirmed by reading the real data, the same way Phase 2's full-walk index was found
unsound. Phase 3's boundary-aware spill captured essentially all of the *mechanically*-placeable
tail (+143). The verified **99.48%** demo build is the deadline-priority state; the enumerated
277-note remainder has a documented owner-action each, rather than being an open unknown.
