# Video: 92% Pakai AI. Kenapa Hasilnya Belum Kerasa?

Standalone talking-head + evidence video for a broad Indonesian
tech-curious audience worried about falling behind on AI. Natural
follow-up to `ai-bakar-uang` (Video #1 answered *"am I being replaced?"*;
this one answers *"OK, but am I falling behind?"*). House video grammar
is `style: evidence`. This folder is the **thumbnail + video bible lock**
only. Standalone — no part numbering.

| File | Role |
|------|------|
| `thumbnail.md` | Hard rules + YAML recipe (layout, colors, copy stack, export 1280×720) |
| `naskah-draft.md` | Teleprompter script (mirrors episode `edit/script.md`) |

```yaml
style: evidence
series: ai-adopsi-gap
asr:
  language: id
```

Agents must not redesign the thumbnail.

## Positioning

- **Audience:** broad Indonesian tech-curious viewers — office workers,
  freelancers, fresh grads, anyone who has tried ChatGPT but wonders why
  national productivity headlines don't match personal experience.
- **Promise:** explain Indonesia's adoption paradox (usage leader,
  productivity laggard) with screenshots, and land on what actually
  matters for **your** career — daily use vs coba-coba.
- **Persona:** same senior-engineer-adjacent, humble voice as
  `ai-bakar-uang` / `freshgrad-ai-dev`. Not hype, not doom — the
  "let's look at the numbers" voice.
- **Voice:** **saya / kalian**, bahasa lisan, no contempt. Acknowledge
  anxiety before rebutting lazy narratives.
- **Tone guardrail:** optimistic-but-honest conclusion. Every claim needs
  a screenshot/source on screen. No unsupported reassurance.
- **Language:** Indonesia. English terms that read naturally on camera
  stay English (GenAI, productivity, readiness, shadow AI).

## Relationship to Video #1

| Video | Question answered |
|-------|-------------------|
| `ai-bakar-uang` | "AI spend is huge — are we being replaced?" → No, money goes to infra; companies still hire. |
| `ai-adopsi-gap` | "Jobs aren't gone — but am I falling behind?" → Usage ≠ readiness; daily users pull ahead. |
| `ai-skill-hiring` | "Bar is up — what is 'AI skill' in a job post?" → Workflow + verification + domain, not buzzwords. |

One-sentence callback to Video #1 in the hook only. Video #3 callbacks to Video #2
(daily users) in the hook only — do not repeat 92%/23%/PwC daily gap. Do not repeat Klarna,
CBA, $700B capex, or replacement-math debunk.

## Research lock

Copy **angles / hook shape**, not wording. Verify on primary sources
before each air date.

**Title (confirmed):** 92% Pakai AI. Kenapa Hasilnya Belum Kerasa?

| Claim | Figure | Primary source |
|-------|--------|----------------|
| Pekerja RI pakai GenAI di kerja | **92%** (global 75%, APAC 83%) | [Microsoft WTI 2024 — Indonesia](https://news.microsoft.com/id-id/2024/06/11/microsoft-dan-linkedin-luncurkan-work-trend-index-2024-menilik-keadaan-ai-dalam-dunia-kerja-di-indonesia/) — cite report year |
| Adopsi 92% tapi produktivitas masih minim | Minister quote | [Kompas, Feb 2026](https://www.kompas.com/jawa-barat/read/2026/02/25/130000488/adopsi-ai-di-indonesia-tembus-92-persen-tapi-produktivitas-masih) |
| Perusahaan RI benar-benar siap AI | **23%** Pacesetters | [Cisco AI Readiness Index 2025 — Kompas Tekno](https://tekno.kompas.com/read/2025/10/15/17440707/riset-cisco-hanya-23-persen-perusahaan-di-indonesia-siap-hadapi-era-ai) |
| Leadership tanpa visi/rencana AI | **48%** khawatir | Microsoft WTI 2024 (same page) |
| Pekerja RI pakai AI setahun vs harian | **69%** vs **16%** daily GenAI | [PwC Hopes & Fears 2025 — Indonesia](https://www.pwc.com/id/en/media-centre/press-release/2026/indonesian/hopes-and-fears-2025-indonesia.html) |
| Manfaat harian vs jarang (RI) | Produktivitas **96% vs 75%**; aman kerja **82% vs 63%**; gaji **72% vs 52%** | PwC (same) |
| Pemimpin tidak rekrut tanpa skill AI | **69%** | Microsoft WTI 2024 |
| Akses belajar non-manager vs exec | **64% vs 89%** | PwC Indonesia |
| Pemakaian tanpa governance perusahaan | Corporate adoption < employee usage | [Kompas.id](https://www.kompas.id/artikel/en-adopsi-ai-generatif-melesat-literasi-digital-indonesia-masih-tertinggal) |

**Honesty guardrails:**

- 92% is **Microsoft–LinkedIn WTI 2024** — still cited by Komdigi in 2026;
  say the report year on camera.
- Cisco 23% and PwC 16% daily measure **different things** — never imply
  they're the same metric.
- Komdigi "produktivitas masih minim" is a **policy acknowledgment**, not
  a measured productivity index.

## Video spine (~15–17 min)

Title: **92% Pakai AI. Kenapa Hasilnya Belum Kerasa?**

1. Hook: 92% → Komdigi productivity gap → 23% company readiness → question.
2. Bagian 1: Personal adoption ≠ organizational readiness (92% / 23% / 48%).
3. Bagian 2: Daily vs sporadic users — PwC Indonesia gap (16% daily, 96% vs 75%).
4. Bagian 3: Why national productivity lags — structure not laziness.
5. Closing: Google Maps analogy + sign-off.

Full teleprompter: `naskah-draft.md`. Episode canonical copy:
`G:/AI/episodes/ai-adopsi-gap-ep1/edit/script.md`.

## Production

**Picture lock:** talking-head plus evidence stills, per `styles/evidence/style.md`.
Keep `style: evidence`.

- Evidence stills from `raw/evidence/` — real captures only.
- Provenance in `edit/evidence.json` per evidence style hard rules.
- MG: `callout` for big numbers; `quote`/`stat` for named claims.
- Default cover mode `prefer_evidence`.

## Hard rules for agents

1. Every claim on screen needs a source citation in the same beat.
2. Cite report years explicitly (especially Microsoft WTI 2024).
3. Real captures only — no AI-generated fake dashboards.
4. Original wording — copy angles, not transcripts.
5. Humble **saya/kalian** voice; don't dunk on doomer or hypers.
6. Confirm radio-edit before `edit/edl.json`.
