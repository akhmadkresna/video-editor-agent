/**
 * CalloutArrow — a dashed pointer that draws itself, then marches, with an
 * italic label at the tip. Port of
 * `_ds/components/overlays/callout-arrow/CalloutArrow.jsx`.
 *
 * Drives `callout` when the author supplied a target (`at`). Spec §3 says to
 * suppress the arrow on full-cam; the renderer has no access to clip layout,
 * so that is implemented as "an arrow requires an explicit `at`" — a callout
 * without one falls back to PunchWord instead of rendering nothing.
 *
 * Two fixes to the DS source, both called out in §7 / ASSESSMENT:
 *   - it sizes the label with `var(--fs-punch-sm)`, which is **undefined** in
 *     its own token files (silently inherits). Uses `sizeBands.labelCqh`.
 *   - it computes an `angle` and never uses it — there is no arrowhead, only a
 *     dot at the tip. An actual head is drawn here, rotated by that angle.
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { drawLine, fadeIn, marchOffset, msToFrames, popIn } from "./motion";
import { cqh, estimateWidthPx } from "./sizing";
import type { OverlayTheme } from "./theme";

export type CalloutArrowProps = {
  label: string;
  /** Target, 0–1 of frame. */
  to: [number, number];
  /** Origin, 0–1 of frame. */
  from: [number, number];
  theme: OverlayTheme;
};

export const CalloutArrow: React.FC<CalloutArrowProps> = ({ label, to, from, theme }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const x1 = from[0] * width;
  const y1 = from[1] * height;
  const x2 = to[0] * width;
  const y2 = to[1] * height;

  const scale = height / 1080;
  const drawFrames = msToFrames(theme.durSlow, fps);
  const progress = drawLine(frame, fps, { durMs: theme.durSlow });
  const marching = frame >= drawFrames;

  // pathLength=1 makes the dash math resolution-independent.
  const dashOffset = marching
    ? marchOffset(frame, fps, {
        periodMs: 900,
        distancePx: 22 * scale,
        delayMs: theme.durSlow,
      })
    : 1 - progress;

  const head = popIn(frame, fps, { durMs: theme.durBase, delayMs: 480 });
  const labelOpacity = fadeIn(frame, fps, { durMs: theme.durBase, delayMs: 280 });

  const angleDeg = (Math.atan2(y2 - y1, x2 - x1) * 180) / Math.PI;
  const headSize = Math.max(8, height * 0.012);

  const labelPx = cqh(theme.bands.labelCqh, height);
  const pointsLeft = x2 < x1;
  // Keep the label inside frame: flip the side if it would run off the edge.
  const estW = estimateWidthPx(label, labelPx);
  const flip = pointsLeft || x2 + estW > width * 0.94;

  return (
    <>
      <svg
        width={width}
        height={height}
        style={{ position: "absolute", inset: 0, overflow: "visible" }}
      >
        <line
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          stroke={theme.ink}
          strokeWidth={theme.strokeW * scale}
          strokeLinecap="round"
          pathLength={1}
          strokeDasharray={marching ? `${5 * scale} ${6 * scale}` : "1 1"}
          strokeDashoffset={dashOffset}
        />
        <circle cx={x1} cy={y1} r={3.5 * scale} fill={theme.ink} />
        <g
          transform={`translate(${x2} ${y2}) rotate(${angleDeg}) scale(${head.scale})`}
          opacity={head.opacity}
        >
          <polygon
            points={`0,0 ${-headSize},${-headSize * 0.5} ${-headSize},${headSize * 0.5}`}
            fill={theme.ink}
          />
        </g>
      </svg>

      <div
        style={{
          position: "absolute",
          left: x2 + (flip ? -14 * scale : 14 * scale),
          top: y2 - labelPx * 1.4,
          transform: flip ? "translateX(-100%)" : undefined,
          fontFamily: theme.fontSans,
          fontSize: labelPx,
          fontWeight: 700,
          fontStyle: "italic",
          color: theme.ink,
          textShadow: theme.textShadow,
          whiteSpace: "nowrap",
          opacity: labelOpacity,
        }}
      >
        {label}
      </div>
    </>
  );
};
