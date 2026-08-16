import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { TimelineCutaway } from "../../types";
import {
  ACCENT,
  assetSrc,
  Backdrop,
  cueSpring,
  DISPLAY,
  sceneBeats,
  UI,
} from "./shared";

const PLATE = "#0a1420";

/**
 * Evidence family: a real staged asset is the hero; type annotates it.
 * Complete without an asset (falls back to title-only), but designed for proof.
 */
export const EvidenceCutaway: React.FC<{ cutaway: TimelineCutaway }> = ({
  cutaway,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const b = sceneBeats(cutaway);
  const sp = (cue: number) => cueSpring(frame, fps, cue, 14, 150);
  const open = sp(b.openSec);
  const proof =
    cutaway.proof ||
    cutaway.assets?.find((a) => a.role === "hero" || a.role === "proof") ||
    cutaway.assets?.[0];
  const title = b.title || cutaway.title || "";
  const kicker = b.kicker || cutaway.kicker || proof?.caption || "";
  const stamp = b.stampLabel || cutaway.stampLabel || "";

  return (
    <AbsoluteFill style={{ background: PLATE, overflow: "hidden" }}>
      <Backdrop cutaway={cutaway} plate={PLATE} defaultDim={0.7} />

      <div
        style={{
          position: "absolute",
          left: width * 0.07,
          top: height * 0.1,
          opacity: open,
        }}
      >
        {kicker ? (
          <div
            style={{
              fontFamily: UI,
              fontWeight: 700,
              fontSize: Math.round(height * 0.022),
              letterSpacing: "0.28em",
              textTransform: "uppercase",
              color: ACCENT,
            }}
          >
            {kicker}
          </div>
        ) : null}
        <div
          style={{
            fontFamily: DISPLAY,
            fontWeight: 800,
            fontSize: Math.round(height * 0.07),
            letterSpacing: "-0.035em",
            color: "#fff",
            marginTop: 10,
            maxWidth: width * 0.5,
          }}
        >
          {title}
        </div>
      </div>

      {proof?.src ? (
        <div
          style={{
            position: "absolute",
            right: width * 0.06,
            top: height * 0.18,
            width: width * 0.52,
            opacity: open,
            transform: `translateY(${interpolate(open, [0, 1], [40, 0])}px) rotate(-1.2deg)`,
            boxShadow: "0 40px 80px rgba(0,0,0,0.55)",
          }}
        >
          <Img
            src={assetSrc(proof.src)}
            style={{
              display: "block",
              width: "100%",
              height: height * 0.58,
              objectFit: "cover",
              objectPosition: "50% 28%",
              border: `3px solid ${ACCENT}`,
            }}
          />
          {stamp && b.stampSec != null ? (
            <div
              style={{
                position: "absolute",
                left: "12%",
                bottom: "14%",
                padding: "14px 22px",
                border: `4px solid ${ACCENT}`,
                color: ACCENT,
                fontFamily: DISPLAY,
                fontWeight: 800,
                fontSize: Math.round(height * 0.032),
                letterSpacing: "0.12em",
                background: "rgba(10,20,32,0.55)",
                opacity: sp(b.stampSec),
                transform: `rotate(-8deg) scale(${interpolate(sp(b.stampSec), [0, 1], [1.4, 1])})`,
              }}
            >
              {stamp}
            </div>
          ) : null}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
