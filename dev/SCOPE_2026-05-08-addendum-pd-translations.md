# Scope addendum — τ cluster: PD translation expansion

**Added:** 2026-05-08, after Tier A foundations shipped (σ.3, ω.6,
ω.7, υ.7, υ.1).
**Origin:** user request — *"scope a τ cluster for PD translation
expansion."* The platform ships with KJV only; this cluster fills in
the two infrastructural gaps that already exist in the code:
(a) primary-translation alternatives the publisher can pick from
(KJV, WEB, ASV, Douay-Rheims, Geneva, YLT, …); (b) source data for
the language-axis popup slots that `scripts/build_edition.POPUP_LANGUAGES`
already declares but for which no data has been ingested
(Aramaic, Ge'ez, Latin, Coptic, Syriac, plus Hebrew/Greek depth).

## What "PD translation" means here

Two distinct concerns share the same on-disk store and the same
ingestion script:

```
content/translations/
├── kjv/                 ← primary English (publisher picks one)
│   ├── _meta.yaml
│   └── <book>.py        (per-book verse data)
├── web/                 ← future τ.1: World English Bible
├── dr/                  ← future τ.2: Douay-Rheims (Catholic synergy)
├── vulgate/             ← future τ.3: Latin (popup language)
├── lxx/                 ← future τ.4: Brenton's LXX (Orthodox synergy)
├── jps1917/             ← future τ.5-A: Jewish edition primary
├── wlc/                 ← future τ.5-B: Hebrew text (popup language)
├── geez_tewahedo/       ← future τ.6: Ge'ez (Tewahedo flagship native)
├── grk_nt/              ← future τ.7: Greek NT (popup language depth)
├── geneva1599/          ← future τ.8: Protestant historical
└── sources/             ← raw upstream dumps (not in slim zips)
```

**Concern A — primary translation alternatives.** Today every edition
ships with `english = KJV` because that's the only translation
extracted. Concern A adds *alternatives* the publisher can pick. The
build pipeline already swaps the English text in popups at build time
via `scripts/apply_style.swap_english_text` per ν.2.7-A; the only
missing piece is the source data.

**Concern B — language-axis popup slots.** `POPUP_LANGUAGES` already
declares `english, hebrew, greek, aramaic, geez, latin, coptic, syriac`
as the matrix axes (per ν.2.7). Hebrew + Greek have data; the rest
are declared but empty. Concern B fills them in, which makes the
per-book popup-language matrix meaningfully populated for editions
that opt into multiple languages.

The two concerns share `scripts/extract_translation.py` as the
ingestion entry-point and `scripts/core/translations.py` as the
read-side resolver. No new schema. Mental model is the existing
"Add a new translation" / "Add a new popup language" recipes from
CLAUDE_PROJECT_RULES §9.

## Why this cluster matters

1. **Buyer-demo depth.** A buyer asking "make me a Catholic study
   Bible" expects Douay-Rheims (and Vulgate alongside) as available
   text choices, not just KJV. Each new translation unlocks an
   edition-tradition pair that's currently missing.
2. **Tradition alignment with ψ.8.** Cross-denominational compare
   (ψ.8) tags *notes* by tradition, but the *primary text* of an
   edition is also a tradition signal — "Catholic study Bible with
   KJV text" feels off. τ.2 + τ.3 finish what ψ.8 starts.
3. **Tewahedo flagship's native language.** The Ethiopian Tewahedo
   edition is the corpus superset, but its current text is English
   KJV. Shipping Ge'ez (τ.6) is a one-of-a-kind feature commercial
   publishers don't offer at the customizable-edition level.
4. **Linguistic study unlock.** Hebrew WLC and Greek NT (τ.7) plus
   Latin Vulgate (τ.3) make the popup-language matrix actually
   useful for academic publishers; today it's a 3-language slot
   with mostly-empty extras.

## Sub-phase order

Each phase mirrors the §9 "Add a new translation" recipe (~1 session
each unless noted). Order follows §3 sequencing rules — buyer-demo
value + edition synergy first, breadth and historicals later.

```
τ.1   WEB (World English Bible)               ~ 1 session · LOW
      Modern PD English baseline; broad-audience alternative to
      KJV's archaic register. USFM source from
      ebible.org (PD); proven format. Synergy: ρ.1 audio (LibriVox
      already has WEB recordings, so τ.1 + ρ.1 unlock single-edition
      modern English audio Bible).
      Edition synergy: any edition wanting modern register.

τ.2   Douay-Rheims (Challoner 1899 revision)   ~ 1 session · LOW
      Catholic English translation; PD; multiple structured digital
      editions on Internet Archive and ccel.org. Edition synergy:
      Catholic Study Bible — pairs with the Catholic-tagged notes
      that ψ.8 surfaces.

τ.3   Latin Vulgate (Clementine)               ~ 1 session · LOW-MED
      Popup-language fill for the `latin` slot already declared in
      POPUP_LANGUAGES. PD; structured digital editions (Sword
      Project, openscriptures). Edition synergy: Catholic + academic.
      Risk: encoding handling for Latin diacritics; well-trodden but
      worth a smoke test.

τ.4   Brenton's Septuagint (LXX, English)      ~ 1 session · LOW
      English translation of the Greek OT; the Orthodox tradition's
      preferred OT base. Pairs with the existing Greek LXX popup
      language (which currently has English-only data; this gives the
      reader the LXX *in English* as a primary text option).
      Edition synergy: Orthodox Study Bible.

τ.5   Hebrew + Jewish English pair              ~ 1-2 sessions · LOW
      Two related ingests:
        τ.5-A  JPS 1917 — Jewish Publication Society OT, PD; the
               natural primary text for the Jewish Study Bible
               edition.
        τ.5-B  WLC — Westminster Leningrad Codex, the Masoretic
               Hebrew OT; fills out the existing `hebrew` popup-
               language slot at the same time, with structured XML
               from openscriptures. (Today the Hebrew popup data is
               sparse — Strong's word entries via χ.6, but not the
               connected Hebrew text.)
      Edition synergy: Jewish Study Bible primary + matures the
      `hebrew` popup language for every edition.

τ.6   Ge'ez Ethiopian Tewahedo                  ~ 2-3 sessions · MED-HIGH
      The flagship's native language. Source data is sparser than
      Latin/Greek but exists: ge'ezexperience.com, archive.org
      Tewahedo dumps, openbible.info Ethiopian texts. Some books
      (Enoch, Jubilees, Meqabyan) have PD Ge'ez editions on archive.org.
      Risk: Unicode rendering for Ge'ez Ethiopic script; font choice
      for the EPUB; Apocrypha + Tewahedo-only books may have patchy
      coverage. Edition synergy: THE Tewahedo flagship — currently
      the corpus superset but ships English text. Shipping Ge'ez
      makes the flagship genuinely flagship.
      v1.0+ inclusion: not in v1.0 terminus, but the most distinctive
      single τ phase in the cluster.

τ.7   Greek New Testament                       ~ 1 session · LOW
      Stephanus (1550) or Westcott-Hort (1881), both PD; structured
      data from openscriptures or Sword Project. Fills the `greek`
      popup-language slot with the actual NT Greek text (today the
      slot has English-only Brenton-LXX OT data plus χ.1's Strong's
      lemma notes). Edition synergy: academic + linguistic study;
      pairs with χ.1 Strong's Greek notes.

τ.8   Geneva Bible (1599)                       ~ 1 session · LOW
      Pre-KJV Reformation translation; PD; structured digital
      editions exist. Edition synergy: Protestant historical /
      Reformed Study Bible variants. Lower priority than τ.1-τ.7
      because WEB already covers "modern PD English" and KJV covers
      "received Anglican text"; Geneva is a third historical lens.

τ.9   ASV (1901) + YLT (1862)                   ~ 1 session · LOW
      Two more academic-leaning English translations. ASV is the
      direct ancestor of NASB; YLT is the literal-translation
      reference. Both PD, both well-digitized. Bundled because each
      ingestion is small and they share the source format
      (ebible.org USFM). Edition synergy: study editions, academic.

τ.10  Major non-English PD                      ~ 1 session each · LOW
      Bundle of historically-significant non-English PD translations:
        - Reina-Valera 1909 (Spanish)
        - Louis Segond 1910 (French)
        - Luther 1545 (German)
        - Russian Synodal 1876
        - Statenvertaling 1637 (Dutch)
      Each is one session of extraction + smoke testing. Ship them
      as ψ.10-A through ψ.10-E (or fewer if some compress) based on
      regional priority — Reina-Valera first (largest under-served
      audience), Russian Synodal second (Orthodox-aligned), then
      the others.
      Edition synergy: international reach; relevant to publishers
      targeting non-English-primary readers.

τ.11  Reformation-era partials                  ~ 1 session · LOW
      Wycliffe Middle English (1395, partial NT/OT) + Tyndale
      (1525-1530, NT + Pentateuch + Jonah). Both PD, both highly
      readable for educational editions but NOT a primary-text
      candidate for buyer editions. Lowest priority; ship if the
      curriculum / educational angle becomes a buyer ask.
      Edition synergy: educational; museum-edition affordance.
```

## Sub-phase ordering rationale (per CLAUDE_PROJECT_RULES §3)

- **Safest first.** Every τ phase is additive (a new translation
  doesn't change builds for editions that don't pick it up). The
  only structural risk is τ.6 Ge'ez (Unicode + font work) — placed
  after the easier ingests so the proven-pattern muscle memory is
  fresh.
- **Buyer-demo value.** τ.1 (WEB) is highest-leverage as a single
  add — it's the universal modern PD baseline. τ.2 (Douay-Rheims)
  is highest-edition-synergy (gives the Catholic edition its
  natural primary). τ.6 (Ge'ez) is the most distinctive single
  feature in the cluster.
- **Pair related phases.** τ.5-A + τ.5-B share Hebrew tooling.
  τ.9's two English translations share the USFM ingest path.
- **Logical seams.** Each τ phase ships independently; the cluster
  can pause between any two phases without leaving the platform in
  a partial state.

## v1.0 inclusion

**None of τ is in the v1.0 terminus.** The terminus stays
`θ.2 + χ.1 + ψ.8 + corpus ≥ 25K`; τ phases are post-v1.0 polish
that ship as v1.1+ point releases. Justification:

- The buyer demo works with KJV only; depth from τ phases is a
  uniqueness multiplier, not a gate.
- Each τ phase is independently deliverable — no "you can't ship
  v1.0 without all of τ" coupling.
- Post-v1.0, the τ cluster lets v1.1, v1.2, etc. each ship a
  meaningful translation expansion without bundling unrelated work.

That said, individual τ phases can be **pulled forward** if a
specific buyer ask requires them (e.g. a Catholic publisher commits
pre-v1.0 → τ.2 + τ.3 jump ahead). The cluster is structured for
that flexibility.

## Tradeoffs / known limitations

- **Translation file size.** Each translation adds ~3-5 MB to a
  fully-built EPUB. Editions that opt into 5 popup languages
  + 2 primary-translation alternatives (e.g. KJV + Douay-Rheims)
  ship at ~30 MB before audio. ρ.1 (audio) compounds this.
  Mitigated by per-edition opt-in (publishers don't get every
  translation by default).
- **Source-data quality varies.** USFM sources from ebible.org are
  high-quality and consistent; older PD digital editions (CCEL,
  Sword Project, archive.org dumps) are messier. Each phase's
  first session is "extract + smoke test"; data-quality
  investigations slip into a second session if needed.
- **Ge'ez (τ.6) is the most uncertain.** Source data is sparser;
  the script renders properly only with a Unicode-aware Ge'ez
  font; some Tewahedo-only books may need TTS fallback (per ρ.3
  in the audio cluster). Worth flagging here so it doesn't
  surprise the implementing session.
- **Copyright diligence at the boundary.** Some translations near
  the PD boundary (RSV, NRSV, NIV, ESV) are explicitly NOT PD
  in the US until well into the 21st century. The τ cluster is
  PD-only; modern translations stay out unless a future cluster
  is added with explicit license-tracking infrastructure.
- **Translation matrix UI scale.** With τ shipping 10+ phases,
  the per-edition popup-language matrix grows wider. The ψ.12
  matrix smoothness pass already in scope addresses this; ν.2.7's
  per-book matrix may also need a pass once the language list
  exceeds ~12. Tracked as a follow-up at ψ.12 implementation
  time, not a separate τ phase.

## Tests / acceptance criteria per phase

Mirror the existing KJV ingest's test pattern (per
CLAUDE_PROJECT_RULES §9 "Add a new translation"):

1. Source data lands under `content/translations/sources/<id>/` with
   the canonical layout for that source format (USFM, Sword
   Project ZIP, openscriptures XML, etc.).
2. `python3 scripts/extract_translation.py <id>` runs to completion
   and writes `content/translations/<id>/_meta.yaml` plus per-book
   `<book>.py` files.
3. `from scripts.core import translations as t; t.list_translations()`
   includes the new id.
4. A smoke test (in `tests/test_scripts.py`) loads at least one
   verse from the new translation by `(book, chapter, verse)` and
   asserts text content non-empty.
5. The /customize console picks up the new translation
   automatically (no UI work per phase unless the new translation
   has special metadata that the existing schema doesn't cover).
6. A build smoke test produces a valid EPUB when an edition
   selects the new translation as its primary text.

The first τ phase (τ.1 WEB) is the pattern-establishing one — it
locks in the test layout that subsequent phases mirror. Treat τ.1's
test additions as the cluster template.

## Future cluster-shape work

If a third or fourth τ phase reveals shared parser-config patterns
(e.g. every USFM ingest has the same _meta defaults), abstract
those into `scripts/core/translation_sources.py` as a follow-up.
Don't pre-abstract: the project's pattern is "two instances visible
before codifying" (per the §9 rule history). Currently zero τ
phases have shipped, so abstraction is premature.

If translation file storage starts to dominate `content/`, consider
moving `content/translations/sources/` (the raw upstream dumps) to
the `.gitignore` block — they're regenerable from
`scripts/extract_translation.py`. Already excluded from slim zips
per the existing rules; just not gitignored. Tracked as a
follow-up; not a τ phase itself.
