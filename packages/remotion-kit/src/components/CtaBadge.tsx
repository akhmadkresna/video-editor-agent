import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { isLetterboxPresentation, letterboxBand } from "../letterbox";
import type { CtaBadgeStyle, ScreenExplainerStyle } from "../types";

type Props = {
  cta?: CtaBadgeStyle;
  screenExplainer?: ScreenExplainerStyle;
};

export const CtaBadge: React.FC<Props> = ({ cta, screenExplainer }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  if (!cta?.enabled || !cta.text) return null;

  const t = frame / fps;
  const period = Math.max(0.4, cta.blinkPeriodSec ?? 1.2);
  // Smooth pulse instead of a hard on/off flash — readable on every frame.
  const pulse = 0.5 + 0.5 * Math.sin((2 * Math.PI * t) / period);
  const opacity = cta.blink === false ? 1 : 0.5 + 0.5 * pulse;
  const fontSize = Math.round(height * ((cta.sizeCqh ?? 2.2) / 100));
  const padY = Math.round(fontSize * 0.5);
  const padX = Math.round(fontSize * 0.9);

  const onBand =
    cta.anchor === "band_top_center" ||
    isLetterboxPresentation(screenExplainer?.screen?.presentation);
  let paddingTop = Math.round(height * ((cta.topCqh ?? 2.6) / 100));
  if (onBand) {
    const band = letterboxBand(
      width,
      height,
      screenExplainer?.screen?.widthRatio ?? 1,
    );
    paddingTop =
      band.top +
      Math.round(band.bandH * ((cta.bandTopCqh ?? cta.topCqh ?? 3.2) / 100));
  }

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
          gap: Math.round(fontSize * 0.55),
          padding: `${padY}px ${padX}px`,
          borderRadius: 999,
          background: "rgba(10, 14, 20, 0.82)",
          border: "2px solid rgba(255,255,255,0.22)",
          boxShadow: "0 12px 34px rgba(10, 14, 20, 0.35)",
          opacity,
        }}
      >
        <span
          style={{
            width: Math.round(fontSize * 1.5),
            height: Math.round(fontSize * 1.05),
            borderRadius: Math.round(fontSize * 0.3),
            background: "#ff0033",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <span
            style={{
              width: 0,
              height: 0,
              borderTop: `${Math.round(fontSize * 0.26)}px solid transparent`,
              borderBottom: `${Math.round(fontSize * 0.26)}px solid transparent`,
              borderLeft: `${Math.round(fontSize * 0.42)}px solid #fff`,
              marginLeft: Math.round(fontSize * 0.08),
            }}
          />
        </span>
        <span
          style={{
            fontFamily: '"Instrument Sans", "Segoe UI", system-ui, sans-serif',
            fontWeight: 800,
            fontSize,
            letterSpacing: "0.02em",
            color: "#fff",
            whiteSpace: "nowrap",
          }}
        >
          {cta.text}
        </span>
      </div>
    </AbsoluteFill>
  );
};
