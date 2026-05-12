"""ν.10 — recently-used quick access pins.

Topic file (created alongside the ν.10 ship). Month 4 #1 of the
non-money sequence (Month 4 #4 per proposal numbering).

Coverage:
- TestNu10RecentsJs:           the `THEME_RECENTS_JS` constant
  exposes `window.ebibleRecents.{track, recent, getAll, clear}`,
  uses namespaced localStorage key, dispatches recentschange,
  caps history per kind, guards localStorage with try/catch.
- TestNu10ApplyDesignSystem:    `<!-- THEME_RECENTS_JS -->`
  marker substitution.
- TestNu10PreflightWired:      /preflight absorbs the marker.

Pinning rationale: ν.10 is infrastructure that future per-console
recent-X widgets consume. Drift in the API or storage shape would
break every downstream consumer silently.
"""

from __future__ import annotations


class TestNu10RecentsJs:
    """The `THEME_RECENTS_JS` constant — JS contract."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_RECENTS_JS

        cls.js = THEME_RECENTS_JS

    def test_is_a_script_block(self):
        assert self.js.startswith("<script>")
        assert self.js.rstrip().endswith("</script>")

    def test_exposes_ebible_recents_api(self):
        assert "window.ebibleRecents" in self.js

    def test_exposes_four_public_methods(self):
        for method in ("track:", "recent:", "getAll:", "clear:"):
            assert method in self.js, f"missing method {method!r}"

    def test_uses_namespaced_localstorage_key(self):
        assert "'ebible_recents'" in self.js or "ebible_recents" in self.js

    def test_localstorage_access_is_guarded(self):
        assert "try" in self.js
        assert "catch" in self.js

    def test_dispatches_recentschange_event(self):
        assert "recentschange" in self.js
        assert "CustomEvent" in self.js
        assert "detail" in self.js

    def test_per_kind_cap_is_50(self):
        # Pin the cap so a future "let's bump it to 1000" change
        # is intentional — unbounded growth becomes a localStorage
        # quota issue.
        assert "PER_KIND_CAP = 50" in self.js

    def test_track_is_idempotent_on_same_id(self):
        # Pattern: filter same id out, then unshift to front.
        # Pin the filter step so a future refactor can't drop it
        # and start growing duplicates.
        # (Token-level check — looks for the filter loop that
        # detects the id collision.)
        assert "i < entries.length" in self.js
        assert "entries[i].id" in self.js

    def test_entries_have_canonical_shape(self):
        # Schema: { id, label, lastUsed }
        for field in ("id:", "label:", "lastUsed:"):
            assert field in self.js, f"schema missing {field!r}"

    def test_recent_limit_defaults_to_5(self):
        # Proposal: "Last-5 ... at top of every console." Pin
        # the default so future widgets don't accidentally show
        # 50 entries.
        assert "limit > 0" in self.js
        # The default fallback should be 5 specifically.
        assert ": 5" in self.js, "default recent() limit drifted from 5"


class TestNu10ApplyDesignSystem:
    """`<!-- THEME_RECENTS_JS -->` marker substitution."""

    def test_substitutes_marker(self):
        from scripts.templates._design import THEME_RECENTS_JS, apply_design_system

        before = "<head><!-- THEME_RECENTS_JS --></head>"
        after = apply_design_system(before, "/preflight")
        assert "<!-- THEME_RECENTS_JS -->" not in after
        assert THEME_RECENTS_JS in after

    def test_no_op_when_marker_absent(self):
        from scripts.templates._design import THEME_RECENTS_JS, apply_design_system

        before = "<html><body>hi</body></html>"
        after = apply_design_system(before, "/preflight")
        assert after == before
        assert THEME_RECENTS_JS not in after

    def test_idempotent_on_second_call(self):
        from scripts.templates._design import apply_design_system

        once = apply_design_system("<!-- THEME_RECENTS_JS -->", "/preflight")
        twice = apply_design_system(once, "/preflight")
        assert once == twice


class TestNu10PreflightWired:
    """/preflight absorbs the recents marker."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.preflight import PREFLIGHT_HTML

        cls.html = PREFLIGHT_HTML

    def test_marker_substituted(self):
        assert "<!-- THEME_RECENTS_JS -->" not in self.html

    def test_ebible_recents_api_present(self):
        assert "window.ebibleRecents" in self.html

    def test_lives_in_head(self):
        head_end = self.html.find("</head>")
        head = self.html[:head_end]
        assert "window.ebibleRecents" in head
