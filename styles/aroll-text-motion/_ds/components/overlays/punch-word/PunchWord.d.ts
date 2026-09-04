/**
 * @startingPoint section="Overlays" subtitle="Bold pop-in hero word for the strongest beat in a sentence" viewport="700x260"
 */
export interface PunchWordProps {
  /** The word or short phrase to render, split and animated word-by-word */
  text: string;
  /** Optional small uppercase tag shown above the word */
  eyebrow?: string;
  /** Type scale */
  size?: "md" | "lg" | "xl";
  align?: "left" | "center" | "right";
  /** Draws an accent underline stroke beneath the word */
  underline?: boolean;
  /** Adds a continuously blinking type-cursor beam after the word, like a live-typed line */
  cursor?: boolean;
}
