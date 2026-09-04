import React from "react";
export function CTATag({ label, variant = "solid", position = "bottom-center" }) {
  const justify = position.includes("left") ? "flex-start" : position.includes("right") ? "flex-end" : "center";
  const solid = variant === "solid";
  return (
    <div style={{ position: "absolute", bottom: "var(--safe-bottom)", left: 0, right: 0, display: "flex", justifyContent: justify, padding: "0 var(--safe-x)", fontFamily: "var(--font-body)" }}>
      <div style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "12px 22px", borderRadius: "var(--radius-pill)", background: solid ? "var(--paper-0)" : "transparent", border: solid ? "none" : "2px solid var(--paper-0)", color: solid ? "var(--ink-950)" : "var(--paper-0)", fontWeight: 800, fontSize: "var(--fs-label)", animation: "ov-bounce-in var(--dur-base) var(--ease-pop) both", boxShadow: solid ? "0 8px 24px rgba(0,0,0,.35)" : "none" }}>
        {label}
        <span style={{ fontSize: 16 }}>&#8594;</span>
      </div>
    </div>
  );
}