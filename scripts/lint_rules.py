#!/usr/bin/env python3
"""lint_rules.py — automated rules-compliance checker (Phase ω.0.1).

Verifies that the project's own invariants — the ones documented in
``dev/CLAUDE_PROJECT_RULES.md`` — actually hold in the codebase. The
goal is to catch drift the moment it's introduced, rather than letting
it accumulate.

Today's checks:

  6.2  Cross-link invariant — every console links to every other.
       Reads each ``*_HTML`` constant in scripts/web.py and verifies
       its nav contains all the others.

  6.1  Canonical-order encoder — every per-book encoder must produce
       output sorted by books.yaml position, not alphabetical / not
       insertion. Verifies by running each known encoder on a small
       fixture and asserting canonical order.

  ENCODE/DECODE  Round-trip stability — for every (encode, decode)
       pair, ``decode(encode(x)) == x``.

  PARSER  No nested mappings — the project's custom YAML parser
       doesn't handle nested mappings. Scans editions.yaml for nested
       structures and flags them.

  DOCS  Cross-references — every addendum mentioned in
       ``dev/PLAN_*.md`` exists on disk; every active doc
       in ``dev/`` is mentioned somewhere.

Usage:

    python3 scripts/lint_rules.py            # run all checks
    python3 scripts/lint_rules.py --json     # machine-readable output
    python3 scripts/lint_rules.py --check 6.2  # just one check

Exits 0 on clean (all checks pass), 1 on any violation. Suitable for
a CI pre-commit gate AND for composition into the ψ.2 preflight
console (the api_preflight aggregator imports run_all() to surface
results in the buyer-demo dashboard).
"""

from __future__ import annotations

import argparse
import json
import ast  # ω.9 — AST-based atomic-writes audit
import os  # ω.18 — os.utime for the freshness fixer
import re
import subprocess  # 2026-05-29 mint guard — git-aware stray-artifact scan
import sys
import time  # ω.23 — per-check timing for the --profile flag
from pathlib import Path
from collections.abc import Callable

REPO = Path(__file__).resolve().parent.parent


# ----------------------------------------------------------------------
# Individual check implementations
# ----------------------------------------------------------------------


def check_cross_link_invariant() -> dict:
    """§6.2 — every console links to every other.

    Reads every NAME_HTML constant whose body looks like a console
    (i.e., contains a header block with nav links). Then for each
    console, verifies its nav contains a link to every other console's
    mounted route.

    Post-split (2026-05-07): constants live in scripts/templates/<name>.py
    rather than scripts/web.py. Falls back to scanning web.py if the
    templates directory doesn't exist (back-compat).
    """
    consoles: dict[str, str] = {}
    templates_dir = REPO / "scripts" / "templates"
    if templates_dir.is_dir():
        # Post-split: one constant per file in templates/.
        # ψ.14 (2026-05-08): some templates substitute HEADER_NAV_LINKS
        # at module load (single-source-of-truth nav). Import the
        # module so the linter sees the post-substitution HTML — what
        # the browser actually receives — instead of the raw source
        # with placeholder comments.
        import importlib
        import sys as _sys

        if str(REPO) not in _sys.path:
            _sys.path.insert(0, str(REPO))
        for py in sorted(templates_dir.glob("*.py")):
            if py.name in ("__init__.py", "_design.py"):
                continue
            modname = f"scripts.templates.{py.stem}"
            try:
                mod = importlib.import_module(modname)
            except Exception:
                # Fall back to raw-source regex for any module that
                # fails to import — keeps the linter robust if a
                # template has an import-time error.
                text = py.read_text(encoding="utf-8")
                for m in re.finditer(
                    r'^([A-Z_]+_HTML)\s*=\s*r"""',
                    text,
                    re.MULTILINE,
                ):
                    name = m.group(1)
                    start = m.end()
                    end = text.find('"""', start)
                    if end < 0:
                        continue
                    consoles[name] = text[start:end]
                continue
            for attr in dir(mod):
                if attr.endswith("_HTML") and isinstance(
                    getattr(mod, attr),
                    str,
                ):
                    consoles[attr] = getattr(mod, attr)
    else:
        # Pre-split fallback
        web_py = (REPO / "scripts" / "web.py").read_text(encoding="utf-8")
        for m in re.finditer(
            r'^([A-Z_]+_HTML)\s*=\s*r"""',
            web_py,
            re.MULTILINE,
        ):
            name = m.group(1)
            start = m.end()
            end = web_py.find('"""', start)
            if end < 0:
                continue
            consoles[name] = web_py[start:end]

    # The mounted routes for each *_HTML — keep this in sync with
    # the do_GET routing block. If a new console is added without
    # being included here, the linter will not catch it (chicken-egg);
    # but the SECOND check below also verifies that every newly-added
    # *_HTML has a route. For now, hardcoded mapping.
    route_for_constant = {
        "INDEX_HTML": "/",
        "MATRIX_HTML": "/matrix",
        "SOURCES_HTML": "/sources",
        "EXPORT_HTML": "/export",
        "CUSTOMIZE_HTML": "/customize",
        "AUDIT_HTML": "/audit",
        "AUDIT_LOG_HTML": "/audit-log",
        "PUBLISHER_HTML": "/publisher",
        "WIZARD_HTML": "/wizard",
        "DIFF_HTML": "/diff",
        "COVERS_HTML": "/covers",
        "PREFLIGHT_HTML": "/preflight",
        "BUILD_TRACKER_HTML": "/build-tracker",  # Ω.0 free-public pivot (2026-05-14)
        "APIHELP_HTML": "/apihelp",
        "OPS_HTML": "/ops",
        "COMPARE_HTML": "/compare",
        "HEBREW_HTML": "/hebrew",  # γ.1
        "GREEK_HTML": "/greek",  # γ.2
    }

    # Filter consoles to ones we have routes for — the editor (INDEX)
    # has a different layout (no console-style nav) and is exempt.
    expected_routes = [r for c, r in route_for_constant.items() if c in consoles and c != "INDEX_HTML"]

    # Per project convention, the nav link to the matrix cluster
    # uses href="/" (the editor route) with display text "matrix".
    # This is pre-existing technical debt: the link text promises
    # /matrix but the href goes to the editor. Cleanup tracked in
    # SESSION_STATE in-flight notes; for now the linter treats "/"
    # as an accepted alias for /matrix so it doesn't false-flag
    # every console.
    matrix_aliases = {"/", "/matrix"}

    violations: list[dict] = []
    for name, body in consoles.items():
        if name == "INDEX_HTML":
            continue  # exempt — different layout
        my_route = route_for_constant.get(name)
        if not my_route:
            # Console exists but no route mapping — missing from the
            # table above. Treat as a violation so the linter forces
            # the table to be updated.
            violations.append(
                {
                    "console": name,
                    "issue": "no route mapping in lint_rules.py",
                }
            )
            continue
        for r in expected_routes:
            if r == my_route:
                continue  # self-link is via active-page span, not nav
            # If checking the matrix route, accept either "/" or "/matrix"
            if r == "/matrix":
                if not any(f'"{a}"' in body or f"'{a}'" in body for a in matrix_aliases):
                    violations.append(
                        {
                            "console": name,
                            "missing_link_to": "/matrix or /",
                        }
                    )
                continue
            # Check for the link. Accept either href="r" or href='r'.
            if f'"{r}"' not in body and f"'{r}'" not in body:
                violations.append(
                    {
                        "console": name,
                        "missing_link_to": r,
                    }
                )

    return {
        "id": "6.2",
        "name": "Cross-link invariant",
        "status": "fail" if violations else "pass",
        "message": (
            f"{len(violations)} missing cross-links across {len(consoles) - 1} consoles"
            if violations
            else f"all {len(consoles) - 1} consoles cross-link to each other"
        ),
        "violations": violations,
    }


def check_encoder_canonical_order() -> dict:
    """§6.1 — every per-book encoder produces canonical-order output.

    Imports the encoders by name and runs them on a small unsorted
    fixture; verifies the output is sorted by books.yaml position,
    not by code order.
    """
    sys.path.insert(0, str(REPO))
    from scripts.core import config

    book_order = list(config.books_by_code().keys())
    rank = {code: i for i, code in enumerate(book_order)}

    # (module_path, encoder_name) pairs to check
    encoders = [
        ("scripts.build_edition", "encode_per_book_languages"),
        ("scripts.build_edition", "encode_per_book_traditions"),
        ("scripts.core.covers", "encode_book_covers"),
    ]

    violations: list[dict] = []
    for mod_name, fn_name in encoders:
        try:
            mod = __import__(mod_name, fromlist=[fn_name])
            fn = getattr(mod, fn_name)
        except (ImportError, AttributeError) as e:
            violations.append(
                {
                    "encoder": f"{mod_name}.{fn_name}",
                    "issue": f"could not import: {e}",
                }
            )
            continue
        # Pick three book codes in deliberately non-canonical order.
        # Canonical order has `gen` (very early) and `mat` (NT, late).
        # We add `tob` from the Apocrypha which sits between OT and NT
        # in the project's 87-book superset.
        if fn_name == "encode_per_book_languages":
            sample = {"mat": ["english"], "tob": ["english"], "gen": ["english"]}
        elif fn_name == "encode_per_book_traditions":
            sample = {"mat": ["catholic"], "tob": ["cross"], "gen": ["protestant"]}
        else:
            sample = {"mat": "x", "tob": "y", "gen": "z"}
        try:
            encoded = fn(sample)
        except Exception as e:
            violations.append(
                {
                    "encoder": f"{mod_name}.{fn_name}",
                    "issue": f"raised on sample input: {e}",
                }
            )
            continue
        codes = [s.split("=")[0] for s in encoded]
        expected = sorted(codes, key=lambda c: rank.get(c, len(book_order)))
        if codes != expected:
            violations.append(
                {
                    "encoder": f"{mod_name}.{fn_name}",
                    "got_order": codes,
                    "expected_order": expected,
                }
            )

    return {
        "id": "6.1",
        "name": "Canonical-order encoders",
        "status": "fail" if violations else "pass",
        "message": (
            f"{len(violations)} encoder(s) produce non-canonical order"
            if violations
            else f"all {len(encoders)} encoders produce canonical order"
        ),
        "violations": violations,
    }


def check_encode_decode_round_trip() -> dict:
    """Every (encode, decode) pair should round-trip cleanly."""
    sys.path.insert(0, str(REPO))
    pairs = [
        (
            "scripts.build_edition",
            "encode_per_book_languages",
            "decode_per_book_languages",
            {"gen": ["english", "hebrew"], "mat": ["english"], "tob": []},
        ),
        (
            "scripts.build_edition",
            "encode_per_book_traditions",
            "decode_per_book_traditions",
            {"gen": ["catholic", "cross"], "mat": ["protestant"], "tob": []},
        ),
        (
            "scripts.core.covers",
            "encode_book_covers",
            "decode_book_covers",
            {"gen": "covers/x/gen.jpg", "mat": "covers/x/mat.png", "tob": ""},
        ),
    ]
    violations: list[dict] = []
    for mod_name, enc_name, dec_name, sample in pairs:
        try:
            mod = __import__(mod_name, fromlist=[enc_name, dec_name])
            enc = getattr(mod, enc_name)
            dec = getattr(mod, dec_name)
        except (ImportError, AttributeError) as e:
            violations.append({"pair": f"{enc_name}/{dec_name}", "issue": str(e)})
            continue
        try:
            recovered = dec(enc(sample))
        except Exception as e:
            violations.append({"pair": f"{enc_name}/{dec_name}", "issue": f"raised: {e}"})
            continue
        if recovered != sample:
            violations.append(
                {
                    "pair": f"{enc_name}/{dec_name}",
                    "input": sample,
                    "round_tripped": recovered,
                }
            )

    return {
        "id": "encode_decode",
        "name": "Encoder/decoder round trip",
        "status": "fail" if violations else "pass",
        "message": (
            f"{len(violations)} pairs do not round-trip cleanly"
            if violations
            else f"all {len(pairs)} encode/decode pairs round-trip"
        ),
        "violations": violations,
    }


def check_doc_cross_references() -> dict:
    """Every SCOPE addendum referenced in the live PLAN / SESSION_STATE exists on
    disk **live OR in dev/archive/** (archive-aware — 2026-05-29 mint Task 0.6, so
    the Phase-3 sweep can move docs without stranding their references); every
    LIVE (non-archived) SCOPE addendum is referenced somewhere. Also validates
    that ``dev/*.md`` links cited in the PLAN / SESSION_STATE / SECURITY / README
    resolve (live or archived) — catches dangling pointers.

    Auto-discovers the active PLAN by picking the lexicographically latest
    ``dev/PLAN_*.md``. Falls back to PLAN_2026-05-07 if none is present.
    """
    dev = REPO / "dev"

    def _read(p: Path) -> str:
        return p.read_text(encoding="utf-8") if p.is_file() else ""

    plan_files = sorted(dev.glob("PLAN_*.md"))
    plan_path = plan_files[-1] if plan_files else (dev / "PLAN_2026-05-07.md")
    referenced_text = _read(plan_path) + "\n" + _read(dev / "SESSION_STATE.md")

    # Every "dev/SCOPE_..." reference in the PLAN+SESSION.
    referenced = set(re.findall(r"dev/SCOPE_[A-Za-z0-9_\-]+\.md", referenced_text))

    # Actual SCOPE files: LIVE (dev/ top level) + archived (dev/archive/** — by
    # bare name, so a reference by bare name still resolves after the sweep).
    actual_live = {f"dev/{p.name}" for p in dev.glob("SCOPE_*.md")}
    archived_names = {p.name for p in dev.rglob("SCOPE_*.md")} - {Path(a).name for a in actual_live}

    violations: list[dict] = []
    for ref in sorted(referenced):
        bare = ref.split("/")[-1]
        if ref not in actual_live and bare not in archived_names:
            violations.append({"issue": "referenced but missing (live or archive)", "doc": ref})
    for f in sorted(actual_live - referenced):
        violations.append({"issue": "live but not referenced (archive candidate)", "doc": f})

    # Dangling intra-repo dev/*.md links cited in the key docs.
    link_text = "\n".join(
        _read(p) for p in (plan_path, dev / "SESSION_STATE.md", dev / "SECURITY.md", REPO / "README.md")
    )
    archive_dir = dev / "archive"
    for c in sorted(set(re.findall(r"dev/[A-Za-z0-9_\-/]+\.md", link_text))):
        bare = c.split("/")[-1]
        live_ok = (REPO / c).is_file()
        archive_ok = archive_dir.is_dir() and any(archive_dir.rglob(bare))
        if not live_ok and not archive_ok:
            violations.append({"issue": "dangling dev/ link", "doc": c})

    return {
        "id": "docs",
        "name": "Documentation cross-references",
        "status": "warn" if violations else "pass",
        "message": (
            f"{len(violations)} doc reference issue(s)"
            if violations
            else f"all {len(actual_live)} live scope addenda referenced consistently"
        ),
        "violations": violations[:40],
    }


def check_session_state_freshness() -> dict:
    """SESSION_STATE.md should be no more than ~1 day stale relative
    to the most recent CHANGELOG entry. A larger gap suggests the
    continuity protocol (Rule §11) has slipped."""
    changelog = REPO / "dev" / "CHANGELOG.md"
    session = REPO / "dev" / "SESSION_STATE.md"
    if not changelog.exists() or not session.exists():
        return {
            "id": "freshness",
            "name": "SESSION_STATE freshness",
            "status": "warn",
            "message": "missing CHANGELOG or SESSION_STATE",
            "violations": [],
        }
    # Cheap heuristic: compare mtime
    cl_mtime = changelog.stat().st_mtime
    ss_mtime = session.stat().st_mtime
    delta = abs(cl_mtime - ss_mtime)
    # If they're more than 6h apart, flag a warn — likely SESSION_STATE
    # was forgotten on a session that updated CHANGELOG (or vice versa)
    if delta > 6 * 3600:
        return {
            "id": "freshness",
            "name": "SESSION_STATE freshness",
            "status": "warn",
            "message": (f"CHANGELOG and SESSION_STATE diverge by {int(delta / 3600)} hours"),
            "violations": [
                {
                    "changelog_mtime": cl_mtime,
                    "session_state_mtime": ss_mtime,
                }
            ],
        }
    return {
        "id": "freshness",
        "name": "SESSION_STATE freshness",
        "status": "pass",
        "message": "CHANGELOG and SESSION_STATE updated together",
        "violations": [],
    }


# ----------------------------------------------------------------------
# Drift-catching checks (Tier 3 — added 2026-05-07 after a real drift
# event). These exist specifically to detect the failure mode where
# code ships but documentation doesn't, OR where a task is started
# but never closed. Each surfaces in /preflight as an actionable
# warning.
# ----------------------------------------------------------------------


def check_inflight_freshness() -> dict:
    """If `dev/IN_FLIGHT.md` declares an in-flight task, that task
    must be either freshly opened (< 4 hours) OR have a corresponding
    CHANGELOG entry mtime within the same window. Otherwise the task
    is likely orphaned.

    Reads the machine-readable marker at the top of IN_FLIGHT.md:
        <!-- TRACKER-STATE: idle -->     no in-flight task
        <!-- TRACKER-STATE: active -->   in-flight task declared

    Using an HTML-comment marker means prose elsewhere in the file
    can mention "active" or "idle" without collision.
    """
    path = REPO / "dev" / "IN_FLIGHT.md"
    if not path.exists():
        return {
            "id": "inflight_freshness",
            "name": "In-flight task tracker",
            "status": "warn",
            "message": "dev/IN_FLIGHT.md does not exist",
            "violations": [{"missing": "dev/IN_FLIGHT.md"}],
        }
    text = path.read_text(encoding="utf-8")
    marker_match = re.search(r"<!--\s*TRACKER-STATE:\s*(idle|active)\s*-->", text)
    if not marker_match:
        return {
            "id": "inflight_freshness",
            "name": "In-flight task tracker",
            "status": "warn",
            "message": ("IN_FLIGHT.md has no <!-- TRACKER-STATE: ... --> marker; cannot determine state"),
            "violations": [],
        }
    state = marker_match.group(1)
    if state == "idle":
        return {
            "id": "inflight_freshness",
            "name": "In-flight task tracker",
            "status": "pass",
            "message": "no in-flight task; tracker is idle",
            "violations": [],
        }
    # state == "active": compare mtime against CHANGELOG mtime.
    import time

    inflight_mtime = path.stat().st_mtime
    changelog = REPO / "dev" / "CHANGELOG.md"
    cl_mtime = changelog.stat().st_mtime if changelog.exists() else 0
    age_hours = (time.time() - inflight_mtime) / 3600.0
    if cl_mtime > inflight_mtime:
        return {
            "id": "inflight_freshness",
            "name": "In-flight task tracker",
            "status": "warn",
            "message": (
                "IN_FLIGHT marker is 'active' but CHANGELOG has "
                "been updated since — task probably shipped; "
                "reset marker to idle"
            ),
            "violations": [
                {
                    "inflight_mtime": inflight_mtime,
                    "changelog_mtime": cl_mtime,
                }
            ],
        }
    if age_hours > 4:
        return {
            "id": "inflight_freshness",
            "name": "In-flight task tracker",
            "status": "fail",
            "message": (f"in-flight task is {age_hours:.1f}h old with no CHANGELOG update — likely orphaned"),
            "violations": [{"age_hours": round(age_hours, 1)}],
        }
    return {
        "id": "inflight_freshness",
        "name": "In-flight task tracker",
        "status": "pass",
        "message": f"in-flight task active for {age_hours:.1f}h (fresh)",
        "violations": [],
    }


# Phases that shipped before the CHANGELOG existed (CHANGELOG was
# created on 2026-05-07). These appear as comments in source files
# but predate the editorial journal — backfilled into the CHANGELOG's
# "Pre-session-2026-05-07 history" section as a chronological summary
# rather than per-phase entries. Allowlist them so the untracked-
# phases check doesn't fire on legacy code.
LEGACY_PHASES_PRE_CHANGELOG = {
    "β.1",
    "β.2",  # phase β early infrastructure
    "ν.2.5",  # mid-ν customization (pre-popup-langs)
    "ξ.5",  # ξ sales tool extensions
    "τ.1",
    "τ.1.5",  # KJV translation extractor + per-edition picker
    "α.1",  # earliest setup
    "γ.1",
    "γ.2",  # any other early ones
    "δ.1",
    "δ.2",
    "ε.1",
    "ζ.1",
    "η.2",
    "η.3",
}


# Phase mention pattern. Matches greek-letter phase tags as used
# throughout this codebase (ν.6.1, π.4-B, ω.0.1, etc.). Only catches
# letter+digit forms; arbitrary letters or words won't match.
_PHASE_RE = re.compile(
    r"(?<![A-Za-z])"  # not preceded by a letter
    r"([νπωψχφυσρτθικλμηξζεδγβα])"  # any greek lowercase
    r"\.\d+"  # mandatory .N
    r"(?:\.\d+|\.[A-Za-z](?:\.\d+)?|-[A-Za-z](?:\.\d+)?)?"  # optional .N / .X / -A.N
)


def check_untracked_phases() -> dict:
    """Every Phase letter mentioned in production code (scripts/,
    tests/) should appear in `dev/CHANGELOG.md`. A phase mentioned
    in code but not in CHANGELOG is the canonical drift signature
    — code shipped, doc forgotten.

    Allowlist: `LEGACY_PHASES_PRE_CHANGELOG` covers phases that
    shipped before the editorial journal existed. Their canonical
    record is git history + the backfilled summary in CHANGELOG.md;
    individual mentions don't need to round-trip.
    """
    code_phases: set[str] = set()
    for sub in ("scripts", "tests"):
        d = REPO / sub
        if not d.exists():
            continue
        for f in d.rglob("*.py"):
            # Skip lint_rules.py itself — its own example strings
            # and the legacy allowlist would self-trigger
            if f.name == "lint_rules.py":
                continue
            try:
                text = f.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for m in _PHASE_RE.finditer(text):
                phase = m.group(0)
                if phase not in LEGACY_PHASES_PRE_CHANGELOG:
                    code_phases.add(phase)

    changelog_path = REPO / "dev" / "CHANGELOG.md"
    if not changelog_path.exists():
        return {
            "id": "untracked_phases",
            "name": "Phase mentions tracked in CHANGELOG",
            "status": "warn",
            "message": "dev/CHANGELOG.md missing",
            "violations": [],
        }
    changelog_text = changelog_path.read_text(encoding="utf-8")
    untracked = sorted(p for p in code_phases if p not in changelog_text)
    if not untracked:
        return {
            "id": "untracked_phases",
            "name": "Phase mentions tracked in CHANGELOG",
            "status": "pass",
            "message": (f"all {len(code_phases)} non-legacy phase mention(s) in code appear in CHANGELOG.md"),
            "violations": [],
        }
    return {
        "id": "untracked_phases",
        "name": "Phase mentions tracked in CHANGELOG",
        "status": "warn",
        "message": (f"{len(untracked)} phase(s) mentioned in code but not in CHANGELOG — likely undocumented ship"),
        "violations": [{"phase": p} for p in untracked[:20]],
    }


def check_session_state_inventory() -> dict:
    """SESSION_STATE.md's inventory pointers section should mention
    every *_HTML console constant in `scripts/web.py`. Top-level
    utility scripts are NOT enforced — the inventory is a curated
    "where things live" guide, not an exhaustive file list.

    Drift signal: a new console (which means a new user-facing
    feature surface) shipped without being added to the inventory.
    """
    state_path = REPO / "dev" / "SESSION_STATE.md"
    if not state_path.exists():
        return {
            "id": "code_doc_sync",
            "name": "SESSION_STATE inventory matches consoles",
            "status": "warn",
            "message": "dev/SESSION_STATE.md missing",
            "violations": [],
        }
    state = state_path.read_text(encoding="utf-8")

    # Post-split (2026-05-07): constants live in scripts/templates/<name>.py.
    # Pre-split fallback: scripts/web.py.
    templates_dir = REPO / "scripts" / "templates"
    html_constants: list[str] = []
    if templates_dir.is_dir():
        for py in sorted(templates_dir.glob("*.py")):
            if py.name == "__init__.py":
                continue
            text = py.read_text(encoding="utf-8")
            html_constants.extend(re.findall(r"^([A-Z_]+_HTML)\s*=\s*r\"\"\"", text, re.MULTILINE))
    else:
        web_py = (REPO / "scripts" / "web.py").read_text(encoding="utf-8")
        html_constants = re.findall(r"^([A-Z_]+_HTML)\s*=\s*r\"\"\"", web_py, re.MULTILINE)
    # Editor (INDEX_HTML) is exempt — it's the original /, predates
    # the consoles concept, and is intentionally not surfaced as a
    # "console" in the inventory.
    html_constants = [c for c in html_constants if c != "INDEX_HTML"]
    missing_consoles = []
    for c in html_constants:
        # Generous: either the constant name OR its lowercase route
        # name appears somewhere in SESSION_STATE
        route_name = c.replace("_HTML", "").lower()
        if c not in state and f"/{route_name}" not in state:
            missing_consoles.append(c)

    if not missing_consoles:
        return {
            "id": "code_doc_sync",
            "name": "SESSION_STATE inventory matches consoles",
            "status": "pass",
            "message": (f"SESSION_STATE references all {len(html_constants)} consoles"),
            "violations": [],
        }
    return {
        "id": "code_doc_sync",
        "name": "SESSION_STATE inventory matches consoles",
        "status": "warn",
        "message": (f"{len(missing_consoles)} console(s) not in inventory"),
        "violations": [{"missing_console": c} for c in missing_consoles],
    }


def _find_open_write_calls(tree: ast.AST) -> list[int]:
    """Walk a parsed module AST and return the line numbers of every
    `open(..., 'w'|'wb'|'w+'|'wt'|'wx')` call. AST-based to avoid the
    whole class of false positives that string-matching against
    docstrings and comments produces."""
    hits: list[int] = []

    class Finder(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            f = node.func
            is_open = (isinstance(f, ast.Name) and f.id == "open") or (
                isinstance(f, ast.Attribute) and f.attr == "open"
            )
            if is_open:
                # Look at every positional arg AND the `mode=` kwarg
                # for a string literal starting with 'w'.
                candidates = []
                candidates.extend(node.args)
                for kw in node.keywords:
                    if kw.arg == "mode":
                        candidates.append(kw.value)
                for c in candidates:
                    v = c.value if isinstance(c, ast.Constant) else None
                    if isinstance(v, str) and v.startswith("w"):
                        hits.append(node.lineno)
                        break
            self.generic_visit(node)

    Finder().visit(tree)
    return hits


def _find_urlopen_calls(tree: ast.AST) -> list[int]:
    """Return line numbers of any `urllib.request.urlopen(...)` or
    `urlopen(...)` (when imported directly) call in the AST."""
    hits: list[int] = []

    class Finder(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            f = node.func
            is_urlopen = False
            if isinstance(f, ast.Attribute) and f.attr == "urlopen" or isinstance(f, ast.Name) and f.id == "urlopen":
                is_urlopen = True
            if is_urlopen:
                hits.append(node.lineno)
            self.generic_visit(node)

    Finder().visit(tree)
    return hits


# ω.23.1 — shared read+parse cache for the two AST-walk checks
# (`check_atomic_writes` + `check_external_http`). Both glob the
# same scripts/ tree; before this cache they each did the same read
# and the same ast.parse. Profile (ω.23) showed the duplication
# was ~87% of total lint wall time. Cache is module-level rather
# than functools.lru_cache because we need an explicit clear hook
# for run_all() to call between back-to-back invocations.
_PARSE_CACHE: dict[str, tuple[ast.Module | None, list[str]]] = {}


def _load_parsed_python(
    path: Path,
) -> tuple[ast.Module | None, list[str]]:
    """Read + parse a Python file, returning ``(tree, lines)``.

    Returns ``(None, [])`` on read failure (`UnicodeDecodeError`,
    `OSError`) or parse failure (`SyntaxError`). The two checks
    that consume this both want both pieces — `tree` for the AST
    walk + `lines` for waiver-comment detection — so we cache the
    pair together to avoid splitting files between calls.

    Memoised on the resolved path string so the same file accessed
    via different `Path` instances still hits.
    """
    key = str(path.resolve())
    if key in _PARSE_CACHE:
        return _PARSE_CACHE[key]
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        _PARSE_CACHE[key] = (None, [])
        return _PARSE_CACHE[key]
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        _PARSE_CACHE[key] = (None, [])
        return _PARSE_CACHE[key]
    _PARSE_CACHE[key] = (tree, text.splitlines())
    return _PARSE_CACHE[key]


def _clear_parse_cache() -> None:
    """Drop the AST cache. Called at the top of `run_all()` so a
    second invocation re-reads the tree on disk — important for
    tests that mutate fixtures between calls and for any future
    long-running consumer (a server that calls `run_all()` repeatedly
    after edits)."""
    _PARSE_CACHE.clear()


def check_external_http() -> dict:
    """Phase ω.10 — every outbound HTTP call must go through the
    retry+timeout wrapper at `scripts/core/http.py`. Raw
    `urllib.request.urlopen` calls outside that file get flagged.

    Drift signal: a future fetcher (LibriVox audio for ρ.1, or one
    of the χ.2-5 commentary ingestors) hits the network without
    inheriting the retry/timeout policy and a transient blip silently
    fails.

    Same waiver mechanism as ω.9: `# http-waived: <reason>` on the
    same or preceding line opts a call site out.
    """
    violations: list[dict] = []
    scripts_dir = REPO / "scripts"
    for py in scripts_dir.rglob("*.py"):
        # http.py itself wraps urlopen — that's the documented
        # exception.
        if py.name == "http.py" and py.parent.name == "core":
            continue
        # ω.23.1 — shared with check_atomic_writes via _PARSE_CACHE.
        tree, lines = _load_parsed_python(py)
        if tree is None:
            continue
        for ln in _find_urlopen_calls(tree):
            same = lines[ln - 1] if 0 < ln <= len(lines) else ""
            prev = lines[ln - 2] if 1 < ln <= len(lines) else ""
            if "http-waived" in same or "http-waived" in prev:
                continue
            violations.append(
                {
                    "file": str(py.relative_to(REPO)).replace("\\", "/"),
                    "line": ln,
                    "snippet": same.strip()[:120],
                }
            )

    if not violations:
        return {
            "id": "external_http",
            "name": "External HTTP (no raw urlopen outside core/http.py)",
            "status": "pass",
            "message": "no raw urlopen() outside scripts/core/http.py",
            "violations": [],
        }
    return {
        "id": "external_http",
        "name": "External HTTP (no raw urlopen outside core/http.py)",
        "status": "fail",
        "message": (
            f"{len(violations)} raw urlopen() call site(s) outside "
            f"scripts/core/http.py — use the retry+timeout wrapper or "
            f"add `# http-waived: <reason>` to opt out"
        ),
        "violations": violations,
    }


def check_atomic_writes() -> dict:
    """Phase ω.9 — every direct write-mode open() call site outside
    `scripts/core/notes_io.py` is suspect.

    Atomic writes go through `notes_io.atomic_write` /
    `atomic_write_bytes`; a raw write-mode open() cannot be crash-
    safe because a crash between the truncate and the final flush
    leaves the file half-written. Build-pipeline scratch directories
    (epub_working/, /tmp/) are exempt because they're regenerable.

    The check currently passes with zero violations; this is a
    drift-prevention lock-in.

    Implementation note: AST-based detection (not regex) so the
    check doesn't match its own docstring or the literal strings
    in surrounding code that *describe* the bug.
    """
    violations: list[dict] = []
    scripts_dir = REPO / "scripts"
    for py in scripts_dir.rglob("*.py"):
        # notes_io.py is THE place atomic_write/atomic_write_bytes
        # live; they themselves use open('wb') under the hood —
        # that's the documented exception.
        if py.name == "notes_io.py":
            continue
        # ω.23.1 — shared with check_external_http via _PARSE_CACHE.
        # Files with read or parse failures return (None, []); the
        # check skips them silently the same way the inline read+parse
        # used to.
        tree, lines = _load_parsed_python(py)
        if tree is None:
            continue
        for ln in _find_open_write_calls(tree):
            # Waiver: `# atomic-waived: <reason>` on the same line
            # OR the immediately preceding line.
            same = lines[ln - 1] if 0 < ln <= len(lines) else ""
            prev = lines[ln - 2] if 1 < ln <= len(lines) else ""
            if "atomic-waived" in same or "atomic-waived" in prev:
                continue
            violations.append(
                {
                    "file": str(py.relative_to(REPO)).replace("\\", "/"),
                    "line": ln,
                    "snippet": same.strip()[:120],
                }
            )

    if not violations:
        return {
            "id": "atomic_writes",
            "name": "Atomic writes (no raw open('w') outside notes_io)",
            "status": "pass",
            "message": "no raw write-mode open() outside notes_io.py",
            "violations": [],
        }
    return {
        "id": "atomic_writes",
        "name": "Atomic writes (no raw open('w') outside notes_io)",
        "status": "fail",
        "message": (
            f"{len(violations)} raw write-mode open() call site(s) "
            f"outside notes_io.py — use atomic_write/atomic_write_bytes "
            f"or add `# atomic-waived: <reason>` to opt out"
        ),
        "violations": violations,
    }


def check_render_coverage_no_regression() -> dict:
    """Audit 2026-05-20 — render-coverage regression detector.

    Pins that books rendered today in ``content/translations/geez-
    tewahedo/`` and ``amharic-tewahedo/`` stay rendered tomorrow. A book
    file disappearing is a fail; new books appearing is silent (the
    expected direction of change).

    Baseline = 2026-05-20 audit-U-belt snapshot. When a new book is
    rendered, ADD its code to the relevant set; never SHRINK the
    expected sets.
    """
    expected_geez = {
        # τ.6.x.5.x Patrologia Orientalis track (printed bilingual Ge'ez+
        # French critical editions) + τ.6.x.NT.c NT pre-pass — all rendered
        # AFTER the 2026-05-20 baseline below.
        "1ch",  # τ.6.x.5.x — Patrologia Orientalis
        "2ch",  # τ.6.x.5.x — Patrologia Orientalis
        "ezr",  # τ.6.x.5.x — Patrologia Orientalis
        "neh",  # τ.6.x.5.x — Patrologia Orientalis
        "job",  # τ.6.x.5.x — Patrologia Orientalis
        "mat",  # τ.6.x.NT.c — NT pre-pass (honest ocr-tier3 partial)
        "1en",  # τ.6.x.2.u — FINAL book of OT catchup queue (2026-05-20)
        "2es",
        "4ba",  # τ.6.x.2.p
        "bar",  # τ.6.x.2.q
        "bel",  # τ.6.x.2.s
        "deu",
        "est",
        "ex",
        "gen",
        "jdg",
        "jdt",
        "jos",
        "jub",  # τ.6.x.2.t
        "jud",  # τ.6.x.NT.a
        "lev",
        "mq1",
        "mq2",
        "mq3",
        "num",
        "paz",  # τ.6.x.2.s
        "phm",  # τ.6.x.NT.a
        "psa",
        "rut",
        "sir",  # τ.6.x.2.o
        "tob",
        "wis",  # τ.6.x.2.r
    }
    expected_amharic = {
        "mat",  # τ.6.x.NT.c — NT pre-pass (honest ocr-tier3 partial)
        "1en",
        "2es",
        "4ba",
        "bar",
        "bel",
        "deu",
        "est",
        "ex",
        "gen",
        "jdg",
        "jdt",
        "jos",
        "jub",
        "jud",  # τ.6.x.NT.a
        "lev",
        "mq1",
        "mq2",
        "mq3",
        "num",
        "paz",
        "phm",  # τ.6.x.NT.a
        "psa",
        "rut",
        "sir",
        "tob",
        "wis",
    }
    base = REPO / "content" / "translations"
    violations: list[dict] = []
    for edition, expected in (
        ("geez-tewahedo", expected_geez),
        ("amharic-tewahedo", expected_amharic),
    ):
        ed_dir = base / edition
        if not ed_dir.is_dir():
            violations.append(
                {
                    "edition": edition,
                    "missing": sorted(expected),
                    "note": "edition directory missing entirely",
                }
            )
            continue
        actual = {p.stem for p in ed_dir.glob("*.py") if not p.stem.startswith("_")}
        missing = expected - actual
        if missing:
            violations.append(
                {
                    "edition": edition,
                    "missing": sorted(missing),
                    "note": "books regressed (file no longer present)",
                }
            )

    if not violations:
        return {
            "id": "render_coverage",
            "name": "Render-coverage no-regression",
            "status": "pass",
            "message": (
                f"geez-tewahedo {len(expected_geez)} + amharic-tewahedo "
                f"{len(expected_amharic)} expected books all present"
            ),
            "violations": [],
        }
    return {
        "id": "render_coverage",
        "name": "Render-coverage no-regression",
        "status": "fail",
        "message": "rendered book(s) regressed — restore from git history before committing",
        "violations": violations,
    }


def check_provenance_tier_known() -> dict:
    """Audit 2026-05-20 — every committed rendered book's SOURCE_QUALITY
    must be a known provenance tier per
    ``scripts.core.provenance_tiers.TIERS``.

    Catches: typos in SOURCE_QUALITY strings; new tier names that
    weren't registered; render scripts that forgot to set the field.
    """
    from scripts.core.provenance_tiers import is_known_tier

    base = REPO / "content" / "translations"
    violations: list[dict] = []
    files_checked = 0
    pattern = re.compile(r'SOURCE_QUALITY\s*=\s*["\']([^"\']+)["\']')
    for edition in ("geez-tewahedo", "amharic-tewahedo"):
        ed_dir = base / edition
        if not ed_dir.is_dir():
            continue
        for py in sorted(ed_dir.glob("*.py")):
            if py.stem.startswith("_"):
                continue
            files_checked += 1
            try:
                text = py.read_text(encoding="utf-8")
            except Exception:
                continue
            m = pattern.search(text)
            if not m:
                violations.append(
                    {
                        "file": str(py.relative_to(REPO)).replace("\\", "/"),
                        "error": "no SOURCE_QUALITY declaration found",
                    }
                )
                continue
            tier = m.group(1)
            if not is_known_tier(tier):
                violations.append(
                    {
                        "file": str(py.relative_to(REPO)).replace("\\", "/"),
                        "error": f"unknown tier {tier!r} (register in scripts.core.provenance_tiers.TIERS)",
                    }
                )

    if not violations:
        return {
            "id": "provenance_tier",
            "name": "Provenance-tier known",
            "status": "pass",
            "message": f"all {files_checked} rendered books declare known tiers",
            "violations": [],
        }
    return {
        "id": "provenance_tier",
        "name": "Provenance-tier known",
        "status": "fail",
        "message": (f"{len(violations)}/{files_checked} rendered book(s) have unknown or missing SOURCE_QUALITY"),
        "violations": violations,
    }


def check_manuscript_witnesses_valid() -> dict:
    """Audit U-belt — every committed witness JSON under
    ``content/manuscript/*/calibration/`` must pass ``validate_witness``.

    Belt-and-suspenders beyond the canonical writer (``write_witness``):
    a direct edit to a witness JSON that drifts from the canonical
    schema (custom uncertain markers, ``✣`` in tokens, extra top-level
    keys, illegible-bijection violations) is silent until the at-scale
    driver or a downstream consumer hits it. This check makes that
    drift a pre-commit failure.

    The 1Ki4 schema-rot incident (08 review markers + ✣ tokens that
    needed a one-shot driver to collate) was exactly this drift class.
    After write_witness shipped + 1Ki4 was migrated, this check pins
    the canonical-schema invariant for the future.
    """
    import json as _json
    from scripts.core.manuscript_records import validate_witness

    cal_glob = REPO / "content" / "manuscript"
    violations: list[dict] = []
    files_checked = 0
    for witness_path in sorted(cal_glob.glob("*/calibration/*_witness*.json")):
        files_checked += 1
        try:
            d = _json.loads(witness_path.read_text(encoding="utf-8"))
        except Exception as e:
            violations.append(
                {
                    "file": str(witness_path.relative_to(REPO)).replace("\\", "/"),
                    "error": f"unreadable: {e}",
                }
            )
            continue
        ok, errs = validate_witness(d)
        if not ok:
            violations.append(
                {
                    "file": str(witness_path.relative_to(REPO)).replace("\\", "/"),
                    "error": "; ".join(errs[:5]) + ("; …" if len(errs) > 5 else ""),
                }
            )

    if not violations:
        return {
            "id": "manuscript_witnesses",
            "name": "Manuscript witnesses canonical-schema",
            "status": "pass",
            "message": f"all {files_checked} committed witness JSON(s) validate ok=True",
            "violations": [],
        }
    return {
        "id": "manuscript_witnesses",
        "name": "Manuscript witnesses canonical-schema",
        "status": "fail",
        "message": (
            f"{len(violations)}/{files_checked} witness JSON(s) fail "
            "validate_witness — use scripts.core.manuscript_records."
            "write_witness() to write witnesses (it derives canonical "
            "tokens + validates before writing)"
        ),
        "violations": violations,
    }


# ----------------------------------------------------------------------
# Runner
# ----------------------------------------------------------------------


def check_plan_coherence() -> dict:
    """ω.15 — compose scripts.lint_plan.run_all() into the master
    rules check. Surfaces plan/CHANGELOG/Depends drift alongside
    the existing 10 invariant checks per the §9 meta-tool pattern.

    Folds the four sub-checks (plan_singular, plan_shipped,
    plan_open, plan_depends) into one rolled-up status: fail if any
    sub-check fails, warn if any warns, pass otherwise.
    """
    try:
        from scripts import lint_plan
    except ImportError as e:
        return {
            "id": "plan_coherence",
            "name": "Plan coherence (ω.15 sub-tool)",
            "status": "warn",
            "message": f"lint_plan import failed: {e}",
            "violations": [],
        }
    try:
        sub = lint_plan.run_all()
    except Exception as e:
        return {
            "id": "plan_coherence",
            "name": "Plan coherence (ω.15 sub-tool)",
            "status": "warn",
            "message": f"lint_plan raised: {e}",
            "violations": [],
        }
    summary = sub.get("summary", {})
    if summary.get("fail", 0) > 0:
        rolled_status = "fail"
    elif summary.get("warn", 0) > 0:
        rolled_status = "warn"
    else:
        rolled_status = "pass"
    violations = []
    for c in sub.get("checks", []):
        if c.get("status") != "pass":
            violations.append(
                {
                    "sub_check": c.get("id"),
                    "status": c.get("status"),
                    "message": c.get("message"),
                }
            )
    msg = (
        f"{summary.get('pass', 0)}/{summary.get('total', 0)} sub-checks pass"
        if rolled_status != "pass"
        else f"all {summary.get('total', 0)} sub-checks pass (plan_singular, plan_shipped, plan_open, plan_depends)"
    )
    return {
        "id": "plan_coherence",
        "name": "Plan coherence (PLAN ↔ CHANGELOG ↔ Depends)",
        "status": rolled_status,
        "message": msg,
        "violations": violations,
    }


# Repo-root-relative path prefixes for the REPO_MAP reverse-path check. Only
# tokens that START with one of these are validated, so section-relative
# citations (META-INF/container.xml, core/config.py, …) don't false-positive.
_REPO_MAP_TOP_PREFIXES = (
    "content/",
    "scripts/",
    "dev/",
    "tests/",
    "epub_working/",
    "docs/",
    "exports/",
    "assets/",
    "GAPS/",
    "project_maccabees_expansion/",
)


def check_repo_map_complete() -> dict:
    """(1) Every non-hidden top-level dir is documented in dev/REPO_MAP.md; (2) every
    backtick-quoted repo-root-relative path cited in the map still resolves on disk
    (reverse-path drift — 2026-05-29 mint Task 0.7). Anti-rot mirror of
    dev/trace_repo.py. Ships WARN; Phase 5 regenerates REPO_MAP post-deletion and
    flips ``_ENFORCE_REPO_MAP`` so drift/missing becomes a hard FAIL.

    Reverse-path validation is intentionally limited to tokens beginning with a
    known top-level dir, and skips glob/placeholder tokens (``*``, ``<>``, ``{}``,
    ``..``), so the freeform prose counts + section-relative paths in the map can't
    produce false positives. (Brittle prose-COUNT parsing is deliberately NOT
    attempted — path-existence drift is the robust, false-positive-free signal.)"""
    repo_map = REPO / "dev" / "REPO_MAP.md"
    skip = {
        ".git",
        "__pycache__",
        "node_modules",
        ".backups",
        ".pytest_cache",
        ".venv",
        "venv",
        ".ruff_cache",
        ".mypy_cache",
        ".sonar",
        ".scannerwork",
    }
    if not repo_map.is_file():
        return {
            "id": "repo_map_complete",
            "name": "Repo map documents every top-level dir",
            "status": "warn",
            "message": "dev/REPO_MAP.md missing",
            "violations": [],
        }
    text = repo_map.read_text(encoding="utf-8")
    violations: list = [
        {"undocumented_dir": p.name}
        for p in sorted(REPO.iterdir())
        if p.is_dir() and not p.name.startswith(".") and p.name not in skip and (p.name + "/") not in text
    ]
    for tok in sorted(set(re.findall(r"`([^`\s]+)`", text))):
        token = tok.rstrip("/")
        if not token.startswith(_REPO_MAP_TOP_PREFIXES):
            continue
        if any(ch in token for ch in "*<>{}") or ".." in token:
            continue
        if not (REPO / token).exists():
            violations.append({"dangling_path": tok})
    n_dangle = sum(1 for v in violations if "dangling_path" in v)
    n_undoc = len(violations) - n_dangle
    status = "pass" if not violations else ("fail" if _ENFORCE_REPO_MAP else "warn")
    return {
        "id": "repo_map_complete",
        "name": "Repo map documents every top-level dir",
        "status": status,
        "message": (
            "all top-level dirs documented + cited paths resolve"
            if not violations
            else f"{n_undoc} undocumented dir(s) + {n_dangle} dangling path(s) in REPO_MAP.md"
        ),
        "violations": violations[:50],
    }


# A string constant that IS a Greek-letter phase tag (e.g. "τ.7.x.b",
# "τ.6.x.2.a-h", "ω.4x"). Anchored full-match so prose / marker strings
# ("TRACKER-STATE: idle", "Next phase") never match.
_PHASE_TAG_FULL = re.compile(r"^[Ͱ-Ͽ]\.[0-9A-Za-z][0-9A-Za-z.x+\-]*$")

# The rolling state docs that get trimmed / archived for bootstrap-bandwidth
# + OOM hygiene (Rule §11). Pinning a durable phase tag against these breaks
# the moment the snapshot rolls (the ~45-pin breakage of 2026-05-21).
_EPHEMERAL_DOCS = ("SESSION_STATE.md", "IN_FLIGHT.md")


def check_no_ephemeral_doc_pins() -> dict:
    """Tests must not pin a phase tag against the rolling state docs
    (``dev/SESSION_STATE.md`` / ``dev/IN_FLIGHT.md``). Those are trimmed +
    archived regularly, so such pins break when the snapshot rolls — the
    failure class that broke ~45 phase pins on 2026-05-21. The durable phase
    record is ``dev/CHANGELOG.md``; route phase pins through
    ``tests.fixtures.assert_phase_recorded`` (which reads CHANGELOG).

    A test is flagged when it BOTH (a) reads an ephemeral doc — via an inline
    "SESSION_STATE.md"/"IN_FLIGHT.md" literal or a module const that points at
    one — AND (b) asserts a phase-tag string constant. Reading an ephemeral
    doc for a non-phase reason (e.g. the TRACKER-STATE marker check) is fine.

    Waiver: ``# ephemeral-doc-waived: <reason>`` on the test's ``def`` line or
    the line above it.
    """
    tests_dir = REPO / "tests"
    if not tests_dir.is_dir():
        return {
            "id": "ephemeral_doc_pins",
            "name": "No phase pins on rolling state docs",
            "status": "pass",
            "message": "tests/ not present",
            "violations": [],
        }

    violations: list[dict] = []
    for py in sorted(tests_dir.glob("*.py")):
        try:
            text = py.read_text(encoding="utf-8")
            tree = ast.parse(text)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        lines = text.splitlines()

        # Module-level consts whose value mentions an ephemeral doc path.
        ephemeral_consts: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.Assign):
                strs = [
                    c.value for c in ast.walk(node.value) if isinstance(c, ast.Constant) and isinstance(c.value, str)
                ]
                if any(any(doc in s for doc in _EPHEMERAL_DOCS) for s in strs):
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name):
                            ephemeral_consts.add(tgt.id)

        for fn in ast.walk(tree):
            if not isinstance(fn, ast.FunctionDef) or not fn.name.startswith("test"):
                continue
            str_consts = [n.value for n in ast.walk(fn) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
            names = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
            reads_ephemeral = any(any(doc in s for doc in _EPHEMERAL_DOCS) for s in str_consts) or bool(
                names & ephemeral_consts
            )
            has_phase_tag = any(_PHASE_TAG_FULL.match(s) for s in str_consts)
            if not (reads_ephemeral and has_phase_tag):
                continue
            same = lines[fn.lineno - 1] if 0 < fn.lineno <= len(lines) else ""
            prev = lines[fn.lineno - 2] if 1 < fn.lineno <= len(lines) else ""
            if "ephemeral-doc-waived" in same or "ephemeral-doc-waived" in prev:
                continue
            violations.append({"file": f"tests/{py.name}", "test": fn.name, "line": fn.lineno})

    return {
        "id": "ephemeral_doc_pins",
        "name": "No phase pins on rolling state docs",
        "status": "fail" if violations else "pass",
        "message": (
            f"{len(violations)} test(s) pin a phase tag against a rolling state doc "
            "(SESSION_STATE.md / IN_FLIGHT.md) — route through "
            "tests.fixtures.assert_phase_recorded (reads CHANGELOG.md)"
            if violations
            else "no phase pins on rolling state docs (SESSION_STATE.md / IN_FLIGHT.md)"
        ),
        "violations": violations,
    }


# ----------------------------------------------------------------------
# Anti-bloat guard (2026-05-29 mint-audit) — truth-record size budget.
# Ships WARN-tier so it can be committed while the records are still over
# budget; the hard ceiling promotes to FAIL once Phase 1 rotation brings
# SESSION_STATE/IN_FLIGHT under budget (flip the flag below in that commit).
# CLAUDE_PROJECT_RULES.md is WARN-only (curated, not auto-rotated).
# ----------------------------------------------------------------------
_ENFORCE_HARD_TRUTH_BUDGET = False  # ← Phase 1 flips this to True
_TRUTH_BUDGETS = {
    "dev/SESSION_STATE.md": {"soft": 60_000, "hard": 120_000, "max_entries": 2},
    "dev/IN_FLIGHT.md": {"soft": 40_000, "hard": 120_000, "max_entries": 2},
    # RULES re-baselined 2026-05-30 after the Phase-1 slim (115KB → 78KB ≈ ~30k
    # tokens, the plan's target). Soft set just above the slimmed size so the guard
    # is a re-bloat sentinel from the new baseline, not permanently red; WARN-only
    # (curated, not auto-rotated). rules_no_frozen_stats is the finer anti-bloat check.
    "dev/CLAUDE_PROJECT_RULES.md": {"soft": 85_000, "hard": None, "max_entries": None},
}


def check_truth_record_budget() -> dict:
    """Cap the always-read truth records by byte size + entry count so they
    cannot silently re-bloat (the 2026-05-29 audit found the session triad
    cost ~200k tokens). WARN at the soft ceiling; the hard ceiling promotes to
    FAIL once Phase 1 rotation lands (see ``_ENFORCE_HARD_TRUTH_BUDGET``).
    ``dev/CLAUDE_PROJECT_RULES.md`` is WARN-only (curated, not auto-rotated)."""
    violations: list = []
    has_hard = False
    for rel, b in _TRUTH_BUDGETS.items():
        p = REPO / rel
        if not p.is_file():
            continue
        size = p.stat().st_size
        if b["hard"] is not None and size > b["hard"]:
            violations.append({"file": rel, "bytes": size, "budget": b["hard"], "tier": "hard"})
            has_hard = True
        elif size > b["soft"]:
            violations.append({"file": rel, "bytes": size, "budget": b["soft"], "tier": "soft"})
        if b["max_entries"] is not None:
            # Count journal ENTRY-START lines (`> **➤➤➤`), not the bare glyph —
            # an entry's prose may mention the marker, and a stable "## ➤➤➤"
            # trailing heading is not an entry. Mirrors rotate_truth_records.
            n = sum(1 for ln in p.read_text(encoding="utf-8").splitlines() if ln.startswith("> **➤➤➤"))
            if n > b["max_entries"]:
                violations.append({"file": rel, "entries": n, "budget": b["max_entries"], "tier": "entries"})
    if not violations:
        status = "pass"
    elif has_hard and _ENFORCE_HARD_TRUTH_BUDGET:
        status = "fail"
    else:
        status = "warn"
    return {
        "id": "truth_record_budget",
        "name": "Truth-record size budget",
        "status": status,
        "message": (
            "truth records within budget"
            if not violations
            else f"{len(violations)} truth-record budget breach(es) — "
            "run `py -3 scripts/rotate_truth_records.py --apply` to archive old entries"
        ),
        "violations": violations,
    }


_COMMERCIAL_STEMS = ("sales", "license_key", "license_state", "onix", "build_onix", "print_cover")
_COMMERCIAL_STEM_RE = re.compile(r"\b(" + "|".join(_COMMERCIAL_STEMS) + r")\b")


def check_commercial_orphans() -> dict:
    """The 2026-05-14 free-public pivot dropped commercial sale / ISBN / ONIX /
    print. These module stems must not exist (or be imported) under scripts/
    once Phase 4 removes them. Ships WARN while they still exist; PROMOTE the
    breach branch to 'fail' in Phase 4 so reintroduction is permanently blocked.
    (archive_org is intentionally NOT on the list — it is legit free distribution.)"""
    scripts_dir = REPO / "scripts"
    violations: list = []
    if scripts_dir.is_dir():
        for p in scripts_dir.rglob("*.py"):
            if "archive" in p.parts:
                continue
            rel = str(p.relative_to(REPO))
            if p.stem in _COMMERCIAL_STEMS:
                violations.append({"kind": "module", "path": rel})
                continue
            try:
                for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                    stripped = line.lstrip()
                    if (stripped.startswith("import ") or stripped.startswith("from ")) and _COMMERCIAL_STEM_RE.search(
                        line
                    ):
                        violations.append({"kind": "import", "path": rel, "line": i})
            except (OSError, UnicodeDecodeError):
                continue
    modules = sorted({v["path"] for v in violations})
    return {
        "id": "commercial_orphans",
        "name": "No commercial-era orphan modules",
        "status": "warn" if violations else "pass",  # PROMOTE to "fail" in Phase 4
        "message": (
            "no commercial-era orphan modules/imports under scripts/"
            if not violations
            else f"{len(violations)} commercial-era reference(s) remain (removed in Phase 4): " + ", ".join(modules)
        ),
        "violations": violations,
    }


def check_changelog_size() -> dict:
    """CHANGELOG.md is append-only and the only un-rotated truth record. WARN
    past a soft byte budget so a manual month-roll gets prompted. Do NOT
    auto-rotate (check_untracked_phases substring-searches the live file)."""
    p = REPO / "dev" / "CHANGELOG.md"
    if not p.is_file():
        return {
            "id": "changelog_size",
            "name": "CHANGELOG size",
            "status": "pass",
            "message": "no CHANGELOG.md",
            "violations": [],
        }
    size = p.stat().st_size
    budget = 1_500_000
    breached = size > budget
    return {
        "id": "changelog_size",
        "name": "CHANGELOG size",
        "status": "warn" if breached else "pass",
        "message": (
            f"CHANGELOG.md is {size:,}B (> {budget:,}B) — consider a manual month-roll to "
            "dev/archive/CHANGELOG_<month>.md"
            if breached
            else f"CHANGELOG.md {size:,}B within budget"
        ),
        "violations": ([{"file": "dev/CHANGELOG.md", "bytes": size, "budget": budget}] if breached else []),
    }


_DATED_DOC_RE = re.compile(r"^(AUDIT|SCOPE|CALIBRATION|PILOT|PROPOSAL|SESSION_END)_\d{4}-\d{2}-\d{2}")


def check_dev_doc_sprawl() -> dict:
    """The always-read dev/ dir should stay lean. WARN when it accumulates too
    many .md files, and list dated single-event docs (AUDIT/SCOPE/CALIBRATION/
    PILOT/PROPOSAL/SESSION_END) that belong in dev/archive/. WARN-only — which
    docs stay live needs human judgment."""
    dev = REPO / "dev"
    budget = 40
    mds = sorted(p.name for p in dev.glob("*.md")) if dev.is_dir() else []
    dated = [n for n in mds if _DATED_DOC_RE.match(n)]
    violations: list = []
    if len(mds) > budget:
        violations.append({"dev_md_count": len(mds), "budget": budget})
    violations.extend({"archive_candidate": f"dev/{n}"} for n in dated)
    return {
        "id": "dev_doc_sprawl",
        "name": "dev/ doc sprawl",
        "status": "warn" if violations else "pass",
        "message": (
            f"dev/ has {len(mds)} .md files (budget {budget}); {len(dated)} dated docs are archive candidates"
            if violations
            else f"dev/ has {len(mds)} .md files within budget"
        ),
        "violations": violations,
    }


_ARC_TAG_RE = re.compile(r"(γ\.\d|ω\.\d|gamma\.\d|omega\.\d)")
_PCT_RE = re.compile(r"\d+\.\d+%")


def check_rules_no_frozen_stats() -> dict:
    """Finished-arc statistics (voice-composition percentages, entry counts)
    belong in CHANGELOG/archive, not the always-read rules. WARN when
    CLAUDE_PROJECT_RULES.md carries too many frozen percentage tokens or
    dated-arc-tag + percentage lines."""
    p = REPO / "dev" / "CLAUDE_PROJECT_RULES.md"
    if not p.is_file():
        return {
            "id": "rules_no_frozen_stats",
            "name": "Rules carry no frozen stats",
            "status": "pass",
            "message": "no rules file",
            "violations": [],
        }
    lines = p.read_text(encoding="utf-8").splitlines()
    pct_tokens = sum(len(_PCT_RE.findall(ln)) for ln in lines)
    arc_pct_lines = [i for i, ln in enumerate(lines, 1) if _ARC_TAG_RE.search(ln) and _PCT_RE.search(ln)]
    violations: list = []
    if pct_tokens > 8:
        violations.append({"percentage_tokens": pct_tokens, "budget": 8})
    violations.extend({"arc_stat_line": i} for i in arc_pct_lines)
    return {
        "id": "rules_no_frozen_stats",
        "name": "Rules carry no frozen stats",
        "status": "warn" if violations else "pass",
        "message": (
            f"CLAUDE_PROJECT_RULES.md has {pct_tokens} percentage tokens + {len(arc_pct_lines)} "
            "dated-arc-stat lines (move finished-arc stats to CHANGELOG/archive)"
            if violations
            else "rules carry no frozen-arc statistics"
        ),
        "violations": violations,
    }


# ----------------------------------------------------------------------
# 2026-05-29 mint-audit anti-bloat guards — Phase 0 tail
#   commercial_terms · retired_terms · triad_plan_consistency · stray_artifacts
#
# Each ships WARN while a breach still exists — a pre-commit `fail` would brick
# its own adding commit (the pre-commit hook blocks on any FAIL). The matching
# cleanup phase flips the guard's ``_ENFORCE_*`` flag to True so the breach
# becomes a hard FAIL and reintroduction is permanently blocked.
# ----------------------------------------------------------------------
_ENFORCE_COMMERCIAL = False  # ← Phase 4 (decommercialize) flips this
_ENFORCE_RETIRED_TERMS = True  # ← Phase 2 flipped (old PLAN archived + PLAYBOOK/REPO_MAP refs cleared)
_ENFORCE_TRIAD_PLAN = True  # ← Phase 2 (roadmap refresh) flipped
_ENFORCE_STRAY_ARTIFACTS = (
    True  # tree verified clean 2026-05-29 → FAIL-tier (blocks future junk; git-aware, gitignored scratch exempt)
)
_ENFORCE_REPO_MAP = False  # ← Phase 5 (regenerate REPO_MAP) flips this


# Curated, always-read PROCESS docs scanned by the term guards. Deliberately
# EXCLUDES the append-only journal (CHANGELOG.md), the rolling state docs
# (SESSION_STATE.md / IN_FLIGHT.md), and dev/archive/ — those legitimately
# reference the commercial past and the retired deadline, so scanning them would
# make these guards permanently un-greenable.
_CURATED_DOC_NAMES = (
    "CLAUDE_PROJECT_RULES.md",
    "SESSION_PLAYBOOK.md",
    "MATRIX_MAP.md",
    "REPO_MAP.md",
    "SCHEMAS.md",
    "SECURITY.md",
    "PERF_BUDGETS.md",
    "ROADMAP_FUTURE.md",
)

# Line-level waiver — a line bearing this marker is exempt from the term scans
# (e.g. the §10 "what this is NOT" pivot note, which must NAME the dropped
# commercial surfaces to document the 2026-05-14 free-public pivot).
_TERM_WAIVER = "term-ref-ok"


def _curated_dev_docs() -> list[Path]:
    """The curated process docs + the single live PLAN (never the journals)."""
    dev = REPO / "dev"
    if not dev.is_dir():
        return []
    docs = [dev / n for n in _CURATED_DOC_NAMES if (dev / n).is_file()]
    docs += sorted(dev.glob("PLAN_*.md"))  # PLAN_SINGULAR → one live plan
    return docs


def _live_script_files() -> list[Path]:
    """``*.py`` under scripts/, excluding dev/archive parts, ``test_`` files, and
    ``lint_rules.py`` itself (which carries the denylist terms as literals)."""
    sd = REPO / "scripts"
    if not sd.is_dir():
        return []
    out: list[Path] = []
    for p in sd.rglob("*.py"):
        if "archive" in p.parts or p.name.startswith("test_") or p.name == "lint_rules.py":
            continue
        out.append(p)
    return out


_COMMERCIAL_TERMS = (
    "royalty",
    "royalties",
    "KDP",
    "retailer",
    "Apple Books",
    "Google Play",
    "ISBN",
    "ONIX",
    "pricing",
    "sales_record",
)
_COMMERCIAL_TERM_RE = re.compile(r"(?i)\b(" + "|".join(re.escape(t) for t in _COMMERCIAL_TERMS) + r")\b")


def check_commercial_terms() -> dict:
    """The 2026-05-14 free-public pivot dropped retail / ISBN / ONIX / store
    distribution. Commercial vocabulary must not live in the always-read process
    docs or in live code. Ships WARN while breaches remain; Phase 4 flips
    ``_ENFORCE_COMMERCIAL`` so reintroduction becomes a hard FAIL. Allowlist: any
    file whose name carries ``archive_org`` (legit free distribution) + any line
    bearing the ``term-ref-ok`` waiver marker (the §10 pivot note)."""
    violations: list = []
    targets = [(p, str(p.relative_to(REPO)).replace("\\", "/")) for p in _curated_dev_docs()]
    targets += [(p, str(p.relative_to(REPO)).replace("\\", "/")) for p in _live_script_files()]
    for p, rel in targets:
        if "archive_org" in p.name:
            continue
        try:
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if _TERM_WAIVER in line:
                    continue
                m = _COMMERCIAL_TERM_RE.search(line)
                if m:
                    violations.append({"path": rel, "line": i, "term": m.group(0)})
        except (OSError, UnicodeDecodeError):
            continue
    status = "pass" if not violations else ("fail" if _ENFORCE_COMMERCIAL else "warn")
    return {
        "id": "commercial_terms",
        "name": "No commercial-era vocabulary",
        "status": status,
        "message": (
            "no commercial vocabulary in process docs / live code"
            if not violations
            else f"{len(violations)} commercial-term reference(s) remain (removed in Phase 4)"
        ),
        "violations": violations[:40],
    }


_RETIRED_TERMS = ("2026-06-07", "hard deadline", "sonar")


def check_retired_terms() -> dict:
    """Retired project vocabulary must not live in the always-read process docs:
    the dropped hard deadline (``2026-06-07`` / ``hard deadline`` — superseded by
    the 'completeness over speed' principle) and the removed ``sonar`` tooling.
    Ships WARN while breaches remain; Phase 1 flips ``_ENFORCE_RETIRED_TERMS``
    once the slim makes it clean, so reintroduction becomes a hard FAIL."""
    violations: list = []
    for p in _curated_dev_docs():
        rel = str(p.relative_to(REPO)).replace("\\", "/")
        try:
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if _TERM_WAIVER in line:
                    continue
                low = line.lower()
                for t in _RETIRED_TERMS:
                    if t.lower() in low:
                        violations.append({"path": rel, "line": i, "term": t})
        except (OSError, UnicodeDecodeError):
            continue
    status = "pass" if not violations else ("fail" if _ENFORCE_RETIRED_TERMS else "warn")
    return {
        "id": "retired_terms",
        "name": "No retired vocabulary",
        "status": status,
        "message": (
            "no retired vocabulary in process docs"
            if not violations
            else f"{len(violations)} retired-term reference(s) remain (removed in the slim)"
        ),
        "violations": violations[:40],
    }


_PLAN_FILE_RE = re.compile(r"PLAN_\d{4}-\d{2}-\d{2}[A-Za-z0-9_\-]*\.md")


def check_triad_plan_consistency() -> dict:
    """The bootstrap triad's PLAN reference must be consistent + live. The plan
    named in the authoritative ``dev/cc-hooks/bootstrap-triad.ps1`` must also be
    named in ``CLAUDE_PROJECT_RULES.md`` (§0) and ``SESSION_PLAYBOOK.md``, and
    must resolve to a LIVE (non-archived) ``dev/<plan>``. Ships WARN; Phase 2
    (roadmap refresh, names the new plan in all three) flips
    ``_ENFORCE_TRIAD_PLAN`` so future divergence is a hard FAIL."""
    dev = REPO / "dev"
    hook = dev / "cc-hooks" / "bootstrap-triad.ps1"
    rules = dev / "CLAUDE_PROJECT_RULES.md"
    playbook = dev / "SESSION_PLAYBOOK.md"
    violations: list = []
    if not hook.is_file():
        violations.append({"issue": "bootstrap-triad.ps1 not found", "path": "dev/cc-hooks/bootstrap-triad.ps1"})
    else:
        hook_plans = sorted(set(_PLAN_FILE_RE.findall(hook.read_text(encoding="utf-8"))))
        if len(hook_plans) != 1:
            violations.append(
                {"issue": f"bootstrap hook names {len(hook_plans)} plans (expected 1)", "plans": hook_plans}
            )
        else:
            canonical = hook_plans[0]
            rules_txt = rules.read_text(encoding="utf-8") if rules.is_file() else ""
            pb_txt = playbook.read_text(encoding="utf-8") if playbook.is_file() else ""
            if canonical not in rules_txt:
                violations.append({"issue": "triad plan not named in CLAUDE_PROJECT_RULES.md", "plan": canonical})
            if canonical not in pb_txt:
                violations.append({"issue": "triad plan not named in SESSION_PLAYBOOK.md", "plan": canonical})
            if not (dev / canonical).is_file():
                violations.append({"issue": "triad plan not live in dev/ (archived or missing)", "plan": canonical})
    status = "pass" if not violations else ("fail" if _ENFORCE_TRIAD_PLAN else "warn")
    return {
        "id": "triad_plan_consistency",
        "name": "Bootstrap-triad PLAN reference consistent + live",
        "status": status,
        "message": (
            "triad PLAN reference consistent across hook / rules / playbook + live"
            if not violations
            else f"{len(violations)} triad-plan inconsistency(ies)"
        ),
        "violations": violations,
    }


_JUNK_SUFFIXES = (".tmp", ".bak", ".orig", ".rej", ".pyc", ".log")
_STRAY_GLYPHS = (">", "<", "→", "➤", "»", "«")


def _git_candidate_files() -> list[str] | None:
    """Tracked + untracked-not-ignored files (repo-relative, forward-slash). None
    if git is unavailable, so the caller can degrade gracefully. Gitignored
    scratch (e.g. *.log build noise) is intentionally invisible — only files that
    are or could be committed are stray candidates."""
    try:
        kw = dict(capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=30, cwd=str(REPO))
        tracked = subprocess.run(["git", "ls-files"], **kw)
        others = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], **kw)
    except (OSError, subprocess.SubprocessError):
        return None
    if tracked.returncode != 0 or others.returncode != 0:
        return None
    return [ln for ln in (tracked.stdout + others.stdout).splitlines() if ln.strip()]


def check_no_stray_artifacts() -> dict:
    """No junk in the committable working tree: junk suffixes (``.tmp/.bak/.orig/
    .rej/.pyc/.log``), zero-byte ``dev/*.md``, shell-glyph filenames (a botched
    ``save.ps1`` sweeps ``>``/arrow chars in), and tracked ``.sonar``/
    ``.scannerwork`` tooling. Git-aware (gitignored scratch is exempt). Ships WARN
    until the tree is verified clean, then ``_ENFORCE_STRAY_ARTIFACTS`` → FAIL."""
    files = _git_candidate_files()
    if files is None:
        return {
            "id": "stray_artifacts",
            "name": "No stray working-tree artifacts",
            "status": "warn",
            "message": "git unavailable — stray-artifact scan skipped",
            "violations": [],
        }
    seen: set = set()
    violations: list = []

    def _add(rel: str, why: str) -> None:
        key = (rel, why)
        if key not in seen:
            seen.add(key)
            violations.append({"stray": rel, "why": why})

    for rel in files:
        name = rel.rsplit("/", 1)[-1]
        if name.endswith(_JUNK_SUFFIXES):
            _add(rel, "junk artifact")
        if any(g in name for g in _STRAY_GLYPHS):
            _add(rel, "shell-glyph filename")
        if rel.startswith((".sonar/", ".scannerwork/")) or "/.sonar/" in rel or "/.scannerwork/" in rel:
            _add(rel, "sonar tooling tracked")
        if rel.startswith("dev/") and rel.endswith(".md"):
            try:
                if (REPO / rel).is_file() and (REPO / rel).stat().st_size == 0:
                    _add(rel, "zero-byte doc")
            except OSError:
                pass
    status = "pass" if not violations else ("fail" if _ENFORCE_STRAY_ARTIFACTS else "warn")
    return {
        "id": "stray_artifacts",
        "name": "No stray working-tree artifacts",
        "status": status,
        "message": (
            "no stray artifacts in the committable working tree"
            if not violations
            else f"{len(violations)} stray artifact(s)"
        ),
        "violations": violations[:40],
    }


ALL_CHECKS = {
    "6.1": check_encoder_canonical_order,
    "6.2": check_cross_link_invariant,
    "encode_decode": check_encode_decode_round_trip,
    "docs": check_doc_cross_references,
    "repo_map_complete": check_repo_map_complete,
    "freshness": check_session_state_freshness,
    "truth_record_budget": check_truth_record_budget,
    "commercial_orphans": check_commercial_orphans,
    "commercial_terms": check_commercial_terms,
    "retired_terms": check_retired_terms,
    "triad_plan_consistency": check_triad_plan_consistency,
    "stray_artifacts": check_no_stray_artifacts,
    "changelog_size": check_changelog_size,
    "dev_doc_sprawl": check_dev_doc_sprawl,
    "rules_no_frozen_stats": check_rules_no_frozen_stats,
    # Drift-catching tier (added after a real drift event)
    "inflight": check_inflight_freshness,
    "untracked_phases": check_untracked_phases,
    "code_doc_sync": check_session_state_inventory,
    # 2026-05-21 — complement to untracked_phases: phase pins must target the
    # durable record (CHANGELOG), never the rolling SESSION_STATE/IN_FLIGHT.
    "ephemeral_doc_pins": check_no_ephemeral_doc_pins,
    # ω.9 + ω.10 hardening tier
    "atomic_writes": check_atomic_writes,
    "external_http": check_external_http,
    # ω.15 plan-coherence tier
    "plan_coherence": check_plan_coherence,
    # Audit-U belt — canonical-schema invariant for manuscript witnesses
    "manuscript_witnesses": check_manuscript_witnesses_valid,
    # Whole-project audit 2026-05-20 — render coverage + provenance tiers
    "render_coverage": check_render_coverage_no_regression,
    "provenance_tier": check_provenance_tier_known,
}


# ----------------------------------------------------------------------
# ω.18 — Auto-fix mode
#
# Most lint failures need human judgment: code review (atomic_writes,
# external_http), template understanding (cross_link, encoders), or
# substantive content writes (CHANGELOG entries, addenda). Auto-fixing
# those would either mask real drift or produce malformed output.
#
# Only `freshness` has a deterministic, single-step fix (touch
# SESSION_STATE.md's mtime to match CHANGELOG.md's). Even that has a
# caveat — if SESSION_STATE was actually forgotten, the fix masks
# the drift instead of revealing it. The fixer's `message` flags
# this so the user knows what they're agreeing to.
#
# Future ω.18.x phases can add more fixers. Each new fixer is its
# own ledger entry so the safety review happens at fixer-grain.
# ----------------------------------------------------------------------


def _fix_freshness(
    check_result: dict,
    *,
    dry_run: bool = False,
) -> dict:
    """Sync SESSION_STATE.md's mtime with CHANGELOG.md's.

    The freshness check warns when the two diverge by > 6h. This
    fixer ONLY fixes the mtime — if SESSION_STATE.md's content is
    actually stale, the fix masks the drift. The returned message
    spells this out explicitly.

    Reversible via `git restore` (the file's content is unchanged;
    only the filesystem timestamp shifts).
    """
    changelog = REPO / "dev" / "CHANGELOG.md"
    session = REPO / "dev" / "SESSION_STATE.md"
    if not changelog.is_file() or not session.is_file():
        return {
            "ok": False,
            "applied": False,
            "message": ("freshness: cannot fix — CHANGELOG.md or SESSION_STATE.md is missing"),
            "changes": [],
        }
    cl_mtime = changelog.stat().st_mtime
    ss_mtime = session.stat().st_mtime
    if abs(cl_mtime - ss_mtime) <= 6 * 3600:
        return {
            "ok": True,
            "applied": False,
            "message": ("freshness: already in sync; nothing to do"),
            "changes": [],
        }
    if dry_run:
        return {
            "ok": True,
            "applied": False,
            "message": (
                f"freshness [dry-run]: would sync SESSION_STATE.md "
                f"mtime to CHANGELOG.md (currently "
                f"{int(abs(cl_mtime - ss_mtime) / 3600)}h apart). "
                f"NOTE: this only fixes the timestamp — if "
                f"SESSION_STATE's content was forgotten, you still "
                f"need to update it manually."
            ),
            "changes": [
                {
                    "file": "dev/SESSION_STATE.md",
                    "field": "mtime",
                    "from": ss_mtime,
                    "to": cl_mtime,
                }
            ],
        }
    os.utime(session, (cl_mtime, cl_mtime))
    return {
        "ok": True,
        "applied": True,
        "message": (
            "freshness: synced SESSION_STATE.md mtime to "
            "CHANGELOG.md. NOTE: if SESSION_STATE's CONTENT was "
            "actually forgotten, this masks the drift; the fix "
            "is timestamp-only."
        ),
        "changes": [
            {
                "file": "dev/SESSION_STATE.md",
                "field": "mtime",
                "from": ss_mtime,
                "to": cl_mtime,
            }
        ],
    }


# Registry: check_id → fixer callable. Functions matching the
# `(check_result, *, dry_run) -> dict` shape can be plugged in
# safely. Empty entries are intentional — most checks need human
# review and the right answer is "no auto-fix available."
def _fix_truth_record_budget(check_result: dict, *, dry_run: bool = False) -> dict:
    """Fixer for ``truth_record_budget`` — delegates to the rotator, which keeps
    the newest entries + stable sections live and archives the rest. Reversible
    via ``git restore`` (live trim) + deleting the appended archive batch."""
    try:
        from scripts.rotate_truth_records import rotate_all
    except Exception as e:  # pragma: no cover — defensive
        return {
            "ok": False,
            "applied": False,
            "message": f"truth_record_budget: rotator unavailable ({e})",
            "changes": [],
        }
    res = rotate_all(dry_run=dry_run)
    return {
        "ok": True,
        "applied": res.get("applied", False),
        "message": "truth_record_budget: " + res.get("message", ""),
        "changes": res.get("changes", []),
    }


FIXERS: dict[str, Callable[..., dict]] = {
    "freshness": _fix_freshness,
    "truth_record_budget": _fix_truth_record_budget,
}


def run_fixers(
    *,
    check_ids: list[str] | None = None,
    dry_run: bool = False,
) -> dict:
    """Run fixers for any failing/warning checks that have one
    registered. Returns ``{checks: [...], summary: {...}}`` where
    each per-check entry surfaces either the fixer's output or a
    "no auto-fix available" stub for unregistered checks.

    Pure dispatcher — checks themselves run via ``run_all``. We
    only fix things the linter is ALREADY flagging; clean checks
    are left alone."""
    lint = run_all(check_ids)
    out_checks: list[dict] = []
    applied = 0
    refused = 0
    skipped_clean = 0
    for c in lint["checks"]:
        cid = c["id"]
        if c["status"] == "pass":
            skipped_clean += 1
            continue
        fixer = FIXERS.get(cid)
        if fixer is None:
            refused += 1
            out_checks.append(
                {
                    "id": cid,
                    "name": c["name"],
                    "status": "refused",
                    "message": (f"no auto-fix available for {cid!r}: {c['message']}"),
                    "changes": [],
                }
            )
            continue
        result = fixer(c, dry_run=dry_run)
        if result.get("applied"):
            applied += 1
        out_checks.append(
            {
                "id": cid,
                "name": c["name"],
                "status": "fixed" if result.get("applied") else ("ready" if result.get("ok") else "failed"),
                "message": result.get("message", ""),
                "changes": result.get("changes", []),
            }
        )
    return {
        "checks": out_checks,
        "summary": {
            "applied": applied,
            "refused": refused,
            "skipped_clean": skipped_clean,
            "dry_run": dry_run,
        },
    }


def run_all(check_ids: list[str] | None = None) -> dict:
    """Run every check (or just the listed ones) and return aggregate.

    Used both by the CLI entrypoint AND by api_preflight() in
    scripts/web.py (which calls run_all() and folds the result into
    the readiness dashboard).

    ω.23 — every per-check dict gains a ``duration_ms`` field
    (float, ms) timed via ``time.perf_counter``. Aggregate
    summary gains ``total_ms`` (sum of per-check durations).
    Both fields are additive — existing consumers (api_preflight,
    test assertions) ignore unknown keys.
    """
    # ω.23.1 — drop the AST cache between back-to-back run_all()
    # calls so consumers (tests, api_preflight) don't accidentally
    # see stale parse trees when files have changed on disk.
    _clear_parse_cache()
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
                    "duration_ms": 0.0,
                }
            )
            continue
        t0 = time.perf_counter()
        try:
            check_result = ALL_CHECKS[cid]()
        except Exception as e:
            check_result = {
                "id": cid,
                "name": cid,
                "status": "fail",
                "message": f"linter check raised: {e}",
                "violations": [],
            }
        check_result["duration_ms"] = round(
            (time.perf_counter() - t0) * 1000.0,
            3,
        )
        results.append(check_result)
    summary = {
        "total": len(results),
        "pass": sum(1 for r in results if r["status"] == "pass"),
        "warn": sum(1 for r in results if r["status"] == "warn"),
        "fail": sum(1 for r in results if r["status"] == "fail"),
    }
    summary["clean"] = summary["fail"] == 0
    summary["total_ms"] = round(
        sum(r.get("duration_ms", 0.0) for r in results),
        3,
    )
    return {"checks": results, "summary": summary}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--check", action="append", help="run only the named check(s); repeat for multiple")
    p.add_argument("--json", action="store_true", help="machine-readable JSON output")
    p.add_argument(
        "--profile",
        action="store_true",
        help=(
            "ω.23 — sort checks by duration descending and print "
            "per-check timing. Useful for spotting which check is "
            "the bottleneck as the suite grows."
        ),
    )
    p.add_argument(
        "--fix",
        action="store_true",
        help=(
            "ω.18 — auto-fix safe drift. Most checks need human "
            "review and surface 'no auto-fix available'. Use "
            "--dry-run to preview without applying."
        ),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "ω.18 — when paired with --fix, preview what would change without writing anything. No-op without --fix."
        ),
    )
    args = p.parse_args(argv)

    if args.fix:
        return _run_fix_cli(args)

    out = run_all(args.check)

    if args.json:
        print(json.dumps(out, indent=2))
    else:
        # ω.23 — when --profile is set, sort checks by duration
        # descending so the slowest is the first thing the operator
        # sees. Default ordering preserves the natural check sequence.
        ordered = (
            sorted(
                out["checks"],
                key=lambda c: c.get("duration_ms", 0.0),
                reverse=True,
            )
            if args.profile
            else out["checks"]
        )
        for c in ordered:
            icon = {"pass": "✓", "warn": "⚠", "fail": "✗"}[c["status"]]
            timing = f"  [{c.get('duration_ms', 0.0):>7.1f} ms]" if args.profile else ""
            print(f"  {icon} {c['name']:35s}{timing}  {c['message']}")
            if c["violations"] and c["status"] != "pass":
                for v in c["violations"][:5]:
                    print(f"      · {v}")
                if len(c["violations"]) > 5:
                    print(f"      … and {len(c['violations']) - 5} more")
        s = out["summary"]
        verdict = "CLEAN" if s["clean"] else "VIOLATIONS"
        if args.profile:
            print(
                f"\n  {verdict}: {s['pass']} pass · {s['warn']} warn · "
                f"{s['fail']} fail · {s.get('total_ms', 0.0):.1f} ms total"
            )
        else:
            print(f"\n  {verdict}: {s['pass']} pass · {s['warn']} warn · {s['fail']} fail")

    return 0 if out["summary"]["clean"] else 1


def _run_fix_cli(args) -> int:
    """ω.18 — render the fix-mode output. Always exits 0 unless a
    fixer hard-failed; "refused" entries (no fixer registered) are
    informational and don't fail the run, since the underlying
    `lint_rules.py` invocation (without --fix) is what catches
    those for CI."""
    out = run_fixers(check_ids=args.check, dry_run=args.dry_run)
    if args.json:
        print(json.dumps(out, indent=2))
        return 0
    icons = {
        "fixed": "✓",
        "ready": "→",  # dry-run preview
        "refused": "·",
        "failed": "✗",
    }
    if not out["checks"]:
        print("  (no failing checks; nothing to fix)")
    for c in out["checks"]:
        icon = icons.get(c["status"], "?")
        print(f"  {icon} {c['name']:35s}  {c['message']}")
    s = out["summary"]
    label = "DRY-RUN" if s["dry_run"] else "APPLIED"
    print(f"\n  {label}: {s['applied']} applied · {s['refused']} refused · {s['skipped_clean']} clean")
    # Exit 1 only if a fixer that was supposed to apply something
    # hard-failed (e.g. write error). "Refused" is informational.
    failed = sum(1 for c in out["checks"] if c["status"] == "failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
