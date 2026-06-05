# EPUB Reading-Experience Overhaul — Layer A discovery findings (resolved design)

**Date:** 2026-06-05 · **Source:** discovery workflow `wf_95b6739a-c67` (6 read-only investigators, grounded in the codebase + the extracted v27 EPUB). Companion to `plans/2026-06-05-epub-reading-experience-overhaul.md`.

## D1 — Badge mode (resolved design)
- Current: per-note inline marker `<a class="note-ref" id="ref-{full_id}" href="#note-{full_id}" epub:type="noteref"><sup class="marker-num">{N}</sup></a>` (inject.py:169) + per-note `<aside class="note" id="note-{full_id}" epub:type="footnote">` in a per-chapter `<aside class="notes-section">` (inject.py:189-234).
- **Badge = ONE per-verse `noteref` badge → ONE per-verse `footnote` aside listing that verse's notes** (reuse the native popup contract; **NO JS** so it works on e-ink). Group notes by (book, ch, v) ignoring the per-note suffix; badge count = notes on that verse.
- **Nested-`<a>` (RSC-005) trap:** the badge/container MUST land BEFORE the next `<a class="vn-link">` opening tag (inject.py:309-335 already backs the region boundary up past it). Guard: `check_nested_anchors.py` + `test_nested_anchors.py` (0/61 base invariant).
- `marker_style` field does NOT yet exist in editions.yaml; `MARKER_STYLES={"numbers"}` at build_edition.py:1695 (badge deliberately excluded). Add `"badge"`, wire through `inject_book`/`build_marker` + a new `build_verse_badge`, surface in /customize.
- **Surgical edit from HEAD's `epub_working`, NEVER bare-base re-bake** (proven lossy — drops harvest-preserved popups, re-qualifies xref hrefs; CHANGELOG 2026-05-24).
- Files: `inject.py`, `build_edition.py`, `editions.yaml`, `stylesheet.css`, `tests/test_marker_style.py`.

## D2 — Cross-reader popups
- The current markup **already uses the correct EPUB3 contract** (`epub:type="noteref"` anchor → `epub:type="footnote"` aside, matched href/id, backlink). So Kobo's "nothing pops up" is **not** a markup-contract bug — most likely the **file size (2–3.4 MB)** + the notes nested inside a `hidden` per-chapter `notes-section`. Fix via D4 (split) + the badge per-verse asides; confirm against the Mac compat research + a device re-test.

## D3 — Kobo structural (mostly config)
- **TOC:** `reader_toc_collapsible: false` already exists (build_edition.py:1955-2031) → unwraps `<details>` to a static flat TOC (no `<details>`/flex) = Kobo-safe. Flip it (default-on for Kobo / all).
- **Title art:** `framed` (`display:inline-block`, art inside the border) is cross-reader-safe; `full-bleed` (`position:absolute; bottom:7%`) fails on Kobo + misaligns on Apple → make framed the default.
- **Apple page-break (expand pushes book to next page):** add `.toc-wrap details { page-break-inside: avoid; }` (one CSS line; harmless on Kobo).

## D4 — File-size / performance (heaviest piece)
- **No splitter exists** — the 61 `index_split_*.html` are a static pre-split calibre baseline (build only filters into them). Per-file 2–3.4 MB is the Kobo crawl.
- Need a **new semantic splitter** (~200-400 LOC; split at section/chapter boundaries, regenerate the OPF manifest+spine + fix cross-file anchors) → ~350 files @ ~0.4 MB. Plus: the Phase-1 scaffold strip (~−10 MB), CSS/HTML minification, image re-encode. This is Phase 4's core.

## D5 — Font embedding (infra exists)
- Zero fonts embedded today (`style_config.EMBED_FONT_PATHS=[]`). The `patch_opf_fonts` (build_edition.py:2641-2693) + apply_style.py `@font-face` (with `unicode-range`) machinery is **already built** — just unused.
- Embed **Cardo** (OFL 1.1; Latin+Greek+Hebrew; ~85 KB subset via fonttools) → prepend to `.vnote-hebrew`/`.vnote-greek` + body stacks. **Abyssinica SIL** (OFL, Ethiopic, ~120 KB) for `ethiopian-tewahedo` + the Ge'ez/Amharic standalones only. Update `ATTRIBUTIONS.md` (OFL permits EPUB embedding + subsetting).

## D6 — Scaffold-leak surface (Phase 1 spec)
- **88,773 / 91,733 notes (96.8%)** carry one of 5 `<em>[Reviewer:…]</em>` variants in `body`, from 8 `detectors.py` sites (HebrewWord 204 · GreekWord 372 · CrossRef 416 · NaveTopical 489 · TorreyTopical 548 · Kenyon 651 · AIXref 777 · AINote 903) + `extract_eastons_ccel.py:150`. Base `epub_working/index_split_*.html` carries 88,682 across 55 files → **strip both in lockstep**.
- **Strip regex (safe — reviewer text has no `<` until `</em>`):** `\s*<em>\[Reviewer:[^<]*</em>` then re-trim.
- **Root-cause fix:** move each body-embed into the existing `reviewer_notes=` field (8 sites); add a defensive strip in `promote.py` (`promote_candidate`, before dedup).
- **Guard:** `lint_rules.check_no_reviewer_scaffolding_in_bodies()` — FAIL on any `[Reviewer:` in a shipping note body (8th tuple field); register in the checks table.
