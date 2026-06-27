#!/usr/bin/env python3
"""Round-15 gate D1 — release asset-set integrity (offline, file-driven).

The real deploy path (``.github/workflows/format-matrix.yml`` + ``scripts/gen_release_catalog.py``)
builds per-edition assets named by ``build_edition.catalog_asset_name``
(``YHWH-<id>-v<ver>-<fmt>-<colour>.<pkg>``) and APPENDS each one's line to the release's
``SHA256SUMS.txt`` — it never PRUNES, so a withdrawn/retired-SKU asset's sum line lingers,
and ``lint_rules.check_retired_edition_skus`` only scans the repo TREE, so it is blind to a
retired-SKU EPUB still attached to the live GitHub release. This gate closes that hole: given
the attached-asset list and the ``SHA256SUMS.txt`` for a tag, it asserts the two agree and
that every asset is a sanctioned, active, correctly-versioned edition.

This is the OFFLINE verifier (no network). Capture the inputs once, e.g.:
    gh release view <tag> --json assets -q '.assets[].name' > assets.txt
    gh release download <tag> -p SHA256SUMS.txt -O - > sums.txt
then:
    py -3 dev/audit_release_assets.py --tag v0.1.0 --assets-file assets.txt --sums-file sums.txt

Checks:
  1. BIJECTION — every attached asset (except meta files: SHA256SUMS.txt, *.asc/*.sig) has
     exactly one ``SHA256SUMS`` line, and every sums line names an attached asset. An ORPHAN
     sums line (asset gone, line lingers) or a MISSING sum (asset attached, no line) FAILs.
     A duplicate name or a duplicate hash across two names FAILs.
  2. SANCTIONED — every matrix-grammar asset parses to a known ``<fmt>``/``<colour>``; its
     ``<id>`` is an ACTIVE edition (``config.editions_by_id``) and NOT in
     ``lint_rules._RETIRED_EDITION_SKUS``; its ``<ver>`` equals the tag. A retired ``<id>``
     or a stale ``<ver>`` FAILs. A non-grammar name that is not a documented legacy/meta
     asset is a WARN (an asset the deploy path should not have produced).

Legacy never-remove cells (``YHWH-Ethiopian-Bible-v<ver>.epub`` / ``.kepub.epub``, the
v0.1.0 flagship the site has always served — ``gen_release_catalog.LEGACY_*``) are exempt
from the grammar + version checks (they are intentionally pinned), but still take part in the
bijection.

``--selftest`` proves each check is non-tautological. Exit 0 = clean; 1 = any FAIL; 2 = usage.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# matrix-grammar asset name (id may contain hyphens; fmt + colour are single lowercase tokens)
_ASSET_RE = re.compile(
    r"^YHWH-(?P<id>.+)-v(?P<ver>\d+\.\d+\.\d+)-(?P<fmt>[a-z]+)-(?P<colour>[a-z]+)\.(?P<pkg>kepub\.epub|epub)$"
)
# legacy never-remove flagship cells (intentionally pinned to a historical version)
_LEGACY_RE = re.compile(r"^YHWH-Ethiopian-Bible-v\d+\.\d+\.\d+\.(?:kepub\.)?epub$")
# platform / auxiliary release assets (desktop apps + the Kobo font pack) — not edition
# catalog cells, so exempt from the edition grammar; the version-bearing ones are checked.
_PLATFORM_RE = re.compile(
    r"^(?:YHWH-(?P<ver>\d+\.\d+\.\d+)(?:-windows-x64\.exe|-x86_64\.AppImage|\.dmg)|yhwh-kobo-font-pack\.zip)$"
)
# sha256sum line: "<64-hex>  <name>" (two spaces) or "<64-hex> *<name>" (binary marker)
_SUMS_RE = re.compile(r"^(?P<hash>[0-9a-fA-F]{64})\s+\*?(?P<name>.+?)\s*$")
# meta assets that legitimately have no self-sum line
_META_ASSETS = {"SHA256SUMS.txt", "SHA256SUMS"}
_SIG_SUFFIXES = (".asc", ".sig", ".sigstore")


@dataclass
class ReleaseAssetResult:
    tag: str
    fails: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    @property
    def green(self) -> bool:
        return not self.fails


def _is_meta(name: str) -> bool:
    return name in _META_ASSETS or name.endswith(_SIG_SUFFIXES)


def _parse_sums(sums_lines: list[str]) -> tuple[dict[str, str], list[str], list[str]]:
    """Parse a SHA256SUMS body -> (name->hash, fails, warns). Flags dup names + hash collisions."""
    sums_names: dict[str, str] = {}
    hash_to_names: dict[str, list[str]] = {}
    fails: list[str] = []
    warns: list[str] = []
    for raw in sums_lines:
        line = raw.strip()
        if not line:
            continue
        m = _SUMS_RE.match(line)
        if not m:
            warns.append(f"unparseable SHA256SUMS line: {line[:60]!r}")
            continue
        name, h = m.group("name"), m.group("hash").lower()
        if name in sums_names:
            fails.append(f"duplicate SHA256SUMS line for {name!r}")
        sums_names[name] = h
        hash_to_names.setdefault(h, []).append(name)
    for h, names in hash_to_names.items():
        uniq = sorted(set(names))
        if len(uniq) > 1:
            fails.append(f"hash {h[:12]}… shared by {len(uniq)} different assets {uniq} (collision/copy-paste)")
    return sums_names, fails, warns


def _check_grammar_asset(
    a: str,
    m,
    *,
    version: str,
    tag: str,
    active_ids: set[str],
    retired_skus: set[str],
    valid_fmts: set[str],
    valid_colours: set[str],
) -> tuple[list[str], bool, bool]:
    """Validate one matrix-grammar asset -> (fails, is_retired, is_stale)."""
    fails: list[str] = []
    eid, ver, fmt, colour = m.group("id"), m.group("ver"), m.group("fmt"), m.group("colour")
    is_retired = eid in retired_skus
    if is_retired:
        fails.append(f"RETIRED-SKU asset still attached: {a} (edition {eid!r} is in _RETIRED_EDITION_SKUS)")
    elif eid not in active_ids:
        fails.append(f"asset references a NON-ACTIVE edition id {eid!r}: {a}")
    is_stale = ver != version
    if is_stale:
        fails.append(f"asset version v{ver} != tag {tag}: {a}")
    if fmt not in valid_fmts:
        fails.append(f"asset has unknown format {fmt!r} (valid: {sorted(valid_fmts)}): {a}")
    if colour not in valid_colours:
        fails.append(f"asset has unknown cover colour {colour!r} (valid: {sorted(valid_colours)}): {a}")
    return fails, is_retired, is_stale


def check_release_assets(
    asset_names: list[str],
    sums_lines: list[str],
    *,
    tag: str,
    active_ids: set[str],
    retired_skus: set[str],
    valid_fmts: set[str],
    valid_colours: set[str],
) -> tuple[list[str], list[str], dict[str, int]]:
    """Pure detector (selftested). Returns (fails, warns, stats)."""
    version = tag.removeprefix("v")
    assets = [a.strip() for a in asset_names if a.strip()]
    asset_set = set(assets)
    fails: list[str] = []
    warns: list[str] = []
    if len(assets) != len(asset_set):
        fails.append(f"duplicate attached asset name(s): {sorted({a for a in assets if assets.count(a) > 1})}")

    sums_names, sum_fails, sum_warns = _parse_sums(sums_lines)
    fails += sum_fails
    warns += sum_warns

    # Check 1 — bijection (meta files are exempt from needing a self-sum line).
    summed = set(sums_names)
    need_sum = {a for a in asset_set if not _is_meta(a)}
    for a in sorted(need_sum - summed):
        fails.append(f"attached asset has NO SHA256SUMS line (unverifiable download): {a}")
    for n in sorted(summed - asset_set):
        fails.append(f"orphan SHA256SUMS line — no such attached asset (lingering after withdrawal): {n}")

    # Check 2 — sanctioned / active / versioned / not-retired.
    grammar = legacy = meta = unknown = retired = stale_ver = platform = 0
    for a in sorted(asset_set):
        if _is_meta(a):
            meta += 1
        elif _LEGACY_RE.match(a):
            legacy += 1
        elif pm := _PLATFORM_RE.match(a):
            platform += 1
            if pm.group("ver") and pm.group("ver") != version:
                stale_ver += 1
                fails.append(f"platform asset version v{pm.group('ver')} != tag {tag}: {a}")
        elif m := _ASSET_RE.match(a):
            grammar += 1
            gf, is_ret, is_stale = _check_grammar_asset(
                a,
                m,
                version=version,
                tag=tag,
                active_ids=active_ids,
                retired_skus=retired_skus,
                valid_fmts=valid_fmts,
                valid_colours=valid_colours,
            )
            fails += gf
            retired += int(is_ret)
            stale_ver += int(is_stale)
        else:
            unknown += 1
            warns.append(f"asset does not match the catalog grammar or a known legacy/meta/platform name: {a}")

    stats = {
        "attached": len(asset_set),
        "sums_lines": len(sums_names),
        "grammar_assets": grammar,
        "legacy_assets": legacy,
        "platform_assets": platform,
        "meta_assets": meta,
        "unknown_assets": unknown,
        "retired_attached": retired,
        "stale_version": stale_ver,
        "orphan_sums": len(summed - asset_set),
        "missing_sums": len(need_sum - summed),
    }
    return fails, warns, stats


def _load_active_ids() -> set[str]:
    from scripts.core import config

    return set(config.editions_by_id())


def _load_retired_skus() -> set[str]:
    from scripts.lint_rules import _RETIRED_EDITION_SKUS

    return set(_RETIRED_EDITION_SKUS)


def _load_valid_fmts_colours() -> tuple[set[str], set[str]]:
    from scripts.build_edition import COVER_COLOURS, FORMAT_MATRIX

    return {f["id"] for f in FORMAT_MATRIX}, set(COVER_COLOURS)


def audit(tag: str, assets_file: str, sums_file: str) -> ReleaseAssetResult:
    res = ReleaseAssetResult(tag=tag)
    asset_names = Path(assets_file).read_text(encoding="utf-8").splitlines()
    sums_lines = Path(sums_file).read_text(encoding="utf-8").splitlines()
    fmts, colours = _load_valid_fmts_colours()
    fails, warns, stats = check_release_assets(
        asset_names,
        sums_lines,
        tag=tag,
        active_ids=_load_active_ids(),
        retired_skus=_load_retired_skus(),
        valid_fmts=fmts,
        valid_colours=colours,
    )
    res.fails, res.warns, res.stats = fails, warns, stats
    return res


def _selftest() -> int:
    active = {"ethiopian-tewahedo", "catholic-study"}
    retired = {"jewish-study", "coptic-orthodox"}
    fmts = {"everywhere", "apple", "kobo", "kindle", "play"}
    colours = {"black", "brown", "forest", "navy", "red"}

    def run(assets, sums):
        return check_release_assets(
            assets, sums, tag="v0.1.0", active_ids=active, retired_skus=retired, valid_fmts=fmts, valid_colours=colours
        )

    good_assets = [
        "YHWH-ethiopian-tewahedo-v0.1.0-everywhere-black.epub",
        "YHWH-catholic-study-v0.1.0-kobo-navy.kepub.epub",
        "YHWH-Ethiopian-Bible-v0.1.0.epub",  # legacy
        "SHA256SUMS.txt",  # meta, no self-sum
    ]
    good_sums = [
        "a" * 64 + "  YHWH-ethiopian-tewahedo-v0.1.0-everywhere-black.epub",
        "b" * 64 + "  YHWH-catholic-study-v0.1.0-kobo-navy.kepub.epub",
        "c" * 64 + "  YHWH-Ethiopian-Bible-v0.1.0.epub",
    ]
    ok = True
    f_good, _, s_good = run(good_assets, good_sums)
    if f_good:
        print("  ✗ selftest: clean release produced FAILs:", f_good)
        ok = False
    if s_good["grammar_assets"] != 2 or s_good["legacy_assets"] != 1 or s_good["meta_assets"] != 1:
        print("  ✗ selftest: stats wrong on clean set:", s_good)
        ok = False

    # retired SKU attached
    f_ret, _, _ = run(
        good_assets + ["YHWH-jewish-study-v0.1.0-everywhere-black.epub"],
        good_sums + ["d" * 64 + "  YHWH-jewish-study-v0.1.0-everywhere-black.epub"],
    )
    if not any("RETIRED-SKU" in m for m in f_ret):
        print("  ✗ selftest: a retired-SKU asset was NOT flagged")
        ok = False

    # orphan sums line
    f_orph, _, _ = run(good_assets, good_sums + ["e" * 64 + "  YHWH-catholic-study-v0.1.0-apple-red.epub"])
    if not any("orphan" in m for m in f_orph):
        print("  ✗ selftest: an orphan SHA256SUMS line was NOT flagged")
        ok = False

    # missing sum
    f_miss, _, _ = run(good_assets + ["YHWH-catholic-study-v0.1.0-apple-red.epub"], good_sums)
    if not any("NO SHA256SUMS" in m for m in f_miss):
        print("  ✗ selftest: a missing-sum asset was NOT flagged")
        ok = False

    # stale version
    f_ver, _, _ = run(
        ["YHWH-ethiopian-tewahedo-v0.0.9-everywhere-black.epub"],
        ["f" * 64 + "  YHWH-ethiopian-tewahedo-v0.0.9-everywhere-black.epub"],
    )
    if not any("!= tag" in m for m in f_ver):
        print("  ✗ selftest: a stale-version asset was NOT flagged")
        ok = False

    print("  ✓ D1 release-asset-gate selftest passed" if ok else "  selftest FAILED")
    return 0 if ok else 1


def _print(res: ReleaseAssetResult, max_show: int) -> None:
    s = res.stats
    status = "PASS" if res.green else "FAIL"
    print(f"\n=== release {res.tag} — D1 asset-set integrity {status} ===")
    if s:
        print(
            f"  attached={s['attached']} sums={s['sums_lines']} grammar={s['grammar_assets']} "
            f"legacy={s['legacy_assets']} platform={s['platform_assets']} meta={s['meta_assets']} "
            f"unknown={s['unknown_assets']} retired={s['retired_attached']} stale_ver={s['stale_version']} "
            f"orphan_sums={s['orphan_sums']} missing_sums={s['missing_sums']}"
        )
    for f in res.fails[:max_show]:
        print("  ✗", f)
    if len(res.fails) > max_show:
        print(f"  ✗ … +{len(res.fails) - max_show} more FAIL(s)")
    for w in res.warns[:max_show]:
        print("  ⚠", w)


def _arg(argv: list[str], flag: str, default: str | None = None) -> str | None:
    return argv[argv.index(flag) + 1] if flag in argv else default


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    tag = _arg(argv, "--tag")
    assets_file = _arg(argv, "--assets-file")
    sums_file = _arg(argv, "--sums-file")
    max_show = int(_arg(argv, "--max-show", "60"))
    json_out = _arg(argv, "--json")
    if not (tag and assets_file and sums_file):
        print(__doc__)
        return 2
    res = audit(tag, assets_file, sums_file)
    _print(res, max_show)
    if json_out:
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump(
                {"tag": res.tag, "green": res.green, "stats": res.stats, "fails": res.fails, "warns": res.warns},
                fh,
                indent=1,
            )
        print(f"\nwrote {json_out}")
    verdict = "integrity-clean" if res.green else "has integrity FAILs"
    print(f"\n{'PASS' if res.green else 'FAIL'}: release {tag} asset-set {verdict}")
    return 1 if not res.green else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
