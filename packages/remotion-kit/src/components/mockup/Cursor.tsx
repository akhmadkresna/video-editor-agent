import React from "react";
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { MockCursorWaypoint, MockStyle } from "../../types";
import { rectCentre, type Rect } from "./regions";

type Resolve = (name: string, tLocal: number) => Rect | null;
type Pt = [number, number];

const HOP_MAX = 0.5; // seconds for a move between waypoints
const CLICK_SEC = 0.5;

/**
 * Pointer layer — lives INSIDE MockCam, so it zooms with the stage. Eased
 * hops between waypoints (a waypoint's point is reached by its atSec), hover
 * nudge, click ripple + a short dip. `ae mockup-suggest` emits a matching
 * `sfx` click cue; this component is visual only.
 */
export const Cursor: React.FC<{
  path: MockCursorWaypoint[];
  resolve: Resolve;
  style: MockStyle;
}> = ({ path, resolve, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (!path.length) return null;

  const sorted = [...path].sort((a, b) => a.atSec - b.atSec);
  const pointOf = (wp: MockCursorWaypoint): Pt => {
    if (wp.point) return wp.point;
    if (wp.target) {
      const r = resolve(wp.target, t);
      if (r) return rectCentre(r);
    }
    return [0.5, 0.5];
  };

  let pos: Pt = pointOf(sorted[0]);
  if (t > sorted[0].atSec) {
    pos = pointOf(sorted[sorted.length - 1]);
    for (let i = 0; i < sorted.length - 1; i++) {
      const a = sorted[i];
      const b = sorted[i + 1];
      if (t > b.atSec) continue;
      const hop = Math.min(HOP_MAX, Math.max(0.001, b.atSec - a.atSec));
      const p = interpolate(t, [b.atSec - hop, b.atSec], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
        easing: Easing.inOut(Easing.cubic),
      });
      const [ax, ay] = pointOf(a);
      const [bx, by] = pointOf(b);
      pos = [interpolate(p, [0, 1], [ax, bx]), interpolate(p, [0, 1], [ay, by])];
      break;
    }
  }

  let click: { at: Pt; local: number } | null = null;
  for (const wp of sorted) {
    if (wp.action !== "click") continue;
    const local = t - wp.atSec;
    if (local >= 0 && local < CLICK_SEC) click = { at: pointOf(wp), local };
  }
  const dip = click && click.local < 0.12 ? 0.9 : 1;

  return (
    <>
      {click && (
        <div
          style={{
            position: "absolute",
            left: `${click.at[0] * 100}%`,
            top: `${click.at[1] * 100}%`,
            width: "3cqw",
            height: "3cqw",
            marginLeft: "-1.5cqw",
            marginTop: "-1.5cqw",
            borderRadius: "50%",
            border: `2px solid ${style.badgeInk}`,
            transform: `scale(${interpolate(click.local, [0, CLICK_SEC], [0.2, 1.6])})`,
            opacity: interpolate(click.local, [0, CLICK_SEC], [0.45, 0]),
          }}
        />
      )}
      <svg
        viewBox="0 0 24 24"
        style={{
          position: "absolute",
          left: `${pos[0] * 100}%`,
          top: `${pos[1] * 100}%`,
          width: "2.3cqw",
          height: "2.3cqw",
          transform: `scale(${dip})`,
          transformOrigin: "6% 6%",
          filter: "drop-shadow(0 2px 3px rgba(20,30,35,0.3))",
          color: style.cursor,
        }}
        fill="currentColor"
        aria-hidden
      >
        <path
          d="M4 3 L4 20 L9 15 L12.6 21.6 L15.3 20.3 L11.7 13.7 L18.2 13.7 Z"
          stroke="rgba(255,255,255,0.9)"
          strokeWidth={1}
          strokeLinejoin="round"
        />
      </svg>
    </>
  );
};
