import React from "react";
export function FlowSteps({ steps = [], direction = "horizontal", activeIndex = -1 }) {
  const isH = direction === "horizontal";
  return (
    <div style={{ display: "flex", flexDirection: isH ? "row" : "column", alignItems: isH ? "center" : "flex-start", gap: 0, fontFamily: "var(--font-body)" }}>
      {steps.map((s, i) => (
        <React.Fragment key={i}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 16px", borderRadius: "var(--radius-pill)", background: i <= activeIndex ? "var(--paper-0)" : "var(--glass-white-12)", color: i <= activeIndex ? "var(--ink-950)" : "var(--paper-0)", border: "1px solid var(--line-hair)", fontSize: "var(--fs-label)", fontWeight: 700, animation: "ov-pop-in var(--dur-base) var(--ease-pop) both", animationDelay: `${i * 120}ms`, whiteSpace: "nowrap" }}>
            <span style={{ width: 20, height: 20, borderRadius: "50%", display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 11, background: i <= activeIndex ? "var(--ink-950)" : "var(--paper-0)", color: i <= activeIndex ? "var(--paper-0)" : "var(--ink-950)" }}>{i + 1}</span>
            {s.label}
          </div>
          {i < steps.length - 1 && (
            <div style={{ width: isH ? 36 : 4, height: isH ? 4 : 24, margin: isH ? "0 4px" : "2px 18px", position: "relative" }}>
              <div style={{ position: "absolute", inset: 0, borderRadius: 2, background: "var(--line-hair)" }} />
              <div style={{ position: "absolute", top: isH ? "50%" : 0, left: isH ? 0 : "50%", width: isH ? 8 : 8, height: isH ? 8 : 8, marginTop: isH ? -4 : 0, marginLeft: isH ? 0 : -4, borderRadius: "50%", background: "var(--paper-0)", boxShadow: "0 0 8px 2px rgba(255,255,255,.7)", animation: `${isH ? "ov-flow-x" : "ov-flow-y"} 1.1s var(--ease-in-out) infinite`, animationDelay: `${i * 140}ms` }} />
            </div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
}
