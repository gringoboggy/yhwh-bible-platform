"""ω.27 follow-on (2026-05-11) — early v1.0 hardening cluster test
classes, split out of the monolithic ``tests/test_scripts.py``
into a topic file alongside the other ω.27 follow-on splits.

Tenth topic extraction. The early v1.0 hardening arc (the pre-
v1.0 foundations that closed the 2026-05-08 security/robustness
scope expansion) shipped six interleaved phases:

- ξ.1   input-validation primitives (parsers + bounds + types)
- ω.10  retry & timeout policy (HTTP client wrapper)
- ξ.2   path-traversal hardening (safe_path resolver)
- ω.9   atomic-write audit linter check (no raw open('w'))
- ω.8   top-level request error boundary (always-200 fallback)
- ξ.4   XSS prevention (HTML sanitizer)

Together these formed the foundation that the later ξ.15-17
late-session cluster built on top of (see test_security_xi_late.py).

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.
"""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------- Phase ξ.1 : input-validation primitives ------------------


class TestValidation:
    """ξ.1 — scripts/core/validation.py is the shared place for
    input-shape validators. Tests cover every validator's happy path
    + every rejection class."""

    @classmethod
    def setup_class(cls):
        from scripts.core import validation

        cls.v = validation

    # ---- require_string / require_short_string ----

    def test_require_string_passes_normal(self):
        assert self.v.require_string("hello", name="x") == "hello"

    def test_require_string_rejects_none(self):
        try:
            self.v.require_string(None, name="x")
        except self.v.ValidationError as e:
            assert "required" in str(e)
            return
        raise AssertionError("expected ValidationError")

    def test_require_string_rejects_int(self):
        try:
            self.v.require_string(42, name="x")
        except self.v.ValidationError as e:
            assert "must be a string" in str(e)
            return
        raise AssertionError("expected ValidationError")

    def test_require_string_rejects_empty_by_default(self):
        try:
            self.v.require_string("", name="x")
        except self.v.ValidationError:
            return
        raise AssertionError("expected ValidationError")

    def test_require_string_allows_empty_when_opted_in(self):
        assert self.v.require_string("", name="x", allow_empty=True) == ""

    def test_require_string_rejects_oversized(self):
        try:
            self.v.require_string("a" * 9999, name="x", max_len=100)
        except self.v.ValidationError as e:
            assert "too long" in str(e)
            return
        raise AssertionError("expected ValidationError")

    def test_require_short_string_caps_at_256(self):
        try:
            self.v.require_short_string("a" * 257, name="x")
        except self.v.ValidationError:
            return
        raise AssertionError("expected ValidationError")

    # ---- validate_book_code ----

    def test_book_code_accepts_gen(self):
        assert self.v.validate_book_code("gen") == "gen"

    def test_book_code_accepts_numeric_prefix(self):
        assert self.v.validate_book_code("1ki") == "1ki"
        assert self.v.validate_book_code("3jn") == "3jn"

    def test_book_code_rejects_uppercase(self):
        try:
            self.v.validate_book_code("Gen")
        except self.v.ValidationError:
            return
        raise AssertionError()

    def test_book_code_rejects_too_long(self):
        try:
            self.v.validate_book_code("genesis")
        except self.v.ValidationError:
            return
        raise AssertionError()

    def test_book_code_rejects_path_traversal_attempt(self):
        try:
            self.v.validate_book_code("../etc")
        except self.v.ValidationError:
            return
        raise AssertionError()

    def test_book_code_rejects_empty(self):
        try:
            self.v.validate_book_code("")
        except self.v.ValidationError:
            return
        raise AssertionError()

    # ---- validate_edition_id ----

    def test_edition_id_accepts_real_values(self):
        for eid in (
            "ethiopian-tewahedo",
            "catholic-study",
            "evangelical-reformed",
            "jewish-study",
            "scholarly-academic",
        ):
            assert self.v.validate_edition_id(eid) == eid

    def test_edition_id_rejects_underscore(self):
        try:
            self.v.validate_edition_id("foo_bar")
        except self.v.ValidationError:
            return
        raise AssertionError()

    def test_edition_id_rejects_leading_digit(self):
        try:
            self.v.validate_edition_id("1edition")
        except self.v.ValidationError:
            return
        raise AssertionError()

    def test_edition_id_rejects_uppercase(self):
        try:
            self.v.validate_edition_id("Catholic-Study")
        except self.v.ValidationError:
            return
        raise AssertionError()

    def test_edition_id_rejects_path_traversal(self):
        try:
            self.v.validate_edition_id("../foo")
        except self.v.ValidationError:
            return
        raise AssertionError()

    # ---- validate_kind_code ----

    def test_kind_code_accepts_real_values(self):
        for kc in ("lang-hebrew", "lang-greek", "comm-doctrine", "xref-citation", "topic-nave"):
            assert self.v.validate_kind_code(kc) == kc

    def test_kind_code_rejects_uppercase(self):
        try:
            self.v.validate_kind_code("Lang-Hebrew")
        except self.v.ValidationError:
            return
        raise AssertionError()

    def test_kind_code_rejects_dot(self):
        try:
            self.v.validate_kind_code("lang.hebrew")
        except self.v.ValidationError:
            return
        raise AssertionError()

    # ---- validate_path_segment ----

    def test_path_segment_accepts_filename(self):
        assert self.v.validate_path_segment("cover.jpg") == "cover.jpg"
        assert self.v.validate_path_segment("file_1.txt") == "file_1.txt"

    def test_path_segment_rejects_slash(self):
        try:
            self.v.validate_path_segment("a/b")
        except self.v.ValidationError:
            return
        raise AssertionError()

    def test_path_segment_rejects_backslash(self):
        try:
            self.v.validate_path_segment("a\\b")
        except self.v.ValidationError:
            return
        raise AssertionError()

    def test_path_segment_rejects_dot(self):
        try:
            self.v.validate_path_segment(".")
        except self.v.ValidationError:
            return
        raise AssertionError()

    def test_path_segment_rejects_dotdot(self):
        try:
            self.v.validate_path_segment("..")
        except self.v.ValidationError:
            return
        raise AssertionError()

    def test_path_segment_rejects_nul(self):
        try:
            self.v.validate_path_segment("foo\x00.txt")
        except self.v.ValidationError:
            return
        raise AssertionError()

    # ---- chapter / verse ----

    def test_chapter_accepts_int(self):
        assert self.v.validate_chapter(1) == 1
        assert self.v.validate_chapter(150) == 150

    def test_chapter_accepts_string_int(self):
        assert self.v.validate_chapter("42") == 42

    def test_chapter_rejects_zero(self):
        try:
            self.v.validate_chapter(0)
        except self.v.ValidationError:
            return
        raise AssertionError()

    def test_chapter_rejects_negative(self):
        try:
            self.v.validate_chapter(-1)
        except self.v.ValidationError:
            return
        raise AssertionError()

    def test_chapter_rejects_oversized(self):
        try:
            self.v.validate_chapter(99999)
        except self.v.ValidationError:
            return
        raise AssertionError()

    def test_chapter_rejects_bool(self):
        # bool is a subclass of int but treating True as chapter 1
        # would be a footgun.
        try:
            self.v.validate_chapter(True)
        except self.v.ValidationError as e:
            assert "bool" in str(e)
            return
        raise AssertionError()

    def test_chapter_rejects_garbage_string(self):
        try:
            self.v.validate_chapter("not-a-number")
        except self.v.ValidationError:
            return
        raise AssertionError()

    def test_verse_accepts_int(self):
        assert self.v.validate_verse(1) == 1
        assert self.v.validate_verse(176) == 176  # Psalm 119

    def test_verse_rejects_zero(self):
        try:
            self.v.validate_verse(0)
        except self.v.ValidationError:
            return
        raise AssertionError()

    # ---- to_error_dict ----

    def test_to_error_dict_shape(self):
        try:
            self.v.validate_chapter(-1)
        except self.v.ValidationError as e:
            d = self.v.to_error_dict(e)
            assert d["status"] == "error"
            assert d["code"] == "validation_error"
            assert d["http"] == 400
            assert "out of range" in d["message"]
            return
        raise AssertionError()

    def test_to_error_dict_custom_http(self):
        try:
            self.v.validate_chapter(-1)
        except self.v.ValidationError as e:
            d = self.v.to_error_dict(e, http=422)
            assert d["http"] == 422


# ---------- Phase ω.10 : retry & timeout policy ----------------------


class TestHttpRetryWrapper:
    """ω.10 — scripts/core/http.py centralizes outbound HTTP with a
    consistent retry+timeout policy. Tests stub urlopen and sleep
    so they run instantly and deterministically."""

    @classmethod
    def setup_class(cls):
        from scripts.core import http

        cls.http = http

    # ---- happy path ----

    def test_get_returns_bytes_on_success(self):
        class FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

            def read(self):
                return b"hello"

        def fake_open(url, timeout):
            return FakeResp()

        out = self.http.get(
            "https://x.org",
            allowlist={"x.org"},
            urlopen=fake_open,
            sleep_fn=lambda s: None,
        )
        assert out == b"hello"

    def test_get_json_parses_payload(self):
        class FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

            def read(self):
                return b'{"k":"v","n":[1,2]}'

        out = self.http.get_json(
            "https://x.org",
            allowlist={"x.org"},
            urlopen=lambda url, timeout: FakeResp(),
            sleep_fn=lambda s: None,
        )
        assert out == {"k": "v", "n": [1, 2]}

    def test_timeout_is_passed_to_urlopen(self):
        seen = []

        class FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

            def read(self):
                return b""

        def fake(url, timeout):
            seen.append(timeout)
            return FakeResp()

        self.http.get(
            "https://x.org",
            allowlist={"x.org"},
            timeout=7,
            urlopen=fake,
            sleep_fn=lambda s: None,
        )
        assert seen == [7]

    # ---- retry on transient failure ----

    def test_retries_on_url_error_then_succeeds(self):
        import urllib.error

        attempts = [0]
        sleeps = []

        class FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

            def read(self):
                return b"after-retry"

        def flaky(url, timeout):
            attempts[0] += 1
            if attempts[0] < 3:
                raise urllib.error.URLError("connection reset")
            return FakeResp()

        out = self.http.get(
            "https://x.org",
            allowlist={"x.org"},
            retries=2,
            urlopen=flaky,
            sleep_fn=lambda s: sleeps.append(s),
        )
        assert out == b"after-retry"
        assert attempts[0] == 3  # 1 initial + 2 retries
        # Two sleeps between three attempts; backoff exponential.
        assert len(sleeps) == 2
        assert sleeps[0] < sleeps[1]  # exponential growth

    def test_retries_on_5xx_then_succeeds(self):
        import urllib.error

        attempts = [0]

        class FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

            def read(self):
                return b"recovered"

        def flaky(url, timeout):
            attempts[0] += 1
            if attempts[0] == 1:
                raise urllib.error.HTTPError(
                    url,
                    503,
                    "Service Unavailable",
                    {},
                    None,
                )
            return FakeResp()

        out = self.http.get(
            "https://x.org",
            allowlist={"x.org"},
            retries=2,
            urlopen=flaky,
            sleep_fn=lambda s: None,
        )
        assert out == b"recovered"
        assert attempts[0] == 2

    def test_retries_on_timeout(self):
        attempts = [0]

        class FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

            def read(self):
                return b"finally"

        def flaky(url, timeout):
            attempts[0] += 1
            if attempts[0] == 1:
                raise TimeoutError("read timed out")
            return FakeResp()

        out = self.http.get(
            "https://x.org",
            allowlist={"x.org"},
            urlopen=flaky,
            sleep_fn=lambda s: None,
        )
        assert out == b"finally"

    # ---- no-retry on 4xx ----

    def test_does_not_retry_on_404(self):
        import urllib.error

        attempts = [0]

        def fail(url, timeout):
            attempts[0] += 1
            raise urllib.error.HTTPError(
                url,
                404,
                "Not Found",
                {},
                None,
            )

        try:
            self.http.get(
                "https://x.org",
                allowlist={"x.org"},
                retries=2,
                urlopen=fail,
                sleep_fn=lambda s: None,
            )
        except self.http.HttpError as e:
            assert e.attempts == 1  # NO retries on a 4xx
            assert e.last_exc.code == 404
            return
        raise AssertionError("expected HttpError")

    def test_does_not_retry_on_400(self):
        import urllib.error

        attempts = [0]

        def fail(url, timeout):
            attempts[0] += 1
            raise urllib.error.HTTPError(url, 400, "Bad", {}, None)

        try:
            self.http.get(
                "https://x.org",
                allowlist={"x.org"},
                retries=5,
                urlopen=fail,
                sleep_fn=lambda s: None,
            )
        except self.http.HttpError as e:
            assert e.attempts == 1
            return
        raise AssertionError("expected HttpError")

    # ---- exhausting retries ----

    def test_exhausts_retries_then_raises(self):
        import urllib.error

        def always_fail(url, timeout):
            raise urllib.error.URLError("connection refused")

        try:
            self.http.get(
                "https://x.org",
                allowlist={"x.org"},
                retries=2,
                urlopen=always_fail,
                sleep_fn=lambda s: None,
            )
        except self.http.HttpError as e:
            # Total attempts = retries + 1 = 3
            assert e.attempts == 3
            assert "URLError" in str(e)
            assert e.url == "https://x.org"
            return
        raise AssertionError("expected HttpError")

    def test_exhausts_retries_on_persistent_5xx(self):
        import urllib.error

        def always_503(url, timeout):
            raise urllib.error.HTTPError(url, 503, "down", {}, None)

        try:
            self.http.get(
                "https://x.org",
                allowlist={"x.org"},
                retries=1,
                urlopen=always_503,
                sleep_fn=lambda s: None,
            )
        except self.http.HttpError as e:
            assert e.attempts == 2  # 1 initial + 1 retry
            return
        raise AssertionError("expected HttpError")

    def test_backoff_is_exponential(self):
        """Three attempts (retries=2) → two sleeps with exponentially
        growing durations. The exact ratio is `backoff` (default 1.5)."""
        import urllib.error

        sleeps = []

        def fail(url, timeout):
            raise urllib.error.URLError("flaky")

        try:
            self.http.get(
                "https://x.org",
                allowlist={"x.org"},
                retries=2,
                backoff=2.0,
                urlopen=fail,
                sleep_fn=lambda s: sleeps.append(s),
            )
        except self.http.HttpError:
            pass
        # Two sleeps between three attempts; second is twice the first
        # (because backoff base is 2.0 → 2^1 = 2, 2^2 = 4).
        assert len(sleeps) == 2
        assert sleeps[1] == sleeps[0] * 2

    # ---- HttpError carries the underlying cause ----

    def test_http_error_carries_underlying_exception(self):
        import urllib.error

        def fail(url, timeout):
            raise urllib.error.URLError("boom")

        try:
            self.http.get(
                "https://x.org",
                allowlist={"x.org"},
                retries=0,
                urlopen=fail,
                sleep_fn=lambda s: None,
            )
        except self.http.HttpError as e:
            assert isinstance(e.last_exc, urllib.error.URLError)
            assert e.__cause__ is e.last_exc  # `raise … from …`
            return
        raise AssertionError("expected HttpError")


# ---------- Phase ξ.2 : path-traversal hardening --------------------


class TestSafePath:
    """Shared helper for sandboxing user-supplied paths against a known-
    safe root. Replaces inline string-checks + Path.relative_to() that
    were duplicated across routes."""

    @classmethod
    def setup_class(cls):
        from scripts.core import safe_path

        cls.mod = safe_path

    def setup_method(self, method):
        # Each test gets its own scratch root + a real file under it
        # so resolve_under can canonicalize successfully.
        import tempfile
        import os

        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "ok.txt").write_text("hi", encoding="utf-8")
        os.makedirs(self.root / "sub", exist_ok=True)
        (self.root / "sub" / "deep.txt").write_text("d", encoding="utf-8")

    def teardown_method(self, method):
        self._tmp.cleanup()

    # ---- happy path ----

    def test_simple_relative_resolves(self):
        out = self.mod.resolve_under(self.root, "ok.txt")
        assert out.name == "ok.txt"
        assert out.is_file()

    def test_subdir_relative_resolves(self):
        out = self.mod.resolve_under(self.root, "sub/deep.txt")
        assert out.name == "deep.txt"
        assert out.is_file()

    def test_backslash_separator_accepted(self):
        # Windows-style separator works the same as POSIX.
        out = self.mod.resolve_under(self.root, "sub\\deep.txt")
        assert out.is_file()

    # ---- string-level rejection ----

    def test_rejects_empty(self):
        try:
            self.mod.resolve_under(self.root, "")
        except self.mod.SafePathError as e:
            assert "empty" in str(e).lower()
            return
        raise AssertionError("expected SafePathError")

    def test_rejects_non_string(self):
        try:
            self.mod.resolve_under(self.root, 42)
        except self.mod.SafePathError:
            return
        raise AssertionError("expected SafePathError")

    def test_rejects_oversized(self):
        try:
            self.mod.resolve_under(self.root, "a" * 2000)
        except self.mod.SafePathError as e:
            assert "long" in str(e).lower()
            return
        raise AssertionError("expected SafePathError")

    def test_rejects_dotdot(self):
        try:
            self.mod.resolve_under(self.root, "../escaped")
        except self.mod.SafePathError as e:
            assert ".." in str(e)
            return
        raise AssertionError("expected SafePathError")

    def test_rejects_dotdot_deeper(self):
        try:
            self.mod.resolve_under(self.root, "sub/../../escaped")
        except self.mod.SafePathError:
            return
        raise AssertionError("expected SafePathError")

    def test_rejects_absolute_posix(self):
        try:
            self.mod.resolve_under(self.root, "/etc/passwd")
        except self.mod.SafePathError as e:
            assert "absolute" in str(e).lower()
            return
        raise AssertionError("expected SafePathError")

    def test_rejects_absolute_windows_drive(self):
        try:
            self.mod.resolve_under(self.root, "C:/Windows/System32/cmd.exe")
        except self.mod.SafePathError as e:
            assert "absolute" in str(e).lower()
            return
        raise AssertionError("expected SafePathError")

    def test_rejects_unc(self):
        try:
            self.mod.resolve_under(self.root, "//host/share/foo")
        except self.mod.SafePathError:
            return
        raise AssertionError("expected SafePathError")

    def test_rejects_hidden_segment(self):
        try:
            self.mod.resolve_under(self.root, ".git/HEAD")
        except self.mod.SafePathError as e:
            assert "hidden" in str(e).lower()
            return
        raise AssertionError("expected SafePathError")

    def test_rejects_hidden_segment_in_middle(self):
        try:
            self.mod.resolve_under(self.root, "sub/.hidden/file")
        except self.mod.SafePathError:
            return
        raise AssertionError("expected SafePathError")

    def test_rejects_nul_byte(self):
        try:
            self.mod.resolve_under(self.root, "ok.txt\x00.evil")
        except self.mod.SafePathError as e:
            assert "control" in str(e).lower()
            return
        raise AssertionError("expected SafePathError")

    def test_rejects_other_control_char(self):
        try:
            self.mod.resolve_under(self.root, "ok\x01.txt")
        except self.mod.SafePathError:
            return
        raise AssertionError("expected SafePathError")

    # ---- non-existent file is fine; existence is the caller's check ----

    def test_resolves_nonexistent_path_safely(self):
        # The point of resolve_under is path safety, not existence.
        # Caller checks .is_file() / .exists().
        out = self.mod.resolve_under(self.root, "nope.txt")
        assert not out.exists()
        assert out.parent == self.root.resolve()

    # ---- safe_root validation ----

    def test_rejects_missing_safe_root(self, tmp_path):
        nope = tmp_path / "does-not-exist"
        try:
            self.mod.resolve_under(nope, "ok.txt")
        except self.mod.SafePathError:
            return
        raise AssertionError("expected SafePathError")


# ---------- Phase ω.9 : atomic-write audit linter check --------------


class TestAtomicWritesLint:
    """ω.9 — `check_atomic_writes` is a Tier-3 drift-prevention lint
    that catches any raw `open(..., 'w')` introduced outside
    `scripts/core/notes_io.py`. These tests verify the check passes
    on the current codebase AND that it actually flags violations
    when one exists (testing the negative path is essential — a
    silently-no-op linter would be worse than no linter)."""

    @classmethod
    def setup_class(cls):
        from scripts import lint_rules

        cls.lint = lint_rules

    def test_currently_passes(self):
        """Today's codebase has zero raw write-mode opens outside
        notes_io.py. If this regresses, the check should fire."""
        result = self.lint.check_atomic_writes()
        assert result["status"] == "pass", result.get("violations")

    def test_check_in_run_all_registry(self):
        """The check must appear in ALL_CHECKS so run_all() picks it
        up. Otherwise the linter would silently drop the new check."""
        assert "atomic_writes" in self.lint.ALL_CHECKS

    def test_detects_violation_in_synthetic_repo(self, tmp_path, monkeypatch):
        """Plant a raw `open('w')` in a synthetic 'scripts/' tree and
        verify the check fails with a violation. Uses monkeypatch to
        redirect REPO at the lint module so we don't actually scan
        the live codebase."""
        # Build a fake scripts/ dir
        synth_scripts = tmp_path / "scripts"
        synth_scripts.mkdir()
        (synth_scripts / "core").mkdir()
        # notes_io.py is the documented exception — must NOT be flagged
        (synth_scripts / "core" / "notes_io.py").write_text(
            "with open('x.json', 'w') as f: f.write('ok')\n",
            encoding="utf-8",
        )
        # Top-level scripts/foo.py — DOES get flagged
        (synth_scripts / "foo.py").write_text(
            "def bad():\n    with open('x.json', 'w') as f:\n        f.write('!')\n",
            encoding="utf-8",
        )
        # Top-level scripts/bar.py — has the waiver comment
        (synth_scripts / "bar.py").write_text(
            "def waived():\n"
            "    # atomic-waived: regenerable build artifact\n"
            "    with open('x.json', 'w') as f: f.write('!')\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(self.lint, "REPO", tmp_path)
        result = self.lint.check_atomic_writes()
        assert result["status"] == "fail"
        # foo.py is the only violation; notes_io.py exempted; bar.py waived.
        files = {v["file"] for v in result["violations"]}
        assert "scripts/foo.py" in files
        assert "scripts/core/notes_io.py" not in files
        assert "scripts/bar.py" not in files


# ---------- Phase ω.8 : top-level request error boundary --------------


class TestRequestErrorBoundary:
    """ω.8 — every Handler.do_* method is wrapped with @_safe_request,
    which catches any uncaught Exception and returns a 500 JSON
    response. The client never sees a Python stack trace.

    These tests exercise the wrapper directly via a fake Handler
    rather than spinning up a real HTTP server — keeps them fast and
    deterministic. The server-level integration is the responsibility
    of a follow-up integration suite (ω.10 retry/timeout test scope)."""

    @classmethod
    def setup_class(cls):
        from scripts import web

        cls.web = web

    def test_all_do_methods_are_wrapped(self):
        """Every public do_* method on Handler must carry the
        @_safe_request decorator. If a future refactor forgets this,
        the lint should fail."""
        for name in ("do_GET", "do_POST", "do_PUT", "do_DELETE"):
            attr = getattr(self.web.Handler, name)
            assert hasattr(attr, "__wrapped__"), (
                f"{name} is not @_safe_request wrapped — adding routes "
                "without the wrapper means uncaught exceptions reach "
                "the client as raw stack traces."
            )

    def test_wrapper_passes_through_happy_path(self):
        """The decorator is a transparent passthrough when the wrapped
        method completes normally."""
        calls = []

        def fake(self):
            calls.append("called")
            return "ok"

        wrapped = self.web._safe_request(fake)

        # Build a minimal fake handler that the decorator will invoke
        # `self.fake()`-style.
        class FakeHandler:
            pass

        result = wrapped(FakeHandler())
        assert calls == ["called"]
        assert result == "ok"

    def test_wrapper_catches_and_returns_500_json(self, monkeypatch, capsys):
        """When the wrapped method raises, the wrapper invokes
        _send_unhandled_error and the client receives a structured
        500 — not a stack trace."""
        sent = []

        def fake_send_unhandled_error(self, exc, method_name="?"):
            sent.append((type(exc).__name__, str(exc), method_name))
            return ("500-json", method_name)

        def boom(self):
            raise RuntimeError("kaboom")

        wrapped = self.web._safe_request(boom)

        class FakeHandler:
            _send_unhandled_error = fake_send_unhandled_error

        result = wrapped(FakeHandler())
        assert sent == [("RuntimeError", "kaboom", "boom")]
        assert result == ("500-json", "boom")

    def test_send_unhandled_error_emits_500_json(self, capsys):
        """The _send_unhandled_error helper itself: writes the trace
        to stderr and produces a JSON 500 response. We verify the
        JSON shape via a fake _send_json captor."""

        class FakeHandler:
            def __init__(self):
                self.sent = None

            def _send_json(self, payload, status=200):
                self.sent = (payload, status)

        # Bind the real method to the fake.
        h = FakeHandler()
        method = self.web.Handler._send_unhandled_error.__get__(h, FakeHandler)
        try:
            raise ValueError("simulated unhandled")
        except ValueError as e:
            method(e, method_name="do_GET")
        payload, status = h.sent
        assert status == 500
        assert payload["error"] == "internal_error"
        # User-facing message references the method name and exc type
        assert "ValueError" in payload["message"]
        assert "do_GET" in payload["message"]
        # CRITICAL: no traceback content in the payload — the
        # operator log gets the full trace, the client gets a clean
        # generic message.
        assert "Traceback" not in payload["message"]
        assert "simulated unhandled" not in payload["message"]
        # Stderr DOES get the trace (operator-side debugging).
        captured = capsys.readouterr()
        assert "ValueError" in captured.err
        assert "simulated unhandled" in captured.err


# ---------- Phase ξ.4 : XSS prevention (HTML sanitizer) ---------------


class TestHtmlSanitize:
    """Whitelist-based HTML sanitizer for note bodies. Defends against
    the XSS classes in the OWASP cheat sheet plus a few project-
    specific ones. Tests cover happy-path preservation of legitimate
    rich apparatus AND aggressive rejection of every disallowed
    construct.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import html_sanitize

        cls.mod = html_sanitize

    def sanitize(self, text):
        return self.mod.sanitize_html(text)

    # ---- happy-path: legitimate apparatus passes through ----

    def test_plain_text_passes_through(self):
        assert self.sanitize("Hello, world.") == "Hello, world."

    def test_basic_inline_tags_pass(self):
        out = self.sanitize("<p><em>In</em> the <strong>beginning</strong></p>")
        assert out == "<p><em>In</em> the <strong>beginning</strong></p>"

    def test_safe_anchor_passes(self):
        out = self.sanitize('<a href="https://example.org" title="ref">x</a>')
        assert out == '<a href="https://example.org" title="ref">x</a>'

    def test_relative_anchor_passes(self):
        out = self.sanitize('<a href="#footnote-1">[1]</a>')
        assert out == '<a href="#footnote-1">[1]</a>'

    def test_mailto_passes(self):
        out = self.sanitize('<a href="mailto:x@example.org">x</a>')
        assert "mailto:x@example.org" in out

    def test_class_lang_dir_pass(self):
        out = self.sanitize('<span class="hebrew" lang="he" dir="rtl">בְּרֵאשִׁית</span>')
        assert 'class="hebrew"' in out
        assert 'lang="he"' in out
        assert 'dir="rtl"' in out

    # ---- XSS classes — every payload's executable bits must be stripped ----

    def test_drops_script_tag_and_contents(self):
        out = self.sanitize("<p>Hi <script>alert(1)</script> there.</p>")
        assert "<script" not in out
        assert "alert(1)" not in out
        # The text outside the script survives.
        assert "Hi" in out and "there" in out

    def test_strips_onclick_handler(self):
        out = self.sanitize('<a href="https://x.org" onclick="alert(1)">x</a>')
        assert "onclick" not in out.lower()
        assert "alert" not in out

    def test_strips_onerror_handler(self):
        out = self.sanitize('<a onerror="alert(1)">x</a>')
        assert "onerror" not in out.lower()

    def test_javascript_url_in_href_rejected(self):
        out = self.sanitize('<a href="javascript:alert(1)">x</a>')
        assert "javascript:" not in out.lower()
        # The text is preserved; the unsafe href is dropped.
        assert ">x</a>" in out

    def test_data_url_in_href_rejected(self):
        out = self.sanitize('<a href="data:text/html,<script>alert(1)</script>">x</a>')
        assert "data:" not in out.lower()

    def test_vbscript_url_in_href_rejected(self):
        out = self.sanitize('<a href="vbscript:msgbox(1)">x</a>')
        assert "vbscript:" not in out.lower()

    def test_iframe_dropped_entirely(self):
        out = self.sanitize('hello <iframe src="https://evil.example/"></iframe> world')
        assert "iframe" not in out.lower()
        assert "evil.example" not in out
        assert "hello" in out and "world" in out

    def test_svg_with_onload_dropped(self):
        out = self.sanitize('text <svg onload="alert(1)"></svg> after')
        assert "<svg" not in out.lower()
        assert "onload" not in out.lower()
        assert "alert" not in out

    def test_style_tag_dropped(self):
        out = self.sanitize("<style>body{display:none}</style><p>visible</p>")
        assert "<style" not in out.lower()
        # Critically: the CSS body is dropped, not preserved as text.
        assert "display:none" not in out
        assert "<p>visible</p>" in out

    def test_style_attribute_dropped(self):
        out = self.sanitize('<p style="color:red">red</p>')
        assert "style=" not in out.lower()
        assert out == "<p>red</p>"

    def test_form_input_button_dropped(self):
        out = self.sanitize("<form><input name=x><button>go</button></form>after")
        assert "<form" not in out.lower()
        assert "<input" not in out.lower()
        assert "<button" not in out.lower()
        assert "after" in out

    def test_meta_refresh_dropped(self):
        out = self.sanitize('<meta http-equiv="refresh" content="0;url=javascript:alert(1)"><p>x</p>')
        assert "<meta" not in out.lower()
        assert "javascript" not in out.lower()
        assert out == "<p>x</p>"

    def test_link_rel_stylesheet_dropped(self):
        out = self.sanitize('<link rel="stylesheet" href="javascript:alert(1)"><p>x</p>')
        assert "<link" not in out.lower()
        assert "javascript" not in out.lower()

    def test_object_embed_dropped(self):
        out = self.sanitize('<object data="x"></object><embed src="x">text')
        assert "<object" not in out.lower()
        assert "<embed" not in out.lower()
        assert "text" in out

    def test_html_comment_with_conditional_script_dropped(self):
        # `<!--[if IE]><script>...<![endif]-->` — IE-style; comments
        # are always stripped regardless of payload.
        out = self.sanitize("before<!--[if IE]><script>alert(1)</script><![endif]-->after")
        assert "<!--" not in out
        assert "script" not in out.lower()
        assert "before" in out and "after" in out

    def test_doctype_stripped(self):
        out = self.sanitize("<!DOCTYPE html><p>x</p>")
        assert "DOCTYPE" not in out
        assert out == "<p>x</p>"

    def test_processing_instruction_stripped(self):
        # Even though html.parser handles PIs idiosyncratically on
        # some inputs, the sanitizer must drop them.
        out = self.sanitize('<?xml version="1.0"?><p>x</p>')
        assert "?xml" not in out

    def test_unknown_tag_is_transparent(self):
        # An unknown tag (not in ALLOWED_TAGS, not in
        # TAGS_DROP_CONTENT) drops the tag but keeps the inner text.
        out = self.sanitize("<bogus>kept</bogus>")
        assert out == "kept"

    def test_target_blank_gets_rel_noopener(self):
        out = self.sanitize('<a href="https://x.org" target="_blank">x</a>')
        assert 'target="_blank"' in out
        assert 'rel="noopener noreferrer"' in out

    def test_target_other_value_dropped(self):
        out = self.sanitize('<a href="https://x.org" target="parent">x</a>')
        assert "target=" not in out
        # rel is only auto-added when target is preserved.
        assert "rel=" not in out

    # ---- attribute splitting / scheme-evasion attempts ----

    def test_javascript_url_with_leading_whitespace_rejected(self):
        out = self.sanitize('<a href="\tjavascript:alert(1)">x</a>')
        assert "javascript" not in out.lower()

    def test_javascript_url_with_uppercase_rejected(self):
        out = self.sanitize('<a href="JaVaScRiPt:alert(1)">x</a>')
        assert "javascript" not in out.lower()
        assert "alert" not in out

    # ---- escaping in text and attributes ----

    def test_special_chars_escaped_in_text(self):
        out = self.sanitize("<p>1 < 2 & 3 > 0</p>")
        assert out == "<p>1 &lt; 2 &amp; 3 &gt; 0</p>"

    def test_quotes_escaped_in_attr(self):
        # Use a properly-quoted source: a title containing a quote
        # entity. The sanitizer must round-trip it (decoded by
        # html.parser, re-escaped on emit).
        out = self.sanitize('<a title="he said &quot;hi&quot;" href="https://x.org">x</a>')
        assert "&quot;" in out
        # And no broken-out attribute.
        assert "<script" not in out.lower()

    # ---- structural ----

    def test_empty_input(self):
        assert self.sanitize("") == ""
        assert self.sanitize(None) == ""

    def test_idempotent(self):
        nasty = (
            "<p>Hi <script>alert(1)</script>"
            '<a href="javascript:alert(2)" onclick="alert(3)">x</a>'
            "<style>body{display:none}</style></p>"
        )
        once = self.sanitize(nasty)
        twice = self.sanitize(once)
        assert once == twice

    def test_void_tags_self_close(self):
        out = self.sanitize("line1<br>line2")
        assert "<br />" in out

    def test_nested_allowed_tags_preserved(self):
        src = "<blockquote><p><em>quote</em> per <cite>source</cite></p></blockquote>"
        out = self.sanitize(src)
        # All four tags survive in their original nesting.
        assert "<blockquote>" in out
        assert "<p>" in out
        assert "<em>" in out
        assert "<cite>" in out

    def test_drops_nested_disallowed_inside_disallowed(self):
        # `<script>` inside `<style>` — both dropped; no leakage.
        out = self.sanitize("<style><script>x</script></style>after")
        assert "x" not in out.replace("after", "")
        assert "after" in out

    def test_id_attr_coerced_to_safe_shape(self):
        out = self.sanitize('<p id="evil-id&quot;=alert(1)">x</p>')
        # The id is rendered as a plain attribute value with no
        # executable context — the security property is "no quote /
        # equals / paren broke out into a new attribute or attribute
        # value", not "the substring is squeaky-clean."
        assert "<p id=" in out
        # The dangerous bits — `=`, `(`, `)` — are stripped.
        assert "=alert" not in out
        assert "(1)" not in out
        # No quote-broken-out attribute.
        assert "<script" not in out.lower()

    def test_image_tag_excluded(self):
        # Inline images are intentionally not whitelisted; the tag
        # drops but the alt-text-style content (none here) doesn't.
        out = self.sanitize('text <img src="x" onerror="alert(1)"> more')
        assert "<img" not in out.lower()
        assert "onerror" not in out.lower()
        assert "text" in out and "more" in out

    # ---- integration: build_aside actually sanitizes ----

    def test_build_aside_strips_malicious_body(self):
        """The §9 build-pipeline integration point: inject.build_aside
        sanitizes body_html before emitting the <aside>. This is the
        actual XSS defense that ships in EPUBs."""
        from scripts.inject import build_aside

        nasty = (
            "<strong>Title.</strong> "
            "<script>alert(1)</script>"
            '<a href="javascript:alert(2)" onclick="alert(3)">click</a>'
        )
        out = build_aside("comm", "gen-1-1-1", "Note 1", nasty)
        # Title preserved
        assert "<strong>Title.</strong>" in out
        # script gone
        assert "<script" not in out
        assert "alert(1)" not in out
        # javascript: href stripped
        assert "javascript:" not in out.lower()
        # onclick stripped
        assert "onclick" not in out.lower()
        # The link text "click" survives
        assert ">click</a>" in out
        # The aside structure intact
        assert 'class="note note-comm"' in out
        assert 'id="note-gen-1-1-1"' in out
