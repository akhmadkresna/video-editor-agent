/**
 * CaptionLine — subordinate line of type, optionally attributed.
 * Port of `_ds/components/overlays/caption-line/CaptionLine.jsx`.
 *
 * Drives `lower_third` and the attribution half of `quote`. Self-places at the
 * bottom safe inset (spec §3 / ASSESSMENT §3.9) unless `inline` is set, which
 * is how `quote` stacks it under the PunchWord.
 *
 * The DS animates only a fade; spec §5 upgrades this to `ov-slide-up` over
 * `durFast` for the lower-third role.
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { slideUp } from "./motion";
import { cqh } from "./sizing";
import type { OverlayTheme } from "./theme";

/** `--safe-x` / `--safe-bottom` from `_ds/tokens/spacing.css`. */
export const SAFE_X_PCT = 6;
export const SAFE_TOP_PCT = 8;
export const SAFE_BOTTOM_PCT = 10;

export type CaptionLineProps = {
  text: string;
  speaker?: string;
  size?: "sm" | "md" | "lg";
  align?: "left" | "right";
  /** Render in flow (used by `quote`) instead of self-placing at the bottom. */
  inline?: boolean;
  delayMs?: number;
  theme: OverlayTheme;
};

export const CaptionLine: React.FC<CaptionLineProps> = ({
  text,
  speaker,
  size = "md",
  align = "left",
  inline = false,
  delayMs = 0,
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();

  if (!text && !speaker) return null;

  const bandCqh =
    size === "lg" ? theme.bands.subCqh : size === "sm" ? theme.bands.labelCqh : theme.bands.metaCqh;

  const { opacity, translateY } = slideUp(frame, fps, {
    durMs: theme.durFast,
    delayMs,
  });

  const placement: React.CSSProperties = inline
    ? {}
    : {
        position: "absolute",
        bottom: `${SAFE_BOTTOM_PCT}%`,
        [align === "right" ? "right" : "left"]: `${SAFE_X_PCT}%`,
        textAlign: align,
      };

  return (
    <div
      style={{
        ...placement,
        fontFamily: theme.fontSans,
        color: theme.ink,
        opacity,
        transform: `translateY(${translateY}px)`,
      }}
    >
      {speaker ? (
        <div
          style={{
            fontSize: cqh(theme.bands.eyebrowCqh, height),
            fontWeight: 700,
            letterSpacing: theme.lsCaps,
            textTransform: "uppercase",
            opacity: 0.7,
            marginBottom: 4,
          }}
        >
          {speaker}
        </div>
      ) : null}
      {text ? (
        <div
          style={{
            fontSize: cqh(bandCqh, height),
            fontWeight: theme.weightBody,
            lineHeight: 1.15,
            textShadow: theme.textShadow,
          }}
        >
          {text}
        </div>
      ) : null}
    </div>
  );
};
