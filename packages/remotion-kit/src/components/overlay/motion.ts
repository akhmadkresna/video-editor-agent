/**
 * Deterministic ports of the A-Roll Text Motion System keyframes
 * (`styles/aroll-text-motion/_ds/tokens/motion.css`).
 *
 * The DS source drives everything with CSS `animation`, which is wall-clock
 * based. Remotion renders frames in parallel across workers, so a wall-clock
 * animation produces a different picture per run. Every recipe here is a pure
 * function of `frame` — same frame in, same value out, always.
 *
 * Recipes follow the handoff spec §5. Note `easing.pop = [0.2,1.4,0.4,1]` has
 * y1 = 1.4 (outside [0,1]) and must NOT go through `Easing.bezier`, which
 * clamps/throws — the overshoot comes from the 3-stop interpolate in `popIn`.
 */
import { Easing, interpolate } from "remotion";

/** `--ease-out` cubic-bezier(.16,1,.3,1) — safe for Easing.bezier. */
export const EASE_OUT = Easing.bezier(0.16, 1.0, 0.3, 1);
/** `--ease-in-out` cubic-bezier(.65,0,.35,1). */
export const EASE_IN_OUT = Easing.bezier(0.65, 0, 0.35, 1);

export function msToFrames(ms: number, fps: number): number {
  return (ms / 1000) * fps;
}

const clamp01 = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/**
 * `ov-pop-in` — the signature entrance for every hero/punch element.
 * scale .72 → 1.04 → 1 (overshoot kept), opacity over the first 30%,
 * translateY 6 → 0.
 */
export function popIn(
  frame: number,
  fps: number,
  opts: { durMs: number; delayMs?: number; risePx?: number },
): { scale: number; opacity: number; translateY: number } {
  const f = frame - msToFrames(opts.delayMs ?? 0, fps);
  const d = Math.max(1, msToFrames(opts.durMs, fps));
  return {
    scale: interpolate(f, [0, 0.7 * d, d], [0.72, 1.04, 1], clamp01),
    opacity: interpolate(f, [0, 0.3 * d], [0, 1], clamp01),
    translateY: interpolate(f, [0, d], [opts.risePx ?? 6, 0], {
      ...clamp01,
      easing: EASE_OUT,
    }),
  };
}

/** `ov-slide-up` — 28px rise + fade. CaptionLine / lower_third / chapter. */
export function slideUp(
  frame: number,
  fps: number,
  opts: { durMs: number; delayMs?: number; fromPx?: number },
): { opacity: number; translateY: number } {
  const f = frame - msToFrames(opts.delayMs ?? 0, fps);
  const d = Math.max(1, msToFrames(opts.durMs, fps));
  return {
    opacity: interpolate(f, [0, d], [0, 1], clamp01),
    translateY: interpolate(f, [0, d], [opts.fromPx ?? 28, 0], {
      ...clamp01,
      easing: EASE_OUT,
    }),
  };
}

/** `ov-bounce-in` — CTATag only. 18px → -4px → 0, scale .9 → 1.02 → 1. */
export function bounceIn(
  frame: number,
  fps: number,
  opts: { durMs: number; delayMs?: number },
): { scale: number; opacity: number; translateY: number } {
  const f = frame - msToFrames(opts.delayMs ?? 0, fps);
  const d = Math.max(1, msToFrames(opts.durMs, fps));
  return {
    translateY: interpolate(f, [0, 0.6 * d, d], [18, -4, 0], clamp01),
    scale: interpolate(f, [0, 0.6 * d, d], [0.9, 1.02, 1], clamp01),
    opacity: interpolate(f, [0, 0.4 * d], [0, 1], clamp01),
  };
}

/** `ov-fade`. */
export function fadeIn(
  frame: number,
  fps: number,
  opts: { durMs: number; delayMs?: number },
): number {
  const f = frame - msToFrames(opts.delayMs ?? 0, fps);
  return interpolate(f, [0, Math.max(1, msToFrames(opts.durMs, fps))], [0, 1], {
    ...clamp01,
    easing: EASE_OUT,
  });
}

/** `ov-underline` — scaleX 0 → 1 from the left edge. */
export function underlineSweep(
  frame: number,
  fps: number,
  opts: { durMs: number; delayMs?: number },
): number {
  const f = frame - msToFrames(opts.delayMs ?? 0, fps);
  return interpolate(f, [0, Math.max(1, msToFrames(opts.durMs, fps))], [0, 1], {
    ...clamp01,
    easing: EASE_OUT,
  });
}

/** `ov-blink` — hard on/off (steps(1)), not a fade. Returns 1 or 0. */
export function blinkStep(
  frame: number,
  fps: number,
  opts: { periodMs?: number; delayMs?: number },
): number {
  const f = frame - msToFrames(opts.delayMs ?? 0, fps);
  if (f < 0) return 1;
  const half = Math.max(1, msToFrames((opts.periodMs ?? 1100) / 2, fps));
  return Math.floor(f / half) % 2 === 0 ? 1 : 0;
}

/**
 * `ov-float` — ±amplitude sine drift, starting only after `delayMs` so the
 * entrance settles first. Spec: apply only when dwell > 3s.
 */
export function floatY(
  frame: number,
  fps: number,
  opts: { periodMs?: number; amplitudePx?: number; delayMs?: number },
): number {
  const f = frame - msToFrames(opts.delayMs ?? 0, fps);
  if (f <= 0) return 0;
  const period = Math.max(1, msToFrames(opts.periodMs ?? 2600, fps));
  return -Math.sin((f / period) * Math.PI * 2) * (opts.amplitudePx ?? 7);
}

/**
 * `ov-drip` — StatCallout's sand-drip particle. Returns a 0..1 phase; the
 * caller maps it to translateY and an opacity ramp. Spec §5 asks for 3
 * instances at staggered offsets, hence `offsetMs`.
 */
export function dripPhase(
  frame: number,
  fps: number,
  opts: { periodMs?: number; offsetMs?: number },
): number {
  const period = Math.max(1, msToFrames(opts.periodMs ?? 1400, fps));
  const f = frame + msToFrames(opts.offsetMs ?? 0, fps);
  return ((f % period) + period) % period / period;
}

/** Opacity ramp for a drip/flow particle: fades in at the start, out at the end. */
export function particleOpacity(phase: number): number {
  return interpolate(phase, [0, 0.15, 0.9, 1], [0, 1, 1, 0], clamp01);
}

/** `ov-flow-x` / `ov-flow-y` — FlowSteps connector dot. 0..1 along the link. */
export function flowDotPhase(
  frame: number,
  fps: number,
  opts: { periodMs?: number; delayMs?: number },
): number {
  const period = Math.max(1, msToFrames(opts.periodMs ?? 1100, fps));
  const f = frame - msToFrames(opts.delayMs ?? 0, fps);
  if (f < 0) return 0;
  return (f % period) / period;
}

/** `ov-draw-line` — stroke-dashoffset 1 → 0 as a 0..1 progress. */
export function drawLine(
  frame: number,
  fps: number,
  opts: { durMs: number; delayMs?: number },
): number {
  const f = frame - msToFrames(opts.delayMs ?? 0, fps);
  return interpolate(f, [0, Math.max(1, msToFrames(opts.durMs, fps))], [0, 1], {
    ...clamp01,
    easing: EASE_OUT,
  });
}

/**
 * `ov-march` — marching ants after the line is drawn. Returns a dashoffset in
 * px, looping over `periodMs`.
 */
export function marchOffset(
  frame: number,
  fps: number,
  opts: { periodMs?: number; distancePx?: number; delayMs?: number },
): number {
  const f = frame - msToFrames(opts.delayMs ?? 0, fps);
  if (f < 0) return 0;
  const period = Math.max(1, msToFrames(opts.periodMs ?? 900, fps));
  return -((f % period) / period) * (opts.distancePx ?? 22);
}

/** Count-up progress 0..1, cubic ease-out (matches the DS's `1-(1-p)^3`). */
export function countUp(
  frame: number,
  fps: number,
  opts: { countMs: number; delayMs?: number },
): number {
  const f = frame - msToFrames(opts.delayMs ?? 0, fps);
  const p = interpolate(f, [0, Math.max(1, msToFrames(opts.countMs, fps))], [0, 1], clamp01);
  return 1 - Math.pow(1 - p, 3);
}

/**
 * `ov-grid-pulse` — AnnotationGrid opacity.
 * Period is 4.5s from `AnnotationGrid.jsx`; spec §5 says "2s sine", but §1 is
 * explicit that the JSX is the source of truth where they disagree.
 */
export function gridPulse(
  frame: number,
  fps: number,
  opts: { base?: number; peak?: number; periodMs?: number },
): number {
  const period = Math.max(1, msToFrames(opts.periodMs ?? 4500, fps));
  const s = 0.5 + 0.5 * Math.sin((frame / period) * Math.PI * 2);
  return (opts.base ?? 0.14) + ((opts.peak ?? 0.32) - (opts.base ?? 0.14)) * s;
}

/**
 * Exit fade. The DS has no exit keyframe of its own (§5) — every kind fades
 * over `exitMs`. `exitStartSec` is computed upstream by
 * `cover/overlay_schedule.py`; without it we fall back to the tail.
 */
export function exitFade(
  frame: number,
  fps: number,
  opts: { durationSec: number; exitStartSec?: number; exitMs: number },
): number {
  const exitFrames = Math.max(1, msToFrames(opts.exitMs, fps));
  const totalFrames = opts.durationSec * fps;
  const startFrame =
    opts.exitStartSec != null
      ? opts.exitStartSec * fps
      : Math.max(0, totalFrames - exitFrames);
  return interpolate(frame, [startFrame, startFrame + exitFrames], [1, 0], clamp01);
}

/**
 * Per-word entrance delay. Spec §5 asks for `i · wordStaggerMs` with the total
 * clamped to 540ms past 6 words.
 *
 * Clamping the *delay* (`min(i * 90, 540)`) would make every word from the 6th
 * onward fire on the same frame — visibly worse on a 12-word line than no
 * stagger at all. Compress the per-word step instead, so the whole line still
 * lands within the budget while every word stays distinct.
 */
export function wordStaggerDelay(
  index: number,
  opts: { wordStaggerMs: number; wordCount?: number; maxTotalMs?: number },
): number {
  const maxTotal = opts.maxTotalMs ?? 540;
  const gaps = Math.max(1, (opts.wordCount ?? 0) - 1);
  const step = Math.min(opts.wordStaggerMs, maxTotal / gaps);
  return index * step;
}
