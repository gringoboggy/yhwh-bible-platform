# Google Play Books — phone QA checklist (M5)

**Policy:** Agents run Thorium/emulator sim (`sim.sh`) — not user phone upload every round.

**Artifact:** `everywhere` navy EPUB — `py -3 scripts/reader_sim.py --build play`

**Automated gate:** `py -3 scripts/reader_sim.py --gate play --artifact <path>`

Full protocol: `dev/EREADERS.md` §Google Play Books (upload steps + minimum tap list).

Staged release URL: v0.1.0 `YHWH-ethiopian-tewahedo-v0.1.0-everywhere-navy.epub`

**Proxy only (not phone truth):** Thorium desktop · `audit_epub_structure` green

**Pre-sim integrity (do FIRST, every re-stage):** the staged file must be a true `everywhere`
build, not a kindle-collapsed copy. Verify:
`unzip -p <epub> content.opf | grep -c '<dc:language>'` → **6**, and the OPF has **no**
`yhwh:target-reader` meta. (Round-13 found the staged navy file collapsed to 1 `dc:language` —
the kindle fingerprint — so Thorium "PASS" was on the wrong artifact. The GitHub release asset is
correct; re-stage via `--build play`.)

**Mac turn 127 (2026-06-18):** Thorium 3.4.0 installed. `YHWH_THORIUM_LIVE=1 scripts/reader_sim.py --sim play` on staged navy EPUB — **PASS** (structural gen11 + script probes). Android Studio / AVD **not installed** — emulator spike deferred; phone upload remains M5 gate.