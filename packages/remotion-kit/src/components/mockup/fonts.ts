/**
 * Real font loading for the Skill Lab "Mist" mock surfaces.
 *
 * Uses @remotion/google-fonts (gates rendering via delayRender/continueRender
 * until the face actually loads — required for deterministic frame renders,
 * unlike a plain <link>). Instrument Sans for UI text, JetBrains Mono for
 * chrome titles / prompts / skill badges.
 */
import { loadFont as loadInstrument } from "@remotion/google-fonts/InstrumentSans";
import { loadFont as loadJetBrains } from "@remotion/google-fonts/JetBrainsMono";

const instrument = loadInstrument("normal", {
  weights: ["400", "500", "600"],
  subsets: ["latin"],
});
const jetbrains = loadJetBrains("normal", {
  weights: ["400", "500", "700"],
  subsets: ["latin"],
});

export const uiFamily = instrument.fontFamily;
export const monoFamily = jetbrains.fontFamily;

export const mockFont = {
  ui: `'${uiFamily}', system-ui, -apple-system, 'Segoe UI', sans-serif`,
  mono: `'${monoFamily}', 'SF Mono', Menlo, Consolas, ui-monospace, monospace`,
} as const;
