# Marathon reviews — per-chapter C-3 / C-6 / C-8 review records

Per-chapter sub-directories (`{ref}/`) hold the adversarial review records
produced during the τ.6.x.4.b (Samuel) and τ.6.x.4.c (Kings) marathons.

**Why this directory exists:** the flat `dev/` layout worked while there
were a few reviews per chapter; 1Ki4 alone produced 11 review files (GG
R1-R7 + CAM R1-R3 + C-8 collation) over 2 days. At 4 chapters in, `dev/`
was already cluttered enough to motivate the split. Going forward every
chapter's reviews land here under `dev/marathon_reviews/{ref}/`.

## Per-chapter layout

```
dev/marathon_reviews/
  1ki4/
    REVIEW_2026-05-19-1ki4-GG-R1.md     ← C-3 round 1 (GG witness)
    REVIEW_2026-05-19-1ki4-GG-R2.md     ← C-3 round 2
    ...
    REVIEW_2026-05-20-1ki4-GG-R7.md     ← C-3 round 7 (APPROVED CLEAN)
    REVIEW_2026-05-20-1ki4-CAM-R1.md    ← C-6 round 1 (CAM witness)
    ...
    REVIEW_2026-05-20-1ki4-CAM-R3.md    ← C-6 round 3 (APPROVED CLEAN)
    REVIEW_2026-05-20-1ki4-collation.md ← C-8 collation review
```

**What stays in `dev/`:**

- `dev/CALIBRATION_{date}-{book}-{ref}.md` — per-chapter calibration
  outcome (the headline record; one per chapter).
- `dev/AUDIT_*.md` — audits.
- `dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md`, `dev/CHANGELOG.md`,
  `dev/MARATHON_LEDGER.md` — durable cross-session state.
- `dev/CLAUDE_PROJECT_RULES.md`, `dev/PLAN_2026-05-09.md` — bootstrap
  triad.

**Filename convention** (unchanged): `REVIEW_{YYYY-MM-DD}-{ref}-{WITNESS}-R{N}.md`
for review rounds; `REVIEW_{YYYY-MM-DD}-{ref}-collation.md` for the C-8
collation review.

**Lookup:** if you need to find a specific round's report, the path is
`dev/marathon_reviews/{ref}/REVIEW_{date}-{ref}-{WITNESS}-R{N}.md` — the
directory is the chapter ref, the file is the round.
