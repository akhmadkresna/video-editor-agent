import type {
  CutawayFamily,
  CutawayLook,
  CutawayStyleName,
  CutawayTone,
  TimelineCutaway,
} from "../../types";

/**
 * One place where every cutaway's material lives: stock, inks, type and the
 * mark language. InterfaceStage owns layout and hit-motion; it must not invent
 * colour.
 *
 * A style is a print recipe, not a theme switcher — `paper` is a real surface a
 * family can print on, `plate` is what the blurred cam gets washed with, and
 * `spot` is the single second ink used for stamps, strikes and seals.
 */
export type CutawayStyleTokens = {
  name: CutawayStyleName;
  /** Wash over footage so elements stay readable; also the field colour. */
  plate: string;
  /** Backdrop dim when the brief does not set one. */
  plateDim: number;
  /** Type sitting directly on the plate. */
  onPlate: string;
  onPlateSoft: string;
  /** Surface a family can print on (receipt, print, clipping). */
  paper: string;
  paperEdge: string;
  /** Inks used on `paper`. */
  ink: string;
  inkSoft: string;
  /** The one second ink: stamps, strikes, seals, accents. */
  spot: string;
  spotSoft: string;
  /** Refusal ink; usually the spot unless the spot is already warm. */
  reject: string;
  display: string;
  mono: string;
  ui: string;
  grain: {
    opacity: number;
    frequency: number;
    blend: "multiply" | "overlay" | "soft-light";
  };
  vignette: number;
  /** 0 = printed (hard corners, no cards); >0 = screen surfaces. */
  radius: number;
  /** Cards and fills vs bare rules and type. */
  chrome: boolean;
};

const DISPLAY = 'Syne, "Segoe UI", "Helvetica Neue", Arial, sans-serif';
const UI = '"Instrument Sans", "Segoe UI", system-ui, sans-serif';
const MONO =
  '"JetBrains Mono", "Roboto Mono", Consolas, ui-monospace, monospace';

/** Series accent, kept for the screen-surface styles. */
const SKY = "#7dd3fc";
const SKY_DEEP = "#0ea5e9";

export const CUTAWAY_STYLES: Record<CutawayStyleName, CutawayStyleTokens> = {
  /** Two-colour riso poster: cream stock, black ink, one red. */
  press: {
    name: "press",
    plate: "#efe5d2",
    plateDim: 0.93,
    onPlate: "#191510",
    onPlateSoft: "rgba(25,21,16,0.58)",
    paper: "#fbf7ee",
    paperEdge: "rgba(25,21,16,0.16)",
    ink: "#191510",
    inkSoft: "rgba(25,21,16,0.6)",
    spot: "#d3372b",
    spotSoft: "rgba(211,55,43,0.5)",
    reject: "#d3372b",
    display: DISPLAY,
    mono: MONO,
    ui: UI,
    grain: { opacity: 0.26, frequency: 1.05, blend: "multiply" },
    vignette: 0,
    radius: 0,
    chrome: false,
  },
  /** Thermal till roll: warm paper, near-black print, validated in teal. */
  thermal: {
    name: "thermal",
    plate: "#0f171f",
    plateDim: 0.62,
    onPlate: "#f6f2e8",
    onPlateSoft: "rgba(246,242,232,0.6)",
    paper: "#f6f2e8",
    paperEdge: "rgba(0,0,0,0.45)",
    ink: "#1d1d1b",
    inkSoft: "rgba(29,29,27,0.55)",
    spot: "#0f766e",
    spotSoft: "rgba(15,118,110,0.5)",
    reject: "#e11d48",
    display: DISPLAY,
    mono: MONO,
    ui: UI,
    grain: { opacity: 0.1, frequency: 1.1, blend: "multiply" },
    vignette: 0.5,
    radius: 0,
    chrome: false,
  },
  /** Print pinned in a darkroom: black field, photo paper, chinagraph red. */
  darkroom: {
    name: "darkroom",
    plate: "#100d0a",
    plateDim: 0.72,
    onPlate: "#f6f1e6",
    onPlateSoft: "rgba(246,241,230,0.5)",
    paper: "#f6f1e6",
    paperEdge: "rgba(0,0,0,0.62)",
    ink: "#171310",
    inkSoft: "rgba(23,19,16,0.62)",
    spot: "#d8443c",
    spotSoft: "rgba(216,68,60,0.5)",
    reject: "#d8443c",
    display: DISPLAY,
    mono: MONO,
    ui: UI,
    grain: { opacity: 0.13, frequency: 0.9, blend: "overlay" },
    vignette: 0.6,
    radius: 0,
    chrome: false,
  },
  /** Cyanotype: white lines burned into prussian-blue paper, amber seals. */
  cyanotype: {
    name: "cyanotype",
    plate: "#0d3b58",
    plateDim: 0.9,
    onPlate: "#f4fafd",
    onPlateSoft: "rgba(240,248,252,0.62)",
    paper: "#e8f2f8",
    paperEdge: "rgba(3,25,42,0.55)",
    ink: "#0b3049",
    inkSoft: "rgba(11,48,73,0.6)",
    spot: "#f2b544",
    spotSoft: "rgba(242,181,68,0.5)",
    reject: "#ff9d8a",
    display: DISPLAY,
    mono: MONO,
    ui: UI,
    grain: { opacity: 0.2, frequency: 0.75, blend: "soft-light" },
    vignette: 0.5,
    radius: 0,
    chrome: false,
  },
  /** Screen surface, dark: the series accent on a deep plate. */
  night: {
    name: "night",
    plate: "#0b1723",
    plateDim: 0.7,
    onPlate: "#ffffff",
    onPlateSoft: "rgba(255,255,255,0.55)",
    paper: "rgba(255,255,255,0.07)",
    paperEdge: "rgba(0,0,0,0.45)",
    ink: "#ffffff",
    inkSoft: "rgba(255,255,255,0.55)",
    spot: SKY,
    spotSoft: "rgba(125,211,252,0.5)",
    reject: "#f87171",
    display: DISPLAY,
    mono: MONO,
    ui: UI,
    grain: { opacity: 0.08, frequency: 0.9, blend: "overlay" },
    vignette: 0.35,
    radius: 28,
    chrome: true,
  },
  /** Screen surface, light: the flat daylight treatment. */
  daylight: {
    name: "daylight",
    plate: "#d9e2ec",
    plateDim: 0.86,
    onPlate: "#0c1c2a",
    onPlateSoft: "rgba(12,28,42,0.55)",
    paper: "#ffffff",
    paperEdge: "rgba(12,28,42,0.18)",
    ink: "#0c1c2a",
    inkSoft: "rgba(12,28,42,0.55)",
    spot: SKY_DEEP,
    spotSoft: "rgba(14,165,233,0.45)",
    reject: "#e11d48",
    display: DISPLAY,
    mono: MONO,
    ui: UI,
    grain: { opacity: 0.07, frequency: 1, blend: "multiply" },
    vignette: 0.2,
    radius: 12,
    chrome: true,
  },
};

/** Legacy `look` values resolve onto the nearest style. */
const LOOK_TO_STYLE: Record<CutawayLook, CutawayStyleName> = {
  glass: "night",
  flat_dark: "night",
  flat_light: "daylight",
  flat_editorial: "press",
};

/** Tone is the brief's voice; it picks the press recipe when nothing else does. */
const TONE_TO_STYLE: Record<CutawayTone, CutawayStyleName> = {
  tactile: "thermal",
  editorial: "press",
  technical: "cyanotype",
  playful: "press",
  serious: "darkroom",
};

/** Each family's home style, used when the brief says nothing. */
const FAMILY_TO_STYLE: Record<CutawayFamily, CutawayStyleName> = {
  document: "thermal",
  evidence: "darkroom",
  system_map: "press",
  flow: "night",
  kinetic_type: "press",
  comparison: "press",
  sequence: "night",
  minimal: "night",
};

/**
 * Resolution order: explicit style → legacy look → tone → family home style.
 * Families call this once and read every colour and face from the result.
 */
export function resolveStyle(
  cutaway: TimelineCutaway,
  family?: CutawayFamily,
): CutawayStyleTokens {
  const explicit = cutaway.style && CUTAWAY_STYLES[cutaway.style];
  if (explicit) return explicit;
  if (cutaway.look) return CUTAWAY_STYLES[LOOK_TO_STYLE[cutaway.look]];
  if (cutaway.tone) return CUTAWAY_STYLES[TONE_TO_STYLE[cutaway.tone]];
  if (family) return CUTAWAY_STYLES[FAMILY_TO_STYLE[family]];
  return CUTAWAY_STYLES.press;
}

/**
 * One type ramp for every family, in fractions of frame height, so a kicker in
 * the receipt is the same size as a kicker in the poster.
 */
export function typeScale(height: number) {
  const px = (f: number) => Math.round(height * f);
  return {
    micro: px(0.016),
    small: px(0.019),
    body: px(0.027),
    lead: px(0.034),
    title: px(0.062),
    hero: px(0.082),
    figure: px(0.12),
  };
}

/** Letterspacing for the small-caps annotation voice shared across families. */
export const ANNOTATION_TRACKING = "0.3em";

/** Stamp geometry: families vary position and label, never the mark language. */
export function stampStyle(
  s: CutawayStyleTokens,
  height: number,
  opts: { ink?: string; rotate?: number; weight?: number } = {},
): React.CSSProperties {
  const ink = opts.ink ?? s.spot;
  const weight = opts.weight ?? 5;
  return {
    padding: `${Math.round(height * 0.015)}px ${Math.round(height * 0.024)}px`,
    border: `${weight}px solid ${ink}`,
    outline: `2px solid ${ink}`,
    outlineOffset: Math.round(weight),
    color: ink,
    fontFamily: s.mono,
    fontWeight: 700,
    fontSize: Math.round(height * 0.03),
    letterSpacing: "0.14em",
    textTransform: "uppercase",
    mixBlendMode: s.chrome ? "normal" : "multiply",
    transform: `rotate(${opts.rotate ?? -8}deg)`,
  };
}

/** A struck-out line drawn in the spot ink; used for refusals and denials. */
export function strikeStyle(
  s: CutawayStyleTokens,
  height: number,
  progress: number,
): React.CSSProperties {
  return {
    position: "absolute",
    left: -12,
    right: -12,
    top: "52%",
    height: Math.max(4, Math.round(height * 0.009)),
    background: s.reject,
    mixBlendMode: s.chrome ? "normal" : "multiply",
    transform: `scaleX(${progress}) rotate(-1.6deg)`,
    transformOrigin: "left center",
  };
}

/** LedgerFlow still speaks the old `Look` shape; keep it fed from tokens. */
export function lookFromStyle(s: CutawayStyleTokens) {
  return {
    background: s.plate,
    plate: s.plate,
    grid: s.name === "night",
    ink: s.onPlate,
    dim: s.onPlateSoft,
    wire: s.spot,
    fill: s.chrome ? s.spotSoft : s.spot,
    onFill: s.chrome ? s.spot : s.paper,
    plus: s.spot,
    minus: s.onPlateSoft,
    card: s.chrome ? s.paper : "transparent",
    cardBorder: s.paperEdge,
    cardShadow: s.chrome ? `0 40px 80px ${s.paperEdge}` : "none",
    row: s.chrome ? s.paper : "transparent",
    divider: s.paperEdge,
    radius: s.radius,
    chrome: s.chrome,
    reject: s.reject,
  };
}
