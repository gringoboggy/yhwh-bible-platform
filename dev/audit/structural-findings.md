# Structural + content EPUB audit — findings (WIN BIG-batch ①)

**Mac lane · 2026-06-23 · `dev/audit_book_structure.py` run across 5 built editions.**
This is the "final rendered product" structural test the code-only deep-audit cannot do:
a deterministic verse → chapter → book → out-of-book walk on the actual built EPUBs.

## Result

**293 / 294 books green across 5 editions** (1 real FAIL, 17 acceptable versification-gap
warns, 0 other false-positives).

| Edition | format | books green | notes |
|---|---|---|---|
| catholic-study | epub | **72/72** | clean (1 Sirach verse-gap warn) |
| eastern-orthodox | epub | **75/75** | clean |
| evangelical-reformed | epub | **66/66** | clean |
| ethiopian-tewahedo (superset) | epub | **76/77** | ⚠ **1 FAIL: `1en`** (see below) |
| standalone-geez | epub | **4/4** | clean (own-vers Psalter gap warns) |

**KEPUB pass — DONE (kepubify v4.0.4):** all 5 editions converted to `.kepub.epub` and re-audited →
**293/294 books green, byte-for-byte the same result as epub** (same per-edition counts, the same single
`1en` FAIL, the same 17 versification-gap warns). Confirms kepubify's Kobo `kobo.*` span injection (which
the auditor already ignores via its `kobo.` id filter) does NOT perturb book/chapter/verse structure —
structure is format-invariant across epub and kepub.

## ⚠ The 1 real FAIL → for WIN (content / base-HTML, not the auditor)

**`1en` (1 Enoch) in `ethiopian-tewahedo` — verse anchors physically out of order:**
- `1en 71`: doc order `[1..13, 46, 14, 15, 16, 17]` — **verse 46 is misplaced** between v13 and v14.
- `1en 90`: doc order `[1..13, 16, 14, 17, 15, 18, 19, …]` — **v14–17 are scrambled** (16 before 14, 17 before 15).

Verified by reading the rendered `v-1en-71-*` / `v-1en-90-*` anchor sequence in the built epub
(not an auditor artifact — the auditor's verse-order check is correct; these anchors are genuinely
out of sequence). ch71 and ch90 sit in the **1En 37–108** range, which `project_build_architecture`
records as the **~161-marker inject residual** (the boundary-aware spill resolver + canonical-
coordinate guard place 99.76%; 1En 37–108 is the known tail). So this is most likely a manifestation
of that known-deferred residual rather than a new regression — **WIN to confirm known-deferred vs
fixable** (it only affects the ethiopian-tewahedo superset; the 4 canon-filtered catalog editions that
exclude 1 Enoch are clean).

## Warns (17) — acceptable, NOT failures

All 17 warns are `missing verse number(s)` — recovered-base **versification gaps** (the auditor
treats a gap as a WARN by design: "recovered-base versification has known holes; a DUPLICATE is a
FAIL"). Examples: catholic `sir 26` missing 20–26 (Sirach numbering divergence); standalone-geez
`psa 17/21/36/41/59/68` missing scattered verses (the Ge'ez Psalter's own-versification: superscriptions
counted differently). 0 spurious-page-break warns, 0 missing-title-frame warns, 0 unresolved-href fails,
0 duplicate-marker fails.

## Auditor calibration applied this round (the `dev/` tool — ①a + ①b)

`dev/audit_book_structure.py` was authored-but-UNRUN; running it surfaced its own gaps, all fixed so
the findings above are 0-FP:

1. **2nd badge emitter (`_NOTEREF_RE`)** — the auditor only knew the collapsed `verse-notes-badge`;
   added the per-note `note-ref note-{kind}` marker (numbers mode) + a **duplicate-marker-id** check
   (the generic href pass can't catch a dup id that still resolves). *(①a)*
2. **Chapter-heading detection** — `_CH_HEADING_RE` matched only `<a id="ch-b#-c#">`, so every
   file-split-boundary chapter (whose `ch-b#-c#` id lives on the `<p class="ch-heading">` itself, not a
   standalone `<a>`) false-warned "no chapter heading." Now matches the id on **any element** →
   **eliminated 162 false warnings**.
3. **Folded deutero-additions** — `{bel,sus,paz}→dan`, `{aes}→est`: a book region carrying ONLY its
   own canonical additions is correct structure, not a "title-page/boundary leak" → **fixed the false
   `dan` FAIL** in every Catholic-canon edition.
4. **Standalone / own-versification fallback** — `build_standalone.py` emits per-chapter
   `geez_{book}_{ch}.xhtml` files with the same `v-{code}-{ch}-{v}` anchors but **no `bp-`/`ch-b`**
   markup; added a fallback that derives book regions from the verse codes and runs the order/gap/dup
   checks (shared `_check_book_order`) → standalone-geez now audits **4/4**.

Also tidied a B905 `zip(strict=)`. `ruff format` clean, compiles, `ruff check` clean except a pre-existing
non-blocking SIM115 (`zipfile.ZipFile` without a context manager, in the original `audit_epub`).

## Follow-ups (next round)

1. **KEPUB pass — ✅ DONE** (see above): all 5 editions, 293/294 green, identical to epub. No action.
2. **`1en` ordering** — WIN: confirm the ch71/ch90 misordering is the known 1En 37–108 residual
   (deferred) or a fixable inject-tail bug.
3. **Per-color** — structure is color-invariant, so one color per edition was audited; no need to fan
   the 5 colors unless a color-specific build path is suspected.
4. **`build_standalone.py` has no CLI `__main__`** — it is import-only (`build_standalone(edition_id,
   output_dir, version)`); a thin `__main__` would make it scriptable like `build_edition.py` (minor
   dev-ergonomics note for WIN).
