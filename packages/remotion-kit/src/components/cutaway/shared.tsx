import React from "react";
import { AbsoluteFill, Img, spring, staticFile } from "remotion";
import type {
  CutawayFamily,
  CutawayFeed,
  CutawayGlyph,
  TimelineCutaway,
} from "../../types";

export const DISPLAY = 'Syne, "Segoe UI", "Helvetica Neue", Arial, sans-serif';
export const UI = '"Instrument Sans", "Segoe UI", system-ui, sans-serif';
export const MONO =
  '"JetBrains Mono", "Roboto Mono", Consolas, ui-monospace, monospace';

/** Locked cool-mist sky accent, plus the darker ramp step for light surfaces. */
export const ACCENT = "#7dd3fc";
export const ACCENT_DEEP = "#0ea5e9";
export const REJECT = "#e11d48";

/** Public-relative asset paths go through staticFile; URLs pass straight. */
export function assetSrc(src: string): string {
  if (/^(https?:|data:|blob:)/.test(src)) return src;
  return staticFile(src);
}

export function groupDigits(n: number): string {
  const s = Math.round(Math.abs(n)).toString();
  let out = "";
  for (let i = 0; i < s.length; i++) {
    if (i > 0 && (s.length - i) % 3 === 0) out += ".";
    out += s[i];
  }
  return out;
}

/** Format a signed amount; unit defaults empty (episode brief supplies currency). */
export function formatAmount(n: number, unit = ""): string {
  const body = groupDigits(n);
  const prefix = unit ? `${unit} ` : "";
  return `${prefix}${body}`;
}

export const signed = (n: number | undefined, unit = "Rp") => {
  const v = n ?? 0;
  return `${v < 0 ? "−" : "+"} ${unit} ${groupDigits(v)}`;
};

/** @deprecated Prefer signed(n, unit) — kept for existing ledger skins. */
export const rupiah = (n: number | undefined) => `Rp ${groupDigits(n ?? 0)}`;

export function amt(n: number | undefined): number {
  return n ?? 0;
}

/**
 * True when the brief actually carries numbers. Non-numeric stories (access
 * maps, step parades) must not render a currency total.
 */
export function hasNumericValues(
  feeds: CutawayFeed[],
  opening = 0,
): boolean {
  if (opening) return true;
  return feeds.some((f) => (f.amount ?? 0) !== 0);
}

export type Pt = { x: number; y: number };

/** Cubic bezier point — a travelling token rides the curve the path draws. */
export function cubicAt(p0: Pt, p1: Pt, p2: Pt, p3: Pt, t: number): Pt {
  const u = 1 - t;
  const a = u * u * u;
  const b = 3 * u * u * t;
  const c = 3 * u * t * t;
  const d = t * t * t;
  return {
    x: a * p0.x + b * p1.x + c * p2.x + d * p3.x,
    y: a * p0.y + b * p1.y + c * p2.y + d * p3.y,
  };
}

/** Legacy scene id → family (migration). */
export const SCENE_TO_FAMILY: Record<string, CutawayFamily> = {
  ledger_flow: "flow",
  receipt_tape: "document",
  kinetic_figures: "kinetic_type",
  blueprint_nodes: "system_map",
  evidence: "evidence",
  minimal: "minimal",
  document: "document",
  flow: "flow",
  kinetic_type: "kinetic_type",
  comparison: "comparison",
  sequence: "sequence",
  system_map: "system_map",
};

export function resolveFamily(cutaway: TimelineCutaway): CutawayFamily {
  if (cutaway.family) return cutaway.family;
  return SCENE_TO_FAMILY[cutaway.scene] ?? "minimal";
}

/** Feeds from entities or legacy feeds — empty when none (no framework VO defaults). */
export function resolveFeeds(cutaway: TimelineCutaway): CutawayFeed[] {
  if (cutaway.feeds?.length) {
    return cutaway.feeds.map((f) => ({
      ...f,
      amount: f.amount ?? 0,
    }));
  }
  if (cutaway.entities?.length) {
    return cutaway.entities.map((e) => ({
      label: e.label,
      amount: e.value ?? 0,
      atSec: e.atSec,
      icon: e.icon,
      unit: e.unit,
      state: e.state,
      focus: e.focus ?? e.asset?.focus,
    }));
  }
  return [];
}

/**
 * Normalize beats so every skin shares the same timing contract.
 * Accepts legacy cues + generic open/total/reject aliases + beats[].
 */
export function sceneBeats(cutaway: TimelineCutaway) {
  const cues = cutaway.cues || {};
  const feeds = resolveFeeds(cutaway);
  const copy = cutaway.copy || {};
  const openSec =
    cues.openSec ?? cues.ledgerInSec ?? beatAt(cutaway, "open", "reveal") ?? 0.15;
  const inOutSec =
    cues.classifySec ?? cues.inOutSec ?? beatAt(cutaway, "classify") ?? 4.1;
  const balanceSec =
    cues.totalSec ?? cues.balanceSec ?? beatAt(cutaway, "total", "update") ?? 10.1;
  const lockSec = cues.lockSec ?? beatAt(cutaway, "lock");
  const stampRaw =
    cues.resolveSec ?? cues.stampSec ?? beatAt(cutaway, "stamp", "resolve");
  const attemptSec =
    cues.rejectSec?.length
      ? cues.rejectSec
      : cues.attemptSec?.length
        ? cues.attemptSec
        : beatsOf(cutaway, "reject");
  const lastAction = Math.max(
    openSec,
    ...feeds.map((f) => f.atSec),
    ...(lockSec != null ? [lockSec] : []),
    ...attemptSec,
    ...(cues.totalSec != null ? [cues.totalSec] : []),
    ...(cues.balanceSec != null ? [cues.balanceSec] : []),
  );
  const stampSec =
    stampRaw != null && stampRaw - lastAction > 3.5
      ? lastAction + 0.85
      : stampRaw;

  return {
    feeds,
    openSec,
    inOutSec,
    balanceSec,
    lockSec,
    attemptSec,
    stampSec,
    opening: cutaway.openingBalance ?? 0,
    kicker: copy.kicker ?? cutaway.kicker ?? "",
    title: copy.title ?? cutaway.title ?? "",
    openingLabel: copy.openingLabel ?? "",
    footerLabel: copy.footerLabel ?? "",
    balanceLabel: copy.totalLabel ?? cutaway.balanceLabel ?? "",
    lockLabel: copy.lockLabel ?? cutaway.lockLabel ?? "",
    stampLabel: copy.stampLabel ?? cutaway.stampLabel ?? "",
    inLabel: copy.inLabel ?? cutaway.inLabel ?? "",
    outLabel: copy.outLabel ?? cutaway.outLabel ?? "",
    attemptLabels: copy.attemptLabels ?? cutaway.attemptLabels ?? [],
    /** A feed's value lands in the ledger a beat after it fires. */
    arrivalOf: (f: CutawayFeed) => f.atSec + 0.6,
  };
}

function beatAt(
  cutaway: TimelineCutaway,
  ...kinds: string[]
): number | undefined {
  const hit = (cutaway.beats || []).find((b) => kinds.includes(b.kind));
  return hit?.atSec;
}

function beatsOf(cutaway: TimelineCutaway, kind: string): number[] {
  return (cutaway.beats || [])
    .filter((b) => b.kind === kind)
    .map((b) => b.atSec);
}

export const CUTAWAY_FADE_FRAMES = 10;
const MOTION_SETTLE_SEC = 0.5;
const HOLD_AFTER_LAST_SEC = 0.45;
const MAX_IDLE_TO_RESOLVE_SEC = 3.5;
const RESOLVE_AFTER_ACTION_SEC = 0.85;
const MIN_PLAY_SEC = 2.4;

const RESOLVE_CUE = new Set(["stampSec", "resolveSec"]);
const ACTION_CUE = new Set([
  "openSec",
  "ledgerInSec",
  "classifySec",
  "inOutSec",
  "totalSec",
  "balanceSec",
  "lockSec",
  "rejectSec",
  "attemptSec",
]);

function cueSeconds(value: unknown): number[] {
  if (Array.isArray(value)) return value.flatMap(cueSeconds);
  if (typeof value === "number" && Number.isFinite(value)) return [value];
  return [];
}

/** Last feed/lock/reject, and a stamp only if it is not parked at window end. */
export function lastCutawayMotionSec(cutaway: TimelineCutaway): number {
  const action: number[] = [];
  const resolve: number[] = [];
  for (const row of [...(cutaway.feeds || []), ...(cutaway.entities || [])]) {
    if (typeof row.atSec === "number") action.push(row.atSec);
  }
  for (const beat of cutaway.beats || []) {
    if (beat.kind === "stamp" || beat.kind === "resolve") resolve.push(beat.atSec);
    else action.push(beat.atSec);
  }
  const cues = cutaway.cues || {};
  for (const [key, val] of Object.entries(cues)) {
    const secs = cueSeconds(val);
    if (RESOLVE_CUE.has(key)) resolve.push(...secs);
    else if (ACTION_CUE.has(key)) action.push(...secs);
  }
  const lastAction = action.length ? Math.max(...action) : 0;
  const lastResolve = resolve.length ? Math.max(...resolve) : undefined;
  if (
    lastResolve != null &&
    lastResolve - lastAction > MAX_IDLE_TO_RESOLVE_SEC
  ) {
    return lastAction + RESOLVE_AFTER_ACTION_SEC;
  }
  return Math.max(lastAction, lastResolve ?? 0);
}

/** Sequence length: last motion + settle + short hold + dissolve, capped by authored window. */
export function cutawaySequenceDurationSec(
  cutaway: TimelineCutaway,
  fps: number,
): number {
  const fade = CUTAWAY_FADE_FRAMES / fps;
  const play = Math.max(
    lastCutawayMotionSec(cutaway) + MOTION_SETTLE_SEC + HOLD_AFTER_LAST_SEC + fade,
    MIN_PLAY_SEC,
  );
  return Math.max(fade + 0.05, Math.min(cutaway.durationSec, play));
}

/** Cue spring: 0 before the cue second, settles at 1 just after. */
export function cueSpring(
  frame: number,
  fps: number,
  cueSec: number,
  damping = 16,
  stiffness = 130,
): number {
  return spring({
    frame: frame - Math.round(cueSec * fps),
    fps,
    config: { damping, stiffness },
    durationInFrames: Math.round(fps * 0.9),
  });
}

/** Running total that re-counts toward each arrival instead of snapping. */
export function runningBalance(
  t: number,
  feeds: CutawayFeed[],
  opening: number,
  arrivalOf: (f: CutawayFeed) => number,
  openSec: number,
): number {
  let prev = opening;
  let target = opening;
  let last = openSec;
  feeds.forEach((f) => {
    if (t >= arrivalOf(f)) {
      prev = target;
      target = target + (f.amount ?? 0);
      last = arrivalOf(f);
    }
  });
  const p = Math.max(0, Math.min(1, (t - last) / 0.45));
  return prev + (target - prev) * p;
}

/** Blurred footage (or a still, for mockups) washed with a flat scene colour. */
export const Backdrop: React.FC<{
  cutaway: TimelineCutaway;
  plate: string;
  defaultDim?: number;
}> = ({ cutaway, plate, defaultDim = 0.6 }) => {
  const b = cutaway.backdrop;
  if (!b || b.kind === "plate") return null;
  const blurPx = b.blurPx ?? 34;
  return (
    <AbsoluteFill>
      {b.src ? (
        <Img
          src={assetSrc(b.src)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: `blur(${blurPx}px) saturate(0.85)`,
            transform: `scale(${b.scale ?? 1.14})`,
          }}
        />
      ) : (
        <AbsoluteFill
          style={{
            backdropFilter: `blur(${blurPx}px) saturate(0.85)`,
            WebkitBackdropFilter: `blur(${blurPx}px) saturate(0.85)`,
          }}
        />
      )}
      <AbsoluteFill style={{ background: plate, opacity: b.dim ?? defaultDim }} />
    </AbsoluteFill>
  );
};

/**
 * Material primitives. Families read as physical objects — paper, print, ink —
 * instead of UI panels, so these carry grain, edge wear and tape rather than
 * borders and rounded cards.
 */

/** Film grain / paper tooth over everything below it. */
export const Grain: React.FC<{
  opacity?: number;
  frequency?: number;
  blend?: React.CSSProperties["mixBlendMode"];
}> = ({ opacity = 0.16, frequency = 0.85, blend = "overlay" }) => {
  const id = `grain-${String(frequency).replace(".", "")}`;
  return (
    <svg
      width="100%"
      height="100%"
      style={{
        position: "absolute",
        inset: 0,
        opacity,
        mixBlendMode: blend,
        pointerEvents: "none",
      }}
    >
      <filter id={id}>
        <feTurbulence
          type="fractalNoise"
          baseFrequency={frequency}
          numOctaves={3}
          stitchTiles="stitch"
        />
        <feColorMatrix type="saturate" values="0" />
      </filter>
      <rect width="100%" height="100%" filter={`url(#${id})`} />
    </svg>
  );
};

/** Lens/press vignette so the frame has a centre of gravity. */
export const Vignette: React.FC<{ strength?: number }> = ({
  strength = 0.55,
}) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(120% 90% at 50% 42%, transparent 38%, rgba(0,0,0,${strength}) 100%)`,
      pointerEvents: "none",
    }}
  />
);

/** Torn strip of masking tape holding a print down. */
export const Tape: React.FC<{
  width: number;
  height?: number;
  rotate?: number;
  style?: React.CSSProperties;
}> = ({ width, height = 34, rotate = -6, style }) => (
  <div
    style={{
      position: "absolute",
      width,
      height,
      transform: `rotate(${rotate}deg)`,
      background:
        "linear-gradient(180deg, rgba(238,230,205,0.62), rgba(216,204,172,0.5))",
      boxShadow: "0 6px 14px rgba(0,0,0,0.28)",
      ...style,
    }}
  >
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundImage:
          "repeating-linear-gradient(90deg, rgba(255,255,255,0.22) 0 3px, transparent 3px 9px)",
      }}
    />
  </div>
);

/**
 * House glyph set: stroked vectors drawn in code so they inherit the scene
 * accent and never need staging. Raster/vector files go through `proof`.
 */
export const GLYPHS: Record<CutawayGlyph, React.ReactNode> = {
  cart: (
    <>
      <path d="M2 4h3l2.6 10.4A2 2 0 0 0 9.5 16h8.2a2 2 0 0 0 2-1.6L21.5 7H6" />
      <circle cx="10" cy="20" r="1.6" />
      <circle cx="18" cy="20" r="1.6" />
    </>
  ),
  bag: (
    <>
      <path d="M6 8h12l-1.2 12H7.2L6 8z" />
      <path d="M9.2 8V6a2.8 2.8 0 0 1 5.6 0v2" />
    </>
  ),
  receipt: (
    <>
      <path d="M6 3h12v18l-3-2-3 2-3-2-3 2V3z" />
      <path d="M9.5 8h5M9.5 12h5" />
    </>
  ),
  wallet: (
    <>
      <path d="M3 7h15a3 3 0 0 1 3 3v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z" />
      <path d="M3 7l12-3.2V7" />
      <circle cx="17" cy="13" r="1.5" />
    </>
  ),
  chart: <path d="M4 20V11M10 20V4M16 20v-6.5M2 20h20" />,
  lock: (
    <>
      <path d="M6 11h12v9H6z" />
      <path d="M9 11V8a3 3 0 0 1 6 0v3" />
    </>
  ),
};

export const Glyph: React.FC<{
  name: CutawayGlyph;
  size: number;
  color: string;
  strokeWidth?: number;
}> = ({ name, size, color, strokeWidth = 1.8 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {GLYPHS[name]}
  </svg>
);
