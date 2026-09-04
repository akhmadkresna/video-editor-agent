---
name: overlay-aroll-design
description: Use this skill to generate white text-overlay motion graphics for A-roll (talking-head) video — punch words, flowcharts, chapter markers, CTAs, captions, list-cycles, and floating callouts/illustration tags. Contains tokens, motion primitives, and React overlay components for prototyping or handoff.
user-invocable: true
---

Read the README.md file within this skill, and explore the other available files.
If creating visual artifacts (mock frames, style boards, throwaway prototypes), copy assets out and create static HTML files for the user to view. If working on production code (e.g. a video editor's overlay layer), copy the component files and read the rules here to become an expert in designing with this system.
If the user invokes this skill without any other guidance, ask them what video/moment they're overlaying, what beats need emphasis, and act as an expert motion-graphics designer who outputs HTML artifacts _or_ production code, depending on the need.

Key constraints to always respect: overlay text is white; one accent color used sparingly (CTA only); pill shapes; snappy sub-500ms entrances; safe-zone insets so nothing overlaps a centered speaker; no icon/illustration should be hand-drawn — use the Lucide substitution already wired into `IllustrationTag`, or ask for real assets.
