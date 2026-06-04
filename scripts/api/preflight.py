"""ω.35-B.7 — /preflight readiness dashboard, extracted from scripts/web.py.

Three pieces extracted as one cohesive unit:
- `api_preflight()` — thin public entry; computes file signatures and
  delegates to the cached inner.
- `_cached_preflight()` — @lru_cache wrapper keyed on mtime signatures
  so repeated dashboard reads are free between file edits.
- `_compute_preflight_uncached()` — the actual work: 10+ checks across
  attribution, covers, popup-translation coverage, publisher meta,
  kinds utilization, rules linter, schema validator, epubcheck,
  content-health, and routes inventory.

Adding a new check = appending to the `checks` list in
`_compute_preflight_uncached()` (and exposing the meta-tool that
produces it; see §9 "Add a meta-tool that integrates with the
preflight dashboard" in CLAUDE_PROJECT_RULES).

Status order: any "fail" → not-ready; otherwise it ships.

Lazy imports: `api_attribution_audit` and `api_covers` still live in
`scripts.web` (they aggregate matrix + corpus state that web.py owns).
The two `_files_signature` / `_notes_dir_signature` helpers also stay
in web.py — they're the canonical mtime probe shared by every cached
endpoint. Importing them inside the function keeps the new module
free of circular-import hazards at module load time.

Backward compatibility: re-exported from `scripts.web` so the route
table lambda (in `_SIMPLE_GET_ROUTES`) and any test that imports
`scripts.web.api_preflight` (or the cache helpers, for cache-clear)
keeps working.
"""

from __future__ import annotations

import functools
from pathlib import Path

from scripts.core import config

REPO = Path(__file__).resolve().parent.parent.parent


def api_preflight() -> dict:
    """Run every preflight check and return a structured dashboard
    payload (Phase ψ.2). Cached cheaply via the same mtime-keyed
    cache pattern as the other derived endpoints."""
    # Lazy import: _files_signature / _notes_dir_signature stay in
    # scripts.web (canonical home for the mtime-probe helpers).
    from scripts.web import _files_signature, _notes_dir_signature

    return _cached_preflight(
        _files_signature(REPO / "content" / "editions.yaml"),
        _files_signature(REPO / "content" / "books.yaml"),
        _files_signature(REPO / "content" / "kinds.yaml"),
        _files_signature(REPO / "content" / "categories.yaml"),
        _notes_dir_signature(),
    )


@functools.lru_cache(maxsize=4)
def _cached_preflight(eds_sig, books_sig, kinds_sig, cats_sig, notes_sig):
    return _compute_preflight_uncached()


def _compute_preflight_uncached() -> dict:  # noqa: C901 — Tier-3 aggregator: one branch per check is the intended shape
    # Lazy imports — api_attribution_audit + api_covers are still
    # in scripts.web; the other meta-tools are pure modules.
    from scripts.web import api_attribution_audit, api_covers
    from scripts.core import translations as _tx
    from scripts.core import matrix as _matrix

    checks: list[dict] = []
    editions = config.load_editions()
    mtx = _matrix.compute_matrix()

    # 1. Note attribution — direct reuse of the audit endpoint
    audit = api_attribution_audit()
    counts = audit.get("counts", {})
    miss = counts.get("missing", 0)
    thin = counts.get("thin", 0)
    total = counts.get("total", 0)
    if miss:
        status, msg = "fail", (f"{miss} note(s) have no attribution at all (of {total} total)")
    elif thin:
        status, msg = "warn", (f"{thin} note(s) have thin attribution (of {total} total)")
    else:
        status, msg = "pass", f"all {total} notes have attribution"
    checks.append(
        {
            "id": "attribution",
            "name": "Note attribution",
            "status": status,
            "message": msg,
            "details": (audit.get("needs_attention") or [])[:10],
            "jump_to": "/audit",
        }
    )

    # 2. Main covers — every edition has its main cover image set
    #    AND that file exists on disk
    #
    # τ.G.constitution.a (2026-05-20): standalone Bibles
    # (standalone-geez / standalone-amharic) are EXCLUDED from this
    # check. As of σ.5 (2026-06-04) they DO carry composed Ethiopic-script
    # covers, so the exclusion is now belt-and-suspenders (they'd pass) —
    # retained because their cover lives via the build_standalone path, not
    # the multi-tradition edition cover generator this check guards.
    standalone_ids = {e["id"] for e in editions if e.get("standalone")}
    covers = api_covers()
    no_main, broken_main = [], []
    for ed_rec in covers["editions"]:
        if ed_rec["edition_id"] in standalone_ids:
            continue
        path = ed_rec["main_cover"]["path"]
        meta = ed_rec["main_cover"]["meta"]
        if not path:
            no_main.append({"edition_id": ed_rec["edition_id"]})
        elif not meta:
            # Path is set but the file is missing from disk
            broken_main.append(
                {
                    "edition_id": ed_rec["edition_id"],
                    "path": path,
                }
            )
    if broken_main:
        status, msg = "fail", (f"{len(broken_main)} edition(s) have a cover_image path pointing at a missing file")
    elif no_main:
        status, msg = "warn", (f"{len(no_main)} edition(s) have no main cover set yet")
    else:
        status, msg = "pass", "every edition has a main cover image"
    checks.append(
        {
            "id": "covers_main",
            "name": "Main covers per edition",
            "status": status,
            "message": msg,
            "details": (broken_main + no_main)[:10],
            "jump_to": "/covers",
        }
    )

    # 3. Popup translation set per edition (warn-only — popup uses WEB
    #    when not set, which is acceptable but not ideal for a buyer)
    no_translation = [{"edition_id": e["id"]} for e in editions if not (e.get("popup_translation") or "").strip()]
    if not no_translation:
        status, msg = "pass", "every edition has a popup translation"
    else:
        status, msg = (
            "warn",
            (f"{len(no_translation)} edition(s) using default WEB for verse popups (no explicit translation chosen)"),
        )
    checks.append(
        {
            "id": "popup_translation",
            "name": "Popup translation per edition",
            "status": status,
            "message": msg,
            "details": no_translation[:10],
            "jump_to": "/customize",
        }
    )

    # 4. Popup translation coverage of the edition's canon
    #    For each edition with a popup_translation set, count how many
    #    of its canon books the translation actually covers
    coverage_issues = []
    for ed in editions:
        tx_id = (ed.get("popup_translation") or "").strip()
        if not tx_id:
            continue
        canon = mtx.edition_canon_books.get(ed["id"], set())
        missing = sorted(b for b in canon if not _tx.has_book(tx_id, b))
        if missing:
            coverage_issues.append(
                {
                    "edition_id": ed["id"],
                    "translation": tx_id,
                    "missing_count": len(missing),
                    "missing_books": missing[:20],
                }
            )
    total_missing = sum(c["missing_count"] for c in coverage_issues)
    if not coverage_issues:
        status, msg = "pass", ("every popup translation covers its edition's canon")
    else:
        status, msg = (
            "warn",
            (f"{total_missing} book(s) across {len(coverage_issues)} edition(s) have no popup translation data"),
        )
    checks.append(
        {
            "id": "popup_coverage",
            "name": "Popup translation coverage",
            "status": status,
            "message": msg,
            "details": coverage_issues[:10],
            "jump_to": "/customize",
        }
    )

    # 5. Per-book covers — informational. Not blocking; many editions
    #    legitimately ship with only a main cover.
    per_book_stats = []
    for ed_rec in covers["editions"]:
        total_slots = len(ed_rec["book_covers"])
        with_cover = sum(1 for s in ed_rec["book_covers"] if s.get("meta"))
        per_book_stats.append(
            {
                "edition_id": ed_rec["edition_id"],
                "set": with_cover,
                "total": total_slots,
            }
        )
    total_set = sum(s["set"] for s in per_book_stats)
    total_slots = sum(s["total"] for s in per_book_stats)
    msg = f"{total_set} of {total_slots} per-book cover slots filled"
    checks.append(
        {
            "id": "covers_per_book",
            "name": "Per-book covers (informational)",
            "status": "pass",  # never blocks ship
            "message": msg,
            "details": per_book_stats,
            "jump_to": "/covers",
        }
    )

    # 6. Publisher metadata — title at minimum for the OPF.
    # Ω.0 pivot (2026-05-14): ISBN no longer required; edition URN term-ref-ok
    # (urn:yhwh:edition:<id>) is auto-generated by build_edition.py.
    incomplete = []
    for ed in editions:
        missing_fields = [f for f in ("title",) if not (ed.get(f) or "").strip()]
        if missing_fields:
            incomplete.append(
                {
                    "edition_id": ed["id"],
                    "missing": missing_fields,
                }
            )
    if not incomplete:
        status, msg = "pass", ("every edition has a title set")
    else:
        status, msg = "warn", (f"{len(incomplete)} edition(s) missing title")
    checks.append(
        {
            "id": "publisher_meta",
            "name": "Publisher metadata",
            "status": status,
            "message": msg,
            "details": incomplete,
            "jump_to": "/publisher",
        }
    )

    # 7. Empty kinds — kinds in kinds.yaml that no note uses.
    #    Soft warn: hints at over-engineered taxonomy or missing apparatus.
    kinds = config.load_kinds()
    used_kinds: set[str] = set()
    # ψ.35-B2 — was: `for ed_id, by_kind in mtx.enabled.items()` reading
    # the raw projection dict directly. The accessor API gives the same
    # shape via per-edition `enabled_kinds_dict()`; iterating
    # `edition_canon_books` enumerates every known edition (a superset
    # of `mtx.enabled.keys()` since both are populated for every
    # edition in editions.yaml).
    for ed_id in mtx.edition_canon_books:
        for kind_code, count in mtx.enabled_kinds_dict(ed_id).items():
            if count > 0:
                used_kinds.add(kind_code)
    unused = sorted(k["code"] for k in kinds if k["code"] not in used_kinds)
    if not unused:
        status, msg = "pass", "every registered kind has at least one note"
    else:
        status, msg = "warn", (f"{len(unused)} kind(s) have zero notes across all editions")
    checks.append(
        {
            "id": "empty_kinds",
            "name": "Kind utilization",
            "status": status,
            "message": msg,
            "details": [{"kind_code": k} for k in unused[:20]],
            "jump_to": "/matrix",
        }
    )

    # 8. Rules compliance (Phase ω.0.1) — composes lint_rules.run_all()
    # so the readiness dashboard surfaces drift from §6.1 / §6.2 / etc.
    # the moment it appears, not at the next code review.
    try:
        from scripts.lint_rules import run_all as _lint_run_all

        lint = _lint_run_all()
        sub_fail = lint["summary"]["fail"]
        sub_warn = lint["summary"]["warn"]
        if sub_fail:
            status, msg = "fail", (f"{sub_fail} rule(s) violated, {sub_warn} warning(s)")
        elif sub_warn:
            status, msg = "warn", f"{sub_warn} rule warning(s)"
        else:
            status, msg = "pass", (f"all {lint['summary']['total']} project rules pass")
        # Surface the failing/warning sub-checks as the details list
        # so a publisher sees "what's wrong" without leaving the page.
        details = [
            {"rule_id": c["id"], "name": c["name"], "status": c["status"], "message": c["message"]}
            for c in lint["checks"]
            if c["status"] != "pass"
        ]
    except Exception as e:
        status = "warn"
        msg = f"rules linter failed to run: {e}"
        details = []
    checks.append(
        {
            "id": "rules_compliance",
            "name": "Rules compliance (§6.1, §6.2, encode/decode, docs)",
            "status": status,
            "message": msg,
            "details": details,
            "jump_to": "/preflight",  # nowhere better to jump — fix in code
        }
    )

    # 8b. Schema compliance (Phase ω.19.2) — composes
    # validate_schemas.run_all() so YAML schema drift surfaces
    # alongside the rules linter on every preflight read. Same
    # Tier-3 surface; same meta-tool composition pattern (§9 of
    # CLAUDE_PROJECT_RULES). Wrap import in try/except so a broken
    # validator can't 500 the dashboard.
    try:
        from scripts.validate_schemas import run_all as _schemas_run_all

        schemas = _schemas_run_all()
        s_summary = schemas["summary"]
        s_fail = s_summary.get("fail", 0)
        s_error = s_summary.get("error", 0)
        s_total = s_summary.get("total", 0)
        if s_fail or s_error:
            status, msg = "fail", (f"{s_fail} file(s) with schema violations, {s_error} unreadable")
        else:
            status, msg = "pass", (f"all {s_total} validated YAML file(s) pass schema")
        # Surface failing/erroring files with their first few errors
        # so a publisher sees what's wrong without leaving the page.
        details = [
            {
                "file": f["file"],
                "status": f["status"],
                "errors": (f.get("errors") or [])[:3],
                "record_count": f.get("record_count", 0),
            }
            for f in schemas["files"]
            if f["status"] != "ok"
        ]
    except Exception as e:
        status = "warn"
        msg = f"schema validator failed to run: {e}"
        details = []
    checks.append(
        {
            "id": "schema_compliance",
            "name": "Schema compliance (editions / kinds / canons / cross-refs)",
            "status": status,
            "message": msg,
            "details": details,
            "jump_to": "/preflight",
        }
    )

    # 9. epubcheck — W3C/IDPF EPUB validator (Phase ω.14)
    #    Runs against built EPUBs in exports/. The check stays
    #    informational when no EPUBs exist yet (info, not warn) so a
    #    fresh checkout doesn't show a red flag for "not validated".
    #    When Java is unavailable, surfaces as 'warn' with a clear
    #    install hint — the platform stays usable without it.
    try:
        from scripts.core import epubcheck as _ec

        ec_result = _ec.run_epubcheck_on_dir(REPO / "exports")
        ec_status = ec_result["status"]
        if ec_status == "pass":
            msg = f"all {ec_result['n_epubs']} EPUB(s) validate cleanly"
            details = []
        elif ec_status == "warn":
            t = ec_result["totals"]
            msg = f"epubcheck: {t['warnings']} warning(s) across {ec_result['n_epubs']} EPUB(s) (no errors)"
            details = [
                {
                    "epub": r["epub"],
                    "errors": r["errors"],
                    "warnings": r["warnings"],
                    "first_message": (r["messages"][0]["message"] if r["messages"] else ""),
                }
                for r in ec_result["results"]
                if r["status"] != "pass"
            ][:10]
        elif ec_status == "fail":
            t = ec_result["totals"]
            msg = f"epubcheck: {t['errors']} error(s), {t['warnings']} warning(s) across {ec_result['n_epubs']} EPUB(s)"
            details = [
                {
                    "epub": r["epub"],
                    "errors": r["errors"],
                    "warnings": r["warnings"],
                    "first_message": (r["messages"][0]["message"] if r["messages"] else ""),
                }
                for r in ec_result["results"]
                if r["status"] == "fail"
            ][:10]
        elif ec_status == "unavailable":
            # Java missing or JAR absent. Surface as warn with the
            # install hint; the rest of the platform stays usable.
            ec_status = "warn"
            msg = ec_result.get("explanation", "epubcheck unavailable")
            details = []
        else:  # 'empty'
            ec_status = "info"
            msg = ec_result.get(
                "explanation",
                "no built EPUBs to validate yet — run `python scripts/build_edition.py <id>`",
            )
            details = []
    except Exception as e:
        ec_status = "warn"
        msg = f"epubcheck check failed to run: {e}"
        details = []
    # The dashboard's status set is {pass, warn, fail}; map 'info'
    # to 'pass' for the summary tally but keep the message
    # informational so the UI can render it differently if it wants.
    summary_status = "pass" if ec_status == "info" else ec_status
    checks.append(
        {
            "id": "epubcheck",
            "name": "EPUB validation (W3C epubcheck)",
            "status": summary_status,
            "message": msg,
            "details": details,
            "jump_to": "/export",
        }
    )

    # 10. Content directory health (Phase ω.29) — composes
    # check_content.run_all() so corruption of notes/, translation
    # _meta.yaml, candidate JSON, or orphan note files surfaces
    # alongside the rules / schema linters. Wrap in try/except so a
    # broken checker can't 500 the dashboard. Same Tier-3 surface;
    # same meta-tool composition pattern (§9 of CLAUDE_PROJECT_RULES).
    try:
        from scripts.check_content import run_all as _content_run_all

        ch = _content_run_all()
        ch_summary = ch["summary"]
        ch_fail = ch_summary.get("fail", 0)
        ch_warn = ch_summary.get("warn", 0)
        ch_total = ch_summary.get("total", 0)
        if ch_fail:
            status, msg = "fail", (f"{ch_fail} content-health check(s) failed (of {ch_total})")
        elif ch_warn:
            status, msg = "warn", f"{ch_warn} content-health warning(s)"
        else:
            status, msg = "pass", f"all {ch_total} content-health check(s) pass"
        details = [
            {
                "check_id": c["id"],
                "name": c["name"],
                "status": c["status"],
                "message": c["message"],
                "first_violations": c["violations"][:3],
            }
            for c in ch["checks"]
            if c["status"] != "pass"
        ]
    except Exception as e:
        status = "warn"
        msg = f"content-health checker failed to run: {e}"
        details = []
    checks.append(
        {
            "id": "content_health",
            "name": "Content directory health (notes / translations / covers / candidates)",
            "status": status,
            "message": msg,
            "details": details,
            "jump_to": "/preflight",
        }
    )

    # ω.35-A — Routes inventory check. Auto-discovers routes in
    # do_GET / do_POST / do_PUT / do_DELETE; surfaces total count
    # and flags duplicate patterns / unanchored regexes / missing
    # methods. Wrap in try/except per the §9 mental model: a
    # broken meta-tool can't 500 the dashboard.
    try:
        from scripts import check_routes as _check_routes_mod

        cr = _check_routes_mod.run_all()
        cr_summary = cr.get("summary", {})
        if cr_summary.get("fail", 0) > 0:
            cr_status = "fail"
        elif cr_summary.get("warn", 0) > 0:
            cr_status = "warn"
        else:
            cr_status = "pass"
        cr_msg = (
            f"{cr.get('route_count', 0)} routes; "
            f"{cr_summary.get('pass', 0)}/{cr_summary.get('total', 0)} sub-checks pass"
        )
        cr_details = [
            {"id": c["id"], "name": c["name"], "status": c["status"], "message": c["message"]}
            for c in cr.get("checks", [])
            if c["status"] != "pass"
        ]
    except Exception as e:  # noqa: BLE001 — meta-tool failure must not break dashboard
        cr_status = "warn"
        cr_msg = f"routes inventory failed to run: {e}"
        cr_details = []
    checks.append(
        {
            "id": "routes_inventory",
            "name": "HTTP routes inventory (web.py do_GET / POST / PUT / DELETE)",
            "status": cr_status,
            "message": cr_msg,
            "details": cr_details,
            "jump_to": "/preflight",
        }
    )

    # 11. Samuel Phase-2 manuscript QA (τ.6.x.4.b, Unit E) — composes
    # manuscript_qa.run_all() so the dual-manuscript collation engine's
    # reproducible calibration contract + the engine's OWN §4-bar
    # metrics surface alongside the other Tier-3 meta-tools. Same §9
    # composition pattern as the rules / schema / content-health
    # checks above. Wrap in try/except so a broken QA tool renders a
    # warn, never 500s the dashboard. NOTE: a sub-90% W↔W both-
    # confident agreement is an EXPECTED `warn` for two distinct
    # recensions under the 2026-05-17 diplomatic-parallel GO — it is
    # not a ship-blocking fail.
    try:
        from scripts.manuscript_qa import run_all as _ms_run_all

        ms = _ms_run_all()
        ms_summary = ms.get("summary", {})
        ms_fail = ms_summary.get("fail", 0)
        ms_warn = ms_summary.get("warn", 0)
        ms_total = ms_summary.get("total", 0)
        if ms_fail:
            ms_status, ms_msg = "fail", (f"{ms_fail} manuscript-QA check(s) failed (of {ms_total})")
        elif ms_warn:
            ms_status, ms_msg = (
                "warn",
                (f"{ms_warn} manuscript-QA warning(s) — expected for distinct recensions (diplomatic-parallel GO)"),
            )
        else:
            ms_status, ms_msg = "pass", f"all {ms_total} manuscript-QA check(s) pass"
        ms_details = [
            {
                "check_id": c["id"],
                "name": c["name"],
                "status": c["status"],
                "message": c["message"],
            }
            for c in ms.get("checks", [])
            if c["status"] != "pass"
        ]
    except Exception as e:  # noqa: BLE001 — meta-tool failure must not break dashboard
        ms_status = "warn"
        ms_msg = f"manuscript QA failed to run: {e}"
        ms_details = []
    checks.append(
        {
            "id": "manuscript_qa",
            "name": "Samuel Phase-2 manuscript QA (calibration contract + engine §4-bar metrics)",
            "status": ms_status,
            "message": ms_msg,
            "details": ms_details,
            "jump_to": "/preflight",
        }
    )

    # 12. Accessibility audit (★C2.deadchecks wiring, 2026-05-24) — composes
    # check_a11y.run_all() so WCAG 2.1 AA / EPUB-Accessibility 1.1 issues
    # (missing page lang, image alt text, marker-colour contrast, heading-
    # level skips, presentational <b>/<i>) surface on the readiness dashboard.
    # It was a built-but-uninvoked "dead check". ERROR-severity → fail,
    # WARN-severity → warn. Pure read-only scan of epub_working — no
    # subprocess/network (unlike audit_dead_code/types/deps, which wrap
    # vulture/mypy/pip-audit and stay manual/CLI-only). Wrapped per the §9
    # meta-tool pattern so a broken checker warns, never 500s the dashboard.
    try:
        from scripts.check_a11y import run_all as _a11y_run_all

        a11y = _a11y_run_all()
        a_summary = a11y["summary"]
        a_fail = a_summary.get("fail", 0)
        a_warn = a_summary.get("warn", 0)
        a_total = a_summary.get("total", 0)
        if a_fail:
            a_status, a_msg = "fail", (f"{a_fail} accessibility check(s) failed (of {a_total})")
        elif a_warn:
            a_status, a_msg = "warn", f"{a_warn} accessibility warning(s)"
        else:
            a_status, a_msg = "pass", f"all {a_total} accessibility check(s) pass"
        a_details = [
            {"check_id": c["id"], "name": c["name"], "status": c["status"], "message": c["message"]}
            for c in a11y["checks"]
            if c["status"] != "pass"
        ]
    except Exception as e:  # noqa: BLE001 — meta-tool failure must not break dashboard
        a_status = "warn"
        a_msg = f"accessibility audit failed to run: {e}"
        a_details = []
    checks.append(
        {
            "id": "accessibility",
            "name": "Accessibility (WCAG 2.1 AA / EPUB Accessibility 1.1)",
            "status": a_status,
            "message": a_msg,
            "details": a_details,
            "jump_to": "/export",
        }
    )

    # 13. Cache-invalidation audit (ω.30 — composes audit_caches.audit()) so
    # @lru_cache sites without a documented clear path surface on the readiness
    # dashboard. It was a built-but-uninvoked "dead check" (mint-6 wired it). Pure
    # stdlib AST + re scan of scripts/ (no subprocess/network — unlike
    # audit_dead_code/types/deps, which wrap vulture/mypy/pip-audit and stay
    # manual/CLI-only). A cache without a clear path is a warn (a developer-review
    # signal), never a ship-blocker. Wrapped per the §9 meta-tool pattern so a
    # broken audit renders a warn, never 500s the dashboard.
    try:
        from scripts.audit_caches import audit as _audit_caches

        ac = _audit_caches()
        ac_summary = ac.get("summary", {})
        ac_total = ac_summary.get("total", 0)
        ac_no_clear = ac_summary.get("no_clear_path", 0)
        ac_clear = ac_summary.get("clear_path", 0)
        ac_wl = ac_summary.get("whitelisted", 0)
        if ac_no_clear:
            ac_status, ac_msg = (
                "warn",
                (
                    f"{ac_no_clear} @lru_cache(s) without a documented clear path "
                    f"(of {ac_total}) — add a cache_clear() site or whitelist"
                ),
            )
        else:
            ac_status, ac_msg = (
                "pass",
                f"all {ac_total} caches accounted for: {ac_clear} clear-path, {ac_wl} whitelisted",
            )
        ac_details = [
            {"func": c["func"], "file": c["file"], "line": c["line"]}
            for c in ac.get("caches", [])
            if c["status"] == "no_clear_path"
        ]
    except Exception as e:  # noqa: BLE001 — meta-tool failure must not break dashboard
        ac_status = "warn"
        ac_msg = f"cache-invalidation audit failed to run: {e}"
        ac_details = []
    checks.append(
        {
            "id": "cache_invalidation",
            "name": "Cache invalidation (ω.30 — @lru_cache clear paths)",
            "status": ac_status,
            "message": ac_msg,
            "details": ac_details,
            "jump_to": "/preflight",
        }
    )

    # Summary
    summary = {
        "total": len(checks),
        "pass": sum(1 for c in checks if c["status"] == "pass"),
        "warn": sum(1 for c in checks if c["status"] == "warn"),
        "fail": sum(1 for c in checks if c["status"] == "fail"),
    }
    summary["ready_to_ship"] = summary["fail"] == 0
    return {"checks": checks, "summary": summary}
