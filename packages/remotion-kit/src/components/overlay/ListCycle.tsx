/**
 * ListCycle — a fixed prefix with a rotating list of items.
 * Port of `_ds/components/overlays/list-cycle/ListCycle.jsx`.
 *
 * Drives the optional `list_cycle` kind (`text`→prefix, `steps[]`→items).
 *
 * The DS advances with `useState` + `setInterval`. That is wall-clock driven,
 * so in a parallel Remotion render each worker would land on a different item
 * for the same frame. The index is derived from the frame instead — and from
 * `stepAtSec` when the author supplied one, so it can be speech-aligned like a
 * diagram.
 *
 * Interval: the JSX says 1500ms, the handoff §3 says 1400ms. §1 makes the JSX
 * the source of truth where they disagree.
 */
import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { cqh, estimateWidthPx, nameSizeCqh } from "./sizing";
import { EASE_OUT } from "./motion";
import type { OverlayTheme } from "./theme";

export type ListCycleProps = {
  prefix: string;
  items: string[];
  /** Sequence-local seconds per item; falls back to a fixed interval. */
  stepAtSec?: number[];
  intervalMs?: number;
  theme: OverlayTheme;
};

export const ListCycle: React.FC<ListCycleProps> = ({
  prefix,
  items,
  stepAtSec,
  intervalMs = 1500,
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();

  if (!items?.length) return null;

  const prefixPx = cqh(theme.bands.bodyCqh, height);
  const itemPx = cqh(nameSizeCqh(theme), height);
  const t = frame / fps;

  let active = 0;
  let itemStartFrame = 0;
  if (stepAtSec?.length) {
    for (let i = 0; i < stepAtSec.length && i < items.length; i++) {
      if (t >= stepAtSec[i]) {
        active = i;
        itemStartFrame = stepAtSec[i] * fps;
      }
    }
  } else {
    const per = (intervalMs / 1000) * fps;
    const n = Math.floor(frame / per);
    active = ((n % items.length) + items.length) % items.length;
    itemStartFrame = n * per;
  }

  const slidePx = Math.max(8, height * 0.013);
  const durFrames = Math.max(1, (theme.durBase / 1000) * fps);
  const local = frame - itemStartFrame;
  const t01 = interpolate(local, [0, durFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });

  const widest = items.reduce(
    (max, it) => Math.max(max, estimateWidthPx(it, itemPx)),
    0,
  );

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: prefixPx * 0.24,
        fontFamily: theme.fontSans,
        color: theme.ink,
        textShadow: theme.textShadow,
      }}
    >
      <span
        style={{
          fontSize: prefixPx,
          fontWeight: theme.weightHero,
          lineHeight: theme.lhTight,
          letterSpacing: theme.lsTight,
        }}
      >
        {prefix}
      </span>
      <div
        style={{
          position: "relative",
          overflow: "hidden",
          minWidth: widest,
          height: itemPx * 1.25,
        }}
      >
        {items.map((item, i) => {
          const isActive = i === active;
          const prev = (active - 1 + items.length) % items.length;
          const isOutgoing = i === prev && local < durFrames;
          if (!isActive && !isOutgoing) return null;
          const opacity = isActive ? t01 : 1 - t01;
          const y = isActive
            ? interpolate(t01, [0, 1], [slidePx, 0])
            : interpolate(t01, [0, 1], [0, -slidePx]);
          return (
            <span
              key={`${i}-${item}`}
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                fontSize: itemPx,
                fontWeight: theme.weightBody,
                color: theme.inkMuted,
                whiteSpace: "nowrap",
                opacity,
                transform: `translateY(${y}px)`,
              }}
            >
              {item}
            </span>
          );
        })}
      </div>
    </div>
  );
};
