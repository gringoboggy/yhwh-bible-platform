# Notarization status — single source of truth

**STATE: PENDING** — Mac build + notarize in progress (instructions pushed 2026-06-20). Run dev/MAC_DESKTOP_BUILD_AND_NOTARIZE.txt on the Mac with your key.

- Accepted submission: `27aedc8a`
- Artifact: dist/YHWH-0.1.0.dmg (SHA-256 `916d882036d91562f135b7818eb6f69591de2e22e49071bb8c8d50aabe6c4e1b`, 339,959,633 bytes)
- Stapled + `stapler validate` OK (re-verified 2026-06-10) + Gatekeeper `spctl -t exec` = Notarized Developer ID
- Uploaded to the v0.1.0 GitHub release (size verified via the release API)

Prior record: `YHWH-1.0.0-beta.1.dmg` auto-stapled 2026-06-06T01:34:46Z
(submission `782d48b8-2e10-4fed-b02e-d7f19288b0d0`; the beta.N scheme is retired).

Full trace: dev/notary_autofinish.log


## Handoff from Mac (2026-06-20)
Mac placed signed+notarized artifact + build recipe on external drive (E:/F: YHWH-v2.4-releases/mac-desktop-build-handoff-2026-06-20/).

- tar: dist-YHWH-mac-v0.1.0.tar.gz (DMG + .app)
- Copied DMG to dist/YHWH-0.1.0.dmg
- README and scripts transferred for future Windows-driven Mac builds.
- Mac desktop build ownership transferred to WIN per README.


## Mac Desktop Build Handoff (2026-06-20)
Mac placed full handoff package on external drives (E:/F: \YHWH-v2.4-releases\mac-desktop-build-handoff-2026-06-20\):
- dist-YHWH-mac-v0.1.0.tar.gz (notarized v0.1.0 DMG + .app bundle, ~646MB)
- README with full instructions for future Windows-coordinated Mac builds using physical Mac or VM.
- Scripts, entitlements, icns, logs, NOTARIZATION_STATUS from Mac.
- Artifact is the v0.1.0 notarized DMG (submission 27aedc8a, SHA from prior).

DMG extracted/copied to dist/YHWH-0.1.0.dmg .
Tar copied to dist/dist-YHWH-mac-v0.1.0.tar.gz .
Mac desktop build responsibility transferred to WIN lane per README.
Future Mac desktop cuts: use the Mac as build target (see README Option A).

Update LANE_HANDOFF / TOOLCHAIN / SESSION_STATE as needed for retirement of autonomous Mac lane.
