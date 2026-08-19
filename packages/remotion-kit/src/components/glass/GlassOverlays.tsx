import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { TimelineOverlay } from "../../types";
import {
  color,
  font,
  letterSpacing,
  radius,
  paperGridStyle,
  duration,
  toneBorderStyle,
  jitterDeg,
} from "./tokens";

/* ------------------------------------------------------------------ */
/* "Poster Study" house style (v5) — opaque grain-textured paper cards, */
/* pure black ink, zero shadow/blur/color. Legibility comes from the    */
/* paper surface itself (matches every reference: ink on paper never    */
/* needs a shadow). The one exception is `code`, which stays a real     */
/* terminal window (a screen convention, not a print one) recolored     */
/* into black/white/gray. Illustrations that show a comparison (dual_   */
/* timeline, scale_compare) express it through TYPE SIZE, not bar       */
/* charts — a bar/tick-mark widget isn't in any reference; a big        */
/* numeral next to a small one is (see WOVE, TP-7).                     */
/*                                                                      */
/* Face-safe placement unchanged: left-third + vertically centered      */
/* (title/divider/quote/code/illustration) or bottom-left corner        */
/* (stat/lower_third/tag) — camera_play keeps the host roughly          */
/* centered, so nothing anchors dead-center.                            */
/*                                                                      */
/* IMPORTANT: Remotion's <AbsoluteFill> defaults to flexDirection:      */
/* "column" — alignItems is the HORIZONTAL axis here, justifyContent    */
/* is VERTICAL (opposite of normal row-flex intuition).                 */
/*                                                                      */
/* Motion timings — exact, from the Kresna "Motion & diagram guide":    */
/*   Title/divider cards: punch in (scale 0.94->1, fade), 220ms,        */
/*     ease-punch. Hold, hard cut out.                                  */
/*   Stat callouts: number counts up from 0 over 300ms, punch ease;     */
/*     label fades in 80ms after.                                       */
/*   Quote cards: fade/rise in 280ms; exit plain fade 200ms ease-out,   */
/*     no punch on exit.                                                */
/*   Chips/lower third: slide in 12px + fade, 180ms, staggered ~60ms.   */
/* ------------------------------------------------------------------ */

function punchSpring(frame: number, fps: number, delay = 0, ms = duration.base) {
  return spring({
    frame: Math.max(0, frame - delay),
    fps,
    config: { damping: 12, stiffness: 260 },
    durationInFrames: Math.round(fps * (ms / 1000)),
  });
}

function easeOutFade(frame: number, fps: number, delay = 0, ms = 280) {
  const frames = Math.max(1, Math.round((ms / 1000) * fps));
  return interpolate(frame, [delay, delay + frames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
}

function useExit(
  durationSec: number,
  exitStartSec: number | undefined,
  fps: number,
  frame: number,
  mode: "hardcut" | "fade" = "hardcut",
  ms = 200,
) {
  const total = Math.max(1, Math.round(durationSec * fps));
  if (mode === "hardcut") return 1;
  const exitFrames = Math.round((ms / 1000) * fps);
  const exitFrom =
    exitStartSec != null
      ? Math.min(total - 2, Math.max(4, Math.round(exitStartSec * fps)))
      : Math.max(0, total - exitFrames);
  return interpolate(frame, [exitFrom, total], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
}

function slideIn(frame: number, fps: number, staggerIndex = 0) {
  const delay = Math.round(staggerIndex * 0.06 * fps);
  const dur = Math.round(0.18 * fps);
  const p = interpolate(frame, [delay, delay + dur], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return { opacity: p, y: interpolate(p, [0, 1], [12, 0]) };
}

function countUpText(raw: string, progress: number): string {
  return raw.replace(/\d+(?:,\d+)?/g, (tok) => {
    const decimals = tok.includes(",") ? tok.split(",")[1].length : 0;
    const target = parseFloat(tok.replace(",", "."));
    const current = target * progress;
    return decimals > 0
      ? current.toFixed(decimals).replace(".", ",")
      : String(Math.round(current));
  });
}

/* ------------------------------------------------------------------ */
/* Rails — face-safe placement (see flex-axis note above)               */
/* ------------------------------------------------------------------ */

const LeftRail: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ alignItems: "flex-start", justifyContent: "center", padding: "0 8%" }}>
    {children}
  </AbsoluteFill>
);

const BottomLeftRail: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ alignItems: "flex-start", justifyContent: "flex-end", padding: "0 8% 9%" }}>
    {children}
  </AbsoluteFill>
);

/* ------------------------------------------------------------------ */
/* Paper card — opaque, unevenly-gridded, sharp corners, zero shadow    */
/* ------------------------------------------------------------------ */

/** Base dog-ear size in px, plus a small per-card jitter (same deterministic
 * hash as the grid/highlight rotation) so cards don't all read as an
 * identical die-cut shape — a real folded corner varies card to card. */
const FOLD_BASE = 22;

const PaperCard: React.FC<{ children: React.ReactNode; maxWidth?: string | number; id?: string }> = ({
  children,
  maxWidth = "62%",
  id = "card",
}) => {
  const fold = FOLD_BASE + Math.abs(jitterDeg(id, 7));
  return (
    <div
      style={{
        position: "relative",
        // Verified by isolated repro: width:fit-content resolves wrong
        // (too narrow) whenever this box's own containing block is ALSO
        // auto/shrink-to-fit-sized (e.g. nested one level inside a plain
        // wrapper div, as every non-stat card already was) — the
        // "available space" fit-content clamps against goes indefinite
        // and it silently undershoots. display:table is the old,
        // boringly reliable shrink-wrap mechanism and doesn't have that
        // failure mode at any nesting depth — use it instead everywhere.
        display: "table",
        maxWidth,
        background: color.paper,
        color: color.ink,
        // clip-path alone can leave a stray sliver on some out-of-flow
        // descendants (e.g. the selection-highlight's caret handles) in
        // headless Chromium — overflow:hidden backs it up so nothing ever
        // paints past the card's own shape.
        overflow: "hidden",
        clipPath: `polygon(0 0, calc(100% - ${fold}px) 0, 100% ${fold}px, 100% 100%, 0 100%)`,
      }}
    >
      <div style={{ position: "absolute", inset: 0, ...paperGridStyle, pointerEvents: "none" }} />
      {/* Folded corner — a real dog-ear, not a rectangle: the paper's
       * underside triangle plus a thin crease line along the fold. */}
      <div
        style={{
          position: "absolute",
          top: 0,
          right: 0,
          width: 0,
          height: 0,
          borderStyle: "solid",
          borderWidth: `0 ${fold}px ${fold}px 0`,
          borderColor: "transparent rgba(16,18,20,0.16) transparent transparent",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 0,
          right: fold,
          width: fold * 1.42,
          height: 1,
          background: "rgba(16,18,20,0.3)",
          transform: "rotate(45deg)",
          transformOrigin: "left top",
        }}
      />
      <div style={{ position: "relative", padding: "48px 56px" }}>{children}</div>
    </div>
  );
};

/** Text-selection highlight — translucent indigo bar + thin caret line +
 * round handle dot (top and bottom) at each end of the range. This is the
 * mobile/OS text-select pattern (long-press to select), not a design-tool
 * resize box — deliberately not a rectangular border with 8 square
 * handles, which read as too mechanical/stiff in an earlier pass. The
 * bar's rotation is a small deterministic jitter per overlay id so
 * repeated instances don't all sit at an identical angle.
 *
 * This is its own motion beat, not a static decoration: the card/text
 * appears first, then — after `delayMs` — the bar sweeps in left-to-right
 * (as if just dragged to select), and the caret+handle pair at each end
 * pops in once the sweep lands, left end first. */
const SelectionHighlight: React.FC<{ children: React.ReactNode; id: string; delayMs?: number }> = ({
  children,
  id,
  delayMs = 340,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const rot = jitterDeg(id, 0.6);
  const delay = Math.round((delayMs / 1000) * fps);
  const sweepFrames = Math.round(fps * (duration.base / 1000));
  const sweep = spring({
    frame: Math.max(0, frame - delay),
    fps,
    config: { damping: 14, stiffness: 220 },
    durationInFrames: sweepFrames,
  });
  const handleFrames = Math.round(fps * 0.12);
  const handleAt = (stagger: number) =>
    interpolate(
      frame,
      [delay + Math.round(sweepFrames * 0.55) + stagger, delay + Math.round(sweepFrames * 0.55) + stagger + handleFrames],
      [0, 1],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
    );
  const leftHandle = handleAt(0);
  const rightHandle = handleAt(Math.round(fps * 0.07));
  const caret: React.CSSProperties = {
    position: "absolute",
    top: "-8%",
    bottom: "-8%",
    width: 2,
    background: color.accent,
  };
  const dot = (pos: "top" | "bottom", reveal: number): React.CSSProperties => ({
    position: "absolute",
    width: 9,
    height: 9,
    borderRadius: "50%",
    background: color.accent,
    left: "50%",
    transform: `translateX(-50%) scale(${reveal})`,
    [pos]: -4.5,
  });
  return (
    <span style={{ position: "relative", zIndex: 0, display: "inline-block" }}>
      <span
        style={{
          position: "absolute",
          left: "-3%",
          right: "-3%",
          top: "6%",
          bottom: "2%",
          background: color.accentSoft,
          zIndex: -1,
          transform: `scaleX(${sweep}) rotate(${rot}deg)`,
          transformOrigin: "left center",
        }}
      />
      <span style={{ ...caret, left: "-3%", opacity: leftHandle }}>
        <span style={dot("top", leftHandle)} />
        <span style={dot("bottom", leftHandle)} />
      </span>
      <span style={{ ...caret, right: "-3%", opacity: rightHandle }}>
        <span style={dot("top", rightHandle)} />
        <span style={dot("bottom", rightHandle)} />
      </span>
      {children}
    </span>
  );
};

/** Mono badge — bracket-bordered label. Dashed border = "amber" tone
 * (caution/estimate), solid = sourced/plain. See tokens.toneBorderStyle. */
const MonoBadge: React.FC<{ children: React.ReactNode; tone?: "teal" | "amber" | "neutral" }> = ({
  children,
  tone,
}) => (
  <div
    style={{
      display: "inline-block",
      fontFamily: font.mono,
      fontSize: 12,
      letterSpacing: letterSpacing.caps,
      color: color.ink,
      border: `1px solid ${color.ink}`,
      borderStyle: toneBorderStyle(tone),
      padding: "3px 10px",
      marginBottom: 14,
    }}
  >
    {children}
  </div>
);

/** Small mono-bordered chip — TitleCard/LowerThird tag rows. */
const TagChip: React.FC<{ label: string; index: number; frame: number; fps: number }> = ({
  label,
  index,
  frame,
  fps,
}) => {
  const t = slideIn(frame, fps, index + 1);
  return (
    <span
      style={{
        opacity: t.opacity,
        transform: `translateY(${t.y}px)`,
        display: "inline-block",
        fontFamily: font.mono,
        fontWeight: 500,
        fontSize: 12,
        letterSpacing: letterSpacing.caps,
        color: color.ink,
        border: `1px solid ${color.ink}`,
        padding: "3px 9px",
      }}
    >
      {label}
    </span>
  );
};

/* ------------------------------------------------------------------ */
/* Title card — dictionary-poster layout: meta row, italic kicker,      */
/* huge headline with a highlight block on the accent phrase, footer    */
/* meta row. Falls back to a plain wordmark+line layout (outro/         */
/* subscribe) when there's no kicker.                                   */
/* ------------------------------------------------------------------ */

const TitleCard: React.FC<{ ov: TimelineOverlay }> = ({ ov }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = punchSpring(frame, fps);
  const scale = interpolate(s, [0, 1], [0.94, 1]);
  const opacity = interpolate(frame, [0, 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const tags = ov.steps || [];
  const isOutro = !ov.kicker && !ov.accent;
  return (
    <LeftRail>
      <div style={{ transform: `scale(${scale})`, opacity }}>
        <PaperCard maxWidth="64%" id={ov.id}>
          {isOutro ? (
            <>
              <div
                style={{
                  fontFamily: font.sans,
                  fontStyle: "italic",
                  fontWeight: 500,
                  fontSize: 30,
                  marginBottom: 14,
                }}
              >
                Kresna
              </div>
              <div style={{ fontFamily: font.sans, fontSize: 18, color: color.inkMuted }}>
                {ov.text || ov.title}
              </div>
            </>
          ) : (
            <>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontFamily: font.mono,
                  fontSize: 11,
                  letterSpacing: letterSpacing.caps,
                  color: color.inkMuted,
                  marginBottom: 14,
                }}
              >
                <span>KRESNA</span>
                <span>+</span>
              </div>
              {ov.kicker ? (
                <div
                  style={{
                    fontFamily: font.sans,
                    fontStyle: "italic",
                    fontWeight: 500,
                    fontSize: 16,
                    marginBottom: 6,
                  }}
                >
                  {ov.kicker.toLowerCase()}
                </div>
              ) : null}
              <div
                style={{
                  fontFamily: font.sans,
                  fontWeight: 900,
                  fontSize: 56,
                  lineHeight: 0.98,
                  letterSpacing: letterSpacing.tight,
                }}
              >
                {ov.text || ov.title}
                {ov.accent ? (
                  <>
                    <br />
                    <SelectionHighlight id={ov.id}>
                      <span style={{ fontStyle: "italic" }}>{ov.accent}</span>
                    </SelectionHighlight>
                  </>
                ) : null}
              </div>
            </>
          )}
          {tags.length ? (
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: 10,
                marginTop: 18,
                paddingTop: 10,
                borderTop: `1px solid ${color.inkFaint}`,
                fontFamily: font.mono,
                fontSize: 10,
                letterSpacing: letterSpacing.caps,
                color: color.inkMuted,
              }}
            >
              {tags.map((t, i) => (
                <TagChip key={t} label={t} index={i} frame={frame} fps={fps} />
              ))}
            </div>
          ) : null}
        </PaperCard>
      </div>
    </LeftRail>
  );
};

/* ------------------------------------------------------------------ */
/* Stat callout — number counts up from 0 over 300ms (punch ease),      */
/* label fades in 80ms after. Mono bracket badge (dashed = estimate),   */
/* numeral, rule, mono caps caption. Paper card, bottom-left.           */
/* ------------------------------------------------------------------ */

const StatCallout: React.FC<{ ov: TimelineOverlay }> = ({ ov }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = punchSpring(frame, fps);
  const scale = interpolate(s, [0, 1], [0.94, 1]);
  const countProgress = Math.min(1, Math.max(0, punchSpring(frame, fps, 0, 300)));
  const numberOpacity = interpolate(frame, [0, 4], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const labelDelay = Math.round(0.08 * fps) + Math.round(0.3 * fps);
  const labelOpacity = easeOutFade(frame, fps, labelDelay, 260);
  const displayValue = ov.value ? countUpText(ov.value, countProgress) : "";
  return (
    <BottomLeftRail>
      {/* PaperCard must never be the *direct* flex child of a rail — a
       * flex item's display is blockified per spec, which was silently
       * defeating width:fit-content on the card and letting the nowrap
       * stat number get clipped by the card's own overflow:hidden. Every
       * other card kind already wraps PaperCard in a plain div; this one
       * didn't, which is why it was the one still breaking. */}
      <div>
        <PaperCard maxWidth="64%" id={ov.id}>
        {ov.sourceLabel ? (
          <div style={{ opacity: labelOpacity }}>
            <MonoBadge tone={ov.tone}>{ov.sourceLabel}</MonoBadge>
          </div>
        ) : null}
        <div
          style={{
            opacity: numberOpacity,
            transform: `scale(${scale})`,
            transformOrigin: "left bottom",
            whiteSpace: "nowrap",
          }}
        >
          <SelectionHighlight id={ov.id}>
            <span
              style={{
                fontFamily: font.sans,
                fontWeight: 900,
                fontSize: 110,
                lineHeight: 0.84,
                letterSpacing: letterSpacing.tight,
                fontVariantNumeric: "tabular-nums",
                whiteSpace: "nowrap",
              }}
            >
              {displayValue}
            </span>
          </SelectionHighlight>
        </div>
        {ov.title ? (
          <>
            <div style={{ width: "100%", height: 2, background: color.ink, margin: "12px 0" }} />
            <div
              style={{
                fontFamily: font.mono,
                fontWeight: 500,
                fontSize: 13,
                letterSpacing: letterSpacing.normal,
                color: color.inkMuted,
                textTransform: "uppercase",
                lineHeight: 1.5,
                opacity: labelOpacity,
              }}
            >
              {ov.title}
            </div>
          </>
        ) : null}
        </PaperCard>
      </div>
    </BottomLeftRail>
  );
};

/* ------------------------------------------------------------------ */
/* Lower third — paper card, bottom-left; name + mono role + tag row    */
/* ------------------------------------------------------------------ */

const LowerThird: React.FC<{ ov: TimelineOverlay }> = ({ ov }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const main = slideIn(frame, fps, 0);
  const tags = ov.steps || [];
  return (
    <BottomLeftRail>
      <div style={{ opacity: main.opacity, transform: `translateY(${main.y}px)` }}>
        <PaperCard maxWidth="none" id={ov.id}>
          <div style={{ fontFamily: font.sans, fontWeight: 900, fontSize: 36, letterSpacing: letterSpacing.tight }}>
            {ov.text}
          </div>
          {ov.title ? (
            <div
              style={{
                fontFamily: font.mono,
                fontWeight: 500,
                fontSize: 12,
                letterSpacing: letterSpacing.caps,
                color: color.inkMuted,
                textTransform: "uppercase",
                marginTop: 6,
              }}
            >
              {ov.title}
            </div>
          ) : null}
          {tags.length ? (
            <div style={{ display: "flex", gap: 10, marginTop: 12, flexWrap: "wrap" }}>
              {tags.map((tag, i) => (
                <TagChip key={tag} label={tag} index={i} frame={frame} fps={fps} />
              ))}
            </div>
          ) : null}
        </PaperCard>
      </div>
    </BottomLeftRail>
  );
};

/* ------------------------------------------------------------------ */
/* Standalone tag badge — small mono chip, top-left                    */
/* ------------------------------------------------------------------ */

const TagBadge: React.FC<{ ov: TimelineOverlay }> = ({ ov }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = slideIn(frame, fps, 0);
  return (
    <AbsoluteFill style={{ alignItems: "flex-start", justifyContent: "flex-start", padding: "8%" }}>
      <div style={{ opacity: s.opacity, transform: `translateY(${s.y}px)` }}>
        <PaperCard maxWidth="none" id={ov.id}>
          <span style={{ fontFamily: font.mono, fontWeight: 600, fontSize: 14, letterSpacing: letterSpacing.caps }}>
            {ov.text}
          </span>
        </PaperCard>
      </div>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* Section divider — bracket badge numbering, ghost numeral, headline   */
/* ------------------------------------------------------------------ */

function dividerNumeral(kicker: string | null | undefined): string | null {
  if (!kicker) return null;
  const m = /\b(\d{2})\b/.exec(kicker);
  return m ? m[1] : null;
}

const SectionDivider: React.FC<{ ov: TimelineOverlay }> = ({ ov }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = punchSpring(frame, fps);
  const scale = interpolate(s, [0, 1], [0.94, 1]);
  const opacity = interpolate(frame, [0, 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const numeral = dividerNumeral(ov.kicker);
  return (
    <LeftRail>
      <div style={{ transform: `scale(${scale})`, opacity, position: "relative", maxWidth: "64%" }}>
        <PaperCard maxWidth="none" id={ov.id}>
          {numeral ? (
            <div
              style={{
                position: "absolute",
                top: 4,
                right: -10,
                fontFamily: font.sans,
                fontWeight: 900,
                fontSize: 170,
                lineHeight: 1,
                color: color.ink,
                opacity: 0.07,
                userSelect: "none",
              }}
            >
              {numeral}
            </div>
          ) : null}
          <div style={{ position: "relative" }}>
            {ov.kicker ? (
              <div
                style={{
                  fontFamily: font.mono,
                  fontSize: 12,
                  letterSpacing: letterSpacing.caps,
                  color: color.inkMuted,
                  marginBottom: 12,
                }}
              >
                [ <b style={{ color: color.ink, fontWeight: 700 }}>{ov.kicker}</b> ]
              </div>
            ) : null}
            <div
              style={{
                fontFamily: font.sans,
                fontWeight: 900,
                fontSize: 44,
                lineHeight: 1.02,
                letterSpacing: letterSpacing.tight,
              }}
            >
              {ov.title || ov.text}
            </div>
          </div>
        </PaperCard>
      </div>
    </LeftRail>
  );
};

/** Splits `text` on the first occurrence of `accent` and wraps just that
 * substring in the italic SelectionHighlight treatment — for inline
 * word-or-phrase emphasis inside a full sentence (quotes), as opposed to
 * TitleCard's accent which is always its own trailing line. */
function renderTextWithAccent(text: string, accent: string | undefined | null, id: string): React.ReactNode {
  if (!accent) return text;
  const idx = text.indexOf(accent);
  if (idx === -1) return text;
  return (
    <>
      {text.slice(0, idx)}
      <SelectionHighlight id={id}>
        <span style={{ fontStyle: "italic" }}>{accent}</span>
      </SelectionHighlight>
      {text.slice(idx + accent.length)}
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Quote card — now literally the TitleCard treatment (same meta row,   */
/* same bold display headline typography, same punch-in, same footer   */
/* rule) instead of a small justified paragraph: a quote is a headline  */
/* someone else said, not a paragraph. The accent word/phrase (if any)  */
/* gets the italic selection-highlight treatment inline, not the whole  */
/* sentence. */
/* ------------------------------------------------------------------ */

const QuoteCard: React.FC<{ ov: TimelineOverlay }> = ({ ov }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = punchSpring(frame, fps);
  const scale = interpolate(s, [0, 1], [0.94, 1]);
  const opacity = interpolate(frame, [0, 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <LeftRail>
      <div style={{ transform: `scale(${scale})`, opacity }}>
        <PaperCard maxWidth="64%" id={ov.id}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontFamily: font.mono,
              fontSize: 11,
              letterSpacing: letterSpacing.caps,
              color: color.inkMuted,
              marginBottom: 14,
            }}
          >
            <span>KUTIPAN</span>
            <span>”</span>
          </div>
          <div
            style={{
              fontFamily: font.sans,
              fontStyle: "italic",
              fontWeight: 500,
              fontSize: 16,
              marginBottom: 6,
            }}
          >
            {ov.kicker ? ov.kicker.toLowerCase() : "kata mereka"}
          </div>
          <div
            style={{
              fontFamily: font.sans,
              fontWeight: 900,
              fontSize: 40,
              lineHeight: 0.98,
              letterSpacing: letterSpacing.tight,
            }}
          >
            {renderTextWithAccent(ov.text || "", ov.accent, ov.id)}
          </div>
        </PaperCard>
      </div>
    </LeftRail>
  );
};

/* ------------------------------------------------------------------ */
/* Code snippet — real terminal window, kept (a screen convention, not  */
/* a print one) but recolored black/white/gray: outline traffic dots,   */
/* bold weight for keywords instead of syntax color.                    */
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
  const lines = ov.steps || [];
  const panelOpacity = easeOutFade(frame, fps, 0, 220);
  const y = interpolate(panelOpacity, [0, 1], [10, 0]);
  const cursorOn = Math.floor(frame / Math.round(fps * 0.5)) % 2 === 0;
  return (
    <LeftRail>
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
    </LeftRail>
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
          <circle cx="54" cy="76" r="9" fill={color.paper} stroke={color.ink} strokeWidth={2.5} />
          <circle cx="92" cy="76" r="9" fill={color.paper} stroke={color.ink} strokeWidth={2.5} />
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
    <LeftRail>
      <div style={{ opacity }}>
        <PaperCard maxWidth={usesContrastPair ? "74%" : "none"} id={ov.id}>
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
        </PaperCard>
      </div>
    </LeftRail>
  );
};

/* ------------------------------------------------------------------ */
/* Dispatch                                                             */
/* ------------------------------------------------------------------ */

export function isGlassKind(kind: string): boolean {
  return [
    "title",
    "stat",
    "lower_third",
    "tag",
    "divider",
    "quote",
    "code",
    "illustration",
  ].includes(kind);
}

export const GlassOverlay: React.FC<{ ov: TimelineOverlay }> = ({ ov }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // Quote now shares TitleCard's punch-in treatment, so it hard-cuts out
  // like every other punch-in card instead of the old soft fade.
  const exitMode: "hardcut" | "fade" =
    ov.kind === "lower_third" || ov.kind === "tag" ? "fade" : "hardcut";
  const exitMs = 180;
  const exit = useExit(ov.durationSec, ov.exitStartSec, fps, frame, exitMode, exitMs);
  const body = (() => {
    switch (ov.kind) {
      case "title":
        return <TitleCard ov={ov} />;
      case "stat":
        return <StatCallout ov={ov} />;
      case "lower_third":
        return <LowerThird ov={ov} />;
      case "tag":
        return <TagBadge ov={ov} />;
      case "divider":
        return <SectionDivider ov={ov} />;
      case "quote":
        return <QuoteCard ov={ov} />;
      case "code":
        return <CodeSnippet ov={ov} />;
      case "illustration":
        return <Illustration ov={ov} />;
      default:
        return null;
    }
  })();
  return <AbsoluteFill style={{ opacity: exit }}>{body}</AbsoluteFill>;
};
