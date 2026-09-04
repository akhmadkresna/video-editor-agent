import React from "react";
export function StatCallout({ eyebrow, value, unit, align = "center", countDuration = 900 }) {
  const items = align === "center" ? "center" : align === "right" ? "flex-end" : "flex-start";
  const target = typeof value === "number" ? value : parseFloat(value);
  const isNumeric = !isNaN(target) && String(value).trim() === String(target);
  const [display, setDisplay] = React.useState(isNumeric ? 0 : value);
  const [progress, setProgress] = React.useState(isNumeric ? 0 : 1);
  React.useEffect(() => {
    if (!isNumeric) { setDisplay(value); setProgress(1); return; }
    let raf, start;
    const step = (t) => {
      if (start === undefined) start = t;
      const p = Math.min((t - start) / countDuration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplay(Math.round(target * eased));
      setProgress(eased);
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, isNumeric, countDuration]);
  return (
    <div style={{ display: "inline-flex", flexDirection: "column", alignItems: items, fontFamily: "var(--font-display)", color: "var(--paper-0)", textShadow: "0 2px 18px rgba(0,0,0,.55)" }}>
      {eyebrow && <span style={{ fontFamily: "var(--font-body)", fontSize: "var(--fs-label)", fontWeight: 700, background: "var(--scrim-strong)", padding: "6px 14px", borderRadius: "var(--radius-sm)", marginBottom: 4, whiteSpace: "nowrap", animation: "ov-slide-up var(--dur-base) var(--ease-out) both" }}>{eyebrow}</span>}
      <span style={{ position: "relative", width: 3, height: 16, marginBottom: -4 }}>
        <span style={{ position: "absolute", top: 0, left: 0, width: 3, height: 6, borderRadius: 2, background: "var(--paper-0)", animation: "ov-drip 1.1s linear 500ms infinite" }} />
      </span>
      <span style={{ fontSize: "var(--fs-punch-xl)", fontWeight: "var(--fw-black)", lineHeight: "var(--lh-tight)", opacity: 0.35 + progress * 0.65, transform: `scale(${0.6 + progress * 0.4})`, display: "inline-block" }}>{display}</span>
      {unit && <span style={{ fontFamily: "var(--font-body)", fontSize: "var(--fs-caption)", fontWeight: 700, animation: "ov-fade var(--dur-base) var(--ease-out) both", animationDelay: "420ms" }}>{unit}</span>}
    </div>
  );
}
