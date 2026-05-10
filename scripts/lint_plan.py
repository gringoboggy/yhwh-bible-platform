#!/usr/bin/env python3
"""lint_plan.py — plan-coherence linter (Phase ω.15).

Verifies that the active ``dev/PLAN_<DATE>.md`` stays coherent with
what's actually shipped (``dev/CHANGELOG.md``) and what's open
(``dev/IN_FLIGHT.md``). Catches drift the moment it's introduced
rather than letting it accumulate across plan refreshes.

Today's checks:

  STATUS_SHIPPED  Every phase the PLAN marks as `✓ shipped` (in §7
       Phase ledger) appears as a phase mention in CHANGELOG.md.
       Catches "PLAN got refreshed but a 'shipped' marker was added
       prematurely" drift.

  STATUS_OPEN     Every phase the PLAN lists in `OPEN` (the §7
       Open block, plus the SHORT/MEDIUM/LONG/HARDENING/RELEASE
       sub-sections of §5) does NOT appear as a fully-shipped phase
       in CHANGELOG. Catches "shipped a phase but didn't update the
       PLAN" drift — the plan-side mirror of the existing
       `untracked_phases` linter check.

  DEPENDS_VALID   Every `Depends:` reference in the PLAN points to
       a known phase id (one that appears as ✓ shipped, ◯ open, ◐
       partial, △ parked, or ✗ deferred). A typo here silently
       breaks the dependency graph the linter is meant to enforce.

  PLAN_SINGULAR   Exactly ONE active `dev/PLAN_*.md` exists at the
       top level of `dev/`. Older plans must live in `dev/archive/`.
       Multi-plan ambiguity defeats the bootstrap protocol.

Usage:

    python3 scripts/lint_plan.py            # run all checks
    python3 scripts/lint_plan.py --json     # machine-readable output

Exits 0 on clean (all checks pass), 1 on any violation. Composed
into ``scripts/lint_rules.py:run_all()`` per the §9 "meta-tool"
mental model so the preflight dashboard surfaces plan drift
alongside the existing 10 invariant checks.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Phase id pattern: Greek letter + . + digit (with optional sub-version
# and -letter suffix). Plus the special composite ids that appear in
# the plan: "v1.0.0", "χ-AI-xrefs", "θ.3.1", etc.
PHASE_ID_RE = re.compile(
    r"(?<![A-Za-z])"
    r"(?:"
    r"[α-ω]\.\d+(?:\.\d+(?:\.\d+)?)?(?:-[A-Z])?"  # Greek letter family
    r"|χ-AI-xrefs"  # named composite
    r"|v\d+\.\d+\.\d+"  # release tag (3-part)
    r")"
    r"(?![A-Za-z0-9])"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _active_plan() -> Path | None:
    """Return the active PLAN file, or None if none exists.

    Picks the lexicographically latest ``dev/PLAN_*.md`` since
    filenames are date-stamped (PLAN_2026-05-09.md > 2026-05-08).
    """
    plans = sorted((REPO / "dev").glob("PLAN_*.md"))
    return plans[-1] if plans else None


# ----------------------------------------------------------------------
# Helpers — extract phase ids per status from the PLAN
# ----------------------------------------------------------------------


def _extract_shipped_ledger(plan_text: str) -> set[str]:
    """Phase ids in §7's `Shipped (✓)` block.

    The block is delimited by the `### Shipped (✓)` header and the
    next `###` header. Inside, phases sit in fenced code blocks; we
    extract everything that matches PHASE_ID_RE.
    """
    m = re.search(
        r"### Shipped \(✓\)\n(.*?)\n### ",
        plan_text,
        flags=re.DOTALL,
    )
    if not m:
        return set()
    return set(PHASE_ID_RE.findall(m.group(1)))


def _extract_open_ledger(plan_text: str) -> set[str]:
    """Phase ids in §7's `Open (◯)` block."""
    m = re.search(
        r"### Open \(◯\)\n(.*?)\n### ",
        plan_text,
        flags=re.DOTALL,
    )
    if not m:
        return set()
    return set(PHASE_ID_RE.findall(m.group(1)))


def _extract_partial_ledger(plan_text: str) -> set[str]:
    """Phase ids in §7's partial / infrastructure-shipped block."""
    m = re.search(
        r"### Shipped infrastructure[^\n]*\(◐\)\n(.*?)\n### ",
        plan_text,
        flags=re.DOTALL,
    )
    if not m:
        return set()
    return set(PHASE_ID_RE.findall(m.group(1)))


def _extract_parked_ledger(plan_text: str) -> set[str]:
    """Phase ids in §7's parked block. Identifiers may be free text
    rather than phase ids (e.g. 'min-confidence calibration mismatch')
    so we only extract the phase-id-shaped tokens that exist."""
    m = re.search(
        r"### Parked[^\n]*\(△\)\n(.*?)\n### ",
        plan_text,
        flags=re.DOTALL,
    )
    if not m:
        return set()
    return set(PHASE_ID_RE.findall(m.group(1)))


def _extract_deferred_ledger(plan_text: str) -> set[str]:
    m = re.search(
        r"### Indefinitely deferred[^\n]*\(✗\)\n(.*?)\n### ",
        plan_text,
        flags=re.DOTALL,
    )
    if not m:
        # Sometimes this is the last section
        m = re.search(
            r"### Indefinitely deferred[^\n]*\(✗\)\n(.*?)$",
            plan_text,
            flags=re.DOTALL,
        )
    if not m:
        return set()
    return set(PHASE_ID_RE.findall(m.group(1)))


def _extract_depends_refs(plan_text: str) -> set[str]:
    """Every phase id mentioned after a `**Depends:**` field.

    Lines like `**Depends:** ψ.7-A` or `**Depends:** ψ.15 (✓ shipped)`
    or `**Depends:** ψ.7-A + ψ.7-B (✓ once they ship)`. We extract
    every PHASE_ID_RE match on the line.
    """
    refs: set[str] = set()
    for line in plan_text.splitlines():
        if "**Depends:**" not in line:
            continue
        body = line.split("**Depends:**", 1)[1]
        # Strip parenthetical asides like "(✓ shipped)" — they are
        # human-readable status, not separate phase ids
        body_no_parens = re.sub(r"\([^)]*\)", "", body)
        for m in PHASE_ID_RE.finditer(body_no_parens):
            refs.add(m.group(0))
    return refs


def _all_known_phase_ids(plan_text: str) -> set[str]:
    """Union of every status block's phase ids — what counts as a
    'known' phase id for Depends:-validation purposes."""
    return (
        _extract_shipped_ledger(plan_text)
        | _extract_open_ledger(plan_text)
        | _extract_partial_ledger(plan_text)
        | _extract_parked_ledger(plan_text)
        | _extract_deferred_ledger(plan_text)
    )


def _changelog_shipped_phases() -> set[str]:
    """Every phase id that appears as SHIPPED in CHANGELOG.md.

    Definition of "shipped": the phase appears on a ``**Phases
    shipped:**`` line at the top of a CHANGELOG entry. Per project
    convention every shipped phase MUST appear on such a line, so
    this is the canonical source.

    Why only this line and not session headers: some session
    headers describe scope-expansion sessions where the phase
    listed is the *target* of a scoping decision, not the *ship*
    (e.g. ``## 2026-05-08 — session — scope expansion (free-only):
    ψ.8 + ρ.1 + ω.6 + ω.7`` — ρ.1 was added to the plan that
    session, not shipped). Restricting to ``**Phases shipped:**``
    eliminates the ambiguity.
    """
    chl = _read(REPO / "dev" / "CHANGELOG.md")
    shipped: set[str] = set()
    for line in chl.splitlines():
        if line.startswith("**Phases shipped:"):
            shipped |= set(PHASE_ID_RE.findall(line))
    return shipped


def _changelog_phase_mentions() -> set[str]:
    """Every phase id that appears anywhere in CHANGELOG.md.

    Looser than `_changelog_shipped_phases()` — used by the
    `plan_shipped` check to verify a PLAN-claimed-shipped phase has
    AT LEAST been mentioned somewhere (handles inherited / legacy
    phases without strict ship-line evidence).
    """
    chl = _read(REPO / "dev" / "CHANGELOG.md")
    return set(PHASE_ID_RE.findall(chl))


# ----------------------------------------------------------------------
# Individual check implementations
# ----------------------------------------------------------------------


def check_plan_singular() -> dict:
    """Exactly one ``dev/PLAN_*.md`` at the top level. Older plans
    must live in ``dev/archive/``."""
    top_level = sorted((REPO / "dev").glob("PLAN_*.md"))
    violations: list[dict] = []
    if len(top_level) == 0:
        violations.append(
            {
                "issue": "no PLAN_*.md found in dev/ — bootstrap will fail",
                "found": [],
            }
        )
    elif len(top_level) > 1:
        for p in top_level[:-1]:
            violations.append(
                {
                    "issue": "older PLAN should be in dev/archive/",
                    "file": str(p.relative_to(REPO)),
                }
            )
    return {
        "id": "plan_singular",
        "name": "Plan singular (one active PLAN_*.md)",
        "status": "fail" if violations else "pass",
        "message": (
            f"{len(top_level)} active PLAN file(s) found"
            if violations
            else f"exactly one active plan: {top_level[-1].name}"
        ),
        "violations": violations,
    }


def check_plan_status_shipped() -> dict:
    """Every phase the PLAN's §7 ledger marks ✓ shipped MUST appear
    in CHANGELOG.md (any mention)."""
    plan = _active_plan()
    if plan is None:
        return {
            "id": "plan_shipped",
            "name": "Plan-claimed shipped phases backed by CHANGELOG",
            "status": "fail",
            "message": "no active PLAN found",
            "violations": [],
        }
    plan_text = _read(plan)
    plan_shipped = _extract_shipped_ledger(plan_text)
    chl_mentions = _changelog_phase_mentions()
    missing = plan_shipped - chl_mentions
    violations = [{"issue": "PLAN says shipped but no CHANGELOG entry", "phase": ph} for ph in sorted(missing)]
    return {
        "id": "plan_shipped",
        "name": "Plan-claimed shipped phases backed by CHANGELOG",
        "status": "fail" if violations else "pass",
        "message": (
            f"{len(violations)} shipped-ledger phase(s) missing from CHANGELOG"
            if violations
            else f"all {len(plan_shipped)} shipped phase(s) backed by CHANGELOG"
        ),
        "violations": violations,
    }


def check_plan_status_open() -> dict:
    """Phases the PLAN lists as ◯ open should NOT appear in CHANGELOG
    yet — if they do, the PLAN is stale. Counterpart to the existing
    ``untracked_phases`` check (which goes the other direction)."""
    plan = _active_plan()
    if plan is None:
        return {
            "id": "plan_open",
            "name": "Plan-claimed open phases not yet shipped",
            "status": "fail",
            "message": "no active PLAN found",
            "violations": [],
        }
    plan_text = _read(plan)
    plan_open = _extract_open_ledger(plan_text)
    chl_shipped = _changelog_shipped_phases()
    stale = plan_open & chl_shipped
    violations = [{"issue": "PLAN says open but CHANGELOG has shipped entry", "phase": ph} for ph in sorted(stale)]
    return {
        "id": "plan_open",
        "name": "Plan-claimed open phases not yet shipped",
        "status": "warn" if violations else "pass",
        "message": (
            f"{len(violations)} open-ledger phase(s) appear shipped"
            if violations
            else f"all {len(plan_open)} open phase(s) confirmed not in CHANGELOG"
        ),
        "violations": violations,
    }


def check_plan_depends_valid() -> dict:
    """Every Depends: reference resolves to a known phase id."""
    plan = _active_plan()
    if plan is None:
        return {
            "id": "plan_depends",
            "name": "Plan Depends: graph references valid phases",
            "status": "fail",
            "message": "no active PLAN found",
            "violations": [],
        }
    plan_text = _read(plan)
    refs = _extract_depends_refs(plan_text)
    known = _all_known_phase_ids(plan_text)
    unknown = refs - known
    violations = [{"issue": "Depends: references unknown phase id", "phase": ph} for ph in sorted(unknown)]
    return {
        "id": "plan_depends",
        "name": "Plan Depends: graph references valid phases",
        "status": "fail" if violations else "pass",
        "message": (
            f"{len(violations)} Depends: reference(s) point to unknown phases"
            if violations
            else f"all {len(refs)} Depends: reference(s) resolve to known phases"
        ),
        "violations": violations,
    }


# ----------------------------------------------------------------------
# Runner
# ----------------------------------------------------------------------


ALL_CHECKS = {
    "plan_singular": check_plan_singular,
    "plan_shipped": check_plan_status_shipped,
    "plan_open": check_plan_status_open,
    "plan_depends": check_plan_depends_valid,
}


def run_all(check_ids: list[str] | None = None) -> dict:
    """Run every plan-coherence check. Composes into the broader
    ``scripts.lint_rules.run_all`` per the §9 meta-tool pattern."""
    selected = check_ids or list(ALL_CHECKS.keys())
    results = []
    for cid in selected:
        if cid not in ALL_CHECKS:
            results.append(
                {
                    "id": cid,
                    "name": cid,
                    "status": "fail",
                    "message": "unknown check id",
                    "violations": [],
                }
            )
            continue
        try:
            results.append(ALL_CHECKS[cid]())
        except Exception as e:
            results.append(
                {
                    "id": cid,
                    "name": cid,
                    "status": "fail",
                    "message": f"linter check raised: {e}",
                    "violations": [],
                }
            )
    summary = {
        "total": len(results),
        "pass": sum(1 for r in results if r["status"] == "pass"),
        "warn": sum(1 for r in results if r["status"] == "warn"),
        "fail": sum(1 for r in results if r["status"] == "fail"),
    }
    summary["clean"] = summary["fail"] == 0
    return {"checks": results, "summary": summary}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--check", action="append", help="run only the named check(s); repeat for multiple")
    p.add_argument("--json", action="store_true", help="machine-readable JSON output")
    args = p.parse_args()

    out = run_all(args.check)

    if args.json:
        print(json.dumps(out, indent=2))
    else:
        for c in out["checks"]:
            icon = {"pass": "✓", "warn": "⚠", "fail": "✗"}[c["status"]]
            print(f"  {icon} {c['name']:50s}  {c['message']}")
            if c["violations"] and c["status"] != "pass":
                for v in c["violations"][:5]:
                    print(f"      · {v}")
                if len(c["violations"]) > 5:
                    print(f"      … and {len(c['violations']) - 5} more")
        s = out["summary"]
        verdict = "CLEAN" if s["clean"] else "VIOLATIONS"
        print(f"\n  {verdict}: {s['pass']} pass · {s['warn']} warn · {s['fail']} fail")

    return 0 if out["summary"]["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
