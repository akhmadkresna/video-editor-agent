import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { CutawayFeed, TimelineCutaway } from "../../types";

const DISPLAY = 'Syne, "Segoe UI", "Helvetica Neue", Arial, sans-serif';
const UI = '"Instrument Sans", "Segoe UI", system-ui, sans-serif';

const ACCENT = "#7dd3fc";
const INK = "#ffffff";
const DIM = "rgba(255,255,255,0.55)";
const CARD = "rgba(255,255,255,0.05)";
const REJECT = "#f87171";

type Pt = { x: number; y: number };

/** Cubic bezier point — token rides the same curve the connector draws. */
function cubicAt(p0: Pt, p1: Pt, p2: Pt, p3: Pt, t: number): Pt {
  const u = 1 - t;
  const a = u * u * u;
  const b = 3 * u * u * t;
  const c = 3 * u * t * t;
  const d = t * t * t;
  return {
    x: a * p0.x + b * p1.x + c * p2.x + d * p3.x,
    y: a * p0.y + b * p1.y + c * p2.y + d * p3.y,
  };
}

function groupDigits(n: number): string {
  const s = Math.round(Math.abs(n)).toString();
  let out = "";
  for (let i = 0; i < s.length; i++) {
    if (i > 0 && (s.length - i) % 3 === 0) out += ".";
    out += s[i];
  }
  return out;
}

const rupiah = (n: number) => `Rp ${groupDigits(n)}`;
const signed = (n: number) => `${n < 0 ? "−" : "+"} Rp ${groupDigits(n)}`;

const DEFAULT_FEEDS: CutawayFeed[] = [
  { label: "Penjualan", amount: 4850000, atSec: 6.5 },
  { label: "Pembelian", amount: -2300000, atSec: 7.7 },
  { label: "Biaya operasional", amount: -250000, atSec: 8.7 },
];

/**
 * Feeds fly into an immutable cash ledger: connectors draw, value tokens ride
 * them, rows insert, the running balance re-counts, then a lock rejects edits.
 * Every beat is a local-second cue so it lands on the spoken word.
 */
export const LedgerFlow: React.FC<{ cutaway: TimelineCutaway }> = ({
  cutaway,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;

  const feeds = cutaway.feeds?.length ? cutaway.feeds : DEFAULT_FEEDS;
  const cues = cutaway.cues || {};
  const ledgerIn = cues.ledgerInSec ?? 0.15;
  const inOut = cues.inOutSec ?? 4.1;
  const balanceCue = cues.balanceSec ?? 10.1;
  const lockCue = cues.lockSec;
  const attempts = cues.attemptSec || [];
  const stampCue = cues.stampSec;
  const opening = cutaway.openingBalance ?? 1200000;

  const sp = (cueSec: number, damping = 16, stiffness = 130) =>
    spring({
      frame: frame - Math.round(cueSec * fps),
      fps,
      config: { damping, stiffness },
      durationInFrames: Math.round(fps * 0.9),
    });

  // Ledger card geometry
  const cardX = width * 0.5;
  const cardY = height * 0.15;
  const cardW = width * 0.42;
  const cardH = height * 0.72;
  const rowTop = cardY + 190;
  const rowGap = 92;

  const chipX = width * 0.06;
  const chipW = width * 0.2;
  const chipH = 108;
  const chipTop = height * 0.28;
  const chipGap = 156;

  // Running balance recount: value lerps toward each arrival total.
  const arrivalOf = (f: CutawayFeed) => f.atSec + 0.6;
  let prevTotal = opening;
  let targetTotal = opening;
  let lastArrival = ledgerIn;
  feeds.forEach((f) => {
    if (t >= arrivalOf(f)) {
      prevTotal = targetTotal;
      targetTotal = targetTotal + f.amount;
      lastArrival = arrivalOf(f);
    }
  });
  const countProgress = interpolate(
    t,
    [lastArrival, lastArrival + 0.45],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const balanceNow = prevTotal + (targetTotal - prevTotal) * countProgress;

  const locked = lockCue != null && t >= lockCue;
  const lockPop = lockCue != null ? sp(lockCue, 11, 170) : 0;
  // Rejected edits shove the card; it snaps back.
  const shake = attempts.reduce((acc, a) => {
    const local = (t - a) * fps;
    if (local < 0 || local > 14) return acc;
    return acc + Math.sin(local * 1.5) * interpolate(local, [0, 14], [10, 0]);
  }, 0);

  const cardScale = interpolate(sp(ledgerIn), [0, 1], [0.94, 1]);
  const cardOpacity = interpolate(sp(ledgerIn), [0, 1], [0, 1]);

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(ellipse 80% 70% at 42% 40%, #16273a 0%, #0d1a26 62%, #08111a 100%)",
        overflow: "hidden",
      }}
    >
      {/* Grid breathing under everything — keeps the plate alive, never loud. */}
      <AbsoluteFill
        style={{
          opacity: 0.16,
          backgroundImage: `linear-gradient(${ACCENT} 1px, transparent 1px), linear-gradient(90deg, ${ACCENT} 1px, transparent 1px)`,
          backgroundSize: "96px 96px",
          transform: `translateY(${Math.sin(t * 0.5) * 8}px)`,
          maskImage:
            "radial-gradient(ellipse 70% 60% at 45% 45%, #000 20%, transparent 75%)",
        }}
      />

      {/* Header */}
      <div style={{ position: "absolute", left: chipX, top: height * 0.1 }}>
        <div
          style={{
            fontFamily: UI,
            fontSize: Math.round(height * 0.024),
            letterSpacing: "0.22em",
            textTransform: "uppercase",
            color: ACCENT,
            opacity: interpolate(sp(0.05), [0, 1], [0, 1]),
          }}
        >
          {cutaway.kicker || "Buku kas"}
        </div>
        <div
          style={{
            fontFamily: DISPLAY,
            fontWeight: 800,
            fontSize: Math.round(height * 0.062),
            lineHeight: 1,
            letterSpacing: "-0.03em",
            color: INK,
            marginTop: 10,
            opacity: interpolate(sp(0.12), [0, 1], [0, 1]),
            transform: `translateY(${interpolate(sp(0.12), [0, 1], [16, 0])}px)`,
          }}
        >
          {cutaway.title || "Tercatat otomatis"}
        </div>
      </div>

      {/* IN / OUT direction pills */}
      {[cutaway.inLabel || "Masuk", cutaway.outLabel || "Keluar"].map(
        (label, i) => {
          const s = sp(inOut + i * 0.35, 13, 150);
          const pulse = 1 + Math.sin((t - inOut) * 4 + i) * 0.02;
          return (
            <div
              key={label}
              style={{
                position: "absolute",
                left: chipX + i * 190,
                top: height * 0.21,
                padding: "10px 22px",
                borderRadius: 999,
                border: `2px solid ${i === 0 ? ACCENT : "rgba(255,255,255,0.3)"}`,
                color: i === 0 ? ACCENT : DIM,
                fontFamily: UI,
                fontWeight: 600,
                fontSize: Math.round(height * 0.024),
                opacity: s,
                transform: `scale(${interpolate(s, [0, 1], [0.7, pulse])})`,
              }}
            >
              {i === 0 ? "↑" : "↓"} {label}
            </div>
          );
        },
      )}

      {/* Connectors + travelling value tokens */}
      <svg
        width={width}
        height={height}
        style={{ position: "absolute", left: 0, top: 0 }}
      >
        <defs>
          <linearGradient id="wire" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor={ACCENT} stopOpacity="0.15" />
            <stop offset="100%" stopColor={ACCENT} stopOpacity="0.9" />
          </linearGradient>
        </defs>
        {feeds.map((f, i) => {
          const from: Pt = {
            x: chipX + chipW,
            y: chipTop + i * chipGap + chipH / 2,
          };
          const to: Pt = { x: cardX, y: rowTop + i * rowGap + 26 };
          const c1: Pt = { x: from.x + 190, y: from.y };
          const c2: Pt = { x: to.x - 190, y: to.y };
          const draw = interpolate(t, [f.atSec, f.atSec + 0.42], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          if (draw <= 0) return null;
          const d = `M ${from.x} ${from.y} C ${c1.x} ${c1.y}, ${c2.x} ${c2.y}, ${to.x} ${to.y}`;
          const len = 900;
          const travel = interpolate(
            t,
            [f.atSec + 0.14, f.atSec + 0.62],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
          );
          const tok = cubicAt(from, c1, c2, to, travel);
          const tokenAlive = travel > 0 && travel < 1;
          return (
            <g key={f.label}>
              <path
                d={d}
                fill="none"
                stroke="url(#wire)"
                strokeWidth={3}
                strokeDasharray={len}
                strokeDashoffset={len * (1 - draw)}
                opacity={locked ? 0.35 : 0.85}
              />
              {tokenAlive ? (
                <>
                  <circle cx={tok.x} cy={tok.y} r={26} fill={ACCENT} opacity={0.18} />
                  <circle cx={tok.x} cy={tok.y} r={11} fill={ACCENT} />
                </>
              ) : null}
            </g>
          );
        })}
      </svg>

      {/* Source chips */}
      {feeds.map((f, i) => {
        const s = sp(Math.max(0.2, f.atSec - 0.45), 15, 140);
        const consumed = t >= arrivalOf(f);
        return (
          <div
            key={f.label}
            style={{
              position: "absolute",
              left: chipX,
              top: chipTop + i * chipGap,
              width: chipW,
              height: chipH,
              borderRadius: 20,
              border: `2px solid ${consumed ? "rgba(125,211,252,0.35)" : ACCENT}`,
              background: consumed ? "rgba(125,211,252,0.06)" : CARD,
              padding: "18px 24px",
              boxSizing: "border-box",
              opacity: interpolate(s, [0, 1], [0, consumed ? 0.72 : 1]),
              transform: `translateX(${interpolate(s, [0, 1], [-40, 0])}px)`,
            }}
          >
            <div
              style={{
                fontFamily: UI,
                fontSize: Math.round(height * 0.022),
                color: DIM,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
              }}
            >
              {f.label}
            </div>
            <div
              style={{
                fontFamily: DISPLAY,
                fontWeight: 800,
                fontSize: Math.round(height * 0.036),
                color: f.amount < 0 ? INK : ACCENT,
                marginTop: 6,
              }}
            >
              {signed(f.amount)}
            </div>
          </div>
        );
      })}

      {/* Ledger card */}
      <div
        style={{
          position: "absolute",
          left: cardX,
          top: cardY,
          width: cardW,
          height: cardH,
          borderRadius: 28,
          border: `2px solid ${locked ? ACCENT : "rgba(255,255,255,0.16)"}`,
          background:
            "linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02))",
          boxShadow: locked
            ? `0 0 0 6px rgba(125,211,252,0.12), 0 40px 80px rgba(0,0,0,0.45)`
            : "0 40px 80px rgba(0,0,0,0.45)",
          opacity: cardOpacity,
          transform: `translateX(${shake}px) scale(${cardScale})`,
          overflow: "hidden",
        }}
      >
        <div style={{ padding: "34px 40px" }}>
          <div
            style={{
              fontFamily: UI,
              fontSize: Math.round(height * 0.021),
              letterSpacing: "0.24em",
              textTransform: "uppercase",
              color: DIM,
            }}
          >
            Kas ledger
          </div>
          <div
            style={{
              fontFamily: DISPLAY,
              fontWeight: 800,
              fontSize: Math.round(height * 0.05),
              color: INK,
              letterSpacing: "-0.02em",
            }}
          >
            BUKU KAS
          </div>
        </div>

        {/* Rows insert as each token lands */}
        {feeds.map((f, i) => {
          const s = sp(arrivalOf(f), 14, 160);
          if (s <= 0) return null;
          return (
            <div
              key={f.label}
              style={{
                position: "absolute",
                left: 40,
                top: rowTop - cardY + i * rowGap,
                width: cardW - 80,
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "16px 22px",
                boxSizing: "border-box",
                borderRadius: 16,
                background: "rgba(255,255,255,0.06)",
                borderLeft: `4px solid ${f.amount < 0 ? "rgba(255,255,255,0.4)" : ACCENT}`,
                opacity: s,
                transform: `translateY(${interpolate(s, [0, 1], [26, 0])}px)`,
              }}
            >
              <span
                style={{
                  fontFamily: UI,
                  fontSize: Math.round(height * 0.024),
                  color: INK,
                }}
              >
                {f.label}
              </span>
              <span
                style={{
                  fontFamily: DISPLAY,
                  fontWeight: 800,
                  fontSize: Math.round(height * 0.028),
                  color: f.amount < 0 ? DIM : ACCENT,
                }}
              >
                {signed(f.amount)}
              </span>
            </div>
          );
        })}

        {/* Running balance */}
        <div
          style={{
            position: "absolute",
            left: 40,
            bottom: 36,
            width: cardW - 80,
          }}
        >
          <div
            style={{
              height: 1,
              background: "rgba(255,255,255,0.16)",
              marginBottom: 20,
            }}
          />
          <div
            style={{
              fontFamily: UI,
              fontSize: Math.round(height * 0.021),
              letterSpacing: "0.2em",
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
              fontSize: Math.round(height * 0.072),
              color: ACCENT,
              letterSpacing: "-0.03em",
              transform: `scale(${1 + interpolate(sp(balanceCue, 10, 180), [0, 1], [0, 0.04])})`,
              transformOrigin: "left center",
            }}
          >
            {rupiah(balanceNow)}
          </div>
        </div>

        {/* Lock badge */}
        {lockCue != null && lockPop > 0 ? (
          <div
            style={{
              position: "absolute",
              right: 34,
              top: 34,
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "12px 20px",
              borderRadius: 999,
              border: `2px solid ${ACCENT}`,
              background: "rgba(125,211,252,0.12)",
              opacity: lockPop,
              transform: `scale(${interpolate(lockPop, [0, 1], [1.6, 1])}) rotate(${interpolate(lockPop, [0, 1], [-12, 0])}deg)`,
            }}
          >
            <span style={{ fontSize: Math.round(height * 0.03) }}>🔒</span>
            <span
              style={{
                fontFamily: UI,
                fontWeight: 600,
                fontSize: Math.round(height * 0.022),
                color: ACCENT,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
              }}
            >
              {cutaway.lockLabel || "Tidak bisa diedit"}
            </span>
          </div>
        ) : null}
      </div>

      {/* Rejected edit attempts bounce off the locked card */}
      {attempts.map((a, i) => {
        const local = t - a;
        if (local < 0 || local > 1.3) return null;
        const push = interpolate(local, [0, 0.32, 1.3], [0, 1, 0.86], {
          extrapolateRight: "clamp",
        });
        const hit = local >= 0.32;
        const label = (cutaway.attemptLabels || ["Edit", "Hapus"])[i] || "Edit";
        const startX = width - 210;
        const endX = cardX + cardW - 230;
        return (
          <div
            key={`${label}-${a}`}
            style={{
              position: "absolute",
              left: startX + (endX - startX) * push,
              top: cardY + 96 + i * 96,
              padding: "14px 26px",
              borderRadius: 14,
              border: `2px solid ${hit ? REJECT : "rgba(255,255,255,0.4)"}`,
              color: hit ? REJECT : INK,
              background: "rgba(8,17,26,0.75)",
              fontFamily: UI,
              fontWeight: 600,
              fontSize: Math.round(height * 0.026),
              textDecoration: hit ? "line-through" : "none",
              opacity: interpolate(local, [0, 0.15, 0.9, 1.3], [0, 1, 1, 0]),
              transform: `rotate(${hit ? interpolate(local, [0.32, 1.3], [0, 8]) : 0}deg)`,
            }}
          >
            {label}
          </div>
        );
      })}

      {/* Validated stamp */}
      {stampCue != null && t >= stampCue ? (
        <div
          style={{
            position: "absolute",
            left: chipX,
            bottom: height * 0.12,
            padding: "18px 34px",
            border: `4px solid ${ACCENT}`,
            borderRadius: 12,
            color: ACCENT,
            fontFamily: DISPLAY,
            fontWeight: 800,
            fontSize: Math.round(height * 0.042),
            letterSpacing: "0.1em",
            opacity: sp(stampCue, 12, 200),
            transform: `rotate(-6deg) scale(${interpolate(sp(stampCue, 12, 200), [0, 1], [1.5, 1])})`,
          }}
        >
          {cutaway.stampLabel || "TERVALIDASI"}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
