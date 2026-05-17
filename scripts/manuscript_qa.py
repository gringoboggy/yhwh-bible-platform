#!/usr/bin/env python3
"""manuscript_qa.py — Samuel Phase-2 dual-manuscript QA meta-tool (Unit E,
τ.6.x.4.b).

Composes the Phase-2 collation engine (Tasks 1-7) into a single
rules-§9 ``run_all() -> dict`` / ``main()`` meta-tool, mirroring
``scripts/lint_rules.py``. It verifies — on the immutable four
calibration chapters (1sa 1, 3, 17; 2sa 11) and the folio manifest —
that the reproducible Phase-2 invariant contract still holds and that
the engine's OWN agreement metrics sit at the design-spec §4 reference
bar.

What it does NOT do (spec-revision 2026-05-17 §3.2 R8): it never
asserts the engine's strict/skeleton/both-confident counts equal the
per-token human philological adjudication in the calibration goldens.
The ``engine_vs_hand_divergence`` check is informational — it surfaces
``manuscript_collation.engine_vs_hand_report()``'s honest
non-equality statement (which contains "intentionally differs") and
the per-chapter delta table, but reports rather than gates on it. A
sub-90% W↔W both-confident agreement is the EXPECTED signal for two
distinct recensions under the 2026-05-17 diplomatic-parallel GO — a
``warn`` with an explanatory message, never a ``fail``.

Checks emitted by ``run_all()``:

  witness_valid           validate_witness over every calibration
                          witness file (fail if any invalid).
  token_conservation      assert_token_conservation per calibration
                          collation (fail if any raises).
  calibration_contract    R1-R7 reproducible invariants over the 4
                          chapters (fail if any breaks).
  coverage                manifest calibrated-vs-pending tally across
                          1sa(1-31)+2sa(1-24); informational pass,
                          warn only if a 'calibrated' chapter lacks
                          GG or CAM folios.
  engine_metric_<ref>     one per 1sa1/1sa3/1sa17/2sa11 — the engine's
                          own metrics held to the §4 bar (fail ONLY if
                          semantic_pass_pct < 95 — the genuine
                          fabrication/incoherence floor; warn if
                          ww_agreement_bothconfident_pct < 90 OR
                          uncertainty_pct > 10 — both EXPECTED,
                          GO-ratified signals, each named in the
                          message as expected-not-a-failure; else
                          pass). The message ALWAYS states all three
                          numbers for transparency.
  engine_vs_hand_divergence
                          informational pass; message =
                          engine_vs_hand_report()'s honest divergence
                          statement (R8). Reports the delta; never
                          asserts equality.

Usage:

    python3 scripts/manuscript_qa.py            # run all checks
    python3 scripts/manuscript_qa.py --json     # machine-readable

Exits 0 when clean (no ``fail``), 1 on any ``fail``. Suitable for a
pre-commit gate and composed into ``/preflight`` via
``scripts/api/preflight.py`` (§9 meta-tool pattern).
"""

from __future__ import annotations

import argparse
import functools
import glob
import json
import os
import sys
from pathlib import Path

# Mirror the sibling §9 meta-tools (check_content.py / validate_schemas.py):
# put the repo root on sys.path at import so `python scripts/manuscript_qa.py`
# can import the `scripts.*` package directly (pytest gets this from the
# pyproject rootdir; a bare CLI invocation does not).
_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# ── design-spec §4 reference bar (the engine's OWN metrics, not hand) ──
#
# The authoritative bar is dev/CALIBRATION_2026-05-16-samuel-widened.md
# §3-4 (the document that produced the 2026-05-17 GO this whole arc
# cites). spec-revision rev.5 fixes exactly THREE engine-metric
# conditions, with exactly ONE of them a fail:
#   * "semantic high (≥95%)"            -> semantic_pass_pct floor;
#     the GENUINE fabrication/incoherence floor. Calibration is 100%
#     semantic on all four chapters, so any sub-95% is a real engine
#     regression. THIS, AND ONLY THIS, is a `fail`.
#   * "both-confident materially <90%"  -> the CONFIRM / distinct-
#     recension signal; an EXPECTED, GO-ratified `warn` (≥90% ~unity
#     would be the *refutation* to surface).
#   * uncertainty_pct > 10              -> ALSO an EXPECTED,
#     GO-ratified `warn` (rev.5), parallel to the W↔W warn.
#
# rev.5 — uncertainty_pct > 10 is now a VISIBLE `warn`, not buried in
# a pass/other message. The earlier build reported-not-gated it; the
# controller verified (2026-05-17) that the engine's uncertainty_pct
# is byte-identical to the immutable, GO'd hand goldens (1sa1 16.34% /
# 1sa3 10.09% / 1sa17 9.62% / 2sa11 10.38%; 3 of 4 > 10) and that
# design-spec §4's "uncertainty ≤ 10%" is a ONE-TIME calibration-GO
# bar (it FIRED its GO 2026-05-17) — NOT a per-build invariant. So
# uncertainty>10 must not `fail` (that would permanently red-flag
# three frozen reference chapters and 500-equivalent the preflight
# tile on ratified data — the "conservative-NO-GO refuted by real
# data" anti-pattern; see memory `no-reassert-ratified-bar`). But the
# project values honest visibility of divergence, so it is surfaced
# as a `warn` with an explanatory message rather than hidden inside a
# `pass`. Uncertainty honesty itself is enforced by the EXACT
# ⟦illegible⟧↔marker bijection in `witness_valid` /
# `calibration_contract` (§4 failure-mode 4), not a token-ratio
# ceiling; the warn just makes the (ratified) magnitude visible. The
# message always states all three numbers for the reader.
_SEMANTIC_PASS_FLOOR = 95.0  # semantic_pass_pct < this -> fail (the genuine floor)
_WW_BOTHCONFIDENT_FLOOR = 90.0  # ww_agreement_bothconfident_pct < this -> warn (expected: distinct recensions)
_UNCERTAINTY_WARN_CEIL = 10.0  # uncertainty_pct > this -> warn (rev.5; expected: MS-damage, GO-ratified)

# The four calibration chapters: (ref, golden-suffix, chapter, book).
# 1sa1's hand golden is the hi-res variant; the others are plain.
# The witness files are always <ref>_witnessGG.json + the hi-res CAM.
_CASES = (
    ("1sa1", "_collation_hires", 1, "1sa"),
    ("1sa3", "_collation", 3, "1sa"),
    ("1sa17", "_collation", 17, "1sa"),
    ("2sa11", "_collation", 11, "2sa"),
)

_CAL_DIR = os.path.join(str(_REPO), "content", "manuscript", "samuel", "calibration")


def _load_case(ref: str, suf: str):
    """Return (gg, cam, golden) dicts for one calibration ref. Pure
    ``json.load`` reads of the immutable reference; no writes."""
    with open(os.path.join(_CAL_DIR, f"{ref}_witnessGG.json"), encoding="utf-8") as fh:
        gg = json.load(fh)
    with open(os.path.join(_CAL_DIR, f"{ref}_witnessCAM_hires.json"), encoding="utf-8") as fh:
        cam = json.load(fh)
    with open(os.path.join(_CAL_DIR, f"{ref}{suf}.json"), encoding="utf-8") as fh:
        golden = json.load(fh)
    return gg, cam, golden


@functools.lru_cache(maxsize=None)
def _collate_case(ref: str, suf: str, ch: int, book: str):
    """Load + collate ONE calibration ref exactly once per process.

    Returns ``(gg, cam, golden, collation)`` for the ref. ``run_all()``
    fans the same four calibration chapters out across
    ``check_token_conservation`` (4×), ``check_calibration_contract``
    (4×) and ``_engine_metric_check`` (4×) — 12 QA-side
    load+``collate`` rounds over only 4 distinct, immutable inputs.
    Routing every one of those through this memoizer collapses the
    QA-side work to 4 collations (one per ref) and 4 JSON-read rounds,
    and makes every subsequent ``/preflight`` dashboard load reuse the
    process-lifetime result.

    This is the rules-§7.1 *project-internal published data* cache
    tier: the four calibration files
    (``content/manuscript/samuel/calibration/*``) are immutable,
    never edited by publishers / the customize console at runtime —
    updates ship via git + a process restart — so a process-lifetime
    ``@lru_cache`` keyed on ``(ref, suf, ch, book)`` is the §7.1
    singleton, mirroring ``manuscript_collation.load_kjv_skeleton``.

    CACHE-SAFETY CONTRACT: ``collate()`` returns a *mutable* dict and
    this cached tuple is now SHARED across all three consuming checks.
    Every consumer MUST treat ``gg`` / ``cam`` / ``golden`` /
    ``collation`` as READ-ONLY — read ``["metrics"]`` / ``["verses"]``
    / ``["alignment"]`` etc. for assertions only; never mutate, never
    ``.pop`` / in-place ``.sort`` / reassign nested structures. All
    three current consumers were audited and are read-only (their
    ``sorted(...)`` / list-comprehension expressions build NEW lists;
    ``assert_token_conservation`` only builds ``collections.Counter``
    views), so no defensive copy is required."""
    from scripts.core import manuscript_collation as mc

    gg, cam, golden = _load_case(ref, suf)
    collation = mc.collate(gg, cam, mc.load_kjv_skeleton(book, ch), book=book, chapter=ch)
    return gg, cam, golden, collation


# ----------------------------------------------------------------------
# Individual check implementations
# ----------------------------------------------------------------------


def check_witness_valid() -> dict:
    """Every calibration witness JSON must pass ``validate_witness``."""
    from scripts.core.manuscript_records import validate_witness

    violations: list[dict] = []
    files = sorted(glob.glob(os.path.join(_CAL_DIR, "*_witness*.json")))
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                d = json.load(fh)
            ok, errs = validate_witness(d)
        except Exception as e:  # noqa: BLE001 — a broken file is itself a violation
            ok, errs = False, [f"could not load/validate: {e}"]
        if not ok:
            violations.append(
                {
                    "file": os.path.basename(f),
                    "errors": errs[:5],
                }
            )
    n = len(files)
    if violations:
        offenders = ", ".join(v["file"] for v in violations)
        return {
            "id": "witness_valid",
            "name": "Calibration witness records valid",
            "status": "fail",
            "message": f"{len(violations)}/{n} calibration witness file(s) invalid: {offenders}",
            "violations": violations,
        }
    return {
        "id": "witness_valid",
        "name": "Calibration witness records valid",
        "status": "pass",
        "message": f"all {n} calibration witness file(s) valid",
        "violations": [],
    }


def check_token_conservation() -> dict:
    """``assert_token_conservation`` must hold for every calibration
    collation (the HARD Phase-2 build gate, re-checked here).

    READ-ONLY consumer of ``_collate_case``: only reads
    ``got["verses"]`` / ``gg`` / ``cam`` and hands them to
    ``assert_token_conservation`` (which builds ``Counter`` views
    only — no mutation)."""
    from scripts.core import manuscript_collation as mc

    violations: list[dict] = []
    for ref, suf, ch, book in _CASES:
        try:
            gg, cam, _, got = _collate_case(ref, suf, ch, book)
            mc.assert_token_conservation(got["verses"], gg, cam)
        except Exception as e:  # noqa: BLE001 — any raise is a conservation failure
            violations.append({"ref": ref, "error": str(e)[:200]})
    if violations:
        return {
            "id": "token_conservation",
            "name": "Token conservation (HARD gate) over calibration",
            "status": "fail",
            "message": (f"{len(violations)}/{len(_CASES)} calibration chapter(s) break token conservation"),
            "violations": violations,
        }
    return {
        "id": "token_conservation",
        "name": "Token conservation (HARD gate) over calibration",
        "status": "pass",
        "message": f"all {len(_CASES)} calibration chapter(s) conserve every evidence token",
        "violations": [],
    }


def check_calibration_contract() -> dict:
    """The R1-R7 reproducible invariants over the 4 calibration
    chapters (spec-revision 2026-05-17 §3.2). Specifically:

      - semantic_pass_basis reproduces the hand golden exactly (R3)
      - lacuna_counts reproduces the hand golden exactly (R4)
      - base == "CAM" 4/4, rationale cites the GO (R5)
      - metrics.definitions == DEFINITIONS, byte-stable (R6)
      - spine ascending (R7)
      - 1sa17 one-sided recensional cells are all 'disagree' (R7)

    R1/R2 are covered by their own dedicated checks
    (``witness_valid`` / ``token_conservation``); this check does NOT
    re-assert the hand-vs-engine agreement counts (that is R8 — the
    informational ``engine_vs_hand_divergence`` check).

    READ-ONLY consumer of ``_collate_case``: only reads
    ``golden["metrics"]`` / ``got["metrics"]`` /
    ``got["base_witness_recommended"]`` / ``got["base_rationale"]`` /
    ``got["verses"]`` / ``a["alignment"]`` for assertions. Its
    ``sorted(spine)`` and the one-sided list-comprehension build NEW
    lists — they never mutate ``got["verses"]`` in place."""
    from scripts.core import manuscript_collation as mc

    violations: list[dict] = []
    for ref, suf, ch, book in _CASES:
        try:
            _, _, golden, got = _collate_case(ref, suf, ch, book)
        except Exception as e:  # noqa: BLE001 — collation failure is a contract break
            violations.append({"ref": ref, "broke": f"collate raised: {e}"})
            continue
        gm = golden["metrics"]
        em = got["metrics"]
        if em["semantic_pass_basis"] != gm["semantic_pass_basis"]:
            violations.append(
                {
                    "ref": ref,
                    "broke": "R3 semantic_pass_basis",
                    "engine": em["semantic_pass_basis"],
                    "hand": gm["semantic_pass_basis"],
                }
            )
        if em["lacuna_counts"] != gm["lacuna_counts"]:
            violations.append(
                {
                    "ref": ref,
                    "broke": "R4 lacuna_counts",
                    "engine": em["lacuna_counts"],
                    "hand": gm["lacuna_counts"],
                }
            )
        if got["base_witness_recommended"] != "CAM":
            violations.append({"ref": ref, "broke": "R5 base!=CAM", "got": got["base_witness_recommended"]})
        if "GO" not in got["base_rationale"]:
            violations.append({"ref": ref, "broke": "R5 rationale missing GO citation"})
        if em["definitions"] != mc.DEFINITIONS:
            violations.append({"ref": ref, "broke": "R6 definitions not byte-stable"})
        spine = [v["v"] for v in got["verses"]]
        if spine != sorted(spine):
            violations.append({"ref": ref, "broke": "R7 spine not ascending"})
        for v in got["verses"]:
            for a in v["alignment"]:
                if a["class"].startswith("lacuna") and not (a["gg"] == mc.ILLEGIBLE or a["cam"] == mc.ILLEGIBLE):
                    violations.append({"ref": ref, "broke": f"R7 v{v['v']} lacuna w/o illegible"})
                    break
        if ref == "1sa17":
            one_sided = [a for v in got["verses"] for a in v["alignment"] if (a["gg"] == "") ^ (a["cam"] == "")]
            if not one_sided:
                violations.append({"ref": ref, "broke": "R7 1sa17 missing one-sided recensional cells"})
            elif not all(a["class"] == "disagree" for a in one_sided):
                violations.append({"ref": ref, "broke": "R7 1sa17 one-sided cell not 'disagree'"})
    if violations:
        return {
            "id": "calibration_contract",
            "name": "Calibration contract R1-R7 (reproducible invariants)",
            "status": "fail",
            "message": (f"{len(violations)} calibration-contract invariant(s) broken across the 4 chapters"),
            "violations": violations,
        }
    return {
        "id": "calibration_contract",
        "name": "Calibration contract R1-R7 (reproducible invariants)",
        "status": "pass",
        "message": (
            f"all R1-R7 reproducible invariants hold across the {len(_CASES)} "
            f"calibration chapters (semantic-pass + lacuna-counts reproduce "
            f"the hand goldens exactly; base=CAM 4/4; definitions byte-stable)"
        ),
        "violations": [],
    }


def check_coverage() -> dict:
    """Manifest calibrated-vs-pending tally across 1sa(1-31) +
    2sa(1-24) = 55 chapters. Informational ``pass`` (the book-wide
    roll-out is intentionally incremental). ``warn`` ONLY if a chapter
    marked ``calibrated`` is missing GG or CAM folios — that would be
    an inconsistent manifest, the one actionable defect here."""
    from scripts.core.manuscript_manifest import chapter_entry, load_manifest

    try:
        load_manifest.cache_clear()
        man = load_manifest()
    except Exception as e:  # noqa: BLE001 — unreadable manifest -> warn, never crash run_all
        return {
            "id": "coverage",
            "name": "Folio manifest coverage (1sa + 2sa)",
            "status": "warn",
            "message": f"manifest failed to load: {e}",
            "violations": [],
        }
    spans = (("1sa", 31), ("2sa", 24))
    calibrated = 0
    pending = 0
    total = 0
    inconsistent: list[dict] = []
    for book, n in spans:
        for ch in range(1, n + 1):
            total += 1
            e = chapter_entry(man, book, ch)
            status = e.get("status")
            if status == "calibrated":
                calibrated += 1
                gg_ok = bool((e.get("GG") or {}).get("folios"))
                cam_ok = bool((e.get("CAM") or {}).get("folios"))
                if not (gg_ok and cam_ok):
                    inconsistent.append(
                        {
                            "ref": f"{book}{ch}",
                            "gg_folios": gg_ok,
                            "cam_folios": cam_ok,
                        }
                    )
            else:
                pending += 1
    msg = f"{calibrated} calibrated / {pending} pending / {total} total"
    if inconsistent:
        return {
            "id": "coverage",
            "name": "Folio manifest coverage (1sa + 2sa)",
            "status": "warn",
            "message": (f"{msg}; {len(inconsistent)} 'calibrated' chapter(s) missing GG or CAM folios"),
            "violations": inconsistent,
        }
    return {
        "id": "coverage",
        "name": "Folio manifest coverage (1sa + 2sa)",
        "status": "pass",
        "message": msg,
        "violations": [],
    }


def _engine_metric_check(ref: str, suf: str, ch: int, book: str) -> dict:
    """One ``engine_metric_<ref>`` check — the engine's OWN metrics
    held to the design-spec §4 reference bar (semantics: rev.5).

      fail  iff semantic_pass_pct < 95 — the GENUINE
            fabrication/incoherence floor (calibration is 100%
            semantic on all four chapters, so sub-95% = a real
            engine regression). NOTHING ELSE FAILS.
      warn  (when not failing) iff ww_agreement_bothconfident_pct < 90
            OR uncertainty_pct > 10. BOTH are EXPECTED, GO-ratified
            signals; each fired condition is named in the message as
            expected-not-a-failure:
              · W↔W<90  — distinct recensions; the 2026-05-17 GO
                chose diplomatic-parallel.
              · unc>10  — MS-damage varies (§4 failure-mode-4); the
                2026-05-17 GO ratified these exact values; honesty is
                enforced by the ⟦illegible⟧↔marker bijection, not a
                token-ratio ceiling.
      pass  otherwise.

    rev.5 (memory ``no-reassert-ratified-bar``): uncertainty>10 USED
    to be reported-not-gated; it is now a VISIBLE ``warn`` (parallel
    to the W↔W warn) so the ratified divergence is honestly surfaced
    rather than buried inside a ``pass``/other message. It is NOT a
    ``fail`` — §4's "uncertainty ≤ 10%" is a one-time calibration-GO
    bar that already fired its GO 2026-05-17, not a per-build
    invariant; failing it would 500-equivalent the preflight tile on
    immutable GO'd data. See the module-level §4-bar comment.

    The message ALWAYS states all three numbers (semantic_pass,
    ww_agreement_bothconfident, uncertainty) regardless of status, for
    transparency.

    READ-ONLY consumer of ``_collate_case``: only reads
    ``got["metrics"]`` sub-keys (``semantic_pass_pct`` /
    ``uncertainty_pct`` / ``ww_agreement_bothconfident_pct``); never
    mutates the cached collation."""
    cid = f"engine_metric_{ref}"
    name = f"Engine metrics @ §4 bar — {ref}"
    try:
        _, _, _, got = _collate_case(ref, suf, ch, book)
        m = got["metrics"]
        sp = m["semantic_pass_pct"]
        unc = m["uncertainty_pct"]
        ww = m["ww_agreement_bothconfident_pct"]
    except Exception as e:  # noqa: BLE001 — engine raise is a hard fail for this chapter
        return {
            "id": cid,
            "name": name,
            "status": "fail",
            "message": f"engine raised on {ref}: {e}",
            "violations": [{"ref": ref, "error": str(e)[:200]}],
        }
    # All three numbers are ALWAYS in the message (transparency), no
    # matter the status.
    nums = f"semantic_pass={sp}% ww_agreement_bothconfident={ww}% uncertainty={unc}%"
    if sp < _SEMANTIC_PASS_FLOOR:
        return {
            "id": cid,
            "name": name,
            "status": "fail",
            "message": (
                f"{ref}: {nums} — design-spec §4 bar violated "
                f"(semantic_pass {sp}% < {_SEMANTIC_PASS_FLOOR}% — the "
                f"genuine fabrication/incoherence floor; calibration is "
                f"100% semantic on all four, so this is a real engine "
                f"regression)"
            ),
            "violations": [
                {
                    "ref": ref,
                    "broke": f"semantic_pass {sp}% < {_SEMANTIC_PASS_FLOOR}%",
                    "metrics": nums,
                }
            ],
        }
    # Not failing. Collect every EXPECTED, GO-ratified sub-bar signal
    # and name each one in the message (rev.5: uncertainty>10 is now a
    # VISIBLE warn parallel to W↔W<90, not buried in a pass message).
    reasons: list[str] = []
    if ww < _WW_BOTHCONFIDENT_FLOOR:
        reasons.append(
            f"W↔W <{_WW_BOTHCONFIDENT_FLOOR:.0f}% expected for distinct "
            f"recensions; the 2026-05-17 GO chose diplomatic-parallel — "
            f"not a failure"
        )
    if unc > _UNCERTAINTY_WARN_CEIL:
        reasons.append(
            f"self-flagged uncertainty >{_UNCERTAINTY_WARN_CEIL:.0f} is "
            f"expected (MS-damage varies per calibration-finding §4 "
            f"failure-mode-4; honesty is enforced by the ⟦illegible⟧↔"
            f"marker bijection in witness_valid/calibration_contract, "
            f"not a token-ratio ceiling); the 2026-05-17 GO ratified "
            f"these values — not a failure"
        )
    if reasons:
        return {
            "id": cid,
            "name": name,
            "status": "warn",
            "message": (
                f"{ref}: {nums} — " + "; ".join(reasons) + " (semantic_pass meets the §4 'semantic high' ≥95% "
                "genuine floor)"
            ),
            "violations": [],
        }
    return {
        "id": cid,
        "name": name,
        "status": "pass",
        "message": f"{ref}: {nums} — within the design-spec §4 bar",
        "violations": [],
    }


def check_engine_vs_hand_divergence() -> dict:
    """R8 (spec-revision 2026-05-17 §3.2) — informational ``pass``.

    Surfaces ``manuscript_collation.engine_vs_hand_report()``'s honest
    non-equality statement as the ``message`` (so it literally
    contains "intentionally differs") plus the per-chapter
    engine-vs-hand delta table as ``extra``. This REPORTS the delta;
    it never asserts engine == hand and never fails on disagreement —
    that non-equality is by design and already produced the
    2026-05-17 GO."""
    from scripts.core import manuscript_collation as mc

    try:
        rep = mc.engine_vs_hand_report()
        statement = rep["honest_divergence_statement"]
        table = rep["chapters"]
    except Exception as e:  # noqa: BLE001 — keep run_all robust; report can't gate
        return {
            "id": "engine_vs_hand_divergence",
            "name": "Engine-vs-hand divergence (R8, informational)",
            "status": "pass",
            "message": (f"engine_vs_hand_report() unavailable ({e}); informational only — not a gate"),
            "violations": [],
        }
    return {
        "id": "engine_vs_hand_divergence",
        "name": "Engine-vs-hand divergence (R8, informational)",
        "status": "pass",
        "message": statement,
        "violations": [],
        "extra": {"chapters": table},
    }


# ----------------------------------------------------------------------
# Runner (rules §9 shape — mirrors scripts/lint_rules.py:run_all/main)
# ----------------------------------------------------------------------


def _all_checks() -> list:
    """Ordered list of zero-arg check callables. ``engine_metric_<ref>``
    is one check per calibration chapter (4 separate entries)."""
    checks = [
        check_witness_valid,
        check_token_conservation,
        check_calibration_contract,
        check_coverage,
    ]
    for ref, suf, ch, book in _CASES:
        checks.append(lambda r=ref, s=suf, c=ch, b=book: _engine_metric_check(r, s, c, b))
    checks.append(check_engine_vs_hand_divergence)
    return checks


def run_all() -> dict:
    """Run every Phase-2 QA check and return the rules-§9 aggregate.

    Used both by the CLI ``main()`` and by ``/preflight``
    (``scripts/api/preflight.py`` composes this verdict into the
    readiness dashboard — §9 meta-tool pattern)."""
    results: list[dict] = []
    for fn in _all_checks():
        try:
            r = fn()
        except Exception as e:  # noqa: BLE001 — a check that raises is itself a fail
            r = {
                "id": getattr(fn, "__name__", "unknown"),
                "name": getattr(fn, "__name__", "unknown"),
                "status": "fail",
                "message": f"QA check raised: {e}",
                "violations": [],
            }
        results.append(r)
    summary = {
        "total": len(results),
        "pass": sum(1 for r in results if r["status"] == "pass"),
        "warn": sum(1 for r in results if r["status"] == "warn"),
        "fail": sum(1 for r in results if r["status"] == "fail"),
    }
    summary["clean"] = summary["fail"] == 0
    return {"checks": results, "summary": summary}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--json", action="store_true", help="machine-readable JSON output")
    args = p.parse_args(argv)

    out = run_all()
    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        for c in out["checks"]:
            icon = {"pass": "✓", "warn": "⚠", "fail": "✗"}[c["status"]]
            print(f"  {icon} {c['name']:46s}  {c['message']}")
            if c["violations"] and c["status"] != "pass":
                for v in c["violations"][:5]:
                    print(f"      · {v}")
                if len(c["violations"]) > 5:
                    print(f"      … and {len(c['violations']) - 5} more")
        s = out["summary"]
        verdict = "CLEAN" if s["clean"] else "VIOLATIONS"
        print(f"\n  {verdict}: {s['pass']} pass · {s['warn']} warn · {s['fail']} fail")

    return 0 if out["summary"]["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
