# Trufflehog secret-scan — 2026-05-10 sweep

**Tool:** `trufflehog3` 3.0.10
**Scope:** entire working tree
**Mode:** `--no-history` (current state only)

## Result: zero real secrets

All MEDIUM-severity findings are false positives:

| Path | Finding | Why it's not a secret |
|---|---|---|
| `content/translations/sources/kjv/signature.txt.asc` | High-entropy GPG signature block | This is a PGP-armored signature on the KJV PD-source distribution — intentional crypto metadata for verifying the upstream archive. Not a leaked credential; the public-key counterpart is upstream. |
| `scripts/check_a11y.py:77,79` | High-entropy string `"0123456789abcdefABCDEF"` | Literal hex-character set used to parse CSS color codes (`#RGB` / `#RRGGBB`). The entropy heuristic confuses character-class constants with random secrets. |
| `scripts/promote.py:67` | High-entropy string `"abcdefghijklmnopqrstuvwxyz"` | The English alphabet, used for generating note-id suffixes (a, b, c, …). Same false-positive class. |

## What this confirms

- No `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` value in tree.
- `.env.example` has only the documented `sk-ant-...` placeholder.
- No SSH keys / cloud credentials / database passwords.
- No private signing keys.

## Recommended hooks

Add a pre-push hook to `save.cmd` that runs:

```
trufflehog3 --no-history --skip-paths content/translations/sources/kjv .
```

Skipping the KJV signature file removes the noise. New entropy-flagged
findings then warrant manual review before each push.

The hex/alphabet constants in `check_a11y.py` and `promote.py` would
still trip; consider adding `# trufflehog:ignore` markers next to them
once the hook is wired (out-of-scope for this sweep).
