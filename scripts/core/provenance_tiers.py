"""Formal provenance-tier registry for rendered Bible text sources.

Codifies the quality hierarchy of source-of-record tiers used in
``content/translations/<edition>/<book>.py`` ``SOURCE_QUALITY`` fields.
Today the values appear ad-hoc per-file; this registry makes them a
small enumerated set + a documented quality ordering. Lint check
``manuscript_witnesses_valid`` (lint_rules.py) is the schema gate;
``check_render_provenance_tier`` (this module) is the per-book gate.

Tier hierarchy, from highest-quality to lowest:

1. **manuscript-collation-tier2** — dual-witness manuscript-collated
   text with apparatus (the τ.6.x.4.b/c output). Two independent
   scribal hands cross-checked verse-by-verse + a recorded per-verse
   apparatus. NOT a critical edition (the witnesses are not
   exhaustively collated against the full tradition), hence "tier2"
   not "tier1".

2. **patrologia-printed-tier1** — printed bilingual critical editions
   (Patrologia Orientalis vols 2/9/13/23). Editorial work has already
   reconciled multiple witnesses + supplied a critical apparatus in
   French. PD; ingest is OCR + lightweight validation. **Highest
   automated tier** because the philological work is pre-done.

3. **ocr-tier3** — parallel-Bible EOTC PDF (printed Tewahedo edition,
   Ge'ez + Amharic columns) extracted via Tesseract or text-layer.
   Single-source; no apparatus; OCR confidence is the only quality
   signal.

4. **kjv-skeleton** — canonical KJV verse skeleton (per-chapter verse
   count + KJV English text). Used as the semantic anchor for all
   higher tiers' collation + render renumbering. NOT a Bible text
   for publication in geez/amharic editions — strictly a structural
   scaffold.

When a new source type lands, add it here (one entry per tier) AND
update the tier-ordered list ``TIERS_QUALITY_DESCENDING``. The lint
rule ``check_render_provenance_tier`` pins that every committed
``content/translations/<edition>/<book>.py`` declares a known tier.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProvenanceTier:
    """One tier's metadata."""

    code: str
    quality_rank: int  # 1 = highest; bigger numbers = lower
    description: str
    examples: tuple[str, ...]


# Single source of truth — every rendered book declares one of these
# code strings via SOURCE_QUALITY. Lint pins this set.
TIERS: dict[str, ProvenanceTier] = {
    "manuscript-collation-tier2": ProvenanceTier(
        code="manuscript-collation-tier2",
        quality_rank=2,
        description=(
            "Dual-witness manuscript collation with per-verse apparatus "
            "(τ.6.x.4.b/c). Two independent scribal hands cross-checked; "
            "no exhaustive tradition-wide critical apparatus, hence "
            "tier2 not tier1."
        ),
        examples=("1sa", "2sa", "1ki", "2ki"),
    ),
    "patrologia-printed-tier1": ProvenanceTier(
        code="patrologia-printed-tier1",
        quality_rank=1,
        description=(
            "Printed bilingual critical edition (Patrologia Orientalis "
            "vols 2/9/13/23). Philological work pre-done; ingest is "
            "OCR + lightweight validation against the printed Ge'ez. "
            "PD; CC BY-NC for any direct reproduction credits where "
            "applicable."
        ),
        examples=("1ch", "2ch", "ezr", "neh", "job"),
    ),
    "ocr-tier3": ProvenanceTier(
        code="ocr-tier3",
        quality_rank=3,
        description=(
            "Parallel-Bible EOTC PDF (printed Tewahedo edition; Ge'ez + "
            "Amharic columns) extracted via Tesseract `script/Ethiopic` "
            "/ `amh` or text-layer (τ.6.x.2 / τ.7.x). Single-source; "
            "OCR confidence is the only quality signal."
        ),
        examples=("gen", "exo", "lev", "num", "deu", "jdg", "rut"),
    ),
    "kjv-skeleton": ProvenanceTier(
        code="kjv-skeleton",
        quality_rank=99,
        description=(
            "Canonical KJV verse skeleton (per-chapter verse count + "
            "KJV English text). Semantic anchor for collation + render "
            "renumbering; NOT itself published as geez/amharic text."
        ),
        examples=("any-book",),
    ),
    "digitized-critical-edition": ProvenanceTier(
        code="digitized-critical-edition",
        quality_rank=1,
        description=(
            "Pre-existing digital critical edition (text-layer extraction "
            "from a digitized published critical edition). Used for the "
            "Tewahedo Psalter (`geez-tewahedo/psa.py`). Same quality "
            "ordinal as patrologia-printed-tier1 — both are reuses of "
            "completed editorial work, with no fresh OCR risk."
        ),
        examples=("psa",),
    ),
    "ai-back-translation-tier4": ProvenanceTier(
        code="ai-back-translation-tier4",
        quality_rank=4,
        description=(
            "LLM-generated English back-translation of an OCR-derived "
            "Ge'ez or Amharic source. Useful for reading-aid popups in "
            "the standalone Ge'ez/Amharic Bibles; not a substitute for "
            "scholarly translation. Inherits source-noise from ocr-tier3."
        ),
        examples=("gen",),
    ),
}

# Convenience: tier codes ordered best-quality first.
TIERS_QUALITY_DESCENDING: list[str] = sorted(TIERS.keys(), key=lambda c: TIERS[c].quality_rank)


def is_known_tier(code: str) -> bool:
    """True iff ``code`` is one of the registered tier strings."""
    return code in TIERS


def tier_for(code: str) -> ProvenanceTier:
    """Return the ``ProvenanceTier`` for ``code`` or raise ``KeyError``."""
    return TIERS[code]
