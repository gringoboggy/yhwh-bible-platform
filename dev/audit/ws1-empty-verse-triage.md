# WS1 empty-verse-anchor triage — the full 205, classified (Mac, 2026-06-25)

> WIN-assigned (`b2e82adf`) follow-up to the WS1 redirect (`dev/audit/ws1-mixed-translation-finding.md`).
> Every empty verse anchor in `epub_working/` is now classified into an action. Data:
> `dev/audit/ws1-empty-verse-resplit-data.json` (regenerated — now handles consecutive empties).

## Headline

**205 empty verse anchors total**, split into three actions:

| class | count | action |
|---|---|---|
| **A — protocanon re-split** | **158 verses** (155 groups) | move WEB[N]'s clause out of the merged terminal verse back under each empty anchor. WEB-sourced, no wording change. **The fix set.** |
| **B — deuterocanon defer** | **43 verses** | sir / lje / Ethiopian Daniel-additions (dan ch12→v49). WEB's numbering differs / book absent → resolve per-verse vs the **Greek/deuterocanon source, not WEB**. Lower priority (apocrypha; not user-reported). |
| **C — legitimate WEB omission** | **4 verses** | `luk 17:36`, `act 8:37`, `act 15:34`, `act 24:7` — WEB textual-critical omissions. **Leave the anchor empty.** The inlined KJV popup is the correct fallback (cosmetic leading-`¶` strip optional). |

158 + 43 + 4 = 205. ✓ (Refines the redirect's "~162": the precise WEB-sourced re-split count is **158**;
the few dan-additions verses the first pass swept into the off-by-one count are actually class B.)

## Key refinement vs the first pass — consecutive empties need N-way splits

The first off-by-one scan matched `base[N+1]` starts-with `WEB[N]`. That misses **runs of consecutive
empty anchors**, where two verses' text merged into the *terminal* verse. Three such groups exist, all
class A (the JSON now emits them as `n_split=3` groups):

- **`jos 15:29` + `15:30`** → base `jos 15:31` body = WEB 15:29 (`Baalah, Iim, Ezem,`) + WEB 15:30
  (`Eltolad, Chesil, Hormah,`) + WEB 15:31 (`Ziklag, Madmannah, Sansannah, …`). Split into three.
- **`neh 10:19` + `10:20`** → base `neh 10:21` body = WEB 10:19 (`Hariph, Anathoth, Nobai,`) + 10:20
  (`Magpiash, Meshullam, Hezir,`) + 10:21 (`Meshezabel, Zadok, Jaddua, …`). Split into three.
- **`1th 5:19` + `5:20`** → base `1th 5:21` body = WEB 5:19 (`Don't quench the Spirit.`) + 5:20
  (`Don't despise prophecies.`) + 5:21 (`Test all things, …`). Split into three.

These are the same dropped-boundary defect, just with two dropped boundaries in a row — confirming the
mechanism is systematic, not isolated. The JSON's `resplit_groups[*].web_per_verse` gives the exact
per-verse seam for each (2-way and 3-way alike).

## Class B — deuterocanon (43, defer)

`sir` (~29: 1:5, 1:7, 1:21, 3:19, 10:21, 11:15-16, 13:14, 16:15-16, 17:5/9/16/18/21, 18:3, 19:18/19/21,
20:3/32, 22:9/10, 23:28, 24:18/24, 25:12, 26:19/27), `lje` (1:25, 1:52, 1:66), and the **Ethiopian
Daniel-additions** block (`dan` ch12 runs to v49 — the Prayer-of-Azariah / Song-of-the-Three / Susanna /
Bel material, not canonical Daniel 12). WEB either lacks these or numbers them differently, so the WEB VPL
is **not** the source. These need the project's own deuterocanon text source, resolved per-verse — **no
guessing**. Lower priority: apocrypha, and none are in the user's device-reported set. Full list:
`resplit-data.json → deutero_defer`.

## Class C — legitimate WEB omissions (4, leave empty)

`luk 17:36`, `act 8:37`, `act 15:34`, `act 24:7` — verses WEB omits on textual-critical grounds (present
in the KJV/TR, absent from the critical text). The empty anchor is **correct** for a WEB base; the inlined
KJV popup is the right fallback. Decision for the user (per the canon's text-crit stance): keep the KJV
popup as-is / strip only the cosmetic leading `¶` / footnote. **Do not "fill" these from WEB** (it has no
text to give).

## Net effect on the re-split scope

The user-ratification item (`HUMAN_DECISIONS`, owner=windows) should read **158 protocanon WEB re-splits**
(155 groups, incl. 3 three-way), with 43 deuterocanon verses tracked separately (different source) and 4
WEB-omitted verses left empty. The protocanon 158 are the device-visible fix (they include every verse the
user reported). `resplit-data.json` is the deterministic, per-verse worklist for WIN to apply after the user
ratifies.
