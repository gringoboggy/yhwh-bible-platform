# GitHub + GitLab repo-settings reconciliation (Mac lane, 2026-06-05)

Turn-11 backlog #2 (the read-only / CLI-doable portion). Audited the two code
repos via `gh` + `glab` (both authenticated). **Finding: they are already
near-launch-ready and well-matched** — most of this was done by the earlier
account-settings sessions. One stale README line fixed; the consequential items
are gated on the owner.

## State of both repos (`gringoboggy/yhwh-bible-platform`)

| Dimension | GitHub | GitLab | Verdict |
|---|---|---|---|
| Description | Geʽez-led, 87-book + Geʽez/Amharic + 91,733 notes + EPUB 3 | **identical** | ✅ matched |
| Topics (18) | lowercase set | same, except `Scripture` vs GitHub `scripture` | ✅ (one cosmetic case delta) |
| Homepage | `https://www.yhwhyaway.com` | (GitLab has no homepage field) | ✅ |
| Visibility | private | private | ⏳ gated (see below) |
| Default branch | `main` | `main` | ✅ |
| `main` protection | none | Maintainers-push (GitLab default) | ✅ both allow owner direct-push → two-lane model intact |
| README / LICENSE / SECURITY | present | present (shared git history) | ✅ matched by construction |

**Visible files (root):** `README.md` (comprehensive; cross-platform quick-start
present; Geʽez/Amharic Bibles surfaced as "the project's distinctive heart"),
`LICENSE` (© 2026 Bogdan Zorlescu, all rights reserved — NOT CC0, correct),
`SECURITY.md` (private reporting → `gringo.boggy@yhwhyaway.com`, scope covers the
build/EPUBs/website). All correct. The `HANDOFF_README_v7.md` link in the README
project-map resolves.

## Fixed this pass

- **README stale line corrected** — `README.md` "Notes" said *"No git remote is
  configured"*, false since the remotes were restored (2026-05-30). Reworded to
  *"the repository is mirrored to GitLab and GitHub; history is also backed up
  off-machine via git bundle."* (Both repos, shared history — one commit fixes both.)

## Remaining — gated on the owner (NOT changed autonomously)

1. **Visibility → public** — both repos are private. Making them public is the
   public-launch action, which is gated behind notarization + the owner's explicit
   greenlight (per the handoff + `dev/NOTARIZATION_STATUS.md`). **Leave private.**
   When launching: also do NOT pick an OSI license in GitHub's picker
   (source-available, not open-source).
2. **Social-preview image** — not settable cleanly via CLI (GitHub needs a web-UI
   multipart upload; passkey/browser). Verify/upload `social-card.png` in-browser at
   launch (the website already serves it as the OG image).
3. **GitLab topic case** — purely cosmetic: GitLab carries `Scripture` where GitHub
   (which forces lowercase) has `scripture`. Optional one-liner if you want them
   byte-identical: `glab api -X PUT "projects/gringoboggy%2Fyhwh-bible-platform" -f "topics=…"`.
   Not worth a write on its own.
4. **Branch protection** — intentionally left permissive. Requiring PRs/reviews on
   `main` would break the Windows↔Mac two-lane direct-push workflow. Revisit only
   after the project moves off the two-lane model.

## The OTHER repos (context, not in this pass's scope)

- `gringoboggy/yhwh-website` (public) — the GitHub Pages deploy; settings fine.
- `gringoboggy/gringoboggy` (public) — the profile README repo; done in a prior session.

*Read-only audit + one README correction. The metadata writes (visibility,
social-preview) are owner/passkey-gated and left for launch.*
