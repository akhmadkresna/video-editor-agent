/**
 * "Design Canvas" house style (2026-08, v6 — LOCKED) design tokens.
 *
 * Superseded the pure black/white "Poster Study" (v5) direction after
 * design review against a design-tool-canvas reference (Figma/editor
 * chrome, not a print poster): cool off-white paper with an unevenly-
 * fading ruled grid (not uniform, not noise-grain), pure ink text, one
 * indigo accent used only for the text-selection highlight mechanic
 * (translucent bar + caret + round handle dot at each end — the mobile/
 * OS text-select pattern, not a design-tool resize box). Code stays a
 * real macOS terminal window (a screen convention, kept deliberately
 * distinct from the paper cards). Zero shadow, zero blur throughout.
 */
import type React from "react";
import { sansFamily, monoFamily } from "./fonts";

export const color = {
  /** Cool off-white paper — the base surface for every card. */
  paper: "#e7eaec",
  /** Near-black ink, cool-leaning to match the paper. */
  ink: "#101214",
  /** Mid gray ink for secondary/meta text (mono labels, attributions). */
  inkMuted: "#63676b",
  /** Faint gray for gutters/rules that shouldn't compete with content. */
  inkFaint: "#9aa0a4",
  /** The one accent — indigo/periwinkle, reserved for the text-selection
   * highlight mechanic only (never a general "accent color" elsewhere). */
  accent: "#4d4de8",
  accentSoft: "rgba(77, 77, 232, 0.22)",
  /** Dark canvas behind the terminal window (the one kind allowed to stay
   * "screen," not "paper" — see CodeSnippet). */
  terminalBg: "#141312",
  terminalHeaderBg: "#1e1c19",
  terminalBorder: "#333029",
} as const;

export const font = {
  sans: `'${sansFamily}', Helvetica, Arial, -apple-system, 'Segoe UI', sans-serif`,
  mono: `'${monoFamily}', 'SF Mono', Menlo, monospace`,
} as const;

export const letterSpacing = {
  tight: "-0.035em",
  normal: "0em",
  wide: "0.04em",
  caps: "0.08em",
} as const;

export const radius = {
  sm: 4,
  md: 8,
} as const;

/** Unevenly-fading ruled grid — two repeating-linear-gradients at a slight
 * off-axis angle (0.3°/90.6°, not perfectly aligned), masked by a radial
 * gradient so the grid is visible in one corner and dissolves elsewhere
 * instead of tiling uniformly across the whole card. Replaces an earlier
 * noise-grain texture, which read as "print poster," not "design canvas." */
export const paperGridStyle: React.CSSProperties = {
  backgroundImage: [
    "repeating-linear-gradient(0.3deg, rgba(16,18,20,0.09) 0 1px, transparent 1px 26px)",
    "repeating-linear-gradient(90.6deg, rgba(16,18,20,0.09) 0 1px, transparent 1px 30px)",
  ].join(", "),
  WebkitMaskImage: "radial-gradient(120% 100% at 22% 18%, black 30%, transparent 78%)",
  maskImage: "radial-gradient(120% 100% at 22% 18%, black 30%, transparent 78%)",
};

/** `--duration-fast/base/slow` from the design system, in ms. */
export const duration = { fast: 120, base: 220, slow: 420 };

/** House tone system: amber = caution/estimate, teal/neutral = sourced/
 * plain. Expressed as a border style (dashed vs solid) rather than color,
 * since the accent color is reserved for the selection mechanic only —
 * mirrors the stadium_ticket illustration's own dashed-vs-solid boxes. */
export type Tone = "teal" | "amber" | "neutral";

export function toneBorderStyle(tone: Tone | undefined | null): "dashed" | "solid" {
  return tone === "amber" ? "dashed" : "solid";
}

/** Small deterministic jitter (not Math.random — renders must stay frame-
 * deterministic) so repeated elements don't all sit at a mathematically
 * identical angle. Hashes the overlay id into a small rotation range. */
export function jitterDeg(id: string, range = 0.6): number {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  return ((h % 1000) / 1000) * range * 2 - range;
}
