# Scope addendum — Audio-augmented EPUBs via LibriVox (Phase ρ.1)

**Added:** 2026-05-08, after σ.3 shipped.
**Origin:** strategic-direction question from the user — "anything to
make it unique or ultra awesome?" Audio-augmented EPUBs were the
second-priority recommendation; user added it to active scope alongside
ψ.8.

## What this phase does

EPUB 3 has native `<audio>` and SMIL (synchronized media) support.
Almost no Bible publishers actually use it. ρ.1 lets a publisher attach
public-domain audio recordings to an edition so the resulting `.epub`
file is both a study Bible *and* an audiobook in one package.
LibriVox's catalog includes complete public-domain readings of the
King James Bible (and individual books in several other PD English
translations) — those become the content stream for the first cut.

The publisher experience: tick a box on `/customize`, pick a voice
from the LibriVox catalog, click BUILD. The resulting EPUB plays
chapter audio with a play/pause control next to each chapter heading,
and (eventually) supports SMIL highlight-along-with-narration for
accessibility-grade media overlays.

## Why this is distinctive

- **Accessibility.** Visually impaired or low-literacy buyers get a
  product that works as audio out of the box. No separate "Audio Bible
  app" required.
- **Single-file delivery.** Buyers don't juggle an EPUB *and* a
  podcast feed — it's all in one `.epub`. Critical for offline use
  (rural / mission / monastic contexts the platform's editions
  target).
- **Audio-narration coverage of *deuterocanonical* and *Tewahedo* books.**
  This is a real gap in commercial Bible audio. LibriVox has many of
  these recorded; commercial audiobook publishers rarely do. ρ.1
  positions the Tewahedo flagship edition as the single most complete
  audio Bible product at any price point.

## Source — LibriVox PD recordings

LibriVox publishes audio under a public-domain dedication. The
catalog is browsable at `librivox.org`; structured metadata is at
`librivox.org/api/feed/audiobooks`.

### Phase ρ.1 — initial readers

Initial cut targets KJV (the platform's existing default English
translation) plus Apocrypha:

| reader / set                                      | books covered                  |
|---------------------------------------------------|--------------------------------|
| KJV — multiple-reader (catalogued)                | OT 39 + NT 27 = 66 books       |
| KJV Apocrypha — single-reader sets (varies)       | Tobit, Judith, 1-2 Maccabees,  |
|                                                   | Wisdom, Sirach, Baruch, etc.   |
| Brenton LXX (Greek OT in English) — partial       | OT books where reader exists   |

Tewahedo-specific PD audio (Enoch, Jubilees, Meqabyan I-III) is sparse
in LibriVox — those slots stay silent in the first cut, with TTS as
a future fallback (ρ.2, deferred).

### Pipeline shape

Mirrors the χ-cluster pipeline pattern (per CLAUDE_PROJECT_RULES §9
"Add a new corpus-growth phase"):

```
LibriVox feed     →  fetcher              →  cached MP3s (or OGG)     →  build-time embed
(librivox.org/        scripts/fetch_           content/audio/<set>/      build_edition.py
 api/feed/...)        librivox.py              <book>_ch_<NNN>.mp3       audio_embed pass
```

1. **`scripts/core/audio.py`** — new module with `LibriVoxFetcher` and
   `AudioStorage` classes. Storage path helper:
   `storage_path_for_audio(edition, book, chapter)` mirrors
   `covers.storage_path_for_book` (per CLAUDE_PROJECT_RULES §9 binary-
   asset pattern).
2. **`scripts/fetch_librivox.py`** — new driver. Reads
   `content/audio/_sets.json` (declarative set list, like υ.7's
   `_fetchers.json`) and downloads each set's MP3s into
   `content/audio/<set_id>/<book>_ch_<NNN>.mp3`. Validates with the
   §9 magic-bytes check and the file format whitelist.
3. **`scripts/build_edition.py audio_embed pass`** — between the filter
   pass and packaging, adds `<audio>` elements next to chapter headings
   in the rendered HTML. Only fires when the edition's
   `audio_set_default` field is set.

## Schema change — additive, no-op when unset

```yaml
# editions.yaml — new fields, all optional
ethiopian_tewahedo:
  ...
  audio_set_default: "kjv-multi-reader"   # ρ.1 — references a set in _sets.json
  audio_per_book: []                      # ρ.1 — flat list of "book=set" overrides
                                          # (like popup_languages_per_book — ν.2.7)
```

Defaults preserve byte-identical builds for editions that don't opt in
(per CLAUDE_PROJECT_RULES §7.2 schema-migration rule). `audio_per_book`
uses the same flat-string encoding as popup_languages_per_book per the
project's "no nested mappings in YAML" pattern.

## UI — /customize gets an Audio card

```
☐ Audio narration (LibriVox PD recordings)

  Default voice for this edition:
  ◉ KJV — multiple readers (66 books, ~120 hrs)
  ○ KJV — single reader, M. Smith (66 books, ~95 hrs)
  ○ KJV Apocrypha — single reader (10 books, ~22 hrs)
  ○ None (no audio in this edition)

  ☐ Per-book overrides (advanced)
    [matrix UI like ν.2.7's per-book languages]

  Note: enabling audio adds ~50-200 MB per book to the EPUB file.
        Storage / bandwidth implication is real.
```

The size warning is rendered live based on the user's selection.

## Tests

- Schema round-trip: `audio_set_default` saved + loaded preserves
  value; `audio_per_book` round-trips through encode/decode pair.
- Default behavior: edition without audio fields ships byte-identical
  to pre-ρ.1 builds (the §7.2 no-op rule).
- Build pipeline: edition with audio enabled produces an EPUB with
  exactly N `<audio>` elements (one per chapter); audio source paths
  resolve correctly from the EPUB's relative roots.
- Validator: validates the audio set exists in `_sets.json`; rejects
  unknown set IDs.
- Storage path helper: `storage_path_for_audio` is canonical;
  duplicating it elsewhere is the anti-pattern that triggered codifying
  the rule.
- File-size estimator: the live size estimate in /customize matches
  actual EPUB output within ±5%.

## Sub-phasing

```
ρ.1.0  Schema + audio module       scripts/core/audio.py +
                                     editions.yaml fields
ρ.1.1  LibriVox fetcher             scripts/fetch_librivox.py +
                                     content/audio/_sets.json
ρ.1.2  Build pipeline integration   audio_embed pass + tests
ρ.1.3  Customize UI                 Audio card + size estimator
ρ.1.4  Per-book overrides           encoder/decoder pair
ρ.1.5  Wizard step                  buyer demo asks "include audio?"
```

ρ.1.0 + ρ.1.1 ship as one batch (the schema is dead without the data
to back it). ρ.1.2 + ρ.1.3 ship as a second batch. ρ.1.4 + ρ.1.5 are
follow-ons.

## Tradeoffs / known limitations

- **EPUB file size.** A KJV-only audio edition is ~1-2 GB. With
  Apocrypha + a few extra translations, 3-5 GB. Many e-readers
  (older Kindles, low-end Android tablets) hit hard limits or load
  slowly. Mitigated by (a) opt-in per edition, (b) clear size warning
  in UI, (c) per-book overrides so a publisher can ship audio for
  Psalms-only if size matters.
- **Reader app compatibility.** Apple Books, Thorium Reader, Calibre,
  Kobo — full `<audio>` support. Older Kindle (pre-2024 firmware) and
  some web readers — silent fallback to text-only. EPUB is graceful
  here: the `<audio>` element renders as nothing on unsupported
  readers, so the book still works as a study Bible.
- **No SMIL highlight-along-with-narration in ρ.1.** That's a separate
  phase (ρ.2 or ρ.3) — building SMIL files requires audio-text
  alignment, which is a research project on its own (forced alignment
  with `aeneas` or similar; PD-only stack so the cost stays at zero).
- **Audio quality varies by reader.** LibriVox is volunteer-recorded;
  some chapters are pristine, some are amateur. The publisher chooses
  per voice/set, not per chapter. ρ.1 doesn't try to filter quality —
  the catalog browser surfaces reader names and lets the publisher
  preview before committing.
- **Bandwidth concern for cloud-hosted future.** This whole feature
  assumes EPUBs ship as monolithic files. If the platform later adds
  cloud streaming (post-v1.0, out of current scope), audio gets pulled
  from a CDN rather than embedded — but that's a different schema and
  not blocking for ρ.1 as defined.

## Future audio phases (ρ.2+, deferred)

- **ρ.2** SMIL synchronized text+audio (highlight-along-with-narration).
- **ρ.3** TTS fallback for PD-recording-sparse books (Enoch, Jubilees,
  Meqabyan, Tewahedo-only material).
- **ρ.4** Multi-translation audio (each translation gets its own reader
  set; audio swaps when translation toggles).
- **ρ.5** Per-language audio sets (Spanish, French, etc. as sources
  emerge in LibriVox).

These are out of scope for v1.0; ρ.1 alone is enough to ship the
distinctive audio-Bible feature.
