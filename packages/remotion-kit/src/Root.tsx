import React from "react";
import { Composition, getInputProps } from "remotion";
import { AgenticTimeline } from "./Composition";
import { CutawayLab, LAB_CUTAWAY } from "./CutawayLab";
import { MockupLab, LAB_MOCK_SCENES } from "./MockupLab";
import { LAB_OVERLAYS, OverlayLab, labDurationInFrames } from "./OverlayLab";
import type { OverlayStyle, TimelineProps } from "./types";
import { DEFAULT_OVERLAY_STYLE, emptyTimeline } from "./types";

/**
 * Mirrors the size/placement overrides in `styles/social/style.md` — social
 * shrinks per-kind sizes hard so MG fits its letterbox top bar while leaving
 * `sizeBands.heroCqh` at 22. It is the pack most likely to regress on a sizing
 * change, so it gets its own Lab composition.
 */
const SOCIAL_OVERLAY_STYLE: OverlayStyle = {
  ...DEFAULT_OVERLAY_STYLE,
  chapter: { kickerSizeCqh: 1.4, titleSizeCqh: 4.2, leftCqw: 5, topCqh: 10, maxWidthCqw: 90 },
  emphasis: { sizeCqh: 5.2, leftCqw: 5, topCqh: 12, maxWidthCqw: 90, underline: true },
  callout: { leftCqw: 5, topCqh: 10, valueSizeCqh: 5.6, sourceSizeCqh: 1.6, maxWidthCqw: 90 },
  diagram: { leftCqw: 5, topCqh: 8, maxWidthCqw: 90, stepSizeCqh: 2.2, connector: "traveling_dot" },
  chip: { leftCqw: 5, topCqh: 14, sizeCqh: 2.0, iconEm: 1.15, float: true },
};

/**
 * Props come from Remotion CLI: `remotion studio … --props=…/remotion-props.json`
 * (`ae compose --studio` passes this).
 */
const loadDefaultProps = (): TimelineProps => {
  const fromCli = getInputProps() as Partial<TimelineProps>;
  if (fromCli?.timeline) {
    return { timeline: fromCli.timeline };
  }
  console.warn(
    "No timeline props — use: ae compose <episode> --studio (passes --props). Using empty timeline.",
  );
  return { timeline: emptyTimeline };
};

export const RemotionRoot: React.FC = () => {
  const defaults = loadDefaultProps();
  const tl = defaults.timeline;
  return (
    <>
      <Composition
        id="AgenticTimeline"
        component={AgenticTimeline}
        durationInFrames={Math.max(1, tl.durationInFrames || 30 * 10)}
        fps={tl.fps || 30}
        width={tl.width || 1920}
        height={tl.height || 1080}
        defaultProps={defaults}
        calculateMetadata={async ({ props }) => {
          const t = props.timeline;
          return {
            durationInFrames: Math.max(1, t.durationInFrames || 1),
            fps: t.fps || 30,
            width: t.width || 1920,
            height: t.height || 1080,
          };
        }}
      />
      <Composition
        id="CutawayLab"
        component={CutawayLab}
        durationInFrames={Math.round(LAB_CUTAWAY.durationSec * 30)}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ cutaway: LAB_CUTAWAY }}
        calculateMetadata={async ({ props }) => {
          const dur = props.cutaway?.durationSec ?? LAB_CUTAWAY.durationSec;
          return {
            durationInFrames: Math.max(1, Math.round(dur * 30)),
            fps: 30,
            width: 1920,
            height: 1080,
          };
        }}
      />
      <Composition
        id="MockupLab"
        component={MockupLab}
        durationInFrames={24 * 30}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ scenes: LAB_MOCK_SCENES }}
        calculateMetadata={async ({ props }) => {
          const end = (props.scenes ?? LAB_MOCK_SCENES).reduce(
            (a, s) => Math.max(a, s.fromSec + s.durationSec),
            1,
          );
          return {
            durationInFrames: Math.max(1, Math.round(end * 30)),
            fps: 30,
            width: 1920,
            height: 1080,
          };
        }}
      />
      <Composition
        id="OverlayLab"
        component={OverlayLab}
        durationInFrames={labDurationInFrames(LAB_OVERLAYS)}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ overlays: LAB_OVERLAYS, styleTokens: DEFAULT_OVERLAY_STYLE }}
        calculateMetadata={async ({ props }) => ({
          durationInFrames: labDurationInFrames(props.overlays ?? LAB_OVERLAYS),
          fps: 30,
          width: 1920,
          height: 1080,
        })}
      />
      <Composition
        id="OverlayLabSocial"
        component={OverlayLab}
        durationInFrames={labDurationInFrames(LAB_OVERLAYS)}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{ overlays: LAB_OVERLAYS, styleTokens: SOCIAL_OVERLAY_STYLE }}
        calculateMetadata={async ({ props }) => ({
          durationInFrames: labDurationInFrames(props.overlays ?? LAB_OVERLAYS),
          fps: 30,
          width: 1080,
          height: 1920,
        })}
      />
    </>
  );
};
