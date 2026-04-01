# Free ImageGen

A fully local image engine for OpenClaw, Codex, and content workflows.

`Free ImageGen` turns prompts or long-form text into editable SVG artwork and export-ready PNGs without calling any online image API.

It is built for people who want something practical, cheap, and controllable:

- no OpenAI image API
- no hosted text-to-image service
- no per-image cost
- editable `.svg` source files
- mobile-first text covers and infographic cards
- article-to-image card set workflows for OpenClaw

---

## Why It Feels Different

Most AI image tools are optimized for photorealistic novelty.

This repo is optimized for something else:

- **text-heavy visuals that still read well on a phone**
- **knowledge cards and Xiaohongshu-style infographic layouts**
- **turning articles into a sequence of image cards**
- **OpenClaw thumbnails and icons generated locally**
- **SVG-first output that stays editable**

The pipeline is simple and deliberate:

```text
Prompt / Article -> structured layout -> SVG -> local PNG export
```

This means the skill behaves more like a **programmatic design engine** than a model-backed “black box” image generator.

---

## Best At

### 1. Text Covers

Use it for:

- Xiaohongshu-style title cards
- text-first thumbnails
- strong headline covers
- bold short-form content visuals

Examples:

- `文字封面，标题 AI 产品设计原则，副标题 清晰层级 高信息密度 强识别度，核心数字 07`
- `title card about vibe coding, big headline, clean mobile-first layout`

### 2. Knowledge Cards / Infographics

Use it for:

- mechanism cards
- comparison cards
- flow diagrams
- product maps
- tool catalogs
- QA-style knowledge cards

The current infographic engine can automatically switch among layouts like:

- `mechanism`
- `comparison`
- `flow`
- `qa`
- `timeline`
- `catalog`
- `map`

### 3. Article to Image Card Sets

This is the most important workflow for OpenClaw.

Give it a long article, and it can generate:

- a cover card
- announcement cards
- data cards
- explanation cards
- section-based infographic cards

It also writes:

- `analysis.json`
- `outline.md`
- `prompts/*.md`

So the workflow is inspectable and reusable instead of being a one-shot black box.

### 4. OpenClaw Assets

It can generate:

- `assets/thumbnail.svg`
- `assets/thumbnail.png`
- `assets/icon.svg`
- `assets/icon.png`

And update `manifest.json` if present.

---

## What It Does

- Generates images from natural-language prompts
- Uses a fully local `Prompt -> SVG -> PNG` pipeline
- Defaults to general illustration mode for characters, objects, and scenes
- Switches to `text_cover` for title-led cover requests
- Switches to `infographic` for knowledge-card and diagram requests
- Can transform long-form articles into multi-image card sets
- Supports staged workflows like outline-only, prompts-only, and images-only
- Produces editable SVG source files and delivery-ready PNGs

---

## Project Structure

```text
SKILL.md
agents/openai.yaml
references/providers.md
scripts/free_image_gen.py
scripts/free_image_http_service.py
```

---

## Requirements

The generator itself is Python-based, but PNG export needs a local SVG renderer.

Supported renderers, in priority order:

1. `rsvg-convert`
2. `inkscape`
3. `qlmanage`
4. `sips`
5. `magick`

On macOS, the skill will use the best available local renderer it can find.

---

## Quick Start

### Generate a normal illustration

```bash
python3 scripts/free_image_gen.py \
  --prompt "长发可爱女生，清新梦幻插画风，柔和光影，细节丰富" \
  --output /absolute/path/output/cute-girl.png \
  --svg-output /absolute/path/output/cute-girl.svg \
  --width 1024 \
  --height 1280
```

### Generate a text-first cover

```bash
python3 scripts/free_image_gen.py \
  --prompt "文字封面，标题 AI 产品设计原则，副标题 清晰层级 高信息密度 强识别度，核心数字 07" \
  --output /absolute/path/output/text-cover.png \
  --svg-output /absolute/path/output/text-cover.svg \
  --width 1080 \
  --height 1440
```

### Generate an infographic

```bash
python3 scripts/free_image_gen.py \
  --prompt "AI 编码工作流信息图，标题 GPT-5.4 Coding Workflow，副标题 从需求到提交，核心数字 4，1. 需求理解 2. 代码实现 3. 验证测试 4. 提交发布" \
  --output /absolute/path/output/workflow-infographic.png \
  --svg-output /absolute/path/output/workflow-infographic.svg \
  --width 1080 \
  --height 1440
```

### Turn an article into a card set

```bash
python3 scripts/free_image_gen.py \
  --prompt-file /absolute/path/article.txt \
  --story-output-dir /absolute/path/output/article-story \
  --story-strategy dense \
  --width 1080 \
  --height 1440
```

This writes outputs like:

- `01-cover.png/svg`
- `02-*.png/svg`
- `03-*.png/svg`
- `04-*.png/svg`
- `analysis.json`
- `outline.md`
- `prompts/*.md`

Available story strategies:

- `auto`
- `story`
- `dense`
- `visual`

### Generate OpenClaw assets

```bash
python3 scripts/free_image_gen.py \
  --prompt "space heist arcade lobster game" \
  --openclaw-project /absolute/path/to/your-openclaw-app
```

---

## Staged Workflow

If you want a more production-like content workflow, you can split the pipeline into stages.

### Generate analysis + outline + prompts only

```bash
python3 scripts/free_image_gen.py \
  --prompt-file /absolute/path/article.txt \
  --story-output-dir /absolute/path/output/article-story \
  --prompts-only
```

### Generate images from an existing story workflow

```bash
python3 scripts/free_image_gen.py \
  --prompt-file /absolute/path/article.txt \
  --story-output-dir /absolute/path/output/article-story \
  --images-only
```

This structure makes it easier to:

- inspect extracted sections
- tweak prompts card by card
- regenerate later without repeating the whole pipeline

---

## Prompting Tips

### For Illustrations

Describe:

- subject
- mood
- palette
- lighting
- detail level

Example:

- `长发可爱女生，清新梦幻插画风，柔和光影，细节丰富`

### For Text Covers

Say explicitly:

- `文字封面`
- `text cover`
- `title card`

Then include:

- title
- subtitle
- key number if any
- tone or aesthetic hints

### For Infographics

Include the structure directly in the prompt whenever possible:

- title
- subtitle
- highlighted number
- bullets / steps / comparisons / grouped items

### For Article-to-Image Workflows

Best input format:

- plain text body
- headings preserved
- bullet lists preserved
- tables preserved as text
- original embedded image placeholders removed

If you already know the content style, guide it with:

- `--story-strategy story`
- `--story-strategy dense`
- `--story-strategy visual`

---

## HTTP Service

Start the local wrapper:

```bash
python3 scripts/free_image_http_service.py --host 127.0.0.1 --port 8787
```

Health check:

```bash
curl http://127.0.0.1:8787/health
```

Generate one image:

```bash
curl -X POST http://127.0.0.1:8787/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "长发可爱女生，清新梦幻插画风，柔和光影，细节丰富",
    "width": 1024,
    "height": 1280,
    "output": "/absolute/path/output/cute-girl.png",
    "svg_output": "/absolute/path/output/cute-girl.svg"
  }'
```

Generate OpenClaw assets:

```bash
curl -X POST http://127.0.0.1:8787/openclaw-assets \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "space lobster game cover",
    "project": "/absolute/path/to/openclaw-project"
  }'
```

---

## What This Is Not

Being honest about the boundaries makes this skill easier to use well.

This is **not**:

- a photorealistic model-backed image generator
- a diffusion model replacement
- a browser screenshot pipeline
- an online hosted rendering service

It is a **local, rule-based, SVG-first composition engine**.

That tradeoff is exactly why it is:

- cheap to run
- inspectable
- editable
- predictable
- easy to adapt for content systems like OpenClaw

---

## Current Limitations

- Visual quality is strongest for text covers, infographics, product maps, and stylized compositions
- Illustration mode is still stylized and rule-based rather than painterly or photorealistic
- Article summarization is heuristic and works best on clearly structured writing
- Complex content can still require prompt cleanup for the best results
- Final PNG quality depends partly on the local SVG renderer available on the machine

---

## License

No license file has been added yet.

If you want this repo to be reused more widely, adding an explicit license is a good next step.
