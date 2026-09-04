# Overlay — A-Roll Text Motion System

A design system for **text overlays on talking-head (A-roll) video** — the punch words, flowcharts, chapter markers, CTAs, captions, and floating labels that get added on top of raw footage in editing. Not a company brand kit: this is a from-scratch motion-graphics system built to spec, since no existing codebase, Figma file, or brand was attached.

**Brief given:** enrich A-roll video with text overlays offering rich variety (flowchart, punch words, illustration, chapter, CTA, etc.), rich motion, varied size/placement, and text that can float around the speaker. Overlay text color is always white. Target format: 16:9 A-roll.

**Source material** (in `uploads/`, referenced for style/motion inspiration only — not this brand):
- `Most businesses don't lack opportunity..mp4` — bold condensed sans punch words ("Sentence", "Business", "Decision"), dashed-grid/annotation motif, hourglass stat callout, flat vector illustration beat. See `frames/biz_*.png` for stills.
- `Pin di Pins by you.mp4` — black background, "we do: [rotating item]" list-cycle pattern, fixed corner logo badge, accent-color handle tag.
- `just create...blender...mp4` — could not be decoded in this environment (unsupported codec/corrupt, 64KB, 0×0 reported dimensions). Not used as a visual reference; flagging so it can be re-exported if it mattered to the brief.

## Components (`components/overlays/`)
Ten overlay primitives, each a starting point:
- **PunchWord** — bold pop-in hero word/phrase; `cursor` adds a continuously blinking type-cursor beam.
- **StatCallout** — giant animated number/stat beat with a continuous sand-drip accent above it.
- **FlowSteps** — connected step chips with marching-ant connector lines for a process/flowchart beat.
- **ChapterMarker** — corner chapter number + title.
- **CTATag** — bottom-anchored call-to-action pill.
- **CaptionLine** — bottom-third subtitle line.
- **ListCycle** — fixed word + continuously self-advancing rotating list item ("We do: ...").
- **CalloutArrow** — dashed pointer with a marching-ant line and cursor-style arrowhead, annotating a spot in frame.
- **IllustrationTag** — small glass pill (icon + word) that floats near the speaker.
- **AnnotationGrid** — full-bleed dashed rule-of-thirds grid + corner triangles, the "design canvas" backdrop seen throughout the reference clips.

## UI kit (`ui_kits/video-preview/`)
`index.html` — an interactive mock A-roll frame (silhouette speaker) with a checklist to toggle each overlay variation on/off and see how they compose together.

## Foundations (`guidelines/`)
Specimen cards for core neutrals, accent/scrim, punch/caption type scale, spacing, and entrance motion (hover a motion card to replay).

## Tokens (`tokens/`)
`colors.css`, `typography.css`, `spacing.css`, `motion.css` — imported by root `styles.css`.

## Intentional additions
No component inventory was supplied (no codebase/Figma), so the eight overlays above were authored from the brief + reference videos rather than lifted from a source.

---

## Content fundamentals
- **Voice:** short, declarative, spoken-language fragments — not full sentences. Punch words are single words or 2–3 word phrases ("Sentence", "Business", "Decision", "Let's test it for 3 Months").
- **Casing:** sentence case by default; eyebrow/label text is small-caps-style uppercase with wide letter-spacing.
- **Emoji:** none observed in source material — avoid.
- **Numbers:** used sparingly as big stat callouts (e.g. "3 Months"), not as decorative data.

## Visual foundations
- **Color:** overlay text and fills are white (`--paper-0`) only, per the brief — no accent color anywhere in the system. Everything else is neutral ink/paper grays and scrims.
- **Background:** overlays sit on top of real video, never on a flat brand background — legibility comes from `--scrim-*` gradients/dims and small glass chips (`--glass-white-12/20` + blur), not opaque cards.
- **Type:** one geometric bold sans across the whole system — heavy weight (800) for punch words, medium/semibold for captions and labels. **Font substitution flagged**: no font files were supplied, so `Plus Jakarta Sans` (Google Fonts) stands in for the rounded-geometric bold seen in the reference clips. Replace with real brand font files if available.
- **Motion:** short, snappy entrances — pop-in with overshoot (`ov-pop-in`), slide-up, fade, and a bounce-in for CTAs. Words inside a punch phrase stagger in individually (90ms). No slow easing; everything reads within ~250–450ms.
- **Shape/placement:** pill shapes for chips/CTAs/tags (`--radius-pill`); safe-zone insets (`--safe-x/top/bottom`) keep chapter markers, captions and CTAs off the frame edges and away from a centered speaker. Callouts and illustration tags are the only pieces meant to float freely around the speaker per the brief.
- **Iconography:** no icon set was supplied — **Lucide** (CDN) is used as a stand-in for `IllustrationTag`, chosen for its thin, neutral stroke that won't compete with bold type. Flagging in case the real brand has its own icon language.
- **Corner radii:** pill (999px) for chips/CTAs; small (6–10px) for rectangular labels/badges. No large rounded "cards" — this system has no card components, only floating text/label treatments.

## Index
- `styles.css`, `tokens/*.css` — global tokens (import-only entry point)
- `components/overlays/*` — 8 overlay components + prompts + `overlays.card.html`
- `ui_kits/video-preview/index.html` — interactive preview
- `guidelines/*.card.html` — 6 foundation specimen cards
- `SKILL.md` — Claude Code-compatible skill wrapper
- `frames/` — extracted stills from the uploaded reference videos (for context, not shipped assets)
