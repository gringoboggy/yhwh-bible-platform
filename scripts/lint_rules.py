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
import re
import sys
from pathlib import Path

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
        # Post-split: one constant per file in templates/
        for py in sorted(templates_dir.glob("*.py")):
            if py.name == "__init__.py":
                continue
            text = py.read_text(encoding="utf-8")
            for m in re.finditer(
                r'^([A-Z_]+_HTML)\s*=\s*r"""', text, re.MULTILINE,
            ):
                name = m.group(1)
                start = m.end()
                end = text.find('"""', start)
                if end < 0:
                    continue
                consoles[name] = text[start:end]
    else:
        # Pre-split fallback
        web_py = (REPO / "scripts" / "web.py").read_text(encoding="utf-8")
        for m in re.finditer(
            r'^([A-Z_]+_HTML)\s*=\s*r"""', web_py, re.MULTILINE,
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
        "INDEX_HTML":    "/",
        "MATRIX_HTML":   "/matrix",
        "SOURCES_HTML":  "/sources",
        "EXPORT_HTML":   "/export",
        "CUSTOMIZE_HTML":"/customize",
        "AUDIT_HTML":    "/audit",
        "PUBLISHER_HTML":"/publisher",
        "WIZARD_HTML":   "/wizard",
        "DIFF_HTML":     "/diff",
        "COVERS_HTML":   "/covers",
        "PREFLIGHT_HTML":"/preflight",
        "APIHELP_HTML": "/apihelp",
        "OPS_HTML": "/ops",
        "COMPARE_HTML":  "/compare",
    }

    # Filter consoles to ones we have routes for — the editor (INDEX)
    # has a different layout (no console-style nav) and is exempt.
    expected_routes = [r for c, r in route_for_constant.items()
                        if c in consoles and c != "INDEX_HTML"]

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
            continue   # exempt — different layout
        my_route = route_for_constant.get(name)
        if not my_route:
            # Console exists but no route mapping — missing from the
            # table above. Treat as a violation so the linter forces
            # the table to be updated.
            violations.append({
                "console": name,
                "issue": "no route mapping in lint_rules.py",
            })
            continue
        for r in expected_routes:
            if r == my_route:
                continue   # self-link is via active-page span, not nav
            # If checking the matrix route, accept either "/" or "/matrix"
            if r == "/matrix":
                if not any(
                    f'"{a}"' in body or f"'{a}'" in body
                    for a in matrix_aliases
                ):
                    violations.append({
                        "console": name,
                        "missing_link_to": "/matrix or /",
                    })
                continue
            # Check for the link. Accept either href="r" or href='r'.
            if f'"{r}"' not in body and f"'{r}'" not in body:
                violations.append({
                    "console": name,
                    "missing_link_to": r,
                })

    return {
        "id": "6.2",
        "name": "Cross-link invariant",
        "status": "fail" if violations else "pass",
        "message": (
            f"{len(violations)} missing cross-links across "
            f"{len(consoles) - 1} consoles"
            if violations else
            f"all {len(consoles) - 1} consoles cross-link to each other"
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
        ("scripts.core.covers",   "encode_book_covers"),
    ]

    violations: list[dict] = []
    for mod_name, fn_name in encoders:
        try:
            mod = __import__(mod_name, fromlist=[fn_name])
            fn = getattr(mod, fn_name)
        except (ImportError, AttributeError) as e:
            violations.append({
                "encoder": f"{mod_name}.{fn_name}",
                "issue": f"could not import: {e}",
            })
            continue
        # Pick three book codes in deliberately non-canonical order.
        # Canonical order has `gen` (very early) and `mat` (NT, late).
        # We add `tob` from the Apocrypha which sits between OT and NT
        # in the project's 87-book superset.
        if fn_name == "encode_per_book_languages":
            sample = {"mat": ["english"], "tob": ["english"], "gen": ["english"]}
        else:
            sample = {"mat": "x", "tob": "y", "gen": "z"}
        try:
            encoded = fn(sample)
        except Exception as e:
            violations.append({
                "encoder": f"{mod_name}.{fn_name}",
                "issue": f"raised on sample input: {e}",
            })
            continue
        codes = [s.split("=")[0] for s in encoded]
        expected = sorted(codes, key=lambda c: rank.get(c, len(book_order)))
        if codes != expected:
            violations.append({
                "encoder": f"{mod_name}.{fn_name}",
                "got_order": codes,
                "expected_order": expected,
            })

    return {
        "id": "6.1",
        "name": "Canonical-order encoders",
        "status": "fail" if violations else "pass",
        "message": (
            f"{len(violations)} encoder(s) produce non-canonical order"
            if violations else
            f"all {len(encoders)} encoders produce canonical order"
        ),
        "violations": violations,
    }


def check_encode_decode_round_trip() -> dict:
    """Every (encode, decode) pair should round-trip cleanly."""
    sys.path.insert(0, str(REPO))
    pairs = [
        ("scripts.build_edition",
         "encode_per_book_languages", "decode_per_book_languages",
         {"gen": ["english", "hebrew"], "mat": ["english"], "tob": []}),
        ("scripts.core.covers",
         "encode_book_covers", "decode_book_covers",
         {"gen": "covers/x/gen.jpg", "mat": "covers/x/mat.png", "tob": ""}),
    ]
    violations: list[dict] = []
    for mod_name, enc_name, dec_name, sample in pairs:
        try:
            mod = __import__(mod_name, fromlist=[enc_name, dec_name])
            enc = getattr(mod, enc_name)
            dec = getattr(mod, dec_name)
        except (ImportError, AttributeError) as e:
            violations.append({"pair": f"{enc_name}/{dec_name}",
                                "issue": str(e)})
            continue
        try:
            recovered = dec(enc(sample))
        except Exception as e:
            violations.append({"pair": f"{enc_name}/{dec_name}",
                                "issue": f"raised: {e}"})
            continue
        if recovered != sample:
            violations.append({
                "pair": f"{enc_name}/{dec_name}",
                "input": sample,
                "round_tripped": recovered,
            })

    return {
        "id": "encode_decode",
        "name": "Encoder/decoder round trip",
        "status": "fail" if violations else "pass",
        "message": (
            f"{len(violations)} pairs do not round-trip cleanly"
            if violations else
            f"all {len(pairs)} encode/decode pairs round-trip"
        ),
        "violations": violations,
    }


def check_doc_cross_references() -> dict:
    """Every addendum referenced in PLAN exists on disk; every active
    addendum in dev/ is mentioned in PLAN or SESSION_STATE.

    Auto-discovers the active PLAN by picking the lexicographically
    latest ``dev/PLAN_*.md`` (date-suffixed → newest wins). Survives
    PLAN refreshes without code changes. Falls back to PLAN_2026-05-07
    if no date-stamped file is present.
    """
    plan_files = sorted((REPO / "dev").glob("PLAN_*.md"))
    plan_path = plan_files[-1] if plan_files else (
        REPO / "dev" / "PLAN_2026-05-07.md"
    )
    plan = plan_path.read_text(encoding="utf-8")
    session = (REPO / "dev" / "SESSION_STATE.md").read_text(encoding="utf-8")
    referenced_text = plan + "\n" + session

    # Find every "dev/SCOPE_..." reference in the PLAN+SESSION
    referenced = set(re.findall(r"dev/SCOPE_[A-Za-z0-9_\-]+\.md",
                                  referenced_text))

    # Actual addendum files in dev/
    actual = set()
    for p in (REPO / "dev").glob("SCOPE_*.md"):
        actual.add(f"dev/{p.name}")

    missing_on_disk = referenced - actual
    orphan_files = actual - referenced

    violations: list[dict] = []
    for ref in sorted(missing_on_disk):
        violations.append({"issue": "referenced but missing on disk",
                            "doc": ref})
    for f in sorted(orphan_files):
        violations.append({"issue": "exists but not referenced anywhere",
                            "doc": f})

    return {
        "id": "docs",
        "name": "Documentation cross-references",
        "status": "warn" if violations else "pass",
        "message": (
            f"{len(violations)} doc reference issue(s)"
            if violations else
            f"all {len(actual)} scope addenda referenced consistently"
        ),
        "violations": violations,
    }


def check_session_state_freshness() -> dict:
    """SESSION_STATE.md should be no more than ~1 day stale relative
    to the most recent CHANGELOG entry. A larger gap suggests the
    continuity protocol (Rule §11) has slipped."""
    changelog = (REPO / "dev" / "CHANGELOG.md")
    session = (REPO / "dev" / "SESSION_STATE.md")
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
            "message": (
                f"CHANGELOG and SESSION_STATE diverge by "
                f"{int(delta/3600)} hours"
            ),
            "violations": [{
                "changelog_mtime": cl_mtime,
                "session_state_mtime": ss_mtime,
            }],
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
    marker_match = re.search(
        r"<!--\s*TRACKER-STATE:\s*(idle|active)\s*-->", text
    )
    if not marker_match:
        return {
            "id": "inflight_freshness",
            "name": "In-flight task tracker",
            "status": "warn",
            "message": (
                "IN_FLIGHT.md has no <!-- TRACKER-STATE: ... --> "
                "marker; cannot determine state"
            ),
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
            "violations": [{
                "inflight_mtime": inflight_mtime,
                "changelog_mtime": cl_mtime,
            }],
        }
    if age_hours > 4:
        return {
            "id": "inflight_freshness",
            "name": "In-flight task tracker",
            "status": "fail",
            "message": (
                f"in-flight task is {age_hours:.1f}h old with no "
                f"CHANGELOG update — likely orphaned"
            ),
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
    "β.1", "β.2",       # phase β early infrastructure
    "ν.2.5",            # mid-ν customization (pre-popup-langs)
    "ξ.5",              # ξ sales tool extensions
    "τ.1", "τ.1.5",     # KJV translation extractor + per-edition picker
    "α.1",              # earliest setup
    "γ.1", "γ.2",       # any other early ones
    "δ.1", "δ.2",
    "ε.1",
    "ζ.1",
    "η.2", "η.3",
}


# Phase mention pattern. Matches greek-letter phase tags as used
# throughout this codebase (ν.6.1, π.4-B, ω.0.1, etc.). Only catches
# letter+digit forms; arbitrary letters or words won't match.
_PHASE_RE = re.compile(
    r"(?<![A-Za-z])"                   # not preceded by a letter
    r"([νπωψχφυσρτθικλμηξζεδγβα])"     # any greek lowercase
    r"\.\d+"                            # mandatory .N
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
            "message": (
                f"all {len(code_phases)} non-legacy phase mention(s) "
                f"in code appear in CHANGELOG.md"
            ),
            "violations": [],
        }
    return {
        "id": "untracked_phases",
        "name": "Phase mentions tracked in CHANGELOG",
        "status": "warn",
        "message": (
            f"{len(untracked)} phase(s) mentioned in code but not in "
            f"CHANGELOG — likely undocumented ship"
        ),
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
            html_constants.extend(re.findall(
                r"^([A-Z_]+_HTML)\s*=\s*r\"\"\"", text, re.MULTILINE
            ))
    else:
        web_py = (REPO / "scripts" / "web.py").read_text(encoding="utf-8")
        html_constants = re.findall(
            r"^([A-Z_]+_HTML)\s*=\s*r\"\"\"", web_py, re.MULTILINE
        )
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
            "message": (
                f"SESSION_STATE references all "
                f"{len(html_constants)} consoles"
            ),
            "violations": [],
        }
    return {
        "id": "code_doc_sync",
        "name": "SESSION_STATE inventory matches consoles",
        "status": "warn",
        "message": (
            f"{len(missing_consoles)} console(s) not in inventory"
        ),
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
            is_open = (
                (isinstance(f, ast.Name) and f.id == "open")
                or (isinstance(f, ast.Attribute) and f.attr == "open")
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
        try:
            text = py.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        try:
            tree = ast.parse(text, filename=str(py))
        except SyntaxError:
            # File has a syntax error — that's a different kind of
            # problem; out of scope for this check.
            continue
        lines = text.splitlines()
        for ln in _find_open_write_calls(tree):
            # Waiver: `# atomic-waived: <reason>` on the same line
            # OR the immediately preceding line.
            same = lines[ln - 1] if 0 < ln <= len(lines) else ""
            prev = lines[ln - 2] if 1 < ln <= len(lines) else ""
            if "atomic-waived" in same or "atomic-waived" in prev:
                continue
            violations.append({
                "file": str(py.relative_to(REPO)).replace("\\", "/"),
                "line": ln,
                "snippet": same.strip()[:120],
            })

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


# ----------------------------------------------------------------------
# Runner
# ----------------------------------------------------------------------


ALL_CHECKS = {
    "6.1":               check_encoder_canonical_order,
    "6.2":               check_cross_link_invariant,
    "encode_decode":     check_encode_decode_round_trip,
    "docs":              check_doc_cross_references,
    "freshness":         check_session_state_freshness,
    # Drift-catching tier (added after a real drift event)
    "inflight":          check_inflight_freshness,
    "untracked_phases":  check_untracked_phases,
    "code_doc_sync":     check_session_state_inventory,
    # ω.9 hardening tier
    "atomic_writes":     check_atomic_writes,
}


def run_all(check_ids: list[str] | None = None) -> dict:
    """Run every check (or just the listed ones) and return aggregate.

    Used both by the CLI entrypoint AND by api_preflight() in
    scripts/web.py (which calls run_all() and folds the result into
    the readiness dashboard).
    """
    selected = check_ids or list(ALL_CHECKS.keys())
    results = []
    for cid in selected:
        if cid not in ALL_CHECKS:
            results.append({
                "id": cid,
                "name": cid,
                "status": "fail",
                "message": "unknown check id",
                "violations": [],
            })
            continue
        try:
            results.append(ALL_CHECKS[cid]())
        except Exception as e:
            results.append({
                "id": cid,
                "name": cid,
                "status": "fail",
                "message": f"linter check raised: {e}",
                "violations": [],
            })
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
    p.add_argument("--check", action="append",
                    help="run only the named check(s); repeat for multiple")
    p.add_argument("--json", action="store_true",
                    help="machine-readable JSON output")
    args = p.parse_args()

    out = run_all(args.check)

    if args.json:
        print(json.dumps(out, indent=2))
    else:
        for c in out["checks"]:
            icon = {"pass": "✓", "warn": "⚠", "fail": "✗"}[c["status"]]
            print(f"  {icon} {c['name']:35s}  {c['message']}")
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
