import { z } from "zod";

export const AsrConfigSchema = z.object({
  backend: z.enum(["auto", "whisper.cpp", "faster-whisper"]).default("auto"),
  model: z.string().default("small"),
  language: z.string().default("id"),
  word_timestamps: z.boolean().default(true),
  diarize: z.boolean().default(false),
});

export const ProjectSchema = z.object({
  id: z.string(),
  sources: z.record(z.string()).default({ cam: "raw/cam.mp4" }),
  style: z.string().default("tutorial"),
  asr: AsrConfigSchema.default({}),
  fps: z.number().int().positive().default(30),
  aspect: z.string().default("16:9"),
  width: z.number().int().positive().default(1920),
  height: z.number().int().positive().default(1080),
});

export const TranscriptWordSchema = z.object({
  type: z.string().optional(),
  word: z.string().optional(),
  text: z.string().optional(),
  start: z.number(),
  end: z.number(),
  score: z.number().optional(),
  speaker_id: z.union([z.string(), z.number()]).optional(),
});

export const TranscriptSchema = z.object({
  language: z.string(),
  backend: z.string(),
  model: z.string(),
  words: z.array(TranscriptWordSchema),
  segments: z
    .array(
      z.object({
        start: z.number(),
        end: z.number(),
        text: z.string(),
      }),
    )
    .default([]),
});

export const EdlRangeSchema = z.object({
  source: z.string(),
  start: z.number(),
  end: z.number(),
  note: z.string().optional(),
  beat: z.string().optional(),
});

export const EdlSchema = z.object({
  sources: z.record(z.string()),
  ranges: z.array(EdlRangeSchema).min(1),
  grade: z.string().nullable().optional(),
});

/** Fake 2–3 cam framing presets (single source, digital crop). */
export const FramingSchema = z.enum(["wide", "medium", "close"]);
export const FramingMotionSchema = z.enum([
  "hold",
  "snap",
  "ease",
  "ease_in",
  "ease_out",
  "drift",
]);

export const CoverEventSchema = z.object({
  type: z.enum([
    "screen",
    "screen_full",
    "screen_with_cam",
    "cam_pip",
    "pip",
    "screen_pip",
    "evidence",
    "evidence_with_cam",
    "punch_in",
    "punch",
    "punch_out",
    "framing",
  ]),
  source: z.string().optional(),
  /** Overlay source for screen_with_cam (default cam). */
  pip_source: z.string().optional(),
  /**
   * Evidence still filename or relative path under raw/evidence/ (or edit/evidence/).
   * Required for evidence / evidence_with_cam.
   */
  src: z.string().optional(),
  /** Evidence layout: float (cozy canvas) or full bleed. */
  layout: z.enum(["float", "full"]).optional(),
  start: z.number(),
  end: z.number(),
  duration: z.number().optional(),
  scale: z.number().optional(),
  framing: FramingSchema.optional(),
  motion: FramingMotionSchema.optional(),
  note: z.string().optional(),
});

/** A-roll MG creatives (source-time). Locked look: Bold + cool mist. */
export const OverlayKindSchema = z.enum([
  "chapter",
  "emphasis",
  "diagram",
  "chip",
  "callout",
]);

export const CoverOverlaySchema = z.object({
  id: z.string().optional(),
  kind: OverlayKindSchema,
  start: z.number(),
  end: z.number(),
  source: z.string().default("cam"),
  text: z.string().optional(),
  kicker: z.string().optional(),
  title: z.string().optional(),
  steps: z.array(z.string()).optional(),
  /** Callout: big value line (e.g. Rp24 jt). */
  value: z.string().optional(),
  /** Callout: estimator source label (e.g. SocialCounts). */
  sourceLabel: z.string().optional(),
  note: z.string().optional(),
});

/** Generated MG cutaway scenes (picture takeover under cam VO), source-time. */
export const CutawaySceneSchema = z.enum(["ledger_flow"]);

export const CutawayFeedSchema = z.object({
  label: z.string(),
  /** Signed rupiah amount. */
  amount: z.number(),
  /** Cam source second when this feed fires (word-snapped). */
  at: z.number(),
});

export const CoverCutawaySchema = z.object({
  id: z.string().optional(),
  scene: CutawaySceneSchema,
  start: z.number(),
  end: z.number(),
  source: z.string().default("cam"),
  kicker: z.string().optional(),
  title: z.string().optional(),
  openingBalance: z.number().optional(),
  feeds: z.array(CutawayFeedSchema).optional(),
  /** Scene beats in cam source seconds. */
  cues: z
    .object({
      ledgerIn: z.number().optional(),
      inOut: z.number().optional(),
      balance: z.number().optional(),
      lock: z.number().optional(),
      attempts: z.array(z.number()).optional(),
      stamp: z.number().optional(),
    })
    .optional(),
  inLabel: z.string().optional(),
  outLabel: z.string().optional(),
  lockLabel: z.string().optional(),
  attemptLabels: z.array(z.string()).optional(),
  stampLabel: z.string().optional(),
  balanceLabel: z.string().optional(),
  note: z.string().optional(),
});

/** Modern-tech SFX under cam VO — no whoosh. Source-time on cover. */
export const SfxKindSchema = z.enum(["typing", "shutter", "click"]);

export const CoverSfxSchema = z.object({
  id: z.string().optional(),
  kind: SfxKindSchema,
  start: z.number(),
  /** Required for typing holds; optional for one-shots (defaults short). */
  end: z.number().optional(),
  src: z.string().optional(),
  bank: z.string().optional(),
  volume: z.number().optional(),
  note: z.string().optional(),
});

export const CameraPlaySchema = z.object({
  /** Alternate home/alt framing at each EDL join when no framing event wins. */
  snap_on_cuts: z.boolean().default(true),
  home: FramingSchema.default("medium"),
  alt: FramingSchema.default("close"),
  /** Use wide on topic-reset beats (notes containing reset/lesson/howto/outro). */
  wide_on_resets: z.boolean().default(true),
  scales: z
    .object({
      wide: z.number().default(1.0),
      medium: z.number().default(1.1),
      close: z.number().default(1.18),
    })
    .default({}),
});

export const CoverSchema = z.object({
  camera_play: CameraPlaySchema.default({}),
  events: z.array(CoverEventSchema).default([]),
  /** Sparse MG creatives in cam source time — confirm before write. */
  overlays: z.array(CoverOverlaySchema).default([]),
  /** Generated MG cutaway scenes in cam source time — confirm before write. */
  cutaways: z.array(CoverCutawaySchema).default([]),
  /** Additive SFX under cam VO (source-time). */
  sfx: z.array(CoverSfxSchema).default([]),
  captions: z
    .array(
      z.object({
        text: z.string(),
        start: z.number(),
        end: z.number(),
        style: z.enum(["plain", "karaoke"]).optional(),
        words: z
          .array(
            z.object({
              text: z.string(),
              start: z.number(),
              end: z.number(),
            }),
          )
          .optional(),
      }),
    )
    .default([]),
});

export const WindowCropNormSchema = z.object({
  x: z.number(),
  y: z.number(),
  w: z.number(),
  h: z.number(),
});

export const TimelineClipSchema = z.object({
  id: z.string(),
  track: z.string(),
  source: z.string(),
  sourceIn: z.number(),
  sourceOut: z.number(),
  fromSec: z.number(),
  durationSec: z.number(),
  layout: z
    .enum([
      "full",
      "float_centered",
      "pip_corner",
      "stack_top",
      "stack_bottom",
    ])
    .default("full"),
  framing: FramingSchema.default("medium"),
  scale: z.number().default(1),
  motion: FramingMotionSchema.default("snap"),
  /** When true, Remotion plays the clip silent. Audio always comes from cam. */
  muted: z.boolean().optional(),
  /** Normalized smart-window crop (0–1 of source frame). */
  windowCrop: WindowCropNormSchema.optional(),
});

export const ScreenExplainerSchema = z.object({
  preset: z.string().optional(),
  canvas: z
    .object({
      background: z.string().optional(),
      backgroundDeep: z.string().optional(),
      gradient: z.string().optional(),
    })
    .optional(),
  screen: z.record(z.unknown()).optional(),
  pip: z.record(z.unknown()).optional(),
});

export const OverlayStyleSchema = z.object({
  preset: z.string().optional(),
  treatment: z.string().optional(),
  accent: z.string().optional(),
  accentName: z.string().optional(),
  ink: z.string().optional(),
  dim: z.string().optional(),
  fonts: z
    .object({
      display: z.string().optional(),
      ui: z.string().optional(),
    })
    .optional(),
});

/** Output-timeline MG instance (after EDL remap). */
export const TimelineOverlaySchema = z.object({
  id: z.string(),
  kind: OverlayKindSchema,
  fromSec: z.number(),
  durationSec: z.number(),
  text: z.string().optional(),
  kicker: z.string().optional(),
  title: z.string().optional(),
  steps: z.array(z.string()).optional(),
  note: z.string().optional(),
});

/** Output-timeline SFX (after EDL remap). src is staged under ae-media/sfx/. */
export const TimelineSfxSchema = z.object({
  id: z.string(),
  kind: SfxKindSchema,
  fromSec: z.number(),
  durationSec: z.number(),
  src: z.string(),
  volume: z.number().default(0.4),
  tile: z.boolean().optional(),
  note: z.string().optional(),
});

export const TimelineSchema = z.object({
  fps: z.number(),
  width: z.number(),
  height: z.number(),
  durationInFrames: z.number(),
  durationSec: z.number(),
  sources: z.record(z.string()),
  clips: z.array(TimelineClipSchema),
  effects: z
    .array(
      z.object({
        type: z.enum(["punch_in", "punch_out"]),
        fromSec: z.number(),
        durationSec: z.number(),
        scale: z.number().default(1.15),
      }),
    )
    .default([]),
  captions: z
    .array(
      z.object({
        text: z.string(),
        start: z.number(),
        end: z.number(),
      }),
    )
    .default([]),
  overlays: z.array(TimelineOverlaySchema).default([]),
  cutaways: z
    .array(
      z.object({
        id: z.string(),
        scene: CutawaySceneSchema,
        fromSec: z.number(),
        durationSec: z.number(),
        kicker: z.string().optional(),
        title: z.string().optional(),
        openingBalance: z.number().optional(),
        feeds: z
          .array(
            z.object({
              label: z.string(),
              amount: z.number(),
              atSec: z.number(),
            }),
          )
          .optional(),
        cues: z
          .object({
            ledgerInSec: z.number().optional(),
            inOutSec: z.number().optional(),
            balanceSec: z.number().optional(),
            lockSec: z.number().optional(),
            attemptSec: z.array(z.number()).optional(),
            stampSec: z.number().optional(),
          })
          .optional(),
        inLabel: z.string().optional(),
        outLabel: z.string().optional(),
        lockLabel: z.string().optional(),
        attemptLabels: z.array(z.string()).optional(),
        stampLabel: z.string().optional(),
        balanceLabel: z.string().optional(),
        note: z.string().optional(),
      }),
    )
    .default([]),
  sfx: z.array(TimelineSfxSchema).default([]),
  presentation: z
    .object({
      screenExplainer: ScreenExplainerSchema.optional(),
      overlays: OverlayStyleSchema.optional(),
      profile: z.enum(["tutorial", "evidence", "social"]).optional(),
      captions: z
        .object({
          style: z.enum(["off", "plain", "karaoke"]).optional(),
          accent: z.string().optional(),
          safeBottomRatio: z.number().optional(),
        })
        .optional(),
      cta: z
        .object({
          enabled: z.boolean().optional(),
          text: z.string().optional(),
          blink: z.boolean().optional(),
          blinkPeriodSec: z.number().optional(),
          anchor: z.enum(["top_center", "top_left"]).optional(),
          topCqh: z.number().optional(),
          sizeCqh: z.number().optional(),
        })
        .optional(),
    })
    .optional(),
});

export type Project = z.infer<typeof ProjectSchema>;
export type Transcript = z.infer<typeof TranscriptSchema>;
export type Edl = z.infer<typeof EdlSchema>;
export type Cover = z.infer<typeof CoverSchema>;
export type Timeline = z.infer<typeof TimelineSchema>;
export type Framing = z.infer<typeof FramingSchema>;
export type FramingMotion = z.infer<typeof FramingMotionSchema>;
export type CoverOverlay = z.infer<typeof CoverOverlaySchema>;
export type TimelineOverlay = z.infer<typeof TimelineOverlaySchema>;
export type CoverSfx = z.infer<typeof CoverSfxSchema>;
export type TimelineSfx = z.infer<typeof TimelineSfxSchema>;
export type SfxKind = z.infer<typeof SfxKindSchema>;
