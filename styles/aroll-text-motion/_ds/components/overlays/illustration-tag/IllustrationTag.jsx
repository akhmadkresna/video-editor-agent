import React from "react";
export function IllustrationTag({ icon = "sparkles", label, corner = "top-right" }) {
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 12, color: "var(--paper-0)", fontFamily: "var(--font-body)", textShadow: "0 2px 12px rgba(0,0,0,.6)", animation: "ov-pop-in var(--dur-base) var(--ease-pop) both, ov-float 2.6s var(--ease-in-out) 0.5s infinite", transformOrigin: corner.replace("-", " ") }}>
      <i data-lucide={icon} style={{ width: 40, height: 40, color: "var(--paper-0)", flexShrink: 0, filter: "drop-shadow(0 2px 6px rgba(0,0,0,.5))" }} />
      <span style={{ fontSize: "var(--fs-punch-md)", fontWeight: "var(--fw-black)", fontFamily: "var(--font-display)", whiteSpace: "nowrap" }}>{label}</span>
    </div>
  );
}
