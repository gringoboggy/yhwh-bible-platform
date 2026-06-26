#!/usr/bin/env python3
"""Round-14 A1 byte-safety proof (P2) — member-wise before/after.

Proves the ``ocf_member_bytes`` CRLF->LF chokepoint (wired at
``build_epub.py`` + ``kindle_post.py``) changes the packaged EPUB by EXACTLY
the line-ending normalization and nothing else. Build the SAME edition/target
twice over an identical source tree — once with A1 un-wired (PRE), once wired
(POST) — then::

    py -3 dev/audit/round14_a1_byteproof.py <pre.epub> <post.epub>

The whole A1 contract collapses to a single member-wise invariant: for every
OCF member, ``post == ocf_member_bytes(name, pre)``. If that holds across an
identical member set, A1 is proven to be the helper applied at the write
chokepoint with ZERO other change (text members -> LF; binaries + the
extensionless ``mimetype`` byte-for-byte unchanged). PASS exits 0, FAIL exits 1.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.zip_repro import _OCF_TEXT_EXTENSIONS, ocf_member_bytes  # noqa: E402
from tests.test_byte_stability_gate import (  # noqa: E402
    _DATE_RE,
    _MODIFIED_RE,
    _RIGHTS_YEAR_RE,
    _URN_RE,
)


def _members(epub: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(epub) as z:
        return {n: z.read(n) for n in z.namelist()}


def _normalize_volatile(name: str, data: bytes) -> bytes:
    """Strip the per-build OPF fields (generator URN / dcterms:modified / dc:date
    / rights-year) so two separate builds differ only in real content + line
    endings — mirrors ``tests.test_byte_stability_gate._content_digest``."""
    if name.endswith(".opf"):
        t = data.decode("utf-8", "replace")
        t = _URN_RE.sub("urn:yhwh:edition:NORMALIZED", t)
        t = _MODIFIED_RE.sub("", t)
        t = _DATE_RE.sub("<dc:date>NORMALIZED</dc:date>", t)
        t = _RIGHTS_YEAR_RE.sub(r"\g<1>YYYY", t)
        data = t.encode("utf-8")
    return data


def proof(pre_epub: Path, post_epub: Path) -> int:
    pre = _members(pre_epub)
    post = _members(post_epub)

    pre_names, post_names = set(pre), set(post)
    added = sorted(post_names - pre_names)
    dropped = sorted(pre_names - post_names)
    if added or dropped:
        print(f"FAIL: member set changed (INV-1). added={added} dropped={dropped}", file=sys.stderr)
        return 1

    identical = 0
    normalized: list[str] = []
    violations: list[str] = []
    bytes_saved = 0
    for name in sorted(pre_names):
        # Strip per-build OPF volatiles first so the only residual delta is A1's
        # line-ending normalization (two separate builds differ in URN/date).
        raw_pre = _normalize_volatile(name, pre[name])
        raw_post = _normalize_volatile(name, post[name])
        expected = ocf_member_bytes(name, raw_pre)
        if raw_post != expected:
            # post differs from "helper applied to pre" -> an unexplained change.
            kind = "binary-changed" if not name.lower().endswith(_OCF_TEXT_EXTENSIONS) else "text-beyond-crlf"
            violations.append(f"{name} [{kind}] pre={len(raw_pre)}B post={len(raw_post)}B exp={len(expected)}B")
        elif raw_post == raw_pre:
            identical += 1
        else:
            normalized.append(name)
            bytes_saved += len(raw_pre) - len(raw_post)

    print(f"members: {len(pre_names)} | identical: {identical} | CRLF->LF normalized: {len(normalized)}")
    by_ext: dict[str, int] = {}
    for n in normalized:
        ext = "." + n.lower().rsplit(".", 1)[-1] if "." in n else "(none)"
        by_ext[ext] = by_ext.get(ext, 0) + 1
    if by_ext:
        print("  normalized by extension: " + ", ".join(f"{k}={v}" for k, v in sorted(by_ext.items())))
    print(f"  bytes removed (\\r): {bytes_saved}")

    if violations:
        print(f"FAIL: {len(violations)} member(s) changed beyond CRLF->LF:", file=sys.stderr)
        for v in violations[:50]:
            print(f"  {v}", file=sys.stderr)
        return 1

    print("PASS: every member is byte-identical OR exactly ocf_member_bytes(name, pre) — A1 = CRLF->LF only.")
    return 0


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: round14_a1_byteproof.py <pre.epub> <post.epub>", file=sys.stderr)
        return 2
    return proof(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    raise SystemExit(main())
