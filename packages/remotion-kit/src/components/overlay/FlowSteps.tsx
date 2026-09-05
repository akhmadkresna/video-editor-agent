/**
 * FlowSteps — numbered step chips joined by connectors, each carrying a
 * traveling glow dot. Port of
 * `_ds/components/overlays/flow-steps/FlowSteps.jsx`.
 *
 * Drives `diagram`. Step timing (`stepAtSec`) is computed upstream in
 * `cover/overlay_schedule.py` and asserted by `tests/test_diagram_motion.py`,
 * so it is consumed here, never re-derived.
 *
 * Deviation from the DS: it snaps a chip from unreached to reached. At chip
 * size that reads as a glitch, so the two states cross-fade over `durFast`.
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { interpolate } from "remotion";
import { flowDotPhase, popIn } from "./motion";
import { cqh } from "./sizing";
import type { OverlayTheme } from "./theme";

const INK_950 = "#0a0a0a";

export type FlowStepsProps = {
  steps: string[];
  /** Sequence-local seconds at which each step becomes "reached". */
  stepAtSec?: number[];
  direction?: "horizontal" | "vertical";
  theme: OverlayTheme;
};

export const FlowSteps: React.FC<FlowStepsProps> = ({
  steps,
  stepAtSec,
  direction,
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();

  if (!steps?.length) return null;

  // §3: vertical when the beat's box is narrow.
  const dir =
    direction ?? ((theme.diagram.maxWidthCqw ?? 40) <= 40 ? "vertical" : "horizontal");
  const vertical = dir === "vertical";

  const fontSize = cqh(theme.diagram.stepSizeCqh ?? 3.6, height);
  const showDot = (theme.diagram.connector ?? "traveling_dot") === "traveling_dot";

  const railLen = vertical ? height * 0.022 : height * 0.033;
  const railThick = Math.max(2, height * 0.0037);
  const dotSize = Math.max(5, height * 0.0074);

  return (
    <div
      style={{
        display: "inline-flex",
        flexDirection: vertical ? "column" : "row",
        alignItems: vertical ? "flex-start" : "center",
        fontFamily: theme.fontSans,
      }}
    >
      {steps.map((label, i) => {
        const enter = popIn(frame, fps, { durMs: theme.durBase, delayMs: i * 120 });
        const stepFrame = stepAtSec?.[i] != null ? stepAtSec[i] * fps : null;
        const reached =
          stepFrame == null
            ? 0
            : interpolate(
                frame,
                [stepFrame, stepFrame + (theme.durFast / 1000) * fps],
                [0, 1],
                { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
              );

        const chipBase: React.CSSProperties = {
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          gap: fontSize * 0.5,
          padding: `${fontSize * 0.42}px ${fontSize * 0.66}px`,
          borderRadius: theme.radiusPill,
          border: `1px solid ${theme.lineHair}`,
          whiteSpace: "nowrap",
          boxSizing: "border-box",
        };

        const badge = (bg: string, fg: string): React.CSSProperties => ({
          width: fontSize * 1.15,
          height: fontSize * 1.15,
          borderRadius: "50%",
          background: bg,
          color: fg,
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: fontSize * 0.62,
          fontWeight: 700,
          flexShrink: 0,
        });

        return (
          <React.Fragment key={`${i}-${label}`}>
            <div
              style={{
                position: "relative",
                display: "inline-flex",
                fontSize,
                fontWeight: 700,
                opacity: enter.opacity,
                transform: `translateY(${enter.translateY}px) scale(${enter.scale})`,
              }}
            >
              {/* sizer — keeps both states the same box */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: fontSize * 0.5,
                  padding: `${fontSize * 0.42}px ${fontSize * 0.66}px`,
                  border: `1px solid transparent`,
                  visibility: "hidden",
                  whiteSpace: "nowrap",
                }}
              >
                <span style={badge("transparent", "transparent")}>{i + 1}</span>
                <span>{label}</span>
              </div>

              {/* unreached */}
              <div
                style={{
                  ...chipBase,
                  background: theme.fillWhite12,
                  color: theme.ink,
                  opacity: 1 - reached,
                }}
              >
                <span style={badge(theme.ink, INK_950)}>{i + 1}</span>
                <span>{label}</span>
              </div>

              {/* reached — inverted */}
              <div
                style={{
                  ...chipBase,
                  background: theme.ink,
                  color: INK_950,
                  borderColor: "transparent",
                  opacity: reached,
                }}
              >
                <span style={badge(INK_950, theme.ink)}>{i + 1}</span>
                <span>{label}</span>
              </div>
            </div>

            {i < steps.length - 1 ? (
              <div
                style={{
                  position: "relative",
                  width: vertical ? railThick : railLen,
                  height: vertical ? railLen : railThick,
                  margin: vertical ? `${fontSize * 0.16}px 0 ${fontSize * 0.16}px ${fontSize * 1.0}px` : `0 ${fontSize * 0.18}px`,
                  borderRadius: 2,
                  background: theme.lineHair,
                  flexShrink: 0,
                }}
              >
                {showDot
                  ? (() => {
                      const ph = flowDotPhase(frame, fps, {
                        periodMs: 1100,
                        delayMs: i * 140,
                      });
                      const travel = (vertical ? railLen : railLen) - dotSize;
                      const pos = ph * Math.max(0, travel);
                      return (
                        <span
                          style={{
                            position: "absolute",
                            width: dotSize,
                            height: dotSize,
                            borderRadius: "50%",
                            background: theme.ink,
                            boxShadow: "0 0 8px 2px rgba(255,255,255,.7)",
                            opacity: interpolate(ph, [0, 0.1, 0.9, 1], [0, 1, 1, 0], {
                              extrapolateLeft: "clamp",
                              extrapolateRight: "clamp",
                            }),
                            ...(vertical
                              ? { top: pos, left: railThick / 2 - dotSize / 2 }
                              : { left: pos, top: railThick / 2 - dotSize / 2 }),
                          }}
                        />
                      );
                    })()
                  : null}
              </div>
            ) : null}
          </React.Fragment>
        );
      })}
    </div>
  );
};
