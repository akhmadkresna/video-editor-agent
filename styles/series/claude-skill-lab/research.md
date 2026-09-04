# Claude Skill Lab — research reference

**Living doc.** Come back here to pick the next episode. Update the date
and the inventory whenever Anthropic or the community ships skills.

Last updated: **2026-09-04** · Sources at bottom.

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

## Episode slate (locked order — see README backlog for the table)

**Launch 6:**
1. `avoid-ai-writing` (GitHub) — "Tulisan kamu ketahuan AI?" · paste AI para → before/after
2. `pptx` (bawaan) — "Catatan rapat → deck, 2 menit" · messy notes → real .pptx
3. `skill-creator` (bawaan) — "Berhenti jelasin ulang tiap hari" · build one SKILL.md for a real repeat task
4. `algorithmic-art` (bawaan) — "Satu prompt, seni yang bisa diulang persis" · prompt → p5.js → tweak seed
5. `discernment-nudge` (bawaan) — "Skill biar kamu nggak kelewat percaya AI" · ask for an estimate → watch the nudge
6. `xlsx` (bawaan) — "CSV berantakan → laporan rapi + chart"

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
