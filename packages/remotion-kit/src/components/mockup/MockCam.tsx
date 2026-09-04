import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { MockCamConfig, MockCamKeyframe, MockCamState } from "../../types";
import type { Rect } from "./regions";
import { WIN } from "./regions";

type Resolve = (name: string, tLocal: number) => Rect | null;
type Shot = { scale: number; ox: number; oy: number };

/** How much of the frame the (padded) focus region should fill, per state.
 *  Lower = tighter push. */
const FILL: Record<MockCamState, number> = {
  establish: 1.0,
  read: 0.7,
  focus: 0.64,
};
/** Context padding around the raw focus rect, per state. */
const PAD: Record<MockCamState, number> = {
  establish: 0,
  read: 0.09,
  focus: 0.03,
};
/** How far the framing is nudged back toward the window centre (0 = none). */
const CENTRE_BIAS = 0.12;
const WIN_R = WIN.x + WIN.w;
const WIN_B = WIN.y + WIN.h;
const WIN_CX = WIN.x + WIN.w / 2;
const WIN_CY = WIN.y + WIN.h / 2;

/** Fit a rect (grown for context, clamped to the window) into the frame.
 *  For scale ≥ 1 the scaled stage always covers the frame for any origin in
 *  (0,1), so we only guard against extreme edge origins. */
function shotFor(
  k: MockCamKeyframe,
  cfg: MockCamConfig,
  rect: Rect | null,
): Shot {
  if (k.state === "establish" || !rect) return { scale: 1, ox: 0.5, oy: 0.5 };
  const pad = PAD[k.state];
  const x = Math.max(WIN.x, rect.x - pad);
  const y = Math.max(WIN.y, rect.y - pad);
  const w = Math.min(WIN_R, rect.x + rect.w + pad) - x;
  const h = Math.min(WIN_B, rect.y + rect.h + pad) - y;

  const fill = FILL[k.state];
  const scale = Math.max(1, Math.min(cfg.maxScale, Math.min(fill / w, fill / h)));
  const clamp = (v: number) => Math.min(0.96, Math.max(0.04, v));
  const b = CENTRE_BIAS;
  return {
    scale,
    ox: clamp((x + w / 2) * (1 - b) + WIN_CX * b),
    oy: clamp((y + h / 2) * (1 - b) + WIN_CY * b),
  };
}

function lerpShot(a: Shot, b: Shot, p: number): Shot {
  return {
    scale: interpolate(p, [0, 1], [a.scale, b.scale]),
    ox: interpolate(p, [0, 1], [a.ox, b.ox]),
    oy: interpolate(p, [0, 1], [a.oy, b.oy]),
  };
}

function resolveRect(
  k: MockCamKeyframe,
  resolve: Resolve,
  at: number,
  lag: number,
): Rect | null {
  if (k.track) {
    const name = k.track === "caret" ? "chat.caret" : "cursor";
    const r = resolve(name, Math.max(0, at - lag));
    if (r) return r;
  }
  if (k.focus) {
    const r = resolve(k.focus, at);
    if (r) return r;
  }
  if (k.focusPoint) {
    return { x: k.focusPoint[0] - 0.12, y: k.focusPoint[1] - 0.09, w: 0.24, h: 0.18 };
  }
  return WIN;
}

function sampleCam(
  cam: MockCamKeyframe[],
  cfg: MockCamConfig,
  resolve: Resolve,
  t: number,
): Shot {
  if (!cam.length) return { scale: 1, ox: 0.5, oy: 0.5 };
  const lag = Math.max(0.12, 0.55 - cfg.followGain * 0.4);
  const sorted = [...cam].sort((a, b) => a.atSec - b.atSec);

  if (t <= sorted[0].atSec) {
    return shotFor(sorted[0], cfg, resolveRect(sorted[0], resolve, sorted[0].atSec, lag));
  }

  for (let i = 0; i < sorted.length - 1; i++) {
    const a = sorted[i];
    const b = sorted[i + 1];
    if (t > b.atSec) continue;
    // A keyframe is a pose held from its atSec; the move to the next pose
    // happens over `ease` seconds ending at the next keyframe's atSec.
    const gap = Math.max(0.001, b.atSec - a.atSec);
    const ease = Math.min(cfg.easeMs / 1000, gap * 0.9);
    const p = interpolate(t, [b.atSec - ease, b.atSec], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.inOut(Easing.cubic),
    });
    return lerpShot(
      shotFor(a, cfg, resolveRect(a, resolve, t, lag)),
      shotFor(b, cfg, resolveRect(b, resolve, t, lag)),
      p,
    );
  }

  const last = sorted[sorted.length - 1];
  return shotFor(last, cfg, resolveRect(last, resolve, t, lag));
}

/**
 * Virtual camera over the mock. Fits the active region into the frame and
 * pulls back to reveal, keyframed by `camera[]`. Cam PIP + MG overlays sit
 * OUTSIDE this wrapper (Composition.tsx) so a push never scales them.
 */
export const MockCam: React.FC<{
  camera?: MockCamKeyframe[];
  cfg: MockCamConfig;
  resolve: Resolve;
  children: React.ReactNode;
}> = ({ camera, cfg, resolve, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const shot = camera?.length
    ? sampleCam(camera, cfg, resolve, frame / fps)
    : { scale: 1, ox: 0.5, oy: 0.5 };

  return (
    <AbsoluteFill style={{ overflow: "hidden", containerType: "size" }}>
      <AbsoluteFill
        style={{
          transform: `scale(${shot.scale})`,
          transformOrigin: `${shot.ox * 100}% ${shot.oy * 100}%`,
          willChange: "transform",
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
