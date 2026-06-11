"""Matrix M1 — the ``FORMAT_MATRIX`` one-home constant.

The format-matrix spec (docs/superpowers/specs/2026-06-10-website-format-
matrix-design.md §5, review MED) requires the format↔profile↔design table
to live in ONE in-repo home — a ``FORMAT_MATRIX`` constant beside
``TARGET_READERS`` in build_edition.py — consumed by the CI matrix
workflow, the release-catalog generator, and the site build, never
re-typed per consumer (the MATRIX_MAP-#3 drift class). The asset-naming
scheme (spec §4.4: ``YHWH-<edition-id>-v<version>-<format>-<colour>.epub``,
Kobo keeping ``.kepub.epub``) gets the same one-home treatment via
``catalog_asset_name``.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "content" / "covers" / "templates"


def _disk_designs_and_colours() -> tuple[set[str], set[str]]:
    """(design stems, colours) actually shipped in content/covers/templates/,
    parsed from the ``<NN>_<name>_<colour>.png`` filenames."""
    designs: set[str] = set()
    colours: set[str] = set()
    for p in TEMPLATES_DIR.glob("*.png"):
        stem, _, colour = p.stem.rpartition("_")
        designs.add(stem)
        colours.add(colour)
    return designs, colours


class TestFormatMatrixShape:
    """The 5-format table itself — spec §2."""

    def test_five_formats_in_catalog_order(self):
        from scripts.build_edition import FORMAT_MATRIX

        assert tuple(f["id"] for f in FORMAT_MATRIX) == (
            "everywhere",
            "apple",
            "kobo",
            "kindle",
            "play",
        )

    def test_required_fields_present_and_nonempty(self):
        # No cover_design field: covers are the EDITION's, not the format's
        # (spec addendum 2026-06-11 — edition_cover_signature).
        from scripts.build_edition import FORMAT_MATRIX

        required = ("id", "label", "target_reader", "packaging", "phase")
        for entry in FORMAT_MATRIX:
            for field in required:
                assert entry.get(field), f"{entry.get('id')}: missing/empty {field!r}"
            assert "cover_design" not in entry, f"{entry['id']}: per-format designs are retired"

    def test_every_target_reader_is_a_valid_profile(self):
        # The one-resolver invariant: a matrix row can only name a profile the
        # resolver understands — an unknown profile would silently resolve to
        # "everywhere" at build time and ship a mislabeled artifact.
        from scripts.build_edition import FORMAT_MATRIX, TARGET_READERS

        for entry in FORMAT_MATRIX:
            assert entry["target_reader"] in TARGET_READERS

    def test_target_profiles_match_spec(self):
        from scripts.build_edition import FORMAT_MATRIX

        by_id = {f["id"]: f for f in FORMAT_MATRIX}
        assert by_id["everywhere"]["target_reader"] == "everywhere"
        assert by_id["apple"]["target_reader"] == "tablet"
        assert by_id["kobo"]["target_reader"] == "eink"
        assert by_id["kindle"]["target_reader"] == "kindle"
        # Play starts from the vanilla build; promoted to its own target only
        # if the user's phone-QA demands it (spec §2 row 5).
        assert by_id["play"]["target_reader"] == "everywhere"

    def test_packaging_kobo_is_kepub_all_others_epub(self):
        from scripts.build_edition import FORMAT_MATRIX

        for entry in FORMAT_MATRIX:
            expected = "kepub.epub" if entry["id"] == "kobo" else "epub"
            assert entry["packaging"] == expected, entry["id"]

    def test_catalog_labels_match_spec(self):
        from scripts.build_edition import FORMAT_MATRIX

        assert {f["id"]: f["label"] for f in FORMAT_MATRIX} == {
            "everywhere": "Computer & everywhere else",
            "apple": "Apple Books",
            "kobo": "Kobo & e-ink",
            "kindle": "Kindle",
            "play": "Google Play Books",
        }

    def test_gating_phases_match_spec_sequencing(self):
        # §6: M1 ships formats 1-2; Kobo lands at M3 (K-R4-2 calibration),
        # Kindle at M4 (kindle_safe arc), Play at M5 (user phone-QA).
        from scripts.build_edition import FORMAT_MATRIX

        assert {f["id"]: f["phase"] for f in FORMAT_MATRIX} == {
            "everywhere": "M1",
            "apple": "M1",
            "kobo": "M3",
            "kindle": "M4",
            "play": "M5",
        }


class TestEditionCoverSignature:
    """Per-edition signature covers — spec addendum 2026-06-11 (user-
    directed): each edition wears its OWN design + colour; the catalog card
    a visitor sees is the cover inside the file they download."""

    def _edition_ids(self):
        from scripts.core.config import load_editions

        return [e["id"] for e in load_editions() if not e.get("standalone")]

    def test_every_edition_resolves_to_a_known_design_and_colour(self):
        from scripts.build_edition import COVER_COLOURS, edition_cover_signature

        disk_designs, _ = _disk_designs_and_colours()
        for eid in self._edition_ids():
            design, colour = edition_cover_signature(eid)
            assert design in disk_designs, f"{eid}: unknown design {design!r}"
            assert colour in COVER_COLOURS, f"{eid}: unknown colour {colour!r}"

    def test_every_signature_template_png_exists(self):
        from scripts.build_edition import edition_cover_signature

        for eid in self._edition_ids():
            design, colour = edition_cover_signature(eid)
            p = TEMPLATES_DIR / f"{design}_{colour}.png"
            assert p.is_file(), f"{eid}: missing template {p.name}"

    def test_flagship_signature_is_missal_central_red(self):
        # The Ethiopian Tewahedo flagship's recorded identity (σ.2 factory
        # map) — also the cover already on the live v0.1.0 flagship EPUB.
        from scripts.build_edition import edition_cover_signature

        assert edition_cover_signature("ethiopian-tewahedo") == ("05_missal_central", "red")

    def test_signatures_showcase_real_variety(self):
        # The user's directive: the catalog must showcase more than one
        # colour and more than one cover style across the nine editions.
        from scripts.build_edition import edition_cover_signature

        sigs = [edition_cover_signature(e) for e in self._edition_ids()]
        assert len({d for (d, _) in sigs}) >= 3, "fewer than 3 distinct designs across the editions"
        assert len({c for (_, c) in sigs}) >= 3, "fewer than 3 distinct colours across the editions"

    def test_typoed_cover_template_raises(self, monkeypatch):
        import pytest

        from scripts.build_edition import edition_cover_signature
        from scripts.core import config

        monkeypatch.setattr(
            config,
            "editions_by_id",
            lambda: {"bad-ed": {"id": "bad-ed", "cover_template": "01_ornate_leafy_chartreuse"}},
        )
        with pytest.raises(ValueError, match="colour"):
            edition_cover_signature("bad-ed")


class TestCoverTemplateLibrary:
    """The full 25-template library (5 designs × 5 colours) the M2 variant
    generator composites from — a missing PNG breaks a variant cell."""

    def test_cover_colours_match_the_shipped_templates(self):
        from scripts.build_edition import COVER_COLOURS, DEFAULT_COVER_COLOUR

        _, disk_colours = _disk_designs_and_colours()
        assert set(COVER_COLOURS) == disk_colours
        assert DEFAULT_COVER_COLOUR == "black"
        assert DEFAULT_COVER_COLOUR in COVER_COLOURS

    def test_every_design_colour_template_exists_on_disk(self):
        from scripts.build_edition import COVER_COLOURS

        disk_designs, _ = _disk_designs_and_colours()
        assert len(disk_designs) == 5
        for design in disk_designs:
            for colour in COVER_COLOURS:
                p = TEMPLATES_DIR / f"{design}_{colour}.png"
                assert p.is_file(), f"missing template: {p.name}"


class TestFormatById:
    def test_known_id_returns_its_entry(self):
        from scripts.build_edition import format_by_id

        entry = format_by_id("kobo")
        assert entry["target_reader"] == "eink"
        assert entry["packaging"] == "kepub.epub"

    def test_unknown_id_raises_value_error(self):
        import pytest

        from scripts.build_edition import format_by_id

        with pytest.raises(ValueError, match="format"):
            format_by_id("betamax")


class TestCatalogAssetName:
    """Spec §4.4 naming — one home so CI uploads and the catalog generator
    can never disagree on an asset's name."""

    def test_epub_format_name(self):
        from scripts.build_edition import catalog_asset_name

        assert (
            catalog_asset_name("catholic-study", "0.1.0", "everywhere", "black")
            == "YHWH-catholic-study-v0.1.0-everywhere-black.epub"
        )

    def test_kobo_keeps_kepub_epub(self):
        from scripts.build_edition import catalog_asset_name

        assert (
            catalog_asset_name("ethiopian-tewahedo", "1.0.0", "kobo", "navy")
            == "YHWH-ethiopian-tewahedo-v1.0.0-kobo-navy.kepub.epub"
        )

    def test_version_v_prefix_is_normalized(self):
        # Callers pass tags ("v0.1.0") and bare versions ("0.1.0")
        # interchangeably; both must yield the same asset name (never "vv").
        from scripts.build_edition import catalog_asset_name

        assert catalog_asset_name("jewish-study", "v0.1.0", "apple", "brown") == catalog_asset_name(
            "jewish-study", "0.1.0", "apple", "brown"
        )

    def test_unknown_format_raises(self):
        import pytest

        from scripts.build_edition import catalog_asset_name

        with pytest.raises(ValueError, match="format"):
            catalog_asset_name("catholic-study", "0.1.0", "papyrus", "black")

    def test_unknown_colour_raises(self):
        import pytest

        from scripts.build_edition import catalog_asset_name

        with pytest.raises(ValueError, match="colour"):
            catalog_asset_name("catholic-study", "0.1.0", "everywhere", "chartreuse")
