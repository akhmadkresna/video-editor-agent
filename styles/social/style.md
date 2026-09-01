# Social portrait style pack

Reusable 9:16 marketing cut. This profile is intentionally separate from the
long-form `tutorial` style: tutorial captions stay off; social uses karaoke.

## Zone map — Option A letterbox (1080×1920)

True **16:9 stage** centered in the portrait frame with black bars:

1. **Top black** (~0–34%) — MG stings (chapter / callout / emphasis / chip)
2. **Landscape stage** (~34–66%) — screen 16:9 + cam PIP bottom-left + blinking CTA on the stage
3. **Bottom black** (~66–100%) — karaoke captions

```yaml
social:
  # Portrait full-cam crops too hard; every keep uses the letterbox stage.
  force_screen_with_cam: true
  # Blinking CTA sits ON the 16:9 stage (not in the black bars).
  cta:
    enabled: true
    text: Full video di YouTube
    blink: true
    blinkPeriodSec: 1.2
    anchor: band_top_center
    bandTopCqh: 3.2
    sizeCqh: 2.0
captions:
  style: karaoke
  accent: "#7dd3fc"
  # Centered in the bottom black letterbox bar.
  safeBottomRatio: 0.17
overlays:
  preset: open_overlay
  treatment: bold
  ink: "#ffffff"
  dim: "rgba(255,255,255,0.58)"
  dwell:
    chip_sec: 3.2
    chapter_sec: 4.0
    diagram_sec: 6.5
    emphasis_sec: 2.2
    min_sec: 1.6
    exit_sec: 0.6
  fonts:
    display: Syne
    ui: Instrument Sans
  # All MG lives in the top black bar.
  chapter:
    kickerSizeCqh: 1.4
    titleSizeCqh: 4.2
    leftCqw: 5
    topCqh: 10
    maxWidthCqw: 90
  emphasis:
    sizeCqh: 5.2
    leftCqw: 5
    topCqh: 12
    maxWidthCqw: 90
    underline: true
  callout:
    leftCqw: 5
    topCqh: 10
    valueSizeCqh: 5.6
    sourceSizeCqh: 1.6
    maxWidthCqw: 90
  diagram:
    leftCqw: 5
    topCqh: 8
    maxWidthCqw: 90
    stepSizeCqh: 2.2
  chip:
    leftCqw: 5
    topCqh: 14
    sizeCqh: 2.0
  safe:
    faceClear: true
    zones: [top, middle, lower_safe]
sfx:
  enabled: true
  no_whoosh: true
  pack: assets/sfx
  volumes:
    typing: 0.34
    shutter: 0.48
    click: 0.34
    paper: 0.32
    tick: 0.26
  typing:
    enabled: false
  shutter:
    max_sec: 0.22
  click:
    max_sec: 0.22
screen_explainer:
  preset: social_letterbox
  canvas:
    background: "#000000"
    backgroundDeep: "#000000"
    gradient: none
  screen:
    presentation: letterbox_landscape
    widthRatio: 1.0
    borderRadiusPx: 0
    objectFit: cover
    crop:
      mode: none
  pip:
    # Bottom-left of the 16:9 stage (not the full 9:16 frame).
    anchor: band_lower_left
    widthRatio: 0.22
    aspectRatio: "4:5"
    insetLeftRatio: 0.02
    insetBottomRatio: 0.03
    borderRadiusPx: 14
    border: none
    objectFit: cover
    objectPosition: "center 28%"
```

## Safe layout

- 1080×1920, 30 fps.
- Every beat uses screen + cam on the letterbox stage. Full cam is never used in
  portrait because the 16:9 crop zooms the host past a usable framing.
- MG stays in the top black bar; karaoke in the bottom black bar; CTA pulses on
  the landscape stage; cam PIP is bottom-left of that stage.
- Use click/shutter one-shots only. No whoosh.
