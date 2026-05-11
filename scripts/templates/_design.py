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
</style>"""


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
    ("/", "note editor"),
    ("/matrix", "symbol matrix"),
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
]


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
    return html
