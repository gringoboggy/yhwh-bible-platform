"""Matrix M1 — the catalog cover composites (review blocker #2).

The Downloads-catalog cells carry the FORMAT's design (FORMAT_MATRIX
``cover_design``) composited with the EDITION's cover text — not the
edition's stored tradition cover. The shipped covers are Pillow composites
("HOLY BIBLE" + subtitle via ``fit_text_block``) and the OPF cover slot is
``image/jpeg``, so the variant pipeline needs real per-(edition × design ×
colour) JPEG composites to swap in (raw template PNGs would be wrong twice:
title-less art + PNG bytes in a JPEG slot — spec §4.2). The M1 set is the
9 editions × the 2 M1 formats' designs in the default colour (= 18),
generated locally on the canonical fonts and COMMITTED under
``content/covers/catalog/`` so CI swaps known bytes and never composites
in-runner (kills the ubuntu font-divergence class at the root).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_DIR = REPO_ROOT / "content" / "covers" / "catalog"


class TestM1CatalogPlan:
    def test_plan_is_nine_editions_by_two_m1_designs_in_default_colour(self):
        from scripts.build_edition import DEFAULT_COVER_COLOUR, FORMAT_MATRIX
        from scripts.generate_edition_covers import STANDARD_EDITION_IDS, m1_catalog_plan

        plan = m1_catalog_plan()
        m1_designs = {f["cover_design"] for f in FORMAT_MATRIX if f["phase"] == "M1"}
        assert len(plan) == len(STANDARD_EDITION_IDS) * len(m1_designs) == 18
        assert {(e, d, c) for (e, d, c) in plan} == {
            (e, d, DEFAULT_COVER_COLOUR) for e in STANDARD_EDITION_IDS for d in m1_designs
        }

    def test_plan_orders_editions_in_declaration_order(self):
        # Canonical-order doctrine (§6.1): the batch enumerates editions in
        # their declared order, designs in FORMAT_MATRIX order within each.
        from scripts.generate_edition_covers import STANDARD_EDITION_IDS, m1_catalog_plan

        plan = m1_catalog_plan()
        edition_sequence = [e for (e, _, _) in plan]
        expected = [e for e in STANDARD_EDITION_IDS for _ in range(2)]
        assert edition_sequence == expected


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


class TestCommittedM1Composites:
    """The 18 M1 composites are repo-committed artifacts (M1 is gated on
    their existence — spec §6); CI consumes the bytes, never regenerates."""

    def test_all_18_m1_composites_exist_on_disk(self):
        from scripts.generate_edition_covers import m1_catalog_plan

        missing = [
            f"{e}_{d}_{c}.jpg" for (e, d, c) in m1_catalog_plan() if not (CATALOG_DIR / f"{e}_{d}_{c}.jpg").is_file()
        ]
        assert not missing, f"missing M1 catalog composites: {missing}"

    def test_committed_composites_are_final_size_jpegs(self):
        from scripts.generate_edition_covers import FINAL_HEIGHT, FINAL_WIDTH, m1_catalog_plan

        for e, d, c in m1_catalog_plan():
            p = CATALOG_DIR / f"{e}_{d}_{c}.jpg"
            with Image.open(p) as img:
                assert img.format == "JPEG", p.name
                assert img.size == (FINAL_WIDTH, FINAL_HEIGHT), p.name
