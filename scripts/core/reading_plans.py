"""ψ.19 — reading plans: declarative YAML schedules for daily Bible
reading.

Plans live in ``content/reading_plans/<id>.yaml``. Each plan is a
flat record (mirroring editions.yaml shape) with:

- ``id``: matches the filename stem
- ``label``: human-readable name
- ``description``: 1-2 sentence summary
- ``entries``: list of ``{day: int, verses: [refs...]}``

Verses are stored as human-readable reference strings (e.g.
``"gen 1:1-2:3"`` or ``"psa 1"``) — the format is intentionally
loose so plans can be hand-edited without a strict grammar.
``parse_verse_ref`` extracts ``(book_code, chapter)`` for the
common case of "<book> <chapter>" / "<book> <chapter>:<verses>";
plans that use unsupported shapes (cross-chapter ranges with
explicit start/end verses) parse to ``None`` and the build-
pipeline integration (ψ.19.1, deferred) will need richer parsing.

Per-edition opt-in: ``editions.yaml`` records may include an
``enabled_reading_plans: [<id>, ...]`` list. The build pipeline
will (in ψ.19.1) emit a ToC section per enabled plan; for now
this is schema-only — opting in is a no-op until the build-time
integration ships.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from . import paths


_PLAN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,40}$")
_REF_RE = re.compile(
    r"""^\s*
        ([a-z0-9]+)        # book code
        \s+
        (\d+)              # chapter
        (?:                # optional :verses
            :
            ([\d,\-\s]+)
        )?
        (?:                # optional dash-chapter (e.g. "gen 1:1-2:3")
            \s*-\s*
            (\d+)
            (?::([\d,\-\s]+))?
        )?
        \s*$
    """,
    re.VERBOSE,
)


def reading_plans_dir():
    """Absolute path to ``content/reading_plans/`` (created on first use)."""
    return paths.content_root() / "reading_plans"


@dataclass(frozen=True)
class ReadingPlanEntry:
    day: int
    verses: tuple = field(default_factory=tuple)  # tuple of strings

    def to_dict(self) -> dict:
        return {"day": self.day, "verses": list(self.verses)}


@dataclass(frozen=True)
class ReadingPlan:
    id: str
    label: str
    description: str
    entries: tuple = field(default_factory=tuple)  # tuple of ReadingPlanEntry

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "entry_count": len(self.entries),
            "entries": [e.to_dict() for e in self.entries],
        }


def _validate_id(plan_id: str) -> None:
    if not _PLAN_ID_RE.match(plan_id or ""):
        raise ValueError(f"invalid reading-plan id {plan_id!r} — use lowercase a-z, 0-9, -, _ (max 41 chars)")


def list_plans() -> list[ReadingPlan]:
    """Return every reading plan on disk, sorted by id.

    Skips files that fail to parse, so a hand-edited typo in one
    plan doesn't break the rest of the registry. Unparseable
    plans surface in the linter's drift checks (future ω.x).
    """
    root = reading_plans_dir()
    if not root.is_dir():
        return []
    out: list[ReadingPlan] = []
    for p in sorted(root.glob("*.yaml")):
        try:
            plan = load_plan(p.stem)
        except (FileNotFoundError, ValueError):
            continue
        if plan is not None:
            out.append(plan)
    return out


def load_plan(plan_id: str) -> Optional[ReadingPlan]:
    """Read one plan from disk. Returns ``None`` if the file is
    missing; raises ValueError on invalid id or malformed YAML."""
    _validate_id(plan_id)
    path = reading_plans_dir() / f"{plan_id}.yaml"
    if not path.is_file():
        return None
    import yaml

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"malformed YAML in {plan_id}.yaml: {e}")
    if not isinstance(data, dict):
        raise ValueError(f"{plan_id}.yaml top level must be a mapping")
    entries_raw = data.get("entries") or []
    if not isinstance(entries_raw, list):
        raise ValueError(f"{plan_id}.yaml: `entries` must be a list of {{day, verses}} records")
    entries: list[ReadingPlanEntry] = []
    # ω.31 — `entry` instead of `e` to avoid shadowing the prior
    # except-block variable name (mypy "Assignment to variable 'e'
    # outside except: block").
    for entry in entries_raw:
        if not isinstance(entry, dict):
            continue  # skip ill-formed entries silently
        day = entry.get("day")
        if not isinstance(day, int):
            continue
        verses_raw = entry.get("verses") or []
        if not isinstance(verses_raw, list):
            continue
        verses = tuple(str(v) for v in verses_raw if isinstance(v, str))
        entries.append(ReadingPlanEntry(day=day, verses=verses))
    return ReadingPlan(
        id=plan_id,
        label=str(data.get("label") or plan_id),
        description=str(data.get("description") or ""),
        entries=tuple(entries),
    )


def parse_verse_ref(ref: str) -> Optional[dict]:
    """Parse a verse reference into structured fields.

    Returns a dict with ``{book, chapter, verses_start?, verses_end?,
    chapter_end?}`` for refs the parser recognises, or ``None``
    for shapes it doesn't.

    Recognised:
    - ``"gen 1"`` → whole chapter
    - ``"gen 1:1"`` → single verse
    - ``"gen 1:1-5"`` → verse range within chapter
    - ``"gen 1:1-2:3"`` → cross-chapter range with verses
    - ``"psa 1-5"`` → multi-chapter range without verses

    Edge cases left for ψ.19.1's richer parser: comma-separated
    verse lists like "gen 1:1,3,5"; explicit "v" prefix like
    "gen 1 v.1"; cross-book ranges.
    """
    if not isinstance(ref, str):
        return None
    m = _REF_RE.match(ref)
    if not m:
        return None
    book = m.group(1).lower()
    chapter = int(m.group(2))
    verses_str = m.group(3)
    chapter_end_str = m.group(4)
    verses_end_str = m.group(5)
    out = {"book": book, "chapter": chapter}
    if verses_str:
        try:
            # Take just the first int as verses_start; the rest is
            # too varied for v1 (commas, ranges, etc.).
            first = re.match(r"\s*(\d+)", verses_str)
            if first:
                out["verses_start"] = int(first.group(1))
            # End-verse: if there's a `-N` inside this chapter's
            # verses_str.
            tail = re.match(r"\s*\d+\s*-\s*(\d+)", verses_str)
            if tail:
                out["verses_end"] = int(tail.group(1))
        except ValueError:
            pass
    if chapter_end_str:
        out["chapter_end"] = int(chapter_end_str)
        if verses_end_str:
            try:
                ve = re.match(r"\s*(\d+)", verses_end_str)
                if ve:
                    out["verses_end"] = int(ve.group(1))
            except ValueError:
                pass
    return out


def plan_summary(plan: ReadingPlan) -> dict:
    """Lightweight summary suitable for /customize cards.

    Doesn't include the full entries list — just metadata so the
    UI doesn't ship 365 entries × 4-5 refs per row.
    """
    if plan is None:
        return {}
    days = sorted({e.day for e in plan.entries})
    return {
        "id": plan.id,
        "label": plan.label,
        "description": plan.description,
        "entry_count": len(plan.entries),
        "first_day": days[0] if days else None,
        "last_day": days[-1] if days else None,
    }
