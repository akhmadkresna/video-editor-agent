import React from "react";
export function PunchWord({ text, eyebrow, size = "lg", align = "left", underline = false, cursor = false }) {
  const fs = size === "xl" ? "var(--fs-punch-xl)" : size === "md" ? "var(--fs-punch-md)" : "var(--fs-punch-lg)";
  const items = String(text).trim().split(/\s+/);
  return (
    <div style={{ fontFamily: "var(--font-display)", textAlign: align, display: "inline-flex", flexDirection: "column", alignItems: align === "center" ? "center" : align === "right" ? "flex-end" : "flex-start", gap: 6, color: "var(--paper-0)", textShadow: "0 2px 18px rgba(0,0,0,.55)" }}>
      {eyebrow && <span style={{ fontSize: "var(--fs-eyebrow)", fontWeight: 700, letterSpacing: "var(--ls-caps)", textTransform: "uppercase", opacity: .82 }}>{eyebrow}</span>}
      <span style={{ display: "inline-flex", alignItems: "baseline" }}>
        <span style={{ fontSize: fs, fontWeight: "var(--fw-black)", lineHeight: "var(--lh-tight)", letterSpacing: "var(--ls-tight)" }}>
          {items.map((w, i) => (
            <span key={i} style={{ display: "inline-block", marginRight: i < items.length - 1 ? "0.28em" : 0, animation: `ov-pop-in var(--dur-base) var(--ease-pop) both`, animationDelay: `${i * 90}ms` }}>{w}</span>
          ))}
        </span>
        {cursor && <span style={{ display: "inline-block", width: Math.max(fs === "var(--fs-punch-xl)" ? 8 : 6, 5), height: "0.78em", background: "var(--paper-0)", marginLeft: 8, alignSelf: "center", animation: `ov-blink 1.1s steps(1) ${items.length * 90 + 200}ms infinite` }} />}
      </span>
      {underline && <span style={{ display: "block", height: 6, width: "38%", background: "var(--paper-0)", transformOrigin: "left", animation: "ov-underline var(--dur-slow) var(--ease-out) both", animationDelay: `${items.length * 90 + 120}ms` }} />}
    </div>
  );
}
