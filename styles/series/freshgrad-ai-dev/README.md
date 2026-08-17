# Series: Freshgrad Software Dev — Era AI

Talking-head career series for Indonesian CS / IT fresh graduates who are scared
AI will eat the junior job. House video grammar stays `style: tutorial`. This
folder is the **thumbnail + series bible lock** only.

| File | Role |
|------|------|
| `thumbnail.md` | Hard rules + YAML recipe (layout, colors, copy stack, export 1280×720) |

Episodes set in `project.yaml`:

```yaml
style: tutorial
series: freshgrad-ai-dev
asr:
  language: id
```

Agents must not redesign the thumbnail. Do not invent episode-local colors or
fonts for A-roll MG — keep Bold + accent `#7dd3fc` from `styles/tutorial`.

## Positioning

- **Audience:** mahasiswa tingkat akhir, freshgrad, junior 0–2 tahun, Indonesia.
- **Promise:** AI tidak menghapus software engineer. Yang mati adalah junior yang
  cuma ngetik sintaks. Series ini nunjukin cara jadi engineer yang *ngarahin*
  AI, bukan yang *digantiin* AI.
- **Voice:** lurus, ngobrol, tanpa doom. Hook pakai angka yang bikin cemas, lalu
  putar ke aksi konkret. Satu metafora per episode, diulang 2–3 kali.
- **Length:** 7–10 menit A-roll. Boleh screen demo pendek di ep 2 dan 4.
- **Language:** Indonesia. Istilah Inggris (agent, review, spec, Git) boleh
  tetap Inggris.

## Research lock (do not swap the five sources)

Ideas and *structure* come from these five videos (views as of 2026-08-17).
Narration in `edit/scripts/` is **original** — copy the angle, not the wording.

| # | Source | Views | Angle we steal |
|---|--------|------:|----------------|
| 1 | [Sajjaad Khader — AI Replacing Developers Has Officially Failed](https://www.youtube.com/watch?v=v3tLa5nHz-M) | 480k | Myth-bust: headline AI ≠ layoff; human-in-the-loop; context > vibe |
| 2 | [The PrimeTime — "AI Can't Replace Juniors" AWS CEO](https://www.youtube.com/watch?v=fP5URbP30j0) | 546k | AWS CEO quote; talent pipeline; juniors explore, AI only follows spec |
| 3 | [Fireship — What will AI Programming look like in 5 Years?](https://www.youtube.com/watch?v=eaedq1Jl2fc) | 591k | Fast hook + prediction + punchline: code is a means, judgment stays |
| 4 | [Tina Huang — How To Learn To Code In 2026](https://www.youtube.com/watch?v=oshQg1uSRvg) | 883k | Vibe vs agentic; fundamentals then agents; learn *with* AI, not *by* AI |
| 5 | [WPU / Sandhika — Kenapa SEKARANG Waktu Terbaik Belajar Coding](https://www.youtube.com/watch?v=oR6Pkw87JvI) | 87k | Contrarian “why now”; T-shaped; three-tier readiness; real portfolio |

Supporting (cite in research notes, not as primary clone): Traversy
`lvFswfNez2o` (163k, AI-enhanced junior), PZN `Sg5YKhKfweg` (65k, mandor/tukang),
WPU roadmap `RzNVQBfJi-A` (182k, speed-run fundamentals).

## Episode map

| Part | Working title | Source mix | Record folder |
|------|---------------|------------|---------------|
| 1 | AI gak gantiin kamu. Yang mati: tukang ketik kode | 1 + 3 | `freshgrad-ai-ep1` |
| 2 | Junior 2026: dari CRUD monkey jadi mandor agent | 2 + PZN | `freshgrad-ai-ep2` |
| 3 | Kenapa sekarang justru waktu terbaik belajar coding | 5 | `freshgrad-ai-ep3` |
| 4 | Roadmap 90 hari: fundamental dulu, baru AI agent | 4 + WPU roadmap | `freshgrad-ai-ep4` |
| 5 | Portofolio yang lolos screening (bukan to-do list) | 5 + 1 (proof) | `freshgrad-ai-ep5` |

## Hard rules for agents

1. Confirm radio-edit strategy before writing `edit/edl.json`.
2. Do not paste source transcripts into the teleprompter. Rewrite in the host's
   voice. Fair-use quote of **one** public CEO line is OK if attributed
   (Matt Garman / AWS).
3. No whoosh. Tutorial overlays only (chapter / emphasis / diagram / chip).
4. Audio always from cam. Screen is visual-only if a demo is used.
