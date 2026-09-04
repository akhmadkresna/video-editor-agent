import React from "react";
export function CalloutArrow({ label, direction = "up-right", length = 70 }) {
  const flipX = direction.includes("left") ? -1 : 1;
  const flipY = direction.includes("up") ? -1 : 1;
  const dx = length * flipX, dy = length * 0.6 * flipY;
  const pad = 30;
  const tipX = pad + (flipX < 0 ? 0 : Math.abs(dx)), tipY = pad + (flipY < 0 ? 0 : Math.abs(dy));
  const originX = pad + (flipX < 0 ? Math.abs(dx) : 0), originY = pad + (flipY < 0 ? Math.abs(dy) : 0);
  const angle = Math.atan2(originY - tipY, originX - tipX) * 180 / Math.PI;
  return (
    <div style={{ position: "relative", width: Math.abs(dx) + pad * 2 + 60, height: Math.abs(dy) + pad * 2, fontFamily: "var(--font-body)" }}>
      <svg width="100%" height="100%" style={{ position: "absolute", inset: 0, overflow: "visible" }}>
        <line x1={originX} y1={originY} x2={tipX} y2={tipY}
          stroke="var(--paper-0)" strokeWidth="2" strokeDasharray="5 6" strokeLinecap="round" style={{ animation: "ov-draw-line var(--dur-slow) var(--ease-out) both, ov-march 900ms linear 680ms infinite" }} />
        <circle cx={originX} cy={originY} r="3.5" fill="var(--paper-0)" />
        <circle cx={tipX} cy={tipY} r="3.5" fill="var(--paper-0)" style={{ animation: "ov-pop-in var(--dur-base) var(--ease-pop) both", animationDelay: "480ms" }} />
      </svg>
      <span style={{ position: "absolute", left: tipX + (flipX < 0 ? -14 : 14), top: tipY - 12, transform: `translateX(${flipX < 0 ? "-100%" : "0"})`, fontSize: "var(--fs-punch-sm)", fontWeight: 700, fontStyle: "italic", color: "var(--paper-0)", textShadow: "0 2px 10px rgba(0,0,0,.6)", whiteSpace: "nowrap", animation: "ov-fade var(--dur-base) var(--ease-out) both", animationDelay: "280ms" }}>{label}</span>
    </div>
  );
}
