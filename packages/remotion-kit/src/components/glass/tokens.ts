/**
 * "Open Overlay" house style (2026-08, v7 — LOCKED) design tokens.
 *
 * Superseded the "Design Canvas" (v6) opaque-paper-card direction: every
 * card lost its panel. Text now sits straight on the a-roll — white ink,
 * zero background, zero grain/grid — with readability held by a darker
 * scrim behind the text (OverlayLayer's veil gradient) instead of a paper
 * surface. This unifies the whole overlay system onto one look: the kinds
 * that used to carry a PaperCard and the kinds that already rendered
 * white-on-veil (chapter/emphasis/diagram/callout/chip) now share the same
 * palette — no accent color anywhere except the translucent white
 * text-selection highlight mechanic (never a general "accent color").
 * Code stays a real macOS terminal window (a screen convention, kept
 * deliberately distinct — it was never part of the paper-card family).
 */
import { sansFamily, monoFamily } from "./fonts";

export const color = {
  /** Primary ink — pure white, for everything sitting on the a-roll. */
  ink: "#ffffff",
  /** Translucent white for secondary/meta text (mono labels, attributions). */
  inkMuted: "rgba(255,255,255,0.68)",
  /** Faint translucent white for gutters/rules/ghost numerals. */
  inkFaint: "rgba(255,255,255,0.4)",
  /** Text-selection highlight — translucent white, the one place color
   * beyond ink appears, and never a hue accent. */
  highlight: "rgba(255,255,255,0.22)",
  /** Dark canvas behind the terminal window (the one kind allowed to stay
   * "screen," not "a-roll" — see CodeSnippet). */
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

/** `--duration-fast/base/slow` from the design system, in ms. */
export const duration = { fast: 120, base: 220, slow: 420 };

/** House tone system: amber = caution/estimate, teal/neutral = sourced/
 * plain. Expressed as a border style (dashed vs solid) rather than color,
 * since color is reserved for the selection mechanic only — mirrors the
 * stadium_ticket illustration's own dashed-vs-solid boxes. */
export type Tone = "teal" | "amber" | "neutral";

export function toneBorderStyle(tone: Tone | undefined | null): "dashed" | "solid" {
  return tone === "amber" ? "dashed" : "solid";
}

/** Small deterministic jitter (not Math.random — renders must stay frame-
 * deterministic) so repeated selection-highlight bars don't all sit at a
 * mathematically identical angle. Hashes the overlay id into a small
 * rotation range. */
export function jitterDeg(id: string, range = 0.6): number {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  return ((h % 1000) / 1000) * range * 2 - range;
}
