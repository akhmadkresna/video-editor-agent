/**
 * Size-band resolution + deterministic shrink-to-fit.
 *
 * Two jobs:
 *
 * 1. Map the DS's `xl`/`lg`/`md` size names onto the *style pack's* per-kind
 *    `*SizeCqh`, not onto hardcoded numbers. This matters because `social`
 *    overrides `emphasis.sizeCqh: 5.2` so its MG fits a top bar, while
 *    `sizeBands.heroCqh` stays 22 — reading the band directly would blow
 *    social's overlays out of their bar (ASSESSMENT §3.3).
 *
 * 2. Keep hero type from clipping. `heroCqh: 22` is ~238px at 1080p, and a
 *    long word at that size is wider than its 48%-width zone box. We shrink
 *    to fit using a character-advance estimate rather than real measurement:
 *    `@remotion/layout-utils` isn't installed, and a heuristic that depends
 *    only on (text, box, base size) stays frame-deterministic, which real
 *    canvas measurement inside a render does not guarantee across workers.
 */
import type { OverlayTheme } from "./theme";

export type SizeName = "xl" | "lg" | "md";

/** Roles a kind can ask to be sized for. */
export type SizeRole = "hero" | "value" | "name" | "step" | "label" | "eyebrow" | "meta";

/** cqh ≈ % of frame height. */
export function cqh(pct: number, frameHeight: number): number {
  return (pct / 100) * frameHeight;
}

/** cqw ≈ % of frame width. */
export function cqw(pct: number, frameWidth: number): number {
  return (pct / 100) * frameWidth;
}

/**
 * `emphasis.sizeCqh` is the dial a style pack uses to say "this is how big
 * hero-ish type may get here". `social` drops it to 5.2 so MG fits a letterbox
 * top bar while leaving `sizeBands.heroCqh` at 22.
 *
 * Reading a band directly therefore blows social's overlays out of their bar —
 * the exact regression this cap exists to prevent. At the default 22 it is a
 * no-op for every band below hero.
 */
function capByEmphasis(baseCqh: number, theme: OverlayTheme): number {
  const cap = theme.emphasis.sizeCqh;
  return cap == null ? baseCqh : Math.min(baseCqh, cap);
}

/**
 * Resolve a DS size name to cqh, routed through the per-kind style override
 * rather than the raw band (ASSESSMENT §3.3).
 */
export function resolveBandCqh(size: SizeName, theme: OverlayTheme): number {
  switch (size) {
    case "xl":
      // `title` — hero scale, but never past what the pack allows.
      return capByEmphasis(theme.bands.heroCqh, theme);
    case "md":
      // `quote` — body scale, likewise capped.
      return capByEmphasis(theme.bands.bodyCqh, theme);
    case "lg":
    default:
      // `emphasis` — the dial itself.
      return theme.emphasis.sizeCqh ?? theme.bands.heroCqh;
  }
}

/** Value size for `stat` / `callout` — packs tune this via `callout.valueSizeCqh`. */
export function valueSizeCqh(theme: OverlayTheme): number {
  return theme.callout.valueSizeCqh ?? capByEmphasis(theme.bands.heroCqh, theme);
}

/** Name line for `lower_third` — `subCqh` has no DS counterpart, so it lands here. */
export function nameSizeCqh(theme: OverlayTheme): number {
  return capByEmphasis(theme.bands.subCqh, theme);
}

/**
 * Estimated rendered width. Used both by the fitter and by count-up, which
 * needs to reserve the width of its *final* value up front — otherwise the box
 * grows every frame as digits are added and everything after it jitters
 * sideways.
 */
export function estimateWidthPx(text: string, fontSizePx: number): number {
  return (text || "").length * avgAdvanceEm(text || "") * fontSizePx;
}

/** Rough per-character advance in em. Caps run wider than mixed case. */
function avgAdvanceEm(text: string): number {
  const letters = text.replace(/\s/g, "");
  if (!letters) return 0.58;
  const upper = letters.replace(/[^A-ZÀ-Þ]/g, "").length;
  const capsRatio = upper / letters.length;
  return 0.58 + 0.06 * capsRatio;
}

/** Width of one word in em at font-size 1. */
function wordWidthEm(word: string): number {
  return word.length * avgAdvanceEm(word);
}

/**
 * Greedy line-breaking, the same algorithm the browser uses for
 * `white-space: normal` — so the predicted line count matches what actually
 * renders. Returns null when a single word is wider than the line (which no
 * amount of wrapping can fix; only shrinking can).
 */
function greedyLineCount(words: string[], availEm: number): number | null {
  if (availEm <= 0) return null;
  const spaceEm = 0.26;
  let lines = 1;
  let cur = 0;
  for (const w of words) {
    const wEm = wordWidthEm(w);
    if (wEm > availEm) return null;
    const add = cur === 0 ? wEm : cur + spaceEm + wEm;
    if (add <= availEm) {
      cur = add;
    } else {
      lines += 1;
      cur = wEm;
    }
  }
  return lines;
}

/** Fixed ladder — a deterministic search, no measurement loop. */
const SCALE_LADDER = [
  1, 0.96, 0.92, 0.88, 0.84, 0.8, 0.75, 0.7, 0.66, 0.62, 0.58, 0.55, 0.5, 0.46, 0.42,
  0.38, 0.34, 0.3, 0.26,
];

/**
 * Shrink `basePx` until the text fits `boxWidthPx` within `maxLines` *and*
 * within `boxHeightPx`.
 *
 * Enforcing the line count matters as much as the width: at `heroCqh: 22` a
 * long line that only respects width still wraps into a wall of text across
 * the speaker's face. Pure function of its inputs → every render worker picks
 * the same size.
 */
export function fitToBox(opts: {
  text: string;
  basePx: number;
  boxWidthPx: number;
  boxHeightPx?: number;
  maxLines?: number;
  lineHeight?: number;
  minScale?: number;
}): number {
  const text = (opts.text || "").trim();
  if (!text || opts.boxWidthPx <= 0) return opts.basePx;

  const words = text.split(/\s+/).filter(Boolean);
  const maxLines = Math.max(1, opts.maxLines ?? 3);
  const lh = opts.lineHeight ?? 1.0;
  const minScale = opts.minScale ?? 0.26;
  // A little headroom absorbs error in the advance table.
  const avail = opts.boxWidthPx * 0.94;

  const heightOk = (lines: number, px: number) =>
    opts.boxHeightPx == null || lines * px * lh <= opts.boxHeightPx;

  // Pass 1 — honour the line budget. For punch type, wrapping into a wall of
  // text is a worse failure than smaller type, so this is the priority.
  for (const s of SCALE_LADDER) {
    if (s < minScale) break;
    const px = opts.basePx * s;
    const lines = greedyLineCount(words, avail / px);
    if (lines == null || lines > maxLines) continue;
    if (!heightOk(lines, px)) continue;
    return px;
  }

  // Pass 2 — nothing fit the line budget (very long text in a narrow zone).
  // Relax the line count but never overflow the box.
  for (const s of SCALE_LADDER) {
    if (s < minScale) break;
    const px = opts.basePx * s;
    const lines = greedyLineCount(words, avail / px);
    if (lines == null) continue;
    if (!heightOk(lines, px)) continue;
    return px;
  }

  return opts.basePx * minScale;
}

/** Hero text: same fit, defaulting to a tighter line budget. */
export function fitHeadline(opts: {
  text: string;
  basePx: number;
  boxWidthPx: number;
  boxHeightPx?: number;
  maxLines?: number;
  lineHeight?: number;
  minScale?: number;
}): number {
  return fitToBox({ maxLines: 3, ...opts });
}
