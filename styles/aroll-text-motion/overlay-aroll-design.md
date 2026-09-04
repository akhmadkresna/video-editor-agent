# Handoff: replace A-roll overlay style with Overlay — A-Roll Text Motion System

**Scope:** replace the entire A-roll text-overlay rendering + tokens in
`packages/remotion-kit` with the design system below. This is a swap, not a
new preset — delete the old look once the new one renders correctly.

**Out of scope — do not touch:** `MockupLayer.tsx` / `MockupLab.tsx` (chat/
diff/repo-view scenes), `CutawayLayer.tsx` + cutaway families, dialogue
captions (`CaptionLayer.tsx`), `screen_explainer`, SFX, `cover`, `radio_edit`.
None of these render overlay text; they are separate components untouched by
this change.

**Design system source:** `styles/aroll-text-motion/overlays.style.yaml`
(this handoff) ports `_ds/overlay-a-roll-text-motion-system-.../` tokens +
10 `components/overlays/*.jsx` primitives into Remotion. Read those `.jsx`
files as the source of truth — not the design system's own guide.md, which is
stale in two places (calls `IllustrationTag` a "glass pill"; it isn't).

Published design system: https://claude.ai/design/p/84d87bf7-87f4-4e94-85de-c1a395156355

---

## 1. Files to change

| File | Change |
|---|---|
| `packages/remotion-kit/src/components/glass/tokens.ts` | Replace token values per §2. Folder name `glass/` is legacy (superseded 2026-08 style, zero blur/backdrop-filter left) — keep the name, don't block on a rename. |
| `packages/remotion-kit/src/components/glass/fonts.ts` | `sansFamily = "Plus Jakarta Sans"`, `monoFamily = "IBM Plex Mono"`. Self-host under `public/fonts` (no CDN in a render). |
| `packages/remotion-kit/src/components/glass/GlassOverlays.tsx` | Replace the 8 kind renderers (`title`, `stat`, `lower_third`, `tag`, `divider`, `quote`, `code`, `illustration`) per §3 mapping. `code` is unchanged (real terminal window, out of scope). |
| `packages/remotion-kit/src/components/OverlayLayer.tsx` | Replace `OneOverlay`'s 5 kind renderers (`chapter`, `emphasis`, `diagram`, `chip`, `callout`) per §3. |
| `packages/remotion-kit/src/types.ts` | Add optional keys to `OverlayStyle` (§4), optional `at?: [number, number]` on `TimelineOverlay` (§3, `callout`/`CalloutArrow`), `"list_cycle"` to `OverlayKind` (optional new kind, §3). |
| `src/agentic_editor/cover/style_load.py` | Replace `DEFAULT_OVERLAYS` dict with §2 values (mirrors `types.ts`'s `DEFAULT_OVERLAY_STYLE`). |
| `styles/tutorial/style.md` (and any other style pack with an `overlays:` fence) | Replace the `overlays:` YAML block with `styles/aroll-text-motion/overlays.style.yaml`'s content. |
| `packages/remotion-kit/src/components/CtaBadge.tsx` | Replace with `CTATag` port (§3). |

Everything else in `Timeline`/`cover.json` authoring is unchanged — same
fields, same whitelist, no `remap.py` change.

---

## 2. Token replacement (`glass/tokens.ts` + `style_load.py` DEFAULT_OVERLAYS)

```ts
export const color = {
  ink: "#ffffff",
  inkMuted: "rgba(255,255,255,0.68)",
  inkFaint: "rgba(255,255,255,0.4)",
  fillWhite12: "rgba(255,255,255,0.12)",   // FlowSteps unreached chip ONLY — flat tint, no blur
  lineHair: "rgba(255,255,255,0.28)",
  terminalBg: "#141312", terminalHeaderBg: "#1e1c19", terminalBorder: "#333029", // unchanged (code kind)
};

export const sizeBand = { heroCqh: 22, bodyCqh: 12, subCqh: 7.0, metaCqh: 3.2, labelCqh: 2.4, eyebrowCqh: 2.0 };
export const density = { maxPrimary: 1, maxSecondary: 1 };

export const font = {
  sans: `'Plus Jakarta Sans', Helvetica, Arial, -apple-system, 'Segoe UI', sans-serif`,
  mono: `'IBM Plex Mono', 'SF Mono', Menlo, monospace`,
};

export const weight = { hero: 800, body: 600 };
export const letterSpacing = { tight: "-0.02em", normal: "0em", wide: "0.04em", caps: "0.14em" };
export const lineHeight = { tight: 0.98, snug: 1.15, normal: 1.4 };
export const textShadow = "0 2px 18px rgba(0,0,0,.55)";

export const radius = { sm: 6, md: 10, pill: 999 };
export const strokeW = 2;

export const easing = { pop: [0.2, 1.4, 0.4, 1], out: [0.16, 1.0, 0.3, 1] };
export const duration = { fast: 220, base: 420, slow: 680 };
export const wordStaggerMs = 90;
export const countMs = 900;
export const exitMs = 340;
```

`toneBorderStyle()` and the `Tone` type: **delete**. The design system has no
tone axis — `tone` on `TimelineOverlay` stays in the schema (don't break old
`cover.json` files) but renders as a no-op.

`jitterDeg()`: keep, still useful for the `AnnotationGrid` corner triangles if
you use it.

---

## 3. Kind → component mapping

Port each design-system `.jsx` (from `components/overlays/*/​*.jsx`, converting
motion per §5) into `glass/` as a Remotion component, then wire it in as
below. Field mapping is preserved exactly — no schema change needed for these.

| kind | renders as | fields | placement notes |
|---|---|---|---|
| `title` | `PunchWord` size `xl` | `text`→text, `kicker`→eyebrow, `accent`→2nd `PunchWord` line, same size | both lines share one continuous word-stagger |
| `emphasis` | `PunchWord` size `lg` | `text`→text | `underline` from style; `cursor` only if line ends mid-thought |
| `quote` | `PunchWord` size `md` + `CaptionLine` | `text`→PunchWord.text, `kicker`→CaptionLine.speaker | attribution enters `durationBase` after quote settles |
| `stat` | `StatCallout` | `value`→value, `title`→eyebrow, `sourceLabel`→meta line | counts 0→value over `countMs`; sand-drip runs the whole dwell |
| `callout` | `StatCallout` if `value` set, else `CalloutArrow` | `value`/`sourceLabel` as above; `text`→CalloutArrow.label | CalloutArrow needs a target — add `at?: [x,y]` (0–1 of frame); absent → anchor to zone edge, point at frame center-third; **suppress on full-cam** (nothing to annotate) |
| `diagram` | `FlowSteps` | `steps[]`→steps[].label, `stepAtSec[]`→activeIndex | `direction: vertical` when `maxWidthCqw ≤ 40`; reached chip = solid white/ink text, unreached = `fillWhite12` + hairline; each connector runs a traveling glow dot (1.1s loop) |
| `chapter` | `ChapterMarker` | trailing 2-digit number in `kicker`→number, `title`→title | `corner` from `zone`: `left_third`→top-left, `right_third`→top-right |
| `divider` | `ChapterMarker` | same as `chapter` | drop the old "ghost numeral" background — the corner badge is the numeral now |
| `chip` | `IllustrationTag` | `text`→label, `note:"icon:<lucide-name>"`→icon | bare white Lucide glyph + punch-md word, **no pill, no fill**; `corner` from `zone`; floats ±7px after entrance if dwell > 3s |
| `tag` | `IllustrationTag` (no icon) | `text`→label | same, floats |
| `lower_third` | `CaptionLine` | `text`→speaker, `title`→text | drops `steps` tag row (DS has none) — if it matters, emit a separate `chip` beat instead |
| `code` | unchanged (`CodeSnippet`) | — | out of scope |
| `illustration` | unchanged (bespoke illustrations) | — | restyle only: swap font/ink tokens, no new illustrations |
| CTA layer | `CTATag` replaces `CtaBadge.tsx` | `label`, `position`→anchor | `variant:"solid"` is the one inverted element (white fill, ink text); `outline` = 2px white border, bounce-in |
| (optional new kind) `list_cycle` | `ListCycle` | `text`→prefix, `steps[]`→items | "we do: [rotating]" pattern, self-advances every `interval`ms (default 1400) |
| (optional, opt-in per beat) `note:"grid:3"` | `AnnotationGrid` | — | full-bleed dashed rule-of-thirds backdrop under the beat; off by default |

Density (1 primary + 1 secondary), face-oval-clear, and zone rotation are
unchanged — this is a visual swap of the renderer, not a placement rewrite.
`AnnotationGrid`/CTA don't count against density.

---

## 4. New optional `OverlayStyle` keys (`types.ts`)

All optional — old `cover.json`/style packs without them still work.

```ts
sizeBandsExt?: { subCqh?: number; labelCqh?: number; eyebrowCqh?: number };
motion?: { easePop?: number[]; easeOut?: number[]; durFast?: number; durBase?: number; durSlow?: number; wordStaggerMs?: number; countMs?: number; exitMs?: number };
type?: { weightHero?: number; weightBody?: number; lsTight?: string; lsCaps?: string; lhTight?: number; textShadow?: string };
shape?: { radiusPill?: number; radiusSm?: number; radiusMd?: number; strokeW?: number; fillWhite12?: string; lineHair?: string };
grid?: { enabled?: boolean; density?: number; opacity?: number };
diagram: { ...; connector?: "traveling_dot" };
chip: { ...; iconEm?: number; float?: boolean };
```

And on `TimelineOverlay`: `at?: [number, number]` (callout target),
`"list_cycle"` added to `OverlayKind` if you're taking that optional kind.

---

## 5. Motion port (CSS keyframes → deterministic Remotion)

The `.jsx` sources use CSS `@keyframes` driven by wall-clock time — **do not
use them as-is**, a frame-parallel render would produce different frames each
run. Convert every one to `useCurrentFrame()` + `interpolate`/`spring`.
ms→frames: `frames = ms/1000 * fps`.

| source keyframe | used by | deterministic version |
|---|---|---|
| `ov-pop-in` (420ms, ease-pop) | every hero/punch entrance | scale `interpolate(f,[0,.7d,d],[0.72,1.04,1])`, opacity `[0,.3d]→[0,1]`, translateY 6→0; keep the overshoot |
| word stagger (90ms) | `PunchWord`, `title`, `quote` | offset word i by `i·2.7f`; clamp total stagger to 540ms past 6 words |
| `ov-slide-up` (28px) | `CaptionLine`, `lower_third` | translateY 28→0 + fade over `durFast` |
| `ov-bounce-in` | `CTATag` only | 3-stop interpolate 18px→-4px→0, scale .9→1.02→1 |
| `ov-underline` (680ms) | `emphasis` underline | scaleX 0→1 from left, delay `words·90+120ms` |
| `ov-blink` (1.1s steps) | `PunchWord cursor` | `Math.floor(f/(0.55·fps)) % 2`, hard step |
| `ov-flow-x`/`ov-flow-y` (1.1s) | `FlowSteps` connector | one glowing dot per connector, `interpolate(phase,[0,1],[0,len-8])`, opacity ramp at ends, delay `i·140ms` |
| `ov-draw-line` (680ms) + `ov-march` (900ms) | `CalloutArrow` | draw first (`strokeDashoffset 1→0`), then march (`-((f/fps)%0.9)/0.9·22`) |
| `ov-drip` | `StatCallout` accent | particle phase `(f/fps·1000 % 1400)/1400`, 3 offset instances |
| `ov-grid-pulse` | `AnnotationGrid` | opacity `.14↔.32` on 2s sine |
| `ov-float` (2.6s, 7px) | `tag`/`chip` | ±7px sine after entrance, only if dwell > 3s |
| count-up | `StatCallout` | `interpolate(f,[0,countMs],[0,value])` ease-out; format with episode locale |
| exit | all kinds | fade over `exitMs` (340ms) — the design system has no exit keyframe of its own |

Something should always be moving inside an on-screen beat (drip / traveling
dot / marching pointer / cursor / float) — don't let a beat go fully static
once its entrance settles.

---

## 6. Selection logic (`overlay_suggest.py`) — no change required

The kind→component mapping in §3 is field-preserving, so the existing
suggester's output renders correctly with zero change to
`overlay_suggest.py`. Leave it as-is unless you also want to change *which*
kind gets picked for a given beat — that's a separate, optional task.

---

## 7. Guardrails (apply to every ported component)

- Text is white (`#ffffff`) only. No hue, anywhere, for any reason.
- No panels/cards/plates/frosted surfaces. Max surface = `fillWhite12` flat
  tint (FlowSteps unreached chip only). No `backdrop-filter` in this layer.
- Face oval stays clear; zone rotation (`left_third`/`right_third`/
  `lower_raised`/`top_sparse`) unchanged.
- One primary + one optional secondary on screen at a time.
- Icons: Lucide only (already wired for `IllustrationTag`), no hand-drawn
  icons. The 7 bespoke `illustration` scenes are restyled (font/ink), not
  replaced.
- `CalloutArrow.jsx` sizes its label with `var(--fs-punch-sm)`, undefined in
  the source tokens (silently inherits) — use `sizeBand.labelCqh` when
  porting, don't carry the bug over.

---

## 8. Suggested order of work

1. Token + font swap (§2) — biggest visual delta for the least risk, both
   `glass/tokens.ts` and `style_load.py` in the same commit.
2. Port `PunchWord`, `CaptionLine`, `ChapterMarker`, `CTATag` (simplest
   motion, covers `title`/`emphasis`/`quote`/`lower_third`/`chapter`/
   `divider` + the CTA layer).
3. Port `StatCallout`, `IllustrationTag` (adds continuous drip/float).
4. Port `FlowSteps`, `CalloutArrow` (connector motion, `at` field for callout
   targeting).
5. `AnnotationGrid` + `ListCycle` — optional, low-risk additions last.
6. Delete old `GlassOverlays.tsx`/`OverlayLayer.tsx` renderers and
   `toneBorderStyle`/`Tone` once every kind above renders from the new
   components — this is a replacement, remove the old code rather than
   leaving it dead.
