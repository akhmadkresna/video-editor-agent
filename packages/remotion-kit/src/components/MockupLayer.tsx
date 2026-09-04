import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { MockStyle, TimelineMockScene } from "../types";
import { DEFAULT_MOCK_STYLE } from "../types";
import { MockCam } from "./mockup/MockCam";
import { MockStage } from "./mockup/MockStage";
import { ClaudeChat } from "./mockup/ClaudeChat";
import { DiffPanel } from "./mockup/DiffPanel";
import { AppWindow } from "./mockup/AppWindow";
import { SkillsPanel } from "./mockup/SkillsPanel";
import { RepoView } from "./mockup/RepoView";
import { Cursor } from "./mockup/Cursor";
import { resolveRegion } from "./mockup/regions";

const FADE = 9;

const MockDissolve: React.FC<{
  durationInFrames: number;
  children: React.ReactNode;
}> = ({ durationInFrames, children }) => {
  const frame = useCurrentFrame();
  const opacity = Math.min(
    interpolate(frame, [0, FADE], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
    interpolate(frame, [durationInFrames - FADE, durationInFrames], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
  );
  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
};

/** First non-Cursor layer is the surface (v1: one surface per scene). */
function Surface({
  scene,
  style,
}: {
  scene: TimelineMockScene;
  style: MockStyle;
}): React.ReactNode {
  for (const layer of scene.layers) {
    if (layer.component === "ClaudeChat") {
      return (
        <ClaudeChat
          turns={layer.data.turns}
          typeCps={layer.data.typeCps}
          style={style}
        />
      );
    }
    if (layer.component === "DiffPanel") {
      return (
        <DiffPanel
          before={layer.data.before}
          after={layer.data.after}
          beforeMarks={layer.data.beforeMarks}
          afterMarks={layer.data.afterMarks}
          atSec={layer.data.atSec}
          style={style}
        />
      );
    }
    if (layer.component === "AppWindow") {
      return (
        <AppWindow
          app={layer.data.app}
          content={layer.data.content as never}
          src={layer.data.src}
          atSec={layer.data.atSec}
          style={style}
        />
      );
    }
    if (layer.component === "SkillsPanel") {
      return (
        <SkillsPanel
          skills={layer.data.skills}
          action={layer.data.action}
          atSec={layer.data.atSec}
          style={style}
        />
      );
    }
    if (layer.component === "RepoView") {
      return (
        <RepoView
          repoUrl={layer.data.repoUrl}
          repo={layer.data.repo}
          path={layer.data.path}
          source={layer.data.source}
          markdown={layer.data.markdown}
          scroll={layer.data.scroll}
          atSec={layer.data.atSec}
          style={style}
        />
      );
    }
  }
  return null;
}

/**
 * Drawn-screen scenes for `style: mockup`. Each scene covers the picture for
 * its window; the cam PIP (a pip_corner clip added by compose) and the MG
 * overlays render on top, outside MockCam.
 */
export const MockupLayer: React.FC<{
  scenes?: TimelineMockScene[];
  style?: MockStyle;
}> = ({ scenes, style }) => {
  const { fps } = useVideoConfig();
  const st = style ?? DEFAULT_MOCK_STYLE;
  if (!scenes?.length) return null;

  return (
    <>
      {scenes.map((scene) => {
        const from = Math.round(scene.fromSec * fps);
        const dur = Math.max(1, Math.round(scene.durationSec * fps));
        return (
          <Sequence
            key={scene.id}
            from={from}
            durationInFrames={dur}
            name={`mockup:${scene.id}`}
          >
            <MockDissolve durationInFrames={dur}>
              <MockCam
                camera={scene.camera}
                cfg={st.cam}
                resolve={(name, tLocal) => resolveRegion(name, scene, tLocal)}
              >
                <MockStage
                  title={scene.stage.title}
                  chrome={scene.stage.chrome ?? "claude"}
                  style={st}
                >
                  <Surface scene={scene} style={st} />
                </MockStage>
                {scene.layers.map((l, i) =>
                  l.component === "Cursor" ? (
                    <Cursor
                      key={i}
                      path={l.data.path}
                      resolve={(name, tLocal) =>
                        resolveRegion(name, scene, tLocal)
                      }
                      style={st}
                    />
                  ) : null,
                )}
              </MockCam>
            </MockDissolve>
          </Sequence>
        );
      })}
    </>
  );
};
