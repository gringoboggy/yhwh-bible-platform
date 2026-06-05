# Auto-note content-quality audit (post RX Phase 1 scaffold strip)

## 1. Intro

**Purpose.** RX Phase 1 stripped the editorial `<em>[Reviewer: …]</em>` scaffold span out of the auto-generated note bodies. This audit answers one question per note kind: with the scaffold gone, do the auto-notes still read as finished, publishable content, or did the strip leave damage (dangling text, orphaned punctuation, broken markup) behind? Secondarily, it flags any genuinely thin/raw bodies — but **only** where brevity is a defect, never where it is the kind's design.

**Method.** Purpose-aware sampling per kind: 24 spread across the length distribution + the 8 shortest bodies (the likeliest-thin), for 32 inspected bodies per kind. Each first assessment was then put through an adversarial critique that independently re-verified the claims — frequently by scanning the *full* on-disk population, not just the 32 samples — and stripped out false flags. Where the critique's final verdict differs from the first assessment, **the critique's verdict governs** (it caught two PASS calls that the sample slice had hidden).

**Scope.** The 6 auto-note kinds (~88.7k notes total). This is **audit-only** — no content was edited. Every remediation below is a suggestion for the Windows lane, not a change made here.

## 2. Summary table

| Kind | Total | Final verdict | Confidence | Strip damage | Est. thin/raw |
|---|---|---|---|---|---|
| topic-nave | 26,335 | **mixed** | high | none | ~22 phrase-only bodies (<0.1%) |
| topic-torrey | 21,764 | **mixed** | high | none | 596 bodies (2.74%) |
| lang-hebrew | 22,980 | **good** | high | none | 0% |
| lang-greek | 7,669 | **mixed** | high | none | ~1,272 bodies (Theós + Phōs) |
| xref-citation | 6,132 | **good** | high | none | 0% |
| dict-easton | 3,779 | **mixed** | high | none | 1,431 bodies (37.9%) |

Headline: **the scaffold strip was clean across all six kinds** — zero strip artifacts anywhere. The "mixed" verdicts are all driven by *pre-existing ingest/source defects* the strip did not cause and did not touch.

## 3. Per-kind sections

### topic-nave — Nave's Topical Bible index

**Purpose.** Topical-concordance grouping: a topic label + the verses on that theme. Terse by design — it indexes a theme, it does not explain it. A body naming even one topic is complete.

**Verdict (critique governs): mixed / high.** The 32-sample verdict (clean, terse-by-design, short bodies fine) holds, but the full-store scan surfaced a defect class the samples missed.

**Strengths.**
- Uniform, balanced template store-wide: `<strong>Topics.</strong> This verse appears under: <LABELS>.` — one bold lead-in, terminal period, no stray markup.
- Zero strip-damage signatures across all 48,099 on-disk bodies: no `[Reviewer`/`[Editor`/`<em>`/`TODO` remnants, no empty bodies, no orphaned text at the strip seam.
- Short single-label bodies (len 54) are complete one-topic indexes, not truncations.

**Genuine weaknesses.**
- 87 bodies embed a mis-parsed Nave **sub-entry description** as if it were a topic heading. This is pre-existing parse content, not strip damage.
- Cosmetic only (NOT defects): consecutive repeated labels (`SETH, SETH`; `PREACHING, PREACHING, PREACHING`) and comma-bearing topic names (`JESUS, THE CHRIST`) are faithful to Nave; optional render-time polish.

**Confirmed thin/raw (after false flags removed).**
- **22 bodies** whose entire label list is the descriptive phrase `The king of Babylon to be rewarded with the spoil of Egypt for his service against.` (eze-region refs plus scattered across 1co/1jn/2ki/1ti/act/2th/deu/isa/joe). The only "topic" is a truncated descriptive sentence — a dangling fragment, not an index.
- **75 bodies** carry the doubled terminal period from that phrase's internal period colliding with the template period (`…for his service against..`).

False flags correctly rejected: the short ALL-CAPS labels (`AX`/`OG`/`AR`/`ER`/`NO`/`UZ`) are genuine Nave headings; do not touch them.

**Note for the implementer.** Grep topic-nave bodies for the literal `The king of Babylon to be rewarded with the spoil of Egypt for his service against.` — 87 bodies (75 with `against..`, 22 phrase-only). Prefer the **root-cause** fix: re-run the Nave parser with a heading-vs-description discriminator (real headings are short ALL-CAPS; this is sentence-case ending in a period) rather than patching 87 instances. After fixing, a store-wide grep for `..` in topic-nave bodies should return 0, and no label list should contain an internal period. Do **not** touch the short ALL-CAPS single-label bodies.

### topic-torrey — Torrey's New Topical Textbook index

**Purpose.** Same shape as Nave's — a topic + its verses. Terse by design.

**Verdict (critique governs): mixed / high.** Strip damage genuinely none; fit-for-purpose is not clean.

**Strengths.**
- Full-corpus scan of all 21,764 bodies: zero scaffold remnants, zero empty/truncated bodies, zero unbalanced `<strong>`. The strip commit acted cleanly; the corruption below predates it.
- 55-char single-topic notes (`…appears under: Day.`) are complete by design.

**Genuine weaknesses.**
- A **cross-reference ref-dump** corruption class leaked into the topic-list field at ingest (not the strip).
- Verbatim-repeated topic labels affect **~2,396 bodies (11%)** — cosmetic and pre-existing, but the first assessment understated this as "a handful."

**Confirmed thin/raw (after false flags removed).**
- **596 bodies (2.74%)** where a scripture cross-reference list leaked into the topic field, often with a Bible book-name posing as a fake heading. Concentrated in luk/mrk/jhn/1jn/2jn/3jn/jud.
- Worst cases: **2jn 1:1c** and **3jn 1:1c** at 7,160 chars / ~1,055 Zechariah refs (`…appears under: Zechariah 1:1  1:7  1:8 …`); **jud** at 4,363 chars / 633 ref tokens; a 422-ref pattern repeated across luk (`Marriage, Pride, Zechariah 1:1 1:7…`). These read as a topical note whose "heading" is a wall of verse numbers.

The 7,160-char `len_max` was rationalized by the first assessment as "the same template scaled" — it is corrupted, not scaled. False flags correctly rejected: 55-char single-topic notes and compound comma-bearing headings.

**Note for the implementer.** Strip sign-off is fine; this is a separate ingest defect (predates the strip). To find the class: scan topic-torrey bodies where the text after `appears under: ` matches a Bible book-name immediately followed by `chap:verse` runs (book-name + `\d+:\d+`). The verbatim-duplicate-topic issue (~11%) is cosmetic/non-blocking. Since the leak traces to the ingest pass, re-check other ingest-heavy kinds for the same ref-dump pattern.

### lang-hebrew — Strong's Hebrew word study

**Purpose.** A lemma + transliteration + concise gloss for ONE word. Terse by design — a dictionary gloss.

**Verdict (critique governs): good / high.** Independently re-verified: all 22,980 bodies AST-parsed across 88 stores.

**Strengths.**
- 0 strip artifacts, 0 HTML imbalances, 0 scaffold remnants, 0 empty/truncated bodies. Structure holds universally:

```
<strong>translit (<em>HEBREW</em>).</strong> gloss.
```
- Brevity is purpose-appropriate: 54-char glosses like `ʼishshâh (אִשָּׁה). a woman.` are complete entries (311 bodies under 60 chars, all well-formed). Length range 54 / 105 / 303.

**Genuine weaknesses.** None material to publishability.

**Confirmed thin/raw.** None.

**Note for the implementer.** Ship lang-hebrew as-is — no remediation needed. One caution about the *audit record*, not the content: the first assessment's "6 empty glosses reconciled via literal double-quotes" narrative is **fabricated/misattributed** — those 6 refs (exo בְּצַלְאֵל, deu שֵׁדִים, gen וַיִּזְכֹּר, 1sa שְׁמוּאֵל, 2sa חָסִיד, jdg פֶּלִאי) are kind=`word` (provenance "User original"), not lang-hebrew; no lang-hebrew body contains a literal double-quote; the true max body is 303 chars; the count is 22,980 (not the "22,397" stated). The verdict survives because the real set is clean either way. Practical follow-up: the curated multi-sentence Hebrew word studies belong to the separate kind=`word` set — make sure **that** kind gets its own audit and is not assumed-covered by this PASS.

### lang-greek — Strong's Greek word study

**Purpose.** Lemma + transliteration + concise gloss. Terse by design.

**Verdict (critique governs): mixed / high.** Strip damage genuinely none; two pre-existing source-extraction defects drop fit-for-purpose.

**Strengths.**
- Re-verified across all 32 samples + a corpus grep: 0 scaffold remnants, 0 unbalanced `<strong>`/`<em>`, 0 empty/bare-lemma bodies. Template `<strong>Translit (<em>Greek</em>).</strong> gloss.` intact.
- 52-char entries (`Alḗtheia (ἀλήθεια). truth.`) are complete by design; high per-occurrence duplication is correct Strong's tagging.

**Genuine weaknesses.** Both are pre-existing source extraction (NOT strip), but both are substandard *for the kind's purpose* (a concise, **accurate** gloss).

**Confirmed thin/raw (after false flags removed).**
- **Theós head-drop — ALL 1,196 θεός entries (100%, grep 1196/1196).** Every θεός gloss reads only `figuratively, a magistrate; by Hebraism, very.` and **none** carry the primary "God / supreme Divinity" sense. The first assessment called this "a few entries (4 refs)" — a ~300x undercount. This is the single most theologically central NT word reading only its tail sub-sense; it is the only corpus gloss starting with `figuratively,`.
- **Phōs paren-imbalance — 76 bodies** (one was in the spread sample as **mat 6:23b**): `…compare G5316 (φαίνω), G5346 (φημί)); luminousness…` — 4 open / 5 close parens (a dangling `)`) plus a Strong's etymology/cross-ref fragment leaking into the gloss prose. The first assessment's balance check covered angle-bracket tags only, so the round-paren malformation went undetected.

False flag correctly rejected: the 52-char `Alḗtheia` entries (complete by design).

**Note for the implementer.** Strip is clean — do not chase strip artifacts. Log a separate source-fidelity fix before public release:
- Theós (greppable, the lone corpus gloss with this shape): `grep -rl 'θεός</em>).</strong> figuratively, a magistrate'`
- Phōs: `grep` for `compare G5316 (φαίνω), G5346 (φημί))`

A "God" gloss reading only "a magistrate" is a visible quality hit on the most-read word.

### xref-citation — Treasury of Scripture Knowledge cross-references

**Purpose.** A list of linked parallel verses. Terse by design — a citation list, not prose.

**Verdict (critique governs): good / high.** Reproduced at full-population scale.

**Strengths.**
- All 6,132 bodies AST-extracted and checked against 14 distinct defect classes + a strict canonical regex (`<strong>Cross-references.</strong> ` + 1..N anchored links joined by ` · ` + terminal `.`): **100% conformance**. Zero scaffold remnants, zero unbalanced HTML, zero empty/truncated bodies.
- Every body carries at least one well-formed, properly-anchored cross-reference link. Link-count distribution: 1,758 single-ref, 990 two-ref, 3,384 three-ref. Lengths 88 / 200 / 222. The shortest (88 chars) is a complete single-ref citation.

**Genuine weaknesses.** Cosmetic/source only: 1,200 distinct bodies recur as exact duplicates (different verses citing the same TSK parallel list — expected apparatus behavior); visible book labels use TSK display abbreviations (`Jol`, `Jas`, `Php`, `Ezk`, `Nam`, `Sng`, `Oba`) diverging from the project's internal canonical codes (65 distinct labels, all consistent).

**Confirmed thin/raw.** None.

**Note for the implementer.** No remediation needed — the strip is verified clean at full population, PASS / ship-as-is is correct. If display polish is ever wanted (NOT a strip fix): the visible TSK abbreviations could be normalized to canonical book codes as an optional, separate label-consistency pass. Never audit-blocking.

### dict-easton — Easton's Bible Dictionary entry

**Purpose.** A definitional/encyclopedic entry. Expected to read as a short, **complete** article.

**Verdict (critique governs): mixed / high.** The first assessment's PASS does not survive source verification. This was the most important catch in the audit.

**Strengths.**
- Strip is clean: all 3,779 stored bodies have 0 `<em>` remnants, 0 `[Reviewer`/`TODO`/`[Editor`, 0 unbalanced `<strong>`, 0 empties. Every body opens with `<strong>Dictionary (Easton's).</strong>`.
- Short stubs (`TEKEL weighed (Daniel 5:27).`, ZABBUD, SHOBAI) are complete-by-design dictionary entries, not truncations.

**Genuine weaknesses.**
- **Systemic mid-sentence truncation** (the central finding below).
- Headword-spacing artifact (~451 entries): the body's leading capital letter is glued into the bold span, e.g.:

```
<strong>FOREST H</strong> ebrews ya'ar…
```
Pre-existing ingest quirk, NOT strip damage; word stays readable; lower-priority cosmetic.

**Confirmed thin/raw (after false flags removed).**
- **1,431 of 3,779 bodies (37.9%) are truncated mid-sentence** by a ~540-char hard length cap applied at the original Easton's ingest, with a literal trailing `…` baked into the store. All 1,431 cluster at 529–562 chars (mean 542, stdev 4.2); non-truncated bodies have a completely different distribution (min 80, mean 284). The 17 near-cap entries lacking an ellipsis all end on clean sentence punctuation, confirming the cut is the cap, not random.
- Verified directly in `content/notes/gen.py`: **LAMECH (gen 4:18b)** ends `(2.) The seventh in descent from…`; **RAMESES (gen 47:11b)** ends `made of Nile mud, sun-dried, some…`. The `…` is in the published content store, **not** a sample-display artifact — which is exactly what the first assessment got wrong (it hedged this as "most plausibly sample-display truncation" and issued PASS without checking the source).
- Other sampled members of the same class (lengths 534–552): NEBO (isa 46:1b), COMING OF CHRIST (1jn 5:20j), CONVERSION (act 15:3c), AVENGER OF BLOOD (2sa 14:7b), FROST (job 37:10d), PROPHET (psa 45:1d), DAN (gen 30:6c), FOREST (ecc 2:6b). These are precisely the multi-sentence encyclopedic articles the kind exists to deliver, delivered incomplete.

False flags correctly rejected: the short name+meaning+ref stubs (TEKEL, ZABBUD, SHOBAI, JANUM, ZABULON) — complete by design; and the headword-spacing artifact — correctly attributed to ingest, not the strip.

**Note for the implementer.** The strip is clean — do not re-check for `<em>`/`[Reviewer]`/`TODO` remnants. The **blocking** issue is unrelated to the strip: a body is truncated iff its `.rstrip()`-ed string ends with `…` (1,431 such, 37.9%). Fix = re-ingest Easton's full articles with the ~540-char cap removed (or raised well above 562) so complete entry text is stored, then re-run. The ~451-entry headword-spacing bug can be fixed in the same re-ingest pass but is non-blocking. Do **not** "fix" the short stubs — they are complete by design.

## 4. Overall read

**Do the auto-notes read well now?** Mostly yes — and the strip is the clean part. **The RX Phase 1 scaffold strip was clean across all six kinds: zero strip artifacts, zero orphaned text at the strip seam, zero unbalanced markup, zero `[Reviewer:]`/`TODO`/`[Editor]`/`<em>` remnants anywhere** (verified at full on-disk population for every kind, not just the 32-sample slice). On the narrow question RX Phase 1 was built to answer, all six kinds pass.

Two kinds are flat-out publishable as-is: **lang-hebrew** and **xref-citation** are clean on every axis. The other four read well *for the common case* but carry **pre-existing ingest/source defects the strip neither caused nor fixed** — and three of those were only visible by scanning the full store, because the 24-spread + 8-shortest samples happened to contain none (topic-nave, topic-torrey) or were rationalized away without a source check (dict-easton). The single most important correction: **dict-easton is NOT publish-as-is** — 37.9% of its bodies are silently truncated mid-sentence in the store, which the sample-only first pass missed.

Net: the strip succeeded; publishability is gated by older ingest bugs, not by anything RX Phase 1 did.

## 5. Prioritized findings

Real strip-damage first, then genuinely-thin clusters. **All strip damage = none, everywhere.** The items below are pre-existing ingest/source defects surfaced by the audit; each lists class size + an *audit-only* suggestion (no edits were made).

**Strip damage (all kinds): NONE.** Verified clean at full population for all six kinds. No strip remediation is required for any kind.

Genuinely-thin / broken-for-purpose clusters, ordered by impact:

1. **dict-easton mid-sentence truncation — 1,431 bodies (37.9%). [BLOCKING for this kind.]** Hard ~540-char ingest cap severs the longest, most substantive articles and stores a literal `…`. Suggestion: re-ingest Easton's with no length cap (detect via `.rstrip()` ending in `…`); verify against `gen.py` LAMECH/RAMESES. Audit-only — no edit made.
2. **lang-greek Theós head-drop — 1,196 bodies (100% of θεός).** Every θεός gloss reads only `figuratively, a magistrate; by Hebraism, very.`, dropping the primary "God" sense. Suggestion: track a source re-extract; greppable via the lone `figuratively,`-leading gloss shape.
3. **topic-torrey ref-dump leak — 596 bodies (2.74%).** A scripture cross-reference list leaked into the topic field (worst: 2jn/3jn 1:1c at 7,160 chars). Suggestion: scan for book-name + `\d+:\d+` after `appears under: `; re-check other ingest-heavy kinds for the same leak.
4. **lang-greek Phōs paren-imbalance — 76 bodies.** Dangling `)` + etymology/cross-ref fragment leaking into the gloss. Suggestion: grep `compare G5316 (φαίνω), G5346 (φημί))`.
5. **topic-nave description-as-heading — 87 bodies (22 phrase-only, 75 with `against..` doubled period).** Mis-parsed Nave sub-entry sentence captured as a topic heading. Suggestion: prefer a root-cause heading-vs-description discriminator over patching instances.

Cosmetic / non-blocking (noted, not prioritized): topic-nave & topic-torrey verbatim-repeated labels (~11% of Torrey); topic comma-delimiter ambiguity; dict-easton headword-spacing glue (~451); xref-citation TSK book-label abbreviations vs canonical codes (65 labels). These are presentation/source-fidelity nits, not fitness failures.

**Terse-by-design brevity is NOT a defect.** The short bodies that dominate five of the six kinds — single-topic Nave/Torrey indexes (54–55 chars), one-word Strong's H/G glosses (52–54 chars), single-ref TSK citations (88 chars), and Easton's name+meaning+ref stubs (`TEKEL weighed (Daniel 5:27).`) — are **complete, correct, publishable** content. They were explicitly checked and must not be penalized for length. The genuinely-thin items above are *broken or truncated*, not merely short.

## 6. References

Public-domain sources underlying the six auto-note kinds:

- **topic-nave** — *Nave's Topical Bible*, Orville J. Nave (1896). Public domain.
- **topic-torrey** — *The New Topical Textbook*, R. A. Torrey (1897). Public domain.
- **lang-hebrew / lang-greek** — *Strong's Exhaustive Concordance*, Hebrew & Greek dictionaries, James Strong (1890). Public domain.
- **xref-citation** — *The Treasury of Scripture Knowledge* (TSK), R. A. Torrey et al. (1880s). Public domain.
- **dict-easton** — *Easton's Bible Dictionary*, Matthew George Easton (1897). Public domain.

---

*Read-only audit produced 2026-06-06 (Mac lane) by a verified multi-agent pass (run `wf_c99c416d-69f`): 6 auto-note kinds, purpose-aware sampling (24 spread + 8 shortest each), each assessment adversarially critiqued (which caught + corrected false flags and one fabricated detail). **Audit only — no `content/notes/` were edited.** Companion to RX Phase 1 + `docs/superpowers/plans/2026-06-05-epub-reading-experience-overhaul.md`.*
