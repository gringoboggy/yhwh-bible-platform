# Translation-spine arc — Douay / JPS / Vulgate / Arabic (Phase-2 finish)

**Status:** PREPARED 2026-05-23 (data acquired + scope verified; ingest NOT started — that is the next arc).
**Owner of the next session:** start here. Pattern is proven (WLC / LXX-Swete / Byzantine-NT / the 11 deuterocanon books).

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

### 1. `arabic-vandyke` — EASIEST, do FIRST
66-book Protestant canon, Ps 9 = 20 (KJV-aligned). Likely **pure identity** — but VERIFY a handful of
known divergence-prone loci first (Ps 9/10 split confirmed KJV-style; spot-check a Psalm-title psalm,
the Joel/Malachi/3 John chapter boundaries, Acts 19:41). RTL is already handled (`arabic` registry
entry has `"dir": "rtl"`; the popup machinery renders RTL like WLC Hebrew). Plain text → HTML-escaped
at render (NOT trusted_html — correct). No deuterocanon (Protestant 66). **Wire:** add `"arabic"` to
`popup_versions._BAKED_NOW` → regen popups for the 66 books → categorize-diff → verify.

### 2. `jps` — MEDIUM, do SECOND
39-book Tanakh, 23,145 verses ≈ WLC's 23,142, Ps 9 = 20. JPS 1917 is English text on the
**Hebrew/Masoretic versification** — the SAME versification WLC uses. So **reuse
`versification.wlc_to_kjv_map`** (the morphhb `VerseMap.xml` Hebrew→KJV map already in the repo) rather
than deriving a new one. Mechanism: `extract_translation.py` has no remap hook, so either (a) add an
optional remap callback to it, or (b) write a small dedicated `extract_jps.py` that applies
`wlc_to_kjv_map` (mirror `extract_wlc_morphhb.py`'s remap usage). Verify against the same WLC
divergence loci already pinned in `tests/test_wlc_ingest.py` (Psalm superscriptions, the Gen 31/32
boundary, the Hebrew verse-1-title psalms). **Wire:** add `"jps"` to `_BAKED_NOW` → regen → verify.

### 3 + 4. `douay-rheims` + `vulgate-clementine` — HARDEST, do TOGETHER, LAST
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
