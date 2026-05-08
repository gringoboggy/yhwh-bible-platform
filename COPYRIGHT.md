# Copyright & Attribution

Single source of truth for the legal and intellectual provenance of
every component in this work. Updated whenever a new source is
incorporated.

---

## 1. Original Editorial Work

**Copyright (c) 2026 TODO_COPYRIGHT_HOLDER. All rights reserved (or as
otherwise specified in `LICENSE`).**

The following are original to this project and protected by copyright:

| Component | Description | Year | Status |
|---|---|---|---|
| Editorial notes | 1,371 attributed annotations across 14 categories | 2026 | © project |
| Cross-canon parallels | Selection, framing, theological synthesis | 2026 | © project |
| Apparatus structure | 63-kind taxonomy, edition-filtering rules | 2026 | © project |
| Per-edition selection | Which sub-kinds appear in each retail SKU | 2026 | © project |
| Introduction matter | Per-book introductions, canon explanations | 2026 | © project |
| Navigation & layout | TOC structure, ch-anchor scheme, popover design | 2026 | © project |
| Code platform | scripts/, content/onix.py, build pipeline | 2026 | © project |
| ONIX metadata | Per-edition retailer descriptions, BISAC selections | 2026 | © project |

Even where a note paraphrases or distills public-domain commentary,
the SELECTION, ARRANGEMENT, and EXPRESSION are original editorial work
and carry copyright. Quoting more than ~50 words verbatim from any
single editorial note for commercial purposes requires written
permission.

---

## 2. Public-Domain Sources (Incorporated)

### 2.1 Biblical text

**World English Bible (WEB)**
- Author/translator: Rainbow Missions, Inc.
- First published: 1997 (revised continuously through 2020)
- Public-domain status: Explicitly dedicated to the public domain by
  the rights holder.
- Source: https://worldenglish.bible/
- Use in this work: Base text for all 87 books; verse-level structure
  preserved.

### 2.2 Hebrew lexicon

**Strong's Exhaustive Concordance of the Bible — Hebrew Lexicon**
- Author: James Strong (1822–1894)
- First published: 1890
- Public-domain status: Public domain in the United States and EU
  (>95 years since author's death; published before 1929).
- Source: Multiple PD digitisations; project uses the standard JSON
  export at `content/sources/strongs_hebrew.json`.
- Use in this work: Hebrew-language `lang-hebrew` notes drawing on
  Strong's numbers, transliteration, gloss definitions.

### 2.3 Cross-references

**Treasury of Scripture Knowledge (TSK)**
- Author: R. A. Torrey (1856–1928), original compilation 1834
- Public-domain status: Public domain in the United States and EU
  (>95 years since author's death).
- Source: Standard PD digitisation at `content/sources/tsk_xrefs.json`.
- Use in this work: Cross-canon parallel-passage suggestions powering
  `parallel`-kind notes.

### 2.4 Patristic / classical commentary (cited where used)

When notes draw on PD-era commentary (Augustine, Chrysostom, Aquinas,
Jerome, Calvin, Luther, etc.), provenance is captured per-note in the
attribution stack and validated by `scripts/validate_attribution.py`.
All cited authorities died >95 years ago and are in the public domain.

---

## 3. Trademarks (None Asserted)

This project asserts no trademarks. "Ethiopian Tewahedo" refers to the
Ethiopian Orthodox Tewahedo Church and its canon — used descriptively,
not as a trademark.

---

## 4. Modern Translations & Commentary (Excluded)

The project deliberately does NOT incorporate any modern (post-1929)
copyrighted translation or commentary. If a future edition needs to
quote modern scholarship:

- Quotations must be ≤300 words from any single source per edition.
- Each quotation must carry standard SBL-style attribution.
- Bulk inclusion (>300 words) requires a paid licence from the
  rights holder.

This is enforced editorially. See `scripts/validate_attribution.py`
for the technical check.

---

## 5. Per-Edition Copyright Notice (for inclusion in EPUB front matter)

Each edition's front matter should display:

> **The [edition name]**
>
> Compiled and annotated by **TODO_CONTRIBUTOR_NAME**.
>
> Biblical text: World English Bible (Public Domain).
> Hebrew lexicon: Strong's Hebrew Concordance, James Strong, 1890 (PD).
> Cross-references: Treasury of Scripture Knowledge, R. A. Torrey,
> 1834 (PD).
>
> Editorial apparatus, selection, and arrangement: © 2026 TODO_COPYRIGHT_HOLDER.
> All rights reserved.
>
> ISBN: TODO_ISBN_13
> First published: TODO_PUBLICATION_DATE.
> Published by TODO_PUBLISHER_NAME.

---

## 6. Reporting Copyright Concerns

If you believe this work incorporates copyrighted material without
proper licence, contact: TODO_COPYRIGHT_CONTACT_EMAIL.
