# Series thumbnail — Freshgrad Software Dev (Era AI)

**Locked.** Do not invent a new YouTube thumbnail layout for this series.
Export **exactly 1280×720** (16:9). Never ship 3:2.

```yaml
series:
  id: freshgrad-ai-dev
  title: Freshgrad Software Dev — Era AI
  channel_use: YouTube thumbnail
output:
  width: 1280
  height: 720
  aspect: "16:9"
  post:
    crop: "iw:iw*9/16:0:0"     # top-crop plates; never centre-crop
    scale: "1280:720"
layout:
  # Same house grammar as odoo / ai-youtube-idr: host RIGHT, copy LEFT
  host:
    side: right
    framing: shoulders_up
    wardrobe: beige_crew_tee
    expression: slight_smile     # ep1–2 may be more serious / raised brow
    rim_light: warm_on_camera_left
    head: never_cropped
  background:
    behind_host: studio_room
    left_and_edges:
      kind: code_or_terminal_still   # Cursor / VS Code / GitHub, darkened
      treatment: darken_blur
      source: episode screen still matching the part (agent, spec, portfolio)
  copy:
    zone: left_two_thirds
    stack: [part_badge, title_lines, payoff_line, chips]
    align: flush_left_single_margin
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
      line_a: "#ffffff"
      line_b: accent
  payoff:
    color: "#ffffff"
    size: smaller_than_title
    position: under_title
  chips:
    count: 3
    row: bottom_left
    shape: dark_pill
    border: accent
colors:
  accent: "#facc15"                # warning-yellow for career-hook thumbs
  ink: "#ffffff"
  chip_fill: "#1a222c"
  bg_wash: dark_desaturated
forbidden:
  - AI-generated finished thumbnail (plate + draw only, same as odoo series)
  - host on left / title over face
  - purple / cream / newspaper looks
  - aspect ratios other than 16:9
  - "I'M COOKED" / skull / fake layoff dashboards
  - judging copy: PRIMITIVE, KAMPUS GAGAL, JOKI, HIJACK
parts:
  1:
    badge: "PART 1"
    title: ["CARA BELAJAR", "PERLU BERUBAH"]
    payoff: "KEKHAWATIRAN YANG MASUK AKAL"
    chips: ["LATIHAN BARU", "SPEC + BACA", "TETAP KULIAH"]
  2:
    badge: "PART 2"
    title: ["INTENT DULU", "KODE MENYUSUL"]
    payoff: "SATU HALAMAN SEBELUM IDE"
    chips: ["SHIFT LEFT", "AADP", "DELEGATE TASKS"]
  3:
    badge: "PART 3"
    title: ["PELATIH", "BUKAN PENGGANTI"]
    payoff: "HINT DULU, KODE KEMUDIAN"
    chips: ["CRUTCH → COACH", "+48% / −17%", "ANALOGI"]
  4:
    badge: "PART 4"
    title: ["YANG PERLU", "DILATIH"]
    payoff: "BACA · REVIEW · SECURITY"
    chips: ["READ > WRITE", "TES", "SISTEM"]
  5:
    badge: "PART 5"
    title: ["LENGKAPI", "SEMESTER INI"]
    payoff: "KULIAH TETAP, METODE DITAMBAH"
    chips: ["LOG PROSES", "USER NYATA", "SATU BUKTI"]
```

**Plate + draw:** never ask an image generator for the finished thumb. Generate a
text-free plate (host + studio; darkened editor UI only on left/edges), then
draw copy to match this recipe. Until a `build_thumbnail.py` exists for this
series, compose in the same metrics spirit as
`styles/series/odoo-studio-agentic-ai/thumbnail.md` (flush-left stack, host
clear of type). Top-crop plates to 16:9.
