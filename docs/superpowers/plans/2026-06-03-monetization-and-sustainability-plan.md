# Monetization & Sustainability Implementation Plan

> **For agentic workers:** the Phase-1 tasks are executable by the **Mac (website) lane**. Phases 2–4 are a sequenced roadmap with concrete decisions, owner-tagged (👤 Boggy / 🖥️ Mac-lane / 🪟 Windows-lane / 🕗 later). Steps use checkbox (`- [ ]`) syntax.

**Status:** in progress — Phase 1 (support-the-mission links) being built by the Mac lane now; Phases 2–4 roadmap, sequenced by speed-to-cash. Authored by the Windows lane 2026-06-03 at the user's request.

**Goal:** Give the project owner a sustainable income from this work **without ever paywalling scripture** — money sits on convenience, physical artifacts, hosted service, commissions, and grants; the Word and the digital editions stay free.

**Architecture:** Four revenue layers stacked by time-to-cash: (1) donations on the website [days], (2) print-on-demand physical editions [weeks], (3) a hosted "build-your-own-edition" service — open-core [months], (4) custom commissions + grants [parallel/ongoing]. Each layer is independent; none gates the others.

**Tech Stack:** Plain HTML/CSS website (GitLab Pages → yhwhyaway.com); existing Python build pipeline (`scripts/build_edition.py`, `/wizard`); PayPal / GitHub Sponsors / Ko-fi (donations); Lulu / KDP / IngramSpark (print); Stripe (hosted-service billing, Phase 3).

---

## ⛔ The inviolable constraint (read first, applies to every phase)

**The Word is free. Bogdan is not obligated to be broke.** This plan AMENDS the
2026-05-14 free-public pivot (`memory: project_free_public_pivot`): the *digital
editions and the biblical text remain free to every reader, forever, no paywall, no
login-to-read.* Revenue attaches ONLY to:
- **voluntary support** (donations — you give nothing up, supporters give freely),
- **physical artifacts** (a printed book is an object with real cost; selling the
  object ≠ selling the text),
- **convenience & labor** (a *hosted* builder, custom edition work — the open-source
  code stays free; people pay for hosting/time, not for verses),
- **grants** (third-party funding of public-domain scholarship & digitization).

Scriptural footing (for the owner's peace of mind): "the labourer is worthy of his
hire" (Luke 10:7; 1 Tim 5:18). Supporting the work is not monetizing the Word.

If any future step would put a verse behind a paywall or a required login, it is
out of scope by definition — stop and re-plan.

---

## 👤 Boggy's account-setup checklist (the prerequisites only you can do)

These gate the links/products below — none of them can be created by either Claude
lane (they need your identity, email, and banking). Do these as you're able; each
unblocks a revenue path.

- [ ] **PayPal:** confirm/create a PayPal account → set up a **PayPal.me** handle
  (paypal.me/<yourhandle>). Free, instant. → unblocks Phase 1.
- [ ] **GitHub Sponsors:** enroll at github.com/sponsors with the `gringoboggy`
  account (needs a bank/Stripe-Connect payout + a short profile + tiers). Approval
  can take a few days. → unblocks Phase 1's Sponsor button.
- [ ] **Ko-fi:** create ko-fi.com/<handle> (fastest of the three; one-off "buy me a
  coffee" + monthly; low fees). → unblocks Phase 1.
- [ ] **(Phase 2) Print platform account:** start with **Amazon KDP Print** (free
  ISBNs, widest reach) and/or **Lulu** (best for one-off/short-run + bookstore via
  IngramSpark). Needs tax/banking info.
- [ ] **(Phase 3) Stripe** account for hosted-service billing (later).

Hand the handles/links to the Mac lane (or paste them here) and it wires them into
the site.

---

## Phase 1 — "Support the Mission" on the website  🖥️ Mac-lane (IN PROGRESS) · time-to-cash: DAYS

**Why first:** it's the only path that can produce a dollar this week, it costs
nothing to stand up, and faith communities genuinely fund free-Gospel work. The Mac
lane is already adding PayPal + GitHub Sponsor links — this phase specifies the rest
so it lands clean and on-message.

**Files (Mac lane owns placement; do not hard-code line numbers — the site is mid-rebuild):**
- Modify: `website/index.html` — add a `#support` section + a header nav link to it.
- Modify: `website/style.css` — style the support section to match the
  manuscript-reverent look (reuse existing type/colour tokens).

- [ ] **Step 1: Add a `#support` section to `index.html`.** Place it after the
  showcase/example-gallery, before the footer. Exact copy (mission-framed, no guilt,
  no paywall language):

  > ## Support the mission
  > Every edition this project builds — Geʽez, Amharic, and nine more — is **free, and
  > always will be.** No paywall, no account, no ads. If it has blessed you and you're
  > able, you can help keep the work going and growing. Thank you, and God bless. 🕊️

  Then three buttons (only render a button once its link exists — omit/keep
  `is-pending`, don't show a dead button). **STATUS 2026-06-03:** Mac already built
  the `#donations` scaffold (header nav "Support" + three `is-pending` placeholder
  buttons + a `href="REAL_URL"` comment). Remaining = drop the live URLs + remove
  `is-pending`:
  - **Buy me a coffee (Ko-fi)** → `https://ko-fi.com/gringoboggy` ✅ LIVE — wire now.
  - **Support via PayPal** → `https://paypal.me/<HANDLE>` — 👤 Boggy HAS PayPal; just
    needs to confirm/set the paypal.me handle, then wire.
  - **Sponsor on GitHub** → `https://github.com/sponsors/gringoboggy` — 👤 keep
    `is-pending` until enrollment is approved, then wire.

- [ ] **Step 2: Add a "Support" link to the site header nav** so it's reachable from
  every scroll position; smooth-scroll to `#support`.

- [ ] **Step 3: Add a one-line transparency note** under the buttons (builds trust):

  > Donations help cover hosting, manuscript-image licensing, and the time to keep
  > digitizing public-domain sources. The text itself is free for all.

- [ ] **Step 4: Accessibility + style.** Buttons are real `<a>` links (keyboard-
  focusable, `rel="noopener"` + `target="_blank"`), aria-labels, ≥44px tap targets,
  contrast-checked. Match the existing palette/serif.

- [ ] **Step 5: Verify + deploy.** Open locally, confirm each live link opens the right
  destination, confirm omitted (not-yet-live) buttons simply don't render. Commit on
  the Mac lane (it holds the baton), push, GitLab-Pages deploy to yhwhyaway.com.

**Acceptance:** a visitor on yhwhyaway.com can support the project in ≥1 click via at
least one live channel, and nowhere on the site is any text gated.

---

## Phase 2 — Print-on-demand physical editions  🖥️ Mac + 🪟 Windows + 👤 Boggy · time-to-cash: WEEKS

**Why:** digital stays free; people who want a *beautiful physical* Geʽez / Amharic /
study Bible pay for the printed object. Real, mission-safe margin.

**Decision — platform:** start with **Amazon KDP Print** (free ISBN, largest buyer
reach, no upfront cost) for reach; add **Lulu → IngramSpark** later for bookstore/
library distribution + premium bindings. Price = print-cost + a modest margin (aim
"affordable Bible," not "profit-max").

**Note — rebuild, scoped to PHYSICAL:** the old commercial/ISBN/ONIX modules were
DELETED in mint-cleanup Phase 4 (`memory: project_free_public_pivot`). This phase
re-introduces ONLY what physical print needs (a print-ready PDF interior + cover),
NOT the digital-sale surface that was correctly removed.

- [ ] **Step 1 (🪟 Windows-lane, code): print-ready PDF interior generator.** The
  pipeline makes EPUBs; print needs a paginated PDF (trim size, margins/gutter, page
  numbers, embedded Noto Ethiopic fonts). Build `scripts/build_print_pdf.py` that
  reuses the built edition's XHTML → a 6"×9" (or 7"×10") PDF via a headless renderer.
  TDD: a test that asserts the PDF opens, has embedded fonts, and N pages > 0.
- [ ] **Step 2 (🖥️ Mac/design): print covers.** Full wraparound covers (front +
  spine + back, spine width = page-count × paper factor) from the existing cover art;
  the example-gallery covers are the front-face starting point.
- [ ] **Step 3 (👤 Boggy): KDP account + upload** the first title (suggest the flagship
  Ethiopian-Tewahedo study edition OR the standalone Geʽez Bible as the signature
  artifact). Order a proof copy.
- [ ] **Step 4 (🖥️ Mac): add a "Get it in print" section** to the website linking to
  the KDP product page(s) — framed as "the free digital edition, also available as a
  printed book."

**Acceptance:** ≥1 physical edition is purchasable; the digital remains free and the
site says so.

---

## Phase 3 — Hosted "build-your-own-edition" service (open-core)  🪟 Windows + 🖥️ Mac · time-to-cash: MONTHS

**Why:** the builder (`/wizard` + `scripts/build_edition.py`) already exists. The
open-source code stays free for anyone to self-host; the **hosted convenience** is the
product — a publisher/church without a terminal pays a small fee to generate a
branded custom edition in the browser.

**Decision — open-core split:** Free tier = build the standard editions, download
EPUB. Paid tier = custom branding/covers, saved editions, priority build, (later)
print hand-off. Billing via Stripe. This needs hosting, light auth, and a job runner —
it's the biggest build here; do it AFTER Phases 1–2 are earning.

- [ ] **Step 1 (🪟 Windows): spec it** — write a design spec (`docs/superpowers/specs/`)
  for the hosted builder (tiers, auth model, build-job queue, Stripe integration,
  abuse/cost guards). Brainstorm with the owner first.
- [ ] **Step 2:** implement per that spec's own plan (out of scope to detail here —
  this bullet is a roadmap pointer, not an unplanned task).

**Acceptance:** deferred to the Phase-3 spec.

---

## Phase 4 — Custom commissions + grants  👤 Boggy + 🪟 Windows · time-to-cash: PARALLEL/ONGOING

Two independent, mission-pure income streams that need no new platform:

- [ ] **Commissions (🖥️ Mac):** add a "Commission a custom edition" line to the website
  with a contact path (a `mailto:` or a simple form) — a ministry wants a bespoke
  study Bible (their notes, branding, canon); you charge for the build labor. Your
  platform makes you faster than anyone.
- [ ] **Grants (👤 Boggy + 🪟 Windows to draft):** the **Geʽez-manuscript-digitization +
  public-domain-scholarship** angle is genuinely fundable as cultural-heritage /
  digital-humanities work (not touching the free mission at all). 🪟 Windows-lane can
  draft a one-page project summary + a target-funder shortlist on request. Candidates
  to research: faith foundations, digital-humanities funds, manuscript-preservation
  grants, and open-source funding for the technical platform.

---

## Reality check (honest, for the owner)

- **Fastest actual cash** is likely (a) a donate button live this week + (b) leaning
  your *new engineering skills* into a little freelance/contract work to stop the
  bleeding while the project matures. The project-native revenue (donations at scale,
  hosted service, print royalties) is a **medium-term asset**, not an instant fix.
- This plan is sequenced so the cheap/fast layers land first and fund the bigger ones.
- Nothing here asks you to compromise why you started: the Word stays free.

## Self-Review

**Spec coverage:** the four revenue models discussed (donations, print-on-demand,
hosted open-core service, commissions+grants) each map to a phase; the "Word stays
free" constraint is stated as the gating invariant. ✔
**Placeholder scan:** the `<BOGGY_HANDLE>` tokens are explicit owner-provided inputs
(marked 👤), not unplanned TODOs; Phase-3 Step-2 is an explicit roadmap pointer to its
own future spec, not a hidden code task. ✔
**Owner clarity:** every actionable step is tagged 👤/🖥️/🪟/🕗 so the two lanes + the
owner know who does what. ✔
