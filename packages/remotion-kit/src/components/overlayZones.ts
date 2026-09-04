import type { CSSProperties } from "react";
import type { OverlayKind, OverlayZone } from "../types";

/** Default zone when cover.json omits `zone` — kind-aware, face-clear. */
export function defaultZoneForKind(kind: OverlayKind): OverlayZone {
  switch (kind) {
    case "lower_third":
    case "stat":
    case "callout":
    case "emphasis":
      return "lower_raised";
    case "chip":
    case "tag":
    case "chapter":
    case "divider":
      return "top_sparse";
    case "diagram":
    case "title":
    case "quote":
    case "code":
    case "illustration":
    default:
      return "left_third";
  }
}

export function resolveZone(
  zone: OverlayZone | undefined,
  kind: OverlayKind,
): OverlayZone {
  return zone ?? defaultZoneForKind(kind);
}

/** Absolute positioning for OverlayLayer kinds (cqw/cqh percentages). */
export function zoneBoxStyle(
  zone: OverlayZone,
  opts: {
    maxWidthCqw?: number;
    insetCqw?: number;
    topCqh?: number;
    bottomCqh?: number;
  } = {},
): CSSProperties {
  const inset = opts.insetCqw ?? 4.5;
  const maxW = opts.maxWidthCqw ?? 42;
  const base: CSSProperties = {
    position: "absolute",
    maxWidth: `${maxW}%`,
  };
  switch (zone) {
    case "right_third":
      return {
        ...base,
        right: `${inset}%`,
        left: "auto",
        top: `${opts.topCqh ?? 18}%`,
        textAlign: "right",
      };
    case "lower_raised":
      if (opts.topCqh != null) {
        return {
          ...base,
          left: `${inset}%`,
          top: `${opts.topCqh}%`,
          bottom: "auto",
        };
      }
      return {
        ...base,
        left: `${inset}%`,
        bottom: `${opts.bottomCqh ?? 28}%`,
        top: "auto",
      };
    case "top_sparse":
      return {
        ...base,
        left: `${inset}%`,
        top: `${opts.topCqh ?? 10}%`,
        maxWidth: `${Math.min(maxW, 38)}%`,
      };
    case "left_third":
    default:
      return {
        ...base,
        left: `${inset}%`,
        top: `${opts.topCqh ?? 12}%`,
      };
  }
}

/** Veil behind type — follows the side the text sits on (not face-center). */
export function zoneVeilBackground(zone: OverlayZone): string {
  switch (zone) {
    case "right_third":
      return "linear-gradient(270deg, rgba(0,0,0,0.42) 0%, rgba(0,0,0,0.1) 32%, transparent 50%)";
    case "lower_raised":
      return "linear-gradient(0deg, rgba(0,0,0,0.38) 0%, rgba(0,0,0,0.12) 40%, transparent 62%)";
    case "top_sparse":
      return "linear-gradient(180deg, rgba(0,0,0,0.36) 0%, rgba(0,0,0,0.1) 36%, transparent 55%)";
    case "left_third":
    default:
      return "linear-gradient(90deg, rgba(0,0,0,0.42) 0%, rgba(0,0,0,0.1) 32%, transparent 50%)";
  }
}

/** Flex rail align for glass AbsoluteFill wrappers. */
export function zoneRailAlign(zone: OverlayZone): {
  alignItems: CSSProperties["alignItems"];
  justifyContent: CSSProperties["justifyContent"];
  padding: string;
  textAlign?: CSSProperties["textAlign"];
} {
  switch (zone) {
    case "right_third":
      return {
        alignItems: "flex-end",
        justifyContent: "center",
        padding: "0 8%",
        textAlign: "right",
      };
    case "lower_raised":
      return {
        alignItems: "flex-start",
        justifyContent: "flex-end",
        padding: "0 8% 9%",
      };
    case "top_sparse":
      return {
        alignItems: "flex-start",
        justifyContent: "flex-start",
        padding: "8% 8% 0",
      };
    case "left_third":
    default:
      return {
        alignItems: "flex-start",
        justifyContent: "center",
        padding: "0 8%",
      };
  }
}
