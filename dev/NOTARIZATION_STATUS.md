# Notarization status — single source of truth

**STATE: PENDING (waiting on Apple)** — last verified 2026-06-05 (Mac session)

The macOS notarization is the ONE genuinely-unfinished launch-prep item. It is
**PREP, not a launch trigger** — the first public release is separately gated
behind the customization feature arc + the user's explicit go. No urgency.

## Why it keeps showing up "not done"

It is genuinely not done **on Apple's side**. Every submission of
`YHWH-1.0.0-beta.1.dmg` (identical signed bytes each time) is stuck In Progress:

| submission | created (UTC) | status |
|---|---|---|
| `0c0d10c1-5e3b-4c6c-a418-368edae22eea` | 2026-06-04 03:34 | `In Progress` |
| `ea5d7451-2fea-4332-a7ae-be86134d27e4` | 2026-06-04 19:20 (resubmit) | `In Progress` |
| `782d48b8-2e10-4fed-b02e-d7f19288b0d0` | 2026-06-05 (resubmit) | `In Progress` |

The `.app` is correctly signed (`Developer ID Application: Bogdan Zorlescu`,
hardened runtime + secure timestamp). The `.dmg` simply has **no notarization
ticket to staple** because Apple has not returned a verdict 24h+ later (the
2026-06-04 notary-service outage). Nothing on our side is broken or forgotten.

## What finishes it — automatic, don't re-derive

`dev/notary_autofinish.sh` **auto-discovers** every `YHWH-1.0.0-beta.1.dmg`
submission from `xcrun notarytool history` (no hardcoded IDs — any resubmit is
picked up automatically) and, the instant Apple returns **Accepted** on any of
them, staples the dmg + regenerates `dist/SHA256SUMS.txt` (after stapling, since
stapling changes the bytes) + verifies + flips this file to **DONE**, then erases
the whole mechanism. On a hard Apple failure (every discovered submission
terminal & non-Accepted) it captures the log + flips this file to **FAILED**.

### How it stays running across sessions / reboots (the persistence)

1. **launchd agent** `~/Library/LaunchAgents/com.yhwhyaway.notary-autofinish.plist`
   (`RunAtLoad` + `StartInterval` 1800s) runs `dev/notary_launchd_runner.sh` ->
   `notary_autofinish.sh 0` every 30 min + at each login/boot. It self-removes
   (boots out + deletes its own plist) the moment Apple returns a terminal verdict.
2. **SessionStart backstop** (Mac-local, in `.claude/settings.local.json` ->
   `dev/notary_ensure_agent.sh`): each Claude session on the Mac re-loads the agent
   if it got unloaded + kickstarts ONE immediate check. This covers the gap where
   launchd skips intervals while the Mac is asleep/unplugged. `settings.local.json`
   is gitignored (Mac-only), but the *logic* lives in the committed
   `dev/notary_*.sh` scripts, so the hook is reconstructable: re-add a
   `SessionStart` hook that runs `dev/notary_ensure_agent.sh`.

## How to check the REAL status (never trust prose — ask Apple)

```
xcrun notarytool history --keychain-profile yhwh-notary
xcrun notarytool info <submission-id> --keychain-profile yhwh-notary
```

Manual finish (equivalent to the auto-finisher, if ever needed):

```
xcrun notarytool wait <accepted-id> --keychain-profile yhwh-notary \
  && xcrun stapler staple dist/YHWH-1.0.0-beta.1.dmg \
  && .venv/bin/python scripts/gen_checksums.py dist --out dist/SHA256SUMS.txt \
  && xcrun stapler validate dist/YHWH-1.0.0-beta.1.dmg
```
