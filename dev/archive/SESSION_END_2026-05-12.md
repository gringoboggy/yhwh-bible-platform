# Session end — 2026-05-12

**Closes**: the longest single-conversation arc in the project's
history. **38+ work units** committed today. **+881 tests** from
the ψ.36-A baseline (2253 → 3134). Lint 11/11 clean on every ship.

This doc is a professional handoff for the next session. It
captures: (1) the day's ships, (2) the code-residue audit for
the five proposal-removals, (3) the translation-status reality
check the publisher asked for, and (4) the recommended
next-session ordering.

---

## 1. Day's ships (in commit order — newest at top)

```
60d9e57  EPUB-scope reckoning: B.AI.5 + B.AI.6 + B.AI.7 + δ.9 REMOVED (doc-only)
22672ea  π-book-covers ingest + B.AI.4 REMOVED (content + doc-only)
cc8724b  ξ.26 license-key validation (Month 6 #5; closes non-money queue)
dbdb573  ξ.21 TOTP 2FA for admin auth (Month 6 #4)
2db2c04  PLAN-REFRESH-2 doc-only refresh (closed 6 of 7 drift items)
1495a85  AUDIT_2026-05-12 doc-only solo-Claude audit
c879c18  ξ.18 CSP nonces (Month 6 #3)
5f7608d  ζ.9 first-run tour engine (Month 6 #2)
a230a0b  γ.4 Ethiopian Tewahedo flagship commentary (Month 6 #1)
2466946  ο.4 archive.org auto-upload (Month 5 #7; CLOSES Month 5)
3cde88e  ε.7 press kit auto-build (Month 5 #6)
9d7dc9d  ε.6 distribution checklist (Month 5 #5)
a694510  ε.3 sales import (Month 5 #4)
```

### Closed scopes

- **Month 5** (executive + distribution operating model) — CLOSED.
  All 7 non-money items shipped: Δ.15, ε.1, ε.2, ε.3, ε.6, ε.7,
  ο.4.
- **Month 6 non-money queue** — CLOSED. All 5 remaining items
  shipped: γ.4, ζ.9, ξ.18, ξ.21, ξ.26. (Of the original 7, two
  removed per publisher EPUB-scope direction: B.AI.4 + B.AI.5.)

### Scope reductions

5 features formally removed from `PROPOSAL_FEATURE_LANDSCAPE.md`
per publisher direction. All five share one root cause: **EPUB
readers sandbox JS + block network**, so any feature requiring
runtime network calls from the EPUB is unimplementable in the
actual shipped product.

| Slot | Title | Why removed |
|---|---|---|
| B.AI.4 | Sharable verse cards | Social-distribution lever out of scope. |
| B.AI.5 | AI co-pilot (Cmd+J) | Anthropic API call from EPUB JS → blocked by Apple Books / Kindle / Google Play / Calibre sandbox. |
| B.AI.6 | Daily devotional auto-curation | Needs LLM + SMTP; neither callable from EPUB. |
| B.AI.7 | Marketing copy generator | Depended on B.AI.5 (orphaned). Also: marketing copy doesn't ship in EPUB. |
| δ.9 | Email subscription for verse-of-day | "Pure backend; SMTP" per spec. Publisher web-server endpoint; EPUB has no way to subscribe. |

All five slots **left vacant in numbering** (do not re-use).
Historical references in `dev/CHANGELOG.md` / prior
`dev/IN_FLIGHT.md` prior-task blocks / prior
`dev/SESSION_STATE.md` snapshot blocks /
`dev/AUDIT_2026-05-12.md` audit corpus snapshot **preserved
unchanged** — those are append-only point-in-time records.

---

## 2. Code-residue audit for the 5 removals

The publisher asked to "take a step back and make sure all the
removals have cleaned up anything in the code to them."
Performed a comprehensive grep across `scripts/`, `tests/`,
`content/`, and `dev/`. **Finding: zero code residue.**

| File pattern | Result |
|---|---|
| `scripts/core/copilot.py` | Does NOT exist. Was a proposal entry only. |
| `scripts/core/verse_card.py` | Does NOT exist. Was a proposal entry only. |
| `import smtplib` / SMTP usage | Not in any `.py` file. |
| `B.AI.[4-7]` references | Only in dev/ docs as strikethrough removal markers + historical CHANGELOG entries. |
| `verse_card` / `copilot` references | Only in dev/ docs as removal markers. |
| `δ.9` / `delta.9` references | Same — strikethroughs + historical. |

The one near-match worth calling out: `scripts/core/verse_of_day.py`
+ `scripts/web.py::api_verse_of_day{,_rss}` exist and stay. These
are **υ.8** (the existing PD-content RSS feed — read-only daily
verse rotation) which is a different feature from the removed
**δ.9** (email subscription). The names overlap; the scope
doesn't. υ.8 was already shipped pre-this-session and is
explicitly kept per publisher direction.

**The removals were correctly doc-only.** No orphan code, no
dead-import statements, no half-implemented module stubs. The
proposal had named these features for future work; none had
ever shipped.

---

## 3. Translation status — the publisher's flagged concern

The publisher asked: "I want to make sure there are more than
just greek and hebrew translations available for the verses.
latin and all that is still in there right?"

**Honest answer: no — the project ships exactly ONE full
verse-by-verse translation today.**

### What's actually shipped

```
content/translations/kjv/                King James Version + Apocrypha
                                         Full text: 81 books / 36,822 verses
                                         License: PD
                                         Source: eBible.org KJV package

content/translations/lxx-brenton-greek/  Septuagint (Brenton 1844, Greek text)
                                         SEED ONLY: Genesis 1:1-3 (3 verses)
                                         License: PD
                                         Status: γ.5 seed; γ.5.x ingest is pending
```

That's it. Two translations on disk; one of them is essentially
empty.

### What the popup-languages config DECLARES

Every edition's `popup_languages_default` in
`content/editions.yaml` lists languages the popup overlay
(ν.2.7) should show. Audit:

```
ethiopian-tewahedo       ['english', 'hebrew', 'greek']
catholic-study           ['english', 'hebrew', 'greek']
evangelical-reformed     ['english', 'greek']
jewish-study             ['english', 'hebrew']
scholarly-academic       ['english', 'hebrew', 'greek']
eastern-orthodox         ['english', 'greek']
anglican-bcp             ['english', 'hebrew', 'greek', 'latin']
lutheran-confessional    ['english', 'hebrew', 'greek']
coptic-orthodox          ['english', 'greek', 'arabic']
```

### The gap

- **English** — KJV ships full; verifiable popup data exists.
- **Hebrew** — only the **γ.1 Strong's word-lookup** ships
  (lemma + morphology per word). **NO full Hebrew verse-by-verse
  translation** (no JPS, no WLC text, no MT) is on disk.
- **Greek** — only **γ.2 Strong's word-lookup** ships
  (lemma + morphology) + the **3-verse LXX seed**. **NO full
  Greek verse-by-verse translation** is on disk.
- **Latin** — declared by anglican-bcp; **NO Vulgate
  translation** is on disk.
- **Arabic** — declared by coptic-orthodox; **NOT shipped**.

What the reader sees when they tap a verse in anglican-bcp and
expect Latin: the popup gracefully degrades (no data → no row).
But the EDITION'S PROMISE — that Latin is available — isn't
kept.

### What's in PLAN

Per `dev/PLAN_2026-05-09.md` §7 + `dev/SCOPE_2026-05-08-addendum-pd-translations.md`:

| Phase | Translation | Status |
|---|---|---|
| τ.1 | WEB → KJV (English) | ✓ shipped 2026-05-07 |
| τ.1.5 | KJV improvements | ✓ shipped |
| τ.2 | Douay-Rheims (English Catholic) | ◯ open |
| **τ.3** | **Vulgate (Latin)** | **◯ open** ← *publisher's named gap* |
| τ.4 | Brenton LXX (English side) | ◯ open |
| τ.5 | JPS + WLC (Hebrew side + JPS English) | ◯ open |
| τ.6 | Ge'ez (Tewahedo) | ◯ open |
| τ.7 | Greek NT (manuscript) | ◯ open |
| τ.8 | Geneva Bible (1599) | ◯ open |
| τ.9 | ASV + YLT | ◯ open |
| τ.10 | non-English translations | ◯ open |
| τ.11 | Reformation-era partials | ◯ open |
| τ.12 | NA28 / SBLGNT (modern critical Greek) | ◯ open |

**The publisher's instinct was right to ask.** The PROPOSAL +
PLAN both reference these as planned. But none have shipped.
The publisher's mental model ("they're still in there") was
out-of-date with the actual shipped state.

---

## 4. Recommended next-session ordering

Given (a) the EPUB-scope reckoning has narrowed AI work to
cover-generation, (b) the non-money queue is closed, and (c) the
translation gap is the largest publisher-visible promise the
project doesn't currently keep, this is the recommended
sequence:

```
N+1   τ.5-A   JPS + WLC ingest (Hebrew side)
              Closes the Hebrew column for every edition that
              declares hebrew in popup_languages_default. JPS
              (Jewish Publication Society, 1917 — PD) ships
              alongside the WLC Hebrew text. ~1.5-2 sessions.
              Pattern proven by τ.1 KJV ingest.

N+2   τ.4     Brenton LXX (English side) — full ingest
              Brings the LXX-Brenton-greek translation up from
              the 3-verse seed to the full text. Closes the
              Greek column for editions declaring greek in
              popup_languages_default. ~1 session.

N+3   τ.3     Vulgate (Latin) — full ingest
              Stuttgart edition (Weber-Gryson 5th ed., 2007 —
              the project would need to find a PD source like
              Vatican Press 1898 or earlier). Closes the Latin
              column for anglican-bcp. ~1.5 sessions.

N+4   τ.2     Douay-Rheims (English Catholic) — full ingest
              PD English Catholic translation. Strengthens
              catholic-study without changing popup-language
              promises. ~1 session.

N+5+  publisher direction:
      - τ.6 Ge'ez / τ.5-B WLC consonantal-only / τ.9 ASV+YLT
      - or money authorization for B.AI.1+B.AI.2 cover gen
      - or γ.4.1 Cyril/John commentary expansion (per
        SCOPE_2026-05-12-addendum-gamma-4-expansion)
      - or one of the uniqueness angles B/D/E from
        AUDIT_2026-05-10 §5
```

**Why translations jump to #1**: the publisher just discovered
the gap. Closing it improves every edition that lists
hebrew/greek/latin in popup_languages_default — which is **9 of
9 editions** (every one). This is the highest-leverage content
work currently open.

---

## 5. State at session close

```
Tests:               3134 passed / 1 skipped / 11-of-11 lint clean
Consoles:            17 cross-linked + 1 editor (/)
Editions:            9
Notes corpus:        51,394
scripts/web.py:      ~5,150 lines (4,564 baseline + Month 5+6 +
                     ξ.21 + ξ.26 additions; no god-module regression)
Test files:          63 (+8 this session: sales / distribution /
                     press_kit / archive_org / ethiopian / tour /
                     csp_nonce / totp / license)
Route tables:        7 tables, ~64 table-routed endpoints
Translations:        2 on disk (KJV full + LXX-Greek 3-verse seed)
SCOPE addenda:       18 indexed in PLAN §11
                     (+2 added today: xi-18-x-style-src + gamma-4-expansion)
Audits:              2 in dev/ (AUDIT_2026-05-11 + AUDIT_2026-05-12)
```

### Bootstrap chain for the next session

Per `dev/CLAUDE_PROJECT_RULES.md` §11 + the PLAN-REFRESH-2 update
to PLAN §10:

```
dev/CLAUDE_PROJECT_RULES.md         canonical conventions + §9 mental models
dev/SESSION_STATE.md                live snapshot of current state
dev/PROPOSAL_FEATURE_LANDSCAPE.md   Month 1-6 operating model (post-v1.0)
dev/PLAN_2026-05-09.md              this file — §10.1 operating model link
dev/SESSION_END_2026-05-12.md       this file — handoff summary
dev/AUDIT_2026-05-12.md             latest audit
```

### Money items still blocked

- **B.AI.1** Main cover AI generation — output ships in EPUB.
- **B.AI.2** Per-book cover AI generation — output ships in EPUB.
- **B.AI.3** Stability AI second provider — abstraction.
- **π.9** Bowker ISBN — ISBN registers + prints on EPUB.

(B.AI.4–B.AI.7 + δ.9 all removed; no longer in the money queue.)

### Autonomous queue (no money required)

- **τ.5-A** JPS + WLC Hebrew (RECOMMENDED NEXT)
- **τ.4** Brenton LXX English
- **τ.3** Vulgate Latin
- **τ.2** Douay-Rheims
- **γ.4.1** Cyril/John commentary expansion (per addendum)
- **ψ.30** matrix a11y + mobile
- **ξ.27 + ξ.28** ops bundle (health + graceful shutdown)
- **Uniqueness angles B/D/E** per AUDIT_2026-05-10 §5

---

*This document is a session-end handoff, not a CHANGELOG entry.
The 38+ work units are documented chronologically in
`dev/CHANGELOG.md`. This file gives the next session a single
focused starting point.*
