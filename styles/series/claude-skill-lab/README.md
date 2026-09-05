# Series: Claude Skill Lab

A **recurring, light** series. Each episode picks **one Claude skill** —
a built-in one, or one found online / on GitHub — explains what it does
and gives a plain verdict. Short. Trivial to shoot: **talking head only,
no screen recording.**

This is **not** an evidence explainer like `ai-bakar-uang` /
`ai-adopsi-gap`, and **not** a live walkthrough. It is a **pure
explainer**: "here's the skill, here's how it works, here's my take."
Every "screen" is a Remotion-drawn mockup — see
[`mockup-system.md`](mockup-system.md). Uses the new `style: mockup` pack.

This folder is the **series bible + template lock** only. Per-episode copy
lives in each episode at `edit/script.md`.

```yaml
style: mockup
series: claude-skill-lab
sources:
  cam: raw/cam.mp4
asr:
  language: id
```

No `raw/screen.mp4`. The drawn screen is authored via `ae mockup-suggest`
→ `edit/mockup.json`, not recorded.

Agents must not redesign the thumbnail, the episode spine, or the
MockStage "Mist" treatment.

## On-camera series name (locked)

**"Claude Skill Lab"** — spoken and on the thumbnail as `SKILL LAB`.
Episode framing: `Claude Skill Lab #N: <skill>`. Intro line stays:
*"Skill Claude minggu ini: X."*

## Positioning

- **Audience:** broad Indonesian tech-curious viewers who already use
  ChatGPT/Claude for casual questions and want to see what "power use"
  actually looks like — office workers, freelancers, fresh grads.
- **Promise:** every episode, one skill, explained clearly, with a plain
  verdict. No hype, no "10 tricks" listicle, no difficult setup.
- **Persona:** same senior-engineer-adjacent, humble voice as the rest of
  the channel. "Here's how it works and whether it's worth it."
- **Voice:** **saya / kalian**, bahasa lisan, no contempt. It's fine to
  say a skill is not worth it.
- **Tone guardrail:** don't oversell. Name the limits in the "Jujurnya"
  beat. A "skip" verdict is fine and expected.
- **Language:** Indonesia. English terms that read naturally stay English
  (skill, prompt, code execution, sandbox, repo, template).

## Why a series (production logic)

- **Repeatable spine** below = scripting is fill-in-the-blank
  (`naskah-template.md`).
- **~7 minutes**, no chapter announcements, light MG → fast to cut.
- **Talking head only.** No screen recording, no clean-capture retakes,
  no privacy scrubbing. The screen is drawn (`ae mockup-suggest`).
- **Backlog** below is 15+ episodes; more land every time Anthropic or the
  community ships a skill.

## Episode spine (~6–9 min, target 7:00)

1. **Hook (0:00–0:30)** — "Skill Claude minggu ini: **X**." One line on
   why it caught my eye. Tease the task.
2. **Skill ini apa & dari mana (0:30–1:30)** — Plain definition. Source on
   screen: Anthropic bawaan, or the GitHub repo URL. One line on turning
   it on ("tinggal diaktifin" / "drop foldernya"). If activation is
   non-trivial, point to the pinned setup video — do not re-teach it.
3. **Demo (1:30–5:00)** — One illustrative task, walked through on the
   drawn screen (`MockStage` + PIP). Show the idea, not a live run — a
   mock chat, a mock output window.
4. **Jujurnya (5:00–6:30)** — What it's good at, where it falls short, the
   plan/setup caveat, who should actually bother.
5. **Verdict + next (6:30–7:00)** — "Worth it" / "skip" / "worth it kalau
   kamu sering X." Tease next skill. Sign-off: *pelan-pelan aja.*

## Production grammar (fixed per episode)

- **Style:** `style: mockup`. `raw/cam.mp4` only — no screen source.
  Two shot states: **full cam** ⇄ **mockup + PIP**. No full-frame B-roll.
  Full build spec in [`mockup-system.md`](mockup-system.md).
- **Scaffold:** one episode folder per skill, via `ae new` only:
  ```
  ae new G:\AI\episodes\claude-skill-lab-NN-<skill-slug>
  ```
  (`NN` = zero-padded episode number, e.g. `claude-skill-lab-01-avoid-ai-writing`).
- **Drawn screen:** `ae mockup-suggest .` → review → `--apply` →
  `edit/mockup.json`. Scenes align to talking-head beats.
- **Overlays:** `callout` for the skill name and the verdict word;
  `quote` / `stat` for any source line (repo name, doc quote, plan
  requirement). MG renders above the mockup, white ink, no panel.
- No chapter announcements (video is too short). Light MG density.

## Setup-light rules (non-negotiable for this series)

1. **Skills covered use only:** a paid Claude plan + the code-execution /
   file-creation toggle in Claude Desktop, OR a drop-in `SKILL.md` folder.
   No MCP servers, no API keys, no CLI installs.
2. If a skill needs more than that, it becomes a **one-line caveat**, not
   the episode. Pick a lighter skill instead — or keep it conceptual
   (e.g. `mcp-builder`).
3. **One pinned "cara aktifin skill di Claude Desktop" video**, linked in
   every description. Episodes do not re-teach activation.

## Explainer guardrails

- State the plan + toggle requirement once (or lean on the pinned setup
  video). Don't imply skills are free or on by default.
- GitHub / community skills: name where it's from, and say plainly that
  Anthropic shipping a built-in skill ≠ endorsing community ones.
- Don't say skills "belajar" or "ingat." **You write them; Claude selects
  them** based on the description. Say it that way.
- The mockup shows the *idea*, not a claimed live result. Keep mock
  content plausible and generic; don't stage a fake "perfect run" and
  present it as something that happened.
- If the verdict is "skip," say skip.

## Episode backlog (locked order)

Research + full skill inventory: [`research.md`](research.md).

### Locked front (reworked 2026-09-05)

| # | Skill | Source | Hook | Task shown |
|---|-------|--------|------|-----------|
| 01 | `avoid-ai-writing` | GitHub | "Tulisan kamu ketahuan AI?" | Paste AI paragraph → run skill → before/after · *in production* |
| 02 | **build `naskah-santai-id`** (via `skill-creator`) | Bawaan | "Claude nulis Bahasa Indonesia kaku? Bikin skill sendiri" | Live-build a custom `SKILL.md` for natural, non-boring Indonesian YouTube scripts → run it on a real stiff draft → **spontaneous on-camera reaction**. *Build episode.* |
| 03 | "how Claude talks to you" — `discernment-nudge` + anti-glazing skill | Bawaan + hand-written | "Skill yang ngatur cara Claude ngomong ke kamu" | Everyday behavior skills: kill "You're absolutely right!" sycophancy + overtrust nudge |
| 04+ | TBD order | — | — | `algorithmic-art` · `skill-creator` proper (meta angle) · Bench roundups |

**Dropped 2026-09-05 (user call):** `pptx`, `xlsx` — "bikin file" demos, weak for this
audience. Only candidates for a future "skill keren tapi nggak kepake" teardown.

**Ep 02 is a format variant:** the Demo beat is a live build + genuine reaction
(not a pre-planned mock run), still drawn on the MockStage. Jujurnya carries the
unscripted "does it sound like me?" reaction. Allowed for *build* episodes only.

### Bench (episodes 7+)

| Skill / topic | Task shown |
|---|---|
| `canvas-design` / `theme-factory` | Poster & consistent look without Canva |
| `slack-gif-creator` | GIF buat WA / Discord / Slack, dari teks |
| `web-asset-generator` (GitHub) | Favicon + app icon + OG image, sekali jalan |
| Tur repo `anthropics/skills` | Isinya apa aja + cara ambil satu (pinned reference) |
| "Skill buat mikir, bukan bikin file" | Honest roundup: `think-deeply` / `scale-game` / `inversion-exercise` |
| `doc-coauthoring` | Nulis *bareng* Claude, bukan minta dinulisin |
| `brand-guidelines` → bikin sendiri | Paksa output ikut satu gaya brand (punyamu) |
| `mcp-builder` | Konsep: kapan skill nggak cukup (setup lebih berat — jaga tetap konseptual) |
| "Skill keren tapi nggak kepake" | Honest teardown beberapa skill |
| `docx` / `pdf` | Surat dari template kop · isi form PDF / tarik tabel |

Add rows as skills ship. One skill per episode unless it's an explicit
roundup.

## Hard rules for agents

1. Scaffold episodes only with `ae new` — never freestyle folders.
2. `style: mockup`, `series: claude-skill-lab` in `project.yaml`, `cam`
   source only — do not change.
3. No screen recording. The drawn screen comes from `ae mockup-suggest` →
   `edit/mockup.json`. Don't hand-build scene trees; hand-editing the
   applied JSON is fine.
4. MockStage stays the **Mist** treatment (see
   [`mockup-system.md`](mockup-system.md)). Don't fork the look per
   episode — promote changes into `styles/mockup/`.
5. Every source line (repo, doc quote, plan requirement) gets an overlay
   in the same beat.
6. Keep it ~7 min. If a cut runs past ~10 min, the skill was too heavy for
   this series — split or drop it.
7. Humble **saya/kalian** voice. "Skip" verdicts are allowed and expected.
8. Confirm radio-edit before `edit/edl.json`; confirm `edit/mockup.json`
   before `--apply`.
