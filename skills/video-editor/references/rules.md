# Non-negotiable editing rules

These come from the framework's hard rules. They hold regardless of what the
user asks for in the moment.

0. **Scaffold only with `ae new`.** Never freestyle `mkdir` / invent folder
   trees from Telegram or the shell. Default Windows root for a bare slug:
   `G:\AI\episodes\<slug>`. Required layout: `project.yaml` + `raw/` + `edit/`
   — see `scaffold.md`.
1. **Confirm before applying.** Never write `edit/edl.json` or run
   `ae edl-suggest . --apply` until the user has seen the plan summary and said
   apply. Every re-proposal resets this.
2. **Never cut mid-word.** Do not hand-author or hand-edit cut ranges. Only
   `ae edl-suggest` produces ranges — it snaps to transcript word boundaries and
   pads 30–200 ms.
3. **Keep `ae cut`'s fades.** 30 ms audio fades per segment are applied by
   `ae cut`. Never substitute a raw `ffmpeg` concat / trim.
4. **Cache transcripts.** Only `ae ingest --force` when the user states that the
   footage in `raw/` changed.
5. **`raw/` is read-only.** All output goes under `edit/`. Never write, rename,
   or move anything in `raw/`.
6. **Local ASR only.** `auto` backend = whisper.cpp on macOS, faster-whisper
   elsewhere. Default language is Indonesian (`asr.language: id` in
   `project.yaml`); override per episode, not globally.
7. **Audio always from cam.** Screen capture is visual-only (muted). Cam VO is
   DeepFilterNet-enhanced by default; the cache is `edit/audio/cam.voice.wav`.
   Do not add ffmpeg denoise / gate chains.
8. **Remotion Studio only via `ae compose . --studio`.** A bare `remotion studio`
   shows a black empty timeline. Media must be `public/ae-media/...` relative,
   never absolute paths.
9. **Promote, don't fork.** If you find a reusable fix (a style knob, a Remotion
   component, an ASR quirk), append a note to `edit/promotions.md` and change the
   framework under `AGENTIC_EDITOR_HOME` — do not copy framework code into the
   episode.
10. **Talking-head stays talking-head.** Do not add picture-takeover cutaways
    (`cover.cutaways[]` / `ae cutaway-suggest`) on `style: tutorial` /
    `style: evidence` episodes; motion lives on MG overlays instead.
11. **`style: mockup` is the exception (Claude Skill Lab).** This one pack
    has no screen recording — the "screen" is a Remotion-drawn mockup, and
    full-frame drawn scenes are the medium, not a cutaway. Rule 10 does not
    apply here. `ae cutaway-suggest` stays off; `ae mockup-suggest` is its
    replacement. Every drawn scene still carries the cam PIP (the pipeline
    adds it): two shot states only — full cam ⇄ mockup + PIP, never
    full-frame b-roll. Cam-only source, no `raw/screen.mp4`. Scenes live in
    `edit/mockup.json` (authored in cam source seconds; `--apply` validates).
    Full spec: `styles/series/claude-skill-lab/mockup-system.md`.
