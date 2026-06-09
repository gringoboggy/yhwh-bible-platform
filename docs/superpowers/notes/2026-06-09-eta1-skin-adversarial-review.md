# η.1 Manuscript-Skin — Adversarial Review (for WIN)

_Date: 2026-06-09 · Reviewer: Mac lane · Status: all findings skeptic-verified, file:line re-confirmed against the live tree._

## Verdict

**The loved η.1 manuscript skin does NOT yet hold up — ship-blocking before v0.1.0.** The vellum/gold look is sound and most of the page repaints correctly, but the skin (a) drives **every primary-button hover state below WCAG AA (3.45–3.46:1)**, (b) **catastrophically breaks dark-mode inputs** on greek/hebrew (typed text 1.08:1 — illegible), (c) leaves **hint text (text-slate-400, ~176 sites) at 2.58–2.81:1**, and (d) **structurally cannot reach** the dozen+ CSS-rule-hex and inline-style spots (matrix/compare/wizard/build_tracker/welcome-overlay) so they read as cool-blue/green islands on the warm ground — including some invisible (1.0–1.5:1) data states. There is also a **brand mismatch**: the site's primary action is RED, the skin paints it GOLD with small text, which the site's own CSS comment explicitly forbids ("never as body text"). None of these are cosmetic-only; the contrast failures are accessibility regressions introduced purely by the skin. Fix the HIGH set before tagging v0.1.0.

---

## ★ Mac-controller addendum (2026-06-09) — cross-check + 2 corrections + the user's color decisions

This review was independently **cross-checked** by the controller before handoff:
- **WCAG math confirmed** against an independent relative-luminance computation: gold rest 4.84:1, gold-line hover 3.46:1 (H1), white-on-emerald 3.77:1 (H5/H6), slate-400 hint 2.58/2.81:1 (H4), gold-as-text 2.76:1 — all match. The L2 "gold-as-text" refutation is also correct (the skin uses gold only as a button *background*, never as a text color; and ink-on-gold is NOT "gold as text" — so the site's "gold never as body text" rule, cited in H7, is not actually violated by the gold buttons).
- **★ CORRECTION to H1's keep-gold fix:** the doc says "darken the hover ground (e.g. ~#7A5A0E) so ink clears 4.5:1" — that is **backwards**. Dark ink #2B2118 on a *darker* gold loses contrast (that's exactly why #9A6E12 hover = 3.46:1 < the #B8860B rest = 4.84:1). To keep gold + ink, the hover must go **LIGHTER**: verified **`#C49A2E` = 6.01:1** ✅ (or #CDA434 = 6.72:1). Use a lighter gold for the hover, not darker.

**User color decisions (2026-06-09) — apply these:**
1. **Keep the gold primary buttons** (the user loved them; rest passes AA at 4.84:1). Fix ONLY the hover → lighter `#C49A2E` (6.01:1). This supersedes H7's "recolor everything to red" as the *default* — but see (3).
2. **Indigo is the sanctioned accent** (user: *"I like indigo, if gold doesn't work for some things we can implement indigo"*). Indigo `#243B6B` = **9.3–10.8:1** on the beige grounds. Use it for **links, secondary actions, focus rings, and every interactive accent where gold-as-text would fail** (the 2.76:1 case). It's already the focus-ring token, so this is consistent. This is the accessible fix for any "gold doesn't read" spot (M7 stepper, links, info states). Reserve gold for button *fills* + hairlines.
3. **OPEN (user to confirm):** H7's full "primary → red for site-parity" is a coherent ALTERNATIVE (antique-on-red 9.7:1, matches the site's red CTA) but it overrides the user's loved gold. **Default = keep gold + lighter hover + indigo accents** (fixes H1's AA failure without discarding gold). If the user prefers strict site-parity, switch the primary to red instead. Either way H5/H6 (route emerald CTAs onto the primary utility), H2 (dark-mode input), H4 (hint text), and the M-tier data-state hexes still apply unchanged.

Everything below is the finders' verified output, kept intact.

---

## Why these are skin-caused, not pre-existing

The skin (`scripts/templates/_design.py` MANUSCRIPT_SKIN_CSS ~L183, applied by `apply_manuscript_skin()` ~L255, injected into every console at `scripts/web.py:1235` `_send_html`) re-tones the Tailwind **utility** palette (slate + blue scales, `.bg-white`, `.bg-blue-600/700`) and a few global `:root` tokens. It **cannot reach**: (1) CSS-rule hex inside each template's own `<style>` block; (2) inline `style=` strings (welcome overlay); (3) the `emerald`, `amber`, `purple`, `rose` Tailwind families (only slate + blue are remapped, `_design.py:194-203`); (4) the dark-theme token block `:root[data-theme="dark"]` (`_design.py:358-372`). Every "island" finding is one of those four structural gaps; every contrast-regression finding is a value the skin DID set but set too low.

---

## HIGH severity (ship-blocking)

### H1 — Primary-button hover fails AA (every skinned console)
- **Console:** ALL skinned consoles — every primary action button on hover/press (compare "Show" `compare.py:67`; distribution Save/Upload; matrix save; sources "Fetch all" `sources.py:82`; wizard "Next →" `wizard.py:155/181/251/262/274/317`; index save; diff swap; publisher "Save" `publisher.py:325`, "Save these changes" `publisher.py:594`).
- **Category:** contrast. **Ratio:** **3.46:1 hover (4.84:1 at rest)** — fails AA 4.5 for normal-size button text (Tailwind btn = text-sm/base, not bold ≥18.66px, so the 3:1 large-text exception does not apply).
- **Problem:** `_design.py:237` remaps `.bg-blue-700, .hover\:bg-blue-700:hover { background: var(--ms-gold-line)=#9A6E12 !important; color: var(--ms-ink)=#2B2118 !important }`. Dark ink #2B2118 on gold-line #9A6E12 = 3.46:1. The resting state (#B8860B + ink) passes at 4.84:1 — so the SAME label drops below AA only on hover, a regression introduced purely by the hover retone. `_design.py:238` forces child text to the same failing ink. (Originally filed 3× — findings 1/13/14 — same root defect.)
- **Fix:** Do NOT switch the hover label to antique #FCF8EF — that only reaches 4.29:1, still below AA (the original "~5.2:1"/"~4.7:1" estimates were wrong). Either (preferred, see H7) recolor the whole primary to RED, OR darken the hover ground so dark ink clears 4.5:1 (e.g. ~#7A5A0E or darker — verify ≥4.5:1 against #2B2118). Fix the child override at `:238` to match. Re-run contrast on both resting (`:236`) and hover (`:237`).
- **file:line:** `scripts/templates/_design.py:236-238`

### H2 — greek/hebrew dark-mode input typed text is near-invisible
- **Console:** hebrew, greek. **Category:** contrast. **Ratio:** **1.08:1** (typed text) — fails AA 4.5 catastrophically.
- **Problem:** hebrew/greek load DARK_MODE_JS, which sets `html[data-theme=dark]` before paint whenever OS `prefers-color-scheme:dark` OR saved `ebible_theme=dark` (`_design.py:1901-1922` — automatic, not just an explicit toggle). In dark mode the lookup `<input class="… theme-bg-surface theme-text …">` (`hebrew.py:75`, `greek.py:69`) resolves `theme-text` → `--color-text-primary` = slate-100 #F1F5F9, because the skin overrides only the LIGHT `:root` tokens (`_design.py:214-225`) and never the dark block (`_design.py:358-372`). The skin separately forces `input { background-color:#FFFDF7 !important }` (`_design.py:246`) on EVERY input. Result: light slate-100 typed text on near-white #FFFDF7 = **1.08:1**, illegible. (Placeholder claim is weaker — no `::placeholder` rule applies theme-text-muted, so placeholder is browser-default; the load-bearing failure is the typed text.)
- **Fix:** Make the input bg theme-aware OR add a dark-token override. Either change `_design.py:246` from `#FFFDF7 !important` to `background-color: var(--color-bg-surface, #FFFDF7) !important` (field follows the active theme), OR add a `:root[data-theme="dark"]{ --color-text-primary:#F4ECD8; --color-bg-surface:#322619; … }` counterpart to `:214-225`.
- **file:line:** `scripts/templates/_design.py:246` (input bg `!important`) vs `:358-372` (dark tokens un-overridden); `hebrew.py:75`; `greek.py:69`

### H3 — skin × dark-mode leaves a half-dark / half-parchment UI
- **Console:** build_tracker, greek, hebrew, preflight (theme-token + dark-mode family). **Category:** broken-layout.
- **Problem:** These four load DARK_MODE_JS + THEME_TOKENS_CSS. DARK_MODE_JS sets `html[data-theme=dark]` on first paint from OS preference or saved theme, activating `:root[data-theme=dark]` (`_design.py:358-372`) → slate-900/800 surfaces + blue accents. The skin overrides only the light `:root` tokens, never the dark block, AND hardcodes `html,body{ background:var(--ms-vellum) }` (`_design.py:226`) + `.bg-white{ var(--ms-parchment) !important }` (`_design.py:229`) with NO theme guard. A dark-mode user gets dark slate panels floating on a forced light parchment/vellum page, with light-on-light / dark-on-dark text in the mixed zones. (matrix/wizard correctly excluded — they use bg-slate-50/bg-white, not theme tokens.)
- **Fix:** In MANUSCRIPT_SKIN_CSS add a matching `:root[data-theme="dark"]` override remapping the dark tokens to a dark MANUSCRIPT palette (e.g. #221C15 page / #2B2118 surface / #F4ECD8 text / gold accents), AND scope `_design.py:226` + `:229` behind `:root:not([data-theme=dark])` so the skin only repaints the light state. Verify each of the 4 consoles in BOTH light and dark. (Alternatively disable the dark toggle on skinned consoles.)
- **file:line:** `scripts/templates/_design.py:226, :229` + missing `:root[data-theme=dark]` override (clashes `:358-372`)

### H4 — text-slate-400 helper/hint text fails AA on the new light grounds
- **Console:** ALL (global skin) — muted/hint text. **Category:** wcag. **Ratio:** **2.58:1 (vellum) / 2.81:1 (parchment)** — fails AA 4.5.
- **Problem:** The JS scale remap sets slate-400 → #A8916B (`_design.py:196`). On parchment #FBF6E9 = 2.81:1, on vellum #F4ECD8 = 2.58:1. text-slate-400 is used **176× across templates** (grep-confirmed) as hint/optional/placeholder text on light cards, including the flagship wizard: `wizard.py:174,176,243,294,346` ("(lowercase, hyphenated…)","(shown to readers)","(optional)", done-filename). The site's secondary text is --sepia #574532 (~6.2:1 on parchment); the skin's slate-400 tone is a low-contrast island the site does not have. Deterministic (the CDN config script is synchronous, so the scale always lands).
- **Fix:** Darken slate-400 in the JS scale (`_design.py:196`) toward the site's secondary-text tone, e.g. #6E5840 / --ms-sepia #574532 (~6:1 on parchment). slate-500 is already #6E5840 (passes), so collapsing 400 toward 500's darkness keeps the manuscript hue while clearing AA for the ~176 sites.
- **file:line:** `scripts/templates/_design.py:196` (slate.400)

### H5 — wizard primary CTAs are emerald (untouched by skin) and fail AA
- **Console:** wizard. **Category:** consistency / wcag. **Ratio:** **white-on-emerald-600 #059669 = 3.77:1** — fails AA 4.5.
- **Problem:** The two PRIMARY terminal CTAs "Build my Bible →" (`wizard.py:328`) and "Download EPUB" (`wizard.py:347`) are `bg-emerald-600 hover:bg-emerald-700 text-white`, while EVERY other wizard action button ("Next →") is `bg-blue-600` (`wizard.py:155,181,251,262,274,317`). The skin remaps only slate + blue (`_design.py:194-203`); emerald is untouched. So the single most important button is bright green (3.77:1 white-on-emerald, FAILS AA) while the lesser buttons become gold — **hierarchy inverted** and green clashes with the vellum. Same untouched-emerald in build_my_bible (text-emerald accents).
- **Fix:** (a, preferred) Route through the gold/red primary utility — change `bg-emerald-600 hover:bg-emerald-700` → `bg-blue-600 hover:bg-blue-700` at `wizard.py:328` and `:347` so the skin gives them the primary treatment (AA-pass, matches every other action). OR (b) add a skin rule promoting emerald primaries with a compliant darker hover (NOT 3.46:1). Option (a) is cleaner and keeps emerald free for true success semantics.
- **file:line:** `scripts/templates/wizard.py:328, :347`

### H6 — index "+ add note" button is emerald, fails AA
- **Console:** index (note editor at `/`). **Category:** wcag. **Ratio:** **white-on-emerald-600 = 3.77:1** — fails AA 4.5.
- **Problem:** `index.py:68-69` `+ add note` is `bg-emerald-600 hover:bg-emerald-700 text-white` — left bright emerald (only bg-blue-600 is remapped). The blue primaries the skin recolors to gold measure 4.84:1 and pass; the un-remapped green button is the one now failing on the manuscript page.
- **Fix:** Change `bg-emerald-600 hover:bg-emerald-700 text-white` → `bg-blue-600 hover:bg-blue-700 text-white` at `index.py:68`. Same fix as H5.
- **file:line:** `scripts/templates/index.py:68`

### H7 — primary-action color mismatches the site (and gold-as-text the site forbids)
- **Console:** ALL (global skin) — primary action color. **Category:** consistency.
- **Problem:** The website's primary action is RED: `.btn-primary` / `.download` / `.btn-platform` use `background:var(--red) #7A1F2B` with antique text (`website/style.css:159-163, 117-122, 208-213`). `style.css:1-3` EXPLICITLY reserves gold for "accent rule / large marks only, never as body text." The η.1 skin remaps every primary button (BTN_PRIMARY = bg-blue-600 hover:bg-blue-700, `_design.py:53`) to GOLD fill with small dark-ink text (`_design.py:236`). So the app's main CTA is a gold block of small text — the one use the site's own comment prohibits — and does not match the site's red CTA.
- **Fix:** `_design.py:236-237` — to MATCH the site, remap `.bg-blue-600` → `background:var(--ms-red) #7A1F2B; color:var(--ms-antique) #FCF8EF` (antique-on-red ~9.7:1, AA-pass) and `.bg-blue-700`/hover → `var(--ms-red-dark) #5E1722` (antique on red-dark ~11:1). Keep gold for hairlines/borders/top-accents only. **This single change also resolves H1's hover failure and converges H5/H6/H10.**
- **file:line:** `scripts/templates/_design.py:236-237` (vs `website/style.css:159-163`)

### (H7 also subsumes the standalone "primary-button hover" finding) — `sources.py:82`, `publisher.py:325,594`
Same `.bg-blue-700` → #9A6E12 + ink = 3.45:1 hover defect across all BTN_PRIMARY sites; auto-fixed if the red recolor in H7 is adopted (antique on red-dark ~11:1). If gold is kept instead, #9A6E12 is too dark to carry ink text — use antique/white text on it.

---

## MEDIUM severity

### M1 — active/hover book-row highlight invisible on vellum
- **Console:** build_my_bible (and sources). **Category:** broken-layout. **Ratio:** `#dbeafe` active row vs `#F4ECD8` vellum = **1.04:1** (invisible); hover `#f1f5f9` = 1.07:1.
- **Problem:** Active highlight is hardcoded `.book-row.active{background:#dbeafe;font-weight:600}` (`build_my_bible.py:44`) — a CSS-rule hex the skin cannot reach. On vellum the selected-book highlight is effectively INVISIBLE; in a book→chapter→verse navigator, losing the selected-row indicator is a real usability break. Hover (`:43`) is the same (1.07:1). Identical at `sources.py:30` (hover) / `sources.py:31` (active).
- **Fix:** Retone the row-state hex to the manuscript palette: `.book-row.active{background:#E3D4AE;font-weight:600}` (skin's slate-200 tone) and `.book-row:hover{background:#EFE6CE}`, in `build_my_bible.py:43-44` AND `sources.py:30-31`. font-weight:600 aids but is not enough alone.
- **file:line:** `scripts/templates/build_my_bible.py:44 (and :43)`; `scripts/templates/sources.py:31 (and :30)`

### M2 — matrix count states near-invisible on parchment
- **Console:** matrix. **Category:** readability. **Ratio:** count-disabled **1.55:1**; count-zero **1.38:1** (both fail AA 4.5 and AA-large 3.0).
- **Problem:** `.count-disabled { color:#fbbf24; font-style:italic }` (`matrix.py:34`) and `.count-zero { color:#cbd5e0 }` (`matrix.py:33`) are CSS-rule hex the skin does NOT remap. The legend (`matrix.py:359-360`) and table sit in a `bg-white` section (`matrix.py:354`) the skin forces to parchment #FBF6E9. Amber on parchment = 1.55:1; #cbd5e0 = 1.38:1. These convey real data states ("potential/filtered-out" and "no notes") and are near-invisible.
- **Fix:** `matrix.py:33-34` — deepen to readable manuscript tones: `.count-disabled { color:#9A6E12; font-style:italic }` (use #7A5A0E for AA-large) and `.count-zero { color:#574532 }` at reduced opacity. Borderline pre-skin; the warm retone is the trigger.
- **file:line:** `scripts/templates/matrix.py:33-34`

### M3 — compare verse-num + "missing" placeholder collapse on parchment
- **Console:** compare (public buyer-demo surface). **Category:** readability. **Ratio:** verse-num **2.38:1**; missing **1.38:1** (both fail AA 4.5).
- **Problem:** `.verse-num { color:#94a3b8 }` (`compare.py:28`) and `.missing { color:#cbd5e1; font-style:italic }` (`compare.py:29`) are CSS-rule hex untouched by the skin. Results sit in a `bg-white` card retoned to parchment. Verse numbers 2.38:1, the "missing verse" italic placeholder 1.38:1 — effectively invisible. A reader sees blank-looking gaps where verses are absent and cannot read verse numbers. Pre-skin these were cool-gray on near-white (~3:1) and passable; on vellum they collapse.
- **Fix:** `compare.py:28-29` — `.verse-num { color:#574532 }` (sepia, 8.7:1) and `.missing { color:#9A6E12; font-style:italic }` (~3.4:1; use #6E5840 for full AA).
- **file:line:** `scripts/templates/compare.py:28-29`

### M4 — form inputs resting border fails UI 3:1
- **Console:** all skinned consoles — form inputs/select/textarea. **Category:** wcag. **Ratio:** **2.28:1** (fails UI 3:1).
- **Problem:** `_design.py:246` sets `border: 1px solid rgba(154,110,18,0.60) !important; background-color:#FFFDF7 !important`. Compositing #9A6E12 at 0.60 alpha over #FFFDF7 gives an effective ~#C2A76E border at 2.28:1 against the fill — below WCAG 1.4.11 3:1 for the boundary of an active UI component. Inputs rely on their border to read as an entry affordance; at 2.28:1 the resting outline is faint. (Focus → indigo is fine; only the resting border fails.)
- **Fix:** `_design.py:246` — drop the alpha. Solid #9A6E12 on #FFFDF7 = 4.48:1 (passes). Change to `border: 1px solid var(--ms-gold-line)` (or rgba(154,110,18,0.85)+ to reach ~3:1). _Note: pairs with H2 — also make the fill theme-aware._
- **file:line:** `scripts/templates/_design.py:246`

### M5 — blanket 3px blood-red top stripe on neutral cards
- **Console:** export, ops, publisher, sources, apihelp (~all bg-white-card consoles). **Category:** broken-layout / consistency.
- **Problem:** `_design.py:249` `.rounded-lg.border { border-top: 3px solid var(--ms-red)=#7A1F2B }` (no `!important`, no scoping) matches ANY element carrying both `rounded-lg` and `border` — striping a red top edge on every neutral card. export stat tiles (`export.py:88,92,96,100`) + section cards (`:69,:79,:109,:114,:145`); ops 6 metric tiles (`ops.py:51,64,74,85,95,105`); sources 4 panels (`sources.py:74,102,141,151`); apihelp 4 cards (`apihelp.py:54,58,64,77`); publisher (`publisher.py:316`). Plain stat tiles read as alert/error cards; the red carries no meaning here. The intentional emerald success card (`export.py:123`) uses `border-2 border-emerald-500` (no plain `border`) so it correctly dodges the rule — an inconsistency in itself.
- **Fix:** Scope the red top-accent to deliberate hero/section cards only — gate behind an opt-in class (e.g. `.ms-card-accent`) added to intended cards, instead of the blanket `.rounded-lg.border` at `_design.py:249`. At minimum exclude compact p-3 stat tiles; consider gold rather than alert-red on neutral cards.
- **file:line:** `scripts/templates/_design.py:249`; sites: `export.py:88,92,96,100`; `ops.py:51,64,74,85,95,105`; `sources.py:74,102,141,151`; `apihelp.py:54,58,64,77`; `publisher.py:316`

### M6 — build_tracker heat-grid: cold green on vellum + low steps indistinct
- **Console:** build_tracker. **Category:** readability. **Ratio:** heat-0 #f8fafc vs heat-1 #ecfdf5 = **1.007:1** (negligible separation).
- **Problem:** The coverage heat-grid is hardcoded CSS-rule hex (`.heat-0..heat-7` at `build_tracker.py:37-44`) on the cool-gray→emerald scale (#f8fafc..#059669) the skin cannot retone. On vellum these read as saturated cold-green islands; heat-0 #f8fafc / heat-1 #ecfdf5 differ by only 1.007:1 — indistinguishable, near-white-blue on beige. The green ramp's luminance spacing was tuned for a white page.
- **Fix:** Retone the heat scale to a warm/gold ramp in `build_tracker.py:37-44` (anchor on #B8860B/#574532) so it reads as "illuminated" density and the low steps separate from the page. (Dark-mode concern folded into H3.)
- **file:line:** `scripts/templates/build_tracker.py:37-44`

### M7 — wizard progress stepper / pick UI stays bright blue+green (half-skinned)
- **Console:** wizard. **Category:** consistency.
- **Problem:** The 5-step stepper and pick UI are hardcoded CSS-rule hex the skin cannot reach: `.step-dot.active{background:#2563eb}` (`wizard.py:33`), `.step-dot.done{background:#10b981}` (`:34`), `.step-line.done{background:#10b981}` (`:36`), `.field-input:focus{border-color:#2563eb;box-shadow:0 0 0 2px #dbeafe}` (`:47`), `.pick-card.picked{border-color:#2563eb;background:#eff6ff}` (`:65`), `.build-progress` (`:80`). The flagship end-user flow's central progress UI stays bright blue/green while buttons around it are gold and the page is vellum — looks half-skinned. Inactive step-dots (cool gray) also clash.
- **Fix:** Retone `wizard.py`'s `<style>` hex to manuscript: step-dot.active & pick-card.picked → indigo #243B6B border / parchment-tint fill; step-dot/line.done → gold #B8860B; field-input:focus → indigo ring; build-progress gradient → gold tones; inactive dot bg → #E3D4AE.
- **file:line:** `scripts/templates/wizard.py:33-36, :47, :65, :80`

### M8 — matrix sticky headers / frozen column stay cool-gray (wrong-temperature seam)
- **Console:** matrix. **Category:** broken-layout.
- **Problem:** Sticky table headers and frozen first column are hardcoded backgrounds: `#f8fafc` (sticky thead, `matrix.py:43`), `white` (frozen first col, `:50`), `#f8fafc` (thead first-child, `:53`), `#fafafa` (cat-row first cell, `:54`) — none match the skin's utility retone. While the page goes warm, the sticky scaffolding stays cool-gray/white, reading as a mismatched gray overlay; the white frozen column seams against parchment cells. On the most data-dense console this is conspicuous.
- **Fix:** `matrix.py:43,50,53,54` — swap to warm equivalents (keep solid/opaque for sticky): thead → #F4ECD8 (vellum), frozen first col → #FBF6E9 (parchment), cat-row first cell → #F4ECD8.
- **file:line:** `scripts/templates/matrix.py:43, :50, :53, :54`

### M9 — matrix status toggle (emerald "on" / tan "off") no longer balanced
- **Console:** matrix. **Category:** consistency.
- **Problem:** `matrix_app.js:593` renders enabled=`text-emerald-700` (untouched → stays vivid green) vs disabled=`text-slate-400` (remapped to warm tan #A8916B). The on/off pair no longer reads as a balanced two-state toggle — "on" glows green, "off" is muted manuscript tan. Same untouched-emerald at `matrix_app.js:639,893,1041,1170` ("✓ saved", totals) sits as a saturated green island. (emerald not in the skin's remap — only slate + blue, `_design.py:194-203`.)
- **Fix:** Decide the status-color policy and apply as a class: (a) remap the emerald family in the skin config (`_design.py` extend.colors) so success tracks the manuscript palette, OR (b) keep emerald as the deliberate success accent but retone the "off" state in `matrix_app.js:593` to a matching muted manuscript gray so the pair stays balanced. Deliberate decision, not auto-pass.
- **file:line:** `scripts/templates/matrix_app.js:593`

### M10 — audit status count-cards lose semantic distinction
- **Console:** audit, audit_log. **Category:** consistency. **Ratio:** indigo on parchment 10.17:1 (passes); semantic distinction is the issue, not contrast.
- **Problem:** Status count cards at `audit.py:75,80,85,90` are `bg-white border-{emerald,blue,amber,red}-300 text-{…}-700`. The skin forces `.bg-white → parchment !important` (all same beige fill); emerald/amber/red stay original (untouched), but the BLUE "User-original" card (`audit.py:80-82`) is retoned by the blue scale: border-blue-300 → #8EA0C8, text-blue-700 → indigo #243B6B. Four of five cards keep their semantic color but the "User-original" card shifts to muted indigo that no longer reads as a distinct category; all cards share one parchment fill so the only status signal is a 1px border. (Text contrast passes — emerald-700 5.08, amber-700 4.65, red-700 6.0, indigo 10.17.) Same in `audit_log.py:75-86`.
- **Fix:** In `_design.py` add a small allow-list so these status borders/text aren't collapsed (tinted manuscript fill per status, or remap the blue 300/700 stops to a tone still reading as "info" distinct from red). Lowest-touch: in `audit.py:80-82` / audit_log swap the blue card to a dedicated info utility the skin maps intentionally.
- **file:line:** `scripts/templates/audit.py:80-82`

### M11 — theme-token consoles inconsistent under dark mode
- **Console:** preflight, build_tracker, greek, hebrew (theme-token family). **Category:** broken-layout.
- **Problem:** These four use `<body class="theme-bg-page theme-text">` (`greek.py:43`, `hebrew.py:49`, `preflight.py:55`, `build_tracker.py:80`) and ship the ACTIVE dark-mode toggle. The skin overrides only the LIGHT `:root` tokens (`_design.py:214-225`); never the dark block (`:358-372`). With a saved dark mode, dark theme-token sub-surfaces (slate-900/800, blue accents) layer UNDER the skin's hardcoded-light grounds (`_design.py:226,229`) → inconsistent dark panels on a forced parchment page with low-contrast seams. (matrix/wizard correctly excluded — bg-slate-50/bg-white, not theme tokens.)
- **Fix:** Same as H3 — in `_design.py` either override the dark-theme tokens OR make the html/body + .bg-white grounds defer when dark is set (wrap `:226,229` under `:root:not([data-theme=dark])`). Verify all 4 in BOTH light and dark. _(Overlaps H3 — same root; fix once.)_
- **file:line:** `scripts/templates/_design.py:226, :229 (vs :358-372)`

### M12 — first-run welcome overlay ignores the skin entirely
- **Console:** index (first-run welcome overlay) — first end-user surface. **Category:** consistency. **Ratio:** CTA #fff on #059669 = 3.77:1 (passes 3:1 large/bold; borderline at 15px/600 for normal-text 4.5).
- **Problem:** WELCOME_OVERLAY_JS builds the modal with hardcoded INLINE styles the class/token skin cannot reach: card `background:#fff` (`_design.py:2611`), heading `color:#0f172a` (`:2615`), body `color:#475569` (`:2619`), "Start building" CTA `background:#059669` emerald (`:2627`), "Explore on my own" `border:#cbd5e1` (`:2632`), `font-family:system-ui` (`:2608`). The first thing a new end-user sees is a cool-grey/emerald system-font modal that does not match the warm-serif manuscript chrome, primary CTA green while every skinned primary is gold (or, post-H7, red).
- **Fix:** Retone the inline styles to manuscript: card #FBF6E9, heading #2B2118, body #574532, primary CTA `var(--ms-red) #7A1F2B` or `var(--ms-gold)` with #FCF8EF text, secondary border rgba(154,110,18,0.6), font-family the EB Garamond/Georgia serif stack. Edit `_design.py:2608,2611,2615,2619,2627,2632`.
- **file:line:** `scripts/templates/_design.py:2608,2611,2615,2619,2627,2632` (WELCOME_OVERLAY_JS)

### M13 — primary-action color differs by console family
- **Console:** hebrew, greek vs ops/publisher/sources/apihelp/covers. **Category:** consistency. **Ratio:** gold btn 4.80:1, red theme-accent btn ~9.7:1 (both pass — issue is cross-console consistency).
- **Problem:** In the slate family (ops, publisher, sources, apihelp, covers) primary buttons are `bg-blue-600` → skin paints GOLD #B8860B (`_design.py:236`). In the theme-token family (hebrew, greek) the primary is class `theme-accent` → `--color-accent`, which the skin remaps to manuscript RED #7A1F2B (`_design.py:222`). So `hebrew.py:79` / `greek.py:73` "Look up" are red (~9.7:1) while equivalent primaries elsewhere are gold (~4.8:1) — two different primary-action colors for the same affordance, no functional reason.
- **Fix:** Pick ONE primary-action color and make both levers agree. Aligning `_design.py:222` (--color-accent) with `:236` (bg-blue-600 fill) is the single edit. **Converges with H7's red recolor: set both to --ms-red with antique text.**
- **file:line:** `scripts/templates/_design.py:236 (gold) vs :222 (--color-accent red)`; `hebrew.py:79`; `greek.py:73`

### M14 — apihelp HTTP-method badge legend loses its color coding
- **Console:** apihelp. **Category:** consistency. **Ratio:** GET ~11.4:1, POST ~6.8:1 (both pass — palette consistency, not contrast).
- **Problem:** Method badges (`apihelp.py:114-119`) are GET=bg-blue-100/text-blue-800, POST=bg-emerald-100/text-emerald-800, GET/POST=bg-purple-100/text-purple-800. The blue-scale remap recolors ONLY the GET badge (blue.100→#DCE3F0, blue.800→#182846, `_design.py:200-201`) while emerald and purple are untouched. One third of the legend shifts to muted indigo while the other two stay bright green/purple — the three-color key no longer reads as one coherent palette.
- **Fix:** Decide method-badge colors as a set: remap all three families in the skin to manuscript-toned-but-distinct hues, OR take GET off the blue scale (explicit non-Tailwind-blue class). Define in `apihelp.py:114-119` with a matching skin rule in `_design.py`.
- **file:line:** `scripts/templates/apihelp.py:114-119`

### M15 — header treatment does not match the site
- **Console:** ALL (global skin) — header parity. **Category:** consistency.
- **Problem:** Site header is LIGHT vellum with a 2px DOUBLE gold-line bottom rule and a serif wordmark (gold cross + sepia "grace") (`website/style.css:65-72`). The app keeps every console's DARK header (header.bg-slate-900/800 → charcoal #221C15, `_design.py:232`) + only a 2px SOLID gold rule (`_design.py:233`). Site=light+double-gold, app=dark+single-gold — a clearly different masthead.
- **Fix:** `_design.py:233` — make the header rule double: `border-bottom:2px double var(--ms-gold-line)`. For full parity, a follow-up could lighten console headers to vellum + mirror the gold-cross wordmark; at minimum mirror the double-rule.
- **file:line:** `scripts/templates/_design.py:232-233` (vs `website/style.css:65-72`)

### M16 — card treatment only partially matches the site card
- **Console:** ALL (global skin) — card border parity. **Category:** consistency.
- **Problem:** Site card is `border:1px solid gold-line + border-top:4px solid red + border-radius:3px + box-shadow` (`website/style.css:97-102`). The skin gives `.rounded-lg.border` only `border-top:3px solid --ms-red` (`_design.py:249`) and relies on the generic `.border` at rgba(154,110,18,0.42) (`:243-244`) for the perimeter, no box-shadow. Result: thinner top rule (3px not 4px); faint translucent perimeter (0.42 alpha) instead of solid 1px gold-line + shadow → app cards look flatter / less defined.
- **Fix:** `_design.py:243-244,249` — bump the top accent to 4px; give cards a stronger solid gold-line perimeter + a subtle box-shadow so panels read as defined boxes. _(Coordinate with M5 — gate the red top-accent first.)_
- **file:line:** `scripts/templates/_design.py:243-244,249` (vs `website/style.css:97-102`)

---

## LOW severity

### L1 — customize amber-50 callout off-tone (cosmetic)
- **Console:** customize (and `wizard.py:196` emerald-50 callout). **Category:** consistency. **Ratio:** ink on amber-50 #FFFBEB = 15.19:1 (passes).
- **Problem:** `customize.py:91` `bg-amber-50 border border-amber-200` callout keeps bright yellow utilities (neither bg-amber-* nor border-amber-* is remapped). Sits as a saturated yellow block on parchment; amber-200 is a cool-leaning yellow off-tone next to vellum/gold. Text contrast fine. Same at `wizard.py:196` (emerald-50/border-emerald-200).
- **Fix:** Optional polish — accept amber/emerald callouts as deliberate caution/info semantics (leave), OR retone in the skin (`.bg-amber-50{background:#FCF8EF!important}` + `.border-amber-200{border-color:var(--ms-gold-line)!important}`). Breaks nothing.
- **file:line:** `scripts/templates/customize.py:91`

### L2 — gold-as-text guard (PARTIALLY REFUTED — forward-looking guard, not a current defect)
- **Console:** guard only — no skin rule produces this. **Category:** contrast. **Ratio:** gold #B8860B as text on vellum #F4ECD8 = 2.76:1 (would fail AA 4.5 AND large 3:1).
- **Problem:** The η.1 skin never assigns gold as a TEXT color: gold is used only as a button BACKGROUND (`_design.py:236`, `background-color`), and text-blue-* → indigo with `.text-blue-700` forced to indigo (`_design.py:240`). So the failing 2.76:1 gold-on-vellum pair is NOT produced by the skin. It would only arise if a console hardcoded a gold text color on a light ground (none found).
- **Fix:** No skin change required. Guard: if any future rule/template sets gold as text on a light ground, use --ms-sepia #574532 (7.75:1) or --ms-ink for text; reserve gold for fills/accents.
- **file:line:** `scripts/templates/_design.py:236` (gold is background-only; no text-gold rule exists)

### L3 — generic decorative borders below UI 3:1 (decorative, not functional)
- **Console:** all skinned consoles — generic decorative borders. **Category:** wcag. **Ratio:** **1.66:1 vellum / 1.70:1 parchment** (below UI 3:1; decorative).
- **Problem:** `_design.py:243-244` sets generic borders (.border/.border-t/.border-slate-200/300) to rgba(154,110,18,0.42). Composited: ~#CEB785 at 1.66:1 over vellum, ~#D2BD8F at 1.70:1 over parchment — below WCAG 3:1 for UI-component boundaries. BUT these are decorative perimeter/zone separators, not the sole indicator of a control's boundary/state (input borders + solid gold-line carry the functional load) → minor deviation, not a functional failure. The SOLID gold-line border (no alpha) passes: 3.87:1 vellum, 4.22:1 parchment.
- **Fix:** Acceptable as decorative grouping. If meant to delineate distinct UI zones to AA, raise the alpha at `:244` (~0.70 reaches ~3:1 over vellum; full-opacity var(--ms-gold-line) = 3.87:1).
- **file:line:** `scripts/templates/_design.py:243-244`

### L4 — customize ed-save-count pill (translucent-white) missed by skin
- **Console:** customize — ed-save-count pill. **Category:** consistency. **Ratio:** pill text white ~7.4:1 (legible — issue is the faint chip bg).
- **Problem:** The skin retones `.bg-white` (opaque) but NOT `bg-white/25` (a distinct utility, `.bg-white\/25` — `.bg-white` does not match it). `customize.py:752` has a save-count pill `class="…rounded-full bg-white/25…"` on the dark charcoal header → renders as ~25% white over charcoal (faint grey smudge). (Low: small, class `hidden`, only shown when unsaved changes exist on an edition.)
- **Fix:** Add a rule for translucent-white utilities on dark headers, e.g. `.bg-white\/25{ background-color: rgba(201,178,122,0.30) !important }`, OR replace `bg-white/25` at `customize.py:752` with a solid manuscript chip. Audit for other bg-white/NN sites.
- **file:line:** `scripts/templates/customize.py:752` (uncovered by `_design.py:229`)

### L5 — sources active/hover row + search highlight cool-blue/lemon on parchment
- **Console:** sources. **Category:** consistency. **Ratio:** ~12:1 (legible — palette coherence only).
- **Problem:** `.book-row:hover{background:#f1f5f9}` (`sources.py:30`), `.book-row.active{background:#dbeafe}` (`:31`), `mark{background:#fef08a}` (`:33`) are CSS-rule hex the class-based skin never reaches → selection/hover/highlight render as cool light-blue and bright lemon islands on warm parchment (off-palette but legible). _(M1 already covers the visibility of `:30-31`; this is the broader palette note incl. `mark` at `:33`.)_
- **Fix:** Retone in `sources.py:30,31,33` to manuscript tints (active #EFE6CE, hover #F4ECD8, mark warm amber #F0E2A8). Better: a shared manuscript selection-tint var in `_design.py` other templates can migrate to.
- **file:line:** `scripts/templates/sources.py:30,31,33`

### L6 — covers cover-slot state colors un-skinned cool/blue islands
- **Console:** covers. **Category:** consistency. **Ratio:** placeholder 2.47:1 (PRE-EXISTING fail, not skin-introduced).
- **Problem:** Every cover-slot state color is CSS-rule hex the skin cannot reach: empty slot border #cbd5e1 / bg #f8fafc (`covers.py:29-30`), has-cover bg #fff (`:35`), dragover #2563eb border / #eff6ff fill (`:36`), uploading #f59e0b (`:37`). On vellum these render as cool-grey/blue rectangles; dragover feedback is plain blue. Placeholder text #94a3b8 on #f8fafc = 2.47:1 (fails AA) but that is PRE-EXISTING — the skin just leaves the cool slot bg under it.
- **Fix:** Retone slot-state hexes in `covers.py:29,30,36,37` to manuscript tones (empty border rgba(154,110,18,0.42) / bg #FBF6E9; dragover --ms-gold / #FBF6E9; keep uploading amber as status). Separately bump placeholder from #94a3b8 to ≥ #6E5840 to clear AA.
- **file:line:** `scripts/templates/covers.py:29,30,36,37`

### L7 — publisher field-input focus glow stays blue while border goes indigo
- **Console:** publisher. **Category:** consistency.
- **Problem:** `.field-input:focus` sets `border-color:#2563eb` AND `box-shadow:0 0 0 2px #dbeafe` (`publisher.py:32`). The skin's `input:focus { border-color:var(--ms-indigo) !important }` (`_design.py:247`) wins the border (now manuscript indigo) but does NOT touch box-shadow → a focused field shows an indigo border ringed by a leftover light-blue #dbeafe glow (two different blues on one element).
- **Fix:** Drop the box-shadow color to a manuscript indigo tint in `publisher.py:32` (e.g. `box-shadow:0 0 0 2px rgba(36,59,107,0.25)`), OR have the skin neutralize stray focus shadows near `_design.py:247` (`input:focus,select:focus,textarea:focus{ box-shadow:none !important }`). The template-side edit is cleaner.
- **file:line:** `scripts/templates/publisher.py:32`

### L8 — `/` note-editor hardcoded status utility colors untouched
- **Console:** index (note-editor at `/`) — status colors. **Category:** consistency.
- **Problem:** The editor's bright status utilities — bg-emerald-600 add-btn (`index.py:68`, see H6), bg-rose-600 delete (`index.py:297`), bg-amber-200 flag (`index.py:206`), preview link #2563eb (`index.py:33`) — are not remapped (skin only remaps bg-blue-600), so they sit on the warm ground unretoned. (CORRECTION to the original finding's font claim: `index.py:29` hardcodes a sans `body{ font-family: ui-sans-serif… }` but the skin's `body{ EB Garamond… }` (`_design.py:227`) is injected at `</head>`, AFTER the template's inline `<style>`, so at equal specificity the SKIN wins and the body is serif — the note-editor is NOT left sans. Font point dropped; only the status-color mismatch survives.) Low: this maintainer note-editor is slated to be separated from `/` per the north-star, so cosmetic parity here is secondary to that separation.
- **Fix:** Status colors can stay until the separate idiot-proof end-user editor lands; the real action item is separating this tool from `/` (north-star), not retoning it. If retoned, map status utilities to manuscript-toned colors in `index.py:33,68,206,297`.
- **file:line:** `scripts/templates/index.py:33,68,206,297`

### L9 — skin requests "EB Garamond" but the app serves no @font-face for it
- **Console:** ALL (global skin) — EB Garamond not served. **Category:** consistency.
- **Problem:** The skin sets EB Garamond as the body/sans/serif stack (JS fontFamily `_design.py:207-208`; body `:227`; --font-stack-body `:224`) but the app has ZERO @font-face rules (grep: 0 in `_design.py`) and NO `/fonts/` route (grep: none in `web.py`). So the app always falls back to Georgia while the SITE renders true EB Garamond (self-hosted woff2) — the two surfaces never match on typography. CSP already allows it (font-src 'self' data:, `web.py:1091,1129`); the only missing piece is a same-origin /fonts/<name>.woff2 route + @font-face in the skin.
- **Fix:** Add a sandboxed `/fonts/<name>.woff2` route in `scripts/web.py` (model on existing static routes; sandbox via `scripts.core.safe_path` over `website/fonts/`) and add @font-face for eb-garamond-latin-400/600/700 + 400-italic into MANUSCRIPT_SKIN_CSS pointing at /fonts/. No CSP edit needed. _(website/fonts/ already self-hosts the woff2 files.)_
- **file:line:** `scripts/templates/_design.py:207-208,224,227` (no @font-face; vs `website/fonts/` + style.css @font-face)

---

## WCAG AA summary — key color pairs

| Pair | Where | Ratio | AA 4.5 (normal) | AA 3.0 (large/UI) |
|---|---|---|---|---|
| ink #2B2118 on gold #B8860B | primary btn **rest** (`_design.py:236`) | 4.84:1 | PASS | PASS |
| ink #2B2118 on gold-line #9A6E12 | primary btn **hover** (`_design.py:237`) | **3.46:1** | **FAIL** (H1) | PASS |
| antique #FCF8EF on gold-line #9A6E12 | proposed hover label | 4.29:1 | **FAIL** | PASS |
| antique #FCF8EF on red #7A1F2B | proposed primary (H7) | ~9.7:1 | PASS | PASS |
| antique #FCF8EF on red-dark #5E1722 | proposed hover (H7) | ~11:1 | PASS | PASS |
| white on emerald-600 #059669 | wizard/index emerald CTA | **3.77:1** | **FAIL** (H5/H6) | PASS |
| slate-100 #F1F5F9 on input #FFFDF7 | dark-mode typed text (H2) | **1.08:1** | **FAIL** | **FAIL** |
| slate-400 #A8916B on parchment #FBF6E9 | hint text (H4) | **2.81:1** | **FAIL** | **FAIL** |
| slate-400 #A8916B on vellum #F4ECD8 | hint text (H4) | **2.58:1** | **FAIL** | **FAIL** |
| input border (gold-line @0.60α) on #FFFDF7 | resting input (M4) | **2.28:1** | n/a | **FAIL** (UI 3:1) |
| count-disabled amber #fbbf24 on parchment | matrix (M2) | **1.55:1** | **FAIL** | **FAIL** |
| count-zero #cbd5e0 on parchment | matrix (M2) | **1.38:1** | **FAIL** | **FAIL** |
| verse-num #94a3b8 on parchment | compare (M3) | **2.38:1** | **FAIL** | **FAIL** |
| missing #cbd5e1 on parchment | compare (M3) | **1.38:1** | **FAIL** | **FAIL** |
| active-row #dbeafe vs vellum #F4ECD8 | build_my_bible/sources (M1) | **1.04:1** | invisible | invisible |
| heat-0 #f8fafc vs heat-1 #ecfdf5 | build_tracker (M6) | **1.007:1** | indistinct | indistinct |
| sepia #574532 on parchment #FBF6E9 | (recommended muted-text tone) | ~6.2:1 | PASS | PASS |
| solid gold-line #9A6E12 on parchment | input border, no alpha (M4 fix) | 4.48:1 | n/a | PASS |
| indigo #243B6B on parchment | audit info card / links | 10.17:1 | PASS | PASS |
| decorative border (gold-line @0.42α) on vellum | generic .border (L3) | 1.66:1 | n/a | FAIL (decorative) |
| ink on amber-50 #FFFBEB | customize callout (L1) | 15.19:1 | PASS | PASS |
| gold #B8860B as text on vellum | guard only — not produced (L2) | 2.76:1 | FAIL | FAIL |

---

## Prioritized fix list for WIN

**Do these before tagging v0.1.0 (HIGH — AA / illegibility / brand):**

1. **H7 + H1 — recolor the primary action to RED.** `_design.py:236-237`: `.bg-blue-600 → background:var(--ms-red) #7A1F2B; color:var(--ms-antique) #FCF8EF`; `.bg-blue-700`/hover → `var(--ms-red-dark) #5E1722`. One change fixes the AA hover failure (H1), matches the site CTA, and stops gold-as-small-text. Update the `:238` child override to antique. Reserve gold for hairlines/borders/top-accents.
2. **H2 — fix dark-mode input typed text.** `_design.py:246`: change `#FFFDF7 !important` → `background-color: var(--color-bg-surface, #FFFDF7) !important` (and/or add the dark-token override below). Also drops the resting-border alpha for M4 in the same edit.
3. **H3 + H11 (M11) — make the skin theme-complete.** Add a `:root[data-theme="dark"]{ … }` dark-manuscript override in MANUSCRIPT_SKIN_CSS, AND scope `_design.py:226,229` behind `:root:not([data-theme=dark])`. Verify greek/hebrew/preflight/build_tracker in BOTH light and dark.
4. **H4 — darken hint text.** `_design.py:196`: slate-400 #A8916B → #6E5840 (≈slate-500). Clears AA for ~176 hint-text sites.
5. **H5 + H6 — emerald CTAs onto the primary utility.** `wizard.py:328,347` and `index.py:68`: `bg-emerald-600 hover:bg-emerald-700` → `bg-blue-600 hover:bg-blue-700` (inherits the red primary from fix 1). Restores hierarchy + AA.

**Then (MEDIUM — readability + site parity; should also land for v0.1.0):**

6. **M2/M3/M1/M6 — retone invisible/near-invisible CSS-rule hex data states:** matrix counts (`matrix.py:33-34`), compare verse-num/missing (`compare.py:28-29`), book-row active/hover (`build_my_bible.py:43-44`, `sources.py:30-31`), build_tracker heat ramp (`build_tracker.py:37-44`).
7. **M4 — input resting border** (folded into fix 2 if done together): drop the 0.60 alpha to solid gold-line → 4.48:1.
8. **M5 — scope the blood-red card stripe** behind an opt-in `.ms-card-accent` class (`_design.py:249`); stop striping neutral stat tiles.
9. **M8/M7 — warm the matrix sticky scaffolding** (`matrix.py:43,50,53,54`) and **retone the wizard stepper/pick UI** (`wizard.py:33-36,47,65,80`).
10. **M13/M9/M10/M14 — settle the status-color & primary-color policy** (one primary color across console families `_design.py:222 vs :236`; emerald success vs off-state balance `matrix_app.js:593`; audit info-card distinction `audit.py:80-82`; method-badge set `apihelp.py:114-119`).
11. **M12 — retone the first-run welcome overlay inline styles** (`_design.py:2608-2632`) — first end-user surface.
12. **M15/M16 — header double-rule + card perimeter/shadow** for site parity (`_design.py:232-233,243-244,249`).

**Optional polish (LOW — non-blocking):**

13. **L9 — serve EB Garamond** (`/fonts/` route in `scripts/web.py` + @font-face in the skin) so app typography matches the site.
14. L1 (amber/emerald callouts), L4 (bg-white/25 pill), L5 (sources mark/highlight), L6 (covers slot states + pre-existing placeholder fail), L7 (publisher focus glow), L8 (`/` note-editor status colors — defer to the separate end-user editor per north-star). L2 is a refuted guard — no change, just don't use gold-as-text in future.

**Note for WIN:** every fix above lands in WIN's domain (`scripts/templates/*` + `scripts/web.py`). The two highest-leverage single edits are fix 1 (red primary — closes H1+H7+helps H5/H6/M13) and fix 3 (dark-token override — closes H3+M11). After edits, re-verify in a running console (`scripts/launcher.py`) in BOTH light and dark, on at least wizard (flagship), matrix (densest), compare (public), and greek/hebrew (dark-mode + theme tokens).
