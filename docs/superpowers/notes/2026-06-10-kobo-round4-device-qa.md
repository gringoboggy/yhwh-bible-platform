# Kobo device-QA round 4 — 2026-06-10 (user, verbal) — FINDINGS + ROOT CAUSES

Artifact tested: `YHWH-Ethiopian-Bible-v0.1.0.kepub.epub` (the shipped v0.1.0,
loaded on the Kobo). User report (no screenshots this round):

1. "Formatting on translations a lot better, but still run-on sentences —
   nothing to break them apart."
2. "Gen 1:1 note badge (◈15) still does nothing — no screen pops up."
3. "Gen 1:26 note badge (◈13) still teleports us to chapter 1 start."

User directive: find fixes AND sweep so the class doesn't exist anywhere else;
implement inside the giant-audit program (this is v0.1.1 work).

## ✅ Round-3 closes confirmed by this round
- K-R3-4 badge clamp HELD — no report of the Gen 2 badge cluster (was the #1
  complaint in round 3).
- K-R3-2 separators WORK where they were emitted — "a lot better" = the study
  cascade now breaks apart in the preview dialog.

## K-R4-1 (HIGH) — translation (verse) popups have NO plain-text separators
**Root cause (artifact-confirmed):** the K-R3-2 `.vn-sep` fix was emitted only
in `apply_badge_markers`' merged STUDY asides (`build_edition.py:1906-1908`).
The verse-popup asides (`<aside class="vnote" id="vnote-{b}-{c}-{v}">`, baked
in `epub_working/` by the popup generator) have zero separators — when Kobo's
preview strips tags, header + verse text + every `vnote-source-label` +
translation run together as one paragraph:
`…the heaven and the earth.Hebrew (Masoretic / WLC)בְּרֵאשִׁ֖ית…`

**Fix spec (build-time, base untouched — 9-KJV invariant safe):** a build pass
over `vnote-*` asides inserting the same hidden separator spans — `¶ ` before
the `<strong>` header close / first `vnote-text`, `◦ ` before each
`vnote-source-label`. Extend the hide-CSS: the current rule is scoped
`.verse-notes .vn-sep` — re-scope so it also covers vnote asides' container
(verify the actual ancestor in the artifact). Pin: every `vnote-source-label`
in a built EPUB is preceded by a `vn-sep`; CSS hides `.vn-sep` in every
`note_popup_style`.

**Class sweep (don't fix just the instance):** enumerate EVERY
`epub:type="footnote"` aside emitter and check each for preview-stripped
legibility: merged study asides ✓ (K-R3-2) · vnote translation popups ✗ (this)
· the category-legend popup (Addendum A) · topical.xhtml popups · any
reference-table popovers. One audit dim covers all.

## K-R4-2 (HIGH) — preview-decline threshold CONFIRMED + BRACKETED
User's round-4 taps + artifact measurements (stripped = tag-stripped chars,
what Kobo's heuristic sees):

| Aside | stripped | device result |
|---|---|---|
| vnotes-gen-1-3 | 3,313 | POPS (round-3 control) |
| vnotes-gen-2-1 | 547 | (untested, predict POP) |
| vnotes-gen-1-26 | 7,748 | JUMP → chapter 1 start |
| vnotes-gen-1-1 | 9,434 | NOTHING (= jump to file start, which IS Gen 1:1) |

**Threshold T: 3,313 < T ≤ 7,748** (vendor research said ~5,000 — consistent).
"NOTHING" at 1:1 and "teleport" at 1:26 are the SAME mechanism: decline →
navigate fallback → target is inside the `hidden=""` notes-section → no
rendered position → Kobo lands at FILE START of piece 000_02 (= Gen 1:1).

**Class size (shipped v0.1.0, whole Bible):** 30,148 merged + 36,535 vnote
asides; ≥5,000 stripped = **67 merged + 1 vnote** (worst: 1sa-16-12 19,520 ·
act-23-6 19,493 · gen-12-10 14,659); 2–5k band = 528 merged + 4 vnote. So at
worst (T≈3.3k) the class is ~600 asides; at T≈5k it is 68. Bounded, fixable.

**Fix direction (design needed — board item 8, now un-gated):** options, in
preference order, to be settled in the audit's fix arc:
(a) **split oversized merged asides by category** — one badge per category
    group for verses whose merged aside exceeds the safe cap (the cascade
    already groups by category; most groups fall under any plausible T);
    completeness preserved, popup always works; verify no category-group
    itself exceeds the cap (check 1sa-16-12 / act-23-6 composition);
(b) benign-fallback hardening as belt-and-braces: a rendered (non-hidden)
    zero-footprint anchor adjacent to the badge as the navigate target —
    needs research on whether Kobo pops the NEXT element or only the target;
(c) preview-stub + full in-book notes (duplicates content; last resort).
**Round-5 calibration page:** bake a hidden test chapter (or use Gen variety)
with asides at ~3.5k/4.5k/5.5k/6.5k stripped to pin T in one tap-pass, so the
cap is data-set, not guessed.

### Mac turn-69 design prep — the (a)-vs-(a)+(b) question ANSWERED

Category compositions of the two worst offenders, bucketed EXACTLY as the
build cascade does (`inject.category_for(kind)` — the same resolver
`apply_badge_markers` calls before `_emit_cascade_sections`), tag-stripped:

| Verse | Category | Stripped chars |
|---|---|---|
| 1sa 16:12 | **hist** | **19,009** |
| 1sa 16:12 | topic | 252 |
| 1sa 16:12 | lang | 64 |
| act 23:6 | **hist** | **19,053** |
| act 23:6 | lang | 383 |
| act 23:6 | topic | 182 |

**Verdict: (a) alone is NOT sufficient — (a)+(b) needed, and (b) must split
WITHIN a single note body.** In both verses the `hist` group is ONE note —
the dict-easton entry (Easton's "DAVID" at 1sa 16:12, Easton's "PAUL" at
act 23:6; kinds.yaml maps dict-easton → hist) at ~19k stripped — ~2.5× the
threshold bracket's UPPER bound. Per-category splitting fixes every other
group trivially (all ≤383 chars), but the oversized unit is a single note
body, so (b) = chunk the entry across multiple asides (continuation links)
or truncate-with-continuation. The fix itself stays gated on the round-5
calibration taps pinning T.

## Sweep items (the "nowhere else" directive)
- S1: separator coverage across ALL footnote-aside emitters (K-R4-1 class).
- S2: stripped-size distribution per aside kind per edition — gate: 0 asides
  over the calibrated cap once the K-R4-2 fix lands (add to
  `dev/verify_kr2_build.py` as gate 4g once T is pinned; warn-tier until then).
- S3: hidden-target navigate fallback — any OTHER noteref class whose target
  has no rendered position (same teleport failure shape): audit all
  `epub:type="noteref"` href targets for hidden ancestors.
- S4: the 117-chapter-start v1/v2 displacement (separate arc, already designed
  — Mac's 2026-06-10 verse-boundary-residual design; v0.1.1).

## Run-on caveat
"Run-on sentences" in TRANSLATION popups = K-R4-1 (no separators), NOT the
prose itself. If the user also means the in-book WEB text reads as run-on
(real-page formatting), that is a different surface — re-ask only if K-R4-1's
fix doesn't visibly resolve the complaint at round 5.
