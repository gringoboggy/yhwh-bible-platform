# v28 ROADMAP — detailed build plan

_Continues `v28_PLANNING.md`. This doc converts the planning answers into
a buildable spec. Scoped to ~3–4 working sessions._

---

## Current state (after v27)

- 31 scripts in `scripts/`, 1,371 source notes across 87 books
- Multi-edition platform shipped — 5 EPUBs build cleanly per run
- Foundation taxonomy: 14 categories, 59 kinds, 5 edition profiles
- Bottleneck: **content**, specifically tradition-specific notes that
  exercise the new sub-kinds. Until those exist, all 5 edition EPUBs are
  byte-near-identical.

The single highest-leverage v28 build is therefore not another tool —
it's the **authoring multiplier** (prospect.py + fetchers) plus enough
content to prove the platform delivers differentiated SKUs.

---

## v28 split into three phases

| Phase | Scope | Estimated sessions |
|---|---|---|
| **28a** | prospect.py + fetcher infrastructure + 3 PD source corpora | 2 sessions |
| **28b** | Content amplification — author 200–500 sub-kind notes via prospect.py review | 1–2 sessions + ongoing |
| **28c** | Commercial release prep — ONIX, font subsetting, ACE, reproducible build | 1–2 sessions |

Phases are sequenced because 28a unlocks 28b, and 28b should land before
28c (no point ONIX-listing editions that aren't materially differentiated).

---

## Phase 28a — prospect.py + fetcher infrastructure

### Goal

Turn the question "what notes should I add to Genesis 3?" into a
machine-generated review queue of 50–200 candidate notes per chapter,
each with kind, anchor, draft body, source citation, and confidence
score. User reviews and one-click-promotes to real notes.

### Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │              prospect.py                       │
                  │                                                │
verse text  ────► │  ┌────────────┐    ┌────────────┐             │
                  │  │ Detectors  │ ──►│  Fetchers   │             │
                  │  │ (per kind) │    │ (per source)│             │
                  │  └────────────┘    └────────────┘             │
                  │         │                  │                   │
                  │         └────────┬─────────┘                   │
                  │                  ▼                             │
                  │          Candidate notes ──► YAML draft file   │
                  └──────────────────────────────────────────────┘
                                    │
                                    ▼
                  ┌──────────────────────────────────────────────┐
                  │          promote.py review CLI                │
                  │   for each candidate: skip | edit | promote   │
                  └──────────────────────────────────────────────┘
                                    │
                                    ▼
                              content/notes/<book>.py
```

### New files

```
content/sources/                            # PD reference corpora cache
  strongs_hebrew.json                       # ~1.5 MB, full lexicon
  strongs_greek.json
  tsk_xrefs.json                            # ~3 MB, ~500K cross-refs
  README.md                                 # license attribution per source

content/candidates/                         # prospect.py output, gitignored
  gen_ch_3.candidates.yaml
  exo_ch_12.candidates.yaml
  ...

scripts/fetch_sources.py                    # one-time corpus builder (~250 LOC)
scripts/prospect.py                         # candidate generator (~450 LOC)
scripts/promote.py                          # review CLI (~300 LOC)
scripts/core/sources.py                     # fetcher base class + registry
scripts/core/detectors.py                   # detector base class + registry
```

### Source priority (for v28a, just 3)

| Order | Source | Covers | License | Effort to parse |
|---|---|---|---|---|
| 1 | **Strong's Hebrew + Greek lexicon** | `lang-hebrew`, `lang-greek` | PD (1890) | low — clean JSON exists |
| 2 | **Treasury of Scripture Knowledge (TSK)** | `xref-citation`, `xref-allusion`, `parallel` | PD (1830s) | low — clean JSON exists |
| 3 | **Charles 1913 edition (1 Enoch, Jubilees)** | `compare-pseudepigrapha` | PD (1913) | medium — text on archive.org, needs OCR cleanup or manual chapter splits |

Defer to 28a-extended (post-MVP):
- Catena Aurea (patristic) — value/effort ratio is great but parser complexity high
- BDB Hebrew Lexicon — mostly redundant with Strong's for note-prompting
- ANF/NPNF series — ~38 volumes, big undertaking, defer to its own session
- Sefaria CC corpus — JSON-clean but rabbinic-heavy; consider after Catena

### Detector list (~10 detectors)

Each detector takes a verse range and returns `[CandidateNote, ...]`:

| Detector | Triggers on | Suggested kind | Confidence basis |
|---|---|---|---|
| `HebrewWordDetector` | Untransliterated Hebrew word OR known proper name | `lang-hebrew` | Strong's frequency + verse importance |
| `GreekWordDetector` | NT verse with words above frequency threshold | `lang-greek` | Strong's frequency |
| `PlaceDetector` | Capitalized term in biblical-place gazetteer | `hist-geographic` | First occurrence ranks highest |
| `PersonDetector` | Capitalized term in biblical-name list | `hist-person` | First occurrence ranks highest |
| `CitationDetector` | TSK marks this verse as cited by another | `xref-citation` | TSK cross-ref strength |
| `AllusionDetector` | TSK weak link or echoing wordlist | `xref-allusion` | TSK + lexical overlap |
| `VariantDetector` | DSS / LXX divergence flagged in apparatus | `text-dss` or `text-lxx` | Apparatus reliability |
| `EnochParallelDetector` | Verse with thematic match in 1 Enoch / Jubilees | `compare-pseudepigrapha` | Charles 1913 cross-index |
| `DifficultyDetector` | Verse in known-hard list (Yale Divinity, etc.) | `apol-difficulty` or `modern-ethics` | Hard-list inclusion |
| `EthicsDetector` | Verse touching war / slavery / sexuality / gender | `modern-ethics` | Keyword + context window |

### Candidate YAML schema

```yaml
verse: gen.3.15
generated_at: 2026-05-XX
candidates:
  - id: gen315-001                                # stable for review-queue idempotency
    kind: lang-hebrew
    anchor: "bruise"                              # text in the verse to anchor on
    confidence: 0.88
    source:
      name: "Strong's H7779"
      attribution: "Strong's Exhaustive Concordance, 1890 (PD)"
      url: "https://..."                          # optional, for review
    draft_title: "Hebrew"
    draft_label: "Hebrew."
    draft_body: |
      <strong>Shuph (שׁוּף).</strong> Used only here, Job 9:17, and
      Psalm 139:11. Meaning contested between "to bruise / crush"
      (LXX τηρέω, Vulgate conteret) and "to lie in wait for"
      (some rabbinic readers). The translation choice...
    notes_for_reviewer: |
      Strong's gives both senses; the entry has no theological
      framing. You'll want to add the protevangelium reading.
```

### prospect.py CLI

```bash
# Generate candidates for one chapter:
python3 scripts/prospect.py gen 3
    → writes content/candidates/gen_ch_3.candidates.yaml

# Generate for whole book, all chapters:
python3 scripts/prospect.py gen --all-chapters

# Re-generate skipping already-promoted candidates:
python3 scripts/prospect.py gen 3 --skip-promoted

# Limit to specific kinds:
python3 scripts/prospect.py gen 3 --only lang-hebrew,xref-citation

# Confidence floor:
python3 scripts/prospect.py gen 3 --min-confidence 0.7
```

### promote.py review CLI

```bash
python3 scripts/promote.py gen 3
    → walks candidates one by one:
       [1/47] gen 3:15 lang-hebrew (conf 0.88)
              "Shuph (שׁוּף). Used only here..."
              Source: Strong's H7779
       [s]kip [e]dit [p]romote [q]uit > _
```

Promote action: writes the note tuple to the right place in
`content/notes/<book>.py`, updates the source-attribution sidecar,
marks candidate as promoted.

### Definition of done for 28a

1. `fetch_sources.py` populates `content/sources/` with 3 corpora
2. `prospect.py gen 3` produces candidates.yaml with ≥30 candidates
3. `promote.py gen 3` walks the queue and successfully promotes ≥5 to real notes
4. `verify.py` paired count goes from 1354 to 1359 with zero new errors
5. Round-trip with `note_search.py` confirms promoted notes are findable
6. README.md and HANDOFF v28a entry written

---

## Phase 28b — content amplification

### Goal

Author 200–500 sub-kind notes spread across the highest-traffic books,
demonstrating real differential output between editions.

### Authoring targets

Two strategies — pick one:

**Strategy A: Depth-first.** Pick 5 books (gen, exo, mat, joh, rev),
amplify them comprehensively. Each chapter gets 30–50 notes across
multiple sub-kinds. Total: ~1,000 new notes. Commercial value: those
5 books look professional; rest of corpus looks thin.

**Strategy B: Breadth-first.** Add 3–5 sub-kind notes per book across
all 87 books. Total: ~350 new notes. Commercial value: every chapter
has *something* tradition-specific in every edition; no book looks
neglected.

**Recommendation:** Strategy B for initial 28b, then Strategy A on
gen + mat + 1en (the three most-marketable for the Tewahedo edition)
after that.

### Tradition coverage

Each note authored should be tagged with the right sub-kind so that
edition filtering activates. Target distribution per 100 notes:

| Sub-kind | Count | Why |
|---|---|---|
| `comm-ethiopian` | 25 | Tewahedo edition's distinctive content |
| `comm-rabbinic` | 15 | Jewish edition's distinctive content |
| `comm-patristic` | 15 | Catholic / Tewahedo distinctive |
| `dist-mariological` | 10 | Catholic / Tewahedo distinctive |
| `dist-typological` | 10 | Catholic / Reformed common |
| `comm-modern-critical` | 15 | Scholarly edition distinctive |
| `compare-pseudepigrapha` | 10 | Tewahedo + Scholarly distinctive |

After ~100 notes per the above mix, a Reformed EPUB and a Tewahedo
EPUB will have visibly different page counts and content.

### Quality gate

Every promoted note must pass `note_quality.py` checks. The threshold
matters because LLM-fetched drafts can be subtly off-tone; the floor
is "no editorial flags raised."

### Definition of done for 28b

1. ≥200 sub-kind notes promoted via promote.py
2. Per-edition build file-size delta ≥ 5% between most/least-noted edition
3. `dashboard.py` shows balanced sub-kind distribution per category
4. HANDOFF v28b entry written with note counts per sub-kind

---

## Phase 28c — commercial release prep

### Items

| Item | Effort | What it unlocks |
|---|---|---|
| **ONIX 3.0 export per edition** | medium | Listing on Ingram, Apple Books, Amazon KDP, etc. |
| **Font subsetting** | low | 60–80% size reduction; faster downloads on mobile |
| **ACE accessibility wrapper** | medium | Library acquisition (seminaries, theological schools) |
| **Reproducible build** | low | Hash-stable outputs; reviewer trust |
| **Per-edition CSS** | low | Sub-kind colour distinction in the new categories |

### ONIX 3.0 spec

New: `scripts/onix_export.py`. Per edition, emits one ONIX XML file:

```xml
<ONIXMessage release="3.0">
  <Header>...</Header>
  <Product>
    <RecordReference>ethiopian-tewahedo-v28</RecordReference>
    <ProductIdentifier><ProductIDType>15</ProductIDType><IDValue>978...</IDValue></ProductIdentifier>
    <DescriptiveDetail>
      <ProductComposition>00</ProductComposition>
      <ProductForm>EB</ProductForm>
      <ProductFormDetail>E101</ProductFormDetail>  <!-- EPUB 3 -->
      <TitleDetail>...</TitleDetail>
      <Subject>...</Subject>
      <AudienceCode>02</AudienceCode>              <!-- adult, scholarly -->
    </DescriptiveDetail>
    <CollateralDetail>
      <TextContent>...description...</TextContent>
    </CollateralDetail>
    <PublishingDetail>...</PublishingDetail>
    <ProductSupply>...</ProductSupply>
  </Product>
</ONIXMessage>
```

Output location: `out/onix/<edition>.onix.xml`. Validates with `xmllint`
against the ONIX 3.0 schema.

### Font subsetting

New: `scripts/subset_fonts.py`. Wraps `pyftsubset` (fonttools). For each
font in `epub_working/fonts/`:

1. Scan all HTML for codepoints actually used
2. Subset font to that codepoint range
3. Write to `out/<edition>/fonts/`
4. Embed checksum in build manifest

Expected savings: 1.5 MB → ~300 KB per font; with 3 fonts × 5 editions =
~18 MB saved across the catalogue.

### ACE accessibility wrapper

`scripts/ace_check.py` — wraps DAISY ACE (Node-based; install via npm).
Runs per edition; outputs HTML report. ACE catches things `check_a11y.py`
misses (image-alt depth, semantic structure flags, language tags,
reading-order). Library acquisitions ask for ACE certification specifically.

### Reproducible build

Patch `build_epub.py`:
- Fix all timestamps to a single canonical value (project's `dcterms:modified`)
- Sort file order in zip alphabetically
- Use `compresslevel=9` deterministically
- Emit a `BUILD_MANIFEST.txt` with sha256 of every file in the EPUB

Verify: `python3 scripts/build_edition.py --all` twice in succession
produces byte-identical EPUBs (modulo a single configurable timestamp).

### Per-edition CSS

New: `epub_working/styles/edition-<id>.css` files. Linked in the OPF
patch step of `build_edition.py`. Each edition's CSS overrides sub-kind
border/marker colours so the visual distinction matches the edition's
tradition emphasis. Example: in `evangelical-reformed.css`, all
`comm-patristic` notes get a slightly muted accent (de-emphasised),
while `dist-typological` notes get a brighter accent (emphasised).

### Definition of done for 28c

1. ONIX 3.0 file generated and validates for all 5 editions
2. Font sizes drop ≥ 60% across builds
3. ACE report shows ≤ 2 warnings, 0 errors per edition
4. Two consecutive builds produce identical EPUB SHA256s
5. Per-edition CSS demonstrably differs across editions in DevTools
6. HANDOFF v28c entry written

---

## Decisions you need to make before we start 28a

1. **Sources to prioritize first.** Confirm Strong's + TSK + Charles 1913 is the right triad, or substitute (e.g., swap Charles for Sefaria CC corpus if rabbinic > pseudepigraphic for your authoring focus).

2. **Authoring sequencing in 28b.** Strategy A (depth-first 5 books) or Strategy B (breadth-first all 87 books)?

3. **ONIX target retailers.** Are you planning Ingram (widest distribution, requires ONIX 3.0)? Apple Books direct (simpler, accepts EPUB-only)? Amazon KDP (no ONIX needed)? This shapes how rigorous the ONIX export needs to be.

4. **ACE certification depth.** Library-grade (full DAISY ACE, every edition certified) or self-certification (run ACE, fix flagged issues, no formal cert)?

5. **Session cadence.** One marathon session for all of 28a, or split into 28a-1 (sources) + 28a-2 (prospect/promote)?

---

## TL;DR

**v28a is the unlock.** Two sessions, three new scripts, three PD source
corpora cached locally, gives you a daily review queue of pre-drafted
candidate notes. From there, 28b (content) and 28c (commercial release)
follow naturally. Diamond tier trim is already settled in v28_PLANNING.md.

When you're ready to build, the answers I need are the 5 decisions above
— or just "start with Strong's + TSK + Charles 1913 and build prospect.py"
and I'll proceed with the recommendation defaults.
