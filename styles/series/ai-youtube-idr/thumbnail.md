# Series thumbnail — AI + YouTube IDR

**Locked.** Do not invent a new YouTube thumbnail layout for this series.
Export **exactly 1280×720** (16:9). Never ship 3:2.

```yaml
series:
  id: ai-youtube-idr
  title: "AI + YouTube = RpXX Juta/Bulan?"
  channel_use: YouTube thumbnail
output:
  width: 1280
  height: 720
  aspect: "16:9"
  post:
    crop: "iw:iw*9/16:0:(ih-iw*9/16)/2"
    scale: "1280:720"
layout:
  # Host RIGHT (talking-head), copy LEFT — same grammar as odoo series
  host:
    side: right
    framing: shoulders_up
    expression: slight_smile
  background:
    kind: evidence_screenshot      # real SocialCounts/vidIQ/YouTube still
    treatment: darken_blur
    source: episode raw/evidence still matching the featured channel
  copy:
    zone: left_two_thirds
    stack: [part_badge, title_lines, payoff_line, chips]
  part_badge:
    shape: rounded_rect
    fill: accent
    text: "PART {n}"
    position: top_left
  title:
    font: bold_condensed_sans
    case: upper
    lines: 2
    colors:
      line_a: "#ffffff"            # e.g. AI + YOUTUBE
      line_b: accent               # e.g. RP24 JUTA?
  payoff:
    text_example: "BEDAH THEAIGRID"
    color: "#ffffff"
    size: smaller_than_title
    position: under_title
  chips:
    count: 3
    row: bottom_left
    shape: dark_pill
    border: accent
    # Typical: FREE TOOLS | REAL ESTIMATE | FACELESS FORMAT
colors:
  accent: "#7dd3fc"                # cool mist — match evidence/tutorial MG
  ink: "#ffffff"
  chip_fill: "#1a222c"
  bg_wash: dark_desaturated
title_number_rules:
  # Use public estimator sites — never invent income.
  preferred_source: socialcounts_last_28d_high
  show_question_mark: true
  explain_range_in_video: true     # callouts: SocialCounts low–high + vidIQ
forbidden:
  - AI-generated fake analytics dashboards as thumb background
  - flat solid background with no evidence UI
  - host on left / title over face
  - purple / cream / newspaper looks
  - aspect ratios other than 16:9
parts:
  1:
    badge: "PART 1"
    title: ["AI + YOUTUBE", "RP24 JUTA?"]
    payoff: "BEDAH THEAIGRID"
    chips: ["FREE TOOLS", "REAL ESTIMATE", "SOCIALCOUNTS"]
```
