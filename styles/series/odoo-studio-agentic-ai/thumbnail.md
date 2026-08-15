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
  # If a generator returns non-16:9: TOP-crop height to iw*9/16, then scale 1280×720.
  # Centre-cropping a 3:2 generation clips the host's hair — build_thumbnail.py top-crops.
  post:
    crop: "iw:iw*9/16:0:0"
    scale: "1280:720"
layout:
  # Rule of thirds — host RIGHT, copy + chips LEFT
  host:
    side: right
    framing: shoulders_up          # chest/shoulders, not full torso
    wardrobe: beige_crew_tee       # lock: kresna-studio2 look
    expression: slight_smile
    rim_light: warm_on_camera_left # host's right shoulder
    head: never_cropped            # whole head + hair inside frame, with headroom
    # Portrait refs (machine-local, not in repo):
    #   D:\AI\Media\kresna-studio2.png  (preferred)
    #   D:\AI\Media\kresna-studio.png
  background:
    # TWO zones — the refs are a blend, not a full-screen screenshot.
    behind_host: studio_room       # warm lamp, plant, bookshelf, LED strip stay visible
    left_and_edges:
      kind: odoo_ui_screenshot
      treatment: darken_blur       # readable copy; UI still recognizable
      source: episode screen still or Studio/list UI matching the part topic
    # Odoo UI must never cover the area behind the host's head.
  copy:
    zone: left_two_thirds
    stack: [part_badge, title_lines, payoff_line, chips]
    align: flush_left_single_margin # badge, BOTH title lines, payoff, rule and
                                    # chips share ONE left edge — no second margin
  part_badge:
    shape: rounded_rect
    fill: accent
    text: "PART {n}"               # white, bold sans, all caps
    position: top_left
  title:
    font: bold_condensed_sans      # Anton (fonts/Anton-Regular.ttf)
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
metrics:
  # Sampled from refs/part1-canonical.png at 1280x720 — build_thumbnail.py draws these.
  margin_x: 49
  part_badge: { y: 88, w: 161, h: 57, label_cap: 27 }
  title_line_a: { y: 173, cap: 134 }   # white, condensed (Anton), letterspaced ~8px
  title_line_b: { y: 321, cap: 125 }   # accent, same face
  payoff: { y: 479, cap: 39 }          # WIDE grotesque (Inter Black) — not the title face
  accent_rule: { y: [538, 544] }       # width follows the payoff line
  chips_row: { y: [570, 628] }         # pill h 58, icon 34, label Inter 600 @34
  margins: { top: "12%", bottom: "13%" }
colors:
  accent: "#3dbff3"                # sampled from locked PART badge
  accent_alt: "#47c9f4"            # title cyan (ODOO)
  ink: "#ffffff"
  chip_fill: "#1a222c"
  bg_wash: dark_desaturated
forbidden:
  - flat solid background (no Odoo UI)
  - Odoo UI filling the whole frame (the studio room must stay behind the host)
  - cropped head / hair touching the top edge
  - two different left margins in the copy stack
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
  3:
    badge: "PART 3"
    title: ["AI BUILDS", "ODOO SALES"]
    payoff: "1 FREE APP"
    chips: [Sales, Cart, Stock]
    # bg: product kanban with "Tambah ke Keranjang" + Kasir menu (sales/cashier build)
  4:
    badge: "PART 4"
    title: ["AI BUILDS", "ODOO BOOKS"]
    payoff: "1 FREE APP"
    chips: [Cash, "P&L", KPI]
    # bg: Dashboard Toko Material — saldo kas / omzet / laba / piutang tiles
  # Keep title line_b at 10 characters or fewer, or it runs into the host.
```

## Agent checklist (every new part)

Do **not** ask an image generator for the finished thumbnail — generators drift on
alignment, type scale and safe margins. Generate a *plate*, then draw the copy.

1. Read this file + open the nearest `refs/*-canonical.png`.
2. Grab a background still from the episode's own `raw/screen.*` that shows the
   feature this part builds (`ffmpeg -ss <t> -i raw/screen.mkv -frames:v 1 …`).
3. Generate a **text-free plate**: locked portrait (beige tee, whole head with
   headroom) on the right, his studio room behind him, darkened Odoo UI panels on
   the left and edges. Say "no text, no letters, no badges" explicitly.
4. Draw the copy stack with `build_thumbnail.py` (metrics above, fonts in `fonts/`):

   ```bash
   uv run python styles/series/odoo-studio-agentic-ai/build_thumbnail.py \
     --plate <episode>/edit/thumbnails/part{n}-plate.png \
     --out   <episode>/edit/thumbnails/yt-thumb-odoo-studio-part{n}.png \
     --part {n} --line-a "AI BUILDS" --line-b "ODOO SALES" \
     --chip cart=Sales --chip basket=Cart --chip box=Stock
   ```

   It top-crops the plate (never centre-crops — generators sit the head near the
   top edge) and writes exactly 1280×720.
5. Verify with `ffprobe` before upload, and eyeball against the canonical ref.
6. Keep the plate next to the output so the part can be rebuilt with new copy.
7. If the look is strong enough to become the new canon, promote a copy into `refs/` here.
