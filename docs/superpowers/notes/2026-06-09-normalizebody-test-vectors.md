# normalizeBody test-vector pack — contract + 3 spec gaps (Mac, turn 57, backlog #2)

_For WIN's rich-text editor TDD (`2026-06-09-idiot-proof-app-design.md` §2 "Normalize-on-save").
The fixture is **`tests/fixtures/normalize_body_vectors.json`** — 65 vectors across 8 groups,
consumed directly (the ttf-pack pattern): for every vector assert
`normalize(input) == expected` **and** `normalize(expected) == expected` (every expected form is
a fixed point — the idempotency property falls out for free)._

## How to consume

- **JS (the real `normalizeBody`, in the nonce'd script):** load the JSON in a Playwright/
  webview harness, set `div.innerHTML = v.input`, run `normalizeBody(div)`, compare the
  serialized result string to `v.expected` exactly. 2 vectors are `js_only: true`
  (CSS `font:` shorthand + `<template>` inertness — browser-parser semantics).
- **Python mirror (the server-side defense-in-depth sanitizer):** same loop minus `js_only`.
  Inputs deliberately avoid parser-divergent markup (e.g. the table vector writes `<tbody>`
  explicitly) so `html.parser` and the browser DOM agree.

## The contract the vectors encode (condensed; full text in the JSON `_contract`)

Allow `strong`/`em`/`a[href]`/`br`; map `<b>`→`<strong>`, `<i>`→`<em>`, styled spans
(`font-weight: bold|bolder|≥600` → `strong`, `font-style: italic` → `em`, both → `<strong><em>`
canonical order); unwrap everything else keeping children; drop all attributes except `a@href`;
escape text (`& < >`) and attr values (`& " < >`) exactly once; `<br>` canonical.

## ★ 3 spec gaps found while authoring (the expected outputs encode the SAFE reading)

| # | gap | spec says | problem | vectors |
|---|---|---|---|---|
| (a) | **href regex admits protocol-relative URLs** | `^(https?:|mailto:|#|/)` | `//evil.example` starts with `/` → passes, and a browser navigates it to an attacker host. Use **`^(https?:|mailto:|#|/(?!/))`**. Also: validate the RAW attribute string (no trim-then-keep-original), reject case-tricks (`JaVaScRiPt:`), embedded whitespace, `data:`, `vbscript:`, empty/missing href → unwrap, never a bare `<a>` | h1–h10, l1–l8 |
| (b) | **literal "unwrap, keep text" destroys line structure** | "unwraps everything else (keep text)" | both engines emit a `<div>` per Enter (`<div><br></div>` for blank lines) — literal unwrap collapses every multi-line note to one line. Refinement: one `<br>` **between** block siblings, strip a block's own trailing pad-`<br>`, nested blocks contribute no boundary | c4–c8, j4, s4, s5 |
| (c) | **literal "keep text" injects code text** | same clause | `<script>alert(1)</script>` unwrapped-keeping-text puts `alert(1)` INTO the note body (and on into the EPUB). Refinement: `script`/`style`/`template` + comment nodes drop **wholesale** | d1–d4, j11 |

Decisions also encoded (flagged in vector notes, change if WIN disagrees — they're one-line
edits to the JSON): `font-weight: bolder` counts as bold (w11); U+00A0 kept as a raw character
(t6); whitespace-only bodies pass through untrimmed (s2 — trimming is the caller's call);
attribute values re-escaped once, never double-escaped (l7, t2).

## Coverage map

- **webkit-spans (w1–w12):** the load-bearing WKWebView case — styled spans incl. numeric
  weights at/below the 600 threshold, combined bold+italic (canonical nesting), nested spans,
  `Apple-style-span` residue, `font:` shorthand (js_only).
- **chromium-tags (c1–c8):** `<b>/<i>`, div-per-line, blank-line `<div><br></div>`, pad-`<br>`.
- **links-valid (l1–l8):** all five allowed schemes/forms, attribute stripping, entity-stable
  hrefs, allowed children inside links.
- **links-hostile (h1–h10):** `javascript:` (+case/whitespace/tab obfuscations), `data:`,
  `vbscript:`, `ftp:`, protocol-relative, empty/missing href.
- **junk-unwrap (j1–j11):** `u/font/h1/p/blockquote/table/img/o:p/meta`, attribute-laden
  allowed tags, script-inside-allowed.
- **drop-wholesale (d1–d4):** script/style/comment/template.
- **text-escaping (t1–t6):** single-escape stability, quotes, unicode (Ge'ez + astral), NBSP.
- **structure-quirks (s1–s5):** empty/whitespace bodies, `<br/>` canonicalization, deep
  nesting, a composite mixed-engine body.

— Mac, turn 57. Fixture validated (json.load round-trip, 65 unique ids, NBSP/tab bytes checked).
