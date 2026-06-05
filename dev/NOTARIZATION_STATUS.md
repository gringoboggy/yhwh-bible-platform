# Notarization status — single source of truth

**STATE: PENDING (waiting on Apple)** — last verified 2026-06-04 (Mac session)

The macOS notarization is the ONE genuinely-unfinished launch-prep item. It is
**PREP, not a launch trigger** — the first public release is separately gated
behind the customization feature arc + the user's explicit go. No urgency.

## Why it keeps showing up "not done"

It is genuinely not done **on Apple's side**. Two submissions of
`YHWH-1.0.0-beta.1.dmg` are both stuck:

| submission | created (UTC) | status |
|---|---|---|
| `0c0d10c1-5e3b-4c6c-a418-368edae22eea` | 2026-06-04 03:34 | `In Progress` |
| `ea5d7451-2fea-4332-a7ae-be86134d27e4` | 2026-06-04 19:20 (resubmit) | `In Progress` |

The `.app` is correctly signed (`Developer ID Application: Bogdan Zorlescu`,
hardened runtime + secure timestamp). The `.dmg` simply has **no notarization
ticket to staple** because Apple has not returned a verdict 16h+ later. Nothing
on our side is broken or forgotten. Each session's `--wait`/auto-finisher dies
when the session closes, so the next session re-discovers it as pending — that
is the recurrence, not a dropped task.

## What finishes it — don't re-derive, just trust this

`dev/notary_autofinish.sh` polls both submissions and, the instant Apple returns
**Accepted**, staples the dmg + regenerates `dist/SHA256SUMS.txt` (after
stapling) + verifies + flips this file to **DONE**. On a hard Apple failure it
captures the log + flips this file to **FAILED**.

Manual one-liner equivalent:

```
xcrun notarytool wait ea5d7451-2fea-4332-a7ae-be86134d27e4 --keychain-profile yhwh-notary \
  && xcrun stapler staple dist/YHWH-1.0.0-beta.1.dmg \
  && .venv/bin/python scripts/gen_checksums.py dist --out dist/SHA256SUMS.txt \
  && xcrun stapler validate dist/YHWH-1.0.0-beta.1.dmg
```

## How to check the REAL status (never trust prose — ask Apple)

```
xcrun notarytool info <submission-id> --keychain-profile yhwh-notary
xcrun notarytool history --keychain-profile yhwh-notary
```
