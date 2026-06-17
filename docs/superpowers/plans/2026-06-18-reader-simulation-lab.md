# Reader Simulation Lab — post-audit dedicated phase

**Status:** PLANNED — start **after** Round 9 audit gate closes (`ci.py` green + `rx-surfaces` dim signed off).

**User directive (2026-06-18):** Do not build reader artifacts or sim harnesses *during* the audit/fix arc; dedicate the *next* phase to replicating reader behavior as closely as automation allows.

**User directive (2026-06-17):** **No EPUB builds until each reader's sim harness exists.** **Agents run reader QA** — the user should not have to physically tap through four readers × many probes every round.

**Goal:** One command (`py -3 scripts/reader_sim.py --sim all`) lets agents verify all four reader profiles using **device-calibrated sim layers** — structural gates plus behavioral proxies wired from proven device rounds. User involvement = occasional one-time calibration sign-off when a sim layer cannot be closed in software.

---

## Gate — do not start until

- [ ] WIN: `scripts/ci.py` full gate **GREEN**
- [ ] WIN: `rx-surfaces` dim closed (fresh eth + catholic-study builds + S1/S2/S3)
- [ ] `docs/superpowers/notes/2026-06-18-round9-audit-findings.md` — audit arc marked complete

---

## Agent-primary QA model

| What | Who runs it |
|---|---|
| Structural gates (epubcheck, verify_kr2, kindle_post, …) | Agents — anytime on cached artifacts (`--gate`) |
| Per-reader sim layers (calibration, Thorium taps, STK channel, …) | Agents — via `--sim` once sim pack ships |
| Full cross-reader sim pass | Agents — `--sim all` once all four sim packs exist |
| Physical device taps | **User only** when a sim layer cannot be automated and needs one-time calibration |

**Ship gate for agents:** `py -3 scripts/reader_sim.py --sim all` GREEN on `build/reader-sim/` artifacts.

---

## Per-reader agent sim stack

| Reader | Full engine replication? | Agent sim (target) | User only if |
|---|---|---|---|
| **Kobo** | ❌ Nickel closed | kepubify + `verify_kr2` + `audit_popup_formula` + **`kobo_tap_calibration`** (pop/decline bracket from device rounds) | New bracket anomaly (e.g. gen 35:18) needs one re-tap to recalibrate |
| **Play** | ❌ custom Android engine | epubcheck + structure audit + **Thorium or Android-emulator** popup/font tap script | Emulator spike fails and proxy untrusted |
| **Kindle** | ⚠ partial | `kindle_post` + M4b gates + **`stk_channel.sh`** (Send-to-Kindle → Kindle-for-Mac ingest poll) | STK channel automation blocked — not Previewer |
| **Apple** | ❌ no public API | epubcheck + verify_kr2 + **Thorium popup/ToC tap script** (tablet proxy, device-calibrated) | iPhone sheet height / font edge case |

**Principle:** Each sim layer encodes a **device-proven oracle** as runnable code — not folklore, not "open it and eyeball."

### Kindle — Previewer is NOT the sim (project-proven)

Kindle Previewer 3 names E-codes fast (`dev/kindle_bisect.py`) but **Previewer PASS ≠ Send-to-Kindle PASS**. KDP/`kpp.amazon` preview is a third channel. Agent sim must exercise **consumer STK → Kindle for Mac** (automated send + library poll + ingest OK).

---

## Deliverables (per reader)

```
dev/reader_sim/
  README.md
  apple/
    build.sh · gate.sh · sim.sh          # sim.sh = Thorium tap protocol
  kobo/
    build.sh · gate.sh · sim.sh          # sim.sh = calibration + popup formula
  kindle/
    build.sh · gate.sh · stk_channel.sh · sim.sh
  play/
    build.sh · gate.sh · sim.sh
```

Orchestrator: **`scripts/reader_sim.py`** — `--build | --gate | --sim` per reader or `all`.

---

## Lane split

| Reader sim | Primary lane | Agent sim work |
|---|---|---|
| **Kobo** | WIN | Calibration export + cap-unit gates (**layer wired**) |
| **Play** | WIN / Mac emulator | Thorium or AVD sideload tap script |
| **Kindle** | Mac | STK-channel automation |
| **Apple** | Mac | Thorium tablet proxy taps |

Build order flexible. **`--sim all`** unlocks when all four `SIM_PACK_READY` flags flip.

---

## Phase plan

### Phase 1 — Scaffold — **DONE**

1. [x] `dev/reader_sim/` tree + README + per-reader `qa-checklist.md`
2. [x] `scripts/reader_sim.py` (`--list`, `--build`, `--gate`, `--sim`)
3. [x] Kobo sim layer partially wired (`kobo_tap_calibration` in `--sim kobo`)

### Phase 2 — Kobo (WIN) — **sim layer mostly done**

1. `build.sh` + `gate.sh` + `sim.sh` wrapping existing tools
2. Flip `SIM_PACK_READY["kobo"]` when scripts ship
3. Agent runs `--sim kobo` — no device taps for routine QA

### Phase 3 — Play (WIN + Mac emulator spike)

1. `sim.sh`: Thorium MCP protocol OR Android emulator sideload
2. Encode M5 tap list as automated assertions where possible
3. Flip `SIM_LAYERS_READY["play"]` when green

### Phase 4 — Kindle (Mac) — real-channel sim

1. `stk_channel.sh`: automated Send-to-Kindle + Kindle-for-Mac arrival
2. `sim.sh`: ingest OK + structural re-check on delivered copy if extractable
3. Flip `SIM_LAYERS_READY["kindle"]` — never Previewer-as-gate

### Phase 5 — Apple (Mac) — Thorium proxy

1. `sim.sh`: Thorium opens `tablet` artifact, asserts popup/ToC/script taps from M2 matrix
2. Flip `SIM_LAYERS_READY["apple"]`
3. User = one-time sign-off that Thorium proxy matched Books.app (already largely proven)

### Phase 6 — Agent sim suite + CI

1. `py -3 scripts/reader_sim.py --sim all` = the routine ship gate for agents
2. Optional `ci.py --reader-sim-gates` (structural only, no rebuild)
3. Document in `TOOLCHAIN.md` §Reader Simulation Lab

---

## What we explicitly defer

- Claiming Thorium = Play Books phone (honest proxy only until emulator works)
- Shipping Nickel/KFX source engines
- User walking four readers every round (that's what sims replace)

---

## References

- `dev/EREADERS.md` — per-reader truth record
- `docs/superpowers/notes/2026-06-18-platform-implementation-matrix.md`
- `dev/TOOLCHAIN.md` — kepubify, Thorium, Chrome DevTools MCP
- `dev/kobo_tap_calibration.py`, `dev/audit_popup_formula.py`, `dev/kindle_bisect.py`