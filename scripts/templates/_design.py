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
  /* ψ.14: visible keyboard-focus rings (buyers may demo via tab) */
  *:focus-visible {
    outline: 2px solid rgb(37 99 235); /* blue-600 */
    outline-offset: 2px;
    border-radius: 0.25rem;
  }
  button:focus-visible,
  a:focus-visible,
  input:focus-visible,
  select:focus-visible,
  textarea:focus-visible {
    outline: 2px solid rgb(37 99 235);
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

    The HEADER_NAV_LINKS marker MUST be 4-space-indented in the
    template — that's the existing convention from ψ.14/15/16. The
    BUYER_ARC_POLISH_CSS marker has no leading whitespace.

    Idempotent: running on a string that already had its markers
    replaced is a no-op (the replace just doesn't find anything).
    Tests rely on this idempotence to avoid double-substitution.

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
    return html
