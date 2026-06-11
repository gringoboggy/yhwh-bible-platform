"""Matrix M1 — the Downloads-catalog manifest generator (spec §5 + the
2026-06-11 per-edition-signature addendum).

``scripts/gen_release_catalog.py`` turns the release's ACTUAL asset list +
SHA256SUMS into ``website/src/data/catalog.json`` for the site build. The
review MEDs it exists to enforce:

  • FULL-COUNT COLUMN GATING — a format column goes live ONLY when every
    edition's SIGNATURE-colour asset (its own cover's colour) is published;
    M2 variant colours light per cell, only where that edition's asset
    exists. Partial uploads must under-show, never over-claim.
  • the asset list is read paginated (a large release truncates a naive
    GET at 100 → columns would silently vanish or over-claim).

Never-remove-live (review MED): while their columns are dark, the
Ethiopian card keeps offering the live v0.1.0 flagship EPUB (everywhere)
and kepub (kobo) — the site serves both today.
"""

from __future__ import annotations

EDITIONS = ["ethiopian-tewahedo", "beta-ed", "gamma-ed"]
SIGNATURES = {
    "ethiopian-tewahedo": ("05_missal_central", "red"),
    "beta-ed": ("03_beadline", "black"),
    "gamma-ed": ("02_classical_corner", "navy"),
}


def _m1_assets(version: str = "0.1.0", editions: list[str] | None = None, extra: list[str] | None = None):
    """Every M1 format's signature-colour asset for ``editions`` (+ extras)."""
    from scripts.build_edition import FORMAT_MATRIX, catalog_asset_name

    names = []
    for f in FORMAT_MATRIX:
        if f["phase"] != "M1":
            continue
        for e in editions if editions is not None else EDITIONS:
            names.append(catalog_asset_name(e, version, f["id"], SIGNATURES[e][1]))
    return names + list(extra or [])


def _sums_for(names: list[str]) -> dict[str, str]:
    return {n: f"{abs(hash(n)):064x}"[:64] for n in names}


def _compute(names, sums=None, tag="v0.1.0", edition_ids=None):
    from scripts.gen_release_catalog import compute_catalog

    return compute_catalog(
        names,
        sums if sums is not None else _sums_for(names),
        tag=tag,
        edition_ids=edition_ids or EDITIONS,
        signatures=SIGNATURES,
    )


class TestComputeCatalog:
    def test_full_m1_set_lights_both_m1_columns(self):
        cat = _compute(_m1_assets())
        by_id = {f["id"]: f for f in cat["formats"]}
        assert by_id["everywhere"]["live"] and by_id["apple"]["live"]
        assert not by_id["kindle"]["live"] and not by_id["play"]["live"]

    def test_cells_keyed_by_signature_colour_carry_name_url_sha256(self):
        from scripts.build_edition import catalog_asset_name

        names = _m1_assets()
        sums = _sums_for(names)
        cat = _compute(names, sums)
        cell = next(f for f in cat["formats"] if f["id"] == "everywhere")["cells"]["gamma-ed"]["navy"]
        expected_name = catalog_asset_name("gamma-ed", "0.1.0", "everywhere", "navy")
        assert cell["name"] == expected_name
        assert cell["url"].endswith(f"/releases/download/v0.1.0/{expected_name}")
        assert cell["sha256"] == sums[expected_name]

    def test_one_missing_edition_kills_the_column(self):
        # Full-count gating: 2 of 3 signature assets present => the column
        # must NOT appear (the third edition's card would 404).
        names = [n for n in _m1_assets() if "beta-ed" not in n or "everywhere" not in n]
        cat = _compute(names)
        by_id = {f["id"]: f for f in cat["formats"]}
        assert not by_id["everywhere"]["live"]
        assert by_id["apple"]["live"]  # untouched column unaffected

    def test_m2_variant_colour_lights_only_its_own_cell(self):
        from scripts.build_edition import catalog_asset_name

        variant = catalog_asset_name("gamma-ed", "0.1.0", "everywhere", "forest")
        cat = _compute(_m1_assets(extra=[variant]))
        ev = next(f for f in cat["formats"] if f["id"] == "everywhere")
        assert ev["live"]
        assert set(ev["cells"]["gamma-ed"]) == {"navy", "forest"}
        assert list(ev["cells"]["gamma-ed"])[0] == "navy"  # signature stays first
        assert set(ev["cells"]["beta-ed"]) == {"black"}  # never over-claim a sibling cell

    def test_dark_column_exposes_no_cells_even_with_partial_assets(self):
        from scripts.build_edition import catalog_asset_name

        partial = [catalog_asset_name("gamma-ed", "0.1.0", "everywhere", "navy")]
        cat = _compute(partial)
        ev = next(f for f in cat["formats"] if f["id"] == "everywhere")
        assert not ev["live"] and ev["cells"] == {}

    def test_kobo_and_everywhere_carry_legacy_cells_while_dark(self):
        cat = _compute([])
        by_id = {f["id"]: f for f in cat["formats"]}
        assert by_id["kobo"]["legacy_cell"]["name"] == "YHWH-Ethiopian-Bible-v0.1.0.kepub.epub"
        assert by_id["everywhere"]["legacy_cell"]["name"] == "YHWH-Ethiopian-Bible-v0.1.0.epub"

    def test_live_everywhere_column_drops_the_legacy_cell(self):
        cat = _compute(_m1_assets())
        ev = next(f for f in cat["formats"] if f["id"] == "everywhere")
        assert ev["live"] and "legacy_cell" not in ev

    def test_editions_carry_signature_and_cover(self):
        cat = _compute(_m1_assets())
        ed = next(e for e in cat["editions"] if e["id"] == "gamma-ed")
        assert ed["signature_design"] == "02_classical_corner"
        assert ed["signature_colour"] == "navy"
        assert ed["cover"] == "covers/gamma-ed.jpg"

    def test_missing_signature_raises(self):
        import pytest

        from scripts.gen_release_catalog import compute_catalog

        with pytest.raises(ValueError, match="signature"):
            compute_catalog([], {}, tag="v0.1.0", edition_ids=["mystery-ed"], signatures={})

    def test_manifest_names_tag_and_version(self):
        cat = _compute([], tag="v1.0.0")
        assert cat["tag"] == "v1.0.0" and cat["version"] == "1.0.0"


class TestRenderCatalogFragment:
    """The no-JS-first HTML fragment build.mjs inlines at {{release_catalog}}:
    one cover CARD per edition (its own signature cover), a download link
    per live format — never a bare colour word as link text."""

    def _catalog(self, names=None):
        cat = _compute(names if names is not None else _m1_assets())
        for e in cat["editions"]:
            e["title"] = e["id"].replace("-", " ").title()
        return cat

    def test_every_edition_renders_a_cover_card(self):
        from scripts.gen_release_catalog import render_catalog_fragment

        html = render_catalog_fragment(self._catalog())
        for e in EDITIONS:
            assert f"covers/{e}.jpg" in html
        assert html.count("card card-static") == len(EDITIONS)

    def test_cards_link_each_live_format_by_device_label(self):
        from scripts.build_edition import catalog_asset_name
        from scripts.gen_release_catalog import render_catalog_fragment

        html = render_catalog_fragment(self._catalog())
        assert html.count("Computer &amp; everywhere else") >= len(EDITIONS)
        assert html.count("Apple Books") >= len(EDITIONS)
        for e in EDITIONS:
            assert catalog_asset_name(e, "0.1.0", "everywhere", SIGNATURES[e][1]) in html

    def test_no_bare_colour_word_link_text(self):
        # The user-directed fix: never "Edition — black". Colours appear in
        # alt text ("… in red"), never as the visible link text.
        from scripts.gen_release_catalog import render_catalog_fragment

        html = render_catalog_fragment(self._catalog())
        for colour in ("black", "brown", "forest", "navy", "red"):
            assert f">{colour}</a>" not in html

    def test_cover_alt_names_design_and_colour(self):
        from scripts.gen_release_catalog import render_catalog_fragment

        html = render_catalog_fragment(self._catalog())
        assert "classical corner in navy" in html
        assert "missal central in red" in html

    def test_dark_state_keeps_covers_note_and_legacy_flagship_offers(self):
        from scripts.gen_release_catalog import render_catalog_fragment

        html = render_catalog_fragment(self._catalog(names=[]))
        assert "being prepared" in html
        assert html.count("card card-static") == len(EDITIONS)  # covers still showcased
        assert "YHWH-Ethiopian-Bible-v0.1.0.epub" in html  # never-remove-live
        assert "YHWH-Ethiopian-Bible-v0.1.0.kepub.epub" in html
        assert ">Apple Books</a>" not in html  # a dark column offers no download link
        assert "-apple-" not in html  # ...and no apple asset URL leaks in

    def test_kobo_sideload_note_present_while_kepub_offered(self):
        from scripts.gen_release_catalog import render_catalog_fragment

        html = render_catalog_fragment(self._catalog())
        assert "sideload" in html and "kepub" in html

    def test_pick_imperative_only_in_the_live_state(self):
        # Review 2026-06-11 finding #6: the page must never instruct a pick
        # the dark state can't honour — the imperative lives in the
        # gate-aware fragment, not the static prose.
        from scripts.gen_release_catalog import render_catalog_fragment

        assert "Pick your edition" in render_catalog_fragment(self._catalog())
        assert "Pick your edition" not in render_catalog_fragment(self._catalog(names=[]))

    def test_sha256sums_link_always_present(self):
        from scripts.gen_release_catalog import render_catalog_fragment

        for names in ([], _m1_assets()):
            html = render_catalog_fragment(self._catalog(names=names))
            assert "SHA256SUMS.txt" in html

    def test_copy_never_carries_a_wrong_book_count(self):
        # The 83-corollary sweep (review MED): catalog copy must never say
        # 87/88 books — the shipped superset is 83.
        from scripts.gen_release_catalog import render_catalog_fragment

        for names in ([], _m1_assets()):
            html = render_catalog_fragment(self._catalog(names=names))
            assert "87" not in html and "88" not in html


class TestNoWithdrawGuard:
    """Never-remove-live, structural (review 2026-06-11 finding #1): a regen
    that would darken a previously-live column refuses to write — the next
    deploy would otherwise withdraw live download links."""

    def test_previously_live_column_going_dark_is_flagged(self):
        from scripts.gen_release_catalog import check_no_withdrawal

        previous = {"formats": [{"id": "everywhere", "live": True}, {"id": "apple", "live": False}]}
        new = {"formats": [{"id": "everywhere", "live": False}, {"id": "apple", "live": False}]}
        assert check_no_withdrawal(previous, new) == ["everywhere"]

    def test_lighting_new_columns_is_never_flagged(self):
        from scripts.gen_release_catalog import check_no_withdrawal

        previous = {"formats": [{"id": "everywhere", "live": True}]}
        new = {"formats": [{"id": "everywhere", "live": True}, {"id": "apple", "live": True}]}
        assert check_no_withdrawal(previous, new) == []

    def test_main_refuses_to_darken_existing_output(self, tmp_path, capsys):
        import json

        from scripts.gen_release_catalog import main

        assets = tmp_path / "assets.json"
        assets.write_text("[]", encoding="utf-8")
        sums = tmp_path / "sums.txt"
        sums.write_text("", encoding="utf-8")
        out = tmp_path / "catalog.json"
        before = json.dumps({"formats": [{"id": "everywhere", "live": True}]})
        out.write_text(before, encoding="utf-8")

        rc = main(["--tag", "v0.1.0", "--assets-file", str(assets), "--sums-file", str(sums), "-o", str(out)])
        assert rc == 1
        assert out.read_text(encoding="utf-8") == before  # untouched
        assert "never-remove-live" in capsys.readouterr().err

        rc = main(
            [
                "--tag",
                "v0.1.0",
                "--assets-file",
                str(assets),
                "--sums-file",
                str(sums),
                "-o",
                str(out),
                "--allow-withdraw",
            ]
        )
        assert rc == 0
        assert json.loads(out.read_text(encoding="utf-8"))["tag"] == "v0.1.0"


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
        manifest = json.loads(out.read_text(encoding="utf-8"))
        assert manifest["tag"] == "v0.1.0"
        # The real editions resolve real signatures + on-disk website covers.
        eth = next(e for e in manifest["editions"] if e["id"] == "ethiopian-tewahedo")
        assert eth["signature_colour"] == "red" and eth["cover"] == "covers/ethiopian-tewahedo.jpg"
        assert (tmp_path / "catalog.html").is_file()


class TestParseSums:
    def test_sha256sum_lines_parse_to_dict(self):
        from scripts.gen_release_catalog import parse_sums

        text = "a" * 64 + "  one.epub\n" + "b" * 64 + "  two.kepub.epub\n"
        assert parse_sums(text) == {"one.epub": "a" * 64, "two.kepub.epub": "b" * 64}

    def test_blank_and_malformed_lines_skipped(self):
        from scripts.gen_release_catalog import parse_sums

        assert parse_sums("\nnot-a-sum-line\n" + "c" * 64 + "  ok.epub\n") == {"ok.epub": "c" * 64}
