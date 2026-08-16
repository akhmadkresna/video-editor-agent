import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { CutawayFamily, TimelineCutaway } from "../types";
import { BlueprintNodes } from "./cutaway/BlueprintNodes";
import { EvidenceCutaway } from "./cutaway/Evidence";
import { KineticFigures } from "./cutaway/KineticFigures";
import { LedgerFlow } from "./cutaway/LedgerFlow";
import { MinimalCutaway } from "./cutaway/Minimal";
import { ReceiptTape } from "./cutaway/ReceiptTape";
import { resolveFamily } from "./cutaway/shared";

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

type FamilyView = React.FC<{ cutaway: TimelineCutaway }>;

/**
 * Family registry: visual engines, not VO topics.
 * comparison → kinetic_type engine; sequence → flow engine until dedicated skins land.
 */
export const CUTAWAY_FAMILY_REGISTRY: Record<CutawayFamily, FamilyView> = {
  document: ReceiptTape,
  flow: LedgerFlow,
  kinetic_type: KineticFigures,
  comparison: KineticFigures,
  sequence: LedgerFlow,
  system_map: BlueprintNodes,
  evidence: EvidenceCutaway,
  minimal: MinimalCutaway,
};

export const CutawaySceneView: React.FC<{ cutaway: TimelineCutaway }> = ({
  cutaway,
}) => {
  const family = resolveFamily(cutaway);
  const View = CUTAWAY_FAMILY_REGISTRY[family] ?? MinimalCutaway;
  return <View cutaway={cutaway} />;
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
