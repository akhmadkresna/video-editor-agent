---
name: video-editor
description: >
  Edit videos: scaffold episode (ae new), transcribe, auto-cut, storyboard plan
  review, cover, render. Use for new project / folder creation — never freestyle mkdir.
version: 0.1.2
platforms: [macos, linux, windows]
metadata:
  hermes:
    category: media
    tags: [video, editing, youtube, transcription, radio-edit, storyboard, ffmpeg, remotion, scaffold]
    requires_tools: [bash]
---

# Video editor (agentic-editor / `ae`)

Drive the local `ae` pipeline for a talking-head / tutorial YouTube episode from
plain-language requests. The user speaks intent ("potong jeda dan yang ngulang");
you translate it to `ae` commands. The cut itself is deterministic Python — you
orchestrate and explain, you do **not** hand-author cut ranges.

## When to Use

- The user wants raw camera footage cut down: silences, thinking pauses, retakes.
- The user asks for a **storyboard** / visual edit plan, a preview, a Remotion Studio
  review, screen-share cover, or YouTube title / description / chapters for an episode.
- Trigger with `/video-editor <what you want>`, or any request naming an episode
  folder plus footage.

Do **not** use for: colour grading, motion-graphics design, multi-cam sync,
music beds — the pipeline does not do those.

## Procedure

### 0. How to run `ae`

- Default `AGENTIC_EDITOR_HOME` on this PC: `G:\AI\video-editor-agent`. Default
  episode workspace: `G:\AI\episodes` (Hermes `terminal.cwd`).
- On the **first** video-edit turn in a session, **run** (do not lecture):
  `echo $env:AGENTIC_EDITOR_HOME` (PowerShell) or `pwd`, then continue. Only if
  the value is empty, stop and tell the user to set Hermes `.env` + restart
  gateway. Never invent paths or freestyle mkdir.
- Invoke the CLI as **`uv run --project $env:AGENTIC_EDITOR_HOME ae <args>`**
  (or `"$AGENTIC_EDITOR_HOME"` on bash). Absolute fallback if env is empty:
  `uv run --project G:\AI\video-editor-agent ae <args>`. The table below writes
  `ae` for brevity.
- Simple probes (`pwd`, `ls`, `ae doctor`) → just run them via the terminal tool.
- First pipeline turn: `ae doctor` — stop if `ffmpeg`/`ffprobe` is MISSING.
- If Telegram shows a dangerous-command approval, tell the user to reply `yes`.

### 0b. New project / scaffold (mandatory)

If the user asks to **create / scaffold / start a new video project or episode**
("bikin project baru", "scaffold", "buat folder", "mulai video baru"), or any
request to create folders/files for editing:

**Hard rule — never freestyle-create the tree.** Do **not** `mkdir`, do **not**
hand-write `project.yaml`, do **not** invent `footage/` / `output/` / `src/`.
Only `ae new` produces a pipeline-valid episode. Full layout:
`references/scaffold.md`.

1. Resolve path: if they give only a slug, use `G:\AI\episodes\<slug>` (Windows
   default). If they give an absolute path, use that. If neither, ask for a
   short slug once.
2. Run `ae new <abs-path>` (add `--force` only after they confirm overwrite).
3. Verify `project.yaml`, `raw/`, and `edit/` exist under that path.
4. Tell them: drop `raw/cam.mp4` (and optional `raw/screen.mp4`), then say
   "footage sudah di raw".
5. `cd` to the episode for all later `ae` commands (`.` = episode).

### 1. Map the request to commands

An **episode** is a folder with `project.yaml` + `raw/` + `edit/`. `cd` into it;
`ae` commands below use `.` as the episode.

| User says (any language) | You run |
|---|---|
| "bikin project / folder", "scaffold", "buat episode", "mulai video baru" | `ae new <path>` only (see 0b + `references/scaffold.md`) |
| "footage sudah di raw", "transkrip dulu", "ingest" | `ae ingest .` |
| "potong footage", "buang jeda / yang ngulang", "auto cut", "radio edit" | `ae ingest .` → `ae edl-suggest .` → `ae storyboard .` → **summarise, then STOP** |
| "storyboard", "show me storyboard", "storyboard please", "tampilin storyboard", "lihat rencana edit", "visualize the plan", "buka storyboard", "refresh storyboard" | If no `edit/edl.suggest.json` or `edit/edl.json`: `ae edl-suggest .` first. Then `ae storyboard .` and point at `edit/storyboard/index.html` |
| "lebih rapat", "jangan agresif", "sisakan jeda mikir" | re-run `ae edl-suggest .` with adjusted flags (`--gap-cut`, `--hold`, `--min-keep`), `ae storyboard .`, summarise, STOP |
| "oke", "terapkan", "apply", "lanjut" | `ae edl-suggest . --apply` → `ae cut .` |
| "lihat hasilnya", "preview video", "studio" | `ae compose . --studio` (or open `edit/preview.mp4` after `ae cut .`) |
| "tampilin layar", "cover", "bagian demo" | `ae cover-suggest .` → propose ranges → STOP → `ae cover .` |
| "cek potongan", "QA" | `ae qa .`, then point at `edit/verify/` |
| "judul / deskripsi / chapter", "shownotes" | read `edit/takes_packed.md`, write `edit/shownotes.md` (see `references/pipeline.md`) |

If a request is ambiguous, ask one short question — do not guess.

### 2. The confirm gate (mandatory)

After `ae edl-suggest .`, run `ae storyboard .` and read `edit/edl.suggest.json`. Report, in the user's
language:

- keep-range count
- kept seconds vs source seconds, and the percentage
- `_meta.gap_classes`: breath / think / ai_wait / retake counts
- anything dropped as a near-duplicate retake

Then **stop and wait**. Never run `ae edl-suggest . --apply` or write
`edit/edl.json` before the user approves. Re-proposing after an adjustment
resets the gate — wait again.

### 3. After approval

`ae edl-suggest . --apply` then `ae cut .`. Report the path to `edit/preview.mp4`
and its rough duration. For screen episodes, offer `ae cover .` next; then
`ae compose . --studio` for review.

Full command reference, flags, and JSON shapes: `references/pipeline.md`.
Non-negotiable editing rules: `references/rules.md`.

## Pitfalls

- **`AGENTIC_EDITOR_HOME` unset** → `ae` cannot resolve templates / Remotion kit.
  Set it before anything else.
- **Freestyle `mkdir` / hand scaffold from Telegram** → wrong tree; `ae ingest`
  fails. Always `ae new`. See `references/scaffold.md`.
- **Editing `edit/edl.json` by hand** → mid-word cuts. Always go through
  `ae edl-suggest`; it snaps to transcript word boundaries and pads 30–200 ms.
- **Skipping `ae cut`'s fades** → audible clicks at every join. Never replace
  `ae cut` with a raw `ffmpeg` concat.
- **Re-transcribing casually** → wastes minutes. Transcripts are cached; only
  `ae ingest --force` when the user says `raw/` changed.
- **Writing under `raw/`** → forbidden. `raw/` is read-only; all output is in
  `edit/`.
- **Running `remotion studio` directly** → black empty timeline. Only
  `ae compose . --studio`.
- **Applying the plan without the user** → violates the confirm gate. Wait for an
  explicit "apply".

## Verification

- After scaffold: path has `project.yaml`, `raw/`, `edit/` — and was created by
  `ae new`, not ad-hoc mkdir.
- `edit/edl.suggest.json` exists and its `_meta.gap_classes` was shown to the
  user before any `--apply`.
- After `ae cut .`: `edit/preview.mp4` exists and is shorter than `raw/cam.mp4`.
- `ae qa .` frames in `edit/verify/` show clean cut boundaries (no mid-word, no
  hard audio pop).
- Nothing was written under `raw/` (except user-dropped footage); agent outputs
  only under `edit/`.
