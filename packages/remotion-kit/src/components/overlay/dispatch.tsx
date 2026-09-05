/**
 * Overlay kind → A-Roll Text Motion System component.
 *
 * One dispatch for all 14 kinds, replacing the two divergent paths this
 * codebase used to have (`OneOverlay` for 5 kinds with its own fonts/springs,
 * `GlassOverlay` for 8 more that never even received the style config).
 *
 * Mapping is spec §3. Every component takes the resolved theme, so there is no
 * code path that can render without style-pack config applied.
 */
import React from "react";
import { useVideoConfig } from "remotion";
import type { OverlayZone, TimelineOverlay } from "../../types";
import { resolveZone, zoneBoxMetrics, zoneCorner } from "../overlayZones";
import { CalloutArrow } from "./CalloutArrow";
import { CaptionLine } from "./CaptionLine";
import { ChapterMarker, chapterNumberFrom } from "./ChapterMarker";
import { FlowSteps } from "./FlowSteps";
import { IllustrationTag } from "./IllustrationTag";
import { ListCycle } from "./ListCycle";
import { PunchWord } from "./PunchWord";
import { StatCallout } from "./StatCallout";
import { iconNameFromNote } from "./icons";
import { cqh, valueSizeCqh } from "./sizing";
import type { OverlayTheme } from "./theme";

/** Kinds that place themselves absolutely rather than sitting in a zone box. */
export const SELF_PLACED_KINDS = new Set(["chapter", "divider", "lower_third"]);

/** Kinds still served by the legacy glass renderers (out of scope, spec §3). */
export const LEGACY_GLASS_KINDS = new Set(["code", "illustration"]);

/** Per-kind box width, used for both placement and the text fitter. */
export function boxOptsForKind(
  kind: string,
  theme: OverlayTheme,
): { maxWidthCqw?: number; bottomCqh?: number; topCqh?: number; insetCqw?: number } {
  switch (kind) {
    case "emphasis":
    case "quote":
    case "title":
      return {
        maxWidthCqw: theme.emphasis.maxWidthCqw,
        bottomCqh: theme.emphasis.bottomCqh,
        topCqh: theme.emphasis.topCqh,
        insetCqw: theme.emphasis.leftCqw,
      };
    case "stat":
    case "callout":
      return {
        maxWidthCqw: theme.callout.maxWidthCqw,
        bottomCqh: theme.callout.bottomCqh,
        topCqh: theme.callout.topCqh,
        insetCqw: theme.callout.leftCqw,
      };
    case "diagram":
      return {
        maxWidthCqw: theme.diagram.maxWidthCqw,
        topCqh: theme.diagram.topCqh,
        insetCqw: theme.diagram.leftCqw,
      };
    case "chip":
    case "tag":
      return {
        maxWidthCqw: 42,
        topCqh: theme.chip.topCqh,
        insetCqw: theme.chip.leftCqw,
      };
    default:
      return { maxWidthCqw: 42 };
  }
}

/**
 * Cursor heuristic (§3: "only if the line ends mid-thought"). Trailing comma /
 * ellipsis / dash, or an explicit `cursor` in the note.
 */
function wantsCursor(ov: TimelineOverlay): boolean {
  if (/\bcursor\b/i.test(ov.note || "")) return true;
  return /[,…-]\s*$/.test(ov.text || "");
}

export function renderOverlayBody(
  ov: TimelineOverlay,
  theme: OverlayTheme,
  frameSize: { width: number; height: number },
): React.ReactNode {
  const zone: OverlayZone = resolveZone(ov.zone, ov.kind);
  const align: "left" | "right" = zone === "right_third" ? "right" : "left";
  const box = zoneBoxMetrics(zone, frameSize, boxOptsForKind(ov.kind, theme));
  const maxWidthCqw = (box.maxWidthPx / frameSize.width) * 100;

  switch (ov.kind) {
    case "title":
      return (
        <PunchWord
          text={ov.text || ""}
          eyebrow={ov.kicker}
          accent={ov.accent}
          size="xl"
          align={align}
          cursor={wantsCursor(ov)}
          maxWidthCqw={maxWidthCqw}
          boxHeightPx={box.maxHeightPx}
          theme={theme}
        />
      );

    case "emphasis":
      return (
        <PunchWord
          text={ov.text || ""}
          eyebrow={ov.kicker}
          size="lg"
          align={align}
          underline={theme.emphasis.underline !== false}
          cursor={wantsCursor(ov)}
          maxWidthCqw={maxWidthCqw}
          boxHeightPx={box.maxHeightPx}
          theme={theme}
        />
      );

    case "quote":
      // §3: PunchWord md + the attribution entering one `durBase` after the
      // quote has settled.
      return (
        <div style={{ display: "inline-flex", flexDirection: "column", gap: "0.4em" }}>
          <PunchWord
            text={ov.text || ""}
            size="md"
            align={align}
            maxWidthCqw={maxWidthCqw}
            boxHeightPx={box.maxHeightPx * 0.7}
            theme={theme}
          />
          {ov.kicker ? (
            <CaptionLine
              text=""
              speaker={ov.kicker}
              inline
              align={align}
              delayMs={theme.durBase + theme.wordStaggerMs * 3}
              theme={theme}
            />
          ) : null}
        </div>
      );

    case "stat":
      return (
        <StatCallout
          value={ov.value || ov.text || ""}
          eyebrow={ov.title}
          meta={ov.sourceLabel}
          align={align}
          valueSizeCqh={valueSizeCqh(theme)}
          maxWidthCqw={maxWidthCqw}
          theme={theme}
        />
      );

    case "callout": {
      // Three-way (§3 + the "never render nothing" rule):
      //   value  → StatCallout
      //   at     → CalloutArrow (an arrow needs a target; this is also how
      //            "suppress on full-cam" is honoured, since the renderer
      //            can't see the clip layout)
      //   else   → PunchWord, so an authored beat is never silently dropped
      if (ov.value) {
        return (
          <StatCallout
            value={ov.value}
            eyebrow={ov.sourceLabel || ov.kicker}
            meta={ov.title}
            align={align}
            valueSizeCqh={theme.callout.valueSizeCqh}
            metaSizeCqh={theme.callout.sourceSizeCqh}
            maxWidthCqw={maxWidthCqw}
            theme={theme}
          />
        );
      }
      if (ov.at && ov.at.length === 2) {
        const originX = zone === "right_third" ? 0.78 : 0.22;
        const originY = zone === "top_sparse" ? 0.2 : 0.72;
        return (
          <CalloutArrow
            label={ov.text || ""}
            to={[ov.at[0], ov.at[1]]}
            from={[originX, originY]}
            theme={theme}
          />
        );
      }
      return (
        <PunchWord
          text={ov.text || ""}
          eyebrow={ov.sourceLabel || ov.kicker}
          size="lg"
          align={align}
          underline={theme.emphasis.underline !== false}
          maxWidthCqw={maxWidthCqw}
          boxHeightPx={box.maxHeightPx}
          theme={theme}
        />
      );
    }

    case "diagram":
      return (
        <div style={{ display: "inline-flex", flexDirection: "column", gap: "0.5em" }}>
          {ov.kicker || ov.title ? (
            <div style={{ fontFamily: theme.fontSans, color: theme.ink }}>
              {ov.kicker ? (
                <div
                  style={{
                    fontSize: cqh(theme.bands.eyebrowCqh, frameSize.height),
                    fontWeight: 700,
                    letterSpacing: theme.lsCaps,
                    textTransform: "uppercase",
                    color: theme.inkMuted,
                  }}
                >
                  {ov.kicker}
                </div>
              ) : null}
              {ov.title ? (
                <div
                  style={{
                    fontSize: cqh(theme.bands.subCqh * 0.7, frameSize.height),
                    fontWeight: theme.weightHero,
                    letterSpacing: theme.lsTight,
                    textShadow: theme.textShadow,
                  }}
                >
                  {ov.title}
                </div>
              ) : null}
            </div>
          ) : null}
          <FlowSteps steps={ov.steps || []} stepAtSec={ov.stepAtSec} theme={theme} />
        </div>
      );

    case "chapter":
    case "divider":
      return (
        <ChapterMarker
          number={chapterNumberFrom(ov.kicker)}
          title={ov.title || ov.text}
          corner={zoneCorner(zone)}
          theme={theme}
        />
      );

    case "chip":
    case "tag":
      return (
        <IllustrationTag
          label={ov.text || ov.title || ""}
          icon={ov.kind === "chip" ? iconNameFromNote(ov.note) : null}
          corner={zoneCorner(zone) === "top-right" ? "top-right" : "top-left"}
          durationSec={ov.durationSec}
          theme={theme}
        />
      );

    case "lower_third":
      // §3 maps text→speaker / title→text, but the *name* is the large line.
      return (
        <CaptionLine
          text={ov.text || ""}
          speaker={ov.title}
          size="lg"
          align={align}
          theme={theme}
        />
      );

    case "list_cycle":
      return (
        <ListCycle
          prefix={ov.text || ""}
          items={ov.steps || []}
          stepAtSec={ov.stepAtSec}
          theme={theme}
        />
      );

    default:
      return null;
  }
}

/** Frame dimensions helper for callers inside a composition. */
export function useFrameSize(): { width: number; height: number } {
  const { width, height } = useVideoConfig();
  return { width, height };
}
