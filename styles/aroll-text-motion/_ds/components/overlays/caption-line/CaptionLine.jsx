import React from "react";
export function CaptionLine({ text, speaker, size = "md" }) {
  const fs = size === "lg" ? "calc(var(--fs-caption) * 1.35)" : size === "sm" ? "calc(var(--fs-caption) * 0.8)" : "var(--fs-caption)";
  return (
    <div style={{ position: "absolute", bottom: "var(--safe-bottom)", left: "var(--safe-x)", right: "var(--safe-x)", fontFamily: "var(--font-body)", animation: "ov-fade var(--dur-base) var(--ease-out) both" }}>
      {speaker && <div style={{ fontSize: "var(--fs-eyebrow)", fontWeight: 700, letterSpacing: "var(--ls-caps)", textTransform: "uppercase", color: "var(--paper-0)", opacity: .7, marginBottom: 4 }}>{speaker}</div>}
      <div style={{ fontSize: fs, fontWeight: 600, color: "var(--paper-0)", lineHeight: "var(--lh-snug)", textShadow: "0 2px 14px rgba(0,0,0,.6)" }}>{text}</div>
    </div>
  );
}
