/**
 * OverlayLab — every overlay kind in isolation, no episode required.
 *
 * The overlay layer is the one piece of this renderer that touches *every*
 * episode in all four style packs, so a regression here is expensive to
 * discover from a real render. This composition is the cheap loop: fixtures
 * cover all 14 kinds plus the awkward cases (1-word stagger, 14-word shrink,
 * unknown icon, valueless callout, both diagram directions, grid opt-in, and
 * two overlays sharing a zone to exercise veil consolidation).
 *
 * The backdrop is generated, not an asset: a mid-grey with a slowly drifting
 * bright patch, so white ink is judged against its worst case somewhere under
 * the playhead, plus a face-oval marker to eyeball the face-clear guardrail.
 */
import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { OverlayLayer } from "./components/OverlayLayer";
import { CTATag } from "./components/overlay/CTATag";
import { DEFAULT_OVERLAY_STYLE, type OverlayStyle, type TimelineOverlay } from "./types";

const SLOT = 4.5;
let slot = 0;
const at = (): { fromSec: number; durationSec: number; exitStartSec: number } => {
  const fromSec = slot++ * SLOT;
  return { fromSec, durationSec: SLOT, exitStartSec: SLOT - 0.9 };
};

export const LAB_OVERLAYS: TimelineOverlay[] = [
  { id: "title-accent", kind: "title", kicker: "Bab 02", text: "Ini judulnya", accent: "besar sekali", zone: "left_third", ...at() },
  { id: "title-one", kind: "title", text: "Satu", zone: "right_third", ...at() },
  {
    id: "emphasis-long",
    kind: "emphasis",
    text: "kalimat panjang sekali yang harus mengecil supaya muat di dalam kotak zona ini",
    zone: "lower_raised",
    ...at(),
  },
  { id: "emphasis-cursor", kind: "emphasis", text: "jadi gini,", zone: "left_third", ...at() },
  { id: "quote-attr", kind: "quote", kicker: "Conor Bronsdon", text: "signals, not proof — worth acting on", zone: "left_third", ...at() },
  { id: "stat-sep", kind: "stat", title: "Tabel ganti kata", value: "3.500.000", sourceLabel: "SKILL.md", zone: "lower_raised", ...at() },
  { id: "callout-value", kind: "callout", value: "43", sourceLabel: "baris", zone: "right_third", ...at() },
  { id: "callout-arrow", kind: "callout", text: "di sini", at: [0.72, 0.38], zone: "left_third", ...at() },
  { id: "callout-plain", kind: "callout", text: "worth it", zone: "lower_raised", ...at() },
  {
    id: "diagram-vert",
    kind: "diagram",
    kicker: "Alur",
    title: "Cara kerjanya",
    steps: ["Baca teks", "Tandai pola", "Tulis ulang", "Review"],
    stepAtSec: [0.6, 1.4, 2.2, 3.0],
    zone: "left_third",
    ...at(),
  },
  { id: "chapter-right", kind: "chapter", kicker: "Bab 07", text: "Jujurnya", zone: "right_third", ...at() },
  { id: "divider-num", kind: "divider", kicker: "Bab 12", title: "Verdict", zone: "left_third", ...at() },
  { id: "chip-icon", kind: "chip", text: "avoid-ai-writing", note: "icon:zap", zone: "top_sparse", ...at() },
  { id: "chip-badicon", kind: "chip", text: "ikon tidak ada", note: "icon:not-a-real-icon", zone: "top_sparse", ...at() },
  { id: "tag-short", kind: "tag", text: "singkat", zone: "top_sparse", fromSec: slot * SLOT, durationSec: 2.5, exitStartSec: 1.6 },
  { id: "lower-third", kind: "lower_third", text: "Kresna", title: "Port Cities", zone: "lower_raised", ...at() },
  { id: "list-cycle", kind: "list_cycle", text: "Bukan cuma", steps: ["caption", "artikel", "email", "thread"], zone: "left_third", ...at() },
  { id: "grid-on", kind: "emphasis", text: "dengan grid", note: "grid:3", zone: "left_third", ...at() },
  // Two in one zone + one in another — veil must stay flat, not stack.
  { id: "veil-a", kind: "emphasis", text: "dua di zona sama", zone: "left_third", ...at() },
  { id: "veil-b", kind: "chip", text: "kedua", zone: "left_third", fromSec: (slot - 1) * SLOT + 0.8, durationSec: 3.0, exitStartSec: 2.1 },
  { id: "veil-c", kind: "chapter", kicker: "Bab 09", text: "zona lain", zone: "right_third", fromSec: (slot - 1) * SLOT + 0.8, durationSec: 3.0, exitStartSec: 2.1 },
];

const Backdrop: React.FC<{ variant?: "grey" | "bright" | "dark" }> = ({ variant = "grey" }) => {
  const frame = useCurrentFrame();
  const base = variant === "bright" ? "#8d8d88" : variant === "dark" ? "#1b1b1a" : "#4a4a48";
  const cx = 50 + 22 * Math.sin(frame / 70);
  const cy = 44 + 12 * Math.cos(frame / 95);
  return (
    <AbsoluteFill style={{ background: base }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${cx}% ${cy}%, rgba(255,255,255,0.55) 0%, rgba(255,255,255,0.12) 34%, transparent 62%)`,
        }}
      />
      {/* face-clear guide */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-start" }}>
        <div
          style={{
            marginTop: "19%",
            width: "24%",
            height: "46%",
            borderRadius: "50%",
            background: "rgba(255,255,255,0.10)",
            border: "1px solid rgba(255,255,255,0.22)",
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const OverlayLab: React.FC<{
  overlays: TimelineOverlay[];
  styleTokens?: OverlayStyle;
  backdrop?: "grey" | "bright" | "dark";
  showCta?: boolean;
}> = ({ overlays, styleTokens = DEFAULT_OVERLAY_STYLE, backdrop = "grey", showCta = true }) => (
  <AbsoluteFill>
    <Backdrop variant={backdrop} />
    <OverlayLayer overlays={overlays} styleTokens={styleTokens} />
    {showCta ? (
      <CTATag
        cta={{ enabled: true, text: "Full video di YouTube", anchor: "top_center", variant: "solid", sizeCqh: 2.2 }}
        styleTokens={styleTokens}
      />
    ) : null}
  </AbsoluteFill>
);

export const labDurationInFrames = (overlays: TimelineOverlay[], fps = 30): number =>
  Math.max(
    1,
    Math.round(overlays.reduce((a, o) => Math.max(a, o.fromSec + o.durationSec), 1) * fps),
  );
