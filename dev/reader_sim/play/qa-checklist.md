# Google Play Books — phone QA checklist (M5)

**Policy:** Agents run Thorium/emulator sim (`sim.sh`) — not user phone upload every round.

**Artifact:** `everywhere` navy EPUB — `py -3 scripts/reader_sim.py --build play`

**Automated gate:** `py -3 scripts/reader_sim.py --gate play --artifact <path>`

Full protocol: `dev/EREADERS.md` §Google Play Books (upload steps + minimum tap list).

Staged release URL: v0.1.0 `YHWH-ethiopian-tewahedo-v0.1.0-everywhere-navy.epub`

**Proxy only (not phone truth):** Thorium desktop · `audit_epub_structure` green