# Round-13 GRAND AUDIT — Mac structural "down-to-verse, down-to-the-word" pass

**Mac lane · 2026-06-23 · the user's directive: "run the full auditor together again, top to bottom, down to verse + word, no time limit."** This is the rendered-product half WIN's code-only deep-audit cannot do.

## Method

Re-ran the calibrated `dev/audit_book_structure.py` (the 4 calibration fixes + standalone fallback from BIG-batch ①) across **5 editions × 2 formats = 10 artifacts** built this session: catholic-study, eastern-orthodox, evangelical-reformed, ethiopian-tewahedo (superset), standalone-geez — each as `.epub` AND `.kepub.epub` (kepubify v4.0.4). Build is content-determined and the round-13 tree changed only code/tests (dev-mode `content_root()` = `repo/content`, unchanged), so this session's artifacts reflect the current content.

## Result — 293/294 books green, epub == kepub

| format | books green | FAIL |
|---|---|---|
| epub (5 editions) | **293/294** | `1en` (ethiopian-tewahedo) |
| kepub (5 editions) | **293/294** | `1en` (ethiopian-tewahedo) — **identical to epub** |

Per-edition: catholic-study 72/72 · eastern-orthodox 75/75 · evangelical-reformed 66/66 · ethiopian-tewahedo 76/77 · standalone-geez 4/4 — **same in both formats** (kepubify's Kobo `kobo.*` span injection does not perturb book/chapter/verse structure). 17 acceptable versification-gap warns (recovered-base holes), 0 other false-positives.

## ★ The 1 FAIL — `1en` (1 Enoch) misordering — VERDICT: base-source artifact, NOT a build regression

The auditor flags, in the ethiopian-tewahedo superset (epub + kepub identically):
- `1en 71`: verse 46 is misplaced between v13 and v14 (rendered anchor order `[1..13, 46, 14, 15, 16, 17]`).
- `1en 90`: v14–17 scrambled (`[1..13, 16, 14, 17, 15, …]`).

**Verdict (traced to root):** the misordering is **present in the BASE scripture HTML** — `epub_working/index_split_021.html` carries `1en` ch71 verse anchors in the order `[1, 2, …, 13, 46, 14, 15, 16, 17]` (sorted = **False**) **before any build/inject step**. So this is a **base-source verse-ordering artifact in 1 Enoch**, NOT a build, inject, or round-13 regression. ch71/ch90 sit in the documented **1En 37–108** range (`project_build_architecture`: the ~161-marker inject residual neighborhood; the base 1 Enoch in this range has known quirks).

**Disposition: deferred-acceptable, → WIN/content to fix the BASE.** The verses are all present and rendered; only their physical order is wrong in the base 1 Enoch source. The fix is a **content/base-HTML re-order** in `epub_working/index_split_021.html` (and the ch90 base file) so the `v-1en-{71,90}-N` anchors are sequential — not a code fix. Low functional severity (a Tewahedo-distinctive book's reading order), but worth correcting for a clean superset. Only the ethiopian-tewahedo superset is affected; the 4 canon-filtered catalog editions exclude 1 Enoch and are clean.

## Auditor (the `dev/` tool) — calibrated + stable across round-13

No new auditor changes this round; the BIG-batch ① calibration holds (2nd badge emitter `_NOTEREF_RE` + dup-id check; any-element `ch-b#-c#` heading detection; Daniel/Esther addition folding; standalone own-versification fallback). 0-FP except the single real `1en` base-ordering FAIL.

## Round-13 structural conclusion

The rendered product is **structurally sound at every level (verse → chapter → book → out-of-book) across all 5 editions and both formats** on the round-13 tree, with one pre-existing base-source `1en` ordering artifact handed to WIN/content. Pairs with the Mac round-13 deep-audit (`round13-mac-*`) + WIN's round-13 half (`round13-remediation.md`).
