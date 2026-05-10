"""
html_sandbox.py — strict AI-output HTML sandbox.

Phase ξ.15 (2026-05-10). Safety companion to χ-AI-notes (shipped
2026-05-10). The threat model differs from ξ.4's publisher-content
sanitizer (`html_sanitize.py`):

    - ξ.4 threat model: a publisher pastes a noisy or malicious HTML
      blob into a note body. Disallowed tags drop, allowed tags pass.
      Generous allowlist (tables, headings, figures, etc.) because
      legitimate editorial apparatus is wide.

    - ξ.15 threat model: the LLM hallucinates an unsafe construct in
      `comm-ai` draft prose at scale. The model is non-adversarial
      but unpredictable; output is generated thousands of times per
      corpus pass. A strict, narrow allowlist limits the blast radius
      of any single hallucinated construct.

Design: compose `html_sanitize.sanitize_html()` (re-uses parser, URL
safety, escape helpers, attribute logic) and apply a second
restrictive pass that drops everything outside the AI allowlist. Two
gates instead of one: even if a future ξ.4 relaxation lets a tag
through, the AI sandbox keeps the AI surface tight.

Public API:
    sandbox_ai_html(text: str) -> str
        Sandbox `text` through publisher-grade sanitize, then
        AI-strict allowlist. Idempotent.

AI allowlist (intentionally narrow):
    Inline:   em, strong, b, i, sup, sub, code, br, span
    Block:    p
    Anchor:   a — `href` must be an in-document anchor (`#...`) or a
              relative path; absolute http/https/mailto/tel URLs are
              rejected. The model has no business emitting external
              links; cross-references go through xref-citation
              detectors not the AI.

Everything else: tag dropped, inner text preserved (matches
sanitize_html's transparent-tag policy for unknown tags).

Relationship to ξ.4:
    sandbox_ai_html(x) is a strict subset of sanitize_html(x). The
    invariant `set(tags(sandbox_ai_html(x))) ⊆ set(tags(sanitize_html(x)))`
    holds for every x.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

from .html_sanitize import _is_safe_url, _SAFE_ID_RE, sanitize_html

# ----------------------------------------------------------------------
# AI allowlist — narrow by design
# ----------------------------------------------------------------------

AI_ALLOWED_TAGS: frozenset[str] = frozenset(
    {
        # Inline emphasis the LLM uses for label/term highlighting
        "em",
        "strong",
        "b",
        "i",
        "sup",
        "sub",
        "code",
        "br",
        "span",
        # Block: paragraphs only
        "p",
        # Anchor: in-doc / relative only
        "a",
    }
)

# Per-tag attributes for AI surface. <a> is the only tag with attrs;
# class/lang/id remain global via sanitize_html's pass.
AI_TAG_ATTRS: dict[str, frozenset[str]] = {
    "a": frozenset({"href", "class", "lang", "id"}),
}

# Global attrs accepted on AI tags. Narrower than html_sanitize's
# GLOBAL_ATTRS — `dir`, `title` and `target` are dropped on AI surface.
AI_GLOBAL_ATTRS: frozenset[str] = frozenset(
    {
        "class",
        "lang",
        "id",
    }
)

# Void tags inside AI allowlist
AI_VOID_TAGS: frozenset[str] = frozenset({"br"})


def _is_ai_safe_href(value: str) -> bool:
    """Stricter than html_sanitize._is_safe_url: AI surface accepts
    only in-document anchors (`#foo`) and relative paths
    (`notes/gen-1.html#xref`). External http/https/mailto/tel URLs are
    rejected — the AI shouldn't be linking out, and any external link
    is more likely a hallucinated source citation than a real one."""
    if not value:
        return False
    s = value.strip()
    s = re.sub(r"^[\x00-\x20]+", "", s)
    if not s:
        return False
    # Anchor-only — always safe.
    if s.startswith("#"):
        return True
    # No scheme = relative path; defer to the publisher-grade safety
    # check (which also catches "//evil.com" protocol-relative).
    if ":" not in s and not s.startswith("//"):
        # Reuse publisher-grade safety as a sanity floor.
        return _is_safe_url(s)
    # Anything with a scheme or protocol-relative form: reject. The
    # AI surface deliberately excludes external links.
    return False


def _is_ai_attr_allowed(tag: str, attr: str) -> bool:
    a = attr.lower()
    if a.startswith("on"):
        return False
    if a == "style":
        return False
    if a in AI_GLOBAL_ATTRS:
        return True
    return a in AI_TAG_ATTRS.get(tag, frozenset())


def _sanitize_ai_attr_value(tag: str, attr: str, value: str) -> str | None:
    if value is None:
        return ""
    a = attr.lower()
    if a == "href":
        return value if _is_ai_safe_href(value) else None
    if a == "id":
        v = _SAFE_ID_RE.sub("", value)[:128]
        return v or None
    return value


class _AISandbox(HTMLParser):
    """Second-pass restrictor. Walks already-sanitized HTML and drops
    anything outside AI_ALLOWED_TAGS / AI_TAG_ATTRS. Inner text of
    dropped tags is preserved (transparent-tag policy)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._out: list[str] = []

    def get_output(self) -> str:
        return "".join(self._out)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag not in AI_ALLOWED_TAGS:
            return
        emitted = self._emit_attrs(tag, attrs)
        attr_str = "".join(f' {k}="{_escape_attr(v)}"' for k, v in emitted)
        if tag in AI_VOID_TAGS:
            self._out.append(f"<{tag}{attr_str} />")
        else:
            self._out.append(f"<{tag}{attr_str}>")

    def handle_startendtag(self, tag, attrs):
        tag = tag.lower()
        if tag not in AI_ALLOWED_TAGS:
            return
        emitted = self._emit_attrs(tag, attrs)
        attr_str = "".join(f' {k}="{_escape_attr(v)}"' for k, v in emitted)
        self._out.append(f"<{tag}{attr_str} />")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag not in AI_ALLOWED_TAGS:
            return
        if tag in AI_VOID_TAGS:
            return
        self._out.append(f"</{tag}>")

    def handle_data(self, data):
        self._out.append(_escape_text(data))

    def handle_entityref(self, name):
        self._out.append(f"&{name};")

    def handle_charref(self, name):
        self._out.append(f"&#{name};")

    def handle_comment(self, data):
        return

    def handle_decl(self, decl):
        return

    def handle_pi(self, data):
        return

    def _emit_attrs(self, tag, attrs):
        out: list[tuple[str, str]] = []
        for k, v in attrs:
            if not _is_ai_attr_allowed(tag, k):
                continue
            sanitized = _sanitize_ai_attr_value(tag, k, v if v is not None else "")
            if sanitized is None:
                continue
            out.append((k.lower(), sanitized))
        return out


def _escape_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_attr(s: str) -> str:
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def sandbox_ai_html(text: str) -> str:
    """Two-pass strict sandbox for AI-emitted note bodies.

    Pass 1 — `sanitize_html()` (publisher-grade): drops `<script>`,
    `<iframe>`, `javascript:` URLs, `on*` handlers, etc.

    Pass 2 — `_AISandbox`: restricts to the AI allowlist (em / strong /
    b / i / sup / sub / code / br / span / p / a-with-anchor-href).
    Everything else: tag dropped, inner text preserved.

    Idempotent: ``sandbox_ai_html(sandbox_ai_html(x)) == sandbox_ai_html(x)``.
    Empty input → empty output.
    """
    if not text:
        return ""
    cleaned = sanitize_html(text)
    if not cleaned:
        return ""
    s = _AISandbox()
    s.feed(cleaned)
    s.close()
    return s.get_output()
