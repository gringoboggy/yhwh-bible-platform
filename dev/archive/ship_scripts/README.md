# Archived one-shot ship scripts

These `_ship_*.py` / `_fix_*.py` files are **one-shot ledgers** of the
entries appended to `content/sources/*.json` (or similar) at a specific
ship moment. They are **NOT re-runnable** in normal operation — running
them again would duplicate entries.

Per project rule **§7.4** (codified at the ω.41 hygiene bundle,
2026-05-13, per AUDIT_2026-05-13-EOD EOD-W4):

> Retain `_ship_*.py` in `scripts/` for one full release cycle after
> the arc closes, then move to `dev/archive/ship_scripts/` preserving
> the original filename.

**Moved here at the 2026-05-15 DEEP-2 audit**, actioning the prior
`AUDIT_2026-05-15-DEEP.md` finding **D-C1** (19 `_ship_*` + 2
`_fix_gamma49*` over the retention threshold; v1.0 shipped 2026-05-10,
the one-cycle window had elapsed). Retired-not-deleted: preserved here
for provenance / emergency reconstruction; git history is authoritative.

Arcs represented (filenames self-document the arc):

- **γ.4.6** — `_ship_gamma46{,b,c,d}.py`
- **γ.4.7** — `_ship_gamma47{,b,c,d}.py`
- **γ.4.8** — `_ship_gamma48{,b,c,d,e,f}.py`
- **γ.4.9** — `_ship_gamma49{,b,c,d}.py` + `_fix_gamma49_npnf.py` +
  `_fix_gamma49b_dedup.py`
- **Π.0** — `_ship_pi0.py`

**Not archived (deliberately retained in `scripts/`):**
`scripts/_dedup_ethiopian_notes.py` — an *obsolete safety script*
(LOAD-BEARING-NO-LONGER banner) kept as an emergency-restore tool per
§7.4; tracked separately in the SESSION_STATE inventory.

Permanent at-scale driver scripts (`scripts/run_*_at_scale.py`) are
re-runnable detectors and remain in `scripts/` indefinitely — they
were never candidates for this archive.
