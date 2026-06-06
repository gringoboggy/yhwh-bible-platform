# Chapter-start verse-boundary bug (CRITICAL follow-up)

**Found:** 2026-06-06, during beta-2 device-QA (user-reported: "◈11◈2 2 A man of the house of Levi… happens A LOT at the beginning of most chapters / bibles-wide").
**Status:** **FIXED for 161 chapters** (content-preserving, confidence-gated) via `scripts/_fix_chapter_verse_boundaries.py` (applied to the base 2026-06-06); **116 chapters FLAGGED** (archaic/genealogy/apocrypha wording the gate couldn't anchor unambiguously) remain for a follow-up pass — they are LEFT UNTOUCHED (never guessed). Verified: verse text correct on exo 2 / gen 1 / exo 13 / gen 25 / lev 4; idempotent (re-run FIX=0); `check_nested_anchors` 0; KJV/JPS-anchored split.
**Pre-existing:** present in `v1.0.0-beta.1` (the recovered base), NOT introduced by the beta-2 polish. The beta-2 polish (P1–P4, commit `8fb606aa`) is independent and verified.

## Symptom

At many chapter starts the reader sees, e.g. (Exodus 2):

```
1 ◈2 2 A man of the house of Levi went and took a daughter of Levi as his wife.
```

i.e. verse number **1**, then its note badge, then verse number **2**, then the text — two verse numbers clustered with no text between, and the text appearing under the wrong number.

## Root cause (verified from the base HTML)

The recovered base `epub_working/index_split_*.html` is **missing the verse-1/verse-2 boundary** at affected chapter starts. Raw markup for Exodus 2:

```
<a class="vn-link" id="v-exo-2-1"><span class="vn">1</span></a>
  <a class="note-ref … id="ref-e0201">…3…</a>      ← verse-1 notes (correct verse)
  <a class="note-ref … id="ref-e0201a">…4…</a>
  <a class="note-ref … id="ref-e0201b">…5…</a>
  <a class="note-ref … id="ref-e0201c">…✦…</a>
<a class="vn-link" id="v-exo-2-2"><span class="vn">2</span></a>
  A man of the house of Levi went and took a daughter of Levi as his wife. …
```

So:
- **verse 1** = number + its 4 notes, **no text**;
- **verse 2** = number + **WEB verse 1 *and* verse 2 text merged** ("A man of the house of Levi…" is WEB Exo 2:1);
- **verse 3+** = correct (the bug is only the first boundary — it does NOT cascade).

The **note ids encode the correct verse** (`e0201` = Exo 2:1), so the notes are right; only the base's verse-number **anchors/text-split** are wrong. This is a base-data / WEB-ingestion artifact, identical in badge and numbers modes (badge just collapses the verse-1 notes into one ◈ badge, so the cluster reads `1 ◈N 2 text`).

## Scope

A heuristic base scan flags ~**301** chapter-starts with the "empty verse-1 → text under verse-2" shape (over-counts: e.g. gen 1:1 is a false positive because its KJV-anchored word-notes fall to the verse start — needs a precise count). Real scope is "most chapters across all editions" per the user.

## Why it is deferred (not blind-fixed)

The reading text is **WEB**, and there is **no clean per-verse WEB source** in the repo (only the base HTML). The clean per-verse sources that DO exist — `content/translations/sources/kjv/eng-kjv_vpl.txt` (+ jps, douay) — are **different translations** (different wording). Re-deriving the WEB v1/v2 split point by fuzzy-aligning WEB text against KJV wording, across ~hundreds of chapters, can mis-split a verse — i.e. corrupt scripture. That is unacceptable to do blind.

## The fix (next session — careful + verified)

1. **Precise detection:** for each `v-{bk}-{ch}-1` anchor, strip the verse-1 `note-ref <a>…</a>` blocks and confirm zero verse TEXT before `v-{bk}-{ch}-2` (fix the earlier probes' slice/strip bugs — end the slice at the full v2 `<a>` open, strip note anchors before tags). Produce the exact affected-chapter list + count.
2. **Source of truth for the split (we HAVE the sources — user 2026-06-06):** every reference translation is on disk with correct standard versification — `content/translations/{kjv,jps,douay-rheims,wlc,lxx-brenton-english,lxx-swete-greek,byzantine-greek,vulgate-clementine,arabic-vandyke}/` (+ the `…/sources/*_vpl.txt` verse-per-line originals). English versification is shared between WEB and KJV/JPS/Douay, so the WEB v1/v2 boundary in the merged text = where KJV/JPS verse-2 begins. Derive the split by locating verse-2's opening content words (from KJV, corroborated by JPS/Douay) inside the merged WEB text. **Confidence-gate:** only auto-split when the anchor matches unambiguously across ≥2 reference translations; otherwise flag for human review — never auto-split scripture when unsure. (A clean WEB verse-per-line source, if acquired, would make this exact rather than aligned.)
3. **Transform:** move the verse text for WEB v1 to sit under the (currently empty) `v-…-1` anchor, leaving WEB v2 under `v-…-2`; keep each verse's notes with their verse.
4. **Verify hard:** re-run `scripts/audit_epub_structure.py`; a new lint guard "no empty verse-1 at a chapter start"; spot-render ≥10 chapter starts on both readers; prove no note loss / no text loss (categorize-diff); epubcheck 0/0/0/0.

## Reference

- Affected example: Exodus 2 (`epub_working/index_split_003.html`).
- Verse-number anchors: `scripts/generate_verse_popups.py::wrap_verse_number` (wraps existing base `<span class="vn">`); the boundary lives in the **base WEB HTML**, so the fix is a base transform (then re-bake), not a build-pipeline change.
- Audit tool: `scripts/audit_epub_structure.py` (add a verse-1-empty check).
