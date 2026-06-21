# Copyright & Attribution

Single source of truth for the legal and intellectual provenance of
every component in this work. Updated whenever a new source is
incorporated.

---

## 1. Original Editorial Work — Copyright, All Rights Reserved

**Copyright (c) 2026 Bogdan Zorlescu. All rights reserved.** See `LICENSE`
for the full terms.

The following original components are the copyrighted property of Bogdan
Zorlescu. They may not be copied, reproduced, distributed, published,
modified, sold, sublicensed, or used to create derivative works, in whole
or in part, without prior written permission (excepting brief quotations
and other uses permitted by applicable copyright law):

| Component | Description | Year | Status |
|---|---|---|---|
| Editorial notes | 91,555 attributed annotations across 15 categories / 72 kinds | 2026 | © Bogdan Zorlescu — all rights reserved |
| Cross-canon parallels | Selection, framing, theological synthesis | 2026 | © Bogdan Zorlescu — all rights reserved |
| Apparatus structure | 72-kind taxonomy, edition-filtering rules | 2026 | © Bogdan Zorlescu — all rights reserved |
| Per-edition selection | Which sub-kinds appear in each edition build | 2026 | © Bogdan Zorlescu — all rights reserved |
| Introduction matter | Per-book introductions, canon explanations | 2026 | © Bogdan Zorlescu — all rights reserved |
| Navigation & layout | TOC structure, ch-anchor scheme, popover design | 2026 | © Bogdan Zorlescu — all rights reserved |
| Code platform | scripts/, build pipeline | 2026 | © Bogdan Zorlescu — all rights reserved |

Even where a note distills public-domain commentary, the selection,
arrangement, and expression are original editorial work and carry
copyright. For permission requests, contact the copyright holder at
gringo.boggy@yhwhyaway.com.

---

## 2. Public-Domain Sources (Incorporated)

These were already in the public domain before incorporation and remain
so; they are reused here, and the copyright above does NOT (and cannot)
restrict them — anyone may use these underlying sources independently.

### 2.1 Biblical text

**World English Bible (WEB)**
- Author/translator: Rainbow Missions, Inc.
- First published: 1997 (revised continuously through 2020)
- Public-domain status: Explicitly dedicated to the public domain by
  the rights holder.
- Source: https://worldenglish.bible/
- Use in this work: Base text for all 87 books; verse-level structure
  preserved.

### 2.2 Hebrew & Greek lexicons

**Strong's Exhaustive Concordance of the Bible — Hebrew & Greek Lexicons**
- Author: James Strong (1822–1894)
- First published: 1890
- Public-domain status: Public domain in the United States and EU
  (>95 years since author's death; published before 1929).
- Source: Standard PD JSON exports at `content/sources/strongs_hebrew.json`
  and `content/sources/strongs_greek.json`.
- Use in this work: `lang-hebrew` / `lang-greek` word-study notes drawing
  on Strong's numbers, transliteration, and gloss definitions.

### 2.3 Cross-references

**Treasury of Scripture Knowledge (TSK)**
- Author: R. A. Torrey (1856–1928), original compilation 1834
- Public-domain status: Public domain in the United States and EU
  (>95 years since author's death).
- Source: Standard PD digitisation at `content/sources/tsk_xrefs.json`.
- Use in this work: Cross-canon parallel-passage suggestions powering
  `parallel`-kind notes.

### 2.4 Reference works (topical / dictionary)

**Nave's Topical Bible** (Orville J. Nave, 1896) and **Easton's Bible
Dictionary** (M. G. Easton, 1893) — both public domain by age; rebuilt
from clean CCEL digitisations (`content/sources/naves_ccel_source.txt`,
`content/sources/eastons_ccel_source.txt`). Power the `topic-nave` and
`dict-easton` notes.

### 2.5 Verse-popup translations (originals)

Each is public domain by age and/or its own dedication; per-source
provenance (publisher, edition date, license, fetch date) is recorded in
`content/translations/<id>/_meta.yaml`:

- **Douay-Rheims** (Challoner revision) & **Clementine Vulgate** — PD by age.
- **JPS Tanakh, 1917** — PD (US, pre-1929).
- **Van Dyck Arabic, 1865** — PD by age.
- **Westminster Leningrad Codex** (OpenScriptures morphhb) — PD/CC dedication.
- **Swete Septuagint, 1930** & **Robinson-Pierpont Byzantine Majority
  Text** (Unlicense / PD) — PD by age / dedication.

### 2.6 Patristic / classical commentary (cited where used)

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
copyrighted translation or commentary. Only public-domain sources are
ingested. This is enforced editorially; see
`scripts/validate_attribution.py` for the technical check.

---

## 5. Per-Edition Notice (for inclusion in EPUB front matter)

Each edition's front matter should display:

> **The [edition name]**
>
> Compiled and annotated by **Bogdan Zorlescu**.
> Editorial apparatus, selection, arrangement, and code:
> © 2026 Bogdan Zorlescu. All rights reserved.
>
> Biblical text: World English Bible (Public Domain).
> Hebrew/Greek lexicons: Strong's Concordance, James Strong, 1890 (PD).
> Cross-references: Treasury of Scripture Knowledge, R. A. Torrey,
> 1834 (PD).
>
> The underlying biblical texts and lexicons are in the public domain;
> the original editorial work is copyrighted. See LICENSE.

---

## 6. Reporting

If you believe this work incorporates copyrighted material that is not in
the public domain, or wish to request permission to reuse the original
copyrighted work, contact the copyright holder at gringo.boggy@yhwhyaway.com.
