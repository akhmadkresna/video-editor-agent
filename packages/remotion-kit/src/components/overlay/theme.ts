/**
 * Resolves an `OverlayStyle` (style-pack config, arriving via
 * `timeline.presentation.overlays`) into concrete values every overlay
 * primitive can read, falling back to `glass/tokens.ts`.
 *
 * This is the single place style-pack config and the TS tokens are
 * reconciled. Before this existed the two diverged silently: the glass
 * kinds never received `styleTokens` at all and hardcoded px sizes, so the
 * whole `sizeBands` / `motion` / `type` / `shape` config was dead weight.
 */
import { DEFAULT_OVERLAY_STYLE, type OverlayStyle, type OverlayZone } from "../../types";
import {
  color,
  duration,
  countMs as tokenCountMs,
  exitMs as tokenExitMs,
  font,
  letterSpacing,
  lineHeight,
  radius,
  sizeBand,
  strokeW as tokenStrokeW,
  textShadow as tokenTextShadow,
  weight,
  wordStaggerMs as tokenWordStaggerMs,
} from "../glass/tokens";

const SANS_FALLBACK = `Helvetica, Arial, -apple-system, 'Segoe UI', sans-serif`;
const MONO_FALLBACK = `'SF Mono', Menlo, monospace`;

/** A family *name* from config becomes a full stack; absent → token stack. */
function fontStack(name: string | undefined, tokenStack: string, fallback: string): string {
  const trimmed = (name || "").trim();
  if (!trimmed) return tokenStack;
  return `'${trimmed}', ${fallback}`;
}

export type SizeBands = {
  heroCqh: number;
  bodyCqh: number;
  subCqh: number;
  metaCqh: number;
  labelCqh: number;
  eyebrowCqh: number;
};

export type OverlayTheme = {
  ink: string;
  inkMuted: string;
  inkFaint: string;
  fillWhite12: string;
  lineHair: string;

  fontSans: string;
  fontMono: string;
  weightHero: number;
  weightBody: number;
  lsTight: string;
  lsCaps: string;
  lhTight: number;
  textShadow: string;

  radiusSm: number;
  radiusMd: number;
  radiusPill: number;
  strokeW: number;

  /** ms */
  durFast: number;
  durBase: number;
  durSlow: number;
  wordStaggerMs: number;
  countMs: number;
  exitMs: number;

  bands: SizeBands;

  chapter: NonNullable<OverlayStyle["chapter"]>;
  emphasis: NonNullable<OverlayStyle["emphasis"]>;
  diagram: NonNullable<OverlayStyle["diagram"]>;
  callout: NonNullable<OverlayStyle["callout"]>;
  chip: NonNullable<OverlayStyle["chip"]>;
  grid: { enabled: boolean; density: number; opacity: number };
  zones: OverlayZone[];
};

const D = DEFAULT_OVERLAY_STYLE;

export function resolveTheme(style?: OverlayStyle): OverlayTheme {
  const s = style || {};
  const bands = s.sizeBands || {};
  const motion = s.motion || {};
  const type = s.type || {};
  const shape = s.shape || {};
  const grid = s.grid || {};

  return {
    ink: s.ink ?? D.ink ?? color.ink,
    inkMuted: s.inkMuted ?? D.inkMuted ?? color.inkMuted,
    inkFaint: s.inkFaint ?? D.inkFaint ?? color.inkFaint,
    fillWhite12: shape.fillWhite12 ?? D.shape?.fillWhite12 ?? color.fillWhite12,
    lineHair: shape.lineHair ?? D.shape?.lineHair ?? color.lineHair,

    fontSans: fontStack(s.fonts?.sans, font.sans, SANS_FALLBACK),
    fontMono: fontStack(s.fonts?.mono, font.mono, MONO_FALLBACK),
    weightHero: type.weightHero ?? D.type?.weightHero ?? weight.hero,
    weightBody: type.weightBody ?? D.type?.weightBody ?? weight.body,
    lsTight: type.lsTight ?? D.type?.lsTight ?? letterSpacing.tight,
    lsCaps: type.lsCaps ?? D.type?.lsCaps ?? letterSpacing.caps,
    lhTight: type.lhTight ?? D.type?.lhTight ?? lineHeight.tight,
    textShadow: type.textShadow ?? D.type?.textShadow ?? tokenTextShadow,

    radiusSm: shape.radiusSm ?? D.shape?.radiusSm ?? radius.sm,
    radiusMd: shape.radiusMd ?? D.shape?.radiusMd ?? radius.md,
    radiusPill: shape.radiusPill ?? D.shape?.radiusPill ?? radius.pill,
    strokeW: shape.strokeW ?? D.shape?.strokeW ?? tokenStrokeW,

    durFast: motion.durFast ?? D.motion?.durFast ?? duration.fast,
    durBase: motion.durBase ?? D.motion?.durBase ?? duration.base,
    durSlow: motion.durSlow ?? D.motion?.durSlow ?? duration.slow,
    wordStaggerMs: motion.wordStaggerMs ?? D.motion?.wordStaggerMs ?? tokenWordStaggerMs,
    countMs: motion.countMs ?? D.motion?.countMs ?? tokenCountMs,
    exitMs: motion.exitMs ?? D.motion?.exitMs ?? tokenExitMs,

    bands: {
      heroCqh: bands.heroCqh ?? D.sizeBands?.heroCqh ?? sizeBand.heroCqh,
      bodyCqh: bands.bodyCqh ?? D.sizeBands?.bodyCqh ?? sizeBand.bodyCqh,
      subCqh: bands.subCqh ?? D.sizeBands?.subCqh ?? sizeBand.subCqh,
      metaCqh: bands.metaCqh ?? D.sizeBands?.metaCqh ?? sizeBand.metaCqh,
      labelCqh: bands.labelCqh ?? D.sizeBands?.labelCqh ?? sizeBand.labelCqh,
      eyebrowCqh: bands.eyebrowCqh ?? D.sizeBands?.eyebrowCqh ?? sizeBand.eyebrowCqh,
    },

    chapter: { ...D.chapter, ...s.chapter },
    emphasis: { ...D.emphasis, ...s.emphasis },
    // stepSizeCqh is in the YAML + Python defaults but missing from
    // DEFAULT_OVERLAY_STYLE — keep an explicit floor so FlowSteps always sizes.
    diagram: { stepSizeCqh: 3.6, ...D.diagram, ...s.diagram },
    callout: { ...D.callout, ...s.callout },
    chip: { ...D.chip, ...s.chip },
    grid: {
      enabled: grid.enabled ?? D.grid?.enabled ?? false,
      density: grid.density ?? D.grid?.density ?? 3,
      opacity: grid.opacity ?? D.grid?.opacity ?? 0.14,
    },
    zones: s.safe?.zones ?? D.safe?.zones ?? ["left_third", "right_third", "lower_raised", "top_sparse"],
  };
}
