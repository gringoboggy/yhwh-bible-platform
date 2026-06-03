"""Manifest folio-entry filler — line-based splice that must stay book-scoped."""

import yaml

from scripts.fill_manifest_entry import fill

SAMPLE = """# header comment (must survive)
1sa:
  1:
    GG:
      folios:
        - f003r
      source_images:
        - x.jpg
    CAM:
      folios:
        - f106r
      views:
        - y.jpg
    status: calibrated

  2:
    GG:
      folios: []
      source_images: []
    CAM:
      folios: []
      views: []
    status: pending

  3:
    GG:
      folios: []
      source_images: []
    CAM:
      folios: []
      views: []
    status: pending

2sa:
  2:
    GG:
      folios: []
      source_images: []
    CAM:
      folios: []
      views: []
    status: pending
"""


def test_fill_targets_right_chapter_and_preserves_rest(tmp_path):
    m = tmp_path / "manifest.yaml"
    m.write_text(SAMPLE, encoding="utf-8")
    fill(m, "1sa", 2, ["fA", "fB"], ["a.jpg", "b.jpg"], ["fC"], ["c.jpg"])
    d = yaml.safe_load(m.read_text(encoding="utf-8"))
    assert d["1sa"][2]["GG"]["folios"] == ["fA", "fB"]
    assert d["1sa"][2]["GG"]["source_images"] == ["a.jpg", "b.jpg"]
    assert d["1sa"][2]["CAM"]["folios"] == ["fC"]
    assert d["1sa"][2]["CAM"]["views"] == ["c.jpg"]
    assert d["1sa"][2]["status"] == "pending"
    # untouched siblings
    assert d["1sa"][1]["status"] == "calibrated"
    assert (d["1sa"][3]["GG"]["folios"] or []) == []
    # header comment preserved (line-based splice, not YAML round-trip)
    assert m.read_text(encoding="utf-8").startswith("# header comment")


def test_fill_is_book_scoped(tmp_path):
    """`  2:` exists under BOTH 1sa and 2sa — filling 2sa must not touch 1sa."""
    m = tmp_path / "manifest.yaml"
    m.write_text(SAMPLE, encoding="utf-8")
    fill(m, "2sa", 2, ["zz"], ["z.jpg"], ["yy"], ["y.jpg"])
    d = yaml.safe_load(m.read_text(encoding="utf-8"))
    assert d["2sa"][2]["GG"]["folios"] == ["zz"]
    assert (d["1sa"][2]["GG"]["folios"] or []) == []  # 1sa2 untouched
