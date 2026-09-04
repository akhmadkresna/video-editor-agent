import React from "react";
export function AnnotationGrid({ density = 3 }) {
  const lines = Array.from({ length: density - 1 });
  return (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none", animation: "ov-grid-pulse 4.5s var(--ease-in-out) infinite" }}>
      {lines.map((_, i) => (
        <span key={"v" + i} style={{ position: "absolute", top: 0, bottom: 0, left: `${((i + 1) / density) * 100}%`, width: 1, borderLeft: "1px dashed var(--line-hair)" }} />
      ))}
      {lines.map((_, i) => (
        <span key={"h" + i} style={{ position: "absolute", left: 0, right: 0, top: `${((i + 1) / density) * 100}%`, height: 1, borderTop: "1px dashed var(--line-hair)" }} />
      ))}
      <svg width="46" height="46" viewBox="0 0 46 46" style={{ position: "absolute", top: 14, left: 14, opacity: .5 }}>
        <path d="M0 0 L46 0 L0 30 Z" fill="var(--paper-0)" />
      </svg>
      <svg width="52" height="52" viewBox="0 0 52 52" style={{ position: "absolute", bottom: 10, right: 10, opacity: .5 }}>
        <path d="M52 52 L0 52 L52 18 Z" fill="var(--paper-0)" />
      </svg>
    </div>
  );
}
