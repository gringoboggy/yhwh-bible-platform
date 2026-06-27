# Round-15 D5 — flagship study-glossary byte-streamer proof (WIN, 2026-06-27)

**Status: ✅ DONE.** The production byte-streamer that splits the flagship study-glossary is
proven byte-identical to the reference splitter on REAL flagship content at the real 64 MB
threshold, the fresh build passes the G5 contract gate, a permanent real-threshold regression
test is wired, and a confounded G5 opt-in check (`--reference-split` false-FAIL on real builds)
was found and fixed.

## The gap D5 named
`_stream_glossary_pieces_from_bytes` (`scripts/build_edition.py:5281`) is reached in PRODUCTION
only by a glossary monolith over `_GLOSSARY_STREAM_BYTE_THRESHOLD` (64 MB) — i.e. the
**ethiopian-tewahedo flagship alone**. Its byte-identity to the in-memory str splitter
(`split_study_glossary_document`) was pinned only on a ~KB synthetic with the threshold
**monkeypatched down to 1/10** (`tests/test_file_split::TestStreamGlossaryFromFile`). The real
byte branch, at the real threshold, on real multi-byte (Hebrew/Greek/Geʽez) content, had **zero
real-edition coverage** — a byte-scan miss (straddle/drop/dup) or a silent fall-through to the
~1.4 GB whole-decode str path would have shipped on the primary published edition undetected.

## DOC-CONFLICT resolved (with real data)
The program asked: *is the flagship glossary actually > 64 MB (so the byte branch fires), or is
it small enough to take the str-delegate path (zero coverage)?* — **Measured: the captured
flagship `index_split_900.html` monolith is 255,384,580 bytes (255.4 MB)** — comfortably over the
64 MB threshold, so the production build **does** take `_stream_glossary_pieces_from_bytes`. (The
"~480 MB" figure in older OOM notes was a stale/str-side estimate; the on-disk UTF-8 monolith is
~255 MB. Either way it is far over 64 MB.)

## CHECK A — str == from-file, byte-identical, on the REAL flagship monolith ✅
Captured the pre-split monolith during a real `ethiopian-tewahedo --target-reader eink` build
(zero production-code change: a driver monkeypatches the module attribute
`_iter_study_glossary_pieces_from_file` to copy the monolith aside, then delegates). Then fed it
into **both** splitters at the production glossary target (`gtarget = FILE_SPLIT_TARGET_DEFAULT =
400_000`):

| splitter | pieces | total piece bytes |
|---|---|---|
| `split_study_glossary_document` (str reference) | 690 | 255,162,686 |
| `_iter_study_glossary_pieces_from_file` (from-file → **byte branch**, 255 MB > 64 MB) | 690 | 255,162,686 |

**All 690 piece names AND bytes identical.** The byte branch ran on real flagship content at the
real threshold for the first time and is proven byte-equal to the reference. (High-RAM check, run
solo on clean RAM ≈ 8 GB free.)

## CHECK B — G5 glossary-contract gate on the fresh flagship build ✅
`dev/audit_glossary_contract.py` on the fresh built epub: **PASS** —
`pieces=690 split=690 cap=400000 max_inner_cp=399171 over_cap=0 book_heads=83 multi_bookhead=0
atoms=30148 distinct_atom_ids=30148`.
- `max_inner_cp=399171` sits **829 cp under the 400 000 navigate cap** — the round-14
  `_atom_rewrite_headroom` reservation holds at flagship link density (0 over-cap).
- one book per split piece (0 multi-bookhead), perfect atom conservation (30148 == 30148).

## Found + fixed in passing — G5 `--reference-split` false-FAIL on real builds
Running the opt-in check 4 (`--reference-split`) on the real epub **FAILed** with 44 intra-book
"inner diverges from reference" pieces. Root-caused with real data — it is a **confound in the
check, not a streamer bug**:
- The build splits the monolith **PRE-`rewrite_links`**, reserving `_atom_rewrite_headroom`
  (32 cp) per rewritable link so the POST-rewrite piece stays under cap.
- Check 4 reconstructs the monolith from the **POST-rewrite** built pieces and re-splits. In a
  built piece, the glossary back-links are already expanded to the cross-file
  `index_split_<n>_<m>.html#frag` form (probe of piece #11: **0 bare `href="#"`, 74 rewritten
  cross-file hrefs**, build-headroom regex matches **0**). So the re-split sees longer atoms with
  **zero** reserved headroom → it packs more per piece → different cut points. The reference
  consistently packed *more* than the build — the exact headroom signature.
- The gate's own synthetic check-4 tests pass only because they feed **href-less, never-rewritten**
  atoms (`<p>note</p>`), where headroom is 0 and no rewrite ever happens.

**Fix (`dev/audit_glossary_contract.py`):** check 4 now detects post-rewrite pieces
(`_REWRITTEN_HREF_RE` = `index_split_<n>_<m>.html` href form) and **SKIPS with an explanatory
WARN** instead of false-FAILing; the docstring is corrected to state the limitation. The sound
str==from-file partition proof is the PRE-rewrite monolith comparison above (CHECK A) — exactly
what `TestStreamGlossaryFromFile` pins. Re-run on the real epub: **PASS (WARN+skip, exit 0)**.
Regression test added: `test_reference_split_skips_post_rewrite_built_pieces`.

## Permanent regression (so the gap can't reopen)
`tests/test_file_split::TestStreamGlossaryFromFile::test_real_threshold_byte_branch_identical_to_str_at_scale`
(slow-marked): synthesizes an **82 MB** glossary (40 books × 10 000 multi-byte asides) that crosses
the **real** `_GLOSSARY_STREAM_BYTE_THRESHOLD` with **no monkeypatch**, so the production dispatcher
selects the byte branch itself, and asserts the from-file pieces are byte-identical to the str
splitter. PASS (20.8 s). This is the durable real-threshold coverage the small monkeypatched cases
lacked (a 255 MB fixture can't be committed; an 82 MB synthetic crossing the same threshold is the
faithful, reproducible proxy).

## Verdict
- str == from-file on the real flagship monolith: **byte-identical (690/690 pieces)**.
- G5 contract on the fresh flagship build: **PASS** (cap/one-book/atom-conservation).
- byte branch confirmed to fire on real content (255 MB > 64 MB).
- bonus: a confounded G5 opt-in check fixed (no more false-FAIL on real builds).
- 9-KJV byte-stable set untouched (eink-only path; no production code changed — only the dev gate
  `audit_glossary_contract.py` reference-split branch + tests).

## Reproduce
- Build + capture: `scratchpad/d5_build_capture.py` (in-process flagship eink build, captures the
  monolith to `…\yhwh-d5\index_split_900_flagship.html`).
- CHECK A: `scratchpad/d5_check_a.py` (str vs from-file on the captured monolith).
- CHECK B: `py -3 dev/audit_glossary_contract.py <epub>` (plain) and `--reference-split` (now
  WARN+skips on post-rewrite builds).
- Permanent test: `pytest tests/test_file_split.py -k real_threshold_byte_branch -m slow`.
