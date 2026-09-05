/**
 * A-roll motion-graphics layer.
 *
 * Sequencing + placement only — every kind's *look* lives in
 * `./overlay/dispatch.tsx` and the A-Roll Text Motion System primitives beside
 * it. This file used to also carry five hand-rolled renderers with their own
 * fonts (`Syne` / `Instrument Sans`, neither of which was ever loaded), their
 * own springs and their own count-up; all of that now comes from one shared
 * set so a style pack's config actually reaches the screen.
 */
import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import type { OverlayStyle, TimelineMockScene, TimelineOverlay } from "../types";
import { GlassOverlay } from "./glass/GlassOverlays";
import { resolveZone, zoneBoxStyle } from "./overlayZones";
import { AnnotationGrid, gridDensityFromNote } from "./overlay/AnnotationGrid";
import { OverlayVeil } from "./overlay/OverlayVeil";
import {
  LEGACY_GLASS_KINDS,
  SELF_PLACED_KINDS,
  boxOptsForKind,
  renderOverlayBody,
} from "./overlay/dispatch";
import { exitFade } from "./overlay/motion";
import { resolveTheme, type OverlayTheme } from "./overlay/theme";

const OneOverlay: React.FC<{ ov: TimelineOverlay; theme: OverlayTheme }> = ({ ov, theme }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // Every kind now gets an exit. The old `useExit` returned a constant 1 for
  // its "hardcut" mode, so 6 of the 8 glass kinds simply popped off screen at
  // the Sequence boundary.
  const opacity = exitFade(frame, fps, {
    durationSec: ov.durationSec,
    exitStartSec: ov.exitStartSec,
    exitMs: theme.exitMs,
  });

  const gridDensity =
    gridDensityFromNote(ov.note) ?? (theme.grid.enabled ? theme.grid.density : null);
  const grid = gridDensity ? (
    <AnnotationGrid density={gridDensity} seed={ov.id} theme={theme} />
  ) : null;

  // `code` and `illustration` are explicitly out of scope for the port
  // (spec §3) and stay on the legacy renderer.
  if (LEGACY_GLASS_KINDS.has(ov.kind)) {
    return (
      <AbsoluteFill style={{ opacity }}>
        {grid}
        <GlassOverlay ov={ov} />
      </AbsoluteFill>
    );
  }

  const body = renderOverlayBody(ov, theme, { width, height });
  if (!body) return null;

  // Self-placing kinds carry their own absolute insets; an arrow spans the
  // whole frame by definition. Everything else sits in its zone box.
  const selfPlaced =
    SELF_PLACED_KINDS.has(ov.kind) || (ov.kind === "callout" && !ov.value && !!ov.at);

  if (selfPlaced) {
    return (
      <AbsoluteFill style={{ opacity }}>
        {grid}
        {body}
      </AbsoluteFill>
    );
  }

  const zone = resolveZone(ov.zone, ov.kind);
  const opts = boxOptsForKind(ov.kind, theme);

  return (
    <AbsoluteFill style={{ opacity }}>
      {grid}
      <div
        style={{
          ...zoneBoxStyle(zone, {
            maxWidthCqw: opts.maxWidthCqw,
            insetCqw: opts.insetCqw,
            topCqh: opts.topCqh,
            bottomCqh: opts.bottomCqh,
          }),
          // Last-resort guard: the fitter shrinks to fit, but never let a beat
          // bleed across the frame if an estimate is off.
          overflow: "hidden",
        }}
      >
        {body}
      </div>
    </AbsoluteFill>
  );
};

export const OverlayLayer: React.FC<{
  overlays: TimelineOverlay[];
  styleTokens?: OverlayStyle;
  /** Active mockup scenes — boosts the veil over `style: mockup`'s light stage. */
  mockups?: TimelineMockScene[];
}> = ({ overlays, styleTokens, mockups }) => {
  const { fps } = useVideoConfig();
  if (!overlays?.length) return null;
  const theme = resolveTheme(styleTokens);

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <OverlayVeil overlays={overlays} theme={theme} mockups={mockups} />
      {overlays.map((ov) => {
        const from = Math.round(ov.fromSec * fps);
        const duration = Math.max(1, Math.round(ov.durationSec * fps));
        return (
          <Sequence key={ov.id} from={from} durationInFrames={duration} name={ov.id}>
            <OneOverlay ov={ov} theme={theme} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
