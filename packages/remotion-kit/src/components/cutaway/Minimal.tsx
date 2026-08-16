import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { TimelineCutaway } from "../../types";
import {
  ACCENT,
  Backdrop,
  cueSpring,
  DISPLAY,
  sceneBeats,
  UI,
} from "./shared";

const PLATE = "#0c1520";

/**
 * Safe fallback family: one strong claim + one accent rule.
 * Used when no richer family fits, or quality gates demote a weak brief.
 */
export const MinimalCutaway: React.FC<{ cutaway: TimelineCutaway }> = ({
  cutaway,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const b = sceneBeats(cutaway);
  const sp = (cue: number) => cueSpring(frame, fps, cue, 14, 150);
  const open = sp(b.openSec);
  const title = b.title || cutaway.title || "";
  const kicker = b.kicker || cutaway.kicker || "";

  return (
    <AbsoluteFill style={{ background: PLATE, overflow: "hidden" }}>
      <Backdrop cutaway={cutaway} plate={PLATE} defaultDim={0.72} />
      <div
        style={{
          position: "absolute",
          left: width * 0.08,
          top: height * 0.34,
          maxWidth: width * 0.84,
          opacity: open,
          transform: `translateY(${interpolate(open, [0, 1], [28, 0])}px)`,
        }}
      >
        {kicker ? (
          <div
            style={{
              fontFamily: UI,
              fontWeight: 700,
              fontSize: Math.round(height * 0.024),
              letterSpacing: "0.28em",
              textTransform: "uppercase",
              color: ACCENT,
              marginBottom: 18,
            }}
          >
            {kicker}
          </div>
        ) : null}
        <div
          style={{
            fontFamily: DISPLAY,
            fontWeight: 800,
            fontSize: Math.round(height * 0.1),
            letterSpacing: "-0.04em",
            lineHeight: 1.05,
            color: "#fff",
          }}
        >
          {title}
        </div>
        <div
          style={{
            marginTop: 28,
            width: interpolate(open, [0, 1], [0, width * 0.28]),
            height: Math.round(height * 0.014),
            background: ACCENT,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
