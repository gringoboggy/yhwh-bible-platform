# Source attributions

This directory caches public-domain reference works used by `scripts/prospect.py` to draft candidate notes. Every fetched source is named below with its licence; the cached files are redistributable under those terms.

The source list is declarative — see `content/sources/_fetchers.json` for the URL + parser-kind table and `scripts/core/fetcher_config.py` for the loader/schema.

## Images & fonts (non-text assets — see also)

The visual assets are documented next to the files they describe, not in this
directory. Cross-referenced here so this file is the single attribution index:

- **Cover templates** (25 designs) — the publisher's own Midjourney-generated
  art + a programmatic hue-shift pipeline: `content/covers/templates/README.md`.
- **Per-book cover art** (the publisher's curated 66-cover set):
  `content/covers/_book_defaults/README.md`.
- **Embedded fonts** — policy is SIL Open Font License 1.1 only:
  `content/assets/fonts/LICENSES.md` (+ `README.md`).

The program itself is © 2026 Bogdan Zorlescu, all rights reserved (`LICENSE`);
the cover art is the publisher's own generated work. The root `README.md` carries
the consolidated licensing overview.

## Strong's Hebrew Dictionary

Strong's Exhaustive Concordance of the Bible, James Strong (1894). Public domain. Digital edition by Open Scriptures, CC-BY-SA.

Source URL: <https://archive.org/download/openscriptures-strongs-json/strongs-hebrew-dictionary.js>

## Strong's Greek Dictionary

Strong's Exhaustive Concordance of the Bible, James Strong (1894). Public domain. Digital edition by Open Scriptures, CC-BY-SA.

Source URL: <https://archive.org/download/openscriptures-strongs-json/strongs-greek-dictionary.js>

## Treasury of Scripture Knowledge

Treasury of Scripture Knowledge (Canne, Browne, Blayney, Scott et al., 1830s). Public domain. Digital edition by openbible.info, CC-BY 4.0.

Source URL: <https://a.openbible.info/data/cross-references.zip>

## Nave's Topical Bible

Nave's Topical Bible, Orville J. Nave (1896). Public domain (US copyright lapsed; author died 1917, work first published 1896).

Source URLs (tried in order):

- <https://a.openbible.info/data/topic-votes.txt.zip> *(parser: `openbible-topics-tsv`)*
- <https://www.ccel.org/n/nave/topical/topical.txt> *(parser: `ccel-text`)*

---

## Patristic and Tewahedo canonical commentary sources

The sources below feed `content/sources/ethiopian_commentaries.json` and the parallel `catholic_commentaries.json` / `protestant_commentaries.json` / `reformation_commentaries.json` / `rabbinic_commentaries.json` files. Each JSON's `_meta.public_domain_basis` block carries the technical attribution; the entries here are the human-readable cross-source legal-audit registry.

### Cyril of Alexandria — Commentary on the Gospel of St. John

Cyril of Alexandria (d. 444), *Commentary on the Gospel of St. John*. English translation by Philip E. Pusey (vol. I, books I-V) and Thomas Randell (vol. II, books VII-XII), Library of Fathers of the Holy Catholic Church, Oxford: James Parker & Co., 1874-1885. Public domain in the US under the pre-1929 rule (US Copyright Act of 1909, §24; works published before 1929 are in the public domain regardless of translator's death date).

Source URL: <https://archive.org/details/commentaryongosp01cyriuoft> (vol. I) and <https://archive.org/details/commentaryongosp02cyriuoft> (vol. II).

Coverage in corpus: 121 verse-keyed entries on John 1-7 + 11-21 (book code `joh`; see §C2 in dev/AUDIT_2026-05-12-C.md for the `joh`/`jhn` alias note). γ.4.1.A-D shipped 2026-05-12.

### Ephrem the Syrian — Commentary on Genesis (and Hymns on Paradise / Commentary on Psalms)

Ephrem the Syrian (d. 373), *Commentary on Genesis*, *Hymns on Paradise*, and selected *Commentary on Psalms*. English translations in *Nicene and Post-Nicene Fathers, Series II, vol. XIII: Gregory the Great (II), Ephraim Syrus, Aphrahat*, ed. Philip Schaff, John Gwynn et al. (Edinburgh: T&T Clark / New York: Christian Literature Co., 1898). Public domain in the US under the pre-1929 rule (US Copyright Act of 1909, §24).

Source URL: <https://www.ccel.org/ccel/schaff/npnf213.html>

Coverage in corpus: 77 verse-keyed entries on Genesis 1-50 (book code `gen`), Psalm 1 (book code `ps` — see §C2 in dev/AUDIT_2026-05-12-C.md for the `ps`/`psa` alias note), and selected hymns. γ.4.2 + γ.4.2.B shipped 2026-05-12.

### 1 Enoch / Mäṣḥafä Hēnok (Ethiopian canonical text)

*The Book of Enoch* (Ge'ez: *Mäṣḥafä Hēnok*). Canonical only in the Ethiopian Tewahedo and Eritrean Orthodox Churches; preserved as a complete text only in Ge'ez. English translation by R. H. Charles, *The Book of Enoch*, Oxford: Clarendon Press, 1912 (2nd ed., revised; first edition 1893). Public domain in the US under the pre-1929 rule (US Copyright Act of 1909, §24); Charles died in 1931 but the publication date is the controlling factor for US public-domain status.

Source URL: <https://archive.org/details/bookofenoch00char_1>

Coverage in corpus: 192 verse-keyed entries across all six canonical sections — Watchers (chs 1-36), Parables (chs 37-71), Astronomical Book (chs 72-82), Dream Visions (chs 83-84), Animal Apocalypse (chs 85-90), Epistle of Enoch (chs 91-108). γ.4.4 + γ.4.4.B-E shipped 2026-05-12 (Mäṣḥafä Hēnok arc CLOSED).

### Jubilees / Mäṣḥafä Kufāle (Ethiopian canonical text)

*The Book of Jubilees* (Ge'ez: *Mäṣḥafä Kufāle*; "Little Genesis"). Canonical only in the Ethiopian Tewahedo and Eritrean Orthodox Churches; preserved as a complete text only in Ge'ez. English translation by R. H. Charles, *The Book of Jubilees, or the Little Genesis*, London: Adam and Charles Black, 1902 (translated from the Ethiopic; with introduction, notes, and indices). Public domain in the US under the pre-1929 rule (US Copyright Act of 1909, §24).

Source URL: <https://archive.org/details/bookofjubilees0000char>

Coverage in corpus: 200 verse-keyed entries across all narrative sections — Sinai prologue + Creation (chs 1-4), Watchers + Noahide covenant (chs 5-10), Abraham cycle (chs 11-22), Decline + eschatology (ch 23), Jacob cycle (chs 24-36), Joseph + Egypt-Exodus-Passover-Sabbath finale (chs 37-50). γ.4.5 + γ.4.5.B-E shipped 2026-05-12 (Mäṣḥafä Kufāle arc CLOSED).
