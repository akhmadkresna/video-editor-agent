# Thumbnail — Claude Skill Lab (series template)

**Locked template.** Do not invent a new layout per episode — only swap
the per-episode variables (skill name, verdict word, source chip, screen
behind host). Export **exactly 1280×720** (16:9).

```yaml
video:
  id: claude-skill-lab-NN-<skill-slug>
  title: "<episode title>"
  channel_use: YouTube thumbnail
  series: claude-skill-lab
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
    expression: curious_calm        # trying it out — not shocked, not smug
  background:
    kind: evidence_screenshot       # Claude Desktop with the skill running, OR the GitHub repo page
    treatment: darken_blur
    source: episode raw/evidence still matching the skill
  copy:
    zone: left_two_thirds
    stack: [series_tag, skill_name, verdict_stamp, chips]
  series_tag:
    text: "SKILL LAB"               # small, above the skill name
    color: accent
    size: small_caps
  skill_name:
    font: bold_condensed_sans
    case: upper
    lines: 1-2
    color: "#ffffff"
    text_example: "SKILL PPTX"
  verdict_stamp:
    text_options: ["WORTH IT?", "WORTH IT", "SKIP", "KALAU KAMU SERING X"]
    note: question form for the thumb; the answer lands in the video
    color: "#ffffff"
    size: smaller_than_skill_name
    position: under_skill_name
  chips:
    count: 2
    row: bottom_left
    shape: dark_pill
    border: accent
    example: ["BAWAAN CLAUDE", "SETUP RINGAN"]   # or ["DARI GITHUB", "DROP-IN"]
colors:
  accent: "#c084fc"                 # violet — distinct from ai-adopsi-gap sky blue
  ink: "#ffffff"
  chip_fill: "#1c1726"
  bg_wash: dark_desaturated
per_episode_variables:
  - skill_name
  - verdict_stamp text
  - source chip (BAWAAN CLAUDE vs DARI GITHUB)
  - background screenshot
forbidden:
  - AI-generated fake Claude UI or fake output as background
  - flat solid background with no screenshot
  - host on left / copy over face
  - shocked / clickbait face
  - changing accent color between episodes
  - aspect ratios other than 16:9
  - inventing a new copy stack per episode
final_example:
  series_tag: "SKILL LAB"
  skill_name: ["SKILL PPTX"]
  verdict_stamp: "WORTH IT?"
  chips: ["BAWAAN CLAUDE", "SETUP RINGAN"]
```
