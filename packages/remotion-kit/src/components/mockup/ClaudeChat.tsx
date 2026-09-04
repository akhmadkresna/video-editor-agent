import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { MockStyle, MockTurn } from "../../types";
import { mockFont } from "./fonts";
import { sequenceTurns } from "./regions";
import { Caret, streamedLength, typedLength } from "./Typewriter";

const RAIL_W = "13%";

/** Stylized Claude Desktop conversation (Mist). Bottom-anchored thread so the
 *  newest turn sits just above the input; MockCam does the zoom. */
export const ClaudeChat: React.FC<{
  turns: MockTurn[];
  typeCps?: number;
  style: MockStyle;
}> = ({ turns, typeCps = 22, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const seq = sequenceTurns(turns, typeCps);

  // Has any turn reached the thread (a user turn only after it's "sent")?
  const hasContent = seq.some((s) => {
    const sf =
      s.turn.role === "user" && (s.turn.reveal ?? "type") === "type"
        ? (s.startSec + s.revealSec) * fps
        : s.startSec * fps;
    return frame >= sf;
  });

  return (
    <>
      {/* collapsed left rail */}
      <div
        style={{
          flex: `0 0 ${RAIL_W}`,
          background: style.rail,
          borderRight: `1px solid ${style.railLine}`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 16,
          paddingTop: 22,
        }}
      >
        <div
          style={{
            width: "1.6cqw",
            height: "1.6cqw",
            borderRadius: 8,
            border: `1px solid ${style.railLine}`,
            display: "grid",
            placeItems: "center",
            color: style.chipInk,
            fontSize: "1.1cqw",
          }}
        >
          +
        </div>
        {[0.9, 0.55, 0.55].map((o, i) => (
          <div
            key={i}
            style={{
              width: "62%",
              height: "0.5cqw",
              borderRadius: 3,
              background: style.railLine,
              opacity: o,
            }}
          />
        ))}
      </div>

      {/* thread + input */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          minWidth: 0,
          justifyContent: hasContent ? "flex-start" : "center",
        }}
      >
        {!hasContent && (
          <div
            style={{
              alignSelf: "center",
              color: style.inputInk,
              fontSize: "2.6cqw",
              letterSpacing: "-0.01em",
              marginBottom: "1.6cqw",
            }}
          >
            Ada yang bisa saya bantu?
          </div>
        )}
        <div
          style={{
            flex: hasContent ? 1 : "0 0 auto",
            display: hasContent ? "flex" : "none",
            flexDirection: "column",
            justifyContent: "center",
            gap: "2.1cqw",
            // big right pad keeps bubbles clear of the bottom-right cam PIP
            padding: "3cqw 24cqw 3cqw 3.4cqw",
            overflow: "hidden",
          }}
        >
          {seq.map((s, i) => {
            const isUser = s.turn.role === "user";
            const userTypes = isUser && (s.turn.reveal ?? "type") === "type";
            // A user turn is composed in the input bar, then "sent" — the
            // bubble only appears once typing finishes.
            const sentF = userTypes
              ? (s.startSec + s.revealSec) * fps
              : s.startSec * fps;
            const startF = isUser ? sentF : s.startSec * fps;
            if (frame < startF) return null;
            const enter = interpolate(frame, [startF, startF + 8], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            const rise = (1 - enter) * 14;

            if (isUser) {
              return (
                <div
                  key={i}
                  style={{
                    alignSelf: "flex-end",
                    maxWidth: "88%",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "flex-end",
                    gap: 9,
                    opacity: enter,
                    transform: `translateY(${rise}px)`,
                  }}
                >
                  <div
                    style={{
                      background: style.userBubble,
                      color: style.userInk,
                      padding: "1.5cqw 1.9cqw",
                      borderRadius: "18px 18px 6px 18px",
                      fontSize: "1.85cqw",
                      lineHeight: 1.5,
                    }}
                  >
                    {s.turn.text}
                  </div>
                  {(s.turn.attachments ?? []).map((a, k) => (
                    <div
                      key={k}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        fontFamily: mockFont.mono,
                        fontSize: "1.25cqw",
                        color: style.chipInk,
                        border: `1px solid ${style.chipBorder}`,
                        borderRadius: 8,
                        padding: "0.5cqw 1cqw",
                      }}
                    >
                      <span
                        style={{
                          width: "0.9cqw",
                          height: "1.1cqw",
                          border: `1px solid ${style.chipInk}`,
                          borderRadius: 2,
                          opacity: 0.7,
                        }}
                      />
                      {a.name}
                    </div>
                  ))}
                </div>
              );
            }

            // assistant
            const full = s.turn.text;
            const reveal = s.turn.reveal ?? "stream";
            const shownLen =
              reveal === "instant"
                ? full.length
                : reveal === "type"
                  ? typedLength(full.length, startF, frame, fps, typeCps)
                  : streamedLength(full, startF, frame, fps);
            const typing = shownLen < full.length;

            return (
              <div
                key={i}
                style={{
                  alignSelf: "flex-start",
                  maxWidth: "88%",
                  display: "flex",
                  flexDirection: "column",
                  gap: 10,
                  opacity: enter,
                  transform: `translateY(${rise}px)`,
                }}
              >
                {s.turn.skillBadge && (
                  <div
                    style={{
                      alignSelf: "flex-start",
                      fontFamily: mockFont.mono,
                      fontSize: "1.3cqw",
                      letterSpacing: "0.03em",
                      color: style.badgeInk,
                      background: style.badgeBg,
                      padding: "0.55cqw 1.15cqw",
                      borderRadius: 999,
                    }}
                  >
                    {"▸"}  {s.turn.skillBadge}
                  </div>
                )}
                <div
                  style={{
                    color: style.asstInk,
                    fontSize: "1.9cqw",
                    lineHeight: 1.62,
                  }}
                >
                  {full.slice(0, shownLen)}
                  <Caret color={style.caret} frame={frame} fps={fps} visible={typing} />
                </div>
                {s.turn.toolBlock && !typing && (
                  <div
                    style={{
                      fontFamily: mockFont.mono,
                      fontSize: "1.25cqw",
                      color: "#cfd8dd",
                      background: "#1e2529",
                      borderRadius: 10,
                      padding: "1cqw 1.3cqw",
                      lineHeight: 1.6,
                      whiteSpace: "pre-wrap",
                    }}
                  >
                    {s.turn.toolBlock.label ? s.turn.toolBlock.label + "\n" : ""}
                    {s.turn.toolBlock.lines.join("\n")}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* input bar — the user's message is typed here, then sent */}
        {(() => {
          const composing = seq.find((s) => {
            if (s.turn.role !== "user") return false;
            if ((s.turn.reveal ?? "type") !== "type") return false;
            const a = s.startSec * fps;
            const b = (s.startSec + s.revealSec) * fps;
            return frame >= a && frame < b;
          });
          const typed = composing
            ? composing.turn.text.slice(
                0,
                typedLength(
                  composing.turn.text.length,
                  composing.startSec * fps,
                  frame,
                  fps,
                  typeCps,
                ),
              )
            : null;
          return (
            <div
              style={{
                margin: "0 3.4cqw 2.6cqw",
                minHeight: "6.5cqh",
                borderRadius: 14,
                background: style.inputBg,
                display: "flex",
                alignItems: "center",
                // right pad keeps typed text out from under the cam PIP
                padding: "1cqw 20cqw 1cqw 1.6cqw",
                color: typed != null ? style.userInk : style.inputInk,
                fontSize: "1.55cqw",
                lineHeight: 1.5,
              }}
            >
              {typed != null ? (
                <span>
                  {typed}
                  <Caret color={style.caret} frame={frame} fps={fps} />
                </span>
              ) : (
                "Tulis pesan ke Claude…"
              )}
            </div>
          );
        })()}
      </div>
    </>
  );
};
