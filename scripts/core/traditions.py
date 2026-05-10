"""
traditions.py — Closed set of denominational traditions for the
cross-denominational compare apparatus (Phase ψ.8).

Public API:
    CANONICAL_TRADITIONS              tuple of (id, label) pairs in
                                       canonical popup-stack order
    TRADITION_IDS                     frozenset of valid tradition ids
    DEFAULT_TRADITION                 "cross" (denominationally neutral)
    valid_tradition(s)                bool — is `s` a known tradition?
    note_tradition(tup)               str  — derived tradition for a note
    edition_to_tradition(edition_id)  str  — lookup; default = DEFAULT_TRADITION
    load_traditions_yaml(path=None)   dict — parsed traditions.yaml

Scope of ψ.8.0 (this module):
    Constants + resolver + edition→tradition lookup + YAML loader.
    No build-pipeline integration. No UI. No editions.yaml schema
    field. Those land in ψ.8.1 / ψ.8.2 / ψ.8.3 as a single batch
    once the foundation here is stable.

The tradition axis is opt-in by design. Editions that don't declare
a `traditions_default` (added in ψ.8.1) build byte-identical to
pre-ψ.8 outputs — see CLAUDE_PROJECT_RULES §7.2 (additive-by-default).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_TRADITIONS_YAML = _REPO_ROOT / "content" / "traditions.yaml"


def _traditions_yaml_path() -> Path:
    """ω.5 paths-resolver entrypoint. Existing ``DEFAULT_TRADITIONS_YAML``
    constant is preserved for back-compat; new call sites should
    prefer this function so they pick up dev/installed/test-override
    resolution automatically."""
    from . import paths

    return paths.traditions_yaml()


# CANONICAL_TRADITIONS is the **ordered** list used in popup rendering
# (ψ.8.2). The order is fixed by editorial convention — alphabetical or
# size-based ordering would imply ranking, which the platform explicitly
# does not editorialise (see spec §"Tradeoffs"). `cross` is the
# denominationally neutral bucket and is rendered ABOVE the tradition
# stack in the popup (linguistic / structural notes belong above
# theological readings, not below). The tuple is materialised here so
# downstream encoders read it in this order without any re-sorting.
CANONICAL_TRADITIONS: tuple[tuple[str, str], ...] = (
    ("catholic", "Catholic"),
    ("protestant", "Protestant"),
    ("orthodox", "Eastern Orthodox"),
    ("jewish", "Jewish"),
    ("tewahedo", "Ethiopian Tewahedo"),
    ("cross", "Cross-tradition"),
)

TRADITION_IDS: frozenset[str] = frozenset(t for t, _ in CANONICAL_TRADITIONS)
DEFAULT_TRADITION = "cross"

# Attribution prefixes that unambiguously map to the `cross` (neutral)
# tradition. Each entry is matched as a case-insensitive substring of a
# note's attribution string. This is how `note_tradition()` derives
# tradition for the ~15K already-shipped notes from the χ-cluster
# pipelines (TSK / Strong's Hebrew / Strong's Greek / Nave's Topical).
# Anything not matching here, and lacking an explicit tradition field,
# falls through to DEFAULT_TRADITION.
_CROSS_ATTRIBUTION_MARKERS: tuple[str, ...] = (
    "treasury of scripture knowledge",
    "tsk",
    "strong's h",  # Hebrew
    "strong's g",  # Greek
    "nave's topical",
    "openbible.info",
)


def valid_tradition(s: object) -> bool:
    """True iff *s* is one of the canonical tradition ids."""
    return isinstance(s, str) and s in TRADITION_IDS


def note_tradition(tup: tuple) -> str:
    """Return the tradition for a note tuple.

    Resolution order:
      1. Explicit 10th tuple field (`tup[9]`), if present and valid.
         (ψ.8.0 reserves this slot for tradition; older 8/9-tuple
         notes don't have it and fall through to step 2 / 3.)
      2. Derive from `tup[8]` (attribution) — known PD-corpus prefixes
         map to ``cross`` per ``_CROSS_ATTRIBUTION_MARKERS``.
      3. ``DEFAULT_TRADITION`` (= ``cross``).

    Always returns a valid tradition id; never raises.
    """
    if not isinstance(tup, tuple) or len(tup) < 8:
        return DEFAULT_TRADITION

    # Step 1: explicit field
    if len(tup) >= 10:
        explicit = tup[9]
        if isinstance(explicit, str) and explicit in TRADITION_IDS:
            return explicit
        # Unknown / non-string explicit values fall through; they will
        # be caught by the linter's check_canonical_order_encoders pass
        # (ψ.8.2) and corrected by the next backfill run.

    # Step 2: derive from attribution
    if len(tup) >= 9:
        attribution = tup[8]
        if isinstance(attribution, str) and attribution.strip():
            lo = attribution.lower()
            for marker in _CROSS_ATTRIBUTION_MARKERS:
                if marker in lo:
                    return "cross"

    # Step 3: default
    return DEFAULT_TRADITION


def edition_to_tradition(
    edition_id: str,
    mapping: Optional[dict] = None,
) -> str:
    """Look up the tradition for an edition id.

    *mapping* is a dict like
    ``{"catholic-study": "catholic", ...}`` — typically the value of
    ``load_traditions_yaml()["edition_to_tradition"]``. Pass it
    explicitly in tests; production callers can pass `None` and the
    default YAML is loaded.

    Unknown ids return ``DEFAULT_TRADITION`` (no exception).
    """
    if mapping is None:
        mapping = load_traditions_yaml().get("edition_to_tradition") or {}
    if not isinstance(edition_id, str):
        return DEFAULT_TRADITION
    val = mapping.get(edition_id)
    if isinstance(val, str) and val in TRADITION_IDS:
        return val
    return DEFAULT_TRADITION


def load_traditions_yaml(path: Path | str | None = None) -> dict:
    """Read ``content/traditions.yaml`` and return the parsed dict.

    Uses a tiny YAML parser (mirror of ``scripts.core.config``'s
    approach) — sufficient for the flat ``edition_to_tradition`` map
    this file holds. No external YAML dep introduced.

    Returns ``{}`` if the file is absent (the platform stays usable
    without it; ``edition_to_tradition()`` then always returns
    ``DEFAULT_TRADITION``).
    """
    p = Path(path) if path else DEFAULT_TRADITIONS_YAML
    if not p.is_file():
        return {}
    text = p.read_text(encoding="utf-8")
    return _parse_traditions_yaml(text)


def _parse_traditions_yaml(text: str) -> dict:
    """Parse the focused subset of YAML used by traditions.yaml.

    Schema:

        edition_to_tradition:
          <edition_id>: <tradition_id>
          ...

    Comments (#-prefixed) and blank lines are ignored. Only the
    flat-mapping form under ``edition_to_tradition`` is recognised;
    anything else is ignored (defensive — future schema additions
    won't break older callers).
    """
    out: dict = {}
    in_section: Optional[str] = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        # Top-level key (no leading whitespace, ends with ':')
        if not line.startswith((" ", "\t")) and line.endswith(":"):
            in_section = line[:-1].strip()
            out.setdefault(in_section, {})
            continue
        # Indented entry under a section
        if in_section and line.startswith((" ", "\t")) and ":" in line:
            stripped = line.strip()
            key, _, value = stripped.partition(":")
            key = key.strip().strip('"').strip("'")
            value = value.strip().strip('"').strip("'")
            if key and value and isinstance(out[in_section], dict):
                # Validate tradition values defensively — unknown ids
                # are silently skipped so a typo here can't poison
                # the lookup. The `traditions audit` linter check
                # (ψ.8.2 territory) will surface bad entries to humans.
                if in_section == "edition_to_tradition" and value not in TRADITION_IDS:
                    continue
                out[in_section][key] = value
    return out


# ----------------------------------------------------------------------
# Tuple emit helper — stamp a tradition onto a note tuple
# ----------------------------------------------------------------------


def with_tradition(tup: tuple, tradition: str) -> tuple:
    """Return a new note tuple with ``tradition`` stamped as the 10th
    field. Pads the 9th field (attribution) with ``""`` if absent so
    the slot is positionally correct.

    The default tradition (``cross``) is encoded only when stamping
    onto a note that already carries an explicit one — for new notes
    where the resolver would already produce ``cross``, callers
    should leave the field off so the diff stays minimal (CLAUDE
    PROJECT RULES §7.2 — no-op when default).

    Raises ``ValueError`` for an unknown tradition id."""
    if not valid_tradition(tradition):
        raise ValueError(f"unknown tradition {tradition!r}; must be one of {sorted(TRADITION_IDS)}")
    if not isinstance(tup, tuple) or len(tup) < 8:
        raise ValueError(f"note tuple must have ≥8 fields, got {len(tup)}")
    base = list(tup[:8])
    attribution = tup[8] if len(tup) >= 9 else ""
    return tuple(base) + (attribution, tradition)
