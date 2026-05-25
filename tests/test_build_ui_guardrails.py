"""Wave 4 W4.3 (slice 2b) — build-console guardrails.

The server caps concurrent builds (build_gate → HTTP 409); the build console
mirrors that client-side so a non-technical user gets a coherent experience:

  1. While EITHER build runs, BOTH build buttons (single-edition Export +
     Build-all) are disabled — a second build can't even be launched from the
     same tab.
  2. A 409 ('build_in_progress') is surfaced as a friendly "already building"
     message (built with safe DOM nodes, not innerHTML), not a raw error code.

(The no-editions empty-state ships with the welcome-flow slice, where it sits
alongside the onboarding UX.) These are source-presence pins (the project's
convention for the raw-string HTML consoles); live behaviour is confirmed
in-browser.
"""

from __future__ import annotations


class TestBuildUIGuardrails:
    def test_cross_button_lock_helper_exists(self):
        from scripts.web import EXPORT_HTML

        assert "lockBuildButtons" in EXPORT_HTML

    def test_both_build_flows_engage_the_lock(self):
        from scripts.web import EXPORT_HTML

        # Single-edition export AND build-all both lock + unlock the buttons.
        assert EXPORT_HTML.count("lockBuildButtons(true)") >= 2
        assert EXPORT_HTML.count("lockBuildButtons(false)") >= 2

    def test_409_build_in_progress_is_handled(self):
        from scripts.web import EXPORT_HTML

        # The console checks for the 409 status and shows the server's message.
        assert "409" in EXPORT_HTML

    def test_409_message_uses_safe_dom_not_innerhtml(self):
        from scripts.web import EXPORT_HTML

        # The build console builds the "already building" notice with a DOM
        # helper (textContent), never innerHTML — satisfies the XSS guard.
        assert "setBuildStatus" in EXPORT_HTML

    def test_no_editions_empty_state_points_to_wizard(self):
        from scripts.web import EXPORT_HTML

        # When /api/matrix returns no editions, the console guides the user to
        # the wizard instead of leaving a dead "— loading —" select. ("/wizard"
        # alone is in every console's nav, so pin on the distinctive copy.)
        assert "No editions yet" in EXPORT_HTML
