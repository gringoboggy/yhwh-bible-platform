# HOME_HTML — finalized AA-clean color spec (Mac → WIN, turn 44 item 4)

_Mac lane, 2026-06-09. Finalizes the "Color rule for HOME + the app" section of `docs/superpowers/specs/2026-06-09-idiot-proof-app-design.md` with **per-element, independently-recomputed WCAG ratios** so the CDN-free `HOME_HTML` ships AA-clean on the first build. Pairs below were computed from sRGB relative luminance (WCAG 2.1 1.4.3/1.4.11), not estimated._

## Why this exists
`HOME_HTML` is **CDN-free** (design spec §1 "Resolved divergence") — it hand-writes ~30 lines of CSS from a `MS_PALETTE` constant exported from `_design.py`, so it is structurally immune to every η.1-skin hazard the adversarial review found (`2026-06-09-eta1-skin-adversarial-review.md`). That means HOME does **not** inherit the skin's fixes — it must carry its own AA-correct colors. This note is that color contract. It also bakes in the **user's decision** (keep gold primary; indigo for links/accents; lighter `#C49A2E` gold hover).

## `MS_PALETTE` — the single source of truth (export from `_design.py`)
Export these as a dict so HOME's `<style>` and the skin never drift (design spec §1 mitigation):

| token | hex | role |
|---|---|---|
| `vellum` | `#F4ECD8` | page / hero ground |
| `parchment` | `#FBF6E9` | card / panel ground |
| `ink` | `#2B2118` | body + on-gold button text |
| `sepia` | `#574532` | secondary / subtitle text |
| `muted` | `#6E5840` | hint / fine-print text (the skin's H4 fix tone) |
| `gold` | `#B8860B` | **primary button fill** (rest) |
| `gold-hover` | `#C49A2E` | primary button fill (hover) — **lighter, not darker** |
| `gold-line` | `#9A6E12` | hairlines / borders / top-accent rules ONLY |
| `indigo` | `#243B6B` | links, secondary actions, focus ring, accents |
| `antique` | `#FCF8EF` | text on red (alt CTA) |
| `red` | `#7A1F2B` | destructive + the alt primary (site-parity) |
| `red-dark` | `#5E1722` | red hover |

## Per-element color map for `HOME_HTML` (verified)

| HOME element | foreground | background | ratio | verdict |
|---|---|---|---|---|
| Body / welcome line | `ink #2B2118` | `vellum #F4ECD8` | **13.38** | AA ✅ |
| Subtitle / secondary text | `sepia #574532` | `vellum` | **7.75** | AA ✅ |
| Fine print (e.g. "free, no account") | `muted #6E5840` | `vellum` | **5.69** | AA ✅ |
| Any card/panel text | `ink` | `parchment #FBF6E9` | **14.59** | AA ✅ |
| **Primary CTA label (rest)** — DEFAULT | `ink #2B2118` | `gold #B8860B` | **4.84** | AA ✅ |
| **Primary CTA label (hover)** — DEFAULT | `ink` | `gold-hover #C49A2E` | **6.01** | AA ✅ |
| Secondary text-links (the 2–3 indigo doors) | `indigo #243B6B` | `vellum` | **9.32** | AA ✅ |
| Secondary links over a card | `indigo` | `parchment` | **10.17** | AA ✅ |
| Footer "Maintainer tools" link | `indigo` | `vellum` | **9.32** | AA ✅ |
| Hero/section hairline + button top-accent | `gold-line #9A6E12` | `vellum` | 3.87 | UI 3:1 ✅ (decorative; **never text**) |
| Hairline over a card | `gold-line` | `parchment` | 4.22 | UI 3:1 ✅ |

**Focus ring (keyboard a11y, all interactive elements):** `2px solid indigo #243B6B` (9.3:1 on vellum) — already the skin's focus token, so HOME matches.

## The ONE rule that prevents the skin's mistakes on HOME
- **Gold is a FILL or a hairline — NEVER a text color.** Gold-as-text on vellum is 2.76:1 (fails). HOME uses gold only as the CTA button background and as `gold-line` hairlines. (This is the L2 guard from the skin review, applied preemptively.)
- **Every link/secondary/accent is indigo**, not gold — that is the user's stated preference and the accessible answer everywhere gold-as-text would fail.
- **The CTA is the only gold element.** One gold button per the design spec's "ONE primary action."

## Default vs. the red site-parity alternative (both AA-clean — user's open Q2)
The design spec's open question 2 is gold-keep (default) vs. red-for-site-parity. Both are AA-confirmed, so WIN can ship the default and the user can flip later with a one-line swap:

| | rest | hover | rest ratio | hover ratio |
|---|---|---|---|---|
| **DEFAULT — gold** (user loved it) | `ink` on `gold #B8860B` | `ink` on `#C49A2E` | 4.84 ✅ | 6.01 ✅ |
| ALT — red (matches site `.btn-primary`) | `antique #FCF8EF` on `red #7A1F2B` | `antique` on `red-dark #5E1722` | 9.63 ✅ | 12.22 ✅ |

Recommendation unchanged: **ship gold** (the user explicitly loved it; ink-on-gold is NOT the "gold as text" the site forbids). If the user later wants strict parity, switch the CTA fill to `red`/`red-dark` with `antique` text — the same one element, still AA.

## Implementation note for WIN
- These colors only need to land in the new `scripts/templates/home.py` `<style>` (built from `MS_PALETTE`) — HOME is CDN-free, so there is **no Tailwind class** to fight. The skin's separate AA fixes (the review doc) still apply to the other 20 consoles independently.
- Recompute is cheap if you change a hex: the relative-luminance formula is in this turn's worklog; ping Mac and I'll re-verify any new pair.

— Mac, turn 44. Item 4 of the fat backlog. (Items: 1 S2-review = running; 2 M2 QA matrix; 3 STAGE-F copy; **4 this**; 5 dmg recipe.)
