"""Tests for refactor — extracted from test_scripts.py in ω.27.

Originally lived in tests/test_scripts.py as part of a 22,000-line
monolithic test file; moved here so each test target sits next to a
single source-of-truth scripts/ module. Future tests for the same
target should land in this file rather than test_scripts.py.
"""

from __future__ import annotations


class TestOmega25BulkRename:
    """ω.25 — atomic project-wide kind-rename. AST-walk for notes
    files (precise position-4 replacement; doesn't touch body text);
    targeted regex for YAML files (kinds.yaml `code:` field +
    enabled_kinds/disabled_kinds list items).

    All tests use synthetic content trees in tmp_path so they don't
    mutate the production tree. Real-tree discovery is exercised
    via the production wiring smoke test at the end.
    """

    @staticmethod
    def _seed_tree(content_dir, *, kind="comm-test", note_kind=None) -> dict:
        """Create a minimal content/ tree containing the kind in
        every supported file shape. Returns paths for assertions."""
        from pathlib import Path

        if note_kind is None:
            note_kind = kind
        content_dir.mkdir(parents=True, exist_ok=True)

        kinds_yaml = content_dir / "kinds.yaml"
        kinds_yaml.write_text(
            "kinds:\n"
            f"  - code: {kind}\n"
            "    category: comm\n"
            "    label: Test\n"
            "  - code: lang-greek\n"
            "    category: lang\n",
            encoding="utf-8",
        )

        editions_yaml = content_dir / "editions.yaml"
        editions_yaml.write_text(
            "editions:\n"
            "  - id: ethiopian-tewahedo\n"
            '    title: "Test"\n'
            "    canon: ethiopian\n"
            "    enabled_categories:\n"
            "      - comm\n"
            "    enabled_kinds:\n"
            f"      - {kind}\n"
            "      - lang-greek\n"
            "    disabled_kinds:\n"
            f"      - {kind}\n",
            encoding="utf-8",
        )

        templates = content_dir / "edition_templates"
        templates.mkdir()
        (templates / "demo.yaml").write_text(
            f"id: demo\nenabled_kinds:\n  - {kind}\n",
            encoding="utf-8",
        )

        scenarios = content_dir / "scenarios"
        scenarios.mkdir()
        (scenarios / "demo.yaml").write_text(
            f"id: demo-scenario\nenabled_kinds:\n  - {kind}\n",
            encoding="utf-8",
        )

        notes = content_dir / "notes"
        notes.mkdir()
        # Two tuples: one with the target kind, one with another;
        # also include the kind code in body text to verify the
        # AST-walk doesn't false-positive there.
        gen_py = notes / "gen.py"
        gen_py.write_text(
            f'"""docstring mentioning {note_kind} should not match."""\n'
            "NOTES = [\n"
            "    (\n"
            "        1, 1, '', '',\n"
            f"        '{note_kind}', 'Title', 'Label',\n"
            f"        '<p>body text mentions {note_kind} for context</p>',\n"
            "    ),\n"
            "    (\n"
            "        1, 2, '', '',\n"
            "        'lang-greek', 'Title', 'Label',\n"
            "        '<p>body</p>',\n"
            "    ),\n"
            "]\n",
            encoding="utf-8",
        )

        return {
            "content": content_dir,
            "kinds": kinds_yaml,
            "editions": editions_yaml,
            "template": templates / "demo.yaml",
            "scenario": scenarios / "demo.yaml",
            "gen_py": gen_py,
        }

    # ---- discovery ----

    def test_discover_finds_every_shape(self, tmp_path):
        from scripts.refactor import discover_kind_usage

        seed = self._seed_tree(tmp_path / "content")
        result = discover_kind_usage(
            "comm-test",
            content_dir=seed["content"],
        )
        # 1 in kinds.yaml + 2 in editions.yaml (enabled + disabled)
        # + 1 in template + 1 in scenario + 1 in gen.py NOTES
        assert result["total"] == 6
        # AST-walk DID NOT match the docstring or body-text mentions.

    def test_discover_unknown_kind_returns_zero(self, tmp_path):
        from scripts.refactor import discover_kind_usage

        seed = self._seed_tree(tmp_path / "content")
        result = discover_kind_usage(
            "nope-not-real",
            content_dir=seed["content"],
        )
        assert result["total"] == 0
        assert result["usage"] == {}

    # ---- plan computation ----

    def test_compute_rename_plan_shape(self, tmp_path):
        from scripts.refactor import compute_kind_rename_plan

        seed = self._seed_tree(tmp_path / "content")
        plan = compute_kind_rename_plan(
            "comm-test",
            "comm-renamed",
            content_dir=seed["content"],
        )
        assert plan["old_code"] == "comm-test"
        assert plan["new_code"] == "comm-renamed"
        # Every entry has the standard {path, rel, kind, count,
        # mutations}. py-kind for notes; yaml-kind otherwise.
        kinds_seen = {f["kind"] for f in plan["files"]}
        assert kinds_seen == {"yaml", "py"}
        # Total mutations matches discovery total above (6).
        assert plan["summary"]["total_mutations"] == 6

    # ---- validation ----

    def test_validate_rejects_identical_codes(self, tmp_path):
        from scripts.refactor import (
            compute_kind_rename_plan,
            validate_kind_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        plan = compute_kind_rename_plan(
            "x",
            "x",
            content_dir=seed["content"],
        )
        errors = validate_kind_rename(
            "x",
            "x",
            plan,
            content_dir=seed["content"],
        )
        assert any("identical" in e for e in errors)

    def test_validate_rejects_missing_old(self, tmp_path):
        from scripts.refactor import (
            compute_kind_rename_plan,
            validate_kind_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        plan = compute_kind_rename_plan(
            "ghost-kind",
            "ghost-renamed",
            content_dir=seed["content"],
        )
        errors = validate_kind_rename(
            "ghost-kind",
            "ghost-renamed",
            plan,
            content_dir=seed["content"],
        )
        assert any("zero references" in e for e in errors)

    def test_validate_rejects_collision(self, tmp_path):
        from scripts.refactor import (
            compute_kind_rename_plan,
            validate_kind_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        # Try renaming comm-test to lang-greek, which already exists.
        plan = compute_kind_rename_plan(
            "comm-test",
            "lang-greek",
            content_dir=seed["content"],
        )
        errors = validate_kind_rename(
            "comm-test",
            "lang-greek",
            plan,
            content_dir=seed["content"],
        )
        assert any("collide" in e or "already appears" in e for e in errors)

    def test_validate_rejects_invalid_shape(self, tmp_path):
        from scripts.refactor import (
            compute_kind_rename_plan,
            validate_kind_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        plan = compute_kind_rename_plan(
            "comm-test",
            "BAD CODE",
            content_dir=seed["content"],
        )
        errors = validate_kind_rename(
            "comm-test",
            "BAD CODE",
            plan,
            content_dir=seed["content"],
        )
        assert any("not a valid kind-code shape" in e for e in errors)

    def test_validate_clean_plan_passes(self, tmp_path):
        from scripts.refactor import (
            compute_kind_rename_plan,
            validate_kind_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        plan = compute_kind_rename_plan(
            "comm-test",
            "comm-new-name",
            content_dir=seed["content"],
        )
        errors = validate_kind_rename(
            "comm-test",
            "comm-new-name",
            plan,
            content_dir=seed["content"],
        )
        assert errors == []

    # ---- apply: dry-run ----

    def test_apply_dry_run_writes_nothing(self, tmp_path):
        from scripts.refactor import (
            compute_kind_rename_plan,
            apply_kind_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        before = seed["kinds"].read_text(encoding="utf-8")
        plan = compute_kind_rename_plan(
            "comm-test",
            "comm-new",
            content_dir=seed["content"],
        )
        result = apply_kind_rename(
            plan,
            dry_run=True,
            refactor_log_path=seed["content"] / ".refactor_log.yaml",
        )
        assert result["ok"] is True
        assert result["dry_run"] is True
        assert seed["kinds"].read_text(encoding="utf-8") == before
        # No audit log file created.
        assert not (seed["content"] / ".refactor_log.yaml").exists()

    # ---- apply: real rewrite ----

    def test_apply_rewrites_yaml_files(self, tmp_path):
        from scripts.refactor import (
            compute_kind_rename_plan,
            apply_kind_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        plan = compute_kind_rename_plan(
            "comm-test",
            "comm-new",
            content_dir=seed["content"],
        )
        result = apply_kind_rename(
            plan,
            dry_run=False,
            refactor_log_path=seed["content"] / ".refactor_log.yaml",
        )
        assert result["ok"] is True
        for path in (seed["kinds"], seed["editions"], seed["template"], seed["scenario"]):
            text = path.read_text(encoding="utf-8")
            assert "comm-test" not in text
            assert "comm-new" in text

    def test_apply_rewrites_notes_files_position_4_only(
        self,
        tmp_path,
    ):
        from scripts.refactor import (
            compute_kind_rename_plan,
            apply_kind_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        plan = compute_kind_rename_plan(
            "comm-test",
            "comm-new",
            content_dir=seed["content"],
        )
        result = apply_kind_rename(plan, dry_run=False)
        assert result["ok"] is True
        text = seed["gen_py"].read_text(encoding="utf-8")
        # Position-4 reference rewritten:
        assert "'comm-new'" in text
        # Body text + docstring NOT rewritten — comm-test still
        # appears there.
        assert "comm-test" in text
        # The rewritten file still parses as Python.
        import ast as _ast

        _ast.parse(text)

    def test_apply_creates_backups(self, tmp_path):
        from scripts.refactor import (
            compute_kind_rename_plan,
            apply_kind_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        plan = compute_kind_rename_plan(
            "comm-test",
            "comm-new",
            content_dir=seed["content"],
        )
        apply_kind_rename(plan, dry_run=False)
        # ensure_backup writes to .backups/ next to the file.
        backups = list(seed["content"].rglob(".backups"))
        assert backups, "expected at least one .backups/ directory"

    def test_apply_writes_audit_log(self, tmp_path):
        from scripts.refactor import (
            compute_kind_rename_plan,
            apply_kind_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        log = seed["content"] / ".refactor_log.yaml"
        plan = compute_kind_rename_plan(
            "comm-test",
            "comm-new",
            content_dir=seed["content"],
        )
        result = apply_kind_rename(
            plan,
            dry_run=False,
            refactor_log_path=log,
        )
        assert log.is_file()
        import yaml as _yaml

        data = _yaml.safe_load(log.read_text(encoding="utf-8"))
        assert "entries" in data
        assert data["entries"][0]["action"] == "rename-kind"
        assert data["entries"][0]["old"] == "comm-test"
        assert data["entries"][0]["new"] == "comm-new"
        assert data["entries"][0]["id"] == result["audit_id"]

    def test_apply_audit_log_appends_per_call(self, tmp_path):
        from scripts.refactor import (
            compute_kind_rename_plan,
            apply_kind_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        log = seed["content"] / ".refactor_log.yaml"
        plan = compute_kind_rename_plan(
            "comm-test",
            "comm-new",
            content_dir=seed["content"],
        )
        apply_kind_rename(plan, dry_run=False, refactor_log_path=log)
        # Second rename: rename comm-new (which we just created)
        # back to a third name. Audit log should now have TWO
        # entries with sequential ids.
        plan2 = compute_kind_rename_plan(
            "comm-new",
            "comm-third",
            content_dir=seed["content"],
        )
        apply_kind_rename(plan2, dry_run=False, refactor_log_path=log)
        import yaml as _yaml

        data = _yaml.safe_load(log.read_text(encoding="utf-8"))
        assert len(data["entries"]) == 2
        assert data["entries"][0]["id"] == "refactor-0001"
        assert data["entries"][1]["id"] == "refactor-0002"

    # ---- rollback ----

    def test_apply_rolls_back_on_python_failure(self, tmp_path):
        # Inject a notes file that the AST-walk thinks is fine, but
        # whose post-rewrite parsing would fail. Simulate by
        # monkeypatching `_write_python_rewrite` to raise.
        from scripts import refactor

        seed = self._seed_tree(tmp_path / "content")
        plan = refactor.compute_kind_rename_plan(
            "comm-test",
            "comm-new",
            content_dir=seed["content"],
        )
        before_yaml = seed["kinds"].read_text(encoding="utf-8")
        before_py = seed["gen_py"].read_text(encoding="utf-8")

        def boom(*a, **kw):
            raise RuntimeError("simulated rewrite failure")

        original = refactor._write_python_rewrite
        refactor._write_python_rewrite = boom
        try:
            result = refactor.apply_kind_rename(
                plan,
                dry_run=False,
                refactor_log_path=seed["content"] / ".refactor_log.yaml",
            )
        finally:
            refactor._write_python_rewrite = original

        assert result["ok"] is False
        # Roll back: every YAML file restored to pre-state.
        assert seed["kinds"].read_text(encoding="utf-8") == before_yaml
        assert seed["gen_py"].read_text(encoding="utf-8") == before_py

    # ---- production wiring ----

    def test_real_tree_discovery_finds_known_kind(self):
        # Pin: discovery against the production tree finds at least
        # one reference to a well-known kind. If a future contributor
        # renames `xref-citation` without going through ω.25, this
        # test surfaces the regression.
        from scripts.refactor import discover_kind_usage

        result = discover_kind_usage("xref-citation")
        assert result["total"] > 100, f"expected >100 references; got {result['total']}"
        assert "content/kinds.yaml" in result["usage"]


class TestOmega251CategoryRename:
    """ω.25.1 — atomic project-wide category-id rename. Same
    framework as ω.25 (kind-rename) with three differences:
      - target file list excludes notes/*.py (categories don't
        appear in note tuples)
      - target file list includes categories.yaml (the registry)
      - YAML patterns are 3 (registry id + kinds.yaml category
        field + enabled_categories list items) instead of 2
    """

    @staticmethod
    def _seed_tree(content_dir, *, cid="comm-test") -> dict:
        """Synthetic tree with a category in every supported
        position. Returns paths for assertions."""
        content_dir.mkdir(parents=True, exist_ok=True)

        categories_yaml = content_dir / "categories.yaml"
        categories_yaml.write_text(
            f"categories:\n  - id: {cid}\n    label: Test\n  - id: lang\n    label: Languages\n",
            encoding="utf-8",
        )

        kinds_yaml = content_dir / "kinds.yaml"
        kinds_yaml.write_text(
            "kinds:\n"
            "  - code: my-kind\n"
            f"    category: {cid}\n"
            "    label: My Kind\n"
            "  - code: lang-greek\n"
            "    category: lang\n",
            encoding="utf-8",
        )

        editions_yaml = content_dir / "editions.yaml"
        editions_yaml.write_text(
            "editions:\n"
            "  - id: ethiopian-tewahedo\n"
            '    title: "Test"\n'
            "    canon: ethiopian\n"
            "    enabled_categories:\n"
            f"      - {cid}\n"
            "      - lang\n"
            "    enabled_kinds:\n"
            "      - my-kind\n",
            encoding="utf-8",
        )

        templates = content_dir / "edition_templates"
        templates.mkdir()
        (templates / "demo.yaml").write_text(
            f"id: demo\nenabled_categories:\n  - {cid}\n",
            encoding="utf-8",
        )

        scenarios = content_dir / "scenarios"
        scenarios.mkdir()
        (scenarios / "demo.yaml").write_text(
            f"id: demo-scenario\nenabled_categories:\n  - {cid}\n",
            encoding="utf-8",
        )

        # No notes/*.py — categories never appear in note tuples.

        return {
            "content": content_dir,
            "categories": categories_yaml,
            "kinds": kinds_yaml,
            "editions": editions_yaml,
            "template": templates / "demo.yaml",
            "scenario": scenarios / "demo.yaml",
        }

    # ---- discovery ----

    def test_discover_finds_every_shape(self, tmp_path):
        from scripts.refactor import discover_category_usage

        seed = self._seed_tree(tmp_path / "content")
        result = discover_category_usage(
            "comm-test",
            content_dir=seed["content"],
        )
        # 1 in categories.yaml (registry) + 1 in kinds.yaml
        # (one kind has category: comm-test) + 1 in editions
        # (enabled_categories item) + 1 in template + 1 in scenario.
        assert result["total"] == 5

    def test_discover_does_not_walk_notes_dir(self, tmp_path):
        # Even if a notes/ dir exists, category discovery doesn't
        # touch it. Pin the contract.
        from scripts.refactor import (
            discover_category_usage,
            category_target_files,
        )

        seed = self._seed_tree(tmp_path / "content")
        notes = seed["content"] / "notes"
        notes.mkdir()
        (notes / "fake.py").write_text(
            "# this file mentions comm-test in a comment\nNOTES = []\n",
            encoding="utf-8",
        )
        targets = category_target_files(seed["content"])
        for t in targets:
            assert t.suffix == ".yaml", f"category targets should be YAML-only; got {t}"
        # Discovery still succeeds with the unrelated notes/ dir.
        result = discover_category_usage(
            "comm-test",
            content_dir=seed["content"],
        )
        assert result["total"] == 5  # same as without notes/

    # ---- plan computation ----

    def test_compute_rename_plan_shape(self, tmp_path):
        from scripts.refactor import compute_category_rename_plan

        seed = self._seed_tree(tmp_path / "content")
        plan = compute_category_rename_plan(
            "comm-test",
            "comm-renamed",
            content_dir=seed["content"],
        )
        assert plan["old_id"] == "comm-test"
        assert plan["new_id"] == "comm-renamed"
        # Every entry uses the YAML rewrite path.
        for f in plan["files"]:
            assert f["kind"] == "yaml"
        assert plan["summary"]["total_mutations"] == 5

    # ---- validation ----

    def test_validate_rejects_collision(self, tmp_path):
        from scripts.refactor import (
            compute_category_rename_plan,
            validate_category_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        plan = compute_category_rename_plan(
            "comm-test",
            "lang",
            content_dir=seed["content"],
        )
        errors = validate_category_rename(
            "comm-test",
            "lang",
            plan,
            content_dir=seed["content"],
        )
        assert any("collide" in e or "already appears" in e for e in errors)

    def test_validate_rejects_invalid_shape(self, tmp_path):
        from scripts.refactor import (
            compute_category_rename_plan,
            validate_category_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        plan = compute_category_rename_plan(
            "comm-test",
            "BAD ID",
            content_dir=seed["content"],
        )
        errors = validate_category_rename(
            "comm-test",
            "BAD ID",
            plan,
            content_dir=seed["content"],
        )
        assert any("not a valid category-id shape" in e for e in errors)

    def test_validate_rejects_missing_old(self, tmp_path):
        from scripts.refactor import (
            compute_category_rename_plan,
            validate_category_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        plan = compute_category_rename_plan(
            "ghost-id",
            "ghost-renamed",
            content_dir=seed["content"],
        )
        errors = validate_category_rename(
            "ghost-id",
            "ghost-renamed",
            plan,
            content_dir=seed["content"],
        )
        assert any("zero references" in e for e in errors)

    def test_validate_clean_plan_passes(self, tmp_path):
        from scripts.refactor import (
            compute_category_rename_plan,
            validate_category_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        plan = compute_category_rename_plan(
            "comm-test",
            "comm-new",
            content_dir=seed["content"],
        )
        errors = validate_category_rename(
            "comm-test",
            "comm-new",
            plan,
            content_dir=seed["content"],
        )
        assert errors == []

    # ---- apply ----

    def test_apply_dry_run_writes_nothing(self, tmp_path):
        from scripts.refactor import (
            compute_category_rename_plan,
            apply_category_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        before = seed["categories"].read_text(encoding="utf-8")
        plan = compute_category_rename_plan(
            "comm-test",
            "comm-new",
            content_dir=seed["content"],
        )
        result = apply_category_rename(
            plan,
            dry_run=True,
            refactor_log_path=seed["content"] / ".refactor_log.yaml",
        )
        assert result["ok"] is True
        assert seed["categories"].read_text(encoding="utf-8") == before

    def test_apply_rewrites_all_three_yaml_shapes(self, tmp_path):
        from scripts.refactor import (
            compute_category_rename_plan,
            apply_category_rename,
        )

        seed = self._seed_tree(tmp_path / "content")
        plan = compute_category_rename_plan(
            "comm-test",
            "comm-new",
            content_dir=seed["content"],
        )
        result = apply_category_rename(
            plan,
            dry_run=False,
            refactor_log_path=seed["content"] / ".refactor_log.yaml",
        )
        assert result["ok"] is True
        for path in (seed["categories"], seed["kinds"], seed["editions"], seed["template"], seed["scenario"]):
            text = path.read_text(encoding="utf-8")
            assert "comm-test" not in text
            assert "comm-new" in text

    def test_apply_writes_audit_log_with_category_action(
        self,
        tmp_path,
    ):
        from scripts.refactor import (
            compute_category_rename_plan,
            apply_category_rename,
        )
        import yaml as _yaml

        seed = self._seed_tree(tmp_path / "content")
        log = seed["content"] / ".refactor_log.yaml"
        plan = compute_category_rename_plan(
            "comm-test",
            "comm-new",
            content_dir=seed["content"],
        )
        apply_category_rename(plan, dry_run=False, refactor_log_path=log)
        data = _yaml.safe_load(log.read_text(encoding="utf-8"))
        assert data["entries"][0]["action"] == "rename-category"
        assert data["entries"][0]["old"] == "comm-test"

    def test_apply_audit_log_shares_id_sequence_with_kind(
        self,
        tmp_path,
    ):
        # Both rename-kind and rename-category append to the same
        # log file with sequential ids; pin that the sequence is
        # shared (no per-action counter).
        from scripts.refactor import (
            compute_category_rename_plan,
            apply_category_rename,
        )
        import yaml as _yaml

        seed = self._seed_tree(tmp_path / "content")
        log = seed["content"] / ".refactor_log.yaml"
        # Pre-seed a refactor-0001 entry as if a kind rename had
        # already happened.
        log.write_text(
            "entries:\n"
            "  - id: refactor-0001\n"
            "    action: rename-kind\n"
            "    old: x\n"
            "    new: y\n"
            "    files: []\n"
            "    applied_at: 2026-05-09T00:00:00Z\n",
            encoding="utf-8",
        )
        plan = compute_category_rename_plan(
            "comm-test",
            "comm-new",
            content_dir=seed["content"],
        )
        result = apply_category_rename(
            plan,
            dry_run=False,
            refactor_log_path=log,
        )
        assert result["audit_id"] == "refactor-0002"
        data = _yaml.safe_load(log.read_text(encoding="utf-8"))
        assert len(data["entries"]) == 2

    def test_apply_rolls_back_on_failure(self, tmp_path):
        from scripts import refactor

        seed = self._seed_tree(tmp_path / "content")
        plan = refactor.compute_category_rename_plan(
            "comm-test",
            "comm-new",
            content_dir=seed["content"],
        )
        before_categories = seed["categories"].read_text(encoding="utf-8")
        before_kinds = seed["kinds"].read_text(encoding="utf-8")

        # Inject a failure mid-apply by replacing _write_yaml_rewrite.
        original = refactor._write_yaml_rewrite
        call_count = [0]

        def boom(*a, **kw):
            call_count[0] += 1
            if call_count[0] >= 2:
                raise RuntimeError("simulated mid-apply failure")
            return original(*a, **kw)

        refactor._write_yaml_rewrite = boom
        try:
            result = refactor.apply_category_rename(
                plan,
                dry_run=False,
                refactor_log_path=seed["content"] / ".refactor_log.yaml",
            )
        finally:
            refactor._write_yaml_rewrite = original

        assert result["ok"] is False
        # Roll back: every YAML file is at its pre-state. The first
        # write (categories.yaml) was applied then rolled back; later
        # files were never touched.
        assert seed["categories"].read_text(encoding="utf-8") == before_categories
        assert seed["kinds"].read_text(encoding="utf-8") == before_kinds

    # ---- production wiring ----

    def test_real_tree_discovery_finds_known_category(self):
        # Pin: discovery against the production tree finds at least
        # one ref to a well-known category. Regression guard.
        from scripts.refactor import discover_category_usage

        result = discover_category_usage("comm")
        assert result["total"] > 5, f"expected >5 references; got {result['total']}"
        # Registry + kinds.yaml + editions.yaml all present.
        assert "content/categories.yaml" in result["usage"]
        assert "content/kinds.yaml" in result["usage"]
        assert "content/editions.yaml" in result["usage"]
