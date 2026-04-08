# Free ImageGen

[中文 README](./README.zh-CN.md)

A **no-API, no-GPU, fully local** image-generation skill for content-first workflows.

If you want to create:
- Xiaohongshu covers
- knowledge cards and infographics
- article-to-image carousels
- OpenClaw-ready visual assets

this is often a better fit than diffusion models.

## Why this exists

Most image generators are optimized for:
- photorealism
- atmosphere
- visual spectacle
- “one prompt, one impressive-looking image”

`Free ImageGen` is optimized for something else:
- ✅ **No API required** — no image API bills
- ✅ **No hardware barrier** — no GPU dependency, no local diffusion setup
- ✅ **Fully local** — better for privacy, reproducibility, and cost control
- ✅ **High freedom** — the agent can decide pagination, layout, tone, and style
- ✅ **Chinese-friendly** — stable Chinese typography, mixed Chinese/English copy, phone-first readability
- ✅ **Xiaohongshu-friendly** — designed for covers, card posts, explainers, and article image sets

If your goal is **content expression**, not photorealistic rendering, this workflow is usually more reliable than diffusion-style generation.

## Compared with diffusion models

Diffusion models are great when you want:
- realistic illustration
- painterly or cinematic results
- visual surprise
- detail-heavy freeform artwork

`Free ImageGen` is better when you want:
- structured visual communication
- article pages with readable text
- explainers, comparisons, checklists, maps, and QA cards
- a full image set generated from one article
- a renderer that follows the agent instead of replacing the agent’s judgment

In one sentence:

> This is a local design renderer for content workflows, not a diffusion model chasing visual spectacle.

## Best use cases

### 1. Xiaohongshu covers
Use it for:
- bold title covers
- opinion-led covers
- tool recommendation covers
- hero-emoji covers

### 2. Infographics and knowledge cards
Built-in card styles include:
- checklist cards
- comparison cards
- mechanism cards
- product maps
- QA cards
- flow cards
- timeline cards

### 3. Turn one article into a full image set
This is one of the strongest workflows.

Good fits:
- Feishu articles
- WeChat articles
- long-form notes
- interviews and summaries
- product updates
- AI tool explainers

### 4. Free-form SVG creation
When you do not want a built-in layout, the agent can directly produce SVG via `custom_svg`.

Good fits:
- mascots
- stickers
- single-page decorative visuals
- custom illustrations where the agent wants full control

## Where the creativity comes from

This skill does **not** invent strong ideas for you.

More accurately:
- 🧠 The creative direction comes from the human
- 🤖 The visual strategy depends on the agent
- 🛠️ The renderer makes those decisions stable and exportable

That is the point of the workflow:
- the agent decides
- the renderer executes

If the agent is strong, the output can be very strong.
If the agent is weak, this skill will not magically turn weak planning into a great image set.

## Quick Start

### Create one cover

```bash
python3 scripts/free_image_gen.py \
  --prompt "text cover, title AI Product Design Principles, subtitle Clear hierarchy and strong mobile readability, theme: light, cover layout: hero_emoji_top, hero emoji: 💡" \
  --output /absolute/path/output/cover.png \
  --width 1080 \
  --height 1440
```

### Create one infographic

```bash
python3 scripts/free_image_gen.py \
  --prompt "infographic mechanism card kicker: three key points title: Why AI Agents suddenly exploded subtitle: It is not just the model — the entry point, UX, and distribution all changed 1. Lower barrier 2. Wider distribution 3. Real monetization" \
  --output /absolute/path/output/infographic.png \
  --width 1080 \
  --height 1440
```

### Give it one article and generate a full image set

```bash
python3 scripts/free_image_gen.py \
  --prompt-file /absolute/path/article.md \
  --story-output-dir /absolute/path/output/article-story \
  --story-strategy auto \
  --width 1080 \
  --height 1440
```

This is good for a quick first draft.

### Recommended workflow: let the agent plan first

This is the workflow that best uses the skill.

Ask the agent to:
- read the full article
- decide pagination
- decide which pages should stay article-like
- decide which pages should become checklist, mechanism, comparison, map, or QA cards
- keep the tone faithful to the source
- output `story-plan.json`
- then call `free-imagegen` to render the set

That gives you a workflow where:
- the agent thinks
- the renderer executes

## Output behavior

Default behavior is intentionally clean:
- PNG only by default
- no extra SVG files unless you explicitly pass `--keep-svg`
- cleaner default naming
- cleaner default output folders

## Freedom level

This skill is **not** “template only.”

You can:
- use built-in layouts for speed
- let the agent plan a full image series
- let the agent directly write `custom_svg`

So the freedom comes from this balance:
- structured when you need stability
- open when you need control

## Fallback vs main path

`illustration` still exists, but it is now best understood as a **lightweight fallback**.

Use `illustration` for:
- quick abstract visuals
- simple decorative single images
- lightweight placeholder-style artwork

Use `custom_svg` first for:
- recognizable objects
- mascots
- animals
- robots
- stickers
- any page where the agent wants direct visual control

## Resources for agents

If you want to integrate this into OpenClaw or another agent workflow, start here:
- `references/story-plan.schema.json`
- `references/story-plan.template.json`
- `references/story-plan.guide.md`
- `references/story-plan.agent-prompt.md`
- `references/custom-svg-best-practices.md`
- `references/custom-svg.story-plan.sample.json`

These files are meant to **protect freedom without sacrificing structure**.

## Summary

If you want a workflow that is:
- free
- local
- API-free
- low-barrier
- Chinese-friendly
- Xiaohongshu-friendly
- agent-driven
- article-to-image capable

then `Free ImageGen` is built for exactly that.
