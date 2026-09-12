/**
 * SceneDiagram — a built-on-cue explainer graphic in the A-Roll Text Motion
 * System idiom: white ink and hairline rules directly on the footage, NO
 * panel, NO fills, NO cards, one ink. Vertically centred; the host stays
 * visible. Three variants:
 *
 *   timeline  — a hairline time axis; risered labels reveal per `stepAtSec`
 *   depmap    — a broken "shared layer" rule + platforms hung off vertical
 *               risers, then struck out on the "titik lemahnya" beat
 *   failover  — one provider struck out, a second added, traffic reroutes
 *
 * Layout rule: connectors are axis-aligned (verticals, straight runs, rounded
 * elbows) — never diagonals that cross labels.
 *
 * Data (from the timeline overlay, authored in cover.json):
 *   note      "scene:timeline" | "scene:depmap" | "scene:failover"
 *   steps[]   labels ("head · sub" splits into a label + a meta line)
 *   stepAtSec scene-local reveal cues (from cover `stepStarts`, EDL-remapped)
 *   title     depmap hub label (default "Azure East US")
 *
 * Entry/exit ride the shared overlay fade (OverlayLayer).
 */
import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { EASE_OUT, drawLine, marchOffset, popIn } from "./motion";
import { cqh } from "./sizing";
import type { OverlayTheme } from "./theme";

export type SceneVariant = "timeline" | "depmap" | "failover";

export type SceneDiagramProps = {
  variant: SceneVariant;
  steps: string[];
  stepAtSec?: number[];
  title?: string;
  durationSec: number;
  theme: OverlayTheme;
};

export function sceneVariantFromNote(note?: string | null): SceneVariant | null {
  const m = /scene:(timeline|depmap|failover)/i.exec(note || "");
  return m ? (m[1].toLowerCase() as SceneVariant) : null;
}

/** 0→1 reveal for beat i, over ~durFast, from stepAtSec[i]. Pure. */
function beatAt(
  frame: number,
  fps: number,
  stepAtSec: number[] | undefined,
  i: number,
  durFastMs: number,
): number {
  const at = stepAtSec?.[i];
  if (at == null) return i === 0 ? 1 : 0;
  const s = at * fps;
  return interpolate(frame, [s, s + (durFastMs / 1000) * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
}

const splitLabel = (raw: string): [string, string] => {
  const p = String(raw).split("·").map((s) => s.trim());
  return [p[0] ?? raw, p[1] ?? ""];
};

export const SceneDiagram: React.FC<SceneDiagramProps> = ({
  variant,
  steps,
  stepAtSec,
  title,
  durationSec,
  theme,
}) => {
  const { width, height, fps } = useVideoConfig();
  const frame = useCurrentFrame();

  const enter = popIn(frame, fps, { durMs: theme.durBase, risePx: height * 0.02 });

  // Working box — vertically centred in the frame.
  const boxH = Math.round(height * 0.4);
  const box = {
    x: Math.round(width * 0.09),
    y: Math.round((height - boxH) / 2),
    w: Math.round(width * 0.82),
    h: boxH,
  };

  const label = cqh(theme.bands.labelCqh ?? 3.0, height);
  const meta = cqh(theme.bands.metaCqh ?? 2.2, height);
  const sw = Math.max(2, theme.strokeW || height * 0.003);

  const beats = (steps || []).map((_, i) =>
    beatAt(frame, fps, stepAtSec, i, theme.durFast),
  );

  const common = { box, label, meta, sw, frame, fps, theme, durationSec };
  const body =
    variant === "timeline"
      ? renderTimeline(steps, beats, common)
      : variant === "depmap"
        ? renderDepmap(steps, beats, { ...common, title })
        : renderFailover(steps, beats, common);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        opacity: enter.opacity,
        transform: `translateY(${enter.translateY}px)`,
      }}
    >
      {/* legibility scrim — a soft centred wash, feathering to nothing top and
          bottom. Not a panel. */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.26) ${
            ((box.y - height * 0.05) / height) * 100
          }%, rgba(0,0,0,0.40) 50%, rgba(0,0,0,0.26) ${
            ((box.y + box.h + height * 0.05) / height) * 100
          }%, rgba(0,0,0,0) 100%)`,
        }}
      />
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{
          position: "absolute",
          inset: 0,
          fontFamily: theme.fontSans,
          filter: "drop-shadow(0 2px 8px rgba(0,0,0,0.55))",
        }}
      >
        {body}
      </svg>
    </div>
  );
};

type Common = {
  box: { x: number; y: number; w: number; h: number };
  label: number;
  meta: number;
  sw: number;
  frame: number;
  fps: number;
  theme: OverlayTheme;
  durationSec: number;
};

/** Rounded elbow: horizontal from (x1,y1), step to y2 at a mid x, into (x2,y2). */
function elbow(x1: number, y1: number, x2: number, y2: number, r: number): string {
  if (Math.abs(y2 - y1) < 1) return `M ${x1} ${y1} H ${x2}`;
  const midX = x1 + (x2 - x1) * 0.5;
  const dy = Math.sign(y2 - y1) || 1;
  const rr = Math.max(
    2,
    Math.min(r, Math.abs(x2 - x1) * 0.35, Math.abs(y2 - y1) * 0.4),
  );
  return [
    `M ${x1} ${y1}`,
    `H ${midX - rr}`,
    `Q ${midX} ${y1} ${midX} ${y1 + rr * dy}`,
    `V ${y2 - rr * dy}`,
    `Q ${midX} ${y2} ${midX + rr} ${y2}`,
    `H ${x2}`,
  ].join(" ");
}

// ───────────────────────────── timeline ─────────────────────────────
function renderTimeline(steps: string[], beats: number[], c: Common) {
  const { box, label, meta, sw, theme } = c;
  const n = Math.max(1, steps.length);
  const axisY = box.y + box.h * 0.5;
  const inset = box.w * 0.045;
  const x0 = box.x + inset;
  const x1 = box.x + box.w - inset;
  const gap = (x1 - x0) / Math.max(1, n - 1);
  const reachedIdx = beats.reduce((a, b, i) => (b > 0.5 ? i : a), 0);
  const drawn = interpolate(reachedIdx, [0, n - 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const riser = box.h * 0.18;
  const dot = Math.max(3.5, sw * 1.9);

  return (
    <g strokeLinecap="round" strokeLinejoin="round">
      <line x1={x0} y1={axisY} x2={x1} y2={axisY} stroke={theme.lineHair} strokeWidth={sw} />
      <line x1={x0} y1={axisY} x2={x0 + (x1 - x0) * drawn} y2={axisY} stroke={theme.ink} strokeWidth={sw} />
      {drawn > 0 && drawn < 1 ? (
        <circle cx={x0 + (x1 - x0) * drawn} cy={axisY} r={dot} fill={theme.ink} />
      ) : null}
      {steps.map((raw, i) => {
        const b = beats[i] ?? 0;
        if (b <= 0.001) return null;
        const cx = x0 + gap * i;
        const [head, sub] = splitLabel(raw);
        const gemini = /gemini/i.test(raw);
        const recover = /pulih|recover|~90/i.test(raw);
        const ink = gemini ? theme.inkMuted : theme.ink;
        return (
          <g key={i} opacity={b} transform={`translate(${cx} ${axisY})`}>
            {recover ? (
              <line x1={-gap * 0.28} y1={0} x2={gap * 0.28} y2={0} stroke={theme.ink} strokeWidth={sw * 3} />
            ) : gemini ? (
              <circle r={dot} fill="none" stroke={ink} strokeWidth={sw} strokeDasharray={`${sw * 1.6} ${sw * 1.6}`} />
            ) : (
              <circle r={dot} fill={ink} />
            )}
            <line x1={0} y1={-dot} x2={0} y2={-riser} stroke={gemini ? theme.lineHair : theme.inkMuted} strokeWidth={sw} />
            <text x={0} y={-riser - meta * 0.7} textAnchor="middle" fill={ink} style={{ fontSize: label, fontWeight: theme.weightHero, letterSpacing: theme.lsTight }}>
              {head}
            </text>
            {sub ? (
              <text x={0} y={riser + meta * 1.1} textAnchor="middle" fill={gemini ? theme.inkFaint : theme.inkMuted} style={{ fontSize: meta }}>
                {sub}
              </text>
            ) : null}
          </g>
        );
      })}
    </g>
  );
}

// ───────────────────────────── depmap (shared-layer bus) ─────────────────────
function renderDepmap(steps: string[], beats: number[], c: Common & { title?: string }) {
  const { box, label, meta, sw, frame, fps, theme, durationSec, title } = c;
  const busY = box.y + box.h * 0.3;
  const busX0 = box.x + box.w * 0.06;
  const busX1 = box.x + box.w * 0.94;
  const cxMid = (busX0 + busX1) / 2;
  const hubText = title || "Azure East US";
  const halfW = Math.max(hubText.length * label * 0.32, box.w * 0.11);

  const n = Math.max(1, steps.length);
  const rowY = box.y + box.h * 0.92;
  const cellW = (busX1 - busX0) / n;
  const dot = Math.max(3.5, sw * 1.9);

  const downT = interpolate(
    frame,
    [durationSec * 0.62 * fps, (durationSec * 0.62 + 0.5) * fps],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE_OUT },
  );
  const march = marchOffset(frame, fps, { periodMs: 950, distancePx: sw * 9 });
  const riserGrow = drawLine(frame, fps, { durMs: theme.durBase });

  return (
    <g strokeLinecap="round" strokeLinejoin="round">
      {/* the shared layer — a rule broken around the hub label */}
      <line x1={busX0} y1={busY} x2={cxMid - halfW} y2={busY} stroke={theme.ink} strokeWidth={sw * 1.3} />
      <line x1={cxMid + halfW} y1={busY} x2={busX1} y2={busY} stroke={theme.ink} strokeWidth={sw * 1.3} />
      <text x={cxMid} y={busY + label * 0.36} textAnchor="middle" fill={theme.ink} style={{ fontSize: label * 1.12, fontWeight: theme.weightHero, letterSpacing: theme.lsTight }}>
        {hubText}
      </text>
      {downT > 0.5 ? (
        <line x1={cxMid - halfW * 0.92} y1={busY - label * 0.16} x2={cxMid + halfW * 0.92} y2={busY - label * 0.16} stroke={theme.ink} strokeWidth={sw * 2} opacity={downT} />
      ) : null}

      {steps.map((raw, i) => {
        const b = beats[i] ?? 0;
        if (b <= 0.001) return null;
        const cx = busX0 + cellW * (i + 0.5);
        const [head] = splitLabel(raw);
        const g = b < 1 ? riserGrow : 1;
        const yTop = busY + dot;
        const yBot = rowY - dot;
        return (
          <g key={i} opacity={b}>
            <line
              x1={cx}
              y1={yTop}
              x2={cx}
              y2={yTop + (yBot - yTop) * g}
              stroke={downT > 0.5 ? theme.ink : theme.lineHair}
              strokeWidth={downT > 0.5 ? sw * 1.2 : sw}
              strokeDasharray={downT > 0.5 ? `${sw * 3} ${sw * 2.2}` : undefined}
              strokeDashoffset={downT > 0.5 ? march : 0}
            />
            <circle cx={cx} cy={busY} r={dot * 0.68} fill={theme.ink} />
            <circle cx={cx} cy={rowY} r={dot} fill={theme.ink} />
            <text x={cx} y={rowY + meta * 1.6} textAnchor="middle" fill={theme.ink} style={{ fontSize: label * 0.95, fontWeight: theme.weightHero, letterSpacing: theme.lsTight }}>
              {head}
            </text>
          </g>
        );
      })}

      {downT > 0.5 ? (
        <text x={cxMid} y={rowY + meta * 3.3} textAnchor="middle" fill={theme.inkMuted} style={{ fontSize: meta, letterSpacing: theme.lsCaps, textTransform: "uppercase" }}>
          satu titik — semua kena
        </text>
      ) : null}
    </g>
  );
}

// ───────────────────────────── failover ─────────────────────────────
function renderFailover(steps: string[], beats: number[], c: Common) {
  const { box, label, meta, sw, frame, fps, theme } = c;
  const b0 = beats[0] ?? 1;
  const b1 = beats[1] ?? 0;
  const b2 = beats[2] ?? 0;

  const baseY = box.y + box.h * 0.38;
  const appX = box.x + box.w * 0.13;
  const provX = box.x + box.w * 0.66;
  const bY = box.y + box.h * 0.8;
  const dot = Math.max(3.5, sw * 1.9);
  const march = marchOffset(frame, fps, { periodMs: 950, distancePx: sw * 9 });
  const r = box.h * 0.14;

  const aFail = b0 > 0.5;
  const rerouted = b2 > 0.5;
  const appLabel = rerouted ? "App ✓" : aFail ? "App ✗" : "App";

  const grow = drawLine(frame, fps, { durMs: theme.durBase });
  const aEndX = appX + dot + (provX - dot - (appX + dot)) * (b0 < 1 ? grow : 1);
  const aName = steps[0] || "Provider A";

  return (
    <g strokeLinecap="round" strokeLinejoin="round">
      <circle cx={appX} cy={baseY} r={dot} fill={theme.ink} />
      <text x={appX} y={baseY - dot - meta * 0.7} textAnchor="middle" fill={theme.ink} style={{ fontSize: label, fontWeight: theme.weightHero, letterSpacing: theme.lsTight }}>
        {appLabel}
      </text>

      {/* App → Provider A (straight run) */}
      <line
        x1={appX + dot}
        y1={baseY}
        x2={aEndX}
        y2={baseY}
        stroke={rerouted ? theme.lineHair : theme.ink}
        strokeWidth={sw}
        strokeDasharray={rerouted ? `${sw * 3} ${sw * 2.2}` : undefined}
        opacity={b0}
      />
      <g opacity={b0}>
        <circle cx={provX} cy={baseY} r={dot} fill={aFail ? "none" : theme.ink} stroke={theme.ink} strokeWidth={sw} />
        <text x={provX + dot + meta * 0.6} y={baseY + meta * 0.34} textAnchor="start" fill={aFail ? theme.inkMuted : theme.ink} style={{ fontSize: label, fontWeight: theme.weightHero, letterSpacing: theme.lsTight }}>
          {aName}
        </text>
        {aFail ? (
          <line
            x1={provX + dot + meta * 0.35}
            y1={baseY}
            x2={provX + dot + meta * 0.6 + aName.length * label * 0.56}
            y2={baseY}
            stroke={theme.ink}
            strokeWidth={sw * 1.8}
          />
        ) : null}
      </g>

      {/* App → Provider B (elbow, appears at beat 1) */}
      {b1 > 0.01 ? (
        <g opacity={b1}>
          <path
            d={elbow(appX + dot, baseY, provX - dot, bY, r)}
            fill="none"
            stroke={rerouted ? theme.ink : theme.lineHair}
            strokeWidth={rerouted ? sw * 1.3 : sw}
            strokeDasharray={rerouted ? `${sw * 3} ${sw * 2.2}` : undefined}
            strokeDashoffset={rerouted ? march : 0}
          />
          <circle cx={provX} cy={bY} r={dot} fill={theme.ink} />
          <text x={provX + dot + meta * 0.6} y={bY + meta * 0.34} textAnchor="start" fill={theme.ink} style={{ fontSize: label, fontWeight: theme.weightHero, letterSpacing: theme.lsTight }}>
            {steps[1] || "Provider ke-2"}
          </text>
        </g>
      ) : null}

      <text
        x={box.x + box.w / 2}
        y={box.y + box.h * 1.04}
        textAnchor="middle"
        fill={theme.inkMuted}
        style={{ fontSize: meta, letterSpacing: theme.lsCaps, textTransform: "uppercase" }}
      >
        {rerouted
          ? steps[2] || "trafik pindah — layanan tetap jalan"
          : b1 > 0.5
            ? "pasang provider ke-2"
            : "satu provider — lumpuh saat down"}
      </text>
    </g>
  );
}
