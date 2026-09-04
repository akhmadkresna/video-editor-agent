# Mockup style pack

Talking-head + **drawn screen** (Remotion mock, no screen recording). Built
for Claude Skill Lab. Two shot states only: full cam ⇄ mockup + PIP. Full
spec: `styles/series/claude-skill-lab/mockup-system.md`.

Inherits the `tutorial` A-roll overlay grammar (open-overlay, white ink, no
panel, surround zones, density 1+1). Drops `screen` source, `cover-suggest`,
`cutaways`. Adds the `mockup` scene grammar + "Mist" theme + `mock_cam`.

The Remotion side reads these from `presentation.mockup` in the timeline
props; `DEFAULT_MOCK_STYLE` in `packages/remotion-kit/src/types.ts` is the
authoritative fallback until a Python `load_mockup()` lands.

```yaml
profile: mockup

overlays:
  # A-Roll Text Motion System — all tokens inherited from DEFAULT_OVERLAYS
  # (styles/aroll-text-motion/overlays.style.yaml). MG renders above the
  # drawn scene via the same <OverlayLayer>.
  preset: aroll_text_motion
  treatment: bold
  ink: "#ffffff"

# Mist mock surfaces — the stage always renders light (it's a screen).
mockup:
  stageBg: "#eceff1"
  window: "#fdfefe"
  windowBorder: "#dee3e6"
  rail: "#f4f6f7"
  railLine: "#e6eaec"
  chromeTitle: "#7d878d"
  chromeDot: "#c3ccd1"
  userBubble: "#eef2f4"
  userInk: "#293136"
  asstInk: "#3a434b"
  badgeBg: "#e9eef0"
  badgeInk: "#496573"        # the one accent — slate
  chipBorder: "#d8dfe2"
  chipInk: "#79848b"
  inputBg: "#f1f4f5"
  inputInk: "#98a2a8"
  caret: "#496573"
  cursor: "#2f3a40"
  pipGradient: "linear-gradient(150deg, #ccd5da, #a4b2ba)"
  pipRing: "rgba(255,255,255,0.60)"
  diffDel: "#b1566b"         # semantic (removed) — not the accent
  diffAdd: "#5c8a68"         # semantic (added)

# Virtual camera over the mock. Fits the active region into the frame and
# pulls back to reveal. calm = fewer moves, smaller pushes, longer holds.
mock_cam:
  easeMs: 420
  holdMinSec: 1.2
  scales: { establish: 1.0, read: 1.20, focus: 1.45 }   # target fills, not literal scale
  maxScale: 1.6
  followGain: 0.12          # caret/cursor trailing-follow strength
  settleAfterRead: true
  intensity: calm

# pip carried over from tutorial verbatim
screen_explainer:
  pip:
    anchor: stage_lower_right
    widthRatio: 0.18
    aspectRatio: "5:6"
    insetRightRatio: 0.034
    insetBottomRatio: 0.044
    borderRadiusPx: 26
    objectFit: cover
    objectPosition: "center 28%"
```

## Cover modes

| Mode | When | Visual | Audio |
|------|------|--------|-------|
| Full cam | Default / between mock scenes | Cam + `camera_play` framing | Cam |
| Mockup + PIP | A `mockups[]` scene covers the frame | `MockStage` (Mist) under `MockCam`, cam PIP at stage lower-right | Cam only |

Drawn scenes come from `ae mockup-suggest .` → `edit/mockup.json`
(`mockups[]` on `cover.json`). Rendered by `<MockupLayer>` in
`Composition.tsx`. MG overlays + cam PIP composite on top, outside `MockCam`.

## Components (remotion-kit)

`components/mockup/`: `MockStage` · `MockCam` · `ClaudeChat` · `DiffPanel`
(built) · `Cursor` · `AppWindow` · `SkillsPanel` (pending). Shared
`Typewriter`, deterministic focus rects in `regions.ts`. Preview:
`MockupLab` composition (`remotion studio`).

Do not fork the look per episode — promote changes here.
