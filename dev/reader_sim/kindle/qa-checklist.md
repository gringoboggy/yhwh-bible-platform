# Kindle — STK + Previewer QA checklist

**Artifacts:**
- Standard: `py -3 scripts/build_kindle.py <edition> --version 0.1.0`
- M4b: `py -3 scripts/build_kindle.py <edition> --version 0.1.0 --m4b`

**Automated gate:** `py -3 scripts/reader_sim.py --gate kindle --artifact <path> [--m4b]`

**Mac Previewer 3:** run conversion; scrape E-codes from log (see `dev/kindle_bisect.py` header).

**Phone STK matrix (6 variants):** `docs/superpowers/notes/2026-06-18-m4b-kindle-fork-design.md` §7

| # | Tap | Pass |
|---|---|---|
| 1 | Gen 1:1 `vn-link` | Readable translation |
| 2 | Gen 1:3 multi-study | No inline ◈ clutter; chapter-tail study reachable (M4b) |
| 3 | Study-heavy chapter | No 3:24-style teleport |