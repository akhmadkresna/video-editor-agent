import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { CutawayFeed, CutawayLook, TimelineCutaway } from "../../types";

const DISPLAY = 'Syne, "Segoe UI", "Helvetica Neue", Arial, sans-serif';
const UI = '"Instrument Sans", "Segoe UI", system-ui, sans-serif';

/** Locked cool-mist sky accent, plus the darker ramp step for light surfaces. */
const ACCENT = "#7dd3fc";
const ACCENT_DEEP = "#0ea5e9";
const REJECT = "#e11d48";

type Look = {
  background: string;
  /** Breathing grid — off for flat treatments. */
  grid: boolean;
  ink: string;
  dim: string;
  /** Wire + token color. */
  wire: string;
  /** Solid fill for pills/markers, with matching text color. */
  fill: string;
  onFill: string;
  /** Positive/negative amount colors. */
  plus: string;
  minus: string;
  card: string;
  cardBorder: string;
  cardShadow: string;
  row: string;
  divider: string;
  radius: number;
  /** Cards vs bare rules (editorial). */
  chrome: boolean;
  reject: string;
};

const LOOKS: Record<CutawayLook, Look> = {
  glass: {
    background:
      "radial-gradient(ellipse 80% 70% at 42% 40%, #16273a 0%, #0d1a26 62%, #08111a 100%)",
    grid: true,
    ink: "#ffffff",
    dim: "rgba(255,255,255,0.55)",
    wire: ACCENT,
    fill: "rgba(125,211,252,0.12)",
    onFill: ACCENT,
    plus: ACCENT,
    minus: "rgba(255,255,255,0.55)",
    card: "linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02))",
    cardBorder: "rgba(255,255,255,0.16)",
    cardShadow: "0 40px 80px rgba(0,0,0,0.45)",
    row: "rgba(255,255,255,0.06)",
    divider: "rgba(255,255,255,0.16)",
    radius: 28,
    chrome: true,
    reject: "#f87171",
  },
  flat_light: {
    background: "#d9e2ec",
    grid: false,
    ink: "#0c1c2a",
    dim: "rgba(12,28,42,0.55)",
    wire: ACCENT_DEEP,
    fill: ACCENT,
    onFill: "#0c1c2a",
    plus: ACCENT_DEEP,
    minus: "#0c1c2a",
    card: "#ffffff",
    cardBorder: "transparent",
    cardShadow: "none",
    row: "#eef3f8",
    divider: "#c4d0dc",
    radius: 12,
    chrome: true,
    reject: REJECT,
  },
  flat_dark: {
    background: "#0e1b26",
    grid: false,
    ink: "#ffffff",
    dim: "rgba(255,255,255,0.55)",
    wire: ACCENT,
    fill: ACCENT,
    onFill: "#08131c",
    plus: ACCENT,
    minus: "rgba(255,255,255,0.7)",
    card: "#16242f",
    cardBorder: "transparent",
    cardShadow: "none",
    row: "#1e2d39",
    divider: "rgba(255,255,255,0.14)",
    radius: 12,
    chrome: true,
    reject: "#fb7185",
  },
  flat_editorial: {
    background: "#e8eef4",
    grid: false,
    ink: "#0b1a27",
    dim: "rgba(11,26,39,0.5)",
    wire: ACCENT_DEEP,
    fill: ACCENT,
    onFill: "#0b1a27",
    plus: ACCENT_DEEP,
    minus: "#0b1a27",
    card: "transparent",
    cardBorder: "transparent",
    cardShadow: "none",
    row: "transparent",
    divider: "#adbccb",
    radius: 0,
    chrome: false,
    reject: REJECT,
  },
};

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
  const look = LOOKS[cutaway.look ?? "glass"] ?? LOOKS.glass;

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

  const cardX = width * 0.5;
  const cardY = height * 0.15;
  const cardW = width * 0.42;
  const cardH = height * 0.72;
  const rowTop = cardY + 190;
  const rowGap = 92;

  const chipX = width * 0.06;
  const chipW = width * 0.2;
  const chipH = 108;
  const chipTop = height * 0.305;
  const chipGap = 152;

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
      style={{ background: look.background, overflow: "hidden" }}
    >
      {look.grid ? (
        <AbsoluteFill
          style={{
            opacity: 0.16,
            backgroundImage: `linear-gradient(${look.wire} 1px, transparent 1px), linear-gradient(90deg, ${look.wire} 1px, transparent 1px)`,
            backgroundSize: "96px 96px",
            transform: `translateY(${Math.sin(t * 0.5) * 8}px)`,
            maskImage:
              "radial-gradient(ellipse 70% 60% at 45% 45%, #000 20%, transparent 75%)",
          }}
        />
      ) : null}

      {/* Header */}
      <div style={{ position: "absolute", left: chipX, top: height * 0.1 }}>
        <div
          style={{
            fontFamily: UI,
            fontSize: Math.round(height * 0.024),
            letterSpacing: "0.22em",
            textTransform: "uppercase",
            color: look.chrome ? look.wire : look.dim,
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
            color: look.ink,
            marginTop: 10,
            opacity: interpolate(sp(0.12), [0, 1], [0, 1]),
            transform: `translateY(${interpolate(sp(0.12), [0, 1], [16, 0])}px)`,
          }}
        >
          {cutaway.title || "Tercatat otomatis"}
        </div>
        {!look.chrome ? (
          <div
            style={{
            marginTop: 12,
            width: interpolate(sp(0.2), [0, 1], [0, 260]),
            height: 8,
              background: look.fill,
            }}
          />
        ) : null}
      </div>

      {/* IN / OUT direction pills */}
      {[cutaway.inLabel || "Masuk", cutaway.outLabel || "Keluar"].map(
        (label, i) => {
          const s = sp(inOut + i * 0.35, 13, 150);
          const pulse = 1 + Math.sin((t - inOut) * 4 + i) * 0.02;
          const active = i === 0;
          return (
            <div
              key={label}
              style={{
                position: "absolute",
                left: chipX + i * 190,
                top: height * 0.235,
                padding: "10px 22px",
                borderRadius: look.radius === 0 ? 0 : 999,
                background: active ? look.fill : "transparent",
                border: active
                  ? `2px solid ${look.fill}`
                  : `2px solid ${look.divider}`,
                color: active ? look.onFill : look.dim,
                fontFamily: UI,
                fontWeight: 600,
                fontSize: Math.round(height * 0.024),
                opacity: s,
                transform: `scale(${interpolate(s, [0, 1], [0.7, pulse])})`,
              }}
            >
              {active ? "↑" : "↓"} {label}
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
                stroke={look.wire}
                strokeWidth={3}
                strokeDasharray={len}
                strokeDashoffset={len * (1 - draw)}
                opacity={locked ? 0.3 : 0.75}
              />
              {tokenAlive ? (
                <circle cx={tok.x} cy={tok.y} r={12} fill={look.wire} />
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
              borderRadius: look.radius === 0 ? 0 : 16,
              borderBottom: look.chrome ? "none" : `1px solid ${look.divider}`,
              borderLeft: `${look.chrome ? 8 : 10}px solid ${
                f.amount < 0 ? look.divider : look.fill
              }`,
              background: look.chrome ? look.card : "transparent",
              padding: "18px 24px",
              boxSizing: "border-box",
              opacity: interpolate(s, [0, 1], [0, consumed ? 0.62 : 1]),
              transform: `translateX(${interpolate(s, [0, 1], [-40, 0])}px)`,
            }}
          >
            <div
              style={{
                fontFamily: UI,
                fontSize: Math.round(height * 0.022),
                color: look.dim,
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
                color: f.amount < 0 ? look.minus : look.plus,
                marginTop: 6,
              }}
            >
              {signed(f.amount)}
            </div>
          </div>
        );
      })}

      {/* Ledger */}
      <div
        style={{
          position: "absolute",
          left: cardX,
          top: cardY,
          width: cardW,
          height: cardH,
          borderRadius: look.radius,
          background: look.card,
          border: locked && look.chrome ? `3px solid ${look.fill}` : "none",
          borderTop: look.chrome ? undefined : `6px solid ${look.ink}`,
          boxShadow: look.cardShadow,
          opacity: cardOpacity,
          transform: `translateX(${shake}px) scale(${cardScale})`,
          overflow: "hidden",
          boxSizing: "border-box",
        }}
      >
        <div style={{ padding: look.chrome ? "34px 40px" : "28px 0 0 32px" }}>
          <div
            style={{
              fontFamily: UI,
              fontSize: Math.round(height * 0.021),
              letterSpacing: "0.24em",
              textTransform: "uppercase",
              color: look.dim,
            }}
          >
            Kas ledger
          </div>
          <div
            style={{
              fontFamily: DISPLAY,
              fontWeight: 800,
              fontSize: Math.round(height * 0.05),
              color: look.ink,
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
          const inset = look.chrome ? 40 : 32;
          return (
            <div
              key={f.label}
              style={{
                position: "absolute",
                left: inset,
                top: rowTop - cardY + i * rowGap,
                width: cardW - inset * 2,
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: look.chrome ? "16px 22px" : "14px 0",
                boxSizing: "border-box",
                borderRadius: look.radius === 0 ? 0 : 10,
                background: look.row,
                borderLeft: look.chrome
                  ? `6px solid ${f.amount < 0 ? look.divider : look.fill}`
                  : "none",
                borderBottom: look.chrome ? "none" : `1px solid ${look.divider}`,
                opacity: s,
                transform: `translateY(${interpolate(s, [0, 1], [26, 0])}px)`,
              }}
            >
              <span
                style={{
                  fontFamily: UI,
                  fontSize: Math.round(height * 0.024),
                  color: look.ink,
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                }}
              >
                {look.chrome ? null : (
                  <span
                    style={{
                      width: 14,
                      height: 14,
                      background: f.amount < 0 ? look.divider : look.fill,
                      display: "inline-block",
                    }}
                  />
                )}
                {f.label}
              </span>
              <span
                style={{
                  fontFamily: DISPLAY,
                  fontWeight: 800,
                  fontSize: Math.round(height * 0.028),
                  color: f.amount < 0 ? look.minus : look.plus,
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
            left: look.chrome ? 40 : 32,
            bottom: 36,
            width: cardW - (look.chrome ? 80 : 64),
          }}
        >
          <div
            style={{
              height: look.chrome ? 1 : 3,
              background: look.chrome ? look.divider : look.ink,
              marginBottom: 20,
            }}
          />
          <div
            style={{
              fontFamily: UI,
              fontSize: Math.round(height * 0.021),
              letterSpacing: "0.2em",
              textTransform: "uppercase",
              color: look.dim,
            }}
          >
            {cutaway.balanceLabel || "Saldo berjalan"}
          </div>
          <div
            style={{
              display: "inline-block",
              fontFamily: DISPLAY,
              fontWeight: 800,
              fontSize: Math.round(height * 0.072),
              color: look.chrome ? look.plus : look.ink,
              letterSpacing: "-0.03em",
              borderBottom: look.chrome ? "none" : `10px solid ${look.fill}`,
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
              right: look.chrome ? 34 : 32,
              top: 34,
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "12px 20px",
              borderRadius: look.radius === 0 ? 0 : 999,
              border: `2px solid ${look.fill}`,
              background: look.fill,
              opacity: lockPop,
              transform: `scale(${interpolate(lockPop, [0, 1], [1.6, 1])}) rotate(${interpolate(lockPop, [0, 1], [-12, 0])}deg)`,
            }}
          >
            <span
              style={{
                fontFamily: UI,
                fontWeight: 700,
                fontSize: Math.round(height * 0.022),
                color: look.onFill,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
              }}
            >
              {cutaway.lockLabel || "Tidak bisa diedit"}
            </span>
          </div>
        ) : null}
      </div>

      {/* Rejected edit attempts bounce off the locked ledger */}
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
              borderRadius: look.radius === 0 ? 0 : 10,
              border: `2px solid ${hit ? look.reject : look.divider}`,
              color: hit ? look.reject : look.ink,
              background: look.chrome ? look.card : look.background,
              fontFamily: UI,
              fontWeight: 700,
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
            border: `4px solid ${look.chrome ? look.wire : look.ink}`,
            background: look.chrome ? "transparent" : look.fill,
            borderRadius: look.radius === 0 ? 0 : 10,
            color: look.chrome ? look.wire : look.onFill,
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
