import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import type { TimelinePrivacy } from "../types";

const BAR_COLOR = "#0b1220";
const LABEL_COLOR = "rgba(200, 210, 220, 0.55)";
const BLUR_TINT = "rgba(11, 18, 32, 0.42)";

type Props = {
  privacy: TimelinePrivacy[];
};

/**
 * Privacy masks over on-screen credentials.
 * - `bar`: solid rects (legacy precise redaction)
 * - `screen_blur`: frosted full-window blur (composite / credential scenes)
 */
export const PrivacyLayer: React.FC<Props> = ({ privacy }) => {
  const { fps, width, height } = useVideoConfig();
  if (!privacy?.length) return null;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {privacy.map((mask) => {
        const from = Math.round(mask.fromSec * fps);
        const duration = Math.max(1, Math.round(mask.durationSec * fps));
        const isBlur = mask.mode === "screen_blur";
        return (
          <Sequence
            key={mask.id}
            from={from}
            durationInFrames={duration}
            name={mask.id}
          >
            <AbsoluteFill>
              {(mask.rects || []).map((r, i) => {
                const left = (r.x / 100) * width;
                const top = (r.y / 100) * height;
                const w = (r.w / 100) * width;
                const h = (r.h / 100) * height;
                if (isBlur) {
                  return (
                    <div
                      key={`${mask.id}-r${i}`}
                      style={{
                        position: "absolute",
                        left,
                        top,
                        width: w,
                        height: h,
                        backdropFilter: "blur(22px)",
                        WebkitBackdropFilter: "blur(22px)",
                        backgroundColor: BLUR_TINT,
                        borderRadius: Math.max(4, Math.round(h * 0.012)),
                        overflow: "hidden",
                      }}
                    >
                      {i === 0 && mask.label ? (
                        <span
                          style={{
                            position: "absolute",
                            left: Math.max(12, Math.round(w * 0.03)),
                            top: Math.max(10, Math.round(h * 0.03)),
                            fontFamily:
                              'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
                            fontSize: Math.max(11, Math.min(16, Math.round(h * 0.04))),
                            fontWeight: 600,
                            letterSpacing: "0.08em",
                            color: LABEL_COLOR,
                            textTransform: "uppercase",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {mask.label}
                        </span>
                      ) : null}
                    </div>
                  );
                }
                return (
                  <div
                    key={`${mask.id}-r${i}`}
                    style={{
                      position: "absolute",
                      left,
                      top,
                      width: w,
                      height: h,
                      backgroundColor: BAR_COLOR,
                      borderRadius: Math.max(2, Math.round(h * 0.08)),
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "flex-start",
                      paddingLeft: Math.max(6, Math.round(w * 0.02)),
                      overflow: "hidden",
                    }}
                  >
                    {i === 0 && mask.label ? (
                      <span
                        style={{
                          fontFamily:
                            'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
                          fontSize: Math.max(
                            10,
                            Math.min(14, Math.round(h * 0.45)),
                          ),
                          fontWeight: 600,
                          letterSpacing: "0.06em",
                          color: LABEL_COLOR,
                          textTransform: "uppercase",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {mask.label}
                      </span>
                    ) : null}
                  </div>
                );
              })}
            </AbsoluteFill>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
