# Video: AI Bakar Triliunan, Tapi Masih Butuh Kita. Kenapa?

Standalone talking-head + evidence video for a broad Indonesian
tech-curious audience worried about AI replacing their jobs. Not a
series — one self-contained video that makes the full argument (money
destination, hiring evidence, replacement-math debunk) in one sitting.
House video grammar is `style: evidence` (talking-head plus real
screenshot evidence — never AI-generated dashboards). This folder is the
**thumbnail + video bible lock** only. If a follow-up video on a related
angle gets made later, it stands on its own — do not retrofit "part"
numbering onto this one.

| File | Role |
|------|------|
| `thumbnail.md` | Hard rules + YAML recipe (layout, colors, copy stack, export 1280×720) |

```yaml
style: evidence
series: ai-bakar-uang
asr:
  language: id
```

Agents must not redesign the thumbnail.

## Positioning

- **Audience:** broad Indonesian tech-curious viewers, not just engineers —
  anyone who has seen AI-replaces-jobs headlines and is anxious about it.
- **Promise:** show the real money and hiring evidence behind the AI
  investment wave, and use it to answer the doom narrative honestly —
  optimistic, but not naive. AI spend is real; replacement is not the
  story the numbers actually tell.
- **Persona:** same senior-engineer-adjacent, humble voice as
  `freshgrad-ai-dev`. Not a hype account, not a doomer account — the
  "let's actually look at the numbers" voice.
- **Voice:** **saya / kalian**, bahasa lisan, no "kuliah percuma"-style
  contempt for anyone. Acknowledge the fear before rebutting it.
- **Tone guardrail:** optimistic conclusion, but every optimistic claim
  must be backed by a screenshot/source on screen. Do not hand-wave
  reassurance without evidence — that is the entire premise of the
  `evidence` style pack.
- **Language:** Indonesia. English terms that read naturally on camera
  stay English (burn rate, hiring, layoff, ROI, infra).

## Research lock

Copy **angles / hook shape**, not wording. Do not paste source video
transcripts into the teleprompter; paraphrase and cite on screen.

EN references that shaped this series (views/dates as of 2026-08):

| Source | Angle we copy |
|--------|----------------|
| [dev.to — "Tech Companies Regret Firing Engineers for AI: The Quiet Rehiring Nobody's Talking About"](https://dev.to/kunal_d6a8fea2309e1571ee7/tech-companies-regret-firing-engineers-for-ai-the-quiet-rehiring-nobodys-talking-about-2026-3bnd) | Concrete gotcha: companies fired for AI, quietly rehiring humans |
| YouTube — "The Math Behind 'AI Will Replace Engineers' Is Embarrassingly Wrong" | Confrontational debunk framing, receipts over opinion |
| [CNBC — "Tech AI spending approaches $700 billion in 2026, cash taking big hit"](https://www.cnbc.com/2026/02/06/google-microsoft-meta-amazon-ai-cash.html) | Real, correctly-scoped dollar evidence for the "bakar triliunan" hook — ~$700B combined 2026 capex, four companies, one year (headline number used to match on-screen still; $725B precise breakdown via Yahoo Finance is a footnote) |
| YouTube — "Big Tech Is Burning Cash on AI — Here's Who Actually Gets It Back" | Nuanced reframe: spend as investment, not proof AI is about to replace anyone |

**Verified evidence for the hook and Bagian 2/3 claims (as of 2026-08,
see `naskah-draft.md` open-questions log for full citation trail):**

| Claim | Evidence | Source |
|-------|----------|--------|
| 2026 AI capex, 4 hyperscalers | ~$700B on the CNBC headline shown on screen (precise breakdown $725B, up 77% from $410B in 2025) | [CNBC](https://www.cnbc.com/2026/02/06/google-microsoft-meta-amazon-ai-cash.html) |
| Klarna cut ~700 agents for AI, rehired humans a year later | CEO publicly admitted "we went too far" | [Forbes](https://www.forbes.com/sites/quickerbettertech/2025/05/18/business-tech-news-klarna-reverses-on-ai-says-customers-like-talking-to-people/), [Entrepreneur](https://www.entrepreneur.com/business-news/klarna-ceo-reverses-course-by-hiring-more-humans-not-ai/491396) |
| Commonwealth Bank of Australia cut 45 roles for a voice bot, reversed + apologised | Call volumes rose, not fell | [ABC News](https://www.abc.net.au/news/2025-08-21/cba-backtracks-on-ai-job-cuts-as-chatbot-lifts-call-volumes/105679492), [Bloomberg](https://www.bloomberg.com/news/articles/2025-08-21/commonwealth-bank-reverses-job-cuts-decision-over-ai-chatbots) |
| 2 of 3 companies that laid off for AI are already rehiring | Careerminds survey, 600 HR pros, Feb 2026 | via [Yahoo Finance](https://finance.yahoo.com/sectors/technology/articles/ai-boomerang-why-companies-quietly-151721619.html) |
| 55% of employers regret AI-driven layoffs | Forrester Research | via [Gadget Review](https://www.gadgetreview.com/55-percent-of-leaders-regret-ai-layoffs-and-a-major-hiring-reversal-is-here) |
| AI coding productivity gain ~26% | Stanford AI Index | cited via secondary aggregation, verify primary Stanford AI Index report before air |
| 35% of employers expect AI to grow total headcount, 24% say already happening | Employer survey, 2026 | cited via secondary aggregation, verify primary report before air |

Still missing: no Indonesian-company example of the "AI layoff then
quiet rehire" pattern found yet — both named cases (Klarna, CBA) are
global/Western. Either find a local case before air, or say on screen
that this evidence is international, not local.

**Local anchor numbers (verify before each air date, figures move):**

| Figure | Value (Aug 2026) | Use |
|--------|------------------:|-----|
| APBN 2026 belanja negara | ~Rp 3.842,7 triliun | "AI capex is over 3x Indonesia's entire annual state budget" |
| MBG (Makan Bergizi Gratis) 2026 pagu | Rp 268 triliun (cut from Rp 335T) | Concrete, widely-known program for scale comparison |
| Kopdes Merah Putih 2026 | ~Rp 83 triliun (incl. Rp 34,57T Dana Desa) | Second concrete comparison, stacks with MBG |
| Kurs used | ~Rp 17.800/USD | Re-check against recording-day kurs, cite on screen |

These are neutral budget-size comparisons only — never frame as
commentary on whether MBG/Kopdes are good or bad policy. The point is
scale, not politics.

Numbers must be verified on primary sources (company earnings calls,
reputable tech press) before air, and shown on screen with a `callout`
overlay. Until verified, say "angka yang beredar / menurut laporan X" —
do not invent precision.

**Relevance rule:** this is an Indonesian-audience channel — any USD
figure must be converted to IDR on screen (kurs as of recording day,
cited) and, where useful, anchored to something Indonesians already
have a scale for (APBN belanja negara, UMR, a well-known local
company's valuation). Evidence should not be purely US-centric — prefer
at least one Indonesian company/startup example per episode alongside
global ones, and reference local job platforms (LinkedIn Indonesia,
Glints, Jobstreet, Kalibrr) instead of generic "job postings".

## Video spine (draft — confirm before locking)

Title: **AI Bakar Triliunan, Tapi Masih Butuh Kita. Kenapa?**
Length: 16–19 min, one continuous argument, no "part depan" teasing.

1. Hook: big burn-rate number on screen (+ IDR, + MBG/Kopdes anchor) →
   "kalau duitnya segini gede, harusnya kita udah diganti dong?" →
   reframe: spend ≠ replacement.
2. Ke mana larinya duit — infra/chip/data center, not payroll
   replacement; mostly lands in US infra, doesn't map 1:1 to ID hiring.
3. Kalau AI jago, kenapa masih nyari orang — real open hiring evidence
   (local + global platforms), plus 2–3 named cases of AI-driven
   layoffs followed by quiet rehiring.
4. Kenapa hitungan "AI gantiin N orang" salah — debunk the replacement
   math (scope, accountability, judgment calls it can't make) → land
   on: AI changes the job, doesn't delete it.
5. Closing analogy + sign-off.

See `naskah-draft.md` for the full teleprompter draft of this spine.

## Production

**Picture lock:** talking-head plus evidence stills, per `styles/evidence/style.md`.
Keep `style: evidence` — do not fork into `style: tutorial` for this
series.

- Evidence stills come from `raw/evidence/` per episode — real captures
  of articles, earnings reports, hiring posts. No AI-generated fake
  dashboards or charts.
- Provenance recorded in `edit/evidence.json` (`src`, `url`,
  `captured_at`, `note`) per the evidence style hard rules.
- MG: `callout` for the big numbers (value + source, small type).
  `stat`/`quote` cards for named claims from the reference videos above.
- Default cover mode `prefer_evidence`; full cam when making the
  argument directly to camera.

## Hard rules for agents

1. Every reassuring/optimistic claim on screen needs a source citation
   in the same beat — no unsupported hopium.
2. Every USD figure gets an IDR conversion on screen, with kurs date —
   never leave a dollar number unconverted for this audience.
3. Evidence assets must be real captures of public pages/reports. No
   AI-generated fake analytics or charts.
4. No pasted transcripts from the reference videos/articles above — copy
   the angle, write original wording, attribute if quoting a number or
   claim.
5. Keep the humble **saya/kalian** voice; don't dunk on either AI-doomers
   or AI-hypers, just show the numbers.
6. Confirm radio-edit before `edit/edl.json`.
