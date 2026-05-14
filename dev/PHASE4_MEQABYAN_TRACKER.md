# Phase-4 Meqabyan Geʽez-revision — chapter tracker

**Seeded at δ.1.0 (2026-05-14).** Tracker mirrors the 67-chapter
table from `project_maccabees_expansion/03_PROGRESS_TRACKER.md`,
adapted for the YHWH v2.4 repo's δ.1.x cluster.

**Authoritative data file:** `content/divergence/meqabyan_geez_
divergence.json` (the per-verse divergence apparatus).
**Working method:** see `project_maccabees_expansion/02_METHODOLOGY.md`
(operator-side; not re-vendored here). Each session picks the next
un-done chapter, renders the Geʽez column at 350 dpi from the
parallel-Bible PDF (`Bible_Amharic_and_Geez.pdf`, pages 1318-1378
per `content/translations/sources/parallel-bible-eotc/_source.yaml`),
translates verse-by-verse from the page images, appends entries to
the JSON, regenerates the per-book markdown via
`scripts/build_meqabyan_revision.py`, and updates this tracker.

**Honesty rules** (encoded in `meqabyan_geez_divergence.json::_meta.
honesty_rules` + enforced by the tools):

- **No OCR trust** — the PDF's OCR text layer is BADLY GARBLED for
  Geʽez (wrong vowel orders + invented fidel + Latin bleed-through);
  page images are authoritative.
- **Page-image authority** — every entry must derive from a 350 dpi
  page-image read, NOT from the PDF's OCR text layer or from any
  external automated extraction.
- **Flag uncertain readings** — entries with confidence < 0.8 are
  rejected by `build_meqabyan_revision.py` without explicit operator
  override + reviewer sign-off.
- **v1 English immutability** — `content/translations/english/`
  body remains UNCHANGED during the entire δ.1.x arc; the divergence
  apparatus + revision markdown are SEPARATE artifacts. Merge into
  v3 happens at δ.2 (separate phase, gated on publisher review).

**Closed-arc invariants regression-guarded** (must remain green
across every δ.1.x ship):

- γ.4.8.E ARC-CLOSE 67/67 chapter coverage of the Meqabyan
  apparatus (mq1 36/36 + mq2 21/21 + mq3 10/10) — pinned in 5+
  test classes.
- γ.4.8.F Meqabyan voice count ≥212 floor — pinned in 4 test
  classes.

---

## Status legend

```
todo       — not yet touched
draft      — page-image read in progress; entries appended but not reviewed
reviewed   — entries reviewed; confidence ≥ 0.8 across the chapter
arc-ready  — chapter has full divergence entries + revision-markdown
             produced; ready for δ.2 merge consideration
```

## Cluster shipping ledger

| Phase tag | Description | Chapters delivered | Status |
|---|---|---|---|
| δ.1.0 | Seed: infrastructure + tracker + JSON + kinds + tools | 0 | ✓ SHIPPED 2026-05-14 |
| δ.1.x.A.0 | Batch-prep for δ.1.x.A: PDF page estimates + per-chapter verse floors + 10-step operator workflow + new entries-empty invariant codified | 0 (prep-only) | ✓ SHIPPED 2026-05-14 |
| δ.1.x.A | mq1 1-9 batch (~5 chapters/session × 2; operator renders pages 1318-1326 per δ.1.x.A.0 prep) | 0 / 9 | pending (operator-mediated) |
| δ.1.x.B | mq1 10-18 batch | 0 / 9 | pending |
| δ.1.x.C | mq1 19-27 batch | 0 / 9 | pending |
| δ.1.x.D | mq1 28-36 batch | 0 / 9 | pending |
| δ.1.x.E | mq2 1-11 batch | 0 / 11 | pending |
| δ.1.x.F | mq2 12-21 batch | 0 / 10 | pending |
| δ.1.x.G | mq3 1-10 batch | 0 / 10 | pending |
| δ.1.Z | Arc-close: 67/67 + GEEZ_DIVERGENCE_SUMMARY + v3-ready gate | — | gated on δ.1.x.A-G |

---

## 1 Mäqabyan (mq1) — 36 chapters

| Ch | Status | Confidence | Entries | δ.1.x phase | Notes |
|---|---|---|---|---|---|
| 1 | todo | — | 0 | — | — |
| 2 | todo | — | 0 | — | — |
| 3 | todo | — | 0 | — | — |
| 4 | todo | — | 0 | — | — |
| 5 | todo | — | 0 | — | — |
| 6 | todo | — | 0 | — | — |
| 7 | todo | — | 0 | — | — |
| 8 | todo | — | 0 | — | — |
| 9 | todo | — | 0 | — | — |
| 10 | todo | — | 0 | — | — |
| 11 | todo | — | 0 | — | — |
| 12 | todo | — | 0 | — | — |
| 13 | todo | — | 0 | — | — |
| 14 | todo | — | 0 | — | — |
| 15 | todo | — | 0 | — | — |
| 16 | todo | — | 0 | — | — |
| 17 | todo | — | 0 | — | — |
| 18 | todo | — | 0 | — | — |
| 19 | todo | — | 0 | — | — |
| 20 | todo | — | 0 | — | — |
| 21 | todo | — | 0 | — | — |
| 22 | todo | — | 0 | — | — |
| 23 | todo | — | 0 | — | — |
| 24 | todo | — | 0 | — | — |
| 25 | todo | — | 0 | — | — |
| 26 | todo | — | 0 | — | — |
| 27 | todo | — | 0 | — | — |
| 28 | todo | — | 0 | — | — |
| 29 | todo | — | 0 | — | — |
| 30 | todo | — | 0 | — | — |
| 31 | todo | — | 0 | — | — |
| 32 | todo | — | 0 | — | — |
| 33 | todo | — | 0 | — | — |
| 34 | todo | — | 0 | — | — |
| 35 | todo | — | 0 | — | — |
| 36 | todo | — | 0 | — | — |

**mq1 progress: 0 / 36 chapters complete.**

---

## 2 Mäqabyan (mq2) — 21 chapters

| Ch | Status | Confidence | Entries | δ.1.x phase | Notes |
|---|---|---|---|---|---|
| 1 | todo | — | 0 | — | — |
| 2 | todo | — | 0 | — | — |
| 3 | todo | — | 0 | — | — |
| 4 | todo | — | 0 | — | — |
| 5 | todo | — | 0 | — | — |
| 6 | todo | — | 0 | — | — |
| 7 | todo | — | 0 | — | — |
| 8 | todo | — | 0 | — | — |
| 9 | todo | — | 0 | — | — |
| 10 | todo | — | 0 | — | — |
| 11 | todo | — | 0 | — | — |
| 12 | todo | — | 0 | — | — |
| 13 | todo | — | 0 | — | — |
| 14 | todo | — | 0 | — | — |
| 15 | todo | — | 0 | — | — |
| 16 | todo | — | 0 | — | — |
| 17 | todo | — | 0 | — | — |
| 18 | todo | — | 0 | — | — |
| 19 | todo | — | 0 | — | — |
| 20 | todo | — | 0 | — | — |
| 21 | todo | — | 0 | — | — |

**mq2 progress: 0 / 21 chapters complete.**

---

## 3 Mäqabyan (mq3) — 10 chapters

| Ch | Status | Confidence | Entries | δ.1.x phase | Notes |
|---|---|---|---|---|---|
| 1 | todo | — | 0 | — | — |
| 2 | todo | — | 0 | — | — |
| 3 | todo | — | 0 | — | — |
| 4 | todo | — | 0 | — | — |
| 5 | todo | — | 0 | — | — |
| 6 | todo | — | 0 | — | — |
| 7 | todo | — | 0 | — | — |
| 8 | todo | — | 0 | — | — |
| 9 | todo | — | 0 | — | — |
| 10 | todo | — | 0 | — | — |

**mq3 progress: 0 / 10 chapters complete.**

---

## Aggregate progress

```
Total chapters covered:  0 / 67
mq1:                     0 / 36
mq2:                     0 / 21
mq3:                     0 / 10
```

Updated at every δ.1.x.A-G batch ship and at δ.1.Z arc-close.

---

*Phase-4 Meqabyan Geʽez-revision tracker, seeded at δ.1.0 2026-05-14.
Adapted from `project_maccabees_expansion/03_PROGRESS_TRACKER.md`.
CC0 1.0 Universal.*
