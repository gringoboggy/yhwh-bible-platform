"""Tests for scripts/audit_caches.py (ω.30 lru_cache invalidation audit).

The audit AST-walks scripts/ for `@lru_cache` decorators, then regex-
scans the codebase for `<func>.cache_clear()` call sites. A whitelist
covers caches that intentionally don't need clearing (signature-keyed
or read-once singletons).
"""

from __future__ import annotations


class TestOmega30AuditCaches:
    """ω.30 — cache invalidation audit. Tests focus on the
    discovery + clear-path detection + whitelist application; the
    live `audit()` call is exercised once to verify production state
    is clean."""

    # ---- _is_lru_cache_decorator ----

    def test_decorator_recognizer_bare(self):
        import ast
        from scripts.audit_caches import _is_lru_cache_decorator

        tree = ast.parse("@lru_cache\ndef f(): pass\n")
        dec = tree.body[0].decorator_list[0]
        assert _is_lru_cache_decorator(dec) is True

    def test_decorator_recognizer_call_form(self):
        import ast
        from scripts.audit_caches import _is_lru_cache_decorator

        tree = ast.parse("@lru_cache(maxsize=4)\ndef f(): pass\n")
        dec = tree.body[0].decorator_list[0]
        assert _is_lru_cache_decorator(dec) is True

    def test_decorator_recognizer_qualified(self):
        import ast
        from scripts.audit_caches import _is_lru_cache_decorator

        tree = ast.parse("@functools.lru_cache(maxsize=1024)\ndef f(): pass\n")
        dec = tree.body[0].decorator_list[0]
        assert _is_lru_cache_decorator(dec) is True

    def test_decorator_recognizer_rejects_other(self):
        import ast
        from scripts.audit_caches import _is_lru_cache_decorator

        tree = ast.parse("@cache\ndef f(): pass\n")
        dec = tree.body[0].decorator_list[0]
        assert _is_lru_cache_decorator(dec) is False

    # ---- discover_lru_caches ----

    def test_discover_finds_all_known_caches(self, tmp_path):
        from scripts.audit_caches import discover_lru_caches

        (tmp_path / "a.py").write_text(
            "from functools import lru_cache\n"
            "\n"
            "@lru_cache\n"
            "def cached_one(): return 1\n"
            "\n"
            "@lru_cache(maxsize=4)\n"
            "def cached_two(x): return x\n",
            encoding="utf-8",
        )
        (tmp_path / "b.py").write_text(
            "import functools\n\n@functools.lru_cache(maxsize=1024)\ndef cached_three(): return 3\n",
            encoding="utf-8",
        )
        result = discover_lru_caches(root=tmp_path)
        names = {r["func"] for r in result}
        assert names == {"cached_one", "cached_two", "cached_three"}

    def test_discover_skips_pycache(self, tmp_path):
        from scripts.audit_caches import discover_lru_caches

        (tmp_path / "a.py").write_text(
            "from functools import lru_cache\n@lru_cache\ndef good(): pass\n",
            encoding="utf-8",
        )
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "noise.py").write_text(
            "from functools import lru_cache\n@lru_cache\ndef noise(): pass\n",
            encoding="utf-8",
        )
        result = discover_lru_caches(root=tmp_path)
        names = {r["func"] for r in result}
        assert names == {"good"}

    def test_discover_skips_dotfile_dirs(self, tmp_path):
        from scripts.audit_caches import discover_lru_caches

        (tmp_path / "real.py").write_text(
            "from functools import lru_cache\n@lru_cache\ndef real(): pass\n",
            encoding="utf-8",
        )
        backups = tmp_path / ".backups"
        backups.mkdir()
        (backups / "old.py").write_text(
            "from functools import lru_cache\n@lru_cache\ndef old(): pass\n",
            encoding="utf-8",
        )
        result = discover_lru_caches(root=tmp_path)
        names = {r["func"] for r in result}
        assert names == {"real"}

    # ---- find_clear_sites ----

    def test_find_clear_sites_detects_call(self, tmp_path):
        from scripts.audit_caches import find_clear_sites

        (tmp_path / "src.py").write_text(
            "from functools import lru_cache\n@lru_cache\ndef target(): pass\n",
            encoding="utf-8",
        )
        (tmp_path / "use.py").write_text(
            "import src\n\ndef invalidate():\n    src.target.cache_clear()\n",
            encoding="utf-8",
        )
        sites = find_clear_sites("target", root=tmp_path)
        assert len(sites) == 1
        assert "use.py" in sites[0]["file"]

    def test_find_clear_sites_returns_empty_when_no_clear(self, tmp_path):
        from scripts.audit_caches import find_clear_sites

        (tmp_path / "src.py").write_text(
            "from functools import lru_cache\n@lru_cache\ndef target(): pass\n",
            encoding="utf-8",
        )
        sites = find_clear_sites("target", root=tmp_path)
        assert sites == []

    # ---- load_whitelist ----

    def test_load_whitelist_parses_underscore_dot_form(self, tmp_path):
        from scripts.audit_caches import load_whitelist

        wl = tmp_path / "wl.py"
        wl.write_text(
            '"""Comment header."""\n_.foo\n_.bar_baz\n# _.commented_out — should be ignored\nrandom text\n',
            encoding="utf-8",
        )
        names = load_whitelist(path=wl)
        assert names == {"foo", "bar_baz"}

    def test_load_whitelist_missing_file_returns_empty(self, tmp_path):
        from scripts.audit_caches import load_whitelist

        names = load_whitelist(path=tmp_path / "nope.py")
        assert names == set()

    # ---- audit() ----

    def test_audit_classifies_all_three_statuses(self, tmp_path):
        from scripts.audit_caches import audit

        (tmp_path / "src.py").write_text(
            "from functools import lru_cache\n"
            "@lru_cache\n"
            "def has_clear(): pass\n"
            "@lru_cache\n"
            "def whitelisted(): pass\n"
            "@lru_cache\n"
            "def no_clear(): pass\n",
            encoding="utf-8",
        )
        (tmp_path / "use.py").write_text(
            "import src\nsrc.has_clear.cache_clear()\n",
            encoding="utf-8",
        )
        result = audit(root=tmp_path, whitelist={"whitelisted"})
        by_func = {c["func"]: c["status"] for c in result["caches"]}
        assert by_func["has_clear"] == "clear_path"
        assert by_func["whitelisted"] == "whitelisted"
        assert by_func["no_clear"] == "no_clear_path"
        assert result["ok"] is False  # one no_clear_path remains

    def test_audit_clean_state_on_real_tree(self):
        # Pin: scripts/ has 23 cached functions (15 with clear paths
        # + 8 whitelisted) and zero "no_clear_path" findings. If a
        # future contributor adds a cache without a clear path AND
        # without whitelisting, this test fails.
        from scripts.audit_caches import audit

        result = audit()
        assert result["ok"] is True, "caches without clear paths:\n" + "\n".join(
            f"  {c['file']}:{c['line']}  {c['func']}" for c in result["caches"] if c["status"] == "no_clear_path"
        )
        assert result["summary"]["no_clear_path"] == 0
        # Spot-check: at least one signature-keyed cache + at least
        # one singleton survive the audit.
        funcs = {c["func"]: c["status"] for c in result["caches"]}
        # Signature-keyed caches in web.py (whitelisted):
        assert funcs.get("_cached_attribution_audit") == "whitelisted"
        # Singleton in sources.py (whitelisted):
        assert funcs.get("strongs_hebrew") == "whitelisted"

    # ---- whitelist file ----

    def test_whitelist_file_present(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        wl = repo / "scripts" / ".cache_audit_whitelist.py"
        assert wl.is_file(), "scripts/.cache_audit_whitelist.py is required for ω.30"

    def test_whitelist_documents_categories(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        text = (repo / "scripts" / ".cache_audit_whitelist.py").read_text(encoding="utf-8")
        # Each whitelist entry should sit under a documented section.
        assert "Signature-keyed" in text or "signature" in text.lower()
        assert "singleton" in text.lower()

    # ---- CLI ----

    def test_main_clean_returns_0(self, capsys):
        from scripts.audit_caches import main

        rc = main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "accounted for" in out

    def test_main_json_output(self, capsys):
        from scripts.audit_caches import main
        import json as _json

        rc = main(["--json"])
        out = capsys.readouterr().out
        assert rc == 0
        data = _json.loads(out)
        assert data["ok"] is True
        assert data["summary"]["no_clear_path"] == 0
