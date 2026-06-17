# Platform implementation matrix (Round 9 output)

**Status:** SUPERSEDED — see `notes/2026-06-18-platform-implementation-matrix.md`.
**Gate:** Round-8 remediation complete before Round 9 audit starts.

Legend: ✅ proven · ⚠ partial · ❌ unsupported · ❓ Round 9 research · TBD design

| Feature | Apple M2 (`tablet`) | Kobo M3 (`eink`) | Kindle M4b (`kindle`) | Play M5 (`everywhere`?) |
|---|---|---|---|---|
| Popup footnotes | ✅ native in-place | ⚠ KePub stripped preview | ❌ → endnotes (M4b) | ❓ |
| Study notes UI | Verse-end badge → merged popup | Glossary backmatter (K-R9c) | Chapter-tail notes (TBD) | TBD |
| Translation UI | `vn-link` at verse start | `vn-link` popup | Per-verse trial (user) | TBD |
| Collapsible ToC | ✅ | ❌ flat | ❌ | ❌ stuck (expected) |
| Embedded fonts | ✅ | ✅ + font pack | partial KFX | ❓ |
| Page breaks | ✅ CSS | spine split only | partial | ❓ |
| Byte budget / size | N/A | ≤ ~4,400 stripped (K-R4-2) | N/A | ❓ |
| Build profile | `tablet` | `eink` + kepubify | `everywhere` + `kindle_post` | `everywhere` or `play` |
| Catalog column | M2 live 45 | M3 live 45 | M4 live 45 | M5 not live |
| Device proof | 1 edition spot | 5-tap list §4 B6 | STK + phone re-gate | Phone §Play |

## Cross-reader rule

**No fork bleed:** Kobo K-R9 and Kindle M4b compromises must not alter `tablet` builds
(`notes/2026-06-15-apple-m2-layout-directive.md`).

## Round 9 fills

- [ ] `platform-apple` brief → M2 polish plan
- [ ] `platform-kobo` brief → K-R4-2 + tap round 9
- [ ] `platform-kindle` brief → M4b fork spec
- [ ] `platform-play` brief → M5 profile decision