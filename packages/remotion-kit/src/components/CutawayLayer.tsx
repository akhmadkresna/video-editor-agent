import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { TimelineCutaway } from "../types";
import { LedgerFlow } from "./cutaway/LedgerFlow";

const FADE_FRAMES = 10;

/** Dissolve on/off so the takeover never hard-flashes against cam. */
const Dissolve: React.FC<{
  durationInFrames: number;
  children: React.ReactNode;
}> = ({ durationInFrames, children }) => {
  const frame = useCurrentFrame();
  const opacity = Math.min(
    interpolate(frame, [0, FADE_FRAMES], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
    interpolate(
      frame,
      [durationInFrames - FADE_FRAMES, durationInFrames],
      [1, 0],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
    ),
  );
  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
};

export const CutawaySceneView: React.FC<{ cutaway: TimelineCutaway }> = ({
  cutaway,
}) => {
  switch (cutaway.scene) {
    case "ledger_flow":
      return <LedgerFlow cutaway={cutaway} />;
    default:
      return null;
  }
};

/**
 * MG cutaways cover the picture for their window. Cam clips stay mounted
 * underneath, so VO keeps playing.
 */
export const CutawayLayer: React.FC<{ cutaways?: TimelineCutaway[] }> = ({
  cutaways,
}) => {
  const { fps } = useVideoConfig();
  if (!cutaways?.length) return null;
  return (
    <>
      {cutaways.map((c) => {
        const from = Math.round(c.fromSec * fps);
        const duration = Math.max(1, Math.round(c.durationSec * fps));
        return (
          <Sequence
            key={c.id}
            from={from}
            durationInFrames={duration}
            name={`cutaway:${c.scene}:${c.id}`}
          >
            <Dissolve durationInFrames={duration}>
              <CutawaySceneView cutaway={c} />
            </Dissolve>
          </Sequence>
        );
      })}
    </>
  );
};
