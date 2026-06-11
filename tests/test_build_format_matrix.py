"""Matrix M1 — the per-edition format-matrix driver (spec §4.3).

The CI workflow runs ONE job per edition with formats serial inside it
(review blocker #4); the per-job work — which formats, which base builds,
which final asset name — is computed HERE from
FORMAT_MATRIX + editions.yaml so the workflow YAML never re-types the
format table or the edition list (the one-home MED). The YAML calls
``scripts/build_format_matrix.py``; these tests pin the driver's pure
planning layer (the build/gate legs are proven on real artifacts, not
simulated in the suite).
"""

from __future__ import annotations

import hashlib
import json


class TestMatrixCells:
    def test_m1_phase_selects_the_two_m1_formats_in_order(self):
        from scripts.build_format_matrix import matrix_cells

        cells = matrix_cells(phase="M1")
        assert [c["id"] for c in cells] == ["everywhere", "apple"]

    def test_unknown_phase_yields_no_cells(self):
        from scripts.build_format_matrix import matrix_cells

        assert matrix_cells(phase="M99") == []


class TestDistinctTargets:
    def test_m1_targets_are_everywhere_and_tablet(self):
        from scripts.build_format_matrix import distinct_targets, matrix_cells

        assert distinct_targets(matrix_cells(phase="M1")) == ["everywhere", "tablet"]

    def test_shared_target_builds_once(self):
        # Two formats on the same profile (e.g. play reuses everywhere) must
        # not trigger a second identical base build.
        from scripts.build_format_matrix import distinct_targets

        cells = [
            {"id": "everywhere", "target_reader": "everywhere"},
            {"id": "play", "target_reader": "everywhere"},
        ]
        assert distinct_targets(cells) == ["everywhere"]


class TestCellAssetName:
    """Spec addendum 2026-06-11: a cell's asset is the base build (the
    edition's own cover already embedded) under the edition's SIGNATURE
    colour — the card a visitor sees is the cover inside the file."""

    def test_cell_asset_carries_the_editions_signature_colour(self):
        from scripts.build_format_matrix import cell_asset_name, matrix_cells

        cell = matrix_cells(phase="M1")[0]
        # catholic-study's signature is 02_classical_corner_navy (factory map).
        assert cell_asset_name("catholic-study", "0.1.0", cell) == "YHWH-catholic-study-v0.1.0-everywhere-navy.epub"

    def test_flagship_signature_colour_is_red(self):
        from scripts.build_format_matrix import cell_asset_name

        assert (
            cell_asset_name("ethiopian-tewahedo", "v0.1.0", {"id": "apple"})
            == "YHWH-ethiopian-tewahedo-v0.1.0-apple-red.epub"
        )


class TestVariantLeg:
    """M2 (spec Addendum A): every cell also ships the edition's OWN design
    in the other template colours — committed composites swapped onto the
    base; signature first, COVER_COLOURS order for the rest."""

    def test_cell_asset_names_signature_first_then_variants(self):
        from scripts.build_format_matrix import cell_asset_names

        names = cell_asset_names("catholic-study", "0.1.0", {"id": "everywhere"})
        assert [c for (c, _) in names] == ["navy", "black", "brown", "forest", "red"]
        assert names[0][1] == "YHWH-catholic-study-v0.1.0-everywhere-navy.epub"
        assert names[2][1] == "YHWH-catholic-study-v0.1.0-everywhere-brown.epub"

    def test_variant_composite_resolves_committed_own_design_file(self):
        from scripts.build_format_matrix import variant_composite_path

        p = variant_composite_path("catholic-study", "forest")
        assert p.name == "catholic-study_02_classical_corner_forest.jpg"
        assert p.is_file(), "M2 is gated on the committed variant composites"

    def test_every_planned_variant_composite_is_committed(self):
        # The full 45-set must be on disk before any CI variant run.
        from scripts.build_format_matrix import CATALOG_COVERS_DIR
        from scripts.generate_edition_covers import catalog_colour_variant_plan

        missing = [
            f"{e}_{d}_{c}.jpg"
            for (e, d, c) in catalog_colour_variant_plan()
            if not (CATALOG_COVERS_DIR / f"{e}_{d}_{c}.jpg").is_file()
        ]
        assert not missing, f"missing variant composites: {missing}"

    def test_missing_composite_raises(self):
        import pytest

        from scripts.build_format_matrix import variant_composite_path

        with pytest.raises(FileNotFoundError, match="composite"):
            variant_composite_path("no-such-edition", "forest")


class TestStandardEditionIds:
    def test_nine_non_standalone_editions_in_declaration_order(self):
        from scripts.build_format_matrix import standard_edition_ids

        ids = standard_edition_ids()
        assert len(ids) == 9
        assert ids[0] == "ethiopian-tewahedo"  # the superset leads
        assert "geez-tewahedo" not in ids and "amharic-tewahedo" not in ids  # LANE P stays out

    def test_list_editions_cli_emits_json(self, capsys):
        from scripts.build_format_matrix import main

        rc = main(["--list-editions"])
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out == list(out) and len(out) == 9


class TestEpubcheckPipJarDiscovery:
    """The driver gates via scripts/epubcheck.py (compose, don't recompute).
    The wrapper must find the PyPI package's bundled jar (the declared
    requirements-dev route, and CI's `pip install epubcheck`) BEFORE the
    PATH wrapper exe — which is broken on Windows (dev/TOOLCHAIN.md) — and
    despite scripts/epubcheck.py shadowing the package name on a CLI run."""

    def test_pip_package_jar_found_without_env_or_path_wrapper(self, monkeypatch):
        from pathlib import Path

        from scripts import epubcheck as wrapper

        monkeypatch.delenv("EPUBCHECK_JAR", raising=False)
        monkeypatch.setattr(wrapper.shutil, "which", lambda name: None)
        kind, path = wrapper.find_epubcheck(None)
        assert kind == "jar"
        assert path is not None and path.endswith("epubcheck.jar")
        assert Path(path).is_file()
        assert "site-packages" in path.replace("\\", "/")


class TestWriteSums:
    def test_sha256sum_compatible_lines_sorted_by_name(self, tmp_path):
        from scripts.build_format_matrix import write_sums

        a = tmp_path / "b-asset.epub"
        a.write_bytes(b"BBB")
        b = tmp_path / "a-asset.epub"
        b.write_bytes(b"AAA")
        sums = write_sums([a, b], tmp_path / "sums.txt")
        lines = sums.read_text(encoding="utf-8").splitlines()
        assert lines == [
            f"{hashlib.sha256(b'AAA').hexdigest()}  a-asset.epub",
            f"{hashlib.sha256(b'BBB').hexdigest()}  b-asset.epub",
        ]
