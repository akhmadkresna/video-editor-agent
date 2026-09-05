/**
 * OverlayVeil — the readability scrim behind overlay text.
 *
 * Rendered ONCE for the whole layer, outside every `<Sequence>`.
 *
 * Previously each overlay painted its own full-frame gradient inside its own
 * Sequence, so N simultaneous overlays stacked N gradients and the picture
 * visibly pumped darker as beats overlapped — then snapped back at the
 * Sequence boundary. Here the envelope per zone is a `max` (not a sum), it
 * ramps in and out instead of hard-cutting, and the union across zones is
 * capped so two zones can never read darker than one.
 */
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { OverlayZone, TimelineMockScene, TimelineOverlay } from "../../types";
import { resolveZone, zoneVeilBackground } from "../overlayZones";
import type { OverlayTheme } from "./theme";

const ZONES: OverlayZone[] = ["left_third", "right_third", "lower_raised", "top_sparse"];

/**
 * White ink relies on the veil for contrast, and the veil's gradient stops
 * are tuned against typical a-roll footage (medium-to-dark). A `style: mockup`
 * scene's stage is a near-white "Mist" surface (`stageBg: #eceff1`) — the
 * opposite case. Over that background the normal veil reads as barely-there
 * and text (chapter markers especially) becomes illegible against the drawn
 * UI — and no amount of *layer opacity* can fix it, since the gradient's own
 * peak alpha is the real ceiling regardless of how close opacity gets to 1.
 *
 * `zoneVeilBackground(zone, true)` swaps in a genuinely darker gradient for
 * this one case; everywhere else the veil is unchanged.
 */
const MOCKUP_VEIL_MIN = 0.6;

function isDuringMockup(
  frame: number,
  fps: number,
  mockups: { fromSec: number; durationSec: number }[],
): boolean {
  return mockups.some((m) => {
    const from = m.fromSec * fps;
    const end = from + m.durationSec * fps;
    return frame >= from && frame <= end;
  });
}

export const OverlayVeil: React.FC<{
  overlays: TimelineOverlay[];
  theme: OverlayTheme;
  mockups?: TimelineMockScene[];
}> = ({ overlays, theme, mockups }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const overMockup = mockups?.length ? isDuringMockup(frame, fps, mockups) : false;

  const rampFrames = Math.max(1, (theme.durFast / 1000) * fps);
  const exitFrames = Math.max(1, (theme.exitMs / 1000) * fps);

  const byZone = new Map<OverlayZone, number>();

  for (const ov of overlays) {
    // `code` draws its own terminal surface and never wanted a veil.
    if (ov.kind === "code") continue;
    const from = ov.fromSec * fps;
    const end = from + ov.durationSec * fps;
    if (frame < from || frame > end) continue;

    const exitAt =
      ov.exitStartSec != null
        ? from + ov.exitStartSec * fps
        : Math.max(from, end - exitFrames);

    const env = Math.min(
      interpolate(frame, [from, from + rampFrames], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      }),
      interpolate(frame, [exitAt, end], [1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      }),
    );
    if (env <= 0) continue;

    const zone = resolveZone(ov.zone, ov.kind);
    byZone.set(zone, Math.max(byZone.get(zone) ?? 0, env));
  }

  if (byZone.size === 0) return null;
  // Two lit zones shouldn't read darker than one.
  const damp = byZone.size >= 2 ? 0.8 : 1;

  return (
    <>
      {ZONES.filter((z) => (byZone.get(z) ?? 0) > 0).map((z) => {
        const base = (byZone.get(z) ?? 0) * damp;
        const opacity = overMockup ? Math.max(base, MOCKUP_VEIL_MIN) : base;
        return (
          <AbsoluteFill
            key={z}
            style={{
              background: zoneVeilBackground(z, overMockup),
              opacity,
              pointerEvents: "none",
            }}
          />
        );
      })}
    </>
  );
};
