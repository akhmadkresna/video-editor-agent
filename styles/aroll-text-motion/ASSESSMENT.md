# Assessment — A-Roll Text Motion System handoff vs. the live repo

Reviewed `overlay-aroll-design.md` + the design-system source (received
2026-09-04, vendored to `_ds/`) against `packages/remotion-kit` +
`src/agentic_editor/cover`. Verdict: **green — small, clean system, very
portable. ~10 primitives × 10–25 lines each. No blocker; ~8 concrete
decisions, all minor.**

## Source review (files received)

`_ds/components/overlays/*/​*.jsx` — the 10 primitives. Each is a thin
styled `<div>` tree using CSS `var(--*)` tokens (`_ds/tokens/*.css`) and
CSS `@keyframes` (`_ds/tokens/motion.css`). Porting = swap `var(--*)` for
`glass/tokens.ts` values (§2) + convert every `animation:` to
`useCurrentFrame()`/`interpolate` (§5). Structure ports 1:1.

Confirmed against source:
- `IllustrationTag` is **bare icon + word, no pill/fill** (handoff was
  right; the DS `guide.md`/`readme` "glass pill" wording is stale).
- `CalloutArrow` really does reference undefined `--fs-punch-sm` (§7 bug).
- `FlowSteps` unreached chip = `glass-white-12` + `line-hair` border;
  reached = solid white pill, ink text + ink number badge (inverted).
- `CTATag` solid = white fill + `ink-950` text + drop shadow — the one
  inverted element, **no hue** (SKILL.md's "one accent color, CTA only"
  is stale; readme + handoff + JSX all say white/ink).
- `list_cycle`/`AnnotationGrid` are genuinely optional and standalone.

---

## 1. Coverage — every kind is mapped ✓

Current `OverlayKind` = 13: `title stat lower_third tag divider quote code
illustration chapter emphasis diagram chip callout` (+ the CTA layer).
§3 maps all of them:

| Renderer today | New component | Notes |
|---|---|---|
| `GlassOverlay` — `title` `stat` `lower_third` `tag` `divider` `quote` `code` `illustration` | `PunchWord` · `StatCallout` · `CaptionLine` · `IllustrationTag` · `ChapterMarker` · `PunchWord`+`CaptionLine` · **unchanged** · **restyle-only** | 6 of 8 change |
| `OneOverlay` (in `OverlayLayer.tsx`) — `chapter` `emphasis` `diagram` `chip` `callout` | `ChapterMarker` · `PunchWord` · `FlowSteps` · `IllustrationTag` · `StatCallout`\|`CalloutArrow` | all 5 change |
| `CtaBadge.tsx` | `CTATag` | file replaced |
| — | `ListCycle` (opt kind `list_cycle`), `AnnotationGrid` (opt `note:"grid:3"`) | new, opt-in |

No orphans. `code` + `illustration` stay (restyle only).

---

## 2. What lands cleanly

- **Field mapping is preserved** → `cover/remap.py build_timeline_overlays`
  and `cover/overlay_suggest.py` need **zero change** (handoff §6 confirms;
  I verified the field names against `TimelineOverlay`).
- **`tone` / `Tone` / `toneBorderStyle`** — delete the type + helper; keep
  `tone` in the `TimelineOverlay` schema as a no-op so old `cover.json`
  still parses. Clean.
- **Tokens replace in 3 mirrored places** — `glass/tokens.ts`,
  `types.ts DEFAULT_OVERLAY_STYLE`, `style_load.py DEFAULT_OVERLAYS`. Plus
  the `overlays:` fence in **4** style packs (tutorial, evidence, social,
  mockup), not just tutorial — `styles/aroll-text-motion/overlays.style.yaml`
  is the drop-in.
- **Fonts exist** — `@remotion/google-fonts/PlusJakartaSans` and
  `/IBMPlexMono` are both in `node_modules`. No download needed.
- **Motion determinism** — §5 is precise. The current renderers are
  already `useCurrentFrame`/`interpolate`/`spring`; the "no CSS keyframes"
  warning applies to the DS `.jsx` sources, not repo code.

---

## 3. Decisions (all minor — pick before / during commit 1)

### 3.1 Sizing — DS `clamp(px,vw,px)` → repo `cqh` (already resolved)

DS `--fs-punch-xl: clamp(48px,9vw,132px)` etc. The repo overlay layer is
`cqh`-based. Handoff §2 already translated to `sizeBand` cqh values; the
port uses the **style pack's per-kind `*SizeCqh`** (`heroCqh 22` for
punch-xl, `emphasis.sizeCqh` for lg, `bodyCqh 12` for md), not the DS
pixel numbers. `overlays.style.yaml` matches. No action.

### 3.2 Font loading — ignore "self-host under `public/fonts`"

`glass/fonts.ts` already loads via `@remotion/google-fonts`, which gates
the render (`delayRender`/`continueRender`) — the established pattern
(also used by `components/mockup/fonts.ts`). Keep it:
`loadFont from "@remotion/google-fonts/PlusJakartaSans"` +
`/IBMPlexMono`. The "self-host, no CDN" line is a DS-side assumption that
doesn't match this repo. **Confirm.**

### 3.3 Size tokens `xl` / `lg` / `md` → per-kind `*SizeCqh`

§3 says `title` = `PunchWord` size `xl`, `emphasis` = `lg`, `quote` =
`md`. But `social` overrides sizes hard (`emphasis.sizeCqh: 5.2` vs
tutorial's `22`) so its MG fits the top bar. The port **must** read the
style pack's per-kind `*SizeCqh` (falling back to `sizeBand.heroCqh` etc.),
not hardcode `xl/lg/md`. Define the map:
`xl→heroCqh, lg→emphasis.sizeCqh, md→~bodyCqh`.

### 3.4 `sizeBands` shape — widen, don't add `sizeBandsExt`

`OverlayStyle.sizeBands` today = `{heroCqh, bodyCqh, metaCqh}`. §4
proposes a separate `sizeBandsExt?` for `sub/label/eyebrow`. Cleaner to
just widen `sizeBands` to all 6 (what `overlays.style.yaml` does) and have
`style_load.py` accept both. Pick one and make types + yaml + loader
agree.

### 3.5 `easing.pop = [0.2, 1.4, 0.4, 1]` is overshoot — not `Easing.bezier`

`y2 = 1.4` is outside [0,1]; Remotion's `Easing.bezier` clamps / can
throw. The overshoot must come from the **keyframe recipe** §5 already
specifies (`interpolate(f,[0,.7d,d],[0.72,1.04,1])`), not from feeding the
bezier to an easing fn. Keep `easePop` in tokens as a record, don't wire
it into `Easing.bezier`.

### 3.6 `CtaBadge` → `CTATag` — preserve the letterbox-band anchor

`CtaBadge.tsx` has social-specific logic: when the screen is letterboxed
it anchors the badge into the top black band (`letterboxBand`). `CTATag`
must keep that path. Also: `CtaBadgeStyle` needs `variant?: "solid" |
"outline"`; `text`→`label` rename (or accept both); `Composition.tsx`
import swap.

### 3.7 `illustration` restyle — verify the 7 scenes read tokens

`illustration:<id>` (`dual_timeline`, `scale_compare`, `spec_gap`,
`car_no_map`, `compass`, `load_test`, `stadium_ticket`) — confirm each
pulls color/font from `glass/tokens.ts` rather than hardcoding, so the
"swap font/ink tokens" restyle is real and not a no-op.

### 3.8 `StatCallout` eyebrow has a dark scrim pill — drop it

DS `StatCallout` renders `eyebrow` on `background: var(--scrim-strong)`
(rgba 0,0,0,.72), `radius-sm`, `6px 14px`. That's a surface — §7 says "no
panels/plates, max = `fillWhite12`". **Recommend:** drop the bg, render
`eyebrow` as bare text + `textShadow` (like `PunchWord`'s eyebrow). Flag
if you'd rather keep the scrim for legibility.

### 3.9 Self-placement split

`CaptionLine` / `ChapterMarker` / `CTATag` self-place with
`position:absolute` + `--safe-*`. The other 6 are inline (placed by the
parent). Port: **chapter / lower_third / CTA keep self-placement**
(map `zone` → corner: `left_third→top-left`, `right_third→top-right`);
**punch / stat / flow / chip / tag / callout** go through
`OverlayLayer`'s existing `zoneBoxStyle`. Define the `zone→corner` map in
one helper.

### 3.10 `chip` / `tag` gain a Lucide icon — add `lucide-react`

Today `chip` is text-only (no icon code anywhere in the repo). §3 wants
`note:"icon:<lucide-name>"` → a Lucide glyph in `IllustrationTag`.
`lucide-react` is **not** a dep. Add it to
`packages/remotion-kit/package.json` (tree-shakes per icon), map the note
name → icon component, fall back to no-icon on an unknown name.

### 3.11 `ChapterMarker` hardcodes px

DS uses `fontSize: 34`, divider `height: 26`. Port scales via
`chapter.kickerSizeCqh` (2.4) / `titleSizeCqh` (12) or a frame-height
ratio, so it tracks the pack (social's chapter is tiny).

---

## 4. Risk & harness

Framework-wide: this is the MG layer for **every** episode in **all 4**
styles. A regression breaks tutorial + evidence + social + mockup output.

- **`ae mg-review` / `ae storyboard`** render real MG stills but need a
  full episode with `edit/cover.json`.
- **Recommend an `OverlayLab` Remotion composition** (sibling of
  `CutawayLab` / `MockupLab`) — one beat per kind, so each ported
  component is checkable in isolation, no episode needed. Not in the
  handoff; it's the safety net for the incremental order.
- `tests/` has no overlay-render tests; the field-preserving mapping means
  the Python suggester tests stay green. Add an `OverlayLab` smoke.

---

## 5. Step plan (§8, expanded — one commit per row)

DS source vendored to `_ds/` — read
`_ds/components/overlays/<name>/<Name>.jsx` while porting each row.

| # | Commit | Files | Checkpoint |
|---|---|---|---|
| 1 | tokens + fonts + config + `lucide-react` | `glass/tokens.ts`, `glass/fonts.ts`, `types.ts` (`DEFAULT_OVERLAY_STYLE` + `OverlayStyle` keys §4), `style_load.py DEFAULT_OVERLAYS`, 4× `style.md` `overlays:` ← `overlays.style.yaml`, `packages/remotion-kit/package.json` (+`lucide-react`). **Delete `toneBorderStyle`/`Tone`.** Old renderers still run on new tokens. | `tsc` + one `ae mg-review` on a scratch episode |
| 2 | `PunchWord` `CaptionLine` `ChapterMarker` `CTATag` + **`OverlayLab`** | new components in `glass/`; wire `title` `emphasis` `quote` `lower_third` `chapter` `divider`; swap `CtaBadge`→`CTATag` in `Composition.tsx` (+ `CtaBadgeStyle.variant`) | `tsc` + `OverlayLab` render + `mg-review` |
| 3 | `StatCallout` `IllustrationTag` | wire `stat`, `callout`(value), `chip`, `tag`; `chip.iconEm/float` | `tsc` + renders |
| 4 | `FlowSteps` `CalloutArrow` | wire `diagram`, `callout`(no value); `TimelineOverlay.at?: [x,y]`; `diagram.connector: traveling_dot`; suppress `CalloutArrow` on full-cam | `tsc` + renders |
| 5 | `AnnotationGrid` + `ListCycle` (optional) | `OverlayKind += "list_cycle"`; `note:"grid:3"` handling; `OverlayStyle.grid` | `tsc` + renders |
| 6 | **delete** | remove old `GlassOverlays.tsx` kind renderers + `OneOverlay`'s 5 kinds; prune `isGlassKind`/dispatch; docs: `agentic-editor/SKILL.md` rules 10/10c/11, `styles/tutorial/style.md` prose, `styles/series/claude-skill-lab/mockup-system.md` ("inherits tutorial overlay grammar" line), `docs/catalog/features/cover-remotion.md` — "Open Overlay v7" → "A-Roll Text Motion System" | full `mg-review` + real episode `ae compose` smoke; `uv run pytest` |

---

## 6. Not touched (confirmed against handoff "out of scope")

`MockupLayer.tsx` / `MockupLab.tsx` / `components/mockup/*` · `CutawayLayer`
+ `cutaway/*` · `CaptionLayer.tsx` · `screen_explainer` · SFX · `cover.py`
selection · `radio_edit`. The mockup style pack's `overlays:` block *is*
swapped (it renders through the same `<OverlayLayer>`), but no mockup
component changes.
