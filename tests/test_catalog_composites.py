"""Downloads-catalog cover composites (spec §4.2 + the 2026-06-11
per-edition-signature addendum).

The signature catalog assets need NO composite — the base build embeds the
edition's own committed cover. Composites are the M2 COLOUR-VARIANT leg:
the edition's OWN design re-composited in each template colour ("HOLY
BIBLE" + subtitle via ``fit_text_block``; a raw template PNG would be wrong
twice — title-less art + PNG bytes in the OPF's image/jpeg cover slot).
Variants are generated locally on the canonical fonts and committed under
``content/covers/catalog/`` when M2 ships; CI swaps committed bytes and
never composites in-runner (the ubuntu font-divergence class).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_DIR = REPO_ROOT / "content" / "covers" / "catalog"


class TestColourVariantPlan:
    def test_plan_is_nine_editions_by_their_own_design_in_all_colours(self):
        from scripts.build_edition import COVER_COLOURS, edition_cover_signature
        from scripts.generate_edition_covers import STANDARD_EDITION_IDS, catalog_colour_variant_plan

        plan = catalog_colour_variant_plan()
        assert len(plan) == len(STANDARD_EDITION_IDS) * len(COVER_COLOURS) == 45
        for e, d, c in plan:
            assert d == edition_cover_signature(e)[0], f"{e}: variant design must be the edition's own"
            assert c in COVER_COLOURS

    def test_plan_orders_editions_in_declaration_order(self):
        # Canonical-order doctrine (§6.1): editions in declared order,
        # colours in COVER_COLOURS order within each.
        from scripts.build_edition import COVER_COLOURS
        from scripts.generate_edition_covers import STANDARD_EDITION_IDS, catalog_colour_variant_plan

        plan = catalog_colour_variant_plan()
        assert [e for (e, _, _) in plan] == [e for e in STANDARD_EDITION_IDS for _ in COVER_COLOURS]
        per_edition_colours = [c for (e, _, c) in plan if e == STANDARD_EDITION_IDS[0]]
        assert per_edition_colours == list(COVER_COLOURS)

    def test_signature_cell_is_in_the_plan(self):
        # The signature colour's composite doubles as a pinnable rendering
        # of the cover the base build embeds.
        from scripts.build_edition import edition_cover_signature
        from scripts.generate_edition_covers import catalog_colour_variant_plan

        design, colour = edition_cover_signature("ethiopian-tewahedo")
        assert ("ethiopian-tewahedo", design, colour) in catalog_colour_variant_plan()


class TestGenerateCatalogComposite:
    def test_writes_final_size_jpeg_with_canonical_name(self, tmp_path):
        from scripts.generate_edition_covers import FINAL_HEIGHT, FINAL_WIDTH, generate_catalog_composite

        out = generate_catalog_composite("catholic-study", "02_classical_corner", "black", out_dir=tmp_path)
        assert out.name == "catholic-study_02_classical_corner_black.jpg"
        assert out.parent == tmp_path
        with Image.open(out) as img:
            assert img.format == "JPEG"
            assert img.size == (FINAL_WIDTH, FINAL_HEIGHT)

    def test_unknown_colour_raises_value_error(self, tmp_path):
        import pytest

        from scripts.generate_edition_covers import generate_catalog_composite

        with pytest.raises(ValueError, match="colour"):
            generate_catalog_composite("catholic-study", "02_classical_corner", "chartreuse", out_dir=tmp_path)

    def test_unknown_design_raises_file_not_found(self, tmp_path):
        import pytest

        from scripts.generate_edition_covers import generate_catalog_composite

        with pytest.raises(FileNotFoundError):
            generate_catalog_composite("catholic-study", "99_nonexistent", "black", out_dir=tmp_path)
