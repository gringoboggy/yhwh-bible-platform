# Kobo e-ink — device QA checklist

**Artifact:** `.kepub.epub` from `py -3 scripts/reader_sim.py --build kobo`

**Automated pre-gate:** `py -3 scripts/reader_sim.py --gate kobo --artifact <path>`

**Tap list:** `docs/superpowers/notes/2026-06-18-kobo-round9-tap-list.md`

**Calibration:** `py -3 dev/kobo_tap_calibration.py <artifact.kepub.epub>`

Sideload as fixed filename `YHWH-koboQA.kepub.epub` (K-R5-1 font-reset lesson).