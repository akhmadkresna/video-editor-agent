import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import type { TimelineSfx } from "../types";

type Props = {
  sfx: TimelineSfx[];
};

/**
 * Additive modern-tech SFX under cam VO. Shutter/click are one-shots.
 * Typing tiles only when present (opt-in / hand-authored — off in default suggest).
 * No whoosh assets — pack is curated in assets/sfx.
 */
export const SfxLayer: React.FC<Props> = ({ sfx }) => {
  const { fps } = useVideoConfig();
  if (!sfx?.length) return null;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {sfx.map((item) => {
        const from = Math.round(item.fromSec * fps);
        const duration = Math.max(1, Math.round(item.durationSec * fps));
        const volume = typeof item.volume === "number" ? item.volume : 0.4;
        const src = staticFile(item.src);

        if (item.tile || item.kind === "typing") {
          // Tile short typing loop across the hold window.
          const tileSec = Math.max(0.4, Math.min(item.durationSec, 1.2));
          const tileFrames = Math.max(1, Math.round(tileSec * fps));
          const tiles: React.ReactNode[] = [];
          for (let offset = 0; offset < duration; offset += tileFrames) {
            const rem = Math.min(tileFrames, duration - offset);
            tiles.push(
              <Sequence
                key={`${item.id}-t${offset}`}
                from={from + offset}
                durationInFrames={rem}
                name={`${item.id}-${offset}`}
                layout="none"
              >
                <Audio src={src} volume={volume} />
              </Sequence>,
            );
          }
          return <React.Fragment key={item.id}>{tiles}</React.Fragment>;
        }

        // Play full remapped durationSec (do not hard-cap — onset may sit late in raw assets).
        return (
          <Sequence
            key={item.id}
            from={from}
            durationInFrames={duration}
            name={item.id}
            layout="none"
          >
            <Audio src={src} volume={volume} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
