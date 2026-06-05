# Handoff → macclaude: finish the beta launch + EN deploy + source-public (2026-06-05, from 🪟 Windows)

Windows is handing the **launch-prep** work to Mac. **The split deep-audit (win lane,
`wf_eeaa8368-6da`) is STILL ROLLING on Windows — do NOT stop it.** Everything below is the
*non-audit* work to finish.

## Saved this session (committed by Windows)
- **Website Geʽez/Amharic progress page — "not started" REMOVED** (commit `555d548e`, already
  live): every book is "source in hand" baseline. We have the complete EOTC parallel Geʽez–
  Amharic Bible PDF in-repo (`content/translations/sources/parallel-bible-eotc/Bible_Amharic_and_Geez.pdf`,
  2,539 pp) + `GAPS/` manuscripts → **it's SETTLED that we have all sources; do NOT re-verify**
  (memory `sources-already-in-place`).
- **EN-flag fix** (this commit): the `EN` badge fired on *file-exists*, so empty/stub
  back-translation files (gen=4 rows, ex/lev/2sa=0) wrongly showed "EN". Fixed
  `scripts/gen_website_progress.py`: new `_en_books` (≥50 real verse rows) + stage-gate (EN only
  on transcribed/ready). **Net: only Psalms shows EN** (the one ~complete back-translation).
  Generator + regenerated `website/src/data/{progress.json,geez-progress.html}` committed.

## TODO for Mac — finish the launch

### 1. Deploy the website (EN fix) → live
EN-fix SOURCE is committed but NOT yet on the live `yhwh-website` Pages repo. Per
`website/README.md`: `node website/build.mjs` → mirror `website/dist/` into the publish working
copy (`/Volumes/MacHD2/yhwh-site-publish`) → commit + push. Verify `geez.html` legend shows only
`◐ source in hand · ◑ transcribed · ● Bible-ready` and **EN appears on Psalms only**.

### 2. Beta release `v1.0.0-beta.1` (Windows-first; macOS auto-joins)
- **Windows binary READY**: `dist/YHWH.exe` (474.9 MB, **Microsoft-authorized/signed** — no
  SmartScreen wall) + 2 EPUBs.
- **macOS** `.dmg`: signed, notarization stuck on Apple's outage → the launchd auto-finisher
  staples + checksums it the moment Apple returns Accepted. **NOT a beta gate** — ship Windows
  first, macOS attaches itself later (see `dev/NOTARIZATION_STATUS.md`).
- **License = ALL RIGHTS RESERVED, source-available.** `LICENSE` + `COPYRIGHT.md` are CORRECT.
  User's words: *"as much code released as possible, but not stolen / distributed / changed
  without my permission."*
- **Publish path**: the site's `releases.js` REPO = `gringoboggy/yhwh-bible-platform` (the
  monorepo). Either (a) make the monorepo public + publish the release on it [needs §3 secret
  cleanup FIRST], or (b) a separate public releases repo + repoint `releases.js`. Then
  `releases.js` auto-fills the download card; repoint the "Code" nav link; redeploy.
- **⚠ gh auth is PER-MACHINE**: Windows `gh` is now `gringoboggy` (the wrong `bridge4kaladin-collab`
  account was logged OUT). **Mac must `gh auth login` as gringoboggy** to create repos / publish.

### 3. ⚠ BEFORE making the monorepo (source) public — REQUIRED secret-history cleanup
Secret-history scan found commit **`54ac7493`** scrubbed a **Voyage API key from `.env`** — a real
key may sit in git HISTORY (exposed the instant the repo goes public). Confirmed CLEAN: no token
patterns in HEAD; `content/auth.json` (TOTP) never committed; the runpod-runbook OAuth ref is a
`${VAR}` placeholder. **Action: inspect `54ac7493` + surrounding history; if a live key is there,
purge with git filter-repo/BFG + ROTATE the Voyage key, THEN flip public.** Do NOT go public until clean.

### 4. License doc-wording sweep (cosmetic, before public)
`LICENSE`/`COPYRIGHT.md` correct, but stale **"CC0" / "commercial"** wording lingers in `VERSION`
("free-public CC0 phase", "first commercial release") + a few docs
(`docs/superpowers/plans/2026-06-03-website-plan.md`, `HANDOFF_README_v7.md`). Sweep the
user-facing ones (esp. `VERSION`) to all-rights-reserved.

## The audit — leave it ROLLING on Windows
`wf_eeaa8368-6da` (win lane: tests-run · byte-stability · rx-surfaces cached; opt-build + verify +
synthesize finishing). When done, its win `survivors` merge with Mac's 12-dim `findings-mac.json`
via `deep-audit-merge.js` (paste both, run on N95) → `notes/2026-06-05-round5-split-audit-findings.md`.
**⚠ Stopping a deep-audit (TaskStop) does NOT kill its pytest/build child processes — they orphan +
churn RAM; clear with `taskkill /F /IM python.exe /T` (NEVER kill `node` = Claude's toolchain).**
