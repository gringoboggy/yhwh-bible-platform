"""Bounded-round-count escalation (audit U-belt 2026-05-20).

The controller calls ``escalate_if_unbounded(chapter_class, current_round,
hard_defects, new_ambiguous=0)`` BEFORE dispatching round N+1 of any
C-3/C-6 review fix-loop. If the round trajectory has crossed the chapter
class's ``expected_rounds_max`` with non-zero hard defects remaining
(geometric convergence broken — see systematic-debugging "3+ fixes =
question the architecture" rule) OR if a single round introduced more
than 2 new AMBIGUOUS-PARCHMENT classes (the reviewer is finding new
failure modes faster than convergence can resolve them), the function
returns an ``EscalationVerdict(escalate=True, ...)`` that the controller
uses to STOP and surface to the user instead of mechanically iterating.

This is the executor-level enforcement of plan METHOD NOTE 3's escalation
bar. Documentation alone left the bar at the controller's discretion; the
helper makes it a function call with a clear pass/fail return.
"""

from __future__ import annotations

from dataclasses import dataclass

from .manuscript_chapter_class import chapter_profile


@dataclass(frozen=True)
class EscalationVerdict:
    """The controller's escalation decision payload.

    - ``escalate=False`` → safe to dispatch round N+1
    - ``escalate=True`` → STOP; surface ``reason`` + ``recommended_action``
      to the user before any further round is dispatched
    """

    escalate: bool
    reason: str
    recommended_action: str


_NO_ESCALATE = EscalationVerdict(escalate=False, reason="", recommended_action="")

# Default bounds when classify() doesn't know the chapter — match
# NARRATIVE (the tightest budget, conservative).
_NARRATIVE_MAX = 4


def _expected_rounds_max(chapter_class: str) -> int:
    """Look up the class's expected_rounds_max from the classifier's
    `chapter_profile`. Falls through to NARRATIVE bounds for unknown
    classes (conservative default — small budget surfaces drift sooner)."""
    # Use any valid (book, ch) in the class — the bounds depend only on
    # class. (1ki, 4) is LIST; (2ki, 15) is REGNAL; (1ki, 1) is NARRATIVE.
    sentinel_chapter = {
        "NARRATIVE": ("1ki", 1),
        "LIST": ("1ki", 4),
        "REGNAL_FRAME": ("2ki", 15),
    }.get(chapter_class)
    if sentinel_chapter is None:
        return _NARRATIVE_MAX
    return chapter_profile(*sentinel_chapter)["expected_rounds_max"]


def escalate_if_unbounded(
    chapter_class: str,
    current_round: int,
    hard_defects: int,
    new_ambiguous: int = 0,
) -> EscalationVerdict:
    """Decide whether to dispatch round N+1 or escalate to the user.

    Arguments
    ---------
    chapter_class
        The chapter's class per ``manuscript_chapter_class.classify``
        (one of ``NARRATIVE``, ``LIST``, ``REGNAL_FRAME``; unknown values
        default to NARRATIVE bounds).
    current_round
        The 1-indexed number of the round that JUST CLOSED. If
        ``current_round`` is the round whose APPROVED CLEAN sealed C-3,
        the caller doesn't need to ask (no N+1 to dispatch).
    hard_defects
        Hard defect count from the round that just closed. Zero means
        APPROVED CLEAN — no further round needed regardless of count.
    new_ambiguous
        Number of NEW AMBIGUOUS-PARCHMENT classes the round introduced.
        >2 in a single round is a class-explosion signal.

    Returns
    -------
    ``EscalationVerdict`` — see class docstring.
    """
    # Class explosion takes priority over zero-defect convergence —
    # finding 3+ new ambiguous classes in one round means the failure-
    # class taxonomy itself is escaping, regardless of whether the round
    # nominally cleared hard defects. The reviewer is finding new modes
    # faster than the matrix can absorb.
    if new_ambiguous > 2:
        return EscalationVerdict(
            escalate=True,
            reason=(
                f"new-ambiguous class explosion: round {current_round} "
                f"added {new_ambiguous} new AMBIGUOUS-PARCHMENT classes "
                "(>2 threshold). The failure-class taxonomy is escaping "
                "the current round's screening; mechanical iteration "
                "would compound rather than resolve."
            ),
            recommended_action=(
                "STOP this chapter's C-3/C-6 loop. Surface the new "
                "AMBIGUOUS classes to the user; consider whether "
                "topology files (`GG_topology.md`/`CAM_topology.md`) "
                "or the chapter classifier need updating before "
                "resuming."
            ),
        )

    # Trivially safe: zero hard defects (and no class explosion above) =
    # converged, no N+1 needed.
    if hard_defects <= 0:
        return _NO_ESCALATE

    max_rounds = _expected_rounds_max(chapter_class)
    if current_round >= max_rounds:
        return EscalationVerdict(
            escalate=True,
            reason=(
                f"current_round={current_round} >= expected_rounds_max="
                f"{max_rounds} for class={chapter_class!r} with "
                f"hard_defects={hard_defects} remaining. Geometric "
                "convergence appears broken (systematic-debugging: 3+ "
                "fixes failing = question the architecture)."
            ),
            recommended_action=(
                "STOP this chapter's C-3/C-6 loop. Surface the open "
                "defect list to the user with the per-round trajectory. "
                "Either the chapter is mis-classified (smaller budget "
                "than its real complexity) or the systematic-failure "
                "screens need extending. Do NOT dispatch round "
                f"{current_round + 1} without user direction."
            ),
        )

    return _NO_ESCALATE
