# Kobo device-QA — ethiopian-tewahedo eink kepub (2026-06-23)

**Source:** the user (Boggy) read the flagship `ethiopian-tewahedo` `.kepub.epub` on his **color Kobo**
(the real-device oracle — memory `kobo_color_ereader_end_stage_qa`) under his **Cardo** reading font and
surfaced 4 defect clusters. Screenshots: `dev/audit/kobo-qa-2026-06-23-screens/01..10` (descriptive names).
The Kobo is at **`G:`** (`KOBOeReader`) plugged into the WIN box; kepubify v4.0.4 is on this box, so WIN
builds + kepubifies + loads directly. **Sideload filename = `YHWH-koboQA.kepub.epub`** (reuse on-device,
K-R5-1); STANDING rule: **always delete the older version on the Kobo before copying the new one.**

## ✅ FIXES APPLIED — B-1 / C / D (2026-06-23, fresh session)

All actionable clusters fixed at the REAL emitter, traced by ground-truthing the live base
HTML + an empirical Cardo cmap check (not trace-agent line numbers). 14 unit pins green
(`tests/test_kobo_device_qa.py`); verified against the BUILT eink kepub by grep — the grep is
what surfaced the 4th + 5th B-1 surfaces (legend + book-page ornament) the source-read missed.
**Gates:** built-epub grep = ZERO Cardo-missing glyphs anywhere · `verify_kr2_build` ALL K-R2
GATES GREEN (the W7 >500KB piece WARNs are the known/deferred char-vs-byte item, all <Kobo's
881KB break) · **epubcheck 0/0/0/0** — but only after it caught a real **CSS-001**: my first D
cut added `.vnote-arabic { direction: rtl }`, and the CSS `direction` property is forbidden in
EPUB 3 stylesheets (the base sheet sets RTL via the inline `dir="rtl"` attribute — the Arabic
markup already carries it). Dropped `direction`, kept `text-align:right`; re-validated 0/0/0/0.
A `test_eink_css_has_no_forbidden_direction_property` pin now guards the class.
**Root cause of the prior "didn't land": build-cache masking** — `build_edition.py` short-
circuits to `cache_lookup` UNLESS `--force` (L7364 `… and not force`). Always `--force` +
grep the output. The fixes (all eink-only → the 9-KJV byte-stable editions are untouched):

- **B-1 (invisible badges) — 5 surfaces, all Cardo-safe.** Empirical Cardo cmap
  (`content/assets/fonts/Cardo-Regular.ttf`): **✧ ⌂ ⌇ ◇ ⚖ ⊛ ❑ ❖ ✦ are ABSENT**. The 4
  category-glyph surfaces now resolve through ONE shared map — `scripts/core/eink_glyphs.py`
  (`eink_category_badge_glyph`), imported by both the emitters and the legend so the key can
  never drift from the body: (a) inline badge (`comm ◇→◊`, U+25CA, in Cardo + Kobo default);
  (b) cascade headers (`cat_meta`, was raw categories.yaml — 4 of ethiopian's 6 categories
  blank); (c) per-note `note-sym` (the biggest — topic `✦` recurs ~825×/chapter-file; new
  `_eink_safe_note_sym` at the row-build site); (d) the **symbol-legend page** (`matter_pages
  .render_symbol_legend_page` — grep caught it still showing `◇/✦`, which would have left the
  key inconsistent with the now-`◊/*` badges). The old design comment "headers keep full
  symbols" was superseded — the user reads with Cardo, so blank boxes win nothing.
  (e) the **book-page ornament** `<div class="bookpage-rule">❖</div>` (baked, blank on every
  book page) → Cardo-safe fleuron `❦` via the eink-only `apply_eink_bookpage_ornament` pass.
- **C (redundant note-body boiler):** new `_strip_redundant_body_boilerplate` (anchored
  `<strong>Dictionary (…).</strong>` 3,779× / `<strong>Topics.</strong>` 48,097× in the live
  base) hooked into the S1 `note_attribution_dedup` block. Lossless — headword / "appears
  under:" list survives; stat `s1_body_boiler_stripped`.
- **D (popup formatting):** `.vnote-kobo-sep`, `br.kobo-vnote-br`, `.vnote-vulgate`,
  `.vnote-arabic` added to the eink-only `_EINK_READER_CSS` (Hebrew/Greek/Geez/Amharic were
  already styled in the base sheet). Scoped to eink for byte-stability; the base-sheet
  Vulgate/Arabic gap (non-eink editions) is a flagged grand-audit follow-up, not a buried edit.

**A** (mid-chapter page-break) + **B-2/B-3** stay deferred per below (A → char-vs-byte re-cut;
B-2/B-3 → repro / `dev/HUMAN_DECISIONS.md`).

## ⚠ CRITICAL METHODOLOGY LESSON (why this is a tracker, not a fix)

A `deep-audit`-style root-cause trace (4 agents) was run and its file:line claims were **wrong on all
three paths it covered** — and I (the parent) compounded it by editing those locations and *only then*
rebuilding. The rebuild proved **none of the 3 fixes landed** (badges still `◇`, boilerplate still present,
CSS not shipped). **The rule for the fresh session: for every fix, trace to the REAL emitter, change it,
rebuild WITH THE BUILD CACHE CLEARED, then grep the built EPUB to confirm the change landed BEFORE reloading
the Kobo.** No blind patches. (The wrong edits were reverted; tree is clean.)

There is a **`build_cache`** (keyed on theme/CSS hashes — see W3b / `test_build_cache.py`) that may have
served a stale render — so a glyph/markup edit can look like a no-op when it's really cache-masked.
**First thing to establish: does `build_edition.py ... --force` clear the render cache? If not, clear it
(or find the flag) before concluding a fix is ineffective.**

## The 4 defects

### A — Page breaks (gen10.6→10.7 mid-chapter; gen3.24→ch4)  [DEFER / careful]
Screens 07–10. On Kobo eink kepub, CSS page-break props are ignored; breaks come from **spine-file
boundaries**. Verified: Gen 1–3 is one split file, Gen 4–10 share the next, so **gen3.24→ch4 is a file
boundary (a legitimate chapter-boundary split)** but **gen10.6→10.7 is MID-FILE** (different cause). The
trace's "Calibre splits at 850 KB" is **wrong** — `verify_kr2_build` shows pieces max ~450 KB, i.e. the
build's own `apply_file_split`/packer chose the cut. **Fixing the mid-chapter cut re-cuts the file-split,
which is the byte-stability-critical char-vs-byte item (the deferred round-13 HIGH).** Do this with the
char-vs-byte work, not as a one-off — it changes piece boundaries on every edition. Real loci to trace:
`build_edition.py` `split_html_document()` / the packer (the K-R15b verse-merge rule); confirm whether the
eink edition actually runs `apply_file_split` (grep `reader_file_split` in `editions.yaml` — it was NOT
obviously set for ethiopian-tewahedo, yet pieces are ~450 KB, so something else splits — RESOLVE THIS).

### B — Badges  [B-1 ready · B-2 defer · B-3 needs repro]
- **B-1 (invisible badges) — the user's biggest concern.** Empirically (from the built epub) the inline
  study badges are `<span class="marker-badge">GLYPH</span>` whole-Bible (hundreds/chapter). Of the glyphs
  actually used (`* H ◇ ‖ ⌘ †`), **only `◇` (U+25C7, the `comm` category) is ABSENT from Cardo** (fontTools
  cmap-checked) → ~750 comm badges render invisible under Cardo while the rest show. **Fix = replace `◇`
  with `◊` (U+25CA lozenge — in BOTH Cardo and Kobo's Publisher-Default, visually near-identical).**
  ⚠ BUT: editing `_EINK_CATEGORY_BADGE_GLYPHS["comm"]` (build_edition.py ~3187) and rebuilding left the
  output **still `◇` (◊=0)** — so EITHER that map is not the inline-badge source (it may be the
  `categories.yaml` `comm` symbol, OR a baked source) OR the build-cache masked it. **TRACE where the
  inline `<span class="marker-badge">◇` glyph actually resolves** (the `eink_backmatter` branch at
  build_edition.py ~4209 calls `_eink_category_badge_glyph(cat, glyph)` which *should* substitute — but the
  rendered glossary rows in `_emit_backmatter_glossary_inner` use the `cat_meta` glyph = `categories.yaml`
  symbol). Check `categories.yaml` `comm` symbol first. Then fix at the true source, clear cache, rebuild,
  grep: expect `<span class="marker-badge">◊` > 0 and `…>◇` = 0.
  - NOTE: the **backmatter category note-sym links** (`<a class="note-sym">◇/⌂/✦</a>`) use the full
    `categories.yaml` symbols, several of which (`◇ ⌂ ✦ ❖ …`) are ALSO not in Cardo → the study-note
    headings go blank under Cardo too. Same root fix (Cardo-cover the category symbols) cleans both.
- **B-2 (badge spacing)** — DEFER (minor, low-confidence). The inter-badge trail is
  ` ​ ​ ` (build_edition.py ~4253) with `.badge-trail {display:inline}` only. Needs
  a clearer repro of what looks wrong before tuning.
- **B-3 (dagger → wrong "II" note)** — NEEDS REPRO. Could not reproduce (Gen 1:1 `†` resolves correctly).
  **In `dev/HUMAN_DECISIONS.md`: ask the user which verse/page showed the `†` jumping to the wrong "II"
  note.** Without it, can't trace the href/anchor bug.

### C — Redundant note-body boilerplate  [code READY, hook WRONG — re-hook]
Screens 02–03. The leaf LABEL ("Easton." / "Topic") is already dropped by S1
(`_strip_redundant_note_label`, build_edition.py ~2864) — but the note BODY still opens with a redundant
`<strong>Dictionary (Easton's).</strong>` (dict-*) / `<strong>Topics.</strong>` (topic-*) that restates the
category heading + byline. `note_attribution_dedup`/`note_group_by_category` ARE on for ethiopian-tewahedo
(editions.yaml ~46). The user said **strip it** (go-ahead). The CORRECT, TESTED helper (it was reverted —
re-add it):

```python
# build_edition.py — near _strip_redundant_note_label
_DICT_BODY_BOILER_RE = re.compile(r"<strong>Dictionary \([^)]{1,40}\)\.</strong>\s*")
_TOPIC_BODY_BOILER_RE = re.compile(r"<strong>Topics\.</strong>\s*")

def _strip_redundant_body_boilerplate(row_html: str, kind: str) -> tuple[str, bool]:
    """Drop the leading dict-*/topic- body source/topic boiler; keep the real headword."""
    if kind.startswith("dict-"):
        new, n = _DICT_BODY_BOILER_RE.subn("", row_html, count=1)
        return new, n > 0
    if kind.startswith("topic-"):
        new, n = _TOPIC_BODY_BOILER_RE.subn("", row_html, count=1)
        return new, n > 0
    return row_html, False
```
⚠ The earlier hook (after the `_strip_redundant_note_label` call at the S1 row loop ~4068) was INERT — the
backmatter glossary bodies are rendered by **`_emit_backmatter_glossary_inner`** (build_edition.py ~4191),
NOT that row. **Re-hook inside the glossary-inner emitter** (where the `<strong>Dictionary…/Topics.</strong>`
is written), then rebuild + grep: expect `Dictionary (Easton` boiler = 0 and `<strong>CREATION</strong>` /
`This verse appears under` still present. (4-case unit test existed + passed — re-create `tests/test_note_body_boiler.py`.)

### D — Translation popup formatting  [CSS source NOT located — find it first]
Screens 04–06. The Kobo "Footnote preview" stacks Hebrew→Greek→Latin→Arabic with labels but cramped.
Verified markup per language: `<p class="vnote-source-label">…</p><p class="vnote-kobo-sep"> · · · </p>
<br class="kobo-vnote-br" /><p class="vnote-{hebrew,greek,vulgate,arabic}">…</p>`. Hebrew/Greek have CSS;
**`.vnote-kobo-sep`, `.kobo-vnote-br`, `.vnote-vulgate`, `.vnote-arabic` have none** → run-together.
⚠ Editing `epub_working/stylesheet.css` did **NOT** ship — the built `stylesheet.css` (50,652 B) lacked the
classes. **The edition stylesheet is assembled by the `apply_*` appenders** (`apply_eink_reader_css`,
`apply_marker_badge_style`, `apply_note_popup_style`, etc. — build_edition.py ~2243/2387/2441) over a base
that is NOT `epub_working/stylesheet.css` verbatim. **FIND where the shipped stylesheet's base comes from**
(grep the build for where `stylesheet.css` is read/written; the `apply_*` chain) and add the CSS there (or
via a new `apply_*` for eink). Proposed CSS (re-use): muted/tight `.vnote-kobo-sep` + `.kobo-vnote-br` +
`.vnote-vulgate`/`.vnote-arabic` block margins (Arabic RTL). Rebuild + grep the shipped css for the classes.

## Suggested order for the fresh session
1. Resolve the **build-cache** question (does `--force` clear render cache?) — gates all verification.
2. **B-1** (badges) — highest user value; trace the real glyph source, fix, verify ◊ in output.
3. **C** (body boilerplate) — re-hook into `_emit_backmatter_glossary_inner`, re-add the test, verify.
4. **D** (popup CSS) — find the stylesheet assembly, add CSS, verify in shipped css.
5. Rebuild ONCE with B-1+C+D confirmed → kepubify → `verify_kr2_build` + epubcheck → **delete old
   `G:\YHWH-koboQA.kepub.epub` + copy new** → tell the user to eject/reconnect.
6. **A** (page-breaks) — fold into the char-vs-byte re-cut (byte-stability-critical), not standalone.
7. B-2 + B-3 — await a clearer repro / the dagger verse (HUMAN_DECISIONS).

**Byte-stability:** B-1/C change only the eink build's rendered output (eink-only; the 9-KJV byte-stable
gate builds `everywhere`-target editions → unaffected). D touches the shared stylesheet (deliberate) — prove
"only the intended CSS changed" + run the determinism gate. A is the deliberate all-edition re-cut.

## ▶ NEW issues from the 2026-06-24 device read (E / F / Hebrew) — fix next session (verify each on-device)

Full plan + lane split in `.remember/remember.md` + `page-breaks-root-cause-2026-06-23.md`. Summary:

- **A (page breaks) — ROOT-CAUSED + MEASURED, merge VIABLE.** Packer cuts spine files between verses
  (`_VN_LINK_RE`); finder `dev/audit_spine_breaks.py`. Measurement: not sub-splitting kills 129/130
  mid-chapter breaks, Kobo renders ≤6.2 MB merged files fine → implement the per-book merge (drop
  `_VN_LINK_RE` + merge a book's base files; golden re-baseline). 1 WIP in build_edition.py:~5213 (backmatter
  keeps default cap — KEEP).
- **E — study-note back-link popups instead of navigating.** `_study_verse_return_link` emits a bare
  `<a href="#v-…" class="note-back study-return">`; Kobo's K-R12 heuristic popups bare `<a>`. The INBOUND
  badge forces navigate via cross-file `epub:type="noteref"` — give the back-link the same (confirm its href
  is cross-file-rewritten first). Verify on-device.
- **F — category symbol still redundant.** The grouped S2 cascade shows the category symbol in the HEADER
  (`vn-cat-head`→`vn-cat-sym`) AND on every note row (`note-sym`). DROP the per-note `note-sym` in
  `_emit_cascade_sections` (header conveys it). ⚠ SUPERSEDES this session's B-1c note-sym substitution.
- **Hebrew — Cardo does NOT trigger Hebrew on Kobo (user-confirmed).** Cardo has the glyphs + is embedded +
  `.vnote-hebrew` lists it first, but the device renders nothing until Kobo manually supplements a Hebrew
  font → the "removed NotoSerifHebrew" decision was wrong for the device. Re-embed + FORCE `NotoSerifHebrew`
  on `.vnote-hebrew` (re-verify Greek/Arabic too) + put it in TOP-LEVEL `G:\fonts\` (currently mis-placed in
  `G:\fonts\kobo\`). Mac researches Kobo's reading-font-override behaviour first (`kobo-font-override-research.md`).
- **B-2** spacing + **B-3** dagger→"II" still await a clearer repro / `dev/HUMAN_DECISIONS.md`.
