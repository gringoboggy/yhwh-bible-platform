"""ω.35-B.6 — exports/build API handlers, extracted from scripts/web.py.

Four handlers for the σ.1/σ.2 + ω.2 export-and-build surface:
- api_export_preview (read-only — pre-flight summary)
- api_export_build (mutation — runs build_edition.py subprocess;
  audit-logged)
- api_build_all_editions (mutation — composes per-edition build;
  packages successful EPUBs into one zip; audit-logged)
- api_download_export (read — streams a built EPUB or zip from disk;
  filename-pattern-validated)

Plus the module-level constant `EXPORTS_DIR` that anchors every
write target. Re-exported from web.py for tests that may
monkeypatch the location.

Backward compatibility: scripts/web.py re-imports all 5 names so
route-table lambdas and existing tests work unchanged.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from scripts.core import audit_log, config, paths

REPO = Path(__file__).resolve().parent.parent.parent
# Frozen-aware write anchor: paths.exports_dir() resolves to a writable,
# PERSISTENT per-user dir when frozen (YHWH_DATA_DIR override, else
# user_data_root), and to <repo>/exports in dev — keeping built EPUBs out of
# the ephemeral PyInstaller _MEIPASS dir so they survive app exit. Tests may
# monkeypatch this module attribute to redirect writes.
EXPORTS_DIR = paths.exports_dir()


def api_export_preview(edition_id: str) -> dict:
    """Pre-flight summary of what shipping `edition_id` will produce.

    The user-facing pitch: 'before you click Export, here's exactly
    what you're about to get — books, notes, kinds, file overview.'
    Powered by the matrix layer (μ.0) so counts are guaranteed
    consistent with what the build will actually emit.
    """
    from scripts.core import matrix as matrix_mod

    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}
    edition = eds[edition_id]

    m = matrix_mod.compute_matrix()
    # ψ.35-B2 — was: `m.enabled.get(edition_id, {})` / `m.potential.get(edition_id, {})`.
    # `enabled_kinds_dict` / `potential_kinds_dict` derive from the
    # canonical per_chapter store and isolate this consumer from the
    # upcoming projection-field removal in ψ.35-Final.
    enabled = m.enabled_kinds_dict(edition_id)
    potential = m.potential_kinds_dict(edition_id)
    canon_books = m.edition_canon_books.get(edition_id, set())
    enabled_kinds = m.edition_enabled_kinds.get(edition_id, set())

    breakdown = matrix_mod.breakdown_by_category(edition_id)
    cats_idx = config.categories_by_id()
    cat_breakdown = []
    for cid in sorted(breakdown, key=lambda x: -breakdown[x]):
        c = cats_idx.get(cid, {})
        cat_breakdown.append(
            {
                "id": cid,
                "label": c.get("label", cid),
                "symbol": c.get("symbol", "?"),
                "count": breakdown[cid],
            }
        )

    filtered_out_kinds = []
    for kind_code, n in potential.items():
        if n > 0 and enabled.get(kind_code, 0) == 0:
            filtered_out_kinds.append({"kind": kind_code, "count": n})
    filtered_out_kinds.sort(key=lambda x: -x["count"])

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pattern = f"Ethiopian_Bible_{edition_id}_*.epub"
    existing = sorted(EXPORTS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    last_build = None
    if existing:
        f = existing[0]
        st = f.stat()
        last_build = {
            "filename": f.name,
            "size_kb": round(st.st_size / 1024),
            "mtime": st.st_mtime,
        }

    return {
        "edition": {
            "id": edition_id,
            "title": edition.get("title", edition_id),
            "short_title": edition.get("short_title", edition_id),
            "canon": edition.get("canon"),
            # Ω.0 pivot (2026-05-14): isbn dropped — front-ends derive term-ref-ok
            # the edition URN (urn:yhwh:edition:<id>) client-side.
            "target_audience": edition.get("target_audience", ""),
            "notes_field": edition.get("notes", ""),
        },
        "summary": {
            "books": len(canon_books),
            "kinds_enabled": len(enabled_kinds),
            "kinds_total": len(config.load_kinds()),
            "notes_shipping": sum(enabled.values()),
            "notes_potential": sum(potential.values()),
        },
        "category_breakdown": cat_breakdown,
        "filtered_out_kinds": filtered_out_kinds[:10],
        "last_build": last_build,
    }


@audit_log.audit_endpoint(action="export_build")
def api_export_build(edition_id: str, version: str = "v28a") -> dict:
    """Run the build pipeline for `edition_id` and return a downloadable
    file reference. Wraps scripts/build_edition.py as a subprocess —
    same CLI tool that produces the actual retail EPUBs, so the buyer
    gets exactly what would ship in the existing pipeline.

    Build is synchronous (typically 10-30 seconds); the HTTP request
    blocks until the EPUB is ready or fails.

    ε.1 — emits `build_start` / `build_complete` / `build_failure`
    events to the event log so a future dashboard can roll up
    build cadence + success rate. emit() failures are swallowed so a
    misconfigured event log can't break the build pipeline itself.
    """
    from scripts.core import event_log

    def _safe_emit(kind, **fields):
        try:
            event_log.emit(kind, **fields)
        except Exception:
            # Best-effort logging — never block the build path on
            # event-log issues.
            pass

    if edition_id not in config.editions_by_id():
        _safe_emit("build_failure", edition_id=edition_id, reason="unknown_edition")
        return {"error": f"unknown edition: {edition_id}"}
    _safe_emit("build_start", edition_id=edition_id, version=version)

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    import subprocess

    # Phase ω.20-B — drop the legacy `--force` so build_one's
    # content-addressable cache (ω.20-A) can short-circuit a rebuild
    # when no inputs have changed. Identical buyer-facing artifact;
    # ~30-90s saved per untouched edition. A future ω.20-C can surface
    # cache_hit in the response payload via a stats sidecar.
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "build_edition.py"),
        edition_id,
        "--output-dir",
        str(EXPORTS_DIR),
        "--version",
        version,
    ]
    # ξ.16 SEC-006 — bound build time so a stuck build_edition.py
    # (origin-fetch hang, malformed input loop, runaway disk write)
    # doesn't pin the only HTTP thread indefinitely. 5-minute cap is
    # generous: a full clean build of the largest edition completes
    # in ~90s on dev hardware. Cache-hit builds finish in seconds.
    # Operator override via YHWH_BUILD_TIMEOUT_SECONDS for unusual
    # hardware.
    import os as _os

    try:
        timeout_s = int(_os.environ.get("YHWH_BUILD_TIMEOUT_SECONDS") or "300")
    except ValueError:
        timeout_s = 300
    if getattr(sys, "frozen", False):
        # Frozen binary: sys.executable is the launcher (YHWH.exe), not a Python
        # interpreter, so the subprocess CLI re-invocation can't run (the
        # launcher's argparse rejects the build_edition.py script path). Build
        # IN-PROCESS instead — build_one runs build_epub in-process too when
        # frozen (see build_edition.py). The subprocess timeout doesn't apply;
        # a single-edition build is bounded by the corpus size.
        from scripts import build_edition as _be

        proc = None
        try:
            _be.build_one(edition_id, EXPORTS_DIR, version, config.load_kinds(), False, False)
        except BaseException as e:  # incl. SystemExit from any build_epub.err() path
            _safe_emit("build_failure", edition_id=edition_id, reason="in_process_exception")
            return {"error": "build failed", "returncode": 1, "stderr": str(e)[-2000:]}
    else:
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(REPO),
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired as e:
            _safe_emit("build_failure", edition_id=edition_id, reason="timeout", timeout_seconds=timeout_s)
            return {
                "error": "build timed out",
                "code": "build_timeout",
                "http": 504,
                "timeout_seconds": timeout_s,
                "stderr": (e.stderr or b"")[-2000:].decode("utf-8", errors="replace")
                if isinstance(e.stderr, bytes)
                else (e.stderr or "")[-2000:],
            }
        if proc.returncode != 0:
            _safe_emit("build_failure", edition_id=edition_id, reason="nonzero_exit", returncode=proc.returncode)
            return {
                "error": "build failed",
                "returncode": proc.returncode,
                "stderr": proc.stderr[-2000:] if proc.stderr else "",
                "stdout_tail": proc.stdout[-500:] if proc.stdout else "",
            }

    pattern = f"Ethiopian_Bible_{edition_id}_{version}_*.epub"
    candidates = sorted(EXPORTS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        _safe_emit("build_failure", edition_id=edition_id, reason="no_epub_found")
        return {"error": "build reported success but no EPUB found"}

    out = candidates[0]
    st = out.stat()
    response = {
        "ok": True,
        "filename": out.name,
        "size_kb": round(st.st_size / 1024),
        "size_mb": round(st.st_size / 1024 / 1024, 2),
        "download_url": f"/api/export/download/{out.name}",
        "build_log_tail": proc.stdout[-300:] if (proc and proc.stdout) else "",
    }

    # Phase ω.20-C — fold the build_one stats sidecar into the response
    # so the UI can render a "served from cache (instant)" vs
    # "rebuilt (took 23s)" badge. Sidecar lives at <out>.stats.json,
    # written by `_write_stats_sidecar` in build_edition.py. Missing /
    # corrupt sidecar degrades silently — the EPUB is the contract;
    # the badge fields are nice-to-have.
    sidecar = out.with_suffix(out.suffix + ".stats.json")
    if sidecar.is_file():
        try:
            import json as _json

            data = _json.loads(sidecar.read_text(encoding="utf-8"))
            for field in ("cache_hit", "skipped", "build_seconds"):
                if field in data:
                    response[field] = data[field]
        except Exception:
            pass

    _safe_emit(
        "build_complete",
        edition_id=edition_id,
        version=version,
        filename=out.name,
        size_mb=response.get("size_mb"),
        cache_hit=response.get("cache_hit"),
        build_seconds=response.get("build_seconds"),
    )
    return response


# Phase ω.2 — Build-all-editions one-click. The buyer-demo arc:
# "click two buttons, get all your customized Bibles." Composes
# api_export_build per edition, collects results, packages successful
# EPUBs into a single zip. Per-edition errors don't abort the batch
# (spec requirement) — partial success is a real outcome and the
# UI surfaces which editions made it.
#
# Pattern: pure-function-API + thin route adapter (6th instance —
# §9 codification well overdue at this point).


@audit_log.audit_endpoint(action="build_all_editions")
def api_build_all_editions(
    *,
    version: str = "v28a",
    build_one=None,
) -> dict:
    """Build every configured edition, package successful outputs
    into a single combined zip, return per-edition status.

    Args:
        version: build version tag (passed through to build_one)
        build_one: callable(edition_id, version=...) → dict
                    Defaults to api_export_build. Tests inject a
                    mock to avoid real subprocess builds.

    Returns:
        {
          "ok": bool,                          # all editions succeeded?
          "zip_filename": str | None,          # combined zip name (None if 0 succeeded)
          "zip_size_mb": float | None,
          "download_url": str | None,
          "success_count": int,
          "fail_count": int,
          "total_count": int,
          "per_edition": [
            {"edition_id": str, "ok": bool, "filename": str | None,
             "size_mb": float | None, "error": str | None},
            ...
          ],
        }
    """
    if build_one is None:
        build_one = api_export_build

    eds = config.load_editions()
    edition_ids = [e["id"] for e in eds]

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    per_edition: list[dict] = []
    successful_files: list[Path] = []

    for ed_id in edition_ids:
        try:
            result = build_one(ed_id, version=version)
        except Exception as e:
            # Defensive: if build_one itself raises (e.g. internal
            # bug), log and continue. Don't abort the batch.
            per_edition.append(
                {
                    "edition_id": ed_id,
                    "ok": False,
                    "filename": None,
                    "size_mb": None,
                    "error": f"exception: {type(e).__name__}: {e}",
                }
            )
            continue
        if result.get("ok"):
            per_edition.append(
                {
                    "edition_id": ed_id,
                    "ok": True,
                    "filename": result.get("filename"),
                    "size_mb": result.get("size_mb"),
                    "error": None,
                }
            )
            fp = EXPORTS_DIR / result.get("filename", "")
            if fp.is_file():
                successful_files.append(fp)
        else:
            per_edition.append(
                {
                    "edition_id": ed_id,
                    "ok": False,
                    "filename": None,
                    "size_mb": None,
                    "error": result.get("error", "build failed"),
                }
            )

    success_count = sum(1 for p in per_edition if p["ok"])
    fail_count = len(per_edition) - success_count

    # Package successful EPUBs into one zip. If zero succeeded,
    # skip — the UI shows the per-edition error list.
    zip_filename = None
    zip_size_mb = None
    download_url = None
    if successful_files:
        import zipfile
        from datetime import datetime, timezone

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        zip_name = f"All_Editions_{version}_{ts}.zip"
        zip_path = EXPORTS_DIR / zip_name
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fp in successful_files:
                zf.write(fp, arcname=fp.name)
        st = zip_path.stat()
        zip_filename = zip_name
        zip_size_mb = round(st.st_size / 1024 / 1024, 2)
        download_url = f"/api/export/download/{zip_name}"

    return {
        "ok": fail_count == 0 and success_count > 0,
        "zip_filename": zip_filename,
        "zip_size_mb": zip_size_mb,
        "download_url": download_url,
        "success_count": success_count,
        "fail_count": fail_count,
        "total_count": len(edition_ids),
        "per_edition": per_edition,
    }


def api_download_export(filename: str) -> tuple[bytes, str] | dict:
    """Read a built export file from disk for streaming to the browser.

    Returns (bytes, mime) on success, or {"error": ...} on failure.
    Validates that the filename matches the expected build pattern so
    we never serve files outside the exports dir.
    """
    if not re.match(r"^Ethiopian_Bible_[a-z0-9-]+_[a-z0-9]+_[\dT\-:Z]+\.epub$", filename):
        return {"error": "invalid export filename"}
    path = EXPORTS_DIR / filename
    if not path.is_file():
        return {"error": "file not found"}
    return (path.read_bytes(), "application/epub+zip")
