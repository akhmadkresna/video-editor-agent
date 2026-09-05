# Claude Skill Lab — research reference

**Living doc.** Come back here to pick the next episode. Update the date
and the inventory whenever Anthropic or the community ships skills.

Last updated: **2026-09-05** · Sources at bottom.

---

## Setup reality (why this series works)

Claude Desktop → Settings → **Capabilities → Skills**.

- Needs a paid plan: **Pro / Max / Team / Enterprise** + **code execution
  turned on**. Team/Enterprise admins enable org-wide first.
- **`skill-creator` is pre-installed** in Claude Desktop.
- Built-in document skills (`docx` / `pdf` / `pptx` / `xlsx`): toggle on.
- Custom / community skills: **upload a zip** in the Skills area. No CLI,
  no API keys, no servers.
- Only skills that break "setup-light": `webapp-testing` (needs
  Playwright), `mcp-builder` (needs Python/Node SDK). Keep those
  conceptual or skip.

One pinned "cara aktifin skill di Claude Desktop" video covers all of the
above once; episodes don't re-teach it.

---

## Official skills — `anthropics/skills` (19 as of 2026-09-04)

### Office files
| Skill | What it does | Light? |
|---|---|---|
| `docx` | Read / generate / edit Word docs, formatting, tracked changes | Y |
| `pdf` | Extract text, merge/split, fill forms, encrypt, OCR | Y |
| `pptx` | Build / extract / edit PowerPoint decks | Y |
| `xlsx` | Build sheets, formulas, charts, clean tabular data | Y |

### Design & art
| Skill | What it does | Light? |
|---|---|---|
| `algorithmic-art` | Reproducible p5.js art via seeded randomness | Y |
| `canvas-design` | Static posters / visual design, named design movements | Y |
| `frontend-design` | Steers UI away from generic "AI-looking" choices | Y |
| `brand-guidelines` | Applies Anthropic's own colors + Poppins/Lora | Y |
| `theme-factory` | Consistent color/font pairings across docs & artifacts | Y |
| `slack-gif-creator` | Animated GIFs sized for Slack (128px emoji, 480px msg) | Y |

### Web artifacts
| Skill | What it does | Light? |
|---|---|---|
| `web-artifacts-builder` | React 18 + TS + Tailwind + shadcn/ui in one HTML file | Y |
| `webapp-testing` | Drive/test local web apps with Playwright | **N** (Playwright) |

### Writing & comms
| Skill | What it does | Light? |
|---|---|---|
| `doc-coauthoring` | Structured co-writing: context → refine → reader-test | Y |
| `internal-comms` | 3P updates, newsletters, FAQs, incident reports in house style | Y |

### Dev & extension
| Skill | What it does | Light? |
|---|---|---|
| `claude-api` | Reference: models, pricing, streaming, tool use, drift checks | Y (hard to demo visually) |
| `mcp-builder` | Build MCP servers (FastMCP / Node SDK) | **N** (SDK install) |
| `skill-creator` | Meta-skill: guided Q&A to build + evaluate new skills | Y (pre-installed) |

### New / behavioral
| Skill | What it does | Light? |
|---|---|---|
| `academy-guide` | Suggests Claude Academy courses on "how do I" queries; auto-fetches catalog | Y (low audience value) |
| `discernment-nudge` | After substantive answers, appends 2–3 "worth a second look" questions to fight overtrust | Y (**on-brand for this channel**) |

---

## Community skills (drop-in zip, no infra)

| Skill | What it does |
|---|---|
| `avoid-ai-writing` | Audits + rewrites text to strip 21 categories of AI tells (43-entry replacement table) |
| `adenaufal/anti-slop-writing` (`indonesian/SKILL.md`) | Natural Bahasa Indonesia: kills stiff formality, template phrases (`tidak hanya… tetapi juga`), forced `Kesimpulan` endings, translationese; restores particles (`nah / sih / dong / kan`). Removal-focused, overlaps ep 1 — reference for ep 2's custom skill, not its own episode. |
| `collision-zone-thinking` | Merges unrelated domains to surface hidden insights/constraints |
| `scale-game` | Stress-tests an idea at extreme scales to expose weak points |
| `think-deeply` | Forces multi-perspective analysis instead of a knee-jerk answer |
| `inversion-exercise` | Reverses the problem statement for fresh angles |
| `simplification-cascades` | Finds one change that simplifies many things at once |
| `color-expert` | Color science + accessibility/contrast guidance |
| `web-asset-generator` | Favicons, app icons, social/OG images in one pass |
| `claude-d3js-skill` | Data viz in d3.js |
| `frontend-slides` | Animation-rich HTML presentations from scratch or conversions |

Community collections: `travisvn/awesome-claude-skills`,
`abubakarsiddik31/claude-skills-collection`. **Always skim a community
`SKILL.md` on camera before trusting it.**

---

## Episode slate (reworked 2026-09-05 — see README backlog for the table)

**Locked front:**
1. `avoid-ai-writing` (GitHub) — "Tulisan kamu ketahuan AI?" · paste AI para → before/after *(in production)*
2. **build `naskah-santai-id`** via `skill-creator` (bawaan) — "Claude nulis Bahasa Indonesia kaku? Bikin skill sendiri" · build a custom SKILL.md for natural, non-boring Indonesian YouTube scripts, then run it on a real stiff draft with spontaneous on-camera reaction. *Build episode* (demo = live build + genuine reaction, still on the mockup). Full beat sketch: session 2026-09-05.
3. **"how Claude talks to you"** — `discernment-nudge` (bawaan) + an anti-glazing / brutal-honesty behavior skill · "Skill yang ngatur cara Claude ngomong ke kamu" · everyday behavior skills — fixes sycophancy ("You're absolutely right!") + overtrust. Confirmed for the series 2026-09-05.
4+. TBD order — `algorithmic-art`, `skill-creator` proper (meta angle, now that ep 2 already used it once), Bench roundups.

**Dropped from the slate (user call 2026-09-05):** `pptx`, `xlsx` — "bikin file" demos, weak for this audience. May only resurface inside a "skill keren tapi nggak kepake" teardown.

**Bench:** `canvas-design`/`theme-factory` (poster & consistent look) ·
`slack-gif-creator` (GIF buat WA/Discord) · `web-asset-generator`
(favicon+icon+OG) · repo tour of `anthropics/skills` (pinned reference) ·
"skill buat mikir, bukan bikin file" roundup (`think-deeply` /
`scale-game` / `inversion-exercise`) · `doc-coauthoring` (write *with*,
not *for*) · `brand-guidelines` → build your own · `mcp-builder` (concept:
kapan skill nggak cukup) · "skill keren tapi nggak kepake" honest teardown.

---

## Sources

- https://github.com/anthropics/skills
- https://github.com/travisvn/awesome-claude-skills
- https://github.com/abubakarsiddik31/claude-skills-collection
- https://codenote.net/en/posts/anthropic-official-skills-catalog-overview/
- https://www.getclaudeskills.com/blog/how-to-install-skills-in-claude-desktop
- https://raw.githubusercontent.com/anthropics/skills/main/skills/discernment-nudge/SKILL.md
- https://raw.githubusercontent.com/anthropics/skills/main/skills/academy-guide/SKILL.md

### Added 2026-09-05 (ep 2 research pass)

- https://github.com/adenaufal/anti-slop-writing — Indonesian anti-slop variant
- https://github.com/karanb192/awesome-claude-skills
- https://github.com/ComposioHQ/awesome-claude-skills
- https://dev.to/suraj_khaitan_f893c243958/i-tried-100-claude-skills-these-are-the-best-1m4a
- No off-the-shelf skill exists for casual/storytelling Bahasa Indonesia YouTube scripts → ep 2 builds one.
- Anti-glazing / brutal-honesty skills (e.g. chadbyte/claude-roast, Brutal Honesty Review) are mostly Claude Code plugins — for ep 3, a Desktop-compatible `SKILL.md` behavior file is needed (likely hand-written or built with `skill-creator`).
