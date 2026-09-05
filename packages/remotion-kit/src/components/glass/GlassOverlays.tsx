import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { TimelineOverlay } from "../../types";
import { color, font, letterSpacing, radius } from "./tokens";
import { resolveZone, zoneRailAlign } from "../overlayZones";
import type { OverlayZone } from "../../types";

/**
 * `code` and `illustration` — the two kinds explicitly out of scope for the
 * A-Roll Text Motion System port (handoff spec §3: "restyle only" for
 * illustration, "unchanged" for code). Everything else that used to live in
 * this file (title/stat/lower_third/tag/divider/quote and their shared v7
 * motion helpers — punchSpring, slideIn, countUpText, StaggerRise,
 * SelectionHighlight, MonoBadge, TagChip, useExit) has moved to
 * `../overlay/*` and been deleted here; `OverlayLayer.tsx` dispatches to this
 * module only for these two kinds now (see `LEGACY_GLASS_KINDS` in
 * `../overlay/dispatch.tsx`).
 */

function easeOutFade(frame: number, fps: number, delay = 0, ms = 280) {
  const frames = Math.max(1, Math.round((ms / 1000) * fps));
  return interpolate(frame, [delay, delay + frames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
}

const ZoneRail: React.FC<{
  zone: OverlayZone;
  children: React.ReactNode;
}> = ({ zone, children }) => {
  const align = zoneRailAlign(zone);
  return (
    <AbsoluteFill
      style={{
        alignItems: align.alignItems,
        justifyContent: align.justifyContent,
        padding: align.padding,
        textAlign: align.textAlign,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* Text block — no panel: white ink straight on the a-roll, readability */
/* held by the darker scrim OverlayLayer paints behind every overlay    */
/* (not a panel of its own) plus a text-shadow. display:table is the    */
/* shrink-wrap mechanism (width:fit-content resolves wrong when its own */
/* containing block is also auto-sized, e.g. nested one level inside a  */
/* plain rail wrapper, which every card here is).                       */
/* ------------------------------------------------------------------ */

const TextBlock: React.FC<{ children: React.ReactNode; maxWidth?: string | number }> = ({
  children,
  maxWidth = "62%",
}) => (
  <div
    style={{
      display: "table",
      maxWidth,
      color: color.ink,
      textShadow: "0 8px 28px rgba(0,0,0,0.55), 0 2px 8px rgba(0,0,0,0.4)",
    }}
  >
    {children}
  </div>
);

/* ------------------------------------------------------------------ */
/* code — a real macOS terminal window. A screen convention, kept       */
/* deliberately distinct from the a-roll text kinds.                    */
/* ------------------------------------------------------------------ */

const SQL_KEYWORDS = new Set([
  "SELECT", "FROM", "WHERE", "AND", "OR", "INSERT", "INTO", "VALUES",
  "UPDATE", "SET", "DELETE", "JOIN", "ON", "ORDER", "BY", "GROUP",
  "LIMIT", "AS", "NOT", "NULL", "IN",
]);

function renderCodeLine(line: string, key: string): React.ReactNode {
  if (line.trim().startsWith("--")) {
    return (
      <div key={key} style={{ color: "#6b6860", fontStyle: "italic" }}>
        {line}
      </div>
    );
  }
  const parts = line.split(/(\s+|[*=(),?])/).filter((p) => p.length > 0);
  return (
    <div key={key}>
      {parts.map((part, i) => {
        const isKeyword = SQL_KEYWORDS.has(part.toUpperCase());
        return (
          <span key={i} style={{ fontWeight: isKeyword ? 800 : 400, color: "#f0eee8" }}>
            {part}
          </span>
        );
      })}
    </div>
  );
}

const CodeSnippet: React.FC<{ ov: TimelineOverlay }> = ({ ov }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const zone = resolveZone(ov.zone, "code");
  const lines = ov.steps || [];
  const panelOpacity = easeOutFade(frame, fps, 0, 220);
  const y = interpolate(panelOpacity, [0, 1], [10, 0]);
  const cursorOn = Math.floor(frame / Math.round(fps * 0.5)) % 2 === 0;
  return (
    <ZoneRail zone={zone}>
      <div
        style={{
          opacity: panelOpacity,
          transform: `translateY(${y}px)`,
          width: 620,
          maxWidth: "60%",
          background: color.terminalBg,
          border: `1px solid ${color.terminalBorder}`,
          borderRadius: radius.md,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 9,
            padding: "10px 14px",
            background: color.terminalHeaderBg,
            borderBottom: `1px solid ${color.terminalBorder}`,
          }}
        >
          <div style={{ display: "flex", gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: "50%", border: "1.5px solid #6b6860" }} />
            <span style={{ width: 10, height: 10, borderRadius: "50%", border: "1.5px solid #6b6860" }} />
            <span style={{ width: 10, height: 10, borderRadius: "50%", border: "1.5px solid #6b6860" }} />
          </div>
          {ov.title ? (
            <div style={{ flex: 1, textAlign: "center", fontFamily: font.mono, fontSize: 11, color: "#8f8c85", marginRight: 26 }}>
              {ov.title}
            </div>
          ) : null}
        </div>
        <div style={{ padding: "15px 17px 18px" }}>
          {ov.kicker ? (
            <div
              style={{
                fontFamily: font.mono,
                fontWeight: 600,
                fontSize: 10,
                letterSpacing: letterSpacing.caps,
                textTransform: "uppercase",
                color: "#8f8c85",
                marginBottom: 12,
              }}
            >
              {ov.kicker}
            </div>
          ) : null}
          {lines.map((line, i) => {
            const lineOpacity = easeOutFade(frame, fps, Math.round(0.06 * fps) * i + 4, 200);
            const isLast = i === lines.length - 1;
            return (
              <div
                key={`${i}-${line}`}
                style={{ fontFamily: font.mono, fontSize: 14, lineHeight: 1.75, opacity: lineOpacity, whiteSpace: "pre", display: "flex" }}
              >
                <span style={{ width: 20, flexShrink: 0, color: "#55524a", textAlign: "right", marginRight: 14 }}>{i + 1}</span>
                <span>
                  {renderCodeLine(line, String(i))}
                  {isLast ? (
                    <span
                      style={{
                        display: "inline-block",
                        width: 7,
                        height: 14,
                        background: "#f0eee8",
                        marginLeft: 2,
                        verticalAlign: -2,
                        opacity: cursorOn ? 1 : 0,
                      }}
                    />
                  ) : null}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </ZoneRail>
  );
};

/* ------------------------------------------------------------------ */
/* Illustrations — comparisons expressed through TYPE SIZE, not bars    */
/* (no reference uses a bar/progress-track widget; WOVE and TP-7 pair   */
/* a big numeral against a small one). The more illustrative diagrams   */
/* (SVG icons, bordered boxes) keep their shapes, recolored to pure ink.*/
/* ------------------------------------------------------------------ */

function illustrationId(ov: TimelineOverlay): string {
  const m = /illustration:([a-z_]+)/.exec(ov.note || "");
  return m?.[1] || "generic";
}

const ContrastItem: React.FC<{ word: string; num: string; big?: boolean }> = ({ word, num, big }) => (
  <div>
    <div
      style={{
        fontFamily: font.sans,
        fontWeight: big ? 800 : 500,
        fontSize: big ? 19 : 15,
        color: color.inkMuted,
        textTransform: "uppercase",
        letterSpacing: letterSpacing.wide,
        marginBottom: 4,
      }}
    >
      {word}
    </div>
    <div
      style={{
        fontFamily: font.sans,
        fontWeight: big ? 900 : 700,
        fontSize: big ? 104 : 38,
        lineHeight: big ? 0.86 : 0.95,
        letterSpacing: letterSpacing.tight,
        color: color.ink,
        fontVariantNumeric: "tabular-nums",
      }}
    >
      {num}
    </div>
  </div>
);

const ContrastPair: React.FC<{ a: [string, string]; b: [string, string]; arrow?: string }> = ({
  a,
  b,
  arrow = "vs",
}) => (
  <div style={{ display: "flex", alignItems: "baseline", gap: 24, flexWrap: "wrap" }}>
    <ContrastItem word={a[0]} num={a[1]} />
    <div style={{ fontFamily: font.mono, fontSize: 18, color: color.inkFaint, alignSelf: "center" }}>{arrow}</div>
    <ContrastItem word={b[0]} num={b[1]} big />
  </div>
);

const DualTimeline: React.FC<{ labels: string[] }> = ({ labels }) => {
  const [l1 = "Kampus", v1 = "revisi tiap 2-4 tahun", l2 = "Industri", v2 = "pivot tiap 6 bulan"] = labels;
  return <ContrastPair a={[l1, v1.match(/[\d–-]+/)?.[0] || v1]} b={[l2, v2.match(/\d+/)?.[0] || v2]} />;
};

const ScaleCompare: React.FC<{ labels: string[] }> = ({ labels }) => {
  const [a = "tugas akhir · 3 orang", b = "produksi · 300.000 orang"] = labels;
  const [aWord, aNum] = a.split("·").map((s) => s.trim());
  const [bWord, bNum] = b.split("·").map((s) => s.trim());
  return <ContrastPair a={[aWord, aNum || a]} b={[bWord, bNum || b]} arrow="→" />;
};

const SpecGap: React.FC<{ labels: string[] }> = ({ labels }) => {
  const [before = '"gak ada spesifikasi rapi"', after = "kalian yang analisa sendiri"] = labels;
  return (
    <div style={{ maxWidth: 420 }}>
      <div style={{ fontFamily: font.sans, fontStyle: "italic", fontWeight: 500, fontSize: 18, color: color.inkMuted, marginBottom: 12 }}>
        {before}
      </div>
      <div style={{ fontFamily: font.sans, fontWeight: 900, fontSize: 26, letterSpacing: letterSpacing.tight, color: color.ink }}>
        {after}
      </div>
    </div>
  );
};

const CarNoMap: React.FC<{ labels: string[] }> = ({ labels }) => {
  const [title = "Mesin dan rangka ada. Peta belum.", sub = "peta: belum ada"] = labels;
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const drive = interpolate(frame, [0, fps * 2], [0, 60], { extrapolateRight: "clamp" });
  return (
    <div>
      <svg width={340} height={100} viewBox="0 0 340 100">
        <line x1="0" y1="78" x2="340" y2="78" stroke={color.inkFaint} strokeWidth={2.5} strokeDasharray="10 8" />
        <g transform={`translate(${drive},0)`}>
          <rect x="40" y="50" width="66" height="24" rx="6" fill={color.ink} />
          <circle cx="54" cy="76" r="9" fill="none" stroke={color.ink} strokeWidth={2.5} />
          <circle cx="92" cy="76" r="9" fill="none" stroke={color.ink} strokeWidth={2.5} />
        </g>
      </svg>
      <div style={{ fontFamily: font.sans, fontWeight: 800, fontSize: 19, color: color.ink, marginTop: 6, maxWidth: 340 }}>{title}</div>
      <div style={{ fontFamily: font.mono, fontWeight: 500, fontSize: 13, color: color.inkMuted, marginTop: 4 }}>{sub}</div>
    </div>
  );
};

const Compass: React.FC = () => {
  const frame = useCurrentFrame();
  const wobble = Math.sin(frame / 9) * 14;
  return (
    <svg width={120} height={120} viewBox="0 0 120 120">
      <circle cx="60" cy="60" r="50" fill="none" stroke={color.inkFaint} strokeWidth={2} />
      <text x="60" y="20" textAnchor="middle" fontFamily={font.mono} fontSize={12} fill={color.inkMuted}>U</text>
      <text x="60" y="106" textAnchor="middle" fontFamily={font.mono} fontSize={12} fill={color.inkMuted}>S</text>
      <g transform={`rotate(${wobble} 60 60)`}>
        <polygon points="60,16 68,60 60,55 52,60" fill={color.ink} />
        <polygon points="60,104 68,60 60,65 52,60" fill={color.inkMuted} />
      </g>
      <circle cx="60" cy="60" r="4" fill={color.ink} />
    </svg>
  );
};

const LoadTest: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const burst = interpolate(frame, [8, 8 + fps * 0.9], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const rays = 10;
  return (
    <svg width={180} height={180} viewBox="0 0 180 180">
      {Array.from({ length: rays }).map((_, i) => {
        const a = (i / rays) * Math.PI * 2;
        const r1 = 10;
        const r2 = 10 + burst * 62;
        return (
          <line
            key={i}
            x1={90 + Math.cos(a) * r1}
            y1={90 + Math.sin(a) * r1}
            x2={90 + Math.cos(a) * r2}
            y2={90 + Math.sin(a) * r2}
            stroke={color.ink}
            strokeWidth={2.5}
            opacity={burst}
          />
        );
      })}
      <circle cx="90" cy="90" r="10" fill={color.ink} />
    </svg>
  );
};

const StadiumTicket: React.FC<{ labels: string[] }> = ({ labels }) => {
  const [title = "Ijazah bikin kalian masuk. Bukan bikin kalian main.", sub = "Masuk stadion — bukan izin main"] = labels;
  return (
    <div style={{ maxWidth: 400 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 16 }}>
        <div
          style={{
            width: 108, height: 52, border: `2px dashed ${color.ink}`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontFamily: font.mono, fontSize: 11, textAlign: "center", fontWeight: 600, color: color.ink,
          }}
        >
          Boarding pass
        </div>
        <div style={{ fontFamily: font.mono, fontSize: 16, color: color.inkMuted }}>{"→"}</div>
        <div
          style={{
            width: 108, height: 52, border: `2px solid ${color.ink}`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontFamily: font.sans, fontWeight: 800, fontSize: 14, color: color.ink,
          }}
        >
          Ijazah
        </div>
      </div>
      <div style={{ fontFamily: font.sans, fontWeight: 800, fontSize: 19, color: color.ink }}>{title}</div>
      <div style={{ fontFamily: font.mono, fontSize: 13, color: color.inkMuted, marginTop: 6 }}>{sub}</div>
    </div>
  );
};

const Illustration: React.FC<{ ov: TimelineOverlay }> = ({ ov }) => {
  const id = illustrationId(ov);
  const labels = ov.steps || [];
  const frame = useCurrentFrame();
  const opacity = easeOutFade(frame, useVideoConfig().fps, 0, 260);
  const usesContrastPair = id === "dual_timeline" || id === "scale_compare";
  const body = (() => {
    switch (id) {
      case "dual_timeline":
        return <DualTimeline labels={labels} />;
      case "scale_compare":
        return <ScaleCompare labels={labels} />;
      case "spec_gap":
        return <SpecGap labels={labels} />;
      case "car_no_map":
        return <CarNoMap labels={labels} />;
      case "compass":
        return <Compass />;
      case "load_test":
        return <LoadTest />;
      case "stadium_ticket":
        return <StadiumTicket labels={labels} />;
      default:
        return null;
    }
  })();
  return (
    <ZoneRail zone={resolveZone(ov.zone, "illustration")}>
      <div style={{ opacity }}>
        <TextBlock maxWidth={usesContrastPair ? "74%" : "none"}>
          {ov.title ? (
            <div
              style={{
                fontFamily: font.mono,
                fontSize: 11,
                letterSpacing: letterSpacing.caps,
                textTransform: "uppercase",
                color: color.inkMuted,
                marginBottom: 18,
              }}
            >
              {ov.title}
            </div>
          ) : null}
          {body}
        </TextBlock>
      </div>
    </ZoneRail>
  );
};

/* ------------------------------------------------------------------ */
/* Dispatch — code / illustration only. Exit fade is applied by the     */
/* caller (`OverlayLayer.tsx`'s `exitFade`, from the new motion system), */
/* not duplicated here.                                                 */
/* ------------------------------------------------------------------ */

export const GlassOverlay: React.FC<{ ov: TimelineOverlay }> = ({ ov }) => {
  switch (ov.kind) {
    case "code":
      return <CodeSnippet ov={ov} />;
    case "illustration":
      return <Illustration ov={ov} />;
    default:
      return null;
  }
};
