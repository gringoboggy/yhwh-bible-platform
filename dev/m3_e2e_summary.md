# M3 end-to-end verification — 2026-06-19

**Tree:** `96e3e86d` (turn 136 canon-SKU scrub)  
**Matrix:** 4 canon-differentiated editions × 5 colours = **20 kepubs**

## Build + per-asset gates (authoritative)

Each asset built via `build_format_matrix.py --phase M3` with gates ON:
zip integrity → epubcheck **0/0/0/0** → `verify_kr2_build.py` **ALL K-R2 GATES GREEN**.

| Edition | Status | Log |
|---------|--------|-----|
| ethiopian-tewahedo | PASS (5/5) | `dev/m3_fanout_win.log` |
| catholic-study | PASS (5/5) | `dev/m3_fanout_win.log` |
| evangelical-reformed | PASS (5/5) | `dev/m3_fanout_win.log` |
| eastern-orthodox | PASS (5/5) | `dev/m3_eastern_resume.log` (resumed after 10h fan-out cap) |

## Inventory

All 20 filenames from `dev/M3_Kobo_Assets_v0.1.0.txt` present under `build/matrix-m3/`.

Checksum sidecars: `sums-{edition}.txt` per edition in `build/matrix-m3/`.

## Notes

- Initial `m3_fanout_win.ps1` hit harness **max_runtime (10h)** mid–eastern-orthodox red epubcheck; 15/20 were already gated-green.
- Eastern resume completed remaining 5 colours with full gates.
- Post-flight `verify_m3_e2e.ps1` (re-epubcheck all 20) is optional belt-and-suspenders; build-time gates are the acceptance criterion.