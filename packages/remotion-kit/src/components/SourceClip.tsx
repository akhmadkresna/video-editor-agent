import React from "react";
import { Video } from "@remotion/media";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type {
  ClipLayout,
  FramingMotion,
  ScreenExplainerStyle,
  WindowCropNorm,
} from "../types";
import { DEFAULT_SCREEN_EXPLAINER } from "../types";
import { isLetterboxPresentation, letterboxBand } from "../letterbox";

type ObjectFit = "contain" | "cover" | "fill" | "none" | "scale-down";

/**
 * Prefer @remotion/media Video over OffthreadVideo.
 * OffthreadVideo extracts frames via blob: URLs; on long Windows renders of
 * multi-GB mezzanines Chrome eventually hits net::ERR_UPLOAD_FILE_CHANGED.
 */
function TimelineVideo({
  src,
  startFrom,
  volume,
  style,
  objectFit = "cover",
}: {
  src: string;
  startFrom: number;
  volume: number;
  style?: React.CSSProperties;
  objectFit?: ObjectFit;
}) {
  const { objectFit: _ignored, ...restStyle } = style ?? {};
  return (
    <Video
      src={src}
      trimBefore={startFrom}
      volume={volume}
      muted={volume === 0}
      objectFit={objectFit}
      style={restStyle}
      delayRenderTimeoutInMilliseconds={120_000}
      delayRenderRetries={3}
      disallowFallbackToOffthreadVideo
    />
  );
}

type Props = {
  src: string;
  sourceIn: number;
  layout: ClipLayout;
  scale?: number;
  motion?: FramingMotion;
  durationSec?: number;
  /** Explicit mute; if omitted, non-cam sources are muted by volume prop. */
  muted?: boolean;
  volume?: number;
  windowCrop?: WindowCropNorm;
  screenExplainer?: ScreenExplainerStyle;
};

const IMAGE_EXT = /\.(png|jpe?g|webp|gif|bmp)(\?.*)?$/i;

function isImageSrc(src: string): boolean {
  return IMAGE_EXT.test(src);
}

/** Parse a "W:H" ratio string (e.g. pip.aspectRatio: "5:6") into width/height.
 * Falls back to 4:5 if missing/malformed — the previous hardcoded default. */
function parseAspectRatio(ratio: string | undefined, fallback = 4 / 5): number {
  if (!ratio) return fallback;
  const m = /^(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)$/.exec(ratio.trim());
  if (!m) return fallback;
  const w = parseFloat(m[1]);
  const h = parseFloat(m[2]);
  return h > 0 ? w / h : fallback;
}

/** Resolve public-relative paths via staticFile; leave http(s) alone. */
function resolveSrc(src: string): string {
  if (
    src.startsWith("http://") ||
    src.startsWith("https://") ||
    src.startsWith("data:") ||
    src.startsWith("blob:")
  ) {
    return src;
  }
  if (src.startsWith("/") && !src.startsWith("/Users") && !src.startsWith("/home")) {
    return src;
  }
  if (src.startsWith("/") || /^[A-Za-z]:[\\/]/.test(src)) {
    console.warn(
      `Absolute media path will not load in Studio: ${src}. Re-run ae compose to stage into public/.`,
    );
    return src;
  }
  return staticFile(src);
}

//: Documentary/interview convention for a push-in is ~100%->115% over
//: 10+ seconds (~1.5%/sec), eased (Sine/Quad accelerate-then-settle),
//: not linear — see the research note above useMotionScale for sources.
//: Scale the target zoom with duration instead of a fixed amount so a
//: 5s hold and a 30s hold both read at roughly the same *rate*, capped
//: at the ~15% ceiling documentaries converge on.
const DRIFT_RATE_PER_SEC = 0.015;
const DRIFT_MIN_PCT = 0.05;
const DRIFT_MAX_PCT = 0.15;

function driftTargetPct(durationSec: number): number {
  return Math.min(
    DRIFT_MAX_PCT,
    Math.max(DRIFT_MIN_PCT, durationSec * DRIFT_RATE_PER_SEC),
  );
}

/** motion="drift"/"pull_back" easing + rate follow documentary interview
 * convention, not an arbitrary choice — see:
 * https://photography.tutsplus.com/tutorials/documentary-in-motion-interview-movement--cms-28295
 * "a cinematic push typically uses keyframes ten seconds or more apart
 * with a modest scale change, something like 100% to 115%... A gentle
 * curve from the Sine or Quad family... accelerates and settles instead
 * of starting and stopping abruptly." Ken Burns push-ins are near-
 * universal on interview/talking-head shots (PBS Frontline uses one on
 * every interview shot); pull-back is the opposite move, used
 * deliberately as a reveal (start tight, pull back to expose context)
 * rather than a routine alternate-every-other-shot default. */
function useMotionScale(
  baseScale: number,
  motion: FramingMotion,
  durationSec: number,
): number {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const ramp = Math.min(0.35, Math.max(0.12, durationSec / 5));

  if (motion === "hold" || motion === "snap") {
    return baseScale;
  }

  if (motion === "drift") {
    const end = baseScale * (1 + driftTargetPct(durationSec));
    return interpolate(t, [0, Math.max(0.05, durationSec)], [baseScale, end], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.inOut(Easing.sin),
    });
  }

  if (motion === "pull_back") {
    const start = baseScale * (1 + driftTargetPct(durationSec));
    return interpolate(t, [0, Math.max(0.05, durationSec)], [start, baseScale], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.inOut(Easing.sin),
    });
  }

  if (motion === "ease_out") {
    const from = Math.min(baseScale * 1.08, 1.28);
    return interpolate(t, [0, ramp], [from, baseScale], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    });
  }

  const from = Math.max(1, baseScale * 0.94);
  return interpolate(t, [0, ramp], [from, baseScale], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
}

function CroppedVideo({
  src,
  startFrom,
  volume,
  liveScale,
  transformOrigin,
  windowCrop,
  objectFit = "cover",
  objectPosition = "center center",
}: {
  src: string;
  startFrom: number;
  volume: number;
  liveScale: number;
  transformOrigin: string;
  windowCrop?: WindowCropNorm;
  objectFit?: string;
  objectPosition?: string;
}) {
  const mediaStyle: React.CSSProperties = {
    width: "100%",
    height: "100%",
    objectFit: objectFit as React.CSSProperties["objectFit"],
    objectPosition,
    transform: `scale(${liveScale})`,
    transformOrigin,
  };

  if (!windowCrop || windowCrop.w <= 0 || windowCrop.h <= 0) {
    if (isImageSrc(src)) {
      return <Img src={src} style={mediaStyle} />;
    }
    return (
      <TimelineVideo
        src={src}
        startFrom={startFrom}
        volume={volume}
        style={mediaStyle}
        objectFit={(objectFit as ObjectFit) || "cover"}
      />
    );
  }

  const { x, y, w, h } = windowCrop;
  // Map source frame so the crop rect fills the container.
  const widthPct = (1 / w) * 100;
  const heightPct = (1 / h) * 100;
  const leftPct = (-x / w) * 100;
  const topPct = (-y / h) * 100;
  const cropStyle: React.CSSProperties = {
    position: "absolute",
    width: `${widthPct}%`,
    height: `${heightPct}%`,
    left: `${leftPct}%`,
    top: `${topPct}%`,
    transform: `scale(${liveScale})`,
    transformOrigin,
  };

  return (
    <div style={{ width: "100%", height: "100%", overflow: "hidden", position: "relative" }}>
      {isImageSrc(src) ? (
        <Img src={src} style={{ ...cropStyle, objectFit: "fill" }} />
      ) : (
        <TimelineVideo
          src={src}
          startFrom={startFrom}
          volume={volume}
          style={cropStyle}
          objectFit="fill"
        />
      )}
    </div>
  );
}

export const SourceClip: React.FC<Props> = ({
  src,
  sourceIn,
  layout,
  scale = 1,
  motion = "snap",
  durationSec = 1,
  muted = false,
  volume,
  windowCrop,
  screenExplainer,
}) => {
  const { width, height, fps } = useVideoConfig();
  const startFrom = Math.max(0, Math.round(sourceIn * fps));
  const liveScale = useMotionScale(scale, motion, durationSec);
  const resolvedSrc = resolveSrc(src);
  const vol = volume ?? (muted ? 0 : 1);
  const se = screenExplainer || DEFAULT_SCREEN_EXPLAINER;
  const screenCfg = { ...DEFAULT_SCREEN_EXPLAINER.screen, ...se.screen };
  const pipCfg = { ...DEFAULT_SCREEN_EXPLAINER.pip, ...se.pip };
  const portrait = height > width;

  if (layout === "pip_corner") {
    const letterbox = isLetterboxPresentation(screenCfg.presentation);
    const band = letterbox
      ? letterboxBand(width, height, screenCfg.widthRatio ?? 1)
      : null;
    const pipW = Math.round(
      width * (pipCfg.widthRatio ?? (portrait ? (letterbox ? 0.22 : 0.36) : 0.18)),
    );
    const pipRatio = parseAspectRatio(pipCfg.aspectRatio); // width / height
    const pipH = Math.round(pipW / pipRatio);
    const anchor = (pipCfg.anchor || "stage_lower_right").toLowerCase();
    const pinLeft = anchor.includes("left");
    const radius = pipCfg.borderRadiusPx ?? 14;

    let left: number | undefined;
    let right: number | undefined;
    let bottom: number | undefined;
    let top: number | undefined;

    if (band && (anchor.includes("band") || letterbox)) {
      // Option A: cam sits on the 16:9 stage, bottom-left of the landscape band.
      const insetX = Math.round(
        band.bandW * (pipCfg.insetLeftRatio ?? pipCfg.insetRightRatio ?? 0.02),
      );
      const insetY = Math.round(
        band.bandH * (pipCfg.insetBottomRatio ?? 0.03),
      );
      left = pinLeft || !anchor.includes("right")
        ? band.left + insetX
        : undefined;
      right = !pinLeft && anchor.includes("right")
        ? width - (band.left + band.bandW) + insetX
        : undefined;
      if (left == null && right == null) {
        left = band.left + insetX;
      }
      top = band.top + band.bandH - pipH - insetY;
    } else {
      bottom = Math.round(
        height * (pipCfg.insetBottomRatio ?? (portrait ? 0.29 : 0.045)),
      );
      const sideInset = Math.round(
        width *
          (pinLeft
            ? (pipCfg.insetLeftRatio ?? pipCfg.insetRightRatio ?? 0.04)
            : (pipCfg.insetRightRatio ?? 0.035)),
      );
      if (pinLeft) left = sideInset;
      else right = sideInset;
    }

    return (
      <AbsoluteFill>
        <div
          style={{
            position: "absolute",
            ...(left != null ? { left } : {}),
            ...(right != null ? { right } : {}),
            ...(top != null ? { top } : {}),
            ...(bottom != null ? { bottom } : {}),
            width: pipW,
            height: pipH,
            borderRadius: radius,
            overflow: "hidden",
            boxShadow:
              "0 22px 44px rgba(18, 24, 32, 0.32), 0 6px 14px rgba(18, 24, 32, 0.18)",
            background: "#0a0a0a",
          }}
        >
          <TimelineVideo
            src={resolvedSrc}
            startFrom={startFrom}
            volume={vol}
            objectFit="cover"
            style={{
              width: "100%",
              height: "100%",
              objectPosition: pipCfg.objectPosition ?? "center 28%",
              transform: `scale(${liveScale})`,
              transformOrigin: "center center",
            }}
          />
        </div>
      </AbsoluteFill>
    );
  }

  if (layout === "float_centered") {
    const letterbox = isLetterboxPresentation(screenCfg.presentation);
    if (letterbox) {
      const band = letterboxBand(width, height, screenCfg.widthRatio ?? 1);
      const radius = screenCfg.borderRadiusPx ?? 0;
      const fit = (screenCfg.objectFit as string | undefined) ?? "cover";
      return (
        <AbsoluteFill style={{ background: "#000" }}>
          <div
            style={{
              position: "absolute",
              left: band.left,
              top: band.top,
              width: band.bandW,
              height: band.bandH,
              borderRadius: radius,
              overflow: "hidden",
              background: "#141414",
            }}
          >
            <CroppedVideo
              src={resolvedSrc}
              startFrom={startFrom}
              volume={vol}
              liveScale={liveScale}
              transformOrigin="center center"
              windowCrop={windowCrop}
              objectFit={fit}
            />
          </div>
        </AbsoluteFill>
      );
    }
    // Soft-round card only: size from screen aspect (no crop / no distort).
    // Fit inside cozy max box; center on cool-mist canvas.
    const widthRatio = screenCfg.widthRatio ?? 0.78;
    const maxW = width * widthRatio;
    const maxH = height * (screenCfg.maxHeightRatio ?? 0.82);
    const ar =
      windowCrop && windowCrop.w > 0 && windowCrop.h > 0
        ? windowCrop.w / windowCrop.h
        : typeof screenCfg.aspectRatio === "number" && screenCfg.aspectRatio > 0
          ? screenCfg.aspectRatio
          : 16 / 9;
    let floatW = maxW;
    let floatH = floatW / ar;
    if (floatH > maxH) {
      floatH = maxH;
      floatW = floatH * ar;
    }
    floatW = Math.round(floatW);
    floatH = Math.round(floatH);
    const radius = screenCfg.borderRadiusPx ?? 24;
    const topRatio = screenCfg.topRatio ?? 0.08;
    return (
      <AbsoluteFill>
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: portrait ? `${Math.round(topRatio * 1000) / 10}%` : "50%",
            width: floatW,
            height: floatH,
            transform: portrait ? "translateX(-50%)" : "translate(-50%, -50%)",
            borderRadius: radius,
            overflow: "hidden",
            boxShadow:
              "0 36px 70px rgba(28, 36, 48, 0.22), 0 12px 28px rgba(28, 36, 48, 0.14)",
            background: "transparent",
          }}
        >
          <CroppedVideo
            src={resolvedSrc}
            startFrom={startFrom}
            volume={vol}
            liveScale={liveScale}
            transformOrigin="center center"
            windowCrop={windowCrop}
            objectFit="fill"
          />
        </div>
      </AbsoluteFill>
    );
  }

  // full cam / edge-to-edge
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <TimelineVideo
        src={resolvedSrc}
        startFrom={startFrom}
        volume={vol}
        objectFit="cover"
        style={{
          width: "100%",
          height: "100%",
          transform: `scale(${liveScale})`,
          transformOrigin: "center 42%",
        }}
      />
    </AbsoluteFill>
  );
};
