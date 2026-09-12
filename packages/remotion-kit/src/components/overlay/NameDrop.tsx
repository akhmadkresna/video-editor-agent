/**
 * NameDrop — a punchy hook beat: N big words pop in around the speaker one at
 * a time, hold, then all exit together on a cue. Two exit styles:
 *
 *   "fall" (default) — gravity + spin, word leaves as one solid block.
 *   "sand"            — the word disintegrates in place: each letter drifts
 *                        outward in its own (seeded, deterministic) direction
 *                        while blurring and fading, whole word keeps a slow
 *                        zoom-in. Distinct register from "fall" — dissolving
 *                        vs. falling — for variety across a multi-overlay
 *                        episode so every beat doesn't leave the same way.
 *
 * Built for the "ChatGPT error. Claude error. Grok … down." opening — the
 * three names drop as the host says "down". Not part of the A-Roll Text Motion
 * System's fade grammar: the words physically leave, they do not fade as a
 * layer, so OverlayLayer renders this kind without the shared exit-fade and
 * OverlayVeil skips it.
 *
 * Contract (all from the timeline overlay):
 *   steps[]        the words, in spoken order (2–4)
 *   durationSec    Sequence length; must outlast the exit
 *   exitStartSec   when the exit begins, seconds from start (the payoff beat)
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { popIn, seededRandom } from "./motion";
import { cqh } from "./sizing";
import type { OverlayTheme } from "./theme";

export type NameDropExit = "fall" | "sand";

export type NameDropProps = {
  words: string[];
  durationSec: number;
  /** Seconds from start when the exit fires. Falls back to 75% of duration. */
  dropAtSec?: number;
  /** Per-word entrance stagger. Tuned to the spoken cadence in cover.json. */
  staggerSec?: number;
  /** Exit style. Default `fall` (existing gravity+spin) for back-compat. */
  exit?: NameDropExit;
  theme: OverlayTheme;
};

const GRAVITY_PX_S2 = 4200;
const SPIN_DEG_S = 65;
/** "sand" exit tuning. */
const SAND_DISSOLVE_SEC = 0.9;
const SAND_MAX_BLUR_PX = 9;
const SAND_MIN_DRIFT_PX = 55;
const SAND_DRIFT_RANGE_PX = 90;
const SAND_ZOOM_TO = 1.12;

/** Anchor points around the speaker (fractions of frame), by word count. */
const LAYOUTS: Record<number, Array<{ x: number; y: number }>> = {
  1: [{ x: 0.5, y: 0.16 }],
  2: [
    { x: 0.22, y: 0.24 },
    { x: 0.78, y: 0.24 },
  ],
  3: [
    { x: 0.17, y: 0.27 },
    { x: 0.5, y: 0.12 },
    { x: 0.83, y: 0.27 },
  ],
  4: [
    { x: 0.16, y: 0.16 },
    { x: 0.5, y: 0.1 },
    { x: 0.84, y: 0.16 },
    { x: 0.5, y: 0.32 },
  ],
};

export const NameDrop: React.FC<NameDropProps> = ({
  words,
  durationSec,
  dropAtSec,
  staggerSec = 1.05,
  exit = "fall",
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const list = (words || []).map((w) => String(w).trim()).filter(Boolean).slice(0, 4);
  if (!list.length) return null;

  const t = frame / fps;
  const drop = dropAtSec != null ? dropAtSec : durationSec * 0.75;
  const layout = LAYOUTS[list.length] ?? LAYOUTS[3];
  // Big — well past `emphasis` lg. Scales down a touch for 4 words.
  const fontSize = cqh(list.length >= 4 ? 8.5 : 10.5, height);

  return (
    <>
      {list.map((word, i) => {
        const anchor = layout[i] ?? { x: 0.5, y: 0.2 };
        const enter = popIn(frame, fps, {
          durMs: theme.durBase,
          delayMs: i * staggerSec * 1000,
          risePx: fontSize * 0.14,
        });
        // Each word's exit fires a hair after the last, for a cascade.
        const exitT = t - (drop + i * 0.05);

        if (exit === "sand") {
          const dissolve =
            exitT <= 0
              ? 0
              : Math.min(1, exitT / SAND_DISSOLVE_SEC);
          // Slow continuous zoom-in, on top of the pop-in scale, so the
          // shot still feels like it's pushing in as the word dissolves.
          const zoom =
            exitT <= 0 ? 1 : 1 + (SAND_ZOOM_TO - 1) * dissolve;
          const opacity =
            dissolve <= 0
              ? enter.opacity
              : enter.opacity * Math.max(0, 1 - dissolve);
          return (
            <div
              key={`${i}-${word}`}
              style={{
                position: "absolute",
                left: `${anchor.x * 100}%`,
                top: `${anchor.y * 100}%`,
                transform: `translate(-50%, -50%) translateY(${enter.translateY}px) scale(${
                  enter.scale * zoom
                })`,
                fontFamily: theme.fontSans,
                fontWeight: theme.weightHero,
                fontSize,
                letterSpacing: theme.lsTight,
                lineHeight: 1,
                color: theme.ink,
                textShadow: theme.textShadow,
                whiteSpace: "nowrap",
                opacity,
              }}
            >
              {word.split("").map((ch, ci) => {
                if (dissolve <= 0) return <span key={ci}>{ch}</span>;
                // Deterministic per-character scatter direction/distance —
                // seeded by word+char index, not Math.random() (must be
                // stable across parallel frame-render workers).
                const seed = i * 97 + ci * 13;
                const angle = seededRandom(seed) * Math.PI * 2;
                const dist =
                  SAND_MIN_DRIFT_PX + seededRandom(seed + 1) * SAND_DRIFT_RANGE_PX;
                const dx = Math.cos(angle) * dist * dissolve;
                // Slight downward bias (dist * 0.25) — sand still settles a
                // little as it disperses, not a pure radial burst.
                const dy = (Math.sin(angle) * dist + dist * 0.25) * dissolve;
                const blur = SAND_MAX_BLUR_PX * dissolve;
                return (
                  <span
                    key={ci}
                    style={{
                      display: "inline-block",
                      transform: `translate(${dx}px, ${dy}px)`,
                      filter: blur > 0.05 ? `blur(${blur}px)` : undefined,
                    }}
                  >
                    {ch === " " ? " " : ch}
                  </span>
                );
              })}
            </div>
          );
        }

        // "fall" (default) — gravity + spin, word leaves as one solid block.
        const fallY = exitT > 0 ? 0.5 * GRAVITY_PX_S2 * exitT * exitT : 0;
        const spin = exitT > 0 ? exitT * SPIN_DEG_S * (i % 2 === 0 ? 1 : -1) : 0;
        // Keep it opaque until it has cleared the bottom edge.
        const gone = anchor.y * height + fallY > height * 1.15;
        const opacity = gone ? 0 : enter.opacity;

        return (
          <div
            key={`${i}-${word}`}
            style={{
              position: "absolute",
              left: `${anchor.x * 100}%`,
              top: `${anchor.y * 100}%`,
              transform: `translate(-50%, -50%) translateY(${
                enter.translateY + fallY
              }px) rotate(${spin}deg) scale(${enter.scale})`,
              fontFamily: theme.fontSans,
              fontWeight: theme.weightHero,
              fontSize,
              letterSpacing: theme.lsTight,
              lineHeight: 1,
              color: theme.ink,
              textShadow: theme.textShadow,
              whiteSpace: "nowrap",
              opacity,
            }}
          >
            {word}
          </div>
        );
      })}
    </>
  );
};
