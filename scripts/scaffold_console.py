"""scaffold_console — generate a new console end-to-end.

A single command that creates every piece needed for a new console:

  1. <NAME>_HTML constant with standard chrome (Tailwind, header,
     cross-links to all existing consoles, UI defense prelude pre-
     injected, corpus-progress widget pre-wired)
  2. Route handler block (`/<route>` and `/<route>.html`) in do_GET
  3. `/<route>` link injected into every existing console's nav
     (uses scripts.bulk_inject)
  4. `route_for_constant` entry in scripts/lint_rules.py
  5. SESSION_STATE.md consoles-inventory line

Dry-run by default; --apply to actually write the changes. Refuses
to operate on a console name that already exists (idempotent guard).

Usage:
    python3 scripts/scaffold_console.py NAME --title "TITLE"
    python3 scripts/scaffold_console.py NAME --title "TITLE" --route /custom
    python3 scripts/scaffold_console.py NAME --title "TITLE" --apply

Phase ω.0.2 — saves ~30 min per new console; gets cheaper as more
consoles exist (every cross-link insertion was previously inline).
"""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

# Reuse the existing bulk-inject helper for nav cross-link rollout.
# This keeps "the way to add nav links to consoles" in one place.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import bulk_inject  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

# These are the file targets the scaffolder modifies. Keeping them
# as constants makes the dry-run plan self-documenting.
WEB_PY = REPO_ROOT / "scripts" / "web.py"
LINT_PY = REPO_ROOT / "scripts" / "lint_rules.py"
SESSION_STATE = REPO_ROOT / "dev" / "SESSION_STATE.md"
# Post-split (2026-05-07): each console's HTML constant lives in its
# own file under scripts/templates/. The scaffolder writes new
# constants there; web.py imports them.
TEMPLATES_DIR = REPO_ROOT / "scripts" / "templates"


class ScaffoldPlan(NamedTuple):
    """The output of dry-run mode — describes what would change.
    Tests and CLI both consume this."""

    name: str
    title: str
    route: str
    constant_name: str
    description: str | None
    target_file: Path
    will_create_constant: bool
    will_register_route: bool
    will_inject_nav: int  # count of consoles to inject /route into
    will_update_linter: bool
    will_update_session_state: bool
    skipped_reason: str | None  # non-None means scaffold won't run


def _normalize_name(raw: str) -> str:
    """Console names are lowercase, dash-separated. Reject anything
    that wouldn't be a valid Python identifier when uppercased."""
    n = (raw or "").strip().lower()
    if not n:
        raise ValueError("console name cannot be empty")
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", n):
        raise ValueError(
            f"console name {n!r} must start with a letter and contain only "
            f"lowercase letters, digits, dashes, or underscores"
        )
    return n


def _constant_name(name: str) -> str:
    """Convert dash-separated name to UPPER_SNAKE_HTML."""
    return name.replace("-", "_").upper() + "_HTML"


def _default_route(name: str) -> str:
    return "/" + name


def build_plan(
    name: str,
    title: str,
    *,
    route: str | None = None,
    description: str | None = None,
    target_file: Path | None = None,
) -> ScaffoldPlan:
    """Inspect the target file and decide what the scaffold would do.
    Pure (no I/O writes); safe to call ad hoc."""
    name = _normalize_name(name)
    title = (title or "").strip()
    if not title:
        raise ValueError("title is required")
    route = route or _default_route(name)
    if not route.startswith("/"):
        raise ValueError(f"route must start with /; got {route!r}")
    constant = _constant_name(name)
    target = target_file or WEB_PY

    if not target.is_file():
        return ScaffoldPlan(
            name=name,
            title=title,
            route=route,
            constant_name=constant,
            description=description,
            target_file=target,
            will_create_constant=False,
            will_register_route=False,
            will_inject_nav=0,
            will_update_linter=False,
            will_update_session_state=False,
            skipped_reason=f"target file does not exist: {target}",
        )

    existing = bulk_inject.list_constants(target)
    # Post-split: when targeting the real web.py (not a test fake),
    # also include constants from scripts/templates/ since that's
    # where they live now.
    if target == WEB_PY and TEMPLATES_DIR.is_dir():
        existing = list(set(existing) | set(bulk_inject.list_constants(TEMPLATES_DIR)))
    if constant in existing:
        return ScaffoldPlan(
            name=name,
            title=title,
            route=route,
            constant_name=constant,
            description=description,
            target_file=target,
            will_create_constant=False,
            will_register_route=False,
            will_inject_nav=0,
            will_update_linter=False,
            will_update_session_state=False,
            skipped_reason=(f"constant {constant} already exists; refusing to overwrite (idempotent guard)"),
        )

    # The scaffolder will inject /route into every NON-INDEX existing
    # console's nav. INDEX_HTML has different chrome and is exempt
    # (same convention as the UI defense prelude).
    inject_count = sum(1 for c in existing if c not in bulk_inject.DEFAULT_EXEMPT)

    only_target = target == WEB_PY
    return ScaffoldPlan(
        name=name,
        title=title,
        route=route,
        constant_name=constant,
        description=description,
        target_file=target,
        will_create_constant=True,
        will_register_route=True,
        will_inject_nav=inject_count,
        will_update_linter=only_target and LINT_PY.is_file(),
        will_update_session_state=only_target and SESSION_STATE.is_file(),
        skipped_reason=None,
    )


def render_constant(plan: ScaffoldPlan, *, existing_consoles: list[str]) -> str:
    """Build the HTML constant body. Standard chrome with self-bold
    nav link + cross-links to every other console + corpus widget +
    UI defense prelude markers (which a follow-on pass injects)."""
    nav_links = []
    for c in existing_consoles:
        if c == "INDEX_HTML":
            nav_links.append(("/", "note editor"))
            continue
        # Strip _HTML suffix and lowercase for both route and label
        stem = c[: -len("_HTML")].lower()
        nav_links.append(("/" + stem, stem))
    # Self-link (the new console)
    self_link = (plan.route, plan.name)

    # Build nav HTML; new console gets font-semibold, others get
    # text-blue-600 hover:underline (consistent with existing consoles)
    nav_parts = []
    for href, label in nav_links:
        nav_parts.append(f'    <a href="{href}" class="text-blue-600 hover:underline">{label}</a>')
    nav_parts.append(f'    <a href="{self_link[0]}" class="font-semibold">{self_link[1]}</a>')
    nav_block = "\n".join(nav_parts)

    desc_html = ""
    if plan.description:
        # Use single quotes inside the f-string to avoid interfering
        # with the surrounding HTML attribute quoting
        desc_html = f'\n    <p class="text-xs text-slate-500">{plan.description}</p>'

    return (
        f"\n\n# Phase ω.0.2 — generated by scripts/scaffold_console.py.\n"
        f"# Console: /{plan.name} ({plan.title})\n"
        f'{plan.constant_name} = r"""<!DOCTYPE html>\n'
        f'<html lang="en">\n'
        f"<head>\n"
        f'<meta charset="utf-8">\n'
        f"<title>E-Bible · {plan.title}</title>\n"
        f'<script src="https://cdn.tailwindcss.com"></script>\n'
        f"<style>\n"
        f'  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }}\n'
        f"</style>\n"
        f"</head>\n"
        f'<body class="bg-slate-50 text-slate-800">\n\n'
        f'<header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">\n'
        f"  <div>\n"
        f'    <h1 class="text-xl font-bold tracking-tight">{plan.title}</h1>'
        f"{desc_html}\n"
        f"  </div>\n"
        f'  <div class="flex items-center gap-4 text-xs">\n'
        f"{nav_block}\n"
        f'    <span id="corpus-progress" class="ml-auto text-xs text-slate-500" title="corpus depth toward the 35,000-note Ethiopian Tewahedo target">·· loading ··</span>\n'
        f"  </div>\n"
        f"</header>\n\n"
        f'<main class="max-w-7xl mx-auto px-6 py-6">\n'
        f"  <!-- TODO: scaffolded by ω.0.2 — replace with real content -->\n"
        f'  <section class="bg-white rounded-lg border border-slate-200 p-8 text-center">\n'
        f'    <p class="text-slate-400 italic">This {plan.name} console was scaffolded by\n'
        f"      <code>scripts/scaffold_console.py</code>. Add real content here.</p>\n"
        f"  </section>\n"
        f"</main>\n\n"
        f"<script>\n"
        f"// Phase ψ.3 — corpus progress widget. Cheap fetch + DOM update;\n"
        f"// silently no-ops on failure so a stale browser tab never breaks.\n"
        f"(function () {{\n"
        f"  fetch('/api/corpus-progress').then(function (r) {{ return r.json(); }})\n"
        f"    .then(function (d) {{\n"
        f"      var el = document.getElementById('corpus-progress');\n"
        f"      if (!el) return;\n"
        f"      var cur = (d.current || 0).toLocaleString();\n"
        f"      var tgt = (d.target || 0).toLocaleString();\n"
        f"      var pct = (typeof d.percent === 'number') ? d.percent.toFixed(1) : '0.0';\n"
        f"      el.textContent = cur + ' / ' + tgt + ' (' + pct + '%)';\n"
        f"    }})\n"
        f"    .catch(function () {{ /* swallow */ }});\n"
        f"}})();\n"
        f"</script>\n\n"
        f"</body>\n"
        f"</html>\n"
        f'"""\n'
    )


def render_route_block(plan: ScaffoldPlan) -> str:
    """The route handler chunk to insert in do_GET. Caller is
    responsible for finding the right insertion point."""
    return (
        f"\n        # Phase ω.0.2 — scaffolded route for /{plan.name}\n"
        f'        if path == "{plan.route}" or path == "{plan.route}.html":\n'
        f"            return self._send_html({plan.constant_name})\n"
    )


def apply_plan(
    plan: ScaffoldPlan,
    *,
    target_file: Path | None = None,
) -> dict:
    """Actually perform the scaffold. Returns a stats dict
    documenting what changed. No-op if plan.skipped_reason is set.

    Post-split (2026-05-07): when targeting the real web.py, the new
    HTML constant is written to scripts/templates/<name>.py and an
    import is added to web.py. When targeting another file (tests),
    constant lands inline as before for back-compat."""
    if plan.skipped_reason:
        return {"applied": False, "reason": plan.skipped_reason}
    target = target_file or plan.target_file

    text = target.read_text()
    # Existing constants for the cross-link list — check both inline
    # and templates/ to support pre- and post-split layouts.
    existing = bulk_inject.list_constants(target)
    if TEMPLATES_DIR.is_dir() and target == WEB_PY:
        existing = sorted(set(existing) | set(bulk_inject.list_constants(TEMPLATES_DIR)))

    # Path 1 (post-split, real web.py): write constant to templates/
    constant_block = render_constant(plan, existing_consoles=existing)
    use_templates_dir = TEMPLATES_DIR.is_dir() and target == WEB_PY
    if use_templates_dir:
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        template_path = TEMPLATES_DIR / f"{plan.name.replace('-', '_')}.py"
        template_path.write_text(
            f'"""HTML for /{plan.name} console — scaffolded by ω.0.2.\n'
            f"\n"
            f"Re-imported by scripts/web.py for back-compat with\n"
            f"`from scripts.web import {plan.constant_name}` callers.\n"
            f'"""\n'
            f"\n"
            f"{constant_block}\n",
            encoding="utf-8",
        )
        # Add import at top of web.py's existing template imports block.
        # Find the marker comment we know is there from the split.
        import_line = f"from scripts.templates.{plan.name.replace('-', '_')} import {plan.constant_name}\n"
        # Find an existing template import line to anchor against
        existing_imports = re.search(
            r"^from scripts\.templates\.\w+ import \w+_HTML$",
            text,
            re.MULTILINE,
        )
        if existing_imports:
            # Insert in alphabetical position. Simple approach: prepend
            # before the first existing import (caller can re-sort later).
            text = text[: existing_imports.start()] + import_line + text[existing_imports.start() :]
        else:
            # Fallback: append after standard imports
            text = text.replace(
                "import webbrowser\n",
                f"import webbrowser\n{import_line}",
                1,
            )
    else:
        # Path 2 (legacy / test target): append constant inline
        main_match = re.search(r"\ndef main\(\)", text)
        if main_match:
            ins = main_match.start()
            text = text[:ins] + constant_block + "\n\n" + text[ins:]
        else:
            text = text.rstrip() + "\n" + constant_block

    # 2. Find the do_GET method and inject the route block before
    #    the first `if path ==` line in it. Simpler heuristic:
    #    insert before the existing `/api/corpus-progress` route
    #    (which exists in this file) — that keeps generated routes
    #    near other read-only ones.
    route_block = render_route_block(plan)
    if 'if path == "/api/corpus-progress"' in text:
        text = text.replace(
            '        if path == "/api/corpus-progress"',
            route_block + '        if path == "/api/corpus-progress"',
            1,
        )
    target.write_text(text)

    # 3. Inject the new nav link into every existing non-exempt
    #    console. Post-split: target is templates/ directory.
    nav_link = f'<a href="{plan.route}" class="text-blue-600 hover:underline">{plan.name}</a>\n    '
    nav_target = TEMPLATES_DIR if use_templates_dir else target
    inj = bulk_inject.insert(
        nav_target,
        nav_link,
        before=f'<span id="corpus-progress"',
        marker=f'href="{plan.route}"',
    )

    stats = {
        "applied": True,
        "constant_added": plan.constant_name,
        "route_added": plan.route,
        "nav_injected_into": inj["modified"],
        "nav_skipped": inj["skipped"],
    }

    # 4. Update lint_rules.py route_for_constant table (only when
    #    operating on the real web.py)
    if plan.will_update_linter and LINT_PY.is_file():
        lint_text = LINT_PY.read_text()
        # Find the route_for_constant dict and add the new entry
        pat = re.compile(
            r'(route_for_constant\s*=\s*\{[^}]*?)("PREFLIGHT_HTML"\s*:\s*"/preflight"\s*,\s*\n)',
            re.DOTALL,
        )
        new_entry = f'        "{plan.constant_name}": "{plan.route}",\n'
        if pat.search(lint_text) and plan.constant_name not in lint_text:
            lint_text = pat.sub(r"\1\2" + new_entry, lint_text, count=1)
            LINT_PY.write_text(lint_text)
            stats["linter_updated"] = True
        else:
            stats["linter_updated"] = False

    # 5. Update SESSION_STATE.md consoles inventory
    if plan.will_update_session_state and SESSION_STATE.is_file():
        ss_text = SESSION_STATE.read_text()
        marker = "  /preflight pre-ship readiness dashboard"
        new_line = f"  {plan.route}{' ' * (10 - len(plan.route))} {plan.title.lower()}"
        if marker in ss_text and plan.route not in ss_text:
            ss_text = ss_text.replace(marker, marker + "\n" + new_line, 1)
            SESSION_STATE.write_text(ss_text)
            stats["session_state_updated"] = True
        else:
            stats["session_state_updated"] = False

    return stats


def format_plan_report(plan: ScaffoldPlan) -> str:
    """Human-readable dry-run output."""
    lines = [
        f"Console scaffold plan",
        f"=" * 50,
        f"  name:           {plan.name}",
        f"  title:          {plan.title}",
        f"  route:          {plan.route}",
        f"  constant name:  {plan.constant_name}",
        f"  target file:    {plan.target_file}",
        f"",
    ]
    if plan.skipped_reason:
        lines.append(f"  STATUS: WILL NOT RUN")
        lines.append(f"  reason: {plan.skipped_reason}")
    else:
        lines.append(f"  STATUS: READY (--apply to commit)")
        lines.append(f"")
        lines.append(f"  Will:")
        if TEMPLATES_DIR.is_dir() and plan.target_file == WEB_PY:
            constant_dest = f"scripts/templates/{plan.name.replace('-', '_')}.py"
        else:
            constant_dest = plan.target_file.name
        lines.append(
            f"    [{('x' if plan.will_create_constant else ' ')}] create {plan.constant_name} constant in {constant_dest}"
        )
        lines.append(f"    [{('x' if plan.will_register_route else ' ')}] register route {plan.route}")
        lines.append(
            f"    [{('x' if plan.will_inject_nav > 0 else ' ')}] inject nav link into {plan.will_inject_nav} existing console(s)"
        )
        lines.append(f"    [{('x' if plan.will_update_linter else ' ')}] update lint_rules.py route_for_constant table")
        lines.append(
            f"    [{('x' if plan.will_update_session_state else ' ')}] update SESSION_STATE.md consoles inventory"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a new web console end-to-end.",
    )
    parser.add_argument("name", help="console name (lowercase, e.g. 'ops', 'dashboard')")
    parser.add_argument("--title", required=True, help='display title (e.g. "Operator Dashboard")')
    parser.add_argument("--route", default=None, help="URL route (default: /<name>)")
    parser.add_argument("--description", default=None, help="optional one-line description below the title")
    parser.add_argument("--target", type=Path, default=None, help="target Python file (default: scripts/web.py)")
    parser.add_argument("--apply", action="store_true", help="actually write changes (default: dry-run)")
    args = parser.parse_args(argv)

    try:
        plan = build_plan(
            args.name,
            args.title,
            route=args.route,
            description=args.description,
            target_file=args.target,
        )
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    print(format_plan_report(plan))

    if plan.skipped_reason:
        return 1
    if not args.apply:
        print()
        print("(dry-run; pass --apply to commit)")
        return 0

    stats = apply_plan(plan, target_file=args.target)
    print()
    print("APPLIED:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
