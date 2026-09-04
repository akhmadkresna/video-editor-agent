import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { MockChrome, MockStyle } from "../../types";
import { mockFont } from "./fonts";
import { WIN } from "./regions";

/**
 * The drawn screen. Mist desktop ground + one floating window with minimal
 * chrome; the surface (ClaudeChat / DiffPanel / …) renders as children.
 * Window inset here MUST match `WIN` in regions.ts.
 */
export const MockStage: React.FC<{
  title?: string;
  chrome?: MockChrome;
  style: MockStyle;
  children: React.ReactNode;
}> = ({ title, chrome = "claude", style, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Gentle mount settle — the window eases the last 1.5% into place.
  const settle = interpolate(frame, [0, Math.round(fps * 0.4)], [0.988, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: style.stageBg,
        fontFamily: mockFont.ui,
        containerType: "size",
      }}
    >
      {/* faint cool top-light so the flat ground isn't dead */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(255,255,255,0.45), rgba(255,255,255,0) 42%)",
        }}
      />

      <div
        style={{
          position: "absolute",
          left: `${WIN.x * 100}%`,
          top: `${WIN.y * 100}%`,
          width: `${WIN.w * 100}%`,
          height: `${WIN.h * 100}%`,
          transform: `scale(${settle})`,
          transformOrigin: "50% 46%",
          background: style.window,
          border: `1px solid ${style.windowBorder}`,
          borderRadius: 14,
          boxShadow: style.windowShadow,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {chrome !== "none" && (
          <div
            style={{
              flex: "0 0 12%",
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "0 26px",
              borderBottom: `1px solid ${style.railLine}`,
            }}
          >
            <div style={{ display: "flex", gap: 10, width: 70 }}>
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  style={{
                    width: 13,
                    height: 13,
                    borderRadius: "50%",
                    border: `1.5px solid ${style.chromeDot}`,
                  }}
                />
              ))}
            </div>
            <div
              style={{
                flex: 1,
                textAlign: "center",
                fontFamily: mockFont.mono,
                fontSize: "1.4cqw",
                letterSpacing: "0.08em",
                textTransform: "lowercase",
                color: style.chromeTitle,
              }}
            >
              {chrome === "claude" ? (title ?? "") : ""}
            </div>
            <div style={{ width: 70 }} />
          </div>
        )}

        <div style={{ flex: 1, display: "flex", minHeight: 0 }}>{children}</div>
      </div>
    </AbsoluteFill>
  );
};
