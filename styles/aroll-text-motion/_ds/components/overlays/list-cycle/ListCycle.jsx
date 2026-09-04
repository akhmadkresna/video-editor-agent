import React from "react";
export function ListCycle({ prefix, items = [], activeIndex, interval = 1500 }) {
  const [auto, setAuto] = React.useState(0);
  React.useEffect(() => {
    if (activeIndex !== undefined) return;
    const t = setInterval(() => setAuto(v => (v + 1) % Math.max(items.length, 1)), interval);
    return () => clearInterval(t);
  }, [items.length, interval, activeIndex]);
  const active = activeIndex !== undefined ? activeIndex : auto;
  return (
    <div style={{ display: "flex", alignItems: "stretch", gap: 14, fontFamily: "var(--font-body)" }}>
      <span style={{ fontSize: "var(--fs-punch-md)", fontWeight: "var(--fw-black)", color: "var(--paper-0)", fontFamily: "var(--font-display)" }}>{prefix}</span>
      <div style={{ position: "relative", overflow: "hidden", minWidth: 220 }}>
        {items.map((it, i) => (
          <div key={i} style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", opacity: i === active ? 1 : 0, transition: "opacity var(--dur-base) var(--ease-out)", transform: "translateY(calc((var(--fs-punch-md) - var(--fs-caption)) * -0.18))" }}>
            <span style={{ fontSize: "var(--fs-caption)", fontWeight: 600, color: "var(--paper-300)", whiteSpace: "nowrap", transform: i === active ? "translateY(0)" : i < active ? "translateY(-14px)" : "translateY(14px)", transition: "transform var(--dur-base) var(--ease-out)" }}>{it}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
