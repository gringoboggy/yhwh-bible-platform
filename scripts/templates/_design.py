"""
_design.py — shared design-system tokens for the 13 consoles.

Phase ψ.13 (2026-05-08). The console templates were Tailwind'd
ad-hoc as each landed; the result is 13 nearly-identical-but-not
header chromes, 13 hand-rolled "save status" banners, and a dozen
flavors of card / button styling. This module is the canonical
source of truth — Python-side constants and small builder functions
that templates import and embed via Python f-strings.

Intent (per the prettification scope addendum):
  - Templates remain plain HTML files with Tailwind utility classes.
    No build step, no JSX, no CSS-in-JS magic.
  - This module is the documentation + the tokens. Templates use
    f-string interpolation: `<header>{HEADER_NAV(current="matrix")}</header>`.

Public surface:
    Class-name tokens (CSS-side):
      BTN_PRIMARY, BTN_SECONDARY, BTN_GHOST, BTN_DANGER, BTN_SMALL
      BADGE_REQUIRED, BADGE_OPTIONAL, BADGE_NEUTRAL
      CARD_SECTION, CARD_SECTION_PADDED
      INPUT_TEXT, INPUT_SELECT
      STATUS_INFO, STATUS_SUCCESS, STATUS_WARN, STATUS_ERROR

    Markup builders:
      HEADER_NAV(current=…)     -> str   the cross-link header bar
      STATUS_BANNER(kind, msg)  -> str   ready-made status banner div
      EMPTY_STATE(label)        -> str   "nothing yet" placeholder
      LOADING_STATE(label)      -> str   "loading…" placeholder

    Constants:
      CONSOLES                  list of (route, label) — single source
                                of truth for the cross-link nav.

The original full-source tokens stay aliased so a partial migration
doesn't break anything: a template can import what it needs and keep
its existing markup for the rest. ψ.13.5 will sweep the 13 consoles
to use this module pervasively (deliberately deferred — that's a
13-file refactor with real regression risk; doing it as a separate
focused phase keeps the diff inspectable).
"""

from __future__ import annotations


# ----------------------------------------------------------------------
# CSS class-name tokens (Tailwind utilities — copy/paste into HTML)
# ----------------------------------------------------------------------

# Buttons. Keep visual hierarchy: primary > secondary > ghost. Danger
# is its own axis (used for delete/clear actions, regardless of
# emphasis).
BTN_PRIMARY = "px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
BTN_SECONDARY = "px-3 py-1.5 rounded border border-slate-300 hover:bg-slate-50 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
BTN_GHOST = "px-3 py-1.5 rounded text-slate-700 hover:text-blue-700 hover:underline text-sm"
BTN_DANGER = (
    "px-3 py-1.5 rounded border border-slate-300 text-red-700 hover:bg-red-50 text-sm font-medium disabled:opacity-50"
)
BTN_SMALL = "px-2 py-1 rounded border border-slate-300 hover:bg-slate-50 text-xs"

# Badges (small inline pills used for required/optional/status).
BADGE_REQUIRED = "text-xs px-1.5 py-0.5 rounded bg-slate-100 text-slate-600"
BADGE_OPTIONAL = "text-xs px-1.5 py-0.5 rounded bg-amber-50 text-amber-700"
BADGE_NEUTRAL = "text-xs px-1.5 py-0.5 rounded bg-slate-100 text-slate-700"

# Cards / sections.
CARD_SECTION = "bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden"
CARD_SECTION_PADDED = "bg-white rounded-lg shadow-sm border border-slate-200 p-4"

# Form fields.
INPUT_TEXT = "border border-slate-300 rounded px-2 py-1 text-sm"
INPUT_SELECT = "border border-slate-300 rounded px-2 py-1 text-sm"

# Status banners — colored backgrounds for inline messages. Pair
# each with one of: info, success, warn, error.
STATUS_INFO = "px-3 py-2 rounded border border-blue-200 bg-blue-50 text-blue-900 text-sm"
STATUS_SUCCESS = "px-3 py-2 rounded border border-emerald-200 bg-emerald-50 text-emerald-900 text-sm"
STATUS_WARN = "px-3 py-2 rounded border border-amber-300 bg-amber-50 text-amber-900 text-sm"
STATUS_ERROR = "px-3 py-2 rounded border border-red-300 bg-red-50 text-red-900 text-sm"


# ----------------------------------------------------------------------
# ψ.14 buyer-arc polish — CSS layer that overlays Tailwind utilities.
# Substituted into the buyer-arc consoles (/wizard, /export, /compare)
# at module load via `.replace("<!-- BUYER_ARC_POLISH_CSS -->", ...)`.
# Keeps the polish source-of-truth here so a future tweak doesn't
# require finding three near-identical inline blocks.
#
# What this gives the consoles:
#   - Visible focus rings on :focus-visible (keyboard navigation)
#   - 150ms transitions on color/opacity/shadow for hover smoothness
#   - .psi14-pending pill — small "● unsaved" badge for dirty-state
#   - .psi14-step-fade-in animation for wizard step transitions
#
# Color values are inlined (rgb()) rather than Tailwind utilities
# because pseudo-element ::after content can't be styled by Tailwind.
# ----------------------------------------------------------------------

BUYER_ARC_POLISH_CSS = """<style>
  /* ψ.14: smoother transitions on interactive elements */
  button, a, input, select, textarea {
    transition: background-color 150ms ease,
                color 150ms ease,
                border-color 150ms ease,
                opacity 150ms ease,
                box-shadow 150ms ease;
  }
  /* ψ.14: visible keyboard-focus rings (buyers may demo via tab).
     ζ.1 — focus-ring color is now themable via --color-focus-ring;
     the rgb() fallback preserves the pre-ζ.1 visual in environments
     where the var isn't set (consoles that haven't yet absorbed the
     THEME_TOKENS_CSS block). */
  *:focus-visible {
    outline: 2px solid var(--color-focus-ring, rgb(37 99 235));
    outline-offset: 2px;
    border-radius: 0.25rem;
  }
  button:focus-visible,
  a:focus-visible,
  input:focus-visible,
  select:focus-visible,
  textarea:focus-visible {
    outline: 2px solid var(--color-focus-ring, rgb(37 99 235));
    outline-offset: 2px;
  }
  /* ψ.14: tactile click feedback for buttons (subtle scale-down) */
  button:active:not(:disabled) {
    transform: scale(0.98);
    transition-duration: 75ms;
  }
  /* ψ.14: dirty-state pill — append to a Save/Build button's parent */
  .psi14-pending::after {
    content: "● unsaved";
    margin-left: 0.5rem;
    padding: 0.125rem 0.5rem;
    font-size: 0.625rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    background: rgb(254 243 199); /* amber-100 */
    color: rgb(146 64 14); /* amber-800 */
    border: 1px solid rgb(252 211 77); /* amber-300 */
    border-radius: 9999px;
    vertical-align: middle;
    display: inline-block;
  }
  /* ψ.14: subtle fade-in for wizard step transitions */
  .psi14-step-fade-in {
    animation: psi14StepFadeIn 200ms ease-out;
  }
  @keyframes psi14StepFadeIn {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
  }
</style>"""


# ----------------------------------------------------------------------
# η.1 — Manuscript skin (2026-06-09). Re-tones the whole console app to
# match the public website (www.yhwhyaway.com): vellum/parchment grounds,
# ink/sepia text, gold hairlines, a red primary action, indigo links, and
# a serif body. Injected app-wide at the single HTML choke point
# (web.py `_send_html`) BEFORE script-nonce injection, so every console
# (wizard, customize, note-editor, …) picks it up with no per-file edits.
#
# Two levers:
#   1. A Tailwind CDN config remap of the `slate` + `blue` color SCALES,
#      so the consoles' existing bg-slate-*/text-slate-*/text-blue-* markup
#      re-tones at the source (no utility enumeration, no per-shade CSS).
#      Config-after-CDN is the documented play-CDN pattern.
#   2. A <style> layer for the signature website accents the scale-remap
#      can't express: parchment cards (bg-white), a RED primary action
#      (bg-blue-600 is the buttons' utility), a charcoal header with a gold
#      rule, the ζ.1 theme-token remap (so .theme-* surfaces match too), and
#      a serif body. `!important` only where it must beat a Tailwind utility.
#
# Font: the app self-hosts EB Garamond (+ Noto Serif Ethiopic for Ge'ez) via the
# same-origin /fonts/ route + the @font-face rules below, matching the website
# exactly (no Georgia fallback). website/fonts is bundled in dev/launcher.spec so
# it resolves in the frozen app too. See docs/superpowers/specs/
# 2026-06-09-app-eb-garamond-selfhosting.md. Reader/EPUB surfaces are NOT affected
# (this is console chrome only; the EPUB build path is separate).
# ----------------------------------------------------------------------

# The manuscript palette as data — the single source of truth for surfaces that
# can't (or shouldn't) inherit the Tailwind-remap skin. HOME_HTML is CDN-free by
# design (docs/superpowers/specs/2026-06-09-idiot-proof-app-design.md §1) and
# builds its <style> from THIS dict, so HOME and the skin can never drift.
# Every pair below is AA-verified per-element in
# docs/superpowers/notes/2026-06-09-home-html-aa-colors.md. Rules baked in:
# gold is a button FILL or hairline, NEVER a text color (2.76:1 on vellum);
# gold hover goes LIGHTER (#C49A2E, 6.01:1), never darker; links/secondary/
# focus = indigo (user decision).
MS_PALETTE: dict[str, str] = {
    "vellum": "#F4ECD8",  # page / hero ground
    "parchment": "#FBF6E9",  # card / panel ground
    "ink": "#2B2118",  # body text + on-gold button text (4.84:1 on gold)
    "sepia": "#574532",  # secondary / subtitle text (7.75:1 on vellum)
    "muted": "#6E5840",  # hint / fine-print text (5.69:1 on vellum)
    "gold": "#B8860B",  # primary button fill (rest)
    "gold_hover": "#C49A2E",  # primary button fill (hover) — lighter, not darker
    "gold_line": "#9A6E12",  # hairlines / borders / top-accent rules ONLY
    "indigo": "#243B6B",  # links, secondary actions, focus ring, accents
    "antique": "#FCF8EF",  # text on red (alt CTA)
    "red": "#7A1F2B",  # destructive + the alt site-parity primary
    "red_dark": "#5E1722",  # red hover
}

MANUSCRIPT_SKIN_CSS = """<!-- manuscript-skin (η.1) -->
<script>
  /* η.1: re-tone the Tailwind palette to the website's manuscript tones.
     The play CDN reads tailwind.config after its own script loads, then
     regenerates utilities — so existing slate/blue markup re-tones. */
  if (window.tailwind) {
    window.tailwind.config = window.tailwind.config || {};
    window.tailwind.config.theme = window.tailwind.config.theme || {};
    window.tailwind.config.theme.extend = window.tailwind.config.theme.extend || {};
    window.tailwind.config.theme.extend.colors = Object.assign(
      {}, window.tailwind.config.theme.extend.colors, {
        slate: {
          50:'#F4ECD8', 100:'#EFE6CE', 200:'#E3D4AE', 300:'#D2BE90',
          400:'#6E5840', 500:'#6E5840', 600:'#574532', 700:'#473726',
          800:'#322619', 900:'#2B2118',
        },
        blue: {
          50:'#EEF1F7', 100:'#DCE3F0', 200:'#BCC8E2', 300:'#8EA0C8',
          400:'#5871A0', 500:'#34528A', 600:'#243B6B', 700:'#1D3158',
          800:'#182846', 900:'#121E36',
        },
      });
    window.tailwind.config.theme.extend.fontFamily = Object.assign(
      {}, window.tailwind.config.theme.extend.fontFamily, {
        sans: ['"EB Garamond"','"Noto Serif Ethiopic"','Georgia','"Times New Roman"','serif'],
        serif: ['"EB Garamond"','"Noto Serif Ethiopic"','Georgia','"Times New Roman"','serif'],
      });
  }
</script>
<style>
  /* η.1: manuscript skin — match www.yhwhyaway.com. */
  /* L9 — self-host EB Garamond (the site's body face) from the same-origin /fonts/
     route so the app renders true EB Garamond instead of falling back to Georgia.
     Mirrors website/style.css; CSP already allows font-src 'self'. */
  @font-face { font-family: "EB Garamond"; font-style: normal; font-weight: 400; font-display: swap; src: url("/fonts/eb-garamond-latin-400-normal.woff2") format("woff2"); }
  @font-face { font-family: "EB Garamond"; font-style: italic; font-weight: 400; font-display: swap; src: url("/fonts/eb-garamond-latin-400-italic.woff2") format("woff2"); }
  @font-face { font-family: "EB Garamond"; font-style: normal; font-weight: 600; font-display: swap; src: url("/fonts/eb-garamond-latin-600-normal.woff2") format("woff2"); }
  @font-face { font-family: "EB Garamond"; font-style: normal; font-weight: 700; font-display: swap; src: url("/fonts/eb-garamond-latin-700-normal.woff2") format("woff2"); }
  /* Ge'ez/Amharic coverage — EB Garamond has no Ethiopic glyphs. unicode-range scoped
     so it only loads when Ethiopic codepoints are present (zero cost on Latin pages). */
  @font-face { font-family: "Noto Serif Ethiopic"; font-style: normal; font-weight: 400; font-display: swap; src: url("/fonts/noto-serif-ethiopic-ethiopic-400-normal.woff2") format("woff2"); unicode-range: U+1200-137F, U+1380-139F, U+2D80-2DDF, U+AB00-AB2F; }
  :root {
    --ms-vellum:#F4ECD8; --ms-parchment:#FBF6E9; --ms-ink:#2B2118; --ms-sepia:#574532;
    --ms-gold:#B8860B; --ms-gold-line:#9A6E12; --ms-gold-hover:#C49A2E; --ms-red:#7A1F2B; --ms-red-dark:#5E1722;
    --ms-indigo:#243B6B; --ms-antique:#FCF8EF; --ms-charcoal:#221C15; --ms-field-bg:#FFFDF7;
    /* remap the ζ.1 theme tokens so .theme-* surfaces match too */
    --color-bg-page:#F4ECD8; --color-bg-surface:#FBF6E9;
    --color-text-primary:#2B2118; --color-text-muted:#574532;
    --color-text-on-accent:#FCF8EF;
    --color-accent:#7A1F2B; --color-accent-hover:#5E1722;
    --color-border:#9A6E12; --color-focus-ring:#243B6B;
    --font-stack-body:"EB Garamond", "Noto Serif Ethiopic", Georgia, "Times New Roman", serif;
  }
  body { font-family: "EB Garamond", "Noto Serif Ethiopic", Georgia, "Times New Roman", serif; }
  /* LIGHT manuscript grounds — scoped so a dark-mode user (greek/hebrew/preflight/
     build_tracker auto-activate dark from OS pref) doesn't get parchment forced
     under dark panels (H3). */
  :root:not([data-theme=dark]) { background-color: var(--ms-vellum); }
  :root:not([data-theme=dark]) body { background-color: var(--ms-vellum); color: var(--ms-ink); }
  :root:not([data-theme=dark]) .bg-white { background-color: var(--ms-parchment) !important; }
  /* DARK manuscript override (H2/H3): dark page/surfaces + light parchment text +
     gold accents, so the skin is theme-complete in dark mode (and typed input text
     reads — H2 was 1.08:1). */
  :root[data-theme="dark"] {
    --color-bg-page:#1B160F; --color-bg-surface:#2B2118;
    --color-text-primary:#F4ECD8; --color-text-muted:#C9B27A;
    --color-border:#9A6E12; --ms-field-bg:#2B2118; background-color: var(--ms-charcoal);
  }
  :root[data-theme="dark"] body { background-color: var(--ms-charcoal); color: #F4ECD8; }
  :root[data-theme="dark"] .bg-white { background-color: #2B2118 !important; }
  .bg-slate-50 { background-color: var(--ms-vellum) !important; }
  /* dark console header -> charcoal with a gold rule (the site's header signature) */
  .bg-slate-900, .bg-slate-800 { background-color: var(--ms-charcoal) !important; }
  header.bg-slate-900, header.bg-slate-800 { border-bottom: 2px double var(--ms-gold-line); }
  /* PRIMARY action = GOLD on dark ink text (buttons use bg-blue-600/700) —
     the illuminated-manuscript look: gold pressed onto dark brown. The hover goes
     LIGHTER (#C49A2E, 6.01:1) — a darker hover dropped dark ink below AA (H1: the
     old #9A6E12 hover = 3.46:1). */
  .bg-blue-600 { background-color: var(--ms-gold) !important; color: var(--ms-ink) !important; }
  .bg-blue-700, .hover\\:bg-blue-700:hover { background-color: var(--ms-gold-hover) !important; color: var(--ms-ink) !important; }
  .bg-blue-600 *, .bg-blue-700 * { color: var(--ms-ink) !important; }
  /* links / accents stay indigo (text-blue-* re-toned by the config scale) */
  .text-blue-700 { color: var(--ms-indigo) !important; }
  /* defined borders — distinguish boxes + panels/areas from the beige ground
     (user: a border around the whole perimeter so zones read as distinct). */
  .border, .border-t, .border-b, .border-l, .border-r,
  .border-slate-200, .border-slate-300 { border-color: rgba(154,110,18,0.42) !important; }
  /* input boxes: a SOLID gold-line border (M4: the 0.60-alpha border was 2.28:1,
     below UI 3:1) + a theme-aware fill (H2: near-white in light, dark surface in
     dark mode so typed text reads). */
  input, select, textarea { border: 1px solid var(--ms-gold-line) !important; background-color: var(--ms-field-bg) !important; }
  input:focus, select:focus, textarea:focus { border-color: var(--ms-indigo) !important; outline: none; }
  /* M5/M16 — cards read as DEFINED boxes matching the site card (solid gold-line
     perimeter + radius + a soft shadow), but the blood-red top-stripe is NO LONGER
     blanket-applied to every .rounded-lg.border (it striped neutral stat tiles as if
     they were alert cards). The site's red 4px top-accent is now OPT-IN via
     .ms-card-accent, for deliberate hero/section cards only. */
  .rounded-lg.border { border: 1px solid var(--ms-gold-line) !important; box-shadow: 0 1px 3px rgba(43,33,24,0.10); }
  .ms-card-accent { border-top: 4px solid var(--ms-red) !important; }
  /* L4 — translucent-white chips on the dark header (bg-white/25, e.g. the customize
     unsaved-changes pill) -> a warm gold tint so they don't read as a grey smudge. */
  .bg-white\\/25 { background-color: rgba(201,178,122,0.30) !important; }
  /* focus ring -> indigo */
  *:focus-visible { outline-color: var(--ms-indigo) !important; }
</style>"""


def apply_manuscript_skin(html: str) -> str:
    """Inject the η.1 manuscript skin into a Tailwind console page so it matches
    the public website. No-op (returns input) if the skin is already present or the
    page isn't a Tailwind CDN console. Idempotent; injects just before </head> so the
    config script runs after the CDN script. Called from web.py `_send_html` before
    script-nonce injection so the inline <script> picks up the CSP nonce."""
    if "manuscript-skin" in html or "cdn.tailwindcss.com" not in html or "</head>" not in html:
        return html
    return html.replace("</head>", MANUSCRIPT_SKIN_CSS + "\n</head>", 1)


# ----------------------------------------------------------------------
# ζ.1 — CSS custom-property theming foundation.
# Substituted into consoles that opt in via the `<!-- THEME_TOKENS_CSS -->`
# marker. Provides the design-token surface that ζ.2 dark mode, ζ.4
# typography, ζ.5 iconography, etc. consume.
#
# Two-layer design:
#   1. `:root { ...light... }` — default values used by every browser
#      without a `data-theme` attribute. These match today's hardcoded
#      Tailwind palette so light-theme visuals are pixel-equivalent
#      before and after ζ.1.
#   2. `:root[data-theme="dark"] { ...dark... }` — defined but
#      INACTIVE until ζ.2 lands a toggle script. Lets dark-theme
#      designers iterate ahead of the ζ.2 ship without needing the
#      toggle wired in first.
#
# `.theme-*` utility classes consume the vars. New themable elements
# use these classes instead of (or alongside) raw Tailwind colors:
#
#   <div class="theme-bg-surface theme-text">...</div>
#
# Existing `bg-white text-slate-900` markup stays light-only — ζ.2's
# job is to gradually migrate dark-mode-sensitive surfaces to the
# `.theme-*` classes. ζ.1 doesn't force that migration; it just
# provides the hooks.
#
# Token naming convention (mirrors design-system practice — surface
# vs. on-surface, semantic status colors, sizing tokens for radii
# left as fallbacks since Tailwind's `rounded-*` covers them):
#   --color-bg-page         page background (body)
#   --color-bg-surface      card / panel background
#   --color-text-primary    default body text
#   --color-text-muted      secondary / placeholder text
#   --color-text-on-accent  text rendered ON the accent color
#   --color-accent          primary brand color (links, primary btn)
#   --color-accent-hover    accent hover state
#   --color-border          default 1px borders
#   --color-focus-ring      keyboard-focus outline (already wired
#                           into BUYER_ARC_POLISH_CSS via var())
#   --color-status-success
#   --color-status-warn
#   --color-status-error
#   --color-status-info
# ----------------------------------------------------------------------

THEME_TOKENS_CSS = """<style>
  /* ζ.1: light theme — default values match the pre-ζ.1 Tailwind
     palette so visual equivalence holds in environments without a
     data-theme attribute. */
  :root {
    --color-bg-page:        rgb(248 250 252);  /* slate-50 */
    --color-bg-surface:     rgb(255 255 255);  /* white */
    --color-text-primary:   rgb(15 23 42);     /* slate-900 */
    --color-text-muted:     rgb(100 116 139);  /* slate-500 */
    --color-text-on-accent: rgb(255 255 255);
    --color-accent:         rgb(37 99 235);    /* blue-600 */
    --color-accent-hover:   rgb(29 78 216);    /* blue-700 */
    --color-border:         rgb(226 232 240);  /* slate-200 */
    --color-focus-ring:     rgb(37 99 235);    /* blue-600 */
    --color-status-success: rgb(16 185 129);   /* emerald-500 */
    --color-status-warn:    rgb(245 158 11);   /* amber-500 */
    --color-status-error:   rgb(220 38 38);    /* red-600 */
    --color-status-info:    rgb(59 130 246);   /* blue-500 */
    /* ζ.4: typography tokens (theme-independent — font choice
       doesn't change between light/dark; line-height + scale stay
       constant). Future ζ.* can swap font-stack-body for a hosted
       font like Inter without touching anything else. The system
       stack here matches Tailwind's font-sans/font-mono defaults
       — zero load cost, no FOIT, looks native on every OS. */
    --font-stack-body:      ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
    --font-stack-mono:      ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    --font-size-xs:         0.75rem;    /* 12px */
    --font-size-sm:         0.875rem;   /* 14px */
    --font-size-base:       1rem;       /* 16px */
    --font-size-lg:         1.125rem;   /* 18px */
    --font-size-xl:         1.25rem;    /* 20px */
    --font-size-2xl:        1.5rem;     /* 24px */
    --leading-tight:        1.25;
    --leading-normal:       1.5;
    --leading-relaxed:      1.625;
    --font-weight-normal:   400;
    --font-weight-medium:   500;
    --font-weight-semibold: 600;
    --font-weight-bold:     700;
  }
  /* ζ.1: dark theme — defined but INACTIVE; ζ.2 wires the toggle.
     Designers can preview by setting `data-theme="dark"` on `<html>`
     manually in devtools today.

     Slate/zinc-leaning palette for surfaces; brighter accents to
     compensate for reduced contrast on dark backgrounds. Mirrors
     Tailwind's commonly-used dark-mode defaults. */
  :root[data-theme="dark"] {
    --color-bg-page:        rgb(15 23 42);     /* slate-900 */
    --color-bg-surface:     rgb(30 41 59);     /* slate-800 */
    --color-text-primary:   rgb(241 245 249);  /* slate-100 */
    --color-text-muted:     rgb(148 163 184);  /* slate-400 */
    --color-text-on-accent: rgb(255 255 255);
    --color-accent:         rgb(59 130 246);   /* blue-500 — brighter */
    --color-accent-hover:   rgb(96 165 250);   /* blue-400 */
    --color-border:         rgb(51 65 85);     /* slate-700 */
    --color-focus-ring:     rgb(96 165 250);   /* blue-400 */
    --color-status-success: rgb(52 211 153);   /* emerald-400 */
    --color-status-warn:    rgb(251 191 36);   /* amber-400 */
    --color-status-error:   rgb(248 113 113);  /* red-400 */
    --color-status-info:    rgb(96 165 250);   /* blue-400 */
  }
  /* ζ.1: utility classes that consume the tokens. Templates opt in
     by replacing `bg-white` with `theme-bg-surface`, etc. */
  .theme-bg-page       { background-color: var(--color-bg-page); }
  .theme-bg-surface    { background-color: var(--color-bg-surface); }
  .theme-text          { color: var(--color-text-primary); }
  .theme-text-muted    { color: var(--color-text-muted); }
  .theme-border        { border-color: var(--color-border); }
  .theme-accent        {
    background-color: var(--color-accent);
    color: var(--color-text-on-accent);
  }
  .theme-accent:hover  { background-color: var(--color-accent-hover); }
  .theme-accent-text   { color: var(--color-accent); }
  .theme-status-success { color: var(--color-status-success); }
  .theme-status-warn    { color: var(--color-status-warn); }
  .theme-status-error   { color: var(--color-status-error); }
  .theme-status-info    { color: var(--color-status-info); }
  /* ζ.4: typography — body inherits the themable font stack the
     moment THEME_TOKENS_CSS is absorbed. The Tailwind CDN's reset
     sets `font-family` on `*`, which is too aggressive to override
     via a token — so we set it on `body` only and let inheritance
     handle the rest. Code/pre opt-in via .theme-font-mono. */
  body {
    font-family: var(--font-stack-body);
    font-size: var(--font-size-base);
    line-height: var(--leading-normal);
  }
  .theme-text-xs   { font-size: var(--font-size-xs);   line-height: var(--leading-normal); }
  .theme-text-sm   { font-size: var(--font-size-sm);   line-height: var(--leading-normal); }
  .theme-text-base { font-size: var(--font-size-base); line-height: var(--leading-normal); }
  .theme-text-lg   { font-size: var(--font-size-lg);   line-height: var(--leading-tight); }
  .theme-text-xl   { font-size: var(--font-size-xl);   line-height: var(--leading-tight); }
  .theme-text-2xl  { font-size: var(--font-size-2xl);  line-height: var(--leading-tight); }
  .theme-font-mono { font-family: var(--font-stack-mono); }
  .theme-weight-normal   { font-weight: var(--font-weight-normal); }
  .theme-weight-medium   { font-weight: var(--font-weight-medium); }
  .theme-weight-semibold { font-weight: var(--font-weight-semibold); }
  .theme-weight-bold     { font-weight: var(--font-weight-bold); }
  /* ζ.5: icon utility. Apply directly to <svg> (or to a wrapping
     <span>) — sizes to 1em of the surrounding text, inherits
     stroke/fill from currentColor so the icon picks up the
     theme-text or theme-status-* color of its parent.
       vertical-align: -0.125em pushes the icon down ~1.5px so it
       sits on the baseline rather than the cap-height of the
       surrounding text. */
  .theme-icon {
    display: inline-block;
    width: 1em;
    height: 1em;
    vertical-align: -0.125em;
    flex-shrink: 0;
    stroke: currentColor;
    fill: none;
  }
  /* ζ.6: toast notifications — fixed-position stack of dismissable
     status banners. Container sits below the dark-mode toggle
     (top: 4rem so it doesn't overlap). Click-through on the
     container itself (pointer-events: none); each toast re-enables
     pointer-events so its dismiss button works. */
  .theme-toast-container {
    position: fixed;
    top: 4rem;
    right: 0.75rem;
    z-index: 9998;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    pointer-events: none;
    max-width: calc(100% - 1.5rem);
  }
  .theme-toast {
    pointer-events: auto;
    min-width: 18rem;
    max-width: 24rem;
    padding: 0.625rem 0.875rem;
    border-radius: 0.5rem;
    border: 1px solid var(--color-border);
    background: var(--color-bg-surface);
    color: var(--color-text-primary);
    display: flex;
    align-items: flex-start;
    gap: 0.625rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
    font-size: var(--font-size-sm);
    line-height: var(--leading-normal);
    animation: theme-toast-in 200ms ease-out;
  }
  /* Per-kind border + icon color. Body text stays --color-text-primary
     so the message is always readable; only the chrome signals kind. */
  .theme-toast-info    { border-color: var(--color-status-info); }
  .theme-toast-success { border-color: var(--color-status-success); }
  .theme-toast-warn    { border-color: var(--color-status-warn); }
  .theme-toast-error   { border-color: var(--color-status-error); }
  .theme-toast-info    .theme-icon { color: var(--color-status-info); }
  .theme-toast-success .theme-icon { color: var(--color-status-success); }
  .theme-toast-warn    .theme-icon { color: var(--color-status-warn); }
  .theme-toast-error   .theme-icon { color: var(--color-status-error); }
  .theme-toast-message { flex: 1; word-wrap: break-word; }
  .theme-toast-dismiss {
    flex-shrink: 0;
    background: none;
    border: none;
    color: var(--color-text-muted);
    cursor: pointer;
    padding: 0;
    width: 1.25em;
    height: 1.25em;
    font-size: 1.125em;
    line-height: 1;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 0.25rem;
  }
  .theme-toast-dismiss:hover { color: var(--color-text-primary); }
  .theme-toast-leaving { animation: theme-toast-out 200ms ease-in forwards; }
  @keyframes theme-toast-in {
    from { opacity: 0; transform: translateX(8px); }
    to   { opacity: 1; transform: translateX(0); }
  }
  @keyframes theme-toast-out {
    from { opacity: 1; transform: translateX(0); }
    to   { opacity: 0; transform: translateX(8px); }
  }
  /* ζ.7: skeleton loaders — shimmer-animated placeholder blocks
     for content that's still loading. Base color is the surface
     tone; the shimmer band is the border tone (slightly contrasted
     in both themes). The gradient slides horizontally to create
     the shimmer effect.
       prefers-reduced-motion: reduce — disables the animation
       entirely so vestibular-disorder users get a static block
       instead of a moving one (WCAG 2.3.3). */
  .theme-skeleton {
    display: inline-block;
    background: linear-gradient(
      90deg,
      var(--color-bg-surface) 0%,
      var(--color-border) 50%,
      var(--color-bg-surface) 100%
    );
    background-size: 200% 100%;
    border: 1px solid var(--color-border);
    border-radius: 0.25rem;
    animation: theme-skeleton-shimmer 1.6s ease-in-out infinite;
  }
  .theme-skeleton-text  { display: block; width: 100%; height: 1em; }
  .theme-skeleton-block { display: block; width: 100%; height: 4rem; }
  @keyframes theme-skeleton-shimmer {
    0%   { background-position:  100% 0; }
    100% { background-position: -100% 0; }
  }
  @media (prefers-reduced-motion: reduce) {
    .theme-skeleton { animation: none; }
  }
  /* ζ.8: command palette (Cmd+K / Ctrl+K). Fixed overlay + centered
     modal with search input + result listbox + kbd-hint footer.
     Composes ζ.1 surfaces, ζ.4 typography (mono kbd hints), ζ.5
     icons. The whole modernization arc pays out here. */
  .theme-cmd-backdrop {
    position: fixed;
    inset: 0;
    z-index: 9999;
    background: rgba(15, 23, 42, 0.5);
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding-top: 12vh;
    animation: theme-cmd-fade-in 150ms ease-out;
  }
  :root[data-theme="dark"] .theme-cmd-backdrop {
    background: rgba(0, 0, 0, 0.65);
  }
  .theme-cmd-modal {
    width: 100%;
    max-width: 32rem;
    margin: 0 1rem;
    background: var(--color-bg-surface);
    color: var(--color-text-primary);
    border: 1px solid var(--color-border);
    border-radius: 0.625rem;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    max-height: 70vh;
  }
  .theme-cmd-input {
    width: 100%;
    padding: 0.875rem 1rem;
    border: none;
    border-bottom: 1px solid var(--color-border);
    background: transparent;
    color: var(--color-text-primary);
    font-size: var(--font-size-base);
    font-family: var(--font-stack-body);
    outline: none;
  }
  .theme-cmd-input::placeholder { color: var(--color-text-muted); }
  .theme-cmd-list {
    list-style: none;
    margin: 0;
    padding: 0.375rem;
    overflow-y: auto;
    flex: 1;
  }
  .theme-cmd-item {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: none;
    background: transparent;
    color: var(--color-text-primary);
    cursor: pointer;
    border-radius: 0.375rem;
    text-align: left;
    font-size: var(--font-size-sm);
    font-family: var(--font-stack-body);
  }
  .theme-cmd-item-label  { flex: 1; }
  .theme-cmd-item-route  {
    font-family: var(--font-stack-mono);
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
  }
  .theme-cmd-item-icon   { color: var(--color-text-muted); opacity: 0; }
  .theme-cmd-item-selected {
    background: var(--color-accent);
    color: var(--color-text-on-accent);
  }
  .theme-cmd-item-selected .theme-cmd-item-route,
  .theme-cmd-item-selected .theme-cmd-item-icon { color: var(--color-text-on-accent); }
  .theme-cmd-item-selected .theme-cmd-item-icon { opacity: 1; }
  .theme-cmd-footer {
    display: flex;
    gap: 0.875rem;
    padding: 0.5rem 0.75rem;
    border-top: 1px solid var(--color-border);
    background: var(--color-bg-page);
  }
  .theme-cmd-kbd {
    display: inline-block;
    padding: 0.0625rem 0.375rem;
    font-family: var(--font-stack-mono);
    font-size: var(--font-size-xs);
    line-height: 1.25;
    color: var(--color-text-primary);
    background: var(--color-bg-surface);
    border: 1px solid var(--color-border);
    border-radius: 0.25rem;
  }
  @keyframes theme-cmd-fade-in {
    from { opacity: 0; }
    to   { opacity: 1; }
  }
  /* ν.7: inline-editable element styling. Composes with ζ.1 tokens
     so dark mode + the editable visual states stay coherent. */
  .theme-editable {
    border-bottom: 1px dashed var(--color-border);
    cursor: text;
    padding: 0.0625rem 0.125rem;
    transition: background-color 100ms ease, border-color 100ms ease;
  }
  .theme-editable:hover {
    background: var(--color-bg-page);
    border-bottom-color: var(--color-text-muted);
  }
  .theme-editable-active {
    background: var(--color-bg-surface);
    border: 1px solid var(--color-accent);
    border-radius: 0.25rem;
    padding: 0.0625rem 0.25rem;
  }
  .theme-editable-pending {
    opacity: 0.6;
    pointer-events: none;
  }
  .theme-editable-error {
    border-color: var(--color-status-error);
    background: rgba(220, 38, 38, 0.05);
  }
  .theme-editable-input {
    font: inherit;
    color: inherit;
    background: transparent;
    border: none;
    outline: none;
    padding: 0;
    margin: 0;
    width: 100%;
    min-width: 4rem;
  }
  /* δ.1: reading-streak indicator. Quiet bottom-right fixed pill
     showing the current consecutive-day streak. Hidden when
     streak is zero. Theme-aware via ζ.1 tokens; clickable to
     dispatch a streakchange event for future δ.* listeners. */
  .theme-streak-indicator {
    position: fixed;
    bottom: 0.75rem;
    right: 0.75rem;
    z-index: 9997;
    display: none;
    align-items: center;
    gap: 0.375rem;
    padding: 0.375rem 0.625rem;
    background: var(--color-bg-surface);
    color: var(--color-text-primary);
    border: 1px solid var(--color-border);
    border-radius: 9999px;
    font-size: var(--font-size-xs);
    line-height: 1.25;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
    cursor: default;
    user-select: none;
  }
  .theme-streak-indicator.theme-streak-visible { display: inline-flex; }
  .theme-streak-indicator .theme-icon { color: rgb(234 88 12); /* orange-600, theme-independent flame */ }
  .theme-streak-indicator .theme-streak-count {
    font-weight: var(--font-weight-semibold);
  }
</style>"""


# ----------------------------------------------------------------------
# ζ.5 — inline-SVG icon library. Lucide-shaped (24x24 viewBox, 2px
# stroke, rounded cap/join), `stroke="currentColor" fill="none"`
# so they automatically pick up the parent's text color. Use with
# `.theme-icon` class (from ζ.5's CSS block above) for sizing.
#
# Why inline (not <img src="icon.svg"> or an icon font):
#   - No extra HTTP request per icon
#   - `currentColor` makes them theme-aware for free
#   - No FOIT — they render with the first paint
#   - Sized via parent's `1em`; no separate sizing system
#
# Adding an icon: pick the Lucide path (https://lucide.dev), wrap
# in `_make_icon(name, path)` and append to ICONS_REGISTRY. The
# `theme_icon(name)` builder + the JS-side window.ebibleIcons
# table both pick it up automatically.
#
# Why a registry instead of bare module-level constants:
#   - Tests can iterate (assert every icon has the right shape)
#   - JS exposure (window.ebibleIcons) is auto-generated
#   - A future ζ.* phase can add ad-hoc icons without modifying
#     this file's structure
# ----------------------------------------------------------------------

_ICON_SVG_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round" '
    'aria-hidden="true" class="theme-icon" data-icon="{name}">'
    "{path}"
    "</svg>"
)


def _make_icon(name: str, path: str) -> str:
    return _ICON_SVG_TEMPLATE.format(name=name, path=path)


# Lucide-shape paths (https://lucide.dev). Each value is the inner
# `<path>` / `<line>` / `<polyline>` markup of a 24x24 SVG; the
# wrapper attrs come from _ICON_SVG_TEMPLATE.
ICONS_REGISTRY: dict[str, str] = {
    "check": _make_icon("check", '<polyline points="20 6 9 17 4 12"></polyline>'),
    "alert-triangle": _make_icon(
        "alert-triangle",
        '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>'
        '<line x1="12" y1="9" x2="12" y2="13"></line>'
        '<line x1="12" y1="17" x2="12.01" y2="17"></line>',
    ),
    "x-circle": _make_icon(
        "x-circle",
        '<circle cx="12" cy="12" r="10"></circle>'
        '<line x1="15" y1="9" x2="9" y2="15"></line>'
        '<line x1="9" y1="9" x2="15" y2="15"></line>',
    ),
    "info": _make_icon(
        "info",
        '<circle cx="12" cy="12" r="10"></circle>'
        '<line x1="12" y1="16" x2="12" y2="12"></line>'
        '<line x1="12" y1="8" x2="12.01" y2="8"></line>',
    ),
    "chevron-right": _make_icon("chevron-right", '<polyline points="9 18 15 12 9 6"></polyline>'),
    "external-link": _make_icon(
        "external-link",
        '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>'
        '<polyline points="15 3 21 3 21 9"></polyline>'
        '<line x1="10" y1="14" x2="21" y2="3"></line>',
    ),
    "flame": _make_icon(
        "flame",
        # δ.1 — reading-streak indicator. Lucide `flame` icon.
        '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path>',
    ),
    "bookmark": _make_icon(
        "bookmark",
        # δ.2 — bookmark indicator. Lucide `bookmark` icon.
        '<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>',
    ),
}


def theme_icon(name: str) -> str:
    """Return the inline-SVG markup for `name`, or empty string if
    not registered. Use in Python f-strings:

        f'<button>{theme_icon("check")} Save</button>'
    """
    return ICONS_REGISTRY.get(name, "")


# JS exposure — the same icon table, accessible to client-side code
# via `window.ebibleIcons.check` etc. Generated once at module load
# so adding to ICONS_REGISTRY automatically updates the JS payload.
def _build_icons_js() -> str:
    import json

    # JSON-encode so quotes inside SVG (`stroke-linecap="round"` etc.)
    # don't break the JS literal.
    payload = json.dumps(ICONS_REGISTRY)
    return (
        "<script>\n"
        "/* ζ.5: SVG icon registry, exposed to client JS. Mirrors\n"
        "   scripts.templates._design.ICONS_REGISTRY. Read via\n"
        "   `window.ebibleIcons['<name>']`. Add new icons by\n"
        "   appending to ICONS_REGISTRY in _design.py — this script\n"
        "   block regenerates at module load. */\n"
        f"window.ebibleIcons = {payload};\n"
        "</script>"
    )


THEME_ICONS_JS = _build_icons_js()


# ----------------------------------------------------------------------
# ζ.6 — toast notifications. `window.ebibleToast(message, kind)` is
# the lightweight ephemeral-banner API: replaces ad-hoc per-console
# `<div class="fail-bg">` markup with a centralized, themable,
# screen-reader-aware notification stack.
#
# Usage from JS:
#     window.ebibleToast('Saved.', 'success');
#     window.ebibleToast('Network error: ' + e.message, 'error');
#     window.ebibleToast('No popup translation set on 2 editions.', 'warn');
#     window.ebibleToast('Build queued; refreshing in 5s', 'info');
#
# Kind defaults to 'info' when unknown / omitted. Auto-dismiss after
# 4s; manual dismiss via the × button. Errors get role="alert" +
# aria-live="assertive" (immediately announced); others get
# role="status" + aria-live="polite" (announced at next idle).
#
# Icons come from window.ebibleIcons (ζ.5). Colors come from
# --color-status-* (ζ.1). Sizing comes from --font-size-sm (ζ.4).
# This is the first ζ.* phase that composes all three foundations.
#
# Message text is inserted via `textContent` (XSS-safe). Any HTML
# in the message string renders as literal text, not markup.
# ----------------------------------------------------------------------

THEME_TOAST_JS = """<script>
(function () {
  'use strict';
  var KINDS = { info: 'info', success: 'check', warn: 'alert-triangle', error: 'x-circle' };
  var AUTO_DISMISS_MS = 4000;

  function ensureContainer() {
    var existing = document.getElementById('ebible-toast-container');
    if (existing) return existing;
    var c = document.createElement('div');
    c.id = 'ebible-toast-container';
    c.className = 'theme-toast-container';
    if (document.body) {
      document.body.appendChild(c);
    } else {
      document.addEventListener('DOMContentLoaded', function () {
        document.body.appendChild(c);
      });
    }
    return c;
  }

  function dismissToast(toast) {
    if (!toast || toast.classList.contains('theme-toast-leaving')) return;
    toast.classList.add('theme-toast-leaving');
    var done = function () { if (toast.parentNode) toast.parentNode.removeChild(toast); };
    toast.addEventListener('animationend', done, { once: true });
    // Fallback: if animationend doesn't fire (reduced-motion or browser
    // quirk), remove after the keyframe duration anyway.
    setTimeout(done, 400);
  }

  window.ebibleToast = function (message, kind) {
    var resolvedKind = KINDS.hasOwnProperty(kind) ? kind : 'info';
    var container = ensureContainer();
    var toast = document.createElement('div');
    toast.className = 'theme-toast theme-toast-' + resolvedKind;
    toast.setAttribute('role', resolvedKind === 'error' ? 'alert' : 'status');
    toast.setAttribute('aria-live', resolvedKind === 'error' ? 'assertive' : 'polite');

    var iconName = KINDS[resolvedKind];
    var iconSvg = (window.ebibleIcons && window.ebibleIcons[iconName]) || '';

    toast.innerHTML = ''
      + '<span class="theme-toast-icon-wrap">' + iconSvg + '</span>'
      + '<span class="theme-toast-message"></span>'
      + '<button type="button" class="theme-toast-dismiss" aria-label="Dismiss notification">×</button>';

    // textContent — XSS-safe. Caller doesn't need to escape.
    toast.querySelector('.theme-toast-message').textContent = String(message);
    container.appendChild(toast);

    var dismissBtn = toast.querySelector('.theme-toast-dismiss');
    dismissBtn.addEventListener('click', function () { dismissToast(toast); });
    var autoTimer = setTimeout(function () { dismissToast(toast); }, AUTO_DISMISS_MS);
    // Cancel auto-dismiss on hover so users can read long messages.
    toast.addEventListener('mouseenter', function () { clearTimeout(autoTimer); });

    return toast;
  };
})();
</script>"""


# ----------------------------------------------------------------------
# ζ.8 — command palette (Cmd+K / Ctrl+K). Closes the Month 2
# modernization arc. Composes everything ζ.* built:
#   - ζ.1 surfaces (--color-bg-surface, --color-accent, --color-border)
#   - ζ.4 typography (font sizes, mono stack for kbd hints + routes)
#   - ζ.5 icons (chevron-right for the selected-row affordance)
#   - ζ.6 toasts (callable from result actions in future extensions)
#
# Public API:
#     window.ebibleCmdPalette.open()    — open the palette
#     window.ebibleCmdPalette.close()   — close it
#     window.ebibleCmdPalette.toggle()  — toggle open/closed
#
# Keyboard:
#     Cmd+K (macOS) / Ctrl+K (other) — toggle from anywhere
#     ↑ / ↓ — navigate results
#     ↵ — open selected
#     Esc — close
#
# A11y:
#     - role="dialog" + aria-modal="true" + aria-label
#     - listbox / option semantics with aria-selected + aria-activedescendant
#     - autofocus on input when opened
#     - backdrop click closes (with target check to avoid closing on modal click)
#
# Data: CONSOLES list (Python) is JSON-embedded into the JS at module
# load — same pattern as THEME_ICONS_JS so the JS-side list stays
# in sync with the Python source of truth.
# ----------------------------------------------------------------------


def _build_cmd_palette_js() -> str:
    import json

    consoles_payload = json.dumps([{"route": route, "label": label} for (route, label) in CONSOLES])
    body = r"""<script>
(function () {
  'use strict';
  var CONSOLES = __CONSOLES_JSON__;

  var modal = null;
  var input = null;
  var listEl = null;
  var selectedIdx = 0;
  var filtered = CONSOLES.slice();
  var restoreFocusTo = null;

  function isOpen() { return !!modal; }

  function applyFilter() {
    var q = ((input && input.value) || '').trim().toLowerCase();
    if (!q) {
      filtered = CONSOLES.slice();
    } else {
      filtered = CONSOLES.filter(function (c) {
        return c.label.toLowerCase().indexOf(q) !== -1
            || c.route.toLowerCase().indexOf(q) !== -1;
      });
    }
    selectedIdx = 0;
    renderList();
  }

  function renderList() {
    if (!listEl) return;
    listEl.innerHTML = '';
    if (filtered.length === 0) {
      var empty = document.createElement('li');
      empty.className = 'theme-cmd-item theme-text-muted';
      empty.textContent = 'No matches.';
      listEl.appendChild(empty);
      return;
    }
    filtered.forEach(function (c, i) {
      var item = document.createElement('li');
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'theme-cmd-item';
      btn.setAttribute('role', 'option');
      btn.id = 'ebible-cmd-item-' + i;
      btn.setAttribute('aria-selected', i === selectedIdx ? 'true' : 'false');
      btn.dataset.index = String(i);

      var iconHtml = (window.ebibleIcons && window.ebibleIcons['chevron-right']) || '';
      btn.innerHTML = ''
        + '<span class="theme-cmd-item-label"></span>'
        + '<span class="theme-cmd-item-route"></span>'
        + '<span class="theme-cmd-item-icon">' + iconHtml + '</span>';
      btn.querySelector('.theme-cmd-item-label').textContent = c.label;
      btn.querySelector('.theme-cmd-item-route').textContent = c.route;

      btn.addEventListener('click', function () { activate(i); });
      btn.addEventListener('mouseenter', function () {
        selectedIdx = i;
        updateSelection();
      });

      item.appendChild(btn);
      listEl.appendChild(item);
    });
    updateSelection();
  }

  function updateSelection() {
    if (!listEl) return;
    var buttons = listEl.querySelectorAll('.theme-cmd-item');
    buttons.forEach(function (b, i) {
      var sel = (i === selectedIdx);
      b.classList.toggle('theme-cmd-item-selected', sel);
      b.setAttribute('aria-selected', sel ? 'true' : 'false');
      if (sel && input) {
        input.setAttribute('aria-activedescendant', 'ebible-cmd-item-' + i);
        if (b.scrollIntoView) b.scrollIntoView({ block: 'nearest' });
      }
    });
  }

  function activate(idx) {
    var target = filtered[idx];
    if (!target) return;
    close();
    window.location.href = target.route;
  }

  function onKeyDown(e) {
    if (e.key === 'Escape') {
      e.preventDefault();
      close();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (filtered.length) {
        selectedIdx = Math.min(selectedIdx + 1, filtered.length - 1);
        updateSelection();
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (filtered.length) {
        selectedIdx = Math.max(selectedIdx - 1, 0);
        updateSelection();
      }
    } else if (e.key === 'Enter') {
      e.preventDefault();
      activate(selectedIdx);
    }
  }

  function open() {
    if (isOpen()) return;
    restoreFocusTo = document.activeElement;

    var backdrop = document.createElement('div');
    backdrop.className = 'theme-cmd-backdrop';
    backdrop.id = 'ebible-cmd-backdrop';
    backdrop.addEventListener('click', function (e) {
      if (e.target === backdrop) close();
    });

    modal = document.createElement('div');
    modal.className = 'theme-cmd-modal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-label', 'Command palette');
    modal.innerHTML = ''
      + '<input type="text" class="theme-cmd-input" placeholder="Jump to console…" '
      +   'aria-label="Search consoles" '
      +   'aria-controls="ebible-cmd-list" '
      +   'aria-autocomplete="list" '
      +   'autocomplete="off" spellcheck="false">'
      + '<ul id="ebible-cmd-list" class="theme-cmd-list" role="listbox" aria-label="Console results"></ul>'
      + '<div class="theme-cmd-footer">'
      +   '<span><kbd class="theme-cmd-kbd">↑</kbd> <kbd class="theme-cmd-kbd">↓</kbd> navigate</span>'
      +   '<span><kbd class="theme-cmd-kbd">↵</kbd> open</span>'
      +   '<span><kbd class="theme-cmd-kbd">Esc</kbd> close</span>'
      + '</div>';

    input = modal.querySelector('.theme-cmd-input');
    listEl = modal.querySelector('.theme-cmd-list');

    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);

    input.addEventListener('input', applyFilter);
    input.addEventListener('keydown', onKeyDown);

    applyFilter();
    input.focus();
  }

  function close() {
    if (!isOpen()) return;
    var backdrop = document.getElementById('ebible-cmd-backdrop');
    if (backdrop && backdrop.parentNode) backdrop.parentNode.removeChild(backdrop);
    modal = null;
    input = null;
    listEl = null;
    selectedIdx = 0;
    if (restoreFocusTo && typeof restoreFocusTo.focus === 'function') {
      try { restoreFocusTo.focus(); } catch (e) { /* element gone */ }
    }
    restoreFocusTo = null;
  }

  function toggle() { if (isOpen()) close(); else open(); }

  // Global trigger: Cmd+K (macOS) / Ctrl+K (others). Listens on
  // capture phase so editor / input fields don't swallow it.
  document.addEventListener('keydown', function (e) {
    var k = (e.key || '').toLowerCase();
    if ((e.metaKey || e.ctrlKey) && k === 'k') {
      e.preventDefault();
      toggle();
    }
  });

  window.ebibleCmdPalette = { open: open, close: close, toggle: toggle };
})();
</script>"""
    return body.replace("__CONSOLES_JSON__", consoles_payload)


# ----------------------------------------------------------------------
# δ.1 — reading streaks (2026-05-11). First reader-track (δ family)
# phase. localStorage-only — no backend. Composes ζ.1 surfaces +
# ζ.4 typography + ζ.5 icons (the flame).
#
# Public API:
#     window.ebibleStreak.mark(ref)        — record a read for the
#                                            current calendar day; ref
#                                            optional (e.g. 'gen 1:1')
#     window.ebibleStreak.getStreak()      — current consecutive-day
#                                            streak; int
#     window.ebibleStreak.getReadDates()   — array of ISO date strings
#                                            on which any read happened
#     window.ebibleStreak.reset()          — clear all streak state
#
# Each mark dispatches a `streakchange` CustomEvent on `document` with
# `{ detail: { streak, dates } }`. Future δ.* phases (δ.2 bookmarks,
# δ.3 memorization, δ.6 pace-tracker) listen for this.
#
# UI: a quiet fixed-bottom-right pill inserts on DOMContentLoaded.
# Hidden via `display: none` unless streak > 0. Composes the flame
# icon from ζ.5's registry — adds visual punch without violating the
# project's no-emoji rule.
#
# localStorage shape:
#     ebible_streak = {
#       "dates": ["2026-05-09", "2026-05-10", "2026-05-11"],
#       "lastRef": "gen 1:1"   // optional; for δ.2 to read
#     }
#
# Streak math: a "streak" is the count of consecutive days ending
# today (or yesterday, if today hasn't been marked yet). A gap of
# one or more days breaks the streak.
# ----------------------------------------------------------------------

THEME_STREAK_JS = """<script>
(function () {
  'use strict';
  var STORAGE_KEY = 'ebible_streak';
  var FLAME_FALLBACK = '<svg class="theme-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path></svg>';

  function todayIso() {
    var d = new Date();
    var y = d.getFullYear();
    var m = String(d.getMonth() + 1).padStart(2, '0');
    var day = String(d.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + day;
  }

  function loadState() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return { dates: [], lastRef: null };
      var parsed = JSON.parse(raw);
      if (!parsed || !Array.isArray(parsed.dates)) return { dates: [], lastRef: null };
      return parsed;
    } catch (e) {
      return { dates: [], lastRef: null };
    }
  }

  function saveState(state) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) { /* private-mode browser — degrade silently */ }
  }

  function dateNDaysAgo(n) {
    var d = new Date();
    d.setDate(d.getDate() - n);
    var y = d.getFullYear();
    var m = String(d.getMonth() + 1).padStart(2, '0');
    var day = String(d.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + day;
  }

  function computeStreak(dates) {
    if (!dates || dates.length === 0) return 0;
    var set = {};
    for (var i = 0; i < dates.length; i++) set[dates[i]] = true;
    // Streak ends today OR yesterday (so a user who reads daily
    // doesn't lose the streak by checking late at night vs early
    // next morning).
    var startOffset = set[todayIso()] ? 0 : (set[dateNDaysAgo(1)] ? 1 : -1);
    if (startOffset < 0) return 0;
    var count = 0;
    var offset = startOffset;
    while (set[dateNDaysAgo(offset)]) {
      count++;
      offset++;
    }
    return count;
  }

  function mark(ref) {
    var state = loadState();
    var today = todayIso();
    if (state.dates.indexOf(today) === -1) {
      state.dates.push(today);
      // Keep only the last 400 dates (over a year of history is plenty).
      if (state.dates.length > 400) state.dates = state.dates.slice(-400);
    }
    if (ref != null) state.lastRef = String(ref);
    saveState(state);
    var streak = computeStreak(state.dates);
    updateIndicator(streak);
    document.dispatchEvent(new CustomEvent('streakchange', {
      detail: { streak: streak, dates: state.dates.slice() }
    }));
    return streak;
  }

  function getStreak() {
    return computeStreak(loadState().dates);
  }

  function getReadDates() {
    return loadState().dates.slice();
  }

  function reset() {
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) {}
    updateIndicator(0);
    document.dispatchEvent(new CustomEvent('streakchange', {
      detail: { streak: 0, dates: [] }
    }));
  }

  function updateIndicator(streak) {
    var el = document.getElementById('ebible-streak-indicator');
    if (!el) return;
    var countEl = el.querySelector('.theme-streak-count');
    if (countEl) countEl.textContent = String(streak);
    var unit = streak === 1 ? 'day' : 'days';
    var labelEl = el.querySelector('.theme-streak-label');
    if (labelEl) labelEl.textContent = unit + ' streak';
    if (streak > 0) {
      el.classList.add('theme-streak-visible');
    } else {
      el.classList.remove('theme-streak-visible');
    }
  }

  function insertIndicator() {
    if (document.getElementById('ebible-streak-indicator')) return;
    var el = document.createElement('div');
    el.id = 'ebible-streak-indicator';
    el.className = 'theme-streak-indicator';
    el.setAttribute('role', 'status');
    el.setAttribute('aria-label', 'Reading streak');
    var iconHtml = (window.ebibleIcons && window.ebibleIcons['flame']) || FLAME_FALLBACK;
    el.innerHTML = iconHtml
      + '<span class="theme-streak-count">0</span>'
      + ' <span class="theme-streak-label">day streak</span>';
    if (document.body) {
      document.body.appendChild(el);
    } else {
      document.addEventListener('DOMContentLoaded', function () {
        document.body.appendChild(el);
      });
    }
    // Initial render — show indicator if there's already a streak
    // from prior sessions.
    updateIndicator(getStreak());
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', insertIndicator);
  } else {
    insertIndicator();
  }

  window.ebibleStreak = {
    mark: mark,
    getStreak: getStreak,
    getReadDates: getReadDates,
    reset: reset
  };
})();
</script>"""


# ----------------------------------------------------------------------
# δ.2 — bookmarks / highlights (2026-05-11). Builds on δ.1's
# localStorage infrastructure. JSON sidecar that the reader exports
# and imports — no backend. Each bookmark carries an optional
# highlight color so the same storage backs both features.
#
# Public API:
#     window.ebibleBookmarks.add(ref, opts?)
#         — opts: { note: str, color: hex_or_name }
#         — returns the stored bookmark dict
#     window.ebibleBookmarks.remove(ref)
#         — returns true if removed, false if absent
#     window.ebibleBookmarks.list()
#         — array of all bookmarks, newest first
#     window.ebibleBookmarks.byRef(ref)
#         — single bookmark or null
#     window.ebibleBookmarks.isBookmarked(ref)
#         — boolean
#     window.ebibleBookmarks.toggle(ref, opts?)
#         — add if absent, remove if present; returns final state
#     window.ebibleBookmarks.export()
#         — returns JSON string (caller saves via blob URL)
#     window.ebibleBookmarks.exportAsDownload()
#         — triggers a browser download of `ebible-bookmarks-YYYY-MM-DD.json`
#     window.ebibleBookmarks.import_(json, opts?)
#         — opts: { merge: true } — default replaces; merge keeps
#           existing + adds new
#
# Each mutation dispatches a `bookmarkschange` CustomEvent on
# `document` so visible-bookmark badges in future reader pages can
# re-render without polling.
#
# Storage shape:
#     ebible_bookmarks = [
#       { "ref": "gen 1:1", "note": "...", "color": "#fbbf24",
#         "addedAt": "2026-05-11T18:30:00Z" },
#       ...
#     ]
# Ordering on disk: newest-first (most recent add first). list()
# preserves this order.
#
# `import_` is named with trailing underscore because `import` is a
# JS reserved word; the API exposes both `import` (via bracket access)
# and `import_` for direct dot-call. Tests pin both.
# ----------------------------------------------------------------------

THEME_BOOKMARKS_JS = """<script>
(function () {
  'use strict';
  var STORAGE_KEY = 'ebible_bookmarks';

  function loadAll() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  }

  function saveAll(items) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch (e) { /* private mode — degrade silently */ }
  }

  function notify() {
    document.dispatchEvent(new CustomEvent('bookmarkschange', {
      detail: { bookmarks: loadAll() }
    }));
  }

  function nowIso() {
    return new Date().toISOString();
  }

  function add(ref, opts) {
    if (ref == null) return null;
    var items = loadAll();
    // Remove any existing entry for the same ref so add() is
    // idempotent (semantically: "ensure this ref is bookmarked").
    items = items.filter(function (it) { return it.ref !== String(ref); });
    var entry = {
      ref: String(ref),
      note: (opts && opts.note != null) ? String(opts.note) : '',
      color: (opts && opts.color != null) ? String(opts.color) : '',
      addedAt: nowIso()
    };
    items.unshift(entry); // newest-first
    saveAll(items);
    notify();
    return entry;
  }

  function remove(ref) {
    if (ref == null) return false;
    var items = loadAll();
    var before = items.length;
    items = items.filter(function (it) { return it.ref !== String(ref); });
    if (items.length === before) return false;
    saveAll(items);
    notify();
    return true;
  }

  function list() {
    return loadAll();
  }

  function byRef(ref) {
    if (ref == null) return null;
    var items = loadAll();
    for (var i = 0; i < items.length; i++) {
      if (items[i].ref === String(ref)) return items[i];
    }
    return null;
  }

  function isBookmarked(ref) {
    return byRef(ref) !== null;
  }

  function toggle(ref, opts) {
    if (isBookmarked(ref)) {
      remove(ref);
      return false;
    }
    add(ref, opts);
    return true;
  }

  function exportJson() {
    return JSON.stringify(loadAll(), null, 2);
  }

  function exportAsDownload() {
    var json = exportJson();
    var blob = new Blob([json], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    var d = new Date();
    var stamp = d.getFullYear() + '-' +
      String(d.getMonth() + 1).padStart(2, '0') + '-' +
      String(d.getDate()).padStart(2, '0');
    a.href = url;
    a.download = 'ebible-bookmarks-' + stamp + '.json';
    document.body.appendChild(a);
    a.click();
    setTimeout(function () {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 0);
  }

  function importJson(jsonStr, opts) {
    var parsed;
    try {
      parsed = JSON.parse(String(jsonStr));
    } catch (e) {
      throw new Error('invalid JSON: ' + e.message);
    }
    if (!Array.isArray(parsed)) {
      throw new Error('expected array of bookmark entries');
    }
    var merge = !!(opts && opts.merge);
    var existing = merge ? loadAll() : [];
    var seenRefs = {};
    var out = [];
    // Imported entries take priority over existing on ref collision.
    parsed.forEach(function (entry) {
      if (!entry || typeof entry.ref !== 'string') return;
      if (seenRefs[entry.ref]) return;
      seenRefs[entry.ref] = true;
      out.push({
        ref: entry.ref,
        note: typeof entry.note === 'string' ? entry.note : '',
        color: typeof entry.color === 'string' ? entry.color : '',
        addedAt: typeof entry.addedAt === 'string' ? entry.addedAt : nowIso()
      });
    });
    existing.forEach(function (entry) {
      if (seenRefs[entry.ref]) return;
      seenRefs[entry.ref] = true;
      out.push(entry);
    });
    saveAll(out);
    notify();
    return out.length;
  }

  window.ebibleBookmarks = {
    add: add,
    remove: remove,
    list: list,
    byRef: byRef,
    isBookmarked: isBookmarked,
    toggle: toggle,
    export: exportJson,
    exportAsDownload: exportAsDownload,
    import: importJson,
    import_: importJson
  };
})();
</script>"""


# ----------------------------------------------------------------------
# ν.10 — recently-used quick access (2026-05-11).
#
# Tracks per-kind recently-used entries in localStorage so consoles
# can render "Recent: X, Y, Z" widgets without re-querying the
# server. Open-ended `kind` parameter — consoles decide what's
# trackable (editions, books, scenarios, translations, scripts, etc.).
#
# Public API:
#     window.ebibleRecents.track(kind, id, label?)
#         — record a use; idempotent on same (kind, id);
#           refreshes lastUsed timestamp
#     window.ebibleRecents.recent(kind, limit=5)
#         — most-recent entries first; up to `limit`
#     window.ebibleRecents.getAll()
#         — full state for export / debugging
#     window.ebibleRecents.clear(kind?)
#         — drop one kind's history (or all if kind omitted)
#
# Each mutation dispatches a `recentschange` CustomEvent on
# `document` with `{ detail: { kind, recents } }` — future widgets
# can re-render without polling.
#
# Storage shape (localStorage key `ebible_recents`):
#     {
#       "editions": [
#         {"id": "catholic-study", "label": "Catholic Study", "lastUsed": "2026-05-11T..."},
#         ...
#       ],
#       "books": [ ... ],
#       ...
#     }
#
# Per-kind cap: 50 entries. A user touching 50+ editions wouldn't
# reasonably see value from anything past the top of the list, and
# the cap keeps localStorage payload under ~10 KB total.
# ----------------------------------------------------------------------

THEME_RECENTS_JS = """<script>
(function () {
  'use strict';
  var STORAGE_KEY = 'ebible_recents';
  var PER_KIND_CAP = 50;

  function loadAll() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return {};
      var parsed = JSON.parse(raw);
      return (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) ? parsed : {};
    } catch (e) {
      return {};
    }
  }

  function saveAll(state) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) { /* private mode — degrade silently */ }
  }

  function notify(kind, recents) {
    document.dispatchEvent(new CustomEvent('recentschange', {
      detail: { kind: kind, recents: recents }
    }));
  }

  function track(kind, id, label) {
    if (kind == null || id == null) return;
    var state = loadAll();
    var k = String(kind);
    var entries = Array.isArray(state[k]) ? state[k] : [];
    // Remove existing entry for the same id (idempotent), then
    // unshift to front. Refresh label if a new one was passed.
    var existing = null;
    var filtered = [];
    for (var i = 0; i < entries.length; i++) {
      if (entries[i].id === String(id)) existing = entries[i];
      else filtered.push(entries[i]);
    }
    var entry = {
      id: String(id),
      label: label != null ? String(label) : (existing && existing.label) || String(id),
      lastUsed: new Date().toISOString()
    };
    filtered.unshift(entry);
    // Cap so localStorage stays bounded.
    if (filtered.length > PER_KIND_CAP) filtered = filtered.slice(0, PER_KIND_CAP);
    state[k] = filtered;
    saveAll(state);
    notify(k, filtered);
    return entry;
  }

  function recent(kind, limit) {
    if (kind == null) return [];
    var lim = (typeof limit === 'number' && limit > 0) ? Math.min(limit, PER_KIND_CAP) : 5;
    var state = loadAll();
    var entries = state[String(kind)];
    return Array.isArray(entries) ? entries.slice(0, lim) : [];
  }

  function getAll() {
    return loadAll();
  }

  function clear(kind) {
    var state = loadAll();
    if (kind == null) {
      try { localStorage.removeItem(STORAGE_KEY); } catch (e) {}
      notify(null, {});
      return;
    }
    var k = String(kind);
    if (state[k] == null) return;
    delete state[k];
    saveAll(state);
    notify(k, []);
  }

  window.ebibleRecents = {
    track: track,
    recent: recent,
    getAll: getAll,
    clear: clear
  };
})();
</script>"""


# ----------------------------------------------------------------------
# ω.39 — hot-reload for templates (2026-05-11). Minimum-viable
# polling implementation; the proper watchdog+SSE upgrade is ω.39.x.
#
# Behavior:
#   - Activates only when hostname is localhost / 127.0.0.1 / ::1.
#     Production deploys on real domains opt out automatically.
#   - Polls /api/dev/templates-mtime every 2s. Compares the returned
#     mtime_ns against the value seen at script-load. If it changed,
#     `window.location.reload()`.
#   - Console-logs once on activation so devs see "ω.39 hot-reload
#     watching" in DevTools.
#
# No external deps; uses only the standard fetch + setInterval. The
# `watchdog` Python package + SSE push are ω.39.x's deliverables —
# polling at 2s is plenty for hot-reload UX (sub-3s feels instant
# for "save → see change").
# ----------------------------------------------------------------------

THEME_HOTRELOAD_JS = """<script>
(function () {
  'use strict';
  // Localhost guard: only run in dev. Production deploys on real
  // domains skip this entirely.
  var host = window.location.hostname;
  var DEV_HOSTS = ['localhost', '127.0.0.1', '::1', ''];
  if (DEV_HOSTS.indexOf(host) === -1) return;

  var POLL_INTERVAL_MS = 2000;
  var baselineMtime = null;
  var pollCount = 0;

  function poll() {
    fetch('/api/dev/templates-mtime', { cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data || typeof data.mtime_ns !== 'number') return;
        if (baselineMtime === null) {
          baselineMtime = data.mtime_ns;
          console.log('[ω.39] hot-reload watching (baseline mtime=' + baselineMtime + ')');
          return;
        }
        if (data.mtime_ns !== baselineMtime) {
          console.log('[ω.39] template change detected; reloading…');
          window.location.reload();
        }
      })
      .catch(function () { /* network blip — ignore, next poll retries */ });
    pollCount++;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      poll();
      setInterval(poll, POLL_INTERVAL_MS);
    });
  } else {
    poll();
    setInterval(poll, POLL_INTERVAL_MS);
  }

  // Expose for tests + dev-tools.
  window.ebibleHotReload = {
    get baselineMtime() { return baselineMtime; },
    get pollCount() { return pollCount; }
  };
})();
</script>"""


# ----------------------------------------------------------------------
# ν.7 — inline editing standardization (2026-05-11). Click → swap
# to <input>, blur or Enter saves, Esc cancels. Standardized
# library that future per-console retrofits (ν.7.x for /customize,
# /publisher, /covers) adopt instead of rolling their own.
#
# Public API:
#     window.ebibleEditable.bind(element, options)
#         options:
#           onSave: async (newValue) => any           // returns or throws
#           validate?: (newValue) => boolean          // pre-save check
#           format?: (value) => string                // display formatting
#           placeholder?: string
#     window.ebibleEditable.unbind(element)            // remove handlers
#
# Lifecycle:
#     1. Click → idle becomes active: original text → <input>
#        with current value selected, autofocus.
#     2. Blur OR Enter → if validate returns true, call onSave
#        with the new value. Pending state (opacity + pointer-
#        events: none) while in flight. On success → idle with
#        new display. On failure → revert + ebibleToast error.
#     3. Esc → cancel; revert to original.
#
# Composes ζ.1 (theme colors), ζ.6 (toast on failure), ν.7's own
# CSS (.theme-editable / .theme-editable-active / etc).
#
# XSS safety: every display update uses textContent. Caller-
# supplied `format` function is called on the saved value before
# render; format-returned strings also rendered as text.
# ----------------------------------------------------------------------

THEME_EDITABLE_JS = """<script>
(function () {
  'use strict';

  function defaultFormat(value) { return value == null ? '' : String(value); }
  function defaultValidate() { return true; }

  function bind(element, options) {
    if (!element || element.__ebibleEditable) return;
    options = options || {};
    var onSave = typeof options.onSave === 'function' ? options.onSave : null;
    if (!onSave) {
      throw new Error('ebibleEditable.bind: onSave is required');
    }
    var validate = typeof options.validate === 'function' ? options.validate : defaultValidate;
    var format = typeof options.format === 'function' ? options.format : defaultFormat;
    var placeholder = options.placeholder || '';

    element.classList.add('theme-editable');
    if (placeholder && !element.textContent.trim()) {
      element.textContent = placeholder;
    }

    function enterEditMode() {
      if (element.classList.contains('theme-editable-active')) return;
      var originalText = element.textContent;
      var input = document.createElement('input');
      input.type = 'text';
      input.className = 'theme-editable-input';
      input.value = originalText === placeholder ? '' : originalText;
      input.setAttribute('aria-label', 'Edit ' + (element.getAttribute('aria-label') || 'value'));

      element.classList.add('theme-editable-active');
      element.textContent = '';
      element.appendChild(input);
      input.focus();
      input.select();

      var committed = false;
      function cleanup(finalText) {
        element.classList.remove('theme-editable-active');
        element.classList.remove('theme-editable-pending');
        // Use textContent for XSS-safety; format() output is also
        // treated as text.
        element.textContent = format(finalText != null ? finalText : originalText);
      }

      function commit() {
        if (committed) return;
        committed = true;
        var newValue = input.value;
        if (!validate(newValue)) {
          element.classList.add('theme-editable-error');
          input.focus();
          setTimeout(function () {
            element.classList.remove('theme-editable-error');
          }, 600);
          committed = false;
          return;
        }
        if (newValue === (originalText === placeholder ? '' : originalText)) {
          // No change → just revert chrome.
          cleanup(originalText);
          return;
        }
        element.classList.add('theme-editable-pending');
        Promise.resolve(onSave(newValue))
          .then(function () {
            cleanup(newValue);
          })
          .catch(function (err) {
            element.classList.remove('theme-editable-pending');
            element.classList.add('theme-editable-error');
            cleanup(originalText);
            element.classList.add('theme-editable-error');
            setTimeout(function () {
              element.classList.remove('theme-editable-error');
            }, 1500);
            if (window.ebibleToast) {
              window.ebibleToast('Save failed: ' + (err && err.message || err || 'unknown'), 'error');
            }
          });
      }

      function cancel() {
        committed = true;
        cleanup(originalText);
      }

      input.addEventListener('blur', commit);
      input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          commit();
        } else if (e.key === 'Escape') {
          e.preventDefault();
          cancel();
        }
      });
    }

    element.addEventListener('click', enterEditMode);
    element.__ebibleEditable = { enter: enterEditMode };
  }

  function unbind(element) {
    if (!element || !element.__ebibleEditable) return;
    // Simplest implementation: clone & replace, dropping listeners.
    // Caller can rebind if they want.
    var fresh = element.cloneNode(true);
    element.parentNode.replaceChild(fresh, element);
    fresh.classList.remove('theme-editable');
    delete fresh.__ebibleEditable;
  }

  window.ebibleEditable = {
    bind: bind,
    unbind: unbind
  };
})();
</script>"""


# ----------------------------------------------------------------------
# ζ.2 — dark-mode toggle (activates ζ.1's :root[data-theme="dark"]).
# Substituted into consoles via the `<!-- DARK_MODE_JS -->` marker
# placed inside the document `<head>` (must be inline-blocking so
# `data-theme` is set BEFORE the body paints — no flash of light).
#
# Behavior:
#   1. On script-load (synchronous): resolve initial theme from
#        localStorage → prefers-color-scheme media query → "light".
#      Sets `<html data-theme="dark">` or removes the attribute.
#      This runs before <body> paints, so dark-mode users never see
#      a flash of light.
#   2. On DOMContentLoaded: insert a fixed-position toggle button
#      (sun/moon SVG, top-right) into the document. The position is
#      `position: fixed` so the button doesn't require markup
#      changes in any existing console.
#   3. Click handler: flip the attribute, persist to localStorage,
#      swap the icon (sun ↔ moon), and dispatch a CustomEvent
#      `themechange` on `document` so future toast/skeleton
#      components can react.
#
# localStorage key: `ebible_theme` (namespace-prefixed to avoid
# collision with future per-feature toggles).
#
# Future ζ.* phases can listen for the `themechange` event to
# trigger their own redraws (e.g., re-rendering charts in
# matching colors).
# ----------------------------------------------------------------------

DARK_MODE_JS = """<script>
(function () {
  'use strict';
  var STORAGE_KEY = 'ebible_theme';
  var html = document.documentElement;

  // ---- Initial state: storage → media query → light ----
  function resolveInitial() {
    try {
      var saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'dark' || saved === 'light') return saved;
    } catch (e) { /* localStorage disabled — fall through */ }
    var prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    return prefersDark ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    if (theme === 'dark') {
      html.setAttribute('data-theme', 'dark');
    } else {
      html.removeAttribute('data-theme');
    }
  }

  // Apply immediately — this script is inline-blocking in <head>,
  // so this runs BEFORE the body paints. No FOAUC for dark-mode
  // users on first load.
  var currentTheme = resolveInitial();
  applyTheme(currentTheme);

  // Expose a small API for tests + future ζ.* components.
  window.ebibleTheme = {
    get: function () { return currentTheme; },
    set: function (theme) {
      currentTheme = (theme === 'dark') ? 'dark' : 'light';
      applyTheme(currentTheme);
      try { localStorage.setItem(STORAGE_KEY, currentTheme); } catch (e) {}
      document.dispatchEvent(new CustomEvent('themechange', { detail: { theme: currentTheme } }));
    },
    toggle: function () {
      this.set(currentTheme === 'dark' ? 'light' : 'dark');
    }
  };

  // ---- Toggle button (inserted post-DOMContentLoaded) ----
  function insertToggle() {
    if (document.getElementById('ebible-theme-toggle')) return;  // idempotent
    var btn = document.createElement('button');
    btn.id = 'ebible-theme-toggle';
    btn.type = 'button';
    btn.setAttribute('aria-label', 'Toggle dark mode');
    btn.title = 'Toggle dark mode (saves to this browser)';
    // Inline styles so the button renders correctly even on consoles
    // that haven't absorbed the THEME_TOKENS_CSS marker yet.
    btn.style.cssText = [
      'position:fixed', 'top:0.75rem', 'right:0.75rem', 'z-index:9999',
      'width:2.25rem', 'height:2.25rem', 'border-radius:9999px',
      'border:1px solid rgba(100,116,139,0.4)',
      'background:rgba(255,255,255,0.85)', 'backdrop-filter:blur(4px)',
      'cursor:pointer', 'display:flex', 'align-items:center',
      'justify-content:center', 'box-shadow:0 1px 2px rgba(0,0,0,0.08)',
      'transition:background-color 150ms ease,border-color 150ms ease'
    ].join(';');
    btn.innerHTML = ''
      + '<svg id="ebible-theme-icon-sun" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
      +   '<circle cx="12" cy="12" r="4"></circle>'
      +   '<path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path>'
      + '</svg>'
      + '<svg id="ebible-theme-icon-moon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display:none">'
      +   '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>'
      + '</svg>';
    function syncIcon() {
      var isDark = html.getAttribute('data-theme') === 'dark';
      var sun = document.getElementById('ebible-theme-icon-sun');
      var moon = document.getElementById('ebible-theme-icon-moon');
      if (sun && moon) {
        sun.style.display = isDark ? 'none' : '';
        moon.style.display = isDark ? '' : 'none';
      }
      // Adapt the button's own background to the active theme so it
      // stays visible on dark backgrounds without needing
      // THEME_TOKENS_CSS to be present.
      btn.style.background = isDark ? 'rgba(30,41,59,0.85)' : 'rgba(255,255,255,0.85)';
      btn.style.color = isDark ? 'rgb(241,245,249)' : 'rgb(15,23,42)';
    }
    syncIcon();
    btn.addEventListener('click', function () {
      window.ebibleTheme.toggle();
      syncIcon();
    });
    document.body.appendChild(btn);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', insertToggle);
  } else {
    insertToggle();
  }
})();
</script>"""


# ----------------------------------------------------------------------
# ζ.9 — First-run tour engine (2026-05-12).
#
# Minimal in-house tour overlay, no CDN dependency (per the project's
# invariant I.1: no heavy framework creep). Mirrors the public API
# shape that Shepherd.js / Driver.js / Intro.js use so future
# migration is cheap if needed.
#
# Public API:
#   window.ebibleTour.start(steps[, opts])
#       — steps: array of {selector, title, body, position?}
#         selector may be falsy → renders as a centred modal
#         position is 'top'|'bottom'|'left'|'right' (default 'bottom')
#       — opts: {storageKey?} (defaults to 'ebible_tour_seen_v1')
#   window.ebibleTour.skip() — close + mark seen
#   window.ebibleTour.next() / .back() — navigate manually
#   window.ebibleTour.startIfFirstRun(storageKey, steps[, opts])
#       — only starts when localStorage[storageKey] is missing
#   window.ebibleTour.reset(storageKey) — clear the seen flag
#       (used by /apihelp's "Restart tour" link)
#
# UX contract:
#   - Dim backdrop covers the whole viewport behind the tooltip.
#   - Target element gets a halo via outline style (no DOM mutation).
#   - Tooltip card has: title, body (textContent — XSS-safe), buttons.
#   - Skip ends the tour and marks seen. Back is disabled on step 0.
#   - Last step's Next button reads "Done".
#   - ESC closes; click-outside does NOT (avoid accidental skip).
#   - ARIA: role="dialog" + aria-modal + aria-labelledby; focus moves
#     into the tooltip on each step; ESC restores prior focus.
#   - Reduced-motion friendly — no animations.
#
# Composes ζ.1 theme tokens (color vars from THEME_TOKENS_CSS).
# Never auto-reshows: storage key bumps to v2 if the tour content
# materially changes and we want returning users to see it again.
# ----------------------------------------------------------------------

THEME_TOUR_JS = """<script>
(function () {
  'use strict';

  var STATE = {
    steps: null,
    index: 0,
    opts: null,
    priorFocus: null,
    backdrop: null,
    tooltip: null,
    halo: null,
  };

  var STORAGE_KEY_DEFAULT = 'ebible_tour_seen_v1';

  function makeEl(tag, className) {
    var el = document.createElement(tag);
    if (className) el.className = className;
    return el;
  }

  function buildBackdrop() {
    var bd = makeEl('div', 'ebible-tour-backdrop');
    bd.style.cssText = ''
      + 'position:fixed;inset:0;'
      + 'background:rgba(15,23,42,0.55);'
      + 'z-index:99998;';
    return bd;
  }

  function buildTooltip() {
    var card = makeEl('div', 'ebible-tour-tooltip');
    card.setAttribute('role', 'dialog');
    card.setAttribute('aria-modal', 'true');
    card.setAttribute('aria-labelledby', 'ebible-tour-title');
    card.style.cssText = ''
      + 'position:fixed;z-index:99999;'
      + 'max-width:24rem;min-width:14rem;'
      + 'padding:1rem 1.25rem;'
      + 'background:var(--color-bg-surface, #fff);'
      + 'color:var(--color-fg, #0f172a);'
      + 'border:1px solid var(--color-border, #e2e8f0);'
      + 'border-radius:0.5rem;'
      + 'box-shadow:0 10px 30px rgba(0,0,0,0.2);'
      + 'font-size:0.875rem;line-height:1.45;';

    var title = makeEl('h3');
    title.id = 'ebible-tour-title';
    title.style.cssText = 'margin:0 0 0.5rem 0;font-size:1rem;font-weight:600;';

    var body = makeEl('p');
    body.className = 'ebible-tour-body';
    body.style.cssText = 'margin:0 0 0.75rem 0;';

    var meta = makeEl('div', 'ebible-tour-meta');
    meta.style.cssText = ''
      + 'display:flex;align-items:center;justify-content:space-between;'
      + 'gap:0.5rem;margin-top:0.5rem;font-size:0.75rem;';

    var progress = makeEl('span', 'ebible-tour-progress');
    progress.style.cssText = 'color:var(--color-text-muted, #64748b);';

    var btnGroup = makeEl('div', 'ebible-tour-buttons');
    btnGroup.style.cssText = 'display:flex;gap:0.5rem;';

    var skip = makeEl('button', 'ebible-tour-skip');
    skip.type = 'button';
    skip.textContent = 'Skip';
    skip.style.cssText = ''
      + 'padding:0.25rem 0.6rem;font-size:0.75rem;'
      + 'background:transparent;border:1px solid var(--color-border, #cbd5e1);'
      + 'color:var(--color-text-muted, #64748b);'
      + 'border-radius:0.25rem;cursor:pointer;';

    var back = makeEl('button', 'ebible-tour-back');
    back.type = 'button';
    back.textContent = 'Back';
    back.style.cssText = skip.style.cssText;

    var next = makeEl('button', 'ebible-tour-next');
    next.type = 'button';
    next.textContent = 'Next';
    next.style.cssText = ''
      + 'padding:0.25rem 0.75rem;font-size:0.75rem;font-weight:600;'
      + 'background:var(--color-accent, #2563eb);color:#fff;'
      + 'border:1px solid var(--color-accent, #2563eb);'
      + 'border-radius:0.25rem;cursor:pointer;';

    btnGroup.appendChild(skip);
    btnGroup.appendChild(back);
    btnGroup.appendChild(next);
    meta.appendChild(progress);
    meta.appendChild(btnGroup);
    card.appendChild(title);
    card.appendChild(body);
    card.appendChild(meta);

    skip.addEventListener('click', skipTour);
    back.addEventListener('click', goBack);
    next.addEventListener('click', goNext);

    return card;
  }

  function buildHalo() {
    var halo = makeEl('div', 'ebible-tour-halo');
    halo.style.cssText = ''
      + 'position:fixed;pointer-events:none;'
      + 'border:3px solid var(--color-accent, #2563eb);'
      + 'border-radius:0.5rem;box-shadow:0 0 0 9999px rgba(15,23,42,0.55);'
      + 'z-index:99997;'
      + 'transition:none;';
    return halo;
  }

  function positionTooltip(step) {
    var tooltip = STATE.tooltip;
    var halo = STATE.halo;
    var backdrop = STATE.backdrop;
    if (!tooltip) return;
    var sel = step && step.selector;
    var target = sel ? document.querySelector(sel) : null;
    if (!target) {
      // Centred modal — hide halo + show full backdrop.
      if (halo) halo.style.display = 'none';
      if (backdrop) backdrop.style.background = 'rgba(15,23,42,0.55)';
      tooltip.style.left = '50%';
      tooltip.style.top = '50%';
      tooltip.style.transform = 'translate(-50%, -50%)';
      return;
    }
    var rect = target.getBoundingClientRect();
    if (halo) {
      halo.style.display = '';
      halo.style.left = (rect.left - 6) + 'px';
      halo.style.top = (rect.top - 6) + 'px';
      halo.style.width = (rect.width + 12) + 'px';
      halo.style.height = (rect.height + 12) + 'px';
    }
    // Hide backdrop colour — halo's box-shadow now provides the dim.
    if (backdrop) backdrop.style.background = 'transparent';

    tooltip.style.transform = '';
    var position = step.position || 'bottom';
    var margin = 12;
    var winW = window.innerWidth;
    var winH = window.innerHeight;
    var tipW = tooltip.offsetWidth || 320;
    var tipH = tooltip.offsetHeight || 120;
    var left, top;
    switch (position) {
      case 'top':
        left = Math.max(8, rect.left + rect.width / 2 - tipW / 2);
        top = Math.max(8, rect.top - tipH - margin);
        break;
      case 'left':
        left = Math.max(8, rect.left - tipW - margin);
        top = Math.max(8, rect.top + rect.height / 2 - tipH / 2);
        break;
      case 'right':
        left = Math.min(winW - tipW - 8, rect.right + margin);
        top = Math.max(8, rect.top + rect.height / 2 - tipH / 2);
        break;
      default:
        left = Math.max(8, rect.left + rect.width / 2 - tipW / 2);
        top = Math.min(winH - tipH - 8, rect.bottom + margin);
    }
    // Clamp into viewport.
    left = Math.max(8, Math.min(left, winW - tipW - 8));
    top = Math.max(8, Math.min(top, winH - tipH - 8));
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
  }

  function renderStep() {
    var step = STATE.steps[STATE.index];
    if (!step) return;
    var tooltip = STATE.tooltip;
    var titleEl = tooltip.querySelector('#ebible-tour-title');
    var bodyEl = tooltip.querySelector('.ebible-tour-body');
    var progressEl = tooltip.querySelector('.ebible-tour-progress');
    var backBtn = tooltip.querySelector('.ebible-tour-back');
    var nextBtn = tooltip.querySelector('.ebible-tour-next');
    // textContent — XSS-safe for every caller-supplied string.
    titleEl.textContent = step.title || '';
    bodyEl.textContent = step.body || '';
    progressEl.textContent = 'Step ' + (STATE.index + 1) + ' of ' + STATE.steps.length;
    backBtn.disabled = STATE.index === 0;
    backBtn.style.opacity = backBtn.disabled ? '0.4' : '1.0';
    nextBtn.textContent = STATE.index === STATE.steps.length - 1 ? 'Done' : 'Next';
    positionTooltip(step);
    // Move focus into the tooltip so keyboard users land here.
    setTimeout(function () { nextBtn.focus(); }, 0);
  }

  function endTour(markSeen) {
    if (STATE.backdrop && STATE.backdrop.parentNode) {
      STATE.backdrop.parentNode.removeChild(STATE.backdrop);
    }
    if (STATE.tooltip && STATE.tooltip.parentNode) {
      STATE.tooltip.parentNode.removeChild(STATE.tooltip);
    }
    if (STATE.halo && STATE.halo.parentNode) {
      STATE.halo.parentNode.removeChild(STATE.halo);
    }
    document.removeEventListener('keydown', onKeydown, true);
    window.removeEventListener('resize', onResize);
    if (markSeen && STATE.opts && STATE.opts.storageKey) {
      try { localStorage.setItem(STATE.opts.storageKey, '1'); } catch (e) {}
    }
    if (STATE.priorFocus && STATE.priorFocus.focus) {
      try { STATE.priorFocus.focus(); } catch (e) {}
    }
    var key = STATE.opts && STATE.opts.storageKey;
    STATE.steps = null;
    STATE.index = 0;
    STATE.opts = null;
    STATE.priorFocus = null;
    STATE.backdrop = null;
    STATE.tooltip = null;
    STATE.halo = null;
    document.dispatchEvent(new CustomEvent('ebibletourend', { detail: { storageKey: key } }));
  }

  function skipTour() { endTour(true); }
  function goNext() {
    if (STATE.index >= STATE.steps.length - 1) {
      endTour(true);
      return;
    }
    STATE.index += 1;
    renderStep();
  }
  function goBack() {
    if (STATE.index <= 0) return;
    STATE.index -= 1;
    renderStep();
  }

  function onKeydown(e) {
    if (e.key === 'Escape') {
      e.preventDefault();
      skipTour();
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      goNext();
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      goBack();
    }
  }

  function onResize() {
    if (STATE.steps) positionTooltip(STATE.steps[STATE.index]);
  }

  function startTour(steps, opts) {
    if (STATE.steps) return; // already running
    if (!steps || !steps.length) return;
    STATE.steps = steps;
    STATE.index = 0;
    STATE.opts = opts || { storageKey: STORAGE_KEY_DEFAULT };
    if (!STATE.opts.storageKey) STATE.opts.storageKey = STORAGE_KEY_DEFAULT;
    STATE.priorFocus = document.activeElement;
    STATE.backdrop = buildBackdrop();
    STATE.tooltip = buildTooltip();
    STATE.halo = buildHalo();
    document.body.appendChild(STATE.backdrop);
    document.body.appendChild(STATE.halo);
    document.body.appendChild(STATE.tooltip);
    document.addEventListener('keydown', onKeydown, true);
    window.addEventListener('resize', onResize);
    renderStep();
  }

  function startIfFirstRun(storageKey, steps, opts) {
    var key = storageKey || STORAGE_KEY_DEFAULT;
    var seen = false;
    try { seen = !!localStorage.getItem(key); } catch (e) {}
    if (seen) return false;
    var resolvedOpts = Object.assign({}, opts || {}, { storageKey: key });
    startTour(steps, resolvedOpts);
    return true;
  }

  function resetTour(storageKey) {
    var key = storageKey || STORAGE_KEY_DEFAULT;
    try { localStorage.removeItem(key); } catch (e) {}
  }

  window.ebibleTour = {
    start: startTour,
    skip: skipTour,
    next: goNext,
    back: goBack,
    startIfFirstRun: startIfFirstRun,
    reset: resetTour,
  };
})();
</script>"""


# ----------------------------------------------------------------------
# Console list — single source of truth for the cross-link nav.
# Adding a new console means appending here AND adding the route in
# scripts/web.py. The §6.2 cross-link invariant linter then verifies
# every console's HEADER_NAV references every other.
# ----------------------------------------------------------------------

# (route, short label) — order is meaningful (it's the nav order).
# The /matrix entry's route is "/" historically (§6.2 documented
# exception per the rules doc); both `/` and `/matrix` are accepted
# by the linter.
CONSOLES: list[tuple[str, str]] = [
    # Idiot-proof IA (v0.1.0): HOME leads; the note editor — a MAINTAINER tool —
    # sits LAST under an honest label. One edit here demotes it across every
    # console's nav at once (spec 2026-06-09-idiot-proof-app-design.md §3).
    ("/home", "home"),
    ("/matrix", "symbol matrix"),
    ("/build-tracker", "build tracker"),  # Ω.0 free-public pivot (2026-05-14)
    ("/sources", "sources"),
    ("/export", "export"),
    ("/customize", "customize"),
    ("/audit", "audit"),
    ("/audit-log", "audit log"),
    ("/publisher", "publisher"),
    ("/wizard", "wizard"),
    ("/diff", "diff"),
    ("/compare", "compare"),
    ("/covers", "covers"),
    ("/preflight", "preflight"),
    ("/ops", "ops"),
    ("/apihelp", "apihelp"),
    ("/hebrew", "hebrew"),  # γ.1
    ("/greek", "greek"),  # γ.2
    ("/distribution", "distribution"),  # mint-6 — re-surface free distribution UI
    ("/build-my-bible", "build my bible"),  # ρ.3 Phase C2 — hierarchical-customization navigator
    ("/notes", "notes (maintainer)"),  # the demoted note editor — keep LAST
]


# ζ.8 — command palette JS payload. Built after CONSOLES is defined
# so the embedded list reflects the live source-of-truth.
THEME_CMD_PALETTE_JS = _build_cmd_palette_js()


def HEADER_NAV_LINKS(current: str = "") -> str:
    """Return just the cross-link `<a>` tags, no wrapping `<div>`.

    Useful when a console wants to append additional elements
    (corpus-progress badge, save-pending indicator, etc.) inside
    its own nav container. The wrapping `<div>` flex container is
    the caller's responsibility.

    `current` is the route of the calling console — that link gets
    rendered as `font-semibold` (the "you are here" marker)."""
    parts = []
    for route, label in CONSOLES:
        if route == current:
            parts.append(f'    <a href="{route}" class="font-semibold">{label}</a>')
        else:
            parts.append(f'    <a href="{route}" class="text-blue-600 hover:underline">{label}</a>')
    return "\n".join(parts)


def HEADER_NAV(current: str = "") -> str:
    """Return the cross-link nav block — the row of route links that
    every console renders in its header.

    `current` is the route of the calling console (e.g. "/matrix");
    that link gets rendered without underline as the visual "you are
    here" marker.

    The output is a `<div>...</div>` containing the link list. The
    surrounding `<header>` chrome remains the caller's
    responsibility (each console's title + description is
    console-specific).
    """
    return '<div class="flex items-center gap-4 text-xs flex-wrap">\n' + HEADER_NAV_LINKS(current) + "\n  </div>"


def STATUS_BANNER(kind: str, message: str, *, hidden: bool = False) -> str:
    """Render a status banner div — inline informational / success /
    warning / error message. `kind` is one of 'info', 'success',
    'warn', 'error'. Pass `hidden=True` to render with the
    `hidden` class (Tailwind utility) so JS can show/hide later.

    Note: `message` is interpolated raw — caller is responsible for
    escaping if it contains untrusted content. The §9 patterns in
    web.py route adapters typically pass server-controlled strings
    that don't need escaping; templates rendering user content
    should use window.ebible.escapeHtml on the JS side.
    """
    cls_map = {
        "info": STATUS_INFO,
        "success": STATUS_SUCCESS,
        "warn": STATUS_WARN,
        "error": STATUS_ERROR,
    }
    cls = cls_map.get(kind)
    if cls is None:
        raise ValueError(f"unknown status kind: {kind!r}; expected info/success/warn/error")
    hidden_cls = " hidden" if hidden else ""
    return f'<div class="{cls}{hidden_cls}">{message}</div>'


def EMPTY_STATE(label: str = "Nothing here yet.") -> str:
    """Standardized empty-state placeholder. Renders a centered
    muted-gray message inside a card-style box. Use anywhere a list
    or table might be empty (no notes, no editions, no candidates,
    etc.) — better than a silent blank panel."""
    return f'<div class="text-center text-sm text-slate-400 py-8">{label}</div>'


def LOADING_STATE(label: str = "Loading…") -> str:
    """Standardized loading-state placeholder. Same visual rhythm as
    EMPTY_STATE but communicates "data is on its way." JS code that
    fetches async data renders this initially, then replaces it
    with the real content (or with EMPTY_STATE if the data is
    empty)."""
    return f'<div class="text-center text-sm text-slate-500 py-8 animate-pulse">{label}</div>'


# ----------------------------------------------------------------------
# ψ.13.5 — design-system substitution helper.
# ----------------------------------------------------------------------
#
# Phases ψ.14 / ψ.15 / ψ.16 each landed a per-template idiom:
#
#     XXXX_HTML = XXXX_HTML.replace(
#         "    <!-- HEADER_NAV_LINKS -->",
#         HEADER_NAV_LINKS("/route"),
#     )
#     XXXX_HTML = XXXX_HTML.replace(
#         "<!-- BUYER_ARC_POLISH_CSS -->",
#         BUYER_ARC_POLISH_CSS,
#     )
#
# Repeated in 13 templates. ψ.13.5 consolidates them into one
# helper so future substitutions (additional design-system markers)
# land in exactly one place.
#
# Why a helper instead of f-string conversion (per the original
# ψ.13.5 spec): the templates contain heavy inline JS + CSS with
# `{...}` braces; converting to f-strings would require escaping
# every brace as `{{...}}` — a high-risk mass diff with no
# user-visible benefit. The helper achieves the same single-source-
# of-truth goal without the brace-escaping cost.
#
# Templates use:
#
#     XXXX_HTML = apply_design_system(XXXX_HTML, "/route")
#
# in place of the two .replace() blocks at the bottom of the file.


def apply_design_system(html: str, current_route: str) -> str:
    """Substitute every design-system marker in the rendered HTML.

    Replaces:
      - `    <!-- HEADER_NAV_LINKS -->`  → HEADER_NAV_LINKS(current_route)
      - `<!-- BUYER_ARC_POLISH_CSS -->`  → BUYER_ARC_POLISH_CSS
      - `<!-- THEME_TOKENS_CSS -->`      → THEME_TOKENS_CSS  (ζ.1)
      - `<!-- DARK_MODE_JS -->`          → DARK_MODE_JS      (ζ.2)
      - `<!-- THEME_ICONS_JS -->`        → THEME_ICONS_JS    (ζ.5)
      - `<!-- THEME_TOAST_JS -->`        → THEME_TOAST_JS    (ζ.6)
      - `<!-- THEME_CMD_PALETTE_JS -->`  → THEME_CMD_PALETTE_JS (ζ.8)
      - `<!-- THEME_STREAK_JS -->`       → THEME_STREAK_JS    (δ.1)
      - `<!-- THEME_BOOKMARKS_JS -->`    → THEME_BOOKMARKS_JS (δ.2)
      - `<!-- THEME_RECENTS_JS -->`      → THEME_RECENTS_JS   (ν.10)
      - `<!-- THEME_HOTRELOAD_JS -->`    → THEME_HOTRELOAD_JS (ω.39)
      - `<!-- THEME_EDITABLE_JS -->`     → THEME_EDITABLE_JS  (ν.7)
      - `<!-- THEME_TOUR_JS -->`         → THEME_TOUR_JS      (ζ.9)

    The HEADER_NAV_LINKS marker MUST be 4-space-indented in the
    template — that's the existing convention from ψ.14/15/16. The
    BUYER_ARC_POLISH_CSS, THEME_TOKENS_CSS, and DARK_MODE_JS
    markers have no leading whitespace.

    DARK_MODE_JS must be placed INSIDE `<head>` so the inline-
    blocking init runs before the body paints (no FOAUC).

    Idempotent: running on a string that already had its markers
    replaced is a no-op (the replace just doesn't find anything).
    Tests rely on this idempotence to avoid double-substitution.

    Templates without the THEME_TOKENS_CSS marker silently skip
    that substitution — ζ.1 only retrofits the markers into one
    representative console (`/preflight`) as proof-of-concept.
    Future ζ.* phases add the marker to more consoles as theming
    work calls for it.

    Adding a new design-system marker (e.g. a future GLOBAL_FOOTER):
    add a `.replace(...)` line here and add the marker placement
    in each template. Single edit; uniform rollout.
    """
    html = html.replace(
        "    <!-- HEADER_NAV_LINKS -->",
        HEADER_NAV_LINKS(current_route),
    )
    html = html.replace(
        "<!-- BUYER_ARC_POLISH_CSS -->",
        BUYER_ARC_POLISH_CSS,
    )
    html = html.replace(
        "<!-- THEME_TOKENS_CSS -->",
        THEME_TOKENS_CSS,
    )
    html = html.replace(
        "<!-- DARK_MODE_JS -->",
        DARK_MODE_JS,
    )
    html = html.replace(
        "<!-- THEME_ICONS_JS -->",
        THEME_ICONS_JS,
    )
    html = html.replace(
        "<!-- THEME_TOAST_JS -->",
        THEME_TOAST_JS,
    )
    html = html.replace(
        "<!-- THEME_CMD_PALETTE_JS -->",
        THEME_CMD_PALETTE_JS,
    )
    html = html.replace(
        "<!-- THEME_STREAK_JS -->",
        THEME_STREAK_JS,
    )
    html = html.replace(
        "<!-- THEME_BOOKMARKS_JS -->",
        THEME_BOOKMARKS_JS,
    )
    html = html.replace(
        "<!-- THEME_RECENTS_JS -->",
        THEME_RECENTS_JS,
    )
    html = html.replace(
        "<!-- THEME_HOTRELOAD_JS -->",
        THEME_HOTRELOAD_JS,
    )
    html = html.replace(
        "<!-- THEME_EDITABLE_JS -->",
        THEME_EDITABLE_JS,
    )
    html = html.replace(
        "<!-- THEME_TOUR_JS -->",
        THEME_TOUR_JS,
    )
    html = html.replace(
        "<!-- WELCOME_OVERLAY_JS -->",
        WELCOME_OVERLAY_JS,
    )
    return html


# ----------------------------------------------------------------------
# W4.3 — first-run welcome overlay. A one-time modal shown on the root
# editor console (what the launcher opens) when scripts.core.onboarding
# reports first_run. "Start building" routes to /wizard; either button
# marks onboarding complete server-side (POST /api/onboarding/complete)
# so it never shows again. Built entirely with DOM nodes (no innerHTML)
# — satisfies the XSS guard and needs no template markup. Injected via a
# `<!-- WELCOME_OVERLAY_JS -->` marker; index.py substitutes it directly
# (it bypasses apply_design_system), and the marker is also wired into
# apply_design_system above so other consoles can opt in later.
# ----------------------------------------------------------------------

WELCOME_OVERLAY_JS = """<script>
(function () {
  'use strict';
  function build(state) {
    if (!state || !state.first_run) return;
    if (document.getElementById('yhwh-welcome-backdrop')) return;
    var backdrop = document.createElement('div');
    backdrop.id = 'yhwh-welcome-backdrop';
    backdrop.setAttribute('role', 'dialog');
    backdrop.setAttribute('aria-modal', 'true');
    backdrop.setAttribute('aria-label', 'Welcome');
    // M12 — the first-run welcome modal is built from inline styles the class/token
    // skin can't reach; retone it to the manuscript chrome so the very first end-user
    // surface matches (parchment card, ink/sepia serif text, the gold primary CTA).
    backdrop.style.cssText = 'position:fixed;inset:0;z-index:10000;background:rgba(15,23,42,0.6);display:flex;align-items:center;justify-content:center;padding:1rem;font-family:"EB Garamond","Noto Serif Ethiopic",Georgia,serif;';

    var card = document.createElement('div');
    card.style.cssText = 'background:#FBF6E9;max-width:30rem;width:100%;border-radius:0.75rem;padding:1.75rem;box-shadow:0 20px 50px rgba(43,33,24,0.3);';

    var h = document.createElement('h2');
    h.textContent = "Welcome to YHWH Ya' Way";
    h.style.cssText = 'font-size:1.5rem;font-weight:700;margin:0 0 0.5rem;color:#2B2118;';

    var p = document.createElement('p');
    p.textContent = 'Build your own study Bible: pick a tradition, choose which notes to include, and export an EPUB. The wizard walks you through it in a few steps.';
    p.style.cssText = 'font-size:0.95rem;color:#574532;margin:0 0 1.25rem;line-height:1.5;';

    var row = document.createElement('div');
    row.style.cssText = 'display:flex;gap:0.75rem;flex-wrap:wrap;';

    var start = document.createElement('button');
    start.type = 'button';
    start.textContent = 'Start building →';
    start.style.cssText = 'background:#B8860B;color:#2B2118;font-weight:600;padding:0.625rem 1.25rem;border:none;border-radius:0.5rem;cursor:pointer;font-size:0.95rem;';

    var skip = document.createElement('button');
    skip.type = 'button';
    skip.textContent = 'Explore on my own';
    skip.style.cssText = 'background:none;color:#574532;padding:0.625rem 1rem;border:1px solid rgba(154,110,18,0.6);border-radius:0.5rem;cursor:pointer;font-size:0.95rem;';

    function dismiss(goWizard) {
      fetch('/api/onboarding/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}'
      }).catch(function () {}).then(function () {
        if (backdrop.parentNode) backdrop.parentNode.removeChild(backdrop);
        if (goWizard) window.location.href = '/wizard';
      });
    }
    start.addEventListener('click', function () { dismiss(true); });
    skip.addEventListener('click', function () { dismiss(false); });

    row.appendChild(start);
    row.appendChild(skip);
    card.appendChild(h);
    card.appendChild(p);
    card.appendChild(row);
    backdrop.appendChild(card);
    (document.body || document.documentElement).appendChild(backdrop);
  }

  function check() {
    fetch('/api/onboarding')
      .then(function (r) { return r.json(); })
      .then(build)
      .catch(function () {});
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', check);
  } else {
    check();
  }
})();
</script>"""
