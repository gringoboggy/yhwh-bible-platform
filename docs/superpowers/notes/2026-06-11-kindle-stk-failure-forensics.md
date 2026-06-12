# Send-to-Kindle 2nd failure (~50 min crunch) — artifact forensics (K-KIN round 2)

**Status:** 2026-06-11, Mac turn 71. The user's Send-to-Kindle RETRY of
`Ethiopian_Bible_catholic-study_kindle-safe_2026-06-10T224859Z.epub` failed
again after ~50 minutes — twice now at the same ~50–60 min mark. NOT the fast
(4–5 min) validation class the turn-69 E3013 fix cleared; a late, DETERMINISTIC
failure deep in the KFX conversion. Full artifact inventory + limits research
run this session (27-tool agent pass; epubcheck re-verified 0/0/0/0 locally).

## Inventory headline (the scale picture)

25.2 MB zipped / 86.9 MB unzipped · 303 XHTML pieces (302 spine) · 102,986
`id=` anchors · 112,498 `<a>` (111,456 internal; 0 broken) · 42,885 noterefs ·
44,767 asides · 30.85M stripped text chars, **24.77M (80.3%) under `hidden=""`
wrappers** · 67 JPEG (10.3 MB) · 4 TTF, no obfuscation · nav 83 links ·
ncx 76 navPoints (all target non-body elements — passes the known STK
NCX-reject class) · no SVG/MathML/data-URIs/fixed-layout/DRM.

## Ranked causes

1. **Hidden-text counter ambiguity (HIGH, cheap to kill).** Amazon's published
   guideline: display:none on a content block >10,000 chars = hard publishing
   error. Our kindle CSS overrides the hides via author display:block
   (last-rule-wins — epubcheck-green, gate-5-green at 955 chars *in the
   effective-CSS model*), BUT the artifact still physically carries
   `hidden=""` on all 284 note wrappers, and **3 odd-template pieces
   (`index_split_014/028/031.html`) wrap 680 live popup targets in
   `<section class="verse-refs-section" … hidden="">` blocks of 278k/243k/171k
   chars** — the fix-the-class escape from the turn-69 `.notes-section` patch.
   If Amazon's opaque counter keys the raw attribute (or first-rule, not
   last-rule), we are 17–28× over their cap. → **Fix shipped this slice:
   `apply_kindle_unhide` strips `hidden=""` from footnote wrappers post-split;
   gate 5 now fails any kindle artifact carrying one.**
2. **Wall-clock timeout on a dictionary-class link graph (HIGH, co-leading).**
   ~112k links/103k ids/43k popup pairs is ~100× a trade ebook; kindlegen-
   lineage tooling is documented superlinear at this scale (12h+/OOM on a 452k
   dictionary). The twice-at-~50-60-min shape fits a service cap. Cannot be
   fixed by polish — only by reducing the graph (bisect rungs below).
3. Popup-footnote machinery per se (subset of 1+2, own bisect rung).
4. Per-file size (136 pieces >300 KB; `topical.xhtml` 1.98 MB) — perf
   guidance only, LOW.
5. Raw size — well inside 200 MB STK cap, VERY LOW.

## One-variable bisect ladder (each rung STK-valid; built by zip rewrite)

0. **Kindle Previewer 3 = the local oracle** (same conversion pipeline;
   ~minutes per trial and it NAMES the E-code). **Undeclared install — needs
   user GO** (guard #1), exactly like the Java install.
1. **UNHIDE** — strip all `hidden=""` + flip the 2 CSS hides (now in the
   builder via `apply_kindle_unhide`; rebuild rather than rezip). Pass ⇒
   hidden-text gate was the killer.
2. **DELINK** — noterefs→spans, asides→divs (text constant, links
   111k→26k). Pass ⇒ the anchor/popup graph chokes the converter; sub-bisect.
3. **HALF-SPINE** — front/back 151 pieces. Both pass ⇒ aggregate timeout;
   one fails ⇒ recurse to the poison file.
4. **Poison-file probes** — stub topical.xhtml; drop the 3 verse-refs pieces.
5. **Asset drops** — images/fonts/ncx (lowest prior).

## Collateral findings (not kindle-specific — logged for triage)

- **★1,598 orphan `vnote` asides never referenced by any noteref** (2 Esdras
  944 · 1 Esdras 448 · Add-Esther 205 · Esther 1): their inline noterefs were
  never emitted. Real user-facing defect in every edition (unreachable
  popups) + dead hidden content. Owner: the popup generator / inject lane —
  needs its own arc (why did the Esdras/Esther bake skip the markers?).
- `page_styles.css` orphan (12 B, in zip, in no manifest — epubcheck 5.x
  USAGE class). Cosmetic; fold into any build_epub touch.
- All 44,483 leaf asides are bidirectionally back-linked (KDP requirement) ✓.

## Source pointers

Amazon Kindle Publishing Guidelines PDF (10k display:none cap) ·
kdp.amazon.com hyperlink/enhanced-typesetting pages · STK email/web caps
(200 MB web) · MobileRead t=357851 (the kindlegen hidden-chars error on an
STK-failing book) · kindling (reverse-engineered kindlegen superlinearity).

## RESOLUTION (Mac turn 77, 2026-06-11 — driver isolated by the local oracle)

Two blockers, both named and closed/isolated by the Kindle Previewer 3 oracle:

**Blocker #1 — TOC husk class (E24010 ×3 → E24001): CLOSED in-build.**
Splitter `_BP_TITLEPAGE_RE` class-keying + `retarget_demoted_toc_anchors` +
gates 4k/4l; the 163704Z rebuild shows ZERO TOC errors.

**Blocker #2 — the generic no-E-code internal error: driver = RAW HTML
CONTENT VOLUME** (converter work), NOT any construct. Full one-variable
matrix (each probe epubcheck 0/0/0/0; verdicts in `~/kp3-runs/<dir>`):

| probe | docs | zip | raw HTML | verdict |
|---|---|---|---|---|
| full 163704Z | 297 | 23.9 MB | 72.8 MB | ✗ generic |
| delink (links 112k→26k, asides→divs) | 300 | ~24 MB | ~72 MB | ✗ generic |
| half-first | 149 | 18.5 MB | ~36 MB | ✓ ET Supported |
| half-second | 148 | 16.1 MB | ~36 MB | ✓ ET Supported |
| 2MB-split (202205Z) | 182 | 23.6 MB | 72.8 MB | ✗ generic |
| **no-split** | **63** | **23.4 MB** | **71.2 MB** | **✗ — doc-count DEAD** |
| **imgstrip (rasters→1×1)** | **63** | **13.8 MB** | **71.2 MB** | **✗ — zip-mass DEAD** |

Threshold ∈ (≈36.5, 71.2) MB raw — `--keep 0:49` (55.2 MB) bracketing rung
in flight. Hypothesis #2's "superlinear/service cap on the graph" was half
right: the cap is real but keys on total content volume, not the link graph
(delink failed identically). Hidden-text (#1) and per-file size (#4) dead.

### Apparatus composition (the ship-knob census; chars — raw bytes ~17% higher)

60.8 MB content = **12.4 MB scripture+frames** + **37.8 MB per-verse
parallel-source popups** (33,969 `vnote` asides: labels 10.1 — "Hebrew
(Masoretic / WLC)" ×119,625 repeats — Hebrew 6.0 · Arabic 5.2 · Vulgate 4.6 ·
Greek 3.9 + 1.1 NT · headers/wrappers 6.9) + **10.6 MB chapter-end notes**
(Easton 3.7 · xref 2.1 · comm-ethiopian 1.0 · comm 0.7 · Heb/Grc lang 0.8 ·
rest <0.5).

### Ship options (presentation-configurable; user pick at the seam)

- **(A) Two-volume kindle** — halves PROVEN passing with full apparatus +
  live popups; the only 100 %-content option.
- **(B) Popup compaction, zero content loss** — compact source labels
  (~10 MB) + verse headers (~few MB); may alone clear a high threshold.
- **(C) Per-language popup knob** — e.g. kindle drops Arabic/Vulgate
  (~7–8 MB each with labels), keeps Hebrew+Greek.
- (B)+(C) compose; threshold bracket decides how much is needed.
