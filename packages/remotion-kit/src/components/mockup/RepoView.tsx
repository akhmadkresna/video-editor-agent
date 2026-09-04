import React from "react";
import {
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { MockStyle } from "../../types";
import { mockFont } from "./fonts";

type Block =
  | { t: "h"; level: number; text: string }
  | { t: "p"; text: string }
  | { t: "li"; text: string; ordered: boolean }
  | { t: "code"; lines: string[] }
  | { t: "quote"; text: string }
  | { t: "tr"; cells: string[]; head: boolean }
  | { t: "hr" }
  | { t: "sp" };

/** Tiny block parser — enough of Markdown to read a SKILL.md at a glance. */
function parse(md: string): Block[] {
  const out: Block[] = [];
  const lines = md.replace(/\r/g, "").split("\n");
  let i = 0;
  let firstTableRow = true;
  while (i < lines.length) {
    const line = lines[i];
    if (line.startsWith("```")) {
      const buf: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) buf.push(lines[i++]);
      i++;
      out.push({ t: "code", lines: buf });
      continue;
    }
    const h = /^(#{1,4})\s+(.*)/.exec(line);
    if (h) {
      out.push({ t: "h", level: h[1].length, text: h[2] });
      i++;
      continue;
    }
    if (/^\s*[-*+]\s+/.test(line)) {
      out.push({ t: "li", text: line.replace(/^\s*[-*+]\s+/, ""), ordered: false });
      i++;
      continue;
    }
    if (/^\s*\d+\.\s+/.test(line)) {
      out.push({ t: "li", text: line.replace(/^\s*\d+\.\s+/, ""), ordered: true });
      i++;
      continue;
    }
    if (/^\s*\|.*\|\s*$/.test(line)) {
      if (/^\s*\|[\s:|-]+\|\s*$/.test(line)) {
        i++;
        continue;
      } // separator row
      const cells = line.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
      out.push({ t: "tr", cells, head: firstTableRow });
      firstTableRow = false;
      i++;
      continue;
    }
    firstTableRow = true;
    if (/^\s*>\s?/.test(line)) {
      out.push({ t: "quote", text: line.replace(/^\s*>\s?/, "") });
      i++;
      continue;
    }
    if (/^\s*(-{3,}|\*{3,})\s*$/.test(line)) {
      out.push({ t: "hr" });
      i++;
      continue;
    }
    if (line.trim() === "") {
      out.push({ t: "sp" });
      i++;
      continue;
    }
    out.push({ t: "p", text: line });
    i++;
  }
  return out;
}

/** `**bold**` → strong; `` `code` `` → mono span; drop other marks. */
function inline(text: string, style: MockStyle): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).filter(Boolean);
  return parts.map((p, k) => {
    if (p.startsWith("**") && p.endsWith("**"))
      return <strong key={k}>{p.slice(2, -2)}</strong>;
    if (p.startsWith("`") && p.endsWith("`"))
      return (
        <code
          key={k}
          style={{
            fontFamily: mockFont.mono,
            fontSize: "0.9em",
            background: style.inputBg,
            borderRadius: 4,
            padding: "0.05em 0.3em",
          }}
        >
          {p.slice(1, -1)}
        </code>
      );
    return <React.Fragment key={k}>{p.replace(/[*_]/g, "")}</React.Fragment>;
  });
}

/** Browser-framed GitHub repo view — real SKILL.md, slow auto-scroll. */
export const RepoView: React.FC<{
  repoUrl: string;
  repo?: string;
  path?: string;
  source?: string;
  markdown: string;
  scroll?: boolean;
  atSec?: number;
  style: MockStyle;
}> = ({ repoUrl, repo, path, source, markdown, scroll = true, atSec = 0.3, style }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;
  const open = interpolate(t, [atSec, atSec + 0.32], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const blocks = parse(markdown);
  // rough content height (px at 1080p) for the scroll travel
  const contentPx = blocks.reduce(
    (a, b) =>
      a +
      (b.t === "h" ? 54 : b.t === "code" ? 30 + b.lines.length * 26 : b.t === "sp" ? 16 : 40),
    0,
  );
  const panePx = 720;
  const maxScroll = Math.max(0, contentPx - panePx);
  const scrollPx = scroll
    ? interpolate(frame, [fps * 1.2, durationInFrames - fps * 1.2], [0, maxScroll], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 0;

  const owner = (repo || repoUrl.replace(/^https?:\/\/github\.com\//, "")).split("/")[0];
  const name = (repo || repoUrl.replace(/^https?:\/\/github\.com\//, "")).split("/")[1] || "";

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        background: style.window,
        opacity: open,
        transform: `scale(${interpolate(open, [0, 1], [0.965, 1])})`,
        transformOrigin: "50% 46%",
        fontFamily: mockFont.ui,
        minWidth: 0,
      }}
    >
      {/* URL bar */}
      <div
        style={{
          flex: "0 0 7%",
          display: "flex",
          alignItems: "center",
          gap: "1cqw",
          padding: "0 2cqw",
          background: style.rail,
          borderBottom: `1px solid ${style.railLine}`,
        }}
      >
        <span
          style={{
            flex: 1,
            fontFamily: mockFont.mono,
            fontSize: "1.3cqw",
            color: style.chipInk,
            background: style.window,
            border: `1px solid ${style.chipBorder}`,
            borderRadius: 999,
            padding: "0.5cqw 1.2cqw",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {repoUrl}
        </span>
      </div>

      {/* repo bar */}
      <div
        style={{
          flex: "0 0 8%",
          display: "flex",
          alignItems: "center",
          gap: "0.6cqw",
          padding: "0 2.4cqw",
          borderBottom: `1px solid ${style.railLine}`,
          fontSize: "1.7cqw",
          color: style.asstInk,
        }}
      >
        <span style={{ color: style.chromeTitle }}>{owner} /</span>
        <strong>{name}</strong>
        {source && (
          <span
            style={{
              marginLeft: "0.8cqw",
              fontSize: "1.1cqw",
              color: style.badgeInk,
              border: `1px solid ${style.badgeInk}`,
              borderRadius: 999,
              padding: "0.15cqw 0.7cqw",
            }}
          >
            {source}
          </span>
        )}
      </div>

      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        {/* file tree */}
        <div
          style={{
            flex: "0 0 22%",
            borderRight: `1px solid ${style.railLine}`,
            background: style.rail,
            padding: "1.6cqw 1.2cqw",
            display: "flex",
            flexDirection: "column",
            gap: "0.9cqw",
            fontFamily: mockFont.mono,
            fontSize: "1.3cqw",
            color: style.chipInk,
          }}
        >
          {["README.md", "SKILL.md", "reference/", "scripts/", "LICENSE"].map((f) => (
            <div
              key={f}
              style={{
                padding: "0.4cqw 0.7cqw",
                borderRadius: 6,
                background: f === "SKILL.md" ? style.badgeBg : "transparent",
                color: f === "SKILL.md" ? style.badgeInk : style.chipInk,
                fontWeight: f === "SKILL.md" ? 600 : 400,
              }}
            >
              {f}
            </div>
          ))}
        </div>

        {/* markdown pane */}
        <div style={{ flex: 1, overflow: "hidden", padding: "0 3.4cqw" }}>
          <div
            style={{
              transform: `translateY(${-scrollPx}px)`,
              paddingTop: "2.6cqw",
              color: style.asstInk,
              fontSize: "1.55cqw",
              lineHeight: 1.62,
              maxWidth: "62ch",
            }}
          >
            {blocks.map((b, k) => {
              if (b.t === "sp") return <div key={k} style={{ height: "1cqw" }} />;
              if (b.t === "hr")
                return (
                  <div
                    key={k}
                    style={{ borderTop: `1px solid ${style.railLine}`, margin: "1.4cqw 0" }}
                  />
                );
              if (b.t === "h")
                return (
                  <div
                    key={k}
                    style={{
                      fontFamily: mockFont.ui,
                      fontWeight: 600,
                      fontSize: `${2.9 - b.level * 0.35}cqw`,
                      margin: `${b.level <= 2 ? 2 : 1.3}cqw 0 0.7cqw`,
                      color: "#2b3940",
                    }}
                  >
                    {inline(b.text, style)}
                  </div>
                );
              if (b.t === "code")
                return (
                  <div
                    key={k}
                    style={{
                      fontFamily: mockFont.mono,
                      fontSize: "1.25cqw",
                      background: "#1e2529",
                      color: "#cfd8dd",
                      borderRadius: 8,
                      padding: "1cqw 1.3cqw",
                      margin: "0.8cqw 0",
                      whiteSpace: "pre-wrap",
                      lineHeight: 1.55,
                    }}
                  >
                    {b.lines.join("\n")}
                  </div>
                );
              if (b.t === "li")
                return (
                  <div key={k} style={{ display: "flex", gap: "0.7cqw", margin: "0.35cqw 0" }}>
                    <span style={{ color: style.badgeInk }}>{b.ordered ? "›" : "•"}</span>
                    <span>{inline(b.text, style)}</span>
                  </div>
                );
              if (b.t === "quote")
                return (
                  <div
                    key={k}
                    style={{
                      borderLeft: `2px solid ${style.badgeInk}`,
                      padding: "0.2cqw 0 0.2cqw 1cqw",
                      color: style.chromeTitle,
                      margin: "0.6cqw 0",
                    }}
                  >
                    {inline(b.text, style)}
                  </div>
                );
              if (b.t === "tr")
                return (
                  <div
                    key={k}
                    style={{
                      display: "flex",
                      gap: "1.2cqw",
                      padding: "0.5cqw 0",
                      borderBottom: `1px solid ${style.railLine}`,
                      fontWeight: b.head ? 600 : 400,
                      color: b.head ? "#2b3940" : style.asstInk,
                    }}
                  >
                    {b.cells.map((c, ci) => (
                      <span key={ci} style={{ flex: 1 }}>
                        {inline(c, style)}
                      </span>
                    ))}
                  </div>
                );
              return (
                <p key={k} style={{ margin: "0.5cqw 0" }}>
                  {inline(b.text, style)}
                </p>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
