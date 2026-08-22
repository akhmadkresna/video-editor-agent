export type Framing = "wide" | "medium" | "close";
export type FramingMotion =
  | "hold"
  | "snap"
  | "ease"
  | "ease_in"
  | "ease_out"
  | "drift"
  | "pull_back";

export type ClipLayout =
  | "full"
  | "float_centered"
  | "pip_corner"
  | "stack_top"
  | "stack_bottom";

export type WindowCropNorm = {
  x: number;
  y: number;
  w: number;
  h: number;
};

export type TimelineClip = {
  id: string;
  track: string;
  source: string;
  sourceIn: number;
  sourceOut: number;
  fromSec: number;
  durationSec: number;
  layout: ClipLayout;
  framing: Framing;
  scale: number;
  motion: FramingMotion;
  /** When true (or source !== cam), clip is silent — audio always from cam. */
  muted?: boolean;
  /** Normalized smart-window crop (0–1 of source frame). */
  windowCrop?: WindowCropNorm;
};

export type PunchEffect = {
  type: "punch_in" | "punch_out";
  fromSec: number;
  durationSec: number;
  scale: number;
};

export type Caption = {
  text: string;
  start: number;
  end: number;
  style?: "plain" | "karaoke";
  words?: Array<{
    text: string;
    start: number;
    end: number;
  }>;
};

export type OverlayKind =
  | "chapter"
  | "emphasis"
  | "diagram"
  | "chip"
  | "callout"
  // "Glass" house style (2026-08) — frosted overlay-on-continuous-A-roll,
  // not a picture-takeover. See components/glass/. Content mapping (reuses
  // existing whitelisted TimelineOverlay fields, no remap.py changes needed):
  //   title       -> text (+ optional kicker)
  //   stat        -> value + sourceLabel (+ optional title = descriptor)
  //   lower_third -> text (name) + title (role) + steps (tag badges)
  //   tag         -> text (standalone floating chip)
  //   divider     -> kicker ("CHAPTER 01") + title (heading)
  //   quote       -> text (quote body) + kicker (attribution)
  //   code        -> steps (code lines) + kicker (label)
  //   illustration-> title (heading) + steps (labels/values) +
  //                  note: "illustration:<id>" selects the bespoke diagram
  //                  (dual_timeline | scale_compare | spec_gap | car_no_map |
  //                  compass | load_test | stadium_ticket)
  | "title"
  | "stat"
  | "lower_third"
  | "tag"
  | "divider"
  | "quote"
  | "code"
  | "illustration";

export type SfxKind = "typing" | "shutter" | "click";

export type TimelineOverlay = {
  id: string;
  kind: OverlayKind;
  fromSec: number;
  durationSec: number;
  text?: string;
  kicker?: string;
  title?: string;
  steps?: string[];
  /** Callout big number (e.g. Rp24 jt). */
  value?: string;
  /** Callout estimator source (e.g. SocialCounts). */
  sourceLabel?: string;
  /** Seconds relative to overlay start when each diagram step should appear. */
  stepAtSec?: number[];
  /** `speech` = transcript-aligned; `even` = paced fallback; `manual` = cover stepStarts. */
  stepMotion?: "speech" | "even" | "manual";
  /** Local second when fade-out begins (after list hold). */
  exitStartSec?: number;
  note?: string;
  /** "glass" kinds only — teal (info/positive) | amber (caution/estimate) |
   * neutral. Drives StatCallout's mono-badge border style (dashed = amber). */
  tone?: "teal" | "amber" | "neutral";
  /** `title` kind only — second-color headline continuation, e.g.
   * text="Kalau ngoding udah gampang," accent="kita dibayar buat apa?" */
  accent?: string;
};

/** Generated MG cutaway scenes (picture takeover; cam VO keeps playing). */
/** @deprecated Prefer CutawayFamily; kept as Remotion component keys / aliases. */
export type CutawayScene =
  | "ledger_flow"
  | "receipt_tape"
  | "kinetic_figures"
  | "blueprint_nodes"
  | "evidence"
  | "minimal";

/**
 * Family id = Sequence / QA label. Every brief renders through InterfaceStage;
 * board layout is inferred from the data (catalog / ledger / access / shot).
 */
export type CutawayFamily =
  | "document"
  | "flow"
  | "kinetic_type"
  | "comparison"
  | "sequence"
  | "system_map"
  | "evidence"
  | "minimal";

export type CutawayIntent =
  | "explain"
  | "compare"
  | "accumulate"
  | "transform"
  | "sequence"
  | "prove"
  | "warn"
  | "summarize";

export type CutawayTone =
  | "technical"
  | "editorial"
  | "tactile"
  | "playful"
  | "serious";

export type CutawayBeatKind =
  | "reveal"
  | "connect"
  | "update"
  | "reject"
  | "resolve"
  | "open"
  | "classify"
  | "total"
  | "lock"
  | "stamp";

/**
 * Print recipe shared by every family: stock, inks, type and mark language.
 * See `components/cutaway/style.ts` for the tokens behind each name.
 */
export type CutawayStyleName =
  | "press"
  | "thermal"
  | "darkroom"
  | "cyanotype"
  | "night"
  | "daylight";

/** @deprecated Superseded by `style`; kept so older covers still render. */
export type CutawayLook =
  | "glass"
  | "flat_light"
  | "flat_dark"
  | "flat_editorial";

/** Framework vector glyph set — drawn in code, tinted by the look. */
export type CutawayGlyph =
  | "cart"
  | "bag"
  | "receipt"
  | "wallet"
  | "chart"
  | "lock";

/** What sits behind the scene elements. */
export type CutawayBackdrop = {
  /** plate = opaque look background; cam_blur = blurred footage under it. */
  kind: "plate" | "cam_blur" | "image";
  /** Staged public path (ae-media/...) for image backdrops and mockups. */
  src?: string;
  blurPx?: number;
  /** 0–1 wash over the backdrop so elements stay readable. */
  dim?: number;
  /** Overscan so blur edges never show. */
  scale?: number;
};

/** Staged image asset (screen crop, logo, photo) used as visual proof. */
export type CutawayAsset = {
  src: string;
  caption?: string;
  /** How the asset participates in the scene. */
  role?: "hero" | "proof" | "texture" | "annotation";
  /** Episode-relative or absolute origin before staging. */
  provenance?: string;
  /** Detail worth magnifying: 0–1 fractions of the image plus a zoom factor. */
  focus?: { x: number; y: number; zoom?: number };
};

/** Verdict polarity for non-numeric stories (access, checks, pass/fail). */
export type CutawayState = "allow" | "deny" | "neutral";

export type CutawayFeed = {
  label: string;
  /** Signed amount (e.g. rupiah); optional for non-numeric entities. */
  amount?: number;
  /** Local second (relative to cutaway start) when this feed fires. */
  atSec: number;
  icon?: CutawayGlyph;
  unit?: string;
  state?: CutawayState;
  /** Hotspot on the UI stage (0–1). Camera punches here when this entity lands. */
  focus?: { x: number; y: number; zoom?: number };
};

/** Neutral entity in a VisualBrief (timeline-local after remap). */
export type CutawayEntity = {
  id?: string;
  label: string;
  value?: number;
  unit?: string;
  atSec: number;
  icon?: CutawayGlyph;
  asset?: CutawayAsset;
  state?: CutawayState;
  /** Hotspot on the UI stage (0–1). Camera punches here when this entity lands. */
  focus?: { x: number; y: number; zoom?: number };
};

export type CutawayBeat = {
  kind: CutawayBeatKind;
  atSec: number;
  label?: string;
};

export type CutawayCopy = {
  kicker?: string;
  title?: string;
  openingLabel?: string;
  totalLabel?: string;
  /** Small print under the document (journal no., source system). */
  footerLabel?: string;
  lockLabel?: string;
  stampLabel?: string;
  attemptLabels?: string[];
  inLabel?: string;
  outLabel?: string;
};

export type TimelineCutaway = {
  id: string;
  /** @deprecated Prefer family; still used as Remotion component key. */
  scene: CutawayScene;
  /** Canonical motion family. */
  family?: CutawayFamily;
  intent?: CutawayIntent;
  tone?: CutawayTone;
  fromSec: number;
  durationSec: number;
  /** Print recipe; overrides the tone/family default. */
  style?: CutawayStyleName;
  /** @deprecated Prefer style. */
  look?: CutawayLook;
  backdrop?: CutawayBackdrop;
  /** Real screenshot/asset shown inside the scene as proof. */
  proof?: CutawayAsset;
  assets?: CutawayAsset[];
  copy?: CutawayCopy;
  /** @deprecated Prefer copy.kicker */
  kicker?: string;
  /** @deprecated Prefer copy.title */
  title?: string;
  /** Opening total when the story accumulates values. */
  openingBalance?: number;
  /** @deprecated Prefer entities */
  feeds?: CutawayFeed[];
  entities?: CutawayEntity[];
  beats?: CutawayBeat[];
  /** Local seconds for scene beats — word-snapped upstream. Legacy names. */
  cues?: {
    ledgerInSec?: number;
    inOutSec?: number;
    balanceSec?: number;
    lockSec?: number;
    /** Rejected edit/delete attempts. */
    attemptSec?: number[];
    stampSec?: number;
    openSec?: number;
    classifySec?: number;
    totalSec?: number;
    rejectSec?: number[];
    resolveSec?: number;
  };
  inLabel?: string;
  outLabel?: string;
  lockLabel?: string;
  attemptLabels?: string[];
  stampLabel?: string;
  balanceLabel?: string;
  note?: string;
};

/** Additive SFX under cam VO (output time after EDL remap). */
export type TimelineSfx = {
  id: string;
  kind: SfxKind;
  fromSec: number;
  durationSec: number;
  /** Staged path under public/, e.g. ae-media/sfx/shutter.mp3 */
  src: string;
  volume: number;
  /** When true, Remotion tiles the clip across durationSec (typing). */
  tile?: boolean;
  note?: string;
};

export type ScreenExplainerStyle = {
  preset?: string;
  canvas?: {
    background?: string;
    backgroundDeep?: string;
    gradient?: string;
  };
  screen?: {
    presentation?: string;
    widthRatio?: number;
    maxHeightRatio?: number;
    /** Portrait only: fraction of frame height from top to the screen card. */
    topRatio?: number;
    borderRadiusPx?: number;
    /** width/height of screen.mp4 — card fits this AR (no distort). */
    aspectRatio?: number;
    objectFit?: string;
    crop?: {
      mode?: "none" | "smart_window_detect";
    };
  };
  pip?: {
    anchor?: string;
    widthRatio?: number;
    /** Stacked portrait: fraction of frame height for the host half. */
    heightRatio?: number;
    aspectRatio?: string;
    insetRightRatio?: number;
    insetLeftRatio?: number;
    insetBottomRatio?: number;
    borderRadiusPx?: number;
    border?: string;
    objectFit?: string;
    objectPosition?: string;
  };
};

/** Locked A-roll MG (mirror styles/tutorial): white ink straight on the
 * a-roll, no panel, no accent color — readability from the veil scrim,
 * not a surface. One look, shared by every kind and every style pack. */
export type OverlayStyle = {
  preset?: string;
  treatment?: "bold";
  ink?: string;
  dim?: string;
  fonts?: { display?: string; ui?: string };
  chapter?: {
    leftCqw?: number;
    topCqh?: number;
    maxWidthCqw?: number;
    kickerSizeCqh?: number;
    titleSizeCqh?: number;
  };
  emphasis?: {
    leftCqw?: number;
    bottomCqh?: number;
    /** When set, pin to top (letterbox top bar) instead of bottom. */
    topCqh?: number;
    sizeCqh?: number;
    maxWidthCqw?: number;
    underline?: boolean;
  };
  diagram?: {
    leftCqw?: number;
    topCqh?: number;
    maxWidthCqw?: number;
    stepSizeCqh?: number;
  };
  callout?: {
    leftCqw?: number;
    bottomCqh?: number;
    /** When set, pin to top (letterbox top bar) instead of bottom. */
    topCqh?: number;
    valueSizeCqh?: number;
    sourceSizeCqh?: number;
    maxWidthCqw?: number;
  };
  chip?: {
    leftCqw?: number;
    topCqh?: number;
    sizeCqh?: number;
  };
};

export const DEFAULT_OVERLAY_STYLE: OverlayStyle = {
  preset: "open_overlay",
  treatment: "bold",
  ink: "#ffffff",
  dim: "rgba(255,255,255,0.55)",
  fonts: {
    display: "Syne",
    ui: "Instrument Sans",
  },
  chapter: { leftCqw: 4.5, topCqh: 12, maxWidthCqw: 42 },
  emphasis: { leftCqw: 4.5, bottomCqh: 28, sizeCqh: 16, underline: true },
  diagram: { leftCqw: 4.5, topCqh: 10, maxWidthCqw: 40 },
  callout: {
    leftCqw: 4.5,
    bottomCqh: 22,
    valueSizeCqh: 14,
    sourceSizeCqh: 2.8,
    maxWidthCqw: 48,
  },
  chip: { leftCqw: 4.5, topCqh: 10, sizeCqh: 3.4 },
};

/** Persistent call-to-action badge (social profile). */
export type CtaBadgeStyle = {
  enabled?: boolean;
  text?: string;
  blink?: boolean;
  blinkPeriodSec?: number;
  /** band_top_center = sit on the letterbox 16:9 stage (Option A). */
  anchor?: "top_center" | "top_left" | "band_top_center";
  topCqh?: number;
  /** Inset from the top edge of the 16:9 band when anchor is band_top_center. */
  bandTopCqh?: number;
  sizeCqh?: number;
};

export type Timeline = {
  fps: number;
  width: number;
  height: number;
  durationInFrames: number;
  durationSec: number;
  sources: Record<string, string>;
  clips: TimelineClip[];
  effects: PunchEffect[];
  captions: Caption[];
  overlays?: TimelineOverlay[];
  cutaways?: TimelineCutaway[];
  sfx?: TimelineSfx[];
  presentation?: {
    screenExplainer?: ScreenExplainerStyle;
    overlays?: OverlayStyle;
    profile?: "tutorial" | "evidence" | "social";
    captions?: {
      style?: "off" | "plain" | "karaoke";
      accent?: string;
      safeBottomRatio?: number;
    };
    cta?: CtaBadgeStyle;
  };
};

export type TimelineProps = {
  timeline: Timeline;
};

export const emptyTimeline: Timeline = {
  fps: 30,
  width: 1920,
  height: 1080,
  durationInFrames: 90,
  durationSec: 3,
  sources: {},
  clips: [],
  effects: [],
  captions: [],
  overlays: [],
  cutaways: [],
  sfx: [],
};

/** Locked cozy + cool mist defaults (mirror styles/tutorial). */
export const DEFAULT_SCREEN_EXPLAINER: ScreenExplainerStyle = {
  preset: "cozy",
  canvas: {
    background: "#d9e2ec",
    backgroundDeep: "#c4d0dc",
    gradient: "radial",
  },
  screen: {
    presentation: "float_centered",
    widthRatio: 0.78,
    maxHeightRatio: 0.82,
    borderRadiusPx: 24,
    objectFit: "fill",
    crop: { mode: "none" },
  },
  pip: {
    anchor: "stage_lower_right",
    widthRatio: 0.18,
    aspectRatio: "5:6",
    insetRightRatio: 0.035,
    insetBottomRatio: 0.045,
    borderRadiusPx: 26,
    border: "none",
    objectFit: "cover",
    objectPosition: "center 28%",
  },
};
