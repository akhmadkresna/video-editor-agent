# Series: Odoo Studio Agentic AI

Locked YouTube thumbnail recipe for every part in this series.

| File | Role |
|------|------|
| `thumbnail.md` | Hard rules + YAML recipe + canonical metrics |
| `build_thumbnail.py` | Draws badge / title / payoff / chips over a text-free plate → exactly 1280×720 |
| `fonts/` | Anton (titles) + Inter (badge, payoff, chips) |
| `refs/part1-canonical.png` | Locked Part 1 reference (1280×720) |
| `refs/part2-canonical.png` | Locked Part 2 reference (1280×720) |

Episodes set `series: odoo-studio-agentic-ai` in `project.yaml`. Agents must not redesign.

**Workflow:** generate a text-free plate → run `build_thumbnail.py` (see `thumbnail.md`). Do not ask an image generator for the finished thumbnail.
