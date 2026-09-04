/**
 * Deterministic focus regions for MockCam and (later) Cursor.
 *
 * No getBoundingClientRect — every rect is derived from the scene data and a
 * few layout constants, so it is identical on every render pass. Rects are
 * fractions of the full stage (0–1). MockCam turns a rect into a
 * transform-origin (its centre) plus a target scale.
 */
import type { MockLayer, MockTurn, TimelineMockScene } from "../../types";

export type Rect = { x: number; y: number; w: number; h: number };

/** Window inset within the stage — must match MockStage. */
export const WIN: Rect = { x: 0.04, y: 0.036, w: 0.92, h: 0.928 };
const WIN_R = WIN.x + WIN.w;
const RAIL_W = 0.13 * WIN.w;
const CHROME_H = 0.12 * WIN.h;
const INPUT_H = 0.11 * WIN.h;
const THREAD_PAD = 0.03;

/** Reveal duration (seconds) for one turn's text. */
export function revealDurSec(turn: MockTurn, cps: number): number {
  const len = turn.text.length;
  switch (turn.reveal ?? (turn.role === "assistant" ? "stream" : "type")) {
    case "instant":
      return 0.3;
    case "stream":
      return Math.max(0.5, len / (cps * 1.8));
    case "type":
    default:
      return Math.max(0.4, len / cps);
  }
}

export type SequencedTurn = {
  turn: MockTurn;
  startSec: number;
  revealSec: number;
  /** Approx height as a fraction of the stage. */
  heightFrac: number;
};

/** Assign each turn a start second (respecting explicit atSec) + est. height. */
export function sequenceTurns(
  turns: MockTurn[],
  cps = 22,
): SequencedTurn[] {
  const out: SequencedTurn[] = [];
  let cursor = 0.4;
  for (let i = 0; i < turns.length; i++) {
    const turn = turns[i];
    const start = turn.atSec ?? cursor;
    const revealSec = revealDurSec(turn, cps);
    const lines = Math.max(1, Math.ceil(turn.text.length / 46));
    const badge = turn.skillBadge ? 0.05 : 0;
    const attach = turn.attachments?.length ? 0.04 : 0;
    const heightFrac = lines * 0.052 + 0.05 + badge + attach;
    out.push({ turn, startSec: start, revealSec, heightFrac });
    cursor = start + revealSec + 0.6;
  }
  return out;
}

function chatTurns(scene: TimelineMockScene): MockTurn[] {
  const l = scene.layers.find((x) => x.component === "ClaudeChat") as
    | Extract<MockLayer, { component: "ClaudeChat" }>
    | undefined;
  return l?.data.turns ?? [];
}

const THREAD_TOP = WIN.y + CHROME_H + THREAD_PAD;
const THREAD_BOTTOM = WIN.y + WIN.h - INPUT_H - THREAD_PAD;
const THREAD_MID = (THREAD_TOP + THREAD_BOTTOM) / 2;
const THREAD_L = WIN.x + RAIL_W;
/** Right pad reserves the bottom-right for the cam PIP (see ClaudeChat). */
const THREAD_R_PAD = 0.24 * (WIN.w - RAIL_W);
const THREAD_W = WIN.w - RAIL_W - THREAD_R_PAD;
const TURN_STEP = 0.15;

/** Band over the turn being written (or last shown) at t. Thread is
 *  vertically centred, so turns sit around THREAD_MID. */
function caretRect(scene: TimelineMockScene, tLocal: number): Rect {
  const seq = sequenceTurns(chatTurns(scene));
  if (!seq.length) return inputRect();
  const shown = seq.filter((s) => s.startSec <= tLocal + 0.001);
  if (!shown.length) return inputRect();

  const activeIdx = shown.findIndex(
    (s) => tLocal >= s.startSec && tLocal <= s.startSec + s.revealSec,
  );
  const active = activeIdx >= 0 ? shown[activeIdx] : undefined;

  // While a user turn is being typed it lives in the input bar. Return a
  // band that slides right with the caret, so the camera pans as it types.
  if (
    active &&
    active.turn.role === "user" &&
    (active.turn.reveal ?? "type") === "type" &&
    tLocal < active.startSec + active.revealSec
  ) {
    const p = Math.max(
      0,
      Math.min(1, (tLocal - active.startSec) / Math.max(0.001, active.revealSec)),
    );
    const cx = 0.26 + p * 0.24; // caret travels left→right along the line
    // Empty-state greeting + composer sit around the window centre.
    return { x: cx - 0.18, y: THREAD_MID - 0.08, w: 0.4, h: 0.3 };
  }

  const idx = activeIdx >= 0 ? activeIdx : shown.length - 1;
  const offset = (idx - (shown.length - 1) / 2) * TURN_STEP;
  const centre = THREAD_MID + offset;
  return {
    x: THREAD_L + 0.03,
    y: Math.max(THREAD_TOP, centre - 0.07),
    w: Math.min(THREAD_W - 0.04, 0.46),
    h: 0.14,
  };
}

function inputRect(): Rect {
  return {
    x: THREAD_L + 0.03,
    y: WIN.y + WIN.h - INPUT_H - 0.02,
    w: THREAD_W - 0.04,
    h: INPUT_H + 0.02,
  };
}

/** The reply — where reading starts (first lines, just below thread centre). */
function assistantRect(): Rect {
  return {
    x: THREAD_L + 0.02,
    y: THREAD_MID - 0.06,
    w: Math.min(THREAD_W, 0.46),
    h: 0.24,
  };
}

/** Resolve a focus-region name to a rect, or null if unknown. */
export function resolveRegion(
  name: string,
  scene: TimelineMockScene,
  tLocal: number,
): Rect | null {
  if (name === "chat.input") return inputRect();
  if (name === "chat.caret") return caretRect(scene, tLocal);
  if (name === "chat.turn.assistant") return assistantRect();
  if (name.startsWith("chat.turn.")) {
    const idx = parseInt(name.slice("chat.turn.".length), 10);
    const seq = sequenceTurns(chatTurns(scene));
    if (Number.isFinite(idx) && seq[idx]) {
      const offset = (idx - (seq.length - 1) / 2) * TURN_STEP;
      return {
        x: THREAD_L + 0.03,
        y: Math.max(THREAD_TOP, THREAD_MID + offset - 0.09),
        w: Math.min(THREAD_W, 0.5),
        h: 0.2,
      };
    }
  }
  if (name === "diff.before")
    return { x: WIN.x + 0.03, y: WIN.y + 0.1, w: WIN.w / 2 - 0.05, h: WIN.h - 0.16 };
  if (name === "diff.after")
    return {
      x: WIN.x + WIN.w / 2 + 0.02,
      y: WIN.y + 0.1,
      w: WIN.w / 2 - 0.05,
      h: WIN.h - 0.16,
    };
  if (name === "app.window") return WIN;

  if (name === "repo.doc") {
    // markdown pane: right of the 22% tree, below the URL + repo bars (~15%)
    return {
      x: WIN.x + 0.22 * WIN.w,
      y: WIN.y + 0.15 * WIN.h,
      w: WIN.w * 0.78,
      h: WIN.h * 0.82,
    };
  }

  if (name === "skills.upload") {
    return { x: WIN_R - 0.24, y: WIN.y + CHROME_H + 0.05, w: 0.18, h: 0.055 };
  }
  if (name.startsWith("skills.row.")) {
    const wanted = name.slice("skills.row.".length);
    const layer = scene.layers.find((x) => x.component === "SkillsPanel") as
      | Extract<MockLayer, { component: "SkillsPanel" }>
      | undefined;
    const idx = layer?.data.skills.findIndex((s) => s.name === wanted) ?? -1;
    if (idx >= 0) {
      const top = WIN.y + CHROME_H + 0.2;
      const rowH = 0.082;
      return {
        // biased toward the right where the toggle sits
        x: WIN.x + 0.52 * WIN.w,
        y: top + idx * rowH,
        w: WIN.w * 0.18,
        h: rowH,
      };
    }
  }
  return null;
}

export const rectCentre = (r: Rect): [number, number] => [
  r.x + r.w / 2,
  r.y + r.h / 2,
];
