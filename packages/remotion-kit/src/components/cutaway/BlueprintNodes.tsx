import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { TimelineCutaway } from "../../types";
import {
  ACCENT,
  assetSrc,
  Backdrop,
  cueSpring,
  Glyph,
  MONO,
  REJECT,
  rupiah,
  runningBalance,
  sceneBeats,
  signed,
} from "./shared";

const PLATE = "#0a1a25";
const LINE = "rgba(125,211,252,0.85)";
const FAINT = "rgba(125,211,252,0.16)";
const INK = "#eaf6ff";
const DIM = "rgba(234,246,255,0.55)";

const Ticks: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  len?: number;
}> = ({ x, y, w, h, len = 26 }) => (
  <g stroke={LINE} strokeWidth={4} fill="none">
    <path d={`M ${x} ${y + len} V ${y} H ${x + len}`} />
    <path d={`M ${x + w - len} ${y} H ${x + w} V ${y + len}`} />
    <path d={`M ${x + w} ${y + h - len} V ${y + h} H ${x + w - len}`} />
    <path d={`M ${x + len} ${y + h} H ${x} V ${y + h - len}`} />
  </g>
);

/**
 * The ledger drawn as an engineering schematic: sources are nodes, money runs
 * on orthogonal traces, and the ledger is a plotted assembly with dimension
 * annotations. Drafting language — mono annotation, ticks, no panels.
 */
export const BlueprintNodes: React.FC<{ cutaway: TimelineCutaway }> = ({
  cutaway,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;
  const b = sceneBeats(cutaway);
  const sp = (cue: number, damping = 16, stiffness = 130) =>
    cueSpring(frame, fps, cue, damping, stiffness);

  const balance = runningBalance(t, b.feeds, b.opening, b.arrivalOf, b.openSec);
  const lockPop = b.lockSec != null ? sp(b.lockSec, 11, 180) : 0;

  const nodeX = Math.round(width * 0.15);
  const nodeY = (i: number) => Math.round(height * 0.31 + i * height * 0.155);
  const busX = Math.round(width * 0.365);
  const blk = {
    x: Math.round(width * 0.51),
    y: Math.round(height * 0.28),
    w: Math.round(width * 0.32),
    h: Math.round(height * 0.41),
  };
  const rowY = (i: number) => blk.y + Math.round(height * 0.085) + i * Math.round(height * 0.055);
  const mono = (size: number) => ({
    fontFamily: MONO,
    fontSize: Math.round(height * size),
    letterSpacing: "0.14em",
  });

  const annot = [
    { x: width * 0.035, y: height * 0.055, text: "BUKU KAS / IMMUTABLE" },
    { x: width * 0.82, y: height * 0.055, text: "REV 04" },
    { x: width * 0.035, y: height * 0.94, text: "SKALA 1:1" },
    { x: width * 0.75, y: height * 0.94, text: "ODOO AUTO-JOURNAL" },
  ];

  return (
    <AbsoluteFill style={{ background: PLATE, overflow: "hidden" }}>
      <Backdrop cutaway={cutaway} plate={PLATE} defaultDim={0.7} />

      {/* Drafting grid */}
      <AbsoluteFill
        style={{
          opacity: 0.5,
          backgroundImage: `linear-gradient(${FAINT} 1px, transparent 1px), linear-gradient(90deg, ${FAINT} 1px, transparent 1px), linear-gradient(rgba(125,211,252,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(125,211,252,0.3) 1px, transparent 1px)`,
          backgroundSize: "34px 34px, 34px 34px, 170px 170px, 170px 170px",
        }}
      />

      {/* Sheet frame + drafting notes */}
      <div
        style={{
          position: "absolute",
          left: width * 0.025,
          top: height * 0.04,
          right: width * 0.025,
          bottom: height * 0.04,
          border: `2px solid ${FAINT}`,
        }}
      />
      {annot.map((a) => (
        <div
          key={a.text}
          style={{
            position: "absolute",
            left: a.x,
            top: a.y,
            color: DIM,
            ...mono(0.017),
            opacity: sp(b.openSec),
          }}
        >
          {a.text}
        </div>
      ))}

      {/* Traces + nodes + the plotted assembly */}
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {b.feeds.map((f, i) => {
          const draw = interpolate(t, [f.atSec, f.atSec + 0.5], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          if (draw <= 0) return null;
          const y = nodeY(i);
          const midY = blk.y + blk.h / 2;
          const d = `M ${nodeX + 34} ${y} H ${busX} V ${midY} H ${blk.x}`;
          const len = 1400;
          return (
            <g key={`trace-${f.label}`}>
              <path
                d={d}
                fill="none"
                stroke={(f.amount ?? 0) < 0 ? "rgba(234,246,255,0.4)" : LINE}
                strokeWidth={3}
                strokeDasharray={len}
                strokeDashoffset={len * (1 - draw)}
              />
              {draw > 0.4 ? (
                <circle cx={busX} cy={y} r={6} fill={LINE} />
              ) : null}
            </g>
          );
        })}

        {/* Source nodes */}
        {b.feeds.map((f, i) => {
          const s = sp(Math.max(0.15, f.atSec - 0.5), 15, 140);
          if (s <= 0) return null;
          const y = nodeY(i);
          return (
            <g key={`node-${f.label}`} opacity={s}>
              <circle
                cx={nodeX}
                cy={y}
                r={interpolate(s, [0, 1], [10, 34])}
                fill="none"
                stroke={(f.amount ?? 0) < 0 ? "rgba(234,246,255,0.55)" : LINE}
                strokeWidth={3}
              />
              <circle cx={nodeX} cy={y} r={6} fill={LINE} />
              <path
                d={`M ${nodeX} ${y - 52} V ${y - 34}`}
                stroke={FAINT}
                strokeWidth={2}
              />
            </g>
          );
        })}

        {/* Ledger assembly outline + corner ticks */}
        <g opacity={sp(b.openSec, 18, 120)}>
          <rect
            x={blk.x}
            y={blk.y}
            width={blk.w}
            height={blk.h}
            fill="rgba(125,211,252,0.05)"
            stroke={LINE}
            strokeWidth={2.5}
          />
          <Ticks x={blk.x} y={blk.y} w={blk.w} h={blk.h} />
          <path
            d={`M ${blk.x} ${blk.y + Math.round(height * 0.055)} H ${blk.x + blk.w}`}
            stroke={FAINT}
            strokeWidth={2}
          />
          {/* Dimension: the whole assembly is locked as one */}
          <g stroke={LINE} strokeWidth={2} fill="none" opacity={0.8}>
            <path d={`M ${blk.x + blk.w + 34} ${blk.y} V ${blk.y + blk.h}`} />
            <path d={`M ${blk.x + blk.w + 24} ${blk.y} H ${blk.x + blk.w + 44}`} />
            <path
              d={`M ${blk.x + blk.w + 24} ${blk.y + blk.h} H ${blk.x + blk.w + 44}`}
            />
          </g>
        </g>

        {/* Detail callout leader */}
        {cutaway.proof ? (
          <path
            d={`M ${blk.x} ${blk.y + blk.h} L ${width * 0.42} ${height * 0.83} H ${width * 0.365}`}
            stroke={FAINT}
            strokeWidth={2}
            strokeDasharray="10 8"
            fill="none"
            opacity={sp(b.arrivalOf(b.feeds[b.feeds.length - 1]) + 0.2)}
          />
        ) : null}
      </svg>

      {/* Node annotations */}
      {b.feeds.map((f, i) => {
        const s = sp(Math.max(0.15, f.atSec - 0.5), 15, 140);
        if (s <= 0) return null;
        return (
          <div
            key={`ann-${f.label}`}
            style={{
              position: "absolute",
              left: nodeX - 46,
              top: nodeY(i) - Math.round(height * 0.105),
              width: 320,
              opacity: s,
            }}
          >
            <div style={{ ...mono(0.017), color: DIM, display: "flex", gap: 10 }}>
              {f.icon ? (
                <Glyph name={f.icon} size={22} color={DIM} strokeWidth={2} />
              ) : null}
              {f.label.toUpperCase()}
            </div>
            <div
              style={{
                ...mono(0.026),
                color: (f.amount ?? 0) < 0 ? INK : ACCENT,
                fontWeight: 700,
                marginTop: 4,
                whiteSpace: "nowrap",
              }}
            >
              {signed(f.amount)}
            </div>
          </div>
        );
      })}

      {/* Assembly title */}
      <div
        style={{
          position: "absolute",
          left: blk.x + 22,
          top: blk.y + Math.round(height * 0.016),
          ...mono(0.023),
          fontWeight: 700,
          color: INK,
          opacity: sp(b.openSec, 18, 120),
        }}
      >
        {(cutaway.title || "Buku kas").toUpperCase()}
      </div>

      {/* Plotted entries */}
      {b.feeds.map((f, i) => {
        const s = sp(b.arrivalOf(f), 14, 160);
        if (s <= 0) return null;
        return (
          <div
            key={`row-${f.label}`}
            style={{
              position: "absolute",
              left: blk.x + 22,
              top: rowY(i),
              width: blk.w - 44,
              display: "flex",
              alignItems: "flex-end",
              opacity: s,
              transform: `translateX(${interpolate(s, [0, 1], [-18, 0])}px)`,
            }}
          >
            <span style={{ ...mono(0.019), color: DIM }}>
              {String(i + 1).padStart(2, "0")}
            </span>
            <span style={{ ...mono(0.021), color: INK, marginLeft: 16 }}>
              {f.label.toUpperCase()}
            </span>
            <span
              style={{
                flex: 1,
                margin: "0 14px",
                height: 14,
                borderBottom: `2px dashed ${FAINT}`,
              }}
            />
            <span
              style={{
                ...mono(0.021),
                fontWeight: 700,
                color: (f.amount ?? 0) < 0 ? DIM : ACCENT,
                whiteSpace: "nowrap",
              }}
            >
              {signed(f.amount)}
            </span>
          </div>
        );
      })}

      {/* Plotted balance */}
      <div
        style={{
          position: "absolute",
          left: blk.x + 22,
          top: blk.y + blk.h - Math.round(height * 0.115),
          opacity: sp(b.openSec + 0.3),
        }}
      >
        <div style={{ ...mono(0.016), color: DIM, letterSpacing: "0.3em" }}>
          {(cutaway.balanceLabel || "Saldo berjalan").toUpperCase()}
        </div>
        <div
          style={{
            ...mono(0.052),
            fontWeight: 700,
            color: INK,
            marginTop: 6,
            transform: `scale(${1 + interpolate(sp(b.balanceSec, 10, 190), [0, 1], [0, 0.03])})`,
            transformOrigin: "left center",
          }}
        >
          {rupiah(balance)}
        </div>
      </div>

      {/* Lock seal: drafted octagon, not a pill */}
      {b.lockSec != null && lockPop > 0 ? (
        <div
          style={{
            position: "absolute",
            left: blk.x + blk.w - Math.round(width * 0.09),
            top: blk.y - Math.round(height * 0.115),
            width: Math.round(width * 0.115),
            height: Math.round(width * 0.115),
            opacity: lockPop,
            transform: `rotate(${interpolate(lockPop, [0, 1], [-16, -6])}deg) scale(${interpolate(lockPop, [0, 1], [1.5, 1])})`,
          }}
        >
          <svg width="100%" height="100%" viewBox="0 0 100 100">
            <polygon
              points="30,4 70,4 96,30 96,70 70,96 30,96 4,70 4,30"
              fill="rgba(10,26,37,0.72)"
              stroke={LINE}
              strokeWidth={3}
            />
            <polygon
              points="32,11 68,11 89,32 89,68 68,89 32,89 11,68 11,32"
              fill="none"
              stroke={FAINT}
              strokeWidth={2}
            />
          </svg>
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 6,
            }}
          >
            <Glyph name="lock" size={30} color={ACCENT} strokeWidth={2.2} />
            <div
              style={{
                ...mono(0.017),
                fontWeight: 700,
                color: ACCENT,
                letterSpacing: "0.2em",
              }}
            >
              LOCK
            </div>
            <div style={{ ...mono(0.013), color: DIM }}>REV 04</div>
          </div>
        </div>
      ) : null}

      {/* Seal note, set as a drawing annotation rather than inside the seal */}
      {b.lockSec != null && lockPop > 0 ? (
        <div
          style={{
            position: "absolute",
            left: blk.x + blk.w - Math.round(width * 0.09) - Math.round(width * 0.19),
            top: blk.y - Math.round(height * 0.048),
            width: Math.round(width * 0.18),
            textAlign: "right",
            ...mono(0.017),
            color: ACCENT,
            opacity: lockPop,
          }}
        >
          {(cutaway.lockLabel || "Tidak bisa diedit").toUpperCase()} ——
        </div>
      ) : null}

      {/* Rejected revisions annotated like drawing notes */}
      {b.attemptSec.map((a, i) => {
        const local = t - a;
        if (local < 0 || local > 1.4) return null;
        const label = (cutaway.attemptLabels || ["Edit", "Hapus"])[i] || "Edit";
        const cross = interpolate(local, [0.28, 0.6], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        const box = 132;
        return (
          <div
            key={`${label}-${a}`}
            style={{
              position: "absolute",
              left: blk.x + i * (box + 150),
              top: height * 0.14,
              opacity: interpolate(local, [0, 0.16, 1.1, 1.4], [0, 1, 1, 0]),
            }}
          >
            <div
              style={{
                width: box,
                height: 56,
                border: `2.5px solid ${cross > 0 ? REJECT : LINE}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                ...mono(0.021),
                color: cross > 0 ? REJECT : INK,
                position: "relative",
              }}
            >
              {label.toUpperCase()}
              <svg
                width={box}
                height={56}
                style={{ position: "absolute", left: 0, top: 0 }}
              >
                <path
                  d={`M 0 0 L ${box * cross} ${56 * cross}`}
                  stroke={REJECT}
                  strokeWidth={3}
                />
                <path
                  d={`M ${box} 0 L ${box - box * cross} ${56 * cross}`}
                  stroke={REJECT}
                  strokeWidth={3}
                />
              </svg>
            </div>
            {cross >= 1 ? (
              <div style={{ ...mono(0.015), color: REJECT, marginTop: 8 }}>
                REJECTED
              </div>
            ) : null}
          </div>
        );
      })}

      {/* Detail callout: real screen, held by ticks instead of a frame */}
      {cutaway.proof ? (
        <div
          style={{
            position: "absolute",
            left: Math.round(width * 0.115),
            top: Math.round(height * 0.735),
            width: Math.round(width * 0.235),
            opacity: sp(b.arrivalOf(b.feeds[b.feeds.length - 1]) + 0.25, 16, 150),
          }}
        >
          <div style={{ ...mono(0.016), color: DIM, marginBottom: 10 }}>
            DETAIL A — {(cutaway.proof.caption || "FORM ODOO").toUpperCase()}
          </div>
          <div style={{ position: "relative" }}>
            <Img
              src={assetSrc(cutaway.proof.src)}
              style={{
                display: "block",
                width: "100%",
                height: Math.round(width * 0.235 * 0.44),
                objectFit: "cover",
                objectPosition: "50% 26%",
                filter: "saturate(0.6) contrast(1.05) brightness(0.92)",
              }}
            />
            {/* Accent wash so the screenshot reads as part of the drawing */}
            <div
              style={{
                position: "absolute",
                inset: 0,
                background: ACCENT,
                opacity: 0.26,
                mixBlendMode: "multiply",
              }}
            />
            <svg
              width="100%"
              height="100%"
              style={{ position: "absolute", inset: 0 }}
            >
              <Ticks
                x={2}
                y={2}
                w={Math.round(width * 0.235) - 4}
                h={Math.round(width * 0.235 * 0.44) - 4}
                len={20}
              />
            </svg>
          </div>
        </div>
      ) : null}

      {/* Validated: approval note in the drawing's stamp area */}
      {b.stampSec != null && t >= b.stampSec ? (
        <div
          style={{
            position: "absolute",
            right: Math.round(width * 0.045),
            bottom: Math.round(height * 0.085),
            padding: "14px 22px",
            border: `2.5px solid ${LINE}`,
            ...mono(0.024),
            fontWeight: 700,
            color: ACCENT,
            opacity: sp(b.stampSec, 12, 200),
            transform: `rotate(-4deg) scale(${interpolate(sp(b.stampSec, 12, 200), [0, 1], [1.35, 1])})`,
          }}
        >
          {(cutaway.stampLabel || "Tervalidasi").toUpperCase()}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
