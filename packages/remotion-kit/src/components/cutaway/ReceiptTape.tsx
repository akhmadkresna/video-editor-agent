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

const PAPER = "#f6f2e8";
const INK = "#1d1d1b";
const INK_SOFT = "rgba(29,29,27,0.55)";
const PLATE = "#0f171f";

/** Dotted leader between a label and its amount, like a printed receipt. */
const Leader: React.FC<{ color?: string }> = ({ color = INK_SOFT }) => (
  <span
    style={{
      flex: 1,
      margin: "0 12px",
      alignSelf: "flex-end",
      height: 18,
      borderBottom: `3px dotted ${color}`,
      opacity: 0.6,
    }}
  />
);

/**
 * The ledger as a thermal receipt: lines print one per VO beat, the total
 * re-prints, and a rubber stamp lands on the paper when it locks. Physical
 * document language — no cards, no rounded panels.
 */
export const ReceiptTape: React.FC<{ cutaway: TimelineCutaway }> = ({
  cutaway,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;
  const b = sceneBeats(cutaway);
  const sp = (cue: number, damping = 16, stiffness = 130) =>
    cueSpring(frame, fps, cue, damping, stiffness);

  const balance = runningBalance(t, b.feeds, b.opening, b.arrivalOf, b.openSec);
  const locked = b.lockSec != null && t >= b.lockSec;
  const lockPop = b.lockSec != null ? sp(b.lockSec, 10, 190) : 0;

  const paperW = Math.round(width * 0.42);
  const paperX = Math.round(width * 0.1);
  const open = sp(b.openSec, 18, 120);
  // Paper feeds down out of frame as the print head runs.
  const feedY = interpolate(open, [0, 1], [-height * 0.5, 8]);
  const jitter = locked ? 0 : Math.sin(t * 26) * 0.6;

  const line = Math.round(height * 0.03);
  const rowGap = 18;

  return (
    <AbsoluteFill style={{ background: PLATE, overflow: "hidden" }}>
      <Backdrop cutaway={cutaway} plate={PLATE} defaultDim={0.62} />

      {/* Print head slit the paper feeds through */}
      <div
        style={{
          position: "absolute",
          left: paperX - 36,
          top: 0,
          width: paperW + 72,
          height: 26,
          background: "rgba(0,0,0,0.55)",
          boxShadow: "0 14px 30px rgba(0,0,0,0.5)",
        }}
      />

      <div
        style={{
          position: "absolute",
          left: paperX,
          top: feedY,
          width: paperW,
          transform: `rotate(-0.9deg) translateY(${jitter}px)`,
          transformOrigin: "50% 0%",
          filter: "drop-shadow(0 34px 46px rgba(0,0,0,0.5))",
        }}
      >
        <div
          style={{
            background: PAPER,
            backgroundImage:
              "repeating-linear-gradient(0deg, rgba(29,29,27,0.035) 0 1px, transparent 1px 4px)",
            padding: "40px 54px 26px",
            fontFamily: MONO,
            color: INK,
          }}
        >
          <div
            style={{
              fontSize: Math.round(height * 0.026),
              letterSpacing: "0.34em",
              fontWeight: 700,
            }}
          >
            {(cutaway.kicker || "Buku kas").toUpperCase()}
          </div>
          <div
            style={{
              fontSize: Math.round(height * 0.019),
              letterSpacing: "0.16em",
              color: INK_SOFT,
              marginTop: 8,
            }}
          >
            {(cutaway.title || "Tercatat otomatis").toUpperCase()}
          </div>

          <div
            style={{
              margin: "26px 0",
              height: 4,
              backgroundImage: `repeating-linear-gradient(90deg, ${INK} 0 14px, transparent 14px 26px)`,
              opacity: 0.7,
            }}
          />

          <div
            style={{
              display: "flex",
              alignItems: "flex-end",
              fontSize: line,
              color: INK_SOFT,
            }}
          >
            <span style={{ letterSpacing: "0.06em" }}>SALDO AWAL</span>
            <Leader />
            <span>{rupiah(b.opening)}</span>
          </div>

          {/* One printed line per feed */}
          {b.feeds.map((f) => {
            const s = sp(b.arrivalOf(f), 22, 200);
            if (s <= 0) return null;
            const ink = interpolate(s, [0, 1], [0.25, 1]);
            const slam = interpolate(s, [0, 1], [10, 0]);
            return (
              <div
                key={f.label}
                style={{
                  display: "flex",
                  alignItems: "flex-end",
                  marginTop: rowGap,
                  fontSize: line,
                  opacity: ink,
                  transform: `translateY(${slam}px)`,
                }}
              >
                {f.icon ? (
                  <span style={{ marginRight: 14, alignSelf: "center" }}>
                    <Glyph name={f.icon} size={26} color={INK} strokeWidth={2.2} />
                  </span>
                ) : null}
                <span style={{ letterSpacing: "0.06em" }}>
                  {f.label.toUpperCase()}
                </span>
                <Leader />
                <span style={{ fontWeight: 700 }}>{signed(f.amount ?? 0)}</span>
              </div>
            );
          })}

          <div
            style={{
              margin: "28px 0 22px",
              height: 4,
              backgroundImage: `repeating-linear-gradient(90deg, ${INK} 0 14px, transparent 14px 26px)`,
              opacity: 0.7,
            }}
          />

          <div
            style={{
              fontSize: Math.round(height * 0.018),
              letterSpacing: "0.3em",
              color: INK_SOFT,
            }}
          >
            {(cutaway.balanceLabel || "Saldo berjalan").toUpperCase()}
          </div>
          <div
            style={{
              fontSize: Math.round(height * 0.062),
              fontWeight: 700,
              letterSpacing: "-0.01em",
              marginTop: 6,
              transform: `scale(${1 + interpolate(sp(b.balanceSec, 10, 180), [0, 1], [0, 0.03])})`,
              transformOrigin: "left center",
            }}
          >
            {rupiah(balance)}
          </div>

          {/* Attachment: the real screen, printed like a fax */}
          {cutaway.proof ? (
            <div
              style={{
                marginTop: 30,
                opacity: sp(b.arrivalOf(b.feeds[b.feeds.length - 1]) + 0.3, 20, 170),
              }}
            >
              <div
                style={{
                  fontSize: Math.round(height * 0.017),
                  letterSpacing: "0.26em",
                  color: INK_SOFT,
                  marginBottom: 10,
                }}
              >
                {(cutaway.proof.caption || "Lampiran").toUpperCase()}
              </div>
              <Img
                src={assetSrc(cutaway.proof.src)}
                style={{
                  display: "block",
                  width: "100%",
                  height: Math.round(paperW * 0.34),
                  objectFit: "cover",
                  objectPosition: "50% 26%",
                  filter: "grayscale(1) contrast(1.5) brightness(1.05)",
                  mixBlendMode: "multiply",
                  opacity: 0.9,
                }}
              />
            </div>
          ) : null}

          <div
            style={{
              marginTop: 24,
              fontSize: Math.round(height * 0.016),
              letterSpacing: "0.22em",
              color: INK_SOFT,
            }}
          >
            NO. JURNAL 000412 · ODOO AUTO-JOURNAL
          </div>
        </div>

        {/* Torn bottom edge */}
        <svg width={paperW} height={26} style={{ display: "block" }}>
          <path
            d={`M0 0 ${Array.from({ length: 26 }, (_, i) =>
              `L ${((i + 0.5) * paperW) / 26} ${i % 2 ? 4 : 22}`,
            ).join(" ")} L ${paperW} 0 Z`}
            fill={PAPER}
          />
        </svg>
      </div>

      {/* Rubber stamp lands across the paper edge */}
      {b.lockSec != null && lockPop > 0 ? (
        <div
          style={{
            position: "absolute",
            left: paperX + paperW * 0.34,
            top: height * 0.6,
            padding: "16px 26px",
            border: `5px solid ${REJECT}`,
            outline: `2px solid ${REJECT}`,
            outlineOffset: 5,
            color: REJECT,
            fontFamily: MONO,
            fontWeight: 700,
            fontSize: Math.round(height * 0.03),
            letterSpacing: "0.14em",
            opacity: lockPop * 0.88,
            mixBlendMode: "multiply",
            transform: `rotate(-11deg) scale(${interpolate(lockPop, [0, 1], [1.7, 1])})`,
          }}
        >
          {(cutaway.lockLabel || "Tidak bisa diedit").toUpperCase()}
        </div>
      ) : null}

      {/* Rejected edits: red ink scrawled over the printed line */}
      {b.attemptSec.map((a, i) => {
        const local = t - a;
        if (local < 0 || local > 1.4) return null;
        const push = interpolate(local, [0, 0.3, 1.4], [0, 1, 0.9], {
          extrapolateRight: "clamp",
        });
        const hit = local >= 0.3;
        const label = (cutaway.attemptLabels || ["Edit", "Hapus"])[i] || "Edit";
        const startX = width * 0.78;
        const endX = paperX + paperW * 0.52;
        return (
          <div
            key={`${label}-${a}`}
            style={{
              position: "absolute",
              left: startX + (endX - startX) * push,
              top: height * (0.3 + i * 0.1),
              fontFamily: MONO,
              fontWeight: 700,
              fontSize: Math.round(height * 0.034),
              letterSpacing: "0.1em",
              color: REJECT,
              textDecoration: hit ? "line-through" : "none",
              opacity: interpolate(local, [0, 0.14, 1, 1.4], [0, 1, 1, 0]),
              transform: `rotate(${hit ? interpolate(local, [0.3, 1.4], [-4, -12]) : -4}deg)`,
            }}
          >
            {label.toUpperCase()}
          </div>
        );
      })}

      {/* Validated: hand-inked mark, not a badge */}
      {b.stampSec != null && t >= b.stampSec ? (
        <div
          style={{
            position: "absolute",
            left: paperX + paperW * 0.5,
            top: height * 0.24,
            fontFamily: MONO,
            fontWeight: 700,
            fontSize: Math.round(height * 0.036),
            letterSpacing: "0.2em",
            color: "#0f766e",
            borderBottom: "6px solid #0f766e",
            paddingBottom: 6,
            mixBlendMode: "multiply",
            opacity: sp(b.stampSec, 12, 200),
            transform: `rotate(-7deg) scale(${interpolate(sp(b.stampSec, 12, 200), [0, 1], [1.4, 1])})`,
          }}
        >
          {(cutaway.stampLabel || "Tervalidasi").toUpperCase()}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
