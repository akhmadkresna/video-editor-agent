# Episode scaffold (required layout)

An **episode** is a thin folder the pipeline owns. Scaffold it only with
`ae new` — never `mkdir` / hand-written trees from Telegram or the shell.

## Default location (this machine)

If the user gives only a short name (slug), put the episode under:

```
G:\AI\episodes\<slug>
```

Examples:

| User says | You run |
|---|---|
| `bikin project hermes-demo` | `ae new G:\AI\episodes\hermes-demo` |
| `scaffold G:\AI\episodes\my-ep` | `ae new G:\AI\episodes\my-ep` |
| `mulai video baru` (no path) | Ask for a slug, then `ae new G:\AI\episodes\<slug>` |

Override only when the user gives an explicit absolute path elsewhere.

## After `ae new <path>` — required tree

```
<episode>/
  project.yaml          # id, sources, style, asr, fps, size
  AGENTS.md             # episode agent notes (from template)
  opencode.json         # optional OpenCode wiring (from template)
  .opencode/            # optional OpenCode agent/commands
  raw/                  # READ-ONLY footage drop zone
    .gitkeep
    cam.mp4             # user drops this (required for ingest)
    screen.mp4          # optional; uncomment sources.screen in project.yaml
    evidence/           # optional stills for evidence style
  edit/                 # ALL outputs live here (created empty at scaffold)
```

**`style: mockup` (Claude Skill Lab) is cam-only** — no `raw/screen.mp4`,
no `sources.screen`. Set `project.yaml`: `style: mockup`, `series:
claude-skill-lab`. The "screen" is drawn later via `ae mockup-suggest` →
`edit/mockup.json`. See `references/rules.md` #11.

Later pipeline steps add under `edit/` only, for example:

- `edit/takes_packed.md`, transcript cache
- `edit/edl.suggest.json` → `edit/edl.json`
- `edit/preview.mp4`, `edit/audio/`, `edit/mezzanine/`
- `edit/cover.json`, `edit/timeline.json`, `edit/final.mp4`
- `edit/shownotes.md`, `edit/verify/`

Do **not** pre-create those files by hand.

## Forbidden freestyle layouts

Never create alternate roots such as:

- `footage/`, `input/`, `output/`, `renders/`, `src/`, `assets/video/`
- a nested `project/` inside the episode
- copying Remotion kit / framework code into the episode

If a previous Telegram turn already made a wrong tree: stop, tell the user,
and offer `ae new G:\AI\episodes\<slug>` (or `--force` only after they confirm).

## Confirm before create

1. Resolve the absolute path (default root + slug, or user path).
2. Show the path in one line and ask confirm if the slug was ambiguous.
3. Run: `uv run --project "$AGENTIC_EDITOR_HOME" ae new <abs-path>`
4. Reply with: absolute path, `raw/cam.mp4` drop instruction, next phrase
   ("footage sudah di raw").
