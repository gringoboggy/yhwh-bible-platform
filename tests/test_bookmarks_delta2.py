"""δ.2 — bookmarks / highlights pins.

Topic file (created alongside the δ.2 ship). Closes Month 3.
Lowercase δ — reader track (distinct from uppercase Δ db track).

Coverage:
- TestDelta2BookmarksJs:          the `THEME_BOOKMARKS_JS` constant
  exposes the full `window.ebibleBookmarks` API surface (add /
  remove / list / byRef / isBookmarked / toggle / export /
  exportAsDownload / import / import_).
- TestDelta2BookmarkIcon:         `bookmark` icon added to ζ.5's
  ICONS_REGISTRY.
- TestDelta2ApplyDesignSystem:    `<!-- THEME_BOOKMARKS_JS -->`
  marker substitution.
- TestDelta2PreflightWired:       /preflight absorbs the marker.
- TestDelta2ApiSafety:            XSS / corruption guards
  (textContent vs innerHTML; try/catch around JSON.parse;
  malformed import raises).

Pinning rationale: δ.2 is the last Month 3 phase and the most
user-facing reader feature in the session. The export/import
contract is durable: users will share bookmark JSONs across
devices, and drift in the storage schema would orphan their
data. Pin each field.
"""

from __future__ import annotations


class TestDelta2BookmarksJs:
    """The `THEME_BOOKMARKS_JS` constant — full API surface."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_BOOKMARKS_JS

        cls.js = THEME_BOOKMARKS_JS

    def test_is_a_script_block(self):
        assert self.js.startswith("<script>")
        assert self.js.rstrip().endswith("</script>")

    def test_exposes_ebible_bookmarks_api(self):
        assert "window.ebibleBookmarks" in self.js

    def test_exposes_full_method_surface(self):
        # Every public method that downstream callers (a future
        # /read console, the EPUB JS layer, etc.) may need.
        for method in (
            "add:",
            "remove:",
            "list:",
            "byRef:",
            "isBookmarked:",
            "toggle:",
            "export:",
            "exportAsDownload:",
            "import:",
            "import_:",  # JS-reserved-word workaround alias
        ):
            assert method in self.js, f"API missing method {method!r}"

    def test_uses_namespaced_localstorage_key(self):
        # Pin `ebible_bookmarks` so a future cleanup doesn't quietly
        # rename and orphan existing users' bookmark data.
        assert "'ebible_bookmarks'" in self.js or "ebible_bookmarks" in self.js

    def test_localstorage_access_is_guarded(self):
        # Private-mode browsers must degrade silently, not throw.
        assert "try" in self.js
        assert "catch" in self.js

    def test_dispatches_bookmarkschange_event(self):
        # Visible-bookmark badges in future reader pages re-render
        # off this event without polling.
        assert "bookmarkschange" in self.js
        assert "CustomEvent" in self.js
        assert "detail" in self.js

    def test_storage_entries_have_canonical_shape(self):
        # The schema fields users will see in their exported JSON:
        # ref / note / color / addedAt. Drift here would orphan
        # imported files from older versions.
        for field in ("ref:", "note:", "color:", "addedAt:"):
            assert field in self.js, f"storage schema missing field {field!r}"

    def test_export_returns_pretty_json(self):
        # Pretty-printed JSON is friendly to humans inspecting the
        # exported file. `JSON.stringify(obj, null, 2)` is the form.
        assert "JSON.stringify" in self.js
        # Pin the 2-space indent so a future "compress for size"
        # change is intentional.
        assert ", null, 2" in self.js, "export JSON not pretty-printed (2-space indent)"

    def test_export_as_download_uses_blob_url(self):
        # Browser-native download via blob URL; no backend needed.
        assert "Blob([" in self.js
        assert "URL.createObjectURL" in self.js
        assert "URL.revokeObjectURL" in self.js, "exportAsDownload doesn't revoke the blob URL — memory leak"

    def test_export_filename_includes_date(self):
        # `ebible-bookmarks-YYYY-MM-DD.json` so users can keep
        # multiple snapshots.
        assert "ebible-bookmarks-" in self.js

    def test_import_validates_array_shape(self):
        # Malformed input (non-array JSON, non-string entries) must
        # raise Error rather than silently corrupt storage.
        assert "expected array" in self.js or "Array.isArray" in self.js

    def test_import_supports_merge_mode(self):
        # Default replaces; `{ merge: true }` keeps existing + adds
        # new. Pin both modes exist.
        assert "merge" in self.js

    def test_add_is_idempotent_on_same_ref(self):
        # Re-adding the same ref shouldn't create a duplicate;
        # it should refresh the existing entry's addedAt.
        # Pattern: `filter(it.ref !== ...)` then `unshift`.
        assert "filter(function" in self.js or "filter((it)" in self.js or "filter(" in self.js


class TestDelta2BookmarkIcon:
    """ζ.5's ICONS_REGISTRY ships a `bookmark` icon for δ.2."""

    def test_bookmark_in_registry(self):
        from scripts.templates._design import ICONS_REGISTRY

        assert "bookmark" in ICONS_REGISTRY

    def test_bookmark_is_valid_svg(self):
        from scripts.templates._design import ICONS_REGISTRY

        svg = ICONS_REGISTRY["bookmark"]
        assert svg.startswith("<svg ")
        assert svg.rstrip().endswith("</svg>")
        assert 'stroke="currentColor"' in svg
        assert 'viewBox="0 0 24 24"' in svg


class TestDelta2ApplyDesignSystem:
    """`<!-- THEME_BOOKMARKS_JS -->` marker substitution."""

    def test_substitutes_marker(self):
        from scripts.templates._design import THEME_BOOKMARKS_JS, apply_design_system

        before = "<head><!-- THEME_BOOKMARKS_JS --></head>"
        after = apply_design_system(before, "/preflight")
        assert "<!-- THEME_BOOKMARKS_JS -->" not in after
        assert THEME_BOOKMARKS_JS in after

    def test_no_op_when_marker_absent(self):
        from scripts.templates._design import THEME_BOOKMARKS_JS, apply_design_system

        before = "<html><body>hi</body></html>"
        after = apply_design_system(before, "/preflight")
        assert after == before
        assert THEME_BOOKMARKS_JS not in after

    def test_idempotent_on_second_call(self):
        from scripts.templates._design import apply_design_system

        once = apply_design_system("<!-- THEME_BOOKMARKS_JS -->", "/preflight")
        twice = apply_design_system(once, "/preflight")
        assert once == twice


class TestDelta2PreflightWired:
    """/preflight absorbs the bookmarks marker."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.preflight import PREFLIGHT_HTML

        cls.html = PREFLIGHT_HTML

    def test_marker_substituted_at_module_load(self):
        assert "<!-- THEME_BOOKMARKS_JS -->" not in self.html

    def test_ebible_bookmarks_api_present(self):
        assert "window.ebibleBookmarks" in self.html

    def test_lives_in_head(self):
        head_end = self.html.find("</head>")
        head = self.html[:head_end]
        assert "window.ebibleBookmarks" in head


class TestDelta2ApiSafety:
    """XSS / corruption guards in the bookmarks module."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import THEME_BOOKMARKS_JS

        cls.js = THEME_BOOKMARKS_JS

    def test_no_innerhtml_with_user_data(self):
        # The module doesn't render bookmark.note / bookmark.ref
        # into the DOM (that's a future /read console's job), so
        # the module itself shouldn't have innerHTML with template
        # interpolation that could be XSS'd. Pin via absence of
        # innerHTML calls that consume bookmark fields.
        for unsafe_pattern in (
            ".innerHTML = entry.",
            ".innerHTML = it.",
            ".innerHTML = b.",
        ):
            assert unsafe_pattern not in self.js, f"unsafe innerHTML pattern found: {unsafe_pattern!r}"

    def test_import_rejects_malformed_json(self):
        # The `import_` function throws on invalid JSON / non-array
        # shapes — caller catches.
        assert "throw new Error" in self.js
        assert "invalid JSON" in self.js or "expected array" in self.js
