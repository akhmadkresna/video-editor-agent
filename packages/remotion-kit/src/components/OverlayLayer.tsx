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

function EnterExit({
  children,
  durationSec,
  exitStartSec,
}: {
  children: React.ReactNode;
  durationSec: number;
  /** Prefer holding content until this local second, then fade. */
  exitStartSec?: number;
}) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 18, stiffness: 140 } });
  const y = interpolate(s, [0, 1], [14, 0]);
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
    <div style={{ opacity, transform: `translateY(${y}px)` }}>{children}</div>
  );
}

const Chapter: React.FC<{
  ov: TimelineOverlay;
  style: ReturnType<typeof useStyle>;
  h: number;
}> = ({ ov, style, h }) => {
  const left = style.chapter?.leftCqw ?? 4.5;
  const top = style.chapter?.topCqh ?? 12;
  const maxW = style.chapter?.maxWidthCqw ?? 42;
  const kickerSize = style.chapter?.kickerSizeCqh ?? 2.4;
  const titleSize = style.chapter?.titleSizeCqh ?? 9;
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
          {ov.kicker}
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
  const line = interpolate(frame, [6, 18], [0, 1], {
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
          {head ? (
            <>
              {head}{" "}
              <span style={{ color: style.accent }}>{tail}</span>
            </>
          ) : (
            <span style={{ color: style.accent }}>{tail}</span>
          )}
        </div>
        <div
          style={{
            marginTop: Math.round(h * 0.02),
            width: Math.round(w * 0.22),
            height: 3,
            background: style.accent,
            transform: `scaleX(${line})`,
            transformOrigin: "left center",
          }}
        />
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

const DiagramStep: React.FC<{
  step: string;
  index: number;
  atSec: number;
  durationSec: number;
  exitStartSec?: number;
  accent?: string;
  h: number;
}> = ({ step, index, atSec, durationSec, exitStartSec, accent, h }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const startF = Math.max(0, Math.round(atSec * fps));
  const local = frame - startF;
  const s = spring({
    frame: Math.max(0, local),
    fps,
    config: { damping: 16, stiffness: 160 },
  });
  const y = interpolate(s, [0, 1], [12, 0]);
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
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "auto 1fr",
        gap: 14,
        alignItems: "center",
        fontFamily: UI,
        fontWeight: 700,
        fontSize: Math.round(h * 0.036),
        opacity,
        transform: `translateY(${local < 0 ? 12 : y}px)`,
      }}
    >
      <span style={{ color: accent }}>{index + 1}</span>
      <span>{step}</span>
    </div>
  );
};

const Diagram: React.FC<{
  ov: TimelineOverlay;
  style: ReturnType<typeof useStyle>;
  h: number;
}> = ({ ov, style, h }) => {
  const steps = ov.steps || [];
  const stepAt = resolveStepAtSec(steps, ov);
  const left = style.diagram?.leftCqw ?? 4.5;
  const top = style.diagram?.topCqh ?? 10;
  const maxW = style.diagram?.maxWidthCqw ?? 40;
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
      <div style={{ display: "grid", gap: Math.round(h * 0.012) }}>
        {steps.map((step, i) => (
          <DiagramStep
            key={`${i}-${step}`}
            step={step}
            index={i}
            atSec={stepAt[i] ?? 0.55}
            durationSec={ov.durationSec}
            exitStartSec={ov.exitStartSec}
            accent={style.accent}
            h={h}
          />
        ))}
      </div>
    </div>
  );
};

const Chip: React.FC<{
  ov: TimelineOverlay;
  style: ReturnType<typeof useStyle>;
  h: number;
}> = ({ ov, style, h }) => {
  const left = style.chip?.leftCqw ?? 4.5;
  const top = style.chip?.topCqh ?? 10;
  const sizeCqh = style.chip?.sizeCqh ?? 3.4;
  return (
  <div
    style={{
      position: "absolute",
      left: `${left}%`,
      top: `${top}%`,
      display: "inline-flex",
      alignItems: "center",
      gap: 10,
      color: style.ink,
      fontFamily: UI,
      fontWeight: 600,
      fontSize: Math.round(h * (sizeCqh / 100)),
      textShadow: "0 6px 18px rgba(0,0,0,0.5)",
    }}
  >
    <EnterExit durationSec={ov.durationSec} exitStartSec={ov.exitStartSec}>
      <span
        style={{
          width: Math.round(h * 0.016),
          height: Math.round(h * 0.016),
          borderRadius: "50%",
          background: style.accent,
          display: "inline-block",
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
}> = ({ ov, style, h }) => {
  const left = style.callout?.leftCqw ?? 4.5;
  const bottom = style.callout?.bottomCqh ?? 22;
  const top = style.callout?.topCqh;
  const valueSize = style.callout?.valueSizeCqh ?? 14;
  const sourceSize = style.callout?.sourceSizeCqh ?? 2.8;
  const maxW = style.callout?.maxWidthCqw ?? 48;
  const value = ov.value || ov.text || "";
  const sourceLabel = ov.sourceLabel || ov.kicker || "";
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
          {value}
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
  if (ov.kind === "chapter") return <Chapter ov={ov} style={style} h={height} />;
  if (ov.kind === "emphasis")
    return <Emphasis ov={ov} style={style} h={height} w={width} />;
  if (ov.kind === "diagram") return <Diagram ov={ov} style={style} h={height} />;
  if (ov.kind === "callout") return <Callout ov={ov} style={style} h={height} />;
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
