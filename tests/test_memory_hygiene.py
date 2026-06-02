"""Tests for dev/cc-hooks/memory_hygiene.py — the Claude memory self-maintenance
tool (audit · backup · propose-prune · archive). All run against a synthetic
memory dir in tmp_path; none touch the real memory.
"""

import importlib.util
import sys
import zipfile
from pathlib import Path

import pytest

_HYGIENE = Path(__file__).resolve().parents[1] / "dev" / "cc-hooks" / "memory_hygiene.py"
_spec = importlib.util.spec_from_file_location("memory_hygiene", _HYGIENE)
mh = importlib.util.module_from_spec(_spec)
sys.modules["memory_hygiene"] = mh
_spec.loader.exec_module(mh)


def _write(p: Path, body: str) -> None:
    p.write_text(body, encoding="utf-8")


def _mem(name: str, desc: str, body: str) -> str:
    return f"---\nname: {name}\ndescription: {desc}\ntype: feedback\n---\n\n{body}\n"


@pytest.fixture
def memdir(tmp_path):
    d = tmp_path / "memory"
    d.mkdir()
    # A clean, indexed memory that links to another live memory.
    _write(
        d / "reference_save.md", _mem("reference-save", "save flow", "The 5-leg save. See [[reference_backup_drives]].")
    )
    _write(d / "reference_backup_drives.md", _mem("backup-drives", "backups", "Bundle to E:/F:."))
    # A memory with a DEAD wikilink (target does not exist).
    _write(d / "feedback_x.md", _mem("feedback-x", "x", "Do X. See [[totally_deleted_memory]]."))
    # An ORPHAN: present on disk but absent from MEMORY.md.
    _write(d / "project_orphan.md", _mem("project-orphan", "orphan", "Orphaned fact."))
    # A protected (user_) memory carrying a superseded marker.
    _write(d / "user_test.md", _mem("user-test", "who", "OBSOLETE personal note."))
    # A non-protected memory carrying a superseded marker (prune candidate).
    _write(d / "feedback_old.md", _mem("feedback-old", "old", "This rule is SUPERSEDED by reference_save."))
    # MEMORY.md indexes everything EXCEPT project_orphan, PLUS a dangling link.
    idx = (
        "- [Save](reference_save.md) — the save flow.\n"
        "- [Backups](reference_backup_drives.md) — E:/F:.\n"
        "- [X](feedback_x.md) — do X.\n"
        "- [User](user_test.md) — who.\n"
        "- [Old](feedback_old.md) — old rule.\n"
        "- [Ghost](feedback_ghost.md) — points at a missing file.\n"
    )
    _write(d / "MEMORY.md", idx)
    return d


def test_audit_detects_dead_link_orphan_and_missing_index(memdir):
    rep = mh.audit(memdir)
    kinds = {(i["kind"], i["file"]) for i in rep["issues"]}
    assert ("dead_wikilink", "feedback_x.md") in kinds
    assert ("orphan_no_index", "project_orphan.md") in kinds
    assert ("index_points_to_missing", "MEMORY.md") in kinds
    assert rep["summary"]["warn"] >= 3
    assert rep["summary"]["clean"] is False


def test_audit_live_wikilink_not_flagged(memdir):
    rep = mh.audit(memdir)
    dead = {i["message"] for i in rep["issues"] if i["kind"] == "dead_wikilink"}
    # reference_save links [[reference_backup_drives]] which exists → not flagged.
    assert not any("reference_backup_drives" in m for m in dead)


def test_audit_ignores_meta_placeholder_links(tmp_path):
    d = tmp_path / "memory"
    d.mkdir()
    # A memory that DISCUSSES the memory format must not self-flag its placeholders.
    _write(
        d / "reference_x.md",
        _mem("reference-x", "x", "Memories link via [[name]] / [[their-name]] / [[wikilinks]] placeholders."),
    )
    _write(d / "MEMORY.md", "- [X](reference_x.md) — x.\n")
    rep = mh.audit(d)
    assert not any(i["kind"] == "dead_wikilink" for i in rep["issues"])


def test_audit_clean_dir_has_no_warnings(tmp_path):
    d = tmp_path / "memory"
    d.mkdir()
    _write(d / "reference_save.md", _mem("reference-save", "save", "The save flow."))
    _write(d / "MEMORY.md", "- [Save](reference_save.md) — the save flow.\n")
    rep = mh.audit(d)
    assert rep["summary"]["warn"] == 0
    assert rep["summary"]["clean"] is True


def test_propose_prune_flags_superseded_skips_protected(memdir):
    rep = mh.propose_prune(memdir)
    files = {c["file"] for c in rep["candidates"]}
    assert "feedback_old.md" in files  # non-protected + superseded marker
    assert "user_test.md" not in files  # protected by user_ prefix despite OBSOLETE
    assert "reference_save.md" not in files  # clean + protected


def test_archive_moves_file_drops_index_and_is_reversible(memdir):
    res = mh.archive(memdir, "feedback_old.md", do_backup=False)
    assert res["ok"] is True
    assert not (memdir / "feedback_old.md").is_file()
    assert (memdir / "_archive" / "feedback_old.md").is_file()
    # index line dropped
    assert "feedback_old.md" not in (memdir / "MEMORY.md").read_text(encoding="utf-8")
    # archived files are ignored by a subsequent audit (no _ files scanned)
    rep = mh.audit(memdir)
    assert not any(i["file"] == "feedback_old.md" for i in rep["issues"])


def test_archive_refuses_protected(memdir):
    res = mh.archive(memdir, "user_test.md", do_backup=False)
    assert res["ok"] is False
    assert "PROTECTED" in res["message"]
    assert (memdir / "user_test.md").is_file()  # untouched


def test_archive_missing_file(memdir):
    res = mh.archive(memdir, "nope.md", do_backup=False)
    assert res["ok"] is False


def test_write_memory_zip_roundtrip(memdir, tmp_path):
    dest = tmp_path / "snap.zip"
    bad = mh.write_memory_zip(memdir, dest)
    assert bad is None
    with zipfile.ZipFile(dest) as zf:
        names = zf.namelist()
    assert any(n.endswith("reference_save.md") for n in names)
    assert any(n.endswith("MEMORY.md") for n in names)


def test_backup_refuses_c_and_skips_unmounted(memdir):
    rep = mh.backup(memdir, drives=["C", "Q"])  # C refused; Q (unlikely mounted) skipped
    by = {r["drive"]: r for r in rep["results"]}
    assert by["C"]["ok"] is False and "refused" in by["C"]["message"].lower()
    assert by["Q"]["ok"] is False
    assert rep["ok"] is False  # nothing landed
