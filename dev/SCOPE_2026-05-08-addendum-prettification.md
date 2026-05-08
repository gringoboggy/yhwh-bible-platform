# Scope addendum — ψ cluster: comprehensive prettification

**Added:** 2026-05-08, after τ cluster scoped.
**Origin:** user request — *"can we prettify the program itself and
make it easy to use and nice to look at type of thing… for everything
you've mentioned… maximum everything in the most logical and
professional way."*

The platform's UI is functional but design-system-less. Every
console was Tailwind'd ad-hoc as it landed; there is no shared
button/card/badge/spacing vocabulary, no centralized color palette,
no consistent typography hierarchy. ψ.10 (popup typography) and
ψ.12 (matrix smoothness) already address two surfaces; this cluster
finishes the sweep across all surfaces with a coherent system.

## Goal

The buyer demo should *feel* like a commercial product, not a
developer tool. Same Tailwind CDN; no build step; no new
dependencies. Just opinionated patterns applied consistently.

## Sub-phase order

```
ψ.13  Design system foundation               ~ 1 session · LOW
      Extract a shared design-system module:
        scripts/templates/_design.py
      Exposes Python-side CSS strings + JS helper components that
      every console template imports. Concretely:
        - Tailwind class tokens (bg-page, bg-card, btn-primary,
          btn-ghost, btn-danger, badge-required, badge-optional,
          card-section, …) defined as constants.
        - Standardized header chrome (the cross-link nav block —
          today duplicated 13×; ω.0.7's bulk_inject already
          partially consolidates this; ψ.13 finishes the
          extraction).
        - Standardized status banner (info/success/warn/error —
          today every console reinvents).
        - One-line escape helper (window.ebible.escapeHtml is
          consolidated already; ψ.13 docs it as canonical).
        - Standardized empty-state and loading-state markup.
      Pre-v1.0: YES (foundation for ψ.14 / ψ.15 / ψ.17).
      Deliverables: _design.py module, every existing console's
                    inline duplicate replaced via bulk_inject;
                    visual-regression smoke (no breakage in the
                    13 consoles' rendered output).

ψ.14  Buyer-arc polish                        ~ 1-2 sessions · LOW-MED
      The three consoles a buyer sees during the demo flow:
      /wizard, /export, /compare. Apply the ψ.13 design system,
      tighten typography hierarchy, add micro-interactions
      (hover states, click feedback, save-pending indicators),
      polish the wizard's step transitions.
      Pre-v1.0: YES (north-star demo arc).
      Deliverables: each of /wizard, /export, /compare passes a
                    "looks like a commercial product" review;
                    keyboard-only navigation works through the
                    whole wizard.

ψ.15  Editor-console polish                   ~ 1-2 sessions · LOW
      /customize, /publisher, /covers, /matrix, /sources.
      Operator workflows; longer time-on-page than the buyer
      arc, so spacing rhythm and visual grouping matter most.
      Lower priority than ψ.14 because operators tolerate more
      density than buyers; v1.0-OK to ship slightly less polished
      here.
      Post-v1.0: ships as v1.1.
      Deliverables: each console gets coherent card/section
                    boundaries (extends ν.2.8); save-pending
                    state visible at a glance (extends ν.2.9);
                    keyboard shortcuts where they earn their
                    place.

ψ.16  Status-dashboard polish                 ~ ½ session · LOW
      /audit, /preflight, /ops. Read-only; function over form.
      Lowest UI priority — these are tools for diagnosing problems,
      not selling-the-product surfaces. A clean numeric KPI grid
      and clear pass/warn/fail color treatment is enough.
      Post-v1.0: v1.1+.
      Deliverables: KPI cards; consistent severity coloring.

ψ.17  Reader-EPUB polish                      ~ 1-2 sessions · MED
      The EPUB output the buyer's reader actually opens. Project
      already has infrastructure for chapter-number formatting
      (ν.6 CHAPTER_NUMBER_FORMATS), chapter ornaments
      (BOOK_TOC_ORNAMENTS), reader-experience knobs
      (ν.6.x apply_reader_toc_transforms). ψ.17 picks tasteful
      defaults so a freshly-built edition looks publishable
      without fiddling:
        - Drop-cap on chapter openings (CSS-only;
          first-letter rules).
        - ToC ornament pass (the project's existing ornaments are
          off by default; ψ.17 picks per-edition tasteful
          defaults).
        - Verse number treatment (subtle, not chunky).
        - Section/heading spacing rhythm.
        - Print-quality margins.
      Pre-v1.0: YES (this is what the buyer's reader sees).
      Deliverables: a freshly-built KJV EPUB rendered side-by-side
                    against a commercial study Bible — same level
                    of typographic care.
```

## v1.0 inclusion logic

Pre-v1.0 (ships before the first commercial cut):
- **ψ.13** — design system foundation (every later phase depends).
- **ψ.14** — buyer-arc polish (the demo MUST feel professional).
- **ψ.17** — reader-EPUB polish (the actual product output).
- ψ.10 — popup typography (already in scope; precedes ψ.8).
- ψ.12 — matrix smoothness (already in scope; precedes ψ.8).

Post-v1.0 (ship as v1.1+):
- **ψ.15** — editor-console polish.
- **ψ.16** — status-dashboard polish.

Updated v1.0 terminus:
```
v1.0 = θ.2 + χ.1 + ψ.8 + ψ.10 + ψ.12 + ψ.13 + ψ.14 + ψ.17
       + corpus ≥ 25K notes
```

## Tests / acceptance criteria

For each pre-v1.0 phase: a screenshot diff in
`tests/visual_baselines/<phase>/` and an updated
`scripts/lint_rules.py` check (if applicable) that asserts the
design-system tokens are referenced from console templates rather
than duplicated.

## Tradeoffs

- **No new dependencies.** Everything stays Tailwind CDN + plain
  ES6. A "real" design system would use a component library (React
  + headless UI, etc.), but the project's no-build-step rule rules
  that out and frankly the platform doesn't need it.
- **Visual regression is human-judgment-heavy.** The screenshot
  diffs catch obvious breakage but stylistic regressions need a
  human to notice. Each phase's ship checklist includes "user
  reviewed the rendered output and it looks better than before."
- **Reader-EPUB polish (ψ.17) is theme-coupled.** Some choices
  (drop-cap fonts, ornament glyphs) tie the look to specific
  themes. Per-edition theme override remains the publisher's
  control; ψ.17 just picks better defaults.
