import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { Caption } from "../types";

type Props = {
  captions: Caption[];
  presentation?: {
    style?: "off" | "plain" | "karaoke";
    accent?: string;
    safeBottomRatio?: number;
  };
};

export const CaptionLayer: React.FC<Props> = ({ captions, presentation }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const t = frame / fps;
  if (presentation?.style === "off") return null;
  const active = captions.filter((c) => t >= c.start && t <= c.end);
  if (!active.length) return null;
  const portrait = height > width;
  const accent = presentation?.accent || "#7dd3fc";
  const bottomRatio = presentation?.safeBottomRatio ?? (portrait ? 0.14 : 0.12);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: Math.round(height * bottomRatio),
        pointerEvents: "none",
      }}
    >
      {active.map((c, i) => {
        const karaoke = c.style === "karaoke" && c.words?.length;
        const enter = spring({
          fps,
          frame: Math.max(0, frame - Math.round(c.start * fps)),
          config: { damping: 18, stiffness: 260, mass: 0.55 },
        });
        return (
          <div
            key={`${c.start}-${i}`}
            style={{
              fontFamily: "Instrument Sans, Helvetica, Arial, sans-serif",
              fontWeight: 900,
              fontSize: portrait ? 72 : 54,
              color: "#fff",
              textTransform: "uppercase",
              textAlign: "center",
              textShadow:
                "0 5px 0 rgba(0,0,0,0.95), 0 8px 24px rgba(0,0,0,0.9)",
              maxWidth: portrait ? "88%" : "80%",
              lineHeight: 1.08,
              letterSpacing: "-0.025em",
              transform: `translateY(${interpolate(enter, [0, 1], [24, 0])}px) scale(${interpolate(
                enter,
                [0, 1],
                [0.92, 1],
              )})`,
            }}
          >
            {karaoke
              ? c.words!.map((word, wordIndex) => {
                  const isActive = t >= word.start && t <= word.end;
                  const isPast = t > word.end;
                  return (
                    <React.Fragment key={`${word.start}-${wordIndex}`}>
                      <span
                        style={{
                          display: "inline-block",
                          color: isActive ? accent : isPast ? "#ffffff" : "rgba(255,255,255,0.72)",
                          transform: `scale(${isActive ? 1.1 : 1})`,
                          transition: "none",
                        }}
                      >
                        {word.text}
                      </span>
                      {wordIndex < c.words!.length - 1 ? " " : ""}
                    </React.Fragment>
                  );
                })
              : c.text}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
