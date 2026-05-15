# Π.2 pre-flight checklist — Ethiopian-Tewahedo popup-language flip

**Seeded at Π.2.prep (2026-05-14)** per the AUDIT_2026-05-14-LIGHT-2
recommendation set. Π.2 is the "flip the switch" phase that
surfaces Geʽez + Amharic in the ethiopian-tewahedo edition's verse
popups by default. This checklist enumerates the gate dependencies,
publisher decision points, exact YAML edits, verification commands,
post-flip QA, and rollback plan so the Π.2 ship can land cleanly
in a single session when its upstream gates are met.

**Authoritative scope reference:** `dev/SCOPE_2026-05-14-parallel-
bible.md` §Π.2 (lines 632-660). This file is the OPERATOR-FACING
pre-flight companion; the SCOPE doc is the design-authoritative
spec.

---

## §1 — Π.2 scope reminder (one-line change + tests)

The Π.2 ship itself is mechanical:

```yaml
# content/editions.yaml — ethiopian-tewahedo block
# BEFORE:
    popup_languages_default:
      - "english"
      - "hebrew"
      - "greek"

# AFTER (Π.2):
    popup_languages_default:
      - "english"
      - "hebrew"
      - "greek"
      - "geez"
      - "amharic"
```

Pin tests (proposed `TestPi2EthiopianTewahedoPopups`):

1. `ethiopian-tewahedo.popup_languages_default` contains both
   `"geez"` and `"amharic"` after Π.2.
2. Sample verses (e.g. mq1 11:1 + gen 1:1) emit popups with all
   five languages.
3. All 8 OTHER editions (catholic-study, evangelical-reformed,
   jewish-study, scholarly-academic, eastern-orthodox,
   anglican-bcp, lutheran-confessional, coptic-orthodox) preserve
   their existing popup_languages_default.

---

## §2 — Gate dependency dashboard

Π.2 may NOT ship until ALL gates below are ✓.

| Gate | Phase | Current state | Π.2 prerequisite reason |
|---|---|---|---|
| Π.1 declarative inventory | Π.1 (committed `13501e9`) | ✓ SHIPPED 2026-05-14 | structural_map for jubilees + one_enoch + laodiceans + meqabyan declared; required for popup-emission code to know which Tewahedo-distinctive slots to surface. |
| Π.1.B laodiceans alternate-source | Π.1.B (committed `f139494`) | ✓ SHIPPED 2026-05-14 | alternate-source for the lao slot declared; required if publisher elects to include lao in ethiopian canon at Π.2 follow-through (see §3 D2). |
| τ.6.x.0c Tesseract install | τ.6.x.0c | ✓ SHIPPED 2026-05-14 | Tesseract 5.5.0 installed + amh.traineddata present + `script/Ethiopic` adopted as Geʽez recognizer (resolves τ.6.x.0b AVAILABILITY-UNCERTAIN gez.traineddata gap with strictly-better third option). Resolver `scripts.core.paths.tesseract_binary()` decouples ingest from PATH state. |
| τ.6.x.1 Tesseract engine wired | τ.6.x.1 | ✓ SHIPPED 2026-05-14 | `scripts/extract_parallel_pdf.py` gains `--engine tesseract` (default) — renders each PDF column at 350 dpi via pymupdf + invokes `tesseract -l script/Ethiopic` (Geʽez) / `tesseract -l amh` (Amharic) per column with W-W1-safe subprocess pattern. Pre-flight resolves the binary via `scripts.core.paths.tesseract_binary()` + verifies both required language packs are present via `tesseract --list-langs` before any PDF page is opened; clean SystemExit with install/tessdata pointers on either gap. |
| τ.6.x.1.A Pilot validation | τ.6.x.1.A | ✓ SHIPPED 2026-05-15 | Empirical end-to-end pilot: page 1318 (mq1 ch1 opening) rendered + OCR'd in 6.5s producing recognizable Geʽez + Amharic body-text at `ocr-tier3` quality. Reference artifact `dev/PILOT_TAU6X1A_OUTPUT.md` captures timing extrapolations (mq1=5.5min, meqabyan=8min, standard-canon=5h single-threaded) + 5 quality observations + publisher-direction inputs. NEW finding: parse_verses_from_text() keys off Arabic digits but PDF uses Ethiopic numerals → parser extension needed at τ.6.x.1.B. |
| τ.6.x.1.B Ethiopic numeral parser | τ.6.x.1.B | ✓ SHIPPED 2026-05-15 | NEW `normalize_verse_numerals()` pure-function pre-pass at the top of `parse_verses_from_text()` converts line-start Ethiopic numerals + Ethiopic punctuation to the Arabic-digit+colon form `VERSE_NUM_RE` already matches. Backward-compatible (text-layer Arabic-digit input is a no-op). Paired `CHAPTER_HEADER_RE` extension tolerates Ethiopic word-space `፡` (U+1361) and Ethiopic comma `፣` (U+1363) as separators. Runtime regression-pins confirmed page 1318 now yields ≥3 Geʽez verses + ≥2 Amharic verses (vs 0 pre-fix). Resolves the τ.6.x.1.A empirical finding. |
| τ.6.x.2.D D-decisions codification | τ.6.x.2.D | ✓ SHIPPED 2026-05-15 | Publisher-direction matrix RESOLVED: D1-a (incremental per-book cadence) + D2-b (batched τ.6.x.3 audit pass) + D3-c (full 87-book audit) + D4-c (Amharic-first inversion — τ.7.x ships BEFORE τ.6.x.2+). DECISION-ONLY ship; no data ingest; τ.6.x.0a contract preserved. Codified in `_source.yaml::ocr_strategy.tau6x2D_decisions` + SCOPE §7.7. Rewires gate ordering below per D4-c inversion. |
| τ.7.x.a Amharic Genesis ingest | τ.7.x.a | ✓ SHIPPED 2026-05-15 | First τ.7.x.* sub-ship: amharic-tewahedo/gen.py upgraded from Π.0 3-verse seed → 1308-verse full-book ingest at 85.3% coverage via text-layer engine + paragraph_mode parser (τ.6.x.1.C) + lenient chapter markers (τ.6.x.1.D) + writer-side renumber_against_floor with GENESIS_VERSE_COUNTS (τ.7.x.a). Chapters 1-42 fully populated + 43 partial (16/34) + 44-50 empty (τ.6.x.3 audit-handoff). Gen 1:1 preserves PDF source's expanded variant `በመጀመሪያው ቁን ...`. Resolves τ.6.x.1.D `chapter_marker_keyword_garbled_past_recognition` residual via the pre-committed renumbering path; 5th instance of single-key back-link annotation pattern. |
| τ.7.x.b-z Amharic remaining books | τ.7.x.b → τ.7.x.z | ⬜ next-phase under D1-a per-book cadence | τ.7.x.b (Amharic Exodus) is next-up. Re-uses τ.7.x.a pipeline (text-layer + paragraph_mode + renumber); needs EXODUS_VERSE_COUNTS floor + structural_map.exodus block (pdf_page_range likely [86, ~150] per τ.7.x.a.0 PILOT §1 boundary inspection — exact end-of-Exodus boundary verified at τ.7.x.b page-range discovery sub-phase). |
| τ.6.x.2+ Geʽez per-book ingest | τ.6.x.2.a → τ.6.x.2.z | ⬜ blocked on τ.7.x completion (D4-c sequencing) | populates geez-tewahedo translation slot per-book at ocr-tier3 under D1-a incremental cadence. Runs after τ.7.x against an Amharic-validated pipeline (D4-c rationale). tier-3 → tier-2 cross-check deferred to τ.6.x.3 per D2-b. |
| τ.6.x.3 batched ocr-tier3 → tier-2 audit | τ.6.x.3 | ⬜ blocked on τ.7.x + τ.6.x.2+ completion (D2-b + D3-c) | Full 87-book operator cross-check pass covering BOTH the Amharic (τ.7.x.x) and Geʽez (τ.6.x.2.x) ocr-tier3 outputs; flips SOURCE_QUALITY = ocr-tier3 → ocr-tier2 on cleared entries; honesty-contract caveat lifts on tier-2 entries. |
| δ.1.x Phase-4 Meqabyan apparatus | δ.1.x (multi-session) | ⬜ blocked on operator page-image render | required for ethiopian-tewahedo's Meqabyan-1-3 popups to be more than the v1 English baseline (Phase-4 page-image revisions feed compare-divergence-geez kind). |

**Π.2 is unblocked ONLY when:** Π.1 ✓ AND Π.1.B ✓ AND τ.6.x.0c ✓
AND τ.6.x.1 ✓ AND τ.6.x.1.A ✓ AND τ.6.x.1.B ✓ AND τ.6.x.2.D ✓
AND τ.7.x ✓ AND τ.6.x.2+ ✓ AND τ.6.x.3 ✓. δ.1.x apparatus is
RECOMMENDED but NOT strictly blocking — Π.2 can ship with
Meqabyan popups showing only the v1 English baseline (Phase-4
apparatus is a bonus enhancement, not a Π.2 prerequisite).
**As of 2026-05-15: Π.1 + Π.1.B + τ.6.x.0c + τ.6.x.1 + τ.6.x.1.A
+ τ.6.x.1.B + τ.6.x.1.C + τ.6.x.1.D + τ.6.x.2.D + τ.7.x.a (first
τ.7.x.* sub-ship) shipped; remaining gates τ.7.x.b-z (under D1-a
per-book cadence) + τ.6.x.2+ (after τ.7.x completion) + τ.6.x.3
(after both arcs). All remaining gates are now data-ingest +
operator cross-check work; no Claude-side technical or publisher-
direction blockers remain.**

**D4-c gate-ordering note:** τ.7.x is intentionally listed
ABOVE τ.6.x.2+ in the gate table above. This is the τ.6.x.2.D
D4-c inversion: the Amharic-trained recognizer produces cleaner
OCR than the script-level Geʽez recognizer (per τ.6.x.1.A pilot),
so the Amharic per-book stream runs first to validate the
per-book ingest pipeline before the noisier Geʽez stream
follows. Per SCOPE §7.7.3.

---

## §3 — Publisher decision matrix

Π.2 surfaces several decisions that require explicit publisher
direction. Defaults are RECOMMENDED but the publisher may override.

### D1 — Default popup-language set for ethiopian-tewahedo

**Recommendation:** `[english, hebrew, greek, geez, amharic]` (5
languages, additive: existing english/hebrew/greek + new geez/
amharic).

**Alternatives:**
- D1.a: `[english, geez, amharic]` (3 languages, drop hebrew/greek)
- D1.b: `[english, hebrew, greek, geez, amharic, syriac]` (6
  languages, add syriac via the Ephrem γ.4.2 corpus)

**Publisher chooses:** the broadest set is D1 default; D1.a is
purist-Ethiopian; D1.b is comparative-patristic. Recommendation
defaults to D1 per memory `feedback_extensive_answers` (broadest
scope) AND because hebrew/greek are already present (additive flip
is safest per project rules §3.1).

### D2 — Letter to Laodiceans (`lao`) canon membership

**Current state:** `lao` is NOT in any canon definition in
`content/canons.yaml` (verified at Π.1.B ship time). Π.1.B declared
the alternate source but explicitly left canon membership as a
publisher decision (per `letter-to-laodiceans/_source.yaml::
ingest_gate_blockers[2]: tewahedo-flagship-edition-canon-decision
(Π.2 prerequisite)`).

**Recommendation:** EXCLUDE `lao` from the ethiopian canon at Π.2
ship time. Reasons:
1. The parallel-Bible PDF (the publisher-supplied authoritative
   source for ethiopian-tewahedo) does NOT contain `lao`.
2. Adding `lao` to the canon would require a separate τ.x.lao
   ingest ship to populate Lightfoot 1875 + James 1924 content
   into `content/notes/lao.py` and `content/translations/*/lao.py`.
3. The Tewahedo broader-canon status is documented per Metzger 1987
   §V but is NOT universally observed across EOTC printed bibles.

**If publisher DOES want `lao` in:** add a separate Π.2.B
post-flip ship that performs canon insertion + τ.x.lao ingest.
Π.2.prep does NOT pre-commit to either direction.

### D3 — 4ba / 2en / 1cl notes-file state

**Current state:** `4ba`, `2en`, `1cl` are in the ethiopian canon
(per `content/canons.yaml` lines 394 / 370 / 439) but have EMPTY
notes-files (`content/notes/{4ba,2en,1cl}.py` are 0-tuple per
AUDIT_2026-05-13-DEEP D-W3 partial-status finding).

**Recommendation:** SHIP Π.2 with the current empty-but-canonical
state. Reasons:
1. The 87-book canon is correctly declared; book-content emission
   handles empty-notes gracefully (verses emit the v1 English
   baseline + Geʽez/Amharic translation; commentary popups are
   simply empty).
2. Populating `4ba/2en/1cl` notes is a SEPARATE future-arc target
   (per AUDIT_2026-05-13-DEEP D-W3) gated on PD source acquisition,
   not on Π.2.

**Alternative:** if publisher wants populated commentary for these
three books before Π.2, defer Π.2 until a γ.4.10+ ship lands.
Recommendation: ship Π.2 first; populate later.

### D4 — Visual QA scope

**Recommendation:** verify ethiopian-tewahedo build across 5
e-readers post-flip:
- Apple Books (macOS / iOS)
- Calibre + KOReader (Linux / generic)
- Kindle Previewer (Amazon)
- Adobe Digital Editions (Windows)
- Thorium (PWA / cross-platform)

For each, verify:
1. Geʽez + Amharic CSS classes render (Noto Sans Ethiopic if
   `EMBED_FONT_PATHS` populated; system fallback otherwise).
2. Popup-language selector shows all 5 languages (per D1).
3. No regression in english/hebrew/greek rendering.
4. Per-book matrix in `/customize` console correctly surfaces
   geez/amharic toggle columns.

---

## §4 — Pre-flight verification commands

Run these BEFORE attempting Π.2. Each command should pass or be
explained-away before flipping the switch.

```bash
# Π.1 ✓ verification
pytest tests/test_parallel_bible_pi1.py -q
# Expect: 58 passed, 0 failed.

# Π.1.B ✓ verification
pytest tests/test_parallel_bible_pi1b.py -q
# Expect: 69 passed, 0 failed.

# τ.6.x.0c ✓ verification (operator-side) — shipped 2026-05-14
tesseract --version
tesseract --list-langs | grep -E "^(amh|script/Ethiopic)$"
# Expect: tesseract 5.x + "amh" present + "script/Ethiopic" present.
# Note: gez.traineddata is intentionally NOT required; τ.6.x.0c adopted
# script/Ethiopic as the Geʽez recognizer (Option C, strictly better
# than the two τ.6.x.0b-anticipated fallbacks). If Tesseract is not on
# PATH, the resolver scripts.core.paths.tesseract_binary() falls back
# to platform-conventional install paths automatically.

# τ.6.x.1 ✓ verification (engine wired)
python3 -c "from scripts.extract_parallel_pdf import ENGINE_DEFAULT, OCR_DPI, GEEZ_LANG, AMH_LANG; print(ENGINE_DEFAULT, OCR_DPI, GEEZ_LANG, AMH_LANG)"
# Expect: tesseract 350 script/Ethiopic amh
python3 scripts/extract_parallel_pdf.py --help | grep -- "--engine"
# Expect: '--engine {tesseract,text-layer}' appears in --help output.

# τ.6.x.2.D ✓ verification (D-decisions codified) — shipped 2026-05-15
python3 -c "import yaml; d = yaml.safe_load(open('content/translations/sources/parallel-bible-eotc/_source.yaml', encoding='utf-8'))['ocr_strategy']['tau6x2D_decisions']; print(d['decisions']['D1_cadence']['choice'], d['decisions']['D2_tier_ramp']['choice'], d['decisions']['D3_audit_plan']['choice'], d['decisions']['D4_amharic_sequencing']['choice'], d['next_phase'])"
# Expect: D1-a D2-b D3-c D4-c τ.7.x.a

# τ.7.x ✓ verification (Amharic per-book ingest — D4-c sequencing puts this FIRST)
ls content/translations/amharic-tewahedo/*.py | wc -l
# Expect: 87 (all canon books), NOT 1 (gen.py-only seed).

# τ.6.x.2+ ✓ verification (Geʽez per-book ingest — D4-c sequencing puts this SECOND)
ls content/translations/geez-tewahedo/*.py | wc -l
# Expect: 87 (all canon books), NOT 1 (gen.py-only seed).

# τ.6.x.3 ✓ verification (full 87-book ocr-tier3 → ocr-tier2 audit pass)
# Expect: every Amharic + Geʽez book file has its SOURCE_QUALITY entries
# audited; tier-3 entries that cleared cross-check are flipped to tier-2;
# entries still at tier-3 carry the operator-cross-check caveat.

# δ.1.x.A-Z apparatus state (optional)
python3 scripts/build_meqabyan_revision.py --check
# Expect: zero rejected entries (any number of accepted is fine).

# Closed-arc invariants (all 12 should remain green)
pytest -k "closed_arc or arc_close or popup_lang or embed_font or amharic or geez_tewahedo or cyril_remains_plurality" -q
# Expect: all pass.

# Project linter
python3 scripts/lint_rules.py
# Expect: CLEAN 11 pass · 0 warn · 0 fail.
```

If any verification fails, do NOT proceed with Π.2. Investigate
and fix the failing gate before flipping the switch.

---

## §5 — Π.2 ship script (exact diff)

When all §2 gates are ✓ and §3 decisions are confirmed, the Π.2
ship is mechanically a single YAML edit + tests + state docs +
build verification.

### §5.1 YAML edit

```diff
# content/editions.yaml — ethiopian-tewahedo block (approximately
# at lines 128-131 as of Π.2.prep ship time; the exact line numbers
# may drift if upstream edits land first — use ruff/diff at apply
# time).

     popup_languages_default:
       - "english"
       - "hebrew"
       - "greek"
+      - "geez"
+      - "amharic"
```

### §5.2 Tests to add

In `tests/test_parallel_bible_pi2.py` (NEW at Π.2 ship time;
modeled on `tests/test_parallel_bible_pi1b.py`):

```
TestPi2EthiopianTewahedoPopups (~6 pins):
  - test_geez_in_popup_languages_default
  - test_amharic_in_popup_languages_default
  - test_english_hebrew_greek_preserved
  - test_other_editions_popup_languages_unchanged
  - test_5_language_popup_emission_sample_verse
  - test_phi1_fonts_render_in_built_epub
```

### §5.3 Build verification

```bash
python3 scripts/build_edition.py ethiopian-tewahedo
java -jar epubcheck.jar exports/ethiopian-tewahedo.epub
# Expect: epubcheck reports zero errors.
```

### §5.4 State doc updates

- CHANGELOG entry with Π.2 ship-message.
- SESSION_STATE headline update.
- IN_FLIGHT.md prior-task chain update.
- SCOPE_2026-05-14-parallel-bible.md §Π.2 status change from ⬜
  pending to ✓ SHIPPED.

---

## §6 — Post-flip QA checklist

After §5 lands, validate:

```
[ ] ethiopian-tewahedo EPUB builds cleanly (build_edition.py exit 0)
[ ] epubcheck passes (zero errors)
[ ] Geʽez popups render on Apple Books
[ ] Geʽez popups render on Calibre / KOReader
[ ] Geʽez popups render on Kindle Previewer
[ ] Geʽez popups render on Adobe Digital Editions
[ ] Geʽez popups render on Thorium
[ ] Amharic popups render on all 5 e-readers
[ ] Existing english/hebrew/greek popups UNCHANGED on all 5 e-readers
[ ] Per-book matrix in /customize console shows geez+amharic columns
[ ] /api/preflight returns CLEAN status
[ ] All 12 closed-arc invariants still green
[ ] Linter 11/11
```

---

## §7 — Rollback plan

If visual QA reveals issues post-flip:

1. **Hot-fix path:** revert the editions.yaml edit (5 lines) via
   `git revert` of the Π.2 commit. Rebuild ethiopian-tewahedo EPUB.
   Confirm rollback restored prior state.

2. **Identified-issue path:** if the issue is a CSS / font /
   rendering bug rather than a Π.2-introduced regression, file a
   φ.x follow-up ship (e.g. φ.2 Ethiopic font polish round 2)
   rather than reverting Π.2 itself.

3. **Publisher-direction-change path:** if publisher decides
   post-flip to revert D1 / D2 / D3 / D4 choices, treat as a
   normal "edit ethiopian-tewahedo" ship rather than a Π.2 rollback.

---

## §8 — Π.2.prep ship contract

This pre-flight checklist file is DECLARATIVE-ONLY. Π.2.prep makes
NO changes to:

- `content/editions.yaml` (Π.2 itself performs the flip).
- `content/canons.yaml` (Π.2 does not change canon membership; D2
  is a SEPARATE Π.2.B-or-later decision).
- `content/notes/*.py` (no data ingest).
- `scripts/*` (no tool changes).
- Production EPUB output (v1.0 byte-identical reproducibility
  preserved).

**Closed-arc invariants regression-guarded across Π.2.prep:**
γ.4.8.E + γ.4.8.F + Π.0.1 + Π.0.4 + τ.6.x.0a/b + δ.1.0 + δ.1.x.A.0
+ Π.1 + Π.1.B all preserved.

**Phase coverage:** Π.2.prep is documented here + cross-referenced
from `dev/SCOPE_2026-05-14-parallel-bible.md §Π.2` + asserted by
`tests/test_parallel_bible_pi2prep.py`.

---

*Π.2 pre-flight checklist, seeded 2026-05-14 at Π.2.prep.
Operator-facing companion to SCOPE §Π.2; updates ride normal Π.2
prep follow-up ships rather than this seed file.*
