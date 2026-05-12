# SCOPE addendum — γ.4.x Ethiopian Tewahedo corpus expansion

**Date:** 2026-05-12
**Parent phase:** γ.4 (Ethiopian Tewahedo commentary — shipped 2026-05-12)
**Status:** γ.4.1 CLOSED 2026-05-12 modulo unfillable Jn 8-10 gap
(Cyril Books VII-VIII LOST). γ.4.1.A (John 1-4, 30) + γ.4.1.B (John 5-7,
27) + γ.4.1.C (John 11-14, 29) + γ.4.1.D (John 15-21, 30) all shipped
2026-05-12 = 116 Cyrilline-John entries spanning the full Gospel
minus the manuscript-tradition gap. γ.4.2 wave-1 (Ephrem on Gen 1-11,
32 entries) also shipped 2026-05-12, sequenced per AUDIT_2026-05-12-B
§ix recommendation to rebalance voice mix from 93% Cyril to current
76% Cyril / 23% Ephrem / 1% 1 Enoch. Combined γ.4.x ship-to-date:
148 entries beyond the γ.4 seed of 12 (corpus total 160). γ.4.2.B-D
(Ephrem Gen 12-50 / Exodus / Numbers + Deut) + γ.4.3-6 still open.

---

## Context

γ.4 shipped 12 seed entries across Ephrem the Syrian / Cyril of
Alexandria / 1 Enoch (R.H. Charles 1912 translation, Ethiopian-
canonical) covering Genesis 1-6, Psalms 1+23, and John 1+19.
PROPOSAL_FEATURE_LANDSCAPE §6 names the eventual corpus target as
"1K-note dump" — comparable to γ.3's planned Patristic corpus
target. γ.4 ships infrastructure + flagship sample; γ.4.x expands
the seed into the full corpus.

This addendum captures the per-source ETL roadmap so future γ.4.x
sub-phases ship against an explicit plan.

---

## Public-domain source inventory

### Ephrem the Syrian (d. 373 AD)

- **NPNF Series 2, Vol 13** (ed. J. Gwynn / Schaff, 1898)
  — Commentary on Genesis, Commentary on Exodus, selected
  Hymns on Paradise, selected Sermons. ~250 pages of English
  translation; ~700-900 verse-keyed entries achievable via
  per-pericope summarization.
- **Hymns on the Nativity** (ed. K.E. McVey, 1989) — NOT PD.
  Skip.
- **Commentary on the Diatessaron** (PD via Carmel McCarthy
  1993 translation? Not PD; 1993). Original Syriac is PD;
  no PD English translation. Skip until 2089.
- **Source format:** plain prose. ETL-friendly.

### Cyril of Alexandria (d. 444 AD)

- **NPNF Series 2, Vol 7** — Letters + Thesaurus + Five
  Tomes Against Nestorius. ~600 pages; theology-heavy, less
  verse-keyed than Ephrem.
- **NPNF Series 2, Vol 14** — Commentary on the Gospel of
  John. ~500 pages, verse-by-verse. Highest yield: ~400-600
  verse-keyed entries from John alone.
- **Commentary on Luke** (PD via R. Payne Smith 1859
  translation — Open Library). ~600 pages. ~400 verse-keyed
  entries.
- **Source format:** Cyril's commentary is structurally
  verse-keyed (commenting "On verse X" sequentially). ETL is
  straightforward — text is already organized by verse.

### 1 Enoch (R.H. Charles 1912, PD)

- **The Book of Enoch** (Oxford: Clarendon, 1912). ~100 pages
  of Charles' commentary + introduction + Ethiopic text.
  Charles' commentary is verse-keyed to 1 Enoch chapter:verse.
- **Strategy:** entries live under 1 Enoch's own
  book/chapter/verse keys (NOT cross-referenced into Genesis
  6:1-4 — γ.4 covers the Genesis cross-ref already). The
  Tewahedo edition has 1 Enoch as Scripture; other editions
  see these entries only if their `traditions_default`
  includes `tewahedo` AND their `canon` includes 1 Enoch.
- **Target:** ~300 verse-keyed entries from the 108-chapter
  book.

### Andəmta (Amharic homiletic commentary) — DEFERRED

- The Tewahedo Church's living homiletic-commentary tradition
  is in Amharic + Ge'ez. Translations into English are
  scattered and mostly post-1989 (NOT PD).
- **Strategy:** defer until the project has either (a) a
  translation budget (commission specific pericopae), or (b) a
  partnership with a Tewahedo seminary to license PD
  translations. Tracked as γ.4.z (z for "blocked").

### Synaxarium (Senkessar) — partial

- The PD English translations of the Ethiopian Synaxarium exist
  (E.A. Wallis Budge 1928; PD globally). ~400 entries on saints'
  days; not verse-keyed but date-keyed.
- **Strategy:** these don't fit the verse-keyed detector
  pattern. Future ψ-phase could surface them as a date-keyed
  liturgical sidebar in editions whose traditions include
  `tewahedo`. Tracked as γ.4.y (orthogonal pattern).

---

## γ.4.x sequence

```
γ.4.1   Cyril's John commentary (NPNF S2 V14)        ~400-600 entries
        ├─ γ.4.1.A  John 1-4 (Prologue + Cana +      30 entries  ✓ SHIPPED 2026-05-12
        │           Nicodemus + Samaritan woman)                  [first wave]
        ├─ γ.4.1.B  John 5-7 (Bethesda + Bread of    27 entries  ✓ SHIPPED 2026-05-12
        │           Life + Tabernacles)                           [second wave]
        ├─ γ.4.1.C  John 11-14 (Lazarus + Last       29 entries  ✓ SHIPPED 2026-05-12
        │           Supper + Farewell Discourse I)               [third wave]
        └─ γ.4.1.D  John 15-21 (Vine + High-         30 entries  ✓ SHIPPED 2026-05-12
                    Priestly Prayer + Passion +                   [fourth wave]
                    Resurrection)                                 CLOSES γ.4.1
        [γ.4.1 books VII-VIII covering John 8-10 are LOST in
         the manuscript tradition; no Cyril coverage possible
         for those chapters per the addendum]
γ.4.2   Ephrem on Genesis (NPNF S2 V13)              ~200-300 entries  PARTIAL
        ├─ γ.4.2.A  Gen 1-11 (primeval history)      32 entries  ✓ SHIPPED 2026-05-12
        │           (creation + Sabbath + Eden +                  [first wave]
        │           Fall + protoevangelium + Cain/                AUDIT-recommended
        │           Abel + Enoch + Noah-flood-                    rebalance
        │           rainbow + Babel)
        ├─ γ.4.2.B  Gen 12-50 (patriarchal narrative) ~40-60 entries
        │                                                         open
        ├─ γ.4.2.C  Ephrem on Exodus                  ~40-60 entries
        │                                                         open
        └─ γ.4.2.D  Ephrem on Numbers + Deuteronomy   ~30-40 entries
                                                                  open
γ.4.3   Cyril's Luke (Payne Smith 1859 — PD)         ~400 entries      open
γ.4.4   1 Enoch (Charles 1912) verse-keyed entries   ~300 entries      PARTIAL
        ├─ γ.4.4.A  First wave covering all 5 books  30 entries  ✓ SHIPPED 2026-05-12
        │           (Watchers + Parables +                        [Jude pin + Son of
        │           Astronomical + Dream Visions /                Man + White Bull]
        │           Animal Apocalypse + Epistle)
        ├─ γ.4.4.B  Watchers detail expansion         ~50-70 entries  open
        ├─ γ.4.4.C  Parables (Son of Man) detail      ~50-70 entries  open
        ├─ γ.4.4.D  Astronomical + Dream Visions      ~40-60 entries  open
        └─ γ.4.4.E  Epistle of Enoch detail           ~40-60 entries  open
γ.4.5   Ephrem's Hymns on Paradise selections        ~80 entries       open
γ.4.6   Cyril's Letters + Thesaurus (selective)      ~150-200 entries  open

γ.4.y   Synaxarium date-keyed liturgical sidebar     ~400 entries      open
        (orthogonal pattern; needs new infrastructure)
γ.4.z   Andəmta — BLOCKED on translation budget /
        seminary partnership                                            BLOCKED
```

**Total achievable PD corpus** (γ.4.1-γ.4.6): ~1,500-1,800
verse-keyed entries — comfortably exceeds PROPOSAL's "1K-note
dump" target.

---

## Per-sub-phase scaffolding

Every γ.4.x sub-phase follows the same pattern:

1. ETL: extract verses from the PD source (NPNF / Charles /
   Payne Smith). Format: source-text → paraphrased summary
   (~150-300 words) → full attribution string.
2. Append entries to
   `content/sources/ethiopian_commentaries.json` (preserves the
   existing schema; no kinds.yaml change).
3. Add seed-coverage tests pinning the new entries to
   `tests/test_ethiopian_gamma4.py`'s `TestGamma4Coverage`.
4. CHANGELOG entry naming the verse range + source-volume +
   entry count.

The detector + loader + kind + tradition wiring are all in
place from γ.4. No code change required for γ.4.1-γ.4.6 — pure
content expansion.

---

## Cost / risk

**Effort estimate:** ~1 session per sub-phase × 6 = ~6 sessions
total to hit the 1K-note PROPOSAL target.

**Risk:** content quality. Paraphrased summaries are AI-assisted
(this addendum's style is the target). A future contributor
should:

- Sample-audit ~10% of each batch by reading the original NPNF
  passage and checking the summary faithfully represents the
  Father's argument.
- Flag any summary that adds modern theological positions the
  Father didn't hold — Tewahedo readers will detect
  imposed-Augustinian-frame artifacts.

**Buyer-facing claim:** the corpus is "AI-assisted summary of
PD sources" — not "verbatim PD text". Pin this in the customer-
facing description so γ.4.x summaries are evaluated correctly.

---

## Activation criteria

γ.4.x sub-phases ship when:

- Publisher confirms the v1.x uniqueness angle is the
  Tewahedo direction (γ.4 is one of two shipped uniqueness
  angles — ψ.37 time-travel is the other).
- Or a buyer-facing milestone (e.g. submitting the
  ethiopian-tewahedo edition to a specific retail channel)
  needs a deeper corpus.

Until then, γ.4's seed (12 entries) is enough to demonstrate
the differentiator; γ.4.x is the realization of the claim.
