/**
 * Real font loading for the A-Roll Text Motion System overlay layer.
 *
 * Via @remotion/google-fonts, which gates rendering (delayRender/
 * continueRender) until the face loads — required for deterministic
 * frame-by-frame renders, unlike a plain <link>.
 *
 * Plus Jakarta Sans = the rounded-geometric bold of the design system
 * (800 punch words, 600 captions/labels). IBM Plex Mono for the `code`
 * kind's terminal window only.
 */
import { loadFont as loadJakarta } from "@remotion/google-fonts/PlusJakartaSans";
import { loadFont as loadIBMPlexMono } from "@remotion/google-fonts/IBMPlexMono";

const jakarta = loadJakarta("normal", {
  weights: ["500", "600", "700", "800"],
  subsets: ["latin"],
});
const plexMono = loadIBMPlexMono("normal", {
  weights: ["400", "500", "600", "700"],
  subsets: ["latin"],
});

export const sansFamily = jakarta.fontFamily;
export const monoFamily = plexMono.fontFamily;
