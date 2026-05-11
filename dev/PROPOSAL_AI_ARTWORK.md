# PLAN — AI-generated cover artwork + program iconography

> **Status:** planning document.
> **Created:** 2026-05-10 (during ω.35-B session).
> **Author scope:** plan-of-record for the AI-art-as-cover-choice feature,
> plus integration notes for the externally-commissioned .exe icon.
> **Audience:** the publisher (you) — choose vendors, sign accounts,
> prep human-designed defaults. Bogdan / the platform handles wiring.

---

## 1. Scope: three asset classes

| Class | Surface | Quantity | Source today | Source proposed |
|---|---|---|---|---|
| **Bible cover** (main cover per edition) | `/api/covers/<edition>/main` → `content/covers/<edition>/main.{png,jpg,webp}` | 1 per edition (~15 editions today; ~50 long-term) | Manual upload, optional | Manual OR AI-generated (user picks per edition) |
| **Per-book covers** (e.g. Genesis, Exodus title pages) | `/api/covers/<edition>/book/<book>` → `content/covers/<edition>/<book>.{png,jpg,webp}` | Up to ~80 per edition (66 protestant + 15 Tewahedo) | Manual upload, optional | Default human-designed set you're commissioning + AI-generated variations user can pick per-book-per-edition |
| **Program `.exe` icon** | Embedded in Windows binary; also `.app` on macOS, `.png` for the in-app header | 1 master, 6+ derived sizes | None yet | Externally commissioned (you have this in hand) |

The three classes are independent — shipping AI-cover features doesn't
block the human-designed defaults or the `.exe` icon, and vice versa.
This plan focuses primarily on **AI cover artwork**, then the
**publisher-side decisions** for everything.

---

## 2. What you need to prepare / decide on your side

### 2.1 Human-designed defaults

**Main covers — INGESTED 2026-05-11.** 25 master cover templates
now live at `content/covers/templates/` (5 styles × 5 colorways,
all 1792 × 2688 PNG, 5:8 aspect ratio paperback standard). See
`content/covers/templates/README.md` for the full catalog +
per-edition style-pairing recommendations.

| Style | Best fit |
|---|---|
| `01_ornate_leafy` | Catholic, Coptic Orthodox (warmer colorways) |
| `02_classical_corner` | Anglican, scholarly |
| `03_beadline` | Premium-positioned editions (Schuyler-grade aesthetic) |
| `04_minimal_lines` | Reformed, Lutheran Confessional, academic |
| `05_missal_central` | Ethiopian Tewahedo flagship, Eastern Orthodox |

Colorways: red, brown, navy, forest, black — covers most denominational
brand conventions.

**Reusable borders** at `content/assets/borders/` (6 transparent
PNG frames). For future expansion: generate a new leather scene
in AI → composite the border over it → save as a new template.
Pipeline documented in the templates README.

**Per-book covers — STILL OPEN.** Publisher is planning **~170 AI
illustrations** for per-book art (one per canonical book × multiple
variants/scenes, with the Ethiopian Tewahedo canon at ~81 books
× ~2 illustrations each ≈ 162). This is a critical sizing data
point for §4 cost analysis below.

Per-book filename convention (when these ship):
- `content/covers/<edition>/<book_code>.png` for an edition's
  specific per-book cover
- `content/covers/_defaults/<book_code>.png` for the
  fall-back-across-editions default

Book codes are lowercase 3-letter from `content/books.yaml`
(e.g. `gen`, `exo`, `lev`, ..., `1en` for 1 Enoch, `jub` for
Jubilees, etc.).

**License**: human-designed templates are publisher-owned
(work-for-hire). AI-generated per-book illustrations carry
provenance via sidecar JSON (provider, model, prompt, seed,
cost, timestamp — see §3.5).

### 2.2 AI-cover account decisions (one-time setup)

You'll need ONE of the following AI image accounts. My recommendation
order is below; you can switch later — the wiring is provider-agnostic.

| Provider | API access | Cost (current public pricing, ballpark) | Quality (Bible-art rated) | Compliance notes |
|---|---|---|---|---|
| **OpenAI gpt-image-1** (DALL-E successor; recommended) | ✅ via OpenAI API | ~$0.04 per 1024×1024 image | Very good; instruction-following is strong for stylistic prompts | Outputs are owned by user; commercial use allowed |
| **Stability AI Stable Diffusion 3 (API)** | ✅ via Stability API | ~$0.01–$0.04 per image | Good; needs more prompt tuning; SDXL fine-tuned variants are excellent for religious art | Outputs commercial; check the model license you select |
| **Anthropic / Claude** | ❌ no image-gen API yet | n/a | n/a | Already wired for χ-AI-notes; cannot generate images |
| **Google Imagen 4** | ✅ via Vertex AI | ~$0.05 per image | Excellent; high photorealism | Requires GCP project; more setup overhead |
| **Midjourney** | ❌ no public API (Discord-only) | $30/mo flat | Best-in-class artistic quality | Manual workflow only; can't be wired into /covers console |
| **Self-hosted SDXL / Flux** | n/a (you host) | GPU rental ~$0.50/hr | Variable; setup-intensive | Full sovereignty; longest engineering path |

**Recommended starter**: OpenAI gpt-image-1 via the existing
`ANTHROPIC_API_KEY`-style credential pattern. You already have the
Anthropic key; OpenAI is the same shape (env var → SDK call). The
cost is predictable and the quality is reliable.

**Action items for you**:
1. Decide on a provider (or "OpenAI for now, design provider-swap
   later").
2. Create an account if needed; load $20–50 of credits to start.
3. Stash the API key in a `.env` file (gitignored) at the project
   root: `OPENAI_API_KEY=sk-...`. The code will read it via
   `os.environ.get("OPENAI_API_KEY")`.
4. Decide on a **monthly budget cap** — for the wiring, I'll add a
   per-month spend gate (defaults to $0 = disabled). When you want
   to enable, set `YHWH_AI_ART_BUDGET_USD=20` (or whatever) in
   environment.

### 2.3 Decisions on style and brand

For the prompts to produce consistent output, the system needs to
know your **brand voice** for art. Pre-commit to these now:

1. **Style family** — pick one or two adjectives the system will
   inject into every prompt. Examples:
   - "Renaissance oil painting" (Botticelli, Caravaggio register)
   - "Byzantine icon" (Ethiopian Orthodox aesthetic — fits Tewahedo
     flagship)
   - "Modern minimalist" (sans-serif typography + geometric)
   - "Hand-painted watercolor" (warm, devotional)
   - "Photorealistic landscape" (location-based — Sinai, Jerusalem,
     etc.)
   - **Recommended for Tewahedo edition**: "Ethiopian Orthodox icon,
     gold-leaf halo, lapis-blue background, large-eyed figures" —
     matches the cultural tradition the flagship edition serves.
2. **Color palette** — gold/blue/red ("liturgical"), earth tones
   ("desert"), neutral grayscale ("scholarly"), etc.
3. **Typography overlay** — should the AI generate text on the
   cover (book name in Ge'ez or English) or should the build
   pipeline composite text on top of a clean image? **Recommended:
   composite separately** — AI text is often misspelled and you
   want full type control. The wiring will generate text-free
   images and let the build pipeline overlay typography.
4. **Aspect ratio** — recommended 2:3 (paperback book cover
   standard). Most APIs default to square 1:1; we'll request 2:3
   where supported.
5. **Hard guardrails** — explicit "do not generate" list, e.g.
   - No depictions of the divine face (consistent with both Jewish
     and Ethiopian Orthodox aniconic traditions for the Father)
   - No modern political imagery
   - No copyrighted character likenesses
   These get appended to every prompt as a negative prompt.

### 2.4 .exe icon — what to deliver to me

When the externally-commissioned icon is ready:
- **Single master file**: 1024×1024 PNG (transparent background),
  flat color (no drop shadow — Windows adds one).
- The build pipeline will derive: 16×16, 32×32, 48×48, 128×128,
  256×256 for the Windows `.ico` file, and 16×16 through 512×512
  for the macOS `.icns` file.
- **Filename**: `assets/program_icon.png` (I'll add the asset
  pipeline; you just drop the file).
- The icon also surfaces as a favicon in all 14 web consoles
  (cached at `/favicon.ico`). Same source file.

---

## 3. Technical architecture (what I'll build, when you say go)

### 3.1 New module: `scripts/core/ai_art.py`

Provider-agnostic art generator. Functions:

```python
def generate_cover(
    prompt: str,
    *,
    aspect_ratio: str = "2:3",
    style_family: str = None,
    seed: int = None,
) -> dict:
    """Returns {"status": "ok", "image_bytes": bytes, "format": "png",
    "provider": str, "cost_usd": float, "prompt_hash": str}
    or {"status": "error", "code": ..., "message": ...}"""

def list_providers() -> list[str]:
    """Available providers (env-key-dependent)."""

def estimate_cost(provider: str, count: int = 1) -> float:
    """Pre-flight cost estimate; powers the budget gate."""
```

Provider detection: `OPENAI_API_KEY` env present → `"openai"` provider
available; `STABILITY_API_KEY` → `"stability"` available; etc. If no
keys: `list_providers()` returns empty; UI disables the AI button.

### 3.2 New API endpoints in `scripts/api/covers.py`

| Method | Path | Action |
|---|---|---|
| POST | `/api/covers/<edition>/main/generate` | Trigger AI generation for main cover; returns proposed images (3–5 variants) for user to pick |
| POST | `/api/covers/<edition>/book/<book>/generate` | Same, for a per-book cover |
| GET | `/api/covers/_ai/budget` | Returns current month's spend + remaining budget |
| GET | `/api/covers/_ai/providers` | Returns available providers + their costs |

Each generation call:
1. Validates the budget (rejects if would exceed cap)
2. Builds the prompt (template + book-specific keywords)
3. Calls `ai_art.generate_cover(prompt, ...)` with N variants
4. Stores variants at `content/covers/<edition>/_drafts/<hash>.png`
5. Returns variant URLs + prompt used + cost charged
6. User clicks "Accept" → file is moved to the canonical slot

### 3.3 UI integration: `/covers` console

The existing `/covers` console (Phase π.4) already has slots for
main + per-book covers, each with an Upload button. Add a sibling
"Generate with AI" button per slot. Click flow:

1. Modal opens: shows the auto-built prompt with a textarea so
   user can edit
2. Style family + variant count + aspect ratio dropdowns
3. "Generate $X" button (live cost preview)
4. After generation: 3–5 thumbnails appear; user clicks one →
   that variant moves to the slot
5. Rejected variants stay in `_drafts/` for 7 days (auto-cleanup)
   so user can revisit

### 3.4 Prompt-template system

Per-book templates live in a new YAML file: `content/_ai_prompts.yaml`.
Example structure:

```yaml
defaults:
  style: "Byzantine icon, gold leaf, lapis blue, Ethiopian Orthodox aesthetic"
  negative: "no text, no human faces of the divine, no modern imagery"
  aspect_ratio: "2:3"

books:
  gen:
    keywords: "creation, garden of Eden, tree of life, seven days"
    color_emphasis: "warm green and amber"
  exo:
    keywords: "Mount Sinai, burning bush, parted sea, tablets"
    color_emphasis: "desert ochre and storm gray"
  # ... etc for each book
```

Composing a prompt: `{defaults.style} | {books.<code>.keywords},
{books.<code>.color_emphasis} | {defaults.negative}`.

You can edit this YAML to tune the look of any book without touching
code. The system reloads it on each generation call.

### 3.5 Attribution + audit trail

Every AI-generated image carries provenance metadata:
- Stored as sidecar JSON: `content/covers/<edition>/<book>.ai.json`
  with `{provider, model, prompt, seed, cost_usd, timestamp,
  user_accepted}`.
- Included in the edition's "Credits" page on build
- Logged in the existing audit log (ξ.13 — `audit_log.audit_endpoint`
  decorator on the generate-cover handler)

### 3.6 Budget enforcement

Two-layer gate:
- **Soft**: per-month rolling spend, surfaced as a banner when 80%
  used. Stored at `content/_ai_spend.yaml` (auto-mutated by the
  protected-paths-guard whitelist).
- **Hard**: refuses to call the API if `current_spend +
  estimated_cost > YHWH_AI_ART_BUDGET_USD`. Returns
  `{"status": "error", "code": "budget_exceeded"}` — UI shows a
  clear "you've used $X of $Y this month".

Default budget: $0 (feature disabled until you set the env var).

---

## 4. Cost analysis

### 4.1 Per-cover cost (current vendor pricing)

| Asset class | Variants/click | Cost/click | Lifetime estimate (one Bible) |
|---|---|---|---|
| Main cover | (already shipped — see §2.1 templates) | $0 | $0 (templates provided) |
| Per-book cover | 3 variants per click | $0.12 | $9.60 (80 books × $0.12) |
| Per-book at PUBLISHER'S TARGET (170 illustrations) | n/a (one-off batch) | $0.04 | **$6.80 one-time batch** |
| **Total per edition (incl. per-book at target)** | — | — | **~$7-10** depending on regenerations |

### 4.2 Publisher's stated target: ~170 AI illustrations

The publisher's plan (added 2026-05-11): **~170 AI illustrations
for the books within the bible themselves**. Sizing this against
the canon:
- Ethiopian Tewahedo canon: ~81 books
- Protestant canon: 66 books
- 170 illustrations ≈ 2 per book (Tewahedo canon × 2 ≈ 162; close
  match) — likely a "title page + chapter divider" or "frontispiece
  + scene" pair per book.

**Cost at OpenAI gpt-image-1 prices**:
- 170 images × $0.04 = **$6.80 one-off** for the entire per-book set
- If 3 variants per book (publisher picks one): 510 × $0.04 = $20.40
- If 5 variants per book: 850 × $0.04 = $34
- If publisher regenerates 20% over 6 months: + ~$5

**This fits comfortably in the recommended $20-50/month budget cap.**
The entire per-book art set for one Bible edition costs less than a
single hour of human illustrator time.

**Sequencing recommendation**: do the AI generation as a batch in
B.AI.2 (per-book endpoint) so the publisher sees the full set
together for cross-book brand consistency. Avoid one-at-a-time
ad-hoc generation that might drift in style.

### 4.3 Lifetime budget for the project

If publisher produces ~50 Bible editions long-term:
- Main covers: 50 × (already shipped templates) = $0
- Per-book art at publisher's 170-illustration target × 50
  editions = 8,500 images × $0.04 = **$340 total**
- Plus 20% regeneration buffer: $410

**Total lifetime AI-art spend for the entire publishing line:
~$400.** Versus the alternative of commissioning a human
illustrator (~$50 per illustration × 170 × 50 editions =
$425,000) — three orders of magnitude cheaper.

### 4.4 Recommended starting budget

- **First month** (when B.AI.1 ships): $20 (room for ~500
  generations to settle on style + first edition's per-book set)
- **Steady state**: $5-10/month (touch-up + new editions; one
  edition's full per-book batch fits in $30-50/month easily)
- **Hard cap to set today**: $50/month — well above expected,
  below any plausible runaway. For batch operations like the
  publisher's 170-illustration set, the hard cap should be
  raised TEMPORARILY (e.g. one month at $100) then dropped back.

---

## 5. Phased rollout

### Phase B.AI.1 — minimum viable AI art (1 session)
- `scripts/core/ai_art.py` module with OpenAI provider only
- `POST /api/covers/<edition>/main/generate` endpoint (main cover
  only — defers per-book to .2)
- Budget gate
- `/covers` console adds an "AI Generate" button to the main slot
- Audit + sidecar JSON
- Tests: provider mock, budget gate, audit-log integration

**Ship blocker**: OpenAI account + API key + budget env var set.

### Phase B.AI.2 — per-book covers (1 session)
- `POST /api/covers/<edition>/book/<book>/generate` endpoint
- Per-book button in `/covers` console
- `content/_ai_prompts.yaml` template system
- Bulk-generate UX: "Generate covers for all empty book slots"

**Ship blocker**: prompt template YAML populated (you provide
keywords per book; can start with the defaults and refine).

### Phase B.AI.3 — second provider (Stability or Imagen) (1 session)
- Add a second provider module so user can A/B compare
- Provider toggle in the UI
- Provider-specific cost telemetry

**Ship blocker**: second account.

### Phase B.AI.4 — quality refinements (1–2 sessions)
- Variant grid with click-to-regenerate-one
- Style transfer (upload a reference image, generate in that style)
- Manual editing of the prompt template per generation
- Multi-edition theme inheritance

### Phase B.AI.5 — production hardening
- Async background generation (instead of blocking the request)
- Caching: identical prompt + seed reuses prior result (free)
- Rate-limit per user (anti-DOS on the API key)

---

## 6. The .exe icon — INGESTED 2026-05-11

**Status: complete.** Publisher delivered a fully pre-rendered
icon pack at `assets/icons/`:

- `program_icon.ico` — Windows multi-resolution icon (embeds
  16/32/48/64/128/256 sizes)
- `program_icon_2048.png` + `program_icon_2048_transparent.png`
  — full-res masters (opaque + alpha)
- 12 pre-rendered PNG sizes: 16, 24, 32, 48, 64, 96, 128, 192,
  256, 384, 512, 1024

Source was Midjourney with manual cleanup (garbled text +
stray © hallucination removed; transparent background isolated).

Total footprint: ~8 MB. Full catalog in `assets/icons/README.md`.

**The originally-planned `scripts/build_icons.py` is no
longer needed** — the publisher pre-rendered every size we'd
have generated.

### Already wired (2026-05-11)

- **Web favicon route**: `/favicon.ico` serves
  `assets/icons/program_icon.ico` with `image/x-icon`
  content-type and a 24-hour public-cache header. Pinned by
  `TestFaviconRoute` (4 tests covering the route, the file
  existence, the 404 path, and all 12 documented sizes).

### Pending wiring (future θ.* phases)

| Target | File | Phase |
|---|---|---|
| PyInstaller (Windows .exe) | `program_icon.ico` | θ.1 (binary build) |
| macOS .icns | derive from `icon_1024.png` (or all sizes) | θ.4 (macOS dist) |
| Linux desktop entry | `icon_512.png` or `icon_1024.png` | θ.5+ |
| Web touch icon (iOS, Android) | `icon_192.png` | when web edition ships PWA features |
| PWA manifest icons | `icon_192.png` + `icon_512.png` | δ.8 (PWA install) |

Each of these is a ~5-line wire-up against the existing icon
files when the relevant phase ships — no fresh asset work.

---

## 7. Risk register

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| AI generates inappropriate imagery despite negative prompts | Medium | High (publisher reputation) | Pre-acceptance human review (UX makes this the default — user MUST click to accept); audit log captures rejected variants for review |
| Generated images are too generic, all editions look the same | Medium | Medium | Per-book + per-edition keyword overrides; style_family parameter; manual fallback always available |
| API cost runaway (e.g. a bug loops the generator) | Low | High | Hard budget cap; refuses to call API if exceeded; alert at 80% |
| Vendor changes pricing or revokes API access | Medium | Low | Provider-agnostic abstraction; switching is one env var |
| AI-art license terms change (e.g. retroactive watermarking) | Low | Medium | Sidecar JSON records the vendor terms at generation time; rebuild with new provider if needed |
| Images saved into `content/covers/` get accidentally deleted by tests | LOW (was Medium before today) | High | The protected-paths guard introduced 2026-05-10 catches this class of bug at session teardown |

---

## 8. Open questions you should decide on

When you say "go" on Phase B.AI.1, please confirm:

1. **Provider for the MVP** — OpenAI gpt-image-1? Or different?
2. **Budget cap** — recommended $20/month for the first month;
   what would you like?
3. **Style family default** — "Byzantine icon" works for the
   Tewahedo flagship; want a different default for editions
   targeting other audiences?
4. **Per-book template** — should I pre-populate
   `content/_ai_prompts.yaml` with reasonable keyword defaults
   for all 66+15 books, or wait for your input on each?
5. **Acceptance UX** — should variants auto-delete after rejection
   (cheap, no human gallery) or stay archived for 7 days (lets you
   revisit decisions)? Recommended: archived 7 days.

---

## 9. References

- `scripts/api/covers.py` — current cover handler module (ω.35-B.3a).
  This is where the new generate endpoint will live.
- `scripts/core/covers.py` — cover validation + encoding helpers
  (already exists; will absorb the AI-art metadata sidecar
  read/write).
- `scripts/api/__init__.py` — package roadmap; will add a B.AI
  family entry.
- `dev/CHANGELOG.md` — π.4-A (cover status feed) and π.4-B (cover
  upload) entries cover the existing infrastructure.
- `dev/CLAUDE_PROJECT_RULES.md` §6 — UI consistency rules
  (`/covers` is one of the 14 cross-linked consoles).
- ξ.13 (audit log) — every AI generation gets logged via the
  existing `audit_log.audit_endpoint` decorator.
- ξ.* (security) — the prompt input gets the same sanitization
  the YAML import endpoint already has (length cap, anchor
  density check for prompts that smuggle YAML, etc.).

---

## 10. Summary — what's blocking what

```
Human-designed defaults    →  YOU drop files in content/covers/_defaults/
                              (no platform work needed)

.exe icon (external)       →  YOU drop assets/program_icon.png
                              + I add scripts/build_icons.py (~1 session)

AI cover art               →  YOU pick provider, sign up, set env vars
                              + I add B.AI.1 (~1 session) once you say go
```

None of these depend on each other. They can ship in any order.

— end of plan —
