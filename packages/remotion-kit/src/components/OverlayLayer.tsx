import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {
  DEFAULT_OVERLAY_STYLE,
  type OverlayStyle,
  type TimelineOverlay,
} from "../types";

const DISPLAY =
  'Syne, "Segoe UI", "Helvetica Neue", Arial, sans-serif';
const UI = '"Instrument Sans", "Segoe UI", system-ui, sans-serif';

function useStyle(style?: OverlayStyle) {
  return {
    ...DEFAULT_OVERLAY_STYLE,
    ...style,
    fonts: { ...DEFAULT_OVERLAY_STYLE.fonts, ...style?.fonts },
    chapter: { ...DEFAULT_OVERLAY_STYLE.chapter, ...style?.chapter },
    emphasis: { ...DEFAULT_OVERLAY_STYLE.emphasis, ...style?.emphasis },
    diagram: { ...DEFAULT_OVERLAY_STYLE.diagram, ...style?.diagram },
    callout: { ...DEFAULT_OVERLAY_STYLE.callout, ...style?.callout },
    chip: { ...DEFAULT_OVERLAY_STYLE.chip, ...style?.chip },
  };
}

/** Softer than the old 140-stiffness snap. */
function softSpring(frame: number, fps: number, delay = 0) {
  return spring({
    frame: Math.max(0, frame - delay),
    fps,
    config: { damping: 20, stiffness: 80 },
  });
}

function popSpring(frame: number, fps: number, delay = 0) {
  return spring({
    frame: Math.max(0, frame - delay),
    fps,
    config: { damping: 11, stiffness: 240 },
  });
}

/** Accent rule that draws left → right (or top → bottom). */
const DrawnLine: React.FC<{
  progress: number;
  widthPx: number;
  heightPx?: number;
  color?: string;
  axis?: "x" | "y";
  origin?: string;
}> = ({
  progress,
  widthPx,
  heightPx = 3,
  color = "#7dd3fc",
  axis = "x",
  origin = "left center",
}) => {
  const p = Math.max(0, Math.min(1, progress));
  return (
    <div
      style={{
        width: widthPx,
        height: heightPx,
        background: color,
        transform: axis === "y" ? `scaleY(${p})` : `scaleX(${p})`,
        transformOrigin: origin,
        borderRadius: Math.min(widthPx, heightPx),
      }}
    />
  );
};

const ID_THOUSANDS = /\d{1,3}(?:\.\d{3})+/;

function findCountable(
  text: string,
): { raw: string; index: number } | null {
  const dotted = text.match(ID_THOUSANDS);
  if (dotted && dotted.index != null) {
    return { raw: dotted[0], index: dotted.index };
  }
  const re = /\d{2,}/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    const before = m.index > 0 ? text[m.index - 1] : "";
    const afterIdx = m.index + m[0].length;
    const after = afterIdx < text.length ? text[afterIdx] : "";
    if (/[\d.]/.test(before) || /[\d.]/.test(after)) continue;
    return { raw: m[0], index: m.index };
  }
  return null;
}

/** Animate a number inside a label (Rp 3.500.000, 250000, …). */
const CountLabel: React.FC<{
  text: string;
  progress: number;
  style?: React.CSSProperties;
}> = ({ text, progress, style }) => {
  const match = findCountable(text);
  if (!match) {
    return <span style={style}>{text}</span>;
  }
  const { raw, index } = match;
  const target = Number(raw.replace(/\./g, ""));
  if (!Number.isFinite(target)) {
    return <span style={style}>{text}</span>;
  }
  const p = Math.max(0, Math.min(1, progress));
  const current = Math.round(target * p);
  const body = current.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return (
    <span style={style}>
      {text.slice(0, index)}
      {body}
      {text.slice(index + raw.length)}
    </span>
  );
};

const AccentPop: React.FC<{
  children: React.ReactNode;
  delay?: number;
  color?: string;
}> = ({ children, delay = 4, color }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = popSpring(frame, fps, delay);
  const scale = interpolate(s, [0, 1], [0.62, 1]);
  const y = interpolate(s, [0, 1], [8, 0]);
  return (
    <span
      style={{
        display: "inline-block",
        color,
        transform: `translateY(${y}px) scale(${scale})`,
        transformOrigin: "left bottom",
      }}
    >
      {children}
    </span>
  );
};

function EnterExit({
  children,
  durationSec,
  exitStartSec,
  style,
}: {
  children: React.ReactNode;
  durationSec: number;
  /** Prefer holding content until this local second, then fade. */
  exitStartSec?: number;
  style?: React.CSSProperties;
}) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = softSpring(frame, fps);
  const y = interpolate(s, [0, 1], [18, 0]);
  const fadeIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const total = Math.max(1, Math.round(durationSec * fps));
  const defaultExitFrames = Math.min(28, Math.max(12, Math.round(fps * 0.9)));
  const exitFrom =
    exitStartSec != null
      ? Math.min(total - 4, Math.max(8, Math.round(exitStartSec * fps)))
      : Math.max(0, total - defaultExitFrames);
  const fadeOut = interpolate(frame, [exitFrom, total], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = Math.min(fadeIn, fadeOut);
  return (
    <div style={{ opacity, transform: `translateY(${y}px)`, ...style }}>
      {children}
    </div>
  );
}

const Chapter: React.FC<{
  ov: TimelineOverlay;
  style: ReturnType<typeof useStyle>;
  h: number;
  w: number;
}> = ({ ov, style, h, w }) => {
  const frame = useCurrentFrame();
  const left = style.chapter?.leftCqw ?? 4.5;
  const top = style.chapter?.topCqh ?? 12;
  const maxW = style.chapter?.maxWidthCqw ?? 42;
  const kickerSize = style.chapter?.kickerSizeCqh ?? 2.4;
  const titleSize = style.chapter?.titleSizeCqh ?? 9;
  const line = interpolate(frame, [10, 28], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        left: `${left}%`,
        top: `${top}%`,
        maxWidth: `${maxW}%`,
        color: style.ink,
        textShadow: "0 8px 28px rgba(0,0,0,0.55)",
      }}
    >
      <EnterExit durationSec={ov.durationSec} exitStartSec={ov.exitStartSec}>
        {ov.kicker ? (
          <div
            style={{
              fontFamily: UI,
              fontSize: Math.round(h * (kickerSize / 100)),
              fontWeight: 600,
              letterSpacing: "0.14em",
              textTransform: "uppercase",
              color: style.accent,
              marginBottom: Math.round(h * 0.012),
            }}
          >
            <AccentPop delay={2} color={style.accent}>
              {ov.kicker}
            </AccentPop>
          </div>
        ) : null}
        <div
          style={{
            fontFamily: DISPLAY,
            fontWeight: 800,
            fontSize: Math.round(h * (titleSize / 100)),
            lineHeight: 0.98,
            letterSpacing: "-0.03em",
          }}
        >
          {ov.text || ov.title}
        </div>
        <div style={{ marginTop: Math.round(h * 0.018) }}>
          <DrawnLine
            progress={line}
            widthPx={Math.round(w * 0.16)}
            color={style.accent}
          />
        </div>
      </EnterExit>
    </div>
  );
};

const Emphasis: React.FC<{
  ov: TimelineOverlay;
  style: ReturnType<typeof useStyle>;
  h: number;
  w: number;
}> = ({ ov, style, h, w }) => {
  const frame = useCurrentFrame();
  const line = interpolate(frame, [8, 24], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const count = interpolate(frame, [2, 22], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const parts = (ov.text || "").split(/\s+/).filter(Boolean);
  const head = parts.slice(0, -1).join(" ");
  const tail = parts.slice(-1)[0] || ov.text || "";
  const left = style.emphasis?.leftCqw ?? 4.5;
  const bottom = style.emphasis?.bottomCqh ?? 28;
  const top = style.emphasis?.topCqh;
  const sizeCqh = style.emphasis?.sizeCqh ?? 16;
  const maxW = style.emphasis?.maxWidthCqw ?? 55;
  const strike = /^(tidak|no|off|deny)$/i.test(tail);
  const strikeP = interpolate(frame, [14, 26], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        left: `${left}%`,
        ...(top != null ? { top: `${top}%` } : { bottom: `${bottom}%` }),
        maxWidth: `${maxW}%`,
        color: style.ink,
        textShadow: "0 8px 28px rgba(0,0,0,0.55)",
      }}
    >
      <EnterExit durationSec={ov.durationSec} exitStartSec={ov.exitStartSec}>
        <div
          style={{
            fontFamily: DISPLAY,
            fontWeight: 800,
            fontSize: Math.round(h * (sizeCqh / 100)),
            lineHeight: 0.92,
            letterSpacing: "-0.04em",
          }}
        >
          {head ? <>{head} </> : null}
          <span style={{ position: "relative", display: "inline-block" }}>
            <AccentPop delay={3} color={style.accent}>
              <CountLabel text={tail} progress={count} />
            </AccentPop>
            {strike ? (
              <span
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  top: "48%",
                  height: 4,
                  background: style.accent,
                  transform: `scaleX(${strikeP})`,
                  transformOrigin: "left center",
                  borderRadius: 4,
                  pointerEvents: "none",
                }}
              />
            ) : null}
          </span>
        </div>
        <div style={{ marginTop: Math.round(h * 0.02) }}>
          <DrawnLine
            progress={line}
            widthPx={Math.round(w * 0.22)}
            color={style.accent}
          />
        </div>
      </EnterExit>
    </div>
  );
};

function resolveStepAtSec(
  steps: string[],
  ov: TimelineOverlay,
): number[] {
  const n = steps.length;
  if (n === 0) return [];
  const raw = ov.stepAtSec;
  if (Array.isArray(raw) && raw.length >= n) {
    return raw.slice(0, n).map((t) => Math.max(0, Number(t) || 0));
  }
  // Even stagger fallback (sentence beats, not per-word).
  const lead = Math.min(0.55, Math.max(0.2, ov.durationSec * 0.12));
  if (n === 1) return [lead];
  const end = Math.max(lead + 0.3, ov.durationSec * 0.92);
  const span = end - lead;
  return Array.from({ length: n }, (_, i) => lead + (span * i) / (n - 1));
}

/** Index | rail gutter | label — rail must never cross the digits. */
function diagramListMetrics(h: number, n: number, stepSizeCqh: number) {
  const fontPx = Math.round(h * (stepSizeCqh / 100));
  const numCol = Math.max(Math.round(fontPx * 1.25), 28);
  const railCol = 22;
  const colGap = 10;
  const rowGap = Math.round(h * 0.012);
  const rowH = Math.max(Math.round(h * 0.048), fontPx + 8);
  const railW = 2;
  const token = 10;
  const railLeft = numCol + colGap + (railCol - railW) / 2;
  const tokenLeft = numCol + colGap + (railCol - token) / 2;
  const railTop = rowH / 2;
  const railH = n > 1 ? (n - 1) * (rowH + rowGap) : 0;
  return {
    fontPx,
    numCol,
    railCol,
    colGap,
    rowGap,
    rowH,
    railW,
    token,
    railLeft,
    tokenLeft,
    railTop,
    railH,
  };
}

const DiagramStep: React.FC<{
  step: string;
  index: number;
  atSec: number;
  durationSec: number;
  exitStartSec?: number;
  accent?: string;
  metrics: ReturnType<typeof diagramListMetrics>;
}> = ({ step, index, atSec, durationSec, exitStartSec, accent, metrics }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const startF = Math.max(0, Math.round(atSec * fps));
  const local = frame - startF;
  const s = softSpring(local, fps);
  const pop = popSpring(local, fps);
  const y = interpolate(s, [0, 1], [14, 0]);
  const tick = interpolate(local, [0, 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeIn = interpolate(local, [0, 7], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const total = Math.max(1, Math.round(durationSec * fps));
  const defaultExitFrames = Math.min(28, Math.max(12, Math.round(fps * 0.9)));
  const exitFrom =
    exitStartSec != null
      ? Math.min(total - 4, Math.max(startF + 6, Math.round(exitStartSec * fps)))
      : Math.max(0, total - defaultExitFrames);
  const fadeOut = interpolate(frame, [exitFrom, total], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = local < 0 ? 0 : Math.min(fadeIn, fadeOut);
  const numScale = interpolate(pop, [0, 1], [0.4, 1]);
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: `${metrics.numCol}px ${metrics.railCol}px 1fr`,
        columnGap: metrics.colGap,
        alignItems: "center",
        minHeight: metrics.rowH,
        fontFamily: UI,
        fontWeight: 700,
        fontSize: metrics.fontPx,
        opacity,
        transform: `translateY(${local < 0 ? 14 : y}px)`,
      }}
    >
      <span
        style={{
          color: accent,
          display: "block",
          width: "100%",
          textAlign: "right",
          fontVariantNumeric: "tabular-nums",
          transform: `scale(${local < 0 ? 0.4 : numScale})`,
          transformOrigin: "right center",
        }}
      >
        {index + 1}
      </span>
      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          alignItems: "center",
        }}
      >
        <DrawnLine
          progress={local < 0 ? 0 : tick}
          widthPx={12}
          heightPx={2}
          color={accent || "#7dd3fc"}
        />
      </div>
      <span>{step}</span>
    </div>
  );
};

const Diagram: React.FC<{
  ov: TimelineOverlay;
  style: ReturnType<typeof useStyle>;
  h: number;
}> = ({ ov, style, h }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const steps = ov.steps || [];
  const stepAt = resolveStepAtSec(steps, ov);
  const left = style.diagram?.leftCqw ?? 4.5;
  const top = style.diagram?.topCqh ?? 10;
  const maxW = style.diagram?.maxWidthCqw ?? 40;
  const stepSizeCqh = style.diagram?.stepSizeCqh ?? 3.6;
  const n = steps.length;
  const metrics = diagramListMetrics(h, n, stepSizeCqh);
  const firstF = Math.round((stepAt[0] ?? 0.2) * fps);
  const lastF = Math.round((stepAt[Math.max(0, n - 1)] ?? 1) * fps);
  const railP = interpolate(frame, [firstF, Math.max(firstF + 1, lastF)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const tokenY = metrics.railH * railP;
  return (
    <div
      style={{
        position: "absolute",
        left: `${left}%`,
        top: `${top}%`,
        maxWidth: `${maxW}%`,
        color: style.ink,
        textShadow: "0 8px 24px rgba(0,0,0,0.5)",
      }}
    >
      <EnterExit durationSec={ov.durationSec} exitStartSec={ov.exitStartSec}>
        <div
          style={{
            fontFamily: UI,
            fontSize: Math.round(h * 0.024),
            fontWeight: 600,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: style.dim,
            marginBottom: Math.round(h * 0.01),
          }}
        >
          {ov.kicker || "Flow"}
        </div>
        <div
          style={{
            fontFamily: DISPLAY,
            fontWeight: 800,
            fontSize: Math.round(h * 0.055),
            letterSpacing: "-0.02em",
            marginBottom: Math.round(h * 0.022),
          }}
        >
          {ov.title || ov.text}
        </div>
      </EnterExit>
      <div style={{ position: "relative" }}>
        {n > 1 ? (
          <div
            style={{
              position: "absolute",
              left: metrics.railLeft,
              top: metrics.railTop,
              width: metrics.railW,
              height: metrics.railH,
              overflow: "hidden",
              pointerEvents: "none",
              zIndex: 0,
            }}
          >
            <DrawnLine
              progress={railP}
              widthPx={metrics.railW}
              heightPx={metrics.railH}
              color={style.accent}
              axis="y"
              origin="top center"
            />
          </div>
        ) : null}
        {n ? (
          <div
            style={{
              position: "absolute",
              left: metrics.tokenLeft,
              top: metrics.railTop + tokenY - metrics.token / 2,
              width: metrics.token,
              height: metrics.token,
              borderRadius: "50%",
              background: style.accent,
              boxShadow: `0 0 12px ${style.accent}`,
              opacity: interpolate(frame, [firstF, firstF + 6], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              pointerEvents: "none",
              zIndex: 2,
            }}
          />
        ) : null}
        <div style={{ display: "grid", rowGap: metrics.rowGap, position: "relative", zIndex: 1 }}>
          {steps.map((step, i) => (
            <DiagramStep
              key={`${i}-${step}`}
              step={step}
              index={i}
              atSec={stepAt[i] ?? 0.55}
              durationSec={ov.durationSec}
              exitStartSec={ov.exitStartSec}
              accent={style.accent}
              metrics={metrics}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

const Chip: React.FC<{
  ov: TimelineOverlay;
  style: ReturnType<typeof useStyle>;
  h: number;
}> = ({ ov, style, h }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const left = style.chip?.leftCqw ?? 4.5;
  const top = style.chip?.topCqh ?? 10;
  const sizeCqh = style.chip?.sizeCqh ?? 3.4;
  const pop = popSpring(frame, fps, 2);
  const scale = interpolate(pop, [0, 1], [0.15, 1]);
  return (
    <div
      style={{
        position: "absolute",
        left: `${left}%`,
        top: `${top}%`,
        color: style.ink,
        fontFamily: UI,
        fontWeight: 600,
        fontSize: Math.round(h * (sizeCqh / 100)),
        textShadow: "0 6px 18px rgba(0,0,0,0.5)",
      }}
    >
      <EnterExit
        durationSec={ov.durationSec}
        exitStartSec={ov.exitStartSec}
        style={{ display: "inline-flex", alignItems: "center", gap: 10 }}
      >
        <span
          style={{
            width: Math.round(h * 0.016),
            height: Math.round(h * 0.016),
            borderRadius: "50%",
            background: style.accent,
            display: "inline-block",
            transform: `scale(${scale})`,
          }}
        />
        {ov.text}
      </EnterExit>
    </div>
  );
};

const Callout: React.FC<{
  ov: TimelineOverlay;
  style: ReturnType<typeof useStyle>;
  h: number;
  w: number;
}> = ({ ov, style, h, w }) => {
  const frame = useCurrentFrame();
  const left = style.callout?.leftCqw ?? 4.5;
  const bottom = style.callout?.bottomCqh ?? 22;
  const top = style.callout?.topCqh;
  const valueSize = style.callout?.valueSizeCqh ?? 14;
  const sourceSize = style.callout?.sourceSizeCqh ?? 2.8;
  const maxW = style.callout?.maxWidthCqw ?? 48;
  const value = ov.value || ov.text || "";
  const sourceLabel = ov.sourceLabel || ov.kicker || "";
  const count = interpolate(frame, [3, 28], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const line = interpolate(frame, [10, 26], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        left: `${left}%`,
        ...(top != null ? { top: `${top}%` } : { bottom: `${bottom}%` }),
        maxWidth: `${maxW}%`,
        color: style.ink,
        textShadow: "0 8px 28px rgba(0,0,0,0.55)",
      }}
    >
      <EnterExit durationSec={ov.durationSec} exitStartSec={ov.exitStartSec}>
        {sourceLabel ? (
          <div
            style={{
              fontFamily: UI,
              fontWeight: 600,
              fontSize: Math.round(h * (sourceSize / 100)),
              color: style.accent,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              marginBottom: Math.round(h * 0.012),
            }}
          >
            {sourceLabel}
          </div>
        ) : null}
        <div
          style={{
            fontFamily: DISPLAY,
            fontWeight: 800,
            fontSize: Math.round(h * (valueSize / 100)),
            lineHeight: 1.05,
          }}
        >
          <CountLabel text={value} progress={count} />
        </div>
        <div style={{ marginTop: Math.round(h * 0.016) }}>
          <DrawnLine
            progress={line}
            widthPx={Math.round(w * 0.18)}
            color={style.accent}
          />
        </div>
        {ov.title ? (
          <div
            style={{
              fontFamily: UI,
              fontWeight: 500,
              fontSize: Math.round(h * 0.028),
              color: style.dim,
              marginTop: Math.round(h * 0.012),
            }}
          >
            {ov.title}
          </div>
        ) : null}
      </EnterExit>
    </div>
  );
};

const OneOverlay: React.FC<{
  ov: TimelineOverlay;
  styleTokens?: OverlayStyle;
}> = ({ ov, styleTokens }) => {
  const { height, width } = useVideoConfig();
  const style = useStyle(styleTokens);
  if (ov.kind === "chapter")
    return <Chapter ov={ov} style={style} h={height} w={width} />;
  if (ov.kind === "emphasis")
    return <Emphasis ov={ov} style={style} h={height} w={width} />;
  if (ov.kind === "diagram") return <Diagram ov={ov} style={style} h={height} />;
  if (ov.kind === "callout")
    return <Callout ov={ov} style={style} h={height} w={width} />;
  if (ov.kind === "chip") return <Chip ov={ov} style={style} h={height} />;
  return null;
};

export const OverlayLayer: React.FC<{
  overlays: TimelineOverlay[];
  styleTokens?: OverlayStyle;
}> = ({ overlays, styleTokens }) => {
  const { fps } = useVideoConfig();
  if (!overlays?.length) return null;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {overlays.map((ov) => {
        const from = Math.round(ov.fromSec * fps);
        const duration = Math.max(1, Math.round(ov.durationSec * fps));
        // Emphasis sits in lower-third — skip left-rail veil (reduces flicker in dense packs).
        const showVeil = ov.kind !== "emphasis";
        return (
          <Sequence key={ov.id} from={from} durationInFrames={duration} name={ov.id}>
            {showVeil ? (
              <AbsoluteFill
                style={{
                  background:
                    "linear-gradient(90deg, rgba(0,0,0,0.42) 0%, rgba(0,0,0,0.1) 32%, transparent 50%)",
                }}
              />
            ) : null}
            <OneOverlay ov={ov} styleTokens={styleTokens} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
