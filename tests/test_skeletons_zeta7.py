"""ζ.7 — skeleton loader pins.

Topic file (created alongside the ζ.7 ship, follows the ω.27
follow-on convention).

Coverage:
- TestZeta7SkeletonCss:        `.theme-skeleton` + variants +
  `@keyframes theme-skeleton-shimmer` + `prefers-reduced-motion`
  rules all present in THEME_TOKENS_CSS; colors pull from ζ.1
  tokens so dark mode adjusts automatically.
- TestZeta7PreflightRetrofit:  /preflight's `#checks` panel
  uses skeleton placeholders instead of the "running checks…"
  plain-text, carries `aria-busy="true"` while loading, and
  the JS `renderChecks` clears both the skeletons AND the
  aria-busy state once real data arrives.
- TestZeta7FetchErrorClearsSkeletons: the ζ.6 toast-error
  path also clears the skeletons (otherwise users see fake
  content shimmering forever after a network failure).

Pinning rationale: skeleton placeholders + aria-busy are the
project's first explicit loading-state contract. Drift in
the CSS (no shimmer animation, no reduced-motion respect)
or the aria-busy lifecycle (stays true forever, blinds screen
readers) would surface as a11y regression — hard to catch
without explicit pins.
"""

from __future__ import annotations


class TestZeta7SkeletonCss:
    """Skeleton CSS rules in THEME_TOKENS_CSS. Pin the base class
    + variants + animation + reduced-motion guard."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_TOKENS_CSS

        cls.css = THEME_TOKENS_CSS

    def test_base_skeleton_rule_present(self):
        assert ".theme-skeleton {" in self.css, "missing `.theme-skeleton {` rule"

    def test_base_skeleton_uses_theme_tokens(self):
        # Pin that the shimmer base + band pull from ζ.1 tokens so
        # dark mode adjusts automatically — otherwise the skeleton
        # would stay light-themed even in dark mode (visible bug).
        idx = self.css.find(".theme-skeleton {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "var(--color-bg-surface)" in block, "skeleton base color not themable"
        assert "var(--color-border)" in block, "skeleton shimmer band color not themable"

    def test_base_skeleton_uses_linear_gradient(self):
        # The shimmer effect IS the gradient sliding horizontally.
        # Without it, the skeleton would just be a static block.
        idx = self.css.find(".theme-skeleton {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "linear-gradient" in block, "skeleton missing the gradient that creates the shimmer"
        assert "background-size: 200% 100%" in block, (
            "skeleton missing oversized background — the slide animation needs room to move"
        )

    def test_base_skeleton_uses_shimmer_animation(self):
        idx = self.css.find(".theme-skeleton {")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "animation: theme-skeleton-shimmer" in block

    def test_text_variant_present(self):
        # Single-line text-height skeleton — for replacing inline
        # spans like the corpus-progress badge text.
        assert ".theme-skeleton-text" in self.css
        idx = self.css.find(".theme-skeleton-text")
        end = self.css.find("}", idx)
        block = self.css[idx:end]
        assert "height: 1em" in block, "text skeleton should match line height"

    def test_block_variant_present(self):
        # Taller paragraph/card skeleton.
        assert ".theme-skeleton-block" in self.css

    def test_shimmer_keyframes_present(self):
        # Animation definition — slides the gradient horizontally
        # so the bright band moves across.
        assert "@keyframes theme-skeleton-shimmer" in self.css

    def test_reduced_motion_disables_animation(self):
        # WCAG 2.3.3: respect prefers-reduced-motion.
        # Vestibular-disorder users get a static placeholder.
        # Anchor on the `@media` keyword rather than the bare
        # query phrase — the phrase also appears in the doc
        # comment earlier in the file, which would false-match.
        media_idx = self.css.find("@media (prefers-reduced-motion: reduce)")
        assert media_idx >= 0, "missing `@media (prefers-reduced-motion: reduce)` rule"
        window = self.css[media_idx : media_idx + 500]
        assert "theme-skeleton" in window, "reduced-motion block doesn't reference skeleton"
        assert "animation: none" in window, "reduced-motion doesn't actually stop the animation"


class TestZeta7PreflightRetrofit:
    """`/preflight` /checks panel uses skeleton placeholders +
    aria-busy while loading; renderChecks clears both."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.preflight import PREFLIGHT_HTML

        cls.html = PREFLIGHT_HTML

    def test_old_text_placeholder_gone(self):
        # The pre-ζ.7 `<p class="text-slate-500 text-sm">running
        # checks…</p>` is the visual we replaced. Pin its removal
        # so a future "let's revert to a simple text loader"
        # change is intentional.
        assert "running checks" not in self.html, (
            "old 'running checks…' text placeholder still present — ζ.7 didn't fully migrate"
        )

    def test_skeleton_placeholders_present(self):
        # The new state: skeleton blocks visible in #checks before
        # the first /api/preflight response.
        assert "theme-skeleton-block" in self.html
        # We render 3 stacked skeleton rows — pin the count so a
        # future change explicitly accounts for it.
        assert self.html.count('class="theme-skeleton theme-skeleton-block"') >= 3, (
            "expected at least 3 skeleton placeholders in /checks panel"
        )

    def test_aria_busy_set_while_loading(self):
        # The #checks container must declare aria-busy="true" so
        # screen readers don't try to read the shimmer placeholders
        # as real content.
        assert 'id="checks"' in self.html
        # Find the #checks div and confirm it has aria-busy="true"
        # AND aria-live="polite" (the latter lets the screen reader
        # announce the real content once it arrives).
        checks_idx = self.html.find('id="checks"')
        checks_end = self.html.find(">", checks_idx)
        checks_open_tag = self.html[checks_idx:checks_end]
        assert 'aria-busy="true"' in checks_open_tag, (
            "#checks missing aria-busy='true' — screen readers will read shimmer as content"
        )
        assert 'aria-live="polite"' in checks_open_tag, (
            "#checks missing aria-live='polite' — screen readers won't announce the real checks"
        )

    def test_sr_only_loading_text_present(self):
        # Visually-hidden status text for screen-reader users while
        # the shimmer plays. Tailwind's `.sr-only` class hides it
        # visually but exposes it to assistive tech.
        assert "sr-only" in self.html
        assert "Loading preflight checks" in self.html, "sr-only loading message missing"

    def test_render_checks_clears_skeletons(self):
        # The JS that swaps real checks in MUST clear the skeleton
        # placeholders. The existing `root.innerHTML = ''` line
        # does it; pin it stays.
        # Also pin the aria-busy reset — otherwise screen readers
        # stay parked in "loading" forever.
        assert "root.innerHTML = ''" in self.html, "renderChecks doesn't clear #checks"
        assert "setAttribute('aria-busy', 'false')" in self.html, (
            "renderChecks doesn't reset aria-busy — screen readers stay in loading state"
        )


class TestZeta7FetchErrorClearsSkeletons:
    """The ζ.6 toast-error path must also clear the skeletons —
    otherwise users see fake content shimmering forever after
    a network failure (the toast tells them what went wrong,
    but the page still LOOKS like it's loading)."""

    def test_catch_block_clears_skeletons_and_aria_busy(self):
        from scripts.templates.preflight import PREFLIGHT_HTML

        # The loadPreflight function has a catch block that handles
        # fetch failures. The dark-mode JS (ζ.2) ALSO has a catch
        # block (for localStorage access) — different concern, must
        # not be matched here. Anchor on the loadPreflight body by
        # finding `async function loadPreflight()` first, then
        # searching the next ~2000 chars for the catch contract.
        load_idx = PREFLIGHT_HTML.find("async function loadPreflight")
        assert load_idx >= 0, "could not find loadPreflight function"
        load_body = PREFLIGHT_HTML[load_idx : load_idx + 2000]
        # The catch block should: clear innerHTML, reset aria-busy,
        # call ebibleToast.
        assert "} catch (e) {" in load_body, "loadPreflight catch block missing"
        assert "root.innerHTML = ''" in load_body, "loadPreflight catch block doesn't clear skeletons"
        assert "setAttribute('aria-busy', 'false')" in load_body, (
            "loadPreflight catch block doesn't reset aria-busy — screen readers stuck in loading"
        )
        assert "ebibleToast" in load_body, "loadPreflight catch block doesn't surface the error as a toast"
