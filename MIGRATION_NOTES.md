# Remotion → HyperFrames migration notes

This is a **clean rebuild**, not a pixel-accurate port. `packages/remotion-kit/`
(React/Remotion, 60+ TSX files) was removed; `packages/hyperframes-kit/` (an HTML
+ GSAP composition rendered via Chrome + FFmpeg) replaces it. The Python `ae` CLI
pipeline's compose stage now materializes each episode's `edit/timeline.json` into
a generated HyperFrames `index.html` via `src/agentic_editor/compose/hf_template.py`,
instead of feeding `timeline.json` to React as `--props` at render time (HyperFrames
has no equivalent live-props system for structural/array data — only scalar
`data-composition-variables` — so the array of clips/overlays/cutaways/mockups is
expanded into repeated HTML/GSAP markup at *generation* time instead).

Old Remotion source is not in this tree; it's recoverable via
`git show 1287d80~1:packages/remotion-kit/src/<path>` for reference.

## Composition families — role-for-role, not pixel-for-pixel

`hf_template.py` reproduces the *behavioral role* each old Remotion layer played,
using HyperFrames' own GSAP/CSS primitives directly rather than the registry
catalog's named blocks — the roles are simple enough (opacity/scale/translate
tweens keyed off `timeline.json` data) that hand-authored markup was more direct
than wiring in the ~400-block catalog for each one. If a family's visual language
grows more elaborate later, prefer `npx hyperframes catalog --query "..."` over
adding more hand-rolled CSS.

- **Camera motion** (`_emit_clip`): `drift` = auto push-in (1.5%/sec scale, clamped
  5–15%, `sine.inOut`), `pull_back` = its mirror, both only on `layout: full` clips.
  `ease_in`/`ease_out`/`hold`/`snap` cover the remaining old motion kinds. Manual
  `punch_in`/`punch_out` (`_emit_punch_effects`) only attach to a `hold`/`snap`
  host clip so they never stack a second `scale` tween on a clip that already owns
  one for its whole span (would trip HyperFrames' `overlapping_gsap_tweens` lint).
- **Overlays** (`_emit_overlay` / `_overlay_body_html`): all 13 old Remotion kinds
  (`title`, `stat`, `lower_third`, `tag`, `divider`, `quote`, `code`,
  `illustration`, `chapter`, `emphasis`, `diagram`, `callout`, `chip`) plus
  `list_cycle` map onto a shared white-ink-over-scrim look (`.overlay-scrim` +
  `.overlay-inner`) — no panel, no accent color beyond the translucent-white chip
  border, matching the old A-Roll Text Motion System's locked style. Fade in/out
  (not pop), with per-kind markup shape only where the kind actually needs
  different structure (rows, code lines, diagram steps).
- **Cutaways** (`_emit_cutaway`): the old family-specific components (BlueprintNodes,
  Evidence, InterfaceStage, KineticFigures, LedgerFlow, Minimal, ReceiptTape)
  consolidate onto one card shape (kicker/title/rows/proof-image/footer) with a
  `style` class (`press`/`thermal`/`darkroom`/`cyanotype`/`night`/`daylight`) that
  swaps the color treatment — the old families mostly differed in tone/palette,
  not structure.
- **Mockups** (`_emit_mockup`): AppWindow/ClaudeChat/DiffPanel/RepoView/SkillsPanel
  render as `.mock-window` content variants keyed by the layer's `component` name
  (kept identical to the old component names — also mirrored in
  `json-schemas/mockup.schema.json`'s `component` enum, so the schema needed no
  change). `camera` keyframes (`establish`/`read`/`focus`) drive a `.mock-body`
  scale tween. `Cursor` (a moving-dot pointer overlay) and `MockCam`/`MockStage`/
  `Typewriter` are dropped in this rebuild — pointer emphasis / staging chrome,
  not core information; can be re-added later as a small absolute-positioned dot
  keyframed against the same `camera` array if a script calls for it.
- **Privacy layer** (`_emit_privacy`): opaque `%`-positioned bars, framework-
  independent (no blur filter — solid redaction reads clearly at any resolution
  and needs no GPU filter support).
- **Captions** (`_emit_caption`): burned-in caption line, fade not pop, unchanged
  in spirit from the old `CaptionLine.tsx`.

## Dropped / simplified pieces

- `SfxLayer` — `compose.stage_sfx_for_hyperframes` already staged
  `timeline.sfx[]` cues into the per-episode project's `assets/sfx/`, but
  `hf_template.py` wasn't actually emitting them into the composition
  (a gap from the initial scaffold, not an intentional drop) — fixed here
  with `_emit_sfx`: one `<audio class="clip">` one-shot per cue, gain via
  the static `data-volume` attribute (no tween — these are short one-shots,
  not faded).
- `MissingTimelineBanner` — Remotion showed this when `--props` was absent; HF
  compositions are generated straight from a present `timeline.json` per episode
  (`prepare_compose`/`prepare_draft`), so there's no "missing props" runtime state
  to bannerize. `hyperframes lint`/`check` catch a malformed composition instead.
- Letterboxing / theme tokens are inlined as plain CSS in `_CSS` rather than a
  separate theme module — the whole composition is one generated file per episode,
  so there is no cross-composition theme sharing to justify indirection.

## Tooling / infra

- `scripts/setup-hyperframes-windows.ps1` (renamed from
  `setup-remotion-windows.ps1`): redirects the npm cache (which `npx hyperframes`
  package installs and its one-time Chrome Headless Shell download land under) to
  the G: house-layout cache dir, same as the pnpm store. Replaces the old
  `REMOTION_SCRATCH_ROOT` env var, which has no HyperFrames equivalent — HF has no
  separate scratch-root concept; `npx` auto-installs into the npm cache.
- `scripts/render_segmented.py` (deleted): the old ENOSPC workaround rendered
  Remotion in three manual frame-range segments (`--frames=a-b`) and concatenated
  with ffmpeg. The `hyperframes render` CLI has no frame-range flag, so this
  doesn't have a like-for-like port — but it also doesn't need one: `hyperframes
  render` natively supports `--frames-cache-dir <dir>` (relocate the extracted-
  frame cache off a small system partition) and `--low-memory-mode` (single
  worker, screenshot capture, no calibration), which cover the same "long
  render exhausts local disk/RAM" problem the segmented script existed for.
- `docs/catalog/features/cover-remotion.md` keeps its filename (many other docs
  link to it by that path) but its content describes the current HyperFrames
  camera-motion / A-Roll Text Motion System design — the filename is a historical
  label, not a claim about the current engine.

## Validation performed

- `uv run pytest`: 170 passed, 2 pre-existing failures unrelated to this migration
  (`test_cutaway_framework.py::test_suggest_cutaways_on_temp_episode`,
  `test_gather.py::test_gather_evidence_missing_plan_writes_nothing_useful`, both
  failing identically on `main`).
- `uv run ruff check .`: no new findings in `hf_template.py` (0 findings) or in
  files this migration touches beyond what was already present in the
  pre-existing `cover/*.py` modules (untouched logic, only renamed references).
- `npx hyperframes lint` / `check` against a hand-built placeholder
  `timeline.json` rendered through `write_hf_composition`: Runtime, Layout,
  Motion, and Contrast checks all pass; the only lint errors are
  `missing_local_asset`/`audio_src_not_found` for the placeholder's fake
  `assets/cam.mp4` path, which doesn't exist in this sandbox — expected, not a
  composition defect.
- **Not validated**: an actual `hyperframes render` to a real MP4. This sandbox
  has no `ffmpeg` binary at all (`ffmpeg -version` → not found), so no render
  path — Remotion's old one or HyperFrames' new one — can execute here. The
  Python pipeline's own `ae doctor` check would likewise fail on this box. This
  should be re-run in an environment with `ffmpeg` before considering the
  compose stage fully proven end-to-end.
