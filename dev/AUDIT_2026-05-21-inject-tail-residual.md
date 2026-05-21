# Inject-tail residual audit (2026-05-21, after boundary-aware spill resolver)

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

**Disposition:** document; defer. Each needs per-book structural investigation (multi-file
spill index or a base re-render), which is a larger, separate effort — explicitly NOT hacked
against the verified 99.48% state near the 2026-06-07 deadline.

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
   versification subtleties.

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
