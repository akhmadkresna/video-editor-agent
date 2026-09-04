# Tutorial style pack

Defaults for tech talking-head + screen recordings.

**Locked A-roll MG (2026-08+, "Open Overlay" v7+ middle-ground):** one look for
every overlay kind — white ink straight on the a-roll, **no panel, no accent
color**. Readability comes from a darker scrim (`OverlayLayer`'s zone-aware
veil) behind the text. **Surround OK** (left / right / above / below the
speaker); **face oval stays clear**. Moderate size hierarchy (hero ~22cqh,
body ~9, meta ~3.4) and density cap (**one primary + optional one secondary**).
Motion recipes: punch, stagger-rise, slide-in, count — snappy support, not
poster collage. Do not invent episode-local forks; promote changes here.

Kinds: `title` · `stat` · `lower_third` · `tag` · `divider` · `quote` · `code` ·
`illustration` · `chapter` · `emphasis` · `diagram` · `callout` · `chip` — all
13 share this one treatment now (the first 8 dispatch to
`packages/remotion-kit/src/components/glass/GlassOverlays.tsx`; the last 5 to
`OverlayLayer.tsx`'s own `OneOverlay` — different components per kind's
structure, same palette). Tokens in `glass/tokens.ts`. `code` stays a real
terminal window — a screen convention, not part of the panel-removal, so it
was never affected. Author cover.json `overlays[]` the same way as before
(`start`/`end` cam-source seconds, word-snapped); optional `zone` =
`left_third` | `right_third` | `lower_raised` | `top_sparse` (suggest rotates
these). The Python remap (`ae cover`) passes `text` / `title` / `kicker` /
`steps` / `value` / `sourceLabel` / `note` / `tone` / `accent` / `zone`
through unchanged (`tone` and the per-overlay `accent` are data fields, not
style colors — see field mapping below). Field mapping:

| Kind | Fields used |
|------|-------------|
| `title` | `text` (headline) + optional `kicker`, `accent` (2nd-color headline continuation), `steps` (tag row). No `kicker`/`accent` → renders as the design's outro/subscribe layout (wordmark + `text` line + tags) instead of a hero headline. |
| `stat` | `value` (big number, **counts up from 0**) + `sourceLabel` + optional `title` (descriptor line) + `tone` (teal/amber — dashed vs solid badge border) |
| `lower_third` | `text` (name) + `title` (role) + `steps` (tag row, tone-cycled) — renders as a full-width bottom band, not a floating card |
| `tag` | `text` (standalone floating chip) + optional `tone` |
| `divider` | `kicker` ("CHAPTER 01" — a trailing 2-digit number renders as an oversized ghost numeral) + `title` (heading) |
| `quote` | `text` (quote body) + `kicker` (attribution) |
| `code` | `steps` (code lines) + `kicker` (label) + optional `title` (filename, e.g. "query.sql") |
| `illustration` | `title` (heading) + `steps` (labels/values) + `note: "illustration:<id>"` where id is one of `dual_timeline` / `scale_compare` / `spec_gap` / `car_no_map` / `compass` / `load_test` / `stadium_ticket` |

`tone` is `"teal" | "amber" | "neutral"` — amber renders the `stat` mono
badge with a dashed border (caution/estimate), teal/neutral render solid
(sourced/plain). It's a border style, not a color — color is reserved for
the white text-selection highlight only.

**Motion (middle-ground recipes):** title/divider/emphasis **punch** in (scale
0.94→1, fade) over ~220ms, then hard/near-hard cut on exit. Titles/quotes may
**stagger-rise** words (60–90ms). Stat numbers **count** up ~300ms with punch
ease; label fades in after. Chips/lower third **slide in** ~12px + fade over
~180ms. Hold until the beat is read (~1.5–2.5s single sting, ~3s denser) —
don't hold static MG once nothing is moving.

The `chapter` / `emphasis` / `diagram` / `chip` / `callout` kinds (config
below) render through `OverlayLayer`'s own `OneOverlay`, not
`GlassOverlays.tsx` — a different component per kind's structure, but the
same white-ink/no-panel/scrim treatment as the 8 kinds above. Either group
is fine to author; there's no "legacy" vs "current" split anymore.

```yaml
captions:
  style: off                   # no full/karaoke dialogue captions — use overlays.emphasis
# Cam VO: DeepFilterNet 3 official CLI (v0.5.6). Raw stays read-only.
# Cache: edit/audio/cam.voice.wav. Opt out per episode: voice_enhance.enabled: false
voice_enhance:
  enabled: true
  backend: deepfilternet
  atten_lim_db: 12
  compensate_delay: true
  sample_rate: 48000
  sources: [cam]
# Locked A-roll overlay presentation (Remotion), Open Overlay v7+ middle-ground —
# white ink, no panel, surround zones, moderate hierarchy, density capped.
overlays:
  # A-Roll Text Motion System. Common tokens (fonts / sizeBands / type /
  # motion / shape / grid) come from DEFAULT_OVERLAYS — see
  # styles/aroll-text-motion/overlays.style.yaml. This pack only overrides
  # timing (dwell) + per-kind placement.
  preset: aroll_text_motion
  treatment: bold
  ink: "#ffffff"
  dwell:
    chip_sec: 4.0
    chapter_sec: 5.5
    diagram_sec: 10.0
    emphasis_sec: 2.4
    min_sec: 1.8
    diagram_hold_after_last_sec: 2.6   # keep full list readable after last step
    diagram_sec_per_step: 1.45
    diagram_search_pad_sec: 8.0        # speech search may look past short cover windows
    exit_sec: 0.9
  density:
    maxPrimary: 1
    maxSecondary: 1
  chapter:
    kickerSizeCqh: 2.4
    titleSizeCqh: 12
    leftCqw: 4.5
    topCqh: 12
    maxWidthCqw: 42
  emphasis:
    sizeCqh: 22
    leftCqw: 4.5
    bottomCqh: 28             # raised — was too low vs face/PIP
    maxWidthCqw: 48
    underline: true
  diagram:
    leftCqw: 4.5
    topCqh: 10
    maxWidthCqw: 40
    stepSizeCqh: 3.6
  chip:
    leftCqw: 4.5
    topCqh: 10
    sizeCqh: 3.4
  safe:
    faceClear: true            # face oval clear; surround margins OK
    zones: [left_third, right_third, lower_raised, top_sparse]
  # Framework default (ae overlay-suggest): denser MG + punch coupling
  # - ~1 sting / 28s keep (≥30 overlays on ~15 min); chapter gap ~42s; emphasis gap ~8s
  # - quiet keep stretches >28s get gap-fill emphasis (iterates to target_total)
  # - thin payoff lexicon → speech-stride emphasis (~24s keep) from local words
  # - punch_in (in EDL) without nearby MG gets a forced emphasis sting
  # - chapter/diagram: prefer screen_with_cam; else framing medium/wide
  # - emphasis: close OK; ID payoff + screen-enter + punch score
  # - zone rotates around speaker (not left-rail only)
punch_in:
  scale: 1.28
  defaultDurationSec: 1.35
# Modern-tech SFX under cam VO (ae sfx-suggest). No whoosh.
# Default: one-shots only (shutter/click). Typing holds are off — too long on demos.
sfx:
  enabled: true
  no_whoosh: true
  pack: assets/sfx
  volumes:
    typing: 0.38
    shutter: 0.48
    click: 0.32
    paper: 0.35
    tick: 0.28
  density:
    sec_per_sfx: 30
    min_gap_sec: 1.2
    shutter_click_min_gap_sec: 0.4
    typing_merge_gap_sec: 1.5
  typing:
    enabled: false
    min_hold_sec: 4.0
    tile_sec: 1.2
  shutter:
    max_sec: 0.22
  click:
    max_sec: 0.22
  mg:
    enabled: true
    chapter: shutter
    diagram: shutter
    emphasis: click
    chip: click
# Fake multicam defaults (ae cover / example_cover). Close must read as cam B.
camera_play:
  snap_on_cuts: true
  home: medium
  alt: close
  wide_on_resets: true
  max_hold_sec: 7
  scales:
    wide: 1.0
    medium: 1.22
    close: 1.42
# Smart radio-edit (ae edl-suggest): clause + gap-class — NOT silence packing.
# breath stays; think hard-cuts; long AI waits compress to a short hold beat.
radio_edit:
  breath_max_sec: 0.6
  wait_min_sec: 5.0         # gaps ≥ this → AI wait compress
  activity_wait_min_sec: 3.5
  hold_sec: 0.4             # visible beat (hold_tail survives word-snap)
  min_keep_sec: 0.90
  pad_before_sec: 0.08
  pad_after_sec: 0.12
  cut_repeats: true
  repeat_similarity: 0.75
  repeat_window_sec: 90
  cut_wait_speech: true
  wait_speech_max_sec: 0.9
  # legacy aliases (mapped to wait_min if new keys absent)
  silence_gap_sec: 0.60
  gap_cut_sec: 5.0
  hold_if_gap_sec: 5.0
cover:
  # Show screen when possible (tutorial default). Use mode: balanced for stricter gates.
  mode: prefer_screen
  screen_bias: 0.35
  require_activity_for_deixis: false
  prefer_screen_when:
    - look at
    - look here
    - here
    - this
    - click
    - klik
    - lihat
    - di sini
    - disini
    - UI
    - dashboard
    - screen
    - menu
    - button
    - form
    - field
    - error
    - cursor
    - code
    - terminal
  jump_cut_cover: punch_in
  min_hold_sec: 2.0
  min_active_sec: 1.0
  activity_fps: 2
  activity_threshold: 0.028
  merge_gap_sec: 1.2
  off_hold_sec: 1.5
  pad_before_sec: 0.5
  pad_after_sec: 1.5
# Locked screen-explainer presentation (Remotion). Do not invent episode-local forks.
screen_explainer:
  preset: cozy
  canvas:
    background: "#d9e2ec"       # cool mist
    backgroundDeep: "#c4d0dc"
    gradient: radial
  screen:
    presentation: float_centered
    widthRatio: 0.78            # cozy
    maxHeightRatio: 0.82
    borderRadiusPx: 24          # soft round
    shadow: soft_float
    objectFit: fill             # card sized to screen.mp4 AR — no distort/crop
    crop:
      mode: none               # no smart_window_detect — supply clean screen raw
  pip:
    anchor: stage_lower_right   # frame corner — not nested inside screen
    widthRatio: 0.18
    aspectRatio: "5:6"          # near-square, rounded (2026-08+; was 4:5/14px)
    insetRightRatio: 0.035
    insetBottomRatio: 0.045
    borderRadiusPx: 26
    border: none
    objectFit: cover
    objectPosition: "center 28%"
```

## Cover modes

| Mode | When | Visual | Audio |
|------|------|--------|-------|
| Full cam | Default / no screen activity | Cam + `camera_play` framing | Cam |
| Screen + soft-float PIP | Deixis keywords **and** screen activity (see `ae cover-suggest`) | Cool-mist canvas, **cozy** floated screen (soft round, full frame) + cam PIP at **stage lower-right** | Cam only |

Agents must load these defaults when `project.yaml` has `style: tutorial` (framework default).

| Layer | Locked look |
|-------|-------------|
| A-roll MG — all 13 kinds (title / stat / lower_third / tag / divider / quote / code / illustration / chapter / emphasis / diagram / callout / chip) | `open_overlay` middle-ground — white ink, no panel, surround zones (face oval clear), moderate size hierarchy, density 1+1, zone-aware veil. `code` alone stays a real terminal window. |
| Screen + PIP stage | Cool-mist canvas `#d9e2ec` + cozy float (soft round, no smart crop) |

Run `ae cover-suggest .` after the EDL is confirmed when a `screen` source exists.
Supply **clean** full-frame screen footage. Float card uses **screen.mp4 aspect
ratio**, soft `borderRadiusPx`, and centers inside the cozy max box — scale to
fit, never distort or smart-crop. Do not fork overlay colors/fonts per episode —
promote changes into this style pack.

**Draft review:** use `ae draft . --seconds 120 --render` (fromSec-safe slice + quality gates).
Do **not** hand-trim `remotion-props.json` by `start`/`end` — overlays use `fromSec`/`durationSec`
and will silently disappear (no opening chip).
