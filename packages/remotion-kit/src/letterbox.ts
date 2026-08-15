/** Shared 9:16 letterbox geometry: centered 16:9 stage with black bars. */

export type LetterboxBand = {
  left: number;
  top: number;
  bandW: number;
  bandH: number;
};

export function letterboxBand(
  frameW: number,
  frameH: number,
  widthRatio = 1,
): LetterboxBand {
  const bandW = Math.round(frameW * Math.min(1, Math.max(0.5, widthRatio)));
  const bandH = Math.round((bandW * 9) / 16);
  const left = Math.round((frameW - bandW) / 2);
  const top = Math.round((frameH - bandH) / 2);
  return { left, top, bandW, bandH };
}

export function isLetterboxPresentation(presentation?: string): boolean {
  const p = (presentation || "").toLowerCase();
  return p === "letterbox_landscape" || p === "letterbox";
}
