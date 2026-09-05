# Claude Skill Lab — mockup system (design doc)

Locked 2026-09-04. This is the build spec for the drawn-screen model.
Companion to [`README.md`](README.md) (series bible) and
[`research.md`](research.md) (topic slate).

---

## Model

Skill Lab records **no screen**. Every "screen" is a Remotion-drawn
mockup. Only the talking head is real footage.

- **Framing: pure explainer.** "Here's the skill, here's how it works,
  here's my take." Not a live test. No honesty-disclosure line, no
  mandatory failure beat. Limits still get mentioned in the "Jujurnya"
  beat, just not staged.
- **Fidelity: stylized.** A recognizably-Claude interface in the Skill
  Lab "Mist" treatment — not a pixel clone. Ages better, no uncanny gap,
  no trademark edge.

### Shot grammar — two states only

| State | Frame | Audio |
|---|---|---|
| **Full cam** | Talking head, `camera_play` framing | cam |
| **Mockup + PIP** | `MockStage` on the stage + cam PIP lower-right (soft-float, existing `pip` tokens) | cam |

No third state. Whenever a mockup is up, the PIP cam is up with it.
Transitions between the two = cut (or the existing cover in/out easing).

### Layer stack during a mockup scene (bottom → top)

1. **`MockCam`** — virtual camera (scale + pan). Wraps 2–3 below; they
   move together in *stage space*.
   1. `MockStage` — the drawn screen (rendered at 2× internally so
      pushes stay crisp)
   2. `Cursor` — pointer on the screen (zooms *with* the stage)
2. Cam PIP bubble — always, when a mockup scene is active. **Outside
   `MockCam`** — stays anchored lower-right at constant size.
3. MG overlays (`title` / `emphasis` / `stat` …) — white ink, no panel.
   **Outside `MockCam`** — screen space, never scaled by a push.
4. Captions / SFX cues

---

## `style: mockup` pack

New pack at `styles/mockup/style.md` (+ token file). Inherits the
`tutorial` A-roll overlay grammar unchanged (open-overlay, white ink, no
panel, surround zones, density 1+1, punch/stagger/count motion). Changes:

- **No `screen` source.** `project.yaml` has `cam` only.
- Drops `cover.mode: prefer_screen` / `cover-suggest` / `cutaways`.
- Adds the `mockup` scene grammar + Mist theme tokens (below).
- Full-frame mockup scenes are native, not "picture-takeover cutaways" —
  house rule 10 does not apply to this pack.
- `pip` tokens carried over from `tutorial` verbatim (near-square,
  `stage_lower_right`, `borderRadiusPx: 26`, `objectPosition: center 28%`).

`project.yaml` for every episode:

```yaml
id: claude-skill-lab-NN-<slug>
series: claude-skill-lab
sources:
  cam: raw/cam.mp4
style: mockup
asr:
  language: id
fps: 30
aspect: "16:9"
width: 1920
height: 1080
```

---

## Mist theme tokens

`styles/mockup/tokens.ts` (mock surfaces only — MG overlay tokens stay in
`glass/tokens.ts`). The stage **always renders light**; it is a screen,
not a themed document.

```
stageBg        #eceff1   (flat)
window         #fdfefe
windowBorder   #dee3e6   (1px hairline)
windowShadow   0 18px 44px -24px rgba(38,58,68,.24), 0 2px 8px -4px rgba(38,58,68,.10)
rail           #f4f6f7
railLine       #e6eaec
chromeTitle    #7d878d
chromeDot      #c3ccd1   (hollow 1.5px ring, not filled)
userBubble     #eef2f4
userInk        #293136
asstInk        #3a434b
badgeBg        #e9eef0
badgeInk       #496573   ← the one accent (slate)
chipBorder     #d8dfe2
chipInk        #79848b
inputBg        #f1f4f5
inputInk       #98a2a8
caret          #496573
cursor         #2f3a40   (dark arrow, 1px white stroke, soft drop shadow)
pipGradient    linear-gradient(150deg, #ccd5da, #a4b2ba)
pipRing        rgba(255,255,255,.60)
```

Character: cool light, product-minimal, line over shadow, flatter and
tighter than a warm treatment. Blends with the existing
`screen_explainer` cool-mist canvas.

Reference render: artifact "MockStage — Linen & Mist", option B.

---

## MockCam — virtual camera

The mockup is never a flat static screen. A scripted virtual camera
(`MockCam`) pushes in on the active spot and pulls back to reveal — the
same idea as the tutorial pack's `camera_play` fake-multicam, but driven
by the mock's own action instead of speech.

### Behaviour

- **Chat typing** → ease to `focus` on the input region; **track the
  caret** (damped follow) as the line grows.
- **Assistant reply starts** → pull back to `read` framing the reply (or
  the whole thread if it's short).
- **Cursor move** → camera follows the cursor at a lower gain (cursor
  leads, camera trails), settling to frame the destination as the click
  lands; a small extra push on the click, release after.
- **Scene start / topic change** → `establish` (whole window).
- **At rest, stop moving.** Once the beat's text is fully revealed, the
  camera settles and holds — no idle drift (mirrors the overlay rule
  "don't hold static MG once nothing is moving").

### States (mirror `camera_play` vocabulary)

| State | Scale (Mist default) | Focus |
|---|---|---|
| `establish` | 1.00 | whole window |
| `read` | 1.20 | active text block |
| `focus` | 1.45 | caret / cursor target / one line |

A keyframe is a **pose that's held** from its `atSec`; the move to the
next pose eases (~420 ms, `Easing.inOut`) ending on the next keyframe's
`atSec`. So `{0 establish}{1.3 focus}{5.2 establish}` = hold wide, ease
in by 1.3, **hold the push through 5.2**, then ease back out. Max scale
**1.6**. `shotFor` grows the focus rect for context, clamps it to the
window, and fits it — no origin clamp beyond the frame edges (for
scale ≥ 1 the stage always covers).

Empty conversation renders a centred "Ada yang bisa saya bantu?" +
composer, so the typing shot has vertical company instead of a wall of
white; once a turn is sent the thread takes over and the composer pins
to the bottom.

### Focus targets

`MockCam` resolves a focus name → box → transform-origin + scale-to-fit
(with padding), using the **same registry as `Cursor`**. Components
publish regions: `chat.input`, `chat.caret`, `chat.turn.assistant`,
`chat.turn[N]`, `diff.before`, `diff.after`, `app.window`,
`skills.row[name]`, plus any `Cursor` hit-target. `track: "caret" |
"cursor" | null` turns on per-frame damped follow between keyframes.

### Pack config — `styles/mockup/style.md`

```yaml
# camelCase — read straight into the Remotion MockCamConfig, no remap.
# (styles/mockup/style.md is the source; Python load_mockup() merges it over
# DEFAULT_MOCK; TS DEFAULT_MOCK_STYLE is only the fallback.)
mock_cam:
  easeMs: 420
  holdMinSec: 1.2
  scales: { establish: 1.0, read: 1.20, focus: 1.45 }
  maxScale: 1.6
  followGain: 0.12        # caret/cursor trailing-follow strength
  settleAfterRead: true   # stop easing once the beat's text is revealed
  intensity: calm         # calm = fewer moves, smaller pushes, longer holds
```

`intensity: calm` is the Mist default — modest pushes, slow eases,
generous holds. Not frantic. A punchier episode can override per
`project.yaml`.

### Data — `camera[]` per scene

Added to each scene in `edit/mockup.json`:

```json
"camera": [
  { "atSec": 0.0,  "state": "establish" },
  { "atSec": 1.2,  "state": "focus", "focus": "chat.input", "track": "caret" },
  { "atSec": 6.5,  "state": "read",  "focus": "chat.turn.assistant" },
  { "atSec": 12.0, "state": "establish" }
]
```

`ae mockup-suggest` auto-generates this track from the layer beats
(typing turn → `focus`+track caret; assistant turn → `read`; cursor path
→ follow). Hand-editable after apply.

---

## Components

Build under `packages/remotion-kit/src/components/mockup/`. Promote any
reusable fix into the pack — never fork into an episode (house rule 9).

**Status (2026-09-04):** all 8 components + the Python bridge built in G:
— `MockStage`, `MockCam`, `ClaudeChat`, `DiffPanel`, `Cursor`,
`AppWindow`, `SkillsPanel`, `RepoView` + `Typewriter` + `regions.ts`.
Wired into `Composition.tsx` (`<MockupLayer>`); preview via `MockupLab`
(`remotion studio`), one scene per surface. **The chat + diff quality
(Mist look, hold-pose camera, type-in-input-then-send, zoom play) is the
locked baseline — don't regress it.**

`Cursor` = eased hops between waypoints (reach the point by its `atSec`),
click ripple + a short dip; lives inside `MockCam`. `AppWindow` =
stylized `mock-deck` / `mock-sheet` / `mock-doc` (or a host `src` still)
with an app toolbar + open anim; scene `chrome: "app"` suppresses the
MockStage title. `SkillsPanel` = Settings → Kapabilitas → Skills, rows
with source pill + animated toggle (`action: "toggle:<name>"`), optional
upload drop-sheet (`action: "upload"`). `RepoView` = browser-framed
GitHub repo — URL bar + `owner / repo` + file tree + a tiny-parsed
**real SKILL.md** with slow auto-scroll; scene `chrome: "none"` (it draws
its own window). New focus regions: `skills.row.<name>`, `skills.upload`,
`repo.doc`.

**Skill → source registry.** `styles/series/claude-skill-lab/skills.yaml`
maps a slug → `{source, repo, branch, path}`. `ae mockup-suggest`
`resolve_skill()` derives the repo web URL + raw `SKILL.md` URL (unknown
slug → `anthropics/skills` + `skills/<slug>`), `fetch_skill_md()` pulls
the real markdown (8 s timeout) and caches it under
`edit/.mockup-cache/<slug>.SKILL.md`. Offline → RepoView gets a `<TODO>`
placeholder and `_meta.repo_md_fetched: false`.

The `> "…"` blockquote branch also appends a light **`Cursor`** to the
`ClaudeChat` scene (rest near the composer → click as the message sends).

### Core (build order)

| # | Component | Role | Data |
|---|-----------|------|------|
| 1 | **`MockStage`** | Scene container — Mist desktop bg, window frame + chrome, enter/exit, rest state for thumbnails. Renders at `oversample` (2×). Reuses `cutaway/shared` (Backdrop/Grain/Vignette). Hosts one surface. Publishes focus regions to the registry. | `{ title?, chrome?: 'claude'\|'app'\|'browser'\|'none', in, out }` |
| 2 | **`MockCam`** | Virtual camera — scale + pan over `MockStage` + `Cursor`, keyframed by `camera[]`, damped caret/cursor follow, settle-at-rest. See MockCam section. | `camera[]: { atSec, state:'establish'\|'read'\|'focus', focus?, track?:'caret'\|'cursor' }` |
| 3 | **`ClaudeChat`** | Stylized conversation. A `reveal: type` **user** turn types into the **input bar** first (dark ink + caret), then "sends" — the bubble pops in and the input clears. Assistant reply reveals in place (`type`/`stream`) with `▸ Pakai skill · X` pill, attachment chips, collapsible tool block. Publishes `chat.*` focus regions; `chat.caret` points at the input bar while composing. | `turns[]: { role:'user'\|'assistant', text, reveal:'instant'\|'type'\|'stream', skillBadge?, attachments?:[{name,kind}], toolBlock?:{label,lines[]}, atSec? }` |
| 4 | **`DiffPanel`** | Before/after text, word-level highlight (del = strike, add = underline). Reveal: before, then after wipes in, highlights pulse. Publishes `diff.before` / `diff.after`. `beforeMarks`/`afterMarks` are **auto-derived** from a word diff of `before` vs `after` at timeline-build time (`diff_marks()` in `cover/mockup.py`); author-supplied marks override. | `{ before, after, beforeMarks?:[{type:'del', span:[start,end]}], afterMarks?:[{type:'add', span:[start,end]}] }` |
| 5 | **`Cursor`** | Pointer inside `MockCam` (zooms with the stage) — eased hops, hover scale, click ripple + SFX cue to `SfxLayer`. Resolves targets from the registry. | `{ path:[{ atSec, target: string\|[x,y], action?:'move'\|'hover'\|'click', dwell? }] }` |
| 6 | **`AppWindow`** | "Output opened" frame — pptx/xlsx/docx/preview/browser chrome, open anim. Stylized mock content (or host still). | `{ app:'pptx'\|'xlsx'\|'docx'\|'preview'\|'browser', content:'mock-deck'\|'mock-sheet'\|'mock-doc'\|{src}, panFrames? }` |
| 7 | **`SkillsPanel`** | Settings → Capabilities → Skills — sidebar, skill rows + toggles, upload drop state. | `{ skills:[{name,source,on}], action?:'toggle:<name>'\|'upload' }` |
| 8 | **`RepoView`** | Browser-framed GitHub repo — URL bar, `owner / repo` + source chip, file tree, real SKILL.md (tiny block parser: headings/lists/code/tables/quote) with slow auto-scroll. Scene `chrome: "none"`. | `{ repoUrl, repo?, path?, source?, markdown, scroll?, atSec? }` |

Shared **`Typewriter`** primitive under 3 & 4: `text.slice(0,
floor(interpolate(frame, [start,end], [0,len])))` + blinking caret, and
it exposes the caret box so `MockCam` can track it.

**Episode 1 (`avoid-ai-writing`)** uses surfaces **`RepoView`** ("dari
mana" beat — real SKILL.md), **`ClaudeChat`** + **`Cursor`** (demo), and
**`DiffPanel`** (before/after). `AppWindow` / `SkillsPanel` start in
episodes 2–3 (`pptx`, `skill-creator`, `discernment-nudge`, `xlsx`).

### Bench (later)

`ArtCanvas` (p5.js in Remotion, seed-tweak beat) · `Toast` / `FileChip`.

---

## Focus regions

`resolveRegion(name, scene, tLocal)` in
`packages/remotion-kit/src/components/mockup/regions.ts` — **deterministic**,
derived from the scene data + a few layout constants (no
`getBoundingClientRect`, so it's identical on every render pass). Both
`Cursor` (→ centre point) and `MockCam` (→ box, grown for context and fit
to the frame) call it. Coordinates resolve in **stage space** (pre-`MockCam`
transform). Names:

`chat.input` · `chat.caret` (slides with typing progress) ·
`chat.turn.assistant` · `chat.turn.N` · `diff.before` · `diff.after` ·
`app.window` · `skills.row.<name>` · `skills.upload` · `repo.doc`.
Fallback: a `focusPoint: [x,y]` (0–1 of stage) on the keyframe.

---

## `ae mockup-suggest .`

Reads **only the cam transcript** (`edit/transcripts/cam.json`) → writes
`edit/mockup.suggest.json` with camera skeletons + `<TODO>` placeholders.
`--apply` runs `validate_mockup()` and writes `edit/mockup.json`. Suggest /
fill / confirm / apply (house rule 1).

The episode script is **not** read — it's a recording guide, not editing
truth. Placement is driven by what the speaker actually said, so no
transcript → nothing to place (`_meta.error`, run `ae ingest .` first).

- **Spoken-phrase triggers** (`_MOCKUP_TRIGGERS` in `cover/mockup.py`), each
  scene anchored to the ASR `start` of its trigger word:
  `repo` / `di github` / `sumbernya` / `skill.md` → **`RepoView`**;
  `settings` / `kapabilitas` / `bagian skill` / `toggle` → **`SkillsPanel`**;
  `sebelum` / `sesudah` / `hasil revisi` → **`DiffPanel`**;
  `kebuka di` / `pptx` / `xlsx` / `docx` → **`AppWindow`**;
  a spoken prompt lead-in (`aku bilang …`, `minta claude …`, `aku ketik …`)
  → **`ClaudeChat`**, user turn = the words the speaker reads aloud after
  the lead-in, + a light `Cursor`. A spoken prompt **wins** over any
  keyword trigger in the same window.
- Multi-word phrase = high confidence; a bare word (`repo`, `settings`,
  `sebelum`, …) = **low** confidence — the scene is still emitted but listed
  in `_meta.low_confidence_scenes` and printed with a `⚠` + `mm:ss` for you
  to verify before `--apply`.
- Repeat hits of the same component within `min_gap_sec` (default 12 s)
  collapse to one. Scene `toSec` = next trigger's anchor, else a per-kind
  dwell (ClaudeChat 22 s, RepoView 14 s, DiffPanel 12 s, others 10 s),
  clamped to transcript end. `build_timeline_mockups` then clamps each
  scene to its longest kept cam slice through the EDL.
- Skill slug = `skill:` in `project.yaml` if set, else the `skills.yaml`
  slug the speaker mentions most, else none.
- Override the trigger table / min-gap per style pack in
  `styles/mockup/style.md`:
  ```yaml
  mockup_suggest:
    min_gap_sec: 12
    triggers:
      RepoView: ["repo", "di github", "sumbernya"]
      SkillsPanel: ["settings", "kapabilitas"]
  ```

`edit/mockup.json` shape (all times **cam source seconds**):

```json
{
  "scenes": [
    {
      "id": "sc-03-demo",
      "fromSec": 92.0,
      "toSec": 148.5,
      "stage": { "title": "avoid-ai-writing", "chrome": "claude" },
      "camera": [
        { "atSec": 92.0,  "state": "establish" },
        { "atSec": 93.4,  "state": "focus", "focus": "chat.input", "track": "caret" },
        { "atSec": 99.0,  "state": "read",  "focus": "chat.turn.assistant" },
        { "atSec": 146.0, "state": "establish" }
      ],
      "layers": [
        { "component": "ClaudeChat", "data": { "turns": [] } },
        { "component": "Cursor", "data": { "path": [] } }
      ]
    }
  ]
}
```

Hand-editing `edit/mockup.json` after apply is fine — it's scene data,
not cut ranges.

**Budget:** keep drawn scenes to **≲ 40 % of runtime**. Full-frame React
Remotion is much heavier than cam passthrough — a mostly-mockup 7-min
episode can hit the ENOSPC / render-time walls the segmented-render path
(`compose/segmented`) was built for.

---

## Pipeline wiring (built)

- **`edit/mockup.json`** — scenes live here, **not** in `cover.json`, so
  `ae cover-suggest` / `ae overlay-suggest` can never clobber them.
  `ae cover .` and `ae compose .` both read it and inject `cover["mockups"]`
  before the timeline build.
- **`src/agentic_editor/cover/mockup.py`** —
  - `build_timeline_mockups(edl, cover)` → `(scenes, pip_clips)`: remaps
    each scene `fromSec/toSec` to the longest contiguous kept cam slice
    (output time), rewrites every inner `atSec` (camera keyframes, chat
    turns, cursor waypoints) to **scene-local** via a deep walk, and emits
    one `pip_corner` cam clip per scene with the real `sourceIn/sourceOut`.
  - `load_mockup(style_name)` → `presentation.mockup` (Mist tokens + `cam`
    config), `styles/mockup/style.md` merged over `DEFAULT_MOCK`.
  - `suggest_mockups` / `validate_mockup` / `write_mockup_suggest`.
- **`cover/__init__.py`** `build_timeline_from_edl_and_cover` — calls
  `build_timeline_mockups`, `clips.extend(pip_clips)`, sets
  `timeline["mockups"]` and `timeline["presentation"]["mockup"]`.
- **`cli.py`** — `ae mockup-suggest` (+`--apply`); `cmd_cover` /
  `cmd_compose` load `edit/mockup.json`.
- **`compose/draft_slice.py`** — `mockups` + `cutaways` trimmed to the
  draft window like overlays.
- **`Composition.tsx`** — `<MockupLayer scenes={timeline.mockups}
  style={timeline.presentation?.mockup} />` between the main clips and the
  `pip_corner` clips, so the cam PIP composites on top; MG overlays render
  above that, outside `MockCam`.
- **`json-schemas/mockup.schema.json`** — reference; runtime check is the
  hand-rolled `validate_mockup()` (repo has no `jsonschema` dep).

`$AGENTIC_EDITOR_HOME` is `D:\AI\video-editor-agent`, a **directory
junction** to `G:\AI\video-editor-agent` — one physical checkout on G:,
so edits under either path are the same files. Nothing to sync.

---

## Deferred / open

- `mockup-suggest` only drafts scene data, never talking-head cut points
  (radio-edit stays the source of truth for the EDL).
- `mockup-suggest`'s transcript match is a coarse token-overlap slide —
  always eyeball `fromSec`/`toSec` against the storyboard before `--apply`.
- A scene that straddles a radio-edit cut is clamped to its **longest**
  kept slice (with the rest dropped) — author scene windows over
  continuous speech.
- `ArtCanvas` p5.js-in-Remotion perf on full renders (test at ep 4).
- Whether the pinned "cara aktifin skill" setup video is itself a
  `style: mockup` episode (likely yes — `SkillsPanel` showcase).
- No `ae`-level guardrail yet on the ≲40 % mock-scene budget — it's a
  documented convention, not enforced.
