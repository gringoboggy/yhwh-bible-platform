# Reader Simulation Lab

**Status:** Phase 1 scaffold. **Agents run reader QA** — not the user tapping four devices.

Plan: [`docs/superpowers/plans/2026-06-18-reader-simulation-lab.md`](../superpowers/plans/2026-06-18-reader-simulation-lab.md)

## Why

Physically checking four readers × many tap probes every round is too much. Each sim pack encodes **device-proven behavior** as code agents can run. User steps in only when a sim layer needs one-time calibration.

## Policy

- **No EPUB builds** until each reader's sim pack ships (`build.sh` + `gate.sh` + `sim.sh`).
- **Agents own QA:** `--gate` (structural) anytime; `--sim` (behavioral proxies) per reader; `--sim all` once all four packs exist.
- **Kindle:** STK channel sim, not Previewer. **Kobo:** calibration bracket already agent-runnable.

## Quick start

```bash
# Profiles + sim-layer status
py -3 scripts/reader_sim.py --list

# Structural gates only (safe during audit)
py -3 scripts/reader_sim.py --gate play --artifact dev/.audit-build/<file>.epub

# Agent sim — gates + behavioral layer (kobo calibration wired; others pending)
py -3 scripts/reader_sim.py --sim kobo --artifact path/to.kepub.epub

# Full suite (after all sim packs ship)
py -3 scripts/reader_sim.py --sim all --artifact-dir build/reader-sim
```

## Per-reader agent sim

| Reader | Structural gates | Agent sim layer | Status |
|---|---|---|---|
| Kobo | epubcheck · verify_kr2 · audit_popup_formula | `kobo_tap_calibration` bracket | **wired** |
| Play | epubcheck · verify_kr2 · structure audit | `thorium_cdp` structural proxy | **wired** |
| Kindle | verify_kindle_safe · verify_kindle_m4b · epubcheck | `stk_channel.sh` (gate-only / poll) | **wired** |
| Apple | epubcheck · verify_kr2 | `thorium_cdp` popup/ToC proxy | **wired** |

**Ship gate for agents:** `--sim all` GREEN.