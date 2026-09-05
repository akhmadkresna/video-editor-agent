/**
 * AnnotationGrid — full-bleed dashed rule-of-thirds backdrop with corner
 * triangles. Port of
 * `_ds/components/overlays/annotation-grid/AnnotationGrid.jsx`.
 *
 * Off by default (`grid.enabled: false`); opt in per beat with
 * `note: "grid:3"`. Renders behind the beat's primitive and does not count
 * against the density cap (§3).
 */
import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { gridPulse } from "./motion";
import { jitterDeg } from "../glass/tokens";
import type { OverlayTheme } from "./theme";

export type AnnotationGridProps = {
  density?: number;
  /** Stable id so the corner jitter is deterministic per beat. */
  seed?: string;
  theme: OverlayTheme;
};

/** `note: "grid:3"` → 3. Returns null when the beat didn't opt in. */
export function gridDensityFromNote(note: string | undefined | null): number | null {
  const m = String(note || "").match(/\bgrid:(\d)/);
  return m ? Number(m[1]) : null;
}

export const AnnotationGrid: React.FC<AnnotationGridProps> = ({
  density,
  seed = "grid",
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();

  const n = Math.max(2, density ?? theme.grid.density ?? 3);
  const opacity = gridPulse(frame, fps, {
    base: theme.grid.opacity ?? 0.14,
    peak: 0.32,
    periodMs: 4500,
  });

  const lines: React.ReactNode[] = [];
  for (let i = 0; i < n - 1; i++) {
    const pct = ((i + 1) / n) * 100;
    lines.push(
      <span
        key={`v${i}`}
        style={{
          position: "absolute",
          left: `${pct}%`,
          top: 0,
          bottom: 0,
          width: 1,
          borderLeft: `1px dashed ${theme.lineHair}`,
        }}
      />,
    );
    lines.push(
      <span
        key={`h${i}`}
        style={{
          position: "absolute",
          top: `${pct}%`,
          left: 0,
          right: 0,
          height: 1,
          borderTop: `1px dashed ${theme.lineHair}`,
        }}
      />,
    );
  }

  const tlSize = Math.max(24, height * 0.043);
  const brSize = Math.max(26, height * 0.048);
  const inset = height * 0.013;

  return (
    <AbsoluteFill style={{ opacity, pointerEvents: "none" }}>
      {lines}
      <svg
        width={tlSize}
        height={tlSize}
        viewBox="0 0 46 46"
        style={{
          position: "absolute",
          top: inset,
          left: inset,
          opacity: 0.5,
          transform: `rotate(${jitterDeg(`${seed}-tl`, 0.6)}deg)`,
        }}
      >
        <path d="M0 0 L46 0 L0 30 Z" fill={theme.ink} />
      </svg>
      <svg
        width={brSize}
        height={brSize}
        viewBox="0 0 52 52"
        style={{
          position: "absolute",
          bottom: inset * 0.75,
          right: inset * 0.75,
          opacity: 0.5,
          transform: `rotate(${jitterDeg(`${seed}-br`, 0.6)}deg)`,
        }}
      >
        <path d="M52 52 L0 52 L52 18 Z" fill={theme.ink} />
      </svg>
    </AbsoluteFill>
  );
};
