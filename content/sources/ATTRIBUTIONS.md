# Source attributions

This directory caches public-domain reference works used by `scripts/prospect.py` to draft candidate notes. Every fetched source is named below with its licence; the cached files are redistributable under those terms.

The source list is declarative — see `content/sources/_fetchers.json` for the URL + parser-kind table and `scripts/core/fetcher_config.py` for the loader/schema.

## Strong's Hebrew Dictionary

Strong's Exhaustive Concordance of the Bible, James Strong (1894). Public domain. Digital edition by Open Scriptures, CC-BY-SA.

Source URL: <https://raw.githubusercontent.com/openscriptures/strongs/master/hebrew/strongs-hebrew-dictionary.js>

## Strong's Greek Dictionary

Strong's Exhaustive Concordance of the Bible, James Strong (1894). Public domain. Digital edition by Open Scriptures, CC-BY-SA.

Source URL: <https://raw.githubusercontent.com/openscriptures/strongs/master/greek/strongs-greek-dictionary.js>

## Treasury of Scripture Knowledge

Treasury of Scripture Knowledge (Canne, Browne, Blayney, Scott et al., 1830s). Public domain. Digital edition by openbible.info, CC-BY 4.0.

Source URL: <https://a.openbible.info/data/cross-references.zip>

## Nave's Topical Bible

Nave's Topical Bible, Orville J. Nave (1896). Public domain (US copyright lapsed; author died 1917, work first published 1896).

Source URLs (tried in order):

- <https://raw.githubusercontent.com/scrollmapper/bible_databases_extras/main/naves/naves.json> *(parser: `json-topic-to-refs`)*
- <https://raw.githubusercontent.com/openbibleinfo/Topical-Bible/main/naves.json> *(parser: `json-topic-to-refs`)*
- <https://a.openbible.info/data/topic-votes.txt.zip> *(parser: `openbible-topics-tsv`)*
- <https://www.ccel.org/n/nave/topical/topical.txt> *(parser: `ccel-text`)*

