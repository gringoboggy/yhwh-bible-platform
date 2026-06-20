# Notarization status — single source of truth

**STATE: PENDING** — Mac build + notarize in progress (instructions pushed 2026-06-20). Run dev/MAC_DESKTOP_BUILD_AND_NOTARIZE.txt on the Mac with your key.

- Accepted submission: `27aedc8a`
- Artifact: dist/YHWH-0.1.0.dmg (SHA-256 `916d882036d91562f135b7818eb6f69591de2e22e49071bb8c8d50aabe6c4e1b`, 339,959,633 bytes)
- Stapled + `stapler validate` OK (re-verified 2026-06-10) + Gatekeeper `spctl -t exec` = Notarized Developer ID
- Uploaded to the v0.1.0 GitHub release (size verified via the release API)

Prior record: `YHWH-1.0.0-beta.1.dmg` auto-stapled 2026-06-06T01:34:46Z
(submission `782d48b8-2e10-4fed-b02e-d7f19288b0d0`; the beta.N scheme is retired).

Full trace: dev/notary_autofinish.log
