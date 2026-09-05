/**
 * IllustrationTag — bare icon + word. Port of
 * `_ds/components/overlays/illustration-tag/IllustrationTag.jsx`.
 *
 * Drives `chip` and `tag`. **No pill, no fill, no border** — the DS's own
 * readme calls this a "glass pill", but the JSX, its prompt.md, the handoff
 * and ASSESSMENT all agree that wording is stale. It is a bare icon beside a
 * punch-md word.
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
import { lucideIcon } from "./icons";
import type { OverlayTheme } from "./theme";

export type IllustrationTagProps = {
  label: string;
  icon?: string | null;
  corner?: "top-left" | "top-right" | "bottom-left" | "bottom-right";
  sizeCqh?: number;
  /** Beat length, so we know whether the float should run at all. */
  durationSec?: number;
  theme: OverlayTheme;
};

export const IllustrationTag: React.FC<IllustrationTagProps> = ({
  label,
  icon,
  corner = "top-left",
  sizeCqh,
  durationSec,
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();

  if (!label) return null;

  const fontSize = cqh(sizeCqh ?? theme.chip.sizeCqh ?? theme.bands.bodyCqh, height);
  const Icon = lucideIcon(icon);
  const iconPx = fontSize * (theme.chip.iconEm ?? 1.15);

  const enter = popIn(frame, fps, { durMs: theme.durBase });
  const shouldFloat = (theme.chip.float ?? true) && (durationSec ?? 0) > 3;
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
      {Icon ? (
        <Icon
          size={iconPx}
          color={theme.ink}
          strokeWidth={theme.strokeW}
          style={{ flexShrink: 0, filter: "drop-shadow(0 2px 6px rgba(0,0,0,.5))" }}
        />
      ) : null}
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
