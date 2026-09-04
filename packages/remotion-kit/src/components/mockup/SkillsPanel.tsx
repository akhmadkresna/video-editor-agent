import React from "react";
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { MockStyle } from "../../types";
import { mockFont } from "./fonts";

type Skill = { name: string; source?: string; on: boolean };

const NAV = ["Umum", "Kapabilitas", "Koneksi", "Akun"];

const Toggle: React.FC<{ on: number; style: MockStyle }> = ({ on, style }) => (
  <div
    style={{
      width: "3cqw",
      height: "1.6cqw",
      borderRadius: 999,
      background: interpolateColor(on, style.railLine, style.badgeInk),
      position: "relative",
      flexShrink: 0,
    }}
  >
    <div
      style={{
        position: "absolute",
        top: "0.18cqw",
        left: `calc(${0.18 + on * 1.42}cqw)`,
        width: "1.24cqw",
        height: "1.24cqw",
        borderRadius: "50%",
        background: "#ffffff",
        boxShadow: "0 1px 2px rgba(20,30,35,0.35)",
      }}
    />
  </div>
);

/** crude 2-stop lerp for the track colour */
function interpolateColor(p: number, a: string, b: string): string {
  const pa = hex(a);
  const pb = hex(b);
  const c = pa.map((v, i) => Math.round(v + (pb[i] - v) * p));
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
}
function hex(h: string): [number, number, number] {
  const m = h.replace("#", "");
  return [
    parseInt(m.slice(0, 2), 16),
    parseInt(m.slice(2, 4), 16),
    parseInt(m.slice(4, 6), 16),
  ];
}

/** Claude Desktop → Settings → Capabilities → Skills. */
export const SkillsPanel: React.FC<{
  skills: Skill[];
  action?: string;
  atSec?: number;
  style: MockStyle;
}> = ({ skills, action, atSec = 0.4, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const toggleTarget = action?.startsWith("toggle:") ? action.slice(7) : null;
  const flipT = atSec + 0.9;
  const uploading = action === "upload";
  const sheet = uploading
    ? interpolate(t, [atSec + 0.6, atSec + 1.2], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
        easing: Easing.inOut(Easing.cubic),
      })
    : 0;

  return (
    <div style={{ flex: 1, display: "flex", background: style.window, position: "relative" }}>
      {/* settings sidebar */}
      <div
        style={{
          width: "24%",
          borderRight: `1px solid ${style.railLine}`,
          background: style.rail,
          padding: "2.4cqw 1.4cqw",
          display: "flex",
          flexDirection: "column",
          gap: "0.6cqw",
          fontFamily: mockFont.ui,
          fontSize: "1.4cqw",
        }}
      >
        <div
          style={{
            fontFamily: mockFont.mono,
            fontSize: "1.1cqw",
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            color: style.chromeTitle,
            marginBottom: "1cqw",
          }}
        >
          Pengaturan
        </div>
        {NAV.map((n) => {
          const sel = n === "Kapabilitas";
          return (
            <div
              key={n}
              style={{
                padding: "0.8cqw 1cqw",
                borderRadius: 8,
                background: sel ? style.badgeBg : "transparent",
                color: sel ? style.badgeInk : style.asstInk,
                fontWeight: sel ? 600 : 400,
              }}
            >
              {n}
            </div>
          );
        })}
      </div>

      {/* skills list — big right pad keeps toggles clear of the cam PIP */}
      <div
        style={{
          flex: 1,
          padding: "2.6cqw 24cqw 2.6cqw 3cqw",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ display: "flex", alignItems: "baseline", gap: "1.4cqw" }}>
          <div
            style={{
              fontFamily: mockFont.ui,
              fontSize: "2.4cqw",
              fontWeight: 600,
              color: style.asstInk,
            }}
          >
            Skills
          </div>
          <div
            style={{
              marginLeft: "auto",
              fontFamily: mockFont.ui,
              fontSize: "1.3cqw",
              color: style.badgeInk,
              border: `1px solid ${style.badgeInk}`,
              borderRadius: 8,
              padding: "0.5cqw 1.1cqw",
            }}
          >
            + Unggah skill
          </div>
        </div>
        <div
          style={{
            fontFamily: mockFont.ui,
            fontSize: "1.35cqw",
            color: style.chromeTitle,
            margin: "0.8cqw 0 1.8cqw",
          }}
        >
          Folder instruksi yang Claude pakai otomatis kalau relevan.
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          {skills.map((s) => {
            const isTarget = s.name === toggleTarget;
            const on = isTarget
              ? interpolate(t, [flipT, flipT + 0.28], [s.on ? 0 : 1, s.on ? 1 : 0], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                  easing: Easing.inOut(Easing.cubic),
                })
              : s.on
                ? 1
                : 0;
            const hi = isTarget
              ? interpolate(t, [flipT - 0.2, flipT + 0.6, flipT + 1.4], [0, 1, 0], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                })
              : 0;
            return (
              <div
                key={s.name}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "1.2cqw",
                  padding: "1.4cqw 1.2cqw",
                  borderTop: `1px solid ${style.railLine}`,
                  borderRadius: 8,
                  background: `rgba(73,101,115,${hi * 0.08})`,
                }}
              >
                <span
                  style={{
                    fontFamily: mockFont.mono,
                    fontSize: "1.55cqw",
                    color: style.asstInk,
                  }}
                >
                  {s.name}
                </span>
                {s.source && (
                  <span
                    style={{
                      fontFamily: mockFont.ui,
                      fontSize: "1.1cqw",
                      color: style.chipInk,
                      border: `1px solid ${style.chipBorder}`,
                      borderRadius: 999,
                      padding: "0.2cqw 0.7cqw",
                    }}
                  >
                    {s.source}
                  </span>
                )}
                <div style={{ marginLeft: "auto" }}>
                  <Toggle on={on} style={style} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* upload drop sheet */}
      {uploading && (
        <div
          style={{
            position: "absolute",
            left: "10%",
            right: "10%",
            bottom: 0,
            transform: `translateY(${(1 - sheet) * 100}%)`,
            background: style.window,
            border: `1px solid ${style.windowBorder}`,
            borderBottom: "none",
            borderRadius: "16px 16px 0 0",
            boxShadow: style.windowShadow,
            padding: "3cqw",
          }}
        >
          <div
            style={{
              border: `2px dashed ${style.badgeInk}`,
              borderRadius: 12,
              padding: "3.5cqw",
              textAlign: "center",
              fontFamily: mockFont.ui,
              fontSize: "1.5cqw",
              color: style.badgeInk,
            }}
          >
            Lepas file .zip skill di sini
          </div>
        </div>
      )}
    </div>
  );
};
