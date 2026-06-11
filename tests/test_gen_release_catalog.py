"""Matrix M1 — the Downloads-catalog manifest generator (spec §5).

``scripts/gen_release_catalog.py`` turns the release's ACTUAL asset list +
SHA256SUMS into ``website/src/data/catalog.json`` for the site build. The
two review MEDs it exists to enforce:

  • FULL-COUNT COLUMN GATING — a format column goes live ONLY when every
    edition has its asset for at least one colour; a colour swatch shows
    ONLY when every edition has that colour. Partial uploads must
    under-show, never over-claim.
  • the asset list is read paginated (a ~232-asset release truncates a
    naive GET at 100 → columns would silently vanish or over-claim).

Never-remove-live (review MED): until the M3 Kobo column ships, the kobo
format carries the existing v0.1.0 flagship kepub as a LEGACY cell — the
site serves it today and the catalog must keep offering it.
"""

from __future__ import annotations

EDITIONS = ["alpha-ed", "beta-ed", "gamma-ed"]


def _m1_assets(version: str = "0.1.0", editions: list[str] | None = None, colours: list[str] | None = None):
    from scripts.build_edition import FORMAT_MATRIX, catalog_asset_name

    names = []
    for f in FORMAT_MATRIX:
        if f["phase"] != "M1":
            continue
        for e in editions if editions is not None else EDITIONS:
            for c in colours or ["black"]:
                names.append(catalog_asset_name(e, version, f["id"], c))
    return names


def _sums_for(names: list[str]) -> dict[str, str]:
    return {n: f"{abs(hash(n)):064x}"[:64] for n in names}


class TestComputeCatalog:
    def test_full_m1_set_lights_both_m1_columns_black_only(self):
        from scripts.gen_release_catalog import compute_catalog

        names = _m1_assets()
        cat = compute_catalog(names, _sums_for(names), tag="v0.1.0", edition_ids=EDITIONS)
        by_id = {f["id"]: f for f in cat["formats"]}
        assert by_id["everywhere"]["live"] and by_id["apple"]["live"]
        assert by_id["everywhere"]["colours"] == ["black"]
        assert not by_id["kindle"]["live"] and not by_id["play"]["live"]

    def test_cells_carry_name_url_and_sha256(self):
        from scripts.build_edition import catalog_asset_name
        from scripts.gen_release_catalog import compute_catalog

        names = _m1_assets()
        sums = _sums_for(names)
        cat = compute_catalog(names, sums, tag="v0.1.0", edition_ids=EDITIONS)
        cell = next(f for f in cat["formats"] if f["id"] == "everywhere")["cells"]["alpha-ed"]["black"]
        expected_name = catalog_asset_name("alpha-ed", "0.1.0", "everywhere", "black")
        assert cell["name"] == expected_name
        assert cell["url"].endswith(f"/releases/download/v0.1.0/{expected_name}")
        assert cell["sha256"] == sums[expected_name]

    def test_one_missing_edition_kills_the_column(self):
        # Full-count gating: 2 of 3 editions present => the column must NOT
        # appear (a visitor picking the third edition would hit a 404).
        from scripts.gen_release_catalog import compute_catalog

        names = [n for n in _m1_assets() if "beta-ed" not in n or "everywhere" not in n]
        cat = compute_catalog(names, _sums_for(names), tag="v0.1.0", edition_ids=EDITIONS)
        by_id = {f["id"]: f for f in cat["formats"]}
        assert not by_id["everywhere"]["live"]
        assert by_id["apple"]["live"]  # untouched column unaffected

    def test_partial_colour_shows_only_complete_colours(self):
        from scripts.gen_release_catalog import compute_catalog

        names = _m1_assets(colours=["black"]) + _m1_assets(editions=["alpha-ed"], colours=["navy"])
        cat = compute_catalog(names, _sums_for(names), tag="v0.1.0", edition_ids=EDITIONS)
        ev = next(f for f in cat["formats"] if f["id"] == "everywhere")
        assert ev["colours"] == ["black"]  # navy incomplete -> hidden

    def test_kobo_carries_the_legacy_flagship_cell_until_m3(self):
        from scripts.gen_release_catalog import compute_catalog

        names = _m1_assets()
        cat = compute_catalog(names, _sums_for(names), tag="v0.1.0", edition_ids=EDITIONS)
        kobo = next(f for f in cat["formats"] if f["id"] == "kobo")
        assert not kobo["live"]
        legacy = kobo["legacy_cell"]
        assert legacy["name"] == "YHWH-Ethiopian-Bible-v0.1.0.kepub.epub"
        assert legacy["url"].endswith("/releases/download/v0.1.0/YHWH-Ethiopian-Bible-v0.1.0.kepub.epub")

    def test_manifest_names_tag_and_version(self):
        from scripts.gen_release_catalog import compute_catalog

        cat = compute_catalog([], {}, tag="v1.0.0", edition_ids=EDITIONS)
        assert cat["tag"] == "v1.0.0" and cat["version"] == "1.0.0"


class TestRenderCatalogFragment:
    """The no-JS-first HTML fragment build.mjs inlines at {{release_catalog}}
    (the geez-progress pattern). Static <details> per live format — fully
    usable without JavaScript; enhancement can layer on later."""

    def _catalog(self, names=None):
        from scripts.gen_release_catalog import compute_catalog

        names = names if names is not None else _m1_assets()
        cat = compute_catalog(names, _sums_for(names), tag="v0.1.0", edition_ids=EDITIONS)
        for e in cat["editions"]:
            e["title"] = e["id"].replace("-", " ").title()
        return cat

    def test_no_live_columns_renders_preparing_note_only(self):
        from scripts.gen_release_catalog import render_catalog_fragment

        html = render_catalog_fragment(self._catalog(names=[]))
        assert "<details" not in html
        assert "being prepared" in html

    def test_live_format_lists_every_edition_with_its_link(self):
        from scripts.build_edition import catalog_asset_name
        from scripts.gen_release_catalog import render_catalog_fragment

        html = render_catalog_fragment(self._catalog())
        assert "Computer &amp; everywhere else" in html
        for e in EDITIONS:
            assert catalog_asset_name(e, "0.1.0", "everywhere", "black") in html

    def test_dark_kobo_column_offers_the_legacy_cell(self):
        from scripts.gen_release_catalog import render_catalog_fragment

        html = render_catalog_fragment(self._catalog())
        assert "YHWH-Ethiopian-Bible-v0.1.0.kepub.epub" in html

    def test_copy_never_carries_a_wrong_book_count(self):
        # The 83-corollary sweep (review MED): catalog copy must never say
        # 87/88 books — the shipped superset is 83.
        from scripts.gen_release_catalog import render_catalog_fragment

        for names in ([], _m1_assets()):
            html = render_catalog_fragment(self._catalog(names=names))
            assert "87" not in html and "88" not in html


class TestMainOffline:
    def test_out_of_repo_output_path_works(self, tmp_path, capsys):
        # Regression: the success print used Path.relative_to(REPO_ROOT),
        # which raises on any -o outside the repo (caught on the first
        # simulated-release run).
        import json

        from scripts.gen_release_catalog import main

        assets = tmp_path / "assets.json"
        assets.write_text("[]", encoding="utf-8")
        sums = tmp_path / "sums.txt"
        sums.write_text("", encoding="utf-8")
        out = tmp_path / "catalog.json"
        rc = main(["--tag", "v0.1.0", "--assets-file", str(assets), "--sums-file", str(sums), "-o", str(out)])
        assert rc == 0
        assert json.loads(out.read_text(encoding="utf-8"))["tag"] == "v0.1.0"
        assert (tmp_path / "catalog.html").is_file()


class TestParseSums:
    def test_sha256sum_lines_parse_to_dict(self):
        from scripts.gen_release_catalog import parse_sums

        text = "a" * 64 + "  one.epub\n" + "b" * 64 + "  two.kepub.epub\n"
        assert parse_sums(text) == {"one.epub": "a" * 64, "two.kepub.epub": "b" * 64}

    def test_blank_and_malformed_lines_skipped(self):
        from scripts.gen_release_catalog import parse_sums

        assert parse_sums("\nnot-a-sum-line\n" + "c" * 64 + "  ok.epub\n") == {"ok.epub": "c" * 64}
