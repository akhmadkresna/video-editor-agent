/**
 * @startingPoint section="Overlays" subtitle="Corner chapter number + title for segmenting a longer A-roll" viewport="700x200"
 */
export interface ChapterMarkerProps {
  number: string | number;
  title: string;
  corner?: "top-left" | "top-right";
}
