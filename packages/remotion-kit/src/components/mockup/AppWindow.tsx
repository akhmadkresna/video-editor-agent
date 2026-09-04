import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { MockStyle } from "../../types";
import { mockFont } from "./fonts";

type Content = "mock-deck" | "mock-sheet" | "mock-doc" | { src: string };

const APP_LABEL: Record<string, string> = {
  pptx: "Presentation.pptx",
  xlsx: "Workbook.xlsx",
  docx: "Document.docx",
  preview: "Preview",
  browser: "Browser",
};

const Bar: React.FC<{ w: string; h?: string; c: string; r?: number }> = ({
  w,
  h = "0.9cqw",
  c,
  r = 3,
}) => <div style={{ width: w, height: h, background: c, borderRadius: r }} />;

const Deck: React.FC<{ style: MockStyle }> = ({ style }) => (
  <div style={{ flex: 1, display: "flex", background: "#e9edf0" }}>
    <div
      style={{
        width: "16%",
        borderRight: `1px solid ${style.railLine}`,
        padding: "1.4cqw 1cqw",
        display: "flex",
        flexDirection: "column",
        gap: "1cqw",
        background: "#f2f5f6",
      }}
    >
      {[0, 1, 2, 3].map((i) => (
        <div
          key={i}
          style={{
            aspectRatio: "16 / 10",
            borderRadius: 5,
            background: style.window,
            border: `${i === 1 ? 2 : 1}px solid ${
              i === 1 ? style.badgeInk : style.railLine
            }`,
          }}
        />
      ))}
    </div>
    <div style={{ flex: 1, display: "grid", placeItems: "center", padding: "3cqw" }}>
      <div
        style={{
          width: "82%",
          aspectRatio: "16 / 9",
          background: style.window,
          borderRadius: 10,
          boxShadow: style.windowShadow,
          padding: "4cqw 4.5cqw",
          display: "flex",
          flexDirection: "column",
          gap: "1.8cqw",
        }}
      >
        <Bar w="62%" h="2.6cqw" c="#2b3940" r={5} />
        <Bar w="88%" c="#c3ccd1" />
        <Bar w="80%" c="#c3ccd1" />
        <Bar w="44%" c="#c3ccd1" />
        <div
          style={{
            marginTop: "auto",
            width: "40%",
            aspectRatio: "3 / 1",
            borderRadius: 8,
            background: style.badgeBg,
            border: `1px solid ${style.badgeInk}`,
          }}
        />
      </div>
    </div>
  </div>
);

const Sheet: React.FC<{ style: MockStyle }> = ({ style }) => {
  const cols = ["A", "B", "C", "D", "E"];
  const rows = Array.from({ length: 9 });
  return (
    <div
      style={{
        flex: 1,
        background: style.window,
        fontFamily: mockFont.mono,
        fontSize: "1.35cqw",
        color: style.asstInk,
        overflow: "hidden",
      }}
    >
      <div style={{ display: "flex" }}>
        <div style={{ width: "5%", borderRight: `1px solid ${style.railLine}` }} />
        {cols.map((c) => (
          <div
            key={c}
            style={{
              flex: 1,
              padding: "0.7cqw 0",
              textAlign: "center",
              background: "#eef2f4",
              borderRight: `1px solid ${style.railLine}`,
              borderBottom: `1px solid ${style.railLine}`,
              color: style.chromeTitle,
            }}
          >
            {c}
          </div>
        ))}
      </div>
      {rows.map((_, r) => (
        <div key={r} style={{ display: "flex" }}>
          <div
            style={{
              width: "5%",
              padding: "0.7cqw 0",
              textAlign: "center",
              background: "#eef2f4",
              borderRight: `1px solid ${style.railLine}`,
              borderBottom: `1px solid ${style.railLine}`,
              color: style.chromeTitle,
            }}
          >
            {r + 1}
          </div>
          {cols.map((c, ci) => (
            <div
              key={c}
              style={{
                flex: 1,
                padding: "0.7cqw 0.9cqw",
                textAlign: ci === 0 ? "left" : "right",
                borderRight: `1px solid ${style.railLine}`,
                borderBottom: `1px solid ${style.railLine}`,
                background: ci === 3 ? "#eef5f2" : "transparent",
              }}
            >
              {r === 0
                ? ci === 0
                  ? "Item"
                  : ["Qty", "Harga", "Total", "%"][ci - 1]
                : ci === 0
                  ? `Baris ${r}`
                  : ((r * 7 + ci * 13) % 90) + (ci === 4 ? "%" : "")}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

const Doc: React.FC<{ style: MockStyle }> = ({ style }) => (
  <div
    style={{
      flex: 1,
      background: "#e9edf0",
      display: "grid",
      placeItems: "start center",
      padding: "3cqw",
      overflow: "hidden",
    }}
  >
    <div
      style={{
        width: "62%",
        background: style.window,
        boxShadow: style.windowShadow,
        borderRadius: 4,
        padding: "5cqw 5.5cqw",
        display: "flex",
        flexDirection: "column",
        gap: "1.5cqw",
      }}
    >
      <Bar w="55%" h="2.4cqw" c="#2b3940" r={4} />
      <div style={{ height: "1cqw" }} />
      {["92%", "86%", "94%", "70%", "88%", "60%"].map((w, i) => (
        <Bar key={i} w={w} c="#c8d0d4" />
      ))}
      <div style={{ height: "1cqw" }} />
      {["90%", "82%", "48%"].map((w, i) => (
        <Bar key={i} w={w} c="#c8d0d4" />
      ))}
    </div>
  </div>
);

/** "Output opened in a real app" — stylized mock content (or a host still). */
export const AppWindow: React.FC<{
  app: string;
  content?: Content;
  src?: string;
  atSec?: number;
  style: MockStyle;
}> = ({ app, content, src, atSec = 0.2, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const open = interpolate(t, [atSec, atSec + 0.32], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const body =
    src || (content && typeof content === "object")
      ? "src"
      : (content as string) || "mock-doc";

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        opacity: open,
        transform: `scale(${interpolate(open, [0, 1], [0.965, 1])})`,
        transformOrigin: "50% 46%",
      }}
    >
      {/* app toolbar */}
      <div
        style={{
          flex: "0 0 8%",
          display: "flex",
          alignItems: "center",
          gap: "1.6cqw",
          padding: "0 2cqw",
          background: "#f2f5f6",
          borderBottom: `1px solid ${style.railLine}`,
          fontFamily: mockFont.ui,
          fontSize: "1.35cqw",
          color: style.chromeTitle,
        }}
      >
        <span
          style={{
            width: "1.4cqw",
            height: "1.4cqw",
            borderRadius: 4,
            background: style.badgeInk,
          }}
        />
        <span style={{ color: style.asstInk }}>
          {APP_LABEL[app] ?? app}
        </span>
        <span>File</span>
        <span>Edit</span>
        <span>View</span>
      </div>

      {body === "src" ? (
        <div style={{ flex: 1, display: "grid", placeItems: "center", background: "#e9edf0" }}>
          {/* host-supplied export (staged path) */}
          <img
            src={src ?? (typeof content === "object" ? content.src : "")}
            style={{ maxWidth: "94%", maxHeight: "94%", borderRadius: 6, boxShadow: style.windowShadow }}
            alt=""
          />
        </div>
      ) : body === "mock-deck" ? (
        <Deck style={style} />
      ) : body === "mock-sheet" ? (
        <Sheet style={style} />
      ) : (
        <Doc style={style} />
      )}
    </div>
  );
};
