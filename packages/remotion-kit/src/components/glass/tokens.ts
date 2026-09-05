/**
 * Overlay — A-Roll Text Motion System tokens.
 *
 * White ink on continuous A-roll. No panels/cards/plates/backdrop-filter.
 * Max surface = `fillWhite12` flat tint (FlowSteps unreached chip only).
 * Face oval stays clear; one primary + one optional secondary on screen.
 *
 * Source of record: styles/aroll-text-motion/overlays.style.yaml +
 * styles/aroll-text-motion/_ds/tokens/*.css. Mirrors
 * src/agentic_editor/cover/style_load.py DEFAULT_OVERLAYS and
 * types.ts DEFAULT_OVERLAY_STYLE.
 *
 * Folder name `glass/` is legacy — no blur/backdrop-filter left. Not
 * renamed to avoid churn.
 */
import { sansFamily, monoFamily } from "./fonts";

export const color = {
  ink: "#ffffff",
  inkMuted: "rgba(255,255,255,0.68)",
  inkFaint: "rgba(255,255,255,0.4)",
  /** FlowSteps unreached chip ONLY — flat tint, no blur. */
  fillWhite12: "rgba(255,255,255,0.12)",
  lineHair: "rgba(255,255,255,0.28)",
  /** Terminal window behind the `code` kind — unchanged, out of scope. */
  terminalBg: "#141312",
  terminalHeaderBg: "#1e1c19",
  terminalBorder: "#333029",
} as const;

/** cqh ≈ % of frame height. */
export const sizeBand = {
  heroCqh: 22,
  bodyCqh: 12,
  subCqh: 7.0,
  metaCqh: 3.2,
  labelCqh: 2.4,
  eyebrowCqh: 2.0,
} as const;

export const density = { maxPrimary: 1, maxSecondary: 1 } as const;

export const font = {
  sans: `'${sansFamily}', Helvetica, Arial, -apple-system, 'Segoe UI', sans-serif`,
  mono: `'${monoFamily}', 'SF Mono', Menlo, monospace`,
} as const;

export const weight = { hero: 800, body: 600 } as const;

export const letterSpacing = {
  tight: "-0.02em",
  normal: "0em",
  wide: "0.04em",
  caps: "0.14em",
} as const;

export const lineHeight = { tight: 0.98, snug: 1.15, normal: 1.4 } as const;

export const textShadow = "0 2px 18px rgba(0,0,0,.55)";

export const radius = { sm: 6, md: 10, pill: 999 } as const;
export const strokeW = 2;

/**
 * Cubic-bezier control points. `pop` overshoots (y2 = 1.4) — a token of
 * record only. Do NOT feed it to `Easing.bezier` (it clamps / throws);
 * the overshoot comes from a 3-stop `interpolate(f,[0,.7d,d],[.72,1.04,1])`.
 */
export const easing = {
  pop: [0.2, 1.4, 0.4, 1] as const,
  out: [0.16, 1.0, 0.3, 1] as const,
};

// The v7 renderer that needed `duration` pinned at these values
// (GlassOverlays.tsx punchSpring/sweep) is deleted — only `code` and
// `illustration` remain there now, neither of which reads this token. The
// A-Roll Text Motion System components (`components/overlay/`) read
// `theme.durFast/durBase/durSlow`, which resolve through
// `OverlayStyle.motion` (style-pack config) and fall back to these values
// only when that's absent. Safe to carry the DS's own values now.
export const duration: { fast: number; base: number; slow: number } = {
  fast: 220,
  base: 420,
  slow: 680,
};
export const wordStaggerMs = 90;
export const countMs = 900;
export const exitMs = 340;

/** Small deterministic jitter (not Math.random — renders stay frame-
 * deterministic). Used by AnnotationGrid corner triangles. */
export function jitterDeg(id: string, range = 0.6): number {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  return ((h % 1000) / 1000) * range * 2 - range;
}
