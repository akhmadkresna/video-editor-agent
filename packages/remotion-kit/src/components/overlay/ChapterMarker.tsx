/**
 * ChapterMarker — corner section badge: big two-digit numeral, hairline rule,
 * caps title. Port of `_ds/components/overlays/chapter-marker/ChapterMarker.jsx`.
 *
 * Drives `chapter` and `divider` (the v7 "ghost numeral" behind the headline is
 * dropped — here the corner numeral *is* the numeral, spec §3).
 *
 * The DS hardcodes `fontSize: 34` and a 26px divider. Both are scaled off the
 * style pack instead (ASSESSMENT §3.11) so `social`, which shrinks
 * `chapter.titleSizeCqh` to 4.2 for its top bar, still fits:
 *   numeral ← `chapter.titleSizeCqh * 0.34`  (tutorial 12 → ~44px, near the
 *                                             DS's 34; social 4.2 → ~15px)
 *   title   ← `chapter.kickerSizeCqh`
 * The 0.34 factor matters: `titleSizeCqh: 12` is 130px, which was a *headline*
 * size under v7. Used literally on a corner badge it is unusable, but keeping
 * the key as the driver means both chapter dials stay live config.
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { slideUp } from "./motion";
import { cqh } from "./sizing";
import { SAFE_TOP_PCT, SAFE_X_PCT } from "./CaptionLine";
import type { OverlayTheme } from "./theme";

export type ChapterMarkerProps = {
  number: string | number;
  title?: string;
  corner?: "top-left" | "top-right";
  theme: OverlayTheme;
};

/** Pulls the trailing digits out of a kicker like `"Bab 01"` → `"01"`. */
export function chapterNumberFrom(kicker: string | undefined, fallback = ""): string {
  const m = String(kicker || "").match(/(\d{1,3})\s*$/);
  return m ? m[1] : fallback;
}

export const ChapterMarker: React.FC<ChapterMarkerProps> = ({
  number,
  title,
  corner = "top-left",
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();

  const numeralPx = cqh((theme.chapter.titleSizeCqh ?? 12) * 0.34, height);
  const titlePx = cqh(theme.chapter.kickerSizeCqh ?? 2.4, height);
  const { opacity, translateY } = slideUp(frame, fps, { durMs: theme.durBase });

  const isRight = corner === "top-right";
  // No digits in the kicker → render the title alone rather than a fake "00".
  const rawNumber = String(number ?? "").trim();
  const label = rawNumber ? rawNumber.padStart(2, "0") : "";

  return (
    <div
      style={{
        position: "absolute",
        top: `${theme.chapter.topCqh ?? SAFE_TOP_PCT}%`,
        [isRight ? "right" : "left"]: `${theme.chapter.leftCqw ?? SAFE_X_PCT}%`,
        display: "flex",
        flexDirection: isRight ? "row-reverse" : "row",
        alignItems: "center",
        gap: Math.max(8, numeralPx * 0.14),
        fontFamily: theme.fontSans,
        color: theme.ink,
        textShadow: theme.textShadow,
        opacity,
        transform: `translateY(${translateY}px)`,
      }}
    >
      {label ? (
        <span
          style={{
            fontSize: numeralPx,
            fontWeight: theme.weightHero,
            lineHeight: 1,
            letterSpacing: theme.lsTight,
            opacity: 0.9,
          }}
        >
          {label}
        </span>
      ) : null}

      {label && title ? (
        <span
          style={{
            width: 1,
            height: Math.max(14, numeralPx * 0.42),
            background: theme.lineHair,
            flexShrink: 0,
          }}
        />
      ) : null}

      {title ? (
        <span
          style={{
            fontSize: titlePx,
            fontWeight: 700,
            letterSpacing: theme.lsCaps,
            textTransform: "uppercase",
          }}
        >
          {title}
        </span>
      ) : null}
    </div>
  );
};
