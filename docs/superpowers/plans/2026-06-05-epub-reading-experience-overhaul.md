# EPUB Reading-Experience Overhaul — master program plan

**Date:** 2026-06-05
**Status:** program plan — Layer A (discovery) → Layer B (implementation) → Layer C (Mac lane). Awaiting user go on Layer A.
**Origin:** 2026-06-04 Kobo COLOR e-reader device QA ([[kobo-color-ereader-end-stage-qa]]) + the user's note that the *intended* note display was designed but never built.
**Spec lineage:** `specs/2026-05-24-epub-presentation-polish-design.md` (§4.1 `marker_style=badge` was **deferred / never implemented** — confirmed by the user as the intended display) + this program's new findings.

> **Hard constraint (user, 2026-06-05): every note and every feature stays ON.**
> We declutter and speed up by *how* content is shown (badge mode, structure,
> fonts, file-splitting), never by dropping notes. Quality/completeness over
> speed (RULES §2; [[project_deadline]]).

---

## 0. Problem inventory (device QA → root cause)

The v27 EPUB the user loaded = `Ethiopian_Bible_ethiopian-tewahedo_v27_2026-06-04` (24 MB zip / **99 MB uncompressed / 61 HTML files @ 2–3.4 MB each**). All root causes below are verified against the real EPUB + the codebase.

| # | Symptom (device) | Root cause | Lane |
|---|---|---|---|
| 1 | Notes read like drafts (every popup) | **`<em>[Reviewer:…]</em>` in 88,773 / 91,733 notes (96.8%)** — `detectors.py` embeds the scaffold in `body`; `promote` never strips it. Baked into BOTH `content/notes/*.py` (source) and `epub_working/index_split_*.html` (base) | **1** |
| 2 | "too cluttered" (Apple + Kobo) | `marker_style=numbers` = one inline marker **per note** (~93 in Genesis 1). The intended `badge` mode (one badge **per verse** → tap → note list) was deferred | **2** |
| 3 | Kobo "horrendously slow / crashes" | 99 MB uncompressed; 2–3.4 MB per HTML file; e-ink CPU can't reflow it | **3** |
| 4 | Kobo: "nothing pops up" | aside/footnote popup markup likely not in Kobo's required form + file size | **3** |
| 5 | Kobo: book title pages show no art | art IS embedded (66 jpg) but the `full-bleed` `position:absolute` overlay defeats Kobo's engine | **3** |
| 6 | Apple: title art shows but misaligned | `full-bleed` title panel `position:absolute; bottom:7%` over a variable-height image | **3** |
| 7 | Kobo: original-language font tiny | **no Hebrew/Greek font embedded** (font-subset embedding was deferred); Kobo falls back to a tiny/absent glyph | **3** |
| 8 | Apple: note text overflows box width (worst in early chapters) | `.note`/`.vnote` lack `overflow-wrap:break-word`; long Hebrew tokens + ref-chains can't wrap (densest in early Genesis) | **3** |
| 9 | Apple: blue "│" bars beside words | known Apple Books artifact — `.vn` still uses `vertical-align:super; line-height:0` (the CSS documents this exact bug for markers but never fixed it for verse numbers) | **3** |
| 10 | Apple: expand a book low on the page → whole book + pills jump to next page | `page-break-inside:avoid` on the expanded chapter-pill list in a reflowable flow | **3** |
| 11 | Kobo: TOC "messed up" | custom TOC uses `<details>/<summary>` + flexbox, unsupported on Kobo's engine | **3** |

**Three lanes:** (1) content scaffold strip · (2) the badge reading redesign · (3) cross-reader device polish.

---

## 1. Confirmed decisions (user, 2026-06-05)

1. **Badge mode is the intended display** — clean scripture text, **one note-count badge per verse**, tap → that verse's notes as a list. (Spec §4.1 `badge`.)
2. **Strip the scaffold the professional way** — remove the `[Reviewer:…]` span from every note (the underlying TSK / Strong's / Easton / Nave / Torrey content is a complete note without it), fix the generator + promote so it can't recur, and add a guard.
3. **All notes + all features ON.** No content reduction. Badge mode + structural fixes carry the declutter/perf load.

---

# LAYER A — Discovery plan ("what I need to figure out")

Read-only investigation, grounded in the extracted EPUB (`C:\Users\bogda\AppData\Local\Temp\kobo-epub-x`) + the codebase. Each task ends in a written finding that feeds Layer B. Best run as one parallel discovery workflow (ultracode), MAX-appropriate fan-out, no file mutation.

- **D1 — Badge injection point (unblocks Phase 5, the centerpiece).**
  Map the base-HTML per-verse structure (where `.vn` / `vn-link` / `ch-anchor` / verse boundaries sit) and `scripts/inject.py` (`build_marker` ~150, `build_aside` ~170). Decide: where a per-verse **note-list container** is injected and where the **verse-end badge** anchors; how notes group by `(book,chapter,verse)`; how badge mode coexists with / replaces the current per-note aside popups; OPF/nav impact. **Output:** concrete injection design + exact functions + risks + a base-regen vs surgical-edit recommendation. (Spec §10 open item — resolve it here.)
- **D2 — Cross-reader popup mechanism (fixes #4, hardens #2).**
  Inspect the current aside markup in `index_split_*.html` (is it `epub:type="noteref"`+`aside epub:type="footnote"`? Apple-only `<a>`+`<aside>`?). Determine the **cross-reader popup pattern** that works on Apple Books AND Kobo AND Google Play Books. **Output:** the canonical popup markup + what inject must emit.
- **D3 — Kobo structural rendering (fixes #5, #6, #10, #11).**
  Confirm Kobo's handling of `<details>/<summary>`, flexbox, `position:absolute`/full-bleed, embedded fonts, and large files. Decide the **Kobo-safe TOC** (static, always-expanded or per-book chapter list — no `<details>`/flex) and the **framed title-page fallback**. **Output:** per-issue Kobo-safe markup/CSS.
- **D4 — Performance / file-size (fixes #3).**
  Trace how `index_split_*.html` is chunked (`scripts/web.py` file-split / `build_edition`). Quantify: post-strip size, feasibility + cost of smaller splits, per-file target for e-ink. **Output:** a size-reduction plan with expected MB.
- **D5 — Font embedding (fixes #7).**
  The `patch_opf_fonts` pattern (`build_edition.py` ~2407). Pick **OFL-licensed** fonts that cover the scripts and are redistributable: **Cardo** (Latin+Greek+Hebrew, OFL) as the prime candidate; **Abyssinica SIL** (Ethiopic, OFL) for the standalone Bibles. Subset + size budget. **Output:** font choice + embedding plan + license note for `ATTRIBUTIONS.md`.
- **D6 — Full scaffold-leak surface + root cause (locks Phase 1 scope).**
  Beyond `[Reviewer:…]`, scan shipping bodies for every editorial-placeholder pattern (`[TODO`, `[Editor`, `[AI…`, bare "before promoting", placeholder URLs, etc.). Confirm the 8 `detectors.py` embed sites + the `promote_candidate` path. **Output:** the complete leak inventory + the exact strip regex set + the generator/promote fix + the lint-guard spec. (Note: `detectors.py` 178/346 already use a separate `reviewer_notes=` field — the fix pattern is "guidance goes in `reviewer_notes`, never in `body`.")

Discovery exit: every Phase below has a concrete, file-level design; no "TBD."

---

# LAYER B — Implementation plan ("how to implement it")

Subagent-driven TDD. Each phase: failing test → implement → **bake-and-prove gate** (where the base changes) → epubcheck 0/0/0/0 on representative editions → `ebible verify` errors=0 → nested-anchors 0/N → lint/mypy/ruff → save (5-leg) → where a device behavior changed, the user re-tests on the Kobo. Phases ship independently. Per RULES §3, ordered safest/most-foundational first.

### Phase 1 — Strip the scaffold + stop the leak (Lane 1; **unblocked, start first**)
- One-shot strip over `content/notes/*.py` **and** `epub_working/index_split_*.html` in lockstep (regex from D6; `\s*<em>\[Reviewer:[^<]*</em>` family). Prove source-strip + base-strip leave identical, well-formed bodies.
- Root-cause fix: `detectors.py` — move every `<em>[Reviewer:…]</em>` body embed into the existing `reviewer_notes=` field (8 sites); `promote.py` — defensively strip any residual scaffold at promote time.
- **Guard:** a `lint_rules.py` check (+ a test) that FAILS if any shipping note body contains an editorial-placeholder pattern → can never recur (RULES §12 "fix the class + add the guard").
- Gate: nested-anchors, `ebible verify`, rebuild flagship + a canon-shape set, epubcheck 0/0/0/0; **byte-diff proves only the scaffold spans changed**. Expected: ~−8–10 MB EPUB.
- **Visible win on every device immediately; also shrinks the Kobo file.**

### Phase 2 — Cross-reader CSS quick wins (Lane 3a; low risk)
- `.note`/`.vnote`: add `overflow-wrap:break-word` + `hyphens` (fix #8).
- `.vn`: replace `vertical-align:super; line-height:0` with explicit baseline-shift (fix #9, the blue "│" artifact) — mirror the already-correct `.verse-num-sup`/`.note-ref sup`.
- Verify on Apple + Kobo (user). Pure CSS; pin new output.

### Phase 3 — Embed original-language fonts (Lane 3b; fixes #7)
- Embed an OFL subset (D5: Cardo for Heb/Grk/Lat; Abyssinica SIL for Ethiopic on standalones) via `patch_opf_fonts`; point `.vnote-hebrew`/`.vnote-greek` (and body) stacks at the embedded family. Update `ATTRIBUTIONS.md`.
- Gate + device re-test (originals legible on Kobo).

### Phase 4 — Kobo structural fixes (Lane 3c; fixes #3, #4, #5, #6, #10, #11)
- Cross-reader popup markup (D2) so popups open on Kobo.
- Kobo-safe **static TOC** (D3) — no `<details>`/flex; keep the rich TOC for Apple via progressive enhancement or ship the safe one everywhere.
- **Framed** title-page fallback (D3) so art renders on Kobo + aligns on Apple; reconsider the full-bleed default.
- **File-splitting** (D4) — smaller `index_split_*` for e-ink performance.
- Gate + device re-test (opens, scrolls, art shows, TOC works on Kobo).

### Phase 5 — Badge reading mode (Lane 2; the centerpiece, depends on D1)
- Implement `marker_style=badge` (spec §4.1 / §9 Phase 3): per-verse note container + one verse-end count badge → tap → note list. Make it the **default** for the standard editions; `numbers` stays available.
- This is the real cure for "too cluttered" **with every note ON** (~93 markers/chapter → ~31 verse badges). Needs a base re-bake (D1) → full gate + device re-test.
- Its own detailed TDD sub-plan (`plans/2026-06-05-badge-marker-mode.md`) written from D1 before executing.

**Program gate (end):** all 11 editions + 2 standalones rebuilt, epubcheck 0/0/0/0 each, `ebible verify` errors=0, lint/mypy/ruff clean, the 9 KJV editions' *non-targeted* output byte-stable (this work intentionally changes presentation — pin the NEW output, categorize-diff the rest). Final user device pass on the Kobo + Apple Books.

---

# LAYER C — Mac-lane parallel task ("meanwhile")

**File-disjoint, research/doc output — zero overlap with the Windows build-pipeline + content work.** Hand off via the baton system (`/handoff to-mac`); Mac reads this section.

**MAC TASK — Cross-reader EPUB compatibility research → reference doc.**
Produce `docs/superpowers/notes/2026-06-05-eink-epub-compat-research.md`: how **Kobo** (esp. color e-ink), **Apple Books**, and **Google Play Books** each handle the features this overhaul depends on — (a) EPUB3 popup footnotes (`epub:type="noteref"`/`"footnote"` + `<aside>`), (b) `<details>/<summary>`, (c) flexbox, (d) embedded fonts (`@font-face`, formats, subsetting), (e) `position:absolute` / full-bleed images, (f) large single-file performance, (g) any Kobo-specific markup (`kobo:` spans, the KePub vs vanilla-EPUB distinction). For each: supported / partial / unsupported + the recommended cross-reader-safe pattern + citations. **This directly de-risks D2/D3/D4/D5** and lets Windows implement against evidence, not guesswork. Pure web research + a doc — no code.

**Mac secondary (if it finishes / prefers):** finish the **owed Apple notarization** (`dist/YHWH-1.0.0-beta.1.dmg` is built+signed; re-attach + staple + verify + regen checksums — command in IN_FLIGHT) once Apple's notary service has recovered. Also disjoint.

---

## Risks & invariants
- **Base re-bake is lossy for harvested popups** (SESSION_PLAYBOOK §7 warns) — Phase 5 must use the surgical re-bake, not a bare regen.
- **`editions.yaml` is SHA-guarded** — back up + restore + `cache_clear()` in any mutating test.
- **Two-lane baton** — only the holder pushes; Mac's doc + Windows' code are disjoint, baton-sequenced at any standalone/editions.yaml touch.
- **Byte-stability posture flips for this arc** — presentation intentionally changes; pin NEW output, prove non-targeted parts unchanged.
- **Phase 1 can start before Layer A finishes** (it only needs D6, the quickest discovery item).
