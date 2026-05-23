# Plan — LXX Greek (Swete) full ingest · Phase 2 spine, sub-phase 2

**Date:** 2026-05-23  ·  **Status:** IN PROGRESS — reconstruction core DONE (committed as a WIP checkpoint); the versification map is the NEXT build.
**Phase:** fully-customizable-builder roadmap Phase 2 (translation spine). WLC Hebrew shipped 2026-05-23 (`fcd6217`); this is the LXX-Greek sub-phase.
**Precedent:** mirror `scripts/extract_wlc_morphhb.py` + the RULES §9 "Add a new translation" recipe. WLC's `dev/CHANGELOG.md` entry (2026-05-23) is the template for the verification rigor (categorize every changed verse; 0 corruption).

---

## 1. Source + license (decided with the user)

- **Source:** Swete's Septuagint (1909–1930), via the **eliranwong/LXX-Swete-1930** digitization, cloned to the gitignored staging dir **`_acquire/LXX-Swete-1930/`** (re-clone: `git clone --depth 1 https://github.com/eliranwong/LXX-Swete-1930.git`).
- **License — PURE-PD path (user-chosen):** Swete's Greek *text* is public domain by age (Swete d. 1917; Vol I 1909/1925, Vol II 1907, Vol III 1912/1930). The eliranwong repo is **GPL-3.0**, but that covers its *added* layers (SBL transliteration `03`, morphology, pronunciation). **Use ONLY the PD text** — `00-Swete_versification.csv` (verse → first word-id) + `01-Swete_word_with_punctuations.csv` (word-id → Greek word). **NEVER** use `03` (transliteration) or any derived column. Mechanical digitization of a PD text creates no new copyright → the emitted text is PD (the same basis as using morphhb's PD WLC text but not its CC-BY morphology). Record the chain (Swete → Pasquale Amicarelli → eliranwong → archive.org PD scans) in `content/sources/ATTRIBUTIONS.md`.
- **Provenance/label:** it is **Swete**, not Brenton (same Codex B / Vaticanus tradition, but Swete's editorial conventions differ — caps the opening words, lowercase θεός). Ingest as a NEW translation id **`lxx-swete-greek`**; update the registry to label it "Greek (Septuagint / Swete)"; retire the 3-verse Brenton seed (`lxx-brenton-greek`).

## 2. Scope (user-chosen: "39 OT now, deutero next")

- **THIS pass: the 39 standard OT books only**, remapped to canonical KJV numbering.
- **Daniel → Theodotion (`Dat`)**, the received text (both `Dan` OG and `Dat` Th exist, 12 ch each).
- **Deuterocanon = the immediate follow-up pass** (Wisdom/Sirach/Judith/Tobit/Baruch/Letter-of-Jeremiah/Susanna/Bel/1-Esdras/1-2-Maccabees) — needs aligning to the project's base numbering, fiddlier than the KJV-numbered 66.
- **SKIP entirely:** Greek `1En` (conflicts with the project's Ge'ez 1 Enoch), `3Ma`, `4Ma`, `Ode` (Odes), `Pss` (Psalms of Solomon), `Sip`, and the duplicate recensions `Tbs`/`Sut`/`Bet` (+ `Dan` OG, since we take `Dat`).

## 3. What's DONE (committed WIP checkpoint, 2026-05-23)

- `scripts/extract_lxx_swete.py` — `parse_versification(path)`, `parse_words(path)`, `reconstruct(versification, words)`. A verse = the `01` words from its `00` start-id up to the next verse's start-id, **space-joined** → **PLAIN Greek** (punctuation already attached in `01`). NOT em-per-word (Greek's house format is plain — confirmed against the base's `vnote-greek` + the Brenton seed).
- `tests/test_lxx_swete_ingest.py` (6 tests green) + fixtures `tests/fixtures/swete_gen_{versification.tsv,words.tsv,expected.json}` (faithful real-data slices; expected auto-reconstructed, not hand-typed).

## 4. NEXT build — the versification map (`scripts/core/versification.py`), TDD

This is the error-prone crux. Extend `versification.py` with a `lxx_swete_to_kjv(swete_book, ch, vs) -> (proj_code, ch, vs) | None` (None = omit, e.g. LXX Ps 151).

- **Book map** `SWETE_BOOK_TO_CODE` (39 OT): Gen→gen, Exo→exo, Lev→lev, Num→num, Deu→deu, Jos→jos, Jdg→jdg, Rut→rut, 1Sa→1sa, 2Sa→2sa, 1Ki→1ki, 2Ki→2ki, 1Ch→1ch, 2Ch→2ch, Ezr→ezr, Neh→neh, Est→est, Job→job, **Psa→psa**, Pro→pro, Ecc→ecc, **Sol→sng**, Isa→isa, **Jer→jer**, Lam→lam, Eze→eze, **Dat→dan** (Theodotion), Hos→hos, Joe→joe, Amo→amo, Oba→oba, Jon→jon, Mic→mic, Nah→nah, Hab→hab, Zep→zep, Hag→hag, Zec→zec, Mal→mal.
- **Psalms remap (confirmed by Swete verse counts):**
  - LXX 1–8 = KJV 1–8 (same)
  - LXX 9 (39v) = KJV 9 (20v) + KJV 10 (18v) — split point at KJV-9's verse count (mind the superscription)
  - LXX 10–112 = KJV 11–113 (chapter +1)
  - LXX 113 (26v) = KJV 114 (8v) + KJV 115 (18v)
  - LXX 114 (9v) = KJV 116:1–9 ; LXX 115 (10v) = KJV 116:10–19
  - LXX 116–145 = KJV 117–146 (chapter +1)
  - LXX 146 (11v) = KJV 147:1–11 ; LXX 147 (9v) = KJV 147:12–20
  - LXX 148–150 = KJV 148–150 (same)
  - **LXX 151 → omit** (not in KJV)
  - **Verse-level superscription offset:** where the LXX (like Hebrew) counts the title as v1 (LXX_count == KJV_count + 1 for a 1:1-mapped psalm), drop the title verse and shift (LXX v → KJV v-1). Resolve per-psalm by comparing Swete counts to `canonical_verse_counts` (e.g. LXX Ps 11 = 9v vs KJV Ps 12 = 8v → offset; LXX Ps 10 = 7v vs KJV Ps 11 = 7v → no offset).
- **Jeremiah:** encode the documented LXX→MT chapter reorder (LXX 25:14→ the Oracles-Against-the-Nations block lands at MT 49–51, etc.). This + Psalms are the two big sub-builds.
- **Default:** identity. **Guard:** `canonical_verse_counts.coord_in_canonical_extent` omits any out-of-extent coord (e.g. the Prayer of Azariah inside Greek Daniel 3, the extra LXX verses).
- **TDD anchors:** Ps 10=KJV 11; the 9/10 merge boundary; the 116 + 147 splits; LXX 151 omitted; a Jeremiah OAN sample; a couple of identity books (Gen, Isa). Plus the coord guard (0 out-of-extent).

## 5. Then (tasks #12–14)

1. **Driver** in `extract_lxx_swete.py`: reconstruct → remap (skip non-39-OT books, Dat→dan) → write `content/translations/lxx-swete-greek/<code>.py` (canonical KJV coords). **Run `python -m ruff format content/translations/lxx-swete-greek/`** before save (RULES §9 — the hook wraps long verses; the existing kjv/wlc data is wrapped this way).
2. **Full run** + coord guard (0 out-of-extent) + verse-count sanity.
3. **Repoint the registry** (`scripts/core/popup_versions.py`): the `lxx-greek` version → `translation_id="lxx-swete-greek"`, label "Greek (Septuagint / Swete)"; it is already in `_BAKED_NOW`. Retire/replace the Brenton seed dir.
4. **Regen** popups (`python -m scripts.generate_verse_popups`) → Greek now on all 39 OT books.
5. **Verify (the WLC rigor):** categorize EVERY changed Greek verse vs HEAD — expect the existing Brenton seed/harvest Greek to be *replaced* by Swete (editorial diffs: caps, lowercase θεός, punctuation), plus thousands ADDED; 0 corruption; investigate any unexplained "other". `ebible verify` errors=0; flagship **epubcheck 0/0/0/0**.
6. **ATTRIBUTIONS.md** (Swete PD chain; GPL compilation noted, only PD text used) + provenance tier if `provenance_tier_known` needs one + update SESSION_STATE/CHANGELOG/MATRIX_MAP + `lint_rules` 16/0/0 + ruff. Save on user "save" (continue ≠ save).

## 6. Gotchas (carried from WLC + this session)

- Run python via the pythoncore full path + `$env:PYTHONUTF8="1"`; one test file at a time; **do NOT run the full `tests/test_scripts.py`** (it hangs on build/socket smokes — run targeted `-k` subsets; see memory).
- `_acquire/` is at the WORKSPACE root (`C:\Users\bogda\Documents\YHWH-v2.4-full\_acquire`), one level ABOVE the repo; gitignored; Glob skips it.
- The Greek differs from the Brenton seed — the replacement is EXPECTED, not a regression (verify via categorize-every-diff, like WLC).
