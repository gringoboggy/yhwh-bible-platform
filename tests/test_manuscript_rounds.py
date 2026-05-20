"""Bounded-round-count escalation helper (audit U-belt 2026-05-20).

The controller calls ``escalate_if_unbounded(chapter_class, current_round,
hard_defects, new_ambiguous=0)`` BEFORE dispatching round N+1. If the
round trajectory has crossed the class's `expected_rounds_max` with non-
zero hard defects remaining (geometric convergence broken) OR if a single
round introduced more than 2 new AMBIGUOUS-PARCHMENT classes (review-class
explosion), the function returns an EscalationVerdict that the controller
uses to STOP and surface to the user instead of mechanically iterating.
"""


class TestNoEscalation:
    """Rounds within budget OR converging trajectory → ESCALATE=False."""

    def test_narrative_round_2_with_defects_no_escalate(self):
        from scripts.core.manuscript_rounds import escalate_if_unbounded

        verdict = escalate_if_unbounded("NARRATIVE", current_round=2, hard_defects=5)
        assert not verdict.escalate
        assert verdict.reason == ""

    def test_list_round_4_with_defects_no_escalate(self):
        from scripts.core.manuscript_rounds import escalate_if_unbounded

        verdict = escalate_if_unbounded("LIST", current_round=4, hard_defects=2)
        assert not verdict.escalate

    def test_any_round_with_zero_defects_no_escalate(self):
        from scripts.core.manuscript_rounds import escalate_if_unbounded

        # Zero hard defects = APPROVED CLEAN territory; no escalation
        # even past expected_rounds_max
        verdict = escalate_if_unbounded("LIST", current_round=10, hard_defects=0)
        assert not verdict.escalate


class TestEscalateOnRoundsExceeded:
    """Past `expected_rounds_max` with non-zero hard defects → ESCALATE."""

    def test_narrative_past_max_with_defects_escalates(self):
        """NARRATIVE expected_rounds_max = 4 per chapter_profile.
        Round 5 with defects → escalate."""
        from scripts.core.manuscript_rounds import escalate_if_unbounded

        verdict = escalate_if_unbounded("NARRATIVE", current_round=5, hard_defects=3)
        assert verdict.escalate
        assert "expected_rounds_max" in verdict.reason.lower() or "max" in verdict.reason.lower()

    def test_list_past_max_with_defects_escalates(self):
        """LIST expected_rounds_max = 7. Round 8 with defects → escalate."""
        from scripts.core.manuscript_rounds import escalate_if_unbounded

        verdict = escalate_if_unbounded("LIST", current_round=8, hard_defects=1)
        assert verdict.escalate

    def test_regnal_past_max_with_defects_escalates(self):
        from scripts.core.manuscript_rounds import escalate_if_unbounded

        verdict = escalate_if_unbounded("REGNAL_FRAME", current_round=9, hard_defects=2)
        assert verdict.escalate


class TestEscalateOnAmbiguousExplosion:
    """A single round introducing >2 new AMBIGUOUS classes → ESCALATE
    regardless of other conditions. The reviewer is finding NEW
    failure modes faster than convergence can resolve them."""

    def test_three_new_ambiguous_in_one_round_escalates(self):
        from scripts.core.manuscript_rounds import escalate_if_unbounded

        verdict = escalate_if_unbounded("NARRATIVE", current_round=2, hard_defects=0, new_ambiguous=3)
        assert verdict.escalate
        assert "ambiguous" in verdict.reason.lower()

    def test_two_new_ambiguous_acceptable(self):
        from scripts.core.manuscript_rounds import escalate_if_unbounded

        verdict = escalate_if_unbounded("NARRATIVE", current_round=2, hard_defects=0, new_ambiguous=2)
        # 2 new ambiguous is at-the-edge but not escalation; the
        # 1Ki4 R7 ship added 2 (v5 mid + v9 tail) and that was approved
        assert not verdict.escalate


class TestVerdictShape:
    """`EscalationVerdict` carries (escalate: bool, reason: str,
    recommended_action: str). The verdict is structured so the
    controller can surface a coherent message to the user."""

    def test_no_escalate_has_empty_strings(self):
        from scripts.core.manuscript_rounds import escalate_if_unbounded

        verdict = escalate_if_unbounded("NARRATIVE", current_round=2, hard_defects=0)
        assert not verdict.escalate
        assert verdict.reason == ""
        assert verdict.recommended_action == ""

    def test_escalate_carries_actionable_message(self):
        from scripts.core.manuscript_rounds import escalate_if_unbounded

        verdict = escalate_if_unbounded("LIST", current_round=8, hard_defects=2)
        assert verdict.escalate
        # Non-empty actionable strings the controller can include in
        # its user-surface message
        assert verdict.reason
        assert verdict.recommended_action


class TestUnknownChapterClass:
    def test_unknown_class_defaults_to_narrative_bounds(self):
        """Conservative default — if the controller passes an unknown
        class, treat as NARRATIVE (the smallest budget) to be safe."""
        from scripts.core.manuscript_rounds import escalate_if_unbounded

        verdict = escalate_if_unbounded("UNKNOWN_CLASS", current_round=5, hard_defects=2)
        # NARRATIVE max is 4; round 5 with defects → escalate
        assert verdict.escalate
