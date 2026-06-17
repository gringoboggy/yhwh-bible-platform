# Reader Simulation Lab — post-audit dedicated phase

**Status:** PLANNED — start **after** Round 9 audit gate closes (`ci.py` green + `rx-surfaces` dim signed off).
**User directive (2026-06-18):** Do not build reader artifacts or sim harnesses *during* the audit/fix arc; dedicate the *next* phase to replicating reader behavior as closely as automation allows.

**Goal:** One command per reader profile produces a gated artifact + a repeatable local QA protocol so agents (and humans) can see popup/nav/font behavior without re-researching each platform every round.

---

## Gate — do not start until

- [ ] WIN: `scripts/ci.py` full gate **GREEN**
- [ ] WIN: `rx-surfaces` dim closed (fresh eth + catholic-study builds + S1/S2/S3)
- [ ] `docs/superpowers/notes/2026-06-18-round9-audit-findings.md` — audit arc marked complete
- [ ] User device items (Kobo re-tap, Play phone) may run in parallel but **do not block** sim-lab start

---

## Honest ceiling

| Reader | Full engine replication? | Best local sim | Device still required for |
|---|---|---|---|
| **Apple Books** | ❌ no public headless engine | Mac **Books.app** + `tablet` build + Thorium proxy | iPhone sheet height, font edge cases |
| **Kobo e-ink** | ❌ Nickel WebKit closed | **kepubify** + `verify_kr2_build` gates (device-proven brackets) + `kobo_tap_calibration.py` | Footnote-preview heuristic, glossary navigate |
| **Kindle** | ⚠ partial | Mac **Kindle Previewer 3** CLI + `kindle_post` + `verify_kindle_safe` + M4b gates | Phone KFX tap targets (Previewer ≠ STK) |
| **Play Books** | ❌ custom Android engine | `everywhere` build + epubcheck + Thorium proxy; optional Android emulator | Real popup/font behavior |

**Principle:** Sims encode **device-proven oracles** as gates + local open tools — not folklore.

---

## Deliverables (per reader)

Each reader gets a **`dev/reader_sim/<id>/`** pack:

```
dev/reader_sim/
  README.md                 # one-page "run the lab"
  apple/
    build.sh                # tablet artifact → ~/Desktop/YHWH-reader-sim/apple/
    gate.sh                 # epubcheck + verify_kr2
    qa-checklist.md         # Books.app tap list (Gen 1:1 …)
  kobo/
    build.sh                # eink → kepubify → kepub
    gate.sh                 # verify_kr2 + kepubify + audit_popup_formula
    qa-checklist.md         # links to kobo-round9-tap-list
  kindle/
    build.sh                # everywhere base → kindle_post [→ m4b when ready]
    gate.sh                 # verify_kindle_safe + verify_kindle_m4b + previewer batch
    qa-checklist.md         # STK matrix + Previewer error codes
  play/
    build.sh                # everywhere navy staging artifact
    gate.sh                 # epubcheck + structural audit
    qa-checklist.md         # EREADERS §Play protocol
  run_all_gates.sh          # CI-local: build nothing, gate latest artifacts in sim dir
```

Plus one orchestrator: **`scripts/reader_sim.py`** (or `dev/reader_sim/run.py`) — `build|gate|all --reader apple|kobo|kindle|play`.

---

## Lane split

| Reader sim | Primary lane | Why |
|---|---|---|
| **Apple** | **Mac** | Books.app native; `tablet` builds |
| **Kindle** | **Mac** | Kindle Previewer 3 installed; M4b implement |
| **Kobo** | **WIN** (build) / either (gates) | kepubify on both; WIN has SSD for matrix builds |
| **Play** | **WIN** (build) / Mac (emulator probe) | `everywhere` artifact; Android emulator TBD on Mac |

**Mac turn 123+ (post-gate):** Apple sim pack first (fastest proof), then Kindle sim (Previewer + M4b), then Play emulator spike.

**WIN post-gate:** Kobo sim pack harden + wire `reader_sim.py` into `ci.py --reader-sim` optional leg.

---

## Phase plan

### Phase 1 — Scaffold (both lanes, ~1 session) — **WIN turn 124 prep DONE**

1. [x] Create `dev/reader_sim/` tree + `README.md` + per-reader `qa-checklist.md`
2. [x] `scripts/reader_sim.py` CLI (`--list`, `--build`, `--gate`, `--gate all`)
3. [x] Pin output dir: `build/reader-sim/<reader>/` (under `/build/`, gitignored)
4. [ ] Desktop copy helper for human QA (post-gate)

### Phase 2 — Apple (Mac)

1. `build.sh`: `ethiopian-tewahedo --target-reader tablet`
2. `gate.sh`: epubcheck + `verify_kr2_build`
3. Document Books.app open + M2 tap checklist
4. Optional: Thorium side-by-side note in qa-checklist

### Phase 3 — Kobo (WIN primary)

1. Reuse `build_format_matrix --formats kobo` single-edition driver
2. Chain existing: `verify_kr2_build`, `audit_popup_formula`, `kobo_tap_calibration`
3. Export tap-list markdown from calibration run into sim dir

### Phase 4 — Kindle (Mac)

1. Wire `kindle_post` + flag-gated M4b into `reader_sim/kindle/build.sh`
2. `gate.sh`: `verify_kindle_safe` + `verify_kindle_m4b` (when shipped)
3. **Previewer batch runner:** wrap KP3 CLI — exit code + log scrape for E-codes (extend `kindle_bisect` patterns)
4. STK pack → `~/Desktop/YHWH-reader-sim/kindle/` (user phone optional layer)

### Phase 5 — Play (WIN build + Mac emulator spike)

1. Stage `everywhere` navy artifact via sim build
2. Gate: epubcheck + `audit_epub_structure`
3. Spike: Android emulator + Play Books sideload — document pass/fail honestly
4. If emulator fails: Thorium + `epubtest.org` matrix as documented proxy only

### Phase 6 — CI integration (WIN)

1. Optional `ci.py --reader-sim-gates` — gate-only on cached `build/reader-sim/` (no rebuild in CI)
2. Document in `TOOLCHAIN.md` §Reader Simulation Lab

---

## What we explicitly defer

- Headless Apple Books automation (no supported API)
- Shipping Nickel/KFX source engines
- Claiming Play emulator = phone truth without device sign-off

---

## References

- `dev/EREADERS.md` — per-reader truth record
- `docs/superpowers/notes/2026-06-18-platform-implementation-matrix.md`
- `dev/TOOLCHAIN.md` — kepubify, Kindle Previewer, Thorium
- `dev/kobo_tap_calibration.py`, `dev/audit_popup_formula.py`, `dev/kindle_bisect.py`
- Platform briefs: `notes/2026-06-18-platform-{apple,kobo,kindle,play}.md`