# Verse-boundary residual (117 chapter starts) — root cause + safe-sweep DESIGN (board item 7)

**Status: DESIGN ONLY (Mac, 2026-06-10). WIN executes after round 4.** Base mutation ⇒ all-editions re-release; fold into v0.1.1, NOT the v0.1.0 cut.

## 1. This is the KNOWN RX-beta2 bug's residual — not a new defect

Turn-62's "NEW pre-existing BASE finding (117 chapter starts)" **is the flagged remainder of the 2026-06-06 arc** `docs/superpowers/notes/2026-06-06-chapter-start-verse-boundary-bug.md`: user-reported in beta-2 QA, root-caused (recovered-base/WEB-ingestion artifact: empty v1, WEB v1+v2 text merged under the v2 anchor; note ids correct; only the FIRST boundary, no cascade), and **161 chapters already repaired** content-preservingly by `scripts/_fix_chapter_verse_boundaries.py` (`809f711f`). **116 chapters were FLAGGED and left untouched** (never-guess gate). Verified today on the live base:

- Independent signature scan (no visible text between the `v-{b}-{ch}-1` and `v-{b}-{ch}-2` vn-links) ⇒ **117 sites / 1,435 chapter starts**, matching WIN's list (psa 31, job 14, eze 6, gen 2/11/32/37/43 …).
- The existing fixer's `--dry-run` re-flags **116** of them today (FIX 0 — idempotency holds). ⚠ Reconcile the 1-site delta (117 signature vs 116 flagged) at execution: likely one site whose `_V1_RE` shape differs; identify by diffing the two lists.
- Etiology confirmed in the ORIGINAL recovered base (`git show 5ee2ad1c:…index_split_000.html`, gen 2): the inversion predates every post-pass — upstream ingestion, exactly as the 06-06 note said.

## 2. Why these 117 resisted the 06-06 pass (verified failure mode)

The fixer derives v2's opening-words anchor from the **on-disk KJV store** (fallback jps → douay-rheims; `_kjv()` at `scripts/_fix_chapter_verse_boundaries.py:63`) + a KJV→modern `_SUBS` map, then requires a UNIQUE match in the merged run. The flagged classes (all seen in today's dry-run):

1. **Archaic/divergent phrasing** KJV↔WEB ("it came to pass…", "this the ordinance of the…") — no unique match.
2. **Genealogy spellings** ("kenan mahalaleel jered" vs WEB "Kenan, Mahalalel, Jared") — 1ch 1, gen genealogies.
3. **No KJV source at all** — apocrypha (aes 7/10 "no KJV v2 to anchor on", 2es, jdt …).

## 3. The fix: anchor on the REAL WEB text (the base IS WEB)

Replace the inference with the ground truth the 06-06 pass lacked:

- **One-time fixture**: fetch WEB (incl. Apocrypha — eBible.org `eng-web` USFM, PD) verse text for just the affected chapters' v1+v2 (≤234 verses) → commit `content/sources/web_boundary_anchors.json` `{ "gen-2": {"v1": "...", "v2": "..."} , ... }` with provenance header. Tiny, auditable, license-clean.
- **Matching**: normalize both sides (smart quotes→ascii, collapse whitespace, casefold; keep "Yahweh" — WEB-native) and locate fixture-v2's opening ~6 words in the merged run. Because the base text IS WEB, this should be a near-exact substring match — the entire reason classes 1–3 existed disappears.
- **Keep every safety property of the proven script** (it already does the hard part): content-preserving reorder+split `[NOTES1][V2ANCHOR][TEXT1][TEXT2]` → `[TEXT1][NOTES1][V2ANCHOR][TEXT2]`; ids untouched (no idmap/noteref ripple); **unique-occurrence confidence gate stays — never guess on scripture**; idempotent; `--dry-run` first.
- **Bridged-verse escape**: if WEB itself bridges v1-2 (USFM `\v 1-2`) the fixture records it; the site is classified LEGIT-BRIDGE, left as-is, and added to the regression pin's allowlist. (Spot-checks gen 2 / psa 31 / job 14 are NOT bridges — expect few/none.)
- **Implementation point**: extend `_kjv()`'s chain with the fixture as the FIRST source (book-ch keyed), `_SUBS`/`LEADING` bypassed when the anchor came from the fixture (same-translation match needs no modernization).

## 4. Gates (execution-time, per the 06-06 precedent + standing rules)

1. `--dry-run` diff: expect ~116→0 FLAG conversions to FIX (any remaining FLAG = listed + manually reviewed, not forced).
2. Post-apply: `check_nested_anchors` 0 · `test_nested_anchors` · re-run the signature scan == 0 (modulo LEGIT-BRIDGE allowlist) · re-run `--dry-run` ⇒ FIX 0 (idempotent).
3. Build gates on BOTH eth and **canon-filtered catholic-study** (standing rule): epubcheck 0/0/0/0 + `dev/verify_kr2_build.py` ALL GREEN.
4. **Byte-gate story**: intentional base mutation ⇒ the 9-KJV byte-identity baseline RESETS; prove determinism (rebuild-twice byte-identical) and record the new baseline SHA; release as v0.1.1 with all editions rebuilt.
5. Spot verification on device-visible sites: gen 2 / psa 31 / job 14 / eze 6 / 1ch 1 / aes 7 (render: v1 number + v1 text + v1 badge; v2 number at v2's true start; popups pair with the eye).
6. **Permanent regression pin**: a test encoding the signature scan (no-visible-text-between-v1-and-v2 == allowlist only) so a future base recovery/re-bake can't silently reintroduce it.

## 5. Effort + sequencing

Small: fixture fetch (one session, scripted) + a ~20-line anchor-source extension to a proven 204-line script + gates. Sequence AFTER round 4 (WIN's call), inside the v0.1.1 window. No popup/note data changes — ids already encode the correct verses.
