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
  cubicAt,
  cueSpring,
  DISPLAY,
  rupiah,
  runningBalance,
  sceneBeats,
  signed,
  UI,
} from "./shared";

const PLATE = "#0a1420";
const INK = "#ffffff";
const DIM = "rgba(255,255,255,0.5)";

/**
 * Type is the whole design: figures arrive at full size, ribbons carry them
 * into a stacked mass, and the total swallows the frame. No panels, no rows —
 * scale and motion do the explaining.
 */
export const KineticFigures: React.FC<{ cutaway: TimelineCutaway }> = ({
  cutaway,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;
  const b = sceneBeats(cutaway);
  const sp = (cue: number, damping = 16, stiffness = 130) =>
    cueSpring(frame, fps, cue, damping, stiffness);

  const balance = runningBalance(t, b.feeds, b.opening, b.arrivalOf, b.openSec);
  const lockPop = b.lockSec != null ? sp(b.lockSec, 12, 170) : 0;

  const rowX = Math.round(width * 0.07);
  const rowY = (i: number) => Math.round(height * 0.34 + i * height * 0.17);
  const ribbonStart = Math.round(width * 0.46);
  // Every figure is carried into the same place: the rule under the total,
  // so the ribbons visibly become the number.
  const sink = {
    x: Math.round(width * 0.78),
    y: Math.round(height * 0.94),
  };
  const arrived = b.feeds.filter((f) => t >= b.arrivalOf(f)).length;

  return (
    <AbsoluteFill style={{ background: PLATE, overflow: "hidden" }}>
      <Backdrop cutaway={cutaway} plate={PLATE} defaultDim={0.68} />

      {/* Proof asset as a duotone bleed off the corner — not a framed card */}
      {cutaway.proof ? (
        <div
          style={{
            position: "absolute",
            right: -Math.round(width * 0.03),
            top: -Math.round(height * 0.06),
            width: Math.round(width * 0.34),
            height: Math.round(height * 0.34),
            opacity: interpolate(
              sp(b.arrivalOf(b.feeds[b.feeds.length - 1]) + 0.2, 18, 150),
              [0, 1],
              [0, 0.94],
            ),
            overflow: "hidden",
          }}
        >
          <Img
            src={assetSrc(cutaway.proof.src)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              objectPosition: "50% 24%",
              filter: "grayscale(0.4) contrast(1.05) brightness(0.92)",
            }}
          />
        </div>
      ) : null}
      {cutaway.proof?.caption ? (
        <div
          style={{
            position: "absolute",
            right: Math.round(width * 0.03),
            top: Math.round(height * 0.29),
            fontFamily: UI,
            fontWeight: 700,
            fontSize: Math.round(height * 0.019),
            letterSpacing: "0.26em",
            textTransform: "uppercase",
            color: PLATE,
            background: ACCENT,
            padding: "8px 16px",
            opacity: sp(b.arrivalOf(b.feeds[b.feeds.length - 1]) + 0.3, 18, 150),
          }}
        >
          {cutaway.proof.caption}
        </div>
      ) : null}

      {/* Kicker + title, set like a magazine opener */}
      <div
        style={{
          position: "absolute",
          left: rowX,
          top: height * 0.09,
          fontFamily: UI,
          fontWeight: 700,
          fontSize: Math.round(height * 0.021),
          letterSpacing: "0.34em",
          textTransform: "uppercase",
          color: ACCENT,
          opacity: sp(b.openSec),
        }}
      >
        {cutaway.kicker || "Buku kas"}
      </div>
      <div
        style={{
          position: "absolute",
          left: rowX,
          top: height * 0.125,
          fontFamily: DISPLAY,
          fontWeight: 800,
          fontSize: Math.round(height * 0.088),
          letterSpacing: "-0.04em",
          lineHeight: 1,
          color: INK,
          opacity: sp(b.openSec + 0.08),
          transform: `translateY(${interpolate(sp(b.openSec + 0.08), [0, 1], [26, 0])}px)`,
        }}
      >
        {cutaway.title || "Tercatat otomatis"}
      </div>

      {/* Ribbons: each figure is carried into the total */}
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {b.feeds.map((f, i) => {
          const from = { x: ribbonStart, y: rowY(i) };
          const to = sink;
          const c1 = { x: from.x + 340, y: from.y };
          const c2 = { x: to.x + 70, y: to.y - 380 };
          const draw = interpolate(t, [f.atSec, f.atSec + 0.5], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          if (draw <= 0) return null;
          const head = cubicAt(from, c1, c2, to, draw);
          const len = 1100;
          return (
            <g key={f.label}>
              <path
                d={`M ${from.x} ${from.y} C ${c1.x} ${c1.y}, ${c2.x} ${c2.y}, ${to.x} ${to.y}`}
                fill="none"
                stroke={(f.amount ?? 0) < 0 ? "rgba(255,255,255,0.28)" : ACCENT}
                strokeWidth={(f.amount ?? 0) < 0 ? 14 : 26}
                strokeLinecap="butt"
                strokeDasharray={len}
                strokeDashoffset={len * (1 - draw)}
                opacity={draw >= 1 ? 0.28 : 0.72}
              />
              {draw < 1 ? (
                <circle cx={head.x} cy={head.y} r={18} fill={ACCENT} />
              ) : null}
            </g>
          );
        })}
      </svg>

      {/* The figures themselves */}
      {b.feeds.map((f, i) => {
        const s = sp(f.atSec - 0.35, 15, 140);
        if (s <= 0) return null;
        const spent = interpolate(
          t,
          [b.arrivalOf(f), b.arrivalOf(f) + 0.8],
          [1, 0.34],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
        );
        return (
          <div
            key={f.label}
            style={{
              position: "absolute",
              left: rowX,
              top: rowY(i) - height * 0.075,
              opacity: s * spent,
              transform: `translateX(${interpolate(s, [0, 1], [-70, 0])}px)`,
            }}
          >
            <div
              style={{
                fontFamily: UI,
                fontWeight: 700,
                fontSize: Math.round(height * 0.019),
                letterSpacing: "0.3em",
                textTransform: "uppercase",
                color: DIM,
              }}
            >
              {f.label}
            </div>
            <div
              style={{
                fontFamily: DISPLAY,
                fontWeight: 800,
                fontSize: Math.round(height * 0.082),
                letterSpacing: "-0.05em",
                lineHeight: 1,
                whiteSpace: "nowrap",
                color: (f.amount ?? 0) < 0 ? DIM : ACCENT,
              }}
            >
              {signed(f.amount)}
            </div>
          </div>
        );
      })}

      {/* Total swallows the lower frame; its rule thickens per arrival */}
      <div
        style={{
          position: "absolute",
          right: Math.round(width * 0.05),
          bottom: Math.round(height * 0.06),
          textAlign: "right",
          opacity: sp(b.openSec + 0.3),
        }}
      >
        <div
          style={{
            fontFamily: UI,
            fontWeight: 700,
            fontSize: Math.round(height * 0.02),
            letterSpacing: "0.32em",
            textTransform: "uppercase",
            color: DIM,
          }}
        >
          {cutaway.balanceLabel || "Saldo berjalan"}
        </div>
        <div
          style={{
            fontFamily: DISPLAY,
            fontWeight: 800,
            fontSize: Math.round(height * 0.14),
            letterSpacing: "-0.055em",
            lineHeight: 0.95,
            color: INK,
            transform: `scale(${1 + interpolate(sp(b.balanceSec, 10, 190), [0, 1], [0, 0.035])})`,
            transformOrigin: "right center",
          }}
        >
          {rupiah(balance)}
        </div>
        <div
          style={{
            marginTop: 14,
            marginLeft: "auto",
            width: interpolate(arrived, [0, b.feeds.length], [0, width * 0.42], {
              extrapolateRight: "clamp",
            }),
            height: Math.round(height * 0.014),
            background: ACCENT,
          }}
        />
      </div>

      {/* Lock reads as outlined type, not a badge */}
      {b.lockSec != null && lockPop > 0 ? (
        <div
          style={{
            position: "absolute",
            left: rowX,
            bottom: Math.round(height * 0.08),
            fontFamily: DISPLAY,
            fontWeight: 800,
            fontSize: Math.round(height * 0.062),
            letterSpacing: "-0.02em",
            color: "transparent",
            WebkitTextStroke: `3px ${ACCENT}`,
            opacity: lockPop * 0.85,
            transform: `scale(${interpolate(lockPop, [0, 1], [1.25, 1])})`,
            transformOrigin: "left bottom",
          }}
        >
          {(cutaway.lockLabel || "Tidak bisa diedit").toUpperCase()}
        </div>
      ) : null}

      {/* Attempts get scored out by a bar, in place */}
      {b.attemptSec.map((a, i) => {
        const local = t - a;
        if (local < 0 || local > 1.4) return null;
        const label = (cutaway.attemptLabels || ["Edit", "Hapus"])[i] || "Edit";
        const enter = interpolate(local, [0, 0.28], [0, 1], {
          extrapolateRight: "clamp",
        });
        const score = interpolate(local, [0.3, 0.55], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        return (
          <div
            key={`${label}-${a}`}
            style={{
              position: "absolute",
              left: ribbonStart + 40,
              top: height * (0.2 + i * 0.09),
              fontFamily: DISPLAY,
              fontWeight: 800,
              fontSize: Math.round(height * 0.062),
              letterSpacing: "-0.02em",
              color: INK,
              opacity: interpolate(local, [0, 0.16, 1.1, 1.4], [0, 1, 1, 0]),
              transform: `translateX(${interpolate(enter, [0, 1], [90, 0])}px)`,
            }}
          >
            {label.toUpperCase()}
            <div
              style={{
                position: "absolute",
                left: -10,
                top: "52%",
                width: `${score * 118}%`,
                height: Math.round(height * 0.012),
                background: ACCENT,
              }}
            />
          </div>
        );
      })}

      {/* Validated: a rule slams under the total */}
      {b.stampSec != null && t >= b.stampSec ? (
        <div
          style={{
            position: "absolute",
            left: rowX,
            bottom: Math.round(height * 0.045),
            width: interpolate(sp(b.stampSec, 12, 200), [0, 1], [0, width * 0.3]),
            height: Math.round(height * 0.016),
            background: ACCENT,
          }}
        />
      ) : null}
    </AbsoluteFill>
  );
};
