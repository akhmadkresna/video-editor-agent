# Video: 69% HRD Nggak Mau Rekrut Tanpa Skill AI. Skill Apa Itu Sebenarnya?

Standalone talking-head + evidence video for a broad Indonesian
tech-curious audience who watched the first two AI-career videos and now
asks *"OK, so what skill do I actually need?"* Natural follow-up to
`ai-bakar-uang` (Video #1: not being replaced) and `ai-adopsi-gap`
(Video #2: daily users pull ahead). House video grammar is `style: evidence`.
This folder is the **thumbnail + video bible lock** only. Standalone — no
part numbering.

| File | Role |
|------|------|
| `thumbnail.md` | Hard rules + YAML recipe (layout, colors, copy stack, export 1280×720) |
| `naskah-draft.md` | Teleprompter script (mirrors episode `edit/script.md`) |

```yaml
style: evidence
series: ai-skill-hiring
asr:
  language: id
```

Agents must not redesign the thumbnail.

## Positioning

- **Audience:** broad Indonesian tech-curious viewers — office workers,
  freelancers, fresh grads, anyone who saw "69% won't hire without AI
  skills" headlines and wonders what that actually means in practice.
- **Promise:** decode real Indonesian job posts and hiring surveys into a
  practical split — what to delegate to AI vs what makes you harder to
  replace. Not a tool tutorial; evidence of what employers filter for.
- **Persona:** same senior-engineer-adjacent, humble voice as
  `ai-bakar-uang` / `ai-adopsi-gap` / `freshgrad-ai-dev`. Not hype, not
  doom — the "let's look at the numbers and the job posts" voice.
- **Voice:** **saya / kalian**, bahasa lisan, no contempt. Acknowledge
  anxiety before rebutting lazy narratives.
- **Tone guardrail:** optimistic-but-honest conclusion. Every claim needs
  a screenshot/source on screen. No unsupported reassurance. This is **not**
  a prompt-engineering course — it's a career-decoding video.
- **Language:** Indonesia. English terms that read naturally on camera
  stay English (skill AI, hiring, workflow, verify, domain knowledge).

## Relationship to Videos #1 and #2

| Video | Question answered |
|-------|-------------------|
| `ai-bakar-uang` | "AI spend is huge — are we being replaced?" → No, money goes to infra; companies still hire. |
| `ai-adopsi-gap` | "Jobs aren't gone — but am I falling behind?" → Usage ≠ readiness; daily users pull ahead. |
| `ai-skill-hiring` | "Bar is up — but what is 'AI skill' in a job post?" → Workflow + verification + domain, not buzzwords. |

One-sentence callback to Video #2 in the hook only. Do not repeat Klarna,
CBA, $700B capex, replacement-math debunk, 92%/23% adoption paradox, or
PwC 16% daily vs sporadic gap (except one bridge line if needed).

## Research lock

Copy **angles / hook shape**, not wording. Verify on primary sources
before each air date. Job-post URLs expire — re-capture before air.

**Title (confirmed):** 69% HRD Nggak Mau Rekrut Tanpa Skill AI. Skill Apa
Itu Sebenarnya?

| Claim | Figure | Primary source |
|-------|--------|----------------|
| Pemimpin RI tidak rekrut tanpa skill AI | **69%** | [Microsoft WTI 2024 — Indonesia](https://news.microsoft.com/id-id/2024/06/11/microsoft-dan-linkedin-luncurkan-work-trend-index-2024-menilik-keadaan-ai-dalam-dunia-kerja-di-indonesia/) — cite report year |
| Prefer less experience + AI over more experience without AI | **76%** (Indonesia) | Same WTI page — verify Indonesia-specific vs APAC on screen |
| AI mentions in LinkedIn job posts → application growth | **+17%** | Microsoft WTI 2024 global/APAC press release |
| LinkedIn members adding AI skills to profiles | **142×** increase | Microsoft WTI 2024 |
| Demand growth for AI skills (Indonesia) | **148%** (2023–2025) | [Get on Board / AWS via Edstellar aggregation](https://www.edstellar.com/blog/skills-in-demand-in-indonesia) — verify primary before air |
| Shortfall digital workers by 2030 | **~9 juta** | Komdigi / industry estimates via Edstellar, Kemenaker — verify primary |

**Job-post evidence plan (capture from real pages, URLs in `evidence.json`):**

| Pattern in ID posts | Example capture | Use |
|---------------------|-----------------|-----|
| Technical AI role (dev/ML) | Kalibrr junior AI developer, Jobstreet AI software dev | Bagian 1 — "skill AI" for engineers |
| Non-technical / ops / admin | Glints or Jobstreet posts mentioning Copilot, automation, AI tools | Bagian 1 — broad audience |
| Verification / communication | Posts citing "explain to non-technical", "review output", "quality" | Bagian 2 — task vs job |
| Buzzword-only posts | Posts listing "AI" with no concrete workflow | Honest beat — not every post is meaningful |

**Honesty guardrails:**

- 69% / 76% are **Microsoft–LinkedIn WTI 2024** — say the report year on
  camera. Re-verify whether 76% is Indonesia-specific or APAC if sources
  disagree.
- Job-post screenshots are **point-in-time** — note capture date in
  `evidence.json`; re-gather if posts expire.
- Do not imply every viewer needs to become an ML engineer. Most "AI
  skill" in generalist posts = productive workflow + verification + domain
  context.
- Secondary aggregators (Edstellar, blog posts) need primary verification
  before air — say "menurut laporan X" until verified.

## Video spine (~15–17 min)

Title: **69% HRD Nggak Mau Rekrut Tanpa Skill AI. Skill Apa Itu Sebenarnya?**

1. Hook: 69% → 76% → "skill AI" sounds vague → real job posts on screen.
2. Bagian 1: What HRD writes vs what they mean — patterns from ID job posts.
3. Bagian 2: Tugas vs pekerjaan (practical) — 3 role examples; AI good at
   tasks, humans paid for jobs (judgment, accountability, context).
4. Bagian 3: Daily productive use at work — verification, workflow
   integration, data boundaries; not a tutorial, but the hiring signal.
5. Closing: AI = asisten junior cepat tapi sering salah; you are the senior
   reviewer → sign-off.

Full teleprompter: `naskah-draft.md`. Episode canonical copy:
`G:/AI/episodes/ai-skill-hiring-ep1/edit/script.md`.

## Production

**Picture lock:** talking-head plus evidence stills, per `styles/evidence/style.md`.
Keep `style: evidence`.

- Evidence stills from `raw/evidence/` — real captures only (job posts,
  WTI press, LinkedIn hiring stats).
- Provenance in `edit/evidence.json` per evidence style hard rules.
- MG: `callout` for big numbers; `quote`/`stat` for named claims; job-post
  stills for Bagian 1.
- Default cover mode `prefer_evidence`.

## Hard rules for agents

1. Every claim on screen needs a source citation in the same beat.
2. Cite report years explicitly (especially Microsoft WTI 2024).
3. Real captures only — no AI-generated fake dashboards or fake job posts.
4. Original wording — copy angles, not transcripts.
5. Humble **saya/kalian** voice; don't dunk on doomer or hypers.
6. Confirm radio-edit before `edit/edl.json`.
7. This is not a tool tutorial — no step-by-step ChatGPT demo unless the
   host explicitly requests a separate tutorial episode.
