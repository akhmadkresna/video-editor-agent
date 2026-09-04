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

/** Normalized rect as percent of frame (0–100). */
export type PrivacyRect = {
  x: number;
  y: number;
  w: number;
  h: number;
};

/** Solid privacy bars over secrets (client ID / secret / tokens). */
export type TimelinePrivacy = {
  id: string;
  fromSec: number;
  durationSec: number;
  rects: PrivacyRect[];
  /** v1: solid bar or full-window frosted blur. */
  mode?: "bar" | "screen_blur";
  label?: string;
  note?: string;
};

/** Face-clear surround zones for A-roll MG (middle-ground Open Overlay). */
export type OverlayZone =
  | "left_third"
  | "right_third"
  | "lower_raised"
  | "top_sparse";

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
  /** Surround placement around the speaker; face oval stays clear. */
  zone?: OverlayZone;
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

// ───────────────────────── Mockup scenes (Skill Lab) ─────────────────────────
// The "drawn screen": a Remotion mock that stands in for a screen recording.
// Full-frame between talking-head beats; cam PIP composites on top (a
// pip_corner clip added by compose). MG overlays render above. See
// styles/series/claude-skill-lab/mockup-system.md.

export type MockChrome = "claude" | "app" | "browser" | "none";
export type MockCamState = "establish" | "read" | "focus";
export type MockReveal = "instant" | "type" | "stream";

/** One virtual-camera keyframe. `atSec` is scene-local. */
export type MockCamKeyframe = {
  atSec: number;
  state: MockCamState;
  /** Focus region name: chat.input | chat.caret | chat.turn.assistant |
   *  chat.turn.N | diff.before | diff.after | app.window. */
  focus?: string;
  /** Explicit focus point (0–1 of the stage) — fallback when no region. */
  focusPoint?: [number, number];
  /** Per-frame trailing follow of a live region. */
  track?: "caret" | "cursor";
};

export type MockAttachment = { name: string; kind?: string };
export type MockToolBlock = { label?: string; lines: string[] };

export type MockTurn = {
  role: "user" | "assistant";
  text: string;
  reveal?: MockReveal;
  /** Scene-local seconds this turn starts appearing; auto-sequenced if absent. */
  atSec?: number;
  /** "▸ Pakai skill · avoid-ai-writing" pill shown before an assistant turn. */
  skillBadge?: string;
  attachments?: MockAttachment[];
  toolBlock?: MockToolBlock;
};

export type MockDiffMark = { type: "add" | "del"; span: [number, number] };

export type MockCursorWaypoint = {
  atSec: number;
  target?: string;
  point?: [number, number];
  action?: "move" | "hover" | "click";
  dwell?: number;
};

export type MockLayer =
  | { component: "ClaudeChat"; data: { turns: MockTurn[]; typeCps?: number } }
  | {
      component: "DiffPanel";
      data: {
        before: string;
        after: string;
        beforeMarks?: MockDiffMark[];
        afterMarks?: MockDiffMark[];
        atSec?: number;
      };
    }
  | { component: "Cursor"; data: { path: MockCursorWaypoint[] } }
  | {
      component: "AppWindow";
      data: { app: string; content?: string; src?: string; atSec?: number };
    }
  | {
      component: "SkillsPanel";
      data: {
        skills: Array<{ name: string; source?: string; on: boolean }>;
        action?: string;
        atSec?: number;
      };
    }
  | {
      component: "RepoView";
      data: {
        repoUrl: string;
        repo?: string;
        path?: string;
        source?: string;
        /** real SKILL.md text (fetched by `ae mockup-suggest`) */
        markdown: string;
        scroll?: boolean;
        atSec?: number;
      };
    };

export type TimelineMockScene = {
  id: string;
  fromSec: number;
  durationSec: number;
  stage: { title?: string; chrome?: MockChrome };
  camera?: MockCamKeyframe[];
  layers: MockLayer[];
  /** Dissolve against cam, seconds (default 0.35). */
  in?: number;
  out?: number;
};

export type MockCamConfig = {
  easeMs: number;
  holdMinSec: number;
  scales: { establish: number; read: number; focus: number };
  maxScale: number;
  /** 0–1: trailing-follow lag is (0.55 - followGain*0.4)s. Lower = looser. */
  followGain: number;
  settleAfterRead: boolean;
  intensity: "calm" | "standard";
};

/** Mist theme — mock surfaces only. MG overlay tokens stay in glass/tokens.ts.
 *  The stage always renders light: it is a screen, not a themed document. */
export type MockStyle = {
  stageBg: string;
  window: string;
  windowBorder: string;
  windowShadow: string;
  rail: string;
  railLine: string;
  chromeTitle: string;
  chromeDot: string;
  userBubble: string;
  userInk: string;
  asstInk: string;
  badgeBg: string;
  badgeInk: string;
  chipBorder: string;
  chipInk: string;
  inputBg: string;
  inputInk: string;
  caret: string;
  cursor: string;
  pipGradient: string;
  pipRing: string;
  diffDel: string;
  diffAdd: string;
  cam: MockCamConfig;
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
  /** Size bands (cqh): hero / body / meta — moderate hierarchy. */
  sizeBands?: {
    heroCqh?: number;
    bodyCqh?: number;
    metaCqh?: number;
  };
  /** Max primary + secondary lines on screen (density cap). */
  density?: {
    maxPrimary?: number;
    maxSecondary?: number;
  };
  chapter?: {
    leftCqw?: number;
    rightCqw?: number;
    topCqh?: number;
    maxWidthCqw?: number;
    kickerSizeCqh?: number;
    titleSizeCqh?: number;
  };
  emphasis?: {
    leftCqw?: number;
    rightCqw?: number;
    bottomCqh?: number;
    /** When set, pin to top (letterbox top bar) instead of bottom. */
    topCqh?: number;
    sizeCqh?: number;
    maxWidthCqw?: number;
    underline?: boolean;
  };
  diagram?: {
    leftCqw?: number;
    rightCqw?: number;
    topCqh?: number;
    maxWidthCqw?: number;
    stepSizeCqh?: number;
  };
  callout?: {
    leftCqw?: number;
    rightCqw?: number;
    bottomCqh?: number;
    /** When set, pin to top (letterbox top bar) instead of bottom. */
    topCqh?: number;
    valueSizeCqh?: number;
    sourceSizeCqh?: number;
    maxWidthCqw?: number;
  };
  chip?: {
    leftCqw?: number;
    rightCqw?: number;
    topCqh?: number;
    sizeCqh?: number;
  };
  safe?: {
    faceClear?: boolean;
    zones?: OverlayZone[];
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
  sizeBands: { heroCqh: 22, bodyCqh: 9, metaCqh: 3.4 },
  density: { maxPrimary: 1, maxSecondary: 1 },
  chapter: { leftCqw: 4.5, topCqh: 12, maxWidthCqw: 42, titleSizeCqh: 12, kickerSizeCqh: 2.4 },
  emphasis: { leftCqw: 4.5, bottomCqh: 28, sizeCqh: 22, underline: true, maxWidthCqw: 48 },
  diagram: { leftCqw: 4.5, topCqh: 10, maxWidthCqw: 40 },
  callout: {
    leftCqw: 4.5,
    bottomCqh: 22,
    valueSizeCqh: 18,
    sourceSizeCqh: 2.8,
    maxWidthCqw: 48,
  },
  chip: { leftCqw: 4.5, topCqh: 10, sizeCqh: 3.4 },
  safe: {
    faceClear: true,
    zones: ["left_third", "right_third", "lower_raised", "top_sparse"],
  },
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
  /** Drawn-screen scenes (Skill Lab `style: mockup`). */
  mockups?: TimelineMockScene[];
  sfx?: TimelineSfx[];
  /** Solid bars masking on-screen credentials (EDL-remapped). */
  privacy?: TimelinePrivacy[];
  presentation?: {
    screenExplainer?: ScreenExplainerStyle;
    overlays?: OverlayStyle;
    /** Mist tokens + MockCam config (Skill Lab). */
    mockup?: MockStyle;
    profile?: "tutorial" | "evidence" | "social" | "mockup";
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
  mockups: [],
  sfx: [],
  privacy: [],
};

/** Locked "Mist" mock treatment + calm MockCam (mirror styles/mockup). */
export const DEFAULT_MOCK_STYLE: MockStyle = {
  stageBg: "#eceff1",
  window: "#fdfefe",
  windowBorder: "#dee3e6",
  windowShadow:
    "0 18px 44px -24px rgba(38,58,68,0.24), 0 2px 8px -4px rgba(38,58,68,0.10)",
  rail: "#f4f6f7",
  railLine: "#e6eaec",
  chromeTitle: "#7d878d",
  chromeDot: "#c3ccd1",
  userBubble: "#eef2f4",
  userInk: "#293136",
  asstInk: "#3a434b",
  badgeBg: "#e9eef0",
  badgeInk: "#496573",
  chipBorder: "#d8dfe2",
  chipInk: "#79848b",
  inputBg: "#f1f4f5",
  inputInk: "#98a2a8",
  caret: "#496573",
  cursor: "#2f3a40",
  pipGradient: "linear-gradient(150deg, #ccd5da, #a4b2ba)",
  pipRing: "rgba(255,255,255,0.60)",
  diffDel: "#b1566b",
  diffAdd: "#5c8a68",
  cam: {
    easeMs: 420,
    holdMinSec: 1.2,
    scales: { establish: 1.0, read: 1.2, focus: 1.45 },
    maxScale: 1.6,
    followGain: 0.12,
    settleAfterRead: true,
    intensity: "calm",
  },
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
