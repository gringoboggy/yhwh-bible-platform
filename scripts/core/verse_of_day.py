"""υ.8 — verse-of-the-day picker and feed payloads.

Pure functions:

- ``pick_verse_for_date(date_iso)`` — deterministically hashes the
  date string and selects a (book, chapter, verse) tuple that has
  at least one note attached. Same date → same verse, every time.
- ``verse_of_day(date_iso, *, edition_id=None)`` — returns the
  picked verse plus its top-ranked note(s) + book title; the
  payload the JSON / RSS feed serializers consume.
- ``rss_feed(*, days=7, base_url="", edition_id=None)`` — emits an
  RSS 2.0 XML string with one ``<item>`` per day for the last
  ``days`` days. Pure string output; no I/O.

Design points:

- **Deterministic from date.** SHA-1 of the date string seeds the
  pick. Two callers asking for the same day get the same verse,
  guaranteeing stable feeds + cacheable RSS items.
- **Always has a note.** The picker walks notes/<book>.py via
  ``notes_io.load_notes`` and only returns verses that exist in
  the corpus, so the daily feed always has something to display.
  Falls back across (chapter, book) deterministically until it
  finds a verse with notes.
- **Rank by kind weight.** Commentary > devotional > literary >
  cross-ref > language. Lets a verse with multiple notes show its
  most pastorally-relevant one in the feed item.
- **No external HTTP, no auth, no per-request state.** The feed is
  cacheable via the existing notes_io mtime cache — no new layer.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date as date_cls, datetime, timedelta, timezone

from . import config
from . import notes_io
from . import paths


# Kind-weighted rank used to pick the "headline" note for a verse.
# Higher = more pastorally relevant for a daily-verse audience.
# Unknown / unlisted prefixes get the default weight (0).
_KIND_PREFIX_WEIGHT = (
    ("comm-", 6),
    ("dev-", 5),
    ("hist-", 4),
    ("lit-", 3),
    ("compare-", 3),
    ("liturgy-", 3),
    ("xref-", 2),
    ("dist-", 2),
    ("lang-", 1),
    ("text-", 1),
    ("topic-", 1),
)


def _kind_weight(kind: str) -> int:
    if not kind:
        return 0
    for prefix, weight in _KIND_PREFIX_WEIGHT:
        if kind.startswith(prefix):
            return weight
    return 0


@dataclass(frozen=True)
class VerseHeadline:
    book_code: str
    book_title: str
    chapter: int
    verse: int
    suffix: str
    notes: tuple = field(default_factory=tuple)  # tuple of dicts

    def to_dict(self) -> dict:
        return {
            "book_code": self.book_code,
            "book_title": self.book_title,
            "chapter": self.chapter,
            "verse": self.verse,
            "suffix": self.suffix,
            "notes": list(self.notes),
            "ref": f"{self.book_title} {self.chapter}:{self.verse}{self.suffix or ''}",
        }


def _normalize_date(date_iso) -> str:
    """Accept ``date`` / ``datetime`` / ``str`` and return a YYYY-MM-DD
    string. Naive parsing — invalid input falls back to today's UTC."""
    if isinstance(date_iso, (date_cls, datetime)):
        return date_iso.strftime("%Y-%m-%d")
    if isinstance(date_iso, str):
        s = date_iso.strip()
        if len(s) >= 10:
            head = s[:10]
            try:
                datetime.strptime(head, "%Y-%m-%d")
                return head
            except ValueError:
                pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _seed_for_date(date_iso: str) -> int:
    """SHA-1-derived seed integer. Stable across runs."""
    digest = hashlib.sha1(date_iso.encode("utf-8")).digest()
    # First 8 bytes as an unsigned 64-bit int — plenty of headroom.
    return int.from_bytes(digest[:8], "big")


def _book_codes_for_edition(edition_id: str | None) -> list[str]:
    """Return the book-code list to draw from — the edition's canon,
    or every notes/*.py file in canonical order if no edition is given."""
    notes_dir = paths.notes_dir()
    available = {p.stem for p in notes_dir.glob("*.py") if p.is_file()}
    books = config.load_books()
    canonical = [b["code"] for b in books if b.get("code") in available]
    if not edition_id:
        return canonical
    eds = config.load_editions()
    ed = next(
        (e for e in eds if isinstance(e, dict) and e.get("id") == edition_id),
        None,
    )
    if ed is None:
        return canonical
    canon_id = ed.get("canon")
    if not canon_id:
        return canonical
    # Lazy import to avoid cycle; mirrors note_search.
    from .matrix import _load_canons

    canons = _load_canons()
    canon_def = canons.get(canon_id) if isinstance(canons, dict) else None
    if not isinstance(canon_def, dict):
        return canonical
    canon_books = set(canon_def.get("books") or [])
    return [c for c in canonical if c in canon_books]


def pick_verse_for_date(
    date_iso,
    *,
    edition_id: str | None = None,
) -> VerseHeadline | None:
    """Deterministically pick a (book, chapter, verse) tuple that has
    at least one note attached for the given date.

    Returns ``None`` only when the corpus has zero notes anywhere
    (impossible in practice — defensive).
    """
    date_norm = _normalize_date(date_iso)
    seed = _seed_for_date(date_norm)
    book_codes = _book_codes_for_edition(edition_id)
    if not book_codes:
        return None

    books_idx = config.books_by_code()

    # Filter to kinds enabled in the edition (if any) so the daily
    # verse always has at least one displayable note for that
    # edition. Reuses the canonical helper from core/matrix.
    enabled_kinds: set | None = None
    if edition_id:
        from .matrix import _enabled_kinds_for_edition

        eds = config.load_editions()
        ed = next(
            (e for e in eds if isinstance(e, dict) and e.get("id") == edition_id),
            None,
        )
        if ed is not None:
            enabled_kinds = _enabled_kinds_for_edition(ed, config.load_kinds())

    notes_dir = paths.notes_dir()

    # Walk books in deterministic-from-seed order, then within each
    # book walk chapters/verses in a stable order; first hit wins.
    n = len(book_codes)
    for offset in range(n):
        book_code = book_codes[(seed + offset) % n]
        path = notes_dir / f"{book_code}.py"
        notes = notes_io.load_notes(path)
        if not notes:
            continue
        # Group notes by (chapter, verse, suffix), filtering by
        # enabled_kinds if requested.
        verses: dict[tuple, list] = {}
        for tup in notes:
            try:
                spec = config.NoteSpec.from_tuple(tup)
            except (ValueError, TypeError):
                continue
            if enabled_kinds is not None and spec.kind not in enabled_kinds:
                continue
            key = (int(spec.chapter), int(spec.verse), spec.suffix or "")
            verses.setdefault(key, []).append(spec)
        if not verses:
            continue
        # Sort keys deterministically and pick by hash.
        keys = sorted(verses.keys())
        ch, vs, suf = keys[seed % len(keys)]
        specs = verses[(ch, vs, suf)]
        # Rank by kind weight, then label length (prefer richer notes).
        ranked = sorted(
            specs,
            key=lambda s: (-_kind_weight(s.kind), -len(s.body_html or ""), s.kind),
        )
        # Top 3 notes max for the feed (don't drown the consumer).
        notes_payload = []
        kinds_idx = config.kinds_by_code()
        cats_idx = config.categories_by_id()
        for spec in ranked[:3]:
            kind_def = kinds_idx.get(spec.kind, {})
            cat_id = kind_def.get("category", "?")
            cat_def = cats_idx.get(cat_id, {})
            notes_payload.append(
                {
                    "kind": spec.kind,
                    "kind_label": kind_def.get("label", spec.kind),
                    "category": cat_id,
                    "category_label": cat_def.get("label", cat_id),
                    "category_symbol": cat_def.get("symbol", "?"),
                    "label": spec.label or "",
                    "title": spec.title or "",
                    "body_html": spec.body_html or "",
                    "attribution": spec.attribution,
                    "anchor": spec.anchor or "",
                }
            )
        book_title = (books_idx.get(book_code) or {}).get("title", book_code)
        return VerseHeadline(
            book_code=book_code,
            book_title=book_title,
            chapter=ch,
            verse=vs,
            suffix=suf,
            notes=tuple(notes_payload),
        )

    return None


def verse_of_day(
    date_iso=None,
    *,
    edition_id: str | None = None,
) -> dict | None:
    """Pick today's (or any date's) verse + headline note(s).
    Returns the JSON-friendly dict the API + RSS layers consume.
    """
    if date_iso is None:
        date_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_norm = _normalize_date(date_iso)
    headline = pick_verse_for_date(date_norm, edition_id=edition_id)
    if headline is None:
        return None
    payload = headline.to_dict()
    payload["date"] = date_norm
    if edition_id:
        payload["edition_id"] = edition_id
    return payload


_RSS_HEADER = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'


def _xml_escape(s) -> str:
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _rfc822_pubdate(d: str) -> str:
    """RSS 2.0 wants RFC-822 dates. We don't track time of day, so use
    midnight UTC."""
    dt = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


def rss_feed(
    *,
    days: int = 7,
    base_url: str = "",
    edition_id: str | None = None,
    today: str | None = None,
) -> str:
    """Emit an RSS 2.0 XML string with one ``<item>`` per day for the
    last ``days`` days (today first, going back). Pure string output;
    no I/O beyond the underlying notes_io reads (which are cached).
    """
    if days < 1:
        days = 1
    if days > 60:
        days = 60
    today_norm = _normalize_date(today) if today else (datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    base = (base_url or "").rstrip("/")
    title_suffix = f" ({edition_id})" if edition_id else ""
    parts = [
        _RSS_HEADER,
        "  <channel>\n",
        f"    <title>Verse of the Day{title_suffix}</title>\n",
        f"    <link>{_xml_escape(base or 'http://localhost/')}</link>\n",
        "    <description>Daily verse from the YHWH Bible publishing platform with editorial apparatus.</description>\n",
        "    <language>en-us</language>\n",
        f'    <atom:link href="{_xml_escape(base + "/api/verse-of-day.rss") if base else ""}" rel="self" type="application/rss+xml" />\n',
    ]
    base_dt = datetime.strptime(today_norm, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    for i in range(days):
        d = (base_dt - timedelta(days=i)).strftime("%Y-%m-%d")
        v = verse_of_day(d, edition_id=edition_id)
        if not v:
            continue
        ref = v.get("ref") or f"{v.get('book_title')} {v.get('chapter')}:{v.get('verse')}"
        notes = v.get("notes") or []
        headline_note = notes[0] if notes else None
        body_html = (headline_note or {}).get("body_html") or ""
        label = (headline_note or {}).get("label") or ""
        title_text = f"{ref}" + (f" — {label}" if label else "")
        # RSS description is HTML; wrap in CDATA so consumers don't
        # re-escape our pre-rendered tags.
        description = (
            f"<p><strong>{_xml_escape(ref)}</strong></p>"
            + (f"<p><em>{_xml_escape(label)}</em></p>" if label else "")
            + (body_html if body_html else "")
        )
        parts.extend(
            [
                "    <item>\n",
                f"      <title>{_xml_escape(title_text)}</title>\n",
                f"      <link>{_xml_escape(base or '')}/sources?book={_xml_escape(v.get('book_code'))}</link>\n",
                f'      <guid isPermaLink="false">verse-of-day:{_xml_escape(d)}{":" + _xml_escape(edition_id) if edition_id else ""}</guid>\n',
                f"      <pubDate>{_rfc822_pubdate(d)}</pubDate>\n",
                f"      <description><![CDATA[{description}]]></description>\n",
                "    </item>\n",
            ]
        )
    parts.extend(
        [
            "  </channel>\n",
            "</rss>\n",
        ]
    )
    return "".join(parts)
