# Evidence style pack

Talking-head **plus** real website/YouTube evidence stills (screenshots — never AI-generated dashboards).

Starts from the tutorial locked look ("Open Overlay" v7 — white ink, no panel,
no accent color). Do not invent episode-local forks. Use when `project.yaml`
has `style: evidence`. Keep `style: tutorial` as the house default for
Odoo/screen demos.

```yaml
captions:
  style: off
overlays:
  # A-Roll Text Motion System — common tokens from DEFAULT_OVERLAYS
  # (styles/aroll-text-motion/overlays.style.yaml). Overrides below only.
  preset: aroll_text_motion
  treatment: bold
  ink: "#ffffff"
  dwell:
    chip_sec: 4.0
    chapter_sec: 5.5
    diagram_sec: 12.0          # longer for free-stack / estimator flows
    emphasis_sec: 2.4
    callout_sec: 3.6           # big number + source label
    min_sec: 1.8
    diagram_hold_after_last_sec: 3.0
    diagram_sec_per_step: 1.55
    diagram_search_pad_sec: 8.0
    exit_sec: 0.9
  chapter:
    kickerSizeCqh: 2.4
    titleSizeCqh: 12
    leftCqw: 4.5
    topCqh: 12
    maxWidthCqw: 42
  emphasis:
    sizeCqh: 22
    leftCqw: 4.5
    bottomCqh: 28
    maxWidthCqw: 48
    underline: true
  diagram:
    leftCqw: 4.5
    topCqh: 10
    maxWidthCqw: 40
    stepSizeCqh: 3.6
  callout:
    leftCqw: 4.5
    bottomCqh: 22
    valueSizeCqh: 18
    sourceSizeCqh: 2.8
    maxWidthCqw: 48
  chip:
    leftCqw: 4.5
    topCqh: 10
    sizeCqh: 3.4
  safe:
    faceClear: true
    zones: [left_third, right_third, lower_raised, top_sparse]
punch_in:
  scale: 1.28
  defaultDurationSec: 1.35
sfx:
  enabled: true
  no_whoosh: true
  pack: assets/sfx              # shared framework pack (all styles)
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
  paper:
    max_sec: 0.45
  tick:
    max_sec: 0.15
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
    callout: shutter
    # Kinds that used to carry a paper card — a page-turn still reads well
    # as their appear cue even after the card was dropped (v7, no panel);
    # tag is a small chip, gets a lighter tick instead.
    title: paper
    stat: paper
    lower_third: paper
    divider: paper
    quote: paper
    illustration: paper
    code: paper
    tag: tick
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
radio_edit:
  breath_max_sec: 0.6
  wait_min_sec: 5.0
  activity_wait_min_sec: 3.5
  hold_sec: 0.4
  min_keep_sec: 0.90
  pad_before_sec: 0.08
  pad_after_sec: 0.12
  cut_repeats: true
  repeat_similarity: 0.75
  repeat_window_sec: 90
  cut_wait_speech: true
  wait_speech_max_sec: 0.9
  silence_gap_sec: 0.60
  gap_cut_sec: 5.0
  hold_if_gap_sec: 5.0
cover:
  # Evidence episodes: stills from raw/evidence/; screen demos optional.
  mode: prefer_evidence
  screen_bias: 0.25
  require_activity_for_deixis: false
  prefer_evidence_when:
    - socialcounts
    - social counts
    - vidiq
    - socialblade
    - estimasi
    - estimate
    - earnings
    - rpm
    - cpm
    - subscriber
    - subscribers
    - views
    - pendapatan
    - juta
    - screenshot
    - website
    - dashboard
  prefer_screen_when:
    - look at
    - look here
    - click
    - klik
    - lihat
    - UI
    - menu
    - button
    - form
    - code
    - terminal
  jump_cut_cover: punch_in
  min_hold_sec: 2.5
  min_active_sec: 1.0
  merge_gap_sec: 1.2
  pad_before_sec: 0.4
  pad_after_sec: 1.2
  evidence:
    dir: raw/evidence
    default_layout: float          # float | full
    default_pip: true              # cam PIP over still (talking-head stays)
    min_hold_sec: 2.5
screen_explainer:
  preset: cozy
  canvas:
    background: "#d9e2ec"
    backgroundDeep: "#c4d0dc"
    gradient: radial
  screen:
    presentation: float_centered
    widthRatio: 0.78
    maxHeightRatio: 0.82
    borderRadiusPx: 24
    shadow: soft_float
    objectFit: contain             # evidence screenshots: show full page
    crop:
      mode: none
  pip:
    anchor: stage_lower_right
    widthRatio: 0.18
    aspectRatio: "4:5"
    insetRightRatio: 0.035
    insetBottomRatio: 0.045
    borderRadiusPx: 14
    border: none
    objectFit: cover
    objectPosition: "center 28%"
```

## Cover modes (evidence)

| Mode | Visual | Audio |
|------|--------|-------|
| Full cam | Cam + `camera_play` | Cam |
| `evidence` / `evidence_with_cam` | Cool-mist canvas + floated/full still from `raw/evidence/` (+ optional cam PIP) | Cam |
| `screen_with_cam` | Same as tutorial (optional demos) | Cam |

## Hard rules

1. Evidence assets must be **real captures** of public pages (SocialCounts, vidIQ, YouTube, etc.). No AI-generated fake dashboards.
2. Keep provenance in `edit/evidence.json` (`src`, `url`, `captured_at`, `note`).
3. Title Rp numbers: prefer conservative public-estimator highs (e.g. SocialCounts last-28d high); show the full range on-screen with source labels via `callout` overlays.
4. Do not change [`styles/tutorial/`](../tutorial/) for this series — promote evidence-only knobs here.
