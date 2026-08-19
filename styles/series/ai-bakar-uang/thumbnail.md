# Thumbnail — AI Bakar Triliunan

**Locked.** Do not invent a new YouTube thumbnail layout for this video.
Export **exactly 1280×720** (16:9). Never ship 3:2. Standalone video —
no part badge, no "part depan" copy anywhere on the thumbnail.

```yaml
video:
  id: ai-bakar-uang
  title: "AI Bakar Triliunan, Tapi Masih Butuh Kita. Kenapa?"
  channel_use: YouTube thumbnail
output:
  width: 1280
  height: 720
  aspect: "16:9"
  post:
    crop: "iw:iw*9/16:0:(ih-iw*9/16)/2"
    scale: "1280:720"
layout:
  # Host RIGHT (talking-head), copy LEFT — same grammar as ai-youtube-idr / odoo series
  host:
    side: right
    framing: shoulders_up
    expression: confident_calm     # reassuring, not shocked/clickbait-scared
  background:
    kind: evidence_screenshot      # real earnings-call / press / hiring-post still
    treatment: darken_blur
    source: episode raw/evidence still matching the featured claim/number
  copy:
    zone: left_two_thirds
    stack: [title_lines, payoff_line, chips]
  title:
    font: bold_condensed_sans
    case: upper
    lines: 2
    colors:
      line_a: "#ffffff"            # e.g. AI BAKAR TRILIUNAN
      line_b: accent               # e.g. TAPI KOK MASIH DIREKRUT?
  payoff:
    text_example: "INI DATANYA"
    color: "#ffffff"
    size: smaller_than_title
    position: under_title
  chips:
    count: 3
    row: bottom_left
    shape: dark_pill
    border: accent
    # Typical: REAL DATA | BUKAN HOPIUM | SUMBER DI VIDEO
colors:
  accent: "#7dd3fc"                # cool mist — match evidence/tutorial MG
  ink: "#ffffff"
  chip_fill: "#1a222c"
  bg_wash: dark_desaturated
title_number_rules:
  # Use verified primary/press sources — never invent a dollar figure.
  preferred_source: primary_earnings_or_press_report
  currency: idr_primary            # lead with IDR; USD as secondary/small text
  show_conversion: true            # e.g. "$700B ≈ Rp12.460T" — kurs date in callout
  show_question_mark: true
  explain_range_in_video: true     # callouts: source + date on screen
forbidden:
  - AI-generated fake analytics/charts as thumb background
  - flat solid background with no evidence screenshot
  - host on left / title over face
  - fear-face / shocked expression (video tone is calm, not doomer-bait)
  - aspect ratios other than 16:9
  - part badge / "part depan" copy — this is a standalone video
final:
  title: ["AI BAKAR TRILIUNAN", "TAPI BUTUH KITA?"]
  payoff: "INI DATANYA"
  chips: ["REAL DATA", "BUKAN HOPIUM", "SUMBER DI VIDEO"]
