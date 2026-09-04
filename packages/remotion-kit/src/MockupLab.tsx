import React from "react";
import { AbsoluteFill } from "remotion";
import { MockupLayer } from "./components/MockupLayer";
import { DEFAULT_MOCK_STYLE, type TimelineMockScene } from "./types";

/**
 * Preview fixture for `remotion studio` — Skill Lab #01 (avoid-ai-writing).
 * Not framework data; a smoke test for MockStage / MockCam / ClaudeChat /
 * DiffPanel. The grey PIP box stands in for the cam bubble that compose adds.
 */
export const LAB_MOCK_SCENES: TimelineMockScene[] = [
  {
    id: "lab-chat",
    fromSec: 0,
    durationSec: 15,
    stage: { title: "avoid-ai-writing", chrome: "claude" },
    camera: [
      { atSec: 0.0, state: "establish" },
      { atSec: 1.3, state: "focus", focus: "chat.input", track: "caret" },
      { atSec: 5.2, state: "establish" },
      { atSec: 6.9, state: "read", focus: "chat.turn.assistant" },
      { atSec: 12.5, state: "establish" },
    ],
    layers: [
      {
        component: "ClaudeChat",
        data: {
          typeCps: 26,
          turns: [
            {
              role: "user",
              reveal: "type",
              atSec: 1.2,
              text: "Perbaiki paragraf ini biar nggak kedengaran ditulis AI — maksud dan gaya santainya jangan berubah.",
              attachments: [{ name: "draft-caption.txt" }],
            },
            {
              role: "assistant",
              reveal: "stream",
              atSec: 6.4,
              skillBadge: "Pakai skill · avoid-ai-writing",
              text: "Ada 4 pola yang saya tandai — pembuka klise, “bukan hanya… tetapi juga”, dua em-dash, dan “di era yang terus berkembang”. Ini versi revisinya.",
            },
          ],
        },
      },
      {
        component: "Cursor",
        data: {
          path: [
            { atSec: 0.5, point: [0.55, 0.42] },
            { atSec: 4.6, target: "chat.input", action: "click" },
            { atSec: 7.5, point: [0.62, 0.58] },
          ],
        },
      },
    ],
  },
  {
    id: "lab-repo",
    fromSec: 23,
    durationSec: 8,
    stage: { chrome: "none" },
    camera: [
      { atSec: 0.0, state: "establish" },
      { atSec: 1.4, state: "read", focus: "repo.doc" },
    ],
    layers: [
      {
        component: "RepoView",
        data: {
          repoUrl: "https://github.com/conorbronsdon/avoid-ai-writing",
          repo: "conorbronsdon/avoid-ai-writing",
          source: "community",
          scroll: true,
          atSec: 0.3,
          markdown: [
            "---",
            "name: avoid-ai-writing",
            "description: Audit and rewrite content to remove AI writing patterns.",
            "---",
            "",
            "# avoid-ai-writing",
            "",
            "Flags and fixes **AI-isms** across formatting, sentence structure,",
            "vocabulary, templates, and register-specific tells.",
            "",
            "## Modes",
            "",
            "- **rewrite** — flag and fix",
            "- **detect** — flag only",
            "- **edit** — modify files in place",
            "",
            "## Scope",
            "",
            "> A writing-quality signal, not proof. High false-positive rates for",
            "> non-native English and second-language text.",
            "",
            "## Vocabulary tiers",
            "",
            "| Tier | Action |",
            "| --- | --- |",
            "| 1A / 1B | always replace |",
            "| 2 | flag in clusters |",
            "| 3 | flag at density |",
          ].join("\n"),
        },
      },
    ],
  },
  {
    id: "lab-diff",
    fromSec: 15,
    durationSec: 8,
    stage: { title: "avoid-ai-writing", chrome: "app" },
    camera: [
      { atSec: 0.0, state: "establish" },
      { atSec: 1.4, state: "read", focus: "diff.after" },
      { atSec: 6.5, state: "establish" },
    ],
    layers: [
      {
        component: "DiffPanel",
        data: {
          atSec: 0.4,
          before:
            "Di era yang terus berkembang, AI bukan hanya alat bantu — tetapi juga mitra kerja yang mengubah cara kita bekerja secara fundamental.",
          after:
            "AI sekarang bukan sekadar alat bantu. Buat banyak orang, dia sudah jadi rekan kerja yang beneran ngubah cara mereka kerja.",
          beforeMarks: [
            { type: "del", span: [0, 26] },
            { type: "del", span: [30, 44] },
          ],
          afterMarks: [{ type: "add", span: [0, 3] }],
        },
      },
    ],
  },
  {
    id: "lab-app",
    fromSec: 31,
    durationSec: 7,
    stage: { title: "Presentation.pptx", chrome: "app" },
    camera: [
      { atSec: 0.0, state: "establish" },
      { atSec: 2.2, state: "read", focus: "app.window" },
    ],
    layers: [
      { component: "AppWindow", data: { app: "pptx", content: "mock-deck", atSec: 0.3 } },
    ],
  },
  {
    id: "lab-skills",
    fromSec: 38,
    durationSec: 10,
    stage: { title: "Pengaturan", chrome: "app" },
    camera: [
      { atSec: 0.0, state: "establish" },
      { atSec: 2.0, state: "read", focus: "skills.row.avoid-ai-writing" },
      { atSec: 6.5, state: "establish" },
    ],
    layers: [
      {
        component: "SkillsPanel",
        data: {
          action: "toggle:avoid-ai-writing",
          atSec: 2.6,
          skills: [
            { name: "skill-creator", source: "Bawaan", on: true },
            { name: "pptx", source: "Bawaan", on: true },
            { name: "xlsx", source: "Bawaan", on: false },
            { name: "avoid-ai-writing", source: "GitHub", on: true },
            { name: "brand-guidelines", source: "GitHub", on: false },
          ],
        },
      },
      {
        component: "Cursor",
        data: {
          path: [
            { atSec: 0.4, point: [0.62, 0.42] },
            { atSec: 2.2, target: "skills.row.avoid-ai-writing" },
            { atSec: 3.4, target: "skills.row.avoid-ai-writing", action: "click" },
            { atSec: 5.5, point: [0.7, 0.6] },
          ],
        },
      },
    ],
  },
];

export const MockupLab: React.FC<{ scenes: TimelineMockScene[] }> = ({
  scenes,
}) => (
  <AbsoluteFill style={{ background: DEFAULT_MOCK_STYLE.stageBg }}>
    <MockupLayer scenes={scenes} />
    {/* stand-in cam PIP bubble (compose adds the real pip_corner clip) */}
    <div
      style={{
        position: "absolute",
        right: "3.4%",
        bottom: "4.4%",
        width: "18%",
        aspectRatio: "5 / 6",
        borderRadius: 26,
        background: DEFAULT_MOCK_STYLE.pipGradient,
        boxShadow: "0 12px 30px -12px rgba(0,0,0,0.32)",
        outline: `1px solid ${DEFAULT_MOCK_STYLE.pipRing}`,
        outlineOffset: -1,
      }}
    />
  </AbsoluteFill>
);
