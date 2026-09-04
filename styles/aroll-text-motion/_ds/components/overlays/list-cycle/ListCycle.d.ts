/**
 * @startingPoint section="Overlays" subtitle="A fixed word plus a rotating list — for enumerating services or steps" viewport="700x120"
 */
export interface ListCycleProps {
  prefix: string;
  items: string[];
  /** Omit to auto-cycle continuously every `interval` ms; pass to drive it manually */
  activeIndex?: number;
  /** Auto-cycle speed in ms, used only when activeIndex is omitted */
  interval?: number;
}
