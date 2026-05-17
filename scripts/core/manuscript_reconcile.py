# scripts/core/manuscript_reconcile.py
"""Reconciliation + apparatus store (Samuel Phase-2, Unit D, τ.6.x.4.b).

Diplomatic-parallel D3 (design-spec 2026-05-16 §5 unit 4; D3 + §7 honesty
contract; spec-revision 2026-05-17 §3.4 — D1=B / D3 CONFIRMED, GO
2026-05-17). Pure logic; the only filesystem touch is
:func:`dump_apparatus`, which Phase-3 invokes (NOT :func:`reconcile`, and
NOT during Task 7) — it writes through the project's atomic-write
convention (rules §7.1, :func:`scripts.core.notes_io.atomic_write`).

THE HONESTY CONTRACT (design-spec §7 — the entire point of this unit):

* The reconciled running text of every spine verse is the **base
  witness's own** token list for that verse and **nothing else**. The
  other witness is NEVER merged into the running text — its divergence
  lives only in the apparatus ``variants[]`` (this is D3: a base
  diplomatic text + a critical apparatus, not an eclectic conflation).
* A verse where the **base witness has no legible reading** (every base
  token empty or ``⟦illegible⟧`` — the both-witness-lacuna case, and also
  the base-side-only lacuna where the base is illegible but the other
  witness is legible) is a **marked gap**: ``gap: True`` with
  ``geez == [ILLEGIBLE]``. Text is **NEVER fabricated** for a gap and the
  other witness's reading is **NEVER substituted into the running text**
  to paper over it. The gap is additionally recorded in the apparatus
  ``lacunae[]`` so it is documented, not silent.
* When the base is illegible / carries a clear scribal slip for a verse
  but the other witness is sound, the disciplined-eclectic fallback
  (adopting the sound witness's reading for that verse) is RECORDED in the
  apparatus (``resolution``, ``reason``, ``from_witness``) so an editor
  can adopt it deliberately — it is **never silently substituted into the
  running text** (strict D3: the running text stays the marked gap until
  an editor deliberately adopts the recorded eclectic reading).

2sa11 (the calibration sample / current test input) has 0 lacunae and
the base (CAM) stands throughout, so every reconciled verse is
``gap: False`` with the CAM tokens and every apparatus entry is
``resolution == "base"``. The logic below is nonetheless written for the
GENERAL case: a future chapter WILL carry ``lacuna-both`` spans, and the
gap/honesty path must already be correct (it is exercised structurally,
not by 2sa11 — see the module-level note + the Task-7 reviewer concern).
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.core.manuscript_records import ILLEGIBLE

# Repo-anchored output root — same primitive every sibling
# ``scripts/core/*`` uses (e.g. ``manuscript_manifest.REPO``):
# ``Path(__file__).resolve().parent.parent.parent`` (this file lives
# in ``scripts/core/``). ``dump_apparatus`` MUST anchor here, not on a
# CWD-relative path, so the book-wide driver (its first real caller,
# τ.6.x.4.b) writes the apparatus to the correct place regardless of
# the process CWD.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

__all__ = ["reconcile", "dump_apparatus"]


def _base_token_field(collation: dict) -> str:
    """Map ``base_witness_recommended`` to the verse token-list field.

    ``"CAM"`` → ``cam_tokens``; ``"GG"`` → ``gg_tokens``. Any other value
    is a hard error (a malformed collation must not silently degrade into
    an empty / wrong-witness running text — that would violate D3).
    """
    base = collation["base_witness_recommended"]
    if base == "CAM":
        return "cam_tokens"
    if base == "GG":
        return "gg_tokens"
    raise ValueError(f"unknown base_witness_recommended {base!r} (expected 'CAM' or 'GG')")


def _base_has_no_legible_reading(base_tokens: list) -> bool:
    """True iff the BASE witness has NO legible token for this spine verse.

    The honest gap test for D3 (design-spec §7; task spec: *gap iff the
    base has no legible reading*). The running text is the base witness's
    own tokens, so the only honest question is: does the base have anything
    legible to publish for this verse? It does NOT iff every base token is
    empty or the ``⟦illegible⟧`` sentinel.

    This is the correct, base-aware GENERAL-CASE rule (2sa11 never
    exercises it — it has 0 lacunae — so the synthetic/structural cases
    matter):

    * all-``lacuna-both`` verse (both witnesses illegible everywhere) →
      every base token is ``⟦illegible⟧`` → gap. ✔ (the classic §7 case)
    * base=CAM and the verse is entirely ``lacuna-cam``/``lacuna-both``
      (CAM illegible everywhere it wrote, GG may be legible) → every CAM
      token is ``⟦illegible⟧`` → gap. ✔ The base running text is still a
      MARKED gap — GG's legible reading is recorded in the apparatus
      (``lacunae`` + a disciplined-eclectic note in ``resolution``), it is
      **never silently merged into the base running text** (strict D3).
    * any ``agree``/``disagree`` cell, or any legible base token → the
      base has a publishable reading → NOT a gap. ✔ (every 2sa11 verse)

    Defining the gap on the base token list (the exact tokens that become
    the running text) also makes the test's honesty invariant — if
    ``⟦illegible⟧`` is in the running text then ``gap`` is True — hold by
    construction for every input, including the general lacuna case.
    """
    return all(t == "" or t == ILLEGIBLE for t in base_tokens)


def _verse_lacunae(verse: dict) -> list[dict]:
    """Structured record of every ``lacuna-*`` row in the verse.

    One ``{"witness", "note"}`` per ``lacuna-gg`` / ``lacuna-cam`` /
    ``lacuna-both`` alignment row, naming which witness(es) are illegible.
    ``[]`` when the verse has no lacuna rows (every 2sa11 verse). This is
    what makes a gap *documented* rather than silently dropped.
    """
    out: list[dict] = []
    for a in verse["alignment"]:
        cls = a["class"]
        if cls == "lacuna-gg":
            out.append({"witness": "GG", "note": "GG illegible (⟦illegible⟧); CAM legible"})
        elif cls == "lacuna-cam":
            out.append({"witness": "CAM", "note": "CAM illegible (⟦illegible⟧); GG legible"})
        elif cls == "lacuna-both":
            out.append(
                {"witness": "GG+CAM", "note": "both witnesses illegible (⟦illegible⟧) — marked gap, not reconstructed"}
            )
    return out


def reconcile(collation: dict):
    """Diplomatic-parallel reconciliation (D3) → ``(reconciled, apparatus)``.

    ``reconciled`` — one entry per spine verse, SAME length and order as
    ``collation["verses"]``::

        {"v": <int>, "geez": [<token>, ...], "gap": <bool>}

    ``geez`` is the **base witness's own** token list for the verse (base =
    ``collation["base_witness_recommended"]``; ``"CAM"`` → ``cam_tokens``,
    ``"GG"`` → ``gg_tokens``) — the other witness is NEVER pulled in here
    (D3: it belongs in the apparatus only). ``gap`` is ``True`` iff the
    verse is a both-witness lacuna (the base has no legible reading); for a
    gap, ``geez == [ILLEGIBLE]`` — a MARKED gap, text NEVER fabricated and
    the other witness NEVER substituted into the running text (design-spec
    §7). Honesty invariant held by construction: if ``ILLEGIBLE`` appears
    in ``" ".join(geez)`` then ``gap`` is ``True`` (only a gap verse emits
    the sentinel; a normal verse's running text is the base's legible
    tokens, which contain no sentinel — for 2sa11 ``gap`` is ``False``
    everywhere with the CAM tokens).

    ``apparatus`` — one structured entry per spine verse that has ANY
    alignment row with ``class != "agree"`` (a recorded disagreement or
    lacuna)::

        {"v": <int>,
         "base_reading": <str: space-joined base tokens for the verse>,
         "variants": [{"witness": "GG"|"CAM", "reading": <str>}, ...],
         "lacunae": [{"witness", "note"}, ...],   # [] when none
         "resolution": <str>,                     # "base" | eclectic note
         "reason": <str>}                         # short human reason

    ``variants`` records the **non-base** witness's reading for the verse
    when it differs from the base (the divergence the apparatus exists to
    document; the non-base witness is the only ``variants[]`` witness).
    ``resolution`` is ``"base"`` when the base diplomatic text stands (the
    D3 default — and every 2sa11 verse); when the base has a clear scribal
    slip / both-witness lacuna and the other witness is sound, the
    disciplined-eclectic fallback is recorded here (with ``from_witness``
    and a ``reason``) — NEVER a silent substitution. For a both-witness
    lacuna the resolution is the honest "marked gap" (no reconstruction).

    Pure: no I/O, no fabrication, no mutation of ``collation``.
    """
    tok_field = _base_token_field(collation)
    non_base = "GG" if collation["base_witness_recommended"] == "CAM" else "CAM"

    reconciled: list[dict] = []
    apparatus: list[dict] = []

    for verse in collation["verses"]:
        v = verse["v"]
        base_tokens = list(verse[tok_field])
        gap = _base_has_no_legible_reading(base_tokens)

        if gap:
            # HONESTY (design-spec §7): the base has NO legible reading for
            # this verse → a MARKED gap. Emit the illegible sentinel — we
            # do NOT invent text and we do NOT pull the other witness's
            # reading into the running text (strict D3: a base-witness
            # diplomatic text; the other witness lives in the apparatus
            # only — even when it is legible here and the base is not, the
            # eclectic option is RECORDED in the apparatus, never silently
            # merged into the running text).
            geez = [ILLEGIBLE]
        else:
            geez = base_tokens
        reconciled.append({"v": v, "geez": geez, "gap": gap})

        # Apparatus: emit one entry for any verse with a recorded
        # disagreement OR lacuna (any non-"agree" alignment row).
        if not any(a["class"] != "agree" for a in verse["alignment"]):
            continue

        base_reading = " ".join(base_tokens)
        if non_base == "GG":
            other_reading = " ".join(verse["gg_tokens"])
        else:
            other_reading = " ".join(verse["cam_tokens"])

        lacunae = _verse_lacunae(verse)

        if gap:
            # The base has no legible reading → honest marked gap. The base
            # running text is the gap sentinel, NEVER a reconstruction.
            resolution = "marked-gap"
            other_legible = any(
                t != "" and t != ILLEGIBLE for t in (verse["gg_tokens"] if non_base == "GG" else verse["cam_tokens"])
            )
            if other_legible:
                # Disciplined-eclectic fallback is AVAILABLE (base illegible,
                # other witness sound) — it is RECORDED here with the source
                # witness so an editor can adopt it deliberately; per strict
                # D3 it is NOT auto-merged into the running text (that would
                # be a silent substitution). `from_witness` names the source.
                entry_extra_from_witness = non_base
                reason = (
                    f"D3/§7: base ({collation['base_witness_recommended']}) illegible for this "
                    f"verse — running text is a MARKED gap (⟦illegible⟧), never fabricated. "
                    f"{non_base} is legible here; the disciplined-eclectic reading is RECORDED "
                    f"(see variants/from_witness) for editorial adoption, never silently merged."
                )
            else:
                entry_extra_from_witness = None
                reason = (
                    "D3/§7: both witnesses illegible for this verse — running "
                    "text is a MARKED gap (⟦illegible⟧), never fabricated and "
                    "never substituted from the other witness; lacuna recorded."
                )
        else:
            entry_extra_from_witness = None
            # D3 default: the base diplomatic reading stands; the divergent
            # other witness is recorded as a variant. (Disciplined-eclectic
            # substitution — base scribal slip + other witness sound — is
            # the ONLY case that would change `resolution` away from "base",
            # and it MUST then carry `from_witness`/`reason`; 2sa11 never
            # triggers it, the base stands throughout.)
            resolution = "base"
            reason = f"D3: {collation['base_witness_recommended']} base running text; {non_base} divergence recorded as variant"

        entry = {
            "v": v,
            "base_reading": base_reading,
            "variants": [{"witness": non_base, "reading": other_reading}],
            "lacunae": lacunae,
            "resolution": resolution,
            "reason": reason,
        }
        # `from_witness` is present ONLY when a disciplined-eclectic
        # fallback is recorded (base illegible + other witness sound); it
        # names the witness an editor would adopt from. Absent otherwise so
        # the schema does not falsely imply an eclectic substitution.
        if entry_extra_from_witness is not None:
            entry["from_witness"] = entry_extra_from_witness
        apparatus.append(entry)

    return reconciled, apparatus


def dump_apparatus(book: str, app: list) -> str:
    """Write the apparatus list to ``content/apparatus/<book>.json``.

    UTF-8, ``ensure_ascii=False`` (Ge'ez stays readable), ``indent=2``,
    via the project's crash-safe atomic-write convention (rules §7.1 —
    :func:`scripts.core.notes_io.atomic_write`, write-then-rename; the
    same primitive every other content artifact uses, so a crash
    mid-write cannot leave a half-written apparatus). The
    ``content/apparatus/`` directory contract is established by
    ``content/apparatus/.gitkeep``.

    NOT called by :func:`reconcile` and NOT called during Task 7 — this
    only defines the directory/schema/atomicity contract. Phase-3's
    book-wide driver invokes it when it actually persists the apparatus
    (one ``<book>.json`` per book). The output path is anchored on the
    repo root (``_REPO_ROOT`` — the same ``Path(__file__).resolve()``
    primitive every sibling ``scripts/core/*`` uses), NOT a CWD-relative
    path, so the book-wide driver (the first real caller) writes to the
    correct ``content/apparatus/<book>.json`` regardless of process CWD.
    Returns the written path as a str.
    """
    from scripts.core.notes_io import atomic_write

    path = _REPO_ROOT / "content" / "apparatus" / f"{book}.json"
    text = json.dumps(app, ensure_ascii=False, indent=2)
    return str(atomic_write(path, text))
