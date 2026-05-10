"""ω.22 — migration package marker.

Each migration is a ``<NNNN>_<name>.py`` module exposing
``ID``, ``DESCRIPTION``, ``up()``, ``down()``. Discovered + invoked
by ``scripts/migrate.py``. See `dev/CHANGELOG.md` ω.22 entry for
the framework spec.
"""
