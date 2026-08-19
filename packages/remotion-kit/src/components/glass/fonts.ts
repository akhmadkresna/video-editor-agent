/**
 * Real font loading for the "poster study" house style (2026-08, v5).
 *
 * Previously NO font was ever loaded anywhere in remotion-kit — every
 * "Instrument Sans/Serif" or "IBM Plex Mono" reference silently fell back
 * to system fonts, in both Remotion Studio and the final render. Fixed
 * here via @remotion/google-fonts, which gates rendering (delayRender/
 * continueRender) until the font actually loads — required for
 * deterministic frame-by-frame rendering, unlike a plain <link> tag.
 */
import { loadFont as loadArchivo } from "@remotion/google-fonts/Archivo";
import { loadFont as loadIBMPlexMono } from "@remotion/google-fonts/IBMPlexMono";

const archivo = loadArchivo("normal", {
  weights: ["400", "500", "700", "800", "900"],
  subsets: ["latin"],
});
const archivoItalic = loadArchivo("italic", {
  weights: ["400", "500"],
  subsets: ["latin"],
});
const plexMono = loadIBMPlexMono("normal", {
  weights: ["400", "500", "600", "700"],
  subsets: ["latin"],
});

export const sansFamily = archivo.fontFamily;
export const monoFamily = plexMono.fontFamily;
// Referenced so the italic weights are actually requested/loaded.
void archivoItalic;
