---
name: agentic-editor
description: >
  Local agentic YouTube editor. Ingest cam/screen footage, ASR (whisper.cpp on Mac,
  faster-whisper on Windows), radio-edit via EDL, dual-source cover, Remotion compose.
  Use when editing talking-head or tutorial videos, building EDLs, or promoting fixes
  into the agentic-editor framework.
---

# Agentic Editor

## Setup (once per machine)

```bash
export AGENTIC_EDITOR_HOME=/path/to/remotion   # this framework repo
cd "$AGENTIC_EDITOR_HOME" && uv sync && pnpm install
uv run ae doctor
# symlink this skill:
# ln -s "$AGENTIC_EDITOR_HOME/skills/agentic-editor" ~/.cursor/skills/agentic-editor
```

Workspace for **editing a video** = the episode folder (`project.yaml` + `raw/` + `edit/`).
Framework code is invoked via `ae` / `$AGENTIC_EDITOR_HOME`. Use a multi-root
`.code-workspace` when promoting reusable fixes.

## Hard rules

1. Confirm strategy before writing `edit/edl.json`.
2. Never cut mid-word; snap to transcript word boundaries; pad 30–200ms.
3. `ae cut` applies 30ms audio fades per segment — do not skip.
4. Cache transcripts — never re-ASR unless source changed (`ae ingest --force`).
5. All outputs in `edit/`. Raw footage is read-only.
6. Local ASR only: `auto` → whisper.cpp (darwin) / faster-whisper (else).
   Default language is **Indonesian** (`asr.language: id`); override per episode for other languages.
7. Promote reusable changes into `$AGENTIC_EDITOR_HOME`, not episode copies.
8. Remotion Studio: **only** via `ae compose . --studio` (stages `public/ae-media` + `--props`).
   Never start `remotion studio` bare — that shows a black empty timeline. Absolute `/Users/...`
   media paths will not load in the browser.
9. **Audio always from cam.** Screen is visual-only (muted). Prefer `screen_with_cam` for UI demos.
    Cam VO is DeepFilterNet-enhanced by default (`voice_enhance`, atten-lim 12 dB, delay compensated).
    Cache: `edit/audio/cam.voice.wav`. Raw is never rewritten. Opt out: `voice_enhance.enabled: false`.
    Do **not** substitute ffmpeg denoise / gate / `dialoguenhance` chains.
    SFX (typing / shutter / click) is additive under cam VO via `cover.sfx[]` — modern tech only,
    **no whoosh**. Run `ae sfx-suggest .` after cover; confirm then `--apply`.
10. **Locked look (`style: tutorial`):** house default for Odoo/tech screen demos.
    A-roll MG = **"Open Overlay" v7** — white ink straight on the a-roll, no panel,
    no accent color; readability from a darker veil scrim behind the text, not a card
    surface or a hue. Screen stage = cool-mist canvas. No full/karaoke captions.
    Do not invent episode-local colors/fonts — change `styles/tutorial/style.md`
    (+ `style_load.py` / remotion-kit theme) instead.
10b. **Evidence episodes (`style: evidence`):** start with **`ae brief`** (script + research)
    then **`ae evidence-gather`** (real screenshots into `raw/evidence/`). Never AI-generate
    fake dashboards. Host records from `edit/script.md` speaking `[[EVIDENCE:]]` cues aloud.
    After ingest: `ae evidence-suggest` ties ASR to stills. Cover events `evidence` /
    `evidence_with_cam`; MG may use `callout`. Promote knobs into `styles/evidence/style.md`.
    Docs: `docs/catalog/features/evidence-style.md`.
11. **MG overlays:** after EDL (and preferably cover) is confirmed, run `ae overlay-suggest .`,
    propose the plan, **wait for confirm**, then write `cover.json` `overlays[]` **and** any
    companion `framing` events (or `ae overlay-suggest . --apply` only after confirm).
    Never invent timings mid-word. **Default:** overlay plan is gated by cover mode +
    camera_play — chapter/diagram prefer `screen_with_cam` (wide/hold); on full-cam they
    emit medium/wide framing companions so MG does not fight close zooms (`faceClear` /
    left_third). Emphasis may sit on close. Structure (chip/chapter/diagram + section
    quotas) is reserved first; emphasis is best-fit from an ID payoff lexicon scored by
    screen-enter + punch proximity (punchy cam without nearby MG gets seeded emphasis).
    Gaps ~50s chapter / ~10s emphasis; density ~1 sting / 32s keep; same-label min gap ~45s
    (keeps “Roadmap” etc. from spam). Quiet keep stretches >55s get gap-fill. Emphasis
    `bottomCqh` default **28** (was too low vs PIP).
    Motion is Remotion-side on these overlays (count, line-draw, accent pop, diagram rail)
    — do not invent extra cover fields for it. **Do not** use picture-takeover
    `cover.cutaways[]` / `ae cutaway-suggest` on tutorial talking-head.
12. **Series YouTube thumbnails:**
    - `series: odoo-studio-agentic-ai` → `styles/series/odoo-studio-agentic-ai/thumbnail.md`
      (+ `refs/*-canonical.png`). Accent `#3dbff3`, export **1280×720**.
      **Plate + draw (required):** never ask an image generator for the finished thumb —
      it drifts on alignment and crops the head. Generate a **text-free plate** (host +
      studio room behind him; darkened Odoo UI only on left/edges), then
      `uv run python styles/series/odoo-studio-agentic-ai/build_thumbnail.py` (canonical
      metrics + fonts in that folder). Top-crop plates to 16:9 (never centre-crop).
    - `series: ai-youtube-idr` → `styles/series/ai-youtube-idr/thumbnail.md`. Accent
      `#7dd3fc`, Rp title from public estimators (SocialCounts-high preferred), evidence
      screenshot background, export **1280×720**.
    - `series: freshgrad-ai-dev` → `styles/series/freshgrad-ai-dev/thumbnail.md`.
      Accent `#facc15`, host RIGHT / copy LEFT, export **1280×720**. Series title:
      **Kampus, AI, dan Masa Depan Anak IT** (15–20 min; saya/kalian + Teman-teman).
      Talking-head stays `style: tutorial` (Bold + MG `#7dd3fc`). Humble voice:
      concern + solutions, no “kampus primitive” / roasting lecturers / “kuliah
      percuma”. Prefer MG quote cards over third-party clips. Do not paste source
      YouTube transcripts into the teleprompter — rewrite the angle.
    Agents must not redesign per episode.
13. **Portrait social cut:** never mutate the confirmed long-form EDL/cover.
    After confirming the short strategy, write sibling `edit/social/edl.json` and
    `edit/social/cover.json`. Use `ae social . --studio` or `ae social .` for a
    separate 1080×1920 output with word-remapped karaoke captions. Run
    `ae social . --qa` before handoff.
    **Never full-cam in portrait:** cropping 16:9 to 9:16 keeps about a third of
    the width, so the host reads as an extreme zoom. `ae social` forces
    `screen_with_cam` on every keep (`styles/social/style.md`
    `social.force_screen_with_cam`); do not hand-author full-cam social ranges.
    Cam audio still comes from the PIP clip, and framing/punch events are inert
    on the stage — leave `events: []` unless an episode has no screen source.
    Top-anchored MG (chapter/chip/diagram) sits in the left band below the
    screen; keep it clear of the right-side PIP. Click/shutter only; no whoosh.

## Process

### TikTok / Reels / Shorts (`edit/social`)

1. Pick one marketing promise and 1–2 proof moments from `takes_packed.md`.
2. Propose the 30–60s radio-edit and **wait for confirmation**.
3. Write word-snapped `edit/social/edl.json` + source-time `cover.json`.
4. `ae social . --studio` for review, then `ae social .` to render.
5. `ae social . --qa` and inspect opening, proof, karaoke, and CTA frames.

### Evidence series (`style: evidence`) — start here

0. **Brief (pre-prod)** — `ae brief . --channel TheAIGRID`
   - Writes `edit/script.md` (A-roll teleprompter with `[[EVIDENCE:]]` cues),
     `edit/record.md`, `edit/research.json` (public estimators), `edit/evidence.plan.json`.
   - Title Rp prefers SocialCounts last-28d **high** (question-mark honesty in script).
1. **Gather evidence** — `ae evidence-gather .`
   - Framework captures **real** screenshots into `raw/evidence/` (Playwright).
   - Never AI-generate fake dashboards. Install once:
     `uv sync --extra evidence && uv run playwright install chromium`
2. **Record** — host reads `edit/script.md`; at each cue speak site name + number; save `raw/cam.mp4`
3. **Inventory** — `ae ingest .` → `edit/takes_packed.md`
4. **Propose** radio-edit → **wait for confirm** → `edit/edl.json` → `ae cut .`
5. **Evidence cover** — `ae evidence-suggest .` (plan + ASR) → confirm → `--apply`
6. **Overlays / SFX / compose** — as below (callout for estimator numbers)

### Default / tutorial path

1. **Inventory** — `ae ingest .` → `edit/takes_packed.md`
2. **Converse** — describe material; ask shaped questions
3. **Propose** radio-edit strategy (4–8 sentences) → **wait for confirm**
4. **Write** `edit/edl.json` (`sources` + `ranges[]` with `source`/`start`/`end`)
5. **Cut** — `ae cut .` → `edit/preview.mp4` (enhances cam VO first)
6. **Cover** (if `sources.screen` exists):
   - Run `ae cover-suggest .` → review `edit/cover.suggest.json`
   - Propose full-cam vs `screen_with_cam` ranges (formula below) → **wait for confirm**
   - Write `edit/cover.json` → `ae cover .`
6a. **Evidence** (if `style: evidence` and stills already in `raw/evidence/`):
   - Prefer the brief→gather path above; manual drops still OK
   - Run `ae evidence-suggest .` → review → confirm → `--apply`
6b. **Overlays (A-roll MG)** — chapter / emphasis / diagram / chip / callout:
   - Run `ae overlay-suggest .` → `edit/overlays.suggest.json` (includes `framing_events`)
    - Propose dense Bold-mist plan synced to cover + zoom/punch → **wait for confirm**
   - Write `cover.json` `overlays[]` + merge companion `framing` into `events[]`
     (source-time, word-snapped) → `ae cover .` / `ae compose .`
6c. **SFX (modern tech)** — typing / shutter / click under cam VO:
   - Run `ae sfx-suggest .` → `edit/sfx.suggest.json`
   - Couples shutter→punch/framing/cut snap, click→screen-enter/deixis, typing→screen demos
   - **No whoosh.** Confirm → `ae sfx-suggest . --apply` → `ae cover .` / compose
7. **Compose** — `ae compose . --studio` or render
8. **QA** — `ae qa .` inspect `edit/verify/` cut frames
9. **Iterate** — natural language; never re-transcribe casually

## EDL shape

```json
{
  "sources": { "cam": "../raw/cam.mp4" },
  "ranges": [
    { "source": "cam", "start": 12.4, "end": 18.1, "note": "hook" }
  ]
}
```

Paths in EDL are relative to `edit/`.

## Cover shape

```json
{
  "camera_play": {
    "snap_on_cuts": true,
    "home": "medium",
    "alt": "close",
    "wide_on_resets": true,
    "max_hold_sec": 16,
    "scales": { "wide": 1.0, "medium": 1.1, "close": 1.18 }
  },
  "events": [
    { "type": "framing", "start": 10.0, "end": 18.0, "framing": "close", "motion": "ease" },
    { "type": "punch_in", "start": 35.5, "end": 41.0, "scale": 1.12 },
    { "type": "screen_with_cam", "start": 14.0, "end": 42.0, "note": "demo UI" }
  ],
  "captions": []
}
```

### Overlay shape (`cover.json` → remapped in `timeline.overlays`)

```json
{
  "overlays": [
    {
      "kind": "chapter",
      "start": 12.0,
      "end": 15.5,
      "kicker": "Chapter 01",
      "text": "Extend kontak dengan Studio"
    },
    { "kind": "emphasis", "start": 40.0, "end": 41.4, "text": "Studio API" },
    {
      "kind": "diagram",
      "start": 88.0,
      "end": 94.0,
      "kicker": "Flow",
      "title": "Toko Material",
      "steps": ["res.partner fields", "Seed kategori", "Gambar produk", "Kartu stok"]
    },
    { "kind": "chip", "start": 0.0, "end": 2.8, "text": "Odoo Studio" }
  ]
}
```

Times are **cam source seconds**. `ae cover` / compose remaps through the EDL onto output `fromSec`.
Diagram `steps[]` reveal **sentence-paced** (not karaoke): `ae cover` aligns each step to
cam transcript phrases → timeline `stepAtSec` / `stepMotion: speech` (even stagger fallback).
Optional cover override: `stepStarts: [sourceSec, ...]`. Schedule enforces
`diagram_hold_after_last_sec` (~2.6s) + `exitStartSec` so lists do not vanish on the last beat;
structure collisions on the left rail are trimmed.

**Overlay ↔ camera_play (framework default in `ae overlay-suggest`):**

| Kind | Prefer cover | Framing on full-cam |
|------|----------------|---------------------|
| `chapter` / `diagram` | `screen_with_cam` (wide/hold already) | companion `framing` **medium** / **wide** |
| `chip` | either | companion **medium** |
| `emphasis` | either | close OK — no companion |

Safe zones stay `left_third` + `faceClear`. Suggest also scales density with keep length (~1 sting / 90s) and writes companion events as `framing_events` (merged into `cover.events` on `--apply`).

### Full cam vs screen + soft-float PIP

| Mode | Visual | Audio |
|------|--------|-------|
| Full me (default) | Cam + `camera_play` framing | Cam |
| `screen_with_cam` | Cool-mist canvas + cozy floated screen (soft round, full frame) + cam PIP at stage lower-right | Cam only |

**Formula** (also implemented by `ae cover-suggest`):

- Signal A: transcript deixis (`prefer_screen_when` — lihat, klik, UI, …)
- Signal B: screen frame-diff activity ≥ threshold
- Use PIP only when both make sense (deixis **or** sustained activity, **and** activity in window), hold ≥ 2.5s
- Do not invent screen ranges with neither signal

Framing presets simulate a 2–3 camera setup from one cam. Propose a camera-play plan from the transcript before writing `cover.json`. On screen ranges, skip framing zooms.

**Screen explainer (locked in `styles/tutorial`):** cozy + cool mist + soft round (`borderRadiusPx: 24`) + `crop.mode: none`. Host supplies clean full-frame screen; do not run smart window detect. Optional static `crop.inset` only for tiny capture-edge trash. PIP anchors to the **frame** lower-right.

### Overlay motion (Remotion, no extra cover fields)

Tutorial talking-head keeps the host on camera. Do **not** author `cover.cutaways[]`
or run `ae cutaway-suggest` — picture-takeover MG reads as fake B-roll and fights
the A-roll. Put the extra motion on existing overlays instead:

| Kind | Motion |
|------|--------|
| `chapter` | kicker pop + accent line draws under the title |
| `emphasis` | last-word pop; numbers count up; underline draws; strike only on `tidak` / `no` / `off` / `deny` |
| `diagram` | rail + token in the gutter **right of the index** (never through glyphs); each step pops + short connector |
| `chip` | accent dot scale-pop |
| `callout` | value counts (Rp / dotted thousands) + underline |

Same locked look: white ink, no panel, no accent color — see rule 10. No whoosh.
Do not invent a new overlay kind for this.

### Generated MG cutaways — do not use (tutorial)

`cover.cutaways[]` is leftover picture-takeover machinery. Leave it empty. If an
old episode still has entries, delete the array and rebuild with `ae cover .`.

## Promote

Append to `edit/promotions.md`, then patch framework packages and re-preview.
Run `ae promote-check .` to list pending notes.
