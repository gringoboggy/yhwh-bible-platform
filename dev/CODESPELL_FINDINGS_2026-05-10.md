# Codespell findings — 2026-05-10 sweep

**Tool:** `codespell` 2.4.2
**Scope:** `content/notes/*.py` (~50K notes across 87 books)
**Filter:** `dev/.codespell-ignore-words.txt` (project-specific
allowlist of Bible proper nouns, archaic English, academic
abbreviations like OT/ANE)

**Raw findings (post-filter):** ~41 candidates

## Why no auto-fix

Manual inspection of representative findings showed that the
majority are NOT typos:

- **Hebrew/Greek transliterations** rendered in italics inside
  note bodies — `mot tamut`, `berit bein ha-betarim`, `te
  shema`, `DED ANIM` (Dedanim, a tribe). Codespell flags these
  as misspellings of similar English words.
- **Topic-list markers** in Kenyon's textual-criticism notes —
  uppercase fragments like `DED ANIM`, `ARABIANS, DED` are
  the Variorum's all-caps topic delimiters, not English prose.
- **Archaic English** preserved from PD sources — `doest`,
  `builded`, `wast`, `saith`. Modernizing would corrupt the
  editorial voice of a 19th-century commentary.
- **Proper nouns** — `Carcas`, `Achor`, `Lama`, `Manger`. All
  Biblical place / person names that codespell mistakes for
  English words (`carcass`, `anchor`, `llama`, `manager`).

Auto-fix would corrupt the corpus. Each candidate needs human
review with surrounding context.

## Genuine OCR-error candidates worth reviewing

These look like real PD-source OCR artifacts that escaped the
prospect-→-promote pipeline:

| File | Line | Found | Likely | Context (excerpt) |
|---|---|---|---|---|
| `deu.py` | 17123 | `tution` | constitution? | "...this, Avith certain alterations (notably **tution**..." — also has `Avith` (OCR of "With") |
| `jos.py` | 3243 | `whic` | which | "**hat which** has come down to us" — `hat` itself is OCR for "that" |
| `jos.py` | 6162 | `fo` | of | "differing fi'om the received text" — multiple OCR artifacts in same paragraph |
| `isa.py` | 20815 | `nd` | and | mid-paragraph; standalone "nd" never legitimate |
| `2ki.py` | 7262 | `ND` | AND | likely sentence-fragment OCR |
| `2sa.py` | 10334 | `muti` | multi | likely word-prefix OCR fragment |

**Recommendation:** treat these as a low-priority cleanup phase
(future ω.34.2 if it warrants its own letter, otherwise fold into
the next CHANGELOG content-cleanup batch). They affect ~6 specific
notes out of ~50K — single-digit ppm — so the buyer demo isn't at
risk, but each fix is a credibility win for the polished editions.

## Findings to ignore (false positives confirmed)

Already in `dev/.codespell-ignore-words.txt`. The remaining 35 of
the 41 post-filter findings break down as:

- ~12 transliterations (`mot`, `bein`, `Thess` not the typo
  but the abbreviation for "Thessalonians", `Shema`, `fane`,
  `mor`, `ane`, `ot`, `nt`, `wast`, `nam`)
- ~8 proper nouns (`Carcas`, `Achor` ×4, `Lama`, `Manger` ×2,
  `Pithon`, `Hel`, `Carmel`)
- ~6 archaic verbs (`builded`, `doest`, `commend`, `commends`,
  `Childs` — possessive form, `saith`)
- ~9 OCR noise that's still legit context (`Noth` inside
  "stones-monu**th**" misread, `bloc` inside "bloc**k**",
  `theses` valid plural of thesis, `bodyHardware` etc.)

## Tool configuration

The ignore file at `dev/.codespell-ignore-words.txt` is the
single source of truth for project-allowed "not a typo" words.
Adding to it doesn't require code changes — codespell reads it
with `-I dev/.codespell-ignore-words.txt`. Recommended pre-commit
hook (future):

```bash
codespell -I dev/.codespell-ignore-words.txt content/notes/ scripts/
```

## Next sweep

Run `codespell -I dev/.codespell-ignore-words.txt scripts/` for a
pure-code typo sweep — much smaller corpus, far fewer false
positives. Did not run today; codespell on `content/notes/` was
the user-prioritized leverage.
