/**
 * @startingPoint section="Overlays" subtitle="Big animated count-up number beat with a continuous sand-drip accent, like an hourglass counter" viewport="700x280"
 */
export interface StatCalloutProps {
  eyebrow?: string;
  /** Numeric values animate counting up from 0; non-numeric strings render as-is */
  value: string | number;
  unit?: string;
  align?: "left" | "center" | "right";
  /** Count-up duration in ms */
  countDuration?: number;
}
