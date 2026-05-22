"""υ.3 — cross-edition / cross-book note search.

Pure-function `search_notes(query, *, edition_id=None, kind=None,
book=None, limit=100)` scans every `notes/<book>.py` file via the
existing `notes_io.load_notes` cache and returns matching notes
ranked by which field matched. Operators previously had to grep
on disk to find a specific note; this surfaces the same query in
the editor UI.

Design points:
- **No new persistence.** Reads through the existing mtime-cached
  `notes_io.load_notes` so repeat queries are cheap and the
  cache invalidates on writes automatically.
- **Pure function returns a dict-friendly shape.** The route
  adapter in `scripts/web.py` translates `SearchHit` records to
  JSON; no HTTP coupling here.
- **Score-based ranking.** Matches in `label` rank above
  `title`, then `kind`, then `attribution`, then `body_plain`.
  Each match contributes its weight; a hit on multiple fields
  rises naturally.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

from . import config
from . import notes_io
from . import paths

# Reuse the canonical kind-filter helper from matrix so search +
# build agree on "what's enabled in this edition". Importing the
# underscore-prefixed name is an in-package call; we don't want to
# duplicate the precedence logic and risk drift.
from .matrix import _enabled_kinds_for_edition, _load_canons  # noqa: F401


@dataclass(frozen=True)
class SearchHit:
    """One note matching the query.

    `score` is internal-ish — higher is more relevant — but exposed
    so the UI can show it (or sort by it on the client).
    """

    book_code: str
    chapter: int
    verse: int
    suffix: str
    anchor: str
    kind: str
    title: str
    label: str
    excerpt: str
    attribution: str | None
    score: int

    def to_dict(self) -> dict:
        return {
            "book_code": self.book_code,
            "chapter": self.chapter,
            "verse": self.verse,
            "suffix": self.suffix,
            "anchor": self.anchor,
            "kind": self.kind,
            "title": self.title,
            "label": self.label,
            "excerpt": self.excerpt,
            "attribution": self.attribution,
            "score": self.score,
        }


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _strip_tags(html_text: str) -> str:
    """Strip HTML tags + decode entities for excerpt + body matching.

    Notes' bodies are stored as HTML; matching the literal HTML
    would surface false positives on tag names + entity refs.
    """
    if not html_text:
        return ""
    plain = _TAG_RE.sub(" ", html_text)
    plain = html.unescape(plain)
    return _WS_RE.sub(" ", plain).strip()


def _make_excerpt(text: str, query: str, *, radius: int = 60) -> str:
    """Return a window around the first occurrence of `query` in
    `text`. If `query` is not a substring, return a leading slice
    so the user always sees *something* of the matched note.
    """
    if not text:
        return ""
    if not query:
        if len(text) <= radius * 2:
            return text
        return text[: radius * 2] + "…"
    lower = text.lower()
    q_lc = query.lower()
    idx = lower.find(q_lc)
    if idx < 0:
        if len(text) <= radius * 2:
            return text
        return text[: radius * 2] + "…"
    start = max(0, idx - radius)
    end = min(len(text), idx + len(query) + radius)
    out = text[start:end]
    if start > 0:
        out = "…" + out
    if end < len(text):
        out = out + "…"
    return out


# Field weights — label/title named the highest because users
# usually search by what they see in the matrix sidebar / per-book
# panel. Body weight is intentionally low so a query that hits the
# label ranks above one that only hits a stray phrase in body html.
_FIELD_WEIGHTS = (
    ("label", 5),
    ("title", 4),
    ("kind", 3),
    ("attribution", 2),
    ("body_plain", 1),
)


def _score(haystacks: dict, query_lc: str) -> int:
    score = 0
    for field, weight in _FIELD_WEIGHTS:
        value = haystacks.get(field) or ""
        if query_lc in value.lower():
            score += weight
    return score


def _best_excerpt_field(haystacks: dict, query_lc: str) -> str:
    """Pick the haystack to draw the excerpt from. Prefer the body
    (richest context); fall back to label or title if the body
    doesn't contain the query."""
    body = haystacks.get("body_plain") or ""
    if query_lc in body.lower() and body:
        return body
    label = haystacks.get("label") or ""
    if query_lc in label.lower() and label:
        return label
    title = haystacks.get("title") or ""
    if query_lc in title.lower() and title:
        return title
    return body or label or title


def search_notes(
    query: str,
    *,
    edition_id: str | None = None,
    kind: str | None = None,
    book: str | None = None,
    limit: int = 100,
) -> list[SearchHit]:
    """Search every note for `query` (case-insensitive substring).

    Returns at most `limit` `SearchHit` records, sorted by score
    descending then by canonical book order, chapter, and verse.

    Empty / whitespace-only `query` returns an empty list — the
    caller is responsible for hiding the result panel until the
    user actually types something.

    `edition_id` filters to kinds enabled in that edition; `kind`
    pins one kind code; `book` pins one book.
    """
    q = (query or "").strip()
    if not q:
        return []
    q_lc = q.lower()

    books_by_code = config.books_by_code()
    canonical_order = {code: i for i, code in enumerate(books_by_code.keys())}

    # editions.yaml records are dicts (per config.load_editions). The
    # final enabled-kinds set is derived via the same precedence the
    # build pipeline uses so search results match what would ship.
    enabled_kind_set: set | None = None
    canon_book_set: set | None = None
    if edition_id:
        editions = config.load_editions()
        ed = next(
            (e for e in editions if isinstance(e, dict) and e.get("id") == edition_id),
            None,
        )
        if ed is not None:
            all_kinds = config.load_kinds()
            enabled_kind_set = _enabled_kinds_for_edition(ed, all_kinds)
            canon_id = ed.get("canon")
            if canon_id:
                canons = _load_canons()
                canon_def = canons.get(canon_id) if isinstance(canons, dict) else None
                if isinstance(canon_def, dict):
                    canon_book_set = set(canon_def.get("books") or [])

    notes_dir = paths.notes_dir()
    if book:
        candidate_files = [notes_dir / f"{book}.py"]
    else:
        candidate_files = sorted(notes_dir.glob("*.py"))
        if canon_book_set is not None:
            candidate_files = [p for p in candidate_files if p.stem in canon_book_set]

    hits: list[SearchHit] = []
    for path in candidate_files:
        if not path.exists():
            continue
        notes = notes_io.load_notes(path)
        if not notes:
            continue
        bcode = path.stem
        for tup in notes:
            try:
                spec = config.NoteSpec.from_tuple(tup)
            except (ValueError, TypeError):
                continue
            if kind and spec.kind != kind:
                continue
            if enabled_kind_set is not None and spec.kind not in enabled_kind_set:
                continue
            body_plain = _strip_tags(spec.body_html)
            haystacks = {
                "label": spec.label or "",
                "title": spec.title or "",
                "kind": spec.kind or "",
                "attribution": spec.attribution or "",
                "body_plain": body_plain,
            }
            score = _score(haystacks, q_lc)
            if score == 0:
                continue
            excerpt_src = _best_excerpt_field(haystacks, q_lc)
            excerpt = _make_excerpt(excerpt_src, q)
            hits.append(
                SearchHit(
                    book_code=bcode,
                    chapter=spec.chapter,
                    verse=spec.verse,
                    suffix=spec.suffix or "",
                    anchor=spec.anchor or "",
                    kind=spec.kind,
                    title=spec.title or "",
                    label=spec.label or "",
                    excerpt=excerpt,
                    attribution=spec.attribution,
                    score=score,
                )
            )

    hits.sort(
        key=lambda h: (
            -h.score,
            canonical_order.get(h.book_code, 9999),
            h.chapter,
            h.verse,
            h.suffix,
        )
    )
    cap = max(0, int(limit)) if limit is not None else len(hits)
    return hits[:cap]
