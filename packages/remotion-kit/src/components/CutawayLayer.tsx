import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { CutawayFamily, TimelineCutaway } from "../types";
import { InterfaceStage } from "./cutaway/InterfaceStage";
import {
  CUTAWAY_FADE_FRAMES,
  cutawaySequenceDurationSec,
  resolveFamily,
} from "./cutaway/shared";

/** Dissolve on/off so the takeover never hard-flashes against cam. */
const Dissolve: React.FC<{
  durationInFrames: number;
  children: React.ReactNode;
}> = ({ durationInFrames, children }) => {
  const frame = useCurrentFrame();
  const opacity = Math.min(
    interpolate(frame, [0, CUTAWAY_FADE_FRAMES], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
    interpolate(
      frame,
      [durationInFrames - CUTAWAY_FADE_FRAMES, durationInFrames],
      [1, 0],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
    ),
  );
  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
};

type FamilyView = React.FC<{ cutaway: TimelineCutaway }>;

/**
 * One engine for every brief. Family ids stay on the timeline for naming and
 * QA; layout is inferred from the data (catalog / ledger / access / shot).
 */
export const CUTAWAY_FAMILY_REGISTRY: Record<CutawayFamily, FamilyView> = {
  document: InterfaceStage,
  flow: InterfaceStage,
  kinetic_type: InterfaceStage,
  comparison: InterfaceStage,
  sequence: InterfaceStage,
  system_map: InterfaceStage,
  evidence: InterfaceStage,
  minimal: InterfaceStage,
};

export const CutawaySceneView: React.FC<{ cutaway: TimelineCutaway }> = ({
  cutaway,
}) => <InterfaceStage cutaway={cutaway} />;

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
        const duration = Math.max(
          1,
          Math.round(cutawaySequenceDurationSec(c, fps) * fps),
        );
        const family = resolveFamily(c);
        return (
          <Sequence
            key={c.id}
            from={from}
            durationInFrames={duration}
            name={`cutaway:${family}:${c.id}`}
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
