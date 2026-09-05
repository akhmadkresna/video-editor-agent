/**
 * PunchWord — the hero type treatment.
 * Port of `_ds/components/overlays/punch-word/PunchWord.jsx`.
 *
 * Drives `title` (xl), `emphasis` (lg), `quote` (md) and the valueless
 * `callout` fallback. Words pop in one at a time; an optional `accent` line
 * continues the *same* stagger sequence rather than restarting it (spec §3).
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { blinkStep, popIn, underlineSweep, wordStaggerDelay } from "./motion";
import { cqh, cqw, fitHeadline, resolveBandCqh, type SizeName } from "./sizing";
import type { OverlayTheme } from "./theme";

export type PunchWordProps = {
  text: string;
  eyebrow?: string;
  /** Rendered as a second line, same size, continuing the word stagger. */
  accent?: string;
  size?: SizeName;
  align?: "left" | "center" | "right";
  underline?: boolean;
  cursor?: boolean;
  maxWidthCqw?: number;
  /** Vertical budget from the zone box, so a long line can't wall off the frame. */
  boxHeightPx?: number;
  maxLines?: number;
  theme: OverlayTheme;
};

export const PunchWord: React.FC<PunchWordProps> = ({
  text,
  eyebrow,
  accent,
  size = "lg",
  align = "left",
  underline = false,
  cursor = false,
  maxWidthCqw = 48,
  boxHeightPx,
  maxLines = 3,
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const words = String(text || "").trim().split(/\s+/).filter(Boolean);
  const accentWords = String(accent || "").trim().split(/\s+/).filter(Boolean);
  if (!words.length && !accentWords.length) return null;

  const boxWidthPx = cqw(maxWidthCqw, width);
  const basePx = cqh(resolveBandCqh(size, theme), height);
  // Fit the whole thing (both lines) so a long accent can't push it off-box.
  const fontSize = fitHeadline({
    text: [text, accent].filter(Boolean).join(" "),
    basePx,
    boxWidthPx,
    boxHeightPx,
    maxLines,
    lineHeight: theme.lhTight,
  });

  const totalWords = words.length + accentWords.length;
  const stagger = { wordStaggerMs: theme.wordStaggerMs, wordCount: totalWords };
  const tailDelay = wordStaggerDelay(totalWords, stagger);
  // The DS's 6px rise is tuned for ~64px type; at a 238px hero it would read as
  // a twitch, so scale it with the type.
  const risePx = 6 * (fontSize / 64);

  const renderWord = (w: string, i: number, italic = false) => {
    const { scale, opacity, translateY } = popIn(frame, fps, {
      durMs: theme.durBase,
      delayMs: wordStaggerDelay(i, stagger),
      risePx,
    });
    return (
      <span
        key={`${i}-${w}`}
        style={{
          display: "inline-block",
          marginRight: "0.28em",
          fontStyle: italic ? "italic" : undefined,
          opacity,
          transform: `translateY(${translateY}px) scale(${scale})`,
        }}
      >
        {w}
      </span>
    );
  };

  const headlineStyle: React.CSSProperties = {
    fontSize,
    fontWeight: theme.weightHero,
    lineHeight: theme.lhTight,
    letterSpacing: theme.lsTight,
  };

  return (
    <div
      style={{
        fontFamily: theme.fontSans,
        textAlign: align,
        display: "inline-flex",
        flexDirection: "column",
        alignItems: align === "center" ? "center" : align === "right" ? "flex-end" : "flex-start",
        gap: Math.max(4, fontSize * 0.06),
        color: theme.ink,
        textShadow: theme.textShadow,
        maxWidth: boxWidthPx,
      }}
    >
      {eyebrow ? (
        <span
          style={{
            fontSize: cqh(theme.bands.eyebrowCqh, height),
            fontWeight: 700,
            letterSpacing: theme.lsCaps,
            textTransform: "uppercase",
            opacity: 0.82,
          }}
        >
          {eyebrow}
        </span>
      ) : null}

      <span style={{ display: "inline-flex", alignItems: "baseline" }}>
        <span style={headlineStyle}>
          {words.map((w, i) => renderWord(w, i))}
          {accentWords.length ? (
            <>
              <br />
              {accentWords.map((w, i) => renderWord(w, words.length + i, true))}
            </>
          ) : null}
        </span>
        {cursor ? (
          <span
            style={{
              display: "inline-block",
              width: Math.max(5, fontSize * (size === "xl" ? 0.06 : 0.05)),
              height: "0.78em",
              background: theme.ink,
              marginLeft: fontSize * 0.1,
              alignSelf: "center",
              opacity: blinkStep(frame, fps, { periodMs: 1100, delayMs: tailDelay + 200 }),
            }}
          />
        ) : null}
      </span>

      {underline ? (
        <span
          style={{
            display: "block",
            height: Math.max(3, fontSize * 0.06),
            width: "38%",
            minWidth: fontSize * 0.9,
            background: theme.ink,
            transformOrigin: "left center",
            transform: `scaleX(${underlineSweep(frame, fps, {
              durMs: theme.durSlow,
              delayMs: tailDelay + 120,
            })})`,
          }}
        />
      ) : null}
    </div>
  );
};
