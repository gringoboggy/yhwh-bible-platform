# Translation-spine arc — Douay / JPS / Vulgate / Arabic (Phase-2 finish)

**Status:** IN PROGRESS 2026-05-23 — **Arabic ✓ + JPS ✓ SHIPPED (baked + verified, UNCOMMITTED); Douay + Vulgate NEXT (scope measured below).**
**Owner of the next session:** start at §3+4 (Douay/Vulgate). Pattern is proven (WLC / LXX-Swete / Byzantine-NT / the 11 deuterocanon books / Arabic / JPS).

> **PROGRESS NOTE (2026-05-23):** The intended mechanism turned out to be a shared one — `extract_translation.apply_remap(by_project_book, remap)` + an optional `extract(remap=)` param (the runbook's option (a)). It remaps each verse via `(code,ch,vs)->coord|None` and concatenates same-coord collisions in source order (like `extract_lxx_swete.build_verses`). `remap=None` is byte-identical to before (proven via a kjv re-extract). Per-source thin drivers inject the adapter. Two findings corrected the plan below: **(1) Arabic is NOT pure identity** — it has 2 content-aligned tail-merges (1Ti 6:22→6:21, 3Jn 1:15→1:14); dropping them would lose Arabic text. **(2) JPS is NOT Masoretic** — eBible `engjps` is already KJV-renumbered (0 divergent chapters; total = the KJV OT count), so the `wlc_to_kjv_map` reuse below is REFUTED and JPS is a pure identity ingest (applying the WLC map would double-remap/corrupt). Both verified by full per-chapter probes vs the KJV skeleton, per `feedback_reverify_conservative_nogo`.

## Goal

Close the Phase-2 translation spine: bake the last four PD translations into the verse-popup
spine so the popups carry English-Catholic (Douay), Jewish (JPS), Latin (Vulgate), and Arabic
columns. The four versions are already REGISTERED in `scripts/core/popup_versions.py`
(`douay` / `jps` / `vulgate` / `arabic`, with labels / content_class / lang / dir / order); they
are gated OFF via `_BAKED_NOW` until their full, versification-aligned data lands.

## Data — ACQUIRED 2026-05-23 (in `content/translations/sources/<id>/`, git-tracked)

Downloaded from eBible.org (PD; the registry in `scripts/extract_translation.py` documents each).
**eBible download URL pattern: `https://eBible.org/Scriptures/<ebible-id>_vpl.zip`** — the id is
mostly the registry slug with the hyphen stripped, BUT two are irregular (don't guess — these are
verified-working):

| project id (sources/ dir) | eBible id | verses | books | Ps 9 verses | versification |
|---|---|---|---|---|---|
| `arabic-vandyke` | `arb-vd` | 31,104 | 66 (Protestant) | **20** | KJV-aligned (near-identity), **RTL** |
| `jps` | `engjps` | 23,145 | 39 (Tanakh) | **20** | Hebrew/Masoretic (≈ WLC's 23,142) |
| `douay-rheims` | `engDRA` | 35,811 | 74 (Catholic) | **39** | **Vulgate numbering** |
| `vulgate-clementine` | `latVUC` | 35,809 | 74 (Catholic) | **39** | **Vulgate numbering** |

Each `sources/<id>/` holds `*_vpl.txt` (the extractor input) + `_about.htm` + `signature.txt.asc`
(provenance), matching the `kjv/` layout. `extract_translation.py` globs `*_vpl.txt`, so the exact
filename (e.g. `latVUC_vpl.txt`) doesn't matter.

## Per-translation versification scope (VERIFIED — Ps 9 probe + dry-run counts)

The key finding: these are NOT all identity ingests. `extract_translation.py` stores verses at the
SOURCE's coordinates (it has no remap step), so any source whose numbering ≠ KJV needs a
`versification.<x>_to_kjv` adapter (like `lxx_swete_to_kjv` / `wlc_to_kjv_map`) BEFORE baking, or the
popups land on the wrong KJV verse. Recommended order = easiest → hardest:

### 1. `arabic-vandyke` — ✓ SHIPPED 2026-05-23 (66 bk / 31,102 v)
**Actual:** KJV versification across all 66 books / 1189 ch EXCEPT two content-aligned tail-splits — AVD 1Ti 6:21+6:22 = KJV 6:21, AVD 3Jn 1:14+1:15 = KJV 1:14. `versification.arabic_to_kjv` (identity + those 2 merges) + `scripts/extract_arabic_vandyke.py`. Baked, epubcheck 0/0/0/0, `tests/test_arabic_vandyke_ingest.py`. (Original plan below — "likely pure identity" — was close but the 2 tail-splits needed the merge, else their Arabic text is lost.)

_(Original plan, retained for context:)_ 66-book Protestant canon, Ps 9 = 20 (KJV-aligned). Likely **pure identity** — but VERIFY a handful of
known divergence-prone loci first (Ps 9/10 split confirmed KJV-style; spot-check a Psalm-title psalm,
the Joel/Malachi/3 John chapter boundaries, Acts 19:41). RTL is already handled (`arabic` registry
entry has `"dir": "rtl"`; the popup machinery renders RTL like WLC Hebrew). Plain text → HTML-escaped
at render (NOT trusted_html — correct). No deuterocanon (Protestant 66). **Wire:** add `"arabic"` to
`popup_versions._BAKED_NOW` → regen popups for the 66 books → categorize-diff → verify.

### 2. `jps` — ✓ SHIPPED 2026-05-23 (39 bk / 23,145 v) — PURE IDENTITY (assumption below REFUTED)
**Actual:** eBible `engjps` is ALREADY KJV-renumbered, NOT Masoretic. Full probe: 0 divergent chapters across 39 books / 929 ch; total 23,145 = the KJV OT verse count; Ps 51 = 19 (not Masoretic 21), Joel = 3 ch (not 4), Mal = 4 ch (not 3), Gen 32 = 32 (not 33). So a plain `extract_translation jps` (NO remap) — reusing `wlc_to_kjv_map` would have double-remapped and corrupted it. `tests/test_jps_ingest.py` pins the KJV-numbering so a future wrong remap fails. (The "reuse the WLC map" plan below assumed Masoretic numbering — wrong for this source.)

_(Original plan, refuted:)_ 39-book Tanakh, 23,145 verses ≈ WLC's 23,142, Ps 9 = 20. JPS 1917 is English text on the
**Hebrew/Masoretic versification** — the SAME versification WLC uses. So **reuse
`versification.wlc_to_kjv_map`** (the morphhb `VerseMap.xml` Hebrew→KJV map already in the repo) rather
than deriving a new one. Mechanism: `extract_translation.py` has no remap hook, so either (a) add an
optional remap callback to it, or (b) write a small dedicated `extract_jps.py` that applies
`wlc_to_kjv_map` (mirror `extract_wlc_morphhb.py`'s remap usage). Verify against the same WLC
divergence loci already pinned in `tests/test_wlc_ingest.py` (Psalm superscriptions, the Gen 31/32
boundary, the Hebrew verse-1-title psalms). **Wire:** add `"jps"` to `_BAKED_NOW` → regen → verify.

### 3 + 4. `douay-rheims` + `vulgate-clementine` — ⏭ NEXT (HARDEST, do TOGETHER, LAST)

**MEASURED SCOPE (probe `_probe_vulgate.py`, 2026-05-23 — both 74 books; douay 35,811 v / vulgate 35,809 v):**
- **Douay vs Vulgate differ in 14 chapters** by one verse (e.g. 1Th 4 17/18, 2Co 1 24/23, Gen 5 32/31, Jhn 11 57/56, Psa 15/19/42/125/135, Sir 29, Jdt 4, Isa 45/46) → the shared `vulgate_to_kjv` map needs a small per-source override for these (like Arabic's tail-merges, but per-translation).
- **Psalms — 139/150 chapters diverge.** Superscription-as-v1 (+1/+2 within a psalm) PLUS the LXX-style chapter merges/splits (Vul 9 = KJV 9+10; Vul 10–112 = KJV +1; Vul 113 = KJV 114+115; Vul 114+115 = KJV 116; Vul 146+147 = KJV 147). Scheme ≈ the LXX `_psalm_map` — TRY reusing/adapting it, but CONTENT-VERIFY against the real Vulgate (the verse-level superscription handling may differ from Swete).
- **Daniel additions inline:** Dan 3 = 100 v (incl. Azariah/Song-of-Three 3:24-90 → `paz`); Dan 13 = Susanna (65 v → `sus`); Dan 14 = Bel (42 v → `bel`); Dan 4 offset (34 vs 37). Reuse the `lxx_swete_to_kjv._cross_book` + `_PAZ_FROM_DAT3` pattern (but the Vulgate is Jerome's Latin, not Theodotion Greek — re-verify the verse boundaries).
- **Esther additions:** est ch10 (13 v vs KJV 3) + ch11–16 (KJV 0) = the Greek additions → `aes` (the WEB↔KJV concordance residual; the deferred LXX case — hardest, may stay editorial).
- **Deuterocanon recension differences (fresh content-align):** Sirach 48/51 ch (Vulgate has the Prologue + its own splits), Tobit 13 ch (Jerome's recension differs sharply from the Greek), Judith 14 ch (e.g. Jdt 1 = 12 v vs KJV 16; Jdt 2 = 18 vs 28), Wisdom 7 ch, Baruch (3:38 vs 37) + lje (1:72 vs 73), 1Ma/2Ma minor.
- **~50 scattered ±1 single-verse offsets across OT+NT** (gen 5/49/50, exo 40, lev 26, num 11/12/13/20+, jos 4/5/21, jdg 5/21, 1sa 20/23/24, 1ki 22, 1ch 11/20, neh 3/12, job 16/39/40/41, ecc 4–7, sng 1/5/6, jer 37, eze 2, hos 2/13/14, jon 1/2, mic 5, hag, mat 17, mrk 4/8/9, jhn 6/11, act 7/14/19, 2co 1/13, rev 12, …) — each a per-chapter segment entry, content-verified.

**Approach:** comparable in size to the whole LXX-Swete ingest — content-align locus-by-locus, TDD, fresh context. Build `versification.vulgate_to_kjv(code,ch,vs)` (segment tables like `_SIR_SEGMENTS` + a Vulgate `_psalm_map` + cross-book for Daniel/Esther additions); two thin drivers (`extract_douay.py`, `extract_vulgate.py`) inject it with their 14-chapter per-source overrides. Then bake both, categorize-diff, epubcheck catholic-study + anglican-bcp.

---

_(Original plan:)_ 74-book Catholic canon, do TOGETHER, LAST
74-book Catholic canon, Ps 9 = 39 (**Vulgate Psalm numbering** — Ps 9 = KJV 9+10 merged, then the
LXX-style offset until the 147 split). Douay is the English of the Vulgate, so **both share ONE
Vulgate→KJV versification adapter** — write `versification.vulgate_to_kjv` once, use it for both. Shape
mirrors the LXX `_psalm_map` (the Vulgate Psalm scheme ≈ the LXX scheme) PLUS: Daniel additions
(Azariah/Bel/Susanna placement), the deuterocanon book numbering, and any per-book offsets. **Derive
by content-aligning the real Douay/Vulgate text against KJV verse-by-verse — NEVER identity-map, never
from memory** (the deuterocanon arc's lesson: a documented number can be wrong; the LXX Psalm map is
the template). Verify at the same loci the LXX map pins (Ps 9/10/113/114/115/146/147, the
superscription offsets). **Wire:** add `"douay"` + `"vulgate"` to `_BAKED_NOW` → regen → verify.

## The proven pattern (per translation)

```
extract_translation.py <id>  (or a dedicated extract_<id>.py for remap)
  → build versification.<x>_to_kjv adapter IF source numbering ≠ KJV (arabic: none; jps: reuse wlc; douay+vulgate: shared vulgate map)
  → ruff format content/translations/<id>/   (the pre-commit hook enforces it; em/long lines wrap)
  → flip popup_versions._BAKED_NOW to include the version id
  → python -m scripts.generate_verse_popups --books <books>   (bake into epub_working/)
  → categorize-diff: content-level aside compare vs HEAD (parse-by-id, NOT line-diff — shared split files bleed) → ONLY this version's asides gained
  → ebible verify (errors=0 / paired)
  → build flagship + a relevant edition (catholic-study for Douay/Vulgate; jewish-study for JPS) → epubcheck 0/0/0/0 (NOT two JVMs at once)
  → lint_rules 16/0/0 · ruff clean · per-translation tests
  → docs (CHANGELOG / SESSION_STATE / this file) → save
```

## Gotchas (carried from the deuterocanon + WLC/LXX arcs)

- **GREP IS UNRELIABLE FOR GREEK/HEBREW/ARABIC** in the translation files (Unicode NFC mismatch) — verify by Read, not Grep.
- **Shared split files**: a raw `git diff` / `generate_verse_popups --dry-run` shows neighbor books + "~60 books" as touched — a shared-file artifact, NOT real drift. Trust a content-level aside-by-id compare.
- **Byte-compat**: after `ruff format`, the OTHER translations' files must be byte-identical to HEAD (prove it); only the new translation's files + `_meta.yaml` change.
- **Don't run two epubcheck JVMs concurrently** (HotSpot OOM → stray `hs_err_pid*.log` in repo root).
- Python = `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe` + `$env:PYTHONUTF8="1"`; tests one file at a time (don't run the full `tests/test_scripts.py` — it hangs on build/socket smokes).
- `extract_translation.py` already maps `PRA→paz`, `PRM→man`, `1ES→1es`, `BAR ch6→lje`, `ESG→aes`, `4ES→2es` — so the Catholic Douay/Vulgate deutero books land on the right project codes automatically (BUT their VERSIFICATION still needs the Vulgate adapter).
