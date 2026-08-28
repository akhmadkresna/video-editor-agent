# `ae` pipeline reference

Invoke as `uv run --project "$AGENTIC_EDITOR_HOME" ae <args>` (PATH-independent);
`ae <args>` alone needs the framework venv on PATH. Most commands run from inside
an **episode** folder (`project.yaml` + `raw/` + `edit/`); `.` = the episode.
`ae new <path>` and `ae doctor` are the exceptions — they run from anywhere.

## Command map

| Command | Does | Needs | Writes |
|---|---|---|---|
| `ae doctor` | Check ffmpeg/ffprobe, ASR backend, Remotion kit | — | — |
| `ae new <path>` | Scaffold an episode (only valid way to create the tree) | — | `project.yaml`, `raw/`, `edit/`, agent config |
| `ae ingest .` | Probe + ASR (whisper.cpp on macOS, faster-whisper else) | `raw/cam.mp4` | `edit/takes_packed.md`, cached transcript |
| `ae edl-suggest .` | Gap-class radio-edit proposal | transcript | `edit/edl.suggest.json` |
| `ae storyboard .` | Visual HTML review of EDL plan (keep ranges + cut gaps) | `edit/edl.suggest.json` or `edit/edl.json` | `edit/storyboard/index.html` |
| `ae edl-suggest . --apply` | Promote proposal to runtime EDL (**after user confirm**) | `edit/edl.suggest.json` | `edit/edl.json` |
| `ae cut .` | Render EDL → preview; enhances cam VO (DeepFilterNet) first; 30 ms fades | `edit/edl.json` | `edit/preview.mp4`, `edit/audio/cam.voice.wav` |
| `ae cover-suggest .` | Propose `screen_with_cam` ranges from deixis + screen activity | transcript, `screen` source | `edit/cover.suggest.json` |
| `ae cover .` | Merge EDL + `edit/cover.json` → timeline | `edit/edl.json`, `edit/cover.json` | `edit/timeline.json` |
| `ae compose . --studio` | Stage media into `public/ae-media`, launch Remotion Studio | `edit/timeline.json` | — |
| `ae compose .` | Headless Remotion render | `edit/timeline.json` | `edit/final.mp4` |
| `ae qa .` | Extract cut-boundary frames | `edit/preview.mp4` | `edit/verify/` |
| `ae mezzanine .` | CRF16 1080p proxies for heavy raw (muxes enhanced audio) | sources | `edit/mezzanine/` |
| `ae promote-check .` | Show `edit/promotions.md` | — | — |

## `ae edl-suggest` flags worth knowing

| Flag | Effect |
|---|---|
| `--gap-cut <sec>` | Cut silences ≥ this (default from style `radio_edit`) |
| `--hold-if-gap <sec>` | Gaps ≥ this keep a short hold beat (AI-wait feel) instead of a full cut |
| `--hold <sec>` | Duration of that hold beat |
| `--min-keep <sec>` | Drop keep ranges shorter than this |
| `--source-start / --source-end <sec>` | Only consider this window of the source |
| `--apply` | Write `edit/edl.json` (still review the suggest file first) |

Adjustments in plain language → flags:
- "lebih rapat / lebih agresif" → lower `--gap-cut`, lower `--min-keep`
- "jangan buru-buru motong" / "sisakan jeda mikir" → raise `--gap-cut`, add `--hold-if-gap`
- "cuma bagian tengah" → `--source-start` / `--source-end`
- "storyboard" / "show me storyboard" / "tampilin storyboard" / "visualize the plan" → `ae storyboard .` (run `ae edl-suggest .` first if no plan file yet)

## `edit/edl.suggest.json` shape

```json
{
  "sources": { "cam": "../raw/cam.mp4" },
  "ranges": [
    { "source": "cam", "start": 12.40, "end": 18.10, "note": "hook" }
  ],
  "_meta": {
    "keep_sec": 820.4,
    "gap_classes": { "breath": 40, "think": 31, "ai_wait": 3, "retake": 9 },
    "dropped_repeat": 9,
    "strategy": "gap-class"
  }
}
```

Report `len(ranges)`, `_meta.keep_sec` vs source duration (from `ae ingest`
output or `ffprobe`), and every `gap_classes` count.

## shownotes (`edit/shownotes.md`)

No dedicated command — read `edit/takes_packed.md` (packed transcript with
timestamps) and write `edit/shownotes.md` yourself:

- **5 title options**, ≤ 70 chars each, honest, no ALL CAPS
- **Description**, 3–4 short paragraphs: what the video shows, who it is for,
  tools used, one-line CTA
- **Chapters**: `mm:ss — label`, one per real topic shift, first at `00:00`,
  labels ≤ 40 chars
- **Tags**: 10–15, comma-separated

Match the episode's language (default Indonesian).

## Scheduling (Hermes Routines)

A routine that runs unattended must stop at the confirm gate. Use:

```
/video-editor ingest ~/episodes/current and propose a radio-edit,
then stop and leave the summary for me — do not apply
```

That produces `edit/edl.suggest.json` + a summary message; a human runs the
apply step later.
