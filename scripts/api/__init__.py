"""ω.35-B — per-topic API modules extracted from scripts/web.py.

The file split started in ω.35-B.1 with `snapshots` as a proof-of-
concept. Each module here holds the api_X handler functions for one
domain; web.py re-imports them to preserve the existing flat
namespace (so route-table lambdas and tests that reference
`scripts.web.api_X` keep working).

Subsequent ω.35-B.x slices add more topics:
- B.1: snapshots
- B.2 (planned): scenarios
- B.3 (planned): sources / covers
- B.4 (planned): editions / customize
- B.5 (planned): exports / build
- B.6 (planned): preflight / audit / help

The route tables themselves stay in web.py for now; moving them
out is a separate concern (web.py's Handler class is the dispatch
point, so the tables either stay there or migrate together with
the file split's final phase).
"""
