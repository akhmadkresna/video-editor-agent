/**
 * IllustrationTag — bare word badge. Port of
 * `_ds/components/overlays/illustration-tag/IllustrationTag.jsx`.
 *
 * Drives the `tag` kind. **No pill, no fill, no border** — the DS's own
 * readme calls this a "glass pill", but the JSX, its prompt.md, the handoff
 * and ASSESSMENT all agree that wording is stale. It is a bare punch-md word.
 *
 * Two composed motions: a pop-in scaled from the anchored corner, then a
 * continuous ±7px float — the float only engages when the beat is on screen
 * long enough to need it (spec §5: dwell > 3s), otherwise it would fight the
 * entrance.
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { floatY, popIn } from "./motion";
import { cqh } from "./sizing";
import type { OverlayTheme } from "./theme";

export type IllustrationTagProps = {
  label: string;
  corner?: "top-left" | "top-right" | "bottom-left" | "bottom-right";
  sizeCqh?: number;
  /** Beat length, so we know whether the float should run at all. */
  durationSec?: number;
  theme: OverlayTheme;
};

export const IllustrationTag: React.FC<IllustrationTagProps> = ({
  label,
  corner = "top-left",
  sizeCqh,
  durationSec,
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();

  if (!label) return null;

  const fontSize = cqh(sizeCqh ?? theme.tag.sizeCqh ?? theme.bands.bodyCqh, height);

  const enter = popIn(frame, fps, { durMs: theme.durBase });
  const shouldFloat = (theme.tag.float ?? true) && (durationSec ?? 0) > 3;
  const drift = shouldFloat
    ? floatY(frame, fps, { periodMs: 2600, amplitudePx: fontSize * 0.12, delayMs: 500 })
    : 0;

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: fontSize * 0.3,
        fontFamily: theme.fontSans,
        color: theme.ink,
        textShadow: theme.textShadow,
        whiteSpace: "nowrap",
        opacity: enter.opacity,
        transform: `translateY(${enter.translateY + drift}px) scale(${enter.scale})`,
        transformOrigin: corner.replace("-", " "),
      }}
    >
      <span
        style={{
          fontSize,
          fontWeight: theme.weightHero,
          lineHeight: theme.lhTight,
          letterSpacing: theme.lsTight,
        }}
      >
        {label}
      </span>
    </div>
  );
};
