# Series thumbnail — Kampus, AI, dan Masa Depan Anak IT

**Locked.** Do not invent a new YouTube thumbnail layout for this series.
Export **exactly 1280×720** (16:9). Never ship 3:2.

Because titles are questions, keep a **large question mark** as the
series binder across all five thumbs. Expression: calm / serious senior,
not shock-clickbait.

```yaml
series:
  id: freshgrad-ai-dev
  title: Kampus, AI, dan Masa Depan Anak IT
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
    expression: calm_serious     # not kaget-lebay; raised brow OK on part 3
    rim_light: warm_on_camera_left
    head: never_cropped
  background:
    behind_host: studio_room
    left_and_edges:
      kind: code_or_terminal_still   # Cursor / VS Code / GitHub, darkened
      treatment: darken_blur
      source: episode still matching the part (campus/code, AI chat, jobs, interview, roadmap)
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
    max_words: 4
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
  binder:
    element: oversized_question_mark   # same glyph family on all 5
    color: accent
    opacity: 0.35
    placement: behind_copy_not_on_face
colors:
  accent: "#facc15"                # warning-yellow; keep across 5 videos
  ink: "#ffffff"
  chip_fill: "#1a222c"
  bg_wash: dark_desaturated
forbidden:
  - AI-generated finished thumbnail (plate + draw only, same as odoo series)
  - host on left / title over face
  - purple / cream / newspaper looks
  - aspect ratios other than 16:9
  - "I'M COOKED" / skull / fake layoff dashboards
  - judging copy: PRIMITIVE, KAMPUS GAGAL, JOKI, HIJACK, KULIAH PERCUMA
  - shock-open-mouth clickbait face
parts:
  1:
    badge: "PART 1"
    title: ["MASIH", "CUKUP?"]
    payoff: "KULIAH IT 4 TAHUN, 2026"
    chips: ["SANGGUP ≠ SIAP", "BUKAN SALAH DOSEN", "15–18 MNT"]
  2:
    badge: "PART 2"
    title: ["DIBAYAR", "BUAT APA?"]
    payoff: "KALAU NGODING SUDAH GAMPANG"
    chips: ["NILAI PINDAH", "CONTEXT ENG", "TEBAK 60 DETIK"]
  3:
    badge: "PART 3"
    title: ["JUNIOR", "-73%"]
    payoff: "PINTUNYA DIPINDAH, BUKAN DITUTUP"
    chips: ["BUKAN KALIAN JELEK", "BPS 16,9%", "TALENT PIPELINE"]
    # Swap "-73%" if primary-source check fails before upload.
  4:
    badge: "PART 4"
    title: ["5 HAL", "INI"]
    payoff: "DICARI HRD, GAK DI TRANSKRIP"
    chips: ["NJELASIN", "BACA KODE", "PAHAM UANG"]
  5:
    badge: "PART 5"
    title: ["ROADMAP", "2026"]
    payoff: "KALAU SAYA BALIK JADI MAHASISWA"
    chips: ["TUTOR BUKAN TUKANG", "5 USER", "KOMPAS BUKAN PETA"]
```

**Plate + draw:** never ask an image generator for the finished thumb. Generate a
text-free plate (host + studio; darkened editor UI only on left/edges), then
draw copy to match this recipe. Until a `build_thumbnail.py` exists for this
series, compose in the same metrics spirit as
`styles/series/odoo-studio-agentic-ai/thumbnail.md` (flush-left stack, host
clear of type). Top-crop plates to 16:9.
