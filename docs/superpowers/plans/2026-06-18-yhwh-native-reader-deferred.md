# YHWH Native Reader — deferred (post current-reader arc)

**Status:** DEFERRED — start only after Round 9 audit gate + Reader Simulation Lab close current readers (Kobo · Kindle · Apple · Play).

**User intent (2026-06-18):** A first-party reader channel that exceeds what any market reader does today — not a patch on Nickel/KFX/Play engines. Current per-reader EPUB forks and sim lab stay the priority.

---

## Goal

One **semantic document model** + **YHWH Reader app** (Chromium/WebView) as the reference renderer:

- Colored, fully formatted popups from badges (HTML/CSS/fonts — all scripts/symbols)
- Math (MathML/KaTeX) in popups where needed
- Badge kinds extensible (translation · study · math · custom · **teleport/navigate**)
- Collapsible native TOC and collapsible body blocks (`<details>` / fold regions)
- Agent-runnable QA oracle (replaces Thorium as "intended behavior" sim)

Optional later: compile profiles for **new** e-ink/color hardware running YHWH runtime — not adaptation to stock Kobo/Kindle ingestion.

---

## Prerequisite (do first)

| Gate | Why |
|---|---|
| Round 9 `ci.py` GREEN + `rx-surfaces` | Audit arc closed |
| Reader Sim Lab `--sim all` | Current-reader rules encoded as runnable oracles |
| M3/M4/M2/M5 columns honest in `EREADERS.md` | Device-proven constraints become the Core spec |

Today's `target_reader` forks (`eink`, `tablet`, `kindle_post`, `everywhere`) remain the shipping path to **existing** stores/devices.

---

## Architecture sketch (when started)

```text
YHWH Core (semantic EPUB + manifest)
  → YHWH Reader (full fidelity — reference)
  → legacy compile profiles (eink / tablet / kindle) — already built; regression via sim lab
```

Badge registry · popup sheet controller · fold/TOC controller · font pack · optional `yhwh:reader-profile=native` OPF meta.

---

## Out of scope for v0 native reader

- Replacing Send-to-Kindle or Kobo sideload as primary distribution
- Claiming stock Nickel/KFX will render rich popups
- Blocking v1.0.0 tag on native reader

---

## References

- `plans/2026-06-18-reader-simulation-lab.md` — near-term
- `dev/EREADERS.md` — per-reader truth today
- `scripts/build_edition.py` — badge/popup/TOC emitters
- pywebview desktop shell — `scripts/launcher.py`