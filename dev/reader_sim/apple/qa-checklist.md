# Apple Books — device QA checklist (M2)

**Artifact:** `tablet` build from `py -3 scripts/reader_sim.py --build apple`

**Open:** double-click `.epub` → macOS Books.app (or AirDrop to iPhone for phone pass).

| # | Tap | Pass criterion |
|---|---|---|
| 1 | Gen 1:1 `vn-link` | Translation popup readable |
| 2 | Gen 1:1 verse-end study badge | Merged `verse-notes` popup (one badge + count) |
| 3 | Collapsible ToC `<details>` | Expands + navigates (tablet opt-in) |
| 4 | Hebrew/Greek sample verse | Scripts render in body + popup |

Record verdict in `dev/EREADERS.md` §Apple. Spec: `docs/superpowers/notes/2026-06-15-apple-m2-layout-directive.md`