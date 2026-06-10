# Adversarial review — the K-R2 splitter arc (`bf751391` + `9c463de9`/`e7685d4b`) + the K-R3 mechanism

**Lane:** Mac (turn-61 backlog item 1) · **Date:** 2026-06-10 · **Method:** 4 attack
dimensions (packing/singletons · the pop regex · canon adjacency · determinism/gates),
every candidate finding independently re-verified with synthetic probes + the REAL base +
freshly built artifacts (workflow `wf_d1c4d568-5fc`, 23 agents; **19 confirmed / 0 refuted
/ 8 info**). Companion artifact data: this Mac built + gated catholic-study AND eth
(turn-61 items 2–3) — both **ALL K-R2 GATES GREEN**, epubcheck 0/0/0/0, kepub deep-verify
clean (279 pieces survive kepubify identically, no dummy titlepage injected, 0 unresolved
/ 0 promoted noterefs post-transform).

## ★ THE HEADLINE — K-R3-4's real mechanism found (it is NOT the splitter)

**The "promoted badge href" hypothesis is REFUTED on artifacts** (0 cross-file noterefs
out of ~109K bare noterefs across eth + catholic, EPUB + kepub — measured independently
twice) **and is structurally impossible** for vnotes asides: the badge tag carries both
the anchor id and the only prose href, so first-referencer attribution can't separate a
badge from its aside. **The planned "attribute the aside to the badge anchor's piece"
splitter fix would be a no-op. Do not build it.**

**The real, artifact-verified mechanism:** `apply_badge_markers`
(`scripts/build_edition.py:2311ff`) places a verse's merged badge at its **LAST marker's
position** — and for a chapter's last verse, inject placed markers INSIDE the next
chapter's first paragraph. Result: **305 chapter-starts in eth (74 in catholic) carry the
PREVIOUS verse's badge between the chapter heading and verse 1.** kobo8's cluster is
exactly this; the user's "first 5" = `vbadge-gen-1-31` (`title="5 notes"`). And because
the splitter cuts at chapter candidates, the piece holding Gen 2's start literally BEGINS
at `ch-b00-c1`'s region — Kobo's failed-pop fallback jumps to the piece top = **"teleport
to chapter 1 start."** This also explains K-R3-3 ("notes spill into the next chapter's
start" = the stray badges, not note text).

**Prescribed fix (WIN sweep):** in `apply_badge_markers`, clamp the badge insertion to
BEFORE any intervening `ch-anchor` / `ch-heading` / `bp-` boundary after the verse's
vn-link; if every marker sits past the opener, insert at the end of the verse's text
region immediately before the opener. The splitter's first-referencer attribution then
keeps the aside in the right piece automatically — **no splitter change needed.** Pin
with an artifact assertion: badges-after-next-chapter-heading == 0.
(Retired side-theory, for the record: the hidden notes-section wrapper rendering on Kobo —
not needed once badge placement explains the visible clusters; rounds 1–2 never showed
aside TEXT inline. kepubify injects 5,587 koboSpans inside the hidden aside in 000_02 —
worth one glance if any spill survives the badge clamp.)

## C1 (HIGH, ships today) — forced title singletons tear real intro blurbs

The title atom's end = the next cut candidate of ANY kind. Two real books carry an intro
blurb after the title div (Jubilees `bp-15` / `index_split_018`, Additions-to-Esther
`bp-25` / `index_split_028`); the next candidate is a vn-link INSIDE the blurb →
**the title page ships with a mid-sentence-torn blurb** (confirmed on this Mac's fresh
eth artifact: piece `018_02` ends `"…the Book of Jubilees?), </p>"`), with (per the
review's probes at the raw-split layer) dangling badges / a notes-section landing
title-side in the worst shape, plus the torn paragraph's id duplicated into the
continuation. The pre-arc 2026-06-06 build left the file intact — regression pinned to
`bf751391`. Gate + unit fixtures are blind to it.
**Fix:** end the title atom at the CLOSE of the book-title-page div (a cut at its
matching `</div>`), so the whole blurb travels intact to the next piece — or, if blurbs
are wanted ON title pages, extend to the next ch/bp-kind cut (skip vn-link cuts) and
relax the gate's scripture check for title pieces. Either way: grow the gate (bp- pieces
carry no notes-section; no id in two pieces).

## Confirmed findings (19; deduped families)

| Family | Findings | Sev | What/where | Fix shape |
|---|---|---|---|---|
| Title-atom tear | C1 | **HIGH** | torn blurbs on Jubilees/AddEsther title pages (ships) | title atom ends at title-div close |
| K-R3-4 mechanism | C8 | **HIGH** | badge placed after next chapter's heading (305 eth sites); teleport = piece-top fallback | clamp in `apply_badge_markers` + artifact pin |
| Gate blind to promoted refs | C9, C13 | HIGH→med | `href="#…"` regex excluded the exact K-R3-4 form from the denominator | **FIXED this commit** — gate now matches noterefs attr-order-insensitively, FAILS on any cross-file noteref (validated: eth + catholic + kepub, all 0) |
| Tautological title count | C14 | MED | my turn-61 canon-aware fix compared the artifact to itself | **FIXED this commit** — each bp- id must occur exactly once across pieces |
| Reopen-id duplication | C4, C11, C16 | MED | stack-reopen replays open tags WITH ids → `page_1468`/`page_1913`/`page_639` etc. duplicated across pieces; poisons idmap (last-writer-wins); blocks a hard id-uniqueness gate | strip `id=` from reopen prefixes (WIN); gate prints an informational dup-id warn meanwhile (kepub's own `kobo.*`/wrapper ids excluded) |
| idmap pollution | C12, C15 | MED-low | `\bid="` also matches `data-tradition-id=` etc. — phantom idmap keys can hijack bare hrefs | tighten to `\sid="` in `apply_file_split` + the gate (gate side done) |
| Orphan asides → title pieces | C2, C10, C18 | MED-low | orphans default to the LAST atom; a file ending with a title page would put a notes-section on it; canon filter leaves dropped books' asides as orphan concentrate | re-home orphans (atom 0 or nearest non-title); zero LIVE orphans today — latent |
| Whitespace-only piece | C3 | LOW | packing/pop interplay can emit a blank spine page (latent at 400 KB) | filter whitespace-only groups, not just empty |
| Pop-regex rigidity | C5, C6, C7 | LOW | form-rigid anchor sub-pattern; first-notes-section boundary assumption; stacked openers pop only the last | hardening only — the pop is VERIFIED SOUND on all 5 real donors, exact matches, guards have ~6× headroom, full in-memory simulation clean |
| Test/coverage gaps | C17, C19 | LOW | pop-only path untested; no canon-filtered-tree splitter test | add with the sweep |

**Cleared by direct verification (do not re-litigate):** consecutive bp- atoms; title at
position 0; lone over-target atoms; pop-chain into title groups (impossible);
empties-filter ordering; sorted() adjacency (all 61 files zero-padded); canon-drop ×
cross-file pop (all 5 donor seams sit inside every canon; artifact-confirmed clean on
catholic-study); step 1b does NOT create cross-file noterefs (donor files have zero
orphan asides; receivers hold the popped chapters' asides natively); determinism (no
set/dict-order leak found).

## Gate status after this commit (`dev/verify_kr2_build.py`)

Canon-aware + non-tautological + promoted-noteref-failing + dup-id-warning. Validated
runs: catholic-study EPUB (75 singletons / 42,886 refs / 0 promoted), eth EPUB
(86 singletons / 66,498 refs / 0 promoted / 5 real dup-id warns = the C16 class),
catholic kepub (clean, 2 dup-id warns). Still for WIN per C13: run it on the actual r3
kepub on G:\, and harden the dup-id warn into a FAIL once the reopen-id strip lands.

## WIN sweep priority (supersedes the round-3 doc's step list)

1. **Badge clamp in `apply_badge_markers`** (C8 — the actual K-R3-3/K-R3-4 fix) + pin.
2. **Title-atom end at div close** (C1 — un-tear Jubilees/AddEsther) + gate growth.
3. Reopen-id strip (C16) → then harden the gate's dup-id warn to FAIL.
4. idmap `\sid="` tighten (C12/C15).
5. Orphan re-home + whitespace-piece filter (C2/C3/C10) + the C17/C19 tests.
6. K-R3-1 (Gen 1:1 ◈15 no-pop) remains open — likely the aside-size threshold;
   unaffected by the above (its aside is same-piece, bare-href — verified).
