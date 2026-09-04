/**
 * @startingPoint section="Overlays" subtitle="Connected step chips for process and flowchart beats" viewport="700x140"
 */
export interface FlowStepsProps {
  steps: { label: string }[];
  direction?: "horizontal" | "vertical";
  /** Steps at or before this index render as "reached" (filled) */
  activeIndex?: number;
}
