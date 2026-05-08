# v28+ Planning — two open questions

_2026-05-06. Reference doc, not commitment. Read before next session._

---

## Q1. Do we still need the full Diamond tier?

**No. The pivot reshuffled priority.** Of the ~16 platinum/diamond/micro
tools brainstormed pre-pivot, only 4 still matter for the multi-SKU
commercial release. The rest are skip-or-defer.

### Still matters (commercial release blockers)

| Tool | Why it's critical now |
|---|---|
| **ONIX 3.0 export per edition** | 5 ISBNs × 5 retailer feeds. Without this, you can't list on Ingram, Amazon KDP, Apple Books at scale. Was "nice to have" pre-pivot; now it's the distribution moat. |
| **ACE accessibility wrapper** | Libraries are the natural channel for the Ethiopian Tewahedo edition (seminaries, Orthodox theological schools). Library acquisitions require ACE / WCAG certification. |
| **Font subsetting** | Hebrew + Greek fonts add 1–3 MB; subsetting cuts ~80%. With 5 editions × multiple retailer formats, this matters at scale. Single-digit hours of work. |
| **Reproducible build** | Commercial trust. "Same input → identical bytes" is checkable by retailers and reviewers. Cheap to add. |

### Skip / defer

- Cross-reader visual regression (epubcheck already catches the worst)
- Print PDF (not a confirmed market — wait for demand signal)
- Reading analytics (only if you ship a web-app SKU later)
- AI substantive scoring (`note_quality.py` covers the editorial floor)
- i18n_audit, css_purge, license_embed, wc, sha256, orphans, info, linearity, changelog — low value at current scope

### What actually outranks the diamond tier

1. **`prospect.py`** — discovery tool (the v28 priority). Multiplies your authoring speed.
2. **Tradition-specific note authoring** — the multi-SKU platform produces identical EPUBs until you write notes with sub-kinds. 20–30 sub-kind notes is enough to make the differential output visible.
3. **Per-edition CSS** — sub-kind colour styling so the new 14 categories are visually distinguishable.

**Recommended v28 sequence:** prospect.py → 30 sub-kind notes → ONIX export → ACE → font subsetting → reproducible build. The diamond items slot in after v28 ships.

---

## Q2. Auto-population from online sources — the discovery → fetch architecture

**Yes, architectable.** It's `prospect.py` evolved: detectors don't just
*flag* opportunities, they *fetch and pre-fill* note bodies from
public-domain sources. You review and promote. No manual search.

### Three-stage pipeline

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│  Detector   │ →  │   Fetcher    │ →  │ Candidate notes │ → review → corpus
│ (per kind)  │    │ (per source) │    │   (YAML draft)  │
└─────────────┘    └──────────────┘    └─────────────────┘
```

### Public-domain source matrix (this is the real moat)

| Kind | Source | Status |
|---|---|---|
| `lang-hebrew` | Strong's Hebrew + BDB lexicon | PD, fully digitized |
| `lang-greek` | Strong's Greek + Thayer's lexicon | PD, fully digitized |
| `xref-citation`, `xref-allusion` | Treasury of Scripture Knowledge (TSK) | PD, ~500K cross-refs |
| `comm-patristic` | Catena Aurea, ANF/NPNF series | PD (text + 19c translation) |
| `comm-rabbinic` | Sefaria public-domain corpus | CC license, machine-readable |
| `text-dss` | OakTree DSS Bible variants | partial PD, some licensed |
| `text-lxx` | Rahlfs LXX + Brenton parallel | PD |
| `hist-geographic` | Wikipedia, JewishEncyclopedia.com (1906) | PD / CC |
| `hist-person` | Catholic Encyclopedia 1913 + JE 1906 | PD |
| `hist-ane` | COS, ANET → out, but ABD partial | mixed (use carefully) |
| `compare-pseudepigrapha` | Charles 1913 edition (1 Enoch, Jubilees) | PD |
| `lang-geez` | UNESCO Tewahedo lexicon project | partial PD |

**The key insight:** modern scholarship is copyrighted, but the
*foundational reference works* — the things a study Bible actually
needs to cite — are mostly 19c–early 20c and PD. You don't need
contemporary sources for a credible study apparatus.

### Implementation sketch (NOT this session)

Three new scripts and one new content directory:

```
content/sources/                    ← cached PD reference corpora
    strongs_hebrew.json             ← parsed lexicon, ~1.5 MB
    strongs_greek.json
    bdb.json
    tsk.json                        ← cross-ref index
    catena_aurea.json
    ...

scripts/fetch_sources.py            ← one-time: download + parse PD sources
scripts/prospect.py                 ← per-verse: detect + fetch candidates
scripts/promote.py                  ← review queue → real note
```

Per-verse prospect output (YAML draft):

```yaml
- verse: gen.3.15
  candidates:
    - kind: dist-mariological
      anchor: "He will bruise your head"
      source: "Catena Aurea (Aquinas, c. 1265, PD)"
      draft: |
        Aquinas compiles patristic readings of the protevangelium...
      confidence: 0.92
    - kind: lang-hebrew
      anchor: "bruise"
      source: "BDB (1907, PD)"
      draft: |
        שׁוּף (shuph). Used only here and Job 9:17, Ps 139:11 — meaning contested...
      confidence: 0.88
```

### The legal red lines

- **Never fetch from copyrighted commentaries**, even via paraphrase. Hard rule.
- **Always cite the PD source** in the candidate. The user can rewrite
  in their own voice but the provenance trail must exist.
- **PD translations** of older works are themselves PD (ANF/NPNF, Charles
  1913, Brenton LXX). Modern translations of the same originals are
  copyrighted — don't use them.
- **CC-BY-SA sources** (Sefaria, Wikipedia) require attribution but no
  paraphrasing requirement.

### Estimated build effort

- `fetch_sources.py` (one-time corpus build): 1 session (~6 hours real time)
- `prospect.py` v2 with fetchers: 1–2 sessions
- `promote.py` review queue: 1 session
- Total: ~3–4 sessions to a working system that turns "what notes should
  I write?" into a daily review queue of 50–200 pre-drafted candidates.

**Once built, your authoring rate goes from ~10 notes/hour (manual) to
~50–100 notes/hour (review and refine).** The 1,371 existing notes
become the baseline; you're targeting 8,000–15,000 for a fully-amplified
study Bible.

---

## TL;DR for next session

1. **Diamond tier:** trim to 4 items (ONIX, ACE, font subset, reproducible build), defer or kill the rest.
2. **Auto-population:** yes, fully architectable. Built on PD reference corpora — Strong's, BDB, TSK, Catena Aurea, ANF, JE, Charles 1913. Three new scripts. ~3–4 sessions of build effort. Multiplies authoring throughput 5–10×.

Both answers point to the same v28 priority: **build prospect.py with fetcher hooks before writing more notes.** The platform is ready; the bottleneck is content, and content is what fetchers solve.
