import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { CutawayFeed, TimelineCutaway } from "../../types";
import {
  assetSrc,
  Backdrop,
  cueSpring,
  formatAmount,
  Glyph,
  Grain,
  hasNumericValues,
  runningBalance,
  sceneBeats,
  Vignette,
} from "./shared";
import {
  resolveStyle,
  stampStyle,
  type CutawayStyleTokens,
} from "./style";

function activeIndex(t: number, feeds: CutawayFeed[]): number {
  let i = -1;
  for (let n = 0; n < feeds.length; n++) {
    if (t >= feeds[n].atSec) i = n;
  }
  return i;
}

/** Pop + damped shake on the control that just landed. */
function hitMotion(t: number, atSec: number) {
  const local = t - atSec;
  if (local < 0) return { x: 0, scale: 1, rot: 0 };
  const pop = interpolate(local, [0, 0.1, 0.36], [0.88, 1.07, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const damp = interpolate(local, [0, 0.5], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return {
    x: Math.sin(local * 46) * 11 * damp,
    scale: pop,
    rot: Math.sin(local * 30) * 2.4 * damp,
  };
}

function boardKind(numeric: boolean, stateful: boolean) {
  if (stateful) return "access" as const;
  if (numeric) return "ledger" as const;
  return "catalog" as const;
}

/**
 * One engine, three boards from the brief:
 * catalog = category tiles, ledger = running total + rows, access = roles.
 * Colour always from the print recipe. Motion always on the live control.
 */
export const InterfaceStage: React.FC<{ cutaway: TimelineCutaway }> = ({
  cutaway,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;
  const b = sceneBeats(cutaway);
  const s = resolveStyle(cutaway);
  const sp = (cue: number) => cueSpring(frame, fps, cue, 14, 150);
  const open = sp(b.openSec);
  const numeric = hasNumericValues(b.feeds, b.opening);
  const stateful = b.feeds.some((f) => f.state);
  const kind = boardKind(numeric, stateful);
  const balance = runningBalance(t, b.feeds, b.opening, b.arrivalOf, b.openSec);
  const active = activeIndex(t, b.feeds);
  const proof =
    cutaway.proof ||
    cutaway.assets?.find((a) => a.role === "hero" || a.role === "proof") ||
    cutaway.assets?.[0];
  const shot = proof?.src && b.feeds.some((f) => f.focus) ? proof : null;

  const hug = kind !== "access" && !shot;
  const uiW = Math.round(width * (hug ? 0.72 : 1));
  const uiX = hug ? Math.round((width - uiW) / 2) : 0;
  const uiY = hug ? Math.round(height * 0.16) : 0;
  const pad = hug ? Math.round(uiW * 0.055) : 0;

  return (
    <AbsoluteFill style={{ background: "transparent", overflow: "hidden" }}>
      <Backdrop
        cutaway={{
          ...cutaway,
          backdrop: cutaway.backdrop?.kind
            ? cutaway.backdrop
            : { kind: "cam_blur", blurPx: 34, dim: 0.22 },
        }}
        plate="rgba(0,0,0,0.22)"
        defaultDim={0.22}
      />
      {s.vignette ? <Vignette strength={Math.min(s.vignette, 0.28)} /> : null}

      <div
        style={{
          position: "absolute",
          left: uiX,
          top: uiY,
          width: hug ? uiW : width,
          height: hug ? "auto" : height,
          opacity: open,
          transform: `translateY(${interpolate(open, [0, 1], [22, 0])}px)`,
          background: hug ? s.paper : "transparent",
          boxShadow: hug ? `18px 22px 0 ${s.paperEdge}` : undefined,
          padding: hug ? pad : 0,
          boxSizing: "border-box",
          overflow: "visible",
        }}
      >
        {shot?.src ? (
          <ShotSurface
            src={shot.src}
            width={width}
            height={height}
            feeds={b.feeds}
            active={active}
            t={t}
            spot={s.spot}
          />
        ) : (
          <Dashboard
            width={hug ? uiW - pad * 2 : width}
            heightFrame={height}
            kind={kind}
            kicker={b.kicker}
            title={b.title}
            lockLabel={b.lockLabel}
            feeds={b.feeds}
            active={active}
            t={t}
            balance={balance}
            balanceLabel={b.balanceLabel}
            sp={sp}
            s={s}
          />
        )}
      </div>

      {b.stampLabel && b.stampSec != null && sp(b.stampSec) > 0 ? (
        <div
          style={{
            ...stampStyle(s, height, { rotate: -7, weight: 5 }),
            position: "absolute",
            right: width * 0.1,
            bottom: height * 0.1,
            background: s.paper,
            opacity: sp(b.stampSec) * 0.94,
            transform: `rotate(-7deg) scale(${interpolate(sp(b.stampSec), [0, 1], [1.3, 1])})`,
          }}
        >
          {b.stampLabel}
        </div>
      ) : null}

      <Grain
        opacity={s.grain.opacity}
        frequency={s.grain.frequency}
        blend={s.grain.blend}
      />
    </AbsoluteFill>
  );
};

const Head: React.FC<{
  kicker: string;
  title: string;
  heightFrame: number;
  s: CutawayStyleTokens;
}> = ({ kicker, title, heightFrame, s }) => (
  <>
    {kicker ? (
      <div
        style={{
          fontFamily: s.mono,
          fontSize: Math.round(heightFrame * 0.018),
          letterSpacing: "0.22em",
          textTransform: "uppercase",
          color: s.spot,
        }}
      >
        {kicker}
      </div>
    ) : null}
    <div
      style={{
        fontFamily: s.display,
        fontWeight: 800,
        fontSize: Math.round(heightFrame * 0.048),
        letterSpacing: "-0.03em",
        color: s.ink,
        marginTop: 8,
        marginBottom: Math.round(heightFrame * 0.036),
        whiteSpace: "nowrap",
      }}
    >
      {title}
    </div>
  </>
);

const Dashboard: React.FC<{
  width: number;
  heightFrame: number;
  kind: "catalog" | "ledger" | "access";
  kicker: string;
  title: string;
  lockLabel: string;
  feeds: CutawayFeed[];
  active: number;
  t: number;
  balance: number;
  balanceLabel: string;
  sp: (cue: number) => number;
  s: CutawayStyleTokens;
}> = ({
  width,
  heightFrame,
  kind,
  kicker,
  title,
  lockLabel,
  feeds,
  active,
  t,
  balance,
  balanceLabel,
  sp,
  s,
}) => {
  const typeMeta = Math.round(heightFrame * 0.016);
  const typeRow = Math.round(heightFrame * 0.03);

  return (
    <div>
      {kind !== "access" ? (
        <Head kicker={kicker} title={title} heightFrame={heightFrame} s={s} />
      ) : null}

      {kind === "catalog" ? (
        <div style={{ display: "flex", gap: 16 }}>
          {feeds.map((f, i) => {
            const on = sp(f.atSec);
            const tileW = Math.floor((width - (feeds.length - 1) * 16) / feeds.length);
            if (on <= 0) {
              return (
                <div
                  key={`empty-${f.label}`}
                  style={{
                    width: tileW,
                    height: Math.round(heightFrame * 0.2),
                    background: "transparent",
                    border: `2px dashed ${s.paperEdge}`,
                  }}
                />
              );
            }
            const live = i === active;
            const hit = hitMotion(t, f.atSec);
            return (
              <div
                key={f.label}
                style={{
                  width: tileW,
                  minHeight: Math.round(heightFrame * 0.2),
                  boxSizing: "border-box",
                  padding: "22px 20px",
                  background: live ? s.ink : s.paper,
                  color: live ? s.paper : s.ink,
                  outline: `2px solid ${s.ink}`,
                  opacity: on,
                  transform: `translateX(${hit.x}px) rotate(${hit.rot}deg) scale(${hit.scale})`,
                }}
              >
                <div
                  style={{
                    fontFamily: s.display,
                    fontWeight: 800,
                    fontSize: Math.round(heightFrame * 0.032),
                    whiteSpace: "nowrap",
                  }}
                >
                  {f.label}
                </div>
                {f.unit ? (
                  <div
                    style={{
                      marginTop: 10,
                      fontFamily: s.mono,
                      fontSize: typeMeta,
                      letterSpacing: "0.14em",
                      textTransform: "uppercase",
                      color: live ? s.paper : s.spot,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {f.unit}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      ) : null}

      {kind === "ledger" ? (
        <>
          <div
            style={{
              fontFamily: s.mono,
              fontSize: typeMeta,
              letterSpacing: "0.18em",
              textTransform: "uppercase",
              color: s.inkSoft,
            }}
          >
            {balanceLabel || "Total"}
          </div>
          <div
            style={{
              fontFamily: s.display,
              fontWeight: 800,
              fontSize: Math.round(heightFrame * 0.072),
              letterSpacing: "-0.04em",
              color: s.ink,
              marginBottom: Math.round(heightFrame * 0.03),
              whiteSpace: "nowrap",
            }}
          >
            {formatAmount(balance, "Rp")}
          </div>
          {feeds.map((f, i) => {
            const on = sp(f.atSec);
            if (on <= 0) return null;
            const live = i === active;
            const amt = f.amount ?? 0;
            const hit = hitMotion(t, f.atSec);
            return (
              <div
                key={f.label}
                style={{
                  display: "flex",
                  alignItems: "baseline",
                  padding: "14px 0",
                  borderTop: `2px solid ${s.ink}`,
                  opacity: on,
                  transform: `translateX(${hit.x}px) rotate(${hit.rot}deg)`,
                }}
              >
                <span
                  style={{
                    flex: 1,
                    fontFamily: s.ui,
                    fontWeight: 700,
                    fontSize: typeRow,
                    color: s.ink,
                    whiteSpace: "nowrap",
                  }}
                >
                  {f.label}
                </span>
                <span
                  style={{
                    fontFamily: s.mono,
                    fontWeight: 700,
                    fontSize: typeRow,
                    color: live ? s.spot : s.ink,
                    whiteSpace: "nowrap",
                  }}
                >
                  {amt < 0 ? "−" : "+"} {formatAmount(Math.abs(amt), "Rp")}
                </span>
              </div>
            );
          })}
        </>
      ) : null}

      {kind === "access" ? (
        <AccessPoster
          width={width}
          heightFrame={heightFrame}
          kicker={kicker}
          title={title}
          lockLabel={lockLabel}
          feeds={feeds}
          active={active}
          t={t}
          sp={sp}
          s={s}
        />
      ) : null}
    </div>
  );
};

const AccessPoster: React.FC<{
  width: number;
  heightFrame: number;
  kicker: string;
  title: string;
  lockLabel: string;
  feeds: CutawayFeed[];
  active: number;
  t: number;
  sp: (cue: number) => number;
  s: CutawayStyleTokens;
}> = ({
  width,
  heightFrame,
  kicker,
  title,
  lockLabel,
  feeds,
  t,
  sp,
  s,
}) => {
  const labelX = Math.round(width * 0.075);
  const rows = Math.max(1, feeds.length);
  const rowTop = heightFrame * (rows > 3 ? 0.3 : 0.34);
  const rowStep = heightFrame * (rows > 3 ? 0.13 : 0.155);
  const rowY = (i: number) => Math.round(rowTop + i * rowStep);
  const targetX = Math.round(width * 0.62);
  const targetY = Math.round(heightFrame * 0.34);
  const targetW = Math.round(width * 0.3);
  const targetH = Math.round(heightFrame * 0.3);

  return (
    <div style={{ position: "relative", width, height: heightFrame }}>
      <div
        style={{
          position: "absolute",
          left: labelX,
          top: heightFrame * 0.13,
          width: width - labelX * 2,
          opacity: sp(0.15),
        }}
      >
        {kicker ? (
          <div
            style={{
              fontFamily: s.mono,
              fontWeight: 700,
              fontSize: Math.round(heightFrame * 0.021),
              letterSpacing: "0.46em",
              textTransform: "uppercase",
              color: s.spot,
            }}
          >
            {kicker}
          </div>
        ) : null}
        <div
          style={{
            marginTop: 14,
            height: 9,
            background: s.ink,
            transform: `scaleX(${sp(0.15)})`,
            transformOrigin: "left center",
          }}
        />
      </div>

      <svg
        width={width}
        height={heightFrame}
        style={{ position: "absolute", inset: 0 }}
      >
        {feeds.map((f, i) => {
          const on = sp(f.atSec);
          if (on <= 0) return null;
          const denied = f.state === "deny";
          const y = rowY(i) + Math.round(heightFrame * 0.045);
          const from = { x: Math.round(width * 0.46), y };
          const to = {
            x: targetX - 18,
            y: targetY + Math.round(targetH * 0.52),
          };
          const midX = (from.x + to.x) / 2;
          const sag = Math.abs(to.y - from.y) * 0.16 + 26;
          const d = `M ${from.x} ${from.y} Q ${midX} ${from.y + sag} ${to.x} ${to.y}`;
          return (
            <path
              key={`route-${f.label}`}
              d={d}
              fill="none"
              stroke={s.ink}
              strokeWidth={denied ? 7 : 11}
              strokeLinecap="round"
              opacity={denied ? 0.4 : 0.94}
            />
          );
        })}
      </svg>

      {feeds.map((f, i) => {
        const on = sp(f.atSec);
        if (on <= 0) return null;
        const denied = f.state === "deny";
        const hit = hitMotion(t, f.atSec);
        return (
          <div
            key={f.label}
            style={{
              position: "absolute",
              left: labelX,
              top: rowY(i),
              opacity: on,
              transform: `translateX(${hit.x}px) rotate(${hit.rot}deg) scale(${hit.scale})`,
            }}
          >
            <div style={{ position: "relative", display: "inline-block" }}>
              <span
                style={{
                  fontFamily: s.display,
                  fontWeight: 800,
                  fontSize: Math.round(heightFrame * 0.082),
                  letterSpacing: "-0.045em",
                  textTransform: "uppercase",
                  color: s.ink,
                  opacity: denied ? 0.55 : 1,
                  whiteSpace: "nowrap",
                }}
              >
                {f.label}
              </span>
              {denied ? (
                <div
                  style={{
                    position: "absolute",
                    left: -12,
                    right: -12,
                    top: "52%",
                    height: 10,
                    background: s.spot,
                    transform: "rotate(-1.6deg)",
                  }}
                />
              ) : null}
            </div>
            {f.unit ? (
              <div
                style={{
                  marginTop: 4,
                  fontFamily: s.mono,
                  fontWeight: 700,
                  fontSize: Math.round(heightFrame * 0.02),
                  letterSpacing: "0.3em",
                  textTransform: "uppercase",
                  color: denied ? s.spot : s.ink,
                }}
              >
                {f.unit}
              </div>
            ) : null}
          </div>
        );
      })}

      <div
        style={{
          position: "absolute",
          left: targetX,
          top: targetY,
          width: targetW,
          height: targetH,
          background: s.ink,
          padding: Math.round(targetW * 0.07),
          boxSizing: "border-box",
          boxShadow: `18px 20px 0 ${s.paperEdge}`,
          transform: "rotate(-1.4deg)",
        }}
      >
        <div
          style={{
            fontFamily: s.display,
            fontWeight: 800,
            fontSize: Math.round(heightFrame * 0.048),
            lineHeight: 1.02,
            letterSpacing: "-0.035em",
            textTransform: "uppercase",
            color: s.paper,
          }}
        >
          {title}
        </div>
        {[0.62, 0.48, 0.55].map((w, i) => (
          <div
            key={`rule-${i}`}
            style={{
              marginTop: i === 0 ? Math.round(targetH * 0.11) : 14,
              width: `${w * 100}%`,
              height: 6,
              background: s.paper,
              opacity: 0.4,
            }}
          />
        ))}
      </div>

      <div
        style={{
          position: "absolute",
          left: targetX + targetW - Math.round(width * 0.045),
          top: targetY - Math.round(heightFrame * 0.05),
          width: Math.round(width * 0.105),
          height: Math.round(width * 0.105),
          borderRadius: "50%",
          background: s.spot,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          mixBlendMode: "multiply",
        }}
      >
        <Glyph
          name="lock"
          size={Math.round(width * 0.045)}
          color={s.paper}
          strokeWidth={2.6}
        />
      </div>

      {lockLabel ? (
        <div
          style={{
            position: "absolute",
            left: targetX,
            top: targetY + targetH + Math.round(heightFrame * 0.035),
            width: targetW,
            fontFamily: s.mono,
            fontWeight: 700,
            fontSize: Math.round(heightFrame * 0.024),
            letterSpacing: "0.22em",
            textTransform: "uppercase",
            color: s.spot,
          }}
        >
          {lockLabel}
        </div>
      ) : null}
    </div>
  );
};

const ShotSurface: React.FC<{
  src: string;
  width: number;
  height: number;
  feeds: CutawayFeed[];
  active: number;
  t: number;
  spot: string;
}> = ({ src, width, height, feeds, active, t, spot }) => {
  const f = active >= 0 ? feeds[active] : undefined;
  const ring = f?.focus;
  const hit = f ? hitMotion(t, f.atSec) : { x: 0, scale: 1, rot: 0 };
  return (
    <div
      style={{
        position: "relative",
        width,
        height,
        overflow: "hidden",
        background: "#111",
      }}
    >
      <Img
        src={assetSrc(src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "contain",
          objectPosition: "center",
        }}
      />
      {ring ? (
        <div
          style={{
            position: "absolute",
            left: `${ring.x * 100}%`,
            top: `${ring.y * 100}%`,
            width: Math.round(width * 0.48),
            height: Math.round(height * 0.1),
            transform: `translate(-50%, -50%) translateX(${hit.x}px) rotate(${hit.rot}deg) scale(${hit.scale})`,
            border: `3px solid ${spot}`,
            background: "transparent",
            pointerEvents: "none",
          }}
        />
      ) : null}
    </div>
  );
};
