# Platform implementation matrix (Round 9)

**Status:** FILLED — synthesized from four Round-9 platform briefs.
**Date:** 2026-06-18 · **Truth owner:** WIN lane
**Sources:** `notes/2026-06-18-platform-{apple,kobo,kindle,play}.md`

Legend: ✅ device-proven · ⚠ partial / code-shipped pending QA · ❌ unsupported or failed · ❓ unverified · 🔧 design TBD

---

## Feature × reader matrix

| Feature | Apple M2 (`tablet`) | Kobo M3 (`eink` + kepubify) | Kindle M4 (`everywhere` + `kindle_post`) | Play M5 (`everywhere`) |
|---|---|---|---|---|
| **Popup footnotes** | ✅ native in-place sheet (M2-1 PASS) | ⚠ KePub tag-stripped preview ≤4,498 chars (gen 35:18 re-tap pending) | ❌ KFX collapses to chapter page-break anchors (phone FAIL) | ❓ no vendor docs; custom Android engine |
| **Study notes UI** | Verse-end **one** badge → merged `verse-notes` popup | Per-category badges → **glossary backmatter** navigate (K-R9/K-R13) | **M4b shipped** — inline ◈ suppressed; chapter-tail `kindle-chapter-study` (structural gate 6/6; phone STK matrix pending) | Same as `everywhere` (merged popups) — ❓ |
| **Translation UI** | `vn-link` at verse start → `vnote-*` popup | `vn-link` at verse start → preview popup (unchanged) | `vn-link` kept inline; STK 6/6 readable translation (2026-06-14); no true popup | `vn-link` present — ❓ |
| **Collapsible ToC** | ✅ opt-in (`TARGET_CAPS.tablet.toc_expandable`) | ❌ flat pills (`toc_expandable: false`) | ❌ flat | ❌ closed-and-stuck (expected fail) |
| **Embedded fonts** | ✅ OFL embed + system fallback | ✅ embed + Cardo font-pack sideload | ⚠ KFX partial; single `dc:language` after `kindle_post` | ⚠ vendor ✅; phone verify Geʽez/Arabic |
| **Page breaks** | ✅ CSS + spine split | **spine split only** (CSS `page-break-*` = N on EPD) | ⚠ chapter `page-break-before` + piece boundaries | ❓ not documented |
| **Multi-script preview** | Popup `lang` spans + embed | OPF `dc:language` chain only (preview strips tags) | `.vn-sep` kept in footnote text | OPF 6-value block — ❓ |
| **Byte / size budget** | N/A (no cap) | ≤4,400 stripped + ≤8,858 B serialized (kepub) | N/A | ~25–30 MiB artifact; under 2 GB limit |
| **Build profile** | `target_reader=tablet` | `eink` → kepubify v4.0.4 | `everywhere` → `kindle_post.make_kindle_safe` | `everywhere` copy (no post-process) |
| **Catalog column** | M2 · 45 assets · live | M3 · 45 `.kepub.epub` · live (user tap sign-off pending) | M4 · 45 assets · live (UX gap) | M5 · **not live** until phone QA |
| **Device proof** | M2 checklist (1 edition spot) | Round-13 PASS + round-9 P0 matrix pending | STK 6/6 delivery only; link targets **not** gated | **Zero proof** — blocks M5 |

---

## Recommended option per reader (from briefs)

| Reader | Option | Summary | Owner / next |
|---|---|---|---|
| **Apple** | **A** — status quo + optional popup CSS polish | Keep `tablet` profile; no Kobo/Kindle fork bleed | Mac build tablet artifact; user M2 re-test |
| **Kobo** | **A** — ship proven stack; close QA gaps | K-R4-2 + K-R9/K-R13 closed in builder; re-tap gen 35:18 | User P0 tap matrix; WIN doc sync done |
| **Kindle** | **A** — M4b marker suppress + chapter-tail study | `apply_kindle_m4b` + `verify_kindle_m4b` shipped (Mac turn 124+); 6/6 structural re-gate (turn 127) | User STK phone matrix §7; Mac STK live poll blocked (no library container) |
| **Play** | **A** — keep `everywhere`; gate on phone QA | No `play` profile until failures proven; fan M5 after rounds 1–3 PASS | User uploads navy EPUB per `EREADERS.md` §Play |

**Declined across readers:** Kobo Option C (revert popup study layout) · Play Option C (skip M5 column) · Kindle Option C (hope for KFX fix) · Apple Option C (port Kobo glossary to tablet).

---

## Cross-reader rules (non-negotiable)

1. **No fork bleed** — Kobo K-R9 glossary and Kindle M4b suppress must not alter `tablet` builds (`notes/2026-06-15-apple-m2-layout-directive.md`).
2. **Kindle `kindle_post` is Amazon-specific** — do not apply to Play if popups fail; design Play-specific path under Option B.
3. **KePub required for Kobo popups** — plain `.epub` uses ADE engine (no popups).
4. **`<details>` ToC** — off for `eink`, `kindle`, `everywhere`; opt-in only on `tablet`.

---

## Open gates (device / build)

| Gate | Reader | Blocks | Status |
|---|---|---|---|
| gen 35:18 re-tap | Kobo | Option B decision for translation vnotes | User device |
| Round-9 P0 tap matrix | Kobo | M3 live claim final sign-off | User device |
| M5 phone QA rounds 1–3 | Play | M5 catalog fan-out + `play.live` | User device |
| M4b phone STK matrix | Kindle | Catalog UX sign-off | User STK (structural 6/6 green @ turn 127) |
| Thorium live sim | Apple / Play | Agent pre-device gate | Mac turn 127 — structural PASS; CDP taps MCP/manual |
| M2 popup CSS polish (optional) | Apple | Cosmetic only | Mac + user |
| `rx-surfaces` dim | All | Popup/cross-piece scans on built artifacts | WIN after `ci.py` |
| `tests-run` / full `ci.py` | All | Round-9 WIN dim closure | WIN in flight (~6h) |

---

## Build path reference

```text
FORMAT_MATRIX columns
  apple  → build_edition --target-reader tablet
  kobo   → build_edition --target-reader eink → kepubify
  kindle → build_edition --target-reader everywhere → kindle_post
  play   → build_edition --target-reader everywhere (copy; phase M5 after QA)
```

---

## Brief cross-links

| Brief | Key shipped state | Top survivor |
|---|---|---|
| [apple](2026-06-18-platform-apple.md) | M2-1 PASS; no tablet fork needed | Popup typography polish (low) |
| [kobo](2026-06-18-platform-kobo.md) | K-R9/K-R13 default; gates 4g/4n/4g-bis | gen 35:18 inversion (med) |
| [kindle](2026-06-18-platform-kindle.md) | `kindle_post` shipped; STK delivery OK | M4b not implemented (high UX) |
| [play](2026-06-18-platform-play.md) | Staged `everywhere` navy EPUB on v0.1.0 | Zero device proof (high) |