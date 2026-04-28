---
name: free-imagegen
description: "Use when the user asks to generate an image, create a picture, draw an illustration, or produce a text cover locally without external APIs. Fully local text-to-image skill for OpenClaw and general assets — generates SVG from prompt, then converts to PNG with local tools only."
---

# Free ImageGen

Use this skill when the user wants **fully local image generation** with a `Prompt -> SVG -> PNG` pipeline and does **not** want online image APIs.

## Mode Selection

| User intent | Mode | Notes |
|---|---|---|
| Headline, title card, `文字封面`, `标题页` | `text_cover` | Xiaohongshu-style big-title covers, mobile-first |
| Infographic, `知识卡片`, `图解`, `流程图`, `对比图` | `infographic` | Layouts: mechanism, comparison, flow, qa, timeline, catalog, map |
| Long article → planned card set | `story plan` | Preferred: agent reads article first, writes `story-plan.json` |
| Long article → auto card set | `article story` | Fallback when agent cannot plan structure |
| Cover, thumbnail, poster, banner, `封面`, `海报` | `cover` | Explicit cover/poster requests only |
| Person, mascot, object, scene, diagram | `custom_svg` | Agent authors SVG directly for full visual control |
| Quick stylized sketch | `illustration` | Fallback only — not for recognizable subjects |

Do **not** use for photorealistic generation, inpainting/outpainting, model-based editing, or online hosted APIs.

## Workflow

1. Choose mode from the table above
2. Build the prompt (see Input Guidance below)
3. Run the appropriate command
4. **Verify output**: confirm the PNG exists and is non-empty (`test -s output.png`); if rendering fails, install a local SVG renderer — see `references/providers.md`

## Core Modes

Choose the mode from the user intent.

### `illustration`

Use this only as a lightweight fallback for quick stylized subject prompts.

Good for:

- abstract or poster-like subject sketches
- quick experiments when exact object fidelity does not matter
- simple stylized compositions without dense text

Avoid relying on `illustration` when the user wants a clearly recognizable:

- person
- animal
- object
- mascot
- scene with specific visual requirements

For those, prefer `custom_svg` so the agent can directly author the SVG instead of being constrained by the built-in illustration branch.

### `text_cover`

Use when the image is mainly driven by a headline or title.

Good triggers:

- `文字封面`
- `text cover`
- `title card`
- `标题页`

Use this for:

- Xiaohongshu-style big-title covers
- mobile-first text thumbnails
- short-form content covers with strong hierarchy

### `infographic`

Use when the request is about explanation, structure, steps, comparison, grouped information, or knowledge cards.

Good triggers:

- `信息图`
- `知识卡片`
- `图解`
- `流程图`
- `对比图`
- `架构图`
- `产品地图`
- `工具盘点`

The generator may choose among layouts like:

- `mechanism`
- `comparison`
- `flow`
- `qa`
- `timeline`
- `catalog`
- `map`

### `cover`

Use only when the prompt explicitly asks for:

- `cover`
- `thumbnail`
- `poster`
- `banner`
- `封面`
- `海报`

### `article story`

Use when the user provides a long article, post, or document and wants it expressed as a set of images.

This is the preferred mode for OpenClaw article-to-visual workflows.

Outputs can include:

- `analysis.json`
- `outline.md`
- `prompts/*.md`
- `01-cover.png`
- `02-*.png` and later cards

### `story plan` (preferred for agent workflows)

Use this when an agent can read the full article first and decide:

- how many pages to make
- which paragraphs belong together
- which page should be `article_page`, `mechanism`, `checklist`, `qa`, `catalog`, `map`, or another supported layout
- which page should stay close to the original article flow
- which page should use a light or dark treatment

This is now the preferred OpenClaw workflow for rich article conversion because it keeps judgment in the agent and keeps rendering in the skill.

Use these bundled references when an agent needs a stable output contract:

- `references/story-plan.schema.json`
- `references/story-plan.template.json`
- `references/story-plan.guide.md`
- `references/custom-svg-best-practices.md`
- `references/custom-svg.story-plan.sample.json`

### `custom_svg` (for full agent visual control)

Use this when the agent wants to write the SVG directly instead of relying on built-in layouts.

Best for:

- free illustration
- mascots
- specific objects like cats, lobsters, robots, tools, or products
- decorative scene pages
- hand-authored SVG diagrams

Recommended references:

- `references/custom-svg-best-practices.md`
- `references/custom-svg.story-plan.sample.json`

## Commands

### Single image

```bash
python3 scripts/free_image_gen.py \
  --prompt "长发可爱女生，清新梦幻插画风，柔和光影，细节丰富" \
  --output /absolute/path/output/image.png \
  --width 1024 \
  --height 1280
```

### Text cover

```bash
python3 scripts/free_image_gen.py \
  --prompt "文字封面，标题 AI 产品设计原则，副标题 清晰层级 高信息密度 强识别度，核心数字 07" \
  --output /absolute/path/output/text-cover.png \
  --width 1080 \
  --height 1440
```

### Infographic

```bash
python3 scripts/free_image_gen.py \
  --prompt "AI 编码工作流信息图，标题 GPT-5.4 Coding Workflow，副标题 从需求到提交，核心数字 4，1. 需求理解 2. 代码实现 3. 验证测试 4. 提交发布" \
  --output /absolute/path/output/infographic.png \
  --width 1080 \
  --height 1440
```

### Article to image card set

```bash
python3 scripts/free_image_gen.py \
  --prompt-file /absolute/path/article.txt \
  --story-output-dir /absolute/path/output/article-story \
  --story-strategy dense \
  --width 1080 \
  --height 1440
```

### Agent-planned story render

```bash
python3 scripts/free_image_gen.py \
  --story-plan-file /absolute/path/story-plan.json \
  --story-output-dir /absolute/path/output/article-story \
  --width 1080 \
  --height 1440
```

### OpenClaw assets

```bash
python3 scripts/free_image_gen.py \
  --prompt "space heist arcade lobster game" \
  --openclaw-project /absolute/path/to/your-openclaw-app
```

### Optional flags

- `--keep-svg` — retain source SVG files (default: PNG only)
- `--prompts-only` / `--images-only` — run only part of the pipeline
- `--story-strategy auto|story|dense|visual` — article layout strategy

## Agent-Planned Story Workflow

For rich article-to-card conversion, prefer agent-planned rendering:

1. Read the full article
2. Decide pagination, layout per page, and visual treatment
3. Write a `story-plan.json` — see `references/story-plan.schema.json` (contract), `references/story-plan.template.json` (skeleton), and `references/story-plan.guide.md` (judgment guide)
4. Render with `--story-plan-file`
5. **Verify**: invalid plans produce a validation error pointing to the schema

Per-page plan controls (`theme`, `density`, `surface_style`, `accent`, `series_style`, `section_role`, `tone`, `decor_level`, `emoji_policy`, `emoji_render_mode`) and supported page types (`article_page`, `text_cover`, `mechanism`, `checklist`, `qa`, `catalog`, `map`, `comparison`, `flow`, `timeline`) are documented in `references/story-plan.guide.md`.

Use `emoji_render_mode: "svg"` when the target environment is Linux/headless and emoji need to stay colorful and stable.

For `custom_svg` pages, see `references/custom-svg-best-practices.md`.

## Input Guidance

- **Text covers**: include real copy directly — title, subtitle, highlighted number
- **Infographics**: include structured content — title, subtitle, bullets, grouped items, step order, before/after language
- **Illustrations**: describe subject, color, mood, lighting, density of detail
- **Articles**: keep headings, bullet lists, tables, and key numbers; remove embedded image placeholders. For mixed content types, let the agent choose layout per page

## Render Controls

Global CLI flags: `--theme auto|light|dark`, `--page-density auto|comfy|compact`, `--surface-style auto|soft|card|minimal|editorial`, `--accent auto|blue|green|warm|rose`. Per-page plan controls and story-plan styling are documented in `references/story-plan.guide.md`.

## Output Expectations

Optimized for phone readability: fewer line breaks, larger text, simple hierarchy. For article conversion, prefer a small set of clear cards over one overloaded image.

## HTTP Wrapper

Start local service:

```bash
python3 scripts/free_image_http_service.py --host 127.0.0.1 --port 8787
```

Endpoints: `/health`, `/generate`, `/openclaw-assets`

## Files

- `scripts/free_image_gen.py` — core SVG generation and PNG export
- `scripts/free_image_http_service.py` — local HTTP wrapper
- `references/providers.md` — local renderer notes and priority
- `references/story-plan.schema.json` — story plan data contract
- `references/story-plan.template.json` — minimum working skeleton
- `references/story-plan.guide.md` — pagination and layout judgment guide
- `references/custom-svg-best-practices.md` — SVG authoring guidelines
- `references/custom-svg.story-plan.sample.json` — sample custom SVG story plan
