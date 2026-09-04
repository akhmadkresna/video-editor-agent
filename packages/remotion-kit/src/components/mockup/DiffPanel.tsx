import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import type { MockDiffMark, MockStyle } from "../../types";
import { mockFont } from "./fonts";

/** Render text with marked spans (add = underline, del = strike). */
function marked(
  text: string,
  marks: MockDiffMark[] | undefined,
  style: MockStyle,
  reveal: number,
): React.ReactNode {
  if (!marks?.length) return text;
  const sorted = [...marks].sort((a, b) => a.span[0] - b.span[0]);
  const out: React.ReactNode[] = [];
  let cursor = 0;
  sorted.forEach((m, i) => {
    const [a, b] = m.span;
    if (a > cursor) out.push(text.slice(cursor, a));
    const isDel = m.type === "del";
    out.push(
      <span
        key={i}
        style={{
          color: isDel ? style.diffDel : style.diffAdd,
          textDecoration: isDel ? "line-through" : "underline",
          textDecorationThickness: "0.12em",
          textUnderlineOffset: "0.16em",
          opacity: interpolate(reveal, [0, 1], [0.25, 1]),
        }}
      >
        {text.slice(a, b)}
      </span>,
    );
    cursor = b;
  });
  if (cursor < text.length) out.push(text.slice(cursor));
  return out;
}

/** Before / after text, side by side. `after` wipes in from the left a beat
 *  after `before`; marks fade up once revealed. */
export const DiffPanel: React.FC<{
  before: string;
  after: string;
  beforeMarks?: MockDiffMark[];
  afterMarks?: MockDiffMark[];
  atSec?: number;
  style: MockStyle;
}> = ({ before, after, beforeMarks, afterMarks, atSec = 0.3, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const beforeIn = interpolate(t, [atSec, atSec + 0.3], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const afterWipe = interpolate(t, [atSec + 0.7, atSec + 1.5], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const markReveal = interpolate(t, [atSec + 1.6, atSec + 2.3], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const col: React.CSSProperties = {
    flex: 1,
    padding: "3.4cqw 3cqw",
    fontSize: "1.75cqw",
    lineHeight: 1.7,
    color: style.asstInk,
  };
  const label: React.CSSProperties = {
    fontFamily: mockFont.mono,
    fontSize: "1.2cqw",
    letterSpacing: "0.14em",
    textTransform: "uppercase",
    color: style.chromeTitle,
    marginBottom: "1.4cqw",
  };

  return (
    <div style={{ flex: 1, display: "flex" }}>
      <div style={{ ...col, opacity: beforeIn }}>
        <div style={label}>Sebelum</div>
        <div>{marked(before, beforeMarks, style, 1)}</div>
      </div>
      <div style={{ width: 1, background: style.railLine }} />
      <div
        style={{
          ...col,
          clipPath: `inset(0 ${(1 - afterWipe) * 100}% 0 0)`,
        }}
      >
        <div style={label}>Sesudah</div>
        <div>{marked(after, afterMarks, style, markReveal)}</div>
      </div>
    </div>
  );
};
