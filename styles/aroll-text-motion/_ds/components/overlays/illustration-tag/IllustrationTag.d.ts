/**
 * @startingPoint section="Overlays" subtitle="Bare white icon + word popping in from a screen corner, near the speaker" viewport="700x160"
 */
export interface IllustrationTagProps {
  /** Lucide icon name (CDN substitute — no icon set was supplied in source material) */
  icon?: string;
  label: string;
  /** Which corner it pops in from — sets the pop-in transform origin */
  corner?: "top-left" | "top-right" | "bottom-left" | "bottom-right";
}
