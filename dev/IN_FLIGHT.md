# In-flight work — current task tracker

<!-- TRACKER-STATE: idle -->

## Prior task

**γ.4.4.C 1 Enoch Parables detail (40 entries on chs 37-71)** shipped
2026-05-12. Substantive expansion of the Book of Parables (1 Enoch's
Son-of-Man Christology section) beyond the 9 first-wave entries in
that section. Brings Parables coverage from 9 to 49 entries across
32 distinct chapters (of the section's 35); 1 Enoch share of corpus
rises from 31% to 35% — Cyril remains plurality voice but 1 Enoch
continues to climb.

**Why it matters for THIS project**: the Parables (1 Enoch 37-71) is
the textual root for pre-Christian Son-of-Man Christology — the
single most theologically load-bearing pre-canonical text for the
identification of Jesus as the apocalyptic Son of Man. Tewahedo
canonisation of 1 Enoch preserves this textual lineage where every
other major communion lost it. Anchor passages now substantively
covered: 38:2 (Righteous One — ho dikaios), 42:1-2 (Wisdom finds no
place → Mary's fiat reverses), 45:3 (Elect One enthroned for
judgment — Mt 25:31 antecedent), 48:4 (Light of Gentiles — Servant–
Son-of-Man identification), 48:7 (saved-in-his-name — Acts 4:12
antecedent), 60:7-8 (Leviathan + Behemoth — Messianic-banquet
preparation), 61:10 (Cherubim / Seraphim / Ophannim hierarchy —
Sǝbḫata Foṣǝlt anchor), 68:1 (Methuselah as first Parables scribe —
Tewahedo monastic-scribal lineage), 69:25 (cosmogonic Oath — name-
in-liturgy theology), 69:27 (Son of Man receives sum of judgment —
Jn 5:22-27 antecedent), 71:11 (Enoch's transfiguration — theosis
witness, Mount-Tabor liturgical parallel).

**Files**:
- `content/sources/ethiopian_commentaries.json` — 40 new 1 Enoch
  Parables entries appended covering all four sub-arcs: prologue
  extension (37:5) + First Parable 38-44 (11 entries: 38:2, 38:4,
  39:6, 39:12, 40:2, 40:9, 41:1, 41:8, 42:1, 42:2, 43:4) + Second
  Parable 45-57 (12: 45:3, 45:4, 46:2, 47:1, 47:3, 48:1, 48:4, 48:7,
  49:1, 49:3, 51:3, 55:4) + Third Parable 58-69 (12: 58:3, 60:1,
  60:7, 60:8, 61:8, 61:10, 63:1, 67:4, 68:1, 69:6, 69:25, 69:27) +
  Translation Visions 70-71 (4: 70:1, 70:3, 71:5, 71:11). _meta
  scope/source strings updated.
- `tests/test_ethiopian_gamma4.py` — new
  `TestGamma44CParablesDetailWave` class with 13 tests.

**Code-side wiring**: zero new code.

**Corpus state post-γ.4.4.C**:
```
ethiopian_commentaries.json: 270 entries (was 230; +40)
├─ Cyril of Alexandria     : 121 entries (John 1-7 + 11-21 — COMPLETE)
├─ Ephrem the Syrian       :  37 entries (Gen 1-9, 11)
└─ 1 Enoch tradition       : 112 entries (1en 5 books; Watchers and
                                          Parables both substantively
                                          expanded — Watchers 30 of
                                          36 chs covered; Parables 32
                                          of 35 chs covered)

Voice mix: ~45% Cyril / ~14% Ephrem / ~41% 1 Enoch
           (was 53/16/31 pre-γ.4.4.C)
γ.4 cumulative              : 258 entries beyond γ.4 seed
                             (.1.A 30 + .1.B 27 + .1.C 29 + .1.D 30 +
                              .2 32 + .4 30 + .4.B 40 + .4.C 40 = 258)
```

**+13 tests**. **γ.4.4.C tests: 13/13 pass in isolation; full-suite
serial = 3406 pass, 1 skip, 11 Windows-handle-inheritance flakers
(all pass individually — environmental, not regression). 11/11 lint
clean.**

**Forward references**:
- **γ.4.4.D** Astronomical + Dream Visions / Animal Apocalypse
  (1En 72-90).
- **γ.4.4.E** Epistle of Enoch detail (1En 91-108).
- **γ.4.2.B** Ephrem on Gen 12-50 (would rebalance voice mix back
  toward Ephrem).
- **γ.4.3** Cyril on Luke (~400 long-term).

**Recommended next ship**:
- **γ.4.4.D Astronomical + Dream Visions** — completes Mäṣḥafä Hēnok
  central narrative arc; would push 1 Enoch share past Cyril and
  make 1 Enoch the plurality voice in the corpus.
- **γ.4.2.B Ephrem on Gen 12-50** — patriarchal narrative; would
  push Ephrem share back toward 20-25% and rebalance.

**Also note — sonar reinstall completed earlier this session**:
SonarQube integration was cleanly removed and reinstalled via
`/sonarqube:sonar-integrate`. Active wiring now: MCP at parent-dir
`.mcp.json` (pinned via `--project bridge4kaladin-collab_yhwh-
bible-platform`), secrets-scanning hooks at USER scope
(`~/.claude/hooks/sonar-secrets/`), canonical config at `YHWH
v2.4/sonar-project.properties`. The ω.47 `sonarqube_quality_gate`
preflight check was NOT reinstated (was tightly coupled to a custom
`scripts/check_sonarqube.py` shim removed in the cleanup; Auto
Analysis on the SonarCloud side handles scanning automatically on
push, so the in-app gate query is no longer load-bearing). Net test
delta from sonar cleanup: -28 tests (test_sonarqube_omega47.py
removed). Net after γ.4.4.C: +13. Combined session delta: -15.
