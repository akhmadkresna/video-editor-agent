# Thumbnail — 69% Skill AI

**Locked.** Do not invent a new YouTube thumbnail layout for this video.
Export **exactly 1280×720** (16:9). Standalone video — no part badge.

```yaml
video:
  id: ai-skill-hiring
  title: "69% HRD Nggak Mau Rekrut Tanpa Skill AI. Skill Apa Itu Sebenarnya?"
  channel_use: YouTube thumbnail
output:
  width: 1280
  height: 720
  aspect: "16:9"
  post:
    crop: "iw:iw*9/16:0:(ih-iw*9/16)/2"
    scale: "1280:720"
layout:
  host:
    side: right
    framing: shoulders_up
    expression: curious_calm       # puzzled but grounded, not fear-bait
  background:
    kind: evidence_screenshot    # Microsoft WTI 69% or job-post still
    treatment: darken_blur
    source: episode raw/evidence still matching the featured claim
  copy:
    zone: left_two_thirds
    stack: [title_lines, payoff_line, chips]
  title:
    font: bold_condensed_sans
    case: upper
    lines: 2
    colors:
      line_a: "#ffffff"            # e.g. 69% WAJIB SKILL AI
      line_b: accent               # e.g. SKILL APA ITU?
  payoff:
    text_example: "CEK LOWONGANNYA"
    color: "#ffffff"
    size: smaller_than_title
    position: under_title
  chips:
    count: 3
    row: bottom_left
    shape: dark_pill
    border: accent
colors:
  accent: "#7dd3fc"
  ink: "#ffffff"
  chip_fill: "#1a222c"
  bg_wash: dark_desaturated
title_number_rules:
  lead_stat: "69%"
  secondary_stat: "76%"
  show_question_mark: true
  explain_in_video: true
forbidden:
  - AI-generated fake analytics/charts as thumb background
  - flat solid background with no evidence screenshot
  - host on left / title over face
  - fear-face / shocked expression
  - aspect ratios other than 16:9
  - part badge / "part depan" copy
final:
  title: ["69% WAJIB SKILL AI", "SKILL APA ITU?"]
  payoff: "CEK LOWONGANNYA"
  chips: ["REAL DATA", "BUKAN HOPIUM", "SUMBER DI VIDEO"]
