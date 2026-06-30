"""Play Books endnote post-process — relocate hidden popups to reachable
back-matter, WITHOUT the Kindle display-strip / dc:language collapse.

Why this exists (device-QA round-2, cluster A2)
------------------------------------------------
The ``play`` FORMAT_MATRIX cell builds the STANDARD ``everywhere`` artifact —
full apparatus, ``target_reader: everywhere`` — and originally shipped it as-is
(no ``post_process``). That artifact keeps every per-chapter hidden
``<aside class="notes-section" … hidden="">`` wrapper. Play Books' page
("location") estimator counts those wrappers' serialized bytes, so each chapter
end inflates the book by ~85 phantom pages. **User decision: ship full
Kindle-style ENDNOTES on Play** — relocate the notes to visible back-matter,
exactly like the Kindle M4b model.

What Play shares with Kindle — and what it must NOT
---------------------------------------------------
The relocation primitive lives in :mod:`scripts.core.kindle_post`'s
``apply_kindle_m4b`` path: ``_apply_kindle_m4b_members`` →
``_clean_scripture_html`` (``_extract_m4b_asides`` + ``_EMPTY_NOTES_SECTION_RE``)
→ ``_relocate_glossary`` / ``_render_kindle_glossary`` / ``_split_kindle_glossary``
→ ``_retarget_study_badges`` / ``_retarget_vn_links``. That member-transform
moves BOTH note families to back-matter glossaries (study ``vnotes-*`` → "Study
Notes"; translation ``vnote-*`` → "Original-Language Witnesses"), retargets the
badge/vn-link source links cross-file, and DROPS the now-empty notes-section /
verse-refs husks — which is precisely the Play phantom-page cure.

Play, however, **stays standard EPUB3**, so it must NOT receive the Kindle-only
transforms that ride along the rest of the Kindle path:

* ``make_kindle_safe`` (display:none / visibility:hidden physical strip +
  ``<dc:language>`` collapse to a single ``en-US``) — Play renders hidden content
  and honours a multi-valued ``dc:language`` like any EPUB3 reader; collapsing it
  would silently drop the edition's declared original languages.
* ``apply_kindle_m4b_css`` — its ``/* yhwh:kindle-m4b */`` block carries a
  Kindle-ONLY ``body { text-align: justify; }`` rule (a workaround for Amazon's
  KFX converter, which falls back to ragged-left; Play already honours the base
  stylesheet's ``p.verse-p`` justification, so a body-level override would
  over-justify ALL body text and diverge from the other EPUB3 readers). The rest
  of that block is KFX-pagination tuning Play's own paginator does not need (and
  ``.toc-chapter-row`` only exists after ``_flatten_toc_pills``, a make_kindle_safe
  step that never runs for Play). The block is one bundled constant under a single
  marker, so Play applies NONE of it — the phantom-page fix is the husk removal,
  not CSS.

So ``make_play_safe`` reuses the kindle_post relocation member-transform WHOLESALE
(``_apply_kindle_m4b_members``) and re-zips through the same OCF chokepoint
(``_ocf_rezip``), but skips both the Kindle display/language transforms and the
Kindle CSS. The result is a standard EPUB3 with the notes moved to reachable
endnotes and zero phantom-page husks.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

from scripts.core import kindle_post

#: A same-file ``id="…"`` attribute (used to resolve in-scripture ``#frag`` hrefs).
_ID_ATTR_RE = re.compile(r'\bid="([^"]+)"')


def make_play_safe(src_epub: Path | str, dst_epub: Path | str) -> dict:
    """Write a Play-safe endnote EPUB at ``dst_epub`` from the standard
    (``everywhere``) EPUB at ``src_epub``.

    Reuses the kindle_post M4b relocation member-transform
    (:func:`scripts.core.kindle_post._apply_kindle_m4b_members`) WITHOUT the
    Kindle display-strip / ``dc:language`` collapse and WITHOUT the Kindle-only
    ``apply_kindle_m4b_css``: both note families move to reachable back-matter
    glossaries, badges/vn-links are retargeted cross-file, and the now-empty
    notes-section / verse-refs husks (Play's ~85-phantom-pages-per-chapter
    source) are dropped. The result re-zips through the shared reproducible OCF
    packager (``mimetype`` first + stored). Returns the relocation stats dict
    (``asides_relocated``, ``witness_relocated``, ``badges_retargeted``,
    ``vn_links_retargeted``, glossary piece counts, …)."""
    src_epub, dst_epub = Path(src_epub), Path(dst_epub)

    with zipfile.ZipFile(src_epub) as zin:
        order = [i.filename for i in zin.infolist()]
        data: dict[str, bytes] = {name: zin.read(name) for name in order}

    if "mimetype" not in data:
        raise ValueError(f"{src_epub} is not an OCF EPUB (no mimetype member)")

    # Reuse the Kindle M4b member-transform WHOLESALE — relocation, retargeting,
    # and husk removal are reader-agnostic. Deliberately NOT calling
    # apply_kindle_m4b (which also appends apply_kindle_m4b_css) nor
    # make_kindle_safe (display strip + dc:language collapse): Play keeps EPUB3.
    stats = kindle_post._apply_kindle_m4b_members(data, order)

    kindle_post._ocf_rezip(dst_epub, data, order)
    return stats


def verify_play_safe(epub_path: Path | str) -> list[str]:
    """Assert a built Play artifact carries no phantom-page or teleport defect.

    Returns a list of human-readable failures (empty list = clean). Mirrors the
    spirit of :func:`scripts.core.kindle_post.verify_kindle_m4b`, but asserts
    ONLY the two Play-relevant contracts (Play keeps standard EPUB3, so display:none
    and a multi-valued ``dc:language`` are NOT failures):

    (a) **Zero oversized hidden blocks** — reuses ``kindle_post._oversized_hidden_blocks``
        (the ``_E999_HIDDEN_LIMIT`` ruler): a leftover ``hidden=""`` wrapper above
        the size ceiling is exactly the byte mass Play's estimator inflates into
        phantom pages.
    (b) **Zero dangling same-file ``#frag`` references** — every in-scripture
        ``verse-notes-badge`` / ``vn-link`` href that points at a same-file
        ``#id`` must resolve to an id that still exists in that file. After the
        relocation those should all point cross-file to the glossary; a leftover
        same-file fragment whose target was relocated out is the Play
        teleport/phantom bug.

    Also checks the basic OCF invariant (``mimetype`` first + stored), which the
    shared ``_ocf_rezip`` guarantees."""
    epub_path = Path(epub_path)
    fails: list[str] = []
    with zipfile.ZipFile(epub_path) as z:
        infos = z.infolist()
        if not infos or infos[0].filename != "mimetype":
            fails.append("mimetype is not the first zip member (OCF violation)")
        elif infos[0].compress_type != zipfile.ZIP_STORED:
            fails.append("mimetype member is not stored (OCF violation)")
        for info in infos:
            name = info.filename
            if not name.endswith(kindle_post._DOC_SUFFIXES):
                continue
            text = z.read(name).decode("utf-8", "replace")
            # (a) oversized hidden blocks — Play phantom-page byte mass.
            for msg in kindle_post._oversized_hidden_blocks(text):
                fails.append(f"{name}: {msg}")
            # (b) dangling same-file badge / vn-link fragments — only meaningful
            # in scripture (the source links that the relocation retargets).
            if not kindle_post._is_scripture_html(name):
                continue
            ids = set(_ID_ATTR_RE.findall(text))
            for m in kindle_post._BADGE_HREF_RE.finditer(text):
                if m.group(2) not in ids:
                    fails.append(f"{name}: dangling same-file badge href #{m.group(2)} (Play teleport risk)")
            for m in kindle_post._VN_LINK_HREF_RE.finditer(text):
                if m.group(2) not in ids:
                    fails.append(f"{name}: dangling same-file vn-link href #{m.group(2)} (Play teleport risk)")
    return fails
