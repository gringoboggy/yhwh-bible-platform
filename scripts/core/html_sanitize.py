"""
html_sanitize.py — whitelist-based HTML sanitizer for note bodies.

Phase ξ.4 (2026-05-08). Note bodies are publisher-authored and may
legitimately contain rich apparatus (`<em>`, `<a>`, `<sup>`, etc.); we
can't strip-everything because that breaks the editorial output. But
we can't trust-everything either — a malicious or noisy source could
inject `<script>`, `onclick=`, `javascript:` URLs, `<iframe>`, etc.

The defense is a whitelist: known-safe tags + known-safe attributes
pass through; everything else is dropped (or in the case of disallowed
tags, the tag is removed but its inner text is preserved). Built on
stdlib `html.parser`; no new dependencies.

Public API:
    sanitize_html(text: str) -> str
        Return a sanitized version of `text`. Idempotent: running the
        result through again yields the same output.

Threat model — explicit:

    The platform is single-user desktop today; the worst that an XSS
    payload could do is execute JS in the reader's EPUB viewer. But
    `<iframe>` + `javascript:` URLs are a class of bug we never want
    to ship even on a single-user platform — the EPUB might be shared,
    the user might browse to one with a noisy upstream source, etc.
    Sanitizing at the build boundary is the defensible posture.

Whitelisted tags:
    Block: p, div, blockquote, ul, ol, li, dl, dt, dd, pre
    Inline: span, a, em, strong, b, i, u, sup, sub, small, mark,
            cite, abbr, q, time, dfn, code, kbd, var, samp,
            ruby, rt, rp, br, wbr
    Headings: h1, h2, h3, h4, h5, h6
    Tables: table, thead, tbody, tfoot, tr, th, td, caption,
            colgroup, col
    Figure: figure, figcaption

Disallowed tag examples (text content is preserved, tag is dropped):
    script, style, iframe, object, embed, link, meta, form, input,
    button, select, textarea, base, frame, frameset, applet, audio,
    video, source, track, map, area, svg, math

Whitelisted attributes:
    All elements: class, lang, dir, title, id (sanitized to a safe
                  CSS-identifier shape).
    `<a>`:        href (must be http/https/mailto/anchor/relative;
                  javascript:/data:/vbscript: rejected), name, target
                  (only "_blank"; rel="noopener noreferrer" auto-added).
    `<th>` / `<td>`: scope, colspan, rowspan.
    `<img>`:      INTENTIONALLY EXCLUDED — note bodies should not embed
                  raw images; covers and per-asset uploads go through
                  validated upload paths (π.4-B). If a future phase
                  needs inline images, wire it through a positive
                  whitelist not by adding `<img>` here.

Disallowed attribute classes:
    All `on*` event handlers (onclick, onerror, onload, onmouseover, …).
    `style` (CSS expressions historically caused XSS in IE; we ship
    no inline styles to keep the threat surface minimal).
    Anything not in the per-tag whitelist.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

# ----------------------------------------------------------------------
# Tag and attribute whitelists
# ----------------------------------------------------------------------

ALLOWED_TAGS: frozenset[str] = frozenset({
    # Block
    "p", "div", "blockquote", "ul", "ol", "li", "dl", "dt", "dd", "pre",
    # Inline
    "span", "a", "em", "strong", "b", "i", "u", "sup", "sub", "small",
    "mark", "cite", "abbr", "q", "time", "dfn", "code", "kbd", "var",
    "samp", "ruby", "rt", "rp", "br", "wbr",
    # Headings
    "h1", "h2", "h3", "h4", "h5", "h6",
    # Tables
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption",
    "colgroup", "col",
    # Figure
    "figure", "figcaption",
    # HR
    "hr",
})

# Tags that are entirely dropped along with their content (no inner
# text preserved). These contain code or markup that's never safe to
# emit. <script> is the canonical case.
TAGS_DROP_CONTENT: frozenset[str] = frozenset({
    "script", "style", "iframe", "object", "embed", "link", "meta",
    "form", "input", "button", "select", "textarea", "base", "frame",
    "frameset", "applet", "svg", "math",
    # Media tags. EPUB 3 supports <audio>/<video> but ρ.1 routes
    # those through a validated build-pipeline pass — note bodies
    # shouldn't embed them directly.
    "audio", "video", "source", "track",
    # Image map / area / map are always disallowed.
    "map", "area",
})

# Self-closing void tags. The serializer emits `<tag />` for these.
VOID_TAGS: frozenset[str] = frozenset({
    "br", "wbr", "hr", "col",
})

# Void tags from the disallowed set — these never have a closing
# tag in HTML5, so the drop-content state machine must NOT push
# them onto the suppress-depth stack (it would never decrement).
DISALLOWED_VOID_TAGS: frozenset[str] = frozenset({
    "input", "meta", "link", "base", "embed", "source", "track",
    "frame", "area", "br",  # br already a void; never disallowed though
})

# Attributes allowed on every element. Per-tag attributes (below)
# add to this baseline.
GLOBAL_ATTRS: frozenset[str] = frozenset({
    "class", "lang", "dir", "title", "id",
})

# Per-tag additional attributes.
TAG_ATTRS: dict[str, frozenset[str]] = {
    "a": frozenset({"href", "name", "target", "rel"}),
    "th": frozenset({"scope", "colspan", "rowspan"}),
    "td": frozenset({"colspan", "rowspan"}),
    "col": frozenset({"span"}),
    "colgroup": frozenset({"span"}),
    "time": frozenset({"datetime"}),
    "q": frozenset({"cite"}),
    "blockquote": frozenset({"cite"}),
    "abbr": frozenset({"title"}),  # already global; explicit for clarity
    "ol": frozenset({"start", "type", "reversed"}),
    "li": frozenset({"value"}),
}

# Safe URL schemes for href / src (we don't allow src, but the URL
# checker is reused). Anything not in this set, plus relative paths
# and anchor-only hrefs, are accepted.
SAFE_URL_SCHEMES: frozenset[str] = frozenset({
    "http", "https", "mailto", "tel",
})

DISALLOWED_URL_SCHEMES: frozenset[str] = frozenset({
    "javascript", "vbscript", "data", "file", "about",
})

# ID values are coerced to a safe CSS-identifier shape:
#   start with a letter, contain only [a-z A-Z 0-9 _ -].
_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9_-]")


def _is_safe_url(url: str) -> bool:
    """Reject javascript:/vbscript:/data: URLs; accept http(s),
    mailto, tel, anchors, and relative paths. Whitespace inside the
    scheme is treated as an attempted bypass (older browsers tolerate
    it) and rejected."""
    s = url.strip()
    if not s:
        return False
    # Leading whitespace inside the scheme — `\tjavascript:...` etc.
    # The HTML spec strips ASCII control chars before scheme parsing
    # in some contexts; we do the same defensively.
    s = re.sub(r"^[\x00-\x20]+", "", s)
    if ":" not in s:
        # Relative path or anchor — no scheme, accept.
        return True
    # Extract the scheme (everything up to the first ":").
    head = s.split(":", 1)[0].lower().strip()
    # Check disallowed first — defense-in-depth.
    if head in DISALLOWED_URL_SCHEMES:
        return False
    # Anchor href like "#foo" reaches here only because there's no
    # ":" in it (handled above) — fall through.
    if head in SAFE_URL_SCHEMES:
        return True
    # Unknown scheme: reject. Future safe schemes can be added to
    # SAFE_URL_SCHEMES explicitly.
    return False


def _is_attr_allowed(tag: str, attr: str) -> bool:
    """True if `attr` is allowed on `tag` per the whitelist. `on*`
    event handlers are always rejected; `style` is always rejected."""
    a = attr.lower()
    if a.startswith("on"):
        return False
    if a == "style":
        return False
    if a in GLOBAL_ATTRS:
        return True
    return a in TAG_ATTRS.get(tag, frozenset())


def _sanitize_attr_value(tag: str, attr: str, value: str) -> str | None:
    """Return the sanitized value, or None to drop the attribute."""
    if value is None:
        return ""
    a = attr.lower()
    # URL attributes — href/src/cite/datetime-with-URL.
    if a in ("href", "src", "cite"):
        return value if _is_safe_url(value) else None
    # `target` on <a>: only "_blank" allowed (anything else is a
    # framing concern we're not handling).
    if a == "target":
        return "_blank" if value.strip() == "_blank" else None
    # `id`: coerce to safe CSS-identifier shape.
    if a == "id":
        v = _SAFE_ID_RE.sub("", value)[:128]
        return v or None
    # Everything else: pass through but escape special chars at
    # serialization time.
    return value


# ----------------------------------------------------------------------
# Parser
# ----------------------------------------------------------------------


class _Sanitizer(HTMLParser):
    """Walks input HTML and emits a whitelisted serialization.

    State machine:
      - When inside a TAGS_DROP_CONTENT element, every event is
        suppressed until the matching close tag is seen. (Handles
        nested cases via a depth counter.)
      - Disallowed tags whose content WE WANT to preserve are
        treated as transparent: the open/close tag is dropped, but
        text events still get serialized. (This is the default for
        anything not in TAGS_DROP_CONTENT.)
      - Allowed tags get re-serialized with their whitelisted
        attributes.

    The parser is `convert_charrefs=True` so character references in
    text content come through as their decoded values; we re-escape
    on emit to preserve the original meaning."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._out: list[str] = []
        # Depth into a TAGS_DROP_CONTENT element. >0 means suppress
        # everything until it returns to 0.
        self._drop_depth = 0
        self._drop_tag_stack: list[str] = []

    def get_output(self) -> str:
        return "".join(self._out)

    # ---- handlers ----

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self._drop_depth:
            if tag in TAGS_DROP_CONTENT and tag not in DISALLOWED_VOID_TAGS:
                # Only push non-void disallowed tags onto the
                # suppress-depth stack — void tags (input, meta,
                # link, embed, source, track, base, frame, area)
                # never produce a matching close event so they'd
                # leave depth permanently stuck.
                self._drop_depth += 1
                self._drop_tag_stack.append(tag)
            return
        if tag in TAGS_DROP_CONTENT:
            if tag in DISALLOWED_VOID_TAGS:
                # Void disallowed tag at top level — drop the tag
                # itself but don't enter suppress mode; nothing
                # follows that needs to be suppressed.
                return
            self._drop_depth = 1
            self._drop_tag_stack = [tag]
            return
        if tag not in ALLOWED_TAGS:
            # Unknown tag: drop the tag itself, keep inner content.
            return
        emitted_attrs = self._emit_attrs(tag, attrs)
        if tag == "a" and any(k == "target" for k, _ in emitted_attrs):
            # Auto-add rel="noopener noreferrer" for safety.
            keys = {k for k, _ in emitted_attrs}
            if "rel" not in keys:
                emitted_attrs.append(("rel", "noopener noreferrer"))
        attr_str = "".join(
            f' {k}="{_escape_attr(v)}"' for k, v in emitted_attrs
        )
        if tag in VOID_TAGS:
            self._out.append(f"<{tag}{attr_str} />")
        else:
            self._out.append(f"<{tag}{attr_str}>")

    def handle_startendtag(self, tag, attrs):
        # Self-closing in source — treat as start of a void tag.
        tag = tag.lower()
        if self._drop_depth:
            return
        if tag in TAGS_DROP_CONTENT or tag not in ALLOWED_TAGS:
            return
        emitted_attrs = self._emit_attrs(tag, attrs)
        attr_str = "".join(
            f' {k}="{_escape_attr(v)}"' for k, v in emitted_attrs
        )
        self._out.append(f"<{tag}{attr_str} />")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self._drop_depth:
            if self._drop_tag_stack and self._drop_tag_stack[-1] == tag:
                self._drop_tag_stack.pop()
                self._drop_depth -= 1
            return
        if tag not in ALLOWED_TAGS:
            return
        if tag in VOID_TAGS:
            return
        self._out.append(f"</{tag}>")

    def handle_data(self, data):
        if self._drop_depth:
            return
        self._out.append(_escape_text(data))

    def handle_entityref(self, name):
        # convert_charrefs=True makes this dead code in practice, but
        # safe to handle.
        if self._drop_depth:
            return
        self._out.append(f"&{name};")

    def handle_charref(self, name):
        if self._drop_depth:
            return
        self._out.append(f"&#{name};")

    def handle_comment(self, data):
        # Comments are always stripped. A `<!--[if IE]><script>...`
        # conditional comment must not survive.
        return

    def handle_decl(self, decl):
        # DOCTYPE and similar — always stripped.
        return

    def handle_pi(self, data):
        # Processing instructions — always stripped.
        return

    # ---- helpers ----

    def _emit_attrs(self, tag, attrs):
        out: list[tuple[str, str]] = []
        for k, v in attrs:
            if not _is_attr_allowed(tag, k):
                continue
            sanitized = _sanitize_attr_value(tag, k, v if v is not None else "")
            if sanitized is None:
                continue
            out.append((k.lower(), sanitized))
        return out


# ----------------------------------------------------------------------
# Escape helpers — match Python stdlib's html.escape semantics.
# ----------------------------------------------------------------------


def _escape_text(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )


def _escape_attr(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace('"', "&quot;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def sanitize_html(text: str) -> str:
    """Return a sanitized version of `text`. Empty input → empty
    output. Idempotent: ``sanitize_html(sanitize_html(x)) ==
    sanitize_html(x)``."""
    if not text:
        return ""
    s = _Sanitizer()
    s.feed(text)
    s.close()
    return s.get_output()
