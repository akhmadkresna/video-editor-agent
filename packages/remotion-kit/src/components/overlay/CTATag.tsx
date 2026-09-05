/**
 * CTATag — persistent call-to-action pill.
 * Port of `_ds/components/overlays/cta-tag/CTATag.jsx`, replacing `CtaBadge`.
 *
 * Two things the DS source does NOT cover, carried over from `CtaBadge`
 * verbatim because `social` depends on them (ASSESSMENT §3.6):
 *   - top anchoring (`CtaBadgeStyle.anchor` is top_center / top_left /
 *     band_top_center — the DS pins to the bottom, which is wrong here), and
 *   - `letterboxBand()` placement into the top black bar when the stage is
 *     letterboxed.
 *
 * Dropped from the old badge: the red `#ff0033` play glyph. §7 is absolute —
 * white ink only, no hue anywhere. The `solid` variant (white fill, ink text)
 * is the one deliberately inverted element in the whole system.
 */
import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { isLetterboxPresentation, letterboxBand } from "../../letterbox";
import type { CtaBadgeStyle, ScreenExplainerStyle } from "../../types";
import { bounceIn } from "./motion";
import { resolveTheme, type OverlayTheme } from "./theme";
import type { OverlayStyle } from "../../types";

type Props = {
  cta?: CtaBadgeStyle;
  screenExplainer?: ScreenExplainerStyle;
  styleTokens?: OverlayStyle;
  theme?: OverlayTheme;
};

const INK_950 = "#0a0a0a";

export const CTATag: React.FC<Props> = ({ cta, screenExplainer, styleTokens, theme: themeProp }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const theme = themeProp ?? resolveTheme(styleTokens);

  const label = cta?.label ?? cta?.text;
  if (!cta?.enabled || !label) return null;

  const fontSize = Math.round(height * ((cta.sizeCqh ?? 2.2) / 100));
  const padY = Math.round(fontSize * 0.55);
  const padX = Math.round(fontSize * 1.0);
  const variant = cta.variant ?? "solid";

  // ── anchoring (unchanged from CtaBadge) ──────────────────────────────────
  const onBand =
    cta.anchor === "band_top_center" ||
    isLetterboxPresentation(screenExplainer?.screen?.presentation);
  let paddingTop = Math.round(height * ((cta.topCqh ?? 2.6) / 100));
  if (onBand) {
    const band = letterboxBand(width, height, screenExplainer?.screen?.widthRatio ?? 1);
    paddingTop = band.top + Math.round(band.bandH * ((cta.bandTopCqh ?? cta.topCqh ?? 3.2) / 100));
  }

  // ── motion: bounce-in entrance, optional slow pulse afterwards ───────────
  const enter = bounceIn(frame, fps, { durMs: theme.durBase });
  const t = frame / fps;
  const period = Math.max(0.4, cta.blinkPeriodSec ?? 1.2);
  const pulse = 0.5 + 0.5 * Math.sin((2 * Math.PI * t) / period);
  const pulseOpacity = cta.blink === false ? 1 : 0.72 + 0.28 * pulse;

  const solid = variant === "solid";

  return (
    <AbsoluteFill
      style={{
        alignItems: cta.anchor === "top_left" ? "flex-start" : "center",
        justifyContent: "flex-start",
        paddingTop,
        paddingLeft: cta.anchor === "top_left" ? Math.round(height * 0.03) : 0,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: Math.round(fontSize * 0.4),
          padding: `${padY}px ${padX}px`,
          borderRadius: theme.radiusPill,
          background: solid ? theme.ink : "transparent",
          border: solid ? "none" : `${theme.strokeW}px solid ${theme.ink}`,
          boxShadow: solid ? "0 8px 24px rgba(0,0,0,.35)" : "none",
          color: solid ? INK_950 : theme.ink,
          fontFamily: theme.fontSans,
          fontWeight: theme.weightHero,
          fontSize,
          whiteSpace: "nowrap",
          opacity: enter.opacity * pulseOpacity,
          transform: `translateY(${enter.translateY}px) scale(${enter.scale})`,
        }}
      >
        <span>{label}</span>
        <span style={{ fontSize: Math.round(fontSize * 0.85), lineHeight: 1 }}>&#8594;</span>
      </div>
    </AbsoluteFill>
  );
};
