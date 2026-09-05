/**
 * StatCallout — a number that counts up, with a sand-drip accent that keeps
 * running the whole dwell. Port of
 * `_ds/components/overlays/stat-callout/StatCallout.jsx`.
 *
 * Drives `stat`, and `callout` when it carries a `value`.
 *
 * Deviation from the DS source: its eyebrow sits on a `--scrim-strong`
 * (rgba(0,0,0,.72)) pill. That is a panel, which §7 forbids outright
 * ("max surface = fillWhite12"). Rendered as bare text + textShadow instead,
 * per ASSESSMENT §3.8.
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { countUp, dripPhase, fadeIn, particleOpacity, slideUp } from "./motion";
import { cqh, cqw, estimateWidthPx, fitHeadline } from "./sizing";
import type { OverlayTheme } from "./theme";

export type StatCalloutProps = {
  value: string | number;
  eyebrow?: string;
  /** Small line under the value (`sourceLabel`). */
  meta?: string;
  align?: "left" | "center" | "right";
  valueSizeCqh?: number;
  metaSizeCqh?: number;
  maxWidthCqw?: number;
  theme: OverlayTheme;
};

/**
 * Counts the first number inside `raw` while preserving everything around it
 * ("Rp24 jt" → "Rp0 jt" … "Rp24 jt") and keeping the original thousands
 * separator. The old code had two implementations of this with *opposite*
 * separators (`.` in OverlayLayer, `,` in glass); this keeps whatever the
 * author wrote.
 */
export function countUpText(raw: string, progress: number): string {
  const s = String(raw ?? "");
  const m = s.match(/\d[\d.,]*/);
  if (!m) return s;
  const token = m[0];
  const sepMatch = token.match(/[.,](?=\d{3}\b)/);
  const sep = sepMatch ? sepMatch[0] : "";
  const target = parseInt(token.replace(/[^\d]/g, ""), 10);
  if (!Number.isFinite(target)) return s;

  const current = Math.round(target * progress);
  let out = String(current);
  if (sep) out = out.replace(/\B(?=(\d{3})+(?!\d))/g, sep);
  return s.replace(token, out);
}

export const StatCallout: React.FC<StatCalloutProps> = ({
  value,
  eyebrow,
  meta,
  align = "left",
  valueSizeCqh,
  metaSizeCqh,
  maxWidthCqw = 48,
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const raw = String(value ?? "");
  if (!raw && !eyebrow && !meta) return null;

  const progress = countUp(frame, fps, { countMs: theme.countMs });
  const display = countUpText(raw, progress);

  const boxWidthPx = cqw(maxWidthCqw, width);
  const basePx = cqh(valueSizeCqh ?? theme.bands.heroCqh, height);
  const fontSize = fitHeadline({
    text: raw,
    basePx,
    boxWidthPx,
    maxLines: 1,
    lineHeight: theme.lhTight,
  });

  const eyebrowEnter = slideUp(frame, fps, { durMs: theme.durBase, fromPx: 12 });
  const metaOpacity = fadeIn(frame, fps, { durMs: theme.durBase, delayMs: theme.durBase });

  // Value fades 0.35 → 1 and scales 0.6 → 1 in lockstep with the count.
  const valueOpacity = 0.35 + progress * 0.65;
  const valueScale = 0.6 + progress * 0.4;

  const dripW = Math.max(3, fontSize * 0.035);
  const dripTravel = fontSize * 0.34;

  return (
    <div
      style={{
        display: "inline-flex",
        flexDirection: "column",
        alignItems: align === "center" ? "center" : align === "right" ? "flex-end" : "flex-start",
        fontFamily: theme.fontSans,
        color: theme.ink,
        textShadow: theme.textShadow,
        maxWidth: boxWidthPx,
      }}
    >
      {eyebrow ? (
        <span
          style={{
            fontSize: cqh(theme.bands.labelCqh, height),
            fontWeight: 700,
            letterSpacing: theme.lsCaps,
            textTransform: "uppercase",
            marginBottom: fontSize * 0.04,
            opacity: eyebrowEnter.opacity,
            transform: `translateY(${eyebrowEnter.translateY}px)`,
            whiteSpace: "nowrap",
          }}
        >
          {eyebrow}
        </span>
      ) : null}

      {/* Drip rail — three offset particles, running the whole dwell so the
          beat is never fully static (§5 closing rule). */}
      <span
        style={{
          position: "relative",
          width: dripW,
          height: dripTravel * 0.45,
          marginBottom: -dripTravel * 0.12,
        }}
      >
        {[0, 470, 940].map((offsetMs) => {
          const phase = dripPhase(frame, fps, { periodMs: 1400, offsetMs });
          return (
            <span
              key={offsetMs}
              style={{
                position: "absolute",
                left: 0,
                top: 0,
                width: dripW,
                height: dripW * 2,
                borderRadius: dripW,
                background: theme.ink,
                opacity: particleOpacity(phase),
                transform: `translateY(${-dripTravel * 0.1 + phase * dripTravel}px)`,
              }}
            />
          );
        })}
      </span>

      {/* minWidth reserves the *final* value's width so the counting digits
          don't grow the box frame by frame and shove the meta line sideways. */}
      <span
        style={{
          display: "inline-block",
          minWidth: estimateWidthPx(raw, fontSize),
          textAlign: align === "right" ? "right" : align === "center" ? "center" : "left",
          fontSize,
          fontWeight: theme.weightHero,
          lineHeight: theme.lhTight,
          letterSpacing: theme.lsTight,
          fontVariantNumeric: "tabular-nums",
          whiteSpace: "nowrap",
          opacity: valueOpacity,
          transform: `scale(${valueScale})`,
          transformOrigin: align === "right" ? "right bottom" : "left bottom",
        }}
      >
        {display}
      </span>

      {meta ? (
        <span
          style={{
            fontFamily: theme.fontMono,
            fontSize: cqh(metaSizeCqh ?? theme.bands.metaCqh, height),
            fontWeight: theme.weightBody,
            letterSpacing: theme.lsCaps,
            textTransform: "uppercase",
            opacity: metaOpacity * 0.85,
            marginTop: fontSize * 0.06,
          }}
        >
          {meta}
        </span>
      ) : null}
    </div>
  );
};
