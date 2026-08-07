# Series thumbnail — Odoo Studio Agentic AI

**Locked.** Do not invent a new YouTube thumbnail layout for this series.
Match `refs/part1-canonical.png` / `refs/part2-canonical.png` (exact **1280×720**, 16:9).

```yaml
series:
  id: odoo-studio-agentic-ai
  title: Odoo Studio Agentic AI
  channel_use: YouTube thumbnail
output:
  width: 1280
  height: 720
  aspect: "16:9"
  # Never ship 3:2 (e.g. 1536×1024) — YouTube pillarboxes black L/R.
  # If a generator returns non-16:9: center-crop height to iw*9/16, then scale 1280×720.
  post:
    crop: "iw:iw*9/16:0:(ih-iw*9/16)/2"
    scale: "1280:720"
layout:
  # Rule of thirds — host RIGHT, copy + chips LEFT
  host:
    side: right
    framing: shoulders_up          # chest/shoulders, not full torso
    wardrobe: beige_crew_tee       # lock: kresna-studio2 look
    expression: slight_smile
    rim_light: warm_on_camera_left # host's right shoulder
    # Portrait refs (machine-local, not in repo):
    #   D:\AI\Media\kresna-studio2.png  (preferred)
    #   D:\AI\Media\kresna-studio.png
  background:
    kind: odoo_ui_screenshot
    treatment: darken_blur         # readable copy; UI still recognizable
    source: episode screen still or Studio/list UI matching the part topic
  copy:
    zone: left_two_thirds
    stack: [part_badge, title_lines, payoff_line, chips]
  part_badge:
    shape: rounded_rect
    fill: accent
    text: "PART {n}"               # white, bold sans, all caps
    position: top_left
  title:
    font: bold_condensed_sans      # Impact / Bebas-like weight
    case: upper
    lines: 2                       # usually
    colors:
      line_a: "#ffffff"            # e.g. AGENTIC AI / BUILD
      line_b: accent               # e.g. ODOO STUDIO / ODOO
  payoff:
    text_example: "1 FREE APP"
    color: "#ffffff"
    size: smaller_than_title
    position: under_title
  chips:
    count: 3
    row: bottom_left
    shape: dark_pill
    border: accent
    icon: accent_or_white
    label: white_sans
    # Swap labels per part — keep count=3 and pill language
colors:
  accent: "#3dbff3"                # sampled from locked PART badge
  accent_alt: "#47c9f4"            # title cyan (ODOO)
  ink: "#ffffff"
  chip_fill: "#1a222c"
  bg_wash: dark_desaturated
forbidden:
  - flat solid background (no Odoo UI)
  - host on left / centered title over face
  - cards, stickers, floating badges on the host
  - purple / cream / newspaper looks
  - inset rounded hero photo of the host
  - aspect ratios other than 16:9
parts:
  # Canonical copy already shipped — reuse structure, change PART + lines + chips only
  1:
    badge: "PART 1"
    title: ["AGENTIC AI", "ODOO STUDIO"]
    payoff: "1 FREE APP"
    chips: [AI, Studio, No Code]
    ref: refs/part1-canonical.png
  2:
    badge: "PART 2"
    title: ["BUILD", "ODOO"]
    payoff: "1 FREE APP"
    chips: [Stock, PO, Menu]
    ref: refs/part2-canonical.png
```

## Agent checklist (every new part)

1. Read this file + open the nearest `refs/*-canonical.png`.
2. Use the locked portrait (beige tee, shoulders-up).
3. Background = darkened/blurred Odoo UI still tied to the episode topic.
4. Left stack: PART badge → 2-line title (white + accent) → payoff → 3 chips.
5. Export / crop to **exactly 1280×720**. Verify with `ffprobe` before upload.
6. Save under the episode as `edit/thumbnails/yt-thumb-odoo-studio-part{n}.png`.
7. If the look is strong enough to become the new canon, promote a copy into `refs/` here.
