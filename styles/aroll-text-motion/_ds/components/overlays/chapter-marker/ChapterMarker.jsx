import React from "react";
export function ChapterMarker({ number, title, corner = "top-left" }) {
  const isLeft = corner.includes("left");
  return (
    <div style={{ position: "absolute", top: "var(--safe-top)", [isLeft ? "left" : "right"]: "var(--safe-x)", display: "flex", alignItems: "center", gap: 12, fontFamily: "var(--font-body)", color: "var(--paper-0)", animation: "ov-slide-up var(--dur-base) var(--ease-out) both", flexDirection: isLeft ? "row" : "row-reverse" }}>
      <span style={{ fontFamily: "var(--font-display)", fontSize: 34, fontWeight: "var(--fw-black)", lineHeight: 1, opacity: .9 }}>{String(number).padStart(2, "0")}</span>
      <span style={{ width: 1, height: 26, background: "var(--line-hair)" }} />
      <span style={{ fontSize: "var(--fs-label)", fontWeight: 700, letterSpacing: "var(--ls-caps)", textTransform: "uppercase" }}>{title}</span>
    </div>
  );
}
