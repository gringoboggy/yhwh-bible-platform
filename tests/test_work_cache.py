"""Tests for scripts/core/work_cache.py — content-hash result cache.

Keyed by sha256(inputs) so re-running any at-scale / vision pass skips
unchanged verses/images and only pays for changed inputs. Stdlib only
(hashlib + sqlite3); in-memory by default, persistable to disk.
"""


def test_key_for_is_stable_and_order_sensitive():
    from scripts.core.work_cache import key_for

    a = key_for("model", "system", "input")
    b = key_for("model", "system", "input")
    assert a == b
    assert len(a) == 64  # sha256 hex
    # order matters, and ("a","b") must differ from ("ab",)
    assert key_for("a", "b") != key_for("b", "a")
    assert key_for("a", "b") != key_for("ab")


def test_get_put_roundtrip():
    from scripts.core.work_cache import WorkCache

    c = WorkCache(":memory:")
    assert c.get("k") is None
    c.put("k", "value")
    assert c.get("k") == "value"
    # overwrite
    c.put("k", "value2")
    assert c.get("k") == "value2"


def test_get_or_compute_caches():
    from scripts.core.work_cache import WorkCache

    c = WorkCache(":memory:")
    calls = []

    def compute():
        calls.append(1)
        return "computed"

    v1, hit1 = c.get_or_compute("k", compute)
    v2, hit2 = c.get_or_compute("k", compute)
    assert v1 == "computed" and v2 == "computed"
    assert hit1 is False  # first call computed
    assert hit2 is True  # second call served from cache
    assert len(calls) == 1  # compute ran exactly once


def test_persists_to_disk(tmp_path):
    from scripts.core.work_cache import WorkCache

    db = str(tmp_path / "cache.sqlite")
    c1 = WorkCache(db)
    c1.put("k", "persisted")
    c1.close()
    c2 = WorkCache(db)
    assert c2.get("k") == "persisted"
    c2.close()
