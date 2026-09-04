import React from "react";

/** Chars shown at `frame`, given a start frame and chars-per-second. */
export function typedLength(
  fullLen: number,
  startFrame: number,
  frame: number,
  fps: number,
  cps: number,
): number {
  const elapsed = (frame - startFrame) / fps;
  if (elapsed <= 0) return 0;
  return Math.min(fullLen, Math.floor(elapsed * cps));
}

/** Word-wise reveal (for assistant `stream`). Returns a substring length. */
export function streamedLength(
  text: string,
  startFrame: number,
  frame: number,
  fps: number,
  wps = 6.5,
): number {
  const elapsed = (frame - startFrame) / fps;
  if (elapsed <= 0) return 0;
  const words = text.split(/(\s+)/); // keep separators
  let budget = Math.floor(elapsed * wps * 2); // separators count as tokens
  let len = 0;
  for (const tok of words) {
    if (budget <= 0) break;
    len += tok.length;
    budget -= 1;
  }
  return Math.min(text.length, len);
}

/** Blinking block caret — deterministic (no CSS animation in renders). */
export const Caret: React.FC<{
  color: string;
  frame: number;
  fps: number;
  visible?: boolean;
}> = ({ color, frame, fps, visible = true }) => {
  if (!visible) return null;
  const on = Math.floor(frame / Math.max(1, Math.round(fps * 0.53))) % 2 === 0;
  return (
    <span
      aria-hidden
      style={{
        display: "inline-block",
        width: "0.09em",
        height: "1.05em",
        marginLeft: "0.06em",
        transform: "translateY(0.16em)",
        background: color,
        opacity: on ? 1 : 0,
      }}
    />
  );
};
