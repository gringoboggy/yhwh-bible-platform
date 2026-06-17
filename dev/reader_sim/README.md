# Reader Simulation Lab

**Status:** Phase 1 scaffold (WIN turn 124 prep). Full builds start after audit gate closes.

Plan: [`docs/superpowers/plans/2026-06-18-reader-simulation-lab.md`](../superpowers/plans/2026-06-18-reader-simulation-lab.md)

## Quick start

```bash
# List profiles
py -3 scripts/reader_sim.py --list

# Gate existing artifacts (no rebuild — safe during audit)
py -3 scripts/reader_sim.py --gate play --artifact dev/.audit-build/Ethiopian_Bible_ethiopian-tewahedo_r8audit_2026-06-17T114553Z.epub

# Sweep cached audit dir
py -3 scripts/reader_sim.py --gate all --artifact-dir dev/.audit-build

# Build (post-audit / heavy)
py -3 scripts/reader_sim.py --build kobo --edition ethiopian-tewahedo --version 0.1.0
```

Output dir (gitignored): `build/reader-sim/<reader>/`

## Per-reader packs

| Reader | Dir | Lane | Local sim | Device layer |
|---|---|---|---|---|
| Apple | `apple/` | Mac | Books.app + `tablet` build | iPhone sheet QA |
| Kobo | `kobo/` | WIN | kepubify + `verify_kr2` + calibration | Footnote-preview taps |
| Kindle | `kindle/` | Mac | Previewer 3 + `kindle_post` + M4b | Send-to-Kindle phone |
| Play | `play/` | WIN | `everywhere` + structure audit | Play Books app upload |

## Automated vs manual

**Automated gates** (orchestrator): epubcheck · verify_kr2 · audit_epub_structure · kindle_post verifiers · audit_popup_formula (kobo).

**Manual checklists** (each `qa-checklist.md`): tap protocols Books.app / Kobo / STK / Play phone.